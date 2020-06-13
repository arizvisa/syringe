import itertools, logging, argparse, os
import ptypes, pecoff, ndk
import six, ctypes

class PROCESS_(ptypes.pbinary.flags):
    _fields_ = [
        (3, 'UNUSED'),
        (1, 'QUERY_LIMITED_INFORMATION'),
        (1, 'SUSPEND_RESUME'),
        (1, 'QUERY_INFORMATION'),
        (1, 'SET_INFORMATION'),
        (1, 'SET_QUOTA'),
        (1, 'CREATE_PROCESS'),
        (1, 'DUP_HANDLE'),
        (1, 'VM_WRITE'),
        (1, 'VM_READ'),
        (1, 'VM_OPERATION'),
        (1, 'RESERVED'),
        (1, 'CREATE_THREAD'),
        (1, 'TERMINATE'),
    ]

class ProcessAccessMask(ndk.setypes.ACCESS_MASK):
    def _SPECIFIC_RIGHTS(self):
        return PROCESS_

class TOKEN_(ptypes.pbinary.flags):
    _fields_ = [
        (7, 'RESERVED'),
        (1, 'ADJUST_SESSIONID'),
        (1, 'ADJUST_DEFAULT'),
        (1, 'ADJUST_GROUPS'),
        (1, 'ADJUST_PRIVILEGES'),
        (1, 'QUERY_SOURCE'),
        (1, 'QUERY'),
        (1, 'IMPERSONATE'),
        (1, 'DUPLICATE'),
        (1, 'ASSIGN_PRIMARY'),
    ]

class TokenAccessMask(ndk.setypes.ACCESS_MASK):
    def _SPECIFIC_RIGHTS(self):
        return TOKEN_

def kernel32_OpenProcess(dwDesiredAccess, bInheritHandle, dwProcessId):
    k32 = ctypes.WinDLL('kernel32.dll')
    if not isinstance(dwDesiredAccess, ProcessAccessMask):
        raise TypeError(TokenHandle)
    k32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
    k32.OpenProcess.restype = ctypes.c_size_t
    res = k32.OpenProcess(dwDesiredAccess.int(), bInheritHandle, dwProcessId or os.getpid())
    if not res:
        raise RuntimeError(k32.GetLastError())
    return ndk.HANDLE().a.set(res)

def kernel32_GetCurrentProcess():
    k32 = ctypes.WinDLL('kernel32.dll')
    k32.GetCurrentProcess.restype = ctypes.c_size_t
    res = k32.GetCurrentProcess()
    return ndk.HANDLE().a.set(res)

def kernel32_CloseHandle(hObject):
    k32 = ctypes.WinDLL('kernel32.dll')
    k32.CloseHandle.argtypes = [ctypes.c_size_t]
    k32.CloseHandle.restype = ctypes.c_bool
    res = k32.CloseHandle(hObject if isinstance(hObject, six.integer_types) else hObject.int())
    if not res:
        raise RuntimeError(k32.GetLastError())
    return res

def kernel32_OpenProcessToken(ProcessHandle, DesiredAccess, TokenHandle):
    k32 = ctypes.WinDLL('kernel32.dll')
    if not isinstance(DesiredAccess, TokenAccessMask):
        raise TypeError(TokenHandle)
    if not isinstance(TokenHandle, ndk.HANDLE) or TokenHandle.size() not in {4, 8}:
        raise TypeError(TokenHandle)

    data = (ctypes.c_ubyte * TokenHandle.size())(*bytearray(TokenHandle.serialize()))
    tokenHandle_t = ctypes.POINTER(ctypes.c_size_t)
    tokenHandle = ctypes.cast(ctypes.pointer(data), tokenHandle_t)

    k32.OpenProcessToken.argtypes = [ctypes.c_size_t, ctypes.c_uint32, tokenHandle_t]
    k32.OpenProcessToken.restype = ctypes.c_bool
    res = k32.OpenProcessToken(ProcessHandle if isinstance(ProcessHandle, six.integer_types) else ProcessHandle.int(), DesiredAccess.int(), tokenHandle)
    if not res:
        raise RuntimeError(k32.GetLastError())

    view = memoryview(tokenHandle.contents)
    return TokenHandle.load(source=ptypes.prov.bytes(view.tobytes()))

def advapi32_LookupPrivilegeValue(lpSystemName, lpName, lpLuid):
    k32, a32 = (ctypes.WinDLL(library) for library in ['kernel32.dll', 'advapi32.dll'])
    if not isinstance(lpLuid, ndk.setypes.LUID):
        raise TypeError(lpLuid)

    class LUID(ctypes.Structure):
        _fields_ = [
            ('LowPart', ctypes.c_uint32),
            ('HighPart', ctypes.c_long),
        ]

    luid = LUID()

    a32.LookupPrivilegeValueA.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(LUID)]
    a32.LookupPrivilegeValueA.restype = ctypes.c_bool
    res = a32.LookupPrivilegeValueA(lpSystemName, lpName, ctypes.pointer(luid))
    if not res:
        raise RuntimeError(k32.GetLastError())
    view = memoryview(luid)
    return lpLuid.load(source=ptypes.prov.bytes(view.tobytes()))

def advapi32_AdjustTokenPrivileges(TokenHandle, DisableAllPrivileges, NewState, PreviousState, ReturnLength):
    k32, a32 = (ctypes.WinDLL(library) for library in ['kernel32.dll', 'advapi32.dll'])

    if not isinstance(NewState, ndk.setypes.TOKEN_PRIVILEGES):
        raise TypeError(NewState)
    if not isinstance(PreviousState, (ndk.setypes.TOKEN_PRIVILEGES, type(None))):
        raise TypeError(PreviousState)
    if not isinstance(ReturnLength, (ndk.DWORD, type(None))):
        raise TypeError(ReturnLength)

    class LUID(ctypes.Structure):
        _fields_ = [('LowPart', ctypes.c_uint32), ('HighPart', ctypes.c_long)]

    class LUID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [('Luid', LUID), ('Attributes', ctypes.c_ulong)]

    def token_privileges_t(count):
        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [('PrivilegeCount', ctypes.c_uint32), ('Privileges', LUID_AND_ATTRIBUTES * count)]
        return TOKEN_PRIVILEGES

    data = (ctypes.c_ubyte * NewState.size())(*bytearray(NewState.serialize()))
    newState_t = ctypes.POINTER(token_privileges_t(len(NewState['Privileges'])))
    newState = ctypes.cast(ctypes.pointer(data), newState_t)

    if PreviousState:
        data = (ctypes.c_ubyte * PreviousState.size())(*bytearray(PreviousState.serialize()))
        previousState_t = ctypes.POINTER(token_privileges_t(len(PreviousState['Privileges'])))
        previousState = ctypes.cast(ctypes.pointer(data), previousState_t)
    else:
        previousState = None

    bufferLength = ctypes.sizeof(previousState.contents) if previousState else 0

    if ReturnLength:
        data = (ctypes.c_ubyte * ReturnLength.size())(*bytearray(ReturnLength.serialize()))
        returnLength_t = ctypes.POINTER(c_uint32_t)
        returnLength = ctypes.cast(data, ctypes.POINTER(ctypes.c_uint32))
    else:
        returnLength = None

    a32.AdjustTokenPrivileges.argtypes = [ctypes.c_size_t, ctypes.c_bool, newState_t, ctypes.c_uint32, oldState_t]
    a32.AdjustTokenPrivileges.restype = ctypes.c_bool
    res = a32.AdjustTokenPrivileges(TokenHandle if isinstance(TokenHandle, six.integer_types) else TokenHandle.int(), DisableAllPrivileges, newState, bufferLength, previousState, returnLength)
    if not res:
        raise RuntimeError(k32.GetLastError())

    if previousState:
        view = memoryview(previousState)
        PreviousState.load(source=ptypes.prov.bytes(view.tobytes()))

    if returnLength:
        view = memoryview(returnLength)
        ReturnLength.load(source=ptypes.prov.bytes(view.tobytes()))

    return returnLength.value if returnLength else 0

def ntdll_NtQueryInformationProcess(ProcessHandle, ProcessInformationClass, ProcessInformation, ReturnLength):
    k32, nt = (ctypes.WinDLL(item) for item in ['kernel32.dll', 'ntdll.dll'])

    if not isinstance(ProcessInformation, (ptypes.ptype.generic, type(None))):
        raise TypeError(ProcessInformation)
    if not isinstance(ReturnLength, (ndk.ULONG, type(None))):
        raise TypeError(ReturnLength)

    fake_processinformation_t = ctypes.c_ubyte * ProcessInformation.size()
    fake_processinformation = fake_processinformation_t(*bytearray(ProcessInformation.serialize()))

    returnLength_t = ctypes.POINTER(ctypes.c_ulong)
    if ReturnLength:
        data = (ctypes.c_ubyte * ReturnLength.size())(*bytearray(ReturnLength.serialize()))
        returnLength = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))
    else:
        returnLength = None

    nt.NtQueryInformationProcess.argtypes = [ctypes.c_size_t, ctypes.c_uint32, ctypes.POINTER(fake_processinformation_t), ctypes.c_ulong, returnLength_t]
    nt.NtQueryInformationProcess.restype = ctypes.c_uint32
    res = nt.NtQueryInformationProcess(ProcessHandle if isinstance(ProcessHandle, six.integer_types) else ProcessHandle.int(), ProcessInformationClass, ctypes.pointer(fake_processinformation), ctypes.sizeof(fake_processinformation), returnLength)
    if res:
        raise RuntimeError(res)

    if returnLength:
        view = memoryview(returnLength)
        ReturnLength.load(source=ptypes.prov.bytes(view.tobytes()))

    view = memoryview(fake_processinformation)
    return ProcessInformation.load(source=ptypes.prov.bytes(view.tobytes()))

def searchpath(filename):
    sep = ';' if os.sep == '\\' else ':'
    for p in os.environ['path'].split(sep):
        try:
            files = set(n.lower() for n in os.listdir(p))
        except OSError:
            continue
        if filename.lower() in files:
            return os.sep.join((p,filename))
        continue
    raise OSError("Unable to find {} in PATH".format(filename))

def modulename(filename):
    # convert filename into a windbg style module name
    return filename.rsplit('.',1)[0].upper()

def iterate_imports(filename):
    z = pecoff.Executable.File(source=ptypes.prov.file(filename, mode='r')).l
    importsDirectory = z['Next']['Header']['DataDirectory'][1]
    if importsDirectory['Address'].int() == 0:
        raise ValueError("No imports found in {}".format(filename))
    for imp in importsDirectory['Address'].d.l[:-1]:
        yield imp['Name'].d.l.str()
    return

def iterate_loader(pid):
    pax = ProcessAccessMask().a.set(SPECIFIC_RIGHTS=dict(QUERY_INFORMATION=1, VM_READ=1))
    handle = kernel32_OpenProcess(pax, False, pid)
    wow64 = ntdll_NtQueryInformationProcess(handle, ndk.pstypes.PROCESS_INFORMATION_CLASS.byname('ProcessWow64Information'), ndk.ULONG_PTR().a, None)
    try:
        pebaddr = getProcessEnvironmentBlock(handle, wow64.int())
    except Exception as e:
        raise OSError('Unable to open process id %d (%s)'% (pid, repr(e)))
    z = ndk.pstypes.PEB(source=ptypes.prov.WindowsProcessHandle(handle.int()), offset=pebaddr, WIN64=0 if wow64.int() else 1)
    for module in z.l['Ldr'].d.l.walk():
        yield module
    return

def getProcessEnvironmentBlock(handle, wow64Q):
    pbi = ntdll_NtQueryInformationProcess(handle, ndk.pstypes.PROCESS_INFORMATION_CLASS.byname('ProcessBasicInformation'), ndk.pstypes.PROCESS_BASIC_INFORMATION(WIN64=0 if wow64Q else 1).a, None)
    return pbi['PebBaseAddress'].int()

def walk_executable(filename):
    for f in iterate_imports(filename):
        try: p = searchpath(f)
        except OSError:
            print('Unable to load %s'% f)
            continue
        try:
            executable = pecoff.Executable.File(source=ptypes.prov.file(p, mode='r')).l
        except ptypes.error.Base as e:
            print('Unable to load %s'% p)
            continue
        yield f, searchpath(f), executable
    return
def walk_process(pid):
    for module in iterate_loader(pid):
        yield module['BaseDllName'].str(), module['FullDllName'].str(), module['DllBase'].d
    return

if __name__ == '__main__':
    import sys
    argv = sys.argv
#    argv = []

    # parse commandline args
    parser = argparse.ArgumentParser()
    parser_type = parser.add_mutually_exclusive_group(required=True)
    parser_type.add_argument('-p', '--pid', type=int, help='specify a pid')
    parser_type.add_argument('-f', '--file', type=str, help='specify a filename')
    parser.add_argument('-l', '--list', default=False, action='store_true', help='list just the module filenames')
    parser.add_argument('--full', default=False, action='store_true', help='list the full filenames')
    #parser.add_argument('--dump', type=str, help='dump/copy files to the specified directory')
    opts = parser.parse_args(argv[1:])

    # check args
    if opts.file:
        file(opts.file,'rb').close()
    elif opts.pid:
        pass

    # collect filenames
    if opts.pid:
        filenames = ((m['FullDllName'].str() if opts.full else m['BaseDllName'].str()) for m in iterate_loader(opts.pid))
    elif opts.file:
        filenames = ((searchpath(n) for n in iterate_imports(opts.file)) if opts.full else iterate_imports(opts.file))
    else:
        raise ValueError

    # list filenames
    if opts.list:
        print('\n'.join(filenames))
        sys.exit(0)

    # dump module information
    if opts.file:
        everything = walk_executable(opts.file)
    if opts.pid:
        everything = walk_process(opts.pid)

    def out(v):
        if v is None: return '?'
        if isinstance(v, bool): return 'Y' if v else 'N'
        if isinstance(v, tuple): return "{:0{:d}x}".format(*v)
        return "{!s}".format(v)

    filenamelength = max(map(len,filter(lambda x:'-' not in x,filenames)))
    columns=['imagebase', 'realbase', 'isdll?', 'seh?', 'nx?', 'aslr?', 'safeseh']
    rows = [['filename'] +  columns]
    for shortname,fullname,module in everything:
        try:
            module.l
        except ptypes.error.Base as e:
            print("Unable to parse %s (%s)"% (fullname if opts.full else shortname, type(e).__name__))
            continue
        characteristics = module['Next']['Header']['FileHeader']['Characteristics']
        dllcharacteristics = module['Next']['Header']['OptionalHeader']['DllCharacteristics']
        loadconfig = module['Next']['Header']['DataDirectory'][0xa]

        nibbles = 2 * module['Next']['Header']['OptionalHeader']['ImageBase'].size()
        result = []
        result.append((module['Next']['Header']['OptionalHeader']['ImageBase'].int(), nibbles))
        result.append((module.getoffset(), nibbles))
        result.append(bool(characteristics['DLL']))
        result.append(not bool(dllcharacteristics['NO_SEH']))
        result.append(bool(dllcharacteristics['NX_COMPAT']))
        result.append(bool(dllcharacteristics['DYNAMIC_BASE']))
        if loadconfig['Address'].int() == 0:
            result.extend((None,)* (len(columns)-len(result)))
        else:
            try:
                l = loadconfig['Address'].d.l
                #result.append(l['GlobalFlagsClear'].int())
                #result.append(l['GlobalFlagsSet'].int())
                #result.append(l['ProcessHeapFlags'].int())
                #result.append(l['SecurityCookie'].d.l.int())
                result.append(l['SEHandlerTable'].int() != 0)
            except (ptypes.error.InitializationError,ptypes.error.LoadError) as e:
                error = loadconfig
                result.extend((None,)* (len(columns)-len(result)))

        name = fullname if opts.full else shortname
        rows.append([name] + result)
        six.print_('.', end='')

    six.print_('loaded {:d} modules!'.format(len(rows) - 1))
    unpack = lambda name, base, address, *flags: (name, base, address, flags)
    header = rows.pop(0)
    nibbles = max(item[1][1] for item in rows)
    name, base, address, flags = unpack(*header)
    print("{:<{:d}s} {:>{:d}s}\t{:>{:d}s}\t{:s}".format(name, filenamelength, base, nibbles, address, nibbles, '\t'.join(flags)))
    for item in rows:
        name, cols = (lambda name, *items: (name, items))(*item)
        aligned = [out(c) if i < 3 else "{:{:d}s}".format(out(c), len(header[i])) for i, c in enumerate(cols)]
        print("{:<{:d}s} {:s}".format(name, filenamelength, '\t'.join(aligned)))
    sys.exit(0)

    pax = ProcessAccessMask().a
    pax.set(SPECIFIC_RIGHTS=dict(QUERY_INFORMATION=1))
    pax.set(STANDARD_RIGHTS=dict(WRITE_OWNER=1, WRITE_DAC=1, READ_CONTROL=1, DELETE=1))
    print(pax['STANDARD_RIGHTS'])
    print(pax['SPECIFIC_RIGHTS'])
    pid = 5892
    handle = kernel32_OpenProcess(pax, False, 2172)
