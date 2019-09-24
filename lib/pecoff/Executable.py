import logging, operator, functools, itertools, array, ptypes
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

    # FIXME: this padding implementation should be properly tested as there's a
    #           chance it could be fucked with
    def __e_padding(self):
        sz = self.blocksize()
        # add Oem structure if within the relocation size (if defined), or
        ofs = self['e_lfarlc'].li.int()
        if ofs > 0:
            leftover = ofs - sz
            return self.Oem if sz + self.Oem().a.blocksize() <= ofs else dyn.clone(self.Oem, blocksize=lambda s: leftover)
        # otherwise insert it if we're still within the total header size
        return self.Oem if sz+self.Oem().a.blocksize() <= self.headersize() else dyn.block(0)

    def __e_lfanew(self):
        # if we're satisfying the specification's req for an extra header, then
        #   include our pointer to it
        #if dos['e_ss'].int() == 0:      # my tests...
        if self['e_lfarlc'].li.int() >= 0x40:
            return dyn.rpointer(Next, self, pint.uint32_t)
        return pint.uint_t

    def filesize(self):
        res = self['e_cp'].li.int()
        if res > 0:
            cp = res - 1
            return cp * 0x200 + self['e_cblp'].li.int()
        return 0

    def headersize(self):
        res = self['e_cparhdr'].li.int()
        return res * 0x10

    def datasize(self):
        res = self.headersize()
        return (self.filesize() - res) if res > 0 else 0

    #e_cparhdr << 4
    #e_cp << 9
    _fields_ = [
        ( e_magic, 'e_magic' ),
        ( uint16, 'e_cblp' ),        # bytes in last page / len mod 512 / UsedBytesInLastPage
        ( uint16, 'e_cp' ),          # pages / 512b pagees / FileSizeInPages
        ( uint16, 'e_crlc' ),        # relocation count / reloc entries count / NumberOfRelocationItems
        ( uint16, 'e_cparhdr' ),     # header size in paragraphs (paragraph=0x10) / number of paragraphs before image / HeaderSizeInParagraphs
        ( uint16, 'e_minalloc' ),    # required paragraphs / minimum number of bss paragraphs / MinimumExtraParagraphs
        ( uint16, 'e_maxalloc' ),    # requested paragraphs / maximum number of bss paragraphs / MaximumExtraParagraphs
        ( uint16, 'e_ss' ),          # ss / stack of image / InitialRelativeSS
        ( uint16, 'e_sp' ),          # sp / sp of image / InitialSP
        ( uint16, 'e_csum' ),        # checksum / checksum (ignored) / Checksum
        ( uint16, 'e_ip' ),          # ip / ip of entry / InitialIP
        ( uint16, 'e_cs' ),          # cs / cs of entry / InitialrmwwelativeIp
        ( lambda self: dyn.rpointer(dyn.array(IMAGE_DOS_HEADER.Relocation, self['e_crlc'].li.int()), self, uint16), 'e_lfarlc' ), # relocation table
        ( uint16, 'e_ovno'),         # overlay number
        #( uint32, 'EXE_SYM_TAB'),   # from inc/exe.inc

        # all the data below here changes based on the linker:
        #    Borland, ARJ, LZEXE, PKLITE, LHARC, LHA, CRUNCH, BSA, LARC, etc..
        ( __e_padding, 'e_oem'),       # oem and reserved data
        ( __e_lfanew, 'e_lfanew'),
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
    type = 'PE'

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
        length = self['OptionalHeader'].li['NumberOfRvaAndSizes'].int()
        if length > 0x10:   # XXX
            logging.warn("{:s} : OptionalHeader.NumberOfRvaAndSizes specified >0x10 entries ({:#x}) for the DataDirectory. Assuming the maximum of 0x10.".format('.'.join((cls.__module__, cls.__name__)), length))
            length = 0x10
        return dyn.clone(portable.DataDirectory, length=length)

    def __Sections(self):
        header = self['FileHeader'].li
        length = header['NumberOfSections'].int()
        return dyn.clone(portable.SectionTableArray, length=length)

    _fields_ = [
        (uint16, 'SignaturePadding'),
        (portable.IMAGE_FILE_HEADER, 'FileHeader'),
        (portable.IMAGE_OPTIONAL_HEADER, 'OptionalHeader'),
        (__DataDirectory, 'DataDirectory'),
        (__Sections, 'Sections'),
        (__Padding, 'Padding'),
    ]

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
        padding = '\0' * (res % 4)

        # Calculate 16-bit checksum
        res = sum(array.array('I', str(data) + padding))
        checksum = len(data)
        checksum += res & 0xffff
        checksum += res / 0x10000
        checksum += checksum / 0x10000
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
    def __Padding(self):
        p = self.getparent(Next)
        header = p.Header()
        optionalheader = header['OptionalHeader'].li
        return dyn.align(optionalheader['SectionAlignment'].int(), undefined=True)

    _fields_ = [
        (__Padding, 'Padding'),
        (lambda self: dyn.block(self.Section.getloadedsize()), 'Data'),
    ]

class FileSegmentEntry(SegmentEntry):
    '''
    This SegmentEntry represents the structure of a segment that is on the
    disk and hasn't been mapped into memory. This honors the FileAlignment
    field from the OptionalHeader when padding the segment's data.
    '''
    def __Padding(self):
        p = self.getparent(Next)
        header = p.Header()
        optionalheader = header['OptionalHeader'].li
        return dyn.align(optionalheader['FileAlignment'].int(), undefined=True)

    _fields_ = [
        (__Padding, 'Padding'),
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
class IMAGE_NT_HEADERS_data(pstruct.type, Header):
    type = 'PE'

    def __Sections(self):
        header = self.p.Header()
        fileheader = header['FileHeader'].li

        # Warn the user if we're unable to determine whether the source is a
        # file-backed or memory-backed provider.
        if all(not isinstance(self.source, item) for item in {ptypes.provider.memorybase, ptypes.provider.filebase}):
            cls = self.__class__
            logging.warn("{:s} : Unknown ptype source.. treating as a fileobj : {!r}".format('.'.join((cls.__module__, cls.__name__)), self.source))

        return dyn.clone(SegmentTableArray, length=fileheader['NumberOfSections'].int())

    def __CertificatePadding(self):
        header = self.p.Header()
        if len(header['DataDirectory']) < 4:
            return ptype.undefined

        res = header['DataDirectory'][4]
        offset, size = res['Address'].int(), res['Size'].int()
        if offset == 0 or isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        lastoffset = self['Sections'].li.getoffset() + self['Sections'].blocksize()
        if hasattr(self.source, 'size') and offset < self.source.size():
            return dyn.block(offset - lastoffset)

        return ptype.undefined

    def __Certificate(self):
        header = self.p.Header()
        if len(header['DataDirectory']) < 4:
            return ptype.undefined

        res = header['DataDirectory'][4]
        offset, size = res['Address'].int(), res['Size'].int()
        if offset == 0 or isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        if hasattr(self.source, 'size') and offset < self.source.size():
            return dyn.clone(parray.block, _object_=portable.headers.Certificate, blocksize=lambda self, size=size: size)

        return ptype.undefined

    _fields_ = [
        (__Sections, 'Sections'),
        (__CertificatePadding, 'CertificatePadding'),
        (__Certificate, 'Certificate'),
    ]

@NextHeader.define
class DosExtender(pstruct.type, Header):
    type = 'DX'
    _fields_ = [
        (word, 'MinRModeParams'),
        (word, 'MaxRModeParams'),

        (word, 'MinIBuffSize'),
        (word, 'MaxIBuffSize'),
        (word, 'NIStacks'),
        (word, 'IStackSize'),
        (dword, 'EndRModeOffset'),
        (word, 'CallBuffSize'),
        (word, 'Flags'),
        (word, 'UnprivFlags'),
        (dyn.block(104), 'Reserv'),
    ]

@NextHeader.define
class PharLap(pstruct.type, Header):
    type = 'MP'
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
            (lambda s: dyn.block(s['Count'].li.int()), 'String'),
        ]

@NextHeader.define
class PharLap3(PharLap, Header):
    type = 'P3'

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

@NextHeader.define
class NeHeader(pstruct.type):
    type = 'NE'
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
        return dyn.block(dos.filesize() - self.blocksize())

    def __NotLoaded(self):
        sz = self['Header'].blocksize()
        sz+= self['Extra'].blocksize()
        sz+= self['Stub'].blocksize()
        sz+= self['Next'].blocksize()
        if isinstance(self.source, ptypes.provider.filebase):
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
    import Executable
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        v = Executable.open(filename)
    else:
        filename = 'obj/kernel32.dll'
        for x in range(10):
            print filename
            try:
                v = Executable.open(filename)
                break
            except IOError:
                pass
            filename = '../'+filename

    sections = v['Sections']
    exports = v['DataDirectory'][0]
    while exports['Address'].int() != 0:
        exports = exports['Address'].d.l
        print exports.l
        break

    imports = v['DataDirectory'][1]
    while imports['Address'].int() != 0:
        imports = imports['Address'].d.l
        print imports.l
        break

    relo = v['DataDirectory'][5]['Address'].d.l
    baseaddress = v['OptionalHeader']['ImageBase']
    section = sections[0]
    data = section.data().serialize()
    for item in relo.filter(section):
        for _, r in item.getrelocations(section):
            print item
            data = r.relocate(data, 0, section)
        continue

