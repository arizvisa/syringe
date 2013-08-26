import ptypes
from ptypes import pint,pfloat,dyn

## primitives
byte = dyn.clone(pint.uint8_t, summary=lambda s:s.details())
word = dyn.clone(pint.uint16_t, summary=lambda s:s.details())
dword = dyn.clone(pint.uint32_t, summary=lambda s:s.details())
float = dyn.clone(pfloat.single, summary=lambda s:s.details())
double = dyn.clone(pfloat.double, summary=lambda s:s.details())

uint8 = dyn.clone(pint.uint8_t, summary=lambda s:s.details())
int8 = dyn.clone(pint.int8_t, summary=lambda s:s.details())
int16 = dyn.clone(pint.int16_t, summary=lambda s:s.details())
uint16 = dyn.clone(pint.uint16_t, summary=lambda s:s.details())
int32 = dyn.clone(pint.int32_t, summary=lambda s:s.details())
uint32 = dyn.clone(pint.uint32_t, summary=lambda s:s.details())

class off_t(pint.uint32_t):
    def summary(self):
        return self.details()
class addr_t(pint.uint32_t):
    def summary(self):
        return self.details()

import datetime
class TimeDateStamp(uint32):
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
    def details(self):
        x = self.epoch + datetime.timedelta( seconds=int(self) )
        return x.strftime('%Y-%m-%d %H:%M:%S')

class IMAGE_COMDAT_SELECT(ptypes.pint.enum, byte):
    _values_ = [
        ('NODUPIC', 1),
        ('ANY', 2),
        ('SAME_SIZE', 3),
        ('EXACT_MATCH', 4),
        ('ASSOCIATIVE', 5),
        ('LARGEST', 6)
    ]

class BaseHeader(object):
    '''base header class. Inherited by root headers'''
    pass
class Header(object):
    '''header class. Inherited by primary headers'''
    pass

