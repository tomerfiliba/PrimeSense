import os
import logging
from contextlib import contextmanager
from hosts import build_hosts, Platform

logger = logging.getLogger("build")
logging.basicConfig(level = logging.INFO)

class BaseBuilder(object):
    GIT_REPO = None
    GIT_BRANCH = None
    PLATFORMS = [Platform.LIN64]

    def __init__(self, hostinfo):
        self.hostinfo = hostinfo
    
    def main(self):
        for host in build_hosts:
            for plat in self.PLATFORMS:
                if plat in host.platforms:
                    with self.hostinfo.connect() as conn:
                        
                        self.cd()
                        self.checkout(conn, plat)
                        self.build(conn, plat)
                        
    
    def run(self, *args):
        return self.conn.modules.subprocess.check_output(args)
    def git(self, *args):
        return self.run("git", *args)
    def pip(self, *args):
        return self.run("pip", *args)
    @contextmanager
    def cd(self, dirname):
        curr = self.conn.modules.os.getcwd()
        self.conn.modules.os.chdir(dirname)
        try:
            yield self.conn.modules.os.getcwd()
        finally:
            self.conn.modules.os.chdir(curr)
    
    def build(self):
        tmpdir = self.conn.modules.tempfile.mkdtemp()
        with self.cd(tmpdir):
            self.checkout()


class OpenNI2Builder(BaseBuilder):
    GIT_REPO = "ssh://git/localhome/GIT/Software/OpenNI2.git"
    GIT_BRANCH = "develop"
    PLATFORMS = ["LIN-64", "LIN-Arm", "src", "android"]

    def checkout(self):
        self.git("clone", self.GIT_REPO, )
        outdir = os.path.basename(self.GIT_REPO).replace(".git", "")
        with self.cd(outdir):
            self.git("checkout", self.GIT_BRANCH)
            self.git("submodule", "update", "--init", "--recursive")
    
    def build(self, flavor):
        with self.cd("OpenNI2/Packaging"):
            self.run("python", "ReleaseVersion.py", flavor)
    

if __name__ == "__main__":
    b = OpenNI2Builder()
    b.main()

















