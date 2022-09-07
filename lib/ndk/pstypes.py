import ptypes, pecoff
from ptypes import *

from . import error, ldrtypes, rtltypes, umtypes, ketypes, Ntddk, heaptypes, sdkddkver
from .datatypes import *

class PEB_FREE_BLOCK(pstruct.type): pass
class PPEB_FREE_BLOCK(P(PEB_FREE_BLOCK)): pass
PEB_FREE_BLOCK._fields_ = [(PPEB_FREE_BLOCK, 'Next'), (ULONG, 'Size')]

class _Win32kCallbackTable(pstruct.type, versioned):
    _fields_ = [
        (PVOID, 'fnCOPYDATA'),
        (PVOID, 'fnCOPYGLOBALDATA'),
        (PVOID, 'fnDWORD'),
        (PVOID, 'fnNCDESTROY'),
        (PVOID, 'fnDWORDOPTINLPMSG'),
        (PVOID, 'fnINOUTDRAG'),
        (PVOID, 'fnGETTEXTLENGTHS'),
        (PVOID, 'fnINCNTOUTSTRING'),
        (PVOID, 'fnPOUTLPINT'),
        (PVOID, 'fnINLPCOMPAREITEMSTRUCT'),
        (PVOID, 'fnINLPCREATESTRUCT'),
        (PVOID, 'fnINLPDELETEITEMSTRUCT'),
        (PVOID, 'fnINLPDRAWITEMSTRUCT'),
        (PVOID, 'fnPOPTINLPUINT'),
        (PVOID, 'fnPOPTINLPUINT2'),
        (PVOID, 'fnINLPMDICREATESTRUCT'),
        (PVOID, 'fnINOUTLPMEASUREITEMSTRUCT'),
        (PVOID, 'fnINLPWINDOWPOS'),
        (PVOID, 'fnINOUTLPPOINT5'),
        (PVOID, 'fnINOUTLPSCROLLINFO'),
        (PVOID, 'fnINOUTLPRECT'),
        (PVOID, 'fnINOUTNCCALCSIZE'),
        (PVOID, 'fnINOUTLPPOINT5_'),
        (PVOID, 'fnINPAINTCLIPBRD'),
        (PVOID, 'fnINSIZECLIPBRD'),
        (PVOID, 'fnINDESTROYCLIPBRD'),
        (PVOID, 'fnINSTRING'),
        (PVOID, 'fnINSTRINGNULL'),
        (PVOID, 'fnINDEVICECHANGE'),
        (PVOID, 'fnPOWERBROADCAST'),
        (PVOID, 'fnINLPUAHDRAWMENU'),
        (PVOID, 'fnOPTOUTLPDWORDOPTOUTLPDWORD'),
        (PVOID, 'fnOPTOUTLPDWORDOPTOUTLPDWORD_'),
        (PVOID, 'fnOUTDWORDINDWORD'),
        (PVOID, 'fnOUTLPRECT'),
        (PVOID, 'fnOUTSTRING'),
        (PVOID, 'fnPOPTINLPUINT3'),
        (PVOID, 'fnPOUTLPINT2'),
        (PVOID, 'fnSENTDDEMSG'),
        (PVOID, 'fnINOUTSTYLECHANGE'),
        (PVOID, 'fnHkINDWORD'),
        (PVOID, 'fnHkINLPCBTACTIVATESTRUCT'),
        (PVOID, 'fnHkINLPCBTCREATESTRUCT'),
        (PVOID, 'fnHkINLPDEBUGHOOKSTRUCT'),
        (PVOID, 'fnHkINLPMOUSEHOOKSTRUCTEX'),
        (PVOID, 'fnHkINLPKBDLLHOOKSTRUCT'),
        (PVOID, 'fnHkINLPMSLLHOOKSTRUCT'),
        (PVOID, 'fnHkINLPMSG'),
        (PVOID, 'fnHkINLPRECT'),
        (PVOID, 'fnHkOPTINLPEVENTMSG'),
        (PVOID, 'xxxClientCallDelegateThread'),
        (PVOID, 'ClientCallDummyCallback'),
        (PVOID, 'fnKEYBOARDCORRECTIONCALLOUT'),
        (PVOID, 'fnOUTLPCOMBOBOXINFO'),
        (PVOID, 'fnINLPCOMPAREITEMSTRUCT2'),
        (PVOID, 'xxxClientCallDevCallbackCapture'),
        (PVOID, 'xxxClientCallDitThread'),
        (PVOID, 'xxxClientEnableMMCSS'),
        (PVOID, 'xxxClientUpdateDpi'),
        (PVOID, 'xxxClientExpandStringW'),
        (PVOID, 'ClientCopyDDEIn1'),
        (PVOID, 'ClientCopyDDEIn2'),
        (PVOID, 'ClientCopyDDEOut1'),
        (PVOID, 'ClientCopyDDEOut2'),
        (PVOID, 'ClientCopyImage'),
        (PVOID, 'ClientEventCallback'),
        (PVOID, 'ClientFindMnemChar'),
        (PVOID, 'ClientFreeDDEHandle'),
        (PVOID, 'ClientFreeLibrary'),
        (PVOID, 'ClientGetCharsetInfo'),
        (PVOID, 'ClientGetDDEFlags'),
        (PVOID, 'ClientGetDDEHookData'),
        (PVOID, 'ClientGetListboxString'),
        (PVOID, 'ClientGetMessageMPH'),
        (PVOID, 'ClientLoadImage'),
        (PVOID, 'ClientLoadLibrary'),
        (PVOID, 'ClientLoadMenu'),
        (PVOID, 'ClientLoadLocalT1Fonts'),
        (PVOID, 'ClientPSMTextOut'),
        (PVOID, 'ClientLpkDrawTextEx'),
        (PVOID, 'ClientExtTextOutW'),
        (PVOID, 'ClientGetTextExtentPointW'),
        (PVOID, 'ClientCharToWchar'),
        (PVOID, 'ClientAddFontResourceW'),
        (PVOID, 'ClientThreadSetup'),
        (PVOID, 'ClientDeliverUserApc'),
        (PVOID, 'ClientNoMemoryPopup'),
        (PVOID, 'ClientMonitorEnumProc'),
        (PVOID, 'ClientCallWinEventProc'),
        (PVOID, 'ClientWaitMessageExMPH'),
        (PVOID, 'ClientWOWGetProcModule'),
        (PVOID, 'ClientWOWTask16SchedNotify'),
        (PVOID, 'ClientImmLoadLayout'),
        (PVOID, 'ClientImmProcessKey'),
        (PVOID, 'fnIMECONTROL'),
        (PVOID, 'fnINWPARAMDBCSCHAR'),
        (PVOID, 'fnGETTEXTLENGTHS2'),
        (PVOID, 'fnINLPKDRAWSWITCHWND'),
        (PVOID, 'ClientLoadStringW'),
        (PVOID, 'ClientLoadOLE'),
        (PVOID, 'ClientRegisterDragDrop'),
        (PVOID, 'ClientRevokeDragDrop'),
        (PVOID, 'fnINOUTMENUGETOBJECT'),
        (PVOID, 'ClientPrinterThunk'),
        (PVOID, 'fnOUTLPCOMBOBOXINFO2'),
        (PVOID, 'fnOUTLPSCROLLBARINFO'),
        (PVOID, 'fnINLPUAHDRAWMENU2'),
        (PVOID, 'fnINLPUAHDRAWMENUITEM'),
        (PVOID, 'fnINLPUAHDRAWMENU3'),
        (PVOID, 'fnINOUTLPUAHMEASUREMENUITEM'),
        (PVOID, 'fnINLPUAHDRAWMENU4'),
        (PVOID, 'fnOUTLPTITLEBARINFOEX'),
        (PVOID, 'fnTOUCH'),
        (PVOID, 'fnGESTURE'),
        (PVOID, 'fnPOPTINLPUINT4'),
        (PVOID, 'fnPOPTINLPUINT5'),
        (PVOID, 'xxxClientCallDefaultInputHandler'),
        (PVOID, 'fnEMPTY'),
        (PVOID, 'ClientRimDevCallback'),
        (PVOID, 'xxxClientCallMinTouchHitTestingCallback'),
        (PVOID, 'ClientCallLocalMouseHooks'),
        (PVOID, 'xxxClientBroadcastThemeChange'),
        (PVOID, 'xxxClientCallDevCallbackSimple'),
        (PVOID, 'xxxClientAllocWindowClassExtraBytes'),
        (PVOID, 'xxxClientFreeWindowClassExtraBytes'),
        (PVOID, 'fnGETWINDOWDATA'),
        (PVOID, 'fnINOUTSTYLECHANGE2'),
        (PVOID, 'fnHkINLPMOUSEHOOKSTRUCTEX2'),
    ]

class PEB(pstruct.type, versioned):
    '''
    0x0098    NT 3.51
    0x0150    NT 4.0
    0x01E8    Win2k
    0x020C    XP
    0x0230    WS03
    0x0238    Vista
    0x0240    Win7_BETA
    0x0248    Win6
    0x0250    Win8
    0x045C    Win10
    '''

    class BitField(pbinary.flags):
        _fields_ = [
            (1, 'ImageUsesLargePages'),
            (1, 'IsProtectedProcess'),
            (1, 'IsLegacyProcess'),
            (1, 'IsImageDynamicallyRelocated'),
            (1, 'SkipPatchingUser32Forwarders'),
            (1, 'SpareBits'),
        ]

    class CrossProcessFlags(pbinary.flags):
        _fields_ = [
            (1, 'ProcessInJob'),
            (1, 'ProcessInitializing'),
            (1, 'ProcessUsingVEH'),
            (1, 'ProcessUsingVCH'),
            (1, 'ProcessUsingFTH'),
            (27, 'ReservedBits0'),
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
            ofs = '[{:x}]'.format(self.getoffset())
            names = '|'.join((k for k, v in self.items() if v))
            return ' '.join([ofs, self.name(), names, '{!r}'.format(self.serialize())])

    class TracingFlags(pbinary.flags):
        _fields_ = [
            (1, 'HeapTracingEnabled'),
            (1, 'CritSecTracingEnabled'),
            (1, 'LibLoaderTracingEnabled'),
            (29, 'SpareTracingBits'),
        ]

    def __init__(self, **attrs):
        super(PEB, self).__init__(**attrs)
        self._fields_ = f = []
        aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

        f.extend([
            (UCHAR, 'InheritedAddressSpace'),
            (UCHAR, 'ReadImageFileExecOptions'),
            (UCHAR, 'BeingDebugged'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.append( (pbinary.littleendian(PEB.BitField), 'BitField') )
        else:
            raise error.NdkUnsupportedVersion(self)
            f.append( (BOOLEAN, 'SpareBool') )

        f.extend([
            (aligned, 'align(Mutant)'),
            (HANDLE, 'Mutant'),
            (P(pecoff.Executable.File), 'ImageBaseAddress'),
            (ldrtypes.PPEB_LDR_DATA, 'Ldr'),
            (P(rtltypes.RTL_USER_PROCESS_PARAMETERS), 'ProcessParameters'),
            (PVOID, 'SubSystemData'),
            (P(heaptypes.HEAP), 'ProcessHeap'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.extend([
                (P(rtltypes.RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (pbinary.littleendian(PEB.CrossProcessFlags), 'CrossProcessFlags'),
                (aligned, 'align(UserSharedInfoPtr)'),
                (P(_Win32kCallbackTable), 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'AtlThunkSListPtr32') if getattr(self, 'WIN64', False) else (ULONG, 'SpareUlong'),
                (P(API_SET_MAP), 'ApiSetMap'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            raise error.NdkUnsupportedVersion(self)
            f.extend([
                (P(rtltypes.RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (ULONG, 'CrossProcessFlags'),
                (P(_Win32kCallbackTable), 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'SpareUlong'),
                (PVOID, 'SparePebPtr0'),
            ])
        else:
            raise error.NdkUnsupportedVersion(self)
            f.extend([
                (P(rtltypes.RTL_CRITICAL_SECTION), 'FastPebLock'),
                (PVOID, 'FastPebLockRoutine'),
                (PVOID, 'FastPebUnlockRoutine'),
                (ULONG, 'EnvironmentUpdateCount'),
                (P(_Win32kCallbackTable), 'KernelCallbackTable'),
                (PVOID, 'EventLogSection'),
                (PVOID, 'EventLog'),
                (PPEB_FREE_BLOCK, 'FreeList'),
            ])

        f.extend([
            (ULONG, 'TlsExpansionCounter'),
            (aligned, 'align(TlsBitmap)'),
            (PVOID, 'TlsBitmap'),           # FIXME: Does TlsBitmapBits represent the number of bytes that are in use?
            (dyn.clone(BitmapBitsUlong, _object_=ULONG, length=2), 'TlsBitmapBits'),
            (PVOID, 'ReadOnlySharedMemoryBase'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.append((PVOID, 'HotpatchInformation'))
        else:
            f.append((PVOID, 'ReadOnlySharedMemoryHeap'))

        f.extend([
            (P(PVOID), 'ReadOnlyStaticServerData'),
            (PVOID, 'AnsiCodePageData'),
            (PVOID, 'OemCodePageData'),
            (PVOID, 'UnicodeCaseTableData'),
            (ULONG, 'NumberOfProcessors'),
            (pbinary.littleendian(PEB.NtGlobalFlag), 'NtGlobalFlag'),
            (dyn.align(8), 'Reserved'),
            (LARGE_INTEGER, 'CriticalSectionTimeout'),
            (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'HeapSegmentReserve'),
            (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'HeapSegmentCommit'),
            (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'HeapDeCommitTotalFreeThreshold'),
            (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'HeapDeCommitFreeBlockThreshold'),
            (ULONG, 'NumberOfHeaps'),
            (ULONG, 'MaximumNumberOfHeaps'),
            (lambda s: P(dyn.clone(heaptypes.ProcessHeapEntries, length=s['NumberOfHeaps'].li.int())), 'ProcessHeaps'),
#            (P(win32k.GDI_HANDLE_TABLE), 'GdiSharedHandleTable'),
            (PVOID, 'GdiSharedHandleTable'),
            (PVOID, 'ProcessStarterHelper'),
            (ULONG, 'GdiDCAttributeList'),
        ])

        f.extend([
            (aligned, 'align(LoaderLock)'),
            (P(rtltypes.RTL_CRITICAL_SECTION), 'LoaderLock')
        ])

        f.extend([
            (ULONG, 'OSMajorVersion'),
            (ULONG, 'OSMinorVersion'),
            (USHORT, 'OSBuildNumber'),
            (USHORT, 'OSCSDVersion'),
            (ULONG, 'OSPlatformId'),
            (ULONG, 'ImageSubSystem'),
            (ULONG, 'ImageSubSystemMajorVersion'),
            (ULONG, 'ImageSubSystemMinorVersion'),
            (aligned, 'align(ActiveProcessAffinityMask)'),
            (ULONG, 'ActiveProcessAffinityMask'),
            (aligned, 'align(GdiHandleBuffer)'),
            (dyn.array(ULONG, 0x3c if getattr(self, 'WIN64', False) else 0x22), 'GdiHandleBuffer'),
            (PVOID, 'PostProcessInitRoutine'),
            (PVOID, 'TlsExpansionBitmap'),
            (dyn.clone(BitmapBitsUlong, _object_=ULONG, length=0x20), 'TlsExpansionBitmapBits'),
            (ULONG, 'SessionId'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINBLUE:
            f.extend([
                (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'Padding5'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINXP:
            f.extend([
                (aligned, 'align(AppCompatFlags)'),
                (ULARGE_INTEGER, 'AppCompatFlags'),
                (ULARGE_INTEGER, 'AppCompatFlagsUser'),
                (PVOID, 'pShimData'),
                (PVOID, 'AppCompatInfo'),
                (umtypes.UNICODE_STRING, 'CSDVersion'),
                (PVOID, 'ActivationContextData'),  # FIXME: P(_ACTIVATION_CONTEXT_DATA)
                (PVOID, 'ProcessAssemblyStorageMap'), # FIXME: P(_ASSEMBLY_STORAGE_MAP)
                (PVOID, 'SystemDefaultActivationContextData'), # FIXME: P(_ACTIVATION_CONTEXT_DATA)
                (PVOID, 'SystemAssemblyStorageMap'),  # FIXME: P(_ASSEMBLY_STORAGE_MAP)
                (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'MinimumStackCommit'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WS03:
            f.extend([
                (PVOID, 'FlsCallback'),  # FIXME: P(_FLS_CALLBACK_INFO)
                (LIST_ENTRY, 'FlsListHead'),
                (PVOID, 'FlsBitmap'),
                (dyn.clone(BitmapBitsUlong, _object_=ULONG, length=4), 'FlsBitmapBits'),
                (ULONG, 'FlsHighIndex'),
            ])
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.extend([
                (aligned, 'align(WerRegistrationData)'),
                (PVOID, 'WerRegistrationData'),
                (PVOID, 'WerShipAssertPtr'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
            f.extend([
                (PVOID, 'pContextData'),
                (PVOID, 'pImageHeaderHash'),
                (pbinary.littleendian(PEB.TracingFlags), 'TracingFlags')
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINBLUE:
            f.extend([
                (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'Padding6'),
                (ULONGLONG, 'CsrServerReadOnlySharedMemoryBase')
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
            f.extend([
                (ULONGLONG, 'CsrServerReadOnlySharedMemoryBase')
            ])

        if self.NTDDI_VERSION >= sdkddkver.NTDDI_WIN10_TH2:
            f.extend([
                (ULONG, 'TppWorkerpListLock'),
                (LIST_ENTRY, 'TppWorkerpList'),
                (dyn.array(PVOID, 128), 'WaitOnAddressHashTable'),
            ])

        if self.NTDDI_VERSION >= sdkddkver.NTDDI_WIN10_RS3:
            f.extend([
                (PVOID, 'TelemetryCoverageHeader'),
                (ULONG, 'CloudFileFlags'),
            ])

        if self.NTDDI_VERSION >= sdkddkver.NTDDI_WIN10_RS4:
            f.extend([
                (ULONG, 'CloudFileDiagFlags'),
                (CHAR, 'PlaceHolderCompatibilityMode'),
                (dyn.block(7), 'PlaceHolderCompatibilityModeReserved'),
            ])

        # FIXME: Some fields added for windows 10 RS5
        # See https://www.geoffchappell.com/studies/windows/win32/ntdll/structs/peb/index.htm
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
            start, size = m['DllBase'].int(), m['SizeOfImage'].int()
            left, right = start, start+size
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
        (P(umtypes.PSTR), 'FrameName'),
    ]

class TEB_ACTIVE_FRAME(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (lambda s: P(TEB_ACTIVE_FRAME), 'Previous'),
        (P(TEB_ACTIVE_FRAME_CONTEXT), 'Context'),
    ]
class PTEB_ACTIVE_FRAME(P(TEB_ACTIVE_FRAME)): pass

class GDI_TEB_BATCH(pstruct.type):
    _fields_ = [
        (ULONG, 'Offset'),
        (HANDLE, 'HDC'),
        (dyn.array(ULONG, 0x136), 'Buffer'),
    ]

class TEB(pstruct.type, versioned):
    '''
    0x0F28    NT 3.51
    0x0F88    NT 4.0
    0x0FA4    Win2k
    0x0FB4    prior to XP SP2
    0x0FB8    XP SP2/WS03+
    0x0FBC    WS03 SP1+
    0x0FF8    Vista/WS08
    0x0FE4    Win7/WS08 R2
    0x0FE8    Win8-Win8.1/WS12
    0x1000    Win10
    '''

    @pbinary.littleendian
    class _SameTebFlags(pbinary.flags):
        _fields_ = [
            (1, 'SafeThunkCall'),
            (1, 'InDebugPrint'),
            (1, 'HasFiberData'),
            (1, 'SkipThreadAttach'),
            (1, 'WerInShipAssertCode'),
            (1, 'RanProcessInit'),
            (1, 'ClonedThread'),
            (1, 'SuppressDebugMsg'),
            (1, 'DisableUserStackWalk'),
            (1, 'RtlExceptionAttached'),
            (1, 'InitialThread'),
            (1, 'SessionAware'),
            (1, 'LoadOwner'),
            (1, 'LoaderWorker'),
            (2, 'SpareSameTebBits'),
        ]

    def __init__(self, **attrs):
        super(TEB, self).__init__(**attrs)
        self._fields_ = f = []
        aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

        f.extend([
            (NT_TIB, 'Tib'),
            (PVOID, 'EnvironmentPointer'),
            (umtypes.CLIENT_ID, 'ClientId'),
            (PVOID, 'ActiveRpcHandle'),
            (PVOID, 'ThreadLocalStoragePointer'),
            (P(PEB), 'ProcessEnvironmentBlock'),
            (ULONG, 'LastErrorValue'),
            (ULONG, 'CountOfOwnedCriticalSections'),
            (PVOID, 'CsrClientThread'),
            (P(Ntddk.W32THREAD), 'Win32ThreadInfo'),
            (dyn.array(ULONG, 0x1a), 'User32Reserved'),
            (dyn.array(ULONG, 5), 'UserReserved'),
            (aligned, 'align(WOW32Reserved)'),
            (PVOID, 'WOW32Reserved'),
            (LCID, 'CurrentLocale'),
            (ULONG, 'FpSoftwareStatusRegister'),
            (dyn.array(PVOID, 0x36), 'SystemReserved1'),
            (LONG, 'ExceptionCode'),
            (aligned, 'align(ActivationContextStackPointer)'),
            (P(Ntddk.ACTIVATION_CONTEXT_STACK), 'ActivationContextStackPointer'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WS03:
            f.append((dyn.block(28 if getattr(self, 'WIN64', False) else 24), 'SpareBytes1'))

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WS03:
            f.append((dyn.block(28 if getattr(self, 'WIN64', False) else 0x28), 'SpareBytes1'))

        else:
            f.append((dyn.block(24 if getattr(self, 'WIN64', False) else 0x24), 'SpareBytes1'))

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.append((ULONG, 'TxFsContext'))

        f.extend([
            (aligned, 'align(GdiTebBatch)'),
            (GDI_TEB_BATCH, 'GdiTebBatch'),
            (aligned, 'align(RealClientId)'),
            (umtypes.CLIENT_ID, 'RealClientId'),
            (PVOID, 'GdiCachedProcessHandle'),
            (ULONG, 'GdiClientPID'),
            (ULONG, 'GdiClientTID'),
            (PVOID, 'GdiThreadLocalInfo'),
            (dyn.array(PVOID, 62), 'Win32ClientInfo'),
            (dyn.array(PVOID, 0xe9), 'glDispatchTable'),
            (dyn.array(PVOID, 0x1d), 'glReserved1'),
            (PVOID, 'glReserved2'),
            (PVOID, 'glSectionInfo'),
            (PVOID, 'glSection'),
            (PVOID, 'glTable'),
            (PVOID, 'glCurrentRC'),
            (PVOID, 'glContext'),
            (aligned, 'align(LastStatusValue)'),
            (umtypes.NTSTATUS, 'LastStatusValue'),
            (aligned, 'align(StaticUnicodeString)'),
            (umtypes.UNICODE_STRING, 'StaticUnicodeString'),
            (dyn.clone(pstr.wstring, length=0x106), 'StaticUnicodeBuffer'),
            (aligned, 'align(DeallocationStack)'),
            (PVOID, 'DeallocationStack'),
            (dyn.array(PVOID, 0x40), 'TlsSlots'),
            (LIST_ENTRY, 'TlsLinks'),
            (PVOID, 'Vdm'),
            (PVOID, 'ReservedForNtRpc'),
            (dyn.array(PVOID, 0x2), 'DbgSsReserved'),
            (ULONG, 'HardErrorMode'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_VISTA:
            f.extend([
                (aligned, 'align(Instrumentation)'),
                (dyn.array(PVOID, 14 if getattr(self, 'WIN64', False) else 16), 'Instrumentation')
            ])

        else:
            f.extend([
                (aligned, 'align(Instrumentation)'),
                (dyn.array(PVOID, 11 if getattr(self, 'WIN64', False) else 9), 'Instrumentation')
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
            f.extend([
                (PVOID, 'SubProcessTag'),
                (PVOID, 'EtwTraceData'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.extend([
                (GUID, 'ActivityId'),
                (PVOID, 'SubProcessTag'),
                (PVOID, 'EtwLocalData'),
                (PVOID, 'EtwTraceData'),
            ])

        f.extend([
            (PVOID, 'WinSockData'),
            (ULONG, 'GdiBatchCount'),
        ])
        f.extend([
            (UCHAR, 'InDbgPrint'),
            (UCHAR, 'FreeStackOnTermination'),
            (UCHAR, 'HasFiberData'),
            (UCHAR, 'IdealProcessor'),
        ])
        f.extend([
            (ULONG, 'GuaranteedStackBytes'),
            (aligned, 'align(ReservedForPerf)'),
            (PVOID, 'ReservedForPerf'),
            (aligned, 'align(ReservedForOle)'),
            (PVOID, 'ReservedForOle'),
            (ULONG, 'WaitingOnLoaderLock'),
            (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(WaitingOnLoaderLock)'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
            f.extend([
                (ULONGLONG, 'SparePointer1'),
                (ULONGLONG, 'SoftPatchPtr1'),
                (ULONGLONG, 'SoftPatchPtr2'),
            ])

        else:
            f.extend([
                (aligned, 'align(SavedPriorityState)'),
                (PVOID, 'SavedPriorityState'),
                (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SoftPatchPtr1'),
                (PVOID, 'ThreadPoolData'),
            ])

        f.extend([
            (PVOID, 'TlsExpansionSlots'),
        ])

        if getattr(self, 'WIN64', False):
            f.extend([
                (PVOID, 'DeallocationBStore'),
                (PVOID, 'BStoreLimit'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN7:
            f.append((ULONG, 'ImpersonationLocale'))

        else:
            f.append((ULONG, 'MuiGeneration'))

        f.extend([
            (ULONG, 'IsImpersonating'),
            (PVOID, 'NlsCache'),
            (PVOID, 'pShimData'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WIN7:
            f.append((ULONG, 'HeapVirtualAffinity'))

        else:
            f.extend([
                (USHORT, 'HeapVirtualAffinity'),
                (USHORT, 'LowFragHeapDataSlot'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WINBLUE:
            f.extend([
                (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'Padding7'),
            ])

        f.extend([
            (aligned, 'align(CurrentTransactionHandle)'),
            (PVOID, 'CurrentTransactionHandle'),
            (PTEB_ACTIVE_FRAME, 'ActiveFrame'),
            (PVOID, 'FlsData'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
            f.extend([
                (UCHAR, 'SafeThunkCall'),
                (dyn.array(UCHAR, 3), 'BooleanSpare'),
            ])
            return

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
            f.extend([
                (PVOID, 'PreferredLangauges'),
                (PVOID, 'UserPrefLanguages'),
                (PVOID, 'MergedPrefLanguages'),
                (ULONG, 'MuiImpersonation'),
                (USHORT, 'CrossTebFlags'),
                (TEB._SameTebFlags, 'SameTebFlags'),
                (PVOID, 'TxnScopeEnterCallback'),
                (PVOID, 'TxnScopeExitCallback'),
                (PVOID, 'TxnScopeContext'),
                (ULONG, 'LockCount'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_VISTA:
            f.extend([
                (ULONG, 'ProcessRundown'),
                (ULONGLONG, 'LastSwitchTime'),
                (ULONGLONG, 'TotalSwitchOutTime'),
                (LARGE_INTEGER, 'WaitReasonBitmap'),
            ])
            return

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN10:
            f.extend([
                (ULONG, 'SpareUlong0'),
                (PVOID, 'ResourceRetValue'),
            ])

        else:
            f.extend([
                (ULONG, 'WowTebOffset'),
                (PVOID, 'ResourceRetValue'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
            f.extend([
                (PVOID, 'ReservedForWdf'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN10:
            f.extend([
                (ULONGLONG, 'ReservedForCrt'),
                (GUID, 'EffectiveContainerId'),
            ])
        return

class THREAD_INFORMATION_CLASS(pint.enum):
    _values_ = [(name, value) for value, name in [
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
        (18, 'ThreadBreakOnTermination'),
        (19, 'ThreadSwitchLegacyState'),
        (20, 'ThreadIsTerminated'),
        (21, 'ThreadLastSystemCall'),
        (22, 'ThreadIoPriority'),
        (23, 'ThreadCycleTime'),
        (24, 'ThreadPagePriority'),
        (25, 'ThreadActualBasePriority'),
        (26, 'ThreadTebInformation'),
        (27, 'ThreadCSwitchMon'),
        (28, 'ThreadCSwitchPmu'),
        (29, 'ThreadWow64Context'),
        (30, 'ThreadGroupInformation'),
        (31, 'ThreadUmsInformation'),
        (32, 'ThreadCounterProfiling'),
        (33, 'ThreadIdealProcessorEx'),
        (34, 'ThreadCpuAccountingInformation'),
        (35, 'ThreadSuspendCount'),
        (36, 'ThreadHeterogeneousCpuPolicy'),
        (37, 'ThreadContainerId'),
        (38, 'ThreadNameInformation'),
        (39, 'ThreadProperty'),
    ]]

class THREAD_BASIC_INFORMATION(pstruct.type, versioned):
    type = THREAD_INFORMATION_CLASS.byname('ThreadBasicInformation')
    def __init__(self, **attrs):
        super(THREAD_BASIC_INFORMATION, self).__init__(**attrs)
        self._fields_ = [
            (umtypes.NTSTATUS, 'ExitStatus'),
            (PVOID, 'TebBaseAddress'),
            (umtypes.CLIENT_ID, 'ClientId'),
            (umtypes.KAFFINITY, 'AffinityMask'),
            (umtypes.KPRIORITY, 'Priority'),
            (umtypes.KPRIORITY, 'BasePriority'),
        ]

class THREAD_PROPERTY_INFORMATION(pstruct.type):
    type = THREAD_INFORMATION_CLASS.byname('ThreadProperty')
    _fields_ = [
        (ULONGLONG, 'Key'),
        (PVOID, 'Object'),
        (PVOID, 'Thread'),
        (ULONG, 'Flags'),
    ]

class PROCESS_INFORMATION_CLASS(pint.enum):
    _values_ = [(name, value) for value, name in [
        (0, 'ProcessBasicInformation'),
        (1, 'ProcessQuotaLimits'),
        (2, 'ProcessIoCounters'),
        (3, 'ProcessVmCounters'),
        (4, 'ProcessTimes'),
        (5, 'ProcessBasePriority'),
        (6, 'ProcessRaisePriority'),
        (7, 'ProcessDebugPort'),
        (8, 'ProcessExceptionPort'),
        (9, 'ProcessAccessToken'),
        (10, 'ProcessLdtInformation'),
        (11, 'ProcessLdtSize'),
        (12, 'ProcessDefaultHardErrorMode'),
        (13, 'ProcessIoPortHandlers'),
        (14, 'ProcessPooledUsageAndLimits'),
        (15, 'ProcessWorkingSetWatch'),
        (16, 'ProcessUserModeIOPL'),
        (17, 'ProcessEnableAlignmentFaultFixup'),
        (18, 'ProcessPriorityClass'),
        (19, 'ProcessWx86Information'),
        (20, 'ProcessHandleCount'),
        (21, 'ProcessAffinityMask'),
        (22, 'ProcessPriorityBoost'),
        (23, 'ProcessDeviceMap'),
        (24, 'ProcessSessionInformation'),
        (25, 'ProcessForegroundInformation'),
        (26, 'ProcessWow64Information'),
        (27, 'ProcessImageFileName'),
        (28, 'ProcessLUIDDeviceMapsEnabled'),
        (29, 'ProcessBreakOnTermination'),
        (30, 'ProcessDebugObjectHandle'),
        (31, 'ProcessDebugFlags'),
        (32, 'ProcessHandleTracing'),
        (33, 'ProcessIoPriority'),
        (34, 'ProcessExecuteFlags'),
        (35, 'ProcessResourceManagement'),
        (36, 'ProcessCookie'),
        (37, 'ProcessImageInformation'),
        (38, 'ProcessCycleTime'),
        (39, 'ProcessPagePriority'),
        (40, 'ProcessInstrumentationCallback'),
        (41, 'ProcessThreadStackAllocation'),
        (42, 'ProcessWorkingSetWatchEx'),
        (43, 'ProcessImageFileNameWin32'),
        (44, 'ProcessImageFileMapping'),
        (45, 'ProcessAffinityUpdateMode'),
        (46, 'ProcessMemoryAllocationMode'),
        (47, 'ProcessGroupInformation'),
        (48, 'ProcessTokenVirtualizationEnabled'),
        (49, 'ProcessConsoleHostProcess'),
        (50, 'ProcessWindowInformation'),
        (51, 'ProcessHandleInformation'),
        (52, 'ProcessMitigationPolicy'),
        (53, 'ProcessDynamicFunctionTableInformation'),
        (54, 'ProcessHandleCheckingMode'),
        (55, 'ProcessKeepAliveCount'),
        (56, 'ProcessRevokeFileHandles'),
        (57, 'ProcessWorkingSetControl'),
        (58, 'ProcessHandleTable'),
        (59, 'ProcessCheckStackExtentsMode'),
        (60, 'ProcessCommandLineInformation'),
        (61, 'ProcessProtectionInformation'),
        (62, 'ProcessMemoryExhaustion'),
        (63, 'ProcessFaultInformation'),
        (64, 'ProcessTelemetryIdInformation'),
        (65, 'ProcessCommitReleaseInformation'),
        (66, 'ProcessDefaultCpuSetsInformation'),
        (67, 'ProcessAllowedCpuSetsInformation'),
        (68, 'ProcessSubsystemProcess'),
        (69, 'ProcessJobMemoryInformation'),
        (70, 'ProcessInPrivate'),
        (71, 'ProcessRaiseUMExceptionOnInvalidHandleClose'),
        (72, 'ProcessIumChallengeResponse'),
        (73, 'ProcessChildProcessInformation'),
        (74, 'ProcessHighGraphicsPriorityInformation'),
        (75, 'ProcessSubsystemInformation'),
        (76, 'ProcessEnergyValues'),
        (77, 'ProcessActivityThrottleState'),
        (78, 'ProcessActivityThrottlePolicy'),
        (79, 'ProcessWin32kSyscallFilterInformation'),
        (80, 'ProcessDisableSystemAllowedCpuSets'),
        (81, 'ProcessWakeInformation'),
        (82, 'ProcessEnergyTrackingState'),
        (83, 'ProcessManageWritesToExecutableMemory'),
        (84, 'ProcessCaptureTrustletLiveDump'),
        (85, 'ProcessTelemetryCoverage'),
        (86, 'ProcessEnclaveInformation'),
        (87, 'ProcessEnableReadWriteVmLogging'),
        (88, 'ProcessUptimeInformation'),
        (89, 'ProcessImageSection'),
        (90, 'ProcessDebugAuthInformation'),
        (91, 'ProcessSystemResourceManagement'),
        (92, 'ProcessSequenceNumber'),
        (93, 'ProcessLoaderDetour'),
        (94, 'ProcessSecurityDomainInformation'),
        (95, 'ProcessCombineSecurityDomainsInformation'),
        (96, 'ProcessEnableLogging'),
        (97, 'ProcessLeapSecondInformation'),
        (98, 'ProcessFiberShadowStackAllocation'),
        (99, 'ProcessFreeFiberShadowStackAllocation'),
    ]]

class PROCESS_BASIC_INFORMATION(pstruct.type, versioned):
    # XXX: there's 2 versions of this structure on server 2016
    #    32-bit -> 24, 32
    #    64-bit -> 48, 64
    _fields_ = [
        (umtypes.NTSTATUS, 'ExitStatus'),
        (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(ExitStatus)'),
        (P(PEB), 'PebBaseAddress'),
        (ULONG_PTR, 'AffinityMask'),
        (umtypes.KPRIORITY, 'BasePriority'),
        (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(BasePriority)'),
        (HANDLE, 'UniqueProcessId'),
        (HANDLE, 'InheritedFromUniqueProcessId'),
    ]

class PROCESS_MEMORY_EXHAUSTION_TYPE(pint.enum, ULONG):
    _values_ = [(n, v) for v, n in [
        (0, 'PMETypeFaultFastOnCommitFailure'),
    ]]

class PROCESS_MEMORY_EXHAUSTION_INFO(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessMemoryExhaustion')
    _fields_ = [
        (USHORT, 'Version'),
        (USHORT, 'Reserved'),
        (PROCESS_MEMORY_EXHAUSTION_TYPE, 'Value'),
        (ULONGLONG, 'Value'),
    ]

class PROCESS_FAULT_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessFaultInformation')
    _fields_ = [
        (ULONG, 'FaultFlags'),
        (ULONG, 'AdditionalInfo'),
    ]

class PROCESS_TELEMETRY_ID_INFORMATION(pstruct.type):
    type = PROCESS_INFORMATION_CLASS.byname('ProcessTelemetryIdInformation')
    _fields_ = [
        (ULONG, 'HeaderSize'),
        (ULONG, 'ProcessId'),
        (ULONGLONG, 'ProcessStartKey'),
        (ULONGLONG, 'CreateTime'),
        (ULONGLONG, 'CreateInterruptTime'),
        (ULONGLONG, 'ProcessSequenceNumber'),
        (ULONGLONG, 'SessionCreateTime'),
        (ULONG, 'SessionId'),
        (ULONG, 'BootId'),
        (ULONG, 'ImageChecksum'),
        (ULONG, 'ImageTimeDateStamp'),
        (ULONG, 'UserIdOffset'),
        (ULONG, 'ImagePathOffset'),
        (ULONG, 'PackageNameOffset'),
        (ULONG, 'RelativeAppNameOffset'),
        (ULONG, 'CommandLineOffset'),
    ]

@pbinary.littleendian
class API_SET_SCHEMA_FLAGS_(pbinary.flags):
    _fields_ = [
        (30, 'unused'),
        (1, 'HOST_EXTENSION'),
        (1, 'SEALED'),
    ]

class API_SET_HEADER(pstruct.type):
    def __init__(self, **attrs):
        super(API_SET_HEADER, self).__init__(**attrs)
        self._fields_ = f = []

        # https://www.geoffchappell.com/studies/windows/win32/apisetschema/index.htm
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
           f.extend([
                (ULONG, 'Version'),
                (ULONG, 'Count'),
            ])

        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
            f.extend([
                (ULONG, 'Version'),
                (ULONG, 'Size'),
                (API_SET_SCHEMA_FLAGS_, 'Flags'),
                (ULONG, 'Count'),
            ])

        else:
            raise error.NdkUnsupportedVersion(self)
        return

    def summary(self):
        res = []
        for fld in self:
            res.append("{:s}={:s}".format(fld, "{:#x}".format(self[fld].int()) if isinstance(self[fld], pint.type) else self[fld].summary()))
        return ' '.join(res)

class API_SET_VALUE_ENTRY(pstruct.type):
    class _Value(rpointer_t):
        _value_ = ULONG
        def summary(self):
            res = super(API_SET_VALUE_ENTRY._Value, self).summary()
            return '{:s} -> {!r}'.format(res, self.d.l.str())

        class _object_(pstr.wstring):
            def blocksize(self):
                try:
                    parent = self.getparent(API_SET_VALUE_ENTRY)
                    result = parent['Size'].li.int()
                except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
                    result = 0
                return result

    def __Value(self):
        def _object_(self, parent=self):
            parent = self.getparent(API_SET_VALUE_ENTRY)
            res = parent['Size'].li.int()
            return dyn.clone(pstr.wstring, blocksize=lambda s, sz=res: sz)

        return dyn.clone(API_SET_VALUE_ENTRY._Value, _baseobject_=self._baseobject_, _object_=_object_)

    _fields_ = [
        (lambda s: dyn.clone(s._Value, _baseobject_=s._baseobject_), 'Value'),
        (ULONG, 'Size'),
    ]

class API_SET_VALUE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (ULONG, 'EndOfEntriesOffset'),
        (ULONG, 'Hash'),
        (lambda s: API_SET_VALUE_ENTRY if s['Count'].li.int() > 1 else ptype.undefined, 'OriginalRedirect'),
        (lambda s: dyn.array(API_SET_VALUE_ENTRY, s['Count'].li.int()), 'Entry'),
    ]

class API_SET_ENTRY(pstruct.type):
    _baseobject_ = None
    class _NameOffset(rpointer_t):
        _value_ = ULONG
        def summary(self):
            res = super(API_SET_ENTRY._NameOffset, self).summary()
            return '{:s} -> {!r}'.format(res, self.d.li.str())

        class _object_(pstr.wstring):
            def blocksize(self):
                try:
                    parent = self.getparent(API_SET_ENTRY)
                    result = parent['NameLength'].li.int()
                except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
                    result = 0
                return result

    class _ValueOffset(rpointer_t):
        _value_ = ULONG
        _object_ = API_SET_VALUE

    _fields_ = [
        (lambda s: dyn.clone(s._NameOffset, _baseobject_=s._baseobject_), 'NameOffset'),
        (ULONG, 'NameLength'),
        (lambda s: dyn.clone(s._ValueOffset, _baseobject_=s._baseobject_), 'ValueOffset'),
    ]

class API_SET_MAP(pstruct.type, versioned):
    def __Entry(self):
        res = self['Header'].li
        return dyn.array(API_SET_ENTRY, res['Count'].int(), recurse={'_baseobject_':self})

    _fields_ = [
        (API_SET_HEADER, 'Header'),
        (__Entry, 'Entry'),
    ]

class KSYSTEM_TIME(pstruct.type):
    _fields_ = [
        (ULONG, 'LowPart'),
        (LONG, 'High1Time'),
        (LONG, 'High2Time'),
    ]

    def summary(self):
        return "LowPart={:#x} High1Time={:#x} High2Time={:#x}".format(self['LowPart'].int(), self['High1Time'].int(), self['High2Time'].int())

class WOW64_SHARED_INFORMATION(pint.enum):
    _values_ = [
        ('SharedNtdll32LdrInitializeThunk', 0),
        ('SharedNtdll32KiUserExceptionDispatcher', 1),
        ('SharedNtdll32KiUserApcDispatcher', 2),
        ('SharedNtdll32KiUserCallbackDispatcher', 3),
        ('SharedNtdll32LdrHotPatchRoutine', 4),
        ('SharedNtdll32ExpInterlockedPopEntrySListFault', 5),
        ('SharedNtdll32ExpInterlockedPopEntrySListResume', 6),
        ('SharedNtdll32ExpInterlockedPopEntrySListEnd', 7),
        ('SharedNtdll32RtlUserThreadStart', 8),
        ('SharedNtdll32pQueryProcessDebugInformationRemote', 9),
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
        _fields_ = [(ULONG, 'Offset'), (ULONG, 'Size')]
    _fields_ = [
        (ULONGLONG, 'EnabledFeatures'),
        (ULONG, 'Size'),
        (ULONG, 'OptimizedSave'),
        (dyn.array(FEATURE, 64), 'Features'),
    ]

class SHARED_GLOBAL_FLAGS_(pbinary.flags):
    _fields_ = [
        (21, 'SpareBits'),
        (1, 'STATE_SEPARATION_ENABLED'),    # 0x00000400
        (1, 'MULTIUSERS_IN_SESSION_SKU'),   # 0x00000200
        (1, 'MULTI_SESSION_SKU'),           # 0x00000100
        (1, 'SECURE_BOOT_ENABLED'),         # 0x00000080
        (1, 'CONSOLE_BROKER_ENABLED'),      # 0x00000040
#       (1, 'SEH_VALIDATION_ENABLED'),      # 0x00000040 (W7)
        (1, 'DYNAMIC_PROC_ENABLED'),        # 0x00000020
        (1, 'LKG_ENABLED'),                 # 0x00000010
#       (1, 'SPARE'),                       # 0x00000010 (W7)
        (1, 'INSTALLER_DETECT_ENABLED'),    # 0x00000008
        (1, 'VIRT_ENABLED'),                # 0x00000004
        (1, 'ELEVATION_ENABLED'),           # 0x00000002
        (1, 'ERROR_PORT'),                  # 0x00000001
    ]

PROCESSOR_MAX_FEATURES = 64
class PF_(parray.type):
    _object_, length = BOOLEAN, PROCESSOR_MAX_FEATURES
    _aliases_ = [
        ('FLOATING_POINT_PRECISION_ERRATA', 0),          # 4.0 and higher (x86)
        ('FLOATING_POINT_EMULATED', 1),                  # 4.0 and higher (x86)
        ('COMPARE_EXCHANGE_DOUBLE', 2),                  # 4.0 and higher
        ('MMX_INSTRUCTIONS_AVAILABLE', 3),               # 4.0 and higher
        ('PPC_MOVEMEM_64BIT_OK', 4),                     # none
        ('ALPHA_BYTE_INSTRUCTIONS', 5),                  # none
        ('XMMI_INSTRUCTIONS_AVAILABLE', 6),              # 5.0 and higher
        ('3DNOW_INSTRUCTIONS_AVAILABLE', 7),             # 5.0 and higher
        ('RDTSC_INSTRUCTION_AVAILABLE', 8),              # 5.0 and higher
        ('PAE_ENABLED', 9),                              # 5.0 and higher
        ('XMMI64_INSTRUCTIONS_AVAILABLE', 10),           # 5.1 and higher
        ('SSE_DAZ_MODE_AVAILABLE', 11),                  # none
        ('NX_ENABLED', 12),                              # late 5.1; late 5.2 and higher
        ('SSE3_INSTRUCTIONS_AVAILABLE', 13),             # 6.0 and higher
        ('COMPARE_EXCHANGE128', 14),                     # 6.0 and higher (x64)
        ('COMPARE64_EXCHANGE128', 15),                   # none
        ('CHANNELS_ENABLED', 16),                        # 6.0 only
        ('XSAVE_ENABLED', 17),                           # 6.1 and higher
        ('ARM_VFP_32_REGISTERS_AVAILABLE', 18),          # none
        ('ARM_NEON_INSTRUCTIONS_AVAILABLE', 19),         # none
        ('SECOND_LEVEL_ADDRESS_TRANSLATION', 20),        # 6.2 and higher
        ('VIRT_FIRMWARE_ENABLED', 21),                   # 6.2 and higher
        ('RDWRFSGSBASE_AVAILABLE', 22),                  # 6.2 and higher (x64)
        ('FASTFAIL_AVAILABLE', 23),                      # 6.2 and higher
        ('ARM_DIVIDE_INSTRUCTION_AVAILABLE', 24),        # none
        ('ARM_64BIT_LOADSTORE_ATOMIC', 25),              # none
        ('ARM_EXTERNAL_CACHE_AVAILABLE', 26),            # none
        ('ARM_FMAC_INSTRUCTIONS_AVAILABLE', 27),         # none
        ('RDRAND_INSTRUCTION_AVAILABLE', 28),            # 6.3 and higher
        ('ARM_V8_INSTRUCTIONS_AVAILABLE', 29),           # none
        ('ARM_V8_CRYPTO_INSTRUCTIONS_AVAILABLE', 30),    # none
        ('ARM_V8_CRC32_INSTRUCTIONS_AVAILABLE', 31),     # none
        ('RDTSCP_INSTRUCTION_AVAILABLE', 32),            # 10.0 and higher
    ]

class KUSER_SHARED_DATA(pstruct.type, versioned):
    # FIXME: https://www.geoffchappell.com/studies/windows/km/ntoskrnl/inc/api/ntexapi_x/kuser_shared_data/index.htm
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

            (0, 'DbgStateSeparationEnabled'),   # 1709
            (0, 'DbgMultiUsersInSessionSKU'),   # 1607
            (0, 'DbgMultiSessionSKU'),          # 10.0
            (0, 'DbgSecureBootEnabled'),        # 6.2

            (1, 'DbgSEHValidationEnabled'),     # 6.1
            (0, 'DbgConsoleBrokerEnabled'),     # 6.2

            (1, 'DbgDynProcessorEnabled'),      # 6.1

            (1, 'DbgSystemDllRelocated'),       # 6.0
            (0, 'DbgLkgEnabled'),               # 6.2

            (1, 'DbgInstallerDetectEnabled'),   # 6.0
            (1, 'DbgVirtEnabled'),              # 6.0
            (1, 'DbgElevationEnabled'),         # 6.0
            (1, 'DbgErrorPortPresent'),         # 6.0
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
            (dyn.clone(pstr.wstring, length=260), 'NtSystemRoot'),
            (ULONG, 'MaxStackTraceDepth'),
            (ULONG, 'CryptoExponent'),
            (ULONG, 'TimeZoneId'),
            (ULONG, 'LargePageMinimum'),
            (dyn.array(ULONG, 7), 'Reserved2'),
            (NT_PRODUCT_TYPE, 'NtProductType'),
            (BOOLEAN, 'ProductTypeIsValid'),
            (dyn.align(4), 'ProductTypeIsValidAlignment'),
            (ULONG, 'NtMajorVersion'),
            (ULONG, 'NtMinorVersion'),
            (dyn.array(BOOLEAN, PROCESSOR_MAX_FEATURES), 'ProcessorFeatures'),  # PF_
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
            f.append((dyn.array(pint.uint8_t, 4), 'Reserved12'))

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
            f.append((ULONG, 'TraceLogging'))
        elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
            f.extend([
                (self.SharedDataFlags, 'SharedDataFlags'),
                (dyn.array(ULONG, 1), 'DataFlagsPad'),
            ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) in {sdkddkver.NTDDI_WINXP, sdkddkver.NTDDI_WIN7}:
            f.extend([
                (ULONGLONG, 'TestRetInstruction'),
                (ULONG, 'SystemCall'),
                (ULONG, 'SystemCallReturn'),
                (dyn.array(ULONGLONG, 3), 'SystemCallPad'),
            ])

        f.extend([
            (KSYSTEM_TIME, 'TickCount'),
            (dyn.array(LONG, 1), 'TickCountPad'),
            (ULONG, 'Cookie'),
        ])

        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
            f.extend([
                (dyn.array(ULONG, 1), 'CookiePad'),  # pad to what, a ULONGLONG?
                (LONGLONG, 'ConsoleSessionForegroundProcessId'),
                (dyn.array(ULONG, 16), 'Wow64SharedInformation'),
                (dyn.array(USHORT, 16), 'UserModeGlobalLogger'),
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
#                (dyn.array(LONG, 1), 'XStatePad'),
#                (dyn.align(0x10), 'XStatePad'),    # ???
                (XSTATE_CONFIGURATION, 'XState'),
            ])
        return

class ETHREAD(pstruct.type, versioned):
    _fields_ = [
        (ketypes.KTHREAD, 'Tcb'),
        (LARGE_INTEGER, 'CreateTime'),
        (LIST_ENTRY, 'KeyedWaitChain'), # XXX: union
        (LONG, 'ExitStatus'),   # XXX: union
        (LIST_ENTRY, 'PostBlockList'),  # XXX: union
        (PVOID, 'KeyedWaitValue'),  # XXX: union
        (ULONG, 'ActiveTimerListLock'),
        (LIST_ENTRY, 'ActiveTimerListHead'),
        (umtypes.CLIENT_ID, 'Cid'),
        (ketypes.KSEMAPHORE, 'KeyedWaitSemaphore'), # XXX: union
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

class PROCESS_BASIC_INFORMATION(pstruct.type):
    _fields_ = [
        (NTSTATUS, 'ExitStatus'),
        (P(PEB), 'PebBaseAddress'),
        (ULONG_PTR, 'AffinityMask'),
        (umtypes.KPRIORITY, 'BasePriority'),
        (ULONG_PTR, 'UniqueProcessId'),
        (ULONG_PTR, 'InheritedFromUniqueProcessId'),
    ]

class PROCESS_EXTENDED_BASIC_INFORMATION(pstruct.type):
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        'ULONG'
        _fields_ = [
            (28, 'SpareBits'),
            (1, 'IsCrossSectionCreate'),
            (1, 'IsProcessDeleting'),
            (1, 'IsWow64Process'),
            (1, 'IsProtectedProcess'),
        ]
    _fields_ = [
        (SIZE_T, 'Size'),
        (PROCESS_BASIC_INFORMATION, 'BasicInfo'),
        (_Flags, 'Flags'),
        (ptype.undefined, 'undefined'),
    ]
    def alloc(self, **fields):
        res = super(PROCESS_EXTENDED_BASIC_INFORMATION, self).alloc(**fields)
        return res if 'Size' in fields else res.set(Size=res.size())

class COPYDATASTRUCT(pstruct.type):
    _fields_ = [
        (ULONG_PTR, 'dwData'),
        (DWORD, 'cbData'),
        (lambda self: P(dyn.block(self['cbData'].li.int())), 'lpData'),
    ]
    def alloc(self, **fields):
        res = super(COPYDATASTRUCT, self).alloc(**fields)
        if res['lpData'].d.initializedQ():
            return res if 'cbData' in fields else res.set(cbData=res['lpData'].d.size())
        return res

class STARTUPINFO(pstruct.type):
    _fields_ = [
        (DWORD, 'cb'),
        (lambda self: getattr(self, '__string__', umtypes.PSTR), 'lpReserved'),
        (lambda self: getattr(self, '__string__', umtypes.PSTR), 'lpDesktop'),
        (lambda self: getattr(self, '__string__', umtypes.PSTR), 'lpTitle'),
        (DWORD, 'dwX'),
        (DWORD, 'dwY'),
        (DWORD, 'dwXSize'),
        (DWORD, 'dwYSize'),
        (DWORD, 'dwXCountChars'),
        (DWORD, 'dwYCountChars'),
        (DWORD, 'dwFillAttribute'),
        (DWORD, 'dwFlags'),
        (WORD, 'wShowWindow'),
        (WORD, 'cbReserved2'),
        (lambda self: P(dyn.block(self['cbReserved2'].li.int())), 'lpReserved2'),
        (HANDLE, 'hStdInput'),
        (HANDLE, 'hStdOutput'),
        (HANDLE, 'hStdError'),
        (ptype.undefined, 'undefined'),
    ]
    def alloc(self, **fields):
        res = super(STARTUPINFO, self).alloc(**fields)
        return res if 'cb' in fields else res.set(cb=res.size())

class STARTUPINFOA(STARTUPINFO):
    pass
class STARTUPINFOW(STARTUPINFO):
    __string__ = umtypes.PWSTR

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

    import ptypes, pstypes

    Peb = pstypes.PEB()
    Peb.setoffset(pebaddress)
    Peb.load()

    Ldr = Peb['Ldr'].d.l
    for x in Ldr['InLoadOrderModuleList'].walk():
        print(x['BaseDllName'].str(), x['FullDllName'].str())
        print(hex(x['DllBase'].int()), hex(x['SizeOfImage'].int()))
