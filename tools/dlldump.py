import itertools,logging,argparse,os
import ptypes,pecoff,ndk
import six,ctypes

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
    try:
        pebaddr = getProcessEnvironmentBlock(pid)
    except Exception as e:
        raise OSError('Unable to open process id %x (%s)'% (pid, repr(e)))
    z = ndk.PEB(source=ptypes.prov.WindowsProcessId(pid), offset=pebaddr)
    for module in z.l['Ldr'].d.l.walk():
        yield module
    return

def getProcessEnvironmentBlock(pid):
    k32 = ctypes.WinDLL('kernel32.dll')
    handle = k32.OpenProcess(0x0400, False, pid)
    if handle == 0:
        raise OSError('Unable to OpenProcess(0x400, 0, %x)'% pid)
    nt = ctypes.WinDLL('ntdll.dll')
    class ProcessBasicInformation(ctypes.Structure):
        _fields_ = [('Reserved1', ctypes.c_uint32),
                    ('PebBaseAddress', ctypes.c_uint32),
                    ('Reserved2', ctypes.c_uint32 * 2),
                    ('UniqueProcessId', ctypes.c_uint32),
                    ('Reserved3', ctypes.c_uint32)]
    pbi = ProcessBasicInformation()
    res = nt.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
    if k32.CloseHandle(handle) == 0:
        six.print_('Unable to CloseHandle(%x)'%(handle), file=sys.stderr)
    if res != 0:
        raise OSError("NtQueryInformationProcess failed to get ProcessBasicInformation (%x)"% (0x100000000+res))
    return pbi.PebBaseAddress

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

