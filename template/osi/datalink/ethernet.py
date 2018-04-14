import ptypes, __base__
from ptypes import *

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

class lladdr(parray.type): length, _object_ = 6, u_char

class header(pstruct.type, __base__.stackable):
    _fields_ = [
        (lladdr, 'dhost'),
        (lladdr, 'shost'),
        (u_short, 'type'),
    ]

    def nextlayer_id(self):
        return self['type'].int()
