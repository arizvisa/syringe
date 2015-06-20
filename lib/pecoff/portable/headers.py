import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,pint,pbinary
from ..__base__ import *

from . import symbols

### locating particular parts of the executable
def locateBase(self):
    """Return the base object of the executable. This is used to find the base address."""
    try:
        nth = self.getparent(ptype.boundary)
    except ValueError, msg:
        nth = list(self.backtrace(fn=lambda x:x))[-1]
    return nth

def locateHeader(self):
    """Return the executable sub-header. This will return the executable main header."""
    try:
        nth = self.getparent(Header)
    except ValueError, msg:
        nth = list(self.backtrace(fn=lambda x:x))[-1]
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
    if issubclass(self.source.__class__, ptypes.provider.filebase):
        return base + offset

    # memory
    pe = locateHeader(self)
    section = pe['Sections'].getsectionbyoffset(offset)
    o = offset - section['PointerToRawData'].int()
    return base + section['VirtualAddress'].num() + o

def calculateRealAddress(self, address):
    """given an rva, return offset relative to the baseaddress"""
    base = locateBase(self)
    address -= base['OptionalHeader']['ImageBase'].int()
    base=base.getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.filebase):
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

class DataDirectoryEntry(pstruct.type):
    pass

class SectionTable(pstruct.type):
    """PE Executable Section Table Entry"""
    class IMAGE_SCN(pbinary.flags):
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

    # FIXME: we can store a longer than 8 byte Name if we want to implement code that navigates to the string table
    #      apparently executables don't care though...
    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'Name'),
        (uint32, 'VirtualSize'),
        (virtualaddress(lambda s:dyn.block(s.parent.getloadedsize()), type=uint32), 'VirtualAddress'),
        (uint32, 'SizeOfRawData'),
        (fileoffset(lambda s:dyn.block(s.parent.getreadsize()), type=uint32), 'PointerToRawData'),
        (fileoffset(lambda s:dyn.array(relocations.Relocation, s.parent['NumberOfRelocations'].li.num()), type=uint32), 'PointerToRelocations'),
        (fileoffset(lambda s:dyn.array(linenumbers.LineNumber, s.parent['NumberOfLinenumbers'].li.num()), type=uint32), 'PointerToLinenumbers'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (pbinary.littleendian(IMAGE_SCN), 'Characteristics'),
    ]

    def getreadsize(self):
        nt = self.getparent(SectionTableArray).p
        alignment = nt['OptionalHeader']['FileAlignment'].num()
        mask = alignment - 1
        return (self['SizeOfRawData'].num() + mask) & ~mask

    def getloadedsize(self):
        # XXX: even though the loadedsize is aligned to SectionAlignment,
        #      the loader doesn't actually map data there and thus the
        #      actual mapped size is rounded to pagesize

        # nt = self.getparent(Header)
        # alignment = nt['OptionalHeader']['SectionAlignment'].num()
        alignment = 0x1000  # pagesize
        mask = alignment - 1
        return (self['VirtualSize'].num() + mask) & ~mask

    def containsaddress(self, address):
        start = self['VirtualAddress'].num()
        return True if (address >= start) and (address < start + self.getloadedsize()) else False

    def containsoffset(self, offset):
        start = self['PointerToRawData'].num()
        return True if (offset >= start) and (offset < start + self.getreadsize()) else False

    def data(self):
        return self['PointerToRawData'].d

    getrelocations = lambda self: self['PointerToRelocations'].d
    getlinenumbers = lambda self: self['NumberOfLinenumbers'].d

    ## offset means section offset
    def getoffsetbyaddress(self, address):
        return address - self['VirtualAddress'].num() + self['PointerToRawData'].num()

    def getaddressbyoffset(self, offset):
        return offset - self['PointerToRawData'].num() + self['VirtualAddress'].num()

class SectionTableArray(parray.type):
    _object_ = SectionTable

    def getsectionbyaddress(self, address):
        """Identify the `SectionTable` by the va specified in /address/"""
        sections = [n for n in self if n.containsaddress(address)]
        if len(sections) > 1:
            logging.warn('More than one section was returned for address %x'% address)
        if len(sections):
            return sections[0]
        raise KeyError('Address %x not in a known section'% (address))

    def getsectionbyoffset(self, offset):
        """Identify the `SectionTable` by the file-offset specified in /offset/"""
        sections = [n for n in self if n.containsoffset(offset)]
        if len(sections) > 1:
            logging.warn('More than one section was returned for offset %x'% address)
        if len(sections):
            return sections[0]
        raise KeyError('Offset %x not in a known section'% (offset))

    def getstringbyoffset(self, offset):
        """Fetch the string in the section specified by /offset/"""
        return self.new(pstr.szstring, __name__='string[%x]'% offset, offset=offset + self.getparent(Header).getoffset()).load().serialize()

    def getstringbyaddress(self, address):
        """Fetch the string in the section specified by /address/"""
        section = self.getsectionbyaddress(address)
        return self.getstringbyoffset( section.getoffsetbyaddress(address) )

    def getsectionbyname(self, name):
        """Return the `SectionTable` specified by /name/"""
        sections = [n for n in self if n['Name'].str() == name]
        if len(sections) > 1:
            logging.warn('More than one section was returned for name %s'% name)
        if len(sections):
            return sections[0]
        raise KeyError('section name %s not known'% (name))

    def details(self, **options):
        cnwidth = max(len(n.classname()) for n in self.value)
        namewidth = max(len(n['Name'].str()) for n in self.value)
        vwidth = max(n['VirtualAddress'].size()*2 for n in self.value)+2
        vswidth = max(n['VirtualSize'].size()*2 for n in self.value)+2
        fwidth = max(n['PointerToRawData'].size()*2 for n in self.value)+2
        fswidth = max(n['SizeOfRawData'].size()*2 for n in self.value)+2
        return '\n'.join('[{:x}] {:>{}}{:4s} Name:{:<{}} Raw[{:=#0{}x}:+{:=#0{}x}] Virtual[{:=#0{}x}:+{:=#0{}x}] Characteristics:{:s}'.format(n.getoffset(), n.classname(),cnwidth,'{%d}'%i, n['Name'].str(),namewidth, n['PointerToRawData'].num(),fwidth, n['SizeOfRawData'].num(),fswidth, n['VirtualAddress'].num(),vwidth, n['VirtualSize'].num(),vswidth, n['Characteristics'].summary()) for i,n in enumerate(self.value))

    def repr(self, **options):
        return self.details(**options)

class OptionalHeader(pstruct.type):
    """PE Executable Optional Header"""
    class DllCharacteristics(pbinary.flags):
        # TODO: GUARD_CF
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

    def is64(self):
        '''Returns True if a 64-bit executable'''
        if len(self.v) > 0:
            magic = self['Magic']
            return magic.li.num() == 0x20b
        return False

    _fields_ = [
        ( uint16, 'Magic' ),
        ( uint8, 'MajorLinkerVersion' ),
        ( uint8, 'MinorLinkerVersion' ),
        ( uint32, 'SizeOfCode' ),
        ( uint32, 'SizeOfInitializedData' ),
        ( uint32, 'SizeOfUninitializedData' ),
        ( virtualaddress(ptype.undefined, type=uint32), 'AddressOfEntryPoint' ),
        ( uint32, 'BaseOfCode' ),
        ( lambda s: pint.uint_t if s.is64() else uint32, 'BaseOfData' ),

        ( lambda s: uint64 if s.is64() else uint32, 'ImageBase' ),
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
        ( lambda s: uint64 if s.is64() else uint32, 'SizeOfStackReserve' ),
        ( lambda s: uint64 if s.is64() else uint32, 'SizeOfStackCommit' ),
        ( lambda s: uint64 if s.is64() else uint32, 'SizeOfHeapReserve' ),
        ( lambda s: uint64 if s.is64() else uint32, 'SizeOfHeapCommit' ),
        ( uint32, 'LoaderFlags' ),
        ( uint32, 'NumberOfRvaAndSizes' ),
    ]

class FileHeader(pstruct.type):
    """PE Executable File Header"""
    class Characteristics(pbinary.flags):
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

    _fields_ = [
        (Machine, 'Machine'),
        (uint16, 'NumberOfSections'),
        (TimeDateStamp, 'TimeDateStamp'),
        (fileoffset(symbols.SymbolTableAndStringTable, type=uint32), 'PointerToSymbolTable'),
        (uint32, 'NumberOfSymbols'),
        (word, 'SizeOfOptionalHeader'),
        (pbinary.littleendian(Characteristics), 'Characteristics')
    ]

class Certificate(pstruct.type):
    class wRevision(uint16, pint.enum):
        _values_ = [
            ('WIN_CERT_REVISION_1_0', 0x0100),
            ('WIN_CERT_REVISION_2_0', 0x0200),
        ]
    class wCertificateType(uint16, pint.enum):
        _values_ = [
            ('WIN_CERT_TYPE_X509', 0x0001),
            ('WIN_CERT_TYPE_PKCS7_SIGNED_DATA', 0x0002),
            ('WIN_CERT_TYPE_RESERVED_1', 0x0003),
            ('WIN_CERT_TYPE_TS_STACK_SIGNED', 0x0004),
        ]

    _fields_ = [
        (uint32, 'dwLength'),
        (wRevision, 'wRevision'),
        (wCertificateType, 'wCertificateType'),
        (lambda s: dyn.block(s['dwLength'].li.num() - 8), 'bCertificate'),
    ]

if __name__ == '__main__':
    from ptypes import provider
    import pecoff
    x = pecoff.Executable.Dos()
    x.source = provider.file('./python.exe')
    offset = x.load()['e_lfanew']
    print x

#    x = FileHeader()
#    x.source = provider.file('./python.exe')
#    x.setoffset( int(offset) )
#    print x.load()

    x = pecoff.Executable.Portable()
    x.setoffset( int(offset) )
    x.source = provider.file('./python.exe')
    print x.load()
