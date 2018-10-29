import ptypes
from ptypes import ptype

from ..__base__ import stackable

class layer(ptype.definition):
    cache = {}

class stackable(stackable):
    def nextlayer_id(self):
        raise NotImplementedError

    def nextlayer(self):
        id = self.nextlayer_id()
        res = layer.withdefault(id, type=id)
        return (res, None)
