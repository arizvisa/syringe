#!/usr/bin/env python
import itertools,logging,argparse
import pecoff,ptypes
ptypes.config.defaults.ptype.clone_name = '{}'
ptypes.config.defaults.pint.bigendian_name = 'be({})'
ptypes.config.defaults.pint.littleendian_name = '{}'

def extract(obj, out):
    if out == 'print':
        res = obj.repr()
    elif out == 'hex':
        res = obj.hexdump()
    elif out == 'raw':
        res = obj.serialize()
    elif len(out) > 0:
        res = resolve(obj, out[0].split(':'))
    else:
        raise Exception, out
    print >>sys.stdout, res

def resolve(result, path):
    for p in path:
        if p == '':
            break
        if p == '.':
            continue
        if p == '..':
            result = result.p
            continue
        if hasattr(result, 'keys'):
            result = result.__getitem__(p)
            continue
        result = result.__getitem__(int(p))
    if not p:
        return result.details()
    if hasattr(result, 'num'):
        return result.num()
    if hasattr(result, 'str'):
        return result.str()
    return result.details()

## commands
def dump_exe(t, output):
    global result; result = t
    if not output or output == 'print':
        print >>sys.stdout, t['Dos'].repr()
        print >>sys.stdout, t['Stub'].hexdump()
        return
    _ = ptypes.dyn.block(t['Dos'].size()+t['Stub'].size())
    return extract(_(offset=0).l, output)

def dump_header(t, output):
    t = t['Next']['Header']
    global result; result = t
    if not output:
        print >>sys.stdout, t.p['Signature'], repr(t.p['Signature'].serialize()+t['SignaturePadding'].serialize())
        print >>sys.stdout, t['FileHeader'].repr()
        print >>sys.stdout, t['OptionalHeader'].repr()
        return
    return extract(t, output)

def list_sections(t, output):
    t = t['Next']['Header']
    global result; result = t['Sections']
    if not output:
        summary = lambda n: '{!r} 0x{:x}:+0x{:x}'.format(n['Name'].str(), n['VirtualAddress'].num(), n['VirtualSize'].num())
        for i,n in enumerate(t['Sections']): print >>sys.stdout, '[{:d}] {}'.format(i, summary(n))
        return
    return extract(t['Sections'], output)

def extract_section(t, index, output):
    t = t['Next']['Header']
    assert 0 <= index < len(t['Sections']), 'Invalid section number'
    t = t['Sections'][index]
    global result; result = t
    #if 'load' in kwds:
    #    return extract(t['VirtualAddress'].d.l, output or 'raw')
    return extract(t['PointerToRawData'].d.l, output or 'raw')

def list_entries(t, output):
    t = t['Next']['Header']
    global result; result = t['DataDirectory']
    summary = lambda n: '{:s} 0x{:x}:+0x{:x}'.format(n.classname(), n['Address'].num(), n['Size'].num())
    if not output:
        for i,n in enumerate(t['DataDirectory']): print >>sys.stdout, '[{:d}] {}'.format(i, summary(n))
        return
    return extract(t['DataDirectory'], output)

def extract_entry(t, index, output):
    t = t['Next']['Header']['DataDirectory']
    assert 0 <= index < len(t), 'Invalid DataDirectory number'
    t = t[index]
    global result; result = t['Address'].d.l
    t,s = t['Address'],t['Size']
    if output == 'print':
        return extract(t.d.l, 'print')
    res = ptypes.dyn.block(s.num())(offset=t.d.getoffset())
    return extract(res.l, output or 'raw')

def list_exports(t, output):
    t = t['Next']['Header']['DataDirectory'][0]
    assert t['Address'].num() != 0, 'Invalid Exports directory'
    t = t['Address'].d.l
    global result; result = t
    if not output:
        name = t['Name'].d.l.str()
        for ofs,ordinal,name,ordinalstring,value in t.iterate():
            print >>sys.stdout, '[{:d}] {!r} {!r} 0x{:x}'.format(ordinal, name, ordinalstring, value)
        return
    return extract(t, output)

def list_imports(t, output):
    t = t['Next']['Header']['DataDirectory'][1]
    assert t['Address'].num() != 0, 'Invalid Imports directory'
    t = t['Address'].d.l
    global result; result = t
    if not output:
        for i,n in enumerate(t.iterate()):
            print >>sys.stdout, '[{:d}] {!r}'.format(i, n['Name'].d.l.str())
        return
    return extract(t, output)

def extract_import(t, index, output):
    t = t['Next']['Header']['DataDirectory'][1]
    assert t['Address'].num() != 0, 'Invalid Imports directory'
    t = t['Address'].d.l
    assert 0 <= index < len(t), 'Invalid Import index'
    t = t[index]
    global result; result = t
    if not output:
        summary = lambda (h,n,a): '{:d} {:s} 0x{:x}'.format(h,n,a)
        for n in t.iterate(): print >>sys.stdout, summary(n)
        return
    return extract(t, output)

def list_resources(t, output):
    t = t['Next']['Header']['DataDirectory'][2]
    assert t['Address'].num() != 0, 'Invalid Resource directory'
    t = t['Address'].d.l
    global result; result = t
    summary = lambda n: '0x{:x}:+0x{:x} {:d}'.format(n['Data'].num(), n['Size'].num(), n['Codepage'].num())
    if not output:
        res = collectresources(t)
        for p in dumpresources(res):
            print >>sys.stdout, '/'.join(map(str,p)), summary(followresource(p, t))
        return
    return extract(t, output)

def extract_resource(t, path, output):
    t = t['Next']['Header']['DataDirectory'][2]
    assert t['Address'].num() != 0, 'Invalid Resource directory'
    t = t['Address'].d.l
    p = map(int,path.split('/'))
    t = followresource(p, t)
    global result; result = t['Data'].d.l
    if output == 'print':
        return extract(t, 'print')
    return extract(t['Data'].d.l, output or 'raw')

def dump_loadconfig(t, output):
    t = t['Next']['Header']['DataDirectory'][10]
    assert t['Address'].num() != 0, 'Invalid LoadConfig directory'
    t = t['Address'].d.l
    global result; result = t
    return extract(t, output or 'print')

def args():
    p = argparse.ArgumentParser(prog="pe.py", description='Display some information about a portable executable file', add_help=True)
    p.add_argument('infile', type=argparse.FileType('rb'), help='a portable executable file')
    res = p.add_mutually_exclusive_group()
    res.add_argument('-m','--dump-exe', action='store_const', const=dump_exe, dest='command', help='display the MZ executable header')
    res.add_argument('-p','--dump-header', action='store_const', const=dump_header, dest='command', help='display the PE header')
    res.add_argument('-s','--list-sections', action='store_const', const=list_sections, dest='command', help='list all the available sections')
    res.add_argument('-S','--extract-section', action='store', nargs=1, type=int, dest='xsection', metavar='index', help='extract the specified section to stdout')
    res.add_argument('-d','--list-entry', action='store_const', const=list_entries, dest='command', help='list all the data directory entries')
    res.add_argument('-D','--extract-entry', action='store', nargs=1, type=int, dest='xentry', metavar='index', help='dump the contents of the datadirectory entry to stdout')
    res.add_argument('-e','--list-exports', action='store_const', const=list_exports, dest='command', help='display the contents of the export directory')
    res.add_argument('-i','--list-imports', action='store_const', const=list_imports, dest='command', help='list all the libraries listed in the import directory')
    res.add_argument('-I','--dump-import', action='store', nargs=1, type=int, dest='ximport', metavar='index', help='list all the imported functions from the specified library')
    res.add_argument('-r','--list-resource', action='store_const', const=list_resources, dest='command', help='display the resource directory tree')
    res.add_argument('-R','--dump-resource', action='store', nargs=1, type=str, dest='xresource', metavar='path', help='dump the resource with the specified path')
    res.add_argument('-l','--dump-loaderconfig', action='store_const', const=dump_loadconfig, dest='command', help='dump the LoadConfig directory entry')

    res = p.add_mutually_exclusive_group(required=False)
    res.add_argument('--raw', action='store_const', dest='output', const='raw', help='output contents in raw mode')
    res.add_argument('--print', action='store_const', dest='output', const='print', help='output contents in a readable format')
    res.add_argument('--hex', action='store_const', dest='output', const='hex', help='output contents as a hex dump')
    res.add_argument('--path', action='store', nargs=1, dest='output', help='output the field specifed by a \':\' separated path.')
    p.set_defaults(output='')
    return p

def figureargs(ns):
    if ns.command:
        return ns.command
    if ns.xsection:
        return lambda t,output: extract_section(t, ns.xsection[0], output)
    if ns.xentry:
        return lambda t,output: extract_entry(t, ns.xentry[0], output)
    if ns.ximport:
        return lambda t,output: extract_import(t, ns.ximport[0], output)
    if ns.xresource:
        return lambda t,output: extract_resource(t, ns.xresource[0], output)
    return None

def collectresources(entry):
    res = {}
    for n in entry.list():
        child = entry.getEntry(n).l
        res[n] = collectresources(child) if hasattr(child, 'list') else child
    return res

def dumpresources(r):
    for n in sorted(r.keys()):
        if type(r[n]) is dict:
            for p in dumpresources(r[n]):
                yield (n,) + p
        else:
            yield n,
        continue
    return

def followresource(p, res):
    if len(p) > 0:
        p,rest = unpack(*p)
        return followresource(rest, res.getEntry(p).l)
    return res.l

def unpack(first,*rest):
    return first,rest

if __name__ == '__main__':
    import sys,logging
    import ptypes,pecoff

    _ = args()
    res = _.parse_args()
    if figureargs(res) is None:
        _.print_usage()
        sys.exit(1)

    ptypes.setsource( ptypes.prov.filebase(res.infile) )
    z = pecoff.Executable.File()
    z = z.l

    result = None
    figureargs(res)(z, output=res.output)
    globals().pop('res')

