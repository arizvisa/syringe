import ptypes
from ptypes import *

from . import umtypes, mmtypes, exception, sdkddkver
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

class RTL_USER_PROCESS_INFORMATION(pstruct.type):
    _fields_ = [
        (ULONG, 'Size'),
        (HANDLE, 'Process'),
        (HANDLE, 'Thread'),
        (umtypes.CLIENT_ID, 'ClientId'),
        (mmtypes.SECTION_IMAGE_INFORMATION, 'ImageInformation'),
    ]

class RTL_USER_PROCESS_PARAMETERS(pstruct.type, versioned):
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
        (ULONG, 'EnvironmentVersion'),
        (PVOID, 'PackageDependencyData'),
        (ULONG, 'ProcessGroupId'),

        (lambda self: pint.uint_t if self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10 else ULONG, 'LoaderThreads'),
        (lambda self: ptype.undefined if self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_RS5 else umtypes.UNICODE_STRING, 'RedirectionDllName'),

        (lambda self: ptype.undefined if self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_19H1 else umtypes.UNICODE_STRING, 'HeapPartitionName'),
        (lambda self: ptype.undefined if self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_19H1 else ULONG_PTR, 'DefaultThreadpoolCpuSetMasks'),
        (lambda self: ptype.undefined if self.NTDDI_VERSION < sdkddkver.NTDDI_WIN10_21H2 else ULONG, 'DefaultThreadpoolCpuSetMaskCount'),
    ]

class RTL_PATH_TYPE(pint.enum):
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

class RTL_BALANCED_NODE(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(RTL_BALANCED_NODE, self).__init__(**attrs)
        f = self._fields_ = []
        f.extend([
            (P(RTL_BALANCED_NODE), 'Left'),
            (P(RTL_BALANCED_NODE), 'Right'),
            (ULONG, 'ParentValue'),
            (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(ParentValue)'),
        ])

class RTL_RB_TREE(pstruct.type):
    _fields_ = [
        (P(RTL_BALANCED_NODE), 'Root'),
        (P(RTL_BALANCED_NODE), 'Min'),
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

class RTL_RUN_ONCE(dynamic.union, versioned):
    def __ULONG3264(self):
        return ULONGLONG if getattr(self, 'WIN64', False) else ULONG
    _fields_ = [
        (PVOID, 'Ptr'),
        (__ULONG3264, 'Value'),
        (__ULONG3264, 'State'),   # ULONGLONG State:2
    ]

class RTL_SRWLOCK(dynamic.union, versioned):
    class _Shared(pbinary.flags):
        _fields_ = [
            (lambda self: 60 if getattr(self, 'WIN64', False) else 28, 'Shared'),
            (1, 'MultipleShared'),
            (1, 'Waking'),
            (1, 'Waiting'),
            (1, 'Locked'),
        ]
    _fields_ = [
        (_Shared, 'Shared'),
        (ULONG, 'Value'),
        (PVOID, 'Ptr'),
    ]

@pbinary.littleendian
class HEAP_(pbinary.flags):
    '''ULONG'''
    _fields_ = [
        (1, 'LOCK_USER_ALLOCATED'),
        (1, 'VALIDATE_PARAMETERS_ENABLED'),
        (1, 'VALIDATE_ALL_ENABLED'),
        (1, 'SKIP_VALIDATION_CHECKS'),
        (1, 'CAPTURE_STACK_BACKTRACES'),
        (1, 'BREAK_WHEN_OUT_OF_VM'),
        (1, 'PROTECTION_ENABLED'),
        (1, 'FLAG_PAGE_ALLOCS'),
        (5, 'RESERVED'),
        (1, 'CREATE_ENABLE_EXECUTE'),
        (1, 'CREATE_ENABLE_TRACING'),
        (1, 'CREATE_ALIGN_16'),
        (4, 'CLASS'),
        (1, 'SETTABLE_USER_FLAG3'),
        (1, 'SETTABLE_USER_FLAG2'),
        (1, 'SETTABLE_USER_FLAG1'),
        (1, 'SETTABLE_USER_VALUE'),
        (1, 'DISABLE_COALESCE_ON_FREE'),
        (1, 'FREE_CHECKING_ENABLED'),
        (1, 'TAIL_CHECKING_ENABLED'),
        (1, 'REALLOC_IN_PLACE_ONLY'),
        (1, 'ZERO_MEMORY'),
        (1, 'GENERATE_EXCEPTIONS'),
        (1, 'GROWABLE'),
        (1, 'NO_SERIALIZE'),
    ]

class RTL_HP_SEG_ALLOC_POLICY(pstruct.type, versioned):
    def __ULONG3264(self):
        return ULONGLONG if getattr(self, 'WIN64', False) else ULONG
    _fields_ = [
        (__ULONG3264, 'MinLargePages'),
        (__ULONG3264, 'MaxLargePages'),
        (UCHAR, 'MinUtilization'),
        (lambda self: dyn.block(7 if getattr(self, 'WIN64', False) else 3), 'padding(MinUtilization)'),
    ]

class RTL_HP_ENV_HANDLE(pstruct.type):
    _fields_ = [
        (dyn.array(PVOID, 2), 'h'),
    ]

class RTL_HEAP_MEMORY_LIMIT_DATA(pstruct.type, versioned):
    def __ULONG3264(self):
        return ULONGLONG if getattr(self, 'WIN64', False) else ULONG
    _fields_ = [
        (__ULONG3264, 'CommitLimitBytes'),
        (__ULONG3264, 'CommitLimitFailureCode'),
        (__ULONG3264, 'MaxAllocationSizeBytes'),
        (__ULONG3264, 'AllocationLimitFailureCode'),
    ]

class RTLP_HP_LOCK_TYPE(pint.enum):
    _values_ = [
        ('HeapLockPaged', 0),
        ('HeapLockNonPaged', 1),
        ('HeapLockTypeMax', 2),
    ]

class RTL_HP_VS_CONFIG(pstruct.type):
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (29, 'Reserved'),
            (1, 'EnableDelayFree'),
            (1, 'FullDecommit'),
            (1, 'PageAlignLargeAllocs'),
        ]
    _fields_ = [
        (_Flags, 'Flags'),
    ]

class RTL_HP_LFH_CONFIG(pstruct.type):
    @pbinary.littleendian
    class _Options(pbinary.flags):
        _fields_ = [
            (14, 'Reserved'),
            (1, 'DisableRandomization'),
            (1, 'WitholdPageCrossingBlocks'),
        ]
    _fields_ = [
        (USHORT, 'MaxBlockSize'),
        (_Options, 'Options'),
    ]

class ACTIVATION_CONTEXT_DATA(pstruct.type):
    _fields_ = [
        (ULONG, 'Magic'),
        (ULONG, 'HeaderSize'),
        (ULONG, 'FormatVersion'),
        (ULONG, 'TotalSize'),
        (ULONG, 'DefaultTocOffset'),
        (ULONG, 'ExtendedTocOffset'),
        (ULONG, 'AssemblyRosterOffset'),
        (ULONG, 'Flags'),
    ]

class ASSEMBLY_STORAGE_MAP_ENTRY(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (umtypes.UNICODE_STRING, 'DosPath'),
        (HANDLE, 'Handle'),
    ]

class ASSEMBLY_STORAGE_MAP(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (ULONG, 'AssemblyCount'),
        #(PASSEMBLY_STORAGE_MAP_ENTRY*, 'AssemblyArray'),
        (lambda self: P(dyn.array(ASSEMBLY_STORAGE_MAP_ENTRY, self['AssemblyCount'].li.int())), 'AssemblyArray'),
    ]

class file_info(pstruct.type):
    _fields_ = [
        (ULONG, 'type'),
        (PWSTR, 'info'),    # WCHAR*
    ]

class progids(pstruct.type):
     def __progids(self):
        try:
            p = self.getparent(progids)
        except Exception:
            count = 0
        else:
            count = p['num'].li.int()
        return dyn.array(PWSTR, count)

     _fields_ = [
        #(WCHAR**, 'progids'),
        (P(__progids), 'progids'),
        (unsigned_int, 'num'),
        (unsigned_int, 'allocated'),
     ]

class entity(pstruct.type):
    class typelib(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'tlbid'),
            (PWSTR, 'tlbid'),
            #(WCHAR*, 'helpdir'),
            (PWSTR, 'helpdir'),
            (WORD, 'flags'),
            (WORD, 'major'),
            (WORD, 'minor'),
        ]
    class comclass(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'clsid'),
            (PWSTR, 'clsid'),
            #(WCHAR*, 'tlbid'),
            (PWSTR, 'tlbid'),
            #(WCHAR*, 'progid'),
            (PWSTR, 'progid'),
            #(WCHAR*, 'name'),       # clrClass: class name
            (PWSTR, 'name'),       # clrClass: class name
            #(WCHAR*, 'version'),    # clrClass: CLR runtime version
            (PWSTR, 'version'),    # clrClass: CLR runtime version
            (DWORD, 'model'),
            (DWORD, 'miscstatus'),
            (DWORD, 'miscstatuscontent'),
            (DWORD, 'miscstatusthumbnail'),
            (DWORD, 'miscstatusicon'),
            (DWORD, 'miscstatusdocprint'),
            (progids, 'progids'),
        ]
    class ifaceps(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'iid'),
            (PWSTR, 'iid'),
            #(WCHAR*, 'base'),
            (PWSTR, 'base'),
            #(WCHAR*, 'tlib'),
            (PWSTR, 'tlib'),
            #(WCHAR*, 'name'),
            (PWSTR, 'name'),
            #(WCHAR*, 'ps32'),   # only stored for 'comInterfaceExternalProxyStub'
            (PWSTR, 'ps32'),   # only stored for 'comInterfaceExternalProxyStub'
            (DWORD, 'mask'),
            (ULONG, 'nummethods'),
        ]
    class klass(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'name'),
            (PWSTR, 'name'),
            (BOOL, 'versioned'),
        ]
    class clrsurrogate(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'name'),
            (PWSTR, 'name'),
            #(WCHAR*, 'clsid'),
            (PWSTR, 'clsid'),
            #(WCHAR*, 'version'),
            (PWSTR, 'version'),
        ]
    class settings(pstruct.type):
        _fields_ = [
            #(WCHAR*, 'name'),
            (PWSTR, 'name'),
            #(WCHAR*, 'value'),
            (PWSTR, 'value'),
            #(WCHAR*, 'ns'),
            (PWSTR, 'ns'),
        ]

    def __u(self):
        res = self['kind'].li

    _fields_ = [
        (DWORD, 'kind'),
        (__u, 'u'),
    ]

class entity_array(pstruct.type):
    _fields_ = [
        (P(entity), 'base'),
        (unsigned_int, 'num'),
        (unsigned_int, 'allocated'),
    ]

class dll_redirect(pstruct.type):
    _fields_ = [
        #(WCHAR*, 'name'),
        (PWSTR, 'name'),
        #(WCHAR*, 'hash'),
        (PWSTR, 'hash'),
        (entity_array, 'entities'),
    ]

class _assembly_type(pint.enum):
    _fields_ = [
        ('APPLICATION_MANIFEST', 0),
        ('ASSEMBLY_MANIFEST', 1),
        ('ASSEMBLY_SHARED_MANIFEST', 2),
    ]

class assembly_type(pint.enum, unsigned___int3264):
    pass

class assembly_version(pstruct.type):
    _fields_ = [
        (USHORT, 'major'),
        (USHORT, 'minor'),
        (USHORT, 'build'),
        (USHORT, 'revision'),
    ]

class assembly_identity(pstruct.type):
    _fields_ = [
        #(WCHAR*, 'name'),
        (PWSTR, 'name'),
        #(WCHAR*, 'arch'),
        (PWSTR, 'arch'),
        #(WCHAR*, 'public_key'),
        (PWSTR, 'public_key'),
        #(WCHAR*, 'language'),
        (PWSTR, 'language'),
        #(WCHAR*, 'type'),
        (PWSTR, 'type'),
        (assembly_version, 'version'),
        (BOOL, 'optional'),
        (BOOL, 'delayed'),
    ]

class ACTCTX_COMPATIBILITY_ELEMENT_TYPE_(pint.enum):
    _values_ = [
        ('UNKNOWN', 0),
        ('OS', 1),
    ]
class ACTCTX_COMPATIBILITY_ELEMENT_TYPE(ACTCTX_COMPATIBILITY_ELEMENT_TYPE_, unsigned___int3264):
    pass

class COMPATIBILITY_CONTEXT_ELEMENT(pstruct.type):
    _fields_ = [
        (GUID, 'Id'),
        (ACTCTX_COMPATIBILITY_ELEMENT_TYPE, 'Type'),
    ]

class ACTCTX_RUN_LEVEL_(pint.enum):
    _values_ = [
        ('UNSPECIFIED', 0),
        ('AS_INVOKER', 1),
        ('HIGHEST_AVAILABLE', 2),
        ('REQUIRE_ADMIN', 3),
        ('NUMBER', 4),
    ]

class ACTCTX_REQUESTED_RUN_LEVEL(ACTCTX_RUN_LEVEL_, unsigned___int3264):
    pass

class assembly(pstruct.type):
    _fields_ = [
        (assembly_type, 'type'),
        (assembly_identity, 'id'),
        (file_info, 'manifest'),
        #(WCHAR*, 'directory'),
        (PWSTR, 'directory'),
        (BOOL, 'no_inherit'),
        (P(dll_redirect), 'dlls'),
        (unsigned_int, 'num_dlls'),
        (unsigned_int, 'allocated_dlls'),
        (entity_array, 'entities'),
        (P(COMPATIBILITY_CONTEXT_ELEMENT), 'compat_contexts'),
        (ULONG, 'num_compat_contexts'),
        (ACTCTX_REQUESTED_RUN_LEVEL, 'run_level'),
        (ULONG, 'ui_access'),
    ]

class strsection_header(pstruct.type):
    _fields = [
        (DWORD, 'magic'),
        (ULONG, 'size'),
        (dyn.array(DWORD, 3), 'unk1'),
        (ULONG, 'count'),
        (ULONG, 'index_offset'),
        (dyn.array(DWORD, 2), 'unk2'),
        (ULONG, 'global_offset'),
        (ULONG, 'global_len'),
]

class guidsection_header(pstruct.type):
    _fields_ = [
        (DWORD, 'magic'),
        (ULONG, 'size'),
        (dyn.array(DWORD, 3), 'unk'),
        (ULONG, 'count'),
        (ULONG, 'index_offset'),
        (DWORD, 'unk2'),
        (ULONG, 'names_offset'),
        (ULONG, 'names_len'),
    ]

class ACTIVATION_CONTEXT(pstruct.type):
    _fields_ = [
        (LONG, 'RefCount'),
        (ULONG, 'Flags'),
        (LIST_ENTRY, 'Links'),
        (P(ACTIVATION_CONTEXT_DATA), 'ActivationContextData'),
        (PVOID, 'NotificationRoutine'),
        (PVOID, 'NotificationContext'),
        (dyn.array(ULONG,8), 'SentNotifications'),
        (dyn.array(ULONG,8), 'DisabledNotifications'),
        (ASSEMBLY_STORAGE_MAP, 'StorageMap'),
        (P(ASSEMBLY_STORAGE_MAP_ENTRY), 'InlineStorageMapEntries'),
        (ULONG, 'StackTraceIndex'),
        #(dyn.array(PVOID,4,4), 'StackTraces'), # FIXME
        (dyn.array(dyn.array(PVOID, 4), 4), 'StackTraces'),
        (file_info, 'config'),
        (file_info, 'appdir'),
        (P(assembly), 'assemblies'),
        (unsigned_int, 'num_assemblies'),
        (unsigned_int, 'allocated_assemblies'),

        (DWORD, 'sections'),
        (P(strsection_header), 'wndclass_section'),
        (P(strsection_header), 'dllredirect_section'),
        (P(strsection_header), 'progid_section'),
        (P(guidsection_header), 'tlib_section'),
        (P(guidsection_header), 'comserver_section'),
        (P(guidsection_header), 'ifaceps_section'),
        (P(guidsection_header), 'clrsurrogate_section'),
    ]

class RTL_ACTIVATION_CONTEXT_STACK_FRAME(pstruct.type):
    def __Previous(self):
        return RTL_ACTIVATION_CONTEXT_STACK_FRAME
    _fields_ = [
        (P(__Previous), 'Previous'),
        (P(ACTIVATION_CONTEXT), 'ActivationContext'),
        (ULONG, 'Flags'),
    ]

class RTL_CALLER_ALLOCATED_ACTIVATION_CONTEXT_STACK_FRAME_BASIC(pstruct.type):
    _fields_ = [
        (SIZE_T, 'Size'),
        (ULONG, 'Format'),
        (RTL_ACTIVATION_CONTEXT_STACK_FRAME, 'Frame'),
    ]

class RTL_CALLER_ALLOCATED_ACTIVATION_CONTEXT_STACK_FRAME_EXTENDED(pstruct.type):
    _fields_ = [
        (SIZE_T, 'Size'),
        (ULONG, 'Format'),
        (RTL_ACTIVATION_CONTEXT_STACK_FRAME, 'Frame'),
        (PVOID, 'Extra1'),
        (PVOID, 'Extra2'),
        (PVOID, 'Extra3'),
        (PVOID, 'Extra4'),
    ]

class RTL_HEAP_ALLOCATED_ACTIVATION_CONTEXT_STACK_FRAME(pstruct.type):
    _fields_ = [
        (RTL_ACTIVATION_CONTEXT_STACK_FRAME, 'Frame'),
        (ULONG_PTR, 'Cookie'),
        (dyn.array(PVOID, 8),  'ActivationStackBackTrace[8]'),
    ]

class ACTIVATION_CONTEXT_STACK_FRAMELIST(pstruct.type):
    _fields_ = [
        (ULONG, 'Magic'),
        (ULONG, 'FramesInUse'),
        (LIST_ENTRY, 'Links'),
        (ULONG, 'Flags'),
        (ULONG, 'NotFramesInUse'),
        (dyn.array(RTL_HEAP_ALLOCATED_ACTIVATION_CONTEXT_STACK_FRAME, 32), 'Frames'),
    ]

class ACTIVATION_CONTEXT_STACK(pstruct.type):
    _fields_ = [
        (P(RTL_ACTIVATION_CONTEXT_STACK_FRAME), 'ActiveFrame'),
        (LIST_ENTRY, 'FrameListCache'),
        (ULONG, 'Flags'),
        (ULONG, 'NextCookieSequenceNumber'),
        (ULONG, 'StackId'),
    ]

class FIBER(pstruct.type, versioned):
    _fields_ = [
        (PVOID, 'FiberData'),
        (P(exception.EXCEPTION_REGISTRATION_RECORD), 'ExceptionList'),    # 0x4, 0x8
        (PVOID, 'StackBase'),                                   # 0x8, 0x10
        (PVOID, 'StackLimit'),                                  # 0xc, 0x18
        (PVOID, 'DeallocationStack'),                           # 0x10, 0x20
        (lambda self: PVOID if getattr(self, 'WIN64', False) else ptype.undefined, 'padding(FiberContext)'),
        (CONTEXT, 'FiberContext'),                              # 0x14, 0x30
    ]

    def __init__(self, **attrs):
        super(FIBER, self).__init__(**attrs)
        f = self._fields_ = self._fields_[:]
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (PVOID, 'Wx86Tib'),                                     # 0x2E0 0x500
                (P(ACTIVATION_CONTEXT_STACK), 'ActivationContextStackPointer'), # 0x2E4 0x508
                (PVOID, 'FlsData'),                 # 0x2E8 0x510
                (ULONG, 'GuaranteedStackBytes'),    # 0x2EC 0x518
                (ULONG, 'TebFlags'),                # 0x2F0 0x51C
            ])

        else:
            f.extend([
                (ULONG, 'GuaranteedStackBytes'),    # 0x2E0
                (PVOID, 'FlsData'),                 # 0x2E4
                (P(ACTIVATION_CONTEXT_STACK), 'ActivationContextStackPointer'),
            ])
        return
