import logging,ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,pint,pbinary
from ..headers import *

from . import symbols,relocations,linenumbers

class IMAGE_DATA_DIRECTORY(pstruct.type):
    def _object_(self):
        # called by 'Address'
        res = self['Size'].int()
        return dyn.block(res)

    def containsaddress(self, addr):
        '''if an address is within our boundaries'''
        start = self['Address'].int()
        end = start + self['Size'].int()
        return start <= addr < end

    def valid(self):
        return self['Size'].int() != 0

    def __Address(self):
        t = self._object_
        if ptypes.iscontainer(t):
            return self.addressing(dyn.clone(t, blocksize=lambda self: self.getparent(IMAGE_DATA_DIRECTORY)['Size'].li.int()), type=uint32)
        return self.addressing(t, type=uint32)

    _fields_ = [
        (__Address, 'Address'),
        (uint32, 'Size')
    ]

    def summary(self):
        return 'Address={:#x} Size={:#x}'.format(self['Address'].int(), self['Size'].int())

class IMAGE_SECTION_HEADER(pstruct.type):
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

    def __VirtualAddress(target):
        parent = target.parent
        expected = parent.getloadedsize()
        if expected and not issubclass(parent.source.__class__, ptypes.provider.memorybase):
            corrected = parent.getreadsize()
            logging.debug("{:s} : Choosing the on-disk size ({:+#x}) to decode field \"{:s}\" instead of the in-memory size ({:+#x}) due to the source being file-backed.".format(parent.instance(), corrected, 'VirtualAddress', expected))
            return dyn.block(corrected)
        return dyn.block(expected)

    def __PointerToRawData(target):
        res = target.parent.getreadsize()
        return dyn.block(res)

    # FIXME: we can store a longer than 8 byte Name if we want to implement code that navigates to the string table
    #      apparently executables don't care though...
    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'Name'),
        (uint32, 'VirtualSize'),
        (virtualaddress(__VirtualAddress, type=uint32), 'VirtualAddress'),
        (uint32, 'SizeOfRawData'),
        (fileoffset(__PointerToRawData, type=uint32), 'PointerToRawData'),
        (fileoffset(lambda target: dyn.clone(relocations.RelocationTable, length=target.parent['NumberOfRelocations'].li.int()), type=uint32), 'PointerToRelocations'),
        (fileoffset(lambda target: dyn.clone(linenumbers.LineNumberTable, length=target.parent['NumberOfLinenumbers'].li.int()), type=uint32), 'PointerToLinenumbers'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (pbinary.littleendian(IMAGE_SCN), 'Characteristics'),
    ]

    def getreadsize(self):
        portable = self.getparent(SectionTableArray)

        # if it's a portable executable, then apply the alignment
        try:
            nt = portable.p
            alignment = nt['OptionalHeader']['FileAlignment'].int()

        # otherwise, there's no alignment necessary
        except KeyError:
            alignment = 1

        _, remainder = divmod(self['SizeOfRawData'].int(), alignment) if alignment else (0, 0)
        res = (alignment - remainder) & (alignment - 1)
        return self['SizeOfRawData'].int() + res

    def getloadedsize(self):
        alignment = 0x1000
        _, remainder = divmod(self['VirtualSize'].int(), alignment) if alignment else (0, 0)
        res = (alignment - remainder) & (alignment - 1)
        return self['VirtualSize'].int() + res

    def containsaddress(self, address):
        start = self['VirtualAddress'].int()
        return True if (address >= start) and (address < start + self.getloadedsize()) else False

    def containsoffset(self, offset):
        start = self['PointerToRawData'].int()
        return True if (offset >= start) and (offset < start + self.getreadsize()) else False

    def data(self):
        return self['PointerToRawData'].d

    getrelocations = lambda self: self['PointerToRelocations'].d
    getlinenumbers = lambda self: self['NumberOfLinenumbers'].d

    ## offset means file offset
    def getoffsetbyaddress(self, address):
        return address - self['VirtualAddress'].int() + self['PointerToRawData'].int()

    def getaddressbyoffset(self, offset):
        return offset - self['PointerToRawData'].int() + self['VirtualAddress'].int()

    def summary(self):
        return 'Name:{} Raw[{:#x}:+{:#x}] Virtual[{:#x}:+{:#x}] NumberOfRelocations:{:d} Characteristics:{:s}'.format(self['Name'].str(), self['PointerToRawData'].int(), self['SizeOfRawData'].int(), self['VirtualAddress'].int(), self['VirtualSize'].int(), self['NumberOfRelocations'].int(), self['Characteristics'].summary())
SectionTable = IMAGE_SECTION_HEADER

class SectionTableArray(parray.type):
    _object_ = IMAGE_SECTION_HEADER

    def getsectionbyaddress(self, address):
        """Identify the `IMAGE_SECTION_HEADER` by the va specified in /address/"""
        sections = [n for n in self if n.containsaddress(address)]
        if len(sections) > 1:
            cls = self.__class__
            logging.warning("{:s} : More than one section was returned for address {:x} ({:s})".format('.'.join((cls.__module__, cls.__name__)), address, ', '.join(s['Name'].str() for s in sections)))
        if len(sections):
            return sections[0]
        raise KeyError('Address %x not in a known section'% (address))

    def getsectionbyoffset(self, offset):
        """Identify the `IMAGE_SECTION_HEADER` by the file-offset specified in /offset/"""
        sections = [n for n in self if n.containsoffset(offset)]
        if len(sections) > 1:
            logging.warning("{:s} : More than one section was returned for offset {:x} ({:s})".format('.'.join((cls.__module__, cls.__name__)), address, ', '.join(s['Name'].str() for s in sections)))
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
        """Return the `IMAGE_SECTION_HEADER` specified by /name/"""
        sections = [n for n in self if n['Name'].str() == name]
        if len(sections) > 1:
            logging.warning("{:s} : More than one section was returned for name {!r}".format('.'.join((cls.__module__, cls.__name__)), name))
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
        return '\n'.join('[{:x}] {:>{}}{:4s} Name:{:<{}} Raw[{:=#0{}x}:+{:=#0{}x}] Virtual[{:=#0{}x}:+{:=#0{}x}] Characteristics:{:s}'.format(n.getoffset(), n.classname(),cnwidth,'{%d}'%i, n['Name'].str(),namewidth, n['PointerToRawData'].int(),fwidth, n['SizeOfRawData'].int(),fswidth, n['VirtualAddress'].int(),vwidth, n['VirtualSize'].int(),vswidth, n['Characteristics'].summary()) for i,n in enumerate(self.value))

    def repr(self, **options):
        return self.details(**options)

class IMAGE_NT_OPTIONAL_MAGIC(pint.enum, uint16):
    _values_ = [
        ('HDR32', 0x10b),
        ('HDR64', 0x20b),
        ('HDR_ROM', 0x107),
    ]

class IMAGE_SUBSYSTEM_(pint.enum, uint16):
    _values_ = [
        ('UNKNOWN', 0),
        ('NATIVE', 1),
        ('WINDOWS_GUI', 2),
        ('WINDOWS_CUI', 3),
        ('OS2_CUI', 5),
        ('POSIX_CUI', 7),
        ('NATIVE_WINDOWS', 8),
        ('WINDOWS_CE_GUI', 9),
        ('EFI_APPLICATION', 10),
        ('EFI_BOOT_SERVICE_DRIVER', 11),
        ('EFI_RUNTIME_DRIVER', 12),
        ('EFI_ROM', 13),
        ('XBOX', 14),
        ('WINDOWS_BOOT_APPLICATION', 16)
    ]

class IMAGE_DLLCHARACTERISTICS_(pbinary.flags):
    # TODO: GUARD_CF
    _fields_ = [
        (1, 'TERMINAL_SERVER_AWARE'),
        (1, 'GUARD_CF'),
        (1, 'WDM_DRIVER'),
        (1, 'APPCONTAINER'),
        (1, 'NO_BIND'),
        (1, 'NO_SEH'),
        (1, 'NO_ISOLATION'),
        (1, 'NX_COMPAT'),
        (1, 'FORCE_INTEGRITY'),
        (1, 'DYNAMIC_BASE'),
        (1, 'HIGH_ENTROPY_VA'),
        (5, 'reserved_11'),
    ]

class IMAGE_OPTIONAL_HEADER(pstruct.type):
    """PE Executable Optional Header"""
    def is64(self):
        '''Returns True if a 64-bit executable'''
        if len(self.v) > 0:
            magic = self['Magic']
            return magic.li.int() == 0x20b
        return False

    _fields_ = [
        ( IMAGE_NT_OPTIONAL_MAGIC, 'Magic' ),
        ( uint8, 'MajorLinkerVersion' ),
        ( uint8, 'MinorLinkerVersion' ),
        ( uint32, 'SizeOfCode' ),
        ( uint32, 'SizeOfInitializedData' ),
        ( uint32, 'SizeOfUninitializedData' ),
        ( virtualaddress(ptype.undefined, type=uint32), 'AddressOfEntryPoint' ),
        ( uint32, 'BaseOfCode' ),
        ( lambda self: pint.uint_t if self.is64() else uint32, 'BaseOfData' ),

        ( lambda self: uint64 if self.is64() else uint32, 'ImageBase' ),
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
        ( IMAGE_SUBSYSTEM_, 'Subsystem' ),
        ( pbinary.littleendian(IMAGE_DLLCHARACTERISTICS_), 'DllCharacteristics' ),
        ( lambda self: uint64 if self.is64() else uint32, 'SizeOfStackReserve' ),
        ( lambda self: uint64 if self.is64() else uint32, 'SizeOfStackCommit' ),
        ( lambda self: uint64 if self.is64() else uint32, 'SizeOfHeapReserve' ),
        ( lambda self: uint64 if self.is64() else uint32, 'SizeOfHeapCommit' ),
        ( uint32, 'LoaderFlags' ),
        ( uint32, 'NumberOfRvaAndSizes' ),
    ]
OptionalHeader = IMAGE_OPTIONAL_HEADER64 = IMAGE_OPTIONAL_HEADER

class IMAGE_FILE_HEADER(pstruct.type):
    """PE Executable File Header"""
    _fields_ = [
        (IMAGE_FILE_MACHINE_, 'Machine'),
        (uint16, 'NumberOfSections'),
        (TimeDateStamp, 'TimeDateStamp'),
        (fileoffset(symbols.SymbolTableAndStringTable, type=uint32), 'PointerToSymbolTable'),
        (uint32, 'NumberOfSymbols'),
        (word, 'SizeOfOptionalHeader'),
        (pbinary.littleendian(IMAGE_FILE_), 'Characteristics')
    ]
FileHeader = IMAGE_FILE_HEADER

class Certificate(pstruct.type):
    class wRevision(pint.enum, uint16):
        _values_ = [
            ('WIN_CERT_REVISION_1_0', 0x0100),
            ('WIN_CERT_REVISION_2_0', 0x0200),
        ]

    class wCertificateType(pint.enum, uint16):
        _values_ = [
            ('WIN_CERT_TYPE_X509', 0x0001),
            ('WIN_CERT_TYPE_PKCS7_SIGNED_DATA', 0x0002),
            ('WIN_CERT_TYPE_RESERVED_1', 0x0003),
            ('WIN_CERT_TYPE_TS_STACK_SIGNED', 0x0004),
        ]

    # XXX: The bCertificate field is padded to a qword-boundary. Keep
    #      this in mind if trying to DER decode it.

    _fields_ = [
        (uint32, 'dwLength'),
        (wRevision, 'wRevision'),
        (wCertificateType, 'wCertificateType'),
        (lambda self: dyn.block(self['dwLength'].li.int() - 8), 'bCertificate'),
    ]

# https://support.microsoft.com/en-us/help/287547/object-ids-associated-with-microsoft-cryptography
# XXX: some of these identifiers are likely in the certificate if we decode it.
_values_ = [
    ('spcIndirectDataContext', '1.3.6.1.4.1.311.2.1.4'),
    ('spcStatementType', '1.3.6.1.4.1.311.2.1.11'),
    ('spcSpOpusInfo', '1.3.6.1.4.1.311.2.1.12'),
    ('individualCodeSigning', '1.3.6.1.4.1.311.2.1.21'),
    ('commercialCodeSigning', '1.3.6.1.4.1.311.2.1.22'),
    ('SPC_MS_JAVA_SOMETHING', '1.3.6.1.4.1.311.15.1'),
    ('spcPelmageData', '1.3.6.1.4.1.311.2.1.15'),
    ('spcLink', '1.3.6.1.4.1.311.2.1.25'),
    ('SPC_TIME_STAMP_REQUEST_OBJID', '1.3.6.1.4.1.311.3.2.1'),
    ('SPC_SIPINFO_OBJID', '1.3.6.1.4.1.311.2.1.30'),
    ('SPC_PE_IMAGE_PAGE_HASHES_V1', '1.3.6.1.4.1.311.2.3.1'), # Page hash using SHA1
    ('SPC_PE_IMAGE_PAGE_HASHES_V2', '1.3.6.1.4.1.311.2.3.2'), # Page hash using SHA256
    ('SPC_NESTED_SIGNATURE_OBJID', '1.3.6.1.4.1.311.2.4.1'),
    ('SPC_RFC3161_OBJID', '1.3.6.1.4.1.311.3.3.1'),

    # Authenticode PE
    ('codeSigning', '1.3.6.1.5.5.7.3.3'),
    ('timeStamping', '1.3.6.1.5.5.7.3.8'),
    ('SPC_KP_LIFETIME_SIGNING_OBJID',  '1.3.6.1.4.1.311.10.3.13'),

    ('itu-t recommendation t 124 version(0) 1', '0.0.20.124.0.1'),
]

if __name__ == '__main__':
    from ptypes import provider
    import pecoff
    x = pecoff.Executable.IMAGE_DOS_HEADER()
    x.source = provider.file('./python.exe')
    offset = x.load()['e_lfanew']
    print(x)

#    x = FileHeader()
#    x.source = provider.file('./python.exe')
#    x.setoffset( int(offset) )
#    print(x.load())

    x = pecoff.Executable.Portable()
    x.setoffset( int(offset) )
    x.source = provider.file('./python.exe')
    print(x.load())
