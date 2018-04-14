import ptypes, osi.__base__
from osi import datalink
from ptypes import ptype,pstruct

class layer(ptype.definition):
    cache = {}

    class unknown(ptype.block):
        def nextlayer_type(self):
            return None

class stackable(osi.__base__.stackable):
    def nextlayer_id(self):
        raise NotImplementedError

    def nextlayer(self):
        id, sz = self.nextlayer_id(), self.nextlayer_size()
        t = layer.withdefault(id, type=id, length=sz)
        return t,sz

    def nextlayer_size(self):
        return None

class terminal(osi.__base__.terminal): pass
