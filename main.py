import sys
sys.path.append('lib/')

import win32com.client as com
import ctypes

import context as ctx

k32 = ctypes.WinDLL('kernel32.dll')
advapi32 = ctypes.WinDLL('kernel32.dll')

# I am Yor, the hunter from the future
class ped_psapi(object):
    wmi = None

    def __init__(self, host="./"):
        super(ped_psapi, self).__init__()
        self.wmi = com.GetObject("winmgmts://%s"% host)
        
    def enumerateProcesses(self):
        res = self.wmi.InstancesOf('Win32_Process')
        return [ (x.Name, x.ProcessId) for x in res ]

    def enumerateThreads(self, pid):
        res = self.wmi.InstancesOf('Win32_Thread')
        res = [ int(x.Handle) for x in res if int(x.ProcessHandle) == pid ]
        assert len(res) > 0
        return res

class ped_debug(object):
    ## XXX: This was taken from http://www.rootkit.com/vault/c0de90e7/gw_ng.c
    ##      I'm not sure why I'm implementing it like this, i think it just
    ##      looked really fun. We get the added benefit of being able to call
    ##      code from the context of any thread

    def safe_set(self, value):
        k32.CloseHandle(self.__handle)
        self.__handle = value
    handle = property(fset=safe_set, fget=lambda self: self.__handle)
    __handle = None

    def __init__(self, tid, isBestowed=False):
        '''
        Yes, I know that 'isBestowed' is kind of weird.
        isBestowed means that this token will be inherited by our children.
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
        self.handle = k32.OpenThread(res, isBestowed, tid)
        assert self.handle

    def __del__(self):
        ## heh, it's a shame that we can't close this handle. thx, python! ;)
        ## we could use "with" i guess, but that shit's gay and only in 2.5
        # k32.CloseHandle(self.handle)
        pass

    def suspend(self):
        return k32.SuspendThread(self.handle)

    def resume(self):
        return k32.ResumeThread(self.handle)

    def terminate(self, exit=0):

        def killed(self, *args, **kwds):
            raise ValueError("Thread %x has been terminated"% self.handle)

        res = k32.TerminateThread(self.handle, exit)
        if res:
            self.__getattribute__ = killed
        return res

    def get(self, flags=ctx.CONTEXT_ALL):
        res = ctx.resolve( ctx.CONTEXT() )
        res['ContextFlags'] = flags

        self.suspend()
        error = k32.GetThreadContext(self.handle, ctypes.byref(res.me))
        self.resume()

        assert error
        return res

    def set(self, context):
        self.suspend()
        res = k32.SetThreadContext(self.handle, byref(context.me))
        self.resume()
        return res

if __name__ == '__main__':
    x = ped_psapi()
    res = dict(x.enumerateProcesses())
    res =  x.enumerateThreads( res[u'uedit32.exe'] )
    thread = res[0]

    # we don't do it by memory because that'd be slow as fuck
#    for x in moduleList(x):
#        searchModuleForInstructionsWeNeed()

    dbg = ped_debug(thread)
    res = dbg.get()
    res['Eip'] = 0
    res = dbg.set(res)
    print res
    
    print res
