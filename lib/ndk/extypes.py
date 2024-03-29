import ptypes
from ptypes import *

from . import umtypes, ketypes, mmtypes
from .datatypes import *

class SYSTEM_INFORMATION_CLASS(pint.enum):
    _values_ = [(n, v) for v, n in [
        (0, 'SystemBasicInformation'),
        (1, 'SystemProcessorInformation'),
        (2, 'SystemPerformanceInformation'),
        (3, 'SystemTimeOfDayInformation'),
        (4, 'SystemPathInformation'),
        (5, 'SystemProcessInformation'),
        (6, 'SystemCallCountInformation'),
        (7, 'SystemDeviceInformation'),
        (8, 'SystemProcessorPerformanceInformation'),
        (9, 'SystemFlagsInformation'),
        (10, 'SystemCallTimeInformation'),
        (11, 'SystemModuleInformation'),
        (12, 'SystemLocksInformation'),
        (13, 'SystemStackTraceInformation'),
        (14, 'SystemPagedPoolInformation'),
        (15, 'SystemNonPagedPoolInformation'),
        (16, 'SystemHandleInformation'),
        (17, 'SystemObjectInformation'),
        (18, 'SystemPageFileInformation'),
        (19, 'SystemVdmInstemulInformation'),
        (20, 'SystemVdmBopInformation'),
        (21, 'SystemFileCacheInformation'),
        (22, 'SystemPoolTagInformation'),
        (23, 'SystemInterruptInformation'),
        (24, 'SystemDpcBehaviorInformation'),
        (25, 'SystemFullMemoryInformation'),
        (26, 'SystemLoadGdiDriverInformation'),
        (27, 'SystemUnloadGdiDriverInformation'),
        (28, 'SystemTimeAdjustmentInformation'),
        (29, 'SystemSummaryMemoryInformation'),
        (30, 'SystemMirrorMemoryInformation'),
        (31, 'SystemPerformanceTraceInformation'),
        (32, 'SystemObsolete0'),
        (33, 'SystemExceptionInformation'),
        (34, 'SystemCrashDumpStateInformation'),
        (35, 'SystemKernelDebuggerInformation'),
        (36, 'SystemContextSwitchInformation'),
        (37, 'SystemRegistryQuotaInformation'),
        (38, 'SystemExtendServiceTableInformation'),
        (39, 'SystemPrioritySeperation'),
        (40, 'SystemVerifierAddDriverInformation'),
        (41, 'SystemVerifierRemoveDriverInformation'),
        (42, 'SystemProcessorIdleInformation'),
        (43, 'SystemLegacyDriverInformation'),
        (44, 'SystemCurrentTimeZoneInformation'),
        (45, 'SystemLookasideInformation'),
        (46, 'SystemTimeSlipNotification'),
        (47, 'SystemSessionCreate'),
        (48, 'SystemSessionDetach'),
        (49, 'SystemSessionInformation'),
        (50, 'SystemRangeStartInformation'),
        (51, 'SystemVerifierInformation'),
        (52, 'SystemVerifierThunkExtend'),
        (53, 'SystemSessionProcessInformation'),
        (54, 'SystemLoadGdiDriverInSystemSpace'),
        (55, 'SystemNumaProcessorMap'),
        (56, 'SystemPrefetcherInformation'),
        (57, 'SystemExtendedProcessInformation'),
        (58, 'SystemRecommendedSharedDataAlignment'),
        (59, 'SystemComPlusPackage'),
        (60, 'SystemNumaAvailableMemory'),
        (61, 'SystemProcessorPowerInformation'),
        (62, 'SystemEmulationBasicInformation'),
        (63, 'SystemEmulationProcessorInformation'),
        (64, 'SystemExtendedHandleInformation'),
        (65, 'SystemLostDelayedWriteInformation'),
        (66, 'SystemBigPoolInformation'),
        (67, 'SystemSessionPoolTagInformation'),
        (68, 'SystemSessionMappedViewInformation'),
        (69, 'SystemHotpatchInformation'),
        (70, 'SystemObjectSecurityMode'),
        (71, 'SystemWatchdogTimerHandler'),
        (72, 'SystemWatchdogTimerInformation'),
        (73, 'SystemLogicalProcessorInformation'),
        (74, 'SystemWow64SharedInformationObsolete'),
        (75, 'SystemRegisterFirmwareTableInformationHandler'),
        (76, 'SystemFirmwareTableInformation'),
        (77, 'SystemModuleInformationEx'),
        (78, 'SystemVerifierTriageInformation'),
        (79, 'SystemSuperfetchInformation'),
        (80, 'SystemMemoryListInformation'),
        (81, 'SystemFileCacheInformationEx'),
        (82, 'SystemThreadPriorityClientIdInformation'),
        (83, 'SystemProcessorIdleCycleTimeInformation'),
        (84, 'SystemVerifierCancellationInformation'),
        (85, 'SystemProcessorPowerInformationEx'),
        (86, 'SystemRefTraceInformation'),
        (87, 'SystemSpecialPoolInformation'),
        (88, 'SystemProcessIdInformation'),
        (89, 'SystemErrorPortInformation'),
        (90, 'SystemBootEnvironmentInformation'),
        (91, 'SystemHypervisorInformation'),
        (92, 'SystemVerifierInformationEx'),
        (93, 'SystemTimeZoneInformation'),
        (94, 'SystemImageFileExecutionOptionsInformation'),
        (95, 'SystemCoverageInformation'),
        (96, 'SystemPrefetchPatchInformation'),
        (97, 'SystemVerifierFaultsInformation'),
        (98, 'SystemSystemPartitionInformation'),
        (99, 'SystemSystemDiskInformation'),
        (100, 'SystemProcessorPerformanceDistribution'),
        (101, 'SystemNumaProximityNodeInformation'),
        (102, 'SystemDynamicTimeZoneInformation'),
        (103, 'SystemCodeIntegrityInformation'),
        (104, 'SystemProcessorMicrocodeUpdateInformation'),
        (105, 'SystemProcessorBrandString'),
        (106, 'SystemVirtualAddressInformation'),
        (107, 'SystemLogicalProcessorAndGroupInformation'),
        (108, 'SystemProcessorCycleTimeInformation'),
        (109, 'SystemStoreInformation'),
        (110, 'SystemRegistryAppendString'),
        (111, 'SystemAitSamplingValue'),
        (112, 'SystemVhdBootInformation'),
        (113, 'SystemCpuQuotaInformation'),
        (114, 'SystemNativeBasicInformation'),
        (115, 'SystemErrorPortTimeouts'),
        (116, 'SystemLowPriorityIoInformation'),
        (117, 'SystemTpmBootEntropyInformation'),
        (118, 'SystemVerifierCountersInformation'),
        (119, 'SystemPagedPoolInformationEx'),
        (120, 'SystemSystemPtesInformationEx'),
        (121, 'SystemNodeDistanceInformation'),
        (122, 'SystemAcpiAuditInformation'),
        (123, 'SystemBasicPerformanceInformation'),
        (124, 'SystemQueryPerformanceCounterInformation'),
        (125, 'SystemSessionBigPoolInformation'),
        (126, 'SystemBootGraphicsInformation'),
        (127, 'SystemScrubPhysicalMemoryInformation'),
        (128, 'SystemBadPageInformation'),
        (129, 'SystemProcessorProfileControlArea'),
        (130, 'SystemCombinePhysicalMemoryInformation'),
        (131, 'SystemEntropyInterruptTimingCallback'),
        (132, 'SystemConsoleInformation'),
        (133, 'SystemPlatformBinaryInformation'),
        (134, 'SystemThrottleNotificationInformation'),
        (135, 'SystemHypervisorProcessorCountInformation'),
        (136, 'SystemDeviceDataInformation'),
        (137, 'SystemDeviceDataEnumerationInformation'),
        (138, 'SystemMemoryTopologyInformation'),
        (139, 'SystemMemoryChannelInformation'),
        (140, 'SystemBootLogoInformation'),
        (141, 'SystemProcessorPerformanceInformationEx'),
        (142, 'SystemCriticalProcessErrorLogInformation'),
        (143, 'SystemSecureBootPolicyInformation'),
        (144, 'SystemPageFileInformationEx'),
        (145, 'SystemSecureBootInformation'),
        (146, 'SystemEntropyInterruptTimingRawInformation'),
        (147, 'SystemPortableWorkspaceEfiLauncherInformation'),
        (148, 'SystemFullProcessInformation'),
        (149, 'SystemKernelDebuggerInformationEx'),
        (150, 'SystemBootMetadataInformation'),
        (151, 'SystemSoftRebootInformation'),
        (152, 'SystemElamCertificateInformation'),
        (153, 'SystemOfflineDumpConfigInformation'),
        (154, 'SystemProcessorFeaturesInformation'),
        (155, 'SystemRegistryReconciliationInformation'),
        (156, 'SystemEdidInformation'),
        (157, 'SystemManufacturingInformation'),
        (158, 'SystemEnergyEstimationConfigInformation'),
        (159, 'SystemHypervisorDetailInformation'),
        (160, 'SystemProcessorCycleStatsInformation'),
        (161, 'SystemVmGenerationCountInformation'),
        (162, 'SystemTrustedPlatformModuleInformation'),
        (163, 'SystemKernelDebuggerFlags'),
        (164, 'SystemCodeIntegrityPolicyInformation'),
        (165, 'SystemIsolatedUserModeInformation'),
        (166, 'SystemHardwareSecurityTestInterfaceResultsInformation'),
        (167, 'SystemSingleModuleInformation'),
        (168, 'SystemAllowedCpuSetsInformation'),
        (169, 'SystemDmaProtectionInformation'),
        (170, 'SystemInterruptCpuSetsInformation'),
        (171, 'SystemSecureBootPolicyFullInformation'),
        (172, 'SystemCodeIntegrityPolicyFullInformation'),
        (173, 'SystemAffinitizedInterruptProcessorInformation'),
        (174, 'SystemRootSiloInformation'),
        (175, 'SystemCpuSetInformation'),
        (176, 'SystemCpuSetTagInformation'),
        (177, 'SystemWin32WerStartCallout'),
        (178, 'SystemSecureKernelProfileInformation'),
        (179, 'SystemCodeIntegrityPlatformManifestInformation'),
        (180, 'SystemInterruptSteeringInformation'),
        (181, 'SystemSuppportedProcessorArchitectures'),
        (182, 'SystemMemoryUsageInformation'),
        (183, 'SystemCodeIntegrityCertificateInformation'),
        (184, 'SystemPhysicalMemoryInformation'),
        (185, 'SystemControlFlowTransition'),
        (186, 'SystemKernelDebuggingAllowed'),
        (187, 'SystemActivityModerationExeState'),
        (188, 'SystemActivityModerationUserSettings'),
        (189, 'SystemCodeIntegrityPoliciesFullInformation'),
        (190, 'SystemCodeIntegrityUnlockInformation'),
        (191, 'SystemIntegrityQuotaInformation'),
        (192, 'SystemFlushInformation'),
        (193, 'SystemProcessorIdleMaskInformation'),
        (194, 'SystemSecureDumpEncryptionInformation'),
        (195, 'SystemWriteConstraintInformation'),
        (196, 'SystemKernelVaShadowInformation'),
        (197, 'SystemHypervisorSharedPageInformation'),
        (198, 'SystemFirmwareBootPerformanceInformation'),
        (199, 'SystemCodeIntegrityVerificationInformation'),
        (200, 'SystemFirmwarePartitionInformation'),
        (201, 'SystemSpeculationControlInformation'),
        (202, 'SystemDmaGuardPolicyInformation'),
        (203, 'SystemEnclaveLaunchControlInformation'),
        (204, 'SystemWorkloadAllowedCpuSetsInformation'),
        (205, 'SystemCodeIntegrityUnlockModeInformation'),
        (206, 'SystemLeapSecondInformation'),
        (207, 'SystemFlags2Information'),
        (208, 'SystemSecurityModelInformation'),
        (209, 'SystemCodeIntegritySyntheticCacheInformation'),
    ]]

class PROCESSOR_ARCHITECTURE_(pint.enum):
    _values_ = [
        ('AMD64', 9),
        ('ARM', 5),
        ('ARM64', 12),
        ('IA64', 6),
        ('INTEL', 0),
        ('UNKNOWN', 0xffff),
    ]

class PROCESSOR_(pint.enum):
    _values_ = [
        ('SHx_SH3', 103),
        ('SHx_SH4', 104),
        ('INTEL_386', 386),
        ('INTEL_486', 486),
        ('INTEL_PENTIUM', 586),
        ('PPC_601', 601),
        ('PPC_603', 603),
        ('PPC_604', 604),
        ('PPC_620', 620),
        ('MOTOROLA_821', 821),
        ('ARM720', 1824),
        ('ARM820', 2080),
        ('ARM920', 2336),
        ('STRONGARM', 2577),
        ('INTEL_IA64', 2200),
        ('MIPS_R4000', 4000),
        ('AMD_X8664', 8664),
        ('HITACHI_SH3', 10003),
        ('HITACHI_SH3E', 10004),
        ('HITACHI_SH4', 10005),
        ('OPTIL', 18767),
        ('ALPHA_21064', 21064),
        ('ARM_7TDMI', 70001),
    ]

class SYSTEM_INFO(pstruct.type, versioned):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemBasicInformation')
    class _wProcessorArchitecture(PROCESSOR_ARCHITECTURE_, WORD):
        pass
    class _dwProcessorType(PROCESSOR_, DWORD):
        pass
    def __return64(type32, type64):
        def win32orwin64(self):
            res = self['wProcessorArchitecture'].li
            return type64 if res.int() else type32
        return win32orwin64
    _fields_ = [
        (_wProcessorArchitecture, 'wProcessorArchitecture'),
        (WORD, 'wReserved'),
        (DWORD, 'dwPageSize'),
        (__return64(PVOID, dyn.clone(PVOID, WIN64=1)), 'lpMinimumApplicationAddress'),
        (__return64(PVOID, dyn.clone(PVOID, WIN64=1)), 'lpMaximumApplicationAddress'),
        (__return64(DWORD_PTR, dyn.clone(DWORD_PTR, WIN64=1)), 'dwActiveProcessorMask'),
        (DWORD, 'dwNumberOfProcessors'),
        (_dwProcessorType, 'dwProcessorType'),
        (DWORD, 'dwAllocationGranularity'),
        (WORD, 'wProcessorLevel'),
        (WORD, 'wProcessorRevision'),
    ]

class SYSTEM_MANUFACTURING_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemManufacturingInformation')
    _fields_ = [
        (ULONG, 'Options'),
        (umtypes.UNICODE_STRING, 'ProfileName'),
    ]

class SYSTEM_ENERGY_ESTIMATION_CONFIG_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemEnergyEstimationConfigInformation')
    _fields_ = [
        (UCHAR, 'Enabled'),
    ]

class HV_DETAILS(parray.type):
    _object_, length = ULONG, 4

class SYSTEM_HYPERVISOR_DETAIL_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemHypervisorInformation')
    _fields_ = [
        (HV_DETAILS, 'HvVendorAndMaxFunction'),
        (HV_DETAILS, 'HypervisorInterface'),
        (HV_DETAILS, 'HypervisorVersion'),
        (HV_DETAILS, 'HvFeatures'),
        (HV_DETAILS, 'HvFeatures'),
        (HV_DETAILS, 'EnlightenmentInfo'),
        (HV_DETAILS, 'ImplementationLimits'),
    ]

class SYSTEM_PROCESSOR_CYCLE_STATS_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemProcessorCycleStatsInformation')
    _fields_ = [
        (dyn.array(dyn.array(ULONGLONG, 2), 4), 'Cycles'),
    ]

class SYSTEM_KERNEL_DEBUGGER_FLAGS(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemKernelDebuggerFlags')
    _fields_ = [
        (UCHAR, 'KernelDebuggerIgnoreUmExceptions'),
    ]

class SYSTEM_CODEINTEGRITYPOLICY_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemCodeIntegrityPolicyInformation')
    _fields_ = [
        (ULONG, 'Options'),
        (ULONG, 'HVCIOptions'),
        (ULONGLONG, 'Version'),
        (GUID, 'PolicyGuid'),
    ]

class SYSTEM_ISOLATED_USER_MODE_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemIsolatedUserModeInformation')
    _fields_ = [
        (UCHAR, 'SecureKernelRunning'),
        (UCHAR, 'HvciEnabled'),
        (UCHAR, 'HvciStrictMode'),
        (UCHAR, 'DebugEnabled'),
        (UCHAR, 'SpareFlags'),
        (UCHAR, 'TrustletRunning'),
        (UCHAR, 'SpareFlags2'),
        (dyn.array(UCHAR, 6), 'Spare0'),
        (ULONGLONG, 'Spare'),
    ]

class SYSTEM_SINGLE_MODULE_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemSingleModuleInformation')
    def __ExInfo(self):
        import rtltypes
        return rtltypes.RTL_PROCESS_MODULE_INFORMATION

    _fields_ = [
        (PVOID, 'TargetModuleAddress'),
        (__ExInfo, 'ExInfo'),
    ]

class SYSTEM_DMA_PROTECTION_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemDmaProtectionInformation')
    _fields_ = [
        (UCHAR, 'DmaProtectionsAvailable'),
        (UCHAR, 'DmaProtectionsInUse'),
    ]

class SYSTEM_INTERRUPT_CPU_SET_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemInterruptCpuSetsInformation')
    _fields_ = [
        (ULONG, 'Gsiv'),
        (USHORT, 'Group'),
        (ULONGLONG, 'CpuSets'),
    ]

class SYSTEM_SECUREBOOT_POLICY_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemSecureBootPolicyInformation')
    _fields_ = [
        (GUID, 'PolicyPublisher'),
        (ULONG, 'PolicyVersion'),
        (ULONG, 'PolicyOptions'),
    ]

class SYSTEM_SECUREBOOT_POLICY_FULL_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemSecureBootPolicyFullInformation')
    _fields_ = [
        (SYSTEM_SECUREBOOT_POLICY_INFORMATION, 'PolicyInformation'),
        (ULONG, 'PolicySize'),
        (UCHAR, 'Policy'),
    ]

class SYSTEM_ROOT_SILO_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemRootSiloInformation')
    _fields_ = [
        (ULONG, 'NumberOfSilos'),
        (PVOID, 'SiloList'),
    ]

class SUPERFETCH_INFORMATION_CLASS(pint.enum):
    _values_ = [(n, v) for v, n in [
        (0x1, 'SuperfetchRetrieveTrace'),
        (0x2, 'SuperfetchSystemParameters'),
        (0x3, 'SuperfetchLogEvent'),
        (0x4, 'SuperfetchGenerateTrace'),
        (0x5, 'SuperfetchPrefetch'),
        (0x6, 'SuperfetchPfnQuery'),
        (0x7, 'SuperfetchPfnSetPriority'),
        (0x8, 'SuperfetchPrivSourceQuery'),
        (0x9, 'SuperfetchSequenceNumberQuery'),
        (0xA, 'SuperfetchScenarioPhase'),
        (0xB, 'SuperfetchWorkerPriority'),
        (0xC, 'SuperfetchScenarioQuery'),
        (0xD, 'SuperfetchScenarioPrefetch'),
        (0xE, 'SuperfetchRobustnessControl'),
        (0xF, 'SuperfetchTimeControl'),
        (0x10, 'SuperfetchMemoryListQuery'),
        (0x11, 'SuperfetchMemoryRangesQuery'),
        (0x12, 'SuperfetchTracingControl'),
        (0x13, 'SuperfetchTrimWhileAgingControl'),
        (0x14, 'SuperfetchInformationMax'),
    ]]

class SUPERFETCH_INFORMATION(pstruct.type):
    type = SYSTEM_INFORMATION_CLASS.byname('SystemSuperfetchInformation')
    class _InfoClass(SUPERFETCH_INFORMATION_CLASS, ULONG):
        pass
    _fields_ = [
        (ULONG, 'Version'),
        (ULONG, 'Magic'),
        (_InfoClass, 'InfoClass'),
        (PVOID, 'Data'),
        (ULONG, 'Length'),
    ]

class PFS_PRIVATE_PAGE_SOURCE_TYPE(pint.enum):
    _values_ = [(n, v) for v, n in [
        (0x0, 'PfsPrivateSourceKernel'),
        (0x1, 'PfsPrivateSourceSession'),
        (0x2, 'PfsPrivateSourceProcess'),
        (0x3, 'PrfsPrivateSourceMax'),
    ]]


class PFS_PRIVATE_PAGE_SOURCE(pstruct.type):
    class _SourceId(dynamic.union):
        _fields_ = [
            (DWORD, 'SessionId'),
            (DWORD, 'ProcessId'),
        ]
    _fields_ = [
        (PFS_PRIVATE_PAGE_SOURCE_TYPE, 'Type'),
        (_SourceId, 'SourceId'),
        (dyn.array(DWORD, 2), 'SpareDwords'),
        (ULONG, 'ImagePathHash'),
        (ULONG, 'UniqueProcessHash'),
    ]

class PF_PRIVSOURCE_INFO_V3(pstruct.type):
    class _Owner(dynamic.union):
        _fields_ = [
            (ULONG_PTR, 'EProcess'),
            (ULONG_PTR, 'GlobalVA'),
        ]
    _fields_ = [
        (PFS_PRIVATE_PAGE_SOURCE, 'DbInfo'),
	    (_Owner, 'Owner'),
        (ULONG, 'WsPrivatePages'),
        (ULONG, 'TotalPrivatePages'),
        (ULONG, 'SessionID'),
        (dyn.array(CHAR, 16), 'ImageName'),
        (dyn.array(BYTE, 12), 'SpareBytes'),
    ]

class PF_PRIVSOURCE_INFO_V3PLUS(pstruct.type):
    _fields_ = [
        (dyn.array(BYTE, 8), 'data2'),
        (DWORD, 'ProcessId'),
        (dyn.array(BYTE, 16), 'data3'),
        (ULONG_PTR, 'EProcess'),
        (dyn.array(BYTE, 60), 'data'),
    ]

class PF_PRIVSOURCE_QUERY_REQUEST(pstruct.type):
    class _sv3(pstruct.type):
        _fields_ = [
            (ULONG, 'InfoCount'),
            (lambda self: dyn.array(PF_PRIVSOURCE_INFO_V3, self['InfoCount'].li.int()), 'InfoArrayV3'),
        ]
    class _sv3plus(pstruct.type):
        _fields_ = [
            (ULONG, 'Type'),
            (ULONG, 'InfoCount'),
            (lambda self: dyn.array(PF_PRIVSOURCE_INFO_V3PLUS, self['InfoCount'].li.int()), 'InfoArrayV3Plus'),
        ]
    def __Info(self):
        version = self['Version'].li.int()
        if version == 3:
            return PF_PRIVSOURCE_QUERY_REQUEST._sv3
        elif version > 3:
            return PF_PRIVSOURCE_QUERY_REQUEST._sv3plus
        raise NotImplementedError(version)
    _fields_ = [
        (ULONG, 'Version'),
        (__Info, 'Info'),
        (dyn.align(4), 'alignment(Info)'),
    ]

class SYSTEM_POOLTAG(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'Tag'),
        (ULONG, 'PagedAllocs'),
        (ULONG, 'PagedFrees'),
        (SIZE_T, 'PagedUsed'),
        (ULONG, 'NonPagedAllocs'),
        (ULONG, 'NonPagedFrees'),
        (SIZE_T, 'NonPagedUsed'),
    ]

class SYSTEM_POOLTAG_INFORMATION(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (lambda self: dyn.array(SYSTEM_POOLTAG, self['Count'].li.int()), 'TagInfo'),
    ]

class ERESOURCE_THREAD(ULONG_PTR): pass

class OWNER_ENTRY(pstruct.type, versioned):
    _fields_ = [
        (ERESOURCE_THREAD, 'OwnerThread'),
        (ULONG, 'TableSize'),
        (lambda self: dyn.padding(8 if getattr(self, 'WIN64', False) else 4), 'padding(TableSize)'),
    ]

class ERESOURCE(pstruct.type, versioned):
    _fields_ = [
        (LIST_ENTRY, 'SystemResourcesList'),
        (P(OWNER_ENTRY), 'OwnerTable'),
        (SHORT, 'ActiveCount'),
        (USHORT, 'Flag'),
        (lambda self: dyn.align(8 if getattr(self, 'WIN64', False) else 4), 'align(SharedWaiters)'),   # FIXME: this might not be right
        (P(ketypes.KSEMAPHORE), 'SharedWaiters'),
        (P(ketypes.KEVENT), 'ExclusiveWatiers'),
        (OWNER_ENTRY, 'OwnerEntry'),
        (ULONG, 'ActiveEntries'),
        (ULONG, 'ContentionCount'),
        (ULONG, 'NumberOfSharedWaiters'),
        (ULONG, 'NumberOfExclusiveWaiters'),
        (lambda self: PVOID if getattr(self, 'WIN64', False) else pint.uint_t, 'Reserved2'),
        (PVOID, 'Address'),
        (ketypes.KSPIN_LOCK, 'SpinLock'),
    ]

class POOL_HEADER(pstruct.type, versioned):
    class _Ulong(pbinary.struct):
        def summary(self):
            res = []
            res.append("Type={:s}({:d})".format(self.field('PoolType').str(), self.field('PoolType').int()))
            res.append("Index={:d}".format(self['PoolIndex']))
            res.append("PreviousSize={:#x}".format(self['PreviousSize']))
            res.append("BlockSize={:#x}".format(self['BlockSize']))
            return ' '.join(res)

    class _Ulong1_PagedPool(_Ulong):
        class _PagedPoolType(mmtypes._POOL_TYPE_PagedPool):
            length = 7
        _fields_ = [
            (_PagedPoolType, 'PoolType'),
            (9, 'BlockSize'),
            (7, 'PoolIndex'),
            (9, 'PreviousSize'),
        ]

    class _Ulong1_NonPagedPool(_Ulong):
        class _NonPagedPoolType(mmtypes._POOL_TYPE_NonPagedPool):
            length = 7
        _fields_ = [
            (_NonPagedPoolType, 'PoolType'),
            (9, 'BlockSize'),
            (7, 'PoolIndex'),
            (9, 'PreviousSize'),
        ]

    class _Ulong164_PagedPool(_Ulong):
        class _PagedPoolType(mmtypes._POOL_TYPE_PagedPool):
            length = 8
        _fields_ = [
            (_PagedPoolType, 'PoolType'),
            (8, 'BlockSize'),
            (8, 'PoolIndex'),
            (8, 'PreviousSize'),
        ]

    class _Ulong164_NonPagedPool(_Ulong):
        class _NonPagedPoolType(mmtypes._POOL_TYPE_NonPagedPool):
            length = 8
        _fields_ = [
            (_NonPagedPoolType, 'PoolType'),
            (8, 'BlockSize'),
            (8, 'PoolIndex'),
            (8, 'PreviousSize'),
        ]

    def __Ulong1(self):
        nonpaged_attribute = self.NONPAGED if hasattr(self, 'NONPAGED') else not self.PAGED if hasattr(self, 'PAGED') else False
        if nonpaged_attribute:
            pooltype32, pooltype64 = (POOL_HEADER._Ulong1_NonPagedPool, POOL_HEADER._Ulong164_NonPagedPool)
        else:
            pooltype32, pooltype64 = (POOL_HEADER._Ulong1_PagedPool, POOL_HEADER._Ulong164_PagedPool)
        res = pooltype64 if getattr(self, 'WIN64', False) else pooltype
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
    _object_ = fpointer(POOL_FREE_CHUNK, 'ListEntry')
    _path_ = ['ListEntry']

POOL_FREE_CHUNK._fields_ = [
    (POOL_HEADER, 'Header'),
    (POOL_FREE_CHUNK_LIST_ENTRY, 'ListEntry'),
]

class GENERAL_LOOKASIDE(pstruct.type):
    @pbinary.littleendian
    class _PagedPoolType(mmtypes._POOL_TYPE_PagedPool):
        length = 32

    @pbinary.littleendian
    class _NonPagedPoolType(mmtypes._POOL_TYPE_NonPagedPool):
        length = 32

    def __PoolType(self):
        nonpaged_attribute = self.NONPAGED if hasattr(self, 'NONPAGED') else not self.PAGED if hasattr(self, 'PAGED') else False
        return GENERAL_LOOKASIDE._NonPagedPoolType if nonpaged_Attribute else GENERAL_LOOKASIDE._PagedPoolType

    _fields_ = [
        (dyn.clone(SLIST_HEADER, _object_=POOL_FREE_CHUNK, _path_=['ListEntry']), 'ListHead'),
        (UINT16, 'Depth'),
        (UINT16, 'MaximumDepth'),
        (ULONG, 'TotalAllocates'),
        (ULONG, 'AllocateMissesOrHits'),
        (ULONG, 'TotalFrees'),
        (ULONG, 'FreeMissesOrHits'),
        (__PoolType, 'Type'),
        (dyn.clone(pstr.string, length=4), 'Tag'),
        (ULONG, 'Size'),
        (PVOID, 'Allocate'),
        (PVOID, 'Free'),
        (LIST_ENTRY, 'ListEntry'),
        (ULONG, 'LastTotalAllocates'),
        (ULONG, 'LastAllocateMissesOrHits'),
        (dyn.array(ULONG, 2), 'Future'),
    ]

class PP_LOOKASIDE_LIST(pstruct.type):
    _fields_ = [
        (P(GENERAL_LOOKASIDE), 'P'),
        (P(GENERAL_LOOKASIDE), 'L'),
    ]

class POOL_DESCRIPTOR(pstruct.type, versioned):
    @pbinary.littleendian
    class _PagedPoolType(mmtypes._POOL_TYPE_PagedPool):
        length = 32

    @pbinary.littleendian
    class _NonPagedPoolType(mmtypes._POOL_TYPE_NonPagedPool):
        length = 32

    def __PoolType(self):
        nonpaged_attribute = self.NONPAGED if hasattr(self, 'NONPAGED') else not self.PAGED if hasattr(self, 'PAGED') else False
        return POOL_DESCRIPTOR._NonPagedPoolType if nonpaged_Attribute else POOL_DESCRIPTOR._PagedPoolType

    def __ListHeads(self):
        POOL_PAGE_SIZE = pow(2, 12)
        POOL_BLOCK_SIZE = 16 if getattr(self, 'WIN64', False) else 8
        POOL_LISTS_PER_PAGE = POOL_PAGE_SIZE // POOL_BLOCK_SIZE
        return dyn.array(POOL_FREE_CHUNK_LIST_ENTRY, POOL_LISTS_PER_PAGE)

    _fields_ = [
        (__PoolType, 'PoolType'),
        (ULONG, 'PoolIndex'),
        (ULONG, 'RunningAllocs'),
        (ULONG, 'RunningDeAllocs'),
        (ULONG, 'TotalPages'),
        (ULONG, 'TotalBigPages'),
        (ULONG, 'Threshold'),
        (PVOID, 'LockAddress'),
        (PVOID, 'PendingFrees'),
        (LONG, 'ThreadsProcessingDeferrals'),
        (LONG, 'PendingFreeDepth'),
        (ULONG, 'TotalBytes'),
        (ULONG, 'Spare0'),
        (__ListHeads, 'ListHeads'),
    ]

class POOL_TRACKER_TABLE(pstruct.type):
    _fields_ = [
        (ULONG, 'Key'),
        (ULONG, 'NonPagedAllocs'),
        (ULONG, 'NonPagedFrees'),
        (SIZE_T, 'NonPagedBytes'),
        (ULONG, 'PagedAllocs'),
        (ULONG, 'PagedFrees'),
        (SIZE_T, 'PagedBytes'),
    ]

class POOL_TRACKER_BIG_PAGES(pstruct.type):
    _fields_ = [
        (PVOID, 'Va'),
        (ULONG, 'Key'),
        (ULONG, 'NumberOfPages'),
        (ULONG, 'QuotaObject'),
    ]
