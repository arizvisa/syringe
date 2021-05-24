import ptypes
from ptypes import *
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

### C99 types
class void(ptype.undefined): pass
class char(pint.int8_t): pass
class signed_char(pint.sint8_t): pass
class unsigned_char(pint.uint8_t): pass
class short(pint.int16_t): pass
class signed_short(pint.sint16_t): pass
class unsigned_short(pint.uint16_t): pass
class int(pint.int32_t): pass
class signed_int(pint.sint32_t): pass
class unsigned_int(pint.uint32_t): pass
class long_long(pint.int64_t): pass
class signed_long_long(pint.sint64_t): pass
class unsigned_long_long(pint.uint64_t): pass

## variable types
class long(pint.int_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class signed_long(pint.sint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class unsigned_long(pint.uint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class long_int(pint.int_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class signed_long_int(pint.sint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class unsigned_long_int(pint.uint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class long_signed_int(pint.sint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)
class long_unsigned_int(pint.uint_t):
    length = property(fget=lambda self: ptypes.Config.integer.size)

## general types
class short_int(short): pass
class signed_short_int(signed_short): pass
class unsigned_short_int(unsigned_short): pass

class star(ptype.pointer_t): pass
class size_t(long_unsigned_int): pass
class ptrdiff_t(long_int): pass

class void_star(star):
    _object_ = void

## stdint.h
class __u_char(unsigned_char): pass
class __u_short(unsigned_short): pass
class __u_int(unsigned_int): pass
class __u_long(unsigned_long_int): pass

class __int8_t(signed_char): pass
class __uint8_t(unsigned_char): pass
class __int16_t(signed_short_int): pass
class __uint16_t(unsigned_short_int): pass
class __int32_t(signed_int): pass
class __uint32_t(unsigned_int): pass
class __int64_t(signed_long_int): pass
class __uint64_t(unsigned_long_int): pass

class int8_t(__int8_t): pass
class int16_t(__int16_t): pass
class int32_t(__int32_t): pass
class int64_t(__int64_t): pass

class uint8_t(__uint8_t): pass
class uint16_t(__uint16_t): pass
class uint32_t(__uint32_t): pass
class uint64_t(__uint64_t): pass

### original types (old)
class mpointer_t(ptype.opointer_t):
    _path_ = ()
    def _calculate_(self, offset):
        res = self.new(self._object_).a
        for item in self._path_:
            res = res[item]
        return offset - res.getoffset()

### malloc types
class __libc_lock_t(unsigned_int): pass
libc_lock_define = __libc_lock_t

class INTERNAL_SIZE_T(size_t): pass
SIZE_SZ = INTERNAL_SIZE_T().a.blocksize()

DEFAULT_MMAP_THRESHOLD = 128 * 1024

MALLOC_ALIGNMENT = 0x10
MALLOC_ALIGN_MASK = MALLOC_ALIGNMENT - 1

NBINS = 128
NSMALLBINS = 64
SMALLBINS_WIDTH = MALLOC_ALIGNMENT

BINMAPSHIFT = 5
BITSPERMAP = pow(2, BINMAPSHIFT)
BINMAPSIZE = NBINS // BITSPERMAP

MIN_CHUNK_SIZE = 2 * SIZE_SZ + 2 * mpointer_t().a.blocksize()
MINSIZE = (MIN_CHUNK_SIZE + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK

request2size = lambda req: MINSIZE if req + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE else ((req + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)
fastbin_index = lambda sz: (sz >> (4 if SIZE_SZ == 8 else 3)) - 2
MAX_FAST_SIZE = 80 * SIZE_SZ // 4

NFASTBINS = fastbin_index(request2size(MAX_FAST_SIZE)) + 1

TCACHE_MAX_BINS = 64
TCACHE_FILL_COUNT = 7

class malloc_link(pstruct.type):
    _fields_ = [
        (lambda self: dyn.clone(mpointer_t, _object_=self._object_, _path_=self._path_), 'fd'),
        (lambda self: dyn.clone(mpointer_t, _object_=self._object_, _path_=self._path_), 'bk'),
    ]

    _object_, _path_ = None, ()

    def summary(self):
        return "fd:{:#x}<->bk:{:#x}".format(self['fd'].int(), self['bk'].int())

    def __next_entry(self, state, path):
        for step in path:
            state = state[step]
        return state

    def walk(self, direction='fd'):
        if direction not in self.keys():
            raise KeyError(direction)
        path, sentinel = [item for item in self._path_], {self.getoffset()}

        item = self[direction]
        while item.int() not in sentinel:
            result = item.d
            yield result.l
            item = self.__next_entry(result, iter(path))
            if any(not item[fld].int() for fld in ['fd', 'bk']):
                break
            item = item[direction]
        return
malloc_link._object_ = malloc_link

class mchunk(pstruct.type):
    class _size(dynamic.union):
        class _flags(pbinary.flags):
            _fields_ = [
                (61, 'unused'),
                (1, 'NON_MAIN_ARENA'),
                (1, 'IS_MMAPPED'),
                (1, 'PREV_INUSE'),
            ]

            def summary(self):
                flags = [name for name in ['NON_MAIN_ARENA', 'IS_MMAPPED', 'PREV_INUSE'] if self[name]]
                return ' '.join(flags)
        class _integer(unsigned_long):
            pass

        _fields_ = [
            (_flags, 'flags'),
            (_integer, 'integer'),
        ]

        def Size(self):
            res = self['integer'].int()
            return res & ~7

        def summary(self):
            res, flags = self.Size(), self['flags']
            return "{:#0{:d}x} {:+#x}{:s}".format(self['integer'].int(), 2 + self['integer'].size() * 2, res, " {!s}".format(flags.summary()) if flags.summary() else '')

    _fields_ = [
        (INTERNAL_SIZE_T, 'prev_size'),
        (_size, 'size'),
    ]

    def Flag(self, name):
        item = self['size']['flags']
        return item[name]

    def Size(self):
        item = self['size']
        return item.Size()

    def summary(self):
        prev, current = (self[fld] for fld in ['prev_size', 'size'])
        return "size={!s} prev_size={:+#x}".format(current.summary(), prev.int())

class tcache_entry(pstruct.type):
    _fields_ = [
        (lambda self: dyn.clone(star, _object_=self.__class__), 'next'),
        (lambda _: dyn.clone(star, _object_=tcache_perthread_struct), 'key'),
    ]

class tcache_perthread_struct(pstruct.type):
    _fields_ = [
        (dyn.array(uint16_t, TCACHE_MAX_BINS), 'counts'),
        (dyn.array(dyn.clone(star, _object_=tcache_entry), TCACHE_MAX_BINS), 'entries'),
    ]

# consolidate these things together
class malloc_chunk_free(pstruct.type):
    def __mem(self):
        res = self['mchunk'].li
        realsize = max(0, res.Size() - sum(self[fld].li.size() for fld in ['mchunk', 'freelink']))
        return dyn.block(realsize if res.Size() < DEFAULT_MMAP_THRESHOLD else ptype.undefined)

    _fields_ = [
        (mchunk, 'mchunk'),
        (void, 'freelink'),
        (__mem, 'mem'),
        (lambda self: dyn.clone(mpointer_t, _object_=self.__class__, _path_=['mem']), 'link'),
        (lambda self: dyn.clone(mpointer_t, _object_=self.__class__, _path_=['mem']), 'linksize'),
    ]

class malloc_chunk(pstruct.type):
    def __freelink(self):
        return dyn.clone(malloc_link, _object_=malloc_chunk, _path_=['freelink'])

    def __mem(self):
        res = self['mchunk'].li
        realsize = max(0, res.Size() - sum(self[fld].li.size() for fld in ['mchunk', 'freelink']))
        return dyn.block(realsize if res.Size() < DEFAULT_MMAP_THRESHOLD else ptype.undefined)

    _fields_ = [
        (mchunk, 'mchunk'),
        (__freelink, 'freelink'),
        (__mem, 'mem'),
        (mchunk, 'nextchunk'),
    ]

    def prev(self):
        cls, mchunk = self.__class__, self['mchunk']
        return self.new(cls, offset=self.getoffset() - mchunk['prev_size'].int())

    def next(self):
        cls, mchunk = self.__class__, self['mchunk']
        return self.new(cls, offset=self.getoffset() + mchunk.Size())

class malloc_chunk_free(malloc_chunk):
    def __mem(self):
        res = self['mchunk'].li
        realsize = max(0, res.Size() - sum(self[fld].li.size() for fld in ['mchunk', 'freelink']))
        return dyn.block(realsize if res.Size() < DEFAULT_MMAP_THRESHOLD else ptype.undefined)

    _fields_ = [
        (mchunk, 'mchunk'),
        (void, 'freelink'),
        (__mem, 'mem'),
        (mchunk, 'nextchunk'),
    ]

class malloc_chunk_fastbin(malloc_chunk_free):
    pass

class mchunkptr(mpointer_t):
    _object_ = malloc_chunk
    _path_ = ['freelink']

class mfastbinptr(mpointer_t):
    _object_ = malloc_chunk_fastbin

class mallinfo(pstruct.type):
    _fields_ = [
        (int, 'arena'), # non-mmapped space allocated from system
        (int, 'ordblks'), # number of free chunks
        (int, 'smblks'), # number of fastbin blocks
        (int, 'hblks'), # number of mmapped regions
        (int, 'hblkhd'), # space in mmapped regions
        (int, 'usmblks'), # always 0, preserved for backwards compatibility
        (int, 'fsmblks'), # space available in freed fastbin blocks
        (int, 'uordblks'), # total allocated space
        (int, 'fordblks'), # total free space
        (int, 'keepcost'), # top-most, releasable (via malloc_trim) space
    ]

class malloc_fastbins(parray.type):
    _object_ = mfastbinptr

class malloc_bins(parray.type):
    _object_ = dyn.clone(malloc_link, _object_=malloc_chunk, _path_=['freelink'])

class malloc_binmap(parray.type):
    _object_ = unsigned_int

class mstate(mpointer_t):
    _object_ = None     # assigned later

class malloc_state(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (30, 'UNUSED'),
            (1, 'NONCONTIGUOUS_BIT'),
            (1, 'RESERVED'),
        ]

    _fields_ = [
        (libc_lock_define, 'mutex'),
        (_flags, 'flags'),
        (int, 'have_fastchunks'),
        (dyn.align(8), 'alignment(fastbinsY)'),
        (dyn.clone(malloc_fastbins, length=NFASTBINS), 'fastbinsY'),
        (mchunkptr, 'top'),
        (mchunkptr, 'last_remainder'),
        (dyn.clone(malloc_bins, length=NBINS - 1), 'bins'),
        (dyn.clone(malloc_binmap, length=BINMAPSIZE), 'binmap'),
        (mstate, 'next'),
        (mstate, 'next_free'),
        (INTERNAL_SIZE_T, 'attached_threads'),
        (INTERNAL_SIZE_T, 'system_mem'),
        (INTERNAL_SIZE_T, 'max_system_mem'),
    ]

mstate._object_ = malloc_state  # defined prior

class malloc_par(pstruct.type):
    _fields_ = [
        (unsigned_long, 'trim_threshold'),
        (INTERNAL_SIZE_T, 'top_pad'),
        (INTERNAL_SIZE_T, 'mmap_threshold'),
        (INTERNAL_SIZE_T, 'arena_test'),
        (INTERNAL_SIZE_T, 'arena_max'),
        (int, 'n_mmaps'),
        (int, 'n_mmaps_max'),
        (int, 'max_n_mmaps'),
        (int, 'no_dyn_threshold'),
        (INTERNAL_SIZE_T, 'mmapped_mem'),
        (INTERNAL_SIZE_T, 'max_mmapped_mem'),
        (ptype.pointer_t, 'sbrk_base'),

        (size_t, 'tcache_bins'),
        (size_t, 'tcache_max_bytes'),
        (size_t, 'tcache_count'),
        (size_t, 'tcache_unsorted_limit'),
    ]

class heap_info(pstruct.type):
    def __reference(self):
        return dyn.clone(mpointer_t, _object_=heap_info)

    _fields_ = [
        (mstate, 'ar_ptr'),
        (__reference, 'prev'),
        (size_t, 'size'),
        (size_t, 'mprotect_size'),
        (dyn.padding(MALLOC_ALIGNMENT), 'pad'),     # -6 * sizeof(size_rt) & (MALLOC_ALIGNMENT - 1)
    ]

if __name__ == '__main__':
    pass
