import ctypes


class CEnum(ctypes.c_int):
    _names_ = {}
    _values_ = {}
    __slots__ = []
    class __metaclass__(type(ctypes.c_int)):
        def __new__(cls, name, bases, namespace):
            cls2 = type(ctypes.c_int).__new__(cls, name, bases, namespace)
            for name, val in namespace["_names_"].items():
                setattr(cls2, name, cls2(val))
            return cls2
    
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
    def __hash__(self, other):
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

