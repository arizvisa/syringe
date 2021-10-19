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
