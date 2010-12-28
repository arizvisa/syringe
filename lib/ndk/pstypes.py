from WinNT import *
from ptypes import *
from umtypes import *
from ldrtypes import *
import heaptypes,sdkddkver

class PEB_FREE_BLOCK(pstruct.type): pass
class PPEB_FREE_BLOCK(dyn.pointer(PEB_FREE_BLOCK)): pass
PEB_FREE_BLOCK._fields_ = [(PPEB_FREE_BLOCK,'Next'),(ULONG,'Size')]

class PEB(pstruct.type):
    class BitField(pbinary.struct):
        _fields_ = [
            (1, 'ImageUsesLargePages'),
            (1, 'IsProtectedProcess'),
            (1, 'IsLegacyProcess'),
            (1, 'IsImageDynamicallyRelocated'),
            (1, 'SkipPatchingUser32Forwarders'),
            (1, 'SpareBits'),
        ]

    def __init__(self, **attrs):
        super(pstruct.type, self).__init__(**attrs)

        try:
            self.NTDDI_VERSION
        except:
            self.NTDDI_VERSION = sdkddkver.NTDDI_VERSION

        self._fields_ = f = []
        f.extend([
            (UCHAR, 'InheritedAddressSpace'),
            (UCHAR, 'ReadImageFileExecOptions'),
            (UCHAR, 'BeingDebugged'),
        ])
        if self.NTDDI_VERSION >= sdkddkver.NTDDI_LONGHORN:
            f.append( (self.BitField, 'BitField') )
        else:
            f.append( (BOOLEAN, 'SpareBool') )
            
        f.extend([
            (HANDLE, 'Mutant'),
            (PVOID, 'ImageBaseAddress'),
            (PPEB_LDR_DATA, 'Ldr'),
            ##
            (PVOID, 'ProcessParameters'),
            (pint.uint32_t, 'SubSystemData'),
            (dyn.pointer(heaptypes.HEAP), 'ProcessHeap'),
        ])

        if self.NTDDI_VERSION >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (pint.uint32_t, 'FastPebLock'),
                (PVOID, 'AltThunkSListPtr'),
                (PVOID, 'IFEOKey'),
                (ULONG, 'CrossProcessFlags'),
                (PVOID, 'UserSharedInfoPtr'),
                (ULONG, 'SystemReserved'),
                (ULONG, 'SpareUlong'),
                (ULONG, 'SparePebPtr0'),
            ])
        else:
            f.extend([
                (PVOID, 'FastPebLock'),
                (pint.uint32_t, 'FastPebLockRoutine'),
                (pint.uint32_t, 'FastPebUnlockRoutine'),
                (ULONG, 'EnvironmentUpdateCount'),
                (pint.uint32_t, 'KernelCallbackTable'),
                (PVOID, 'EventLogSection'),
                (PVOID, 'EventLog'),
                (PPEB_FREE_BLOCK, 'FreeList'),
            ])
        
        f.extend([
            (ULONG, 'TlxExpansionCounter'),
            (PVOID, 'TlsBitmap'),
            (dyn.array(ULONG,2), 'TlsBitmapBits'),
            (PVOID, 'ReadOnlySharedMemoryBase'),
        ])

        if self.NTDDI_VERSION >= sdkddkver.NTDDI_LONGHORN:
            f.append( (PVOID, 'HotpatchInformation') )
        else:
            f.append( (PVOID, 'ReadOnlySharedMemoryHeap') )

        f.extend([
            (PVOID, 'ReadOnlyStaticServerData'),
            (PVOID, 'AnsiCodePageData'),
            (PVOID, 'OemCodePageData'),
            (PVOID, 'UnicodeCaseTableData'),
            (ULONG, 'NumberOfProcessors'),
            (ULONG, 'NtGlobalFlag'),
            (ULONG, 'Reserved'),
            (LARGE_INTEGER, 'CriticalSectionTimeout'),
            (ULONG, 'HeapSegmentReserve'),
            (ULONG, 'HeapSegmentCommit'),
            (ULONG, 'HeapDeCommitTotalFreeThreshold'),
            (ULONG, 'HeapDeCommitFreeBlockThreshold'),
            (ULONG, 'NumberOfHeaps'),
            (ULONG, 'MaximumNumberOfHeaps'),
            (PVOID, 'ProcessHeaps'),
            (PVOID, 'GdiSharedHandleTable'),
            (PVOID, 'ProcessStarterHelper'),
            (ULONG, 'GdiDCAttributeList'),
        ])
        if self.NTDDI_VERSION >= sdkddkver.NTDDI_LONGHORN:
            f.append( (PVOID, 'LoaderLock') )
        else:
            f.append( (PVOID, 'LoaderLock') )
        
        f.extend([
            (ULONG, 'OSMajorVersion'),
            (ULONG, 'OSMinorVersion'),
            (USHORT, 'OSBuildNumber'),
            (USHORT, 'OSCSDVersion'),
            (ULONG, 'OSPlatformId'),
            (ULONG, 'ImageSubSystem'),
            (ULONG, 'ImageSubSystemMajorVersion'),
            (ULONG, 'ImageSubSystemMinorVersion'),
            (ULONG, 'ImageProcessAffinityMask'),
            (dyn.array(ULONG,0x22), 'GdiHandleBuffer'),
            (pint.uint32_t, 'PostProcessInitRoutine'),
            (pint.uint32_t, 'TlsExpansionBitmap'),
            (dyn.array(ULONG,0x20), 'TlsExpansionBitmapBits'),
            (ULONG, 'SessionId'),
        ])
        if self.NTDDI_VERSION >= sdkddkver.NTDDI_WINXP:
            f.extend([
                (ULARGE_INTEGER, 'AppCompatFlags'),
                (ULARGE_INTEGER, 'AppCompatFlagsUser'),
                (PVOID, 'pShimData'),
                (PVOID, 'AppCompatInfo'),
                (UNICODE_STRING, 'CSDVersion'),
                (pint.uint32_t, 'ActivationContextData'),
                (pint.uint32_t, 'ProcessAssemblyStorageMap'),
                (pint.uint32_t, 'SystemDefaultActivationContextData'),
                (pint.uint32_t, 'SystemAssemblyStorageMap'),
                (ULONG, 'MinimumStackCommit'),
            ])
        if self.NTDDI_VERSION >= sdkddkver.NTDDI_WS03:
            f.extend([
                (PVOID, 'FlsCallback'),
                (LIST_ENTRY, 'FlsListHead'),
                (pint.uint32_t, 'FlsBitmap'),
                (dyn.array(ULONG,4), 'FlsBitmapBits'),
                (ULONG, 'FlsHighIndex'),
            ])
        if self.NTDDI_VERSION >= sdkddkver.NTDDI_LONGHORN:
            f.extend([
                (PVOID, 'WerRegistrationData'),
                (PVOID, 'WerShipAssertPtr'),

                (PVOID, 'pContextData'),
                (PVOID, 'pImageHeaderHash'),

## not sure what this means...
#   +0x240 TracingFlags     : 0
#   +0x240 HeapTracingEnabled : 0y0
#   +0x240 CritSecTracingEnabled : 0y0
#   +0x240 SpareTracingBits : 0y000000000000000000000000000000 (0)
            ])
        return

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

    import ptypes,pstypes

    Peb = pstypes.PEB()
    Peb.setoffset(pebaddress)
    Peb.load()

    Ldr = Peb['Ldr'].d.l
    for x in Ldr['InLoadOrderModuleList'].walk():
        print x['BaseDllName'].get(),x['FullDllName'].get()
        print hex(int(x['DllBase'])), hex(int(x['SizeOfImage']))
