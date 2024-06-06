import ptypes
from ptypes import *

from . import layer, stackable, terminal, network

pint.setbyteorder(ptypes.config.byteorder.bigendian)

from ..network import inet4

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class in_addr(pint.enum, inet4.in_addr):
    _values_ = [
        ('ALL-SYSTEMS', 0xE0000001),
        ('ALL-ROUTERS', 0xE0000002),
    ]
    def set(self, integer):
        if isinstance(integer, str) and self.has(integer):
            return self.__setvalue__(integer)
        return super(pint.enum, self).set(integer)

class IGMP_(pint.enum, u_char):
    _values_ = [
        ('MEMBERSHIP_QUERY', 0x11),         # membership query
        ('V1_MEMBERSHIP_REPORT', 0x12),     # Ver. 1 membership report
        ('V2_MEMBERSHIP_REPORT', 0x16),     # Ver. 2 membership report
        ('V2_LEAVE_GROUP', 0x17),           # Leave-group message
        ('DVMRP', 0x13),                    # DVMRP routing message
        ('PIM', 0x14),                      # PIM routing message
        ('MTRACE_RESP', 0x1e),              # traceroute resp.(to sender)
        ('MTRACE', 0x1f),                   # mcast traceroute messages
    ]

@network.layer.define
class igmp(pstruct.type, stackable):
    type = 2
    _fields_ = [
        (IGMP_, 'igmp_type'),       # version & type of IGMP message
        (u_char, 'igmp_code'),      # subtype for routing msgs
        (u_short, 'igmp_cksum'),    # IP-style checksum
        (in_addr, 'igmp_group'),    # group address being reported (zero for queries)
    ]
    def seconds(self):
        res = self['igmp_code']
        return res.int() * 0.1
    def layer(self):
        layer, id, remaining = super(header, self).layer()
        res = self['length'].li
        return layer, id, max(0, res.int() - sum(self[fld].li.size() for fld in ['source port', 'dest port', 'length', 'checksum']))
