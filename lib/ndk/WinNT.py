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

if False:
    class _LIST_ENTRY(pstruct.type):
        _fields_ = [
            (lambda s: dyn.clone(LIST_ENTRY,_object_=s._object_), 'Entry'),
            (lambda s: s._object_, 'Value')
        ]

    class LIST_ENTRY(_LIST_ENTRY):
        '''_object_ represents the type of linked list it is'''

        _fields_ = [
            (lambda s: dyn.pointer(dyn.clone(_LIST_ENTRY,_object_=s._object_)), 'Flink'),
            (lambda s: dyn.pointer(dyn.clone(_LIST_ENTRY,_object_=s._object_)), 'Blink'),
        ]

        def walk(self, direction='Flink', path=('Entry',)):
            '''Walks through a circular linked list'''
            def nextentry(state,path):
                try:
                    next = path.next()
                    return nextentry(state[next], path)
                except StopIteration:
                    pass
                return state

            n = self[direction]
            start = self.getoffset()
            while True:
                result = n.d
                yield result.l
                n = nextentry(result, iter(path))
                n = n[direction]
                if n.int() == start:
                    break
                continue
            return

        def moonwalk(self):
            return self.walk('Blink')

        def summary(self):
            fwd,bak=self['Flink'].int(),self['Blink'].int()
            return '[Flink=0x%x,Blink=0x%x]'%(fwd,bak)

    LIST_ENTRY._object_ = ptype.empty

    class _LIST_ENTRY(pstruct.type):
        _fields_ = [
            (lambda s: dyn.pointer(s._object_), 'Flink'),
            (lambda s: dyn.pointer(s._object_), 'Blink'),
        ]

    class _LIST_ENTRY(pstruct.type):
        _object_ = None
        _path_ = ()

        _fields_ = [
            (lambda s: dyn.pointer(s._object_), 'Flink'),
            (lambda s: dyn.pointer(s._object_), 'Blink'),
        ]
        flink,blink = 'Flink','Blink'

        def forward(self):
            return self[self.flink].d
        def backward(self):
            return self[self.blink].d

        def walk(self, direction=flink):
            '''Walks through a circular linked list'''
            def nextentry(state,path):
                try:
                    next = path.next()
                    return nextentry(state[next], path)
                except StopIteration:
                    pass
                return state

            n = self[direction]
            start = self.getoffset()
            while True:
                result = n.d
                yield result.l
                n = nextentry(result, iter(self._path_))
                n = n[direction]
                if n.int() == start:
                    break
                continue
            return

        def moonwalk(self):
            return self.walk(direction=self.blink)

class _LIST_ENTRY(pstruct.type):
    _object_ = None
    _path_ = ()

    _fields_ = [
        (lambda s: s._object_, 'Flink'),
        (lambda s: s._object_, 'Blink'),
    ]
    flink,blink = 'Flink','Blink'

    def __init__(self, **attrs):
        super(_LIST_ENTRY,self).__init__(**attrs)
        assert issubclass(self._object_, ptype.pointer_t), '%s.%s._object_ is not a valid pointer'%(self.__module__,self.__class__.__name__)

    def forward(self):
        return self[self.flink].d
    def backward(self):
        return self[self.blink].d

    def walk_nextentry(self,state,path):
        try:
            # python doesn't tail-recursion anyways...
            next = path.next()
            state = self.walk_nextentry(state[next], path)
        except StopIteration:
            pass
        return state

    def walk(self, direction=flink):
        '''Walks through a circular linked list'''
        n = self[direction]
        start = self.getoffset()
        while True:
            result = n.d
            yield result.l

            n = self.walk_nextentry(result, iter(self._path_))
            if n.__class__ != self.__class__:
                raise ValueError("%s.%s - resolving of %s didn't result in the correct type"%(self.__module__, self.__class__.__name__, self._path_))
            n = n[direction]

            if n.int() == start:
                break
            continue
        return

    def moonwalk(self):
        return self.walk(direction=self.blink)

_LIST_ENTRY._object_ = dyn.pointer(_LIST_ENTRY)
_LIST_ENTRY._path_ = ()
LIST_ENTRY = _LIST_ENTRY

### ??
class UCHAR(pint.uint8_t): pass

###
class EXCEPTION_FLAGS(pbinary.struct):
    _fields_ = [
        (1,    'NONCONTINUABLE'),
        (1,    'UNWINDING'),
        (1,    'EXIT_UNWIND'),
        (1,    'STACK_INVALID'),
        (1,    'NESTED_CALL'),
        (1,    'TARGET_UNWIND'),
        (1,    'COLLIDED_UNWIND'),
        (1+24, 'unknown'),
    ]

class EXCEPTION_RECORD32(pstruct.type):
    _fields_ = [
        (DWORD, 'ExceptionCode'),
        (EXCEPTION_FLAGS, 'ExceptionFlags'),
        (lambda s: dyn.pointer(EXCEPTION_RECORD32), 'ExceptionRecord'),
        (PVOID, 'ExceptionAddress'),
        (DWORD, 'NumberParameters'),
        (lambda s: dyn.array(DWORD, s['NumberParameters'].l.int()), 'ExceptionInformation'),
    ]

class EXCEPTION_RECORD(EXCEPTION_RECORD32): pass

if False:
    # FIXME: this isn't tested at all
    class EXCEPTION_RECORD64(pstruct.type):
        _fields_ = [
            (DWORD, 'ExceptionCode'),
            (EXCEPTION_FLAGS, 'ExceptionFlags'),
            (lambda s: dyn.pointer(EXCEPTION_RECORD64), 'ExceptionRecord'), # FIXME: 64
            (PVOID, 'ExceptionAddress'),    # FIXME: 64
            (DWORD, 'NumberParameters'),
            (DWORD, '__unusedAlignment'),
            (lambda s: dyn.array(DWORD64, s['NumberParameters'].l.int()), 'ExceptionInformation'),
        ]

class EXCEPTION_REGISTRATION(pstruct.type):
    _fields_ = [
        (lambda s:dyn.pointer(EXCEPTION_REGISTRATION), 'Next'),
        (PVOID, 'Handler'),
    ]

    def isLast(self):
        return self['Next'].int() == 0xffffffff

    def fetch(self):
        result = []
        while True:
            result.append(self['Handler'])
            if self.isLast():
                break
            self = self['Next'].d.l
        return result

class NT_TIB(pstruct.type):
    _fields_ = [
#        (dyn.block(4), 'ExceptionList'),
        (dyn.pointer(EXCEPTION_REGISTRATION), 'ExceptionList'),
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
