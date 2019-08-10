# http://www.freebsd.org/cgi/man.cgi?query=tar&sektion=5&manpath=FreeBSD+8-current
import ptypes
from ptypes import *
import operator

class stringinteger(pstr.string):
    def int(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = int(res)
        except ValueError: res = 0
        return res
    def long(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = long(res)
        except ValueError: res = 0
        return res
    __int__ = int
    def set(self, integer):
        n = str(integer)
        prefix = '0'*(self.length-1 - len(n))
        return super(stringinteger,self).set(prefix+n+'\x00')

class stringoctal(stringinteger):
    def int(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = int(res,8)
        except ValueError: res = 0
        return res
    def long(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = long(res,8)
        except ValueError: res = 0
        return res

    def set(self, integer):
        n = oct(integer)[1:]
        prefix = '0'*(self.length-1 - len(n))
        return super(stringoctal,self).set(prefix+n+'\x00')

class stream_t(parray.infinite):
    def summary(self):
        return '%s size: %x, %d files.'% (self._object_.typename(), self.size(), len(self))

    def isTerminator(self, value):
        return value.iseof()

class linkflag(pint.enum, pstr.char_t):
    _values_ = [(_, ord(n)) for _,n in [
        ('REGTYPE',  '0'),  # regular file
        ('AREGTYPE', '\0'), # regular file
        ('LNKTYPE',  '1'),  # link
        ('SYMTYPE',  '2'),  # reserved
        ('CHRTYPE',  '3'),  # character special
        ('BLKTYPE',  '4'),  # block special
        ('DIRTYPE',  '5'),  # directory (in this case, the size field has no meaning)
        ('FIFOTYPE', '6'),  # FIFO special (archiving a FIFO file archives its existence, not contents)
        ('CONTTYPE', '7'),  # reserve
    ]]

class header_t(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string,length=100), 'filename'),
        (dyn.clone(stringoctal,length=8), 'mode'),
        (dyn.clone(stringoctal,length=8), 'uid'),
        (dyn.clone(stringoctal,length=8), 'gid'),
        (dyn.clone(stringoctal,length=12), 'size'),
        (dyn.clone(stringoctal,length=12), 'mtime'),
        (dyn.clone(stringoctal,length=8), 'checksum'),
        (linkflag, 'linkflag'),
        (dyn.clone(pstr.string,length=100), 'linkname'),
    ]

    def listing(self):
        name = self['filename'].str()
        mode = self['mode'].int()
        uid,gid = self['uid'].int(),self['gid'].int()
        size = self['size'].int()
        mtime,checksum = self['mtime'].int(),self['checksum'].int()
        return '{!r} mode={:04o} uid={:d} gid={:d} size=0x{:x} mtime={:x} checksum={:x}'.format(name, mode, uid, gid, size, mtime, checksum) + (' -> {!r}'.format(self['linkname'].get()) if self['linkflag'].int() else '')

    def isempty(self):
        return self['filename'].str() == ''

# FIXME: we can auto-detect which header we are by checking 'magic'
class header_extended_t(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string,length=6), 'magic'),
        (dyn.clone(stringinteger,length=2), 'version'),
        (dyn.clone(pstr.string,length=32), 'uname'),
        (dyn.clone(pstr.string,length=32), 'gname'),
        (dyn.clone(stringinteger,length=8), 'devmajor'),
        (dyn.clone(stringinteger,length=8), 'devminor'),
    ]

    def listing(self):
        major,minor = self['devmajor'],self['devminor']
        uname = 'uname={:s}'.format(self['uname'].str()) if len(self['uname'].str()) > 0 else ''
        gname = 'gname={:s}'.format(self['gname'].str()) if len(self['uname'].str()) > 0 else ''
        device = ('dev={:s}'.format('.'.join(map(str,(major.int(),minor.int()))))) if len(major.get() + minor.get()) > 0 else ''
        res = (' ' + ' '.join(filter(None,(uname, gname, device)))) if any((uname, gname, device)) else ''
        return 'ext v{:d}'.format(self['version'].int()) + res

class member_t(pstruct.type):
    def iseof(self):
        return all(n == '\x00' for n in self.serialize())

    def listing(self):
        index = int(self.name())
        return '{:d}) {:s}'.format(index, self['header'].listing())

    def summary(self):
        common = self['header']['common']
        filename = common['filename']
        mode = common['mode']
        uid,gid = common['uid'],common['gid']
        sz,rsz = common['size'],self['data'].size()
        return '\n'.join(map(repr,(filename,mode,uid,gid,sz))) + '\n' + self['data'].hexdump(rows=4)

### old
class header_old(pstruct.type):
    _fields_ = [
        (header_t, 'common'),
        (dyn.clone(pstr.string,length=255), 'pad'),
    ]

    def dump(self):
        return '\n'.join(map(repr,(self['common'],)))

    def listing(self):
        return self['common'].listing()

    def getsize(self):
        return self['common'].li['size'].int()

class old(stream_t):
    class member(member_t):
        _fields_=[(header_old,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

### ustar
class header_ustar(header_old):
    _fields_ = [
        (header_t, 'common'),
        (header_extended_t, 'extended'),

        (dyn.clone(pstr.string,length=155), 'prefix'),
        (dyn.block(12), 'padding'),
    ]

    def dump(self):
        prefixofs = self.getoffset('prefix')
        return '\n'.join(map(repr, (self['common'], self['extended'])) + filter(lambda n:n.startswith('[%x] '%prefixofs), self.details().split('\n')))

    def listing(self):
        return ' | '.join((self['common'].listing(), self['extended'].listing()))

    def getsize(self):
        sz = self['common'].li['size'].int()
        return (sz+511)/512*512

class ustar(stream_t):
    class member(member_t):
        _fields_=[(header_ustar,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

### gnu
class gnu_sparse(pstruct.type):
    _fields_ = [
           (dyn.clone(stringoctal,length=12), 'offset'),
           (dyn.clone(stringoctal,length=12), 'numbytes'),
    ]

class gnu_sparse_header(pstruct.type):
    _fields_ = [
        (dyn.array(gnu_sparse,21), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string,length=7), 'padding'),
    ]

class gnu_sparse_array(parray.terminated):
    _object_ = gnu_sparse_header
    def isTerminator(self, value):
        return value['isextended'].str() == '\x00'

class header_gnu(header_old):
    def __extended_data(self):
        if self['isextended'].li.str() == '\x00':
            return dyn.clone(parray.type,_object_=gnu_sparse_header)
        return gnu_sparse_array

    _fields_ = [
        (header_t, 'common'),
        (header_extended_t, 'extended'),

        (dyn.clone(stringoctal,length=12), 'atime'),
        (dyn.clone(stringoctal,length=12), 'ctime'),
        (dyn.clone(stringoctal,length=12), 'offset'),
        (dyn.clone(pstr.string,length=4), 'longnames'),
        (pstr.char_t, 'unused'),
        (dyn.array(gnu_sparse,4), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string,length=12), 'realsize'),
        (dyn.clone(pstr.string,length=17), 'pad'),
        (__extended_data, 'extended_data'),
    ]

    def dump(self):
        return '\n'.join(map(repr, (self, self['common'], self['extended'])))

    def listing(self):
        res = 'atime=0x{:x} ctime=0x{:x}'.format(self['atime'].int(), self['ctime'].int())
        return ' | '.join((self['common'].listing(), self['extended'].listing(), res))

class gnu(stream_t):
    class member(member_t):
        _fields_=[(header_gnu,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

if __name__ == '__main__':
    import sys,os,os.path,logging,argparse
    import ptypes,archive.tar
    if sys.platform == 'win32': import msvcrt

    arg_p = argparse.ArgumentParser(prog=sys.argv[0] if len(sys.argv) > 0 else 'tar.py', description="List or extract information out of a .tar file", add_help=False)
    arg_p.add_argument('FILE', nargs='*', action='append', type=str, help='list of filenames to extract')
    arg_commands_gr = arg_p.add_argument_group("Main operation mode")
    arg_commands_gr.add_argument('-h', '--help', action='store_const', help="show this help message and exit", dest='mode', const='help')
    arg_commands_gr.add_argument('-l', '--list', action='store_const', help="list the contents of an archive", dest='mode', const='list')
    arg_commands_gr.add_argument('-x', '--extract', '--get', action='store_const', help="extract files from an archive", dest='mode', const='extract')
    arg_commands_gr.add_argument('-d', '--dump', action='store_const', help="dump the specified file records", dest='mode', const='dump')
    arg_device_gr = arg_p.add_argument_group("Device selection and switching")
    arg_device_gr.add_argument('-f', '--file', nargs=1, action='store', type=str, metavar="ARCHIVE", help="use archive file or device ARCHIVE", dest='source')
    arg_device_gr.add_argument('-o', '--output', nargs=1, action='store', type=str, metavar="DEVICE", help="extract files to specified DEVICE or FORMAT", dest='target', default=None)
    arg_device_gr.add_argument('-t', '--type', nargs=1, action='store', type=str.lower, metavar="TYPE", help="specify tar type (old, ustar, gnu)", dest='type', choices=('old','ustar','gnu'), default=('ustar',))

    if len(sys.argv) <= 1:
        print >>sys.stdout, arg_p.format_usage()
        sys.exit(0)

    args = arg_p.parse_args(sys.argv[1:])
    if args.mode == 'help':
        print >>sys.stdout, arg_p.format_help()
        sys.exit(0)

    # fix up arguments
    source_a,target_a = args.source[0],None if args.target is None else args.target[0]
    if source_a == '-':
        if sys.platform == 'win32': msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        source = ptypes.prov.stream(sys.stdin)
    else:
        source = ptypes.prov.file(source_a, mode='rb')

    if target_a == '-':
        if sys.platform == 'win32': msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        target = sys.stdout
    else:
        target = target_a

    filelist, = args.FILE
    filetype, = args.type
    filelookup = set(filelist)
    indexlookup = set((int(n) for n in filelist if n.isdigit()))

    isMatchedName = lambda r: (not filelookup) or (r['header']['common']['filename'].str() in filelookup)
    isMatchedIndex = lambda r: int(r.name()) in indexlookup

    # some useful functions
    def iterate(root):
        for rec in root:
            if isMatchedIndex(rec) or isMatchedName(rec):
                yield rec
            continue
        return

    def dictionary(root):
        res = {}
        for k in root.keys():
            v = root[k]
            if isinstance(v, pint.type):
                res[k] = v.int()
            elif isinstance(v, pstr.type):
                try:
                    res[k] = v.str()
                except UnicodeDecodeError:
                    res[k] = v.serialize()
            else:
                res[k] = v.summary()
            continue
        return res

    # create the file type
    lookup = {'old': archive.tar.old, 'ustar': archive.tar.ustar, 'gnu': archive.tar.gnu}
    cls = lookup[filetype]
    z = cls(source=source)

    # implement each mode
    if args.mode == 'list':
        for rec in iterate(z.l[:-1]):
            print rec.listing()
        sys.exit(0)

    elif args.mode == 'extract':
        target = target or os.path.join('.','{path:s}','{name:s}')

    elif args.mode == 'dump':
        target = target or sys.stdout

    # help
    else:
        print >>sys.stdout, arg_p.format_help()
        sys.exit(1)

    # for each member...
    for rec in iterate(z.l[:-1]):

        # assign what data we're writing
        if args.mode == 'extract':
            sz = rec['header'].getsize()
            data = rec['data'].serialize()[:sz]
        elif args.mode == 'dump':
            data = '\n'.join((' '.join((ptypes.utils.repr_class(rec.classname()),rec.name())), ptypes.utils.indent(rec['header'].dump())))

        # set some reasonable defaults
        res = dictionary(rec['header']['common'])
        res['index'] = int(rec.name())
        res['path'],res['name'] = os.path.split(res['filename'].replace('/', os.sep))

        # write to a generated filename
        if isinstance(target, basestring):
            outname = target.format(**res)

            dirpath,name = os.path.split(outname)
            dirpath and not os.path.isdir(dirpath) and os.makedirs(dirpath)

            res = os.path.join(dirpath, name)
            if res.endswith(os.path.sep):
                if os.path.isdir(res):
                    logging.warn("Unable to create already existing subdirectory for record : {:d} : {:s}".format(int(rec.name()), res))
                else:
                    logging.info("Creating subdirectory due to member : {:d} : {:s}".format(int(rec.name()), res))
                    os.makedirs(res)
                continue

            if os.path.exists(res):
                logging.warn("Overwriting already existing file due to member : {:d} : {:s}".format(int(rec.name()), res))
            else:
                logging.info("Creating file for member : {:d} : {:s}".format(int(rec.name()), res))

            with file(res, 'wb') as out: print >>out, data

        # fall-back to writing to already open target
        else:
            print >>target, data
        continue

    sys.exit(0)

