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

class ip4_option_type(ptype.definition):
    cache = {}
    class _enum_(pint.enum, u_char):
        pass
    _default_ = ptype.block

@ip4_option_type.define
class EOOL(ptype.block):
    '''End of Option List'''
    type = 0x00

@ip4_option_type.define
class NOP(ptype.block):
    '''No Operation'''
    type = 0x01

class ip4_option_with_length(pstruct.type):
    def __data(self):
        res = self['length'].li
        size = ip4_option_type.enum.length + res.size()
        return dyn.block(max(0, res.int() - size))

    _fields_ = [
        (u_char, 'length'),
        (__data, 'option'),
    ]

@ip4_option_type.define
class SEC(ip4_option_with_length):
    '''Security (defunct)'''
    type = 0x02

@ip4_option_type.define
class RR(ip4_option_with_length):
    '''Record Route'''
    type = 0x07

@ip4_option_type.define
class ZSU(ip4_option_with_length):
    '''Experimental Measurement'''
    type = 0x0A

@ip4_option_type.define
class MTUP(ip4_option_with_length):
    '''MTU Probe'''
    type = 0x0B

@ip4_option_type.define
class MTUR(ip4_option_with_length):
    '''MTU Reply'''
    type = 0x0C

@ip4_option_type.define
class ENCODE(ip4_option_with_length):
    '''ENCODE'''
    type = 0x0F

@ip4_option_type.define
class QS(ip4_option_with_length):
    '''Quick-Start'''
    type = 0x19

@ip4_option_type.define
class EXP(ip4_option_with_length):
    '''RFC3692-style Experiment'''
    type = 0x1E

@ip4_option_type.define
class TS(ip4_option_with_length):
    '''Time Stamp'''
    type = 0x44

    def __timestamp(self):
        l = self['ipt_len'].li.int()
        return dyn.array(pint.uint32_t, max(0, l - 4))

    _fields_ = [
        #(u_char, 'ipt_code'),
        (u_char, 'ipt_len'),
        (u_char, 'ipt_ptr'),
        (u_char, 'ipt_flg/ipt_oflw'),
        (__timestamp, 'ipt_timestamp'),
    ]

@ip4_option_type.define
class TR(ip4_option_with_length):
    '''Traceroute'''
    type = 0x52

@ip4_option_type.define
class EXP(ip4_option_with_length):
    '''RFC3692-style Experiment'''
    type = 0x5E

@ip4_option_type.define
class SEC(ip4_option_with_length):
    '''Security (RIPSO)'''
    type = 0x82

@ip4_option_type.define
class LSR(ip4_option_with_length):
    '''Loose Source Route'''
    type = 0x83

@ip4_option_type.define
class E_SEC(ip4_option_with_length):
    '''Extended Security (RIPSO)'''
    type = 0x85

@ip4_option_type.define
class CIPSO(ip4_option_with_length):
    '''Commercial IP Security Option'''
    type = 0x86

@ip4_option_type.define
class SID(ip4_option_with_length):
    '''Stream ID'''
    type = 0x88

@ip4_option_type.define
class SSR(ip4_option_with_length):
    '''Strict Source Route'''
    type = 0x89

@ip4_option_type.define
class VISA(ip4_option_with_length):
    '''Experimental Access Control'''
    type = 0x8E

@ip4_option_type.define
class IMITD(ip4_option_with_length):
    '''IMI Traffic Descriptor'''
    type = 0x90

@ip4_option_type.define
class EIP(ip4_option_with_length):
    '''Extended Internet Protocol'''
    type = 0x91

@ip4_option_type.define
class ADDEXT(ip4_option_with_length):
    '''Address Extension'''
    type = 0x93

@ip4_option_type.define
class RTRALT(ip4_option_with_length):
    '''Router Alert'''
    type = 0x94

@ip4_option_type.define
class SDB(ip4_option_with_length):
    '''Selective Directed Broadcast'''
    type = 0x95

@ip4_option_type.define
class DPS(ip4_option_with_length):
    '''Dynamic Packet State'''
    type = 0x97

@ip4_option_type.define
class UMP(ip4_option_with_length):
    '''Upstream Multicast Packet'''
    type = 0x98

@ip4_option_type.define
class EXP(ip4_option_with_length):
    '''RFC3692-style Experiment'''
    type = 0x9E

@ip4_option_type.define
class FINN(ip4_option_with_length):
    '''Experimental Flow Control'''
    type = 0xCD

@ip4_option_type.define
class EXP(ip4_option_with_length):
    '''RFC3692-style Experiment '''
    type = 0xDE

class ip4_opt(pstruct.type):
    def __Length(self):
        res = self['ipo_type'].li
        t = ip4_option_type.lookup(res.int())
        return pint.uint_t if getattr(t, 'no_length', False) else u_char

    def __Value(self):
        res = self['ipo_type'].li
        return ip4_option_type.lookup(res.int())

    _fields_ = [
        (ip4_option_type.enum, 'ipo_type'),
        (__Length, 'ipo_len'),
        (__Value, 'ipo_value'),
    ]

    def alloc(self, **fields):
        res = super(ip4_opt, self).alloc(**fields)
        if 'ipo_len' not in fields:
            res['ipo_len'].set(res.size())
        return res

class ip4_optarray(parray.block):
    _object_ = ip4_opt

class ip4_opts(ptype.encoded_t):
    def _object_(self):
        size = self.size()
        return dyn.clone(ip4_optarray, blocksize = lambda self, sz=size: sz)

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
