import ptypes
from ptypes import *
from ptypes.pint import littleendian

class pFixed(ptype.type):
    length = 0

    def __float__(self):
        v = list(reversed(self.serialize()))

        center = self.length / 2
        divisor = 2**(center*8)

        high = utils.h2i(v[:center])
        low = utils.h2i(v[center:]) / float(divisor)
        return float(high)+low

    def __repr__(self):
        if self.initialized:
            res = '%f'%self.__float__()
        else:
            res = '???'
        return '%s %s'% (self.__class__, res)

## float types
#TODO: define __repr__ for each of these types
# FIXME: if we modify pfloat.type, we can support this structure directly
class FLOAT16(pbinary.struct):
    _fields_ = [
        (1, 'sign'),
        (5, 'exponent'),
        (10, 'mantissa')
    ]

class FLOAT(pbinary.struct):
    _fields_ = [
        (1, 'sign'),
        (8, 'exponent'),
        (23, 'mantissa')
    ]

class DOUBLE(pbinary.struct):
    _fields_ = [
        (1, 'sign'),
        (11, 'exponent'),
        (52, 'mantissa')
    ]

## int types
class SI8(pint.sint_t):
    length = 1
    signed = True

class UI8(pint.uint_t):
    length = 1
    signed = False

class SI16(pint.sint_t):
    length = 2
    signed = True

class UI16(pint.uint_t):
    length = 2
    signed = False

class SI32(pint.sint_t):
    length = 4
    signed = True

class UI32(pint.uint_t):
    length = 4
    signed = False

class UI64(pint.uint_t):
    length = 8
    signed = False

(SI8, UI8, SI16, UI16, SI32, UI32, UI64) = ( littleendian(x) for x in (SI8,UI8,SI16,UI16,SI32,UI32,UI64) )

class FIXED(pFixed):
    length = 4

class FIXED8(pFixed):
    length = 2

class STRING(pstr.szstring):
    def isTerminator(self, v):
        return int(v) == 0

    def __str__(self):
        return ''.join( [str(v) for v in self] )

class Empty(ptype.type):
    initialized = property(fget=lambda x: True, fset=lambda x,v: None)
    value = []

