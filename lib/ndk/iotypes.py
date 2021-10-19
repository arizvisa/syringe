import logging

import ptypes
from ptypes import *

from . import exception, umtypes, ketypes
from .datatypes import *

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
    class FILE_(pbinary.enum):
        length, _values_ = 2, [
            ('ANY_ACCESS', 0),
            ('READ_ACCESS', 1),
            ('WRITE_ACCESS', 2),
            ('READWRITE_ACCESS', 3),
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
        (FILE_, 'Access'),
        (12, 'Function'),
        (METHOD_, 'Method'),
    ]
