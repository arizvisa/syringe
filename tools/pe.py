#!/usr/bin/env python
import itertools,operator,logging,argparse
import pecoff,ptypes
import six
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
        raise Exception(out)
    six.print_(res, file=sys.stdout)

def resolve(result, path):
    for p in path:
        if p == '':
            break
        elif p == '.':
            pass
        elif p == '..':
            result = result.p
        elif p == '!' and hasattr(result, 'd'):
            result = result.d.li
        elif hasattr(result, 'keys'):
            result = result.__field__(p) if isinstance(result, (ptypes.pbinary.type,ptypes.pbinary.partial)) else operator.getitem(result, p)
        else:
            result = result.__field__(int(p)) if isinstance(result, (ptypes.pbinary.type,ptypes.pbinary.partial)) else operator.getitem(result, int(p))
        continue

    if not p:
        return result.details()
    if not isinstance(result, (ptypes.ptype.pointer_t,ptypes.pbinary.partial)):
        if hasattr(result, 'num'): return result.num()
        if hasattr(result, 'int'): return result.int()
        if hasattr(result, 'str'): return result.str()
    return result.repr()

## commands
def dump_exe(t, output):
    global result; result = t
    if not output or output == 'print':
        six.print_(t['Dos'].repr(), file=sys.stdout)
        six.print_(t['Stub'].hexdump(), file=sys.stdout)
        return
    if isinstance(output, basestring):
        _ = ptypes.dyn.block(t['Dos'].size()+t['Stub'].size())
        return extract(_(offset=0).li, output)
    return extract(t, output)

def dump_header(t, output):
    t = t['Next']['Header']
    global result; result = t
    if not output:
        six.print_(t.p['Signature'], repr(t.p['Signature'].serialize()+t['SignaturePadding'].serialize()), file=sys.stdout)
        six.print_(t['FileHeader'].repr(), file=sys.stdout)
        six.print_(t['OptionalHeader'].repr(), file=sys.stdout)
        return
    return extract(t, output)

def list_sections(t, output):
    t = t['Next']['Header']
    global result; result = t['Sections']
    if not output:
        summary = lambda n: '{!r} {:#x}:{:+#x} Raw:{:#x}:{:+#x}'.format(n['Name'].str(), n['VirtualAddress'].int(), n['VirtualSize'].int(), n['PointerToRawData'].int(), n['SizeOfRawData'].int())
        for i,n in enumerate(t['Sections']): six.print_('[{:d}] {}'.format(i, summary(n)), file=sys.stdout)
        return
    return extract(t['Sections'], output)

def extract_section(t, index, output):
    t = t['Next']['Header']
    if not (0 <= index < len(t['Sections'])):
        raise IndexError("Invalid section index.")
    t = t['Sections'][index]
    global result; result = t
    #if 'load' in kwds:
    #    return extract(t['VirtualAddress'].d.li, output or 'raw')
    return extract(t['PointerToRawData'].d.li, output or 'hex')

def list_entries(t, output):
    t = t['Next']['Header']
    global result; result = t['DataDirectory']
    summary = lambda n: '{:s} {:#x}:{:+#x}'.format(n.classname(), n['Address'].int(), n['Size'].int())
    if not output:
        for i,n in enumerate(t['DataDirectory']): six.print_('[{:d}] {}'.format(i, summary(n)), file=sys.stdout)
        return
    return extract(t['DataDirectory'], output)

def extract_entry(t, index, output):
    t = t['Next']['Header']['DataDirectory']
    if not(0 <= index < len(t)):
        raise IndexError("Invalid DataDirectory entry number.")
    t = t[index]
    global result; result = t['Address'].d.li
    t,s = t['Address'],t['Size']
    if output == 'print' or not isinstance(output, basestring):
        return extract(t.d.li, output)
    res = ptypes.dyn.block(s.int())(offset=t.d.getoffset())
    return extract(res.li, output or 'raw')

def list_exports(t, output):
    t = t['Next']['Header']['DataDirectory'][0]
    if t['Address'].int() == 0:
        raise ValueError("No Exports directory entry.")
    t = t['Address'].d.li
    global result; result = t
    if not output:
        name = t['Name'].d.li.str()
        for ofs,ordinal,name,ordinalstring,value in t.iterate():
            six.print_('[{:d}] {!r} {!r} {:#x}'.format(ordinal, name, ordinalstring, value), file=sys.stdout)
        return
    return extract(t, output)

def list_imports(t, output):
    t = t['Next']['Header']['DataDirectory'][1]
    if t['Address'].int() == 0:
        raise ValueError("No Imports directory entry.")
    t = t['Address'].d.li
    global result; result = t
    if not output:
        for i,n in enumerate(t.iterate()):
            six.print_('[{:d}] {!r}'.format(i, n['Name'].d.li.str()), file=sys.stdout)
        return
    return extract(t, output)

def extract_import(t, index, output):
    t = t['Next']['Header']['DataDirectory'][1]
    if t['Address'].int() == 0:
        raise ValueError("No Imports directory entry.")
    t = t['Address'].d.li
    if not(0 <= index < len(t)):
        raise IndexError("Invalid Imports table index.")
    t = t[index]
    global result; result = t
    if not output:
        summary = lambda (h,n,a): '{:d} {:s} {:#x}'.format(h,n,a)
        for n in t.iterate(): six.print_(summary(n), file=sys.stdout)
        return
    return extract(t, output)

def list_resources(t, output):
    t = t['Next']['Header']['DataDirectory'][2]
    if t['Address'].int() == 0:
        raise ValueError("No Resource directory entry.")
    t = t['Address'].d.li
    global result; result = t
    summary = lambda n: '{:#x}:{:+#x} {:d}'.format(n['Data'].int(), n['Size'].int(), n['Codepage'].int())
    if not output:
        res = collectresources(t)
        for p in dumpresources(res):
            six.print_('/'.join(map(str,p)), summary(followresource(p, t)), file=sys.stdout)
        return
    return extract(t, output)

def extract_resource(t, path, output):
    t = t['Next']['Header']['DataDirectory'][2]
    if t['Address'].int() == 0:
        raise ValueError("No Resource directory entry.")
    t = t['Address'].d.li
    p = []
    for n in path.split('/'):
        try: n = int(n)
        except ValueError: n = str(n)
        p.append(n)
    t = followresource(p, t)
    global result; result = t['Data'].d.li
    if output == 'print':
        return extract(t, 'print')
    return extract(t['Data'].d.li, output or 'raw')

def dump_loadconfig(t, output):
    t = t['Next']['Header']['DataDirectory'][10]
    if t['Address'].int() == 0:
        raise ValueError("No LoadConfig directory entry.")
    t = t['Address'].d.li
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
    for n in entry.List():
        child = entry.Entry(n).li
        res[n] = collectresources(child) if isinstance(child, pecoff.portable.resources.IMAGE_RESOURCE_DIRECTORY) else child
    return res

def dumpresources(r):
    for n in sorted(six.viewkeys(r)):
        if isinstance(r[n], dict):
            for p in dumpresources(r[n]):
                yield (n,) + p
        else:
            yield n,
        continue
    return

def followresource(p, res):
    if len(p) > 0:
        p, rest = unpack(*p)
        return followresource(rest, res.Entry(p).li)
    return res.li

def unpack(first, *rest):
    return first, rest

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

