import sys
import os
import ConfigParser
from plumbum import local, cli, FG
from plumbum.utils import copy

HERE = local.path(__file__).dirname
ROOT = HERE.up()

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'sources.ini'))

class BuildPackage(cli.Application):
    upload = cli.Flag("--upload")
    dont_register = cli.Flag("--dont-register")
    
    def main(self):
        local.cwd.chdir(HERE)
        sys.path.insert(0, str(ROOT))
        local.env["PYTHONPATH"] = ROOT

        local.python("build_openni.py")
        local.python("build_nite.py")
        
        from primesense import openni2, nite2
        
        dist = local.path("../dist")
        dist.delete()
        dist.mkdir()
        
        tmp = local.path("tmp")
        tmp.delete()
        tmp.mkdir()
        
        copy("../primesense", tmp / "primesense")
        copy("MANIFEST.in", tmp)
        copy("../LICENSE", tmp)
        copy("../README.rst", tmp)
        
        ver = "%s.%s.%s.%s-%s" % (openni2.c_api.ONI_VERSION_MAJOR, openni2.c_api.ONI_VERSION_MINOR, 
            openni2.c_api.ONI_VERSION_MAINTENANCE, openni2.c_api.ONI_VERSION_BUILD, config.get("pypi", "release"))
        
        data = local.path("setup_template.py").read().replace("$VERSION$", ver)
        (tmp / "setup.py").write(data)
        
        with local.cwd(tmp):
            if self.upload:
                # copy pypirc to ~
                orig = local.path("~/.pypirc")
                if orig.exists():
                    copy(orig, "~/.pypirc-openni-wrapper")
                    restore = True
                copy(ROOT / "_pypirc", "~/.pypirc")
                try:
                    local.python["setup.py", "sdist", "--formats=zip,gztar", 
                        None if self.dont_register else "register", "upload"] & FG
                finally:
                    if restore:
                        copy("~/.pypirc-openni-wrapper", orig)
            else:
                local.python["setup.py", "sdist", "--formats=zip,gztar"] & FG
        
        for fn in tmp / "dist" // "*":
            fn.move(dist)



if __name__ == "__main__":
    BuildPackage.run()



