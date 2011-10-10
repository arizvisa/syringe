from ptypes import *

class seq_parameter_set_rbsp(pbinary.struct):
    class __pic_order_type_1(pbinary.struct):
        _fields_ = [
            (1, 'delta_pic_order_always_zero_flag'),
            (v, 'offset_for_non_ref_pic'),
            (v, 'offset_for_top_to_bottom_field'),
            (v, 'num_ref_frames_in_pic_order_cnt_cycle'),
            (lambda s: dyn.array( dyn.clone(pbinary.struct,_fields_=[(v,'offset_for_ref_frame')]), s['num_ref_frames_in_pic_order_cnt_cycle']), 'ref_frames')
        ]

    def __pic_order(self):
        type = self['pic_order_cnt_type']
        if type == 0:
            return dyn.clone(pbinary.struct, _fields_=[(v, 'log2_max_pic_order_cnt_lsb')])
        elif type == 1:
            return __pic_order_type_1
        raise NotImplementedError(type)

    class __frame_crop_offset(pbinary.struct):
        _fields_ = [
            (v, 'frame_crop_left_offset'),
            (v, 'frame_crop_right_offset'),
            (v, 'frame_crop_top_offset'),
            (v, 'frame_crop_bottom_offset'),
        ]

    def __frame_crop(self):
        if self['frame_cropping_flag']:
            return __frame_crop_offset
        return dyn.clone(pbinary.struct,_fields_=[])

    _fields_ = [
        (8, 'profile_idc'),
        (1, 'constraint_set0_flag'),
        (1, 'constraint_set1_flag'),
        (1, 'constraint_set2_flag'),
        (5, 'reserved_zero_5bits'),
        (8, 'level_idc'),
        (v, 'seq_parameter_set_id'),
        (v, 'pic_order_cnt_type'),
        (__pic_order, 'pic_order'),
        (v, 'num_ref_frames'),
        (1, 'gaps_in_frame_num_value_allowed_flag'),
        (v, 'pic_width_in_mbs_minus1')
        (v, 'pic_height_in_map_units_minus1'),
        (1, 'frame_mbs_only_flag'),
        (lambda s: [0,1][s['frame_mbs_only_flag']], 'mb_adaptive_frame_field_flag'),
        (1, 'direct_8x8_inference_flag'),
        (1, 'frame_cropping_flag'),
        (__frame_crop, 'frame_crop'),
        (1, 'vul_parameters_present_flag'),
        (lambda s: [dyn.clone(pbinary.struct,_fields_=[]),__vul_parameters][s['vul_parameters_present_flag']], 'vul_parameters'),
        (__rbsp_trailing_bits, 'rbsp_trailing_bits'),
    ]
