import ptypes, functools, itertools
from ptypes import *

from . import layer, stackable, terminal
from . import utils, address
from .. import layer as link

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
lladdr = address.ethaddr

@link.define
class ethhdr(pstruct.type, stackable):
    type = layer.enum.byname('ETHERNET')
    def __type(self):
        from .. import network
        # FIXME: these enumerations could be better organized.
        class type(network.layer.enum, u_short):
            pass
        return type

    _fields_ = [
        (address.ethaddr, 'dhost'),
        (address.ethaddr, 'shost'),
        #(u_short, 'type'),
        (__type, 'type'),
    ]

    def layer(self):
        layer, unimplemented, remaining = super(ethhdr, self).layer()
        return layer, self['type'], None

header = ethhdr
