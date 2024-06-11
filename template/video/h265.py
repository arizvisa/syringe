import ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

# random utilities used by the specification
u = lambda unsigned_integer: unsigned_integer
s = lambda signed_integer: -signed_integer
f = lambda flag: flag

# exp-golomb codes (page 221, section 9.2)
class exp_golomb(pbinary.struct):
    class _leadingZeroBits(pbinary.terminatedarray):
        _object_ = 1

        #def isTerminator(self, bit):
        #    return bit.int()

        # XXX: we could set an arbitrary maximum length to prevent
        #      infinitely consuming '\0' during allocation...
        #length = 8

        # XXX: ...but it's probably better to switch the terminator check by confirming
        #      that we're allocating (loading) from the empty provider.
        def isTerminator(self, bit):
            return True if isinstance(self.source, ptypes.provider.empty) else bit.int()

        def alloc(self, *args, **attributes):
            if not args:
                return super(exp_golomb._leadingZeroBits, self).alloc(*args, **attributes)

            # exp_golomb doesn't use its values typically, so
            # intead we use our parameter as the array length.
            [length] = args
            res = super(exp_golomb._leadingZeroBits, self).alloc(length=length, **attributes)

            # now we explicitly set all bits to zero, and the last to 1.
            zeros = [0] * len(res)
            return res.set(zeros[:-1] + [1])

    _fields_ = [
        (_leadingZeroBits, 'leadingZeroBits'),
        (lambda self: max(0, self['leadingZeroBits'].bits() - 1), 'codeNum'),
    ]
    def codeNum(self):
        integer = self['codeNum']
        raise NotImplementedError('page 222')

    def alloc(self, **fields):
        """Allocate the instance using the types specified in `fields`.

        The "leadingZeroBits" field can be specified as an integer which
        will result in setting the length of the field (in number of bits).
        """

        # If the field is a native integer, then construct a `_leadingZeroBits`
        # object with the given integer as its length.
        if isinstance(fields.get('leadingZeroBits'), int):
            fields['leadingZeroBits'] = self._leadingZeroBits().alloc(fields['leadingZeroBits'])
        return super(exp_golomb, self).alloc(**fields)

class exp_golomb_unsigned(exp_golomb):
    def number(self):
        return self.codeNum()

class exp_golomb_signed(exp_golomb):
    def number(self):
        res = self.codeNum()
        raise NotImplementedError('page 222 section 9.2.2')

v = None
ue = lambda v: exp_golomb_unsigned
se = lambda v: exp_golomb_signed

# it starts... (in the voice of timon from the lion king)
class nal_unit_header(pbinary.struct):
    _fields_ = [
        (u(1), 'forbidden_zero_bit'),
        (u(6), 'nal_unit_type'),
        (u(6), 'nuh_layer_id'),
        (u(3), 'nuh_temporal_id_plus_1'),
    ]

class nal_unit(pbinary.struct):
    _fields_ = [
        (nal_unit_header, 'nal_unit_header'),
        # FIXME: NumBytesInRbsp
    ]

class profile_tier_level_profile_present_flag(pbinary.struct):
    # page 62
    class _general_profile_idc_4_11(pbinary.struct):
        #class _general_profile_idc_5_9_10_11(pbinary.struct):
        #    _fields_ = [
        #        (u(1), 'general_max_14bit_constraint_flag'),
        #        (u(33), 'general_reserved_zero_33bits'),
        #    ]
        #class _general_profile_idc_5_9_10_11_else(pbinary.struct):
        #    _fields_ = [
        #        (u(34), 'general_reserved_zero_34bits'),
        #    ]

        def __idc_5_9_10_11(true, false):
            def general_profile_idc_5_9_10_11(self):
                parent = self.getparent(profile_tier_level_profile_present_flag)
                values = {5,9,10,11}
                ok = parent['general_profile_idc'] in values or any(parent['general_profile_compatibility_flag'][index] for index in values)
                return true if ok else false
            return general_profile_idc_5_9_10_11

        _fields_ = [
            (u(1), 'general_max_12bit_constraint_flag'),
            (u(1), 'general_max_10bit_constraint_flag'),
            (u(1), 'general_max_8bit_constraint_flag'),
            (u(1), 'general_max_422chroma_constraint_flag'),
            (u(1), 'general_max_420chroma_constraint_flag'),
            (u(1), 'general_max_monochrome_constraint_flag'),
            (u(1), 'general_intra_constraint_flag'),
            (u(1), 'general_one_picture_only_constraint_flag'),
            (u(1), 'general_lower_bit_rate_constraint_flag'),

            # should probably be separate structures...
            (__idc_5_9_10_11(1, 0), 'general_max_14bit_constraint_flag'),
            (__idc_5_9_10_11(33, 0), 'general_reserved_zero_33bits'),
            (__idc_5_9_10_11(0, 34), 'general_reserved_zero_34bits'),
        ]

    class _general_profile_idc_2(pbinary.struct):
        _fields_ = [
            (u(7), 'general_reserved_zero_7bits'),
            (u(1), 'general_one_picture_only_constraint_flag'),
            (u(35), 'general_reserved_zero_35bits'),
        ]

    def __general_profile_idc_check(true, false, values):
        def general_profile_idc_5_9_10_11(self):
            ok = self['general_profile_idc'] in values or any(self['general_profile_compatibility_flag'][index] for index in values)
            return true if ok else false
        return general_profile_idc_5_9_10_11

    # page 63
    _fields_ = [
        (u(2), 'general_profile_space'),
        (u(1), 'general_tier_flag'),
        (u(5), 'general_profile_idc'),
        (dyn.clone(pbinary.array, length=32, _object_=u(1)), 'general_profile_compatibility_flag'),
        (u(1), 'general_progressive_source_flag'),
        (u(1), 'general_interlaced_source_flag'),
        (u(1), 'general_non_packed_constraint_flag'),
        (u(1), 'general_frame_only_constraint_flag'),
        (__general_profile_idc_check(_general_profile_idc_4_11, 0, {4,5,6,7,8,9,10,11}), 'general_profile_idc_4_through_11'),
        (__general_profile_idc_check(_general_profile_idc_2, 0, {2}), 'general_profile_idc_2'),
        (__general_profile_idc_check(0, u(43), {2,4,5,6,7,8,9,10,11}), 'general_reserved_zero_43_bits'),
        (__general_profile_idc_check(u(1), 0, {1,2,3,4,5,9,11}), 'general_inbld_flag'),
        (__general_profile_idc_check(0, u(1), {1,2,3,4,5,9,11}), 'general_reserved_zero_bit'),
    ]

class profile_tier_level(pbinary.struct):
    profile_present_flag = maxNumSubLayersMinus1 = 0
    class sub_layer_flags(pbinary.flags):
        _fields_ = [
            (u(1), 'sub_layer_profile_present'),
            (u(1), 'sub_layer_level_present'),
        ]
    _fields_ = [
        (lambda self: profile_tier_level_profile_present_flag if self.profile_present_flag else 0, 'profile_tier_level_profile'),
        (u(8), 'general_level_idc'),
        (lambda self, sub_layer_flags=sub_layer_flags: dyn.clone(pbinary.array, length=self.maxNumSubLayersMinus1, _object_=sub_layer_flags), 'sub_layers'),
        (lambda self: dyn.clone(pbinary.array, _object_=u(2), length=max(0, 8 - self.maxNumSubLayersMinus1)), 'reserved_zero_2bits'),
    ]

class video_parameter_set_rbsp(pbinary.struct):
    # page 54
    class vps_max_items(pbinary.struct):
        _fields_ = [
            (ue(v), 'vps_max_dec_pic_buffering_minus1'),
            (ue(v), 'vps_max_num_reorder_pics'),
            (ue(v), 'vps_max_latency_increase_plus1'),
        ]
    _fields_ = [
        (u(4), 'vps_video_parameter_set_id'),
        (u(1), 'vps_base_layer_internal_flag'),
        (u(1), 'vps_base_layer_available_flag'),
        (u(6), 'vps_max_layers_minus1'),
        (u(3), 'vps_max_sub_layers_minus1'),
        (u(1), 'vps_temporal_id_nesting_flag'),
        (u(16), 'vps_reserved_0xffff_16bits'),
        (lambda self: dyn.clone(profile_tier_level, profile_present_flag=1, maxNumSubLayersMinus1=self['vps_max_sub_layers_minus1']), 'profile_tier_level'),
        (u(1), 'vps_sub_layer_ordering_info_present_flag'),
        (lambda self, vps_max_items=vps_max_items: dyn.clone(pbinary.array, _object_=vps_max_items, length=self['vps_max_sub_layers_minus1'] if self['vps_sub_layer_ordering_info_present_flag'] else 0), 'vps_max'),
        (u(6), 'vps_max_layer_id'),
        (ue(v), 'vps_num_layer_sets_minus1')
        # page 54
    ]

if __name__ == '__main__':
    import sys, random, h265
    #import importlib; importlib.reload(h265)
    def p2(string): print(string)
    p = p2 if sys.version_info.major < 3 else eval('print')
    state = random.Random()
    p(state.randint(0, pow(2,5)))

    x = pbinary.new(h265.exp_golomb_unsigned)
    c = h265.exp_golomb_unsigned._leadingZeroBits()
    p(c.alloc(5))
    print(c[4])
    c.alloc(length=5)
    x = h265.exp_golomb_unsigned()
    x.alloc(leadingZeroBits=8)

    p(x.a)
    x = h265.video_parameter_set_rbsp()
    p(x.alloc(vps_max_sub_layers_minus1=3, vps_sub_layer_ordering_info_present_flag=1))
    print(x.serialize())

    fields = dict(vps_max_dec_pic_buffering_minus1=1, vps_max_num_reorder_pics=1, vps_max_latency_increase_plus1=1)
    p(x['vps_max'][0].alloc(**{fld : {'leadingZeroBits':5, 'codeNum': state.randint(0, pow(2,5))} for fld in fields}))
    p(x['vps_max'][1].alloc(**{fld : {'leadingZeroBits':5, 'codeNum': state.randint(0, pow(2,5))} for fld in fields}))
    p(x['vps_max'][2].alloc(**{fld : {'leadingZeroBits':5, 'codeNum': state.randint(0, pow(2,5))} for fld in fields}))
    p(x)
    #x.setoffset(x.getoffset(), recurse=True)
    p('-'*80)
    p(x.getposition())
    x.setposition(x.getposition(), recurse=True)
    p(x)
    p(x.bits())
    p(x.serialize())
    p(x.hexdump())

    boffset, Fbitposition = 8 * 0xf, lambda bitmap: 8 * bitmap[0] + bitmap[1]
    iterable = x.traverse(edges=lambda o: iter(o.value), filter=lambda o: Fbitposition(o.getposition()) < boffset <= Fbitposition(o.getposition()) + o.bits())
    p("offset: {:#x}".format(boffset // 8))
    for item in iterable: p(item)
    sys.exit()

    p(x['profile_tier_level'].field('general_level_idc'))

    p(ptypes.config.partial)
    ptypes.Config.pbinary.offset = ptypes.config.partial.bit

    x.setposition(x.getposition(), recurse=True)
    y = pbinary.new(x)
    p(y.hexdump())
    print(x.serialize().hex())

    a = pbinary.new(h265.video_parameter_set_rbsp, source=ptypes.prov.bytes(y.serialize() + b'\xff'*4))
    print(a.l)
    p(a.l)
    print(a['vps_max'][0])

    x.set(vps_video_parameter_set_id=8)
    p(x['profile_tier_level'])
    p(x['profile_tier_level']['profile_tier_level_profile'])

    print(x['vps_max'].serialize().hex())

    #importlib.reload(h265)
    data = bytes.fromhex('084210842108')
    data = b'\x08B'
    x = pbinary.new(h265.exp_golomb_unsigned, source=ptypes.prov.bytes(data))
    p(x.l)
