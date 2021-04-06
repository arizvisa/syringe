import sys, ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils,pbinary
from ..headers import *

class UWOP_(pbinary.enum):
    length, _values_ = 4, [
        ('PUSH_NONVOL', 0),
        ('ALLOC_LARGE', 1),
        ('ALLOC_SMALL', 2),
        ('SET_FPREG', 3),
        ('SAVE_NONVOL', 4),
        ('SAVE_NONVOL_FAR', 5),
        ('SAVE_XMM', 6),
        ('SAVE_XMM_FAR', 7),
        ('SAVE_XMM128', 8),
        ('SAVE_XMM128_FAR', 9),
        ('PUSH_MACHFRAME', 10),
    ]

class UNWIND_CODE(pbinary.struct):
    # FIXME: define operation_info which depends on the unwind_operation_code.
    _fields_ = [
        (4, 'operation_info'),
        (UWOP_, 'unwind_operation_code'),
        (8, 'offset_in_prolog'),
    ]

class UNW_FLAG_(pbinary.enum):
    length, _values_ = 5, [
        ('NHANDLER', 0),
        ('EHANDLER', 1),
        ('UHANDLER', 2),
        ('FHANDLER', 3),
        ('CHAININFO', 4),
    ]

class UNWIND_INFO(pstruct.type):
    class _Header(pbinary.struct):
        _fields_=[
            (UNW_FLAG_, 'Flags'),
            (3, 'Version'),
        ]

    class _Frame(pbinary.struct):
        _fields_ = [
            (4, 'Offset'),
            (4, 'Register'),
        ]

    class _HandlerInfo(pstruct.type):
        def __Data(self):
            if 'ndk' in sys.modules:
                import ndk.exception
                return ndk.exception.FuncInfo
            return ptype.undefined
        _fields_ = [
            (virtualaddress(ptype.undefined, type=dword), 'Address'),
            (virtualaddress(__Data, type=dword), 'Data')
        ]

    def __HandlerInfo(self):
        res = self['Header'].li
        flags = res.item('Flags')
        return self._HandlerInfo if any(flags[item] for item in ['EHANDLER', 'UHANDLER', 'FHANDLER']) else ptype.undefined

    def __FunctionEntry(self):
        res = self['Header'].li
        flags = res.item('Flags')
        return RUNTIME_FUNCTION if flags['CHAININFO'] else ptype.undefined

    _fields_ = [
        (_Header, 'Header'),
        (byte, 'SizeOfProlog'),
        (byte, 'CountOfCodes'),
        (_Frame, 'Frame'),
        (lambda self: dyn.array(UNWIND_CODE, self['CountOfCodes'].li.int()), 'UnwindCode'),
        (dyn.align(4), 'align(ExceptionHandler)'),  # FIXME: this was copied from IDA
        (__HandlerInfo, 'HandlerInfo'),
        (__FunctionEntry, 'FunctionEntry'),
    ]

class IMAGE_RUNTIME_FUNCTION_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(ptype.undefined, type=dword), 'BeginAddress'),
        (virtualaddress(ptype.undefined, type=dword), 'EndAddress'),
        (virtualaddress(UNWIND_INFO, type=dword), 'UnwindData'),
    ]

class IMAGE_EXCEPTION_DIRECTORY(parray.block):
    _object_ = IMAGE_RUNTIME_FUNCTION_ENTRY

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
