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
    # Block Type (0)
    [
        # Coeff Band (0)
        [
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (1)
        [
            bytearray(b'\xFD\x88\xFE\xFF\xE4\xDB\x80\x80\x80\x80\x80'),
            bytearray(b'\xBD\x81\xF2\xFF\xE3\xD5\xFF\xDB\x80\x80\x80'),
            bytearray(b'\x6A\x7E\xE3\xFC\xD6\xD1\xFF\xFF\x80\x80\x80'),
        ],
        # Coeff Band (2)
        [
            bytearray(b'\x01\x62\xF8\xFF\xEC\xE2\xFF\xFF\x80\x80\x80'),
            bytearray(b'\xB5\x85\xEE\xFE\xDD\xEA\xFF\x9A\x80\x80\x80'),
            bytearray(b'\x4E\x86\xCA\xF7\xC6\xB4\xFF\xDB\x80\x80\x80'),
        ],
        # Coeff Band (3)
        [
            bytearray(b'\x01\xB9\xF9\xFF\xF3\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\xB8\x96\xF7\xFF\xEC\xE0\x80\x80\x80\x80\x80'),
            bytearray(b'\x4D\x6E\xD8\xFF\xEC\xE6\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (4)
        [
            bytearray(b'\x01\x65\xFB\xFF\xF1\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\xAA\x8B\xF1\xFC\xEC\xD1\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x25\x74\xC4\xF3\xE4\xFF\xFF\xFF\x80\x80\x80'),
        ],
        # Coeff Band (5)
        [
            bytearray(b'\x01\xCC\xFE\xFF\xF5\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\xCF\xA0\xFA\xFF\xEE\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x66\x67\xE7\xFF\xD3\xAB\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (6)
        [
            bytearray(b'\x01\x98\xFC\xFF\xF0\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\xB1\x87\xF3\xFF\xEA\xE1\x80\x80\x80\x80\x80'),
            bytearray(b'\x50\x81\xD3\xFF\xC2\xE0\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (7)
        [
            bytearray(b'\x01\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xF6\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xFF\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
    ],
    # Block Type (1)
    [
        # Coeff Band (0)
        [
            bytearray(b'\xC6\x23\xED\xDF\xC1\xBB\xA2\xA0\x91\x9B\x3E'),
            bytearray(b'\x83\x2D\xC6\xDD\xAC\xB0\xDC\x9D\xFC\xDD\x01'),
            bytearray(b'\x44\x2F\x92\xD0\x95\xA7\xDD\xA2\xFF\xDF\x80'),
        ],
        # Coeff Band (1)
        [
            bytearray(b'\x01\x95\xF1\xFF\xDD\xE0\xFF\xFF\x80\x80\x80'),
            bytearray(b'\xB8\x8D\xEA\xFD\xDE\xDC\xFF\xC7\x80\x80\x80'),
            bytearray(b'\x51\x63\xB5\xF2\xB0\xBE\xF9\xCA\xFF\xFF\x80'),
        ],
        # Coeff Band (2)
        [
            bytearray(b'\x01\x81\xE8\xFD\xD6\xC5\xF2\xC4\xFF\xFF\x80'),
            bytearray(b'\x63\x79\xD2\xFA\xC9\xC6\xFF\xCA\x80\x80\x80'),
            bytearray(b'\x17\x5B\xA3\xF2\xAA\xBB\xF7\xD2\xFF\xFF\x80'),
        ],
        # Coeff Band (3)
        [
            bytearray(b'\x01\xC8\xF6\xFF\xEA\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\x6D\xB2\xF1\xFF\xE7\xF5\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x2C\x82\xC9\xFD\xCD\xC0\xFF\xFF\x80\x80\x80'),
        ],
        # Coeff Band (4)
        [
            bytearray(b'\x01\x84\xEF\xFB\xDB\xD1\xFF\xA5\x80\x80\x80'),
            bytearray(b'\x5E\x88\xE1\xFB\xDA\xBE\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x16\x64\xAE\xF5\xBA\xA1\xFF\xC7\x80\x80\x80'),
        ],
        # Coeff Band (5)
        [
            bytearray(b'\x01\xB6\xF9\xFF\xE8\xEB\x80\x80\x80\x80\x80'),
            bytearray(b'\x7C\x8F\xF1\xFF\xE3\xEA\x80\x80\x80\x80\x80'),
            bytearray(b'\x23\x4D\xB5\xFB\xC1\xD3\xFF\xCD\x80\x80\x80'),
        ],
        # Coeff Band (6)
        [
            bytearray(b'\x01\x9D\xF7\xFF\xEC\xE7\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x79\x8D\xEB\xFF\xE1\xE3\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x2D\x63\xBC\xFB\xC3\xD9\xFF\xE0\x80\x80\x80'),
        ],
        # Coeff Band (7)
        [
            bytearray(b'\x01\x01\xFB\xFF\xD5\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\xCB\x01\xF8\xFF\xFF\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x89\x01\xB1\xFF\xE0\xFF\x80\x80\x80\x80\x80'),
        ],
    ],
    # Block Type (2)
    [
        # Coeff Band (0)
        [
            bytearray(b'\xFD\x09\xF8\xFB\xCF\xD0\xFF\xC0\x80\x80\x80'),
            bytearray(b'\xAF\x0D\xE0\xF3\xC1\xB9\xF9\xC6\xFF\xFF\x80'),
            bytearray(b'\x49\x11\xAB\xDD\xA1\xB3\xEC\xA7\xFF\xEA\x80'),
        ],
        # Coeff Band (1)
        [
            bytearray(b'\x01\x5F\xF7\xFD\xD4\xB7\xFF\xFF\x80\x80\x80'),
            bytearray(b'\xEF\x5A\xF4\xFA\xD3\xD1\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x9B\x4D\xC3\xF8\xBC\xC3\xFF\xFF\x80\x80\x80'),
        ],
        # Coeff Band (2)
        [
            bytearray(b'\x01\x18\xEF\xFB\xDA\xDB\xFF\xCD\x80\x80\x80'),
            bytearray(b'\xC9\x33\xDB\xFF\xC4\xBA\x80\x80\x80\x80\x80'),
            bytearray(b'\x45\x2E\xBE\xEF\xC9\xDA\xFF\xE4\x80\x80\x80'),
        ],
        # Coeff Band (3)
        [
            bytearray(b'\x01\xBF\xFB\xFF\xFF\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xDF\xA5\xF9\xFF\xD5\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\x8D\x7C\xF8\xFF\xFF\x80\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (4)
        [
            bytearray(b'\x01\x10\xF8\xFF\xFF\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xBE\x24\xE6\xFF\xEC\xFF\x80\x80\x80\x80\x80'),
            bytearray(b'\x95\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (5)
        [
            bytearray(b'\x01\xE2\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xF7\xC0\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xF0\x80\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (6)
        [
            bytearray(b'\x01\x86\xFC\xFF\xFF\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xD5\x3E\xFA\xFF\xFF\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x37\x5D\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
        # Coeff Band (7)
        [
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
    ],
    # Block Type (3)
    [
        # Coeff Band (0)
        [
            bytearray(b'\xCA\x18\xD5\xEB\xBA\xBF\xDC\xA0\xF0\xAF\xFF'),
            bytearray(b'\x7E\x26\xB6\xE8\xA9\xB8\xE4\xAE\xFF\xBB\x80'),
            bytearray(b'\x3D\x2E\x8A\xDB\x97\xB2\xF0\xAA\xFF\xD8\x80'),
        ],
        # Coeff Band (1)
        [
            bytearray(b'\x01\x70\xE6\xFA\xC7\xBF\xF7\x9F\xFF\xFF\x80'),
            bytearray(b'\xA6\x6D\xE4\xFC\xD3\xD7\xFF\xAE\x80\x80\x80'),
            bytearray(b'\x27\x4D\xA2\xE8\xAC\xB4\xF5\xB2\xFF\xFF\x80'),
        ],
        # Coeff Band (2)
        [
            bytearray(b'\x01\x34\xDC\xF6\xC6\xC7\xF9\xDC\xFF\xFF\x80'),
            bytearray(b'\x7C\x4A\xBF\xF3\xB7\xC1\xFA\xDD\xFF\xFF\x80'),
            bytearray(b'\x18\x47\x82\xDB\x9A\xAA\xF3\xB6\xFF\xFF\x80'),
        ],
        # Coeff Band (3)
        [
            bytearray(b'\x01\xB6\xE1\xF9\xDB\xF0\xFF\xE0\x80\x80\x80'),
            bytearray(b'\x95\x96\xE2\xFC\xD8\xCD\xFF\xAB\x80\x80\x80'),
            bytearray(b'\x1C\x6C\xAA\xF2\xB7\xC2\xFE\xDF\xFF\xFF\x80'),
        ],
        # Coeff Band (4)
        [
            bytearray(b'\x01\x51\xE6\xFC\xCC\xCB\xFF\xC0\x80\x80\x80'),
            bytearray(b'\x7B\x66\xD1\xF7\xBC\xC4\xFF\xE9\x80\x80\x80'),
            bytearray(b'\x14\x5F\x99\xF3\xA4\xAD\xFF\xCB\x80\x80\x80'),
        ],
        # Coeff Band (5)
        [
            bytearray(b'\x01\xDE\xF8\xFF\xD8\xD5\x80\x80\x80\x80\x80'),
            bytearray(b'\xA8\xAF\xF6\xFC\xEB\xCD\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x2F\x74\xD7\xFF\xD3\xD4\xFF\xFF\x80\x80\x80'),
        ],
        # Coeff Band (6)
        [
            bytearray(b'\x01\x79\xEC\xFD\xD4\xD6\xFF\xFF\x80\x80\x80'),
            bytearray(b'\x8D\x54\xD5\xFC\xC9\xCA\xFF\xDB\x80\x80\x80'),
            bytearray(b'\x2A\x50\xA0\xF0\xA2\xB9\xFF\xCD\x80\x80\x80'),
        ],
        # Coeff Band (7)
        [
            bytearray(b'\x01\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xF4\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
            bytearray(b'\xEE\x01\xFF\x80\x80\x80\x80\x80\x80\x80\x80'),
        ],
    ],
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
