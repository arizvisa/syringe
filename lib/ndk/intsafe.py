import ptypes, codecs
from ptypes import *

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
    length = property(fget=lambda self: (globals()['__int64'] if getattr(self, 'WIN64', False) else globals()['__int32']).length)
class unsigned___int3264(pint.uint_t):
    length = property(fget=lambda self: (unsigned___int64 if getattr(self, 'WIN64', False) else unsigned___int32).length)
class intptr_t(pint.int_t):
    length = property(fget=lambda self: (globals()['__int64'] if getattr(self, 'WIN64', False) else long).length)
class uintptr_t(pint.uint_t):
    length = property(fget=lambda self: (globals()['__int64'] if getattr(self, 'WIN64', False) else long).length)
class ptrdiff_t(pint.int_t):
    length = property(fget=lambda self: (globals()['__int64'] if getattr(self, 'WIN64', False) else int).length)
class ssize_t(pint.sint_t):
    length = property(fget=lambda self: (globals()['__int64'] if getattr(self, 'WIN64', False) else int).length)
class size_t(pint.uint_t):
    length = property(fget=lambda self: (unsigned___int64 if getattr(self, 'WIN64', False) else unsigned_int).length)

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

class CLSID(rfc4122):
    class _Data(pint.uint_t):
        def summary(self):
            return "{:0{:d}x}".format(self.int(), self.size() * 2)

    class _Data4(pint.uint_t):
        def summary(self):
            res = self.serialize()
            d1 = ''.join(map('{:02x}'.format, bytearray(res[:2])))
            d2 = ''.join(map('{:02x}'.format, bytearray(res[2:])))
            return '-'.join([d1, d2])

    def __Data(self, byteorder, length):
        class _Data(byteorder(self._Data)):
            pass
        _Data.length = length
        return _Data

    def __Data1(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data, length=4)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        return self.__Data(order, 4)

    def __Data2and3(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data, length=2)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        return self.__Data(order, 2)

    def __Data4(self):
        if not hasattr(self, 'byteorder'):
            return dyn.clone(self._Data4, length=8)
        if self.byteorder is ptypes.config.byteorder.bigendian:
            order = pint.bigendian
        elif self.byteorder is ptypes.config.byteorder.littleendian:
            order = pint.littleendian
        else:
            raise ValueError(self.byteorder)
        class _Data4(order(self._Data4)):
            length = 8
        return _Data4

    _fields_ = [
        (__Data1, 'Data1'),
        (__Data2and3, 'Data2'),
        (__Data2and3, 'Data3'),
        (__Data4, 'Data4'),
    ]
