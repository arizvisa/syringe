# http://www.freebsd.org/cgi/man.cgi?query=tar&sektion=5&manpath=FreeBSD+8-current
import ptypes
from ptypes import *
import sys, operator, six

BLOCKSIZE = 2**9
largeinteger = long if sys.version_info.major < 3 else int

class stringinteger(pstr.string):
    def int(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = largeinteger(res)
        except ValueError: res = 0
        return res

    def set(self, integer):
        n = str(integer)
        prefix = '0' * (self.length - 1 - len(n))
        return super(stringinteger, self).set(prefix + n + '\0')

    def summary(self):
        res = super(stringinteger, self).summary()
        return "{:s} :> {:d}".format(res, self.int())

class stringoctal(stringinteger):
    def int(self):
        try: res = self.str()
        except UnicodeDecodeError: res = self.get()
        try: res = largeinteger(res, 8)
        except ValueError: res = 0
        return res

    def set(self, integer):
        n = oct(integer)[1:]
        prefix = '0' * (self.length - 1 - len(n))
        return super(stringoctal, self).set(prefix + n + '\0')

class padstring(pstr.string):
    def str(self):
        res = super(padstring, self).str()
        return res.rstrip()

class stream_t(parray.infinite):
    def summary(self):
        return "{:s} size: {:#x}, {:d} files.".format(self._object_.typename(), self.size(), len(self))

    def isTerminator(self, value):
        return value.iseof()

class linkflag_t(pstr.char_t):
    def get(self):
        return self.int()

class linkflag(pint.enum, linkflag_t):
    _values_ = [
        ('REGTYPE',  b'0'),  # regular file
        ('AREGTYPE', b'\0'), # regular file
        ('LNKTYPE',  b'1'),  # link
        ('SYMTYPE',  b'2'),  # reserved
        ('CHRTYPE',  b'3'),  # character special
        ('BLKTYPE',  b'4'),  # block special
        ('DIRTYPE',  b'5'),  # directory (in this case, the size field has no meaning)
        ('FIFOTYPE', b'6'),  # FIFO special (archiving a FIFO file archives its existence, not contents)
        ('CONTTYPE', b'7'),  # reserve
    ]
    _values_ = [(_, six.byte2int(by)) for _, by in _values_]

class common_t(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=100), 'filename'),
        (dyn.clone(stringoctal, length=8), 'mode'),
        (dyn.clone(stringinteger, length=8), 'uid'),
        (dyn.clone(stringinteger, length=8), 'gid'),
        (dyn.clone(stringoctal, length=12), 'size'),
        (dyn.clone(stringoctal, length=12), 'mtime'),
        (dyn.clone(stringoctal, length=8), 'checksum'),
        (linkflag, 'linkflag'),
        (dyn.clone(pstr.string, length=100), 'linkname'),
    ]

    def summary(self):
        filename = self['filename'].str().encode('unicode_escape').decode(sys.getdefaultencoding())
        mode, uid, gid, sz = (self[fld] for fld in ['mode', 'uid', 'gid', 'size'])
        mtime, checksum = (self[fld] for fld in ['mtime', 'checksum'])
        return "filename=\"{:s}\" size={:#x} mode={:04d} uid={:d} gid={:d} mtime={:#x} checksum={:#x} linkflag={:s}{:s}".format(filename.replace('"', '\\"'), sz.int(), mode.int(), uid.int(), gid.int(), mtime.int(), checksum.int(), self['linkflag'].summary(), " linkname={:s}".format(self['linkname'].str()) if self['linkflag']['LNKTYPE'] else '')

    def isempty(self):
        return False

    def listing(self):
        name = self['filename'].str().encode('unicode_escape').decode(sys.getdefaultencoding())
        mode = self['mode'].int()
        uid, gid = self['uid'].int(), self['gid'].int()
        size = self['size'].int()
        mtime, checksum = self['mtime'].int(), self['checksum'].int()
        return "\"{:s}\" {:s} size={:#x} mode={:04o} uid={:d} gid={:d} mtime={:#x} checksum={:#x}".format(name.replace('"', '\\"'), self['linkflag'].summary(), size, mode, uid, gid, mtime, checksum) + (" -> {:s}".format(self['linkname'].str().encode('unicode_escape').decode(sys.getdefaultencoding())) if self['linkflag']['LNKTYPE'] else '')

### Extended headers
class header(ptype.definition):
    attribute, cache = 'magic', {}
class header_member(ptype.definition):
    attribute, cache = 'magic', {}

# FIXME: we can auto-detect which header we are by checking 'magic'
class extended_t(pstruct.type):
    _fields_ = [
        (dyn.clone(stringinteger, length=2), 'version'),
        (dyn.clone(pstr.string, length=32), 'uname'),
        (dyn.clone(pstr.string, length=32), 'gname'),
        (dyn.clone(stringinteger, length=8), 'devmajor'),
        (dyn.clone(stringinteger, length=8), 'devminor'),
    ]

    def summary(self):
        major, minor = self['devmajor'], self['devminor']
        uname = "uname=\"{:s}\"".format(self['uname'].str()) if len(self['uname'].str()) > 0 else ''
        gname = "gname=\"{:s}\"".format(self['gname'].str()) if len(self['uname'].str()) > 0 else ''
        device = ("dev={:s}".format('.'.join(map("{:d}".format, [major.int(), minor.int()])))) if sum(map(len, {item.str() for item in [major, minor]})) > 0 else ''
        res = (' ' + ' '.join(filter(None, [uname, gname, device]))) if any({uname, gname, device}) else ''
        return "version={:d}".format(self['version'].int()) + res

    def isempty(self):
        return False

    def listing(self):
        major, minor = self['devmajor'], self['devminor']
        uname = "uname=\"{:s}\"".format(self['uname'].str()) if len(self['uname'].str()) > 0 else ''
        gname = "gname=\"{:s}\"".format(self['gname'].str()) if len(self['uname'].str()) > 0 else ''
        device = ("dev={:s}".format('.'.join(map("{:d}".format, [major.int(), minor.int()])))) if sum(map(len, {item.str() for item in [major, minor]})) > 0 else ''
        res = (' ' + ' '.join(filter(None, [uname, gname, device]))) if any({uname, gname, device}) else ''
        return "(extended) v{:d}".format(self['version'].int()) + res

class header_t(pstruct.type):
    def __extended(self):
        res = self['magic'].li
        return header.lookup(res.str())

    def __member(self):
        res = self['magic'].li
        return header_member.lookup(res.str())

    _fields_ = [
        (common_t, 'common'),
        (dyn.clone(padstring, length=6), 'magic'),
        (__extended, 'extended'),
        (__member, 'member'),
    ]

    def member_name(self):
        res = self['common']
        return res['filename'].str()

    def member_type(self):
        res = self['common']
        return res['linkflag']

    def member_linkname(self):
        res = self['common']
        return res['linkname'].str()

    def member_mode(self):
        res = self['common']
        return res['mode'].int()

    def member_owner(self):
        res = self['common']
        return res['uid'].int(), res['gid'].int()

    def member_checksum(self):
        res = self['common']
        return res['checksum'].int()

    def member_size(self):
        res = self['extended']
        return res.member_size()

    def listing(self):
        magic, iterable = self['magic'].str(), (self[fld].listing() for fld in ['common', 'extended', 'member'] if hasattr(self[fld], 'isempty') and not self[fld].isempty())
        return "{:s}{:s}".format("<{:s}> ".format(magic.encode('unicode_escape').decode(sys.getdefaultencoding())) if magic else '', ' | '.join(iterable))

    def dump(self):
        res = []
        for item in self.traverse(filter=lambda node: isinstance(node, pstruct.type)):
            repr = "{!r}".format(item)
            res.extend(repr.split('\n'))
        return '\n'.join(res)

class member_t(pstruct.type):
    def __data(self):
        header = self['header'].li
        return dyn.block(header.member_size())

    _fields_ = [
        (header_t, 'header'),
        (__data, 'data'),
    ]

    def iseof(self):
        iterable = self.serialize()
        return all(item == '\0' for item in iterable)

    def listing(self):
        index = int(self.name())
        return "{:d}) {:s}".format(index, self['header'].listing())

    def filename(self):
        res = self['header']
        return res.member_name()

    def filemode(self):
        res = self['header']
        return res.member_mode()

    def fileowner(self):
        res = self['header']
        return res.member_owner()

    def filesize(self):
        res = self['header']['common']
        return res['size'].int()

    def data(self):
        res = self['data']
        return res.serialize()

class File(stream_t):
    _object_ = member_t

### old
@header.define
class header_old(pstruct.type):
    magic, _fields_ = '', []
    def member_size(self):
        p = self.getparent(header_t)
        res = p['common']
        return res['size'].int()

@header_member.define
class header_old_member(pstruct.type):
    magic, _fields_ = '', [
        (dyn.clone(pstr.string, length=255), 'pad'),
    ]

    def summary(self):
        padding = self['pad'].str().encode('unicode_escape').decode(sys.getdefaultencoding())
        return "pad=\"{:s}\"".format(padding.replace('"', '\\"'))

    def isempty(self):
        return self['pad'].str() == ""

    def listing(self):
        return "(header_old) {:s}".format(self.summary()) if self['pad'].str() else ''

### ustar
@header.define
class header_ustar(extended_t):
    magic = 'ustar'
    def member_size(self):
        p = self.getparent(header_t)
        res = p['common']
        count = res['size'].int()
        return count + BLOCKSIZE - (count % BLOCKSIZE) if count > 0 else 0

@header_member.define
class header_ustar_member(pstruct.type):
    magic = 'ustar'
    _fields_ = [
        (dyn.clone(pstr.string, length=155), 'prefix'),
        (dyn.block(12), 'padding'),
    ]

    def summary(self):
        prefix = self['prefix'].str().encode('unicode_escape').decode(sys.getdefaultencoding())
        return "prefix=\"{:s}\" padding={:s}".format(prefix.replace('"', '\\"'), self['padding'].summary())

    def isempty(self):
        return self['prefix'].str() == ""

    def listing(self):
        return "(header_ustar) {:s}".format(self.summary())

### gnu
class gnu_sparse(pstruct.type):
    _fields_ = [
       (dyn.clone(stringoctal, length=12), 'offset'),
       (dyn.clone(stringoctal, length=12), 'numbytes'),
    ]
    def summary(self):
        offset, numbytes = (self[fld].int() for fld in ['offset', 'numbytes'])
        return "offset={:#x} numbytes={:#x}".format(offset, numbytes)

class gnu_sparse_header(pstruct.type):
    _fields_ = [
        (dyn.array(gnu_sparse, 21), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string, length=7), 'padding'),
    ]

class gnu_sparse_array(parray.terminated):
    _object_ = gnu_sparse_header
    def isTerminator(self, value):
        return value['isextended'].str() == '\0'

@header.define
class header_gnu(extended_t):
    magic = 'gnu'
    def member_size(self):
        p = self.getparent(header_t)
        res = p['common']
        return res['size'].int()

@header_member.define
class header_gnu_member(pstruct.type):
    magic = 'gnu'
    def __extended_data(self):
        if self['isextended'].li.str() == '\0':
            return dyn.clone(parray.type, _object_=gnu_sparse_header)
        return gnu_sparse_array

    _fields_ = [
        (dyn.clone(stringoctal, length=12), 'atime'),
        (dyn.clone(stringoctal, length=12), 'ctime'),
        (dyn.clone(stringoctal, length=12), 'offset'),
        (dyn.clone(pstr.string, length=4), 'longnames'),
        (pstr.char_t, 'unused'),
        (dyn.array(gnu_sparse, 4), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string, length=12), 'realsize'),
        (dyn.clone(pstr.string, length=17), 'pad'),
        (__extended_data, 'extended_data'),
    ]

    def isempty(self):
        return False

    def listing(self):
        # TODO
        return "(header_gnu) atime={:#x} ctime={:#x} offset={:#x} longnames={:s} ...".format(self['atime'].int(), self['ctime'].int(), self['offset'].int(), self['longnames'].summary())

if __name__ == '__main__':
    import six
    import sys, os, os.path, logging, argparse, fnmatch
    import ptypes, archive.tar
    if sys.platform == 'win32': import msvcrt

    arg_p = argparse.ArgumentParser(prog=sys.argv[0] if len(sys.argv) > 0 else 'tar.py', description="List or extract information out of a .tar file", add_help=False)
    arg_p.add_argument('FILE', nargs='*', action='append', type=str, help='list of globs to filter members to extract')
    arg_commands_gr = arg_p.add_argument_group("Main operation mode")
    arg_commands_gr.add_argument('-h', '--help', action='store_const', help="show this help message and exit", dest='mode', const='help')
    arg_commands_gr.add_argument('-l', '--list', action='store_const', help="list the contents of an archive", dest='mode', const='list')
    arg_commands_gr.add_argument('-x', '--extract', '--get', action='store_const', help="extract files from an archive", dest='mode', const='extract')
    arg_commands_gr.add_argument('-d', '--dump', action='store_const', help="dump the specified file members", dest='mode', const='dump')
    arg_device_gr = arg_p.add_argument_group("Device selection and switching")
    arg_device_gr.add_argument('-f', '--file', action='store', type=argparse.FileType('rb'), default='-', metavar="ARCHIVE", help="use archive file or device ARCHIVE", dest='source')
    arg_device_gr.add_argument('-o', '--output', action='store', type=str, metavar="FORMATSPEC", help="extract members by applying attributes to specified FORMATSPEC (or DEVICE)", dest='target', default='-')

    if len(sys.argv) <= 1:
        six.print_(arg_p.format_usage(), file=sys.stdout)
        sys.exit(0)

    args = arg_p.parse_args(sys.argv[1:])
    if args.mode == 'help':
        six.print_(arg_p.format_help(), file=sys.stdout)
        sys.exit(0)

    # fix up arguments
    source_a, target_a = args.source, args.target
    if source_a == '-':
        if sys.platform == 'win32': msvcrt.setmode(source_a.fileno(), os.O_BINARY)
        source = ptypes.prov.stream(source_a)
    else:
        source = ptypes.prov.fileobj(source_a)

    if target_a == '-':
        if sys.platform == 'win32': msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        target = sys.stdout
    else:
        target = target_a

    filelist, = args.FILE
    filelookup = {item for item in filelist}
    indexlookup = {int(n) for n in filelist if n.isdigit()}

    isMatchedName = lambda record: (not filelookup) or any(fnmatch.fnmatch(record.filename(), pattern) for pattern in filelookup)
    isMatchedIndex = lambda record: int(record.name()) in indexlookup

    # some useful functions
    def iterate(root):
        for item in root:
            if isMatchedIndex(item) or isMatchedName(item):
                yield item
            continue
        return

    def dictionary(root):
        res = {}
        for k in root.keys():
            v = root[k]
            if hasattr(v, 'int'):
                res[k] = v.int()
            elif hasattr(v, 'str'):
                try:
                    res[k] = v.str()
                except UnicodeDecodeError:
                    res[k] = v.serialize()
            else:
                res[k] = v.summary()
            continue
        return res

    # create the file type
    z = archive.tar.File(source=source)

    # implement each mode
    if args.mode == 'list':
        z = z.l
        for member in iterate(z[:-1]):
            print(member.listing())
        sys.exit(0)

    elif args.mode == 'extract':
        target = target or os.path.join('.', '{path:s}', '{name:s}')

    elif args.mode == 'dump':
        target = target or sys.stdout

    # help
    else:
        six.print_(arg_p.format_help(), file=sys.stdout)
        sys.exit(1)

    # for each member...
    z = z.l
    for member in iterate(z[:-1]):

        # assign what data we're writing
        if args.mode == 'extract':
            sz = member.filesize()
            data = member.data()[:sz]

        elif args.mode == 'dump':
            magic = member['header']['magic'].str()
            data = '\n'.join((' '.join([ptypes.utils.repr_class(member.classname()), member.name()] + (["({:s})".format(magic)] if magic else [])), ptypes.utils.indent(member['header'].dump())))

        # set some reasonable defaults from each header (back2front)
        res = {}
        for key in reversed(member['header'].keys()):
            if isinstance(member['header'][key], pstruct.type):
                res.update(dictionary(member['header'][key]))
            continue
        res['index'] = int(member.name())
        res['path'], res['name'] = os.path.split(member.filename().replace('/', os.sep))

        # write to a generated filename
        if isinstance(target, six.string_types):
            outname = target.format(**res)

            dirpath, name = os.path.split(outname)
            dirpath and not os.path.isdir(dirpath) and os.makedirs(dirpath)

            res = os.path.join(dirpath, name)
            if res.endswith(os.path.sep):
                if os.path.isdir(res):
                    logging.warn("Unable to create already existing subdirectory for member : {:d} : {:s}".format(int(member.name()), res))
                else:
                    logging.info("Creating subdirectory due to member : {:d} : {:s}".format(int(member.name()), res))
                    os.makedirs(res)
                continue

            if os.path.exists(res):
                logging.warn("Overwriting already existing file due to member : {:d} : {:s}".format(int(member.name()), res))
            else:
                logging.info("Creating file for member : {:d} : {:s}".format(int(member.name()), res))

            with file(res, 'wb') as out: six.print_(data, file=out)

        # fall-back to writing to already open target
        else:
            six.print_(data, file=target)
        continue

    sys.exit(0)
