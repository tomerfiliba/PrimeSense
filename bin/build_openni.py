import os
import ConfigParser
from cbinder.generator import CBindings

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'sources.ini'))


predefs = {
    "ONI_C" : ((), ""), 
    "ONI_C_API" : ((), ""), 
    "ONI_C_API_EXPORT" : ((), ""),
    "ONI_C_API_IMPORT" : ((), ""),
    "ONI_API_IMPORT" : ((), ""),
    "ONI_API_EXPORT" : ((), ""),
    "ONI_CPP_API_EXPORT" : ((), ""),
    "ONI_CPP_API_IMPORT" : ((), ""),
    "ONI_CALLBACK_TYPE" : ((), ""),
    "NITE_API" : ((), ""),
}

prelude = [
    "typedef int bool;",
    "typedef signed char int8_t;",
    "typedef unsigned char uint8_t;",
    "typedef signed short int16_t;",
    "typedef unsigned short uint16_t;",
    "typedef signed long int32_t;",
    "typedef unsigned long uint32_t;",
    "typedef signed long long int64_t;",
    "typedef unsigned long long uint64_t;",
]

HFILES = [
    "OniCAPI.h", "PS1080.h", "PSLink.h",
]
HFILES = [os.path.join(config.get("headers", "openni_include_dir"), f) for f in HFILES]
INCLUDES = [
    "OniCEnums.h", "OniCProperties.h", "OniCTypes.h", "OniVersion.h", "PrimeSense.h",
]

class OpenNI2Builder(CBindings):
    @classmethod
    def build(cls):
        builder = cls(HFILES, includes = INCLUDES, predefs = predefs, prelude = prelude)
        builder.export("../primesense/_openni2.py")

    def filter_type(self, tp):
        return tp.name not in ["bool", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", 
            "uint16_t", "uint32_t", "uint64_t"]

    def filter_func(self, func):
        return "Android" not in func.name

    def emit_prelude(self, m):
        #copy("../cbinder/lib.py", "../primesense/cbinder_lib.py")
        m.from_("primesense.utils", "CEnum", "UnloadedDLL")

    def before_funcs_hook(self, m):
        m.import_("functools")
        m.from_("primesense.utils", "OpenNIError")
        m.sep()
        with m.def_("oni_call", "func"):
            m.stmt("@functools.wraps(func)")
            with m.def_("wrapper", "*args"):
                m.stmt("res = func(*args)")
                with m.if_("res != OniStatus.ONI_STATUS_OK"):
                    m.stmt("msg = oniGetExtendedError()")
                    with m.if_("not msg"):
                        m.stmt("msg = ''")
                    m.stmt("buf = ctypes.create_string_buffer(1024)")
                    m.stmt("rc = _oniGetLogFileName(buf, ctypes.sizeof(buf))")
                    with m.if_("rc == OniStatus.ONI_STATUS_OK"):
                        m.stmt("logfile = buf.value")
                    with m.else_():
                        m.stmt("logfile = None")
                    m.raise_("OpenNIError(res, msg.strip(), logfile)")
                m.return_("res")
            m.return_("wrapper")

    def emit_func(self, m, func):
        if func.type.name == "OniStatus":
            m.stmt("@oni_call")
        CBindings.emit_func(self, m, func)


if __name__ == "__main__":
    OpenNI2Builder.build()


