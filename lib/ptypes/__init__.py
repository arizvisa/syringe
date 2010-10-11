import ptype,parray,pstruct
import pint,pfloat,pstr
import pbinary

import dyn,provider
import utils

__all__ = 'ptype,parray,pstruct,pint,pfloat,pstr,pbinary,dyn,provider,utils'.split(',')

## globally changing the ptype provider
def setsource(provider):
    ptype.type.source = provider

## globally changing the endianness of all new 
class littleendian(object): pass
class bigendian(object): pass
def setbyteorder(endianness):
    if endianness is littleendian:
        pint.setbyteorder(pint.littleendian)
    elif endianness is bigendian:
        pint.setbyteorder(pint.bigendian)
    else:
        print 'Unknown endianness %s specified'% repr(endianness)
    return

## default to byte order detected by python
import sys
if sys.byteorder == 'little':
    setbyteorder(littleendian)
elif sys.byteorder == 'big':
    setbyteorder(bigendian)
else:
    assert False is True, sys.byteorder

## some things people people might find useful
from ptype import debug,debugrecurse
from ptype import isptype,ispcontainer

from provider import file,memory
from utils import hexdump
