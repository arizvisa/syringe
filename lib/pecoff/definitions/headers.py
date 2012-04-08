import ptypes,__base__
from ptypes import pstruct,parray,ptype,dyn,pstr,pint,pbinary
from __base__ import *
import symbols
from warnings import warn

def findBase(self):
    try:
        nth = self.getparent(BaseHeader)
    except ValueError, msg:
        nth = list(self.walk())[-1]
    return nth

def findHeader(self):
    try:
        nth = self.getparent(Header)
    except ValueError, msg:
        nth = list(self.walk())[-1]
    return nth

def RelativeAddress(self, address):
    '''given a va, returns offset relative to the baseaddress'''
    base = findBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.file):
        pe = findHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def RelativeOffset(self, offset):
    '''return an offset relative to the baseaddress'''
    base = findBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.file):
        return base + offset

    # memory
    pe = findHeader(self)
    section = pe['Sections'].getsectionbyoffset(offset)
    o = offset - section['PointerToRawData'].int()
    return base + int(section['VirtualAddress']) + o

def RealAddress(self, address):
    '''given an rva, return offset relative to the baseaddress'''
    base = findBase(self)
    address -= base['Pe']['OptionalHeader']['ImageBase'].int()
    base=base.getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.file):
        pe = findHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def realaddress(type):
    return dyn.opointer(type, RealAddress)
def fileoffset(type):
    return dyn.opointer(type, RelativeOffset)
def virtualaddress(type):
    return dyn.opointer(type, RelativeAddress)

### DosHeader
class DosHeader(pstruct.type):
    _fields_ = [
        ( uint16, 'e_magic'),
        ( uint16, 'e_cblp'),
        ( uint16, 'e_cp'),
        ( uint16, 'e_crlc'),
        ( uint16, 'e_cparhdr'),
        ( uint16, 'e_minalloc'),
        ( uint16, 'e_maxalloc'),
        ( uint16, 'e_ss'),
        ( uint16, 'e_sp'),
        ( uint16, 'e_csum'),
        ( uint16, 'e_ip'),
        ( uint16, 'e_cs'),
        ( uint16, 'e_lfarlc'),
        ( uint16, 'e_ovno'),
        ( dyn.array(uint16, 4), 'e_res'),
        ( uint16, 'e_oemid'),
        ( uint16, 'e_oeminfo'),
        ( dyn.array(uint16, 10), 'e_res2'),
        ( uint32, 'e_lfanew')
    ]

### NeHeader
if False:   # this hasn't ever really been tested
    class NE_Pointer(pstruct.type):
        _fields_ = [
            ( uint16, 'Index' ),
            ( uint16, 'Offset' )
        ]

    class NE_Version(pstruct.type):
        _fields_ = [
            ( uint8, 'Minor' ),
            ( uint8, 'Major' )
        ]

    class NeHeader(pstruct.type):
        _fields_ = [
            ( uint8, 'LinkVersion' ),
            ( uint8, 'LinkRevision' ),
            ( uint16, 'EntryOffset' ),
            ( uint16, 'EntryLength' ),
            ( uint32, 'CRC' ),
            ( uint8, 'ProgramFlags' ),
            ( uint8, 'ApplicationFlags' ),
            ( uint8, 'AutoDataSegmentIndex' ),
            ( uint16, 'HeapSize' ),
            ( uint16, 'StackSize' ),
            ( NE_Pointer, 'EntryPointer' ),
            ( NE_Pointer, 'StackPointer' ),
            ( uint16, 'SegmentCount' ),
            ( uint16, 'ModuleCount' ),
            ( uint16, 'NRNamesSize' ),
            ( uint16, 'SegmentOffset' ),
            ( uint16, 'ResourceOffset' ),
            ( uint16, 'RNamesOffset' ),
            ( uint16, 'ModuleOffset' ),
            ( uint16, 'ImportOffset' ),
            ( uint32, 'NRNamesOffset' ),
            ( uint16, 'MoveableEntryPointcount' ),
            ( uint16, 'AlignmentSize' ),
            ( uint16, 'ResourceCount' ),
            ( uint8, 'TargetOS' ),
            ( uint8, 'OS2_Flags' ),
            ( uint16, 'ReturnThunksOffset' ),
            ( uint16, 'SegmentThunksOffset' ),
            ( uint16, 'SwapMinimumSize' ),
            ( NE_Version, 'ExpectedVersion' )
        ]

### NtHeader
class FileHeader(pstruct.type):
    class __Characteristics(pbinary.littleendian(pbinary.struct)):
        _fields_ = [
            (1, 'BYTES_REVERSED_HI'),
            (1, 'UP_SYSTEM_ONLY'),
            (1, 'DLL'),
            (1, 'SYSTEM'),
            (1, 'NET_RUN_FROM_SWAP'),
            (1, 'REMOVABLE_RUN_FROM_SWAP'),
            (1, 'DEBUG_STRIPPED'),
            (1, '32BIT_MACHINE'),
            (1, 'BYTES_REVERSED_LO'),
            (1, 'reserved_9'),
            (1, 'LARGE_ADDRESS_AWARE'),
            (1, 'AGGRESSIVE_WS_TRIM'),
            (1, 'LOCAL_SYMS_STRIPPED'),
            (1, 'LINE_NUMS_STRIPPED'),
            (1, 'EXECUTABLE_IMAGE'),
            (1, 'RELOCS_STRIPPED'),
        ]
        
    _fields_ = [
        (word, 'Machine'),
        (uint16, 'NumberOfSections'),
        (TimeDateStamp, 'TimeDateStamp'),
        (dyn.pointer(symbols.SymbolTableAndStringTable), 'PointerToSymbolTable'),
        (uint32, 'NumberOfSymbols'),
        (word, 'SizeOfOptionalHeader'),
        (__Characteristics, 'Characteristics')
    ]

    def getsymbols(self):
        '''fetch the symbol and string table'''
        ofs,length = (int(self['PointerToSymbolTable']), int(self['NumberOfSymbols']))
        res = self.newelement(symbols.SymbolTableAndStringTable, 'Symbols', ofs + self.parent.getoffset() )
        res.length = length
        return res

class OptionalHeader(pstruct.type):
    class __DllCharacteristics(pbinary.littleendian(pbinary.struct)):
        _fields_ = [
            (1, 'TERMINAL_SERVER_AWARE'),
            (1, 'reserved_1'),
            (1, 'WDM_DRIVER'),
            (1, 'reserved_3'),
            (1, 'NO_BIND'),
            (1, 'NO_SEH'),
            (1, 'NO_ISOLATION'),
            (1, 'NX_COMPAT'),
            (1, 'FORCE_INTEGRITY'),
            (1, 'DYNAMIC_BASE'),
            (6, 'reserved_10'),
        ]

    _fields_ = [
        ( uint16, 'Magic' ),
        ( uint8, 'MajorLinkerVersion' ),
        ( uint8, 'MinorLinkerVersion' ),
        ( uint32, 'SizeOfCode' ),
        ( uint32, 'SizeOfInitializedData' ),
        ( uint32, 'SizeOfUninitializedData' ),
        ( uint32, 'AddressOfEntryPoint' ),
        ( uint32, 'BaseOfCode' ),
        ( uint32, 'BaseOfData' ),
        ( uint32, 'ImageBase' ),
        ( uint32, 'SectionAlignment' ),
        ( uint32, 'FileAlignment' ),
        ( uint16, 'MajorOperatingSystemVersion' ),
        ( uint16, 'MinorOperatingSystemVersion' ),
        ( uint16, 'MajorImageVersion' ),
        ( uint16, 'MinorImageVersion' ),
        ( uint16, 'MajorSubsystemVersion' ),
        ( uint16, 'MinorSubsystemVersion' ),
        ( uint32, 'Win32VersionValue' ),
        ( uint32, 'SizeOfImage' ),
        ( uint32, 'SizeOfHeaders' ),
        ( uint32, 'CheckSum' ),
        ( uint16, 'Subsystem' ),
        ( __DllCharacteristics, 'DllCharacteristics' ),
        ( uint32, 'SizeOfStackReserve' ),
        ( uint32, 'SizeOfStackCommit' ),
        ( uint32, 'SizeOfHeapReserve' ),
        ( uint32, 'SizeOfHeapCommit' ),
        ( uint32, 'LoaderFlags' ),
        ( uint32, 'NumberOfRvaAndSizes' ),
        ( lambda s: dyn.clone(datadirectory.DataDirectory, length=int(s['NumberOfRvaAndSizes'].load())), 'DataDirectory' ),
    ]

class IMAGE_SCN(pint.enum, dword):
    _values_ = [
        ('TYPE_NO_PAD', 0x00000008),
        ('CNT_CODE', 0x00000020),
        ('CNT_INITIALIZED_DATA', 0x00000040),
        ('CNT_UNINITIALIZED_DATA', 0x00000080),
        ('LNK_OTHER', 0x00000100),
        ('LNK_INFO', 0x00000200),
        ('LNK_REMOVE', 0x00000800),
        ('LNK_COMDAT', 0x00001000),
        ('GPREL', 0x00008000),
        ('MEM_PURGEABLE', 0x00020000),
        ('MEM_16BIT', 0x00020000),
        ('MEM_LOCKED', 0x00040000),
        ('MEM_PRELOAD', 0x00080000),
        ('ALIGN_1BYTES', 0x00100000),
        ('ALIGN_2BYTES', 0x00200000),
        ('ALIGN_4BYTES', 0x00300000),
        ('ALIGN_8BYTES', 0x00400000),
        ('ALIGN_16BYTES', 0x00500000),
        ('ALIGN_32BYTES', 0x00600000),
        ('ALIGN_64BYTES', 0x00700000),
        ('ALIGN_128BYTES', 0x00800000),
        ('ALIGN_256BYTES', 0x00900000),
        ('ALIGN_512BYTES', 0x00a00000),
        ('ALIGN_1024BYTES', 0x00b00000),
        ('ALIGN_2048BYTES', 0x00c00000),
        ('ALIGN_4096BYTES', 0x00d00000),
        ('ALIGN_8192BYTES', 0x00e00000),
        ('LNK_NRELOC_OVFL', 0x01000000),
        ('MEM_DISCARDABLE', 0x02000000),
        ('MEM_NOT_CACHED', 0x04000000),
        ('MEM_NOT_PAGED', 0x08000000),
        ('MEM_SHARED', 0x10000000),
        ('MEM_EXECUTE', 0x20000000),
        ('MEM_READ', 0x40000000),
        ('MEM_WRITE', 0x80000000),
    ]

class SectionTable(pstruct.type):
    # FIXME: we can store a longer than 8 byte Name if we want to implement code that navigates to the string table
    #      apparently executables don't care though...
    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'Name'),
        (uint32, 'VirtualSize'),
        (uint32, 'VirtualAddress'),
        (uint32, 'SizeOfRawData'),
#        (dyn.opointer(lambda s:dyn.block(s.parent.getreadsize()), RelativeOffset), 'PointerToRawData'),
#        (dyn.opointer(lambda s:dyn.array(relocations.Relocation, int(s.parent['NumberOfRelocations'])), RelativeOffset), 'PointerToRelocations'),
#        (dyn.opointer(lambda s:dyn.array(linenumbers.LineNumber, int(s.parent['NumberOfLinenumbers'])), RelativeOffset), 'PointerToLinenumbers'),
        (fileoffset(lambda s:dyn.block(s.parent.getreadsize())), 'PointerToRawData'),
        (fileoffset(lambda s:dyn.array(relocations.Relocation, int(s.parent['NumberOfRelocations']))), 'PointerToRelocations'),
        (fileoffset(lambda s:dyn.array(linenumbers.LineNumber, int(s.parent['NumberOfLinenumbers']))), 'PointerToLinenumbers'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (IMAGE_SCN, 'Characteristics'),
    ]

    def getreadsize(self):
        try:
            nt = self.getparent(NtHeader)
            alignment = int(nt['OptionalHeader']['FileAlignment'])

        except ValueError:
            alignment = 1       # we are an object with perfect alignment

        mask = alignment - 1
        return (int(self['SizeOfRawData']) + mask) & ~mask

    def getloadedsize(self):
        try:
            nt = self.getparent(NtHeader)
            alignment = int(nt['OptionalHeader']['SectionAlignment'])

        except ValueError:
            alignment = 0x1000   # XXX: pagesize

        mask = alignment-1
        vsize,rsize = int(self['VirtualSize']), (int(self['SizeOfRawData']) + mask) & ~mask
        if vsize > rsize:
            return vsize
        return rsize

    def containsaddress(self, address):
        start = self['VirtualAddress'].int()
        if (address >= start) and (address < start + self.getloadedsize()):
            return True
        return False

    def containsoffset(self, offset):
        start = self['PointerToRawData'].int()
        if (offset >= start) and (offset < start + self.getreadsize()):
            return True
        return False

    if False:
        def __repr__(self):
            name = self['Name'].get()
            kwds = ['VirtualAddress', 'VirtualSize', 'Characteristics']
            fields = ', '.join(['%s:%x'% (k, int(self[k])) for k in kwds])
            return '%s %s {%s}'% (self.__class__, name, fields)

    if False:
        def __repr__(self):
            kwds = ['VirtualAddress', 'VirtualSize', 'Characteristics']
            fields = ', '.join(['%s:%x'% (k, int(self[k])) for k in kwds])
            v = self.getrelocations()
            r = '\n'.join(map(repr, v))
            self.delchild(v)
            if r:
                res += '\n' + r
            return res

            def __repr__(self):
                name = self['Name'].get()
                return ' '.join([name, super(SectionTable, self).__repr__()])

    def get(self):
        '''fetch a block containing the contents of the section'''
        return self['PointerToRawData'].d

    getrelocations = lambda self: self['PointerToRelocations'].d
    getlinenumbers = lambda self: self['NumberOfLinenumbers'].d

    ## offset means section offset
    def getoffsetbyaddress(self, address):
        return address - self['VirtualAddress'].int() + self['PointerToRawData'].int()

    def getaddressbyoffset(self, offset):
        return offset - self['PointerToRawData'].int() + self['VirtualAddress'].int()

class SectionTableArray(parray.type):
    _object_ = SectionTable

    def getsectionbyaddress(self, address):
        sections = [n for n in self if n.containsaddress(address)]
        if len(sections) > 1:
            warn('More than one section was returned for address %x'% address)
        if len(sections):
            return sections[0]
        raise KeyError('address %x not in a known section'% (address))

    ## offset means file offset in the following declarations
    def getsectionbyoffset(self, offset):
        sections = [n for n in self if n.containsoffset(offset)]
        if len(sections) > 1:
            warn('More than one section was returned for offset %x'% address)
        if len(sections):
            return sections[0]
        raise KeyError('offset %x not in a known section'% (offset))

    def getstringbyoffset(self, offset):
        return self.newelement(pstr.szstring, 'string[%x]'% offset, offset + self.getparent(NtHeader).getoffset()).load().serialize()

    def getstringbyaddress(self, address):
        return self.getstringbyoffset( self.getoffsetbyaddress(address) )

    def getsectionbyname(self, name):
        ## it was bound to happen
        sections = [n for n in self if n['Name'].str() == name]
        if len(sections) > 1:
            warn('More than one section was returned for name %s'% name)
        if len(sections):
            return sections[0]
        raise KeyError('section name %s not known'% (name))

class NtHeader(pstruct.type, Header):
    _fields_ = [
        ( uint32, 'Signature' ),
        ( FileHeader, 'Header' ),
        ( OptionalHeader, 'OptionalHeader' ),
        ( lambda s: dyn.clone(SectionTableArray, length=int(s['Header'].load()['NumberOfSections'])), 'Sections' )
    ]

### Coff Header
class CoffHeader(pstruct.type, Header):
    _fields_ = [
        ( FileHeader, 'Header' ),
        ( lambda s: dyn.clone(SectionTableArray, length=int(s['Header'].load()['NumberOfSections'])), 'Sections' )
    ]

### delayed imports
import datadirectory,relocations

if __name__ == '__main__':
    from ptypes import provider
    import headers
    from headers import *
    x = DosHeader()
    x.source = provider.file('./python.exe')
    offset = x.load()['e_lfanew']
    print x

#    x = FileHeader()
#    x.source = provider.file('./python.exe')
#    x.setoffset( int(offset) )
#    print x.load()

    x = NtHeader()
    x.setoffset( int(offset) )
    x.source = provider.file('./python.exe')
    print x.load()
