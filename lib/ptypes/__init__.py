from . import ptype, parray, pstruct, pbinary, pint, pfloat, pstr
from . import utils, dynamic, provider
dyn, prov = dynamic, provider

__all__ = 'ptype','parray','pstruct','pbinary','pint','pfloat','pstr','dynamic','dyn','prov'

from . import config
Config = config.defaults

## globally changing the ptype provider
def setsource(provider):
    '''Sets the default ptype provider to the one specified'''
    provider.seek,provider.consume,provider.store
    ptype.source = provider
    return provider

## globally changing the byte order
def setbyteorder(endianness):
    '''
    Sets the integer byte order to the endianness specified for all non-binary types.
    Can be either config.byteorder.bigendian or config.byteorder.littleendian.
    '''
    [ module.setbyteorder(endianness) for module in (ptype,pint,pfloat) ]

## some things people people might find useful
#from ptype import debug, debugrecurse
from .ptype import istype, iscontainer, isinstance, undefined

from .provider import file, memory
from .utils import hexdump

if __name__ == '__main__':
    import builtins, ptypes
    class a(ptypes.ptype.type):
        length = 4

    data = b'\x41\x41\x41\x41'

    import ctypes
    b = ctypes.cast(ctypes.pointer(ctypes.c_buffer(data,4)), ctypes.c_void_p)

    ptypes.setsource(ptypes.prov.memory())
    print('ptype-static-memory', builtins.isinstance(ptypes.ptype.source, ptypes.prov.memory))
    print('ptype-instance-memory', builtins.isinstance(ptypes.ptype.type().source, ptypes.prov.memory))
    c = a(offset=b.value).l
    print('type-instance-memory', c.serialize() == data)

    ptypes.setsource(ptypes.prov.empty())
    print('ptype-static-empty', builtins.isinstance(ptypes.ptype.source, ptypes.prov.empty))
    print('ptype-instance-empty', builtins.isinstance(ptypes.ptype.type().source, ptypes.prov.empty))
    c = a(offset=b.value).l
    print('type-instance-empty', c.serialize() == b'\x00\x00\x00\x00')
    ptypes.setsource(ptypes.prov.memory())
