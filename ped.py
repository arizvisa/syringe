# this is the debugger attacher for manipulating a process

import sys
sys.path.append('lib/')

import win32com.client as com
import ctypes

import context as ctx

k32 = ctypes.WinDLL('kernel32.dll')
advapi32 = ctypes.WinDLL('kernel32.dll')

hooker = ctypes.CDLL('hooker.dll')

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

if __name__ == '__main__':
.text:7C92B04D 89 83 70 01 00 00                 mov     [ebx+170h], eax
.text:7C92B053 5F                                pop     edi
.text:7C92B054 5E                                pop     esi
.text:7C92B055 5B                                pop     ebx
.text:7C92B056 C9                                leave
.text:7C92B057 C2 04 00                          retn    4

7c92a931
.text:7C92A931 EB FE                             jmp     short 7C92A931

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

    # execution of hooks are stored in TEB.Win32ThreadInfo

    pid = 3560

    tid,address,state,reason = getProcessByName( u'pidgin.exe' )
    hooker.disableWindowHooks(tid)

    #hProcess = k32.OpenProcess(0x0400, False, pid)
    #res = k32.FlushInstructionCache( hProcess, 0x7c92b04d, 0x1000 )
    dbg = ped_debug(tid)

    # need to first write 0x7c92a931 at the top of our call stack
    # the write also needs to return to this address too

    # push a return address onto our stack
    dbg.suspend()
    
    res = dbg.get()
    original, res = (dbg.get(), dbg.get())
    bottom = original['Ebp']-8
#    res['Eip'] = 0x7c92b04d
    res['Eip'] = 0x7c92a931
    res['Ebp'] = bottom-4
    res['Esp'] -= 0x4000

    res['Ebx'] = bottom - 0x170
    res['Eax'] = 0xcccccccc

    dbg.suspend()
    assert dbg.set(res)
    assert dbg.set(original)
    dbg.resume()

    dbg.resume()            # this triggers the hook

bp 0x7c92b04d
bp 0X7c92b053
