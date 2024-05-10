import ptypes
from ptypes import *

from . import layer, stackable, terminal

layers = {
    2 : 0x0800
}

class header(pstruct.type, stackable):
    _fields_ = [
        (pint.littleendian(pint.uint32_t), 'family'),
    ]

    def layer(self):
        layer, id, remaining = super(stackable, self).layer()
        return None, id, None

    def nextlayer_id(self):
        res = self['family'].li.int()
        return layers[res]
