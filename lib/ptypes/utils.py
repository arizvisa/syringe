import builtins, sys, math, random
import functools, operator, itertools, types

# Just some logging stuff.
from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, __name__]))

# Setup some version-agnostic types that we can perform checks with
string_types = (str, unicode) if sys.version_info[0] < 3 else (str,)
text_types = (unicode,) if sys.version_info[0] < 3 else (str,)
iterbytes = functools.partial(itertools.imap, ord) if sys.version_info[0] < 3 else iter

def iconsume(iterable, amount):
    '''this is just like itertools.islice but only implement the 2-parameter version.'''
    for _, item in zip(range(amount), iterable):
        yield item
    return
islice = itertools.islice if not hasattr(sys, 'implementation') else itertools.islice if sys.implementation.name in {'cpython'} else iconsume

def zip_longest(*args, **kargs):
    '''
    Return a zip_longest object whose .__next__() method returns a tuple where
    the i-th element comes from the i-th iterable argument.  The .__next__()
    method continues until the longest iterable in the argument sequence
    is exhausted and then it raises StopIteration.  When the shorter iterables
    are exhausted, the fillvalue is substituted in their place.  The fillvalue
    defaults to None or can be specified by a keyword argument.
    '''
    fillvalue = kargs.pop('fillvalue', None)
    if kargs:
        raise TypeError('zip_longest() got an unexpected keyword argument')
    def stopiteration(leftover):
        yield leftover.pop(0)
    filling, available = itertools.repeat(fillvalue), len(args) * [fillvalue]
    available.pop(0)
    iterables = [itertools.chain(arg, stopiteration(available), filling) for arg in args]
    try:
        while True:
            yield tuple(map(next, iterables))
    except IndexError:
        pass
    return

# If izip_longest exists, then use it...otherwise we need to use the above definition (micropython).
try:
    izip_longest = itertools.izip_longest if sys.version_info[0] < 3 else itertools.zip_longest
except AttributeError:
    izip_longest = zip_longest

# We need this because micropython doesn't implement a multi-parameter next().
def builtins_next(iterable, *args):
    '''
    next(iterator[, default])

    Return the next item from the iterator. If default is given and the iterator
    '''
    if len(args) > 1:
        raise TypeError("next expected at most {:d} arguments, got {:d}".format(2, 1 + len(args)))
    try:
        result = builtins.next(iterable)
    except StopIteration as E:
        if args:
            default, = args
            return default
        raise E
    return result

# py2 and micropython
next = builtins.next if not hasattr(sys, 'implementation') else builtins.next if sys.implementation.name in {'cpython'} else builtins_next

## byteorder calculations.
def byteorder_calculator(length):
    mask, offset, suboffset = length - 1, 0, 0

    # FIXME: this only works with lengths that are powers of 2, since we're using bitmasks.

    # I was raised with slow divisions, so I'm pretty sure this can be made faster.
    while True:
        shift = (mask - offset) & mask
        translated = offset & ~mask | shift, suboffset
        bits = (yield translated)
        suboffset += bits
        offset, suboffset = offset + suboffset // 8, suboffset & 7
    return

def position_calculator(length, base=0, position=(0, 0)):
    '''Coroutine that consumes an arbitrary number of bits, and yields the translated positions whilst maintaining the byte order.'''
    mask = length - 1

    # Instantiate our coroutine, grab the very first position, and discard it.
    # This is because we're going to calculate the bits needed to get to the
    # position we were given within our position parameter.
    coro = byteorder_calculator(length)
    _, _ = next(coro)

    # Now we need to figure out how many bits we need to discard before we
    # get to the position the user has requested. To accomplish this, we
    # again need to take away the alignment to get the offset, and then use
    # it to calculate the number of bits to get to the actual desried position.
    offset, suboffset = position
    goal = offset - base
    start, bytes = goal & ~mask, mask - (goal & mask)
    bits = 8 * (start + bytes) + suboffset

    # Finally we can actually discard the bits and recalculate our offset and suboffset.
    offset, suboffset = coro.send(bits)
    translated = base + offset, suboffset

    if translated != position:
        Log.warning("{:s} : A non-critical error occurred when calculating the bit position. Expected position to be {!s}, but translated position was {!s}.".format('.'.join([__name__, 'position_calculator']), *itertools.chain(position, translated)))

    # This is doing 2 additions and a comparison for every single iteration...
    while True:
        bits = (yield translated)
        offset, suboffset = coro.send(bits)
        translated = base + offset, suboffset
    return

## string formatting
def strdup(string, terminator='\0'):
    """Will return a copy of ``string`` with the provided ``terminated`` characters trimmed"""
    count = len(list(itertools.takewhile(lambda item: item not in terminator, string)))
    return string[:count]

def indent(string, tabsize=4, char=' ', newline='\n'):
    """Indent each line of ``string`` with the specified tabsize"""
    indent = char * tabsize
    strings = [(indent + item) for item in string.split(newline)]
    return newline.join(strings)

## temporary attribute assignments for a context
class assign(object):
    """Will temporarily assign the provided attributes to the specified to all code within it's scope"""

    # the following is a table of forwarded attributes to ensure that the
    # proper attribute is fetched so it'll get restored properly
    magical = {
        'source' : '__source__',
    }

    def __init__(self, *objects, **attributes):
        self.objects = objects
        self.attributes = { self.magical.get(attribute, attribute) : value for attribute, value in attributes.items() }

    def __enter__(self):
        objects, attributes = self.objects, self.attributes
        self.states = tuple({attribute : getattr(item, attribute) for attribute in attributes.keys()} for item in objects)
        [item.__update__(attributes) for item in objects]
        return objects

    def __exit__(self, exc_type, exc_value, traceback):
        [item.__update__(attributes) for item, attributes in zip(self.objects, self.states)]
        return

## ptype padding types
class padding:
    """Used for providing padding."""
    class source:
        def __bytesdecorator__(method):
            def closure(*args, **kwargs):
                iterable = method(*args, **kwargs)
                return (bytes(bytearray([item])) for item in iterable)
            return closure if sys.version_info[0] < 3 else method

        @classmethod
        @__bytesdecorator__
        def repeat(cls, value):
            iterable = iterbytes(value)
            return itertools.cycle(iterable)

        @classmethod
        @__bytesdecorator__
        def iterable(cls, iterable):
            return iterbytes(iterable)

        @classmethod
        def file(cls, file):
            return itertools.starmap(file.read, itertools.repeat([1]))

        @classmethod
        @__bytesdecorator__
        def prng(cls, seed=None):
            random.seed(seed)
            return itertools.starmap(random.randint, itertools.repeat([0, 0xff]))

        @classmethod
        @__bytesdecorator__
        def zero(cls):
            return iterbytes(cls.repeat(b'\0'))

    @classmethod
    def fill(cls, amount, source):
        """Returns a bytearray of ``amount`` elements, from the specified ``source``"""
        iterable = islice(source, amount)
        return bytes(bytearray(iterable))

## exception remapping
def mapexception(mapping={}, any=None, ignored=()):
    """Decorator for a function that maps exceptions from one type into another.

    ``mapping`` is a dictionary describing how to map exceptions. Each key can be a single item or a tuple which will then be mapped to the exception type specified in the value.
    ``any`` describes the exception to raise if any exception is raised. None can be used to use the raised exception.
    ``ignored`` specifies a list of exceptions to pass through unmodified
    """
    if not isinstance(mapping, dict):
        raise AssertionError("The type of the exception map ({!s}) is expected to be of a mappable type".format(mapping.__class__()))
    if not isinstance(ignored, (tuple, list)):
        raise AssertionError("The type of the ignored list ({!s}) is expected to contain of exceptions".format(ignored.__class__()))
    if any is not None and not issubclass(any, BaseException):
        raise AssertionError("The type of the exception to raise ({!s}) is expected to inherit from the {!s} type".format(any, BaseException))

    def decorator(fn):
        def decorated(*args, **kwds):
            try:
                return fn(*args, **kwds)

            except Exception:
                type, value, traceback = sys.exc_info()

            with_traceback = (lambda E: E) if not hasattr(sys, 'implementation') else operator.methodcaller('with_traceback', traceback) if sys.implementation.name in {'cpython'} else (lambda E: E)

            for src, dst in mapping.items():
                if type is src or (isinstance(src, (tuple, list)) and type in src):
                    E = dst(type, value)
                    raise with_traceback(E)
                continue
            raise value if type in ignored or any is None else with_traceback(any(type, value))

        functools.update_wrapper(decorated, fn)
        return decorated
    return decorator

## naming representations of a type or instance
def repr_class(name):
    #return "<class '{:s}'>".format(name)
    return "<class {:s}>".format(name)
def repr_instance(classname, name):
    return "<instance {:s} '{:s}'>".format(classname, name)
def repr_position(pos, hex=True, precision=0):
    if len(pos) == 1:
        ofs, = pos
        return "{:x}".format(ofs)
    ofs, bofs = pos
    if precision > 0 or hex:
        partial = bofs / 8.0
        if hex:
            return "{:x}.{:x}".format(ofs, math.trunc(partial * 0x10))
        fraction = ":0{:d}x".format(precision)
        res = '{:x}.{' + fraction + '}'
        return res.format(ofs, math.trunc(partial * pow(10, precision)))
    return "{:x}.{:x}".format(ofs, bofs)

## hexdumping capability
def printable(data, nonprintable=u'.'):
    """Return a string of only printable characters"""
    return functools.reduce(lambda agg, item: agg + (bytearray([item]).decode(sys.getdefaultencoding() if hasattr(sys, 'getdefaultencoding') else 'latin1') if item >= 0x20 and item < 0x7f else nonprintable), bytearray(data), u'')

def hexrow(value, offset=0, width=16, breaks=[8], offset_width=4):
    """Returns ``value as a formatted hexadecimal str"""
    value = bytearray(islice(value, width))
    extra = width - len(value)

    ## left
    left = "{:0{:d}x}".format(offset, offset_width)

    ## middle
    res = [ "{:02x}".format(item) for item in value ]
    if len(value) < width:
        res += ['  '] * extra

    for item in breaks:
        if item < len(res):
            res[item] = ' ' + res[item]
        continue
    middle = ' '.join(res)

    ## right
    right = printable(value) + ' ' * extra

    return '  '.join([left, middle, right])

def hexdump(value, offset=0, width=16, rows=None, **kwds):
    """Returns ``value`` as a formatted hexdump

    If ``offset`` is specified, then the hexdump will start there.
    If ``rows`` or it's alias ``lines`` is specified, only that number of rows
    will be displayed.
    """

    rows = kwds.pop('rows', kwds.pop('lines', None))
    kwds.setdefault('offset_width', len("{:x}".format(offset + len(value))))
    value = iter(value)

    getRow = lambda o: hexrow(data, offset=o, **kwds)

    res = []
    (ofs, data) = offset, bytearray(islice(value, width))
    for i in (itertools.count(1) if rows is None else range(1, rows)):
        res.append( getRow(ofs) )
        ofs, data = ofs + width, bytearray(islice(value, width))
        if len(data) < width:
            break
        continue

    if len(data) > 0:
        res.append( getRow(ofs) )
    return '\n'.join(res)

def emit_repr(data, width=0, message=' ... total {size} bytes ... ', padding=' ', **formats):
    """Return a string replaced with ``message`` if larger than ``width``

    Message can contain the following format operands:
    width = width to be displayed
    charwidth = width of each character
    bytewidth = number of bytes that can fit within width
    length = number of bytes displayed
    **format = extra format specifiers for message
    """
    size = formats.setdefault('size', len(data))
    charwidth = formats.setdefault('charwidth', len(r'\xFF'))
    bytewidth = formats.setdefault('bytewidth', width // charwidth)

    hexify = lambda data: str().join(map(r"\x{:02x}".format, bytearray(data)))

    if width <= 0 or bytewidth >= len(data):
        return hexify(data)

    # figure out how many bytes we can print
    formatted = message.format(**formats)
    bytefrac, bytewidth = math.modf((width - len(formatted)) * 1.0 / charwidth)
    padlength = math.trunc(charwidth * bytefrac)

    # build the string that we'll slice our message into
    msg = padding * math.trunc(padlength / 2.0 + 0.5) + formatted + padding * math.trunc(padlength / 2)
    left, right = data[:math.trunc(bytewidth / 2 + 0.5)], data[len(data) - math.trunc(bytewidth / 2):]
    return hexify(left) + msg + hexify(right)

def emit_hexrows(data, height, message, offset=0, width=16, **attrs):
    """Return a hexdump replaced with ``message`` if rows are larger than ``height``

    Message can contain the following format operands:
    leftover - number of hexdump rows skipped
    height - the height requested
    count - the total rows in the hexdump
    skipped - the total number of bytes skipped
    size - the total number of bytes
    """
    size = len(data)
    count = math.trunc(math.ceil(size * 1.0 / width))
    half = math.trunc(height / 2.0)
    leftover = (count - half * 2)
    skipped = leftover * width
    attrs.setdefault('offset_width', len("{:x}".format(offset + size)))

    # display everything
    if height <= 0 or leftover <= 0:
        for o in range(0, size, width):
            # offset, width, attrs
            yield hexrow(data[o : o + width], offset + o, width, **attrs)
        return

    # display rows
    o1 = offset
    for o in range(0, half * width, width):
        yield hexrow(data[o : o + width], o + o1, **attrs)
    yield message.format(leftover=leftover, height=height, count=count, skipped=skipped, size=size)
    o2 = width * (count - half)
    for o in range(0, half * width, width):
        yield hexrow(data[o + o2 : o + o2 + width], o + o1 + o2, **attrs)
    return

def valueiterator(value, direction=+1):
    '''iterates through all the values in the specified direction yielding the bytes and their size (not in that order).'''
    for item in value[::direction]:
        if isinstance(item.value, bytes):
            yield len(item.value), item.value

        # If we encounter None, then the rest of this item should be uninitialized.
        elif item.value is None:
            break

        elif not hasattr(item, 'blockbits'):
            for size, value in valueiterator(item.value, direction):
                yield size, value
            continue

        else:
            yield item.size(), item.serialize()
        continue
    return

def valueaccumulate(value, direction, offset=0):
    '''iterate through a list yielding the current offset and the bytes that should be there.'''
    for size, value in valueiterator(value, direction):
        yield offset, value
        offset += size
    return

def attributes(instance):
    """Return all constant attributes of an instance.

    This skips over things that require executing code such as properties.
    """
    i, t = ( set(dir(_)) for _ in (instance, instance.__class__))
    result = {}
    for k in i:
        v = getattr(instance.__class__, k, callable)
        if not (callable(v) or hasattr(v, '__delete__')):
            result[k] = getattr(instance, k)
        continue
    for k in i.difference(t):
        v = getattr(instance, k)
        if not callable(v):
            result[k] = getattr(instance, k)
        continue
    return result

def fakedecorator(*args, **kattrs):
    '''This is a placeholder in case we are unable to tamper with the code belonging to a function type.'''
    kargs = list(args)
    def prepare(decoratee, **ignored):
        return decoratee
    return prepare(kargs.pop(0)) if not kattrs and len(kargs) == 1 and callable(kargs[0]) else prepare

def memoize(*kargs, **kattrs):
    '''Converts a function into a memoized callable
    kargs = a list of positional arguments to use as a key
    kattrs = a keyword-value pair describing attributes to use as a key

    if key='string', use kattrs[key].string as a key
    if key=callable(n)', pass kattrs[key] to callable, and use the returned value as key

    if no memoize arguments were provided, try keying the function's result by _all_ of it's arguments.
    '''
    F_VARARG = 0x4
    F_VARKWD = 0x8
    F_VARGEN = 0x20
    kargs = list(kargs)
    kattrs = tuple((o, a) for o, a in sorted(kattrs.items()))

    # Define some utility functions for interacting with a function object in a portable manner
    has_function = lambda F, attribute='im_func' if sys.version_info[0] < 3 else '__func__': hasattr(F, attribute)
    get_function = lambda F, attribute='im_func' if sys.version_info[0] < 3 else '__func__': getattr(F, attribute)

    def prepare_callable(fn, kargs=kargs, kattrs=kattrs):
        if has_function(fn):
            fn = get_function(fn)
        if not isinstance(fn, memoize.__class__):
            raise AssertionError("Callable {!r} is not of a function type".format(fn))
        cache = {}
        co = fn.__code__
        flags, varnames = co.co_flags, iter(co.co_varnames)
        if (flags & F_VARGEN) != 0:
            raise AssertionEerror("Not able to memoize {!r} generator function".format(fn))
        argnames = islice(varnames, co.co_argcount)
        c_positional = tuple(argnames)
        c_attribute = kattrs
        c_var = (next(varnames) if flags & F_VARARG else None, next(varnames) if flags & F_VARKWD else None)
        if not kargs and not kattrs:
            kargs[:] = itertools.chain(c_positional, filter(None, c_var))
        def key(*args, **kwds):
            res = iter(args)
            p = dict(zip(c_positional, res))
            p.update(kwds)
            a, k = c_var
            if a is not None: p[a] = tuple(res)
            if k is not None: p[k] = dict(kwds)
            k1 = (p.get(k, None) for k in kargs)
            k2 = ((n(p[o]) if callable(n) else getattr(p[o], n, None)) for o, n in c_attribute)
            return tuple(itertools.chain(k1, [None], k2))
        def callee(*args, **kwds):
            res = key(*args, **kwds)
            try: return cache[res] if res in cache else cache.setdefault(res, fn(*args, **kwds))
            except TypeError: return fn(*args, **kwds)
        def force(*args, **kwds):
            res = key(*args, **kwds)
            cache[res] = fn(*args, **kwds)
            return cache[res]

        # set some state utilities on the memoized function
        callee.memoize_key = lambda *args, **kwargs: key(*args, **kwargs)
        callee.memoize_key.__doc__ = """Generate a unique key based on the provided arguments."""
        callee.memoize_cache = lambda: cache
        callee.memoize_cache.__doc__ = """Return the current memoize cache."""
        callee.memoize_clear = lambda: cache.clear()
        callee.memoize_clear.__doc__ = """Empty the current memoize cache."""

        # add some wrappers to interact with the cache
        callee.force = lambda *args, **kwargs: force(*args, **kwargs)
        callee.force.__doc__ = """Force calling the function whilst updating the memoize cache."""
        callee.fetch = lambda *args, **kwargs: operator.getitem(cache, key(*args, **kwargs))
        callee.fetch.__doc__ = """Return the item in the cache for the specified key."""
        callee.store = lambda *args, **kwargs: lambda result: operator.setitem(cache, key(*args, **kwargs), result) or result
        callee.store.__doc__ = """Return a closure that stores the result to the specified key."""

        callee.__name__ = fn.__name__
        callee.__doc__ = fn.__doc__
        callee.callable = fn
        return callee if isinstance(callee, types.FunctionType) else types.FunctionType(callee)
    return prepare_callable(kargs.pop(0)) if not kattrs and len(kargs) == 1 and callable(kargs[0]) else prepare_callable

if not any(hasattr(memoize, __attribute__) for __attribute__ in ['func_code', '__code__']):
    Log.warning("{:s} : Memoization will be disabled due to the current implementation of python{:s} not allowing access of a function's code attributes (performance will be affected).".format(__name__, " ({:s})".format(sys.implementation.name) if hasattr(sys, 'implementation') else ''))
    memoize = fakedecorator

def memoize_method(*karguments, **kattributes):
    instancemethod = types.MethodType

    ## Some constants that we will use for our decorator.
    class undefined(object): pass
    class memoization_key_barrier(object): pass

    # Define a utility function for extracting the known parameter names from a function object
    def extract_parameters(F):
        '''Extract the names for all positional parameters and any variable length parameters available for the callable `F`.'''
        F_VARARG = 0x4
        F_VARKWD = 0x8
        F_VARGEN = 0x20

        # Check some of the attributes of the code type and verify that it's a proper candidate
        co = F.__code__
        flags, varnames = co.co_flags, iter(co.co_varnames)
        if (flags & F_VARGEN):
            raise TypeError("Unable to memoize a callable ({!s}) that is a generator type.".format(F))

        # Extract the positional argument names including any variable argument names
        items = islice(varnames, co.co_argcount)
        positional_arguments = tuple(items)
        variable_arguments = (next(varnames) if flags & F_VARARG else None, next(varnames) if flags & F_VARKWD else None)

        # Return the argument names and a tuple of the variable arguments that are available
        return positional_arguments, variable_arguments

    # Define our getter class that we will use to keep track of the memoized
    # method and cache all of its results
    class MemoizedMethod(object):
        def __init__(self, F, Karguments, Kattributes):
            '''Instantiate class using the provided parameters and attributes to generate the key for the memoized function F.'''
            self.cache_name, self.callable = 'MemoizedMethod_cache', F

            # Attributes used to generate a key for items in the cache
            self.Karguments = [item for item in Karguments]
            self.Kattributes = [(name, item) for name, item in sorted(Kattributes.items() if isinstance(Kattributes, dict) else Kattributes)]

            # Persist information from the callable's parameters that we will need. Since this
            # is a method, we'll need to consume the first parameter since it's just going to
            # be the instance identifier.
            Favailable, self.Fvarargs = extract_parameters(F)
            self.Fargs = [item for item in Favailable]

        def key(self, *args, **kwargs):
            '''Generate a key for the given parameter values.'''
            values = iter(args)

            # Build a dictionary of the arguments using the parameter names we fetched earlier,
            # and combine them with the keyword parameters we were given now.
            parameters = {argname : argvalue for argname, argvalue in zip(self.Fargs, values)}
            parameters.update(kwargs)

            # Now we need to extract the variable arguments and variable keywords. If the
            # callable has a variable-length parameter, then consume the rest of the values
            # so that it can be stored. If the callable has a keyword-argument parameter, then
            # copy it into a dictionary so we can store it.
            Fvarargs, Fvarkwds = self.Fvarargs
            if Fvarargs is not None:
                parameters[Fvarargs] = tuple(values)
            if Fvarkwds is not None:
                parameters[Fvarkwds] = { key : value for key, value in kwargs.items() }

            # Now we have a dictionary containing all our parameter values keyed by their
            # name, we need to iterate through our arguments whilst retaining their order so
            # that we can combine them into a tuple that we can use as a key for our cache.
            key_positionals = (parameters.get(key, undefined) for key in self.Karguments)
            key_callables = (Fattribute(parameters[key]) if callable(Fattribute) else getattr(parameters[key], Fattribute, undefined) for key, Fattribute in self.Kattributes)
            iterable = itertools.chain(key_positionals, [memoization_key_barrier], key_callables)
            return tuple(iterable)

        def __set_name__(self, object, name):
            self.cache_name = "MemoizedMethod<{:s}>_cache".format(name)
            # FIXME: we should use self.callable as a key for the real cache so
            #        that we don't have to ensure the cache names have to be unique.

        def __get__(self, object, type):

            # Figure out if we're being called with an empty object, because if so
            # then we need to return the original callable so that it looks like
            # we haven't tampered with it in any way.
            if object is None:
                return self.callable

            # Otherwise we have an object, and we need to grab the cache out of
            # it using the property that we calculated. If the cache isn't there
            # yet, then we need to stash an empty one there so that we can use it.
            cache_name = "__{:s}".format(self.cache_name)
            if not hasattr(object, cache_name):
                setattr(object, cache_name, {})
            # FIXME: we should use self.callable as a key of some sort in case
            #        the duplicate name being stored to the object's cache won't
            #        result in the same cache being used for more than one method
            #        within the same instance.

            # Grab the cache that is associated with our object, and the method that will be
            # called if the memoization key is not found in it.
            cache, method = getattr(object, cache_name), instancemethod(self.callable, object)

            def callee(*args, **kwargs):
                identity = self.key(object, *args, **kwargs)
                if identity in cache:
                    return cache[identity]

                # The key that we generated was not found in the cache. So,
                # we need to execute the callable, grab the result, and store
                # it into the cache using our key.
                result = method(*args, **kwargs)
                return cache.setdefault(identity, result)
            return functools.update_wrapper(callee, self.callable)

    # Define the closures that are used to when decorating a method
    def prepare(F, karguments=karguments, kattributes=kattributes):
        return MemoizedMethod(F, karguments, kattributes)

    def prepare_all(F):
        positional_arguments, variable_arguments = extract_parameters(F)
        arguments = itertools.chain(positional_arguments, filter(None, variable_arguments))
        return prepare(F, karguments=arguments, kattributes={})

    # If we were only given a single argument, then this is parameter-less
    # decorator that is being used and we use all arguments as a key.
    if len(karguments) == 1 and callable(karguments[0]) and not kattributes:
        return prepare_all(*karguments, **kattributes)

    # Otherwise our parameters are the arguments that we use to make a key,
    # and we need to need to return a closure to receive the callable to decorate.
    return prepare

if not any(hasattr(memoize_method, __attribute__) for __attribute__ in ['func_code', '__code__']):
    Log.warning("{:s} : Memoization (method) will be disabled due to the current implementation of python{:s} not allowing access of a function's code attributes (performance will be affected).".format(__name__, " ({:s})".format(sys.implementation.name) if hasattr(sys, 'implementation') else ''))
    memoize_method = fakedecorator

# check equivalency of two callables
def callable_eq2(ca, a, cb, b):
    a_ = a.im_func if isinstance(a, types.MethodType) else a
    b_ = b.im_func if isinstance(b, types.MethodType) else b
    return a_ is b_

def callable_eq3(ca, a, cb, b):
    a_ = a.__func__ if isinstance(a, types.MethodType) else a
    b_ = b.__func__ if isinstance(b, types.MethodType) else b
    return a_ is b_

def callable_equ(ca, a, cb, b):
    '''micropython'''
    if ca is cb is None:
        return a is b

    # if everything is defined (not None), then we need both namespaces.
    elif all((ca, cb)):
        nsa, nsb = ca.__dict__, cb.__dict__
        ta, tb = ca.__class__.__dict__, cb.__class__.__dict__

        aname, bname = a.__name__, b.__name__
        fa, fb = nsa.get(aname, ta.get(aname, 1)), nsb.get(bname, tb.get(bname, 2))

    # otherwise one of them is None and the other is not...so put them
    # in the exact same variable so we can use the same logic.
    else:
        c, name, other = (ca, a.__name__, b) if cb is None else (cb, b.__name__, a)
        ns, t = c.__dict__, c.__class__.__dict__
        fa, fb = ns.get(name, t.get(name, 1)), other
    return fa is fb

if any(hasattr(callable_equ, __attribute__) for __attribute__ in ['__code__', 'func_code']):
    callable_eq = callable_eq2 if sys.version_info[0] < 3 else callable_eq3
else:
    callable_eq = callable_equ

# operator implementations
class fakeoperator(object):
    @staticmethod
    def itemgetter(item, *args):
        '''
        Return a callable object that fetches the given item(s) from its operand.
        After f = itemgetter(2), the call f(r) returns r[2].
        After g = itemgetter(2, 5, 3), the call g(r) returns (r[2], r[5], r[3])
        '''
        def getter(object):
            if not args:
                return object[item]
            iterable = (object[n] for n in [item] + [arg for arg in args])
            return tuple(iterable)
        if hasattr(getter, '__name__'):
            getter.__name__ = "itemgetter({:s})".format(', '.join(map("{!s}".format, [item] + [arg for arg in args]))) if args else "itemgetter({!s})".format(item)
        return getter

    @staticmethod
    def methodcaller(name, *args, **kargs):
        '''
        Return a callable object that calls the given method on its operand.
        After f = methodcaller('name'), the call f(r) returns r.name().
        After g = methodcaller('name', 'date', foo=1), the call g(r) returns
        r.name('date', foo=1).
        '''
        def getter(object):
            callable = getattr(object, name)
            return callable(*args, **kargs)
        if not isinstance(name, str):
            raise TypeError('method name must be a string')
        if hasattr(getter, '__name__'):
            getter.__name__ = "methodcaller({:s}{:s})".format(', '.join(map("{!r}".format, [name] + [arg for arg in args])), ", {:s}".format(', '.join("{:s}={!r}".format(*karg) for karg in kargs.items())) if kargs else '')
        return getter

    @staticmethod
    def setitem(a, b, c):
        '''Same as a[b] = c.'''
        a[b] = c
    @staticmethod
    def getitem(a, b):
        '''Same as a[b].'''
        return a[b]
    @staticmethod
    def add(a, b):
        '''Same as a + b.'''
        return a + b

if not all(hasattr(operator, __attribute__) for __attribute__ in ['itemgetter', 'methodcaller', 'setitem', 'getitem', 'add']):
    Log.info("{:s} : Using custom implementation of `{:s}` module due to the current implementation of python{:s} not defining required callables (performance will be affected).".format(__name__, 'operator', " ({:s})".format(sys.implementation.name) if hasattr(sys, 'implementation') else ''))
    operator = fakeoperator

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
    from ptypes import utils

    @mapexception({Failure:Success})
    def blah_failure_to_success():
        raise Failure
    @mapexception(any=Success)
    def blah_success():
        raise OSError
    @mapexception({Failure:Failure})
    def blah_nomatch():
        raise OSError
    @mapexception()
    def blah_noexception():
        pass
    @mapexception({(OSError,StopIteration):Success})
    def blah_multiple_1():
        raise OSError
    @mapexception({(OSError,StopIteration):Success})
    def blah_multiple_2():
        raise StopIteration
    @mapexception(ignored=(OSError,))
    def blah_pass():
        raise OSError

    class blah(object):
        @mapexception({Failure:Success})
        def method(self):
            raise Failure

    @TestCase
    def test_mapexception_1():
        try:
            blah_failure_to_success()
        except Success:
            raise Success
    @TestCase
    def test_mapexception_2():
        try:
            blah_success()
        except Success:
            raise Success
    @TestCase
    def test_mapexception_3():
        try:
            blah_nomatch()
        except OSError:
            raise Success
    @TestCase
    def test_mapexception_4():
        try:
            blah_noexception()
        except Exception:
            raise Failure
        raise Success
    @TestCase
    def test_mapexception_5():
        try:
            blah_multiple_1()
        except Success:
            raise Success
    @TestCase
    def test_mapexception_6():
        try:
            blah_multiple_2()
        except Success:
            raise Success
    @TestCase
    def test_mapexception_7():
        try:
            x = blah()
            x.method()
        except Success:
            raise Success
    @TestCase
    def test_mapexception_8():
        try:
            x = blah_pass()
        except OSError:
            raise Success

    @TestCase
    def test_memoize_fn_1():
        @utils.memoize('arg1','arg2')
        def blah(arg1,arg2,arg3,arg4):
            blah.counter += 1
            return arg1+arg2
        blah.counter = 0
        blah(15,20,0,0)
        blah(35,30,0,0)
        res = blah(15,20, 30,35)
        if res == 35 and blah.counter == 2:
            raise Success

    @TestCase
    def test_memoize_fn_2():
        @utils.memoize('arg1','arg2', arg3='attribute')
        def blah(arg1,arg2,arg3):
            blah.counter += 1
            return arg1+arg2
        class f(object): attribute=10
        class g(object): attribute=20
        blah.counter = 0
        blah(15,20,f)
        blah(15,20,g)
        res = blah(15,20,f)
        if res == 35 and blah.counter == 2:
            raise Success

    @TestCase
    def test_memoize_fn_3():
        x,y,z = 10,15,20
        @utils.memoize('arg1','arg2', kwds=lambda n: n['arg3'])
        def blah(arg1,arg2,**kwds):
            blah.counter += 1
            return arg1+arg2
        blah.counter = 0
        blah(15,20,arg3=10)
        blah(15,20,arg3=20)
        res = blah(15,20,arg3=10)
        if res == 35 and blah.counter == 2:
            raise Success

    @TestCase
    def test_memoize_im_1():
        class a(object):
            counter = 0
            @utils.memoize('self','arg')
            def blah(self, arg):
                a.counter += 1
                return arg * arg
        x = a()
        x.blah(10)
        x.blah(5)
        res = x.blah(10)
        if x.counter == 2 and res == 100:
            raise Success

    @TestCase
    def test_memoize_im_2():
        class a(object):
            def __init__(self): self.counter = 0
            @utils.memoize('self','arg', self='test')
            def blah(self, arg):
                self.counter += 1
                return arg * arg
            test = 100
        x,y = a(),a()
        x.blah(10)
        x.blah(5)
        y.blah(10)
        res = x.blah(10)
        if x.counter == 2 and y.counter == 1 and res == 100:
            raise Success

    @TestCase
    def test_memoize_im_3():
        class a(object):
            def __init__(self): self.counter = 0
            @utils.memoize('self','arg', self=lambda s: s.test)
            def blah(self, arg):
                self.counter += 1
                return arg * arg
            test = 100
        x,y = a(),a()
        x.blah(10)
        x.blah(5)
        y.blah(10)
        res = x.blah( 10)
        if x.counter == 2 and y.counter == 1 and res == 100:
            raise Success

    @TestCase
    def test_hexrow():
        data = b'\0' * 16
        row = hexrow(data, offset=0, width=16, breaks=[8])
        if row == '  '.join(['0000', ' '.join(8*['00']), ' '.join(8*['00']), '.'*16]):
            raise Success

    @TestCase
    def test_callableeq_function_same():
        def callable(*args):
            return True
        if callable_eq(None, callable, None, callable) and callable():
            raise Success

    @TestCase
    def test_callableeq_function_diff():
        def callable1(*args):
            return True
        def callable2(*args):
            return True
        if not callable_eq(None, callable1, None, callable2) and all(item() for item in [callable1, callable2]):
            raise Success

    @TestCase
    def test_callableeq_methodclass_same_1():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A(), A
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodclass_same_2():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A, None
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodclass_same_3():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A(), None
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodclass_diff_1():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method
        class B(A):
            def method(*self):
                return True

        x, y = A(), B
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodclass_diff_2():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method
        class B(A):
            def method(*self):
                return True

        x, y = A(), B()
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_same_1():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A(), A()
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_same_2():
        def method(*self):
            return True
        class A(object):
            pass
        class B(object):
            pass
        A.method = method
        B.method = method

        x, y = A, B
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_same_3():
        def method(*self):
            return True
        class A(object):
            pass
        class B(object):
            pass
        A.method = method
        B.method = method

        x, y = A(), B()
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_diff_1():
        def method(*self):
            return True
        class A(object):
            def method(*self):
                return True
        class B(object):
            pass
        B.method = method

        x, y = A, B
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_diff_2():
        def method(*self):
            return True
        class A(object):
            def method(*self):
                return True
        class B(object):
            pass
        B.method = method

        x, y = A(), B()
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_diff_3():
        def method(*self):
            return True
        class A(object):
            def method(*self):
                return True
        class B(object):
            pass
        B.method = method

        x, y = A(), B
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodmethod_diff_4():
        def method(*self):
            return True
        class A(object):
            def method(*self):
                return True
        class B(object):
            pass
        B.method = method

        x, y = A(), None
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_methodfunc_same():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A(), None
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_same_1():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method
        class B(A): pass

        x, y = A(), B()
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_same_2():
        class X(object):
            pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X): pass

        x, y = A, B
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_same_3():
        class X(object):
            pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X): pass

        x, y = A(), B()
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_same_4():
        class X(object):
            pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X): pass

        x, y = A(), B
        if callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_diff_1():
        class X(object): pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X):
            def method(*self):
                return True

        x, y = A, B
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_diff_2():
        class X(object): pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X):
            def method(*self):
                return True

        x, y = A(), B()
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_callableeq_inheritance_diff_3():
        class X(object): pass
        def method(*self):
            return True
        X.method = method
        class A(X): pass
        class B(X):
            def method(*self):
                return True

        x, y = A(), B()
        if not callable_eq(x, x.method, y, method if y is None else y.method) and all(item() for item in [x.method, method if y is None else y.method]):
            raise Success

    @TestCase
    def test_padding_sourcerepeat():
        source = padding.source.repeat(iter(b'\0' * 2))
        zero, iterable = bytearray(b'\0')[0], (item for item in iterbytes(source))
        if next(iterable) == zero and next(iterable) == zero and next(iterable) == zero and next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourceiterable():
        source = padding.source.iterable(iter(b'\0' * 2))
        zero, iterable = bytearray(b'\0')[0], (item for item in iterbytes(source))
        if next(iterable) == zero and next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourcezero():
        source = padding.source.zero()
        zero, iterable = bytearray(b'\0')[0], (item for item in iterbytes(source))
        if next(iterable) == zero and next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourcefile():
        class fakefile(object):
            def __init__(self, data):
                self.iterable = iter(bytearray(data))
            def read(self, count):
                res = bytearray()
                while count > 0:
                    res += bytearray([next(self.iterable)])
                    count -= 1
                return bytes(res)

        filedata = b'hola'
        f = fakefile(filedata)
        source = padding.source.file(f)

        for a, b in zip(source, bytearray(filedata)):
            if a != bytes(bytearray([b])):
                raise Failure
            continue
        raise Success

    @TestCase
    def test_padding_sourceprng():
        seed = id(0)
        random.seed(seed)
        res = bytes(bytearray(random.randint(0, 0xff) for i in range(0x10)))
        source = padding.source.prng(seed)

        for a, b in zip(res, source):
            if a != b:
                raise Failure
            continue
        raise Success

    @TestCase
    def test_padding_fillzero():
        source = padding.source.zero()
        data = padding.fill(0x10, source)
        if data == b'\0'*0x10:
            raise Success

    @TestCase
    def test_padding_fillrepeat():
        source = padding.source.repeat(b'A')
        data = padding.fill(0x10, source)
        if data == b'A'*0x10:
            raise Success

    @TestCase
    def test_padding_filliterable():
        source = padding.source.iterable(b'ABCD')
        data = padding.fill(4, source)
        if data == b'ABCD':
            raise Success

    @TestCase
    def test_printable():
        data = b'fuckyou\0\0\0\0'
        if utils.printable(data) == 'fuckyou....':
            raise Success

    @TestCase
    def test_hexdump():
        offset = 57005
        data = b'fuckyou\0\0\0\0' * 2

        left_items = ["{:04x}".format(offset + i) for i in range(0, len(data), 16)]
        center_items = [ "{:02x}".format(item) for item in bytearray(data) ]
        center_items += ['  '] * (16 - len(data) % 16)
        right_items = utils.printable(data) + ' ' * (16 - len(data) % 16)

        center_chunks = []
        for i in range(0, len(center_items), 8):
            res = []
            for j in range(0, 8):
                res.append(center_items[i + j])
            center_chunks.append(res)

        left_iterable = iter(left_items)
        center_iterable = iter(center_chunks)
        right_iterable = iter(right_items)

        res = []
        res.append('  '.join([next(left_iterable), ' '.join(next(center_iterable)), ' '.join(next(center_iterable)), str().join(utils.islice(right_iterable, 16))]))
        res.append('  '.join([next(left_iterable), ' '.join(next(center_iterable)), ' '.join(next(center_iterable)), str().join(utils.islice(right_iterable, 16))]))

        if utils.hexdump(data, offset=offset, width=16) == '\n'.join(res):
            raise Success

    @TestCase
    def test_emit_repr():
        data = b'fuckyou\0\0\0\0' * 2
        match = str().join(map("\\x{:02x}".format, bytearray(data)))
        if emit_repr(data) == match:
            raise Success

    @TestCase
    def test_memoize_force_1():
        @utils.memoize('arg')
        def f(arg, manipulate=2):
            return manipulate * arg

        [f(item) for item in [20, 30, 20, 30]]

        if f(20, manipulate=3) != 2 * 20:
            raise Failure

        if f.force(20, manipulate=1) == 1 * 20:
            raise Success

    @TestCase
    def test_memoize_force_2():
        @utils.memoize('arg')
        def f(arg, manipulate=2):
            return manipulate * arg

        [f(item) for item in [20, 30, 20, 30]]
        if f(20, manipulate=3) != 2 * 20:
            raise Failure

        f.force(20, manipulate=1)

        if f(20, manipulate=20) == 1 * 20:
            raise Success

    @TestCase
    def test_memoize_fetch_1():
        args = []
        @utils.memoize('arg')
        def f(arg, args=args):
            args.append(arg)
            return 2 * arg

        [f(item) for item in [20, 30, 20, 30]]
        if args != [20, 30]:
            raise Failure

        if f.fetch(30) == 2 * 30:
            raise Success

    @TestCase
    def test_memoize_fetch_2():
        args = []
        @utils.memoize('arg')
        def f(arg, args=args):
            args.append(arg)
            return 2 * arg

        [f(item) for item in [20, 30, 20, 30]]
        if args != [20, 30]:
            raise Failure

        try:
            f.fetch(40)
        except KeyError:
            raise Success

        raise Failure

    @TestCase
    def test_memoize_store_1():
        args = []
        @utils.memoize('arg')
        def f(arg, args=args):
            args.append(arg)
            return 2 * arg

        [f(item) for item in [20, 30, 20, 30]]
        if args != [20, 30]:
            raise Failure

        if f.store(30)(15) == 15:
            raise Success

    @TestCase
    def test_memoize_store_2():
        args = []
        @utils.memoize('arg')
        def f(arg, args=args):
            args.append(arg)
            return 2 * arg

        [f(item) for item in [20, 30, 20, 30]]
        if args != [20, 30]:
            raise Failure

        if f.fetch(30) != 2 * 30:
            raise Failure

        if f.store(30)(15) != 15:
            raise Failure

        if f(30) == 15:
            raise Success

    @TestCase
    def test_memoize_crossstore_1():
        class mine(object):
            def __init__(self):
                self.count = 0
            @utils.memoize('arg')
            def method(self, arg):
                self.count += 1
                return arg * 2

        self, expected = mine(), 0
        if self.count != expected:
            raise AssertionError
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure

        # the memoized decorator is specific to the method definition
        # and therefore the cache that is used between various
        # implementations is share.
        self2, expected = mine(), 0
        if self2.count != expected:
            raise AssertionError
        result, expected = self2.method(20), 40
        if not (result == expected and self2.count == 0):
            raise Failure
        result, expected = self2.method(20), 40
        if not (result == expected and self2.count == 0):
            raise Failure
        raise Success

    @TestCase
    def test_memoize_crossstore_2():
        class mine(object):
            def __init__(self):
                self.count = 0
            @utils.memoize_method('arg')
            def method(self, arg):
                self.count += 1
                return arg * 2

        self, expected = mine(), 0
        if self.count != expected:
            raise AssertionError
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure

        # the memoized method is using a cache that is locked to the
        # instance the method is associated with.
        self2, expected = mine(), 0
        if self2.count != expected:
            raise Failure
        result, expected = self2.method(20), 40
        if not (result == expected and self2.count == 1):
            raise Failure
        result, expected = self2.method(20), 40
        if not (result == expected and self2.count == 1):
            raise Failure
        raise Success

    @TestCase
    def test_memoize_crossstore_3():
        class mine(object):
            def __init__(self):
                self.count = 0
            @utils.memoize_method('arg')
            def method(self, arg):
                self.count += 1
                return arg * 2
            @utils.memoize_method('arg')
            def method2(self, arg):
                self.count += 1
                return 1 + arg * 2

        self, expected = mine(), 0
        if self.count != expected:
            raise AssertionError
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure
        result, expected = self.method(20), 40
        if not (result == expected and self.count == 1):
            raise Failure
        result, expected = self.method2(20), 41
        if not (result == expected and self.count == 2):
            raise Failure
        result, expected = self.method2(20), 41
        if not (result == expected and self.count == 2):
            raise Failure
        raise Success

    @TestCase
    def test_byteorder_0():
        F = utils.byteorder_calculator(8)
        if next(F) == (7, 0):
            raise Success

    @TestCase
    def test_byteorder_1():
        F = utils.byteorder_calculator(8)
        if next(F) == (7, 0) and F.send(8 * 7) == (0, 0):
            raise Success

    @TestCase
    def test_byteorder_2():
        F = utils.byteorder_calculator(8)
        if next(F) == (7, 0) and F.send(8 * 8) == (15, 0):
            raise Success

    @TestCase
    def test_byteorder_3():
        F = utils.byteorder_calculator(4)
        if next(F) == (3, 0):
            raise Success

    @TestCase
    def test_byteorder_4():
        F = utils.byteorder_calculator(4)
        if next(F) == (3, 0) and F.send(8 * 3) == (0, 0):
            raise Success

    @TestCase
    def test_byteorder_5():
        F = utils.byteorder_calculator(4)
        if next(F) == (3, 0) and F.send(8 * 4) == (7, 0):
            raise Success

    @TestCase
    def test_byteorder_6():
        F = utils.byteorder_calculator(16)
        if next(F) == (15, 0):
            raise Success

    @TestCase
    def test_byteorder_7():
        F = utils.byteorder_calculator(16)
        if next(F) == (15, 0) and F.send(8 * 15) == (0, 0):
            raise Success

    @TestCase
    def test_byteorder_8():
        F = utils.byteorder_calculator(16)
        if next(F) == (15, 0) and F.send(8 * 16) == (31, 0):
            raise Success

    @TestCase
    def test_position_calculate_0():
        I = utils.position_calculator(8, base=0, position=(8, 0))
        if next(I) == (8, 0) and I.send(0) == (8, 0):
            raise Success

    @TestCase
    def test_position_calculate_1():
        I = utils.position_calculator(8, base=8, position=(8, 0))
        if next(I) == (8, 0) and I.send(0) == (8, 0):
            raise Success

    @TestCase
    def test_position_calculate_2():
        I = utils.position_calculator(8, base=8, position=(12, 0))
        if next(I) == (12, 0) and I.send(8 * 4) == (8, 0):
            raise Success

    @TestCase
    def test_position_calculate_3():
        I = utils.position_calculator(8, base=8, position=(15, 0))
        if next(I) == (15, 0) and I.send(8 * 2) == (13, 0):
            raise Success

    @TestCase
    def test_position_calculate_4():

        # logically, we shouldn't be able to seek backwards...but
        # mathematically we can. seeking to (0, 0), pushes us forward
        # to the next dword at offset 4...which means 16-bits = 4+2

        I = utils.position_calculator(4, base=3, position=(0, 0))
        if next(I) == (0, 0) and I.send(8 * 2) == (6, 0):
            raise Success

    @TestCase
    def test_position_calculate_5():
        I = utils.position_calculator(16, base=0, position=(0, 0))
        if next(I) == (0, 0) and I.send(8 * 16) == (16, 0):
            raise Success

    @TestCase
    def test_position_calculate_6():
        I = utils.position_calculator(16, base=4, position=(4, 0))
        if next(I) == (4, 0) and I.send(8 * 16) == (16 + 4, 0):
            raise Success

    @TestCase
    def test_position_calculate_7():
        I = utils.position_calculator(16, base=0, position=(13, 0))
        if next(I) == (13, 0) and I.send(8) == (12, 0):
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
