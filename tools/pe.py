#!/usr/bin/env python
import itertools,operator,logging,argparse
import ptypes,pecoff,ber
import six
#ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
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
    elif out == 'list':
        res = '\n'.join((n.summary() if hasattr(n, 'summary') else str(n) for n in obj))
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
    if isinstance(result, (ptypes.ptype.pointer_t, ptypes.pbinary.partial)):
        return repr(result)
    if hasattr(result, 'num'):
        return result.num()
    elif hasattr(result, 'int'):
        return result.int()
    elif hasattr(result, 'str'):
        return result.str()
    return repr(result)

## commands
def dump_exe(t, output):
    global result; result = t
    if not output or output == 'print':
        six.print_(result['Dos'].repr(), file=sys.stdout)
        six.print_(result['Stub'].hexdump(), file=sys.stdout)
        return
    if isinstance(output, basestring):
        t = ptypes.dyn.block(result['Dos'].size() + result['Stub'].size())
        return extract(t(offset=0).li, output)
    return extract(result, output)

def dump_header(t, output):
    H = t['Next']['Header']
    global result; result = H
    if not output:
        six.print_(result.p['Signature'], repr(result.p['Signature'].serialize()+result['SignaturePadding'].serialize()), file=sys.stdout)
        six.print_(result['FileHeader'].repr(), file=sys.stdout)
        six.print_(result['OptionalHeader'].repr(), file=sys.stdout)
        return
    return extract(result, output)

def list_sections(t, output):
    H = t['Next']['Header']
    global result; result = H['Sections']
    if not output:
        summary = lambda s: '{!r} {:#x}:{:+#x} Raw:{:#x}:{:+#x}'.format(s['Name'].str(), s['VirtualAddress'].int(), s['VirtualSize'].int(), s['PointerToRawData'].int(), s['SizeOfRawData'].int())
        for i, S in enumerate(result):
            six.print_('[{:d}] {:s}'.format(i, summary(S)), file=sys.stdout)
        return
    if output == 'list':
        return extract((S['Name'].str() for S in result), output)
    return extract(result, output)

def extract_section(t, index, output):
    H = t['Next']['Header']
    if not (0 <= index < len(H['Sections'])):
        raise IndexError("Invalid section index.")
    S = H['Sections'][index]
    global result; result = S
    #if 'load' in kwds:
    #    return extract(t['VirtualAddress'].d.li, output or 'raw')
    return extract(result['PointerToRawData'].d.li, output or 'hex')

def list_entries(t, output):
    H = t['Next']['Header']
    global result; result = H['DataDirectory']
    summary = lambda n: '{:s} {:#x}:{:+#x}'.format(n.classname(), n['Address'].int(), n['Size'].int())
    if not output:
        for i, n in enumerate(result):
            six.print_('[{:d}] {}'.format(i, summary(n)), file=sys.stdout)
        return
    if output == 'list':
        return extract((n.classname() for n in result if n['Address'].int()), output)
    return extract(result, output)

def extract_entry(t, index, output):
    d = t['Next']['Header']['DataDirectory']
    if not(0 <= index < len(d)):
        raise IndexError("Invalid DataDirectory entry number.")
    E = d[index]
    global result; result = E['Address'].d.li
    T, cb = E['Address'], E['Size']
    if output == 'print' or not isinstance(output, basestring):
        return extract(T.d.li, output)
    res = ptypes.dyn.block(cb.int())(offset=T.d.getoffset())
    return extract(res.li, output or 'raw')

def list_exports(t, output):
    E = t['Next']['Header']['DataDirectory']['Export']
    if E['Address'].int() == 0:
        raise ValueError("No Exports directory entry.")
    et = E['Address'].d.li
    global result; result = et
    if not output:
        filename = result['Name'].d.li.str()
        six.print_("Name:{:s} NumberOfFunctions:{:d} NumberOfNames:{:d}".format(filename, result['NumberOfFunctions'].int(), result['NumberOfNames'].int()))
        for ofs, ordinal, name, ordinalstring, value in result.iterate():
            six.print_("[{:d}] {!r} {!r} {:#x}".format(ordinal, name, ordinalstring, value), file=sys.stdout)
        return
    if output == 'list':
        return extract(("{:d}:{:s}:{:s}:{#x}".format(ordinal, name, ordinalstring, value) for _, ordinal, name, ordinalstring, value in result if n['Address'].int()), output)
    return extract(result, output)

def list_imports(t, output):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry.")
    it = E['Address'].d.li
    global result; result = it
    if not output:
        _ = list(result.iterate())
        imax = len(str(len(_)))
        nmax = max([len(ite['Name'].d.li.str()) for ite in _] or [0])
        for i, ite in enumerate(result.iterate()):
            iat, int = ite['IAT'].d.li, ite['INT'].d.li
            six.print_("[{:d}]{:s} {:<{:d}s} IAT[{:d}] INT[{:d}]".format(i, ' '*(imax-len(str(i))), ite['Name'].d.li.str(), nmax, len(iat), len(int)), file=sys.stdout)
        return
    if output == 'list':
        return extract((n['Name'].d.li.str() for n in result[:-1]), output)
    return extract(result, output)

def extract_import(t, index, output):
    E = t['Next']['Header']['DataDirectory']['Import']
    if E['Address'].int() == 0:
        raise ValueError("No Imports directory entry.")
    it = E['Address'].d.li
    if not(0 <= index < len(it)):
        raise IndexError("Invalid Imports table index.")
    ite = it[index]
    global result; result = ite
    if not output:
        summary = lambda (h,n,a,v): 'hint:{:d} name:{:s} offset:{:#x} value:{:#x}'.format(h,n,a,v)
        for ie in result.iterate():
            six.print_(summary(ie), file=sys.stdout)
        return
    return extract(result, output)

def list_resources(t, output):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry.")
    rt = E['Address'].d.li
    global result; result = rt
    summary = lambda n: '{:#x}:{:+#x} codepage:{:d}'.format(n['Data'].int(), n['Size'].int(), n['Codepage'].int())
    if not output:
        res = collectresources(result)
        for re in dumpresources(res):
            six.print_('/'.join(map(str, re)), summary(followresource(re, rt)), file=sys.stdout)
        return
    return extract(result, output)

def extract_resource(t, path, output):
    E = t['Next']['Header']['DataDirectory']['Resource']
    if E['Address'].int() == 0:
        raise ValueError("No Resource directory entry.")
    rt = E['Address'].d.li
    rtp = []
    for p in path.split('/'):
        try: p = int(p)
        except ValueError: p = str(p)
        rtp.append(p)
    rte = followresource(rtp, rt)
    global result; result = rte['Data'].d.li if 'Data' in rte.keys() else rte
    if output == 'print':
        # FIXME: dump structure if it's not a record
        return extract(result, 'print')
    return extract(result, output or 'raw')

def dump_loadconfig(t, output):
    E = t['Next']['Header']['DataDirectory']['LoadConfig']
    if E['Address'].int() == 0:
        raise ValueError("No LoadConfig directory entry.")
    lc = E['Address'].d.li
    global result; result = lc
    return extract(result, output or 'print')

def list_signature(t, output):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry.")
    s = E['Address'].d.li
    global result; result = s
    summary = lambda i, e: '[{:d}] {:+#x} wRevision:{:s} wCertificateType:{:s} bCertificate:{:d}'.format(i, e.getoffset(), e['wRevision'].str(), e['wCertificateType'].str(), e['bCertificate'].size())
    if not output or output == 'print':
        for i, se in enumerate(result):
            six.print_(summary(i, se), file=sys.stdout)
        return
    return extract(result, output or 'raw')

def extract_signature(t, index, output):
    E = t['Next']['Header']['DataDirectory']['Security']
    if E['Address'].int() == 0:
        raise ValueError("No Security directory entry.")
    s = E['Address'].d.li
    if not (0 <= index < len(s)):
        raise IndexError("Invalid section index.")
    se = s[index]
    cert = se['bCertificate'].cast(ber.File)
    global result; result = cert
    return extract(result, output or 'print')

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
    res.add_argument('-k','--list-signature', action='store_const', const=list_signature, dest='command', help='list the certificates at the Security directory entry')
    res.add_argument('-K','--dump-signature', action='store', nargs=1, type=int, dest='xsignature', metavar='index', help='dump the certificate at the specified index')

    res = p.add_mutually_exclusive_group(required=False)
    res.add_argument('--raw', action='store_const', dest='output', const='raw', help='output contents in raw mode')
    res.add_argument('--print', action='store_const', dest='output', const='print', help='output contents in a readable format')
    res.add_argument('--hex', action='store_const', dest='output', const='hex', help='output contents as a hex dump')
    res.add_argument('--list', action='store_const', dest='output', const='list', help='output item in a single line')
    res.add_argument('--path', action='store', nargs=1, dest='output', help='output the field specifed by a \':\' separated path.')
    p.set_defaults(output='')
    return p

def figureargs(ns):
    if ns.command:
        return ns.command
    elif ns.xsection:
        return lambda t,output: extract_section(t, ns.xsection[0], output)
    elif ns.xentry:
        return lambda t,output: extract_entry(t, ns.xentry[0], output)
    elif ns.ximport:
        return lambda t,output: extract_import(t, ns.ximport[0], output)
    elif ns.xresource:
        return lambda t,output: extract_resource(t, ns.xresource[0], output)
    elif ns.xsignature:
        return lambda t,output: extract_signature(t, ns.xsignature[0], output)
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

