import ptypes
from ptypes import *

from .dtyp import *

class _POOL_TYPE(pbinary.enum):
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
class POOL_TYPE16(_POOL_TYPE):
    width = 16

@pbinary.littleendian
class POOL_TYPE32(_POOL_TYPE):
    width = 32

class _POOL_HEADER(pstruct.type, versioned):
    class _Ulong1(pbinary.struct):
        _fields_ = [
            (dyn.clone(_POOL_TYPE, width=7), 'PoolType'),
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
            (dyn.clone(_POOL_TYPE, width=8), 'PoolType'),
            (8, 'BlockSize'),
            (8, 'PoolIndex'),
            (8, 'PreviousSize'),
        ]

    def __init__(self, **attrs):
        super(_POOL_HEADER, self).__init__(**attrs)
        self._fields_ = res = []

        ulong1 = _POOL_HEADER._Ulong164 if getattr(self, 'WIN64', False) else _POOL_HEADER._Ulong1

        res.extend([
            (pbinary.littleendian(ulong1), 'Ulong1'),
            (dyn.clone(pstr.string, length=4), 'PoolTag'),
        ])

        if getattr(self, 'WIN64', False):
            res.append((PVOID, 'ProcessBilled'))
        return

    _fields_ = [
        (_Ulong1, 'Ulong1'),
        (dyn.clone(pstr.string, length=4), 'PoolTag'),
    ]

    def summary(self):
        res = self['Ulong1']
        return "\"{:s}\" {:s}".format(self['PoolTag'].str().encode('escape_unicode').replace('"', '\\"'), res.summary())

class _POOL_FREE_CHUNK(pstruct.type, versioned): pass
class _POOL_FREE_CHUNK_LIST_ENTRY(LIST_ENTRY):
    _object_ = fptr(_POOL_FREE_CHUNK, 'ListEntry')
    _path_ = ('ListEntry',)

_POOL_FREE_CHUNK._fields_ = [
    (_POOL_HEADER, 'Header'),
    (_POOL_FREE_CHUNK_LIST_ENTRY, 'ListEntry'),
]

class _POOL_DESCRIPTOR(pstruct.type, versioned):
    def __ListHeads(self):
        PAGE_SIZE = 2**12
        POOL_BLOCK_SIZE = 16 if getattr(self, 'WIN64', False) else 8
        POOL_LISTS_PER_PAGE = PAGE_SIZE / POOL_BLOCK_SIZE
        return dyn.array(_POOL_FREE_CHUNK_LIST_ENTRY, POOL_LISTS_PER_PAGE)

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

class _GENERAL_LOOKASIDE(pstruct.type):
    _fields_ = [
        (dyn.clone(SLIST_HEADER, _object_=_POOL_FREE_CHUNK, _path_=('ListEntry',)), 'ListHead'),
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

class _PP_LOOKASIDE_LIST(pstruct.type):
    _fields_ = [
        (P(_GENERAL_LOOKASIDE), 'P'),
        (P(_GENERAL_LOOKASIDE), 'L'),
    ]
