import ptypes, pecoff
from ptypes import *

from . import error, ldrtypes, rtltypes, umtypes, mmtypes, ketypes, Ntddk, heaptypes, sdkddkver
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
                (1, 'FLG_STOP_ON_EXCEPTION'),           # 0x00000001
                (1, 'FLG_SHOW_LDR_SNAPS'),              # 0x00000002
                (1, 'FLG_DEBUG_INITIAL_COMMAND'),       # 0x00000004
                (1, 'FLG_STOP_ON_HUNG_GUI'),            # 0x00000008
                (1, 'FLG_HEAP_ENABLE_TAIL_CHECK'),      # 0x00000010
                (1, 'FLG_HEAP_ENABLE_FREE_CHECK'),      # 0x00000020
                (1, 'FLG_HEAP_VALIDATE_PARAMETERS'),    # 0x00000040
                (1, 'FLG_HEAP_VALIDATE_ALL'),           # 0x00000080
                (1, 'FLG_POOL_ENABLE_TAIL_CHECK'),      # 0x00000100
                (1, 'FLG_POOL_ENABLE_FREE_CHECK'),      # 0x00000200
                (1, 'FLG_POOL_ENABLE_TAGGING'),         # 0x00000400
                (1, 'FLG_HEAP_ENABLE_TAGGING'),         # 0x00000800
                (1, 'FLG_USER_STACK_TRACE_DB'),         # 0x00001000
                (1, 'FLG_KERNEL_STACK_TRACE_DB'),       # 0x00002000
                (1, 'FLG_MAINTAIN_OBJECT_TYPELIST'),    # 0x00004000
                (1, 'FLG_HEAP_ENABLE_TAG_BY_DLL'),      # 0x00008000
                (1, 'FLG_IGNORE_DEBUG_PRIV'),           # 0x00010000
                (1, 'FLG_ENABLE_CSRDEBUG'),             # 0x00020000
                (1, 'FLG_ENABLE_KDEBUG_SYMBOL_LOAD'),   # 0x00040000
                (1, 'FLG_DISABLE_PAGE_KERNEL_STACKS'),  # 0x00080000
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WINXP:
                f.append((1, 'FLG_HEAP_ENABLE_CALL_TRACING'))   # 0x00100000
            else:
                f.append((1, 'FLG_ENABLE_SYSTEM_CRIT_BREAKS'))  # 0x00100000

            f.extend([
                (1, 'FLG_HEAP_DISABLE_COALESCING'),     # 0x00200000
                (1, 'FLG_ENABLE_CLOSE_EXCEPTIONS'),     # 0x00400000
                (1, 'FLG_ENABLE_EXCEPTION_LOGGING'),    # 0x00800000
                (1, 'FLG_ENABLE_HANDLE_TYPE_TAGGING'),  # 0x01000000
                (1, 'FLG_HEAP_PAGE_ALLOCS'),            # 0x02000000
                (1, 'FLG_DEBUG_INITIAL_COMMAND_EX'),    # 0x04000000
                (1, 'FLG_DISABLE_DBGPRINT'),            # 0x08000000
                (1, 'FLG_CRITSEC_EVENT_CREATION'),      # 0x10000000
                (1, 'FLG_STOP_ON_UNHANDLED_EXCEPTION'), # 0x20000000
                (1, 'FLG_ENABLE_HANDLE_EXCEPTIONS'),    # 0x40000000
                (1, 'FLG_DISABLE_PROTDLLS'),            # 0x80000000
            ])
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

class THREADINFOCLASS(pint.enum):
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
    type = THREADINFOCLASS.byname('ThreadBasicInformation')
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
    type = THREADINFOCLASS.byname('ThreadProperty')
    _fields_ = [
        (ULONGLONG, 'Key'),
        (PVOID, 'Object'),
        (PVOID, 'Thread'),
        (ULONG, 'Flags'),
    ]

class PROCESS_INFORMATION_CLASS(pint.enum):
    _values_ = [(name, value) for value, name in [
        (0, 'ProcessMemoryPriority'),
        (1, 'ProcessMemoryExhaustionInfo'),
        (2, 'ProcessAppMemoryInfo'),
        (3, 'ProcessInPrivateInfo'),
        (4, 'ProcessPowerThrottling'),
        (5, 'ProcessReservedValue1'),
        (6, 'ProcessTelemetryCoverageInfo'),
        (7, 'ProcessProtectionLevelInfo'),
        (8, 'ProcessLeapSecondInfo'),
        (9, 'ProcessMachineTypeInfo'),
    ]]

class ProcessInformationClass(ptype.definition):
    cache = {}
    __key__ = staticmethod(lambda object: PROCESS_INFORMATION_CLASS.byname(object.type, object.type))
    __get__ = classmethod(lambda cls, key, *args, **kwargs: super(ProcessInformationClass, cls).__get__(key if isinstance(key, tuple(integer.__class__ for integer in [sys.maxsize, sys.maxsize + 1])) else PROCESS_INFORMATION_CLASS.byname(key), *args, **kwargs))
    __set__ = classmethod(lambda cls, key, object, **kwargs: setattr(object, cls.attribute, key) or super(ProcessInformationClass, cls).__set__(key, object, **kwargs))

class MEMORY_PRIORITY_(pint.enum):
    _values_ = [
        ('VERY_LOW', 1),
        ('LOW', 2),
        ('MEDIUM', 3),
        ('BELOW_NORMAL', 4),
        ('NORMAL', 5),
    ]

@ProcessInformationClass.define
class MEMORY_PRIORITY_INFORMATION(pstruct.type):
    type = 'ProcessMemoryPriority'
    class _MemoryPriority(MEMORY_PRIORITY_, ULONG): pass
    _fields_ = [(_MemoryPriority, 'MemoryPriority')]

class PROCESS_MEMORY_EXHAUSTION_TYPE(pint.enum):
    _values_ = []
    # PMETypeFailFastOnCommitFailure

@ProcessInformationClass.define
class PROCESS_MEMORY_EXHAUSTION_INFO(pstruct.type):
    type = 'ProcessMemoryExhaustionInfo'
    class _Type(PROCESS_MEMORY_EXHAUSTION_TYPE, ULONG): pass
    _fields_ = [
        (USHORT, 'Version'),
        (USHORT, 'Reserved'),
        (_Type, 'Type'),
        (ULONG_PTR, 'Value'),
    ]

@ProcessInformationClass.define
class APP_MEMORY_INFORMATION(pstruct.type):
    type = 'ProcessAppMemoryInfo'
    _fields_ = [
        (ULONG64, 'AvailableCommit'),
        (ULONG64, 'PrivateCommitUsage'),
        (ULONG64, 'PeakPrivateCommitUsage'),
        (ULONG64, 'TotalCommitUsage'),
    ]

ProcessInformationClass.define(type='ProcessInPrivateInfo')(ptype.undefined)

@ProcessInformationClass.define
class PROCESS_POWER_THROTTLING_STATE(pstruct.type):
    type = 'ProcessPowerThrottling'
    _fields_ = [
        (ULONG, 'Version'),
        (ULONG, 'ControlMask'),
        (ULONG, 'StateMask'),
    ]

class PROTECTION_LEVEL_(pint.enum):
    _values_ = [
        ('WINTCB_LIGHT', 1),
        ('WINDOWS', 2),
        ('WINDOWS_LIGHT', 3),
        ('ANTIMALWARE_LIGHT', 4),
        ('LSA_LIGHT', 5),
        ('WINTCB', 6),
        ('CODEGEN_LIGHT', 7),
        ('AUTHENTICODE', 8),
        ('PPL_APP', 9),
        ('NONE', 10),
    ]

@ProcessInformationClass.define
class PROCESS_PROTECTION_LEVEL_INFORMATION(pstruct.type):
    type = 'ProcessProtectionLevelInfo'
    class _ProtectionLevel(PROTECTION_LEVEL_, DWORD): pass
    _fields_ = [
        (_ProtectionLevel, 'ProtectionLevel'),
    ]

@ProcessInformationClass.define
class PROCESS_LEAP_SECOND_INFO(pstruct.type):
    type = 'ProcessLeapSecondInfo'
    _fields_ = [
        (ULONG, 'Flags'),
        (ULONG, 'Reserved'),
    ]

@pbinary.littleendian
class MACHINE_ATTRIBUTES(pbinary.flags):
    _fields_ = [
        (29, 'Reserved'),
        (1, 'Wow64Container'),
        (1, 'KernelEnabled'),
        (1, 'UserEnabled'),
    ]

class IMAGE_FILE_MACHINE_(pint.enum):
    _values_ = [
        ('UNKNOWN', 0),
        ('TARGET_HOST', 0x0001),
        ('I386', 0x014c),
        ('R3000', 0x0162),
        ('R4000', 0x0166),
        ('R10000', 0x0168),
        ('WCEMIPSV2', 0x0169),
        ('ALPHA', 0x0184),
        ('SH3', 0x01a2),
        ('SH3DSP', 0x01a3),
        ('SH3E', 0x01a4),
        ('SH4', 0x01a6),
        ('SH5', 0x01a8),
        ('ARM', 0x01c0),
        ('THUMB', 0x01c2),
        ('ARMNT', 0x01c4),
        ('AM33', 0x01d3),
        ('POWERPC', 0x01F0),
        ('POWERPCFP', 0x01f1),
        ('IA64', 0x0200),
        ('MIPS16', 0x0266),
        ('ALPHA64', 0x0284),
        ('MIPSFPU', 0x0366),
        ('MIPSFPU16', 0x0466),
        ('AXP64', 0x0284),
        ('TRICORE', 0x0520),
        ('CEF', 0x0CEF),
        ('EBC', 0x0EBC),
        ('AMD64', 0x8664),
        ('M32R', 0x9041),
        ('ARM64', 0xAA64),
        ('CEE', 0xC0EE),
    ]

@ProcessInformationClass.define
class PROCESS_MACHINE_INFORMATION(pstruct.type):
    type = 'ProcessMachineTypeInfo'
    class _ProcessMachine(IMAGE_FILE_MACHINE_, USHORT): pass
    _fields_ = [
        (_ProcessMachine, 'ProcessMachine'),
        (USHORT, 'Res0'),
        (MACHINE_ATTRIBUTES, 'MachineAttributes'),
    ]

class PROCESSINFOCLASS(pint.enum):
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
        (77, 'ProcessActivityThrottlingState'),
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
        (100, 'ProcessAltSystemCallInformation'),
        (101, 'ProcessDynamicEHContinuationTargets'),
        (102, 'ProcessDynamicEnforcedCetCompatibleRanges'),
        (103, 'ProcessCreateStateChange'),
        (104, 'ProcessApplyStateChange'),
        (105, 'ProcessEnableOptionalXStateFeatures'),
        (106, 'ProcessAltPrefetchParam'),
        (107, 'ProcessAssignCpuPartitions'),
        (108, 'ProcessPriorityClassEx'),
        (109, 'ProcessMembershipInformation'),
        (110, 'ProcessEffectiveIoPriority'),
        (111, 'ProcessEffectivePagePriority'),
    ]]

class ProcessInfoClass(ptype.definition):
    cache = {}
    __key__ = staticmethod(lambda object: PROCESSINFOCLASS.byname(object.type, object.type))
    __get__ = classmethod(lambda cls, key, *args, **kwargs: super(ProcessInfoClass, cls).__get__(key if isinstance(key, tuple(integer.__class__ for integer in [sys.maxsize, sys.maxsize + 1])) else PROCESSINFOCLASS.byname(key), *args, **kwargs))
    __set__ = classmethod(lambda cls, key, object, **kwargs: setattr(object, cls.attribute, key) or super(ProcessInfoClass, cls).__set__(key, object, **kwargs))

## ProcessInfoClass definitions
@ProcessInfoClass.define
class PROCESS_BASIC_INFORMATION(pstruct.type, versioned):
    type = 'ProcessBasicInformation'

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

#@ProcessInfoClass.define
class QUOTA_LIMITS(pstruct.type, versioned):
    type = 'ProcessQuotaLimits'
    _fields_ = [
        (SIZE_T, 'PagedPoolLimit'),
        (SIZE_T, 'NonPagedPoolLimit'),
        (SIZE_T, 'MinimumWorkingSetSize'),
        (SIZE_T, 'MaximumWorkingSetSize'),
        (SIZE_T, 'PagefileLimit'),
        (LARGE_INTEGER, 'TimeLimit'),
    ]
class RATE_QUOTA_LIMIT(dynamic.union):
    @pbinary.littleendian
    class _ANONYMOUS_STRUCT(pbinary.flags):
        _fields_ = [            # FIXME: revserd
            (7, 'RatePercent'),
            (25, 'Reserved0'),
        ]
    _fields_ = [
        (ULONG, 'RateData'),
        (_ANONYMOUS_STRUCT, 'DUMMYSTRUCTNAME'),
    ]

@ProcessInfoClass.define
class QUOTA_LIMITS_EX(pstruct.type, versioned):
    type = 'ProcessQuotaLimits'
    _fields_ = [
        (SIZE_T, 'PagedPoolLimit'),
        (SIZE_T, 'NonPagedPoolLimit'),
        (SIZE_T, 'MinimumWorkingSetSize'),
        (SIZE_T, 'MaximumWorkingSetSize'),
        (SIZE_T, 'PagefileLimit'),
        (LARGE_INTEGER, 'TimeLimit'),
        (SIZE_T, 'WorkingSetLimit'),
        (SIZE_T, 'Reserved2'),
        (SIZE_T, 'Reserved3'),
        (SIZE_T, 'Reserved4'),
        (ULONG, 'Flags'),
        (RATE_QUOTA_LIMIT, 'CpuRateLimit'),
    ]

@ProcessInfoClass.define
class IO_COUNTERS(pstruct.type, versioned):
    type = 'ProcessIoCounters'
    _fields_ = [
        (ULONGLONG, 'ReadOperationCount'),
        (ULONGLONG, 'WriteOperationCount'),
        (ULONGLONG, 'OtherOperationCount'),
        (ULONGLONG, 'ReadTransferCount'),
        (ULONGLONG, 'WriteTransferCount'),
        (ULONGLONG, 'OtherTransferCount'),
    ]

@ProcessInfoClass.define
class VM_COUNTERS(pstruct.type, versioned):
    type = 'ProcessVmCounters'
    _fields_ = [
        (SIZE_T, 'PeakVirtualSize'),
        (SIZE_T, 'VirtualSize'),
        (ULONG, 'PageFaultCount'),
        (SIZE_T, 'PeakWorkingSetSize'),
        (SIZE_T, 'WorkingSetSize'),
        (SIZE_T, 'QuotaPeakPagedPoolUsage'),
        (SIZE_T, 'QuotaPagedPoolUsage'),
        (SIZE_T, 'QuotaPeakNonPagedPoolUsage'),
        (SIZE_T, 'QuotaNonPagedPoolUsage'),
        (SIZE_T, 'PagefileUsage'),
        (SIZE_T, 'PeakPagefileUsage'),
    ]
#@ProcessInfoClass.define
class VM_COUNTERS_EX(pstruct.type, versioned):
    type = 'ProcessVmCounters'
    _fields_ = [
        (SIZE_T, 'PeakVirtualSize'),
        (SIZE_T, 'VirtualSize'),
        (ULONG, 'PageFaultCount'),
        (SIZE_T, 'PeakWorkingSetSize'),
        (SIZE_T, 'WorkingSetSize'),
        (SIZE_T, 'QuotaPeakPagedPoolUsage'),
        (SIZE_T, 'QuotaPagedPoolUsage'),
        (SIZE_T, 'QuotaPeakNonPagedPoolUsage'),
        (SIZE_T, 'QuotaNonPagedPoolUsage'),
        (SIZE_T, 'PagefileUsage'),
        (SIZE_T, 'PeakPagefileUsage'),
        (SIZE_T, 'PrivateUsage'),
    ]
#@ProcessInfoClass.define
class VM_COUNTERS_EX2(pstruct.type, versioned):
    type = 'ProcessVmCounters'
    _fields_ = [
        (VM_COUNTERS_EX, 'CountersEx'),
        (SIZE_T, 'PrivateWorkingSetSize'),
        (SIZE_T, 'SharedCommitUsage'),
    ]
@ProcessInfoClass.define
class KERNEL_USER_TIMES(pstruct.type, versioned):
    type = 'ProcessTimes'
    _fields_ = [
        (LARGE_INTEGER, 'CreateTime'),
        (LARGE_INTEGER, 'ExitTime'),
        (LARGE_INTEGER, 'KernelTime'),
        (LARGE_INTEGER, 'UserTime'),
    ]

ProcessInfoClass.define(type='ProcessBasePriority')(umtypes.KPRIORITY)
ProcessInfoClass.define(type='ProcessRaisePriority')(ULONG)
ProcessInfoClass.define(type='ProcessDebugPort')(HANDLE)

@ProcessInfoClass.define
class PROCESS_EXCEPTION_PORT(pstruct.type, versioned):
    type = 'ProcessExceptionPort'
    _fields_ = [
        (HANDLE, 'ExceptionPortHandle'),
        (ULONG, 'StateFlags'),
    ]

@ProcessInfoClass.define
class PROCESS_ACCESS_TOKEN(pstruct.type, versioned):
    type = 'ProcessAccessToken'
    _fields_ = [
        (HANDLE, 'Token'),
        (HANDLE, 'Thread'),
    ]

@ProcessInfoClass.define
class PROCESS_LDT_INFORMATION(pstruct.type, versioned):
    type = 'ProcessLdtInformation'
    _fields_ = [
        (ULONG, 'Start'),
        (ULONG, 'Length'),
        (dyn.array(ketypes.LDT_ENTRY, 1), 'LdtEntries'),    # FIXME
    ]

@ProcessInfoClass.define
class PROCESS_LDT_SIZE(pstruct.type, versioned):
    type = 'ProcessLdtSize'
    _fields_ = [
        (ULONG, 'Length'),
    ]

ProcessInfoClass.define(type='ProcessDefaultHardErrorMode')(ULONG)

class EMULATOR_PORT_ACCESS_TYPE(pint.enum, ULONG):
    _fields_ = [
        ('Uchar', 0),
        ('Ushort', 1),
        ('Ulong', 2),
    ]
class EMULATOR_PORT_ACCESS_MODE(pint.enum):
    _fields_ = [
        ('EMULATOR_READ_ACCESS', 0x01),
        ('EMULATOR_WRITE_ACCESS', 0x02),
    ]

class EMULATOR_ACCESS_ENTRY(pstruct.type):
    class _AccessMode(EMULATOR_PORT_ACCESS_MODE, UCHAR):
        pass
    _fields_ = [
        (ULONG, 'BasePort'),
        (ULONG, 'NumConsecutivePorts'),
        (EMULATOR_PORT_ACCESS_TYPE, 'AccessType'),
        (_AccessMode, 'AccessMode'),
        (UCHAR, 'StringSupport'),
        (PVOID, 'Routine'),
    ]

@ProcessInfoClass.define
class PROCESS_IO_PORT_HANDLER_INFORMATION(pstruct.type, versioned):
    type = 'ProcessIoPortHandlers'
    _fields_ = [
        (BOOLEAN, 'Install'),
        (ULONG, 'NumEntries'),
        (ULONG, 'Context'),
        (P(EMULATOR_ACCESS_ENTRY), 'EmulatorAccessEntries'),
    ]

@ProcessInfoClass.define
class POOLED_USAGE_AND_LIMITS(pstruct.type, versioned):
    type = 'ProcessPooledUsageAndLimits'
    _fields_ = [
        (SIZE_T, 'PeakPagedPoolUsage'),
        (SIZE_T, 'PagedPoolUsage'),
        (SIZE_T, 'PagedPoolLimit'),
        (SIZE_T, 'PeakNonPagedPoolUsage'),
        (SIZE_T, 'NonPagedPoolUsage'),
        (SIZE_T, 'NonPagedPoolLimit'),
        (SIZE_T, 'PeakPagefileUsage'),
        (SIZE_T, 'PagefileUsage'),
        (SIZE_T, 'PagefileLimit'),
    ]

@ProcessInfoClass.define
class PROCESS_WS_WATCH_INFORMATION(parray.type):
    type = 'ProcessWorkingSetWatch'
    _fields_ = [
        (PVOID, 'FaultingPc'),
        (PVOID, 'FaultingVa'),
    ]

ProcessInfoClass.define(type='ProcessUserModeIOPL')(ULONG)
ProcessInfoClass.define(type='ProcessEnableAlignmentFaultFixup')(BOOLEAN)

class PROCESS_PRIORITY_CLASS_(pint.enum):
    _values_ = [
        ('UNKNOWN', 0),
        ('IDLE', 1),
        ('NORMAL', 2),
        ('HIGH', 3),
        ('REALTIME', 4),
        ('BELOW_NORMAL', 5),
        ('ABOVE_NORMAL', 6),
    ]

@ProcessInfoClass.define
class PROCESS_PRIORITY_CLASS(pstruct.type, versioned):
    type = 'ProcessPriorityClass'
    _fields_ = [
        (BOOLEAN, 'Foreground'),
        (UCHAR, 'PriorityClass'),
    ]

ProcessInfoClass.define(type='ProcessWx86Information')(ULONG)

#ProcessInfoClass.define(type='ProcessHandleCount')(ULONG)
@ProcessInfoClass.define
class PROCESS_HANDLE_INFORMATION(pstruct.type, versioned):
    type = 'ProcessHandleCount'
    _fields_ = [
        (ULONG, 'HandleCount'),
        (ULONG, 'HandleCountHighWatermark'),
    ]

ProcessInfoClass.define(type='ProcessAffinityMask')(umtypes.KAFFINITY)
ProcessInfoClass.define(type='ProcessPriorityBoost')(ULONG)

#@ProcessInfoClass.define
class PROCESS_DEVICEMAP_INFORMATION(dynamic.union):
    type = 'ProcessDeviceMap'
    class _Query(pstruct.type):
        _fields_ = [
            (ULONG, 'DriveMap'),
            (dyn.array(UCHAR, 32), 'DriveType'),
        ]
    _fields_ = [
        (HANDLE, 'DeviceHandle'),
        (_Query, 'Query'),
    ]

@ProcessInfoClass.define
class PROCESS_DEVICEMAP_INFORMATION_EX(pstruct.type, versioned):
    type = 'ProcessDeviceMap'
    class _u(PROCESS_DEVICEMAP_INFORMATION):
        pass
    _fields_ = [
        (_u, 'u'),
        (ULONG, 'Flags'),
    ]

@ProcessInfoClass.define
class PROCESS_SESSION_INFORMATION(pstruct.type, versioned):
    type = 'ProcessSessionInformation'

@ProcessInfoClass.define
class PROCESS_FOREGROUND_BACKGROUND(pstruct.type, versioned):
    type = 'ProcessForegroundInformation'

ProcessInfoClass.define(type='ProcessWow64Information')(ULONG_PTR)
ProcessInfoClass.define(type='ProcessImageFileName')(umtypes.UNICODE_STRING)
ProcessInfoClass.define(type='ProcessLUIDDeviceMapsEnabled')(ULONG)
ProcessInfoClass.define(type='ProcessBreakOnTermination')(ULONG)
ProcessInfoClass.define(type='ProcessDebugObjectHandle')(ULONG)
ProcessInfoClass.define(type='ProcessDebugFlags')(ULONG)

class PROCESS_HANDLE_TRACING_ENTRY(pstruct.type):
    PROCESS_HANDLE_TRACING_MAX_STACKS = 16
    _fields_ = [
        (HANDLE, 'Handle'),
        (umtypes.CLIENT_ID, 'ClientId'),
        (ULONG, 'Type'),
        (dyn.array(PVOID, PROCESS_HANDLE_TRACING_MAX_STACKS), 'Stacks'),
    ]

@ProcessInfoClass.define
class PROCESS_HANDLE_TRACING_QUERY(pstruct.type, versioned):
    type = 'ProcessHandleTracing'
    _fields_ = [
        (HANDLE, 'Handle'),
        (ULONG, 'TotalTraces'),
        (dyn.array(PROCESS_HANDLE_TRACING_ENTRY, 1), 'HandleTrace'),
    ]

class _IO_PRIORITY_HINT(pint.enum):
    _values_ = [
        ('IoPriorityVeryLow', 0),
        ('IoPriorityLow', 1),
        ('IoPriorityNormal', 2),
        ('IoPriorityHigh', 3),
        ('IoPriorityCritical', 4),
    ]
@ProcessInfoClass.define
class IO_PRIORITY_HINT(_IO_PRIORITY_HINT):
    type = 'ProcessIoPriority'
    length = 4

ProcessInfoClass.define(type='ProcessExecuteFlags')(ULONG)

class THREAD_TLS_INFORMATION(pstruct.type):
    _fields_ = [
        (ULONG, 'Flags'),
        (PVOID, 'NewTlsData'),
        (PVOID, 'OldTlsData'),
        (HANDLE, 'ThreadId'),
    ]

class PROCESS_TLS_INFORMATION_TYPE(pint.enum):
    _values_ = [
        ('ProcessTlsReplaceIndex', 0),
        ('ProcessTlsReplaceVector', 1),
    ]

@ProcessInfoClass.define
class PROCESS_TLS_INFORMATION(pstruct.type, versioned):
    type = 'ProcessResourceManagement'
    'ProcessTlsInformation'
    _fields_ = [
        (ULONG, 'Flags'),
        (ULONG, 'OperationType'),
        (ULONG, 'ThreadDataCount'),
        (ULONG, 'TlsIndex'),
        (ULONG, 'PreviousCount'),
        (dyn.array(THREAD_TLS_INFORMATION, 1), 'ThreadData'),   # FIXME
    ]

ProcessInfoClass.define(type='ProcessCookie')(ULONG)
ProcessInfoClass.define(type='ProcessImageInformation')(mmtypes.SECTION_IMAGE_INFORMATION)

@ProcessInfoClass.define
class PROCESS_CYCLE_TIME_INFORMATION(pstruct.type, versioned):
    type = 'ProcessCycleTime'
    _fields_ = [
        (ULONGLONG, 'AccumulatedCycles'),
        (ULONGLONG, 'CurrentCycleCount'),
    ]

@ProcessInfoClass.define
class PAGE_PRIORITY_INFORMATION(pstruct.type, versioned):
    type = 'ProcessPagePriority'
    _fields_ = [
        (ULONG, 'PagePriority'),
    ]

@ProcessInfoClass.define
class PROCESS_INSTRUMENTATION_CALLBACK_INFORMATION(pstruct.type, versioned):
    type = 'ProcessInstrumentationCallback'
    _fields_ = [
        (ULONG, 'Version'),
        (ULONG, 'Reserved'),
        (PVOID, 'Callback'),
    ]

#@ProcessInfoClass.define
class PROCESS_STACK_ALLOCATION_INFORMATION(pstruct.type, versioned):
    type = 'ProcessThreadStackAllocation'
    _fields_ = [
        (SIZE_T, 'ReserveSize'),
        (SIZE_T, 'ZeroBits'),
        (PVOID, 'StackBase'),
    ]

@ProcessInfoClass.define
class PROCESS_STACK_ALLOCATION_INFORMATION_EX(pstruct.type, versioned):
    type = 'ProcessThreadStackAllocation'
    _fields_ = [
        (ULONG, 'PreferredNode'),
        (ULONG, 'Reserved0'),
        (ULONG, 'Reserved1'),
        (ULONG, 'Reserved2'),
        (PROCESS_STACK_ALLOCATION_INFORMATION, 'AllocInfo'),
    ]

@ProcessInfoClass.define
class PROCESS_WS_WATCH_INFORMATION_EX(pstruct.type, versioned):
    type = 'ProcessWorkingSetWatchEx'
    length, _object_ = 0, VOID  # FIXME

ProcessInfoClass.define(type='ProcessImageFileNameWin32')(umtypes.UNICODE_STRING)
ProcessInfoClass.define(type='ProcessImageFileMapping')(ULONG)

@ProcessInfoClass.define
class PROCESS_AFFINITY_UPDATE_MODE(dynamic.union):
    type = 'ProcessAffinityUpdateMode'
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [    # FIXME: reversed
            (1, 'EnableAutoUpdate'),
            (1, 'Permanent'),
            (30, 'Reserved'),
        ]
    _fields_ = [
        (ULONG, 'Flags'),
        (_Flags, '_b'),
    ]

@ProcessInfoClass.define
class PROCESS_MEMORY_ALLOCATION_MODE(pstruct.type, versioned):
    type = 'ProcessMemoryAllocationMode'
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [    # FIXME: reversed
            (1, 'Reserved'),
            (31, 'TopDown'),
        ]
    _fields_ = [
        (ULONG, 'Flags'),
        (_Flags, '_b'),
    ]

ProcessInfoClass.define(type='ProcessGroupInformation')(dyn.clone(parray.block, _object_=USHORT))
ProcessInfoClass.define(type='ProcessTokenVirtualizationEnabled')(ULONG)
ProcessInfoClass.define(type='ProcessConsoleHostProcess')(ULONG_PTR)

@ProcessInfoClass.define
class PROCESS_WINDOW_INFORMATION(pstruct.type, versioned):
    type = 'ProcessWindowInformation'
    _fields_ = [
        (ULONG, 'WindowFlags'),
        (USHORT, 'WindowTitleLength'),
        (dyn.array(WCHAR, 1), 'WindowTitle'),   # FIXME
    ]

class PROCESS_HANDLE_TABLE_ENTRY_INFO(pstruct.type):
    _fields_ = [
        (HANDLE, 'HandleValue'),
        (ULONG_PTR, 'HandleCount'),
        (ULONG_PTR, 'PointerCount'),
        (ULONG, 'GrantedAccess'),
        (ULONG, 'ObjectTypeIndex'),
        (ULONG, 'HandleAttributes'),
        (ULONG, 'Reserved'),
    ]

@ProcessInfoClass.define
class PROCESS_HANDLE_SNAPSHOT_INFORMATION(pstruct.type, versioned):
    type = 'ProcessHandleInformation'
    _fields_ = [
        (ULONG_PTR, 'NumberOfHandles'),
        (ULONG_PTR, 'Reserved'),
        (PROCESS_HANDLE_TABLE_ENTRY_INFO, 'Handles[1]'),
    ]

class PROCESS_MITIGATION_POLICY(pint.enum):
    _fields_ = [(name, index) for index, name in enumerate([
        'ProcessDEPPolicy',
        'ProcessASLRPolicy',
        'ProcessDynamicCodePolicy',
        'ProcessStrictHandleCheckPolicy',
        'ProcessSystemCallDisablePolicy',
        'ProcessMitigationOptionsMask',
        'ProcessExtensionPointDisablePolicy',
        'ProcessControlFlowGuardPolicy',
        'ProcessSignaturePolicy',
        'ProcessFontDisablePolicy',
        'ProcessImageLoadPolicy',
        'ProcessSystemCallFilterPolicy',
        'ProcessPayloadRestrictionPolicy',
        'ProcessChildProcessPolicy',
        'ProcessSideChannelIsolationPolicy',
        'ProcessUserShadowStackPolicy',
        'ProcessRedirectionTrustPolicy',
        'ProcessUserPointerAuthPolicy',
        'ProcessSEHOPPolicy',
  ])]

@ProcessInfoClass.define
class PROCESS_MITIGATION_POLICY_INFORMATION(pstruct.type, versioned):
    type = 'ProcessMitigationPolicy'
    class _Policy(PROCESS_MITIGATION_POLICY, ULONG):
        pass
    _fields_ = [
        (_Policy, 'Policy'),
        (ptype.undefined, 'u'), # FIXME: https://github.com/winsiderss/systeminformer/blob/0cebf35f8464c11726f551980d31c0593d0717a0/phnt/include/ntpsapi.h
    ]

ProcessInfoClass.define(type='ProcessHandleCheckingMode')(ULONG)

@ProcessInfoClass.define
class PROCESS_KEEPALIVE_COUNT_INFORMATION(pstruct.type, versioned):
    type = 'ProcessKeepAliveCount'
    _fields_ = [
        (ULONG, 'WakeCount'),
        (ULONG, 'NoWakeCount'),
    ]

@ProcessInfoClass.define
class PROCESS_REVOKE_FILE_HANDLES_INFORMATION(pstruct.type, versioned):
    type = 'ProcessRevokeFileHandles'
    _fields_ = [
        (umtypes.UNICODE_STRING, 'TargetDevicePath'),
    ]

class PROCESS_WORKING_SET_OPERATION(pint.enum):
    _values_ = [
        ('ProcessWorkingSetSwap', 0),
        ('ProcessWorkingSetEmpty', 1),
    ]

@ProcessInfoClass.define
class PROCESS_WORKING_SET_CONTROL(pstruct.type, versioned):
    type = 'ProcessWorkingSetControl'
    class _Operation(PROCESS_WORKING_SET_OPERATION, ULONG):
        pass
    _fields_ = [
        (ULONG, 'Version'),
        (_Operation, 'Operation'),
        (ULONG, 'Flags'),
    ]

ProcessInfoClass.define(type='ProcessHandleTable')(dyn.clone(parray.block, _object_=ULONG))
ProcessInfoClass.define(type='ProcessCheckStackExtentsMode')(ULONG)
ProcessInfoClass.define(type='ProcessCommandLineInformation')(umtypes.UNICODE_STRING)

@ProcessInfoClass.define
class PS_PROTECTION(dynamic.union):
    type = 'ProcessProtectionInformation'
    class _Level(pbinary.flags):
        _fields_ = [
            (3, 'Type'),
            (1, 'Audit'),
            (4, 'Signer'),
        ]
    _fields_ = [
        (UCHAR, 'Level'),
        (_Level, 'f'),  # FIXME: order
    ]

class PROCESS_MEMORY_EXHAUSTION_TYPE(pint.enum, ULONG):
    _values_ = [(n, v) for v, n in [
        (0, 'PMETypeFaultFastOnCommitFailure'),
    ]]

@ProcessInfoClass.define
class PROCESS_MEMORY_EXHAUSTION_INFO(pstruct.type, versioned):
    type = 'ProcessMemoryExhaustion'
    _fields_ = [
        (USHORT, 'Version'),
        (USHORT, 'Reserved'),
        (PROCESS_MEMORY_EXHAUSTION_TYPE, 'Value'),
        (ULONGLONG, 'Value'),
    ]

@ProcessInfoClass.define
class PROCESS_FAULT_INFORMATION(pstruct.type, versioned):
    type = 'ProcessFaultInformation'
    _fields_ = [
        (ULONG, 'FaultFlags'),
        (ULONG, 'AdditionalInfo'),
    ]

@ProcessInfoClass.define
class PROCESS_TELEMETRY_ID_INFORMATION(pstruct.type, versioned):
    type = 'ProcessTelemetryIdInformation'
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

@ProcessInfoClass.define
class PROCESS_COMMIT_RELEASE_INFORMATION(pstruct.type, versioned):
    type = 'ProcessCommitReleaseInformation'
    @pbinary.littleendian
    class _f(pbinary.flags):
        _fields_ = [
            (1, 'Eligible'),
            (1, 'ReleaseRepurposedMemResetCommit'),
            (1, 'ForceReleaseMemResetCommit'),
            (29, 'Spare'),
        ]
    _fields_ = [
        (ULONG, 'Version'),
        (_f, 'f'),  # FIXME: order
        (SIZE_T, 'CommitDebt'),
        (SIZE_T, 'CommittedMemResetSize'),
        (SIZE_T, 'RepurposedMemResetSize'),
    ]

@ProcessInfoClass.define
class PROCESS_JOB_MEMORY_INFO(pstruct.type, versioned):
    type = 'ProcessJobMemoryInformation'
    _fields_ = [
        (ULONGLONG, 'SharedCommitUsage'),
        (ULONGLONG, 'PrivateCommitUsage'),
        (ULONGLONG, 'PeakPrivateCommitUsage'),
        (ULONGLONG, 'PrivateCommitLimit'),
        (ULONGLONG, 'TotalCommitLimit'),
    ]

ProcessInfoClass.define(type='ProcessRaiseUMExceptionOnInvalidHandleClose')(ULONG)

@ProcessInfoClass.define
class PROCESS_CHILD_PROCESS_INFORMATION(pstruct.type, versioned):
    type = 'ProcessChildProcessInformation'
    _fields_ = [
        (BOOLEAN, 'ProhibitChildProcesses'),
        (BOOLEAN, 'AlwaysAllowSecureChildProcess'),
        (BOOLEAN, 'AuditProhibitChildProcesses'),
    ]

ProcessInfoClass.define(type='ProcessHighGraphicsPriorityInformation')(BOOLEAN)

@ProcessInfoClass.define
class SUBSYSTEM_INFORMATION_TYPE(pint.enum, ULONG):
    type = 'ProcessSubsystemInformation'
    _values_ = [
        ('SubsystemInformationTypeWin32', 0),
        ('SubsystemInformationTypeWSL', 1),
    ]

class ENERGY_STATE_DURATION(dynamic.union):
    class _ChangeTime(pstruct.type):
        @pbinary.littleendian
        class _Duration(pbinary.flags):
            _fields_ = [    # FIXME: reversed
                (1, 'IsInState'),
                (31, 'Duration'),
            ]
        _fields_ = [
            (ULONG, 'LastChangeTime'),
            (ULONG, 'Duration:31'),
            (ULONG, 'IsInState:1'),
        ]
    _fields_ = [
        (ULONGLONG, 'Value'),
        (_ChangeTime, 'ChangeTime'),
    ]

#@ProcessInfoClass.define
class PROCESS_ENERGY_VALUES(pstruct.type, versioned):
    type = 'ProcessEnergyValues'
    class _ULONGLONGPAIR(parray.type):
        _object_, length = ULONGLONG, 2
    class _Durations(pstruct.type):
        _fields_ = [
            (ENERGY_STATE_DURATION, 'ForegroundDuration'),
            (ENERGY_STATE_DURATION, 'DesktopVisibleDuration'),
            (ENERGY_STATE_DURATION, 'PSMForegroundDuration'),
        ]
    _fields_ = [
        (dyn.array(_ULONGLONGPAIR, 4), 'Cycles'),
        (ULONGLONG, 'DiskEnergy'),
        (ULONGLONG, 'NetworkTailEnergy'),
        (ULONGLONG, 'MBBTailEnergy'),
        (ULONGLONG, 'NetworkTxRxBytes'),
        (ULONGLONG, 'MBBTxRxBytes'),
        (_Durations, 'Durations'),
        (ULONG, 'CompositionRendered'),
        (ULONG, 'CompositionDirtyGenerated'),
        (ULONG, 'CompositionDirtyPropagated'),
        (ULONG, 'Reserved1'),
        (dyn.array(_ULONGLONGPAIR, 4), 'AttributedCycles'),
        (dyn.array(_ULONGLONGPAIR, 4), 'WorkOnBehalfCycles'),
    ]

class TIMELINE_BITMAP(pstruct.type):
    class _Bitmap(pstruct.type):
        _fields_ = [
            (ULONG, 'EndTime'),
            (ULONG, 'Bitmap'),
        ]
    _fields_ = [
        (ULONGLONG, 'Value'),
        (_Bitmap, 'Bitmap'),
    ]

class PROCESS_ENERGY_VALUES_EXTENSION(pstruct.type):
    class _Timelines(dynamic.union):
        class _Bitmaps(pstruct.type):
            _fields_ = [
                (TIMELINE_BITMAP, 'CpuTimeline'),
                (TIMELINE_BITMAP, 'DiskTimeline'),
                (TIMELINE_BITMAP, 'NetworkTimeline'),
                (TIMELINE_BITMAP, 'MBBTimeline'),
                (TIMELINE_BITMAP, 'ForegroundTimeline'),
                (TIMELINE_BITMAP, 'DesktopVisibleTimeline'),
                (TIMELINE_BITMAP, 'CompositionRenderedTimeline'),
                (TIMELINE_BITMAP, 'CompositionDirtyGeneratedTimeline'),
                (TIMELINE_BITMAP, 'CompositionDirtyPropagatedTimeline'),
                (TIMELINE_BITMAP, 'InputTimeline'),
                (TIMELINE_BITMAP, 'AudioInTimeline'),
                (TIMELINE_BITMAP, 'AudioOutTimeline'),
                (TIMELINE_BITMAP, 'DisplayRequiredTimeline'),
                (TIMELINE_BITMAP, 'KeyboardInputTimeline'),
            ]
        _fields_ = [
            (dyn.array(TIMELINE_BITMAP, 14), 'Timelines'),   # FIXME: 9 for REDSTONE2, 14 for REDSTONE3/4/5
            (_Bitmaps, 'Bitmaps'),
        ]
    class _Durations(dynamic.union):
        class _States(pstruct.type):
            _fields_ = [
                (ENERGY_STATE_DURATION, 'InputDuration'),
                (ENERGY_STATE_DURATION, 'AudioInDuration'),
                (ENERGY_STATE_DURATION, 'AudioOutDuration'),
                (ENERGY_STATE_DURATION, 'DisplayRequiredDuration'),
                (ENERGY_STATE_DURATION, 'PSMBackgroundDuration'),
            ]
        _fields_ = [
            (dyn.array(ENERGY_STATE_DURATION, 5), 'Durations'),
            (_States, 'States'),
        ]
    _fields_ = [
        (_Timelines, 'Timelines'),
        (_Durations, 'Durations'),
        (ULONG, 'KeyboardInput'),
        (ULONG, 'MouseInput'),
    ]

@ProcessInfoClass.define
class PROCESS_EXTENDED_ENERGY_VALUES(pstruct.type, versioned):
    type = 'ProcessEnergyValues'
    _fields_= [
        (PROCESS_ENERGY_VALUES, 'Base'),
        (PROCESS_ENERGY_VALUES_EXTENSION, 'Extension'),
    ]

@ProcessInfoClass.define
class PROCESS_ACTIVITY_THROTTLE_POLICY(pstruct.type, versioned):
    type = 'ProcessActivityThrottlePolicy'
    'ProcessReserved3Information'
    [
    ]

@ProcessInfoClass.define
class WIN32K_SYSCALL_FILTER(pstruct.type, versioned):
    type = 'ProcessWin32kSyscallFilterInformation'
    _fields_ = [
        (ULONG, 'FilterState'),
        (ULONG, 'FilterSet'),
    ]
class JOBOBJECT_WAKE_FILTER(pstruct.type):
    _fields_ = [
        (ULONG, 'HighEdgeFilter'),
        (ULONG, 'LowEdgeFilter'),
    ]

@ProcessInfoClass.define
class PROCESS_WAKE_INFORMATION(pstruct.type, versioned):
    type = 'ProcessWakeInformation'
    _fields_ = [
        (ULONGLONG, 'NotificationChannel'),
        (dyn.array(ULONG, 7), 'WakeCounters'),
        (P(JOBOBJECT_WAKE_FILTER), 'WakeFilter'),
    ]

@ProcessInfoClass.define
class PROCESS_ENERGY_TRACKING_STATE(pstruct.type, versioned):
    type = 'ProcessEnergyTrackingState'
    @pbinary.littleendian
    class _UpdateTag(pbinary.flags):
        _fields_ = [
            (31, 'Unused'),
            (1, 'UpdateTag'),
        ]
    _fields_ = [
        (ULONG, 'StateUpdateMask'),
        (ULONG, 'StateDesiredValue'),
        (ULONG, 'StateSequence'),
        (_UpdateTag, 'UpdateTag'),  # FIXME: order
        (dyn.array(WCHAR, 64), 'Tag'),
    ]

@ProcessInfoClass.define
class MANAGE_WRITES_TO_EXECUTABLE_MEMORY(pstruct.type, versioned):
    type = 'ProcessManageWritesToExecutableMemory'
    @pbinary.littleendian
    class _flags(pbinary.flags):
        _fields_ = [
            (8, 'Version'),
            (1, 'ProcessEnableWriteExceptions'),
            (1, 'ThreadAllowWrites'),
            (22, 'Spare'),
        ]
    _fields_ = [
        (_flags, 'f'),  # FIXME: order
        (PVOID, 'KernelWriteToExecutableSignal'),
    ]

@ProcessInfoClass.define
class PROCESS_READWRITEVM_LOGGING_INFORMATION(pstruct.type, versioned):
    type = 'ProcessEnableReadWriteVmLogging'
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (1, 'EnableReadVmLogging'),
            (1, 'EnableWriteVmLogging'),
            (6, 'Unused'),
        ]
    _fields_ = [
        (UCHAR, 'Flags'),
        (_Flags, 'f'),  # FIXME: order
    ]

@ProcessInfoClass.define
class PROCESS_UPTIME_INFORMATION(pstruct.type, versioned):
    type = 'ProcessUptimeInformation'

    class _f(ULONG):
        '''union {
            ULONG HangCount : 4;
            ULONG GhostCount : 4;
            ULONG Crashed : 1;
            ULONG Terminated : 1;
        }'''

    _fields_ = [
        (ULONGLONG, 'QueryInterruptTime'),
        (ULONGLONG, 'QueryUnbiasedTime'),
        (ULONGLONG, 'EndInterruptTime'),
        (ULONGLONG, 'TimeSinceCreation'),
        (ULONGLONG, 'Uptime'),
        (ULONGLONG, 'SuspendedTime'),
        (_f, 'f'),  # FIXME: this is a union of binary fields
    ]

ProcessInfoClass.define(type='ProcessImageSection')(HANDLE)

@ProcessInfoClass.define
class PROCESS_SYSTEM_RESOURCE_MANAGEMENT(pstruct.type, versioned):
    type = 'ProcessSystemResourceManagement'
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
        (1, 'Foreground'),
        (31, 'Reserved'),
        ]
    _fields_ = [
        (ULONG, 'Flags'),
        (_Flags, 'f'),  # FIXME: order
    ]

ProcessInfoClass.define(type='ProcessSequenceNumber')(ULONGLONG)

@ProcessInfoClass.define
class PROCESS_SECURITY_DOMAIN_INFORMATION(pstruct.type, versioned):
    type = 'ProcessSecurityDomainInformation'
    _fields_ = [
        (ULONGLONG, 'SecurityDomain'),
    ]

@ProcessInfoClass.define
class PROCESS_COMBINE_SECURITY_DOMAINS_INFORMATION(pstruct.type, versioned):
    type = 'ProcessCombineSecurityDomainsInformation'
    _fields_ = [
        (HANDLE, 'ProcessHandle'),
    ]

@ProcessInfoClass.define
class PROCESS_LOGGING_INFORMATION(pstruct.type, versioned):
    type = 'ProcessEnableLogging'
    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (1, 'EnableReadVmLogging'),
            (1, 'EnableWriteVmLogging'),
            (1, 'EnableProcessSuspendResumeLogging'),
            (1, 'EnableThreadSuspendResumeLogging'),
            (28, 'Reserved'),
        ]
    _fields_ = [
        (ULONG, 'Flags'),
        (_Flags, 'f'),  # FIXME: order
    ]

@ProcessInfoClass.define
class PROCESS_LEAP_SECOND_INFORMATION(PROCESS_LEAP_SECOND_INFO):
    type = 'ProcessLeapSecondInformation'

@ProcessInfoClass.define
class PROCESS_FIBER_SHADOW_STACK_ALLOCATION_INFORMATION(pstruct.type, versioned):
    type = 'ProcessFiberShadowStackAllocation'
    _fields_ = [
        (ULONGLONG, 'ReserveSize'),
        (ULONGLONG, 'CommitSize'),
        (ULONG, 'PreferredNode'),
        (ULONG, 'Reserved'),
        (PVOID, 'Ssp'),
    ]

@ProcessInfoClass.define
class PROCESS_FREE_FIBER_SHADOW_STACK_ALLOCATION_INFORMATION(pstruct.type, versioned):
    type = 'ProcessFreeFiberShadowStackAllocation'
    _fields_ = [
        (PVOID, 'Ssp'),
    ]

ProcessInfoClass.define(type='ProcessAltSystemCallInformation')(BOOLEAN)

@ProcessInfoClass.define
class PROCESS_DYNAMIC_EH_CONTINUATION_TARGETS_INFORMATION(pstruct.type, versioned):
    type = 'ProcessDynamicEHContinuationTargets'
    [
    ]

@ProcessInfoClass.define
class PROCESS_DYNAMIC_ENFORCED_ADDRESS_RANGE_INFORMATION(pstruct.type, versioned):
    type = 'ProcessDynamicEnforcedCetCompatibleRanges'
    [
    ]

ProcessInfoClass.define(type='ProcessEnableOptionalXStateFeatures')(ULONG64)

@ProcessInfoClass.define
class PROCESS_PRIORITY_CLASS_EX(pstruct.type, versioned):
    type = 'ProcessPriorityClassEx'
    [
    ]

@ProcessInfoClass.define
class PROCESS_MEMBERSHIP_INFORMATION(pstruct.type, versioned):
    type = 'ProcessMembershipInformation'
    [
    ]

ProcessInfoClass.define(type='ProcessEffectiveIoPriority')(IO_PRIORITY_HINT)
ProcessInfoClass.define(type='ProcessEffectivePagePriority')(ULONG)

### API_SET_SCHEMA
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
