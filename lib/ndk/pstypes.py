import ptypes, pecoff
from ptypes import *

from . import ldrtypes, rtltypes, umtypes, Ntddk, heaptypes, sdkddkver
from .datatypes import *

class PEB_FREE_BLOCK(pstruct.type): pass
class PPEB_FREE_BLOCK(P(PEB_FREE_BLOCK)): pass
PEB_FREE_BLOCK._fields_ = [(PPEB_FREE_BLOCK,'Next'),(ULONG,'Size')]

class PEB(pstruct.type, versioned):
    class BitField(pbinary.flags):
        _fields_ = [
            (1, 'ImageUsesLargePages'),
            (1, 'IsProtectedProcess'),
            (1, 'IsLegacyProcess'),
            (1, 'IsImageDynamicallyRelocated'),
            (1, 'SkipPatchingUser32Forwarders'),
            (1, 'SpareBits'),
        ]

    class CrossProcessFlags(pbinary.flags):
        _fields_ = [
            (1, 'ProcessInJob'),
            (1, 'ProcessInitializing'),
            (1, 'ProcessUsingVEH'),
            (1, 'ProcessUsingVCH'),
            (1, 'ProcessUsingFTH'),
            (27, 'ReservedBits0'),
        ]

    class NtGlobalFlag(pbinary.flags):
        def __init__(self, **attrs):
            super(PEB.NtGlobalFlag, self).__init__(**attrs)

            f = []
            f.extend([
                (1, 'FLG_STOP_ON_EXCEPTION'),   # 0x00000001
                (1, 'FLG_SHOW_LDR_SNAPS'),  # 0x00000002
                (1, 'FLG_DEBUG_INITIAL_COMMAND'),   # 0x00000004
                (1, 'FLG_STOP_ON_HUNG_GUI'),    # 0x00000008
                (1, 'FLG_HEAP_ENABLE_TAIL_CHECK'),  # 0x00000010
                (1, 'FLG_HEAP_ENABLE_FREE_CHECK'),  # 0x00000020
                (1, 'FLG_HEAP_VALIDATE_PARAMETERS'),    # 0x00000040
                (1, 'FLG_HEAP_VALIDATE_ALL'),   # 0x00000080
                (1, 'FLG_POOL_ENABLE_TAIL_CHECK'),  # 0x00000100
                (1, 'FLG_POOL_ENABLE_FREE_CHECK'),  # 0x00000200
                (1, 'FLG_POOL_ENABLE_TAGGING'), # 0x00000400
                (1, 'FLG_HEAP_ENABLE_TAGGING'), # 0x00000800
                (1, 'FLG_USER_STACK_TRACE_DB'), # 0x00001000
                (1, 'FLG_KERNEL_STACK_TRACE_DB'),   # 0x00002000
                (1, 'FLG_MAINTAIN_OBJECT_TYPELIST'),    # 0x00004000
                (1, 'FLG_HEAP_ENABLE_TAG_BY_DLL'),  # 0x00008000
                (1, 'FLG_IGNORE_DEBUG_PRIV'),   # 0x00010000
                (1, 'FLG_ENABLE_CSRDEBUG'), # 0x00020000
                (1, 'FLG_ENABLE_KDEBUG_SYMBOL_LOAD'),   # 0x00040000
                (1, 'FLG_DISABLE_PAGE_KERNEL_STACKS'),  # 0x00080000
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WINXP:
                f.append((1, 'FLG_HEAP_ENABLE_CALL_TRACING'))   #0x00100000
            else:
                f.append((1, 'FLG_ENABLE_SYSTEM_CRIT_BREAKS'))   #0x00100000

            f.extend([
                (1, 'FLG_HEAP_DISABLE_COALESCING'), # 0x00200000
                (1, 'FLG_ENABLE_CLOSE_EXCEPTIONS'), # 0x00400000
                (1, 'FLG_ENABLE_EXCEPTION_LOGGING'),    # 0x00800000
                (1, 'FLG_ENABLE_HANDLE_TYPE_TAGGING'),  # 0x01000000
                (1, 'FLG_HEAP_PAGE_ALLOCS'),    # 0x02000000
                (1, 'FLG_DEBUG_INITIAL_COMMAND_EX'),    # 0x04000000
            ])
            f.append((1+1+1+1+1, 'FLG_RESERVED'))
            self._fields_ = list(reversed(f))

        def __repr__(self):
            ofs = '[{:x}]'.format(self.getoffset())
            names = '|'.join((k for k,v in self.items() if v))
            return ' '.join([ofs, self.name(), names, '{!r}'.format(self.serialize())])

    class TracingFlags(pbinary.flags):
        _fields_ = [
            (1, 'HeapTracingEnabled'),
            (1, 'CritSecTracingEnabled'),
            (30, 'SpareTracingBits'),
        ]

    def __init__(self, **attrs):
        super(PEB, self).__init__(**attrs)
        self._fields_ = f = []
        aligned = dyn.align(8 if getattr(self,'WIN64',False) else 4)

        f.extend([
            (UCHAR, 'InheritedAddressSpace'),
            (UCHAR, 'ReadImageFileExecOptions'),
            (UCHAR, 'BeingDebugged'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append( (pbinary.littleendian(PEB.BitField), 'BitField') )
        else:
            raise NotImplementedError
            f.append( (BOOLEAN, 'SpareBool') )

        f.extend([
            (aligned, 'align(Mutant)'),
            (HANDLE, 'Mutant'),
            (P(pecoff.Executable.File), 'ImageBaseAddress'),
            (ldrtypes.PPEB_LDR_DATA, 'Ldr'),
            (P(rtltypes._RTL_USER_PROCESS_PARAMETERS), 'ProcessParameters'),
            (PVOID, 'SubSystemData'),
            (P(heaptypes._HEAP), 'ProcessHeap'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.extend([
                (P(rtltypes._RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (pbinary.littleendian(PEB.CrossProcessFlags), 'CrossProcessFlags'),
                (aligned, 'align(UserSharedInfoPtr)'),
                (PVOID, 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'AtlThunkSListPtr32') if getattr(self,'WIN64',False) else (ULONG,'SpareUlong'),
                (P(API_SET_MAP), 'ApiSetMap'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            raise NotImplementedError
            f.extend([
                (P(rtltypes._RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (ULONG, 'CrossProcessFlags'),
                (PVOID, 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'SpareUlong'),
                (PVOID, 'SparePebPtr0'),
            ])
        else:
            raise NotImplementedError
            f.extend([
                (P(rtltypes._RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'FastPebLockRoutine'),
                (PVOID, 'FastPebUnlockRoutine'),
                (ULONG, 'EnvironmentUpdateCount'),
                (PVOID, 'KernelCallbackTable'),
                (PVOID, 'EventLogSection'),
                (PVOID, 'EventLog'),
                (PPEB_FREE_BLOCK, 'FreeList'),
            ])

        f.extend([
            (ULONG, 'TlsExpansionCounter'),
            (aligned, 'align(TlsBitmap)'),
            (PVOID, 'TlsBitmap'),           # FIXME: Does TlsBitmapBits represent the number of bytes that are in use?
            (pbinary.littleendian(dyn.clone(pbinary.array, _object_=1, length=32*2)), 'TlsBitmapBits'),
            (PVOID, 'ReadOnlySharedMemoryBase'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append((PVOID, 'HotpatchInformation'))
        else:
            f.append((PVOID, 'ReadOnlySharedMemoryHeap'))

        f.extend([
            (P(PVOID), 'ReadOnlyStaticServerData'),
            (PVOID, 'AnsiCodePageData'),
            (PVOID, 'OemCodePageData'),
            (PVOID, 'UnicodeCaseTableData'),
            (ULONG, 'NumberOfProcessors'),
            (pbinary.littleendian(PEB.NtGlobalFlag), 'NtGlobalFlag'),
            (dyn.align(8), 'Reserved'),
            (LARGE_INTEGER, 'CriticalSectionTimeout'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'HeapSegmentReserve'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'HeapSegmentCommit'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'HeapDeCommitTotalFreeThreshold'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'HeapDeCommitFreeBlockThreshold'),
            (ULONG, 'NumberOfHeaps'),
            (ULONG, 'MaximumNumberOfHeaps'),
            (lambda s: P(dyn.clone(heaptypes.ProcessHeapEntries, length=s['NumberOfHeaps'].li.int())), 'ProcessHeaps'),
#            (P(win32k.GDI_HANDLE_TABLE), 'GdiSharedHandleTable'),
            (PVOID, 'GdiSharedHandleTable'),
            (PVOID, 'ProcessStarterHelper'),
            (ULONG, 'GdiDCAttributeList'),
        ])

        f.extend([
            (aligned, 'align(LoaderLock)'),
            (P(rtltypes._RTL_CRITICAL_SECTION), 'LoaderLock')
        ])

        f.extend([
            (ULONG, 'OSMajorVersion'),
            (ULONG, 'OSMinorVersion'),
            (USHORT, 'OSBuildNumber'),
            (USHORT, 'OSCSDVersion'),
            (ULONG, 'OSPlatformId'),
            (ULONG, 'ImageSubSystem'),
            (ULONG, 'ImageSubSystemMajorVersion'),
            (ULONG, 'ImageSubSystemMinorVersion'),
            (aligned, 'align(ActiveProcessAffinityMask)'),
            (ULONG, 'ActiveProcessAffinityMask'),
            (aligned, 'align(GdiHandleBuffer)'),
            (dyn.array(ULONG,0x3c if getattr(self,'WIN64',False) else 0x22), 'GdiHandleBuffer'),
            (PVOID, 'PostProcessInitRoutine'),
            (PVOID, 'TlsExpansionBitmap'),
            (dyn.array(ULONG,0x20), 'TlsExpansionBitmapBits'),
            (ULONG, 'SessionId'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINXP:
            f.extend([
                (aligned, 'align(AppCompatFlags)'),
                (ULARGE_INTEGER, 'AppCompatFlags'),
                (ULARGE_INTEGER, 'AppCompatFlagsUser'),
                (PVOID, 'pShimData'),
                (PVOID, 'AppCompatInfo'),
                (umtypes.UNICODE_STRING, 'CSDVersion'),
                (PVOID, 'ActivationContextData'),  # FIXME: P(_ACTIVATION_CONTEXT_DATA)
                (PVOID, 'ProcessAssemblyStorageMap'), # FIXME: P(_ASSEMBLY_STORAGE_MAP)
                (PVOID, 'SystemDefaultActivationContextData'), # FIXME: P(_ACTIVATION_CONTEXT_DATA)
                (PVOID, 'SystemAssemblyStorageMap'),  # FIXME: P(_ASSEMBLY_STORAGE_MAP)
                (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'MinimumStackCommit'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WS03:
            f.extend([
                (PVOID, 'FlsCallback'),  # FIXME: P(_FLS_CALLBACK_INFO)
                (LIST_ENTRY, 'FlsListHead'),
                (PVOID, 'FlsBitmap'),
                (dyn.array(ULONG,4), 'FlsBitmapBits'),
                (ULONG, 'FlsHighIndex'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (aligned, 'align(WerRegistrationData)'),
                (PVOID, 'WerRegistrationData'),
                (PVOID, 'WerShipAssertPtr'),
                (PVOID, 'pContextData'),
                (PVOID, 'pImageHeaderHash'),
                (pbinary.littleendian(PEB.TracingFlags), 'TracingFlags')
            ])

        # FIXME: Some fields added for windows 8
        # See https://www.geoffchappell.com/studies/windows/win32/ntdll/structs/peb/index.htm
        return

    def getmodulebyname(self, name):
        ldr = self['Ldr'].d.l
        for m in ldr.walk():
            if m['BaseDllName'].str() == name:
                return m
            continue
        raise KeyError(name)

    def getmodulebyaddress(self, address):
        ldr = self['Ldr'].d.l
        for m in ldr.walk():
            start,size = m['DllBase'].int(),m['SizeOfImage'].int()
            left,right = start, start+size
            if address >= left and address <= right:
                return m
            continue
        raise KeyError(name)

    def getmodulebyfullname(self, name):
        ldr = self['Ldr'].d.l
        name = name.lower().replace('\\', '/')
        for m in ldr.walk():
            if m['FullDllName'].str().lower().replace('\\', '/') == name:
                return m
            continue
        raise KeyError(name)

class TEB_ACTIVE_FRAME_CONTEXT(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (P(umtypes.PSTR), 'FrameName'),
    ]

class TEB_ACTIVE_FRAME(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (lambda s: P(TEB_ACTIVE_FRAME), 'Previous'),
        (P(TEB_ACTIVE_FRAME_CONTEXT), 'Context'),
    ]
class PTEB_ACTIVE_FRAME(P(TEB_ACTIVE_FRAME)): pass

class GDI_TEB_BATCH(pstruct.type):
    _fields_ = [
        (ULONG, 'Offset'),
        (HANDLE, 'HDC'),
        (dyn.array(ULONG,0x136), 'Buffer'),
    ]

class TEB(pstruct.type, versioned):
    class SameTebFlags(pbinary.flags):
        _fields_ = [
            (1, 'DbgSafeThunkCall'),
            (1, 'DbgInDebugPrint'),
            (1, 'DbgHasFiberData'),
            (1, 'DbgSkipThreadAttach'),
            (1, 'DbgWerInShipAssertCode'),
            (1, 'DbgRanProcessInit'),
            (1, 'DbgClonedThread'),
            (1, 'DbgSupressDebugMsg'),
            (1, 'DbgDisableUserStackWalk'),
            (1, 'DbgRtlExceptionAttached'),
            (1, 'DbgInitialThread'),
            (5, 'SpareSameTebBits'),
        ]

    def __init__(self, **attrs):
        super(TEB, self).__init__(**attrs)
        self._fields_ = f = []
        aligned = dyn.align(8 if getattr(self,'WIN64',False) else 4)

        f.extend([
            (NT_TIB, 'Tib'),
            (PVOID, 'EnvironmentPointer'),
            (umtypes.CLIENT_ID, 'Cid'),
            (PVOID, 'ActiveRpcHandle'),
            (PVOID, 'ThreadLocalStoragePointer'),
            (P(PEB), 'ProcessEnvironmentBlock'),
            (ULONG, 'LastErrorValue'),
            (ULONG, 'CountOfOwnedCriticalSections'),
            (PVOID, 'CsrClientThread'),
            (P(Ntddk.W32THREAD), 'Win32ThreadInfo'),
            (dyn.array(ULONG,0x1a), 'User32Reserved'),
            (dyn.array(ULONG,5), 'UserReserved'),
            (aligned, 'align(WOW32Reserved)'),
            (PVOID, 'WOW32Reserved'),
            (LCID, 'CurrentLocale'),
            (ULONG, 'FpSoftwareStatusRegister'),
            (dyn.array(PVOID,0x36), 'SystemReserved1'),
            (LONG, 'ExceptionCode'),
            (aligned, 'align(ActivationContextStackPointer)'),
            (P(Ntddk.ACTIVATION_CONTEXT_STACK), 'ActivationContextStackPointer'),
        ])

        f.append((dyn.block(24 if getattr(self,'WIN64',False) else 0x24), 'SpareBytes1'))

        f.extend([
            (ULONG, 'TxFsContext'),
            (aligned, 'align(GdiTebBatch)'),
            (GDI_TEB_BATCH, 'GdiTebBatch'),
            (aligned, 'align(RealClientId)'),
            (umtypes.CLIENT_ID, 'RealClientId'),
            (PVOID, 'GdiCachedProcessHandle'),
            (ULONG, 'GdiClientPID'),
            (ULONG, 'GdiClientTID'),
            (PVOID, 'GdiThreadLocalInfo'),
            (dyn.array(PVOID,62), 'Win32ClientInfo'),
            (dyn.array(PVOID,0xe9), 'glDispatchTable'),
            (dyn.array(PVOID,0x1d), 'glReserved1'),
            (PVOID, 'glReserved2'),
            (PVOID, 'glSectionInfo'),
            (PVOID, 'glSection'),
            (PVOID, 'glTable'),
            (PVOID, 'glCurrentRC'),
            (PVOID, 'glContext'),
            (aligned, 'align(LastStatusValue)'),
            (umtypes.NTSTATUS, 'LastStatusValue'),
            (aligned, 'align(StaticUnicodeString)'),
            (umtypes.UNICODE_STRING, 'StaticUnicodeString'),
#            (WCHAR, 'StaticUnicodeBuffer[0x105]'),
            (dyn.clone(pstr.wstring, length=0x106), 'StaticUnicodeBuffer'),
            (aligned, 'align(DeallocationStack)'),
            (PVOID, 'DeallocationStack'),
            (dyn.array(PVOID,0x40), 'TlsSlots'),
            (LIST_ENTRY, 'TlsLinks'),
            (PVOID, 'Vdm'),
            (PVOID, 'ReservedForNtRpc'),
            (dyn.array(PVOID,0x2), 'DbgSsReserved'),
            (ULONG, 'HardErrorMode'),
        ])

        f.extend([
            (aligned, 'align(Instrumentation)'),
            (dyn.array(PVOID,11 if getattr(self,'WIN64',False) else 9), 'Instrumentation')
        ])

        f.extend([
            (GUID, 'ActivityId'),
            (PVOID, 'SubProcessTag'),
            (PVOID, 'EtwTraceData'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append((PVOID, 'EtwLocalData'))

        f.extend([
            (PVOID, 'WinSockData'),
            (ULONG, 'GdiBatchCount'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (UCHAR, 'SpareBool0'),
                (UCHAR, 'SpareBool1'),
                (UCHAR, 'SpareBool2'),
            ])
        else:
            f.extend([
                (UCHAR, 'InDbgPrint'),
                (UCHAR, 'FreeStackOnTermination'),
                (UCHAR, 'HasFiberData'),
            ])

        f.extend([
            (UCHAR, 'IdealProcessor'),
            (ULONG, 'GuaranteedStackBytes'),
            (aligned, 'align(ReservedForPerf)'),
            (PVOID, 'ReservedForPerf'),
            (PVOID, 'ReservedForOle'),
            (ULONG, 'WaitingOnLoaderLock'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append((aligned, 'align(SavedPriorityState)'))
            f.append((PVOID, 'SavedPriorityState'))
        else:
            f.append((ULONG, 'SparePointer1'))

        f.extend([
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'SoftPatchPtr1'),
            (PVOID, 'ThreadPoolData'),
            (PVOID, 'TlsExpansionSlots'),
        ])

        if getattr(self, 'WIN64', False):
            f.extend([
                (PVOID, 'DeallocationBStore'),
                (PVOID, 'BStoreLimit'),
            ])

        f.extend([
            (ULONG, 'MuiGeneration'),
            (ULONG, 'IsImpersonating'),
            (PVOID, 'NlsCache'),
            (PVOID, 'pShimData'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
            f.append((ULONG, 'LowFragHeapDataSlot'))
        else:
            f.append((ULONG, 'HeapVirtualAffinity'))

        f.extend([
            (aligned, 'align(CurrentTransactionHandle)'),
            (PVOID, 'CurrentTransactionHandle'),
            (PTEB_ACTIVE_FRAME, 'ActiveFrame'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.append((PVOID, 'FlsData'))

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.extend([
                (PVOID, 'PreferredLangauges'),
                (PVOID, 'UserPrefLanguages'),
                (PVOID, 'MergedPrefLanguages'),
                (ULONG, 'MuiImpersonation'),
                (USHORT, 'CrossTebFlags'),
                (TEB.SameTebFlags, 'SameTebFlags'),   # XXX
                (PVOID, 'TxnScopeEntercallback'),
                (PVOID, 'TxnScopeExitCAllback'),
                (PVOID, 'TxnScopeContext'),
                (ULONG, 'LockCount'),
                (ULONG, 'SpareUlong0'),
                (PVOID, 'ResourceRetValue'),
            ])
        return

class THREAD_INFORMATION_CLASS(pint.enum):
    _values_ = [(n,v) for v,n in (
        (0, 'ThreadBasicInformation'),
        (1, 'ThreadTimes'),
        (2, 'ThreadPriority'),
        (3, 'ThreadBasePriority'),
        (4, 'ThreadAffinityMask'),
        (5, 'ThreadImpersonationToken'),
        (6, 'ThreadDescriptorTableEntry'),
        (7, 'ThreadEnableAlignmentFaultFixup'),
        (8, 'ThreadEventPair'),
        (9, 'ThreadQuerySetWin32StartAddress'),
        (10, 'ThreadZeroTlsCell'),
        (11, 'ThreadPerformanceCount'),
        (12, 'ThreadAmILastThread'),
        (13, 'ThreadIdealProcessor'),
        (14, 'ThreadPriorityBoost'),
        (15, 'ThreadSetTlsArrayAddress'),
        (16, 'ThreadIsIoPending'),
        (17, 'ThreadHideFromDebugger'),
        (18, 'ThreadBreakOnTermination'),
        (19, 'ThreadSwitchLegacyState'),
        (20, 'ThreadIsTerminated'),
        (21, 'ThreadLastSystemCall'),
        (22, 'ThreadIoPriority'),
        (23, 'ThreadCycleTime'),
        (24, 'ThreadPagePriority'),
        (25, 'ThreadActualBasePriority'),
        (26, 'ThreadTebInformation'),
        (27, 'ThreadCSwitchMon'),
        (28, 'ThreadCSwitchPmu'),
        (29, 'ThreadWow64Context'),
        (30, 'ThreadGroupInformation'),
        (31, 'ThreadUmsInformation'),
        (32, 'ThreadCounterProfiling'),
        (33, 'ThreadIdealProcessorEx'),
        (34, 'ThreadCpuAccountingInformation'),
        (35, 'ThreadSuspendCount'),
        (36, 'ThreadHeterogeneousCpuPolicy'),
        (37, 'ThreadContainerId'),
        (38, 'ThreadNameInformation'),
        (39, 'ThreadProperty'),
        (40, 'ThreadSelectedCpuSets'),
        (41, 'ThreadSystemThreadInformation'),
    )]

class THREAD_BASIC_INFORMATION(pstruct.type, versioned):
    type = THREAD_INFORMATION_CLASS.byname('ThreadBasicInformation')
    def __init__(self, **attrs):
        super(THREAD_BASIC_INFORMATION, self).__init__(**attrs)
        self._fields_ = [
            (umtypes.NTSTATUS, 'ExitStatus'),
            (PVOID, 'TebBaseAddress'),
            (umtypes.CLIENT_ID, 'ClientId'),
            (umtypes.KAFFINITY, 'AffinityMask'),
            (umtypes.KPRIORITY, 'Priority'),
            (umtypes.KPRIORITY, 'BasePriority'),
        ]

class THREAD_PROPERTY_INFORMATION(pstruct.type):
    type = THREAD_INFORMATION_CLASS.byname('ThreadProperty')
    _fields_ = [
        (ULONGLONG, 'Key'),
        (PVOID, 'Object'),
        (PVOID, 'Thread'),
        (ULONG, 'Flags'),
    ]

class PROCESS_INFORMATION_CLASS(pint.enum):
    _values_ = [(n,v) for v,n in (
        (0, 'ProcessBasicInformation'),
        (1, 'ProcessQuotaLimits'),
        (2, 'ProcessIoCounters'),
        (3, 'ProcessVmCounters'),
        (4, 'ProcessTimes'),
        (5, 'ProcessBasePriority'),
        (6, 'ProcessRaisePriority'),
        (7, 'ProcessDebugPort'),
        (8, 'ProcessExceptionPort'),
        (9, 'ProcessAccessToken'),
        (9, 'ProcessLdtInformation'),
        (10, 'ProcessLdtSize'),
        (11, 'ProcessDefaultHardErrorMode'),
        (12, 'ProcessIoPortHandlers'),
        (13, 'ProcessPooledUsageAndLimits'),
        (14, 'ProcessWorkingSetWatch'),
        (15, 'ProcessUserModeIOPL'),
        (16, 'ProcessEnableAlignmentFaultFixup'),
        (17, 'ProcessPriorityClass'),
        (18, 'ProcessWx86Information'),
        (19, 'ProcessHandleCount'),
        (20, 'ProcessAffinityMask'),
        (21, 'ProcessPriorityBoost'),
        (22, 'ProcessDeviceMap'),
        (23, 'ProcessSessionInformation'),
        (24, 'ProcessForegroundInformation'),
        (25, 'ProcessWow64Information'),
        (26, 'ProcessImageFileName'),
        (27, 'ProcessLUIDDeviceMapsEnabled'),
        (28, 'ProcessBreakOnTermination'),
        (29, 'ProcessDebugObjectHandle'),
        (30, 'ProcessDebugFlags'),
        (31, 'ProcessHandleTracing'),
        (32, 'ProcessIoPriority'),
        (33, 'ProcessExecuteFlags'),
        (34, 'ProcessResourceManagement'),
        (35, 'ProcessCookie'),
        (36, 'ProcessImageInformation'),
        (37, 'ProcessCycleTime'),
        (38, 'ProcessPagePriority'),
        (39, 'ProcessInstrumentationCallback'),
        (40, 'ProcessThreadStackAllocation'),
        (41, 'ProcessWorkingSetWatchEx'),
        (42, 'ProcessImageFileNameWin32'),
        (43, 'ProcessImageFileMapping'),
        (44, 'ProcessAffinityUpdateMode'),
        (45, 'ProcessMemoryAllocationMode'),
        (46, 'ProcessGroupInformation'),
        (47, 'ProcessTokenVirtualizationEnabled'),
        (48, 'ProcessConsoleHostProcess'),
        (49, 'ProcessWindowInformation'),
        (50, 'ProcessHandleInformation'),
        (51, 'ProcessMitigationPolicy'),
        (52, 'ProcessDynamicFunctionTableInformation'),
        (53, 'ProcessHandleCheckingMode'),
        (54, 'ProcessKeepAliveCount'),
        (55, 'ProcessRevokeFileHandles'),
        (56, 'ProcessWorkingSetControl'),
        (57, 'ProcessHandleTable'),
        (58, 'ProcessCheckStackExtentsMode'),
        (59, 'ProcessCommandLineInformation'),
        (60, 'ProcessProtectionInformation'),
        (61, 'ProcessMemoryExhaustion'),
        (62, 'ProcessFaultInformation'),
        (63, 'ProcessTelemetryIdInformation'),
        (64, 'ProcessCommitReleaseInformation'),
        (65, 'ProcessDefaultCpuSetsInformation'),
        (66, 'ProcessAllowedCpuSetsInformation'),
        (67, 'ProcessReserved1Information'),
        (68, 'ProcessReserved2Information'),
        (69, 'ProcessSubsystemProcess'),
        (70, 'ProcessJobMemoryInformation'),
    )]

class PROCESS_MEMORY_EXHAUSTION_TYPE(pint.enum, ULONG):
    _values_ = [(n,v) for v,n in (
        (0, 'PMETypeFaultFastOnCommitFailure'),
    )]

class PROCESS_MEMORY_EXHAUSTION_INFO(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessMemoryExhaustion')
    _fields_ = [
        (USHORT, 'Version'),
        (USHORT, 'Reserved'),
        (PROCESS_MEMORY_EXHAUSTION_TYPE, 'Value'),
        (ULONGLONG, 'Value'),
    ]

class PROCESS_FAULT_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessFaultInformation')
    _fields_ = [
        (ULONG, 'FaultFlags'),
        (ULONG, 'AdditionalInfo'),
    ]

class PROCESS_TELEMETRY_ID_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessTelemetryIdInformation')
    _fields_ = [
        (ULONG, 'HeaderSize'),
        (ULONG, 'ProcessId'),
        (ULONGLONG, 'ProcessStartKey'),
        (ULONGLONG, 'CreateTime'),
        (ULONGLONG, 'CreateInterruptTime'),
        (ULONGLONG, 'ProcessSequenceNumber'),
        (ULONGLONG, 'SessionCreateTime'),
        (ULONG, 'SessionId'),
        (ULONG, 'BootId'),
        (ULONG, 'ImageChecksum'),
        (ULONG, 'ImageTimeDateStamp'),
        (ULONG, 'UserIdOffset'),
        (ULONG, 'ImagePathOffset'),
        (ULONG, 'PackageNameOffset'),
        (ULONG, 'RelativeAppNameOffset'),
        (ULONG, 'CommandLineOffset'),
    ]

@pbinary.littleendian
class API_SET_SCHEMA_FLAGS_(pbinary.flags):
    _fields_ = [
        (30, 'unused'),
        (1, 'HOST_EXTENSION'),
        (1, 'SEALED'),
    ]

class API_SET_HEADER(pstruct.type):
    def __init__(self, **attrs):
        super(API_SET_HEADER, self).__init__(**attrs)
        self._fields_ = f = []

        # https://www.geoffchappell.com/studies/windows/win32/apisetschema/index.htm
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
           f.extend([
                (ULONG, 'Version'),
                (ULONG, 'Count'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
            f.extend([
                (ULONG, 'Version'),
                (ULONG, 'Size'),
                (API_SET_SCHEMA_FLAGS_, 'Flags'),
                (ULONG, 'Count'),
            ])

        else:
            raise error.ImplementationError(self, 'API_SET_HEADER.__init__')
        return

    def summary(self):
        res = []
        for fld in self:
            res.append("{:s}={:s}".format(fld, "{:#x}".format(self[fld].int()) if isinstance(self[fld], pint.type) else self[fld].summary()))
        return ' '.join(res)

class API_SET_VALUE_ENTRY(pstruct.type):
    class _Value(rpointer_t):
        _value_ = ULONG
        def summary(self):
            res = super(API_SET_VALUE_ENTRY._Value, self).summary()
            return '{:s} -> {!r}'.format(res, self.d.l.str())

        class _object_(pstr.wstring):
            def blocksize(self):
                try:
                    parent = self.getparent(API_SET_VALUE_ENTRY)
                    result = parent['Size'].li.int()
                except (error.NotFoundError, error.InitializationError):
                    result = 0
                return result

    def __Value(self):
        def _object_(self, parent=self):
            parent = self.getparent(API_SET_VALUE_ENTRY)
            res = parent['Size'].li.int()
            return dyn.clone(pstr.wstring, blocksize=lambda s,sz=res: sz)

        return dyn.clone(API_SET_VALUE_ENTRY._Value, _baseobject_=self._baseobject_, _object_=_object_)

    _fields_ = [
        (lambda s: dyn.clone(s._Value, _baseobject_=s._baseobject_), 'Value'),
        (ULONG, 'Size'),
    ]

class API_SET_VALUE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (ULONG, 'EndOfEntriesOffset'),
        (ULONG, 'Hash'),
        (lambda s: API_SET_VALUE_ENTRY if s['Count'].li.int() > 1 else ptype.undefined, 'OriginalRedirect'),
        (lambda s: dyn.array(API_SET_VALUE_ENTRY, s['Count'].li.int()), 'Entry'),
    ]

class API_SET_ENTRY(pstruct.type):
    _baseobject_ = None
    class _NameOffset(rpointer_t):
        _value_ = ULONG
        def summary(self):
            res = super(API_SET_ENTRY._NameOffset, self).summary()
            return '{:s} -> {!r}'.format(res, self.d.li.str())

        class _object_(pstr.wstring):
            def blocksize(self):
                try:
                    parent = self.getparent(API_SET_ENTRY)
                    result = parent['NameLength'].li.int()
                except (error.NotFoundError, error.InitializationError):
                    result = 0
                return result

    class _ValueOffset(rpointer_t):
        _value_ = ULONG
        _object_ = API_SET_VALUE

    _fields_ = [
        (lambda s: dyn.clone(s._NameOffset, _baseobject_=s._baseobject_), 'NameOffset'),
        (ULONG, 'NameLength'),
        (lambda s: dyn.clone(s._ValueOffset, _baseobject_=s._baseobject_), 'ValueOffset'),
    ]

class API_SET_MAP(pstruct.type, versioned):
    def __Entry(self):
        res = self['Header'].li
        return dyn.array(API_SET_ENTRY, res['Count'].int(), recurse={'_baseobject_':self})

    _fields_ = [
        (API_SET_HEADER, 'Header'),
        (__Entry, 'Entry'),
    ]

class KSYSTEM_TIME(pstruct.type):
    _fields_ = [
        (ULONG, 'LowPart'),
        (LONG, 'High1Time'),
        (LONG, 'High2Time'),
    ]

class WOW64_SHARED_INFORMATION(pint.enum):
    _values_ = [
        ('SharedNtdll32LdrInitializeThunk', 0),
        ('SharedNtdll32KiUserExceptionDispatcher', 1),
        ('SharedNtdll32KiUserApcDispatcher', 2),
        ('SharedNtdll32KiUserCallbackDispatcher', 3),
        ('SharedNtdll32LdrHotPatchRoutin', 4),
        ('SharedNtdll32ExpInterlockedPopEntry', 5),
        ('SharedNtdll32ExpInterlockedPopEntrySList', 6),
        ('SharedNtdll32ExpInterlockedPopEntrySListEn', 7),
        ('SharedNtdll32RtlUserThreadStar', 8),
        ('SharedNtdll32pQueryProcessDebugInfo', 9),
        ('SharedNtdll32EtwpNotificationThread', 10),
        ('SharedNtdll32BaseAddress', 11),
        ('Wow64SharedPageEntriesCount', 12),
    ]

class NT_PRODUCT_TYPE(pint.enum, ULONG):
    _values_ = [
        ('NtProductWinNt', 1),
        ('NtProductLanManNt', 2),
        ('NtProductServer', 3),
    ]
class ALTERNATIVE_ARCHITECTURE_TYPE(pint.enum, ULONG):
    _values_ = [
        ('StandardDesign', 0),
        ('NEC98x86', 1),
        ('EndAlternatives', 2),
    ]

class XSTATE_CONFIGURATION(pstruct.type):
    class FEATURE(pstruct.type):
        _fields_ = [(ULONG,'Offset'),(ULONG,'Size')]
    _fields_ = [
        (ULONGLONG, 'EnabledFeatures'),
        (ULONG, 'Size'),
        (ULONG, 'OptimizedSave'),
        (dyn.array(FEATURE,64), 'Features'),
    ]

class KUSER_SHARED_DATA(pstruct.type, versioned):
    class TscQpc(pbinary.struct):
        _fields_ = [
            (16, 'Pad'),
            (6, 'Shift'),
            (1, 'SpareFlag'),
            (1, 'Enabled'),
        ]

    class SharedDataFlags(pbinary.flags):
        _fields_ = [
            (25, 'SpareBits'),
            (1, 'DbgSEHValidationEnabled'),
            (1, 'DbgDynProcessorEnabled'),
            (1, 'DbgSystemDllRelocated'),
            (1, 'DbgInstallerDetectEnabled'),
            (1, 'DbgVirtEnabled'),
            (1, 'DbgElevationEnabled'),
            (1, 'DbgErrorPortPresent'),
        ]

    def __init__(self, **attrs):
        super(KUSER_SHARED_DATA, self).__init__(**attrs)
        self._fields_ = f = []

        PROCESSOR_MAX_FEATURES = 64

        f.extend([
            (ULONG, 'TickCountLowDeprecated'),
            (ULONG, 'TickCountMultiplier'),
            (KSYSTEM_TIME, 'InterruptTime'),
            (KSYSTEM_TIME, 'SystemTime'),
            (KSYSTEM_TIME, 'TimeZoneBias'),
            (USHORT, 'ImageNumberLow'),
            (USHORT, 'ImageNumberHigh'),
            (dyn.clone(pstr.wstring,length=260), 'NtSystemRoot'),
            (ULONG, 'MaxStackTraceDepth'),
            (ULONG, 'CryptoExponent'),
            (ULONG, 'TimeZoneId'),
            (ULONG, 'LargePageMinimum'),
            (dyn.array(ULONG,7), 'Reserved2'),
            (NT_PRODUCT_TYPE, 'NtProductType'),
            (BOOLEAN, 'ProductTypeIsValid'),
            (dyn.align(4), 'ProductTypeIsValidAlignment'),
            (ULONG, 'NtMajorVersion'),
            (ULONG, 'NtMinorVersion'),
            (dyn.array(BOOLEAN,PROCESSOR_MAX_FEATURES), 'ProcessorFeatures'),
            (ULONG, 'Reserved1'),
            (ULONG, 'Reserved3'),
            (ULONG, 'TimeSlip'),
            (ALTERNATIVE_ARCHITECTURE_TYPE, 'AlternativeArchitecture'),
            (ULONG, 'AltArchitecturePad'),
            (LARGE_INTEGER, 'SystemExpirationDate'),
            (ULONG, 'SuiteMask'),
            (BOOLEAN, 'KdDebuggerEnabled'),
            (UCHAR, 'NXSupportPolicy'),
            (dyn.align(4), 'ActiveConsoleAlignment'),
            (ULONG, 'ActiveConsoleId'),
            (ULONG, 'DismountCount'),
            (ULONG, 'ComPlusPackage'),
            (ULONG, 'LastSystemRITEventTickCount'),
            (ULONG, 'NumberOfPhysicalPages'),
            (BOOLEAN, 'SafeBootMode'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
            f.append((self.TscQpc, 'TscQpc'))
        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) > sdkddkver.NTDDI_WIN7:
            f.append((dyn.array(pint.uint8_t,4), 'Reserved12'))

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
            f.append((ULONG, 'TraceLogging'))
        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
            f.extend([
                (self.SharedDataFlags, 'SharedDataFlags'),
                (dyn.array(ULONG,1), 'DataFlagsPad'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) in (sdkddkver.NTDDI_WINXP, sdkddkver.NTDDI_WIN7):
            f.extend([
                (ULONGLONG, 'TestRetInstruction'),
                (ULONG, 'SystemCall'),
                (ULONG, 'SystemCallReturn'),
                (dyn.array(ULONGLONG,3), 'SystemCallPad'),
            ])

        f.extend([
            (KSYSTEM_TIME, 'TickCount'),
            (dyn.array(LONG,1), 'TickCountPad'),
            (ULONG, 'Cookie'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
            f.extend([
                (dyn.array(ULONG,1), 'CookiePad'),  # pad to what, a ULONGLONG?
                (LONGLONG, 'ConsoleSessionForegroundProcessId'),
                (dyn.array(ULONG,16), 'Wow64SharedInformation'),
                (dyn.array(USHORT,16), 'UserModeGlobalLogger'),
                (ULONG, 'ImageFileExecutionOptions'),
                (ULONG, 'LangGenerationCount'),
                (ULONGLONG, 'Reserved5'),
                (ULONGLONG, 'InterruptTimeBias'),
                (ULONGLONG, 'TscQpcBias'),
                (ULONG, 'ActiveProcessorCount'),
                (USHORT, 'ActiveGroupCount'),
                (USHORT, 'Reserved4'),
                (ULONG, 'AitSamplingValue'),
                (ULONG, 'AppCompatFlag'),
                (ULONGLONG, 'SystemDllNativeRelocation'),
                (ULONGLONG, 'SystemDllWowRelocation'),
#                (dyn.array(LONG,1), 'XStatePad'),
#                (dyn.align(0x10), 'XStatePad'),    # ???
                (XSTATE_CONFIGURATION, 'XState'),
            ])
        return

if __name__ == '__main__':
    import ctypes
    def openprocess (pid):
        k32 = ctypes.WinDLL('kernel32.dll')
        res = k32.OpenProcess(0x30 | 0x0400, False, pid)
        return res

    def getcurrentprocess ():
        k32 = ctypes.WinDLL('kernel32.dll')
        return k32.GetCurrentProcess()

    def getPBIObj (handle):
        nt = ctypes.WinDLL('ntdll.dll')
        class ProcessBasicInformation(ctypes.Structure):
            _fields_ = [('Reserved1', ctypes.c_uint32),
                        ('PebBaseAddress', ctypes.c_uint32),
                        ('Reserved2', ctypes.c_uint32 * 2),
                        ('UniqueProcessId', ctypes.c_uint32),
                        ('Reserved3', ctypes.c_uint32)]

        pbi = ProcessBasicInformation()
        res = nt.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
        return pbi

    handle = getcurrentprocess()
    pebaddress = getPBIObj(handle).PebBaseAddress

    import ptypes,pstypes

    Peb = pstypes.PEB()
    Peb.setoffset(pebaddress)
    Peb.load()

    Ldr = Peb['Ldr'].d.l
    for x in Ldr['InLoadOrderModuleList'].walk():
        print x['BaseDllName'].str(),x['FullDllName'].str()
        print hex(x['DllBase'].int()), hex(x['SizeOfImage'].int())
