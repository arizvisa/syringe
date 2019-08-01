import ptypes
from ptypes import pstruct
from ..headers import *

class LineNumber(pstruct.type):
    _fields_ = [
        (dword, 'Type'),    # FIXME: SymbolTableIndex or VirtualAddress based on Linenumber
        (uint16, 'Linenumber'),
    ]

class LineNumberTable(parray.type):
    _object_ = LineNumber

# heh..
