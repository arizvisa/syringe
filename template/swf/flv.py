import ptypes
from primitives import *
from ptypes import *

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
class AACAUDIODATA(pstruct.type):
    _fields_ = [(lambda s: AudioSpecificConfig if s.getparent(FLVTAG)['TagHeader'].li['AACPacketType'] == 0 else ptype.block, 'Data')]
@TagBody.define
class AudioTagBody(pstruct.type):
    type = 8
    def __Data(self):
        h = self.getparent(FLVTAG)['TagHeader'].li
        if h['SoundFormat'] == 10:
            return AACAUDIODATA
        return ptype.block
    _fields_ = [(__Data, 'Data')]

### VIDEODATA
class AVCVIDEOPACKET(pstruct.type):
    _fields_ = [(lambda s: AVCDecoderConfigurationRecord if s.getparent(FLVTAG)['VideoTagHeader'].li['AVCPacketType'] == 0 else ptype.block, 'Data')]
@TagHeader.define
class VideoTagHeader(pstruct.type):
    type = 9
    class Type(pbinary.struct):
        _fields_ = [(4, 'FrameType'), (4, 'CodecID')]
    _fields_ = [
        (Type, 'Type'),
        (lambda s: UI8 if s['Type'].li['CodecID'] == 7 else pint.uint_t, 'AVCPacketType'),
        (lambda s: SI24 if s['Type'].li['CodecID'] == 7 else pint.uint_t, 'CompositionTime'),
    ]

@TagBody.define
class VideoTagBody(pstruct.type):
    type = 9
    def __Data(self):
        h = self.getparent(FLVTAG)['VideoTagHeader'].li
        t = h['Type']
        if t['FrameType'] == 5:
            return UI8
        res = {2:H263VIDEOPACKET,3:SCREENVIDEOPACKET,4:VP6FLVVIDEOPACKET,5:VP6FLVALPHAVIDEOPACKET,6:SCREENV2VIDEOPACKET,7:AVCVIDEOPACKET}
        return res[t['CodecID']]
    _fields_ = [(__Data,'Data')]

### SCRIPTDATA
class SCRIPTDATAVALUE(pstruct.type):
    def __ScriptDataValue(self):
        t = self['Type'].li.num()
        return SCRIPTDATATYPE.get(t)
    _fields_ = [
        (UI8,'Type'),
        (__ScriptDataValue, 'ScriptDataValue'),
    ]

class SCRIPTDATATYPE(ptype.definition): cache = {}

class SCRIPTDATASTRING(pstruct.type):
    _fields_ = [(UI16,'StringLength'),(lambda s:dyn.clone(STRING,length=s['StringLength'].li.num()),'StringData')]

class SCRIPTDATAOBJECTPROPERTY(pstruct.type):
    _fields_ = [(SCRIPTDATASTRING,'PropertyName'),(SCRIPTDATAVALUE,'PropertyValue')]

@TagBody.define
class ScriptTagBody(pstruct.type):
    type = 18
    _fields_ = [(SCRIPTDATAVALUE,'Name'),(SCRIPTDATAVALUE,'Value')]

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
        return type(value['PropertyValue'].li['ScriptDataValue']) == SCRIPTDATAOBJECTEND
        #return value['PropertyName'].li['StringLength'] == 0 and value['PropertyValue'].li['Type'].num() == SCRIPTDATAOBJECTEND.type
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
    _fields_ = [(UI32,'StrictArrayLength'),(lambda s:dyn.clone(SCRIPTDATAVALUE,length=s['StrictArrayLength'].li.num()),'StrictArrayValue')]
@SCRIPTDATATYPE.define
class SCRIPTDATADATE(pstruct.type):
    type = 11
    _fields_ = [(DOUBLE,'DateTime'),(SI16,'LocalDateTimeOffset')]
@SCRIPTDATATYPE.define
class SCRIPTDATALONGSTRING(pstruct.type):
    type = 12
    _fields_ = [
        (UI32, 'StringLength'),
        (lambda s: dyn.clone(STRING,length=s['StringLength'].li.num()), 'StringData'),
    ]

### Structures
class Tag(pstruct.type):
    def __Header(self):
        base = self.getparent(FLVTAG)
        t = base['Type'].li['TagType']
        return TagHeader.get(t)

    def __FilterParams(self):
         return FilterParams if s['Type'].li['Filter'] == 1 else ptype.undefined

    def __Data(self):
        base = self.getparent(FLVTAG)
        sz = base['DataSize'].li.num()
        ex = base['Header'].li.size() + base['FilterParams'].li.size()
        t = base['Type'].li['TagType']
        return TagBody.get(t, length=sz - ex)

    _fields_ = [
        (__Header, 'Header'),
        (__FilterParams, 'FilterParams'),
        (__Data, 'Data'),
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
        
    _fields_ = [
        (__FilterParams, 'FilterParams'),
    ]

### FLVTAG
class FLVTAG(pstruct.type):
    class Type(pbinary.struct):
        _fields_ = [(2,'Reserved'),(1,'Filter'),(5,'TagType')]

    def __Tag(self):
        sz = self['DataSize'].li.num()
        return dyn.block(sz)

    _fields_ = [
        (Type, 'Type'),
        (UI24, 'DataSize'),
        (UI24, 'Timestamp'),
        (UI8, 'TimestampExtended'),
        (UI24, 'StreamID'),
        (__Tag, 'Tag'),
    ]

### file types
class File(pstruct.type):
    class Header(pstruct.type):
        class TypeFlags(pbinary.struct):
            _fields_ = [(5,'Reserved(0)'),(1,'Audio'),(1,'Reserved(1)'),(1,'Video')]
        def __Padding(self):
            sz = self['DataOffset'].li.num()
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
        sz = h['DataOffset'].num()
        return dyn.block(sz - h.size())

    class Body(parray.block):
        class _object_(pstruct.type):
            _fields_ = [
                (UI32, 'PreviousTagSize'),
                (FLVTAG, 'Tag'),
            ]

    def __Body(self):
        ex = self['Header'].li['DataOffset'].num()
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

