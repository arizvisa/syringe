import ptypes
from ptypes import *

from . import umtypes
from .datatypes import *

class SIZE_T64(ULONGLONG): pass

class RTL_CRITICAL_SECTION(pstruct.type, versioned):
    _fields_ = [
        (PVOID, 'DebugInfo'),
        (LONG, 'LockCount'),
        (LONG, 'RecursionCount'),
        (PVOID, 'OwningThread'),
        (PVOID, 'LockSemaphore'),
        (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SpinCount'),
    ]

class RTL_BITMAP(pstruct.type):
    class _Buffer(BitmapBitsArray):
        _object_ = ULONG

    def __Buffer(self):
        res = self['SizeOfBitMap'].l
        fractionQ = 1 if res.int() % 32 else 0
        target = dyn.clone(RTL_BITMAP._Buffer, length=fractionQ + res.int() // 32)
        return P(target)

    _fields_ = [
        (ULONG, 'SizeOfBitMap'),
        (__Buffer, 'Buffer'),
    ]

class RTL_BITMAP_EX(pstruct.type):
    class _Buffer(BitmapBitsArray):
        _object_ = ULONGLONG

    def __Buffer(self):
        res = self['SizeOfBitMap'].l
        fractionQ = 1 if res.int() % 64 else 0
        target = dyn.clone(RTL_BITMAP_EX._Buffer, length=fractionQ + res.int() // 64)
        return P(target)

    _fields_ = [
        (ULONGLONG, 'SizeOfBitMap'),
        (__Buffer, 'Buffer'),
    ]

class RTL_DRIVE_LETTER_CURDIR(pstruct.type):
    _fields_ = [
        (WORD, 'Flags'),
        (WORD, 'Length'),
        (ULONG, 'TimeStamp'),
        (umtypes.STRING, 'DosPath'),
    ]

class CURDIR(pstruct.type):
    _fields_ = [
        (umtypes.UNICODE_STRING, 'DosPath'),
        (HANDLE, 'Handle'),
    ]
    def summary(self):
        return 'Handle={:x} DosPath={!r}'.format(self['Handle'].int(), self['DosPath'].str())

class RTL_USER_PROCESS_PARAMETERS(pstruct.type):
    _fields_ = [
        (ULONG, 'MaximumLength'),
        (ULONG, 'Length'),
        (ULONG, 'Flags'),
        (ULONG, 'DebugFlags'),
        (PVOID, 'ConsoleHandle'),
        (ULONG, 'ConsoleFlags'),
        (PVOID, 'StandardInput'),
        (PVOID, 'StandardOutput'),
        (PVOID, 'StandardError'),
        (CURDIR, 'CurrentDirectory'),
        (umtypes.UNICODE_STRING, 'DllPath'),
        (umtypes.UNICODE_STRING, 'ImagePathName'),
        (umtypes.UNICODE_STRING, 'CommandLine'),
#        (P(lambda s: dyn.block(s.getparent(RTL_USER_PROCESS_PARAMETERS)['EnvironmentSize'].int())), 'Environment'),
#        (P(lambda s: dyn.lazyblockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.int())), 'Environment'),
        (P(lambda s: dyn.blockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.int())), 'Environment'),
        (ULONG, 'StartingX'),
        (ULONG, 'StartingY'),
        (ULONG, 'CountX'),
        (ULONG, 'CountY'),
        (ULONG, 'CountCharsX'),
        (ULONG, 'CountCharsY'),
        (ULONG, 'FillAttribute'),
        (ULONG, 'WindowFlags'),
        (ULONG, 'ShowWindowFlags'),
        (umtypes.UNICODE_STRING, 'WindowTitle'),
        (umtypes.UNICODE_STRING, 'DesktopInfo'),
        (umtypes.UNICODE_STRING, 'ShellInfo'),
        (umtypes.UNICODE_STRING, 'RuntimeData'),

        (dyn.array(RTL_DRIVE_LETTER_CURDIR, 32), 'CurrentDirectories'),
        (ULONG, 'EnvironmentSize'),
    ]

class RLT_PATH_TYPE(pint.enum):
    _values_ = [
        ('RtlPathTypeUnknown', 0),
        ('RtlPathTypeUncAbsolute', 1),
        ('RtlPathTypeDriveAbsolute', 2),
        ('RtlPathTypeDriveRelative', 3),
        ('RtlPathTypeRooted', 4),
        ('RtlPathTypeRelative', 5),
        ('RtlPathTypeLocalDevice', 6),
        ('RtlPathTypeRootLocalDevice', 7),
    ]

class RTL_RELATIVE_NAME(pstruct.type):
    _fields_ = [
        (umtypes.UNICODE_STRING, 'RelativeName'),
        (HANDLE, 'ContainingDirectory'),
        (PVOID, 'CurDirRef'),
    ]

class RTL_PROCESS_MODULE_INFORMATION(pstruct.type):
    _fields_ = [
        (PVOID, 'MappedBase'),
        (PVOID, 'ImageBase'),
        (ULONG, 'ImageSize'),
        (ULONG, 'Flags'),
        (USHORT, 'LoadOrderIndex'),
        (USHORT, 'InitOrderIndex'),
        (USHORT, 'LoadCount'),
        (USHORT, 'OffsetToFileName'),
        (dyn.clone(pstr.string, length=256), 'FullPathName'),
    ]


class RTL_BALANCED_LINKS(pstruct.type):
    def __init__(self, **attrs):
        super(RTL_BALANCED_LINKS, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (P(RTL_BALANCED_LINKS), 'Parent'),
            (P(RTL_BALANCED_LINKS), 'LeftChild'),
            (P(RTL_BALANCED_LINKS), 'RightChild'),
            (CHAR, 'Balance'),
            (dyn.array(UCHAR, 3), 'Reserved'),
        ])

class RTL_AVL_COMPARE_ROUTINE(void): pass
class RTL_AVL_ALLOCATE_ROUTINE(void): pass
class RTL_AVL_FREE_ROUTINE(void): pass

class RTL_AVL_TABLE(pstruct.type, versioned):
    _fields_ = [
        (RTL_BALANCED_LINKS, 'BalancedRoot'),
        (PVOID, 'OrderedPointer'),
        (ULONG, 'WhichOrderedElement'),
        (ULONG, 'NumberGenericTableElements'),
        (ULONG, 'DepthOfTree'),
        (P(RTL_BALANCED_LINKS), 'RestartKey'),
        (ULONG, 'DeleteCount'),
        (P(RTL_AVL_COMPARE_ROUTINE), 'CompareRoutine'),
        (P(RTL_AVL_ALLOCATE_ROUTINE), 'AllocateRoutine'),
        (P(RTL_AVL_FREE_ROUTINE), 'FreeRoutine'),
        (PVOID, 'TableContext'),
    ]

class RTL_STACK_TRACE_ENTRY(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_STACK_TRACE_ENTRY, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (P(RTL_STACK_TRACE_ENTRY), 'HashChain'),
            (ULONG, 'TraceCount'),
            (USHORT, 'Index'),
            (USHORT, 'Depth'),
            (dyn.array(PVOID, 32), 'BackTrace'),
        ])

class STACK_TRACE_DATABASE(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(STACK_TRACE_DATABASE, self).__init__(**attrs)
        from . import extypes

        f = self._fields_ = []
        f.extend([
            (extypes.ERESOURCE, 'Lock'),
            (BOOLEAN, 'DumpInProgress'),
            (dyn.align(8 if getattr(self, 'WIN64', False) else 4), 'align(CommitBase)'),
            (PVOID, 'CommitBase'),
            (PVOID, 'CurrentLowerCommitLimit'),
            (PVOID, 'CurrentUpperCommitLimit'),
            (P(UCHAR), 'NextFreeLowerMemory'),
            (P(UCHAR), 'NextFreeUpperMemory'),
            (ULONG, 'NumberOfEntriesAdded'),
            (ULONG, 'NumberOfAllocationFailures'),
            (P(RTL_STACK_TRACE_ENTRY), 'EntryIndexArray'),
            (ULONG, 'NumberOfBuckets'),
            (lambda self: dyn.array(P(RTL_STACK_TRACE_ENTRY), self['NumberOfBuckets'].li.int()), 'Buckets'),
        ])

class RTL_TRACE_BLOCK(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_TRACE_BLOCK, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (ULONG, 'Magic'),
            (ULONG, 'Count'),
            (ULONG, 'Size'),
            (ULONG, 'UserCount'),
            (ULONG, 'UserSize'),
            (PVOID, 'UserContext'),
            (P(RTL_TRACE_BLOCK), 'Next'),
            (PVOID, 'Trace'),
        ])

class RTL_TRACE_DATABASE(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_TRACE_DATABASE, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (ULONG, 'Magic'),
            (ULONG, 'Flags'),
            (ULONG, 'Tag'),
            (P(RTL_TRACE_SEGMENT), 'SegmentList'),
            (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MaximumSize'),
            (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'CurrentSize'),
            (PVOID, 'Owner'),
            (RTL_CRITICAL_SECTION, 'Lock'),
            (ULONG, 'NoOfBuckets'),
            (lambda self: P(dyn.array(RTL_TRACE_BLOCK, self['NoOfBuckets'].li.int())), 'Buckets'),
            (RTL_TRACE_HASH_FUNCTION, 'HashFunction'),
            (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'NoOfTraces'),
            (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'NoOfHits'),
            (dyn.array(ULONG, 16), 'HashCount'),
        ])

class RTL_TRACE_SEGMENT(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_TRACE_SEGMENT, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (ULONG, 'Magic'),
            (P(RTL_TRACE_DATABASE), 'Database'),
            (P(RTL_TRACE_SEGMENT), 'NextSegment'),
            (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'TotalSize'),
            (P(CHAR), 'SegmentStart'),
            (P(CHAR), 'SegmentEnd'),
            (P(CHAR), 'SegmentFree'),
        ])

class RTL_TRACE_ENUMERATE(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_TRACE_SEGMENT, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (P(RTL_TRACE_DATABASE), 'Database'),
            (ULONG, 'Index'),
            (P(RTL_TRACE_BLOCK), 'Block'),
        ])

# XXX: These should probably be unions
class RTL_RUN_ONCE(pstruct.type, versioned):
    _fields_ = [
        (P(ptype.undefined), 'Ptr'),
    ]

class RTL_SRWLOCK(pstruct.type, versioned):
    _fields_ = [
        (P(ptype.undefined), 'Ptr'),
    ]
