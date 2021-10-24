'''
https://github.com/DFIR-ORC/dfir-orc/tree/main/src/OrcLib
'''
import ndk, ptypes
from ptypes import *
from ndk.datatypes import *

class _REPARSE_DATA_BUFFER(pstruct.type):
    def __PathBuffer(self):
        length = self['ReparseDataLength'].li.int()
        return dyn.clone(pstr.wstring, length=length)
    _fields_ = [
        (ULONG, 'ReparseTag'),
        (USHORT,'ReparseDataLength'),
        (USHORT,'Reserved'),
        (USHORT,'SubstituteNameOffset'),
        (USHORT,'SubstituteNameLength'),
        (USHORT,'PrintNameOffset'),
        (USHORT,'PrintNameLength'),
        (ULONG,'Flags'),
        (__PathBuffer, 'PathBuffer'),
    ]

# copied from http://www.writeblocked.org/resources/NTFS_CHEAT_SHEETS.pdf
# redefined based on https://raw.githubusercontent.com/REhints/Publications/master/Conferences/RECON'2013/RECON_2013.pdf

class _BIOS_PARAMETER_BLOCK(pstruct.type):
    '''BPB @ EBPB'''
    _fields_ = [
        (WORD, 'BytesPerSector'),
        (BYTE, 'SecPerCluster'),
        (WORD, 'ReservedSectors'),
        (dyn.array(BYTE, 5), 'Reserved'),       # 0x000000xxxx
        (BYTE, 'MediaDescriptorID'),
        (WORD, 'Reserved2'),                    # 0x0000
        (WORD, 'SectorsPerTrack'),
        (WORD, 'NumberOfHeads'),
        (DWORD, 'HiddenSectors'),
        (dyn.array(DWORD, 2), 'Reserved3'),

        # Extended BIOS Parameter Block
        (LONGLONG, 'TotalSectors'),
        (LONGLONG, 'StartingCluster'),          # $MFT
        (LONGLONG, 'MFTMirrStartingCluster'),   # $MFTMirror
        (DWORD, 'ClustersPerMFTRecord'),
        (DWORD, 'ClustersPerIndexBuffer'),
        (LONGLONG, 'VolumeSerialNumber'),
        (DWORD, 'Reserved4'),                   # checksum
    ]

class Boot(pstruct.type):
    _fields_ = [
        (dyn.block(3), 'branch'),
        (ULONGLONG, 'oem'),
        (_BIOS_PARAMETER_BLOCK, 'bios parameter block'),
        (dyn.block(426), 'code'),
        (USHORT, 'sentinel'),   # 0xaa55
    ]

class Descriptor(pstruct.type):
    '''File Record Segment Header'''
    _fields_ = [
        (ULONG, 'Signature'),   # "FILE"
        (USHORT, 'Update Sequence Array Offset'),
        (USHORT, 'Update Sequence Array Size'),
        (ULONG, '$LogFile Sequence Number'),
        (USHORT, 'Sequence Number'),
        (USHORT, 'Hard Link Count'),
        (USHORT, '1st Attribute Offset'),
        (USHORT, 'Flags'),
        (ULONG, 'Used size'),
        (ULONG, 'Allocated size'),
        (ULONGLONG, 'File reference'),
        (USHORT, 'Next Attribute Id'),

        #(USHORT, 'Update Sequence Number'),
        #(dyn.array(ptype.undefined, 0), 'Update Sequence Array'),

        #(dyn.block(2), 'unused'),
        #(ULONG, 'MFT record number'),
        #(dyn.clone(pint.uinteger_t, length=6), 'Default Location of Update Sequence Array'),
        #(dyn.clone(pint.uinteger_t, length=10), 'Reserved for Update Sequence Array'),
        #(ULONGLONG, 'Reserved for Sequence Array'),
        #(ULONGLONG, 'Common Location of 1st Attribute'),
    ]

### MFT Attributes
class MFT_Attribute(ptype.definition):
    cache, attribute = {}, 'id'

class MFT_Attribute_Id(pint.enum, ULONG):
    _values_ = [
        ('$STANDARD_INFORMATION', 0x10),
        ('$ATTRIBUTE_LIST', 0x20),
        ('$FILE_NAME', 0x30),
        ('$OBJECT_ID', 0x40),
        ('$SECURITY_DESCRIPTOR', 0x50),
        ('$VOLUME_NAME', 0x60),
        ('$VOLUME_INFORMATION', 0x70),
        ('$DATA', 0x80),
        ('$INDEX_ROOT', 0x90),
        ('$INDEX_ALLOCATION', 0xa0),
        ('$BITMAP', 0xb0),
        ('$REPARSE_POINT', 0xc0),
        ('$EA_INFORMATION', 0xd0),
        ('$PROPERTY_SET', 0xe0),
        ('$LOGGED_UTILITY_STREAM', 0x100),
    ]

@MFT_Attribute.define
class Attribute_List(ptype.undefined):
    id = 0x20

@MFT_Attribute.define
class Attribute_ObjectID(ptype.undefined):
    id = 0x40

@MFT_Attribute.define
class Attribute_SecurityDescriptor(ptype.block):
    '''$SECURITY_DESCRIPTOR'''
    id = 0x50

@MFT_Attribute.define
class Attribute_VolumeName(ptype.undefined):
    id = 0x60

@MFT_Attribute.define
class Attribute_VolumeInformation(ptype.undefined):
    id = 0x70

@MFT_Attribute.define
class Attribute_Data(ptype.block):
    '''$DATA'''
    id = 0x80

@MFT_Attribute.define
class Attribute_IndexRoot(pstruct.type):
    '''$INDEX_ROOT'''
    id = 0x90

    _fields_ = [
        (ULONG, 'Type'),
        (ULONG, 'Collation Rule'),
        (ULONG, 'Allocation Index Entry Size'),
        (BYTE, 'Clusters per Index Record'),
        (dyn.align(8), 'Padding'),              # FIXME: padding, not alignment
    ]

@MFT_Attribute.define
class Attribute_IndexAllocation(ptype.undefined):
    id = 0xa0

@MFT_Attribute.define
class Attribute_Bitmap(ptype.undefined):
    '''$BITMAP'''
    id = 0xb0

@MFT_Attribute.define
class Attribute_ReparsePoint(ptype.undefined):
    id = 0xc0

@MFT_Attribute.define
class Attribute_LoggedToolStream(ptype.undefined):
    id = 0x100

class Attribute(pstruct.type):
    class Header(pstruct.type):
        '''Non-Resident and Resident Attribute Header'''
        class _Form_Code(pint.enum, BYTE):
            _values_ = [('Resident', 0x00), ('Non-Resident', 0x01)]
        class _Flags(pbinary.flags):
            _fields_ = [
                (1, 'Sparse'),
                (1, 'Encrypted'),
                (6, 'Unused'),
                (8, 'Compressed'),
            ]

        _fields_ = [
            (ULONG, 'Attribute Length'),
            (BYTE, 'Form Code'),
            (BYTE, 'Name Length'),
            (BYTE, 'Name Offset'),
            (_Flags, 'Flags'),
            (USHORT, 'Attribute Id'),
        ]

    def __Header(self):
        res = self['Header'].li
        return NonResident_Header if res['Form Code'].int() else Resident_Header

    def __Attribute(self):
        res = self['Header'].li
        if res['Form Code'].int():
            return DataRun

        # Resident attribute
        res, h = self['Id'].li, self['Residency'].li
        t = MFT_Attribute.lookup(res.int())
        if issubclass(t, ptype.block):
            return dyn.clone(t, length=h.Length())
        return t

    def __Space(self):
        res = self['Residency'].li
        cb = sum(self[fld].li.size() for fld in ['Id', 'Header', 'Residency'])
        return dyn.block(res.Offset() - cb)

    def __Extra(self):
        res = self['Residency'].li
        attribute = self['Attribute'].li
        cb = res.Length() - attribute.size()
        return dyn.block(max(0, cb))

    _fields_ = [
        (MFT_Attribute_Id, 'Id'),
        (Header, 'Header'),
        (__Header, 'Residency'),
        (__Space, 'Space'),
        (__Attribute, 'Attribute'),
        (__Extra, 'Extra'),
    ]

### Residency headers
class Resident_Header(pstruct.type):
    '''Resident Attribute Header'''
    _fields_ = [
        (ULONG, 'Length'),
        (USHORT, 'Offet'),
        (BYTE, 'Indexed Flag'),
        (BYTE, 'Padding'),
    ]

    def Offset(self):
        return self['Offset'].int()

    def Length(self):
        return self['Length'].int()

class DataRun(pstruct.type):
    class InfoSize(pbinary.struct):
        _fields_ = [
            (4, 'Cluster Length'),
            (4, 'Offset Length'),
        ]

    def __SizedInteger(field):
        def SizedInteger(self, name=field):
            res = self['info'].li
            return dyn.clone(pint.uinteger_t, length=res[name])
        return SizedInteger

    _fields_ = [
        (InfoSize, 'info'),
        (__SizedInteger('Cluster Length'), 'Size'),
        (__SizedInteger('Offset Length'), 'Offset'),
        (dyn.align(8), 'Padding'),  # FIXME: This shouldn't be alignment, but rather padding to make the size a multiple of 8
    ]

class NonResident_Header(pstruct.type):
    '''Non-resident Attribute Header'''
    _fields_ = [
        (ULONGLONG, 'Start virtual cluster number'),
        (ULONGLONG, 'End virtual cluster number'),
        (BYTE, 'Runlist Offset'),
        (BYTE, 'Compression Unit Size'),
        (dyn.align(8), 'Padding'),          # FIXME: This should be padding, not alignment (but I'm lazy)
        (ULONGLONG, 'Size of attribute content'),
        (ULONGLONG, 'Size on disk of attribute content'),
        (ULONGLONG, 'Initialized size of attribute content'),
    ]

    def Offset(self):
        res = self['Runlist Offset'].li
        return res.int()

    def Length(self):
        # This is the minimum size of a Data Run to calculate its real size
        return 1

### MFT Attribute Types
class Standard_Flags(pbinary.flags):
    _fields_ = [
        (17, 'Reserved'),
        (1, 'Encrypted'),
        (1, 'Not Indexed'),
        (1, 'Offline'),
        (1, 'Compressed'),
        (1, 'Reparse Point'),
        (1, 'Sparse File'),
        (1, 'Temporary'),

        (1, 'Normal'),
        (1, 'Device'),
        (1, 'Archive'),
        (2, 'Unused'),
        (1, 'System'),
        (1, 'Hidden'),
        (1, 'Read-only'),
    ]

@MFT_Attribute.define
class Standard_Information(pstruct.type):
    '''$STANDARD_INFORMATION'''
    id = 0x10

    _fields_ = [
        (ULONGLONG, 'Date Created'),
        (ULONGLONG, 'Date Modified'),
        (ULONGLONG, 'Date MFT Modified'),
        (ULONGLONG, 'Date Accessed'),
        (Standard_Flags, 'Flags'),
        (ULONG, 'Max Versions'),
        (ULONG, 'Version Number'),

        #(ULONG, 'Class Id'),
        #(ULONG, 'Owner Id'),
        #(ULONG, 'Security Id'),
        #(ULONGLONG, 'Quota Charged'),
        #(ULONGLONG, 'Update Sequence Number'),
        #(dyn.block(8), 'unused'),
    ]

@MFT_Attribute.define
class File_Name(pstruct.type):
    '''$FILE_NAME'''
    id = 0x30

    class _Name_Type(pint.enum, BYTE):
        _values_ = [
            ('POSIX', 0),
            ('Win32', 1),
            ('DOS', 2),
            ('7DOS', 3),
        ]

    _fields_ = [
        (ULONGLONG, 'Parent Directory'),
        (ULONGLONG, 'Date Created'),
        (ULONGLONG, 'Date Modified'),
        (ULONGLONG, 'Date MFT Modified'),
        (ULONGLONG, 'Date Accessed'),
        (ULONGLONG, 'Logical Size'),
        (ULONGLONG, 'Physical Size'),
        (Standard_Flags, 'Flags'),
        (ULONG, 'Reparse Value'),
        (BYTE, 'Name Length'),
        (_Name_Type, 'Name Type'),
        (lambda self: dyn.block(self['Name Length'].li.int()), 'Name'),
    ]

### FIXME: integrate this into the deviceiocontrol context manager, maybe fix the names too
class USNRecord(pstruct.type):
    @pbinary.littleendian
    class _reason(pbinary.flags):
        _fields_ = [
            (1, 'CLOSE'),
            (9, 'RESERVED'),
            (1, 'STREAM_CHANGE'),
            (1, 'REPARSE_POINT_CHANGE'),
            (1, 'OBJECT_ID_CHANGE'),
            (1, 'ENCRYPTION_CHANGE'),
            (1, 'COMPRESSION_CHANGE'),
            (1, 'HARD_LINK_CHANGE'),
            (1, 'BASIC_INFO_CHANGE'),
            (1, 'INDEXABLE_CHANGE'),
            (1, 'RENAME_NEW_NAME'),
            (1, 'RENAME_OLD_NAME'),
            (1, 'SECURITY_CHANGE'),
            (1, 'EA_CHANGE'),
            (1, 'FILE_DELETE'),
            (1, 'FILE_CREATE'),
            (1, 'unknown(7)'),
            (1, 'NAMED_DATA_TRUNCATION'),
            (1, 'NAMED_DATA_EXTEND'),
            (1, 'NAMED_DATA_OVERWRITE'),
            (1, 'unknown(3)'),
            (1, 'DATA_TRUNCATION'),
            (1, 'DATA_EXTEND'),
            (1, 'DATA_OVERWRITE'),
        ]

    @pbinary.littleendian
    class _fileAttributes(pbinary.flags):
        _fields_ = [
            (14, 'RESERVED'),
            (1, 'NO_SCRUB_DATA'),
            (1, 'VIRTUAL'),
            (1, 'INTEGRITY_STREAM'),
            (1, 'ENCRYPTED'),
            (1, 'NOT_CONTENT_INDEXED'),
            (1, 'OFFLINE'),
            (1, 'COMPRESSED'),
            (1, 'REPARSE_POINT'),
            (1, 'SPARSE_FILE'),
            (1, 'TEMPORARY'),
            (1, 'NORMAL'),
            (1, 'DEVICE'),
            (1, 'ARCHIVE'),
            (1, 'DIRECTORY'),
            (1, 'unknown'),
            (1, 'SYSTEM'),
            (1, 'HIDDEN'),
            (1, 'READONLY'),
        ]

    @pbinary.littleendian
    class _referenceNumber(pbinary.struct):
        _fields_ = [
            (16, 'sequenceNumber'),
            (48, 'entryNumber'),
        ]
    def __filenameOffset(self):
        length = self['filenameLength'].li
        t = dyn.clone(pstr.wstring, length=length.int())
        return dyn.rpointer(t, self, USHORT)
    _fields_ = [
        (USHORT, 'majorVersion'),
        (USHORT, 'minorVersion'),
        (_referenceNumber, 'fileReferenceNumber'),
        (_referenceNumber, 'parentFileReferenceNumber'),
        (ULONGLONG, 'usn'),
        (ULONGLONG, 'timestamp'),                           # might be an ndk.FILETIME from epoch
        (_reason, 'reason'),
        (ULONG, 'sourceInfo'),
        (ULONG, 'securityId'),
        (_fileAttributes, 'fileAttributes'),
        (USHORT, 'filenameLength'),
        (__filenameOffset, 'filenameOffset'),               # this is an rpointer to a utf16 pstr.swstring
    ]

class USNJournal(parray.block):
    class Record(pstruct.type):
        def __content(self):
            res, fields = self['length'].li, ['length', 'record']
            return dyn.block(max(0, res - sum(self[fld].li.size() for fld in fields)))
        _fields_ = [
            (ULONG, 'length'),
            (USNRecord, 'record'),
            (__content, 'content'),
        ]
    _object_ = Record
