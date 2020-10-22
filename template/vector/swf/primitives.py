import ptypes
from ptypes import *
from ptypes.pint import littleendian

## float types
class FLOAT16(pfloat.half): pass
class FLOAT(pfloat.single): pass
class DOUBLE(pfloat.double): pass

## int types
class SI8(pint.int8_t): pass
class SI16(pint.int16_t): pass
class SI24(pint.int_t): length = 3
class SI32(pint.int32_t): pass
class SI64(pint.int64_t): pass

class UI8(pint.int8_t): pass
class UI16(pint.int16_t): pass
class UI24(pint.int_t): length = 3
class UI32(pint.int32_t): pass
class UI64(pint.int64_t): pass

(SI8, UI8, SI16, UI16, SI32, UI32, UI64) = ( littleendian(x) for x in (SI8,UI8,SI16,UI16,SI32,UI32,UI64) )

## fixed-point types
class SI8_8(pfloat.sfixed_t): length,fractional = 2,8
class SI16_16(pfloat.sfixed_t): length,fractional = 4,16
class UI8_8(pfloat.ufixed_t): length,fractional = 2,8
class UI16_16(pfloat.ufixed_t): length,fractional = 4,16

class FIXED(UI16_16): pass
class FIXED8(SI8_8): pass

class STRING(pstr.szstring): pass

class Empty(ptype.type):
    initialized = property(fget=lambda x: True, fset=lambda x,v: None)
    value = ''

class Zero(pint.uint_t,Empty): pass
