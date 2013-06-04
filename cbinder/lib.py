import ctypes


class CEnumMeta(type(ctypes.c_int)):
    def __new__(cls, name, bases, namespace):
        cls2 = type(ctypes.c_int).__new__(cls, name, bases, namespace)
        if namespace.get("__module__") != __name__:
            namespace["_values_"].clear()
            for name in namespace["_names_"].keys():
                if name.startswith("_"):
                    continue
                setattr(cls2, name, cls2(namespace[name]))
                namespace["_names_"][name] = namespace[name]
                namespace["_values_"][namespace[name]] = name
        return cls2

def with_meta(meta, base = object):
    return meta("NewBase", (base,), {"__module__" : __name__})

class CEnum(with_meta(CEnumMeta, ctypes.c_int)):
    _names_ = {}
    _values_ = {}
    __slots__ = []
    
    def __repr__(self):
        name = self._values_.get(self.value)
        if name is None:
            return "%s(%r)" % (self.__class__.__name__, self.val)
        else:
            return "%s.%s" % (self.__class__.__name__, name)
    @classmethod
    def from_param(cls, obj):
        return int(obj)
    @classmethod
    def from_name(cls, name):
        return cls._names_[name]
    @classmethod
    def from_value(cls, val):
        return getattr(self, cls._values_[val])

    def __int__(self):
        return int(self.value)
    def __index__(self):
        return int(self)
    def __eq__(self, other):
        return int(self) == int(other)
    def __ne__(self, other):
        return int(self) != int(other)
    def __gt__(self, other):
        return int(self) > int(other)
    def __ge__(self, other):
        return int(self) >= int(other)
    def __lt__(self, other):
        return int(self) < int(other)
    def __le__(self, other):
        return int(self) <= int(other)
    def __hash__(self):
        return hash(int(self))


class DLLNotLoaded(Exception):
    pass

class UnloadedDLL(object):
    __slots__ = []
    def __bool__(self):
        return False
    __nonzero__ = __bool__
    def __call__(self, *args, **kwargs):
        raise DLLNotLoaded("DLL is not loaded")
    def __getattr__(self, name):
        raise DLLNotLoaded("DLL is not loaded")

UnloadedDLL = UnloadedDLL()

