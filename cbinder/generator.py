import os
import re
import itertools
from pycparser import CParser, c_ast
from srcgen.python import PythonModule
from collections import OrderedDict
import time


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
delimiters = re.compile(r'''([!%^&*()[\]{};,:+\-/?:\s"'|=])''')
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
class CStruct(object):
    def __init__(self, name, members):
        self.name = name
        self.members = members
    def get_ctype(self):
        return self.name
    def to_ctypes(self, m):
        with m.class_(self.name, ["ctypes.Structure"]):
            with m.def_("__repr__", "self"):
                m.return_("'{0}({1})' % ({2})", self.name, ", ".join("%s = %%r" % (n,) for n, _ in self.members), 
                    ", ".join("self.%s" % (n,) for n, _ in self.members))
        m.stmt("{0}._fields_ = [", self.name)
        for name, type in self.members:         # @ReservedAssignment
            m.stmt("    ({0!r}, {1}),", name, type.get_ctype())
        m.stmt("]")
        m.sep()

@autorepr
class CEnum(object):
    def __init__(self, name, members):
        self.name = name
        self.members = members
    def get_ctype(self):
        return "ctypes.c_int"
    def to_ctypes(self, m):
        with m.class_(self.name, ["CEnum"]):
            m.stmt("_names_ = {0!r}", dict(self.members))
            m.stmt("_values_ = {0!r}", dict((v, k) for k, v in self.members))
            for name, value in self.members:
                m.stmt("{0} = {1}", name, value)
        if self.name.startswith("_anon_"):
            for k, _ in self.members:
                m.stmt("{0} = {1}.{0}", k, self.name)
        m.sep()

@autorepr
class CUnion(object):
    def __init__(self, name, members):
        self.name = name
        self.members = members
    def get_ctype(self):
        return self.name
    def to_ctypes(self, m):
        with m.class_(self.name, ["ctypes.Union"]):
            m.stmt("_fields_ = []")
        for name, type in self.members:     # @ReservedAssignment
            m.stmt("{0}._fields_.append(({1!r}, {2}))", self.name, name, type.get_ctype())
        m.sep()

@autorepr
class CTypedef(object):
    def __init__(self, name, type):         # @ReservedAssignment
        self.name = name
        self.type = type
    def get_ctype(self):
        return self.name
    def to_ctypes(self, m):
        m.stmt("{0} = {1}", self.name, self.type.get_ctype())

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
        # 32
        "int" : "c_int", "signed int" : "c_int", "int32" : "c_int", "int32_t" : "c_int", "__int32" : "c_int",
        "unsigned int" : "c_uint", "uint" : "c_uint", "uint_t" : "c_uint", "uint32" : "c_uint", 
        "uint32_t" : "c_uint", "unsigned __int32" : "c_uint", "long" : "c_long", "signed long" : "c_long", 
        "unsigned long" : "c_ulong", "ulong" : "c_ulong", "ulong_t" : "c_ulong",
        # 64
        "long long" : "c_longlong", "signed long long" : "c_longlong", "int64" : "c_longlong", "int64_t" : "c_longlong",
        "__int64" : "c_longlong", "unsigned long long" : "c_ulonglong", "ulonglong" : "c_ulonglong", 
        "ulonglong_t" : "c_ulonglong", "unsigned __int64" : "c_longlong", "uint64" : "c_ulonglong",
        "uint64_t" : "c_ulonglong", "unsigned __int64" : "c_ulonglong",
    }
    
    def __init__(self, name, indir_levels = 0, subscripts = None, quals = None):
        self.name = name
        self.indir_levels = indir_levels
        self.subscripts = subscripts
        self.quals = None
    def get_ctype(self):
        if self.indir_levels == 1 and not self.quals:
            if self.name == "char":
                return "ctypes.c_char_p"
            elif self.name == "wchar":
                return "ctypes.c_wchar_p"
            elif self.name == "void":
                return "ctypes.c_void_p"
        
        if isinstance(self.name, tuple):
            # CFUNCTYPE(c_int, POINTER(c_int), POINTER(c_int))
            restype, argtypes = self.name
            restype = restype.get_ctype()
            if restype == "void":
                restype = None
            tp = "ctypes.CFUNCTYPE(%s, %s)" % (restype, ", ".join(a.get_ctype() for _, a in argtypes))
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
            return eval("%s%s" % (node.op, node.expr.value))
        elif isinstance(node, c_ast.BinaryOp):
            return eval("%s%s%s" % (node.left.value, node.op, node.right.value))
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
        else:
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
        for m in node.decls:
            members.append((m.name, self.type_to_ctype(m.type)))
        struct = CStruct(node.name, members)
        if not struct.name:
            struct.name = "_anon_struct_%d" % (self.counter.next(),)
        self.module.types[struct.name] = struct
        return struct.name

    def create_union(self, node):
        members = []
        for m in node.decls:
            members.append((m.name, self.type_to_ctype(m.type)))
        union = CUnion(node.name, members)
        if not union.name:
            union.name = "_anon_union_%d" % (self.counter.next(),)
        self.module.types[union.name] = union
        return union.name
    
    def _resolve_typedef(self, realname, newname):
        if realname.startswith("_anon_"):
            obj = self.module.types.pop(realname)
            obj.name = newname
            self.module.types[obj.name] = obj
        else:
            self.module.types[newname] = CTypedef(newname, CType(realname))
    
    def visit_Typedef(self, node):
        if isinstance(node.type, c_ast.TypeDecl):
            node2 = node.type.type
            if isinstance(node2, c_ast.Enum):
                self._resolve_typedef(self.create_enum(node2), node.name)
            elif isinstance(node2, c_ast.Struct):
                self._resolve_typedef(self.create_struct(node2), node.name)
            elif isinstance(node2, c_ast.Union):
                self._resolve_typedef(self.create_union(node2), node.name)
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
    def __init__(self, hfile, includes = [], predefs = {}, prelude = []):
        self.hfile = hfile
        self.types = OrderedDict()
        self.funcs = OrderedDict()
        self.macros = OrderedDict()
        self.macros.update(predefs)
        
        lines = self._load_with_includes(hfile, includes)
        lines[0:0] = prelude
        text = self._preprocess(lines)
        
        parser = CParser()
        ast = parser.parse(text, hfile)
        visitor = CtypesGenVisitor(self)
        visitor.visit(ast)
    
    @classmethod
    def _load_with_includes(cls, rootfile, includes):
        path = os.path.dirname(os.path.abspath(rootfile))
        lines = strip_comments(open(rootfile, "rU").read()).splitlines() + ['']
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
            if filename not in includes:
                continue
            lines2 = strip_comments(open(os.path.join(path, filename), "rU").read()).splitlines() + ['']
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
    
    def export(self, filename, decorate = None):
        m = PythonModule()
        m.comment("Auto-generated file; do not edit directly", time.ctime())
        m.sep()
        m.import_("ctypes")
        m.from_("cbinder.lib", "CEnum", "UnloadedDLL")
        m.sep()
        generated_macros = set()
        for name, (args, value) in self.macros.items():
            if args or not value:
                continue
            identifiers = [tok for tok in delimiters.split(value) if identifier_pattern.match(tok)]
            if any(tok not in generated_macros for tok in identifiers):
                continue
            m.stmt("{0} = {1}", name, value)
            generated_macros.add(name)
        m.sep()
        for t in self.types.values():
            t.to_ctypes(m)
        m.sep()
        m.stmt("_dll = UnloadedDLL")
        for f in self.funcs.values():
            m.stmt("_{0} = UnloadedDLL", f.name)
        m.sep()
        with m.def_("load_dll", "dllname"):
            m.stmt("global _dll")
            with m.if_("_dll"):
                m.raise_("ValueError('DLL already loaded')")
            m.stmt("_dll = ctypes.CDLL(dllname)")
            m.sep()
            for f in self.funcs.values():
                m.stmt("global _{0}", f.name)
                m.stmt("_{0} = _dll.{0}", f.name)
                restype = f.type.get_ctype()
                if restype == "void":
                    restype = None
                m.stmt("_{0}.restype  = {1}", f.name, restype)
                m.stmt("_{0}.argtypes = [{1}]", f.name, ", ".join(arg.get_ctype() for name, arg in f.args))
                m.sep()

        for f in self.funcs.values():
            if decorate:
                decorate(m, f)
            with m.def_(f.name, *(n for n, _ in f.args)):
                textargs = ", ".join("%s" % (arg.as_pretty_type(name),) for name, arg in f.args)
                m.stmt("'''{0}({1})'''", f.type.as_pretty_type(f.name), textargs)
                m.return_("_{0}({1})", f.name, ", ".join(n for n, _ in f.args))
        
        m.dump(filename)
        return m




