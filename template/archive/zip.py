#http://www.pkware.com/documents/casestudies/APPNOTE.TXT
from ptypes import *

class Local_file_header(pstruct.type):
    type = 0x04034b50
    _fields_ = [
        (dyn.block(4), 'local file header signature'), #(0x04034b50)
        (pint.uint16_t, 'version needed to extract'),
        (pint.uint16_t, 'general purpose bit flag'),
        (pint.uint16_t, 'compression method'),
        (pint.uint16_t, 'last mod file time'),
        (pint.uint16_t, 'last mod file date'),
        (pint.uint16_t, 'crc-32'),
        (pint.uint32_t, 'compressed size'),
        (pint.uint32_t, 'uncompressed size'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),

        (lambda s:dyn.clone(pstr.string, length=s['file name length'].li.int()), 'file name'),
        (lambda s:dyn.block(s['extra field length'].li.int()), 'extra field'),
    ]

class Data_descriptor(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'crc-32'),
        (pint.uint32_t, 'compressed size'),
        (pint.uint32_t, 'uncompressed size'),
    ]

class Archive_extra_data_record(pstruct.type):
    type = 0x08064b50
    _fields_ = [
        (pint.uint32_t, 'archive extra data signature'),
        (pint.uint32_t, 'extra field length'),
        (lambda s: dyn.block(s['extra field length'].li.int()), 'extra field data'),
    ]

class Central_directory_File_header(pstruct.type):
    type = 0x02014b50
    _fields_ = [
        (pint.uint32_t, 'central file header signature'),  #(0x02014b50)
        (pint.uint16_t, 'version made by'),
        (pint.uint16_t, 'version needed to extract'),
        (pint.uint16_t, 'general purpose bit flag'),
        (pint.uint16_t, 'compression method'),
        (pint.uint16_t, 'last mod file time'),
        (pint.uint16_t, 'last mod file date'),
        (pint.uint32_t, 'crc-32'),
        (pint.uint32_t, 'compressed size'),
        (pint.uint32_t, 'uncompressed size'),
        (pint.uint16_t, 'file name length'),
        (pint.uint16_t, 'extra field length'),
        (pint.uint16_t, 'file comment length'),
        (pint.uint16_t, 'disk number start'),
        (pint.uint16_t, 'internal file attributes'),
        (pint.uint32_t, 'external file attributes'),
        (pint.uint32_t, 'relative offset of local header'),

        (lambda s: dyn.clone(pstr.string,length=s['file name length'].li.int()), 'file name'),
        (lambda s: dyn.block(s['extra field length'].li.int()), 'extra field'),
        (lambda s: dyn.clone(pstr.string,length=s['file comment length'].li.int()), 'file comment'),
    ]

class Central_directory_Digital_signature(pstruct.type):
    type = 0x05054b50
    _fields_ = [
        (pint.uint32_t, 'header signature'), # 0x05054b50
        (pint.uint16_t, 'size of data'),
        (lambda s: dyn.block(s['size of data'].li.int()), 'signature data'),
    ]

class Zip64_end_of_central_directory_record(pstruct.type):
    # FIXME
    type = 0x06064b50
    _fields_ = [
        (pint.uint32_t, 'signature'),   # (0x06064b50)
        (pint.uint64_t, 'size of zip64 end of central directory record'),
        (pint.uint16_t, 'version made by'),
        (pint.uint16_t, 'version needed to extract'),
        (pint.uint32_t, 'number of this disk'),
        (pint.uint32_t, 'number of the disk with the start of the central directory'),
        (pint.uint64_t, 'total number of entries in the central directory on this disk'),
        (pint.uint64_t, 'total number of entries in the central directory'),
        (pint.uint64_t, 'size of the central directory'),
        (pint.uint64_t, 'offset of start of central directory with respect to the starting disk number'),
        (dyn.block(0), 'zip64 extensible data sector'), #(variable size)
    ]

class Zip64_end_of_central_dir_locator(pstruct.type):
    type = 0x07064b50
    _fields_ = [
        (pint.uint32_t, 'signature'), # (0x07064b50)
        (pint.uint32_t, 'number of the disk with the start of the zip64 end of central directory'),
        (pint.uint64_t, 'relative offset of the zip64 end of central directory record'),
        (pint.uint32_t, 'total number of disks'),
    ]

class Central_Directory_End_of_central_directory_record(pstruct.type):
    type = 0x06054b50
    _fields_ = [
        (pint.uint32_t, 'end of central dir signature'), #(0x06054b50)
        (pint.uint16_t, 'number of this disk'),
        (pint.uint16_t, 'number of the disk with the start of the central directory'),
        (pint.uint16_t, 'total number of entries in the central directory on this disk'),
        (pint.uint16_t, 'total number of entries in the central directory'),
        (pint.uint32_t, 'size of the central directory'),
        (pint.uint32_t, 'offset of start of central directory with respect to the starting disk number'),
        (pint.uint16_t, '.ZIP file comment length'),
        (lambda s: dyn.clone(pstr.string, length=s['.ZIP file comment length'].li.int()), '.ZIP file comment'),
    ]
