import six, functools, ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class pQTInt(pint.bigendian(pint.uint32_t)): pass
class pQTInt64(pint.bigendian(pint.uint64_t)): pass

class pQTType(pQTInt):
    def summary(self):
        octets = bytearray(self.serialize())
        if self.value:
            return "{!r} ({:#0{:d}x})".format(bytes(octets).decode('latin1'), self.int(), 2 + 2 * self.size())
        return 'uninitialized'

    def __eq__(self, other):
        octets = bytearray(self.serialize())
        if isinstance(other, bytes):
            items = bytearray(other)
            return octets == items
        elif isinstance(other, six.string_types):
            item = bytes(octets).decode('latin1')
            return item == other
        return self.int() == other

    def __ne__(self, other):
        return not(self.__eq__(other))

    def set(self, value):
        octets = bytearray(value)
        res = functools.reduce(lambda agg, item: agg * pow(2, 8) + item, octets, 0)
        return super(pQTType,self).set(res)

class Fixed(pfloat.ufixed_t):
    fractional, length = 16, 4

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
        (lambda self: dyn.clone(pstr.string, length=self['c'].li.int()), 's'),
    ]
    def str(self):
        return self['s'].str()
