import ptypes
from ptypes import *

from . import layer, stackable, terminal, network

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

@network.layer.define
class header(pstruct.type, stackable):
    type = 0x11

    _fields_ = [
        (u_short, 'uh_sport'),  # source port
        (u_short, 'uh_dport'),  # destination port
        (u_short, 'uh_ulen'),   # udp length
        (u_short, 'uh_sum'),    # udp checksum
    ]

    def layer(self):
        layer, id, remaining = super(header, self).layer()
        res, fields = self['uh_ulen'].li, ['uh_sport', 'uh_dport', 'uh_ulen', 'uh_sum']
        length = res.int() if remaining is None else min(remaining, res.int())
        return layer, id, max(0, length - sum(self[fld].li.size() for fld in fields))

    def summary(self):
        res = []
        for field in self:
            res.append("{:s}={:#x}".format(field, self[field]))
        return ' '.join(res)
