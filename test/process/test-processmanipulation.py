
###
#### to fix the issue with window messages being dispatched, we might need to execute code that
###  calls GetQueueStatus, and then will empty the queue to dispatch them later

# this is the debugger attacher for manipulating a process
import sys,time
sys.path.append('lib/')

import win32com.client as com
import ctypes

import context as ctx

k32 = ctypes.WinDLL('kernel32.dll')
u32 = ctypes.WinDLL('user32.dll')
advapi32 = ctypes.WinDLL('kernel32.dll')

#hooker = ctypes.CDLL('whook.dll')

class ped_psapi(object):
    wmi = None

    def __init__(self, host="./"):
        super(ped_psapi, self).__init__()
        self.wmi = com.GetObject("winmgmts://%s"% host)

    def enumerateProcesses(self, verbose=False):
        res = self.wmi.InstancesOf('Win32_Process')
        return [ (x.ProcessId, x.Name, x.ExecutablePath, x.CommandLine) for x in res ]

    def enumerateThreads(self, pid):
        res = self.wmi.InstancesOf('Win32_Thread')
        res = [ (int(x.Handle), x.StartAddress, x.ThreadState, x.ThreadWaitReason) for x in res if int(x.ProcessHandle) == pid ]
        assert len(res) > 0
        return res

class ped_debug(object):
    ## XXX: This was taken from http://www.rootkit.com/vault/c0de90e7/gw_ng.c
    ##      I'm not sure why I'm implementing it like this, i think it just
    ##      looked really fun. We get the added benefit of being able to call
    ##      code from the context of any thread

    def safe_set(self, value):
        k32.CloseHandle(self.__hThread)
        self.__hThread = value
    hThread = property(fset=safe_set, fget=lambda self: self.__hThread)
    __hThread = None

    def __init__(self, tid, isBestowed=False):
        '''
        Yes, I know that 'isBestowed' is kind of weird.
        isBestowed means that these handles will be inherited by our children.
        '''

        STANDARD_RIGHTS_REQUIRED = 0xf0000
        SYNCHRONIZE = 0x100000
        THREAD_TERMINATE = 0x0001
        THREAD_SUSPEND_RESUME = 0x0002
        THREAD_GET_CONTEXT = 0x0008
        THREAD_SET_CONTEXT = 0x0010
        THREAD_SET_INFORMATION = 0x0020
        THREAD_QUERY_INFORMATION = 0x0040
        THREAD_SET_THREAD_TOKEN = 0x0080
        THREAD_IMPERSONATE = 0x0100
        THREAD_DIRECT_IMPERSONATION = 0x0200

        THREAD_ALL_ACCESS = STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0x3ff

        res = THREAD_SET_CONTEXT | THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME
        res = THREAD_ALL_ACCESS
        self.hThread = k32.OpenThread(res, isBestowed, tid)
        assert self.hThread

    def __del__(self):
        ## heh, it's a shame that we can't close these handles. thx, python! ;)
        ## we could use "with" i guess, but that shit's gay and only in 2.5
        # k32.CloseHandle(self.hThread)
        pass

    def suspend(self):
        return k32.SuspendThread(self.hThread)

    def resume(self):
        return k32.ResumeThread(self.hThread)

    def terminate(self, exit=0):

        def killed(self, *args, **kwds):
            raise ValueError("Thread %x has been terminated"% self.hThread)

        res = k32.TerminateThread(self.hThread, exit)
        if res:
            self.__getattribute__ = killed
        return res

    def get(self, flags=ctx.CONTEXT_ALL):
        res = ctx.resolve( ctx.CONTEXT() )
        res['ContextFlags'] = flags

        self.suspend()
        error = k32.GetThreadContext(self.hThread, ctypes.byref(res.me))
        self.resume()

        assert error
        return res

    def set(self, context):
        self.suspend()
        res = k32.SetThreadContext(self.hThread, ctypes.byref(context.me))
        self.resume()
        return res

def getProcessByName(name):
    x = ped_psapi()
    res = x.enumerateProcesses()
    res = dict([(b,a) for a,b,c,d in res])
    res = x.enumerateThreads( res[name] )
    return res[0]

### heh
options = { 'value':('Eax',0), 'address':('Ebx', 0x170), 'stack':0xc }
def ped_poke(dbg, address, value, options=options):
    res = dbg.get()

    # value
    reg,offset = options['value']
    res[reg] = value - offset

    # address
    reg,offset = options['address']
    res[reg] = address - offset

    ##
    res['Esp'] -= options['stack']
    res['Eip'] = write_address

    dbg.set(res)

write_address = 0x7c912dd9
stop_address = 0x7c940f45

if __name__ == '__main__':
    """
    .text:7C912DD9                   loc_7C912DD9:                           ; CODE XREF: .text:7C93C58Aj
    .text:7C912DD9 8B 46 20                          mov     eax, [esi+20h]
    .text:7C912DDC 5E                                pop     esi
    .text:7C912DDD 5B                                pop     ebx
    .text:7C912DDE 5D                                pop     ebp
    .text:7C912DDF C2 10 00                          retn    10h

    .text:7C940F45                   loc_7C940F45:                           ; CODE XREF: LdrpLoadImportModule(x,x,x,x,x):loc_7C940F45j
    .text:7C940F45 EB FE                             jmp     short loc_7C940F45

    #i need to identify what each instruction is capable of reading/writing, and how to save each state for restoration later
    # mov [ memxpr( add(@ebx, 0x170) ) ], register
    # pop register  (register)     #how do we make something useful out of stack-using instructions, w/o storing their value
    # pop register  (register)
    # pop register  (register)
    # leave  ( @esp )
    # retn 4 ( @eip )

    # jmp register

    # this type of hooking can be defeated via a SetWindowHookEx hook, which is
    # called from by the kernel via u32.DispatchHookW.
    # msctf.dll contains functions that use this hook. Ultramon.exe seems to set one.
    # these are also stored in PEB.KernelCallbackTable

    # addresses of hooks are stored in TEB.Win32ThreadInfo
    """

# [1] allocate space on stack
# [2] save top of stack
# [3] write halt instruction at return address
# [4] resume
# [5] check that we're at the halt address

    tid,address,state,reason = getProcessByName( u'notepad.exe' )
    print repr( (tid, address, state, reason) )
#    hooker.disableWindowHooks(tid)

    dbg = ped_debug(tid)

    dbg.suspend()
    original = dbg.get()
    print repr(original)

#    top = original['Esp'] - 4
#    res['Ebp'] = top
#    res['Esp'] = top - options['stack']
#    dbg.set(res)
#    ped_poke(dbg, top+4, stop_address)

    res = dbg.get()
    res['Eip'] = stop_address
    res['Eax'] = 0x0d0e0a0d
    res['Ebx'] = 0x0d0e0a0d
    res['Ecx'] = 0x0d0e0a0d
    res['Edx'] = 0x0d0e0a0d

    dbg.set(res)

    dbg.resume()
#    dbg.set(original)
###

"""
bp 0x7c912dd9
bp 0x7c940f45
"""

############## enumthread windows
from ctypes import *

def enumerateThreadWindows(threadId):
    WNDENUMPROC = WINFUNCTYPE(c_int, c_int, c_long)

    windows = []
    def enumerator(hWnd, object):
        windows.append(hWnd)
        return 1

    res = u32.EnumThreadWindows(threadId, WNDENUMPROC(enumerator), c_void_p(0))
    assert bool(res)

    return windows

def getLastErrorTuple():
    errorCode = GetLastError()
    p_string = c_void_p(0)

    # FORMAT_MESSAGE_
    ALLOCATE_BUFFER = 0x100
    FROM_SYSTEM = 0x1000
    res = k32.FormatMessageA(
        ALLOCATE_BUFFER | FROM_SYSTEM, 0, errorCode,
        0, pointer(p_string), 0, None
    )
    res = cast(p_string, c_char_p)
    errorString = str(res.value)
    res = k32.LocalFree(res)
    assert res == 0, "kernel32!LocalFree failed. Error 0x%08x."% k32.GetLastError()

    return (errorCode, errorString)

def getLastErrorString():
    code, string = getLastErrorTuple()
    return string

def getWindowText(hWnd):
    buffer = (c_byte*1024)()
    res = u32.GetWindowTextA( hWnd, pointer(buffer), len(buffer) )
    assert bool(res), repr(getLastErrorTuple())
    return ''.join([ chr(x) for x in buffer ][ : res ])

def sendUpdateMessage(hWnd):
    WM_PAINT = 0x000f   # WinUser.h
    res = u32.PostMessageA(hWnd, WM_PAINT, 0, 0)
    if bool(res):
        print 'WM_PAINT was processed by application'
    else:
        print 'WM_PAINT was not processed by application'
    return True

res = enumerateThreadWindows(tid)
print repr([hex(x) for x in res])
print repr([getWindowText(x) for x in res])

res = [ sendUpdateMessage(hwnd) for hwnd in res ]
