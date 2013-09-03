import os
import time
import rpyc
import threading
import logging
import socket
import shutil
import sys
import tempfile
from functools import partial
from mightly.lib import parallelize, remote_run, RemoteCommandError, sendmail, gitrepo
from mightly.report import Report


class HostConnectError(Exception):
    pass

class Host(object):
    def __init__(self, hostname, gitbase, installbase, rpyc_port = 18861):
        self.hostname = hostname
        self.gitbase = gitbase
        self.installbase = installbase
        self.rpyc_port = rpyc_port
    def __repr__(self):
        return "<Host %r>" % (self.hostname,)
    def connect(self):
        try:
            return rpyc.classic.connect(self.hostname, self.rpyc_port)
        except (socket.error, socket.timeout) as ex:
            raise HostConnectError("Could not connect to %r: %s" % (self.hostname, ex))

class REQUIRED(object):
    pass
class REMOVED(object):
    pass

class Deps(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._deps = kwargs.values()
    def __getattr__(self, name):
        return None
    def __iter__(self):
        return iter(self._deps)


class Task(object):
    NOT_RUN = 0
    RUNNING = 1
    FINISHED = 2
    _state = NOT_RUN
    _tid = None
    
    ATTRS = {}
    
    def __init__(self, deps = None, **kwargs):
        if deps is None:
            deps = Deps()
        elif not isinstance(deps, Deps):
            raise TypeError("deps must be either None or an instance of Deps")
        self._lock = threading.Lock()
        self.deps = deps
        ALL_ATTRS = {}
        for cls in reversed(self.__class__.mro()):
            ALL_ATTRS.update(getattr(cls, "ATTRS", ()))
        for k, v in kwargs.items():
            if k not in ALL_ATTRS or ALL_ATTRS.get(k) is REMOVED:
                raise TypeError("Invalid keyword argument %r" % (k,))
            setattr(self, k, v)
        for k, default in ALL_ATTRS.items():
            if k not in kwargs:
                if default is REQUIRED:
                    raise TypeError("Keyword argument %r is required" % (k,))
                elif default is not REMOVED:
                    setattr(self, k, default)
    
    def __repr__(self):
        return self.__class__.__name__
    
    def run(self, report, **params):
        with self._lock:
            if self._state == self.NOT_RUN:
                self._state = self.RUNNING
                self._tid = threading.current_thread().ident
            elif self._state == self.RUNNING:
                if self._tid == threading.current_thread().ident:
                    raise ValueError("Cyclic dependency detected")
                else:
                    return
            elif self._state == self.FINISHED:
                return

        logger = logging.getLogger(self.__class__.__name__)
        self.params = params
        if self.deps:
            logger.info("%s: Satisfying dependencies...", self)
            for dep in self.deps:
                dep.run(report, **self.params)
        logger.info("Running %s", self)
        report2 = report.new_section(str(self))
        self._run(report2)
        logger.info("**** %s is done ****", self)
        
        with self._lock:
            self._state = self.FINISHED
    
    def _run(self, report):
        raise NotImplementedError


class Target(object):
    def __init__(self, name, command, output_pattern):
        self.name = name
        self.command = command
        self.output_pattern = output_pattern
    def __repr__(self):
        return "<Target %r>" % (self.name,)


class GitBuilder(Task):
    GIT_REPO = None
    GIT_DIR = None
    ATTRS = {"hosts" : REQUIRED, "branch" : "develop"}
    
    def _run(self, report):
        self.outputs = {}
        names = set()
        for host, targets in self.hosts.items():
            self.outputs[host] = {}
            for target in targets:
                if target.name in names:
                    raise ValueError("Target name %r appears more than once" % (target.name,))
                names.add(target.name)
                self.outputs[host][target.name] = None
        
        parallelize((partial(self._build_on_host, report, host, targets) for host, targets in self.hosts.items()),
            logger = logging.getLogger(self.__class__.__name__))
    
    @classmethod
    def get_repo_root(cls, host, conn, target):
        return conn.modules.os.path.join(host.gitbase, cls.GIT_DIR, getattr(target, "name", target))
    
    def clean(self):
        def clean_host(host, targets):
            with host.connect() as conn:
                for tgt in targets:
                    root = self.get_repo_root(host, conn, tgt)
                    conn.modules.shutil.rmtree(root, ignore_errors = True)
        
        parallelize((partial(clean_host, host, targets) for host, targets in self.hosts.items()),
            logger = logging.getLogger(self.__class__.__name__))
    
    def _build_on_host(self, report, host, targets):
        for target in targets:
            #report2 = report.new_section()
            logger = logging.getLogger("%s %s/%s" % (self.__class__.__name__, host.hostname, target.name))
            try:
                with host.connect() as conn:
                    conn._config["connid"] = host.hostname
                    logger.info("Building %s:%s on %r", self, target.name, host.hostname)
                    with self.gitrepo(conn, self.get_repo_root(host, conn, target), logger) as root:
                        was_built = self._build_if_needed(host, conn, root, logger, target)
                        self._collect_outputs(host, conn, root, logger, target, was_built)
            except Exception as ex:
                report.add_error("%s %s/%s - FAILED: %r", self.__class__.__name__, host.hostname, target.name, ex)
                raise
            else:
                report.add_succ("%s %s/%s - SUCCESS", self.__class__.__name__, host.hostname, target.name)

    def _build_if_needed(self, host, conn, root, logger, target):
        last_head_fn = conn.modules.os.path.join(root, ".git", "mighlty-last-head")
        head, _ = remote_run(conn, logger, ["git", "rev-parse", "HEAD"])
        head = head.strip()
        if not self.params.get("force_build", False):
            try:
                with conn.builtin.open(last_head_fn, "r") as f:
                    last_head = f.read()
            except IOError:
                last_head = None
            logger.debug("HEAD is %s, last built HEAD is %s", head, last_head)
            output = [conn.modules.os.path.abspath(f)
                for f in conn.modules.glob.glob(conn.modules.os.path.join(root, target.output_pattern))]
            need_build = not output or head != last_head
        else:
            need_build = True
        
        if need_build:
            remote_run(conn, logger, ["git", "submodule", "update", "--init", "--recursive"])
            remote_run(conn, logger, ["git", "clean", "-fxd"])
            logger.info("Building...")
            self._build(host, conn, target, logger)
            with conn.builtin.open(last_head_fn, "w") as f:
                f.write(head)
        
        return need_build
    
    def _collect_outputs(self, host, conn, root, logger, target, was_built):
        if target.output_pattern:
            output = [conn.modules.os.path.abspath(f)
                for f in conn.modules.glob.glob(conn.modules.os.path.join(root, target.output_pattern))]
            if len(output) == 1:
                output = output[0]
            if not output:
                raise ValueError("No outputs found for %s %s (%s)" % (self, target.name, host.hostname))
            assert output
        else:
            output = None
        self.outputs[host][target.name] = output
        if was_built:
            logger.info("Built %r", output)
        else:
            logger.info("%r is up to date", output)
        if self.params.get("copy_outputs", False):
            self._copy_outputs(conn, logger, output)
    
    def _build(self, host, conn, target, logger):
        raise NotImplementedError()
    
    def gitrepo(self, conn, path, logger):
        return gitrepo(conn, path, self.GIT_REPO, self.branch, logger)

    def update_env_vars(self, host, conn, target, env):
        pass
    
    def _copy_outputs(self, conn, logger, outputs):
        local_outputs_dir = self.params["local_outputs_dir"]
        dst = os.path.join(local_outputs_dir, self.GIT_DIR)
        if not os.path.exists(dst):
            os.mkdir(dst)
        if not isinstance(outputs, (tuple, list)):
            outputs = [outputs]

        for fn in outputs:
            logger.info("Downloading %s to %s", fn, dst)
            rpyc.classic.download(conn, fn, os.path.join(dst, os.path.basename(fn)))


class OpenNIBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNI2.git"
    GIT_DIR = "OpenNI2"
    
    def _build(self, host, conn, target, logger):
        conn.modules.os.chdir("Packaging")
        remote_run(conn, logger, target.command)

    def update_env_vars(self, host, conn, target, env):
        oni_repo = self.get_repo_root(host, conn, target)
        glob = conn.modules.glob.glob
        path_join = conn.modules.os.path.join
        outputs_path = glob(path_join(oni_repo, "Packaging", "OpenNI-*"))
        if not outputs_path:
            outputs_path = glob(path_join(oni_repo, "Packaging", "Output*"))
        outputs_path = outputs_path[0]
        
        env["OPENNI2_INCLUDE"] = path_join(outputs_path, "Include")
        env["OPENNI2_REDIST"] = path_join(outputs_path, "Redist")
        env["OPENNI2_LIB"] = path_join(outputs_path, "Lib")
        env["OPENNI2_DRIVERS_PATH"] = path_join(outputs_path, "Driver")
        classpath = [glob(path_join(outputs_path, "Redist", "*.jar"))[0]]
        if "CLASSPATH" in conn.modules.os.environ:
            classpath.append(conn.modules.os.environ["CLASSPATH"])
        env["CLASSPATH"] = conn.modules.os.path.pathsep.join(classpath)


class NiteBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Research/ComputerVision/Common.git"
    GIT_DIR = "NiTE2"

    def _build(self, host, conn, target, logger):
        env = conn.modules.os.environ.copy()
        self.deps.openni_task.update_env_vars(host, conn, target, env)
    
        conn.modules.os.chdir("SDK/Packaging")
        try:
            remote_run(conn, logger, target.command, env = env)
        except RemoteCommandError:
            files = conn.modules.glob.glob("build.*.txt")
            if files:
                with conn.builtin.open(files[0]) as f:
                    text = f.read()
                logger.error("%s:\n%s", files[0], text)
            raise
    
    def update_env_vars(self, host, conn, target, env):
        nite_repo = self.get_repo_root(host, conn, target)
        glob = conn.modules.glob.glob
        path_join = conn.modules.os.path.join
        outputs_path = glob(path_join(nite_repo, "SDK", "Packaging", "NiTE-*"))
        if not outputs_path:
            outputs_path = glob(path_join(nite_repo, "SDK", "Packaging", "Output*"))
        outputs_path = outputs_path[0]
        env["NITE2_INCLUDE"] = path_join(outputs_path, "Include")
        env["NITE2_REDIST"] = path_join(outputs_path, "Redist")


class WrapperBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNIForPython.git"
    GIT_DIR = "PythonWrapper"
    ATTRS = {"host" : REQUIRED, "hosts" : REMOVED, "target" : REQUIRED, "branch" : "master"}

    @property
    def hosts(self):
        return {self.host : [Target("generic", None, output_pattern = "dist/*.tar.gz")]}

    def _build(self, host, conn, target, logger):
        env = {}
        self.deps.openni_task.update_env_vars(host, conn, self.target, env)
        self.deps.nite_task.update_env_vars(host, conn, self.target, env)
        logger.debug("openni_include_dir = %s", env["OPENNI2_INCLUDE"])
        logger.debug("nite_include_dir = %s", env["NITE2_INCLUDE"])
        
        logger.info("Installing python wrapper dependencies")
        remote_run(conn, logger, ["pip", "install", "-r", "requires.txt"], sudo = True)

        conn.modules.os.chdir("bin")
        with conn.builtin.open("sources.ini", "w") as f:
            f.write("[headers]\n")
            f.write("openni_include_dir=%s\n" % (env["OPENNI2_INCLUDE"],))
            f.write("nite_include_dir=%s\n" % (env["NITE2_INCLUDE"],))
            f.write("[pypi]\n")
            f.write("release=internal\n")
        
        logger.info("Building OpenNI wrapper")
        remote_run(conn, logger, ["python", "build_all.py"])


class FirmwareBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/Firmware/PS12xx.git"
    GIT_DIR = "Firmware"
    
    def _build(self, host, conn, target, logger):
        conn.modules.os.chdir("Redist")
        remote_run(conn, logger, target.command)


class CrayolaTester(Task):
    GIT_REPO = "ssh://git/localhome/GIT/Software/Nightly.git"
    GIT_BRANCH = "crayola"
    ATTRS = {"hosts" : REQUIRED}
    
    def _run(self, report):
        parallelize((partial(self._run_on_host, report, host, targets) for host, targets in self.hosts.items()),
            logger = logging.getLogger(self.__class__.__name__))
    
    def _run_on_host(self, report, host, targets):
        first_time = True
        for target_name in targets:
            #report2 = report.new_section("Crayola %s/%s" % (host.hostname, target_name)) 
            logger = logging.getLogger("Crayola %s/%s" % (host.hostname, target_name))
            logger.info("Testing on %s", host.hostname)
            try:
                with host.connect() as conn:
                    conn._config["connid"] = host.hostname
                    self._install_artifact(self.deps.openni_task, host, conn, target_name, logger)
                    self._install_artifact(self.deps.nite_task, host, conn, target_name, logger)
                    if first_time:
                        # these need to be installed only once per host
                        self._install_python_packages(host, conn, logger)
                        self._upload_firmware(host, conn, logger)
                    self._run_crayola(host, conn, target_name, logger)
            except Exception as ex:
                report.add_error("%s %s/%s - FAILED: %r", self.__class__.__name__, host.hostname, target_name, ex)
                raise
            else:
                report.add_succ("%s %s/%s - SUCCESS", self.__class__.__name__, host.hostname, target_name)
                
            first_time = False
    
    def _install_artifact(self, task, host, conn, target_name, logger):
        artifact = task.outputs[host][target_name]
        path_join = conn.modules.os.path.join
        glob = conn.modules.glob.glob
        target = conn.modules.os.path.basename(artifact).replace(".msi", "").replace(".tar.bz2", "").replace(".tar.gz", "")
        logger.info("Installing %s", target)
        if artifact.endswith(".msi"):
            logger.debug("Installing %s", artifact)
            remote_run(conn, logger, ["msiexec", "/i", artifact, "/quiet"])
        else:
            destdir = path_join(host.installbase, target_name, target)
            conn.modules.shutil.rmtree(destdir, ignore_errors = True)
            if not conn.modules.os.path.exists(destdir):
                conn.modules.os.makedirs(destdir)
            remote_run(conn, logger, ["tar", "xjf", artifact], cwd = destdir)
            installer = glob(path_join(destdir, "*", "install.sh"))[0]
            remote_run(conn, logger, [installer], sudo = True)
        logger.info("Successfully installed %s", target)

    def _install_python_packages(self, host, conn, logger):
        logger.info("Installing python packages")
        remote_run(conn, logger, ["pip", "install", "nose"], sudo = True)
        remote_run(conn, logger, ["pip", "install", "srcgen>=1.1"], sudo = True)
        
        [(wrapper_host, wrapper_tgt)] = self.deps.wrapper_task.outputs.items()
        artifact = wrapper_tgt.values()[0]
        
        with wrapper_host.connect() as wrapper_conn:
            tmpdir = conn.modules.tempfile.gettempdir()
            dst = conn.modules.os.path.join(tmpdir, wrapper_conn.modules.os.path.basename(artifact))
            logger.info("Copying %s:%s to %s:%s", wrapper_host.hostname, artifact, host.hostname, dst)
            with wrapper_conn.builtin.open(artifact, "rb") as srcf, conn.builtin.open(dst, "wb") as dstf:
                shutil.copyfileobj(srcf, dstf)
        
        remote_run(conn, logger, ["pip", "install", "-U", dst], sudo = True)
        
    def _upload_firmware(self, host, conn, logger):
        if not self.deps.fw_task:
            return
        # XXX: implement me
        logger.error("Uploading firmware (NOT IMPLEMENTED)")

    def _run_crayola(self, host, conn, target_name, logger):
        logger.info("Installing crayola")
        path = conn.modules.os.path.join(host.installbase, "crayola")
        with gitrepo(conn, path, self.GIT_REPO, self.GIT_BRANCH, logger):
            remote_run(conn, logger, ["python", "setup.py", "install"], cwd = "crayola-report", sudo = True)
            remote_run(conn, logger, ["python", "setup.py", "install"], cwd = "crayola", sudo = True)

            env = conn.modules.os.environ.copy()
            self.deps.openni_task.update_env_vars(host, conn, target_name, env)
            self.deps.nite_task.update_env_vars(host, conn, target_name, env)

            if sys.platform != "win32":
                path = ["/usr/local/bin"]
                if "PATH" in env:
                    path.append(env["PATH"])
                env["PATH"] = conn.os.modules.path.pathsep.join(path)
            
            logger.info("Running tests")
            try:
                out, err = remote_run(conn, logger, ["nosetests", "-d", "--with-crayola-report"],
                    cwd = "tests", env = env)
                if out.strip():
                    logger.debug(out)
                if err.strip():
                    logger.debug(err)
            finally:
                t, v, tb = sys.exc_info()
                try:
                    logger.info("Copying logs from host")
                    dstdir = os.path.join(self.params["local_outputs_dir"], "nose", "%s-%s" % (host.hostname, target_name))
                    shutil.rmtree(dstdir, ignore_errors = True)
                    os.makedirs(dstdir)
                    rpyc.classic.download(conn, "tests/nose_report.html", os.path.join(dstdir, "nose_report.html"))
                    rpyc.classic.download(conn, "tests/nose-logs", os.path.join(dstdir, "nose-logs"))
                except (IOError, OSError, ValueError):
                    logger.warn("Failed to download logs", exc_info = True)
                if t:
                    raise t, v, tb


def mightly_run(tasks, to_addrs = [], mail_server = "ex2010", 
        from_addr = "NightlyUpdate@primesense.com", destination_dir = r"G:\RnD\Software\Nightly_Builds", 
        exit = True, force_build = False, copy_outputs = True):
    
    local_outputs_dir = os.path.join(tempfile.gettempdir(), "mightly-logs")
    shutil.rmtree(local_outputs_dir, ignore_errors = True)
    os.mkdir(local_outputs_dir)
    
    fh = logging.FileHandler(os.path.join(local_outputs_dir, "mightly.log"), "w")
    fmt = logging.Formatter("%(asctime)s|%(thread)04d| %(name)-32s| %(message)s", datefmt = "%H:%M:%S")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(fh)
    logging.root.addHandler(sh)
    report = Report("Mightly Run")
    report.add_text(time.asctime())

    if not isinstance(tasks, (tuple, list)):
        tasks = [tasks]
    logger = logging.getLogger("Mightly")
    logger.info("===== Started %s =====", time.asctime())
    try:
        for task in tasks:
            task.run(report, force_build = force_build, copy_outputs = copy_outputs,
                local_outputs_dir = local_outputs_dir)
    except Exception:
        succ = False
        logger.error("FAILED!", exc_info = True)
    else:
        succ = True
        logger.info("SUCCESS!")
    fh.flush()
    
    if os.path.exists(destination_dir):
        dst_dir = os.path.join(destination_dir, time.strftime("%Y.%m.%d-%H%M"))
        shutil.rmtree(dst_dir, ignore_errors = True)
        logger.info("Copying logs to %s", dst_dir)
        shutil.copytree(local_outputs_dir, dst_dir)
        url = "file:///%s" % (dst_dir.replace("\\", "/"),)
        report.elements.insert(1, ("font-size:2em;", (url, dst_dir)))

    body = report.render()

    with open(os.path.join(".", "email.html"), "w") as f:
        f.write(body)
    
    if to_addrs:
        sendmail(mail_server, from_addr, to_addrs, "Nightly passed :-)" if succ else "Nightly failed :-(", 
            body)
    
    if exit:
        sys.exit(0 if succ else 1)
    else:
        return succ






