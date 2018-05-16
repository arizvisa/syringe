#!/usr/bin/env python
import six,argparse
import functools,operator,itertools,types
import ptypes,pecoff,ber
#ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
ptypes.config.defaults.ptype.clone_name = '{}'
ptypes.config.defaults.pint.bigendian_name = 'be({})'
ptypes.config.defaults.pint.littleendian_name = '{}'

def Locate(path, obj):
    return Resolve(obj, path.split(':'))

def Extract(obj, out):
    if out == 'print':
        res = obj.repr()
    elif out == 'hex':
        res = obj.hexdump()
    elif out == 'raw':
        res = obj.serialize()
    elif out == 'list':
        res = '\n'.join((n.summary() if hasattr(n, 'summary') else str(n) for n in obj))

    # default
    elif not obj:
        res = obj.details()
    elif isinstance(obj, (ptypes.ptype.pointer_t, ptypes.pbinary.partial)):
        res = repr(obj)
    elif hasattr(obj, 'num'):
        res = obj.num()
    elif hasattr(obj, 'int'):
        res = obj.int()
    elif hasattr(obj, 'str'):
        res = obj.str()
    else:
        res = repr(obj)
    six.print_(res, file=sys.stdout)

def Resolve(result, path):
    for p in path:
        if p == '':
            break
        elif p == '.':
            pass
        elif p == '..':
            result = result.p
        elif p == '!' and hasattr(result, 'd'):
            result = result.d.li
        elif p == '@' and hasattr(result, 'o'):
            result = result.o.li
        elif hasattr(result, '__field__'):
            result = result.__field__(p) if hasattr(result, '__keys__') else result.__field__(int(p))
        else:
            raise AttributeError(p, result)
        continue
    return result

## commands
def dump_exe(t, output, F=None):
    global result; result = t
    if F:
        return Extract(F(result), output)
    if not output or output in {'print'}:
        six.print_(result['Dos'].repr(), file=sys.stdout)
        six.print_(result['Stub'].hexdump(), file=sys.stdout)
        return
    if output in {'hex','raw'}:
        t = ptypes.dyn.block(result['Dos'].size() + result['Stub'].size())
        return Extract(t(offset=0).li, output)
    return Extract(result, output)

def dump_header(t, output, F=None):
    H = t['Next']['Header']
    global result; result = H
    if F:
        return Extract(F(result), output)
    if not output:
        six.print_(result.p['Signature'], repr(result.p['Signature'].serialize()+result['SignaturePadding'].serialize()), file=sys.stdout)
        six.print_(result['FileHeader'].repr(), file=sys.stdout)
        six.print_(result['OptionalHeader'].repr(), file=sys.stdout)
        return
    return Extract(result, output)

def list_sections(t, output, F=None):
    H = t['Next']['Header']
    global result; result = H['Sections']
    if F:
        return Extract(F(result), output)
    if not output:
        summary = lambda s: '{!r} {:#x}:{:+#x} Raw:{:#x}:{:+#x}'.format(s['Name'].str(), s['VirtualAddress'].int(), s['VirtualSize'].int(), s['PointerToRawData'].int(), s['SizeOfRawData'].int())
        for i, S in enumerate(result):
            six.print_('[{:d}] {:s}'.format(i, summary(S)), file=sys.stdout)
        return
    if output in {'list'}:
        return Extract((S['Name'].str() for S in result), output)
    return Extract(result, output)

def extract_section(t, index, output, F=None):
    H = t['Next']['Header']
    if not (0 <= index < len(H['Sections'])):
        raise IndexError("Invalid section index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(H['Sections'])))
    S = H['Sections'][index]
    global result; result = S
    #if 'load' in kwds:
    #    return Extract(t['VirtualAddress'].d.li, output or 'raw')
    if F:
        return Extract(F(result), output)
    return Extract(result['PointerToRawData'].d.li, output or 'hex')

def list_entries(t, output, F=None):
    H = t['Next']['Header']
    global result; result = H['DataDirectory']
    if F:
        return Extract(F(result), output)
    summary = lambda n: '{:s} {:#x}:{:+#x}'.format(n.classname(), n['Address'].int(), n['Size'].int())
    if not output:
        for i, n in enumerate(result):
            six.print_('[{:d}] {}'.format(i, summary(n)), file=sys.stdout)
        return
    if output in {'list'}:
        return Extract((n.classname() for n in result if n['Address'].int()), output)
    return Extract(result, output)

def extract_entry(t, index, output, F=None):
    d = t['Next']['Header']['DataDirectory']
    if not(0 <= index < len(d)):
        raise IndexError("Invalid DataDirectory entry number was specified ({:d} <= {:d} < {:d}).".format(0, index, len(d)))
    E = d[index]
    global result; result = E
    T, cb = E['Address'], E['Size']
    if F:
        return Extract(F(result), output)
    if output in {'hex', 'raw'}:
        res = ptypes.dyn.block(cb.int())(offset=T.d.getoffset())
        return Extract(res.li, output)
    return Extract(result, output or 'print')

def list_exports(t, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Export']
    if E['Address'].int() == 0:
        raise ValueError("No Exports directory entry was found.")
    et = E['Address'].d.li
    global result; result = et
    if F:
        return Extract(F(result), output)
    if not output:
        filename = result['Name'].d.li.str()
        six.print_("Name:{:s} NumberOfFunctions:{:d} NumberOfNames:{:d}".format(filename, result['NumberOfFunctions'].int(), result['NumberOfNames'].int()))
        for ofs, hint, name, ordinalstring, entrypoint, fwd in result.iterate():
            six.print_("[{:d}] {!r} {!r} {:s}".format(hint, name, ordinalstring, "{:#x}".format(entrypoint) if fwd is None else fwd), file=sys.stdout)
        return
    if output in {'list'}:
        return Extract(("{:s}:{:s}:{:s}:{:s}:{:s}:{:s}".format('' if rva is None else "{:d}".format(rva), '' if hint is None else "{:d}".format(hint), name or '', ordinalstring or '', "{:d}".format(entrypoint) if fwd is None else '', fwd if entrypoint is None else '') for rva, hint, name, ordinalstring, entrypoint, fwd in result.iterate()), output)
    return Extract(result, output)

def list_imports(t, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry was found.")
    it = E['Address'].d.li
    global result; result = it
    if F:
        return Extract(F(result), output)
    if not output:
        _ = list(result.iterate())
        imax = len(str(len(_)))
        nmax = max([len(ite['Name'].d.li.str()) for ite in _] or [0])
        for i, ite in enumerate(result.iterate()):
            iat, int = ite['IAT'].d.li, ite['INT'].d.li
            six.print_("[{:d}]{:s} {:<{:d}s} IAT[{:d}] INT[{:d}]".format(i, ' '*(imax-len(str(i))), ite['Name'].d.li.str(), nmax, len(iat), len(int)), file=sys.stdout)
        return
    if output in {'list'}:
        return Extract(("{:d}:{:s}".format(i, n['Name'].d.li.str()) for i, n in enumerate(result[:-1])), output)
    return Extract(result, output)

def extract_import(t, index, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry was found.")
    it = E['Address'].d.li
    if not(0 <= index < len(it)):
        raise IndexError("Invalid Imports table index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(it)))
    ite = it[index]
    global result; result = ite
    if not F and output in {'list'}:
        summary = lambda (h,n,a,v): 'hint:{:d} name:{:s} offset:{:#x} value:{:#x}'.format(h,n,a,v)
        for ie in result.iterate():
            six.print_(summary(ie), file=sys.stdout)
        return
    return Extract(F(result) if F else result, output)

def list_resources(t, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry was found.")
    rt = E['Address'].d.li
    global result; result = rt
    if F:
        return Extract(F(result), output)
    summary = lambda n: '{:#x}:{:+#x} codepage:{:d}'.format(n['Data'].int(), n['Size'].int(), n['Codepage'].int())
    if not output:
        res = collectresources(result)
        for re in dumpresources(res):
            six.print_('/'.join(map(str, re)), summary(followresource(re, rt)), file=sys.stdout)
        return
    return Extract(result, output)

def extract_resource(t, path, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry was found.")
    rt = E['Address'].d.li
    rtp = []
    for p in path.split('/'):
        try: p = int(p)
        except ValueError: p = str(p)
        rtp.append(p)

    try:
        global result; result = followresource(rtp, rt)

    except LookupError, (p, rest, res):
        leftover = (p,) + rest[:]
        cp = rtp[:-len(leftover)]
        raise ValueError("Unable to locate resource item {:s} in resource directory: {:s}".format('/'.join(map(str,leftover)), '/'.join(map(str,cp))))

    if F:
        return Extract(F(result), output)

    if output in {'hex', 'raw'}:
        res = result['Data'].d.li if 'Data' in result.keys() else result
        return Extract(res, output)
    return Extract(result, output or 'print')

def dump_loadconfig(t, output, F=None):
    E = t['Next']['Header']['DataDirectory']['LoadConfig']
    if E['Address'].int() == 0:
        raise ValueError("No LoadConfig directory entry was found.")
    lc = E['Address'].d.li
    global result; result = lc
    if F:
        return Extract(F(result), output)
    return Extract(result, output or 'print')

def list_signature(t, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry was found.")
    s = E['Address'].d.li
    global result; result = s
    if F:
        return Extract(F(result), output)
    summary = lambda i, e: '[{:d}] {:+#x} wRevision:{:s} wCertificateType:{:s} bCertificate:{:d}'.format(i, e.getoffset(), e['wRevision'].str(), e['wCertificateType'].str(), e['bCertificate'].size())
    if not output or output in {'print'}:
        for i, se in enumerate(result):
            six.print_(summary(i, se), file=sys.stdout)
        return
    return Extract(result, output or 'raw')

def extract_signature(t, index, output, F=None):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry was found.")
    s = E['Address'].d.li
    if not (0 <= index < len(s)):
        raise IndexError("Invalid signature index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(s)))
    se = s[index]
    global result; result = se['bCertificate']
    if F:
        result = result.cast(ber.File)
        return Extract(F(result), output)
    if output in {'hex', 'raw'}:
        return Extract(result, output)
    result = result.cast(ber.File)
    return Extract(result, output or 'print')

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
    res.add_argument('-R','--dump-resource', action='store', nargs=1, type=str, dest='xresource', metavar='path', help='dump the resource with the \'/\'-separated specified path')
    res.add_argument('-l','--dump-loaderconfig', action='store_const', const=dump_loadconfig, dest='command', help='dump the LoadConfig directory entry')
    res.add_argument('-k','--list-signature', action='store_const', const=list_signature, dest='command', help='list the certificates at the Security directory entry')
    res.add_argument('-K','--dump-signature', action='store', nargs=1, type=int, dest='xsignature', metavar='index', help='dump the certificate at the specified index')

    res = p.add_argument_group()
    res.add_argument('--path', action='store', dest='location', metavar='path', help='navigate to a specific field described by a \':\' separated path.')
    p.set_defaults(location='')

    res = p.add_mutually_exclusive_group(required=False)
    res.add_argument('--raw', action='store_const', dest='output', const='raw', help='output contents in raw mode')
    res.add_argument('--print', action='store_const', dest='output', const='print', help='output contents in a readable format')
    res.add_argument('--hex', action='store_const', dest='output', const='hex', help='output contents as a hex dump')
    res.add_argument('--list', action='store_const', dest='output', const='list', help='output item in a single line')
    p.set_defaults(output='')
    return p

def figureargs(ns):
    F = functools.partial(Locate, ns.location) if ns.location else None
    if ns.command:
        return lambda t,output,loc=F: ns.command(t, output, loc)
    elif ns.xsection:
        return lambda t,output,loc=F: extract_section(t, ns.xsection[0], output, loc)
    elif ns.xentry:
        return lambda t,output,loc=F: extract_entry(t, ns.xentry[0], output, loc)
    elif ns.ximport:
        return lambda t,output,loc=F: extract_import(t, ns.ximport[0], output, loc)
    elif ns.xresource:
        return lambda t,output,loc=F: extract_resource(t, ns.xresource[0], output, loc)
    elif ns.xsignature:
        return lambda t,output,loc=F: extract_signature(t, ns.xsignature[0], output, loc)
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
        entry = res.Entry(p)
        if entry is None:
            raise LookupError(p, rest, res)
        return followresource(rest, entry.li)
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

