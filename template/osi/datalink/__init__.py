#from .__base__ import layer
#from ..__base__ import stackable

import ptypes
from ptypes import ptype

from .. import layer, stackable, terminal

class layer(layer):
    cache = {}

class stackable(stackable):
    _layer_ = layer

    #def layer(self):
    #    layer, id, remaining = super(stackable, self).layer()
    #    return layer, id, remaining

    ### XXX: discard the following
    def nextlayer_id(self):
        raise NotImplementedError

    def nextlayer(self):
        id = self.nextlayer_id()
        res = layer.withdefault(id, type=id)
        return (res, None)

class terminal(terminal):
    _layer_ = layer

from . import ethernet, null
