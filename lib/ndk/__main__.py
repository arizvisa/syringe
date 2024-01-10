import ptypes, ndk, pecoff
import ctypes, ctypes.wintypes, contextlib

try:
    K32 = ctypes.WinDLL('kernel32.dll')
except Exception:
    raise OSError
else:
    K32.DebugBreak.argtypes = []
    K32.DebugBreak.restypes = None
    K32.GetLastError.argtypes = []
    K32.GetLastError.restype = ctypes.wintypes.DWORD
    K32.GetCurrentProcess.argtypes = []
    K32.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    K32.GetCurrentProcessId.argtypes = []
    K32.GetCurrentProcessId.restype = ctypes.wintypes.DWORD
    K32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
    K32.OpenProcess.restype = ctypes.wintypes.HANDLE
    K32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
    K32.CloseHandle.restype = ctypes.wintypes.BOOL
    K32.GetProcessInformation.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.wintypes.LPVOID, ctypes.wintypes.DWORD ]
    K32.GetProcessInformation.restype = ctypes.wintypes.BOOL
    K32.IsWow64Process.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.BOOL)]
    K32.IsWow64Process.restype = ctypes.wintypes.BOOL

try:
    NT = ctypes.WinDLL('ntdll.dll')
except Exception:
    raise OSError
else:
    ctypes.wintypes.PVOID, ctypes.wintypes.NTSTATUS = ctypes.wintypes.LPVOID, ctypes.c_size_t
    NT.NtQueryInformationProcess.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.wintypes.PVOID, ctypes.wintypes.ULONG, ctypes.wintypes.PULONG ]
    NT.NtQueryInformationProcess.restype = ctypes.wintypes.NTSTATUS

# FIXME: this is terrible design that was repurposed from some pretty ancient code.
class MemoryReference(ptypes.provider.memoryview):
    def __init__(self, instance, **attributes):
        if ptypes.isinstance(instance):
            object = instance
            object.source = self
        else:
            object = instance(source=self, **attributes).a

        # XXX: not sure why i'm instantiating a type and keeping it around. this is
        #      supposed to be a provider or something, and shouldn't keep any state.

        self._instance = object
        reference = bytearray(object.serialize() if object.initializedQ() else object.blocksize() * b'\0')
        buffer_t = ctypes.c_byte * len(reference)
        buffer = buffer_t(*reference)

        address, length = ctypes.addressof(buffer), ctypes.sizeof(buffer)
        super(MemoryReference, self).__init__(buffer)

        self.__boundaries = address, length
        self.__buffer = buffer
        object.setoffset(address, recurse=True)

    @property
    def instance(self):
        return self._instance

    def seek(self, offset):
        address, _ = self.__boundaries
        realoffset = offset - address
        return super(MemoryReference, self).seek(realoffset)

    def store(self, data):
        address, length = self.__boundaries
        offset, buffer = self.offset, self.__buffer
        left, right = offset, min(offset + len(data), length)
        buffer[left : right] = bytearray(data)[0 : right - left]

    @property
    def address(self):
        address, length = self.__boundaries
        return address

    def size(self):
        address, result = self.__boundaries
        return result

    def __enter__(self):
        '''Enter a block that returns a reference to the instance and loads its contents upon completion.'''
        instance = self._instance
        address, _ = self.__boundaries
        instance.setoffset(address)
        return instance

    def __exit__(self, etype, evalue, etb):
        instance = self._instance
        if evalue is None:
            return instance.l
        raise evalue

    @property
    @contextlib.contextmanager
    def modify(self):
        '''Enter a block that allows the user to modify the current instance and commit its changes upon completion.'''
        instance = self._instance
        address, _ = self.__boundaries
        self._instance.setoffset(address)

        try:
            yield instance
        finally:
            result = instance.c
        return result

class WindowsError(OSError):
    def __init__(self):
        code, string = ptypes.provider.win32error.getLastErrorTuple()
        super(WindowsError, self).__init__(code, string)

class missing_datadirectory_entry(pecoff.portable.headers.IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(pecoff.headers.virtualaddress)

if __name__ == '__main__':
    import sys, os
    pid = int(sys.argv[1]) if len(sys.argv) == 2 else os.getpid()

    handle = K32.OpenProcess(0x30 | 0x400, False, pid)

    _WIN64 = ctypes.wintypes.BOOL(1)
    if not K32.IsWow64Process(handle, ctypes.pointer(_WIN64)):
        raise WindowsError('unable due determine the address type for the given process', pid)
    WIN64 = True if _WIN64.value else False

    with MemoryReference(ndk.pstypes.ProcessInfoClass.lookup('ProcessBasicInformation'), WIN64=WIN64) as pbi:
        res = ctypes.wintypes.ULONG(0)
        status = NT.NtQueryInformationProcess(handle, pbi.type, pbi.getoffset(), pbi.size(), ctypes.pointer(res))
        if status != ndk.NTSTATUS.byname('STATUS_SUCCESS'):
            raise WindowsError(status)
        elif res.value != pbi.size():
            raise ValueError('unexpected size', res.value, pbi.size())

    source = ptypes.setsource(ptypes.prov.memory() if os.getpid() == pid else ptypes.prov.WindowsProcessHandle(handle))
    peb = ndk.pstypes.PEB(offset = pbi['PebBaseAddress'].int(), WIN64=WIN64)
    peb = peb.l

    ldr = peb['Ldr'].d
    ldr = ldr.l
    for mod in ldr['InLoadOrderModuleList'].walk():
        mz = mod['DllBase'].d
        print("{:#x}{:+#x} : {:s} : {:s}".format(mod['DllBase'], mod['SizeOfImage'], mod['BaseDllName'].str(), mod['FullDllName'].str()))
        mz = mz.l
        pe = mz['Next']
        datadirectory = pe['Header']['DataDirectory']
        pdebug = datadirectory['Debug']['Address'] if 6 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        ploader = datadirectory['LoaderConfig']['Address'] if 10 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        pcom = datadirectory['COM']['Address'] if 15 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        print("Entry: {:s} -> *{:#x}".format(mz.instance(), mod['EntryPoint'].int()))
        print("Characteristics: {}".format(pe['Header']['FileHeader']['Characteristics'].summary()))
        print("DllCharacteristics: {}".format(pe['Header']['OptionalHeader']['DllCharacteristics'].summary()))
        if ploader.int(): print("GuardFlags: {}".format(ploader.d.li['GuardFlags'].summary()))
        if ploader.int(): print("SecurityCookie: {}".format(ploader.d.li['SecurityCookie'].summary()))
        if ploader.int(): print("SafeSEH: {:b}".format(True if ploader.d.li['SEHandlerTable'].int() and ploader.d.li['SEHandlerCount'].int() else False))
        if pdebug.int() and any(entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int() for entry in pdebug.d.li):
            entry = next(entry for entry in pdebug.d.li if entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int())
            print("{}".format(entry['AddressOfRawData'].d.li.summary()))
        print()

    K32.CloseHandle(handle)
