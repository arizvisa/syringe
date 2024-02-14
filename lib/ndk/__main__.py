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
    K32.GetNativeSystemInfo.argtypes = [ ctypes.wintypes.LPVOID ]
    K32.GetNativeSystemInfo.restype = None
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
    NT.NtQueryInformationThread.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.wintypes.PVOID, ctypes.wintypes.ULONG, ctypes.wintypes.PULONG ]
    NT.NtQueryInformationThread.restype = ctypes.wintypes.NTSTATUS

    try:
        NT.NtWow64QueryInformationProcess64.argtypes = [ ctypes.wintypes.HANDLE, ctypes.c_size_t, ctypes.wintypes.PVOID, ctypes.wintypes.ULONG, ctypes.wintypes.PULONG ]
        NT.NtWow64QueryInformationProcess64.restype = ctypes.wintypes.NTSTATUS
    except AttributeError:
        pass

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
    def __init__(self, *args):
        code, string = ptypes.provider.win32error.getLastErrorTuple()
        super(WindowsError, self).__init__((code, string), args)

class missing_datadirectory_entry(pecoff.portable.headers.IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(pecoff.headers.virtualaddress)

if __name__ == '__main__':
    import sys, os, fnmatch, argparse, itertools

    argh = argparse.ArgumentParser(description='dump the loaded modules for the given process')
    argh.add_argument('-p', '--pid', dest='pid', metavar='PID', type=int, default=os.getpid(), help='target process id')
    argh.add_argument('-w', '--wide', dest='wide', action='store_true', default=False, help='use wide single-line output')
    argh.add_argument('patterns', nargs='*', metavar='PATTERN', help='filter the listed modules using the specified globs (full module path)')
    args = argh.parse_args()

    pid = args.pid
    patterns = args.patterns
    Fmatch = (lambda path: any(fnmatch.fnmatch(path, pattern) for pattern in patterns)) if patterns else (lambda path: True)

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_WRITE = 0x0020
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_OPERATION = 0x0008

    with MemoryReference(ndk.extypes.SYSTEM_INFO) as sbi:
        K32.GetNativeSystemInfo(sbi.getoffset())
    SYS64 = any(sbi['wProcessorArchitecture'][name] for name in {'AMD64', 'IA64', 'ARM64'})

    ME_WOW64_ = ctypes.wintypes.BOOL(-1)
    if not K32.IsWow64Process(K32.GetCurrentProcess(), ctypes.pointer(ME_WOW64_)):
        raise WindowsError('unable to determine the address type for the current process', os.getpid())
    ME_WOW64 = True if ME_WOW64_.value else False
    ME_WIN64 = False if not SYS64 or ME_WOW64 else True

    handle = K32.OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_WRITE|PROCESS_VM_READ|PROCESS_VM_OPERATION, False, pid)
    if not handle:
        raise WindowsError('unable to open process', pid)

    WOW64_ = ctypes.wintypes.BOOL(-1)
    if not K32.IsWow64Process(handle, ctypes.pointer(WOW64_)):
        raise WindowsError('unable to determine the address type for the given process', pid)
    WOW64 = True if WOW64_.value else False
    WIN64 = False if not SYS64 or WOW64 else True

    USE_WOW64 = ME_WOW64 and not WOW64
    PEB64 = True if USE_WOW64 else ME_WIN64

    # FIXME: we should grab the main thread and use the TEB to get the PEB.
    HACK = sbi['dwPageSize'].int() if not ME_WOW64 and WOW64 else 0

    FQueryInformationProcess = NT.NtWow64QueryInformationProcess64 if USE_WOW64 else NT.NtQueryInformationProcess
    with MemoryReference(ndk.pstypes.ProcessInfoClass.lookup('ProcessBasicInformation'), WIN64=PEB64) as pbi:
        res = ctypes.wintypes.ULONG(0)
        status = FQueryInformationProcess(handle, pbi.type, pbi.getoffset(), pbi.size(), ctypes.pointer(res))
        if status != ndk.NTSTATUS.byname('STATUS_SUCCESS'):
            raise WindowsError('unable to query process information', "{:s}({:#0{:d}x})".format(ndk.NTSTATUS.byvalue(status), status, 2 + 8) if ndk.NTSTATUS.has(status) else status)
        elif res.value != pbi.size():
            raise ValueError('unexpected size', res.value, pbi.size())
    K32.CloseHandle(handle)

    source = ptypes.setsource(ptypes.prov.memory() if os.getpid() == pid else ptypes.prov.WindowsProcessId(pid))
    peb = ndk.pstypes.PEB(offset = pbi['PebBaseAddress'].int() + HACK, WIN64=WIN64)
    peb = peb.l

    def get_datadirectory(portable):
        datadirectory = portable['Header']['DataDirectory']
        prelocations = datadirectory['Relocations']['Address'] if 5 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        pexceptions = datadirectory['Exceptions']['Address'] if 3 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        pdebug = datadirectory['Debug']['Address'] if 6 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        ploader = datadirectory['LoaderConfig']['Address'] if 10 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        pcom = datadirectory['COM']['Address'] if 15 < len(datadirectory) else missing_datadirectory_entry().a['Address']
        return pexceptions, prelocations, pdebug, ploader, pcom

    def multiple():
        module = (yield)
        try:
            while True:
                print("{:#x}{:+#x} : {:s} : {:s}".format(module['DllBase'], module['SizeOfImage'], module['BaseDllName'].str(), module['FullDllName'].str()))

                executable = (yield)
                portable = executable['Next']
                exceptions, relocations, debug, loader, com = get_datadirectory(portable)

                print("Entry: {:s} -> *{:#x}".format(executable.instance(), module['EntryPoint'].int()))
                print("HasRelocations: {:b}".format(True if relocations.int() else False))
                print("Characteristics: {}".format(portable['Header']['FileHeader']['Characteristics'].summary()))
                print("DllCharacteristics: {}".format(portable['Header']['OptionalHeader']['DllCharacteristics'].summary()))

                if loader.int(): print("GuardFlags: {}".format(loader.d.li['GuardFlags'].summary()))
                if loader.int(): print("SecurityCookie: {}".format(loader.d.li['SecurityCookie'].summary()))
                if loader.int(): print("SafeSEH: {:b}".format(True if loader.d.li['SEHandlerTable'].int() and loader.d.li['SEHandlerCount'].int() else False))
                if debug.int() and any(entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int() for entry in debug.d.li):
                    entry = next(entry for entry in debug.d.li if entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int())
                    print("{}".format(entry['AddressOfRawData'].d.li.summary()))

                module = (yield)
                print()
        except GeneratorExit:
            pass
        return

    def single():
        '''
        EXE - EXECUTABLE_IMAGE
        DLL - DLL
        SYS - SYSTEM

        File:
            ALARGE - LARGE_ADDRESS_AWARE
            SWAP - REMOVABLE_RUN_FROM_SWAP || NET_RUN_FROM_SWAP
            -RELO - Relocations stripped

        Optional:
            ASLR64 - HIGH_ENTROPY_VA
            DYN - DYNAMIC_BASE
            INT - FORCE_INTEGRITY
            NX - NX_COMPAT
            -SEH - NO_SEH
            +SEH - !NO_SEH
            CFG - GUARD_CF

        GuardFlags:
            -C - SECURITY_COOKIE_UNUSED
            IAT+ - PROTECT_DELAYLOAD_IAT
            -EXP - CF_ENABLE_EXPORT_SUPPRESSION | CF_EXPORT_SUPPRESSION_INFO_PRESENT
            CFI - CF_INSTRUMENTED | CF_FUNCTION_TABLE_PRESENT
            CFW - CFW_INSTRUMENTED | CF_FUNCTION_TABLE_PRESENT
            RET - RETPOLINE_PRESENT && RF_ENABLE
            RET+ - RETPOLINE_PRESENT && RF_STRICT

        Directory:
            R - Relocations
        C - Characterstics
        D - DllCharacteristics
        G - GuardFlags
        SC - SecurityCookie
        SEH - SafeSEH
        EX - ExDllCharacteristics
        COR - DotNET (COR)
        '''
        class stash(object):
            pass

        try:
            while True:
                module = (yield)
                executable = (yield)
                portable = executable['Next']
                exceptions, relocations, debug, loader, com = get_datadirectory(portable)

                # FIXME: This was thrown together and I'm almost 100% sure that none of this is accurate. I seriously
                #        couldn't find a single resource that tells you which fields correlate to which mitigation.
                has_relocations = True if relocations.int() else False
                characteristics = portable['Header']['FileHeader']['Characteristics']
                dll_characteristics = portable['Header']['OptionalHeader']['DllCharacteristics']
                guard_flags = loader.d.li['GuardFlags'] if loader.int() else None
                securty_cookie = loader.d.li['SecurityCookie'] if loader.int() else None
                sehandlertable = loader.d.li['SEHandlerTable'] if loader.int() else None
                sehandlercount = loader.d.li['SEHandlerCount'] if loader.int() else None

                has_ex_dllcharacteristics = debug.int() and any(entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int() for entry in debug.d.li)
                iterable = (entry for entry in debug.d.li if entry['Type']['EX_DLLCHARACTERISTICS'] and entry['AddressOfRawData'].int())
                ex_dllcharacteristics_entry = next(iterable, None) if has_ex_dllcharacteristics else None

                # IMAGE_FILE_HEADER
                file = stash()

                descriptions = {'DLL': 'DLL', 'SYSTEM': 'SYS'}
                file.image_type = sorted({descriptions[name] for name in descriptions if characteristics[name]} or {'EXE'} if characteristics['EXECUTABLE_IMAGE'] else {})

                descriptions = {'LARGE_ADDRESS_AWARE': 'LARGE', 'REMOVABLE_RUN_FROM_SWAP': 'SWAP', 'NET_RUN_FROM_SWAP': 'SWAP', 'RELOCS_STRIPPED': 'RELOSTRIP'}
                file.flags = sorted({descriptions[name] for name in descriptions if characteristics[name]})

                # IMAGE_OPTIONAL_HEADER
                optional = stash()

                descriptions = {'HIGH_ENTROPY_VA': 'ASLR64', 'DYNAMIC_BASE': 'DYN', 'FORCE_INTEGRITY': 'INT', 'NX_COMPAT': 'NX', 'GUARD_CF': 'CF'}
                optional.flags = sorted({descriptions[name] for name in descriptions if dll_characteristics[name]})
                optional.seh = "{:s}SEH".format('-' if dll_characteristics['NO_SEH'] else '+')

                # Directory
                directory = stash()
                directory.relocations = True if relocations.int() else False
                directory.exceptions = True if exceptions.int() else False
                directory.cor = True if com.int() else False

                # GuardFlags
                guard = stash()
                guard.canary = '' if guard_flags is None else '-C' if guard_flags['SECURITY_COOKIE_UNUSED'] else '+C' if loader.d['SecurityCookie'].int() else ''
                guard.seh = 'SEH' if loader.int() and all([loader.d[fld].int() for fld in ['SEHandlerCount', 'SEHandlerTable']]) else ''
                guard.ret = '' if guard_flags is None else '' if not guard_flags['RETPOLINE_PRESENT'] else 'RET+' if guard_flags['RF_ENABLE'] and guard_flags['RF_STRICT'] else 'RET' if guard_flags['RF_ENABLE'] else '' if not guard_flags['RF_ENABLE'] else 'RET?'
                guard.cfg = True if loader.int() and all([loader.d[fld].int() for fld in ['GuardCFCheckFunctionPointer', 'GuardCFDispatchFunctionPointer', 'GuardCFFunctionCount', 'GuardCFFunctionTable']]) else False
                guard.cf = '' if guard_flags is None else '' if not guard_flags['CF_FUNCTION_TABLE_PRESENT'] else 'CFI' if guard_flags['CF_INSTRUMENTED'] else 'CFW' if guard_flags['CFW_INSTRUMENTED'] else ''

                # Loader (FIXME: should probably check XFG and the other stupid shit)
                load = stash()

                print("{:s} : {:#x}{:+#x} : {:s} : File({:s}) Optional({:s}) Directory({:s}) GuardFlags({:s})".format(
                    ','.join(file.image_type),
                    executable.getoffset(), executable.size(), module['BaseDllName'].str(),
                    ','.join(file.flags),
                    ','.join(itertools.chain([optional.seh],optional.flags)),
                    ','.join(["{:s}RELO".format('+' if directory.relocations else '-'), "{:s}EXC".format('+' if directory.exceptions else '-')] + (['COR'] if directory.cor else [])),
                    ','.join(item for item in itertools.chain([guard.canary, guard.seh, guard.ret, 'CFG' if guard.cfg and guard.cf else '']) if item)
                ))

        except GeneratorExit:
            pass
        return

    emitter = single() if args.wide else multiple()
    emitter.send(None)

    ldr = peb['Ldr'].d
    ldr = ldr.l
    for mod in ldr['InLoadOrderModuleList'].walk():
        if not Fmatch(mod['FullDllName'].str()):
            continue
        emitter.send(mod)

        mz = mod['DllBase'].d
        mz = mz.l
        emitter.send(mz)
    emitter.close()
