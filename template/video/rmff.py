import ptypes,logging
from ptypes import *
# ripped from https://common.helixcommunity.org/2003/HCS_SDK_r5/htmfiles/rmff.htm

class UINT32( pint.bigendian(pint.uint32_t) ): pass
class UINT16( pint.bigendian(pint.uint16_t) ): pass
class UINT8( pint.bigendian(pint.uint8_t) ): pass
class INT32( pint.bigendian(pint.int32_t) ): pass
class ULONG32( pint.bigendian(pint.uint32_t) ): pass

class object_id(UINT32):
    def str(self):
        return self.serialize()

    def details(self):
        return self.summary()

class Str8(pstruct.type):
    _fields_ = [
        (UINT8, 'len'),
        (lambda s: dyn.clone(pstr.string, length=s['len'].li.int()), 's')
    ]
    def __str__(self):
        return str(self['s'])

### General Types with record lookups
class RealMedia_Header(pstruct.type):
    def __object(self):
        id, ver = self['object_id'].li.serialize(), self['object_version'].li.int()
        t = (ver, id)
        return self.Media_Type.withdefault(t, type=t, length=self['size'].li.int() - 10)

    def blocksize(self):
        return self['size'].li.int()

    _fields_ = [
        (object_id, 'object_id'),
        (UINT32, 'size'),
        (UINT16, 'object_version'),
        (__object, 'object'),
#        (__extra, 'extra')
    ]

    class Media_Type(ptype.definition):
        cache = {}

class RealMedia_Structure(pstruct.type):
    _fields_ = [
        (ULONG32, 'size'),
        (UINT16, 'object_version'),
        (lambda s: s.Media_Type.withdefault(s['object_version'].li.int(), type=s['object_version'].int()), 'object'),
    ]
    class Media_Type(ptype.definition):
        pass

class RealMedia_Record(pstruct.type):
    _fields_ = [
        (UINT16, 'object_version'),
        (lambda s: s.Media_Type.withdefault(s['object_version'].li.int(), type=s['object_version'].int()), 'object')
    ]
    class Media_Type(ptype.definition):
        pass

# http://git.ffmpeg.org/?p=ffmpeg;a=blob;f=libavformat/rmdec.c;h=436a7e08f2a593735d50e15ba38ed34c5f8eede1;hb=HEAD
class Type_Specific_RealAudio(pstruct.type):
    def __object(self):
        ver = self['object_version'].li.int()
        return self.Media_Type.withdefault(ver, type=ver)

    def __codec(self):
        version, fourcc = self['object_version'].li.int(), self['object'].li.codec()
        t = (version, fourcc)
        type = self.Audio_Codec.withdefault(t, type=t, length=self['i_codec'].li.int())
        return dyn.clone(type, blocksize=lambda s: self['i_codec'].li.int())

    _fields_ = [
        (object_id, 'object_id'),
        (UINT16, 'object_version'),
        (__object, 'object'),
        (UINT32, 'i_codec'),
        (__codec, 'codec')
    ]

    class Media_Type(ptype.definition):
        attribute,cache = 'object_version',{}

    class Audio_Codec(ptype.definition):
        cache = {}

class Type_Specific_RealVideo(pstruct.type):
    def __object(self):
        # XXX: just a check that doesn't belong here
        v = self['version'].li.int()
        if v != 0:
            raise NotImplementedError('Unknown Video Type Version at %x: %x'% (self.getoffset(), v))

        id = self['id'].li.serialize()
        return self.Video_Codec.withdefault(id, type=id)

    def __unknown(self):
        fields = (n for _,n in self._fields_[:-1])
        return dyn.block(s['size'].li.int() - sum(self[n].li.size() for n in fields))

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
        (__unknown, 'unknown'),
    ]

    class Video_Codec(ptype.definition):
        cache = {}

### type specific codec data
@Type_Specific_RealAudio.Audio_Codec.define
class Codec_Data_cook_v4(pstruct.type):
    type = (4, 'cook')
    _fields_ = [
        (UINT16, 'unknown_0'),
        (UINT8, 'unknown_2'),
        (ULONG32, 'length'),
        (lambda s: dyn.block(s['length'].li.int()), 'data')
    ]

@Type_Specific_RealAudio.Audio_Codec.define
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

        (UINT16, 'unused'),
        (UINT8, 'subband_start'),
        (UINT8, 'vlc_bits'),

        (ULONG32, 'channel_mask'),
    ]

@Type_Specific_RealVideo.Video_Codec.define
class Codec_Data_RV30(pstruct.type):
    type = 'RV30'
    _fields_ = [
    ]

@Type_Specific_RealVideo.Video_Codec.define
class Codec_Data_RV20(pstruct.type):
    type = 'RV20'
    _fields_ = [
        (UINT16, 'frame size count'),
        (UINT16, 'unknown[1]'),
        (UINT32, 'colorinfo'),
        (lambda s: dyn.array(UINT16, s['frame size count'].li.int()), 'framesize'),
    ]

### type specific
@Type_Specific_RealAudio.Media_Type.define
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

@Type_Specific_RealAudio.Media_Type.define
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
#        print(hex(self.getoffset()))
#        print(self['desc1'], self['desc2'])
        return self['desc2'].serialize()

# FIXME
class Type_Specific_vAny_Audio(Type_Specific_v4_Audio): pass
Type_Specific_RealAudio.Media_Type.default = Type_Specific_vAny_Audio

@Type_Specific_RealAudio.Media_Type.define
class Type_Specific_v5_Audio(pstruct.type):
    object_version = 5
    _fields_ = [
        (UINT16, 'unused[0]'),
        (UINT32, '.ra5'),
        (UINT32, 'data_size'),
        (UINT16, 'version2'),

        (UINT32, 'header_size'),

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

        (dyn.block(3), 'unknown[18]'),
        (UINT8, 'unknown[19]'),

#        (UINT32, 'unknown[18]'),
#        (UINT32, 'unknown[19]'),
#        (UINT32, 'unknown[1a]'),
#        (UINT16, 'unknown[1b]'),
    ]

    def codec(self):
        return self['codec'].serialize()

@Type_Specific_RealAudio.Media_Type.define
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

### sub-headers
@RealMedia_Header.Media_Type.define
class RealMedia_File_Header_v0(pstruct.type):
    type = (0, '.RMF')
    _fields_ = [
        (UINT32, 'file_version'),
        (UINT32, 'num_headers'),
    ]

@RealMedia_Header.Media_Type.define
class RealMedia_File_Header_v1(RealMedia_File_Header_v0):
    type = (1, '.RMF')

@RealMedia_Header.Media_Type.define
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

@RealMedia_Header.Media_Type.define
class RealMedia_MediaProperties_Header_v0(pstruct.type):
    type = (0, 'MDPR')

    def __type_specific_data(self):
        mimetype = self['mime_type'].li.str()
        typesize = self['type_specific_len'].li.int()
        if mimetype == 'video/x-pn-realvideo':
            return dyn.clone(Type_Specific_RealVideo, blocksize=lambda s: typesize)
        elif mimetype == 'audio/x-pn-realaudio':
            return dyn.clone(Type_Specific_RealAudio, blocksize=lambda s: typesize)
        elif mimetype == 'logical-fileinfo':
            return LogicalStream
        logging.warning('%s:%s: Unable to identify mimetype "%s"'%(self.__module__, self.shortname(), mimetype))
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
        (lambda s: dyn.clone(pstr.string, length=s['stream_name_size'].li.int()), 'stream_name'),
        (UINT8, 'mime_type_size'),
        (lambda s: dyn.clone(pstr.string, length=s['mime_type_size'].li.int()), 'mime_type'),
        (UINT32, 'type_specific_len'),
#        (lambda s: dyn.block(s['type_specific_len'].li.int()), 'type_specific_data'),
        (__type_specific_data, 'type_specific_data')
    ]

@RealMedia_Header.Media_Type.define
class RealMedia_Content_Description_Header(pstruct.type):
    type = (0, 'CONT')

    _fields_ = [
        (UINT16, 'title_len'),
        (lambda s: dyn.clone(pstr.string, length=s['title_len'].li.int()), 'title'),
        (UINT16, 'author_len'),
        (lambda s: dyn.clone(pstr.string, length=s['author_len'].li.int()), 'author'),
        (UINT16, 'copyright_len'),
        (lambda s: dyn.clone(pstr.string, length=s['copyright_len'].li.int()), 'copyright'),
        (UINT16, 'comment_len'),
        (lambda s: dyn.clone(pstr.string, length=s['comment_len'].li.int()), 'comment'),
    ]

@RealMedia_Header.Media_Type.define
class RealMedia_Data_Chunk_Header(pstruct.type):
    type = (-1, 'DATA')
    _fields_ = [
        (UINT32, 'num_packets'),
        (UINT32, 'next_data_header'),
        (lambda s: dyn.array( MediaMedia_Packet_Header_v0, s['num_packets'].li.int() ), 'packets')
    ]

@RealMedia_Header.Media_Type.define
class RealMedia_Index_Chunk_Header(pstruct.type):
    type = (0, 'INDX')
    _fields_ = [
        (UINT32, 'num_indices'),
        (UINT16, 'stream_number'),
        (UINT32, 'next_index_header'),
        (lambda s: dyn.array( Index_Packet_Record, s['num_indices'].li.int() ), 'packets')
    ]

@RealMedia_Header.Media_Type.define
class RealMedia_Data_Chunk_Header(pstruct.type):
    type = (0, 'DATA')
    _fields_ = [
        (UINT32, 'num_packets'),
        (UINT32, 'next_data_header'),
        (lambda s: dyn.array(Media_Packet_Record, s['num_packets'].li.int()), 'packets')
    ]

### logical stream structures
class LogicalStream(RealMedia_Structure):
    class Media_Type(ptype.definition):
        attribute,cache = 'object_version',{}

@LogicalStream.Media_Type.define
class LogicalStream_v0(pstruct.type):
    object_version = 0
    _fields_ = [
        (UINT16, 'num_physical_streams'),
        (lambda s: dyn.array(UINT16, s['num_physical_streams'].li.int()), 'physical_stream_numbers'),
        (lambda s: dyn.array(ULONG32, s['num_physical_streams'].li.int()), 'data_offsets'),
        (UINT16, 'num_rules'),
        (lambda s: dyn.array(UINT16, s['num_rules'].li.int()), 'rule_to_physical_stream_number_map'),
        (UINT16, 'num_properties'),
        (lambda s: dyn.array(NameValueProperty, s['num_properties'].li.int()), 'properties'),
    ]

### name value property structures
class NameValueProperty(RealMedia_Structure):
    class Media_Type(ptype.definition):
        cache = {}

@NameValueProperty.Media_Type.define
class NameValueProperty_v0(pstruct.type):
    type = 0
    def __value_data(self):
        v = self['type'].li.int()
        l = self['value_length'].li.int()

        if v == 0:
            assert l == 4
            return UINT32
        elif v == 2:
            return dyn.clone(pstr.string, length=l)
        else:
            logging.warning('%s:%s: Unknown Value type %x size +%x'%(self.__module__, self.p.shortname(), v, l))
        return dyn.block(l)

    _fields_ = [
        (UINT8, 'name_length'),
        (lambda s: dyn.clone(pstr.string, length=s['name_length'].li.int()), 'name'),
        (INT32, 'type'),
        (UINT16, 'value_length'),
        (__value_data, 'value_data')
    ]

### data packets records
class Media_Packet_Record(RealMedia_Record):
    class Media_Type(ptype.definition):
        cache = {}

@Media_Packet_Record.Media_Type.define
class Media_Packet_Header_v0(pstruct.type):
    type = 0

    PN_RELIABLE_FLAG = 0x0001
    PN_KEYFRAME_FLAG = 0x0002
    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT8, 'packet_group'),
        (UINT8, 'flags'),
        (lambda s: dyn.block(s['length'].li.int()-12), 'data'),
    ]

@Media_Packet_Record.Media_Type.define
class Media_Packet_Header_v1(pstruct.type):
    type = 1

    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT16, 'asm_rule'),
        (UINT8, 'asm_flags'),
        (lambda s: dyn.block(s['length'].li.int()-13), 'data'),
    ]

### index packet records
class Index_Packet_Record(RealMedia_Record):
    class Media_Type(ptype.definition):
        cache = {}

@Index_Packet_Record.Media_Type.define
class IndexRecord_v0(pstruct.type):
    type = 0
    _fields_ = [
        (UINT32, 'timestamp'),
        (UINT32, 'offset'),
        (UINT32, 'packet_count_for_this_packet'),
    ]

###
class File(parray.terminated):
    _object_ = RealMedia_Header

    def isTerminator(self, value):
        l = len(self.value)
        if l > 0:
            return l > self.value[0]['object']['num_headers'].int() + 1
        return False

if __name__ == '__main__':
    import sys
    import ptypes,video.rmff as rmff
    ptypes.setsource( ptypes.file(sys.argv[1], mode='rb') )

    self = rmff.File()
    z = self.l
    print(len(self.value))

#    offset = 0x16f
#    print(self.at(offset))

#    typespecific = self[3]['object']['type_specific_data']

    mdpr = [x for x in self.traverse(filter=lambda x: type(x) == rmff.RealMedia_Header) if x['object_id'].serialize() == 'MDPR']
    for x in mdpr:
        print(x.__name__, x['object']['mime_type'])
