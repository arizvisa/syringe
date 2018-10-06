# http://www.forensicswiki.org/wiki/Windows_Prefetch_File_Format

import ptypes
from ptypes import *

# primitives
class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class FILETIME(ptype.undefined): length=8

class USTRING30(pstr.string): length=0x3c

class PFHEAD(pstruct.type):
    _fields_= [
        (DWORD, 'Version'),
        (DWORD, 'Magic'),
        (DWORD, 'Unknown1'),
        (DWORD, 'FileSize'),
        (USTRING30, 'ExecutableName'),
        (DWORD, 'Hash'),
        (DWORD, 'Unknown2'),

        (DWORD, 'SectionAOffset'),
        (DWORD, 'SectionANumberOfEntries'),

        (DWORD, 'SectionBOffset'),
        (DWORD, 'SectionBNumberOfEntries'),

        (DWORD, 'SectionCOffset'),
        (DWORD, 'SectionCLength'),

        (DWORD, 'SectionDOffset'),
        (DWORD, 'SectionDLength'),

        (FILETIME, 'LatestExecution'),
        (dyn.array(DWORD,4), 'Unknown3'),
        (DWORD, 'ExecutionCounter'),
        (DWORD, 'Unknown4'),
    ]
