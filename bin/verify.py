import os
import inspect
import tokenize
from io import StringIO
from primelib import _openni2, openni2, _nite2, nite2
from cbinder.generator import delimiters


def get_identifiers(source):
    g = tokenize.generate_tokens(StringIO(unicode(source)).readline)
    return set(tokval for toktype, tokval, _, _, _  in g if toktype == tokenize.NAME)

def get_unexposed_functions(wrapper_mod, autgen_mod):
    identifiers = get_identifiers(inspect.getsource(wrapper_mod))
    for func in autgen_mod.all_funcs:
        if func.__name__ not in identifiers:
            yield func.__name__

def show_unexposed_functions(wrapper_mod, autgen_mod, hfile, to_ignore = []):
    first_time = True
    hfile_tokens = set(delimiters.split(open(hfile, "r").read()))
    for func in get_unexposed_functions(wrapper_mod, autgen_mod):
        if func in to_ignore:
            continue
        if func in hfile_tokens:
            func += " <<<< FIX ME"
        else:
            func += " (not exposed in %s)" % (os.path.basename(hfile),)
        if first_time:
            print "%s\n======================" % (wrapper_mod.__name__,)
            first_time = False
        print "    ", func
    if not first_time:
        print

if __name__ == "__main__":
    show_unexposed_functions(openni2, _openni2, "../res/include/OpenNI.h", ["oniGetExtendedError"])
    show_unexposed_functions(nite2, _nite2, "../res/include/NiTE.h")



