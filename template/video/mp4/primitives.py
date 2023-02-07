import sys, functools, ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class pQTInt(pint.bigendian(pint.uint32_t)): pass
class pQTInt64(pint.bigendian(pint.uint64_t)): pass

class pQTType(pQTInt):
    def summary(self):
        if self.value is None:
            return 'uninitialized'
        octets = bytearray(self.serialize())
        return "{!r} ({:#0{:d}x})".format(bytes(octets).decode('latin1'), self.int(), 2 + 2 * self.size())

    def __eq__(self, other):
        octets = bytearray(self.serialize())
        if isinstance(other, bytes):
            items = bytearray(other)
            return octets == items
        elif isinstance(other, (bytes, unicode if sys.version_info.major < 3 else str)):
            item = bytes(octets).decode('latin1')
            return item == other
        return self.int() == other

    def __ne__(self, other):
        return not(self.__eq__(other))

    # Seems that Py3 deletes the following method if you define __eq__ and __ne__.
    def __hash__(self):
        return super(pQTType, self).__hash__()

    def set(self, value):
        if isinstance(value, (bytes, bytearray)):
            octets = bytearray(value)
            integer = functools.reduce(lambda agg, item: agg * pow(2, 8) + item, octets, 0)
            return super(pQTType, self).set(integer)
        return super(pQTType, self).set(value)

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
