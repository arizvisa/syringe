import ptypes
from ptypes import *

from .dtyp import *

class SYSTEM_INFORMATION_CLASS(pint.enum):
    _values_ = [(n,v) for v,n in (
        (1, 'SystemBasicInformation'), 	
        (2, 'SystemProcessorInformation'), 	
        (3, 'SystemPerformanceInformation'), 	
        (4, 'SystemTimeOfDayInformation'), 	
        (5, 'SystemPathInformation'), 	
        (6, 'SystemProcessInformation'), 	
        (7, 'SystemCallCountInformation'), 	
        (8, 'SystemDeviceInformation'), 	
        (9, 'SystemProcessorPerformanceInformation'), 	
        (10, 'SystemFlagsInformation'), 	
        (11, 'SystemCallTimeInformation'), 	
        (12, 'SystemModuleInformation'), 	
        (13, 'SystemLocksInformation'), 	
        (14, 'SystemStackTraceInformation'), 	
        (15, 'SystemPagedPoolInformation'), 	
        (16, 'SystemNonPagedPoolInformation'), 	
        (17, 'SystemHandleInformation'), 	
        (18, 'SystemObjectInformation'), 	
        (19, 'SystemPageFileInformation'), 	
        (20, 'SystemVdmInstemulInformation'), 	
        (21, 'SystemVdmBopInformation'), 	
        (22, 'SystemFileCacheInformation'), 	
        (23, 'SystemPoolTagInformation'), 	
        (24, 'SystemInterruptInformation'), 	
        (25, 'SystemDpcBehaviorInformation'), 	
        (26, 'SystemFullMemoryInformation'), 	
        (27, 'SystemLoadGdiDriverInformation'), 	
        (28, 'SystemUnloadGdiDriverInformation'), 	
        (29, 'SystemTimeAdjustmentInformation'), 	
        (30, 'SystemSummaryMemoryInformation'), 	
        (31, 'SystemMirrorMemoryInformation'), 	
        (32, 'SystemPerformanceTraceInformation'), 	
        (33, 'SystemObsolete0'), 	
        (34, 'SystemExceptionInformation'), 	
        (35, 'SystemCrashDumpStateInformation'), 	
        (36, 'SystemKernelDebuggerInformation'), 	
        (37, 'SystemContextSwitchInformation'), 	
        (38, 'SystemRegistryQuotaInformation'), 	
        (39, 'SystemExtendServiceTableInformation'), 	
        (40, 'SystemPrioritySeperation'), 	
        (41, 'SystemVerifierAddDriverInformation'), 	
        (42, 'SystemVerifierRemoveDriverInformation'), 	
        (43, 'SystemProcessorIdleInformation'), 	
        (44, 'SystemLegacyDriverInformation'), 	
        (45, 'SystemCurrentTimeZoneInformation'), 	
        (46, 'SystemLookasideInformation'), 	
        (47, 'SystemTimeSlipNotification'), 	
        (48, 'SystemSessionCreate'), 	
        (49, 'SystemSessionDetach'), 	
        (50, 'SystemSessionInformation'), 	
        (51, 'SystemRangeStartInformation'), 	
        (52, 'SystemVerifierInformation'), 	
        (53, 'SystemVerifierThunkExtend'), 	
        (54, 'SystemSessionProcessInformation'), 	
        (55, 'SystemLoadGdiDriverInSystemSpace'), 	
        (56, 'SystemNumaProcessorMap'), 	
        (57, 'SystemPrefetcherInformation'), 	
        (58, 'SystemExtendedProcessInformation'), 	
        (59, 'SystemRecommendedSharedDataAlignment'), 	
        (60, 'SystemComPlusPackage'), 	
        (61, 'SystemNumaAvailableMemory'), 	
        (62, 'SystemProcessorPowerInformation'), 	
        (63, 'SystemEmulationBasicInformation'), 	
        (64, 'SystemEmulationProcessorInformation'), 	
        (65, 'SystemExtendedHandleInformation'), 	
        (66, 'SystemLostDelayedWriteInformation'), 	
        (67, 'SystemBigPoolInformation'), 	
        (68, 'SystemSessionPoolTagInformation'), 	
        (69, 'SystemSessionMappedViewInformation'), 	
        (70, 'SystemHotpatchInformation'), 	
        (71, 'SystemObjectSecurityMode'), 	
        (72, 'SystemWatchdogTimerHandler'), 	
        (73, 'SystemWatchdogTimerInformation'), 	
        (74, 'SystemLogicalProcessorInformation'), 	
        (75, 'SystemWow64SharedInformationObsolete'), 	
        (76, 'SystemRegisterFirmwareTableInformationHandler'), 	
        (77, 'SystemFirmwareTableInformation'), 	
        (78, 'SystemModuleInformationEx'), 	
        (79, 'SystemVerifierTriageInformation'), 	
        (80, 'SystemSuperfetchInformation'), 	
        (81, 'SystemMemoryListInformation'), 	
        (82, 'SystemFileCacheInformationEx'), 	
        (83, 'SystemThreadPriorityClientIdInformation'), 	
        (84, 'SystemProcessorIdleCycleTimeInformation'), 	
        (85, 'SystemVerifierCancellationInformation'), 	
        (86, 'SystemProcessorPowerInformationEx'), 	
        (87, 'SystemRefTraceInformation'), 	
        (88, 'SystemSpecialPoolInformation'), 	
        (89, 'SystemProcessIdInformation'), 	
        (90, 'SystemErrorPortInformation'), 	
        (91, 'SystemBootEnvironmentInformation'), 	
        (92, 'SystemHypervisorInformation'), 	
        (93, 'SystemVerifierInformationEx'), 	
        (94, 'SystemTimeZoneInformation'), 	
        (95, 'SystemImageFileExecutionOptionsInformation'), 	
        (96, 'SystemCoverageInformation'), 	
        (97, 'SystemPrefetchPatchInformation'), 	
        (98, 'SystemVerifierFaultsInformation'), 	
        (99, 'SystemSystemPartitionInformation'), 	
        (101, 'SystemSystemDiskInformation'), 	
        (102, 'SystemProcessorPerformanceDistribution'), 	
        (103, 'SystemNumaProximityNodeInformation'), 	
        (104, 'SystemDynamicTimeZoneInformation'), 	
        (105, 'SystemCodeIntegrityInformation'), 	
        (106, 'SystemProcessorMicrocodeUpdateInformation'), 	
        (107, 'SystemProcessorBrandString'), 	
        (108, 'SystemVirtualAddressInformation'), 	
        (109, 'SystemLogicalProcessorAndGroupInformation'), 	
        (110, 'SystemProcessorCycleTimeInformation'), 	
        (111, 'SystemStoreInformation'), 	
        (112, 'SystemRegistryAppendString'), 	
        (113, 'SystemAitSamplingValue'), 	
        (114, 'SystemVhdBootInformation'), 	
        (115, 'SystemCpuQuotaInformation'), 	
        (116, 'SystemNativeBasicInformation'), 	
        (117, 'SystemSpare1'), 	
        (118, 'SystemLowPriorityIoInformation'), 	
        (119, 'SystemTpmBootEntropyInformation'), 	
        (120, 'SystemVerifierCountersInformation'), 	
        (121, 'SystemPagedPoolInformationEx'), 	
        (122, 'SystemSystemPtesInformationEx'), 	
        (123, 'SystemNodeDistanceInformation'), 	
        (124, 'SystemAcpiAuditInformation'), 	
        (125, 'SystemBasicPerformanceInformation'), 	
        (126, 'SystemQueryPerformanceCounterInformation'), 	
        (127, 'SystemSessionBigPoolInformation'), 	
        (128, 'SystemBootGraphicsInformation'), 	
        (129, 'SystemScrubPhysicalMemoryInformation'), 	
        (130, 'SystemBadPageInformation'), 	
        (131, 'SystemProcessorProfileControlArea'), 	
        (132, 'SystemCombinePhysicalMemoryInformation'), 	
        (133, 'SystemEntropyInterruptTimingCallback'), 	
        (134, 'SystemConsoleInformation'), 	
        (135, 'SystemPlatformBinaryInformation'), 	
        (136, 'SystemThrottleNotificationInformation'), 	
        (137, 'SystemHypervisorProcessorCountInformation'), 	
        (138, 'SystemDeviceDataInformation'), 	
        (139, 'SystemDeviceDataEnumerationInformation'), 	
        (140, 'SystemMemoryTopologyInformation'), 	
        (141, 'SystemMemoryChannelInformation'), 	
        (142, 'SystemBootLogoInformation'), 	
        (143, 'SystemProcessorPerformanceInformationEx'), 	
        (144, 'SystemSpare0'), 	
        (145, 'SystemSecureBootPolicyInformation'), 	
        (146, 'SystemPageFileInformationEx'), 	
        (147, 'SystemSecureBootInformation'), 	
        (148, 'SystemEntropyInterruptTimingRawInformation'), 	
        (149, 'SystemPortableWorkspaceEfiLauncherInformation'), 	
        (150, 'SystemFullProcessInformation'), 	
        (151, 'SystemKernelDebuggerInformationEx'), 	
        (152, 'SystemBootMetadataInformation'), 	
        (153, 'SystemSoftRebootInformation'), 	
        (154, 'SystemElamCertificateInformation'), 	
        (155, 'SystemOfflineDumpConfigInformation'), 	
        (156, 'SystemProcessorFeaturesInformation'), 	
        (157, 'SystemRegistryReconciliationInformation'), 	
        (158, 'SystemEdidInformation'), 	
        (159, 'SystemManufacturingInformation'), 	
        (160, 'SystemEnergyEstimationConfigInformation'), 	
        (161, 'SystemHypervisorDetailInformation'), 	
        (162, 'SystemProcessorCycleStatsInformation'), 	
        (163, 'SystemVmGenerationCountInformation'), 	
        (164, 'SystemTrustedPlatformModuleInformation'), 	
        (165, 'SystemKernelDebuggerFlags'), 	
        (166, 'SystemCodeIntegrityPolicyInformation'), 	
        (167, 'SystemIsolatedUserModeInformation'), 	
        (168, 'SystemHardwareSecurityTestInterfaceResultsInformation'), 	
        (169, 'SystemSingleModuleInformation'), 	
        (170, 'SystemAllowedCpuSetsInformation'), 	
        (171, 'SystemDmaProtectionInformation'), 	
        (172, 'SystemInterruptCpuSetsInformation'), 	
        (173, 'SystemSecureBootPolicyFullInformation'), 	
        (174, 'SystemCodeIntegrityPolicyFullInformation'), 	
        (175, 'SystemAffinitizedInterruptProcessorInformation'), 	
        (176, 'SystemRootSiloInformation'), 
    )]

class SYSTEM_MANUFACTURING_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemManufacturingInformation')
    _fields_ = [
        (ULONG, 'Options'),
        (UNICODE_STRING, 'ProfileName'),
    ]

class SYSTEM_ENERGY_ESTIMATION_CONFIG_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemEnergyEstimationConfigInformation')
    _fields_ = [
        (UCHAR, 'Enabled'),
    ]

class HV_DETAILS(parray.type):
    _object_, length = ULONG, 4

class SYSTEM_HYPERVISOR_DETAIL_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemHypervisorInformation')
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
    type = PROCESS_INFORMATION_CLASS.byname('SystemProcessorCycleStatsInformation')
    _fields_ = [
        (dyn.array(dyn.array(ULONGLONG, 2), 4), 'Cycles'),
    ]

class SYSTEM_KERNEL_DEBUGGER_FLAGS(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemKernelDebuggerFlags')
    _fields_ = [
        (UCHAR, 'KernelDebuggerIgnoreUmExceptions'),
    ]

class SYSTEM_CODEINTEGRITYPOLICY_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemCodeIntegrityPolicyInformation')
    _fields_ = [
        (ULONG, 'Options'),
        (ULONG, 'HVCIOptions'),
        (ULONGLONG, 'Version'),
        (_GUID, 'PolicyGuid'),
    ]

class SYSTEM_ISOLATED_USER_MODE_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemIsolatedUserModeInformation')
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
    type = PROCESS_INFORMATION_CLASS.byname('SystemSingleModuleInformation')
    _fields_ = [
        (PVOID, 'TargetModuleAddress'),
        (RTL_PROCESS_MODULE_INFORMATION, 'ExInfo'),
    ]

class SYSTEM_DMA_PROTECTION_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemDmaProtectionInformation')
    _fields_ = [
        (UCHAR, 'DmaProtectionsAvailable'),
        (UCHAR, 'DmaProtectionsInUse'),
    ]

class SYSTEM_INTERRUPT_CPU_SET_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemInterruptCpuSetsInformation')
    _fields_ = [
        (ULONG, 'Gsiv'),
        (USHORT, 'Group'),
        (ULONGLONG, 'CpuSets'), 
    ]

class SYSTEM_SECUREBOOT_POLICY_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemSecureBootPolicyInformation')
    _fields_ = [
        (_GUID, 'PolicyPublisher'),
        (ULONG, 'PolicyVersion'),
        (ULONG, 'PolicyOptions'),
    ] 

class SYSTEM_SECUREBOOT_POLICY_FULL_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemSecureBootPolicyFullInformation')
    _fields_ = [
        (SYSTEM_SECUREBOOT_POLICY_INFORMATION, 'PolicyInformation'),
        (ULONG, 'PolicySize'),
        (UCHAR, 'Policy'),
    ]

class SYSTEM_ROOT_SILO_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('SystemRootSiloInformation')
    _fields_ = [
        (ULONG, 'NumberOfSilos'),
        (PVOID, 'SiloList'),
    ]
