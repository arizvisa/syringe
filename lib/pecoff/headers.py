import ptypes,__base__
from ptypes import pstruct,parray,ptype,dyn,pstr,pint,pbinary
from __base__ import *
import symbols
from warnings import warn

### locating particular parts of the executable
class Header(object): pass

def locateBase(self):
    """Return the base object of the executable. This is used to find the base address."""
    try:
        nth = self.getparent(ptype.boundary)
    except ValueError, msg:
        nth = list(self.walk())[-1]
    return nth

def locateHeader(self):
    """Return the executable sub-header. This will return the executable main header."""
    try:
        nth = self.getparent(Header)
    except ValueError, msg:
        nth = list(self.walk())[-1]
    return nth

## types of relative pointers in the executable
def calculateRelativeAddress(self, address):
    """given a va, returns offset relative to the baseaddress"""
    base = locateBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.filebase):
        pe = locateHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def calculateRelativeOffset(self, offset):
    """return an offset relative to the baseaddress"""
    base = locateBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.file):
        return base + offset

    # memory
    pe = locateHeader(self)
    section = pe['Sections'].getsectionbyoffset(offset)
    o = offset - section['PointerToRawData'].int()
    return base + section['VirtualAddress'].num() + o

def calculateRealAddress(self, address):
    """given an rva, return offset relative to the baseaddress"""
    base = locateBase(self)
    address -= base['Pe']['OptionalHeader']['ImageBase'].int()
    base=base.getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.file):
        pe = locateHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def realaddress(target, **kwds):
    """Returns a pointer to /target/ where value is an rva"""
    kwds.setdefault('__name__', 'realaddress')
    return dyn.opointer(target, calculateRealAddress, **kwds)
def fileoffset(target, **kwds):
    """Returns a pointer to /target/ where value is a fileoffset"""
    kwds.setdefault('__name__', 'fileoffset')
    return dyn.opointer(target, calculateRelativeOffset, **kwds)
def virtualaddress(target, **kwds):
    """Returns a pointer to /target/ where value is a va"""
    kwds.setdefault('__name__', 'virtualaddress')
    return dyn.opointer(target, calculateRelativeAddress, **kwds)

### NeHeader
    class NeHeader(pstruct.type):
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

## <class NeHeader>
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
##</class NeHeader>

### NtHeader
class NtHeader(pstruct.type, Header):
    """PE Executable Header"""
    class FileHeader(pstruct.type):
        """PE Executable File Header"""
        class Characteristics(pbinary.struct):
            _fields_ = [
                (1, 'BYTES_REVERSED_HI'), (1, 'UP_SYSTEM_ONLY'), (1, 'DLL'), (1, 'SYSTEM'),
                (1, 'NET_RUN_FROM_SWAP'), (1, 'REMOVABLE_RUN_FROM_SWAP'), (1, 'DEBUG_STRIPPED'),
                (1, '32BIT_MACHINE'), (1, 'BYTES_REVERSED_LO'), (1, 'reserved_9'),
                (1, 'LARGE_ADDRESS_AWARE'), (1, 'AGGRESSIVE_WS_TRIM'), (1, 'LOCAL_SYMS_STRIPPED'),
                (1, 'LINE_NUMS_STRIPPED'), (1, 'EXECUTABLE_IMAGE'), (1, 'RELOCS_STRIPPED'),
            ]

        class Machine(word, pint.enum):
            _values_ = [
                ('UNKNOWN', 0x0000), ('AM33', 0x01d3), ('AMD64', 0x8664), ('ARM', 0x01c0),
                ('EBC', 0x0ebc), ('I386', 0x014c), ('IA64', 0x0200), ('M32R', 0x9041),
                ('MIPS16', 0x0266), ('MIPSFPU', 0x0366), ('MIPSFPU16', 0x0466), ('POWERPC', 0x01f0),
                ('POWERPCFP', 0x01f1), ('R4000', 0x0166), ('SH3', 0x01a2), ('SH3DSP', 0x01a3),
                ('SH4', 0x01a6), ('SH5', 0x01a8), ('THUMB', 0x01c2), ('WCEMIPSV2', 0x0169),
            ]

## <class FileHeader>
        _fields_ = [
            (Machine, 'Machine'),
            (uint16, 'NumberOfSections'),
            (TimeDateStamp, 'TimeDateStamp'),
            (fileoffset(symbols.SymbolTableAndStringTable), 'PointerToSymbolTable'),
            (uint32, 'NumberOfSymbols'),
            (word, 'SizeOfOptionalHeader'),
            (pbinary.littleendian(Characteristics), 'Characteristics')
        ]
## </class FileHeader>

    class OptionalHeader(pstruct.type):
        """PE Executable Optional Header"""
        class DllCharacteristics(pbinary.struct):
            _fields_ = [
                (1, 'TERMINAL_SERVER_AWARE'), (1, 'reserved_1'), (1, 'WDM_DRIVER'),
                (1, 'reserved_3'), (1, 'NO_BIND'), (1, 'NO_SEH'), (1, 'NO_ISOLATION'),
                (1, 'NX_COMPAT'), (1, 'FORCE_INTEGRITY'), (1, 'DYNAMIC_BASE'), (6, 'reserved_10'),
            ]

        class Subsystem(uint16, pint.enum):
            _values_ = [
                ('UNKNOWN', 0), ('NATIVE', 1), ('WINDOWS_GUI', 2), ('WINDOWS_CUI', 3),
                ('OS2_CUI', 5), ('POSIX_CUI', 7), ('NATIVE_WINDOWS', 8), ('WINDOWS_CE_GUI', 9),
                ('EFI_APPLICATION', 10), ('EFI_BOOT_SERVICE_DRIVER', 11), ('EFI_RUNTIME_DRIVER', 12),
                ('EFI_ROM', 13), ('XBOX', 14),
            ]

## <class OptionalHeader>
        def DataDirectory(self):
            length = self['NumberOfRvaAndSizes'].load().num()
            if length > 0x10:   # XXX
                warn('OptionalHeader.NumberOfRvaAndSizes specified >0x10 entries (0x%x) for the DataDirectory. Assuming the maximum of 0x10'% length)
                length = 0x10
            return dyn.clone(datadirectory.DataDirectory, length=length)

        def __Is64(self):
            if len(self.v) > 0:
                magic = self['Magic']
                return magic.num() == 0x20b if magic.initialized else magic.l.num() == 0x20b
            return False

        _fields_ = [
            ( uint16, 'Magic' ),
            ( uint8, 'MajorLinkerVersion' ),
            ( uint8, 'MinorLinkerVersion' ),
            ( uint32, 'SizeOfCode' ),
            ( uint32, 'SizeOfInitializedData' ),
            ( uint32, 'SizeOfUninitializedData' ),
            ( virtualaddress(ptype.undefined), 'AddressOfEntryPoint' ),
            ( uint32, 'BaseOfCode' ),
            ( lambda s: pint.uint_t if s.__Is64() else uint32, 'BaseOfData' ),

            ( lambda s: uint64 if s.__Is64() else uint32, 'ImageBase' ),
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
            ( Subsystem, 'Subsystem' ),
            ( pbinary.littleendian(DllCharacteristics), 'DllCharacteristics' ),
            ( lambda s: uint64 if s.__Is64() else uint32, 'SizeOfStackReserve' ),
            ( lambda s: uint64 if s.__Is64() else uint32, 'SizeOfStackCommit' ),
            ( lambda s: uint64 if s.__Is64() else uint32, 'SizeOfHeapReserve' ),
            ( lambda s: uint64 if s.__Is64() else uint32, 'SizeOfHeapCommit' ),
            ( uint32, 'LoaderFlags' ),
            ( uint32, 'NumberOfRvaAndSizes' ),
            ( DataDirectory, 'DataDirectory' ),
        ]
## </class OptionalHeader>

    class SectionTableArray(parray.type):
        class SectionTable(pstruct.type):
            """PE Executable Section Table Entry"""
            class IMAGE_SCN(pbinary.struct):
                _fields_ = [
                    (1, 'MEM_WRITE'),               # 0x80000000
                    (1, 'MEM_READ'),                # 0x40000000
                    (1, 'MEM_EXECUTE'),             # 0x20000000
                    (1, 'MEM_SHARED'),              # 0x10000000
                    (1, 'MEM_NOT_PAGED'),           # 0x08000000
                    (1, 'MEM_NOT_CACHED'),          # 0x04000000
                    (1, 'MEM_DISCARDABLE'),         # 0x02000000
                    (1, 'LNK_NRELOC_OVFL'),         # 0x01000000

                #   (1, 'ALIGN_8192BYTES'), # 0x00e00000
                #   (1, 'ALIGN_4096BYTES'), # 0x00d00000
                #   (1, 'ALIGN_2048BYTES'), # 0x00c00000
                #   (1, 'ALIGN_1024BYTES'), # 0x00b00000
                #   (1, 'ALIGN_512BYTES'), # 0x00a00000
                #   (1, 'ALIGN_256BYTES'), # 0x00900000
                #   (1, 'ALIGN_128BYTES'), # 0x00800000
                #   (1, 'ALIGN_64BYTES'), # 0x00700000
                #   (1, 'ALIGN_32BYTES'), # 0x00600000
                #   (1, 'ALIGN_16BYTES'), # 0x00500000
                #   (1, 'ALIGN_8BYTES'), # 0x00400000
                #   (1, 'ALIGN_4BYTES'), # 0x00300000
                #   (1, 'ALIGN_2BYTES'), # 0x00200000
                #   (1, 'ALIGN_1BYTES'), # 0x00100000

                    (4, 'ALIGN'),                   # 0x00?00000
                    (1, 'MEM_PRELOAD'),             # 0x00080000
                    (1, 'MEM_LOCKED'),              # 0x00040000
                #   (1, 'MEM_16BIT'),              # 0x00020000 # ARM
                    (1, 'MEM_PURGEABLE'),           # 0x00020000
                    (1, 'reserved_16'),

                    (1, 'GPREL'),                   # 0x00008000
                    (2, 'reserved_14'),
                    (1, 'LNK_COMDAT'),              # 0x00001000
                    (1, 'LNK_REMOVE'),              # 0x00000800
                    (1, 'reserved_11'),
                    (1, 'LNK_INFO'),                # 0x00000200
                    (1, 'LNK_OTHER'),               # 0x00000100

                    (1, 'CNT_UNINITIALIZED_DATA'),  # 0x00000080
                    (1, 'CNT_INITIALIZED_DATA'),    # 0x00000040
                    (1, 'CNT_CODE'),                # 0x00000020
                    (1, 'reserved_4'),
                    (1, 'TYPE_NO_PAD'),             # 0x00000008
                    (3, 'reserved_0'),
                ]

## <class SectionTable>
            # FIXME: we can store a longer than 8 byte Name if we want to implement code that navigates to the string table
            #      apparently executables don't care though...
            _fields_ = [
                (dyn.clone(pstr.string, length=8), 'Name'),
                (uint32, 'VirtualSize'),
                (virtualaddress(lambda s:dyn.block(s.parent.getloadedsize())), 'VirtualAddress'),
                (uint32, 'SizeOfRawData'),
                (fileoffset(lambda s:dyn.block(s.parent.getreadsize())), 'PointerToRawData'),
                (fileoffset(lambda s:dyn.array(relocations.Relocation, s.parent['NumberOfRelocations'].l.num())), 'PointerToRelocations'),
                (fileoffset(lambda s:dyn.array(linenumbers.LineNumber, s.parent['NumberOfLinenumbers'].l.num())), 'PointerToLinenumbers'),
                (uint16, 'NumberOfRelocations'),
                (uint16, 'NumberOfLinenumbers'),
                (pbinary.bigendian(IMAGE_SCN), 'Characteristics'),
            ]

            def getreadsize(self):
                try:
                    nt = self.getparent(NtHeader)
                    alignment = nt['OptionalHeader']['FileAlignment'].num()

                except ValueError:
                    alignment = 1       # we are an object with perfect alignment

                mask = alignment - 1
                return (self['SizeOfRawData'].num() + mask) & ~mask

            def getloadedsize(self):
                try:
                    nt = self.getparent(NtHeader)
                    alignment = nt['OptionalHeader']['SectionAlignment'].num()

                except ValueError:
                    alignment = 0x1000   # XXX: pagesize

                mask = alignment-1
                vsize,rsize = self['VirtualSize'].num(), (self['SizeOfRawData'].num() + mask) & ~mask
                if vsize > rsize:
                    return vsize
                return rsize

            def containsaddress(self, address):
                start = self['VirtualAddress'].num()
                if (address >= start) and (address < start + self.getloadedsize()):
                    return True
                return False

            def containsoffset(self, offset):
                start = self['PointerToRawData'].num()
                if (offset >= start) and (offset < start + self.getreadsize()):
                    return True
                return False

            def data(self):
                return self['PointerToRawData'].d

            getrelocations = lambda self: self['PointerToRelocations'].d
            getlinenumbers = lambda self: self['NumberOfLinenumbers'].d

            ## offset means section offset
            def getoffsetbyaddress(self, address):
                return address - self['VirtualAddress'].num() + self['PointerToRawData'].num()

            def getaddressbyoffset(self, offset):
                return offset - self['PointerToRawData'].num() + self['VirtualAddress'].num()
## </class SectionTable>

## <class SectionTableArray>
        _object_ = SectionTable

        def getsectionbyaddress(self, address):
            """Identify the `SectionTable` by the va specified in /address/"""
            sections = [n for n in self if n.containsaddress(address)]
            if len(sections) > 1:
                warn('More than one section was returned for address %x'% address)
            if len(sections):
                return sections[0]
            raise KeyError('address %x not in a known section'% (address))

        def getsectionbyoffset(self, offset):
            """Identify the `SectionTable` by the file-offset specified in /offset/"""
            sections = [n for n in self if n.containsoffset(offset)]
            if len(sections) > 1:
                warn('More than one section was returned for offset %x'% address)
            if len(sections):
                return sections[0]
            raise KeyError('offset %x not in a known section'% (offset))

        def getstringbyoffset(self, offset):
            """Fetch the string in the section specified by /offset/"""
            return self.newelement(pstr.szstring, 'string[%x]'% offset, offset + self.getparent(NtHeader).getoffset()).load().serialize()

        def getstringbyaddress(self, address):
            """Fetch the string in the section specified by /address/"""
            return self.getstringbyoffset( self.getoffsetbyaddress(address) )

        def getsectionbyname(self, name):
            """Return the `SectionTable` specified by /name/"""
            sections = [n for n in self if n['Name'].str() == name]
            if len(sections) > 1:
                warn('More than one section was returned for name %s'% name)
            if len(sections):
                return sections[0]
            raise KeyError('section name %s not known'% (name))
## </class SectionTableArray>

## <class NtHeader>
    _fields_ = [
        ( uint32, 'Signature' ),
        ( FileHeader, 'Header' ),
        ( OptionalHeader, 'OptionalHeader' ),
        ( lambda s: dyn.clone(s.SectionTableArray, length=s['Header'].load()['NumberOfSections'].num()), 'Sections' )
    ]
## </class NtHeader>

### Coff Header
class CoffHeader(pstruct.type, Header):
    """Coff Object File Header"""
    _fields_ = [
        ( NtHeader.FileHeader, 'Header' ),
        ( lambda s: dyn.clone(NtHeader.SectionTableArray, length=s['Header'].load()['NumberOfSections'].num()), 'Sections' )
    ]

### extra headers -- http://www.program-transformation.org/Transform/PcExeFormat
class ExtraHeaders(object):
    class General(pstruct.type):
        _fields_ = [
            ( dyn.block(30), 'e_padding'),
            ( uint32, 'e_lfanew'),
        ]
    class PE(pstruct.type):
        _fields_ = [
            ( dyn.array(uint16, 3), 'e_res' ),
            ( uint16, 'e_oemid' ),
            ( uint16, 'e_oeminfo' ),
            ( dyn.array(uint16, 10), 'e_res2' ),
            ( uint32, 'e_lfanew' )
        ]
    class NE(pstruct.type):
        _fields_ = [
            ( uint32, '???'),
            ( uint16, 'behavior bits'),
            ( dyn.block(26), 'additional behavior'),
            ( uint32, 'e_lfanew' ),
        ]
    class Borland(pstruct.type):
        _fields_ = [
            ( uint16, '0100'),
            ( uint8, 'signature'),
            ( uint8, 'version'),
            ( uint16, '???'),
        ]
    class ARJ(pstruct.type):
        _fields_ = [( uint32, 'signature' )] # RJSX
    class LZEXE(pstruct.type):
        _fields_ = [( uint32, 'signature' )] # LZ09/LZ91
    class PKLITE(pstruct.type):
        _fields_ = [
            ( uint8, 'minor'),
            ( uint8, 'major/compression'),
            ( dyn.block(6), 'signature'),
        ]
    class LHARC(pstruct.type):
        _fields_ = [
            ( uint32, 'unused?'),
            ( dyn.block(3), 'branch-to-extraction'),
            ( uint16, '??'),
            ( dyn.block(12), 'signature'),
        ]
    class LHA(pstruct.type):
        _fields_ = [
            ( dyn.block(8), '???'),
            ( dyn.block(10), 'signature'),
        ]
    class CRUNCH(pstruct.type):
        _fields_ = [
            ( uint32, '00020001'),
            ( uint16, '1565'),
        ]
    class BSA(pstruct.type):
        _fields_ = [
            ( uint16, '000f'),
            ( uint8, 'a7'),
        ]
    class LARC(pstruct.type):
        _fields_ = [
            ( uint32, '???'),
            ( dyn.block(11), 'signature'),
        ]

### DosHeader
class DosHeader(pstruct.type):
    class Relocation(pstruct.type):
        _fields_ = [
            ( uint16, 'offset' ),
            ( uint16, 'segment' ),
        ]

    class __extra(dyn.union_t):
        _fields_ = [
            (ExtraHeaders.General, "General"),
            (ExtraHeaders.PE, "PE"),
            (ExtraHeaders.NE, "NE"),
            (ExtraHeaders.LARC, "LARC"),
            (ExtraHeaders.BSA, "BSA"),
            (ExtraHeaders.CRUNCH, "CRUNCH"),
            (ExtraHeaders.LHA, "LHA"),
            (ExtraHeaders.LHARC, "LHARC"),
            (ExtraHeaders.PKLITE, "PKLITE"),
            (ExtraHeaders.LZEXE, "LZEXE"),
            (ExtraHeaders.ARJ, "ARJ"),
            (ExtraHeaders.Borland, "Borland"),
        ]

    def __extra_space(self):
        headersize = self['e_cparhdr'].l.num() * 16
        size = headersize - 0x1e
        return ptype.clone(ptype.block, length=size if size > 0 else 0)

    _fields_ = [
        ( uint16, 'e_magic' ),
        ( uint16, 'e_cblp' ),        # bytes in last page
        ( uint16, 'e_cp' ),          # pages
        ( uint16, 'e_crlc' ),        # relocation count
        ( uint16, 'e_cparhdr' ),     # header size (paragraphs)
        ( uint16, 'e_minalloc' ),    # required paragraphs
        ( uint16, 'e_maxalloc' ),    # requested paragraphs
        ( uint16, 'e_ss' ),
        ( uint16, 'e_sp' ),
        ( uint16, 'e_csum' ),
        ( uint16, 'e_ip' ),
        ( uint16, 'e_cs' ),
        ( lambda s: fileoffset(dyn.array(DosHeader.Relocation,s['e_crlc'].l.num()), __name__='e_lfarlc', type=uint16), 'e_lfarlc' ), # relocation table
        ( uint16, 'e_ovno' ),        # overlay number
        ( ExtraHeaders.General, 'e_misc' ),
        #( lambda s: dyn.clone(s.__extra, root=s.__extra_space()), 'e_misc' ),

        #( dyn.array(uint16, 4), 'e_res' ),
        #( uint16, 'e_oemid' ),
        #( uint16, 'e_oeminfo' ),
        #( dyn.array(uint16, 10), 'e_res2' ),
        #( uint32, 'e_lfanew' )

        #( dyn.clone(uint32, set=lambda s,v,**a: super(uint32,s).set(s.p.p.getoffset('Pe')-s.p.p.getoffset())), 'e_lfanew')
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
