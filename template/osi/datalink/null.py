import ptypes
from ptypes import *

from ..__base__ import stackable

layers = {
    2 : 0x0800
}

class header(pstruct.type, stackable):
    _fields_ = [
        (pint.littleendian(pint.uint32_t), 'family'),
    ]

    def nextlayer_id(self):
        res = self['family'].li.int()
        return layers[res]

