import ptypes
from ptypes import *

from . import Ntddk, umtypes
from .datatypes import *

### ntdll.dll!ZwQueryObject
#ntdll_ZwQueryObject = __stdcall(NTSTATUS, (HANDLE, 'Handle'), (DWORD, 'ObjectInformationClass'), (PVOID, 'ObjectInformation'), (ULONG, 'ObjectInformationLength'), (PULONG, 'ReturnLength'))

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

if __name__ == '__main__':
    pass
