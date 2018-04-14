import ptypes
from ptypes import *

from .__base__ import *
from . import portable

import logging,operator,itertools,array

def open(filename, **kwds):
    logging.warn("{package:s} : {package:s}.open({filename!r}{kwds:s}) has been deprecated. Try using {package:s}.File(source=ptypes.prov.file({filename!r}{kwds:s})) instead.".format(package=__name__, filename=filename, kwds=(', '+', '.join('{:s}={!r}'.format(k, v) for k, v in kwds.iteritems())) if kwds else ''))
    res = File(filename=filename, source=ptypes.provider.file(filename, **kwds))
    return res.load()

class Dos(pstruct.type):
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
            s,o = self['segment'],self['offset']
            return '(segment:offset) %04x:%04x (linear) %05x'% (s.int(),o.int(),(s.int()*0x10+o.int())&0xfffff)

        def repr(self):
            return self.summary()

    class Oem(pstruct.type):
        _fields_ = [
            ( dyn.array(uint16,4), 'e_reserved' ),
            ( uint16, 'e_oemid' ),
            ( uint16, 'e_oeminfo' ),
            ( dyn.array(uint16,10), 'e_reserved2' ),
        ]

    # FIXME: this padding implementation should be properly tested as there's a
    #           chance it could be fucked with
    def __e_padding(self):
        sz = self.blocksize()
        # add Oem structure if within the relocation size (if defined), or
        ofs = self['e_lfarlc'].li.int()
        if ofs > 0:
            leftover = ofs-sz
            return self.Oem if sz+self.Oem().a.blocksize() <= ofs else dyn.clone(self.Oem,blocksize=lambda s:leftover)
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
        cp = self['e_cp'].li.int()-1
        return cp*0x200 + self['e_cblp'].li.int()

    def headersize(self):
        hdr = self['e_cparhdr'].li.int()
        return hdr * 0x10

    def datasize(self):
        return self.filesize() - self.headersize()

    #e_cparhdr << 4
    #e_cp << 9
    _fields_ = [
        ( uint16, 'e_magic' ),
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
        ( lambda self: dyn.rpointer(dyn.array(Dos.Relocation,self['e_crlc'].li.int()), self, uint16), 'e_lfarlc' ), # relocation table
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
        return NextHeader.lookup(t, dyn.clone(NextHeader.unknown, type=t))

    def __Data(self):
        t = self['Signature'].li.serialize()
        return NextData.lookup(t, dyn.clone(NextData.unknown, type=t))

    _fields_ = [
        (uint16, 'Signature'),
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
        sz = self.getparent(File)['Dos']['e_lfanew'].li.int()
        opt = self['OptionalHeader'].li
        res = map(self.__getitem__,('SignaturePadding','FileHeader','OptionalHeader','DataDirectory','Sections'))
        res = sum(map(operator.methodcaller('blocksize'),res))
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
        root = self.getparent(File)
        res = self['OptionalHeader']['Checksum']
        field = res.copy(offset=res.offset-root.offset).set(0)

        data = list(root.serialize())
        data[field.offset:field.offset+field.size()] = field.serialize()

        # FIXME: somehow I'm off-by-one occasionally here
        res = sum(array.array('L', ''.join(data) + '\x00'*(4-len(data)%4)))
        checksum = (res&0xffff) + (res>>16)
        checksum += (checksum>>16)
        return (checksum&0xffff) + len(data)

    def Machine(self):
        return self['FileHeader']['Machine']
Portable = IMAGE_NT_HEADERS64 = IMAGE_NT_HEADERS

@NextData.define
class IMAGE_NT_HEADERS_data(pstruct.type, Header):
    type = 'PE'

    def __Sections(self):
        cls = self.__class__
        header = self.p.Header()
        sections = header['Sections'].li
        optionalheader = header['OptionalHeader'].li

        # memory
        if isinstance(self.source, ptypes.provider.memorybase) or (hasattr(ptypes.provider, 'Ida') and self.source is ptypes.provider.Ida):
            class sectionentry(pstruct.type):
                noncontiguous = True
                _fields_ = [
                    (dyn.align(optionalheader['SectionAlignment'].int(), undefined=True), 'Padding'),
                    (lambda s: dyn.block(s.Section.getloadedsize()), 'Data'),
                ]

        # file (default)
        else:
            if not isinstance(self.source, ptypes.provider.filebase):
                logging.warn("{:s} : Unknown ptype source.. treating as a fileobj : {!r}".format('.'.join((cls.__module__, cls.__name__)), self.source))

            class sectionentry(pstruct.type):
                _fields_ = [
                    (dyn.align(optionalheader['FileAlignment'].int()), 'Padding'),
                    (lambda s: dyn.block(s.Section.getreadsize()), 'Data'),
                ]

        sectionentry.properties = lambda self: dict(itertools.chain(super(pstruct.type, self).properties().iteritems(), {'SectionName':self.SectionName}.iteritems()))
        class result(parray.type):
            length = len(sections)
            def _object_(self):
                sect = sections[len(self.value)]
                return dyn.clone(sectionentry, Section=sect, SectionName=sect['Name'].str())
        return result

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
            return dyn.clone(parray.block, _object_=portable.headers.Certificate, blocksize=lambda self,size=size: size)

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
            return '{:#x}:{:+#x}'.format(self['Offset'].int(),self['Size'].int())

    _fields_ = [
        (word, 'Level'),
        (word, 'HeaderSize'),
        (dword, 'FileSize'),
        (word, 'CheckSum'),

        (dyn.clone(OffsetSize,_object_=PharLap.RunTimeParams), 'RunTimeParams'),
        (OffsetSize, 'Reloc'),
        (dyn.clone(OffsetSize,_object_=dyn.clone(parray.block,_object_=PharLap.SegInfo)), 'SegInfo'),
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
        dos = self['Dos'].li
        ofs = dos['e_lfarlc'].int()
        return dyn.block(ofs - self.blocksize()) if ofs > 0 else dyn.block(0)

    def __Relocations(self):
        dos = self['Dos'].li
        ofs = dos['e_lfarlc'].int()
        return dyn.array(Dos.Relocation, dos['e_crlc'].li.int() if ofs == self.blocksize() else 0)

    def __Stub(self):
        # everything up to e_lfanew
        dos = self['Dos'].li
        lfanew = dos['e_lfanew'].int()
        if lfanew > 0:
            return dyn.block(lfanew - self.blocksize())
        return ptype.undefined

    def __Next(self):
        dos = self['Dos'].li
        if dos['e_lfanew'].int() == self.blocksize():
            return Next
        return dyn.block(dos.filesize() - self.blocksize())

    def __NotLoaded(self):
        sz = self['Dos'].blocksize()
        sz+= self['Extra'].blocksize()
        sz+= self['Stub'].blocksize()
        sz+= self['Next'].blocksize()
        if isinstance(self.source, ptypes.provider.filebase):
            return dyn.block( self.source.size() - sz)
        return ptype.undefined

    _fields_ = [
        (Dos, 'Dos'),
        (lambda s: dyn.block(s['Dos'].li.headersize() - s.blocksize()), 'Extra'),
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
    for e in relo.getbysection(section):
        for a,r in e.getrelocations(section):
            print e
            data = r.relocate(data, 0, section)
        continue

