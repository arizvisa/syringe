#!/usr/bin/env python
import sys,itertools,logging,optparse,os.path,locale,datetime,math,json
import ptypes,pecoff
from ptypes import *

def portable_print2(*args, **kwargs):
    file = kwargs.pop('file', sys.stdout)
    assert(not(kwargs))
    print >>file, ' '.join(map("{!s}".format, args))
print_ = portable_print2 if sys.version_info.major < 3 else eval('print')

#Type = 16       # Version Info
#Name = 1        # Name
#Language = 1033 # English

def parseResourceDirectory(filename):
    source = ptypes.prov.file(filename, mode='r')
    mz = pecoff.Executable.File(source=source).l
    pe = mz['Next']['Header']
    sections = pe['Sections']
    datadirectory = pe['DataDirectory']
    resourceDirectory = datadirectory[2]
    return resourceDirectory['Address']

def getChildByKey(versionInfo, szKey):
    return next(item for item in versionInfo['Children'] if item['szKey'].str() == szKey)

def iterateStringFileInfo(versionInfo):
    sfi = getChildByKey(versionInfo, u'StringFileInfo')
    for item in sfi['Children']:
        szkey = item['szKey'].str()
        if len(szkey) != 8:
            logging.warning("Skipping invalid format for the \"{:s}\" in the \"{:s}\" table from the version information".format('szKey', 'StringFileInfo'))
            continue
        Lg, Cp = szkey[:4], szkey[4:]
        yield int(Lg, 16), int(Cp, 16)
    return

def extractLgCpIds(versionInfo):
    try:
        vfi = getChildByKey(versionInfo, u'VarFileInfo')
    except StopIteration:
        items = []
    else:
        iterable = (item['Value'].cast(parray.type(_object_=pint.uint16_t,length=2)) for item in vfi['Children'])
        items = ((cp.int(), lg.int()) for cp, lg in iterable)

    iterable = itertools.chain(iterateStringFileInfo(versionInfo), items)
    return tuple({item for item in iterable})

def getStringFileInfo(versionInfo, pack_LgidCp):
    (Lgid, Cp) = pack_LgidCp
    sfi = getChildByKey(versionInfo, u'StringFileInfo')
    LgidCp = '{:04X}{:04X}'.format(Lgid,Cp)
    for st in sfi['Children']:
        if st['szKey'].str().upper() == LgidCp:
            return [s for s in st['Children']]
        continue
    raise KeyError(Lgid, Cp)

class help(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        self.usage = '%prog EXECUTABLE'

        self.add_option('', '--dump-names', default=False, action='store_true', help='dump the name tables available under the VERSION_INFO resource directory as JSON')
        self.add_option('', '--name', default=None, type='int', help='use the specified name when searching through the resource directory')
        self.add_option('', '--dump-resources', default=False, action='store_true', help='dump the languages for the resources available under the VERSION_INFO resource directory as JSON')
        self.add_option('', '--resource', default=None, type='int', help='use the specified language when searching through the resource directory')

        # VS_FIXEDFILEINFO
        self.add_option('-u', '--use-fixedfileinfo', default=False, action='store_true', help='use the VS_FIXEDFILEINFO structure instead of the string table')

        # VS_VERSIONINFO
        self.add_option('', '--list-lgcp', default=False, action='store_true', help='dump the language-id/codepage pairs that are available as JSON')
        self.add_option('-l', '--language-id', dest='lgid', default=None, type='int', help='use the specified language-id when locating the correct string table')
        self.add_option('-c', '--codepage', default=None, type='int', help='use the specified codepage when locating the correct stringtable')

        # fields
        self.add_option('-d', '--dump', default=False, action='store_true', help='dump the discovered properties that can be used for FORMAT as JSON')
        self.add_option('-f', '--format', default='{__name__~upper}/{ProductVersion}/{OriginalFilename}', type='str', help='output the specified format (defaults to {__name__~upper}/{ProductVersion}/{OriginalFilename})')
        self.description = 'Extract the version information from the resource directory of the specified EXECUTABLE and write it to stdout using FORMAT.'

help = help()

if __name__ == '__main__':
    import sys,logging

    opts,args = help.parse_args(sys.argv)
    try:
        filename = args.pop(1)

    except Exception:
        help.print_help()
        sys.exit(0)

    # parse the executable
    try:
        resource_address = parseResourceDirectory(filename)
    except ptypes.error.LoadError as e:
        print_("File {:s} does not appear to be an executable.".format(filename), file=sys.stderr)
        sys.exit(1)
    if resource_address.int() == 0:
        print_("File {:s} does not contain a resource data directory entry.".format(filename), file=sys.stderr)
        sys.exit(1)
    resource = resource_address.d.li

    # save it somewhere
    pe = resource.getparent(pecoff.IMAGE_NT_HEADERS)

    # parse the resource names
    VERSION_INFO = 16
    if VERSION_INFO not in resource.List():
        print_("File {:s} does not appear to contain a VERSION_INFO ({:d}) entry within its resource directory.".format(filename, VERSION_INFO), file=sys.stderr)
        sys.exit(1)

    try:
        resource_Names = resource.Entry(VERSION_INFO).l
    except AttributeError:
        print_("No entries for VERSION_INFO ({:d}) in the resource directory from file {:s}.".format(VERSION_INFO, filename), file=sys.stderr)
        sys.exit(1)
    if opts.dump_names:
        print_('Dumping the name table entries from the resource directory as requested by user:', file=sys.stderr)
        print_(json.dumps([item for item in resource_Names.iterate()]), file=sys.stdout)
        sys.exit(0)

    # parse the resource languages from the resource name
    try:
        if opts.name is not None:
            resource_Languages = resource_Names.Entry(opts.name).l
        else:
            if resource_Names['NumberOfIdEntries'].int() != 1:
                raise IndexError
            resource_Languages = resource_Names['Ids'][0]['Entry'].d.l
            print_("Defaulting to the only available language entry: {:d}".format(resource_Names['Ids'][0]['Name'].int()), file=sys.stderr)
    except IndexError:
        print_("More than one entry was found under VERSION_INFO ({:d}) in file {:s}: {!s}".format(VERSION_INFO, filename, tuple(item['Name'].int() for item in resource_Names['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        print_("No resource found in file {:s} with the requested name ({!s}).".format(filename, opts.name), file=sys.stderr)
        sys.exit(1)
    if opts.dump_resources:
        print_('Dumping the languages for the resource entries from the resource name table as requested by user:', file=sys.stderr)
        print_(json.dumps([item for item in resource_Languages.iterate()]), file=sys.stdout)
        sys.exit(0)

    # grab the version record from the resource language
    try:
        if opts.resource is not None:
            resource_Version = resource_Languages.entry(opts.resource).l
        else:
            if resource_Languages['NumberOfIdEntries'].int() != 1:
                resource_Version = resource_Languages['Ids'][0]['Entry'].d.l
                print_("More than one language resource entry ({:s}) was found in the file {:s}. As no --resource was specified, trying the very first one ({:d}).".format(', '.join(map("{:d}".format, (item['Name'].int() for item in resource_Languages['Ids']))), filename, resource_Languages['Ids'][0]['Name'].int()), file=sys.stderr)

            else:
                resource_Version = resource_Languages['Ids'][0]['Entry'].d.l
                print_("Defaulting to the only available language resource entry: {:d}".format(resource_Languages['Ids'][0]['Name'].int()), file=sys.stderr)

    except IndexError:
        print_("More than one language resource entry was found in file {:s}: {!s}".format(filename, tuple(item['Name'].int() for item in resource_Languages['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        resource_Name = resource_Languages.getparent(pecoff.portable.resources.IMAGE_RESOURCE_DIRECTORY_ENTRY)
        print_("No version record found in file {:s} for entry ({!s}) with the requested language ({!s}).".format(filename, resource_Name.Name(), opts.resource), file=sys.stderr)
        sys.exit(1)
    else:
        versionInfo = resource_Version['OffsetToData'].d

    # parse the version info and check its size
    viresource = versionInfo.l
    vi = viresource.new(pecoff.portable.resources.VS_VERSIONINFO, offset=viresource.getoffset())
    vi = vi.l
    if vi['Unknown'].size():
        Fhex, unknown = operator.methodcaller('encode', 'hex') if sys.version_info.major < 3 else bytes.hex, vi['Unknown'].serialize()
        logging.warning("Error parsing {:d} bytes from the version information: {:s}".format(vi['Unknown'].size(), Fhex(unknown)))
    if viresource.size() != vi.size():
        logging.warning("Found {:d} extra bytes in the resource directory that could be padding as it was not decoded as part of the version information".format(viresource.size() - vi.size()))
        extra = vi['Unknown'].load(length=viresource.size() - vi.size())
        logging.warning("{:X}: {!s}".format(extra.getoffset(), ' '.join(map("{:02X}".format, bytearray(extra.serialize())))))

    # extract the language/codepage ids from the version info
    lgcpids = extractLgCpIds(vi)
    if opts.list_lgcp:
        print_('Dumping language/codepage identifiers as requested by user:', file=sys.stderr)
        print_(json.dumps([{"language": lg, "codepage": cp} for lg, cp in lgcpids]), file=sys.stdout)
        sys.exit(0)

    # if the user wants to use the tagVS_FIXEDFILEINFO structure, then we'll
    # just initialize the property dictionary here.
    ffi, properties = vi['Value'], {}
    if opts.use_fixedfileinfo:
        properties['ProductVersion'] = ffi['dwProductVersion'].str()
        properties['FileVersion'] = ffi['dwFileVersion'].str()
        properties['Platform'] = ffi['dwFileOS'].field('PLATFORM').str()
        properties['OperatingSystem'] = ffi['dwFileOS'].field('OS').str()
        properties['FileType'] = ffi['dwFileType'].str()
        properties['FileSubtype'] = ffi['dwFileSubType'].str()
        properties['OriginalFilename'] = os.path.basename(filename)
        properties['OriginalFilename~upper'] = os.path.basename(filename).upper()
        properties['OriginalFilename~lower'] = os.path.basename(filename).lower()

    # otherwise we just extract the properties from the string table
    else:
        # check how many language/codepage identifiers we have. if we have
        # more than one, then we have to depend on the user to choose which one.
        if len(lgcpids) > 1:
            language = opts.resource if opts.lgid is None else opts.lgid
            if language is None:
                lg, _ = locale.getlocale()
                if lg:
                    lgid = next((id for id, lang in locale.windows_locale.items() if lang == lg), None)
                    if lgid is not None:
                        print_("More than one language identifier ({:s}) has been found in file {:s}. Filtering them using the language from the default locale {:s} ({:d}).".format(', '.join(map("{:d}".format, (lg for lg, _ in lgcpids))), filename, lg, lgid), file=sys.stderr)
                    language = lgid

            choices = [cp for lg,cp in lgcpids if lg == language] if opts.codepage is None else [opts.codepage]
            if len(choices) != 1:
                print_("More than one codepage identifier ({:s}) was found in file {:s}. Use --list to list the language/codepage identifiers available and choose one or use -h for more information.".format(', '.join(map("{:d}".format, choices)), filename), file=sys.stderr)
                sys.exit(1)
            codepage, = choices

            identifier = language, codepage
            if identifier not in lgcpids:
                print_("The specified language/codepage identifier {!s} does not exist in file {:s}. Use --list to list the identifiers that are available or use -h for more information.".format(identifier, filename), file=sys.stderr)
                sys.exit(1)

        # otherwise, we can just use the only language/codepage that was there
        else:
            identifier, = lgcpids

            # if the user tried to explicitly specify one, then let them know that
            # we didn't need their help figuring out the string table.
            choices = [("language ({:d})", opts.lgid), ("codepage ({:d})", opts.codepage)]
            if any(item is not None for _, item in choices):
                chosen = (spec.format(item) for spec, item in choices if item is not None)
                print_("Ignoring the requested {:s} as only one identifier {!s} was found in file {:s}.".format(' and '.join(chosen), identifier, filename), file=sys.stderr)

        # extract the properties for the language/codepage from the string table
        try:
            stringTable = getStringFileInfo(vi, identifier)
        except KeyError:
            print_("The StringFileInfo table in {:s} for the chosen language/codepage identifier {!s} has no available properties.".format(filename, identifier), file=sys.stderr)
            sys.exit(1)
        properties = {item['szKey'].str() : item['Value'].str() for item in stringTable}

        # uppercase and lowercase any properties that end with "name".
        candidates = [ szKey for szKey in properties if szKey.lower().endswith('name') ]
        [ properties.setdefault("{:s}~upper".format(key), properties[key].upper()) for key in candidates ]
        [ properties.setdefault("{:s}~lower".format(key), properties[key].lower()) for key in candidates ]

        # now we'll add the VS_FIXEDFILEINFO fields to our list of properties.
        fixedproperties = properties.setdefault(u'VS_FIXEDFILEINFO', {})
        fixedproperties[u'dwProductVersion'] = ffi['dwProductVersion'].str()
        fixedproperties[u'dwFileVersion'] = ffi['dwFileVersion'].str()
        fixedproperties[u'dwFileOS'] = {u'PLATFORM': ffi['dwFileOS'].field('PLATFORM').str(), u'OS': ffi['dwFileOS'].field('OS').str()}
        fixedproperties[u'dwFileType'] = ffi['dwFileType'].str()
        #fixedproperties[u'dwFileSubtype'] = {u'langID': "{:x}".format(ffi['dwFileSubtype']['langID']), u'charsetID': "{:x}".format(ffi['dwFileSubType']['charsetID'])}
        fixedproperties[u'dwFileSubtype'] = {key: "{:x}".format(ffi['dwFileSubtype'][key]) for key in [u'langID', u'charsetID'] if key in ffi['dwFileSubType']}
        fixedproperties[u'dwFileDateMS'] = "{:x}".format(ffi['dwFileDateMS'])
        fixedproperties[u'dwFileDateLS'] = "{:x}".format(ffi['dwFileDateLS'])

    properties.setdefault(u'__path__', filename)
    properties.setdefault(u'__name__', os.path.basename(filename))
    properties.setdefault(u'__name__~upper', os.path.basename(filename).upper())
    properties.setdefault(u'__name__~lower', os.path.basename(filename).lower())
    properties.setdefault(u'__machine__', pe['FileHeader']['Machine'].str())

    # add the timestamps for creation, modification, and access.
    timeformat = lambda ts: u"{:02d}{:02d}{:02d}".format(ts.hour, ts.minute, ts.second)
    dateformat = lambda ts: u"{:04d}{:02d}{:02d}".format(ts.year, ts.month, ts.day)

    # we discard the microseconds here with math.trunc so that the isoformat length is constant
    ctime, mtime, atime = (datetime.datetime.fromtimestamp(math.trunc(F(filename))) for F in [os.path.getctime, os.path.getmtime, os.path.getatime])
    ctimestamp, mtimestamp, atimestamp = (datetime.datetime.fromtimestamp(F(filename)) for F in [os.path.getctime, os.path.getmtime, os.path.getatime])
    properties.setdefault(u'__ctime__', {u'datetime' : 'T'.join(format(ctime) for format in [dateformat, timeformat]), u'date': dateformat(ctime), u'time': timeformat(ctime), u'iso': ctime.isoformat(), u'year': "{:04d}".format(ctime.year), u'month': "{:02d}".format(ctime.month), u'day': "{:02d}".format(ctime.day), u'hour': "{:02d}".format(ctime.hour), u'minute': "{:02d}".format(ctime.minute), u'second': "{:02d}".format(ctime.second), u'usecond': "{:06d}".format(ctimestamp.microsecond)})
    properties.setdefault(u'__mtime__', {u'datetime' : 'T'.join(format(mtime) for format in [dateformat, timeformat]), u'date': dateformat(mtime), u'time': timeformat(mtime), u'iso': mtime.isoformat(), u'year': "{:04d}".format(mtime.year), u'month': "{:02d}".format(mtime.month), u'day': "{:02d}".format(mtime.day), u'hour': "{:02d}".format(mtime.hour), u'minute': "{:02d}".format(mtime.minute), u'second': "{:02d}".format(mtime.second), u'usecond': "{:06d}".format(mtimestamp.microsecond)})
    properties.setdefault(u'__atime__', {u'datetime' : 'T'.join(format(atime) for format in [dateformat, timeformat]), u'date': dateformat(atime), u'time': timeformat(atime), u'iso': atime.isoformat(), u'year': "{:04d}".format(atime.year), u'month': "{:02d}".format(atime.month), u'day': "{:02d}".format(atime.day), u'hour': "{:02d}".format(atime.hour), u'minute': "{:02d}".format(atime.minute), u'second': "{:02d}".format(atime.second), u'usecond': "{:06d}".format(atimestamp.microsecond)})

    # if we were asked to dump the available properties, then do just that.
    if opts.dump:
        print_('Dumping the available properties as requested by user:', file=sys.stderr)
        print_(json.dumps(properties), file=sys.stdout)
        sys.exit(0)

    # format the path according to the filesystem encoding
    res = sys.getfilesystemencoding()
    make_object = lambda name, dictionary: type(name, (object,), {key : (make_object(key, value) if isinstance(value, dict) else value) for key, value in dictionary.items()})
    encoded = { attribute : (make_object(attribute, property) if isinstance(property, dict) else property) for attribute, property in properties.items() }

    path = opts.format.format(**encoded)
    if path.endswith(os.path.sep):
        print_("The generated path ({!s}) ends with the path separator {!r} and is thus considered an invalid path".format(path, os.path.sep), file=sys.stderr)
        sys.exit(1)
    print_(path, file=sys.stdout)
    sys.exit(0)
