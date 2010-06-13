from WinNT import *
from ptypes import *
from umtypes import *
from ldrtypes import *
import heaptypes

#NTDDI_VERSION = 0

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

    _fields_ = [
        (UCHAR, 'InheritedAddressSpace'),
        (UCHAR, 'ReadImageFileExecOptions'),
        (UCHAR, 'BeingDebugged'),
        (BitField, 'BitField'),
        (HANDLE, 'Mutant'),
        (PVOID, 'ImageBaseAddress'),
        (PPEB_LDR_DATA, 'Ldr'),
        ##
        (PVOID, 'ProcessParameters'),
        (pint.uint32_t, 'SubSystemData'),
        (dyn.pointer(heaptypes.HEAP), 'ProcessHeap'),
        (pint.uint32_t, 'FastPebLock'),
        (pint.uint32_t, 'FastPebLockRoutine'),
        (pint.uint32_t, 'FastPebUnlockRoutine'),
        (pint.uint32_t, 'EnvironmentUpdateCount'),
        (pint.uint32_t, 'KernelCallbackTable'),
        (pint.uint32_t, 'EventLogSection'),
        (pint.uint32_t, 'EventLog'),
        (pint.uint32_t, 'FreeList'),
        (pint.uint32_t, 'TlxExpansionCounter'),
        (pint.uint32_t, 'TlsBitmap')
    ]

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

    import sys
    sys.path.append('f:/work')

    import pstypes

    Peb = pstypes.PEB()
    Peb.setoffset(pebaddress)
    Peb.load()

    Ldr = Peb['Ldr'].get().load()
    for x in Ldr['InLoadOrderModuleList'].walk():
        print x['BaseDllName'].get(),x['FullDllName'].get()
        print hex(int(x['DllBase'])), hex(int(x['SizeOfImage']))
