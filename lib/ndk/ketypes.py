import ptypes
from ptypes import *

from .datatypes import *

class DISPATCHER_HEADER(pstruct.type):
    _fields_ = [
        (LONG, 'Lock'),
        (LONG, 'SignalState'),
        (LIST_ENTRY, 'WaitListHead'),
    ]

class KEVENT(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
    ]

class KSEMAPHORE(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (LONG, 'Limit'),
    ]

class KGATE(KEVENT): pass

class KSPIN_LOCK(ULONG_PTR): pass

