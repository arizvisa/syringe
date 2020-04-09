import logging
import functools, itertools, types, builtins, operator, math, six

import ptypes
from ptypes import *

from . import stream as jpegstream

intofdata = lambda data: six.moves.reduce(lambda t, c: t * 256 | c, bytearray(data), 0)
dataofint = lambda integer: ((integer == 0) and b'\0') or (dataofint(integer // 256).lstrip(b'\0') + six.int2byte(integer % 256))

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

class StreamMarker(jpegstream.StreamMarker):
    Type, Table = MarkerType, Marker

class DecodedStream(jpegstream.DecodedStream):
    _marker_ = StreamMarker

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
        if isinstance(self.source, ptypes.prov.bounded):
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
        res = Boxes.withdefault(hdr.Type(), type=hdr.Type())
        if issubclass(res, ptype.block):
            return dyn.clone(res, length=cb)
        elif issubclass(res, ptype.encoded_t):
            return dyn.clone(res, _value_=dyn.clone(ptype.block, length=cb))
        return dyn.clone(res, blocksize=lambda s, length=cb: length)

    def __padding(self):
        hdr = self['header'].li
        cb = hdr.DataLength()
        return dyn.block(max((0,cb - self['data'].li.size())))

    _fields_ = [
        (BoxHeader, 'header'),
        (__data, 'data'),
        (__padding, 'padding'),
    ]

class SuperBox(parray.block):
    _object_ = Box

class File(parray.infinite):
    _object_ = Box

### Box types
@Boxes.define
class Signature(pstr.string):
    type = b'\x6a\x50\x20\x20'
    length = 4
    @classmethod
    def default(cls):
        return cls().set(b'\x0d\x0a\x87\x0a')
    def valid(self):
        return self.serialize() == self.default().serialize()
    def properties(self):
        res = super(Signature, self).properties()
        res['valid'] = self.valid()
        return res

@Boxes.define
class FileType(pstruct.type):
    type = b'\x66\x74\x79\x70'
    class Identifier(pstr.string): length = 4
    _fields_ = [
        (Identifier, 'BR'),
        (u32, 'MinV'),
        (Identifier, 'CL'),
    ]

@Boxes.define
class Jp2Header(SuperBox):
    type = b'\x6a\x70\x32\x68'

@Boxes.define
class ImageHeader(pstruct.type):
    type = b'\x69\x68\x64\x72'
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
    type = b'\x62\x70\x63\x63'
    _fields_ = [
        (1, 'Signed'),
        (7, 'BitDepth'),
    ]

@Boxes.define
class Palette(pstruct.type):
    type = b'\x70\x63\x6c\x72'
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
    type = b'\x63\x6d\x61\x70'
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
    type = b'\x63\x64\x65\x66'

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
    type = b'\x63\x64\x65\x66'

@Boxes.define
class CaptureResolution(pstruct.type):
    type = b'\x72\x65\x73\x63'
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
    type = b'\x72\x65\x73\x64'
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
    type = b'\x63\x6f\x6c\x72'
    def __PROFILE(self):
        try:
            hdr = self.getparent(Box)['header'].li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ['METH', 'PREC', 'APPROX', 'EnumCS']
        return dyn.block(max((0, hdr.DataLength() - sum(self[fld].li.size() for fld in fields))))

    _fields_ = [
        (u8, 'METH'),
        (u8, 'PREC'),
        (u8, 'APPROX'),
        (lambda s: u0 if s['METH'].li.int() == 2 else u32, 'EnumCS'),
        (__PROFILE, 'PROFILE'),
    ]

@Boxes.define
class ContiguousCodeStream(jpegstream.Stream):
    type = b'\x6a\x70\x32\x63'
    _object_ = DecodedStream

    def isDelimiter(self, marker):
        return intofdata(marker) in {0xff93, 0xffd9, 0xff92}

@Boxes.define
class IntellectualProperty(ptype.block):
    type = b'\x6a\x70\x32\x69'

@Boxes.define
class XML(ptype.block):
    type = b'\x78\x6d\x6c\x20'

@Boxes.define
class UUID(pstruct.type):
    type = b'\x75\x75\x69\x64'
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
    type = b'\x75\x69\x6e\x66'

class UUID(pstruct.type):
    class _time_hi_and_version(pbinary.struct):
        _fields_ = [
            (4, 'version'),
            (12, 'time_hi'),
        ]
        def summary(self):
            return "{:04x}".format(self.int())

    class _clock_seq_hi_and_res(pbinary.struct):
        _fields_ = [
            (3, 'variant'),
            (13, 'clock_seq'),
        ]
        def summary(self):
            return "{:04x}".format(self.int())

    class _node(parray.type):
        length, _object_ = 6, u8
        def summary(self):
            iterable = (item.int() for item in self)
            return ''.join(map("{:02x}".format, iterable))

    _fields_ = [
        (u32, 'time_low'),
        (u16, 'time_mid'),
        (_time_hi_and_version, 'time_hi_and_version'),
        (_clock_seq_hi_and_res, 'clock_seq_hi_and_res'),
        (_node, 'node'),
    ]

    def summary(self, **options):
        fmt = "urn:uuid:{:s}".format
        res = self.str() if self.initializedQ() else '????????-????-????-????-????????????'
        return fmt(res)

    def str(self):
        d1 = '{:08x}'.format(self['time_low'].int())
        d2 = '{:04x}'.format(self['time_mid'].int())
        d3 = '{:04x}'.format(self['time_hi_and_version'].int())
        d4 = '{:04x}'.format(self['clock_seq_hi_and_res'].int())
        iterable = (item.int() for item in self['node'])
        d5 = ''.join(map('{:02x}'.format, iterable))
        return '-'.join([d1, d2, d3, d4, d5])

@Boxes.define
class UUIDList(pstruct.type):
    type = b'\x75\x63\x73\x74'
    _fields_ = [
        (u16, 'NU'),
        (lambda self: dyn.array(UUID, self['NU'].li.int()), 'UUID'),
    ]

@Boxes.define
class URL(pstruct.type):
    type = b'\x75\x72\x6c\x20'
    def __LOC(self):
        try:
            hdr = self.getparent(Box)['header'].li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ['VERS', 'FLAG']
        return dyn.clone(pstr.string, length=hdr.DataLength() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u8, 'VERS'),
        (dyn.clone(u0, length=3), 'FLAG'),
        (__LOC, 'LOC'),
    ]

### Update enumeration with any defined Box types
BoxType._values_ = [(t.__name__, intofdata(key)) for key, t in six.viewitems(Boxes.cache)]

### Marker types
@Marker.define
class SOC(ptype.block):
    pass

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
class SOD(ptype.block):
    pass

@Marker.define
class EOC(ptype.block):
    pass

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

    def NumberOfTiles(self):
        width = self['Xsiz'].int() - self['XOsiz'].int()
        height = self['Ysiz'].int() - self['YOsiz'].int()
        X, Y = (item / self[fld].int() for fld, item in zip(['XTsiz', 'YTsiz'], [width, height]))
        return six.moves.reduce(operator.mul, map(math.ceil, [X, Y]))

class Scod(pbinary.flags):
    _fields_ = [
        (5, 'Reserved'),
        (1, 'EPHUsed'),
        (1, 'SOPUsed'),
        (1, 'Entropy'),
    ]

class SGcod(pstruct.type):
    class _Progression_order(pint.enum, u8):
        _values_ = [
            ('Layer-resolution level-component-position', 0),
            ('Resolution level-layer-component-position', 1),
            ('Resolution level-position-component-layer', 2),
            ('Position-component-resolution level-layer', 3),
            ('Component-position-resolution level-layer', 4),
        ]
    _fields_ = [
        (_Progression_order, 'Progression order'),
        (u16, 'Number of layers'),
        (u8, 'Multiple component transformation'),
    ]

class Precinct(pbinary.struct):
    _fields_ = [
        (4, 'PPy'),
        (4, 'PPx'),
    ]

class SPcod(pstruct.type):
    _fields_ = [
        (u8, 'Number of decomposition levels'),
        (u8, 'Code-block width'),
        (u8, 'Code-block height'),
        (u8, 'Code-block style'),
        (u8, 'Transformation'),
    ]

@Marker.define
class COD(pstruct.type):
    def __missed(self):
        length, fields = self['Lcod'].li, ['Lcod', 'Scod', 'SGcod', 'SPcod']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    def __LL(self):
        scod, spcod = (self[fld].li for fld in ['Scod', 'SPcod'])
        count = (1 + spcod['Number of decomposition levels'].int()) if scod['Entropy'] else 0
        return dyn.array(Precinct, count)

    _fields_ = [
        (u16, 'Lcod'),
        (Scod, 'Scod'),
        (SGcod, 'SGcod'),
        (SPcod, 'SPcod'),
        (__LL, 'LL'),
    ]

class Scoc(pbinary.flags):
    _fields_ = [
        (7, 'Reserved'),
        (1, 'Entropy'),
    ]

class SPcoc(SPcod): pass

@Marker.define
class COC(pstruct.type):
    def __Ccoc(self):
        stream = self.getparent(stream.DecodedStream)
        try:
            index = next(i for i, item in enumerate(stream) if isinstance(item['Value'], SIZ))
        except StopIteration:
            logging.warn("Unable to locate SIZ marker!")
            return u8
        Csiz = stream[index]['Value']['Csiz']
        return u8 if Csiz.int() < 257 else u16

    def __LL(self):
        scod, spcod = (self[fld].li for fld in ['Scoc', 'SPcoc'])
        count = (1 + spcod['Number of decomposition levels'].int()) if scod['Entropy'] else 0
        return dyn.array(Precinct, count)

    _fields_ = [
        (u16, 'Lcoc'),
        (__Ccoc, 'Ccoc'),
        (Scoc, 'Scoc'),
        (SPcoc, 'SPcoc'),
        (__LL, 'LL'),
    ]

@Marker.define
class RGN(pstruct.type):
    def __Crgn(self):
        Csiz = 0
        return u8 if Csiz < 257 else u16

    def __SPrgn(self):
        length, fields = self['Lrgn'].li, ['Lrgn', 'Crgn', 'Srgn']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lrgn'),
        (__Crgn, 'Crgn'),
        (u8, 'Srgn'),
        (__SPrgn, 'SPrgn'),
    ]

@Marker.define
class QCD(pstruct.type):
    def __SPqcd(self):
        length, fields = self['Lqcd'].li, ['Lqcd', 'Sqcd']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

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
        length, fields = self['Lqcc'].li, ['Lqcc', 'Cqcc', 'Sqcc']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

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
        length, fields = self['Lpod'].li, ['Lpod', 'RSpod', 'CSpod', 'LYEpod', 'REpod', 'CEpod', 'Ppod']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

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
        length, fields = self['Ltlm'].li, ['Ltlm', 'Ztlm', 'Stlm', 'Ttlm', 'Ptlm']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

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
        length, fields = self['Lplm'].li, ['Lplm', 'Zplm', 'Nplm']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lplm'),
        (u8, 'Zplm'),
        (u8, 'Nplm'),
        (__missed, 'missed'),
    ]

@Marker.define
class PLT(pstruct.type):
    def __Iplt(self):
        length, fields = self['Lplt'].li, ['Lplt', 'Zplt']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lplt'),
        (u8, 'Zplt'),
        (__Iplt, 'Iplt'),
    ]

@Marker.define
class PPM(pstruct.type):
    def __Ippm(self):
        length, fields = self['Lppm'].li, ['Lppm', 'Zppm', 'Nppm']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lppm'),
        (u8, 'Zppm'),
        (u32, 'Nppm'),
        (__Ippm, 'Ippm'),
    ]

@Marker.define
class PPT(pstruct.type):
    def __Ippt(self):
        length, fields = self['Lppt'].li, ['Lppt', 'Zppt']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lppt'),
        (u8, 'Zppt'),
        (__Ippt, 'Ippt'),
    ]

@Marker.define
class SOP(pstruct.type):
    def __missed(self):
        length, fields = self['Lsop'].li, ['Lsop', 'Nsop']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lsop'),
        (u16, 'Nsop'),
        (__missed, 'missed'),
    ]

@Marker.define
class EPH(ptype.block):
    pass

@Marker.define
class COM(pstruct.type):
    def __content(self):
        length, fields = self['Lcme'].li, ['Lcme', 'Rcme']
        return dyn.clone(pstr.string, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lcme'),
        (u16, 'Rcme'),
        (__content, 'Ccme'),
    ]

if __name__ == '__main__':
    import ptypes, image.jpeg.jp2 as jp2
    ptypes.setsource(ptypes.prov.file('logo.jp2', mode='r'))

    z = jp2.File().l

    print(z[3]['data'].decode())

    a = ptype.block(offset=z.getoffset()+z.size(), length=0x100).l
    print(a.hexdump())
