import ptypes, builtins, functools, logging
from ptypes import *

import ptypes.bitmap as bitmap
from . import layer, stackable, terminal, datalink

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class in_addr(pint.enum, u_long):
    _values_ = [
        ('ALL-SYSTEMS', 0xE0000001),
        ('ALL-ROUTERS', 0xE0000002),
        ('DVRMP', 0xE0000004),
        ('ALL-OSPF', 0xE0000005),
        ('ALL-OSPF-DR', 0xE0000006),
        ('ALL-RIPv2', 0xE0000009),
        ('EIGRP', 0xE000000A),
        ('PIM', 0xE000000D),
        ('VRRP', 0xE0000012),
        ('IPAllL1ISs', 0xE0000013),
        ('IPAllL2ISs', 0xE0000014),
        ('IPAllIntermediate', 0xE0000015),
        ('IGMPv3', 0xE0000016),
        ('HSRPv2', 0xE0000066),
        ('MDAP', 0xE0000067),
        ('PTPv2-Peer', 0xE000006B),
        ('AllJoyn', 0xE0000071),
        ('MDNS', 0xE00000FB),
        ('LLMNR', 0xE00000FC),
        ('Teredo-Discovery', 0xE00000FD),
        ('NTP-Client', 0xE0000101),
        ('SLPv1-General', 0xE0000116),
        ('SLPv1-Agent', 0xE0000123),
        ('AUTO-RP-ANNOUNCE', 0xE0000127),
        ('AUTO-RP-DISCOVERY', 0xE0000128),
        ('H.323', 0xE0000129),
        ('PTPv2', 0xE0000181),
        ('SSDP', 0xEFFFFFFA),
        ('SLPv2', 0xEFFFFFFA),
    ]

    def summary(self):
        res = self.int()
        integer = bitmap.new(res, 32)
        octets = bitmap.split(integer, 8)
        if self.has(res):
            return '{:#s}({:#x}) : {:d}.{:d}.{:d}.{:d}'.format(self, *map(bitmap.int, [integer] + octets))
        return '{:#x} : {:d}.{:d}.{:d}.{:d}'.format(*map(bitmap.int, [integer] + octets))

    def set(self, integer):
        if isinstance(integer, str) and self.has(integer):
            return self.__setvalue__(integer)
        elif isinstance(integer, str):
            octets = integer.split('.', 3)
            return self.set([builtins.int(item) for item in integer.split('.')])
        elif isinstance(integer, (tuple, list)):
            octets = bitmap.join([bitmap.new(item, 8) for item in integer])
            integer = bitmap.push(octets, bitmap.new(0, 32 - bitmap.size(octets)))
            return self.set(bitmap.int(integer))
        elif not bitmap.isinteger(integer):
            raise TypeError(integer)
        return super(in_addr, self).set(integer)

    def is_linklocal(self):
        '''169.254/16'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(16) == 0xA9FE0000

    def is_multicast(self):
        '''224/4'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(4) == 0xE0000000

    def is_broadcast(self):
        '''224/4'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(32) == 0xFFFFFFFF

    def is_local(self):
        '''127/8'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(8) == 0x7F000000

    def is_private(self):
        '''10/8 172.16/12 192.168/16'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        address, Fmask = self.int(), Fcidr(8 * self.blocksize())
        return any(address & Fmask(bits) == network for bits, network in [(8, 0x0A00000000), (12, 0xAC100000), (16, 0xC0A80000)])

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

@layer.define
class ip4_hdr(pstruct.type, stackable):
    type = 4

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

    _fields_ = [
#        (u_char, 'ip_h'),
        (_ip_h, 'ip_h'),
        (_ip_tos, 'ip_tos'),
        (u_short, 'ip_len'),
        (u_short, 'ip_id'),
        (_ip_fragoff, 'ip_fragoff'),
        (u_char, 'ip_ttl'),
        (u_char, 'ip_protocol'),
        (u_short, 'ip_sum'),

        (in_addr, 'ip_src'),
        (in_addr, 'ip_dst'),

        (__ip4_opts, 'ip_opt'),
        (dyn.padding(4), 'padding(ip_opt)'),
    ]

    @classmethod
    def _checksum(cls, bytes):
        array = bytearray(bytes)
        iterable = map(functools.partial(functools.reduce, lambda agg, item: 0x100 * agg + item), zip(*[iter(array)] * 2))
        shorts = [item for item in iterable]
        seed = sum(shorts)
        shifted, _ = divmod(seed, pow(2, 16))
        checksum = shifted + (seed & 0XFFFF)
        return 0xFFFF & ~checksum

    def checksum(self):
        bytes = self.copy().set(ip_sum=0).serialize()
        return self._checksum(bytes)

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
        return layer, self['ip_protocol'].li.int(), max(0, self['ip_len'].li.int() - 4 * header['hlen'])

@datalink.layer.define
class datalink_ip4(ip4_hdr):
    type = 0x0800
