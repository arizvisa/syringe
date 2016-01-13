"""
This module abstracts page fetching from the os.
It's intended to be used by a memorymanager, so don't
use this directly unless you know what you're doing.

To use this, call one of the following.
allocator.new(pid=yourpid)
allocator.new(handle=yourhandle)
"""

import sys,ctypes
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

    def setMemoryPermission(self, address, count, permission):
        '''
        Changes the permisions of /count/ pages at /address/ to /permission/.
        Permission = 110 (rwx) - readable and writeable, but not executable
        '''
        raise NotImplementedError

    def read(self, address, length):
        '''Read /length/ bytes starting at /address/'''
        raise NotImplementedError

    def write(self, address, data):
        '''Write /data/ to the location specified by /address/'''
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

    def freeExecutable(self, address, count, **attrs):
        '''
        removes the pages that were marked executable
        '''
        raise NotImplementedError

    def getPageSize(self):
        '''returns page size of the platform'''
        raise NotImplementedError

    ## XXX: this is cheating, but it makes allocators work just like a ptypes source
    __offset = 0
    def seek(self, offset):
        self.__offset = offset
    def consume(self, amount):
        return self.read(self.__offset, amount)
    def write(self, data):
        return self.write(self.__offset, data)

class Local(OSExecPageAllocator):
    def read(self, address, length):
        blockpointer = ctypes.POINTER(ctypes.c_char*length)
        v = ctypes.c_void_p(address)
        p = ctypes.cast(v, blockpointer)
        return ''.join(p.contents)

    def write(self, address, value):
        assert type(value) is str
        length = len(value)
        blockpointer = ctypes.POINTER(ctypes.c_char*length)
        v = ctypes.c_void_p(address)
        p = ctypes.cast(v, blockpointer)
        for i,c in zip(xrange(length), str(value)):
            p.contents[i] = c
        return True

if sys.platform == 'linux2':
    libc = ctypes.CDLL('libc.so.6')
    libc.mmap.restype = ctypes.c_uint

    PROT_NONE = 0x0
    PROT_READ = 0x1
    PROT_WRITE = 0x2
    PROT_EXEC = 0x4
    PROT_GROWSDOWN = 0x01000000
    PROT_GROWSUP = 0x02000000
    MAP_SHARED = 0x01
    MAP_PRIVATE = 0x02
    MAP_FIXED = 0x10
    MAP_FILE = 0
    MAP_ANONYMOUS = 0x20
    MAP_GROWSDOWN = 0x00100
    MAP_DENYWRITE = 0x00800
    MAP_EXECUTABLE = 0x01000
    MAP_LOCKED = 0x02000
    MAP_NORESERVE = 0x04000
    MAP_POPULATE = 0x08000
    MAP_NONBLOCK = 0x10000

    class LinuxLocal(Local):
        def getPageSize(self):
            return 1<<12

        def getWriteable(self, desiredAddress, count, **attrs):
            res = libc.mmap(
                desiredAddress, count*4096, PROT_WRITE|PROT_READ,
                MAP_ANONYMOUS|MAP_PRIVATE, -1, 0
            )
            if res == 0xffffffff:
                raise OSError('Unable to map page')
            return res

        def freeWriteable(self, address, count, **attrs):
            res = libc.munmap(address, count*4096)
            if res == 0xffffffff:
                raise OSError('Unable to unmap page')
            return res

        def getExecutable(self, sourceAddress, count, **attrs):
            size = count * 4096
            res = libc.mprotect(sourceAddress, size, PROT_READ|PROT_EXEC)
            if res == 0xffffffff:
                raise OSError('Unable to mprotect page')
            return sourceAddress

        def freeExecutable(self, address, count, **attrs):
            return self.freeWriteable(address, count)

    def new(*args, **kwds):
        return LinuxLocal(*args, **kwds)

############################ platform specific shit
if sys.platform == 'win32':
    k32 = ctypes.WinDLL('kernel32.dll')
    from win32context import *

    ### utility functions
    def getLastErrorTuple():
        errorCode = k32.GetLastError()
        p_string = ctypes.c_void_p(0)

        # FORMAT_MESSAGE_
        ALLOCATE_BUFFER = 0x100
        FROM_SYSTEM = 0x1000
        res = k32.FormatMessageA(
            ALLOCATE_BUFFER | FROM_SYSTEM, 0, errorCode,
            0, ctypes.pointer(p_string), 0, None
        )
        res = ctypes.cast(p_string, ctypes.c_char_p)
        errorString = str(res.value)
        res = k32.LocalFree(res)
        assert res == 0, "kernel32!LocalFree failed. Error 0x%08x."% k32.GetLastError()

        return (errorCode, errorString)

    def getLastErrorString():
        code, string = getLastErrorTuple()
        return string

    ### alocator definitions
    class Windows(Local):
        handle = int

        def setMemoryPermission(self, address, count, permission):
            # O(1), baby

            allocatorToKernel = {
                0: PAGE_NOACCESS,
                1: PAGE_EXECUTE,
                2: PAGE_WRITECOPY,            #wtf?
                3: PAGE_EXECUTE_WRITECOPY,    #?
                4: PAGE_READONLY,
                5: PAGE_EXECUTE_READ,
                6: PAGE_READWRITE,
                7: PAGE_EXECUTE_READWRITE,
            }

            oldProtections = ctypes.c_uint32()
            res = k32.VirtualProtectEx(
                self.handle,
                address,
                count * 0x1000,
                allocatorToKernel[permission],
                ctypes.byref(oldProtections)
            )
            if not res:
                raise OSError("GetLastError() -> %s"% (repr(getLastErrorTuple())))

            # and...back
            kernelToAllocator = { PAGE_NOACCESS : 0, PAGE_EXECUTE : 1, PAGE_WRITECOPY : 2, PAGE_EXECUTE_WRITECOPY : 3, PAGE_READONLY : 4, PAGE_EXECUTE_READ : 5, PAGE_READWRITE : 6, PAGE_EXECUTE_READWRITE : 7 }
            return kernelToAllocator[oldProtections.value]

        def getPageSize(self):
            return 1<<12

        def getWriteable(self, address, count, **attrs):
            MEM_COMMIT = 0x1000
            MEM_RESERVE = 0x2000
            res = k32.VirtualAllocEx(
                self.handle,
                address,
                count * 0x1000,
                MEM_COMMIT|MEM_RESERVE,
                PAGE_READWRITE
            )
            if not res:
                raise OSError("GetLastError() -> %s"% (repr(getLastErrorTuple())))
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
                raise OSError("GetLastError() -> %s"% (repr(getLastErrorTuple())))
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
                raise OSError("GetLastError() -> %s"% (repr(getLastErrorTuple())))
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
                raise OSError("GetLastError() -> %s"% (repr(getLastErrorTuple())))
            return res != 0

        def read(self, address, length):
            assert type(address) in (int,long), "Invalid address type %s"% repr(address)
            assert type(length) in (int,long)
            NumberOfBytesRead = ctypes.c_int()
            res = ctypes.c_char*length
            Buffer = res()

            res = k32.ReadProcessMemory(self.handle, address, Buffer, length, byref(NumberOfBytesRead))
            if res == 0:
                message = 'Unable to read from handle(%x)[%08x:%08x].'% (self.handle, address, address+length)
                raise OSError(message, "GetLastError() -> %s"% (repr(getLastErrorTuple())))

            assert NumberOfBytesRead.value == length, 'Expected %d bytes, received %d bytes.'% (length, NumberOfBytesRead.value)
            return str(Buffer.raw)

        def write(self, address, value):
            assert type(address) in (int,long), "Invalid address type %s"% repr(address)
            assert type(value) is str
            NumberOfBytesWritten = ctypes.c_int()

            res = ctypes.c_char*len(value)
            Buffer = res()
            Buffer.value = value

            res = k32.WriteProcessMemory(self.handle, address, Buffer, len(value), byref(NumberOfBytesWritten))
            if res == 0:
                message = 'Unable to write to handle(%x)[%08x:%08x].'% (self.handle, address, address+len(value))
                raise OSError(message, "GetLastError() -> %s"% (repr(getLastErrorTuple())))

            #assert NumberOfBytesWritten.value == len(value), 'Expected %d bytes, received %d bytes.'% (len(value), NumberOfBytesWritten.value)
            return NumberOfBytesWritten.value

    class WindowsHandle(Windows):
        def __init__(self, handle):
            id = k32.GetProcessId(handle)
            self.handle = handle
            super(WindowsHandle, self).__init__(id)

    class WindowsProcessId(Windows):
        def __init__(self, pid, **kwds):
            res = k32.OpenProcess(kwds.get('access', PROCESS_INFO_ALL|PROCESS_VM_ALL), False, pid)
            if res == 0:
                raise OSError('Unable to open process %d(0x%x)'% (pid, pid))
            self.handle = res
            self.id = pid

        def detach(self):
            k32.CloseHandle(self.handle)
            self.handle = self.id = None

    class WindowsLocal(Windows):
        def __init__(self):
            id = k32.GetCurrentProcess()
            super(WindowsLocal, self).__init__(id)
            self.handle = id    # XXX: shouldn't this be a handle of some kind?

    def new(*args, **kwds):
        if 'pid' in kwds:
            pid = kwds['pid']
            del(kwds['pid'])
            return WindowsProcessId(pid, **kwds)
        if 'handle' in kwds:
            handle = kwds['handle']
            del(kwds['handle'])
            return WindowsHandle(handle, **kwds)
        return WindowsLocal()

if __name__ == '__main__':
    import allocator
    x = allocator.new()

    res = x.getWriteable(0x0, 4)
    print hex(res)
    x.write(res, 'ehlo')

    v = x.getExecutable(res, 4)
    print hex(v)
    print repr(x.read(res, 4))

    x.freeWriteable(res, 4)
    # should fail on windows
    x.freeExecutable(v, 4)
