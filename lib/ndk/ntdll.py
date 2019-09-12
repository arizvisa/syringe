import ptypes
from ptypes import *

### ntdll.dll!ZwQueryObject
#ntdll_ZwQueryObject = __stdcall(NTSTATUS, (HANDLE, 'Handle'), (DWORD, 'ObjectInformationClass'), (PVOID, 'ObjectInformation'), (ULONG, 'ObjectInformationLength'), (PULONG, 'ReturnLength'))

class OBJECT_INFORMATION_CLASS(pint.enum, pint.uint32_t):
    _values_ = [
        ('ObjectNameInformation', 1),
        ('ObjectTypeInformation', 2),
    ]

class PUBLIC_OBJECT_TYPE_INFORMATION(pstruct.type):
    _fields_ = [
        (UNICODE_STRING, 'TypeName'),
        (dyn.array(ULONG, MAX_PATH), 'Reserved'),
    ]

class TYPE_KERNEL_OBJECT(pint.enum, pint.uint32_t):
    _values_ = [
        ('TYPE_KERNEL_OBJECT_UNKNOWN', 0),
        ('TYPE_KERNEL_OBJECT_TYPE', 1),                     # "Type"
        ('TYPE_KERNEL_OBJECT_DIRECTORY', 2),                # "Directory"
        ('TYPE_KERNEL_OBJECT_SYMBOLICLINK', 3),             # "SymbolicLink"
        ('TYPE_KERNEL_OBJECT_TOKEN', 4),                    # "Token"
        ('TYPE_KERNEL_OBJECT_PROCESS', 5),                  # "Process"
        ('TYPE_KERNEL_OBJECT_THREAD', 6),                   # "Thread"
        ('TYPE_KERNEL_OBJECT_JOB', 7),                      # "Job"
        ('TYPE_KERNEL_OBJECT_DEBUGOBJECT', 8),              # "DebugObject"
        ('TYPE_KERNEL_OBJECT_EVENT', 9),                    # "Event"
        ('TYPE_KERNEL_OBJECT_EVENTPAIR', 10),               # "EventPair"
        ('TYPE_KERNEL_OBJECT_MUTANT', 11),                  # "Mutant"
        ('TYPE_KERNEL_OBJECT_CALLBACK', 12),                # "Callback"
        ('TYPE_KERNEL_OBJECT_SEMAPHORE', 13),               # "Semaphore"
        ('TYPE_KERNEL_OBJECT_TIMER', 14),                   # "Timer"
        ('TYPE_KERNEL_OBJECT_PROFILE', 15),                 # "Profile"
        ('TYPE_KERNEL_OBJECT_KEYEDEVENT', 16),              # "KeyedEvent"
        ('TYPE_KERNEL_OBJECT_WINDOWSTATION', 17),           # "WindowStation"
        ('TYPE_KERNEL_OBJECT_DESKTOP', 18),                 # "Desktop"
        ('TYPE_KERNEL_OBJECT_SECTION', 19),                 # "Section"
        ('TYPE_KERNEL_OBJECT_KEY', 20),                     # "Key"
        ('TYPE_KERNEL_OBJECT_PORT', 21),                    # "Port"
        ('TYPE_KERNEL_OBJECT_WAITABLEPORT', 22),            # "WaitablePort"
        ('TYPE_KERNEL_OBJECT_ADAPTER', 23),                 # "Adapter"
        ('TYPE_KERNEL_OBJECT_CONTROLLER', 24),              # "Controller"
        ('TYPE_KERNEL_OBJECT_DEVICE', 25),                  # "Device"
        ('TYPE_KERNEL_OBJECT_DRIVER', 26),                  # "Driver"
        ('TYPE_KERNEL_OBJECT_IOCOMPLETION', 27),            # "IoCompletion"
        ('TYPE_KERNEL_OBJECT_FILE', 28),                    # "File"
        ('TYPE_KERNEL_OBJECT_WMIGUID', 29),                 # "WmiGuid"
        ('TYPE_KERNEL_OBJECT_FILTERCONNECTIONPORT', 30),    # "FilterConnectionPort"
        ('TYPE_KERNEL_OBJECT_FILTERCOMMUNICATIONPORT', 31), # "FilterCommunicationPort"
        ('TYPE_KERNEL_OBJECT_OTHER', 32),
    ]

if __name__ == '__main__':
    pass
