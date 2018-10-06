import ptypes, __base__
from ptypes import *

layers = {
    2 : 0x0800
}

class header(pstruct.type, __base__.stackable):
    _fields_ = [
        (pint.littleendian(pint.uint32_t), 'family'),
    ]

    def nextlayer_id(self):
        res = self['family'].li.int()
        return layers[res]

