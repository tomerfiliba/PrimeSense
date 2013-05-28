from cbinder import CBindings

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
        builder = cls("../res/include/OniCAPI.h", 
            includes = ["OniCEnums.h", "OniCProperties.h", "OniCTypes.h", "OniVersion.h"], 
            predefs = predefs, 
            prelude = prelude)
        builder.export("../primelib/_openni2.py")

    def filter_type(self, tp):
        return tp.name not in ["bool", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", 
            "uint16_t", "uint32_t", "uint64_t"]

    def before_funcs_hook(self, m):
        m.import_("functools")
        m.from_("primelib.utils", "OpenNIError")
        m.sep()
        with m.def_("oni_call", "func"):
            m.stmt("@functools.wraps(func)")
            with m.def_("wrapper", "*args"):
                m.stmt("res = func(*args)")
                with m.if_("res != OniStatus.ONI_STATUS_OK"):
                    m.raise_("OpenNIError(res, oniGetExtendedError().strip())")
                m.return_("res")
            m.return_("wrapper")

    def emit_func(self, m, func):
        if func.type.name == "OniStatus":
            m.stmt("@oni_call")
        CBindings.emit_func(self, m, func)

class Nite2Builder(CBindings):
    @classmethod
    def build(cls):
        builder = cls("../res/include/NiteCAPI.h", 
            includes = ["NiteCEnums.h", "NiteCTypes.h", "NiteVersion.h", 
                "OniCAPI.h", "OniCEnums.h", "OniCProperties.h", "OniCTypes.h", "OniVersion.h"], 
            predefs = predefs, 
            prelude = prelude)
        builder.export("../primelib/_nite2.py")

    def filter_type(self, tp):
        return tp.name not in ["bool", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", 
            "uint16_t", "uint32_t", "uint64_t"]
    
    def filter_func(self, func):
        return not func.name.lower().startswith("oni")
    
    def before_funcs_hook(self, m):
        m.import_("functools")
        m.from_("primelib.utils", "NiteError")
        m.sep()
        with m.def_("nite_call", "func"):
            m.stmt("@functools.wraps(func)")
            with m.def_("wrapper", "*args"):
                m.stmt("res = func(*args)")
                with m.if_("res != NiteStatus.NITE_STATUS_OK"):
                    m.raise_("NiteError(res)")
                m.return_("res")
            m.return_("wrapper")
    
    def emit_func(self, m, func):
        if func.type.name == "NiteStatus":
            m.stmt("@nite_call")
        CBindings.emit_func(self, m, func)



if __name__ == "__main__":
    OpenNI2Builder.build()
    Nite2Builder.build()


