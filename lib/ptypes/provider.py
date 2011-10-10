import utils
import os,logging

class base(object):
    '''Base provider class. Intended to be Inherited from'''
    def seek(self, offset):
        '''Seek to a particular offset'''
        raise NotImplementedError('Developer forgot to overload this method')
    def consume(self, amount):
        '''Read some number of bytes'''
        raise NotImplementedError('Developer forgot to overload this method')
    def store(self, data):
        '''Write some number of bytes'''
        raise NotImplementedError('Developer forgot to overload this method')

class empty(base):
    '''Empty'''
    offset = 0
    def seek(self, offset):
        '''Seek to a particular offset'''
        offset=0
    def consume(self, amount):
        '''Read some number of bytes'''
        return '\x00'*amount
    def store(self, data):
        '''Write some number of bytes'''
        raise OSError('Attempted to write to read-only medium %s'% repr(self))

class file(base):
    '''Basic file provider'''
    file = None
    def __init__(self, filename, mode='rb'):
        # lie to the user, and always ensure we can
        #   read from the file in binary
        mode = set(list(mode))
        if 'w' in mode:
            if os.access(filename,6):
                logging.info("-> %s.%s(%s, %s) : opened file for write", self.__module__, type(self).__name__, repr(filename), repr(mode))
                mode = 'r+b'
            else:
                # overwrite
                logging.info("-> %s.%s(%s, %s) : creating new file", self.__module__, type(self).__name__, repr(filename), repr(mode))
                mode = 'wb'
        else:
            logging.warn("-> %s.%s(%s, %s): you didn't ask for 'r', which is important. so, i'm fixing it for you by giving you 'r+b' instead", self.__module__, type(self).__name__, repr(filename), repr(mode))
            mode = 'r+b'

        ## XXX: i thought __builtins__ was a module...
        self.file = __builtins__['file'](filename, mode)

    def seek(self, offset):
        self.file.seek(offset)

    def consume(self, amount):
        offset = self.file.tell()
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(offset,amount,self)

        result = self.file.read(amount)
        if len(result) == amount:
            return result
        raise StopIteration('unable to complete read. %d:+%x from %s'%(offset,amount,self))

    def store(self, data):
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

class iter(base):
    '''Basic iterator provider'''
    iterator = iter
    counter = int
    def __init__(self, iterable):
        iterable = iter(iterable)
        self.iterator = iterable
        self.counter = 0

    def seek(self, offset):
        ## Seeking does nothing on an iterator
        pass

    def consume(self, amount):
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(self.counter,amount,self)
        result = ''.join([x for i,x in zip(utils.infiniterange(0), self.iterator)])
        self.counter += amount
        return result

    def store(self, data):
        ## Can't write to an iterator
        pass

import array
class string(base):
    '''Basic string provider'''

    offset = int
    value = str     # this is backed by an array.array type
    def __init__(self, string):
        self.value = array.array('c', string)
    def seek(self, offset):
        self.offset = offset
    def consume(self, amount):
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(self.offset,amount,self)
        res = self.value[self.offset: self.offset+amount].tostring()
        if len(res) != amount:
            raise StopIteration('unable to complete read. %d:+%x from %s'%(self.offset,amount,self))
        self.offset += amount
        return res
    def store(self, data):
        left, right = self.offset, self.offset + len(data)
        self.value[left:right] = array.array('c',data)
        self.offset = right
        return len(data)
    def size(self):
        return len(self.value)

import ctypes
from ctypes import *

## TODO: figure out an elegant way to catch exceptions we might cause
##       by dereferencing any of these pointers

class memory(base):
    '''Basic in-process memory provider using ctypes'''
    address = 0
    def seek(self, offset):
        self.address = offset

    def consume(self, amount):
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(self.address,amount,self)
        res = memory._read(self.address, amount)
        self.address += amount
        return res

    def store(self, data):
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

class localstring(memory):
    '''
    This provider is very fragile. If specified address is out of bounds, then it WILL
    dereference data rampantly..
    '''

    __size = 0
    buffer = None       # keeps a reference to the string
    baseaddress = None  # base address into buffer
    def __init__(self, string):
        super(localstring,self).__init__()

        self.buffer = str(string)
        p = id(self.buffer)
        pbase,psize = p+0x14,p+8    # XXX: hardcoded...
        self.__size = reduce(lambda x,y: x+ord(y), self._read(psize, 4), 0)
        self.baseaddress = pbase

    def size(self):
        return self.__size

    def consume(self, amount):
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(self.address,amount,self)

        p = self.baseaddress+self.address
        if self.address+amount <= self.__size:
            res = memory._read(p, amount)
            self.address += amount
            return res

        amount = self.__size-self.address
        return self.consume(amount)

    def store(self, data):
        p = self.baseaddress+self.address
        if self.address+len(data) <= self.__size:
            res = memory._write(p, data)
            self.address += len(data)
            return res

        data = data[:self.__size-self.address]
        return self.store(data)

class mmap_readonly(localstring):
    '''This is for benchmarking an idea for testing, do not use!!!'''
    def __init__(self, filename, mode='rb'):
        if 'w' in mode:
            raise NotImplementedError('Writing is not implemented for this provider')
        return super(mmap_readonly, self).__init__( __builtins__['file'](filename,mode).read() )

import sys
if sys.platform == 'win32':
    k32 = ctypes.WinDLL('kernel32.dll')
    class WindowsProcessHandle(base):
        '''Given a process handle'''
        address = 0
        handle = None
        def __init__(self, handle):
            self.handle = handle

        def seek(self, offset):
            '''Seek to a particular offset'''
            self.address = offset

        def consume(self, amount):
            assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(self.address,amount,self)

            NumberOfBytesRead = ctypes.c_int()
            res = ctypes.c_char*amount
            Buffer = res()

            res = k32.ReadProcessMemory(self.handle, self.address, Buffer, amount, byref(NumberOfBytesRead))
            if res == 0:
                raise ValueError('Unable to read pid(%x)[%08x:%08x].'% (self.handle, self.address, self.address+amount))

            assert NumberOfBytesRead.value == amount, 'unable to complete %d byte read. only received %d:+%x from %s'%(amount, self.offset,NumberOfBytesRead.value,self)

            self.address += amount
            # XXX: test tihs shit out
            return str(Buffer.raw)

        def store(self, value):
            NumberOfBytesWritten = ctypes.c_int()

            res = ctypes.c_char*len(value)
            Buffer = res()
            Buffer.value = value

            res = k32.WriteProcessMemory(self.handle, self.address, Buffer, len(value), byref(NumberOfBytesWritten)) 
            if res == 0:
                raise ValueError('Unable to write to pid(%x)[%08x:%08x].'% (self.id, self.address, self.address+len(value)))

            self.address += len(value)

            assert NumberOfBytesWritten.value == amount, 'unable to complete %d byte write. only wrote %d:+%x to %s'%(amount, self.offset,NumberOfBytesWritten.value,self)
            return NumberOfBytesWritten.value

    def WindowsProcessId(pid, **attributes):
        handle = k32.OpenProcess(0x30, False, pid)
        return WindowsProcessHandle(handle)
