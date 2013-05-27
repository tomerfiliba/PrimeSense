import unittest
import subprocess
import os
import primelib


class TestBindings(unittest.TestCase):
    GEN_DIR = primelib.__path__[0]
    GEN_ONI = os.path.join(GEN_DIR, "_openni2.py")
    GEN_NITE = os.path.join(GEN_DIR, "_nite2.py")

    def test_cbinder(self):
        if os.path.exists(self.GEN_ONI):
            os.unlink(self.GEN_ONI)
        if os.path.exists(self.GEN_NITE):
            os.unlink(self.GEN_NITE)
        subprocess.check_call(["python", "../bin/build.py"])
        self.assertTrue(os.path.exists(self.GEN_ONI))
        self.assertTrue(os.path.exists(self.GEN_NITE))
        
        from primelib import _openni2
        from primelib import _nite2
        from primelib import openni2
        from primelib import nite2
        
        openni2.initialize("../res/redist")
        print openni2.get_version()
        openni2.unload()
        
        nite2.initialize("../res/redist")
        print nite2.get_version()
        nite2.unload()



if __name__ == "__main__":
    unittest.main()



