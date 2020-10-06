import ptypes, ndk
from ptypes import *

import six, datetime
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
    _fields_ = [
        (DWORD, 'dwLowDateTime'),
        (DWORD, 'dwHighDateTime')
    ]
    def timestamp(self):
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * 0x100000000 | + low
    def datetime(self):
        epoch = datetime.datetime(1601, 1, 1)
        return epoch + datetime.timedelta(microseconds=self.timestamp() / 10.0)
    def summary(self):
        epoch, ts = datetime.datetime(1601, 1, 1), self.timestamp()
        ts_s, ts_hns = ts // 1e7, ts % 1e7
        ts_ns = ts_hns * 1e-7

        res = epoch + datetime.timedelta(seconds=ts_s)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.9f}".format(res.second + ts_ns).zfill(12), ts)
TIME_T = FILETIME

class LengthPrefixedAnsiString(pstruct.type):
    _fields_ = [
        (DWORD, 'Length'),
        (lambda self: dyn.clone(pstr.string, length=self['Length'].li.int()), 'String')
    ]
    def summary(self):
        res = self['String'].str()
        return "(length={:d}) {!r}".format(self['Length'].int(), res)

class LengthPrefixedUnicodeString(pstruct.type):
    _fields_ = [
        (DWORD, 'Length'),
        (lambda self: dyn.clone(pstr.wstring, length=self['Length'].li.int()), 'String')
    ]
    def summary(self):
        res = self['String'].str()
        return "(length={:d}) {!r}".format(self['Length'].int(), res)

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
class REGSECT(Sector.Pointer): symbol, type = '+', None
Sector.default = REGSECT
@Sector.define
class MAXREGSECT(REGSECT): symbol, type = '+', 0xfffffffa
@Sector.define
class NotApplicable(DWORD): symbol, type = '-', 0xfffffffb
@Sector.define
class DIFSECT(DWORD): symbol, type = 'D', 0xfffffffc
@Sector.define
class FATSECT(DWORD): symbol, type = 'F', 0xfffffffd
@Sector.define
class ENDOFCHAIN(DWORD): symbol, type = '$', 0xfffffffe
@Sector.define
class FREESECT(DWORD): symbol, type = '.', 0xffffffff

class SECT(Sector.Pointer): pass

### File-allocation tables that populate a single sector
class AllocationTable(parray.type):
    def summary(self, **options):
        return str().join(Sector.withdefault(entry.int(), type=entry.int()).symbol for entry in self)
    def _object_(self):
        return dyn.clone(Sector.Pointer, _object_=self.Pointer)

class FAT(AllocationTable):
    Pointer = lambda self: dyn.block(self._uSectorSize)

    # Walk the linked-list of fat sectors
    def chain(self, index):
        yield index
        while self[index].int() <= MAXREGSECT.type:
            index = self[index].int()
            yield index
        return

class DIFAT(AllocationTable):
    Pointer = lambda self: dyn.clone(FAT, length=self._uSectorCount)

    # Walk
    def chain(self, index):
        yield index
        while self[index].int() <= MAXREGSECT.type:
            index = self[index].int()
            yield index
        return

    # Collect all DIFAT components (linked-list) until we hit ENDOFCHAIN
    def collect(self, count):
        yield self

        while count > 0:
            self = self.next()
            yield self.l
            count -= 1
        return

    def next(self):
        last = self.value[-1]
        if last.o['ENDOFCHAIN']:
            cls = self.__class__
            raise AssertionError("{:s}: Encountered {:s} while trying to traverse to next DIFAT table. {:s}".format('.'.join((cls.__module__, cls.__name__)), ENDOFCHAIN.typename(), last.summary()))
        return last.dereference(_object_=DIFAT, length=self._uSectorCount)

class MINIFAT(AllocationTable):
    Pointer = lambda self: dyn.clone(parray.type, length=self._uSectorSize // self._uMiniSectorSize, _object_=dyn.block(self._uMiniSectorSize))

    def chain(self, index):
        while self[index].int() <= MAXREGSECT.type:
            yield index
            index += 1
        return

### Header types
class uByteOrder(pint.enum, USHORT):
    _values_ = [
        ('LittleEndian', 0xfffe),
        ('BigEndian', 0xfeff),
    ]
    def ByteOrder(self):
        res = self.int()
        if res == 0xfffe:
            return ptypes.config.byteorder.littleendian
        elif res == 0xfeff:
            return ptypes.config.byteorder.bigendian
        cls = self.__class__
        raise ValueError("{:s}: Unsupported value set for enumeration \"uByteOrder\". {:s}".format('.'.join((cls.__module__, cls.__name__)), self.summary()))

class Header(pstruct.type):
    _fields_ = [
        (dyn.block(8), 'abSig'),
        (CLSID, 'clsid'),

        (USHORT, 'uMinorVersion'),      # Minor version (0x3e)
        (USHORT, 'uMajorVersion'),      # Major version (3 or 4)
        (uByteOrder, 'uByteOrder'),    # 0xfffe -- little-endian
    ]
    def ByteOrder(self):
        return self['uByteOrder'].ByteOrder()

class HeaderSectorShift(pstruct.type):
    _fields_ = [
        (USHORT, 'uSectorShift'),       # Major version | 3 -> 0x9 | 4 -> 0xc
        (USHORT, 'uMiniSectorShift'),   # 6
    ]
    def SectorSize(self):
        res = self['uSectorShift'].int()
        return 2 ** res
    def MiniSectorSize(self):
        res = self['uMiniSectorShift'].int()
        return 2 ** res

class HeaderFat(pstruct.type):
    _fields_ = [
        (DWORD, 'csectDirectory'),      # Number of directory sectors
        (DWORD, 'csectFat'),            # Number of fat sectors
        (SECT, 'sectDirectory'),        # First directory sector location
        (DWORD, 'dwTransaction'),
    ]

class HeaderMiniFat(pstruct.type):
    class _sectMiniFat(SECT):
        def _object_(self):
            mf = self.getparent(HeaderMiniFat)
            return dyn.clone(MINIFAT, length=self._uSectorCount) # FIXME: not sure if this works
    _fields_ = [
        (ULONG, 'ulMiniSectorCutoff'), # Mini stream cutoff size
        (_sectMiniFat, 'sectMiniFat'), # First mini fat sector location
        (DWORD, 'csectMiniFat'),       # Number of mini fat sectors
    ]

class HeaderDiFat(pstruct.type):
    # FIXME: _sectDifat should be used instead of just a generic pointer to a SECT
    class _sectDifat(SECT):
        def _object_(self):
            difat = self.getparent(HeaderDiFat)
            res = difat['sectDifat'].li.int()
            return dyn.array(DIFAT.Sector, length=res)
    _fields_ = [
        (dyn.clone(SECT, _object_=DIFAT), 'sectDifat'), # First difat sector location
        (DWORD, 'csectDifat'),                          # Number of difat sectors
    ]

### Directory types
class DirectoryEntryData(ptype.block):
    def properties(self):
        parent, res = self.parent, super(DirectoryEntryData, self).properties()
        if isinstance(parent, DirectoryEntry):
            res['index'] = int(parent.__name__)
            res['type'] = parent['Type'].str()
        return res
class DirectoryEntryType(pint.enum, BYTE):
    _values_=[('Unknown', 0), ('Storage', 1), ('Stream', 2), ('Root', 5)]
class DirectoryEntryFlag(pint.enum, BYTE):
    _values_=[('red', 0), ('black', 1)]
class DirectoryEntryIdentifier(pint.enum, DWORD):
    _values_=[('MAXREGSID', 0xfffffffa), ('NOSTREAM', 0xffffffff)]

class DirectoryEntry(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.wstring, length=32), 'Name'),
        (USHORT, 'uName'),
        (DirectoryEntryType, 'Type'),
        (DirectoryEntryFlag, 'Flag'),
        (DirectoryEntryIdentifier, 'iLeftSibling'),
        (DirectoryEntryIdentifier, 'iRightSibling'),
        (DirectoryEntryIdentifier, 'iChild'),
        (CLSID, 'clsid'),
        (DWORD, 'dwState'),
        (FILETIME, 'ftCreation'),
        (FILETIME, 'ftModified'),
        (SECT, 'sectLocation'),     # FIXME: This pointer only supports regular sectors and not mini-sectors
        (QWORD, 'qwSize'),
    ]

    def summary(self):
        return '{!r} {:s} SECT:{:x} SIZE:{:x} {:s}'.format(self['Name'].str(), self['Type'].summary(), self['sectLocation'].int(), self['qwSize'].int(), self['clsid'].summary())

    def Data(self, type=None, clamp=True):
        """Return the contents of the directory entry.
        If clamp is True, then resize the returned sectors according to the size specified in the directory entry.
        """
        F = self.getparent(File)

        # If the entry is a root type, then the data uses the fat and represents the mini-sector data.
        if self['Type']['Root']:
            fat = F.Fat()
            iterable = fat.chain(self['sectLocation'].int())
            minisector = dyn.block(self._uMiniSectorSize, __name__='MiniSector')
            datatype = dyn.blockarray(minisector, self['qwSize'].int())
            return F.chain(iterable).cast(datatype)

        # Determine whether the data is stored in the minifat or the regular fat
        fat = F.MiniFat() if self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int() else F.Fat()
        fData = F.MiniData if self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int() else F.Data

        # Now we can look up our sectors in the fat
        iterable = fat.chain(self['sectLocation'].int())
        data = fData(iterable, type=DirectoryEntryData)

        # Crop the block if specified, or use the regular one if not
        res = data.cast(DirectoryEntryData, length=self['qwSize'].int()) if clamp else data
        res.parent, res.__name__ = self, 'Data'

        # Spawn the correct child type if one was suggested
        if type is None:
            return res.new(ptype.block, offset=0, length=res.size(), source=ptypes.prov.proxy(res))
        return res.new(type, offset=0, source=ptypes.prov.proxy(res))

class Directory(parray.block):
    _object_ = DirectoryEntry
    def blocksize(self):
        return self._uSectorSize

    def details(self):
        res = []
        maxoffsetlength = max(len('[{:x}]'.format(item.getoffset())) for item in self)
        maxnamelength = max(len('{!r}'.format(item['Name'].str())) for item in self)
        for i, item in enumerate(self):
            offset = '[{:x}]'.format(item.getoffset())
            res.append('{:<{offsetwidth}s} {:s}[{:d}] {!r:>{filenamewidth}} {:s} SECT:{:x} SIZE:{:x} {:s}'.format(offset, item.classname(), i, item['Name'].str(), item['Type'].summary(), item['sectLocation'].int(), item['qwSize'].int(), item['clsid'].summary(), offsetwidth=maxoffsetlength, filenamewidth=maxnamelength))
        return '\n'.join(res)

    def byname(self, name):
        for item in self:
            if item['Name'].str() == name:
                return item
            continue
        raise KeyError("{:s}.byname({!r}): Unable to find directory entry matching the specified name!".format(self.classname(), name))

    def repr(self):
        return self.details()

    def RootEntry(self):
        iterable = (entry for entry in self if entry['Type']['Root'])
        return next(iterable, None)

### File type
class File(pstruct.type):
    def __reserved(self):
        '''Hook decoding of the "reserved" field in order to keep track of the sector and mini-sector dimensions.'''
        header = self['Header'].li

        # Validate the byte-order
        order = header.ByteOrder()

        # Store the sector size attributes
        info = self['SectorShift'].li
        sectorSize = info.SectorSize()
        self._uSectorSize = self.attributes['_uSectorSize'] = sectorSize
        self._uSectorCount = self.attributes['_uSectorCount'] = sectorSize // Sector.Pointer().blocksize()

        # Store the mini-sector size attributes
        miniSectorSize = info.MiniSectorSize()
        self._uMiniSectorSize = self.attributes['_uMiniSectorSize'] = miniSectorSize
        self._uMiniSectorCount = self.attributes['_uMiniSectorCount'] = miniSectorSize // Sector.Pointer().blocksize()

        return dyn.block(6)

    def __Data(self):
        self.Sector = dyn.block(self._uSectorSize, __name__='Sector')
        return dyn.blockarray(self.Sector, self.source.size() - self._uSectorSize)

    _fields_ = [
        (Header, 'Header'),
        (HeaderSectorShift, 'SectorShift'),
        (__reserved, 'reserved'),
        (HeaderFat, 'Fat'),
        (HeaderMiniFat, 'MiniFat'),
        (HeaderDiFat, 'DiFat'),
        (dyn.clone(DIFAT, length=109), 'Table'),    # FIXME: This hardcoded 109 is wrong if the Sector size is not 512
        (__Data, 'Data'),
    ]

    @ptypes.utils.memoize(self=lambda self: self)
    def DiFat(self):
        '''Return an array containing the DiFat'''
        count = self['DiFat']['csectDifat'].int()

        # First DiFat entries
        res = self.new(DIFAT, recurse=self.attributes, length=self._uSectorCount).alloc(length=0)
        [res.append(item) for item in iter(self['Table'])]

        # Check if we need to find more
        next, count = self['DiFat']['sectDifat'], self['DiFat']['csectDifat'].int()
        if next.int() >= MAXREGSECT.type:
            return res

        # Append the contents of the other entries
        next = next.d.l
        for table in next.collect(count):
            [res.append(item) for item in iter(table)]
        return res
    getDiFat = DiFat

    @ptypes.utils.memoize(self=lambda self: self)
    def MiniFat(self):
        '''Return an array containing the MiniFat'''
        res = self['MiniFat']
        start, count = res['sectMiniFat'].int(), res['csectMiniFat'].int()

        # Walk through the chain of FAT sectors that contain the MiniFat
        fat, res = self.Fat(), self.new(MINIFAT, recurse=self.attributes, length=self._uSectorCount).alloc(length=0)
        for index in fat.chain(start):
            sector = fat[index]
            if sector.o['ENDOFCHAIN']: break

            # Convert the sector into a MINIFAT, and append all its elements to our result
            mf = sector.d.l.cast(MINIFAT, length=self._uSectorCount)
            [res.append(item) for item in mf]
        return res
    getMiniFat = MiniFat

    @ptypes.utils.memoize(self=lambda self: self)
    def Fat(self):
        '''Return an array containing the FAT'''
        count, difat = self['Fat']['csectFat'].int(), self.DiFat()
        res = self.new(FAT, recurse=self.attributes, Pointer=FAT.Pointer, length=self._uSectorCount).alloc(length=0)
        for _, v in zip(range(count), difat):
            [res.append(item) for item in iter(v.d.l)]
        return res
    getFat = Fat

    def Directory(self):
        '''Return the whole Directory'''
        fat = self.Fat()
        dsect = self['Fat']['sectDirectory'].int()
        res = self.chain(fat.chain(dsect))
        return res.cast(Directory, __name__='Directory', blocksize=lambda: res.size())
    getDirectory = Directory

    def chain(self, iterable):
        '''Return the sector for each index specified in iterable.'''
        res = self.new(ptype.container, value=[])
        [res.append(item) for item in map(self['Data'].__getitem__, iterable)]
        return res

    def minichain(self, iterable):
        '''Return the minisector for each index specified in iterable.'''
        mf = self.MiniFat()
        res = self.new(ptype.container, value=[])
        for sptr in map(mf.__getitem__, iterable):
            [res.append(item) for item in sptr.d.l]
        return res

    def Data(self, iterable, type=None):
        '''Return the sectors for each index in iterable as a block.'''
        # If an integer was specified, then just return the sector by index
        if isinstance(iterable, six.integer_types):
            return self['Data'][iterable]

        # Now grab the container, and then cast it to a block
        res = self.chain(iterable)
        return res.cast(ptype.block, length=res.size()) if type is None else res.cast(type, blocksize=lambda cb=res.size(): cb)

    def __MiniData__(self):
        '''Return the mini-sector table.'''
        # First grab the directory
        D = self.Directory()

        # Find the first Root entry
        R = D.RootEntry()
        if R is None:
            cls = self.__class__
            raise ValueError("{:s}: Unable to locate a directory entry of type Root(5).".format('.'.join((cls.__module__, cls.__name__))))

        # Now we can return the whole table
        return R.Data()

    def MiniData(self, iterable, type=None):
        '''Return the minisectors for each index in iterable as a block.'''
        data = self.__MiniData__()

        # If an integer was specified, then just return the minisector by index
        if isinstance(iterable, six.integer_types):
            return data[iterable]

        # Now make a container and then cast it to a block
        res = self.new(ptype.container, value=[])
        [res.append(item) for item in map(data.__getitem__, iterable)]
        return res.cast(ptype.block, length=res.size()) if type is None else res.cast(type, blocksize=lambda cb=res.size(): cb)

### Specific stream types
class Stream(ptype.definition): cache = {}

class ClipboardFormatOrAnsiString(pstruct.type):
    def __FormatOrAnsiString(self):
        marker = self['MarkerOrLength'].li.int()
        if marker in (0x00000000, ):
            return ptype.undefined
        elif marker in (0xfffffffe, 0xffffffff):
            return DWORD
        return dyn.clone(pstr.string, length=marker)

    _fields_ = [
        (DWORD, 'MarkerOrLength'),
        (__FormatOrAnsiString, 'FormatOrAnsiString'),
    ]

    def summary(self):
        return "MarkerOrLength={:#0{:d}x} FormatOrAnsiString={:s}".format(self['MarkerOrLength'].int(), 2+self['MarkerOrLength'].size()*2, self['FormatOrAnsiString'].summary())

class ClipboardFormatOrUnicodeString(pstruct.type):
    def __FormatOrUnicodeString(self):
        marker = self['MarkerOrLength'].li.int()
        if marker in (0x00000000, ):
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
            (lambda self: dyn.block(self.blocksize() - self['Clsid'].li.size()), 'Data'),
        ]
    _fields_ = [
        (DWORD, 'Size'),
        (lambda self: ptype.undefined if self['Size'].li.int() == 0 else dyn.clone(MONIKERSTREAM.Stream, blocksize=lambda _: self['Size'].li.int()), 'Stream'),
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
                _fields_+= [(1, _) for _ in ('DM_ORIENTATION', 'DM_PAPERSIZE', 'DM_PAPERLENGTH', 'DM_PAPERWIDTH', 'DM_SCALE')]
                _fields_+= [(1, _) for _ in ('DM_COPIES', 'DM_DEFAULTSOURCE', 'DM_PRINTQUALITY', 'DM_COLOR', 'DM_DUPLEX', 'DM_YRESOLUTION', 'DM_TTOPTION', 'DM_COLLATE', 'DM_NUP')]
                _fields_+= [(1, _) for _ in ('DM_ICMMETHOD', 'DM_ICMINTENT', 'DM_MEDIATYPE', 'DM_DITHERTYPE')]

            __cond = lambda n, t: lambda self: t if self['dmFields'][n] else pint.uint_t

            _fields_ = [
                (dmFields, 'dmFields'),
                (__cond('DM_ORIENTATION', WORD), 'dmOrientation'),
                (__cond('DM_PAPERSIZE', WORD), 'dmPaperSize'),
                (__cond('DM_PAPERLENGTH', WORD), 'dmPaperLength'),
                (__cond('DM_PAPERWIDTH', WORD), 'dmPaperWidth'),
                (__cond('DM_SCALE', WORD), 'dmScale'),
                (__cond('DM_COPIES', WORD), 'dmCopies'),
                (__cond('DM_DEFAULTSOURCE', WORD), 'dmDefaultSource'),
                (__cond('DM_PRINTQUALITY', WORD), 'dmPrintQuality'),
                (__cond('DM_COLOR', WORD), 'dmColor'),
                (__cond('DM_DUPLEX', WORD), 'dmDuplex'),
                (__cond('DM_YRESOLUTION', WORD), 'dmYResolution'),
                (__cond('DM_TTOPTION', WORD), 'dmTTOptions'),
                (__cond('DM_COLLATE', WORD), 'dmCollate'),
                (WORD, 'reserved0'),
                (DWORD, 'reserved1'),
                (DWORD, 'reserved2'),
                (DWORD, 'reserved3'),
                (__cond('DM_NUP', DWORD), 'dmNup'),
                (DWORD, 'reserved4'),
                (__cond('DM_ICMMETHOD', DWORD), 'dmICMMethod'),
                (__cond('DM_ICMINTENT', DWORD), 'dmICMIntent'),
                (__cond('DM_MEDIATYPE', DWORD), 'dmMediaType'),
                (__cond('DM_DITHERTYPE', DWORD), 'dmDitherType'),
                (DWORD, 'reserved5'),
                (DWORD, 'reserved6'),
                (DWORD, 'reserved7'),
                (DWORD, 'reserved8'),
            ]

        def __Padding(self):
            sz = self['dmSize'].li.int()
            total = 32+32+2+2+2+2
            res = sz - (total+s['fields'].li.size())
            return dyn.block(res)

        _fields_ = [
            (dyn.clone(pstr.string, length=32), 'dmDeviceName'),
            (dyn.clone(pstr.string, length=32), 'dmFormName'),
            (WORD, 'dmSpecVersion'),
            (WORD, 'dmDriverVersion'),
            (WORD, 'dmSize'),
            (WORD, 'dmDriverExtra'),
            (Fields, 'Fields'),
            (__Padding, 'Padding'),
            (lambda self: dyn.block(self['dmDriverExtra'].li.int()), 'PrinterData'),
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
        (lambda self: dyn.clone(DVTARGETDEVICE, blocksize=lambda _: self['TargetDeviceSize'].li.int()), 'TargetDevice'),
    ]

class OLEPresentationStream(pstruct.type):
    class Dimensions(pstruct.type):
        _fields_ = [(DWORD, 'Width'), (DWORD, 'Height')]

    class TOC(pstruct.type):
        _fields_ = [
            (DWORD, 'Signature'),
            (DWORD, 'Count'),
            (lambda self: dyn.array(TOCENTRY, self['Count'].li.int()), 'Entry'),
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
        (lambda self: dyn.block(self['Size'].int()), 'Data'),
        (dyn.block(18), 'Reserved2'),
        (TOC, 'Toc'),
    ]

class OLENativeStream(pstruct.type):
    _fields_ = [
        (DWORD, 'NativeDataSize'),
        (lambda self: dyn.block(self['NativeDataSize'].li.int()), 'NativeData'),
    ]

class CompObjHeader(pstruct.type):
    _fields_ = [
        (WORD, 'Reserved1'),
        (uByteOrder, 'ByteOrder'),
        (DWORD, 'Version'),
        (DWORD, 'Reserved2'),
        (dyn.array(DWORD, 4), 'Reserved3'),
    ]

@Stream.define
class CompObjStream(pstruct.type):
    type = '\x01CompObj'
    _fields_ = [
        (CompObjHeader, 'Header'),
        (LengthPrefixedAnsiString, 'AnsiUserType'),
        (ClipboardFormatOrAnsiString, 'AnsiClipboardFormat'),
        (LengthPrefixedAnsiString, 'AnsiProgramId'),
        (DWORD, 'UnicodeMarker'),
        (LengthPrefixedUnicodeString, 'UnicodeUserType'),
        (ClipboardFormatOrUnicodeString, 'UnicodeClipboardFormat'),
        (LengthPrefixedUnicodeString, 'UnicodeProgramId'),
    ]

if __name__ == '__main__':
    import ptypes, office.storage as storage
    filename = 'test.xls'
    filename = 'plant_types.ppt'
    ptypes.setsource(ptypes.prov.file(filename, mode='r'))

    a = storage.File()
    a = a.l
    print(a['Header'])
    print(a['Fat']['sectDirectory'].d.l)
    print(a['MiniFat']['sectMiniFat'].d.l[-1])
    print(a['DiFat']['sectDifat'])
    difat = a.DiFat()
    fat = a.Fat()
    minifat = a.MiniFat()

    d = a.Directory()
