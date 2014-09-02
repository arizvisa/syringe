import sys,itertools,_random,math
import functools,random

## string formatting
def strdup(string, terminator='\x00'):
    """Will return a copy of ``string`` up to the provided ``terminated``"""
    string = iter(string)
    res = ''
    for x in string:
        if x == terminator:
            break
        res += x
    return res

def indent(string, tabsize=4, char=' ', newline='\n'):
    """Indent each line of ``string`` with the specified tabsize"""
    indent = char*tabsize
    strings = [(indent + x) for x in string.split(newline)]
    return newline.join(strings)

## temporary attribute assignments for a context
class assign(object):
    """Will temporarily assign the provided attributes to the specified to all code within it's scope"""
    def __init__(self, *objects, **attrs):
        self.objects = objects
        self.attributes = attrs

    def __enter__(self):
        objects,attrs = self.objects,self.attributes
        self.states = tuple( dict((k,getattr(o,k)) for k in attrs.keys()) for o in objects)
        [o.update_attributes(attrs) for o in objects]
        return objects

    def __exit__(self, exc_type, exc_value, traceback):
        [o.update_attributes(a) for o,a in zip(self.objects,self.states)]
        return

## ptype padding types
class padding:
    """Used for providing padding."""
    class source:
        @classmethod
        def repeat(cls,value):
            return itertools.cycle(iter(value))

        @classmethod
        def source(cls,iterable):
            return (x for x in iter(iterable))

        @classmethod
        def file(cls,file):
            return itertools.imap(file.read, itertools.repeat(1))
            #return (file.read(1) for x in itertools.count())

        @classmethod
        def prng(cls,seed=None):
            random.seed(seed)
            return itertools.imap(chr, itertools.starmap(random.randint, itertools.repeat((0,0xff))))
            #return (chr(random.randint(0,0xff)) for x in itertools.count())

        @classmethod
        def zero(cls):
            return cls.repeat('\x00')

    @classmethod
    def fill(cls, amount, source):
        """Returns a string of ``amount`` elements, from the specified ``source``"""
        return ''.join(itertools.islice(source, amount))

## exception remapping
def mapexception(map={}, any=None, ignored=()):
    """Decorator for a function that maps exceptions from one type into another.

    /map/ is a dictionary describing how to map exceptions.
        Each tuple can be one of the following formats and will map any instance of Source to Destination
            (Source, Destination)
            ((Source1,Source2...), Destination)
    /any/ describes the exception to raise if any exception is raised.
        use None to pass the original exception through
    /ignored/ will allow exceptions of these types to fall through
    
    """
    assert type(map) is dict, 'exception /map/ expected to be of a dictionary type'
    assert hasattr(ignored, '__contains__'), '/ignored/ is expected to be a list of exceptions'
    if any is not None:
        assert issubclass(any,BaseException), '/any/ expected to be a solitary exception'

    def decorator(fn):
        def decorated(*args, **kwds):
            try:
                return fn(*args, **kwds)
            except:
                t,v,tb = sys.exc_info()

            for src,dst in map.iteritems():
                if t is src or (hasattr(src,'__contains__') and t in src):
                    raise dst(*v)
                continue
            if t in ignored or any is None:
                raise t(*v)
            raise any(*v)

        functools.update_wrapper(decorated, fn)
        return decorated
    return decorator

## naming representations of a type or instance
def repr_class(name):
    #return "<class '%s'>"% name
    return "<class %s>"% name
def repr_instance(classname, name):
    return "<instance %s '%s'>"% (classname, name)
def repr_position(pos, hex=True, precision=0):
    if len(pos) == 1:
        ofs, = pos
        return '{:x}'.format(ofs)
    ofs,bofs = pos
    if precision > 0:
        partial = bofs / 8.0
        if hex:
            return '{:x}.{:x}'.format(ofs,math.trunc(partial*0x10))
        fraction = ':0{:d}d'.format(precision)
        res = '{:x}.{'+fraction+'}'
        return res.format(ofs,math.trunc(partial * 10**precision))
    return '{:x}.{:x}'.format(ofs,bofs)

## hexdumping capability
def printable(s):
    """Return a string of only printable characters"""
    return reduce(lambda t,c: t + (c if ord(c) >= 0x20 and ord(c) < 0x7f else '.'), iter(s), '')

def hexrow(value, offset=0, length=16, breaks=[8]):
    """Returns ``value as a formatted hexadecimal str"""
    value = str(value)[:length]
    extra = length - len(value)

    ## left
    left = '%04x'% offset

    ## middle
    res = [ '%02x'%ord(x) for x in value ]
    if len(value) < length:
        res += ['  ' for x in range(extra)]

    for x in breaks:
        if x < len(res):
            res[x] = ' %s'% res[x]
    middle = ' '.join(res)

    ## right
    right = printable(value) + ' '*extra

    return '%s  %s  %s'% (left, middle, right)

def hexdump(value, offset=0, length=16, rows=None, **kwds):
    """Returns ``value`` as a formatted hexdump

    If ``offset`` is specified, then the hexdump will start there.
    If ``rows`` or it's alias ``lines`` is specified, only that number of rows
    will be displayed.
    """

    if 'lines' in kwds:
        rows = kwds.pop('lines')

    # TODO: should prolly make this an iterator somehow...
    value = iter(value)

    def tryRead(iterable, length):
        res = ''
        try:
            for x in itertools.islice(iterable, length):
                res += x
    
        except StopIteration:
            pass
        return res

    getRow = lambda o: hexrow(data, offset=o, **kwds)
    
    res = []
    (ofs, data) = offset, tryRead(value, length)
    for i in (itertools.count(1) if rows is None else xrange(1, rows)):
        res.append( getRow(ofs) )
        ofs, data = (ofs + length, tryRead(value, length))
        if len(data) < length:
            break
        continue

    if len(data) > 0:
        res.append( getRow(ofs) )
    return '\n'.join(res)

def emit_repr(data, width=0, message=' .. skipped {leftover} chars .. ', padding=' '):
    """Return a string replaced with ``message`` if larger than ``width``

    Message can contain the following format operands:
    width = width to be displayed
    charwidth = width of each character
    bytewidth = number of bytes that can fit within width
    length = number of bytes displayed
    leftover = approximate number of bytes skipped
    """
    size = len(data)
    charwidth = len(r'\xFF')
    bytewidth = width / charwidth
    leftover = size - bytewidth

    hexify = lambda s: ''.join('\\x%02x'%ord(x) for x in iter(s))

    if width <= 0 or bytewidth >= len(data):
        return hexify(data)

    # FIXME: the skipped/leftover bytes are being calculated incorrectly..
    msg = message.format(size=size, charwidth=charwidth, width=width, leftover=leftover)

    # figure out how many bytes we can print
    bytefrac,bytewidth = math.modf((width - len(msg)) * 1.0 / charwidth)
    padlength = math.trunc(charwidth*bytefrac)
    
    msg = padding*math.trunc(padlength/2.0+0.5) + msg + padding*math.trunc(padlength/2)
    left,right = data[:math.trunc(bytewidth/2 + 0.5)], data[size-math.trunc(bytewidth/2):]
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
    count = math.trunc(math.ceil(size*1.0/width))
    half = math.trunc(height/2.0)
    leftover = (count - half*2)
    skipped = leftover*width

    # display everything
    if height <= 0 or leftover <= 0:
        for o in xrange(0, size, width):
            yield hexrow(data[o:o+width], offset+o, width, **attrs)
        return

    # display rows
    o1 = offset
    for o in xrange(0, half*width, width):
        yield hexrow(data[o:o+width], o+o1, width, **attrs)
    yield message.format(leftover=leftover, height=height, count=count, skipped=skipped, size=size)
    o2 = width*(count-half)
    for o in xrange(0, half*width, width):
        yield hexrow(data[o+o2:o+o2+width], o+o2+offset, width, **attrs)
    return
    
if __name__ == '__main__':
    # test cases are found at next instance of '__main__'
    import config,logging
    config.defaults.log = logging.RootLogger(logging.DEBUG)

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
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':

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
        blah_failure_to_success()
    @TestCase
    def test_mapexception_2():
        blah_success()
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
        blah_multiple_1()
    @TestCase
    def test_mapexception_6():
        blah_multiple_2()
    @TestCase
    def test_mapexception_7():
        x = blah()
        x.method()
    @TestCase
    def test_mapexception_8():
        try:
            x = blah_pass()
        except OSError:
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
