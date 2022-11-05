import ptypes, ndk
from ptypes import *

import functools, operator, itertools, types, math
ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### Primitive types
class ULONG(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class USHORT(pint.uint16_t): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class QWORD(pint.uint64_t): pass

class CLSID(ndk.CLSID):
    class _Data(pint.uint_t):
        def summary(self):
            return "{:0{:d}x}".format(self.int(), self.size() * 2)

    class _Data4(pint.uint_t):
        def summary(self):
            res = self.serialize()
            d1 = ''.join(map('{:02x}'.format, bytearray(res[:2])))
            d2 = ''.join(map('{:02x}'.format, bytearray(res[2:])))
            return '-'.join([d1, d2])

    def __Data(self, byteorder, length):
        class _Data(byteorder(self._Data)):
            pass
        _Data.length = length
        return _Data

    def __Data1(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data, length=4)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        return self.__Data(order, 4)

    def __Data2and3(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data, length=2)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        return self.__Data(order, 2)

    def __Data4(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data4, length=8)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        class _Data4(order(self._Data4)):
            length = 8
        return _Data4

    _fields_ = [
        (__Data1, 'Data1'),
        (__Data2and3, 'Data2'),
        (__Data2and3, 'Data3'),
        (__Data4, 'Data4'),
    ]

class FILETIME(ndk.FILETIME): pass
class TIME_T(ndk.FILETIME): pass

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
        raise NotImplementedError
    def _object_(self):
        return dyn.block(self._uSectorSize)
    def summary(self, **options):
        return self.object.summary(**options)

@Sector.define
class REGSECT(Pointer): symbol, type = '+', None
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

Sector.default = Sector.lookup(None)

class SectorType(pint.enum, DWORD):
    def summary(self):
        return super(SectorType, self).summary() if self.has(self.int()) else "{:#010x}".format(self.int())
SectorType._values_ = [(item.__name__, type) for type, item in Sector.cache.items() if type is not None]
Pointer._value_ = SectorType

class SECT(Pointer): pass

### File-allocation tables that populate a single sector
class AllocationTable(parray.type):
    def summary(self, **options):
        try:
            member = self[0] if len(self) else self._object_()
            membername = member.typename() if ptype.isinstance(member) else member.__name__
        except NotImplementedError:
            membername = '(untyped)'
        items = str().join(Sector.withdefault(entry.int(), type=entry.int()).symbol for entry in self)
        return ' '.join(["{:s}[{:s}]".format(membername, "{:d}".format(len(self)) if self.initializedQ() else '...'), items])
    def _object_(self):
        raise NotImplementedError

    # Walk the linked-list of sectors
    def chain(self, index):
        yield index
        while self[index].int() <= MAXREGSECT.type:
            index = self[index].int()
            yield index
        return

    # Yields the index of all objects in the table that matches 'type'
    def filter(self, type):
        for index, item in enumerate(self):
            if item.object[type]:
                yield index
            continue
        return

    def allocate(self, count):
        '''Find space within the allocation table to allocate the specified number of sectors, and then return the new chain.'''
        available = (idx for idx, item in enumerate(self) if item.object['FREESECT'])
        chain = [sidx for _, sidx in zip(range(count), available)]

        # Create a second chain that contains the values that we need
        # to write to the table.
        sectors = chain[:] + ['ENDOFCHAIN']
        sectors.pop(0)

        # Now iterate through our chain assigning the sectors that compose it
        for nextidx, sidx in zip(sectors, chain):
            self[sidx].object.set(nextidx)
        return chain

    def __resize_increase(self, chain, count):
        '''Allocate the number of sectors to chain by appending more sectors to it, and then return all of its sectors.'''
        items = chain[:]
        if count < len(items):
            raise ValueError(count, len(items))

        # Ensure the last element marks the end of a chain.
        sidx = items[-1]
        if not self[sidx].object['ENDOFCHAIN']:
            raise ValueError(sidx, self[sidx].object)

        # Figure out how many more sectors we need to add,
        # and then allocate them. After they've been allocate,
        # then we just need to point the end of the chain to
        # the beginning of our allocation.
        allocation = self.allocate(count - len(items))
        if len(allocation):
            self[sidx].object.set(allocation[0])
        return items + allocation

    def __resize_decrease(self, chain, count):
        '''Decrease the number of sectors for chain by terminating it, and then return all of the sectors that were used to contain it.'''
        items = chain[:]
        if len(items) < count:
            raise ValueError(count, len(items))

        # consume count elements from the iterator
        iterable = (sidx for sidx in items)
        for _, sidx in zip(range(count), iterable):
            pass

        # Terminate the element, and any other indices that follow
        self[sidx].object.set('ENDOFCHAIN')
        for _, sidx in enumerate(iterable):
            self[sidx].object.set('FREESECT')
        return items

    def resize(self, chain, count):
        '''Modify the number of sectors used for chain.'''
        items = [sidx for sidx in self.chain(chain)]
        if count < len(items):
            result = self.__resize_decreate(items, count)
        elif count > len(items):
            result = self.__resize_increase(items, count)
        else:
            result = items[:]
        return result

class FAT(AllocationTable):
    class Pointer(Pointer):
        def _calculate_(self, nextindex):
            realindex = self.__index__
            return self._uSectorSize + realindex * self._uSectorSize

    def _object_(self):
        '''return a custom pointer that can be used to dereference entries in the FAT.'''
        t = dyn.block(self._uSectorSize)
        return dyn.clone(self.Pointer, _object_=t, __index__=len(self.value))

class DIFAT(AllocationTable):
    class IndirectPointer(Pointer):
        '''
        the value for an indirect pointer points directly to the sector
        containing its contents, so we can use it to calculate the index
        to the correct position of the file.
        '''
        def _calculate_(self, index):
            return self._uSectorSize + index * self._uSectorSize

    def _object_(self):
        '''return a custom pointer that can be used to dereference the FAT.'''
        t = dyn.clone(FAT, length=self._uSectorCount)
        return dyn.clone(DIFAT.IndirectPointer, _object_=t)

    def iterate(self):
        '''Yield all allocation tables dereferenced from the DiFat.'''
        for table in self.li:
            if table.object.int() >= MAXREGSECT.type:
                break
            yield table
        return

    def collect(self, count):
        '''Yield each entry from the DIFAT table.'''
        yield self

        while count > 0:
            self = self.next()
            yield self.l
            count -= 1
        return

    def next(self):
        '''Return the next DIFAT table.'''
        last = self.value[-1]
        if last.object['ENDOFCHAIN']:
            cls = self.__class__
            raise AssertionError("{:s}: Encountered {:s} while trying to traverse to next DIFAT table. {:s}".format('.'.join((cls.__module__, cls.__name__)), ENDOFCHAIN.typename(), last.summary()))
        return last.dereference(_object_=DIFAT, length=self._uSectorCount)

class MINIFAT(AllocationTable):
    class Pointer(Pointer):
        def _calculate_(self, next_index_from_chain):
            if self.__sector__:
                sector, index = self.__sector__, self.__index__
                return sector.getoffset() + self._uMiniSectorSize * index
            raise NotImplementedError

    def _object_(self):
        p, index = self.getparent(File), len(self.value)
        count, table = self._uSectorSize // self._uMiniSectorSize, [item for item in p.minisectors()]
        sector = table[index // count] if index // count < len(table) else None
        return dyn.clone(self.Pointer, _object_=dyn.block(self._uMiniSectorSize), __index__=index % count, __sector__=sector)

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
    class _abSig(ptype.block):
        length = 8

    _fields_ = [
        (_abSig, 'abSig'),
        (CLSID, 'clsid'),

        (USHORT, 'uMinorVersion'),      # Minor version (0x3e)
        (USHORT, 'uMajorVersion'),      # Major version (3 or 4)
        (uByteOrder, 'uByteOrder'),    # 0xfffe -- little-endian
    ]
    def summary(self):
        Fhex = bytes.hex if hasattr(bytes, 'hex') else operator.methodcaller('encode', 'hex')
        res = []
        res.append("({:s})".format(self['uByteOrder'].str()))
        res.append("0x{:s}".format(Fhex(self['abSig'].serialize())))
        res.append("version={:g}".format(self.Version()))
        res.append("clsid={:s}".format(self['clsid'].str()))
        return ' '.join(res)

    def Version(self):
        major, minor = (self[fld].int() for fld in ['uMajorVersion', 'uMinorVersion'])
        mantissa = pow(10, math.floor(1. + math.log10(minor)))
        return major + minor / mantissa

    def ByteOrder(self):
        return self['uByteOrder'].ByteOrder()

class HeaderSectorShift(pstruct.type):
    _fields_ = [
        (USHORT, 'uSectorShift'),       # Major version | 3 -> 0x9 | 4 -> 0xc
        (USHORT, 'uMiniSectorShift'),   # 6
    ]
    def summary(self):
        fields = ['uSectorShift', 'uMiniSectorShift']
        return ' '.join("{:s}={:d} ({:#x})".format(fld, self[fld].int(), pow(2, self[fld].int())) for fld in fields)
    def SectorSize(self):
        res = self['uSectorShift'].int()
        return pow(2, res)
    def MiniSectorSize(self):
        res = self['uMiniSectorShift'].int()
        return pow(2, res)

class HeaderFat(pstruct.type):
    _fields_ = [
        (DWORD, 'csectDirectory'),      # Number of directory sectors
        (DWORD, 'csectFat'),            # Number of fat sectors
        (SECT, 'sectDirectory'),        # First directory sector location
        (DWORD, 'dwTransaction'),
    ]
    def summary(self):
        fields = [
            ('sectDirectory', None),
            ('csectDirectory', "{:d}"),
            ('csectFat', "{:d}"),
            ('dwTransaction', "{:#010x}")
        ]
        return ' '.join("{:s}={!s}".format(fld, fmtstring.format(self[fld].int()) if fmtstring else self[fld].summary()) for fld, fmtstring in fields)

class HeaderMiniFat(pstruct.type):
    _fields_ = [
        (ULONG, 'ulMiniSectorCutoff'),  # Mini stream cutoff size
        (SECT, 'sectMiniFat'),          # First mini fat sector location
        (DWORD, 'csectMiniFat'),        # Number of mini fat sectors
    ]
    def summary(self):
        fields = [
            ('ulMiniSectorCutoff', "{:d}"),
            ('sectMiniFat', None),
            ('csectMiniFat', "{:d}")
        ]
        return ' '.join("{:s}={!s}".format(fld, fmtstring.format(self[fld].int()) if fmtstring else self[fld].summary()) for fld, fmtstring in fields)

class HeaderDiFat(pstruct.type):
    _fields_ = [
        (dyn.clone(SECT, _object_=DIFAT), 'sectDifat'), # First difat sector location
        (DWORD, 'csectDifat'),                          # Number of difat sectors
    ]
    def summary(self):
        fields = [
            ('sectDifat', None),
            ('csectDifat', "{:d}")
        ]
        return ' '.join("{:s}={!s}".format(fld, fmtstring.format(self[fld].int()) if fmtstring else self[fld].summary()) for fld, fmtstring in fields)

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
    def __clsid(self):
        p = self.getparent(File)
        header = p['Header']
        order = header.ByteOrder()
        return dyn.clone(CLSID, byteorder=order)

    _fields_ = [
        (dyn.clone(pstr.wstring, length=32), 'Name'),
        (USHORT, 'uName'),
        (DirectoryEntryType, 'Type'),
        (DirectoryEntryFlag, 'Flag'),
        (DirectoryEntryIdentifier, 'iLeftSibling'),
        (DirectoryEntryIdentifier, 'iRightSibling'),
        (DirectoryEntryIdentifier, 'iChild'),
        (__clsid, 'clsid'),
        (DWORD, 'dwState'),
        (FILETIME, 'ftCreation'),
        (FILETIME, 'ftModified'),
        (SECT, 'sectLocation'),     # FIXME: This pointer only supports regular sectors and not mini-sectors
        (QWORD, 'qwSize'),
    ]

    def summary(self):
        return "Name:{!r} {:s} SECT:{:x} SIZE:{:x} {:s}".format(self.Name(), self['Type'].summary(), self['sectLocation'].int(), self['qwSize'].int(), self['clsid'].summary())

    def Name(self):
        res = (1 + self['uName'].int()) // 2
        return u''.join(item.str() for item in self['Name'][0 : res]).rstrip(u'\0')

    def Id(self):
        return self['clsid']

    def Size(self):
        res = self['qwSize']
        return res.int()

    def Data(self, type=None, clamp=True):
        """Return the contents of the directory entry.
        If clamp is True, then resize the returned sectors according to the size specified in the directory entry.
        """
        F = self.getparent(File)

        # If the entry is a root type, then the data uses the fat and represents the mini-sector data.
        if self['Type']['Root']:
            minisector = dyn.block(self._uMiniSectorSize, __name__='MiniSector')
            datatype = dyn.blockarray(minisector, self['qwSize'].int())
            stream = F.Stream(self['sectLocation'])
            source = ptypes.provider.disorderly(stream, autoload={}, autocommit={})
            return self.new(datatype, source=source).l

        # Determine whether the data is stored in the minifat or the regular fat, and
        # then use it to fetch the data using the correct reference.
        fstream = F.MiniStream if self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int() else F.Stream
        data = fstream(self['sectLocation'].int())

        # Crop the block if specified, or use the regular one if not
        source = ptypes.provider.disorderly(data, autocommit={})
        res = self.new(DirectoryEntryData, length=self['qwSize'].int(), source=source).l if clamp else data

        # Load the correct child type from it if one was suggested
        return res if type is None else res.new(type).l

class Directory(parray.block):
    _object_ = DirectoryEntry
    def blocksize(self):
        return self._uSectorSize

    def details(self):
        Fescape = lambda self: eval("{!r}".format(self).replace('\\', '\\\\'))

        maxoffsetlength = max(len("[{:x}]".format(item.getoffset())) for item in self) if len(self) else 0
        maxnamelength = max(len(Fescape(item.Name())) for item in self) if len(self) else 0
        maxtypelength = max(len(item['Type'].summary()) for item in self) if len(self) else 0
        maxstartlength = max(len("{:x}".format(item['sectLocation'].int())) for item in self) if len(self) else 0
        maxsizelength = max(len("{:x}".format(item['qwSize'].int())) for item in self) if len(self) else 0

        res = []
        for i, item in enumerate(self):
            offset = "[{:x}]".format(item.getoffset())
            res.append("{:<{offsetwidth}s} {:s}[{:d}] {!s:>{filenamewidth}} {:<{typewidth}s} SECT:{:<{startwidth}x} SIZE:{:<{sizewidth}x} CLSID:{:s}".format(offset, item.classname(), i, Fescape(item.Name()), item['Type'].summary(), item['sectLocation'].int(), item['qwSize'].int(), item['clsid'].summary(), offsetwidth=maxoffsetlength, filenamewidth=maxnamelength, typewidth=maxtypelength, startwidth=maxstartlength, sizewidth=maxsizelength))
        return '\n'.join(res)

    def byname(self, name, index=0):
        for item in self:
            available = {item.Name(), item['Name'].str()}

            if name in available and index > 0:
                index -= 1

            elif name in available:
                return item
            continue
        raise KeyError("{:s}.byname({!r}): Unable to find directory entry matching the specified name.".format(self.classname(), name))

    def repr(self):
        return self.details()

    def RootEntry(self):
        iterable = (entry for entry in self if entry['Type']['Root'])
        return next(iterable, None)
    root = RootEntry

    def filter(self, type):
        critique = type if callable(type) else operator.itemgetter(type)
        iterable = ((index, entry) for index, entry in enumerate(self) if critique(entry['Type']))
        return iterable

    def stores(self):
        return self.filter('Storage')

    def roots(self):
        return self.filter('Root')

    def children(self, index):
        node = index if isinstance(index, DirectoryEntry) else self[index]
        iChild = node['iChild']
        if iChild['NOSTREAM']:
            raise TypeError(iChild)
        for index, node in self.enumerate(iChild.int()):
            yield index, node
        return

    def enumerate(self, index):
        if not isinstance(index, DirectoryEntry):
            (_, node), = stack = [(index, self[index])]
        else:
            index, node = self.value.index(index), index

        while not node['iLeftSibling']['NOSTREAM']:
            iLeft = node['iLeftSibling'].int()
            node = self[iLeft]
            stack.append((iLeft, node))

        for index, node in stack[::-1]:
            yield index, node
            if node['iRightSibling']['NOSTREAM']:
                continue
            iRight = node['iRightSibling'].int()
            for index, node in self.enumerate(iRight):
                yield index, node
            continue
        return

### File type
class FileSectors(parray.block):
    def _object_(self):
        res = self.getparent(File)
        return getattr(res, 'Sector', dyn.block(self._uSectorSize, __name__='Sector'))

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
        self._uSectorCount = self.attributes['_uSectorCount'] = sectorSize // Pointer().blocksize()

        # Store the mini-sector size attributes
        miniSectorSize = info.MiniSectorSize()
        self._uMiniSectorSize = self.attributes['_uMiniSectorSize'] = miniSectorSize
        self._uMiniSectorCount = self.attributes['_uMiniSectorCount'] = miniSectorSize // Pointer().blocksize()

        return dyn.block(6)

    def __Data(self):
        self.Sector = dyn.block(self._uSectorSize, __name__='Sector')
        return dyn.clone(FileSectors, blocksize=lambda _, cb=self.source.size() - self._uSectorSize: cb)

    def __Table(self):
        total, size = self._uSectorSize, sum(self[fld].li.size() for fld in ['Header', 'SectorShift', 'reserved', 'Fat', 'MiniFat', 'DiFat'])

        # Figure out how many pointers can fit into whatever number of bytes are left
        leftover = (total - size) // Pointer().blocksize()
        return dyn.clone(DIFAT, length=leftover)

    def __padding(self):
        total, size = self._uSectorSize, sum(self[fld].li.size() for fld in ['Header', 'SectorShift', 'reserved', 'Fat', 'MiniFat', 'DiFat', 'Table'])
        return dyn.block(max(0, total - size))

    _fields_ = [
        (Header, 'Header'),
        (HeaderSectorShift, 'SectorShift'),
        (__reserved, 'reserved'),
        (HeaderFat, 'Fat'),
        (HeaderMiniFat, 'MiniFat'),
        (HeaderDiFat, 'DiFat'),
        (__Table, 'Table'),
        (__padding, 'padding(Table)'),
        (__Data, 'Data'),
    ]

    @ptypes.utils.memoize(self=lambda self: self)
    def DiFat(self):
        '''Return an array containing the DiFat'''
        count = self['DiFat']['csectDifat'].int()

        ## First DiFat entries
        items = [self['Table']]

        ## Check if we need to find more and use them to make a source
        next, count = self['DiFat']['sectDifat'], self['DiFat']['csectDifat'].int()
        if next.int() < MAXREGSECT.type:
            next = next.d.l
            items.extend(table for table in next.collect(count))
        source = ptypes.provider.disorderly(items)

        ## Now we need to figure out the number of entries and then load it.
        length = sum(1 for item in itertools.chain(*items))
        count = len(self['Table']) + self._uSectorCount * (len(items) - 1)
        assert(count == length)

        ## We're loading it from the source temporarily, so we can still dereference the sector.
        return self.new(DIFAT, recurse=self.attributes, length=length).load(source=source)

    @ptypes.utils.memoize(self=lambda self: self)
    def MiniFat(self):
        '''Return an array containing the MiniFat'''
        res = self['MiniFat']
        start, count = res['sectMiniFat'].int(), res['csectMiniFat'].int()
        fat = self.Fat()
        iterable = fat.chain(start)
        sectors = [sector for sector in self.chain(iterable)]
        source = ptypes.provider.disorderly(sectors, autocommit={})
        return self.new(MINIFAT, recurse=self.attributes, length=count * self._uSectorCount).load(source=source)

    @ptypes.utils.memoize(self=lambda self: self)
    def Fat(self):
        '''Return an array containing the FAT'''
        count, difat = self['Fat']['csectFat'].int(), self.DiFat()
        sectors = [sector.d.l for _, sector in zip(range(count), difat)]
        source = ptypes.provider.disorderly(sectors, autocommit={})
        return self.new(FAT, recurse=self.attributes, length=self._uSectorCount).load(source=source)

    def difatsectors(self):
        '''Return all the tables in the document that contains DiFat.'''
        items = [self['Table']]

        # If there's nothing to continue with, then we're done.
        next, count = self['DiFat']['sectDifat'], self['DiFat']['csectDifat'].int()
        if next.int() >= MAXREGSECT.type:
            return items

        # Yield any other table entries containing the difat
        next = next.d.l
        for table in next.collect(count):
            items.append(table)
        return items

    def fatsectors(self):
        '''Return all sectors in the document which contains the Fat.'''
        count, difat = self['Fat']['csectFat'].int(), self.DiFat()

        result = []
        for _, items in zip(range(count), difat.iterate()):
            result.append(items.d.l)
        return result

    @ptypes.utils.memoize(self=lambda self: self)
    def minisectors(self):
        '''Return the sectors associated with the ministream as a list.'''
        fat, directory = self.Fat(), self.Directory()
        root = directory.RootEntry()
        start, _ = (root[item].int() for item in ['sectLocation', 'qwSize'])
        iterable = fat.chain(start)
        return [item for item in self.chain(iterable)]

    def directorysectors(self):
        fat, directory = self.Fat(), self['Fat']['sectDirectory'].int()
        iterable = fat.chain(directory)
        return [sector.cast(Directory) for sector in self.chain(iterable)]

    def chain(self, iterable):
        '''Yield the sector for each index specified in iterable.'''
        for index in iterable:
            yield self['Data'][index]
        return

    def minichain(self, iterable):
        '''Yield the minisector for each minisector index specified in iterable.'''
        sectors, shift = self.minisectors(), self['SectorShift']['uMiniSectorShift'].int()
        source = ptypes.provider.disorderly(sectors, autocommit={})
        minisectors = self.new(parray.type, _object_=dyn.block(pow(2, shift)), length=source.size() // pow(2, shift), source=source).l
        for index in iterable:
            yield minisectors[index]
        return

    def Stream(self, sector):
        '''Return the stream starting at a specified sector in the fat.'''
        fat = self.Fat()
        iterable = fat.chain(sector)
        items = [sector for sector in self.chain(iterable)]
        return self.new(ptype.container, value=items)

    def MiniStream(self, sector):
        '''Return the ministream starting at a specified minisector in the minifat.'''
        minifat = self.MiniFat()
        iterable = minifat.chain(sector)
        items = [minisector for minisector in self.minichain(iterable)]
        return self.new(ptype.container, value=items)

    def Directory(self):
        '''Return the whole Directory for the document.'''
        fat = self.Fat()
        dsect = self['Fat']['sectDirectory'].int()
        sectors = self.Stream(dsect)
        source = ptypes.provider.disorderly(sectors, autocommit={})
        return self.new(Directory, __name__='Directory', blocksize=lambda sz=sectors.size(): sz, source=source).l

### Specific stream types
class Stream(ptype.definition): cache = {}

class ClipboardFormatOrAnsiString(pstruct.type):
    def __FormatOrAnsiString(self):
        marker = self['MarkerOrLength'].li.int()
        if marker in {0x00000000}:
            return ptype.undefined
        elif marker in {0xfffffffe, 0xffffffff}:
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
        if marker in {0x00000000}:
            return ptype.undefined
        elif marker in {0xfffffffe, 0xffffffff}:
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
        (TIME_T, 'LocalUpdateTime'),
        (TIME_T, 'LocalCheckUpdateTime'),
        (TIME_T, 'RemoteUpdateTime'),
    ]

if False:
    class DEVMODEA(pstruct.type):
        class Fields(pstruct.type):
            # FIXME: this can't be right, it doesn't even align
            class dmFields(pbinary.flags):
                _fields_ = []
                _fields_+= [(1, _) for _ in ['DM_ORIENTATION', 'DM_PAPERSIZE', 'DM_PAPERLENGTH', 'DM_PAPERWIDTH', 'DM_SCALE']]
                _fields_+= [(1, _) for _ in ['DM_COPIES', 'DM_DEFAULTSOURCE', 'DM_PRINTQUALITY', 'DM_COLOR', 'DM_DUPLEX', 'DM_YRESOLUTION', 'DM_TTOPTION', 'DM_COLLATE', 'DM_NUP']]
                _fields_+= [(1, _) for _ in ['DM_ICMMETHOD', 'DM_ICMINTENT', 'DM_MEDIATYPE', 'DM_DITHERTYPE']]

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
    import sys, ptypes, office.storage as storage
    filename = 'test.xls'
    filename = 'plant_types.ppt'
    filename = sys.argv[1]
    ptypes.setsource(ptypes.prov.file(filename, mode='r'))

    z = storage.File()
    z = z.l
    print(z['Header'])
    print(z['Fat'])
    print(z['MiniFat'])
    print(z['DiFat'])
    difat = z.DiFat()
    fat = z.Fat()
    minifat = z.MiniFat()

    D = z.Directory()
