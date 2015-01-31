import ptypes
from ptypes import pstruct
from ..__base__ import *

class LineNumber(pstruct.type):
    _fields_ = [
        (dword, 'Type'),
        (uint16, 'Linenumber'),
        (addr_t, 'Address')
    ]

# heh..
