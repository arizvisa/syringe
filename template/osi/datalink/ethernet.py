import __base__
from ptypes import *

pint.setbyteorder(pint.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

class lladdr(dyn.array(u_char, 6)): pass

class header(pstruct.type, __base__.stackable):
    _fields_ = [
        (lladdr, 'dhost'),
        (lladdr, 'shost'),
        (u_short, 'type'),
    ]

    def nextlayer_id(self):
        return self['type'].number()
