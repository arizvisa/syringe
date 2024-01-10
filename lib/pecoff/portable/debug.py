import ptypes, sys, os.path
from ptypes import pstruct,parray,ptype,dyn,pstr,pbinary,utils
from ..headers import *

class IMAGE_DEBUG_TYPE_(pint.enum, DWORD):
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
        ('EX_DLLCHARACTERISTICS', 20),
    ]

class IMAGE_DEBUG_DIRECTORY_DATA(ptype.definition):
    cache = {}

# http://www.debuginfo.com/articles/debuginfomatch.html#debuginfoinpe
class IMAGE_DEBUG_DIRECTORY_ENTRY(pstruct.type):
    @staticmethod
    def __RawData__(self):
        self = self.getparent(IMAGE_DEBUG_DIRECTORY._object_)
        res, blocksize = (self[fld].li.int() for fld in ['Type', 'SizeOfData'])
        return IMAGE_DEBUG_DIRECTORY_DATA.get(res, blocksize=lambda _: blocksize)

    _fields_ = [
        (DWORD, 'Characteristics'),
        (TimeDateStamp, 'TimeDateStamp'),
        (WORD, 'MajorVersion'),
        (WORD, 'MinorVersion'),
        (IMAGE_DEBUG_TYPE_, 'Type'),
        (DWORD, 'SizeOfData'),
        (virtualaddress(__RawData__, type=DWORD), 'AddressOfRawData'),
        (fileoffset(__RawData__, type=DWORD), 'PointerToRawData'),
    ]

class IMAGE_DEBUG_DIRECTORY(parray.block):
    _object_ = IMAGE_DEBUG_DIRECTORY_ENTRY

## IMAGE_DEBUG_TYPE_CODEVIEW
class CodeViewInfo(ptype.definition):
    cache = {}

@CodeViewInfo.define
class CV_INFO_PDB20(pstruct.type):
    type = b'NB10'
    _fields_ = [
        (DWORD, 'Offset'),
        (DWORD, 'Signature'),
        (DWORD, 'Age'),
        (pstr.szstring, 'PdbFileName'),
    ]
    def SymHash(self):
        # return the signature/age "hash" despite it not being a real thing.
        iterable = ("{:0{:d}X}".format(self[fld].int(), 2 * self[fld].size()) for fld in ['Signature', 'Age'])
        return ''.join(iterable)

    def SymPath(self):
        # don't think the signature hash or anything even matters.
        return self['PdbFileName'].str()

    def SymUrl(self):
        import ntpath
        sympath = self.SymPath()

        # we're going to return a file:// url because the PDB20 information
        # is not intended to be hosted on a symsrv afaict.
        drive, pathname = ntpath.splitdrive(sympath)
        path = '/'.join(pathname.split('\\'))
        query = '&'.join("{:s}={:s}".format(fld, format(self[fld].int())) for fld, format in [('Signature', "{:08X}".format), ('Age', "{:d}".format), ('Offset', "{:d}".format)])

        # because py2's urllib is stupid, we use "drive" as '\0' and add it back in afterwards.
        if sys.version_info.major < 3:
            import urllib
            return urllib.basejoin('file:', "{:s}{:s}?{:s}".format('\0', path, query)).replace('\0', drive)

        # format each component into the actual file:// url w/o a fragment
        import urllib.parse
        return urllib.parse.urlunsplit(('file', drive, path, query, None))

@CodeViewInfo.define
class CV_INFO_PDB70(pstruct.type):
    type = b'RSDS'
    _fields_ = [
        (GUID, 'Signature'),
        (DWORD, 'Age'),
        (pstr.szstring, 'PdbFileName'),
    ]

    def Signature(self):
        items = []
        for fld in (self['Signature'][name] for name in ['Data1', 'Data2', 'Data3']):
            items.append("{:0{:d}X}".format(fld.int(), 2 * fld.size()))
        items.append(''.join(map("{:02X}".format, bytearray(self['Signature']['Data4'].serialize()))))
        return ''.join(items)

    def SymHash(self):
        sig, age = self.Signature(), self['Age'].int()
        return ''.join([self.Signature(), "{:X}".format(age)])

    def SymPath(self):
        import ntpath
        hash, filename = self.SymHash(), self['PdbFileName'].str()
        drive, pathname = ntpath.splitdrive(filename)
        return filename if drive else '/'.join([hash, filename])

    def SymUrl(self, baseuri='https://msdl.microsoft.com/download/symbols'):
        import ntpath
        signature, sympath = self.Signature(), self.SymPath()

        # Split up the path and check it it has a drive letter (making
        # it an absolute path).
        drive, pathname = ntpath.splitdrive(sympath)
        path = '/'.join(pathname.split('\\'))
        query = '&'.join("{:s}={:s}".format(name, item) for name, item in [('Signature', signature), ('Age', "{:d}".format(self['Age'].int()))])

        # If it doesn't have a drive letter, then it's a url and we just need to
        # prefix the sympath that we got with it. Py2's urllib is stupid, though.
        if not drive and sys.version_info.major < 3:
            import urllib
            path = '/'.join([self['PdbFileName'].str(), sympath])
            return urllib.basejoin(baseuri if baseuri.endswith('/') else "{:s}/".format(baseuri), path)

        # Py3's urllib isn't that bad, so we can that combine all our components
        # from the baseuri together with the pdf filename and our sympath.
        elif not drive:
            import urllib.parse
            scheme, location, path, query, fragment = urllib.parse.urlsplit(baseuri)
            newpath = '/'.join([path, self['PdbFileName'].str(), sympath])
            return urllib.parse.urlunsplit((scheme, location, newpath, query, fragment))

        # Otherwise we have a drive, and we just need to deal with Py2's urllib again.
        # We use '\0' as a placeholder, and then replace it with the drive afterwards.
        if sys.version_info.major < 3:
            import urllib
            return urllib.basejoin('file:', "{:s}{:s}?{:s}".format('\0', path, query)).replace('\0', drive)

        # With Py3's urllib, we can just use each component as-is.
        import urllib.parse
        return urllib.parse.urlunsplit(('file', drive, path, query, None))

        # Otherwise, our path needs to be combined with the baseurl.
        sympath = self.SymPath()
        if sys.version_info.major < 3:
            import urllib
            path = '/'.join([self['PdbFileName'].str(), sympath])
            return urllib.basejoin(baseuri if baseuri.endswith('/') else "{:s}/".format(baseuri), path)

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_CODEVIEW(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('CODEVIEW')
    def __Info(self):
        res = self['Signature'].li.serialize()
        return CodeViewInfo.lookup(res)

    def __Extra(self):
        bs, res = self.blocksize(), sum(self[fld].li.size() for fld in ['Signature', 'Info'])
        return dyn.block(max(0, bs - res))

    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'Signature'),
        (__Info, 'Info'),
        (__Extra, 'Extra'),
    ]
IMAGE_DEBUG_TYPE_CODEVIEW = IMAGE_DEBUG_DATA_CODEVIEW

## IMAGE_DEBUG_TYPE_MISC
class IMAGE_DEBUG_MISC_(pint.enum, DWORD):
    _values_ = [('EXENAME', 1)]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_MISC(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('MISC')

    def __Extra(self):
        length, res = self['Length'].li, sum(self[fld].li.size() for fld in ['DataType', 'Length', 'Unicode', 'align(Unicode)', 'Data'])
        return dyn.block(max(0, length.int() - res))

    _fields_ = [
        (IMAGE_DEBUG_MISC_, 'DataType'),
        (DWORD, 'Length'),
        (BYTE, 'Unicode'),
        (dyn.block(3), 'align(Unicode)'),
        (lambda self: pstr.szwstring if self['Unicode'].li.int() else pstr.szstring, 'Data'),
        (__Extra, 'Extra'),
    ]
IMAGE_DEBUG_TYPE_MISC = IMAGE_DEBUG_DATA_MISC

## IMAGE_DEBUG_TYPE_COFF
# http://waleedassar.blogspot.com/2012/06/loading-coff-symbols.html
# http://www.delorie.com/djgpp/doc/coff/symtab.html
@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_COFF(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('COFF')

    def __Extra(self):
        fields = [
            'NumberOfSymbols', 'LvaToFirstSymbol', 'NumberOfLinenumbers', 'LvaToFirstLinenumber',
            'RvaToFirstByteOfCode', 'RvaToLastByteOfCode', 'RvaToFirstByteOfData', 'RvaToLastByteOfData'
        ]
        bs, res = self.blocksize(), sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, bs - res))

    _fields_ = [
        (DWORD, 'NumberOfSymbols'),
        (DWORD, 'LvaToFirstSymbol'),
        (DWORD, 'NumberOfLinenumbers'),
        (DWORD, 'LvaToFirstLinenumber'),

        (virtualaddress(VOID, type=DWORD), 'RvaToFirstByteOfCode'),
        (virtualaddress(VOID, type=DWORD), 'RvaToLastByteOfCode'),
        (virtualaddress(VOID, type=DWORD), 'RvaToFirstByteOfData'),
        (virtualaddress(VOID, type=DWORD), 'RvaToLastByteOfData'),

        (__Extra, 'Extra'),
    ]
IMAGE_DEBUG_TYPE_COFF = IMAGE_DEBUG_DATA_COFF

## IMAGE_DEBUG_TYPE_FPO
# https://msdn.microsoft.com/library/windows/desktop/ms680547(v=vs.85).aspx?id=19509
class FRAME_(pbinary.enum):
    length, _values_ = 2, [
        ('FPO', 0),
        ('TRAP', 1),
        ('TSS', 2),
    ]

class FPO_DATA(pstruct.type):
    @pbinary.littleendian
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
        (DWORD, 'ulOffStart'),
        (DWORD, 'cbProcSize'),
        (DWORD, 'cdwLocals'),
        (WORD, 'cdwParams'),
        (_BitValues, 'BitValues'),
    ]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_FPO(parray.block):
    type = IMAGE_DEBUG_TYPE_.byname('FPO')
    _object_ = FPO_DATA
IAMGE_DEBUG_TYPE_FPO = IMAGE_DEBUG_DATA_FPO

## IMAGE_DEBUG_TYPE_RESERVED10
#https://github.com/dotnet/roslyn/issues/5940
@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_RESERVED10(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('RESERVED10')
    class _Signature(DWORD):
        def summary(self):
            res = bytes(bytearray(reversed(self.serialize())))
            return "{!r} ({:#08x})".format(res, self.int())

    def __Extra(self):
        bs, res = self.blocksize(), sum(self[fld].li.size() for fld in ['Signature'])
        return dyn.block(max(0, bs - res))

    _fields_ = [
        (_Signature, 'Signature'),
        (__Extra, 'Extra'),
    ]
IMAGE_DEBUG_TYPE_RESERVED10 = IMAGE_DEBUG_DATA_RESERVED10

## IMAGE_DEBUG_TYPE_VC_FEATURE
@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_VC_FEATURE(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('VC_FEATURE')
    #Counts: Pre-VC++ 11.00=0, C/C++=202, /GS=202, /sdl=0, guardN=201
    _fields_ = [
        (DWORD, 'Version'),
        (DWORD, 'C/C++'),
        (DWORD, 'GS'),
        (DWORD, 'SDL'),
        (DWORD, 'guardN'),
    ]
IMAGE_DEBUG_TYPE_VC_FEATURE = IMAGE_DEBUG_DATA_VC_FEATURE

## IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS
class IMAGE_DLLCHARACTERISTICS_EX_(pbinary.flags):
    _fields_ = [
        (9, 'UNKNOWN'),
        (1, 'FORWARD_CFI_COMPAT'),
        (5, 'RESERVED'),
        (1, 'CET_COMPAT'),
    ]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_EX_DLLCHARACTERISTICS(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('EX_DLLCHARACTERISTICS')
    def __Padding(self):
        bs, fields = self.blocksize(), ['ExDllCharacteristics']
        res = max(0, bs - sum(self[fld].li.size() for fld in fields))
        return dyn.block(res)
    _fields_ = [
        (pbinary.littleendian(IMAGE_DLLCHARACTERISTICS_EX_), 'ExDllCharacteristics'),
        (__Padding, 'Padding'),
    ]
    def summary(self):
        return "Padding={:#x} : ExDllCharacteristics={:s}".format(self['Padding'], self['ExDllCharacteristics'].summary())
IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS = IMAGE_DEBUG_DATA_EX_DLLCHARACTERISTICS

## IMAGE_DEBUG_TYPE_POGO
class LTCG_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda self: dyn.block(self.getparent(LTCG_ENTRY).li['size'].int()), type=DWORD), 'rva'),
        (DWORD, 'size'),
        (pstr.szstring, 'section'),
        (dyn.padding(4), 'align(section)'),
    ]

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_POGO(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('POGO')

    class _Signature(DWORD):
        def summary(self):
            res = bytes(bytearray(reversed(self.serialize())))
            return "{!r} ({:#08x})".format(res, self.int())

    def __entries(self):
        bs, res = self.blocksize(), sum(self[fld].li.size() for fld in ['Signature'])
        return dyn.blockarray(LTCG_ENTRY, max(0, bs - res))

    _fields_ = [
        (_Signature, 'Signature'),
        (__entries, 'Entries'),
    ]
IMAGE_DEBUG_TYPE_POGO = IMAGE_DEBUG_DATA_POGO

@IMAGE_DEBUG_DIRECTORY_DATA.define
class IMAGE_DEBUG_DATA_REPRO(pstruct.type):
    type = IMAGE_DEBUG_TYPE_.byname('REPRO')
    _fields_ = [
        (DWORD, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Unknown'),
    ]
IMAGE_DEBUG_TYPE_REPRO = IMAGE_DEBUG_DATA_REPRO
