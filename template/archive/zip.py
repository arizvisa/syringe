import logging
logging.root.setLevel(logging.INFO)

import six, ptypes
from ptypes import *

import datetime

## General structures
@pbinary.littleendian
class MSTime(pbinary.struct):
    _fields_ = [
        (6, 'Hour'),
        (5, 'Minute'),
        (5, '2Seconds'),
    ]
    def time(self):
        return datetime.time(self['Hour'], self['Minute'], 2 * self['2Seconds'])

    def isoformat(self):
        res = self.time()
        return res.isoformat()

    def summary(self):
        return self.isoformat()

@pbinary.littleendian
class MSDate(pbinary.struct):
    _fields_ = [
        (7, 'Year'),
        (4, 'Month'),
        (5, 'Day'),
    ]
    def date(self):
        return datetime.date(1980 + self['Year'], self['Month'], self['Day'])

    def isoformat(self):
        res = self.date()
        return res.isoformat()

    def summary(self):
        return self.isoformat()

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
        return 'crc-32={:08X} compressed-size={:d} uncompressed-size={:d}'.format(self['crc-32'].int(), self['compressed size'].int(), self['uncompressed size'].int())

class ZipDataDescriptor(pstruct.type):
    Signature = 0x08074b50
    class _SignatureScan(parray.terminated):
        _object_ = pint.uint8_t
        def isTerminator(self, value):
            if len(self.value) > 3:
                octets = pint.uint32_t().set(ZipDataDescriptor.Signature)
                return self[-4:].serialize() == octets.serialize()
            return False
        def int(self):
            return self[-4:].cast(pint.uint32_t).int()
        def data(self):
            return self.serialize()[:-4]

    _fields_ = [
        (_SignatureScan, 'data'),
        (DataDescriptor, 'descriptor'),
    ]

    def summary(self):
        return 'descriptor={{{:s}}} data={{...}}'.format(self['descriptor'].summary())

    def data(self, **kwds):
        return self['data'].data()

@pbinary.littleendian
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
        (1, 'Encrypted'),
    ]

## Compression methods
class CompressionMethod(pint.enum, pint.uint16_t):
    _values_ = [
        ('Stored', 0),
        ('Shrunk', 1),      # LZW
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
    default = unknown

@CompressionMethodFlags.define
class MethodImplodingFlags(pbinary.flags):
    type = 6
    _fields_ = [(1, '8kDictionary'), (1, '3Shannon-FanoTrees')]

class MethodDeflatingFlags(pbinary.struct):
    _fields_ = [(2, 'Quality')]
@CompressionMethodFlags.define
class MethodDeflatingFlags8(MethodDeflatingFlags):
    type = 8
@CompressionMethodFlags.define
class MethodDeflatingFlags9(MethodDeflatingFlags):
    type = 9

@CompressionMethodFlags.define
class MethodLZMAFlags(pbinary.flags):
    type = 14
    _fields_ = [(1, 'EOS'), (1, 'unused')]

## Extra data field mappings
class ExtraField(ptype.definition):
    cache = {}

class Extra_NTFS_TagType(ptype.definition):
    attribute, cache = 'tag', {}

class Extra_NTFS_Tag(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'Tag'),
        (pint.uint16_t, 'Size'),
        (lambda self: Extra_NTFS_TagType.get(self['Tag'].li.int(), length=self['Size'].li.int()), 'Attribute'),
    ]

    def summary(self):
        return "({:+#x}) {:s}".format(self['Size'].int(), self['Attribute'].summary())

@Extra_NTFS_TagType.define
class NTFS_Attributes(pstruct.type):
    tag = 1
    class TenthOfAMicrosecond(pint.uint64_t):
        def datetime(self):
            epoch = datetime.datetime(1601, 1, 1, 0, 0, 0)
            res = datetime.timedelta(microseconds=self.int() / 10.)
            return epoch + res
        def isoformat(self):
            res = self.datetime()
            return res.isoformat()
        def summary(self):
            return self.isoformat()

    _fields_ = [
        (TenthOfAMicrosecond, 'Mtime'),
        (TenthOfAMicrosecond, 'Atime'),
        (TenthOfAMicrosecond, 'Ctime'),
    ]

    def summary(self):
        return "Mtime={:s} Atime={:s} Ctime={:s}".format(self['Mtime'].isoformat(), self['Atime'].isoformat(), self['Ctime'].isoformat())

@ExtraField.define
class Extra_NTFS(pstruct.type):
    type = 0x000a
    _fields_ = [
        (pint.uint32_t, 'Reserved'),
        (lambda self: dyn.blockarray(Extra_NTFS_Tag, self.blocksize() - self['Reserved'].li.size()), 'Tags'),
    ]

    def summary(self):
        return "Reserved={:#x} [{:s}]".format(self['Reserved'].int(), ', '.join(item.summary() for item in self['Tags']))

# FIXME: Add these from section 4.6
class Extensible_data_field(pstruct.type):
    def __unknown(self):
        cb = sum(self[k].li.size() for k in ('id','size','data'))
        return dyn.block(self.blocksize() - cb)

    def __data(self):
        id, size = (self[item].li for item in ['id', 'size'])
        return ExtraField.get(id.int(), blocksize=lambda self, bs=size.int(): bs)

    _fields_ = [
        (pint.uint16_t, 'id'),
        (pint.uint16_t, 'size'),
        (__data, 'data'),
        (__unknown, 'unknown'),
    ]

    def summary(self):
        return "{:s} {:s}".format(self['data'].classname(), self['data'].summary())

## File records
class ZipRecord(ptype.definition):
    cache = {}
    attribute = 'signature'

class LocalFileHeader(pstruct.type):
    signature = 0, 0x04034b50

@ZipRecord.define
class LocalFileHeader32(LocalFileHeader):
    signature = 32, 0x04034b50

    def __extra_field(self):
        cb = self['extra field length'].li
        return dyn.clone(Extensible_data_field, blocksize=lambda s, bs=cb.int(): bs)

    def __file_data(self):
        desc = self.p.DirectoryRecord['data descriptor'] if hasattr(self.p, 'DirectoryRecord') else self['data descriptor'].li
        return dyn.block(desc['compressed size'].int())

    def __post_data_descriptor(self):
        if hasattr(self.p, 'DirectoryRecord'):
            flags = self.p.DirectoryRecord['general purpose bit flag']
            return DataDescriptor if flags['PostDescriptor'] else ptype.undefined
        flags = self['general purpose bit flag'].li
        return ZipDataDescriptor if flags['PostDescriptor'] else ptype.undefined

    _fields_ = [
        (pint.uint16_t, 'version needed to extract'),
        (BitFlags, 'general purpose bit flag'),
        (CompressionMethod, 'compression method'),
        (MSTime, 'last mod file time'),
        (MSDate, 'last mod file date'),
        (DataDescriptor, 'data descriptor'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),
        (lambda self: dyn.clone(pstr.string, length=self['file name length'].li.int()), 'file name'),
        (__extra_field, 'extra field'),
        # XXX: if encrypted, include encryption header here
        (__file_data, 'file data'),
        # XXX: i think this record is actually encoded within the file data
        (__post_data_descriptor, 'post data descriptor'),
    ]

    def summary(self):
        needed = self['version needed to extract']
        method, desc = self.Method(), self.Descriptor()
        dt = datetime.datetime.combine(self['last mod file date'].date(), self['last mod file time'].time())
        return "{:s} (version {:d}) {!r} datetime={:s} compressed={:#x} uncompressed={:#x} crc32={:#x}{:s}".format(method.str(), needed.int(), self.Name(), dt.isoformat(), desc['compressed size'].int(), desc['uncompressed size'].int(), desc['crc-32'].int(), " {:s}".format(self['general purpose bit flag'].summary()) if self['general purpose bit flag'].int() > 0 else '')

    def Name(self):
        return self['file name'].str()
    def Method(self):
        return self['compression method']
    def Descriptor(self):
        PostDescriptorQ = self['general purpose bit flag'].o['PostDescriptor']
        return self['post data descriptor']['descriptor'] if PostDescriptorQ else self['data descriptor']
    def Data(self):
        PostDescriptorQ = self['general purpose bit flag'].o['PostDescriptor']
        return self['post data descriptor'].data() if PostDescriptorQ else self['file data'].serialize()

    def extract(self, **kwds):
        res = self.Data()
        if not kwds.get('decompress', False):
            logging.debug('Extracting {:d} bytes of compressed content'.format(len(res)))
            return res

        method = self['compression method']
        if method['Stored']:
            logging.debug('Decompressing ({:s}) {:d} bytes of content.'.format('Uncompressed', len(res)))
            return res
        elif method['Deflated']:
            import zlib
            logging.debug('Decompressing ({:s}) {:d} bytes of content.'.format('Zlib', len(res)))
            return zlib.decompress(res, -zlib.MAX_WBITS)
        elif method['BZIP2']:
            import bz2
            logging.debug('Decompressing ({:s}) {:d} bytes of content.'.format('BZip2', len(res)))
            return bz2.decompress(res)
        elif method['LZMA']:
            import lzma
            logging.debug('Decompressing ({:s}) {:d} bytes of content.'.format('Lzma', len(res)))
            return lzma.decompress(res)
        raise ValueError, method

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        filename, meth, descr = self.Name(), self.Method(), self.Descriptor()
        dt = datetime.datetime.combine(self['last mod file date'].date(), self['last mod file time'].time())
        return '{{{:d}}} {:s} ({:x}{:+x}) {!r} method={:s} {:s} timestamp={:s}'.format(index, cls, ofs, bs, filename, meth.str(), descr.summary(), dt.isoformat())

class CentralDirectoryEntry(pstruct.type):
    signature = 0, 0x02014b50

@ZipRecord.define
class CentralDirectoryEntry32(CentralDirectoryEntry):
    signature = 32, 0x02014b50

    def __relative_offset_of_local_header(self):
        t = dyn.clone(Record, DirectoryRecord=self)
        return dyn.pointer(t, pint.uint32_t)

    def __file_name(self):
        res = self['file name length'].li
        return dyn.clone(pstr.string, length=res.int())

    def __extra_field(self):
        cb = self['extra field length'].li
        return dyn.clone(Extensible_data_field, blocksize=lambda s, bs=cb.int(): bs)

    def __file_comment(self):
        res = self['file comment length'].li
        return dyn.clone(pstr.string, length=res.int())

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
        (__relative_offset_of_local_header, 'relative offset of local header'),
        (__file_name, 'file name'),
        (__extra_field, 'extra field'),
        (__file_comment, 'file comment'),
    ]

    def summary(self):
        disk, offset = (self[item] for item in ['disk number start', 'relative offset of local header'])
        version, needed = (self[item] for item in ['version made by', 'version needed to extract'])
        method, desc = self.Method(), self.Descriptor()
        dt = datetime.datetime.combine(self['last mod file date'].date(), self['last mod file time'].time())
        return "disk#{:d} {:s} (version={:d}<{:d}) offset={:+#x} {!r}{:s} datetime={:s} compressed={:#x} uncompressed={:#x} crc32={:#x}{:s}".format(disk.int(), method.str(), needed.int(), version.int(), offset.int(), self.Name(), " ({:s})".format(self['file comment'].str()) if self['file comment length'].int() else '', dt.isoformat(), desc['compressed size'].int(), desc['uncompressed size'].int(), desc['crc-32'].int(), " {:s}".format(self['general purpose bit flag'].summary()) if self['general purpose bit flag'].int() > 0 else '')

    def Name(self):
        return self['file name'].str()
    def Method(self):
        return self['compression method']
    def Descriptor(self):
        return self['data descriptor']
    def Comment(self):
        return self['file comment'].str()

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        filename, meth, descr = self.Name(), self.Method(), self.Descriptor()
        dt = datetime.datetime.combine(self['last mod file date'].date(), self['last mod file time'].time())
        return '{{{:d}}} {:s} ({:x}{:+x}) {!r} version-made-by={:s} version-needed-to-extract={:s} compression-method={:s} {:s} timestamp={:s} disk-number-start={:d} internal-file-attributes={:#x} external-file-attributes={:#x}'.format(index, cls, ofs, bs, filename, self['version made by'].str(), self['version needed to extract'].str(), meth.str(), descr.summary(), dt.isoformat(), self['disk number start'].int(), self['internal file attributes'].int(), self['external file attributes'].int()) + ('// {:s}'.format(self.Comment()) if self['file comment length'].int() > 0 else '')


class EndOfCentralDirectory(pstruct.type):
    signature = 0, 0x06054b50

@ZipRecord.define
class EndOfCentralDirectory32(EndOfCentralDirectory):
    signature = 32, 0x06054b50
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

    def summary(self):
        disk = self['number of this disk']
        socdisk = self['number of the disk with the start of the central directory']
        offset = self['offset of start of central directory with respect to the starting disk number']
        length = self['total number of entries in the central directory on this disk']
        total = self['total number of entries in the central directory']
        size = self['size of the central directory']
        return "disk#{:d} soc-disk#{:d} soc-offset={:#x} soc-length={:d}/{:d} soc-size={:+d}{:s}".format(disk.int(), socdisk.int(), offset.int(), length.int(), total.int(), size.int(), " ({:s})".format(self['.ZIP file comment'].str()) if self['.ZIP file comment length'].int() else '')

    def Comment(self):
        return self['.ZIP file comment'].str()

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        return '{{{:d}}} {:s} ({:x}{:+x}) number-of-this-disk={:d} number-of-this-disk-with-the-start-of-the-central-directory={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory={:d} offset-of-the-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, ofs, bs, self['number of this disk'].int(), self['number of the disk with the start of the central directory'].int(), self['total number of entries in the central directory on this disk'].int(), self['total number of entries in the central directory'].int(), self['size of the central directory'].int(), self['offset of start of central directory with respect to the starting disk number']) + ('// {:s}'.format(self.Comment()) if self['.ZIP file comment length'].int() > 0 else '')

@ZipRecord.define
class EndOfCentralDirectory64(EndOfCentralDirectory):
    signature = 64, 0x06054b50

    def __ExtensibleDataSector(self):
        size = EndOfCentralDirectory().a.size()
        expectedSize = self['size of zip64 end of central directory record'].li.int()
        if expectedSize < size:
            ptypes.log.warn('size of zip64 end of central directory record is less than the minimum size: {:#x} < {:#x}'.format(expectedSize, size))
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

    def summary(self):
        offset = self['offset of start of central directory with respect to the starting disk number']
        length = self['total number of entries in the central directory on this disk']
        size = self['size of the central directory']
        return "(version {:d}>{:d} index {:d}) offset={:#x} length={:d} size={:+d}{:s}".format(self['version made by'].int(), self['version needed to extract'].int(), self['number of this disk'].int(), offset.int(), length.int(), size.int(), " ({:s})".format(self['.ZIP file comment'].str()) if self['.ZIP file comment length'].int() else '')

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        data = self['zip64 extensible data sector'].summary()
        return '{{{:d}}} {:s} ({:x}{:+x}) version-made-by={:s} version-needed-to-extract={:s} number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} number-of-the-disk-with-the-start-of-the-central-directory={:d} total-number-of-entires-in-the-central-directory-on-this-disk={:d} total-number-of-entries-in-the-central-directory={:d} size-of-the-central-directory={:#x} offset-of-start-of-central-directory-with-respect-to-the-starting-disk-number={:d}'.format(index, cls, ofs, bs, self['number of the disk with the start of the zip64 end of central directory'].int(), self['number of the disk with the start of the central directory'].int(), self['total number of entries in the central directory on this disk'].int(), self['total number of entries in the central directory'].int(), self['size of the central directory'].int(), self['offset of start of central directory with respect to the starting disk number'].int(), datasector)

class EndOfCentralDirectoryLocator(pstruct.type):
    signature = 0, 0x07054b50

@ZipRecord.define
class EndOfCentralDirectoryLocator64(EndOfCentralDirectoryLocator):
    signature = 64, 0x07054b50
    _fields_ = [
        (pint.uint32_t, 'number of the disk with the start of the zip64 end of central directory'),
        (pint.uint64_t, 'relative offset of the zip64 end of central directory record'),
        (pint.uint32_t, 'total number of disks'),
    ]

    def summary(self):
        disk = self['number of the disk with the start of the zip64 end of central directory']
        offset = self['relative offset of the zip64 end of central directory record']
        return "disk#={:d} eoc={:#0{:d}x} disks={:d}".format(disk.int(), offset.int(), 2 + 2 * offset.size(), self['total number of disks'].int())

    def extract(self, **kwds):
        return self.serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        return '{{{:d}}} {:s} ({:x}{:+x}) number-of-the-disk-with-the-start-of-the-zip64-end-of-central-directory={:d} relative-offset-of-the-zip64-end-of-central-directory-record={:#x} total-number-of-disks={:d}'.format(index, cls, ofs, bs, self['number of the disk with the start of the zip64 end of central directory'].int(), self['relative offset of the zip64 end of central directory record'].int(), self['total number of disks'].int())

class ArchiveExtraData(pstruct.type):
    signature = 0, 0x08064b50

@ZipRecord.define
class ArchiveExtraData32(ArchiveExtraData):
    signature = 32, 0x08064b50

    _fields_ = [
        (pint.uint32_t, 'extra field length'),
        (lambda s: dyn.block(s['extra field length'].li.int()), 'extra field data'),
    ]

    def extract(self, **kwds):
        return self['extra field data'].serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        return '{{{:d}}} {:s} ({:x}{:+x}) extra-field-length={:d} extra-field={:s}'.format(index, cls, ofs, bs, self['extra field length'].int(), self['extra field data'].summary())

class DigitalSignature(pstruct.type):
    signature = 0, 0x05054b50

@ZipRecord.define
class DigitalSignature32(DigitalSignature):
    signature = 32, 0x05054b50

    _fields_ = [
        (pint.uint16_t, 'size of data'),
        (lambda s: dyn.block(s['size of data'].li.int()), 'signature data'),
    ]

    def extract(self, **kwds):
        return self['signature data'].serialize()

    def listing(self):
        cls, index, ofs, bs = self.classname(), int(self.getparent(Record).name()), self.getparent(Record).getoffset(), self.getparent(Record).size()
        return '{{{:d}}} {:s} ({:x}{:+x}) size-of-data={:d} signature-data={:s}'.format(index, cls, ofs, bs, self['size of data'].int(), self['signature data'].summary())

## File records
class Record(pstruct.type):
    def __Record(self):
        bits, sig = 32, self['Signature'].li.int()
        try:
            p = self.getparent(Directory)
        except ptypes.error.NotFoundError:
            return ZipRecord.lookup((bits, sig))

        t = ZipRecord.lookup((bits, sig))
        if isinstance(p, File) and hasattr(p, 'Directory'):
            cd = p.Directory
            return dyn.clone(t, DirectoryRecord=cd.member(self.getoffset()))
        return t

    # FIXME: Signature should be a parray.terminated which seeks for a valid signature
    #        and has a method which returns the correct code for __Record to be correct.
    _fields_ = [
        (pint.uint32_t, 'Signature'),
        (__Record, 'Record'),
    ]

    def summary(self):
        return "{:0{:d}x}".format(self['Signature'].int(), 2 * self['Signature'].size(), self['Record'].summary())

# Central Directory
class Directory(parray.terminated):
    _object_ = Record

    def isTerminator(self, value):
        if isinstance(value['record'], EndOfCentralDirectory):
            return True
        return isinstance(self.length, six.integer_types) and len(self.value) >= self.length

    def member(self, offset):
        for item in self:
            rec = item['record']
            if isinstance(rec, CentralDirectoryEntry) and offset == rec['relative offset of local header'].int():
                return rec
            continue
        raise IndexError(offset)

class File(Directory):
    _object_ = Record

    def isTerminator(self, value):
        return isinstance(value['record'], EndOfCentralDirectory)

if __name__ == '__main__':
    import sys, os, os.path
    import zlib, logging, argparse
    import ptypes, archive.zip
    if sys.platform == 'win32': import msvcrt

    arg_p = argparse.ArgumentParser(prog=sys.argv[0] if len(sys.argv) > 0 else 'zip.py', description='List or extract information out of a .zip file', add_help=False)
    arg_p.add_argument('FILE', nargs='*', action='append', type=str, help='list of filenames to extract')
    arg_p.add_argument('-v', '--verbose', action='store_true', help='output verbose logging information', dest='verbose')
    arg_commands_gr = arg_p.add_argument_group('main operation mode')
    arg_commands_gr.add_argument('-h', '--help', action='store_const', help='show this help message and exit', dest='mode', const='help')
    arg_commands_gr.add_argument('-l', '--list', action='store_const', help='list the contents of an archive', dest='mode', const='list')
    arg_commands_gr.add_argument('-la', '--list-all', action='store_const', help='list the entire contents of an archive', dest='mode', const='list-all')
    arg_commands_gr.add_argument('-x', '--extract', '--get', action='store_const', help='extract the specified file records', dest='mode', const='extract')
    arg_commands_gr.add_argument('-d', '--dump', action='store_const', help='dump the specified file records', dest='mode', const='dump')
    arg_device_gr = arg_p.add_argument_group('device selection and switching')
    arg_device_gr.add_argument('-F', action='store_false', default=True, dest='use_eoc', help='use entire file instead of central directory')
    arg_device_gr.add_argument('-f', '--file', action='store', type=argparse.FileType('rb'), default='-', metavar='ARCHIVE', help='use archive file or device ARCHIVE', dest='source')
    arg_device_gr.add_argument('-o', '--output', action='store', type=str, metavar='DEVICE', help='extract files to specified DEVICE or FORMAT', dest='target', default='-')
    arg_info_gr = arg_p.add_argument_group('format output')
    arg_info_gr.add_argument('-j', '--compressed', action='store_true', help='extract data from archive in its compressed form', dest='compress', default=False)

    if len(sys.argv) <= 1:
        six.print_(arg_p.format_usage(), file=sys.stdout)
        sys.exit(0)

    args = arg_p.parse_args(sys.argv[1:])
    if args.mode == 'help':
        six.print_(arg_p.format_help(), file=sys.stdout)
        sys.exit(0)

    # fix up arguments
    source_a, target_a = args.source, args.target
    if args.use_eoc:
        if source_a.name == '<stdin>':
            if sys.platform == 'win32': msvcrt.setmode(source_a.fileno(), os.O_BINARY)
            source_data = source_a.read()
        else:
            source_data = source_a.read()
        source = ptypes.prov.string(source_data)
    else:
        source = ptypes.prov.fileobj(source_a)

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
    def iterate_file(root):
        for rec in root:
            if args.mode == 'list-all' and isMatched(rec):
                yield rec
            elif isMatchedIndex(rec):
                yield rec
            elif isMatchedName(rec) and isinstance(rec['Record'], archive.zip.LocalFileHeader):
                yield rec
            continue
        return

    def iterate_directory(root):
        for rec in root:
            if args.mode == 'list-all' and isMatched(rec):
                yield rec
            elif isMatchedIndex(rec):
                yield rec
            elif isMatchedName(rec) and isinstance(rec['Record'], archive.zip.CentralDirectoryEntry):
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
        logging.root.setLevel(logging.DEBUG)

    # first locate the EndOfCentralDirectory
    eoc = None
    if args.use_eoc:
        logging.debug("Locating EndOfCentralDirectory in {:#x} bytes...".format(len(source_data)))
        signature = pint.uint32_t().set(EndOfCentralDirectory.signature[1])
        idx = signature.size() + source_data[::-1].index(signature.serialize()[::-1])
        rec = archive.zip.Record(source=ptypes.prov.string(source_data[-idx:])).l

        # validate it
        if rec['Signature'].int() == signature.int():
            eoc = rec['Record']
        else:
            logging.fatal("Unable to locate end of central directory")

    # now we can read the central directory
    if eoc is None:
        logging.debug("Reading zip file without CentralDirectory...")
        z = archive.zip.File(source=source)
        iterate = iterate_file

    else:
        offset_f, length_f = (eoc[item] for item in ['offset of start of central directory with respect to the starting disk number', 'total number of entries in the central directory on this disk'])
        logging.debug("Reading {:d} elements from CentralDirectory at offset {:#x}...".format(length_f.int(), offset_f.int()))
        z = archive.zip.Directory(source=source, offset=offset_f.int())
        iterate = iterate_directory

    # handle the mode that the user specified
    if args.mode == 'list':
        z = z.l
        for rec in iterate(z[:-1]):
            print(rec['Record'].listing())
        sys.exit(0)

    elif args.mode == 'list-all':
        z = z.l
        for rec in iterate(z[:-1]):
            print(rec['Record'].listing())
        sys.exit(0)

    elif args.mode == 'extract':
        target = target or os.path.join('.', '{path:s}', '{name:s}')

    elif args.mode == 'dump':
        target = target or sys.stdout

    # help
    else:
        six.print_(arg_p.format_help(), file=sys.stdout)
        sys.exit(1)

    # for each record...
    z = z.l
    for rec in iterate(z[:-1]):

        # assign what data we're writing
        if args.mode == 'extract':
            if isinstance(rec['Record'], archive.zip.CentralDirectoryEntry):
                drec = rec['Record']['relative offset of local header'].d.li
                data = drec['Record'].extract(decompress=not args.compress)
            else:
                data = rec['Record'].extract(decompress=not args.decompress)

            data = rec['Record']['relative offset of local header'].d.li['Record'].extract(decompress=not args.compress) if isinstance(rec['Record'], archive.zip.CentralDirectoryEntry) else rec['Record'].extract(decompress=not args.decompress)
        elif args.mode == 'dump':
            data = '\n'.join((' '.join((ptypes.utils.repr_class(rec.classname()), rec.name())), ptypes.utils.indent('{!r}'.format(rec['Record']))))
        else:
            raise NotImplementedError(args.mode)

        # set some reasonable defaults for formatting
        res = dictionary(rec['Record'])
        res['index'] = int(rec.name())
        res['path'], res['name'] = os.path.split(res['file name'] if 'file name' in res.keys() else rec.name())

        # write to a generated filename
        if isinstance(target, six.string_types):
            outname = target.format(**res)

            dirpath, name = os.path.split(outname)
            dirpath and not os.path.isdir(dirpath) and os.makedirs(dirpath)

            res = os.path.join(dirpath, name)
            if res.endswith(os.path.sep):
                if os.path.isdir(res):
                    logging.warn('Refusing to overwrite already existing subdirectory for record({:d}): {:s}'.format(int(rec.name()), res))
                else:
                    logging.info('Creating subdirectory for record({:d}): {:s}'.format(int(rec.name()), res))
                    os.makedirs(res)
                continue

            if os.path.exists(res):
                logging.warn('Overwriting already existing file with record({:d}): {:s}'.format(int(rec.name()), res))
            else:
                logging.info('Creating new file for record({:d}): {:s}'.format(int(rec.name()), res))

            logging.debug('{:s}ing {:d} bytes from record({:d}) to file: {:s}'.format(args.mode.title(), len(data), int(rec.name()), res))
            with file(res, 'wb') as out: six.print_(data, file=out)

        # fall-back to writing to already open target
        else:
            logging.debug('{:s}ing {:d} bytes from record({:d}) to stream: {:s}'.format(args.mode.title(), len(data), int(rec.name()), target.name))
            six.print_(data, file=target)
        continue

    sys.exit(0)
