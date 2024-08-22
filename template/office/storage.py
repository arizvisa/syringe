import ptypes
from ptypes import *
from . import intsafe

import sys, functools, operator, itertools, types, math, logging
ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
logger = logging.getLogger(__name__)

### Primitive types
class ULONG(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class USHORT(pint.uint16_t): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class QWORD(pint.uint64_t): pass

class CLSID(intsafe.CLSID): pass
class FILETIME(intsafe.FILETIME): pass
class TIME_T(intsafe.FILETIME): pass

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
    def alloc(self, *args, **attributes):
        res = super(SectorType, self).alloc(*args, **attributes)
        return res.set(0xffffffff)
SectorType._values_ = [(item.__name__, type) for type, item in Sector.cache.items() if type is not None]
Pointer._value_ = SectorType

class SECT(Pointer):
    def _calculate_(self, index):
        parent = self.parent
        uHeaderSize = getattr(parent if parent else self, '_uHeaderSize', pow(2, 9))
        uSectorSize = getattr(parent if parent else self, '_uSectorSize', 0)
        return uHeaderSize + index * uSectorSize

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

    def alloc(self, *values, **attrs):
        values = values if values else [['FREESECT'] * len(self)]
        return super(AllocationTable, self).alloc(*values, **attrs)

    def _object_(self):
        raise NotImplementedError

    def set(self, *values, **attrs):
        '''Overwrite the sector values with the list of values while preserving the table size.'''
        if not values:
            return super(AllocationTable, self).set(*values, **attrs)
        [value] = values
        iterable = value if len(self) <= len(value) else itertools.chain(value, ['FREESECT'] * len(self))
        items = [item for _, item in zip(range(len(self)), iterable)]
        return super(AllocationTable, self).set(items, **attrs)

    # Walk the linked-list of sectors
    def chain(self, index):
        '''Yield the index of each sector in the chain starting at the given index.'''
        maximum = MAXREGSECT.type
        if 0 <= index <= maximum:
            yield index
        while 0 <= index <= maximum and self[index].int() <= maximum:
            index = self[index].int()
            yield index
        return

    def count(self, index):
        '''Return the number of sectors contained by a chain starting at the specified index until termination or encountering a cycle.'''
        integer_types = tuple(operator.add(index, sys.maxsize).__class__ for index in range(2))
        visited, iterable = {index for index in []}, self.chain(index) if isinstance(index, integer_types) else index
        for index in iterable:
            if index in visited:
                break
            visited.add(index)
        return len(visited)

    # Yields the index of all objects in the table that matches 'type'
    def enumerate(self, type=None):
        '''Yield the index and pointer for each item within the table.'''
        critique = (lambda _: True) if type is None else type if callable(type) else (lambda item, type=type: item.object[type])
        return ((index, item) for index, item in enumerate(self) if critique(item))

    def iterate(self, *args, **kwargs):
        '''Yield the pointer for each item within the table.'''
        return (item for _, item in self.enumerate(*args, **kwargs))

    # Updating a chain within the allocation table
    def link(self, chain):
        '''Link a given chain of sectors together overwriting any previous entries but leaving the entries uncommitted.'''
        result, chain = [], [index for index in chain]
        while len(chain) > 1:
            index = chain.pop(0)
            sector, value = self[index], chain[0]
            sector.set(value), result.append(index)

        if chain:
            index = chain.pop(0)
            self[index].set('ENDOFCHAIN'), result.append(index)

        assert(not chain)
        return result

    def unlink(self, chain, type='FREESECT'):
        '''Completely unlink and return the given chain of sectors by overwriting their table entries with the specified type and leaving them uncommitted.'''
        chain = [index for index in chain] if hasattr(chain, '__iter__') else [index for index in self.chain(chain)]
        [self[index].set(type) for index in chain]
        return chain

    # Resizing a chain within the allocation table.
    def reduceChain(self, chain, amount, type='FREESECT'):
        '''Reduce a chain by releasing the specified number of sectors, leaving them uncommitted, and returning the new smaller chain.'''
        chain = [index for index in chain] if hasattr(chain, '__iter__') else [index for index in self.chain(chain)]
        result = self.link(chain[:-amount] if amount else chain)
        released = chain[-amount:] if amount else []
        [self[index].set(type) for index in released]
        return result

    def growChain(self, chain, amount, available=None):
        '''Grow a chain by adding the specified count of sectors from available, leaving then uncommitted, and returning the new larger chain.'''
        chain = [index for index in chain] if hasattr(chain, '__iter__') else [index for index in self.chain(chain)]
        source = self.availableEntries() if available is None else (index for index in available)
        additional = (index for _, index in zip(range(amount), source))
        return self.link(chain + [index for index in additional])

    def resizeChain(self, chain, count, available=None):
        '''Modify the length of a chain to the specified count, leaving each entry in the allocation table uncommitted, and then return the new chain.'''
        chain = [index for index in chain] if hasattr(chain, '__iter__') else [index for index in self.chain(chain)]
        if count < len(chain):
            return self.reduceChain(chain, len(chain) - count)
        elif count > len(chain):
            return self.growChain(chain, count - len(chain), available=available)
        return chain

    # Calculations using things from the allocation table
    def sectorSize(self):
        '''Return the number of bytes occupied by a sector being described by the current allocation table.'''
        pointer_t = self._object_ if ptypes.istype(self._object_) else self._object_()
        assert(issubclass(pointer_t, Pointer)), "{:s} is not a subclass of {:s}.".format(pointer_t.typename(), Pointer.typename())
        sector_t = pointer_t._object_
        sector = self.new(sector_t) if any(F(sector_t) for F in [ptypes.istype, callable]) else sector_t
        assert(ptypes.isinstance(sector)), "{!s} is not an instance.".format(sector_t)
        try: result = sector.blocksize()
        except ptypes.error.InitializationError: result = sector.a.blocksize()
        return result

    def entries(self, bytes):
        '''Return the required number of entries in order to store the specified number of bytes.'''
        size = self.sectorSize()
        count, extra = divmod(bytes, size) if size else 0
        return 1 + count if extra else count

    def used(self, chain):
        '''Return the total number of bytes used by the given `chain`.'''
        return self.count(chain) * self.sectorSize()

    def required(self, *chain):
        '''Return the minimum number of sectors required to store the specified chain or all the table entries if a chain is not provided.'''
        maxregsect = SectorType.byname('MAXREGSECT')
        ignored = {maxregsect} | {SectorType.byname(name) for name in ['FREESECT', 'NotApplicable']}
        if not chain:
            everything = ((index, item.object) for index, item in enumerate(self))
            filtered = ((index, item.int()) for index, item in everything if item.int() not in ignored)
            iterable = (index for index in itertools.chain.from_iterable(filtered) if index <= maxregsect)

        else:
            [integer] = chain
            integers = integer if hasattr(integer, '__iter__') else self.chain(integer)
            iterable = (index for index in integers if index <= maxregsect)

        # Grab all the unique indices and use them to calculate the total numbre
        # of required sectors. We only have 0 if nothing in the table was set.
        used = {index for index in iterable}
        return 1 + max(used) if used else 0

    # General utilities used for calculating sizes.
    def tableSize(self, length):
        '''Return the size of an allocation table that can hold the specified number of entries.'''
        integer_types = tuple(operator.add(index, sys.maxsize).__class__ for index in range(2))
        count = length if isinstance(length, integer_types) else len(length)
        return count * self.new(self._object_).a.size()

    def streamSize(self, length):
        '''Return the size of a stream containing the specified number of sectors from the allocation table.'''
        integer_types = tuple(operator.add(index, sys.maxsize).__class__ for index in range(2))
        count = length if isinstance(length, integer_types) else len(length)
        return self.sectorSize() * count

    # Methods that can be used to search for entries of specific types.
    def contiguousEntries(self, start, count, type='FREESECT'):
        '''Yield each chain from the allocation table at index `start` that represents a contiguous number of entries as specified by `count`.'''
        critique = type if callable(type) else (lambda item, type=type: item.object[type])
        available = (index for index in range(start, len(self)) if critique(self[index]))
        iterable = ((index, index + count) for index in available)
        for left, right in iterable:
            items = self[left : right]
            if len(items) == count and all(critique(item) for item in items):
                yield [index for index in range(left, right)]
            continue
        return

    def availableEntries(self, start=0, stop=None, type='FREESECT'):
        '''Yield each entry of the allocation table that is available and unused.'''
        critique = type if callable(type) else (lambda item, type=type: item.object[type])
        iterable = range(start, len(self) if stop is None else stop)
        return (index for index in range(start, len(self)) if critique(self[index]))

class AllocationTableMixin(object):
    def __entry_count__(self):
        if hasattr(self, '_uSectorCount'):
            return self._uSectorCount
        elif self.parent or isinstance(self, File):
            return self.getparent(File)._uSectorCount
        raise NotImplementedError

    def __difat_entry__(self):
        '''Return the element type used for each element of the indirect file allocation table.'''
        entry, count = self.__fat_entry__(), self.__entry_count__()
        object = dyn.clone(FAT, length=count, _object_=entry)
        return dyn.clone(DIFAT.IndirectPointer, _object_=object)

    def __fat_entry__(self):
        '''Return the element type used for each element of the file allocation table.'''
        count = self.__entry_count__()
        object = dyn.clone(FileSector, length=count)
        return dyn.clone(FAT.Pointer, _object_=object)

    def __minientry_count__(self):
        '''Return the number of minisectors within a file sector.'''
        if all(hasattr(self, attribute) for attribute in ['_uSectorCount', '_uMiniSectorSize']):
            return self._uSectorSize // self._uMiniSectorSize
        elif self.parent or isinstance(self, File):
            self = self.getparent(File)
            return self._uSectorSize // self._uMiniSectorSize
        raise NotImplementedError

    def __minifat_entry__(self):
        '''Return the element type used for each element of the miniature file allocation table.'''
        raise NotImplementedError

class FAT(AllocationTable):
    class Pointer(Pointer):
        def _calculate_(self, nextindex):
            realindex = self.__index__
            return self._uHeaderSize + realindex * self._uSectorSize
        def dereference(self, **attrs):
            parent = self.getparent(FAT)
            attrs.setdefault('source', parent.parent.source)
            return super(FAT.Pointer, self).dereference(**attrs)

    def _object_(self):
        '''return a custom pointer that can be used to dereference entries in the FAT.'''
        target = dyn.clone(FileSector, length=self._uSectorSize)
        return dyn.clone(self.Pointer, _object_=target, __index__=len(self.value))

class DIFAT(AllocationTable, AllocationTableMixin):
    class IndirectPointer(Pointer):
        '''
        the value for an indirect pointer points directly to the sector
        containing its contents, so we can use it to calculate the index
        to the correct position of the file.
        '''
        def _calculate_(self, index):
            return self._uHeaderSize + index * self._uSectorSize
        def dereference(self, **attrs):
            parent = self.getparent(File)
            #attrs.setdefault('source', ptypes.provider.proxy(parent, autocommit={}))
            attrs.setdefault('source', parent.source)
            return super(DIFAT.IndirectPointer, self).dereference(**attrs)

    def _object_(self):
        '''return a custom pointer that can be used to dereference the FAT.'''
        target = dyn.clone(FAT, length=self._uSectorCount)
        return dyn.clone(DIFAT.IndirectPointer, _object_=target)

    def enumerate(self):
        '''Yield the index and IndirectPointer of each entry within the DiFat.'''
        for index, table in enumerate(self.li):
            if table.object.int() > MAXREGSECT.type:
                break
            yield index, table
        return

    def iterate(self):
        '''Yield each IndirectPointer for each entry within the DiFat.'''
        return (entry for _, entry in self.enumerate())

    def collect(self):
        """Yield each sector that follows the current DIFAT sector.

        If the current DIFAT instance is stored in the header, then no sectors will be returned.
        """
        cls = self.__class__
        if self.getoffset() < self._uHeaderSize:
            return

        this, visited = self, {sector for sector in []}
        while isinstance(this, cls) and this._uHeaderSize <= this.getoffset():
            yield this.l

            pointer, length = this.value[-1], getattr(this, '_uSectorCount', 0)
            if pointer.object['ENDOFCHAIN']:
                break

            elif pointer.object.int() > MAXREGSECT.type:
                logger.error("{:s}: Encountered {:#s} while trying to traverse to next {:s} table at {:s}.".format('.'.join([cls.__module__, cls.__name__]), pointer.object, cls.typename(), this.instance()))
                break

            target = dyn.clone(cls, length=length) if length else cls
            object = dyn.clone(cls.IndirectPointer, _object_=target)
            this = pointer.cast(object).dereference()

        if this.getoffset() < self._uHeaderSize:
            F = self.getparent(File)
            logger.error("{:s}: Encountered table {:s} that references header {:s} instead of a valid sector.".format('.'.join([cls.__module__, cls.__name__]), this.instance(), F.instance()))
        return

    def tableSize(self, length):
        '''Return the size of a DIFAT table that can hold the specified number of entries (including the link entry).'''

        # we need to handle this specially because the last entry of each sector
        # will occupy the link for the entries in the DIFAT table.
        size, esize = self.sectorSize(), self.new(self._object_).a.size()
        count, extra = divmod(size, esize)
        assert(not(extra))

        # if the number of entries fits within a single sector,
        # then we're good and can use it to calculate our length.
        if length <= count:
            return length * esize

        # otherwise, we need to figure out how many sectors are actually
        # needed to store the entries and include the link in the calculation.
        sectors, extra = divmod(length, count - 1)
        assert(sectors)

        # now we can calculate the total number of entries (including the link
        # entry) that are needed to store the requested number of entries.
        res = sectors * count + extra if extra > 1 else sectors * count + extra - 1
        return esize * res

class MINIFAT(AllocationTable):
    class Pointer(Pointer):
        def _calculate_(self, next_index_from_chain):
            if not hasattr(self, '__minisource__'):
                sector, index, count = self.__sector__, self.__index__, self._uSectorSize // self._uMiniSectorSize
                sector_index = index % count
                return sector.getoffset() + self._uMiniSectorSize * sector_index
            elif hasattr(self, '__index__'):
                return self.__index__ * self._uMiniSectorSize
            raise NotImplementedError

        def dereference(self, **attrs):
            if hasattr(self, '__minisource__'):
                attrs.setdefault('source', self.__minisource__)
            return super(MINIFAT.Pointer, self).dereference(**attrs)

    def _object_(self):
        parent, index = self.getparent(File), len(self.value)
        count, table = self._uSectorSize // self._uMiniSectorSize, self.__minitable__ if hasattr(self, '__minitable__') else [item for item in parent.__ministream_sectors__()]
        sector = table[index // count] if index // count < len(table) else None
        return dyn.clone(self.Pointer, _object_=parent.MiniSector, __index__=index, __sector__=sector, __minisource__=ptypes.provider.disorderly(table, autocommit={}))

### Header types
class uByteOrder(pint.enum, USHORT):
    _values_ = [
        ('little', 0xfffe),
        ('big', 0xfeff),
    ]
    def ByteOrder(self):
        res = self.int()
        if res == 0xfffe:
            return ptypes.config.byteorder.littleendian
        elif res == 0xfeff:
            return ptypes.config.byteorder.bigendian
        cls, order = self.__class__, ptypes.Config.integer.order
        logger.debug("{:s}: Using default byteorder ({!s}) as an unsupported value was set for enumeration \"uByteOrder\" : {:s}".format('.'.join([cls.__module__, cls.__name__]), order.__name__, self.summary()))
        return order

    def set(self, order):
        integer_types = tuple(operator.add(index, sys.maxsize).__class__ for index in range(2))
        if isinstance(order, integer_types):
            return super(uByteOrder, self).set(order)
        elif order.lower().startswith(('big', 'little')):
            return super(uByteOrder, self).set('big') if order.lower().startswith('big') else super(uByteOrder, self).set('little')
        return super(uByteOrder, self).set(order)

    def alloc(self, *args, **attrs):
        res = super(uByteOrder, self).alloc(*args, **attrs)
        return res.set(sys.byteorder)

class Header(pstruct.type):
    class _abSig(ptype.block):
        length, _constant_ = 8, b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        def default(self):
            res, bytes = self.copy(), self._constant_
            return res.set(bytes)
        def valid(self):
            return self.serialize() == self._constant_
        def alloc(self, *args, **attrs):
            res = super(Header._abSig, self).alloc(*args, **attrs)
            return res.set(self._constant_)
        def properties(self):
            res = super(Header._abSig, self).properties()
            if self.initializedQ():
                res['valid'] = self.valid()
            return res

    _fields_ = [
        (_abSig, 'abSig'),
        (CLSID, 'clsid'),

        (USHORT, 'uMinorVersion'),      # Minor version (0x3e)
        (USHORT, 'uMajorVersion'),      # Major version (3 or 4)
        (uByteOrder, 'uByteOrder'),     # 0xfffe -- little-endian
    ]

    def alloc(self, **fields):
        fields.setdefault('uByteOrder', uByteOrder)
        fields.setdefault('abSig', self._abSig)
        res = super(Header, self).alloc(**fields)
        res if 'uMinorVersion' in fields else res['uMinorVersion'].set(0x3e)
        res if 'uMajorVersion' in fields else res['uMajorVersion'].set(3)
        res if 'uByteOrder' in fields else res['uByteOrder'].set('little')
        return res

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
        mantissa = pow(10, math.floor(1. + math.log10(minor))) if minor else 0
        return major + (minor / mantissa if mantissa else 0)

    def ByteOrder(self):
        return self['uByteOrder'].ByteOrder()

class HeaderSectorShift(pstruct.type):
    _fields_ = [
        (USHORT, 'uSectorShift'),       # Major version | 3 -> 0x9 | 4 -> 0xc
        (USHORT, 'uMiniSectorShift'),   # 6
    ]
    def alloc(self, **fields):
        fields.setdefault('uSectorShift', 9)
        fields.setdefault('uMiniSectorShift', 6)
        return super(HeaderSectorShift, self).alloc(**fields)
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

    def alloc(self, **fields):
        fields.setdefault('sectDirectory', 'ENDOFCHAIN')
        return super(HeaderFat, self).alloc(**fields)

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

    def alloc(self, **fields):
        fields.setdefault('sectMiniFat', 'ENDOFCHAIN')
        fields.setdefault('ulMiniSectorCutoff', 0x1000)
        return super(HeaderMiniFat, self).alloc(**fields)

class HeaderDiFat(pstruct.type, AllocationTableMixin):
    def __sectDifat(self):
        entry = self.__difat_entry__()
        object = dyn.clone(DIFAT, _object_=self.__difat_entry__(), length=self.__entry_count__())
        return dyn.clone(SECT, _object_=object)

    _fields_ = [
        (__sectDifat, 'sectDifat'),     # First difat sector location
        (DWORD, 'csectDifat'),          # Number of difat sectors
    ]

    def summary(self):
        fields = [
            ('sectDifat', None),
            ('csectDifat', "{:d}")
        ]
        return ' '.join("{:s}={!s}".format(fld, fmtstring.format(self[fld].int()) if fmtstring else self[fld].summary()) for fld, fmtstring in fields)

    def alloc(self, **fields):
        fields.setdefault('sectDifat', 'ENDOFCHAIN')
        return super(HeaderDiFat, self).alloc(**fields)

### Directory types
class DirectoryEntryData(ptype.block):
    def properties(self):
        parent, res = self.parent, super(DirectoryEntryData, self).properties()
        if isinstance(parent, DirectoryEntry):
            res['index'] = int(parent.__name__)
            res['type'] = parent['Type'].str()
        return res

class DirectoryEntryRootData(parray.type):
    '''MiniStream'''
    def _object_(self):
        raise NotImplementedError

class DirectoryEntryType(pint.enum, BYTE):
    _values_=[('Unknown', 0), ('Storage', 1), ('Stream', 2), ('Root', 5)]
class DirectoryEntryFlag(pint.enum, BYTE):
    _values_=[('red', 0), ('black', 1)]
class DirectoryEntryIdentifier(pint.enum, DWORD):
    _values_=[('MAXREGSID', 0xfffffffa), ('NOSTREAM', 0xffffffff)]

class DirectoryEntry(pstruct.type):
    def __clsid(self):
        try:
            parent = self.getparent(File)
        except ptypes.error.ItemNotFoundError:
            return CLSID

        header = parent['Header']
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

    def alloc(self, **fields):
        res = super(DirectoryEntry, self).alloc(**fields)
        res if 'uName' in fields else res.set(uName=pstr.szwstring().set(res['Name'].str()).size())
        res if 'sectLocation' in fields else res.set(sectLocation=0 if res['Type']['Unknown'] else 'ENDOFCHAIN')
        res if 'qwSize' in fields else res.set(qwSize=0)
        res if 'iChild' in fields else res.set(iChild='NOSTREAM')
        res if 'iLeftSibling' in fields else res.set(iLeftSibling='NOSTREAM')
        res if 'iRightSibling' in fields else res.set(iRightSibling='NOSTREAM')
        return res

    def summary(self):
        sectLocation = self['sectLocation'].object
        return "Name:{!r} {:s} SECT:{:s} SIZE:{:x} CLSID:{:s}".format(self.Name(), self['Type'], "{:#s}".format(sectLocation) if sectLocation.has(sectLocation.int()) else "{:X}".format(sectLocation.int()), self['qwSize'].int(), self['clsid'])

    def Name(self):
        '''Return the name of the directory entry as a string.'''
        res = (1 + self['uName'].int()) // 2
        return u''.join(item.str() for item in self['Name'][0 : res]).rstrip(u'\0')

    def Id(self):
        '''Return the CLSID for the contents referenced by the directory entry.'''
        return self['clsid']

    def Size(self):
        '''Return the size of the contents for the directory entry.'''
        res = self['qwSize']
        return res.int()

    def Data(self, *type, **clamp):
        """Return the contents of the directory entry as the given type or DirectoryEntryData.
        If no type is given, the DirectoryStream definition will be used with the name of the directory entry.
        If clamp is not specified or true, then the type being returned will be sized according to the directory entry.
        If clamp is not true, then the type being returned will be sized according to the number of sectors it occupies.
        Any other keywords will be applied as attributes to the returned instance if a type was specified.
        """
        F = self.getparent(File)

        # Check if we've been asked to clamp the directory entry data or not.
        iterable = (clamp.pop(kwarg) for kwarg in ['clamp', 'clamped'] if kwarg in clamp)
        is_clamped = next(iterable, True)

        # If the entry is a root type, then the data uses the fat and represents the mini-sector data.
        if self['Type']['Root']:
            parent, stream, size = self.getparent(File), F.Stream(self['sectLocation'].int()), self['qwSize'].int()
            source = ptypes.provider.proxy(stream, autocommit={})

            # Figure out the correct type to use for the MiniStream.
            count, unaligned = divmod(size, self._uMiniSectorSize)
            Fobject = lambda self, sector=parent.MiniSector, last=dyn.block(unaligned): sector if len(self.value) < count else last
            clamped_t = dyn.clone(DirectoryEntryRootData, length=count + 1 if unaligned else count, _object_=Fobject)
            backing_t = dyn.clone(DirectoryEntryRootData, length=count + 1 if unaligned else count, _object_=parent.MiniSector)

            # Figure out if we need it to be casted to a type of some sort.
            [datatype] = type if len(type) else [None]
            backing = self.new(clamped_t if is_clamped else backing_t, source=source)
            result = backing if datatype is None else self.new(datatype, source=ptypes.provider.proxy(backing.l, autocommit={}), **clamp)

        # Determine whether the data is stored in the minifat or the regular fat, and
        # then use it to fetch the data using the correct reference.
        else:
            fstream = F.MiniStream if self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int() else F.Stream
            data = fstream(self['sectLocation'].int())

            # Assign all of the pieces that we'll use to return what the user wanted.
            source = ptypes.provider.proxy(data, autocommit={})
            clamped = self.new(DirectoryEntryData, length=self['qwSize'].int(), source=source)
            backing = self.new(DirectoryEntryData, length=data.size(), source=source)

            # Figure out the correct datatype to use depending on the parameter
            # or by searching the DirectoryStream definitions with the stream name.
            streamname = self['Name'].str()
            [datatype] = type if len(type) else [DirectoryStream.lookup(streamname, None)]

            # Load the correct child type from whatever was requested.
            if is_clamped:
                res = clamped if datatype is None else self.new(datatype, source=ptypes.provider.proxy(clamped.l, autocommit={}), **clamp)
            else:
                res = backing if datatype is None else self.new(datatype, source=source, **clamp)
            result = res

        # Ignore any exceptions if we received any and just return what we got.
        try:
            result.li if result.value is None else result
        except Exception as E:
            cls, exception = self.__class__, E.__class__
            logger.warning("{:s}.Data: Ignoring {:s} that was raised during load: {}".format('.'.join([cls.__module__, cls.__name__]), '.'.join([exception.__module__, exception.__name__]), result), exc_info=True)
        return result

    def items(self):
        '''Return the index and item of each directory entry below the current one.'''
        parent = self.getparent(Directory)
        for index, entry in parent.items(self):
            yield index, entry
        return

    def children(self):
        '''Return each element belonging to the current directory entry (Root or Storage).'''
        parent = self.getparent(Directory)
        for _, item in parent.children(self):
            yield item
        return

    def stores(self):
        '''Return all of the stores that belong to the current directory entry (Root or Storage).'''
        parent = self.getparent(Directory)
        for _, item in parent.stores(self):
            yield item
        return

    def chain(self):
        '''Return the chain of sectors or minisectors containing the contents of the directory entry.'''
        F = self.getparent(File)

        # If the entry is a root type, then it will always be in the fat.
        if self['Type']['Root']:
            return F.chain(self['sectLocation'].int())

        # If the size of the entry is smaller than the minisector cutoff, then use the minifat.
        elif self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int():
            return F.minichain(self['sectLocation'].int())

        # Otherwise it's in the fat like most things and we just need to return it.
        return F.chain(self['sectLocation'].int())

    def streamQ(self):
        '''Return true if the directory entry is stored by the fat as a regular stream backed by regular sectors.'''
        F = self.getparent(File)
        return self['qwSize'].int() >= F['MiniFat']['ulMiniSectorCutoff'].int() or self['Type']['Root']

    def ministreamQ(self):
        '''Return true if the directory entry is stored by the minifat as a stream backed by minisectors.'''
        F = self.getparent(File)
        return self['qwSize'].int() < F['MiniFat']['ulMiniSectorCutoff'].int() and not self['Type']['Root']

    def valid(self):
        '''Validate the DirectoryEntry by checking that some of its fields are within bounds.'''
        integer_checks = []
        integer_checks.append((operator.itemgetter('Type'), functools.partial(operator.contains, {0, 1, 2, 5})))
        integer_checks.append((operator.itemgetter('Flag'), functools.partial(operator.contains, {0, 1})))
        integer_checks.append((operator.itemgetter('uName'), functools.partial(operator.contains, {size for size in range(self['Name'].size())})))
        integer_checks.append((operator.itemgetter('sectLocation'), lambda integer: integer <= MAXREGSECT.type))
        return functools.reduce(lambda ok, field_check: (lambda Fgetitem, Fcheck: ok and Fcheck(Fgetitem(self).int()))(*field_check), integer_checks, True)

    def used(self):
        '''Return whether the DirectoryEntry is valid and actually being used.'''
        integer_checks = []
        integer_checks.append((operator.itemgetter('Type'), functools.partial(operator.contains, {1, 2, 5})))
        integer_checks.append((operator.itemgetter('Flag'), functools.partial(operator.contains, {0, 1})))
        integer_checks.append((operator.itemgetter('uName'), functools.partial(operator.contains, {size for size in range(1, self['Name'].size())})))
        integer_checks.append((operator.itemgetter('sectLocation'), lambda integer: integer <= MAXREGSECT.type))
        return functools.reduce(lambda ok, field_check: (lambda Fgetitem, Fcheck: ok and Fcheck(Fgetitem(self).int()))(*field_check), integer_checks, True)

    def __sector_space(self):
        '''Private method that returns a tuple of the sector size and number of sectors that the directory entry occupies.'''
        F = self.getparent(File)
        fat = F.Fat() if F['MiniFat']['ulMiniSectorCutoff'].int() < self['qwSize'].int() or self['Type']['Root'] else F.MiniFat()
        size = self._uSectorSize if F['MiniFat']['ulMiniSectorCutoff'].int() < self['qwSize'].int() or self['Type']['Root'] else self._uMiniSectorSize
        sector = self['sectLocation'].int()
        count, iterable = fat.count(sector), fat.chain(sector)
        sectors = [index for _, index in zip(range(count), iterable)]
        if not sectors:
            return size, count

        index = sectors[-1]
        if not fat[index].object['ENDOFCHAIN']:
            cls = self.__class__
            logger.warning("{:s}.space({:s}): {:s} chain ({:d} sectors) at {:s} {:d} will cycle when at sector {:d} ({:s}).".format('.'.join([cls.__module__, cls.__name__]), self.instance(), fat.classname(), count, 'mini-sector' if isinstance(fat, MINIFAT) else 'sector', sector, fat[index].int(), ', '.join(map("{:d}".format, sectors))))
        return size, count

    def count(self):
        '''Return the number of sectors that are occupied by the current directory entry.'''
        _, count = self.__sector_space()
        return count

    def space(self):
        '''Return the maximum number of bytes that are occupied by the current directory entry.'''
        size, count = self.__sector_space()
        return size * count

class Directory(parray.block):
    _object_ = DirectoryEntry

    def blocksize(self):
        return self._uSectorSize

    def alloc(self, *fields, **attrs):
        if fields:
            return super(Directory, self).alloc(*fields, **attrs)

        initialized = super(Directory, self).alloc(**attrs)
        return super(Directory, self).alloc([item.a for item in initialized], **attrs)

    def details(self):
        Fescape = (lambda self: "{!r}".format(self)[+1 : -1]) if isinstance(u'', str) else (lambda self: eval("{!r}".format(self).replace('\\', '\\\\')))

        maxoffsetlength = max(len("[{:x}]".format(item.getoffset())) for item in self) if len(self) else 0
        maxindexlength = len("{:d}".format(len(self)))
        maxnamelength = max(len(Fescape(item.Name())) for item in self) if len(self) else 0
        maxtypelength = max(len("{:s}".format(item['Type'])) for item in self) if len(self) else 0
        maxstartlength = max(len("{:X}".format(item['sectLocation'].int())) for item in self) if len(self) else 0
        sectorlengths = [len("{:#s}".format(item['sectLocation'].object)) for item in self if item['sectLocation'].object.has(item['sectLocation'].int())]
        maxlocationlength = max(sectorlengths) if sectorlengths else 0
        maxstartlength = max(maxlocationlength, maxstartlength)
        maxsizelength = max(len("{:x}".format(item['qwSize'].int())) for item in self) if len(self) else 0

        rows = []
        for i, item in enumerate(self):
            offset = "[{:x}]".format(item.getoffset())
            sectorLocation = item['sectLocation'].object
            sectorDescription = "{:#s}".format(sectorLocation) if sectorLocation.has(sectorLocation.int()) else "{:X}".format(sectorLocation.int())
            rows.append("{:<{offsetwidth}s} {:s}{:<{:d}s} {!s:>{filenamewidth}} {:<{typewidth}s} SECT:{:<{startwidth}s} SIZE:{:<{sizewidth}x} CLSID:{:s}".format(offset, item.classname(), "[{:d}]".format(i), 2 + maxindexlength, Fescape(item.Name()), "{:s}".format(item['Type']), sectorDescription, item['qwSize'].int(), item['clsid'], offsetwidth=maxoffsetlength, filenamewidth=maxnamelength, typewidth=maxtypelength, startwidth=maxstartlength, sizewidth=maxsizelength))
        return '\n'.join(rows)

    def __byname_directory(self, name):
        '''Return the index and entry of the first DirectoryEntry within the directory that is using the specified name.'''
        for index, item in enumerate(self):
            available = {item.Name(), item['Name'].str()}
            if name in available:
                return index, item
            continue
        raise KeyError("{:s}.byname({!r}): Unable to find directory entry matching the specified name.".format(self.classname(), name))

    def __byname_tree(self, store, name):
        '''Return the index and entry of the first DirectoryEntry belonging to the tree identified by store that is using the given name.'''
        store = store or self.RootEntry()
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        iterable = self.children(self[istore]) if 0 <= istore < len(self) else []
        for index, item in iterable:
            available = {item.Name(), item['Name'].str()}
            if name in available:
                return index, item
            continue
        raise KeyError("{:s}.byname({:d}, {!r}): Unable to find directory entry matching the specified name.".format(self.classname(), istore, name))

    def byname(self, *name):
        '''Return the first DirectoryEntry that is using the specified name.'''
        Fget_entry_by_name = self.__byname_tree if len(name) == 2 else self.__byname_directory
        _, entry = Fget_entry_by_name(*name)
        return entry

    def __bytype_directory(self, directoryentrytype):
        '''Return the index and entry of the first DirectoryEntry within the directory that is using the specified type.'''
        for index, item in enumerate(self):
            if item['Type'][directoryentrytype]:
                return index, item
            continue
        raise KeyError("{:s}.bytype({!r}): Unable to find directory entry matching the specified type.".format(self.classname(), directoryentrytype))

    def __bytype_tree(self, store, directoryentrytype):
        '''Return the index and entry of the first DirectoryEntry belonging to the tree identified by store that is using the given type.'''
        store = store or self.RootEntry()
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        iterable = self.children(self[istore]) if 0 <= istore < len(self) else []
        for index, item in iterable:
            if item['Type'][directoryentrytype]:
                return index, item
            continue
        raise KeyError("{:s}.bytype({:d}, {!r}): Unable to find directory entry matching the specified type.".format(self.classname(), istore, directoryentrytype))

    def bytype(self, *directoryentrytype):
        '''Return the first DirectoryEntry that is using the specified type.'''
        Fget_entry_by_type = self.__bytype_tree if len(directoryentrytype) == 2 else self.__bytype_directory
        _, entry = Fget_entry_by_type(*directoryentrytype)
        return entry

    def __hasname_directory(self, name):
        '''Return whether the given name is used by any entry within the directory.'''
        iterable = ((index, item) for index, item in enumerate(self))
        return any(name in {item.Name(), item['Name'].str()} for _, item in iterable)

    def __hasname_tree(self, store, name):
        '''Return whether the given name is used by any entry within the tree specified by store.'''
        [store, name] = [store if store else self.RootEntry(), name]
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        iterable = self.children(self[istore]) if 0 <= istore < len(self) else []
        return any(name in {item.Name(), item['Name'].str()} for _, item in iterable)

    def hasname(self, *store_and_name):
        '''Return whether a DirectoryEntry with the specified name exists within the directory or underneath the specified store.'''
        Fhas_entry_with_name = self.__hasname_tree if len(store_and_name) == 2 else self.__hasname_directory
        return Fhas_entry_with_name(*store_and_name)

    def repr(self):
        return self.details()

    def RootEntry(self):
        type = 'Root'
        iterable = (entry for entry in self if entry['Type'][type])
        result = next(iterable, None)

        # if we couldn't find a root entry, then do a quick sanity check over the directory to raise an exception.
        if result is None:
            count, invalid = len(self), [index for index, entry in enumerate(self) if not entry.used()]
            descriptions = [string for string in itertools.chain(map("{:d}".format, invalid[:-1]), map("and {:d}".format, invalid[-1:]))] if len(invalid) > 1 else ["{:d}".format(*invalid)] if invalid else []
            complaints = ', '.join(descriptions) if len(descriptions) > 2 else ' '.join(descriptions)
            raise KeyError("{:s}.RootEntry(): Unable to find a \"{:s}\" directory entry within the {:d} entr{:s}{:s} that are available.".format(self.classname(), type, count, 'y' if count == 1 else 'ies', " (entr{:s} {:s} possibly corrupted)".format('y' if len(descriptions) == 1 else 'ies', complaints) if descriptions else ''))
        return result
    root = property(fget=RootEntry)

    def stores(self, storage=None):
        '''Return the index and entry of each store in the directory (Storage).'''
        storage = self.RootEntry() if storage is None else storage
        iterable = [] if storage['iChild']['NOSTREAM'] else self.items(storage['iChild'].int())
        for index, entry in iterable:
            if entry['Type']['Storage']:
                yield index, entry
            continue
        return

    def enumerate(self, storage=None):
        '''Return the index and entry of each item from the directory in their sorted order.'''
        storage = self.RootEntry() if storage is None else storage
        for index, entry in self.children(storage):
            yield index, entry
        return

    def iterate(self, storage=None):
        '''Return the each entry from the directory in their sorted order.'''
        storage = self.RootEntry() if storage is None else storage
        for _, entry in self.children(storage):
            yield entry
        return

    def children(self, index):
        '''Return the index and entry of each element belonging to the directory at the specified index.'''
        node = index if isinstance(index, DirectoryEntry) else self[index]
        iChild = node['iChild']
        if iChild['NOSTREAM']:
            return
        for index, node in self.items(iChild.int()):
            yield index, node
        return

    def items(self, index):
        '''Return the index and entry of each element below the directory entry at the specified index.'''
        if not isinstance(index, DirectoryEntry):
            [(_, node)] = stack = [(index, self[index])]
        else:
            [(index, node)] = stack = [(self.value.index(index), index)]

        while not node['iLeftSibling']['NOSTREAM']:
            iLeft = node['iLeftSibling'].int()
            node = self[iLeft]
            stack.append((iLeft, node))

        for index, node in stack[::-1]:
            yield index, node
            if node['iRightSibling']['NOSTREAM']:
                continue
            iRight = node['iRightSibling'].int()
            for index, node in self.items(iRight):
                yield index, node
            continue
        return

    def minimum(self, index):
        '''Return the index of the first directory entry within the branch at the specified index.'''
        index, node = (self.value.index(index), index) if isinstance(index, DirectoryEntry) else (index, self[index])
        while not node['iLeftSibling']['NOSTREAM']:
            index = node['iLeftSibling'].int()
            node = self[index]
        return index

    def maximum(self, index):
        '''Return the index of the last directory entry within the branch at the specified index.'''
        index, node = (self.value.index(index), index) if isinstance(index, DirectoryEntry) else (index, self[index])
        while not node['iRightSibling']['NOSTREAM']:
            index = node['iRightSibling'].int()
            node = self[index]
        return index

    def entries(self, bytes):
        '''Return the number of directory entries that can fit inside the specified number of bytes.'''
        res = self.new(self._object_).a
        size = res.size()
        count, extra = divmod(bytes, size) if size else 0
        return 1 + count if extra else count

    def __well_shaped__(self):
        '''Return whether the tree starting at the given storage node is actually in the shape of a tree.'''
        check, roots = {}, {}
        for index, entry in enumerate(self):
            iterable = (entry[side] for side in ['iLeftSibling', 'iRightSibling'])
            filtered = (sibling for sibling in iterable if not(sibling['NOSTREAM']))
            [check.setdefault(item.int(), []).append(index) for item in filtered]
            roots.setdefault(entry['iChild'].int(), []).append(index) if not(entry['iChild']['NOSTREAM']) else roots
        terrible_parents = [(index, check[index]) for index in sorted(check) if len(check[index]) > 1]
        for index, parents in terrible_parents:
            iterable = itertools.chain(map("{:d}".format, parents[:-1]), map("and {:d}".format, parents[-1:])) if len(parents) > 2 else [' and '.join(map("{:d}".format, parents))]
            logger.warning("{:s}: Directory Entry {:s} at index {:d} is referenced more than once by entr{:s}.".format('.'.join([self.__class__.__module__, self.__class__.__name__]), self[index].instance(), index, "y {:s}".format(', '.join(iterable)) if len(parents) == 1 else "ies {:s}".format(', '.join(iterable))))
        return all(len(parents) <= 1 and all(iparent in check for iparent in parents if iparent not in roots) for index, parents in check.items())

    def __parents__(self):
        '''Return a dictionary that can be used to determine the index of the parent for each directory entry.'''
        result = {}
        for index, entry in enumerate(self):
            iterable = (entry[side] for side in ['iLeftSibling', 'iRightSibling'])
            filtered = [sibling for sibling in iterable if not(sibling['NOSTREAM'])]
            assert(all(item.int() not in result) for item in filtered)
            [result.setdefault(item.int(), index) for item in filtered]
        return result

    def __rotate_left__(self, store, index):
        '''Rotate the directory tree around the entry at the specified index.'''
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        ientry, entry = (self.value.index(index), index) if isinstance(index, DirectoryEntry) else (index, self[index])
        parents = self.__parents__()

        right, iright = self[ientry]['iRightSibling'], self[ientry]['iRightSibling'].int()
        iterable = (side for side in ['iLeftSibling', 'iRightSibling'] if self[parents[ientry]][side].int() == ientry)
        iparent, [parentside] = (parents[ientry], iterable) if ientry in parents else (parents.get(ientry, -1), [None])

        if not right['NOSTREAM']:
            self[ientry]['iRightSibling'].set(self[iright]['iLeftSibling'].int())
            self[iright]['iLeftSibling'].set(ientry)
        else:
            return self[ientry]

        if ientry in parents:
            self[iparent][parentside].set(iright)
            return self[iright]

        assert(self[istore]['iChild'].int() == ientry)
        self[istore]['iChild'].set(iright)
        return self[iright]

    def __rotate_right__(self, store, index):
        '''Rotate the directory tree around the entry at the specified index.'''
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        ientry, entry = (self.value.index(index), index) if isinstance(index, DirectoryEntry) else (index, self[index])
        parents = self.__parents__()

        left, ileft = self[ientry]['iLeftSibling'], self[ientry]['iLeftSibling'].int()
        iterable = (side for side in ['iLeftSibling', 'iRightSibling'] if self[parents[ientry]][side].int() == ientry)
        iparent, [parentside] = (parents[ientry], iterable) if ientry in parents else (parents.get(ientry, -1), [None])

        if not left['NOSTREAM']:
            self[ientry]['iLeftSibling'].set(self[ileft]['iRightSibling'].int())
            self[ileft]['iRightSibling'].set(ientry)
        else:
            return self[ientry]

        if ientry in parents:
            self[iparent][parentside].set(ileft)
            return self[ileft]

        assert(self[istore]['iChild'].int() == ientry)
        self[istore]['iChild'].set(ileft)
        return self[ileft]

    def disconnect(self, store, index):
        '''Disconnect a directory entry from the specified tree and return it.'''
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        ientry = self.value.index(index) if isinstance(index, DirectoryEntry) else index

        # use the store parameter to figure out the root node.
        assert(not(self[istore]['iChild']['NOSTREAM']))
        iroot = self[istore]['iChild'].int()

        # grab our lookup table for identifying the parent of a directory entry.
        assert(self.__well_shaped__())
        parents = self.__parents__()

        # this is a leaf node and we only need to remove it from the parent.
        if all(self[ientry][side]['NOSTREAM'] for side in ['iLeftSibling', 'iRightSibling']):
            iparent = parents.get(ientry, iroot)
            if ientry not in parents:
                assert(self[istore]['iChild'].int() == ientry), "{:s}: Entry {:s} at specified index ({:d}) is not a child of {:s} at index {:d}.".format('.'.join([self.__class__.__module__, self.__class__.__name__]), self[ientry].instance(), ientry, self[istore].instance(), istore)
                self[iparent]['iChild'].set('NOSTREAM')

            elif iparent != iroot:
                [self[iparent][side].set('NOSTREAM') for side in ['iLeftSibling', 'iRightSibling'] if self[iparent][side].int() == ientry]
            assert(any(self[iparent][side]['NOSTREAM'] for side in ['iLeftSibling', 'iRightSibling']))

        # if one of our sides are empty, then the other side gets attached to the parent.
        elif any(self[ientry][side]['NOSTREAM'] for side in ['iLeftSibling', 'iRightSibling']):
            [side] = (side for side in ['iLeftSibling', 'iRightSibling'] if not self[ientry][side]['NOSTREAM'])
            ibranch = self[ientry][side].int()

            # if we're changing the root node, then we update our reference to it.
            if ientry == iroot:
                store['iChild'].set(ibranch)

            # otherwise figure out which side is being removed from our parent, and attach to it.
            else:
                [parentside] = (side for side in ['iLeftSibling', 'iRightSibling'] if self[parents[ientry]][side].int() == ientry)
                self[parents[ientry]][parentside].set(ibranch)

            # parent was updated, so verify things and then detach our branches here.
            assert(self[istore]['iChild'].int() == ibranch if iroot == ientry else self[parents[ientry]]['iLeftSibling'].int() == ibranch if self[ientry]['iRightSibling']['NOSTREAM'] else self[parents[ientry]]['iLeftSibling'].int() == ibranch)
            [self[ientry][side].set('NOSTREAM') for side in ['iLeftSibling', 'iRightSibling']]

        # if we're not a leaf node, then we'll have to do some reparenting. first
        # we'll grab both of the branches that are related to our in-order successor.
        else:
            isuccessor = self.minimum(self[ientry]['iRightSibling'].int())
            isuccessorbranch = self[isuccessor]['iRightSibling'].int()

            # attach our removed entry's branch to our successor's branch.
            if parents[isuccessor] == ientry:
                [side] = (side for side in ['iLeftSibling', 'iRightSibling'] if self[isuccessorbranch][side]['NOSTREAM'])
                self[parents[isuccessorbranch]][side].set(isuccessor)

            elif isuccessor in parents:
                [side] = (side for side in ['iLeftSibling', 'iRightSibling'] if self[parents[isuccessor]][side].int() == isuccessor)
                self[parents[isuccessor]][side].set(isuccessorbranch)
                self[isuccessor]['iRightSibling'].set(self[ientry]['iRightSibling'].int())

            # otherwise our successor branch becomes the root node.
            else:
                assert(isuccessor == self[istore]['iChild'].int())
                self[istore]['iChild'].set(isuccessorbranch)

            # plug the successor in place of the removed entry by attaching our removed entry's left branch to it.
            assert(self[isuccessor]['iLeftSibling']['NOSTREAM'])
            self[isuccessor]['iLeftSibling'].set(self[ientry]['iLeftSibling'].int())

            # if we just removed the root node, then point its parent directly at our successor.
            if ientry == self[istore]['iChild'].int():
                self[istore]['iChild'].set(isuccessor)

            # otherwise, we need to update our removed entry's parent to reference the successor.
            else:
                [parentside] = (side for side in ['iLeftSibling', 'iRightSibling'] if self[parents[ientry]][side].int() == ientry)
                self[parents[ientry]][parentside].set(isuccessor)

            # next we need to recolor everything to maintain our invariants.
            [self[ientry][side].set('NOSTREAM') for side in ['iLeftSibling', 'iRightSibling']]
        return self[ientry]

    def connect_child(self, store, index):
        '''Connect a directory entry at the given index to another directory entry as its child'''
        istore = self.value.index(store) if isinstance(store, DirectoryEntry) else store
        ientry = self.value.index(index) if isinstance(index, DirectoryEntry) else index

        # If the root node isn't actually a root node, then our job
        # is easy and we only need to assign the index to it.
        if self[istore]['iChild']['NOSTREAM']:
            self[istore]['iChild'].set(ientry)
            return self[ientry]

        # Otherwise, we insert ourselves in front of the already attached entry.
        iroot = self[istore]['iChild'].int()
        siblings = ileft, _ = (self[iroot][side].int() for side in ['iLeftSibling', 'iRightSibling'])

        # Update the entry that is being connected so that it can replace the root node.
        self[ientry]['iLeftSibling'].set(ileft), self[ientry]['iRightSibling'].set(iroot)

        # Remove the branch that was attached to the entry and update the root node.
        self[iroot]['iLeftSibling'].set('NOSTREAM'), self[istore]['iChild'].set(ientry)
        return self[ientry]

    def connect_predecessor(self, anchor, index):
        '''Connect a directory entry at the given index to the left branch of a directory entry.'''
        ianchor = self.value.index(anchor) if isinstance(anchor, DirectoryEntry) else anchor
        ientry = self.value.index(index) if isinstance(index, DirectoryEntry) else index

        ibranch = self[ianchor]['iLeftSibling'].int()
        if not self[ianchor]['iLeftSibling']['NOSTREAM']:
            [ileft, iright] = [self[ibranch][side].int() for side in ['iLeftSibling', 'iRightSibling']]
            self[ientry]['iLeftSibling'].set(ibranch), self[ientry]['iRightSibling'].set(iright), self[ibranch]['iRightSibling'].set('NOSTREAM')

        self[ianchor]['iLeftSibling'].set(ientry)
        return self[ientry]

    def connect_successor(self, anchor, index):
        '''Connect a directory entry to the specified tree after the entry at the given index and return it.'''
        ianchor = self.value.index(anchor) if isinstance(anchor, DirectoryEntry) else anchor
        ientry = self.value.index(index) if isinstance(index, DirectoryEntry) else index

        ibranch = self[ianchor]['iRightSibling'].int()
        if not self[ianchor]['iRightSibling']['NOSTREAM']:
            [ileft, iright] = [self[ibranch][side].int() for side in ['iLeftSibling', 'iRightSibling']]
            self[ientry]['iRightSibling'].set(ibranch), self[ientry]['iLeftSibling'].set(iright), self[ibranch]['iLeftSibling'].set('NOSTREAM')

        self[ianchor]['iRightSibling'].set(ientry)
        return self[ientry]

### Sector types
class SectorContent(ptype.block, AllocationTableMixin):
    @classmethod
    def typename(cls):
        return cls.__name__

    def asTable(self, allocationTable, **attrs):
        '''Return the block as an allocation table of the specified type.'''
        assert(issubclass(allocationTable, AllocationTable)), "Given type {:s} does not inherit from {:s}".format(allocationTable.typename(), AllocationTable.typename())
        attrs.setdefault('source', ptypes.provider.proxy(self, autocommit={}))
        if allocationTable in {DIFAT, FAT}:
            attrs['_object_'] = self.__difat_entry__() if allocationTable == DIFAT else self.__fat_entry__()
        elif allocationTable in {MINIFAT}:
            pass    # FIXME
        return self.new(allocationTable, **attrs)
    astable = property(fget=lambda self: self.asTable)

    def asDirectory(self, **attrs):
        '''Return the sector as a list of directory entries.'''
        attrs.setdefault('source', ptypes.provider.proxy(self, autocommit={}))
        attrs.setdefault('blocksize', self.size)

        # If a single directory entry can fit within this block, then
        # we can simply load it using the sector as its contents.
        required, size = DirectoryEntry().a.blocksize(), self.size()
        if required <= size:
            return self.new(Directory, **attrs).li

        # Otherwise, this sector is smaller than a directory entry,
        # and we can't use it as backing for the directory.
        logger.warning("{:s}: Unable to fit a directory entry ({:+#x} byte{:s}) into the {:+#x} byte{:s} sector at {:s}.".format('.'.join([self.__class__.__module__, self.__class__.__name__]), required, '' if required == 1 else 's', size, '' if size == 1 else 's', self.instance()))
        return self.new(parray.type, _object_=DirectoryEntry, length=0, source=attrs['source'])
    asdirectory = property(fget=lambda self: self.asDirectory)

class FileSector(SectorContent):
    '''An individual sector within the file.'''
    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uSectorCount)
        return super(FileSector, self).asTable(allocationTable, **attrs)

    def index(self):
        '''Return the sector index for the current sector.'''
        cls, offset, header, size = self.__class__, self.getoffset(), self._uHeaderSize, self._uSectorSize
        shifted = offset - header
        if offset < header:
            raise ValueError("{:s}: Location of {:s} is referencing the sector containing the file header.".format('.'.join([cls.__module__, cls.__name__]), self.instance()))
        elif shifted % size:
            logger.warning("{:s}: Calculated index ({:d}) might be wrong due to location of {:s} not being aligned to a sector ({:#x}).".format('.'.join([cls.__module__, cls.__name__]), shifted // size, self.instance(), size))
        return shifted // size

class StreamSector(SectorContent):
    '''An individual sector belonging to a stream.'''
    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uSectorCount)
        return super(StreamSector, self).asTable(allocationTable, **attrs)

class MiniSector(SectorContent):
    '''An individual minisector belonging to a ministream.'''
    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uMiniSectorCount)
        return super(MiniSector, self).asTable(allocationTable, **attrs)

# Sector stream types
class ContentStream(parray.type):
    @classmethod
    def typename(cls):
        return cls.__name__

    def asTable(self, allocationTable, **attrs):
        '''Return the array as an allocation table of the specified type.'''
        assert(issubclass(allocationTable, AllocationTable)), "Given type {:s} does not inherit from {:s}".format(allocationTable.typename(), AllocationTable.typename())
        attrs.setdefault('source', ptypes.provider.proxy(self, autocommit={}))
        return self.new(allocationTable, **attrs).li
    astable = property(fget=lambda self: self.asTable)

    def asDirectory(self, **attrs):
        '''Return the array as a list of directory entries.'''
        attrs.setdefault('source', ptypes.provider.proxy(self, autocommit={}))
        attrs.setdefault('blocksize', self.size)
        return self.new(Directory, **attrs).li
    asdirectory = property(fget=lambda self: self.asDirectory)

class FileSectors(parray.block, ContentStream):
    '''An array of sectors within the file.'''
    def _object_(self):
        parent = self.getparent(File)
        return parent.FileSector

    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uSectorCount * len(self))
        return super(FileSectors, self).asTable(allocationTable, **attrs)

class StreamSectors(ContentStream):
    '''An array of sectors belonging to a stream.'''
    _object_ = StreamSector
    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uSectorCount * len(self))
        return super(StreamSectors, self).asTable(allocationTable, **attrs)

class MiniStreamSectors(ContentStream):
    '''An array of minisectors belonging to a ministream.'''
    _object_ = MiniSector
    def asTable(self, allocationTable, **attrs):
        attrs.setdefault('length', self._uMiniSectorCount * len(self))
        return super(MiniStreamSectors, self).asTable(allocationTable, **attrs)

### File type
class File(pstruct.type, AllocationTableMixin):
    attributes = {
        '_uHeaderSize': pow(2, 9),      # _always_ hardcoded to 512
        '_uSectorSize': pow(2, 9),
        '_uMiniSectorSize': pow(2, 6),
    }

    def __reserved(self):
        '''Hook decoding of the "reserved" field in order to keep track of the sector and mini-sector dimensions.'''
        header = self['Header'].li

        # Validate the byte-order
        order = header.ByteOrder()

        # Store the sector size attributes
        info = self['SectorShift'].li
        sectorSize = info.SectorSize()
        if info['uSectorShift'].int():
            self._uSectorSize = self.attributes['_uSectorSize'] = sectorSize
        self._uSectorCount = self.attributes['_uSectorCount'] = sectorSize // Pointer().blocksize()

        # Store the mini-sector size attributes
        miniSectorSize = info.MiniSectorSize()
        if info['uMiniSectorShift'].int():
            self._uMiniSectorSize = self.attributes['_uMiniSectorSize'] = miniSectorSize
        self._uMiniSectorCount = self.attributes['_uMiniSectorCount'] = miniSectorSize // Pointer().blocksize()

        return dyn.clone(ptype.block, length=6)

    def __Data(self):
        if not getattr(self, '_uSectorSize', 0):
            return FileSectors
        if isinstance(self.source, ptypes.provider.bounded):
            return dyn.clone(FileSectors, blocksize=lambda _, cb=max(0, self.source.size() - self._uHeaderSize): cb)
        return FileSectors

    def __Table(self):
        total, size = self._uHeaderSize, sum(self[fld].li.size() for fld in ['Header', 'SectorShift', 'reserved', 'Fat', 'MiniFat', 'DiFat'])

        # Figure out how many pointers can fit into whatever number of bytes are left
        leftover = max(0, total - size) // Pointer().blocksize()
        return dyn.clone(DIFAT, length=leftover, _object_=self.__difat_entry__())

    def __padding(self):
        res, fields = self._uHeaderSize, ['Header', 'SectorShift', 'reserved', 'Fat', 'MiniFat', 'DiFat', 'Table']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        return dyn.block(size) if size else ptype.block

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

    def alloc(self, **fields):
        fields.setdefault('Header', Header)
        fields.setdefault('SectorShift', HeaderSectorShift)
        fields.setdefault('DiFat', HeaderDiFat)
        res = super(File, self).alloc(**fields)

        # Extract the sector shifts used for the sector sizes.
        info = res['SectorShift']

        # Calculate the sector size attributes.
        sectorSize = info.SectorSize()
        if info['uSectorShift'].int():
            res._uSectorSize = res.attributes['_uSectorSize'] = sectorSize
        res._uSectorCount = res.attributes['_uSectorCount'] = sectorSize // Pointer().blocksize()

        # Calculate the mini-sector size attributes.
        miniSectorSize = info.MiniSectorSize()
        if info['uMiniSectorShift'].int():
            res._uMiniSectorSize = res.attributes['_uMiniSectorSize'] = miniSectorSize
        res._uMiniSectorCount = res.attributes['_uMiniSectorCount'] = miniSectorSize // Pointer().blocksize()

        # Initialize the DIFAT table if it wasn't explicitly specified.
        if 'Table' not in fields:
            res['Table'].set([0xffffffff] * len(res['Table']))
        return res

    @property
    @ptypes.utils.memoize(self=lambda self: self._uSectorSize)
    def StreamSector(self):
        class Sector(StreamSector):
            length = self._uSectorSize
        Sector.__name__ = 'StreamSector'
        return Sector

    @property
    @ptypes.utils.memoize(self=lambda self: self._uMiniSectorSize)
    def MiniSector(self):
        class Sector(MiniSector):
            length = self._uMiniSectorSize
        Sector.__name__ = 'MiniSector'
        return Sector

    @property
    @ptypes.utils.memoize(self=lambda self: self._uSectorSize)
    def FileSector(self):
        class Sector(FileSector):
            length = self._uSectorSize
        Sector.__name__ = 'FileSector'
        return Sector

    @ptypes.utils.memoize(self=lambda self: id(self.value))
    def DiFat(self):
        '''Return an array containing the DiFat'''
        count = self['DiFat']['csectDifat'].int()
        table = self['Table']

        ## Grab any other difat sectors (specified in the header) and use them
        ## to make a source. We chop out the last element of each table since
        ## the last item is actually a link to the very next one.
        iterable = itertools.chain([table], [dfsector[:-1] for dfsector in self.__difat_sectors__()])
        items = [item for item in iterable]
        source = ptypes.provider.disorderly(items, autocommit={})

        ## Now we need to figure out the number of entries and then load it.
        length = sum(len(item) for item in items)
        count = len(table) + self._uSectorCount * (len(items) - 1) - (len(items) - 1)
        assert(count == length), "expected {:d} DiFat entries, got {:d} instead".format(count, length)

        ## Attach the source to the DIFAT, load it, and then return.
        return self.new(DIFAT, recurse=self.attributes, length=length, source=source, _object_=self.__difat_entry__()).load()

    @ptypes.utils.memoize(self=lambda self: id(self.value), attrs=lambda attrs:frozenset(map(tuple, attrs.items())))
    def MiniFat(self, **attrs):
        '''Return an array containing the MiniFat'''
        res = self['MiniFat']
        start, count = res['sectMiniFat'].int(), res['csectMiniFat'].int()
        fat = self.Fat()
        iterable = fat.chain(start)
        sectors = [sector for sector in self.fatsectors(iterable)]
        source = ptypes.provider.disorderly(sectors, autocommit={})
        minisectors = [item for item in self.__ministream_sectors__()]
        return self.new(MINIFAT, __minitable__=minisectors, recurse=self.attributes, length=count * self._uSectorCount, source=source).load(**attrs)

    @ptypes.utils.memoize(self=lambda self: id(self.value), attrs=lambda attrs:frozenset(map(tuple, attrs.items())))
    def Fat(self, **attrs):
        '''Return an array containing the FAT'''
        count, difat = self['Fat']['csectFat'].int(), self.DiFat()

        sectors = [sector for _, sector in zip(range(count), difat)]
        dereferenced = (sector.d for sector in sectors)
        loaded = (sector.l for sector in dereferenced)
        length = sum(len(sector) for sector in loaded)

        data, indices = self['Data'], (sector.int() for sector in sectors)
        realsectors = [(data[index] if 0 <= index < len(data) else data.new(self.FileSector, offset=self._uHeaderSize + index * self._uSectorSize).l) for index in indices]
        #source = ptypes.provider.disorderly(dereferenced, autocommit={})
        source = ptypes.provider.disorderly(realsectors, autocommit={})
        return self.new(FAT, recurse=self.attributes, length=length, source=source).load(**attrs)

    def __difat_sectors__(self):
        '''Return a list of the sectors that compose the difat excluding the "Table" included in the header.'''
        items = []

        # If there's nothing specified in the header, then we're essentially done.
        start, count = self['DiFat']['sectDifat'], self['DiFat']['csectDifat'].int()
        if start.int() > MAXREGSECT.type:
            return items

        # Dereference the pointer in the header to grab the first sector,
        # and then yield any entries we can collect up to "count".
        dfsector = start.d.li
        for _, table in zip(range(count), dfsector.collect()):
            items.append(table)
        return items

    def __fat_sectors__(self):
        '''Return a list of the sectors that compose the file allocation table.'''
        count, difat = self['Fat']['csectFat'].int(), self.DiFat()

        # Iterate through the entire difat and collect each table
        result = []
        for _, items in zip(range(count), difat.iterate()):
            result.append(items.d.l)
        return result

    def fatsectors(self, chain):
        '''Yield the contents of each sector specified by the given chain.'''
        fat, available = self.Fat(), self['Data']

        # Iterate through the specifed chain and
        # yield each sector that is available.
        for index in chain:
            if 0 <= index < len(available):
                yield available[index]

            # If the index is not available, then we
            # need to dereference it out of the fat.
            elif 0 <= index < len(fat):
                yield fat[index].d

            # Otherwise we need to create a new sector to yield.
            else:
                yield available.new(self.FileSector, offset=self._uHeaderSize + index * self._uSectorSize)
            continue
        return

    @ptypes.utils.memoize(self=lambda self: id(self.value))
    def __ministream_sectors__(self):
        '''Return the contents of the sectors containing the ministream as a list.'''
        fat, directory = self.Fat(), self.Directory()
        candidates = [entry for entry in directory if entry['Type']['Root']]
        if len(candidates) != 1:
            return []
        [root] = candidates
        start, _ = (root[item].int() for item in ['sectLocation', 'qwSize'])
        return [item.l for item in self.fatsectors(fat.chain(start))] if 0 <= start <= MAXREGSECT.type else []

    def minisectors(self, chain):
        '''Yield the contents of each minisector specified by the given chain.'''
        sectors, shift = self.__ministream_sectors__(), self['SectorShift']['uMiniSectorShift'].int()
        source = ptypes.provider.disorderly(sectors, autocommit={})
        minisectors = self.new(MiniStreamSectors, _object_=self.MiniSector, length=source.size() // pow(2, shift), source=source).l
        return (minisectors[index] for index in chain)

    def directorysectors(self):
        '''Return the contents of each sector containing the Directory as a list.'''
        fat, directory = self.Fat(), self['Fat']['sectDirectory'].int()
        iterable = (sector.li for sector in self.fatsectors(fat.chain(directory)))
        return [sector for sector in iterable]

    def difatchain(self):
        '''Return the fat chain for the DIFAT as a list of sector numbers.'''
        start, count = self['DiFat']['sectDifat'], self['DiFat']['csectDifat'].int()
        if start.int() > MAXREGSECT.type:
            return []

        # snag the last entry of each difat sector. this entry'll be the index
        # of the sector that follows it. the very last entry of this list should
        # be ENDOFCHAIN which ends up getting clamped out using "csectDiFat".
        iterable = (sector[-1] for sector in self.__difat_sectors__())
        result = [item.int() for item in itertools.chain([start], iterable)]
        return result[:count]

    def chain(self, sector):
        '''Return the fat chain starting at the given sector as a list.'''
        fat = self.Fat()
        iterable = fat.chain(sector)

        # Now we can collect the entire chain, but truncate it to avoid an infinite
        # loop. This is done by constraining its length using the length of the fat.
        truncated = [index for _, index in zip(range(len(fat)), iterable)]

        # Verify that the last sector is ENDOFCHAIN and return our result if so.
        entry = fat[truncated[-1]] if truncated else fat.new(fat._object_).a.set('ENDOFCHAIN')
        if entry.object['ENDOFCHAIN']:
            return truncated
        object = entry.object.copy()

        # Warn the user if the last sector is not the ENDOFCHAIN.
        cls, expected = self.__class__, object.set('ENDOFCHAIN')
        logger.warning("{:s}.chain({:d}): The fat chain ({:d} sector{:s}) was truncated due to being terminated by {:s} instead of {:s} as expected.".format('.'.join([cls.__module__, cls.__name__]), sector, len(truncated), '' if len(truncated) == 1 else 's', entry.object, expected))
        return truncated

    def minichain(self, sector):
        '''Return the minifat chain starting at the given sector as a list.'''
        minifat = self.MiniFat()
        iterable = minifat.chain(sector)

        # Similar to the regular fat, we truncate the chain that we're returning
        # using the length of the minifat to avoid an infinite loop.
        truncated = [index for _, index in zip(range(len(minifat)), iterable)]

        # Then we confirm that we retrieved a proper chain terminated with
        # ENDOFCHAIN. If we did, then we can return our result untampered.
        entry = minifat[truncated[-1]] if truncated else minifat.new(minifat._object_).a.set('ENDOFCHAIN')
        if entry.object['ENDOFCHAIN']:
            return truncated
        object = entry.object.copy()

        # Otherwise we log a warning suggesting that we truncated it.
        cls, expected = self.__class__, object.set('ENDOFCHAIN')
        logger.warning("{:s}.minichain({:d}): The minifat chain ({:d} minisector{:s}) was truncated due to being terminated by {:s} instead of {:s} as expected.".format('.'.join([cls.__module__, cls.__name__]), sector, len(truncated), '' if len(truncated) == 1 else 's', entry.object, expected))
        return truncated

    def filesectors(self, start, *stop):
        '''Use the specified index to return a `FileSector` or range of `FileSectors` from the file.'''
        integer_types = tuple(operator.add(index, sys.maxsize).__class__ for index in range(2))
        size = pow(2, self['SectorShift']['uSectorShift'].int())
        location = self._uHeaderSize + size * start
        if not stop:
            return self.new(self.FileSector, offset=location)
        count = operator.sub(*sorted(itertools.chain([start], stop))[::-1])
        return self.new(FileSectors, offset=location, blocksize=lambda cb=count * size: cb)

    def Stream(self, sector):
        '''Return the contents of the stream starting at a specified sector using the fat.'''
        fat = self.Fat()
        iterable = sector if hasattr(sector, '__iter__') else fat.chain(sector)
        type, items = self.StreamSector, [sector for sector in self.fatsectors(iterable)]
        source = ptypes.provider.disorderly(items, autocommit={})
        return self.new(StreamSectors, _object_=type, length=len(items), source=source).l

    def MiniStream(self, sector):
        '''Return the contents of the ministream starting at a specified minisector using the minifat.'''
        minifat = self.MiniFat()
        iterable = sector if hasattr(sector, '__iter__') else minifat.chain(sector)
        type, items = self.MiniSector, [minisector for minisector in self.minisectors(iterable)]
        source = ptypes.provider.disorderly(items, autocommit={})
        return self.new(MiniStreamSectors, _object_=type, length=len(items), source=source).l

    def Directory(self):
        '''Return the array of Directory entries for the file.'''
        items = [sector for sector in self.directorysectors()]
        source, size = ptypes.provider.disorderly(items, autocommit={}), sum(sector.blocksize() for sector in items)
        return self.new(Directory, __name__='Directory', source=source, blocksize=lambda sz=size: sz).l

### Specific stream types
class DirectoryStream(ptype.definition):
    cache = {}

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

@DirectoryStream.define
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
    filename = sys.argv[1]
    try:
        ptypes.setsource(ptypes.prov.file(filename, mode='rw'))
    except ptypes.error.ProviderError as E:
        print("{!s}: Unable to open file in r/w, trying as r/o instead...".format(E))
        ptypes.setsource(ptypes.prov.file(filename, mode='rb'))

    store = storage.File()
    print('>>> Loading File...')
    store = store.l
    print(store['Header'])
    print()

    print('>>> Loading DiFat...')
    print(store['DiFat'])
    difat = store.DiFat()
    print()

    print('>>> Loading Fat...')
    print(store['Fat'])
    fat = store.Fat()
    print()

    print('>>> Loading MiniFat...')
    print(store['MiniFat'])
    minifat = mfat = store.MiniFat()
    print()

    print('>>> Loading Directory...')
    directory = store.Directory()
    print(directory)
