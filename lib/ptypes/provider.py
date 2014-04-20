import __builtin__,array,exceptions,sys,itertools
import config,utils,error
Config = config.defaults

class base(object):
    '''Base provider class. Intended to be Inherited from'''
    def seek(self, offset):
        '''Seek to a particular offset'''
        raise error.ImplementationError(self, 'seek', message='Developer forgot to overload this method')
    def consume(self, amount):
        '''Read some number of bytes. If the first byte wasn't able to be consumed, raise an exception'''
        raise error.ImplementationError(self, 'seek', message='Developer forgot to overload this method')
    def store(self, data):
        '''Write some number of bytes. If nothing was able to be written, raise an exception.'''
        raise error.ImplementationError(self, 'seek', message='Developer forgot to overload this method')

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
        raise error.UserError(self, 'store', message='Attempted to write to read-only medium %s'% repr(self))

## core providers
class string(base):
    '''Basic writeable string provider'''
    offset = int
    value = str     # this is backed by an array.array type
    def __init__(self, string=''):
        self.value = array.array('c', string)
    def seek(self, offset):
        self.offset = offset

    @utils.mapexception(any=error.ProviderError,ignored=(error.ConsumeError,error.UserError))
    def consume(self, amount):
        if amount < 0:
            raise error.UserError(self, 'consume', message='tried to consume a negative number of bytes. %d:+%s from %s'%(self.offset,amount,self))
        res = self.value[self.offset: self.offset+amount].tostring()
        if res == '' and amount > 0:
            raise error.ConsumeError(self,self.offset,amount,len(res))
        if len(res) == amount:
            self.offset += amount
        return res

    @utils.mapexception(any=error.ProviderError,ignored=(error.StoreError,))
    def store(self, data):
        try:
            left, right = self.offset, self.offset + len(data)
            self.value[left:right] = array.array('c',data)
            self.offset = right
            return len(data)
        except Exception,e:
            raise error.StoreError(self,self.offset,len(data),exception=e)
        raise error.ProviderError

    @utils.mapexception(any=error.ProviderError)
    def size(self):
        return len(self.value)

class proxy(string):
    '''proxy to the source of a specific ptype. snapshots the instance offset and length at time of construction.'''
    def __init__(self, source):
        self.type = source
        self.offset = 0
        self.baseoffset = source.getoffset()
        self.size = source.blocksize()

    def seek(self, offset):
        if offset >= 0 and offset <= self.size:
            ofs = self.offset
            self.offset = offset
            return ofs
        raise error.UserError(self.type, 'seek', message='Requested offset 0x%x is outside bounds (0,%x)'% (offset, self.size))

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        bo,ofs = self.baseoffset,self.offset
        left = ofs
        right = left+amount

        if left >= 0 and right <= self.size:
            self.type.source.seek(bo+ofs)
            result = self.type.source.consume(amount)
            self.offset += amount
            return result
        raise error.ConsumeError(self, ofs, amount, amount=right-self.size)

    def consume(self, amount):
        bo,ofs = self.baseoffset,self.offset
        left = ofs
        right = left+amount

        if right < 0 or left > self.size or left < 0:
            raise error.ConsumeError(self, ofs, amount, amount=right-self.size)

        right = min(right, self.size)

        self.type.source.seek(bo+ofs)
        result = self.type.source.consume(right-left)
        self.offset += amount
        return result

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        bo,ofs = self.baseoffset,self.offset
        left = ofs
        right = left+len(data)
        if left >= 0 and right <= self.size:
            self.type.source.seek(bo+ofs)
            self.offset += len(data)
            return self.type.source.store(data)
        raise error.StoreError(self, ofs,len(data), 0)

    def __repr__(self):
        return '%s -> %x -> %s'% (super(proxy, self).__repr__(), self.baseoffset, self.type.name())

import random as _random
class random(base):
    @utils.mapexception(any=error.ProviderError)
    def seek(self, offset):
        _random.seed(offset)   # lol

    @utils.mapexception(any=error.ProviderError)
    def consume(self, amount):
        return ''.join(chr(_random.randint(0,255)) for x in xrange(amount))

    @utils.mapexception(any=error.ProviderError)
    def store(self, data):
        Config.log.info('random.store : Tried to write %x bytes to a read-only medium'%(type(self), len(data)))
        return len(data)

## useful providers
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

    @utils.mapexception(any=error.ProviderError)
    def remove(self, amount):
        '''removes some number of bytes from the beginning of the cache'''
        assert amount < len(self.data)
        result = self.data[:amount]
        del(self.data[:amount])
        self.data_ofs += amount
        return result
    
    ###
    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''read data from the cache'''
        o = self.offset - self.data_ofs
        if o < 0:
            raise ValueError('%s.consume : Unable to seek to offset %x (%x,+%x)'% (type(self).__name__, self.offset, self.data_ofs, len(self.data)))

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

        raise error.ConsumeError(self, self.offset,amount)

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
            raise ValueError("%s.store : Unable to store %x bytes outside of provider's cache size (%x,+%x)"%(type(self), len(data), self.data_ofs, len(self.data)))

    @utils.mapexception(any=error.ProviderError)
    def store(self, data):
        return self._write(data)

    def __repr__(self):
        return '%s[eof=%s base=%x length=+%x] ofs=%x'%( type(self), repr(self.eof), self.data_ofs, len(self.data), self.offset)

    def __getitem__(self, i):
        return self.data[i-self.data_ofs]

    def __getslice__(self, i, j):
        return self.data[i-self.data_ofs:j-self.data_ofs].tostring()

    def hexdump(self, **kwds):
        return utils.hexdump(self.data.tostring(), offset=self.data_ofs, **kwds)

class iter(stream):
    def _read(self, amount):
        return ''.join(itertools.islice(self.source, amount))

    def _write(self, data):
        Config.log.info('iter._write : Tried to write %x bytes to an iterator'%(len(data)))
        return len(data)

class filebase(base):
    '''Basic file provider'''
    file = None
    def __init__(self, filename, mode='r'):
        self.open(filename, mode)

    @utils.mapexception(any=error.ProviderError)
    def open(self, filename, mode='r'):
        raise error.ImplementationError(self, 'open', message='Developer forgot to overload this method')

    @utils.mapexception(any=error.ProviderError)
    def seek(self, offset):
        self.file.seek(offset)

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        offset = self.file.tell()
        if amount < 0:
            raise error.UserError(self, 'consume', message='Tried to consume a negative number of bytes. %d:+%s from %s'%(offset,amount,self))
        Config.log.debug('%s.consume : Attempting to consume %x:+%x'%(type(self).__name__, offset, amount))

        try:
            result = self.file.read(amount)
        except OverflowError, e:
            self.file.seek(offset)
            raise error.ConsumeError(self,offset,amount, len(result), exception=e)

        if result == '' and amount > 0:
            raise error.ConsumeError(self,offset,amount, len(result))

        if len(result) != amount:
            self.file.seek(offset)
        return result

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        ofs = self.file.tell()
        try:
            return self.file.write(data)
        except Exception, e:
            self.file.seek(offset)
            raise error.StoreError(self, ofs,len(data), exception=e)

    @utils.mapexception(any=error.ProviderError)
    def close(self):
        return self.file.close()

    @utils.mapexception(any=error.ProviderError)
    def size(self):
        old = self.file.tell()
        self.file.seek(0, 2)
        result = self.file.tell()
        self.file.seek(old, 0)
        return result

    def __repr__(self):
        return '%s -> %s'% (super(filebase, self).__repr__(), repr(self.file))

    def __del__(self):
        self.close()

## optional providers
import os
try:
    raise ImportError, "Skipping posix version of the `file` provider"
    import os

    class file(filebase):
        '''Basic posix file provider'''
        @utils.mapexception(any=error.ProviderError)
        def open(self, filename, mode='rw', perms=0644):
            mode = ''.join(sorted(list(x.lower() for x in mode)))
            flags = (os.O_SHLOCK|os.O_FSYNC) if 'posix' in sys.modules else 0

            # this is always assumed
            if mode.startswith('b'):
                mode = mode[1:]

            # setup access
            flags = 0
            if 'r' in mode:
                flags |= os.O_RDONLY
            if 'w' in mode:
                flags |= os.O_WRONLY

            if (flags & os.O_RDONLY) and (flags & os.O_WRONLY):
                flags ^= os.O_RDONLY|os.O_WRONLY
                flags |= os.O_RDWR

            access = 'read/write' if (flags&os.O_RDWR) else 'write' if (flags&os.O_WRONLY) else 'read-only' if flags & os.O_RDONLY else 'unknown'

            if os.access(filename,6):
                Config.log.info("%s(%s, %s) : Opening file for %s", type(self).__name__, repr(filename), repr(mode), access)
            else:
                flags |= os.O_CREAT|os.O_TRUNC
                Config.log.info("%s(%s, %s) : Creating new file for %s", type(self).__name__, repr(filename), repr(mode), access)

            # mode defaults to rw-rw-r--
            self.fd = os.open(filename, flags, perms)
            self.file = os.fdopen(self.fd)

    @utils.mapexception(any=error.ProviderError)
    def close(self):
        os.close(self.fd)
        return super(file,self).close()

except ImportError:
    Config.log.info("__module__ : Unable to import 'os' module. Using non-posix version of `file` provider.")

    class file(filebase):
        '''Basic file provider'''
        @utils.mapexception(any=error.ProviderError)
        def open(self, filename, mode='rw'):
            usermode = list(x.lower() for x in mode)

            # this is always assumed
            if 'b' in usermode:
                usermode.remove('b')

            if '+' in usermode:
                access = 'r+b'
            elif 'r' in usermode and 'w' in usermode:
                access = 'r+b'
            elif 'w' in usermode:
                access = 'wb'
            elif 'r' in usermode:
                access = 'rb'

            straccess = 'read/write' if access =='r+b' else 'write' if access == 'wb' else 'read-only' if access == 'rb' else 'unknown'

            if os.access(filename,6):
                Config.log.info("%s(%s, %s) : Opening file for %s", type(self).__name__, repr(filename), repr(access), straccess)
            else:
                access = 'w+b'
                Config.log.info("%s(%s, %s) : Creating new file for %s", type(self).__name__, repr(filename), repr(access), straccess)

            self.file = __builtin__.open(filename, access, 0)
    

try:
    import tempfile
    class filecopy(filebase):
        """Makes a temporary copy of a file"""

        @utils.mapexception(any=error.ProviderError)
        def open(self, filename, mode):
            input = open(filename, 'rb')
            input.seek(0)

            if input:
                output = tempfile.TemporaryFile()
                for data in input:
                    output.write(data)
                output.seek(0)
                self.file = output

            input.close()
            return output

        def save(self, filename):
            '''make a copy of file and save it to filename'''
            ofs = self.file.tell()
            
            output = file(filename, 'wb')
            for data in self.file:
                output.write(data)
            output.close()

            self.file.seek(ofs)

except ImportError:
    Config.log.warning("__module__ : Unable to import 'tempfile' module. Failed to load `filecopy` provider.")

try:
    import ctypes

    ## TODO: figure out an elegant way to catch exceptions we might cause
    ##       by dereferencing any of these pointers on both windows (veh) and posix (signals)

    class memory(base):
        '''Basic in-process memory provider using ctypes'''
        address = 0
        def seek(self, offset):
            self.address = offset

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            if amount < 0:
                raise error.UserError(self, 'consume', message='tried to consume a negative number of bytes. %d:+%s from %s'%(self.address,amount,self))
            res = memory._read(self.address, amount)
            if len(res) == 0 and amount > 0:
                raise error.ConsumeError(self,offset,amount,len(res))
            if len(res) == amount:
                self.address += amount
            return res

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, data):
            res = memory._write(self.address, data)
            if res != len(data):
                raise error.StoreError(self,self.address,len(data),written=res)
            self.address += len(data)
            return res

        @staticmethod
        def _read(address, length):
            blockpointer = ctypes.POINTER(ctypes.c_char*length)
            v = ctypes.c_void_p(address)
            p = ctypes.cast(v, blockpointer)
            return ''.join(p.contents)

        @staticmethod
        def _write(address, value):
            length = len(value)
            blockpointer = ctypes.POINTER(ctypes.c_char*length)
            v = ctypes.c_void_p(address)
            p = ctypes.cast(v, blockpointer)
            for i,c in zip(xrange(length), str(value)):
                p.contents[i] = c
            return i

except ImportError:
    Config.log.warning("__module__ : Unable to import 'ctypes' module. Failed to load `memory` provider.")

try:
    import ctypes
    try:
        k32 = ctypes.WinDLL('kernel32.dll')
    except Exception,m:
        raise OSError,m

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

    class WindowsProcessHandle(base):
        '''Given a process handle'''
        address = 0
        handle = None
        def __init__(self, handle):
            self.handle = handle

        def seek(self, offset):
            '''Seek to a particular offset'''
            self.address = offset

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            if amount < 0:
                raise error.UserError(self, 'consume', message='tried to consume a negative number of bytes. %d:+%s from %s'%(self.address,amount,self))

            NumberOfBytesRead = ctypes.c_int()
            res = ctypes.c_char*amount
            Buffer = res()

            # FIXME: instead of failing on an incomplete read, perform a partial read
            res = k32.ReadProcessMemory(self.handle, self.address, Buffer, amount, ctypes.byref(NumberOfBytesRead))
            if (res == 0) or (NumberOfBytesRead.value != amount):
                e = ValueError('Unable to read pid(%x)[%08x:%08x].'% (self.handle, self.address, self.address+amount))
                raise error.ConsumeError(self, self.address,amount, NumberOfBytesRead.value)

            self.address += amount
            # XXX: test this shit out
            return str(Buffer.raw)

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, value):
            NumberOfBytesWritten = ctypes.c_int()

            res = ctypes.c_char*len(value)
            Buffer = res()
            Buffer.value = value

            res = k32.WriteProcessMemory(self.handle, self.address, Buffer, len(value), ctypes.byref(NumberOfBytesWritten)) 
            if (res == 0) or (NumberOfBytesWritten.value != len(value)):
                e = OSError('Unable to write to pid(%x)[%08x:%08x].'% (self.id, self.address, self.address+len(value)))
                raise error.StoreError(self, self.address,len(value), written=NumberOfBytesWritten.value, exception=e)

            self.address += len(value)
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
            if result == INVALID_HANDLE_VALUE:
                raise OSError(win32error.getLastErrorTuple())
            self.handle = result

        @utils.mapexception(any=error.ProviderError)
        def seek(self, offset):
            '''Seek to a particular offset'''
            distance,resultDistance = ctypes.c_longlong(offset),ctypes.c_longlong(offset)
            FILE_BEGIN = 0
            result = k32.SetFilePointerEx(
                self.handle, distance, ctypes.byref(resultDistance),
                FILE_BEGIN
            )
            if result == 0:
                raise OSError(win32error.getLastErrorTuple())
            self.offset = resultDistance.value

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            resultBuffer = (ctypes.c_char*amount)()
            amount,resultAmount = ctypes.c_ulong(amount),ctypes.c_ulong(amount)
            result = k32.ReadFile(
                self.handle, ctypes.byref(resultBuffer),
                amount, ctypes.byref(resultAmount),
                None
            )
            if (result == 0) or (resultAmount.value == 0 and amount > 0):
                e = OSError(win32error.getLastErrorTuple())
                raise error.ConsumeError(self,self.offset,amount,resultAmount.value, exception=e)

            if resultAmount.value == amount:
                self.offset += resultAmount.value
            return str(resultBuffer.raw)

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, value):
            buffer = (c_char*len(value))(value)
            resultWritten = ctypes.c_ulong()
            result = k32.WriteFile(
                self.handle, buffer,
                len(value), ctypes.byref(resultWritten),
                None
            )
            if (result == 0) or (resultWritten.value != len(value)):
                e = OSError(win32error.getLastErrorTuple())
                raise error.StoreError(self, self.offset,len(value),resultWritten.value,exception=e)
            self.offset += resultWritten.value
            return resultWritten

        @utils.mapexception(any=error.ProviderError)
        def close(self):
            result = k32.CloseHandle(self.handle)
            if (result == 0):
                raise OSError(win32error.getLastErrorTuple())
            self.handle = None
            return result

    Config.log.info("__module__ : Successfully loaded `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers.")
except ImportError:
    Config.log.warning("__module__ : Unable to import 'ctypes' module. Failed to load `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers.")

except OSError, m:
    Config.log.warning("__module__ : Unable to load 'kernel32.dll' (%s). Failed to load `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers."% m)

try:
    import _idaapi
    class Ida(object):
        '''Ida singleton'''
        offset = 0xffffffff

        def __init__(self):
            raise UserWarning("%s.%s is a static object and contains only staticmethods."%(self.__module__,self.__class__.__name__))

        @classmethod
        def seek(cls, offset):
            cls.offset = offset

        @classmethod
        def consume(cls, amount):
            result = _idaapi.get_many_bytes(cls.offset, amount)
            cls.offset += len(result)
            return result

        @classmethod
        def store(cls, data):
            #_idaapi.put_many_bytes(cls.offset, data)
            _idaapi.patch_many_bytes(cls.offset, data)
            cls.offset += len(data)
            return len(data)

    Config.log.warning("__module__ : Successfully loaded `Ida` provider.")
except ImportError:
    Config.log.info("__module__ : Unable to import '_idaapi' module (not running IDA?). Failed to load `Ida` provider.")

try:
    import _PyDbgEng
    class PyDbgEng(object):
        offset = 0
        def __init__(self, client=None):
            self.client = client

        @classmethod
        def connect(cls, remote):
            if remote is None:
                result = _PyDbgEng.Create()
            elif type(remote) is tuple:
                host,port = client
                result = _PyDbgEng.Connect('tcp:port={},server={}'.format(port,host))
            elif type(remote) is dict:
                result = _PyDbgEng.Connect('tcp:port={port},server={host}'.format(**client))
            elif type(remote) is str:
                result = _PyDbgEng.Connect(client)
            return cls(result)
        @classmethod
        def connectprocessserver(cls, remote):
            result = _PyDbgEng.ConnectProcessServer(remoteOptions=remote)
            return cls(result)
        def connectkernel(self, remote):
            if remote is None:
                result = _PyDbgEng.AttachKernel(flags=_PyDbgEng.ATTACH_LOCAL_KERNEL)
            else:
                result = _PyDbgEng.AttachKernel(flags=0, connectOptions=remote)
            return cls(result)

        def seek(self, offset):
            '''Seek to a particular offset'''
            self.offset = offset

        def consume(self, amount):
            '''Read some number of bytes'''
            try:
                result = str( self.client.DataSpaces.Virtual.Read(self.offset, amount) )
            except RuntimeError, e:
                raise StopIteration('Unable to read 0x%x bytes from address %x'% (amount, self.offset))
            return result
            
        def store(self, data):
            '''Write some number of bytes'''
            return self.client.DataSpaces.Virtual.Write(self.offset, data)
    
    Config.log.warning("__module__ : Successfully loaded `PyDbgEng` provider.")
except ImportError:
    Config.log.info("__module__ : Unable to import '_PyDbgEng' module. Failed to load `PyDbgEng` provider.")

try:
    import pykd as _pykd
    class Pykd(base):
        def __init__(self):
            self.addr = 0

        def seek(self, offset):
            # FIXME: check to see if we're at an invalid address
            self.addr = offset

        def consume(self, amount):
            return ''.join(map(chr,_pykd.loadBytes(self.addr, amount)))

        def store(self, data):
            raise error.StoreError(self, self.addr, len(data), message="Pykd doesn't allow you to write to memory.")
            return len(data)

    Config.log.warning("__module__ : Successfully loaded `Pykd` provider.")
except ImportError:
    Config.log.info("__module__ : Unable to import 'pykd' module. Failed to load `Pykd` provider.")

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
    import config,logging
    config.defaults.log.setLevel(logging.DEBUG)

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
    import os,random
    from __builtin__ import *
    import provider
    import tempfile

    class pythondevelopersarestupid(object):
        def __enter__(self, *args):
            name = tempfile.mktemp()
            self.file = file(name, 'w+b')
            return self.file
        def __exit__(self, *args):
            self.file.close()
            filename = self.file.name
            del(self.file)
            os.unlink(filename)

    import time
    @TestCase
    def test_file_readonly():
        data = 'A'*512
        with pythondevelopersarestupid() as f:
            f.write(data)
            f.seek(0)

            z = provider.file(f.name, mode='r')
            a = z.consume(len(data))
            assert a == data

            try:
                z.store('nope')
            except:
                raise Success
            finally:
                z.close()
        raise Failure

    @TestCase
    def test_file_writeonly():
        data = 'A'*512
        with pythondevelopersarestupid() as f:
            f.write(data)
            f.seek(0)

            z = provider.file(f.name, mode='w')
            z.store(data)
            z.seek(0)
            try:
                a = z.consume(len(data))
                assert a == data
            except:
                raise Success
            finally:
                z.close()
        return

    @TestCase
    def test_file_readwrite():
        data = 'A'*512
        with pythondevelopersarestupid() as f:
            f.write(data)
            f.seek(0)

            z = provider.file(f.name, mode='rw')
            z.store(data)

            z.seek(0)
            a = z.consume(len(data))
            assert a == data

            z.close()
        raise Success

    @TestCase
    def test_filecopy_read():
        pass
    @TestCase
    def test_filecopy_write():
        pass
    @TestCase
    def test_filecopy_readwrite():
        pass

    @TestCase
    def test_memory_read():
        pass
    @TestCase
    def test_memory_write():
        pass
    @TestCase
    def test_memory_readwrite():
        pass

    @TestCase
    def test_random_read():
        pass
    @TestCase
    def test_random_write():
        pass
    @TestCase
    def test_random_readwrite():
        pass

    @TestCase
    def test_proxy_read():
        pass
    @TestCase
    def test_proxy_write():
        pass
    @TestCase
    def test_proxy_readwrite():
        pass

    #@TestCase
    def test_windows_remote_consume():
        import multiprocessing,os,ctypes
        q = multiprocessing.Queue()
        string = "hola mundo"

        def stringalloc(string):
            v = ctypes.c_char*len(string)
            x = v(*string)
            return x,ctypes.addressof(x)

        def stringspin(q,string):
            _,x = stringalloc(string)
            q.put(x)
            while True:
                pass

        p = multiprocessing.Process(target=stringspin, args=(q,string,))
        p.start()
        address = q.get()
        print hex(address)

        src = provider.WindowsProcessId(p.pid)
        src.seek(address)
        data = src.consume(len(string))
        p.terminate()
        if data == string:
            raise Success
        
    @TestCase
    def test_windows_remote_store():
        pass

if __name__ == '__main__' and 0:
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

