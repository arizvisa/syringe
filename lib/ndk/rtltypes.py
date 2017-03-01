import umtypes
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
        (P(ULONG), 'Buffer'),
    ]

class _RTL_DRIVE_LETTER_CURDIR(pstruct.type):
    _fields_ = [
        (WORD, 'Flags'),
        (WORD, 'Length'),
        (ULONG, 'TimeStamp'),
        (umtypes.STRING, 'DosPath'),
    ]

class _RTL_USER_PROCESS_PARAMETERS(pstruct.type):
    class CURDIR(pstruct.type):
        _fields_ = [(umtypes.UNICODE_STRING,'DosPath'), (HANDLE,'Handle')]
        def summary(self):
            return 'Handle={:x} DosPath={!r}'.format(self['Handle'].int(), self['DosPath'].str())

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
        (umtypes.UNICODE_STRING, 'DllPath'),
        (umtypes.UNICODE_STRING, 'ImagePathName'),
        (umtypes.UNICODE_STRING, 'CommandLine'),
#        (P(lambda s: dyn.block(s.getparent(_RTL_USER_PROCESS_PARAMETERS)['EnvironmentSize'].int())), 'Environment'),
#        (P(lambda s: dyn.lazyblockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.int())), 'Environment'),
        (P(lambda s: dyn.blockarray(pstr.szwstring, s.getparent()['EnvironmentSize'].li.int())), 'Environment'),
        (ULONG, 'StartingX'),
        (ULONG, 'StartingY'),
        (ULONG, 'CountX'),
        (ULONG, 'CountY'),
        (ULONG, 'CountCharsX'),
        (ULONG, 'CountCharsY'),
        (ULONG, 'FillAttribute'),
        (ULONG, 'WindowFlags'),
        (ULONG, 'ShowWindowFlags'),
        (umtypes.UNICODE_STRING, 'WindowTitle'),
        (umtypes.UNICODE_STRING, 'DesktopInfo'),
        (umtypes.UNICODE_STRING, 'ShellInfo'),
        (umtypes.UNICODE_STRING, 'RuntimeData'),

        (dyn.array(_RTL_DRIVE_LETTER_CURDIR,32), 'CurrentDirectories'),
        (ULONG, 'EnvironmentSize'),
    ]

class _RLT_PATH_TYPE(pint.enum):
    _values_ = [
        ('RtlPathTypeUnknown', 0),
        ('RtlPathTypeUncAbsolute', 1),
        ('RtlPathTypeDriveAbsolute', 2),
        ('RtlPathTypeDriveRelative', 3),
        ('RtlPathTypeRooted', 4),
        ('RtlPathTypeRelative', 5),
        ('RtlPathTypeLocalDevice', 6),
        ('RtlPathTypeRootLocalDevice', 7),
    ]

class _RTL_RELATIVE_NAME(pstruct.type):
    _fields_ = [
        (umtypes.UNICODE_STRING, 'RelativeName'),
        (HANDLE, 'ContainingDirectory'),
        (PVOID, 'CurDirRef'),
    ]

