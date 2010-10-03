import ptypes
from ptypes import *

class pQTInt(pint.bigendian(pint.uint32_t)): pass
class pQTType(pQTInt):
    def __repr__(self):
        return "%s '%c%c%c%c' (%08x)"% ( repr(self.__class__), self.value[0], self.value[1], self.value[2], self.value[3], int(self) )

    def __cmp__(self, x):
        if type(x) is str:
            return cmp('%c%c%c%c'% tuple(self.value[:4]), x)
        return cmp(int(self), x)

class pQTIntArray(parray.terminated):
    _object_ = pQTInt
    currentsize = maxsize = 0   # copied from powerpoint

    def isTerminator(self, value):
        s = value.size()
        self.currentsize += s
        if (self.currentsize < self.maxsize):
            return False
        return True

    def load(self):
        currentsize = 0
        return super(pQTIntArray, self).load()

    def deserialize(self,source):
        currentsize = 0
        return super(pQTIntArray, self).deserialize(source)

class Fixed(pint.uint32_t): pass

class Matrix(pstruct.type):
    _fields_ = [
        (Fixed, 'a'),
        (Fixed, 'b'),
        (Fixed, 'u'),
        (Fixed, 'c'),
        (Fixed, 'd'),
        (Fixed, 'v'),
        (Fixed, 'Tx'),
        (Fixed, 'Ty'),
        (Fixed, 'w'),
    ]

class pQTString(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'c'),
        (lambda s: dyn.clone(pstr.string, length=int(s['c'].l)), 's'),
    ]

    def get(self):
        return self['s'].get()
