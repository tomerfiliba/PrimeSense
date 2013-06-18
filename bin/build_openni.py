from cbinder.generator import CBindings
 

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

class OpenNI2Builder(CBindings):
    @classmethod
    def build(cls):
        builder = cls(["../res/include/OniCAPI.h", "../res/include/PSLink.h", "../res/include/PS1080.h"], 
            includes = ["OniCEnums.h", "OniCProperties.h", "OniCTypes.h", "OniVersion.h", "PrimeSense.h"], 
            predefs = predefs, 
            prelude = prelude, 
            debug = True
            )
        builder.export("../primelib/_openni2.py")

    def filter_type(self, tp):
        return tp.name not in ["bool", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", 
            "uint16_t", "uint32_t", "uint64_t"]

    def filter_func(self, func):
        return "Android" not in func.name

    def emit_prelude(self, m):
        #copy("../cbinder/lib.py", "../primelib/cbinder_lib.py")
        m.from_("primelib.utils", "CEnum", "UnloadedDLL")

    def before_funcs_hook(self, m):
        m.import_("functools")
        m.from_("primelib.utils", "OpenNIError")
        m.sep()
        with m.def_("oni_call", "func"):
            m.stmt("@functools.wraps(func)")
            with m.def_("wrapper", "*args"):
                m.stmt("res = func(*args)")
                with m.if_("res != OniStatus.ONI_STATUS_OK"):
                    m.stmt("msg = oniGetExtendedError()")
                    with m.if_("not msg"):
                        m.stmt("msg = ''")
                    m.raise_("OpenNIError(res, msg.strip())")
                m.return_("res")
            m.return_("wrapper")

    def emit_func(self, m, func):
        if func.type.name == "OniStatus":
            m.stmt("@oni_call")
        CBindings.emit_func(self, m, func)


if __name__ == "__main__":
    OpenNI2Builder.build()


