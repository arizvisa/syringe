import sys,time
from ctypes import *

guiThread = 0x98c
address = 0x7C935288 

try:
    guiThread, address = [int(x,16) for x in sys.argv[1:]]

except:
    blah = """
    guiThread
    specify the thread that you know contains the GDI message pump

    address
    set eip to this instruction (like an EB FE that you can find in ntdll.dll)
    my box has a useful address of 7C935288

    to repro, pick a thread like that belongs to notepad.
    choose the first thread id (should be the gui thread).
    after this program sets its thread context.
    attach to the process, and check the register state.

    eax, ebx, ecx, edx should all be set to 0x0d0e0a0d
    eip should be at the address that you chose.
    """
    sys.stderr.write('%s threadContainingGDIMessagePump addressOfBlockInstruction\n'% sys.argv[0])
    sys.stderr.write(blah)

    sys.exit(0)
    
# ctypes shit
class CONTEXT(Structure):
    _fields_ = [
        ('ContextFlags', c_long),
        ('Dr0', c_uint32),
        ('Dr1', c_uint32),
        ('Dr2', c_uint32),
        ('Dr3', c_uint32),
        ('Dr6', c_uint32),
        ('Dr7', c_uint32),
        ('FloatSave', c_uint32*28),
        ('SegGs', c_uint32),
        ('SegFs', c_uint32),
        ('SegEs', c_uint32),
        ('SegDs', c_uint32),
        ('Edi', c_uint32),
        ('Esi', c_uint32),
        ('Ebx', c_uint32),
        ('Edx', c_uint32),
        ('Ecx', c_uint32),
        ('Eax', c_uint32),
        ('Ebp', c_uint32),
        ('Eip', c_uint32),
        ('SegCs', c_uint32),
        ('EFlags', c_uint32),
        ('Esp', c_uint32),
        ('SegSs', c_uint32),
        ('ExtendedRegisters', c_byte * 512)
    ]

# blah
u32 = windll.user32
k32 = windll.kernel32

### open thread
THREAD_SET_CONTEXT = 0x0010
THREAD_GET_CONTEXT = 0x0008
THREAD_SUSPEND_RESUME = 0x0002
hThread = k32.OpenThread(
    THREAD_SET_CONTEXT|THREAD_GET_CONTEXT|THREAD_SUSPEND_RESUME, 
    False,
    guiThread
)
assert hThread, "unable to open thread %x"% guiThread

### suspend thread
res = k32.SuspendThread(hThread)
assert res != -1, "unable to suspend thread"

### get its context
CONTEXT_i386 = 0x00010000
CONTEXT_i486 = 0x00010000
CONTEXT_CONTROL = (CONTEXT_i386 | 0x00000001L)
CONTEXT_INTEGER = (CONTEXT_i386 | 0x00000002L)
CONTEXT_SEGMENTS = (CONTEXT_i386 | 0x00000004L)
CONTEXT_FLOATING_POINT = (CONTEXT_i386 | 0x00000008L)
CONTEXT_DEBUG_REGISTERS = (CONTEXT_i386 | 0x00000010L)
CONTEXT_EXTENDED_REGISTERS = (CONTEXT_i386 | 0x00000020L)
CONTEXT_FULL = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS)
CONTEXT_ALL = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS | CONTEXT_FLOATING_POINT | CONTEXT_DEBUG_REGISTERS | CONTEXT_EXTENDED_REGISTERS)

blah = CONTEXT()
blah.ContextFlags = 65559
res = k32.GetThreadContext(hThread, pointer(blah))
assert bool(res), 'unable to getthreadcontext'

### set thread context
blah.Eip = address
blah.Eax = 0x0d0e0a0d
blah.Ebx = 0x0d0e0a0d
blah.Ecx = 0x0d0e0a0d
blah.Edx = 0x0d0e0a0d
res = k32.SetThreadContext(hThread, pointer(blah))
assert bool(res), 'unable to setthreadcontext'

print 'waiting 5 seconds...try sending the thread some messages'
time.sleep(5)

### resume thread
res = k32.ResumeThread(hThread)
assert res != -1, 'unable to resumethread'

### now we attach to the process see what the registers are set to

