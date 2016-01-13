from WinNT import *

class _RTL_CRITICAL_SECTION(pstruct.type):
    _fields_ = [
        (PVOID, 'DebugInfo'),
        (LONG, 'LockCount'),
        (LONG, 'RecursionCount'),
        (PVOID, 'OwningThread'),
        (PVOID, 'LockSemaphore'),
        (ULONG, 'SpinCount'),
    ]

class _RTL_BITMAP(pstruct.type):
    _fields_ = [
        (ULONG, 'SizeOfBitMap'),
        (dyn.pointer(ULONG), 'Buffer'),
    ]

