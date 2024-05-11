import ptypes
from ptypes import *

from . import layer, stackable, terminal, network

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class tcp_seq(pint.uint32_t): pass

class flags(pbinary.flags):
    _fields_ = [(1,F) for F in ('NON','CWR','ECE','URG','ACK','PSH','RST','SYN','FIN')]

@network.layer.define
class header(pstruct.type, stackable):
    type = 0x06
    class _offset_and_flags(pbinary.struct):
        class _th_off(pbinary.integer):
            def blockbits(self):
                return 4
            def summary(self):
                res = super(header._offset_and_flags._th_off, self).summary()
                return "{:s} : {:+d} bytes".format(res, 4 * self.int())
        _fields_ = [
            (_th_off,'th_off'),
            (3,'th_rsvd'),
            (flags, 'th_flags')
        ]
        def summary(self):
            res = []
            res.append("th_off={:d} ({:+d})".format(self['th_off'], 4 * self['th_off']))
            res.append("th_rsvd={:s}".format(self.field('th_rsvd').summary())) if self['th_rsvd'] else ()
            return "{:s} | th_flags={:s}".format(' '.join(res), self['th_flags'].summary())

    def __th_options(self):
        res = self['off_flags'].li
        total = 4 * res['th_off']
        # FIXME: implement these options
        return dyn.array(u_char, total - 0x14)

    _fields_ = [
        (u_short, 'th_sport'),
        (u_short, 'th_dport'),
        (tcp_seq, 'th_seq'),
        (tcp_seq, 'th_ack'),

        #(u_char, 'th_off'),
        #(u_char, 'th_flags'),
        (pbinary.bigendian(_offset_and_flags), 'off_flags'),

        (u_short, 'th_win'),
        (u_short, 'th_sum'),
        (u_short, 'th_urp'),

        (__th_options, 'th_options'),
    ]

    def th_off(self):
        return self['off_flags']['th_off']

    def th_flags(self):
        return self['off_flags']['th_flags']
