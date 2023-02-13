import sys, ptypes
from ptypes import *

from . import iotypes
from .datatypes import *

class _MI_SYSTEM_VA_TYPE(pint.enum):
    _values_ = [
        ('MiVaUnused',  0),
        ('MiVaSessionSpace',  1),
        ('MiVaProcessSpace',  2),
        ('MiVaBootLoaded',  3),
        ('MiVaPfnDatabase',  4),
        ('MiVaNonPagedPool',  5),
        ('MiVaPagedPool',  6),
        ('MiVaSpecialPoolPaged',  7),
        ('MiVaSystemCache',  8),
        ('MiVaSystemPtes',  9),
        ('MiVaHal',  10),
        ('MiVaFormerlySessionGlobalSpace',  11),
        ('MiVaDriverImages',  12),
        ('MiVaSystemPtesLarge',  13),
        ('MiVaKernelStacks',  14),
        ('MiVaSecureNonPagedPool',  15),
        ('MiVaKernelShadowStacks',  16),
        ('MiVaKasan',  17),
        ('MiVaMaximumType',  18),
    ]

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
pbinary.partial(_objects_=pbinary.flags, _fields_=[(1,'hi'),(31,'no')]).load(source=ptypes.prov.bytes(b'\x80\x00\x00\x01'))
class SECTION_IMAGE_INFORMATION(pstruct.type, versioned):
    class _ImageFlags(pbinary.flags):
        _fields_ = [
            (1, 'ComPlusNativeReady'),
            (1, 'ComPlusILOnly'),
            (1, 'ImageDynamicallyRelocated'),
            (1, 'ImageMappedFlat'),
            (1, 'BaseBelow4gb'),
            (1, 'ComPlusPrefer32bit'),
            (2, 'Reserved'),
        ]
    def __init__(self, **attrs):
        super(SECTION_IMAGE_INFORMATION, self).__init__(**attrs)
        integer = ULONG if not getattr(self, 'WIN64', False) else ULONGLONG
        f = self._fields_ = [
            (PVOID, 'TransferAddress'),
            (ULONG, 'StackZeroBits'),
            (dyn.block(0 if not getattr(self, 'WIN64', False) else 4), 'padding(StackZeroBits)'),
            (integer, 'MaximumStackSize'),
            (integer, 'CommittedStackSize'),
        ]

        f.extend([
            (ULONG, 'SubSystemType'),
            (USHORT, 'SubSystemMinorVersion'),
            (USHORT, 'SubSystemMajorVersion'),
        ])

        if not getattr(self, 'WIN64', False):
            f.extend([
                (ULONG, 'GpValue'),
            ])
        else:
            f.extend([
                (USHORT, 'MajorOperatingSystemVersion'),
                (USHORT, 'MinorOperatingSystemVersion'),
            ])

        f.extend([
            (USHORT, 'ImageCharacteristics'),
            (USHORT, 'DllCharacteristics'),
            (USHORT, 'Machine'),
            (UCHAR, 'ImageContainsCode'),
            (UCHAR, 'ImageFlags'),  # FIXME
            (ULONG, 'LoaderFlags'),
            (ULONG, 'ImageFileSize'),
            (ULONG, 'CheckSum'),
        ])

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

class MMPTE_HIGHLOW(pstruct.type):
    _fields_ = [
        (ULONG, 'LowPart'),
        (ULONG, 'HighPart'),
    ]

class HARDWARE_PTE(pbinary.flags, versioned):
    '''HARDWARE_PTE, HARDWARE_PTE_X86, HARDWARE_X86PAE'''
    def __init__(self, **attrs):
        super(HARDWARE_PTE, self).__init__(**attrs)
        f = self._fields_ = [
            (1, 'Valid'),
            (1, 'Write'),
            (1, 'Owner'),
            (1, 'WriteThrough'),
            (1, 'CacheDisable'),
            (1, 'Accessed'),
            (1, 'Dirty'),
            (1, 'LargePage'),
            (1, 'Global'),
            (1, 'CopyOnWrite'),
            (1, 'Prototype'),
            (1, 'reserved0'),
        ]

        # WIN32
        if not getattr(self, 'WIN64', False):
            return f.append((20, 'PageFrameNumber'))

        # PAE
        if getattr(self, 'PAE', False):

            # PAE < 5.1
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WINXP:
                f.extend([
                    (24, 'PageFrameNumber'),
                    (28, 'reserved1'),
                ])

            # PAE < 1703
            elif self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_RS2:
                f.extend([
                    (26, 'PageFrameNumber'),
                    (26, 'reserved1'),
                ])

            # PAE >= 1703
            else:
                f.extend([
                    (26, 'PageFrameNumber'),
                    (25, 'reserved1'),
                    (1, 'NoExecute'),
                ])
            return

        # WIN64
        if getattr(self, 'WIN64', False):

            # WIN64 <= early 6.1
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WIN7:
                f.extend([
                    (28, 'PageFrameNumber'),
                    (12, 'reserved1'),
                ])

            # WIN64 > early 6.1 (late)
            else:
                f.extend([
                    (36, 'PageFrameNumber'),
                    (4, 'reserved1'),
                ])

            return f.extend([
                (11, 'SoftwareWsIndex'),
                (1, 'NoExecute'),
            ])
        raise NotImplementedError(self.NTDDI_VERSION)

class MMPTE_HARDWARE(pbinary.flags, versioned):
    def __init__(self, **attrs):
        super(MMPTE_HARDWARE, self).__init__(**attrs)
        f = self._fields_ = [
            (1, 'Valid'),
        ]

        # FIXME: UP
        if False and sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
            f += [(1, 'Write')]
        # MP
        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN6:
            f += [(1, 'Writable')]
        else:
            f += [(1, 'Dirty1')]

        f.extend([
            (1, 'Owner'),
            (1, 'WriteThrough'),
            (1, 'CacheDisable'),
            (1, 'Accessed'),
            (1, 'Dirty'),
            (1, 'LargePage'),
            (1, 'Global'),
            (1, 'CopyOnWrite'),
        ])

        # WIN64 < 6.0
        if getattr(self, 'WIN64', False) and sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN6:
            f += [(1, 'Prototype')]
        # WIN64 > 6.0
        elif getattr(self, 'WIN64', False):
            f += [(1, 'Unused')]
        # WIN32
        else:
            f += [(1, 'Prototype')]

        # FIXME: UP
        if False and sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN6:
            f += [
                (1, 'reserved' + ('0' if getattr(self, 'WIN64', False) else ''))
            ]
        # MP
        else:
            f += [(1, 'Write')]

        # WIN32
        if not getattr(self, 'WIN64', False):
            return f.append((20, 'PageFrameNumber'))

        # PAE
        if getattr(self, 'PAE', False):

            # PAE < 5.1
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WINXP:
                f.extend([
                    (24, 'PageFrameNumber'),
                    (28, 'reserved1'),
                ])

            # PAE < 1703
            elif self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_RS2:
                f.extend([
                    (26, 'PageFrameNumber'),
                    (26, 'reserved1'),
                ])

            # PAE >= 1703
            else:
                f.extend([
                    (26, 'PageFrameNumber'),
                    (25, 'reserved1'),
                    (1, 'NoExecute'),
                ])
            return

        # WIN64
        if getattr(self, 'WIN64', False):

            # WIN64 <= early 6.0
            f += [
                (28 if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WIN6 else 36, 'PageFrameNumber'),
            ]

            # WIN64 <= early 6.0
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WIN6:
                f.extend([
                    (12, 'reserved1'),
                    (11, 'SoftwareWsIndex')
                ])

            # WIN64 <= 1607
            elif self.NTDDI_VERSION <= sdkddkver.NTDDI_WIN10_RS1:
                f.extend([
                    (4, 'reserved1'),
                    (11, 'SoftwareWsIndex')
                ])

            # WIN64 > 1607
            else:
                f.extend([
                    (4, 'ReservedForHardware'),
                    (4, 'ReservedForSoftware'),
                    (4, 'WsleAge'),
                    (3, 'WsleProtection'),
                ])

            return f.append((1, 'NoExecute'))
        raise NotImplementedError(self.NTDDI_VERSION)

class MMPTE_PROTOTYPE(pbinary.flags, versioned):
    def __init__(self, **attrs):
        super(MMPTE_PROTOTYPE, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'Valid'),
                (8, 'ProtoAddressLow'),
                (1, 'ReadOnly'),
                (1, 'Prototype'),
                (21, 'ProtoAddressHigh'),
            ])

        # WIN64
        else:
            f.extend([
                (1, 'Valid'),
                (7, 'Unused0'),
                (1, 'ReadOnly'),
                (1, 'Unused1'),
                (1, 'Prototype'),
                (5, 'Protection'),
                (48, 'ProtoAddress'),
            ])
        return

class MMPTE_SOFTWARE(pbinary.flags):
    '''page is in swapfile.'''
    def __init__(self, **attrs):
        super(MMPTE_SOFTWARE, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'Valid'),
                (4, 'PageFileLow'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (20, 'PageFileHigh'),
            ])

        # WIN64
        else:
            f.extend([
                (1, 'Valid'),
                (4, 'PageFileLow'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (10, 'UsedPageTableEntries'),
                (1, 'InStore'),
                (9, 'Reserved'),
                (32, 'PageFileHigh'),
            ])
        return

class MMPTE_TIMESTAMP(pbinary.flags):
    '''"GlobalTimeStamp" is just a page reference counter.'''
    def __init__(self, **attrs):
        super(MMPTE_TIMESTAMP, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'MustBeZero'),
                (4, 'PageFileLow'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (20, 'GlobalTimeStamp'),
            ])

        # WIN64
        else:
            f.extend([
                (1, 'MustBeZero'),
                (4, 'PageFileLow'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (20, 'Reserved'),
                (32, 'GlobalTimeStamp'),
            ])
        return

class MMPTE_TRANSITION(pbinary.flags):
    def __init__(self, **attrs):
        super(MMPTE_TRANSITION, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'Valid'),
                (1, 'Write'),
                (1, 'Owner'),
                (1, 'WriteThrough'),
                (1, 'CacheDisable'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (20, 'PageFrameNumber'),
            ])
        # WIN64
        else:
            f.extend([
                (1, 'Valid'),
                (1, 'Write'),
                (1, 'Owner'),
                (1, 'WriteThrough'),
                (1, 'CacheDisable'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (26, 'PageFrameNumber'),
                (26, 'Unused'),
            ])
        return

class MMPTE_SUBSECTION(pbinary.flags):
    def __init__(self, **attrs):
        super(MMPTE_SUBSECTION, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'Valid'),
                (9, 'SubsectionAddressLow'),
                (1, 'Prototype'),
                (21, 'SubsectionAddressHigh'),
            ])

        # WIN64
        else:
            f.extend([
                (1, 'Valid'),
                (4, 'Unused0'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (5, 'Unused1'),
                (48, 'SubsectionAddress'),
            ])
        return

class MMPTE_LIST(pbinary.flags):
    def __init__(self, **attrs):
        super(MMPTE_LIST, self).__init__(**attrs)
        f = self._fields_ = []

        # WIN32
        if not getattr(self, 'WIN64', False):
            f.extend([
                (1, 'Valid'),
                (1, 'OneEntry'),
                (8, 'filler0'),
                (1, 'Prototype'),
                (1, 'filler1'),
                (20, 'NextEntry'),  # pointer
            ])

        # WIN64
        else:
            f.extend([
                (1, 'Valid'),
                (1, 'OneEntry'),
                (3, 'filler0'),
                (5, 'Protection'),
                (1, 'Prototype'),
                (1, 'Transition'),
                (20, 'filler1'),
                (32, 'NextEntry'),  # pointer
            ])
        return

class MMPTE(dynamic.union, versioned):

    # FIXME: >= 6.2 is ULONGLONG
    _fields_ = [
        (lambda self: ULONG if not getattr(self, 'WIN64', False) else ULONGLONG, 'Long'),
        (lambda self: ULONG if not getattr(self, 'WIN64', False) else ULONGLONG, 'VolatileLong'),
        (lambda self: MMPTE_HIGHLOW if getattr(self, 'PAE', False) else ptype.undefined, 'HighLow'),

        (pbinary.littleendian(HARDWARE_PTE), 'Flush'),
        (pbinary.littleendian(MMPTE_HARDWARE), 'Hard'),
        (pbinary.littleendian(MMPTE_PROTOTYPE), 'Proto'),
        (pbinary.littleendian(MMPTE_SOFTWARE), 'Soft'),

        # > late 6.0
        (lambda self: pbinary.littleendian(MMPTE_TIMESTAMP) if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) > sdkddkver.NTDDI_WS08 else ptype.undefined, 'TimeStamp'),
        (pbinary.littleendian(MMPTE_TRANSITION), 'Trans'),
        (pbinary.littleendian(MMPTE_SUBSECTION), 'Subsect'),
        (pbinary.littleendian(MMPTE_LIST), 'List'),
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
