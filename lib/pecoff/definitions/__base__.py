import ptypes
from ptypes import pint,pstruct,dyn

## primitives
class byte(pint.uint8_t): pass
class word(pint.uint16_t): pass
class dword(pint.uint32_t): pass
class float(pint.int32_t): pass     # XXX: not implemented yet
class double(pint.int64_t): pass     # XXX: not implemented yet

uint8 = pint.uint8_t
int8 = pint.int8_t
int16 = pint.int16_t
uint16 = pint.uint16_t
int32 = pint.int32_t
uint32 = pint.uint32_t
off_t = pint.uint32_t
addr_t = pint.uint32_t

import datetime
class TimeDateStamp(uint32):
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
    def __repr__(self):
        x = self.epoch + datetime.timedelta( seconds=int(self) )
        return '%s %s'%(self.__class__, x.strftime('%F %T'))

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

