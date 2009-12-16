import ctypes,ctypeless
k32 = ctypes.WinDLL('kernel32.dll')
advapi32 = ctypes.WinDLL('advapi32.dll')
ntdll = ctypes.WinDLL('ntdll.dll')

from utils import *
from win32context import *

class debug(object):
    def attach(self, id, **kwds):
        '''attaches to an entity identified by id'''
        raise NotImplementedError

    def suspend(self):
        '''suspends execution of entity. returns previous suspend count'''
        raise NotImplementedError
    def resume(self):
        '''resumes execution of entity. returns previous resume count'''
        raise NotImplementedError

    def detach(self):
        '''detach from an entity'''
        raise NotImplementedError

    def read(self, address, length):
        '''read from memory from entity'''
        raise NotImplementedError

    def write(self, address, value):
        '''write value to memory of entity'''
        raise NotImplementedError

    def getcontext(self):
        '''get an entity's context. return a dictionary type'''
        raise NotImplementedError

    def setcontext(self, context):
        '''set an entity's context. take's a dictionary type'''
        raise NotImplementedError

def raiseW32Error(message):
    raise OSError("%s\nGetLastError() -> %s"% (message, repr(getLastErrorTuple())))

class win32thread(debug):
    '''packages everything needed for managing the win32 process at the thread granularity'''
    id = 0
    handle = None

    def attach(self, id, **kwds):
        assert self.handle == None          ## avoid attaching more than once

        access = kwds.get('access', THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_SUSPEND_RESUME|THREAD_QUERY_INFORMATION)
        res = k32.OpenThread(access, False, id)
        if res == 0:
            raiseW32Error('Unable to open thread %d(0x%x)'% (id, id))

        self.handle = res
        self.id = id

    def detach(self):
        res = k32.CloseHandle(self.handle)
        self.handle = self.id = None

    def getcontext(self):
        ctx = CONTEXT()
        ctx.ContextFlags = CONTEXT_ALL

        res = k32.GetThreadContext(self.handle, ctypes.byref(ctx))
        if res == 0:
            raiseW32Error('Unable to get context for thread %d(0x%x)'% (self.id, self.id))
        return ctx

    def setcontext(self, context):
        res = k32.SetThreadContext(self.handle, ctypes.byref(context))
        if res == 0:
            raiseW32Error('Unable to set thread context for %d(0x%x)'% (self.id, self.id))

    def getPid(self):
        ## XXX: need to get process id from thread handle
        resultSize = c_int()
        tbi = THREAD_BASIC_INFORMATION()
        res = ntdll.NtQueryInformationThread(self.handle, ThreadBasicInformation, byref(tbi), sizeof(tbi), byref(resultSize))
        if res != 0:        # XXX: is this right?
            raiseW32Error('Unable to get process id for %d(0x%x)'% (self.id, self.id))
            
        assert resultSize.value == sizeof(tbi), "result size does not match expected size"
        assert tbi.ClientId.UniqueThread == self.id, "returned thread id does not %d(0x%x)"% (self.id, self.id)
        return tbi.ClientId.UniqueProcess

    def suspend(self):
        return k32.SuspendThread(self.handle)
    def resume(self):
        return k32.ResumeThread(self.handle)

class win32process(debug):
    '''packages everything needed for managing the win32 process'''
    k32.DebugSetProcessKillOnExit(False)    #XXX: polite by default
    handle = None
    id = 0
    def attach(self, id, **kwds):
        res = k32.OpenProcess(kwds.get('access', PROCESS_ALL_ACCESS), False, id)
        if res == 0:
            raiseW32Error('Unable to open process %d(0x%x)'% (id, id))
        handle = res

        res = k32.DebugActiveProcess(id)
        if res == 0:
            k32.CloseHandle(handle)
            raiseW32Error('Unable to attach to process %d(0x%x)'% (id, id))

        self.handle = handle
        self.id = id

        res = k32.DebugSetProcessKillOnExit(False)
        if res == 0:
            __import__('warnings').warn('Unable to set process kill on exit')


    def detach(self):
        id = self.id

        res = k32.DebugActiveProcessStop(id)
        k32.CloseHandle(self.handle)
        if res == 0:
            raiseW32Error('Unable to detach from pid %d(%x).'% (id, id))

        self.handle = self.id = None

    def read(self, address, length):
        NumberOfBytesRead = ctypes.c_int()
        res = ctypes.c_char*length
        Buffer = res()

        res = k32.ReadProcessMemory(self.handle, address, Buffer, length, byref(NumberOfBytesRead))
        if res == 0:
            raiseW32Error('Unable to read pid(%x)[%08x:%08x].'% (5, address, address+length))

        assert NumberOfBytesRead.value == length, 'Expected %d bytes, received %d bytes.'% (length, NumberOfBytesRead.value)

        # XXX: test tihs shit out
        res = str(Buffer.raw)
        return res

    def write(self, address, value):
        NumberOfBytesWritten = ctypes.c_int()

        res = ctypes.c_char*len(value)
        Buffer = res()
        Buffer.value = value

        res = k32.WriteProcessMemory(self.handle, address, Buffer, len(value), byref(NumberOfBytesWritten)) 
        if res == 0:
            raiseW32Error('Unable to write to pid(%x)[%08x:%08x].'% (self.id, address, address+len(value)))

        #assert NumberOfBytesWritten.value == length, 'Expected %d bytes, received %d bytes.'% (length, NumberOfBytesWritten.value)

        return NumberOfBytesWritten.value

class win32debug(debug):
    thread = process = None
    def attach(self, id, **kwds):
        res = win32thread()
        res.attach(id)
        self.thread = res

        pid = self.thread.getPid()
        ## need to check if we're already attached to this particular pid
        ##     and then use that as our self.process handle
        res = win32process()
        res.attach(pid)
        self.process = res

    def detach(self):
        self.process.detach()
        self.thread.detach()
        self.process = self.thread = None

    def read(self, address, length):
        if length > 0:
            return self.process.read(address, length)
        #warn('Refused read of 0 bytes from %x'% address)
        return ''

    def write(self, address, value):
        if len(value) > 0:
            return self.process.write(address, value)
        #warn('Refused write of 0 bytes to %x'% address)
        return 0

    def setcontext(self, context):
        return self.thread.setcontext(context.me)

    def getcontext(self):
        return ctypeless.resolve(self.thread.getcontext())

    def enablePrivileges(self):
        id = k32.GetCurrentProcessId()

        token = HANDLE()
        res = advapi32.OpenProcessToken( k32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES|TOKEN_QUERY, byref(token))
        if res == 0:
            raiseW32Error('Unable to open a token to ourself %d(0x%x)'% (id, id))

        luid = LUID()
        res = advapi32.LookupPrivilegeValueA(None, "SeDebugPrivilege", byref(luid))
        if res == 0:
            raiseW32Error('Unable to lookup "SeDebugPrivilege" for %d(0x%x)'% (id, id))

        tokenPrivileges = TOKEN_PRIVILEGES()
        tokenPrivileges.PrivilegeCount = 1
        tokenPrivileges.Privileges[0].Luid = luid
        tokenPrivileges.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
        res = advapi32.AdjustTokenPrivileges(token, False, byref(tokenPrivileges), 0, None, None)
        if res == 0:
            raiseW32Error('Unable to enable "SeDebugPrivilege" for %d(0x%x)'% (id, id))

        # should not fail
        return True

    def suspend(self):
        return self.thread.suspend()

    def resume(self):
        return self.thread.resume()

def Default(*args, **kwds):
    return win32debug()
