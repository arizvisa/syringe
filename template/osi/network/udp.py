import __base__
from __base__ import layer,stackable

from ptypes import *

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

@layer.define
class header(pstruct.type, stackable):
    type = 0x11
    _fields_ = [
        (u_short, 'source port'),       
        (u_short, 'dest port'),       
        (u_short, 'length'),
        (u_short, 'checksum'),
    ]

    def nextlayer_size(self):
        return self['length'].int() - self.blocksize()
