from ptypes import *
from WinNT import *
import ldrtypes,rtltypes,umtypes,Ntddk
import heaptypes,sdkddkver

class PEB_FREE_BLOCK(pstruct.type): pass
class PPEB_FREE_BLOCK(dyn.pointer(PEB_FREE_BLOCK)): pass
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
            ofs = '[%x]'% self.getoffset()
            names = '|'.join((k for k,v in self.items() if v))
            return ' '.join([ofs, self.name(), names, repr(self.serialize())])

    def __init__(self, **attrs):
        super(PEB, self).__init__(**attrs)

        self._fields_ = f = []
        f.extend([
            (UCHAR, 'InheritedAddressSpace'),
            (UCHAR, 'ReadImageFileExecOptions'),
            (UCHAR, 'BeingDebugged'),
        ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append( (self.BitField, 'BitField') )
        else:
            f.append( (BOOLEAN, 'SpareBool') )

        f.extend([
            (HANDLE, 'Mutant'),
            (PVOID, 'ImageBaseAddress'),
            (ldrtypes.PPEB_LDR_DATA, 'Ldr'),
            ##
            (dyn.pointer(rtltypes._RTL_USER_PROCESS_PARAMETERS), 'ProcessParameters'),
            (pint.uint32_t, 'SubSystemData'),
            (dyn.pointer(heaptypes._HEAP), 'ProcessHeap'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.extend([
                (pint.uint32_t, 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (ULONG, 'CrossProcessFlags'),
                (PVOID, 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'SpareUlong'),
                (dyn.pointer(API_SET_MAP, type=ULONG), 'ApiSetMap'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (pint.uint32_t, 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (ULONG, 'CrossProcessFlags'),
                (PVOID, 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'SpareUlong'),
                (ULONG, 'SparePebPtr0'),
            ])
        else:
            f.extend([
                (PVOID, 'FastPebLock'),
                (pint.uint32_t, 'FastPebLockRoutine'),
                (pint.uint32_t, 'FastPebUnlockRoutine'),
                (ULONG, 'EnvironmentUpdateCount'),
                (pint.uint32_t, 'KernelCallbackTable'),
                (PVOID, 'EventLogSection'),
                (PVOID, 'EventLog'),
                (PPEB_FREE_BLOCK, 'FreeList'),
            ])

        f.extend([
            (ULONG, 'TlxExpansionCounter'),
            (PVOID, 'TlsBitmap'),
            (dyn.array(ULONG,2), 'TlsBitmapBits'),
            (PVOID, 'ReadOnlySharedMemoryBase'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append( (PVOID, 'HotpatchInformation') )
        else:
            f.append( (PVOID, 'ReadOnlySharedMemoryHeap') )

        f.extend([
            (PVOID, 'ReadOnlyStaticServerData'),
            (PVOID, 'AnsiCodePageData'),
            (PVOID, 'OemCodePageData'),
            (PVOID, 'UnicodeCaseTableData'),
            (ULONG, 'NumberOfProcessors'),
#            (ULONG, 'NtGlobalFlag'),
            (PEB.NtGlobalFlag, 'NtGlobalFlag'),
            (ULONG, 'Reserved'),
            (LARGE_INTEGER, 'CriticalSectionTimeout'),
            (ULONG, 'HeapSegmentReserve'),
            (ULONG, 'HeapSegmentCommit'),
            (ULONG, 'HeapDeCommitTotalFreeThreshold'),
            (ULONG, 'HeapDeCommitFreeBlockThreshold'),
            (ULONG, 'NumberOfHeaps'),
            (ULONG, 'MaximumNumberOfHeaps'),
            (lambda s: dyn.pointer( dyn.clone(heaptypes.ProcessHeapEntries, length=s['NumberOfHeaps'].li.num()), PVOID), 'ProcessHeaps'),
#            (dyn.pointer(win32k.GDI_HANDLE_TABLE), 'GdiSharedHandleTable'),
            (PVOID, 'GdiSharedHandleTable'),
            (PVOID, 'ProcessStarterHelper'),
            (ULONG, 'GdiDCAttributeList'),
        ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append( (PVOID, 'LoaderLock') )
        else:
            f.append( (PVOID, 'LoaderLock') )

        f.extend([
            (ULONG, 'OSMajorVersion'),
            (ULONG, 'OSMinorVersion'),
            (USHORT, 'OSBuildNumber'),
            (USHORT, 'OSCSDVersion'),
            (ULONG, 'OSPlatformId'),
            (ULONG, 'ImageSubSystem'),
            (ULONG, 'ImageSubSystemMajorVersion'),
            (ULONG, 'ImageSubSystemMinorVersion'),
            (ULONG, 'ImageProcessAffinityMask'),
            (dyn.array(ULONG,0x22), 'GdiHandleBuffer'),
            (pint.uint32_t, 'PostProcessInitRoutine'),
            (pint.uint32_t, 'TlsExpansionBitmap'),
            (dyn.array(ULONG,0x20), 'TlsExpansionBitmapBits'),
            (ULONG, 'SessionId'),
        ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINXP:
            f.extend([
                (ULARGE_INTEGER, 'AppCompatFlags'),
                (ULARGE_INTEGER, 'AppCompatFlagsUser'),
                (PVOID, 'pShimData'),
                (PVOID, 'AppCompatInfo'),
                (umtypes.UNICODE_STRING, 'CSDVersion'),
                (pint.uint32_t, 'ActivationContextData'),
                (pint.uint32_t, 'ProcessAssemblyStorageMap'),
                (pint.uint32_t, 'SystemDefaultActivationContextData'),
                (pint.uint32_t, 'SystemAssemblyStorageMap'),
                (ULONG, 'MinimumStackCommit'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WS03:
            f.extend([
                (PVOID, 'FlsCallback'),
                (LIST_ENTRY, 'FlsListHead'),
                (pint.uint32_t, 'FlsBitmap'),
                (dyn.array(ULONG,4), 'FlsBitmapBits'),
                (ULONG, 'FlsHighIndex'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (PVOID, 'WerRegistrationData'),
                (PVOID, 'WerShipAssertPtr'),

                (PVOID, 'pContextData'),
                (PVOID, 'pImageHeaderHash'),

## FIXME: not sure what this means in the pdb structure...
#   +0x240 TracingFlags     : 0
#   +0x240 HeapTracingEnabled : 0y0
#   +0x240 CritSecTracingEnabled : 0y0
#   +0x240 SpareTracingBits : 0y000000000000000000000000000000 (0)
            ])
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
            start,size = m['DllBase'].num(),m['SizeOfImage'].num()
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
        (dyn.pointer(umtypes.PSTR), 'FrameName'),
    ]

class TEB_ACTIVE_FRAME(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (lambda s: dyn.pointer(TEB_ACTIVE_FRAME), 'Previous'),
        (dyn.pointer(TEB_ACTIVE_FRAME_CONTEXT), 'Context'),
    ]
class PTEB_ACTIVE_FRAME(dyn.pointer(TEB_ACTIVE_FRAME)): pass

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
            (1, 'DbgIssuedInitialBp'),
            (1, 'DbgClonedThread'),
            (9, 'SpareSameTebBits'),
        ]

    def __init__(self, **attrs):
        super(TEB, self).__init__(**attrs)
        self._fields_ = f = []

        f.extend([
            (NT_TIB, 'Tib'),
            (PVOID, 'EnvironmentPointer'),
            (umtypes.CLIENT_ID, 'Cid'),
            (PVOID, 'ActiveRpcHandle'),
            (PVOID, 'ThreadLocalStoragePointer'),
            (dyn.pointer(PEB), 'ProcessEnvironmentBlock'),
            (ULONG, 'LastErrorValue'),
            (ULONG, 'CountOfOwnedCriticalSections'),
            (PVOID, 'CsrClientThread'),
            (dyn.pointer(Ntddk.W32THREAD), 'Win32ThreadInfo'),
            (dyn.array(ULONG,0x1a), 'User32Reserved'),
            (dyn.array(ULONG,5), 'UserReserved'),
            (PVOID, 'WOW32Reserved'),
            (LCID, 'CurrentLocale'),
            (ULONG, 'FpSoftwareStatusRegister'),
            (dyn.array(PVOID,0x36), 'SystemReserved1'),
            (LONG, 'ExceptionCode'),
            (dyn.pointer(Ntddk.ACTIVATION_CONTEXT_STACK), 'ActivationContextStackPointer'),
        ])

        if self.WIN64:
            f.append((dyn.block(24), 'SpareBytes1'))
        else:
            f.append((dyn.block(0x24), 'SpareBytes1'))

        f.extend([
            (ULONG, 'TxFsContext'),
            (GDI_TEB_BATCH, 'GdiTebBatch'),
            (umtypes.CLIENT_ID, 'RealClientId'),
            (PVOID, 'GdiCachedProcessHandle'),
            (ULONG, 'GdiClientPID'),
            (ULONG, 'GdiClientTID'),
            (PVOID, 'GdiThreadLocalInfo'),
            (dyn.array(SIZE_T,62), 'Win32ClientInfo'),
            (dyn.array(PVOID,0xe9), 'glDispatchTable'),
            (dyn.array(SIZE_T,0x1d), 'glReserved1'),
            (PVOID, 'glReserved2'),
            (PVOID, 'glSectionInfo'),
            (PVOID, 'glSection'),
            (PVOID, 'glTable'),
            (PVOID, 'glCurrentRC'),
            (PVOID, 'glContext'),
            (umtypes.NTSTATUS, 'LastStatusValue'),
            (umtypes.UNICODE_STRING, 'StaticUnicodeString'),
#            (WCHAR, 'StaticUnicodeBuffer[0x105]'),
            (dyn.clone(pstr.wstring, length=0x106), 'StaticUnicodeBuffer'),
            (PVOID, 'DeallocationStack'),
            (dyn.array(PVOID,0x40), 'TlsSlots'),
            (LIST_ENTRY, 'TlsLinks'),
            (PVOID, 'Vdm'),
            (PVOID, 'ReservedForNtRpc'),
            (dyn.array(PVOID,0x2), 'DbgSsReserved'),
            (ULONG, 'HardErrorDisabled'),
        ])

        if self.WIN64:
            f.append((dyn.array(PVOID,11), 'Instrumentation'))
        else:
            f.append((dyn.array(PVOID,9), 'Instrumentation'))

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
            (PVOID, 'ReservedForPerf'),
            (PVOID, 'ReservedForOle'),
            (ULONG, 'WaitingOnLoaderLock'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.append((PVOID, 'SavedPriorityState'))
        else:
            f.append((ULONG, 'SparePointer1'))

        f.extend([
            (ULONG, 'SoftPatchPtr1'),
            (PVOID, 'ThreadPoolData'),
            (PVOID, 'TlsExpansionSlots'),
            (ULONG, 'ImpersonationLocale'),
            (ULONG, 'IsImpersonating'),
            (PVOID, 'NlsCache'),
            (PVOID, 'pShimData'),
            (ULONG, 'HeapVirualAffinity'),
            (PVOID, 'CurrentTransactionHandle'),
            (PTEB_ACTIVE_FRAME, 'ActiveFrame'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WS03:
            f.append((PVOID, 'FlsData'))

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (PVOID, 'PreferredLangauges'),
                (PVOID, 'UserPrefLanguages'),
                (PVOID, 'MergedPrefLanguages'),
                (ULONG, 'MuiImpersonation'),
                (USHORT, 'CrossTebFlags'),
                (self.SameTebFlags, 'SameTebFlags'),   # XXX
                (PVOID, 'TxnScopeEntercallback'),
                (PVOID, 'TxnScopeExitCAllback'),
                (PVOID, 'TxnScopeContext'),
                (ULONG, 'LockCount'),
                (ULONG, 'ProcessRundown'),
                (ULONGLONG, 'LastSwitchTime'),
                (ULONGLONG, 'TotalSwitchOutTime'),
                (LARGE_INTEGER, 'WaitReasonBitMap'),
            ])
        else:
            f.extend([
                (UCHAR, 'SafeThunkCall'),
                (dyn.block(UCHAR,3), 'BooleanSpare'),
            ])
        return

class THREAD_BASIC_INFORMATION(pstruct.type):
    _fields_ = [
        (umtypes.NTSTATUS, 'ExitStatus'),
        (PVOID, 'TebBaseAddress'),
        (umtypes.CLIENT_ID, 'ClientId'),
        (umtypes.KAFFINITY, 'AffinityMask'),
        (umtypes.KPRIORITY, 'Priority'),
        (umtypes.KPRIORITY, 'BasePriority'),
    ]

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
    )]

class _API_SET_HEADER(pstruct.type):
    _fields_ = [
        (ULONG, 'Version'),
        (ULONG, 'Count'),
    ]

class _API_SET_VALUE_ENTRY(pstruct.type):
    _fields_ = [
        (lambda s: dyn.rpointer((lambda _:dyn.clone(pstr.wstring,blocksize=lambda _:s['Size'].li.num())), object=s._baseobject_, type=ULONG, summary=lambda _:'{:s} -> {!r}'.format(super(ptype.rpointer_t,_).summary(),_.d.l.str())), 'Value'),
        (ULONG, 'Size'),
    ]

class _API_SET_VALUE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (ULONG, 'EndOfEntriesOffset'),
        (ULONG, 'Hash'),
        (lambda s: _API_SET_VALUE_ENTRY if s['Count'].li.num() > 1 else ptype.undefined, 'OriginalRedirect'),
        (lambda s: dyn.array(_API_SET_VALUE_ENTRY, s['Count'].li.num()), 'Entry'),
    ]

class _API_SET_ENTRY(pstruct.type):
    _baseobject_ = None
    _fields_ = [
        (lambda s: dyn.rpointer((lambda _:dyn.clone(pstr.wstring,blocksize=lambda _:s['NameLength'].li.num())), object=s._baseobject_, type=ULONG, summary=lambda _:'{:s} -> {!r}'.format(super(ptype.rpointer_t,_).summary(),_.d.l.str())), 'NameOffset'),
        (ULONG, 'NameLength'),
        (lambda s: dyn.rpointer(_API_SET_VALUE, object=s._baseobject_, type=ULONG), 'ValueOffset'),
    ]

class API_SET_MAP(pstruct.type, versioned):
    def __Entry(self):
        res = self['Header'].li
        return dyn.array(_API_SET_ENTRY, res['Count'].num(), recurse={'_baseobject_':self})

    _fields_ = [
        (_API_SET_HEADER, 'Header'),
        (__Entry, 'Entry'),
    ]

    def __init__(self, **attrs):
        super(API_SET_MAP, self).__init__(**attrs)
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) != sdkddkver.NTDDI_WIN7:
            raise error.ImplementationError(self, 'API_SET_MAP.__init__')
        return

class KSYSTEM_TIME(pstruct.type):
    _fields_ = [
        (ULONG, 'LowPart'),
        (LONG, 'High1Time'),
        (LONG, 'High2Time'),
    ]

class _WOW64_SHARED_INFORMATION(pint.enum):
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
        print hex(x['DllBase'].num()), hex(x['SizeOfImage'].num())
