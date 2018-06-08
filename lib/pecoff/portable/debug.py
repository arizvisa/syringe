import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,pbinary,utils
from ..__base__ import *

from .headers import virtualaddress,realaddress,fileoffset
from . import headers

pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

class IMAGE_DEBUG_TYPE_(pint.enum, uint32):
    _values_ = [
        ('UNKNOWN', 0),
        ('COFF', 1),
        ('CODEVIEW', 2),
        ('FPO', 3),
        ('MISC', 4),
        ('EXCEPTION', 5),
        ('FIXUP', 6),
        ('OMAP_TO_SRC', 7),
        ('OMAP_FROM_SRC', 8),
        ('BORLAND', 9),
        ('RESERVED10', 10),
        ('CLSID', 11),
        ('VC_FEATURE', 12),
        ('POGO', 13),
        ('ILTCG', 14),
        ('MPX', 15),
        ('REPRO', 16),
    ]

class IMAGE_DEBUG_DIRECTORY_DATA(ptype.definition):
    cache = {}

# http://www.debuginfo.com/articles/debuginfomatch.html#debuginfoinpe
class IMAGE_DEBUG_DIRECTORY_ENTRY(pstruct.type):
    @staticmethod
    def __RawData__(self):
        self = self.getparent(IMAGE_DEBUG_DIRECTORY._object_)
        res = self['Type'].li.int()
        return IMAGE_DEBUG_DIRECTORY_DATA.withdefault(res, length=self['SizeOfData'].li.int())

    _fields_ = [
        (uint32, 'Characteristics'),
        (TimeDateStamp, 'TimeDateStamp'),
        (uint16, 'MajorVersion'),
        (uint16, 'MinorVersion'),
        (IMAGE_DEBUG_TYPE_, 'Type'),
        (uint32, 'SizeOfData'),
        (virtualaddress(__RawData__), 'AddressOfRawData'),
        (fileoffset(__RawData__), 'PointerToRawData'),
    ]

class IMAGE_DEBUG_DIRECTORY(parray.block):
    _object_ = IMAGE_DEBUG_DIRECTORY_ENTRY

## IMAGE_DEBUG_TYPE_CODEVIEW
class CodeViewInfo(ptype.definition):
    cache = {}

@CodeViewInfo.define
class CV_INFO_PDB20(pstruct.type):
    type = 'NB10'
    _fields_ = [
        (uint32, 'Offset'),
        (uint32, 'Signature'),
        (uint32, 'Age'),
        (pstr.szstring, 'PdbFileName'),
    ]

@CodeViewInfo.define
class CV_INFO_PDB70(pstruct.type):
    type = 'RSDS'
    _fields_ = [
        (GUID, 'Signature'),
        (uint32, 'Age'),
        (pstr.szstring, 'PdbFileName'),
    ]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_CODEVIEW(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('CODEVIEW')
    def __Info(self):
        res = self['Signature'].li.serialize()
        return CodeViewInfo.lookup(res)

    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'Signature'),
        (__Info, 'Info'),
    ]

## IMAGE_DEBUG_TYPE_MISC
class IMAGE_DEBUG_MISC_(pint.enum, uint32):
    _values_ = [('EXENAME', 1)]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_MISC(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('MISC')

    _fields_ = [
        (IMAGE_DEBUG_MISC_, 'DataType'),
        (uint32, 'Length'),
        (uint8, 'Unicode'),
        (dyn.block(3), 'align(Unicode)'),
        (lambda s: dyn.clone(pstr.wstring if s['Unicode'].int() else pstr.string, length=s['Length'].li.int()), 'Data'),
    ]

## IMAGE_DEBUG_TYPE_COFF

# http://waleedassar.blogspot.com/2012/06/loading-coff-symbols.html
# http://www.delorie.com/djgpp/doc/coff/symtab.html
@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_COFF(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('COFF')
    _fields_ = [
        (uint32, 'NumberOfSymbols'),
        (uint32, 'LvaToFirstSymbol'),
        (uint32, 'NumberOfLinenumbers'),
        (uint32, 'LvaToFirstLinenumber'),

        (virtualaddress(ptype.undefined, type=uint32), 'RvaToFirstByteOfCode'),
        (virtualaddress(ptype.undefined, type=uint32), 'RvaToLastByteOfCode'),
        (virtualaddress(ptype.undefined, type=uint32), 'RvaToFirstByteOfData'),
        (virtualaddress(ptype.undefined, type=uint32), 'RvaToLastByteOfData'),
    ]

## IMAGE_DEBUG_TYPE_FPO

# https://msdn.microsoft.com/library/windows/desktop/ms680547(v=vs.85).aspx?id=19509
class FRAME_(pbinary.enum):
    width, _values_ = 2, [
        ('FPO', 0),
        ('TRAP', 1),
        ('TSS', 2),
    ]

class FPO_DATA(pstruct.type):
    class _BitValues(pbinary.struct):
        _fields_ = [
            (8, 'cbProlog'),
            (3, 'cbRegs'),
            (1, 'fHasSEH'),
            (1, 'fUseBP'),
            (1, 'reserved'),
            (FRAME_, 'cbFrame'),
        ]

    _fields_ = [
        (uint32, 'ulOffStart'),
        (uint32, 'cbProcSize'),
        (uint32, 'cdwLocals'),
        (uint16, 'cdwParams'),
        (_BitValues, 'BitValues'),
    ]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_FPO(parray.block):
    type = IMAGE_DEBUG_TYPE_.byname('FPO')
    _object_ = FPO_DATA

## IMAGE_DEBUG_TYPE_RESERVED10

#https://github.com/dotnet/roslyn/issues/5940
@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_RESERVED10(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('RESERVED10')
    class _Signature(uint32):
        def summary(self):
            res = str().join(reversed(self.serialize()))
            return "{!r} ({:#08x})".format(res, self.int())
    _fields_ = [
        (_Signature, 'Signature')
    ]
