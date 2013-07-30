from mightly.partools import parallel_map
import os


class HostInfo(object):
    def __init__(self, hostname, platforms):
        self.hostname = hostname
        self.platforms = platforms

build_server = HostInfo("buildserver", ["WIN32", "WIN64"])
sdk64 = HostInfo("sdk64", ["LIN64", "Arm", "Android"])
sdk32 = HostInfo("sdk32", ["LIN32"])
softwaremac = HostInfo("softwaremac", ["OSX"])

class Task(object):
    def __init__(self, workers, depends = ()):
        self.workers = workers
        self.depends = ()
        self.built = False

    def make(self):
        if self.built:
            return
        parallel_map(lambda task: task.make(), self.depends)
        self.outputs = parallel_map(self.build_on_worker, self.workers)
        self.built = True
    
    def make_on_worker(self, worker):
        pass


class FirmwareTask(Task):
    host = [build_server]
    
    def make_on_worker(self, worker):
        pass

class GitBuildTask(Task):
    GIT_REPO = None
    GIT_BRANCH = None
    
    def make_on_worker(self, worker):
        with worker.connect() as conn:
            check_output = conn.modules.subprocess.check_output
            tmpdir = conn.modules.tempfile.mkdtemp()
            conn.modules.os.chdir(tmpdir)
            check_output(["git", "clone", self.GIT_REPO, "-b", self.GIT_BRANCH, "--recurse-submodules"])
            repodir = conn.modules.os.path.join(tmpdir, os.path.basename(self.GIT_REPO))
            if repodir.endswith(".git"):
                repodir = repodir[:-4]
            conn.modules.os.chdir(repodir)
            self._build(worker, conn, repodir)
    
    def _build(self, worker, conn, dirname):
        raise NotImplementedError()


class OpenNITask(GitBuildTask):
    hosts = [build_server, sdk64, sdk32]
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNI2.git"
    GIT_BRANCH = "develop"
    
    def _build(self, worker, conn, dirname):
        conn.modules.os.chdir(conn.modules.os.path.join(dirname, "Packaging"))
        check_output = conn.modules.subprocess.check_output
        for plat in worker.platforms:
            check_output(["python", "ReleaseVersion.py", "x86"])


class NiteTask(GitBuildTask):
    pass

class PythonWrapperTask(GitBuildTask):
    pass

class CrayolaTask(Task):
    pass


fw_task = FirmwareTask()
openni_task = OpenNITask()
nite_task = NiteTask([openni_task])
wrapper_task = PythonWrapperTask([nite_task, openni_task])
crayola_task = CrayolaTask([fw_task, wrapper_task])


crayola_task.make()






















