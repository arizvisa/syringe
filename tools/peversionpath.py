#!/usr/bin/env python
import itertools,logging,optparse,os.path
import ptypes,pecoff
from ptypes import *

#Type = 16       # Version Info
#Name = 1        # Name
#Language = 1033 # English

def parseResourceDirectory(filename):
    mz = pecoff.Executable.open(filename, mode='r')
    pe = mz['Next']['Header']
    sections = pe['Sections']
    datadirectory = pe['DataDirectory']
    resourceDirectory = datadirectory[2]
    return resourceDirectory['Address'].d

def extractLgCpIds(versionInfo):
    _,vfi = versionInfo['Children']
    vfi = vfi['Child']
    res = (val.cast(parray.type(_object_=pint.uint16_t,length=2)) for val in itertools.chain( *(var['Child']['Value'] for var in vfi['Children']) ))
    return tuple((cp.num(),lg.num()) for cp,lg in res)

def getStringTable(versionInfo, (Lgid, Cp)):
    sfi,_ = versionInfo['Children']
    sfi = sfi['Child']
    LgidCp = '{:04X}{:04X}'.format(Lgid,Cp)
    for st in sfi['Children']:
        st = st['Child']
        if st['szKey'].str().upper() == LgidCp:
            return [s['Child'] for s in st['Children']]
        continue
    raise KeyError, (Lgid,Cp)

class help(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        self.usage = '%prog executable'

        # resources
        self.add_option('', '--dump-names', default=False, action='store_true', help='dump the VERSION_INFO name resources available')
        self.add_option('', '--name', default=1, type='int', help='use the specified resource name')
        self.add_option('', '--dump-languages', default=False, action='store_true', help='dump the VERSION_INFO language resources available')
        self.add_option('', '--language', default=1033, type='int', help='use the specified resource language')
    
        # VS_VERSIONINFO
        self.add_option('', '--list', default=False, action='store_true', help='dump the language-id+codepages available')
        self.add_option('', '--langid', default=None, type='int', help='use the specified language-id')
        self.add_option('', '--codepage', default=None, type='int', help='use the specified codepage')

        # fields
        self.add_option('-d', '--dump', default=False, action='store_true', help='dump the properties available')
        self.add_option('-f', '--format', default='{ProductVersion}/{OriginalFilename}', type='str', help='output the specified format (defaults to {ProductVersion}/{OriginalFilename})')
        self.description = 'If path-format is not specified, grab the VS_VERSIONINFO out of the executable\'s resource. Otherwise output ``path-format`` using the fields from the VS_VERSIONINFO\'s string table'

help = help()

if __name__ == '__main__':
    import sys,logging

    opts,args = help.parse_args(sys.argv)
    try:
        filename = args.pop(1)

    except:
        help.print_help()
        sys.exit(0)
    
    # parse the executable
    try:
        resource = parseResourceDirectory(filename)
    except ptypes.error.LoadError, e:
        print >>sys.stderr, 'File %s does not appear to be an executable'% filename
        sys.exit(1)
    if resource.getoffset() == 0:
        print >>sys.stderr, 'File %s does not contain a resource datadirectory entry'% filename
        sys.exit(1)
    resource = resource.l

    # parse the resource names
    VERSION_INFO = 16
    if VERSION_INFO not in resource.list():
        print >>sys.stderr, 'File %s does not appear to contain a VERSION_INFO entry within it\'s resources directory.'% filename
        sys.exit(1)

    try:
        resource_Names = resource.entry(VERSION_INFO).l
    except AttributeError:
        print >>sys.stderr, 'No resource entry in %s that matches VERSION_INFO : %r'%(filename, VERSION_INFO)
        sys.exit(1)
    if opts.dump_names:
        print >>sys.stdout, '\n'.join(map(repr,resource_Names.iterate()))
        sys.exit(0)

    # parse the resource languages
    try:
        resource_Languages = resource_Names.getEntry(opts.name).l
    except AttributeError:
        print >>sys.stderr, 'No resource found in %s with the requested name : %r'%(filename, opts.name)
        sys.exit(1)
    if opts.dump_languages:
        print >>sys.stdout, '\n'.join(map(repr,resource_Languages.iterate()))
        sys.exit(0)

    # grab the version record
    try:
        resource_Version = resource_Languages.getEntry(opts.language).l
    except AttributeError:
        print >>sys.stderr, 'No version record found in %s for the specified language : %r'%(filename, opts.language)
        sys.exit(1)
    else:
        versionInfo = resource_Version['Data'].d

    # parse the version info
    vi = versionInfo.l.cast(pecoff.portable.resources.VS_VERSIONINFO)
    lgcpids = extractLgCpIds(vi)
    if opts.list:
        print >>sys.stdout, '\n'.join(map(repr,lgcpids))
        sys.exit(0)

    # if we have to choose, figure out which language,codepage to find
    if len(lgcpids) > 1:
        language = opts.language if opts.langid is None else opts.langid
        try:
            codepage, = [cp for lg,cp in lgcpids if lg == language] if opts.codepage is None else (opts.codepage,)
        except ValueError, e:
            print >>sys.stderr, 'More than one (language,codepage) has been found in %s. Use -d to list the ones available and choose one. Use -h for more information.'% filename
            sys.exit(1)
        if (language,codepage) not in lgcpids:
            print >>sys.stderr, 'Invalid (language,codepage) in %s : %r not in %s'%(filename, (language,codepage), lgcpids)
            sys.exit(1)
    else:
        (language,codepage), = lgcpids

    # extract the properties for the language and cp
    try:
        st = getStringTable(vi, (language,codepage))
    except KeyError:
        print >>sys.stderr, '(language,codepage) in %s has no properties : %r'%(filename, (language,codepage))
        sys.exit(1)
    else:
        strings = dict((s['szKey'].str(),s['Value'].str()) for s in st)
        strings.setdefault('__path__', filename)
        strings.setdefault('__name__', os.path.split(filename)[1])

    # build the path
    if opts.dump:
        print >>sys.stdout, '\n'.join(repr(x) for x in strings.items())
        sys.exit(0)

    path = opts.format.format(**strings)
    print >>sys.stdout, path
    sys.exit(0)

