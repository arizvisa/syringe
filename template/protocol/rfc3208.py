#!/usr/bin/env python
'''https://datatracker.ietf.org/doc/html/rfc3208'''
import builtins, operator, os, math, functools, itertools, sys, types
import ptypes, osi, osi.address
from ptypes import *

# ensure all the integers we inherit from are in the correct byteorder
ptypes.setbyteorder('big')

### pgm constants
IPV4_NLA_AFI = 1

### base types
class uint8_t(pint.uint8_t): pass
class uint16_t(pint.uint16_t): pass
class uint32_t(pint.uint32_t): pass
class uint48_t(pint.uint_t): length = 6

class afi_enum_t(osi.address.family.enum, uint16_t):
    def alloc(self, *values, **attributes):
        if len(values) != 1:
            return super(afi_enum_t, self).alloc(*values, **attributes)
        return super(afi_enum_t, self).alloc(IPV4_NLA_AFI, **attributes)

### pgm definitions
class PGM_OPT(ptype.definition):
    cache = {}

    _default_ = ptype.block
    class _enum_(pbinary.enum):
        length = 7

class PGM_OPT(PGM_OPT):
    class _object_(pbinary.flags):
        _fields_ = [
            (1, 'END'),
            (PGM_OPT.enum, 'MASK'),
        ]
        def set(self, *integer, **fields):
            if not integer:
                return super(PGM_OPT._object_, self).set(**fields)
            [res] = integer
            return self.set(MASK=res & 0x7F, END=True if res & 0x80 else False)
        def alloc(self, *integer, **fields):
            if not integer:
                return super(PGM_OPT._object_, self).alloc(**fields)
            [res] = integer
            if isinstance(res, int):
                return self.a.set(MASK=res & 0x7F, END=True if res & 0x80 else False)
            return self.a.set(MASK=res)

        def int(self):
            res = super(PGM_OPT._object_, self).int()
            return res & 0x7F

class PGM_OPX_MASK(pbinary.enum):
    ''' extensibility bits '''
    length, _values_ = 2, [
        ('IGNORE', 0b00),
        ('INVALIDATE', 0b01),
        ('DISCARD', 0b10),
        ('RESERVED', 0b11),
    ]

class PGM_OP_(pbinary.flags):
    _option_type_ = -1
    def __SPECIFIC(self):
        option_type = getattr(self, '_option_type_', -1)
        return PGM_OPT_SPECIFIC.lookup(option_type, 7)
    _fields_ = [
        (5, 'RESERVED'),
        (1, 'ENCODED'),                 # F-bit
        (PGM_OPX_MASK, 'OPX_MASK'),     # how to handle unknown options
        (1, 'ENCODED_NULL'),            # U-BIT
        (__SPECIFIC, 'SPECIFIC'),
    ]

    def summary(self):
        flags = []
        flags.append('ENCODED') if self['ENCODED'] else flags
        flags.append('ENCODED_NULL') if self['ENCODED_NULL'] else flags
        flags.append("OPX_MASK={:#s}".format(self.field('OPX_MASK')))
        res = [' '.join(flags)] if flags else []
        res.append("RESERVED={:s}".format(self.field('RESERVED').summary())) if self['RESERVED'] else res
        res.append("SPECIFIC={:s}".format(self.field('SPECIFIC').summary()))
        return ' : '.join(res)

class PGM_OPT_SPECIFIC(ptype.definition):
    cache, _object_ = {}, PGM_OP_

#class pgm_opt_header(pstruct.type):
class pgm_opt(pstruct.type):
    '''9. Options'''

    def __flags(self):
        res = self['type'].li
        opt = PGM_OPT.lookup(res.int(), ptype.undefined)
        return opt.flags if hasattr(opt, 'flags') else dyn.clone(PGM_OPT_SPECIFIC.type, _option_type_=res.int())

    def __option(self):
        res = self['type'].li
        option_t = PGM_OPT.get(res.int())
        if issubclass(option_t, parray.block):
            length, fields = self['length'].li, ['type', 'length', 'flags']
            return dyn.clone(option_t, blocksize=lambda self, cb=length.int() - sum(self[fld].li.size() for fld in fields): max(0, cb))
        return option_t

    _fields_ = [
        (PGM_OPT.type, 'type'),
        (uint8_t, 'length'),
        (__flags, 'flags'),
        (__option, 'option'),
    ]

    def alloc(self, **fields):
        if hasattr(fields.get('option'), 'type'):
            fields.setdefault('type', fields['option'].type)
        elif 'type' not in fields:
            fields.setdefault('flags', PGM_OPT_SPECIFIC.type)

        # allocate the requested fields.
        res = super(pgm_opt, self).alloc(**fields)

        # add any fields that were missing
        if 'length' not in fields:
            res['length'].set(res.size())
        if 'type' not in fields and hasattr(res['option'], 'type'):
            res['type'].set(res['option'].type)
        return res

@PGM_OPT.define
class PGM_OPT_LENGTH(uint16_t):
    type, significant = 0x00, False
    class flags(ptype.undefined):
        '''throw away the 16-bit flags entirely.'''
    #_fields_ = [
    #    (uint16_t, 'opt_total_length'),     # total length of all options
    #]

@PGM_OPT.define
class PGM_OPT_FRAGMENT(pstruct.type):
    type, significant = 0x01, False
    _fields_ = [
        (uint32_t, 'opt_sqn'),          # first sequence number
        (uint32_t, 'opt_frag_off'),     # offset
        (uint32_t, 'opt_frag_len'),     # length
    ]
    def set(self, *args, **kwargs):
        res = super(PGM_OPT_FRAGMENT, self).set(*args, **kwargs)
        if res['opt_frag_off'].int() > res['opt_frag_len'].int():
            raise ValueError("{:s} : frag_off ({:d}) is larger than frag_len ({:d})".format(self.instance(), *(res[fld].int() for fld in ['opt_frag_off', 'opt_frag_len'])))
        return res

class PGM_OPT_NAK_SEQNO(uint32_t):
    pass

class PGM_OPT_NAK_SEQNO_LIST(parray.block):
    _object_ = PGM_OPT_NAK_SEQNO
    def summary(self):
        iterable = map("{:d}".format, (item for item in self))
        return "({:d}) [{:s}]".format(len(self), ', '.join(iterable))
    #def blocksize(self):
    #    raise NotImplementedError
    #    p = self.getparent(NAK)
    #    return 4 + 4 * number_of_SQNs

@PGM_OPT.define
class PGM_OPT_NAK_LIST(PGM_OPT_NAK_SEQNO_LIST):
    '''requested sequence number [62].'''
    type, significant = 0x02, False
    #_fields_ = [
    #    (PGM_OPT_NAK_SEQNO_LIST, 'opt_sqn'),    # requested sequence number [62]
    #]

@PGM_OPT.define
class PGM_OPT_JOIN(uint32_t):
    '''Minimum sequence number'''
    type, significant = 0x03, False
    #_fields_ = [
    #    (uint32_t, 'opt_join_min'),     # minimum sequence number
    #]

@PGM_OPT.define
class PGM_OPT_REDIRECT(pstruct.type):
    type, significant = 0x07, True
    def __opt_nla(self):
        return osi.address.family.lookup(self['opt_nla_afi'].li.int())
    _fields_ = [
        (afi_enum_t, 'opt_nla_afi'),    # nla afi
        (uint16_t, 'opt_reserved'),     # reserved
        (__opt_nla, 'opt_nla'),         # dlr nla
    ]
    def alloc(self, **fields):
        fields.setdefault('opt_nla_afi', IPV4_NLA_AFI)
        return super().alloc(**fields)

@PGM_OPT.define
class PGM_OPT_SYN(ptype.block):
    type, significant = 0x0D, False

@PGM_OPT.define
class PGM_OPT_FIN(ptype.block):
    type, significant = 0x0E, False

@PGM_OPT.define
class PGM_OPT_RST(ptype.block):
    type, significant = 0x0F, False

    @PGM_OPT_SPECIFIC.define
    class PGM_OPT_RST(pbinary.struct):
        type = 0x0F
        _fields_ = [
            (1, 'N'),
            (6, 'ErrorCode'),
        ]

@PGM_OPT.define
class PGM_OPT_PARITY_PRM(uint32_t):
    '''Transmission group size.'''
    type, significant = 0x08, True

    @PGM_OPT_SPECIFIC.define
    class Specific(pbinary.flags):
        type, _fields_ = 0x08, [
            (5, 'Unused'),
            (1, 'PROACTIVE'),   # PARITY_PRM_PRO
            (1, 'ONDEMAND'),    # PARITY_PRM_OND
        ]

    #_fields_ = [
    #    (uint32_t, 'parity_prm_tgs'),
    #]

@PGM_OPT.define
class PGM_OPT_PARITY_GRP(uint32_t):
    '''Group number.'''
    type, significant = 0x09, False
    #_fields_ = [
    #    (uint32_t, 'prm_group'),
    #]

@PGM_OPT.define
class PGM_OPT_CURR_TGSIZE(uint32_t):
    '''Actual transmission group size.'''
    type, significant = 0x0A, True      # XXX: unless part of ODATA
    #_fields_ = [
    #    (uint32_t, 'prm_atgsize'),
    #]

@PGM_OPT.define
class PGM_OPT_CR(pstruct.type):
    type, significant = 0x10, True

    @PGM_OPT_SPECIFIC.define
    class Specific(pbinary.flags):
        type, _fields_ = 0x0A, [
            (4, 'Unused'),
            (1, 'L'),   # ne worst link
            (1, 'P'),   # ne worst path
            (1, 'R'),   # rcvr worst path
        ]
    _fields_ = [
        (uint32_t, 'opt_cr_lead'),      # congestion report reference sqn
        (uint16_t, 'opt_cr_ne_wl'),     # ne worst link
        (uint16_t, 'opt_cr_ne_wp'),     # ne worst path
        (uint16_t, 'opt_cr_rx_wp'),     # rcvr worst path
        (uint16_t, 'opt_reserved1'),    # reserved
        (afi_enum_t, 'opt_nla_afi'),    # nla afi
        (uint16_t, 'opt_reserved2'),    # reserved
        (uint32_t, 'opt_cr_rcvr'),      # worst receivers nla
    ]
    def alloc(self, **fields):
        fields.setdefault('opt_nla_afi', IPV4_NLA_AFI)
        return super().alloc(**fields)

@PGM_OPT.define
class PGM_OPT_CRQST(ptype.block):
    type, significant = 0x11, True

    @PGM_OPT_SPECIFIC.define
    class PGM_OPT_CRQST_(pbinary.flags):
        type, _fields_ = 0x11, [
            (4, 'Reserved'),
            (1, 'NEL'),         # request OPT_CR_NE_WL report
            (1, 'NEP'),         # request OPT_CR_NE_WP report
            (1, 'RXP'),         # request OPT_CR_RX_WP report
        ]

@PGM_OPT.define
class PGM_OPT_NAK_BO_IVL(pstruct.type):
    type, significant = 0x04, True
    _fields_ = [
        (uint32_t, 'opt_nak_bo_ivl'),
        (uint32_t, 'opt_nak_bo_ivl_sqn'),
    ]

@PGM_OPT.define
class PGM_OPT_NAK_BO_RNG(ptype.block):
    type, significant = 0x05, True
    _fields_ = [
        (uint32_t, 'opt_nak_max_bo_ivl'),   # maximum nak back-off interval
        (uint32_t, 'opt_nak_min_bo_ivl'),   # minimum nak back-off interval
    ]

@PGM_OPT.define
class PGM_OPT_NBR_UNREACH(ptype.block):
    type, significant = 0x0B, True

@PGM_OPT.define
class PGM_OPT_PATH_NLA(osi.address.in4_addr):
    '''Path NLA.'''
    type, significant = 0x0C, True
    # FIXME: it seems that this is assumed to always be 4-bytes with no AFI to define its type.
    #_fields_ = [
    #    (in_addr, 'opt_path_nla'),      # path nla
    #]

@PGM_OPT.define
class PGM_OPT_INVALID(ptype.block):
    type = 0x7F

####
class pgm_type_e(pint.enum):
    _values_ = [
        ('SPM_TYPE', 0x00),     # 0x00 - 0x03 = SPM-like
        ('POLL_TYPE', 0x01),
        ('POLR_TYPE', 0x02),
        ('OD_TYPE', 0x04),      # 0x04 - 0x07 = DATA-like
        ('RD_TYPE', 0x05),
        ('NAK_TYPE', 0x08),     # 0x08 - 0x0B = NAK-like
        ('NNAK_TYPE', 0x09),
        ('NCF_TYPE', 0x0A),
        ('SPMR_TYPE', 0x0C),    # 0x0C - 0x0F - SPMR-like
    ]

class PGM_(pgm_type_e, uint8_t):
    pass

class pgm_message(ptype.definition):
    cache = {}

class pgm_header(pstruct.type):
    class PGM_OPT_(pbinary.flags):
        _fields_ = [
            (1, 'PARITY'),      # parity packet
            (1, 'VAR_PKTLEN'),  # + variable sized packets
            (4, 'unused'),
            (1, 'NETWORK'),     # network-significant: must be interpreted by network elements
            (1, 'PRESENT'),     # option extension are present
        ]
    _fields_ = [
        (uint16_t, 'pgm_sport'),            # source port: tsi::sport or UDP port depending on direction
        (uint16_t, 'pgm_dport'),            # destination port
        (PGM_, 'pgm_type'),                 # version / packet type
        (PGM_OPT_, 'pgm_options'),          # options
        (uint16_t, 'pgm_checksum'),         # checksum
        (uint48_t, 'pgm_gsi'),              # global source id
        (uint16_t, 'pgm_tsdu_length'),      # tsdu length
    ]
    # XXX: pgm_gsi is composed of sockaddr_in with an ipv4,
    #      or the lower 48-bits of the md5 for a hostname.

@pgm_message.define
class PGM_SPM(pstruct.type):
    type = 0x00
    def __spm_nla(self):
        return osi.address.family.lookup(self['spm_nla_afi'].li.int())
    _fields_ = [
        (uint32_t, 'spm_sqn'),          # spm sequence number
        (uint32_t, 'spm_trail'),        # trailing edge sequence number
        (uint32_t, 'spm_lead'),         # leading edge sequence number
        (afi_enum_t, 'spm_nla_afi'),    # nla afi
        (uint16_t, 'spm_reserved'),     # reserved
        (__spm_nla, 'spm_nla'),         # path nla
    ]
    def alloc(self, **fields):
        fields.setdefault('spm_nla_afi', IPV4_NLA_AFI)
        return super().alloc(**fields)

class PGM_POLL_(pint.enum, uint16_t):
    _values_ = [
        ('GENERAL', 0x00),  # general poll
        ('DLR', 0x01),      # DLR poll
    ]

@pgm_message.define
class PGM_POLL(pstruct.type):
    type = 0x01
    _fields_ = [
        (uint32_t, 'poll_sqn'),         # poll sequence number
        (uint16_t, 'poll_round'),       # poll round
        (PGM_POLL_, 'poll_s_type'),     # poll sub-type
        (afi_enum_t, 'poll_nla_afi'),   # nla afi
        (uint16_t, 'poll_reserved'),    # reserved
        (uint32_t, 'poll_nla'),         # path nla
        (uint32_t, 'poll_bo_ivl'),      # poll back-off interval
        (dyn.block(4), 'poll_rand'),    # random string
        (uint32_t, 'poll_mask'),        # matching bit-mask
    ]
    def alloc(self, **fields):
        fields.setdefault('poll_nla_afi', IPV4_NLA_AFI)
        return super().alloc(**fields)

@pgm_message.define
class PGM_POLR(pstruct.type):
    type = 0x02
    _fields_ = [
        (uint32_t, 'polr_sqn'),         # polr sequence number
        (uint16_t, 'polr_round'),       # polr round
        (uint16_t, 'polr_reserved'),    # reserved
    ]

class DATA(pstruct.type):
    _fields_ = [
        (uint32_t, 'data_sqn'),     # data packet sequence number
        (uint32_t, 'data_trail'),   # trailing edge sequence number
    ]

@pgm_message.define
class PGM_ODATA(DATA):
    type = 0x04

@pgm_message.define
class PGM_RDATA(DATA):
    type = 0x05

@pgm_message.define
class PGM_NAK(pstruct.type):
    type = 0x08
    def __nak_src_nla(self):
        return osi.address.family.lookup(self['nak_src_nla_afi'].li.int())
    def __nak_grp_nla(self):
        return osi.address.family.lookup(self['nak_grp_nla_afi'].li.int())
    _fields_ = [
        (uint32_t, 'nak_sqn'),              # requested sequence number
        (afi_enum_t, 'nak_src_nla_afi'),    # nla afi
        (uint16_t, 'nak_src_reserved'),     # reserved
        (__nak_src_nla, 'nak_src_nla'),     # source nla
        (afi_enum_t, 'nak_grp_nla_afi'),    # nla afi
        (uint16_t, 'nak_grp_reserved'),     # reserved
        (__nak_grp_nla, 'nak_grp_nla'),     # multicast group nla
    ]
    def alloc(self, **fields):
        fields.setdefault('nak_src_nla_afi', IPV4_NLA_AFI)
        fields.setdefault('nak_grp_nla_afi', IPV4_NLA_AFI)
        return super().alloc(**fields)

@pgm_message.define
class PGM_NNAK(PGM_NAK):
    type = 0x09

@pgm_message.define
class PGM_NCF(PGM_NAK):
    type = 0x0A

@pgm_message.define
class PGM_SPMR(ptype.block):
    type = 0x0C

@pgm_message.define
class PGM_ACK(pstruct.type):
    type = 0x0D
    _fields_ = [
        (uint32_t, 'ack_rx_max'),   # RX_MAX
        (uint32_t, 'ack_bitmap'),   # received packets
    ]

# FIXME: the option array...really isn't an array, as the first
#        element is _always_ supposed to be a PGM_OPT_LENGTH.
class pgm_opt_array(parray.type):
    _object_ = pgm_opt
    def has(self, option):
        filtered = (opt for opt in self if isinstance(opt, pgm_opt))
        for opt in filtered:
            if ptypes.istype(option) and isinstance(opt['option'], option):
                return opt

            # check if the option type matches.
            mask = opt['type'].field('MASK')
            if mask[option] or mask.int() == option:
                return True
            continue
        return False

    def by(self, option):
        filtered = (opt for opt in self if isinstance(opt, pgm_opt))
        for opt in filtered:
            if ptypes.istype(option) and isinstance(opt['option'], option):
                return opt

            # if the type matches, then return the current option.
            mask = opt['type'].field('MASK')
            if mask[option] or mask.int() == option:
                return opt
            continue
        raise KeyError(option)

    # prolly worth noting that network-significant options
    # are required to come first.. according to the rfc.
    def has_network_significance(self):
        filtered = (opt for opt in self if isinstance(opt, pgm_opt))
        iterable = (getattr(opt['option'], 'significant', False) for opt in filtered)
        return any(iterable)

    def alloc(self, *values, **attributes):
        if len(values) != 1:
            res = super(pgm_opt_array, self).alloc(*values, **attributes)

        # if we got a single element (should be a list), then be friendly and
        # and convert each of them to the corresponding option (if necessary).
        else:
            [iterable] = values
            Fconvert = lambda item: item if ptypes.isinstance(item) or ptypes.istype(item) else pgm_opt().alloc(**item) if isinstance(item, dict) else pgm_opt().alloc(type=item) if PGM_OPT.enum.has(item) else item
            res = super(pgm_opt_array, self).alloc([Fconvert(item) for item in iterable], **attributes)

        # if the last element is the right element type, then set its END flag.
        if len(res) and isinstance(res[-1], self._object_):
            res[-1]['type'].set(END=1)
        return res

class pgm_opt_exts(parray.terminated, pgm_opt_array):
    #_object_ = pgm_opt_header
    _object_ = pgm_opt
    def isTerminator(self, opt):
        return 'type' in opt and opt['type']['END']

class PGM_EXTS_LENGTH(pgm_opt):
    def __padding_options(self):
        res, fields = self['length'].li, ['type', 'length', 'flags', 'option']
        length = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        return dyn.block(length) if length else ptype.block
    _fields_ = [
        (PGM_OPT.type, 'type'),
        (uint8_t, 'length'),
        (pint.uint_t, 'flags'),
        (uint16_t, 'option'),
        (__padding_options, 'padding(option)'),
    ]
    def alloc(self, **fields):
        fields.setdefault('type', 'PGM_OPT_LENGTH')
        res = super(PGM_EXTS_LENGTH, self).alloc(**fields)
        if 'length' not in fields:
            res['length'].set(sum(self[fld].size() for fld in self))
        if 'option' not in fields:
            res['option'].set(res.size())
        return res

class PGM_EXTS_LENGTH_fake(pgm_opt):
    class _type(PGM_OPT.type):
        _fields_ = [(pbinary.enum, field) for _, field in PGM_OPT.type._fields_]
    _fields_ = [
        (_type, 'type'),
        (pint.uint_t, 'length'),
        (ptype.undefined, 'flags'),
        (pint.uint_t, 'option'),
        (ptype.block, 'padding(option)'),
    ]
    def alloc(self, *args, **fields):
        return super(pgm_opt, self).alloc(*args, **fields)

# XXX: the following structures are ripped from the leaked windows src.
#      it's included because microsoft's implementation of the protocol
#      actually encodes these fields in little- instead of big-endian.
@pint.littleendian
class ULONG(uint32_t): pass
@pint.littleendian
class USHORT(uint16_t): pass
@pint.littleendian
class UCHAR(uint8_t): pass
class tFRAGMENT_OPTIONS(pstruct.type):
    _fields_ = [
        (ULONG, 'MessageFirstSequence'),
        (ULONG, 'MessageOffset'),
        (ULONG, 'MessageLength'),
    ]
class tPOST_PACKET_FEC_CONTEXT(pstruct.type):
    _fields_ = [
        (USHORT, 'EncodedTSDULength'),
        (UCHAR, 'FragmentOptSpecific'),
        (UCHAR, 'Pad'),
        (tFRAGMENT_OPTIONS, 'EncodedFragmentOptions'),
    ]

@osi.network.layer.define
class pgm_packet(pstruct.type):
    type = 113

    def __message(self):
        res = self['pgm_type'].li
        return pgm_message.lookup(res.int())

    def __exts_length(self):
        res = self['pgm_options'].li
        if res['PRESENT']:
            return PGM_EXTS_LENGTH
        return PGM_EXTS_LENGTH_fake

    def __exts(self):
        res = self['exts_length'].li
        if res['option'].int() > res.size():
            return pgm_opt_exts
        return pgm_opt_array

    def __padding_exts(self):
        res, exts = (self[fld].li for fld in ['exts_length', 'exts'])
        length = max(0, res['option'].int() - sum(item.size() for item in [res, exts]))
        return dyn.block(length) if length else ptype.block

    def __data(self):
        res = self['pgm_tsdu_length'].li
        return dyn.block(res.int()) if res.int() else ptype.block

    def __padding_data(self):
        res, fields = self['pgm_tsdu_length'].li, ['data']
        required = res.int() - sum(self[fld].li.size() for fld in fields)
        return dyn.block(required) if required > 0 else ptype.block

    _fields_ = pgm_header._fields_ + [
        (__message, 'msg'),
        (__exts_length, 'exts_length'),
        (__exts, 'exts'),
        (__padding_exts, 'padding(exts)'),
        (__data, 'data'),
        (__padding_data, 'padding'),
    ]

    def alloc(self, **fields):
        # if the "exts" field is a list, then promote it to a pgm_opt_exts.
        if isinstance(fields.get('exts', None), list):
            fields['exts'] = pgm_opt_exts().alloc(fields['exts'])

        # if any option extensions were specified, then
        # ensure that the option extension length is alloc'd.
        if 'exts_length' not in fields and 'exts' in fields:
            fields['exts_length'] = PGM_EXTS_LENGTH

        # alloc all the fields that were specified
        res = super(pgm_packet, self).alloc(**fields)

        # set the type and the transmission unit length
        if 'pgm_type' not in fields and hasattr(res['msg'], 'type'):
            res['pgm_type'].set(res['msg'].type)
        if 'pgm_tsdu_length' not in fields:
            #res['pgm_tsdu_length'].set(res['data'].size())
            res['pgm_tsdu_length'].set(res['data'].size() + res['padding'].size())

        # check if there are any options present.
        if 'pgm_options' not in fields:
            res['exts_length'].size() and res['pgm_options'].set(PRESENT=1)

        # now we process the specific options.
        if 'pgm_options' not in fields and len(res['exts']):
            res['pgm_options'].set(NETWORK=res['exts'].has_network_significance())
            res['pgm_options'].set(PARITY=any(res['exts'].has(parity) for parity in ['PGM_OPT_PARITY_GRP', 'PGM_OPT_PARITY_PRM']))
            res['pgm_options']['PARITY'] and res['exts'].set(VAR_PKTLEN=res['exts'].has('OPT_VAR_PKTLEN'))

        # fix the option length iff it exists.
        if len(res['exts']) and res['exts_length']['type'].field('MASK', 'PGM_OPT_LENGTH'):
            res['exts_length']['option'].set(sum(res[fld].size() for fld in ['exts_length', 'exts', 'padding(exts)']))
        elif isinstance(res['exts_length'], PGM_EXTS_LENGTH):
            res['exts_length']['option'].set(sum(res[fld].size() for fld in ['exts_length', 'exts', 'padding(exts)']))

        # after everything, calculate the checksum.
        if 'pgm_checksum' not in fields:
            res['pgm_checksum'].set(0)
            bytes = res.serialize()
            res['pgm_checksum'].set(osi.utils.checksum(bytes) or 0xFFFF)     # non-zero checksum
        return res

    def properties(self):
        props = super(pgm_packet, self).properties()
        if not self.initializedQ():
            return props

        props['checksum_result'] = cksum = osi.utils.checksum(self.serialize())
        props['checksum'] = self['pgm_checksum'].int()
        if self['pgm_checksum'].int():
            props['checksum_ok'] = cksum == 0
        else:
            props['checksum_missing'] = True
        return props

class GF256(object):
    '''
    Multiplication tables for GF(256) using the generator polynomial ripped from RMCAST.sys.
    These are required for RS(n,k) encoding (and decoding).
    '''

    # used to calculate exp
    gFECLog = [ 0x000000FF, 0x00000000, 0x00000001, 0x00000019, 0x00000002, 0x00000032, 0x0000001A, 0x000000C6, 0x00000003, 0x000000DF, 0x00000033, 0x000000EE, 0x0000001B, 0x00000068, 0x000000C7, 0x0000004B, 0x00000004, 0x00000064, 0x000000E0, 0x0000000E, 0x00000034, 0x0000008D, 0x000000EF, 0x00000081, 0x0000001C, 0x000000C1, 0x00000069, 0x000000F8, 0x000000C8, 0x00000008, 0x0000004C, 0x00000071, 0x00000005, 0x0000008A, 0x00000065, 0x0000002F, 0x000000E1, 0x00000024, 0x0000000F, 0x00000021, 0x00000035, 0x00000093, 0x0000008E, 0x000000DA, 0x000000F0, 0x00000012, 0x00000082, 0x00000045, 0x0000001D, 0x000000B5, 0x000000C2, 0x0000007D, 0x0000006A, 0x00000027, 0x000000F9, 0x000000B9, 0x000000C9, 0x0000009A, 0x00000009, 0x00000078, 0x0000004D, 0x000000E4, 0x00000072, 0x000000A6, 0x00000006, 0x000000BF, 0x0000008B, 0x00000062, 0x00000066, 0x000000DD, 0x00000030, 0x000000FD, 0x000000E2, 0x00000098, 0x00000025, 0x000000B3, 0x00000010, 0x00000091, 0x00000022, 0x00000088, 0x00000036, 0x000000D0, 0x00000094, 0x000000CE, 0x0000008F, 0x00000096, 0x000000DB, 0x000000BD, 0x000000F1, 0x000000D2, 0x00000013, 0x0000005C, 0x00000083, 0x00000038, 0x00000046, 0x00000040, 0x0000001E, 0x00000042, 0x000000B6, 0x000000A3, 0x000000C3, 0x00000048, 0x0000007E, 0x0000006E, 0x0000006B, 0x0000003A, 0x00000028, 0x00000054, 0x000000FA, 0x00000085, 0x000000BA, 0x0000003D, 0x000000CA, 0x0000005E, 0x0000009B, 0x0000009F, 0x0000000A, 0x00000015, 0x00000079, 0x0000002B, 0x0000004E, 0x000000D4, 0x000000E5, 0x000000AC, 0x00000073, 0x000000F3, 0x000000A7, 0x00000057, 0x00000007, 0x00000070, 0x000000C0, 0x000000F7, 0x0000008C, 0x00000080, 0x00000063, 0x0000000D, 0x00000067, 0x0000004A, 0x000000DE, 0x000000ED, 0x00000031, 0x000000C5, 0x000000FE, 0x00000018, 0x000000E3, 0x000000A5, 0x00000099, 0x00000077, 0x00000026, 0x000000B8, 0x000000B4, 0x0000007C, 0x00000011, 0x00000044, 0x00000092, 0x000000D9, 0x00000023, 0x00000020, 0x00000089, 0x0000002E, 0x00000037, 0x0000003F, 0x000000D1, 0x0000005B, 0x00000095, 0x000000BC, 0x000000CF, 0x000000CD, 0x00000090, 0x00000087, 0x00000097, 0x000000B2, 0x000000DC, 0x000000FC, 0x000000BE, 0x00000061, 0x000000F2, 0x00000056, 0x000000D3, 0x000000AB, 0x00000014, 0x0000002A, 0x0000005D, 0x0000009E, 0x00000084, 0x0000003C, 0x00000039, 0x00000053, 0x00000047, 0x0000006D, 0x00000041, 0x000000A2, 0x0000001F, 0x0000002D, 0x00000043, 0x000000D8, 0x000000B7, 0x0000007B, 0x000000A4, 0x00000076, 0x000000C4, 0x00000017, 0x00000049, 0x000000EC, 0x0000007F, 0x0000000C, 0x0000006F, 0x000000F6, 0x0000006C, 0x000000A1, 0x0000003B, 0x00000052, 0x00000029, 0x0000009D, 0x00000055, 0x000000AA, 0x000000FB, 0x00000060, 0x00000086, 0x000000B1, 0x000000BB, 0x000000CC, 0x0000003E, 0x0000005A, 0x000000CB, 0x00000059, 0x0000005F, 0x000000B0, 0x0000009C, 0x000000A9, 0x000000A0, 0x00000051, 0x0000000B, 0x000000F5, 0x00000016, 0x000000EB, 0x0000007A, 0x00000075, 0x0000002C, 0x000000D7, 0x0000004F, 0x000000AE, 0x000000D5, 0x000000E9, 0x000000E6, 0x000000E7, 0x000000AD, 0x000000E8, 0x00000074, 0x000000D6, 0x000000F4, 0x000000EA, 0x000000A8, 0x00000050, 0x00000058, 0x000000AF ]

    # 2x GF(256)
    gFECExp = bytes.fromhex('01020408102040801D3A74E8CD8713264C982D5AB475EAC98F03060C183060C09D274E9C254A94356AD4B577EEC19F23468C050A142850A05DBA69D2B96FDEA15FBE61C2992F5EBC65CA890F1E3C78F0FDE7D3BB6BD6B17FFEE1DFA35BB671E2D9AF4386112244880D1A3468D0BD67CE811F3E7CF8EDC7933B76ECC5973366CC85172E5CB86DDAA94F9E214284152A54A84D9A2952A455AA49923972E4D5B773E6D1BF63C6913F7EFCE5D7B37BF6F1FFE3DBAB4B963162C495376EDCA557AE4182193264C88D070E1C3870E0DDA753A651A259B279F2F9EFC39B2B56AC458A09122448903D7AF4F5F7F3FBEBCB8B0B162C58B07DFAE9CF831B366CD8AD478E01020408102040801D3A74E8CD8713264C982D5AB475EAC98F03060C183060C09D274E9C254A94356AD4B577EEC19F23468C050A142850A05DBA69D2B96FDEA15FBE61C2992F5EBC65CA890F1E3C78F0FDE7D3BB6BD6B17FFEE1DFA35BB671E2D9AF4386112244880D1A3468D0BD67CE811F3E7CF8EDC7933B76ECC5973366CC85172E5CB86DDAA94F9E214284152A54A84D9A2952A455AA49923972E4D5B773E6D1BF63C6913F7EFCE5D7B37BF6F1FFE3DBAB4B963162C495376EDCA557AE4182193264C88D070E1C3870E0DDA753A651A259B279F2F9EFC39B2B56AC458A09122448903D7AF4F5F7F3FBEBCB8B0B162C58B07DFAE9CF831B366CD8AD478E0000')

    # GF(256)
    gFECInverse = bytes.fromhex('00018EF447A77ABAAD9DDD983DAA5D96D872C058E03E4C6690DE5580A0834B2A6CED395160562C8A70D01F4A268B336E48896F2EA4C3405E5022CFA9AB0C15E1365FF8D5924EA60430882B1E166745933823688C811A256113C1CB63970E37412457CA5BB9C4174D528DEFB320EC2F3228D111D9E9FBDA79DB7706BB84CDFEFC1B54A11D7CCCE4B04931272D536902F518DF444F9BBC0F5C0BDCBD94AC09C7A21C829FC634C24605CE3B0D3C9C08BEB787E5EE6BEBF2BFAFC564077B959AAEB61259A53565B8A39ED2F7625A857DA83A2971C8F6F943D7D610737678990A1991143FE6F086B1E2F1FA74F3B46D21B26AE3E7B5EA038FD3C942D4E8757FFF7EFD')

    # FECGroupSize (shift)
    gFECLog2 = bytes.fromhex('000001000200000003000000000000000400000000000000000000000000000005000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007000000')

    gFECMultTable = [ bytes.fromhex(table) for table in ['00' * 0x100
    ,   '000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F404142434445464748494A4B4C4D4E4F505152535455565758595A5B5C5D5E5F606162636465666768696A6B6C6D6E6F707172737475767778797A7B7C7D7E7F808182838485868788898A8B8C8D8E8F909192939495969798999A9B9C9D9E9FA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBFC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDFE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF'
    ,   '00020406080A0C0E10121416181A1C1E20222426282A2C2E30323436383A3C3E40424446484A4C4E50525456585A5C5E60626466686A6C6E70727476787A7C7E80828486888A8C8E90929496989A9C9EA0A2A4A6A8AAACAEB0B2B4B6B8BABCBEC0C2C4C6C8CACCCED0D2D4D6D8DADCDEE0E2E4E6E8EAECEEF0F2F4F6F8FAFCFE1D1F191B151711130D0F090B050701033D3F393B353731332D2F292B252721235D5F595B555751534D4F494B454741437D7F797B757771736D6F696B656761639D9F999B959791938D8F898B85878183BDBFB9BBB5B7B1B3ADAFA9ABA5A7A1A3DDDFD9DBD5D7D1D3CDCFC9CBC5C7C1C3FDFFF9FBF5F7F1F3EDEFE9EBE5E7E1E3'
    ,   '000306050C0F0A09181B1E1D14171211303336353C3F3A39282B2E2D24272221606366656C6F6A69787B7E7D74777271505356555C5F5A59484B4E4D44474241C0C3C6C5CCCFCAC9D8DBDEDDD4D7D2D1F0F3F6F5FCFFFAF9E8EBEEEDE4E7E2E1A0A3A6A5ACAFAAA9B8BBBEBDB4B7B2B1909396959C9F9A99888B8E8D848782819D9E9B989192979485868380898A8F8CADAEABA8A1A2A7A4B5B6B3B0B9BABFBCFDFEFBF8F1F2F7F4E5E6E3E0E9EAEFECCDCECBC8C1C2C7C4D5D6D3D0D9DADFDC5D5E5B585152575445464340494A4F4C6D6E6B686162676475767370797A7F7C3D3E3B383132373425262320292A2F2C0D0E0B080102070415161310191A1F1C'
    ,   '0004080C1014181C2024282C3034383C4044484C5054585C6064686C7074787C8084888C9094989CA0A4A8ACB0B4B8BCC0C4C8CCD0D4D8DCE0E4E8ECF0F4F8FC1D1915110D0905013D3935312D2925215D5955514D4945417D7975716D6965619D9995918D898581BDB9B5B1ADA9A5A1DDD9D5D1CDC9C5C1FDF9F5F1EDE9E5E13A3E32362A2E22261A1E12160A0E02067A7E72766A6E62665A5E52564A4E4246BABEB2B6AAAEA2A69A9E92968A8E8286FAFEF2F6EAEEE2E6DADED2D6CACEC2C627232F2B37333F3B07030F0B17131F1B67636F6B77737F7B47434F4B57535F5BA7A3AFABB7B3BFBB87838F8B97939F9BE7E3EFEBF7F3FFFBC7C3CFCBD7D3DFDB'
    ,   '00050A0F14111E1B282D22273C39363350555A5F44414E4B787D72776C696663A0A5AAAFB4B1BEBB888D82879C999693F0F5FAFFE4E1EEEBD8DDD2D7CCC9C6C35D585752494C434675707F7A61646B6E0D080702191C131625202F2A31343B3EFDF8F7F2E9ECE3E6D5D0DFDAC1C4CBCEADA8A7A2B9BCB3B685808F8A91949B9EBABFB0B5AEABA4A19297989D86838C89EAEFE0E5FEFBF4F1C2C7C8CDD6D3DCD91A1F10150E0B04013237383D26232C294A4F40455E5B54516267686D76737C79E7E2EDE8F3F6F9FCCFCAC5C0DBDED1D4B7B2BDB8A3A6A9AC9F9A95908B8E818447424D485356595C6F6A65607B7E717417121D180306090C3F3A35302B2E2124'
    ,   '00060C0A181E141230363C3A282E242260666C6A787E747250565C5A484E4442C0C6CCCAD8DED4D2F0F6FCFAE8EEE4E2A0A6ACAAB8BEB4B290969C9A888E84829D9B91978583898FADABA1A7B5B3B9BFFDFBF1F7E5E3E9EFCDCBC1C7D5D3D9DF5D5B51574543494F6D6B61677573797F3D3B31372523292F0D0B01071513191F27212B2D3F39333517111B1D0F09030547414B4D5F59535577717B7D6F696365E7E1EBEDFFF9F3F5D7D1DBDDCFC9C3C587818B8D9F999395B7B1BBBDAFA9A3A5BABCB6B0A2A4AEA88A8C868092949E98DADCD6D0C2C4CEC8EAECE6E0F2F4FEF87A7C767062646E684A4C464052545E581A1C161002040E082A2C262032343E38'
    ,   '00070E091C1B1215383F363124232A2D70777E796C6B6265484F464154535A5DE0E7EEE9FCFBF2F5D8DFD6D1C4C3CACD90979E998C8B8285A8AFA6A1B4B3BABDDDDAD3D4C1C6CFC8E5E2EBECF9FEF7F0ADAAA3A4B1B6BFB895929B9C898E87803D3A333421262F2805020B0C191E17104D4A434451565F5875727B7C696E6760A7A0A9AEBBBCB5B29F98919683848D8AD7D0D9DECBCCC5C2EFE8E1E6F3F4FDFA4740494E5B5C55527F78717663646D6A3730393E2B2C25220F08010613141D1A7A7D74736661686F42454C4B5E5950570A0D04031611181F32353C3B2E2920279A9D94938681888FA2A5ACABBEB9B0B7EAEDE4E3F6F1F8FFD2D5DCDBCEC9C0C7'
    ,   '0008101820283038404850586068707880889098A0A8B0B8C0C8D0D8E0E8F0F81D150D053D352D255D554D457D756D659D958D85BDB5ADA5DDD5CDC5FDF5EDE53A322A221A120A027A726A625A524A42BAB2AAA29A928A82FAF2EAE2DAD2CAC2272F373F070F171F676F777F474F575FA7AFB7BF878F979FE7EFF7FFC7CFD7DF747C646C545C444C343C242C141C040CF4FCE4ECD4DCC4CCB4BCA4AC949C848C69617971494159512921393109011911E9E1F9F1C9C1D9D1A9A1B9B1898199914E465E566E667E760E061E162E263E36CEC6DED6EEE6FEF68E869E96AEA6BEB6535B434B737B636B131B030B333B232BD3DBC3CBF3FBE3EB939B838BB3BBA3AB'
    ,   '0009121B242D363F48415A536C657E779099828BB4BDA6AFD8D1CAC3FCF5EEE73D342F2619100B02757C676E5158434AADA4BFB689809B92E5ECF7FEC1C8D3DA7A7368615E574C45323B2029161F040DEAE3F8F1CEC7DCD5A2ABB0B9868F949D474E555C636A71780F061D142B223930D7DEC5CCF3FAE1E89F968D84BBB2A9A0F4FDE6EFD0D9C2CBBCB5AEA798918A83646D767F4049525B2C253E3708011A13C9C0DBD2EDE4FFF68188939AA5ACB7BE59504B427D746F661118030A353C272E8E879C95AAA3B8B1C6CFD4DDE2EBF0F91E170C053A332821565F444D727B6069B3BAA1A8979E858CFBF2E9E0DFD6CDC4232A3138070E151C6B6279704F465D54'
    ,   '000A141E28223C36505A444E78726C66A0AAB4BE88829C96F0FAE4EED8D2CCC65D574943757F616B0D071913252F313BFDF7E9E3D5DFC1CBADA7B9B3858F919BBAB0AEA49298868CEAE0FEF4C2C8D6DC1A100E043238262C4A405E546268767CE7EDF3F9CFC5DBD1B7BDA3A99F958B81474D53596F657B71171D03093F352B2169637D77414B555F39332D27111B050FC9C3DDD7E1EBF5FF99938D87B1BBA5AF343E202A1C160802646E707A4C465852949E808ABCB6A8A2C4CED0DAECE6F8F2D3D9C7CDFBF1EFE58389979DABA1BFB57379676D5B514F452329373D0B011F158E849A90A6ACB2B8DED4CAC0F6FCE2E82E243A30060C12187E746A60565C4248'
    ,   '000B161D2C273A3158534E45747F6269B0BBA6AD9C978A81E8E3FEF5C4CFD2D97D766B60515A474C252E333809021F14CDC6DBD0E1EAF7FC959E8388B9B2AFA4FAF1ECE7D6DDC0CBA2A9B4BF8E8598934A415C57666D707B1219040F3E352823878C919AABA0BDB6DFD4C9C2F3F8E5EE373C212A1B100D066F6479724348555EE9E2FFF4C5CED3D8B1BAA7AC9D968B8059524F44757E6368010A171C2D263B30949F8289B8B3AEA5CCC7DAD1E0EBF6FD242F323908031E157C776A61505B464D1318050E3F3429224B405D56676C717AA3A8B5BE8F849992FBF0EDE6D7DCC1CA6E6578734249545F363D202B1A110C07DED5C8C3F2F9E4EF868D909BAAA1BCB7'
    ,   '000C1814303C2824606C7874505C4844C0CCD8D4F0FCE8E4A0ACB8B4909C88849D918589ADA1B5B9FDF1E5E9CDC1D5D95D5145496D6175793D3125290D011519272B3F33171B0F03474B5F53777B6F63E7EBFFF3D7DBCFC3878B9F93B7BBAFA3BAB6A2AE8A86929EDAD6C2CEEAE6F2FE7A76626E4A46525E1A16020E2A26323E4E42565A7E72666A2E22363A1E12060A8E82969ABEB2A6AAEEE2F6FADED2C6CAD3DFCBC7E3EFFBF7B3BFABA7838F9B97131F0B07232F3B37737F6B67434F5B576965717D5955414D0905111D3935212DA9A5B1BD9995818DC9C5D1DDF9F5E1EDF4F8ECE0C4C8DCD094988C80A4A8BCB034382C2004081C1054584C4064687C70'
    ,   '000D1A1734392E236865727F5C51464BD0DDCAC7E4E9FEF3B8B5A2AF8C81969BBDB0A7AA8984939ED5D8CFC2E1ECFBF66D60777A5954434E05081F12313C2B26676A7D70535E49440F0215183B36212CB7BAADA0838E9994DFD2C5C8EBE6F1FCDAD7C0CDEEE3F4F9B2BFA8A5868B9C910A07101D3E332429626F7875565B4C41CEC3D4D9FAF7E0EDA6ABBCB1929F88851E1304092A27303D767B6C61424F5855737E6964474A5D501B16010C2F223538A3AEB9B4979A8D80CBC6D1DCFFF2E5E8A9A4B3BE9D90878AC1CCDBD6F5F8EFE27974636E4D40575A111C0B0625283F3214190E03202D3A377C71666B4845525FC4C9DED3F0FDEAE7ACA1B6BB9895828F'
    ,   '000E1C123836242A707E6C624846545AE0EEFCF2D8D6C4CA909E8C82A8A6B4BADDD3C1CFE5EBF9F7ADA3B1BF959B89873D33212F050B19174D43515F757B6967A7A9BBB59F91838DD7D9CBC5EFE1F3FD47495B557F71636D37392B250F01131D7A746668424C5E500A041618323C2E209A948688A2ACBEB0EAE4F6F8D2DCCEC0535D4F416B657779232D3F311B150709B3BDAFA18B859799C3CDDFD1FBF5E7E98E80929CB6B8AAA4FEF0E2ECC6C8DAD46E60727C56584A441E10020C26283A34F4FAE8E6CCC2D0DE848A9896BCB2A0AE141A08062C22303E646A78765C52404E2927353B111F0D035957454B616F7D73C9C7D5DBF1FFEDE3B9B7A5AB818F9D93'
    ,   '000F1E113C33222D78776669444B5A55F0FFEEE1CCC3D2DD88879699B4BBAAA5FDF2E3ECC1CEDFD0858A9B94B9B6A7A80D02131C313E2F20757A6B6449465758E7E8F9F6DBD4C5CA9F90818EA3ACBDB2171809062B24353A6F60717E535C4D421A15040B26293837626D7C735E51404FEAE5F4FBD6D9C8C7929D8C83AEA1B0BFD3DCCDC2EFE0F1FEABA4B5BA97988986232C3D321F10010E5B54454A676879762E21303F121D0C03565948476A65747BDED1C0CFE2EDFCF3A6A9B8B79A95848B343B2A25080716194C43525D707F6E61C4CBDAD5F8F7E6E9BCB3A2AD808F9E91C9C6D7D8F5FAEBE4B1BEAFA08D82939C39362728050A1B14414E5F507D72636C'
    ,   '00102030405060708090A0B0C0D0E0F01D0D3D2D5D4D7D6D9D8DBDADDDCDFDED3A2A1A0A7A6A5A4ABAAA9A8AFAEADACA2737071767774757A7B78797E7F7C7D77464544434241404F4E4D4C4B4A494846979495929390919E9F9C9D9A9B989994E5E6E7E0E1E2E3ECEDEEEFE8E9EAEBE5343736313033323D3C3F3E39383B3A3E8F8C8D8A8B888986878485828380818F5E5D5C5B5A595857565554535251505D2C2F2E29282B2A25242726212023222CFDFEFFF8F9FAFBF4F5F6F7F0F1F2F3F9C8CBCACDCCCFCEC1C0C3C2C5C4C7C6C8191A1B1C1D1E1F10111213141516171A6B68696E6F6C6D62636061666764656BBAB9B8BFBEBDBCB3B2B1B0B7B6B5B4B'
    ,   '00112233445566778899AABBCCDDEEFF0D1C2F3E49586B7A8594A7B6C1D0E3F21A0B38295E4F7C6D9283B0A1D6C7F4E517063524534271609F8EBDACDBCAF9E83425160770615243BCAD9E8FF8E9DACB39281B0A7D6C5F4EB1A09382F5E4D7C62E3F0C1D6A7B4859A6B78495E2F3C0D12332011067764554ABBA8998EFFECDDC68794A5B2C3D0E1FE0F1C2D3A4B586976574475621300312EDFCCFDEA9B88B9A7263504136271405FAEBD8C9BEAF9C8D7F6E5D4C3B2A1908F7E6D5C4B3A291805C4D7E6F18093A2BD4C5F6E79081B2A35140736215043726D9C8FBEA9D8CBFAE4657647502132031CEDFECFD8A9BA8B94B5A69780F1E2D3CC3D2E1F08796A5B4'
    ,   '00122436485A6C7E9082B4A6D8CAFCEE3D2F190B75675143ADBF899BE5F7C1D37A685E4C32201604EAF8CEDCA2B08694475563710F1D2B39D7C5F3E19F8DBBA9F4E6D0C2BCAE988A647640522C3E081AC9DBEDFF8193A5B7594B7D6F110335278E9CAAB8C6D4E2F01E0C3A2856447260B3A19785FBE9DFCD233107156B794F5DF5E7D1C3BDAF998B657741532D3F091BC8DAECFE8092A4B6584A7C6E100234268F9DABB9C7D5E3F11F0D3B2957457361B2A09684FAE8DECC223006146A784E5C01132537495B6D7F9183B5A7D9CBFDEF3C2E180A74665042ACBE889AE4F6C0D27B695F4D33211705EBF9CFDDA3B18795465462700E1C2A38D6C4F2E09E8CBAA8'
    ,   '001326354C5F6A79988BBEADD4C7F2E12D3E0B1861724754B5A69380F9EADFCC5A497C6F16053023C2D1E4F78E9DA8BB776451423B281D0EEFFCC9DAA3B08596B4A79281F8EBDECD2C3F0A1960734655998ABFACD5C6F3E0011227344D5E6B78EEFDC8DBA2B18497766550433A291C0FC3D0E5F68F9CA9BA5B487D6E1704312275665340392A1F0CEDFECBD8A1B28794584B7E6D14073221C0D3E6F58C9FAAB92F3C091A63704556B7A49182FBE8DDCE021124374E5D687B9A89BCAFD6C5F0E3C1D2E7F48D9EABB8594A7F6C15063320ECFFCAD9A0B3869574675241382B1E0D9B88BDAED7C4F1E2031025364F5C697AB6A59083FAE9DCCF2E3D081B62714457'
    ,   '0014283C5044786CA0B4889CF0E4D8CC5D4975610D192531FDE9D5C1ADB98591BAAE9286EAFEC2D61A0E32264A5E6276E7F3CFDBB7A39F8B47536F7B17033F2B697D4155392D1105C9DDE1F5998DB1A534201C0864704C589480BCA8C4D0ECF8D3C7FBEF8397ABBF73675B4F23370B1F8E9AA6B2DECAF6E22E3A06127E6A5642D2C6FAEE8296AABE72665A4E22360A1E8F9BA7B3DFCBF7E32F3B07137F6B5743687C4054382C1004C8DCE0F4988CB0A435211D0965714D599581BDA9C5D1EDF9BBAF9387EBFFC3D71B0F33274B5F6377E6F2CEDAB6A29E8A46526E7A16023E2A0115293D5145796DA1B5899DF1E5D9CD5C4874600C182430FCE8D4C0ACB88490'
    ,   '00152A3F54417E6BA8BD8297FCE9D6C34D586772190C3326E5F0CFDAB1A49B8E9A8FB0A5CEDBE4F13227180D66734C59D7C2FDE88396A9BC7F6A55402B3E0114293C03167D6857428194ABBED5C0FFEA64714E5B30251A0FCCD9E6F3988DB2A7B3A6998CE7F2CDD81B0E31244F5A6570FEEBD4C1AABF809556437C690217283D5247786D06132C39FAEFD0C5AEBB84911F0A35204B5E6174B7A29D88E3F6C9DCC8DDE2F79C89B6A360754A5F34211E0B8590AFBAD1C4FBEE2D380712796C53467B6E51442F3A0510D3C6F9EC8792ADB836231C096277485D9E8BB4A1CADFE0F5E1F4CBDEB5A09F8A495C63761D083722ACB98693F8EDD2C704112E3B50457A6F'
    ,   '00162C3A584E7462B0A69C8AE8FEC4D27D6B51472533091FCDDBE1F79583B9AFFAECD6C0A2B48E984A5C667012043E288791ABBDDFC9F3E537211B0D6F794355E9FFC5D3B1A79D8B594F756301172D3B9482B8AECCDAE0F62432081E7C6A504613053F294B5D6771A3B58F99FBEDD7C16E78425436201A0CDEC8F2E48690AABCCFD9E3F59781BBAD7F69534527310B1DB2A49E88EAFCC6D002142E385A4C76603523190F6D7B41578593A9BFDDCBF1E7485E647210063C2AF8EED4C2A0B68C9A26300A1C7E6852449680BAACCED8E2F45B4D776103152F39EBFDC7D1B3A59F89DCCAF0E68492A8BE6C7A40563422180EA1B78D9BF9EFD5C311073D2B495F6573'
    ,   '00172E395C4B7265B8AF9681E4F3CADD6D7A435431261F08D5C2FBEC899EA7B0DACDF4E38691A8BF62754C5B3E291007B7A0998EEBFCC5D20F18213653447D6AA9BE8790F5E2DBCC11063F284D5A6374C4D3EAFD988FB6A17C6B524520370E1973645D4A2F380116CBDCE5F29780B9AE1E09302742556C7BA6B1889FFAEDD4C34F58617613043D2AF7E0D9CEABBC859222350C1B7E6950479A8DB4A3C6D1E8FF9582BBACC9DEE7F02D3A031471665F48F8EFD6C1A4B38A9D40576E791C0B3225E6F1C8DFBAAD94835E49706702152C3B8B9CA5B2D7C0F9EE33241D0A6F7841563C2B120560774E598493AABDD8CFF6E151467F680D1A2334E9FEC7D0B5A29B8C'
    ,   '0018302860785048C0D8F0E8A0B890889D85ADB5FDE5CDD55D456D753D250D15273F170F475F776FE7FFD7CF879FB7AFBAA28A92DAC2EAF27A624A521A022A324E567E662E361E068E96BEA6EEF6DEC6D3CBE3FBB3AB839B130B233B736B435B6971594109113921A9B19981C9D1F9E1F4ECC4DC948CA4BC342C041C544C647C9C84ACB4FCE4CCD45C446C743C240C140119312961795149C1D9F1E9A1B99189BBA38B93DBC3EBF37B634B531B032B33263E160E465E766EE6FED6CE869EB6AED2CAE2FAB2AA829A120A223A726A425A4F577F672F371F078F97BFA7EFF7DFC7F5EDC5DD958DA5BD352D051D554D657D6870584008103820A8B09880C8D0F8E0'
    ,   '0019322B647D564FC8D1FAE3ACB59E878D94BFA6E9F0DBC2455C776E2138130A071E352C637A5148CFD6FDE4ABB299808A93B8A1EEF7DCC5425B7069263F140D0E173C256A735841C6DFF4EDA2BB9089839AB1A8E7FED5CC4B5279602F361D0409103B226D745F46C1D8F3EAA5BC978E849DB6AFE0F9D2CB4C557E6728311A031C052E3778614A53D4CDE6FFB0A9829B9188A3BAF5ECC7DE59406B723D240F161B0229307F664D54D3CAE1F8B7AE859C968FA4BDF2EBC0D95E476C753A230811120B2039766F445DDAC3E8F1BEA78C959F86ADB4FBE2C9D0574E657C332A0118150C273E7168435ADDC4EFF6B9A08B929881AAB3FCE5CED75049627B342D061F'
    ,   '001A342E68725C46D0CAE4FEB8A28C96BDA78993D5CFE1FB6D775943051F312B677D53490F153B21B7AD8399DFC5EBF1DAC0EEF4B2A8869C0A103E246278564CCED4FAE0A6BC92881E042A30766C42587369475D1B012F35A3B9978DCBD1FFE5A9B39D87C1DBF5EF79634D57110B253F140E203A7C664852C4DEF0EAACB69882819BB5AFE9F3DDC7514B657F39230D173C260812544E607AECF6D8C2849EB0AAE6FCD2C88E94BAA0362C02185E446A705B416F753329071D8B91BFA5E3F9D7CD4F557B61273D13099F85ABB1F7EDC3D9F2E8C6DC9A80AEB42238160C4A507E6428321C06405A746EF8E2CCD6908AA4BE958FA1BBFDE7C9D3455F716B2D371903'
    ,   '001B362D6C775A41D8C3EEF5B4AF8299ADB69B80C1DAF7EC756E435819022F34475C716A2B301D069F84A9B2F3E8C5DEEAF1DCC7869DB0AB3229041F5E4568738E95B8A3E2F9D4CF564D607B3A210C172338150E4F547962FBE0CDD6978CA1BAC9D2FFE4A5BE9388110A273C7D664B50647F524908133E25BCA78A91D0CBE6FD011A372C6D765B40D9C2EFF4B5AE8398ACB79A81C0DBF6ED746F425918032E35465D706B2A311C079E85A8B3F2E9C4DFEBF0DDC6879CB1AA3328051E5F4469728F94B9A2E3F8D5CE574C617A3B200D162239140F4E557863FAE1CCD7968DA0BBC8D3FEE5A4BF9289100B263D7C674A51657E534809123F24BDA68B90D1CAE7FC'
    ,   '001C3824706C4854E0FCD8C4908CA8B4DDC1E5F9ADB195893D2105194D517569A7BB9F83D7CBEFF3475B7F63372B0F137A66425E0A16322E9A86A2BEEAF6D2CE534F6B77233F1B07B3AF8B97C3DFFBE78E92B6AAFEE2C6DA6E72564A1E02263AF4E8CCD08498BCA014082C3064785C402935110D5945617DC9D5F1EDB9A5819DA6BA9E82D6CAEEF2465A7E62362A0E127B67435F0B17332F9B87A3BFEBF7D3CF011D3925716D4955E1FDD9C5918DA9B5DCC0E4F8ACB094883C2004184C507468F5E9CDD18599BDA115092D3165795D412834100C5844607CC8D4F0ECB8A4809C524E6A76223E1A06B2AE8A96C2DEFAE68F93B7ABFFE3C7DB6F73574B1F03273B'
    ,   '001D3A2774694E53E8F5D2CF9C81A6BBCDD0F7EAB9A4839E25381F02514C6B76879ABDA0F3EEC9D46F7255481B06213C4A57706D3E230419A2BF9885D6CBECF1130E2934677A5D40FBE6C1DC8F92B5A8DEC3E4F9AAB7908D362B0C11425F78659489AEB3E0FDDAC77C61465B0815322F5944637E2D30170AB1AC8B96C5D8FFE2263B1C01524F6875CED3F4E9BAA7809DEBF6D1CC9F82A5B8031E3924776A4D50A1BC9B86D5C8EFF24954736E3D20071A6C71564B1805223F8499BEA3F0EDCAD735280F12415C7B66DDC0E7FAA9B4938EF8E5C2DF8C91B6AB100D2A3764795E43B2AF8895C6DBFCE15A47607D2E3314097F6245580B16312C978AADB0E3FED9C4'
    ,   '001E3C227866445AF0EECCD28896B4AAFDE3C1DF859BB9A70D13312F756B4957E7F9DBC59F81A3BD17092B356F71534D1A042638627C5E40EAF4D6C8928CAEB0D3CDEFF1ABB59789233D1F015B4567792E30120C56486A74DEC0E2FCA6B89A84342A08164C52706EC4DAF8E6BCA2809EC9D7F5EBB1AF8D933927051B415F7D63BBA58799C3DDFFE14B557769332D0F1146587A643E20021CB6A88A94CED0F2EC5C42607E243A1806ACB2908ED4CAE8F6A1BF9D83D9C7E5FB514F6D732937150B6876544A100E2C329886A4BAE0FEDCC2958BA9B7EDF3D1CF657B59471D03213F8F91B3ADF7E9CBD57F61435D07193B25726C4E500A143628829CBEA0FAE4C6D8'
    ,   '001F3E217C63425DF8E7C6D9849BBAA5EDF2D3CC918EAFB0150A2B3469765748C7D8F9E6BBA4859A3F20011E435C7D622A35140B56496877D2CDECF3AEB1908F938CADB2EFF0D1CE6B74554A170829367E61405F021D3C238699B8A7FAE5C4DB544B6A7528371609ACB3928DD0CFEEF1B9A68798C5DAFBE4415E7F603D22031C3B24051A47587966C3DCFDE2BFA0819ED6C9E8F7AAB5948B2E31100F524D6C73FCE3C2DD809FBEA1041B3A2578674659110E2F306D72534CE9F6D7C8958AABB4A8B79689D4CBEAF5504F6E712C33120D455A7B6439260718BDA2839CC1DEFFE06F70514E130C2D329788A9B6EBF4D5CA829DBCA3FEE1C0DF7A65445B06193827'
    ,   '0020406080A0C0E01D3D5D7D9DBDDDFD3A1A7A5ABA9AFADA27076747A787E7C774543414F4D4B49469492909E9C9A9894E6E0E2ECEEE8EAE53731333D3F393B3E8C8A88868482808F5D5B59575553515D2F292B252721232CFEF8FAF4F6F0F2F9CBCDCFC1C3C5C7C81A1C1E101214161A686E6C626066646BB9BFBDB3B1B7B5BCDED8DAD4D6D0D2DD0F090B050701030F7D7B79777573717EACAAA8A6A4A2A0AB999F9D939197959A484E4C42404644483A3C3E3032343639EBEDEFE1E3E5E7E25056545A585E5C538187858B898F8D81F3F5F7F9FBFDFFF0222426282A2C2E251711131D1F191B14C6C0C2CCCEC8CAC6B4B2B0BEBCBAB8B76563616F6D6B696'
    ,   '0021426384A5C6E71534577691B0D3F22A0B6849AE8FECCD3F1E7D5CBB9AF9D854751637D0F192B341600322C5E487A67E5F3C1DFADBB8996B4A2908EFCEAD8CA889EACB2C0D6E4FBD9CFFDE39187B5A82A3C0E10627446597B6D5F413325170FCDDBE9F78593A1BE9C8AB8A6D4C2F0ED6F794B552731031C3E281A0476605244D6C0F2EC9E88BAA58791A3BDCFD9EBF67462504E3C2A18072533011F6D7B49519385B7A9DBCDFFE0C2D4E6F88A9CAEB33127150B796F5D426076445A283E0C1E5C4A78661402302F0D1B29374553617CFEE8DAC4B6A0928DAFB98B95E7F1C3DB190F3D235147756A485E6C7200162439BBAD9F81F3E5D7C8EAFCCED0A2B4869'
    ,   '0022446688AACCEE0D2F496B85A7C1E31A385E7C92B0D6F4173553719FBDDBF934167052BC9EF8DA391B7D5FB193F5D72E0C6A48A684E2C023016745AB89EFCD684A2C0EE0C2A48665472103EDCFA98B72503614FAD8BE9C7F5D3B19F7D5B3915C7E183AD4F690B251731537D9FB9DBF46640220CEEC8AA84B690F2DC3E187A5D0F294B6587A1C3EDDFF99BB55771133CAE88EAC42600624C7E583A14F6D0B29E4C6A0826C4E280AE9CBAD8F61432507FEDCBA9876543210F3D1B7957B593F1DB89AFCDE30127456B597F1D33D1F795BA280E6C42A086E4CAF8DEBC9270563418CAEC8EA0426406281A3C5E7092B4D6F96B4D2F01E3C5A789BB9DFFD13315775'
    ,   '002346658CAFCAE90526436089AACFEC0A294C6F86A5C0E30F2C496A83A0C5E61437527198BBDEFD113257749DBEDBF81E3D587B92B1D4F71B385D7E97B4D1F2280B6E4DA487E2C12D0E6B48A182E7C422016447AE8DE8CB27046142AB88EDCE3C1F7A59B093F6D5391A7F5CB596F3D036157053BA99FCDF33107556BF9CF9DA50731635DCFF9AB955761330D9FA9FBC5A791C3FD6F590B35F7C193AD3F095B644670221C8EB8EAD41620724CDEE8BA84E6D082BC2E184A74B680D2EC7E481A2785B3E1DF4D7B2917D5E3B18F1D2B79472513417FEDDB89B77543112FBD8BD9E6C4F2A09E0C3A685694A2F0CE5C6A38066452003EAC9AC8F63402506EFCCA98A'
    ,   '0024486C90B4D8FC3D197551AD89E5C17A5E3216EACEA28647630F2BD7F39FBBF4D0BC9864402C08C9ED81A5597D11358EAAC6E21E3A5672B397FBDF23076B4FF5D1BD9965412D09C8EC80A4587C10348FABC7E31F3B5773B296FADE22066A4E0125496D91B5D9FD3C187450AC88E4C07B5F3317EBCFA38746620E2AD6F29EBAF7D3BF9B67432F0BCAEE82A65A7E12368DA9C5E11D395571B094F8DC2004684C03274B6F93B7DBFF3E1A7652AE8AE6C2795D3115E9CDA18544600C28D4F09CB802264A6E92B6DAFE3F1B7753AF8BE7C3785C3014E8CCA08445610D29D5F19DB9F6D2BE9A66422E0ACBEF83A75B7F13378CA8C4E01C385470B195F9DD2105694D'
    ,   '00254A6F94B1DEFB35107F5AA184EBCE6A4F2005FEDBB4915F7A1530CBEE81A4D4F19EBB40650A2FE1C4AB8E75503F1ABE9BF4D12A0F60458BAEC1E41F3A5570B590FFDA21046B4E80A5CAEF14315E7BDFFA95B04B6E0124EACFA0857E5B341161442B0EF5D0BF9A54711E3BC0E58AAF0B2E41649FBAD5F03E1B7451AA8FE0C577523D18E3C6A98C4267082DD6F39CB91D38577289ACC3E6280D6247BC99F6D3A386E9CC37127D5896B3DCF90227486DC9EC83A65D781732FCD9B693684D2207C2E788AD56731C39F7D2BD986346290CA88DE2C73C1976539DB8D7F2092C436616335C7982A7C8ED2306694CB792FDD87C593613E8CDA287496C0326DDF897B2'
    ,   '00264C6A98BED4F22D0B6147B593F9DF5A7C1630C2E48EA877513B1DEFC9A385B492F8DE2C0A604699BFD5F301274D6BEEC8A28476503A1CC3E58FA95B7D17317553391FEDCBA187587E1432C0E68CAA2F096345B791FBDD02244E689ABCD6F0C1E78DAB597F1533ECCAA0867452381E9BBDD7F103254F69B690FADC2E086244EACCA68072543E18C7E18BAD5F791335B096FCDA280E64429DBBD1F70523496F5E781234C6E08AAC73553F19EBCDA7810422486E9CBAD0F6290F6543B197FDDB9FB9D3F507214B6DB294FED82A0C6640C5E389AF5D7B1137E8CEA48270563C1A2B0D6741B395FFD906204A6C9EB8D2F471573D1BE9CFA5835C7A1036C4E288AE'
    ,   '00274E699CBBD2F525026B4CB99EF7D04A6D0423D6F198BF6F482106F3D4BD9A94B3DAFD082F4661B196FFD82D0A6344DEF990B742650C2BFBDCB5926740290E35127B5CA98EE7C010375E798CABC2E57F583116E3C4AD8A5A7D1433C6E188AFA186EFC83D1A735484A3CAED183F5671EBCCA5827750391ECEE980A752751C3B6A4D2403F6D1B89F4F680126D3F49DBA20076E49BC9BF2D505224B6C99BED7F0FED9B09762452C0BDBFC95B24760092EB493FADD280F664191B6DFF80D2A43645F781136C3E48DAA7A5D3413E6C1A88F15325B7C89AEC7E030177E59AC8BE2C5CBEC85A25770193EEEC9A08772553C1B81A6CFE81D3A5374A483EACD381F7651'
    ,   '00285078A088F0D85D750D25FDD5AD85BA92EAC21A324A62E7CFB79F476F173F69413911C9E199B1341C644C94BCC4ECD3FB83AB735B230B8EA6DEF62E067E56D2FA82AA725A220A8FA7DFF72F077F5768403810C8E098B0351D654D95BDC5EDBB93EBC31B334B63E6CEB69E466E163E01295179A189F1D95C740C24FCD4AC84B991E9C119314961E4CCB49C446C143C032B537BA38BF3DB5E760E26FED6AE86D0F880A8705820088DA5DDF52D057D556A423A12CAE29AB2371F674F97BFC7EF6B433B13CBE39BB3361E664E96BEC6EED1F981A9715921098CA4DCF42C047C54022A527AA28AF2DA5F770F27FFD7AF87B890E8C018304860E5CDB59D456D153D'
    ,   '0029527BA48DF6DF557C072EF1D8A38AAA83F8D10E275C75FFD6AD845B72092049601B32EDC4BF961C354E67B891EAC3E3CAB198476E153CB69FE4CD123B406992BBC0E9361F644DC7EE95BC634A311838116A439CB5CEE76D443F16C9E09BB2DBF289A07F562D048EA7DCF52A0378517158230AD5FC87AE240D765F80A9D2FB39106B429DB4CFE66C453E17C8E19AB393BAC1E8371E654CC6EF94BD624B30197059220BD4FD86AF250C775E81A8D3FADAF388A17E572C058FA6DDF42B027950AB82F9D00F265D74FED7AC855A7308210128537AA58CF7DE547D062FF0D9A28BE2CBB099466F143DB79EE5CC133A416848611A33ECC5BE971D344F66B990EBC2'
    ,   '002A547EA882FCD64D671933E5CFB19B9AB0CEE43218664CD7FD83A97F552B0129037D5781ABD5FF644E301ACCE698B2B399E7CD1B314F65FED4AA80567C02285278062CFAD0AE841F354B61B79DE3C9C8E29CB6604A341E85AFD1FB2D0779537B512F05D3F987AD361C62489EB4CAE0E1CBB59F49631D37AC86F8D2042E507AA48EF0DA0C265872E9C3BD97416B153F3E146A4096BCC2E87359270DDBF18FA58DA7D9F3250F715BC0EA94BE68423C16173D4369BF95EBC15A700E24F2D8A68CF6DCA2885E740A20BB91EFC51339476D6C463812C4EE90BA210B755F89A3DDF7DFF58BA1775D230992B8C6EC3A106E44456F113BEDC7B99308225C76A08AF4DE'
    ,   '002B567DAC87FAD1456E1338E9C2BF948AA1DCF7260D705BCFE499B26348351E09225F74A58EF3D84C671A31E0CBB69D83A8D5FE2F047952C6ED90BB6A413C171239446FBE95E8C3577C012AFBD0AD8698B3CEE5341F6249DDF68BA0715A270C1B304D66B79CE1CA5E750823F2D9A48F91BAC7EC3D166B40D4FF82A978532E05240F725988A3DEF5614A371CCDE69BB0AE85F8D30229547FEBC0BD96476C113A2D067B5081AAD7FC68433E15C4EF92B9A78CF1DA0B205D76E2C9B49F4E651833361D604B9AB1CCE77358250EDFF489A2BC97EAC1103B466DF9D2AF84557E03283F14694293B8C5EE7A512C07D6FD80ABB59EE3C819324F64F0DBA68D5C770A21'
    ,   '002C5874B09CE8C47D512509CDE195B9FAD6A28E4A66123E87ABDFF3371B6F43E9C5B19D5975012D94B8CCE024087C50133F4B67A38FFBD76E42361ADEF286AACFE397BB7F53270BB29EEAC6022E5A7635196D4185A9DDF14864103CF8D4A08C260A7E5296BACEE25B77032FEBC7B39FDCF084A86C403418A18DF9D5113D496583AFDBF7331F6B47FED2A68A4E62163A7955210DC9E591BD04285C70B498ECC06A46321EDAF682AE173B4F63A78BFFD390BCC8E4200C7854EDC1B5995D7105294C601438FCD0A488311D694581ADD9F5B69AEEC2062A5E72CBE793BF7B57230FA589FDD115394D61D8F480AC6844301C5F73072BEFC3B79B220E7A5692BECAE6'
    ,   '002D5A77B499EEC375582F02C1EC9BB6EAC7B09D5E7304299FB2C5E82B06715CC9E493BE7D50270ABC91E6CB0825527F230E795497BACDE0567B0C21E2CFB8958FA2D5F83B16614CFAD7A08D4E63143965483F12D1FC8BA6103D4A67A489FED3466B1C31F2DFA885331E694487AADDF0AC81F6DB1835426FD9F483AE6D40371A032E5974B79AEDC0765B2C01C2EF98B5E9C4B39E5D70072A9CB1C6EB2805725FCAE790BD7E532409BF92E5C80B26517C200D7A5794B9CEE355780F22E1CCBB968CA1D6FB3815624FF9D4A38E4D60173A664B3C11D2FF88A5133E4964A78AFDD045681F32F1DCAB86301D6A4784A9DEF3AF82F5D81B36416CDAF780AD6E433419'
    ,   '002E5C72B896E4CA6D43311FD5FB89A7DAF486A8624C3E10B799EBC50F21537DA987F5DB113F4D63C4EA98B67C52200E735D2F01CBE597B91E30426CA688FAD44F61133DF7D9AB85220C7E509AB4C6E895BBC9E72D03715FF8D6A48A406E1C32E6C8BA945E70022C8BA5D7F9331D6F413C12604E84AAD8F6517F0D23E9C7B59B9EB0C2EC26087A54F3DDAF814B651739446A1836FCD2A08E2907755B91BFCDE337196B458FA1D3FD5A740628E2CCBE90EDC3B19F557B092780AEDCF23816644AD1FF8DA36947351BBC92E0CE042A58760B255779B39DEFC166483A14DEF082AC7856240AC0EE9CB2153B4967AD83F1DFA28CFED01A344668CFE193BD77592B05'
    ,   '002F5E71BC93E2CD654A3B14D9F687A8CAE594BB76592807AF80F1DE133C4D6289A6D7F8351A6B44ECC3B29D507F0E21436C1D32FFD0A18E260978579AB5C4EB0F20517EB39CEDC26A45341BD6F988A7C5EA9BB479562708A08FFED11C33426D86A9D8F73A15644BE3CCBD925F70012E4C63123DF0DFAE812906775895BACBE41E31406FA28DFCD37B54250AC7E899B6D4FB8AA568473619B19EEFC00D22537C97B8C9E62B04755AF2DDAC834E61103F5D72032CE1CEBF903817664984ABDAF5113E4F60AD82F3DC745B2A05C8E796B9DBF485AA67483916BE91E0CF022D5C7398B7C6E9240B7A55FDD2A38C416E1F30527D0C23EEC1B09F371869468BA4D5FA'
    ,   '00306050C0F0A0909DADFDCD5D6D3D0D27174777E7D787B7BA8ADAEA7A4A1A2A4E7E2E1E8EBEEEDED3E3B3831323734369590939A999C9F9F4C494A4340454649CACFCCC5C6C3C0C01316151C1F1A191BB8BDBEB7B4B1B2B26164676E6D686B6D2E2B282122272424F7F2F1F8FBFEFDFF5C595A53505556568580838A898C8F825154575E5D585B5B888D8E87848182802326252C2F2A2929FAFFFCF5F6F3F0F6B5B0B3BAB9BCBFBF6C696A6360656664C7C2C1C8CBCECDCD1E1B18111217141B989D9E97949192924144474E4D484B49EAEFECE5E6E3E0E03336353C3F3A393F7C797A7370757676A5A0A3AAA9ACAFAD0E0B080102070404D7D2D1D8DBDEDDD'
    ,   '00316253C4F5A69795A4F7C65160330237065564F3C291A0A293C0F1665704356E5F0C3DAA9BC8F9FBCA99A83F0E5D6C59683B0A9DACFFCECCFDAE9F08396A5BDCEDBE8F18297A4B49782B1A8DBCEFDEEBDA89B82F1E4D7C7E4F1C2DBA8BD8E9B283D0E17647142527164574E3D281B085B4E7D64170231210217243D4E5B687A594C7F66150033230015263F4C596A792A3F0C15667340507366554C3F2A190CBFAA9980F3E6D5C5E6F3C0D9AABF8C9FCCD9EAF38095A6B69580B3AAD9CCFFE79481B2ABD8CDFEEECDD8EBF28194A7B4E7F2C1D8ABBE8D9DBEAB9881F2E7D4C17267544D3E2B18082B3E0D14677241520114273E4D586B7B584D7E671401322'
    ,   '00326456C8FAAC9E8DBFE9DB4577211307356351CFFDAB998AB8EEDC427026140E3C6A58C6F4A29083B1E7D54B792F1D093B6D5FC1F3A59784B6E0D24C7E281A1C2E784AD4E6B08291A3F5C7596B3D0F1B297F4DD3E1B78596A4F2C05E6C3A0812207644DAE8BE8C9FADFBC95765330115277143DDEFB98B98AAFCCE50623406380A5C6EF0C294A6B587D1E37D4F192B3F0D5B69F7C593A1B280D6E47A481E2C36045260FECC9AA8BB89DFED7341172531035567F9CB9DAFBC8ED8EA7446102224164072ECDE88BAA99BCDFF6153053723114775EBD98FBDAE9CCAF8665402302A184E7CE2D086B4A795C3F16F5D0B392D1F497BE5D781B3A092C4F6685A0C3E'
    ,   '00336655CCFFAA9985B6E3D0497A2F1C17247142DBE8BD8E92A1F4C75E6D380B2E1D487BE2D184B7AB98CDFE67540132390A5F6CF5C693A0BC8FDAE9704316255C6F3A0990A3F6C5D9EABF8C152673404B782D1E87B4E1D2CEFDA89B0231645772411427BE8DD8EBF7C491A23B085D6E65560330A99ACFFCE0D386B52C1F4A79B88BDEED744712213D0E5B68F1C297A4AF9CC9FA635005362A194C7FE6D580B396A5F0C35A693C0F13207546DFECB98A81B2E7D44D7E2B1804376251C8FBAE9DE4D782B1281B4E7D61520734AD9ECBF8F3C095A63F0C596A76451023BA89DCEFCAF9AC9F063560534F7C291A83B0E5D6DDEEBB8811227744586B3E0D94A7F2C1'
    ,   '0034685CD0E4B88CBD89D5E16D59053167530F3BB783DFEBDAEEB2860A3E6256CEFAA6921E2A764273471B2FA397CBFFA99DC1F5794D112514207C48C4F0AC9881B5E9DD5165390D3C085460ECD884B0E6D28EBA36025E6A5B6F33078BBFE3D74F7B27139FABF7C3F2C69AAE22164A7E281C4074F8CC90A495A1FDC945712D191F2B7743CFFBA793A296CAFE72461A2E784C1024A89CC0F4C5F1AD9915217D49D1E5B98D0135695D6C580430BC88D4E0B682DEEA66520E3A0B3F6357DBEFB3879EAAF6C24E7A261223174B7FF3C79BAFF9CD91A5291D417544702C1894A0FCC85064380C80B4E8DCEDD985B13D09556137035F6BE7D38FBB8ABEE2D65A6E3206'
    ,   '00356A5FD4E1BE8BB580DFEA61540B3E77421D28A396C9FCC2F7A89D16237C49EEDB84B13A0F50655B6E31048FBAE5D099ACF3C64D7827122C194673F8CD92A7C1F4AB9E15207F4A74411E2BA095CAFFB683DCE96257083D0336695CD7E2BD882F1A4570FBCE91A49AAFF0C54E7B2411586D32078CB9E6D3EDD887B2390C53669FAAF5C04B7E21142A1F4075FECB94A1E8DD82B73C0956635D68370289BCE3D671441B2EA590CFFAC4F1AE9B10257A4F06336C59D2E7B88DB386D9EC67520D385E6B34018ABFE0D5EBDE81B43F0A5560291C4376FDC897A29CA9F6C3487D2217B085DAEF64510E3B05306F5AD1E4BB8EC7F2AD981326794C7247182DA693CCF9'
    ,   '00366C5AD8EEB482AD9BC1F77543192F47712B1D9FA9F3C5EADC86B032045E688EB8E2D456603A0C23154F79FBCD97A1C9FFA59311277D4B6452083EBC8AD0E601376D5BD9EFB583AC9AC0F67442182E46702A1C9EA8F2C4EBDD87B133055F698FB9E3D557613B0D22144E78FACC96A0C8FEA49210267C4A6553093FBD8BD1E702346E58DAECB680AF99C3F577411B2D4573291F9DABF1C7E8DE84B230065C6A8CBAE0D65462380E21174D7BF9CF95A3CBFDA79113257F4966500A3CBE88D2E403356F59DBEDB781AE98C2F476401A2C4472281E9CAAF0C6E9DF85B331075D6B8DBBE1D75563390F20164C7AF8CE94A2CAFCA69012247E4867510B3DBF89D3E5'
    ,   '00376E59DCEBB285A592CBFC794E17205760390E8BBCE5D2F2C59CAB2E194077AE99C0F772451C2B0B3C6552D7E0B98EF9CE97A025124B7C5C6B320580B7EED941762F189DAAF3C4E4D38ABD380F56611621784FCAFDA493B384DDEA6F580136EFD881B633045D6A4A7D241396A1F8CFB88FD6E164530A3D1D2A7344C1F6AF9882B5ECDB5E6930072710497EFBCC95A2D5E2BB8C093E675070471E29AC9BC2F52C1B4275F0C79EA989BEE7D055623B0C7B4C1522A790C9FEDEE9B08702356C5BC3F4AD9A1F2871466651083FBA8DD4E394A3FACD487F261131065F68EDDA83B46D5A0334B186DFE8C8FFA69114237A4D3A0D5463E6D188BF9FA8F1C643742D1A'
    ,   '00387048E0D890A8DDE5AD953D054D75A79FD7EF477F370F7A420A329AA2EAD2536B231BB38BC3FB8EB6FEC66E561E26F4CC84BC142C645C29115961C9F1B981A69ED6EE467E360E7B430B339BA3EBD301397149E1D991A9DCE4AC943C044C74F5CD85BD152D655D28105860C8F0B880526A221AB28AC2FA8FB7FFC76F571F2751692119B189C1F98CB4FCC46C541C24F6CE86BE162E665E2B135B63CBF3BB83023A724AE2DA92AADFE7AF973F074F77A59DD5ED457D350D7840083098A0E8D0F7CF87BF172F675F2A125A62CAF2BA8250682018B088C0F88DB5FDC56D551D25A49CD4EC447C340C7941093199A1E9D1033B734BE3DB93ABDEE6AE963E064E76'
    ,   '0039724BE4DD96AFD5ECA79E3108437AB78EC5FC536A2118625B102986BFF4CD734A013897AEE5DCA69FD4ED427B3009C4FDB68F2019526B1128635AF5CC87BEE6DF94AD023B7049330A4178D7EEA59C5168231AB58CC7FE84BDF6CF6059122B95ACE7DE7148033A4079320BA49DD6EF221B5069C6FFB48DF7CE85BC132A6158D1E8A39A350C477E043D764FE0D992AB665F142D82BBF0C9B38AC1F8576E251CA29BD0E9467F340D774E053C93AAE1D8152C675EF1C883BAC0F9B28B241D566F370E457CD3EAA198E2DB90A9063F744D80B9F2CB645D162F556C271EB188C3FA447D360FA099D2EB91A8E3DA754C073EF3CA81B8172E655C261F546DC2FBB089'
    ,   '003A744EE8D29CA6CDF7B983251F516B87BDF3C96F551B214A703E04A298D6EC1329675DFBC18FB5DEE4AA90360C427894AEE0DA7C46083259632D17B18BC5FF261C5268CEF4BA80EBD19FA50339774DA19BD5EF49733D076C56182284BEF0CA350F417BDDE7A993F8C28CB6102A645EB288C6FC5A602E147F450B3197ADE3D94C763802A49ED0EA81BBF5CF69531D27CBF1BF852319576D063C7248EED49AA05F652B11B78DC3F992A8E6DC7A400E34D8E2AC96300A447E152F615BFDC789B36A501E2482B8F6CCA79DD3E94F753B01EDD799A3053F714B201A546EC8F2BC8679430D3791ABE5DFB48EC0FA5C662812FEC48AB0162C62583309477DDBE1AF95'
    ,   '003B764DECD79AA1C5FEB38829125F6497ACE1DA7B400D365269241FBE85C8F33308457EDFE4A992F6CD80BB1A216C57A49FD2E948733E05615A172C8DB6FBC0665D102B8AB1FCC7A398D5EE4F743902F1CA87BC1D266B50340F4279D8E3AE95556E2318B982CFF490ABE6DD7C470A31C2F9B48F2E155863073C714AEBD09DA6CCF7BA81201B566D09327F44E5DE93A85B602D16B78CC1FA9EA5E8D37249043FFFC489B21328655E3A014C77D6EDA09B68531E2584BFF2C9AD96DBE0417A370CAA91DCE7467D300B6F54192283B8F5CE3D064B70D1EAA79CF8C38EB5142F625999A2EFD4754E03385C672A11B08BC6FD0E357843E2D994AFCBF0BD86271C516A'
    ,   '003C7844F0CC88B4FDC185B90D317549E7DB9FA3172B6F531A26625EEAD692AED3EFAB97231F5B672E12566ADEE2A69A34084C70C4F8BC80C9F5B18D3905417DBB87C3FF4B77330F467A3E02B68ACEF25C602418AC90D4E8A19DD9E5516D29156854102C98A4E0DC95A9EDD165591D218FB3F7CB7F43073B724E0A3682BEFAC66B57132F9BA7E3DF96AAEED2665A1E228CB0F4C87C400438714D093581BDF9C5B884C0FC4874300C45793D01B589CDF15F63271BAF93D7EBA29EDAE6526E2A16D0ECA894201C58642D115569DDE1A599370B4F73C7FBBF83CAF6B28E3A06427E033F7B47F3CF8BB7FEC286BA0E32764AE4D89CA014286C501925615DE9D591AD'
    ,   '003D7A47F4C98EB3F5C88FB2013C7B46F7CA8DB0033E7944023F7845F6CB8CB1F3CE89B4073A7D40063B7C41F2CF88B504397E43F0CD8AB7F1CC8BB605387F42FBC681BC0F3275480E337449FAC780BD0C31764BF8C582BFF9C483BE0D30774A0835724FFCC186BBFDC087BA0934734EFFC285B80B36714C0A37704DFEC384B9EBD691AC1F2265581E236459EAD790AD1C21665BE8D592AFE9D493AE1D20675A1825625FECD196ABEDD097AA1924635EEFD295A81B26615C1A27605DEED394A9102D6A57E4D99EA3E5D89FA2112C6B56E7DA9DA0132E6954122F6855E6DB9CA1E3DE99A4172A6D50162B6C51E2DF98A514296E53E0DD9AA7E1DC9BA615286F52'
    ,   '003E7C42F8C684BAEDD391AF152B6957C7F9BB853F01437D2A145668D2ECAE9093ADEFD16B5517297E40023C86B8FAC4546A2816AC92D0EEB987C5FB417F3D033B054779C3FDBF81D6E8AA942E10526CFCC280BE043A7846112F6D53E9D795ABA896D4EA506E2C12457B3907BD83C1FF6F51132D97A9EBD582BCFEC07A44063876480A348EB0F2CC9BA5E7D9635D1F21B18FCDF34977350B5C62201EA49AD8E6E5DB99A71D23615F0836744AF0CE8CB2221C5E60DAE4A698CFF1B38D37094B754D73310FB58BC9F7A09EDCE25866241A8AB4F6C8724C0E3067591B259FA1E3DDDEE0A29C26185A64330D4F71CBF5B7891927655BE1DF9DA3F4CA88B60C32704E'
    ,   '003F7E41FCC382BDE5DA9BA419266758D7E8A9962B14556A320D4C73CEF1B08FB38CCDF24F70310E56692817AA95D4EB645B1A2598A7E6D981BEFFC07D42033C7B44053A87B8F9C69EA1E0DF625D1C23AC93D2ED506F2E1149763708B58ACBF4C8F7B689340B4A752D12536CD1EEAF901F20615EE3DC9DA2FAC584BB06397847F6C988B70A35744B132C6D52EFD091AE211E5F60DDE2A39CC4FBBA8538074679457A3B04B986C7F8A09FDEE15C63221D92ADECD36E51102F774809368BB4F5CA8DB2F3CC714E0F306857162994ABEAD55A65241BA699D8E7BF80C1FE437C3D023E01407FC2FDBC83DBE4A59A27185966E9D697A8152A6B540C33724DF0CF8EB1'
    ,   '004080C01D5D9DDD3A7ABAFA2767A7E77434F4B46929E9A94E0ECE8E5313D393E8A86828F5B57535D2925212CF8F4F0F9CDC1C5C81C10141A6E62666BBFB3B7BCD8D4D0DD0905010F7B77737EAAA6A2AB9F93979A4E4246483C303439EDE1E5E2565A5E53878B8F81F5F9FDF024282C25111D1914C0CCC8C6B2BEBAB7636F6B687C707479ADA1A5ABDFD3D7DA0E02060F3B37333EEAE6E2EC9894909D49454146F2FEFAF7232F2B25515D5954808C8881B5B9BDB064686C62161A1E13C7CBCFC4A0ACA8A5717D7977030F0B06D2DEDAD3E7EBEFE2363A3E3044484C4195999D9A2E22262BFFF3F7F98D8185885C50545D6965616CB8B4B0BECAC6C2CF1B17131'
    ,   '004182C319589BDA3273B0F12B6AA9E86425E6A77D3CFFBE5617D4954F0ECD8CC8894A0BD1905312FABB7839E3A26120ACED2E6FB5F437769EDF1C5D87C605448DCC0F4E94D51657BFFE3D7CA6E72465E9A86B2AF0B17233DB9A5918C28340014504C7865C1DDE9F7736F5B46E2FECAD2160A3E23879BAFB135291D00A4B88C9074685C41E5F9CDD3574B7F62C6DAEEF6322E1A07A3BF8B95110D3924809CA8BCF8E4D0CD6975415FDBC7F3EE4A56627ABEA2968B2F3307199D81B5A80C102438ACB084993D21150B8F93A7BA1E02362EEAF6C2DF7B67534DC9D5E1FC58447064203C0815B1AD9987031F2B36928EBAA2667A4E53F7EBDFC145596D70D4C8FCE'
    ,   '004284C6155791D32A68AEEC3F7DBBF95416D0924103C5877E3CFAB86B29EFADA8EA2C6EBDFF397B82C0064497D51351FCBE783AE9AB6D2FD6945210C38147054D0FC98B581ADC9E6725E3A17230F6B4195B9DDF0C4E88CA3371B7F52664A2E0E5A76123F0B27436CF8D4B09DA985E1CB1F33577A4E620629BD91F5D8ECC0A489AD81E5C8FCD0B49B0F23476A5E72163CE8C4A08DB995F1DE4A66022F1B375373270B6F42765A3E1185A9CDE0D4F89CB6624E2A07331F7B54C0EC88A591BDD9FD7955311C2804604FDBF793BE8AA6C2E83C1074596D41250A9EB2D6FBCFE387A7F3DFBB96A28EEAC5517D1934002C4862B69AFED3E7CBAF8014385C7145690D2'
    ,   '004386C5115297D42261A4E73370B5F64407C2815516D3906625E0A37734F1B288CB0E4D99DA1F5CAAE92C6FBBF83D7ECC8F4A09DD9E5B18EEAD682BFFBC793A0D4E8BC81C5F9AD92F6CA9EA3E7DB8FB490ACF8C581BDE9D6B28EDAE7A39FCBF85C6034094D71251A7E42162B6F53073C1824704D0935615E3A06526F2B174371A599CDF0B488DCE387BBEFD296AAFEC5E1DD89B4F0CC98A7C3FFAB96D2EEBA892D1145783C00546B0F33675A1E22764D6955013C7844102F4B77231E5A66320175491D2064580C33576B3F02467A2E15310D5964201C4877132F7B46023E6A59FDC195A8ECD084BBDFE3B78ACEF2A69DB985D1ECA894C0FF9BA7F3CE8AB6E2D'
    ,   '004488CC0D4985C11A5E92D617539FDB3470BCF8397DB1F52E6AA6E22367ABEF682CE0A46521EDA97236FABE7F3BF7B35C18D4905115D99D4602CE8A4B0FC387D094581CDD995511CA8E4206C7834F0BE4A06C28E9AD6125FEBA7632F3B77B3FB8FC3074B5F13D79A2E62A6EAFEB27638CC8044081C5094D96D21E5A9BDF1357BDF93571B0F4387CA7E32F6BAAEE226689CD014584C00C4893D71B5F9EDA1652D5915D19D89C5014CF8B4703C2864A0EE1A5692DECA86420FBBF7337F6B27E3A6D29E5A16024E8AC7733FFBB7A3EF2B6591DD1955410DC984307CB8F4E0AC68205418DC9084C80C41F5B97D312569ADE3175B9FD3C78B4F02B6FA3E72662AEEA'
    ,   '00458ACF094C83C6125798DD1B5E91D42461AEEB2D68A7E23673BCF93F7AB5F0480DC2874104CB8E5A1FD0955316D99C6C29E6A36520EFAA7E3BF4B17732FDB890D51A5F99DC135682C7084D8BCE0144B4F13E7BBDF83772A6E32C69AFEA2560D89D5217D1945B1ECA8F4005C386490CFCB97633F5B07F3AEEAB6421E7A26D283D78B7F23471BEFB2F6AA5E02663ACE9195C93D610559ADF0B4E81C4024788CD7530FFBA7C39F6B36722EDA86E2BE4A15114DB9E581DD2974306C98C4A0FC085ADE82762A4E12E6BBFFA3570B6F33C7989CC034680C50A4F9BDE115492D7185DE5A06F2AECA96623F7B27D38FEBB7431C1844B0EC88D4207D396591CDA9F5015'
    ,   '00468CCA054389CF0A4C86C00F4983C5145298DE11579DDB1E5892D41B5D97D1286EA4E22D6BA1E72264AEE82761ABED3C7AB0F6397FB5F33670BAFC3375BFF95016DC9A5513D99F5A1CD6905F19D3954402C88E4107CD8B4E08C2844B0DC781783EF4B27D3BF1B77234FEB87731FBBD6C2AE0A6692FE5A36620EAAC6325EFA9A0E62C6AA5E3296FAAEC2660AFE92365B4F2387EB1F73D7BBEF83274BBFD377188CE04428DCB014782C40E4887C10B4D9CDA105699DF155396D01A5C93D51F59F0B67C3AF5B3793FFABC7630FFB97335E4A2682EE1A76D2BEEA86224EBAD6721D89E5412DD9B5117D2945E18D7915B1DCC8A4006C98F4503C6804A0CC3854F09'
    ,   '00478EC901468FC802458CCB03448DCA04438ACD05428BCC064188CF074089CE084F86C1094E87C00A4D84C30B4C85C20C4B82C50D4A83C40E4980C70F4881C610579ED911569FD812559CDB13549DDA14539ADD15529BDC165198DF175099DE185F96D1195E97D01A5D94D31B5C95D21C5B92D51D5A93D41E5990D71F5891D62067AEE92166AFE82265ACEB2364ADEA2463AAED2562ABEC2661A8EF2760A9EE286FA6E1296EA7E02A6DA4E32B6CA5E22C6BA2E52D6AA3E42E69A0E72F68A1E63077BEF93176BFF83275BCFB3374BDFA3473BAFD3572BBFC3671B8FF3770B9FE387FB6F1397EB7F03A7DB4F33B7CB5F23C7BB2F53D7AB3F43E79B0F73F78B1F6'
    ,   '004890D83D75ADE57A32EAA2470FD79FF4BC642CC98159118EC61E56B3FB236BF5BD652DC88058108FC71F57B2FA226A014991D93C74ACE47B33EBA3460ED69EF7BF672FCA825A128DC51D55B0F82068034B93DB3E76AEE67931E9A1440CD49C024A92DA3F77AFE77830E8A0450DD59DF6BE662ECB835B138CC41C54B1F92169F3BB632BCE865E1689C11951B4FC246C074F97DF3A72AAE27D35EDA54008D098064E96DE3B73ABE37C34ECA44109D199F2BA622ACF875F1788C01850B5FD256D044C94DC3971A9E17E36EEA6430BD39BF0B86028CD855D158AC21A52B7FF276FF1B96129CC845C148BC31B53B6FE266E054D95DD3870A8E07F37EFA7420AD29A'
    ,   '004992DB3970ABE2723BE0A94B02D990E4AD763FDD944F0696DF044DAFE63D74D59C470EECA57E37A7EE357C9ED70C453178A3EA08419AD3430AD1987A33E8A1B7FE256C8EC71C55C58C571EFCB56E27531AC1886A23F8B12168B3FA18518AC3622BF0B95B12C980105982CB2960BBF286CF145DBFF62D64F4BD662FCD845F16733AE1A84A03D891014893DA3871AAE397DE054CAEE73C75E5AC773EDC954E07A6EF347D9FD60D44D49D460FEDA47F36420BD0997B32E9A03079A2EB09409BD2C48D561FFDB46F26B6FF246D8FC61D542069B2FB19508BC2521BC0896B22F9B0115883CA2861BAF3632AF1B85A13C881F5BC672ECC855E1787CE155CBEF72C65'
    ,   '004A94DE357FA1EB6A20FEB45F15CB81D49E400AE1AB753FBEF42A608BC11F55B5FF216B80CA145EDF954B01EAA07E34612BF5BF541EC08A0B419FD53E74AAE0773DE3A94208D69C1D5789C32862BCF6A3E9377D96DC0248C9835D17FCB66822C288561CF7BD6329A8E23C769DD70943165C82C82369B7FD7C36E8A24903DD97EEA47A30DB914F0584CE105AB1FB256F3A70AEE40F459BD1501AC48E652FF1BB5B11CF856E24FAB0317BA5EF044E90DA8FC51B51BAF02E64E5AF713BD09A440E99D30D47ACE63872F3B9672DC68C52184D07D9937832ECA6276DB3F9125886CC2C66B8F219538DC7460CD2987339E7ADF8B26C26CD87591392D8064CA7ED3379'
    ,   '004B96DD317AA7EC6229F4BF5318C58EC48F5219F5BE6328A6ED307B97DC014A95DE0348A4EF3279F7BC612AC68D501B511AC78C602BF6BD3378A5EE024994DF377CA1EA064D90DB551EC388642FF2B9F3B8652EC289541F91DA074CA0EB367DA2E9347F93D8054EC08B561DF1BA672C662DF0BB571CC18A044F92D9357EA3E86E25F8B35F14C9820C479AD13D76ABE0AAE13C779BD00D46C8835E15F9B26F24FBB06D26CA815C1799D20F44A8E33E753F74A9E20E4598D35D16CB806C27FAB15912CF846823FEB53B70ADE60A419CD79DD60B40ACE73A71FFB46922CE855813CC875A11FDB66B20AEE538739FD4094208439ED53972AFE46A21FCB75B10CD86'
    ,   '004C98D42D61B5F95A16C28E773BEFA3B4F82C6099D5014DEEA2763AC38F5B177539EDA15814C08C2F63B7FB024E9AD6C18D5915ECA074389BD7034FB6FA2E62EAA6723EC78B5F13B0FC28649DD105495E12C68A733FEBA704489CD02965B1FD9FD3074BB2FE2A66C5895D11E8A4703C2B67B3FF064A9ED2713DE9A55C10C488C985511DE4A87C3093DF0B47BEF2266A7D31E5A9501CC884276BBFF30A4692DEBCF0246891DD0945E6AA7E32CB87531F084490DC2569BDF1521ECA867F33E7AB236FBBF70E4296DA7935E1AD5418CC8097DB0F43BAF6226ECD815519E0AC7834561ACE827B37E3AF0C4094D8216DB9F5E2AE7A36CF83571BB8F4206C95D90D41'
    ,   '004D9AD72964B3FE521FC8857B36E1ACA4E93E738DC0175AF6BB6C21DF9245085518CF827C31E6AB074A9DD02E63B4F9F1BC6B26D895420FA3EE39748AC7105DAAE7307D83CE1954F8B5622FD19C4B060E4394D9276ABDF05C11C68B7538EFA2FFB26528D69B4C01ADE0377A84C91E535B16C18C723FE8A5094493DE206DBAF74904D39E602DFAB71B5681CC327FA8E5EDA0773AC4895E13BFF2256896DB0C411C5186CB3578AFE24E03D499672AFDB0B8F5226F91DC0B46EAA7703DC38E5914E3AE7934CA87501DB1FC2B6698D5024F470ADD906E23F4B915588FC23C71A6EBB6FB2C619FD20548E4A97E33CD80571A125F88C53B76A1EC400DDA976924F3BE'
    ,   '004E9CD2256BB9F74A04D6986F21F3BD94DA0846B1FF2D63DE90420CFBB56729357BA9E7105E8CC27F31E3AD5A14C688A1EF3D7384CA1856EBA57739CE80521C6A24F6B84F01D39D206EBCF2054B99D7FEB0622CDB954709B4FA286691DF0D435F11C38D7A34E6A8155B89C7307EACE2CB855719EEA0723C81CF1D53A4EA3876D49A4806F1BF6D239ED0024CBBF52769400EDC92652BF9B70A4496D82F61B3FDE1AF7D33C48A5816ABE537798EC0125C753BE9A7501ECC823F71A3ED1A5486C8BEF0226C9BD50749F4BA6826D19F4D032A64B6F80F4193DD602EFCB2450BD9978BC51759AEE0327CC18F5D13E4AA78361F5183CD3A74A6E8551BC987703EECA2'
    ,   '004F9ED1216EBFF0420DDC93632CFDB284CB1A55A5EA3B74C6895817E7A87936155A8BC4347BAAE55718C9867639E8A791DE0F40B0FF2E61D39C4D02F2BD6C232A65B4FB0B4495DA6827F6B94906D798AEE1307F8FC0115EECA3723DCD82531C3F70A1EE1E5180CF7D32E3AC5C13C28DBBF4256A9AD5044BF9B66728D8974609541BCA85753AEBA4165988C73778A9E6D09F4E01F1BE6F2092DD0C43B3FC2D62410EDF90602FFEB1034C9DD2226DBCF3C58A5B14E4AB7A3587C81956A6E938777E31E0AF5F10C18E3C73A2ED1D5283CCFAB5642BDB94450AB8F7266999D607486B24F5BA4A05D49B2966B7F8084796D9EFA0713ECE81501FADE2337C8CC3125D'
    ,   '0050A0F05D0DFDADBAEA1A4AE7B747176939C999346494C4D38373238EDE2E7ED28272228FDF2F7F6838C898356595C5BBEB1B4BE6B646160151A1F15C0CFCACB9E91949E4B444140353A3F35E0EFEAED08070208DDD2D7D6A3ACA9A376797C76B3BCB9B366696C6D18171218CDC2C7C0252A2F25F0FFFAFB8E81848E5B545156F3FCF9F326292C2D585752588D828780656A6F65B0BFBABBCEC1C4CE1B14111BDED1D4DE0B040100757A7F75A0AFAAAD484742489D929796E3ECE9E336393C3D68676268BDB2B7B6C3CCC9C316191C1BFEF1F4FE2B242120555A5F55808F8A80454A4F45909F9A9BEEE1E4EE3B343136D3DCD9D306090C0D78777278ADA2A7A'
    ,   '0051A2F35908FBAAB2E31041EBBA49187928DB8A207182D3CB9A693892C33061F2A35001ABFA09584011E2B31948BBEA8BDA2978D283702139689BCA6031C293F9A85B0AA0F102534B1AE9B81243B0E180D12273D9887B2A326390C16B3AC9980B5AA9F85203F0A1B9E81B4AE0B142137223D0812B7A89D8C091623399C83B6AEFBE4D1CB6E714455D0CFFAE0455A6F796C73465CF9E6D3C247586D77D2CDF8E1D4CBFEE4415E6B7AFFE0D5CF6A754056435C6973D6C9FCED68774258FDE2D7C1647B4E54F1EEDBCA4F50657FDAC5F0E6F3ECD9C366794C5DD8C7F2E84D52677E4B54617BDEC1F4E5607F4A50F5EADFC9DCC3F6EC49566372F7E8DDC7627D485'
    ,   '0052A4F65507F1A3AAF80E5CFFAD5B09491BEDBF1C4EB8EAE3B14715B6E4124092C03664C7956331386A9CCE6D3FC99BDB897F2D8EDC2A787123D587247680D2396B9DCF6C3EC89A93C13765C69462307022D486257781D3DA887E2C8FDD2B79ABF90F5DFEAC5A080153A5F75406F0A2E2B04614B7E51341481AECBE1D4FB9EB7220D684277583D1D88A7C2E8DDF297B3B699FCD6E3CCA9891C33567C4966032E0B24416B5E711434A18EEBC1F4DBBE9A9FB0D5FFCAE580A0351A7F55604F2A04B19EFBD1E4CBAE8E1B34517B4E610420250A6F45705F3A1A8FA0C5EFDAF590BD98B7D2F8CDE287A7321D785267482D090C23466C59761333A689ECC6F3DCB99'
    ,   '0053A6F55102F7A4A2F10457F3A05506590AFFAC085BAEFDFBA85D0EAAF90C5FB2E11447E3B045161043B6E54112E7B4EBB84D1EBAE91C4F491AEFBC184BBEED792ADF8C287B8EDDDB887D2E8AD92C7F207386D57122D78482D12477D3807526CB986D3E9AC93C6F693ACF9C386B9ECD92C13467C3906536306396C56132C794F2A15407A3F005565003F6A50152A7F4ABF80D5EFAA95C0F095AAFFC580BFEAD4013E6B51142B7E4E2B14417B3E01546194ABFEC481BEEBDBBE81D4EEAB94C1F8BD82D7EDA897C2F297A8FDC782BDE8DD281742783D025767023D685217287D4396A9FCC683BCE9D9BC83D6ECA996C3F6033C695316297C4C291643793C03566'
    ,   '0054A8FC4D19E5B19ACE3266D7837F2B297D81D56430CC98B3E71B4FFEAA56025206FAAE1F4BB7E3C89C603485D12D797B2FD38736629ECAE1B5491DACF80450A4F00C58E9BD41153E6A96C27327DB8F8DD92571C094683C1743BFEB5A0EF2A6F6A25E0ABBEF13476C38C490217589DDDF8B772392C63A6E4511EDB9085CA0F45501FDA9184CB0E4CF9B673382D62A7E7C28D480316599CDE6B24E1AABFF03570753AFFB4A1EE2B69DC93561D084782C2E7A86D26337CB9FB4E01C48F9AD5105F1A5590DBCE814406B3FC39726728EDAD88C702495C13D694216EABE0F5BA7F3A3F70B5FEEBA4612396D91C57420DC888ADE2276C7936F3B1044B8EC5D09F5A1'
    ,   '0055AAFF491CE3B692C7386DDB8E7124396C93C67025DA8FABFE0154E2B7481D7227D88D3B6E91C4E0B54A1FA9FC03564B1EE1B40257A8FDD98C732690C53A6FE4B14E1BADF807527623DC893F6A95C0DD88772294C13E6B4F1AE5B00653ACF996C33C69DF8A75200451AEFB4D18E7B2AFFA0550E6B34C193D6897C27421DE8BD5807F2A9CC936634712EDB80E5BA4F1ECB94613A5F00F5A7E2BD48137629DC8A7F20D58EEBB441135609FCA7C29D6839ECB3461D7827D280C59A6F34510EFBA31649BCE782DD287A3F6095CEABF4015085DA2F74114EBBE9ACF3065D386792C4316E9BC0A5FA0F5D1847B2E98CD32677A2FD085336699CCE8BD4217A1F40B5E'
    ,   '0056ACFA4513E9BF8ADC2670CF996335095FA5F34C1AE0B683D52F79C6906A3C1244BEE85701FBAD98CE3462DD8B71271B4DB7E15E08F2A491C73D6BD482782E247288DE6137CD9BAEF80254EBBD47112D7B81D7683EC492A7F10B5DE2B44E1836609ACC7325DF89BCEA1046F9AF55033F6993C57A2CD680B5E3194FF0A65C0A481EE4B20D5BA1F7C2946E3887D12B7D4117EDBB0452A8FECB9D67318ED822745A0CF6A01F49B3E5D0867C2A95C3396F5305FFA91640BAECD98F75239CCA30666C3AC096297F85D3E6B04A1CA3F50F596533C99F20768CDAEFB94315AAFC06507E28D2843B6D97C1F4A2580EB1E71D4B7721DB8D32649EC8FDAB5107B8EE1442'
    ,   '0057AEF94116EFB882D52C7BC3946D3A194EB7E0580FF6A19BCC3562DA8D742332659CCB7324DD8AB0E71E49F1A65F082B7C85D26A3DC493A9FE0750E8BF46116433CA9D25728BDCE6B1481FA7F0095E7D2AD3843C6B92C5FFA85106BEE910475601F8AF1740B9EED4837A2D95C23B6C4F18E1B60E59A0F7CD9A63348CDB2275C89F663189DE27704A1DE4B30B5CA5F2D1867F2890C73E695304FDAA1245BCEBFAAD5403BBEC1542782FD681396E97C0E3B44D1AA2F50C5B6136CF9820778ED9ACFB0255EDBA43142E7980D76F38C196B5E21B4CF4A35A0D376099CE7621D88F9EC93067DF8871261C4BB2E55D0AF3A487D0297EC691683F0552ABFC4413EABD'
    ,   '0058B0E87D25CD95FAA24A1287DF376FE9B1590194CC247C134BA3FB6E36DE86CF977F27B2EA025A356D85DD4810F8A0267E96CE5B03EBB3DC846C34A1F9114983DB336BFEA64E167921C991045CB4EC6A32DA82174FA7FF90C82078EDB55D054C14FCA4316981D9B6EE065ECB937B23A5FD154DD88068305F07EFB7227A92CA1B43ABF3663ED68EE1B951099CC42C74F2AA421A8FD73F670850B8E0752DC59DD48C643CA9F119412E769EC6530BE3BB3D658DD54018F0A8C79F772FBAE20A5298C02870E5BD550D623AD28A1F47AFF77129C1990C54BCE48BD33B63F6AE461E570FE7BF2A729AC2ADF51D45D0886038BEE60E56C39B732B441CF4AC396189D1'
    ,   '0059B2EB7920CB92F2AB40198BD23960F9A04B1280D9326B0B52B9E0722BC099EFB65D0496CF247D1D44AFF6643DD68F164FA4FD6F36DD84E4BD560F9DC42F76C39A7128BAE30851316883DA4811FAA33A6388D1431AF1A8C8917A23B1E8035A2C759EC7550CE7BEDE876C35A7FE154CD58C673EACF51E47277E95CC5E07ECB59BC22970E2BB50096930DB821049A2FB623BD0891B42A9F090C9227BE9B05B02742DC69F0D54BFE686DF346DFFA64D148DD43F66F4AD461F7F26CD94065FB4ED5801EAB3217893CAAAF31841D38A6138A1F8134AD8816A33530AE1B82A7398C1B7EE055CCE977C25451CF7AE3C658ED74E17FCA5376E85DCBCE50E57C59C772E'
    ,   '005AB4EE752FC19BEAB05E049FC52B71C9937D27BCE60852237997CD560CE2B88FD53B61FAA04E14653FD18B104AA4FE461CF2A8336987DDACF61842D9836D370359B7ED762CC298E9B35D079CC62872CA907E24BFE50B51207A94CE550FE1BB8CD63862F9A34D17663CD2881349A7FD451FF1AB306A84DEAFF51B41DA806E34065CB2E87329C79DECB6580299C32D77CF957B21BAE00E54257F91CB500AE4BE89D33D67FCA648126339D78D164CA2F8401AF4AE356F81DBAAF01E44DF856B31055FB1EB702AC49EEFB55B019AC02E74CC967822B9E30D57267C92C85309E7BD8AD03E64FFA54B11603AD48E154FA1FB4319F7AD366C82D8A9F31D47DC866832'
    ,   '005BB6ED712AC79CE2B9540F93C8257ED9826F34A8F31E453B608DD64A11FCA7AFF41942DE8568334D16FBA03C678AD1762DC09B075CB1EA94CF2279E5BE53084318F5AE326984DFA1FA174CD08B663D9AC12C77EBB05D067823CE950952BFE4ECB75A019DC62B700E55B8E37F24C992356E83D8441FF2A9D78C613AA6FD104B86DD306BF7AC411A643FD289154EA3F85F04E9B22E7598C3BDE60B50CC977A2129729FC45803EEB5CB907D26BAE10C57F0AB461D81DA376C1249A4FF6338D58EC59E7328B4EF0259277C91CA560DE0BB1C47AAF16D36DB80FEA548138FD439626A31DC871B40ADF688D33E65F9A24F14B3E8055EC299742F510AE7BC207B96CD'
    ,   '005CB8E46D31D589DA86623EB7EB0F53A9F5114DC4987C20732FCB971E42A6FA4F13F7AB227E9AC695C92D71F8A4401CE6BA5E028BD7336F3C6084D8510DE9B59EC2267AF3AF4B174418FCA0297591CD376B8FD35A06E2BEEDB1550980DC3864D18D6935BCE004580B57B3EF663ADE827824C09C1549ADF1A2FE1A46CF93772B217D99C54C10F4A8FBA7431F96CA2E7288D4306CE5B95D01520EEAB63F6387DB6E32D68A035FBBE7B4E80C50D985613DC79B7F23AAF6124E1D41A5F9702CC894BFE3075BD28E6A366539DD810854B0EC164AAEF27B27C39FCC907428A1FD1945F0AC48149DC125792A7692CE471BFFA35905E1BD34688CD083DF3B67EEB2560A'
    ,   '005DBAE76934D38ED28F6835BBE6015CB9E4035ED08D6A376B36D18C025FB8E56F32D588065BBCE1BDE0075AD4896E33D68B6C31BFE205580459BEE36D30D78ADE836439B7EA0D500C51B6EB6538DF82673ADD800E53B4E9B5E80F52DC81663BB1EC0B56D885623F633ED9840A57B0ED0855B2EF613CDB86DA87603DB3EE0954A1FC1B46C895722F732EC9941A47A0FD1845A2FF712CCB96CA97702DA3FE1944CE937429A7FA1D401C41A6FB7528CF92772ACD901E43A4F9A5F81F42CC91762B7F22C598164BACF1ADF0174AC4997E23C69B7C21AFF215481449AEF37D20C79A104DAAF77924C39EC29F7825ABF6114CA9F4134EC09D7A277B26C19C124FA8F5'
    ,   '005EBCE2653BD987CA947628AFF1134D89D7356BECB2500E431DFFA126789AC40F51B3ED6A34D688C59B7927A0FE1C4286D83A64E3BD5F014C12F0AE297795CB1E40A2FC7B25C799D48A6836B1EF0D5397C92B75F2AC4E105D03E1BF386684DA114FADF3742AC896DB856739BEE0025C98C6247AFDA3411F520CEEB037698BD53C6280DE5907E5BBF6A84A1493CD2F71B5EB0957D08E6C327F21C39D1A44A6F8336D8FD15608EAB4F9A7451B9CC2207EBAE40658DF81633D702ECC92154BA9F7227C9EC04719FBA5E8B6540A8DD3316FABF51749CE90722C613FDD83045AB8E62D7391CF4816F4AAE7B95B0582DC3E60A4FA1846C19F7D236E30D28C0B55B7E9'
    ,   '005FBEE1613EDF80C29D7C23A3FC1D4299C62778F8A746195B04E5BA3A6584DB2F7091CE4E11F0AFEDB2530C8CD3326DB6E90857D7886936742BCA95154AABF45E01E0BF3F6081DE9CC3227DFDA2431CC7987926A6F91847055ABBE4643BDA85712ECF90104FAEF1B3EC0D52D28D6C33E8B7560989D637682A7594CB4B14F5AABCE3025DDD82633C7E21C09F1F40A1FE257A9BC4441BFAA5E7B8590686D9386793CC2D72F2AD4C13510EEFB0306F8ED10A55B4EB6B34D58AC8977629A9F61748E2BD5C0383DC3D62207F9EC1411EFFA07B24C59A1A45A4FBB9E60758D8876639CD92732CACF3124D0F50B1EE6E31D08F540BEAB5356A8BD496C92877F7A84916'
    ,   '0060C0A09DFD5D3D2747E787BADA7A1A4E2E8EEED3B313736909A9C9F49434549CFC5C3C0161C1A1BBDB7B1B2646E686D2B212724F2F8FEFF59535556808A8C82545E585B8D878180262C2A29FFF5F3F6B0BABCBF69636564C2C8CECD1B11171B9D979192444E4849EFE5E3E0363C3A3F79737576A0AAACAD0B010704D2D8DED4A2A8AEAD7B717776D0DADCDF09030500464C4A499F959392343E383BEDE7E1ED6B616764B2B8BEBF19131516C0CACCC98F858380565C5A5BFDF7F1F2242E2826F0FAFCFF2923252482888E8D5B515752141E181BCDC7C1C0666C6A69BFB5B3BF39333536E0EAECED4B41474492989E9BDDD7D1D2040E0809AFA5A3A0767C7A7'
    ,   '0061C2A399F85B3A2F4EED8CB6D774155E3F9CFDC7A605647110B3D2E8892A4BBCDD7E1F2544E78693F251300A6BC8A9E28320417B1AB9D8CDAC0F6E543596F76504A7C6FC9D3E5F4A2B88E9D3B211703B5AF998A2C360011475D6B78DEC4F2ED9B81B7A402182E3F69734556F0EADCC87E645241E7FDCBDA8C96A0B3150F392CAAB0869533291F0E58427467C1DBEDF94F556370D6CCFAEBBDA79182243E0817617B4D5EF8E2D4C59389BFAC0A102632849EA8BB1D073120766C5A49EFF5C3DAFCE6D0C3657F49580E142231978DBBAF19033526809AACBDEBF1C7D472685E41372D1B08AEB48293C5DFE9FA5C467064D2C8FEED4B516776203A0C1FB9A3958'
    ,   '0062C4A695F751333755F391A2C066046E0CAAC8FB993F5D593B9DFFCCAE086ADCBE187A492B8DEFEB892F4D7E1CBAD8B2D076142745E38185E741231072D4B6A5C761033052F49692F056340765C3A1CBA90F6D5E3C9AF8FC9E385A690BADCF791BBDDFEC8E284A4E2C8AE8DBB91F7D1775D3B182E046242042E486B5D77113573593F1C2A006646002A4C6F5973153395BFD9FACCE680A0E6CCAA89BF95F3D8BE94F2D1E7CDAB8BCDE781A294BED8FE58721437012B4D6D2B01674472583E1F29036546705A3C1C5A70163503294F69CFE583A096BCDAFABC96F0D3E5CFA982E4CEA88BBD97F1D197BDDBF8CEE482A402284E6D5B711737715B3D1E2802644'
    ,   '0063C6A591F257343F5CF99AAECD680B7E1DB8DBEF8C294A412287E4D0B31675FC9F3A596D0EABC8C3A00566523194F782E144271370D5B6BDDE7B182C4FEA89E58623407417B2D1DAB91C7F4B288DEE9BF85D3E0A69CCAFA4C762013556F390197ADFBC88EB4E2D2645E083B7D471126704A1C2F6953053583B9EFDC9AA0F6CD7B41172462580E3E88B2E4D791ABFDCA9CA6F0C385BFE9D96F550330764C1A22B48ED8EBAD97C1F1477D2B185E64320553693F0C4A702616A09ACCFFB983D5E3251F497A3C065060D6ECBA89CFF5A394C2F8AE9DDBE1B787310B5D6E2812447CEAD086B5F3C99FAF19237546003A6C5B0D376152142E7848FEC492A1E7DD8BB'
    ,   '0064C8AC8DE945210763CFAB8AEE42260E6AC6A283E74B2F096DC1A584E04C281C78D4B091F5593D1B7FD3B796F25E3A1276DABE9FFB57331571DDB998FC5034385CF094B5D17D193F5BF793B2D67A1E3652FE9ABBDF73173155F99DBCD874102440EC88A9CD61052347EB8FAECA66022A4EE286A7C36F0B2D49E581A0C4680C7014B8DCFD9935517713BFDBFA9E32567E1AB6D2F3973B5F791DB1D5F4903C586C08A4C0E185294D6B0FA3C7E6822E4A6206AACEEF8B27436501ADC9E88C2044482C80E4C5A10D694F2B87E3C2A60A6E46228EEACBAF0367412589EDCCA8046054309CF8D9BD117553379BFFDEBA16725A3E92F6D7B31F7B5D3995F1D0B4187C'
    ,   '0065CAAF89EC43260F6AC5A086E34C291E7BD4B197F25D381174DBBE98FD52373C59F693B5D07F1A3356F99CBADF70152247E88DABCE61042D48E782A4C16E0B781DB2D7F1943B5E7712BDD8FE9B34516603ACC9EF8A2540690CA3C6E0852A4F44218EEBCDA807624B2E81E4C2A7086D5A3F90F5D3B6197C55309FFADCB91673F0953A5F791CB3D6FF9A35507613BCD9EE8B24416702ADC8E1842B4E680DA2C7CCA9066345208FEAC3A6096C4A2F80E5D2B7187D5B3E91F4DDB8177254319EFB88ED42270164CBAE87E24D280E6BC4A196F35C391F7AD5B099FC53361075DABFB4D17E1B3D58F792BBDE71143257F89DAACF60052346E98CA5C06F0A2C49E683'
    ,   '0066CCAA85E3492F1771DBBD92F45E382E48E284ABCD6701395FF593BCDA70165C3A90F6D9BF15734B2D87E1CEA802647214BED8F7913B5D6503A9CFE0862C4AB8DE74123D5BF197AFC963052A4CE68096F05A3C1375DFB981E74D2B0462C8AEE482284E6107ADCBF3953F597610BADCCAAC06604F2983E5DDBB1177583E94F26D0BA1C7E88E24427A1CB6D0FF99335543258FE9C6A00A6C543298FED1B71D7B3157FD9BB4D2781E2640EA8CA3C56F091F79D3B59AFC5630086EC4A28DEB4127D5B3197F50369CFAC2A40E6847218BEDFB9D37517E18B2D4EC8A2046690FA5C389EF45230C6AC0A69EF852341B7DD7B1A7C16B0D2244EE88B0D67C1A3553F99F'
    ,   '0067CEA981E64F281F78D1B69EF950373E59F097BFD871162146EF88A0C76E097C1BB2D5FD9A33546304ADCAE2852C4B42258CEBC3A40D6A5D3A93F4DCBB1275F89F3651791EB7D0E780294E6601A8CFC6A1086F472089EED9BE1770583F96F184E34A2D0562CBAC9BFC55321A7DD4B3BADD74133B5CF592A5C26B0C2443EA8DED8A23446C0BA2C5F2953C5B7314BDDAD3B41D7A52359CFBCCAB02654D2A83E491F65F381077DEB98EE940270F68C1A6AFC861062E49E087B0D77E193156FF981572DBBC94F35A3D0A6DC4A38BEC45222B4CE582AACD64033453FA9DB5D27B1C690EA7C0E88F26417611B8DFF790395E573099FED6B1187F482F86E1C9AE0760'
    ,   '0068D0B8BDD56D05670FB7DFDAB20A62CEA61E76731BA3CBA9C17911147CC4AC81E951393C54EC84E68E365E5B338BE34F279FF7F29A224A2840F89095FD452D1F77CFA7A2CA721A7810A8C0C5AD157DD1B901696C04BCD4B6DE660E0B63DBB39EF64E26234BF39BF9912941442C94FC503880E8ED853D55375FE78F8AE25A323E56EE8683EB533B593189E1E48C345CF09820484D259DF597FF472F2A42FA92BFD76F07026AD2BAD8B00860650DB5DD7119A1C9CCA41C74167EC6AEABC37B132149F1999CF44C24462E96FEFB932B43EF873F57523A82EA88E05830355DE58DA0C870181D75CDA5C7AF177F7A12AAC26E06BED6D3BB036B0961D9B1B4DC640C'
    ,   '0069D2BBB9D06B026F06BDD4D6BF046DDEB70C65670EB5DCB1D8630A0861DAB3A1C8731A1871CAA3CEA71C75771EA5CC7F16ADC4C6AF147D1079C2ABA9C07B125F368DE4E68F345D3059E28B89E05B3281E8533A3851EA83EE873C55573E85ECFE972C45472E95FC91F8432A2841FA932049F29B99F04B224F269DF4F69F244DBED76C05076ED5BCD1B8036A6801BAD36009B2DBD9B00B620F66DDB4B6DF640D1F76CDA4A6CF741D7019A2CBC9A01B72C1A8137A7811AAC3AEC77C15177EC5ACE188335A58318AE38EE75C35375EE58C3F56ED8486EF543D503982EBE9803B52402992FBF9902B422F46FD9496FF442D9EF74C25274EF59CF198234A48219AF3'
    ,   '006AD4BEB5DF610B771DA3C9C2A8167CEE843A505B318FE599F34D272C46F892C1AB157F741EA0CAB6DC62080369D7BD2F45FB919AF04E2458328CE6ED8739539FF54B212A40FE94E8823C565D3789E3711BA5CFC4AE107A066CD2B8B3D9670D5E348AE0EB813F552943FD979CF64822B0DA640E056FD1BBC7AD13797218A6CC2349F79D96FC4228543E80EAE18B355FCDA719737812ACC6BAD06E040F65DBB1E288365C573D83E995FF412B204AF49E0C66D8B2B9D36D077B11AFC5CEA41A70BCD668020963DDB7CBA11F757E14AAC0523886ECE78D3359254FF19B90FA442E7D17A9C3C8A21C760A60DEB4BFD56B0193F9472D264CF298E48E305A513B85EF'
    ,   '006BD6BDB1DA670C7F14A9C2CEA51873FE9528434F2499F281EA573C305BE68DE18A375C503B86ED9EF548232F44F9921F74C9A2AEC57813600BB6DDD1BA076CDFB409626E05B8D3A0CB761D117AC7AC214AF79C90FB462D5E3588E3EF8439523E55E8838FE45932412A97FCF09B264DC0AB167D711AA7CCBFD469020E65D8B3A3C8751E1279C4AFDCB70A616D06BBD05D368BE0EC873A512249F49F93F8452E422994FFF398254E3D56EB808CE75A31BCD76A010D66DBB0C3A8157E7219A4CF7C17AAC1CDA61B700368D5BEB2D9640F82E9543F3358E58EFD962B404C279AF19DF64B202C47FA91E289345F533885EE6308B5DED2B9046F1C77CAA1ADC67B10'
    ,   '006CD8B4ADC17519472B9FF3EA86325E8EE2563A234FFB97C9A5117D6408BCD0016DD9B5ACC07418462A9EF2EB87335F8FE3573B224EFA96C8A4107C6509BDD1026EDAB6AFC3771B45299DF1E884305C8CE05438214DF995CBA7137F660ABED2036FDBB7AEC2761A44289CF0E985315D8DE15539204CF894CAA6127E670BBFD30468DCB0A9C5711D432F9BF7EE82365A8AE6523E274BFF93CDA11579600CB8D40569DDB1A8C4701C422E9AF6EF83375B8BE7533F264AFE92CCA01478610DB9D5066ADEB2ABC7731F412D99F5EC80345888E4503C2549FD91CFA3177B620EBAD6076BDFB3AAC6721E402C98F4ED81355989E5513D2448FC90CEA2167A630FBBD7'
    ,   '006DDAB7A9C4731E4F2295F8E68B3C519EF34429375AED80D1BC0B667815A2CF214CFB9688E5523F6E03B4D9C7AA1D70BFD26508167BCCA1F09D2A47593483EE422F98F5EB86315C0D60D7BAA4C97E13DCB1066B7518AFC293FE49243A57E08D630EB9D4CAA7107D2C41F69B85E85F32FD90274A54398EE3B2DF68051B76C1AC84E95E332D40F79ACBA6117C620FB8D51A77C0ADB3DE690455388FE2FC91264BA5C87F120C61D6BBEA87305D432E99F43B56E18C92FF48257419AEC3DDB0076AC6AB1C716F02B5D889E4533E204DFA97583582EFF19C2B46177ACDA0BED36409E78A3D504E2394F9A8C5721F016CDBB67914A3CED0BD0A67365BEC819FF24528'
    ,   '006EDCB2A5CB791757398BE5F29C2E40AEC0721C0B65D7B9F997254B5C3280EE412F9DF3E48A38561678CAA4B3DD6F01EF81335D4A2496F8B8D6640A1D73C1AF82EC5E302749FB95D5BB0967701EACC22C42F09E89E7553B7B15A7C9DEB0026CC3AD1F716608BAD494FA4826315FED836D03B1DFC8A6147A3A54E6889FF1432D1977C5ABBCD2600E4E2092FCEB853759B7D96B05127CCEA0E08E3C52452B99F7583684EAFD93214F0F61D3BDAAC47618F6982A44533D8FE1A1CF7D13046AD8B69BF547293E50E28CCCA2107E6907B5DB355BE98790FE4C22620CBED0C7A91B75DAB406687F11A3CD8DE3513F2846F49A741AA8C6D1BF0D63234DFF9186E85A34'
    ,   '006FDEB1A1CE7F105F3081EEFE91204FBED1600F1F70C1AEE18E3F50402F9EF1610EBFD0C0AF1E713E51E08F9FF0412EDFB0016E7E11A0CF80EF5E31214EFF90C2AD1C73630CBDD29DF2432C3C53E28D7C13A2CDDDB2036C234CFD9282ED5C33A3CC7D12026DDCB3FC93224D5D3283EC1D72C3ACBCD3620D422D9CF3E38C3D5299F647283857E689C6A918776708B9D62748F99686E958377817A6C9D9B60768F8972649593687E8A7C879160669D8B7462998F7E78839561976C7A8B8D766095B3485EAFA95244B046BDAB5A5CA7B14E58A3B54442B9AF5BAD5640B1B74C5AA3A55E48B9BF4452A650ABBD4C4AB1A7584EB5A35254AFB94DBB4056A7A15A4CB'
    ,   '0070E090DDAD3D4DA7D747377A0A9AEA5323B3C38EFE6E1EF48414642959C9B9A6D646367B0B9BEB0171E191DCAC3C4CF58515652858C8B85222B2C28FFF6F1F5121B1C18CFC6C1CF68616662B5BCBBB0272E292DFAF3F4FA5D54535780898E8F78717672A5ACABA5020B0C08DFD6D1DA4D44434790999E90373E393DEAE3E4EA2D242327F0F9FEF0575E595D8A83848F18111612C5CCCBC5626B6C68BFB6B1B0474E494D9A93949A3D343337E0E9EEE5727B7C78AFA6A1AF08010602D5DCDBDF38313632E5ECEBE5424B4C489F96919A0D040307D0D9DED0777E797DAAA3A4A5525B5C588F86818F28212622F5FCFBF0676E696DBAB3B4BA1D141317C0C9CEC'
    ,   '0071E293D9A83B4AAFDE4D3C760794E54332A1D09AEB7809EC9D0E7F3544D7A686F764155F2EBDCC2958CBBAF0811263C5B427561C6DFE8F6A1B88F9B3C251201160F382C8B92A5BBECF5C2D671685F45223B0C18BFA6918FD8C1F6E2455C6B797E675044E3FACDD3849DAABE1900372D4A536470D7CEF9E7B0A99E8A2D340312253C0B1FB8A19688DFC6F1E5425B6C7611083F2B8C95A2BCEBF2C5D1766F584A4D546377D0C9FEE0B7AE998D2A33041E79605743E4FDCAD4839AADB91E073023342D1A0EA9B08799CED7E0F4534A7D6700192E3A9D84B3ADFAE3D4C0677E495B5C457266C1D8EFF1A6BF889C3B22150F68714652F5ECDBC5928BBCA80F16213'
    ,   '0072E496D5A73143B7C55321621086F4730197E5A6D44230C4B620521163F587E69402703341D7A55123B5C784F6601295E771034032A4D62250C6B4F7851361D1A335470476E092661482F0B3C15725A2D04634770593E11567F183C0B224563745D3A1E290067480F264165527B1C34436A0D291E37507F38117652654C2B0BFCD5B296A188EFC087AEC9EDDAF394BCCBE285A196BFD8F7B099FEDAEDC4A38592BBDCF8CFE681AEE9C0A783B49DFAD2A58CEBCFF8D1B699DEF790B483AACDE6E1C8AF8BBC95F2DD9AB3D4F0C7EE89A1D6FF98BC8BA2C5EAAD84E3C7F0D9BE988FA6C1E5D2FB9CB3F4DDBA9EA980E7CFB891F6D2E5CCAB84C3EA8DA99EB7D0F'
    ,   '0073E695D1A23744BFCC592A6E1D88FB631085F6B2C15427DCAF3A490D7EEB98C6B520531764F182790A9FECA8DB4E3DA5D64330740792E11A69FC8FCBB82D5E91E277044033A6D52E5DC8BBFF8C196AF28114672350C5B64D3EABD89CEF7A095724B1C286F56013E89B0E7D394ADFAC3447D2A1E59603708BF86D1E5A29BCCF3F4CD9AAEE9D087B80F366155122B7C45C2FBAC98DFE6B18E39005763241D4A7F98A1F6C285BCEBD4635A0D397E471029AE97C0F4B38ADDE2556C3B0F4871261AEDD483B7F0C99EA1162F784C0B32655CDBE2B581C6FFA89720194E7A3D04536681B8EFDB9CA5F2CD7A431420675E0930B78ED9EDAA93C4FB4C75221651683F0'
    ,   '0074E89CCDB9255187F36F1B4A3EA2D61367FB8FDEAA364294E07C08592DB1C52652CEBAEB9F0377A1D5493D6C1884F03541DDA9F88C1064B2C65A2E7F0B97E34C38A4D081F5691DCBBF23570672EE9A5F2BB7C392E67A0ED8AC30441561FD896A1E82F6A7D34F3BED9905712054C8BC790D91E5B4C05C28FE8A16623347DBAF98EC70045521BDC91F6BF783D2A63A4E8BFF63174632AEDA0C78E490C1B5295DBECA562273079BEF394DD1A5F4801C68ADD94531601488FC2A5EC2B6E7930F7BD4A03C48196DF1855327BBCF9EEA7602C7B32F5B0A7EE2964034A8DC8DF96511F2861A6E3F4BD7A375019DE9B8CC5024E195097D2C58C4B066128EFAABDF4337'
    ,   '0075EA9FC9BC23568FFA65104633ACD90376E99CCABF20558CF966134530AFDA0673EC99CFBA255089FC63164035AADF0570EF9ACCB926538AFF60154336A9DC0C79E693C5B02F5A83F6691C4A3FA0D50F7AE590C6B32C5980F56A1F493CA3D60A7FE095C3B6295C85F06F1A4C39A6D3097CE396C0B52A5F86F36C194F3AA5D0186DF287D1A43B4E97E27D085E2BB4C11B6EF184D2A7384D94E17E0B5D28B7C21E6BF481D7A23D4891E47B0E582DB2C71D68F782D4A13E4B92E7780D5B2EB1C41461FE8BDDA837429BEE71045227B8CD1762FD88DEAB344198ED72075124BBCE1267F88DDBAE31449DE877025421BECB1164FB8ED8AD32479EEB74015722BDC8'
    ,   '0076EC9AC5B3295F97E17B0D5224BEC83345DFA9F6801A6CA4D2483E61178DFB66108AFCA3D54F39F1871D6B3442D8AE5523B9CF90E67C0AC2B42E580771EB9DCCBA2056097FE5935B2DB7C19EE87204FF8913653A4CD6A0681E84F2ADDB4137AADC46306F1983F53D4BD1A7F88E146299EF75035C2AB0C60E78E294CBBD275185F3691F4036ACDA1264FE88D7A13B4DB6C05A2C73059FE92157CDBBE492087EE3950F792650CABC740298EEB1C75D2BD0A63C4A1563F98F4731ABDD82F46E18493FA5D38CFA6016DEA832441B6DF7817A0C96E0BFC95325ED9B0177285EC4B22F59C3B5EA9C0670B8CE54227D0B91E71C6AF086D9AF35438BFD67114E38A2D4'
    ,   '0077EE99C1B62F589FE871065E29B0C72354CDBAE2950C7BBCCB52257D0A93E44631A8DF87F0691ED9AE3740186FF68165128BFCA4D34A3DFA8D14633B4CD5A28CFB62154D3AA3D41364FD8AD2A53C4BAFD841366E1980F73047DEA9F1861F68CABD24530B7CE5925522BBCC94E37A0DE99E0770285FC6B1760198EFB7C0592E0572EB9CC4B32A5D9AED74035B2CB5C22651C8BFE790097EB9CE5720780F96E14334ADDA82F56C1BDCAB32451D6AF38460178EF9A1D64F38FF8811663E49D0A789FE6710483FA6D11661F88FD7A0394EAADD44336B1C85F23542DBACF4831A6DCFB821560E79E0975027BEC991E67F08EC9B02752D5AC3B473049DEAB2C55C2B'
    ,   '0078F088FD850D75E79F176F1A62EA92D3AB235B2E56DEA6344CC4BCC9B13941BBC34B33463EB6CE5C24ACD4A1D95129681098E095ED651D8FF77F07720A82FA6B139BE396EE661E8CF47C04710981F9B8C04830453DB5CD5F27AFD7A2DA522AD0A820582D55DDA5374FC7BFCAB23A42037BF38BFE860E76E49C146C1961E991D6AE265E2B53DBA33149C1B9CCB43C44057DF58DF8800870E29A126A1F67EF976D159DE590E860188AF27A02770F87FFBEC64E36433BB3CB5921A9D1A4DC542CBDC54D354038B0C85A22AAD2A7DF572F6E169EE693EB631B89F17901740C84FC067EF68EFB830B73E19911691C64EC94D5AD255D2850D8A0324AC2BACFB73F47'
    ,   '0079F28BF9800B72EF961D64166FE49DC3BA31483A43C8B12C55DEA7D5AC275E9BE26910621B90E9740D86FF8DF47F065821AAD3A1D8532AB7CE453C4E37BCC52B52D9A0D2AB2059C4BD364F3D44CFB6E8911A631168E39A077EF58CFE870C75B0C9423B4930BBC25F26ADD4A6DF542D730A81F88AF378019CE56E17651C97EE562FA4DDAFD65D24B9C04B324039B2CB95EC671E6C159EE77A0388F183FA7108CDB43F46344DC6BF225BD0A9DBA229500E77FC85F78E057CE198136A1861EA937D048FF684FD760F92EB60196B1299E0BEC74C35473EB5CC5128A3DAA8D15A23E69F146D1F66ED940970FB82F089027B255CD7AEDCA52E57CAB33841334AC1B8'
    ,   '007AF48EF58F017BF78D03790278F68CF389077D067CF288047EF08AF18B057FFB810F750E74FA800C76F882F9830D770872FC86FD870973FF850B710A70FE84EB911F651E64EA901C66E892E9931D671862EC96ED971963EF951B611A60EE94106AE49EE59F116BE79D13691268E69CE399176D166CE298146EE09AE19B156FCBB13F453E44CAB03C46C8B2C9B33D473842CCB6CDB73943CFB53B413A40CEB4304AC4BEC5BF314BC7BD33493248C6BCC3B9374D364CC2B8344EC0BAC1BB354F205AD4AED5AF215BD7AD23592258D6ACD3A9275D265CD2A8245ED0AAD1AB255FDBA12F552E54DAA02C56D8A2D9A32D572852DCA6DDA72953DFA52B512A50DEA4'
    ,   '007BF68DF18A077CFF8409720E75F883E398156E1269E49F1C67EA91ED961B60DBA02D562A51DCA7245FD2A9D5AE23583843CEB5C9B23F44C7BC314A364DC0BBABD05D265A21ACD7542FA2D9A5DE53284833BEC5B9C24F34B7CC413A463DB0CB700B86FD81FA770C8FF479027E0588F393E8651E621994EF6C179AE19DE66B104B30BDC6BAC14C37B4CF4239453EB3C8A8D35E255922AFD4572CA1DAA6DD502B90EB661D611A97EC6F1499E29EE56813730885FE82F9740F8CF77A017D068BF0E09B166D116AE79C1F64E992EE9518630378F58EF289047FFC870A710D76FB803B40CDB6CAB13C47C4BF3249354EC3B8D8A32E552952DFA4275CD1AAD6AD205B'
    ,   '007CF884ED911569C7BB3F432A56D2AE93EF6B177E0286FA5428ACD0B9C5413D3B47C3BFD6AA2E52FC800478116DE995A8D4502C4539BDC16F1397EB82FE7A06760A8EF29BE7631FB1CD49355C20A4D8E5991D610874F08C225EDAA6CFB3374B4D31B5C9A0DC58248AF6720E671B9FE3DEA2265A334FCBB71965E19DF4880C70EC901468017DF9852B57D3AFC6BA3E427F0387FB92EE6A16B8C4403C5529ADD1D7AB2F533A46C2BE106CE894FD8105794438BCC0A9D5512D83FF7B076E1296EA9AE6621E770B8FF35D21A5D9B0CC48340975F18DE4981C60CEB2364A235FDBA7A1DD59254C30B4C8661A9EE28BF7730F324ECAB6DFA3275BF5890D711864E09C'
    ,   '007DFA87E994136ECFB23548265BDCA183FE79046A1790ED4C31B6CBA5D85F221B66E19CF28F0875D4A92E533D40C7BA98E5621F710C8BF6572AADD0BEC34439364BCCB1DFA22558F984037E106DEA97B5C84F325C21A6DB7A0780FD93EE69142D50D7AAC4B93E43E29F18650B76F18CAED35429473ABDC0611C9BE688F5720F6C1196EB85F87F02A3DE59244A37B0CDEF921568067BFC81205DDAA7C9B4334E770A8DF09EE36419B8C5423F512CABD6F4890E731D60E79A3B46C1BCD2AF28555A27A0DDB3CE493495E86F127C0186FBD9A4235E304DCAB7166BEC91FF820578413CBBC6A8D5522F8EF37409671A9DE0C2BF38452B56D1AC0D70F78AE4991E63'
    ,   '007EFC82E59B1967D7A92B55324CCEB0B3CD4F315628AAD4641A98E681FF7D037B0587F99EE0621CACD2502E4937B5CBC8B6344A2D53D1AF1F61E39DFA840678F6880A74136DEF91215FDDA3C4BA3846453BB9C7A0DE5C2292EC6E1077098BF58DF3710F681694EA5A24A6D8BFC1433D3E40C2BCDBA52759E997156B0C72F08EF18F0D73146AE8962658DAA4C3BD3F41423CBEC0A7D95B2595EB6917700E8CF28AF476086F1193ED5D23A1DFB8C6443A3947C5BBDCA2205EEE90126C0B75F7890779FB85E29C1E60D0AE2C52354BC9B7B4CA4836512FADD3631D9FE186F87A047C0280FE99E7651BABD557294E30B2CCCFB1334D2A54D6A81866E49AFD83017F'
    ,   '007FFE81E19E1F60DFA0215E3E41C0BFA3DC5D22423DBCC37C0382FD9DE2631C5B24A5DABAC5443B84FB7A05651A9BE4F88706791966E7982758D9A6C6B93847B6C948375728A9D6691697E888F77609156AEB94F48B0A75CAB5344B2B54D5AAED92136C0C73F28D324DCCB3D3AC2D524E31B0CFAFD0512E91EE6F10700F8EF1710E8FF090EF6E11AED1502F4F30B1CED2AD2C53334CCDB20D72F38CEC93126D2A55D4ABCBB4354AF58A0B74146BEA9589F67708681796E95629A8D7B7C84936C7B839462659D8A71867E699F9860778641B9AE585FA7B04BBC4453A5A25A4DB9CE3621D7D0283FC433CBDC2A2DD5C233F40C1BEDEA1205FE09F1E61017EFF80'
    ,   '00801D9D3ABA27A774F469E94ECE53D3E868F575D252CF4F9C1C8101A626BB3BCD4DD050F777EA6AB939A42483039E1E25A538B81F9F028251D14CCC6BEB76F687079A1ABD3DA020F373EE6EC949D4546FEF72F255D548C81B9B068621A13CBC4ACA57D770F06DED3EBE23A304841999A222BF3F98188505D656CB4BEC6CF17113930E8E29A934B467E77AFA5DDD40C0FB7BE666C141DC5C8F0F9212B535A828DE5EC343E464F979AA2AB73790108D0D36B62BAB0C8C119142C25FDF78F865E594148909AE2EB333E060FD7DDA5AC7477CFC61E146C65BDB0888159532B22FAF59D944C463E37EFE2DAD30B017970A8AB131AC2C8B0B9616C545D858FF7FE262'
    ,   '00811F9E3EBF21A07CFD63E242C35DDCF879E766C647D95884059B1ABA3BA524ED6CF273D352CC4D91108E0FAF2EB03115940A8B2BAA34B569E876F757D648C9C746D859F978E667BB3AA42585049A1B3FBE20A101801E9F43C25CDD7DFC62E32AAB35B414950B8A56D749C868E977F6D253CD4CEC6DF372AE2FB13090118F0E93128C0DAD2CB233EF6EF071D150CE4F6BEA74F555D44ACB1796088929A836B77EFF61E040C15FDE02831D9C3CBD23A286079918B839A726FA7BE564C445DB5A54D54BCA6AEB75F428A937B616970988AC2DB33292138D0CD051CF4EEE6FF170B938A62787069819C544DA5BFB7AE46541C05EDF7FFE60E13DBC22A303821C9D'
    ,   '0082199B32B02BA964E67DFF56D44FCDC84AD153FA78E361AC2EB5379E1C87058D0F9416BF3DA624E96BF072DB59C24045C75CDE77F56EEC21A338BA13910A8807851E9C35B72CAE63E17AF851D348CACF4DD654FD7FE466AB29B230991B80028A089311B83AA123EE6CF775DC5EC54742C05BD970F269EB26A43FBD14960D8F0E8C17953CBE25A76AE873F158DA41C3C644DF5DF476ED6FA220BB399012890B83019A18B133A82AE765FE7CD557CC4E4BC952D079FB60E22FAD36B41D9F0486098B10923BB922A06DEF74F65FDD46C4C143D85AF371EA68A527BC3E97158E0C84069D1FB634AF2DE062F97BD250CB494CCE55D77EFC67E528AA31B31A980381'
    ,   '00831B9836B52DAE6CEF77F45AD941C2D85BC340EE6DF576B437AF2C8201991AAD2EB6359B188003C142DA59F774EC6F75F66EED43C058DB199A02812FAC34B747C45CDF71F26AE92BA830B31D9E06859F1C8407A92AB231F370E86BC546DE5DEA69F172DC5FC74486059D1EB033AB2832B129AA04871F9C5EDD45C668EB73F08E0D9516B83BA320E261F97AD457CF4C56D54DCE60E37BF83AB921A20C8F179423A038BB15960E8D4FCC54D779FA62E1FB78E063CD4ED65597148C0FA122BA39C94AD251FF7CE467A526BE3D9310880B11920A8927A43CBF7DFE66E54BC850D364E77FFC52D149CA088B13903EBD25A6BC3FA7248A099112D053CB48E665FD7E'
    ,   '008415912AAE3FBB54D041C57EFA6BEFA82CBD3982069713FC78E96DD652C3474DC958DC67E372F6199D0C8833B726A2E561F074CF4BDA5EB135A4209B1F8E0A9A1E8F0BB034A521CE4ADB5FE460F17532B627A3189C0D8966E273F74CC859DDD753C246FD79E86C83079612A92DBC387FFB6AEE55D140C42BAF3EBA0185149029AD3CB8038716927DF968EC57D342C681059410AB2FBE3AD551C044FF7BEA6E64E071F54ECA5BDF30B425A11A9E0F8BCC48D95DE662F377981C8D09B236A723B337A622991D8C08E763F276CD49D85C1B9F0E8A31B524A04FCB5ADE65E170F4FE7AEB6FD450C145AA2EBF3B8004951156D243C77CF869ED0286179328AC3DB9'
    ,   '008517922EAB39BC5CD94BCE72F765E0B83DAF2A96138104E461F376CA4FDD586DE87AFF43C654D131B426A31F9A088DD550C247FB7EEC69890C9E1BA722B035DA5FCD48F471E36686039114A82DBF3A62E775F04CC95BDE3EBB29AC10950782B732A025991C8E0BEB6EFC79C540D2570F8A189D21A436B353D644C17DF86AEFA92CBE3B87029015F570E267DB5ECC49119406833FBA28AD4DC85ADF63E674F1C441D356EA6FFD78981D8F0AB633A1247CF96BEE52D745C020A537B20E8B199C73F664E15DD84ACF2FAA38BD01841693CB4EDC59E560F27797128005B93CAE2B1E9B098C30B527A242C755D06CE97BFEA623B134880D9F1AFA7FED68D451C346'
    ,   '0086119722A433B544C255D366E077F1880E991FAA2CBB3DCC4ADD5BEE68FF790D8B1C9A2FA93EB849CF58DE6BED7AFC85039412A721B630C147D056E365F2741A9C0B8D38BE29AF5ED84FC97CFA6DEB92148305B036A127D650C741F472E5631791068035B324A253D542C471F760E69F198E08BD3BAC2ADB5DCA4CF97FE86E34B225A31690078170F661E752D443C5BC3AAD2B9E188F09F87EE96FDA5CCB4D39BF28AE1B9D0A8C7DFB6CEA5FD94EC8B137A02693158204F573E462D751C6402EA83FB90C8A1D9B6AEC7BFD48CE59DFA620B73184029513E264F375C046D15723A532B40187109667E176F045C354D2AB2DBA3C890F981EEF69FE78CD4BDC5A'
    ,   '0087139426A135B24CCB5FD86AED79FE981F8B0CBE39AD2AD453C740F275E1662DAA3EB90B8C189F61E672F547C054D3B532A62193148007F97EEA6DDF58CC4B5ADD49CE7CFB6FE81691058230B723A4C245D156E463F7708E099D1AA82FBB3C77F064E351D642C53BBC28AF1D9A0E89EF68FC7BC94EDA5DA324B03785029611B433A72092158106F87FEB6CDE59CD4A2CAB3FB80A8D199E60E773F446C155D2991E8A0DBF38AC2BD552C641F374E0670186129527A034B34DCA5ED96BEC78FFEE69FD7AC84FDB5CA225B1368403971076F165E250D743C43ABD29AE1C9B0F88C344D057E562F6718F089C1BA92EBA3D5BDC48CF7DFA6EE91790048331B622A5'
    ,   '00880D851A92179F34BC39B12EA623AB68E065ED72FA7FF75CD451D946CE4BC3D058DD55CA42C74FE46CE961FE76F37BB830B53DA22AAF278C048109961E9B13BD35B038A72FAA228901840C931B9E16D55DD850CF47C24AE169EC64FB73F67E6DE560E877FF7AF259D154DC43CB4EC6058D08801F97129A31B93CB42BA326AE67EF6AE27DF570F853DB5ED649C144CC0F87028A159D18903BB336BE21A92CA4B73FBA32AD25A028830B8E069911941CDF57D25AC54DC840EB63E66EF179FC74DA52D75FC048CD45EE66E36BF47CF971B23ABF37A820A52D860E8B039C1491190A82078F10981D953EB633BB24AC29A162EA6FE778F075FD56DE5BD34CC441C9'
    ,   '00890F861E9711983CB533BA22AB2DA478F177FE66EF69E044CD4BC25AD355DCF079FF76EE67E168CC45C34AD25BDD548801870E961F9910B43DBB32AA23A52CFD74F27BE36AEC65C148CE47DF56D059850C8A039B12941DB930B63FA72EA8210D84028B139A1C9531B83EB72FA620A975FC7AF36BE264ED49C046CF57DE58D1E76EE861F970F67FDB52D45DC54CCA439F16901981088E07A32AAC25BD34B23B179E18910980068F2BA224AD35BC3AB36FE660E971F87EF753DA5CD54DC442CB1A93159C048D0B8226AF29A038B137BE62EB6DE47CF573FA5ED751D840C94FC6EA63E56CF47DFB72D65FD950C841C74E921B9D148C05830AAE27A128B039BF36'
    ,   '008A098312981B9124AE2DA736BC3FB548C241CB5AD053D96CE665EF7EF477FD901A991382088B01B43EBD37A62CAF25D852D15BCA40C349FC76F57FEE64E76D3DB734BE2FA526AC1993109A0B81028875FF7CF667ED6EE451DB58D243C94AC0AD27A42EBF35B63C8903800A9B119218E56FEC66F77DFE74C14BC842D359DA507AF073F968E261EB5ED457DD4CC645CF32B83BB120AA29A3169C1F95048E0D87EA60E369F872F17BCE44C74DDC56D55FA228AB21B03AB933860C8F05941E9D1747CD4EC455DF5CD663E96AE071FB78F20F85068C1D97149E2BA122A839B330BAD75DDE54C54FCC46F379FA70E16BE8629F15961C8D07840EBB31B238A923A02A'
    ,   '008B0B80169D1D962CA727AC3AB131BA58D353D84EC545CE74FF7FF462E969E2B03BBB30A62DAD269C17971C8A01810AE863E368FE75F57EC44FCF44D259D9527DF676FD6BE060EB51DA5AD147CC4CC725AE2EA533B838B3098202891F94149FCD46C64DDB50D05BE16AEA61F77CFC77951E9E1583088803B932B239AF24A42FFA71F17AEC67E76CD65DDD56C04BCB40A229A922B43FBF348E05850E981393184AC141CA5CD757DC66ED6DE670FB7BF012991992048F0F843EB535BE28A323A8870C8C07911A9A11AB20A02BBD36B63DDF54D45FC942C249F378F873E56EEE6537BC3CB721AA2AA11B90109B0D86068D6FE464EF79F272F943C848C355DE5ED5'
    ,   '008C05890A860F831498119D1E921B9728A42DA122AE27AB3CB039B536BA33BF50DC55D95AD65FD344C841CD4EC24BC778F47DF172FE77FB6CE069E566EA63EFA02CA529AA26AF23B438B13DBE32BB3788048D01820E870B9C109915961A931FF07CF579FA76FF73E468E16DEE62EB67D854DD51D25ED75BCC40C945C64AC34F5DD158D457DB52DE49C54CC043CF46CA75F970FC7FF37AF661ED64E86BE76EE20D810884078B028E19951C90139F169A25A920AC2FA32AA631BD34B83BB73EB2FD71F874F77BF27EE965EC60E36FE66AD559D05CDF53DA56C14DC448CB47CE42AD21A824A72BA22EB935BC30B33FB63A8509800C8F038A06911D94189B179E12'
    ,   '008D078A0E8309841C911B96129F159838B53FB236BB31BC24A923AE2AA72DA070FD77FA7EF379F46CE16BE662EF65E848C54FC246CB41CC54D953DE5AD75DD0E06DE76AEE63E964FC71FB76F27FF578D855DF52D65BD15CC449C34ECA47CD40901D971A9E1399148C018B06820F8508A825AF22A62BA12CB439B33EBA37BD30DD50DA57D35ED459C14CC64BCF42C845E568E26FEB66EC61F974FE73F77AF07DAD20AA27A32EA429B13CB63BBF32B8359518921F9B169C1189048E03870A800D3DB03AB733BE34B921AC26AB2FA228A50588028F0B860C8119941E93179A109D4DC04AC743CE44C951DC56DB5FD258D575F872FF7BF67CF169E46EE367EA60ED'
    ,   '008E018F028C038D048A058B06880789088609870A840B850C820D830E800F81109E119F129C139D149A159B16981799189619971A941B951C921D931E901F9120AE21AF22AC23AD24AA25AB26A827A928A629A72AA42BA52CA22DA32EA02FA130BE31BF32BC33BD34BA35BB36B837B938B639B73AB43BB53CB23DB33EB03FB140CE41CF42CC43CD44CA45CB46C847C948C649C74AC44BC54CC24DC34EC04FC150DE51DF52DC53DD54DA55DB56D857D958D659D75AD45BD55CD25DD35ED05FD160EE61EF62EC63ED64EA65EB66E867E968E669E76AE46BE56CE26DE36EE06FE170FE71FF72FC73FD74FA75FB76F877F978F679F77AF47BF57CF27DF37EF07FF1'
    ,   '008F038C0689058A0C830F800A85098618971B941E911D92149B1798129D119E30BF33BC36B935BA3CB33FB03AB539B628A72BA42EA12DA224AB27A822AD21AE60EF63EC66E965EA6CE36FE06AE569E678F77BF47EF17DF274FB77F872FD71FE50DF53DC56D955DA5CD35FD05AD559D648C74BC44EC14DC244CB47C842CD41CEC04FC34CC649C54ACC43CF40CA45C946D857DB54DE51DD52D45BD758D25DD15EF07FF37CF679F57AFC73FF70FA75F976E867EB64EE61ED62E46BE768E26DE16EA02FA32CA629A52AAC23AF20AA25A926B837BB34BE31BD32B43BB738B23DB13E901F931C9619951A9C139F109A15991688078B048E018D02840B8708820D810E'
    ,   '00903DAD7AEA47D7F464C9598E1EB323F565C8588F1FB22201913CAC7BEB46D6F767CA5A8D1DB02003933EAE79E944D402923FAF78E845D5F666CB5B8C1CB121F363CE5E8919B42407973AAA7DED40D006963BAB7CEC41D1F262CF5F8818B525049439A97EEE43D3F060CD5D8A1AB727F161CC5C8B1BB626059538A87FEF42D2FB6BC6568111BC2C0F9F32A275E548D80E9E33A374E449D9FA6AC7578010BD2D0C9C31A176E64BDBF868C5558212BF2FF969C4548313BE2E0D9D30A077E74ADA089835A572E24FDFFC6CC1518616BB2BFD6DC0508717BA2A099934A473E34EDEFF6FC2528515B8280B9B36A671E14CDC0A9A37A770E04DDDFE6EC3538414B929'
    ,   '00913FAE7EEF41D0FC6DC3528213BD2CE574DA4B9B0AA435198826B767F658C9D746E879A93896072BBA148555C46AFB32A30D9C4CDD73E2CE5FF160B0218F1EB3228C1DCD5CF2634FDE70E131A00E9F56C769F828B91786AA3B9504D445EB7A64F55BCA1A8B25B49809A736E677D9488110BE2FFF6EC0517DEC42D303923CAD7BEA44D505943AAB8716B829F968C6579E0FA130E071DF4E62F35DCC1C8D23B2AC3D9302D243ED7C50C16FFE2EBF118049D876E737A60899B5248A1BCB5AF465C859F766B627891834A50B9A4ADB75E42DBC128353C26CFDD140EE7FAF3E90011F8E20B161F05ECFE372DC4D9D0CA233FA6BC5548415BB2A069739A878E947D6'
    ,   '009239AB72E04BD9E476DD4F9604AF3DD547EC7EA7359E0C31A3089A43D17AE8B7258E1CC557FC6E53C16AF821B3188A62F05BC9108229BB8614BF2DF466CD5F73E14AD8019338AA9705AE3CE577DC4EA6349F0DD446ED7F42D07BE930A2099BC456FD6FB6248F1D20B2198B52C06BF9118328BA63F15AC8F567CC5E8715BE2CE674DF4D9406AD3F02903BA970E249DB33A10A9841D378EAD745EE7CA5379C0E51C368FA23B11A88B5278C1EC755FE6C8416BD2FF664CF5D60F259CB12802BB99507AC3EE775DE4C71E348DA03913AA840D279EB32A00B99A4369D0FD644EF7D22B01B8950C269FBC654FF6DB4268D1FF765CE5C8517BC2E13812AB861F358CA'
    ,   '00933BA876E54DDEEC7FD7449A09A132C556FE6DB320881B29BA12815FCC64F79704AC3FE172DA497BE840D30D9E36A552C169FA24B71F8CBE2D8516C85BF36033A0089B45D67EEDDF4CE477A93A9201F665CD5E8013BB281A8921B26CFF57C4A4379F0CD241E97A48DB73E03EAD059661F25AC917842CBF8D1EB625FB68C05366F55DCE10832BB88A19B122FC6FC754A330980BD546EE7D4FDC74E739AA0291F162CA598714BC2F1D8E26B56BF850C334A70F9C42D179EAD84BE370AE3D950655C66EFD23B0188BB92A8211CF5CF4679003AB38E675DD4E7CEF47D40A9931A2C251F96AB4278F1C2EBD158658CB63F007943CAF71E24AD9EB78D0439D0EA635'
    ,   '009435A16AFE5FCBD440E175BE2A8B1FB5218014DF4BEA7E61F554C00B9F3EAA77E342D61D8928BCA3379602C95DFC68C256F763A83C9D09168223B77CE849DDEE7ADB4F8410B1253AAE0F9B50C465F15BCF6EFA31A504908F1BBA2EE571D044990DAC38F367C6524DD978EC27B312862CB8198D46D273E7F86CCD599206A733C155F460AB3F9E0A158120B47FEB4ADE74E041D51E8A2BBFA0349501CA5EFF6BB6228317DC48E97D62F657C3089C3DA9039736A269FD5CC8D743E276BD29881C2FBB1A8E45D170E4FB6FCE5A9105A4309A0EAF3BF064C5514EDA7BEF24B0118558CC6DF932A607938C18B92DE672D347ED79D84C8713B22639AD0C9853C766F2'
    ,   '009537A26EFB59CCDC49EB7EB2278510A5309207CB5EFC6979EC4EDB178220B557C260F539AC0E9B8B1EBC29E570D247F267C5509C09AB3E2EBB198C40D577E2AE3B990CC055F76272E745D01C892BBE0B9E3CA965F052C7D742E075B92C8E1BF96CCE5B9702A03525B012874BDE7CE95CC96BFE32A705908015B722EE7BD94C41D476E32FBA188D9D08AA3FF366C451E471D3468A1FBD2838AD0F9A56C361F4168321B478ED4FDACA5FFD68A4319306B3268411DD48EA7F6FFA58CD019436A3EF7AD84D8114B62333A604915DC86AFF4ADF7DE824B113869603A134F86DCF5AB82D8F1AD643E17464F153C60A9F3DA81D882ABF73E644D1C154F663AF3A980D'
    ,   '009631A762F453C5C452F563A63097019503A432F761C65051C760F633A5029437A1069055C364F2F365C2549107A036A2349305C056F16766F057C1049235A36EF85FC90C9A3DABAA3C9B0DC85EF96FFB6DCA5C990FA83E3FA90E985DCB6CFA59CF68FE3BAD0A9C9D0BAC3AFF69CE58CC5AFD6BAE389F09089E39AF6AFC5BCDDC4AED7BBE288F19188E29BF7AEC4BDD49DF78EE2BBD1A8C8D1BBC2AEF79DE48EB7DDA4C891FB82E2FB91E884DDB7CEA7EE84FD91C8A2DBBBA2C8B1DD84EE97FB2248315D046E17776E047D1148225B327B1168045D374E2E375D2448117B0268513B422E771D64041D770E623B51284108621B772E443D5D442E573B6208711'
    ,   '009733A466F155C2CC5BFF68AA3D990E8512B621E374D04749DE7AED2FB81C8B178024B371E642D5DB4CE87FBD2A8E199205A136F463C7505EC96DFA38AF0B9C2EB91D8A48DF7BECE275D1468413B720AB3C980FCD5AFE6967F054C3019632A539AE0A9D5FC86CFBF562C6519304A037BC2B8F18DA4DE97E70E743D4168125B25CCB6FF83AAD099E9007A334F661C552D94EEA7DBF288C1B158226B173E440D74BDC78EF2DBA1E898710B423E176D245CE59FD6AA83F9B0C029531A664F357C072E541D6148327B0BE298D1AD84FEB7CF760C4539106A2353BAC089F5DCA6EF965F256C1039430A7A93E9A0DCF58FC6BE077D3448611B5222CBB1F884ADD79EE'
    ,   '00982DB55AC277EFB42C9901EE76C35B75ED58C02FB7029AC159EC749B03B62EEA72C75FB0289D055EC673EB049C29B19F07B22AC55DE8702BB3069E71E95CC4C951E47C930BBE267DE550C827BF0A92BC249109E67ECB53089025BD52CA7FE723BB0E9679E154CC970FBA22CD55E07856CE7BE30C9421B9E27ACF57B820950D8F17A23AD54DF8603BA3168E61F94CD4FA62D74FA0388D154ED663FB148C39A165FD48D03FA7128AD149FC648B13A63E10883DA54AD267FFA43C8911FE66D34B46DE6BF31C8431A9F26ADF47A830851D33AB1E8669F144DC871FAA32DD45F068AC348119F66EDB43188035AD42DA6FF7D941F46C831BAE366DF540D837AF1A82'
    ,   '00992FB65EC771E8BC25930AE27BCD5465FC4AD33BA2148DD940F66F871EA831CA53E57C940DBB2276EF59C028B1079EAF368019F168DE47138A3CA54DD462FB8910A63FD74EF86135AC1A836BF244DDEC75C35AB22B9D0450C97FE60E9721B843DA6CF51D8432ABFF66D049A1388E1726BF099078E157CE9A03B52CC45DEB720F9620B951C87EE7B32A9C05ED74C25B6AF345DC34AD1B82D64FF9608811A73EC55CEA739B02B42D79E056CF27BE0891A0398F16FE67D1481C8533AA42DB6DF4861FA930D841F76E3AA3158C64FD4BD2E37ACC55BD24920B5FC670E901982EB74CD563FA128B3DA4F069DF46AE37811829B0069F77EE58C1950CBA23CB52E47D'
    ,   '009A29B352C87BE1A43E8D17F66CDF4555CF7CE6079D2EB4F16BD842A3398A10AA308319F862D14B0E9427BD5CC675EFFF65D64CAD37841E5BC172E8099320BA49D360FA1B8132A8ED77C45EBF25960C1C8635AF4ED467FDB822910BEA70C359E379CA50B12B980247DD6EF4158F3CA6B62C9F05E47ECD5712883BA140DA69F39208BB21C05AE97336AC1F8564FE4DD7C75DEE74950FBC2663F94AD031AB188238A2118B6AF043D99C06B52FCE54E77D6DF744DE3FA5168CC953E07A9B01B228DB41F2688913A03A7FE556CC2DB7049E8E14A73DDC46F56F2AB0039978E251CB71EB58C223B90A90D54FFC66871DAE3424BE0D9776EC5FC5801AA933D248FB61'
    ,   '009B2BB056CD7DE6AC37871CFA61D14A45DE6EF5138838A3E972C259BF24940F8A11A13ADC47F76C26BD0D9670EB5BC0CF54E47F9902B22963F848D335AE1E85099222B95FC474EFA53E8E15F368D8434CD767FC1A8131AAE07BCB50B62D9D068318A833D54EFE652FB4049F79E252C9C65DED76900BBB206AF141DA3CA7178C128939A244DF6FF4BE25950EE873C35857CC7CE7019A2AB1FB60D04BAD36861D9803B328CE55E57E34AF1F8462F949D2DD46F66D8B10A03B71EA5AC127BC0C971B8030AB4DD666FDB72C9C07E17ACA515EC575EE089323B8F269D942A43F8F14910ABA21C75CEC773DA6168D6BF040DBD44FFF648219A93278E353C82EB5059E'
    ,   '009C25B94AD66FF39408B12DDE42FB6735A9108C7FE35AC6A13D8418EB77CE526AF64FD320BC0599FE62DB47B428910D5FC37AE6158930ACCB57EE72811DA438D448F16D9E02BB2740DC65F90A962FB3E17DC458AB378E1275E950CC3FA31A86BE229B07F468D14D2AB60F9360FC45D98B17AE32C15DE4781F833AA655C970ECB529900CFF63DA4621BD04986BF74ED2801CA539CA56EF73148831AD5EC27BE7DF43FA669509B02C4BD76EF2019D24B8EA76CF53A03C85197EE25BC734A8118D61FD44D82BB70E92F569D04CBF239A0654C871ED1E823BA7C05CE5798A16AF330B972EB241DD64F89F03BA26D549F06C3EA21B8774E851CDAA368F13E07CC559'
    ,   '009D27BA4ED369F49C01BB26D24FF56825B8029F6BF64CD1B9249E03F76AD04D4AD76DF0049923BED64BF16C9805BF226FF248D521BC069BF36ED449BD209A079409B32EDA47FD6008952FB246DB61FCB12C960BFF62D8452DB00A9763FE44D9DE43F964900DB72A42DF65F80C912BB6FB66DC41B528920F67FA40DD29B40E9335A8128F7BE65CC1A9348E13E77AC05D108D37AA5EC379E48C11AB36C25FE5787FE258C531AC168BE37EC459AD308A175AC77DE0148933AEC65BE17C8815AF32A13C861BEF72C8553DA01A8773EE54C98419A33ECA57ED7018853FA256CB71ECEB76CC51A538821F77EA50CD39A41E83CE53E974801DA73A52CF75E81C813BA6'
    ,   '009E21BF42DC63FD841AA53BC658E779158B34AA57C976E8910FB02ED34DF26C2AB40B9568F649D7AE308F11EC72CD533FA11E807DE35CC2BB259A04F967D84654CA75EB168837A9D04EF16F920CB32D41DF60FE039D22BCC55BE47A8719A6387EE05FC13CA21D83FA64DB45B82699076BF54AD429B70896EF71CE50AD338C12A8368917EA74CB552CB20D936EF04FD1BD239C02FF61DE4039A718867BE55AC4821CA33DC05EE17F069827B944DA65FB9709B628D54BF46A138D32AC51CF70EEFC62DD43BE209F0178E659C73AA41B85E977C856AB358A146DF34CD22FB10E90D648F769940AB52B52CC73ED108E31AFC35DE27C811FA03E47D966F8059B24BA'
    ,   '009F23BC46D965FA8C13AF30CA55E976059A26B943DC60FF8916AA35CF50EC730A9529B64CD36FF08619A53AC05FE37C0F902CB349D66AF5831CA03FC55AE679148B37A852CD71EE9807BB24DE41FD62118E32AD57C874EB9D02BE21DB44F8671E813DA258C77BE4920DB12ED44BF7681B8438A75DC27EE19708B42BD14EF26D28B70B946EF14DD2A43B8718E27DC15E2DB20E916BF448D7A13E821DE778C45B22BD019E64FB47D8AE318D12E877CB5427B8049B61FE42DDAB348817ED72CE513CA31F807AE559C6B02F930CF669D54A39A61A857FE05CC3B52A9609F36CD04F36A9158A70EF53CCBA259906FC63DF4033AC108F75EA56C9BF209C03F966DA45'
    ,   '00A05DFDBA1AE74769C93494D3738E2ED2728F2F68C83595BB1BE64601A15CFCB919E44403A35EFED0708D2D6ACA37976BCB3696D1718C2C02A25FFFB818E5456FCF3292D575882806A65BFBBC1CE141BD1DE04007A75AFAD47489296ECE3393D6768B2B6CCC3191BF1FE24205A558F804A459F9BE1EE3436DCD3090D7778A2ADE7E832364C43999B717EA4A0DAD50F00CAC51F1B616EB4B65C53898DF7F822267C73A9ADD7D80200EAE53F3B414E949B515E8480FAF52F2DC7C812166C63B9BB111EC4C0BAB56F6D878852562C23F9F63C33E9ED97984240AAA57F7B010ED4D08A855F5B212EF4F61C13C9CDB7B8626DA7A872760C03D9DB313EE4E09A954F4'
    ,   '00A15FFEBE1FE14061C03E9FDF7E8021C2639D3C7CDD2382A302FC5D1DBC42E39938C667278678D9F859A70646E719B85BFA04A5E544BA1B3A9B65C48425DB7A2F8E70D19130CE6F4EEF11B0F051AF0EED4CB21353F20CAD8C2DD37232936DCCB617E94808A957F6D776882969C8369774D52B8ACA6B953415B44AEBAB0AF4555EFF01A0E041BF1E3F9E60C18120DE7F9C3DC36222837DDCFD5CA20343E21CBDC766983979D82687A607F95818B947E605A45AFBBB1AE44564C53B9ADA7B852471D02E8FCF6E903110B14FEEAE0FF150B312EC4D0DAC52F3D2738D2C6CCD3392E849B71656F709A88928D677379668C92A8B75D49435CB6A4BEA14B5F554AA0B'
    ,   '00A259FBB210EB4979DB2082CB699230F250AB0940E219BB8B29D270399B60C2F95BA0024BE912B08022D97B32906BC90BA952F0B91BE04272D02B89C062993BEF4DB6145DFF04A69634CF6D24867DDF1DBF44E6AF0DF65464C63D9FD6748F2D16B44FEDA406FD5F6FCD3694DD7F8426E446BD1F56F40FAD9D3FC4662F8D76D4C3619A3871D3288ABA18E34108AA51F3319368CA8321DA7848EA11B3FA58A3013A9863C1882AD17343E11AB8F153A80AC86A91337AD82381B113E84A03A15AF82C8E75D79E3CC76555F70CAEE745BE1CDE7C87256CCE3597A705FE5C15B74CEED5778C2E67C53E9CAC0EF5571EBC47E527857EDC9537CC6E5EFC07A5EC4EB517'
    ,   '00A35BF8B615ED4E71D22A89C7649C3FE241B91A54F70FAC9330C86B25867EDDD97A82216FCC3497A80BF3501EBD45E63B9860C38D2ED6754AE911B2FC5FA704AF0CF45719BA42E1DE7D852668CB33904DEE16B5FB58A0033C9F67C48A29D17276D52D8EC0639B3807A45CFFB112EA499437CF6C228179DAE546BE1D53F008AB43E018BBF556AE0D329169CA8427DF7CA102FA5917B44CEFD0738B2866C53D9E9A39C1622C8F77D4EB48B0135DFE06A578DB2380CE6D953609AA52F1BF1CE447EC4FB7145AF901A29D3EC6652B8870D30EAD55F6B81BE3407FDC2487C96A923135966ECD8320D87B44E71FBCF251A90AD7748C2F61C23A99A605FD5E10B34BE8'
    ,   '00A455F1AA0EFF5B49ED1CB8E347B6129236C763389C6DC9DB7F8E2A71D52480399D6CC89337C66270D42581DA7E8F2BAB0FFE5A01A554F0E246B71348EC1DB972D62783D87C8D293B9F6ECA9135C460E044B5114AEE1FBBA90DFC5803A756F24BEF1EBAE145B41002A657F3A80CFD59D97D8C2873D726829034C5613A9E6FCBE440B1154EEA1BBFAD09F85C07A352F676D22387DC78892D3F9B6ACE9531C064DD79882C77D322869430C1653E9A6BCF4FEB1ABEE541B01406A253F7AC08F95D9632C3673C9869CDDF7B8A2E75D1208404A051F5AE0AFB5F4DE918BCE743B216AF0BFA5E05A150F4E642B3174CE819BD3D9968CC9733C26674D02185DE7A8B2F'
    ,   '00A557F2AE0BF95C41E416B3EF4AB81D8227D5702C897BDEC36694316DC83A9F19BC4EEBB712E04558FD0FAAF653A1049B3ECC69359062C7DA7F8D2874D12386329765C09C39CB6E73D62481DD788A2FB015E7421EBB49ECF154A6035FFA08AD2B8E7CD98520D2776ACF3D98C4619336A90CFE5B07A250F5E84DBF1A46E311B464C13396CA6F9D38258072D78B2EDC79E643B11448ED1FBAA702F05509AC5EFB7DD82A8FD37684213C996BCE9237C560FF5AA80D51F406A3BE1BE94C10B547E256F301A4F85DAF0A17B240E5B91CEE4BD47183267ADF2D889530C2673B9E6CC94FEA18BDE144B6130EAB59FCA005F752CD689A3F63C634918C29DB7E228775D0'
    ,   '00A651F7A204F35559FF08AEFB5DAA0CB214E34510B641E7EB4DBA1C49EF18BE79DF288EDB7D8A2C208671D78224D375CB6D9A3C69CF389E9234C365309661C7F254A30550F601A7AB0DFA5C09AF58FE40E611B7E244B31519BF48EEBB1DEA4C8B2DDA7C298F78DED274832570D62187399F68CE9B3DCA6C60C63197C2649335F95FA80E5BFD0AACA006F15702A453F54BED1ABCE94FB81E12B443E5B016E1478026D177228473D5D97F882E7BDD2A8C329463C59036C1676BCD3A9CC96F983E0BAD5AFCA90FF85E52F403A5F056A107B91FE84E1BBD4AECE046B11742E413B572D42385D07681272B8D7ADC892FD87EC066913762C43395993FC86E3B9D6ACC'
    ,   '00A753F4A601F55251F602A5F750A403A205F15604A357F0F354A00755F206A159FE0AADFF58AC0B08AF5BFCAE09FD5AFB5CA80F5DFA0EA9AA0DF95E0CAB5FF8B215E14614B347E0E344B01745E216B110B743E4B611E54241E612B5E740B413EB4CB81F4DEA1EB9BA1DE94E1CBB4FE849EE1ABDEF48BC1B18BF4BECBE19ED4A79DE2A8DDF788C2B288F7BDC8E29DD7ADB7C882F7DDA2E898A2DD97E2C8B7FD8208773D48621D57271D62285D77084238225D176248377D0D374802775D22681CB6C983F6DCA3E999A3DC96E3C9B6FC869CE3A9DCF689C3B389F6BCC9E39CD6A9235C166349367C0C364903765C23691309763C49631C56261C63295C7609433'
    ,   '00A84DE59A32D77F298164CCB31BFE5652FA1FB7C860852D7BD3369EE149AC04A40CE9413E9673DB8D25C06817BF5AF2F65EBB136CC42189DF77923A45ED08A055FD18B0CF67822A7CD43199E64EAB0307AF4AE29D35D0782E8663CBB41CF951F159BC146BC3268ED870953D42EA0FA7A30BEE46399174DC8A22C76F10B85DF5AA02E74F30987DD5832BCE6619B154FCF850B51D62CA2F87D1799C344BE306AE0EA643EB943CD971278F6AC2BD15F0585CF411B9C66E8B2375DD3890EF47A20AFF57B21A65CD2880D67E9B334CE401A9AD05E048379F7AD2842CC9611EB653FB5BF316BEC1698C2472DA3F97E840A50D09A144EC933BDE7620886DC5BA12F75F'
    ,   '00A94FE69E37D17821886EC7BF16F05942EB0DA4DC75933A63CA2C85FD54B21B842DCB621AB355FCA50CEA433B9274DDC66F892058F117BEE74EA80179D0369F15BC5AF38B22C46D349D7BD2AA03E54C57FE18B1C960862F76DF3990E841A70E9138DE770FA640E9B019FF562E8761C8D37A9C354DE402ABF25BBD146CC5238A2A8365CCB41DFB520BA244ED953CDA7368C1278EF65FB91049E006AFD77E9831AE07E14830997FD68F26C06911B85EF7EC45A30A72DB3D94CD64822B53FA1CB53F9670D9A108EE471EB751F88029CF667DD4329BE34AAC055CF513BAC26B8D24BB12F45D258C6AC39A33D57C04AD4BE2F950B61F67CE2881D871973E46EF09A0'
    ,   '00AA49E39238DB71399370DAAB01E24872D83B91E04AA9034BE102A8D973903AE44EAD0776DC3F95DD77943E4FE506AC963CDF7504AE4DE7AF05E64C3D9774DED57F9C3647ED0EA4EC46A50F7ED4379DA70DEE44359F7CD69E34D77D0CA645EF319B78D2A309EA4008A241EB9A30D37943E90AA0D17B98327AD03399E842A10BB71DFE54258F6CC68E24C76D1CB655FFC56F8C2657FD1EB4FC56B51F6EC4278D53F91AB0C16B88226AC02389F852B11B218B68C2B319FA5018B251FB8A20C36962C82B81F05AB9135BF112B8C963802A10BA59F38228CB61298360CABB11F258862CCF6514BE5DF7BF15F65C2D8764CEF45EBD1766CC2F85CD67842E5FF516BC'
    ,   '00AB4BE0963DDD76319A7AD1A70CEC4762C92982F45FBF1453F818B3C56E8E25C46F8F2452F919B2F55EBE1563C82883A60DED46309B7BD0973CDC7701AA4AE1953EDE7503A848E3A40FEF44329979D2F75CBC1761CA2A81C66D8D2650FB1BB051FA1AB1C76C8C2760CB2B80F65DBD16339878D3A50EEE4502A949E2943FDF74379C7CD7A10AEA4106AD4DE6903BDB7055FE1EB5C368882364CF2F84F259B912F358B81365CE2E85C269892254FF1FB4913ADA7107AC4CE7A00BEB40369D7DD6A209E942349F7FD49338D87305AE4EE5C06B8B2056FD1DB6F15ABA1167CC2C8766CD2D86F05BBB1057FC1CB7C16A8A2104AF4FE49239D972359E7ED5A308E843'
    ,   '00AC45E98A26CF6309A54CE0832FC66A12BE57FB9834DD711BB75EF2913DD478248861CDAE02EB472D8168C4A70BE24E369A73DFBC10F9553F937AD6B519F05C48E40DA1C26E872B41ED04A8CB678E225AF61FB3D07C953953FF16BAD9759C306CC02985E64AA30F65C9208CEF43AA067ED23B97F458B11D77DB329EFD51B814903CD5791AB65FF39935DC7013BF56FA822EC76B08A44DE18B27CE6201AD44E8B418F15D3E927BD7BD11F854379B72DEA60AE34F2C8069C5AF03EA46258960CCD8749D3152FE17BBD17D94385BF71EB2CA668F2340EC05A9C36F862A49E50CA0FC50B91576DA339FF559B01C7FD33A96EE42AB0764C8218DE74BA20E6DC12884'
    ,   '00AD47EA8E23C96401AC46EB8F22C86502AF45E88C21CB6603AE44E98D20CA6704A943EE8A27CD6005A842EF8B26CC6106AB41EC8825CF6207AA40ED8924CE6308A54FE2862BC16C09A44EE3872AC06D0AA74DE08429C36E0BA64CE18528C26F0CA14BE6822FC5680DA04AE7832EC4690EA349E4802DC76A0FA248E5812CC66B10BD57FA9E33D97411BC56FB9F32D87512BF55F89C31DB7613BE54F99D30DA7714B953FE9A37DD7015B852FF9B36DC7116BB51FC9835DF7217BA50FD9934DE7318B55FF2963BD17C19B45EF3973AD07D1AB75DF09439D37E1BB65CF19538D27F1CB15BF6923FD5781DB05AF7933ED4791EB359F4903DD77A1FB258F5913CD67B'
    ,   '00AE41EF822CC36D19B758F69B35DA74329C73DDB01EF15F2B856AC4A907E84664CA258BE648A7097DD33C92FF51BE1056F817B9D47A953B4FE10EA0CD638C22C86689274AE40BA5D17F903E53FD12BCFA54BB1578D63997E34DA20C61CF208EAC02ED432E806FC1B51BF45A379976D89E30DF711CB25DF38729C66805AB44EA8D23CC620FA14EE0943AD57B16B857F9BF11FE503D937CD2A608E749248A65CBE947A8066BC52A84F05EB11F72DC339DDB759A3459F718B6C26C832D40EE01AF45EB04AAC76986285CF21DB3DE709F3177D93698F55BB41A6EC02F81EC42AD03218F60CEA30DE24C389679D7BA14FB5513BD52FC913FD07E0AA44BE58826C967'
    ,   '00AF43EC8629C56A11BE52FD9738D47B228D61CEA40BE748339C70DFB51AF65944EB07A8C26D812E55FA16B9D37C903F66C9258AE04FA30C77D8349BF15EB21D8827CB640EA14DE29936DA751FB05CF3AA05E9462C836FC0BB14F8573D927ED1CC638F204AE509A6DD729E315BF418B7EE41AD0268C72B84FF50BC1379D63A950DA24EE18B24C8671CB35FF09A35D9762F806CC3A906EA453E917DD2B817FB5449E60AA5CF608C2358F71BB4DE719D326BC42887ED42AE017AD53996FC53BF10852AC66903AC40EF943BD77812BD51FEA708E44B218E62CDB619F55A309F73DCC16E822D47E804ABD07F933C56F915BAE34CA00F65CA2689F25DB11E74DB3798'
    ,   '00B07DCDFA4A8737E959942413A36EDECF7FB202358548F826965BEBDC6CA1118333FE4E79C904B46ADA17A79020ED5D4CFC3181B606CB7BA515D8685FEF22921BAB66D6E1519C2CF2428F3F08B875C5D464A9192E9E53E33D8D40F0C777BA0A9828E55562D21FAF71C10CBC8B3BF64657E72A9AAD1DD060BE0EC37344F4398936864BFBCC7CB101DF6FA212259558E8F949843403B37ECE10A06DDDEA5A9727B505C8784FFF32825CEC2191A616DB6B7ACA07B78030FD4D9323EE5E69D914A42D9D50E0D767AA1AC474B9093E8E43F3E2529F2F18A865D50BBB76C6F1418C3CAE1ED36354E4299947F73A8ABD0DC07061D11CAC9B2BE6568838F54572C20FBF'
    ,   '00B17FCEFE4F8130E1509E2F1FAE60D1DF6EA01121905EEF3E8F41F0C071BF0EA312DC6D5DEC229342F33D8CBC0DC3727CCD03B28233FD4C9D2CE25363D21CAD5BEA2495A514DA6BBA0BC57444F53B8A8435FB4A7ACB05B465D41AAB9B2AE455F849873606B779C819A866D7E7569829279658E9D968A617C677B908388947F6B607C97848F9378657E62899A918D66769D816A79726E8598839F74676C709B815A46ADBEB5A9425F4458B3A0ABB75C4CA7BB50434854BFA2B9A54E5D564AA1BED5C922313A26CDD0CBD73C2F2438D3C32834DFCCC7DB302D362AC1D2D9C52E34EFF3180B001CF7EAF1ED06151E02E9F9120EE5F6FDE10A170C10FBE8E3FF140'
    ,   '00B279CBF2408B39F94B80320BB972C0EF5D96241DAF64D616A46FDDE4569D2FC371BA08318348FA3A8843F1C87AB1032C9E55E7DE6CA715D567AC1E27955EEC9B29E25069DB10A262D01BA99022E95B74C60DBF8634FF4D8D3FF4467FCD06B458EA2193AA18D361A113D86A53E12A98B705CE7C45F73C8E4EFC3785BC0EC5772B9952E0D96BA012D260AB19209259EBC476BD0F36844FFD3D8F44F6CF7DB604E85A91231AA863D111A368DAE3519A2807B57ECCF5478C3EFE4C87350CBE75C7B002C97B42F03B8949FB3082BB09C2705FED2694AD1FD466A614DF6D54E62D9F73C10AB88133F84A8A38F34178CA01B39C2EE5576EDC17A565D71CAE9725EE5C'
    ,   '00B37BC8F6458D3EF1428A3907B47CCFFF4C843709BA72C10EBD75C6F84B8330E350982B15A66EDD12A169DAE4579F2C1CAF67D4EA599122ED5E96251BA860D3DB68A0132D9E56E52A9951E2DC6FA71424975FECD261A91AD566AE1D239058EB388B43F0CE7DB506C97AB2013F8C44F7C774BC0F31824AF936854DFEC073BB08AB18D0635DEE26955AE92192AC1FD76454E72F9CA211D96AA516DE6D53E0289B48FB3380BE0DC576B90AC2714FFC3487B704CC7F41F23A8946F53D8EB003CB7870C30BB88635FD4E8132FA4977C40CBF8F3CF44779CA02B17ECD05B6883BF3409320E85B65D61EAD62D119AA9427EF5C6CDF17A49A29E1529D2EE6556BD810A3'
    ,   '00B475C1EA5E9F2BC97DBC08239756E28F3BFA4E65D110A446F23387AC18D96D03B776C2E95D9C28CA7EBF0B209455E18C38F94D66D213A745F13084AF1BDA6E06B273C7EC58992DCF7BBA0E259150E4893DFC4863D716A240F43581AA1EDF6B05B170C4EF5B9A2ECC78B90D269253E78A3EFF4B60D415A143F73682A91DDC680CB879CDE6529327C571B0042F9B5AEE8337F64269DD1CA84AFE3F8BA014D5610FBB7ACEE5519024C672B3072C9859ED8034F5416ADE1FAB49FD3C88A317D6620ABE7FCBE0549521C377B602299D5CE88531F0446FDB1AAE4CF8398DA612D36709BD7CC8E3579622C074B5012A9E5FEB8632F3476CD819AD4FFB3A8EA511D064'
    ,   '00B577C2EE5B992CC174B6032F9A58ED9F2AE85D71C406B35EEB299CB005C772239654E1CD78BA0FE25795200CB97BCEBC09CB7E52E725907DC80ABF9326E45146F33184A81DDF6A8732F04569DC1EABD96CAE1B378240F518AD6FDAF643813465D012A78B3EFC49A411D3664AFF3D88FA4F8D3814A163D63B8E4CF9D560A2178C39FB4E62D715A04DF83A8FA316D46113A664D1FD488A3FD267A5103C894BFEAF1AD86D41F436836EDB19AC8035F742308547F2DE6BA91CF14486331FAA68DDCA7FBD08249153E60BBE7CC9E550922755E02297BB0ECC799421E3567ACF0DB8E95C9E2B07B270C5289D5FEAC673B10476C301B4982DEF5AB702C07559EC2E9B'
    ,   '00B671C7E2549325D96FA81E3B8D4AFCAF19DE684DFB3C8A76C007B19422E55343F53284A117D0669A2CEB5D78CE09BFEC5A9D2B0EB87FC9358344F2D761A6108630F74164D215A35FE92E98BD0BCC7A299F58EECB7DBA0CF046813712A463D5C573B402279156E01CAA6DDBFE488F396ADC1BAD883EF94FB305C27451E7209611A760D6F3458234C87EB90F2A9C5BEDBE08CF795CEA2D9B67D116A08533F44252E42395B006C1778B3DFA4C69DF18AEFD4B8C3A1FA96ED8249255E3C670B7019721E65075C304B24EF83F89AC1ADD6B388E49FFDA6CAB1DE157902603B572C4D462A513368047F10DBB7CCAEF599E287BCD0ABC992FE85EA214D36540F63187'
    ,   '00B773C4E6519522D166A215378044F3BF08CC7B59EE2A9D6ED91DAA883FFB4C63D410A78532F641B205C17654E32790DC6BAF183A8D49FE0DBA7EC9EB5C982FC671B502209753E417A064D3F146823579CE0ABD9F28EC5BA81FDB6C4EF93D8AA512D66143F4308774C307B09225E1561AAD69DEFC4B8F38CB7CB80F2D9A5EE99126E25577C004B340F73384A611D5622E995DEAC87FBB0CFF488C3B19AE6ADDF245813614A367D0239450E7C572B6014DFA3E89AB1CD86F9C2BEF587ACD09BE57E02493B106C2758631F54260D713A4E85F9B2C0EB97DCA398E4AFDDF68AC1B348347F0D265A116E552962103B470C78B3CF84F6DDA1EA95AED299EBC0BCF78'
    ,   '00B86DD5DA62B70FA911C47C73CB1EA64FF7229A952DF840E65E8B333C8451E99E26F34B44FC2991378F5AE2ED558038D169BC040BB366DE78C015ADA21ACF7721994CF4FB43962E8830E55D52EA3F876ED603BBB40CD961C77FAA121DA570C8BF07D26A65DD08B016AE7BC3CC74A119F0489D252A9247FF59E1348C833BEE5642FA2F979820F54DEB53863E31895CE40DB560D8D76FBA02A41CC9717EC613ABDC64B10906BE6BD375CD18A0AF17C27A932BFE4649F1249C3A8257EFE0588D3563DB0EB6B901D46CCA72A71F10A87DC52C9441F9F64E9B23853DE8505FE7328AFD459028279F4AF254EC39818E36E35BB20ADF6768D005BD1BA376CEC179AC14'
    ,   '00B96FD6DE67B108A118CE777FC610A95FE630898138EE57FE47912820994FF6BE07D16860D90FB61FA670C9C178AE17E1588E373F8650E940F92F969E27F14861D80EB7BF06D069C079AF161EA771C83E8751E8E0598F369F26F04941F82E97DF66B00901B86ED77EC711A8A019CF768039EF565EE7318821984EF7FF469029C27BAD141CA573CA63DA0CB5BD04D26B9D24F24B43FA2C953C8553EAE25B8D347CC513AAA21BCD74DD64B20B03BA6CD5239A4CF5FD44922B823BED545CE5338AA31ACC757DC412AB02BB6DD4DC65B30AFC45932A229B4DF45DE4328B833AEC551DA472CBC37AAC15BC05D36A62DB0DB442FB2D949C25F34AE35A8C353D8452EB'
    ,   '00BA69D3D268BB01B903D06A6BD102B86FD506BCBD07D46ED66CBF0504BE6DD7DE64B70D0CB665DF67DD0EB4B50FDC66B10BD86263D90AB008B261DBDA60B309A11BC87273C91AA018A271CBCA70A319CE74A71D1CA675CF77CD1EA4A51FCC767FC516ACAD17C47EC67CAF1514AE7DC710AA79C3C278AB11A913C07A7BC112A85FE5368C8D37E45EE65C8F35348E5DE7308A59E3E2588B318933E05A5BE13288813BE85253E93A80388251EBEA508339EE54873D3C8655EF57ED3E84853FEC56FE44972D2C9645FF47FD2E94952FFC46912BF84243F92A90289241FBFA409329209A49F3F2489B219923F04A4BF122984FF5269C9D27F44EF64C9F25249E4DF7'
    ,   '00BB6BD0D66DBD06B10ADA6167DC0CB77FC414AFA912C279CE75A51E18A373C8FE45952E289343F84FF4249F9922F249813AEA5157EC3C87308B5BE0E65D8D36E15A8A31378C5CE750EB3B80863DED569E25F54E48F323982F9444FFF94292291FA474CFC972A219AE15C57E78C313A860DB0BB0B60DDD66D16ABA0107BC6CD7DF64B40F09B262D96ED505BEB803D368A01BCB7076CD1DA611AA7AC1C77CAC17219A4AF1F74C9C27902BFB4046FD2D965EE5358E8833E358EF54843F398252E93E8555EEE85383388F34E45F59E2328941FA2A91972CFC47F04B9B20269D4DF6C07BAB1016AD7DC671CA1AA1A71CCC77BF04D46F69D202B90EB565DED863B308'
    ,   '00BC65D9CA76AF138935EC5043FF269A0FB36AD6C579A01C863AE35F4CF029951EA27BC7D468B10D972BF24E5DE1388411AD74C8DB67BE029824FD4152EE378B3C8059E5F64A932FB509D06C7FC31AA6338F56EAF9459C20BA06DF6370CC15A9229E47FBE8548D31AB17CE7261DD04B82D9148F4E75B823EA418C17D6ED20BB778C41DA1B20ED76BF14D94283B875EE277CB12AEBD01D864FE429B27348851ED66DA03BFAC10C975EF538A36259940FC69D50CB0A31FC67AE05C85392A964FF344F8219D8E32EB57CD71A81407BB62DE4BF72E92813DE458C27EA71B08B46DD15AE63F83902CF549D36FB60A19A57CC055E9308C9F23FA46DC60B90516AA73CF'
    ,   '00BD67DACE73A914813CE65B4FF228951FA278C5D16CB60B9E23F94450ED378A3E8359E4F04D972ABF02D86571CC16AB219C46FBEF528835A01DC77A6ED309B47CC11BA6B20FD568FD409A27338E54E963DE04B9AD10CA77E25F85382C914BF642FF25988C31EB56C37EA4190DB06AD75DE03A87932EF449DC61BB0612AF75C8F8459F22368B51EC79C41EA3B70AD06DE75A803D29944EF366DB01BCA815CF72C67BA11C08B56FD247FA209D8934EE53D964BE0317AA70CD58E53F82962BF14C8439E35E4AF72D9005B862DFCB76AC119B26FC4155E8328F1AA77DC0D469B30EBA07DD6074C913AE3B865CE1F548922FA518C27F6BD60CB1249943FEEA578D30'
    ,   '00BE61DFC27CA31D9927F8465BE53A842F914EF0ED538C32B608D76974CA15AB5EE03F819C22FD43C779A61805BB64DA71CF10AEB30DD26CE85689372A944BF5BC02DD637EC01FA1259B44FAE7598638932DF24C51EF308E0AB46BD5C876A917E25C833D209E41FF7BC51AA4B907D866CD73AC120FB16ED054EA358B9628F74965DB04BAA719C678FC429D233E805FE14AF42B958836E957D36DB20C11AF70CE3B855AE4F9479826A21CC37D60DE01BF14AA75CBD668B7098D33EC524FF12E90D967B8061BA57AC440FE219F823CE35DF6489729348A55EB6FD10EB0AD13CC728739E65845FB249A1EA07FC1DC62BD03A816C9776AD40BB5318F50EEF34D922C'
    ,   '00BF63DCC679A51A912EF24D57E8348B3F805CE3F9469A25AE11CD7268D70BB47EC11DA2B807DB64EF508C3329964AF541FE229D8738E45BD06FB30C16A975CAFC439F203A8559E66DD20EB1AB14C877C37CA01F05BA66D952ED318E942BF748823DE15E44FB279813AC70CFD56AB609BD02DE617BC418A72C934FF0EA558936E55A8639239C40FF74CB17A8B20DD16EDA65B9061CA37FC04BF428978D32EE519B24F8475DE23E810AB569D6CC73AF10A41BC77862DD01BE358A56E9F34C902F19A67AC5DF60BC038837EB544EF12D92269945FAE05F833CB708D46B71CE12AD67D804BBA11EC27DF649952A308F53EC58E73B849E21FD42C976AA150FB06CD3'
    ,   '00C09D5D27E7BA7A4E8ED31369A9F4349C5C01C1BB7B26E6D2124F8FF53568A825E5B87802C29F5F6BABF6364C8CD111B97924E49E5E03C3F7376AAAD0104D8D4A8AD7176DADF03004C4995923E3BE7ED6164B8BF1316CAC985805C5BF7F22E26FAFF2324888D51521E1BC7C06C69B5BF3336EAED4144989BD7D20E09A5A07C7945409C9B3732EEEDA1A4787FD3D60A008C895552FEFB2724686DB1B61A1FC3CB1712CEC96560BCBFF3F62A2D81845852DEDB0700ACA975763A3FE3E4484D919DE1E4383F93964A490500DCDB7772AEA4282DF1F65A5F8380CCC91512BEBB676FB3B66A6DC1C4181B57528E892520FCF67A7FA3A4080DD1D29E9B4740ECE9353'
    ,   '00C19F5E23E2BC7D4687D91865A4FA3B8C4D13D2AF6E30F1CA0B5594E92876B705C49A5B26E7B9784382DC1D60A1FF3E894816D7AA6B35F4CF0E5091EC2D73B20ACB955429E8B6774C8DD3126FAEF031864719D8A5643AFBC0015F9EE3227CBD0FCE90512CEDB3724988D6176AABF53483421CDDA0613FFEC5045A9BE62779B814D58B4A37F6A8695293CD0C71B0EE2F985907C6BB7A24E5DE1F4180FD3C62A311D08E4F32F3AD6C5796C80974B5EB2A9D5C02C3BE7F21E0DB1A4485F83967A61EDF81403DFCA2635899C7067BBAE42592530DCCB1702EEFD4154B8AF73668A91BDA844538F9A7665D9CC2037EBFE120975608C9B4752BEAD1104E8FF2336DAC'
    ,   '00C2995B2FEDB6745E9CC70571B3E82ABC7E25E793510AC8E2207BB9CD0F549665A7FC3E4A88D3113BF9A26014D68D4FD91B4082F6346FAD87451EDCA86A31F3CA085391E5277CBE94560DCFBB7922E076B4EF2D599BC00228EAB17307C59E5CAF6D36F4804219DBF13368AADE1C478513D18A483CFEA5674D8FD41662A0FB39894B10D2A6643FFDD7154E8CF83A61A335F7AC6E1AD883416BA9F2304486DD1FEC2E75B7C3015A98B2702BE99D5F04C65092C90B7FBDE6240ECC975521E3B87A4381DA186CAEF5371DDF844632F0AB69FF3D66A4D012498BA16338FA8E4C17D526E4BF7D09CB905278BAE1235795CE0C9A5803C1B5772CEEC4065D9FEB2972B0'
    ,   '00C39B582BE8B0735695CD0E7DBEE625AC6F37F487441CDFFA3961A2D1124A894586DE1D6EADF53613D0884B38FBA360E92A72B1C201599ABF7C24E794570FCC8A4911D2A1623AF9DC1F4784F7346CAF26E5BD7E0DCE965570B3EB285B98C003CF0C5497E4277FBC995A02C1B27129EA63A0F83B488BD31035F6AE6D1EDD854609CA925122E1B97A5F9CC40774B7EF2CA5663EFD8E4D15D6F33068ABD81B43804C8FD71467A4FC3F1AD9814231F2AA69E0237BB8CB085093B6752DEE9D5E06C5834018DBA86B33F0D5164E8DFE3D65A62FECB47704C79F5C79BAE2215291C90AC6055D9EED2E76B590530BC8BB7820E36AA9F1324182DA193CFFA76417D48C4F'
    ,   '00C4955137F3A2666EAAFB3F599DCC08DC18498DEB2F7EBAB27627E3854110D4A56130F4925607C3CB0F5E9AFC3869AD79BDEC284E8ADB1F17D3824620E4B5715793C20660A4F53139FDAC680ECA9B5F8B4F1EDABC7829EDE52170B4D2164783F23667A3C50150949C5809CDAB6F3EFA2EEABB7F19DD8C484084D51177B3E226AE6A3BFF995D0CC8C0045591F73362A672B6E7234581D0141CD8894D2BEFBE7A0BCF9E5A3CF8A96D65A1F0345296C703D7134286E02475B1B97D2CE88E4A1BDFF93D6CA8CE0A5B9F975302C6A06435F125E1B07412D687434B8FDE1A7CB8E92D5C98C90D6BAFFE3A32F6A76305C19054804415D1B77322E6EE2A7BBFD91D4C88'
    ,   '00C5975233F6A46166A3F1345590C207CC095B9EFF3A68ADAA6F3DF8995C0ECB854012D7B67321E4E32674B1D0154782498CDE1B7ABFED282FEAB87D1CD98B4E17D2804524E1B37671B4E6234287D510DB1E4C89E82D7FBABD782AEF8E4B19DC925705C0A16436F3F43163A6C70250955E9BC90C6DA8FA3F38FDAF6A0BCE9C592EEBB97C1DD88A4F488DDF1A7BBEEC29E22775B0D1144683844113D6B77220E5AB6E3CF9985D0FCACD085A9FFE3B69AC67A2F0355491C30601C4965332F7A56039FCAE6B0ACF9D585F9AC80D6CA9FB3EF53062A7C6035194935604C1A06537F2BC792BEE8F4A18DDDA1F4D88E92C7EBB70B5E7224386D41116D3814425E0B277'
    ,   '00C691573FF9AE687EB8EF294187D016FC3A6DABC3055294824413D5BD7B2CEAE52374B2DA1C4B8D9B5D0ACCA46235F319DF884E26E0B77167A1F630589EC90FD7114680E82E79BFA96F38FE965007C12BEDBA7C14D285435593C4026AACFB3D32F4A3650DCB9C5A4C8ADD1B73B5E224CE085F99F13760A6B07621E78F491ED8B37522E48C4A1DDBCD0B5C9AF23463A54F89DE1870B6E12731F7A0660EC89F595690C70169AFF83E28EEB97F17D18640AA6C3BFD955304C2D4124583EB2D7ABC64A2F5335B9DCA0C1ADC8B4D25E3B472985E09CFA76136F0E62077B1D91F488E814710D6BE782FE9FF396EA8C00651977DBBEC2A4284D31503C592543CFAAD6B'
    ,   '00C793543BFCA86F76B1E5224D8ADE19EC2B7FB8D71044839A5D09CEA16632F5C5025691FE396DAAB37420E7884F1BDC29EEBA7D12D581465F98CC0B64A3F730975004C3AC6B3FF8E12672B5DA1D498E7BBCE82F4087D3140DCA9E5936F1A5625295C10669AEFA3D24E3B7701FD88C4BBE792DEA854216D1C80F5B9CF33460A733F4A06708CF9B5C4582D6117EB9ED2ADF184C8BE42377B0A96E3AFD925501C6F63165A2CD0A5E99804713D4BB7C28EF1ADD894E21E6B2756CABFF385790C403A46337F09F580CCBD2154186E92E7ABD488FDB1C73B4E0273EF9AD6A05C2965161A6F2355A9DC90E17D084432CEBBF788D4A1ED9B67125E2FB3C68AFC0075394'
    ,   '00C88D4507CF8A420EC6834B09C1844C1CD491591BD3965E12DA9F5715DD985038F0B57D3FF7B27A36FEBB7331F9BC7424ECA96123EBAE662AE2A76F2DE5A06870B8FD3577BFFA327EB6F33B79B1F43C6CA4E1296BA3E62E62AAEF2765ADE8204880C50D4F87C20A468ECB034189CC04549CD911539BDE165A92D71F5D95D018E0286DA5E72F6AA2EE2663ABE92164ACFC3471B9FB3376BEF23A7FB7F53D78B0D810559DDF17529AD61E5B93D1195C94C40C4981C30B4E86CA02478FCD05408890581DD5975F1AD29E5613DB995114DC8C4401C98B4306CE824A0FC7854D08C0A86025EDAF6722EAA66E2BE3A1692CE4B47C39F1B37B3EF6BA7237FFBD7530F8'
    ,   '00C98F4603CA8C4506CF894005CC8A430CC5834A0FC680490AC3854C09C0864F18D1975E1BD2945D1ED791581DD4925B14DD9B5217DE985112DB9D5411D89E5730F9BF7633FABC7536FFB97035FCBA733CF5B37A3FF6B0793AF3B57C39F0B67F28E1A76E2BE2A46D2EE7A1682DE4A26B24EDAB6227EEA86122EBAD6421E8AE6760A9EF2663AAEC2566AFE92065ACEA236CA5E32A6FA6E0296AA3E52C69A0E62F78B1F73E7BB2F43D7EB7F1387DB4F23B74BDFB3277BEF83172BBFD3471B8FE375099DF16539ADC15569FD910559CDA135C95D31A5F96D0195A93D51C5990D61F4881C70E4B82C40D4E87C1084D84C20B448DCB02478EC801428BCD044188CE07'
    ,   '00CA89430FC5864C1ED4975D11DB98523CF6B57F33F9BA7022E8AB612DE7A46E78B2F13B77BDFE3466ACEF2569A3E02A448ECD074B81C2085A90D319559FDC16F03A79B3FF3576BCEE2467ADE12B68A2CC06458FC3094A80D2185B91DD17549E884201CB874D0EC4965C1FD5995310DAB47E3DF7BB7132F8AA6023E9A56F2CE6FD3774BEF2387BB1E3296AA0EC2665AFC10B4882CE04478DDF15569CD01A5993854F0CC68A4003C99B5112D8945E1DD7B97330FAB67C3FF5A76D2EE4A86221EB0DC7844E02C88B4113D99A501CD6955F31FBB8723EF4B77D2FE5A66C20EAA96375BFFC367AB0F3396BA1E22864AEED274983C00A468CCF05579DDE145892D11B'
    ,   '00CB8B400BC0804B16DD9D561DD6965D2CE7A76C27ECAC673AF1B17A31FABA715893D3185398D8134E85C50E458ECE0574BFFF347FB4F43F62A9E92269A2E229B07B3BF0BB7030FBA66D2DE6AD6626ED9C5717DC975C1CD78A4101CA814A0AC1E82363A8E32868A3FE3575BEF53E7EB5C40F4F84CF04448FD2195992D91252997DB6F63D76BDFD366BA0E02B60ABEB20519ADA115A91D11A478CCC074C87C70C25EEAE652EE5A56E33F8B87338F3B37809C2824902C989421FD4945F14DF9F54CD06468DC60D4D86DB10509BD01B5B90E12A6AA1EA2161AAF73C7CB7FC3777BC955E1ED59E5515DE834808C3884303C8B97232F9B27939F2AF6424EFA46F2FE4'
    ,   '00CC854917DB925E2EE2AB6739F5BC705C90D9154B87CE0272BEF73B65A9E02CB8743DF1AF632AE6965A13DF814D04C8E42861ADF33F76BACA064F83DD1158946DA1E8247AB6FF33438FC60A5498D11D31FDB47826EAA36F1FD39A5608C48D41D519509CC20E478BFB377EB2EC2069A589450CC09E521BD7A76B22EEB07C35F9DA165F93CD014884F43871BDE32F66AA864A03CF915D14D8A8642DE1BF733AF662AEE72B75B9F03C4C80C9055B97DE123EF2BB7729E5AC6010DC955907CB824EB77B32FEA06C25E999551CD08E420BC7EB276EA2FC3079B5C509408CD21E579B0FC38A4618D49D5121EDA46836FAB37F539FD61A4488C10D7DB1F8346AA6EF23'
    ,   '00CD874A13DE945926EBA16C35F8B27F4C81CB065F92D8156AA7ED2079B4FE3398551FD28B460CC1BE7339F4AD602AE7D419539EC70A408DF23F75B8E12C66AB2DE0AA673EF3B9740BC68C4118D59F5261ACE62B72BFF538478AC00D5499D31EB57832FFA66B21EC935E14D9804D07CAF9347EB3EA276DA0DF125895CC014B865A97DD104984CE037CB1FB366FA2E82516DB915C05C8824F30FDB77A23EEA469C20F4588D11C569BE42963AEF73A70BD8E4309C49D501AD7A8652FE2BB763CF177BAF03D64A9E32E519CD61B428FC5083BF6BC7128E5AF621DD09A570EC38944EF2268A5FC317BB6C9044E83DA175D90A36E24E9B07D37FA854802CF965B11DC'
    ,   '00CE814F1FD19E503EF0BF7121EFA06E7CB2FD3363ADE22C428CC30D5D93DC12F83679B7E72966A8C6084789D9175896844A05CB9B551AD4BA743BF5A56B24EAED236CA2F23C73BDD31D529CCC024D83915F10DE8E400FC1AF612EE0B07E31FF15DB945A0AC48B452BE5AA6434FAB57B69A7E82676B8F7395799D6184886C907C7094688D8165997F93778B6E62867A9BB753AF4A46A25EB854B04CA9A541BD53FF1BE7020EEA16F01CF804E1ED09F51438DC20C5C92DD137DB3FC3262ACE32D2AE4AB6535FBB47A14DA955B0BC58A445698D7194987C80668A6E92777B9F638D21C539DCD034C82EC226DA3F33D72BCAE602FE1B17F30FE905E11DF8F410EC0'
    ,   '00CF834C1BD4985736F9B57A2DE2AE616CA3EF2077B8F43B5A95D916418EC20DD8175B94C30C408FEE216DA2F53A76B9B47B37F8AF602CE3824D01CE99561AD5AD622EE1B67935FA9B5418D7804F03CCC10E428DDA155996F73874BBEC236FA075BAF6396EA1ED22438CC00F5897DB1419D69A5502CD814E2FE0AC6334FBB7784788C40B5C93DF1071BEF23D6AA5E9262BE4A86730FFB37C1DD29E5106C9854A9F501CD3844B07C8A9662AE5B27D31FEF33C70BFE8276BA4C50A4689DE115D92EA2569A6F13E72BDDC135F90C708448B864905CA9D521ED1B07F33FCAB6428E732FDB17E29E6AA6504CB87481FD09C535E91DD12458AC60968A7EB2473BCF03F'
    ,   '00D0BD6D67B7DA0ACE1E73A3A97914C481513CECE6365B8B4F9FF22228F895451FCFA27278A8C515D1016CBCB6660BDB9E4E23F3F92944945080ED3D37E78A5A3EEE83535989E434F0204D9D97472AFABF6F02D2D80865B571A1CC1C16C6AB7B21F19C4C4696FB2BEF3F5282885835E5A0701DCDC7177AAA6EBED30309D9B4647CACC1111BCBA676B2620FDFD50568B8FD2D40909A4A27F733E38E5E5484E93963B3DE0E04D4B969AD7D10C0CA1A77A7E2325F8F855538E82CFC91414B9BF6264292FF2F25F598488C5C31E1EB3B5686C3137EAEA47419C90DDDB0606ABAD7075D8DE0303AEA875793432EFEF4244999DC0C61B1BB6B06D612C2AF7F75A5C818'
    ,   '00D1BF6E63B2DC0DC61779A8A5741ACB91402EFFF2234D9C5786E83934E58B5A3FEE80515C8DE332F92846979A4B25F4AE7F11C0CD1C72A368B9D7060BDAB4657EAFC1101DCCA273B86907D6DB0A64B5EF3E50818C5D33E229F896474A9BF5244190FE2F22F39D4C875638E9E4355B8AD0016FBEB3620CDD16C7A97875A4CA1BFC2D43929F4E20F13AEB85545988E6376DBCD2030EDFB160AB7A14C5C81977A6C3127CADA0711FCE05D4BA6B66B7D9085283ED3C31E08E5F94452BFAF726489982533DECE1305E8F4495FB2A27F6984913C2AC7D70A1CF1ED5046ABBB66709D8BD6C02D3DE0F61B07BAAC41518C9A7762CFD93424F9EF021EA3B5584895836E7'
    ,   '00D2B96B6FBDD604DE0C67B5B16308DAA17318CACE1C77A57FADC61410C2A97B5F8DE63430E2895B815338EAEE3C5785FE2C4795914328FA20F2994B4F9DF624BE6C07D5D10368BA60B2D90B0FDDB6641FCDA67470A2C91BC11378AAAE7C17C5E133588A8E5C37E53FED86545082E93B4092F92B2FFD96449E4C27F5F123489A61B3D80A0EDCB765BF6D06D4D00269BBC01279ABAF7D16C41ECCA77571A3C81A3EEC87555183E83AE032598B8F5D36E49F4D26F4F022499B4193F82A2EFC9745DF0D66B4B06209DB01D3B86A6EBCD7057EACC71511C3A87AA07219CBCF1D76A4805239EBEF3D56845E8CE73531E3885A21F3984A4E9CF725FF2D4694904229FB'
    ,   '00D3BB686BB8D003D6056DBEBD6E06D5B1620AD9DA0961B267B4DC0F0CDFB7647FACC41714C7AF7CA97A12C1C21179AACE1D75A6A5761ECD18CBA37073A0C81BFE2D459695462EFD28FB93404390F82B4F9CF42724F79F4C994A22F1F221499A81523AE9EA3951825784EC3F3CEF875430E38B585B88E033E6355D8E8D5E36E5E1325A898A5931E237E48C5F5C8FE7345083EB383BE8805386553DEEED3E56859E4D25F6F5264E9D489BF32023F0984B2FFC94474497FF2CF92A4291924129FA1FCCA47774A7CF1CC91A72A1A27119CAAE7D15C6C5167EAD78ABC31013C0A87B60B3DB080BD8B063B6650DDEDD0E66B5D1026AB9BA6901D207D4BC6F6CBFD704'
    ,   '00D4B56177A3C216EE3A5B8F994D2CF8C11574A0B66203D72FFB9A4E588CED399F4B2AFEE83C5D8971A5C41006D2B3675E8AEB3F29FD9C48B06405D1C71372A623F796425480E135CD1978ACBA6E0FDBE2365783954120F40CD8B96D7BAFCE1ABC6809DDCB1F7EAA5286E73325F190447DA9C81C0ADEBF6B934726F2E43051854692F32731E58450A87C1DC9DF0B6ABE875332E6F024459169BDDC081ECAAB7FD90D6CB8AE7A1BCF37E382564094F52118CCAD796FBBDA0EF6224397815534E065B1D00412C6A7738B5F3EEAFC28499DA47011C5D30766B24A9EFF2B3DE9885CFA2E4F9B8D5938EC14C0A17563B7D6023BEF8E5A4C98F92DD50160B4A27617C3'
    ,   '00D5B76273A6C411E6335184954022F7D10466B3A27715C037E280554491F326BF6A08DDCC197BAE598CEE3B2AFF9D486EBBD90C1DC8AA7F885D3FEAFB2E4C9963B6D40110C5A772855032E7F6234194B26705D0C11476A35481E33627F29045DC096BBEAF7A18CD3AEF8D58499CFE2B0DD8BA6F7EABC91CEB3E5C89984D2FFAC61371A4B56002D720F597425386E43117C2A07564B1D306F1244693825735E079ACCE1B0ADFBD689F4A28FDEC395B8EA87D1FCADB0E6CB94E9BF92C3DE88A5FA57012C7D60361B44396F42130E5875274A1C31607D2B065924725F0E13456831ACFAD7869BCDE0BFC294B9E8F5A38EDCB1E7CA9B86D0FDA2DF89A4F5E8BE93C'
    ,   '00D6B1677FA9CE18FE284F99815730E6E13750869E482FF91FC9AE7860B6D107DF096EB8A07611C721F790465E88EF393EE88F594197F026C01671A7BF690ED8A37512C4DC0A6DBB5D8BEC3A22F493454294F3253DEB8C5ABC6A0DDBC31572A47CAACD1B03D5B264825433E5FD2B4C9A9D4B2CFAE234538563B5D2041CCAAD7B5B8DEA3C24F29543A57314C2DA0C6BBDBA6C0BDDC51374A24492F5233BED8A5C845235E3FB2D4A9C7AACCB1D05D3B46265B3D4021ACCAB7D9B4D2AFCE4325583F82E499F875136E006D0B76179AFC81E19CFA87E66B0D701E7315680984E29FF27F19640588EE93FD90F68BEA67017C1C61077A1B96F08DE38EE895F4791F620'
    ,   '00D7B3647BACC81FF62145928D5A3EE9F12642958A5D39EE07D0B4637CABCF18FF284C9B845337E009DEBA6D72A5C1160ED9BD6A75A2C611F82F4B9C835430E7E3345087984F2BFC15C2A6716EB9DD0A12C5A17669BEDA0DE43357809F482CFB1CCBAF7867B0D403EA3D598E914622F5ED3A5E89964125F21BCCA87F60B7D304DB0C68BFA07713C42DFA9E495681E5322AFD994E5186E235DC0B6FB8A77014C324F397405F88EC3BD20561B6A97E1ACDD50266B1AE791DCA23F49047588FEB3C38EF8B5C4394F027CE197DAAB56206D1C91E7AADB26501D63FE88C5B4493F720C71074A3BC6B0FD831E682554A9DF92E36E185524D9AFE29C01773A4BB6C08DF'
    ,   '00D8AD75479FEA328E5623FBC91164BC01D9AC74469EEB338F5722FAC81065BD02DAAF77459DE8308C5421F9CB1366BE03DBAE76449CE9318D5520F8CA1267BF04DCA971439BEE368A5227FFCD1560B805DDA870429AEF378B5326FECC1461B906DEAB734199EC34885025FDCF1762BA07DFAA724098ED35895124FCCE1663BB08D0A57D4F97E23A865E2BF3C1196CB409D1A47C4E96E33B875F2AF2C0186DB50AD2A77F4D95E038845C29F1C31B6EB60BD3A67E4C94E139855D28F0C21A6FB70CD4A1794B93E63E825A2FF7C51D68B00DD5A0784A92E73F835B2EF6C41C69B10ED6A37B4991E43C80582DF5C71F6AB20FD7A27A4890E53D81592CF4C61E6BB3'
    ,   '00D9AF76439AEC35865F29F0C51C6AB311C8BE67528BFD24974E38E1D40D7BA222FB8D5461B8CE17A47D0BD2E73E489133EA9C4570A9DF06B56C1AC3F62F5980449DEB3207DEA871C21B6DB481582EF7558CFA2316CFB960D30A7CA590493FE666BFC91025FC8A53E0394F96A37A0CD577AED80134ED9B42F1285E87B26B1DC4885127FECB1264BD0ED7A1784D94E23B994036EFDA0375AC1FC6B0695C85F32AAA7305DCE930469F2CF5835A6FB6C019BB6214CDF821578E3DE4924B7EA7D108CC1563BA8F5620F94A93E53C09D0A67FDD0472AB9E4731E85B82F42D18C1B76EEE374198AD7402DB68B1C71E2BF2845DFF265089BC6513CA79A0D60F3AE3954C'
    ,   '00DAA9734F95E63C9E4437EDD10B78A221FB88526EB4C71DBF6516CCF02A59834298EB310DD7A47EDC0675AF93493AE063B9CA102CF6855FFD27548EB2681BC1845E2DF7CB1162B81AC0B369558FFC26A57F0CD6EA3043993BE1924874AEDD07C61C6FB5895320FA5882F12B17CDBE64E73D4E94A87201DB79A3D00A36EC9F4515CFBC665A80F3298B5122F8C41E6DB734EE9D477BA1D208AA7003D9E53F4C96578DFE2418C2B16BC91360BA865C2FF576ACDF0539E3904AE832419BA77D0ED4914B38E2DE0477AD0FD5A67C409AE933B06A19C3FF25568C2EF4875D61BBC812D3097AA09C4635EF4D97E43E02D8AB71F2285B81BD6714CE6CB6C51F23F98A50'
    ,   '00DBAB704B90E03B964D3DE6DD0676AD31EA9A417AA1D10AA77C0CD7EC37479C62B9C91229F28259F42F5F84BF6414CF5388F82318C3B368C51E6EB58E5525FEC41F6FB48F5424FF5289F92219C2B269F52E5E85BE6515CE63B8C81328F38358A67D0DD6ED36469D30EB9B407BA0D00B974C3CE7DC0777AC01DAAA714A91E13A954E3EE5DE0575AE03D8A8734893E338A47F0FD4EF34449F32E9994279A2D209F72C5C87BC6717CC61BACA112AF1815AC61D6DB68D5626FD508BFB201BC0B06B518AFA211AC1B16AC71C6CB78C5727FC60BBCB102BF0805BF62D5D86BD6616CD33E8984378A3D308A57E0ED5EE35459E02D9A9724992E239944F3FE4DF0474AF'
    ,   '00DCA579578BF22EAE720BD7F9255C80419DE43816CAB36FEF334A96B8641DC1825E27FBD50970AC2CF089557BA7DE02C31F66BA944831ED6DB1C8143AE69F4319C5BC604E92EB37B76B12CEE03C45995884FD210FD3AA76F62A538FA17D04D89B473EE2CC1069B535E9904C62BEC71BDA067FA38D5128F474A8D10D23FF865A32EE974B65B9C01C9C4039E5CB176EB273AFD60A24F8815DDD0178A48A562FF3B06C15C9E73B429E1EC2BB674995EC30F12D5488A67A03DF5F83FA2608D4AD712BF78E527CA0D905855920FCD20E77AB6AB6CF133DE19844C41861BD934F36EAA9750CD0FE225B8707DBA27E508CF529E8344D91BF631AC6469AE33F11CDB468'
    ,   '00DDA77A538EF429A67B01DCF528528F518CF62B02DFA578F72A508DA47903DEA27F05D8F12C568B04D9A37E578AF02DF32E5489A07D07DA5588F22F06DBA17C5984FE230AD7AD70FF225885AC710BD608D5AF725B86FC21AE7309D4FD205A87FB265C81A8750FD25D80FA270ED3A974AA770DD0F9245E830CD1AB765F82F825B26F15C8E13C469B14C9B36E479AE03DE33E4499B06D17CA4598E23F16CBB16C10CDB76A439EE439B66B11CCE538429F419CE63B12CFB568E73A409DB46913CEEB364C91B8651FC24D90EA371EC3B964BA671DC0E9344E931CC1BB664F92E8354994EE331AC7BD60EF324895BC611BC618C5BF624B96EC31BE6319C4ED304A97'
    ,   '00DEA17F5F81FE20BE601FC1E13F409E61BFC01E3EE09F41DF017EA0805E21FFC21C63BD9D433CE27CA2DD0323FD825CA37D02DCFC225D831DC3BC62429CE33D994738E6C61867B927F9865878A6D907F8265987A77906D84698E73919C7B8665B85FA2404DAA57BE53B449ABA641BC53AE49B4565BBC41A845A25FBDB057AA42FF18E5070AED10F914F30EECE106FB14E90EF3111CFB06EF02E518FAF710ED0ED334C92B26C13CD538DF22C0CD2AD738C522DF3D30D72AC32EC934D6DB3CC12B66817C9E937489608D6A9775789F628D70976A8885629F769B7C81636E8974974AAD50B2BF58A54CA146BB5954B34EA15CBB46A4A94EB35AB750AD4F42A558B'
    ,   '00DFA37C5B84F827B66915CAED324E9171AED20D2AF58956C71864BB9C433FE0E23D419EB9661AC5548BF7280FD0AC73934C30EFC8176BB425FA86597EA1DD02D9067AA5825D21FE6FB0CC1334EB9748A8770BD4F32C508F1EC1BD62459AE6393BE4984760BFC31C8D522EF1D60975AA4A95E93611CEB26DFC235F80A77804DBAF700CD3F42B578819C6BA65429DE13EDE017DA2855A26F968B7CB1433EC904F4D92EE3116C9B56AFB245887A07F03DC3CE39F4067B8C41B8A5529F6D10E72AD76A9D50A2DF28E51C01F63BC9B4438E707D8A47B5C83FF20B16E12CDEA354996944B37E8CF106CB322FD815E79A6DA05E53A4699BE611DC2538CF02F08D7AB74'
    ,   '00E0DD3DA7477A9A53B38E6EF41429C9A6467B9B01E1DC3CF51528C852B28F6F51B18C6CF6162BCB02E2DF3FA5457898F7172ACA50B08D6DA444799903E3DE3EA2427F9F05E5D838F1112CCC56B68B6B04E4D939A3437E9E57B78A6AF0102DCDF3132ECE54B48969A0407D9D07E7DA3A55B58868F2122FCF06E6DB3BA1417C9C59B98464FE1E23C30AEAD737AD4D7090FF1F22C258B88565AC4C71910BEBD63608E8D535AF4F72925BBB8666FC1C21C1AE4E739309E9D434FD1D20C05ABA8767FB1B26C65CBC8161A84875950FEFD2325DBD8060FA1A27C70EEED333A9497494AA4A77970DEDD030F91924C45EBE83630CECD131AB4B76965FBF8262F81825C5'
    ,   '00E1DF3EA3427C9D5BBA8465F81927C6B657698815F4CA2BED0C32D34EAF91707190AE4FD2330DEC2ACBF514896856B7C72618F96485BB5A9C7D43A23FDEE001E2033DDC41A09E7FB95866871AFBC52454B58B6AF71628C90FEED031AC4D739293724CAD30D1EF0EC82917F66B8AB45525C4FA1B866759B87E9FA140DD3C02E3D93806E77A9BA54482635DBC21C0FE1F6F8EB051CC2D13F234D5EB0A977648A9A84977960BEAD435F3122CCD50B18F6E1EFFC120BD5C628345A49A7BE60739D83BDAE405987947A66081BF5EC3221CFD8D6C52B32ECFF110D63709E87594AA4B4AAB9574E90836D711F0CE2FB2536D8CFC1D23C25FBE8061A746789904E5DB3A'
    ,   '00E2D93BAF4D769443A19A78EC0E35D786645FBD29CBF012C5271CFE6A88B35111F3C82ABE5C678552B08B69FD1F24C697754EAC38DAE103D4360DEF7B99A24022C0FB198D6F54B66183B85ACE2C17F5A4467D9F0BE9D230E7053EDC48AA917333D1EA089C7E45A77092A94BDF3D06E4B5576C8E1AF8C321F6142FCD59BB806244A69D7FEB0932D007E5DE3CA84A7193C2201BF96D8FB456816358BA2ECCF71555B78C6EFA1823C116F4CF2DB95B6082D3310AE87C9EA547907249AB3FDDE6046684BF5DC92B10F225C7FC1E8A6853B1E00239DB4FAD9674A3417A980CEED5377795AE4CD83A01E334D6ED0F9B7942A0F11328CA5EBC8765B2506B891DFFC426'
    ,   '00E3DB38AB4870934BA89073E0033BD896754DAE3DDEE605DD3E06E57695AD4E31D2EA099A7941A27A99A142D1320AE9A7447C9F0CEFD734EC0F37D447A49C7F6281B95AC92A12F129CAF211826159BAF4172FCC5FBC8467BF5C648714F7CF2C53B0886BF81B23C018FBC320B350688BC5261EFD6E8DB5568E6D55B625C6FE1DC4271FFC6F8CB4578F6C54B724C7FF1C52B1896AF91A22C119FAC221B251698AF5162ECD5EBD8566BE5D658615F6CE2D6380B85BC82B13F028CBF310836058BBA6457D9E0DEED635ED0E36D546A59D7E30D3EB089B7840A37B98A043D0330BE897744CAF3CDFE704DC3F07E47794AC4F01E2DA39AA4971924AA99172E1023AD9'
    ,   '00E4D531B75362867397A642C42011F5E60233D751B58460957140A422C6F713D13504E06682B357A246779315F1C02437D3E206806455B144A09175F31726C2BF5B6A8E08ECDD39CC2819FD7B9FAE4A59BD8C68EE0A3BDF2ACEFF1B9D7948AC6E8ABB5FD93D0CE81DF9C82CAA4E7F9B886C5DB93FDBEA0EFB1F2ECA4CA8997D6387B652D43001E510F4C521A7437296856150B432D6E703F61223C741A59470B256678305E1D034C12514F07692A34754B08165E30736D227C3F216907445A1DC3809ED6B8FBE5AAF4B7A9E18FCCD293ADEEF0B8D6958BC49AD9C78FE1A2BCF0DE9D83CBA5E6F8B7E9AAB4FC92D1CF8EB0F3EDA5CB8896D987C4DA92FCBFA1E'
    ,   '00E5D732B35664817B9EAC49C82D1FFAF61321C445A092778D685ABF3EDBE90CF11426C342A795708A6F5DB839DCEE0B07E2D035B45163867C99AB4ECF2A18FDFF1A28CD4CA99B7E846153B637D2E00509ECDE3BBA5F6D887297A540C12416F30EEBD93CBD586A8F7590A247C62311F4F81D2FCA4BAE9C79836654B130D5E702E30634D150B58762987D4FAA2BCEFC1915F0C227A64371946E8BB95CDD380AEF12F7C520A1447693698CBE5BDA3F0DE8E40133D657B280659F7A48AD2CC9FB1E1CF9CB2EAF4A789D6782B055D43103E6EA0F3DD859BC8E6B917446A322C7F510ED083ADF5EBB896C967341A425C0F2171BFECC29A84D7F9A6085B752D33604E1'
    ,   '00E6D137BF596E886385B254DC3A0DEBC62017F1799FA84EA54374921AFCCB2D917740A62EC8FF19F21423C54DAB9C7A57B18660E80E39DF34D2E5038B6D5ABC3FD9EE08806651B75CBA8D6BE30532D4F91F28CE46A097719A7C4BAD25C3F412AE487F9911F7C026CD2B1CFA7294A345688EB95FD73106E00BEDDA3CB45265837E98AF49C12710F61DFBCC2AA2447395B85E698F07E1D630DB3D0AEC6482B553EF093ED850B681678C6A5DBB33D5E20429CFF81E967047A14AAC9B7DF51324C241A79076FE182FC922C4F3159D7B4CAA876156B038DEE90FE40235D35BBD8A6CD03601E76F89BE58B35562840CEADD3B16F0C721A94F789E7593A442CA2C1BFD'
    ,   '00E7D334BB5C688F6B8CB85FD03703E4D63105E26D8ABE59BD5A6E8906E1D532B15662850AEDD93EDA3D09EE6186B2556780B453DC3B0FE80CEBDF38B75064837F98AC4BC42317F014F3C720AF487C9BA94E7A9D12F5C126C22511F6799EAA4DCE291DFA7592A641A54276911EF9CD2A18FFCB2CA34470977394A047C82F1BFCFE192DCA45A29671957246A12EC9FD1A28CFFB1C937440A743A49077F81F2BCC4FA89C7BF41327C024C3F7109F784CAB997E4AAD22C5F116F21521C649AE9A7D816652B53ADDE90EEA0D39DE51B6826557B08463EC0B3FD83CDBEF08876054B330D7E3048B6C58BF5BBC886FE00733D4E60135D25DBA8E698D6A5EB936D1E502'
    ,   '00E8CD25876F4AA213FBDE36947C59B126CEEB03A1496C8435DDF810B25A7F974CA48169CB2306EE5FB7927AD83015FD6A82A74FED0520C87991B45CFE1633DB987055BD1FF7D23A8B6346AE0CE4C129BE56739B39D1F41CAD4560882AC2E70FD43C19F153BB9E76C72F0AE240A88D65F21A3FD7759DB850E1092CC4668EAB432DC5E008AA42678F3ED6F31BB951749C0BE3C62E8C6441A918F0D53D9F7752BA6189AC44E60E2BC3729ABF57F51D38D047AF8A62C0280DE554BC9971D33B1EF6B55D789032DAFF17A64E6B8321C9EC04937B5EB614FCD93180684DA507EFCA22F91134DC7E96B35BEA0227CF6D85A048DF3712FA58B0957DCC2401E94BA3866E'
    ,   '00E9CF26836A4CA51BF2D43D987157BE36DFF910B55C7A932DC4E20BAE4761886C85A34AEF0620C9779EB851F41D3BD25AB3957CD93016FF41A88E67C22B0DE4D83117FE5BB2947DC32A0CE540A98F66EE0721C86D84A24BF51C3AD3769FB950B45D7B9237DEF811AF4660892CC5E30A826B4DA401E8CE27997056BF1AF3D53CAD44628B2EC7E108B65F799035DCFA139B7254BD18F1D73E80694FA603EACC25C1280EE742AB8D64DA3315FC59B0967FF71E38D1749DBB52EC0523CA6F86A049759CBA53F61F39D06E87A148ED0422CB43AA8C65C0290FE658B1977EDB3214FD19F0D63F9A7355BC02EBCD2481684EA72FC6E009AC45638A34DDFB12B75E7891'
    ,   '00EAC9238F6546AC03E9CA208C6645AF06ECCF25896340AA05EFCC268A6043A90CE6C52F83694AA00FE5C62C806A49A30AE0C329856F4CA609E3C02A866C4FA518F2D13B977D5EB41BF1D238947E5DB71EF4D73D917B58B21DF7D43E92785BB114FEDD379B7152B817FDDE34987251BB12F8DB319D7754BE11FBD8329E7457BD30DAF913BF55769C33D9FA10BC56759F36DCFF15B953709A35DFFC16BA5073993CD6F51FB3597A903FD5F61CB05A79933AD0F319B55F7C9639D3F01AB65C7F9528C2E10BA74D6E842BC1E208A44E6D872EC4E70DA14B68822DC7E40EA2486B8124CEED07AB41628827CDEE04A842618B22C8EB01AD47648E21CBE802AE44678D'
    ,   '00EBCB208B6040AB0BE0C02B806B4BA016FDDD369D7656BD1DF6D63D967D5DB62CC7E70CA74C6C8727CCEC07AC47678C3AD1F11AB15A7A9131DAFA11BA51719A58B39378D33818F353B89873D83313F84EA5856EC52E0EE545AE8E65CE2505EE749FBF54FF1434DF7F94B45FF41F3FD46289A942E90222C96982A249E20929C2B05B7B903BD0F01BBB50709B30DBFB10A64D6D862DC6E60DAD46668D26CDED069C7757BC17FCDC37977C5CB71CF7D73C8A6141AA01EACA21816A4AA10AE1C12AE80323C86388A843E30828C36883A348FE1535DE759EBE55F51E3ED57E95B55EC42F0FE44FA4846FCF2404EF44AF8F64D23919F259B29279D93212F952B99972'
    ,   '00ECC529977B52BE33DFF61AA448618D668AA34FF11D34D855B9907CC22E07EBCC2009E55BB79E72FF133AD66884AD41AA466F833DD1F81499755CB00EE2CB27856940AC12FED73BB65A739F21CDE408E30F26CA7498B15DD03C15F947AB826E49A58C60DE321BF77A96BF53ED0128C42FC3EA06B8547D911CF0D9358B674EA217FBD23E806C45A924C8E10DB35F769A719DB458E60A23CF42AE876BD53910FCDB371EF24CA08965E8042DC17F93BA56BD5178942AC6EF038E624BA719F5DC30927E57BB05E9C02CA14D648836DAF31FF41831DD638FA64AC72B02EE50BC95795EB29B77C9250CE06D81A844FA163FD338D4FD11AF436A860BE7CE229C7059B5'
    ,   '00EDC72A937E54B93BD6FC11A8456F82769BB15CE50822CF4DA08A67DE3319F4EC012BC67F92B855D73A10FD44A9836E9A775DB009E4CE23A14C668B32DFF518C52802EF56BB917CFE1339D46D80AA47B35E749920CDE70A88654FA21BF6DC3129C4EE03BA577D9012FFD538816C46AB5FB29875CC210BE66489A34EF71A30DD977A50BD04E9C32EAC416B863FD2F815E10C26CB729FB558DA371DF049A48E637B96BC51E8052FC240AD876AD33E14F90DE0CA279E7359B436DBF11CA548628F52BF9578C12C06EB6984AE43FA173DD024C9E30EB75A709D1FF2D8358C614BA6BE5379942DC0EA07856842AF16FBD13CC8250FE25BB69C71F31E34D9608DA74A'
    ,   '00EEC12F9F715EB023CDE20CBC527D9346A88769D93718F6658BA44AFA143BD58C624DA313FDD23CAF416E8030DEF11FCA240BE555BB947AE90728C67698B75905EBC42A9A745BB526C8E709B957789643AD826CDC321DF3608EA14FFF113ED0896748A616F8D739AA446B8535DBF41ACF210EE050BE917FEC022DC3739DB25C0AE4CB25957B54BA29C7E806B65877994CA28D63D33D12FC6F81AE40F01E31DF866847A919F7D836A54B648A3AD4FB15C02E01EF5FB19E70E30D22CC7C92BD530FE1CE20907E51BF2CC2ED03B35D729C49A78866D63817F96A84AB45F51B34DA836D42AC1CF2DD33A04E618F3FD1FE10C52B04EA5AB49B75E60827C97997B856'
    ,   '00EFC32C9B7458B72BC4E807B05F739C56B9957ACD220EE17D92BE51E60925CAAC436F8037D8F41B876844AB1CF3DF30FA1539D6618EA24DD13E12FD4AA5896645AA8669DE311DF26E81AD42F51A36D913FCD03F88674BA438D7FB14A34C608FE9062AC5729DB15EC22D01EE59B69A75BF507C9324CBE708947B57B80FE0CC238A6549A611FED23DA14E628D3AD5F916DC331FF047A8846BF71834DB6C83AF4026C9E50ABD527E910DE2CE21967955BA709FB35CEB0428C75BB49877C02F03ECCF200CE354BB9778E40B27C87F90BC5399765AB502EDC12EB25D719E29C6EA05638CA04FF8173BD448A78B64D33C10FF35DAF619AE416D821EF1DD32856A46A9'
    ,   '00F0FD0DE7171AEAD3232EDE34C4C939BB4B46B65CACA151689895658F7F72826B9B96668C7C7181B84845B55FAFA252D0202DDD37C7CA3A03F3FE0EE41419E9D6262BDB31C1CC3C05F5F808E2121FEF6D9D90608A7A7787BE4E43B359A9A454BD4D40B05AAAA7576E9E93638979748406F6FB0BE1111CECD52528D832C2CF3FB1414CBC56A6AB5B62929F6F857578880AFAF707ED1D10E0D92924D43ECEC333DA2A27D73DCDC03009F9F404EE1E13E361919C6C86767B8BB2424FBF55A5A85867979A6A80707D8DB44449B953A3AE5EDC2C21D13BCBC6360FFFF202E81815E50CFCF101EB1B16E6DF2F22D238C8C535B7474ABA50A0AD5D6494996983737E8E'
    ,   '00F1FF0EE3121CEDDB2A24D538C9C736AB5A54A548B9B74670818F7E93626C9D4BBAB445A85957A690616F9E73828C7DE0111FEE03F2FC0D3BCAC435D82927D69667699875848A7B4DBCB243AE5F51A03DCCC233DE2F21D0E61719E805F4FA0BDD2C22D33ECFC13006F7F908E5141AEB7687897895646A9BAD5C52A34EBFB14031C0CE3FD2232DDCEA1B15E409F8F6079A6B65947988867741B0BE4FA2535DAC7A8B857499686697A1505EAF42B3BD4CD1202EDF32C3CD3C0AFBF504E91816E7A75658A944B5BB4A7C8D83729F6E60910CFDF302EF1E10E1D72628D934C5CB3AEC1D13E20FFEF00137C6C839D4252BDA47B6B849A4555BAA9C6D63927F8E8071'
    ,   '00F2F90BEF1D16E4C3313AC82CDED5279B69629074868D7F58AAA153B7454EBC2BD9D220C4363DCFE81A11E307F5FE0CB04249BB5FADA65473818A789C6E659756A4AF5DB94B40B295676C9E7A888371CD3F34C622D0DB290EFCF705E11318EA7D8F847692606B99BE4C47B551A3A85AE6141FED09FBF00225D7DC2ECA3833C1AC5E55A743B1BA486F9D96648072798B37C5CE3CD82A21D3F4060DFF1BE9E21087757E8C689A916344B6BD4FAB5952A01CEEE517F3010AF8DF2D26D430C2C93BFA0803F115E7EC1E39CBC032D6242FDD6193986A8E7C7785A2505BA94DBFB446D12328DA3ECCC73512E0EB19FD0F04F64AB8B341A5575CAE897B708266949F6D'
    ,   '00F3FB08EB1810E3CB3830C320D3DB288B78708360939B6840B3BB48AB5850A30BF8F003E0131BE8C0333BC82BD8D02380737B886B9890634BB8B043A0535BA816E5ED1EFD0E06F5DD2E26D536C5CD3E9D6E669576858D7E56A5AD5EBD4E46B51DEEE615F6050DFED6252DDE3DCEC63596656D9E7D8E86755DAEA655B6454DBE2CDFD724C7343CCFE7141CEF0CFFF704A7545CAF4CBFB7446C9F976487747C8F27D4DC2FCC3F37C4EC1F17E407F4FC0FAC5F57A447B4BC4F67949C6F8C7F77843AC9C132D1222AD9F1020AF91AE9E112B1424AB95AA9A1527A89817291626A9931C2CA39DA2921D2FA0901F211E2EA19BA4941B251A2AA5971828A799A696192'
    ,   '00F4F501F70302F6F30706F204F0F105FB0F0EFA0CF8F90D08FCFD09FF0B0AFEEB1F1EEA1CE8E91D18ECED19EF1B1AEE10E4E511E71312E6E31716E214E0E115CB3F3ECA3CC8C93D38CCCD39CF3B3ACE30C4C531C73332C6C33736C234C0C13520D4D521D72322D6D32726D224D0D125DB2F2EDA2CD8D92D28DCDD29DF2B2ADE8B7F7E8A7C88897D788C8D798F7B7A8E70848571877372868377768274808175609495619763629693676692649091659B6F6E9A6C98996D689C9D699F6B6A9E40B4B541B74342B6B34746B244B0B145BB4F4EBA4CB8B94D48BCBD49BF4B4ABEAB5F5EAA5CA8A95D58ACAD59AF5B5AAE50A4A551A75352A6A35756A254A0A155'
    ,   '00F5F702F30604F1FB0E0CF908FDFF0AEB1E1CE918EDEF1A10E5E712E31614E1CB3E3CC938CDCF3A30C5C732C33634C120D5D722D32624D1DB2E2CD928DDDF2A8B7E7C89788D8F7A708587728376748160959762936664919B6E6C99689D9F6A40B5B742B34644B1BB4E4CB948BDBF4AAB5E5CA958ADAF5A50A5A752A35654A10BFEFC09F80D0FFAF00507F203F6F401E01517E213E6E4111BEEEC19E81D1FEAC03537C233C6C4313BCECC39C83D3FCA2BDEDC29D82D2FDAD02527D223D6D42180757782738684717B8E8C79887D7F8A6B9E9C69986D6F9A90656792639694614BBEBC49B84D4FBAB04547B243B6B441A05557A253A6A4515BAEAC59A85D5FAA'
    ,   '00F6F107FF090EF8E31512E41CEAED1BDB2D2ADC24D2D52338CEC93FC73136C0AB5D5AAC54A2A55348BEB94FB74146B0708681778F797E88936562946C9A9D6B4BBDBA4CB44245B3A85E59AF57A1A650906661976F999E68738582748C7A7D8BE01611E71FE9EE1803F5F204FC0A0DFB3BCDCA3CC43235C3D82E29DF27D1D62096606791699F986E758384728A7C7B8D4DBBBC4AB24443B5AE585FA951A7A0563DCBCC3AC23433C5DE282FD921D7D026E61017E119EFE81E05F3F402FA0C0BFDDD2B2CDA22D4D3253EC8CF39C13730C606F0F701F90F08FEE51314E21AECEB1D76808771897F788E956364926A9C9B6DAD5B5CAA52A4A3554EB8BF49B14740B6'
    ,   '00F7F304FB0C08FFEB1C18EF10E7E314CB3C38CF30C7C33420D7D324DB2C28DF8B7C788F70878374609793649B6C689F40B7B344BB4C48BFAB5C58AF50A7A3540BFCF80FF00703F4E01713E41BECE81FC03733C43BCCC83F2BDCD82FD02723D4807773847B8C887F6B9C986F906763944BBCB84FB04743B4A05753A45BACA85F16E1E512ED1A1EE9FD0A0EF906F1F502DD2A2ED926D1D52236C1C532CD3A3EC99D6A6E9966919562768185728D7A7E8956A1A552AD5A5EA9BD4A4EB946B1B5421DEAEE19E61115E2F60105F20DFAFE09D62125D22DDADE293DCACE39C63135C2966165926D9A9E697D8A8E79867175825DAAAE59A65155A2B64145B24DBABE49'
    ,   '00F8ED15C73F2AD2936B7E8654ACB9413BC3D62EFC0411E9A85045BD6F97827A768E9B63B1495CA4E51D08F022DACF374DB5A0588A72679FDE2633CB19E1F40CEC1401F92BD3C63E7F87926AB84055ADD72F3AC210E8FD0544BCA951837B6E969A62778F5DA5B04809F1E41CCE3623DBA1594CB4669E8B7332CADF27F50D18E0C53D28D002FAEF1756AEBB4391697C84FE0613EB39C1D42C6D958078AA5247BFB34B5EA6748C996120D8CD35E71F0AF28870659D4FB7A25A1BE3F60EDC2431C929D1C43CEE1603FBBA4257AF7D85906812EAFF07D52D38C081796C9446BEAB535FA7B24A9860758DCC3421D90BF3E61E649C8971A35B4EB6F70F1AE230C8DD25'
    ,   '00F9EF16C33A2CD59B62748D58A1B74E2BD2C43DE81107FEB0495FA6738A9C6556AFB940956C7A83CD3422DB0EF7E1187D84926BBE4751A8E61F09F025DCCA33AC5543BA6F96807937CED821F40D1BE2877E689144BDAB521CE5F30ADF2630C9FA0315EC39C0D62F61988E77A25B4DB4D1283EC712EBFD044AB3A55C8970669F45BCAA53867F6990DE2731C81DE4F20B6E978178AD5442BBF50C1AE336CFD92013EAFC05D0293FC68871679E4BB2A45D38C1D72EFB0214EDA35A4CB560998F76E91006FF2AD3C53C728B9D64B1485EA7C23B2DD401F8EE1759A0B64F9A63758CBF4650A97C85936A24DDCB32E71E08F1946D7B8257AEB8410FF6E019CC3523DA'
    ,   '00FAE913CF3526DC83796A904CB6A55F1BE1F208D42E3DC79862718B57ADBE4436CCDF25F90310EAB54F5CA67A8093692DD7C43EE2180BF1AE5447BD619B88726C96857FA3594AB0EF1506FC20DAC933778D9E64B84251ABF40E1DE73BC1D2285AA0B349956F7C86D92330CA16ECFF0541BBA8528E74679DC2382BD10DF7E41ED82231CB17EDFE045BA1B248946E7D87C3392AD00CF6E51F40BAA9538F75669CEE1407FD21DBC8326D97847EA2584BB1F50F1CE63AC0D329768C9F65B94350AAB44E5DA77B81926837CDDE24F80211EBAF5546BC609A89732CD6C53FE3190AF082786B914DB7A45E01FBE812CE3427DD9963708A56ACBF451AE0F309D52F3CC6'
    ,   '00FBEB10CB3020DB8B70609B40BBAB500BF0E01BC03B2BD0807B6B904BB0A05B16EDFD06DD2636CD9D66768D56ADBD461DE6F60DD62D3DC6966D7D865DA6B64D2CD7C73CE71C0CF7A75C4CB76C97877C27DCCC37EC1707FCAC5747BC679C8C773AC1D12AF10A1AE1B14A5AA17A81916A31CADA21FA0111EABA4151AA718A9A6158A3B34893687883D32838C318E3F30853A8B84398637388D82333C813E8F8034EB5A55E857E6E95C53E2ED50EF5E51E45BEAE558E75659ECE3525DE05FEEE15748F9F64BF4454AFFF0414EF34CFDF247F84946FB44F5FA4F40F1FE43FC4D42F62998972A95242B9E91202F922D9C93269928279A25949B2E21909F229D2C239'
    ,   '00FCE519D72B32CEB34F56AA6498817D7B879E62AC5049B5C8342DD11FE3FA06F60A13EF21DDC43845B9A05C926E778B8D7168945AA6BF433EC2DB27E9150CF0F10D14E826DAC33F42BEA75B9569708C8A766F935DA1B84439C5DC20EE120BF707FBE21ED02C35C9B44851AD639F867A7C809965AB574EB2CF332AD618E4FD01FF031AE628D4CD314CB0A9559B677E828478619D53AFB64A37CBD22EE01C05F909F5EC10DE223BC7BA465FA36D918874728E976BA55940BCC13D24D816EAF30F0EF2EB17D9253CC0BD4158A46A968F737589906CA25E47BBC63A23DF11EDF408F8041DE12FD3CA364BB7AE529C607985837F669A54A8B14D30CCD529E71B02FE'
    ,   '00FDE71AD32E34C9BB465CA168958F726B968C71B8455FA2D02D37CA03FEE419D62B31CC05F8E21F6D908A77BE4359A4BD405AA76E93897406FBE11CD52832CFB14C56AB629F85780AF7ED10D9243EC3DA273DC009F4EE13619C867BB24F55A8679A807DB44953AEDC213BC60FF2E8150CF1EB16DF2238C5B74A50AD6499837E7F829865AC514BB6C43923DE17EAF00D14E9F30EC73A20DDAF5248B57C819B66A9544EB37A879D6012EFF508C13C26DBC23F25D811ECF60B79849E63AA574DB0CE3329D41DE0FA077588926FA65B41BCA55842BF768B916C1EE3F904CD302AD718E5FF02CB362CD1A35E44B9708D976A738E9469A05D47BAC8352FD21BE6FC01'
    ,   '00FEE11FDF213EC0A35D42BC7C829D635BA5BA44847A659BF80619E727D9C638B64857A96997887615EBF40ACA342BD5ED130CF232CCD32D4EB0AF51916F708E718F906EAE504FB1D22C33CD0DF3EC122AD4CB35F50B14EA8977689656A8B749C73926D818E6F907649A857BBB455AA49C627D8343BDA25C3FC1DE20E01E01FFE21C03FD3DC3DC2241BFA05E9E607F81B94758A6669887791AE4FB05C53B24DA54AAB54B8B756A94F70916E828D6C9370FF1EE10D02E31CFAC524DB3738D926C936D728C4CB2AD5330CED12FEF110EF0C83629D717E9F6086B958A74B44A55AB25DBC43AFA041BE58678679959A7B8467E809F61A15F40BEDD233CC202FCE31D'
    ,   '00FFE31CDB2438C7AB5448B7708F936C4BB4A857906F738CE01F03FC3BC4D8279669758A4DB2AE513DC2DE21E61905FADD223EC106F9E51A7689956AAD524EB131CED22DEA1509F69A65798641BEA25D7A859966A15E42BDD12E32CD0AF5E916A75844BB7C839F600CF3EF10D72834CBEC130FF037C8D42B47B8A45B9C637F80629D817EB9465AA5C9362AD512EDF10E29D6CA35F20D11EE827D619E59A6BA45F40B17E82FD0CC335FA0BC43847B6798BF405CA3649B877814EBF708CF302CD353ACB04F88776B94F8071BE423DCC03F18E7FB04C33C20DFB34C50AF68978B74C53A26D91EE1FD026E918D72B54A56A98E716D9255AAB64925DAC639FE011DE2'
    ]]

    @classmethod
    def poly_generator_borked(cls, N, K):
        res = bytearray(bytes.fromhex('01000000'))  # unsure why these 3 00s are needed...
        poly = itertools.product(*map(range, [K, N]))
        for index in itertools.starmap(operator.mul, poly):
            res.append(cls.gFECExp[index % 0xFF])
        return res
    poly_generator = poly_generator_borked

    @classmethod
    def multiply(cls, A, B, K):
        res = bytearray()
        for i, a in enumerate(A):
            bi, br = divmod(i, K)
            b = B[br * K + bi]
            res.append(cls.gFECMultTable[b][a])
        return res

    @classmethod
    def add(cls, A, B):
        res = bytearray()
        for a, b in zip(A, B):
            res.append(A ^ B)
        return res

    @classmethod
    def vandermonde(cls, bytematrix, K):
        raise NotImplementedError

    @classmethod
    def inverse(cls, bytematrix, K):
        raise NotImplementedError

if __name__ == '__main__':
    import sys, importlib
    import ptypes, protocol.rfc3208, protocol.rfc3208 as rfc3208
    from protocol.rfc3208 import *

    x = pgm_packet().alloc(pgm_tsdu_length=0x10)
    osi.utils.checksum(x.serialize())

    #data = b'' + b"\x00\x50\x56\xa4\x58\xd2\xa0\x36\x9f\x00\xc3\xa9\x08\x00\x45\x00" + b"\x00\xa0\x2c\xea\x40\x00\x3f\x71\x63\xb7\xc0\xa8\x0a\x6f\xc0\xa8" + b"\x1e\x8c\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79" + b"\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75" + b"\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b" + b"\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74" + b"\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66" + b"\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63" + b"\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69" + b"\x74\x79\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79" + b"\x66\x75\x63\x6b\x69\x74\x79\x66\x75\x63\x6b\x69\x74\x79"
    #source = ptypes.setsource(ptypes.prov.bytes(data))
    data = b'' + b"\x00\x50\x56\xa4\x58\xd2\xa0\x36\x9f\x00\xc3\xa9\x08\x00\x45\x00" + b"\x00\x3c\xc8\x71\x40\x00\x3f\x06\xc8\xfe\xc0\xa8\x0a\x6f\xc0\xa8" + b"\x1e\x8c\xa1\x20\xde\xad\xf7\x20\x89\x45\x00\x00\x00\x00\xa0\x02" + b"\x7d\x78\x52\xcc\x00\x00\x02\x04\x05\xb4\x04\x02\x08\x0a\x5a\x0a" + b"\x73\x30\x00\x00\x00\x00\x01\x03\x03\x07"
    source = ptypes.setsource(ptypes.prov.bytes(data))
    data = b'' + b"\x00\x50\x56\xa4\x58\xd2\xa0\x36\x9f\x00\xc3\xa9\x08\x00\x45\x00" + b"\x00\x28\x68\xbc\x40\x00\x3f\x06\x28\xc8\xc0\xa8\x0a\x6f\xc0\xa8" + b"\x1e\x8c\xaa\xb2\x0d\x3d\x23\xd3\x9e\xf3\x97\x63\xac\x14\x50\x10" + b"\x00\xfb\x46\x5f\x00\x00\x00\x00\x00\x00\x00\x00"
    source = ptypes.setsource(ptypes.prov.bytes(data))
    data = b'' + b"\x00\x50\x56\xa4\x58\xd2\xa0\x36\x9f\x00\xc3\xa9\x08\x00\x45\x00" + b"\x00\x31\xe4\xf1\x40\x00\x3f\x06\xac\x89\xc0\xa8\x0a\x6f\xc0\xa8" + b"\x1e\x8c\xb0\x5e\x0d\x3d\xcc\xbb\x05\xe1\xcb\x86\x75\x36\x50\x18" + b"\x00\xfb\x0d\x73\x00\x00\x48\x49\x41\x48\x49\x41\x49\x41\x0a"
    source = ptypes.setsource(ptypes.prov.bytes(data))

    import osi, osi.datalink, osi.network, osi.network.inet4
    x = osi.packet()
    x.l
    print(x[0])
    print(x[1])
    print(x[2])
    print(x[3])
    ip4 = x[1]
    print(ip4['ip_sum'])
    ip4['ip_sum'].set(0)
    meh = ip4.serialize()
    print(hex(osi.utils.checksum(meh)))

    ### packet construction
    data = bytes.fromhex('4aff6987000347fe85e0ed4285e0000000000000000000000000000100010000c0a8c1a60004000c8808000200000008')
    sport, dport, gsi = 19199, 27015, 147201099728352
    msg = rfc3208.PGM_SPM().a.set(spm_lead=1, spm_nla_afi=1, spm_nla='192.168.193.166')
    _parity_prm = rfc3208.PGM_OPT_PARITY_PRM().set(8)   #.alloc(parity_prm_tgs=8)
    parity_prm = rfc3208.pgm_opt().alloc(option=_parity_prm).set(flags=dict(SPECIFIC=dict(PROACTIVE=1)))
    exts = [parity_prm]

    pkt = rfc3208.pgm_packet().alloc(
        pgm_sport=sport, pgm_dport=dport, pgm_gsi=gsi,
        msg=msg,
        exts=exts,
        pgm_options=dict(NETWORK=1, PRESENT=1),
        data=b''
    )
    assert(pkt.serialize() == data)

    data = bytes.fromhex('46cc9bff04013f293138313235000007500fc40a500fc3ff0004001481100000500fc408000000000000000a61616161616161')
    sport, dport, gsi = 18124, 39935, 54117413303552
    msg = rfc3208.PGM_ODATA().a.set(data_sqn=0x500FC40A, data_trail=0x500FC3FF)
    frag = rfc3208.PGM_OPT_FRAGMENT().alloc(opt_sqn=0x500FC408, opt_frag_off=0x00000000, opt_frag_len=0x0000000A)
    exts = [frag]

    pkt = rfc3208.pgm_packet().alloc(
        pgm_sport=sport, pgm_dport=dport, pgm_gsi=gsi,
        msg=msg,
        exts=[rfc3208.pgm_opt().alloc(option=ext) for ext in exts],
        data=b'aaaaaaa'
    )
    assert(pkt.serialize() == data)

    data = bytes.fromhex('22cf270f0401eb6c3add80113add00050000000000000000000400088d04000068656c6c6f')
    sport, dport, gsi = 8911, 9999, 64723010796253
    msg = rfc3208.PGM_ODATA().a.set(data_sqn=0x00000000, data_trail=0x00000000)
    syn = rfc3208.PGM_OPT_SYN
    exts = [syn]

    pkt = rfc3208.pgm_packet().alloc(
        pgm_sport=sport, pgm_dport=dport, pgm_gsi=gsi,
        msg=msg,
        exts=[rfc3208.pgm_opt().alloc(option=ext) for ext in exts],
        data=b'hello'
    )
    assert(pkt.serialize() == data)

    data = bytes.fromhex('22cf270f00011e593add80113add0000000000000000000000000000000100000a0208e8000400088f040000')
    sport, dport, gsi = 8911, 9999, 64723010796253
    msg = rfc3208.PGM_SPM().a.set(spm_nla_afi=1, spm_nla='10.2.8.232')
    rst = rfc3208.PGM_OPT_RST
    exts = [rst]

    pkt = rfc3208.pgm_packet().alloc(
        pgm_sport=sport, pgm_dport=dport, pgm_gsi=gsi,
        msg=msg,
        exts=[rfc3208.pgm_opt().alloc(option=ext) for ext in exts],
    )
    assert(pkt.serialize() == data)
