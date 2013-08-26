import ptype,parray,pstruct,pbinary
import pint,pfloat,pstr
import config
littleendian,bigendian = config.byteorder.littleendian,config.byteorder.bigendian

import dyn,provider as prov
import utils
provider = prov

#__all__ = 'ptype,parray,pstruct,pint,pfloat,pstr,pbinary,dyn,provider,utils'.split(',')
#__all__ = 'ptype,parray,pstruct,pint,pfloat,pstr,pbinary,dyn'.split(',')

## globally changing the ptype provider
def setsource(prov):
    '''Sets the default ptype provider to the one specified'''
#    assert issubclass(prov.__class__, prov.provider), 'Needs to be of type %s'% repr(prov.provider)
    prov.seek
    prov.consume
    prov.store
    ptype.base.source = prov

## globally changing the byte order
def setbyteorder(endianness):
    '''
        _Globally_ sets the integer byte order to the endianness specified.
        can be either .bigendian or .littleendian
    '''
    ptype.setbyteorder(endianness)
    pint.setbyteorder(endianness)
    pbinary.setbyteorder(endianness)

## some things people people might find useful
from ptype import debug,debugrecurse
from ptype import istype,iscontainer

from provider import file,memory
from utils import hexdump

#__all__+= 'setsource,littleendian,bigendian,setbyteorder'.split(',')
#__all__+= 'debug,debugrecurse,istype,iscontainer,file,memory,hexdump'.split(',')

## default to byte order detected by python
setbyteorder( config.integer.byteorder )
