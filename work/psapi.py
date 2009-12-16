import ctypes
import win32com.client as com

# FIXME: the attach/detach interface is lame
#        i need to remove this dependency on pywin32, and use comtypes instead

class psapi(object):
    def attach(self, id, **attrs):
        raise NotImplementedError
    def detach(self, **attrs):
        raise NotImplementedError

    def enumerateProcesses(self, **attrs):
        raise NotImplementedError

    def enumerateThreads(self, id, **attrs):
        raise NotImplementedError

def getInterface():
    return psapi_win32()

### FIXME: might want to switch this to an attach/detach interface
class psapi_win32(object):
    wmi = None

    def attach(self, id="./"):
        self.wmi = com.GetObject("winmgmts://%s"% id)

    def detach(self):
        # XXX: do we need to call some windows function to deallocate self.wmi?
        self.wmi = None
        
    def enumerateProcesses(self):
        '''returns a tuple of (process id, name, executable path, commandline)'''
        res = self.wmi.InstancesOf('Win32_Process')
        return [ (x.ProcessId, x.Name, x.ExecutablePath, x.CommandLine) for x in res ]

    def enumerateThreads(self, id):
        '''returns a tuple of (thread handle, start address, thread state, thread block reason)'''
        res = self.wmi.InstancesOf('Win32_Thread')
        res = [ (int(x.Handle), x.StartAddress, x.ThreadState, x.ThreadWaitReason) for x in res if int(x.ProcessHandle) == id ]
        assert len(res) > 0
        return res

