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

class tcp_options(ptype.definition):
    cache = {}
    class _enum_(pint.enum, u_char):
        _values_ = [
          ('END-OF-OPTION', 0),                                 # End of Option List [RFC9293]
          ('NOOP', 1),                                          # No-Operation [RFC9293]
          ('MSS', 2),                                           # Maximum Segment Size [RFC9293]
          ('Window Scale', 3),                                  # [RFC7323]
          ('SACK Permitted', 4),                                # [RFC2018]
          ('SACK', 5),                                          # [RFC2018]
          ('Echo', 6),                                          # (obsoleted by option 8) [RFC1072][RFC6247]
          ('Echo Reply', 7),                                    # (obsoleted by option 8) [RFC1072][RFC6247]
          ('Timestamps', 8),                                    # [RFC7323]
          ('Partial Order Connection Permitted', 9),            # (obsolete) [RFC1693][RFC6247]
          ('Partial Order Service Profile', 10),                # (obsolete) [RFC1693][RFC6247]
          ('CC', 11),                                           # (obsolete) [RFC1644][RFC6247]
          ('CC.NEW', 12),                                       # (obsolete) [RFC1644][RFC6247]
          ('CC.ECHO', 13),                                      # (obsolete) [RFC1644][RFC6247]
          ('TCP Alternate Checksum Request', 14),               # (obsolete) [RFC1146][RFC6247]
          ('TCP Alternate Checksum Data', 15),                  # (obsolete) [RFC1146][RFC6247]
          ('Skeeter', 16),                                      # [Stev_Knowles]
          ('Bubba', 17),                                        # [Stev_Knowles]
          ('Trailer Checksum Option', 18),                      # [Subbu_Subramaniam][Monroe_Bridges]
          ('MD5 Signature Option', 19),                         # (obsoleted by option 29) [RFC2385]
          ('SCPS Capabilities', 20),                            # [Keith_Scott]
          ('Selective Negative Acknowledgements', 21),          # [Keith_Scott]
          ('Record Boundaries', 22),                            # [Keith_Scott]
          ('Corruption experienced', 23),                       # [Keith_Scott]
          ('SNAP', 24),                                         # [Vladimir_Sukonnik]
          ('Unassigned', 25),                                   # (released 2000-12-18)
          ('TCP Compression Filter', 26),                       # [Steve_Bellovin]
          ('Quick-Start Response', 27),                         # [RFC4782]
          ('User Timeout Option', 28),                          # [RFC5482]
          ('TCP-AO', 29),                                       # TCP Authentication Option [RFC5925]
          ('MPTCP', 30),                                        # Multipath TCP [RFC8684]
          ('TCP Fast Open Cookie', 34),                         # [RFC7413]
          ('TCP-ENO', 69),                                      # Encryption Negotiation [RFC8547]
          ('AccECN0', 172),                                     # Accurate ECN Order 0 [RFC-ietf-tcpm-accurate-ecn-34]
          ('AccECN1', 174),                                     # Accurate ECN Order 1 [RFC-ietf-tcpm-accurate-ecn-34]
          ('RFC3692-style Experiment 1', 253),                  # (also improperly used for shipping products) [RFC4727]
          ('RFC3692-style Experiment 2', 254),                  # (also improperly used for shipping products) [RFC4727]
    ]

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
