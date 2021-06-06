import sys, math, datetime, time, itertools, functools, codecs

import ptypes
from ptypes import *
from ptypes import bitmap

from . import sdkddkver, winerror

izip_longest = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest
string_types = (str, unicode) if sys.version_info.major < 3 else (str,)

### versioned base-class
class versioned(ptype.base):
    '''
    This base class, or really a mixin, will propagate all version-related
    attributes to its children instances. This way the user can instantiate
    a type with the NTDDI_VERSION and WIN64 attributes set to whatever they
    desire and then every type can just check its own attributes in order to
    determine which structure variation it should use.
    '''
    NTDDI_VERSION = sdkddkver.NTDDI_VERSION
    WIN64 = sdkddkver.WIN64
    attributes = { 'NTDDI_VERSION': NTDDI_VERSION, 'WIN64': WIN64 }
    def __init__(self, **attrs):
        super(versioned, self).__init__(**attrs)
        self.attributes['NTDDI_VERSION'] = self.NTDDI_VERSION
        self.attributes['WIN64'] = self.WIN64

### C datatypes (microsoft)
class int(pint.int32_t): pass
class signed_int(pint.sint32_t): pass
class unsigned_int(pint.uint32_t): pass
class __int8(pint.int8_t): pass
class signed___int8(pint.sint8_t): pass
class unsigned___int8(pint.uint8_t): pass
class __int16(pint.int16_t): pass
class signed___int16(pint.sint16_t): pass
class unsigned___int16(pint.uint16_t): pass
class __int32(pint.int32_t): pass
class signed___int32(pint.sint32_t): pass
class unsigned___int32(pint.uint32_t): pass
class __int64(pint.int64_t): pass
class signed___int64(pint.sint64_t): pass
class unsigned___int64(pint.uint64_t): pass

class char(pint.int8_t): pass
class signed_char(pint.sint8_t): pass
class unsigned_char(pint.uint8_t): pass
class short(pint.int16_t): pass
class signed_short(pint.sint16_t): pass
class unsigned_short(pint.uint16_t): pass
class long(pint.int32_t): pass
class signed_long(pint.sint32_t): pass
class unsigned_long(pint.uint32_t): pass
class long_long(pint.int64_t): pass
class signed_long_long(pint.sint64_t): pass
class unsigned_long_long(pint.uint64_t): pass

class float(pfloat.single): pass
class double(pfloat.double): pass
class long_double(pfloat.double): pass

class void(ptype.undefined): pass
class bool(pint.int8_t, pint.enum): _values_ = [('false', 0)]

class wchar_t(pstr.wchar_t): pass
class __wchar_t(pstr.wchar_t): pass
class char8_t(pstr.char_t): encoding = codecs.lookup('utf-8')
class char16_t(pstr.wchar_t): pass
class char32_t(pstr.wchar_t): encoding = codecs.lookup('utf-32-le' if ptypes.Config.integer.order == ptypes.config.byteorder.littleendian else 'utf-32-be')

class __ptr32(ptype.pointer_t._value_): length = 4
class __ptr64(ptype.pointer_t._value_): length = 8

# aliases since dunder-prefixed symbols get mangled
class ptr32(__ptr32): pass
class ptr64(__ptr64): pass

class star(ptype.pointer_t, versioned):
    @property
    def _value_(self):
        return ptr64 if getattr(self, 'WIN64', False) else ptr32

class rstar(ptype.rpointer_t, versioned):
    @classmethod
    def typename(cls):
        return cls.__name__

    @property
    def _value_(self):
        return ptr64 if getattr(self, 'WIN64', False) else ptr32

    def decode(self, object, **attrs):
        root = ptype.force(self._baseobject_, self)
        base = root.getoffset() if isinstance(root, ptype.generic) else root().getoffset()
        t = ptr64 if getattr(self, 'WIN64', False) else ptr32
        return t().set(base + object.get())

class fstar(ptype.opointer_t, versioned):
    """This is typically used for LIST_ENTRY"""
    @property
    def _value_(self):
        return ptr64 if getattr(self, 'WIN64', False) else ptr32

    @classmethod
    def typename(cls):
        return cls.__name__

    _path_ = ()
    def _calculate_(self, offset):
        res = self.new(self._object_).a
        for p in self._path_: res = res[p]
        return offset - res.getoffset()

    def classname(self):
        res = getattr(self, '_object_', ptype.undefined) or ptype.undefined
        return self.typename() + '(' + res.typename() + (', _path_={!r})'.format(self._path_) if self._path_ else ')')

class ostar(ptype.opointer_t, versioned):
    @property
    def _value_(self):
        return ptr64 if getattr(self, 'WIN64', False) else ptr32

    @classmethod
    def typename(cls):
        return cls.__name__

    def classname(self):
        cls = self.__class__
        res = getattr(self, '_object_', ptype.undefined) or ptype.undefined
        return self.typename() + '(' + res.typename() + ')'

    def _calculate_(self, offset):
        raise NotImplementedError

    def summary(self):
        res = self.int()
        ptr, calculated = self._value_, self._calculate_(res)
        return u"({:s}*) {:+#x} : *{:#x}".format(ptr.__name__, res, calculated)

class void_star(star): _object_ = void

### Fixed-width integral types (stdint.h)
class int8_t(signed_char): pass
class uint8_t(unsigned_char): pass
class int16_t(short): pass
class uint16_t(unsigned_short): pass
class int32_t(int): pass
class uint32_t(unsigned_int): pass
class int64_t(long_long): pass
class uint64_t(unsigned_long_long): pass
class int_least8_t(signed_char): pass
class uint_least8_t(unsigned_char): pass
class int_least16_t(short): pass
class uint_least16_t(unsigned_short): pass
class int_least32_t(int): pass
class uint_least32_t(unsigned_int): pass
class int_least64_t(long_long): pass
class uint_least64_t(unsigned_long_long): pass
class int_fast8_t(signed_char): pass
class uint_fast8_t(unsigned_char): pass
class int_fast16_t(short): pass
class uint_fast16_t(unsigned_short): pass
class int_fast32_t(int): pass
class uint_fast32_t(unsigned_int): pass
class int_fast64_t(long_long): pass
class uint_fast64_t(unsigned_long_long): pass
class intmax_t(long_long): pass
class uintmax_t(unsigned_long_long): pass

# variable sized types
class __int3264(pint.int_t):
    length = property(fget=lambda self: (__int64 if getattr(self, 'WIN64', False) else __int32).length)
class unsigned___int3264(pint.uint_t):
    length = property(fget=lambda self: (unsigned___int64 if getattr(self, 'WIN64', False) else unsigned___int32).length)
class intptr_t(pint.int_t):
    length = property(fget=lambda self: (__int64 if getattr(self, 'WIN64', False) else long).length)
class uintptr_t(pint.uint_t):
    length = property(fget=lambda self: (__int64 if getattr(self, 'WIN64', False) else long).length)
class ptrdiff_t(pint.int_t):
    length = property(fget=lambda self: (__int64 if getattr(self, 'WIN64', False) else int).length)
class ssize_t(pint.sint_t):
    length = property(fget=lambda self: (__int64 if getattr(self, 'WIN64', False) else int).length)
class size_t(pint.uint_t):
    length = property(fget=lambda self: (unsigned___int64 if getattr(self, 'WIN64', False) else unsigned_int).length)

## pointer types and utilities
class pointer_t(star):
    @classmethod
    def typename(cls):
        return cls.__name__

class fpointer_t(fstar): pass
class rpointer_t(rstar): pass
class opointer_t(ostar): pass

## pointer utilities
def pointer(target, **attrs):
    attrs.setdefault('_object_', target)
    return dyn.clone(pointer_t, **attrs)
def fpointer(type, fieldname):
    return dyn.clone(fpointer_t, _object_=type, _path_=tuple(fieldname) if hasattr(fieldname, '__iter__') else (fieldname,))

def rpointer(target, base, **attrs):
    return dyn.clone(rpointer_t, _baseobject_=base, _object_=target, **attrs)
def opointer(target, Fcalculate, **attrs):
    return dyn.clone(opointer_t, _calculate_=Fcalculate, _object_=target, **attrs)

P = pointer

### intsafe.h
class CHAR(char): pass
class INT8(signed_char): pass
class UCHAR(unsigned_char): pass
class UINT8(unsigned_char): pass
class BYTE(unsigned_char): pass
class SHORT(short): pass
class INT16(signed_short): pass
class USHORT(unsigned_short): pass
class UINT16(unsigned_short): pass
class WORD(unsigned_short): pass
class INT(int): pass
class INT32(signed_int): pass
class UINT(unsigned_int): pass
class UINT32(unsigned_int): pass
class LONG(long): pass
class ULONG(unsigned_long): pass
class DWORD(unsigned_long): pass
class LONGLONG(__int64): pass
class LONG64(__int64): pass
class INT64(signed___int64): pass
class ULONGLONG(unsigned___int64): pass
class DWORDLONG(unsigned___int64): pass
class ULONG64(unsigned___int64): pass
class DWORD64(unsigned___int64): pass
class UINT64(unsigned___int64): pass

class INT_PTR(__int3264): pass
class UINT_PTR(unsigned___int3264): pass
class LONG_PTR(__int3264): pass
class ULONG_PTR(unsigned___int3264): pass

class DWORD_PTR(ULONG_PTR): pass
class SSIZE_T(LONG_PTR): pass
class SIZE_T(ULONG_PTR): pass

### typedefs.h
class VOID(void): pass
class PVOID(void_star):
    def classname(self):
        return self.typename()
#class LPVOID(PVOID): pass
#class CHAR(char): pass
class CCHAR(char): pass
#class PCHAR(P(CHAR)): pass
#class PSTR(P(pstr.szstring)): pass
#class LPSTR(PSTR): pass
#class PCSTR(P(pstr.szstring)): pass
#class LCPSTR(PCSTR): pass
#class UCHAR(unsigned_char): pass
#class PUCHAR(P(UCHAR)): pass
#class BYTE(unsigned_char): pass
#class LPBYTE(P(BYTE)): pass
class BOOLEAN(BYTE): pass
#class PBOOLEAN(P(BOOLEAN)): pass
#class UINT8(uint8_t): pass
#class SHORT(int16_t): pass
#class PSHORT(P(SHORT)): pass
#class USHORT(uint16_t): pass
#class PUSHORT(P(USHORT)): pass
#class PWORD(P(WORD)): pass
#class LPWORD(PWORD): pass
class WCHAR(wchar_t): pass
#class PWCHAR(P(WCHAR)): pass
class PWSTR(P(pstr.szwstring)): pass
#class LPWSTR(PWSTR): pass
#class UINT16(uint16_t): pass
#class PCWSTR(PWSTR): pass
#class LPCWSTR(PCWSTR): pass
#class INT(int32_t): pass
#class LONG(int32_t): pass
#class PLONG(P(LONG)): pass
#class LPLONG(PLONG): pass
class BOOL(int32_t): pass
class WINBOOL(BOOL): pass
#class INT32(int32_t): pass
#class UINT(uint32_t): pass
#class PUINT(P(UINT)): pass
#class LPUINT(PUINT): pass
#class ULONG(uint32_t): pass
#class PULONG(P(ULONG)): pass
#class LPULONG(PULONG): pass
#class DWORD(uint32_t): pass
#class PDWORD(P(DWORD)): pass
#class LPDWORD(PDWORD): pass
#class UINT32(uint32_t): pass
#class ULONG64(uint64_t): pass
#class DWORD64(uint64_t): pass
#class PDWORD64(P(DWORD64)): pass
#class UINT64(uint64_t): pass
#class ULONGLONG(uint64_t): pass
class FLOAT(float): pass
class DOUBLE(double): pass

class HANDLE(PVOID): pass
class HKEY(HANDLE): pass
#class PHKEY(P(HKEY)): pass
class HMODULE(HANDLE): pass
class HINSTANCE(HANDLE): pass
class NTSTATUS(winerror.NTSTATUS, LONG): pass
class POOL_TYPE(INT): pass
#class HRESULT(LONG): pass
#class SIZE_T(ULONG_PTR): pass
#class PSIZE_T(P(SIZE_T)): pass
class LANGID(WORD): pass

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
#class PLARGE_INTEGER(P(LARGE_INTEGER)): pass

class BSTR(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'length'),
        (lambda self: dyn.clone(pstr.wstring, length=self['length'].li.int()), 'string')
    ]

class HRESULT(dynamic.union):
    @pbinary.littleendian
    class _hresult(pbinary.struct):
        class _severity(pbinary.enum):
            length, _values_ = 1, [('TRUE', 1), ('FALSE', 0)]
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
        return "F:{:#x}<->B:{:#x}".format(self[self.flink].int(), self[self.blink].int())

    def forward(self):
        if self[self.flink].int() == self._sentinel_:
            raise StopIteration(self)
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
        elif isinstance(self._sentinel_, string_types):
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
        (LONG, 'HighPart'),
    ]

class EXCEPTION_REGISTRATION(pstruct.type):
    _fields_ = [
        (lambda self: pointer(EXCEPTION_REGISTRATION), 'Next'),
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

class NT_TIB(pstruct.type, versioned):
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
            res = self.serialize()
            d1 = ''.join(map('{:02x}'.format, bytearray(res[:2])))
            d2 = ''.join(map('{:02x}'.format, bytearray(res[2:])))
            return '-'.join([d1, d2])

    _fields_ = [
        (_Data1, 'Data1'),
        (_Data2and3, 'Data2'),
        (_Data2and3, 'Data3'),
        (_Data4, 'Data4'),
    ]

    def iterate(self):
        yield self['Data1'].int()
        yield self['Data2'].int()
        yield self['Data3'].int()
        data4 = self['Data4'].serialize()
        data4hi = bytearray(data4[:2])
        data4lo = bytearray(data4[2:])
        yield functools.reduce(lambda agg, item: agg * pow(2, 8) + item, data4hi)
        yield functools.reduce(lambda agg, item: agg * pow(2, 8) + item, data4lo)

    def components(self):
        return [item for item in self.iterate()]

    def summary(self, **options):
        if self.initializedQ():
            return self.str()
        return '{????????-????-????-????-????????????}'

    def str(self):
        d1 = '{:08x}'.format(self['Data1'].int())
        d2 = '{:04x}'.format(self['Data2'].int())
        d3 = '{:04x}'.format(self['Data3'].int())
        _ = self['Data4'].serialize()
        d4 = ''.join( map('{:02x}'.format, bytearray(_[:2])) )
        d5 = ''.join( map('{:02x}'.format, bytearray(_[2:])) )
        return '{{{:s}}}'.format('-'.join([d1, d2, d3, d4, d5]))

class GUID(rfc4122):
    _fields_ = [
        (Ftransform(__type), __fieldname) for Ftransform, (__type, __fieldname) in zip([pint.littleendian, pint.littleendian, pint.littleendian, pint.bigendian], rfc4122._fields_)
    ]
    def str(self):
        result = super(GUID, self).str()
        return result.upper()

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
        '''Return the number of 100ns represented by the instance.'''
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * pow(2, 32) + low

    def datetime(self):
        res, epoch = self.timestamp(), datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc if hasattr(datetime, 'timezone') else None)
        delta = datetime.timedelta(microseconds=res * 1e-1)
        return epoch + delta

    def get(self):
        return self.datetime()

    def set(self, *dt, **fields):
        cons = datetime.datetime
        if not fields:
            epoch = cons(1601, 1, 1, tzinfo=datetime.timezone.utc if hasattr(datetime, 'timezone') else None)
            dt, = dt or [cons.fromtimestamp(time.time(), datetime.timezone.utc if hasattr(datetime, 'timezone') else None)]
            result = dt - epoch

            microseconds = math.trunc(result.total_seconds() * 1e6)
            hundred_nanoseconds = res = math.trunc(microseconds * 1e1)

            fields['dwLowDateTime']  = (res // pow(2, 0)) & 0xffffffff
            fields['dwHighDateTime'] = (res // pow(2,32)) & 0xffffffff
            return self.set(**fields)
        return super(FILETIME, self).set(**fields)

    def summary(self):
        tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone))) if hasattr(datetime, 'timezone') else None
        try:
            dt = self.datetime()
            res = dt.astimezone(tzinfo) if tzinfo else dt
        except (ValueError, OverflowError):
            return super(FILETIME, self).summary()

        ts, seconds = self.timestamp(), res.second + res.microsecond * 1e-6
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s}{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.6f}".format(seconds).zfill(9), res.strftime('%z'), ts)

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

# Various bitmap types
class BitmapBitsArray(parray.type):
    _object_, length = ptype.undefined, 0

    # Make this type look sorta like a pbinary.array
    def bits(self):
        return self.size() << 3
    def bitmap(self):
        iterable = (bitmap.new(item.int(), 8 * item.size()) for item in self)
        return functools.reduce(bitmap.push, map(bitmap.reverse, iterable), bitmap.zero)
    def check(self, index):
        bits = 8 * self.new(self._object_).a.size()
        res, offset = self[index // bits], index % bits
        return res.int() & pow(2, offset) and 1
    def run(self):
        return self.bitmap()

    def repr(self):
        return self.details()
    def summary(self):
        res = self.bitmap()
        return "{:s} ({:s}, {:d})".format(self.__element__(), bitmap.hex(res), bitmap.size(res))
    def details(self):
        bytes_per_item = self.new(self._object_).a.size()
        bits_per_item = bytes_per_item * 8
        bytes_per_row = bytes_per_item * (1 if self.bits() < 0x200 else 2)
        bits_per_row = bits_per_item * (1 if self.bits() < 0x200 else 2)

        items = bitmap.split(self.bitmap(), bits_per_row)

        width = len("{:x}".format(self.bits()))
        return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, i * bits_per_row, width, min(self.bits(), i * bits_per_row + bits_per_row) - 1, width, bitmap.string(item)) for i, item in enumerate(items)))

class BitmapBitsUlong(BitmapBitsArray):
    _object_, length = ULONG, 0

class BitmapBitsBytes(ptype.block):
    _object_, length = UCHAR, 0
    def __element__(self):
        res = self.size()
        return "{:s}[{:d}]".format(self._object_.typename(), res)

    # Make this type look sorta like a pbinary.array
    def bits(self):
        return self.size() << 3
    def bitmap(self):
        iterable = (bitmap.new(item, 8) for item in bytearray(self.serialize()))
        return functools.reduce(bitmap.push, map(bitmap.reverse, iterable), bitmap.zero)
    def check(self, index):
        res, offset = self[index >> 3], index & 7
        return ord(res) & pow(2, offset) and 1
    def run(self):
        return self.bitmap()

    def repr(self):
        return self.details()
    def summary(self):
        res = self.bitmap()
        return "{:s} ({:s}, {:d})".format(self.__element__(), bitmap.hex(res), bitmap.size(res))
    def details(self):
        bytes_per_row = 8
        iterable = iter(bitmap.string(self.bitmap()))
        rows = izip_longest(*[iterable] * 8 * bytes_per_row)
        res = map(lambda columns: (' ' if column is None else column for column in columns), rows)
        items = map(str().join, res)

        width = len("{:x}".format(self.bits()))
        return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, 8 * i * bytes_per_row, width, min(self.bits(), 8 * i * bytes_per_row + 8 * bytes_per_row) - 1, width, item) for i, item in enumerate(items)))

class FLOATING_SAVE_AREA(pstruct.type):
    _fields_ = [
        (DWORD, 'ControlWord'),
        (DWORD, 'StatusWord'),
        (DWORD, 'TagWord'),
        (DWORD, 'ErrorOffset'),
        (DWORD, 'ErrorSelector'),
        (DWORD, 'DataOffset'),
        (DWORD, 'DataSelector'),
        (dyn.array(BYTE, 80), 'RegisterArea'),
        (DWORD, 'Spare0'),
    ]

class M128A(pstruct.type):
    _fields_ = [
        (ULONGLONG, 'Low'),
        (LONGLONG, 'High'),
    ]

class XSAVE_FORMAT(pstruct.type):
    _fields_ = [
        (WORD, 'ControlWord'),
        (WORD, 'StatusWord'),
        (BYTE, 'TagWord'),
        (BYTE, 'Reserved1'),
        (WORD, 'ErrorOpcode'),
        (DWORD, 'ErrorOffset'),
        (WORD, 'ErrorSelector'),
        (WORD, 'Reserved2'),
        (DWORD, 'DataOffset'),
        (WORD, 'DataSelector'),
        (WORD, 'Reserved3'),
        (DWORD, 'MxCsr'),
        (DWORD, 'MxCsr_Mask'),
        (dyn.array(M128A, 8), 'FloatRegisters'),
        (dyn.array(M128A, 16), 'XmmRegisters'),
        (dyn.array(BYTE, 96), 'Reserved4'),
    ]

class XMM_SAVE_AREA32(XSAVE_FORMAT): pass
class XMM_REGISTER_AREA(pstruct.type):
    _fields_ = [
        (dyn.array(M128A, 2), 'Header'),
        (dyn.array(M128A, 8), 'Legacy'),
        (M128A, 'Xmm0'),
        (M128A, 'Xmm1'),
        (M128A, 'Xmm2'),
        (M128A, 'Xmm3'),
        (M128A, 'Xmm4'),
        (M128A, 'Xmm5'),
        (M128A, 'Xmm6'),
        (M128A, 'Xmm7'),
        (M128A, 'Xmm8'),
        (M128A, 'Xmm9'),
        (M128A, 'Xmm10'),
        (M128A, 'Xmm11'),
        (M128A, 'Xmm12'),
        (M128A, 'Xmm13'),
        (M128A, 'Xmm14'),
        (M128A, 'Xmm15'),
    ]

class CONTEXT(pstruct.type, versioned):
    class FloatState(dynamic.union):
        _fields_ = [
            (XMM_SAVE_AREA32, 'FltSave'),
            (XMM_REGISTER_AREA, 'FltRegister'),
        ]

    def __init__(self, **attrs):
        super(CONTEXT, self).__init__(**attrs)

        if getattr(self, 'WIN64', False):
            _fields_ = [
                (DWORD64, 'P1Home'),
                (DWORD64, 'P2Home'),
                (DWORD64, 'P3Home'),
                (DWORD64, 'P4Home'),
                (DWORD64, 'P5Home'),
                (DWORD64, 'P6Home'),
                (DWORD, 'ContextFlags'),
                (DWORD, 'MxCsr'),
                (WORD, 'SegCs'),
                (WORD, 'SegDs'),
                (WORD, 'SegEs'),
                (WORD, 'SegFs'),
                (WORD, 'SegGs'),
                (WORD, 'SegSs'),
                (DWORD, 'EFlags'),
                (DWORD64, 'Dr0'),
                (DWORD64, 'Dr1'),
                (DWORD64, 'Dr2'),
                (DWORD64, 'Dr3'),
                (DWORD64, 'Dr6'),
                (DWORD64, 'Dr7'),
                (DWORD64, 'Rax'),
                (DWORD64, 'Rcx'),
                (DWORD64, 'Rdx'),
                (DWORD64, 'Rbx'),
                (DWORD64, 'Rsp'),
                (DWORD64, 'Rbp'),
                (DWORD64, 'Rsi'),
                (DWORD64, 'Rdi'),
                (DWORD64, 'R8'),
                (DWORD64, 'R9'),
                (DWORD64, 'R10'),
                (DWORD64, 'R11'),
                (DWORD64, 'R12'),
                (DWORD64, 'R13'),
                (DWORD64, 'R14'),
                (DWORD64, 'R15'),
                (DWORD64, 'Rip'),
                (self.FloatState, 'FltState'),
                (dyn.array(M128A, 26), 'VectorRegister'),
                (DWORD64, 'VectorControl'),
                (DWORD64, 'DebugControl'),
                (DWORD64, 'LastBranchToRip'),
                (DWORD64, 'LastBranchFromRip'),
                (DWORD64, 'LastExceptionToRip'),
                (DWORD64, 'LastExceptionFromRip'),
            ]
        else:
            _fields_ = [
                (DWORD, 'ContextFlags'),
                (DWORD, 'Dr0'),
                (DWORD, 'Dr1'),
                (DWORD, 'Dr2'),
                (DWORD, 'Dr3'),
                (DWORD, 'Dr6'),
                (DWORD, 'Dr7'),
                (FLOATING_SAVE_AREA, 'FloatSave'),
                (DWORD, 'SegGs'),
                (DWORD, 'SegFs'),
                (DWORD, 'SegEs'),
                (DWORD, 'SegDs'),
                (DWORD, 'Edi'),
                (DWORD, 'Esi'),
                (DWORD, 'Ebx'),
                (DWORD, 'Edx'),
                (DWORD, 'Ecx'),
                (DWORD, 'Eax'),
                (DWORD, 'Ebp'),
                (DWORD, 'Eip'),
                (DWORD, 'SegCs'),
                (DWORD, 'EFlags'),
                (DWORD, 'Esp'),
                (DWORD, 'SegSs'),
                (dyn.array(BYTE, 512), 'ExtendedRegisters'),
            ]
        self._fields_ = _fields_

if __name__ == '__main__':
    import ptypes
    data = b'\x6b\xa7\xb8\x10\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x6ba7b810, 0x9dad, 0x11d1, 0x80b4, 0x00c04fd430c8]):
        raise AssertionError

    data = b'\x7d\x44\x48\x40\x9d\xc0\x11\xd1\xb2\x45\x5f\xfd\xce\x74\xfa\xd2'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x7d444840, 0x9dc0, 0x11d1, 0xb245, 0x5ffdce74fad2]):
        raise AssertionError

    data = b'\x6b\xa7\xb8\x10\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x6ba7b810, 0x9dad, 0x11d1, 0x80b4, 0x00c04fd430c8]):
        raise AssertionError

    data = b'\x6b\xa7\xb8\x11\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x6ba7b811, 0x9dad, 0x11d1, 0x80b4, 0x00c04fd430c8]):
        raise AssertionError

    data = b'\x6b\xa7\xb8\x12\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x6ba7b812, 0x9dad, 0x11d1, 0x80b4, 0x00c04fd430c8]):
        raise AssertionError

    data = b'\x6b\xa7\xb8\x14\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8'
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x6ba7b814, 0x9dad, 0x11d1, 0x80b4, 0x00c04fd430c8]):
        raise AssertionError

    data = b'\x78\x56\x34\x12\x34\x12\x78\x56' + b'\x12\x34\x56\x78\x12\x34\x56\x78'
    data = b'\x12\x34\x56\x78' * 4
    instance = rfc4122(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x12345678, 0x1234, 0x5678, 0x1234, 0x567812345678]):
        raise AssertionError

    data = b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00F'
    instance = GUID(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x21401, 0, 0, 0xc000, 0x46]):
        raise AssertionError

    data = b'\x00\x67\x61\x56\x54\xC1\xCE\x11\x85\x53\x00\xAA\x00\xA1\xF9\x5B'
    instance = CLSID(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x56616700, 0xc154, 0x11ce, 0x8553, 0x00aa00a1f95b]):
        raise AssertionError

    data = b'\x91\x22\xdb\xb2\xe8\x8f\x02\x45\xa2\x05\x56\xa2\x84\x96\xd4\x42'
    instance = GUID(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0xB2DB2291, 0x8FE8, 0x4502, 0xA205, 0x56A28496D442]):
        raise AssertionError

    data = b'\x01\x00\x00\x00\x21\x07\xd3\x11\x44\x86\xc8\xc1\xca\x00\x00\x00'
    instance = GUID(source=ptypes.prov.bytes(data)).l
    if not([item for item in instance.iterate()] == [0x00000001, 0x0721, 0x11d3, 0x4486, 0xC8C1CA000000]):
        raise AssertionError
