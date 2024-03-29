'''
Multiple Stream Format
https://github.com/microsoft/microsoft-pdb
'''
import builtins, ptypes, ndk.intsafe as intsafe
from ptypes import *
from ndk.intsafe import *

class CB(intsafe.long): pass
class SN(intsafe.unsigned_short): pass
class UNSN(intsafe.unsigned_long): pass
class OFF(intsafe.long): pass
class ushort(intsafe.unsigned_short): pass
class PN16(intsafe.unsigned___int16): pass
class SPN16(intsafe.unsigned___int16): pass
class PN32(intsafe.unsigned___int32): pass
class SPN32(intsafe.unsigned___int32): pass
#PN, SPN, UPN, USPN = PN16, SPN16, PN32, SPN32

class Pointer(ptype.opointer_t):
    def _object_(self):
        if hasattr(self, '_cbPg'):
            return dyn.block(self._cbPg)
        p = self.getparent(None)    # XXX: should be MSF or File
        hdr = p['hdr']
        return dyn.block(hdr['cbPg'].int())

    def summary(self):
        return self.object.summary()

class PagePointer(Pointer):
    def _calculate_(self, index):
        parent = self.parent
        cbPg = getattr(parent if parent else self, '_cbPg', 0)
        return index * cbPg

    def _object_(self):
        parent = self.parent
        cbPg = getattr(parent if parent else self, '_cbPg', 0)
        return dyn.block(cbPg)

class PN(PagePointer): _value_ = PN16
class SPN(PagePointer): _value_ = SPN16
class UPN(PagePointer): _value_ = PN32
class USPN(PagePointer): _value_ = SPN32

# FIXME: the people (person?) who wrote the PDB parsing code is fucking nuts. no wonder
#        nobody at micro$oft attempted to document it, it's completely unreadable fucking
#        trash. reusage of method names for variables across different scopes? omfg...

cbPgMax = 0x1000
cbPgMin = 0x400
cbDbMax = 128 * 0x10000             # 128meg
cpnDbMax = 0x10000
cbitsFpmMax = cpnDbMax
cbFpmMax = cbitsFpmMax // 8
cpnDbMaxBigMsf = 0x100000           # 2^20 pages
cbitsFpmMaxBigMsf = cpnDbMaxBigMsf
cbFpmMaxBigMsf = cbitsFpmMaxBigMsf // 8

snMax = 0x1000              # max no of streams in msf
pnMaxMax = 0xffff           # max no of pgs in any msf
unsnMax = 0x10000           # 64K streams
upnMaxMax = cpnDbMaxBigMsf  # 2^20 pages

### https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L196
# XXX: this next shit is hilarious, look at what this next chunk of copied code actually means...

# #ifdef SMALLPAGES
#     MSF_PARMS(1024, 10, pnMaxMax, 8, 8),    // gives 64meg
# #else
#     MSF_PARMS(cbPgMin, 10, pnMaxMax, 8, 8), // gives 64meg (??)
# #endif
#     MSF_PARMS(2048,    11, pnMaxMax, 4, 4), // gives 128meg
#     MSF_PARMS(cbPgMax, 12, 0x7fff,   2, 1)  // gives 128meg

SMALLPAGES = False
cbPgMax, cbPgMin = 0x1000, 0x200 if SMALLPAGES else 0x400

rgmsfparms = [
    (1024, 10) if SMALLPAGES else (cbPgMin, 10),             # ?!?! who in the fuck #ifdef'd cbPgMin to 0x400
    (2048, 11),
    (cbPgMax, 12),
]

# #ifdef SMALLPAGES
#     MSFHC_PARMS(cbPgMin,  9, upnMaxMax, 4, 1),  // gives .5GB, note this is used
#                                                 // primarily for small pdbs, so
#                                                 // keep growth rate low (2K).
#     MSFHC_PARMS(1024,    10, upnMaxMax, 8, 1),  // gives 1.0GB
# #else
#     MSFHC_PARMS(cbPgMin, 10, upnMaxMax, 8, 1),  // gives 1.0GB
# #endif
#     MSFHC_PARMS(2048,    11, upnMaxMax, 4, 1),  // gives 2.0GB
#     MSFHC_PARMS(cbPgMax, 12, upnMaxMax, 2, 1)   // gives 4.0GB

rgmsfparms_hc = (
    [(cbPgMin, 9), (1024, 10)] if SMALLPAGES else [(cbPgMin, 10)]
) + [
    (2048, 11),
    (cbPgMax, 12),
]

# XXX: and the best part about all of those conditionals being used to set some globals is that... both
#      rgmsfparms and rgmsfparms_hc end up being the same damn thing (log2)... completely disregarding all
#      the macro-specific options they defined. 56 lines of fucking obfuscation for no reason whatsoever...

cpnMaxForCb = lambda cb: ((cb) + cbPgMin - 1) // cbPgMin    # XXX: love this naming scheme *pulls trigger*
cpnForCbLgCbPg = lambda count, page: math.trunc((lambda shift, divisor: math.ceil((count + shift) // divisor))(pow(2, math.log2(page)) - 1, pow(2, math.log2(page))))

class PG(ptype.block):
    length = cbPgMax

class szMagic(pstruct.type):
    class _Format(pstruct.type):
        def __Extra(self):
            res = self['Format'].li
            return dyn.clone(pstr.string, length=13 if res.str() == 'pro' else 0)

        _fields_ = [
            (dyn.clone(pstr.string, length=3), 'Format'),       # MSF | pro
            (__Extra, 'Extra'),                                 # gram database
        ]

        def alloc(self, **fields):
            res = super(szMagic._Format, self).alloc(**fields)
            if all(fld not in fields for fld in ['Format', 'Extra']):
                return res.set(Format='MSF', Extra=' ')
            elif 'Extra' not in fields and res['Format'].str() == 'MSF':
                return res.set(Extra=' ')
            elif 'Extra' not in fields and res['Format'].str() == 'pro':
                return res.set(Extra='gram database ')
            return res

        def summary(self):
            return "{!r}".format(u''.join(self[fld].str() for fld in ['Format', 'Extra']))

        def str(self):
            return u''.join(self[fld].str() for fld in ['Format', 'Extra']).strip()

        def BigHeader(self):
            return self.str() == 'MSF'

    _fields_ = [
        (dyn.clone(pstr.string, length=15), 'Producer'),    # Microsoft C/C++
        (dyn.clone(pstr.string, length=1), 'pre(Format)'),
        (_Format, 'Format'),                                #  MSF
        (dyn.clone(pstr.string, length=1), 'post(Format)'),
        (dyn.clone(pstr.string, length=4), 'Version'),      # 7.00
        (dyn.clone(pstr.string, length=2), 'CRLF'),         # \r\n
        (dyn.clone(pstr.string, length=1), '1A'),           # \x1a
        (dyn.clone(pstr.string, length=2), 'DSJG'),         # DS | JG
        (dyn.clone(pstr.string, length=1), 'NULL'),         # \0
    ]

    def alloc(self, **fields):
        fields.setdefault('Format', self._Format().alloc())
        res = super(szMagic, self).alloc(**fields)
        bighdr = False if res['Format'].str() == 'program database' else True
        if 'Producer' not in fields:
            res['Producer'].set('Microsoft C/C++')
        if any(fld not in fields for fld in ['pre(Format)', 'post(Format)']):
            res.set(**{fld : ' ' for fld in ['pre(Format)', 'post(Format)'] if fld not in fields})
        if 'CRLF' not in fields:
            res['CRLF'].set('\r\n')
        if '1A' not in fields:
            res['1A'].set('\x1a')
        if 'DSJG' not in fields:
            res['DSJG'].set('DS' if bighdr else 'DS')
        if 'NULL' not in fields:
            res['NULL'].set('\0')
        if 'Version' not in fields:
            res['VERSION'].set("{:.2f}".format(7 if bighdr else 2))
        return res

    def BigHeader(self):
        return self['Format'].BigHeader()

    def Version(self):
        string = self['Version'].str()
        return builtins.float(string)

    def str(self):
        return u''.join(self[fld].str() for fld in self)

class SI(pstruct.type):
    _fields_ = [
        (CB, 'cb'),                     # https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L1749
        (lambda self: dyn.array(UPN, self['cb'].li.int()), 'mpspnpn'),
    ]
    def spnMac(self):
        '''https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L275'''
        cb = self['cb'].int()
        result, mask = cpnForCbLgCbPg(cb, self._cbPg), pow(2, 8 * USPN().a.blocksize()) - 1
        assert(result == result & mask)
        return result

class SI_PERSIST(SI):
    # PDB/msf/msf.cpp:1331
    # PDB/msf/msf.cpp:1306
    _fields_ = [
        (CB, 'cb'),                     # https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L1749
        (intsafe.signed___int32, 'mpspnpn'),    # XXX: guessing this is an index into the mpspnpn field
    ]
    def summary(self):
        return "cb={:#x} mpspnpn={:#x}".format(self['cb'], self['mpspnpn'])

cbMaxSerialization = snMax * SI_PERSIST().a.blocksize() + SN().a.blocksize() + ushort().a.blocksize() + pnMaxMax * PN().a.blocksize()
class MSF_HDR(pstruct.type):
    '''PDB/msf/msf.cpp:933'''
    _fields_ = [
        #(dyn.clone(pstr.string, length=0x2c), 'szMagic'),   # Microsoft C/C++ program database 2.00\r\n\x1a\x4a\x47
        (CB, 'cbPg'),
        (PN, 'pnFpm'),
        (PN, 'pnMac'),
        (SI_PERSIST, 'siSt'),
        #(dyn.array(PN, cpnMaxForCb(cbMaxSerialization)), 'mpspnpn'),
    ]

    def summary(self):
        return "cbPg={:#x} pnFpm={:#x} pnMac={:#x} siSt={{{:s}}}".format(self['cbPg'], self['pnFpm'], self['pnMac'], self['siSt'])

    def alloc(self, **fields):
        res = super(MSF_HDR, self).alloc(**fields)
        if 'cbPg' not in fields:
            res.set(cbPg=cbPgMax)
        if 'pnFpm' not in fields:
            res.set(PnFpm=1)    # must be 1 or 2
        return res if 'cbPg' not in fields else res.set(cbPg=cbPgMax)

cbBigMSFMaxSer = unsnMax * SI_PERSIST().a.blocksize() + UNSN().a.blocksize() + upnMaxMax * UPN().a.blocksize()
class BIGMSF_HDR(MSF_HDR):
    '''PDB/msf/msf.cpp:946'''
    _fields_ = [
        #(dyn.clone(pstr.string, length=0x1e), 'szMagic'),   # Microsoft C/C++ MSF 7.00\r\n\x1a\x44\x53
        (CB, 'cbPg'),
        (UPN, 'pnFpm'),
        (UPN, 'pnMac'),
        (SI_PERSIST, 'siSt'),
        #(dyn.array(PN32, cpnMaxForCb(cpnMaxForCb(cbBigMSFMaxSer) * PN32.length)), 'mpspnpn'),
    ]
    def summary(self):
        return "cbPg={:#x} pnFpm={:#x} pnMac={:#x} siSt={{{:s}}}".format(self['cbPg'], self['pnFpm'], self['pnMac'], self['siSt'].summary())

class StrmTbl(pstruct.type):
    '''https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L554'''

class StrmTbl_BigMsf2(StrmTbl):
    '''https://github.com/Microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L551'''

    ### Size: https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L753
    ###       sizeof(SPN32) + snMacT*sizeof(CB);
    def __streamLocations(self):
        header, sizes = self._msfHeader, self['streamSizes'].li
        table = [ cpnForCbLgCbPg(size.int(), self._msfHeader['cbPg'].int()) for size in sizes ]

        # FIXME: this is a list of SPNs, but because of how large each entry can be,
        #        it shouldn't only use SPNs as an intermediary. nobody should really
        #        care about them being pointers anyways... (i sure as fuck don't).
        class argh(parray.type):
            pass
        argh.length, argh._object_ = len(table), lambda self, table=table: dyn.block(4 * table[len(self.value)])
        return argh

    _fields_ = [
        (SPN32, 'snMacT'),  # number of streams
        (lambda self: dyn.array(CB, self['snMacT'].li.int()), 'streamSizes'),
        (__streamLocations, 'streamLocations'),
    ]

class StrmTbl_SmallMsf(StrmTbl):
    '''https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L692'''

    ### Size: https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L857
    ###       sizeof(SN) + sizeof(ushort) + snMacT * sizeof(SI_PERSIST)

    # FIXME: not sure if this is an array of SI_PERSIST...
    _fields_ = [
        (SN, 'snMacT'), # number of streams
        (ushort, '0'),
        (lambda self: dyn.array(SI_PERSIST, self['snMacT'].li.int()), 'cbCopyRgsiSer'),
    ]

class _mpspnpn(parray.type):
    '''This points to an array of segments that contain the stream table.'''
    def enumerate(self):
        if hasattr(self, '_msfHeader'):
            minimum = self._msfHeader['pnFpm'].int()
        elif isinstance(self.parent, MSF):
            minimum = self.parent['hdr']['pnFpm'].int()
        else:
            minimum = 0

        carry = 0
        for segment in self:
            if segment.int() < minimum:
                continue
            for index, pnpn in enumerate(segment.d.li):
                yield carry + index, pnpn
            carry += len(segment.d)
        return

    def iterate(self):
        for _, segment in self.enumerate():
            yield segment
        return

    def segments(self):
        '''https://github.com/microsoft/microsoft-pdb/blob/master/PDB/msf/msf.cpp#L1960'''
        if hasattr(self, '_msfHeader'):
            header = self._msfHeader
            pageSize = self._msfHeader['cbPg'].int()
            start, size = (header['siSt'][field].int() for field in ['mpspnpn', 'cb'])
        elif isinstance(self.parent, MSF):
            header = self.parent['hdr']
            pageSize = header['cgPg'].int()
            start, size = (header['siSt'][field].int() for field in ['mpspnpn', 'cb'])
        else:
            pageSize = cbPgMin
            start, size = 0, pageSize

        count = math.trunc(math.ceil((size + pageSize - 1) // pageSize))
        for valid, segment in zip(range(start + count), self.iterate()):
            if valid >= start:
                yield segment
            continue
        return

    def dereference(self, **attrs):
        table = [segment.d.l for segment in self.segments()]
        source = ptypes.provider.disorderly(table, autocommit={})

        if hasattr(self, '_msfHeader'):
            header = self._msfHeader
            pageSize = self._msfHeader['cbPg'].int()
            start, size = (header['siSt'][field].int() for field in ['mpspnpn', 'cb'])
        elif isinstance(self.parent, MSF):
            header = self.parent['hdr']
            pageSize = header['cgPg'].int()
            start, size = (header['siSt'][field].int() for field in ['mpspnpn', 'cb'])
        else:
            pageSize = cbPgMin
            start, size = 0, pageSize

        # create a backing type using the collected segments as its source,
        # and then a block of the correct size that actually uses it.
        segment_t = dyn.block(pageSize)
        backing_t = dyn.array(segment_t, len(table))
        backing = self.new(backing_t, recurse=self.attributes, source=source).l
        return self.new(dyn.block(size), source=ptypes.provider.proxy(backing))

class MSF(pstruct.type):
    class _mpspnpn_SmallMsf(_mpspnpn):
        class PageNumber(PN):
            def _object_(self):
                return dyn.array(PN, self._cbPg // PN().a.blocksize())
        _object_ = PageNumber

    class _mpspnpn_BigMsf2(_mpspnpn):
        class UnsignedPageNumber(UPN):
            def _object_(self):
                return dyn.array(UPN, self._cbPg // UPN().a.blocksize())
        _object_ = UnsignedPageNumber

    def __mpspnpn(self):
        res = self['szMagic'].li
        _mpspnpn_BigMsf2 = self._mpspnpn_BigMsf2
        _mpspnpn_SmallMsf = self._mpspnpn_SmallMsf
        ty, length = (_mpspnpn_BigMsf2, cpnMaxForCb(cpnMaxForCb(cbBigMSFMaxSer) * PN32.length)) if res.BigHeader() else (_mpspnpn_SmallMsf, cpnMaxForCb(cbMaxSerialization))
        return dyn.clone(ty, length=length)

    def __padding(self):
        hdr, fields = self['hdr'].li, ['szMagic', 'align(szMagic)', 'hdr', 'reserved', 'mpspnpn']
        pgsize, count = hdr['cbpg'].int(), hdr['pnFpm'].int()
        length = pgsize * count - sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, length))

    @property
    def PG(self):
        raise AssertionError('this property has been deprecated, because it is pretty fucking stupid.')
        if self.initializedQ():
            return dyn.clone(PG, length=self['hdr']['cbPg'].int())
        return dyn.clone(PG, length=cbPgMax)

    #def __free_page_map(self):
    #    hdr = self['hdr'].li
    #    page = dyn.clone(PG, length=hdr['cbpg'].int())
    #    return dyn.array(page, hdr['pnFpm'].int())

    #def __pages(self):
    #    hdr = self['hdr'].li
    #    pgsize, total = hdr['cbpg'].int(), hdr['pnMac'].int()

    #    count = hdr['pnMac'].int() - hdr['pnFpm'].int()
    #    return dyn.clone(ptype.block, length=pgsize * max(0, count))
    #    return dyn.array(block, max(0, count))

    def __reserved_boundary(self):
        '''hook decoding an empty field in order to propagate the page size'''
        self._msfHeader = self.attributes['_msfHeader'] = hdr = self['hdr'].li
        self._cbPg = self.attributes['_cbPg'] = hdr['cbPg'].int()
        spnMac = hdr['siSt']['cb']
        self._cpnForCbLgCbPg = self.attributes['_cpnForCbLgCbPg'] = cpnForCbLgCbPg(spnMac.int(), hdr['cbPg'].int())
        return ptype.undefined

    _fields_ = [
        (szMagic, 'szMagic'),
        (dyn.align(4), 'align(szMagic)'),
        (lambda self: BIGMSF_HDR if self['szMagic'].li.BigHeader() else MSF_HDR, 'hdr'),
        (__reserved_boundary, 'reserved'),
        (__mpspnpn, 'mpspnpn'),         # XXX: this looks like it references an allocation table
        (__padding, 'padding'),
        #(__free_page_map, 'Fpm'),
        #(__pages, 'Mac'),   # XXX: what the fuck is with this naming?
    ]

    def alloc(self, **fields):
        fields.setdefault('szMagic', szMagic().a)
        res = super(MSF, self).alloc(**fields)
        if 'hdr' not in fields:
            res['hdr'].a
        if 'hdr' not in fields and 'Fpm' in fields:
            res['hdr'].set(pnFpm=res['Fpm'].size() // res['hdr']['cbPg'].int())
            assert(res['hdr']['pnFpm'].int() == res['Fpm'].size() / res['hdr']['cbPg'].int())
        if 'hdr' not in fields and 'Mac' in fields:
            used = 1 + res['hdr']['pnFpm'].int()
            res['hdr'].set(pnMac=used + res['Mac'].size() // res['hdr']['cbPg'].int())
            assert(res['hdr']['pnMac'].int() == used + res['Mac'].size() / res['hdr']['cbPg'].int())
        return res

### trash everything below this ###
class Relocation(pstruct.type):
    _fields_ = [
        (int, 'Address'),
        (int, 'SymbolIndex'),
        (short, 'Type'),
    ]

class ImageSymbol(pstruct.type):
    _fields_ = [
        (int, 'Zero'),
        (int, 'OffsetToLongName'),
        (int, 'Value'),
        (short, 'SectionNumber'),
        (short, 'Type'),
        (short, 'StorageClassAndAuxSymbolCount'),
    ]

class CodeViewChunk(pstruct.type):
    _fields_ = [
        (int, 'Header'),
        (int, 'Size'),
    ]

class CodeViewSymbolHeader(pstruct.type):
    _fields_ = [
        (short, 'Bytes'),
        (short, 'Magic'),
    ]

class CodeViewProc(pstruct.type):
    _fields_ = [
        (short, 'Bytes'),
        (short, 'Magic'),
    ]

class CodeViewProcSize(pstruct.type):
    _fields_ = [
        (int, 'Size'),
    ]

class CodeViewProcSection(pstruct.type):
    _fields_ = [
        (int, 'SectionRelative'),
        (short, 'SectionIndex'),
    ]

class CodeViewProcTerm(pstruct.type):
    _fields_ = [
        (int, 'Magic'),
    ]

class CodeViewProcEnd(pstruct.type):
    _fields_ = [
        (int, 'Magic'),
    ]

class CodeViewLocal(pstruct.type):
    _fields_ = [
        (int, 'TypeIndex'),
        (short, 'Flags'),
    ]

class CodeViewRegisterRange(pstruct.type):
    _fields_ = [
        (short, 'Register'),
        (short, 'Flags'),
        (int, 'BasePointerOffset'),
        (int, 'OffsetStartCode'),
        (short, 'SectionIndexStartCode'),
        (short, 'RangeCode'),
    ]

class CodeViewRegister(pstruct.type):
    _fields_ = [
        (short, 'Register'),
        (short, 'NoName'),
        (int, 'OffsetStartCode'),
        (short, 'SectionIndexStartCode'),
        (short, 'RangeCode'),
    ]

class CodeViewLineInfoRaw(pstruct.type):
    _fields_ = [
        (int, 'FunctionOffset'),
        (int, 'FunctionIndex'),
        (int, 'FunctionSize'),
        (int, 'SourceFileOffset'),
        (int, 'NumPairs'),
        (int, 'Size'),
    ]

class CodeViewLinePair(pstruct.type):
    _fields_ = [
        (int, 'Offset'),
        (int, 'Line'),
    ]

class CodeViewLineInfo(pstruct.type):
    def __LinePairs(self):
        res = self['Raw'].li
        return dyn.array(CodeViewLinePair, res['NumPairs'].int())
    _fields_ = [
        (CodeViewLineInfoRaw, 'Raw'),
        (__LinePairs, 'LinePairs'),
    ]

###
class WriteMagic(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=27), 'magicstring'),
        (char, 'Magic?'),
        (dyn.clone(pstr.string, length=2), 'DS'),
        (dyn.block(3), 'Null magic'),
    ]
    def alloc(self, **fields):
        res = super(WriteMagic, self).alloc(**fields)
        if 'magicstring' not in fields:
            res['magicstring'].set('Microsoft C/C++ MSF 7.00\r\n')
        if 'Magic?' not in fields:
            res['Magic?'].set(26)
        if 'DS' not in fields:
            res['DS'].set('DS')
        return res

class WriteSuperBlock(pstruct.type):
    _fields_ = [
        (int, 'BlockSize'),
        (int, 'Free block'),
        (int, 'BlockCount'),
        (int, 'DirectoryStream.Length'),
        (int, 'Unknown'),
        (int, 'DirectoryHints.Blocks.Head'),
    ]

class WriteDirectoryHint(pstruct.type):
    _fields_ = [
        (int, 'hack'),  # umm, what
    ]

class WriteDirectory(pstruct.type):
    class _DirectoryEntry(pint.enum):
        _values_ = [
            ('OldMSFDirectory', 0),
            ('PDB', 1),
            ('TPI', 2),
            ('DBI', 3),
            ('IPI', 4),
            ('Globals', 5),
            ('Publics', 6),
            ('Symbols', 7),
        ]

    _fields_ = [
        (int, 'CountAdditionalStreams'),
        (lambda self: dyn.array(self['CountAdditionalStreams'].li.int()), 'Length'),
        (lambda self: dyn.array(self['CountAdditionalStreams'].li.int()), 'Blocks'),
    ]

class WritePDBInfoStream(pstruct.type):
    class slashnames(pstruct.type):
        _fields_ = [
            (int, 'length'),
            (lambda self: dyn.clone(pstr.string, length=self['length'].li.int()), 'string'),
        ]
        def alloc(self, **fields):
            res = super(WritePDBInfoStream, self).alloc(**fields)
            return res if 'length' in fields else res.set(length=res['string'].size())
    _fields_ = [
        (int, 'version'),
        (int, 'signature'),
        (int, 'age'),
        (GUID, 'GUID'),
        (slashnames, '/names'),
        (int, 'hash table size/capacity pair'),
        (int, 'one'),
        (int, 'bit vector number of dwords of data'),
        (int, 'dwords of data'),
        (int, 'bit vector of deleted data'),
        (int, 'offset of stream name'),
        (int, 'stream index of string table'),
        (int, 'VC110 signature'),
    ]
    def alloc(self, **fields):
        if '/names' not in fields:
            fields['/names'] = {'string': '/names'}
        res = super(WritePDBInfoStream, self).alloc(**fields)
        if 'version' not in fields:
            res['version'].set(20000404)
        if 'signature' not in fields:
            res['signature'].set(0)
        if 'age' not in fields:
            res['age'].set(0)
        if 'VC110 signature' not in fields:
            res['VC110 signature'].set(20091201)
        return res

class WriteTPIStream(pstruct.type):
    _fields_ = [
        (int, 'version'),
        (int, 'hardcoded magic size'),
        (int, 'Type index begin'),
        (int, 'Type index end'),
        (int, 'Type record bytes'),
        (short, 'Hash stream index'),
        (short, 'Hash aux stream index'),
        (int, 'Hash key size'),
        (int, 'Number of hash buckets'),
        (int, 'Hash value buffer offset'),
        (int, 'Hash value buffer length'),
        (int, 'Index offset buffer offset'),
        (int, 'Index offset buffer length'),
        (int, 'Hash adjustment buffer offset'),
        (int, 'Hash adjustment buffer length'),
    ]
    def alloc(self, **fields):
        res = super(WriteTPIStream, self).alloc(**fields)
        if 'version' not in fields:
            res['version'].set(20040203)
        if 'hardcoded magic size' not in fields:
            res['hardcoded magic size'].set(56)
        if 'Hash key size' not in fields:
            res['Hash key size'].set(4)
        if 'Number of hash buckets' not in fields:
            res['Number of hash buckets'].set(262143)
        return res

class WriteDBIStream(pstruct.type):
    _fields_ = [
        (int, 'signature'),
        (int, 'version'),
        (int, 'age'),
        (short, 'stream index of global symbols'),  # from PDBDirectory
        (short, 'build number'),
        (short, 'stream index of public symbols'),  # from PDBDirectory
        (short, 'PDB DLL version'),
        (short, 'stream index of symbol records'),  # from PDBDirectory
        (short, 'rebuild number of PDB DLL'),
        (int, 'ModuleSubstreamSize'),
        (int, 'SectionContributionSize'),
        (int, 'SectionMapSize'),
        (int, 'FileSubstreamSize'),
        (int, 'type server map size'),
        (int, 'index of MFC type server'),
        (int, 'DbgHeader info size'),       # 2 byte stream index times 11 valid entries in a full table
        (int, 'EC substream size'),
        (short, 'flags'),
        (short, 'machine type'),
        (int, 'pad'),
    ]
    def alloc(self, **fields):
        res = super(WriteDBIStream, self).alloc(**fields)
        if 'signature' not in fields:
            res['signature'].set(0xffffffff)
        if 'version' not in fields:
            res['version'].set(19990903)
        if 'age' not in fields:
            res['age'].set(1)
        if 'DbgHeader info size' not in fields:
            res['DbgHeader info size'].set(2 * 11)
        if 'EC substream size' not in fields:
            res['EC substream size'].set(93)
        if 'machine type' not in fields:
            res['machine type'].set(0x8664)
        return res

class EmitDBIModule(pstruct.type):
    _fields_ = [
        (int, 'unusedheader'),
        (int, 'written'),
        (short, 'flags'),
        (short, 'stream number of debug info'),
        (int, 'SymbolSize'),
        (int, 'bytes of line number info'),
        (int, 'LinesSize'),
        (short, 'num contributing file'),
        (short, 'padding'),
        (int, 'file name offsets'),
        (int, 'name index for source file name'),
        (int, 'name index for path to compiler PDB'),
        (pstr.string, 'SourceFile'),
        (char, 'modsize'),
        (dyn.padding(4), 'padding(modsize)'),
    ]

class EmitDBISectionContributions(pstruct.type):
    _fields_ = [
        (int, 'version'),
    ]
    def alloc(self, **fields):
        res = super(EmitDBISectionContributions, self).alloc(**fields)
        if 'version' not in fields:
            res['version'].set(0xeffe0000 + 19970605)
        return res

class EmitDBISectionMapEntry(pstruct.type):
    _fields_ = [
        (short, 'flags'),
        (short, 'overlay'),
        (short, 'group'),
        (short, 'frame'),
        (short, 'name'),
        (short, 'class name'),
        (int, 'offset'),
        (int, 'length'),
    ]
    def alloc(self, **fields):
        res = super(EmitDBISectionMapEntry, self).alloc(**fields)
        if 'name' not in fields:
            res['name'].set(0xffff)
        if 'class name' not in fields:
            res['class name'].set(0xffff)
        return res

class EmitDBISectionMapEntries(pstruct.type):
    _fields_ = [
        (EmitDBISectionMapEntry, 'Head'),
        #(EmitDBISectionMapEntries, 'Next'),
    ]

class EmitDBISectionMap(pstruct.type):
    _fields_ = [
        (short, 'actual entry count'),
        (short, 'logical count'),
        (EmitDBISectionMapEntries, 'SectionHeaders'),

        # magic section (?)
        (short, 'flags'),
        (short, 'overlay'),
        (short, 'group'),
        (short, 'frame'),
        (short, 'name'),
        (short, 'class name'),
        (int, 'offset'),
        (int, 'length'),
    ]
    def alloc(self, **fields):
        res = super(EmitDBISectionMapEntry, self).alloc(**fields)
        if 'flags' not in fields:
            res['flags'].set(0x208)
        if 'frame' not in fields:
            res['frame'].set(10)
        if 'name' not in fields:
            res['name'].set(0xffff)
        if 'class name' not in fields:
            res['class name'].set(0xffff)
        if 'length' not in fields:
            res['length'].set(0xffffffff)
        return res

class EmitDBIFiles(pstruct.type):
    class filename(pstruct.type):
        _fields_ = [
            (int, 'length'),
            (lambda self: dyn.clone(pstr.string, length=self['length'].li.int()), 'string'),
        ]
        def alloc(self, **fields):
            res = super(WritePDBInfoStream, self).alloc(**fields)
            return res if 'length' in fields else res.set(length=res['string'].size())
    _fields_ = [
        (short, 'modulecount'),
        (short, 'filecount'),
        (lambda self: dyn.array(short, self['modulecount'].li.int()), 'unused'),
        (lambda self: dyn.array(short, self['modulecount'].li.int()), 'Number of files in this module'),
        (lambda self: dyn.array(int, self['modulecount'].li.int()), 'offset of file name in names buffer'),
        (filename, 'filename'),
        (dyn.padding(4), 'padding(filename)'),
    ]

class WriteDBIStrings(pstruct.type):
    _fields_ = [
        (int, 'Signature'),
        (int, 'Hash version'),
        (int, 'Bytes of string data'),
        (pstr.string, 'some name'),
        (pstr.string, 'some path'),
        (int, 'Hash count'),
        (lambda self: dyn.array(int, self['Hash count'].li.int()), 'Hash ID'),
        (int, 'Name count'),
    ]

class EmitDBIOptionalHeader(pstruct.type):
    _fields_ = [
        (int, 'FPO'),
        (int, 'Exception'),
        (int, 'Fixup'),
        (int, 'OmapToSrc'),
        (int, 'OmapFromSrc'),
        (int, 'SectionHdr'),
        (int, 'TokenRidMap'),
        (int, 'Xdata'),
        (int, 'Pdata'),
        (int, 'NewFPO'),
        (int, 'SectionHdrOrig'),
    ]

class WriteIPIStream(pstruct.type):
    _fields_ = [
        (int, 'version'),
        (int, 'hardcoded magic size'),
        (int, 'Type Index begin'),
        (int, 'Type Index end'),
        (short, 'Hash stream index'),
        (short, 'Hash aux stream index'),
        (int, 'Hash key size'),
        (int, 'Number of hash buckets'),
        (int, 'Hash value buffer offset'),
        (int, 'Hash value buffer length'),
        (int, 'Index offset buffer offset'),
        (int, 'Index offset buffer length'),
        (int, 'Hash adjustment buffer offset'),
        (int, 'Hash adjustment buffer length'),
    ]
    def alloc(self, **fields):
        res = super(WriteTPIStream, self).alloc(**fields)
        if 'version' not in fields:
            res['version'].set(20040203)
        if 'hardcoded magic size' not in fields:
            res['hardcoded magic size'].set(56)
        if 'Hash key size' not in fields:
            res['Hash key size'].set(4)
        if 'Number of hash buckets' not in fields:
            res['Number of hash buckets'].set(262143)
        return res

class WriteUnknown(pstruct.type):
    _fields_ = [(int, 'unknown')]

class WriteGlobalsStream(WriteUnknown): pass
class WritePublicsStream(WriteUnknown): pass
class WritePublicSymbolRecordsStream(WriteUnknown): pass
class WriteDBIModuleSymbols(WriteUnknown): pass
class WritePDBStrings(WriteUnknown): pass
class WritePDBSectionHeaders(WriteUnknown): pass

class File(pstruct.type):
    def __WriteBlockMap(self):
        res = self['SuperBlock'].li
        ffsize = res['BlockSize'].int()
        return dyn.padding(ffsize)
    def __PadToBeginningOfBlock(self):
        res = self['SuperBlock'].li
        blockindex, blocksize = (res[fld] for fld in ['DirectoryHints.Blocks.Head', 'BlockSize'])
        return dyn.padding(blockindex.int() * blocksize.int())
    def __PadGarbageToBeginningOfBlock(self):
        res = self['SuperBlock'].li
        blockindex, blocksize = (res[fld] for fld in ['DirectoryHints.Blocks.Head', 'BlockSize'])
        return dyn.padding(blockindex.int() * blocksize.int())

    _fields_ = [
        (WriteMagic, 'Magic'),
        (WriteSuperBlock, 'SuperBlock'),
        (__WriteBlockMap, 'BlockMap'),
        (__PadToBeginningOfBlock, 'padding(DirectoryHint)'),
        (WriteDirectoryHint, 'DirectoryHint'),
        (__PadToBeginningOfBlock, 'padding(Directory)'),
        (WriteDirectory, 'Directory'),
        (__PadToBeginningOfBlock, 'padding(PDBInfoStream)'),
        (WritePDBInfoStream, 'PDBInfoStream'),
        (__PadGarbageToBeginningOfBlock, 'padding(TPIStream)'),
        (WriteTPIStream, 'TPIStream'),
        (__PadGarbageToBeginningOfBlock, 'padding(DPIStream)'),
        (WriteDBIStream, 'DBIStream'),
        (__PadGarbageToBeginningOfBlock, 'padding(IPIStream)'),
        (WriteIPIStream, 'IPIStream'),

        (__PadGarbageToBeginningOfBlock, 'padding(GlobalStream)'),
        (WriteGlobalsStream, 'GlobalStream'),
        (__PadGarbageToBeginningOfBlock, 'padding(PublicsStream)'),
        (WritePublicsStream, 'PublicsStream'),
        (__PadGarbageToBeginningOfBlock, 'padding(PublicSymbolRecordsStream)'),
        (WritePublicSymbolRecordsStream, 'PublicSymbolRecordsStream'),
        (__PadToBeginningOfBlock, 'padding(DBIModuleSymbols)'),
        (WriteDBIModuleSymbols, 'DBIModuleSymbols'),
        (__PadGarbageToBeginningOfBlock, 'padding(PDBStrings)'),
        (WritePDBStrings, 'PDBStrings'),
        (__PadToBeginningOfBlock, 'padding(PDBSectionHeaders)'),
        (WritePDBSectionHeaders, 'PDBSectionHeaders'),
        (__PadGarbageToBeginningOfBlock, 'padding(end of file)'),
    ]
    def alloc(self, **fields):
        res = super(File, self).alloc(**fields)
        if 'BlockMap' not in fields:
            res['BlockMap'].set(b'\xff' * res['BlockMap'].size())
        return res

if __name__ == '__main__':
    import sys, os, ptypes
    #pdbpath = ['tmp', 'ida', 'WPDShServiceObj.pdb', '82295FF85B7242C3A5F218DD2BB2BAA11', 'WPDShServiceObj.pdb']
    #source = ptypes.prov.file(os.path.join(os.path.expanduser('~'), *pdbpath), 'rb')
    if len(sys.argv) != 2:
        raise FileNotFoundError(sys.argv)
    source = ptypes.prov.file(sys.argv[1], 'rb')
    z = MSF(source=source).l
    assert(z['szmagic'].str().startswith('Microsoft C/C++'))
    assert(z['szmagic'].Version() == 7.)
    assert(z['szmagic']['CRLF'].str() == '\r\n')
    assert(z['szmagic']['1A'].str() == '\x1a')
    assert(z['szmagic']['DSJG'].str() == 'DS')
    assert(z['szmagic']['DSJG'].str() == 'DS')
    assert(z['szmagic'].str() == 'Microsoft C/C++ MSF 7.00\r\n\x1a\x44\x53')
    #assert(z['hdr'].int() == 0x1000), # not sure what this was for

    if False:
        a = MSF().a
        assert(a['szmagic'].str() == 'Microsoft C/C++ MSF 7.00\r\n\x1a\x44\x53')
        print(a)
        print(a['hdr'])

        print(a['hdr']['sist'])
        for item in a['mpspnpn']:
            print(item)

        print(a['Fpm'][0].hexdump())
        print(a.size())
        #for item in a['mac']:
        #    print(item)
