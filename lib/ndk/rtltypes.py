from WinNT import *
from umtypes import *

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

class _RTL_DRIVE_LETTER_CURDIR(pstruct.type):
    _fields_ = [
        (WORD, 'Flags'),
        (WORD, 'Length'),
        (ULONG, 'TimeStamp'),
        (STRING, 'DosPath'),
    ]

class _RTL_USER_PROCESS_PARAMETERS(pstruct.type):
    class CURDIR(pstruct.type):
        _fields_ = [(UNICODE_STRING,'DosPath'), (HANDLE,'Handle')]
        def summary(self):
            return 'Handle={:x} DosPath={!r}'.format(self['Handle'].num(), self['DosPath'].str())

    _fields_ = [
        (ULONG, 'MaximumLength'),
        (ULONG, 'Length'),
        (ULONG, 'Flags'),
        (ULONG, 'DebugFlags'),
        (PVOID, 'ConsoleHandle'),
        (ULONG, 'ConsoleFlags'),
        (PVOID, 'StandardInput'),
        (PVOID, 'StandardOutput'),
        (PVOID, 'StandardError'),
        (CURDIR, 'CurrentDirectory'),
        (UNICODE_STRING, 'DllPath'),
        (UNICODE_STRING, 'ImagePathName'),
        (UNICODE_STRING, 'CommandLine'),
#        (dyn.pointer(lambda s: dyn.block(s.getparent(_RTL_USER_PROCESS_PARAMETERS)['EnvironmentSize'].num())), 'Environment'),
#        (dyn.pointer(lambda s: dyn.lazyblockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.num())), 'Environment'),
        (dyn.pointer(lambda s: dyn.blockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.num())), 'Environment'),
        (ULONG, 'StartingX'),
        (ULONG, 'StartingY'),
        (ULONG, 'CountX'),
        (ULONG, 'CountY'),
        (ULONG, 'CountCharsX'),
        (ULONG, 'CountCharsY'),
        (ULONG, 'FillAttribute'),
        (ULONG, 'WindowFlags'),
        (ULONG, 'ShowWindowFlags'),
        (UNICODE_STRING, 'WindowTitle'),
        (UNICODE_STRING, 'DesktopInfo'),
        (UNICODE_STRING, 'ShellInfo'),
        (UNICODE_STRING, 'RuntimeData'),

        (dyn.array(_RTL_DRIVE_LETTER_CURDIR,32), 'CurrentDirectories'),
        (ULONG, 'EnvironmentSize'),
    ]
