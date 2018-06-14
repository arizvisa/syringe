import logging
logging.root.setLevel(logging.WARNING)

import ptypes
from ptypes import *

## General structures
class MSTime(pint.uint16_t): pass
class MSDate(pint.uint16_t): pass

class VersionMadeBy(pint.enum, pint.uint16_t):
    _values_ = [(n, i) for i, n in enumerate(('MSDOS', 'Amiga', 'OpenVMS', 'Unix', 'VM/CMS', 'Atari ST', 'OS/2', 'Macintosh', 'Z-System', 'CP/M', 'Windows', 'MVS', 'VSE', 'Acorn', 'VFAT', 'Alternate MVS', 'BeOS', 'Tandem', 'Os/400', 'OSX'))]
class VersionNeeded(pint.enum, pint.uint16_t):
    _values_ = []

class DataDescriptor(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'crc-32'),
        (pint.uint32_t, 'compressed size'),
        (pint.uint32_t, 'uncompressed size'),
    ]

    def summary(self):
        return 'crc-32=0x{:08x} compressed-size={:d} uncompressed-size={:d}'.format(self['crc-32'].int(), self['compressed size'].int(), self['uncompressed size'].int())

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
#       (lambda s: CompressionMethodFlags.get(s.getparent(type=pstruct.type)['Method'].li.int()), 'Compression'),
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
        _fields_ = [(2, 'unknown')]

@CompressionMethodFlags.define(type=6)
class MethodImplodingFlags(pbinary.flags):
    _fields_ = [(1, '8kDictionary'), (1, '3Shannon-FanoTrees')]

@CompressionMethodFlags.define(type=8)
@CompressionMethodFlags.define(type=9)
class MethodDeflatingFlags(pbinary.struct):
    _fields_ = [(2, 'Quality')]

@CompressionMethodFlags.define(type=14)
class MethodLZMAFlags(pbinary.flags):
    _fields_ = [(1, 'EOS'), (1, 'unused')]

## Extra data field mappings

# FIXME: Add these from section 4.6
class Extensible_data_field(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'id'),
        (pint.uint16_t, 'size'),
        (lambda s: dyn.block(s['size'].li.int()), 'data'),
    ]

## File records
class ZipRecord(ptype.definition):
    cache = {}
    attribute = 'signature'

@ZipRecord.define(signature=(32, 0x04034b50))
class LocalFileHeader(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'version needed to extract'),
        (pbinary.littleendian(BitFlags), 'general purpose bit flag'),
        (CompressionMethod, 'compression method'),
        (MSTime, 'last mod file time'),
        (MSDate, 'last mod file date'),
        (DataDescriptor, 'data descriptor'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),
        (lambda self: dyn.clone(pstr.string, length=self['file name length'].li.int()), 'file name'),
        (lambda self: dyn.clone(Extensible_data_field, blocksize=(lambda s, cb=self['extra field length'].li.int(): cb)), 'extra field'),
        # XXX: if encrypted, include encryption header here
        (lambda self: dyn.block(self['data descriptor'].li['compressed size'].int()), 'file data'),
        # XXX: i think this record is actually encoded within the file data
        (lambda self: DataDescriptor if self['general purpose bit flag'].li.object['PostDescriptor'] else ptype.undefined, 'post data descriptor'),
    ]

    def extract(self, **kwds):
        if not kwds.get('decompress', False):
            return self['file data'].serialize()

        res, method = self['file data'].serialize(), self['compression method']
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
        time, date = self['last mod file time'], self['last mod file date']
        filename = self['file name'].str()
        return '{:s}) {:s} {!r} method={:s} {:s} time/date={:04x}:{:04x}'.format(index, cls, filename, meth, descr, time.int(), date.int())

@ZipRecord.define(signature=(32, 0x02014b50))
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
        (lambda self: dyn.pointer(Record, pint.uint32_t), 'relative offset of local header'),
        (lambda self: dyn.clone(pstr.string, length=self['file name length'].li.int()), 'file name'),
        (lambda self: dyn.block(self['extra field length'].li.int()), 'extra field'),
        (lambda self: dyn.clone(pstr.string, length=self['file comment length'].li.int()), 'file comment'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        meth = self['compression method'].str()
        descr = self['data descriptor'].summary()
        time, date = self['last mod file time'], self['last mod file date']
        filename = self['file name'].str()
        return '{:s}) {:s} {!r} version-made-by={:s} version-needed-to-extract={:s} compression-method={:s} {:s} last-mod-file-time/date={:04x}:{:04x} disk-number-start={:d} internal-file-attributes=0x{:x} external-file-attributes=0x{:x}'.format(index, cls, filename, self['version made by'].str(), self['version needed to extract'].str(), meth, descr, time.int(), date.int(), self['disk number start'].int(), self['internal file attributes'].int(), self['external file attributes'].int()) + ("// %s"%self['file comment'].str() if self['file comment length'].int() > 0 else '')

@ZipRecord.define(signature=(32, 0x06054b50))
class EndOfCentralDirectory(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'number of this disk'),
        (pint.uint16_t, 'number of the disk with the start of the central directory'),
        (pint.uint16_t, 'total number of entries in the central directory on this disk'),
        (pint.uint16_t, 'total number of entries in the central directory'),
        (pint.uint32_t, 'size of the central directory'),
        (lambda self: dyn.pointer(Record, pint.uint32_t), 'offset of start of central directory with respect to the starting disk number'),
        (pint.uint16_t, '.ZIP file comment length'),
        (lambda s: dyn.clone(pstr.string, length=s['.ZIP file comment length'].li.int()), '.ZIP file comment'),
    ]

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) {:s} number-of-this-disk={:d} number-of-this-disk-with-the-start-of-the-central-directory={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory=0x{:x} offset-of-the-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, self['number of this disk'].int(), self['number of the disk with the start of the central directory'].int(), self['total number of entries in the central directory on this disk'].int(), self['total number of entries in the central directory'].int(), self['size of the central directory'].int(), self['offset of start of central directory with respect to the starting disk number']) + ("// %s"%self['.ZIP file comment'].str() if self['.ZIP file comment length'].int() > 0 else '')

@ZipRecord.define(signature=(64, 0x06054b50))
class EndOfCentralDirectory64(pstruct.type):
    def __ExtensibleDataSector(self):
        size = EndOfCentralDirectory().a.size()
        expectedSize = self['size of zip64 end of central directory record'].li.int()
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
        return '{:s}) {:s} version-made-by={:s} version-needed-to-extract={:s} number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} number-of-the-disk-with-the-start-of-the-central-directory={:d} total-number-of-entires-in-the-central-directory-on-this-disk={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory=0x{:x} offset-of-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, self['number of the disk with the start of the zip64 end of central directory'].int(), self['number of the disk with the start of the central directory'].int(), self['total number of entries in the central directory on this disk'].int(), self['total number of entries in the central directory'].int(), self['size of the central directory'].int(), self['offset of start of central directory with respect to the starting disk number'].int(), datasector)

@ZipRecord.define(signature=(64, 0x07054b50))
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
        return '{:s}) {:s} number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} relative-offset-of-the-zip64-end-of-central-directory-record=0x{:x} total-number-of-disks={:d}'.format(index, cls, self['number of the disk with the start of the zip64 end of central directory'].int(), self['relative offset of the zip64 end of central directory record'].int(), self['total number of disks'].int())

@ZipRecord.define(signature=(32, 0x08064b50))
class ArchiveExtraData(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'extra field length'),
        (lambda s: dyn.block(s['extra field length'].li.int()), 'extra field data'),
    ]

    def extract(self, **kwds):
        return self['extra field data'].serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) extra-field-length={:d} extra-field={:s}'.format(index, cls, self['extra field length'].int(), self['extra field data'].summary())

@ZipRecord.define(signature=(32, 0x05054b50))
class DigitalSignature(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'size of data'),
        (lambda s: dyn.block(s['size of data'].li.int()), 'signature data'),
    ]

    def extract(self, **kwds):
        return self['signature data'].serialize()

    def listing(self):
        index = self.getparent(Record).name()
        cls = self.classname()
        return '{:s}) size-of-data={:d} signature-data={:s}'.format(index, cls, self['size of data'].int(), self['signature data'].summary())

## File records
class Record(pstruct.type):
    def __Record(self):
        bits = 32
        sig = self['Signature'].li.int()
        return ZipRecord.lookup((bits, sig))

    _fields_ = [
        (pint.uint32_t, 'Signature'),
        (__Record, 'Record'),
    ]

class File(parray.infinite):
    _object_ = Record

    def isTerminator(self, value):
        return value.__class__ == EndOfCentralDirectory

if __name__ == '__main__':
    import sys, os, os.path
    import zlib, logging, argparse
    import ptypes, archive.zip
    if sys.platform == 'win32': import msvcrt

    arg_p = argparse.ArgumentParser(prog=sys.argv[0] if len(sys.argv) > 0 else 'zip.py', description="List or extract information out of a .zip file", add_help=False)
    arg_p.add_argument('FILE', nargs='*', action='append', type=str, help='list of filenames to extract')
    arg_p.add_argument('-v', '--verbose', action='store_true', help="output verbose logging information", dest='verbose')
    arg_commands_gr = arg_p.add_argument_group("main operation mode")
    arg_commands_gr.add_argument('-h', '--help', action='store_const', help="show this help message and exit", dest='mode', const='help')
    arg_commands_gr.add_argument('-l', '--list', action='store_const', help="list the contents of an archive", dest='mode', const='list')
    arg_commands_gr.add_argument('-la', '--list-all', action='store_const', help="list the entire contents of an archive", dest='mode', const='list-all')
    arg_commands_gr.add_argument('-x', '--extract', '--get', action='store_const', help="extract the specified file records", dest='mode', const='extract')
    arg_commands_gr.add_argument('-d', '--dump', action='store_const', help="dump the specified file records", dest='mode', const='dump')
    arg_device_gr = arg_p.add_argument_group("device selection and switching")
    arg_device_gr.add_argument('-f', '--file', nargs=1, action='store', type=str, metavar="ARCHIVE", help="use archive file or device ARCHIVE", dest='source')
    arg_device_gr.add_argument('-o', '--output', nargs=1, action='store', type=str, metavar="DEVICE", help="extract files to specified DEVICE or FORMAT", dest='target', default=None)
    arg_info_gr = arg_p.add_argument_group("format output")
    arg_info_gr.add_argument('-j', '--compressed', action='store_true', help="extract data from archive in its compressed form", dest='compress', default=False)

    if len(sys.argv) <= 1:
        print >>sys.stdout, arg_p.format_usage()
        sys.exit(0)

    args = arg_p.parse_args(sys.argv[1:])
    if args.mode == 'help':
        print >>sys.stdout, arg_p.format_help()
        sys.exit(0)

    # fix up arguments
    source_a, target_a = args.source[0], None if args.target is None else args.target[0]
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

    isMatchedName = lambda r: (not filelookup) or ('file name' in r['Record'].keys() and r['Record']['file name'].str() in filelookup)
    isMatchedIndex = lambda r: int(r.name()) in indexlookup
    isMatched = lambda r: isMatchedName(r) or isMatchedIndex(r)

    # some useful functions
    def iterate(root):
        for rec in root:
            if args.mode == 'list-all' and isMatched(rec):
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

    # set the verbosity
    if args.verbose:
        logging.root.setLevel(logging.INFO)

    # create the file instance
    z = archive.zip.File(source=source)

    # handle the mode that the user specified
    if args.mode == 'list':
        for rec in iterate(z.l[:-1]):
            print rec['Record'].listing()
        sys.exit(0)

    elif args.mode == 'list-all':
        for rec in iterate(z.l[:-1]):
            print rec['Record'].listing()
        sys.exit(0)

    elif args.mode == 'extract':
        target = target or os.path.join('.', '{path:s}', '{name:s}')

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
            data = '\n'.join((' '.join((ptypes.utils.repr_class(rec.classname()), rec.name())), ptypes.utils.indent("{!r}".format(rec['Record']))))
        else:
            raise NotImplementedError(args.mode)

        # set some reasonable defaults for formatting
        res = dictionary(rec['Record'])
        res['index'] = int(rec.name())
        res['path'], res['name'] = os.path.split(res['file name'] if 'file name' in res.keys() else rec.name())

        # write to a generated filename
        if isinstance(target, basestring):
            outname = target.format(**res)

            dirpath, name = os.path.split(outname)
            dirpath and not os.path.isdir(dirpath) and os.makedirs(dirpath)

            res = os.path.join(dirpath, name)
            if res.endswith(os.path.sep):
                if os.path.isdir(res):
                    logging.warn("Refusing to overwrite already existing subdirectory for record({:d}) : {:s}".format(int(rec.name()), res))
                else:
                    logging.info("Creating subdirectory for record({:d}) : {:s}".format(int(rec.name()), res))
                    os.makedirs(res)
                continue

            if os.path.exists(res):
                logging.warn("Overwriting already existing file with record({:d}) : {:s}".format(int(rec.name()), res))
            else:
                logging.info("Creating new file for record({:d}) : {:s}".format(int(rec.name()), res))

            logging.info("{:s}ing {:d} bytes from record({:d}) to file: {:s}".format(args.mode.title(), len(data), int(rec.name()), res))
            with file(res, 'wb') as out: print >>out, data

        # fall-back to writing to already open target
        else:
            print >>target, data
        continue

    sys.exit(0)
