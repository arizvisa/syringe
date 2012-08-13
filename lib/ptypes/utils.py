def printable(s):
    """Return a string of only printable characters"""
    r = ''
    for c in s:
        if ord(c) >= 32 and ord(c) < 127:
            r += c
        else:
            r += '.'

    return r

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
            for i,x in zip(xrange(length), iterable):
                res += x
    
        except StopIteration:
            pass
        return res

    getRow = lambda o: hexrow(data, offset=o, **kwds)
    
    res = []
    (ofs, data) = offset, tryRead(value, length)
    for i in infiniterange(1, rows):
        res.append( getRow(ofs) )
        ofs, data = (ofs + length, tryRead(value, length))
        if len(data) < length:
            break
        continue

    if len(data) > 0:
        res.append( getRow(ofs) )
    return '\n'.join(res)

def infiniterange(start, stop=None, step=1):
    """Returns a generator that will count infinitely from ``start`` to ``stop`` by step ``step``"""
    assert step != 0

    if step > 0:
        test = lambda x: x < stop
    elif step < 0:
        test = lambda x: x > stop

    if stop is None:
        test = lambda x: True
    res = start
    while test(res):
        yield res
        res += step
    return

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

def forever():
    """A generator that yield's True forever"""
    while True:
        yield True
    return

class assign(object):
    """Will temporarily assign the provided attributes to the specified to all code within it's scope"""
    def __init__(self, *objects, **attrs):
        self.objects = objects
        self.attributes = attrs

    def __enter__(self):
        objects,attrs = self.objects,self.attributes
        self.states = tuple( dict((k,getattr(o,k)) for k,v in attrs.iteritems()) for o in objects)
        [o.update_attributes(attrs) for o in objects]
        return objects

    def __exit__(self, exc_type, exc_value, traceback):
        [o.update_attributes(a) for o,a in zip(self.objects,self.states)]
        return

class padding:
    """Used for providing padding."""
    class source:
        @classmethod
        def repeat(cls,value):
            def generator():
                while True:
                    for x in iter(value):
                        yield x
            return (x for x in generator())

        @classmethod
        def source(cls,iterable):
            return (x for x in iter(iterable))

        @classmethod
        def file(cls,file):
            return (file.read(1) for x in forever())

        @classmethod
        def prng(cls,seed=None):
            import random   # hide this module's dependency in here. ;)
            random.seed(seed)
            return (chr(random.randint(0,0xff)) for x in forever())

        @classmethod
        def zero(cls):
            return cls.repeat('\x00')

    @classmethod
    def fill(cls, amount, source):
        """Returns a string of ``amount`` elements, from the specified ``source``"""
        return ''.join(x for i,x in zip(xrange(amount),source))
