import ptypes, ndk, office.propertyset
from ptypes import *
from ndk.datatypes import *

class uint0(pint.uint_t):
    length = 0

class GUID(ndk.GUID):
    pass

@pbinary.littleendian
class LinkFlags(pbinary.flags):
    _fields_ = [
        (1, 'HasLinkTargetIDList'),         # The shell link is saved with an item ID list (IDList). If this bit is set, a LinkTargetIDList structure (section 2.2) MUST follow the ShellLinkHeader. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasLinkInfo'),                 # The shell link is saved with link information. If this bit is set, a LinkInfo structure (section 2.3) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasName'),                     # The shell link is saved with a name string. If this bit is set, a NAME_STRING StringData structure (section 2.4) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasRelativePath'),             # The shell link is saved with a relative path string. If this bit is set, a RELATIVE_PATH StringData structure (section 2.4) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasWorkingDir'),               # The shell link is saved with a working directory string. If this bit is set, a WORKING_DIR StringData structure (section 2.4) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasArguments'),                # The shell link is saved with command line arguments. If this bit is set, a COMMAND_LINE_ARGUMENTS StringData structure (section 2.4) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'HasIconLocation'),             # The shell link is saved with an icon location string. If this bit is set, an ICON_LOCATION StringData structure (section 2.4) MUST be present. If this bit is not set, this structure MUST NOT be present.
        (1, 'IsUnicode'),                   # The shell link contains Unicode encoded strings. This bit SHOULD be set. If this bit is set, the StringData section contains Unicode-encoded strings; otherwise, it contains strings that are encoded using the system default code page.
        (1, 'ForceNoLinkInfo'),             # The LinkInfo structure (section 2.3) is ignored.
        (1, 'HasExpString'),                # The shell link is saved with an EnvironmentVariableDataBlock (section 2.5.4).
        (1, 'RunInSeparateProcess'),        # The target is run in a separate virtual machine when launching a link target that is a 16-bit application.
        (1, 'Unused1'),                     # A bit that is undefined and MUST be ignored.
        (1, 'HasDarwinID'),                 # The shell link is saved with a DarwinDataBlock (section 2.5.3).
        (1, 'RunAsUser'),                   # The application is run as a different user when the target of the shell link is activated.
        (1, 'HasExpIcon'),                  # The shell link is saved with an IconEnvironmentDataBlock (section 2.5.5).
        (1, 'NoPidlAlias'),                 # The file system location is represented in the shell namespace when the path to an item is parsed into an IDList.
        (1, 'Unused2'),                     # A bit that is undefined and MUST be ignored.
        (1, 'RunWithShimLayer'),            # The shell link is saved with a ShimDataBlock (section 2.5.8).
        (1, 'ForceNoLinkTrack'),            # The TrackerDataBlock (section 2.5.10) is ignored.
        (1, 'EnableTargetMetadata'),        # The shell link attempts to collect target properties and store them in the PropertyStoreDataBlock (section 2.5.7) when the link target is set.
        (1, 'DisableLinkPathTracking'),     # The EnvironmentVariableDataBlock is ignored.
        (1, 'DisableKnownFolderTracking'),  # The SpecialFolderDataBlock (section 2.5.9) and the KnownFolderDataBlock (section 2.5.6) are ignored when loading the shell link. If this bit is set, these extra data blocks SHOULD NOT be saved when saving the shell link.
        (1, 'DisableKnownFolderAlias'),     # If the link has a KnownFolderDataBlock (section 2.5.6), the unaliased form of the known folder IDList SHOULD be used when translating the target IDList at the time that the link is loaded.
        (1, 'AllowLinkToLink'),             # Creating a link that references another link is enabled. Otherwise, specifying a link as the target IDList SHOULD NOT be allowed.
        (1, 'UnaliasOnSave'),               # When saving a link for which the target IDList is under a known folder, either the unaliased form of that known folder or the target IDList SHOULD be used.
        (1, 'PreferEnvironmentPath'),       # The target IDList SHOULD NOT be stored; instead, the path specified in the EnvironmentVariableDataBlock (section 2.5.4) SHOULD be used to refer to the target.
        (1, 'KeepLocalIDListForUNCTarget'), # When the target is a UNC name that refers to a location on a local machine, the local path IDList in the PropertyStoreDataBlock (section 2.5.7) SHOULD be stored, so it can be used when the link is loaded on the local machine.
        (5, 'Unused'),
    ][::-1]

@pbinary.littleendian
class FileAttributesFlags(pbinary.flags):
    _fields_ = [
        (1, 'FILE_ATTRIBUTE_READONLY'),             # The file or directory is read-only. For a file, if this bit is set, applications can read the file but cannot write to it or delete it. For a directory, if this bit is set, applications cannot delete the directory.
        (1, 'FILE_ATTRIBUTE_HIDDEN'),               # The file or directory is hidden. If this bit is set, the file or folder is not included in an ordinary directory listing.
        (1, 'FILE_ATTRIBUTE_SYSTEM'),               # The file or directory is part of the operating system or is used exclusively by the operating system.
        (1, 'Reserved1'),                           # A bit that MUST be zero.
        (1, 'FILE_ATTRIBUTE_DIRECTORY'),            # The link target is a directory instead of a file.
        (1, 'FILE_ATTRIBUTE_ARCHIVE'),              # The file or directory is an archive file. Applications use this flag to mark files for backup or removal.
        (1, 'Reserved2'),                           # A bit that MUST be zero.
        (1, 'FILE_ATTRIBUTE_NORMAL'),               # The file or directory has no other flags set. If this bit is 1, all other bits in this structure MUST be clear.
        (1, 'FILE_ATTRIBUTE_TEMPORARY'),            # The file is being used for temporary storage.
        (1, 'FILE_ATTRIBUTE_SPARSE_FILE'),          # The file is a sparse file.
        (1, 'FILE_ATTRIBUTE_REPARSE_POINT'),        # The file or directory has an associated reparse point.
        (1, 'FILE_ATTRIBUTE_COMPRESSED'),           # The file or directory is compressed. For a file, this means that all data in the file is compressed. For a directory, this means that compression is the default for newly created files and subdirectories.
        (1, 'FILE_ATTRIBUTE_OFFLINE'),              # The data of the file is not immediately available.
        (1, 'FILE_ATTRIBUTE_NOT_CONTENT_INDEXED'),  # The contents of the file need to be indexed.
        (1, 'FILE_ATTRIBUTE_ENCRYPTED'),            # The file or directory is encrypted. For a file, this means that all data in the file is encrypted. For a directory, this means that encryption is the default for newly created files and subdirectories.
        (17, 'Unused'),
    ][::-1]

class SW_SHOW(pint.enum, DWORD):
    _values_ = [
        ('NORMAL', 1),
        ('MAXIMIZED', 3),
        ('MINNOACTIVE', 7),
    ]

class VK_(pint.enum, BYTE):
    _values_ = [
        ('None', 0x00),         # No key assigned.
        ('VK_0', 0x30),         # "0" key
        ('VK_1', 0x31),         # "1" key
        ('VK_2', 0x32),         # "2" key
        ('VK_3', 0x33),         # "3" key
        ('VK_4', 0x34),         # "4" key
        ('VK_5', 0x35),         # "5" key
        ('VK_6', 0x36),         # "6" key
        ('VK_7', 0x37),         # "7" key
        ('VK_8', 0x38),         # "8" key
        ('VK_9', 0x39),         # "9" key
        ('VK_A', 0x41),         # "A" key
        ('VK_B', 0x42),         # "B" key
        ('VK_C', 0x43),         # "C" key
        ('VK_D', 0x44),         # "D" key
        ('VK_E', 0x45),         # "E" key
        ('VK_F', 0x46),         # "F" key
        ('VK_G', 0x47),         # "G" key
        ('VK_H', 0x48),         # "H" key
        ('VK_I', 0x49),         # "I" key
        ('VK_J', 0x4A),         # "J" key
        ('VK_K', 0x4B),         # "K" key
        ('VK_L', 0x4C),         # "L" key
        ('VK_M', 0x4D),         # "M" key
        ('VK_N', 0x4E),         # "N" key
        ('VK_O', 0x4F),         # "O" key
        ('VK_P', 0x50),         # "P" key
        ('VK_Q', 0x51),         # "Q" key
        ('VK_R', 0x52),         # "R" key
        ('VK_S', 0x53),         # "S" key
        ('VK_T', 0x54),         # "T" key
        ('VK_U', 0x55),         # "U" key
        ('VK_V', 0x56),         # "V" key
        ('VK_W', 0x57),         # "W" key
        ('VK_X', 0x58),         # "X" key
        ('VK_Y', 0x59),         # "Y" key
        ('VK_Z', 0x5A),         # "Z" key
        ('VK_F1', 0x70),        # "F1" key
        ('VK_F2', 0x71),        # "F2" key
        ('VK_F3', 0x72),        # "F3" key
        ('VK_F4', 0x73),        # "F4" key
        ('VK_F5', 0x74),        # "F5" key
        ('VK_F6', 0x75),        # "F6" key
        ('VK_F7', 0x76),        # "F7" key
        ('VK_F8', 0x77),        # "F8" key
        ('VK_F9', 0x78),        # "F9" key
        ('VK_F10', 0x79),       # "F10" key
        ('VK_F11', 0x7A),       # "F11" key
        ('VK_F12', 0x7B),       # "F12" key
        ('VK_F13', 0x7C),       # "F13" key
        ('VK_F14', 0x7D),       # "F14" key
        ('VK_F15', 0x7E),       # "F15" key
        ('VK_F16', 0x7F),       # "F16" key
        ('VK_F17', 0x80),       # "F17" key
        ('VK_F18', 0x81),       # "F18" key
        ('VK_F19', 0x82),       # "F19" key
        ('VK_F20', 0x83),       # "F20" key
        ('VK_F21', 0x84),       # "F21" key
        ('VK_F22', 0x85),       # "F22" key
        ('VK_F23', 0x86),       # "F23" key
        ('VK_F24', 0x87),       # "F24" key
        ('VK_NUMLOCK', 0x90),   # "NUM LOCK" key
        ('VK_SCROLL', 0x91),    # "SCROLL LOCK" key
    ]

class HOTKEYF_(pbinary.flags):
    _fields_ = [
        (5, 'RESERVED'),
        (1, 'ALT'),
        (1, 'CONTROL'),
        (1, 'SHIFT'),
    ]

class HotKeyFlags(pstruct.type):
    _fields_ = [
        (VK_, 'LowByte'),
        (HOTKEYF_, 'HighByte'),
    ]

class ShellLinkHeader(pstruct.type):
    def blocksize(self):
        # If we're allocated, then we can just read our size field to determine
        # the blocksize, otherwise we need to cheat and assume it's a complete
        # structure. We do this by making a copy using the original blocksize
        # to allocate it and calculate the expected size.
        Fblocksize = super(ShellLinkHeader, self).blocksize
        return self['HeaderSize'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    def __Reserved(type, required):
        def Freserved(self):
            expected = self['HeaderSize'].li
            return type if required <= expected.int() else uint0
        return Freserved

    def __Padding(self):
        expected, fields = self['HeaderSize'].li, ['HeaderSize', 'LinkCLSID', 'LinkFlags', 'FileAttributes', 'CreationTime', 'AccessTime', 'WriteTime', 'FileSize', 'IconIndex', 'ShowCommand', 'HotKey', 'Reserved1', 'Reserved2', 'Reserved3']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'HeaderSize'),
        (CLSID, 'LinkCLSID'),
        (LinkFlags, 'LinkFlags'),
        (FileAttributesFlags, 'FileAttributes'),
        (FILETIME, 'CreationTime'),
        (FILETIME, 'AccessTime'),
        (FILETIME, 'WriteTime'),
        (DWORD, 'FileSize'),
        (DWORD, 'IconIndex'),
        (SW_SHOW, 'ShowCommand'),
        (HotKeyFlags, 'HotKey'),
        (__Reserved(WORD, 0x44), 'Reserved1'),
        (__Reserved(DWORD, 0x48), 'Reserved2'),
        (__Reserved(DWORD, 0x4c), 'Reserved3'),
        (__Padding, 'Padding'),
    ]

class ItemID(pstruct.type):
    def __Data(self):
        expected, fields = self['ItemIDSize'].li, ['ItemIDSize']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (WORD, 'ItemIDSize'),
        (__Data, 'Data'),
    ]

class IDList(parray.terminated):
    _object_ = ItemID
    def isTerminator(self, item):
        return item['ItemIDSize'].int() == 0

class LinkTargetIDList(pstruct.type):
    def __padding_IDList(self):
        expected = self['IDListSize'].li.int()
        return dyn.block(max(0, expected - self['IDList'].li.size()))

    _fields_ = [
        (WORD, 'IDListSize'),
        (IDList, 'IDList'),
        (__padding_IDList, 'padding(IDList)'),
    ]

class DRIVE_(pint.enum, DWORD):
    _values_ = [
        ('UNKNOWN', 0x00000000),      # The drive type cannot be determined.
        ('NO_ROOT_DIR', 0x00000001),  # The root path is invalid; for example, there is no volume mounted at the path.
        ('REMOVABLE', 0x00000002),    # The drive has removable media, such as a floppy drive, thumb drive, or flash card reader.
        ('FIXED', 0x00000003),        # The drive has fixed media, such as a hard drive or flash drive.
        ('REMOTE', 0x00000004),       # The drive is a remote (network) drive.
        ('CDROM', 0x00000005),        # The drive is a CD-ROM drive.
        ('RAMDISK', 0x00000006),      # The drive is a RAM disk.
    ]

class VolumeID(pstruct.type):
    def blocksize(self):
        # If we're allocated, then we can just read our size field to determine
        # the blocksize, otherwise we need to cheat and assume it's a complete
        # structure. We do this by making a copy using the original blocksize
        # to allocate it and calculate the expected size.
        Fblocksize = super(VolumeID, self).blocksize
        return self['VolumeIDSize'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    def __VolumeLabelOffset(self):
        size = self['VolumeIDSize'].li
        if size.int() < 0x10:
            return dyn.rpointer(pstr.szstring, self, uint0)
        return dyn.rpointer(pstr.szstring, self, DWORD)

    def __VolumeLabelOffsetUnicode(self):
        size, offset = (self[fld].li for fld in ['VolumeIDSize', 'VolumeLabelOffset'])
        t = uint0 if any(item.int() < 0x14 for item in {size, offset}) else DWORD
        return dyn.rpointer(pstr.szwstring, self, t)

    def __Data(self):
        expected, fields = self['VolumeIDSize'].li.int(), ['VolumeIDSize', 'DriveType', 'DriveSerialNumber', 'VolumeLabelOffset', 'VolumeLabelOffsetUnicode']
        return dyn.block(max(0, expected - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'VolumeIDSize'),
        (DRIVE_, 'DriveType'),
        (DWORD, 'DriveSerialNumber'),
        (__VolumeLabelOffset, 'VolumeLabelOffset'),
        (__VolumeLabelOffsetUnicode, 'VolumeLabelOffsetUnicode'),
        #(ptype.undefined, 'VolumeLabelOffset'),
        #(ptype.undefined, 'VolumeLabelOffsetUnicode'),

        # This data contains the two previously defined strings
        (__Data, 'Data'),
    ]

class WNNC_NET_(pint.enum, DWORD):
    _values_ = [
        ('AVID', 0x001A0000),
        ('DOCUSPACE', 0x001B0000),
        ('MANGOSOFT', 0x001C0000),
        ('SERNET', 0x001D0000),
        ('RIVERFRONT1', 0X001E0000),
        ('RIVERFRONT2', 0x001F0000),
        ('DECORB', 0x00200000),
        ('PROTSTOR', 0x00210000),
        ('FJ_REDIR', 0x00220000),
        ('DISTINCT', 0x00230000),
        ('TWINS', 0x00240000),
        ('RDR2SAMPLE', 0x00250000),
        ('CSC', 0x00260000),
        ('3IN1', 0x00270000),
        ('EXTENDNET', 0x00290000),
        ('STAC', 0x002A0000),
        ('FOXBAT', 0x002B0000),
        ('YAHOO', 0x002C0000),
        ('EXIFS', 0x002D0000),
        ('DAV', 0x002E0000),
        ('KNOWARE', 0x002F0000),
        ('OBJECT_DIRE', 0x00300000),
        ('MASFAX', 0x00310000),
        ('HOB_NFS', 0x00320000),
        ('SHIVA', 0x00330000),
        ('IBMAL', 0x00340000),
        ('LOCK', 0x00350000),
        ('TERMSRV', 0x00360000),
        ('SRT', 0x00370000),
        ('QUINCY', 0x00380000),
        ('OPENAFS', 0x00390000),
        ('AVID1', 0X003A0000),
        ('DFS', 0x003B0000),
        ('KWNP', 0x003C0000),
        ('ZENWORKS', 0x003D0000),
        ('DRIVEONWEB', 0x003E0000),
        ('VMWARE', 0x003F0000),
        ('RSFX', 0x00400000),
        ('MFILES', 0x00410000),
        ('MS_NFS', 0x00420000),
        ('GOOGLE', 0x00430000),
    ]

class CommonNetworkRelativeLink(pstruct.type):
    def blocksize(self):
        # If we're allocated, then we can just read our size field to determine
        # the blocksize, otherwise we need to cheat and assume it's a complete
        # structure. We do this by making a copy using the original blocksize
        # to allocate it and calculate the expected size.
        Fblocksize = super(CommonNetworkRelativeLink, self).blocksize
        return self['CommonNetworkRelativeLinkSize'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    @pbinary.littleendian
    class _CommonNetworkRelativeLinkFlags(pbinary.flags):
        _fields_ = [
            (1, 'ValidDevice'),
            (1, 'ValidNetType'),
            (30, 'Unused'),
        ][::-1]

    def __CommonNetworkRelativeLinkOffset(target, required):
        def Foffset(self):
            expected = self['CommonNetworkRelativeLinkSize'].li
            t = uint0 if required < expected.int() else DWORD
            return dyn.rpointer(target, self, t)
        return Foffset

    def __CommonNetworkRelativeLinkData(self):
        expected, fields = self['CommonNetworkRelativeLinkSize'].li, ['CommonNetworkRelativeLinkSize', 'CommonNetworkRelativeLinkFlags', 'NetNameOffset', 'DeviceNameOffset', 'NetworkProviderType' 'NetNameOffsetUnicode', 'DeviceNameOffsetUnicode']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'CommonNetworkRelativeLinkSize'),
        (_CommonNetworkRelativeLinkFlags, 'CommonNetworkRelativeLinkFlags'),
        (__CommonNetworkRelativeLinkOffset(pstr.szstring, 0xc), 'NetNameOffset'),
        (__CommonNetworkRelativeLinkOffset(pstr.szstring, 0x10), 'DeviceNameOffset'),   # ValidDevice
        (WNNC_NET_, 'NetworkProviderType'),                                             # ValidNetType

        ### These are conditional depending on the size
        (__CommonNetworkRelativeLinkOffset(pstr.szwstring, 0x18), 'NetNameOffsetUnicode'),
        (__CommonNetworkRelativeLinkOffset(pstr.szwstring, 0x1c), 'DeviceNameOffsetUnicode'),

        ### These might be in an arbitrary order despite what the documentation claims
        #(pstr.szstring, 'NetName'),
        #(pstr.szstring, 'DeviceName'),
        #(pstr.szwstring, 'NetNameUnicode'),
        #(pstr.szwstring, 'DeviceNameUnicode'),
        (__CommonNetworkRelativeLinkData, 'CommonNetworkRelativeLinkData'),
    ]

class LinkInfo(pstruct.type):
    def blocksize(self):
        # If we're allocated, then we can just read our size field to determine
        # the blocksize, otherwise we need to cheat and assume it's a complete
        # structure. We do this by making a copy using the original blocksize
        # to allocate it and calculate the expected size.
        Fblocksize = super(LinkInfo, self).blocksize
        return self['LinkInfoSize'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    @pbinary.littleendian
    class _LinkInfoFlags(pbinary.flags):
        _fields_ = [
            (1, 'VolumeIDAndLocalBasePath'),
            (1, 'CommonNetworkRelativeLinkAndPathSuffix'),
            (30, 'Unused'),
        ][::-1]

    def __LinkInfoHeaderOffset(target, required):
        def Foffset(self):
            expected = self['LinkInfoHeaderSize'].li
            t = DWORD if required <= expected.int() else uint0
            return dyn.rpointer(target, self, t)
        return Foffset

    def __LinkInfoData(self):
        expected, header = (self[fld].li for fld in ['LinkInfoSize', 'LinkInfoHeaderSize'])
        return dyn.block(max(0, expected.int() - header.int()))

    _fields_ = [
        (DWORD, 'LinkInfoSize'),
        (DWORD, 'LinkInfoHeaderSize'),
        (_LinkInfoFlags, 'LinkInfoFlags'),

        ### XXX: These are conditional depending on the LinkInfoFlags and sized by LinkInfoHeaderSize
        (__LinkInfoHeaderOffset(VolumeID, 0x10), 'VolumeIDOffset'),                                     # VolumeIDAndLocalBasePath
        (__LinkInfoHeaderOffset(pstr.szstring, 0x14), 'LocalBasePathOffset'),                           # VolumeIDAndLocalBasePath
        (__LinkInfoHeaderOffset(CommonNetworkRelativeLink, 0x18), 'CommonNetworkRelativeLinkOffset'),   # CommonNetworkRelativeLinkAndPathSuffix
        (__LinkInfoHeaderOffset(pstr.szstring, 0x1c), 'CommonPathSuffixOffset'),                        #
        (__LinkInfoHeaderOffset(pstr.szwstring, 0x20), 'LocalBasePathOffsetUnicode'),                   # VolumeIDAndLocalBasePath
        (__LinkInfoHeaderOffset(pstr.szwstring, 0x24), 'CommonPathSuffixOffsetUnicode'),                # If size >= 0x24

        ### These might be in an arbitrary order despite what the documentation claims
        #(VolumeID, 'VolumeID'), #
        #(pstr.szwstring, 'LocalBasePath'), #
        #(CommonNetworkRelativeLink, 'CommonNetworkRelativeLink'),
        #(pstr.szwstring, 'CommonPathSuffix'), #
        #(pstr.szwstring, 'LocalBasePathUnicode'),
        #(pstr.szwstring, 'CommonPathSuffixUnicode'),
        (__LinkInfoData, 'LinkInfoData'),
    ]

class StringData(pstruct.type):
    _fields_ = [
        (WORD, 'CountCharacters'),
        (pstr.string, 'String'),
    ]

    def str(self):
        item = self['String']
        return item.str()

    def summary(self):
        count, string = self['CountCharacters'], self.str()
        return "(CountCharacters={:d}) String: {:s}".format(count.int(), string)

class AnsiStringData(StringData):
    _fields_ = [
        (WORD, 'CountCharacters'),
        (lambda self: dyn.clone(pstr.string, length=self['CountCharacters'].li.int()), 'String'),
    ]

class UnicodeStringData(StringData):
    _fields_ = [
        (WORD, 'CountCharacters'),
        (lambda self: dyn.clone(pstr.wstring, length=self['CountCharacters'].li.int()), 'String'),
    ]

class EXTRA_DATA(ptype.definition):
    attribute, cache = 'signature', {}

class EXTRA_DATA_BLOCK(pint.enum, DWORD):
    _values_ = [
        ('CONSOLE_PROPS', 0xA0000002),                  # A ConsoleDataBlock structure (section 2.5.1).
        ('CONSOLE_FE_PROPS', 0xA0000004),               # A ConsoleFEDataBlock structure (section 2.5.2).
        ('DARWIN_PROPS', 0xA0000006),                   # A DarwinDataBlock structure (section 2.5.3).
        ('ENVIRONMENT_PROPS', 0xA0000001),              # An EnvironmentVariableDataBlock structure (section 2.5.4).
        ('ICON_ENVIRONMENT_PROPS', 0xA0000007),         # An IconEnvironmentDataBlock structure (section 2.5.5).
        ('KNOWN_FOLDER_PROPS', 0xA000000B),             # A KnownFolderDataBlock structure (section 2.5.6).
        ('PROPERTY_STORE_PROPS', 0xA0000009),           # A PropertyStoreDataBlock structure (section 2.5.7).
        ('SHIM_PROPS', 0xA0000008),                     # A ShimDataBlock structure (section 2.5.8).
        ('SPECIAL_FOLDER_PROPS', 0xA0000005),           # A SpecialFolderDataBlock structure (section 2.5.9).
        ('TRACKER_PROPS', 0xA0000003),                  # A TrackerDataBlock structure (section 2.5.10).
        ('VISTA_AND_ABOVE_IDLIST_PROPS', 0xA000000C),   # A VistaAndAboveIDListDataBlock structure (section 2.5.11).
    ]

class ExtraDataBlock(pstruct.type):
    def __BlockData(self):
        size, signature = (self[fld].li for fld in ['BlockSize', 'BlockSignature'])
        total, fields = self['BlockSize'].li.int(), ['BlockSize', 'BlockSignature']
        expected = total - sum(self[fld].li.size() for fld in fields)
        return EXTRA_DATA.withdefault(signature.int(), ptype.block, length=max(0, expected))

    def __padding_BlockData(self):
        expected, fields = self['BlockSize'].li.int(), ['BlockSize', 'BlockSignature', 'BlockData']
        return dyn.block(max(0, expected - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'BlockSize'),
        (lambda self: dyn.clone(EXTRA_DATA_BLOCK, length=0) if self['BlockSize'].li.int() < 8 else EXTRA_DATA_BLOCK, 'BlockSignature'),
        (__BlockData, 'BlockData'),
        (__padding_BlockData, 'padding(BlockData)'),
    ]

class ExtraData(parray.terminated):
    _object_ = ExtraDataBlock
    def isTerminator(self, item):
        return item['BlockSize'].int() < 4

### extra data blocks
class RGBI(pbinary.flags):
    _fields_ = [
        (1, 'INTENSITY'),
        (1, 'RED'),
        (1, 'GREEN'),
        (1, 'BLUE'),
    ]

class FOREGROUND_(RGBI): pass
class BACKGROUND_(RGBI): pass

class FF_(pbinary.enum):
    length, _values_ = 4, [
        ('DONTCARE', 0),
        ('ROMAN', 1),
        ('SWISS', 2),
        ('MODERN', 3),
        ('SCRIPT', 4),
        ('DECORATIVE', 4),
    ]

class TMPF_(pbinary.flags):
    _fields_ = [
        (1, 'DEVICE'),
        (1, 'TRUETYPE'),
        (1, 'VECTOR'),
        (1, 'FIXED_PITCH'),
    ]

@EXTRA_DATA.define
class ConsoleDataBlock(pstruct.type):
    signature = 0xA0000002

    @pbinary.littleendian
    class _FillAttributes(pbinary.flags):
        _fields_ = [
            (8, 'Unused'),
            (BACKGROUND_, 'BACKGROUND'),
            (FOREGROUND_, 'FOREGROUND'),
        ]

    @pbinary.littleendian
    class _FontFamily(pbinary.struct):
        _fields_ = [
            (24, 'Unused'),
            (FF_, 'Family'),
            (TMPF_, 'Pitch'),
        ]

    _fields_ = [
        (_FillAttributes, 'FillAttributes'),
        (_FillAttributes, 'PopupFillAttributes'),
        (INT16, 'ScreenBufferSizeX'),
        (INT16, 'ScreenBufferSizeY'),
        (INT16, 'WindowSizeX'),
        (INT16, 'WindowSizeY'),
        (INT16, 'WindowOriginX'),
        (INT16, 'WindowOriginY'),
        (DWORD, 'Unused1'),
        (DWORD, 'Unused2'),
        (DWORD, 'FontSize'),
        (_FontFamily, 'FontFamily'),
        (DWORD, 'FontWeight'),
        (dyn.clone(pstr.wstring, length=32), 'Face Name'),
        (DWORD, 'CursorSize'),
        (DWORD, 'FullScreen'),
        (DWORD, 'QuickEdit'),
        (DWORD, 'InsertMode'),
        (DWORD, 'AutoPosition'),
        (DWORD, 'HistoryBufferSize'),
        (DWORD, 'NumberOfHistoryBuffers'),
        (DWORD, 'HistoryNoDup'),
        (dyn.array(DWORD, 16), 'ColorTable'),
    ]

@EXTRA_DATA.define
class ConsoleFEDataBlock(pstruct.type):
    signature = 0xA0000004
    _fields_ = [
        (DWORD, 'CodePage'),
    ]

@EXTRA_DATA.define
class DarwinDataBlock(pstruct.type):
    signature = 0xA0000006
    def __padding(field, size):
        def Fpadding(self):
            return dyn.block(max(0, size - self[field].li.size()))
        return Fpadding
    _fields_ = [
        (pstr.szstring, 'DarwinDataAnsi'),
        (__padding('DarwinDataAnsi', 260), 'padding(DarwinDataAnsi)'),
        (pstr.szwstring, 'DarwinDataUnicode'),
        (__padding('DarwinDataUnicode', 520), 'padding(DarwinDataUnicode)'),
    ]

@EXTRA_DATA.define
class EnvironmentVariableDataBlock(pstruct.type):
    signature = 0xA0000001
    def __padding(field, size):
        def Fpadding(self):
            return dyn.block(max(0, size - self[field].li.size()))
        return Fpadding
    _fields_ = [
        (pstr.szstring, 'TargetAnsi'),
        (__padding('TargetAnsi', 260), 'padding(TargetAnsi)'),
        (pstr.szwstring, 'TargetUnicode'),
        (__padding('TargetUnicode', 520), 'padding(TargetUnicode)'),
    ]

@EXTRA_DATA.define
class IconEnvironmentDataBlock(EnvironmentVariableDataBlock):
    signature = 0xA0000007

@EXTRA_DATA.define
class KnownFolderDataBlock(pstruct.type):
    signature = 0xA000000B
    _fields_ = [
        (GUID, 'KnownFolderID'),
        (DWORD, 'Offset'),
    ]

class SerializedPropertyValueStringName(pstruct.type):
    _fields_ = [
        (DWORD, 'Value Size'),
        (DWORD, 'Name Size'),
        (BYTE, 'Reserved'),
        (pstr.szwstring, 'Name'),
        (lambda self: dyn.block(max(0, self['Name Size'].li.int() - self['Name'].li.size())), 'padding(Name)'),
        (office.propertyset.TypedPropertyValue, 'Value'),
        (lambda self: dyn.block(max(0, self['Value Size'].li.int() - self['Value'].li.size())), 'padding(Value)'),
    ]

class SerializedPropertyValueIntegerName(pstruct.type):
    _fields_ = [
        (DWORD, 'Value Size'),
        (DWORD, 'Id'),
        (BYTE, 'Reserved'),
        (office.propertyset.TypedPropertyValue, 'Value'),
        (lambda self: dyn.block(max(0, self['Value Size'].li.int() - self['Value'].li.size())), 'padding(Value)'),
    ]

@EXTRA_DATA.define
class PropertyStoreDataBlock(pstruct.type):
    signature = 0xA0000009

    class _Serialized_Property_Value(parray.terminated):
        def isTerminator(self, item):
            return item['Value Size'].int() == 0

    def __Serialized_Property_Value(self):
        format = self['Format ID']
        items = [component for component in format.iterate()]
        if items == [0xD5CDD505, 0x2E9C, 0x101B, 0x9397, 0x08002B2CF9AE]:
            t = SerializedPropertyValueStringName
        else:
            t = SerializedPropertyValueIntegerName
        return dyn.clone(self._Serialized_Property_Value, _object_=t)

    def __padding_Serialized_Property_Value(self):
        expected, fields = self['Storage Size'].li, ['Storage Size', 'Version', 'Format ID']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'Storage Size'),
        (DWORD, 'Version'),
        (GUID, 'Format ID'),
        (__Serialized_Property_Value, 'Serialized Property Value'),
        (__padding_Serialized_Property_Value, 'padding(Serialized Property Value)'),
    ]

@EXTRA_DATA.define
class ShimDataBlock(pstruct.type):
    signature = 0xA0000008
    def __LayerName(self):
        p = self.parent
        if p:
            size = p['BlockSize'].li.int() - sum(p[fld].li.size() for fld in ['BlockSize', 'BlockSignature'])
            return dyn.clone(pstr.wstring, length=size // 2)
        return pstr.wstring

    _fields_ = [
        (__LayerName, 'LayerName'),
    ]

@EXTRA_DATA.define
class SpecialFolderDataBlock(pstruct.type):
    signature = 0xA0000005
    _fields_ = [
        (DWORD, 'SpecialFolderID'),
        (DWORD, 'Offset'),
    ]

@EXTRA_DATA.define
class TrackerDataBlock(pstruct.type):
    signature = 0xA0000003

    class _Droid(parray.type):
        length, _object_ = 2, GUID
        def summary(self):
            items = [item.str() for item in self]
            return "({:d}) {:s}".format(len(items), ', '.join(items))

    _fields_ = [
        (DWORD, 'Length'),
        (DWORD, 'Version'),
        (dyn.clone(pstr.string, length=16), 'MachineID'),
        (_Droid, 'Droid'),
        (_Droid, 'DroidBirth'),
    ]

@EXTRA_DATA.define
class VistaAndAboveIDListDataBlock(IDList):
    signature = 0xA000000C

class File(pstruct.type):
    def __ConditionalType(flag, type):
        def Ftype(self):
            header = self['Header'].li
            return type if header['LinkFlags'][flag] else ptype.undefined
        return Ftype

    def __ConditionalStringData(flag):
        def FStringData(self):
            header = self['Header'].li
            string_t = UnicodeStringData if header['LinkFlags']['IsUnicode'] else AnsiStringData
            return string_t if header['LinkFlags'][flag] else ptype.undefined
        return FStringData

    _fields_ = [
        (ShellLinkHeader, 'Header'),
        (__ConditionalType('HasLinkTargetIDList', LinkTargetIDList), 'IDList'), # HasLinkTargetIDList
        (__ConditionalType('HasLinkInfo', LinkInfo), 'Info'),                   # HasLinkInfo

        (__ConditionalStringData('HasName'), 'NAME_STRING'),                    # HasName
        (__ConditionalStringData('HasRelativePAth'), 'RELATIVE_PATH'),          # HasRelativePath
        (__ConditionalStringData('HasWorkingDir'), 'WORKING_DIR'),              # HasWorkingDir
        (__ConditionalStringData('HasArguments'), 'COMMAND_LINE_ARGUMENTS'),    # HasArguments
        (__ConditionalStringData('HasIconLocation'), 'ICON_LOCATION'),          # HasIconLocation

        (ExtraData, 'Extra'),
    ]

if __name__ == '__main__':
    import builtins, operator, os, math, functools, itertools, sys, types

    #    x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    0000 4C 00 00 00 01 14 02 00 00 00 00 00 C0 00 00 00
    0010 00 00 00 46 9B 00 08 00 20 00 00 00 D0 E9 EE F2
    0020 15 15 C9 01 D0 E9 EE F2 15 15 C9 01 D0 E9 EE F2
    0030 15 15 C9 01 00 00 00 00 00 00 00 00 01 00 00 00
    0040 00 00 00 00 00 00 00 00 00 00 00 00 BD 00 14 00
    0050 1F 50 E0 4F D0 20 EA 3A 69 10 A2 D8 08 00 2B 30
    0060 30 9D 19 00 2F 43 3A 5C 00 00 00 00 00 00 00 00
    0070 00 00 00 00 00 00 00 00 00 00 00 46 00 31 00 00
    0080 00 00 00 2C 39 69 A3 10 00 74 65 73 74 00 00 32
    0090 00 07 00 04 00 EF BE 2C 39 65 A3 2C 39 69 A3 26
    00A0 00 00 00 03 1E 00 00 00 00 F5 1E 00 00 00 00 00
    00B0 00 00 00 00 00 74 00 65 00 73 00 74 00 00 00 14
    00C0 00 48 00 32 00 00 00 00 00 2C 39 69 A3 20 00 61
    00D0 2E 74 78 74 00 34 00 07 00 04 00 EF BE 2C 39 69
    00E0 A3 2C 39 69 A3 26 00 00 00 2D 6E 00 00 00 00 96
    00F0 01 00 00 00 00 00 00 00 00 00 00 61 00 2E 00 74
    0100 00 78 00 74 00 00 00 14 00 00 00 3C 00 00 00 1C
    0110 00 00 00 01 00 00 00 1C 00 00 00 2D 00 00 00 00
    0120 00 00 00 3B 00 00 00 11 00 00 00 03 00 00 00 81
    0130 8A 7A 30 10 00 00 00 00 43 3A 5C 74 65 73 74 5C
    0140 61 2E 74 78 74 00 00 07 00 2E 00 5C 00 61 00 2E
    0150 00 74 00 78 00 74 00 07 00 43 00 3A 00 5C 00 74
    0160 00 65 00 73 00 74 00 60 00 00 00 03 00 00 A0 58
    0170 00 00 00 00 00 00 00 63 68 72 69 73 2D 78 70 73
    0180 00 00 00 00 00 00 00 40 78 C7 94 47 FA C7 46 B3
    0190 56 5C 2D C6 B6 D1 15 EC 46 CD 7B 22 7F DD 11 94
    01A0 99 00 13 72 16 87 4A 40 78 C7 94 47 FA C7 46 B3
    01B0 56 5C 2D C6 B6 D1 15 EC 46 CD 7B 22 7F DD 11 94
    01C0 99 00 13 72 16 87 4A 00 00 00 00
    '''
    rows = map(operator.methodcaller('strip'), hexadecimal_representation.split('\n'))
    items = [item.replace(' ', '') for offset, item in map(operator.methodcaller('split', ' ', 1), filter(None, rows))]
    data = bytes().join(map(operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex, items))

    # HeaderSize: (4 bytes, offset 0x0000), 0x0000004C as required.
    # LinkCLSID: (16 bytes, offset 0x0004), 00021401-0000-0000-C000-000000000046.
    # LinkFlags: (4 bytes, offset 0x0014), 0x0008009B means the following LinkFlags (section 2.1.1) are set:
    #     HasLinkTargetIDList
    #     HasLinkInfo
    #     HasRelativePath
    #     HasWorkingDir
    #     IsUnicode
    #     EnableTargetMetadata
    # FileAttributes: (4 bytes, offset 0x0018), 0x00000020, means the following FileAttributesFlags (section 2.1.2) are set:
    #     FILE_ATTRIBUTE_ARCHIVE
    # CreationTime: (8 bytes, offset 0x001C) FILETIME 9/12/08, 8:27:17PM.
    # AccessTime: (8 bytes, offset 0x0024) FILETIME 9/12/08, 8:27:17PM.
    # WriteTime: (8 bytes, offset 0x002C) FILETIME 9/12/08, 8:27:17PM.
    # FileSize: (4 bytes, offset 0x0034), 0x00000000.
    # IconIndex: (4 bytes, offset 0x0038), 0x00000000.
    # ShowCommand: (4 bytes, offset 0x003C), SW_SHOWNORMAL(1).
    # Hotkey: (2 bytes, offset 0x0040), 0x0000.
    # Reserved: (2 bytes, offset 0x0042), 0x0000.
    # Reserved2: (4 bytes, offset 0x0044), 0 x00000000.
    # Reserved3: (4 bytes, offset 0x0048), 0 x00000000.
    # Because HasLinkTargetIDList is set, a LinkTargetIDList structure (section 2.2) follows:
    #     IDListSize: (2 bytes, offset 0x004C), 0x00BD, the size of IDList.
    #     IDList: (189 bytes, offset 0x004E) an IDList structure (section 2.2.1) follows:
    #         ItemIDList: (187 bytes, offset 0x004E), ItemID structures (section 2.2.2) follow:
    #             ItemIDSize: (2 bytes, offset 0x004E), 0x0014
    #             Data: (12 bytes, offset 0x0050), <18 bytes of data> [computer]
    #             ItemIDSize: (2 bytes, offset 0x0062), 0x0019
    #             Data: (23 bytes, offset 0x0064), <23 bytes of data> [c:]
    #             ItemIDSize: (2 bytes, offset 0x007B), 0x0046
    #             Data: (68 bytes, offset 0x007D), <68 bytes of data> [test]
    #             ItemIDSize: (2 bytes, offset 0x00C1), 0x0048
    #             Data: (68 bytes, offset 0x00C3), <70 bytes of data> [a.txt]
    #         TerminalID: (2 bytes, offset 0x0109), 0x0000 indicates the end of the IDList.
    # Because HasLinkInfo is set, a LinkInfo structure (section 2.3) follows:
    #     LinkInfoSize: (4 bytes, offset 0x010B), 0x0000003C
    #     LinkInfoHeaderSize: (4 bytes, offset 0x010F), 0x0000001C as specified in the LinkInfo structure definition.
    #     LinkInfoFlags: (4 bytes, offset 0x0113), 0x00000001 VolumeIDAndLocalBasePath is set.
    #     VolumeIDOffset: (4 bytes, offset 0x0117), 0x0000001C, references offset 0x0127.
    #     LocalBasePathOffset: (4 bytes, offset 0x011B), 0x0000002D, references the character string "C:\test\a.txt".
    #     CommonNetworkRelativeLinkOffset: (4 bytes, offset 0x011F), 0x00000000 indicates CommonNetworkRelativeLink is not present.
    #     CommonPathSuffixOffset: (4 bytes, offset 0x0123), 0x0000003B, references offset 0x00000146, the character string "" (empty string).
    #     VolumeID: (17 bytes, offset 0x0127), because VolumeIDAndLocalBasePath is set, a VolumeID structure (section 2.3.1) follows:
    #         VolumeIDSize: (4 bytes, offset 0x0127), 0x00000011 indicates the size of the VolumeID structure.
    #         DriveType: (4 bytes, offset 0x012B), DRIVE_FIXED(3).
    #         DriveSerialNumber: (4 bytes, offset 0x012F), 0x307A8A81.
    #         VolumeLabelOffset: (4 bytes, offset 0x0133), 0x00000010, indicates that Volume Label Offset Unicode is not specified and references offset 0x0137 where the Volume Label is stored.
    #         Data: (1 byte, offset 0x0137), "" an empty character string.
    #     LocalBasePath: (14 bytes, offset 0x0138), because VolumeIDAndLocalBasePath is set, the character string "c:\test\a.txt" is present.
    #     CommonPathSuffix: (1 byte, offset 0x0146), "" an empty character string.
    # Because HasRelativePath is set, the RELATIVE_PATH StringData structure (section 2.4) follows:
    #     CountCharacters: (2 bytes, offset 0x0147), 0x0007 Unicode characters.
    #     String (14 bytes, offset 0x0149), the Unicode string: ".\a.txt".
    # Because HasWorkingDir is set, the WORKING_DIR StringData structure (section 2.4) follows:
    #     CountCharacters: (2 bytes, offset 0x0157), 0x0007 Unicode characters.
    #     String (14 bytes, offset 0x0159), the Unicode string: "c:\test".
    # Extra data section: (100 bytes, offset 0x0167), an ExtraData structure (section 2.5) follows:
    #     ExtraDataBlock (96 bytes, offset 0x0167), the TrackerDataBlock structure (section 2.5.10) follows:
    #         BlockSize: (4 bytes, offset 0x0167), 0x00000060
    #         BlockSignature: (4 bytes, offset 0x016B), 0xA000003, which identifies the TrackerDataBlock structure (section 2.5.10).
    #         Length: (4 bytes, offset 0x016F), 0x00000058, the required minimum size of this extra data block.
    #         Version: (4 bytes, offset 0x0173), 0x00000000, the required version.
    #         MachineID: (16 bytes, offset 0x0177), the character string "chris-xps", with zero fill.
    #         Droid: (32 bytes, offset 0x0187), 2 GUID values.
    #         DroidBirth: (32 bytes, offset 0x01A7), 2 GUID values.
    #     TerminalBlock: (4 bytes, offset 0x01C7), 0x00000000 indicates the end of the extra data section.

    import ptypes, lnkfile
    from lnkfile import *
    #importlib.reload(lnkfile)

    source = ptypes.setsource(ptypes.prov.bytes(data))

    z = File()
    z = z.l
    print(z)
