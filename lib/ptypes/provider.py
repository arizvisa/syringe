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
import sys, os, builtins, itertools, functools, operator
import bisect, random as _random

from . import config, utils, error
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'provider']))

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

class backed(bounded):
    '''Base provider class for describing a provider that is backed by some other type.'''
    def __init__(self, offset, reference):
        self.__offset, self.__backing = offset, reference
    @property
    def backing(self):
        return self.__backing
    @backing.setter
    def backing(self, new):
        self.__backing[:] = new
    @property
    def offset(self):
        return self.__offset

    @utils.mapexception(any=error.ProviderError)
    def size(self):
        return len(self.__backing)

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.__offset = self.__offset, offset
        return res

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError, error.UserError))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the backed provider.'''
        if amount < 0:
            raise error.UserError(self, 'consume', message="tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(self.offset, amount, self))
        if amount == 0:
            return self.backing[0:0]

        # Check if the desired number of bytes are available in the backing.
        offset, size = self.__offset, self.size()
        if size <= offset:
            raise error.ConsumeError(self, offset, amount)

        # Otherwise we need to clamp our read size to consume whatever is available.
        minimum = min(offset + amount, size)
        result = self.backing[offset : minimum]
        if not result and amount > 0:
            raise error.ConsumeError(self, offset, amount, len(result))
        if len(result) == amount:
            self.__offset += amount
        return result

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError, ))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        left, right, size = self.__offset, self.__offset + len(data), self.size()
        if left > size:
            self.__offset = size
            _ = self.store(b'\0' * max(0, left - size))

        # After padding our backing to the required size, we should now
        # actually point to the correct offset.
        if self.__offset == left:
            self.__offset, self.backing[left : right] = right, data
            return len(data)
        raise error.StoreError(self, left, len(data))

class proxied(bounded):
    '''Provider that is backed by other objects that is backed by other objects that is backed by other objects that is backed by another provider.'''

    def __iter__(self):
        raise NotImplementedError("The current provider {!s} does not implement this method.".format(self.__class__))

    def iterate(self):
        '''Iterate through all of the instances that back this provider in the order that they are laid out contiguously.'''
        for item in iter(self):
            yield item
        return

    @classmethod
    def __collect__(cls, iterable, left, right):
        offset = 0
        if left > offset:
            for item in iterable:
                if left < offset + item.size():
                    yield offset, item
                    offset += item.size()
                    break
                offset += item.size()
        else:
            item = next(iterable)
            yield offset, item
            offset += item.size()

        for item in iterable:
            if right <= offset:
                break
            yield offset, item
            offset += item.size()
        return

    @classmethod
    def __interval__(cls, iterable, left, right):
        for position, item in cls.__collect__(iterable, left, right):
            lposition, rposition = left - position, right - position
            yield item, max(0, lposition), min(item.size(), rposition)
        return

    def interval(self, left, right):
        '''Return the instance, start offset, end offset of every item within the specified interval.'''
        iterable, left, right = iter(self), left, right
        return self.__interval__(iterable, left, right)

    def __pinpoint__(self, left, right):
        '''Return the start offset and end offset of the original source that are within the specified interval.'''
        # XXX: this isn't really implemented at the moment as i'd need to consolidate each
        #      contiguous interval and most importantly i don't actually need this anymore.
        def recurse(iterable, left, right):
            for item, start, stop in self.__interval__(iterable, left, right):
                if isinstance(item.source, proxied):
                    iterable, offset, size = iter(item.source), item.getoffset(), item.size()
                    for item in recurse(iterable, offset, offset + size):
                        yield item
                else:
                    res = left - position
                    yield item, res, res + (right - left)
                continue
            return
        iterable, left, right = iter(self), left, right
        return recurse(iterable, left, right)

## core providers
class empty(bounded):
    '''Empty provider. Returns only zeroes.'''
    offset = 0
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        offset = 0
        return 0
    def consume(self, amount):
        '''Consume ``amount`` bytes from the provider.'''
        return b'\0' * amount
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        Log.info("{:s}.store : Tried to write {:d} bytes to a read-only medium.".format(type(self).__name__, len(data)))
        return len(data)
    def size(self):
        return 0

class proxy(proxied):
    """Provider that will read or write its data to/from the specified ptype.

    If autoload or autocommit is specified during construction, the object will sync the proxy with it's source before performing any operations requested of the proxied-type.
    """
    def __init__(self, source, **kwds):
        """Instantiate the provider using ``source`` as it's backing ptype.

        autocommit -- A dict that will be passed to the source type's .commit method when data is stored to the provider.
        autoload -- A dict that will be passed to the source type's .load method when data is read from the provider.
        """

        self._object = source
        self.offset = 0

        valid = {'autocommit', 'autoload'}
        res = {item for item in kwds.keys()} - valid
        if res - valid:
            raise error.UserError(self, '__init__', message="Invalid keyword(s) specified. Expected ({!r}) : {!r}".format(valid, tuple(res)))

        self.autoload = kwds.get('autoload', None)
        self.autocommit = kwds.get('autocommit', None)

    @property
    def object(self):
        return self._object

    def size(self):
        '''Return the size of the object.'''
        res = self._object
        return res.size()

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the provider.'''
        left, right = self.offset, self.offset + amount

        buf = self._object.serialize() if self.autoload is None else self._object.load(**self.autoload).serialize()
#        if self.autoload is not None:
#            Log.debug("{:s}.consume : Autoloading : {:s} : {!r}".format(type(self).__name__, self._object.instance(), self._object.source))

        if (amount > 0 and left >= 0 and right <= len(buf)) or not amount:
            result = buf[left : right]
            self.offset += amount
            return result

        elif left < len(buf):
            result = buf[left:]
            return result

        consumed = len(buf) - left
        raise error.ConsumeError(self, left, amount, amount=consumed)

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        left, right = self.offset, self.offset + len(data)

        # if trying to store within the bounds of self._object..
        if left >= 0 and right <= self._object.blocksize():
            from . import ptype, pbinary
            if isinstance(self._object, pbinary.partial):
                self.store_partial(self._object, self.offset, data)

            elif isinstance(self._object, ptype.type):
                self.store_object(self._object, self.offset, data)

            elif isinstance(self._object, ptype.container):
                self.store_range(self._object, self.offset, data)

            else:
                raise NotImplementedError(self._object.__class__)

            self.offset += len(data)
            self._object if self.autocommit is None else self._object.commit(**self.autocommit)
#            if self.autocommit is not None:
#                Log.debug("{:s}.store : Autocommitting : {:s} : {!r}".format(type(self).__name__, self._object.instance(), self._object.source))
            return len(data)

        # otherwise, check if nothing is being written
        if left == right:
            return len(data)

        raise error.StoreError(self, left, len(data), 0)

    @classmethod
    def store_partial(cls, object, offset, data):
        left, right = offset, offset + len(data)
        size, value = object.blocksize(), object.serialize()
        padding = utils.padding.fill(size - min(size, len(data)), object.padding)
        object.load(offset=0, source=memoryview(value[:left] + data + padding + value[right:]))
        return sum({data, padding})

    @classmethod
    def store_object(cls, object, offset, data):
        left, right = offset, offset + len(data)
        res = object.blocksize()
        object.value = object.value[:left] + data + object.value[right:]
        return res

    @classmethod
    def store_range(cls, object, offset, data):
        result, left, right = 0, offset, offset + len(data)
        sl = list(cls.collect(object, left, right))

        # fix beginning element
        n = sl.pop(0)
        source, bs, l = n.serialize(), n.blocksize(), left - (n.getoffset() - object.getoffset())
        s = bs - l
        sourcedata = source[:l] + data[:s] + source[l+len(data[:s]):]
        n.load(offset=0, source=memoryview(sourcedata))
        result, data = result + len(data[:s]), data[s:] # sum the blocksize

        # fix elements in the middle
        while len(sl) > 1:
            n = sl.pop(0)
            source, bs = n.serialize(), n.blocksize()
            sourcedata = data[:bs] + source[len(data[:bs]):]
            n.load(offset=0, source=memoryview(sourcedata))
            result, data = result + len(data[:bs]), data[bs:]

        # fix last element
        if len(sl) > 0:
            n = sl.pop(0)
            source, bs = n.serialize(), n.blocksize()
            sourcedata = data[:bs] + source[len(data[:bs]):]
            padding = utils.padding.fill(bs - min(bs, len(sourcedata)), n.padding)
            n.load(offset=0, source=memoryview(sourcedata + padding))
            result, data = result + len(data[:bs]), data[bs:]

        # check to see if there's any data left
        if len(data) > 0:
            Log.warning("{:s} : store_range : {:d} bytes left-over from trying to write to {:d} bytes.".format(cls.__name__, len(data), result))

        # return the aggregated total
        return result

    @classmethod
    def collect(cls, object, left, right):
        '''an iterator that returns all the leaf nodes of ``object`` from field offset ``left`` to ``right``.'''
        # figure out which objects to start and stop at
        lobj = object.at(object.getoffset() + left, recurse=True) if left >= 0 else None
        robj = object.at(object.getoffset() + right, recurse=True) if right < object.blocksize() else None

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

    def __iter__(self):
        yield self._object

    def __repr__(self):
        '''x.__repr__() <=> repr(x)'''
        return "{:s} -> {:s}".format(super(proxy, self).__repr__(), self._object.instance())

class disorderly(proxied):
    def __init__(self, items, **kwds):
        '''Instantiate the provider using ``items`` as the backing types.'''
        self.offset, self.contiguous = 0, [item for item in items]

        # build the datastructures we need for finding the object for an offset.
        # FIXME: this shouldn't be done at construction time, and in the future
        #        we should be able add/remove backing objects as needed.
        self.index, self.tree = self.__build_index__(), self.__build_tree__()

        valid = {'autocommit', 'autoload'}
        res = {item for item in kwds.keys()} - valid
        if res - valid:
            raise error.UserError(self, '__init__', message="Invalid keyword(s) specified. Expected ({!r}) : {!r}".format(valid, tuple(res)))

        self.autoload = kwds.get('autoload', None)
        self.autocommit = kwds.get('autocommit', None)

    @property
    def object(self):
        return self.contiguous

    def size(self):
        '''Return the size of the object.'''
        return sum(item.size() for item in self.contiguous)

    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        res, self.offset = self.offset, offset
        return res

    def __build_index__(self):
        index, offset = {}, 0
        for object in self.contiguous:
            size = object.size()
            left, right = offset, offset + size
            left, right = sorted([left, right])
            item = left, right, object
            index[left] = item
            index.setdefault(right, item)
            offset = right
        return index

    def __build_tree__(self):
        tree, offset = [], 0
        for item in self.contiguous:
            size = item.size()
            left, right = offset, offset + size

            # XXX: this doesn't belong here since we're growing the tree linearly,
            #      but in the future this logic will be moved into its own method
            #      so that we can modify the tree after it has already been created.
            start, stop = bisect.bisect_left(tree, left), bisect.bisect_right(tree, right)
            if start != stop or all([start%2, stop%2]):
                tree[start:stop] = [left, right]
            elif not all([start%2, stop%2]):
                tree[start:stop] = [left, right]
            elif start%2:
                tree[start:stop] = [right]
            elif stop%2:
                tree[start:stop] = [left]
            offset += size
        return tree

    def __traverse__(self, left, right):
        total = sum(object.size() for object in self.contiguous)
        if left < 0 or (left != right and total <= left):
            raise error.ConsumeError(self, left, right - left, amount=right - total)
        right = min(total, right)

        index, stop = bisect.bisect_right(self.tree, left) - 1, left
        iterable = (self.index[offset] for offset in self.tree[index:])
        while stop < right:
            start, stop, object = next(iterable)

            size = stop - start
            assert(object.size() == size)

            lside = max(start, left)
            assert(lside >= start), (start, lside)
            lslice = lside - start

            rside = min(stop, right)
            assert(start <= rside <= stop), (stop, rside)
            rslice = rside - start

            yield lslice, rslice, object
        return

    def consume(self, amount):
        '''Consume ``amount`` bytes from the provider and return the data that was consumed.'''
        left, right = self.offset, self.offset + amount
        result = bytearray()
        for lslice, rslice, item in self.__traverse__(left, right):
            data = item.serialize() if self.autoload is None else item.load(**self.autoload).serialize()
            # FIXME: if our item changes size during autoload, then our tree is out-of-sync
            result.extend(data[lslice : rslice])
        if len(result) == amount:
            self.offset += len(result)
        return builtins.bytes(result)

    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        left, right, size = self.offset, self.offset + len(data), sum(item.size() for item in self.contiguous)

        if left == right:
            return len(data)

        elif not (left >= 0 and right <= size):
            raise error.StoreError(self, left, len(data), 0)

        from . import ptype, pbinary

        cls, successful, offset = self.__class__, [], 0
        try:
            for lslice, rslice, item in self.__traverse__(left, right):
                amount = rslice - lslice

                if isinstance(item, pbinary.partial):
                    size = proxy.store_partial(item, lslice, data[offset : offset + amount])
                elif isinstance(item, ptype.type):
                    size = proxy.store_object(item, lslice, data[offset : offset + amount])
                elif isinstance(item, ptype.container):
                    size = proxy.store_range(item, lslice, data[offset : offset + amount])
                else:
                    raise TypeError

                self.offset, offset = self.offset + size, offset + amount
                successful.append(item)

        except error.ConsumeError as E:
            Log.warning("{:s} : store : Unable to write {:d} bytes to offset {:#x} of object {:s}.".format(cls.__name__, amount, lslice, item.instance()))
            raise E

        except Exception as E:
            Log.warning("{:s} : store : Unable to write {:d} bytes to offset {:#x} of unknown object {!s}.".format(cls.__name__, amount, lslice, item))
            raise E

        # FIXME: Not sure if I'm supposed to trap and raise an exception or whatever if this fails?
        if self.autocommit is not None:
            [item.commit(**self.autocommit) for item in successful]
        return offset

    def __iter__(self):
        '''Iterate through all of the instances that back this provider.'''
        for item in self.contiguous:
            yield item
        return

    def __repr__(self):
        '''x.__repr__() <=> repr(x)'''
        return "{:s} -> [{:s}]".format(super(disorderly, self).__repr__(), ', '.join(map(operator.methodcaller('instance'), self.contiguous)))

class memoryview(backed):
    '''Basic writeable bytes provider.'''
    data = memoryview   # this is backed by a memoryview type
    def __init__(self, reference=b''):
        view = builtins.memoryview(reference)
        super(memoryview, self).__init__(0, view)

    @property
    def value(self):
        return self.backing.tobytes()

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError, error.UserError))
    def consume(self, amount):
        result = super(memoryview, self).consume(amount)
        return result.tobytes()

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError, ))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        try:
            view = builtins.memoryview(data)
            result = super(memoryview, self).store(view)

        except Exception:
            raise error.StoreError(self, self.offset, len(data))
        return result

class array(backed):
    '''Provider that is backed by an array of some sort.'''
    data = list

    def __init__(self, reference=bytearray()):
        super(array, self).__init__(0, reference)

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError, error.UserError))
    def consume(self, amount):
        result = super(array, self).consume(amount)
        return builtins.bytes(bytearray(result))

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError, ))
    def store(self, data):
        return super(array, self).store(bytearray(data))

class bytes(memoryview):
    '''This is an alias for the memoryview provider.'''
string = bytes

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
        '''Consume ``amount`` bytes from the provider.'''
        offset = self.file.tell()
        if amount < 0:
            raise error.UserError(self, 'consume', message="Tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(offset, amount, self))

        result = b''
        try:
            result = self.file.read(amount)

        except OverflowError:
            self.file.seek(offset)
            raise error.ConsumeError(self, offset, amount, len(result))

        if result == b'' and amount > 0:
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

        except Exception:
            self.file.seek(offset)
            raise error.StoreError(self, offset, len(data))
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
        except Exception: pass
filebase = fileobj

## other providers
class remote(bounded):
    '''
    Base remote provider class.

    Intended to be inherited from when defining a remote provider that needs to
    cache any data that is being read or written. To use this, simply inherit
    from this class and implement the remote.read(), and the remote.send() methods.

    Once the provider is instantiated, the user may call the .send() method to
    submit any committed data, or the .reset() method when it is necessary to
    reset the data that was cached.
    '''
    __cons__ = staticmethod(bytearray)

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

    def size(self):
        '''Return the number of bytes that have already been committed and would end up being sent.'''
        return len(self.__buffer__)

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
            return builtins.bytes(buffer)
        # Otherwise, we need to read some more data from our class.
        data = self.read(right - len(cache))
        cache += data

        # If we still don't have enough data, then raise an exception.
        if len(cache) < right:
            raise error.ConsumeError(self, self.offset, amount)

        # Now we can return the data from our cache that we just populated.
        self.offset, buffer = right, cache[left : right]
        return builtins.bytes(buffer)

    def store(self, data):
        '''Write some number of bytes to the current offset. If nothing was able to be written, raise an exception.'''
        buffer, data = self.__buffer__, self.__cons__(data)

        # If our current offset is past the length of our buffer, then pad it
        # to the size that we'll need.
        if self.offset > len(buffer):
            padding = b'\0' * (self.offset - len(self.__buffer__))
            buffer += padding

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
        return builtins.bytes(buffer)

    def read(self, amount):
        """Read some number of bytes from the provider and return it.

        This is required to be implemented and called by a child implementation.
        """
        raise error.ImplementationError(self, 'read', message='User forgot to implement this method')

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
        '''Consume ``amount`` bytes from the provider.'''
        res = map(_random.randint, (0,) * amount, (255,) * amount)
        return builtins.bytes(bytearray(res))

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
        self.data = bytearray()
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
        self.data.extend(bytearray(data))
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
        return builtins.bytes(result)

    ###
    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the provider.'''
        o = self.offset - self.data_ofs
        if o < 0:
            raise ValueError("{:s}.consume : Unable to seek to offset {:x} ({:x}:{:+x})".format(type(self).__name__, self.offset, self.data_ofs, len(self.data)))

        # select the requested data
        if (self.eof) or (o + amount <= len(self.data)):
            result = builtins.bytes(self.data[o : o + amount])
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
                self.data[o : o + len(data)] = bytearray(data)
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
        return "{!s}[eof={!r},base={:x},length={:+x}] offset={:x}".format(type(self), self.eof, self.data_ofs, len(self.data), self.offset)

    def __getitem__(self, i):
        '''x.__getitem__(y) <==> x[y]'''
        if isinstance(i, slice):
            return self.__getslice__(i.start, i.stop)
        res = self.data[i - self.data_ofs]
        return chr(res)

    def __getslice__(self, i, j):
        '''x.__getslice__(i, j) <==> x[i:j]'''
        res = self.data[i - self.data_ofs : j - self.data_ofs]
        return builtins.bytes(res)

    def hexdump(self, **kwds):
        data = builtins.bytes(self.data)
        return utils.hexdump(data, offset=self.data_ofs, **kwds)

class iterable(stream):
    '''Provider that caches data read from a generator/iterable in order to provide random-access reading.'''

    @staticmethod
    def __iconsume__(iterable, amount):
        '''this is just like itertools.islice but only implement the 2-parameter version.'''
        for _, item in zip(range(amount), iterable):
            yield item
        return

    def _itertools_read(self, amount):
        return bytes(bytearray(itertools.islice(self.source, amount)))
    def _iconsume_read(self, amount):
        return bytes(bytearray(self.__iconsume__(self.source, amount)))
    _read = _itertools_read if not hasattr(sys, 'implementation') else _itertools_read if sys.implementation.name in {'cpython'} else _iconsume_read

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
        mode = str().join(sorted(item.lower() for item in mode))
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
                Log.warning("{:s}({!r}, {!r}) : Truncating file by user-request.".format(type(self).__name__, filename, access))
            Log.info("{:s}({!r}, {!r}) : Opening file for {:s}".format(type(self).__name__, filename, access, straccess))

        else:  # file not found
            if 'r+' in access:
                Log.warning("{:s}({!r}, {!r}) : File not found. Modifying access to write-only.".format(type(self).__name__, filename, access))
                access = 'wb'
            Log.warning("{:s}({!r}, {!r}) : Creating new file for {:s}".format(type(self).__name__, filename, access, straccess))

        return builtins.open(filename, access, 0)

try:
    import tempfile as __tempfile__

    class filecopy(fileobj):
        """A provider that reads/writes from a temporary copy of the specified file.

        If the user wishes to save the file to another location, a .save method is provided.
        """
        def __init__(self, *args, **kwds):
            res = self.open(*args, **kwds)
            return super(filecopy, self).__init__(res)

        @utils.mapexception(any=error.ProviderError)
        def open(self, filename):
            '''Open the specified file as a temporary file.'''
            with open(filename, 'rb') as input:
                input.seek(0)
                output = __tempfile__.TemporaryFile(mode='w+b')
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
            except Exception: pass

        def __repr__(self):
            '''x.__repr__() <=> repr(x)'''
            return "{:s} -> pid:{:#x} ({:d})".format(super(memorybase, self).__repr__(), self._pid, self._pid)

except OSError:
    Log.info("{:s} : Skipping defining any linux-based providers (`LinuxProcessId`) due to being on a non-linux platform ({:s}).".format(__name__, sys.platform))

### Windows Native APIs
try:
    import ctypes
    try:
        import ctypes.wintypes
        class NATIVE(object):
            __available__ = {item for item in []}

            WORD = ctypes.wintypes.WORD
            DWORD = ctypes.wintypes.DWORD
            LPVOID = PVOID = LPCVOID = ctypes.wintypes.LPVOID
            HANDLE = ctypes.wintypes.HANDLE
            SIZE_T = ctypes.c_size_t
            BOOL = ctypes.wintypes.BOOL
            LPCSTR = ctypes.wintypes.LPCSTR
            LARGE_INTEGER = ctypes.wintypes.LARGE_INTEGER
            PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
            NTSTATUS = ctypes.c_size_t
            DWORD_PTR = ctypes.c_void_p
            ULONG_PTR = ctypes.c_void_p
            KPRIORITY = ctypes.c_ulong
            ULONG = ctypes.wintypes.ULONG
            PULONG = ctypes.POINTER(ULONG)
            ULONGLONG = ULONG64 = ctypes.c_ulonglong
            PULONGLONG = PULONG64 = ctypes.POINTER(ULONG64)
            PVOID64 = ctypes.c_ulonglong

        NATIVE.K32 = ctypes.WinDLL('kernel32.dll')
        NATIVE.NT = ctypes.WinDLL('ntdll.dll')

        class CONST(object): pass
        NATIVE.CONST = CONST
        NATIVE.CONST.STATUS_SUCCESS = 0
        del(CONST)

        class SYSTEM_INFO(ctypes.Structure):
            _fields_ = [
                ('wProcessorArchitecture', NATIVE.WORD),
                ('wReserved', NATIVE.WORD),
                ('dwPageSize', NATIVE.DWORD),
                ('lpMinimumApplicationAddress', NATIVE.PVOID),
                ('lpMaximumApplicationAddress', NATIVE.PVOID),
                ('dwActiveProcessorMask', NATIVE.DWORD_PTR),
                ('dwNumberOfProcessors', NATIVE.DWORD),
                ('dwProcessorType', NATIVE.DWORD),
                ('dwAllocationGranularity', NATIVE.DWORD),
                ('wProcessorLevel', NATIVE.WORD),
                ('wProcessorRevision', NATIVE.WORD),
            ]

        NATIVE.SYSTEM_INFO = SYSTEM_INFO
        del(SYSTEM_INFO)

        NATIVE.CONST.PROCESSOR_ARCHITECTURE_AMD64 = 9
        NATIVE.CONST.PROCESSOR_ARCHITECTURE_ARM = 5
        NATIVE.CONST.PROCESSOR_ARCHITECTURE_ARM64 = 12
        NATIVE.CONST.PROCESSOR_ARCHITECTURE_IA64 = 6
        NATIVE.CONST.PROCESSOR_ARCHITECTURE_INTEL = 0
        NATIVE.CONST.PROCESSOR_ARCHITECTURE_UNKNOWN = 0xffff

        NATIVE.K32.GetNativeSystemInfo.argtypes = [ ctypes.POINTER(NATIVE.SYSTEM_INFO) ]
        NATIVE.K32.GetNativeSystemInfo.restype = None

    except Exception as E:
        class NATIVE(object):
            __available__ = {}
        raise OSError(E)

    # Define the ctypes parameters for the windows api used by win32error
    try:
        NATIVE.K32.GetLastError.argtypes = []
        NATIVE.K32.GetLastError.restype = NATIVE.DWORD
        NATIVE.K32.FormatMessageA.argtypes = [NATIVE.DWORD, NATIVE.LPVOID, NATIVE.DWORD, NATIVE.DWORD, NATIVE.LPVOID, NATIVE.DWORD, NATIVE.LPVOID]
        NATIVE.K32.FormatMessageA.restype = NATIVE.DWORD
        NATIVE.K32.LocalFree.argtypes = [NATIVE.HANDLE]
        NATIVE.K32.LocalFree.restype = NATIVE.HANDLE

    except AttributeError: pass
    else: NATIVE.__available__ |= {'WIN32ERROR'}

    # Define the ctypes parameters for the windows api used by WindowsProcessId and WindowsProcessHandle
    try:
        NATIVE.K32.DebugBreak.argtypes = []
        NATIVE.K32.DebugBreak.restypes = None

        NATIVE.K32.CloseHandle.argtypes = [NATIVE.HANDLE]
        NATIVE.K32.CloseHandle.restype = NATIVE.BOOL

        NATIVE.K32.GetCurrentProcess.argtypes = []
        NATIVE.K32.GetCurrentProcess.restype = NATIVE.HANDLE
        NATIVE.K32.GetCurrentProcessId.argtypes = []
        NATIVE.K32.GetCurrentProcessId.restype = NATIVE.DWORD
        NATIVE.K32.OpenProcess.argtypes = [NATIVE.DWORD, NATIVE.BOOL, NATIVE.DWORD]
        NATIVE.K32.OpenProcess.restype = NATIVE.HANDLE

        NATIVE.K32.GetProcessInformation.argtypes = [ NATIVE.HANDLE, ctypes.c_size_t, NATIVE.LPVOID, NATIVE.DWORD ]
        NATIVE.K32.GetProcessInformation.restype = NATIVE.BOOL

        # 5.1
        NATIVE.K32.IsWow64Process.argtypes = [NATIVE.HANDLE, ctypes.POINTER(NATIVE.BOOL)]
        NATIVE.K32.IsWow64Process.restype = NATIVE.BOOL

        class PROCESS_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('ExitStatus', NATIVE.NTSTATUS),
                ('PebBaseAddress', NATIVE.PVOID),
                ('AffinityMask', NATIVE.ULONG_PTR),
                ('BasePriority', NATIVE.KPRIORITY),
                ('UniqueProcessId', NATIVE.ULONG_PTR),
                ('InheritedFromUniqueProcessId', NATIVE.ULONG_PTR),
            ]

        NATIVE.PROCESS_BASIC_INFORMATION = PROCESS_BASIC_INFORMATION
        del(PROCESS_BASIC_INFORMATION)
        NATIVE.CONST.ProcessBasicInformation = 0

        NATIVE.NT.NtQueryInformationProcess.argtypes = [ NATIVE.HANDLE, ctypes.c_size_t, NATIVE.PVOID, NATIVE.ULONG, NATIVE.PULONG ]
        NATIVE.NT.NtQueryInformationProcess.restype = NATIVE.NTSTATUS
        NATIVE.NT.NtQueryInformationThread.argtypes = [ NATIVE.HANDLE, ctypes.c_size_t, NATIVE.PVOID, NATIVE.ULONG, NATIVE.PULONG ]
        NATIVE.NT.NtQueryInformationThread.restype = NATIVE.NTSTATUS

        NATIVE.K32.ReadProcessMemory.argtypes = [NATIVE.HANDLE, NATIVE.LPCVOID, NATIVE.LPVOID, NATIVE.SIZE_T, ctypes.POINTER(NATIVE.SIZE_T)]
        NATIVE.K32.ReadProcessMemory.restype = NATIVE.BOOL
        NATIVE.K32.WriteProcessMemory.argtypes = [NATIVE.HANDLE, NATIVE.LPVOID, NATIVE.LPCVOID, NATIVE.SIZE_T, ctypes.POINTER(NATIVE.SIZE_T)]
        NATIVE.K32.WriteProcessMemory.restype = NATIVE.BOOL

        NATIVE.CONST.PROCESS_QUERY_INFORMATION = 0x0400
        NATIVE.CONST.PROCESS_VM_WRITE = 0x0020
        NATIVE.CONST.PROCESS_VM_READ = 0x0010
        NATIVE.CONST.PROCESS_VM_OPERATION = 0x0008

    except AttributeError: pass
    else: NATIVE.__available__ |= {'PROCESS'}

    # Define the ctypes parameters for the windows api used by WindowsFile
    try:
        NATIVE.K32.CreateFileA.argtypes = [NATIVE.LPCSTR, NATIVE.DWORD, NATIVE.DWORD, ctypes.c_void_p, NATIVE.DWORD, NATIVE.DWORD, NATIVE.HANDLE]
        NATIVE.K32.CreateFileA.restype = NATIVE.HANDLE
        NATIVE.K32.SetFilePointerEx.argtypes = [NATIVE.HANDLE, NATIVE.LARGE_INTEGER, NATIVE.PLARGE_INTEGER, NATIVE.DWORD]
        NATIVE.K32.SetFilePointerEx.restype = NATIVE.BOOL
        NATIVE.K32.ReadFile.argtypes = [NATIVE.HANDLE, NATIVE.LPVOID, NATIVE.DWORD, ctypes.POINTER(NATIVE.DWORD), ctypes.c_void_p]
        NATIVE.K32.ReadFile.restype = NATIVE.BOOL
        NATIVE.K32.WriteFile.argtypes = [NATIVE.HANDLE, NATIVE.LPCVOID, NATIVE.DWORD, ctypes.POINTER(NATIVE.DWORD), ctypes.c_void_p]
        NATIVE.K32.WriteFile.restype = NATIVE.BOOL
        NATIVE.K32.CloseHandle.argtypes = [NATIVE.HANDLE]
        NATIVE.K32.CloseHandle.restype = NATIVE.BOOL

    except AttributeError: pass
    else: NATIVE.__available__ |= {'FILE'}

    # Define the ctypes parameters for the windows api used by Wow64
    try:
        # 5.2
        NATIVE.NT.NtWow64QueryInformationProcess64.argtypes = [ NATIVE.HANDLE, ctypes.c_size_t, NATIVE.PVOID, NATIVE.ULONG, NATIVE.PULONG ]
        NATIVE.NT.NtWow64QueryInformationProcess64.restype = NATIVE.NTSTATUS
        #NATIVE.NT.NtWow64QueryVirtualMemory64.argtypes = [NATIVE.HANDLE, NATIVE.PVOID64, ctypes.c_size_t, NATIVE.PVOID, NATIVE.ULONG64, NATIVE.PULONG64]
        #NATIVE.NT.NtWow64QueryVirtualMemory64.restype = NATIVE.NTSTATUS
        NATIVE.NT.NtWow64ReadVirtualMemory64.argtypes = [NATIVE.HANDLE, NATIVE.PVOID64, NATIVE.PVOID, NATIVE.ULONG64, NATIVE.PULONG64]
        NATIVE.NT.NtWow64ReadVirtualMemory64.restype = NATIVE.NTSTATUS

        # 6.0
        NATIVE.NT.NtWow64WriteVirtualMemory64.argtypes = [NATIVE.HANDLE, NATIVE.PVOID64, NATIVE.PVOID, NATIVE.ULONG64, NATIVE.PULONG64]
        NATIVE.NT.NtWow64WriteVirtualMemory64.restype = NATIVE.NTSTATUS

        class PROCESS_BASIC_INFORMATION_WOW64(ctypes.Structure):
            _fields_ = [
                ('ExitStatus', NATIVE.NTSTATUS),
                ('PebBaseAddress', NATIVE.ULONGLONG),
                ('AffinityMask', NATIVE.ULONGLONG),
                ('BasePriority', NATIVE.KPRIORITY),
                ('UniqueProcessId', NATIVE.ULONGLONG),
                ('InheritedFromUniqueProcessId', NATIVE.ULONGLONG),
            ]

        NATIVE.PROCESS_BASIC_INFORMATION_WOW64 = PROCESS_BASIC_INFORMATION_WOW64
        del(PROCESS_BASIC_INFORMATION_WOW64)

    except AttributeError: pass
    else: NATIVE.__available__ |= {'WOW64'}

except ImportError:
    Log.info("{:s} : Unable to import the 'ctypes' module. This will prevent the availability of providers that are for the Windows platforms.".format(__name__))

except OSError as E:
    Log.info("{:s} : Unable to load the required libraries into the current process ({!s}). Providers for the Windows platform will be unavailable.".format(__name__, E))

### Now we'll define the classes based on whatever APIs we were able to build ctypes for.
try:
    if 'WIN32ERROR' not in NATIVE.__available__:
        raise OSError

    class win32error:
        @staticmethod
        def getLastErrorTuple():
            errorCode = NATIVE.K32.GetLastError()
            p_string = ctypes.c_void_p(0)

            # FORMAT_MESSAGE_
            ALLOCATE_BUFFER = 0x100
            FROM_SYSTEM = 0x1000
            res = NATIVE.K32.FormatMessageA(
                ALLOCATE_BUFFER | FROM_SYSTEM, 0, errorCode,
                0, ctypes.pointer(p_string), 0, None
            )
            res = ctypes.cast(p_string, ctypes.c_char_p)
            errorString = builtins.bytes(res.value)
            res = NATIVE.K32.LocalFree(res)
            if res == 0:
                raise AssertionError("KERNEL32.dll!LocalFree failed. Error {:#0{:d}x}.".format(NATIVE.K32.GetLastError(), 2 + 8))

            return (errorCode, errorString)

        @staticmethod
        def getLastErrorString():
            code, string = getLastErrorTuple()
            return string

    class WindowsError(OSError):
        def __init__(self, *args):
            code, string = win32error.getLastErrorTuple()
            super(WindowsError, self).__init__((code, string), args)

except OSError:
    Log.info("{:s} : Error handling for the Windows platform (`{:s}`) will be unavailable.".format(__name__, 'WindowsError'))

class WindowsWithHandle(base):
    '''Windows provider base class.'''
    def __init__(self, handle=None, address=0):
        self.__handle__ = handle
        self.__address__ = address

    @classmethod
    def read_handle(cls, handle, address, amount):
        raise NotImplementedError("Current provider {!s} does not implement this method.".format(cls))

    @classmethod
    def write_handle(cls, handle, address, data):
        raise NotImplementedError("Current provider {!s} does not implement this method.".format(cls))

    @classmethod
    def close_handle(cls, handle):
        raise NotImplementedError("Current provider {!s} does not implement this method.".format(cls))

    @classmethod
    def seek_handle(cls, handle, old, new):
        raise NotImplementedError("Current provider {!s} does not implement this method.".format(cls))

    @utils.mapexception(any=error.ProviderError)
    def seek(self, offset):
        '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
        handle, address = self.__handle__, self.__address__
        new_offset = self.seek_handle(handle, address, offset)
        result, self.__address__ = address, new_offset
        return result

    @utils.mapexception(any=error.ProviderError, ignored=(error.ConsumeError,))
    def consume(self, amount):
        '''Consume ``amount`` bytes from the provider.'''
        if amount < 0:
            raise error.UserError(self, 'consume', message="tried to consume a negative number of bytes ({:x}:{:+x}) from {!s}".format(self.address, amount, self))

        handle, address = self.__handle__, self.__address__

        try:
            result, buffer = self.read_handle(handle, address, amount)
        except Exception as E:
            raise error.ConsumeError(self, address, amount)

        if result != amount:
            raise error.ConsumeError(self, address, amount, result)

        self.__address__ = address + result
        return builtins.memoryview(buffer).tobytes()

    @utils.mapexception(any=error.ProviderError, ignored=(error.StoreError,))
    def store(self, data):
        '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
        handle, address = self.__handle__, self.__address__

        try:
            result, buffer = self.write_handle(handle, address, data)
        except Exception as E:
            raise error.StoreError(self, address, len(data))

        if result != len(data):
            raise error.StoreError(self, address, len(data), written=result)

        self.__address__ = address + result
        return result

    @utils.mapexception(any=error.ProviderError)
    def close(self):
        handle = self.__handle__
        result, new_handle = self.close_handle(handle)
        self.__handle__ = new_handle
        return result

### Windows Process API
try:
    if 'PROCESS' not in NATIVE.__available__:
        raise OSError

    class WindowsProcessHandle(memorybase, WindowsWithHandle):
        '''Windows memory provider that will use a process handle in order to access memory.'''
        def __init__(self, handle):
            super(WindowsProcessHandle, self).__init__(handle)

        @classmethod
        def read_handle(cls, handle, address, amount):
            NumberOfBytesRead = NATIVE.SIZE_T()
            buffer_t = ctypes.c_char * amount

            buffer = buffer_t()
            result = NATIVE.K32.ReadProcessMemory(handle, address, ctypes.pointer(buffer), amount, ctypes.pointer(NumberOfBytesRead))
            if not result:
                raise OSError("Unable to read from address {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + amount, amount, handle))
            return NumberOfBytesRead.value, buffer

        @classmethod
        def write_handle(cls, handle, address, data):
            NumberOfBytesWritten = NATIVE.SIZE_T()

            buffer_t = ctypes.c_char * len(data)
            buffer = buffer_t(data)

            result = NATIVE.K32.WriteProcessMemory(handle, address, ctypes.pointer(buffer), len(data), ctypes.pointer(NumberOfBytesWritten))
            if not result:
                raise OSError("Unable to write to address {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + len(data), len(data), handle))
            return NumberOfBytesWritten.value, buffer

        @classmethod
        def close_handle(cls, handle):
            result = NATIVE.K32.CloseHandle(handle)
            if not result:
                if 'WIN32ERROR' in NATIVE.__available__:
                    raise OSError(win32error.getLastErrorTuple())
                raise OSError("Unable to close the specified handle {:#x}.".format(handle))
            return result, None

        @classmethod
        def seek_handle(cls, handle, old, new):
            return new

except OSError:
    Log.info("{:s} : Opening a remote process by its handle on the Windows platform (`{:s}`) will be unavailable.".format(__name__, 'WindowsProcessHandle'))

try:
    if 'WOW64' not in NATIVE.__available__:
        raise OSError

    class WindowsProcessHandleWow64(WindowsProcessHandle):
        '''Windows memory provider that will use a process handle in order to access memory.'''

        @classmethod
        def read_handle(cls, handle, address, amount):
            NumberOfBytesRead = NATIVE.ULONG64()
            buffer_t = ctypes.c_char * amount

            buffer = buffer_t()
            result = NATIVE.NT.NtWow64ReadVirtualMemory64(handle, address, ctypes.pointer(buffer), amount, ctypes.pointer(NumberOfBytesRead))
            if result != NATIVE.CONST.STATUS_SUCCESS:
                raise OSError("Unable to read from address {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + amount, amount, handle))
            return NumberOfBytesRead.value, buffer

        @classmethod
        def write_handle(cls, handle, address, data):
            NumberOfBytesWritten = NATIVE.ULONG64()

            buffer_t = ctypes.c_char * len(data)
            buffer = buffer_t(data)

            result = NATIVE.NT.NtWow64WriteVirtualMemory64(handle, address, ctypes.pointer(buffer), len(data), ctypes.pointer(NumberOfBytesWritten))
            if result != NATIVE.CONST.STATUS_SUCCESS:
                raise OSError("Unable to write to address {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + len(data), len(data), handle))
            return NumberOfBytesWritten.value, buffer

except OSError:
    Log.info("{:s} : Opening a remote wow64 process by its handle on the Windows platform (`{:s}`) will be unavailable.".format(__name__, 'WindowsProcessHandleWow64'))

except AttributeError:
    pass

try:
    if 'PROCESS' not in NATIVE.__available__:
        raise OSError

    def WindowsProcessId(pid, **attributes):
        '''Return a provider that allows one to read/write from memory owned by the specified windows process ``pid``.'''
        sysinfo = NATIVE.SYSTEM_INFO()
        NATIVE.K32.GetNativeSystemInfo(ctypes.pointer(sysinfo))

        wProcessorArchitecture = sysinfo.wProcessorArchitecture
        SYS64 = wProcessorArchitecture in {NATIVE.CONST.PROCESSOR_ARCHITECTURE_AMD64, NATIVE.CONST.PROCESSOR_ARCHITECTURE_ARM64, NATIVE.CONST.PROCESSOR_ARCHITECTURE_IA64}

        current = NATIVE.K32.GetCurrentProcess()
        current_wow64_ = NATIVE.BOOL()
        current_wow64 = current_wow64_.value if 'WOW64' in NATIVE.__available__ and NATIVE.K32.IsWow64Process(current, ctypes.pointer(current_wow64_)) else False

        flags = NATIVE.CONST.PROCESS_QUERY_INFORMATION | NATIVE.CONST.PROCESS_VM_WRITE | NATIVE.CONST.PROCESS_VM_READ
        other = NATIVE.K32.OpenProcess(flags, False, pid)

        if not other:
            if 'WIN32ERROR' in NATIVE.__available__:
                raise OSError(win32error.getLastErrorTuple())
            raise OSError("Unable to open a handle to the process id {:d} ({:#x}).".format(pid, pid))

        other_wow64_ = NATIVE.BOOL()
        other_wow64 = other_wow64_.value if 'WOW64' in NATIVE.__available__ and NATIVE.K32.IsWow64Process(other, ctypes.pointer(other_wow64_)) else False

        if 'WOW64' in NATIVE.__available__:
            return WindowsProcessHandleWow64(other) if current_wow64 and not other_wow64 else WindowsProcessHandle(other)
        return WindowsProcessHandle(other)

except OSError:
    Log.info("{:s} : Opening a remote process by its id on the Windows platform (`{:s}`) will be unavailable.".format(__name__, 'WindowsProcessId'))

### Windows File API
try:
    if 'FILE' not in NATIVE.__available__:
        raise OSError

    class WindowsFile(WindowsWithHandle):
        '''A provider that uses the Windows File API.'''
        def __init__(self, filename, mode='rb'):
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

            result = NATIVE.K32.CreateFileA(
                filename, amode, smode, None, cmode,
                FILE_ATTRIBUTE_NORMAL, None
            )
            if result == INVALID_HANDLE_VALUE:
                raise OSError(win32error.getLastErrorTuple())

            super(WindowsFile, self).__init__(result)

        @classmethod
        def seek_handle(cls, handle, old, new):
            distance, resultDistance = ctypes.c_longlong(new), ctypes.c_longlong(new)
            FILE_BEGIN = 0
            result = NATIVE.K32.SetFilePointerEx(
                handle, distance, ctypes.byref(resultDistance),
                FILE_BEGIN
            )
            if not result:
                if 'WIN32ERROR' in NATIVE.__available__:
                    raise OSError(win32error.getLastErrorTuple())
                raise OSError("Unable to seek from offset {:#x} to {:#x} ({:+#x}) with handle {:#x}.".format(old, new, new - old, handle))
            return resultDistance.value

        @classmethod
        def read_handle(cls, handle, address, amount):
            buffer_t = ctypes.c_char * amount
            resultBuffer = buffer_t()

            amount, resultAmount = ctypes.c_ulong(amount), ctypes.c_ulong(amount)
            result = NATIVE.K32.ReadFile(
                handle, ctypes.pointer(resultBuffer),
                amount, ctypes.pointer(resultAmount),
                None
            )
            if not result:
                if 'WIN32ERROR' in NATIVE.__available__:
                    raise OSError(win32error.getLastErrorTuple())
                raise OSError("Unable to read from offset {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + amount, amount, handle))
            return resultAmount.value, resultBuffer

        @classmethod
        def write_handle(cls, handle, address, data):
            buffer_t = ctypes.c_char * len(data)
            buffer = buffer_t(data)
            resultWritten = ctypes.c_ulong()

            result = NATIVE.K32.WriteFile(
                handle, buffer,
                len(data), ctypes.pointer(resultWritten),
                None
            )
            if not result:
                if 'WIN32ERROR' in NATIVE.__available__:
                    raise OSError(win32error.getLastErrorTuple())
                raise OSError("Unable to write to offset {:#x}..{:#x} ({:+#x}) with handle {:#x}.".format(address, address + amount, amount, handle))
            return resultWritten.value, buffer

        @classmethod
        def close_handle(cls, handle):
            result = NATIVE.K32.CloseHandle(self.handle)
            if not result:
                if 'WIN32ERROR' in NATIVE.__available__:
                    raise OSError(win32error.getLastErrorTuple())
                raise OSError("Unable to close the specified handle {:#x}.".format(handle))
            return result, None

except OSError:
    Log.info("{:s} : Opening a file using the native api on the Windows platform (`{:s}`) will be unavailable.".format(__name__, 'WindowsFile'))

try:
    _ = 'idaapi' in sys.modules

    import idaapi as __idaapi__
    class Ida(debuggerbase):
        '''A provider that uses IDA Pro's API for reading/writing to the database.'''

        class __api__(object):
            """
            Static class for abstracting around IDA's API prior to 7.0,
            and 7.0 or later.
            """
            BADADDR = __idaapi__.BADADDR

            if hasattr(__idaapi__, 'get_many_bytes'):
                get_bytes = staticmethod(__idaapi__.get_many_bytes)
            elif hasattr(__idaapi__, 'get_bytes'):
                get_bytes = staticmethod(__idaapi__.get_bytes)
            else:
                raise ImportError('get_bytes')

            if hasattr(__idaapi__, 'get_nlist_ea'):
                get_nlist_ea = staticmethod(__idaapi__.get_nlist_ea)
            else:
                raise ImportError('get_nlist_ea')

            if hasattr(__idaapi__, 'get_nlist_size'):
                get_nlist_size = staticmethod(__idaapi__.get_nlist_size)
            else:
                raise ImportError('get_nlist_size')

            if hasattr(__idaapi__, 'getseg'):
                getseg = staticmethod(__idaapi__.getseg)
            else:
                raise ImportError('getseg')

            if hasattr(__idaapi__, 'patch_many_bytes'):
                patch_bytes = staticmethod(__idaapi__.patch_many_bytes)
            elif hasattr(__idaapi__, 'patch_bytes'):
                patch_bytes = staticmethod(__idaapi__.patch_bytes)
            else:
                raise ImportError('patch_bytes')

            if hasattr(__idaapi__, 'put_many_bytes'):
                put_bytes = staticmethod(__idaapi__.put_many_bytes)
            elif hasattr(__idaapi__, 'put_bytes'):
                put_bytes = staticmethod(__idaapi__.put_bytes)
            else:
                raise ImportError('put_bytes')

            if hasattr(__idaapi__, 'isEnabled'):
                is_mapped = staticmethod(__idaapi__.isEnabled)
            elif hasattr(__idaapi__, 'is_mapped'):
                is_mapped = staticmethod(__idaapi__.is_mapped)
            else:
                raise ImportError('is_mapped')

            if hasattr(__idaapi__, 'get_imagebase'):
                get_imagebase = staticmethod(__idaapi__.get_imagebase)
            else:
                raise ImportError('get_imagebase')

            if hasattr(__idaapi__, 'get_flags'):
                get_flags = staticmethod(__idaapi__.get_flags)
            else:
                raise ImportError('get_flags')

            if hasattr(__idaapi__, 'FF_IVL'):
                FF_IVL = staticmethod(__idaapi__.FF_IVL)
            else:
                raise ImportError('FF_IVL')

            if hasattr(__idaapi__, 'get_nlist_name'):
                get_nlist_name = staticmethod(__idaapi__.get_nlist_name)
            else:
                raise ImportError('get_nlist_name')

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
                return b''.join([cls.read(offset, half, padding=padding), cls.read(offset + half, half + size % 2, padding=padding)])
            if cls.__api__.is_mapped(offset):
                return b'' if size == 0 else (padding * size) if (cls.__api__.getFlags(offset) & cls.__api__.FF_IVL) == 0 else cls.__api__.get_many_bytes(offset, size)
            raise Exception((offset, size))

        @classmethod
        def expr(cls, string):
            index = (i for i in range(cls.__api__.get_nlist_size()) if string == cls.__api__.get_nlist_name(i))
            try:
                res = cls.__api__.get_nlist_ea(utils.next(index))

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
            '''Consume ``amount`` bytes from the provider.'''
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

    import binaryninja as __binaryninja__
    class Binja(debuggerbase):
        '''A provider that uses Binary Ninja's BinaryViewType API for reading/writing from an address space.'''
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

    import _PyDbgEng as __PyDbgEng__
    class PyDbgEng(debuggerbase):
        '''A provider that uses the PyDbgEng.pyd module to interact with the memory of the current debugged process.'''

        offset = 0
        def __init__(self, client=None):
            self.client = client

        @classmethod
        def connect(cls, remote):
            if remote is None:
                result = __PyDbgEng__.Create()
            elif isinstance(remote, tuple):
                host, port = client
                result = __PyDbgEng__.Connect("tcp:port={}, server={}".format(port, host))
            elif isinstance(remote, dict):
                result = __PyDbgEng__.Connect("tcp:port={port}, server={host}".format(**client))
            elif isinstance(remote, utils.string_types):
                result = __PyDbgEng__.Connect(client)
            return cls(result)

        @classmethod
        def connectprocessserver(cls, remote):
            result = __PyDbgEng__.ConnectProcessServer(remoteOptions=remote)
            return cls(result)

        def connectkernel(self, remote):
            if remote is None:
                result = __PyDbgEng__.AttachKernel(flags=__PyDbgEng__.ATTACH_LOCAL_KERNEL)
            else:
                result = __PyDbgEng__.AttachKernel(flags=0, connectOptions=remote)
            return cls(result)

        @classmethod
        def expr(cls, string):
            control = __PyDbgEng__.IDebugControl
            dtype = DEBUG_VALUE_INT32
            return control.Evaluate(string, dtype)

        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            res, self.offset = self.offset, offset
            return res

        def consume(self, amount):
            '''Consume ``amount`` bytes from the provider.'''
            try:
                result = self.client.DataSpaces.Virtual.Read(self.offset, amount)

            # Unable to read {:+d} bytes from address {:x}".format(amount, self.offset))
            except RuntimeError:
                raise error.ConsumeError(self, self.offset, amount)
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
    import pykd as __pykd__
    class Pykd(debuggerbase):
        '''A provider that uses the Pykd library to interact with the memory of a debugged process.'''
        def __init__(self):
            self.address = 0

        @classmethod
        def expr(cls, string):
            return __pykd__.expr(string)

        def seek(self, offset):
            '''Seek to the specified ``offset``. Returns the last offset before it was modified.'''
            # FIXME: check to see if we're at an invalid address
            res, self.address = self.address, offset
            return res

        def consume(self, amount):
            '''Consume ``amount`` bytes from the provider.'''
            if amount == 0:
                return b''
            try:
                data = __pykd__.loadBytes(self.address, amount)
                res = bytearray(data)
            except Exception:
                raise error.ConsumeError(self, self.address, amount, 0)
            self.address += amount
            return builtins.bytes(res)

        def store(self, data):
            '''Store ``data`` at the current offset. Returns the number of bytes successfully written.'''
            if not len(data):
                return 0
            amount, argh = len(data), bytearray(data)
            items = [octet for octet in argh]
            try:
                __pykd__.writeBytes(self.address, items)
            except Exception:
                raise error.StoreError(self, self.address, len(data))
            self.address += amount
            return amount

    Log.info("{:s} : Successfully loaded the `Pykd` provider.".format(__name__))
    if _: DEFAULT.append(Pykd)

except ImportError:
    Log.info("{:s} : Unable to import the 'pykd' module. Failed to define the `Pykd` provider.".format(__name__))

try:
    _ = 'lldb' in sys.modules

    import lldb as __lldb__
    class lldb(debuggerbase):
        def __init__(self, sbprocess=None):
            self.__process = sbprocess or __lldb__.process
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
            process, err = self.__process, __lldb__.SBError()
            if amount > 0:
                data = process.ReadMemory(self.address, amount, err)
                if err.Fail() or len(data) != amount:
                    raise error.ConsumeError(self, self.address, amount)
                self.address += len(data)
                return builtins.bytes(data)
            return b''

        def store(self, data):
            process, err = self.__process, __lldb__.SBError()
            amount = process.WriteMemory(self.address, builtins.bytes(data), err)
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

    import gdb as __gdb__
    class gdb(debuggerbase):
        def __init__(self, inferior=None):
            gdb = __gdb__
            self.inferior = inferior or gdb.selected_inferior()
            self.address = 0

        @classmethod
        def expr(cls, expression):
            gdb = __gdb__

            try:
                type = gdb.lookup_type('intptr_t')
            except gdb.error as E:
                message, = E.args
                raise error.TypeError(cls, 'expr', message=message)

            value = gdb.parse_and_eval(expression)
            res = value.cast(type)
            return int(res)

        def seek(self, offset):
            res, self.address = self.address, offset
            return res

        def consume(self, amount):
            gdb, process = __gdb__, self.inferior
            try:
                mem = process.read_memory(self.address, amount)
            except gdb.MemoryError:
                mem = None
            if mem is None or mem.nbytes != amount:
                raise error.ConsumeError(self, self.address, amount)
            self.address += mem.nbytes
            return mem.tobytes()

        def store(self, data):
            gdb, process = __gdb__, self.inferior
            try:
                process.write_memory(self.address, data)
            except gdb.MemoryError:
                raise error.StoreError(self, self.address, len(data))
            self.address += len(data)
            return len(data)

    Log.info("{:s} : Successfully loaded the `gdb` provider.".format(__name__))
    if _: DEFAULT.append(gdb)

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
            '''Consume ``amount`` bytes from the provider.'''
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

        @classmethod
        def _read(cls, address, length):
            block_t = ctypes.c_char * length
            pointer_t = ctypes.POINTER(block_t)
            voidpointer = ctypes.c_void_p(address)
            blockpointer = ctypes.cast(voidpointer, pointer_t)
            if length:
                return builtins.memoryview(blockpointer.contents).tobytes()
            if not address:
                Log.warning("{:s}._read({:#x}, {:+d}): dereferenced a NULL pointer ({:#x}) to read {:d} bytes.".format(cls.__name__, address, length, address, length))
            return builtins.memoryview(b'').tobytes()

        @classmethod
        def _write(cls, address, value):
            block_t = ctypes.c_char * len(value)
            pointer_t = ctypes.POINTER(block_t)
            voidpointer = ctypes.c_void_p(address)
            blockpointer = ctypes.cast(voidpointer, pointer_t)
            if value:
                for i, item in enumerate(value):
                    blockpointer.contents[i] = item
                return 1 + i
            Log.warning("{:s}._write({:#x}, {!r}): dereferenced a NULL pointer ({:#x}) to write {:d} bytes.".format(cls.__name__, address, value, address, len(value)))
            return 0

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
    import ptypes, os, random, tempfile, builtins
    from ptypes import ptype,parray, pint, pbinary, provider

    from builtins import *

    class temporaryname(object):
        def __enter__(self, *args):
            self.name = tempfile.mktemp()
            return self.name
        def __exit__(self, *args):
            try: os.unlink(self.name)
            except Exception: pass
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
            except Exception:
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
            except Exception:
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
    def test_bytearray_read():
        data = bytearray(b'ABCD')
        z = provider.bytes(data)
        z.seek(2)
        if bytes(z.consume(2)) == b'CD' and z.offset == 4:
            raise Success

    @TestCase
    def test_bytearray_write():
        data = bytearray(b'ABCDEF')
        z = provider.bytes(data)
        z.seek(2)
        z.store(b'FF')
        if z.offset == 4 and bytes(z.consume(2)) == b'EF' and bytes(data) == b'ABFFEF':
            raise Success

    @TestCase
    def test_proxy_write_container():
        class t1(parray.type):
            _object_ = pint.uint8_t
            length = 0x10*4

        class t2(parray.type):
            _object_ = pint.uint32_t
            length = 0x10

        source = t1().set([0x41]*4 + [0x42]*4 + [0x43] * (4 * 0xe))
        res = t2(source=provider.proxy(source)).l
        res[1].set(0x0d0e0a0d)
        res.commit()
        if b''.join(item.serialize() for item in source[:0xc]) == b'AAAA\x0d\x0a\x0e\x0dCCCC':
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

        source = t1(source=ptypes.prov.bytes(b'abcABCdefDEFghiGHIjlkJLK')).l
        res = t2(source=ptypes.prov.proxy(source)).l
        source[0].set((0x41,0x41,0x41))
        source.commit()
        res[1].set(0x42424242)
        res[1].commit()
        if source[0].serialize() == b'AAA' and source[1].serialize() == b'ABB' and [source[2]['a']] == [item for item in bytearray(b'B')] and [source[2]['b']] == [item for item in bytearray(b'B')]:
            raise Success

    @TestCase
    def test_disorder_traverse_exact():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(0, 32)]
        if len(items) == 8:
            raise Success

    @TestCase
    def test_disorder_traverse_partial_start():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(2, 32)]
        if len(items) == 8:
            raise Success

    @TestCase
    def test_disorder_traverse_partial_stop():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(0, 30)]
        if len(items) == 8:
            raise Success

    @TestCase
    def test_disorder_traverse_partial_both():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(2, 30)]
        if len(items) == 8:
            raise Success

    @TestCase
    def test_disorder_traverse_exact_center():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(12, 20)]
        if len(items) == 2:
            raise Success

    @TestCase
    def test_disorder_traverse_partial_center():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(15, 17)]
        if len(items) == 2:
            raise Success

    @TestCase
    def test_disorder_traverse_single():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(16, 17)]
        if len(items) == 1:
            raise Success

    @TestCase
    def test_disorder_traverse_empty():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(16, 16)]
        if len(items) == 0:
            raise Success

    @TestCase
    def test_disorder_traverse_empty_busted():
        u32 = pint.uint32_t
        backing = [item(offset=4*i).a for i, item in enumerate([u32] * 8)]
        fragmented = ptypes.prov.disorderly(backing)
        items = [item for item in fragmented.__traverse__(20, 14)]
        if len(items) == 0:
            raise Success

    @TestCase
    def test_disorder_load():
        u32 = pint.uint32_t
        backing = bytearray(range(32))
        source = ptypes.prov.bytes(backing)
        backwards = [u32().load(source=source, offset=offset) for offset in range(0, 32, 4)][::-1]
        fragmented = ptypes.prov.disorderly(backwards)
        argh = parray.type(length=8, _object_=u32, source=fragmented).l
        if all(x.int() == y.int() for x, y in zip(argh, backwards)):
            raise Success

    @TestCase
    def test_disorder_commit():
        u32 = pint.uint32_t
        backing = bytearray(range(32))
        source = ptypes.prov.bytes(backing)
        items = parray.type(length=8, _object_=u32, source=source).l
        backwards = [item for item in reversed(items)]

        fragmented = ptypes.prov.disorderly(backwards, autocommit={})

        x = parray.type(length=8, _object_=u32, source=fragmented).l
        for i, item in enumerate(x):
            shifted = i + 0x41
            item.set(shifted + shifted*pow(2,8) + shifted*pow(2,16) + shifted*pow(2,24))

        if backing != bytearray(range(32)):
            raise Failure

        # we can do this because of autocommit, otherwise we'd need to
        # move through the types directly.
        x.commit()

        if backing == bytearray(itertools.chain(*(4 * [i] for i in reversed(range(0x41, 0x49))))):
            raise Success

    try:
        import nt, multiprocessing, os, ctypes
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

    import os, tempfile

    @TestCase
    def test_boundaries_file_readexact():
        filename = tempfile.mktemp()
        with open(filename, 'wb') as out:
            out.write(b'1234')

        source = provider.file(filename, 'rb')
        start = source.seek(0)
        try:
            if start == 0 and source.consume(4) == b'1234' and source.seek(4) == 4:
                raise Success
        finally:
            source.close(), os.unlink(filename)
        raise Failure

    @TestCase
    def test_boundaries_file_readsmall():
        filename = tempfile.mktemp()
        with open(filename, 'wb') as out:
            out.write(b'1234')

        source = provider.file(filename, 'rb')
        start = source.seek(0)
        try:
            if start == 0 and source.consume(16) == b'1234' and source.seek(4) == 0:
                raise Success
        finally:
            source.close(), os.unlink(filename)
        raise Failure

    @TestCase
    def test_boundaries_file_readoob():
        filename = tempfile.mktemp()
        with open(filename, 'wb') as out:
            out.write(b'1234')

        source = provider.file(filename, 'rb')
        start = source.seek(4)
        try:
            source.consume(1)

        except error.ConsumeError:
            if start == 0 and source.seek(4) == 4:
                raise Success
        finally:
            source.close(), os.unlink(filename)
        raise Failure

    @TestCase
    def test_boundaries_file_readedge():
        filename = tempfile.mktemp()
        with open(filename, 'wb') as out:
            out.write(b'1234')

        source = provider.file(filename, 'rb')
        start = source.seek(4)
        try:
            if source.consume(0) == b'':
                raise Success
        finally:
            source.close(), os.unlink(filename)
        raise Failure

    @TestCase
    def test_boundaries_file_readedgeoob():
        filename = tempfile.mktemp()
        with open(filename, 'wb') as out:
            out.write(b'1234')

        source = provider.file(filename, 'rb')
        start = source.seek(64)
        try:
            if source.consume(0) == b'':
                raise Success
        finally:
            source.close(), os.unlink(filename)
        raise Failure

    @TestCase
    def test_boundaries_bytes_readexact():
        source = provider.bytes(b'1234')
        start = source.seek(0)
        if start == 0 and source.consume(4) == b'1234' and source.seek(4) == 4:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_bytes_readsmall():
        source = provider.bytes(b'1234')
        start = source.seek(0)
        if start == 0 and source.consume(16) == b'1234' and source.seek(4) == 0:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_bytes_readoob():
        source = provider.bytes(b'1234')
        start = source.seek(4)
        try:
            source.consume(1)
        except error.ConsumeError:
            if start == 0 and source.seek(4) == 4:
                raise Success
        raise Failure

    @TestCase
    def test_boundaries_bytes_readedge():
        source = provider.bytes(b'1234')
        start = source.seek(4)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_bytes_readedgeoob():
        source = provider.bytes(b'1234')
        start = source.seek(64)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_proxy_readexact():
        block = ptype.type().set(b'1234')
        source = provider.proxy(block)
        start = source.seek(0)
        if start == 0 and source.consume(4) == b'1234' and source.seek(4) == 4:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_proxy_readsmall():
        block = ptype.type().set(b'1234')
        source = provider.proxy(block)
        start = source.seek(0)
        if start == 0 and source.consume(16) == b'1234' and source.seek(4) == 0:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_proxy_readoob():
        block = ptype.type().set(b'1234')
        source = provider.proxy(block)
        start = source.seek(4)
        try:
            source.consume(1)
        except error.ConsumeError:
            if start == 0 and source.seek(4) == 4:
                raise Success
        raise Failure

    @TestCase
    def test_boundaries_proxy_readedge():
        block = ptype.type().set(b'1234')
        source = provider.proxy(block)
        start = source.seek(4)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_proxy_readedgeoob():
        block = ptype.type().set(b'1234')
        source = provider.proxy(block)
        start = source.seek(64)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder1_readexact():
        contiguous = [ptype.block().set(b'1234')]
        source = provider.disorderly(contiguous)
        start = source.seek(0)
        if start == 0 and source.consume(4) == b'1234' and source.seek(4) == 4:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder1_readsmall():
        contiguous = [ptype.block().set(b'1234')]
        source = provider.disorderly(contiguous)
        start = source.seek(0)
        if start == 0 and source.consume(16) == b'1234' and source.seek(4) == 0:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder1_readoob():
        contiguous = [ptype.block().set(b'1234')]
        source = provider.disorderly(contiguous)
        start = source.seek(4)
        try:
            source.consume(1)
        except error.ConsumeError:
            if start == 0 and source.seek(4) == 4:
                raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder1_readedge():
        contiguous = [ptype.block().set(b'1234')]
        source = provider.disorderly(contiguous)
        start = source.seek(4)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder1_readedgeoob():
        contiguous = [ptype.block().set(b'1234')]
        source = provider.disorderly(contiguous)
        start = source.seek(64)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder2_readexact():
        s = b'1234'
        contiguous = [ptype.block().set(s[index : index + 1]) for index, _ in enumerate(s)]
        source = provider.disorderly(contiguous)
        start = source.seek(0)
        if start == 0 and source.consume(4) == b'1234' and source.seek(4) == 4:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder2_readsmall():
        s = b'1234'
        contiguous = [ptype.block().set(s[index : index + 1]) for index, _ in enumerate(s)]
        source = provider.disorderly(contiguous)
        start = source.seek(0)
        if start == 0 and source.consume(16) == b'1234' and source.seek(4) == 0:
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder2_readoob():
        s = b'1234'
        contiguous = [ptype.block().set(s[index : index + 1]) for index, _ in enumerate(s)]
        source = provider.disorderly(contiguous)
        start = source.seek(4)
        try:
            source.consume(1)
        except error.ConsumeError:
            if start == 0 and source.seek(4) == 4:
                raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder2_readedge():
        s = b'1234'
        contiguous = [ptype.block().set(s[index : index + 1]) for index, _ in enumerate(s)]
        source = provider.disorderly(contiguous)
        start = source.seek(4)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_boundaries_disorder2_readedgeoob():
        s = b'1234'
        contiguous = [ptype.block().set(s[index : index + 1]) for index, _ in enumerate(s)]
        source = provider.disorderly(contiguous)
        start = source.seek(64)
        if source.consume(0) == b'':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_nonoverlap_1():
        u32 = pint.uint32_t
        argh = parray.type(length=4, _object_=u32).a
        res = ptypes.prov.proxy.store_range(argh, 0, b'AAAAAAAA')
        if res == 8 and argh.serialize() == b'AAAAAAAA\0\0\0\0\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_nonoverlap_2():
        u32 = pint.uint32_t
        argh = parray.type(length=4, _object_=u32).a
        res = ptypes.prov.proxy.store_range(argh, 4, b'AAAAAAAA')
        if res == 8 and argh.serialize() == b'\0\0\0\0AAAAAAAA\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_nonoverlap_3():
        u8 = pint.uint8_t
        argh = parray.type(length=0x10, _object_=u8).a
        res = ptypes.prov.proxy.store_range(argh, 12, b'AAAA')
        if res == 4 and argh.serialize() == b'\0\0\0\0\0\0\0\0\0\0\0\0AAAA':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_nonoverlap_offset_1():
        u32 = pint.uint32_t
        argh = parray.type(length=4, _object_=u32, offset=0x12345).a
        res = ptypes.prov.proxy.store_range(argh, 4, b'AAAAAAAA')
        if res == 8 and argh.serialize() == b'\0\0\0\0AAAAAAAA\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_nonoverlap_offset_2():
        u8 = pint.uint8_t
        argh = parray.type(length=0x10, _object_=u8, offset=-0x1000).a
        res = ptypes.prov.proxy.store_range(argh, 12, b'AAAA')
        if res == 4 and argh.serialize() == b'\0\0\0\0\0\0\0\0\0\0\0\0AAAA':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_overlap_1():
        u32 = pint.uint32_t
        argh = parray.type(length=4, _object_=u32).a
        res = ptypes.prov.proxy.store_range(argh, 2, b'AAAAAAAA')
        if res == 8 and argh.serialize() == b'\0\0AAAAAAAA\0\0\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_overlap_2():
        u64 = pint.uint64_t
        argh = parray.type(length=2, _object_=u64).a
        res = ptypes.prov.proxy.store_range(argh, 2, b'AAAA')
        if res == 4 and argh.serialize() == b'\0\0AAAA\0\0\0\0\0\0\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_overlap_offset_1():
        u32 = pint.uint32_t
        argh = parray.type(length=4, _object_=u32, offset=0x1400).a
        res = ptypes.prov.proxy.store_range(argh, 2, b'AAAAAAAA')
        if res == 8 and argh.serialize() == b'\0\0AAAAAAAA\0\0\0\0\0\0':
            raise Success
        raise Failure

    @TestCase
    def test_proxy_store_range_overlap_offset_2():
        u64 = pint.uint64_t
        argh = parray.type(length=2, _object_=u64, offset=-42).a
        res = ptypes.prov.proxy.store_range(argh, 2, b'AAAA')
        if res == 4 and argh.serialize() == b'\0\0AAAA\0\0\0\0\0\0\0\0\0\0':
            raise Success
        raise Failure

if __name__ == '__main__' and 0:
    from ptypes import ptype, parray, pstruct, pint, provider

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
        import array
        s = lambda x:array.array('c',x)
        a = provider.virtual()
        a.available = [0,5]
        a.data = {0:s('hello'),5:s('world')}
        a.flatten(0,5)
        if len(a.data[0]) == 10:
            raise Success

    @TestCase
    def test_consume():
        import array
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
