import unittest
import subprocess
import os
import sys


class TestBindings(unittest.TestCase):
    GEN_FILE = "../primelib/_openni2.py"
    
    def test_cbinder(self):
        if os.path.exists(self.GEN_FILE):
            os.unlink(self.GEN_FILE)
        subprocess.check_call(["python", "../bin/build.py"])
        self.assertTrue(os.path.exists(self.GEN_FILE))
        
        sys.path.insert(0, os.path.dirname(self.GEN_FILE))
        import _openni2
        import openni2



if __name__ == "__main__":
    unittest.main()
