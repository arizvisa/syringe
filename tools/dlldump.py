import itertools,logging,argparse,os
import ptypes,pecoff,ndk
import ctypes

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
    raise OSError, "Unable to find {} in PATH".format(filename)
def modulename(filename):
    # convert filename into a windbg style module name
    return filename.rsplit('.',1)[0].upper()

def iterate_imports(filename):
    z = pecoff.Executable.open(filename, mode='r')
    importsDirectory = z['Pe']['DataDirectory'][1]
    if importsDirectory['Address'].num() == 0:
        raise ValueError, "No imports found in {}".format(filename)
    for imp in importsDirectory['Address'].d.l[:-1]:
        yield imp['Name'].d.l.str()
    return
def iterate_loader(pid):
    try:
        pebaddr = getProcessEnvironmentBlock(pid)
    except Exception, e:
        raise OSError, 'Unable to open process id %x (%s)'% (pid, repr(e))
    z = ndk.PEB(source=ptypes.prov.WindowsProcessId(pid), offset=pebaddr)
    for module in z.l['Ldr'].d.l.walk():
        yield module
    return

def getProcessEnvironmentBlock(pid):
    k32 = ctypes.WinDLL('kernel32.dll')
    handle = k32.OpenProcess(0x0400, False, pid) 
    if handle == 0:
        raise OSError, 'Unable to OpenProcess(0x400, 0, %x)'% pid
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
        print >>sys.stderr, 'Unable to CloseHandle(%x)'%(handle)
    if res != 0:
        raise OSError, "NtQueryInformationProcess failed to get ProcessBasicInformation (%x)"% (0x100000000+res)
    return pbi.PebBaseAddress

def walk_executable(filename):
    for f in iterate_imports(filename):
        p = searchpath(f)
        try:
            executable = pecoff.Executable.open(p, mode='r')
        except ptypes.error.Base, e:
            print 'Unable to load %s'% p
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
        print '\n'.join(filenames)
        sys.exit(0)

    # dump module information
    if opts.file:
        everything = walk_executable(opts.file)
    if opts.pid:
        everything = walk_process(opts.pid)

    def out(v):
        if v is None: return '?'
        if type(v) is bool: return 'Y' if v else 'N'
        if type(v) in (int,long): return '%08x'% v
        return str(v)

    filenamelength = max(map(len,filter(lambda x:'-' not in x,filenames)))
    columns=('imagebase', 'realbase', 'isdll?', 'seh?', 'nx?', 'aslr?', 'safeseh')
    print 'filename'.ljust(filenamelength), '\t'.join(columns)
    for shortname,fullname,module in everything:
        try:
            module.l
        except ptypes.error.Base, e:
            print "Unable to parse %s (%s)"% (fullname if opts.full else shortname, type(e).__name__)
            continue
        characteristics = module['Pe']['Header']['Characteristics']
        dllcharacteristics = module['Pe']['OptionalHeader']['DllCharacteristics']
        loadconfig = module['Pe']['DataDirectory'][0xa]

        result = []
        result.append(module['Pe']['OptionalHeader']['ImageBase'].num())
        result.append(module.getoffset())
        result.append(bool(characteristics['DLL']))
        result.append(not bool(dllcharacteristics['NO_SEH']))
        result.append(bool(dllcharacteristics['NX_COMPAT']))
        result.append(bool(dllcharacteristics['DYNAMIC_BASE']))
        if loadconfig['Address'].num() == 0:
            result.extend((None,)* (len(columns)-len(result)))
        else:
            try:
                l = loadconfig['Address'].d.l
                #result.append(l['GlobalFlagsClear'].num())
                #result.append(l['GlobalFlagsSet'].num())
                #result.append(l['ProcessHeapFlags'].num())
                #result.append(l['SecurityCookie'].d.l.num())
                result.append(l['SEHandlerTable'].num() != 0)
            except (ptypes.error.InitializationError,ptypes.error.LoadError), e:
                error = loadconfig
                result.extend((None,)* (len(columns)-len(result)))

        name = fullname if opts.full else shortname
        print name.ljust(filenamelength), '\t'.join(map(out,result))
    sys.exit(0)

