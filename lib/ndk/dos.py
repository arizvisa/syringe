import ptypes
from ptypes import *

# mostly from http://www.piclist.com/techref/dos/psps.htm
# http://textfiles.com/uploads/kds-dospsp.txt
class psp(pstruct.type):
    class internal(pstruct.type):
        _fields_ = [(pint.uint16_t, 'parent program segment address'),(dyn.block(20),'job file table')]
    class work(pstruct.type):
        _fields_ = [(pint.uint32_t, 'ss:sp'),(pint.uint16_t, 'sizeof handle table'),(pint.uint32_t, 'handle table'),(dyn.block(24),'reserved')]
    _fields_ = [
        (pint.uint16_t, 'int 20h'),
        (pint.uint16_t, 'memory size'),
        (pint.uint8_t, 'reserved'),
        (dyn.clone(pint.uint_t,length=5), 'int 21h'),
        (pint.uint32_t, 'int 22h'),
        (pint.uint32_t, 'int 23h'),
        (pint.uint32_t, 'int 24h'),
        (internal, 'internal'),
        (pint.uint16_t, 'environment segment'),
        (work, 'work'),
        (dyn.block(3), 'dos function dispatcher'),
        (pint.uint16_t, 'reserved - unused?'),
        (dyn.block(7), 'fcb#1'),
        (dyn.block(16), 'unopened fcb#1'),
        (dyn.block(20), 'unopened fcb#2'),
        (pint.uint8_t, 'parameter length'),
        (dyn.block(127), 'parameters'),
        (dyn.block(128), 'command tail and dta'),
    ]
