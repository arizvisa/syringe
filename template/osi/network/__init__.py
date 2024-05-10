import ptypes, logging
from .. import layer, stackable, terminal, datalink

class layer(layer):
    cache = {}

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import arp, inet4, inet6
