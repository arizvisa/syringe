import utils
import warnings

class provider(object):
    '''Base provider class. Intended to be Inherited from'''
    def seek(self, offset):
        '''Seek to a particular offset'''
        raise NotImplementedError('Developer forgot to overload this method')
    def consume(self, amount):
        '''Read some number of bytes'''
        raise NotImplementedError('Developer forgot to overload this method')
    def write(self, data):
        '''Write some number of bytes'''
        raise NotImplementedError('Developer forgot to overload this method')

class file(provider):
    '''Basic file provider'''
    file = None
    def __init__(self, filename, mode='rb'):
        ## XXX: i thought __builtins__ was a module...
        if not mode.startswith('r'):
            warnings.warn("You are not using the correct syntax for a mode, so i'm fixing it for you")
            mode = 'r+b'

        if 'w' in mode:
            warnings.warn("You are not using the correct syntax for a mode, so i'm fixing it for you")
            mode = 'r+b'

        if not mode.endswith('b'):
            mode += 'b'

        self.file = __builtins__['file'](filename, mode)

    def seek(self, offset):
        self.file.seek(offset)

    def consume(self, amount):
        offset,result = self.file.tell(), self.file.read(amount)
        if len(result) == amount:
            return result
        raise StopIteration('Unable to read 0x%x bytes at file offset 0x%x'% (amount, offset))

    def write(self, data):
        return self.file.write(data)

    def close(self):
        return self.file.close()

    def size(self):
        old = self.file.tell()
        self.file.seek(0, 2)
        result = self.file.tell()
        self.file.seek(old, 0)
        return result

    def __repr__(self):
        return '%s -> %s'% (super(file, self).__repr__(), repr(self.file))

class iter(provider):
    '''Basic iterator provider'''
    iterator = iter
    def __init__(self, iterable):
        iterable = iter(iterable)
        self.iterator = iterable

    def seek(self, offset):
        ## Seeking does nothing on an iterator
        pass

    def consume(self, amount):
        return ''.join([x for i,x in zip(utils.infiniterange(0), self.iterator)])

    def write(self, data):
        ## Can't write to an iterator
        pass

class string(provider):
    '''Basic string provider'''

    offset = int
    string = str
    def __init__(self, string):
        self.string = str(string)
    def seek(self, offset):
        self.offset = offset
    def consume(self, amount):
        res = self.string[self.offset: self.offset+amount]
        self.offset += amount
        return res
    def write(self, data):
        left, right = self.offset, self.offset + len(data)
        self.string = self.string[:left] + data + self.string[right:]
        self.offset = right
        return len(data)

import ctypes
from ctypes import *

## TODO: figure out an elegant way to catch exceptions we might cause
##       by dereferencing any of these pointers

class memory(provider):
    '''Basic in-process memory provider using ctypes'''
    address = 0
    def seek(self, offset):
        self.address = offset

    def consume(self, amount):
        res = memory._read(self.address, amount)
        self.address += amount
        return res

    def write(self, data):
        res = memory._write(self.address, data)
        self.address += len(data)
        return res

    @staticmethod
    def _read(address, length):
        blockpointer = POINTER(c_char*length)
        v = c_void_p(address)
        p = cast(v, blockpointer)
        return ''.join(p.contents)

    @staticmethod
    def _write(address, value):
        length = len(value)
        blockpointer = POINTER(c_char*length)
        v = c_void_p(address)
        p = cast(v, blockpointer)
        for i,c in zip(xrange(length), str(value)):
            p.contents[i] = c
        return True

import sys
if sys.platform == 'win32':
    k32 = ctypes.WinDLL('kernel32.dll')
    class WindowsProcessHandle(provider):
        '''Given a process handle'''
        address = 0
        handle = None
        def __init__(self, handle):
            self.handle = handle

        def seek(self, offset):
            '''Seek to a particular offset'''
            self.address = offset

        def consume(self, amount):
            NumberOfBytesRead = ctypes.c_int()
            res = ctypes.c_char*amount
            Buffer = res()

            res = k32.ReadProcessMemory(self.handle, self.address, Buffer, amount, byref(NumberOfBytesRead))
            if res == 0:
                raise ValueError('Unable to read pid(%x)[%08x:%08x].'% (self.handle, self.address, self.address+amount))

            assert NumberOfBytesRead.value == amount, 'Expected %d bytes, received %d bytes.'% (amount, NumberOfBytesRead.value)

            self.address += amount
            # XXX: test tihs shit out
            return str(Buffer.raw)

        def write(self, value):
            NumberOfBytesWritten = ctypes.c_int()

            res = ctypes.c_char*len(value)
            Buffer = res()
            Buffer.value = value

            res = k32.WriteProcessMemory(self.handle, self.address, Buffer, len(value), byref(NumberOfBytesWritten)) 
            if res == 0:
                raise ValueError('Unable to write to pid(%x)[%08x:%08x].'% (self.id, self.address, self.address+len(value)))

            self.address += len(value)

            #assert NumberOfBytesWritten.value == amount, 'Expected %d bytes, received %d bytes.'% (amount, NumberOfBytesWritten.value)
            return NumberOfBytesWritten.value

    def WindowsProcessId(pid, **attributes):
        handle = k32.OpenProcess(0x30, False, pid)
        return WindowsProcessHandle(handle)
