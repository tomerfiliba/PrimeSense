from cbinder.generator import CBindings
from build_openni import predefs, prelude


class Nite2Builder(CBindings):
    @classmethod
    def build(cls):
        builder = cls(["../res/include/NiteCAPI.h"], 
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

    def emit_prelude(self, m):
        #copy("../cbinder/lib.py", "../primelib/cbinder_lib.py")
        m.from_("primelib.utils", "CEnum", "UnloadedDLL")
    
    def emit_struct_decl(self, m, tp):
        if tp.name.lower().startswith("oni"):
            m.from_("_openni2", tp.name)
        else:
            CBindings.emit_struct_decl(self, m, tp)
    
    def emit_struct_fields(self, m, tp):
        if not tp.name.lower().startswith("oni"):
            CBindings.emit_struct_fields(self, m, tp)

    def emit_union_decl(self, m, tp):
        if tp.name.lower().startswith("oni"):
            m.from_("_openni2", tp.name)
        else:
            CBindings.emit_union_decl(self, m, tp)
    
    def emit_union_fields(self, m, tp):
        if not tp.name.startswith("Oni"):
            CBindings.emit_union_fields(self, m, tp)

    def emit_enum(self, m, tp):
        if tp.name.lower().startswith("oni"):
            m.from_("_openni2", tp.name)
        else:
            CBindings.emit_enum(self, m, tp)
    
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
    Nite2Builder.build()


