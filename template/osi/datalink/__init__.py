import ptypes
from .. import layer, stackable, terminal

class layer(layer):
    cache = {}

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import ethernet, null
