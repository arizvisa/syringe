import sys, ptypes
from ptypes import *

from . import iotypes
from .datatypes import *

class _POOL_TYPE_PagedPool(pbinary.enum):
    _values_ = [
        ('NonPagedPool', 0x0000),
        ('PagedPool', 0x0001),
        ('NonPagedPoolMustSucceed', 0x0002),
        ('DontUseThisType', 0x0003),
        ('NonPagedPoolCacheAligned', 0x0004),
        ('PagedPoolCacheAligned', 0x0005),
        ('NonPagedPoolCacheAlignedMustS', 0x0006),
        ('MaxPoolType', 0x0007),
    ]

class _POOL_TYPE_NonPagedPool(pbinary.enum):
    _values_ = [
        ('NonPagedPoolBase', 0),
        ('NonPagedPoolBaseMustSucceed', 2),
        ('NonPagedPoolBaseCacheAligned', 4),
        ('NonPagedPoolBaseCacheAlignedMustS', 6),

        ('NonPagedPoolSession', 0x0020),
        ('PagedPoolSession', 0x0021),
        ('NonPagedPoolMustSucceedSession', 0x0022),
        ('DontUseThisTypeSession', 0x0023),
        ('NonPagedPoolCacheAlignedSession', 0x0024),
        ('PagedPoolCacheAlignedSession', 0x0025),
        ('NonPagedPoolCacheAlignedMustSSession', 0x0026),

        ('NonPagedPoolNx', 0x200),
        ('NonPagedPoolNxCacheAligned', 0x204),
        ('NonPagedPoolSessionNx', 0x220),
    ]

class SECTION_BASIC_INFORMATION(pstruct.type):
    _fields_ = [
        (PVOID, 'BaseAddress'),
        (ULONG, 'Attributes'),
        (LARGE_INTEGER, 'Size'),
    ]

class SECTION_IMAGE_INFORMATION(pstruct.type):
    _fields_ = [
        (PVOID, 'EntryPoint'),
        (ULONG, 'StackZeroBits'),
        (ULONG, 'StackReserved'),
        (ULONG, 'StackCommit'),
        (ULONG, 'ImageSubsystem'),
        (WORD, 'SubSystemVersionLow'),
        (WORD, 'SubSystemVersionHigh'),
        (ULONG, 'Unknown1'),
        (ULONG, 'ImageCharacteristics'),
        (ULONG, 'ImageMachineType'),
        (dyn.array(ULONG, 3), 'Unknown2'),
    ]

@pbinary.littleendian
class SEGMENT_FLAGS(pbinary.flags):
    _fields_ = [
        (10, 'TotalNumberOfPtes4132'),
        (1, 'ExtraSharedWowSubsections'),
        (1, 'LargePages'),
        (20, 'Spare'),
    ]

class EVENT_COUNTER(pstruct.type):
    def __Event(self):
        # lazy loading to prevent python's stupid module recursion issues
        from . import ketypes
        return ketypes.KEVENT
    _fields_ = [
        (ULONG, 'RefCount'),
        (__Event, 'Event'),
        (LIST_ENTRY, 'ListEntry'),
    ]

@pbinary.littleendian
class MMSECTION_FLAGS(pbinary.flags):
    _fields_ = [
        (1, 'BeingDeleted'),
        (1, 'BeingCreated'),
        (1, 'BeingPurged'),
        (1, 'NoModifiedWriting'),
        (1, 'FailAllIo'),
        (1, 'Image'),
        (1, 'Based'),
        (1, 'File'),
        (1, 'Networked'),
        (1, 'NoCache'),
        (1, 'PhysicalMemory'),
        (1, 'CopyOnWrite'),
        (1, 'Reserve'),
        (1, 'Commit'),
        (1, 'FloppyMedia'),
        (1, 'WasPurged'),
        (1, 'UserReference'),
        (1, 'GlobalMemory'),
        (1, 'DeleteOnClose'),
        (1, 'FilePointerNull'),
        (1, 'DebugSymbolsLoaded'),
        (1, 'SetMappedFileIoComplete'),
        (1, 'CollidedFlush'),
        (1, 'NoChange'),
        (1, 'filler0'),
        (1, 'ImageMappedInSystemSpace'),
        (1, 'UserWritable'),
        (1, 'Accessed'),
        (1, 'GlobalOnlyPerSession'),
        (1, 'Rom'),
        (1, 'WriteCombined'),
        (1, 'filler'),
    ]

@pbinary.littleendian
class MMSUBSECTION_FLAGS(pbinary.flags):
    _fields_ = [
        (1, 'ReadOnly'),
        (1, 'ReadWrite'),
        (1, 'SubsectionStatic'),
        (1, 'GlobalMemory'),
        (5, 'Protection'),
        (1, 'Spare'),
        (10, 'StartingSector4132'),
        (12, 'SectorEndOffset'),
    ]

@pbinary.littleendian
class MMSUBSECTION_FLAGS2(pbinary.flags):
    _fields_ = [
        (1, 'SubsectionAccessed'),
        (1, 'SubsectionConverted'),
        (30, 'Reserved'),
    ]

@pbinary.littleendian
class MMVAD_FLAGS(pbinary.flags):
    _fields_ = [
        (1, 'PrivateMemory'),
        (2, 'Spare'),
        (5, 'Protection'),
        (1, 'MemCommit'),
        (3, 'VadType'),
        (1, 'NoChange'),
        (19, 'CommitCharge'),
    ]

@pbinary.littleendian
class MMVAD_FLAGS2(pbinary.flags):
    _fields_ = [
        (1, 'CopyOnWrite'),
        (1, 'Inherit'),
        (1, 'ExtendableFile'),
        (1, 'LongVad'),
        (1, 'ReadOnly'),
        (1, 'MultipleSecured'),
        (1, 'OneSecured'),
        (1, 'SecNoChange'),
        (24, 'CommitCharge'),
    ]

@pbinary.littleendian
class MMVAD_FLAGS3(pbinary.flags):
    _fields_ = [
        (8, 'Spare2'),
        (15, 'LastSequentialTrim'),
        (1, 'SequentialAccess'),
        (1, 'Spare'),
        (1, 'Teb'),
        (6, 'PreferredNode'),
    ]

# FIXME: find the definition for MMVAD wherever it is or redefine it

class MMADDRESS_LIST(pstruct.type):
    _fields_ = [
        (ULONG_PTR, 'StartVpn'),
        (ULONG_PTR, 'EndVpn'),
    ]

class MMSECURE_ENTRY(pstruct.type):
    def __List(self):
        return dyn.clone(LIST_ENTRY, _path_=['List'], _object_=MMSECURE_ENTRY)
    _fields_ = [
        (ULONG_PTR, 'StartVpn'),
        (ULONG_PTR, 'EndVpn'),
        (__List, 'List'),
    ]

class CONTROL_AREA(pstruct.type):
    _fields_ = [
        (lambda self: P(SEGMENT), 'Segment'),
        (LIST_ENTRY, 'DereferenceList'),
        (ULONG, 'NumberOfSectionReferences'),
        (ULONG, 'NumberOfPfnReferences'),
        (ULONG, 'NumberOfMappedViews'),
        (ULONG, 'NumberOfSystemCacheViews'),
        (ULONG, 'NumberOfUserReferences'),
        (MMSECTION_FLAGS, 'Flags'),
        (P(iotypes.FILE_OBJECT), 'FilePointer'),
        (P(EVENT_COUNTER), 'WaitingForDeletion'),
        (USHORT, 'ModifiedWriteCount'),
        (USHORT, 'FlushInProgressCount'),
        (ULONG, 'WritableUserReferences'),
        (ULONG, 'QuadwordPad'),
    ]

class LARGE_CONTROL_AREA(pstruct.type):
    _fields_ = [
        (lambda self: P(SEGMENT), 'Segment'),
        (LIST_ENTRY, 'DereferenceList'),
        (ULONG, 'NumberOfSectionReferences'),
        (ULONG, 'NumberOfPfnReferences'),
        (ULONG, 'NumberOfMappedViews'),
        (ULONG, 'NumberOfSystemCacheViews'),
        (ULONG, 'NumberOfUserReferences'),
        (MMSECTION_FLAGS, 'Flags'),
        (P(iotypes.FILE_OBJECT), 'FilePointer'),
        (P(EVENT_COUNTER), 'WaitingForDeletion'),
        (USHORT, 'ModifiedWriteCount'),
        (USHORT, 'FlushInProgressCount'),
        (ULONG, 'WritableUserReferences'),
        (ULONG, 'QuadwordPad'),
        (ULONG, 'StartingFrame'),
        (LIST_ENTRY, 'UserGlobalList'),
        (ULONG, 'SessionId'),
    ]

class MMPTE(dynamic.union):
    _fields_ = [
        (ULONG, 'Long'),
        # TODO
        #(HARDWARE_PTE, 'Flush'),
        #(MMPTE_HARDWARE, 'Hard'),
        #(MMPTE_PROTOTYPE, 'Proto'),
        #(MMPTE_SOFTWARE, 'Soft'),
        #(MMPTE_TRANSITION, 'Trans'),
        #(MMPTE_SUBSECTION, 'Subsect'),
        #(MMPTE_LIST, 'List'),
    ]

class SUBSECTION(pstruct.type):
    _fields_ = [
        (P(CONTROL_AREA), 'ControlArea'),
        (MMSUBSECTION_FLAGS, 'SubsectionFlags'),
        (ULONG, 'StartingSector'),
        (ULONG, 'NumberOfFullSectors'),
        (P(MMPTE), 'SubsectionBase'),   # XXX: this should be an ptr to an array
        (ULONG, 'UnusedPtes'),
        (ULONG, 'PtesInSubsection'),
        (lambda self: P(SUBSECTION), 'NextSubsection'),
    ]

class SEGMENT_OBJECT(pstruct.type):
    _fields_ = [
        (PVOID, 'BaseAddress'),
        (ULONG, 'TotalNumberOfPtes'),
        (LARGE_INTEGER, 'SizeOfSegment'),
        (ULONG, 'NonExtendedPtes'),
        (ULONG, 'ImageCommitment'),
        (P(CONTROL_AREA), 'ControlArea'),
        (P(SUBSECTION), 'Subsection'),
        (P(LARGE_CONTROL_AREA), 'LargeControlArea'),
        (P(MMSECTION_FLAGS), 'MmSectionFlags'),
        (P(MMSUBSECTION_FLAGS), 'MmSubSectionFlags'),
    ]

class SECTION_OBJECT(pstruct.type):
    _fields_ = [
        (PVOID, 'StartingVa'),
        (PVOID, 'EndingVa'),
        (PVOID, 'LeftChild'),
        (PVOID, 'RightChild'),
        (P(SEGMENT_OBJECT), 'Segment'),
    ]
