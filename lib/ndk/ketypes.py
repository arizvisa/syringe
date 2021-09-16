import ptypes
from ptypes import *

from .datatypes import *
from . import rtltypes

class DISPATCHER_HEADER(pstruct.type):
    _fields_ = [
        (LONG, 'Lock'),
        (LONG, 'SignalState'),
        (LIST_ENTRY, 'WaitListHead'),
    ]

class KEVENT(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
    ]

class KSEMAPHORE(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (LONG, 'Limit'),
    ]

class KGATE(KEVENT): pass

class KSPIN_LOCK(ULONG_PTR): pass

class KDPC(pstruct.type):
    _fields_ = [
        (UCHAR, 'Type'),
        (UCHAR, 'Importance'),
        (USHORT, 'Number'),
        (lambda self: dyn.clone(LIST_ENTRY, _path_=('DpcListEntry',), _object_=P(KDPC)), 'DpcListEntry'),
        (PVOID, 'DeferredRoutine'),
        (PVOID, 'DeferredContext'),
        (PVOID, 'SystemArgument1'),
        (PVOID, 'SystemArgument2'),
        (PVOID, 'DpcData'),
    ]

class KSCB(pstruct.type):
    class _Spare1(pbinary.flags):
        _fields_ = [
            (4, 'Spare1'),
            (1, 'RankBias'),
            (1, 'HardCap'),
            (1, 'OverQuota'),
            (1, 'Inserted'),
        ]
    _fields_ = [
        (ULONGLONG, 'GenerationCycles'),
        (ULONGLONG, 'UnderQuotaCycleTarget'),
        (ULONGLONG, 'RankCycleTarget'),
        (ULONGLONG, 'LongTermCycles'),
        (ULONGLONG, 'LastReportedCycles'),
        (ULONGLONG, 'OverQuotaHistory'),
        (LIST_ENTRY, 'PerProcessorList'),
        (rtltypes.RTL_BALANCED_NODE, 'QueueNode'),
        (_Spare1, 'Spare1'),
        (UCHAR, 'Spare2'),
        (USHORT, 'ReadySummary'),
        (ULONG, 'Rank'),
        (dyn.array(LIST_ENTRY, 16), 'ReadyListHead'),
    ]

class KSCHEDULING_GROUP(pstruct.type):
    _fields_ = [
        (USHORT, 'Value'),
        (UCHAR, 'Type'),
        (UCHAR, 'HardCap'),
        (ULONG, 'RelativeWeight'),
        (ULONGLONG, 'QueryHistoryTimeStamp'),
        (LONGLONG, 'NotificationCycles'),
        (lambda self: dyn.clone(LIST_ENTRY, _path_=('SchedulingGroupList',), _object_=P(KSCHEDULING_GROUP)), 'SchedulingGroupList'),
        (P(KDPC), 'NotificationDpc'),
        (P(KSCB), 'PerProcessor'),
    ]

class KTHREAD(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(KTHREAD, self).__init__(**attrs)
        self._fields_ = f = []

        f.extend([
            (DISPATCHER_HEADER, 'Header'),
            (PVOID, 'SListFaultAddress'),
            (ULONGLONG, 'QuantumTarget'),
            (PVOID, 'InitialStack'),
            (PVOID, 'StackLimit'),
            (PVOID, 'StackBase'),
            (KSPIN_LOCK, 'ThreadLock'),
            (ULONGLONG, 'CycleTime'),
            (ULONG, 'HighCycleTime'),
            (PVOID, 'ServiceTable'),
            (ULONG, 'CurrentRunTime'),
            (ULONG, 'ExpectedRunTime'),
            (PVOID, 'KernelStack'),
            (P(XSAVE_FORMAT), 'StateSaveArea'),
            #(P(KSCHEDULING_GROUP), 'SchedulingGroup'),
            (PVOID, 'SchedulingGroup'),
            (KWAIT_STATUS_REGISTER, 'WaitRegister'),
            (BOOLEAN, 'Running'),
            (dyn.array(BOOLEAN, 2), 'Alerted'),
            (ULONG, 'MiscFlags'),
            (ULONG, 'ThreadFlags'),
            (UCHAR, 'Tag'),
            (UCHAR, 'SystemHeteroCpuPolicy'),
            (UCHAR, 'UserHeteroCpuPolicy'),
            (UCHAR, 'SpecCtrl'),
            (ULONG, 'SystemCallNumber'),
            (ULONG, 'ReadyTime'),
            (PVOID, 'FirstArgument'),
            (P(KTRAP_FRAME), 'TrapFrame'),
            (KAPC_STATE, 'ApcState'),
        ])

