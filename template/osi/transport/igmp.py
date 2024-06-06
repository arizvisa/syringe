import ptypes, functools
from ptypes import *

from . import layer, stackable, terminal, network

pint.setbyteorder(ptypes.config.byteorder.bigendian)

from ..network import inet4

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass
class in_addr(inet4.in_addr): pass

def checksum(bytes):
    array = bytearray(bytes)
    iterable = map(functools.partial(functools.reduce, lambda agg, item: 0x100 * agg + item), zip(*[iter(array)] * 2))
    shorts = [item for item in iterable]
    seed = sum(shorts)
    shifted, _ = divmod(seed, pow(2, 16))
    checksum = shifted + (seed & 0XFFFF)
    return 0xFFFF & ~checksum

class igmpv2(pstruct.type):
    _fields_ = [
        (in_addr, 'igmp_group'),                # group address being reported (zero for queries)
    ]

class igmp_type(pint.enum, u_char):
    _values_ = [
        ('MEMBERSHIP_QUERY', 0x11),             # membership query
        ('V1_MEMBERSHIP_REPORT', 0x12),         # Ver. 1 membership report
        ('DVMRP', 0x13),                        # DVMRP routing message
        ('PIM', 0x14),                          # PIMv1 message (historic)
        ('V2_MEMBERSHIP_REPORT', 0x16),         # Ver. 2 membership report
        ('HOST_LEAVE_MESSAGE', 0x17),           # Leave-group message
        ('MTRACE_REPLY', 0x1e),                 # mtrace(8) reply
        ('MTRACE_QUERY', 0x1f),                 # mtrace(8) probe
        ('v3_HOST_MEMBERSHIP_REPORT', 0x22),    # Ver. 3 membership report
    ]

class igmpv3_grouprec(pstruct.type):
    def __ig_sources(self):
        res = self['ig_numsrc'].li
        return dyn.array(in_addr, res.int())
    _fields_ = [
        (u_char, 'ig_type'),            # record type
        (u_char, 'ig_datalen'),         # length of auxiliary data
        (u_short, 'ig_numsrc'),         # number of sources
        (in_addr, 'ig_group'),          # group address being reported
        (__ig_sources, 'ig_sources'),   # source addresses
    ]
    def alloc(self, **fields):
        res = super(igmp_grouprec, self).alloc(**fields)
        if 'ig_numsrc' not in fields:
            res['ig_numsrc'].set(len(res['ig_sources']))
        if 'ig_datalen' not in fields:
            pass    # FIXME
        return res

class igmpv3_report_mode(pint.enum):
    _values_ = [
        ('IGMP_DO_NOTHING', 0),                 # don't send a record
        ('IGMP_MODE_IS_INCLUDE', 1),            # MODE_IN
        ('IGMP_MODE_IS_EXCLUDE', 2),            # MODE_EX
        ('IGMP_CHANGE_TO_INCLUDE_MODE', 3),     # TO_IN
        ('IGMP_CHANGE_TO_EXCLUDE_MODE', 4),     # TO_EX
        ('IGMP_ALLOW_NEW_SOURCES', 5),          # ALLOW_NEW
        ('IGMP_BLOCK_OLD_SOURCES', 6),          # BLOCK_OLD
    ]

class igmpv3_report(pstruct.type):
    def __ir_groups(self):
        res = self['ir_numgrps'].li
        return dyn.array(igmp_grouprec, res.int())
    _fields_ = [
        (u_char, 'ir_type'),            # IGMP_v3_HOST_MEMBERSHIP_REPORT
        (u_char, 'ir_rsv1'),            # must be zero
        (u_short, 'ir_cksum'),          # checksum
        (u_short, 'ir_rsv2'),           # must be zero
        (u_short, 'ir_numgrps'),        # number of group records
        (__ir_groups, 'ir_groups'),     # group records
    ]

    def alloc(self, **fields):
        res = super(igmp_report, self).alloc(**fields)
        if 'ir_numgrps' not in fields:
            res['ir_numgrps'].set(len(res['ir_groups']))
        if 'ir_cksum' not in fields:
            data = res.set(ir_cksum=0).serialize()
            res['ir_cksum'].set(checksum(bytearray(data)))
        return res

class IGMP_V3_(pint.enum):
    _fields_ = [
        ('GENERAL_QUERY', 1),
        ('GROUP_QUERY', 2),
        ('GROUP_SOURCE_QUERY', 3),
    ]

class igmpv3_float(pfloat.float_t):
    components = 1, 3, 4

class igmpv3(pstruct.type, stackable):
    class _igmp_misc(pbinary.flags):
        _fields_ = [
            (3, 'QRV'),
            (1, 'S'),
            (4, 'RESV'),
        ]

    def __igmp_sources(self):
        res = self['igmp_numsrc'].li
        return dyn.array(in_addr, res.int())

    _fields_ = [
        (_igmp_misc, 'igmp_misc'),          # reserved/suppress/robustness
        (igmpv3_float, 'igmp_qqi'),         # querier's query interval
        (u_short, 'igmp_numsrc'),           # number of sources
        (__igmp_sources, 'igmp_sources'),   # source addresses
    ]

    def alloc(self, **fields):
        res = super(igmpv3, self).alloc(**fields)
        if 'igmp_numsrc' not in fields:
            res['igmp_numsrc'].set(len(res['igmp_sources']))
        if 'igmp_cksum' not in fields:
            data = res.set(igmp_cksum=0).serialize()
            res['igmp_cksum'].set(checksum(bytearray(data)))
        return res

@network.layer.define
class igmp(pstruct.type, stackable):
    type = 2
    def __igmp_group(self):
        res = self['igmp_type'].li
        return pint.uint_t if res.int() in {0x11, 0x22} else igmpv2
    def __igmp_v3(self):
        res = self['igmp_type'].li
        return igmpv3 if res.int() in {0x11, 0x22} else ptype.undefined
        
    _fields_ = [
        (igmp_type, 'igmp_type'),       # version & type of IGMP message
        (igmpv3_float, 'igmp_code'),    # subtype for routing msgs
        (u_short, 'igmp_cksum'),        # IP-style checksum
        (__igmp_group, 'igmp_group'),   # group address being reported (zero for queries)
        (__igmp_v3, 'igmp_v3'),
    ]
    def seconds(self):
        res = self['igmp_code']
        return res.int() * 0.1

    def alloc(self, **fields):
        res = super(igmp, self).alloc(**fields)
        if 'igmp_cksum' not in fields:
            data = res.set(igmp_cksum=0).serialize()
            res['igmp_cksum'].set(checksum(bytearray(data)))
        return res

if __name__ == '__main__':
    import ptypes, osi.transport.igmp
    from osi.transport.igmp import igmp

    data = bytes.fromhex('2200fa150000000103000000e00000e8')
    x = igmp().load(source=ptypes.prov.bytes(data))
    print(x)
    print(x['igmp_v3'])

    data = bytes.fromhex('2200eefb0000000104000000ea010101')
    x = igmp().load(source=ptypes.prov.bytes(data))
    print(x)
    print(x['igmp_v3'])
