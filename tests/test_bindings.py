import unittest
import subprocess
import os
import primelib
import inspect
import tokenize
import logging
import ConfigParser
from io import StringIO
from cbinder.generator import delimiters

config = ConfigParser.ConfigParser()
config.read("../bin/sources.ini")


class TestBindings(unittest.TestCase):
    GEN_DIR = primelib.__path__[0]
    GEN_ONI = os.path.join(GEN_DIR, "_openni2.py")
    GEN_NITE = os.path.join(GEN_DIR, "_nite2.py")

    def test_openni2_bindings(self):
        if os.path.exists(self.GEN_ONI):
            os.unlink(self.GEN_ONI)
        subprocess.check_call(["python", "../bin/build_openni.py"])
        self.assertTrue(os.path.exists(self.GEN_ONI))
        
        from primelib import _openni2
        from primelib import openni2
        
        openni2.initialize()
        ver = openni2.get_version()
        openni2.unload()

        self.assertEqual(ver.major, openni2.c_api.ONI_VERSION_MAJOR)
        self.assertEqual(ver.minor, openni2.c_api.ONI_VERSION_MINOR)

        h_file = os.path.join(config.get("headers", "openni_include_dir"), "OpenNI.h")

        self.check_unexposed_functions(openni2, _openni2, h_file, ["oniGetExtendedError"])
        self.check_missing_names_by_prefix(openni2, h_file, "DEVICE_PROPERTY_", "ONI_")
        self.check_missing_names_by_prefix(openni2, h_file, "STREAM_PROPERTY_", "ONI_")
        

    def _get_identifiers(self, mod):
        source = inspect.getsource(mod)
        g = tokenize.generate_tokens(StringIO(unicode(source)).readline)
        return set(tokval for toktype, tokval, _, _, _  in g if toktype == tokenize.NAME)
    
    def _get_unexposed_functions(self, wrapper_mod, autgen_mod):
        identifiers = self._get_identifiers(wrapper_mod)
        for func in autgen_mod.all_funcs:
            if func.__name__ not in identifiers:
                yield func.__name__
    
    def check_unexposed_functions(self, wrapper_mod, autgen_mod, hfile, to_ignore = []):
        hfile_tokens = set(delimiters.split(open(hfile, "r").read()))
        fail = False
        for func in self._get_unexposed_functions(wrapper_mod, autgen_mod):
            if func in to_ignore:
                continue
            if func in hfile_tokens:
                fail = True
                logging.error("%s is not exposed by wrapper <<< FIX ME", func)
            else:
                logging.warning("%s is missing from wrapper (not exposed in %s either)", func, os.path.basename(hfile))
        
        if fail:
            self.fail("Found unexposed API function")
    
    def check_missing_names_by_prefix(self, wrapper_mod, hfile, prefix, pyprefix):
        identifiers = self._get_identifiers(wrapper_mod)
        hfile_tokens = set(delimiters.split(open(hfile, "r").read()))
        
        fail = False
        for tok in hfile_tokens:
            if tok.startswith(prefix):
                pytok = pyprefix + tok
                if pytok not in identifiers:
                    logging.error("%s is missing", pytok)
                    fail = True

        if fail:
            self.fail("Found unexposed properties")
    
    def test_nite_bindings(self):
        if os.path.exists(self.GEN_ONI):
            os.unlink(self.GEN_ONI)
        subprocess.check_call(["python", "../bin/build_openni.py"])
        self.assertTrue(os.path.exists(self.GEN_ONI))

        if os.path.exists(self.GEN_NITE):
            os.unlink(self.GEN_NITE)
        subprocess.check_call(["python", "../bin/build_nite.py"])
        self.assertTrue(os.path.exists(self.GEN_NITE))

        from primelib import _nite2
        from primelib import nite2

        nite2.initialize()
        ver = nite2.get_version()
        nite2.unload()

        self.assertEqual(ver.major, nite2.c_api.NITE_VERSION_MAJOR)
        self.assertEqual(ver.minor, nite2.c_api.NITE_VERSION_MINOR)

        h_file = os.path.join(config.get("headers", "nite_include_dir"), "NiTE.h")
        self.check_unexposed_functions(nite2, _nite2, h_file)


if __name__ == "__main__":
    unittest.main()



