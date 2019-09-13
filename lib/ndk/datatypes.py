import six, math, datetime

import ptypes
from ptypes import *

from . import sdkddkver, winerror

### versioned base-class
class versioned(ptype.base):
    '''
    This base-class (mixin) will propagate all version-related attributes to
    its children. This waythe user can instantiate their type with NTDDI_VERSION
    and WIN64 being set to the desire structure, and everything can just check
    itself to determine which structure variation to use.
    '''
    NTDDI_VERSION = sdkddkver.NTDDI_VERSION
    WIN64 = sdkddkver.WIN64
    attributes = { 'NTDDI_VERSION':NTDDI_VERSION, 'WIN64':WIN64 }
    def __init__(self, **attrs):
        super(versioned, self).__init__(**attrs)
        self.attributes['NTDDI_VERSION'] = self.NTDDI_VERSION
        self.attributes['WIN64'] = self.WIN64

### stdint.h (sorta)
class int8(pint.sint8_t): pass
class int16(pint.sint16_t): pass
class int32(pint.sint32_t): pass
class int64(pint.sint64_t): pass

class hyper(dynamic.union):
    _fields_ = [
        (pint.sint64_t, 'signed'),
        (pint.uint64_t, 'unsigned'),
    ]

### pointer datatypes
PVALUE32 = dyn.clone(ptype.pointer_t._value_, length=4)
PVALUE64 = dyn.clone(ptype.pointer_t._value_, length=8)

## field pointers
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
    return dyn.clone(fpointer_t, _object_=type, _path_=tuple(fieldname) if hasattr(fieldname, '__iter__') else (fieldname,))
fptr = fpointer

## pointer types
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

## relative pointers
class rpointer_t(ptype.rpointer_t, versioned):
    @property
    def _value_(self):
        return PVALUE64 if getattr(self, 'WIN64', False) else PVALUE32

    def decode(self, object, **attrs):
        root = ptype.force(self._baseobject_, self)
        base = root.getoffset() if isinstance(root, ptype.generic) else root().getoffset()
        t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
        return t().set(base + object.get())

def rpointer(target, base, **attrs):
    return dyn.clone(rpointer_t, _baseobject_=base, _object_=target, **attrs)
rptr = rpointer

### core datatypes (handles and such)
class BYTE(pint.uint8_t): pass
class UCHAR(pstr.char_t): pass
class CHAR(pstr.char_t): pass
class PCHAR(pointer(CHAR)): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class DWORD_PTR(PVOID): pass
class short(pint.int16_t): pass
class SHORT(pint.sint16_t): pass
class USHORT(pint.uint16_t): pass
class INT(pint.sint32_t): pass
class UINT(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class ULONG(pint.uint32_t): pass
class LONG_PTR(PVOID): pass
class ULONG_PTR(PVOID): pass
class LONGLONG(pint.sint64_t): pass
class ULONGLONG(pint.uint64_t): pass
class INT8(pint.sint8_t): pass
class INT16(pint.sint16_t): pass
class INT32(pint.sint32_t): pass
class INT64(pint.sint64_t): pass
class UINT8(pint.uint8_t): pass
class UINT16(pint.uint16_t): pass
class UINT32(pint.uint32_t): pass
class UINT64(pint.uint64_t): pass
class LONG32(pint.sint32_t): pass
class LONG64(pint.sint64_t): pass
class ULONG32(pint.uint32_t): pass
class ULONG64(pint.uint64_t): pass
class octet(pint.uint8_t): pass
class BOOL(pint.uint32_t): pass
class BOOLEAN(BYTE): pass
class PBOOLEAN(pointer(BOOLEAN)): pass
class QWORD(int64): pass

class SIZE_T(ULONG): pass
class SIZE_T64(ULONGLONG): pass

class BSTR(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'length'),
        (lambda s: dyn.clone(pstr.wstring, length=s['length'].li.int()), 'string')
    ]

class DOUBLE(pfloat.double): pass
class FLOAT(pfloat.single): pass

class DWORD32(pint.uint32_t): pass
class DWORD64(pint.uint64_t): pass
class DWORDLONG(ULONGLONG): pass
class error_status_t(pint.uint32_t): pass

class HANDLE(PVOID): pass
class PHANDLE(pointer(HANDLE)): pass
class HCALL(DWORD): pass

class HRESULT(dynamic.union):
    @pbinary.littleendian
    class _hresult(pbinary.struct):
        class _severity(pbinary.enum):
            width, _values_ = 1, [('TRUE', 1), ('FALSE', 0)]
        _fields_ = [
            (_severity, 'severity'),
            (4, 'reserved'),
            (winerror.FACILITY_, 'facility'),
            (16, 'code'),
        ]
    class _result(winerror.HRESULT, LONG): pass
    _fields_ = [
        (_result, 'result'),
        (_hresult, 'hresult'),
    ]

class LMCSTR(pstr.szwstring): pass
class LMSTR(pstr.szwstring): pass
class LPCSTR(pointer(pstr.szstring)): pass
class LPCWSTR(pointer(pstr.szwstring)): pass
class PWSTR(pointer(pstr.wstring)): pass
class LPWSTR(pointer(pstr.szwstring)): pass
class LPCVOID(PVOID): pass
class NET_API_STATUS(DWORD): pass
class NTSTATUS(winerror.NTSTATUS, LONG): pass
class PCONTEXT_HANDLE(PVOID): pass
class RPC_BINDING_HANDLE(PVOID): pass

class UNICODE(pstr.wchar_t): pass
class STRING(pstr.szstring): pass
class WCHAR(pstr.wchar_t): pass
class PWCHAR(pointer(WCHAR)): pass
class UNC(STRING): pass

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

class MULTI_SZ(pstruct.type):
    class StringsValue(parray.block):
        _object_ = pstr.szwstring
        def isTerminator(self, value):
            return value.str() == ''
        def blocksize(self):
            res = self.getparent(MULTI_SZ)
            return res['nChar'].li.int()
    _fields_ = [
        (pointer(lambda s: s.getparent(MULTI_SZ).StringsValue), 'Value'),
        (DWORD, 'nChar'),
    ]

class UINT128(pstruct.type):
    _fields_ = [
        (UINT64, 'lower'),
        (UINT64, 'upper'),
    ]

class ULARGE_INTEGER(pstruct.type):
    _fields_ = [
        (pint.uint64_t, 'QuadPart'),
        (UINT64, 'upper'),
    ]

## Singly-linked list
class SLIST_ENTRY(fpointer_t):
    _object_ = None
    _sentinel_ = 0

    def __init__(self, **attrs):
        super(SLIST_ENTRY, self).__init__(**attrs)
        if not issubclass(self._object_, ptype.pointer_t):
            raise AssertionError('{:s}._object_ is not a valid pointer.'.format( '.'.join((self.__module__, self.__class__.__name__)) ))

    def __walk_nextentry(self, state, path):
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
        elif hasattr(self._sentinel_, '__iter__'):
            sentinel = {item for item in self._sentinel_}
        else:
            sentinel = {self._sentinel_}

        item = self
        while item.int() not in sentinel:
            result = item.d
            yield result.l
            item = self.__walk_nextentry(result, iter(self._path_))
            if item.int() == 0: break
        return

SLIST_ENTRY._object_ = SLIST_ENTRY
SLIST_ENTRY._path_ = ()

class SLIST_HEADER(pstruct.type, versioned):
    def __Next(self):
        path = getattr(self, '_path_', SLIST_ENTRY._path_)
        target = getattr(self, '_object_', SLIST_ENTRY._object_)
        return dyn.clone(SLIST_ENTRY, _path_=path, _object_=target)

    def __init__(self, **attrs):
        super(SLIST_HEADER, self).__init__(**attrs)
        f = self._fields_ = []

        # HeaderX64
        if getattr(self, 'WIN64', False):
            f.extend([
                (pint.uint16_t, 'Depth'),
                (dyn.clone(pint.uint_t, length=6), 'Sequence'),
                (self.__Next, 'Next'),
            ])

        # DUMMYSTRUCTNAME
        else:
            f.extend([
                (self.__Next, 'Next'),
                (pint.uint16_t, 'Depth'),
                (pint.uint16_t, 'Sequence'),
            ])

    def summary(self):
        return 'Next->{:s} Depth:{:d} Sequence:{:d}'.format(self['Next'].summary(), self['Depth'].int(), self['Sequence'].int())

## Doubly-linked list
class LIST_ENTRY(pstruct.type):
    _fields_ = [
        (lambda self: self._object_, 'Flink'),
        (lambda self: self._object_, 'Blink'),
    ]
    _path_ = ()
    flink, blink = 'Flink', 'Blink'
    _object_ = _sentinel_ = None

    def __init__(self, **attrs):
        super(LIST_ENTRY, self).__init__(**attrs)
        if not issubclass(self._object_, ptype.pointer_t):
            cls = self.__class__
            raise AssertionError('{:s}._object_ is not a valid pointer'.format( '.'.join((self.__module__, cls.__name__)) ))

    def summary(self):
        return "F:{:#x}<->B:{:#x}".format(self['Flink'].int(), self['Blink'].int())

    def forward(self):
        if self[self.flink].int() == self._sentinel_:
            raise StopIteration, self
        return self[self.flink].d

    def backward(self):
        return self[self.blink].d

    def __walk_nextentry(self, state, path):
        try:
            # python doesn't tail-recurse anyways...
            key = next(path)
            state = self.__walk_nextentry(state[key], path)
        except StopIteration:
            pass
        return state

    def walk(self, direction=flink):
        '''Walks through a circular linked list'''
        if self._sentinel_ is None:
            sentinel = {self.getoffset()}
        elif isinstance(self._sentinel_, basestring):
            sentinel = {self[self._sentinel_].int()}
        elif hasattr(self._sentinel_, '__iter__'):
            sentinel = {item for item in self._sentinel_}
        else:
            sentinel = {self._sentinel_}

        item = self[direction]
        while item.int() != 0 and item.int() not in sentinel:
            result = item.d
            yield result.l
            item = self.__walk_nextentry(result, iter(self._path_))
            item = item[direction]
        return

    def moonwalk(self):
        return self.walk(direction=self.blink)

LIST_ENTRY._object_ = pointer(LIST_ENTRY)
LIST_ENTRY._path_ = ()

### Thread-Information-Block and other user primitives
class LCID(DWORD): pass

class LUID(pstruct.type):
    _fields_ = [
        (DWORD, 'LowPart'),
        (DWORD, 'HighPart'),
    ]
class PLUID(pointer(LUID)): pass

class KSPIN_LOCK(ULONG): pass

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
        (lambda self: pointer(NT_TIB), 'Self'),
    ]

class CLIENT_ID(pstruct.type):
    _fields_ = [
        (PVOID, 'UniqueProcess'),
        (PVOID, 'UniqueThread'),
    ]

### GUID (rfc4122) types and aliases
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
            d1 = ''.join(map('{:02x}'.format, map(six.byte2int, res[:2])) )
            d2 = ''.join(map('{:02x}'.format, map(six.byte2int, res[2:])) )
            return '-'.join((d1, d2))
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
        d4 = ''.join( map('{:02x}'.format, map(six.byte2int, _[:2])) )
        d5 = ''.join( map('{:02x}'.format, map(six.byte2int, _[2:])) )
        return '{{{:s}}}'.format('-'.join((d1, d2, d3, d4, d5)))

class GUID(rfc4122):
    _fields_ = [
        (transformation(t), n) for transformation, (t, n) in zip((pint.littleendian, pint.littleendian, pint.littleendian, pint.bigendian), rfc4122._fields_)
    ]

CLSID = UUID = GUID

### Time
class SYSTEMTIME(pstruct.type):
    _fields_ = [
        (WORD, 'wYear'),
        (WORD, 'wMonth'),
        (WORD, 'wDayOfWeek'),
        (WORD, 'wDay'),
        (WORD, 'wHour'),
        (WORD, 'wMinute'),
        (WORD, 'wSecond'),
        (WORD, 'wMilliseconds'),
    ]

class FILETIME(pstruct.type):
    _fields_ = [
        (DWORD, 'dwLowDateTime'),
        (DWORD, 'dwHighDateTime')
    ]

    def timestamp(self):
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * 2**32 + low

    def datetime(self):
        epoch = datetime.datetime(1601, 1, 1)
        return epoch + datetime.timedelta(microseconds=self.timestamp() / 1e1)

    def set(self, *dt, **fields):
        if not fields:
            dt, = dt or (datetime.datetime.now(),)
            delta = dt - datetime.datetime(1601, 1, 1)
            day_ms, second_ms, ms_100ns = map(math.trunc, (8.64e10, 1e6, 1e1))
            microseconds = delta.days * day_ms + delta.seconds * second_ms + delta.microseconds

            res = microseconds * ms_100ns
            fields['dwLowDateTime']  = (res // 2**0 ) & 0xffffffff
            fields['dwHighDateTime'] = (res // 2**32) & 0xffffffff
        return super(FILETIME, self).set(**fields)

    def summary(self):
        epoch, ts = datetime.datetime(1601, 1, 1), self.timestamp()
        ts_s, ts_hns = ts // 1e7, ts % 1e7
        ts_ns = ts_hns * 1e-7

        res = epoch + datetime.timedelta(seconds=ts_s)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.9f}".format(res.second + ts_ns).zfill(12), ts)

class EVENT_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (USHORT, 'Id'),
        (UCHAR, 'Version'),
        (UCHAR, 'Channel'),
        (UCHAR, 'Level'),
        (UCHAR, 'Opcode'),
        (USHORT, 'Task'),
        (ULONGLONG, 'Keyword'),
    ]

class EVENT_HEADER(pstruct.type):
    class Time(dynamic.union):
        class UserTime(pstruct.type): _fields_ = [(ULONG, name) for name in ('Kernel', 'User')]
        _fields_ = [
            (UserTime, 'System'),
            (ULONG64, 'Processor'),
        ]
    _fields_ = [
        (USHORT, 'Size'),
        (USHORT, 'HeaderType'),
        (USHORT, 'Flags'),
        (USHORT, 'EventProperty'),
        (ULONG, 'ThreadId'),
        (ULONG, 'ProcessId'),
        (LARGE_INTEGER, 'TimeStamp'),
        (GUID, 'ProviderId'),
        (EVENT_DESCRIPTOR, 'EventDescriptor'),
        (Time, 'Time'),
        (GUID, 'ActivityId'),
    ]

