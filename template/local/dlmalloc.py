import ptypes
from ptypes import *
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

class char(pint.uint8_t): pass
class schar(pint.sint8_t): pass
class uint(pint.uint32_t): pass
class sint(pint.sint32_t): pass
class ulong(pint.uint64_t): pass
class slong(pint.sint64_t): pass
class size_t(pint.uint64_t): pass
class pointer_t(ptype.opointer_t):
    _path_ = ()
    def _calculate_(self, offset):
        res = self.new(self._object_).a
        for item in self._path_:
            res = res[item]
        return offset - res.getoffset()

libc_lock_define = uint

class INTERNAL_SIZE_T(size_t): pass
SIZE_SZ = INTERNAL_SIZE_T().a.blocksize()

DEFAULT_MMAP_THRESHOLD = 128 * 1024

MALLOC_ALIGNMENT = 0x10
MALLOC_ALIGN_MASK = MALLOC_ALIGNMENT - 1

NBINS = 128
NSMALLBINS = 64
SMALLBINS_WIDTH = MALLOC_ALIGNMENT

BINMAPSHIFT = 5
BITSPERMAP = 2 ** BINMAPSHIFT
BINMAPSIZE = NBINS // BITSPERMAP

MIN_CHUNK_SIZE = 2 * SIZE_SZ + 2 * pointer_t().a.blocksize()
MINSIZE = (MIN_CHUNK_SIZE + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK

request2size = lambda req: MINSIZE if req + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE else ((req + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)
fastbin_index = lambda sz: (sz >> (4 if SIZE_SZ == 8 else 3)) - 2
MAX_FAST_SIZE = 80 * SIZE_SZ // 4

NFASTBINS = fastbin_index(request2size(MAX_FAST_SIZE)) + 1

class malloc_link(pstruct.type):
    _fields_ = [
        (lambda self: dyn.clone(pointer_t, _object_=self._object_, _path_=self._path_), 'fd'),
        (lambda self: dyn.clone(pointer_t, _object_=self._object_, _path_=self._path_), 'bk'),
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
        class _integer(ulong):
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

# consolidate these things together
class malloc_chunk_free(pstruct.type):
    def __mem(self):
        res = self['mchunk'].li
        realsize = max(0, res.Size() - sum(self[fld].li.size() for fld in ['mchunk', 'freelink']))
        return dyn.block(realsize if res.Size() < DEFAULT_MMAP_THRESHOLD else ptype.undefined)

    _fields_ = [
        (mchunk, 'mchunk'),
        (ptype.undefined, 'freelink'),
        (__mem, 'mem'),
        (lambda self: dyn.clone(pointer_t, _object_=self.__class__, _path_=['mem']), 'link'),
        (lambda self: dyn.clone(pointer_t, _object_=self.__class__, _path_=['mem']), 'linksize'),
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
        (ptype.undefined, 'freelink'),
        (__mem, 'mem'),
        (mchunk, 'nextchunk'),
    ]

class malloc_chunk_fastbin(malloc_chunk_free):
    pass

class mchunkptr(pointer_t):
    _object_ = malloc_chunk
    _path_ = ['freelink']

class mfastbinptr(pointer_t):
    _object_ = malloc_chunk_fastbin

class mallinfo(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'arena'), # non-mmapped space allocated from system
        (pint.uint32_t, 'ordblks'), # number of free chunks
        (pint.uint32_t, 'smblks'), # number of fastbin blocks
        (pint.uint32_t, 'hblks'), # number of mmapped regions
        (pint.uint32_t, 'hblkhd'), # space in mmapped regions
        (pint.uint32_t, 'usmblks'), # always 0, preserved for backwards compatibility
        (pint.uint32_t, 'fsmblks'), # space available in freed fastbin blocks
        (pint.uint32_t, 'uordblks'), # total allocated space
        (pint.uint32_t, 'fordblks'), # total free space
        (pint.uint32_t, 'keepcost'), # top-most, releasable (via malloc_trim) space
    ]

class malloc_fastbins(parray.type):
    _object_ = mfastbinptr

class malloc_bins(parray.type):
    _object_ = dyn.clone(malloc_link, _object_=malloc_chunk, _path_=['freelink'])

class malloc_binmap(parray.type):
    _object_ = uint

class mstate(pointer_t):
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
        (sint, 'have_fastchunks'),
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
        (ulong, 'trim_threshold'),
        (INTERNAL_SIZE_T, 'top_pad'),
        (INTERNAL_SIZE_T, 'mmap_threshold'),
        (INTERNAL_SIZE_T, 'arena_test'),
        (INTERNAL_SIZE_T, 'arena_max'),
        (sint, 'n_mmaps'),
        (sint, 'n_mmaps_max'),
        (sint, 'max_n_mmaps'),
        (sint, 'no_dyn_threshold'),
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
        return dyn.clone(pointer_t, _object_=heap_info)

    _fields_ = [
        (mstate, 'ar_ptr'),
        (__reference, 'prev'),
        (size_t, 'size'),
        (size_t, 'mprotect_size'),
        (dyn.padding(MALLOC_ALIGNMENT), 'pad'),     # -6 * sizeof(size_rt) & (MALLOC_ALIGNMENT - 1)
    ]

if __name__ == '__main__':
    pass
