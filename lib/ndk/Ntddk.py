import ptypes
from ptypes import *

from . import sdkddkver, ketypes, umtypes
from .datatypes import *

class TL(pstruct.type):
    _fields_ = [
        (P(lambda self: TL), 'next'),
        (PVOID, 'pobj'),
        (PVOID, 'pfnFree'),
    ]
class PTL(P(TL)): pass

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

class MMPTE_HARDWARE(pbinary.flags, versioned):
    def __init__(self, **attrs):
        res = super(MMPTE_HARDWARE, self).__init__(**attrs)
        major, minor = sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), sdkddkver.NTDDI_MINOR(self.NTDDI_VERSION)

        self._fields_ = f = [
            (1, 'Valid'),
            (1, 'Writable'),
            (1, 'Owner'),
            (1, 'WriteThrough'),
            (1, 'CacheDisable'),
            (1, 'Accessed'),
            (1, 'Dirty'),
            (1, 'LargePage'),
            (1, 'Global'),
            (1, 'CopyOnWrite'),
            (1, 'Prototype'),
            (1, 'Write'),
        ]

        if not getattr(self, 'WIN64', False):
            f.append((20, 'PageFrameNumber'),)

        elif getattr(self, 'PAE', False):
            raise NotImplementedError('PAE not implemented')

            # 5.2 - 6.0
            if False:
                f.extend([
                    (28, 'PageFrameNumber'),
                    (12, 'Reserved1'),
                    (11, 'SoftwareWsIndex'),
                    (1, 'NoExecute'),
                ])

            # FIXME: 6.0 to 1607
            if False:
                f.extend([
                    (36, 'PageFrameNumber'),
                    (4, 'ReservedForHardware'),
                    (11, 'SoftwareWsIndex'),
                    (1, 'NoExecute'),
                ])

            # FIXME: 1703 and higher
            if False:
                f.extend([
                    (36, 'PageFrameNumber'),
                    (4, 'ReservedForHardware'),
                    (4, 'ReservedForSoftware'),
                    (4, 'WsleAge'),
                    (3, 'WsleProtection'),
                    (1, 'NoExecute'),
                ])

        # 5.0
        elif major == 0x05000000:
            f.append([
                (24, 'PageFrameNumber'),
                (28, 'Reserved1'),
            ])

        # 5.1
        elif major >= 0x05010000:
            f.append([
                (26, 'PageFrameNumber'),
                (25, 'Reserved1'),
                (1, 'NoExecute'),
            ])
        return
