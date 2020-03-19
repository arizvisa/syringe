import logging
import functools,operator,itertools

import ptypes
from ptypes import *

from . import stream as jpegstream

intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, data), 0)
dataofint = lambda integer: ((integer == 0) and '\x00') or (dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### primitive types
class u0(pint.uint_t): pass
class s0(pint.sint_t): pass
class u8(pint.uint8_t): pass
class s8(pint.sint8_t): pass
class u16(pint.uint16_t): pass
class s16(pint.sint16_t): pass
class u32(pint.uint32_t): pass
class s32(pint.sint32_t): pass
class u64(pint.uint64_t): pass
class s64(pint.sint64_t): pass

### JPEG2k Markers
class Marker(jpegstream.Marker):
    attribute, cache = '__name__', {}
    Table = [
        ('SOC', dataofint(0xff4f)),
        ('SOT', dataofint(0xff90)),
        ('SOD', dataofint(0xff93)),
        ('EOC', dataofint(0xffd9)),
        ('SIZ', dataofint(0xff51)),
        ('COD', dataofint(0xff52)),
        ('COC', dataofint(0xff53)),
        ('RGN', dataofint(0xff5e)),
        ('QCD', dataofint(0xff5c)),
        ('QCC', dataofint(0xff5d)),
        ('POC', dataofint(0xff5f)),
        ('TLM', dataofint(0xff55)),
        ('PLM', dataofint(0xff57)),
        ('PLT', dataofint(0xff58)),
        ('PPM', dataofint(0xff60)),
        ('PPT', dataofint(0xff61)),
        ('SOP', dataofint(0xff91)),
        ('EPH', dataofint(0xff92)),
        ('CRG', dataofint(0xff63)),
        ('COM', dataofint(0xff64)),
        ('CBD', dataofint(0xff78)),
        ('MCC', dataofint(0xff75)),
        ('MCT', dataofint(0xff74)),
        ('MCO', dataofint(0xff77)),
    ]

class MarkerType(jpegstream.MarkerType): pass
MarkerType._values_ = [(name, intofdata(data)) for name, data in Marker.Table]

class MarkerStream(jpegstream.MarkerStream):
    Type, Table = MarkerType, Marker

### enumerations
class Boxes(ptype.definition): cache = {}
class BoxType(pint.enum, u32): pass

### JP2 containers
class BoxHeader(pstruct.type):
    def __boxLengthExtended(self):
        res = self['boxLength'].li.int()
        if res == 1:
            return u64
        return u0
    _fields_ = [
        (u32, 'boxLength'),
        (BoxType, 'boxType'),
        (__boxLengthExtended, 'boxLengthExt'),
    ]
    def Type(self):
        return self['boxType'].serialize()

    def Length(self):
        res = self['boxLength'].int()
        if res:
            return self['boxLengthExt'].int() if res == 1 else res
        if isinstance(self.source, ptypes.prov.filebase):
            return self.source.size() - self.getoffset()

        cls = self.__class__
        logging.info("{:s}.Length : Field `boxLength` is 0 and source is unbounded for `boxType`. : {!r}".format('.'.join((__name__, cls.__name__)), self.Type()))
        return 8

    def DataLength(self):
        return self.Length() - self.size()

    def summary(self):
        boxType = self['boxType']
        boxLength = self.Length()
        return "boxType={boxType:s} : boxLength={boxLength:#x} ({boxLength:d})".format(boxType = boxType.summary(), boxLength = boxLength)

class Box(pstruct.type):
    def __data(self):
        hdr = self['header'].li
        cb = hdr.DataLength()
        res = Boxes.withdefault(hdr.Type(), type=hdr.Type(), length=cb)
        return dyn.clone(res, blocksize=lambda s, cb=cb: cb) if issubclass(res, (ptype.block, parray.block)) else res

    def __padding(self):
        hdr = self['header'].li
        cb = hdr.DataLength()
        return dyn.block(max((0,cb - self['data'].li.size())))

    _fields_ = [
        (BoxHeader, 'header'),
        (__data, 'data'),
        (__padding, 'padding'),
    ]

class SuperBox(parray.block): _object_ = Box

class File(parray.infinite): _object_ = Box

### Box types
@Boxes.define
class Signature(pstr.string):
    type = '\x6a\x50\x20\x20'
    length = 4
    @classmethod
    def default(cls):
        return cls().set('\x0d\x0a\x87\x0a')
    def valid(self):
        return self.serialize() == self.default().serialize()
    def properties(self):
        res = super(Signature, self).properties()
        res['valid'] = self.valid()
        return res

@Boxes.define
class FileType(pstruct.type):
    type = '\x66\x74\x79\x70'
    class Identifier(pstr.string): length = 4
    _fields_ = [
        (Identifier, 'BR'),
        (u32, 'MinV'),
        (Identifier, 'CL'),
    ]

@Boxes.define
class Jp2Header(SuperBox):
    type = '\x6a\x70\x32\x68'

@Boxes.define
class ImageHeader(pstruct.type):
    type = '\x69\x68\x64\x72'
    _fields_ = [
        (u32, 'HEIGHT'),
        (u32, 'WIDTH'),
        (u16, 'NC'),
        (u8, 'BPC'),
        (u8, 'C'),
        (u8, 'UnkC'),
        (u8, 'IPR'),
    ]

@Boxes.define
class BitsPerComponent(pbinary.struct):
    type = '\x62\x70\x63\x63'
    _fields_ = [
        (1, 'Signed'),
        (7, 'BitDepth'),
    ]

@Boxes.define
class Palette(pstruct.type):
    type = '\x70\x63\x6c\x72'
    class _B(pbinary.struct):
        _fields_ = [
            (1, 'Signed'),
            (7, 'BitDepth'),
        ]

    def __C(self):
        res = self['NPC'].li.int()
        return dyn.block(res * self['NE'].li.int())

    _fields_ = [
        (u16, 'NE'),
        (u8, 'NPC'),
        (_B, 'B'),
        (__C, 'C'),
    ]

@Boxes.define
class ComponentMapping(parray.block):
    type = '\x63\x6d\x61\x70'
    class Component(pstruct.type):
        class MTYP(pint.enum, u8):
            _values_ = [
                ('DirectUse', 0),
                ('PaletteMapping', 1),
            ]
        _fields_ = [
            (u16, 'CMP'),
            (MTYP, 'MTYP'),
            (u8, 'PCOL'),
        ]
    _object_ = Component

@Boxes.define
class ChannelDefinition(parray.block):
    type = '\x63\x64\x65\x66'

    class Definition(pstruct.type):
        class Typ(pint.enum, u16):
            _values_ = [
                ('Color', 0),
                ('Opacity', 1),
                ('PreMultiplyOpacity', 2),
                ('Unspecified', 65535),
            ]
        class Assoc(pint.enum, u16):
            _values_ = [
                ('Whole', 0),
                ('Unassociated', 65535),
            ]
        _fields_ = [
            (u16, 'N'),
            (u16, 'Cn'),
            (Typ, 'Typ'),
            (Assoc, 'Assoc'),
        ]
    _object_ = Definition

@Boxes.define
class Resolution(SuperBox):
    type = '\x63\x64\x65\x66'

@Boxes.define
class CaptureResolution(pstruct.type):
    type = '\x72\x65\x73\x63'
    _fields_ = [
        (u16, 'VRcN'),
        (u16, 'VRcD'),
        (u16, 'HRcN'),
        (u16, 'HRcD'),
        (u8, 'VRcE'),
        (u8, 'HRcE'),
    ]

@Boxes.define
class DefauiltDisplayResolution(pstruct.type):
    type = '\x72\x65\x73\x64'
    _fields_ = [
        (u16, 'VRdN'),
        (u16, 'VRdD'),
        (u16, 'HRdN'),
        (u16, 'HRdD'),
        (u8, 'VRdE'),
        (u8, 'HRdE'),
    ]

@Boxes.define
class ColourSpecification(pstruct.type):
    type = '\x63\x6f\x6c\x72'
    def __PROFILE(self):
        try:
            hdr = self.getparent(Box)['header'].li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ('METH','PREC','APPROX','EnumCS')

        res = [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, hdr.DataLength() - cb)))

    _fields_ = [
        (u8, 'METH'),
        (u8, 'PREC'),
        (u8, 'APPROX'),
        (lambda s: u0 if s['METH'].li.int() == 2 else u32, 'EnumCS'),
        (__PROFILE, 'PROFILE'),
    ]

@Boxes.define
class ContiguousCodeStream(jpegstream.Stream):
    type = '\x6a\x70\x32\x63'

    _object_ = dyn.clone(jpegstream.DecodedStream, _object_=MarkerStream)

@Boxes.define
class IntellectualProperty(ptype.block):
    type = '\x6a\x70\x32\x69'

@Boxes.define
class XML(ptype.block):
    type = '\x78\x6d\x6c\x20'

@Boxes.define
class UUID(pstruct.type):
    type = '\x75\x75\x69\x64'
    def __DATA(self):
        try:
            hdr = self.getparent(Box)['header'].li
        except ptypes.error.NotFoundError:
            return dyn.block(0)
        return dyn.block(hdr.DataLength() - self['ID'].li.size())

    _fields_ = [
        (dyn.block(16), 'ID'),
        (__DATA, 'DATA'),
    ]

@Boxes.define
class UUIDInfo(SuperBox):
    type = '\x75\x69\x6e\x66'

@Boxes.define
class UUIDList(pstruct.type):
    type = '\x75\x63\x73\x74'
    _fields_ = []

@Boxes.define
class URL(pstruct.type):
    type = '\x75\x72\x6c\x20'
    def __LOC(self):
        try:
            hdr = self.getparent(Box)['header'].li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ('VERS','FLAG')

        res = [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.clone(pstr.string, length=hdr.DataLength() - cb)

    _fields_ = [
        (u8, 'VERS'),
        (dyn.clone(pint.uint_t, length=3), 'FLAG'),
        (__LOC, 'LOC'),
    ]

### Update enumeration with any defined Box types
BoxType._values_ = [(t.__name__, intofdata(key)) for key, t in Boxes.cache.viewitems()]

### Marker types
@Marker.define
class SOC(pstruct.type):
    _fields_ = []

@Marker.define
class SOT(pstruct.type):
    _fields_ = [
        (u16, 'Lsot'),
        (u16, 'Isot'),
        (u32, 'Psot'),
        (u8, 'TPsot'),
        (u8, 'TNsot'),
    ]

@Marker.define
class SOD(pstruct.type):
    _fields_ = []

@Marker.define
class EOC(pstruct.type):
    _fields_ = []

@Marker.define
class SIZ(pstruct.type):
    class C(pstruct.type):
        class Ssiz(pbinary.struct):
            _fields_ = [
                (1, 'Signed'),
                (7, 'Components'),
            ]
        _fields_ = [
            (Ssiz, 'Ssiz'),
            (u8, 'XRsiz'),
            (u8, 'YRsiz'),
        ]
    _fields_ = [
        (u16, 'Lsiz'),
        (u16, 'Rsiz'),
        (u32, 'Xsiz'),
        (u32, 'Ysiz'),
        (u32, 'XOsiz'),
        (u32, 'YOsiz'),
        (u32, 'XTsiz'),
        (u32, 'YTsiz'),
        (u32, 'XTOsiz'),
        (u32, 'YTOsiz'),
        (u16, 'Csiz'),
        (lambda s: dyn.array(SIZ.C, s['Csiz'].li.int()), 'C'),
    ]

@Marker.define
class COD(pstruct.type):
    class Scod(pbinary.struct):
        _fields_ = [
            (5, 'Entropy1'),
            (1, 'EPHUsed'),
            (1, 'SOPUsed'),
            (1, 'Entropy2'),
        ]
    class SPcod(pstruct.type):
        class CodeBlock(pstruct.type):
            _fields_ = [
                (u8, 'numresolutions'),
                (u8, 'Code-block size width'),
                (u8, 'Code-block size height'),
                (u8, 'Code-block style'),
                (u8, 'Transform'),
                (u8, 'Multiple component transform'),
                #(ptype.block, 'Packet partition size'),
            ]

        _fields_ = [
            (u8, 'Progression order'),
            (u16, 'Number of layers'),
            (lambda s: dyn.array(s.CodeBlock, s['Number of layers'].li.int()), 'Layers'),
        ]

    def __missed(self):
        length, fields = self['Lcod'].li, ('Scod','Spcod')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lcod'),
        (Scod, 'Scod'),
        (SPcod, 'SPcod'),
        (__missed, 'missed'),
    ]

@Marker.define
class COC(pstruct.type):
    def __Ccoc(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __SPcoc(self):
        length, fields = self['Lcoc'].li, ('Ccoc','Scoc')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lcoc'),
        (__Ccoc, 'Ccoc'),
        (u8, 'Scoc'),
        (__SPcoc, 'SPcoc'),
    ]

@Marker.define
class RGN(pstruct.type):
    def __Crgn(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __SPrgn(self):
        length, fields = self['Lrgn'].li, ('Crgn','Srgn')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lrgn'),
        (__Crgn, 'Crgn'),
        (u8, 'Srgn'),
        (__SPrgn, 'SPrgn'),
    ]

@Marker.define
class QCD(pstruct.type):
    def __SPqcd(self):
        length, fields = self['Lqcd'].li, ('Sqcd',)

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lqcd'),
        (u8, 'Sqcd'),
        (__SPqcd, 'SPqcd'),
    ]

@Marker.define
class QCC(pstruct.type):
    def __Cqcc(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __SPqcc(self):
        length, fields = self['Lqcc'].li, ('Cqcc','Sqcc')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lqcc'),
        (__Cqcc, 'Cqcc'),
        (u8, 'Sqcc'),
        (__SPqcc, 'SPqcc'),
    ]

@Marker.define
class POC(pstruct.type):
    def __CSpod(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __CEpod(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __missed(self):
        length, fields = self['Lpod'].li, ('RSpod','CSpod','LYEpod','REpod','CEpod','Ppod')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lpod'),
        (u8, 'RSpod'),
        (__CSpod, 'CSpod'),
        (u16, 'LYEpod'),
        (u8, 'REpod'),
        (__CEpod, 'CEpod'),
        (u8, 'Ppod'),
        (__missed, 'missed'),
    ]

@Marker.define
class TLM(pstruct.type):
    def __Ttlm(self):
        ST = 0
        if ST == 0:
            return u0
        elif ST == 1:
            return u8
        elif ST == 2:
            return u16
        return u0

    def __Ptlm(self):
        ST = 0
        if ST == 0:
            return u16
        elif ST == 1:
            return u32
        return u0

    def __missed(self):
        length, fields = self['Ltlm'].li, ('Ztlm','Stlm','Ttlm','Ptlm')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Ltlm'),
        (u8, 'Ztlm'),
        (u8, 'Stlm'),
        (__Ttlm, 'Ttlm'),
        (__Ptlm, 'Ptlm'),
        (__missed, 'missed'),
    ]

@Marker.define
class PLM(pstruct.type):
    def __missed(self):
        length, fields = self['Lplm'].li, ('Zplm','Nplm')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lplm'),
        (u8, 'Zplm'),
        (u8, 'Nplm'),
        (__missed, 'missed'),
    ]

@Marker.define
class PLT(pstruct.type):
    def __Iplt(self):
        length, fields = self['Lplt'].li, ('Zplt',)

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lplt'),
        (u8, 'Zplt'),
        (__Iplt, 'Iplt'),
    ]

@Marker.define
class PPM(pstruct.type):
    def __Ippm(self):
        length, fields = self['Lppm'].li, ('Zppm','Nppm')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lppm'),
        (u8, 'Zppm'),
        (u32, 'Nppm'),
        (__Ippm, 'Ippm'),
    ]

@Marker.define
class PPT(pstruct.type):
    def __Ippt(self):
        length, fields = self['Lppt'].li, ('Zppt',)

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lppt'),
        (u8, 'Zppt'),
        (__Ippt, 'Ippt'),
    ]

@Marker.define
class SOP(pstruct.type):
    def __missing(self):
        length, fields = self['Lsop'].li, ('Nsop',)

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lsop'),
        (u16, 'Nsop'),
        (__missing, 'missing'),
    ]

@Marker.define
class EPH(pstruct.type):
    _fields_ = []

@Marker.define
class COM(pstruct.type):
    def __missing(self):
        length, fields = self['Lcme'].li, ('Rcme','Ccme')

        res = [length] + [self[n].li for n in fields]
        cb = sum(map(operator.methodcaller('size'), res))
        return dyn.block(max((0, length.int() - cb)))

    _fields_ = [
        (u16, 'Lcme'),
        (u16, 'Rcme'),
        (u8, 'Ccme'),
        (__missing, 'missing'),
    ]

if __name__ == '__main__':
    import ptypes, jp2
    ptypes.setsource(ptypes.prov.file('logo.jp2', mode='r'))

    z = jp2.File().l

    print(z[3]['data'].decode())

    a = ptype.block(offset=z.getoffset()+z.size(), length=0x100).l
    print(a.hexdump())
