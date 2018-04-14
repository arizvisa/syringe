import ptypes,ndk
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### Primitive types
class ULONG(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class USHORT(pint.uint16_t): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class QWORD(pint.uint64_t): pass

class CLSID(ndk.rfc4122): pass

class FILETIME(pstruct.type):
    _fields_ = [(DWORD,'dwLowDateTime'),(DWORD,'dwHighDateTime')]
TIME_T = FILETIME

class LengthPrefixedAnsiString(pstruct.type):
    _fields_ = [(DWORD, 'Length'),(lambda s: dyn.clone(pstr.string,length=s['Length'].li.num()),'String')]
class LengthPrefixedUnicodeString(pstruct.type):
    _fields_ = [(DWORD, 'Length'),(lambda s: dyn.clone(pstr.wstring,length=s['Length'].li.num()),'String')]

### Sector types
class Sector(ptype.definition):
    cache = {}
    class Pointer(ptype.opointer_t):
        def _calculate_(self, index):
            return self._uSectorSize + index * self._uSectorSize
        class _value_(pint.enum, DWORD):
            _values_ = [
                ('MAXREGSECT', 0xfffffffa),
                ('NotApplicable', 0xfffffffb),
                ('DIFSECT', 0xfffffffc),
                ('FATSECT', 0xfffffffd),
                ('ENDOFCHAIN', 0xfffffffe),
                ('FREESECT', 0xffffffff),
            ]
        def _object_(self):
            return dyn.block(self._uSectorSize)
        def summary(self, **options):
            return self.object.summary(**options)

@Sector.define
class REGSECT(Sector.Pointer): symbol,type = '+',None
Sector.unknown = REGSECT
@Sector.define
class MAXREGSECT(REGSECT): symbol,type = '+',0xfffffffa
@Sector.define
class NotApplicable(DWORD): symbol,type = '-',0xfffffffb
@Sector.define
class DIFSECT(DWORD): symbol,type = 'D',0xfffffffc
@Sector.define
class FATSECT(DWORD): symbol,type = 'F',0xfffffffd
@Sector.define
class ENDOFCHAIN(DWORD): symbol,type = '$',0xfffffffe
@Sector.define
class FREESECT(DWORD): symbol,type = '.',0xffffffff

class SECT(Sector.Pointer): pass

### File-allocation tables that populate a single sector
class AllocationTable(parray.type):
    def summary(self, **options):
        return ''.join(Sector.lookup(n.int(), dyn.clone(Sector.unknown, type=n.int())).symbol for n in self)
    def _object_(self):
        return dyn.clone(Sector.Pointer,_object_=self.Pointer)
    def chain(self, index):
        yield index
        while self[index].num() <= MAXREGSECT.type:
            index = self[index].num()
            yield index
        return

class FAT(AllocationTable):
    Pointer = lambda s: dyn.block(s._uSectorSize)

class DIFAT(AllocationTable):
    Pointer = lambda s: dyn.clone(FAT, length=s._uSectorCount)

    def collect(self, count):
        res = self
        yield res
        while count > 0:
            res = res.next()
            yield res.l
            count -= 1
        return

    def next(self):
        last = self.value[-1]
        assert last.num() != ENDOFCHAIN.type, 'Encountered end of chain while trying to traverse to next DIFAT table'
        return last.dereference(_object_=DIFAT, length=self._uSectorCount)

class MINIFAT(DIFAT):
    Pointer = lambda s: dyn.block(s._uSectorSize)

### Types
class DirectoryEntry(pstruct.type):
    class Type(pint.enum, BYTE):
        _values_=[('Unknown',0),('Storage',1),('Stream',2),('Root',5)]
    class Flag(pint.enum, BYTE):
        _values_=[('red',0),('black',1)]
    class Identifier(pint.enum, DWORD):
        _values_=[('MAXREGSID',0xfffffffa),('NOSTREAM',0xffffffff)]

    _fields_ = [
        (dyn.clone(pstr.wstring, length=32), 'Name'),
        (USHORT, 'uName'),
        (Type, 'Type'),
        (Flag, 'Flag'),
        (Identifier, 'iLeftSibling'),
        (Identifier, 'iRightSibling'),
        (Identifier, 'iChild'),
        (CLSID, 'clsid'),
        (DWORD, 'dwState'),
        (FILETIME, 'ftCreation'),
        (FILETIME, 'ftModified'),
        (SECT, 'sectLocation'),
        (QWORD, 'qwSize'),
    ]

    def summary(self):
        return '{!r} {:s} SECT:{:x} SIZE:{:x} {:s}'.format(self['Name'].str(), self['Type'].summary(), self['sectLocation'].num(), self['qwSize'].num(), self['clsid'].summary())

class Directory(parray.block):
    _object_ = DirectoryEntry
    def blocksize(self):
        return self._uSectorSize

    def details(self):
        res = []
        maxoffsetlength = max(len('[{:x}]'.format(n.getoffset())) for n in self)
        maxnamelength = max(len('{!r}'.format(n['Name'].str())) for n in self)
        for i,n in enumerate(self):
            offset = '[{:x}]'.format(n.getoffset())
            res.append('{:<{offsetwidth}s} {:s}[{:d}] {!r:>{filenamewidth}} {:s} SECT:{:x} SIZE:{:x} {:s}'.format(offset, n.classname(), i, n['Name'].str(), n['Type'].summary(), n['sectLocation'].num(), n['qwSize'].num(), n['clsid'].summary(), offsetwidth=maxoffsetlength, filenamewidth=maxnamelength))
        return '\n'.join(res)
    def repr(self):
        return self.details()

class File(pstruct.type):
    class Header(pstruct.type):
        _fields_ = [
            (dyn.block(8), 'abSig'),
            (CLSID, 'clsid'),

            (USHORT, 'uMinorVersion'),      # Minor version (0x3e)
            (USHORT, 'uMajorVersion'),      # Major version (3 or 4)
            (USHORT, 'uByteOrder'),         # 0xfffe -- little-endian
        ]
    class SectorShift(pstruct.type):
        _fields_ = [
            (USHORT, 'uSectorShift'),       # Major version | 3 -> 0x9 | 4 -> 0xc
            (USHORT, 'uMiniSectorShift'),   # 6
        ]
    class Fat(pstruct.type):
        _fields_ = [
            (DWORD, 'csectDirectory'),      # Number of directory sectors
            (DWORD, 'csectFat'),            # Number of fat sectors
            (SECT, 'sectDirectory'),        # First directory sector location
            (DWORD, 'dwTransaction'),
        ]
    class Minifat(pstruct.type):
        class sectMinifat(SECT):
            def _object_(self):
                minifat = self.getparent(File.Minifat)
                return dyn.clone(MINIFAT, length=self._uSectorCount)
        _fields_ = [
            (ULONG, 'ulMiniSectorCutoff'), # Mini stream cutoff size
            (sectMinifat, 'sectMinifat'),  # First mini fat sector location
            (DWORD, 'csectMiniFat'),       # Number of mini fat sectors
        ]
    class Difat(pstruct.type):
        class sectDifat(SECT):
            def _object_(self):
                difat = self.getparent(File.Difat)
                l = difat['sectDifat'].li.num()
                return dyn.array(DIFAT.Sector, length=l)
        _fields_ = [
            (dyn.clone(SECT,_object_=DIFAT), 'sectDifat'),  # First difat sector location
            (DWORD, 'csectDifat'),                          # Number of difat sectors
        ]

    def __reserved(self):
        header = self['Header'].li
        assert header['uByteOrder'].li.num() == 0xfffe, "Invalid byte order specified for compound document"

        info = self['SectorShift'].li
        sectorSize = 2**info['uSectorShift'].li.num()
        self._uSectorSize = self.attributes['_uSectorSize'] = sectorSize
        self._uSectorCount = self.attributes['_uSectorCount'] = sectorSize / Sector.Pointer().blocksize()

        miniSectorSize = 2**info['uMiniSectorShift'].li.num()
        self._uMiniSectorSize = self.attributes['_uMiniSectorSize'] = miniSectorSize
        self._uMiniSectorCount = self.attributes['_uMiniSectorCount'] = miniSectorSize / Sector.Pointer().blocksize()

        return dyn.block(6)

    def __Table(self):
        length = sum(self[n].size() for n in ('Header','SectorShift','reserved','Fat','MiniFat','Difat'))
        return dyn.clone(DIFAT, length=109)
    def __Data(self):
        self.Sector = dyn.block(self._uSectorSize, __name__='Sector')
        return dyn.blockarray(self.Sector, self.source.size() - self._uSectorSize)

    _fields_ = [
        (Header, 'Header'),
        (SectorShift, 'SectorShift'),
        (__reserved, 'reserved'),
        (Fat, 'Fat'),
        (Minifat, 'MiniFat'),
        (Difat, 'Difat'),
        (dyn.clone(DIFAT,length=109), 'Table'),
        (__Data, 'Data'),
    ]

    @ptypes.utils.memoize(self=lambda s: s)
    def getDifat(self):
        '''Return an array containing the Difat'''
        count = self['Difat']['csectDifat'].num()

        # First Difat entries
        res = self.new(DIFAT, recurse=self.attributes, length=self._uSectorCount)
        map(res.append, (p for p in self['Table']))

        # Check if we need to find more
        next,count = self['Difat']['sectDifat'],self['Difat']['csectDifat'].num()
        if next.num() >= MAXREGSECT.type:
            return res

        # Append the contents of the other entries
        next = next.d.l
        for table in next.collect(count):
            map(res.append, (p for p in table))
        return res

    @ptypes.utils.memoize(self=lambda s: s)
    def getMiniFat(self):
        '''Return an array containing the MiniFAT'''
        mf = self['MiniFat']
        fat,count = mf['sectMiniFat'],mf['csectMiniFat'].num()
        res = self.new(MINIFAT, recurse=self.attributes, length=self._uSectorCount)
        for table in fat.d.l.collect(count-1):
            map(res.append, (p for p in table))
        return res

    @ptypes.utils.memoize(self=lambda s: s)
    def getFat(self):
        '''Return an array containing the FAT'''
        count,difat = self['Fat']['csectFat'].num(),self.getDifat()
        res = self.new(FAT, recurse=self.attributes, Pointer=FAT.Pointer, length=self._uSectorCount)
        for _,v in zip(xrange(count), difat):
            map(res.append, (p for p in v.d.l))
        return res

    def getDirectory(self):
        fat = self.getFat()
        dsect = self['Fat']['sectDirectory'].num()
        res = self.extract( fat.chain(dsect) )
        return res.cast(Directory, blocksize=lambda:res.size())

    def extract(self, iterable):
        res = self.new(ptype.container)
        map(res.append, map(self['Data'].__getitem__, iterable))
        return res

class ClipboardFormatOrAnsiString(pstruct.type):
    def __FormatOrAnsiString(self):
        marker = self['MarkerOrLength'].li.num()
        if marker in (0x00000000,):
            return ptype.undefined
        elif marker in (0xfffffffe, 0xffffffff):
            return DWORD
        return dyn.clone(pstr.string, length=marker)

    _fields_ = [
        (DWORD, 'MarkerOrLength'),
        (__FormatOrAnsiString, 'FormatOrAnsiString'),
    ]

class ClipboardFormatOrUnicodeString(pstruct.type):
    def __FormatOrUnicodeString(self):
        marker = self['MarkerOrLength'].li.num()
        if marker in (0x00000000,):
            return ptype.undefined
        elif marker in (0xfffffffe, 0xffffffff):
            return DWORD
        return dyn.clone(pstr.wstring, length=marker)

    _fields_ = [
        (DWORD, 'MarkerOrLength'),
        (__FormatOrUnicodeString, 'FormatOrUnicodeString'),
    ]

class MONIKERSTREAM(pstruct.type):
    class Stream(pstruct.type):
        _fields_ = [
            (CLSID, 'Clsid'),
            (lambda s: dyn.block(s.blocksize() - s['Clsid'].li.size()), 'Data'),
        ]
    _fields_ = [
        (DWORD, 'Size'),
        (lambda s: ptype.undefined if s['Size'].li.num() == 0 else dyn.clone(MONIKERSTREAM.Stream, blocksize=lambda _:s['Size'].li.num()), 'Stream'),
    ]

class OLEStream(pstruct.type):
    class StreamFlags(pint.enum, DWORD):
        _values_ = [
            ('Embedded', 0x00000000),
            ('Linked', 0x00000001),
            ('Implementation-Specific', 0x00001000),
        ]

    _fields_ = [
        (DWORD, 'Version'),
        (StreamFlags, 'Flags'),
        (DWORD, 'LinkUpdateOption'),
        (DWORD, 'Reserved1'),
        (MONIKERSTREAM, 'ReservedMoniker'),
        (MONIKERSTREAM, 'RelativeSourceMoniker'),
        (MONIKERSTREAM, 'AbsoluteSourceMoniker'),
        (LONG, 'ClsidIndicator'),
        (CLSID, 'Clsid'),
        (LengthPrefixedUnicodeString, 'ReservedDisplayName'),
        (DWORD, 'Reserved2'),
        (FILETIME, 'LocalUpdateTime'),
        (FILETIME, 'LocalCheckUpdateTime'),
        (FILETIME, 'RemoteUpdateTime'),
    ]

if False:
    class DEVMODEA(pstruct.type):
        class Fields(pstruct.type):
            # FIXME: this can't be right, it doesn't even align
            class dmFields(pbinary.flags):
                _fields_ = []
                _fields_+= [(1,_) for _ in ('DM_ORIENTATION', 'DM_PAPERSIZE', 'DM_PAPERLENGTH', 'DM_PAPERWIDTH', 'DM_SCALE')]
                _fields_+= [(1,_) for _ in ('DM_COPIES', 'DM_DEFAULTSOURCE', 'DM_PRINTQUALITY', 'DM_COLOR', 'DM_DUPLEX', 'DM_YRESOLUTION', 'DM_TTOPTION', 'DM_COLLATE', 'DM_NUP')]
                _fields_+= [(1,_) for _ in ('DM_ICMMETHOD', 'DM_ICMINTENT', 'DM_MEDIATYPE', 'DM_DITHERTYPE')]

            __cond = lambda n,t: lambda s: t if s['dmFields'][n] else pint.uint_t

            _fields_ = [
                (dmFields, 'dmFields'),
                (__cond('DM_ORIENTATION',WORD), 'dmOrientation'),
                (__cond('DM_PAPERSIZE',WORD), 'dmPaperSize'),
                (__cond('DM_PAPERLENGTH',WORD), 'dmPaperLength'),
                (__cond('DM_PAPERWIDTH',WORD), 'dmPaperWidth'),
                (__cond('DM_SCALE',WORD), 'dmScale'),
                (__cond('DM_COPIES',WORD), 'dmCopies'),
                (__cond('DM_DEFAULTSOURCE',WORD), 'dmDefaultSource'),
                (__cond('DM_PRINTQUALITY',WORD), 'dmPrintQuality'),
                (__cond('DM_COLOR',WORD), 'dmColor'),
                (__cond('DM_DUPLEX',WORD), 'dmDuplex'),
                (__cond('DM_YRESOLUTION',WORD), 'dmYResolution'),
                (__cond('DM_TTOPTION',WORD), 'dmTTOptions'),
                (__cond('DM_COLLATE',WORD), 'dmCollate'),
                (WORD, 'reserved0'),
                (DWORD, 'reserved1'),
                (DWORD, 'reserved2'),
                (DWORD, 'reserved3'),
                (__cond('DM_NUP',DWORD), 'dmNup'),
                (DWORD, 'reserved4'),
                (__cond('DM_ICMMETHOD',DWORD), 'dmICMMethod'),
                (__cond('DM_ICMINTENT',DWORD), 'dmICMIntent'),
                (__cond('DM_MEDIATYPE',DWORD), 'dmMediaType'),
                (__cond('DM_DITHERTYPE',DWORD), 'dmDitherType'),
                (DWORD, 'reserved5'),
                (DWORD, 'reserved6'),
                (DWORD, 'reserved7'),
                (DWORD, 'reserved8'),
            ]

        def __Padding(self):
            sz = self['dmSize'].li.num()
            total = 32+32+2+2+2+2
            res = sz - (total+s['fields'].li.size())
            return dyn.block(res)

        _fields_ = [
            (dyn.clone(pstr.string,length=32), 'dmDeviceName'),
            (dyn.clone(pstr.string,length=32), 'dmFormName'),
            (WORD, 'dmSpecVersion'),
            (WORD, 'dmDriverVersion'),
            (WORD, 'dmSize'),
            (WORD, 'dmDriverExtra'),
            (Fields, 'Fields'),
            (__Padding, 'Padding'),
            (lambda s: dyn.block(s['dmDriverExtra'].li.num()), 'PrinterData'),
        ]

class DVTARGETDEVICE(pstruct.type):
    def __DeviceData(self):
        sz = self.blocksize() - 8
        return dyn.block(sz)

    # FIXME: these WORDs are actually 16-bit rpointer types

    _fields_ = [
        (WORD, 'DriverNameOffset'),
        (WORD, 'DeviceNameOffset'),
        (WORD, 'PortNameOffset'),
        (WORD, 'ExtDevModeOffset'),
        (__DeviceData, 'DeviceData'),
    ]

class TOCENTRY(pstruct.type):
    _fields_ = [
        (ClipboardFormatOrAnsiString, 'AnsiClipboardFormat'),
        (DWORD, 'TargetDeviceSize'),
        (DWORD, 'Aspect'),
        (DWORD, 'Lindex'),
        (DWORD, 'Tymed'),
        (dyn.block(12), 'Reserved1'),
        (DWORD, 'Advf'),
        (DWORD, 'Reserved2'),
        (lambda s: dyn.clone(DVTARGETDEVICE, blocksize=lambda _:s['TargetDeviceSize'].li.num()), 'TargetDevice'),
    ]

class OLEPresentationStream(pstruct.type):
    class Dimensions(pstruct.type):
        _fields_ = [(DWORD,'Width'),(DWORD,'Height')]

    class TOC(pstruct.type):
        _fields_ = [
            (DWORD, 'Signature'),
            (DWORD, 'Count'),
            (lambda s: dyn.array(TOCENTRY, s['Count'].li.num()), 'Entry'),
        ]

    _fields_ = [
        (ClipboardFormatOrAnsiString, 'AnsiClipboardFormat'),
        (DWORD, 'TargetDeviceSize'),
        (DVTARGETDEVICE, 'TargetDevice'),
        (DWORD, 'Aspect'),
        (DWORD, 'Lindex'),
        (DWORD, 'Advf'),
        (DWORD, 'Reserved1'),
        (Dimensions, 'Dimensions'),
        (DWORD, 'Size'),
        (lambda s: dyn.block(s['Size'].num()), 'Data'),
        (dyn.block(18), 'Reserved2'),
        (TOC, 'Toc'),
    ]

class OLENativeStream(pstruct.type):
    _fields_ = [
        (DWORD, 'NativeDataSize'),
        (lambda s: dyn.block(s['NativeDataSize'].li.num()), 'NativeData'),
    ]

class CompObjHeader(pstruct.type):
    _fields_ = [
        (DWORD, 'Reserved1'),
        (DWORD, 'Version'),
        (dyn.block(20), 'Reserved2'),
    ]

class CompObjStream(pstruct.type):
    _fields_ = [
        (CompObjHeader, 'Header'),
        (LengthPrefixedAnsiString, 'AnsiUserType'),
        (ClipboardFormatOrAnsiString, 'AnsiClipboardFormat'),
        (LengthPrefixedAnsiString, 'Reserved1'),
        (DWORD, 'UnicodeMarker'),
        (LengthPrefixedUnicodeString, 'UnicodeUserType'),
        (ClipboardFormatOrUnicodeString, 'UnicodeUserType'),
        (LengthPrefixedUnicodeString, 'Reserved2'),
    ]

if __name__ == '__main__':
    import ptypes,storage
    filename = 'test.xls'
    filename = 'plant_types.ppt'
    ptypes.setsource(ptypes.prov.file(filename,mode='r'))

    a = storage.File()
    a = a.l
    print a['Header']
    print a['Fat']['sectDirectory'].d.l
    print a['MiniFat']['sectMinifat'].d.l[-1]
    print a['Difat']['sectDifat']
    difat = a.getDifat()
    fat = a.getFat()
    minifat = a.getMiniFat()

    d = a.getDirectory()
