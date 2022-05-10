import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,pbinary,utils
from ..headers import *

class UINT32(uint32): pass
class UINT64(uint64): pass

class IMAGE_TLS_CALLBACK(ptype.undefined):
    '''
    void NTAPI IMAGE_TLS_CALLBACK(PVOID DllHandle, DWORD Reason, PVOID Reserved)
    '''

class IMAGE_TLS_CALLBACK_ARRAY(parray.terminated):
    def isTerminator(self, value):
        return value.int() == 0

class TLS_Characteristics(pbinary.struct):
    _fields_ = [_fields_ for _fields_ in reversed([
        (20, 'Reserved0'),
        (4, 'Alignment'),
        (8, 'Reserved1'),
    ])]

# FIXME: could be ULONG_PTR

class IMAGE_TLS_DIRECTORY32(pstruct.type):
    class _AddressOfCallbacks(IMAGE_TLS_CALLBACK_ARRAY):
        class PIMAGE_TLS_CALLBACK(realaddress(IMAGE_TLS_CALLBACK, type=uint32)):
            pass
        _object_ = PIMAGE_TLS_CALLBACK

    @pbinary.littleendian
    class _Characteristics(TLS_Characteristics):
        '''UINT32'''

    def __StartAddressOfRawData(self):
        p = self.getparent(IMAGE_TLS_DIRECTORY32)
        start, end = (p[fld].int() for fld in ['StartAddressOfRawData', 'EndAddressOfRawData'])
        return dyn.block(max(start, end) - start)

    _fields_ = [
        (realaddress(__StartAddressOfRawData, type=UINT32), 'StartAddressOfRawData'),
        (realaddress(ptype.undefined, type=UINT32), 'EndAddressOfRawData'),
        (realaddress(UINT32, type=UINT32), 'AddressOfIndex'),   # FIXME: this doesn't seem to calculate the address correctly
        (realaddress(_AddressOfCallbacks, type=UINT32), 'AddressOfCallbacks'),
        (UINT32, 'SizeOfZeroFill'),
        (_Characteristics, 'Characteristics'),
    ]

class IMAGE_TLS_DIRECTORY64(pstruct.type):
    class _AddressOfCallbacks(IMAGE_TLS_CALLBACK_ARRAY):
        class PIMAGE_TLS_CALLBACK(realaddress(IMAGE_TLS_CALLBACK, type=uint64)):
            pass
        _object_ = PIMAGE_TLS_CALLBACK

    @pbinary.littleendian
    class _Characteristics(TLS_Characteristics):
        '''UINT32'''

    def __StartAddressOfRawData(self):
        p = self.getparent(IMAGE_TLS_DIRECTORY64)
        start, end = (p[fld].int() for fld in ['StartAddressOfRawData', 'EndAddressOfRawData'])
        return dyn.block(max(start, end) - start)

    _fields_ = [
        (realaddress(__StartAddressOfRawData, type=UINT64), 'StartAddressOfRawData'),
        (realaddress(ptype.undefined, type=UINT64), 'EndAddressOfRawData'),
        (realaddress(UINT64, type=UINT64), 'AddressOfIndex'),
        (realaddress(_AddressOfCallbacks, type=UINT64), 'AddressOfCallbacks'),
        (UINT32, 'SizeOfZeroFill'),
        (_Characteristics, 'Characteristics'),
    ]
