import sys,math,random
import functools,operator,itertools,types
import six

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

    def __init__(self, *objects, **attrs):
        self.objects = objects
        self.attributes = { self.magical.get(k, k) : v for k, v in six.iteritems(attrs) }

    def __enter__(self):
        objects, attrs = self.objects, self.attributes
        self.states = tuple( dict((k, getattr(o, k)) for k in attrs.keys()) for o in objects)
        [o.__update__(attrs) for o in objects]
        return objects

    def __exit__(self, exc_type, exc_value, traceback):
        [o.__update__(a) for o, a in zip(self.objects, self.states)]
        return

## ptype padding types
class padding:
    """Used for providing padding."""
    class source:
        def __bytesdecorator__(method):
            def closure(*args, **kwargs):
                iterable = method(*args, **kwargs)
                return (six.int2byte(item) for item in iterable)
            return closure if sys.version_info.major < 3 else method

        @classmethod
        @__bytesdecorator__
        def repeat(cls, value):
            iterable = six.iterbytes(value)
            return itertools.cycle(iterable)

        @classmethod
        @__bytesdecorator__
        def iterable(cls, iterable):
            return six.iterbytes(iterable)

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
            return six.iterbytes(cls.repeat(b'\x00'))

    @classmethod
    def fill(cls, amount, source):
        """Returns a bytearray of ``amount`` elements, from the specified ``source``"""
        iterable = itertools.islice(source, amount)
        return bytes().join(six.int2byte(item) for item in six.iterbytes(iterable))

## exception remapping
def mapexception(map={}, any=None, ignored=()):
    """Decorator for a function that maps exceptions from one type into another.

    ``map`` is a dictionary describing how to map exceptions. Each key can be a single item or a tuple which will then be mapped to the exception type specified in the value.
    ``any`` describes the exception to raise if any exception is raised. None can be used to use the raised exception.
    ``ignored`` specifies a list of exceptions to pass through unmodified
    """
    if not isinstance(map, dict):
        raise AssertionError("The type of the exception map ({!s}) is expected to be of a mappable type".format(type(map)))
    if not hasattr(ignored, '__contains__'):
        raise AssertionError("The type of the ignored list ({!s}) is expected to contain of exceptions".format(type(ignored)))
    if any is not None and not issubclass(any, BaseException):
        raise AssertionError("The type of the exception to raise ({!s}) is expected to inherit from the {!s} type".format(any, BaseException))

    def decorator(fn):
        def decorated(*args, **kwds):
            try:
                return fn(*args, **kwds)

            except Exception:
                type, value, traceback = sys.exc_info()

            with_traceback = (lambda item: item) if sys.version_info.major < 3 else operator.methodcaller('with_traceback', traceback)

            for src, dst in six.iteritems(map):
                if type is src or (hasattr(src, '__contains__') and type in src):
                    raise with_traceback(dst(type, value))
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
        return res.format(ofs, math.trunc(partial * 10**precision))
    return "{:x}.{:x}".format(ofs, bofs)

## hexdumping capability
def printable(data, nonprintable=u'.'):
    """Return a string of only printable characters"""
    return functools.reduce(lambda agg, item: agg + (six.int2byte(item).decode(sys.getdefaultencoding()) if item >= 0x20 and item < 0x7f else nonprintable), bytearray(data), u'')

def hexrow(value, offset=0, width=16, breaks=[8]):
    """Returns ``value as a formatted hexadecimal str"""
    value = bytearray(value)[:width]
    extra = width - len(value)

    ## left
    left = "{:04x}".format(offset)

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

    return '  '.join((left, middle, right))

def hexdump(value, offset=0, width=16, rows=None, **kwds):
    """Returns ``value`` as a formatted hexdump

    If ``offset`` is specified, then the hexdump will start there.
    If ``rows`` or it's alias ``lines`` is specified, only that number of rows
    will be displayed.
    """

    rows = kwds.pop('rows', kwds.pop('lines', None))
    value = iter(value)

    getRow = lambda o: hexrow(data, offset=o, **kwds)

    res = []
    (ofs, data) = offset, bytearray(itertools.islice(value, width))
    for i in (itertools.count(1) if rows is None else range(1, rows)):
        res.append( getRow(ofs) )
        ofs, data = ofs + width, bytearray(itertools.islice(value, width))
        if len(data) < width:
            break
        continue

    if len(data) > 0:
        res.append( getRow(ofs) )
    return '\n'.join(res)

def emit_repr(data, width=0, message=' .. skipped {leftover} chars .. ', padding=' ', **formats):
    """Return a string replaced with ``message`` if larger than ``width``

    Message can contain the following format operands:
    width = width to be displayed
    charwidth = width of each character
    bytewidth = number of bytes that can fit within width
    length = number of bytes displayed
    leftover = approximate number of bytes skipped
    **format = extra format specifiers for message
    """
    size = len(data)
    charwidth = len(r'\xFF')
    bytewidth = width // charwidth
    leftover = size - bytewidth

    hexify = lambda s: str().join(map(r"\x{:02x}".format, six.iterbytes(s)))

    if width <= 0 or bytewidth >= len(data):
        return hexify(data)

    # FIXME: the skipped/leftover bytes are being calculated incorrectly..
    msg = message.format(size=size, charwidth=charwidth, width=width, leftover=leftover, **formats)

    # figure out how many bytes we can print
    bytefrac, bytewidth = math.modf((width - len(msg)) * 1.0 / charwidth)
    padlength = math.trunc(charwidth * bytefrac)

    msg = padding * math.trunc(padlength / 2.0 + 0.5) + msg + padding * math.trunc(padlength / 2)
    left, right = data[:math.trunc(bytewidth / 2 + 0.5)], data[size - math.trunc(bytewidth / 2):]
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
    has_function = (lambda F: hasattr(F, 'im_func')) if sys.version_info.major < 3 else (lambda F: hasattr(F, '__func__'))
    get_function = (lambda F: F.im_func) if sys.version_info.major < 3 else (lambda F: F.__func__)

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
        argnames = itertools.islice(varnames, co.co_argcount)
        c_positional = tuple(argnames)
        c_attribute = kattrs
        c_var = (six.next(varnames) if flags & F_VARARG else None, six.next(varnames) if flags & F_VARKWD else None)
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

        # set some utilies on the memoized function
        callee.memoize_key = lambda *args, **kwargs: key(*args, **kwargs)
        callee.memoize_key.__doc__ = """Generate a unique key based on the provided arguments."""
        callee.memoize_cache = lambda: cache
        callee.memoize_cache.__doc__ = """Return the current memoize cache."""
        callee.memoize_clear = lambda: cache.clear()
        callee.memoize_clear.__doc__ = """Empty the current memoize cache."""
        callee.force = lambda *args, **kwargs: force(*args, **kwargs)
        callee.force.__doc__ = """Force calling the function whilst updating the memoize cache."""

        callee.__name__ = fn.__name__
        callee.__doc__ = fn.__doc__
        callee.callable = fn
        return callee if isinstance(callee, types.FunctionType) else types.FunctionType(callee)
    return prepare_callable(kargs.pop(0)) if not kattrs and len(kargs) == 1 and callable(kargs[0]) else prepare_callable

# check equivalency of two callables
def callable_eq2(a, b):
    a_ = a.im_func if isinstance(a, types.MethodType) else a
    b_ = b.im_func if isinstance(b, types.MethodType) else b
    return a_ is b_

def callable_eq3(a, b):
    a_ = a.__func__ if isinstance(a, types.MethodType) else a
    b_ = b.__func__ if isinstance(b, types.MethodType) else b
    return a_ is b_

callable_eq = callable_eq2 if sys.version_info.major < 3 else callable_eq3

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
        except:
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
    def test_method_eq():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x, y = A(), A()
        if callable_eq(x.method, y.method) and all(item() for item in [x.method, y.method]):
            raise Success

    @TestCase
    def test_method_eq_callable():
        def method(*self):
            return True
        class A(object):
            pass
        A.method = method

        x = A()
        if callable_eq(x.method, method) and all(item() for item in [x.method, method]):
            raise Success

    @TestCase
    def test_padding_sourcerepeat():
        source = padding.source.repeat(iter(b'\0' * 2))
        zero, iterable = six.byte2int(b'\0'), six.iterbytes(source)
        if six.next(iterable) == zero and six.next(iterable) == zero and six.next(iterable) == zero and six.next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourceiterable():
        source = padding.source.iterable(iter(b'\0' * 2))
        zero, iterable = six.byte2int(b'\0'), six.iterbytes(source)
        if six.next(iterable) == zero and six.next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourcezero():
        source = padding.source.zero()
        zero, iterable = six.byte2int(b'\0'), six.iterbytes(source)
        if six.next(iterable) == zero and six.next(iterable) == zero:
            raise Success

    @TestCase
    def test_padding_sourcefile():
        class fakefile(object):
            def __init__(self, data):
                self.iterable = iter(bytearray(data))
            def read(self, count):
                res = b''
                while count > 0:
                    res += six.int2byte(six.next(self.iterable))
                    count -= 1
                return res

        filedata = b'hola'
        f = fakefile(filedata)
        source = padding.source.file(f)

        for a, b in zip(source, bytearray(filedata)):
            if a != six.int2byte(b):
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
        res.append('  '.join([next(left_iterable), ' '.join(next(center_iterable)), ' '.join(next(center_iterable)), str().join(itertools.islice(right_iterable, 16))]))
        res.append('  '.join([next(left_iterable), ' '.join(next(center_iterable)), ' '.join(next(center_iterable)), str().join(itertools.islice(right_iterable, 16))]))

        if utils.hexdump(data, offset=offset, width=16) == '\n'.join(res):
            raise Success

    @TestCase
    def test_emit_repr():
        data = b'fuckyou\0\0\0\0' * 2
        match = str().join(map("\\x{:02x}".format, bytearray(data)))
        if emit_repr(data) == match:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
