#!/usr/bin/env python
import six,argparse,logging,importlib
import functools,operator,itertools,types
import ptypes,pecoff
#ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
ptypes.config.defaults.ptype.clone_name = '{}'
ptypes.config.defaults.pint.bigendian_name = 'be({})'
ptypes.config.defaults.pint.littleendian_name = '{}'

def Locate(path, obj):
    return Resolve(obj, path.split(':'))

def Extract(obj, outformat, file=None):
    out = lambda string, **kwargs: six.print_(string, **kwargs)
    if outformat == 'print':
        res = "{!r}".format(obj)
    elif outformat == 'hex':
        res = obj.hexdump()
    elif outformat == 'raw':
        out = lambda string, **kwargs: (kwargs['file'] if sys.version_info.major < 3 else kwargs['file'].buffer).write(string)
        res = obj.serialize()
    elif outformat == 'list':
        res = '\n'.join((n.summary() if hasattr(n, 'summary') else str(n) for n in obj))

    # default
    elif not obj:
        res = obj.details()
    elif isinstance(obj, (ptypes.ptype.pointer_t, ptypes.pbinary.partial)):
        res = "{!r}".format(obj)
    elif hasattr(obj, 'num'):
        res = obj.num()
    elif hasattr(obj, 'int'):
        res = obj.int()
    elif hasattr(obj, 'str'):
        res = obj.str()
    else:
        res = "{!r}".format(obj)
    out(res, file=file)

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
def dump_exe(t, outformat, F=None, output=None):
    global result; result = t
    if F:
        return Extract(F(result), outformat, file=output)
    if not outformat or outformat in {'print'}:
        six.print_("{!r}\n".format(result), file=output)
        six.print_("{!r}\n".format(result['Header']), file=output)
        six.print_(result['Stub'].hexdump(), file=output)
        return
    if outformat in {'hex','raw'}:
        t = ptypes.dyn.block(result['Header'].size() + result['Stub'].size())
        return Extract(t(offset=0).li, outformat, file=output)
    return Extract(result, outformat, file=output)

def dump_header(t, outformat, F=None, output=None):
    H = t['Next']['Header']
    global result; result = H
    if F:
        return Extract(F(result), outformat, file=output)
    if not outformat:
        six.print_("{!r}".format(result.p['Signature']), "{!r}\n".format(result.p['Signature'].serialize() + result['SignaturePadding'].serialize()), file=output)
        six.print_("{!r}\n".format(result['FileHeader']), file=output)
        six.print_("{!r}\n".format(result['OptionalHeader']), file=output)
        return
    return Extract(result, outformat, file=output)

def list_sections(t, outformat, F=None, output=None):
    H = t['Next']['Header']
    global result; result = H['Sections']
    if F:
        return Extract(F(result), outformat, file=output)
    if not outformat:
        summary = lambda s: "{!r} {:#x}:{:+#x} Raw:{:#x}:{:+#x}".format(s['Name'].str(), s['VirtualAddress'].int(), s['VirtualSize'].int(), s['PointerToRawData'].int(), s['SizeOfRawData'].int())
        for i, S in enumerate(result):
            six.print_("[{:d}] {:s}".format(i, summary(S)), file=output)
        return
    if outformat in {'list'}:
        # FIXME: output some attributes that can be fielded
        return Extract((S['Name'].str() for S in result), outformat, file=output)
    return Extract(result, outformat, file=output)

def extract_section(t, index, outformat, F=None, output=None):
    H = t['Next']['Header']
    if not (0 <= index < len(H['Sections'])):
        raise IndexError("Invalid section index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(H['Sections'])))
    S = H['Sections'][index]
    global result; result = S
    #if 'load' in kwds:
    #    return Extract(t['VirtualAddress'].d.li, outformat or 'raw', file=output)
    if F:
        return Extract(F(result), outformat, file=output)
    if outformat == 'print':
        return six.print_("{!r}".format(S), file=output)
    return Extract(result['PointerToRawData'].d.li, outformat or 'hex', file=output)

def list_entries(t, outformat, F=None, output=None):
    H = t['Next']['Header']
    global result; result = H['DataDirectory']
    if F:
        return Extract(F(result), outformat, file=output)
    summary = lambda n: "{:s} {:#x}:{:+#x}".format(n.classname(), n['Address'].int(), n['Size'].int())
    if not outformat:
        for i, n in enumerate(result):
            six.print_("[{:d}] {:s}".format(i, summary(n)), file=output)
        return
    if outformat in {'list'}:
        # FIXME: output some attributes that can be fielded
        return Extract((n.classname() for n in result if n['Address'].int()), outformat, file=output)
    return Extract(result, outformat, file=output)

def extract_entry(t, index, outformat, F=None, output=None):
    d = t['Next']['Header']['DataDirectory']
    if not(0 <= index < len(d)):
        raise IndexError("Invalid DataDirectory entry number was specified ({:d} <= {:d} < {:d}).".format(0, index, len(d)))
    E = d[index]
    global result; result = E['Address'].d.li
    T, cb = E['Address'], E['Size']
    if F:
        return Extract(F(result), outformat, file=output)
    if outformat in {'hex', 'raw'}:
        res = ptypes.dyn.block(cb.int())(offset=T.d.getoffset())
        return Extract(res.li, outformat, file=output)
    return Extract(result, outformat or 'print', file=output)

def list_exports(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Export']
    if E['Address'].int() == 0:
        raise ValueError("No Exports directory entry was found.")
    global et; et = E['Address'].d.li
    global result; result = et
    if F:
        return Extract(F(result), outformat, file=output)
    if not outformat:
        filename = result['Name'].d.li.str()
        six.print_("Name:{:s} NumberOfFunctions:{:d} NumberOfNames:{:d}".format(filename, result['NumberOfFunctions'].int(), result['NumberOfNames'].int()), file=output)
        for ofs, hint, name, ordinalstring, entrypoint, fwd in result.iterate():
            six.print_("[{:d}] {!r} {!r} {:s}".format(hint, name, ordinalstring, "{:#x}".format(entrypoint) if fwd is None else fwd), file=output)
        return
    if outformat in {'list'}:
        return Extract(("{:s}:{:s}:{:s}:{:s}:{:s}:{:s}".format('' if rva is None else "{:d}".format(rva), '' if hint is None else "{:d}".format(hint), name or '', ordinalstring or '', "{:d}".format(entrypoint) if fwd is None else '', fwd if entrypoint is None else '') for rva, hint, name, ordinalstring, entrypoint, fwd in result.iterate()), outformat, file=output)
    return Extract(result, outformat, file=output)

def extract_export(t, index, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Export']
    if E['Address'].int() == 0:
        raise ValueError("No Exports directory entry was found.")
    global et; et = E['Address'].d.li
    if not(0 <= index < len(et)):
        raise IndexError("Invalid Exports table index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(it)))
    ete = next(e for i, e in enumerate(et.iterate()) if i == index)
    global result; result = ete
    if not F and (not outformat or outformat in {'print'}):
        # rva, hint, name, ordinalname, entry, forwarded
        six.print_("index={:d} rva={:#x} hint={:#x} name={!s} ordinalname={!s} entry={:#x} forwarded={!s}".format(index, *ete), file=output)
        return
    if not F and outformat in {'raw','hex'}:
        aof, aon, no = (et[n].d.li[index] for n in ('AddressOfFunctions', 'AddressOfNames', 'AddressOfNameOrdinals'))
        data = ptypes.parray.type(length=3).set([aof, aon, no])
        return Extract(data, outformat, file=output)
    return Extract(F(et) if F else result, outformat, file=output)

def list_imports(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry was found.")
    global it; it = E['Address'].d.li
    global result; result = it
    if F:
        return Extract(F(result), outformat, file=output)
    if not outformat:
        items = [item for item in result.iterate()]
        imax = len(str(len(items)))
        nmax = max([len(ite['Name'].d.li.str()) for ite in items] or [0])
        for i, ite in enumerate(result.iterate()):
            iat, int = ite['IAT'].d.li, ite['INT'].d.li
            six.print_("[{:d}]{:s} {:<{:d}s} IAT[{:d}] INT[{:d}]".format(i, ' '*(imax-len(str(i))), ite['Name'].d.li.str(), nmax, len(iat), len(int)), file=output)
        return
    if outformat in {'list'}:
        return Extract(("{:d}:{:s}".format(i, n['Name'].d.li.str()) for i, n in enumerate(result[:-1])), outformat, file=output)
    return Extract(result, outformat, file=output)

def extract_import(t, index, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry was found.")
    global it; it = E['Address'].d.li
    if not(0 <= index < len(it)):
        raise IndexError("Invalid Imports table index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(it)))
    ite = it[index]
    global result; result = ite
    if not F and (not outformat or outformat in {'list'}):
        # FIXME: separate these fields somehow
        summary = "hint:{:d} name:{:s} offset:{:#x} value:{:#x}".format
        for ie in result.iterate():
            six.print_(summary(*ie), file=output)
        return
    return Extract(F(result) if F else result, outformat, file=output)

def list_resources(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry was found.")
    global rt; rt = E['Address'].d.li
    global result; result = rt
    if F:
        return Extract(F(result), outformat, file=output)
    summary = lambda n: "{:#x}:{:+#x} CodePage:{:d}".format(n['OffsetToData'].int(), n['Size'].int(), n['Codepage'].int())
    if not outformat:
        res = collectresources(result)
        for re in dumpresources(res):
            six.print_('/'.join(map(str, re)), summary(followresource(re, rt)), file=output)
        return
    return Extract(result, outformat, file=output)

def extract_resource(t, path, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry was found.")
    global rt; rt = E['Address'].d.li
    rtp = []
    for p in path.split('/'):
        try: p = int(p)
        except ValueError: p = str(p)
        rtp.append(p)

    try:
        global result; result = followresource(rtp, rt)

    except LookupError as packed:
        (p, rest, res) = packed.args
        leftover = (p,) + rest[:]
        cp = rtp[:-len(leftover)]
        raise ValueError("Unable to locate resource item {:s} in resource directory: {:s}".format('/'.join(map(str,leftover)), '/'.join(map(str,cp))))

    if F:
        return Extract(F(result), outformat, file=output)

    if outformat in {'hex', 'raw'}:
        res = result['Data'].d.li if 'Data' in result.keys() else result
        return Extract(res, outformat, file=output)
    return Extract(result, outformat or 'print', file=output)

def dump_loadconfig(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['LoadConfig']
    if E['Address'].int() == 0:
        raise ValueError("No LoadConfig directory entry was found.")
    global lc; lc = E['Address'].d.li
    global result; result = lc
    if F:
        return Extract(F(result), outformat, file=output)
    return Extract(result, outformat or 'print', file=output)

def list_signature(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry was found.")
    global s; s = E['Address'].d.li
    global result; result = s
    if F:
        return Extract(F(result), outformat, file=output)
    summary = lambda i, e: "[{:d}] {:+#x} wRevision:{:s} wCertificateType:{:s} bCertificate:{:d}".format(i, e.getoffset(), e['wRevision'].str(), e['wCertificateType'].str(), e['bCertificate'].size())
    if not outformat or outformat in {'print'}:
        for i, se in enumerate(result):
            six.print_(summary(i, se), file=output)
        return
    return Extract(result, outformat or 'raw', file=output)

def extract_signature(t, index, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry was found.")
    global s; s = E['Address'].d.li
    if not (0 <= index < len(s)):
        raise IndexError("Invalid signature index was specified ({:d} <= {:d} < {:d}).".format(0, index, len(s)))
    se = s[index]

    try:
        module = importlib.import_module('protocol.ber')

        class CertificatePadded(ptypes.pstruct.type):
            _fields_ = [
                (module.File, 'SignedData'),
                (ptypes.dynamic.padding(8), 'Padding'),
            ]

        rt = CertificatePadded

    except (ImportError, AttributeError):
        rt, _ = None, logging.warning("Unable to import ptypes template, `ber`, in order to cast the Security directory entry.")

    global result; result = se['bCertificate']
    if F:
        result = result if rt is None else result.cast(rt)
        return Extract(F(result), outformat, file=output)
    if outformat in {'hex', 'raw'} or (outformat in {'list'} and rt is None):
        return Extract(result, 'hex' if outformat in {'list'} else outformat, file=output)
    result = result if rt is None else result.cast(rt)
    return Extract(result, outformat or 'print', file=output)

def emit_pdb(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Debug']
    if E['Address'].int() == 0:
        raise ValueError("No debug data directory entry was found.")
    global D; D = E['Address'].d.li
    item = next((item for item in D if item['Type']['CODEVIEW']), None)
    if item is None:
        raise ValueError("Unable to locate item type {:s} in debug data directory: {:s}".format('CODEVIEW', ', '.join(item['Type'].str() for item in D)))
    global result; result = item['PointerToRawData'].d.li
    info = result['Info']
    if not outformat:
        six.print_("{!s}".format(info.SymUrl()), file=output)
        return
    if outformat in {'list'}:
        fields = [fld for fld in info]
        six.print_(':'.join(fields[0:1] + [info[fields[0]].str().upper()]))
        six.print_(':'.join(fields[1:2] + ["{:d}".format(info[fields[1]].int())]))
        six.print_(':'.join(fields[2:3] + [info[fields[2]].str()]))
        return
    if F:
        return Extract(F(info), outformat, file=output)
    return Extract(info, outformat, file=output)

def list_debugpogo(t, outformat, F=None, output=None):
    E = t['Next']['Header']['DataDirectory']['Debug']
    if E['Address'].int() == 0:
        raise ValueError("No debug data directory entry was found.")
    global D; D = E['Address'].d.li
    item = next((item for item in D if item['Type']['POGO']), None)
    global result; result = item['PointerToRawData'].d.li
    entries = result['Entries']
    if F:
        return Extract(F(entries), outformat, file=output)
    if not outformat or outformat in {'print'}:
        items = [item for item in entries]
        for i, item in enumerate(items):
            rva, size = (item[fld] for fld in ['rva', 'size'])
            six.print_("[{:d}] {:#x}-{:#x} {:+#x} {:s}".format(i, rva.int(), rva.int() + size.int(), size.int(), item['section'].str()))
        return
    if outformat in {'list'}:
        return Extract(("{:x}{:+x}:{:x}:{:s}".format(item['rva'].int(), item['rva'].int()+item['size'].int(), item['size'].int(), item['section'].str()) for item in entries), outformat, file=output)
    return Extract(entries, outformat, file=output)

def args():
    p = argparse.ArgumentParser(prog="pe.py", description='Display some information about a portable executable file', add_help=True)
    p.add_argument('infile', type=argparse.FileType('rb'), help='a portable executable file')
    p.add_argument('-o', '--outfile', dest='output', type=argparse.FileType('wb'), default='-', help='a file to write the output to')
    p.add_argument('-O', '--format', action='store', dest='format', type=operator.methodcaller('lower'), choices=['raw', 'print', 'hex', 'list'], default='', help='specify the output format to emit the requested fields as')
    p.add_argument('--path', action='store', dest='location', metavar='PATH', default='', help='navigate to a specific field described by a \':\' separated path.')

    res = p.add_mutually_exclusive_group(required=True)
    res.add_argument('-m','--dump-exe', action='store_const', const=dump_exe, dest='command', help='display the MZ executable header')
    res.add_argument('-p','--dump-header', action='store_const', const=dump_header, dest='command', help='display the PE header')
    res.add_argument('-s','--list-sections', action='store_const', const=list_sections, dest='command', help='list all the available sections')
    res.add_argument('-S','--extract-section', action='store', nargs=1, type=int, dest='xsection', metavar='index', help='extract the specified section to stdout')
    res.add_argument('-d','--list-entry', action='store_const', const=list_entries, dest='command', help='list all the data directory entries')
    res.add_argument('-D','--extract-entry', action='store', nargs=1, type=int, dest='xentry', metavar='index', help='dump the contents of the datadirectory entry to stdout')
    res.add_argument('-e','--list-exports', action='store_const', const=list_exports, dest='command', help='display the contents of the export directory')
    res.add_argument('-E','--dump-export', action='store', nargs=1, type=int, dest='xexport', metavar='index', help='dump the specified export')
    res.add_argument('-i','--list-imports', action='store_const', const=list_imports, dest='command', help='list all the libraries listed in the import directory')
    res.add_argument('-I','--dump-import', action='store', nargs=1, type=int, dest='ximport', metavar='index', help='list all the imported functions from the specified library')
    res.add_argument('-r','--list-resource', action='store_const', const=list_resources, dest='command', help='display the resource directory tree')
    res.add_argument('-R','--dump-resource', action='store', nargs=1, type=str, dest='xresource', metavar='path', help='dump the resource with the \'/\'-separated specified path')
    res.add_argument('-l','--dump-loaderconfig', action='store_const', const=dump_loadconfig, dest='command', help='dump the LoadConfig directory entry')
    res.add_argument('-k','--list-signature', action='store_const', const=list_signature, dest='command', help='list the certificates at the Security directory entry')
    res.add_argument('-K','--dump-signature', action='store', nargs=1, type=int, dest='xsignature', metavar='index', help='dump the certificate at the specified index')
    res.add_argument('--dump-pogo', action='store_const', const=list_debugpogo, dest='command', help='dump the pogo entry from the debug datadirectory')
    res.add_argument('--emit-pdb', action='store_const', const=emit_pdb, dest='command', help='display the pdb path from the debug datadirectory')

    return p

def figureargs(ns):
    F = functools.partial(Locate, ns.location) if ns.location else None
    if ns.command:
        return lambda t,format,loc=F,output=sys.stdout: ns.command(t, format, loc, output=output)
    elif ns.xsection:
        return lambda t,format,loc=F,output=sys.stdout: extract_section(t, ns.xsection[0], format, loc, output=output)
    elif ns.xentry:
        return lambda t,format,loc=F,output=sys.stdout: extract_entry(t, ns.xentry[0], format, loc, output=output)
    elif ns.xexport:
        return lambda t,format,loc=F,output=sys.stdout: extract_export(t, ns.xexport[0], format, loc, output=output)
    elif ns.ximport:
        return lambda t,format,loc=F,output=sys.stdout: extract_import(t, ns.ximport[0], format, loc, output=output)
    elif ns.xresource:
        return lambda t,format,loc=F,output=sys.stdout: extract_resource(t, ns.xresource[0], format, loc, output=output)
    elif ns.xsignature:
        return lambda t,format,loc=F,output=sys.stdout: extract_signature(t, ns.xsignature[0], format, loc, output=output)
    return None

def collectresources(entry):
    res = {}
    for n in entry.List():
        child = entry.Entry(n).li
        res[n] = collectresources(child) if isinstance(child, pecoff.portable.resources.IMAGE_RESOURCE_DIRECTORY) else child
    return res

def dumpresources(r):
    keys = {item for item in r.keys()}
    for n in sorted(keys, key="{!s}".format):
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

    infile = ptypes.prov.fileobj(res.infile)
    ptypes.setsource(infile)
    z = pecoff.Executable.File(source=infile)
    z = z.l

    result = None
    figureargs(res)(z, format=res.format, output=res.output)
    globals().pop('res')

