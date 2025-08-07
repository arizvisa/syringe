import ptypes, builtins, logging
from ptypes import *

import ptypes.bitmap as bitmap
from . import layer, stackable, terminal, datalink
from . import utils, address

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass
in_addr = address.in4_addr

class IPOPT_(pint.enum, u_char):
    _values_ = [
        ('EOOL', 0),            # End of Options List [RFC791]
        ('NOP', 1),             # No Operation [RFC791]
        ('SEC', 130),           # Security [RFC1108]
        ('LSR', 131),           # Loose Source Route [RFC791]
        ('TS', 68),             # Time Stamp [RFC791]
        ('E-SEC', 133),         # Extended Security [RFC1108]
        ('CIPSO', 134),         # Commercial Security [draft-ietf-cipso-ipsecurity-01]
        ('RR', 7),              # Record Route [RFC791]
        ('SID', 136),           # Stream ID [RFC791][RFC6814]
        ('SSR', 137),           # Strict Source Route [RFC791]
        ('ZSU', 10),            # Experimental Measurement
        ('MTUP', 11),           # MTU Probe [RFC1063][RFC1191]
        ('MTUR', 12),           # MTU Reply [RFC1063][RFC1191]
        ('FINN', 205),          # Experimental Flow Control
        ('VISA', 142),          # Experimental Access Control [RFC6814]
        ('ENCODE', 15),         # ??? [RFC6814]
        ('IMITD', 144),         # IMI Traffic Descriptor
        ('EIP', 145),           # Extended Internet Protocol [RFC1385][RFC6814]
        ('TR', 82),             # Traceroute [RFC1393][RFC6814]
        ('ADDEXT', 147),        # Address Extension [RFC6814]
        ('RTRALT', 148),        # Router Alert [RFC2113]
        ('SDB', 149),           # Selective Directed Broadcast [RFC6814]
        ('DPS', 151),           # Dynamic Packet State [RFC6814]
        ('UMP', 152),           # Upstream Multicast Pkt. [RFC6814]
    ]

class IP4_OPT_UNPACKED:
    _values_ = [
        ('EOOL', (0,0,0)),          # End of Options List [RFC791]
        ('NOP', (0,0,1)),           # No Operation [RFC791]
        ('SEC', (1,0,2)),           # Security [RFC1108]
        ('LSR', (1,0,3)),           # Loose Source Route [RFC791]
        ('TS', (0,2,4)),            # Time Stamp [RFC791]
        ('E-SEC', (1,0,5)),         # Extended Security [RFC1108]
        ('CIPSO', (1,0,6)),         # Commercial Security [draft-ietf-cipso-ipsecurity-01]
        ('RR', (0,0,7)),            # Record Route [RFC791]
        ('SID', (1,0,8)),           # Stream ID [RFC791][RFC6814]
        ('SSR', (1,0,9)),           # Strict Source Route [RFC791]
        ('ZSU', (0,0,10)),          # Experimental Measurement
        ('MTUP', (0,0,11)),         # MTU Probe [RFC1063][RFC1191]
        ('MTUR', (0,0,12)),         # MTU Reply [RFC1063][RFC1191]
        ('FINN', (1,2,13)),         # Experimental Flow Control
        ('VISA', (1,0,14)),         # Experimental Access Control [RFC6814]
        ('ENCODE', (0,0,15)),       # ??? [RFC6814]
        ('IMITD', (1,0,16)),        # IMI Traffic Descriptor
        ('EIP', (1,0,17)),          # Extended Internet Protocol [RFC1385][RFC6814]
        ('TR', (0,2,18)),           # Traceroute [RFC1393][RFC6814]
        ('ADDEXT', (1,0,19)),       # Address Extension [RFC6814]
        ('RTRALT', (1,0,20)),       # Router Alert [RFC2113]
        ('SDB', (1,0,21)),          # Selective Directed Broadcast [RFC6814]
        ('DPS', (1,0,23)),          # Dynamic Packet State [RFC6814]
        ('UMP', (1,0,24)),          # Upstream Multicast Pkt. [RFC6814]
    ]

class ip4_option(ptype.definition):
    cache = {}
    default = ptype.block
    class _object_(pbinary.flags):
        _fields_ = [
            (1, 'copied'),
            (2, 'class'),
            (5, 'number'),
        ]

class IP4_OPT(ptype.generic): pass
class IP4_OPT_LENGTH(IP4_OPT): pass

class PointerToRouteData(pstruct.type):
    class _pointer(ptype.opointer_t):
        _value_, _object_ = u_char, in_addr
        def _calculate_(self, byte):
            return self.getoffset() + self.size() + byte

    def __route_data(self):
        res, fields = self['length'].li, ['length', 'pointer']
        used = 1 + sum(self[fld].li.size() for fld in fields)
        available = max(0, res.int() - used)
        count, extra = divmod(available, in_addr.length)
        return dyn.array(in_addr, count)

    def __padding(self):
        res, fields = self['length'].li, ['length', 'pointer', 'data']
        used = 1 + sum(self[fld].li.size() for fld in fields)
        missed = max(0, res.int() - used)
        return dyn.block(missed) if missed else ptype.block

    _fields_ = [
        (u_char, 'length'),
        (_pointer, 'pointer'),
        (__route_data, 'data'),
        (__padding, 'padding'),
    ]

    def alloc(self, **fields):
        res = super(PointerToRouteData, self).alloc(**fields)
        if 'length' not in fields:
            res['length'].set(1 + res.size())
        return res

@ip4_option.define
class EOOL(ptype.block, IP4_OPT):
    '''End of Option List'''
    type = 0x00

@ip4_option.define
class NOP(ptype.block, IP4_OPT):
    '''No Operation'''
    type = 0x01

@ip4_option.define
class SEC(pstruct.type, IP4_OPT_LENGTH):
    '''Security (defunct)'''
    type = IPOPT_.byname('SEC')
    _fields_ = [
        (u_short, 'S'),                             # Security
        (u_short, 'C'),                             # Compartments
        (u_short, 'H'),                             # Handling Restrictions
        (dyn.clone(pint.uint_t, length=3), 'TCC'),  # Transmission Control Code
    ]

@ip4_option.define
class SSRR(PointerToRouteData, IP4_OPT):
    '''Strict Source and Record Route'''
    type = IPOPT_.byname('SSR')

@ip4_option.define
class RR(PointerToRouteData, IP4_OPT):
    '''Record Route'''
    type = IPOPT_.byname('RR')

@ip4_option.define
class ZSU(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Measurement'''
    type = 0x0A

@ip4_option.define
class MTUP(u_short, IP4_OPT_LENGTH):
    '''MTU Probe'''
    type = IPOPT_.byname('MTUP')

@ip4_option.define
class MTUR(u_short, IP4_OPT_LENGTH):
    '''MTU Reply'''
    type = IPOPT_.byname('MTUR')

@ip4_option.define
class ENCODE(ptype.block, IP4_OPT_LENGTH):
    '''ENCODE'''
    type = 0x0F

@ip4_option.define
class QS(ptype.block, IP4_OPT_LENGTH):
    '''Quick-Start'''
    type = 0x19

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x1E

@ip4_option.define
class TS(pstruct.type, IP4_OPT_LENGTH):
    '''Time Stamp'''
    type = 0x44

    def __timestamp(self):
        l = self['ipt_len'].li.int()
        return dyn.array(pint.uint32_t, max(0, l - 4))

    _fields_ = [
        #(u_char, 'ipt_code'),
        #(u_char, 'ipt_len'),
        (u_char, 'ipt_ptr'),
        (u_char, 'ipt_flg/ipt_oflw'),
        (__timestamp, 'ipt_timestamp'),
    ]

@ip4_option.define
class TR(pstruct.type, IP4_OPT_LENGTH):
    '''Traceroute'''
    type = IPOPT_.byname('TR')
    _fields_ = [
        (u_short, 'ID'),
        (u_short, 'OHC'),
        (u_short, 'RHC'),
        (in_addr, 'Originator'),
    ]

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x5E

@ip4_option.define
class LSR(PointerToRouteData, IP4_OPT_LENGTH):
    '''Loose Source Route'''
    type = IPOPT_.byname('LSR')

@ip4_option.define
class E_SEC(ptype.block, IP4_OPT_LENGTH):
    '''Extended Security (RIPSO)'''
    type = 0x85

@ip4_option.define
class CIPSO(ptype.block, IP4_OPT_LENGTH):
    '''Commercial IP Security Option'''
    type = 0x86

@ip4_option.define
class SID(u_short, IP4_OPT_LENGTH):
    '''Stream ID'''
    type = 0x88

@ip4_option.define
class VISA(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Access Control'''
    type = 0x8E

@ip4_option.define
class IMITD(ptype.block, IP4_OPT_LENGTH):
    '''IMI Traffic Descriptor'''
    type = 0x90

@ip4_option.define
class EIP(ptype.block, IP4_OPT_LENGTH):
    '''Extended Internet Protocol'''
    type = IPOPT_.byname('EIP')

@ip4_option.define
class ADDEXT(ptype.block, IP4_OPT_LENGTH):
    '''Address Extension'''
    type = 0x93

@ip4_option.define
class SDB(ptype.block, IP4_OPT_LENGTH):
    '''Selective Directed Broadcast'''
    type = 0x95

@ip4_option.define
class DPS(ptype.block, IP4_OPT_LENGTH):
    '''Dynamic Packet State'''
    type = 0x97

@ip4_option.define
class UMP(ptype.block, IP4_OPT_LENGTH):
    '''Upstream Multicast Packet'''
    type = 0x98

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x9E

@ip4_option.define
class FINN(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Flow Control'''
    type = 0xCD

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment '''
    type = 0xDE

@ip4_option.define
class RA(pint.enum, u_short, IP4_OPT_LENGTH):
    '''Router Alert'''
    type = IPOPT_.byname('RTRALT')
    _values_ = [
        ('ALERT', 0),
    ]

class ip4_opt(pstruct.type):
    def __Length(self):
        opt = self['ipo_type'].li
        res = ip4_option.lookup(opt.int())
        return u_char if issubclass(res, IP4_OPT_LENGTH) else pint.uint_t

    def __Value(self):
        opt = self['ipo_type'].li
        return ip4_option.lookup(opt.int())

    def __Missed(self):
        res, fields = self['ipo_len'].li, ['ipo_type', 'ipo_len', 'ipo_value']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (IPOPT_, 'ipo_type'),
        (__Length, 'ipo_len'),
        (__Value, 'ipo_value'),
        (__Missed, 'ip_missed'),
    ]

    def alloc(self, **fields):
        res = super(ip4_opt, self).alloc(**fields)
        if 'ipo_len' not in fields:
            res['ipo_len'].set(sum(res[fld].size() for fld in res))
        if 'ipo_type' not in fields and hasattr(res['ipo_value'], 'type'):
            res['ipo_type'].set(res['ipo_value'].type)
        return res

class ip4_options(parray.block):
    _object_ = ip4_opt
    def isTerminator(self, option):
        return option['ipo_type']['EOOL']
    def alloc(self, *values, **attributes):
        if not values:
            return super(ip4_options, self).alloc(*values, **attributes)
        res, [items] = [], values
        for item in items:
            if ptype.isinstance(item) and isinstance(item, IP4_OPT):
                res.append(self._object_().alloc(ipo_value=item))

            elif ptype.istype(item) and issubclass(item, IP4_OPT):
                res.append(self._object_().alloc(ipo_value=item))

            elif isinstance(item, (int, str)):
                res.append(self._object_().alloc(ipo_type=item))

            else:
                res.append(item)
            continue
        return super(ip4_options, self).alloc(res, **attributes)

class ip4_opts(ptype.encoded_t):
    def _object_(self):
        size = self.size()
        return dyn.clone(ip4_options, blocksize = lambda self, sz=size: sz)

@layer.define(type=4)   # protocol number
@datalink.layer.define
class ip4_hdr(pstruct.type, stackable):
    type = 0x0800

    class _ip_h(pbinary.struct):
        _fields_ = [(4,'ver'),(4,'hlen')]

    class _ip_tos(pbinary.struct):
        class _ecn(pbinary.enum):
            length, _values_ = 2, [
                ('NotECT',  0b00),
                ('ECT0',    0b01),
                ('ECT1',    0b10),
                ('CE',      0b11),
            ]

        _fields_ = [
            (6, 'dscp'),
            (_ecn, 'ecn'),
        ]

    class _ip_fragoff(pbinary.flags):
        _fields_ = [
            (1, 'reserved'),
            (1, 'donotfragment'),
            (1, 'morefragments'),
            (13, 'offset')
        ]

    def __ip4_opts(self):
        res, fields = self['ip_h'].li, ['ip_h', 'ip_tos', 'ip_len', 'ip_id', 'ip_fragoff', 'ip_ttl', 'ip_protocol', 'ip_sum', 'ip_src', 'ip_dst']
        size = sum(self[fld].li.size() for fld in fields)
        optsize = max(0, 4 * res['hlen'] - size)
        backing = dyn.block(optsize)
        return dyn.clone(ip4_opts, _value_=backing)

    def __ip_protocol(self):
        from .. import transport
        # FIXME: these enumerations could be better organized.
        class ip_protocol(transport.layer.enum, u_char):
            pass
        return ip_protocol

    _fields_ = [
#        (u_char, 'ip_h'),
        (_ip_h, 'ip_h'),
        (_ip_tos, 'ip_tos'),
        (u_short, 'ip_len'),
        (u_short, 'ip_id'),
        (_ip_fragoff, 'ip_fragoff'),
        (u_char, 'ip_ttl'),
        #(u_char, 'ip_protocol'),
        (__ip_protocol, 'ip_protocol'),
        (u_short, 'ip_sum'),

        (in_addr, 'ip_src'),
        (in_addr, 'ip_dst'),

        (__ip4_opts, 'ip_opt'),
        (dyn.padding(4), 'padding(ip_opt)'),
    ]

    def checksum(self):
        instance = self.copy().set(ip_sum=0)
        return utils.checksum(instance.serialize())

    def layer(self):
        layer, id, remaining = super(ip4_hdr, self).layer()
        header, fields = self['ip_h'].li, ['ip_h', 'ip_tos', 'ip_len', 'ip_id', 'ip_fragoff', 'ip_ttl', 'ip_protocol', 'ip_sum', 'ip_src', 'ip_dst', 'ip_opt', 'padding(ip_opt)']

        # Check if the header length matches the actual size we decoded.
        if 4 * header['hlen'] == sum(self[fld].li.size() for fld in fields):
            return layer, self['ip_protocol'].li.int(), max(0, self['ip_len'].li.int() - 4 * header['hlen'])

        # Otherwise, log a warning before returning the next layer.
        hlen, optsize = 4 * header['hlen'], sum(self[fld].size() for fld in ['ip_opt', 'padding(ip_opt)'])
        hsize = sum(self[fld].size() for fld in fields) - optsize
        logging.warning("{:s} : Error decoding the IP4 header. The size specified in the header ({:d}) does not match the size ({:d}) of the header with its options ({:d}).".format(self.instance(), hlen, hsize, optsize))
        return layer, self['ip_protocol'].li, max(0, self['ip_len'].li.int() - 4 * header['hlen'])

header = ip4_hdr
