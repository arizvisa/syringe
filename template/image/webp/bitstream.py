import builtins, operator, os, math, functools, itertools, sys, types
import ptypes
from ptypes import *

pbinary.setbyteorder('big')

### VP8 bitstream types
#def Bool(p):
#    return p
Flag = 1
def Lit(n):
    return n
def SignedLit(n):
    return -n
#def P(n):
#    return n
def f(n):
    return n
def L(n):
    return Lit(n)
#def B(p):
#    return Bool(p)

### VP8 boolean entropy data
default_coef_probs = [
  [ # Block Type ( 0 )
    [ # Coeff Band ( 0 )
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 1 )
      bytearray([253, 136, 254, 255, 228, 219, 128, 128, 128, 128, 128]),
      bytearray([189, 129, 242, 255, 227, 213, 255, 219, 128, 128, 128]),
      bytearray([106, 126, 227, 252, 214, 209, 255, 255, 128, 128, 128]),
    ],
    [ # Coeff Band ( 2 )
      bytearray([1, 98, 248, 255, 236, 226, 255, 255, 128, 128, 128]),
      bytearray([181, 133, 238, 254, 221, 234, 255, 154, 128, 128, 128]),
      bytearray([78, 134, 202, 247, 198, 180, 255, 219, 128, 128, 128]),
    ],
    [ # Coeff Band ( 3 )
      bytearray([1, 185, 249, 255, 243, 255, 128, 128, 128, 128, 128]),
      bytearray([184, 150, 247, 255, 236, 224, 128, 128, 128, 128, 128]),
      bytearray([77, 110, 216, 255, 236, 230, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 4 )
      bytearray([1, 101, 251, 255, 241, 255, 128, 128, 128, 128, 128]),
      bytearray([170, 139, 241, 252, 236, 209, 255, 255, 128, 128, 128]),
      bytearray([37, 116, 196, 243, 228, 255, 255, 255, 128, 128, 128]),
    ],
    [ # Coeff Band ( 5 )
      bytearray([1, 204, 254, 255, 245, 255, 128, 128, 128, 128, 128]),
      bytearray([207, 160, 250, 255, 238, 128, 128, 128, 128, 128, 128]),
      bytearray([102, 103, 231, 255, 211, 171, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 6 )
      bytearray([1, 152, 252, 255, 240, 255, 128, 128, 128, 128, 128]),
      bytearray([177, 135, 243, 255, 234, 225, 128, 128, 128, 128, 128]),
      bytearray([80, 129, 211, 255, 194, 224, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 7 )
      bytearray([1, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([246, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([255, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
    ]
  ],
  [ # Block Type ( 1 )
    [ # Coeff Band ( 0 )
      bytearray([198, 35, 237, 223, 193, 187, 162, 160, 145, 155, 62]),
      bytearray([131, 45, 198, 221, 172, 176, 220, 157, 252, 221, 1]),
      bytearray([68, 47, 146, 208, 149, 167, 221, 162, 255, 223, 128]),
    ],
    [ # Coeff Band ( 1 )
      bytearray([1, 149, 241, 255, 221, 224, 255, 255, 128, 128, 128]),
      bytearray([184, 141, 234, 253, 222, 220, 255, 199, 128, 128, 128]),
      bytearray([81, 99, 181, 242, 176, 190, 249, 202, 255, 255, 128]),
    ],
    [ # Coeff Band ( 2 )
      bytearray([1, 129, 232, 253, 214, 197, 242, 196, 255, 255, 128]),
      bytearray([99, 121, 210, 250, 201, 198, 255, 202, 128, 128, 128]),
      bytearray([23, 91, 163, 242, 170, 187, 247, 210, 255, 255, 128]),
    ],
    [ # Coeff Band ( 3 )
      bytearray([1, 200, 246, 255, 234, 255, 128, 128, 128, 128, 128]),
      bytearray([109, 178, 241, 255, 231, 245, 255, 255, 128, 128, 128]),
      bytearray([44, 130, 201, 253, 205, 192, 255, 255, 128, 128, 128]),
    ],
    [ # Coeff Band ( 4 )
      bytearray([1, 132, 239, 251, 219, 209, 255, 165, 128, 128, 128]),
      bytearray([94, 136, 225, 251, 218, 190, 255, 255, 128, 128, 128]),
      bytearray([22, 100, 174, 245, 186, 161, 255, 199, 128, 128, 128]),
    ],
    [ # Coeff Band ( 5 )
      bytearray([1, 182, 249, 255, 232, 235, 128, 128, 128, 128, 128]),
      bytearray([124, 143, 241, 255, 227, 234, 128, 128, 128, 128, 128]),
      bytearray([35, 77, 181, 251, 193, 211, 255, 205, 128, 128, 128]),
    ],
    [ # Coeff Band ( 6 )
      bytearray([1, 157, 247, 255, 236, 231, 255, 255, 128, 128, 128]),
      bytearray([121, 141, 235, 255, 225, 227, 255, 255, 128, 128, 128]),
      bytearray([45, 99, 188, 251, 195, 217, 255, 224, 128, 128, 128]),
    ],
    [ # Coeff Band ( 7 )
      bytearray([1, 1, 251, 255, 213, 255, 128, 128, 128, 128, 128]),
      bytearray([203, 1, 248, 255, 255, 128, 128, 128, 128, 128, 128]),
      bytearray([137, 1, 177, 255, 224, 255, 128, 128, 128, 128, 128]),
    ]
  ],
  [ # Block Type ( 2 )
    [ # Coeff Band ( 0 )
      bytearray([253, 9, 248, 251, 207, 208, 255, 192, 128, 128, 128]),
      bytearray([175, 13, 224, 243, 193, 185, 249, 198, 255, 255, 128]),
      bytearray([73, 17, 171, 221, 161, 179, 236, 167, 255, 234, 128]),
    ],
    [ # Coeff Band ( 1 )
      bytearray([1, 95, 247, 253, 212, 183, 255, 255, 128, 128, 128]),
      bytearray([239, 90, 244, 250, 211, 209, 255, 255, 128, 128, 128]),
      bytearray([155, 77, 195, 248, 188, 195, 255, 255, 128, 128, 128]),
    ],
    [ # Coeff Band ( 2 )
      bytearray([1, 24, 239, 251, 218, 219, 255, 205, 128, 128, 128]),
      bytearray([201, 51, 219, 255, 196, 186, 128, 128, 128, 128, 128]),
      bytearray([69, 46, 190, 239, 201, 218, 255, 228, 128, 128, 128]),
    ],
    [ # Coeff Band ( 3 )
      bytearray([1, 191, 251, 255, 255, 128, 128, 128, 128, 128, 128]),
      bytearray([223, 165, 249, 255, 213, 255, 128, 128, 128, 128, 128]),
      bytearray([141, 124, 248, 255, 255, 128, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 4 )
      bytearray([1, 16, 248, 255, 255, 128, 128, 128, 128, 128, 128]),
      bytearray([190, 36, 230, 255, 236, 255, 128, 128, 128, 128, 128]),
      bytearray([149, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 5 )
      bytearray([1, 226, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([247, 192, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([240, 128, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 6 )
      bytearray([1, 134, 252, 255, 255, 128, 128, 128, 128, 128, 128]),
      bytearray([213, 62, 250, 255, 255, 128, 128, 128, 128, 128, 128]),
      bytearray([55, 93, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
    ],
    [ # Coeff Band ( 7 )
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]),
    ]
  ],
  [ # Block Type ( 3 )
    [ # Coeff Band ( 0 )
      bytearray([202, 24, 213, 235, 186, 191, 220, 160, 240, 175, 255]),
      bytearray([126, 38, 182, 232, 169, 184, 228, 174, 255, 187, 128]),
      bytearray([61, 46, 138, 219, 151, 178, 240, 170, 255, 216, 128]),
    ],
    [ # Coeff Band ( 1 )
      bytearray([1, 112, 230, 250, 199, 191, 247, 159, 255, 255, 128]),
      bytearray([166, 109, 228, 252, 211, 215, 255, 174, 128, 128, 128]),
      bytearray([39, 77, 162, 232, 172, 180, 245, 178, 255, 255, 128]),
    ],
    [ # Coeff Band ( 2 )
      bytearray([1, 52, 220, 246, 198, 199, 249, 220, 255, 255, 128]),
      bytearray([124, 74, 191, 243, 183, 193, 250, 221, 255, 255, 128]),
      bytearray([24, 71, 130, 219, 154, 170, 243, 182, 255, 255, 128]),
    ],
    [ # Coeff Band ( 3 )
      bytearray([1, 182, 225, 249, 219, 240, 255, 224, 128, 128, 128]),
      bytearray([149, 150, 226, 252, 216, 205, 255, 171, 128, 128, 128]),
      bytearray([28, 108, 170, 242, 183, 194, 254, 223, 255, 255, 128]),
    ],
    [ # Coeff Band ( 4 )
      bytearray([1, 81, 230, 252, 204, 203, 255, 192, 128, 128, 128]),
      bytearray([123, 102, 209, 247, 188, 196, 255, 233, 128, 128, 128]),
      bytearray([20, 95, 153, 243, 164, 173, 255, 203, 128, 128, 128]),
    ],
    [ # Coeff Band ( 5 )
      bytearray([1, 222, 248, 255, 216, 213, 128, 128, 128, 128, 128]),
      bytearray([168, 175, 246, 252, 235, 205, 255, 255, 128, 128, 128]),
      bytearray([47, 116, 215, 255, 211, 212, 255, 255, 128, 128, 128]),
    ],
    [ # Coeff Band ( 6 )
      bytearray([1, 121, 236, 253, 212, 214, 255, 255, 128, 128, 128]),
      bytearray([141, 84, 213, 252, 201, 202, 255, 219, 128, 128, 128]),
      bytearray([42, 80, 160, 240, 162, 185, 255, 205, 128, 128, 128]),
    ],
    [ # Coeff Band ( 7 )
      bytearray([1, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([244, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
      bytearray([238, 1, 255, 128, 128, 128, 128, 128, 128, 128, 128]),
    ]
  ]
]

### VP8 bitstream utilities
def bitstream_condition_field(field, key, nokey):
    def is_set(self):
        return key if self[field] else nokey
    return is_set

### these structures are boolean-encoded into a stream
start_code = f(24)
@pbinary.littleendian
class size_code(pbinary.struct):
    _fields_ = [
        (2, 'scale'),
        (14, 'size'),
    ]

class frame_tag(pstruct.type):
    @pbinary.littleendian
    class _frame_tag(pbinary.flags):
        _fields_ = [
            (19, 'first_part_size'),
            (1, 'key_frame'),
            #(2, 'version'), (1, 'is_experimental'),    # in reference implementation
            (3, 'version'),
            (1, 'show_frame'),
        ]

    class _start_code(pbinary.enum):
        length = start_code
        _values_ = [
            ('DEFAULT', 0x9D012A),
        ]
        def properties(self):
            res = super(frame_tag._start_code, self).properties()
            res['valid'] = self['DEFAULT']
            return res
        def alloc(self, *values, **attributes):
            if values:
                return super(frame_tag._start_code, self).alloc(*values, **attributes)
            return self.alloc(0x9D012A)

    def __is_keyframe(true, false):
        def is_keyframe(self):
            res = self['frame_tag'].li
            return true if res['key_frame'] else false
        return is_keyframe

    _fields_ = [
        (_frame_tag, 'frame_tag'),
        (__is_keyframe(_start_code, 0), 'start_code'),
        (__is_keyframe(size_code, 0), 'horizontal_size_code'),
        (__is_keyframe(size_code, 0), 'vertical_size_code'),
    ]

color_space = L(1)
clamping_type = L(1)
segmentation_enabled = L(1)
filter_type = L(1)
loop_filter_level = L(6)
sharpness_level = L(3)
log2_nbr_of_dct_partitions = L(2)
refresh_entropy_probs = L(1)
refresh_golden_frame = L(1)
refresh_alternate_frame = L(1)
copy_buffer_to_golden = L(2)
copy_buffer_to_alternate = L(2)
sign_bias_golden = L(1)
sign_bias_alternate = L(1)
refresh_entropy_probs = L(1)
refresh_last = L(1)
mb_no_skip_coeff = L(1)
prob_skip_false = L(8)
prob_intra = L(8)
prob_last = L(8)
prob_gf = L(8)
intra_16x16_prob_update_flag = L(1)
intra_16x16_prob = L(8)
intra_chroma_prob_update_flag = L(1)
intra_chroma_prob = L(8)

update_mb_segmentation_map = L(1)
update_segment_feature_data = L(1)
segment_feature_mode = L(1)
quantizer_update = L(1)
quantizer_update_value = L(7)
quantizer_update_sign = L(1)
loop_filter_update = L(1)
lf_update_value = L(6)
lf_update_sign = L(1)
segment_prob_update = L(1)
segment_prob = L(8)

class update_segment_quantizer_entry(pbinary.struct):
    _fields_ = [
        (quantizer_update, 'quantizer_update'),
        (bitstream_condition_field('quantizer_update', quantizer_update_value, 0), 'quantizer_update_value'),
        (bitstream_condition_field('quantizer_update', quantizer_update_sign, 0), 'quantizer_update_sign'),
    ]

class update_segment_loop_filter_entry(pbinary.struct):
    _fields_ = [
        (loop_filter_update, 'loop_filter_update'),
        (bitstream_condition_field('loop_filter_update', lf_update_value, 0), 'lf_update_value'),
        (bitstream_condition_field('loop_filter_update', lf_update_sign, 0), 'lf_update_sign'),
    ]

class update_mb_segment_prob_entry(pbinary.struct):
    _fields_ = [
        (segment_prob_update, 'segment_prob_update'),
        (bitstream_condition_field('segment_prob_update', segment_prob, 0), 'segment_prob'),
    ]

MAX_MB_SEGMENTS = 4
MB_FEATURE_TREE_PROBS = 3
class update_segmentation(pbinary.struct):
    class _update_segment_quantizer(pbinary.array):
        length, _object_ = MAX_MB_SEGMENTS, update_segment_quantizer_entry
    class _update_segment_loop_filter(pbinary.array):
        length, _object_ = MAX_MB_SEGMENTS, update_segment_loop_filter_entry
    class _update_mb_segment_prob(pbinary.array):
        length, _object_ = MB_FEATURE_TREE_PROBS, update_mb_segment_prob_entry

    _fields_ = [
        (update_mb_segmentation_map, 'update_mb_segmentation_map'),
        (update_segment_feature_data, 'update_segment_feature_data'),
        (bitstream_condition_field('update_segment_feature_data', segment_feature_mode, 0), 'segment_feature_mode'),
        (bitstream_condition_field('update_segment_feature_data', _update_segment_quantizer, 0), 'update_segment_quantizer'),
        (bitstream_condition_field('update_segment_feature_data', _update_segment_loop_filter, 0), 'update_segment_loop_filter'),
        (bitstream_condition_field('update_mb_segmentation_map', _update_mb_segment_prob, 0), 'update_mb_segment_prob'),
    ]

loop_filter_adj_enable = L(1)
mode_ref_lf_delta_update = L(1)
ref_frame_delta_update_flag = L(1)
delta_magnitude = L(6)
delta_sign = L(1)
mb_mode_delta_update_flag = L(1)
delta_magnitude = L(6)
delta_sign = L(1)

class ref_frame_delta_entry(pbinary.struct):
    _fields_ = [
        (ref_frame_delta_update_flag, 'ref_frame_delta_update_flag'),
        (bitstream_condition_field('ref_frame_delta_update_flag', delta_magnitude, 0), 'delta_magnitude'),
        (bitstream_condition_field('ref_frame_delta_update_flag', delta_sign, 0), 'delta_sign'),
    ]

class mb_mode_delta_entry(pbinary.struct):
    _fields_ = [
        (mb_mode_delta_update_flag, 'mb_mode_delta_update_flag'),
        (bitstream_condition_field('mb_mode_delta_update_flag', delta_magnitude, 0), 'delta_magnitude'),
        (bitstream_condition_field('mb_mode_delta_update_flag', delta_sign, 0), 'delta_sign'),
    ]

MAX_REF_LF_DELTAS = 4
class mb_lf_adjustments(pbinary.flags):
    class _mode_ref_loop_filter(pbinary.struct):
        class _ref_frame_delta_update(pbinary.array):
            length, _object_ = MAX_REF_LF_DELTAS, ref_frame_delta_entry
        class _mb_mode_delta_update(pbinary.array):
            length, _object_ = MAX_REF_LF_DELTAS, ref_frame_delta_entry
        _fields_ = [
            (mode_ref_lf_delta_update, 'mode_ref_lf_delta_update'),
            (bitstream_condition_field('mode_ref_lf_delta_update', _ref_frame_delta_update, 0), 'ref_frame_delta_update'),
            (bitstream_condition_field('mode_ref_lf_delta_update', _mb_mode_delta_update, 0), 'mb_mode_delta_update'),
        ]

    _fields_ = [
        (loop_filter_adj_enable, 'loop_filter_adj_enable'),
        (bitstream_condition_field('loop_filter_adj_enable', _mode_ref_loop_filter, 0), 'mode_ref_loop_filter'),
    ]

y_ac_qi = L(7)
y_dc_delta_present = L(1)
y_dc_delta_magnitude = L(4)
y_dc_delta_sign = L(1)
y2_dc_delta_present = L(1)
y2_dc_delta_magnitude = L(4)
y2_dc_delta_sign = L(1)
y2_ac_delta_present = L(1)
y2_ac_delta_magnitude = L(4)
y2_ac_delta_sign = L(1)
uv_dc_delta_present = L(1)
uv_dc_delta_magnitude = L(4)
uv_dc_delta_sign = L(1)
uv_ac_delta_present = L(1)
uv_ac_delta_magnitude = L(4)
uv_ac_delta_sign = L(1)
class quant_indices(pbinary.flags):
    # FIXME: these entries could be grouped, but then it wouldn't correspond
    #        directly to the bitstream specification (RFC6386).
    _fields_ = [
        (y_ac_qi, 'y_ac_qi'),

        (y_dc_delta_present, 'y_dc_delta_present'),
        (bitstream_condition_field('y_dc_delta_present', y_dc_delta_magnitude, 1), 'y_dc_delta_magnitude'),
        (bitstream_condition_field('y_dc_delta_present', y_dc_delta_sign, 0), 'y_dc_delta_sign'),

        (y2_dc_delta_present, 'y2_dc_delta_present'),
        (bitstream_condition_field('y2_dc_delta_present', y2_dc_delta_magnitude, 0), 'y2_dc_delta_magnitude'),
        (bitstream_condition_field('y2_dc_delta_present', y2_dc_delta_sign, 0), 'y2_dc_delta_sign'),

        (y2_ac_delta_present, 'y2_ac_delta_present'),
        (bitstream_condition_field('y2_ac_delta_present', y2_ac_delta_magnitude, 0), 'y2_ac_delta_magnitude'),
        (bitstream_condition_field('y2_ac_delta_present', y2_ac_delta_sign, 0), 'y2_ac_delta_sign'),

        (uv_dc_delta_present, 'uv_dc_delta_present'),
        (bitstream_condition_field('uv_dc_delta_present', uv_dc_delta_magnitude, 0), 'uv_dc_delta_magnitude'),
        (bitstream_condition_field('uv_dc_delta_present', uv_dc_delta_sign, 0), 'uv_dc_delta_sign'),

        (uv_ac_delta_present, 'uv_ac_delta_present'),
        (bitstream_condition_field('uv_ac_delta_present', uv_ac_delta_magnitude, 0), 'uv_ac_delta_magnitude'),
        (bitstream_condition_field('uv_ac_delta_present', uv_ac_delta_sign, 0), 'uv_ac_delta_sign'),
    ]

coeff_prob_update_flag =  L(1)
coeff_prob =  L(8)
class coeff_prob_update(pbinary.struct):
    _fields_ = [
        (coeff_prob_update_flag, 'coeff_prob_update_flag'),
        (bitstream_condition_field('coeff_prob_update_flag', coeff_prob, 0), 'coeff_prob'),
    ]

BLOCK_TYPES = 4
COEF_BANDS = 8
PREV_COEF_CONTEXTS = 3
ENTROPY_NODES = 11

class token_prob_update_nested(pbinary.array):
    length = BLOCK_TYPES
    class _object_(pbinary.array):
        length = COEF_BANDS
        class _object_(pbinary.array):
            length = PREV_COEF_CONTEXTS
            class _object_(pbinary.array):
                length, _object_ = ENTROPY_NODES, coeff_prob_update

    def summary(self):
        res = self.bits()
        return "...{:d} bit{:s}...".format(res, '' if res == 1 else 's')

class token_prob_update(pbinary.array):
    length = BLOCK_TYPES * COEF_BANDS * PREV_COEF_CONTEXTS * ENTROPY_NODES
    _object_ = coeff_prob_update

    def summary(self):
        res = self.bits()
        return "...{:d} bit{:s}...".format(res, '' if res == 1 else 's')

mv_prob_update_flag = L(1)
prob = L(7)
class mv_prob_update(pbinary.array):
    length = 2
    class _object_(pbinary.array):
        length = 19
        class _object_(pbinary.struct):
            _fields_ = [
                (mv_prob_update_flag, 'mv_prob_update_flag'),
                (lambda self: prob if self['mv_prob_update_flag'] else 0, 'prob'),
            ]

class frame_header(pbinary.struct):
    def __condition_keyframe(key, nokey):
        def is_keyframe(self):
            p = self.parent.parent
            if not isinstance(p, pstruct.type):
                return nokey
            tag = p.value[0]
            res = tag['frame_tag'].li
            return key if res['key_frame'] else nokey
        return is_keyframe

    def __refresh_frame_field(field, key, nokey):
        def is_not_keyframe(self):
            p = self.parent.parent
            if not isinstance(p, pstruct.type):
                return nokey
            tag = p.value[0]
            res = tag['frame_tag'].li
            if res['key_frame']:
                return nokey
            return key if self[field] else nokey
        return is_not_keyframe

    class _filter_type(pbinary.enum):
        length, _values_ = filter_type, [
            ('NORMAL_LOOPFILTER', 0),
            ('SIMPLE_LOOPFILTER', 1),
        ]

    _fields_ = [
        (__condition_keyframe(color_space, 0), 'color_space'),
        (__condition_keyframe(clamping_type, 0), 'clamping_type'),
        (segmentation_enabled, 'segmentation_enabled'),
        (bitstream_condition_field('segmentation_enabled', update_segmentation, 0), 'update_segmentation'),
        (_filter_type, 'filter_type'),
        (loop_filter_level, 'loop_filter_level'),
        (sharpness_level, 'sharpness_level'),
        (mb_lf_adjustments, 'mb_lf_adjustments'),
        (log2_nbr_of_dct_partitions, 'log2_nbr_of_dct_partitions'),
        (quant_indices, 'quant_indices'),

        # if we're a key frame
        #(__condition_keyframe(refresh_entropy_probs, 0), 'refresh_entropy_probs'),     # XXX: duplicate field

        # if we're not a key frame
        (__condition_keyframe(0, refresh_golden_frame), 'refresh_golden_frame'),
        (__condition_keyframe(0, refresh_alternate_frame), 'refresh_alternate_frame'),
        (__refresh_frame_field('refresh_golden_frame', copy_buffer_to_golden, 0), 'copy_buffer_to_golden'),
        (__refresh_frame_field('refresh_alternate_frame', copy_buffer_to_alternate, 0), 'copy_buffer_to_alternate'),
        (__condition_keyframe(0, sign_bias_golden), 'sign_bias_golden'),
        (__condition_keyframe(0, sign_bias_alternate), 'sign_bias_alternate'),
        #(__condition_keyframe(0, refresh_entropy_probs), 'refresh_entropy_probs'),     # XXX: duplicate field

        (refresh_entropy_probs, 'refresh_entropy_probs'),   # XXX: this field is in both keyframes and non-keyframes
        (__condition_keyframe(0, refresh_last), 'refresh_last'),

        # FIXME: this next field is entropy-coded using `default_coef_probs`.
        (token_prob_update, 'token_prob_update'),
        (mb_no_skip_coeff, 'mb_no_skip_coeff'),
        #(bitstream_condition_field('mb_no_skip_coeff', prob_skip_false, 0), 'prob_skip_false'),
        #(__condition_keyframe(0, prob_intra), 'prob_intra'),
        #(__condition_keyframe(0, prob_last), 'prob_last'),
        #(__condition_keyframe(0, prob_gf), 'prob_gf'),
        #(__condition_keyframe(0, intra_16x16_prob_update_flag), 'intra_16x16_prob_update_flag'),
        #(bitstream_condition_field('intra_16x16_prob_update_flag', dyn.clone(pbinary.array, _object_=intra_16x16_prob, length=4), 0), 'intra_16x16_prob'),
        #(__condition_keyframe(0, intra_chroma_prob_update_flag), 'intra_chroma_prob_update_flag'),
        #(bitstream_condition_field('intra_chroma_prob_update_flag', dyn.clone(pbinary.array, _object_=intra_chroma_prob, length=3), 0), 'intra_chroma_prob'),
        #(mv_prob_update, 'mv_prob_update'),
    ]

    def summary(self):
        res = self.bits()
        return "...{:d} bit{:s}...".format(res, '' if res == 1 else 's')
