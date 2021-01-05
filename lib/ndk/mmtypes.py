import sys, ptypes
from ptypes import *

from .datatypes import *

class POOL_TYPE(pbinary.enum):
    _values_ = [
        ('NonPagedPool', 0x0000),
        ('PagedPool', 0x0001),
        ('NonPagedPoolMustSucceed', 0x0002),
        ('DontUseThisType', 0x0003),
        ('NonPagedPoolCacheAligned', 0x0004),
        ('PagedPoolCacheAligned', 0x0005),
        ('NonPagedPoolCacheAlignedMustS', 0x0006),
        ('MaxPoolType', 0x0007),
        ('NonPagedPoolSession', 0x0020),
        ('PagedPoolSession', 0x0021),
        ('NonPagedPoolMustSucceedSession', 0x0022),
        ('DontUseThisTypeSession', 0x0023),
        ('NonPagedPoolCacheAlignedSession', 0x0024),
        ('PagedPoolCacheAlignedSession', 0x0025),
        ('NonPagedPoolCacheAlignedMustSSession', 0x0026),
    ]

@pbinary.littleendian
class POOL_TYPE16(POOL_TYPE):
    width = 16

@pbinary.littleendian
class POOL_TYPE32(POOL_TYPE):
    width = 32

class POOL_HEADER(pstruct.type, versioned):
    class _Ulong1(pbinary.struct):
        _fields_ = [
            (dyn.clone(POOL_TYPE, width=7), 'PoolType'),
            (9, 'BlockSize'),
            (7, 'PoolIndex'),
            (9, 'PreviousSize'),
        ]

        def summary(self):
            res = []
            res.append("Type={:s}({:d})".format(self.item('PoolType').str(), self.item('PoolType').int()))
            res.append("Index={:d}".format(self['PoolIndex']))
            res.append("PreviousSize={:#x}".format(self['PreviousSize']))
            res.append("BlockSize={:#x}".format(self['BlockSize']))
            return ' '.join(res)

    class _Ulong164(_Ulong1):
        _fields_ = [
            (dyn.clone(POOL_TYPE, width=8), 'PoolType'),
            (8, 'BlockSize'),
            (8, 'PoolIndex'),
            (8, 'PreviousSize'),
        ]

    def __Ulong1(self):
        res = POOL_HEADER._Ulong164 if getattr(self, 'WIN64', False) else POOL_HEADER._Ulong1
        return pbinary.littleendian(res)

    _fields_ = [
        (__Ulong1, 'Ulong1'),
        (dyn.clone(pstr.string, length=4), 'PoolTag'),
        (lambda self: PVOID if getattr(self, 'WIN64', False) else pint.uint_t, 'ProcessBilled'),
    ]

    def summary(self):
        res, tag = self['Ulong1'], self['PoolTag'].str()
        encoded = tag.encode('unicode_escape')
        return "\"{:s}\" {:s}".format(encoded.decode(sys.getdefaultencoding()).replace('"', '\\"'), res.summary())

class POOL_FREE_CHUNK(pstruct.type, versioned): pass
class POOL_FREE_CHUNK_LIST_ENTRY(LIST_ENTRY):
    _object_ = fptr(POOL_FREE_CHUNK, 'ListEntry')
    _path_ = ('ListEntry',)

POOL_FREE_CHUNK._fields_ = [
    (POOL_HEADER, 'Header'),
    (POOL_FREE_CHUNK_LIST_ENTRY, 'ListEntry'),
]

class POOL_DESCRIPTOR(pstruct.type, versioned):
    def __ListHeads(self):
        PAGE_SIZE = 2**12
        POOL_BLOCK_SIZE = 16 if getattr(self, 'WIN64', False) else 8
        POOL_LISTS_PER_PAGE = PAGE_SIZE // POOL_BLOCK_SIZE
        return dyn.array(POOL_FREE_CHUNK_LIST_ENTRY, POOL_LISTS_PER_PAGE)

    _fields_ = [
        (POOL_TYPE32, 'PoolType;'),
        (ULONG, 'PoolIndex;'),
        (ULONG, 'RunningAllocs;'),
        (ULONG, 'RunningDeAllocs;'),
        (ULONG, 'TotalPages;'),
        (ULONG, 'TotalBigPages;'),
        (ULONG, 'Threshold;'),
        (PVOID, 'LockAddress;'),
        (PVOID, 'PendingFrees;'),
        (LONG, 'PendingFreeDepth;'),
        (__ListHeads, 'ListHeads'),
    ]

class GENERAL_LOOKASIDE(pstruct.type):
    _fields_ = [
        (dyn.clone(SLIST_HEADER, _object_=POOL_FREE_CHUNK, _path_=('ListEntry',)), 'ListHead'),
        (UINT16, 'Depth'),
        (UINT16, 'MaximumDepth'),
        (ULONG32, 'TotalAllocates'),
        (ULONG32, 'AllocateMissesOrHits'),
        (ULONG32, 'TotalFrees'),
        (ULONG32, 'FreeMissesOrHits'),
        (POOL_TYPE32, 'Type'),
        (dyn.clone(pstr.string, length=4), 'Tag'),
        (ULONG32, 'Size'),
        (PVOID, 'Allocate'),
        (PVOID, 'Free'),
        (LIST_ENTRY, 'ListEntry'),
        (ULONG32, 'LastTotalAllocates'),
        (ULONG32, 'LastAllocateMissesOrHits'),
        (dyn.array(ULONG32, 2), 'Future'),
    ]

class PP_LOOKASIDE_LIST(pstruct.type):
    _fields_ = [
        (P(GENERAL_LOOKASIDE), 'P'),
        (P(GENERAL_LOOKASIDE), 'L'),
    ]
