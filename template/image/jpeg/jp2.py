import ptypes, logging, operator, math, six

from ptypes import *
from . import codestream, intofdata, dataofint

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
class MarkerType(codestream.MarkerType):
    _values_ = [
        ('SOC', 0xff4f),
        ('SOT', 0xff90),
        ('SOD', 0xff93),
        ('EOC', 0xffd9),
        ('SIZ', 0xff51),
        ('COD', 0xff52),
        ('COC', 0xff53),
        ('RGN', 0xff5e),
        ('QCD', 0xff5c),
        ('QCC', 0xff5d),
        ('POC', 0xff5f),
        ('TLM', 0xff55),
        ('PLM', 0xff57),
        ('PLT', 0xff58),
        ('PPM', 0xff60),
        ('PPT', 0xff61),
        ('SOP', 0xff91),
        ('EPH', 0xff92),
        ('CRG', 0xff63),
        ('COM', 0xff64),
        ('CBD', 0xff78),
        ('MCC', 0xff75),
        ('MCT', 0xff74),
        ('MCO', 0xff77),
    ]

class Marker(codestream.Marker):
    cache, table = {}, MarkerType._values_

class StreamMarker(codestream.StreamMarker):
    Type, Table = MarkerType, Marker

class DecodedStream(codestream.DecodedStream):
    Element = StreamMarker

### enumerations
class Boxes(ptype.definition): cache = {}
class BoxType(pint.enum, u32): pass

### JP2 containers
class Box(pstruct.type):
    def __boxLengthExtended(self):
        res = self['boxLength'].li
        return u64 if res.int() == 1 else u0

    def __data(self):
        t, cb = self['boxType'].li.serialize(), self.DataLength()
        res = Boxes.withdefault(t, type=t)
        if issubclass(res, ptype.block):
            return dyn.clone(res, length=cb)
        elif issubclass(res, ptype.encoded_t):
            return dyn.clone(res, _value_=dyn.clone(ptype.block, length=cb))
        return dyn.clone(res, blocksize=lambda s, length=cb: length)

    def __padding(self):
        res = self['boxData'].li
        return dyn.block(max(0, self.DataLength() - res.size()))

    _fields_ = [
        (u32, 'boxLength'),
        (BoxType, 'boxType'),
        (__boxLengthExtended, 'boxLengthExt'),
        (__data, 'boxData'),
        (__padding, 'boxPadding'),
    ]

    def alloc(self, **fields):

        # If no boxLength was specified, then set a default length so that this
        # box isn't unbounded.
        res = super(Box, self).alloc(**fields) if operator.contains(fields, 'boxLength') else super(Box, self).alloc(boxLength=1, **fields)

        # If a boxLength was provided, then that was it and we can just return
        # what we currently have
        if any(operator.contains(fields, item) for item in ['boxLength', 'boxLengthExt']):

            # Update the boxType if the user didn't specify one in the fields
            return res.set(boxType=intofdata(res['boxData'].type)) if not operator.contains(fields, 'boxType') and hasattr(res['boxData'], 'type') else res

        # If the size fits within 32-bits, then recurse with our boxLength assigned
        length = res.size() - res['boxLengthExt'].size()
        if 1 < length < 0x100000000:
            fields['boxLength'] = length
            fields['boxLengthExt'] = 0
            return self.alloc(**fields)

        # Otherwise, this is a 64-bit length, so we need to re-allocate with
        # the boxLength set to 1 so that boxLengthExt is allocated as a u64.
        fields['boxLength'] = 1
        fields['boxLengthExt'] = u64().set(length)
        return self.alloc(**fields)

    def Length(self):
        res = self['boxLength'].li
        if res.int():
            return self['boxLengthExt'].int() if res.int() == 1 else res.int()

        cls = self.__class__
        if isinstance(self.source, ptypes.prov.bounded):
            logging.warn("{:s}.Length : Found a {:s} of type {!r} with an unbounded length at {:s}.".format('.'.join((__name__, cls.__name__)), self.classname(), self['boxType'].serialize(), self.instance()))
            return self.source.size() - self.getoffset()

        logging.info("{:s}.Length : Field `boxLength` is 0 and source is unbounded for `boxType`. : {!r}".format('.'.join((__name__, cls.__name__)), self['boxType'].serialize()))
        return 8

    def DataLength(self):
        res = self.Length()
        return max(0, res - sum(self[fld].li.size() for fld in ['boxLength', 'boxType', 'boxLengthExt']))

    def summary(self):
        return "boxType={boxType:s} : boxLength={boxLength:#x} ({boxLength:d}) : {boxData!s}".format(boxType=self['boxType'].summary(), boxLength=self.Length(), boxData=self['boxData'].summary())

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
    class _C(pint.enum, u8):
        _values_ = [
            ('Uncompressed', 0),
            ('MH', 1),
            ('MR', 2),
            ('MMR', 3),
            ('JBIG', 4),
            ('JPEG', 5),
            ('JPEG-LS', 6),
            ('JPEG-2000', 7),
            ('JBIG2', 8),
            ('ANY', 9),
        ]

    class _Boolean(pint.enum, u8):
        _values_ = [
            ('no', 0),
            ('yes', 1),
        ]

    _fields_ = [
        (u32, 'HEIGHT'),
        (u32, 'WIDTH'),
        (u16, 'NC'),
        (u8, 'BPC'),
        (_C, 'C'),
        (_Boolean, 'UnkC'),
        (_Boolean, 'IPR'),
    ]

@Boxes.define
class BitsPerComponent(pbinary.blockarray):
    type = b'\x62\x70\x63\x63'

    class Component(pbinary.struct):
        _fields_ = [
            (1, 'Signed'),
            (7, 'BitDepth'),
        ]
    _object_ = Component

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

    def alloc(self, **fields):
        res = super(Palette, self).alloc(**fields)
        cb = res['C'].size()
        if operator.contains(fields, 'NE'):
            return res.set(NPC=cb // res['NE'].int())
        elif operator.contains(fields, 'NPC'):
            return res.set(NE=cb // res['NPC'].int())

        # try and figure out the least number of components
        # required to store the 'C' field
        for npc in range(cb):
            if cb % npc == 0:
                return res.set(NPC=npc, NE=cb // npc)
            continue
        return res

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
    type = b'\x72\x65\x73\x20'

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
    class _METH(pint.enum, u8):
        _values_ = [
            ('Enumerated', 1),
            ('Restricted ICC', 2),
            ('Any ICC', 3),
            ('Vendor Colour', 4),
        ]

    class _EnumCS(pint.enum, u32):
        _values_ = [
            ('Bi-level', 0),
            ('YCbCr(1)', 1),
            ('YCbCr(2)', 3),
            ('YCbCr(3)', 4),
            ('PhotoYCC', 9),
            ('CMY', 11),
            ('CMYK', 12),
            ('YCCK', 13),
            ('CIELab', 14),
            ('Bi-level(2)', 15),
            ('sRGB', 16),
            ('greyscale', 17),
            ('sYCC', 18),
            ('CIEJab', 19),
            ('e-sRGB', 20),
            ('ROMM-RGB', 21),
            ('YPbPr(1125/60)', 22),
            ('YPbPr(1150/50)', 23),
            ('e-sYCC', 24),
        ]

    def __PROFILE(self):
        try:
            hdr = self.getparent(Box).li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ['METH', 'PREC', 'APPROX', 'EnumCS']
        return dyn.block(max(0, hdr.DataLength() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (_METH, 'METH'),
        (s8, 'PREC'),
        (u8, 'APPROX'),
        (lambda self: u0 if self['METH'].li.int() == 2 else self._EnumCS, 'EnumCS'),
        (__PROFILE, 'PROFILE'),
    ]

    def alloc(self, **fields):
        res = super(ColourSpecification, self).alloc(**fields)
        return res if operator.contains(fields, 'METH') or res['EnumCS'].size() > 0 else res.set(METH=2)

@Boxes.define
class ContiguousCodeStream(codestream.Stream):
    type = b'\x6a\x70\x32\x63'
    _object_ = DecodedStream

    def StartOfDataMarkerQ(self, marker):
        return intofdata(marker) == 0xff93

    def DataMarkerQ(self, marker):
        return 0xff90 <= intofdata(marker) < 0xffff

    def EndOfDataMarkerQ(self, marker):
        return intofdata(marker) == 0xffd9

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
            hdr = self.getparent(Box).li
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

    def alloc(self, **fields):
        res = super(UUIDList, self).alloc(**fields)
        return res if operator.contains(fields, 'NU') else res.set(NU=len(res['UUID']))

@Boxes.define
class URL(pstruct.type):
    type = b'\x75\x72\x6c\x20'
    def __LOC(self):
        try:
            hdr = self.getparent(Box).li
        except ptypes.error.NotFoundError:
            return dyn.block(0)

        fields = ['VERS', 'FLAG']
        return dyn.clone(pstr.string, length=hdr.DataLength() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u8, 'VERS'),
        (dyn.clone(u0, length=3), 'FLAG'),
        (__LOC, 'LOC'),
    ]

@Boxes.define
class ReaderRequirements(pstruct.type):
    type = b'\x72\x72\x65\x71'
    class _V(pstruct.type):
        def __VM(self):
            try:
                p = self.getparent(ReaderRequirements)

            except ptypes.error.NotFoundError:
                return u0
            return dyn.clone(u0, length=p['ML'].li.int())
        _fields_ = [
            (UUID, 'VF'),
            (__VM, 'VM'),
        ]

    class _SF(pint.enum, u16):
        _values_ = [
            (1, 'Codestream contains no extensions'),
            (2, 'Contains multiple composition layers'),
            (3, 'Codestream is compressed using JPEG 2000 and requires at least a Profile 0 decoder'),
            (4, 'Codestream is compressed using JPEG 2000 and requires at least a Profile 1 decoder'),
            (5, 'Codestream is compressed using JPEG 2000'),
            (6, 'Codestream is compressed using JPEG 2000 Extensions'),
            (7, 'Codestream is compressed using DCT'),
            (8, 'Does not contain opacity'),
            (9, 'Compositing layer includes opacity channel (non-premultiplied)'),
            (10, 'Compositing layer includes premultiplied channel opacity'),
            (11, 'Compositing layer specifies opacity using a chroma-key value'),
            (12, 'Codestream is contiguous'),
            (13, 'Codestream is fragmented such that fragments are all in file and in order'),
            (14, 'Codestream is fragmented such that fragments are all in file but out of order'),
            (15, 'Codestream is fragmented such that fragments are in multiple local files'),
            (16, 'Codestream is fragmented such that fragments are across the internet'),
            (17, 'Rendered result created using compositing'),
            (18, 'Support for compositing layers is not required (reader can load a single, discrete compositing layer)'),
            (19, 'Contains multiple, discrete layers that should not be combined through either animation or compositing'),
            (20, 'Compositing layers each contain only a single codestream'),
            (21, 'Compositing layers contain multiple codestreams'),
            (22, 'All compositing layers are in the same colourspace'),
            (23, 'Compositing layers are in multiple colourspaces'),
            (24, 'Rendered result created without using animation'),
            (25, 'Animated, but first layer covers entire area and is opaque'),
            (26, 'Animated, but first layer does not cover the entire rendered result area'),
            (27, 'Animated, and no layer is reused'),
            (28, 'Animated, but layers are reused'),
            (29, 'Animated with persistent frames only'),
            (30, 'Animated with non-persistent frames'),
            (31, 'Rendered result created without using scaling'),
            (32, 'Rendered result involves scaling within a layer'),
            (33, 'Rendered result involves scaling between layers'),
            (34, 'Contains ROI metadata'),
            (35, 'Contains IPR metadata'),
            (36, 'Contains Content metadata'),
            (37, 'Contains History metadata'),
            (38, 'Contains Creation metadata'),
            (39, 'Portion of file is digitally signed in a secure method'),
            (40, 'Portion of file is checksummed'),
            (41, 'Desired Graphic Arts reproduction specified'),
            (42, 'Compositing layer uses palettized colour'),
            (43, 'Compositing layer uses Restricted ICC profile'),
            (44, 'Compositing layer uses Any ICC profile'),
            (45, 'Compositing layer uses sRGB enumerated colourspace'),
            (46, 'Compositing layer uses sRGB-grey enumerated colourspace'),
            (47, 'Compositing layer uses BiLevel 1 enumerated colourspace'),
            (48, 'Compositing layer uses BiLevel 2 enumerated colourspace'),
            (49, 'Compositing layer uses YCbCr 1 enumerated colourspace'),
            (50, 'Compositing layer uses YCbCr 2 enumerated colourspace'),
            (51, 'Compositing layer uses YCbCr 3 enumerated colourspace'),
            (52, 'Compositing layer uses PhotoYCC enumerated colourspace'),
            (53, 'Compositing layer uses YCCK enumerated colourspace'),
            (54, 'Compositing layer uses CMY enumerated colourspace'),
            (55, 'Compositing layer uses CMYK enumerated colourspace'),
            (56, 'Compositing layer uses CIELab enumerated colourspace with default parameters'),
            (57, 'Compositing layer uses CIELab enumerated colourspace with parameters'),
            (58, 'Compositing layer uses CIEJab enumerated colourspace with default parameters'),
            (59, 'Compositing layer uses CIEJab enumerated colourspace with parameters'),
            (60, 'Compositing layer uses e-sRGB enumerated colourspace'),
            (61, 'Compositing layer uses ROMM-RGB enumerated colourspace'),
            (62, 'Compositing layers have non-square samples'),
            (63, 'Compositing layers have labels'),
            (64, 'Codestreams have labels'),
            (65, 'Compositing layers have different colour spaces'),
            (66, 'Compositing layers have different metadata'),
        ]

    _fields_ = [
        (u8, 'ML'),
        (lambda self: dyn.clone(u0, length=self['ML'].li.int()), 'FUAM'),
        (lambda self: dyn.clone(u0, length=self['ML'].li.int()), 'DCM'),

        (u16, 'NSF'),
        (lambda self: dyn.array(self._SF, self['NSF'].li.int()), 'SF'),

        (lambda self: dyn.clone(u0, length=self['ML'].li.int()), 'SM'),

        (u16, 'NVF'),
        (lambda self: dyn.array(self._V, self['NVF'].li.int()), 'V'),
    ]

    def alloc(self, **fields):
        res = super(ReaderRequirements, self).alloc(**fields)
        # FIXME: we could probably figure out ML by looking at integer sizes
        if not operator.contains(fields, 'NVF'):
            res.set(NSF=len(res['V']))
        return res if operator.contains(fields, 'NSF') else res.set(NSF=len(res['SF']))

@Boxes.define
class DataReference(pstruct.type):
    type = b'\x64\x74\x62\x6c'
    _fields_ = [
        (u16, 'NDR'),
        (lambda self: dyn.array(Box, self['NDR'].li.int()), 'DR'),
    ]

    def alloc(self, **fields):
        res = super(DataReference, self).alloc(**fields)
        return res if operator.contains(fields, 'NDR') else res.set(NDR=len(res['DR']))

@Boxes.define
class FragmentTable(SuperBox):
    type = b'\x66\x74\x62\x6c'

@Boxes.define
class FragmentList(pstruct.type):
    type = b'\x66\x6c\x73\x74'
    class _Fragment(pstruct.type):
        _fields_ = [
            (u64, 'OFF'),
            (u32, 'LEN'),
            (u16, 'DR'),
        ]
    _fields_ = [
        (u16, 'NF'),
        (lambda self: dyn.array(_Fragment, self['NF'].li.int()), 'Fragment'),
    ]

    def alloc(self, **fields):
        res = super(FragmentList, self).alloc(**fields)
        return res if operator.contains(fields, 'NF') else res.set(NDR=len(res['Fragment']))

@Boxes.define
class CompositingLayer(SuperBox):
    type = b'\x6a\x70\x6c\x68'

@Boxes.define
class ColourGroup(SuperBox):
    type = b'\x63\x67\x72\x70'

@Boxes.define
class CodestreamRegistration(pstruct.type):
    type = b'\x63\x72\x65\x67'
    _fields_ = [
        (u16, 'XS'),
        (u16, 'YS'),
        (u16, 'CDN'),
        (u8, 'XR'),
        (u8, 'YR'),
        (u8, 'XO'),
        (u8, 'YO'),
    ]

@Boxes.define
class Composition(SuperBox):
    type = b'\x63\x6f\x6d\x70'

@Boxes.define
class CompositionOptions(pstruct.type):
    type = b'\x63\x6f\x70\x74'
    _fields_ = [
        (u32, 'HEIGHT'),
        (u32, 'WIDTH'),
        (u8, 'LOOP'),
    ]

@Boxes.define
class InstructionSet(pstruct.type):
    type = b'\x69\x6e\x73\x74'
    class _Ityp(pbinary.flags):
        _fields_ = [
            (11, 'Reserved'),
            (1, 'Crop'),
            (1, 'Animation'),
            (1, 'Dimensions'),
            (1, 'Offset')
        ]
    class _INST(pstruct.type):
        class _PERSISTLIFE(pbinary.flags):
            _fields_ = [
                (1, 'PERSIST'),
                (31, 'LIFE'),
            ]

        # FIXME: pretty certain these fields are conditional
        _fields_ = [
            (u32, 'XO'),                    # Offset
            (u32, 'YO'),
            (u32, 'WIDTH'),                 # Dimensions
            (u32, 'HEIGHT'),
            (_PERSISTLIFE, 'PERSISTLIFE'),  # Animation
            (u32, 'NEXT-USE'),
            (u32, 'XC'),                    # Crop
            (u32, 'YC'),
            (u32, 'WC'),
            (u32, 'HC'),
        ]

    _fields_ = [
        (_Ityp, 'Ityp'),
        (u16, 'REPT'),
        (u16, 'TICK'),
    ]

@Boxes.define
class Association(SuperBox):
    type = b'\x61\x73\x6f\x63'

@Boxes.define
class NumberList(parray.block):
    type = b'\x6e\x6c\x73\x74'
    _object_ = u32

@Boxes.define
class Label(ptype.block):
    type = b'\x6c\x62\x6c\x20'

@Boxes.define
class BinaryFilter(pstruct.type):
    type = b'\x62\x66\x69\x6c'
    # FIXME: this is incomplete
    _fields_ = [
        (UUID, 'F'),
        (ptype.undefined, 'DATA'),
    ]

@Boxes.define
class DesiredReproductions(SuperBox):
    type = b'\x64\x72\x65\x70'

@Boxes.define
class GraphicsTechnologyStandardOutput(ptype.block):
    type = b'\x67\x74\x73\x6f'

@Boxes.define
class ROIDescription(ptype.block):
    type = b'\x72\x6f\x69\x64'
    # FIXME

@Boxes.define
class DigitalSignature(ptype.block):
    type = b'\x63\x68\x63\x6b'
    # FIXME

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

    def alloc(self, **fields):
        res = super(SOT, self).alloc(**fields)
        return res if operator.contains(fields, 'Lsot') else res.set(Lsot=res.size())

@Marker.define
class SOD(ptype.block):
    @classmethod
    def EncodedQ(cls):
        return True

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

    def alloc(self, **fields):
        res = super(SIZ, self).alloc(**fields)
        if not operator.contains(fields, 'Csiz'):
            res.set(Csiz=len(res['C']))
        return res if operator.contains(fields, 'Lsiz') else res.set(Lsiz=res.size())

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
    class _style(pbinary.flags):
        _fields_ = [
            (2, 'Reserved'),
            (1, 'Segmentation symbols'),
            (1, 'Predictable termination'),
            (1, 'Vertically causal context'),
            (1, 'Termination on each coding pass'),
            (1, 'Reset context probabilities on coding pass boundaries'),
            (1, 'Selective arithmetic coding bypass'),
        ]

    class _Transformation(pint.enum, u8):
        _values_ = [
            ('9-7 irreversible filter', 0),
            ('5-3 irreversible filter', 1),
        ]

    _fields_ = [
        (u8, 'Number of decomposition levels'),
        (u8, 'Code-block width'),
        (u8, 'Code-block height'),
        (_style, 'Code-block style'),
        (_Transformation, 'Transformation'),
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

    def alloc(self, **fields):
        res = super(COD, self).alloc(**fields)
        if operator.contains(fields, 'SPcod') or not res['Scod']['Entropy']:
            return res if operator.contains(fields, 'Lcod') else res.set(Lcod=res.size())
        res['SPcod'].set(max(0, len(res['LL']) - 1))
        return res if operator.contains(fields, 'Lcod') else res.set(Lcod=res.size())

class Scoc(pbinary.flags):
    _fields_ = [
        (7, 'Reserved'),
        (1, 'Entropy'),
    ]

class SPcoc(SPcod): pass

@Marker.define
class COC(pstruct.type):
    def __Ccoc(self):
        stream = self.getparent(codestream.DecodedStream)
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

    def alloc(self, **fields):
        res = super(COC, self).alloc(**fields)
        if operator.contains(fields, 'SPcoc') or not res['Scoc']['Entropy']:
            return res if operator.contains(fields, 'Lcoc') else res.set(Lcoc=res.size())
        res['SPcoc'].set(max(0, len(res['LL']) - 1))
        return res if operator.contains(fields, 'Lcoc') else res.set(Lcoc=res.size())

@Marker.define
class RGN(pstruct.type):
    def __Crgn(self):
        stream = self.getparent(codestream.DecodedStream)
        try:
            index = next(i for i, item in enumerate(stream) if isinstance(item['Value'], SIZ))
        except StopIteration:
            logging.warn("Unable to locate SIZ marker!")
            return u8
        Csiz = stream[index]['Value']['Csiz']
        return u8 if Csiz.int() < 257 else u16

    def __SPrgn(self):
        length, fields = self['Lrgn'].li, ['Lrgn', 'Crgn', 'Srgn']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lrgn'),
        (__Crgn, 'Crgn'),
        (u8, 'Srgn'),
        (__SPrgn, 'SPrgn'),
    ]

    def alloc(self, **fields):
        res = super(RGN, self).alloc(**fields)
        return res if operator.contains(fields, 'Lrgn') else res.set(Lrgn=res.size())

class Sqcd(pbinary.struct):
    class _style(pbinary.enum):
        width, _values_ = 5, [
            ('None', 0),
            ('Scalar derived', 1),
            ('Scalar expounded', 2),
        ]

    _fields_ = [
        (3, 'guard'),
        (_style, 'style'),
    ]

class A29(pbinary.struct):
    '''
    Table A.29 - Reversible step size values for the SPqcd and SPqcc parameters (reversible transform only)
    '''

    _fields_ = [
        (5, 'Exponent'),
        (3, 'Reserved'),
    ]

    def float(self):
        return math.ldexp(1.0, -self['Exponent'])

    def summary(self):
        res = self.item('Exponent')
        return "Exponent={:s} : Result={:f}".format(res.summary(), self.float())

    repr = summary

class A30(pbinary.struct):
    '''
    Table A.30 - Quantization values for the SPqcd and SPqcc parameters (irreversible transformation only)
    '''

    _fields_ = [
        (5, 'Exponent'),
        (11, 'Mantissa'),
    ]

    def float(self):
        fraction = self['Mantissa'] / math.pow(2, 11)
        return math.ldexp(1.0 + fraction, -self['Exponent'])

    def summary(self):
        return "Mantissa={:s} Exponent={:s} : Result={:f}".format(self.item('Mantissa').summary(), self.item('Exponent').summary(), self.float())
    repr = summary

class ScalarArray(pbinary.array):
    def summary(self):
        fmt, iterable = "{:f}".format, (item.float() for item in self)
        return "[{:s}]".format(', '.join(map(fmt, iterable)))

@Marker.define
class QCD(pstruct.type):
    def __SPqcd(self):
        p, res, fields = self.parent, self['Sqcd'].li, ['Lqcd', 'Sqcd']
        style, length = res.item('style'), 0 if p is None else (p.blocksize() - p['Type'].blocksize()) - sum(self[fld].li.size() for fld in fields)
        if style['None']:
            return dyn.clone(ScalarArray, _object_=A29, length=length)
        elif style['Scalar derived']:
            return dyn.clone(ScalarArray, _object_=A30, length=length // 2)
        elif style['Scalar expounded']:
            return dyn.clone(ScalarArray, _object_=A30, length=length // 2)
        return dyn.clone(pbinary.array, _object_=8, length=length)

    _fields_ = [
        (u16, 'Lqcd'),
        (Sqcd, 'Sqcd'),
        (__SPqcd, 'SPqcd'),
    ]

    def alloc(self, **fields):
        res = super(QCD, self).alloc(**fields)
        return res if operator.contains(fields, 'Lqcd') else res.set(Lqcd=res.size())

class Sqcc(Sqcd): pass

@Marker.define
class QCC(pstruct.type):
    def __Cqcc(self):
        stream = self.getparent(codestream.DecodedStream)
        try:
            index = next(i for i, item in enumerate(stream) if isinstance(item['Value'], SIZ))
        except StopIteration:
            logging.warn("Unable to locate SIZ marker!")
            return u8
        Csiz = stream[index]['Value']['Csiz']
        return u8 if Csiz.int() < 257 else u16

    def __SPqcc(self):
        p, res, fields = self.parent, self['Sqcc'].li, ['Lqcc', 'Cqcc', 'Sqcc']
        style, length = res.item('style'), 0 if p is None else (p.blocksize() - p['Type'].blocksize()) - sum(self[fld].li.size() for fld in fields)
        if style['None']:
            return dyn.clone(pbinary.array, _object_=A29, length=length)
        elif style['Scalar derived']:
            return dyn.clone(pbinary.array, _object_=A30, length=length // 2)
        elif style['Scalar expounded']:
            return dyn.clone(pbinary.array, _object_=A30, length=length // 2)
        return dyn.clone(pbinary.array, _object_=8, length=length)

    _fields_ = [
        (u16, 'Lqcc'),
        (__Cqcc, 'Cqcc'),
        (Sqcc, 'Sqcc'),
        (__SPqcc, 'SPqcc'),
    ]

    def alloc(self, **fields):
        res = super(QCC, self).alloc(**fields)
        return res if operator.contains(fields, 'Lqcc') else res.set(Lqcc=res.size())

@Marker.define
class POC(pstruct.type):
    def __CSpoc(self):
        stream = self.getparent(codestream.DecodedStream)
        try:
            index = next(i for i, item in enumerate(stream) if isinstance(item['Value'], SIZ))
        except StopIteration:
            logging.warn("Unable to locate SIZ marker!")
            return u8
        Csiz = stream[index]['Value']['Csiz']
        return u8 if Csiz.int() < 257 else u16

    def __CEpoc(self):
        return u16 if isinstance(self['CSpoc'], u16) else u8

    def __Ppoc(self):
        length, fields = self['Lpoc'].li, ['Lpoc', 'RSpoc', 'CSpoc', 'LYEpoc', 'REpoc', 'CEpoc', 'Ppoc']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lpoc'),
        (u8, 'RSpoc'),
        (__CSpoc, 'CSpoc'),
        (u16, 'LYEpoc'),
        (u8, 'REpoc'),
        (__CEpoc, 'CEpoc'),
        (__Ppoc, 'Ppoc'),
    ]

    def alloc(self, **fields):
        res = super(POC, self).alloc(**fields)
        return res if operator.contains(fields, 'Lpoc') else res.set(Lpoc=res.size())

@Marker.define
class TLM(pstruct.type):
    class _Stlm(pbinary.struct):
        _fields_ = [
            (1, 'Unused'),
            (1, 'SP'),
            (2, 'ST'),
            (4, 'Reserved'),
        ]

    def __Ttlm(self):
        stlm = self['Stlm'].li
        if stlm['ST'] == 0:
            return u0
        elif stlm['ST'] == 1:
            return u8
        elif stlm['ST'] == 2:
            return u16
        return u0

    def __Ptlm(self):
        stlm = self['Stlm'].li
        return u32 if stlm['SP'] == 1 else u16

    def __missed(self):
        length, fields = self['Ltlm'].li, ['Ltlm', 'Ztlm', 'Stlm', 'Ttlm', 'Ptlm']
        return dyn.clone(ptype.block, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Ltlm'),
        (u8, 'Ztlm'),
        (_Stlm, 'Stlm'),
        (__Ttlm, 'Ttlm'),
        (__Ptlm, 'Ptlm'),
        (__missed, 'missed'),
    ]

    def alloc(self, **fields):
        res = super(TLM, self).alloc(**fields)
        return res if operator.contains(fields, 'Ltlm') else res.set(Ltlm=res.size())

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

    def alloc(self, **fields):
        res = super(PLM, self).alloc(**fields)
        return res if operator.contains(fields, 'Lplm') else res.set(Lplm=res.size())

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

    def alloc(self, **fields):
        res = super(PLT, self).alloc(**fields)
        return res if operator.contains(fields, 'Lplt') else res.set(Lplt=res.size())

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

    def alloc(self, **fields):
        res = super(PPM, self).alloc(**fields)
        return res if operator.contains(fields, 'Lppm') else res.set(Lppm=res.size())

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

    def alloc(self, **fields):
        res = super(PPT, self).alloc(**fields)
        return res if operator.contains(fields, 'Lppt') else res.set(Lppt=res.size())

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

    def alloc(self, **fields):
        res = super(SOP, self).alloc(**fields)
        return res if operator.contains(fields, 'Lsop') else res.set(Lsop=res.size())

@Marker.define
class EPH(ptype.block):
    pass

@Marker.define
class CRG(pstruct.type):
    _fields_ = [
        (u16, 'Lcrg'),
        (u16, 'Xcrg'),
        (u16, 'Ycrg'),
    ]

    def alloc(self, **fields):
        res = super(CRG, self).alloc(**fields)
        return res if operator.contains(fields, 'Lcrg') else res.set(Lcrg=res.size())

@Marker.define
class COM(pstruct.type):
    def __content(self):
        length, fields = self['Lcom'].li, ['Lcom', 'Rcom']
        return dyn.clone(pstr.string, length=length.int() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (u16, 'Lcom'),
        (u16, 'Rcom'),
        (__content, 'Ccom'),
    ]

    def alloc(self, **fields):
        res = super(COM, self).alloc(**fields)
        return res if operator.contains(fields, 'Lcom') else res.set(Lcom=res.size())

if __name__ == '__main__':
    import ptypes, image.jpeg.jp2 as jp2
    ptypes.setsource(ptypes.prov.file('logo.jp2', mode='r'))

    z = jp2.File().l

    print(z[3]['data'].decode())

    a = ptype.block(offset=z.getoffset()+z.size(), length=0x100).l
    print(a.hexdump())
