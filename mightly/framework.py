import rpyc
import threading
import logging
from functools import partial
from contextlib import contextmanager
from mightly.lib import parallelize, remote_run

logger = logging.getLogger("mightly")
logging.basicConfig(level = logging.DEBUG, format = "%(thread)d|%(asctime)s %(name)-7s %(levelname)-5s] %(message)s",
    datefmt = "%H:%M:%S")


class Host(object):
    def __init__(self, hostname, outputs, rpyc_port = 18861):
        self.hostname = hostname
        self.outputs = outputs
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

        if self.dependencies:
            logger.info("%s: Satisfying dependencies...", self)
            parallelize(dep.run for dep in self.dependencies)
        logger.info("Running %s", self)
        self._run()
        logger.info("%s is done", self)
        
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

class GitBuilder(Task):
    GIT_REPO = None
    ATTRS = {"hosts" : REQUIRED, "branch" : "develop"}
    
    def _run(self):
        self.outputs = {}
        names = set()
        for _, platforms in self.hosts.items():
            for plat in platforms:
                if plat.name in names:
                    raise ValueError("BuildPlatform name %r appears more than once" % (plat.name,))
                names.add(plat.name)
        
        parallelize(partial(self._build_on_host, host, platforms) for host, platforms in self.hosts.items())
    
    def _build_on_host(self, host, platforms):
        for plat in platforms:
            self.outputs[host] = {}
            with host.connect() as conn:
                conn._config["connid"] = host.hostname
                logger.info("Building %s:%s on %r", self, plat.name, host.hostname)
                output = self._build(host, conn, plat)
                self.outputs[host][plat.name] = output
                logger.info("Built %r", output)
    
    def _build(self, host, conn, flavor):
        raise NotImplementedError()
    
    @contextmanager
    def gitrepo(self, conn, path):
        logger.info("Fetching git repo %s on %s", path, conn._config["connid"])
        prevcwd = conn.modules.os.getcwd()
        if not conn.modules.os.path.exists(path):
            conn.modules.os.makedirs(path)
        conn.modules.os.chdir(path)
        if not conn.modules.os.path.isdir(".git"):
            remote_run(conn, ["git", "init"])
            remote_run(conn, ["git", "remote", "add", "origin", self.GIT_REPO])
        
        remote_run(conn, ["git", "fetch", "origin"])
        remote_run(conn, ["git", "reset", "--hard"], allow_failure = True)
        remote_run(conn, ["git", "clean", "-fxd"])
        remote_run(conn, ["git", "checkout", "-b", "build_branch"], allow_failure = True)
        
        if len(self.branch) >= 7 and all(ch in "0123456789abcdefABCDEF" for ch in self.branch):
            # hash
            remote_run(conn, ["git", "reset", "--hard", self.branch])
        else:
            # branch name
            remote_run(conn, ["git", "reset", "--hard", "origin/%s" % (self.branch,)])
        
        remote_run(conn, ["git", "submodule", "update", "--init", "--recursive"])
        try:
            yield
        finally:
            conn.modules.os.chdir(prevcwd)


class OpenNIBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNI2.git"
    
    def _build(self, host, conn, platform):
        path = conn.modules.os.path.join(host.outputs, "OpenNI2", platform.name)
        
        with self.gitrepo(conn, path):
            conn.modules.os.chdir("Packaging")
            remote_run(conn, platform.command)
            return [conn.modules.os.path.abspath(f)
                for f in conn.modules.glob.glob(platform.output_pattern)][0]


class NiteBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Research/ComputerVision/Common.git"
    ATTRS = {"openni_task" : REQUIRED}

    def _build(self, host, conn, platform):
        path = conn.modules.os.path.join(host.outputs, "NiTE2", platform.name)
        
        with self.gitrepo(conn, path):
            conn.modules.os.chdir("SDK/Packaging")
            env = conn.modules.os.environ.copy()
            openni_inc = conn.modules.glob.glob(conn.modules.os.path.join(
                host.outputs, "OpenNI2", platform.name, "Packaging/OpenNI-*/Include"))
            if not openni_inc:
                openni_inc = conn.modules.glob.glob(conn.modules.os.path.join(
                host.outputs, "OpenNI2", platform.name, "Packaging/Output*/Include"))
            openni_redist = conn.modules.glob.glob(conn.modules.os.path.join(
                host.outputs, "OpenNI2", platform.name, "Packaging/OpenNI-*/Redist"))
            if not openni_redist:
                openni_redist = conn.modules.glob.glob(conn.modules.os.path.join(
                host.outputs, "OpenNI2", platform.name, "Packaging/Output*/Redist"))
            
            env["OPENNI2_INCLUDE"] = openni_inc[0]
            env["OPENNI2_REDIST"] = openni_redist[0]

            remote_run(conn, platform.command, env = env)
            return [conn.modules.os.path.abspath(f)
                for f in conn.modules.glob.glob(platform.output_pattern)][0]


class WrapperBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Research/ComputerVision/Common.git"
    ATTRS = {"host" : REQUIRED, "hosts" : REMOVED}
    
    def _run(self):
        with self.host.connect() as conn:
            conn._config["connid"] = self.host.hostname
            path = conn.modules.os.path.join(self.host.outputs, "PythonWrapper")
            openni_include = conn.modules.glob.glob(conn.modules.os.path.join(
                self.host.outputs, "OpenNI2", "linux64", "Packaging/OpenNI-*/Include"))[0]
            nite_include = conn.modules.glob.glob(conn.modules.os.path.join(
                self.host.outputs, "NiTE2", "linux64", "Packaging/OpenNI-*/Include"))[0]
                        
            with self.gitrepo(conn, path):
                logger.info("Installing python wrapper dependencies")
                remote_run(conn, ["sudo", "pip", "install", "-r", "requires.txt"])

                conn.modules.os.chdir("bin")
                with conn.builtin.open("sources.ini", "w") as f:
                    f.write("[headers]\nopenni_include_dir=%s\nnite_include_dir=%s\n" % (openni_include, nite_include))
                logger.info("Building OpenNI wrapper")
                remote_run(conn, "python", "build_all.py")
                self.outputs = [conn.modules.os.path.abspath(conn.modules.glob.glob("../dist/*.tar.gz")[0])]
                logger.info("Built %s", self.outputs[0])


class FirmwareBuilder(GitBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Research/ComputerVision/Common.git"
    ATTRS = {"host" : REQUIRED, "hosts" : REMOVED}
    
    def _run(self):
        with self.host.connect() as conn:
            conn._config["connid"] = self.host.hostname
            path = conn.modules.os.path.join(self.host.outputs, "Firmware")
            #openni_include = conn.modules.glob.glob(conn.modules.os.path.join(
            #    self.host.outputs, "OpenNI2", "linux64", "Packaging/OpenNI-*/Include"))[0]
            #nite_include = conn.modules.glob.glob(conn.modules.os.path.join(
            #    self.host.outputs, "NiTE2", "linux64", "Packaging/OpenNI-*/Include"))[0]
                        
            with self.gitrepo(conn, path):
                pass


class CrayolaTester(Task):
    ATTRS = {"hosts" : REQUIRED}
    
    def _run(self):
        for host in self.hosts:
            self._run_on_host(host)
    
    def _run_on_host(self, host):
        self._install_openni()
        self._install_nite()
        self._install_python_packages()
        self._upload_firmware()
        self._run_crayola()











