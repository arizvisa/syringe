import ptypes
from ptypes import ptype,pstruct

from ..__base__ import stackable, terminal
from .. import network

class layer(ptype.definition):
    cache = {}

    class unknown(ptype.block):
        def nextlayer_type(self):
            return None
    default = unknown

class stackable(stackable):
    def nextlayer_id(self):
        raise NotImplementedError

    def nextlayer(self):
        id, sz = self.nextlayer_id(), self.nextlayer_size()
        t = layer.withdefault(id, type=id, length=sz)
        return t,sz

    def nextlayer_size(self):
        return None

class terminal(terminal): pass
