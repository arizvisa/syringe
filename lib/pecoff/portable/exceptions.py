import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils,pbinary
from ..headers import *

class UNWIND_CODE(dyn.union):
    # http://msdn.microsoft.com/en-us/library/ck9asaa9.aspx

    # FIXME: this is a pretty minimal grammar...
    #            fix this implementation and treat like one.

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
        class UNW_FLAG_(pbinary.enum):
            width = 5
            _values_ = [
                ('NHANDLER', 0),
                ('EHANDLER', 1),
                ('UHANDLER', 2),
                ('FHANDLER', 3),
                ('CHAININFO', 4),
            ]
        _fields_=[
            (UNW_FLAG_, 'Flags'),
            (3, 'Version'),
        ]

    class Frame(pbinary.struct):
        _fields_ = [
            (4, 'Register'),
            (4, 'Offset'),
        ]
    class ExceptionHandler(pstruct.type):
        _fields_ = [
            (virtualaddress(ptype.undefined, type=dword), 'Address'),
            (ptype.undefined, 'Data')
        ]

    def __ExceptionHandler(self):
        h = self['Header'].l
        n = h.__field__('Flags')
        if (n.int() & (n.byname('EHANDLER') | n.byname('UHANDLER')) > 0) and (n.int() & n.byname('CHAININFO') == 0):
            return self.ExceptionHandler
        return ptype.undefined

    def __ChainedUnwindInfo(self):
        h = self['Header'].l
        n = h.__field__('Flags')
        if n.int() == n.byname('CHAININFO') > 0:
            return RUNTIME_FUNCTION
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (byte, 'SizeOfProlog'),
        (byte, 'CountOfCodes'),
        (Frame, 'Frame'),
        (lambda s: dyn.array(UNWIND_CODE, s['CountOfCodes'].li.int()), 'UnwindCode'),
        (dyn.align(4), 'align(ExceptionHandler)'),  # FIXME: this was copied from IDA
        (__ExceptionHandler, 'ExceptionHandler'),
        (__ChainedUnwindInfo, 'ChainedUnwindInfo'),
    ]

class RUNTIME_FUNCTION(pstruct.type):
    _fields_ = [
        (dword, 'BeginAddress'),
        (dword, 'EndAddress'),
        (virtualaddress(UNWIND_INFO, type=dword), 'UnwindData'),
    ]

class IMAGE_EXCEPTION_DIRECTORY(parray.block):
    _object_ = RUNTIME_FUNCTION

    def blocksize(self):
        return self.p.p['Size'].int()

if __name__ == '__main__':
    import ptypes, pecoff
    source = ptypes.provider.file('c:/windows/system32/wow64win.dll', mode='rb')
    a = pecoff.Executable.File(source=source).l
    print(a['Next']['Header']['padding'].hexdump())
    print(a['Next']['Data']['Segments'][0])
    #b = a.new(dyn.block(0x5b74), offset=0x50e00)
    b = a['Next']['Header']['DataDirectory'][3]['Address'].d
    b=b.l
    #c = RUNTIME_FUNCTION(source=ptypes.prov.proxy(b))
    c = b[2]['UnwindData'].d.l
    print(c['header'])
    print(ptypes.bitmap.string(c['header'].bitmap()))
    print(c['sizeofprolog'])
    print(c['countofcodes'])
    print(c['frame'])
    print(c['unwindcode'])
    print(c['exceptionhandler'])
    print(c['chainedunwindinfo'])
