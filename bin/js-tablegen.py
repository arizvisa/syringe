from __future__ import print_function
import sys, os
import collections, json
import functools, operator, itertools
import ptypes, pecoff
import logging
Log = logging.getLogger()

import argparse

def parse_resources(pe):
    sections = pe['Sections']
    datadirectory = pe['DataDirectory']
    resourceDirectory = datadirectory['ResourceTable']
    if resourceDirectory['Address'].int():
        return resourceDirectory['Address'].d
    raise ptypes.error.LoadError(resourceDirectory)

def GetChildByKey(versionInfo, szKey):
    return next(ch['Child'] for ch in versionInfo['Children'] if ch['Child']['szKey'].str() == szKey)

def ExtractLgCpIds(versionInfo):
    vfi = GetChildByKey(versionInfo, u'VarFileInfo')
    res = (val.cast(ptypes.parray.type(_object_=ptypes.pint.uint16_t,length=2)) for val in itertools.chain( *(var['Child']['Value'] for var in vfi['Children']) ))
    return tuple((cp.int(), lg.int()) for cp, lg in res)

def GetStringTable(versionInfo, pack_LgidCp):
    (Lgid, Cp) = pack_LgidCp
    sfi = GetChildByKey(versionInfo, u'StringFileInfo')
    LgidCp = '{:04X}{:04X}'.format(Lgid,Cp)
    for st in sfi['Children']:
        st = st['Child']
        if st['szKey'].str().upper() == LgidCp:
            return [s['Child'] for s in st['Children']]
        continue
    raise KeyError(Lgid, Cp)

def get_resource_version(pe, opts):
    # parse the resource directory
    try:
        resource = parse_resources(pe)
    except ptypes.error.LoadError as e:
        return ''
    if resource.getoffset() == 0:
        Log.warning("PE {:s} does not seem to have a resource entry. Unable to determine version info.".format(pe.source.file.name))
        return ''
    resource = resource.l

    # sanity check that a VERSION_INFO record exists
    VERSION_INFO = 16
    if VERSION_INFO not in resource.List():
        Log.warning("PE {:s} does not appear to contain a VERSION_INFO entry within its resources directory.".format(pe.source.file.name))
        return ''

    # Get the VERSION_INFO entry
    try:
        names = resource.Entry(VERSION_INFO).l
    except AttributeError:
        Log.warning("PE {:s} does not have a resource entry that matches VERSION_INFO.".format(pe.source.file.name))
        return ''

    # Check the name
    try:
        if opts.name is not None:
            languages = names.Entry(opts.name).l
        else:
            if names['NumberOfIds'].int() != 1:
                raise IndexError
            languages = names['Ids'][0]['Entry'].d.l
            Log.info("Defaulting to the only language entry: {:d}".format(names['Ids'][0]['Name'].int()))
    except IndexError:
        Log.warning("PE {:s} has more than one name in VERSION_INFO. : {!r}".format(pe.source.file.name, tuple(n['Name'].int() for n in resource_Names['Ids'])))
        return ''
    except AttributeError:
        Log.warning("PE {:s} has no resource in VERSION_INFO with the requested language. : {!r}".format(pe.source.file.name, tuple(n['Name'].int() for n in resource_Names['Ids'])))
        return ''

    # Check the languages
    try:
        if opts.language is not None:
            version = languages.Entry(opts.language).l
        else:
            if languages['NumberOfIds'].int() != 1:
                raise IndexError
            version = languages['Ids'][0]['Entry'].d.l
            Log.info("Defaulting to the only version entry: {:d}".format(languages['Ids'][0]['Name'].int()))

    except IndexError:
        Log.warning("PE {:s} has more than one language. : {!r}".format(pe.source.file.name, tuple(n['Name'].int() for n in languages['Ids'])))
        return ''
    except AttributeError:
        Log.warning("PE {:s} has no version records found for the specified language. : {!r}".format(pe.source.file.name, opts.language))
        return ''
    else:
        versionInfo = version['Data'].d

    # parse the version info
    vi = versionInfo.l.cast(pecoff.portable.resources.VS_VERSIONINFO)
    lgcpids = ExtractLgCpIds(vi)

    # figure out the language and codepage
    if len(lgcpids) > 1:
        language = opts.language if opts.langid is None else opts.langid
        try:
            codepage, = [cp for lg,cp in lgcpids if lg == language] if opts.codepage is None else (opts.codepage,)
        except ValueError as e:
            Log.warning("PE {:s} has more than one (language,codepage). Please specify one via command-line. Use -h for more information.".format(pe.source.file.name))
            return ''
        if (language,codepage) not in lgcpids:
            Log.warning("An invalid (language,codepage) was specified for {:s}. : {!r} not in {!r}".format(pe.source.file.name, (language,codepage), lgcpids))
            return ''
    else:
        (language,codepage), = lgcpids

    # rip out the properties for the language+codepage
    try:
        st = GetStringTable(vi, (language,codepage))
    except KeyError:
        Log.warning("PE {:s} has no properties for the specified (language,codepage). : {!r}".format(pe.source.file.name, (language,codepage)))
        return ''
    else:
        strings = dict((s['szKey'].str(),s['Value'].str()) for s in st)
    return strings[u'FileVersion'].split(' ')[0]

def dump_exports(pe, jsname, outfile):
    dd = pe['DataDirectory']['ExportTable']
    try:
        et = dd['Address'].d.l
    except Exception:
        print("const {:s} = {{".format(jsname), file=outfile)
        print("};", file=outfile)
        return jsname

    # collect all exports
    res = list()
    for _, _, name, _, va in et.iterate():
        res.append((name, va))

    # output it in javascript
    jsname = jsname or 'ExportOffsets'
    print("const {:s} = {{".format(jsname), file=outfile)
    for name, ea in res:
        print("  '{:s}': {:d},".format(name, ea), file=outfile)
    print("};", file=outfile)
    return jsname

def dump_imports(pe, jsname, outfile):
    dd = pe['DataDirectory']['ImportTable']
    try:
        it = dd['Address'].d.l
    except Exception:
        print("const {:s} = {{".format(jsname), file=outfile)
        print("};", file=outfile)
        return jsname

    # collect all the imports
    res = collections.defaultdict(list)
    for e in it[:-1]:
        m = e['Name'].d.l
        for hint, name, offset, _ in e.iterate():
            ea = pe.getaddressbyoffset(offset)
            res[m.str()].append( (hint, name, ea) )
        continue

    # output a javascripty version of the dict
    jsname = jsname or 'ImportOffsets'
    print("const {:s} = {{".format(jsname), file=outfile)
    for m in res:
        print("  '{:s}': [".format(m.lower()), file=outfile)
        for hint, name, address in res[m]:
            print("    [{:d}, '{:s}', '{:s}'],".format(address, m, name), file=outfile)
        print("  ],", file=outfile)
    print("};", file=outfile)
    return jsname

Args = argparse.ArgumentParser(description='Dump the imports and exports for binaries into the specified output file (or stdout).')
Args.add_argument('infile', type=argparse.FileType('rb'), nargs='+', help='read from the specified portable executables')
Args.add_argument('-o', '--output', dest='outfile', default=sys.stdout, type=argparse.FileType('w'), help='write the output to the specified file')
Args.add_argument('--name', default=None, type=int, help='use the specified resouce name')
Args.add_argument('--language', default=None, type=int, help='use the specified resource language')
Args.add_argument('--langid', default=None, type=int, help='use the specified language-id')
Args.add_argument('--codepage', default=None, type=int, help='use the specified codepage')

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(filename)s:%(lineno)d <%(levelname)s> %(message)s')

    if len(sys.argv) <= 1:
        print(Args.format_usage())
        sys.exit(1)
    args = Args.parse_args(sys.argv[1:])

    result = collections.defaultdict(dict)
    name = None
    for source in itertools.imap(ptypes.prov.fileobj, args.infile):
        Log.info("Beginning to process {:s}...".format(source.file.name))
        infile = pecoff.Executable.File(source=source)
        try:
            infile = infile.l
        except ptypes.error.LoadError:
            Log.fatal("Unable to load portable executable {!r}".format(source.file.name))
            sys.exit(1)

        pe = infile['Next']['Header']

        name = os.path.split(source.file.name)[1]
        version = get_resource_version(pe, args)
        minor = version.rsplit('.', 1)[-1]

        result[version]['Name'] = json.dumps(name)
        Log.info("Processing the imports for {:s}...".format(source.file.name))
        result[version]['Imports'] = dump_imports(pe, 'ImportsOffset_{:s}'.format(minor), args.outfile)
        Log.info("Processing the exports for {:s}...".format(source.file.name))
        result[version]['Exports'] = dump_exports(pe, 'ExportsOffset_{:s}'.format(minor), args.outfile)

        Log.info("...completed processing {:s}.".format(source.file.name))
        continue

    latest = sorted(result.keys())[-1]
    print("module.exports['Name'] = {:s};".format(result[latest]['Name']), file=args.outfile)

    for version, structs in sorted(result.items(), key=operator.itemgetter(0)):
        print("module.exports['{:s}'] = {{ {:s} }};".format(version, ', '.join(("{:s}: {:s}".format(k, v) for k, v in structs.items()))), file=args.outfile)

    print("module.exports[null] = module.exports['{:s}'];".format(latest), file=args.outfile)
    sys.exit(0)
