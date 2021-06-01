#!/usr/bin/env python
import itertools,logging,optparse,os.path
import ptypes,pecoff
from ptypes import *

import six

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

def extractLgCpIds(versionInfo):
    vfi = getChildByKey(versionInfo, u'VarFileInfo')
    sfi = getChildByKey(versionInfo, u'StringFileInfo')
    fichildren = itertools.chain(vfi['Children'], sfi['Children'])
    res = (val.cast(parray.type(_object_=pint.uint16_t,length=2)) for val in itertools.chain( *(var['Value'] for var in fichildren) ))
    return tuple((cp.int(), lg.int()) for cp, lg in res)

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
        self.usage = '%prog executable'

        self.add_option('', '--dump-names', default=False, action='store_true', help='dump the VERSION_INFO name resources available')
        self.add_option('', '--name', default=None, type='int', help='use the specified resource name')
        self.add_option('', '--dump-languages', default=False, action='store_true', help='dump the VERSION_INFO language resources available')
        self.add_option('', '--language', default=None, type='int', help='use the specified resource language')

        # VS_VERSIONINFO
        self.add_option('', '--list', default=False, action='store_true', help='dump the language-id+codepages available')
        self.add_option('-l', '--langid', default=None, type='int', help='use the specified language-id')
        self.add_option('-c', '--codepage', default=None, type='int', help='use the specified codepage')

        # fields
        self.add_option('-u', '--use-fixedfileinfo', default=False, action='store_true', help='use the VS_FIXEDFILEINFO structure instead of the string table')
        self.add_option('-d', '--dump', default=False, action='store_true', help='dump the properties available')
        self.add_option('-f', '--format', default='{__name__}/{ProductVersion}/{OriginalFilename}', type='str', help='output the specified format (defaults to {__name__}/{ProductVersion}/{OriginalFilename})')
        self.description = 'If ``path-format`` is not specified, grab the VS_VERSIONINFO out of the executable\'s resource. Otherwise output ``path-format`` using the fields from the VS_VERSIONINFO\'s string table.'

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
        six.print_("File {:s} does not appear to be an executable.".format(filename), file=sys.stderr)
        sys.exit(1)
    if resource_address.int() == 0:
        six.print_("File {:s} does not contain a resource data directory entry.".format(filename), file=sys.stderr)
        sys.exit(1)
    resource = resource_address.d.li

    # save it somewhere
    pe = resource.getparent(pecoff.IMAGE_NT_HEADERS)

    # parse the resource names
    VERSION_INFO = 16
    if VERSION_INFO not in resource.List():
        six.print_("File {:s} does not appear to contain a VERSION_INFO ({:d}) entry within its resource directory.".format(filename, VERSION_INFO), file=sys.stderr)
        sys.exit(1)

    try:
        resource_Names = resource.Entry(VERSION_INFO).l
    except AttributeError:
        six.print_("No entries for VERSION_INFO ({:d}) in the resource directory from file {:s}.".format(VERSION_INFO, filename), file=sys.stderr)
        sys.exit(1)
    if opts.dump_names:
        six.print_('Dumping the name table entries from the resource directory as requested by user:', file=sys.stderr)
        six.print_('\n'.join(map("{!s}".format, resource_Names.iterate())), file=sys.stdout)
        sys.exit(0)

    # parse the resource languages from the resource name
    try:
        if opts.name is not None:
            resource_Languages = resource_Names.Entry(opts.name).l
        else:
            if resource_Names['NumberOfIdEntries'].int() != 1:
                raise IndexError
            resource_Languages = resource_Names['Ids'][0]['Entry'].d.l
            six.print_("Defaulting to the only available language entry: {:d}".format(resource_Names['Ids'][0]['Name'].int()), file=sys.stderr)
    except IndexError:
        six.print_("More than one entry was found under VERSION_INFO ({:d}) in file {:s}: {!s}".format(VERSION_INFO, filename, tuple(item['Name'].int() for item in resource_Names['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        six.print_("No resource found in file {:s} with the requested name ({!s}).".format(filename, opts.name), file=sys.stderr)
        sys.exit(1)
    if opts.dump_languages:
        six.print_('Dumping the language entries from the resource name table as requested by user:', file=sys.stderr)
        six.print_('\n'.join(map("{!s}".format, resource_Languages.iterate())), file=sys.stdout)
        sys.exit(0)

    # grab the version record from the resource language
    try:
        if opts.language is not None:
            resource_Version = resource_Languages.entry(opts.language).l
        else:
            if resource_Languages['NumberOfIdEntries'].int() != 1:
                raise IndexError
            resource_Version = resource_Languages['Ids'][0]['Entry'].d.l
            six.print_("Defaulting to the only available language entry: {:d}".format(resource_Languages['Ids'][0]['Name'].int()), file=sys.stderr)

    except IndexError:
        six.print_("More than one language entry was found in file {:s}: {!s}".format(filename, tuple(item['Name'].int() for item in resource_Languages['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        resource_Name = resource_Languages.getparent(pecoff.portable.resources.IMAGE_RESOURCE_DIRECTORY_ENTRY)
        six.print_("No version record found in file {:s} for entry ({!s}) with the requested language ({!s}).".format(filename, resource_Name.Name(), opts.language), file=sys.stderr)
        sys.exit(1)
    else:
        versionInfo = resource_Version['OffsetToData'].d

    # parse the version info and check its size
    viresource = versionInfo.l
    vi = viresource.new(pecoff.portable.resources.VS_VERSIONINFO, offset=viresource.getoffset()).load(offset=0, source=ptypes.provider.proxy(viresource))
    vi.setoffset(vi.getoffset(), recurse=True)
    if vi['Unknown'].size():
        Fhex, unknown = operator.methodcaller('encode', 'hex') if sys.version_info.major < 3 else bytes.hex, vi['Unknown'].serialize()
        logging.warning("Error parsing {:d} bytes from the version information: {:s}".format(vi['Unknown'].size(), Fhex(unknown)))
    if viresource.size() != vi.size():
        logging.warning("Found {:d} extra bytes in the resource that could be padding as it was not decoded as part of the version information".format(viresource.size() - vi.size()))
        extra = vi['Unknown'].load(length=viresource.size() - vi.size())
        logging.warning("{!s}".format(extra))

    # extract the language/codepage ids from the version info
    lgcpids = extractLgCpIds(vi)
    if opts.list:
        six.print_('Dumping language/codepage identifiers as requested by user:', file=sys.stderr)
        six.print_('\n'.join(map("{!s}".format, lgcpids)), file=sys.stdout)
        sys.exit(0)

    # if the user wants to use the tagVS_FIXEDFILEINFO structure, then we'll
    # just initialize the property dictionary here.
    ffi = vi['Value']
    if opts.use_fixedfileinfo:
        properties = {}
        properties['ProductVersion'] = ffi['dwProductVersion'].str()
        properties['FileVersion'] = ffi['dwFileVersion'].str()
        properties['Platform'] = ffi['dwFileOS'].item('PLATFORM').str()
        properties['OperatingSystem'] = ffi['dwFileOS'].item('OS').str()
        properties['FileType'] = ffi['dwFileType'].str()
        properties['FileSubtype'] = ffi['dwFileSubType'].str()
        properties['OriginalFilename'] = filename

    # otherwise we just extract the properties from the string table
    else:
        # check how many language/codepage identifiers we have. if we have
        # more than one, then we have to depend on the user to choose which one.
        if len(lgcpids) > 1:
            language = opts.language if opts.langid is None else opts.langid
            try:
                codepage, = [cp for lg,cp in lgcpids if lg == language] if opts.codepage is None else (opts.codepage,)
            except ValueError as e:
                six.print_("More than one language/codepage identifier has been found in file {:s}. Use --list to list the ones available and choose one or use -h for more information.".format(filename), file=sys.stderr)
                sys.exit(1)
            identifier = language, codepage
            if identifier not in lgcpids:
                six.print_("The specified language/codepage identifier {!s} does not exist in file {:s}. Use --list to list the identifiers that are available or use -h for more information.".format(identifier, filename), file=sys.stderr)
                sys.exit(1)

        # otherwise, we can just use the only language/codepage that was there
        else:
            identifier, = lgcpids

            # if the user tried to explicitly specify one, then let them know that
            # we didn't need their help figuring out the string table.
            choices = [("language ({:d})", opts.langid), ("codepage ({:d})", opts.codepage)]
            if any(item is not None for _, item in choices):
                chosen = (spec.format(item) for spec, item in choices if item is not None)
                six.print_("Ignoring the requested {:s} as only one identifier {!s} was found in file {:s}.".format(' and '.join(chosen), identifier, filename), file=sys.stderr)

        # extract the properties for the language/codepage from the string table
        try:
            stringTable = getStringFileInfo(vi, identifier)
        except KeyError:
            six.print_("The StringFileInfo table in {:s} for the chosen language/codepage identifier {!s} has no available properties.".format(filename, identifier), file=sys.stderr)
            sys.exit(1)
        properties = {item['szKey'].str() : item['Value'].str() for item in stringTable}

    properties.setdefault('__path__', filename)
    properties.setdefault('__name__', os.path.split(filename)[1])
    properties.setdefault('__machine__', pe['FileHeader']['Machine'].str())

    # if we were asked to dump the available properties, then do just that.
    if opts.dump:
        six.print_('Dumping the available properties as requested by user:', file=sys.stderr)
        six.print_('\n'.join(map("{!s}".format, properties.items())), file=sys.stdout)
        sys.exit(0)

    # format the path according to the filesystem encoding
    res = sys.getfilesystemencoding()
    encoded = { attribute : property for attribute, property in properties.items() }

    path = opts.format.format(**encoded)
    six.print_(path, file=sys.stdout)
    sys.exit(0)
