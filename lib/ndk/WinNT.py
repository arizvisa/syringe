import ptypes
from ptypes import *

from . import sdkddkver

###
class versioned(ptype.type):
    '''will update the attrs with the operating systems NTDDI_VERSION'''
    NTDDI_VERSION = sdkddkver.NTDDI_VERSION
    WIN64 = sdkddkver.WIN64
    attributes = { 'NTDDI_VERSION':NTDDI_VERSION, 'WIN64':WIN64 }
    def __init__(self, **attrs):
        super(versioned, self).__init__(**attrs)
        self.attributes['NTDDI_VERSION'] = self.NTDDI_VERSION
        self.attributes['WIN64'] = self.WIN64

###
PVALUE32 = dyn.clone(ptype.pointer_t._value_, length=4)
PVALUE64 = dyn.clone(ptype.pointer_t._value_, length=8)

class fpointer_t(ptype.opointer_t, versioned):
    """This is typically used for LIST_ENTRY"""
    @property
    def _value_(self):
        return PVALUE64 if getattr(self, 'WIN64', False) else PVALUE32

    _path_ = ()
    def _calculate_(self, offset):
        res = self.new(self._object_).a
        for p in self._path_: res = res[p]
        return offset - res.getoffset()
    def classname(self):
        res = getattr(self, '_object_', ptype.undefined) or ptype.undefined
        return self.typename() + '(' + res.typename() + (', _path_={!r})'.format(self._path_) if self._path_ else ')')

def fpointer(type, fieldname):
    return dyn.clone(fpointer_t, _object_=type, _path_=tuple(fieldname) if hasattr(fieldname,'__iter__') else (fieldname,))
fptr = fpointer

###
class PVOID(ptype.pointer_t, versioned):
    @property
    def _value_(self):
        return PVALUE64 if getattr(self, 'WIN64', False) else PVALUE32
    _object_ = ptype.undefined

class pointer_t(ptype.pointer_t, versioned):
    @property
    def _value_(self):
        return PVALUE64 if getattr(self, 'WIN64', False) else PVALUE32
    _object_ = ptype.undefined

    @classmethod
    def typename(cls):
        return cls.__name__

def pointer(target, **attrs):
    return dyn.clone(pointer_t, _object_=target)
P = pointer

###
class rpointer_t(ptype.rpointer_t, versioned):
    @property
    def _value_(self):
        return PVALUE64 if getattr(self, 'WIN64', False) else PVALUE32

    def decode(self, object, **attrs):
        root = ptype.force(self._baseobject_, self)
        base = root.getoffset() if isinstance(root,ptype.generic) else root().getoffset()
        t = pint.uint64_t if getattr(self,'WIN64',False) else pint.uint32_t
        return t().set(base + object.get())

def rpointer(target, base, **attrs):
    return dyn.clone(rpointer_t, _baseobject_=base, _object_=target, **attrs)
rptr = rpointer

###
class short(pint.int16_t): pass
class ULONG_PTR(PVOID): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass

class SHORT(pint.int16_t): pass
class LONG(pint.int32_t): pass
class USHORT(pint.uint16_t): pass
class ULONG(pint.uint32_t): pass

class HANDLE(PVOID): pass
class PHANDLE(pointer(HANDLE)): pass

class CHAR(pint.uint8_t): pass
class PCHAR(pointer(CHAR)): pass
class WCHAR(pint.uint16_t): pass
class PWCHAR(pointer(WCHAR)): pass

class LCID(DWORD): pass

class PWSTR(pointer(pstr.wstring)): pass
class LPWSTR(pointer(pstr.wstring)): pass

class LONGLONG(pint.int64_t): pass
class ULONGLONG(pint.uint64_t): pass

class LARGE_INTEGER(dynamic.union):
    class u(pstruct.type):
        _fields_ = [
            (DWORD, 'LowPart'),
            (DWORD, 'HighPart'),
        ]
    _fields_ = [
        (u, 'u'),
        (LONGLONG, 'QuadPart')
    ]

class ULARGE_INTEGER(dynamic.union):
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

class PLUID(pointer(LUID)): pass

###
class BOOLEAN(BYTE): pass
class PBOOLEAN(pointer(BOOLEAN)): pass

### Singly-linked list
class _SLIST_ENTRY(fpointer_t):
    _object_ = None
    _sentinel_ = 0

    def __init__(self, **attrs):
        super(_SLIST_ENTRY,self).__init__(**attrs)
        if not issubclass(self._object_, ptype.pointer_t):
            raise AssertionError('{:s}._object_ is not a valid pointer.'.format( '.'.join((self.__module__,self.__class__.__name__)) ))

    def __walk_nextentry(self,state,path):
        try:
            # python doesn't tail-recurse anyways...
            next = path.next()
            state = self.__walk_nextentry(state[next], path)
        except StopIteration:
            pass
        return state

    def walk(self):
        '''Walks through a linked list'''
        if self._sentinel_ is None:
            sentinel = {0}
        elif hasattr(self._sentinel_,'__iter__'):
            sentinel = set(self._sentinel_)
        else:
            sentinel = {self._sentinel_}

        n = self
        while n.int() not in sentinel:
            result = n.d
            yield result.l
            n = self.__walk_nextentry(result, iter(self._path_))
            if n.int() == 0: break
        return

_SLIST_ENTRY._object_ = _SLIST_ENTRY
_SLIST_ENTRY._path_ = ()
SLIST_ENTRY = _SLIST_ENTRY

class SLIST_HEADER(pstruct.type, versioned):
    def __Next(self):
        p = getattr(self, '_path_', _SLIST_ENTRY._path_)
        o = getattr(self, '_object_', _SLIST_ENTRY._object_)
        return dyn.clone(_SLIST_ENTRY, _path_=p, _object_=o)

    def __init__(self, **attrs):
        super(SLIST_HEADER, self).__init__(**attrs)
        f = self._fields_ = []
        aligned = dyn.align(8 if getattr(self,'WIN64',False) else 4)

        f.extend([
            (pint.uint32_t if getattr(self,'WIN64',False) else pint.uint_t, 'Alignment'),
            (self.__Next, 'Next'),
            (pint.uint16_t, 'Depth'),
            (pint.uint16_t, 'Sequence'),
        ])

    def summary(self):
        return 'Next->{:s} Depth:{:d} Sequence:{:d}'.format(self['Next'].summary(), self['Depth'].int(), self['Sequence'].int())

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
        if not issubclass(self._object_, ptype.pointer_t):
            raise AssertionError('{:s}._object_ is not a valid pointer'.format( '.'.join((self.__module__,self.__class__.__name__)) ))

    def summary(self):
        return '<->'.join(('f:'+hex(self['Flink'].int()), 'b:'+hex(self['Blink'].int())))

    def forward(self):
        if self[self.flink].int() == self._sentinel_:
            raise StopIteration, self
        return self[self.flink].d

    def backward(self):
        return self[self.blink].d

    def __walk_nextentry(self,state,path):
        try:
            # python doesn't tail-recurse anyways...
            key = next(path)
            state = self.__walk_nextentry(state[key], path)
        except StopIteration:
            pass
        return state

    def walk(self, direction=flink):
        '''Walks through a circular linked list'''
        n = self[direction]

        if self._sentinel_ is None:
            sentinel = {self.getoffset()}
        elif isinstance(self._sentinel_, basestring):
            sentinel = {self[self._sentinel_].int()}
        elif hasattr(self._sentinel_,'__iter__'):
            sentinel = set(self._sentinel_)
        else:
            sentinel = {self._sentinel_}

        while n.int() != 0 and n.int() not in sentinel:
            result = n.d
            yield result.l
            n = self.__walk_nextentry(result, iter(self._path_))
            n = n[direction]
        return

    def moonwalk(self):
        return self.walk(direction=self.blink)

_LIST_ENTRY._object_ = pointer(_LIST_ENTRY)
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
        (lambda s: pointer(EXCEPTION_RECORD32), 'ExceptionRecord'),
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
            (lambda s: pointer(EXCEPTION_RECORD64), 'ExceptionRecord'), # FIXME: 64
            (PVOID, 'ExceptionAddress'),    # FIXME: 64
            (DWORD, 'NumberParameters'),
            (DWORD, '__unusedAlignment'),
            (lambda s: dyn.array(DWORD64, s['NumberParameters'].li.int()), 'ExceptionInformation'),
        ]

class EXCEPTION_REGISTRATION(pstruct.type):
    _fields_ = [
        (lambda s:pointer(EXCEPTION_REGISTRATION), 'Next'),
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
        (pointer(EXCEPTION_REGISTRATION), 'ExceptionList'),
        (PVOID, 'StackBase'),
        (PVOID, 'StackLimit'),
        (PVOID, 'SubSystemTib'),
        (PVOID, 'FiberData'),
        (PVOID, 'ArbitraryUserPointer'),
        (lambda s: pointer(NT_TIB), 'Self'),
    ]

class SIZE_T(ULONG): pass
class SIZE_T64(ULONGLONG): pass

class rfc4122(pstruct.type):
    class _Data1(pint.bigendian(pint.uint32_t)):
        def summary(self):
            return '{:08x}'.format(self.int())
    class _Data2and3(pint.bigendian(pint.uint16_t)):
        def summary(self):
            return '{:04x}'.format(self.int())
    class _Data4(pint.bigendian(pint.uint64_t)):
        def summary(self):
            res = list(self.serialize())
            d1 = ''.join(map('{:02x}'.format,map(ord,res[:2])) )
            d2 = ''.join(map('{:02x}'.format,map(ord,res[2:])) )
            return '-'.join((d1,d2))
    _fields_ = [
        (_Data1, 'Data1'),
        (_Data2and3, 'Data2'),
        (_Data2and3, 'Data3'),
        (_Data4, 'Data4'),
    ]

    def summary(self, **options):
        if self.initializedQ():
            return self.str()
        return '{{????????-????-????-????-????????????}}'

    def str(self):
        d1 = '{:08x}'.format(self['Data1'].int())
        d2 = '{:04x}'.format(self['Data2'].int())
        d3 = '{:04x}'.format(self['Data3'].int())
        _ = list(self['Data4'].serialize())
        d4 = ''.join( map('{:02x}'.format,map(ord,_[:2])) )
        d5 = ''.join( map('{:02x}'.format,map(ord,_[2:])) )
        return '{{{:s}}}'.format('-'.join((d1,d2,d3,d4,d5)))

class GUID(rfc4122):
    _fields_ = [
        (transformation(t),n) for transformation,(t,n) in zip((pint.littleendian, pint.littleendian, pint.littleendian, pint.bigendian), rfc4122._fields_)
    ]

class CLIENT_ID(pstruct.type):
    _fields_ = [
        (PVOID, 'UniqueProcess'),
        (PVOID, 'UniqueThread'),
    ]
