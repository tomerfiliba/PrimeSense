import rpyc
import threading
import logging
from functools import partial
from contextlib import contextmanager
from mightly.lib import parallelize, remote_run, RemoteCommandError


logging.basicConfig(level = logging.DEBUG, format = "%(asctime)s|%(thread)04d| %(name)-32s| %(message)s",
    datefmt = "%H:%M:%S")

class Host(object):
    def __init__(self, hostname, outputs, installs, rpyc_port = 18861):
        self.hostname = hostname
        self.outputs = outputs
        self.installs = installs
        self.rpyc_port = rpyc_port
    def __repr__(self):
        return "<Host %r>" % (self.hostname,)
    def connect(self):
        return rpyc.classic.connect(self.hostname, self.rpyc_port)

class REQUIRED(object):
    pass
class REMOVED(object):
    pass

class Task(object):
    NOT_RUN = 0
    RUNNING = 1
    FINISHED = 2
    _state = NOT_RUN
    _tid = None
    
    ATTRS = {}
    
    def __init__(self, dependencies, **kwargs):
        if not isinstance(dependencies, (tuple, list)):
            dependencies = [dependencies]
        self._lock = threading.Lock()
        self.dependencies = dependencies
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
                else:
                    setattr(self, k, default)
    
    def __repr__(self):
        return self.__class__.__name__
    
    def run(self):
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
        if self.dependencies:
            logger.info("%s: Satisfying dependencies...", self)
            for dep in self.dependencies:
                dep.run()
        logger.info("Running %s", self)
        self._run()
        logger.info("**** %s is done ****", self)
        
        with self._lock:
            self._state = self.FINISHED
    
    def _run(self):
        raise NotImplementedError


class BuildPlatform(object):
    def __init__(self, name, command, output_pattern):
        self.name = name
        self.command = command
        self.output_pattern = output_pattern
    def __repr__(self):
        return "<BuildPlatform %r>" % (self.name,)

@contextmanager
def gitrepo(conn, path, repo, branch, logger):
    logger.info("Fetching git repo %s on %s", path, conn._config["connid"])
    try:
        # this might fail if the directory the server was chdir'ed into was deleted
        prevcwd = conn.modules.os.getcwd()
    except OSError:
        conn.modules.os.chdir(conn.modules.os.path.expanduser("~"))
        prevcwd = conn.modules.os.getcwd()
    
    is_hash = (len(branch) >= 7 and all(ch in "0123456789abcdefABCDEF" for ch in branch))
    
    if not conn.modules.os.path.exists(path):
        conn.modules.os.makedirs(path)
    conn.modules.os.chdir(path)
    if not conn.modules.os.path.isdir(".git"):
        if is_hash:
            remote_run(conn, ["git", "clone", repo, "."], logger = logger)
        else:
            remote_run(conn, ["git", "clone", repo, ".", "-b", branch], logger = logger)

    remote_run(conn, ["git", "fetch", "origin"], logger = logger)
    remote_run(conn, ["git", "reset", "--hard"], allow_failure = True, logger = logger)
    remote_run(conn, ["git", "branch", "build_branch"], allow_failure = True, logger = logger)
    remote_run(conn, ["git", "checkout", "build_branch"], logger = logger)
    
    if is_hash:
        remote_run(conn, ["git", "reset", "--hard", branch], logger = logger)
    else:
        remote_run(conn, ["git", "reset", "--hard", "origin/%s" % (branch,)], logger = logger)

    try:
        yield conn.modules.os.getcwd()
    finally:
        conn.modules.os.chdir(prevcwd)


class GitBuilder(Task):
    GIT_REPO = None
    ATTRS = {"hosts" : REQUIRED, "branch" : "develop", "force_build" : False}
    
    def _run(self):
        self.outputs = {}
        names = set()
        for host, platforms in self.hosts.items():
            self.outputs[host] = {}
            for plat in platforms:
                if plat.name in names:
                    raise ValueError("BuildPlatform name %r appears more than once" % (plat.name,))
                names.add(plat.name)
                self.outputs[host][plat.name] = None
        
        parallelize(partial(self._build_on_host, host, platforms) for host, platforms in self.hosts.items())
    
    @classmethod
    def get_repo_root(cls, host, conn, platform):
        raise NotImplementedError()
    
    def clean(self):
        def clean_host(host, platforms):
            with host.connect() as conn:
                for plat in platforms:
                    root = self.get_repo_root(host, conn, plat)
                    conn.modules.shutil.rmtree(root, ignore_errors = True)
        
        parallelize(partial(clean_host, host, platforms) for host, platforms in self.hosts.items())
    
    def _build_on_host(self, host, platforms):
        for plat in platforms:
            logger = logging.getLogger("%s %s/%s" % (self.__class__.__name__, host.hostname, plat.name))
            with host.connect() as conn:
                conn._config["connid"] = host.hostname
                logger.info("Building %s:%s on %r", self, plat.name, host.hostname)

                with self.gitrepo(conn, self.get_repo_root(host, conn, plat), logger = logger) as root:
                    last_head_fn = conn.modules.os.path.join(root, ".git", "mighlty-last-head")
                    head = remote_run(conn, ["git", "rev-parse", "HEAD"], logger = logger).strip()
                    if not self.force_build:
                        try:
                            with conn.builtin.open(last_head_fn, "r") as f:
                                last_head = f.read()
                        except IOError:
                            last_head = None
                        logger.debug("HEAD is %s, last built HEAD is %s", head, last_head)
                        need_build = head != last_head
                    else:
                        need_build = True
                    
                    if need_build:
                        remote_run(conn, ["git", "submodule", "update", "--init", "--recursive"], logger = logger)
                        remote_run(conn, ["git", "clean", "-fxd"], logger = logger)
                        self._build(host, conn, plat, logger)
                        with conn.builtin.open(last_head_fn, "w") as f:
                            f.write(head)
                    
                    output = [conn.modules.os.path.abspath(f)
                        for f in conn.modules.glob.glob(conn.modules.os.path.join(root, plat.output_pattern))]
                    if len(output) == 1:
                        output = output[0]
                    if not output:
                        raise ValueError("No outputs found for %s %s (%s)" % (self, plat.name, host.hostname))
                    assert output
                    self.outputs[host][plat.name] = output
                    if need_build:
                        logger.info("Built %r", output)
                    else:
                        logger.info("%r is up to date", output)
    
    def _build(self, host, conn, platform, logger):
        raise NotImplementedError()
    
    def gitrepo(self, conn, path, logger):
        return gitrepo(conn, path, self.GIT_REPO, self.branch, logger)


class OpenNIBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNI2.git"
    
    @classmethod
    def get_repo_root(cls, host, conn, platform):
        return conn.modules.os.path.join(host.outputs, "OpenNI2", platform.name)
    
    def _build(self, host, conn, platform, logger):
        conn.modules.os.chdir("Packaging")
        remote_run(conn, platform.command, logger = logger)


class NiteBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Research/ComputerVision/Common.git"

    @classmethod
    def get_repo_root(cls, host, conn, platform):
        return conn.modules.os.path.join(host.outputs, "NiTE2", platform.name)

    def _build(self, host, conn, platform, logger):
        conn.modules.os.chdir("SDK/Packaging")
        oni_repo = OpenNIBuilder.get_repo_root(host, conn, platform)
        glob = conn.modules.glob.glob
        path_join = conn.modules.os.path.join
        outputs_path = glob(path_join(oni_repo, "Packaging", "OpenNI-*"))
        if not outputs_path:
            outputs_path = glob(path_join(oni_repo, "Packaging", "Output*"))
        outputs_path = outputs_path[0]
        
        env = conn.modules.os.environ.copy()
        env["OPENNI2_INCLUDE"] = path_join(outputs_path, "Include")
        env["OPENNI2_REDIST"] = path_join(outputs_path, "Redist")
        env["OPENNI2_LIB"] = path_join(outputs_path, "Lib")
        env["OPENNI2_DRIVERS_PATH"] = path_join(outputs_path, "Driver")
        classpath = [glob(path_join(outputs_path, "Redist", "*.jar"))[0]]
        if "CLASSPATH" in env:
            classpath.append(env["CLASSPATH"])
        env["CLASSPATH"] = conn.modules.os.path.pathsep.join(classpath)
    
        try:
            remote_run(conn, platform.command, env = env, logger = logger)
        except RemoteCommandError:
            files = conn.modules.glob.glob("build.*.txt")
            if files:
                with conn.builtin.open(files[0]) as f:
                    text = f.read()
                logger.error("%s:\n%s", files[0], text)
            raise


class WrapperBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNIForPython.git"
    ATTRS = {"host" : REQUIRED, "hosts" : REMOVED, "platform" : REQUIRED, "branch" : "master"}
    
    def _run(self):
        self.platform = BuildPlatform(self.platform, None, None)
        logger = logging.getLogger("%s %s/%s" % (self.__class__.__name__, self.host.hostname, self.platform.name))
        with self.host.connect() as conn:
            conn._config["connid"] = self.host.hostname
            oni_repo = OpenNIBuilder.get_repo_root(self.host, conn, self.platform)
            nite_repo = NiteBuilder.get_repo_root(self.host, conn, self.platform)
            glob = conn.modules.glob.glob
            path_join = conn.modules.os.path.join

            oni_outputs_path = glob(path_join(oni_repo, "Packaging", "OpenNI-*"))
            if not oni_outputs_path:
                oni_outputs_path = glob(path_join(oni_repo, "Packaging", "Output*"))
            oni_outputs_path = oni_outputs_path[0]

            nite_outputs_path = glob(path_join(nite_repo, "SDK", "Packaging", "NiTE-*"))
            if not nite_outputs_path:
                nite_outputs_path = glob(path_join(nite_repo, "SDK", "Packaging", "Output*"))
            nite_outputs_path = nite_outputs_path[0]

            openni_include = path_join(oni_outputs_path, "Include")
            nite_include = path_join(nite_outputs_path, "Include")
            path = conn.modules.os.path.join(self.host.outputs, "PythonWrapper")
            logger.info("openni_include_dir = %s", openni_include)
            logger.info("nite_include_dir = %s", nite_include)

            with self.gitrepo(conn, path, logger = logger):
                logger.info("Installing python wrapper dependencies")
                try:
                    remote_run(conn, ["which", "sudo"], logger = logger)
                except RemoteCommandError:
                    remote_run(conn, ["pip", "install", "-r", "requires.txt"], logger = logger)
                else:
                    remote_run(conn, ["sudo", "pip", "install", "-r", "requires.txt"], logger = logger)

                conn.modules.os.chdir("bin")
                with conn.builtin.open("sources.ini", "w") as f:
                    f.write("[headers]\n")
                    f.write("openni_include_dir=%s\n" % (openni_include,))
                    f.write("nite_include_dir=%s\n" % (nite_include,))
                    f.write("[pypi]\n")
                    f.write("release=internal\n")
                
                logger.info("Building OpenNI wrapper")
                remote_run(conn, ["python", "build_all.py"], logger = logger)
                dist = conn.modules.os.path.abspath(conn.modules.glob.glob("../dist/*.tar.gz")[0])
                self.outputs = {self.host : {self.platform.name : dist}}
                logger.info("Built %s", dist)


class FirmwareBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/Firmware/PS12xx.git"

    @classmethod
    def get_repo_root(cls, host, conn, platform):
        return conn.modules.os.path.join(host.outputs, "OpenNI2", platform.name)
    
    def _build(self, host, conn, platform, logger):
        conn.modules.os.chdir("Redist")
        remote_run(conn, platform.command, logger = logger)
        # copy to Release
    


class CrayolaTester(Task):
    GIT_REPO = "ssh://git/localhome/GIT/Software/Nightly.git"
    GIT_BRANCH = "crayola"
    ATTRS = {"hosts" : REQUIRED, "openni_task" : REQUIRED, "nite_task" : REQUIRED, 
        "wrapper_task" : REQUIRED, "fw_task" : REQUIRED}
    
    def _run(self):
        for host, platforms in self.hosts.items():
            self._run_on_host(host, platforms)
    
    def _run_on_host(self, host, platforms):
        first_time = True
        for platname in platforms:
            logger = logging.getLogger("Crayola %s/%s" % (host.hostname, platname))
            logger.info("Testing on %s", host.hostname)
            with host.connect() as conn:
                conn._config["connid"] = host.hostname
                self._install_openni(host, conn, platname, logger)
                self._install_nite(host, conn, platname, logger)
                if first_time:
                    self._install_python_packages(host, conn, platname, logger)
                    self._install_crayola(host, conn, platname, logger)
                    self._upload_firmware(host, conn, platname, logger)
                self._run_crayola(host, conn, platname, logger)
            first_time = False
    
    def _install_artifact(self, task, host, conn, platname, logger):
        artifact = task.outputs[host][platname]
        path_join = conn.modules.os.path.join
        glob = conn.modules.glob.glob
        target = conn.modules.os.path.basename(artifact).replace(".msi", "").replace(".tar.bz2", "").replace(".tar.gz", "")
        logger.info("Installing %s", target)
        if artifact.endswith(".msi"):
            logger.debug("Installing %s", artifact)
            remote_run(conn, ["msiexec", "/i", artifact, "/quiet"])
        else:
            destdir = path_join(host.installs, platname, target)
            conn.modules.shutil.rmtree(destdir, ignore_errors = True)
            if not conn.modules.os.path.exists(destdir):
                conn.modules.os.makedirs(destdir)
            remote_run(conn, ["tar", "xjf", artifact], cwd = destdir, logger = logger)
            installer = glob(path_join(destdir, "*", "install.sh"))[0]
            remote_run(conn, ["sudo", installer], logger = logger)
        logger.info("Successfully installed %s", target)
    
    def _install_openni(self, host, conn, platname, logger):
        self._install_artifact(self.openni_task, host, conn, platname, logger)

    def _install_nite(self, host, conn, platname, logger):
        self._install_artifact(self.nite_task, host, conn, platname, logger)

    def _install_python_packages(self, host, conn, platname, logger):
        artifact = self.wrapper_task.outputs[host][platname]
        logger.info("Installing python packages")
        remote_run(conn, ["sudo", "pip", "install", "nose"], logger = logger)
        remote_run(conn, ["sudo", "pip", "install", "srcgen>=1.1"], logger = logger)
        remote_run(conn, ["sudo", "pip", "install", "-U", artifact], logger = logger)
        
    def _install_crayola(self, host, conn, platname, logger):
        logger.info("Installing crayola")
        path = conn.modules.os.path.join(host.installs, "crayola")
        with gitrepo(conn, path, self.GIT_REPO, self.GIT_BRANCH, logger) as repo:
            remote_run(conn, ["sudo", "python", "setup.py", "install"], cwd = "crayola-report", logger = logger)
            remote_run(conn, ["sudo", "python", "setup.py", "install"], cwd = "crayola", logger = logger)

    def _upload_firmware(self, host, conn, platname, logger):
        logger.info("Uploading firmware")

    def _run_crayola(self, host, conn, platname, logger):
        print "hello world"








