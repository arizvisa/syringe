import ptypes
from ptypes import *

from . import umtypes, rtltypes, ketypes, mmtypes
from .datatypes import *

class SYSTEM_INFORMATION_CLASS(pint.enum):
    _values_ = [(n, v) for v, n in (
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
    )]

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
    _fields_ = [
        (PVOID, 'TargetModuleAddress'),
        (rtltypes.RTL_PROCESS_MODULE_INFORMATION, 'ExInfo'),
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

class ERESOURCE_THREAD(ULONG_PTR): pass

class OWNER_ENTRY(pstruct.type, versioned):
    _fields_ = [
        (ERESOURCE_THREAD, 'OwnerThread'),
        (ULONG, 'TableSize')
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
        (lambda self: dyn.align(8 if getattr(self, 'WIN64', False) else 4), 'align(Reserved2)'),   # FIXME: this might not be right
        (lambda self: PVOID if getattr(self, 'WIN64', False) else pint.uint_t, 'Reserved2'),
        (PVOID, 'Address'),
        (KSPIN_LOCK, 'SpinLock'),
        (lambda self: dyn.padding(8 if getattr(self, 'WIN64', False) else 4), 'padding(SpinLock)'),   # FIXME: this might not be right
    ]

class GENERAL_LOOKASIDE(pstruct.type):
    _fields_ = [
        (dyn.clone(SLIST_HEADER, _object_=mmtypes.POOL_FREE_CHUNK, _path_=('ListEntry',)), 'ListHead'),
        (UINT16, 'Depth'),
        (UINT16, 'MaximumDepth'),
        (ULONG, 'TotalAllocates'),
        (ULONG, 'AllocateMissesOrHits'),
        (ULONG, 'TotalFrees'),
        (ULONG, 'FreeMissesOrHits'),
        (POOL_TYPE, 'Type'),
        (dyn.clone(pstr.string, length=4), 'Tag'),
        (ULONG, 'Size'),
        (PVOID, 'Allocate'),
        (PVOID, 'Free'),
        (LIST_ENTRY, 'ListEntry'),
        (ULONG, 'LastTotalAllocates'),
        (ULONG, 'LastAllocateMissesOrHits'),
        (dyn.array(ULONG, 2), 'Future'),
    ]
