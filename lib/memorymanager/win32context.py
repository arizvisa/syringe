# this makes ctypes friendlier (for me, anyways)

from ctypes import *
## page permissions
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_GUARD = 0x100
PAGE_NOCACHE = 0x200
PAGE_WRITECOMBINE = 0x400

## process access permissions from winnt.h
DELETE = 0x00010000L
READ_CONTROL = 0x00020000L
WRITE_DAC = 0x00040000L
WRITE_OWNER = 0x00080000L
SYNCHRONIZE = 0x00100000L

ACCESS_SYSTEM_SECURITY = 0x01000000L
MAXIMUM_ALLOWED = 0x02000000L

GENERIC_READ = 0x80000000L
GENERIC_WRITE = 0x40000000L
GENERIC_EXECUTE = 0x20000000L
GENERIC_ALL = 0x10000000L

STANDARD_RIGHTS_REQUIRED = 0x000F0000L
STANDARD_RIGHTS_READ = READ_CONTROL
STANDARD_RIGHTS_WRITE = READ_CONTROL
STANDARD_RIGHTS_EXECUTE = READ_CONTROL
STANDARD_RIGHTS_ALL = 0x001F0000L
SPECIFIC_RIGHTS_ALL = 0x0000FFFFL

PROCESS_TERMINATE = 0x0001
PROCESS_CREATE_THREAD = 0x0002
PROCESS_SET_SESSIONID = 0x0004
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_DUP_HANDLE = 0x0040
PROCESS_CREATE_PROCESS = 0x0080
PROCESS_SET_QUOTA = 0x0100
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
#PROCESS_ALL_ACCESS = STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xFFFF
PROCESS_VM_ALL = PROCESS_VM_OPERATION|PROCESS_VM_READ|PROCESS_VM_WRITE
PROCESS_INFO_ALL = PROCESS_QUERY_INFORMATION|PROCESS_SET_INFORMATION

THREAD_TERMINATE = 0x0001
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_SET_CONTEXT = 0x0010
THREAD_QUERY_INFORMATION = 0x0040
THREAD_SET_INFORMATION = 0x0020
THREAD_SET_THREAD_TOKEN = 0x0080
THREAD_IMPERSONATE = 0x0100
THREAD_DIRECT_IMPERSONATION = 0x0200
THREAD_SET_LIMITED_INFORMATION = 0x0400  # winnt
THREAD_QUERY_LIMITED_INFORMATION = 0x0800  # winnt
THREAD_ALL_ACCESS = STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xFFFF

JOB_OBJECT_ASSIGN_PROCESS = 0x0001
JOB_OBJECT_SET_ATTRIBUTES = 0x0002
JOB_OBJECT_QUERY = 0x0004
JOB_OBJECT_TERMINATE = 0x0008
JOB_OBJECT_SET_SECURITY_ATTRIBUTES = 0x0010
JOB_OBJECT_ALL_ACCESS = STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0x1F

## constants for contexts
CONTEXT_i386 = 0x00010000    # this assumes that i386 and
CONTEXT_i486 = 0x00010000    # i486 have identical context records
CONTEXT_CONTROL = (CONTEXT_i386 | 0x00000001L) # SS:SP, CS:IP, FLAGS, BP
CONTEXT_INTEGER = (CONTEXT_i386 | 0x00000002L) # AX, BX, CX, DX, SI, DI
CONTEXT_SEGMENTS = (CONTEXT_i386 | 0x00000004L)           # DS, ES, FS, GS
CONTEXT_FLOATING_POINT = (CONTEXT_i386 | 0x00000008L)     # 387 state
CONTEXT_DEBUG_REGISTERS = (CONTEXT_i386 | 0x00000010L)    # DB 0-3,6,7
CONTEXT_EXTENDED_REGISTERS = (CONTEXT_i386 | 0x00000020L) # cpu specific extensions

CONTEXT_FULL  = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS)

CONTEXT_ALL = CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS
CONTEXT_ALL |= CONTEXT_FLOATING_POINT | CONTEXT_DEBUG_REGISTERS
CONTEXT_ALL |= CONTEXT_EXTENDED_REGISTERS

## basic types
DWORD64 = c_uint64
DWORD = c_uint32
WORD = c_uint16
BYTE = c_uint8
LONG = c_long
ULONG = c_ulong
INT = c_int
UINT = c_uint
ULONGLONG = c_uint64
LONGLONG = c_int64

## complex structures
class M128A(Structure):
    _fields_ = [
        ('Low', ULONGLONG),
        ('High', LONGLONG)
    ]

class MMX(Structure):
    _fields_ = [
        ('Header', ARRAY(M128A, 2)),
        ('Legacy', ARRAY(M128A, 8)),
        ('Xmm0', M128A),
        ('Xmm1', M128A),
        ('Xmm2', M128A),
        ('Xmm3', M128A),
        ('Xmm4', M128A),
        ('Xmm5', M128A),
        ('Xmm6', M128A),
        ('Xmm7', M128A),
        ('Xmm8', M128A),
        ('Xmm9', M128A),
        ('Xmm10', M128A),
        ('Xmm11', M128A),
        ('Xmm12', M128A),
        ('Xmm13', M128A),
        ('Xmm14', M128A),
        ('Xmm15', M128A)
    ]

class XMM_SAVE_AREA32(Structure):
    _fields_ = [
        ('ControlWord', WORD),
        ('StatusWord', WORD),
        ('TagWord', BYTE),
        ('Reserved1', BYTE),
        ('ErrorOpcode', WORD),
        ('ErrorOffset', DWORD),
        ('ErrorSelector', WORD),
        ('Reserved2', WORD),
        ('DataOffset', DWORD),
        ('DataSelector', WORD),
        ('Reserved3', WORD),
        ('MxCsr', DWORD),
        ('MxCsr_Mask', DWORD),
        ('FloatRegisters', ARRAY(M128A, 8)),
        ('XmmRegisters', ARRAY(M128A, 16)),
        ('Reserved4', ARRAY(BYTE, 96))
    ]

SIZE_OF_80387_REGISTERS = 80
class FLOATING_SAVE_AREA(Structure):
    _fields_ = [
        ('ControlWord', DWORD),
        ('StatusWord', DWORD),
        ('TagWord', DWORD),
        ('ErrorOffset', DWORD),
        ('ErrorSelector', DWORD),
        ('DataOffset', DWORD),
        ('DataSelector', DWORD),
        ('RegisterArea', ARRAY(BYTE, SIZE_OF_80387_REGISTERS)),
        ('Cr0NpxState', DWORD)
    ]

MAXIMUM_SUPPORTED_EXTENSION = 512
class CONTEXT(Structure):
    _fields_ = [
        ('ContextFlags', DWORD),
        ('Dr0', DWORD),
        ('Dr1', DWORD),
        ('Dr2', DWORD),
        ('Dr3', DWORD),
        ('Dr6', DWORD),
        ('Dr7', DWORD),
        ('FloatSave', FLOATING_SAVE_AREA),
        ('SegGs', DWORD),
        ('SegFs', DWORD),
        ('SegEs', DWORD),
        ('SegDs', DWORD),
        ('Edi', DWORD),
        ('Esi', DWORD),
        ('Ebx', DWORD),
        ('Edx', DWORD),
        ('Ecx', DWORD),
        ('Eax', DWORD),
        ('Ebp', DWORD),
        ('Eip', DWORD),
        ('SegCs', DWORD),
        ('EFlags', DWORD),
        ('Esp', DWORD),
        ('SegSs', DWORD),
        ('ExtendedRegisters', ARRAY(BYTE, MAXIMUM_SUPPORTED_EXTENSION))
    ]

## other win32 stuff
HANDLE = c_voidp
class CLIENT_ID(Structure):
    _fields_ = [
        ('UniqueProcess', HANDLE),
        ('UniqueThread', HANDLE)
    ]

ThreadBasicInformation = 0  # _THREADINFOCLASS
KAFFINITY = KPRIORITY = c_ulong
PVOID = c_voidp
NTSTATUS = c_long
class THREAD_BASIC_INFORMATION(Structure):
    _fields_ = [
        ('ExitStatus', NTSTATUS),
        ('TebBaseAddress', PVOID),
        ('ClientId', CLIENT_ID),
        ('AffinityMask', KAFFINITY),
        ('Priority', KPRIORITY),
        ('BasePriority', KPRIORITY),
    ]

## token shit
class LUID(Structure):
    _fields_ = [
        ('LowPart', DWORD),
        ('HighPart', LONG)
    ]

class LUID_AND_ATTRIBUTES(Structure):
    _fields_ = [
        ('Luid', LUID),
        ('Attributes', DWORD)
    ]

class TOKEN_PRIVILEGES(Structure):
    _fields_ = [
        ('PrivilegeCount', ULONG),
        ('Privileges', LUID_AND_ATTRIBUTES*1)
    ]

SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001
SE_PRIVILEGE_ENABLED = 0x00000002
SE_PRIVILEGE_REMOVED = 0X00000004
SE_PRIVILEGE_USED_FOR_ACCESS = 0x80000000

SE_PRIVILEGE_VALID_ATTRIBUTES = (SE_PRIVILEGE_ENABLED_BY_DEFAULT | SE_PRIVILEGE_ENABLED | SE_PRIVILEGE_REMOVED | SE_PRIVILEGE_USED_FOR_ACCESS)
PRIVILEGE_SET_ALL_NECESSARY = (1)

class PRIVILEGE_SET(Structure):
    _fields_ = [
        ('PrivilegeCount', DWORD),
        ('Control', DWORD),
        ('Privilege', LUID_AND_ATTRIBUTES*1)
    ]

## token constants
TOKEN_ASSIGN_PRIMARY = 0x0001
TOKEN_DUPLICATE = 0x0002
TOKEN_IMPERSONATE = 0x0004
TOKEN_QUERY = 0x0008
TOKEN_QUERY_SOURCE = 0x0010
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_ADJUST_GROUPS = 0x0040
TOKEN_ADJUST_DEFAULT = 0x0080
TOKEN_ADJUST_SESSIONID = 0x0100

TOKEN_ALL_ACCESS_P = STANDARD_RIGHTS_REQUIRED | TOKEN_ASSIGN_PRIMARY | TOKEN_DUPLICATE | TOKEN_IMPERSONATE | TOKEN_QUERY | TOKEN_QUERY_SOURCE | TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT
TOKEN_ALL_ACCESS = TOKEN_ALL_ACCESS_P | TOKEN_ADJUST_SESSIONID

TOKEN_READ = STANDARD_RIGHTS_READ | TOKEN_QUERY
TOKEN_WRITE = STANDARD_RIGHTS_WRITE | TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT
TOKEN_EXECUTE = STANDARD_RIGHTS_EXECUTE


