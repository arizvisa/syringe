import ptypes
from ptypes import pint,pfloat,dyn

class Header(object): pass

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
        return '0x{:x} {!r}'.format(self.num(), self.details())

class IMAGE_COMDAT_SELECT(ptypes.pint.enum, byte):
    _values_ = [
        ('NODUPIC', 1),
        ('ANY', 2),
        ('SAME_SIZE', 3),
        ('EXACT_MATCH', 4),
        ('ASSOCIATIVE', 5),
        ('LARGEST', 6)
    ]

