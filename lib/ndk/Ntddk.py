import ptypes
from ptypes import *

from . import sdkddkver
from .dtyp import *

class KSEMAPHORE(pstruct.type):
    _fields_ = [
        (dyn.block(0x10), 'Header'),    # XXX
        (LONG, 'Limit'),
    ]

class _TL(pstruct.type):
    _fields_ = [
        (P(lambda s:_TL), 'next'),
        (PVOID,'pobj'),
        (PVOID,'pfnFree'),
    ]
class PTL(P(_TL)): pass

class W32THREAD(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(W32THREAD, self).__init__(**attrs)
        f = []

        f.extend([
            (ETHREAD, 'pEThread'),
            (ULONG, 'RefCount'),
            (PTL, 'ptlW32'),
            (PVOID, 'pgdiDcattr'),
            (PVOID, 'pgdiBrushAttr'),
            (PVOID, 'pUMPDObjs'),
            (PVOID, 'pUMPDHeap'),
            (DWORD, 'dwEngAcquireCount'),
            (PVOID, 'pSemTable'),
            (PVOID, 'pUMPDObj'),
        ])

        self._fields_ = f

class KTHREAD(dyn.block(0x200), versioned): pass

class ETHREAD(pstruct.type, versioned):
    _fields_ = [
        (KTHREAD, 'Tcb'),
        (LARGE_INTEGER, 'CreateTime'),
        (LIST_ENTRY, 'KeyedWaitChain'), # XXX: union
        (LONG, 'ExitStatus'),   # XXX: union
        (LIST_ENTRY, 'PostBlockList'),  # XXX: union
        (PVOID, 'KeyedWaitValue'),  # XXX: union
        (ULONG, 'ActiveTimerListLock'),
        (LIST_ENTRY, 'ActiveTimerListHead'),
        (CLIENT_ID, 'Cid'),
        (KSEMAPHORE, 'KeyedWaitSemaphore'), # XXX: union
#        (PS_CLIENT_SECURITY_CONTEXT, 'ClientSecurity'),
        (dyn.block(4), 'ClientSecurity'),
        (LIST_ENTRY, 'IrpList'),
        (ULONG, 'TopLevelIrp'),
#        (PDEVICE_OBJECT, 'DeviceToVerify'),
        (P(dyn.block(0xb8)), 'DeviceToVerify'),
#        (_PSP_RATE_APC *, 'RateControlApc'),
        (dyn.block(4), 'RateControlApc'),
        (PVOID, 'Win32StartAddress'),
        (PVOID, 'SparePtr0'),
        (LIST_ENTRY, 'ThreadListEntry'),
#        (EX_RUNDOWN_REF, 'RundownProtect'),
#        (EX_PUSH_LOCK, 'ThreadLock'),
        (dyn.block(4), 'RundownProtect'),
        (dyn.block(4), 'ThreadLock'),
        (ULONG, 'ReadClusterSize'),
        (LONG, 'MmLockOrdering'),
        (ULONG, 'CrossThreadFlags'),    # XXX: union
        (ULONG, 'SameThreadPassiveFlags'),  # XXX: union
        (ULONG, 'SameThreadApcFlags'),  # XXX
        (UCHAR, 'CacheManagerActive'),
        (UCHAR, 'DisablePageFaultClustering'),
        (UCHAR, 'ActiveFaultCount'),
        (ULONG, 'AlpcMessageId'),
        (PVOID, 'AlpcMessage'),  # XXX: union
        (LIST_ENTRY, 'AlpcWaitListEntry'),
        (ULONG, 'CacheManagerCount'),
    ]

class ACTIVATION_CONTEXT_STACK(pstruct.type, versioned):
    _fields_ = [
#        (PRTL_ACTIVATION_CONTEXT_STACK_FRAME, 'ActiveFrame'),
        (dyn.block(4), 'ActiveFrame'),
        (LIST_ENTRY, 'FrameListCache'),
        (ULONG, 'Flags'),
        (ULONG, 'NextCookieSequenceNumber'),
        (ULONG, 'StackId'),
    ]

# copied from https://improsec.com/tech-blog/windows-kernel-shellcode-on-windows-10-part-4-there-is-no-code
class THREADINFO(pstruct.type):
    _fields_ = [
        (W32THREAD, 'ti'),
    ]

class THROBJHEAD(pstruct.type):
    _fields_ = [
        (PVOID, 'head'),    # FIXME: _HEAD should be typed as it's not a PVOID
        (dyn.pointer(THREADINFO), 'pti'),
    ]

class THRDESKHEAD(pstruct.type):
    _fields_ = [
        (THROBJHEAD, 'head'),
        (dyn.pointer(PVOID), 'rpdesk'), # FIXME: (PDESKTOP rpdesk) DESKTOP should be typed, it's not a PVOID
        (PVOID, 'pSelf'),               # FIXME: this should be self-referential
    ]

class WND(pstruct.type):
    _fields_ = [
        (THRDESKHEAD, 'head'),
    ]
