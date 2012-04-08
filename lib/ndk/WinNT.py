from ptypes import *

short = pint.int16_t

class PVOID(dyn.pointer(ptype.empty, type=dyn.byteorder(pint.uint32_t))): pass
class PVOID64(dyn.pointer(ptype.empty, type=dyn.byteorder(pint.uint64_t))): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass

class SHORT(pint.int16_t): pass
class LONG(pint.int32_t): pass
class USHORT(pint.uint16_t): pass
class ULONG(pint.uint32_t): pass

class HANDLE(PVOID): pass
class PHANDLE(dyn.pointer(HANDLE)): pass

class CHAR(pint.uint8_t): pass
class PCHAR(dyn.pointer(CHAR)): pass
class WCHAR(pint.uint16_t): pass
class PWCHAR(dyn.pointer(WCHAR)): pass

class LCID(DWORD): pass

class PWSTR(dyn.pointer(pstr.wstring)): pass
class LPWSTR(dyn.pointer(pstr.wstring)): pass

class LONGLONG(pint.int64_t): pass
class ULONGLONG(pint.uint64_t): pass

class LARGE_INTEGER(dyn.union):
    class u(pstruct.type):
        _fields_ = [
            (DWORD, 'LowPart'),
            (DWORD, 'HighPart'),
        ]
    _fields_ = [
        (u, 'u'),
        (LONGLONG, 'QuadPart')
    ]

class ULARGE_INTEGER(dyn.union):
    class u(pstruct.type):
        _fields_ = [
            (DWORD, 'LowPart'),
            (DWORD, 'HighPart'),
        ]
    _fields_ = [
        (u, 'u'),
        (ULONGLONG, 'QuadPart')
    ]

class LUID(pstruct.type):
    _fields_ = [
        (DWORD, 'LowPart'),
        (DWORD, 'HighPart'),
    ]

class PLUID(dyn.pointer(LUID)): pass

###
class BOOLEAN(pint.int32_t): pass
class PBOOLEAN(dyn.pointer(BOOLEAN)): pass

class LIST_ENTRY(pstruct.type): pass
class LIST_ENTRY(pstruct.type):
    '''_object_ represents the type of linked list it is'''

    _object_ = LIST_ENTRY
    _fields_ = [
        (lambda s: dyn.pointer(s._object_), 'Flink'),
        (lambda s: dyn.pointer(s._object_), 'Blink'),
    ]

    def walk(self, direction='Flink'):
        '''WAlks through a circular linked list'''
        n = self[direction]
        while True:
            yield n.d
            n = n[direction]
            if int(n) == int(self[direction]):
                break
            n = n[direction]
        return

    def moonwalk(self):
        return self.walk('Blink')

### ??
class UCHAR(pint.uint8_t): pass

###
class NT_TIB(pstruct.type):
    _fields_ = [
        (dyn.block(4), 'ExceptionList'),
        (PVOID, 'StackBase'),
        (PVOID, 'StackLimit'),
        (PVOID, 'SubSystemTib'),
        (PVOID, 'FiberData'),
        (PVOID, 'ArbitraryUserPointer'),
        (lambda s: dyn.pointer(NT_TIB), 'Self'),
    ]

###
import sdkddkver
class versioned(ptype.type):
    '''will update the attrs with the operating systems NTDDI_VERSION'''
    def __init__(self, **attrs):
        attrs['NTDDI_VERSION'] = attrs.setdefault('NTDDI_VERSION', sdkddkver.NTDDI_VERSION)
        attrs['WIN64'] = attrs.setdefault('WIN64', sdkddkver.WIN64)
        super(versioned, self).__init__(**attrs)

class SIZE_T(ULONG): pass

class GUID(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Data1'),
        (pint.uint16_t, 'Data2'),
        (pint.uint16_t, 'Data3'),
        (pint.littleendian(pint.uint64_t), 'Data4'),
    ]

class CLIENT_ID(pstruct.type):
    _fields_ = [
        (PVOID, 'UniqueProcess'),
        (PVOID, 'UniqueThread'),
    ]
