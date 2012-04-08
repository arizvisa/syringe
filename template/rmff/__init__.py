import ptypes,logging
from ptypes import *
# ripped from https://common.helixcommunity.org/2003/HCS_SDK_r5/htmfiles/rmff.htm

class UINT32( pint.bigendian(pint.uint32_t) ): pass
class UINT16( pint.bigendian(pint.uint16_t) ): pass
class UINT8( pint.bigendian(pint.uint8_t) ): pass
class INT32( pint.bigendian(pint.int32_t) ): pass
class ULONG32( pint.bigendian(pint.uint32_t) ): pass

class Str8(pstruct.type):
    _fields_ = [
        (UINT8, 'len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['len'].l)), 's')
    ]
    def __str__(self):
        return str(self['s'])

### General Types
class RealMedia_Header(pstruct.type):
    def __object(self):
        global realmedia_header
        id,ver = self['object_id'].l.serialize(),int(self['object_version'].l)

        try:
            res = realmedia_header.lookup((ver,id))
        except KeyError:
            logging.warn("%s:%s:(id:%s,ver:%d): Unable to identify header type at offset %x"%(self.__module__, self.shortname(), id, ver, self.getoffset()))
            res = dyn.block( int(self['size'].l) - 10 )
        return res

    def __extra(self):
        l = int(self['size'].l)
        s = self['object'].size() + 4 + 4 + 2
        if l > s:
            id,ver = self['object_id'].serialize(),int(self['object_version'])
            logging.warn('%s:%s:(id:%s,ver:%x): Decoded only %d bytes at offset %x'%(self.__module__, self.shortname(), id, ver, l-s, self.getoffset()))
            return dyn.block( l - s )

        if s != l: 
            id,ver = self['object_id'].serialize(),int(self['object_version'])
            logging.warn('%s:%s:(id:%s,ver:%x): Attempted to read %x bytes past parent block at offset %x'%(self.__module__, self.shortname(), id, ver, s-l, self.getoffset()))

        return dyn.block(0)

    def blocksize(self):
        return int(self['size'])

    _fields_ = [
        (UINT32, 'object_id'),
        (UINT32, 'size'),
        (UINT16, 'object_version'),
        (__object, 'object'),
        (__extra, 'extra')
    ]

class RealMedia_Structure(pstruct.type):
    def getobject(self):
        ver = int(self['object_version'].l)
        return self._object_[ver]

    _fields_ = [
        (ULONG32, 'size'),
        (UINT16, 'object_version'),
        (getobject, 'object'),
    ]

class RealMedia_Record(pstruct.type):
    def getobject(self):
        ver = int(self['object_version'].l)
        return self._object_[ver]

    _fields_ = [
        (UINT16, 'object_version'),
        (getobject, 'object')
    ]

### non general types
class record(object):
    cache = None
    @classmethod
    def lookup(cls, id):
        return cls.cache[id]

    @classmethod
    def define(cls, type):
        assert type not in cls.cache
        cls.cache[type.type] = type
        return type

class realmedia_header(record): cache = {}

### type specific codec data
class codec(record): pass
class audio_codec(codec): cache = {}
class video_codec(codec): cache = {}

@audio_codec.define
class Codec_Data_cook_v4(pstruct.type):
    type = (4, 'cook')
    _fields_ = [
        (UINT16, 'unknown_0'),
        (UINT8, 'unknown_2'),
        (ULONG32, 'length'),
        (lambda s: dyn.block(int(s['length'].l)), 'data')
    ]

@audio_codec.define
class Codec_Data_cook_v5(pstruct.type):
    # taken from ffmpeg/libavcodec/cook.c
    type = (5, 'cook')

    MONO=0x1000001
    STEREO=0x1000002
    JOINT_STEREO=0x1000003
    MULTICHANNEL_COOK=0x2000000

    _fields_ = [
        (UINT32, 'cookversion'),
        (UINT16, 'samples_per_frame'),
        (UINT16, 'subbands'),
#        (UINT16, 'unknown_0'),
#        (UINT8, 'unknown_2'),
#        (UINT8, 'unknown_3'),
#        (ULONG32, 'length'),
#        (lambda s: dyn.block(int(s['length'].l)), 'data')
    ]

@video_codec.define
class Codec_Data_RV30(pstruct.type):
    type = 'RV30'
    _fields_ = [
    ]

@video_codec.define
class Codec_Data_RV20(pstruct.type):
    type = 'RV20'
    _fields_ = [
        (UINT16, 'frame size count'),
        (UINT16, 'unknown[1]'),
        (UINT32, 'colorinfo'),
        (lambda s: dyn.array(UINT16, s['frame size count'].l.int()), 'framesize'),
    ]

### type specific
# http://git.ffmpeg.org/?p=ffmpeg;a=blob;f=libavformat/rmdec.c;h=436a7e08f2a593735d50e15ba38ed34c5f8eede1;hb=HEAD

class Type_Specific_v3_Audio(pstruct.type):
    object_version = 3
    _fields_ = [
        (dyn.block(14), 'unknown[1]'),  # XXX: this might not be right
        (Str8, 'metadata'),
        (UINT8, 'unknown[3]'),
        (Str8, 'fourcc'),
    ]

    def codec(self):
        return self['fourcc'].serialize()

class Type_Specific_v4_Audio(pstruct.type):
    object_version = 4
    _fields_ = [
        (UINT16, 'unused[0]'),
        (UINT32, '.ra4'),
        (UINT32, 'data_size'),
        (UINT16, 'version2'),
        (UINT32, 'header_size'),
        (UINT16, 'flavor'),
        (UINT32, 'coded_frame_size'),
        (UINT32, 'unknown[7]'),
        (UINT32, 'unknown[8]'),
        (UINT32, 'unknown[9]'),
        (UINT16, 'sub_packet_h'),
        (UINT16, 'frame_size'),
        (UINT16, 'sub_packet_size'),
        (UINT16, 'sample_rate'),
        (UINT32, 'unknown[f]'),
        (UINT16, 'channels'),
        (Str8, 'desc1'),
        (Str8, 'desc2'),
    ]
    def codec(self):
#        print hex(self.getoffset())
#        print self['desc1'], self['desc2']
        return self['desc2'].serialize()

class Type_Specific_vAny_Audio(Type_Specific_v4_Audio): pass

class Type_Specific_v5_Audio(pstruct.type):
    object_version = 5
    _fields_ = [
        (UINT16, 'unused[0]'),
        (UINT32, '.ra5'),
        (UINT32, 'data_size'),
        (UINT16, 'version2'),

        (UINT16, 'header_size?'),
        (UINT16, 'header_size'),
#        (UINT32, 'header_size'),

        (UINT16, 'flavor'),
        (UINT32, 'coded_frame_size'),

        (UINT16, 'unknown[7]'),
        (UINT16, 'unknown[8]'),
        (UINT32, 'unknown[9]'),
        (UINT32, 'unknown[a]'),

        (UINT16, 'sub_packet_h'),
        (UINT16, 'frame_size'),
        (UINT16, 'sub_packet_size'),

        (UINT16, 'unknown[e]'),
        (UINT16, 'unknown[f]'),
        (UINT16, 'unknown[10]'),
        (UINT16, 'unknown[11]'),

        (UINT16, 'sample_rate'),
        (UINT16, 'unknown[13]'),
        (UINT16, 'bitpersample'),
        (UINT16, 'channels'),

        (UINT32, 'genr'),
        (dyn.block(4), 'codec'),

        (UINT32, 'unknown[18]'),
        (UINT32, 'unknown[19]'),
        (UINT32, 'unknown[1a]'),
        (UINT16, 'unknown[1b]'),
    ]

    def codec(self):
        return self['codec'].serialize()

class Type_Specific_v0_Audio(pstruct.type):
    object_version = 0

    _fields_ = [
        (UINT32, 'unknown[0]'),
        (UINT16, 'unknown[1]'),
        (UINT16, 'unknown[2]'),
        (UINT16, 'unknown[3]'),
        (UINT16, 'unknown[4]'),
        (Str8, 'unknown[5]'),
        (UINT16, 'unknown[6]'),
        (UINT32, 'unknown[7]'),
        (dyn.block(4), 'Auto?'),
        (dyn.block(4), 'fourcc'),
        # FIXME: I think this is really an array of structs that contains strings
    ]
    def codec(self):
        return self['fourcc'].serialize()

class Type_Specific_RealAudio(pstruct.type):
    _object_ = {
        0 : Type_Specific_v0_Audio,
        3 : Type_Specific_v3_Audio,
        4 : Type_Specific_v4_Audio,
        5 : Type_Specific_v5_Audio
    }

    def __object(self):
        ver = int(self['object_version'].l)
        try:
            return self._object_[ver]
        except KeyError:
            pass
        raise NotImplementedError( 'Unknown Type at %x: %x'% (self.getoffset(), ver))

    def __codec(self):
        fourcc = self['object'].l.codec()
        version = int(self['object_version'].l)

        try:
            type = audio_codec.lookup((fourcc, version))
            return dyn.clone(type, blocksize=lambda s: int(self['i_codec'].l))
        except KeyError:
            logging.warn('%s:%s: Unable to find codec "%s" version %d'%(self.__module__, self.shortname(), fourcc, version))

        return ptype.empty   #XXX

    _fields_ = [
        (UINT32, 'object_id'),
        (UINT16, 'object_version'),
        (__object, 'object'),
        (UINT32, 'i_codec'),
        (__codec, 'codec')
    ]

class Type_Specific_RealVideo(pstruct.type):
    def __object(self):
        # XXX: just a check that doesn't belong here
        v = self['version'].l.int()
        if v != 0:
            raise NotImplementedError('Unknown Video Type Version at %x: %x'% (self.getoffset(), v))

        id = self['id'].l.serialize()
        try:
            result = video_codec.lookup(id)
        except KeyError:
            logging.warn('%s:%s: Unable to find codec "%s"'%(self.__module__, self.shortname(), id))
            result = ptype.empty
        return result

    _fields_ = [
        (UINT16, 'version'),
        (UINT16, 'size'),
        (dyn.block(4), 'tag'),
        (dyn.block(4), 'id'),
        (UINT16, 'width'),
        (UINT16, 'height'),
        (UINT16, 'fps'),

        (dyn.block(4), 'unknown_block'),
        (UINT16, 'frame_rate'),
        (UINT16, 'unknown_u16'),
        
#        (dyn.block(8), 'unknown_block'),
        (__object, 'object'),
        (lambda s: dyn.block(s['size'].l.int() - s.size()), '__unknown'),
    ]
    
### sub-headers
@realmedia_header.define
class RealMedia_File_Header_v0(pstruct.type):
    type = (0, '.RMF')
    _fields_ = [
        (UINT32, 'file_version'),
        (UINT32, 'num_headers'),
    ]
    
@realmedia_header.define
class RealMedia_File_Header_v1(RealMedia_File_Header_v0):
    type = (1, '.RMF')

@realmedia_header.define
class RealMedia_Properties_Header_v0(pstruct.type):
    type = (0, 'PROP')

    _fields_ = [
        (UINT32, 'max_bit_rate'),
        (UINT32, 'avg_bit_rate'),
        (UINT32, 'max_packet_size'),
        (UINT32, 'avg_packet_size'),
        (UINT32, 'num_packets'),
        (UINT32, 'duration'),
        (UINT32, 'preroll'),
        (UINT32, 'index_offset'),
        (UINT32, 'data_offset'),
        (UINT16, 'num_streams'),
        (UINT16, 'flags'),
    ]

@realmedia_header.define
class RealMedia_MediaProperties_Header_v0(pstruct.type):
    type = (0, 'MDPR')

    def __type_specific_data(self):
        mimetype = self['mime_type'].l.str()
        typesize = self['type_specific_len'].l.int()
        if mimetype == 'video/x-pn-realvideo':
            return dyn.clone(Type_Specific_RealVideo, blocksize=lambda s: typesize)
        elif mimetype == 'audio/x-pn-realaudio':
            return dyn.clone(Type_Specific_RealAudio, blocksize=lambda s: typesize)
        logging.warn('%s:%s: Unable to identify mimetype "%s"'%(self.__module__, self.shortname(), mimetype))
        return dyn.block(typesize)

    _fields_ = [
        (UINT16, 'stream_number'),
        (UINT32, 'max_bit_rate'),
        (UINT32, 'avg_bit_rate'),
        (UINT32, 'max_packet_size'),
        (UINT32, 'avg_packet_size'),
        (UINT32, 'start_time'),
        (UINT32, 'preroll'),
        (UINT32, 'duration'),
        (UINT8, 'stream_name_size'),
        (lambda s: dyn.clone(pstr.string, length=int(s['stream_name_size'].l)), 'stream_name'),
        (UINT8, 'mime_type_size'),
        (lambda s: dyn.clone(pstr.string, length=int(s['mime_type_size'].l)), 'mime_type'),
        (UINT32, 'type_specific_len'),
#        (lambda s: dyn.block(int(s['type_specific_len'].l)), 'type_specific_data'),
        (__type_specific_data, 'type_specific_data')
    ]

@realmedia_header.define
class RealMedia_Content_Description_Header(pstruct.type):
    type = (0, 'CONT')

    _fields_ = [
        (UINT16, 'title_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['title_len'].l)), 'title'),
        (UINT16, 'author_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['author_len'].l)), 'author'),
        (UINT16, 'copyright_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['copyright_len'].l)), 'copyright'),
        (UINT16, 'comment_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['comment_len'].l)), 'comment'),
    ]

@realmedia_header.define
class RealMedia_Data_Chunk_Header(pstruct.type):
    type = (-1, 'DATA')
    _fields_ = [
        (UINT32, 'num_packets'),
        (UINT32, 'next_data_header'),
        (lambda s: dyn.array( Media_Packet_Header_v0, int(s['num_packets'].l) ), 'packets')
    ]

@realmedia_header.define
class RealMedia_Index_Chunk_Header(pstruct.type):
    type = (0, 'INDX')
    _fields_ = [
        (UINT32, 'num_indices'),
        (UINT16, 'stream_number'),
        (UINT32, 'next_index_header'),
        (lambda s: dyn.array( IndexRecord, int(s['num_indices'].l) ), 'packets')
    ]

### logical stream structures
class LogicalStream_v0(RealMedia_Structure):
    object_version = 0
    _fields_ = [
        (UINT16, 'num_physical_streams'),
        (lambda s: dyn.array(UINT16, int(s['num_physical_streams'].l)), 'physical_stream_numbers'),
        (lambda s: dyn.array(ULONG32, int(s['num_physical_streams'].l)), 'data_offsets'),
        (UINT16, 'num_rules'),
        (lambda s: dyn.array(UINT16, int(s['num_rules'].l)), 'rule_to_physical_stream_number_map'),
        (UINT16, 'num_properties'),
        (lambda s: dyn.array(NameValueProperty, int(s['num_properties'].l)), 'properties'),
    ]

class LogicalStream(RealMedia_Structure):
    _object_ = { 0 : LogicalStream_v0 }

class NameValueProperty_v0(pstruct.type):
    _fields_ = [
        (UINT8, 'name_length'),
        (lambda s: dyn.clone(pstr.string, length=int(s['name_length'].l)), 'name'),
        (INT32, 'type'),
        (UINT16, 'value_length'),
        (lambda s: dyn.block(int(s['value_length'])), 'value_data')
    ]

class NameValueProperty(RealMedia_Structure):
    _object_ = { 0 : NameValueProperty_v0 }

### data packets
class Media_Packet_Header_v0(pstruct.type):
    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT8, 'packet_group'),
        (UINT8, 'flags'),
        (lambda s: dyn.block( int(s['length'].l) ), 'data'),
    ]

class Media_Packet_Header_v1(pstruct.type):
    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT16, 'asm_rule'),
        (UINT8, 'asm_flags'),
        (lambda s: dyn.block( int(s['length'].l) ), 'data'),
    ]

class Media_Packet_Header(RealMedia_Record):
    _object_ = { 0 : Media_Packet_Header_v0, 1 : Media_Packet_Header_v1 }

### index records
class IndexRecord_v0(pstruct.type):
    _fields_ = [
        (UINT32, 'timestamp'),
        (UINT32, 'offset'),
        (UINT32, 'packet_count_for_this_packet'),
    ]

class IndexRecord(RealMedia_Record):
    _object_ = { 0 : IndexRecord_v0 }

###
class File(parray.terminated):
    _object_ = RealMedia_Header

    def isTerminator(self, value):
        l = len(self.value)
        if l > 0:
            return l > int(self.value[0]['object']['num_headers']) + 1
        return False

if __name__ == '__main__':
    ptypes.setsource( provider.file('./poc.rma', mode='rb') )

    self = File()   
    self.l
    print len(self.value)

    offset = 0x16f
    print self.at(offset)

    typespecific = self[3]['object']['type_specific_data']
