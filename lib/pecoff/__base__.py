import ptypes
from ptypes import pint,pfloat,dyn

class Header(object): pass

class Machine(pint.enum, pint.uint16_t):
    _values_ = [
        ('UNKNOWN', 0x0000), ('AM33', 0x01d3), ('AMD64', 0x8664), ('ARM', 0x01c0),
        ('EBC', 0x0ebc), ('I386', 0x014c), ('IA64', 0x0200), ('M32R', 0x9041),
        ('MIPS16', 0x0266), ('MIPSFPU', 0x0366), ('MIPSFPU16', 0x0466), ('POWERPC', 0x01f0),
        ('POWERPCFP', 0x01f1), ('R4000', 0x0166), ('SH3', 0x01a2), ('SH3DSP', 0x01a3),
        ('SH4', 0x01a6), ('SH5', 0x01a8), ('THUMB', 0x01c2), ('WCEMIPSV2', 0x0169),
    ]

## primitives
byte = dyn.clone(pint.uint8_t)
word = dyn.clone(pint.uint16_t)
dword = dyn.clone(pint.uint32_t)
float = dyn.clone(pfloat.single)
double = dyn.clone(pfloat.double)

uint8 = dyn.clone(pint.uint8_t)
int8 = dyn.clone(pint.int8_t)
int16 = dyn.clone(pint.int16_t)
uint16 = dyn.clone(pint.uint16_t)
int32 = dyn.clone(pint.int32_t)
uint32 = dyn.clone(pint.uint32_t)
uint64 = dyn.clone(pint.uint64_t)

class off_t(pint.uint32_t): pass
class addr_t(pint.uint32_t): pass

import datetime
class TimeDateStamp(uint32):
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
    def details(self):
        x = self.epoch + datetime.timedelta( seconds=int(self) )
        return x.strftime('%Y-%m-%d %H:%M:%S')
    def summary(self):
        return '{:#x} {!r}'.format(self.int(), self.details())

class IMAGE_COMDAT_SELECT(ptypes.pint.enum, byte):
    _values_ = [
        ('NODUPIC', 1),
        ('ANY', 2),
        ('SAME_SIZE', 3),
        ('EXACT_MATCH', 4),
        ('ASSOCIATIVE', 5),
        ('LARGEST', 6)
    ]

