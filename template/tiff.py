import math,fractions,itertools,operator,functools
import ptypes
from ptypes import *

ptypes.setbyteorder( pint.bigendian )

### types
class Type(ptype.definition):
    cache = {}

@Type.define(type=1)
class BYTE(pint.uint8_t): pass

@Type.define(type=2)
class ASCII(pstr.char_t): pass

@Type.define(type=3)
class SHORT(pint.uint16_t): pass

@Type.define(type=4)
class LONG(pint.uint32_t): pass

@Type.define(type=5)
class RATIONAL(dyn.array(pint.uint32_t,2)):
    def float(self):
        numerator,denominator = map(operator.methodcaller('num'), (self[0],self[1]))
        return float(numerator) / denominator
    def set(self, value):
        fr = fractions.Fraction(value)
        return super(RATIONAL,self).set((fr.numerator,fr.denominator))
    def get(self):
        return self.float()
    def summary(self):
        return '{:f} (0x{:x}, 0x{:x})'.format(self.float(), self[0].num(), self[1].num())

@Type.define(type=6)
class SBYTE(pint.sint8_t): pass

@Type.define(type=7)
class UNDEFINED(ptype.block): pass

@Type.define(type=8)
class SSHORT(pint.sint16_t): pass

@Type.define(type=9)
class SLONG(pint.sint32_t): pass

@Type.define(type=10)
class SRATIONAL(RATIONAL):
    _object_ = pint.sint32_t

@Type.define(type=11)
class FLOAT(pfloat.single): pass
@Type.define(type=12)
class DOUBLE(pfloat.double): pass

class DirectoryType(pint.enum, pint.uint16_t):
    _values_ = [(n.__name__, n.type) for _,n in Type.cache.iteritems()]

### tags
class Tags(ptype.definition):
    attribute,cache = 'tag',{}

class DirectoryTag(pint.uint16_t, pint.enum): pass
DirectoryTag._values_ = [
    ('PhotometricInterpretation', 262),
    ('NewSubfileType', 254),
    ('SubfileType', 255),
    ('ImageWidth', 256),
    ('ImageLength', 257),
    ('BitsPerSample', 258),
    ('Compression', 259),
    ('Threshholding', 263),
    ('CellWidth', 264),
    ('CellLength', 265),
    ('FillOrder', 266),
    ('DocumentName', 269),
    ('ImageDescription', 270),
    ('Make', 271),
    ('Model', 272),
    ('StripOffsets', 273),
    ('Orientation', 274),
    ('SamplesPerPixel', 277),
    ('RowsPerStrip', 278),
    ('StripByteCounts', 279),
    ('MinSampleValue', 280),
    ('MaxSampleValue', 281),
    ('XResolution', 282),
    ('YResolution', 283),
    ('PlanarConfiguration', 284),
    ('PageName', 285),
    ('XPosition', 286),
    ('YPosition', 287),
    ('FreeOffsets', 288),
    ('FreeByteCounts', 289),
    ('GrayResponseUnit', 290),
    ('GrayResponseCurve', 291),
    ('T4Options', 292),
    ('T6Options', 293),
    ('ResolutionUnit', 296),
    ('PageNumber', 297),
    ('TransferFunction', 301),
    ('Software', 305),
    ('DateTime', 306),
    ('Artist', 315),
    ('HostComputer', 316),
    ('Predictor', 317),
    ('WhitePoint', 318),
    ('PrimaryChromaticities', 319),
    ('ColorMap', 320),
    ('HalftoneHints', 321),
    ('TileWidth', 322),
    ('TileLength', 323),
    ('TileOffsets', 324),
    ('TileByteCounts', 325),
    ('InkSet', 332),
    ('InkNames', 333),
    ('NumberOfInks', 334),
    ('DotRange', 336),
    ('TargetPrinter', 337),
    ('ExtraSamples', 338),
    ('SampleFormat', 339),
    ('SMinSampleValue', 340),
    ('SMaxSampleValue', 341),
    ('TransferRange', 342),
    ('JPEGProc', 512),
    ('JPEGInterchangeFormat', 513),
    ('JPEGInterchangeFormatLngth', 514),
    ('JPEGRestartInterval', 515),
    ('JPEGLosslessPredictors', 517),
    ('JPEGPointTransforms', 518),
    ('JPEGQTables', 519),
    ('JPEGDCTables', 520),
    ('JPEGACTables', 521),
    ('YCbCrCoefficients', 529),
    ('YCbCrSubSampling', 530),
    ('YCbCrPositioning', 531),
    ('ReferenceBlackWhite', 532),
    ('Copyright', 33432),
]

### file
class Entry(pstruct.type):
    def __value(self):
        count = self['count'].li.num()
        try:
            object = Type.lookup(self['type'].li.num())
        except KeyError:
            return pint.uint32_t
        else:
            t = dyn.array(object, count)
            if count == 1 and t().a.size() <= 4: return object
            if t().a.size() <= 4: return t
        return ptype.undefined

    def __pointer(self):
        count = self['count'].li.num()
        try:
            object = Type.lookup(self['type'].li.num())
            t = dyn.array(object, count)
        except KeyError:
            pass
        else:
            if isinstance(self['value'], ptype.undefined): return dyn.pointer(t)
        return ptype.undefined

    _fields_ = [
        (DirectoryTag, 'tag'),
        (DirectoryType, 'type'),
        (pint.uint32_t, 'count'),
        (__value, 'value'),
        (lambda s: dyn.block(0) if isinstance(s['value'], ptype.undefined) else dyn.block(4-s['value'].li.size()), 'padding'),
        (__pointer, 'pointer'),
    ]

class Directory(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda s: dyn.array(Entry, s['count'].li.num()), 'entry'),
        (dyn.pointer(lambda _: Directory), 'next')
    ]

    def iterate(self):
        for n in self['entry']:
            yield n
        return

    def data(self):
        raise NotImplementedError

class Header(pstruct.type):
    def byteorder(self):
        bo = self['byteorder'].serialize()
        if bo == 'II':
            return ptypes.config.byteorder.littleendian
        elif bo == 'MM':
            return ptypes.config.byteorder.bigendian
        raise NotImplementedError("Unknown byteorder : {!r}".format(bo))

    _fields_ = [
        (dyn.block(2), 'byteorder'),
        (dyn.block(2), 'signature'),
    ]

class File(pstruct.type):
    _fields_ = [
        (Header, 'header'),
        (lambda s: dyn.pointer(Directory,type=dyn.clone(pint.uint32_t,byteorder=s['header'].li.byteorder()), recurse={'byteorder':s['header'].li.byteorder()}), 'pointer'),
    ]

if __name__ == '__main__':
    import ptypes,tiff
    reload(tiff)
    ptypes.setsource( ptypes.file('sample.tif') )

    a = tiff.File()
    a = a.l
    for n in a['pointer'].d.l.iterate():
        print n.l
        if not isinstance(n['value'], ptypes.ptype.undefined):
            print n['value']
            continue
        assert not isinstance(n['pointer'], ptypes.ptype.undefined)
        for v in n['pointer'].d.l:
            print v
        continue

