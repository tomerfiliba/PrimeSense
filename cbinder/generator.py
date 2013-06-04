import os
import re
import itertools
import time
from pycparser import CParser, c_ast
from srcgen.python import PythonModule
from collections import OrderedDict


include_pattern = re.compile(r'^\s*#\s*include\s*[<"](.+?)[">]\s*$', re.IGNORECASE)
define_pattern = re.compile(r'^\s*#\s*define\s+(\w+)(?:\((.*?)\))?\s*(.*)\s*$', re.IGNORECASE)
undef_pattern = re.compile(r'^\s*#\s*undef\s+(\w+)\s*$', re.IGNORECASE)
if_pattern = re.compile(r'^\s*#\s*if\s+(.+)\s*$', re.IGNORECASE)
elif_pattern = re.compile(r'^\s*#\s*if\s+(.+)\s*$', re.IGNORECASE)
else_pattern = re.compile(r'^\s*#\s*else\s*$', re.IGNORECASE)
endif_pattern = re.compile(r'^\s*#\s*endif\s*$', re.IGNORECASE)
ifdef_pattern = re.compile(r'^\s*#\s*ifdef\s+(\w+)\s*$', re.IGNORECASE)
ifndef_pattern = re.compile(r'^\s*#\s*ifndef\s+(\w+)\s*$', re.IGNORECASE)
ml_comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
sl_comment_pattern = re.compile(r'//.*?\n')
delimiters = re.compile(r'''([!%^&*()[\]{}<>;,:+\-/?:\s"'|=])''')
identifier_pattern = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')

def strip_comments(text):
    text = text.replace("\\\n", " ")
    return sl_comment_pattern.sub("\n", ml_comment_pattern.sub("", text))

def autorepr(cls):
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join("%s = %r" % (k, v) 
            for k, v in sorted(self.__dict__.items()) if not k.startswith("_") and v))
    cls.__repr__ = __repr__
    return cls

@autorepr
class CFunc(object):
    def __init__(self, name, args, type):      # @ReservedAssignment
        self.name = name
        self.args = args
        self.type = type

@autorepr
class CEnum(object):
    def __init__(self, name, members):
        self.name = name
        self.members = members
    def get_ctype(self):
        return "ctypes.c_int"

@autorepr
class CStruct(object):
    def __init__(self, name, members, packed = False):
        self.name = name
        self.members = members
        self.packed = packed
    def get_ctype(self):
        return self.name

@autorepr
class CUnion(object):
    def __init__(self, name, members, packed = False):
        self.name = name
        self.members = members
        self.packed = packed
    def get_ctype(self):
        return self.name

@autorepr
class CTypedef(object):
    def __init__(self, name, type):         # @ReservedAssignment
        self.name = name
        self.type = type
    def get_ctype(self):
        return self.name

@autorepr
class CType(object):
    builtin_ctypes = {
        # Misc
        "_Bool" : "c_bool", "bool" : "c_bool", "wchar_t" : "c_wchar", "wchar" : "c_wchar",
        "float" : "c_float", "double" : "c_double", "long double" : "c_longdouble",
        # 8
        "char" : "c_char", "signed char" : "c_byte", "int8" : "c_byte", "int8_t" : "c_byte", "__int8" : "c_byte",
        "unsigned char" : "c_ubyte", "uchar" : "c_ubyte", "uchar_t" : "c_ubyte", "uint8" : "c_ubyte", 
        "uint8_t" : "c_ubyte", "unsigned __int8" : "c_byte",
        # 16
        "short" : "c_short", "signed short" : "c_short", "int16" : "c_short", "int16_t" : "c_short", "__int16" : "c_short",
        "unsigned short" : "c_ushort", "ushort" : "c_ushort", "ushort_t" : "c_ushort", "uint16" : "c_ushort",
        "uint16_t" : "c_ushort", "unsigned __int16" : "c_ushort",
        "short int" : "c_short",
        # 32
        "int" : "c_int", "signed int" : "c_int", "int32" : "c_int", "int32_t" : "c_int", "__int32" : "c_int",
        "unsigned int" : "c_uint", "uint" : "c_uint", "uint_t" : "c_uint", "uint32" : "c_uint", 
        "uint32_t" : "c_uint", "unsigned __int32" : "c_uint", "long" : "c_long", "signed long" : "c_long", 
        "unsigned long" : "c_ulong", "ulong" : "c_ulong", "ulong_t" : "c_ulong",
        "long int" : "c_long",
        # 64
        "long long" : "c_longlong", "signed long long" : "c_longlong", "int64" : "c_longlong", "int64_t" : "c_longlong",
        "__int64" : "c_longlong", "unsigned long long" : "c_ulonglong", "ulonglong" : "c_ulonglong", 
        "ulonglong_t" : "c_ulonglong", "unsigned __int64" : "c_longlong", "uint64" : "c_ulonglong",
        "uint64_t" : "c_ulonglong", "unsigned __int64" : "c_ulonglong",
    }
    
    def __init__(self, name, indir_levels = 0, subscripts = None, quals = None, calling_convention = "auto"):
        self.name = name
        self.indir_levels = indir_levels
        self.subscripts = subscripts
        self.quals = None
        self.calling_convention = calling_convention
    
    def get_ctype(self):
        if self.indir_levels == 1 and not self.quals:
            if self.name == "char":
                return "ctypes.c_char_p"
            elif self.name == "wchar":
                return "ctypes.c_wchar_p"
            elif self.name == "void":
                return "ctypes.c_void_p"
        
        if isinstance(self.name, tuple):
            restype, argtypes = self.name
            restype = restype.get_ctype()
            if restype == "void":
                restype = None
            
            if self.calling_convention == "auto":
                callingconv = "_get_calling_conv"
            elif self.calling_convention == "stdcall":
                callingconv = "ctypes.WINFUNCTYPE"
            elif self.calling_convention == "cdecl":
                callingconv = "ctypes.CFUNCTYPE"
            else:
                raise ValueError("Unknown calling convention %r" % (self.calling_convention))
            
            tp = "%s(%s, %s)" % (callingconv, restype, ", ".join(a.get_ctype() for _, a in argtypes))
            for _ in range(self.indir_levels - 1):
                tp = "ctypes.POINTER(%s)" % (tp)
        else:
            key = (self.quals if self.quals else "") + self.name
            if key in self.builtin_ctypes:
                tp = "ctypes." + self.builtin_ctypes[key]
            else:
                tp = self.name
            for _ in range(self.indir_levels):
                tp = "ctypes.POINTER(%s)" % (tp)
        
        if self.subscripts:
            for subs in self.subscripts:
                tp = "(%s * %s)" % (tp, subs)
        return tp
    
    def as_pretty_type(self, argname):
        return ("%s %s%s %s%s" % (self.quals if self.quals else "", self.name, "*" * self.indir_levels, argname, 
            ("".join("[%s]" % (subs,) for subs in self.subscripts) if self.subscripts else ""))).strip()

class CtypesGenVisitor(c_ast.NodeVisitor):
    def __init__(self, module):
        self.module = module
        self.counter = itertools.count(0)

    def eval_const(self, node):
        if isinstance(node, c_ast.UnaryOp):
            expr = "(%s%s)" % (node.op, self.eval_const(node.expr))
            try:
                return eval(expr)
            except Exception:
                return expr
        elif isinstance(node, c_ast.BinaryOp):
            expr = "(%s %s %s)" % (self.eval_const(node.left), node.op, self.eval_const(node.right))
            try:
                return eval(expr)
            except Exception:
                return expr
        elif isinstance(node, c_ast.ID):
            return node.name
        elif isinstance(node.value, c_ast.ID):
            return node.value.name
        elif node.value.startswith("0x"):
            return int(node.value, 16)
        elif node.value.startswith("0"):
            return int(node.value, 8)
        elif node.value.isdigit():
            return int(node.value)
        else:
            raise TypeError(node.value)

    def type_to_ctype(self, node, quals = None, indir_levels = 0, subscripts = None):
        if isinstance(node, c_ast.TypeDecl):
            return self.type_to_ctype(node.type, node.quals, indir_levels, subscripts)
        elif isinstance(node, c_ast.PtrDecl):
            return self.type_to_ctype(node.type, node.quals, indir_levels + 1, subscripts)
        elif isinstance(node, c_ast.IdentifierType):
            return CType(" ".join(node.names), indir_levels = indir_levels, quals = quals if quals else None, 
                subscripts = subscripts if subscripts else None)
        elif isinstance(node, c_ast.FuncDecl):
            rettype = self.type_to_ctype(node.type)
            args = [(a.name, self.type_to_ctype(a.type)) for a in node.args.params]
            return CType((rettype, args), indir_levels = indir_levels, quals = quals if quals else None, 
                subscripts = subscripts if subscripts else None)
        elif isinstance(node, c_ast.ArrayDecl):
            if subscripts:
                subscripts.append(self.eval_const(node.dim))
            else:
                subscripts = [self.eval_const(node.dim)]
            return self.type_to_ctype(node.type, quals, indir_levels, subscripts)
        elif isinstance(node, (c_ast.Struct, c_ast.Union)):
            return CType(node.name, indir_levels = indir_levels, quals = quals if quals else None, 
                subscripts = subscripts if subscripts else None)
        else:
            node.show(showcoord = True)
            raise TypeError(node)
    
    def visit_Decl(self, node):
        if isinstance(node.type, c_ast.FuncDecl):
            if node.type.args:
                args = [(a.name, self.type_to_ctype(a.type)) for a in node.type.args.params]
            else:
                args = []
            self.module.funcs[node.name] = CFunc(node.name, args, self.type_to_ctype(node.type.type))
        else:
            self.generic_visit(node)
    
    def create_enum(self, node):
        members = []
        for e in node.values.enumerators:
            if e.value is None:
                v = members[-1][1] + 1 if members else 0
            else:
                v = self.eval_const(e.value)
            members.append((e.name, v))
        enum = CEnum(node.name, members)
        if not enum.name:
            enum.name = "_anon_enum_%d" % (self.counter.next(),)
        self.module.types[enum.name] = enum
        return enum.name
    
    def create_struct(self, node):
        members = []
        if node.decls:
            for m in node.decls:
                members.append((m.name, self.type_to_ctype(m.type)))
        struct = CStruct(node.name, members, packed = node.coord.line in self.module.packed_lines)
        if not struct.name:
            struct.name = "_anon_struct_%d" % (self.counter.next(),)
        self.module.types[struct.name] = struct
        return struct.name

    def create_union(self, node):
        members = []
        for m in node.decls:
            members.append((m.name, self.type_to_ctype(m.type)))
        union = CUnion(node.name, members, packed = node.coord.line in self.module.packed_lines)
        if not union.name:
            union.name = "_anon_union_%d" % (self.counter.next(),)
        self.module.types[union.name] = union
        return union.name
    
    def _resolve_typedef(self, node, realname, newname):
        if realname.startswith("_anon_"):
            obj = self.module.types.pop(realname)
            obj.name = newname
            self.module.types[obj.name] = obj
            if isinstance(obj, (CStruct, CUnion)):
                obj.packed |= node.coord.line in self.module.packed_lines
        elif newname != realname:
            self.module.types[newname] = CTypedef(newname, CType(realname))
    
    def visit_Typedef(self, node):
        if isinstance(node.type, c_ast.TypeDecl):
            node2 = node.type.type
            if isinstance(node2, c_ast.Enum):
                self._resolve_typedef(node, self.create_enum(node2), node.name)
            elif isinstance(node2, c_ast.Struct):
                self._resolve_typedef(node, self.create_struct(node2), node.name)
            elif isinstance(node2, c_ast.Union):
                self._resolve_typedef(node, self.create_union(node2), node.name)
            elif isinstance(node2, c_ast.IdentifierType):
                self.module.types[node.name] = CTypedef(node.name, self.type_to_ctype(node2))
            else:
                raise TypeError(node2)
        else:
            self.module.types[node.name] = CTypedef(node.name, self.type_to_ctype(node.type))
    
    def visit_Enum(self, node):
        self.create_enum(node)
    def visit_Struct(self, node):
        self.create_struct(node)
    def visit_Union(self, node):
        self.create_union(node)


class CBindings(object):
    def __init__(self, hfiles, includes = [], predefs = {}, prelude = [], debug = False):
        self.hfiles = hfiles
        self.types = OrderedDict()
        self.funcs = OrderedDict()
        self.macros = OrderedDict()
        self.macros.update(predefs)
        
        lines = []
        self._included = set()
        for hfile in hfiles:
            lines.extend(self._load_with_includes(hfile, includes))
        lines[0:0] = prelude
        text = self._preprocess(lines)
        if debug:
            with open("tmp.c", "w") as f:
                f.write(text)
        
        self.packed_lines = set(self._get_packed_regions(text))
        
        parser = CParser()
        ast = parser.parse(text, "tmp.c")
        visitor = CtypesGenVisitor(self)
        visitor.visit(ast)
    
    def _get_packed_regions(self, text):
        lines = text.splitlines()
        in_packed = False
        for i, l in enumerate(lines, 1):
            l = l.strip().lower()
            if not l.startswith("#pragma") or "pack" not in l:
                if in_packed:
                    yield i
                continue
            
            if "push" in l:
                if in_packed:
                    raise ValueError("Detected #pragma pack without a matching pop")
                in_packed = True
            elif "pop" in l:
                if not in_packed:
                    raise ValueError("Detected #pragma pop without a matching pack")
                in_packed = False
            else:
                raise ValueError("Unknown #pragma pack option %r" % (l,))
        if in_packed:
            raise ValueError("Detected #pragma pack without a matching pop")
    
    def _load_with_includes(self, rootfile, includes):
        path = os.path.dirname(os.path.abspath(rootfile))
        lines = strip_comments(open(rootfile, "rU").read()+"\n\n\n").splitlines()
        i = -1
        while i + 1 < len(lines):
            i += 1
            line = lines[i]
            m = include_pattern.match(line)
            if not m:
                continue
            del lines[i]
            i -= 1
            filename = m.group(1)
            if filename not in includes or filename in self._included:
                continue
            self._included.add(filename)
            lines2 = strip_comments(open(os.path.join(path, filename), "rU").read()+"\n\n\n").splitlines()
            lines[i+1:i+1] = lines2
        return [l.strip() for l in lines if l.strip()]
    
    def _preprocess(self, lines):
        lines2 = []
        for line in lines:
            m = define_pattern.match(line)
            if m:
                name, args, body = m.groups()
                self.macros[name] = ([a.strip() for a in args.split(",")] if args else (), body)
                continue
            m = undef_pattern.match(line)
            if m:
                name = m.group(1)
                self.macros.pop(name, None)
                continue
            if ifdef_pattern.match(line) or ifndef_pattern.match(line) or endif_pattern.match(line):
                continue
            if if_pattern.match(line) or elif_pattern.match(line) or else_pattern.match(line):
                continue
            
            replaced = True
            while replaced:
                replaced = False
                tokens = delimiters.split(line)
                for name, (args, body) in self.macros.items():
                    while name in tokens:
                        replaced = True
                        i = tokens.index(name)
                        tokens[i:i+1] = body
                line = "".join(tokens).strip()
            lines2.append(line)
        return "\n".join(lines2)
    
    def export(self, filename):
        m = PythonModule()
        m.comment("Auto-generated file; do not edit directly", time.ctime())
        m.import_("sys")
        m.sep()
        m.import_("ctypes")
        m.from_("cbinder.lib", "CEnum", "UnloadedDLL")
        self.emit_prelude(m)
        m.sep()
        generated_macros = set()
        for name, (args, value) in self.macros.items():
            if not self.filter_macro(name, args, value):
                continue
            self.emit_macro(m, name, args, value, generated_macros)
        m.sep()
        with m.def_("_get_calling_conv", "*args"):
            with m.if_("sys.platform == 'win32'"):
                m.return_("ctypes.WINFUNCTYPE(*args)")
            with m.else_():
                m.return_("ctypes.CFUNCTYPE(*args)")
        m.sep()
        for t in self.types.values():
            if not self.filter_type(t):
                continue
            if isinstance(t, CEnum):
                self.emit_enum(m, t)
            elif isinstance(t, CStruct):
                self.emit_struct_decl(m, t)
            elif isinstance(t, CUnion):
                self.emit_union_decl(m, t)
            elif isinstance(t, CTypedef):
                pass
            else:
                raise TypeError(t)
        m.sep()
        for t in self.types.values():
            if not self.filter_type(t):
                continue
            if isinstance(t, CTypedef):
                self.emit_typedef(m, t)
        m.sep()
        for t in self.types.values():
            if not self.filter_type(t):
                continue
            if isinstance(t, CStruct):
                self.emit_struct_fields(m, t)
            elif isinstance(t, CUnion):
                self.emit_union_fields(m, t)
        m.sep()
        m.stmt("_dll = UnloadedDLL")
        for f in self.funcs.values():
            if self.filter_func(f):
                self.emit_func_unloaded(m, f)
        m.sep()
        with m.def_("load_dll", "dllname"):
            m.stmt("global _dll")
            with m.if_("_dll"):
                m.raise_("ValueError('DLL already loaded')")
            m.stmt("_dll = ctypes.CDLL(dllname)")
            m.sep()
            for f in self.funcs.values():
                if not self.filter_func(f):
                    continue
                self.emit_func_prototype(m, f)
                m.sep()
        
        self.before_funcs_hook(m)
        for f in self.funcs.values():
            if not self.filter_func(f):
                continue
            self.emit_func(m, f)

        m.stmt("all_types = [")
        for t in self.types.values():
            if not self.filter_type(t):
                continue
            m.stmt("    {0},", t.name)
        m.stmt("]")
        m.sep()
        m.stmt("all_funcs = [")
        for f in self.funcs.values():
            if not self.filter_func(f):
                continue
            m.stmt("    {0},", f.name)
        m.stmt("]")
        
        m.dump(filename)
        return m
    
    def filter_macro(self, name, args, value):
        return True
    
    def filter_type(self, tp):
        return True
    
    def filter_func(self, func):
        return True
    
    def emit_prelude(self, m):
        pass
    
    def emit_macro(self, m, name, args, value, generated_macros):
        if not value:
            return
        tokens = delimiters.split(value)
        identifiers = [tok for tok in tokens if identifier_pattern.match(tok)]
        if any((tok not in generated_macros and tok not in args) for tok in identifiers):
            return
        python_tokens = []
        while tokens:
            t = tokens.pop(0)
            if not t.strip():
                continue
            if t == "##":
                if not tokens or not python_tokens:
                    #print "unexpected end of tokens!"
                    return
                python_tokens[-1] = "str(%s)" % (python_tokens[-1],)
                python_tokens.append("+ str(%s)" % (tokens.pop(0),))
            elif t == "#":
                if not tokens:
                    #print "unexpected end of tokens!"
                    return
                python_tokens.append("str(%s)" % (tokens.pop(0),))
            else:
                python_tokens.append(t)
        
        code = " ".join(t.encode("unicode_escape") for t in python_tokens).strip()
        if args:
            code = "lambda %s: %s" % (", ".join(args), code)
        try:
            compile(code, "?", "eval")
        except Exception:
            return
        
        m.stmt("{0} = {1}", name, code)
        generated_macros.add(name)
    
    def emit_struct_decl(self, m, tp):
        with m.class_(tp.name, ["ctypes.Structure"]):
            if tp.packed:
                m.stmt("_packed_ = 1")
            for name, type in tp.members:         # @ReservedAssignment
                m.stmt("{0} = {1!r}", name, type.get_ctype())
            m.sep()
            with m.def_("__repr__", "self"):
                m.return_("'{0}({1})' % ({2})", tp.name, ", ".join("%s = %%r" % (n,) for n, _ in tp.members), 
                    ", ".join("self.%s" % (n,) for n, _ in tp.members))

    def emit_struct_fields(self, m, tp):
        m.stmt("{0}._fields_ = [", tp.name)
        for name, type in tp.members:         # @ReservedAssignment
            m.stmt("    ({0!r}, {1}),", name, type.get_ctype())
        m.stmt("]")
        m.sep()

    def emit_union_decl(self, m, tp):
        with m.class_(tp.name, ["ctypes.Union"]):
            if tp.packed:
                m.stmt("_packed_ = 1")
            for name, type in tp.members:         # @ReservedAssignment
                m.stmt("{0} = {1!r}", name, type.get_ctype())
            m.sep()
            with m.def_("__repr__", "self"):
                m.return_("'{0}({1})' % ({2})", tp.name, ", ".join("%s = %%r" % (n,) for n, _ in tp.members), 
                    ", ".join("self.%s" % (n,) for n, _ in tp.members))

    def emit_union_fields(self, m, tp):
        self.emit_struct_fields(m, tp)
    
    def emit_enum(self, m, tp):
        with m.class_(tp.name, ["CEnum"]):
            m.stmt("_names_ = {0!r}", dict(tp.members))
            m.stmt("_values_ = {0!r}", dict((v, k) for k, v in tp.members))
            for name, value in tp.members:
                m.stmt("{0} = {1}", name, value)
        self.emit_enum_top_level_fields(m, tp)
        m.sep()
    
    def emit_enum_top_level_fields(self, m, tp):
        if tp.name.startswith("_anon_"):
            for k, _ in tp.members:
                m.stmt("{0} = {1}.{0}", k, tp.name)
        m.sep()
    
    def emit_typedef(self, m, tp):
        m.stmt("{0} = {1}", tp.name, tp.type.get_ctype())
    
    def emit_func_prototype(self, m, func):
        m.stmt("global _{0}", func.name)
        m.stmt("_{0} = _dll.{0}", func.name)
        restype = func.type.get_ctype()
        if restype == "void":
            restype = None
        m.stmt("_{0}.restype  = {1}", func.name, restype)
        m.stmt("_{0}.argtypes = [{1}]", func.name, ", ".join(arg.get_ctype() for _, arg in func.args))
    
    def emit_func_unloaded(self, m, func):
        m.stmt("_{0} = UnloadedDLL", func.name)
    
    def before_funcs_hook(self, m):
        pass
    
    def emit_func(self, m, func):
        with m.def_(func.name, *(n for n, _ in func.args)):
            textargs = ", ".join("%s" % (arg.as_pretty_type(name),) for name, arg in func.args)
            m.stmt("'''{0}({1})'''", func.type.as_pretty_type(func.name), textargs)
            m.return_("_{0}({1})", func.name, ", ".join(n for n, _ in func.args))





