import ptype,parray,pstruct
import pint,pfloat,pstr
import pbinary

import dyn,provider
import utils

#__all__ = 'ptype,parray,pstruct,pint,pfloat,pstr,pbinary,dyn,provider,utils'.split(',')
__all__ = 'ptype,parray,pstruct,pint,pfloat,pstr,pbinary,dyn'.split(',')

## globally changing the ptype provider
def setsource(prov):
    '''Sets the default ptype provider to the one specified'''
#    assert issubclass(prov.__class__, provider.provider), 'Needs to be of type %s'% repr(provider.provider)
    prov.seek
    prov.consume
    prov.store
    ptype.type.source = prov

## globally changing the endianness of all new pint types
from pint import bigendian,littleendian
def setbyteorder(endianness):
    '''
        _Globally_ sets the integer byte order to the endianness specified.
        can be either .bigendian or .littleendian
    '''
    pint.setbyteorder(endianness)
    dyn.setbyteorder(endianness)

## default to byte order detected by python
import sys
if sys.byteorder == 'little':
    setbyteorder(pint.littleendian)
elif sys.byteorder == 'big':
    setbyteorder(pint.bigendian)
else:
    assert False is True, sys.byteorder

## some things people people might find useful
from ptype import debug,debugrecurse
from ptype import istype,iscontainer

from provider import file,memory
from utils import hexdump

#__all__+= 'setsource,littleendian,bigendian,setbyteorder'.split(',')
#__all__+= 'debug,debugrecurse,istype,iscontainer,file,memory,hexdump'.split(',')
