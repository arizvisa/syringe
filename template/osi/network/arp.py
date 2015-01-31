from __base__ import layer,datalink,stackable,terminal
from ptypes import *

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

@datalink.liayer.define
class header(pstruct.type,terminal):
    type = 0x0806
    _fields_ = [
        (u_short, 'ar_hrd'),
        (u_short, 'ar_pro'),
        (u_char, 'ar_hln'),
        (u_char, 'ar_pln'),
        (u_short, 'ar_op'),

        (lambda s: dyn.block(s['ar_hln'].li.int()), 'ar_sha'),
        (lambda s: dyn.block(s['ar_pln'].li.int()), 'ar_spa'),

        (lambda s: dyn.block(s['ar_hln'].li.int()), 'ar_tha'),
        (lambda s: dyn.block(s['ar_pln'].li.int()), 'ar_tpa'),
    ]
