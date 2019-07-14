import ptypes
from ptypes import *

from .datatypes import *

class DISPATCHER_HEADER(pstruct.type):
    _fields_ = [
        (LONG, 'Lock'),
        (LONG, 'SignalState'),
        (LIST_ENTRY, 'WaitListHead'),
    ]

class _KEVENT(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
    ]

class _KSEMAPHORE(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (LONG, 'Limit'),
    ]

class _KGATE(_KEVENT): pass
