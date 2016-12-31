import ptypes
from ptypes import pstruct
from ..__base__ import *

class LineNumber(pstruct.type):
    _fields_ = [
        (dword, 'Type'),    # FIXME: SymbolTableIndex or VirtualAddress based on Linenumber
        (uint16, 'Linenumber'),
    ]

# heh..
