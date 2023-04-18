import logging, traceback, operator, functools, itertools, array, ptypes
from ptypes import *

from .headers import *
from . import portable

class Signature(pint.enum, uint16):
    # We'll just store all signature types here
    _values_ = [
        ('IMAGE_DOS_SIGNATURE', 0x5a4d),
        ('IMAGE_OS2_SIGNATURE', 0x454e),
        ('IMAGE_OS2_SIGNATURE_LE', 0x454c),
        ('IMAGE_NT_SIGNATURE', 0x4550),

        ('OSF_FLAT_SIGNATURE', 0x454c),
        ('OSF_FLAT_LX_SIGNATURE', 0x584c),
    ]

class IMAGE_DOS_HEADER(pstruct.type):
    class e_magic(Signature): pass

    class Relocation(pstruct.type):
        _fields_ = [
            ( uint16, 'offset' ),
            ( uint16, 'segment' ),
        ]

        def linear(self):
            return self['segment'].int()*0x10 + self['offset'].int()

        def decode(self, **attrs):
            p = self.getparent(ptype.boundary)
            attrs.setdefault('offset', p['Stub'].getoffset()+self.linear())
            return self.new(ptype.undefined, **attrs)

        def summary(self):
            seg, offset = self['segment'], self['offset']
            return "(segment:offset) {:04x}:{:04x} (linear) {:05x}".format(seg.int(), offset.int(), (seg.int() * 0x10 + offset.int()) & 0xfffff)

        def repr(self):
            return self.summary()

    class Oem(pstruct.type):
        _fields_ = [
            ( dyn.array(uint16, 4), 'e_reserved' ),
            ( uint16, 'e_oemid' ),
            ( uint16, 'e_oeminfo' ),
            ( dyn.array(uint16, 10), 'e_reserved2' ),
        ]

    # FIXME: this implementation should be properly tested as there's a chance it could be fucked with
    def __e_oem(self):
        res = self['e_lfarlc'].li
        fields = ['e_magic', 'e_cblp', 'e_cp', 'e_crlc', 'e_cparhdr', 'e_minalloc', 'e_maxalloc', 'e_ss', 'e_sp', 'e_csum', 'e_ip', 'e_cs', 'e_lfarlc', 'e_ovno']

        # if our calculated size for the field directly matches the Oem
        # structure, then this for sure is going to be a PECOFF executable.
        t = IMAGE_DOS_HEADER.Oem
        if res.int() == sum(self[fld].li.size() for fld in fields) + t().a.size() + 4:
            return t

        # otherwise we need to pad it with whatever the input claims it should be
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))

    def __e_lfanew(self):
        paragraphs, relocations = self['e_cparhdr'].li, self['e_lfarlc'].li
        fields = ['e_magic', 'e_cblp', 'e_cp', 'e_crlc', 'e_cparhdr', 'e_minalloc', 'e_maxalloc', 'e_ss', 'e_sp', 'e_csum', 'e_ip', 'e_cs', 'e_lfarlc', 'e_ovno', 'e_oem']

        # if everything matches, then there's a pointer here for PECOFF executables
        if 0x10 * paragraphs.int() == relocations.int() == sum(self[fld].li.size() for fld in fields) + 4:
            return dyn.rpointer(Next, self, pint.uint32_t)

        # XXX: otherwise if paragraphs are less than the relocation pointer, then assume the e_lfanew pointer is still here.
        elif 0x10 * paragraphs.int() < relocations.int() and relocations.int() == sum(self[fld].li.size() for fld in fields) + 4:
            cls = self.__class__
            logging.warning("{:s} : IMAGE_DOS_HEADER.e_cparhdr specified an unexpected number of paragraphs ({:d}). Assuming that there's at least {:d}.".format('.'.join([cls.__module__, cls.__name__]), paragraphs.int(), 4))
            return dyn.rpointer(Next, self, pint.uint32_t)

        # any other condition means that there isn't anything here.
        return pint.uint_t

    def __e_rlc(self):
        fields = ['e_magic', 'e_cblp', 'e_cp', 'e_crlc', 'e_cparhdr', 'e_minalloc', 'e_maxalloc', 'e_ss', 'e_sp', 'e_csum', 'e_ip', 'e_cs', 'e_lfarlc', 'e_ovno', 'e_oem', 'e_lfanew']
        header, count = (self[fld].li.int() for fld in ['e_lfanew', 'e_crlc'])

        if header < sum(self[fld].li.size() for fld in fields) + 4 * count:
            count = 0
        return dyn.array(IMAGE_DOS_HEADER.Relocation, count)

    def __e_parhdr(self):
        fields = ['e_magic', 'e_cblp', 'e_cp', 'e_crlc', 'e_cparhdr', 'e_minalloc', 'e_maxalloc', 'e_ss', 'e_sp', 'e_csum', 'e_ip', 'e_cs', 'e_lfarlc', 'e_ovno', 'e_oem', 'e_rlc', 'e_lfanew']

        # Pad the number of paragraphs that compose the header, ensuring that we clamp it to a minimum count of 4.
        res = 0x10 * max(4, self['e_cparhdr'].li.int())
        return dyn.block(res - sum(self[fld].li.size() for fld in fields))

    def filesize(self):
        res = self['e_cp'].li.int()
        if res > 0:
            cp = res - 1
            return cp * 0x200 + self['e_cblp'].li.int()
        return 0

    def headersize(self):
        res = self['e_cparhdr'].li
        return res.int() * 0x10

    def datasize(self):
        res = self.headersize()
        return (self.filesize() - res) if res > 0 else 0

    def __e_lfarlc(self):
        res = self['e_crlc'].li
        t = dyn.array(IMAGE_DOS_HEADER.Relocation, res.int())
        return dyn.rpointer(t, self, uint16)

    # e_cparhdr * pow(2,4)
    # e_cp * pow(2,9)
    _fields_ = [
        ( e_magic, 'e_magic' ),
        ( uint16, 'e_cblp' ),       # bytes in last page / len mod 512 / UsedBytesInLastPage
        ( uint16, 'e_cp' ),         # pages / 512b pagees / FileSizeInPages
        ( uint16, 'e_crlc' ),       # relocation count / reloc entries count / NumberOfRelocationItems
        ( uint16, 'e_cparhdr' ),    # header size in paragraphs (paragraph=0x10) / number of paragraphs before image / HeaderSizeInParagraphs
        ( uint16, 'e_minalloc' ),   # required paragraphs / minimum number of bss paragraphs / MinimumExtraParagraphs
        ( uint16, 'e_maxalloc' ),   # requested paragraphs / maximum number of bss paragraphs / MaximumExtraParagraphs
        ( uint16, 'e_ss' ),         # ss / stack of image / InitialRelativeSS
        ( uint16, 'e_sp' ),         # sp / sp of image / InitialSP
        ( uint16, 'e_csum' ),       # checksum / checksum (ignored) / Checksum
        ( uint16, 'e_ip' ),         # ip / ip of entry / InitialIP
        ( uint16, 'e_cs' ),         # cs / cs of entry / InitialRelativeCS
        ( __e_lfarlc, 'e_lfarlc' ), # relocation table / address of relocation table / AddressOfRelocationTable

        ( uint16, 'e_ovno'),        # overlay number / overlay # / OverlayNumber
        #( uint32, 'EXE_SYM_TAB'),  # from inc/exe.inc

        # all the data below here changes based on the linker:
        #    Borland, ARJ, LZEXE, PKLITE, LHARC, LHA, CRUNCH, BSA, LARC, etc..
        ( __e_oem, 'e_oem'),        # oem and reserved data
        ( __e_lfanew, 'e_lfanew'),  # new exe header / offset of executable header / AddressOfNewExeHeader
        ( __e_rlc, 'e_rlc' ),       # relocations...sometimes?
        ( __e_parhdr, 'e_parhdr'),  # padding according to number of paragraphs for header size
    ]

### What file format the next header is
class NextHeader(ptype.definition):
    cache = {}

### What file format the data is
class NextData(ptype.definition):
    cache = {}

class Next(pstruct.type):
    def __Header(self):
        t = self['Signature'].li.serialize()
        return NextHeader.withdefault(t, type=t)

    def __Data(self):
        t = self['Signature'].li.serialize()
        return NextData.withdefault(t, type=t)

    _fields_ = [
        (Signature, 'Signature'),
        (__Header, 'Header'),
        (__Data, 'Data'),
    ]

    def Header(self):
        return self['Header']

    def Data(self):
        return self['Data']

## Portable Executable (PE)
@NextHeader.define
class IMAGE_NT_HEADERS(pstruct.type, Header):
    type = b'PE'

    def __Padding(self):
        '''Figure out the PE header size and pad according to SizeOfHeaders'''
        p = self.getparent(File)

        sz = p['Header']['e_lfanew'].li.int()
        opt = self['OptionalHeader'].li

        f = functools.partial(operator.getitem, self)
        res = map(f, ('SignaturePadding', 'FileHeader', 'OptionalHeader', 'DataDirectory', 'Sections'))
        res = sum(map(operator.methodcaller('blocksize'), res))
        res += 2
        return dyn.block(opt['SizeOfHeaders'].int() - res - sz)

    def __DataDirectory(self):
        cls = self.__class__
        hdr, optional = (self[fld].li for fld in ['FileHeader', 'OptionalHeader'])
        length, directory = optional['NumberOfRvaAndSizes'].int(), 8

        if hdr['SizeOfOptionalHeader'].int() < optional.size():
            logging.warning("{:s} : FileHeader.SizeOfOptionalHeader ({:+#x}) is smaller than the OptionalHeader ({:+#x}). Ignoring the OptionalHeader.NumberOfRvaAndSizes ({:d}) and thus the DataDirectory.".format('.'.join([cls.__module__, cls.__name__]), hdr['SizeOfOptionalHeader'].size(), optional.size(), length))
            length = 0

        elif length * directory != hdr['SizeOfOptionalHeader'].int() - optional.size():
            available = hdr['SizeOfOptionalHeader'].int() - optional.size()
            logging.warning("{:s} : OptionalHeader.NumberOfRvaAndSizes ({:d}) does not correspond to FileHeader.SizeOfOptionalHeader ({:+#x}). Available space ({:+#x}) results in only {:d} entries.".format('.'.join([cls.__module__, cls.__name__]), length, optional.size(), available, available // directory))
            length = available // directory

        elif length > 0x10:
            logging.warning("{:s} : OptionalHeader.NumberOfRvaAndSizes ({:d}) is larger than {:d}. Assuming the maximum number of DataDirectory entries ({:d}).".format('.'.join([cls.__module__, cls.__name__]), length, 0x10, 0x10))

        return dyn.clone(portable.DataDirectory, length=min(0x10, length))

    def __OptionalHeaderPadding(self):
        hdr, fields = self['FileHeader'].li, ['OptionalHeader', 'DataDirectory']
        expected = hdr['SizeOfOptionalHeader'].int()
        return dyn.block(max(0, expected - sum(self[fld].li.size() for fld in fields)))

    def __Sections(self):
        header = self['FileHeader'].li
        length = header['NumberOfSections'].int()
        return dyn.clone(portable.SectionTableArray, length=length)

    _fields_ = [
        (uint16, 'SignaturePadding'),
        (portable.IMAGE_FILE_HEADER, 'FileHeader'),
        (portable.IMAGE_OPTIONAL_HEADER, 'OptionalHeader'),
        (__DataDirectory, 'DataDirectory'),
        (__OptionalHeaderPadding, 'Padding(OptionalHeader,DataDirectory)'),
        (__Sections, 'Sections'),
        (__Padding, 'Padding'),
    ]

    def FileHeader(self):
        '''Return the FileHeader which contains a number of sizes used by the file.'''
        return self['FileHeader']

    def getaddressbyoffset(self, offset):
        section = self['Sections'].getsectionbyoffset(offset)
        return section.getaddressbyoffset(offset)

    def getoffsetbyaddress(self, address):
        section = self['Sections'].getsectionbyaddress(address)
        return section.getoffsetbyaddress(address)

    def loadconfig(self):
        return self['DataDirectory'][10]['Address'].d.li

    def tls(self):
        return self['DataDirectory'][9]['Address'].d.li

    def relocateable(self):
        characteristics = self['OptionalHeader']['DllCharacteristics']
        return 'DYNAMIC_BASE' in characteristics

    def has_seh(self):
        characteristics = self['OptionalHeader']['DllCharacteristics']
        return 'NO_SEH' not in characteristics

    def has_nx(self):
        characteristics = self['OptionalHeader']['DllCharacteristics']
        return 'NX_COMPAT' in characteristics

    def has_integrity(self):
        characteristics = self['OptionalHeader']['DllCharacteristics']
        return 'FORCE_INTEGRITY' in characteristics

    def is64(self):
        return self['OptionalHeader'].li.is64()

    def checksum(self):
        p = self.getparent(File)
        res = self['OptionalHeader']['Checksum']

        # Make a copy of our checksum initialized to 0
        field = res.copy(offset=res.offset - p.offset).set(0)

        # Make a copy of our File header, and overwrite the original
        # checksum with 0 so that we can calculate what the checksum
        # is supposed to be.
        data = bytearray(p.serialize())
        data[field.offset : field.offset + field.size()] = field.serialize()

        # Pad the data so that it's a multiple of a dword
        res = 4 - len(data) % 4
        padding = b'\0' * (res % 4)

        # Calculate 16-bit checksum
        res = sum(array.array('I' if len(array.array('I', 4 * b'\0')) > 1 else 'H', bytes(data) + padding))
        checksum = len(data)
        checksum += res & 0xffff
        checksum += res // 0x10000
        checksum += checksum // 0x10000
        checksum &= 0xffff

        # Clamp the result to 32-bits
        return checksum & 0xffffffff

    def Machine(self):
        return self['FileHeader']['Machine']
Portable = IMAGE_NT_HEADERS64 = IMAGE_NT_HEADERS

class SegmentEntry(pstruct.type):
    '''
    Base class for a section entry that both memory-backed and file-backed
    entries inherit from.
    '''
    def properties(self):
        res = super(SegmentEntry, self).properties()
        if hasattr(self, 'Section'):
            res['SectionName'] = self.Section['Name'].str()
        return res

class MemorySegmentEntry(SegmentEntry):
    '''
    This SegmentEntry represents the structure of a segment that has been
    already mapped into memory. This honors the SectionAlignment field from
    the OptionalHeader when padding the segment's data.
    '''
    noncontiguous = True
    def __Alignment(self):
        p = self.getparent(Next)
        header = p.Header()
        optionalheader = header['OptionalHeader'].li
        return dyn.align(optionalheader['SectionAlignment'].int(), undefined=True)

    _fields_ = [
        (__Alignment, 'Alignment'),
        (lambda self: dyn.block(self.Section.getloadedsize()), 'Data'),
    ]

class FileSegmentEntry(SegmentEntry):
    '''
    This SegmentEntry represents the structure of a segment that is on the
    disk and hasn't been mapped into memory. This honors the FileAlignment
    field from the OptionalHeader when padding the segment's data.
    '''
    def __Alignment(self):
        p = self.getparent(Next)
        header = p.Header()
        optionalheader = header['OptionalHeader'].li
        return dyn.align(optionalheader['FileAlignment'].int(), undefined=False)

    _fields_ = [
        (__Alignment, 'Alignment'),
        (lambda self: dyn.block(self.Section.getreadsize()), 'Data'),
    ]

class SegmentTableArray(parray.type):
    '''
    This is a simple array of segment entries where each entry is individually
    tied directly to the SectionTableEntry that it is associated with. Each
    entry is aligned depending on whether it is being loaded from disk or has
    been already loaded into memory.
    '''
    def _object_(self):
        p = self.getparent(Next)
        header = p.Header()
        sections = header['Sections']
        entry = MemorySegmentEntry if isinstance(self.source, ptypes.provider.memorybase) else FileSegmentEntry
        return dyn.clone(entry, Section=sections[len(self.value)])

@NextData.define
class IMAGE_NT_DATA(pstruct.type, Header):
    type = b'PE'

    def __Padding(self):
        if isinstance(self.source, ptypes.provider.memorybase):
            alignment = 0x1000
            res = (alignment - self.getoffset() % alignment) & (alignment - 1)
            return dyn.block(res)
        return dyn.block(0)

    def __Segments(self):
        header = self.p.Header()
        fileheader = header['FileHeader'].li

        # Warn the user if we're unable to determine whether the source is a
        # file-backed or memory-backed provider.
        if all(not isinstance(self.source, item) for item in {ptypes.provider.memorybase, ptypes.provider.fileobj}):
            cls = self.__class__
            logging.warning("{:s} : Unknown ptype source.. treating as a fileobj : {!r}".format('.'.join((cls.__module__, cls.__name__)), self.source))

        return dyn.clone(SegmentTableArray, length=fileheader['NumberOfSections'].int())

    def __CertificatePadding(self):
        header = self.p.Header()
        if len(header['DataDirectory']) < 4:
            return ptype.undefined

        res = header['DataDirectory'][4]
        offset, size = res['Address'].int(), res['Size'].int()
        if offset == 0 or isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        if isinstance(self.source, ptypes.provider.bounded) and offset < self.source.size():
            res = self['Segments'].li.getoffset() + self['Segments'].blocksize()
            return dyn.block(offset - res)

        return ptype.undefined

    def __Certificate(self):
        header = self.p.Header()
        if len(header['DataDirectory']) < 4:
            return ptype.undefined

        res = header['DataDirectory'][4]
        offset, size = res['Address'].int(), res['Size'].int()
        if offset == 0 or isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        if isinstance(self.source, ptypes.provider.bounded) and offset < self.source.size():
            return dyn.clone(parray.block, _object_=portable.headers.Certificate, blocksize=lambda self, size=size: size)

        return ptype.undefined

    _fields_ = [
        (__Padding, 'Padding'),
        (__Segments, 'Segments'),
        (__CertificatePadding, 'CertificatePadding'),
        (__Certificate, 'Certificate'),
    ]

@NextHeader.define
class DosExtender(pstruct.type, Header):
    type = b'DX'
    _fields_ = [
        (word, 'MinRModeParams'),   # minimum number of real-mode params to leave free at run time
        (word, 'MaxRModeParams'),   # maximum number of real-mode params to leave free at run time

        (word, 'MinIBuffSize'),     # minimum number of real-mode params to leave free at run time
        (word, 'MaxIBuffSize'),     # maximum number of real-mode params to leave free at run time
        (word, 'NIStacks'),         # number of interrupt stacks
        (word, 'IStackSize'),       # size in KB of each interrupt stack
        (dword, 'EndRModeOffset'),  # offset of byte past end of real-mode code and data
        (word, 'CallBuffSize'),     # offset of byte past end of real-mode code and data
        (word, 'Flags'),            # flags (0: file is vmm, 1: file is debugger)
        (word, 'UnprivFlags'),      # unprivileged flag (if nonzero, executes at ring 1, 2, or 3)
        (dyn.block(104), 'Reserv'),
    ]

# https://github.com/open-watcom/open-watcom-v2/blob/master/bld/watcom/h/exephar.h

@NextHeader.define
class PharLap(pstruct.type, Header):
    type = b'MP'
    _fields_ = [
        (word, 'SizeRemaind'),
        (word, 'ImageSize'),
        (word, 'NRelocs'),
        (word, 'HeadSize'),
        (word, 'MinExtraPages'),
        (dword, 'ESP'),
        (word, 'CheckSum'),
        (dword, 'EIP'),
        (word, 'FirstReloc'),
        (word, 'NOverlay'),
        (word, 'Reserved'),
    ]

    class SegInfo(pstruct.type):
        _fields_ = [
            (word, 'Selector'),
            (word, 'Flags'),
            (dword, 'BaseOff'),
            (dword, 'MinAlloc'),
        ]

    class RunTimeParams(DosExtender): pass

    class RepeatBlock(pstruct.type):
        _fields_ = [
            (word, 'Count'),
            (lambda self: dyn.block(self['Count'].li.int()), 'String'),
        ]

@NextHeader.define
class PharLap3(PharLap, Header):
    type = b'P3'

    class OffsetSize(pstruct.type):
        def __Offset(self):
            t = getattr(self, '_object_', ptype.block)
            return dyn.rpointer(lambda _: dyn.clone(t, blocksize=lambda _:self['Size'].li.int()), self.getparent(PharLap3), dword)

        _fields_ = [
            (__Offset, 'Offset'),
            (dword, 'Size'),
        ]

        def summary(self):
            return '{:#x}:{:+#x}'.format(self['Offset'].int(), self['Size'].int())

    _fields_ = [
        (word, 'Level'),
        (word, 'HeaderSize'),
        (dword, 'FileSize'),
        (word, 'CheckSum'),

        (dyn.clone(OffsetSize, _object_=PharLap.RunTimeParams), 'RunTimeParams'),
        (OffsetSize, 'Reloc'),
        (dyn.clone(OffsetSize, _object_=dyn.clone(parray.block, _object_=PharLap.SegInfo)), 'SegInfo'),
        (word, 'SegEntrySize'),
        (OffsetSize, 'Image'),
        (OffsetSize, 'SymTab'),
        (OffsetSize, 'GDTLoc'),
        (OffsetSize, 'LDTLoc'),
        (OffsetSize, 'IDTLoc'),
        (OffsetSize, 'TSSLoc'),

        (dword, 'MinExtraPages'),
        (dword, 'MaxExtraPages'),

        (dword, 'Base'),
        (dword, 'ESP'),
        (word, 'SS'),
        (dword, 'EIP'),
        (word, 'CS'),
        (word, 'LDT'),
        (word, 'TSS'),

        (word, 'Flags'),
        (dword, 'MemReq'),
        (dword, 'Checksum32'),
        (dword, 'StackSize'),
        (dyn.block(0x100), 'Reserv'),
    ]

# https://github.com/open-watcom/open-watcom-v2/blob/master/bld/watcom/h/exeflat.h
# https://faydoc.tripod.com/formats/exe-LE.htm
# https://www.program-transformation.org/Transform/PcExeFormat

# XXX: none of these have been used yet
# http://www.edm2.com/0303/rmx-os2.html
# https://github.com/oshogbo/ghidra-lx-loader
# https://github.com/oshogbo/ghidra-lx-loader/blob/master/src/main/java/lx/LX.java
# https://github.com/oshogbo/ghidra-lx-loader/blob/master/src/main/java/lx/LXHeader.java
# https://github.com/oshogbo/ghidra-lx-loader/blob/master/src/main/java/lx/LXObjectPageTable.java
# https://github.com/oshogbo/ghidra-lx-loader/blob/master/src/main/java/lx/LXFixupPageTable.java

class unsigned_0(pint.uint_t): pass
class unsigned_8(byte): pass
class unsigned_16(word): pass
class unsigned_32(dword): pass

@NextHeader.define
class os2_flat_header(pstruct.type, Header):
    type = b'LE'

    class OSF_CPU_(pint.enum, unsigned_16):
        _values_ = [
            ('286', 1),
            ('386', 2),
            ('486', 3),
        ]

    class OSF_(pbinary.flags):
        '''unsigned_32'''
        class _OSF_PM_(pbinary.enum):
            length, _values_ = 4, [
                ('NOT_COMPATIBLE', 1),
                ('COMPATIBLE', 2),
                ('APP', 3),
            ]
        _fields_ = [
            (1, 'unused_1f'),
            (1, 'OSF_TERM_INSTANCE'),
            (2+8+2, 'unused_13'),
            (1, 'OSF_DEVICE_DRIVER'),
            (1, 'OSF_IS_PROT_DLL'),

            (1, 'OSF_IS_DLL'),
            (1, 'unused_e'),
            (1, 'OSF_LINK_ERROR'),
            (1, 'unused_c'),
            (_OSF_PM_, 'OSF_PM'),
            (2, 'unused_6'),
            (1, 'OSF_EXTERNAL_FIXUPS_DONE'),
            (1, 'OSF_INTERNAL_FIXUPS_DONE'),
            (1, 'unused_3'),
            (1, 'OSF_INIT_INSTANCE'),
            (1, 'unused_1'),
            (1, 'OSF_SINGLE_DATA'),
        ]

    class object_record(pstruct.type):
        '''LXObjectTable'''
        class OBJ_(pbinary.flags):
            '''unsigned_32'''
            class PERM_(pbinary.enum):
                length, _values_ = 4, [
                    ('PERM_LOCKABLE', 4),
                    ('PERM_RESIDENT', 2),
                    ('PERM_SWAPPABLE', 1),  # LE
                ]
            _fields_ = [
                (16, 'unused_10'),
                (1, 'IOPL'),
                (1, 'CONFORMING'),
                (1, 'BIG'),
                (1, 'ALIAS_REQUIRED'),
                (PERM_, 'PERM_'),
                (1, 'HAS_INVALID'),
                (1, 'HAS_PRELOAD'),
                (1, 'SHARABLE'),
                (1, 'DISCARDABLE'),
                (1, 'RESOURCE'),
                (1, 'EXECUTABLE'),
                (1, 'WRITEABLE'),
                (1, 'READABLE'),
            ]
        _fields_ = [
            (unsigned_32, 'size'),      # object virtual size
            (unsigned_32, 'addr'),      # base virtual address
            (OBJ_, 'flags'),
            (unsigned_32, 'mapidx'),    # page map index
            (unsigned_32, 'mapsize'),   # number of entries in page map
            (unsigned_32, 'reserved'),
        ]

    class le_map_entry(pstruct.type):
        _fields_ = [
            (dyn.clone(pint.uint_t, length=3), 'page_num'), # 24-bit page number in .exe file
            (unsigned_8, 'flags'),
        ]
    map_entry = le_map_entry    # LXObjectPageTable

    class bundle_types(pint.enum, unsigned_8):
        _values_ = [
            ('FLT_BNDL_EMPTY', 0),
            ('FLT_BNDL_ENTRY16', 1),
            ('FLT_BNDL_GATE16', 2),
            ('FLT_BNDL_ENTRY32', 3),
            ('FLT_BNDL_ENTRYFWD', 4),
        ]

    class flat_bundle_prefix(pstruct.type):
        def __b32_type(self):
            return os2_flat_header.bundle_types
        _fields_ = [
            (unsigned_8, 'b32_cnt'),
            (__b32_type, 'b32_type'),
            (unsigned_16, 'b32_obj'),
        ]

    class flat_null_prefix(pstruct.type):
        def __b32_type(self):
            return os2_flat_header.bundle_types
        _fields_ = [
            (unsigned_8, 'b32_cnt'),
            (__b32_type, 'b32_type'),
        ]

    class flat_bundle_gate16(pstruct.type):
        _fields_ = [
            (unsigned_8, 'e32_flags'),      # flag bits are same as in OS/2 1.x
            (unsigned_16, 'offset'),
            (unsigned_16, 'callgate'),
        ]

    class flat_bundle_entry16(pstruct.type):
        _fields_ = [
            (unsigned_8, 'e32_flags'),      # flag bits are same as in OS/2 1.x
            (unsigned_16, 'e32_offset'),
        ]

    class flat_bundle_entry32(pstruct.type):
        _fields_ = [
            (unsigned_8, 'e32_flags'),      # flag bits are same as in OS/2 1.x
            (unsigned_16, 'e32_offset'),
        ]

    class flat_bundle_entryfwd(pstruct.type):
        _fields_ = [
            (unsigned_8, 'e32_flags'),      # flag bits are same as in OS/2 1.x
            (unsigned_16, 'modord'),
            (unsigned_32, 'value'),
        ]

    class flat_res_table(pstruct.type):
        _fields_ = [
            (unsigned_16, 'type_id'),
            (unsigned_16, 'name_id'),
            (unsigned_32, 'res_size'),
            (unsigned_16, 'object'),
            (unsigned_32, 'offset'),
        ]

    class flat_page(pstruct.type):
        _fields_ = [
            (unsigned_32, 'offset'),
            (unsigned_32, 'size'),
            (unsigned_32, 'flags'),
        ]

    class flat_fixup(pstruct.type):
        class _target(pstruct.type):
            _fields_ = [
                (unsigned_8, 'object'),
                (unsigned_16, 'offset'),
            ]
        _fields_ = [
            (unsigned_8, 'source'),
            (unsigned_8, 'flags'),
            (unsigned_16, 'offset'),
            (lambda self: _target if self['flags'].li.int() else ptype.undefined, 'target'),    # FIXME: check flags properly
        ]

    class _r(dynamic.union):
        OSF_FLAT_RESERVED = 20
        class _vxd(pstruct.type):
            _fields_ = [
                (dyn.array(unsigned_8, 8), 'reserved1'),    # +0xB0
                (unsigned_32, 'winresoff'),                 # +0xB8 Windows VxD version info resource offset
                (unsigned_32, 'winreslen'),                 # +0xBC Windows VxD version info resource lenght
                (unsigned_16, 'device_ID'),                 # +0xC0 Windows VxD device ID
                (unsigned_16, 'DDK_version'),               # +0xC2 Windows VxD DDK version (0x030A)
            ]
        _fields_ = [
            (dyn.array(unsigned_8, OSF_FLAT_RESERVED), 'reserved'),
            (_vxd, 'vxd'),
        ]

    def __offset(target, *fields):
        def pointer(self):
            p = self.getparent(Header)
            parameters = [p[fld].li for fld in fields]
            return target(p, *parameters)
        def offset(self):
            try:
                p = self.getparent(ptype.boundary)
                result = dyn.rpointer(pointer, p, unsigned_32)
            except ptypes.error.ItemNotFoundError:
                result = dyn.pointer(pointer, unsigned_32)
            return result
        return offset

    _fields_ = [
        (unsigned_8, 'byte_order'),             # the byte ordering of the .exe
        (unsigned_8, 'word_order'),             # the word ordering of the .exe

        # FIXME: this should change according to the orders we just snagged
        (unsigned_32, 'level'),                 # the exe format level
        (OSF_CPU_, 'cpu_type'),                 # the cpu type
        (unsigned_16, 'os_type'),               # the operating system type
        (unsigned_32, 'version'),               # .exe version
        (pbinary.littleendian(OSF_), 'flags'),  # .exe flags

        (unsigned_32, 'num_pages'),             # # of pages in .exe
        (unsigned_32, 'start_obj'),             # starting object number (eip)
        (unsigned_32, 'eip'),                   # starting value of eip
        (unsigned_32, 'stack_obj'),             # object # for stack pointer (esp)
        (unsigned_32, 'esp'),                   # starting value of esp

        (unsigned_32, 'page_size'),             # .exe page size
        (lambda self: unsigned_32 if self.type == b'LE' else unsigned_0, 'last_page'),  # size of last page - LE
        (lambda self: unsigned_32 if self.type == b'LX' else unsigned_0, 'page_shift'), # left shift for page offsets - LX

        (unsigned_32, 'fixup_size'),            # fixup section size
        (unsigned_32, 'fixup_cksum'),           # fixup section checksum
        (unsigned_32, 'loader_size'),           # loader section size
        (unsigned_32, 'loader_cksum'),          # loader section checksum

        # FIXME: these should all be pointers
        (__offset((lambda ns, number: dyn.array(ns.object_record, number.int())), 'num_objects'), 'objtab_off'),    # object table offset
        (unsigned_32, 'num_objects'),           # number of objects in .exe

        (unsigned_32, 'objmap_off'),            # object page map offset
        (unsigned_32, 'idmap_off'),             # iterated data map offset

        (__offset((lambda ns, number: dyn.array(ns.flat_res_table, number.int())), 'num_rsrcs'), 'rsrc_off'),       # offset of resource table
        (unsigned_32, 'num_rsrcs'),             # number of resource entries
        (unsigned_32, 'resname_off'),           # offset of resident names table
        (unsigned_32, 'entry_off'),             # offset of entry table
        (unsigned_32, 'moddir_off'),            # offset of module directives table
        (unsigned_32, 'num_moddirs'),           # number of module directives

        (unsigned_32, 'fixpage_off'),           # offset of fixup page table
        (unsigned_32, 'fixrec_off'),            # offset of fixup record table
        (unsigned_32, 'impmod_off'),            # offset of import module name table
        (unsigned_32, 'num_impmods'),           # # of entries in import mod name tbl
        (unsigned_32, 'impproc_off'),           # offset of import procedure name table
        (unsigned_32, 'cksum_off'),             # offset of per-page checksum table
        (unsigned_32, 'page_off'),              # offset of enumerated data pages
        (unsigned_32, 'num_preload'),           # number of preload pages
        (unsigned_32, 'nonres_off'),            # offset of non-resident names table
        (unsigned_32, 'nonres_size'),           # size of non-resident names table
        (unsigned_32, 'nonres_cksum'),          # non-resident name table checksum
        (unsigned_32, 'autodata_obj'),          # object # of autodata segment

        (__offset((lambda ns, length: dyn.block(length.int())), 'debug_len'), 'debug_off'), # offset of the debugging information
        (unsigned_32, 'debug_len'),             # length of the debugging info

        (unsigned_32, 'num_inst_preload'),      # # of instance pages in preload sect
        (unsigned_32, 'num_inst_demand'),       # # instance pages in demand load sect

        (unsigned_32, 'heapsize'),              # size of heap - for 16-bit apps
        (unsigned_32, 'stacksize'),             # size of stack OS/2 only
        (_r, 'r'),
    ]

@NextHeader.define
class os2_flat_extended_header(os2_flat_header, Header):
    type = b'LX'

    class object_record(pstruct.type):
        class OBJ_(pbinary.flags):
            '''unsigned_32'''
            class PERM_(pbinary.enum):
                length, _values_ = 4, [
                    ('PERM_LOCKABLE', 4),
                    ('PERM_CONTIGUOUS', 3), # LX
                    ('PERM_RESIDENT', 2),
                    ('HAS_ZERO_FILL', 1),   # LX
                ]
            _fields_ = [
                (16, 'unused_10'),
                (1, 'IOPL'),
                (1, 'CONFORMING'),
                (1, 'BIG'),
                (1, 'ALIAS_REQUIRED'),
                (PERM_, 'PERM_'),
                (1, 'HAS_INVALID'),
                (1, 'HAS_PRELOAD'),
                (1, 'SHARABLE'),
                (1, 'DISCARDABLE'),
                (1, 'RESOURCE'),
                (1, 'EXECUTABLE'),
                (1, 'WRITEABLE'),
                (1, 'READABLE'),
            ]
        _fields_ = [
            (unsigned_32, 'size'),      # object virtual size
            (unsigned_32, 'addr'),      # base virtual address
            (OBJ_, 'flags'),
            (unsigned_32, 'mapidx'),    # page map index
            (unsigned_32, 'mapsize'),   # number of entries in page map
            (unsigned_32, 'reserved'),
        ]

    class lx_map_entry(pstruct.type):
        _fields_ = [
            (unsigned_32, 'page_offset'),   # offset from Preload page start shifted by page_shift in hdr
            (unsigned_16, 'data_size'),
            (unsigned_16, 'flags'),
        ]
    map_entry = lx_map_entry

@NextHeader.define
class NeHeader(pstruct.type):
    type = b'NE'
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

### FileBase
class File(pstruct.type, ptype.boundary):
    def __Padding(self):
        dos = self['Header'].li
        ofs = dos['e_lfarlc'].int()
        return dyn.block(ofs - self.blocksize()) if ofs > 0 else dyn.block(0)

    def __Relocations(self):
        dos = self['Header'].li
        ofs = dos['e_lfarlc'].int()
        return dyn.array(Dos.Relocation, dos['e_crlc'].li.int() if ofs == self.blocksize() else 0)

    def __Extra(self):
        res = self['Header'].li.headersize()
        if res > 0:
            return dyn.block(res - self.blocksize())
        return ptype.undefined

    def __Stub(self):
        # everything up to e_lfanew
        dos = self['Header'].li
        res = dos['e_lfanew'].int()
        if res > 0:
            return dyn.block(res - self.blocksize())
        return ptype.undefined

    def __Next(self):
        dos = self['Header'].li
        if dos['e_lfanew'].int() == self.blocksize():
            return Next

        # If the entire header is zero, then we assume that this is a PE because
        # only Micro$oft does stupid shit like this with compiled help files.
        elif dos['e_lfanew'].int() == dos.filesize() == 0:
            cls, log = self.__class__, logging.getLogger(__name__)
            log.warning("{:s} : Assuming a {:s} header immediately follows {:s} due to the calculated size from {:s} and the value for {:s}.{:s} being 0.".format('.'.join([cls.__module__, cls.__name__]), 'PECOFF', dos.instance(), dos.instance(), dos.classname(), 'e_lfanew'))
            return Next

        return dyn.block(dos.filesize() - self.blocksize())

    def __NotLoaded(self):
        sz = self['Header'].blocksize()
        sz+= self['Extra'].blocksize()
        sz+= self['Stub'].blocksize()
        sz+= self['Next'].blocksize()
        if isinstance(self.source, ptypes.provider.bounded):
            return dyn.block(self.source.size() - sz)
        return ptype.undefined

    _fields_ = [
        (IMAGE_DOS_HEADER, 'Header'),
        (__Extra, 'Extra'),
        (__Stub, 'Stub'),
        (__Next, 'Next'),
        #(__NotLoaded, 'NotLoaded'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, pecoff.Executable
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        ptypes.setsource(ptypes.prov.file(filename, 'rb'))
        self = z = pecoff.Executable.File()
        z=z.l
    else:
        filename = 'obj/kernel32.dll'
        ptypes.setsource(ptypes.prov.file(filename, 'rb'))
        for x in range(10):
            print(filename)
            try:
                self = z = pecoff.Executable.File()
                z=z.l
                break
            except IOError:
                pass
            filename = '../'+filename

    v=z['next']['header']
    sections = v['Sections']
    exports = v['DataDirectory'][0]
    while exports['Address'].int() != 0:
        exports = exports['Address'].d.l
        print(exports.l)
        break

    imports = v['DataDirectory'][1]
    while imports['Address'].int() != 0:
        imports = imports['Address'].d.l
        print(imports.l)
        break

    relo = v['DataDirectory'][5]['Address'].d.l
    baseaddress = v['OptionalHeader']['ImageBase']
    section = sections[0]
    data = section.data().serialize()
    for item in relo.filter(section):
        for type, offset in item.getrelocations(section):
            print(type, offset)
        continue

