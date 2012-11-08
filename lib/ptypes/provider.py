import __builtin__
import utils
import os,logging
import array

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
        self.open(filename, mode)

    def open(self, filename, mode='rb'):

        # lie to the user, and always ensure we
        #   read from the file in binary mode

        mode = set(list(mode))
        if 'w' in mode:
            # if file exists and is writeable
            if os.access(filename,6):
                logging.info("-> %s.%s(%s, %s) : opened file for write", self.__module__, type(self).__name__, repr(filename), repr(mode))
                mode = 'r+b'
            # if file doesn't exist, then create it
            else:
                logging.info("-> %s.%s(%s, %s) : creating new file", self.__module__, type(self).__name__, repr(filename), repr(mode))
                mode = 'wb'
            self.file = __builtin__.file(filename, mode)
            return

        # if read isn't specified, then force user to open as read/write
        if 'r' not in mode:
            logging.warn("-> %s.%s(%s, %s): you didn't ask for 'r', which is important. so, i'm fixing it for you by giving you 'r+b' instead", self.__module__, type(self).__name__, repr(filename), repr(mode))
            mode = 'r+b'
            self.file = __builtin__.file(filename, mode)
            return

        # if nothing is specified, then open read/write if allowed
        mode = 'r+b' if os.access(filename, 6) else 'rb'
        self.file = __builtin__.file(filename, mode)

    def seek(self, offset):
        self.file.seek(offset)

    def consume(self, amount):
        offset = self.file.tell()
        assert amount >= 0, 'tried to consume a negative number of bytes. %d:+%s from %s'%(offset,amount,self)
        logging.debug('%s - attempting to consume %x:+%x'%(self.__module__, offset,amount))

        try:
            result = self.file.read(amount)
            if len(result) == amount:
                return result
        except OverflowError:
            pass
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

import array
class string(base):
    '''Basic writeable string provider'''

    offset = int
    value = str     # this is backed by an array.array type
    def __init__(self, string=''):
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
        return super(mmap_readonly, self).__init__( __builtin__.file(filename,mode).read() )

import sys
if sys.platform == 'win32':
    class win32error:
        @staticmethod
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

        @staticmethod
        def getLastErrorString():
            code, string = getLastErrorTuple()
            return string

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

    class WindowsFile(base):
        offset = 0
        def __init__(self, filename, mode='rb'):
            self.offset = 0

            GENERIC_READ, GENERIC_WRITE = 0x40000000,0x80000000
            FILE_SHARE_READ,FILE_SHARE_WRITE = 1,2
            OPEN_EXISTING,OPEN_ALWAYS = 3,4
            FILE_ATTRIBUTE_NORMAL = 0x80
            INVALID_HANDLE_VALUE = -1

#            raise NotImplementedError("These are not the correct permissions")

            cmode = OPEN_EXISTING

            if 'w' in mode:
                smode = FILE_SHARE_READ|FILE_SHARE_WRITE
                amode = GENERIC_READ|GENERIC_WRITE
            else:
                smode = FILE_SHARE_READ
                amode = GENERIC_READ|GENERIC_WRITE

            result = k32.CreateFileA(
                filename, amode, smode, None, cmode,
                FILE_ATTRIBUTE_NORMAL, None
            )
            assert result != INVALID_HANDLE_VALUE, win32error.getLastErrorTuple()
            self.handle = result

        def seek(self, offset):
            '''Seek to a particular offset'''
            distance,resultDistance = ctypes.c_longlong(offset),ctypes.c_longlong(offset)
            FILE_BEGIN = 0
            result = k32.SetFilePointerEx(
                self.handle, distance, ctypes.byref(resultDistance),
                FILE_BEGIN
            )
            assert result != 0, win32error.getLastErrorTuple()
            self.offset = resultDistance.value

        def consume(self, amount):
            resultBuffer = (ctypes.c_char*amount)()
            amount,resultAmount = ctypes.c_ulong(amount),ctypes.c_ulong(amount)
            result = k32.ReadFile(
                self.handle, ctypes.byref(resultBuffer),
                amount, ctypes.byref(resultAmount),
                None
            )
            assert result != 0, win32error.getLastErrorTuple()
            self.offset += resultAmount.value
            return str(resultBuffer.raw)

        def store(self, value):
            buffer = (c_char*len(value))(value)
            resultWritten = ctypes.c_ulong()
            result = k32.WriteFile(
                self.handle, buffer,
                len(value), ctypes.byref(resultWritten),
                None
            )
            assert result != 0, win32error.getLastErrorTuple()
            self.offset += resultWritten.value
            return resultWritten

        def close(self):
            result = k32.CloseHandle(self.handle)
            assert result != 0, win32error.getLastErrorTuple()
            self.handle = None
            return result

class stream(base):
    data = data_ofs = None
    iterator = None
    eof = False

    offset = None

    def __init__(self, source, offset=0):
        self.source = source
        self.data = array.array('c')
        self.data_ofs = self.offset = offset

    def seek(self, offset):
        self.offset = offset
    def _read(self, amount):
        '''how to read raw data from the source'''
        return self.source.read(amount)
    def _write(self, data):
        '''how to write raw data into the source'''
        return self.source.write(data)

    def __getattr__(self, name):
        return getattr(self.source, name)

    ###
    def preread(self, amount):
        '''read some bytes and append it to the cache'''
        if self.eof:
            raise EOFError

        data = self._read(amount)
        self.data.extend( array.array('c', data) )
        if len(data) < amount:    # XXX: this really can't be the only way(?) that an instance
                                  #      of something ~fileobj.read (...) can return for a 
            self.eof = True
        return data

    def remove(self, amount):
        '''removes some number of bytes from the beginning of the cache'''
        assert amount < len(self.data)
        result = self.data[:amount]
        del(self.data[:amount])
        self.data_ofs += amount
        return result
    
    ###
    def consume(self, amount):
        '''read data from the cache'''
        o = self.offset - self.data_ofs
        if o < 0:
            raise ValueError('%s.consume : unable to satisfy requested offset %x (%x,+%x)'% (type(self), self.offset), self.data_ofs, len(self.data))

        # select the requested data
        if (self.eof) or (o + amount <= len(self.data)):
            result = self.data[o:o+amount].tostring()
            self.offset += amount
            return result

        # preread enough bytes so that stuff works
        elif (len(self.data) == 0) or (o <= len(self.data)):
            n = amount - (len(self.data) - o)
            self.preread(n)
            result = self.consume(amount)
            return result

        raise ValueError(repr(self))

    if False:
        def store(self, data):
            '''updates data at an offset in the stream's cache.'''
            # FIXME: this logic _apparently_ hasn't been thought out at all..check notes
            o = self.offset - self.data_ofs
            if o>=0 and o<=len(self.data):
                self.data[o:o+len(data)] = array.array('c', data)
                if o+len(data) >= len(self.data):
                    self.eof = False
                self._write(data)
                return len(data)
            raise ValueError("%s.store : unable to store %x bytes outside of provider's cache size (%x,+%x)"%(type(self), len(data), self.data_ofs, len(self.data)))

    def store(self, data):
        return self._write(data)

    ###
    def __repr__(self):
        return '%s eof=%s base=%x length=+%x] ofs=%x'%( type(self), repr(self.eof), self.data_ofs, len(self.data), self.offset)

    def __getitem__(self, i):
        return self.data[i-self.data_ofs]

    def __getslice__(self, i, j):
        return self.data[i-self.data_ofs:j-self.data_ofs].tostring()

    def hexdump(self, **kwds):
        return utils.hexdump(self.data.tostring(), offset=self.data_ofs, **kwds)

class iter(stream):
    def _read(self, amount):
        return ''.join(x for i,x in zip(xrange(amount), self.source))

    def _write(self, data):
        logging.info('%s._write : tried to write %x bytes to an iterator'%(type(self), len(data)))
        return len(data)

import random as randommodule
class random(base):
    def seek(self, offset):
        randommodule.seed(offset)   # lol

    def consume(self, amount):
        return ''.join(chr(x) for x in randommodule.sample(range(0x100),amount))

    def store(self, data):
        raise OSError('Attempted to write to read-only medium %s'% repr(self))

class proxy(string):
    '''proxy to the source of a specific ptype'''
    def __init__(self, source):
        self.type = source

    def seek(self, offset):
        return self.type.source.seek(offset)

    def consume(self, amount):
        return self.type.source.consume(amount)

    def store(self, data):
        return self.type.source.store(data)

if __name__ == '__main__' and 0:
    import array
    import ptypes,ptypes.provider as provider
#    x = provider.WindowsFile('c:/users/arizvisa/a.out')
#    raise NotImplementedError("Stop being lazy and finish WindowsFile")

    import array
    class fakefile(object):
        d = array.array('L', ((0xdead*x)&0xffffffff for x in range(0x1000)))
        d = array.array('c', d.tostring())
        o = 0
        def seek(self, ofs):
            self.o = ofs
        def read(self, amount):
            r = self.d[self.o:self.o+amount].tostring()
            self.o += amount
            return r
    
    import ptypes
    from ptypes import *
    strm = provider.stream(fakefile())
#    print repr(strm.fileobj.d)
#    print strm.buffer_data
    
#    print repr(fakefile().d[0:0x30].tostring())
    x = dyn.array(pint.uint32_t, 3)(source=strm)
    x = x.l
#    print repr(x.l.serialize())

    print repr(pint.uint32_t(offset=0,source=strm).l.serialize() + \
     pint.uint32_t(offset=4,source=strm).l.serialize() + \
     pint.uint32_t(offset=8,source=strm).l.serialize() + \
     pint.uint32_t(offset=0xc,source=strm).l.serialize() + \
     pint.uint32_t(offset=0x10,source=strm).l.serialize() + \
     pint.uint32_t(offset=0x14,source=strm).l.serialize() + \
     pint.uint32_t(offset=0x18,source=strm).l.serialize() )

if __name__ == '__main__':
    # test cases are found at next instance of '__main__'
    import logging
    logging.root=logging.RootLogger(logging.DEBUG)

    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)

            except Success:
                print '%s: Success'% name
                return True

            except Failure,e:
                pass

            print '%s: Failure'% name
            return False

        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

    a = provider.virtual()
    a.available = [0,6]
    a.data = {0:'hello',6:'world'}
    print a.available
    print a.data

    @TestCase
    def test_first():
        if a._find(0) == 0:
            raise Success

    @TestCase
    def test_first_2():
        if a._find(3) == 0:
            raise Success

    @TestCase
    def test_first_3():
        if a._find(4) == 0:
            raise Success

    @TestCase
    def test_hole():
        if a._find(5) == -1:
            raise Success
    
    @TestCase
    def test_second():
        if a.available[a._find(6)] == 6:
            raise Success
    @TestCase
    def test_second_2():
        if a.available[a._find(9)] == 6:
            raise Success

    @TestCase
    def test_second_3():
        if a.available[a._find(10)] == 6:
            raise Success

    @TestCase
    def test_less():
        if a.find(-1) == -1:
            raise Success
    
    @TestCase
    def test_tail():
        if a.find(11) == -1:
            raise Success

    @TestCase
    def test_flatten():
        from array import array
        s = lambda x:array('c',x)
        a = provider.virtual()
        a.available = [0,5]
        a.data = {0:s('hello'),5:s('world')}
        a.flatten(0,5)
        if len(a.data[0]) == 10:
            raise Success

    @TestCase
    def test_consume():
        s = lambda x:array.array('c',x)

        global a
        a = provider.virtual()
        a.available = [0, 5, 10, 15, 20]
        a.data = {0:s('hello'),5:s('world'),10:s('55555'),15:s('66666'),20:s('77777')}
        a.seek(17)
        if a.consume(5) == '66677':
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

