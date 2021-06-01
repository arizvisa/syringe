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

def getStringTable(versionInfo, pack_LgidCp):
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
        self.add_option('', '--langid', default=None, type='int', help='use the specified language-id')
        self.add_option('', '--codepage', default=None, type='int', help='use the specified codepage')

        # fields
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
        six.print_('File %s does not appear to be an executable'% filename, file=sys.stderr)
        sys.exit(1)
    if resource_address.int() == 0:
        six.print_('File %s does not contain a resource datadirectory entry'% filename, file=sys.stderr)
        sys.exit(1)
    resource = resource_address.d.li

    # save it somewhere
    pe = resource.getparent(pecoff.IMAGE_NT_HEADERS)

    # parse the resource names
    VERSION_INFO = 16
    if VERSION_INFO not in resource.List():
        six.print_('File %s does not appear to contain a VERSION_INFO entry within its resources directory.'% filename, file=sys.stderr)
        sys.exit(1)

    try:
        resource_Names = resource.Entry(VERSION_INFO).l
    except AttributeError:
        six.print_('No resource entry in %s that matches VERSION_INFO : %r'%(filename, VERSION_INFO), file=sys.stderr)
        sys.exit(1)
    if opts.dump_names:
        six.print_('\n'.join(map(repr,resource_Names.Iterate())), file=sys.stdout)
        sys.exit(0)

    # parse the resource languages
    try:
        if opts.name is not None:
            resource_Languages = resource_Names.Entry(opts.name).l
        else:
            if resource_Names['NumberOfIdEntries'].int() != 1:
                raise IndexError
            resource_Languages = resource_Names['Ids'][0]['Entry'].d.l
            six.print_('Defaulting to the only language entry: %d'%(resource_Names['Ids'][0]['Name'].int()), file=sys.stderr)
    except IndexError:
        six.print_('More than one name found in %s : %r'%(filename, tuple(n['Name'].int() for n in resource_Names['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        six.print_('No resource found in %s with the requested name : %r'%(filename, opts.name), file=sys.stderr)
        sys.exit(1)
    if opts.dump_languages:
        six.print_('\n'.join(map(repr,resource_Languages.Iterate())), file=sys.stdout)
        sys.exit(0)

    # grab the version record
    try:
        if opts.language is not None:
            resource_Version = resource_Languages.Entry(opts.language).l
        else:
            if resource_Languages['NumberOfIdEntries'].int() != 1:
                raise IndexError
            resource_Version = resource_Languages['Ids'][0]['Entry'].d.l
            six.print_('Defaulting to the only version entry: %d'%(resource_Languages['Ids'][0]['Name'].int()), file=sys.stderr)

    except IndexError:
        six.print_('More than one language found in %s : %r'%(filename, tuple(n['Name'].int() for n in resource_Languages['Ids'])), file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        six.print_('No version record found in %s for the specified language : %r'%(filename, opts.language), file=sys.stderr)
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
        six.print_('\n'.join(map(repr,lgcpids)), file=sys.stdout)
        sys.exit(0)

    # if we have to choose, figure out which language,codepage to find
    if len(lgcpids) > 1:
        language = opts.language if opts.langid is None else opts.langid
        try:
            codepage, = [cp for lg,cp in lgcpids if lg == language] if opts.codepage is None else (opts.codepage,)
        except ValueError as e:
            six.print_('More than one (language,codepage) has been found in %s. Use -d to list the ones available and choose one. Use -h for more information.'% filename, file=sys.stderr)
            sys.exit(1)
        if (language,codepage) not in lgcpids:
            six.print_('Invalid (language,codepage) in %s : %r not in %s'%(filename, (language,codepage), lgcpids), file=sys.stderr)
            sys.exit(1)
    else:
        (language,codepage), = lgcpids

    # extract the properties for the language and cp
    try:
        st = getStringTable(vi, (language,codepage))
    except KeyError:
        six.print_('(language,codepage) in %s has no properties : %r'%(filename, (language,codepage)), file=sys.stderr)
        sys.exit(1)
    else:
        strings = dict((s['szKey'].str(),s['Value'].str()) for s in st)
        strings.setdefault('__path__', filename)
        strings.setdefault('__name__', os.path.split(filename)[1])
        strings.setdefault('__machine__', pe['FileHeader']['Machine'].str())

    # build the path
    if opts.dump:
        six.print_('\n'.join(map(repr, strings.items())), file=sys.stdout)
        sys.exit(0)

    res = sys.getfilesystemencoding()
    encoded = { k : v for k, v in six.iteritems(strings) }

    path = opts.format.format(**encoded)
    six.print_(path, file=sys.stdout)
    sys.exit(0)
