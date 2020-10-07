"""
Various providers that a ptype can be sourced from.

Each ptype instance can read and write it's data to particular provider type. A
provider type is responsible for keeping track of the current offset into some
byte-seekable data source and exposing a few general methods for reading and
writing to the source.

The interface for a provider must look like the following:

    class interface(object):
        def seek(self, offset): return last-offset-before
        def consume(self, amount): return string-containing-data
        def store(self, stringdata): return number-of-bytes-written

It is up to the implementor to maintain the current offset, and update them when
the .store or .consume methods are called.

Example usage:
# define a type
    type = ...

# set global source
    import ptypes
    ptypes.setsource( ptypes.provider.name(...) )

    instance = type()
    print( repr(instance) )

# set instance's source during construction
    import ptypes.provider
    instance = type(source=ptypes.provider.name(...))
    print( repr(instance) )

# set instance's source after construction
    import ptypes.provider
    instance = type()
    ...
    instance.source = ptypes.provider.name(...)
    instance.load()
    print( repr(instance) )

# set instance's source during load
    instance = type()
    instance.load(source=ptypes.provider.name(...))
    print( repr(instance) )

# set instances's source during commit
    instance = type()
    instance.commit(source=ptypes.provider.name(...))
    print( repr(instance) )
"""
import six
import sys, os
import itertools, operator, functools
import importlib, array, random as _random
from six.moves import builtins

from . import config, utils, error
Config = config.defaults
Log = Config.log.getChild('provider')

class base(object):
    '''
    Base provider class.

    Intended to be used as a template for a provider implementation.
    '''
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        raise error.ImplementationError(self, 'seek', message='User forgot to implement this method')
    def consume(self, amount):
        '''Read some number of bytes from the current offset. If the first byte wasn't able to be consumed, raise an exception.'''
        raise error.ImplementationError(self, 'consume', message='User forgot to implement this method')
    def store(self, data):
        '''Write some number of bytes to the current offset. If nothing was able to be written, raise an exception.'''
        raise error.ImplementationError(self, 'store', message='User forgot to implement this method')

class remote(base):
    '''
    Base remote provider class.

    Intended to be inherited from when defining a remote provider that needs to
    cache any data that is being read or written. To use this, simply inherit
    from this class and implement the remote.read(), and the remote.send() methods.

    Once the provider is instantiated, the user may call the .send() method to
    submit any committed data, or the .reset() method when it is necessary to
    reset the data that was cached.
    '''
    __cons__ = staticmethod(functools.partial(array.array, 'B'))

    def __init__(self):
        """This initializes any attributes required by a remote provider.

        Supermethod initializes the default buffer and other required attributes.
        This is required to be implemented and called by a child implementation.
        """
        self.offset = 0

        # This is the buffer that gets committed to before sending
        self.__buffer__ = self.__cons__()

        # This is a cache that remote data will be read into as a
        # ptype instance needs it. We make a copy to avoid re-construction.
        self.__cache__ = self.__buffer__[:]

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res

    def consume(self, amount):
        '''Read some number of bytes from the current offset. If the first byte wasn't able to be consumed, raise an exception.'''
        cache, left, right = self.__cache__, self.offset, self.offset + amount

        # If we have enough data in our cache, then we can simply return it.
        if len(cache) >= right:
            self.offset, buffer = right, cache[left : right]
            return buffer.tostring() if sys.version_info.major < 3 else buffer.tobytes()
        # Otherwise, we need to read some more data from our class.
        data = self.read(right - len(cache))
        cache.fromstring(data) if sys.version_info.major < 3 else cache.frombytes(data)

        # If we still don't have enough data, then raise an exception.
        if len(cache) < right:
            raise error.ConsumeError(self, self.offset, amount)

        # Now we can return the data from our cache that we just populated.
        self.offset, buffer = right, cache[left : right]
        return buffer.tostring() if sys.version_info.major < 3 else buffer.tobytes()

    def store(self, data):
        '''Write some number of bytes to the current offset. If nothing was able to be written, raise an exception.'''
        buffer, data = self.__buffer__, self.__cons__(data)

        # If our current offset is past the length of our buffer, then pad it
        # to the size that we'll need.
        if self.offset > len(buffer):
            padding = b'\0' * (self.offset - len(self.__buffer__))
            buffer.fromstring(padding) if sys.version_info.major < 3 else buffer.frombytes(padding)

        # Update the offset and the buffer with the data the caller provided.
        self.offset, buffer[self.offset:] = self.offset + len(data), data
        return len(data)

    def reset(self):
        '''Reset the reader for the remote provider.'''
        self.offset = 0

        # Delete all elements in the cache to avoid re-construction
        del(self.__cache__[:])

    def send(self):
        """Submit the currently committed data to the remote provider.

        Supermethod returns a buffer containing the data that is to be sent.
        This is required to be implemented and called by a child implementation.
        """

        # We make an empty copy of .__buffer__ here to avoid reconstructing
        # the buffer instance.
        buffer, self.__buffer__ = self.__buffer__, self.__buffer__[0 : 0]
        return buffer.tostring() if sys.version_info.major < 3 else buffer.tobytes()

    def read(self, amount):
        """Read some number of bytes from the provider and return it.

        This is required to be implemented and called by a child implementation.
        """
        raise error.ImplementationError(self, 'read', message='User forgot to implement this method')

class memorybase(base):
    '''Base provider class for reading/writing with a memory-type backing. Intended to be inherited from.'''

class debuggerbase(memorybase):
    '''Base provider class for reading/writing with a debugger-type backing. Intended to be inherited from.'''

    def expr(self, string):
        raise error.ImplementationError(self, 'expr', message='User forgot to implement this method')

class bounded(base):
    '''Base provider class for describing a backing that has boundaries of some kind.'''

    def size(self):
        raise error.ImplementationError(self, 'size', message='User forgot to implement this method')

## core providers
class empty(base):
    '''Empty provider. Returns only zeroes.'''
    offset = 0
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        offset = 0
        return 0
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        return b'\0' * amount
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        Log.info("{:s}.store : Tried to write {:d} bytes to a read-only medium.".format(type(self).__name__, len(data)))
        return len(data)

class proxy(bounded):
    """Provider that will read or write it's data to/from the specified ptype.

    If autoload or autocommit is specified during construction, the object will sync the proxy with it's source before performing any operations requested of the proxied-type.
    """
    def __init__(self, source, **kwds):
        """Instantiate the provider using ``source`` as it's backing ptype.

        autocommit -- A dict that will be passed to the source type's .commit method when data is stored to the provider.
        autoload -- A dict that will be passed to the source type's .load method when data is read from the provider.
        """

        self.instance = source
        self.offset = 0

        valid = {'autocommit', 'autoload'}
        res = six.viewkeys(kwds) - valid
        if res - valid:
            raise error.UserError(self, '__init__', message="Invalid keyword(s) specified. Expected ({!r}) : {!r}".format(valid, tuple(res)))

        self.autoload = kwds.get('autoload', None)
        self.autocommit = kwds.get('autocommit', None)

    def size(self):
        '''Return the size of the object.'''
        res = self.instance
        return res.size()

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        left, right = self.offset, self.offset + amount

        buf = self.instance.serialize() if self.autoload is None else self.instance.load(**self.autoload).serialize()
#        if self.autoload is not None:
#            Log.debug("{:s}.consume : Autoloading : {:s} : {!r}".format(type(self).__name__, self.instance.instance(), self.instance.source))

        if amount >= 0 and left >= 0 and right <= len(buf):
            result = buf[left : right]
            self.offset += amount
            return result

        raise error.ConsumeError(self, left, amount, amount=right - len(buf))

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        left, right = self.offset, self.offset + len(data)

        # if trying to store within the bounds of self.instance..
        if left >= 0 and right <= self.instance.blocksize():
            from . import ptype, pbinary
            if isinstance(self.instance, pbinary.partial):
                self.__write_partial(self.instance, self.offset, data)

            elif isinstance(self.instance, ptype.type):
                self.__write_object(self.instance, self.offset, data)

            elif isinstance(self.instance, ptype.container):
                self.__write_range(self.instance, self.offset, data)

            else:
                raise NotImplementedError(self.instance.__class__)

            self.offset += len(data)
            self.instance if self.autocommit is None else self.instance.commit(**self.autocommit)
#            if self.autocommit is not None:
#                Log.debug("{:s}.store : Autocommitting : {:s} : {!r}".format(type(self).__name__, self.instance.instance(), self.instance.source))
            return len(data)

        # otherwise, check if nothing is being written
        if left == right:
            return len(data)

        raise error.StoreError(self, left, len(data), 0)

    @classmethod
    def __write_partial(cls, object, offset, data):
        left, right = offset, offset + len(data)
        size, value = object.blocksize(), object.serialize()
        padding = utils.padding.fill(size - min(size, len(data)), object.padding)
        object.load(offset=0, source=string(value[:left] + data + padding + value[right:]))
        return sum({data, padding})

    @classmethod
    def __write_object(cls, object, offset, data):
        left, right = offset, offset + len(data)
        res = object.blocksize()
        object.value = object.value[:left] + data + object.value[right:]
        return res

    @classmethod
    def __write_range(cls, object, offset, data):
        result, left, right = 0, offset, offset + len(data)
        sl = list(cls.collect(object, left, right))

        # fix beginning element
        n = sl.pop(0)
        source, bs, l = n.serialize(), n.blocksize(), left - n.getoffset()
        s = bs - l
        _ = source[:l] + data[:s] + source[l + s:]
        n.load(offset=0, source=string(_))
        data = data[s:]
        result += s    # sum the blocksize

        # fix elements in the middle
        while len(sl) > 1:
            n = sl.pop(0)
            source, bs = n.serialize(), n.blocksize()
            _ = data[:bs] + source[len(data[:bs]):]
            n.load(offset=0, source=string(_))
            data = data[bs:]
            result += bs    # sum the blocksize

        # fix last element
        if len(sl) > 0:
            n = sl.pop(0)
            source, bs = n.serialize(), n.blocksize()
            _ = data[:bs] + source[len(data[:bs]):]
            padding = utils.padding.fill(bs - min(bs, len(_)), n.padding)
            n.load(offset=0, source=string(_ + padding))
            data = data[bs:]
            result += len(data[:bs])    # sum the final blocksize

        # check to see if there's any data left
        if len(data) > 0:
            Log.warn("{:s} : __write_range : {:d} bytes left-over from trying to write to {:d} bytes.".format(cls.__name__, len(data), result))

        # return the aggregated total
        return result

    @classmethod
    def collect(cls, object, left, right):
        '''an iterator that returns all the leaf nodes of ``object`` from field offset ``left`` to ``right``.'''
        # figure out which objects to start and stop at
        lobj = object.field(left, recurse=True) if left >= 0 else None
        robj = object.field(right, recurse=True) if right < object.blocksize() else None

        # return all leaf objects with a .value that's not a pbinary
        from . import ptype, pbinary
        leaves = object.traverse(lambda s: s.value, filter=lambda s: isinstance(s, ptype.type) or isinstance(s, pbinary.partial))

        # consume everything up to lobj
        list(itertools.takewhile(lambda n: n is not lobj, leaves))

        # now yield all elements from left..right
        if lobj is not None: yield lobj
        for res in itertools.takewhile(lambda n: n is not robj, leaves):
            yield res
        if robj is not None: yield robj

    def __repr__(self):
        '''x.__repr__() <=> repr(x)'''
        return "{:s} -> {:s}".format(super(proxy, self).__repr__(), self.instance.instance())

class bytes(bounded):
    '''Basic writeable bytes provider.'''
    offset = int
    data = bytes     # this is backed by an bytearray type

    @property
    def value(self):
        return self.data

    @value.setter
    def value(self, value):
        self.data = value

    def __init__(self, string=b''):
        res = bytearray(string) if isinstance(string, builtins.bytes) else bytearray(string, sys.getdefaultencoding())
        self.offset = 0
        self.data = res

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError, error.UserError))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        if amount < 0:
            raise error.UserError(self, 'consume', message="tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(self.offset, amount, self))
        if amount == 0:
            return b''
        if self.offset >= len(self.data):
            raise error.ConsumeError(self, self.offset, amount)

        minimum = min((self.offset + amount, len(self.data)))
        res = self.data[self.offset : minimum]
        if res == b'' and amount > 0:
            raise error.ConsumeError(self, self.offset, amount, len(res))
        if len(res) == amount:
            self.offset += amount
        return builtins.bytes(res)

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError, ))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        try:
            left, right = self.offset, self.offset + len(data)
            self.offset, self.data[left : right] = right, data
            return len(data)

        except Exception as E:
            raise error.StoreError(self, self.offset, len(data), exception=E)
        raise error.ProviderError

    @utils.mapexception(any=error.ProviderError)
    def size(self):
        return len(self.data)

class string(bytes):
    '''This is an alias for the bytes provider.'''

class fileobj(bounded):
    '''Base provider class for reading/writing from a fileobj. Intended to be inherited from.'''
    file = None
    def __init__(self, fileobj):
        self.file = fileobj

    @utils.mapexception(any=error.ProviderError)
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res = self.file.tell()
        self.file.seek(offset)
        return res

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        offset = self.file.tell()
        if amount < 0:
            raise error.UserError(self, 'consume', message="Tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(offset, amount, self))

        result = ''
        try:
            result = self.file.read(amount)

        except OverflowError as E:
            self.file.seek(offset)
            raise error.ConsumeError(self, offset, amount, len(result), exception=E)

        if result == '' and amount > 0:
            raise error.ConsumeError(self, offset, amount, len(result))

        if len(result) != amount:
            self.file.seek(offset)
        return result

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        offset = self.file.tell()
        try:
            result = self.file.write(data)

        except Exception as E:
            self.file.seek(offset)
            raise error.StoreError(self, offset, len(data), exception=E)
        return result

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
        '''x.__repr__() <=> repr(x)'''
        return "{:s} -> {!r}".format(super(fileobj, self).__repr__(), self.file)

    def __del__(self):
        try: self.close()
        except: pass
filebase = fileobj

## other providers
class random(base):
    """Provider that returns random data when read from."""
    def __init__(self):
        self.offset = 0

    @utils.mapexception(any=error.ProviderError)
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        _random.seed(self.offset)   # lol
        return res

    @utils.mapexception(any=error.ProviderError)
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        res = map(_random.randint, (0,) * amount, (255,) * amount)
        return builtins.bytes().join(map(six.int2byte, res))

    @utils.mapexception(any=error.ProviderError)
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        Log.info("{:s}.store : Tried to write {:d} bytes to a read-only medium.".format(type(self).__name__, len(data)))
        return len(data)

## special providers
class stream(base):
    """Provider that caches data read from a file stream in order to provide random-access reading.

    When reading from a particular offset, this provider will load only as much data as needed into it's cache in order to satify the user's request.
    """
    data = data_ofs = None
    iterator = None
    eof = False

    offset = None

    def __init__(self, source, offset=0):
        self.source = source
        self.data = array.array('B')
        self.data_ofs = self.offset = offset

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res
    def _read(self, amount):
        return self.source.read(amount)
    def _write(self, data):
        return self.source.write(data)

    def __getattr__(self, name):
        return getattr(self.source, name)

    ###
    def preread(self, amount):
        '''Preload some bytes from the stream and append it to the cache.'''
        if self.eof:
            raise EOFError

        data = self._read(amount)
        self.data.extend( array.array('B', bytearray(data)) )
        if len(data) < amount:    # XXX: this really can't be the only way(?) that an instance
                                  #      of something ~fileobj.read (...) can return for a 
            self.eof = True
        return data

    @utils.mapexception(any=error.ProviderError)
    def remove(self, amount):
        '''Removes some number of bytes from the beginning of the cache.'''
        assert amount < len(self.data)
        result = self.data[:amount]
        del(self.data[:amount])
        self.data_ofs += amount
        return result

    ###
    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the given provider.'''
        o = self.offset - self.data_ofs
        if o < 0:
            raise ValueError("{:s}.consume : Unable to seek to offset {:x} ({:x}:{:+x})".format(type(self).__name__, self.offset, self.data_ofs, len(self.data)))

        # select the requested data
        if (self.eof) or (o + amount <= len(self.data)):
            result = self.data[o : o + amount].tostring()
            self.offset += amount
            return result

        # preread enough bytes so that stuff works
        elif len(self.data) == 0 or o <= len(self.data):
            n = amount - (len(self.data) - o)
            self.preread(n)
            return self.consume(amount)

        # preread up to the offset
        if o + amount > len(self.data):
            self.preread(o - len(self.data))
            return self.consume(amount)

        raise error.ConsumeError(self, self.offset, amount)

    if False:
        def store(self, data):
            '''updates data at an offset in the stream's cache.'''
            # FIXME: this logic _apparently_ hasn't been thought out at all..check notes
            o = self.offset - self.data_ofs
            if o >= 0 and o <= len(self.data):
                self.data[o : o + len(data)] = array.array('B', bytearray(data))
                if o + len(data) >= len(self.data):
                    self.eof = False
                self._write(data)
                return len(data)
            raise ValueError("{:s}.store : Unable to store {:+d} bytes outside of provider's cache size ({:x}:{:+x}).".format(type(self), len(data), self.data_ofs, len(self.data)))

    @utils.mapexception(any=error.ProviderError)
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        return self._write(data)

    def __repr__(self):
        '''x.__repr__() <=> repr(x)'''
        return "{:s}[eof={!r},base={:x},length={:+x}] offset={:x}".format(type(self), self.eof, self.data_ofs, len(self.data), self.offset)

    def __getitem__(self, i):
        '''x.__getitem__(y) <==> x[y]'''
        return self.data[i - self.data_ofs]

    def __getslice__(self, i, j):
        '''x.__getslice__(i, j) <==> x[i:j]'''
        return self.data[i - self.data_ofs : j - self.data_ofs].tostring()

    def hexdump(self, **kwds):
        return utils.hexdump(self.data.tostring(), offset=self.data_ofs, **kwds)

class iterable(stream):
    '''Provider that caches data read from a generator/iterable in order to provide random-access reading.'''
    def _read(self, amount):
        return builtins.bytes().join(itertools.islice(self.source, amount))

    def _write(self, data):
        Log.info("iter._write : Tried to write {:+x} bytes to an iterator".format(len(data)))
        return len(data)

class posixfile(fileobj):
    '''Basic posix file provider.'''
    def __init__(self, *args, **kwds):
        res = self.open(*args, **kwds)
        super(posixfile, self).__init__(res)

    @utils.mapexception(any=error.ProviderError)
    def open(self, filename, mode='rw', perms=0o644):
        mode = builtins.bytes().join(sorted(set(x.lower() for x in mode)))
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

        if os.access(filename, 6):
            Log.info("{:s}({!r}, {!r}) : Opening file for {:s}".format(type(self).__name__, filename, mode, access))
        else:
            flags |= os.O_CREAT|os.O_TRUNC
            Log.info("{:s}({!r}, {!r}) : Creating new file for {:s}".format(type(self).__name__, filename, mode, access))

        # mode defaults to rw-rw-r--
        self.fd = os.open(filename, flags, perms)
        return os.fdopen(self.fd)

    @utils.mapexception(any=error.ProviderError)
    def close(self):
        os.close(self.fd)
        return super(posixfile, self).close()

class file(fileobj):
    '''Basic file provider.'''
    def __init__(self, *args, **kwds):
        res = self.open(*args, **kwds)
        return super(file, self).__init__(res)

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

        if os.access(filename, 0):
            if 'wb' in access:
                Log.warn("{:s}({!r}, {!r}) : Truncating file by user-request.".format(type(self).__name__, filename, access))
            Log.info("{:s}({!r}, {!r}) : Opening file for {:s}".format(type(self).__name__, filename, access, straccess))

        else:  # file not found
            if 'r+' in access:
                Log.warn("{:s}({!r}, {!r}) : File not found. Modifying access to write-only.".format(type(self).__name__, filename, access))
                access = 'wb'
            Log.warn("{:s}({!r}, {!r}) : Creating new file for {:s}".format(type(self).__name__, filename, access, straccess))

        return builtins.open(filename, access, 0)

try:
    class filecopy(fileobj):
        """A provider that reads/writes from a temporary copy of the specified file.

        If the user wishes to save the file to another location, a .save method is provided.
        """
        import tempfile as __tempfile__

        def __init__(self, *args, **kwds):
            res = self.open(*args, **kwds)
            return super(filecopy, self).__init__(res)

        @utils.mapexception(any=error.ProviderError)
        def open(self, filename):
            '''Open the specified file as a temporary file.'''
            with open(filename, 'rb') as input:
                input.seek(0)
                output = self.__tempfile__.TemporaryFile(mode='w+b')
                for data in input:
                    output.write(data)
                output.seek(0)
            return output

        def save(self, filename):
            '''Copy the current temporary file to the specified ``filename``.'''
            ofs = self.file.tell()
            with builtins.file(filename, 'wb') as output:
                self.file.seek(0)
                for data in self.file:
                    output.write(data)
            self.file.seek(ofs)

except ImportError:
    Log.info("{:s} : Unable to import the 'tempfile' module. Failed to define the `filecopy` provider.".format(__name__))

## platform-specific providers
DEFAULT = []
try:
    if not sys.platform.startswith('linux'):
        raise OSError

    class LinuxProcessId(memorybase):
        @staticmethod
        def _open(pid, path="/proc/{:d}/mem"):
            return open(path.format(pid), 'rb')

        def __init__(self, pid):
            self._pid = pid
            res = self._open(pid)
            self._fileobj = fileobj(res)

        def seek(self, offset):
            return self._fileobj.seek(offset)
        def consume(self, amount):
            return self._fileobj.consume(amount)
        def store(self, data):
            return self._fileobj.store(data)

        def close(self):
            return self._fileobj.close()

        def __del__(self):
            try: self.close()
            except: pass

        def __repr__(self):
            '''x.__repr__() <=> repr(x)'''
            return "{:s} -> pid:{:#x} ({:d})".format(super(memorybase, self).__repr__(), self._pid, self._pid)

except OSError as E:
    Log.info("{:s} : Skipping defining any linux-based providers (`LinuxProcessId`) due to being on a non-linux platform ({:s}).".format(__name__, sys.platform))

try:
    import ctypes
    try:
        k32 = ctypes.WinDLL('kernel32.dll')
    except Exception as E:
        raise OSError(E)

    # Define the ctypes parameters for the windows api used by win32error
    k32.GetLastError.restype = ctypes.c_uint32
    k32.FormatMessageA.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
    k32.FormatMessageA.restype = ctypes.c_uint32
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    k32.LocalFree.restype = ctypes.c_void_p

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
            if res == 0:
                raise AssertionError("KERNEL32.dll!LocalFree failed. Error {:#0{:d}x}.".format(k32.GetLastError(), 2 + 8))

            return (errorCode, errorString)

        @staticmethod
        def getLastErrorString():
            code, string = getLastErrorTuple()
            return string

    # Define the ctypes parameters for the windows api used by WindowsProcessHandle
    k32.ReadProcessMemory.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k32.ReadProcessMemory.restype = ctypes.c_bool
    k32.WriteProcessMemory.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k32.WriteProcessMemory.restype = ctypes.c_bool

    class WindowsProcessHandle(memorybase):
        '''Windows memory provider that will use a process handle in order to access memory.'''
        address = 0
        handle = None
        def __init__(self, handle):
            self.handle = handle

        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            res, self.address = self.address, offset
            return res

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            if amount < 0:
                raise error.UserError(self, 'consume', message="tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(self.address, amount, self))

            NumberOfBytesRead = ctypes.c_size_t()
            buffer_t = ctypes.c_char * amount
            buffer = buffer_t()

            # FIXME: instead of failing on an incomplete read, perform a partial read
            res = k32.ReadProcessMemory(self.handle, self.address, buffer, amount, ctypes.pointer(NumberOfBytesRead))
            if (res == 0) or (NumberOfBytesRead.value != amount):
                e = ValueError("Unable to read pid({:x})[{:08x}:{:08x}].".format(self.handle, self.address, self.address + amount))
                raise error.ConsumeError(self, self.address, amount, NumberOfBytesRead.value)

            self.address += amount
            return memoryview(buffer).tobytes()

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, value):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            NumberOfBytesWritten = ctypes.c_size_t()

            buffer_t = ctypes.c_char * len(value)
            buffer = buffer_t()
            buffer.value = value

            res = k32.WriteProcessMemory(self.handle, self.address, buffer, len(value), ctypes.pointer(NumberOfBytesWritten))
            if (res == 0) or (NumberOfBytesWritten.value != len(value)):
                e = OSError("Unable to write to pid({:x})[{:08x}:{:08x}].".format(self.id, self.address, self.address + len(value)))
                raise error.StoreError(self, self.address, len(value), written=NumberOfBytesWritten.value, exception=e)

            self.address += len(value)
            return NumberOfBytesWritten.value

    # Define the ctypes parameters for the windows api used by WindowsProcessId
    k32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
    k32.OpenProcess.restype = ctypes.c_size_t

    def WindowsProcessId(pid, **attributes):
        '''Return a provider that allows one to read/write from memory owned by the specified windows process ``pid``.'''
        handle = k32.OpenProcess(0x30, False, pid)
        return WindowsProcessHandle(handle)

    # Define the ctypes parameters for the windows api used by WindowsFile
    k32.CreateFileA.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
    k32.CreateFileA.restype = ctypes.c_size_t
    k32.SetFilePointerEx.argtypes = [ctypes.c_size_t, ctypes.c_longlong, ctypes.c_longlong, ctypes.c_uint32]
    k32.SetFilePointerEx.restype = ctypes.c_bool
    k32.ReadFile.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
    k32.ReadFile.restype = ctypes.c_bool
    k32.WriteFile.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
    k32.WriteFile.restype = ctypes.c_bool
    k32.CloseHandle.argtypes = [ctypes.c_size_t]
    k32.CloseHandle.restype = ctypes.c_bool

    class WindowsFile(base):
        '''A provider that uses the Windows File API.'''
        offset = 0
        def __init__(self, filename, mode='rb'):
            self.offset = 0

            GENERIC_READ, GENERIC_WRITE = 0x40000000, 0x80000000
            FILE_SHARE_READ, FILE_SHARE_WRITE = 1, 2
            OPEN_EXISTING, OPEN_ALWAYS = 3, 4
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
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            distance, resultDistance = ctypes.c_longlong(offset), ctypes.c_longlong(offset)
            FILE_BEGIN = 0
            result = k32.SetFilePointerEx(
                self.handle, distance, ctypes.byref(resultDistance),
                FILE_BEGIN
            )
            if result == 0:
                raise OSError(win32error.getLastErrorTuple())
            res, self.offset = self.offset, resultDistance.value
            return res

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            buffer_t = ctypes.c_char * amount
            resultBuffer = buffer_t()

            amount, resultAmount = ctypes.c_ulong(amount), ctypes.c_ulong(amount)
            result = k32.ReadFile(
                self.handle, ctypes.pointer(resultBuffer),
                amount, ctypes.pointer(resultAmount),
                None
            )
            if (result == 0) or (resultAmount.value == 0 and amount > 0):
                e = OSError(win32error.getLastErrorTuple())
                raise error.ConsumeError(self, self.offset, amount, resultAmount.value, exception=e)

            if resultAmount.value == amount:
                self.offset += resultAmount.value
            return memoryview(resultBuffer).tobytes()

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, value):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            buffer_t = c-char * len(value)
            buffer = buffer_t(value)
            resultWritten = ctypes.c_ulong()

            result = k32.WriteFile(
                self.handle, buffer,
                len(value), ctypes.pointer(resultWritten),
                None
            )
            if (result == 0) or (resultWritten.value != len(value)):
                e = OSError(win32error.getLastErrorTuple())
                raise error.StoreError(self, self.offset, len(value), resultWritten.value, exception=e)
            self.offset += resultWritten.value
            return resultWritten.value

        @utils.mapexception(any=error.ProviderError)
        def close(self):
            result = k32.CloseHandle(self.handle)
            if (result == 0):
                raise OSError(win32error.getLastErrorTuple())
            self.handle = None
            return result

    Log.info("{:s} : Successfully loaded the `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers.".format(__name__))
except ImportError:
    Log.info("{:s} : Unable to import the 'ctypes' module. Failed to define the `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers.".format(__name__))

except OSError as E:
    Log.info("{:s} : Unable to load 'kernel32.dll' ({!s}). Failed to define the `WindowsProcessHandle`, `WindowsProcessId`, and `WindowsFile` providers.".format(__name__, E))

try:
    _ = 'idaapi' in sys.modules
    class Ida(debuggerbase):
        '''A provider that uses IDA Pro's API for reading/writing to the database.'''

        class __api__(object):
            """
            Static class for abstracting around IDA's API prior to 7.0,
            and 7.0 or later.
            """
            module = importlib.import_module('idaapi')
            BADADDR = module.BADADDR

            if hasattr(module, 'get_many_bytes'):
                get_bytes = staticmethod(module.get_many_bytes)
            elif hasattr(module, 'get_bytes'):
                get_bytes = staticmethod(module.get_bytes)
            else:
                raise ImportError('get_many_bytes')

            get_nlist_ea = staticmethod(module.get_nlist_ea)
            get_nlist_size = staticmethod(module.get_nlist_size)
            getseg = staticmethod(module.getseg)

            if hasattr(module, 'patch_many_bytes'):
                patch_bytes = staticmethod(module.patch_many_bytes)
            elif hasattr(module, 'patch_bytes'):
                patch_bytes = staticmethod(module.patch_bytes)
            else:
                raise ImportError('patch_many_bytes')

            if hasattr(module, 'put_many_bytes'):
                put_bytes = staticmethod(module.put_many_bytes)
            elif hasattr(module, 'put_bytes'):
                put_bytes = staticmethod(module.put_bytes)
            else:
                raise ImportError('put_many_bytes')

            if hasattr(module, 'isEnabled'):
                is_mapped = staticmethod(module.isEnabled)
            elif hasattr(module, 'is_mapped'):
                is_mapped = staticmethod(module.is_mapped)
            else:
                raise ImportError('isEnabled')

        offset = __api__.BADADDR
        def __new__(cls):
            Log.info("{:s} : This class is intended to be used statically. Please do not instantiate this. Returning static version of class.".format('.'.join((__name__, cls.__name__))))
            return cls

        @classmethod
        def read(cls, offset, size, padding=b'\0'):
            result = cls.__api__.get_bytes(offset, size) or b''
            if len(result) == size:
                return result

            half = size // 2
            if half > 0:
                return builtins.bytes().join((cls.read(offset, half, padding=padding), cls.read(offset + half, half + size%2, padding=padding)))
            if cls.__api__.is_mapped(offset):
                return b'' if size == 0 else (padding * size) if (cls.module.getFlags(offset) & cls.module.FF_IVL) == 0 else cls.module.get_many_bytes(offset, size)
            raise Exception((offset, size))

        @classmethod
        def expr(cls, string):
            index = (i for i in range(cls.__api__.get_nlist_size()) if string == cls.module.get_nlist_name(i))
            try:
                res = cls.__api__.get_nlist_ea(six.next(index))

            except StopIteration:
                raise NameError("{:s}.expr : Unable to resolve symbol : {!r}".format('.'.join((__name__, cls.__name__)), string))
            return res

        @classmethod
        def within_segment(cls, offset):
            s = cls.__api__.getseg(offset)
            return s is not None and s.startEA <= offset < s.endEA

        @classmethod
        def seek(cls, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            res, cls.offset = cls.offset, offset
            return res

        @classmethod
        def consume(cls, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            startofs = cls.offset
            try:
                result = cls.read(cls.offset, amount)

            except Exception as err:
                if isinstance(err, tuple) and len(err) == 2:
                    ofs, amount = err
                    raise error.ConsumeError(cls, ofs, amount, ofs - startofs)
                Log.fatal("{:s} : Unable to read {:+d} bytes from {:x} due to unexpected exception ({:x}:{:+x}).".format('.'.join((__name__, cls.__name__)), amount, startofs, cls.offset, amount), exc_info=True)
                raise error.ConsumeError(cls, startofs, amount, cls.offset - startofs)

            cls.offset += len(result)
            return result

        @classmethod
        def store(cls, data):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            #cls.__api__.put_many_bytes(cls.offset, data)
            cls.__api__.patch_many_bytes(cls.offset, data)
            cls.offset += len(data)
            return len(data)

    Log.info("{:s} : Successfully loaded the `Ida` provider.".format(__name__))
    if _: DEFAULT.append(Ida)

except ImportError:
    Log.info("{:s} : Unable to import the 'idaapi' module (not running IDA?). Failed to define the `Ida` provider.".format(__name__))

try:
    _ = 'binaryninja' in sys.modules
    class Binja(debuggerbase):
        '''A provider that uses Binary Ninja's BinaryViewType API for reading/writing from an address space.'''
        import binaryninja

        def __init__(self, bv):
            self._view = bv
            self._address = 0

        def seek(self, address):
            res, self._address = self._address, address
            return res

        def consume(self, amount):
            res = self._view.read(self._address, amount)
            self._address += len(res)
            return res

        def store(self, data):
            res = self._view.write(self._address, data)
            self._address += res
            return res

        def expr(self, string):
            return self._view.eval(string)

    Log.info("{:s} : Successfully loaded the `Binja` provider.".format(__name__))

    frame = sys._getframe()
    while frame.f_back:
        frame = frame.f_back
    try:
        if _: DEFAULT.append(lambda bv=frame.f_globals['bv']: Binja(bv))
    except (AttributeError, KeyError):
        raise ImportError
    finally:
        del(frame)

except ImportError:
    Log.info("{:s} : Unable to import the 'binaryninja' module (not running Binja?). Failed to define the `Binja` provider.".format(__name__))

try:
    _ = '_PyDbgEng' in sys.modules
    class PyDbgEng(debuggerbase):
        '''A provider that uses the PyDbgEng.pyd module to interact with the memory of the current debugged process.'''
        import _PyDbgEng as __PyDbgEng__

        offset = 0
        def __init__(self, client=None):
            self.client = client

        @classmethod
        def connect(cls, remote):
            if remote is None:
                result = cls.__PyDbgEng__.Create()
            elif isinstance(remote, tuple):
                host, port = client
                result = cls.__PyDbgEng__.Connect("tcp:port={}, server={}".format(port, host))
            elif isinstance(remote, dict):
                result = cls.__PyDbgEng__.Connect("tcp:port={port}, server={host}".format(**client))
            elif isinstance(remote, six.string_types):
                result = cls.__PyDbgEng__.Connect(client)
            return cls(result)

        @classmethod
        def connectprocessserver(cls, remote):
            result = cls.__PyDbgEng__.ConnectProcessServer(remoteOptions=remote)
            return cls(result)

        def connectkernel(self, remote):
            if remote is None:
                result = cls.__PyDbgEng__.AttachKernel(flags=cls.__PyDbgEng__.ATTACH_LOCAL_KERNEL)
            else:
                result = cls.__PyDbgEng__.AttachKernel(flags=0, connectOptions=remote)
            return cls(result)

        @classmethod
        def expr(cls, string):
            control = cls.__PyDbgEng__.IDebugControl
            dtype = DEBUG_VALUE_INT32
            return control.Evaluate(string, dtype)

        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            res, self.offset = self.offset, offset
            return res

        def consume(self, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            try:
                result = self.client.DataSpaces.Virtual.Read(self.offset, amount)

            except RuntimeError as E:
                raise StopIteration("Unable to read {:+d} bytes from address {:x}".format(amount, self.offset))
            return builtins.bytes(result)

        def store(self, data):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            return self.client.DataSpaces.Virtual.Write(self.offset, data)

    Log.info("{:s} : Successfully loaded the `PyDbgEng` provider.".format(__name__))
    if _: DEFAULT.append(PyDbgEng)

except ImportError:
    Log.info("{:s} : Unable to import the '_PyDbgEng' module. Failed to define the `PyDbgEng` provider.".format(__name__))

try:
    _ = 'pykd' in sys.modules
    class Pykd(debuggerbase):
        '''A provider that uses the Pykd library to interact with the memory of a debugged process.'''
        import pykd as __pykd__

        def __init__(self):
            self.addr = 0

        @classmethod
        def expr(cls, string):
            return cls.__pykd__.expr(string)

        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            # FIXME: check to see if we're at an invalid address
            res, self.addr = self.addr, offset
            return res

        def consume(self, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            if amount == 0:
                return b''
            try:
                data = self.__pykd__.loadBytes(self.addr, amount)
                res = map(six.int2byte, data)
            except:
                raise error.ConsumeError(self, self.addr, amount, 0)
            self.addr += amount
            return builtins.bytes().join(res)

        def store(self, data):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            raise error.StoreError(self, self.addr, len(data), message="Pykd doesn't allow you to write to memory.")
            res = len(data)
            self.addr += res
            return res

    Log.info("{:s} : Successfully loaded the `Pykd` provider.".format(__name__))
    if _: DEFAULT.append(Pykd)

except ImportError:
    Log.info("{:s} : Unable to import the 'pykd' module. Failed to define the `Pykd` provider.".format(__name__))

try:
    _ = 'lldb' in sys.modules
    class lldb(debuggerbase):
        module = importlib.import_module('lldb')
        def __init__(self, sbprocess=None):
            self.__process = sbprocess or self.module.process
            self.address = 0

        @classmethod
        def expr(cls, string):
            raise NotImplementedError   # XXX

        def seek(self, offset):
            res, self.address = self.address, offset
            return res

        def consume(self, amount):
            if amount < 0:
                raise error.ConsumeError(self, self.address, amount)
            process, err = self.__process, self.module.SBError()
            if amount > 0:
                data = process.ReadMemory(self.address, amount, err)
                if err.Fail() or len(data) != amount:
                    raise error.ConsumeError(self, self.address, amount)
                self.address += len(data)
                return six.binary_type(data)
            return b''

        def store(self, data):
            process, err = self.__process, self.module.SBError()
            amount = process.WriteMemory(self.address, six.binary_type(data), err)
            if err.Fail() or len(data) != amount:
                raise error.StoreError(self, self.address, len(data))
            self.address += amount
            return amount

    Log.info("{:s} : Successfully loaded the `lldb` provider.".format(__name__))
    if _: DEFAULT.append(lldb)

except ImportError:
    Log.info("{:s} : Unable to import the 'lldb' module. Failed to define the `lldb` provider.".format(__name__))

try:
    _ = 'gdb' in sys.modules
    class gdb(debuggerbase):
        module = importlib.import_module('gdb')
        def __init__(self, inferior=None):
            self.__process = inferior or self.module.selected_inferior()
            self.address = 0

        @classmethod
        def expr(cls, string):
            res = gdb.parse_and_eval(string)
            return res.cast( gdb.lookup_type("long") )

        def seek(self, offset):
            res, self.address = self.address, offset
            return res

        def consume(self, amount):
            process = self.__process
            try:
                data = process.read_memory(self.address, amount)
            except gdb.MemoryError:
                data = None
            if data is None or len(data) != amount:
                raise error.ConsumeError(self, self.address, amount)
            self.address += len(data)
            return data

        def store(self, data):
            process = self.__process
            try:
                process.write_memory(self.address, data)
            except gdb.MemoryError:
                raise error.StoreError(self, self.address, len(data))
            self.address += len(data)
            return len(data)

    Log.info("{:s} : Successfully loaded the `gdb` provider.".format(__name__))
    if _: DEFAULT.append(lldb)

except ImportError:
    Log.info("{:s} : Unable to import the 'gdb' module. Failed to define the `gdb` provider.".format(__name__))

try:
    import ctypes

    ## TODO: figure out an elegant way to catch exceptions we might cause
    ##       by dereferencing any of these pointers on both windows (veh) and posix (signals)

    class memory(memorybase):
        '''Basic in-process memory provider based on ctypes.'''
        address = 0
        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            res, self.address = self.address, offset
            return res

        @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
        def consume(self, amount):
            '''Consume ``amount`` bytes from the given provider.'''
            if amount < 0:
                raise error.UserError(self, 'consume', message="tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(self.address, amount, self))
            res = memory._read(self.address, amount)
            if len(res) == 0 and amount > 0:
                raise error.ConsumeError(self, offset, amount, len(res))
            if len(res) == amount:
                self.address += amount
            return res

        @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
        def store(self, data):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            res = memory._write(self.address, data)
            if res != len(data):
                raise error.StoreError(self, self.address, len(data), written=res)
            self.address += len(data)
            return res

        @staticmethod
        def _read(address, length):
            block_t = ctypes.c_char * length
            pointer_t = ctypes.POINTER(block_t)
            voidpointer = ctypes.c_void_p(address)
            blockpointer = ctypes.cast(voidpointer, pointer_t)
            return memoryview(blockpointer.contents).tobytes()

        @staticmethod
        def _write(address, value):
            block_t = ctypes.c_char * len(value)
            pointer_t = ctypes.POINTER(block_t)
            voidpointer = ctypes.c_void_p(address)
            blockpointer = ctypes.cast(voidpointer, pointer_t)
            for i, item in enumerate(value):
                blockpointer.contents[i] = item
            return 1 + i

    DEFAULT.append(memory)

except ImportError:
    Log.info("{:s} : Unable to import the 'ctypes' module. Failed to define the `memory` provider.".format(__name__))

default = DEFAULT[0]

if __name__ == '__main__':
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)
                raise Failure
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes
    from ptypes import parray,pint,pbinary,provider

    import six
    import os,random,tempfile,time
    from six.moves.builtins import *

    class temporaryname(object):
        def __enter__(self, *args):
            self.name = tempfile.mktemp()
            return self.name
        def __exit__(self, *args):
            try: os.unlink(self.name)
            except: pass
            del(self.name)

    class temporaryfile(object):
        def __enter__(self, *args):
            name = tempfile.mktemp()
            self.file = file(name, 'w+b')
            return self.file
        def __exit__(self, *args):
            self.file.close()
            filename = self.file.name
            del(self.file)
            os.unlink(filename)

    @TestCase
    def test_file_readonly():
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.file(filename, mode='r')
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
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.file(filename, mode='w')
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
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.file(filename, mode='rw')
            z.store(data)

            z.seek(0)
            a = z.consume(len(data))
            assert a == data

            z.close()
        raise Success

    @TestCase
    def test_filecopy_read():
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.filecopy(filename)
            if z.consume(len(data)) == data:
                raise Success
        return

    @TestCase
    def test_filecopy_write():
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.filecopy(filename)
            a = z.store(b'B' * len(data))

            z.seek(0)
            a = z.consume(len(data))
            if a.count(b'B') == len(data):
                raise Success
        return

    @TestCase
    def test_filecopy_readwrite():
        data = b'A'*512
        with temporaryname() as filename:
            f = open(filename, 'wb')
            f.write(data)
            f.seek(0)
            f.close()

            z = provider.filecopy(filename)
            z.seek(len(data))
            a = z.store(b'B' * len(data))

            z.seek(0)
            a = z.consume(len(data)*2)
            if a.count(b'A') == len(data) and a.count(b'B') == len(data):
                raise Success
        return

    try:
        import ctypes
        @TestCase
        def test_memory_read():
            data = b'A'*0x40
            buf = ctypes.c_buffer(data)
            ea = ctypes.addressof(buf)
            z = provider.memory()
            z.seek(ea)
            if z.consume(len(data)) == data:
                raise Success
            raise Failure

        @TestCase
        def test_memory_write():
            data = b'A'*0x40
            buf = ctypes.c_buffer(data)
            ea = ctypes.addressof(buf)
            z = provider.memory()
            z.seek(ea)
            z.store(b'B'*len(data))
            if buf.value == b'B'*len(data):
                raise Success
            raise Failure

        @TestCase
        def test_memory_readwrite():
            data = b'A'*0x40
            buf = ctypes.c_buffer(data)
            ea = ctypes.addressof(buf)
            z = provider.memory()
            z.seek(ea)
            z.store(b'B'*len(data))
            z.seek(ea)
            if z.consume(len(data)) == b'B'*len(data):
                raise Success

    except ImportError:
        Log.warning("{:s} : Skipping the `memory` provider tests.".format(__name__))
        pass

    @TestCase
    def test_random_read():
        z = provider.random()
        z.seek(0)
        a = z.consume(0x40)
        z.seek(0)
        if a == z.consume(0x40):
            raise Success

    @TestCase
    def test_random_write():
        raise Failure('Unable to write to provider.random()')

    @TestCase
    def test_random_readwrite():
        raise Failure('Unable to write to provider.random()')

    @TestCase
    def test_proxy_read_container():
        class t1(parray.type):
            _object_ = pint.uint8_t
            length = 0x10*4

        class t2(parray.type):
            _object_ = pint.uint32_t
            length = 0x10

        source = t1().set((0x41,)*4 + (0x42,)*4 + (0x43,)*(4*0xe))
        res = t2(source=provider.proxy(source)).l
        if res[0].int() == 0x41414141 and res[1].int() == 0x42424242 and res[2].int() == 0x43434343:
            raise Success
        raise Failure

    @TestCase
    def test_proxy_write_container():
        class t1(parray.type):
            _object_ = pint.uint8_t
            length = 0x10*4

        class t2(parray.type):
            _object_ = pint.uint32_t
            length = 0x10

        source = t1().set((0x41,)*4 + (0x42,)*4 + (0x43,)*(4*0xe))
        res = t2(source=provider.proxy(source)).l
        res[1].set(0x0d0e0a0d)
        res.commit()
        if builtins.bytes().join(n.serialize() for n in source[0 : 0xc]) == b'AAAA\x0d\x0a\x0e\x0dCCCC':
            raise Success

    @TestCase
    def test_proxy_readwrite_container():
        class t1(parray.type):
            length = 8
            class _object_(pbinary.struct):
                _fields_ = [(8,'a'),(8,'b'),(8,'c')]
            _object_ = pbinary.bigendian(_object_)

        class t2(parray.type):
            _object_ = pint.uint32_t
            length = 6

        source = t1(source=ptypes.prov.string(b'abcABCdefDEFghiGHIjlkJLK')).l
        res = t2(source=ptypes.prov.proxy(source)).l
        source[0].set((0x41,0x41,0x41))
        source.commit()
        res[1].set(0x42424242)
        res[1].commit()
        if source[0].serialize() == b'AAA' and source[1].serialize() == b'ABB' and source[2]['a'] == six.byte2int(b'B') and source[2]['b'] == six.byte2int(b'B'):
            raise Success

    try:
        import nt,multiprocessing,os,ctypes
        raise ImportError
        def stringalloc(string):
            v = ctypes.c_char*len(string)
            x = v(*string)
            return x,ctypes.addressof(x)

        def stringspin(q,string):
            _,x = stringalloc(string)
            q.put(x)
            while True:
                pass

        @TestCase
        def test_windows_remote_consume():
            q = multiprocessing.Queue()
            string = "hola mundo"

            p = multiprocessing.Process(target=stringspin, args=(q,string,))
            p.start()
            address = q.get()
            print("{:#x}".format(address))

            src = provider.WindowsProcessId(p.pid)
            src.seek(address)
            data = src.consume(len(string))
            p.terminate()
            if data == string:
                raise Success

        @TestCase
        def test_windows_remote_store():
            pass

    except ImportError:
        Log.warning("{:s} : Skipping the `WindowsProcessId` provider tests.".format(__name__))

if __name__ == '__main__' and 0:
    from ptypes import ptype,parray,pstruct,pint,provider
    from array import array

    # FIXME: the virtual provider is essentially an implementation of an interval tree. there's a
    #        great bioinformatics library for this named cgranges which exposes a rope-like interface
    #        for managing intervals within a single-dimensional array.

    a = provider.virtual()
    a.available = [0,6]
    a.data = {0:'hello',6:'world'}
    print(a.available)
    print(a.data)

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

        a = provider.virtual()
        a.available = [0, 5, 10, 15, 20]
        a.data = {0:s('hello'),5:s('world'),10:s('55555'),15:s('66666'),20:s('77777')}
        a.seek(17)
        if a.consume(5) == '66677':
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
