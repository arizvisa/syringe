import ctypes
k32 = ctypes.WinDLL('kernel32.dll')
from win32context import *

### this is written this way in case we need to target this at PaX.
## logic is like:
##    1] address = getWriteableMemory(suggestion, length)
##    2] newaddress = getExecutableMemory(address, length)
##           this will transform already writeable data to something executable
##    3] freeExecutable(newaddress, length)
##    4] freeWriteable(address, length)

class OSExecPageAllocator(object):
    def __init__(self, id):
        self.id = id

    def getWriteable(self, desiredAddress, count, **attrs):
        '''
        returns a pointer to a contiguous list of writeable pages
        '''
        raise NotImplementedError

    def freeWriteable(self, address, count, **attrs):
        '''
        unmaps specified pages
        '''
        raise NotImplementedError

    def getExecutable(self, sourceAddress, count, **attrs):
        '''
        returns a pointer to some executable memory
        using the data in the specified pages
        '''
        raise NotImplementedError

    def freeExecutable(self, sourceAddress, count, **attrs):
        '''
        removes the pages that were marked executable
        '''
        raise NotImplementedError

    def getPageSize(self):
        '''returns page size of the platform'''
        raise NotImplementedError

############################ platform specific shit
# XXX: this is prototype code, but we can "optimize" (heh) it by removing the
#      virtualprotect calls.

import utils
class Windows(OSExecPageAllocator):
    handle = int

    def __init__(self, debugger):
        super(Windows, self).__init__(debugger)
        self.handle = self.id.process.handle

    def getPageSize(self):
        return 1<<12

    def getWriteable(self, address, count, **attrs):
        MEM_COMMIT = 0x1000
        res = k32.VirtualAllocEx(
            self.handle,
            address,
            count * 0x1000,
            MEM_COMMIT,
            PAGE_READWRITE
        )
        if not res:
            raise OSError("GetLastError() -> %s"% (repr(utils.getLastErrorTuple())))
        return res

    def getExecutable(self, address, count, **attrs):
        oldProtections = DWORD()
        
        res = k32.VirtualProtectEx(
            self.handle,
            address,
            count * 0x1000,
            PAGE_EXECUTE,
            byref(oldProtections)
        )
        if not res:
            raise OSError("GetLastError() -> %s"% (repr(utils.getLastErrorTuple())))
        return address

    def freeExecutable(self, address, count, **attrs):
        oldProtections = DWORD()

        res = k32.VirtualProtectEx(
            self.handle,
            address,
            count * 0x1000,
            PAGE_EXECUTE,
            byref(oldProtections)
        )
        if not res:
            raise OSError("GetLastError() -> %s"% (repr(utils.getLastErrorTuple())))
        return res != 0

    def freeWriteable(self, address, count, **attrs):
        MEM_DECOMMIT = 0x4000

        res = k32.VirtualFreeEx(
            self.handle,
            address,
            count * 0x1000,
            MEM_DECOMMIT
        )
        if not res:
            raise OSError("GetLastError() -> %s"% (repr(utils.getLastErrorTuple())))
        return res != 0

def Default(*args, **kwds):
    return Windows(*args, **kwds)

