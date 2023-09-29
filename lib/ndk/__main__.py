import ptypes, ndk
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
    K32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
    K32.OpenProcess.restype = ctypes.c_size_t
    K32.CloseHandle.argtypes = [ctypes.c_size_t]
    K32.CloseHandle.restype = ctypes.c_bool
    K32.GetProcessInformation.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.c_void_p, ctypes.wintypes.DWORD ]
    K32.GetProcessInformation.restype = ctypes.wintypes.BOOL

try:
    NT = ctypes.WinDLL('ntdll.dll')
except Exception:
    raise OSError
else:
    NT.NtQueryInformationProcess.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.c_void_p, ctypes.wintypes.ULONG, ctypes.wintypes.PULONG ]
    NT.NtQueryInformationProcess.restype = ctypes.c_size_t

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

if __name__ == '__main__':
    import sys, os
    pid = int(sys.argv[1]) if len(sys.argv) == 2 else os.getpid()

    handle = K32.OpenProcess(0x30 | 0x400, False, pid)

    with MemoryReference(ndk.pstypes.ProcessInfoClass.lookup('ProcessBasicInformation'), WIN64=1) as pbi:
        res = ctypes.wintypes.ULONG(0)
        status = NT.NtQueryInformationProcess(handle, pbi.type, pbi.getoffset(), pbi.size(), ctypes.pointer(res))
        if status != ndk.NTSTATUS.byname('STATUS_SUCCESS'):
            raise WindowsError()
        elif res.value != pbi.size():
            raise ValueError('unexpected size', res.value, pbi.size())

    source = ptypes.setsource(ptypes.prov.memory() if os.getpid() == pid else ptypes.prov.WindowsProcessHandle(handle))
    peb = ndk.pstypes.PEB(offset = pbi['PebBaseAddress'].int())
    peb = peb.l

    ldr = peb['Ldr'].d
    ldr = ldr.l
    for mod in ldr['InLoadOrderModuleList'].walk():
        pe = mod['DllBase'].d
        print("{:#x}{:+#x} : {:s} : {:s}".format(mod['DllBase'], mod['SizeOfImage'], mod['BaseDllName'].str(), mod['FullDllName'].str()))
        pe = pe.l
        print("{:s} -> *{:#x}".format(pe.instance(), mod['EntryPoint'].int()))
        print(pe['Next']['Header']['FileHeader']['Characteristics'].summary())
        print(pe['Next']['Header']['OptionalHeader']['DllCharacteristics'].summary())
        print()

    K32.CloseHandle(handle)
