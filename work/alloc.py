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

class OSPageAllocator(object):
    def attach(self, id):
        raise NotImplementedError
    def detach(self):
        raise NotImplementedError

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
# XXX: this is prototype code, but we can optimize it by removing the
#      virtualprotect calls.

class WindowPageAllocator(OSPageAllocator):
    handle = None
    def attach(self, handle):
        # XXX: should we duplicatehandle this?
        self.handle = handle

    def detach(self, handle):
        self.handle = None

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
        return address

    def freeWriteable(self, address, count, **attrs):
        oldProtections = DWORD()
        
        res = k32.VirtualProtectEx(
            self.handle,
            address,
            count * 0x1000,
            PAGE_EXECUTE,
            byref(oldProtections)
        )
        return res != 0

    def freeExecutable(self, address, count, **attrs):
        MEM_DECOMMIT = 0x4000

        res = k32.VirtualFreeEx(
            self.handle,
            address,
            count * 0x1000,
            MEM_DECOMMIT
        )
        return res != 0

def getPageAllocator():
    return WindowPageAllocator()

