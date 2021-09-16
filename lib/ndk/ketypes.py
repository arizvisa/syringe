import ptypes
from ptypes import *

from .datatypes import *

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

