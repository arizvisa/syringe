import ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.bigendian)

class int8(pint.int8_t): pass
class uint8(pint.uint8_t): pass
class Fixed(pint.uint32_t): pass
class Integer(pint.uint16_t): pass
class Long(pint.uint32_t): pass
class Mode(pint.uint16_t): pass
class Pattern(pint.uint64_t): pass
class Point(pint.uint32_t): pass

class Rect(pstruct.type):
    _fields_ = [
        (Integer, 'top'),
        (Integer, 'left'),
        (Integer, 'bottom'),
        (Integer, 'right'),
    ]

class Rgn(pstruct.type):
    def __data(self):
        s = int(self['size'].l)
        return dyn.block(s - 10)

    _fields_ = [
        (Integer, 'size'),
        (Rect, 'region'),
        (__data, 'data'),
    ]

    def blocksize(self):
        return int(self['size'].l)

class Opcode_v1(pint.uint8_t): pass
class Opcode_v2(pint.uint16_t): pass

class Int16Data(pstruct.type):
    _fields_ = [
        (Integer, 'size'),
        (lambda s: dyn.block(int(s['size'].l)), 'data')
    ]
