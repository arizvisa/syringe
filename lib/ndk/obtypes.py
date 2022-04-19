import ptypes
from ptypes import *

from . import Ntddk, umtypes, setypes
from .datatypes import *

### ntdll.dll!ZwQueryObject
#ntdll_ZwQueryObject = __stdcall(NTSTATUS, (HANDLE, 'Handle'), (DWORD, 'ObjectInformationClass'), (PVOID, 'ObjectInformation'), (ULONG, 'ObjectInformationLength'), (PULONG, 'ReturnLength'))

pint.setbyteorder(ptypes.config.byteorder.littleendian)

class OBJECT_INFORMATION_CLASS(pint.enum, pint.uint32_t):
    _values_ = [
        ('ObjectBasicInformation', 0),
        ('ObjectNameInformation', 1),
        ('ObjectTypeInformation', 2),
        ('ObjectAllInformation', 3),
        ('ObjectDataInformation', 4),
    ]

class PUBLIC_OBJECT_TYPE_INFORMATION(pstruct.type):
    _fields_ = [
        (umtypes.UNICODE_STRING, 'TypeName'),
        (dyn.array(ULONG, MAX_PATH), 'Reserved'),
    ]

class TYPE_KERNEL_OBJECT_(pint.enum, pint.uint32_t):
    _values_ = [
        ('UNKNOWN', 0),
        ('TYPE', 1),                     # "Type"
        ('DIRECTORY', 2),                # "Directory"
        ('SYMBOLICLINK', 3),             # "SymbolicLink"
        ('TOKEN', 4),                    # "Token"
        ('PROCESS', 5),                  # "Process"
        ('THREAD', 6),                   # "Thread"
        ('JOB', 7),                      # "Job"
        ('DEBUGOBJECT', 8),              # "DebugObject"
        ('EVENT', 9),                    # "Event"
        ('EVENTPAIR', 10),               # "EventPair"
        ('MUTANT', 11),                  # "Mutant"
        ('CALLBACK', 12),                # "Callback"
        ('SEMAPHORE', 13),               # "Semaphore"
        ('TIMER', 14),                   # "Timer"
        ('PROFILE', 15),                 # "Profile"
        ('KEYEDEVENT', 16),              # "KeyedEvent"
        ('WINDOWSTATION', 17),           # "WindowStation"
        ('DESKTOP', 18),                 # "Desktop"
        ('SECTION', 19),                 # "Section"
        ('KEY', 20),                     # "Key"
        ('PORT', 21),                    # "Port"
        ('WAITABLEPORT', 22),            # "WaitablePort"
        ('ADAPTER', 23),                 # "Adapter"
        ('CONTROLLER', 24),              # "Controller"
        ('DEVICE', 25),                  # "Device"
        ('DRIVER', 26),                  # "Driver"
        ('IOCOMPLETION', 27),            # "IoCompletion"
        ('FILE', 28),                    # "File"
        ('WMIGUID', 29),                 # "WmiGuid"
        ('FILTERCONNECTIONPORT', 30),    # "FilterConnectionPort"
        ('FILTERCOMMUNICATIONPORT', 31), # "FilterCommunicationPort"
        ('OTHER', 32),
    ]

class OBJECT_TYPE_LIST(pstruct.type):
    _fields_ = [
        (WORD, 'Level'),
        (setypes.ACCESS_MASK, 'Remaining'),
        (P(GUID), 'ObjectType'),
    ]

class OBJECT_TYPE_CODE(pint.enum):
    _values_ = [
        ('Adapter', 0),
        ('ALPC Port', 1),
        ('Callback', 2),
        ('Controller', 3),
        ('Device', 4),
        ('Driver', 5),
        ('Event', 6),
        ('File', 7),
        ('FilterCommunicationPort', 8),
        ('IoCompletion', 9),
        ('IoCompletionReserve', 10),
        ('IRTimer', 11),
        ('KeyedEvent', 12),
        ('Mutant', 13),
        ('PcwObject', 14),
        ('PowerRequest', 15),
        ('Profile', 16),
        ('Section', 17),
        ('Semaphore', 18),
        ('SymbolicLink', 19),
        ('Timer', 20),
        ('TpWorkerFactory', 21),
        ('Type', 22),
        ('UserApcReserve', 23),
        ('WaitCompletionPacket', 24),
    ]

class OBJECT_TYPE_INITIALIZER(pstruct.type):
    class _ObjectTypeFlags(pbinary.flags):
        _fields_ = [
            (1, 'CaseInsensitive'),
            (1, 'UnnamedObjectsOnly'),
            (1, 'UseDefaultObject'),
            (1, 'SecurityRequired'),
            (1, 'MaintainHandleCount'),
            (1, 'MaintainTypeList'),
            (1, 'SupportObjectCallbacks'),
            (1, 'CacheAligned'),
        ]
    class _ObjectTypeCode(OBJECT_TYPE_CODE, ULONG): pass

    _fields_ = [
        (USHORT, 'Length'),
        (_ObjectTypeFlags, 'ObjecTypeFlags'),
        (_ObjectTypeCode, 'ObjectTypeCode'),
        (ULONG, 'InvalidAttributes'),
    ]

class POB_PRE_OPERATION_CALLBACK(PVOID): pass
class POB_POST_OPERATION_CALLBACK(PVOID): pass
class OB_OPERATION(pint.enum, ULONG):
    _values_ = [('HANDLE_CREATE', 1), ('HANDLE_DUPLICATE', 2)]

class OBJECT_TYPE(pstruct.type): pass

class OBJECT_HEADER_QUOTA(pstruct.type):
    # from https://github.com/Exploitables/ExFreePool-Vulnerability/blob/main/ExFreePoolVulnExpl/exploit.h
    _fields_ = [
	    (ULONG, 'PagedPoolCharge'),
	    (ULONG, 'NonPagedPoolCharge'),
	    (ULONG, 'SecurityDescriptorCharge'),
	    (ULONG, 'Reserved1'),
	    (ULONGLONG, 'SecurityDescriptorQuotaBlock'),
	    (ULONG, 'Reserved2'),
    ]

class OBJECT_HEADER(pstruct.type, versioned):
    # from https://github.com/Exploitables/ExFreePool-Vulnerability/blob/main/ExFreePoolVulnExpl/exploit.h
    class u_0(dynamic.union):
        class s_0(pstruct.type):
            _fields_ = [
                (LONG_PTR, 'PointerCount'),
                (LONG_PTR, 'HandleCount'),
            ]
        _fields_ = [
            (s_0, 's_0'),
            (LIST_ENTRY, 'Entry'),
        ]
    class u1_2K(dynamic.union):
        _fields_ = [
            (LONG_PTR, 'HandleCount'),
            (P(SINGLE_LIST_ENTRY), 'SEntry'),
        ]
    class u1_XP(dynamic.union):
        _fields_ = [
            (LONG_PTR, 'HandleCount'),
            (PVOID, 'NextToFree'),
        ]
    class _TraceFlags(pbinary.flags):
        _fields_ = [
            (1, 'DbgRefTrace'),
            (1, 'DbgTracePermanent'),
            (6, 'Reserved'),
        ]
    class _InfoMask(pbinary.flags):
        _fields_ = [
            (1, 'Reserved'),
            (1, 'OBJECT_HEADER_HANDLE_REVOCATION_INFO'),
            (1, 'OBJECT_HEADER_AUDIT_INFO'),
            (1, 'OBJECT_HEADER_PROCESS_INFO'),
            (1, 'OBJECT_HEADER_QUOTA_INFO'),
            (1, 'OBJECT_HEADER_HANDLE_INFO'),
            (1, 'OBJECT_HEADER_NAME_INFO'),
            (1, 'OBJECT_HEADER_CREATOR_INFO'),
        ]
    class _Flags(pbinary.flags):
        _fields_ = [item for item in reversed([
		    (1, 'NewObject'),
		    (1, 'KernelObject'),
		    (1, 'KernelOnlyAccess'),
		    (1, 'ExclusiveObject'),
		    (1, 'PermanentObject'),
		    (1, 'DefaultSecurityQuota'),
		    (1, 'SingleHandleEntry'),
		    (1, 'DeletedInline'),
        ])]
    #class u_4(dynamic.union):
    #    _fields_ = [
    #        (P(OBJECT_CREATE_INFORMATION), 'ObjectCreateInfo'),
    #        (PVOID, 'QuotaBlockCharged'),
    #    ]
    def __init__(self, **attrs):
        super(OBJECT_HEADER, self).__init__(**attrs)
        self._fields_ = F = []

        # all of the random variations...because geoff is fucking crazy...but more like crazy awesome.
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN2K:
            F.append((self.u_0, 'u_0'))
        else:
            F.append((LONG_PTR, 'PointerCount'))
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WINXP:
            F.append((self.u1_2K, 'u_1'))
        else:
            F.append((self.u1_XP, 'u_1'))
        if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN7:
            F.append((P(OBJECT_TYPE), 'Type'))
        else:
            F.append((umtypes.EX_PUSH_LOCK, 'Lock'))

        # >= NTDDI_WIN7
        F.extend([
            (UCHAR, 'TypeIndex'),
            (self._TraceFlags, 'TraceFlags'),
            (self._InfoMask, 'InfoMask'),
            (self._Flags, 'Flags'),
            (ULONG if getattr(self, 'WIN64', False) else ptype.undefined, 'Reserved'),
            (PVOID, 'QuotaBlockChanged'),   # FIXME this is u_4, but might not be necessary
            (PVOID, 'SecurityDescriptor'),
            (QUAD, 'Body'),
        ])

class OB_OPERATION_REGISTRATION(pstruct.type): pass
class CALLBACK_ENTRY_ITEM(pstruct.type): pass
class CALLBACK_ENTRY(pstruct.type): pass

OBJECT_TYPE._fields_ = [
        (dyn.clone(LIST_ENTRY, _object_=OBJECT_TYPE), 'TypeList'),
        (umtypes.UNICODE_STRING, 'Name'),
        (PVOID, 'DefaultObject'),
        (UCHAR, 'Index'),
        (dyn.padding(4), 'padding(Index)'),
        (ULONG, 'TotalNumberOfObjects'),
        (ULONG, 'TotalNumberOfHandles'),
        (ULONG, 'HighWaterNumberOfObjects'),
        (ULONG, 'HighWaterNumberOfHandles'),
        (lambda self: dyn.padding(8 if getattr(self, 'WIN64', False) else 4), 'align(TypeInfo)'),
        (OBJECT_TYPE_INITIALIZER, 'TypeInfo'),
        (umtypes.EX_PUSH_LOCK, 'TypeLock'),
        (ULONG, 'Key'),
        (lambda self: dyn.padding(8 if getattr(self, 'WIN64', False) else 4), 'padding(Key)'),
        (dyn.clone(LIST_ENTRY, _object_=CALLBACK_ENTRY_ITEM), 'CallbackList'),
    ]

OB_OPERATION_REGISTRATION._fields_ = [
    (P(OBJECT_TYPE), 'ObjectType'),
    (OB_OPERATION, 'Operations'),
    (POB_PRE_OPERATION_CALLBACK, 'PreOperation'),
    (POB_POST_OPERATION_CALLBACK, 'PostOperation'),
]

CALLBACK_ENTRY_ITEM._fields_ = [
        (dyn.clone(LIST_ENTRY, _object_=CALLBACK_ENTRY_ITEM), 'EntryItemList'),
        (OB_OPERATION, 'Operations'),
        (P(CALLBACK_ENTRY), 'CallbackEntry'),
        (P(OBJECT_TYPE), 'ObjectType'),
        (POB_PRE_OPERATION_CALLBACK, 'PreOperation'),
        (POB_POST_OPERATION_CALLBACK, 'PostOperation'),
        (ULONGLONG, 'unk'),
    ]

CALLBACK_ENTRY._fields_ = [
        (USHORT, 'Version'),
        (dyn.block(6), 'buffer1'),
        (P(OB_OPERATION_REGISTRATION), 'RegistrationContext'),
        (USHORT, 'AltitudeLength1'),
        (USHORT, 'AltitudeLength2'),
        (dyn.block(4), 'buffer2'),
        (P(pstr.wstring), 'AltitudeString'),
        (CALLBACK_ENTRY_ITEM, 'Items'),
    ]

@pbinary.littleendian
class OBJ_(pbinary.flags):
    _fields_ = [
        (20, 'INVALID_ATTRIBUTES'),
        (1, 'IGNORE_IMPERSONATED_DEVICEMAP'),
        (1, 'FORCE_ACCESS_CHECK'),
        (1, 'KERNEL_HANDLE'),
        (1, 'OPENLINK'),
        (1, 'OPENIF'),
        (1, 'CASE_INSENSITIVE'),
        (1, 'EXCLUSIVE'),
        (1, 'PERMANENT'),
        (2, 'reserved'),
        (1, 'INHERIT'),
        (1, 'unused'),
    ]

class OBJECT_ATTRIBUTES(pstruct.type):
    _fields_ = [
        (ULONG, 'Length'),
        (ULONG64, 'RootDirectory'),
        (ULONG64, 'ObjectName'),
        (OBJ_, 'Attributes'),
        (ULONG64, 'SecurityDescriptor'),
        (ULONG64, 'SecurityQualityOfService'),
    ]

if __name__ == '__main__':
    pass
