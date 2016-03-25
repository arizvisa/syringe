import logging
logging.root.setLevel(100)

import ptypes
from ptypes import *

## General structures
class MSTime(pint.uint16_t): pass
class MSDate(pint.uint16_t): pass

class VersionMadeBy(pint.enum, pint.uint16_t):
    _values_ = [(n,i) for i,n in enumerate(('MSDOS', 'Amiga', 'OpenVMS', 'Unix', 'VM/CMS', 'Atari ST', 'OS/2', 'Macintosh', 'Z-System', 'CP/M', 'Windows', 'MVS', 'VSE', 'Acorn', 'VFAT', 'Alternate MVS', 'BeOS', 'Tandem', 'Os/400', 'OSX'))]
class VersionNeeded(pint.enum, pint.uint16_t):
    _values_ = []

class DataDescriptor(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'crc-32'),
        (pint.uint32_t, 'compressed size'),
        (pint.uint32_t, 'uncompressed size'),
    ]

    def summary(self):
        return 'crc-32=0x{:08x} compressed-size={:d} uncompressed-size={:d}'.format(self['crc-32'].num(), self['compressed size'].num(), self['uncompressed size'].num())

class BitFlags(pbinary.flags):
    _fields_ = [
        (2, 'Reserved'),
        (1, 'MaskedDirectory'),
        (1, 'PKEnhanced'),
        (1, 'UTF8'),
        (4, 'unused'),
        (1, 'StrongEncryption'),
        (1, 'CompressedPatchData'),
        (1, 'EnhancedDeflating'),
        (1, 'PostDescriptor'),
        (2, 'Compression'),
#       (lambda s: CompressionMethodFlags.get(s.getparent(type=pstruct.type)['Method'].li.num()), 'Compression'),
        (1, 'Encrypted'),
    ]

## Compression methods
class CompressionMethod(pint.enum, pint.uint16_t):
    _values_ = [
        ('Stored', 0),
        ('Shrunk', 1),  # LZW
        ('Reduced(1)', 2),  # Expanding
        ('Reduced(2)', 3),
        ('Reduced(3)', 4),
        ('Reduced(4)', 5),
        ('Imploded', 6),    # Shannon-Fano
        ('Tokenized', 7),
        ('Deflated', 8),    # zlib?
        ('Deflate64', 9),   # zlib64
        ('PKImplode', 10),  # old IBM TERSE
        ('BZIP2', 12),      # bz2
        ('LZMA', 14),       # lzma
        ('Terse', 18),      # IBM TERSE
        ('LZ77', 19),
        ('WavPack', 97),    # audio
        ('PPMd', 98),
    ]

class CompressionMethodFlags(ptype.definition):
    cache = {}
    class unknown(pbinary.struct):
        _fields_ = [(2,'unknown')]

@CompressionMethodFlags.define(type=6)
class MethodImplodingFlags(pbinary.flags):
    _fields_ = [(1,'8kDictionary'),(1,'3Shannon-FanoTrees')]

@CompressionMethodFlags.define(type=8)
@CompressionMethodFlags.define(type=9)
class MethodDeflatingFlags(pbinary.struct):
    _fields_ = [(2,'Quality')]

@CompressionMethodFlags.define(type=14)
class MethodLZMAFlags(pbinary.flags):
    _fields_ = [(1,'EOS'),(1,'unused')]

## File records
class ZipRecord(ptype.definition):
    cache = {}
    attribute = 'signature'

@ZipRecord.define(signature=(32,0x04034b50))
class LocalFileHeader(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'version needed to extract'),
        (BitFlags, 'general purpose bit flag'),
        (CompressionMethod, 'compression method'),
        (MSTime, 'last mod file time'),
        (MSDate, 'last mod file date'),
        (DataDescriptor, 'data descriptor'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),
        (lambda s: dyn.clone(pstr.string, length=s['file name length'].li.num()), 'file name'),
        (lambda s: dyn.block(s['extra field length'].li.num()), 'extra field'),

        (lambda s: dyn.block(s['data descriptor'].li['compressed size'].num()), 'file data'),

        (lambda s: DataDescriptor if s['general purpose bit flag'].li.object['PostDescriptor'] else ptype.undefined, 'post data descriptor'),
    ]

    def extract(self, **kwds):
        if not kwds.get('decompress', False):
            return self['file data'].serialize()

        res,method = self['file data'].serialize(),self['compression method']
        if method['Stored']:
            return res
        elif method['Deflated']:
            import zlib
            return zlib.decompress(res, -zlib.MAX_WBITS)
        elif method['BZIP2']:
            import bz2
            return bz2.decompress(res)
        elif method['LZMA']:
            import lzma
            return lzma.decompress(res)
        raise ValueError, method

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        meth = self['compression method'].str()
        descr = self['data descriptor'].summary()
        time,date = self['last mod file time'],self['last mod file date']
        filename = self['file name'].str()
        return '{:s}) {:s} {!r} method={:s} {:s} time/date={:04x}:{:04x}'.format(index, cls, filename, meth, descr, time.num(), date.num())

@ZipRecord.define(signature=(32,0x02014b50))
class CentralDirectory(pstruct.type):
    _fields_ = [
        (VersionMadeBy, 'version made by'),
        (VersionNeeded, 'version needed to extract'),
        (BitFlags, 'general purpose bit flag'),
        (CompressionMethod, 'compression method'),
        (MSTime, 'last mod file time'),
        (MSDate, 'last mod file date'),
        (DataDescriptor, 'data descriptor'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),
        (pint.uint16_t, 'file comment length'),
        (pint.uint16_t, 'disk number start'),
        (pint.uint16_t, 'internal file attributes'),
        (pint.uint32_t, 'external file attributes'),
        (dyn.rpointer(ptype.undefined, type=pint.uint32_t), 'relative offset of local header'),
        (lambda s: dyn.clone(pstr.string, length=s['file name length'].li.num()), 'file name'),
        (lambda s: dyn.block(s['extra field length'].li.num()), 'extra field'),
        (lambda s: dyn.clone(pstr.string, length=s['file comment length'].li.num()), 'file comment'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        meth = self['compression method'].str()
        descr = self['data descriptor'].summary()
        time,date = self['last mod file time'],self['last mod file date']
        filename = self['file name'].str()
        return '{:s}) {:s} {!r} version-made-by={:s} version-needed-to-extract={:s} compression-method={:s} {:s} last-mod-file-time/date={:04x}:{:04x} disk-number-start={:d} internal-file-attributes=0x{:x} external-file-attributes=0x{:x}'.format(index, cls, filename, self['version made by'].str(), self['version needed to extract'].str(), meth, descr, time.num(), date.num(), self['disk number start'].num(), self['internal file attributes'].num(), self['external file attributes'].num()) + ("// %s"%self['file comment'].str() if self['file comment length'].num() > 0 else '')

@ZipRecord.define(signature=(32,0x06054b50))
class EndOfCentralDirectory(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'number of this disk'),
        (pint.uint16_t, 'number of the disk with the start of the central directory'),
        (pint.uint16_t, 'total number of entries in the central directory on this disk'),
        (pint.uint16_t, 'total number of entries in the central directory'),
        (pint.uint32_t, 'size of the central directory'),
        (pint.uint32_t, 'offset of start of central directory with respect to the starting disk number'),
        (pint.uint16_t, '.ZIP file comment length'),
        (lambda s: dyn.clone(pstr.string, length=s['.ZIP file comment length'].li.num()), '.ZIP file comment'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) {:s} number-of-this-disk={:d} number-of-this-disk-with-the-start-of-the-central-directory={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory=0x{:x} offset-of-the-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, self['number of this disk'].num(), self['number of the disk with the start of the central directory'].num(), self['total number of entries in the central directory on this disk'].num(), self['total number of entries in the central directory'].num(), self['size of the central directory'].num(), self['offset of start of central directory with respect to the starting disk number']) + ("// %s"%self['.ZIP file comment'].str() if self['.ZIP file comment length'].num() > 0 else '')

@ZipRecord.define(signature=(64,0x06054b50))
class EndOfCentralDirectory64(pstruct.type):
    def __ExtensibleDataSector(self):
        size = EndOfCentralDirectory().a.size()
        expectedSize = self['size of zip64 end of central directory record'].li.num()
        if expectedSize < size:
            ptypes.log.warn("size of zip64 end of central directory record is less than the minimum size : %x : %x", expectedSize, size)
        return dyn.block(expectedSize - size)

    _fields_ = [
        (pint.uint64_t, 'size of zip64 end of central directory record'),

        (VersionMadeBy, 'version made by'),
        (VersionNeeded, 'version needed to extract'),
        (pint.uint32_t, 'number of the disk with the start of the zip64 end of central directory'),

        (pint.uint32_t, 'number of the disk with the start of the central directory'),
        (pint.uint64_t, 'total number of entries in the central directory on this disk'),

        (pint.uint64_t, 'total number of entries in the central directory'),
        (pint.uint64_t, 'size of the central directory'),
        (pint.uint64_t, 'offset of start of central directory with respect to the starting disk number'),
        (__ExtensibleDataSector, 'zip64 extensible data sector'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        data = self['zip64 extensible data sector'].summary()
        return '{:s}) {:s} version-made-by={:s} version-needed-to-extract={:s} number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} number-of-the-disk-with-the-start-of-the-central-directory={:d} total-number-of-entires-in-the-central-directory-on-this-disk={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory=0x{:x} offset-of-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, self['number of the disk with the start of the zip64 end of central directory'].num(), self['number of the disk with the start of the central directory'].num(), self['total number of entries in the central directory on this disk'].num(), self['total number of entries in the central directory'].num(), self['size of the central directory'].num(), self['offset of start of central directory with respect to the starting disk number'].num(), datasector)

@ZipRecord.define(signature=(64,0x07054b50))
class EndOfCentralDirectoryLocator64(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'number of the disk with the start of the zip64 end of central directory'),
        (pint.uint64_t, 'relative offset of the zip64 end of central directory record'),
        (pint.uint32_t, 'total number of disks'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) {:s} number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} relative-offset-of-the-zip64-end-of-central-directory-record=0x{:x} total-number-of-disks={:d}'.format(index, cls, self['number of the disk with the start of the zip64 end of central directory'].num(), self['relative offset of the zip64 end of central directory record'].num(), self['total number of disks'].num())

@ZipRecord.define(signature=(32,0x08064b50))
class ArchiveExtraData(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'extra field length'),
        (lambda s: dyn.block(s['extra field length'].li.num()), 'extra field data'),
    ]

    def extract(self, **kwds):
        return self['extra field data'].serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) extra-field-length={:d} extra-field={:s}'.format(index, cls, self['extra field length'].num(), self['extra field data'].summary())

@ZipRecord.define(signature=(32,0x05054b50))
class DigitalSignature(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'size of data'),
        (lambda s: dyn.block(s['size of data'].li.num()), 'signature data'),
    ]

    def extract(self, **kwds):
        return self['signature data'].serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) size-of-data={:d} signature-data={:s}'.format(index, cls, self['size of data'].num(), self['signature data'].summary())

## File records
class Record(pstruct.type):
    def __Record(self):
        bits = 32
        sig = self['Signature'].li.num()
        return ZipRecord.lookup((bits,sig))

    _fields_ = [
        (pint.uint32_t, 'Signature'),
        (__Record, 'Record'),
    ]

class File(parray.infinite):
    _object_ = Record

    def isTerminator(self, value):
        return value.__class__ == EndOfCentralDirectory

if __name__ == '__main__':
    import sys,os,os.path,zlib,logging,argparse
    import ptypes,archive.zip
    if sys.platform == 'win32': import msvcrt

    arg_p = argparse.ArgumentParser(prog=sys.argv[0] if len(sys.argv) > 0 else 'zip.py', description="List or extract information out of a .zip file", add_help=False)
    arg_p.add_argument('FILE', nargs='*', action='append', type=str, help='list of filenames to extract')
    arg_commands_gr = arg_p.add_argument_group("Main operation mode")
    arg_commands_gr.add_argument('-h', '--help', action='store_const', help="show this help message and exit", dest='mode', const='help')
    arg_commands_gr.add_argument('-l', '--list', action='store_const', help="list the contents of an archive", dest='mode', const='list')
    arg_commands_gr.add_argument('-x', '--extract', '--get', action='store_const', help="extract files from an archive", dest='mode', const='extract')
    arg_commands_gr.add_argument('-d', '--dump', action='store_const', help="dump the specified file records", dest='mode', const='dump')
    arg_device_gr = arg_p.add_argument_group("Device selection and switching")
    arg_device_gr.add_argument('-f', '--file', nargs=1, action='store', type=str, metavar="ARCHIVE", help="use archive file or device ARCHIVE", dest='source')
    arg_device_gr.add_argument('-o', '--output', nargs=1, action='store', type=str, metavar="DEVICE", help="extract files to specified DEVICE or FORMAT", dest='target', default=None)
    arg_info_gr = arg_p.add_argument_group("Format output")
    arg_info_gr.add_argument('-v', '--verbose', action='store_true', help="verbosely list entire contents of archive", dest='verbose')
    arg_info_gr.add_argument('-j', '--compressed', action='store_true', help="extract data from archive in compressed form", dest='compress', default=False)

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
    filelookup = set(filelist)
    indexlookup = set((int(n) for n in filelist if n.isdigit()))

    verbose = args.verbose
    isMatchedName = lambda r: (not filelookup) or ('Filename' in r['Record'].keys() and r['Record']['Filename'].str() in filelookup)
    isMatchedIndex = lambda r: int(r.name()) in indexlookup
    isMatched = lambda r: isMatchedName(r) or isMatchedIndex(r)

    # some useful functions
    def iterate(root):
        for rec in root:
            if verbose and isMatched(rec):
                yield rec
            elif isMatchedIndex(rec):
                yield rec
            elif isMatchedName(rec) and isinstance(rec['Record'], archive.zip.LocalFileHeader):
                yield rec
            continue
        return

    def dictionary(root):
        res = {}
        for k in root.keys():
            v = root[k]
            if isinstance(v, pint.type):
                res[k] = v.num()
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
    z = archive.zip.File(source=source)

    # implement each mode
    if args.mode == 'list':
        for rec in iterate(z.l[:-1]):
            print rec['Record'].listing()
        sys.exit(0)

    elif args.mode == 'extract':
        target = target or os.path.join('.','{path:s}','{name:s}')

    elif args.mode == 'dump':
        target = target or sys.stdout

    # help
    else:
        print >>sys.stdout, arg_p.format_help()
        sys.exit(1)

    # for each record...
    for rec in iterate(z.l[:-1]):

        # assign what data we're writing
        if args.mode == 'extract':
            data = rec['Record'].extract(decompress=not args.compress)
        elif args.mode == 'dump':
            data = '\n'.join((' '.join((ptypes.utils.repr_class(rec.classname()),rec.name())), ptypes.utils.indent(repr(rec['Record']))))

        # set some reasonable defaults
        res = dictionary(rec['Record'])
        res['index'] = int(rec.name())
        res['path'],res['name'] = os.path.split(res['file name'] if 'file name' in res.keys() else rec.name())

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
                    logging.info("Creating subdirectory due to record : {:d} : {:s}".format(int(rec.name()), res))
                    os.makedirs(res)
                continue

            if os.path.exists(res):
                logging.warn("Overwriting already existing file due to record : {:d} : {:s}".format(int(rec.name()), res))
            else:
                logging.info("Creating file for record : {:d} : {:s}".format(int(rec.name()), res))

            with file(res, 'wb') as out: print >>out, data

        # fall-back to writing to already open target
        else:
            print >>target, data
        continue

    sys.exit(0)
