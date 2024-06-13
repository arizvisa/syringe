import ptypes, logging
from .. import layer, stackable, terminal, datalink

class layer(layer):
    """
    This definition contains the protocol number for the network layer. It
    is commonly used for sockets and can be found inside the /etc/protocols.
    """
    cache = {}

    # FIXME: This enumeration should actually be treated
    #        as a centralized database for the ethertypes.
    class _enum_(ptypes.pint.enum):
        _values_ = [
            ('IP', 0x0800),
            ('X.75', 0x0801),
            ('NBS', 0x0802),
            ('ECMA', 0x0803),
            ('CHAOSnet', 0x0804),
            ('X.25', 0x0805),
            ('ARP', 0x0806),
            ('DCA', 0x1234),
            ('THD', 0x4321),
            ('BBN', 0x5208),
            ('DEC-LAT', 0x6004),
            ('DEC-LAVC', 0x6007),
            ('DEC-AMBER', 0x6008),
            ('DEC-MUMPS', 0x6009),
            ('HP-Probe', 0x8005),
            ('Nestar', 0x8006),
            ('Excelan', 0x8010),
            ('RARP', 0x8035),
            ('IPX', 0x8037),
            ('DEC-VAXELN', 0x803B),
            ('DEC-DNS', 0x803C),
            ('DEC-CSMA/CD', 0x803D),
            ('DEC-DTS', 0x803E),
            ('VMTP', 0x805B),
            ('Matra', 0x807A),
            ('EtherTalk', 0x809B),
            ('Spider', 0x809F),
            ('Nixdorf', 0x80A3),
            ('Pacer', 0x80C6),
            ('Applitek', 0x80C7),
            ('IBM-SNA', 0x80D5),
            ('Varian', 0x80DD),
            ('Retix', 0x80F2),
            ('AARP', 0x80F3),
            ('Novell', 0x8138),
            ('SNMP', 0x814C),
            ('PowerLAN', 0x8191),
            ('XTP', 0x817D),
            ('Kalpana', 0x8582),
            ('IP6', 0x86DD),
            ('Loopback', 0x9000),
        ]

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import arp, inet4, inet6
