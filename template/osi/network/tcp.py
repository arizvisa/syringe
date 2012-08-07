import __base__
from __base__ import layer,stackable

from ptypes import *
class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class tcp_seq(pint.uint32_t): pass

@layer.define
class header(pstruct.type, stackable):
    type = 0x06
    _fields_ = [
        (u_short, 'th_sport'),
        (u_short, 'th_dport'),
        (tcp_seq, 'th_seq'),
        (tcp_seq, 'th_ack'),

        (u_char, 'th_off'),
        (u_char, 'th_flags'),

        (u_short, 'th_win'),
        (u_short, 'th_sum'),
        (u_short, 'th_urp'),
    ]

    def nextlayer_size(self):
        raise NotImplementedError 

