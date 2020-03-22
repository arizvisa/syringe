"""Array container types.

A parray.type is used to create a data structure that describes an list of a
particular subtype. The methods provided to a user expose a list-like interface
to the user. A parray.type's interface inherits from ptype.container and will
always have a .value that's a list. In most cases, a parray.type can be treated
as a python list.

The basic parray interface provides the following methods on top of the methods
required to provide an array-type interface.

    class interface(parray.type):
        # the sub-element that the array is composed of.
        _object_ = sub-type

        # the length of the array
        length = count

        def insert(self, index, object):
            '''Insert ``object`` into the array at the specified ``index``.'''

        def append(self, object):
            '''Appends the specified ``object`` to the end of the array type.'''

        def extend(self, iterable):
            '''Appends all the objects provided in ``iterable`` to the end of the array type.'''

        def pop(self, index):
            '''Removes and returns the instance at the specified index of the array.'''

There are a couple of array types that can be used to describe the different data structures
one may encounter. They are as following:

    parray.type -- The basic array type. /self.length// specifies it's length,
                   and /self._object_/ specifies it's subtype.

    parray.terminated -- An array type that is terminated by a specific element
                         type. In this array type, /self.length/ is initially
                         set to None due to the termination of this array being
                         defined by the result of a user-supplied
                         .isTerminator(sub-instance) method.

    parray.uninitialized -- An array type that will read until an error or other
                            kind of interrupt happens. The size of this type is
                            determined dynamically.

    parray.infinite -- An array type that will read indefinitely until it
                       consumes the blocksize of it's parent element or the
                       entirety of it's data source.

    parray.block -- An array type that will read elements until it reaches the
                    length of it's .blocksize() method. If a sub-element causes
                    the array to read past it's .blocksize(), the sub-element
                    will remain partially uninitialized.

Example usage:
    # define a basic type
    from ptypes import parray
    class type(parray.type):
        _object_ = subtype
        length = 4

    # define a terminated array
    class terminated(parray.terminated):
        _object_ = subtype
        def isTerminator(self, value):
            return value is sentineltype or value == sentinelvalue

    # define a block array
    class block(parray.block):
        _object_ = subtype
        def blocksize(self):
            return size-of-array

    # instantiate and load a type
    instance = type()
    instance.load()

    # fetch an element from the array
    print(instance[index])

    # print the length of the array
    print(len(instance))
"""
import six
import itertools,operator,functools

from . import ptype,utils,error,config
Config = config.defaults
Log = Config.log.getChild(__name__[len(__package__)+1:])
__all__ = 'type,terminated,infinite,block'.split(',')

class _parray_generic(ptype.container):
    '''provides the generic features expected out of an array'''
    def __contains__(self,v):
        '''D.__contains__(k) -> True if D has a field named k, else False'''
        return any(x is v for x in self.value)

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        if not self.initializedQ():
            return self.length
        return len(self.value)

    def insert(self, index, object):
        """Insert ``object`` into ``self`` at the specified ``index``.

        This will update the offsets within ``self``, so that all elements are
        contiguous when committing.
        """
        offset = self.value[index].getoffset()
        object.setoffset(offset, recurse=True)
        object.parent,object.source = self,None
        self.value.insert(index, object)

        for i in six.moves.range(index, len(self.value)):
            v = self.value[i]
            v.setoffset(offset, recurse=True)
            offset += v.blocksize()
        return

    def __append__(self, object):
        idx = len(self.value)
        offset = super(_parray_generic, self).__append__(object)
        offset = (self.value[idx - 1].getoffset() + self.value[idx - 1].size()) if idx > 0 else self.getoffset()
        self.value[idx].setoffset(offset)
        return offset

    def append(self, object):
        """Append ``object`` to a ``self``. Return the offset it was inserted at.

        This will update the offset of ``object`` so that it will appear at the
        end of the array.
        """
        return self.__append__(object)

    def extend(self, iterable):
        map(self.append, iterable)
        return self

    def pop(self, index=-1):
        """Remove the element at ``index`` or the last element in the array.

        This will update all the offsets within ``self`` so that all elements are
        contiguous.
        """

        # determine the correct index
        idx = self.value.index(self.value[index])
        res = self.value.pop(idx)

        offset = res.getoffset()
        for i,n in enumerate(self.value[idx:]):
            n.setoffset(offset, recurse=True)
            offset += n.blocksize()
        return res

    def __getindex__(self, index):
        return index

    def __delitem__(self, index):
        '''x.__delitem__(y) <==> del x[y]'''
        if isinstance(index, slice):
            origvalue = self.value[:]
            for idx in six.moves.range(*slice(index.start or 0, index.stop, index.step or 1).indices(index.stop)):
                realidx = self.__getindex__(idx)
                self.value.pop( self.value.index(origvalue[realidx]) )
            return origvalue.__getitem__(index)
        return self.pop(index)

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if isinstance(index, slice):
            ivalue = itertools.repeat(value) if isinstance(value, ptype.generic) else iter(value)
            res = self.value[:]
            for idx in six.moves.range(*slice(index.start or 0, index.stop, index.step or 1).indices(index.stop)):
                idx = self.__getindex__(idx)
                self.value[idx] = six.next(ivalue)
            return res.__getitem__(index)

        idx = self.__getindex__(index)
        result = super(_parray_generic, self).__setitem__(idx, value)
        result.__name__ = str(index)
        return result

    def __getitem__(self, index):
        '''x.__getitem__(y) <==> x[y]'''
        if isinstance(index, slice):
            result = [ self.value[ self.__getindex__(idx) ] for idx in six.moves.range(*index.indices(len(self))) ]
            t = ptype.clone(type, length=len(result), _object_=self._object_)
            return self.new(t, offset=result[0].getoffset() if len(result) else self.getoffset(), value=result)

        idx = self.__getindex__(index)
        ([None]*len(self))[idx]     # make python raise the correct exception if so..
        return super(_parray_generic, self).__getitem__(idx)

    def __element__(self):
        try: length = len(self)
        except: length = self.length or 0

        object = self._object_
        if object is None:
            res = '(untyped)'
        else:
            res = object.typename() if ptype.istype(object) else object.__name__

        return u"{:s}[{:d}]".format(res, length)

    def summary(self, **options):
        res = super(_parray_generic, self).summary(**options)
        return ' '.join((self.__element__(), res))

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        prop = ','.join(u"{:s}={!r}".format(k,v) for k,v in six.iteritems(self.properties()))
        result, element = self.repr(), self.__element__()

        # multiline (includes element description)
        if result.count('\n') > 0 or utils.callable_eq(self.repr, _parray_generic.details):
            result = result.rstrip('\n')
            if prop:
                return u"{:s} '{:s}' {{{:s}}} {:s}\n{:s}".format(utils.repr_class(self.classname()),self.name(),prop,element,result)
            return u"{:s} '{:s}' {:s}\n{:s}".format(utils.repr_class(self.classname()),self.name(),element,result)

        # if the user chose to not use the default summary, then prefix the element description.
        if any(utils.callable_eq(self.repr, item) for item in [_parray_generic.repr, _parray_generic.summary]):
            result = ' '.join((element,result))

        _hex,_precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(),self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

class type(_parray_generic):
    '''
    A container for managing ranges of a particular object.

    Settable properties:
        _object_:ptype.type<w>
            The type of the array
        length:int<w>
            The length of the array only used during initialization of the object
    '''
    _object_ = None     # subclass of ptype.type
    length = 0          # int

    # load ourselves lazily
    def __load_block(self, **attrs):
        offset = self.getoffset()
        for index in six.moves.range(self.length):
            n = self.new(self._object_, __name__=str(index), offset=offset, **attrs)
            self.value.append(n)
            offset += n.blocksize()
        return self

    # load ourselves incrementally
    def __load_container(self, **attrs):
        offset = self.getoffset()
        for index in six.moves.range(self.length):
            n = self.new(self._object_, __name__=str(index), offset=offset, **attrs)
            self.value.append(n)
            n.load()
            offset += n.blocksize()
        return self

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        result._object_ = self._object_
        result.length = self.length
        return result

    def alloc(self, fields=(), **attrs):
        result = super(type, self).alloc(**attrs)
        if len(fields) > 0 and isinstance(fields[0], tuple):
            for k, val in fields:
                idx = result.__getindex__(k)
                if ptype.istype(val) or ptype.isresolveable(val):
                    result.value[idx] = result.new(val).a
                elif isinstance(val, ptype.generic):
                    result.value[idx] = result.new(val)
                else:
                    result.value[idx].set(val)
                continue
        else:
            for idx, val in enumerate(fields):
                name = str(idx)
                if ptype.istype(val) or ptype.isresolveable(val):
                    result.value[idx] = result.new(val,__name__=name).a
                elif isinstance(val, ptype.generic):
                    result.value[idx] = result.new(val,__name__=name)
                else:
                    result.value[idx].set(val)
                continue

            # re-alloc elements that exist in the rest of the array
            for idx in six.moves.range(len(fields), len(result.value)):
                result.value[idx].a

        result.setoffset(self.getoffset(), recurse=True)
        return result

    def load(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                object = self._object_
                self.value = []

                # which kind of load are we
                if ptype.istype(object) and not ptype.iscontainer(object):
                    self.__load_block()

                elif ptype.iscontainer(object) or ptype.isresolveable(object):
                    self.__load_container()

                else:
                    Log.info("type.load : {:s} : Unable to load array due to an unknown element type ({!s}).".format(self.instance(), object))
            return super(type, self).load(**attrs)
        except error.LoadError as E:
            raise error.LoadError(self, exception=E)
        raise error.AssertionError(self, 'type.load')

    def __setvalue__(self, *values, **attrs):
        """Update self with the contents of the first argument in ``value``"""
        if not values:
            return self

        value, = values
        if self.initializedQ() and len(self) == len(value):
            return super(type, self).__setvalue__(*value)
        else:
            iterable = enumerate(value)

        length, self.value = len(self), []
        for idx, ivalue in iterable:
            if ptype.isresolveable(ivalue) or ptype.istype(ivalue):
                res = self.new(ivalue, __name__=str(idx)).a
            elif isinstance(ivalue, ptype.generic):
                res = ivalue
            else:
                res = self.new(self._object_, __name__=str(idx)).a.set(ivalue)
            self.value.append(res)

        # output a warning if the length is already set to something and the user explicitly changed it to something different.
        if length and length != len(self):
            Log.warn("type.__setvalue__ : {:s} : Length of array was explicitly changed ({:d} != {:d}).".format(self.instance(), length, len(self)))

        result = super(type, self).__setvalue__(*value)
        result.length = len(self)
        return self

    def __getstate__(self):
        return super(type, self).__getstate__(), self._object_, self.length

    def __setstate__(self, state):
        state, self._object_, self.length = state
        super(type, self).__setstate__(state)

class terminated(type):
    '''
    an array that terminates deserialization based on the value returned by
    .isTerminator()
    '''
    length = None
    def isTerminator(self, value):
        '''intended to be overloaded. should return True if element /value/ represents the end of the array.'''
        raise error.ImplementationError(self, 'terminated.isTerminator')

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        if self.length is None:
            if self.value is None:
                raise error.InitializationError(self, 'terminated.__len__')
            return len(self.value)
        return super(terminated, self).__len__()

    def alloc(self, fields=(), **attrs):
        attrs.setdefault('length', len(fields))
        attrs.setdefault('isTerminator', lambda value: False)
        return super(terminated, self).alloc(fields, **attrs)

    def load(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                forever = itertools.count() if self.length is None else six.moves.range(self.length)
                offset, self.value, n = self.getoffset(), [], None

                for index in forever:
                    n = self.new(self._object_,__name__=str(index),offset=offset)
                    self.value.append(n)
                    if self.isTerminator(n.load()):
                        break

                    size = n.blocksize()
                    if size <= 0 and Config.parray.break_on_zero_sized_element:
                        Log.warn("terminated.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), n.instance()))
                        break
                    if size < 0:
                        raise error.AssertionError(self, 'terminated.load', message="Element size for {:s} is < 0".format(n.classname()))
                    offset += size

        except (Exception, error.LoadError) as E:
            raise error.LoadError(self, exception=E)

        return self

    def initializedQ(self):
        '''Returns True if all elements excluding the last one (sentinel) are initialized'''

        # Check to see if array contains any elements
        if self.value is None:
            return False

        # Check if all elements are initialized.
        return all(n.initializedQ() for n in self.value)

class uninitialized(terminated):
    """An array that can contain uninitialized or partially initialized elements.

    This array determines it's size dynamically ignoring partially or
    uninitialized elements found near the end.
    """
    def size(self):
        if self.value is not None:
            return sum(n.size() for n in self.value if n.value is not None)
        raise error.InitializationError(self, 'uninitialized.size')

    def initializedQ(self):
        '''Returns True if all elements are partial or completely initialized.'''

        # Check to see if array contains any elements
        if self.value is None:
            return False

        # Grab all initialized elements near the beginning
        res = list(itertools.takewhile(operator.methodcaller('initializedQ'), self.value))

        # Return True if the whole thing is initialized or just the tail is uninitialized
        return len(res) == len(self.value) or all(not n.initializedQ() for n in self.value[len(res):])

class infinite(uninitialized):
    '''An array that reads elements until an exception or interrupt happens'''

    def __next_element(self, offset, **attrs):
        '''Utility method that returns a new element at a specified offset and loads it. intended to be overloaded.'''
        index = len(self.value)
        n = self.new(self._object_, __name__=str(index), offset=offset)
        try:
            n.load(**attrs)
        except (error.LoadError, error.InitializationError) as E:
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.info("infinite.__next_element : {:s} : Unable to read terminal element {:s} : {:s}".format(self.instance(), n.instance(), path))
        return n

    def isTerminator(self, value):
        return False

    def properties(self):
        res = super(infinite, self).properties()

        # Check if we're really an underloaded parray.infinite
        if res.get('underload', False):

            # If the size of our partially initialized last element is larger
            # than what our expected size should be, then it's not.
            if self.value[-1].blocksize() >= self.blocksize() - self.size():
                res.pop('underload')
            return res

        # That was all we wanted..
        return res

    def load(self, **attrs):
        # fallback to regular loading if user has hardcoded the length
        if attrs.get('length', self.length) is not None:
            return super(infinite, self).load(**attrs)

        with utils.assign(self, **attrs):
            offset, self.value = self.getoffset(), []

            current,maximum = 0,None if self.parent is None else self.parent.blocksize()
            try:
                while True if maximum is None else current < maximum:

                    # read next element at the current offset
                    n = self.__next_element(offset)
                    if not n.initializedQ():
                        Log.debug("infinite.load : {:s} : Element {:d} left partially initialized : {:s}".format(self.instance(), len(self.value), n.instance()))
                    self.value.append(n)

                    if not n.initializedQ():
                        break

                    if self.isTerminator(n):
                        break

                    # check sanity of element size
                    size = n.blocksize()
                    if size <= 0 and Config.parray.break_on_zero_sized_element:
                        Log.warn("infinite.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), n.instance()))
                        break
                    if size < 0:
                        raise error.AssertionError(self, 'infinite.load', message="Element size for {:s} is < 0".format(n.classname()))

                    # next iteration
                    offset += size
                    current += size

            except (Exception, error.LoadError) as E:
                if self.parent is not None:
                    path = str().join(map("<{:s}>".format, self.backtrace()))
                    if len(self.value):
                        Log.warn("infinite.load : {:s} : Stopped reading at element {:s} : {:s}".format(self.instance(), self.value[-1].instance(), path), exc_info=True)
                    else:
                        Log.warn("infinite.load : {:s} : Stopped reading before load : {:s}".format(self.instance(), path), exc_info=True)
                raise error.LoadError(self, exception=E)
        return self

    def loadstream(self, **attr):
        '''an iterator that incrementally populates the array'''
        with utils.assign(self, **attr):
            self.value = []
            offset = self.getoffset()

            current,maximum = 0,None if self.parent is None else self.parent.blocksize()
            try:
                while True if maximum is None else current < maximum:

                    # yield next element at the current offset
                    n = self.__next_element(offset)
                    self.value.append(n)
                    yield n

                    if not n.initializedQ():
                        break

                    if self.isTerminator(n):
                        break

                    # check sanity of element size
                    size = n.blocksize()
                    if size <= 0 and Config.parray.break_on_zero_sized_element:
                        Log.warn("infinite.loadstream : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), n.instance()))
                        break
                    if size < 0:
                        raise error.AssertionError(self, 'infinite.loadstream', message="Element size for {:s} is < 0".format(n.classname()))

                    # next iteration
                    offset += size
                    current += size

            except error.LoadError as E:
                if self.parent is not None:
                    path = str().join(map("<{:s}>".format, self.backtrace()))
                    Log.warn("infinite.loadstream : {:s} : Stopped reading at element {:s} : {:s}".format(self.instance(), n.instance(), path))
                raise error.LoadError(self, exception=E)
            pass
        super(type, self).load()

class block(uninitialized):
    '''An array that reads elements until their size totals the same amount returned by .blocksize()'''
    def isTerminator(self, value):
        return False

    def load(self, **attrs):
        # fallback to regular loading if user has hardcoded the length
        if attrs.get('length', self.length) is not None:
            return super(block, self).load(**attrs)

        with utils.assign(self, **attrs):
            forever = itertools.count() if self.length is None else six.moves.range(len(self))
            offset, self.value = self.getoffset(), []

            if self.blocksize() == 0:   # if array is empty...
                return self

            current = 0
            for index in forever:
                n = self.new(self._object_, __name__=str(index), offset=offset)

                try:
                    n = n.load()

                except error.LoadError as E:
                    #E = error.LoadError(self, exception=E)
                    o = current + n.blocksize()

                    # if we error'd while decoding too much, then let user know
                    if o > self.blocksize():
                        path = str().join(map("<{:s}>".format, n.backtrace()))
                        Log.warn("block.load : {:s} : Reached end of blockarray at {:s} : {:s}".format(self.instance(), n.instance(), path))
                        self.value.append(n)

                    # otherwise add the incomplete element to the array
                    elif o < self.blocksize():
                        Log.warn("block.load : {:s} : LoadError raised at {:s} : {!r}".format(self.instance(), n.instance(), E))
                        self.value.append(n)

                    break

                size = n.blocksize()
                if size <= 0 and Config.parray.break_on_zero_sized_element:
                    Log.warn("block.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), n.instance()))
                    break
                if size < 0:
                    raise error.AssertionError(self, 'block.load', message="Element size for {:s} is < 0".format(n.classname()))

                # if our child element pushes us past the blocksize
                if current + size >= self.blocksize():
                    path = str().join(map("<{:s}>".format, n.backtrace()))
                    Log.debug("block.load : {:s} : Terminated at {:s} : {:s}".format(self.instance(), n.instance(), path))
                    self.value.append(n)
                    break

                # add to list, and check if we're done.
                self.value.append(n)
                if self.isTerminator(n):
                    break
                offset,current = offset+size,current+size

            pass
        return self

    def initializedQ(self):
        return super(block, self).initializedQ() and (self.size() >= self.blocksize() if self.length is None else len(self.value) == self.length)

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
    import ptypes,array,random
    from ptypes import pstruct,parray,pint,provider,utils,dynamic,ptype
    import string

    class RecordGeneral(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'start'),
            (pint.uint8_t, 'end'),
        ]

    class qword(ptype.type): length = 8
    class dword(ptype.type): length = 4
    class word(ptype.type): length = 2
    class byte(ptype.type): length = 1

    random.seed()
    def function(self):
#        if len(self.value) > 0:
#            self[0].load()
#            print(self[0])
        return random.sample([byte, word, dword, function2], 1)[0]

    def function2(self):
        return qword()

    @TestCase
    def test_array_type_dword():
        class myarray(parray.type):
            length = 5
            _object_ = dword

        x = myarray()
#        print(x)
#        print(x.length,len(x), x.value)
        x.source = provider.string(b'AAAA'*15)
        x.l
#        print(x.length,len(x), x.value)
#        print("{!r}".format(x))
        if len(x) == 5 and x[4].serialize() == b'AAAA':
            raise Success

    @TestCase
    def test_array_type_function():
        class myarray(parray.type):
            length = 16
            _object_ = function

        x = myarray()
        x.source = provider.memory()
        x.setoffset(id(x))
        x.load()
#        print(x)

        if len(x) == 16:
            raise Success

    @TestCase
    def test_array_terminated_uint8():
        class myarray(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, v):
                if v.serialize() == b'H':
                    return True
                return False

        block = b'GFEDCBABCDHEFG'
        x = myarray(source=provider.string(block)).l
        if len(x) == 11:
            raise Success

    @TestCase
    def test_array_infinite_struct():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        chars = b'\xdd\xdd'
        string = chars * 8
        string = string[:-1]

        z = RecordContainer(source=provider.string(string)).l
        if len(z)-1 == int(len(string)/2.0) and len(string)%2 == 1:
            raise Success

    @TestCase
    def test_array_infinite_struct_partial():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        data = provider.string(b'AAAAA')
        z = RecordContainer(source=data).l
        s = RecordGeneral().a.blocksize()

        if z.blocksize() == len(z)*s and len(z) == 3 and z.size() == 5 and not z[-1].initializedQ():
            raise Success

    @TestCase
    def test_array_block_uint8():
        class container(parray.block):
            _object_ = pint.uint8_t
            blocksize = lambda s:4

        block = bytes().join(map(six.int2byte,six.moves.range(0x10)))

        a = container(source=provider.string(block)).l
        if len(a) == 4:
            raise Success

    @TestCase
    def test_array_infinite_type_partial():
        b = string.ascii_letters+string.digits

        count = 0x10

        child_type = pint.uint32_t
        class container_type(parray.infinite):
            _object_ = child_type

        block_length = child_type.length * count
        block = b'\0'*block_length

        n = container_type(source=provider.string(block)).l
        if len(n)-1 == count and not n[-1].initializedQ():
            raise Success

    @TestCase
    def test_array_block_uint32():
        count = 8

        child_type = pint.uint32_t
        class container_type(parray.block):
            _object_ = child_type

        block_length = child_type.length * count
        block = b'\0'*block_length
        container_type.blocksize = lambda s: child_type.length * 4

        a = container_type(source=provider.string(block)).l
        if len(a) == 4:
            raise Success

    @TestCase
    def test_array_infinite_nested_array():
        class subarray(parray.type):
            length = 4
            _object_ = pint.uint8_t
            def int(self):
                return six.moves.reduce(lambda x,y:x*256+int(y), self.v, 0)

            def repr(self, **options):
                if self.initializedQ():
                    return self.classname() + " {:x}".format(self.int())
                return self.classname() + ' ???'

        class extreme(parray.infinite):
            _object_ = subarray
            def isTerminator(self, v):
                return v.int() == 0x42424242

        a = extreme(source=provider.string(b'A'*0x100 + b'B'*0x100 + b'C'*0x100 + b'DDDD'))
        a=a.l
        if len(a) == (0x100 / subarray.length)+1:
            raise Success

    @TestCase
    def test_array_infinite_nested_block():
        random.seed(0)

        class leaf(pint.uint32_t): pass
        class rootcontainer(parray.block):
            _object_ = leaf

        class acontainer(rootcontainer):
            blocksize = lambda x: 8

        class bcontainer(rootcontainer):
            _object_ = pint.uint16_t
            blocksize = lambda x: 8

        class ccontainer(rootcontainer):
            _object_ = pint.uint8_t
            blocksize = lambda x: 8

        class arr(parray.infinite):
            def randomcontainer(self):
                l = [ acontainer, bcontainer, ccontainer ]
                return random.sample(l, 1)[0]

            _object_ = randomcontainer

        string = bytes().join([ six.int2byte(random.randint(six.byte2int(b'A'),six.byte2int(b'Z'))) for x in six.moves.range(0x100) ])
        a = arr(source=provider.string(string))
        a=a.l
        if a.blocksize() == 0x108:
            raise Success

    @TestCase
    def test_array_infinite_nested_partial():
        class fakefile(object):
            d = array.array('L', ((0xdead*x)&0xffffffff for x in six.moves.range(0x100)))
            d = array.array('B', bytearray(d.tostring() + b'\xde\xad\xde\xad'))
            o = 0
            def seek(self, ofs):
                self.o = ofs
            def read(self, amount):
                r = self.d[self.o:self.o+amount].tostring()
                self.o += amount
                return r
        strm = provider.stream(fakefile())

        class stoofoo(pstruct.type):
            _fields_ = [ (pint.uint32_t, 'a') ]
        class argh(parray.infinite):
            _object_ = stoofoo

        x = argh(source=strm)
        for a in x.loadstream():
            pass
        if not a.initializedQ() and x[-2].serialize() == b'\xde\xad\xde\xad':
            raise Success

    @TestCase
    def test_array_terminated_string():
        class szstring(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, value):
                return value.int() == 0

        data = provider.string(b'hello world\x00not included\x00')
        a = szstring(source=data).l
        if len(a) == len(b'hello world\x00'):
            raise Success

    @TestCase
    def test_array_nested_terminated_string():
        class szstring(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, value):
                return value.int() == 0

        class argh(parray.terminated):
            _object_ = szstring
            def isTerminator(self, value):
                return value.serialize() == b'end\x00'

        data = provider.string(b'hello world\x00is included\x00end\x00not\x00')
        a = argh(source=data).l
        if len(a) == 3:
            raise Success

    @TestCase
    def test_array_block_nested_terminated_string():
        class szstring(parray.terminated):
            _object_ = pint.uint16_t
            def isTerminator(self, value):
                return value.int() == 0

        class ninethousand(parray.block):
            _object_ = szstring
            blocksize = lambda x: 9000

        s = ((b'A'*498) + b'\x00\x00') + ((b'B'*498)+b'\x00\x00')
        a = ninethousand(source=provider.string(s*9000)).l
        if len(a) == 18 and a.size() == 9000:
            raise Success

    @TestCase
    def test_array_block_nested_terminated_block():
        class fiver(parray.block):
            _object_ = pint.uint8_t
            blocksize = lambda s: 5

        class feiverfrei(parray.terminated):
            _object_ = fiver
            def isTerminator(self, value):
                return value.serialize() == b'\x00\x00\x00\x00\x00'

        class dundundun(parray.block):
            _object_ = feiverfrei
            blocksize = lambda x: 50

        dat = b'A'*5
        end = b'\x00'*5
        s = (dat*4)+end + (dat*4)+end
        a = dundundun(source=provider.string(s*5)).l
        if len(a) == 2 and len(a[0]) == 5 and len(a[1]) == 5:
            raise Success

    @TestCase
    def test_array_block_blocksize():
        class blocked(parray.block):
            _object_ = pint.uint32_t

            def blocksize(self):
                return 16

        data = b'\xAA\xAA\xAA\xAA'*4
        data+= b'\xBB'*4

        x = blocked(source=provider.string(data))
        x = x.l
        if len(x) == 4 and x.size() == 16:
            raise Success

    @TestCase
    def test_array_set_uninitialized():
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty())
        a.set([x for x in six.moves.range(69)])
        if len(a) == 69 and sum(x.int() for x in a) == 2346:
            raise Success

    @TestCase
    def test_array_set_initialized():
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty(), length=69)
        a.a.set([42 for _ in six.moves.range(69)])
        if sum(x.int() for x in a) == 2898:
            raise Success

    @TestCase
    def test_array_alloc_keyvalue_set():
        class argh(parray.type):
            _object_ = pint.int32_t
        a = argh(length=4).alloc(((0,0x77777777),(3,-1)))
        if a[0].int() == 0x77777777 and a[-1].int() == -1:
            raise Success

    @TestCase
    def test_array_alloc_set_iterable():
        class argh(parray.type):
            _object_ = pint.int32_t
        a = argh(length=4).alloc((0,2,4))
        if tuple(s.int() for s in a) == (0,2,4,0):
            raise Success

    @TestCase
    def test_array_alloc_keyvalue_instance():
        class aigh(parray.type):
            _object_ = pint.uint8_t
            length = 4
        class argh(parray.type):
            _object_ = pint.uint32_t

        x = aigh().alloc(list(bytearray(b'PE\0\0')))
        a = argh(length=4).alloc(((0,x),(-1,0x5a4d)))
        if a[0].serialize() == b'PE\0\0' and a[-1].serialize() == b'MZ\0\0':
            raise Success

    @TestCase
    def test_array_set_initialized_value():
        a = parray.type(_object_=pint.uint32_t,length=4).a
        a.set((10,10,10,10))
        if sum(x.int() for x in a) == 40:
            raise Success

    @TestCase
    def test_array_set_initialized_type():
        a = parray.type(_object_=pint.uint8_t,length=4).a
        a.set((pint.uint32_t,)*4)
        if sum(x.size() for x in a) == 16:
            raise Success

    @TestCase
    def test_array_set_initialized_container():
        b = ptype.clone(parray.type,_object_=pint.uint8_t,length=4)
        a = parray.type(_object_=pint.uint8_t,length=4).a
        a.set((b,)*4)
        if sum(x.size() for x in a) == 16:
            raise Success

    @TestCase
    def test_array_set_initialized_instance():
        b = ptype.clone(parray.type,_object_=pint.uint8_t,length=4)
        a = parray.type(_object_=pint.uint8_t,length=4).a
        a.set(tuple(pint.uint32_t().set(0x40) for x in six.moves.range(4)))
        if sum(x.int() for x in a) == 256:
            raise Success

    @TestCase
    def test_array_set_uninitialized_dynamic_value():
        class blah(parray.type):
            def _object_(self):
                length = 0 if len(self.value) == 0 else (self.value[-1].length+1)%4
                return ptype.clone(pint.uint_t,length=length)
            length = 16
        a = blah()
        a.set((0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3))
        if sum(x.size() for x in a) == 6*4:
            raise Success

    @TestCase
    def test_array_set_uninitialized_dynamic_type():
        class blah(parray.type):
            def _object_(self):
                length = 0 if len(self.value) == 0 else (self.value[-1].length+1)%4
                return ptype.clone(pint.uint_t,length=length)
            length = 4
        a = blah()
        a.set((pint.uint8_t,pint.uint8_t,pint.uint8_t,pint.uint8_t))
        if sum(x.size() for x in a) == 4:
            raise Success
    @TestCase
    def test_array_set_uninitialized_dynamic_instance():
        class blah(parray.type):
            def _object_(self):
                length = 0 if len(self.value) == 0 else (self.value[-1].length+1)%4
                return ptype.clone(pint.uint_t,length=length)
            length = 4
        a = blah()
        a.set((pint.uint8_t().set(2),pint.uint8_t().set(2),pint.uint8_t().set(2),pint.uint8_t().set(2)))
        if sum(x.int() for x in a) == 8:
            raise Success

    @TestCase
    def test_array_alloc_value():
        class blah(parray.type):
            _object_ = pint.uint32_t
            length = 4
        a = blah().alloc((4,8,0xc,0x10))
        if all(x.size() == 4 for x in a) and tuple(x.int() for x in a) == (4,8,12,16):
            raise Success

    @TestCase
    def test_array_alloc_type():
        class blah(parray.type):
            _object_ = pint.uint32_t
            length = 4
        a = blah().alloc((pint.uint8_t,)*4)
        if all(x.size() == 1 for x in a):
            raise Success

    @TestCase
    def test_array_alloc_instance():
        class blah(parray.type):
            _object_ = pint.uint32_t
            length = 4
        a = blah().alloc([pint.uint8_t().set(i) for i in six.moves.range(4)])
        if all(x.size() == 1 for x in a) and sum(x.int() for x in a) == 6:
            raise Success

    @TestCase
    def test_array_alloc_partial():
        class blah(parray.type):
            _object_ = pint.uint32_t
            length = 4
        a = blah().alloc([pint.uint8_t])
        if a[0].size() == 1 and all(a[x].size() == 4 for x in six.moves.range(1,4)):
            raise Success

    @TestCase
    def test_array_alloc_infinite_empty():
        class blah(parray.infinite):
            _object_ = pint.uint32_t

        a = blah().a
        if a.serialize() == b'':
            raise Success

    #@TestCase
    #def test_array_alloc_terminated_partial():
    #    class blah(parray.terminated):
    #        _object_ = pint.uint32_t
    #        def isTerminator(self, value):
    #            return value.int() == 1
    #    a = blah().a
    #    a.value.extend(map(a.new, (pint.uint32_t,)*2))
    #    a.a
    #    if a.serialize() == '\x00\x00\x00\x00\x00\x00\x00\x00':
    #        raise Success

    @TestCase
    def test_array_alloc_infinite_sublement_infinite():
        class blah(parray.infinite):
            class _object_(parray.terminated):
                _object_ = pint.uint32_t
                def isTerminator(self, value):
                    return value.int() == 1
        a = blah().a
        if a.initializedQ() and a.serialize() == b'':
            raise Success

    @TestCase
    def test_array_set_array_with_dict():
        class blah(parray.type):
            length = 4
            class _object_(pstruct.type):
                _fields_ = [(pint.uint32_t, 'a'), (pint.uint32_t, 'b')]

        res = blah().a.set([dict(a=1, b=2), dict(a=3, b=4), dict(a=5), dict(b=6)])
        if res.get() == ((1, 2), (3, 4), (5, 0), (0, 6)):
            raise Success

    @TestCase
    def test_array_append_getoffset():
        x = parray.type(length=2, _object_=pint.uint32_t, offset=0x10).a
        offset = x.append(pint.uint16_t)
        if offset == x.getoffset() + x[0].size() * 2:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
