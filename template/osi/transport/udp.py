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
        (u_short, 'source port'),
        (u_short, 'dest port'),
        (u_short, 'length'),
        (u_short, 'checksum'),
    ]

    def layer(self):
        layer, id, remaining = super(header, self).layer()
        res, fields = self['length'].li, ['source port', 'dest port', 'length', 'checksum']
        length = res.int() if remaining is None else min(remaining, res.int())
        return layer, id, max(0, length - sum(self[fld].li.size() for fld in fields))
