import ptypes,ndk
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### Primitive types
class ULONG(pint.uint32_t): pass
class USHORT(pint.uint16_t): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class QWORD(pint.uint64_t): pass

class CLSID(ndk.rfc4122): pass

class FILETIME(pstruct.type):
    _fields_ = [(DWORD,'dwLowDateTime'),(DWORD,'dwHighDateTime')]
TIME_T = FILETIME

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
        return ''.join(Sector.get(n.num()).symbol for n in self)
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
        maxoffsetlength = max(len('[%x]'%x.getoffset()) for x in self)
        maxnamelength = max(len(repr(x['Name'].str())) for x in self)
        for i,x in enumerate(self):
            offset = '[%x]'% x.getoffset()
            res.append('{:<{offsetwidth}s} {:s}[{:d}] {!r:>{filenamewidth}} {:s} SECT:{:x} SIZE:{:x} {:s}'.format(offset, x.classname(), i, x['Name'].str(), x['Type'].summary(), x['sectLocation'].num(), x['qwSize'].num(), x['clsid'].summary(), offsetwidth=maxoffsetlength, filenamewidth=maxnamelength))
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

    @ptypes.utils.memoize(self=lambda s: s.source)
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

    @ptypes.utils.memoize(self=lambda s: s.source)
    def getMiniFat(self):
        '''Return an array containing the MiniFAT'''
        mf = self['MiniFat']
        fat,count = mf['sectMiniFat'],mf['csectMiniFat'].num()
        res = self.new(MINIFAT, recurse=self.attributes, length=self._uSectorCount)
        for table in fat.d.l.collect(count-1):
            map(res.append, (p for p in table))
        return res

    @ptypes.utils.memoize(self=lambda s: s.source)
    def getFat(self):
        '''Return an array containing the FAT'''
        count,difat = self['Fat']['csectFat'].num(),self.getDifat()
        res = self.new(FAT, recurse=self.attributes, Pointer=FAT.Pointer, length=self._uSectorCount)
        for _,v in zip(xrange(count), difat):
            map(res.append, (p for p in v.l.d.l))
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
