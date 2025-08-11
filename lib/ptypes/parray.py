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
import functools, operator, itertools
from . import ptype, bitmap, utils, error, provider

__all__ = 'type,terminated,infinite,block'.split(',')

from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'parray']))
integer_types = bitmap.integer_types

class __array_interface__(ptype.container):
    '''provides the generic features expected out of an array'''
    def __contains__(self, instance):
        '''L.__contains__(x) -> True if L has an item x, else False'''
        if isinstance(instance, integer_types):
            return 0 <= instance < len(self)
        return super(__array_interface__, self).__contains__(instance)

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
        object.parent, object.source = self, None
        self.value.insert(index, object)

        for i in range(index, len(self.value)):
            item = self.value[i]
            item.setoffset(offset, recurse=True)
            offset += item.blocksize()
        return

    def __append__(self, object):
        idx = len(self.value)
        item = object if ptype.isinstance(object) or ptype.istype(object) else self.new(self._object_).set(object)
        result = super(__array_interface__, self).__append__(item)
        offset = (self.value[idx - 1].getoffset() + self.value[idx - 1].size()) if idx > 0 else self.getoffset()
        result.setoffset(offset, recurse=True)
        return result

    def append(self, object):
        """Append ``object`` to a ``self``. Return the offset it was inserted at.

        This will update the offset of ``object`` so that it will appear at the
        end of the array.
        """
        return self.__append__(object)

    def extend(self, iterable):
        return [ self.append(item) for item in iterable ]

    def pop(self, index=-1):
        """Remove the element at ``index`` or the last element in the array.

        This will update all the offsets within ``self`` so that all elements are
        contiguous.
        """

        # determine the correct index
        idx = self.value.index(self.value[index])
        res = self.value.pop(idx)

        offset = res.getoffset()
        for i, item in enumerate(self.value[idx:]):
            item.setoffset(offset, recurse=True)
            offset += item.blocksize()
        return res

    def __getindex__(self, index):
        if not isinstance(index, integer_types):
            raise TypeError(self, '__array_interface__.__getindex__', "Expected an integer instead of {!s} for the index of an array ({:s}).".format(index.__class__, self.typename()))
        return index

    def __delitem__(self, index):
        '''x.__delitem__(y) <==> del x[y]'''
        if isinstance(index, slice):
            origvalue = self.value[:]
            for idx in range(*slice(index.start or 0, index.stop, index.step or 1).indices(index.stop)):
                realidx = self.__getindex__(idx)
                self.value.pop( self.value.index(origvalue[realidx]) )
            return origvalue.__getitem__(index)
        return self.pop(index)

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if isinstance(index, slice):
            ivalue = itertools.repeat(value) if isinstance(value, ptype.generic) else iter(value)
            res = self.value[:]
            for idx in range(*slice(index.start or 0, index.stop, index.step or 1).indices(index.stop)):
                i = self.__getindex__(idx)
                self.value[i] = utils.next(ivalue)
            return res.__getitem__(index)

        idx = self.__getindex__(index)
        result = super(__array_interface__, self).__setitem__(idx, value)
        result.__name__ = str(index)
        return result

    def __getitem__(self, index):
        '''x.__getitem__(y) <==> x[y]'''
        if isinstance(index, slice):
            cls, result = self.__class__, [ self.value[self.__getindex__(idx)] for idx in range(*index.indices(len(self))) ]
            t = ptype.clone(cls, length=len(result), _object_=self._object_)
            return self.new(t, offset=result[0].getoffset() if len(result) else self.getoffset(), value=result)

        idx = self.__getindex__(index)
        ([None]*len(self))[idx]     # make python raise the correct exception if so..
        return super(__array_interface__, self).__getitem__(idx)

    def __element__(self):
        try: length = len(self)
        except Exception: length = self.length or 0

        object = self._object_
        if object is None:
            res = '(untyped)'
        else:
            res = object.typename() if ptype.istype(object) else object.__name__

        return u"{:s}[{:d}]".format(res, length)

    def summary(self):
        res = super(__array_interface__, self).summary()
        if self.initializedQ():
            return ' '.join([self.__element__(), res])
        return ' '.join([self.__element__(), res])

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        # If we got an InitializationError while fetching the properties (due to
        # a bunk user implementation), then we simply fall back to the internal
        # implementation.
        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        result, element = self.repr(), self.__element__()

        # multiline (includes element description)
        if result.count('\n') > 0 or utils.callable_eq(self, self.repr, __array_interface__, __array_interface__.details):
            result = result.rstrip('\n')
            if prop:
                return u"{:s} '{:s}' {{{:s}}} {:s}\n{:s}".format(utils.repr_class(self.classname()), self.name(), prop, element, result)
            return u"{:s} '{:s}' {:s}\n{:s}".format(utils.repr_class(self.classname()), self.name(), element, result)

        # if the user chose to not use the default summary, then prefix the element description.
        if all(not utils.callable_eq(self, self.repr, __array_interface__, item) for item in [__array_interface__.repr, __array_interface__.summary]):
            result = ' '.join([element, result])

        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

class type(__array_interface__):
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
        for index in range(self.length):
            item = self.new(self._object_, __name__=str(index), offset=offset, **attrs)
            self.value.append(item)
            offset += item.blocksize()
        return self

    # load ourselves incrementally
    def __load_container(self, **attrs):
        offset = self.getoffset()
        for index in range(self.length):
            item = self.new(self._object_, __name__=str(index), offset=offset, **attrs)
            self.value.append(item)
            item.load()
            offset += item.blocksize()
        return self

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        result._object_ = self._object_
        result.length = self.length
        return result

    def alloc(self, fields=(), **attrs):
        iterable = ((index, field) for index, field in fields.items()) if isinstance(fields, dict) else ((index, field) for index, field in enumerate(fields))
        fields = {index : field for index, field in iterable}

        # now we can start allocating things. the process here is to first use the
        # length (if available) to initialize the array. during this process, we use
        # any fields we were given as the element. without a length, this gets skipped.
        self.value = []
        with utils.assign(self, **attrs):
            offset, object, length = self.getoffset(), self._object_, getattr(self, 'length', 0) or 0
            for index in range(length):
                field = fields.pop(index, object)
                field_is_type, field_is_instance = ptype.isresolveable(field) or ptype.istype(field), ptype.isinstance(field)

                # figure out whether we need to instantiate a new field or
                # just update the original and then append it to our current value.
                element = self.new(field if field_is_type or field_is_instance else object, __name__=str(index), offset=offset)
                self.value.append(element)

                # use the type to determine whether we're adding or updating an element.
                if field_is_type:
                    value = element.a
                elif field_is_instance:
                    value = element
                else:
                    value = element.alloc(field)     # generic.alloc will fallback to generic.set

                offset += value.blocksize()

            # if there's any signed fields, that we were given, then remove them and translate them
            # to the number of elements in the array. we use these to replace any previously-allocated
            # elements. this has a side-effect in that if the size of the additional element is
            # different, then the offsets of the elements that follow it will be incorrect.
            # FIXME: it's probably better to translate all negative indexes and process them using
            #        the first loop, or to cull negative indexes out of the dictionary altogether.
            negatives = ((index + len(self.value), fields.pop(index)) for index in sorted(fields) if index < 0)
            for index, field in negatives:
                name, fieldoffset = "{:d}".format(index), self.value[index].getoffset()
                if ptype.istype(field) or ptype.isresolveable(field):
                    self.value[index] = self.new(field, offset=fieldoffset).a
                elif isinstance(field, ptype.generic):
                    self.value[index] = self.new(field, offset=fieldoffset)
                else:
                    self.value[index].alloc(field)    # generic.alloc will fall back to generic.set
                value = self.value[index]
                offset = max(offset, value.getoffset() + value.blocksize())

            # the final step takes whatever indices we have left, and treats them as additional
            # elements that get added one-by-one. these get appended to whatever work was completed
            # by the previous loops. if the leftover indices are not sequential (like our fields
            # was a dictionary), then we fill up any elements in-between with the original type.
            extra = sorted((len(self.value) + index if index < 0 else index) for index in fields)
            for index in range(*[len(self.value), 1 + extra[-1] if extra else len(self.value)]):
                field = fields.pop(index, object)
                field_is_type, field_is_instance = ptype.isresolveable(field) or ptype.istype(field), ptype.isinstance(field)

                # now we can instantiate the next element from a new field
                # or by updating the old one, and then add it to our list.
                element = self.new(field if field_is_type or field_is_instance else object, __name__=str(index), offset=offset)
                self.value.append(element)

                # check the type of our field to figure out how to allocate it.
                if field_is_type:
                    value = element.a
                elif field_is_instance:
                    value = element
                else:
                    value = element.alloc(field)     # generic.alloc will fall back to generic.set
                offset += element.blocksize()

        # now we just need to update the offsets and return ourselves.
        self.setoffset(self.getoffset(), recurse=True)
        return self

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
        except error.LoadError:
            raise error.LoadError(self)
        raise error.AssertionError(self, 'type.load')

    def __setvalue__(self, *values, **attrs):
        """Update self with the contents of the first argument in ``value``"""
        if not values:
            return self

        [value] = values
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
            Log.warning("type.__setvalue__ : {:s} : Length of array was explicitly changed ({:d} != {:d}).".format(self.instance(), length, len(self)))

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
        if self.length is None:
            raise error.ImplementationError(self, 'terminated.isTerminator')
        return False

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        if self.length is None:
            if self.value is None:
                raise error.InitializationError(self, 'terminated.__len__')
            return len(self.value)
        return super(terminated, self).__len__()

    def alloc(self, *fields, **attrs):
        if not fields:
            attrs.setdefault('length', getattr(self, 'length', 0) or 0)
            return super(terminated, self).alloc(**attrs)

        # If some fields were explicitly specified, then take the length from
        # them unless the caller gave us a length to use.
        [items] = fields
        attrs.setdefault('length', len(items))
        return super(terminated, self).alloc(items, **attrs)

    def load(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                forever = itertools.count() if self.length is None else range(self.length)
                offset, self.value = self.getoffset(), []

                for index in forever:
                    item = self.new(self._object_, __name__=str(index), offset=offset)
                    self.value.append(item)
                    if self.isTerminator(item.load()):
                        break
                    size = item.blocksize()

                    # we only allow elements with a zero size when the object type is
                    # a call (meaning it's a dynamic type) or if its blocksize is dynamic.
                    if size <= 0:
                        if ptype.istype(self._object_) and item.__blocksize_originalQ__():
                            Log.warning("terminated.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), item.instance()))
                            break

                        # validate that the element size is a sane value, as the size returned
                        # by the user's implementation should _always_ be positive.
                        if size < 0:
                            raise error.AssertionError(self, 'terminated.load', message="Element size for {:s} is < 0".format(item.classname()))
                        Log.info("terminated.load : {:s} : Added a dynamic element with a {:d} length to a terminated array : {:s}".format(self.instance(), size, item.instance()))
                    offset += size

        except (Exception, error.LoadError):
            raise error.LoadError(self)

        return self

class uninitialized(terminated):
    """An array that can contain uninitialized or partially initialized elements.

    This array determines it's size dynamically ignoring partially or
    uninitialized elements found near the end.
    """
    def size(self):
        if self.value is not None:
            return sum(item.size() for item in self.value if item.value is not None)
        raise error.InitializationError(self, 'uninitialized.size')

    def alloc(self, fields=(), **attrs):
        return super(uninitialized, self).alloc(fields, **attrs)

    def __properties__(self):
        res = super(uninitialized, self).__properties__()

        # If we're really not initialized, then there's nothing to do.
        if self.value is None:
            return res

        # Otherwise, we're actually initialized but not entirely and we need
        # to fix up our properties a bit to clean up the rendering of the instance.
        # fix up our properties a bit to clean up our rendering of the instance.
        if self.length is not None:
            if self.length < len(self.value):
                res['inflated'] = True
            elif self.length > len(self.value):
                res['abated'] = True
            return res
        return res

    def initializedQ(self):
        '''Returns True if all elements are partial or completely initialized.'''

        # Check to see if array contains any elements
        if self.value is None:
            return False

        # Grab all initialized elements near the beginning
        res = list(itertools.takewhile(utils.operator.methodcaller('initializedQ'), self.value))

        # Return True if the whole thing is initialized or just the tail is uninitialized
        return len(res) == len(self.value) or all(not item.initializedQ() for item in self.value[len(res):])

    def serialize(self):
        '''Serialize all currently available content of the array.'''
        iterable = itertools.takewhile(lambda item: item.initializedQ() or item.size() > 0, self.value)
        return b''.join(item.serialize() for item in iterable)

class infinite(uninitialized):
    '''An array that reads elements until an exception or interrupt happens'''

    def __next_element(self, offset, **attrs):
        '''Utility method that returns a new element at a specified offset and loads it. intended to be overloaded.'''
        index = len(self.value)
        item = self.new(self._object_, __name__=str(index), offset=offset)
        try:
            item.load(**attrs)
        except (error.LoadError, error.InitializationError):
            Log.info("infinite.__next_element : {:s} : Unable to read terminal element {:s}.".format(self.instance(), item.instance()))
        return item

    def isTerminator(self, value):
        return False

    def __properties__(self):
        res = super(infinite, self).__properties__()

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
            current, offset, self.value = 0, self.getoffset(), []

            # set any conditions that may be necessary for terminating this array. if there
            # is a length, we use that. if the provider is bounded, then we use that too.
            forever = itertools.count() if self.length is None else range(self.length)
            Fwhile = functools.partial(operator.ge, self.source.size() - self.getoffset()) if isinstance(self.source, provider.bounded) else lambda current: True

            # grab the blocksize and use it if we were assigned one that is different
            # from the default. this can allow one to constrain this type of array.
            custom_specified_blocksize = not self.__blocksize_originalQ__()
            blocksize = self.blocksize()

            # in this array type, we always include the last partially-read element.
            # this is different if a blocksize was specified, as the blocksize is
            # used to explicitly constraint the size of the array being read.
            try:
                for index in forever:
                    if not Fwhile(current):
                        break

                    # read next element at the current offset
                    item = self.__next_element(offset)
                    if not item.initializedQ():
                        Log.debug("infinite.load : {:s} : Element {:d} left partially initialized : {:s}".format(self.instance(), len(self.value), item.instance()))
                    self.value.append(item)

                    if not item.initializedQ():
                        break

                    if self.isTerminator(item):
                        break
                    size = item.blocksize()

                    # only allow elements with a zero size if the array has a limited length,
                    # when the object type is a call, or if its blocksize is dynamically calculated.
                    if size <= 0 and self.length is None:
                        if ptype.istype(self._object_) and item.__blocksize_originalQ__():
                            Log.warning("infinite.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), item.instance()))
                            break

                        # check sanity of element size
                        if size < 0:
                            raise error.AssertionError(self, 'infinite.load', message="Element size for {:s} is < 0".format(item.classname()))
                        Log.debug("infinite.load : {:s} : Added a dynamic element with a {:d} length to an infinite array : {:s}".format(self.instance(), size, item.instance()))

                    # next iteration
                    offset += size
                    current += size

                    # if we have a custom blocksize, then check that we haven't surpassed it.
                    if custom_specified_blocksize and current >= blocksize:
                        break
                    continue

            except (Exception, error.LoadError):
                if self.parent is not None:
                    if len(self.value):
                        Log.warning("infinite.load : {:s} : Stopped reading at element {:s}.".format(self.instance(), self.value[-1].instance()), exc_info=True)
                    else:
                        Log.warning("infinite.load : {:s} : Stopped reading before load.".format(self.instance()), exc_info=True)
                raise error.LoadError(self)
        return self

    def __deserialize_block__(self, block):
        try:
            super(infinite, self).__deserialize_block__(block)
        except (StopIteration, error.ProviderError) as exception:
            if not self.initializedQ():
                raise exception
            uninitialized = [item.blocksize() for item in itertools.takewhile(lambda item: not item.initializedQ(), self.value[::-1])]
            Log.warning("infinite.__deserialize_block__ : {:s} : Consumed {:d}{:+d} elements for infinite-sized-array with the size being {:#x}{:+#x} for the total blocksize ({:+#x}).".format(self.instance(), len(self.value) - len(uninitialized), len(uninitialized), self.size(), sum(uninitialized), self.blocksize()))
        return self

    # XXX: this iterator isn't used for anything and should probably be
    #      removed... its purpose is likely completely unnecessary anyways.
    def loadstream(self, **attr):
        '''an iterator that incrementally populates the array'''
        with utils.assign(self, **attr):
            current, offset, self.value = 0, self.getoffset(), []

            # this array type will consume its input indefinitely...unless a length
            # was explicitly assigned or the stream is bounded. so, we set some
            # conditions so that we can stop loading the array when we hit them.
            length_unlimited = self.length is None
            forever = itertools.count() if self.length is None else range(self.length)
            Fwhile = functools.partial(operator.ge, self.source.size() - self.getoffset()) if isinstance(self.source, provider.bounded) else lambda current: True

            # if a blocksize was specified, then we need to check that too.
            # the blocksize will _always_ constraint the load size of a type.
            custom_specified_blocksize = not self.__blocksize_originalQ__()
            blocksize = self.blocksize()

            # when loading from a stream, we consume everything that we're able
            # to until our conditions are met. if the provider raises an error,
            # then we add our partial element and can terminate our reading.
            try:
                for index in forever:
                    if not Fwhile(current):
                        break

                    # yield next element at the current offset
                    item = self.__next_element(offset)
                    self.value.append(item)
                    yield item

                    if not item.initializedQ():
                        break

                    if self.isTerminator(item):
                        break
                    size = item.blocksize()

                    # validate the element size. if the element has a zero size, then we check if the array
                    # has a length. if it doesn't, then we need to check if the object or its blocksize
                    # is being determined dynamically. if it isn't, then we break to avoid an infinite loop.
                    if size <= 0 and self.length is None:
                        if issubclass(self._object_, ptype.generic) and item.__blocksize_originalQ__():
                            Log.warning("infinite.loadstream : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), item.instance()))
                            break

                        # check sanity of element size
                        if size < 0:
                            raise error.AssertionError(self, 'infinite.loadstream', message="Element size for {:s} is < 0".format(item.classname()))
                        Log.info("infinite.loadstream : {:s} : Added a dynamic element with a {:d} length to an infinite array : {:s}".format(self.instance(), size, item.instance()))

                    # next iteration
                    offset += size
                    current += size

                    # if a custom blocksize was specified, then stop reading when we encounter it.
                    if custom_specified_blocksize and current >= blocksize:
                        break
                    continue

            except error.LoadError:
                if self.parent is not None:
                    Log.warning("infinite.loadstream : {:s} : Stopped reading at element {:s}.".format(self.instance(), item.instance()))
                raise error.LoadError(self)
            pass

        # Read everything until we have a load error, because that's what this
        # method does...
        try:
            super(type, self).load()
        except error.LoadError:
            pass
        return

class block(uninitialized):
    '''An array that reads elements until their size totals the same amount returned by .blocksize()'''
    def isTerminator(self, value):
        return False

    def load(self, **attrs):
        length = attrs.get('length', self.length)

        # demote to loading a regular array if the "length" is hardcoded.
        if length is not None:
            try:
                return super(block, self).load(**attrs)

            # if we caught a loading error, then we log an error and re-raise
            # the exception. the intent is to simulate the regular load error
            # that you get from being unable to load a regular array.
            except error.LoadError as E:
                Log.warning("block.load : {:s} : LoadError raised while trying to load a block array that has been demoted due to an explicit length ({:d}).".format(self.instance(), length))
                raise

        with utils.assign(self, **attrs):
            forever = itertools.count() if self.length is None else range(len(self))
            offset, self.value = self.getoffset(), []

            if self.blocksize() == 0:   # if array is empty...
                return self

            current = 0
            for index in forever:
                item = self.new(self._object_, __name__=str(index), offset=offset)

                try:
                    item = item.load()

                except error.LoadError as E:
                    #E = error.LoadError(self)
                    o = current + item.blocksize()

                    # if we error'd while decoding too much, then let user know
                    if o > self.blocksize():
                        Log.warning("block.load : {:s} : Reached end of blockarray at {:s}.".format(self.instance(), item.instance()))
                        self.value.append(item)

                    # otherwise add the incomplete element to the array
                    elif o < self.blocksize():
                        Log.warning("block.load : {:s} : LoadError raised at {:s} : {!r}".format(self.instance(), item.instance(), E))
                        self.value.append(item)
                    break

                # validate the size of the element, we only will allow zero-sized
                # elements if our object is dynamically determined via a callable.
                size = item.blocksize()
                if size <= 0:
                    if ptype.istype(self._object_) and item.__blocksize_originalQ__():
                        Log.warning("block.load : {:s} : Terminated early due to zero-length element : {:s}".format(self.instance(), item.instance()))
                        self.value.append(item)
                        break

                    # verify the sanity of the element size as lengths can't be less than zero.
                    if size < 0:
                        raise error.AssertionError(self, 'block.load', message="Element size for {:s} is < 0".format(item.classname()))
                    Log.info("block.load : {:s} : Added a dynamic element with a {:d} length to a block array : {:s}".format(self.instance(), size, item.instance()))

                # if our child element pushes us past the blocksize
                if current + size >= self.blocksize():
                    Log.debug("block.load : {:s} : Terminated at {:s}.".format(self.instance(), item.instance()))
                    self.value.append(item)
                    break

                # add to list, and check if we're done.
                self.value.append(item)
                if self.isTerminator(item):
                    break
                offset, current = offset+size, current+size

            pass
        return self

    def alloc(self, *args, **attrs):
        return super(block if args else terminated, self).alloc(*args, **attrs)

    def initializedQ(self):
        length = self.length
        return super(block, self).initializedQ() and (self.size() >= self.blocksize() if length is None else len(self.value) == length)

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
    import ptypes, sys, array, string, random, functools
    from ptypes import pstruct, parray, pint, provider, utils, dynamic, ptype
    from ptypes.utils import operator

    arraytobytes = operator.methodcaller('tostring' if sys.version_info[0] < 3 else 'tobytes')
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
        x.source = provider.bytes(b'AAAA'*15)
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
        x = myarray(source=provider.bytes(block)).l
        if len(x) == 11:
            raise Success

    @TestCase
    def test_array_infinite_struct():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        chars = b'\xdd\xdd'
        string = chars * 8
        string = string[:-1]

        z = RecordContainer(source=provider.bytes(string)).l
        if len(z)-1 == int(len(string)/2.0) and len(string)%2 == 1:
            raise Success

    @TestCase
    def test_array_infinite_struct_partial():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        data = provider.bytes(b'AAAAA')
        z = RecordContainer(source=data).l
        s = RecordGeneral().a.blocksize()

        if z.blocksize() == len(z)*s and len(z) == 3 and z.size() == 5 and not z[-1].initializedQ():
            raise Success

    @TestCase
    def test_array_block_uint8():
        class container(parray.block):
            _object_ = pint.uint8_t
            blocksize = lambda s:4

        block = bytes(bytearray(range(0x10)))

        a = container(source=provider.bytes(block)).l
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

        n = container_type(source=provider.bytes(block)).l
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

        a = container_type(source=provider.bytes(block)).l
        if len(a) == 4:
            raise Success

    @TestCase
    def test_array_infinite_nested_array():
        class subarray(parray.type):
            length = 4
            _object_ = pint.uint8_t
            def int(self):
                return functools.reduce(lambda agg, item: 256 * agg + item.int(), self.value, 0)
            def repr(self):
                if self.initializedQ():
                    return self.classname() + " {:x}".format(self.int())
                return self.classname() + ' ???'

        class extreme(parray.infinite):
            _object_ = subarray
            def isTerminator(self, v):
                return v.int() == 0x42424242

        a = extreme(source=provider.bytes(b'A'*0x100 + b'B'*0x100 + b'C'*0x100 + b'DDDD'))
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

        iterable = (random.randint(*params) for params in [tuple(boundary for boundary in bytearray(b'AZ'))] * 0x100)
        string = bytes(bytearray(iterable))
        a = arr(source=provider.bytes(string))
        a=a.l
        if a.blocksize() == 0x108:
            raise Success

    @TestCase
    def test_array_infinite_nested_partial():
        class fakefile(object):
            d = array.array('L' if len(array.array('I', 4 * b'\0')) > 1 else 'I', ((item * 0xdead) & 0xffffffff for item in range(0x100)))
            d = array.array('B', bytearray(arraytobytes(d) + b'\xde\xad\xde\xad'))
            o = 0
            def seek(self, ofs):
                self.o = ofs
            def read(self, amount):
                r = arraytobytes(self.d[self.o : amount + self.o])
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

        data = provider.bytes(b'hello world\x00not included\x00')
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

        data = provider.bytes(b'hello world\x00is included\x00end\x00not\x00')
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
        a = ninethousand(source=provider.bytes(s*9000)).l
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
        a = dundundun(source=provider.bytes(s*5)).l
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

        x = blocked(source=provider.bytes(data))
        x = x.l
        if len(x) == 4 and x.size() == 16:
            raise Success

    @TestCase
    def test_array_set_uninitialized():
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty())
        a.set([x for x in range(69)])
        if len(a) == 69 and sum(x.int() for x in a) == 2346:
            raise Success

    @TestCase
    def test_array_set_initialized():
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty(), length=69)
        a.a.set([42 for _ in range(69)])
        if sum(x.int() for x in a) == 2898:
            raise Success

    @TestCase
    def test_array_alloc_keyvalue_set():
        class argh(parray.type):
            _object_ = pint.int32_t
        a = argh(length=4).alloc({0: 0x77777777, 3: -1})
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
        a = argh(length=4).alloc({0: x, -1: 0x5a4d})
        if a[0].serialize() == b'PE\0\0' and a[-1].serialize() == b'MZ\0\0':
            raise Success

    @TestCase
    def test_array_alloc_withdict():
        class member(pstruct.type):
            _fields_ = [
                (pint.uint8_t, 'a'),
                (pint.uint8_t, 'b'),
            ]

        class argh(parray.type):
            _object_ = member

        print('-'*40)
        a = argh().alloc([{'a': 1, 'b': 2}])
        print('='*40)
        if len(a) == 1 and (a[0]['a'].int(),a[0]['b'].int()) == (1,2):
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
        a.set(tuple(pint.uint32_t().set(0x40) for x in range(4)))
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
        a = blah().alloc([pint.uint8_t().set(i) for i in range(4)])
        if all(x.size() == 1 for x in a) and sum(x.int() for x in a) == 6:
            raise Success

    @TestCase
    def test_array_alloc_partial():
        class blah(parray.type):
            _object_ = pint.uint32_t
            length = 4
        a = blah().alloc([pint.uint8_t])
        if a[0].size() == 1 and all(a[x].size() == 4 for x in range(1,4)):
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
    #    if a.serialize() == b'\x00\x00\x00\x00\x00\x00\x00\x00':
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
        result = x.append(pint.uint16_t)
        if result.getoffset() == x.getoffset() + x[0].size() * 2:
            raise Success

    @TestCase
    def test_array_alloc_dynamic_element_blocksize_1():
        class t(parray.type):
            _object_, length = pint.uint8_t, 4

        class dynamic_t(ptype.block):
            def blocksize(self):
                return 1 if self.getoffset() else 0
        res = t().alloc({2: dynamic_t})
        if res.size() == 4:
            raise Success

    @TestCase
    def test_array_alloc_dynamic_element_blocksize_2():
        class t(parray.type):
            _object_, length = pint.uint8_t, 4

        class dynamic_t(ptype.block):
            def blocksize(self):
                return 1 if self.getoffset() else 0
        res = t().alloc([pint.uint8_t, pint.uint8_t, dynamic_t, pint.uint8_t])
        if res.size() == 4:
            raise Success

    @TestCase
    def test_array_slice_1():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[:].get()) == tuple(result):
            raise Success

    @TestCase
    def test_array_slice_2():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[::1].get()) == tuple(result[::1]):
            raise Success

    @TestCase
    def test_array_slice_3():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[::2].get()) == tuple(result[::2]):
            raise Success

    @TestCase
    def test_array_slice_4():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[::-1].get()) == tuple(result[::-1]):
            raise Success

    @TestCase
    def test_array_slice_5():
        result = bytearray([1,2,3,4,5,0])
        class argh(parray.terminated):
            _object_, isTerminator = pint.uint8_t, lambda self, item: not item.int()

        res = argh().load(source=provider.bytes(result))
        if res.size() == len(result) and tuple(res[::2].get()) == tuple(result[::2]):
            raise Success

    @TestCase
    def test_array_slice_6():
        result = bytearray([1,2,3,4,5,0])
        class argh(parray.block):
            _object_, blocksize = pint.uint8_t, lambda self, size=4: size

        res = argh().load(source=provider.bytes(result))
        if res.size() == 4 and tuple(res[::-1].get()) == tuple(result[3::-1]):
            raise Success

    @TestCase
    def test_array_slice_7():
        result = bytearray([1,2,3,4,4,3,2,1])
        class argh(parray.infinite):
            _object_ = pint.uint8_t

        res = argh().load(source=provider.bytes(result))
        if (res.size(), res.blocksize()) == (8, 9) and tuple(res[:].get()) == tuple(result[:]) + (0,):
            raise Success

    @TestCase
    def test_array_slice_preserve_1():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
            def get(self):
                return [2 * x for x in super(argh, self).get()]
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[:].get()) == tuple(2 * x for x in result):
            raise Success

    @TestCase
    def test_array_slice_preserve_2():
        result = [1,2,3,4]
        class argh(parray.type):
            _object_, length = pint.uint8_t, len(result)
            def get(self):
                return [2 * x for x in super(argh, self).get()]
        res = argh().set(result)
        if res.size() == len(result) and tuple(res[::-1].get()) == tuple(2 * x for x in result[::-1]):
            raise Success

    @TestCase
    def test_array_alloc_with_offset_1():
        # XXX: this might occur with ptype.block or really any type that
        #      has a custom blocksize. i can only repro w/ arrays, though.
        class myblock(ptype.block):
            def blocksize(self):
                offset = self.getoffset()
                return abs((offset % 8) - 8) % 8

        class mystruct(pstruct.type):
            def alloc(self, *a, **fields):
                fields.setdefault('b', *a) if a else fields
                return super(mystruct, self).alloc(**fields)
        mystruct._fields_ = [(myblock, 'a'), (pint.uint32_t, 'b')]

        class argh(parray.type): pass
        argh._object_ = mystruct
        argh.length = 4

        expected = argh().load(source=provider.empty())
        offsets = [item.getoffset() for item in expected]
        res = argh().alloc([pint.uint8_t] + [0 for offset in offsets][1:])
        if all(item.getoffset() == offset for item, offset in zip(res[2:], offsets[2:])):
            raise Success

    @TestCase
    def test_array_alloc_with_offset_2():
        class myblock(ptype.block):
            def blocksize(self):
                offset = self.getoffset()
                return abs((offset % 8) - 8) % 8

        class mystruct(pstruct.type):
            def alloc(self, *a, **fields):
                fields.setdefault('b', *a) if a else fields
                return super(mystruct, self).alloc(**fields)
        mystruct._fields_ = [(myblock, 'a'), (pint.uint32_t, 'b')]

        class argh(parray.terminated):
            def isTerminator(self, value):
                return len(self.value) > 4
        argh._object_ = mystruct

        expected = argh().load(source=provider.empty())
        offsets = [item.getoffset() for item in expected]
        res = argh().alloc([pint.uint8_t] + [0 for offset in offsets][1:])
        if all(item.getoffset() == offset for item, offset in zip(res[2:], offsets[2:])):
            raise Success

    @TestCase
    def test_array_alloc_with_offset_3():
        class myblock(ptype.block):
            def blocksize(self):
                offset = self.getoffset()
                return abs((offset % 8) - 8) % 8

        class mystruct(pstruct.type):
            def alloc(self, *a, **fields):
                fields.setdefault('b', *a) if a else fields
                return super(mystruct, self).alloc(**fields)
        mystruct._fields_ = [(myblock, 'a'), (pint.uint32_t, 'b')]

        class argh(parray.block):
            def blocksize(self):
                return 8 * 4
        argh._object_ = mystruct

        expected = argh().a
        offsets = [item.getoffset() for item in expected]
        res = argh().alloc([pint.uint8_t] + [0 for offset in offsets][1:])
        if all(item.getoffset() == offset for item, offset in zip(res[2:], offsets[2:])):
            raise Success

    @TestCase
    def test_array_alloc_with_offset_4():
        class myblock(ptype.block):
            def blocksize(self):
                offset = self.getoffset()
                return abs((offset % 8) - 8) % 8

        class mystruct(pstruct.type):
            def alloc(self, *a, **fields):
                fields.setdefault('b', *a) if a else fields
                return super(mystruct, self).alloc(**fields)
        mystruct._fields_ = [(myblock, 'a'), (pint.uint32_t, 'b')]

        class argh(parray.infinite): pass
        argh._object_ = mystruct

        expected = argh().load(source=ptypes.prov.bytes(b'\0'*0x20))
        offsets = [item.getoffset() for item in expected]
        res = argh().alloc([pint.uint8_t] + [0 for offset in offsets][1:])
        if all(item.getoffset() == offset for item, offset in zip(res[2:], offsets[2:])):
            raise Success

    @TestCase
    def test_array_alloc_terminated_length_1():
        class t(parray.terminated):
            _object_ = pint.uint32_t
        x = t().a
        if len(x) == 0:
            raise Success

    @TestCase
    def test_array_alloc_terminated_length_2():
        class t(parray.terminated):
            _object_ = pint.uint32_t
        x = t(length=2).a
        if len(x) == 2:
            raise Success

    @TestCase
    def test_array_alloc_terminated_length_3():
        class t(parray.terminated):
            _object_ = pint.uint32_t
        x = t().alloc(length=2)
        if len(x) == 2:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
