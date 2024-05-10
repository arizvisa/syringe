import ptypes
from ptypes import *

from . import layer, stackable, terminal, datalink

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

@datalink.layer.define
class header(pstruct.type, terminal):
    type = 0x0806
    _fields_ = [
        (u_short, 'ar_hrd'),
        (u_short, 'ar_pro'),
        (u_char, 'ar_hln'),
        (u_char, 'ar_pln'),
        (u_short, 'ar_op'),

        (lambda self: dyn.block(self['ar_hln'].li.int()), 'ar_sha'),
        (lambda self: dyn.block(self['ar_pln'].li.int()), 'ar_spa'),

        (lambda self: dyn.block(self['ar_hln'].li.int()), 'ar_tha'),
        (lambda self: dyn.block(self['ar_pln'].li.int()), 'ar_tpa'),
    ]
