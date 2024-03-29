import math, fractions, itertools, operator, functools, logging
import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### types
class Type(ptype.definition):
    cache = {}

@Type.define
class BYTE(pint.uint8_t): type = 1

@Type.define
class ASCII(pstr.char_t): type = 2

@Type.define
class SHORT(pint.uint16_t): type = 3

@Type.define
class LONG(pint.uint32_t): type = 4

@Type.define
class RATIONAL(parray.type):
    length, _object_ = 2, pint.uint32_t
    type = 5
    def float(self):
        numerator, denominator = (item.int() for item in self)
        return float(numerator) / denominator
    def set(self, value):
        fr = fractions.Fraction(value)
        return super(RATIONAL,self).set([fr.numerator, fr.denominator])
    def get(self):
        return self.float()
    def summary(self):
        return '{:f} ({:#x}, {:#x})'.format(self.float(), self[0].int(), self[1].int())

@Type.define
class SBYTE(pint.sint8_t): type = 6

@Type.define
class UNDEFINED(ptype.block): type = 7

@Type.define
class SSHORT(pint.sint16_t): type = 8

@Type.define
class SLONG(pint.sint32_t): type = 9

@Type.define
class SRATIONAL(RATIONAL):
    type, _object_ = 10, pint.sint32_t

@Type.define
class FLOAT(pfloat.single): type = 11
@Type.define
class DOUBLE(pfloat.double): type = 12

@Type.define
class IFD(pint.uint32_t):
    type = 13
    def summary(self):
        integral = self.int()
        return '{:+#0{:d}x} ({:+d})'.format(integral, 2 * self.size() + sum(map(len, ['0x', '+'])), integral)

@Type.define
class LONG8(pint.uint64_t): type = 16
@Type.define
class SLONG8(pint.sint64_t): type = 17

@Type.define
class IFD8(pint.uint64_t):
    type = 18
    def summary(self):
        integral = self.int()
        return '{:+#0{:d}x} ({:+d})'.format(integral, 2 * self.size() + sum(map(len, ['0x', '+'])), integer)

class DirectoryType(pint.enum, pint.uint16_t):
    pass
DirectoryType._values_ = [(item.__name__, item.type) for _, item in Type.cache.items()]

### tags
class Tags(ptype.definition):
    attribute, cache = 'tag', {}
class TagValue(ptype.definition):
    cache = {}

class TIFFTAG(pint.enum):
    _values_ = [
        ('NewSubfileType', 254),
        ('SubfileType', 255),
        ('ImageWidth', 256),
        ('ImageLength', 257),
        ('BitsPerSample', 258),
        ('Compression', 259),
        ('PhotometricInterpretation', 262),
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
        ('ColorResponseUnit', 300),
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
        ('BadFaxLines', 326),
        ('CleanFaxData', 327),
        ('ConsecutiveBadFaxLines', 328),
        ('SubIFD', 330),
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
        ('ClipPath', 343),
        ('XClipPathUnits', 344),
        ('YClipPathUnits', 345),
        ('Indexed', 346),
        ('JPEGTables', 347),
        ('OPIProxy', 351),
        ('GlobalParametersIFD', 400),
        ('ProfileType', 401),
        ('FaxProfile', 402),
        ('CodingMethods', 403),
        ('VersionYear', 404),
        ('ModeNumber', 405),
        ('Decode', 433),
        ('ImageBaseColor', 434),
        ('T82Options', 435),
        ('JPEGProc', 512),
        ('JPEGInterchangeFormat', 513),
        ('JPEGInterchangeFormatLength', 514),
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
        ('XMLPacket', 700),
        ('OPIImageID', 32781),
        ('Matteing', 32995),
        ('DataType', 32996),
        ('ImageDepth', 32997),
        ('TileDepth', 32998),
        ('PixarImageFullWidth', 33300),
        ('PixarImageFullLength', 33301),
        ('PixarTextureFormat', 33302),
        ('PixarWrapModes', 33303),
        ('PixarFieldOfViewCotangent', 33304),
        ('PixarMatrixWorldToScreen', 33305),
        ('PixarMatrixWorldToCamera', 33306),
        ('WriterSerialNumber', 33405),
        ('CFARepeatPatternDim', 33421),
        ('CFAPattern', 33422),
        ('Copyright', 33432),
        ('RichTIFFIPTC', 33723),
        ('IT8Site', 34016),
        ('IT8ColorSequence', 34017),
        ('IT8Header', 34018),
        ('IT8RasterPadding', 34019),
        ('IT8BitsPerRunLength', 34020),
        ('IT8BitsPerExtendedRunLength', 34021),
        ('IT8ColorTable', 34022),
        ('IT8ImageColorIndicator', 34023),
        ('IT8BkgColorIndicator', 34024),
        ('IT8ImageColorValue', 34025),
        ('IT8BkgColorValue', 34026),
        ('IT8PixelIntensityRange', 34027),
        ('IT8TransparencyIndicator', 34028),
        ('IT8ColorCharacterization', 34029),
        ('IT8HCUsage', 34030),
        ('IT8TrapIndicator', 34031),
        ('IT8CMYKEquivalent', 34032),
        ('FrameCount', 34232),
        ('Photoshop', 34377),
        ('EXIFIFD', 34665),
        ('ICCProfile', 34675),
        ('ImageLayer', 34732),
        ('JBIGOptions', 34750),
        ('GPSIFD', 34853),
        ('FaxRecvParams', 34908),
        ('FaxSubAddress', 34909),
        ('FaxRecvTime', 34910),
        ('FaxDCS', 34911),
        ('SToNits', 37439),
        ('FedexEDR', 34929),
        ('InteroperabilityIFD', 40965),
        ('DNGVersion', 50706),
        ('DNGBackwardVersion', 50707),
        ('UniqueCameraModel', 50708),
        ('LocalizedCameraModel', 50709),
        ('CFAPlaneColor', 50710),
        ('CFALayout', 50711),
        ('LinearizationTable', 50712),
        ('BlackLevelRepeatDim', 50713),
        ('BlackLevel', 50714),
        ('BlackLevelDeltaH', 50715),
        ('BlackLevelDeltaV', 50716),
        ('WhiteLevel', 50717),
        ('DefaultScale', 50718),
        ('DefaultCropOrigin', 50719),
        ('DefaultCropSize', 50720),
        ('ColorMatrix1', 50721),
        ('ColorMatrix2', 50722),
        ('CameraCalibration1', 50723),
        ('CameraCalibration2', 50724),
        ('ReductionMatrix1', 50725),
        ('ReductionMatrix2', 50726),
        ('AnalogBalance', 50727),
        ('ASSHotNeutral', 50728),
        ('ASSHotWhiteXY', 50729),
        ('BaseLineExposure', 50730),
        ('BaseLineNoise', 50731),
        ('BaseLineSharpness', 50732),
        ('BayerGreenSplit', 50733),
        ('LinearResponseLimit', 50734),
        ('CameraSerialNumber', 50735),
        ('LensInfo', 50736),
        ('ChromaBlurRadius', 50737),
        ('AntialiasStrength', 50738),
        ('ShadowScale', 50739),
        ('DNGPrivateData', 50740),
        ('MakerNoteSafety', 50741),
        ('CalibrationIlluminant1', 50778),
        ('CalibrationIlluminant2', 50779),
        ('BestQualityScale', 50780),
        ('RawDataUniqueID', 50781),
        ('OriginalRawFilename', 50827),
        ('OriginalRawFiledata', 50828),
        ('ActiveArea', 50829),
        ('MaskedAreas', 50830),
        ('ASSHotICCProfile', 50831),
        ('ASSHotPreProfileMatrix', 50832),
        ('CurrentICCProfile', 50833),
        ('CurrentPreProfileMatrix', 50834),
        ('DCSHueShiftValues', 65535),
    ]

class DirectoryTag(TIFFTAG, pint.uint16_t):
    pass

### Tag types
@TagValue.define
class OFILETYPE(pint.enum):
    type = 'SubfileType'
    _values_ = [
        ('IMAGE', 1),
        ('REDUCEDIMAGE', 2),
        ('PAGE', 3),
    ]

@TagValue.define
class COMPRESSION(pint.enum):
    type = 'Compression'
    _values_ = [
        ('NONE', 1),
        ('CCITTRLE', 2),
        ('CCITTFAX3', 3),
        ('CCITT_T4', 3),
        ('CCITTFAX4', 4),
        ('CCITT_T6', 4),
        ('LZW', 5),
        ('OJPEG', 6),
        ('JPEG', 7),
        ('T85', 9),
        ('T43', 10),
        ('NEXT', 32766),
        ('CCITTRLEW', 32771),
        ('PACKBITS', 32773),
        ('THUNDERSCAN', 32809),
        ('IT8CTPAD', 32895),
        ('IT8LW', 32896),
        ('IT8MP', 32897),
        ('IT8BL', 32898),
        ('PIXARFILM', 32908),
        ('PIXARLOG', 32909),
        ('DEFLATE', 32946),
        ('ADOBE_DEFLATE', 8),
        ('DCS', 32947),
        ('JBIG', 34661),
        ('SGILOG', 34676),
        ('SGILOG24', 34677),
        ('JP2000', 34712),
        ('LZMA', 34925),
    ]

@TagValue.define
class PHOTOMETRIC(pint.enum):
    type = 'PhotometricInterpretation'
    _values_ = [
        ('MINISWHITE', 0),
        ('MINISBLACK', 1),
        ('RGB', 2),
        ('PALETTE', 3),
        ('MASK', 4),
        ('SEPARATED', 5),
        ('YCBCR', 6),
        ('CIELAB', 8),
        ('ICCLAB', 9),
        ('ITULAB', 10),
        ('CFA', 32803),
        ('LOGL', 32844),
        ('LOGLUV', 32845),
    ]

@TagValue.define
class THRESHHOLD(pint.enum):
    type = 'Threshholding'
    _values_  = [
        ('BILEVEL', 1),
        ('HALFTONE', 2),
        ('ERRORDIFFUSE', 3),
    ]

@TagValue.define
class FILLORDER(pint.enum):
    type = 'FillOrder'
    _values_ = [
        ('MSB2LSB', 1),
        ('LSB2MSB', 2),
    ]

@TagValue.define
class ORIENTATION(pint.enum):
    type = 'Orientation'
    _values_ = [
        ('TOPLEFT', 1),
        ('TOPRIGHT', 2),
        ('BOTRIGHT', 3),
        ('BOTLEFT', 4),
        ('LEFTTOP', 5),
        ('RIGHTTOP', 6),
        ('RIGHTBOT', 7),
        ('LEFTBOT', 8),
    ]

@TagValue.define
class PLANARCONFIG(pint.enum):
    type = 'PlanarConfiguration'
    _values_ = [
        ('CONTIG', 1),
        ('SEPARATE', 2),
    ]

@TagValue.define
class GRAYRESPONSEUNIT(pint.enum):
    type = 'GrayResponseUnit'
    _values_ = [
        ('10S', 1),
        ('100S', 2),
        ('1000S', 3),
        ('10000S', 4),
        ('100000S', 5),
    ]

@TagValue.define
class GROUP3OPT(pint.enum):
    type = 'T4Options'
    _values_ = [
        ('2DENCODING', 0x1),
        ('UNCOMPRESSED', 0x2),
        ('FILLBITS', 0x3),
    ]

@TagValue.define
class GROUP4OPT(pint.enum):
    type = 'T6Options'
    _values_ = [
        ('UNCOMPRESSED', 0x2),
    ]

@TagValue.define
class RESUNIT(pint.enum):
    type = 'ResolutionUnit'
    _values_ = [
        ('NONE', 1),
        ('INCH', 2),
        ('CENTIMETER', 3),
    ]

@TagValue.define
class COLORRESPONSEUNIT(pint.enum):
    type = 'ColorResponseUnit'
    _values_ = [
        ('10S', 1),
        ('100S', 2),
        ('1000S', 3),
        ('10000S', 4),
        ('100000S', 5),
    ]

@TagValue.define
class PREDICTOR(pint.enum):
    type = 'Predictor'
    _values_ = [
        ('NONE', 1),
        ('HORIZONTAL', 2),
        ('FLOATINGPOINT', 3),
    ]

@TagValue.define
class CLEANFAXDATA(pint.enum):
    type = 'CleanFaxData'
    _values_ = [
        ('CLEAN', 0),
        ('REGENERATED', 1),
        ('UNCLEAN', 2),
    ]

@TagValue.define
class INKSET(pint.enum):
    type = 'InkSet'
    _values_ = [
        ('CMYK', 1),
        ('MULTIINK', 2),
    ]

@TagValue.define
class EXTRASAMPLES(pint.enum):
    type = 'ExtraSamples'
    _values_ = [
        ('UNSPECIFIED', 0),
        ('ASSOCALPHA', 1),
        ('UNASSALPHA', 2),
    ]

@TagValue.define
class SAMPLEFORMAT(pint.enum):
    type = 'SampleFormat'
    _values_ = [
        ('UINT', 1),
        ('INT', 2),
        ('IEEEFP', 3),
        ('VOID', 4),
        ('COMPLEXINT', 5),
        ('COMPLEXIEEEFP', 6),
    ]

@TagValue.define
class PROFILETYPE(pint.enum):
    type = 'ProfileType'
    _values_ = [
        ('UNSPECIFIED', 0),
        ('G3_FAX', 1),
    ]

@TagValue.define
class FAXPROFILE(pint.enum):
    type = 'FaxProfile'
    _values_ = [
        ('S', 1),
        ('F', 2),
        ('J', 3),
        ('C', 4),
        ('L', 5),
        ('M', 6),
    ]

@TagValue.define
class CODINGMETHODS(pint.enum):
    type = 'CodingMethods'
    _values_ = [
        ('T4_1D', 1<<1),
        ('T4_2D', 1<<2),
        ('T6', 1<<3),
        ('T85', 1<<4),
        ('T42', 1<<5),
        ('T43', 1<<6),
    ]

@TagValue.define
class JPEGPROC(pint.enum):
    type = 'JPEGProc'
    _values_ = [
        ('BASELINE', 1),
        ('LOSSLESS', 2),
    ]

@TagValue.define
class YCBRPOSITION(pint.enum):
    type = 'YCbCrPositioning'
    _values_ = [
        ('CENTERED', 1),
        ('COSITED', 2),
    ]

### file
class Entry(pstruct.type):
    def __figure_type(self):
        tag_f, type_f = (self[fld].li for fld in ['tag', 'type'])

        # determine the base type
        try:
            type_ = Type.lookup(type_f.int())
        except KeyError:
            type_ = pint.uint32_t

        # figure out if there's a tag enumeration associated with it
        try:
            tag_ = TagValue.lookup(tag_f.str())
        except KeyError:
            t = type_

        # construct an enumeration type so that we can return it
        else:
            # FIXME: we need to create this type iff the tagvalue
            #        tells us that this is an enumeration, otherwise
            #        we should use the tag_ type whilst falling back
            #        to the type_ if there wasn't a definition for it.
            ns = {key : value for key, value in tag_.__dict__.items()}
            ns.update(type_.__dict__)
            t = type(tag_.__name__, (tag_, type_), ns)
        return t

    def __value(self):
        # FIXME: we need to use the tagvalue somehow to determine
        #        whether the type+tag combination results in this
        #        actually being a pointer/offset or just a long.
        t, count = self.__figure_type(), self['count'].li.int()

        # if the length of our value is less than a dword, then the
        # type's value can be stored within the entry. otherwise,
        # we undefine it so that we use the pointer.
        return t if t().a.size() * count <= 4 else ptype.undefined

    def __padding(self):
        if isinstance(self['value'].li, ptype.undefined):
            return dyn.block(0)
        cb = 4 - self['value'].li.size()
        return dyn.block(max(0, cb))

    def __pointer(self):
        t, count = self.__figure_type(), self['count'].li.int()
        result = dyn.clone(parray.type, _object_=t, length=count)

        # if the value has been undefined, then this is a pointer
        # to the result type.
        if isinstance(self['value'].li, ptype.undefined):
            return dyn.pointer(result, pint.uint32_t)

        # otherwise our value is in the proper place, and we
        # need to return an unsized fake pointer.
        return dyn.pointer(ptype.undefined, pint.uint_t)

    _fields_ = [
        (DirectoryTag, 'tag'),
        (DirectoryType, 'type'),
        (pint.uint32_t, 'count'),
        (__value, 'value'),
        (__padding, 'padding'),
        (__pointer, 'pointer'),
    ]

class Directory(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(Entry, self['count'].li.int()), 'entry'),
        (lambda _: dyn.pointer(Directory, pint.uint32_t), 'next')
    ]

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

    def enumerate(self):
        count = 0
        while True:
            for index, item in enumerate(self['entry']):
                yield count + index, item
            if not self['next'].int():
                break
            self, count = self['next'].d.li, count + self['count'].int()
        return

    def data(self):
        raise NotImplementedError

class Header(pstruct.type):
    class _byteorder(pint.enum, pint.uint16_t):
        _values_ = [
            ('littleendian', 0x4949),
            ('bigendian', 0x4d4d),
        ]

    @classmethod
    def Big(cls):
        items = {'byteorder': ptypes.config.byteorder.bigendian}
        return cls(recurse=items).a.set(order='bigendian', signature=0x002a)
    @classmethod
    def Little(cls):
        items = {'byteorder': ptypes.config.byteorder.littleendian}
        return cls(recurse=items).a.set(order='littleendian', signature=0x2a00)

    def Order(self):
        order = self['order'].serialize()
        if order == 'II':
            return ptypes.config.byteorder.littleendian
        elif order == 'MM':
            return ptypes.config.byteorder.bigendian
        cls = self.__class__
        logging.info("{:s}.byteorder : Unknown byteorder for {!r}. Defaulting to the platform. : {!r}.".format('.'.join([__name__, cls.__name__]), order, ptypes.Config.integer.order.__name__))
        return ptypes.Config.integer.order

    class _signature(pint.uint16_t):
        def default(self):
            return self.copy().set(0x002a)

    _fields_ = [
        (_byteorder, 'order'),
        (_signature, 'signature'),
    ]

    def set_be(self):
        return self.alloc(order='bigendian', signature=0x002a)
    def set_le(self):
        return self.alloc(order='littleendian', signature=0x2a00)

class File(pstruct.type):
    def __pointer(self):
        order = self['header'].li.Order()
        pointer = dyn.rpointer(Directory, self, pint.uint32_t, byteorder=order)
        return dyn.clone(pointer, recurse={'byteorder': order})

    def __data(self):
        minimum = self['header'].li.size() + self['pointer'].li.size()

        # if our source is bounded, then we can use it to determine
        # how many bytes are used for the data.
        if isinstance(self.source, ptypes.prov.bounded):
            size = self.source.size() - minimum

        # otherwise, we can't be sure what the size is we use 0.
        else:
            size = 0
        return dyn.block(max(0, size))

    _fields_ = [
        (Header, 'header'),
        (__pointer, 'pointer'),
        (__data, 'data'),
    ]

if __name__ == '__main__':
    import sys, ptypes, image.tiff as tiff
    filename = sys.argv[1]
    ptypes.setsource(ptypes.provider.file(filename, 'rb'))

    z = tiff.File()
    z = z.l

    a = z['pointer'].d
    a = a.l

    for item in a.iterate():
        print(item.l)
        if not isinstance(item['value'], ptypes.undefined):
            print(item['value'])
            continue
        if isinstance(item['pointer'], ptypes.undefined):
            raise AssertionError(item['pointer'])
        for value in item['pointer'].d.l:
            print(value)
        continue
