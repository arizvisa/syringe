import ptypes, functools, operator, sys
from ptypes import *

from . import layer, stackable, terminal, network
from . import utils, address

pint.setbyteorder(ptypes.config.byteorder.bigendian)

tohex = operator.methodcaller('encode', 'hex') if sys.version_info.major < 3 else operator.methodcaller('hex')

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass
in_addr = address.in4_addr

def checksum(bytes):
    array = bytearray(bytes)
    iterable = map(functools.partial(functools.reduce, lambda agg, item: 0x100 * agg + item), zip(*[iter(array)] * 2))
    shorts = [item for item in iterable]
    seed = sum(shorts)
    shifted, _ = divmod(seed, pow(2, 16))
    checksum = shifted + (seed & 0XFFFF)
    return 0xFFFF & ~checksum

class igmp_sources(parray.type):
    _object_ = in_addr
    def summary(self):
        return "[{:s}]".format(', '.join(map("{:s}".format, self)))

class igmpv3_float(pfloat.float_t):
    components = 1, 3, 4

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

class v1(in_addr):
    ''' group address being reported (zero for queries) '''

class v2(v1):
    pass

class v3_report_mode(pint.enum, u_char):
    _values_ = [
        ('NOTHING', 0),     # don't send a record
        ('MODE_IN', 1),     # MODE_IS_INCLUDE
        ('MODE_EX', 2),     # MODE_IS_EXCLUDE
        ('TO_IN', 3),       # CHANGE_TO_INCLUDE_MODE
        ('TO_EX', 4),       # CHANGE_TO_EXCLUDE_MODE
        ('ALLOW_NEW', 5),   # ALLOW_NEW_SOURCES
        ('BLOCK_OLD', 6),   # BLOCK_OLD_SOURCES
    ]

class v3_grouprec(pstruct.type):
    def __ig_sources(self):
        res = self['ig_numsrc'].li
        return dyn.clone(igmp_sources, length=res.int())

    def __ig_auxdata(self):
        res = self['ig_datalen'].li
        return dyn.block(4 * res.int()) if res.int() else ptype.block

    def __ig_alignaux(self):
        res, size = self['ig_datalen'].li, self['ig_auxdata'].li.size()
        return dyn.block(max(0, 4 * res.int() - size))

    _fields_ = [
        (v3_report_mode, 'ig_type'),        # record type
        (u_char, 'ig_datalen'),             # length of auxiliary data
        (u_short, 'ig_numsrc'),             # number of sources
        (in_addr, 'ig_group'),              # group address being reported
        (__ig_sources, 'ig_sources'),       # source addresses
        (__ig_auxdata, 'ig_auxdata'),
        (__ig_alignaux, 'ig_alignaux'),
    ]

    def summary(self):
        res = []
        res.append("{:#s}".format(self['ig_type']))
        res.append("{:#A}".format(self['ig_group']))
        res.append("({:d}) {:s}".format(len(self['ig_sources']), self['ig_sources'].summary()))
        if self['ig_auxdata'].size():
            res.append("({:d}) {:s}".format(self['ig_auxdata'].size(), tohex(self['ig_auxdata'].serialize())))
        return ' : '.join(res)

    def alloc(self, **fields):
        res = super(v3_grouprec, self).alloc(**fields)
        if 'ig_numsrc' not in fields:
            res['ig_numsrc'].set(len(res['ig_sources']))
        if 'ig_datalen' not in fields:
            sz = sum(res[fld].size() for fld in ['ig_auxdata', 'ig_alignaux'])
            words, extra = divmod(sz, 4)
            res['ig_datalen'].set(words)
        return res

class v3_group_records(parray.type):
    _object_ = v3_grouprec

    def details(self):
        res = []
        for record in self:
            res.append("{}".format(record))
        return "{:s}\n".format('\n'.join(res))

class v3_report(pstruct.type):
    type = 0x22
    def __ir_groups(self):
        res = self['ir_numgrps'].li
        return dyn.clone(v3_group_records, length=res.int())

    _fields_ = [
        (u_short, 'ir_rsv2'),           # must be zero
        (u_short, 'ir_numgrps'),        # number of group records
        (__ir_groups, 'ir_groups'),     # group records
        (ptype.block, 'ir_endgroups'),  # just a placeholder
    ]

    def alloc(self, **fields):
        fields.setdefault('ir_rsv2', 0)
        res = super(v3_report, self).alloc(**fields)
        if 'ir_numgrps' not in fields:
            res['ir_numgrps'].set(len(res['ir_groups']))
        return res

    def details(self):
        res = ("{}".format(self[fld]) for fld in ['ir_rsv2', 'ir_numgrps', 'ir_groups'])
        return "{:s} ->\n{:s}\n{}\n".format('\n'.join(res), '\n'.join(map("  {:s}".format, self['ir_groups'].details().rstrip().split('\n'))), self['ir_endgroups'])

class IGMP_V3_(pint.enum):
    _fields_ = [
        ('GENERAL_QUERY', 1),
        ('GROUP_QUERY', 2),
        ('GROUP_SOURCE_QUERY', 3),
    ]

class v3_query(pstruct.type, stackable):
    type = 0x11
    class _igmp_misc(pbinary.flags):
        _fields_ = [
            (3, 'QRV'),     # robustness
            (1, 'S'),       # supress
            (4, 'RESV'),    # reserved
        ]

    def __igmp_sources(self):
        res = self['igmp_numsrc'].li
        return dyn.clone(igmp_sources, length=res.int())

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
        return res

@network.layer.define
class igmp(pstruct.type, stackable):
    type = 2
    def __igmp_group(self):
        res, code = (self[fld].li for fld in ['igmp_type', 'igmp_code'])

        # distinguish between v2 and v1
        if self.parent and getattr(self.parent, '_remaining', 12) < 12:
            return v2 if code.int() else v1

        # distinguish between v2 and v3
        if res.int() in {0x11, 0x22}:
            return v3_query if res.int() == 0x11 else v3_report
        return v2

    _fields_ = [
        (igmp_type, 'igmp_type'),       # version & type of IGMP message
        (igmpv3_float, 'igmp_code'),    # subtype for routing msgs
        (u_short, 'igmp_cksum'),        # IP-style checksum
        (__igmp_group, 'igmp_group'),   # igmp_group (v2), ig_sources (v3), or ir_groups (v3)
    ]

    def alloc(self, **fields):
        res = super(igmp, self).alloc(**fields)
        if 'igmp_type' not in fields and hasattr(res['igmp_group'], 'type'):
            res['igmp_type'].set(res['igmp_group'].type)
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
    print(x['igmp_group'])
    print(x['igmp_group']['ir_groups'])
    print(x['igmp_group']['ir_groups'][0].summary())
    print(x['igmp_group']['ir_groups'][0]['ig_group'].set('EIGRP'))
    print("{:#s}".format(x['igmp_group']['ir_groups'][0]['ig_group']))
    print("{:#A}".format(x['igmp_group']['ir_groups'][0]['ig_group']))

    data = bytes.fromhex('2200eefb0000000104000000ea010101')
    x = igmp().load(source=ptypes.prov.bytes(data))
    print(x)
    print(x['igmp_group'])
    print(x['igmp_group']['ir_groups'][0])
    print("{:A}".format(x['igmp_group']['ir_groups'][0]['ig_group'].set('ALL-ROUTERS')))
    print("{:#A}".format(x['igmp_group']['ir_groups'][0]['ig_group'].set('ALL-ROUTERS')))
    print(x)

    groups = []
    groups.append(osi.transport.igmp.v3_grouprec().alloc(ig_type='TO_IN', ig_group='234.1.1.1'))
    x = igmp().alloc(igmp_type='v3_HOST_MEMBERSHIP_REPORT', igmp_group=osi.transport.igmp.v3_report().alloc(ir_groups=groups))
    x['igmp_group']
