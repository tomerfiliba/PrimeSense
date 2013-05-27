import ctypes


class OpenNIError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, code, message)

class NiteError(Exception):
    def __init__(self, code):
        Exception.__init__(self, code)

def inherit_properties(struct, attrname):
    def deco(cls):
        for name, _ in struct._fields_:
            def getter(self, name = name):
                return getattr(getattr(self, attrname), name)
            def setter(self, value, name = name):
                return setattr(getattr(self, attrname), name, value)
            setattr(cls, name, property(getter, setter))
        return cls
    return deco

class ClosedHandleError(Exception):
    pass
class ClosedHandle(object):
    def __getattr__(self, name):
        raise ClosedHandleError("Invalid handle")
    def __bool__(self):
        return False
    __nonzero__ = __bool__
ClosedHandle = ClosedHandle()

class HandleObject(object):
    __slots__ = ["_handle"]
    def __init__(self, handle):
        self._handle = handle
    def __del__(self):
        self.close()
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()
    def close(self):
        if hasattr(self, "_handle") and self._handle:
            self._close()
            self._handle = ClosedHandle
    def _close(self):
        raise NotImplementedError()

def _py_to_ctype_obj(obj):
    size = None
    if isinstance(obj, (int, bool)):
        obj = ctypes.c_int(obj)
    elif isinstance(obj, float):
        obj = ctypes.c_float(obj)
    elif isinstance(obj, str):
        obj = ctypes.create_string_buffer(obj)
        size = len(obj)
    return obj, size

