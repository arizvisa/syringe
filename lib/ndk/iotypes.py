import functools, operator, itertools

import ptypes
from ptypes import *

from . import exception, umtypes, ketypes
from .datatypes import *

class FILE_INFORMATION_CLASS(pint.enum):
    # XXX: would be cool to use a ptype.definition to associate the correct types for
    #      https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_file_information_class'''
    _values_ = [
        ('FileDirectoryInformation', 1),
        ('FileFullDirectoryInformation', 2),
        ('FileBothDirectoryInformation', 3),
        ('FileBasicInformation', 4),
        ('FileStandardInformation', 5),
        ('FileInternalInformation', 6),
        ('FileEaInformation', 7),
        ('FileAccessInformation', 8),
        ('FileNameInformation', 9),
        ('FileRenameInformation', 10),
        ('FileLinkInformation', 11),
        ('FileNamesInformation', 12),
        ('FileDispositionInformation', 13),
        ('FilePositionInformation', 14),
        ('FileFullEaInformation', 15),
        ('FileModeInformation', 16),
        ('FileAlignmentInformation', 17),
        ('FileAllInformation', 18),
        ('FileAllocationInformation', 19),
        ('FileEndOfFileInformation', 20),
        ('FileAlternateNameInformation', 21),
        ('FileStreamInformation', 22),
        ('FilePipeInformation', 23),
        ('FilePipeLocalInformation', 24),
        ('FilePipeRemoteInformation', 25),
        ('FileMailslotQueryInformation', 26),
        ('FileMailslotSetInformation', 27),
        ('FileCompressionInformation', 28),
        ('FileObjectIdInformation', 29),
        ('FileCompletionInformation', 30),
        ('FileMoveClusterInformation', 31),
        ('FileQuotaInformation', 32),
        ('FileReparsePointInformation', 33),
        ('FileNetworkOpenInformation', 34),
        ('FileAttributeTagInformation', 35),
        ('FileTrackingInformation', 36),
        ('FileIdBothDirectoryInformation', 37),
        ('FileIdFullDirectoryInformation', 38),
        ('FileValidDataLengthInformation', 39),
        ('FileShortNameInformation', 40),
        ('FileIoCompletionNotificationInformation', 41),
        ('FileIoStatusBlockRangeInformation', 42),
        ('FileIoPriorityHintInformation', 43),
        ('FileSfioReserveInformation', 44),
        ('FileSfioVolumeInformation', 45),
        ('FileHardLinkInformation', 46),
        ('FileProcessIdsUsingFileInformation', 47),
        ('FileNormalizedNameInformation', 48),
        ('FileNetworkPhysicalNameInformation', 49),
        ('FileIdGlobalTxDirectoryInformation', 50),
        ('FileIsRemoteDeviceInformation', 51),
        ('FileUnusedInformation', 52),
        ('FileNumaNodeInformation', 53),
        ('FileStandardLinkInformation', 54),
        ('FileRemoteProtocolInformation', 55),
        ('FileRenameInformationBypassAccessCheck', 56),
        ('FileLinkInformationBypassAccessCheck', 57),
        ('FileVolumeNameInformation', 58),
        ('FileIdInformation', 59),
        ('FileIdExtdDirectoryInformation', 60),
        ('FileReplaceCompletionInformation', 61),
        ('FileHardLinkFullIdInformation', 62),
        ('FileIdExtdBothDirectoryInformation', 63),
        ('FileDispositionInformationEx', 64),
        ('FileRenameInformationEx', 65),
        ('FileRenameInformationExBypassAccessCheck', 66),
        ('FileDesiredStorageClassInformation', 67),
        ('FileStatInformation', 68),
        ('FileMemoryPartitionInformation', 69),
        ('FileStatLxInformation', 70),
        ('FileCaseSensitiveInformation', 71),
        ('FileLinkInformationEx', 72),
        ('FileLinkInformationExBypassAccessCheck', 73),
        ('FileStorageReserveIdInformation', 74),
        ('FileCaseSensitiveInformationForceAccessCheck', 75),
        ('FileCaseSensitiveInformationForceAccessCheck', 75),
        ('FileKnownFolderInformation', 76),
    ]

class VPB(pstruct.type):
    MAXIMUM_VOLUME_LABEL_LENGTH = 32
    _fields_ = [
        (CSHORT, 'Type'),
        (CSHORT, 'Size'),
        (USHORT, 'Flags'),
        (USHORT, 'VolumeLabelLength'),
        #(P(DEVICE_OBJECT), 'DeviceObject'),
        (PVOID, 'DeviceObject'),
        #(P(DEVICE_OBJECT), 'RealDevice'),
        (PVOID, 'RealDevice'),
        (ULONG, 'SerialNumber'),
        (ULONG, 'ReferenceCount'),
        (dyn.array(WCHAR, MAXIMUM_VOLUME_LABEL_LENGTH), 'VolumeLabel'),
    ]

class SECTION_OBJECT_POINTERS(pstruct.type):
    _fields_ = [
        (PVOID, 'DataSectionObject'),
        (PVOID, 'SharedCacheMap'),
        (PVOID, 'ImageSectionObject'),
    ]

class FILE_OBJECT(pstruct.type):
    _fields_ = [
        (CSHORT, 'Type'),
        (CSHORT, 'Size'),
        #(P(DEVICE_OBJECT), 'DeviceObject'),
        (PVOID, 'DeviceObject'),
        (P(VPB), 'Vpb'),
        (PVOID, 'FsContext'),
        (PVOID, 'FsContext2'),
        (P(SECTION_OBJECT_POINTERS), 'SectionObjectPointer'),
        (PVOID, 'PrivateCacheMap'),
        (NTSTATUS, 'FinalStatus'),
        (lambda self: P(FILE_OBJECT), 'RelatedFileObject'),
        (BOOLEAN, 'LockOperation'),
        (BOOLEAN, 'DeletePending'),
        (BOOLEAN, 'ReadAccess'),
        (BOOLEAN, 'WriteAccess'),
        (BOOLEAN, 'DeleteAccess'),
        (BOOLEAN, 'SharedRead'),
        (BOOLEAN, 'SharedWrite'),
        (BOOLEAN, 'SharedDelete'),
        (ULONG, 'Flags'),
        (umtypes.UNICODE_STRING, 'FileName'),
        (LARGE_INTEGER, 'CurrentByteOffset'),
        (ULONG, 'Waiters'),
        (ULONG, 'Busy'),
        (PVOID, 'LastLock'),
        (ketypes.KEVENT, 'Lock'),
        (ketypes.KEVENT, 'Event'),
        #(P(IO_COMPLETION_CONTEXT), 'CompletionContext'),
        (PVOID, 'CompletionContext'),
        (ketypes.KSPIN_LOCK, 'IrpListLock'),
        (LIST_ENTRY, 'IrpList'),
        (PVOID, 'FileObjectExtension'),
    ]

class IO_STATUS_BLOCK(pstruct.type):
    _fields_ = [
        (PVOID, 'Pointer'),
        (ULONG_PTR, 'Information'),
    ]

class SYSTEM_HANDLE_INFORMATION(pstruct.type):
    def __GrantedAccess(self):
        import setypes
        return setypes.ACCESS_MASK
    _fields_ = [
        (USHORT, 'ProcessId'),
        (USHORT, 'CreatorBackTraceIndex'),
        (UCHAR, 'ObjectTypeNumber'),
        (UCHAR, 'Flags'),
        (USHORT, 'Handle'),
        (PVOID, 'Object'),
        (__GrantedAccess, 'GrantedAccess'),
    ]

class SYSTEM_HANDLE_INFORMATION_EX(pstruct.type):
    _fields_ = [
        (ULONG, 'NumberOfHandles'),
        (lambda self: dyn.array(SYSTEM_HANDLE_INFORMATION, self['NumberOfHandles'].li.int()), 'Information'),
    ]

@pbinary.littleendian
class CTL_CODE(pbinary.struct):
    class FILE_DEVICE_(pbinary.enum):
        length, _values_ = 16, [
            ('BEEP',                          0x00000001),
            ('CD_ROM',                        0x00000002),
            ('CD_ROM_FILE_SYSTEM',            0x00000003),
            ('CONTROLLER',                    0x00000004),
            ('DATALINK',                      0x00000005),
            ('DFS',                           0x00000006),
            ('DISK',                          0x00000007),
            ('DISK_FILE_SYSTEM',              0x00000008),
            ('FILE_SYSTEM',                   0x00000009),
            ('INPORT_PORT',                   0x0000000a),
            ('KEYBOARD',                      0x0000000b),
            ('MAILSLOT',                      0x0000000c),
            ('MIDI_IN',                       0x0000000d),
            ('MIDI_OUT',                      0x0000000e),
            ('MOUSE',                         0x0000000f),
            ('MULTI_UNC_PROVIDER',            0x00000010),
            ('NAMED_PIPE',                    0x00000011),
            ('NETWORK',                       0x00000012),
            ('NETWORK_BROWSER',               0x00000013),
            ('NETWORK_FILE_SYSTEM',           0x00000014),
            ('NULL',                          0x00000015),
            ('PARALLEL_PORT',                 0x00000016),
            ('PHYSICAL_NETCARD',              0x00000017),
            ('PRINTER',                       0x00000018),
            ('SCANNER',                       0x00000019),
            ('SERIAL_MOUSE_PORT',             0x0000001a),
            ('SERIAL_PORT',                   0x0000001b),
            ('SCREEN',                        0x0000001c),
            ('SOUND',                         0x0000001d),
            ('STREAMS',                       0x0000001e),
            ('TAPE',                          0x0000001f),
            ('TAPE_FILE_SYSTEM',              0x00000020),
            ('TRANSPORT',                     0x00000021),
            ('UNKNOWN',                       0x00000022),
            ('VIDEO',                         0x00000023),
            ('VIRTUAL_DISK',                  0x00000024),
            ('WAVE_IN',                       0x00000025),
            ('WAVE_OUT',                      0x00000026),
            ('8042_PORT',                     0x00000027),
            ('NETWORK_REDIRECTOR',            0x00000028),
            ('BATTERY',                       0x00000029),
            ('BUS_EXTENDER',                  0x0000002a),
            ('MODEM',                         0x0000002b),
            ('VDM',                           0x0000002c),
            ('MASS_STORAGE',                  0x0000002d),
            ('SMB',                           0x0000002e),
            ('KS',                            0x0000002f),
            ('CHANGER',                       0x00000030),
            ('SMARTCARD',                     0x00000031),
            ('ACPI',                          0x00000032),
            ('DVD',                           0x00000033),
            ('FULLSCREEN_VIDEO',              0x00000034),
            ('DFS_FILE_SYSTEM',               0x00000035),
            ('DFS_VOLUME',                    0x00000036),
            ('SERENUM',                       0x00000037),
            ('TERMSRV',                       0x00000038),
            ('KSEC',                          0x00000039),
            ('FIPS',                          0x0000003A),
            ('INFINIBAND',                    0x0000003B),
            ('VMBUS',                         0x0000003E),
            ('CRYPT_PROVIDER',                0x0000003F),
            ('WPD',                           0x00000040),
            ('BLUETOOTH',                     0x00000041),
            ('MT_COMPOSITE',                  0x00000042),
            ('MT_TRANSPORT',                  0x00000043),
            ('BIOMETRIC',                     0x00000044),
            ('PMI',                           0x00000045),
            ('EHSTOR',                        0x00000046),
            ('DEVAPI',                        0x00000047),
            ('GPIO',                          0x00000048),
            ('USBEX',                         0x00000049),
            ('CONSOLE',                       0x00000050),
            ('NFP',                           0x00000051),
            ('SYSENV',                        0x00000052),
            ('VIRTUAL_BLOCK',                 0x00000053),
            ('POINT_OF_SERVICE',              0x00000054),
            ('STORAGE_REPLICATION',           0x00000055),
            ('TRUST_ENV',                     0x00000056),
            ('UCM',                           0x00000057),
            ('UCMTCPCI',                      0x00000058),
            ('PERSISTENT_MEMORY',             0x00000059),
            ('NVDIMM',                        0x0000005a),
            ('HOLOGRAPHIC',                   0x0000005b),
            ('SDFXHCI',                       0x0000005c),
            ('IRCLASS',                       0x00000f60),
        ]
    class FILE_ACCESS(pbinary.enum):
        length, _values_ = 2, [
            ('ANY', 0),         # FILE_ANY_ACCESS
            ('READ', 1),        # FILE_READ_ACCESS
            ('WRITE', 2),       # FILE_WRITE_ACCESS
            ('READ_WRITE', 3),  # FILE_READ_ACCESS|FILE_WRITE_ACCESS
        ]
    class METHOD_(pbinary.enum):
        length, _values_ = 2, [
            ('BUFFERED', 0),
            ('IN_DIRECT', 1),
            ('OUT_DIRECT', 2),
            ('NEITHER', 3),
        ]
    _fields_ = [
        (FILE_DEVICE_, 'DeviceType'),
        (FILE_ACCESS, 'Access'),
        (12, 'Function'),
        (METHOD_, 'Method'),
    ]

class IO_TYPE_(pint.enum):
    _values_ = [
        ('ADAPTER', 0x00000001),
        ('CONTROLLER', 0x00000002),
        ('DEVICE', 0x00000003),
        ('DRIVER', 0x00000004),
        ('FILE', 0x00000005),
        ('IRP', 0x00000006),
        ('MASTER_ADAPTER', 0x00000007),
        ('OPEN_PACKET', 0x00000008),
        ('TIMER', 0x00000009),
        ('VPB', 0x0000000a),
        ('ERROR_LOG', 0x0000000b),
        ('ERROR_MESSAGE', 0x0000000c),
        ('DEVICE_OBJECT_EXTENSION', 0x0000000d),
    ]

class IRP_MJ_(pint.enum, UCHAR):
    _values_ = [
        ('CREATE', 0x00),
        ('CREATE_NAMED_PIPE', 0x01),
        ('CLOSE', 0x02),
        ('READ', 0x03),
        ('WRITE', 0x04),
        ('QUERY_INFORMATION', 0x05),
        ('SET_INFORMATION', 0x06),
        ('QUERY_EA', 0x07),
        ('SET_EA', 0x08),
        ('FLUSH_BUFFERS', 0x09),
        ('QUERY_VOLUME_INFORMATION', 0x0a),
        ('SET_VOLUME_INFORMATION', 0x0b),
        ('DIRECTORY_CONTROL', 0x0c),
        ('FILE_SYSTEM_CONTROL', 0x0d),
        ('DEVICE_CONTROL', 0x0e),
        ('INTERNAL_DEVICE_CONTROL', 0x0f),
        ('SHUTDOWN', 0x10),
        ('LOCK_CONTROL', 0x11),
        ('CLEANUP', 0x12),
        ('CREATE_MAILSLOT', 0x13),
        ('QUERY_SECURITY', 0x14),
        ('SET_SECURITY', 0x15),
        ('POWER', 0x16),
        ('SYSTEM_CONTROL', 0x17),
        ('DEVICE_CHANGE', 0x18),
        ('QUERY_QUOTA', 0x19),
        ('SET_QUOTA', 0x1a),
        ('PNP', 0x1b),
        #('PNP_POWER', IRP_MJ_PNP),   # Obsolete....
        #('MAXIMUM_FUNCTION', 0x1b),
        #('SCSI', IRP_MJ_INTERNAL_DEVICE_CONTROL),

        # FltMgr's IRP major codes
        ('ACQUIRE_FOR_SECTION_SYNCHRONIZATION', (-1)),
        ('RELEASE_FOR_SECTION_SYNCHRONIZATION', (-2)),
        ('ACQUIRE_FOR_MOD_WRITE', (-3)),
        ('RELEASE_FOR_MOD_WRITE', (-4)),
        ('ACQUIRE_FOR_CC_FLUSH', (-5)),
        ('RELEASE_FOR_CC_FLUSH', (-6)),
        ('NOTIFY_STREAM_FO_CREATION', (-7)),

        ('FAST_IO_CHECK_IF_POSSIBLE', (-13)),
        ('NETWORK_QUERY_OPEN', (-14)),
        ('MDL_READ', (-15)),
        ('MDL_READ_COMPLETE', (-16)),
        ('PREPARE_MDL_WRITE', (-17)),
        ('MDL_WRITE_COMPLETE', (-18)),
        ('VOLUME_MOUNT', (-19)),
        ('VOLUME_DISMOUNT', (-20)),
    ]

class IRP_MN(ptype.definition):
    cache = {}
    default = UCHAR

@IRP_MN.define(type='DIRECTORY_CONTROL')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_DIRECTORY_CONTROL'''
    _values_ = [
        ('QUERY_DIRECTORY', 0x01),
        ('NOTIFY_CHANGE_DIRECTORY', 0x02),
    ]

@IRP_MN.define(type='FILE_SYSTEM_CONTROL')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_FILE_SYSTEM_CONTROL'''
    _values_ = [
        ('USER_FS_REQUEST', 0x00),
        ('MOUNT_VOLUME', 0x01),
        ('VERIFY_VOLUME', 0x02),
        ('LOAD_FILE_SYSTEM', 0x03),
        #('TRACK_LINK', 0x04),    # To be obsoleted soon
        ('KERNEL_CALL', 0x04),
    ]

@IRP_MN.define(type='LOCK_CONTROL')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_LOCK_CONTROL'''
    _values_ = [
        ('LOCK', 0x01),
        ('UNLOCK_SINGLE', 0x02),
        ('UNLOCK_ALL', 0x03),
        ('UNLOCK_ALL_BY_KEY', 0x04),
    ]

@IRP_MN.define(type='READ')
@IRP_MN.define(type='WRITE')
class IRP_MN_READWRITE(dynamic.union):
    class _flags(pbinary.flags):
        _fields_ = [
            (4, 'padding'),
            (1, 'DPC'),
            (1, 'MDL'),
            (1, 'COMPLETE'),
            (1, 'COMPRESSED'),
        ]
    class _enumeration(pint.enum, UCHAR):
        _values_ = [
            ('NORMAL', 0x00),
            ('DPC', 0x01),
            ('MDL', 0x02),
            ('COMPLETE', 0x04),
            ('COMPRESSED', 0x08),

            ('MDL_DPC', 2|1),           # (IRP_MN_MDL|IRP_MN_DPC)
            ('COMPLETE_MDL', 4|2),      # (IRP_MN_COMPLETE|IRP_MN_MDL)
            ('COMPLETE_MDL_DPC', 6|1),  # (IRP_MN_COMPLETE_MDL|IRP_MN_DPC)
        ]
    _fields_ = [
        (dyn.clone(pbinary.partial, _object_=_flags), 'flags'),
        (_enumeration, 'enum'),
    ]

class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_READ|IRP_MJ_WRITE'''
    _values_ = [
        ('NORMAL', 0x00),
        ('DPC', 0x01),
        ('MDL', 0x02),
        ('COMPLETE', 0x04),
        ('COMPRESSED', 0x08),

        ('MDL_DPC', 2|1),           # (IRP_MN_MDL|IRP_MN_DPC)
        ('COMPLETE_MDL', 4|2),      # (IRP_MN_COMPLETE|IRP_MN_MDL)
        ('COMPLETE_MDL_DPC', 6|1),  # (IRP_MN_COMPLETE_MDL|IRP_MN_DPC)
    ]

@IRP_MN.define(type='INTERNAL_DEVICE_CONTROL')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_SCSI'''
    _values_ = [
        ('SCSI_CLASS', 0x01),
    ]

@IRP_MN.define(type='PNP')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_PNP'''
    _values_ = [
        ('START_DEVICE', 0x00),
        ('QUERY_REMOVE_DEVICE', 0x01),
        ('REMOVE_DEVICE', 0x02),
        ('CANCEL_REMOVE_DEVICE', 0x03),
        ('STOP_DEVICE', 0x04),
        ('QUERY_STOP_DEVICE', 0x05),
        ('CANCEL_STOP_DEVICE', 0x06),

        ('QUERY_DEVICE_RELATIONS', 0x07),
        ('QUERY_INTERFACE', 0x08),
        ('QUERY_CAPABILITIES', 0x09),
        ('QUERY_RESOURCES', 0x0A),
        ('QUERY_RESOURCE_REQUIREMENTS', 0x0B),
        ('QUERY_DEVICE_TEXT', 0x0C),
        ('FILTER_RESOURCE_REQUIREMENTS', 0x0D),

        ('READ_CONFIG', 0x0F),
        ('WRITE_CONFIG', 0x10),
        ('EJECT', 0x11),
        ('SET_LOCK', 0x12),
        ('QUERY_ID', 0x13),
        ('QUERY_PNP_DEVICE_STATE', 0x14),
        ('QUERY_BUS_INFORMATION', 0x15),
        ('DEVICE_USAGE_NOTIFICATION', 0x16),
        ('SURPRISE_REMOVAL', 0x17),

        ('QUERY_LEGACY_BUS_INFORMATION', 0x18),

        ('IRP_MN_DEVICE_ENUMERATED', 0x19),
    ]

@IRP_MN.define(type='POWER')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_POWER'''
    _values_ = [
        ('WAIT_WAKE', 0x00),
        ('POWER_SEQUENCE', 0x01),
        ('SET_POWER', 0x02),
        ('QUERY_POWER', 0x03),
    ]

@IRP_MN.define(type='SYSTEM_CONTROL')
class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_SYSTEM_CONTROL'''
    _values_ = [
        ('QUERY_ALL_DATA', 0x00),
        ('QUERY_SINGLE_INSTANCE', 0x01),
        ('CHANGE_SINGLE_INSTANCE', 0x02),
        ('CHANGE_SINGLE_ITEM', 0x03),
        ('ENABLE_EVENTS', 0x04),
        ('DISABLE_EVENTS', 0x05),
        ('ENABLE_COLLECTION', 0x06),
        ('DISABLE_COLLECTION', 0x07),
        ('REGINFO', 0x08),
        ('EXECUTE_METHOD', 0x09),

        ('SET_TRACE_NOTIFY', 0x0A),
        ('REGINFO_EX', 0x0B),
    ]

class IRP_MN_(pint.enum, UCHAR):
    '''IRP_MJ_**'''
    _values_ = map(operator.attrgetter('_values_'), filter(lambda definition: hasattr(definition, '_values_'), map(operator.itemgetter(1), IRP_MN.cache.items())))
    _values_ = [_values_ for _values_ in sorted(_values_, key=len)]
    _values_ = [("IRP_MN_{:s}".format(key), value) for key, value in itertools.chain(*reversed(_values_))]

