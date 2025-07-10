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

class token_prob_update(pbinary.array):
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
