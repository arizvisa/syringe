import ptypes
from ptypes import *

from ..__base__ import stackable

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

class oui(pbinary.struct):
    _fields_ = [
        (6, 'sextet'),
        (1, 'local'),
        (1, 'multicast'),
    ]

class lladdr(parray.type):
    length, _object_ = 6, lambda self: u_char if self.value else oui
    def summary(self):
        oui = self[0]
        scope = 'local' if oui['local'] else 'global'
        cast = 'multicast' if oui['multicast'] else 'unicast'
        octets = [ "{:02X}".format(octet.int()) for octet in self ]
        return "({:s}) {:s}".format(','.join([scope,cast]), '-'.join(octets))

class header(pstruct.type, stackable):
    _fields_ = [
        (lladdr, 'dhost'),
        (lladdr, 'shost'),
        (u_short, 'type'),
    ]

    def nextlayer_id(self):
        return self['type'].int()
