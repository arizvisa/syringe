import ptypes
import umtypes
from ptypes import *
from WinNT import *

# FIXME: most of these should be within a file called obtypes.py

pint.setbyteorder(ptypes.config.byteorder.littleendian)
class SID(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'Revision'),
        (pint.uint8_t, 'Count'),
        (dyn.clone(pint.uint_t, length=6, byteorder=ptypes.config.byteorder.bigendian), 'Top-authority'),
        (lambda s: dyn.array(pint.uint32_t, s['Count'].li), 'Sub-authority'),
    ]
    def summary(self):
        return 'S-{:d}-{:d}'.format(self['Revision'].int(),self['Top-authority'].int()) + ('-' if self['Count'].int() > 0 else '') + '-'.join(str(_.int()) for _ in self['Sub-authority'])
    repr = lambda s: s.summary()

class OBJECT_TYPE_CODE(pint.enum):
    _values_ = [
        ('Adapter', 0),
        ('ALPC Port', 1),
        ('Callback', 2),
        ('Controller', 3),
        ('Device', 4),
        ('Driver', 5),
        ('Event', 6),
        ('File', 7),
        ('FilterCommunicationPort', 8),
        ('IoCompletion', 9),
        ('IoCompletionReserve', 10),
        ('IRTimer', 11),
        ('KeyedEvent', 12),
        ('Mutant', 13),
        ('PcwObject', 14),
        ('PowerRequest', 15),
        ('Profile', 16),
        ('Section', 17),
        ('Semaphore', 18),
        ('SymbolicLink', 19),
        ('Timer', 20),
        ('TpWorkerFactory', 21),
        ('Type', 22),
        ('UserApcReserve', 23),
        ('WaitCompletionPacket', 24),
    ]

class OBJECT_TYPE_INITIALIZER(pstruct.type):
    class _ObjectTypeFlags(pbinary.flags):
        _fields_ = [
            (1, 'CaseInsensitive'),
            (1, 'UnnamedObjectsOnly'),
            (1, 'UseDefaultObject'),
            (1, 'SecurityRequired'),
            (1, 'MaintainHandleCount'),
            (1, 'MaintainTypeList'),
            (1, 'SupportObjectCallbacks'),
            (1, 'CacheAligned'),
        ]
    class _ObjectTypeCode(OBJECT_TYPE_CODE, ULONG): pass

    _fields_ = [
        (USHORT, 'Length'),
        (_ObjectTypeFlags, 'ObjecTypeFlags'),
        (_ObjectTypeCode, 'ObjectTypeCode'),
        (ULONG, 'InvalidAttributes'),
    ]

class POB_PRE_OPERATION_CALLBACK(PVOID): pass
class POB_POST_OPERATION_CALLBACK(PVOID): pass
class OB_OPERATION(pint.enum, ULONG):
    _values_ = [('HANDLE_CREATE',1),('HANDLE_DUPLICATE',2)]

class OBJECT_TYPE(pstruct.type): pass
class OB_OPERATION_REGISTRATION(pstruct.type): pass
class CALLBACK_ENTRY_ITEM(pstruct.type): pass
class CALLBACK_ENTRY(pstruct.type): pass

OBJECT_TYPE._fields_ = [
        (dyn.clone(LIST_ENTRY,_object_=OBJECT_TYPE), 'TypeList'),
        (umtypes.UNICODE_STRING, 'Name'),
        (PVOID, 'DefaultObject'),
        (UCHAR, 'Index'),
        (ULONG, 'TotalNumberOfObjects'),
        (ULONG, 'TotalNumberOfHandles'),
        (ULONG, 'HighWaterNumberOfObjects'),
        (ULONG, 'HighWaterNumberOfHandles'),
        (OBJECT_TYPE_INITIALIZER, 'TypeInfo'),
        (umtypes.EX_PUSH_LOCK, 'TypeLock'),
        (ULONG, 'Key'),
        (dyn.clone(LIST_ENTRY,_object_=CALLBACK_ENTRY_ITEM), 'CallbackList'),
    ]

OB_OPERATION_REGISTRATION._fields_ = [
    (P(OBJECT_TYPE), 'ObjectType'),
    (OB_OPERATION, 'Operations'),
    (POB_PRE_OPERATION_CALLBACK, 'PreOperation'),
    (POB_POST_OPERATION_CALLBACK, 'PostOperation'),
]

CALLBACK_ENTRY_ITEM._fields_ = [
        (dyn.clone(LIST_ENTRY,_object_=CALLBACK_ENTRY_ITEM), 'EntryItemList'),
        (OB_OPERATION, 'Operations'),
        (P(CALLBACK_ENTRY), 'CallbackEntry'),
        (P(OBJECT_TYPE), 'ObjectType'),
        (POB_PRE_OPERATION_CALLBACK, 'PreOperation'),
        (POB_POST_OPERATION_CALLBACK, 'PostOperation'),
        (ULONGLONG, 'unk'),
    ]

CALLBACK_ENTRY._fields_ = [
        (USHORT, 'Version'),
        (dyn.block(6), 'buffer1'),
        (P(OB_OPERATION_REGISTRATION), 'RegistrationContext'),
        (USHORT, 'AltitudeLength1'),
        (USHORT, 'AltitudeLength2'),
        (dyn.block(4), 'buffer2'),
        (P(pstr.wstring), 'AltitudeString'),
        (CALLBACK_ENTRY_ITEM, 'Items'),
    ]

## Patchguard (from https://github.com/tandasat/PgResarch/# )
class PgContextBase(pstruct.type):
    _fields_ = [
        (dyn.array(UCHAR, 192), 'CmpAppendDllSection'),
        (ULONG, 'unknown'),
        (ULONG, 'ContextSizeInQWord'),
        (ULONGLONG, 'ExAcquireResourceSharedLite'),
    ]

class PgContext_7(pstruct.type):
    _fields_ = [
        (PgContextBase, 'Base'),
        (ULONGLONG, 'ExAllocatePoolWithTag'),
        (ULONGLONG, 'ExFreePool'),
        (ULONGLONG, 'ExMapHandleToPointer'),
        (ULONGLONG, 'ExQueueWorkItem'),
        (ULONGLONG, 'ExReleaseResourceLite'),
        (ULONGLONG, 'ExUnlockHandleTableEntry'),
        (ULONGLONG, 'ExfAcquirePushLockExclusive'),
        (ULONGLONG, 'ExfReleasePushLockExclusive'),
        (ULONGLONG, 'KeAcquireInStackQueuedSpinLockAtDpcLevel'),
        (ULONGLONG, 'ExAcquireSpinLockShared'),
        (ULONGLONG, 'KeBugCheckEx'),
        (ULONGLONG, 'KeDelayExecutionThread'),
        (ULONGLONG, 'KeEnterCriticalRegionThread'),
        (ULONGLONG, 'KeLeaveCriticalRegion'),
        (ULONGLONG, 'KeEnterGuardedRegion'),
        (ULONGLONG, 'KeLeaveGuardedRegion'),
        (ULONGLONG, 'KeReleaseInStackQueuedSpinLockFromDpcLevel'),
        (ULONGLONG, 'ExReleaseSpinLockShared'),
        (ULONGLONG, 'KeRevertToUserAffinityThread'),
        (ULONGLONG, 'KeProcessorGroupAffinity'),
        (ULONGLONG, 'KeSetSystemGroupAffinityThread'),
        (ULONGLONG, 'KeSetTimer'),
        (ULONGLONG, 'LdrResFindResource'),
        (ULONGLONG, 'MmDbgCopyMemory'),
        (ULONGLONG, 'ObfDereferenceObject'),
        (ULONGLONG, 'ObReferenceObjectByName'),
        (ULONGLONG, 'RtlAssert'),
        (ULONGLONG, 'RtlImageDirectoryEntryToData'),
        (ULONGLONG, 'RtlImageNtHeader'),
        (ULONGLONG, 'RtlLookupFunctionTable'),
        (ULONGLONG, 'RtlSectionTableFromVirtualAddress'),
        (ULONGLONG, 'DbgPrint'),
        (ULONGLONG, 'DbgPrintEx'),
        (ULONGLONG, 'KiProcessListHead'),
        (ULONGLONG, 'KiProcessListLock'),
        (ULONGLONG, 'unknown1'),
        (ULONGLONG, 'PsActiveProcessHead'),
        (ULONGLONG, 'PsInvertedFunctionTable'),
        (ULONGLONG, 'PsLoadedModuleList'),
        (ULONGLONG, 'PsLoadedModuleResource'),
        (ULONGLONG, 'PsLoadedModuleSpinLock'),
        (ULONGLONG, 'PspActiveProcessLock'),
        (ULONGLONG, 'PspCidTable'),
        (ULONGLONG, 'SwapContext'),
        (ULONGLONG, 'EnlightenedSwapContext'),
        (ULONGLONG, 'unknown2'),
        (ULONGLONG, 'unknown3'),
        (ULONGLONG, 'unknown4'),
        (ULONGLONG, 'workerRoutine'),
        (ULONGLONG, 'workerQueueContext'),
        (ULONGLONG, 'unknown5'),
        (ULONGLONG, 'Prcb'),
        (ULONGLONG, 'PageBase'),
        (ULONGLONG, 'DcpRoutineToBeScheduled'),
        (ULONG, 'unknown6'),
        (ULONG, 'unknown7'),
        (ULONG, 'offsetToPg_SelfValidation'),
        (ULONG, 'offsetToRtlLookupFunctionEntryEx'),
        (ULONG, 'offsetToFsRtlUninitializeSmallMcb'),
        (ULONG, 'unknown8'),
        (ULONGLONG, 'field_298'),
        (ULONGLONG, 'field_2A0'),
        (ULONGLONG, 'field_2A8'),
        (ULONGLONG, 'field_2B0'),
        (ULONGLONG, 'field_2B8'),
        (ULONGLONG, 'field_2C0'),
        (ULONGLONG, 'field_2C8'),
        (ULONGLONG, 'field_2D0'),
        (ULONGLONG, 'field_2D8'),
        (ULONGLONG, 'field_2E0'),
        (ULONGLONG, 'field_2E8'),
        (ULONGLONG, 'field_2F0'),
        (ULONGLONG, 'field_2F8'),
        (ULONGLONG, 'field_300'),
        (ULONGLONG, 'isErroFound'),
        (ULONGLONG, 'bugChkParam1'),
        (ULONGLONG, 'bugChkParam2'),
        (ULONGLONG, 'bugChkParam4Type'),
        (ULONGLONG, 'bugChkParam3'),
        (ULONGLONG, 'field_330'),
    ]

class PgContext_8_1(pstruct.type):
    _fields_ = [
        (PgContextBase, 'Base'),
        (ULONGLONG, 'ExAcquireResourceExclusiveLite'),
        (ULONGLONG, 'ExAllocatePoolWithTag'),
        (ULONGLONG, 'ExFreePool'),
        (ULONGLONG, 'ExMapHandleToPoULONGer'),
        (ULONGLONG, 'ExQueueWorkItem'),
        (ULONGLONG, 'ExReleaseResourceLite'),
        (ULONGLONG, 'ExUnlockHandleTableEntry'),
        (ULONGLONG, 'ExfAcquirePushLockExclusive'),
        (ULONGLONG, 'ExfReleasePushLockExclusive'),
        (ULONGLONG, 'ExfAcquirePushLockShared'),
        (ULONGLONG, 'ExfReleasePushLockShared'),
        (ULONGLONG, 'KeAcquireInStackQueuedSpinLockAtDpcLevel'),
        (ULONGLONG, 'ExAcquireSpinLockSharedAtDpcLevel'),
        (ULONGLONG, 'KeBugCheckEx'),
        (ULONGLONG, 'KeDelayExecutionThread'),
        (ULONGLONG, 'KeEnterCriticalRegionThread'),
        (ULONGLONG, 'KeLeaveCriticalRegion'),
        (ULONGLONG, 'KeEnterGuardedRegion'),
        (ULONGLONG, 'KeLeaveGuardedRegion'),
        (ULONGLONG, 'KeReleaseInStackQueuedSpinLockFromDpcLevel'),
        (ULONGLONG, 'ExReleaseSpinLockSharedFromDpcLevel'),
        (ULONGLONG, 'KeRevertToUserAffinityThread'),
        (ULONGLONG, 'KeProcessorGroupAffinity'),
        (ULONGLONG, 'KeSetSystemGroupAffinityThread'),
        (ULONGLONG, 'KeSetCoalescableTimer'),
        (ULONGLONG, 'ObfDereferenceObject'),
        (ULONGLONG, 'ObReferenceObjectByName'),
        (ULONGLONG, 'RtlImageDirectoryEntryToData'),
        (ULONGLONG, 'RtlImageNtHeader'),
        (ULONGLONG, 'RtlLookupFunctionTable'),
        (ULONGLONG, 'RtlPcToFileHeader'),
        (ULONGLONG, 'RtlSectionTableFromVirtualAddress'),
        (ULONGLONG, 'DbgPrULONG'),
        (ULONGLONG, 'MmAllocateIndependentPages'),
        (ULONGLONG, 'MmFreeIndependentPages'),
        (ULONGLONG, 'MmSetPageProtection'),
        (ULONGLONG, 'unknown1'),
        (ULONGLONG, 'unknown2'),
        (ULONGLONG, 'unknown3'),
        (ULONGLONG, 'unknown4'),
        (ULONGLONG, 'RtlLookupFunctionEntry'),
        (ULONGLONG, 'KeAcquireSpinLockRaiseToDpc'),
        (ULONGLONG, 'KeReleaseSpinLock'),
        (ULONGLONG, 'MmGetSessionById'),
        (ULONGLONG, 'MmGetNextSession'),
        (ULONGLONG, 'MmQuitNextSession'),
        (ULONGLONG, 'MmAttachSession'),
        (ULONGLONG, 'MmDetachSession'),
        (ULONGLONG, 'MmGetSessionIdEx'),
        (ULONGLONG, 'MmIsSessionAddress'),
        (ULONGLONG, 'KeInsertQueueApc'),
        (ULONGLONG, 'KeWaitForSingleObject'),
        (ULONGLONG, 'PsCreateSystemThread'),
        (ULONGLONG, 'ExReferenceCallBackBlock'),
        (ULONGLONG, 'ExGetCallBackBlockRoutine'),
        (ULONGLONG, 'ExDereferenceCallBackBlock'),
        (ULONGLONG, 'KiScbQueueScanWorker'),
        (ULONGLONG, 'PspEnumerateCallback'),
        (ULONGLONG, 'CmpEnumerateCallback'),
        (ULONGLONG, 'DbgEnumerateCallback'),
        (ULONGLONG, 'ExpEnumerateCallback'),
        (ULONGLONG, 'ExpGetNextCallback'),
        (ULONGLONG, 'PopPoCoalescinCallback_'),
        (ULONGLONG, 'KiSchedulerApcTerminate'),
        (ULONGLONG, 'KiSchedulerApc'),
        (ULONGLONG, 'PopPoCoalescinCallback'),
        (ULONGLONG, 'Pg_SelfEncryptWaitAndDecrypt'),
        (ULONGLONG, 'KiWaitAlways'),
        (ULONGLONG, 'KiEntropyTimingRoutine'),
        (ULONGLONG, 'KiProcessListHead'),
        (ULONGLONG, 'KiProcessListLock'),
        (ULONGLONG, 'ObpTypeObjectType'),
        (ULONGLONG, 'IoDriverObjectType'),
        (ULONGLONG, 'PsActiveProcessHead'),
        (ULONGLONG, 'PsInvertedFunctionTable'),
        (ULONGLONG, 'PsLoadedModuleList'),
        (ULONGLONG, 'PsLoadedModuleResource'),
        (ULONGLONG, 'PsLoadedModuleSpinLock'),
        (ULONGLONG, 'PspActiveProcessLock'),
        (ULONGLONG, 'PspCidTable'),
        (ULONGLONG, 'ExpUuidLock'),
        (ULONGLONG, 'AlpcpPortListLock'),
        (ULONGLONG, 'KeServiceDescriptorTable'),
        (ULONGLONG, 'KeServiceDescriptorTableShadow'),
        (ULONGLONG, 'VfThunksExtended'),
        (ULONGLONG, 'PsWin32CallBack'),
        (ULONGLONG, 'TriageImagePageSize_0x28'),
        (ULONGLONG, 'KiTableInformation'),
        (ULONGLONG, 'HandleTableListHead'),
        (ULONGLONG, 'HandleTableListLock'),
        (ULONGLONG, 'ObpKernelHandleTable'),
        (ULONGLONG, 'HyperSpace'),
        (ULONGLONG, 'KiWaitNever'),
        (ULONGLONG, 'KxUnexpectedULONGerrupt0'),
        (ULONGLONG, 'pgContextEndFieldToBeCached'),
        (ULONGLONG, 'unknown13'),
        (ULONGLONG, 'workerQueueItem'),
        (ULONGLONG, 'ExNode0_0x198'),
        (ULONGLONG, 'workerRoutine'),
        (ULONGLONG, 'workerQueueContext'),
        (ULONGLONG, 'unknown15'),
        (ULONGLONG, 'Prcb'),
        (ULONGLONG, 'PageBase'),
        (ULONGLONG, 'secondParamOfEndOfUninitialize'),
        (ULONGLONG, 'dcpRoutineToBeScheduled'),
        (ULONG, 'numberOfChunksToBeValidated'),
        (ULONG, 'field_41C'),
        (ULONG, 'offsetToPg_SelfValidationInBytes'),
        (ULONG, 'field_424'),
        (ULONG, 'offsetToFsUninitializeSmallMcbInBytes'),
        (ULONG, 'field_42C'),
        (ULONGLONG, 'spinLock'),
        (ULONG, 'offsetToValidationInfoInBytes'),
        (ULONG, 'field_43C'),
        (ULONG, 'unknown22'),
        (ULONG, 'hashShift'),
        (ULONGLONG, 'hashSeed'),
        (ULONGLONG, 'unknown24'),
        (ULONG, 'comparedSizeForHash'),
        (ULONG, 'field_45C'),
        (ULONG, 'unknown26'),
        (ULONG, 'field_464'),
        (ULONGLONG, 'schedulerType'),
        (ULONGLONG, 'unknown28'),
        (ULONGLONG, 'unknown29'),
        (ULONGLONG, 'unknown30'),
        (ULONGLONG, 'unknown31'),
        (ULONGLONG, 'unknown32'),
        (ULONGLONG, 'unknown33'),
        (ULONGLONG, 'unknown34'),
        (ULONGLONG, 'unknown35'),
        (ULONGLONG, 'unknown36'),
        (ULONGLONG, '_guard_check_icall_fptr'),
        (ULONGLONG, 'hal_guard_check_icall_fptr'),
        (ULONGLONG, '_guard_check_icall_fptr_108'),
        (ULONGLONG, 'isErroFound'),
        (ULONGLONG, 'bugChkParam1'),
        (ULONGLONG, 'bugChkParam2'),
        (ULONGLONG, 'bugChkParam4Type'),
        (ULONGLONG, 'bugChkParam3'),
        (ULONG, 'unknown42'),
        (ULONG, 'shouldMmAllocateIndependentPagesBeUsed'),
        (ULONG, 'lockType'),
        (ULONG, 'field_504'),
        (ULONGLONG, 'pagevrf'),
        (ULONGLONG, 'pagespec'),
        (ULONGLONG, 'init'),
        (ULONGLONG, 'pagekd'),
        (ULONGLONG, 'unknown44'),
        (ULONGLONG, 'TriageImagePageSize_0x48'),
        (ULONGLONG, 'unknown45'),
        (ULONG, 'checkWin32kIfNotNegativeOne'),
        (ULONG, 'field_544'),
        (ULONGLONG, 'win32kBase'),
        (ULONGLONG, 'sessionPoULONGer'),
        (ULONG, 'onTheFlyEnDecryptionFlag'),
        (ULONG, 'dispatcherHeaderShouldBeMaked'),
        (ULONG, 'usedToDetermineErrorAsFlag'),
        (ULONG, 'field_564'),
        (ULONGLONG, 'threadForAPC'),
        (ULONGLONG, 'unknown51'),
        (ULONGLONG, 'unknown52'),
        (ULONGLONG, 'unknown53'),
        (ULONGLONG, 'unknown54'),
        (ULONGLONG, 'unknown55'),
        (ULONGLONG, 'unknown56'),
        (ULONGLONG, 'unknown57'),
        (ULONGLONG, 'unknown58'),
        (ULONGLONG, 'apc'),
        (ULONGLONG, 'KiDispatchCallout'),
        (ULONGLONG, 'EmpCheckErrataList_PopPoCoalescinCallback'),
        (ULONGLONG, 'shouldKeWaitForSingleObjectBeUsed'),
        (ULONGLONG, 'shouldKiScbQueueWorkerBeUsed'),
        (ULONGLONG, 'unknown62'),
        (ULONGLONG, 'unknown63'),
        (ULONGLONG, 'PgOriginalHash'),
        (ULONGLONG, 'unknown65'),
        (ULONGLONG, 'shouldPg_SelfEncryptWaitAndDecryptBeUsed'),
        (ULONG, 'offsetToPteRestoreInfoArrayInNumbers'),
        (ULONG, 'numberOfPteToBeRestored'),
        (ULONGLONG, 'hal_HaliHaltSystem'),
        (ULONGLONG, 'unknown68'),
        (ULONGLONG, 'KeBugCheckEx_'),
        (ULONGLONG, 'unknown69'),
        (ULONGLONG, 'KeBugCheck2'),
        (ULONGLONG, 'unknown70'),
        (ULONGLONG, 'KiBugCheckDebugBreak'),
        (ULONGLONG, 'unknown71'),
        (ULONGLONG, 'KiDebugTrapOrFault'),
        (ULONGLONG, 'unknown72'),
        (ULONGLONG, 'DbgBreakPoULONGWithStatus'),
        (ULONGLONG, 'unknown73'),
        (ULONGLONG, 'RtlCaptureContext'),
        (ULONGLONG, 'unknown74'),
        (ULONGLONG, 'KeQueryCurrentStackInformation'),
        (ULONGLONG, 'unknown75'),
        (ULONGLONG, 'KeQueryCurrentStackInformation_chunk'),
        (ULONGLONG, 'unknown76'),
        (ULONGLONG, 'KiSaveProcessorControlState'),
        (ULONGLONG, 'unknown77'),
        (ULONGLONG, 'HalPrivateDispatchTable_0x48'),
        (ULONGLONG, 'unknown78'),
        (ULONGLONG, 'unknown79'),
        (ULONGLONG, 'unknown80'),
        (ULONGLONG, 'unknown81'),
        (ULONGLONG, 'unknown82'),
        (ULONGLONG, 'unknown83'),
        (ULONGLONG, 'unknown84'),
        (ULONGLONG, 'unknown85'),
        (ULONGLONG, 'unknown86'),
        (ULONGLONG, 'unknown87'),
        (ULONGLONG, 'unknown88'),
        (ULONGLONG, 'unknown89'),
        (ULONGLONG, 'unknown90'),
        (ULONGLONG, 'unknown91'),
        (ULONGLONG, 'unknown92'),
        (ULONGLONG, 'unknown93'),
        (ULONGLONG, 'unknown94'),
        (ULONGLONG, 'unknown95'),
        (ULONGLONG, 'unknown96'),
        (ULONGLONG, 'unknown97'),
        (ULONGLONG, 'unknown98'),
        (ULONGLONG, 'unknown99'),
        (ULONGLONG, 'unknown100'),
        (ULONGLONG, 'unknown101'),
        (ULONGLONG, 'unknown102'),
        (ULONGLONG, 'unknown103'),
        (ULONGLONG, 'unknown104'),
        (ULONGLONG, 'unknown105'),
        (ULONGLONG, 'unknown106'),
        (ULONGLONG, 'unknown107'),
        (ULONGLONG, 'unknown108'),
    ]

if __name__ == '__main__':
    a = """
    01 04 00 00 00 00 00 05
    15 00 00 00 A7 40 4F 46
    FE 3C DA 76 44 37 1D 25
    """
    a = """
    01 02 00 00 00 00 00 05
    20 00 00 00 20 02 00 00
    """
    a = """
    01 01 00 00 00 00 00 01
    00 00 00 00
    """
    b = a.strip().replace('\n','').replace(' ','').decode('hex')
    c = SID(__name__='sid').load(source=prov.string(b))
    print c['Revision']
    print c['Top-authority']
    print c['Sub-authority'][0]
    print c['Sub-authority'][1]
    print c['Sub-authority'][2]
    print c['Sub-authority'][3]
    print c.summary()

"""
typedef struct _HHIVE {
    ULONG                   Signature;
    PGET_CELL_ROUTINE       GetCellRoutine;
    PALLOCATE_ROUTINE       Allocate;
    PFREE_ROUTINE           Free;
    PFILE_SET_SIZE_ROUTINE  FileSetSize;
    PFILE_WRITE_ROUTINE     FileWrite;
    PFILE_READ_ROUTINE      FileRead;
    PFILE_FLUSH_ROUTINE     FileFlush;
    struct _HBASE_BLOCK     *BaseBlock;
    RTL_BITMAP              DirtyVector;    // only for Stable bins
    ULONG                   DirtyCount;
    ULONG                   DirtyAlloc;     // allocated bytges for dirty vect
    ULONG                   Cluster;        // Usually 1 512 byte sector.  Set up force writes to be done in larger units on machines with larger sectors.  Is number of logical 512 sectors.
    BOOLEAN                 Flat;               // TRUE if FLAT
    BOOLEAN                 ReadOnly;           // TRUE if READONLY
    BOOLEAN                 Log;
    BOOLEAN                 Alternate;
    ULONG                   HiveFlags;
    ULONG                   LogSize;
    ULONG                   RefreshCount;       // debugging aid
    ULONG                   StorageTypeCount;   // 1 > Number of largest valid type. (1 for Stable only, 2 for stable & volatile)
    ULONG                   Version;            // hive version, to allow supporting multiple formats simultaneously.
    struct _DUAL {
        ULONG               Length;
        PHMAP_DIRECTORY     Map;
        PHMAP_TABLE         SmallDir;
        ULONG               Guard;          // Always == -1
        HCELL_INDEX         FreeDisplay[HHIVE_FREE_DISPLAY_SIZE];
        ULONG               FreeSummary;
        LIST_ENTRY          FreeBins;           // list of freed HBINs (FREE_HBIN)
    } Storage[ HTYPE_COUNT ];

    //
    // Caller defined data goes here
    //

} HHIVE, *PHHIVE;
"""
if __name__ == '__main__':
    pass
