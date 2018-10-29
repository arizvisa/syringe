import ptypes
from ptypes import *

from .__base__ import layer, stackable

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class tcp_seq(pint.uint32_t): pass

class flags(pbinary.flags):
    _fields_ = [(1,f) for f in ('URG','ACK','PSH','RST','SYN','FIN')]

@layer.define
class header(pstruct.type, stackable):
    type = 0x06
    class _offset_and_flags(pbinary.struct):
        _fields_ = [
            (4,'th_off'),
            (6,'th_rsvd'),
            (flags, 'th_flags')
        ]
        def summary(self):
            return '{:d} | {:s}'.format(self['th_off'], self['th_flags'].summary())

    def __th_options(self):
        total = self['th_off/th_flags'].li['th_off']*4
        return dyn.array(u_char, total - 0x14)

    _fields_ = [
        (u_short, 'th_sport'),
        (u_short, 'th_dport'),
        (tcp_seq, 'th_seq'),
        (tcp_seq, 'th_ack'),

        #(u_char, 'th_off'),
        #(u_char, 'th_flags'),
        (pbinary.bigendian(_offset_and_flags), 'th_off/th_flags'),

        (u_short, 'th_win'),
        (u_short, 'th_sum'),
        (u_short, 'th_urp'),

        (__th_options, 'th_options'),
    ]

    def th_off(self):
        return self['th_off/th_flags']['th_off']

    def th_flags(self):
        return self['th_off/th_flags']['th_flags']

    def nextlayer_size(self):
        raise NotImplementedError

