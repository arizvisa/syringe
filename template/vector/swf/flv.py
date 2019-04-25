import ptypes, math, logging
from ptypes import *

from .primitives import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)
### primitives

## float types
class FLOAT16(pfloat.half): pass
class FLOAT(pfloat.single): pass
class DOUBLE(pfloat.double): pass

## int types
class SI8(pint.int8_t): pass
class SI16(pint.int16_t): pass
class SI24(pint.int_t): length = 3
class SI32(pint.int32_t): pass
class SI64(pint.int64_t): pass

class UI8(pint.int8_t): pass
class UI16(pint.int16_t): pass
class UI24(pint.int_t): length = 3
class UI32(pint.int32_t): pass
class UI64(pint.int64_t): pass

(SI8, UI8, SI16, UI16, SI32, UI32, UI64) = ( pint.bigendian(x) for x in (SI8,UI8,SI16,UI16,SI32,UI32,UI64) )

## fixed-point types
class SI8_8(pfloat.sfixed_t): length,fractional = 2,8
class SI16_16(pfloat.sfixed_t): length,fractional = 4,16
class UI8_8(pfloat.fixed_t): length,fractional = 2,8
class UI16_16(pfloat.fixed_t): length,fractional = 4,16

#### Tags
class TagHeader(ptype.definition): cache = {}
class TagBody(ptype.definition): cache = {}

### AUDIODATA
@TagHeader.define
class AudioTagHeader(pbinary.struct):
    type = 8
    _fields_ = [
        (4,'SoundFormat'),
        (2,'SoundRate'),
        (1,'SoundSize'),
        (1,'SoundType'),
        (lambda s: 8 if s['SoundFormat'] == 10 else 0,'AACPacketType'),
    ]

# FIXME
@TagBody.define
class AudioTagBody(pstruct.type):
    type = 8
    def __Data(self):
        h = self.getparent(FLVTAG)['TagHeader'].li
        return AudioPacketData.lookup(h['SoundFormat'])
    _fields_ = [(__Data, 'Data')]

## audio packet data
class AudioPacketData(ptype.definition): cache = {}

@AudioPacketData.define
class AACAUDIODATA(pstruct.type):
    type = 10
    _fields_ = [(lambda s: AudioSpecificConfig if s.getparent(FLVTAG)['TagHeader'].li['AACPacketType'] == 0 else ptype.block, 'Data')]

### VIDEODATA
@TagHeader.define
class VideoTagHeader(pstruct.type):
    type = 9
    class Type(pbinary.struct):
        _fields_ = [(4, 'FrameType'), (4, 'CodecID')]
        def summary(self):
            return 'FrameType:{:d} CodecId:{:d}'.format(self['FrameType'], self['CodecID'])

    def __Header(self):
        t = self['Type'].li
        return VideoPacketHeader.withdefault(t['CodecID'], type=t['CodecID'])

    _fields_ = [
        (Type, 'Type'),
        (__Header, 'Header'),
    ]

    def summary(self):
        h = self['Type']
        return 'Type{{{:s}}} {:s}'.format(h.summary(), self['Header'].classname(), self['Header'].summary() or repr(''))

# FIXME
@TagBody.define
class VideoTagBody(pstruct.type):
    type = 9
    def __Data(self):
        h = self.getparent(StreamTag)['Header'].li
        t = h['Type']
        if t['FrameType'] == 5:
            return UI8
        return VideoPacketData.lookup(t['CodecId'])
    _fields_ = [(__Data,'Data')]

## video packet header
class VideoPacketHeader(ptype.definition):
    cache = {}
    class unknown(pstruct.type): _fields_ = []
    default = unknown

@VideoPacketHeader.define
class AVCVIDEOPACKETHEADER(pstruct.type):
    type = 7
    class AVCPacketType(pint.enum, UI8):
        _values_ = [
            (0, 'AVC sequence header'),
            (1, 'AVC NALU'),
            (2, 'AVC end-of-sequence header'),
        ]
    _fields_ = [
        (AVCPacketType, 'AVCPacketType'),
        (SI24, 'CompositionTime'),
    ]

## video packet data
class VideoPacketData(ptype.definition): cache = {}

@VideoPacketData.define
class H263VIDEOPACKET(pbinary.struct):
    """Sorenson H.263"""
    type = 2
    def __Custom(self):
        t = self['PictureSize']
        if t == 0:
            return 8
        elif t == 1:
            return 16
        return 0

    class ExtraInformation(pbinary.terminatedarray):
        class _object_(pbinary.struct):
            _fields_ = [
                (1, 'Flag'),
                (lambda s: s['Flag'] and 8 or 0, 'Data'),
            ]
        def isTerminator(self, value):
            return self['Flag'] == 0

    class MACROBLOCK(pbinary.struct):
        class BLOCKDATA(ptype.block):
            # FIXME: Look up H.263 ieee spec
            pass

        _fields_ = [
            (1, 'CodecMacroBlockFlag'),
            # ...
            (ptype.block, 'MacroBlockType'),       # H.263 5.3.2
            (ptype.block, 'BlockPattern'),         # H.263 5.3.5
            (2, 'QuantizerInformation'),    # H.263 5.3.6
            (2, 'MotionVectorData'),        # H.263 5.3.7
            (6, 'ExtraMotionVectorData'),   # H.263 5.3.8
            (dyn.array(BLOCKDATA, 6), 'BlockData'),
        ]

    _fields_ = [
        (17, 'PictureStartCode'),
        (5, 'Version'),
        (8, 'TemporalReference'),
        (3, 'PictureSize'),
        (__Custom, 'CustomWidth'),
        (__Custom, 'CustomHeight'),
        (2, 'PictureType'),
        (1, 'DeblockingFlag'),
        (5, 'Quantizer'),
        (ExtraInformation, 'ExtraInformation'),
        (MACROBLOCK, 'Macroblock'),
    ]

@VideoPacketData.define
class SCREENVIDEOPACKET(pstruct.type):
    """Screen video"""
    type = 3
    class IMAGEBLOCK(pstruct.type):
        _fields_ = [
            (pint.bigendian(UI16), 'DataSize'), # UB[16], but whatever
            (lambda s: dyn.block(s['DataSize'].li.int()), 'Data'),
        ]

    def __ImageBlocks(self):
        w,h = self['Width'],self['Height']
        blocks_w = math.ceil(w['Image'] / float(w['Block']))
        blocks_h = math.ceil(h['Image'] / float(h['Block']))
        count = long(blocks_w * blocks_h)
        return dyn.array(self.IMAGEBLOCK, count)

    class Dim(pbinary.struct):
        _fields_ = [(4,'Block'),(12,'Image')]

    _fields_ = [
        (Dim, 'Width'),
        (Dim, 'Height'),
        (__ImageBlocks, 'ImageBlocks'),
    ]

@VideoPacketData.define
class VP6FLVVIDEOPACKET(ptype.block):
    """On2 VP6"""
    type = 4
    class Adjustment(pbinary.struct):
        _fields_ = [(4, 'Horizontal'),(4,'Vertical')]

    _fields_ = [
        (Adjustment, 'Adjustment'),
        (lambda s: dyn.block(s.getparent(StreamTag).DataSize() - s['Adjustment'].li.size()), 'Data'),
    ]

@VideoPacketData.define
class VP6FLVALPHAVIDEOPACKET(pstruct.type):
    """On2 VP6 with alpha channel"""
    type = 5
    def __AlphaData(self):
        return ptype.undefined

    def __Data(self):
        streamtag = self.getparent(StreamTag)
        sz = streamtag.DataSize()
        ofs = self['OffsetToAlpha'].li.int()

        if ofs + self['Adjustment'].li.size() >= sz:
            logging.warn('OffsetToAlpha incorrect : %x', self.getoffset())
            return dyn.block(sz - self['Adjustment'].size() - self['OffsetToAlpha'].size())
        return dyn.block(ofs)

    _fields_ = [
        (VP6FLVVIDEOPACKET.Adjustment, 'Adjustment'),
        (UI24, 'OffsetToAlpha'),
#        (lambda s: dyn.block(s['OffsetToAlpha'].li.int()), 'Data'),
        (__Data, 'Data'),
        (lambda s: dyn.block(s.getparent(StreamTag).DataSize() - (s['Adjustment'].li.size()+s['OffsetToAlpha'].li.size()+s['Data'].li.size())), 'AlphaData'),
    ]

@VideoPacketData.define
class SCREENV2VIDEOPACKET(pstruct.type):
    """Screen video version 2"""
    type = 6
    class Flags(pbinary.struct):
        _fields_ = [
            (6, 'Reserved'),
            (1, 'HasIFrameImage'),
            (1, 'HasPaletteInfo'),
        ]
    class IMAGEBLOCKV2(pstruct.type):
        class IMAGEFORMAT(pbinary.struct):
            _fields_ = [
                (3, 'Reserved'),
                (2, 'ColorDepth'),
                (1, 'HasDiffBlocks'),
                (1, 'ZlibPrimeCompressCurrent'),
                (1, 'ZlibPrimeCompressPrevious'),
            ]
        class IMAGEDIFFPOSITION(pstruct.type):
            _fields_ = [(UI8,n) for n in ('RowStart','Height')]
        class IMAGEPRIMEPOSITION(pbinary.struct):
            _fields_ = [(UI8,n) for n in ('Block column','Block row')]

        def __ImageBlockHeader(self):
            # FIXME: since this field depends on 2 separate flags...which one should get prio?
            fmt = self['Format'].li
            if fmt['HasDiffBlocks']:
                return self.IMAGEDIFFPOSITION
            elif fmt['ZlibPrimeCompressCurrent']:
                return self.IMAGEPRIMEPOSITION
            return ptype.undefined

        _fields_ = [
            (pint.bigendian(UI16), 'DataSize'), # UB[16], but whatever
            (IMAGEFORMAT, 'Format'),
            (__ImageBlockHeader, 'ImageBlockHeader'),
            (lambda s: dyn.block(s['DataSize'].li.int()), 'Data'),
        ]

    def __ImageBlocks(self):
        w,h = self['Width'],self['Height']
        blocks_w = math.ceil(w['Image'] / float(w['Block']))
        blocks_h = math.ceil(h['Image'] / float(h['Block']))
        count = long(blocks_w * blocks_h)
        return dyn.array(self.IMAGEBLOCKV2, count)

    def __IFrameImage(self):
        w,h = self['Width'],self['Height']
        blocks_w = math.ceil(w['Image'] / float(w['Block']))
        blocks_h = math.ceil(h['Image'] / float(h['Block']))
        count = long(blocks_w * blocks_h)
        return dyn.array(self.IMAGEBLOCKV2, count)

    _fields_ = [
        (SCREENVIDEOPACKET.Dim, 'Width'),
        (SCREENVIDEOPACKET.Dim, 'Height'),
        (Flags, 'Flags'),
        (lambda s: s['Flags'].li['HasPaletteInfo'] and SCREENVIDEOPACKET.IMAGEBLOCK or ptype.block, 'PaletteInfo'),
        (__ImageBlocks, 'ImageBlocks'),
        (__IFrameImage, 'IFrameImage'),
    ]

@VideoPacketData.define
class AVCVIDEOPACKET(pstruct.type):
    """AVC"""
    type = 7
    def __Data(self):
        h = self.getparent(StreamTag)['Header']
        t = h['AVCPacketType'].int()
        if t == 0:
            # FIXME: ISO 14496-15, 5.2.4.1
            return AVCDecoderConfigurationRecord
        elif t == 1:
            # FIXME: avcC
            return NALU
        return ptype.block

    _fields_ = [
        (__Data, 'Data')
    ]

### SCRIPTDATA
class SCRIPTDATAVALUE(pstruct.type):
    def __ScriptDataValue(self):
        t = self['Type'].li.int()
        return SCRIPTDATATYPE.withdefault(t, type=t)
    _fields_ = [
        (UI8,'Type'),
        (__ScriptDataValue, 'Value'),
    ]
    def summary(self):
        return '{:s}({:d})/{:s}'.format(self['Value'].classname(), self['Type'].int(), self['Value'].summary())
    repr = summary

class SCRIPTDATATYPE(ptype.definition): cache = {}

class SCRIPTDATASTRING(pstruct.type):
    _fields_ = [(UI16,'StringLength'),(lambda s:dyn.clone(STRING,length=s['StringLength'].li.int()),'StringData')]
    def summary(self):
        return self['StringData'].summary()
    repr = summary

class SCRIPTDATAOBJECTPROPERTY(pstruct.type):
    _fields_ = [(SCRIPTDATASTRING,'Name'),(SCRIPTDATAVALUE,'Value')]
    def summary(self):
        return '{!r}={!r}'.format(self['Name'].str(), self['Value'].str())
    repr = summary

# FIXME
@TagBody.define
class ScriptTagBody(pstruct.type):
    type = 18
    _fields_ = [(SCRIPTDATAVALUE,'Name'),(SCRIPTDATAVALUE,'Value')]
    def summary(self):
        return 'Name:{:s} Value:{:s}'.format(self['Name'].summary(), self['Value'].summary())
    repr = summary

@SCRIPTDATATYPE.define
class DOUBLE(DOUBLE):
    type = 0
@SCRIPTDATATYPE.define
class UI8(UI8):
    type = 1
@SCRIPTDATATYPE.define
class SCRIPTDATASTRING(SCRIPTDATASTRING):
    type = 2
@SCRIPTDATATYPE.define
class SCRIPTDATAOBJECT(parray.terminated):
    type = 3
    _object_ = SCRIPTDATAOBJECTPROPERTY
    def isTerminator(self, value):
        return type(value['Value'].li['Value']) == SCRIPTDATAOBJECTEND
        #return value['PropertyName'].li['StringLength'] == 0 and value['PropertyValue'].li['Type'].int() == SCRIPTDATAOBJECTEND.type
    def summary(self):
        return repr([ x.summary() for x in self ])
    repr = summary

@SCRIPTDATATYPE.define
class UI16(UI16):
    type = 7
@SCRIPTDATATYPE.define
class SCRIPTDATAECMAARRAY(pstruct.type):
    type = 8
    _fields_ = [
        (UI32,'EcmaArrayLength'),
        (SCRIPTDATAOBJECT, 'Variables'),
    ]
@SCRIPTDATATYPE.define
class SCRIPTDATAOBJECTEND(ptype.type):
    type = 9
@SCRIPTDATATYPE.define
class SCRIPTDATASTRICTARRAY(pstruct.type):
    type = 10
    _fields_ = [(UI32,'StrictArrayLength'),(lambda s:dyn.clone(SCRIPTDATAVALUE,length=s['StrictArrayLength'].li.int()),'StrictArrayValue')]
    def summary(self):
        return '{!r}'.format([x.summary() for x in self['StrictArrayValue']])
    repr = summary

@SCRIPTDATATYPE.define
class SCRIPTDATADATE(pstruct.type):
    type = 11
    _fields_ = [(DOUBLE,'DateTime'),(SI16,'LocalDateTimeOffset')]
    def summary(self):
        return 'DataTime:{:s} LocalDateTimeOffset:{:d}'.format(self['DateTime'].summary(), self['LocalDateTimeOffset'].int())
    repr = summary

@SCRIPTDATATYPE.define
class SCRIPTDATALONGSTRING(pstruct.type):
    type = 12
    _fields_ = [
        (UI32, 'StringLength'),
        (lambda s: dyn.clone(STRING,length=s['StringLength'].li.int()), 'StringData'),
    ]

    def summary(self):
        return self['StringData'].str()
    repr = summary

### Structures
class StreamTag(pstruct.type):
    def __Header(self):
        base = self.getparent(FLVTAG)
        t = base['Type'].li['TagType']
        return TagHeader.withdefault(t, type=t)

    def __FilterParams(self):
        base = self.getparent(FLVTAG)
        return FilterParams if base['Type'].li['Filter'] == 1 else ptype.undefined

    def __Body(self):
        base = self.getparent(FLVTAG)
        t = base['Type'].li['TagType']
        return TagBody.withdefault(t, type=t, length=self.DataSize())

    def DataSize(self):
        base = self.getparent(FLVTAG)
        sz = base['DataSize'].li.int()
        ex = self['Header'].li.size() + self['FilterParams'].li.size()
        return sz - ex

    _fields_ = [
        (__Header, 'Header'),
        (__FilterParams, 'FilterParams'),
        (__Body, 'Body'),
    ]

class EncryptionTagHeader(pstruct.type):
    _fields_ = [
        (UI8, 'NumFilters'),
        (STRING, 'FilterName'),
        (UI24, 'Length'),
    ]
class EncryptionFilterParams(pstruct.type):
    _fields_ = [(dyn.array(UI8,16), 'IV')]
class SelectiveEncryptionFilterParams(pbinary.struct):
    _fields_ = [(1,'EncryptedAU'),(7,'Reserved'),(lambda s: dyn.clone(pbinary.array,length=16,_object_=8),'IV')]

class FilterParams(pstruct.type):
    def __FilterParams(self):
        header = self.getparent(EncryptionTagHeader)
        filtername = header['FilterName'].li.str()
        if filtername == 'Encryption':
            return EncryptionFilterParams
        if filtername == 'SE':
            return SelectiveEncryptionFilterParams
        return ptype.undefined

    _fields_ = [
        (__FilterParams, 'FilterParams'),
    ]

class FLVTAG(pstruct.type):
    class Type(pbinary.struct):
        _fields_ = [(2,'Reserved'),(1,'Filter'),(5,'TagType')]
        def summary(self):
            return 'TagType:{:d} {:s}Reserved:{:d}'.format(self['TagType'], 'Filtered ' if self['Filter'] else '', self['Reserved'])

    def __Extra(self):
        sz = self['DataSize'].li.int()
        ts = self['Stream'].li.size()
        return dyn.block(sz-ts)

    _fields_ = [
        (Type, 'Type'),
        (UI24, 'DataSize'),
        (UI24, 'Timestamp'),
        (UI8, 'TimestampExtended'),
        (UI24, 'StreamID'),
        (StreamTag, 'Stream'),
        (__Extra, 'Extra'),
    ]

### file types
class File(pstruct.type):
    class Header(pstruct.type):
        class TypeFlags(pbinary.struct):
            _fields_ = [(5,'Reserved(0)'),(1,'Audio'),(1,'Reserved(1)'),(1,'Video')]
            def summary(self):
                res = []
                if self['Audio']: res.append('Audio')
                if self['Video']: res.append('Video')
                if self['Reserved(1)'] or self['Reserved(0)']: res.append('Reserved?')
                return '/'.join(res)
        def __Padding(self):
            sz = self['DataOffset'].li.int()
            return dyn.block(sz - 9)
        _fields_ = [
            (dyn.array(UI8,3), 'Signature'),
            (UI8, 'Version'),
            (TypeFlags, 'TypeFlags'),
            (UI32, 'DataOffset'),
            (__Padding, 'Padding'),
        ]

    def __Padding(self):
        h = self['Header'].li
        sz = h['DataOffset'].int()
        return dyn.block(sz - h.size())

    class Body(parray.block):
        class _object_(pstruct.type):
            _fields_ = [
                (UI32, 'PreviousTagSize'),
                (FLVTAG, 'Tag'),
            ]

    def __Body(self):
        ex = self['Header'].li['DataOffset'].int()
        return dyn.clone(self.Body, blocksize=lambda s:self.source.size() - ex)

    _fields_ = [
        (Header, 'Header'),
        (__Body, 'Body'),
    ]

if __name__ == '__main__':
    import ptypes,swf.flv as flv
    ptypes.setsource(ptypes.prov.file('c:/users/user/Documents/blah.flv',mode='rb'))
    reload(flv)
    a = flv.File()
    a = a.l
    print a['Header']['TypeFlags']
    print a['Header']
    print a['Header']['Padding'].hexdump()
    print a['Body'][0]['Tag']
    print a['Body'][0]['Tag']['TagData']

