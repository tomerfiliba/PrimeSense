from plumbum import local, cli
from plumbum.utils import copy, delete


class BuildPackage(cli.Application):
    upload = cli.Flag("--upload")
    def main(self):
        local.python("build_openni.py")
        local.python("build_nite.py")
        
        from primelib import openni2
        
        dist = local.path("../dist")
        dist.delete()
        dist.mkdir()
        
        tmp = local.path("tmp")
        tmp.delete()
        tmp.mkdir()
        
        copy("../primelib", tmp / "primelib")
        copy("MANIFEST.in", tmp)
        copy("../LICENSE", tmp)
        copy("../README.rst", tmp)
        
        ver = "%s.%s.%s.%s" % (openni2.c_api.ONI_VERSION_MAJOR, openni2.c_api.ONI_VERSION_MINOR, 
            openni2.c_api.ONI_VERSION_MAINTENANCE, openni2.c_api.ONI_VERSION_BUILD)
        data = local.path("setup_template.py").read().replace("$VERSION$", ver)
        (tmp / "setup.py").write(data)
        
        with local.cwd(tmp):
            if self.upload:
                local.python("setup.py", "sdist", "--formats=zip,gztar", "register", "upload")
            else:
                local.python("setup.py", "sdist", "--formats=zip,gztar")
        
        for fn in tmp / "dist" // "*":
            fn.move(dist)



if __name__ == "__main__":
    BuildPackage.run()



