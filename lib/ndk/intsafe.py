import ptypes, functools, codecs, math, datetime, time, builtins, sys
from ptypes import *
from ptypes import bitmap

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

    def set(self, *args, **fields):
        if not args:
            return super(rfc4122, self).set(**fields)

        [arg] = args
        if isinstance(arg, (''.__class__, u''.__class__)):
            string = arg[+1 : -1] if arg[:1] + arg[-1:] == '{}' else arg
            arg = time_low, time_mid, time_high_and_version, clock_seq, node = [builtins.int(component, 0x10) for component in string.split('-', 4)]

        # chop up the components and fit them into the right place.
        components = time_low, time_mid, time_high_and_version, clock_seq, node = arg
        time_low_ = bitmap.new(time_low, 8 * 4)
        time_mid_ = bitmap.new(time_mid, 4 * 4)
        time_high_and_version_ = bitmap.new(time_high_and_version, 4 * 4)
        clock_seq_ = bitmap.new(clock_seq, 4 * 4)
        node_ = bitmap.new(node, 4 * 12)

        # shove those values into the correct components
        Data1 = bitmap.value(time_low_)
        Data2 = bitmap.value(time_mid_)
        Data3 = bitmap.value(time_high_and_version_)
        Data4_ = bitmap.new(0, 0)
        Data4_ = bitmap.push(Data4_, clock_seq_)
        Data4_ = bitmap.push(Data4_, node_)
        Data4 = bytearray(map(bitmap.value, bitmap.split(Data4_, 8)))

        # assign our fields and ask the parent class to set them.
        fields['Data1'] = Data1
        fields['Data2'] = Data2
        fields['Data3'] = Data3
        fields['Data4'] = Data4
        return super(rfc4122, self).set(**fields)

    def str(self):
        time_low = '{:08X}'.format(self['Data1'].int())
        time_mid = '{:04X}'.format(self['Data2'].int())
        time_high_and_version = '{:04X}'.format(self['Data3'].int())
        _ = self['Data4'].serialize()
        clock_seq = ''.join( map('{:02X}'.format, bytearray(_[:2])) )   # clock_seq_hi_and_reserved, clock_seq_low
        node = ''.join( map('{:02X}'.format, bytearray(_[2:])) )
        return '{{{:s}}}'.format('-'.join([time_low, time_mid, time_high_and_version, clock_seq, node]))

    def __format__(self, spec):
        if self.value is None or not spec:
            return super(rfc4122, self).__format__(spec)

        prefix, spec, sizes = spec[:-1], spec[-1:], [4, 2, 2, 2, 8]
        if not prefix and spec in 'xX':
            iterable = ((integer, size) for integer, size in zip(self.iterate(), sizes))
            return '-'.join("{:0{:d}{:s}}".format(integer, 2 * size, spec) for integer, size in iterable)
        elif prefix in {'#', '#0'} and spec in 'xX':
            iterable = ((integer, size) for integer, size in zip(self.iterate(), sizes))
            integers, sizes = zip(*iterable)
            res = functools.reduce(lambda agg, index: agg * pow(2, 8 * sizes[index]) + integers[index], range(len(integers)), 0)
            return "{:{:s}{:d}{:s}}".format(res, prefix, 2 + 2 * sum(sizes), spec)
        elif spec in 'xXdon':
            iterable = ((integer, size) for integer, size in zip(self.iterate(), sizes))
            integers, sizes = zip(*iterable)
            res = functools.reduce(lambda agg, index: agg * pow(2, 8 * sizes[index]) + integers[index], range(len(integers)), 0)
            return "{:{:s}{:s}}".format(res, prefix, spec)
        elif spec in 's':
            iterable = ((integer, size) for integer, size in zip(self.iterate(), sizes))
            res = "{{{:s}}}".format('-'.join("{:0{:d}X}".format(integer, 2 * size) for integer, size in iterable))
            return "{:{:s}s}".format(res, prefix)
        return super(rfc4122, self).__format__(prefix + spec)

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
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s}{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.6f}".format(seconds).zfill(9), '' if sys.version_info.major < 3 else res.strftime('%z'), ts)

    def days(self):
        ts = self.timestamp()
        #864e11 = nanoseconds in day
        #864e9 = 100ns in day
        return ts * 125e-12 / 108
    def hours(self):
        ts = self.timestamp()
        return ts * 25e-11 / 9
    def minutes(self):
        ts = self.timestamp()
        return ts * 15e-9 / 9
    def seconds(self):
        ts = self.timestamp()
        return ts * 1e-7
    def milliseconds(self):
        ts = self.timestamp()
        return ts * 1e-4
    def microseconds(self):
        ts = self.timestamp()
        return ts * 1e-1

### Various bitmap types
class BitmapBitsArray(parray.type):
    _object_, length = ptype.undefined, 0

    # Make this type look sorta like a pbinary.array
    def bits(self):
        return self.size() << 3
    def bitmap(self):
        iterable = (bitmap.new(item.int(), 8 * item.size()) for item in self)
        return functools.reduce(bitmap.append, iterable, bitmap.zero)
    def check(self, index):
        bits = 8 * self.new(self._object_).a.size()
        res, offset = self[index // bits], index % bits
        return res.int() & pow(2, offset) and 1
    def scan(self, position):
        res = self.bitmap()
        return bitmap.scan(res, True, position)
    def scanreverse(self, position):
        res = self.bitmap()
        return bitmap.scanreverse(res, True, position)
    def iterate(self):
        '''iterate through the bitmap returning all the indices that are true'''
        for index in range(self.bits()):
            if self.check(index):
                yield index
            continue
        return
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

        items = reversed(bitmap.split(self.bitmap(), bits_per_row))

        width = len("{:x}".format(self.bits()))
        return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, i * bits_per_row, width, min(self.bits(), i * bits_per_row + bits_per_row) - 1, width, bitmap.string(item, reversed=True)) for i, item in enumerate(items)))

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
        return functools.reduce(bitmap.append, iterable, bitmap.zero)
    def check(self, index):
        res, offset = self[index >> 3], index & 7
        return ord(res) & pow(2, offset) and 1
    def scan(self, position):
        res = self.bitmap()
        return bitmap.scan(res, True, position)
    def scanreverse(self, position):
        res = self.bitmap()
        return bitmap.scanreverse(res, True, position)
    def iterate(self):
        '''iterate through the bitmap returning all the indices that are true'''
        for index in range(self.bits()):
            if self.check(index):
                yield index
            continue
        return
    def repr(self):
        return self.details()
    def summary(self):
        res = self.bitmap()
        return "{:s} ({:s}, {:d})".format(self.__element__(), bitmap.hex(res), bitmap.size(res))
    def details(self):
        bytes_per_row = 8
        iterable = (item for item in bitmap.string(self.bitmap(), reversed=True))
        rows = izip_longest(*[iterable] * 8 * bytes_per_row)
        res = map(lambda columns: (' ' if column is None else column for column in columns), rows)
        items = map(str().join, res)

        width = len("{:x}".format(self.bits()))
        return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, 8 * i * bytes_per_row, width, min(self.bits(), 8 * i * bytes_per_row + 8 * bytes_per_row) - 1, width, item) for i, item in enumerate(items)))
