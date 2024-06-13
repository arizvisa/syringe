import ptypes
from .. import layer, stackable, terminal

class layer(layer):
    cache = {}

    # FIXME: This enumeration should actually be treated
    #        as a centralized database for the ethertypes.
    class _enum_(ptypes.pint.enum):
        _values_ = [
            ('Ethernet', 1),
            ('AX.25', 3),
            ('ProNET', 4),
            ('Chaos', 5),
            ('IEEE802', 6),
            ('ARCNET', 7),
            ('Hyperchannel', 8),
            ('Lanstar', 9),
            ('Autonet', 10),
            ('LocalTalk', 11),
            ('LocalNet', 12),
            ('Ultra', 13),
            ('SMDS', 14),
            ('FrameRelay', 15),
            ('HDLC', 17),
            ('Fibre', 18),
            ('ATM', 19),
            ('Serial', 20),
            ('Metricom', 23),
            ('IEEE1394.1995', 24),
            ('MAPOS', 25),
            ('Twinaxial', 26),
            ('EUI-64', 27),
            ('HIPARP', 28),
            ('ARPSec', 30),
            ('IPsec', 31),
            ('InfiniBand', 32),
            ('CAI', 33),
            ('Wiegand', 34),
            ('PureIP', 35),
            ('HW_EXP1', 36),
            ('HFI', 37),
            ('UB', 38),
            ('AEthernet', 257),
        ]

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import ethernet, null
