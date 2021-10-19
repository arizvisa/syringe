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

class KTRAP_FRAME(pstruct.type, versioned):
    class _Last(pstruct.type):
        _fields_ = [
            (ULONG64, 'DebugControl'),
            (ULONG64, 'LastBranchToRip'),
            (ULONG64, 'LastBranchFromRip'),
            (ULONG64, 'LastExceptionToRip'),
            (ULONG64, 'LastExceptionFromRip'),
        ]

    def __init__(self, **attrs):
        super(KTRAP_FRAME, self).__init__(**attrs)
        self._fields_ = []

        f32 = [
            (ULONG, 'DbgEbp'),
            (ULONG, 'DbgEip'),
            (ULONG, 'DbgArgMark'),
            (ULONG, 'DbgArgPointer'),
            (USHORT, 'TempSegCs'),
            (UCHAR, 'Logging'),
            (UCHAR, 'FrameType'),
            (ULONG, 'TempEsp'),
            (ULONG, 'Dr0'),
            (ULONG, 'Dr1'),
            (ULONG, 'Dr2'),
            (ULONG, 'Dr3'),
            (ULONG, 'Dr6'),
            (ULONG, 'Dr7'),
            (ULONG, 'SegGs'),
            (ULONG, 'SegEs'),
            (ULONG, 'SegDs'),
            (ULONG, 'Edx'),
            (ULONG, 'Ecx'),
            (ULONG, 'Eax'),
            (ULONG, 'MxCsr'),
            #(P(EXCEPTION_REGISTRATION_RECORD), 'ExceptionList'),
            (PVOID, 'ExceptionList'),
            (ULONG, 'SegFs'),
            (ULONG, 'Edi'),
            (ULONG, 'Esi'),
            (ULONG, 'Ebx'),
            (ULONG, 'Ebp'),
            (ULONG, 'ErrCode'),
            (ULONG, 'Eip'),
            (ULONG, 'SegCs'),
            (ULONG, 'EFlags'),
            (ULONG, 'HardwareEsp'),
            (ULONG, 'HardwareSegSs'),
            (ULONG, 'V86Es'),
            (ULONG, 'V86Ds'),
            (ULONG, 'V86Fs'),
            (ULONG, 'V86Gs'),
        ]

        f64 = [
            (ULONG64, 'P1Home'),
            (ULONG64, 'P2Home'),
            (ULONG64, 'P3Home'),
            (ULONG64, 'P4Home'),
            (ULONG64, 'P5'),
            (KPROCESSOR_MODE, 'PreviousMode'),
            (KIRQL, 'PreviousIrql'),
            (UCHAR, 'FaultIndicator'),
            (UCHAR, 'ExceptionActive'),
            (ULONG, 'MxCsr'),
            (ULONG64, 'Rax'),
            (ULONG64, 'Rcx'),
            (ULONG64, 'Rdx'),
            (ULONG64, 'R8'),
            (ULONG64, 'R9'),
            (ULONG64, 'R10'),
            (ULONG64, 'R11'),
            (ULONG64, 'GsBase'),
            (M128A, 'Xmm0'),
            (M128A, 'Xmm1'),
            (M128A, 'Xmm2'),
            (M128A, 'Xmm3'),
            (M128A, 'Xmm4'),
            (M128A, 'Xmm5'),
            (ULONG64, 'ContextRecord'),
            (ULONG64, 'Dr0'),
            (ULONG64, 'Dr1'),
            (ULONG64, 'Dr2'),
            (ULONG64, 'Dr3'),
            (ULONG64, 'Dr6'),
            (ULONG64, 'Dr7'),
            (KTRAP_FRAME._Last, 'Last'),
            (USHORT, 'SegDs'),
            (USHORT, 'SegEs'),
            (USHORT, 'SegFs'),
            (USHORT, 'SegGs'),
            (ULONG64, 'TrapFrame'),
            (ULONG64, 'Rbx'),
            (ULONG64, 'Rdi'),
            (ULONG64, 'Rsi'),
            (ULONG64, 'Rbp'),
            (ULONG64, 'ExceptionFrame'),
            (ULONG64, 'Rip'),
            (USHORT, 'SegCs'),
            (dyn.array(USHORT, 3), 'Fill1'),
            (ULONG, 'EFlags'),
            (ULONG, 'Fill2'),
            (ULONG64, 'Rsp'),
            (USHORT, 'SegSs'),
            (USHORT, 'Fill3'),
            (ULONG, 'Fill4'),
        ]

        self._fields_ = f64 if getattr(self, 'WIN64', False) else f32

class FAST_MUTEX(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(FAST_MUTEX, self).__init__(**attrs)
        alignment = 8 if getattr(self, 'WIN64', False) else 4
        padding = 4 if getattr(self, 'WIN64', False) else 0
        self._fields_ = [
            (LONG, 'Count'),
            (dyn.align(alignment), 'align(Owner)'),
            (PVOID, 'Owner'),
            (ULONG, 'Contention'),
            (dyn.block(padding), 'padding(Contention)'),
            (ketypes.KEVENT, 'Event'),
            (ULONG, 'OldIrql'),
            (dyn.block(padding), 'padding(OldIrql)'),
        ]

class EPROCESS(pstruct.type, versioned):
    class _MitigationFlags(pbinary.flags):
        _fields_ = [
            (2, 'Unused'),
            (1, 'EnableModuleTamperingProtectionNoInherit'),
            (1, 'EnableModuleTamperingProtection'),
            (1, 'AuditLoaderIntegrityContinuity'),
            (1, 'LoaderIntegrityContinuityEnabled'),
            (1, 'AuditBlockNonMicrosoftBinariesAllowStore'),
            (1, 'AuditBlockNonMicrosoftBinaries'),
            (1, 'SignatureMitigationOptIn'),
            (1, 'AuditProhibitLowILImageMap'),
            (1, 'ProhibitLowILImageMap'),
            (1, 'AuditProhibitRemoteImageMap'),
            (1, 'ProhibitRemoteImageMap'),
            (1, 'PreferSystem32Images'),
            (1, 'AuditNonSystemFontLoading'),
            (1, 'DisableNonSystemFonts'),
            (1, 'AuditFilteredWin32kAPIs'),
            (1, 'EnableFilteredWin32kAPIs'),
            (1, 'AuditDisallowWin32kSystemCalls'),
            (1, 'DisallowWin32kSystemCalls'),
            (1, 'AuditDisableDynamicCode'),
            (1, 'DisableDynamicCodeAllowRemoteDowngrade'),
            (1, 'DisableDynamicCodeAllowOptOut'),
            (1, 'DisableDynamicCode'),
            (1, 'ExtensionPointDisable'),
            (1, 'StackRandomizationDisabled'),
            (1, 'HighEntropyASLREnabled'),
            (1, 'ForceRelocateImages'),
            (1, 'DisallowStrippedImages'),
            (1, 'ControlFlowGuardStrict'),
            (1, 'ControlFlowGuardExportSuppressionEnabled'),
            (1, 'ControlFlowGuardEnabled'),
        ]
    class _MitigationFlags2(pbinary.flags):
        _fields_ = [
            (20, 'Unused'),
            (1, 'AuditImportAddressFilter'),
            (1, 'EnableImportAddressFilter'),
            (1, 'AuditRopSimExec'),
            (1, 'EnableRopSimExec'),
            (1, 'AuditRopCallerCheck'),
            (1, 'EnableRopCallerCheck'),
            (1, 'AuditRopStackPivot'),
            (1, 'EnableRopStackPivot'),
            (1, 'AuditExportAddressFilterPlus'),
            (1, 'EnableExportAddressFilterPlus'),
            (1, 'AuditExportAddressFilter'),
            (1, 'EnableExportAddressFilter'),
        ]
    def __init__(self, **attrs):
        super(EPROCESS, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (ketypes.KPROCESS, 'Pcb'),
        ])

class ETHREAD(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(ETHREAD, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (ketypes.KTHREAD, 'Pcb'),
            (LARGE_INTEGER, 'CreateTime'),
        ])

class MDL_(pbinary.flags):
    '''WORD'''
    _fields_ = [
        (1, 'INTERNAL'),
        (1, 'PAGE_CONTENTS_INVARIANT'),
        (1, 'MAPPING_CAN_FAIL'),
        (1, 'NETWORK_HEADER'),
        (1, 'IO_SPACE'),
        (1, 'DESCRIBES_AWE'),
        (1, 'FREE_EXTRA_PTES'),
        (1, 'LOCKED_PAGE_TABLES'),
        (1, 'WRITE_OPERATION'),
        (1, 'IO_PAGE_READ'),
        (1, 'PARTIAL_HAS_BEEN_MAPPED'),
        (1, 'PARTIAL'),
        (1, 'ALLOCATED_FIXED_SIZE'),
        (1, 'SOURCE_IS_NONPAGED_POOL'),
        (1, 'PAGES_LOCKED'),
        (1, 'MAPPED_TO_SYSTEM_VA'),
    ]

class MDL(pstruct.type, versioned):
    @pbinary.littleendian
    class _MdlFlags(MDL_):
        '''WORD'''
    def __init__(self, **attrs):
        super(MDL, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (P(MDL), 'Next'),
            (WORD, 'Size'),
            (self._MdlFlags, 'MdlFlags'),
        ])
        if getattr(self, 'WIN64', False):
            F.extend([
                (WORD, 'AllocationProcessorNumber'),
                (WORD, 'Reserved'),
            ])

        F.extend([
            (P(EPROCESS), 'Process'),
            (PVOID, 'MappedSystemVa'),
            (PVOID, 'StartVa'),
            (ULONG, 'ByteCount'),
            (ULONG, 'ByteOffset'),
        ])

class SYSTEM_MODULE_ENTRY(pstruct.type):
    _fields_ = [
        (HANDLE, 'Section'),
        (PVOID, 'MappedBase'),
        (PVOID, 'ImageBase'),
        (ULONG, 'ImageSize'),
        (ULONG, 'Flags'),
        (USHORT, 'LoadOrderIndex'),
        (USHORT, 'InitOrderIndex'),
        (USHORT, 'LoadCount'),
        (USHORT, 'OffsetToFileName'),
        #(dyn.array(UCHAR, 256), 'FullPathName'),
        (dyn.clone(pstr.string, length=256), 'FullPathName'),
    ]

class SYSTEM_MODULE_INFORMATION(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (lambda self: dyn.array(SYSTEM_MODULE_ENTRY, self['Count'].li.int()), 'Module'),
    ]

class KLDR_DATA_TABLE_ENTRY(pstruct.type):
    def __InLoadOrderLinks(self):
        return dyn.clone(LIST_ENTRY, _object_=KLDR_DATA_TABLE_ENTRY)
    class PNON_PAGED_DEBUG_INFO(PVOID): pass
    _fields_ = [
        (__InLoadOrderLinks, 'InLoadOrderLinks'),
        (PVOID, 'ExceptionTable'),
        (ULONG, 'ExceptionTableSize'),
        (PVOID, 'GpValue'),
        (PNON_PAGED_DEBUG_INFO, 'NonPagedDebugInfo'),
        (PVOID, 'DllBase'),
        (PVOID, 'EntryPoint'),
        (ULONG, 'SizeOfImage'),
        (umtypes.UNICODE_STRING, 'FullDllName'),
        (umtypes.UNICODE_STRING, 'BaseDllName'),
        (ULONG, 'Flags'),
        (USHORT, 'LoadCount'),
        (USHORT, '__Unused5'),
        (PVOID, 'SectionPointer'),
        (ULONG, 'CheckSum'),
        (PVOID, 'LoadedImports'),
        (PVOID, 'PatchInformation'),
    ]
