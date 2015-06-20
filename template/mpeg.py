from ptypes import *
pbinary.setbyteorder( pbinary.bigendian )

class layer(ptype.definition):
    cache = {}
    class unknown(pbinary.array):
        _object_ = length = 0

###
@layer.define
class sequence_header(pbinary.struct):
    type = 0x00001b3
    _fields_ = [
        (12, 'horizontal_size'),
        (12, 'vertical_size'),
        (4, 'pel_aspect_ratio'),
        (4, 'picture_rate'),
        (18, 'bit_rate'),
        (1, 'marker_bit'),
        (10, 'vbv_buffer_size'),
        (1, 'constrained_parameters_flag'),
        (1, 'load_intra_quantizer_matrix'),
        (lambda s: (0, 8*64)[s['load_intra_quantizer_matrix'] == 1], 'intra_quantizer_matrix'),
        (1, 'load_non_intra_quantizer_matrix'),
        (lambda s: (0, 8*64)[s['load_non_intra_quantizer_matrix'] == 1], 'non_intra_quantizer_matrix'),
    ]

@layer.define
class sequence_end_code(pbinary.struct):
    type = 0x1b7
    _fields_ = []

@layer.define
class end_code(sequence_end_code):
    type = 0x1b8

@layer.define
class group_of_pictures(pbinary.struct):
    type = 0x1b8
    _fields_ = [
        (25, 'time_code'),
        (1, 'closed_gop'),
        (1, 'broken_link'),
    ]

@layer.define
class picture(pbinary.struct):
    type = 0x100

    class extra_bit(pbinary.struct):
        _fields_ = [(1,'extra_bit_picture'), (8, 'extra_information_picture')]

    _fields_ = [
        (10, 'temporal_reference'),
        (3, 'picture_coding_type'),
        (16, 'vbv_delay'),
        (lambda s: (0,1)[s['picture_coding_type'] in (2,3)], 'full_pel_forward_vector'),
        (lambda s: (0,3)[s['picture_coding_type'] in (2,3)], 'forward_f_code'),
        (lambda s: (0,1)[s['picture_coding_type'] == 3], 'full_pel_backward_vector'),
        (lambda s: (0,3)[s['picture_coding_type'] == 3], 'backward_f_code'),
        (dyn.clone(pbinary.terminatedarray, _object_=extra_bit, isTerminator=lambda s,v: v['extra_bit_picture'] == 0), 'extra_bit'),
    ]

@layer.define
class slice(pbinary.struct):
    # 0x100 - 0x1af
    type = (0x100, 0x1b0)

    class extra_bit(pbinary.struct):
        _fields_ = [(1,'extra_bit_slice'), (8, 'extra_information_slice')]

    _fields_ = [
        (5, 'quantizer_scale'),
        (dyn.clone(pbinary.terminatedarray, _object_=extra_bit, isTerminator=lambda s,v: v['extra_bit_slice'] == 0), 'extra_bit'),
    ]
map(layer.define, (dyn.clone(slice,type=_,__name__='{:s}<{:d}>'.format(slice.__name__,_)) for _ in xrange(*slice.type)))

@layer.define
class pack(pbinary.struct):
    type = 0x1ba
    _fields_ = [
        (4, '0010'),
        (3, 'system_clock_reference[high]'),
        (1, 'marker_bit[3]'),
        (15, 'system_clock_reference[mid]'),
        (1, 'marker_bit[5]'),
        (15, 'system_clock_reference[low]'),
        (1, 'marker_bit[7]'),
        (1, 'marker_bit[8]'),
        (22, 'mux_rate'),
        (1, 'marker_bit[10]'),
    ]

    def get_system_clock_reference(self):
        s = 'system_clock_reference[%s]'
        return tuple((self[s%x] for x in 'high mid low'.split(' ')))

@layer.define
class system_header(pbinary.struct):
    type = 0x1bb

    class streamarray(pbinary.blockarray):
        class stream(pbinary.struct):
            _fields_ = [
                (4, 'stream_id'),
                (4, 'stream_number'),

                (2, '11'),
                (1, 'STD_buffer_bound_scale'),
                (13, 'STD_buffer_size_bound'),
            ]
        _object_ = stream
        def isTerminator(self, value):
            return value['stream_id']&8!=8

    def __streamarray(self):
        bits = self['header_length']*8
        s = 1+22+1+6+1+1+1+1+1+5+8
        assert bits > s
        max = bits-s
        return dyn.clone(self.streamarray, blockbits=lambda s:max)
        

    _fields_ = [
        (16, 'header_length'),
        (1, 'marker_bit'),
        (22, 'rate_bound'),
        (1, 'marker_bit'),
        (6, 'audio_bound'),
        (1, 'fixed_flag'),
        (1, 'CSPS_flag'),
        (1, 'system_audio_lock_flag'),
        (1, 'system_video_lock_flag'),
        (1, 'marker_bit'),
        (5, 'video_bound'),
        (8, 'reserved_byte'),
        (__streamarray, 'streamarray'),
    ]

###
class packet(pbinary.struct):
    _fields_ = [
        (32, 'code'),
        (lambda s: layer.lookup(s['code']), 'data'),
    ]

class stream(pbinary.terminatedarray):
    _object_ = packet
    def isTerminator(self, value):
        return type(value) == end_code

class stream(pbinary.array):
    _object_ = packet
    length = 20

if __name__ == '__main__':
    import ptypes,mpeg
#    ptypes.setsource( ptypes.file('./poc-mpeg.stream') )
    ptypes.setsource( ptypes.file('./poc.mov') )
    reload(mpeg)

    a = mpeg.stream(offset=0x3ba, length=20)
    print a.l
