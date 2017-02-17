import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils,pbinary
from ..__base__ import *

from . import headers
from .headers import virtualaddress

class UNWIND_CODE(dyn.union):
    #http://msdn.microsoft.com/en-us/library/ck9asaa9.aspx

    @pbinary.bigendian
    class _CodeOffset(pbinary.struct):
        _fields_ = [
            (8, 'CodeOffset'),
            (4, 'UnwindOp'),
            (4, 'OpInfo'),
        ]
    _fields_ = [
        (_CodeOffset, 'CodeOffset'),
        (word, 'FrameOffset')
    ]

class UNWIND_INFO(pstruct.type):
    class Header(pbinary.struct):
        EHANDLER = 0x1
        UHANDLER = 0x2
        CHAININFO = 0x4
        _fields_=[(3,'Version'),(5,'Flags')]
    class Frame(pbinary.struct): _fields_=[(4,'Register'),(4,'Offset')]
    class ExceptionHandler(pstruct.type):
        _fields_ = [
            (virtualaddress(ptype.undefined), 'Address'),
            (ptype.undefined, 'Data')
        ]
    def __ExceptionHandler(self):
        h = self['Header'].l
        n = h['Flags']
        if (n&(h.EHANDLER|h.UHANDLER)>0) and (n&h.CHAININFO == 0):
            return self.ExceptionHandler
        return ptype.undefined
    def __ChainedUnwindInfo(self):
        h = self['Header'].l
        n = h['Flags']
        if n&h.CHAININFO > 0:
            return RUNTIME_FUNCTION
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (byte, 'SizeOfProlog'),
        (byte, 'CountOfCodes'),
        (Frame, 'Frame'),
        (lambda s: dyn.array(UNWIND_CODE, s['CountOfCodes'].li.int()), 'UnwindCode'),
        (__ExceptionHandler, 'ExceptionHandler'),
        (__ChainedUnwindInfo, 'ChainedUnwindInfo'),
    ]

class RUNTIME_FUNCTION(pstruct.type):
    _fields_ = [
        (dword, 'BeginAddress'),
        (dword, 'EndAddress'),
        (virtualaddress(UNWIND_INFO), 'UnwindData'),
    ]

class IMAGE_EXCEPTION_DIRECTORY(parray.block):
    _object_ = RUNTIME_FUNCTION

    def blocksize(self):
        return self.p.p['Size'].int()

if __name__ == '__main__':
    import pecoff,ptypes
    a = pecoff.Executable.open('c:/windows/sysnative/wow64win.dll')
    print a['padding'].hexdump()
    print a['Data']['Sections'][0]
    #b = a.new(dyn.block(0x5b74), offset=0x50e00)
    b = a['Data']['DataDirectory'][3]['virtualaddress'].d
    b=b.l
    #c = RUNTIME_FUNCTION(source=ptypes.prov.proxy(b))
    c = b[2]['UnwindData'].d.l
    print c['header']
    print ptypes.bitmap.string(c['header'].bitmap())
    print c['sizeofprolog']
    print c['countofcodes']
    print c['frame']
    print c['unwindcode']
    print c['exceptionhandler']
    print c['chainedunwindinfo']
