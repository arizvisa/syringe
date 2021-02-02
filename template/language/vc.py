import ptypes
from ptypes import *

# https://github.com/hvdieren/swan_runtime/blob/master/runtime/except-win32.h
# https://github.com/hvdieren/swan_runtime/blob/master/runtime/except-win64.h

# constants
EXCEPTION_MAXIMUM_PARAMETERS = 15

# native types
class char(pint.int8_t): pass
class int(pint.int32_t): pass
class long(pint.integer.lookup(ptypes.Config.integer.size)): pass
class DWORD(pint.uint32_t): pass
class ULONG(pint.uint32_t): pass
class ULONG64(pint.uint64_t): pass
class PVOID(ptype.pointer_t):
    _object_ = ptype.undefined
class ULONG_PTR(ptype.pointer_t):
    _object_ = ptype.undefined

# structured types
class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (PVOID, 'spare'),
        (dyn.array(char, 1), 'name'),
    ]

class _EXCEPTION_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'ExceptionCode'),
        (DWORD, 'ExceptionFlags'),
        (dyn.pointer(lambda: _EXCEPTION_RECORD), 'ExceptionRecord'),
        (PVOID, 'ExceptionAddress'),
        (DWORD, 'NumberParameters'),
        (dyn.array(dyn.pointer(ULONG), EXCEPTION_MAXIMUM_PARAMETERS), 'ExceptionInformation'),
    ]
EXCEPTION_RECORD = _EXCEPTION_RECORD

class PMD(pstruct.type):
    _fields_ = [
        (int, 'mdisp'),
        (int, 'pdisp'),
        (int, 'vdisp'),
    ]

class win32_except_info(pint.enum):
    _values_ = [
        ('info_magic_number', 0),
        ('info_cpp_object', 1),
        ('info_throw_data', 2),
        ('info_image_base', 3),
    ]

class win64_except_info(pint.enum):
    _values_ = [
        ('info_magic_number', 0),
        ('info_cpp_object', 1),
        ('info_throw_data', 2),
        ('info_image_base', 3),
    ]

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (int, 'toState'),
        (DWORD, 'offWindFunclet'),
    ]

class HandlerType(pstruct.type):
    class _adjectives(pint.enum, DWORD):
        _values_ = [
            (1, 'const'),
            (2, 'volatile'),
            (8, 'reference'),
        ]
    _fields_ = [
        (_adjectives, 'adjectives'),
        (DWORD, 'offTypeDescriptor'),
        (int, 'dispCatchObj'),
        (DWORD, 'offHandlerCode'),
        (DWORD, 'unknown'),
    ]

class TryBlockMapEntry(pstruct.type):
    _fields_ = [
        (int, 'tryLow'),
        (int, 'tryHigh'),
        (int, 'catchHigh'),
        (int, 'nCatches'),
        (DWORD, 'offHandlerArray'),
    ]

class Ip2StateMapEntry(pstruct.type):
    _fields_ = [
        (DWORD, 'offIp'),
        (int, 'iTryLevel'),
    ]

class FuncInfo(pstruct.type):
    class _magicNumber(pbinary.struct):
        _fields_ = [
            (3, 'bbtFlags'),
            (29, 'number'),
        ]
    _fields_ = [
        (_magicNumber, 'magicNumber'),
        (int, 'maxState'),
        (DWORD, 'offUnwindMap'),
        (DWORD, 'nTryBlocks'),
        (DWORD, 'offTryBlockMap'),
        (DWORD, 'nIpMapEntries'),
        (DWORD, 'offIpToStateMap'),
        (int, 'EHFlags'),
    ]

class Win32CatchableType(pstruct.type):
    _fields_ = [
        (DWORD, 'properties'),
        (dyn.pointer(TypeDescriptor), 'pType'),
        (PMD, 'thisDisplacement'),
        (int, 'sizeOrOffset'),
        (PVOID, 'copyFunction'),
    ]

class Win64CatchableType(pstruct.type):
    _fields_ = [
        (DWORD, 'properties'),
        (DWORD, 'offTypeDescriptor'),
        (PMD, 'thisDisplacement'),
        (int, 'sizeOrOffset'),
        (DWORD, 'offCopyFunction'),
    ]

class Win32CatchableTypeInfo(pstruct.type):
    _fields_ = [
        (int, 'nCatchableTypes'),
        (dyn.array(dyn.pointer(Win32CatchableType), 1), 'arrayOfCatchableTypes'),
    ]

class Win64CatchableTypeInfo(pstruct.type):
    _fields_ = [
        (int, 'nCatchableTypes'),
        (DWORD, 'offArrayOfCatchableTypes'),
    ]

class Win32ThrowInfo(pstruct.type):
    _fields_ = [
        (DWORD, 'attributes'),
        (PVOID, 'pmfnUnwind'),
        (PVOID, 'pForwardCompat'),
        (dyn.pointer(Win32CatchableTypeInfo), 'pCatchableTypeArray'),
    ]

class Win64ThrowInfo(pstruct.type):
    _fields_ = [
        (DWORD, 'attributes'),
        (DWORD, 'offDtor'),
        (DWORD, 'pfnForwardCompat'),
        (DWORD, 'offCatchableTypeInfo'),
    ]

### this is all cilk-related
class cilk_fiber(ptype.undefined): pass
class cilkrts_worker(ptype.undefined): pass
class cilkrts_stack_frame(ptype.undefined): pass

class pending_exception_info32(pstruct.type):
    _fields_ = [
        (PVOID, 'rethrow_sp'),
        (dyn.pointer(cilk_fiber), 'fiber'),
        (dyn.pointer(cilkrts_worker), 'w'),
        (dyn.pointer(cilkrts_stack_frame), 'saved_sf'),
        (Win32ThrowInfo, 'fake_info'),
        (dyn.pointer(Win32ThrowInfo), 'real_info'),
        (DWORD, 'ExceptionCode'),
        (DWORD, 'ExceptionFlags'),
        (DWORD, 'NumberParameters'),
        (dyn.array(ULONG_PTR, EXCEPTION_MAXIMUM_PARAMETERS), 'ExceptionInformation'),
    ]

class pending_exception_info64(pstruct.type):
    _fields_ = [
        (dyn.pointer(lambda: pending_exception_info), 'nested_exception'),
        (ULONG64, 'rethrow_rip'),
        (ULONG64, 'exception_rbp'),
        (ULONG64, 'exception_rsp'),
        (ULONG64, 'sync_rbp'),
        (ULONG64, 'sync_rsp'),
        (dyn.pointer(cilk_fiber), 'exception_fiber'),
        (dyn.pointer(cilkrts_worker), 'w'),
        (dyn.pointer(cilkrts_stack_frame), 'saved_protected_tail'),
        (dyn.pointer(EXCEPTION_RECORD), 'pExceptRec'),
        (Win64ThrowInfo, 'copy_ThrowInfo'),
        (DWORD, 'offset_dtor'),
        (int, 'nested_exception_found'),
        (int, 'saved_protected_tail_worker_id'),
    ]

class exception_entry_t(pstruct.type):
    _fields_ = [
        (PVOID, 'exception_object'),
        (dyn.pointer(pending_exception_info32), 'pei'),
    ]

class pending_exceptions_t(pstruct.type):
    _fields_ = [
        (long, 'lock'),
        (int, 'max_pending_exceptions'),
        (dyn.pointer(exception_entry_t), 'entries'),
    ]
