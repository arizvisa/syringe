import ptypes, logging
from .. import layer, stackable, terminal, network

class layer(layer):
    cache = {}

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import udp, tcp, rfc2236
