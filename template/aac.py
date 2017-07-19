from ptypes import *

ONLY_LONG_SEQUENCE = 0
LONG_START_SEQUENCE = 1
LONG_STOP_SEQUENCE = 2
EIGHT_SHORT_SEQUENCE = 3

def get_variables(sampling_frequency_index, window_sequence, scale_factor_grouping, max_sfb):
    '''returns num_windows, num_window_groups, window_group_length, num_swb, swb_offset, sect_sfb_offset'''
    # XXX: from page 59 of 206 in aac iso13818-7.pdf
    num_swb = swb_offset = sect_sfb_offset = 0

    if window_sequence in (ONLY_LONG_SEQUENCE, LONG_START_SEQUENCE, LONG_STOP_SEQUENCE):
        num_windows = 1
        num_window_groups = 1
        window_group_length = None  # XXX
        num_swb = None
    elif window_sequence == EIGHT_SHORT_SEQUENCE:
        num_windows = 8
        num_window_groups = 1
        window_group_length = None  # XXX
        for i in range(num_windows):
            if bitset(scale_factor_grouping, 6-i):
                num_window_groups -= 1
            else:
                window_group_length     # += 1      # XXX
            continue

        for g in range(num_window_groups):
            pass
    return num_windows, num_window_groups, window_group_length, num_swb, swb_offset, sect_sfb_offset

class adif_header(pbinary.struct):
    _fields_ = [
        (32, 'adif_id'),
        (1, 'copyright_id_present'),
        (lambda s: [0,72][s['copyright_id_present']], 'copyright_id'),
        (1, 'original_copy'),
        (1, 'home'),
        (1, 'bitstream_type'),
        (23, 'bitrate'),
        (4, 'num_program_config_elements'),
        (lambda s: [20,0][s['bitstream_type']], 'adif_buffer_fullness'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_program_config_elements'], _object_=program_config_element), 'program_config_elements')
    ]

class adts_fixed_header(pbinary.struct):
    _fields_ = [
        (12, 'syncword'),
        (1, 'ID'),
        (2, 'layer'),
        (1, 'protection_absent'),
        (2, 'profile'),
        (4, 'sampling_frequency_index'),
        (1, 'private_bit'),
        (3, 'channel_configuration'),
        (1, 'orignal/copy'),
        (1, 'home'),
#        (lambda s: [0,2][s['ID'] == 0], 'emphasis')
    ]

class adts_variable_header(pbinary.struct):
    _fields_ = [
        (1, 'copyright_identification_bit'),
        (1, 'copyright_identification_start'),
        (13, 'frame_length'),
        (11, 'adts_buffer_fullness'),
        (2, 'number_of_raw_data_blocks_in_frame'),
    ]

class adts_header_error_check(pbinary.struct):
    def __raw_data_block_position(self):
        if self.parent['adts_fixed_header']['protection_absent'] == 0:
            s = self.parent['adts_variable_header']['number_of_raw_data_blocks_in_frame']
            return dyn.clone(pbinary.array, length=s, _object_=16)
        return 0

    _fields_ = [
        (__raw_data_block_position, 'raw_data_block_position'),
        (lambda s: [16,0][s.parent['adts_fixed_header']['protection_absent']], 'crc_check'),
    ]

class adts_error_check(pbinary.struct):
    _fields_ = [
        (lambda s: [16,0][s.getparent(adts_frame)['adts_fixed_header']['protection_absent']], 'crc_check'),
    ]
class adts_raw_data_block_error_check(adts_error_check): pass

class raw_data_block(pbinary.struct):
    def __element(self):
        try:
            result = Element.lookup( self['id_syn_ele'] )
        except KeyError:
            print 'unable to find', self['id_syn_ele']
            result = 0
        return result

    _fields_ = [
        (3, 'id_syn_ele'),
        (__element, 'ele'),
    ]

class raw_data_stream(pbinary.terminatedarray):
    _object_ = raw_data_block
    def isTerminator(self, value):
        return type(v) is _END

class adts_frame(pbinary.struct):
    class data_block_0(pbinary.struct):
        _fields_ = [
            (raw_data_block, 'raw_data_block'),
        ]

    class data_block_1(pbinary.struct):
        _fields_ = [
            (raw_data_block, 'raw_data_block'),
            (adts_raw_data_block_error_check, 'adts_raw_data_block_error_check'),
        ]

    def __data(self):
        #FIXME
#        raise NotImplementedError
        self.sampling_frequency_index = self['adts_fixed_header']
        self.window_sequence = 0
        self.scale_factor_grouping = 0
        self.max_sfb = 0
        self.common_window = 0

        num_windows,num_window_groups,window_group_length,num_swb,swb_offset,sect_sfb_offset = get_variables(self.sampling_frequency_index, self.window_sequence, self.scale_factor_grouping, self.max_sfb)
        attrs = {
            'num_windows' : num_windows,
            'num_window_groups' : num_window_groups,
            'window_group_length' : window_group_length,
            'num_swb' : num_swb,
            'swb_offset' : swb_offset,
            'sect_sfb_offset' : sect_sfb_offset,

            'sampling_frequency_index' : self.sampling_frequency_index,
            'window_sequence' : self.window_sequence,
            'scale_factor_grouping' : self.scale_factor_grouping,
            'max_sfb' : self.max_sfb,

            'common_window' : self.common_window,
        }

        count = self['adts_variable_header']['number_of_raw_data_blocks_in_frame']
        if count == 0:
            return dyn.clone(pbinary.array, length=1, _object_=self.data_block_0, attrs=attrs)
        return dyn.clone(pbinary.array, length=count, _object_=self.data_block_1, attrs=attrs)

    _fields_ = [
        (adts_fixed_header, 'adts_fixed_header'),
        (adts_variable_header, 'adts_variable_header'),

        (lambda s: [adts_error_check, adts_header_error_check][s['adts_variable_header']['number_of_raw_data_blocks_in_frame']==1], 'adts_error_check'),
#        (lambda s: dyn.clone(pbinary.array, length=s['adts_variable_header']['number_of_raw_data_blocks_in_frame'], _object_=[s.data_block_0,s.data_block_1][s['adts_variable_header']['number_of_raw_data_blocks_in_frame']==1]), 'data')
        (__data, 'data')
    ]

    def blocksize(self):
        return self['adts_variable_header']['frame_length']

    def blockbits(self):
        return self.blocksize()*8

class adts_sequence(pbinary.terminatedarray):
    _object_ = adts_frame

    def isTerminator(self, value):
        return False

class Element(ptype.definition):
    cache = {}

#######
class pulse_data(pbinary.struct):
    class pulse(pbinary.struct):
        _fields_ = [(5, 'offset'),(4,'amp')]

    _fields_ = [
        (2, 'number_pulse'),
        (6, 'pulse_start_sfb'),
        (lambda s: dyn.clone(pbinary.array, length=s['number_pulse']+1, _object_=s.pulse), 'pulse'),
    ]

# XXX
class section_data(pbinary.struct):
    _fields_ = []

# XXX
class scale_factor_data(pbinary.struct):
    _fields_ = []

# XXX
class tns_data(pbinary.struct):
    _fields_ = [

    ]

# XXX
class spectral_data(pbinary.struct):
    _fields_ = []

# XXX
class dynamic_range_info(pbinary.struct):
    _fields_ = []

class gain_control_data(pbinary.struct):
    _fields_ = []

class individual_channel_stream(pbinary.struct):
    _fields_ = [
        (8, 'global_gain'),
        (lambda s: [0,ics_info][s.common_window == 0], 'ics_info'),         # XXX: this depends on some value determined by the parent's definition
        (section_data, 'section_data'),         # XXX
        (scale_factor_data, 'scale_factor_data'),   # XXX

        (1, 'pulse_data_present'),
        (lambda s: [0,pulse_data][s['pulse_data_present']], 'pulse_data'),

    # XXX
        (1, 'tns_data_present'),
        (lambda s: [0,tns_data][s['tns_data_present']], 'tns_data'),

    # XXX
        (1, 'gain_control_data_present'),
        (lambda s: [0,gain_control_data][s['gain_control_data_present']], 'gain_control_data'),

    # XXX
        (spectral_data, 'spectral_data'),
    ]

class ics_info(pbinary.struct):
    class window_sequence_eight_short(pbinary.struct):
        type = 2
        _fields_ = [(4, 'max_sfb'), (7, 'scale_factor_grouping')]
    class window_sequence_else(pbinary.struct):
        type = None
        _fields_ = [
            (6, 'max_sfb'),
            (1, 'predictor_data_present'),
            (lambda s: [0,1][s['predictor_data_present']], 'predictor_reset'),
            (lambda s: [0,5][s['predictor_reset']], 'predictor_reset_group_number'),
            (lambda s: s['max_sfb'], 'prediction_used'),
        ]

    _fields_ = [
        (1, 'ics_reserved_bit'),
        (2, 'window_sequence'),
        (1, 'window_shape'),
        (lambda s: [s.window_sequence_else, s.window_sequence_eight_short][s['window_sequence']==s.window_sequence_eight_short.type], 'sequence'),
    ]

class common_window(pbinary.struct):
    _fields_ = [
        (ics_info, 'ics_info'),
        (2, 'ms_mask_present'),
        (lambda s: [0,s.num_window_groups * s.max_sfb][s['ms_mask_present']==1], 'ms_used'),
    ]

@Element.define
class single_channel_element(pbinary.struct):
    type = 0

    _fields_ = [
        (4, 'element_instance_tag'),
        (dyn.clone(individual_channel_stream, attrs={'common_window':0}), 'stream'),
    ]

@Element.define
class channel_pair_element(pbinary.struct):
    type = 1

    _fields_ = [
        (4, 'element_instance_tag'),
        (1, 'common_window'),
        (common_window, 'window'),

        # ???
        (lambda s:dyn.clone(individual_channel_stream, attrs={'common_window':s['common_window']}), 'stream_0'),
        (lambda s:dyn.clone(individual_channel_stream, attrs={'common_window':s['common_window']}), 'stream_1'),
    ]

    def load(self):
        result = super(channel_pair_element, self)
        result.attrs['window_sequence'] = result['window']['ics_info']['window_sequence']
        return result.load()

@Element.define
class coupling_channel_element(pbinary.struct):
    type = 2
    _fields_ = [
        (4, 'element_instance_tag'),
        (1, 'ind_sw_cce_flag'),
        (3, 'num_coupled_elements'),

        # XXX: some array here

        (1, 'cc_domain'),
        (1, 'gain_element_sign'),
        (2, 'gain_element_scale'),

        # ???: individual_channel_stream(0)
        (dyn.clone(individual_channel_stream, attrs={'common_window':0}), 'stream'),

        # XXX: some array here
    ]

@Element.define
class lfe_channel_element(pbinary.struct):
    type = 3
    _fields_ = [
        (4, 'element_instance_tag'),
        # ???: individual_channel_stream(0)
        (dyn.clone(individual_channel_stream, common_window=0), 'stream'),
    ]

@Element.define
class data_stream_element(pbinary.struct):
    type = 4
    def data_stream(self):
        c = self['count']
        count = c['cnt'] + c['esc_count']
        return dyn.clone(pbinary.array, length=count, _object_=extension_payload)

    class __count(pbinary.struct):
        _fields_ = [
            (8, 'cnt'),
            (lambda s: [0,8][s['cnt'] == 255], 'esc_count'),
        ]

    _fields_ = [
        (4, 'element_instance_tag'),
        (1, 'data_byte_align_flag'),
        (__count, 'count'),

        # ???: alignment here
        (pbinary.align(8), 'alignment'),
        (data_stream, 'data_stream'),
    ]

@Element.define
class program_config_element(pbinary.struct):
    type = 5

    class front_element(pbinary.struct):
        _fields_ = [(1,'is_cpe'),(4,'tag_select')]
    class side_element(pbinary.struct):
        _fields_ = [(1,'is_cpe'),(4,'tag_select')]
    class back_element(pbinary.struct):
        _fields_ = [(1,'is_cpe'),(4,'tag_select')]
    class lfe_element(pbinary.struct):
        _fields_ = [(4,'tag_select')]
    class assoc_data_element(pbinary.struct):
        _fields_ = [(4,'tag_select')]
    class valid_cc_element(pbinary.struct):
        _fields_ = [(1,'is_ind_sw'),(4,'tag_select')]

    _fields_ = [
        (4, 'element_instance_tag'),
        (2, 'profile'),
        (4, 'sampling_frequency_index'),
        (4, 'num_front_channel_elements'),

        (4, 'num_side_channel_elements'),
        (4, 'num_back_channel_elements'),
        (2, 'num_lfe_channel_elements'),

        (3, 'num_assoc_data_elements'),
        (4, 'num_valid_cc_elements'),

        (1, 'mono_mixdown_present'),
        (lambda s: [0,4][s['mono_mixdown_present']], 'mono_mixdown_element_number'),

        (1, 'stereo_mixdown_present'),
        (lambda s: [0,4][s['stereo_mixdown_present']], 'stereo_mixdown_element_number'),

        (1, 'matrix_mixdown_idx_present'),
        (lambda s: [0,2][s['matrix_mixdown_idx_present']], 'matrix_mixdown_idx'),
        (lambda s: [0,1][s['matrix_mixdown_idx_present']], 'pseudo_surround_enable'),

        (lambda s: dyn.clone(pbinary.array, length=s['num_front_channel_elements'], _object_=front_element), 'front_element'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_side_channel_elements'], _object_=side_element), 'side_element'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_back_channel_elements'], _object_=back_element), 'back_element'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_lfe_channel_elements'], _object_=lfe_element), 'lfe_element'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_assoc_data_elements'], _object_=assoc_data_element), 'assoc_data_element'),
        (lambda s: dyn.clone(pbinary.array, length=s['num_valid_cc_elements'], _object_=valid_cc_element), 'valid_cc_element'),

        # align here

        (8, 'comment_field_bytes'),
        (lambda s: dyn.clone(pbinary.array, length=s['comment_field_bytes'], _object_=8), 'comment_field')
    ]

class extension_payload(pbinary.struct):
    class fill_data(pbinary.struct):
        _fields_ = [
            (4, 'fill_nibble'),
            (lambda s: dyn.clone(pbinary.array, length=s.cnt, _object_=8), 'fill_byte')
        ]

    def __data(self):
#        print self.attrs
#        return dyn.clone(pbinary.array, _object_=8, length=self.cnt)
        return dyn.clone(pbinary.array, _object_=8, length=0)

        t = self['extension_type']
        if t == EXT_DYNAMIC_RANGE:
            return dynamic_range_info   # XXX
        elif t == EXT_SBR_DATA:
            return dyn.clone(pbinary.array, _object_=8, length=self.cnt)
            return sbr_extension_data   # XXX
        elif t == EXT_SBR_DATA_CRC:
            return dyn.clone(pbinary.array, _object_=8, length=self.cnt)
            return sbr_extension_data   # XXX
        elif t == EXT_FILL_DATA:
            return self.fill_data
        return dyn.clone(pbinary.array, length=self.cnt, _object_=8)

    _fields_ = [
        (4, 'extension_type'),
        (__data, 'extension_data'),
    ]

@Element.define
class fill_element(pbinary.struct):
    type = 6

    def extension_payload(self):
        c = self['count']
        count = c['cnt'] + c['esc_count'] - 1
#        return dyn.clone(pbinary.array, length=count/8, _object_=extension_payload, cnt=count)
        return dyn.clone(pbinary.array, length=count/8, _object_=extension_payload, attrs={'cnt':count})

    class __count(pbinary.struct):
        _fields_ = [
            (4, 'cnt'),
            (lambda s: [0,8][s['cnt'] == 15], 'esc_count'),
        ]

    _fields_ = [
        (__count, 'count'),
        (extension_payload, 'payload'),
    ]

@Element.define
class end_element(pbinary.array):
    type = 7
    _object_ = length = 0

class File(adts_sequence): pass

if __name__ == '__main__':
    import ptypes
    ptypes.setsource( ptypes.file('poc.aac') )
    z = File()
    z = z.l

