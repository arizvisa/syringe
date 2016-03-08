from ptypes import *

short = pint.int16_t

class fpointer_t(ptype.opointer_t):
    """This is typically used for LIST_ENTRY"""
    _path_ = ()
    def _calculate_(self, offset):
        res = self.new(self._object_).a
        for p in self._path_: res = res[p]
        return offset - res.getoffset()
    def classname(self):
        return self.typename() + '(' + self._object_.typename() + (', _path_=%r)'%(self._path_,) if self._path_ else ')')

def fpointer(type, fieldname):
    return dyn.clone(fpointer_t, _object_=type, _path_=tuple(fieldname) if hasattr(fieldname,'__iter__') else (fieldname,))

class PVOID(dyn.pointer(ptype.undefined, type=pint.uint32_t)): pass
class PVOID64(dyn.pointer(ptype.undefined, type=pint.uint64_t)): pass
class ULONG_PTR(ptype.pointer_t): pass

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
class BOOLEAN(BYTE): pass
class PBOOLEAN(dyn.pointer(BOOLEAN)): pass

### Singly-linked list
class _SLIST_ENTRY(fpointer_t):
    _object_ = None
    _sentinel_ = 0

    def __init__(self, **attrs):
        super(_SLIST_ENTRY,self).__init__(**attrs)
        assert issubclass(self._object_, ptype.pointer_t), '%s.%s._object_ is not a valid pointer'%(self.__module__,self.__class__.__name__)

    def walk_nextentry(self,state,path):
        try:
            # python doesn't tail-recurse anyways...
            next = path.next()
            state = self.walk_nextentry(state[next], path)
        except StopIteration:
            pass
        return state

    def walk(self):
        '''Walks through a linked list'''
        sentinel = 0 if self._sentinel_ is None else self._sentinel_
        n = self
        while n.num() != sentinel:
            result = n.d
            yield result.l
            n = self.walk_nextentry(result, iter(self._path_))
            if n.int() == 0: break
        return

_SLIST_ENTRY._object_ = _SLIST_ENTRY
_SLIST_ENTRY._path_ = ()
SLIST_ENTRY = _SLIST_ENTRY

class SLIST_HEADER(pstruct.type):
    def __Next(self):
        p = getattr(self, '_path_', _SLIST_ENTRY._path_)
        o = getattr(self, '_object_', _SLIST_ENTRY._object_)
        return dyn.clone(_SLIST_ENTRY, _path_=p, _object_=o)

    _fields_ = [
        (__Next, 'Next'),
        (pint.uint16_t, 'Depth'),
        (pint.uint16_t, 'Sequence'),
    ]

    def summary(self):
        return 'Next->{:s} Depth:{:d} Sequence:{:d}'.format(self['Next'].summary(), self['Depth'].num(),self['Sequence'].num())

### Doubly-linked list
class _LIST_ENTRY(pstruct.type):
    _fields_ = [
        (lambda s: s._object_, 'Flink'),
        (lambda s: s._object_, 'Blink'),
    ]
    flink,blink = 'Flink','Blink'
    _object_ = None
    _path_ = ()
    _sentinel_ = None

    def __init__(self, **attrs):
        super(_LIST_ENTRY,self).__init__(**attrs)
        assert issubclass(self._object_, ptype.pointer_t), '%s.%s._object_ is not a valid pointer'%(self.__module__,self.__class__.__name__)

    def summary(self):
        return '<->'.join(('f:'+hex(self['Flink'].num()), 'b:'+hex(self['Blink'].num())))

    def forward(self):
        if self[self.flink].num() == self._sentinel_:
            raise StopIteration, self
        return self[self.flink].d

    def backward(self):
        return self[self.blink].d

    def walk_nextentry(self,state,path):
        try:
            # python doesn't tail-recurse anyways...
            next = path.next()
            state = self.walk_nextentry(state[next], path)
        except StopIteration:
            pass
        return state

    def walk(self, direction=flink):
        '''Walks through a circular linked list'''
        n = self[direction]
        sentinel = self.getoffset() if self._sentinel_ is None else self._sentinel_
        while n.num() != 0 and n.int() != sentinel:
            result = n.d
            yield result.l
            n = self.walk_nextentry(result, iter(self._path_))
            n = n[direction]
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
        (lambda s: dyn.array(DWORD, s['NumberParameters'].li.int()), 'ExceptionInformation'),
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
            (lambda s: dyn.array(DWORD64, s['NumberParameters'].li.int()), 'ExceptionInformation'),
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
            self = self['Next'].d.li
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
    NTDDI_VERSION = sdkddkver.NTDDI_VERSION
    WIN64 = sdkddkver.WIN64
    attributes = { 'NTDDI_VERSION':NTDDI_VERSION, 'WIN64':WIN64 }

class SIZE_T(ULONG): pass

class rfc4122(pstruct.type):
    _fields_ = [
        (pint.bigendian(pint.uint32_t), 'Data1'),
        (pint.bigendian(pint.uint16_t), 'Data2'),
        (pint.bigendian(pint.uint16_t), 'Data3'),
        (pint.bigendian(pint.uint64_t), 'Data4'),
    ]
    def repr(self, **options):
        return self.summary(**options)
    def summary(self, **options):
        if self.initialized:
            d1 = '%08x'% self['Data1'].num()
            d2 = '%04x'% self['Data2'].num()
            d3 = '%04x'% self['Data3'].num()
            _ = list(self['Data4'].serialize())
            d4 = ''.join('%02x'%ord(ch) for ch in _[:2])
            d5 = ''.join('%02x'%ord(ch) for ch in _[2:])
            return '{' + '-'.join((d1,d2,d3,d4,d5)) + '}'
        return '{????????-????-????-????-????????????}'

class GUID(rfc4122):
    _fields_ = [
        (endian(t),n) for endian,(t,n) in zip((pint.littleendian,pint.littleendian,pint.littleendian,pint.bigendian),rfc4122._fields_)
    ]

class CLIENT_ID(pstruct.type):
    _fields_ = [
        (PVOID, 'UniqueProcess'),
        (PVOID, 'UniqueThread'),
    ]
