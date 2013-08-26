import logging,types
import ptype,utils,bitmap,config
import inspect

# todo:
# sometimes a structure member should be considered signed.
#   when reading from _fields_, we can check to see if a negative
#   was specified, assume that's the number of bits, and it's
#   signed.
#   XXX: i added support for the sign flag, but now how to figure out storing it
#        in order to display properly..
#
# struct.__repr__ could be improved to display the bit offset within
#   a byte and render vertically like pstruct.type instead of outputting
#   it all on one line

def setbyteorder(endianness):
    '''Sets the _global_ byte order for any pbinary.type.
    can be either .bigendian or .littleendian
    '''
    global partial
    assert endianness in (config.byteorder.bigendian,config.byteorder.littleendian), repr(endianness)
    partial.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian

# instance tests
def istype(t):
    return t.__class__ is t.__class__.__class__ and not ptype.isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

def iscontainer(t):
    return istype(t) and issubclass(t, container)

def force(t, self, chain=None):
    ''' as long as value is a function, keep calling it with a context until we get a "ptype" '''
    if chain is None:
        chain = []
    chain.append(t)

    # conversions
    if bitmap.isinteger(t):
        return ptype.clone(type, value=(0,t))
    if bitmap.isbitmap(t):
        return ptype.clone(type, value=t)

    # passthrough
    if istype(t):
        return t

    # functions
    if isinstance(t, types.FunctionType):
        return force(t(self), self, chain)
    if isinstance(t, types.MethodType):
        return force(t(), self, chain)

    if inspect.isgenerator(t):
        return force(t.next(), self, chain)

    raise ValueError('pbinary.force : chain=%s : refusing request to resolve %s to a type that does not inherit from pbinary.type : %s'% (repr(chain), repr(t), ','.join(self.backtrace())))

class type(ptype.base):
    '''represents an atomic component of a pbinary structure'''
    value = None
    position = 0,0
    #__name__ = '[unnamed-binary]'
    def setoffset(self, value):
        _,b = self.getposition()
        return self.setposition((value,b))
    def getoffset(self):
        o,_ = self.getposition()
        return o
    offset = property(fget=getoffset,fset=setoffset)

    @property
    def boffset(self):
        _,b = self.getposition()
        return b
    @boffset.setter
    def boffset(self, value):
        o,_ = self.getposition()
        self.setposition((o,value))

    initializedQ = lambda s: s.value is not None

    def number(self):
        return bitmap.number(self.value)
    def bits(self):
        return bitmap.size(self.value)
    def blockbits(self):
        return self.bits()
    def set(self, value):
        _,s = self.value
        self.value = value,s
    def bitmap(self):
        return tuple(self.value)
    def update(self, bitmap):
        v,s = bitmap
        self.value = v,s
        return self

    def deserialize_consumer(self, consumer):
        bb = self.blockbits()
        self.set( consumer.consume(bb) )
        return self

    def newelement(self, pbinarytype, name, position, **attrs):
        '''Given a valid type that we can contain, instantiate a new element'''
        res = force(pbinarytype, self)

        if 'recurse' in attrs:
            attrs['recurse'].update(self.attributes)
        else:
            attrs['recurse'] = self.attributes

        res = res(**attrs)

        res.parent = self
        res.__name__ = name
        res.setposition(position)

        if 'source' not in attrs:
            res.source = self.source
        return res

    def summary(self):
        if self.initializedQ():
            return '(0x%x, %d)'% self.bitmap()
        return '???'

    def details(self):
        if self.initializedQ():
            return bitmap.hex(self.bitmap())
        return '???'

    def contains(self, offset):
        nmin = self.getoffset()
        nmax = nmin+self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    # default methods
    def load(self, **attrs):
        raise NotImplementedError
    def commit(self, **attrs):
        raise NotImplementedError
    def copy(self):
        raise NotImplementedError

    def size(self):
        return (self.bits()+7)/8
    def blocksize(self):
        return (self.blockbits()+7)/8

    def alloc(self, **attrs):
        '''will initialize a pbinary.type with zeroes'''
        with utils.assign(self, **attrs):
            result = self.deserialize_consumer( bitmap.consumer('\x00' for x in utils.infiniterange(0)))
        return result

    def repr(self):
        """Return a __repr__ of the type"""
        prop = '{%s}'% ','.join('%s=%s'%(k,repr(v)) for k,v in self.properties().iteritems())
        return '[%x] %s %s %s'%( self.getoffset(), self.name(), prop, self.details())

class container(type):
    '''contains a list of variable-bit integers'''
    # instead of being a list of bitmap tuples, use an object
    #__name__ = '[unnamed-binary-container]'

    # positioning
    def getposition(self, index=None):
        if index is None:
            return super(container,self).getposition()
        n = self.value[index]
        return n.getposition()

    def setposition(self, (offset,bitoffset), recurse=False):
        a,b = self.getposition()
        offset,boffset = (offset+(bitoffset/8),bitoffset%8)
        super(container,self).setposition((offset,boffset))

        if recurse:
            for n in self.value:
                n.setposition((offset,boffset), recurse=recurse)
                boffset += n.blockbits()
            pass
        return a,b

    # loading
    def deserialize_consumer(self, consumer, generator):
        """initialize container object with bitmap /consumer/ using the type produced by /generator/"""
        assert self.value is not None, 'Parent must initialize self.value'
        value = self.value

        position = self.getposition()
        for n in generator:
            value.append(n)
            n.setposition(position)
            n.deserialize_consumer(consumer)    # can raise StopIteration
            s = n.blockbits()

            a,b = position
            b += s
            a,b = (a + b/8, b % 8)
            position = (a,b)
        return self

    def initializedQ(self):
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value if isinstance(x,type)])

    ### standard stuff
    def number(self):
        return bitmap.number(self.bitmap())
    def bitmap(self):
        return reduce(lambda x,y:bitmap.push(x, y.bitmap()), self.value, bitmap.new(0,0))

    def bits(self):
        return reduce(lambda x,y:x+y.bits(), self.value, 0)
    def blockbits(self):
        return reduce(lambda x,y:x+y.blockbits(), self.value, 0)
    def blocksize(self):
        return (self.blockbits()+7)/8

    def set(self, value):
        v,s = res = self.bitmap()
        agg = value,s
        for x in self.value:
            s = x.bits()
            agg,v = bitmap.shift(agg, s)
            x.set(v)
        return res

    def update(self, bitmap):
        raise NotImplementedError('not allowed to change size of container')
        v,s = bitmap
        self.value = v,s
        return self

    def serialize(self):
        raise NotImplementedError
        x = bitmap.join(x.bitmap() for x in self.value)
        return bitmap.data(x)

    ## misc
    def copy(self):
        raise NotImplementedError
        result = self.newelement( self.__class__, self.__name__, self.getposition() )
        result.deserialize_consumer( bitmap.consumer(self.serialize()) )    # FIXME: this doesn't pay attention to alignment or position
        return result

    def alloc(self, **attrs):
        with utils.assign(self, **attrs):
            result = self.deserialize_consumer( bitmap.consumer('\x00' for x in utils.infiniterange(0)))
        return result

    def load(self, **attrs):
        raise NotImplementedError("Not allowed to load from a binary-type. traverse to a partial, and then call .load")

    def commit(self, **attrs):
        raise NotImplementedError("Not allowed to commit from a binary-type")

### generics
class _array_generic(container):
    length = 0
    def __len__(self):
        if not self.initialized:
            return int(self.length)
        return len(self.value)

    def __iter__(self):
        for x in self.value:
            yield x if isinstance(x,container) else x.number()
        return

    def __getitem__(self, index):
        res = self.value[index]
        return res if isinstance(res,container) else res.number()

    def __setitem__(self, index, value):
#        raise NotImplementedError('Implemented, but untested...')
        if isinstance(value,type):
            self.value[index] = value
            return

        v = self.value[index]
        if not isinstance(v,container):
            v.set(value & ((2**v.bits())-1))
            return

        raise ValueError('Unknown type %s while trying to assign to index %d'% (value.__class_, index))

    def details(self):
        if not self.initialized:
            return self.__details_uninitialized()
        return self.__details_initialized()

    def __details_uninitialized(self):
        obj = self._object_
        if bitmap.isbitmap(obj):
            name = '<%x,%x>'%obj
        else:
            name = obj.__class__
        return '%s[%d] length=?'% (name, len(self))

    def __details_initialized(self):
        obj = self._object_
        if iscontainer(obj):
            name = obj().name()
        else:
            obj = self.newelement(obj,'',(0,0)).bitmap()
            name = '<%x,%x>'%obj
        bits = self.bits()
        value = '0x%s'% bitmap.hex(self.bitmap())
        return '%s[%d] value=%s,bits=%d'% (name, len(self), value, bits)

class _struct_generic(container):
    __fastindex = dict  # our on-demand index lookup for .value

    def __iter__(self):
        return iter(self.keys())

    def getposition(self, name=None):
        if name is None:
            return super(_struct_generic,self).getposition()
        index = self.__getindex(name)
        return super(_struct_generic,self).getposition(index)

    def __getindex(self, name):
        try:
            return self.__fastindex[name]
        except TypeError:
            self.__fastindex = {}
        except KeyError:
            pass

        res = self.keys()
        for i in range( len(res) ):
            if name == res[i]:
                self.__fastindex[name] = i
                return i

        raise KeyError(name)

    def keys(self):
        '''return the name of each field'''
        return [name for type,name in self._fields_]

    def values(self):
        '''return all the integer values of each field'''
        result = []
        for x in self.value:
            if isinstance(x,container):
                result.append(x)
                continue
            result.append(x.number())
        return result

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def __getitem__(self, name):
        index = self.__getindex(name)
        res = self.value[index]
        return res if isinstance(res, container) else res.number()

    def __setitem__(self, name, value):
#        raise NotImplementedError('Implemented, but untested...')
        index = self.__getindex(name)
        if isinstance(value,type):
            self.value[index] = value
            return
        v = self.value[index]
        integer,bits = v.value
        v.value = (value, bits)

    def details(self):
        if not self.initialized:
            return self.__details_uninitialized()
        return self.__details_initialized()

    def __details_initialized(self):
        result = []
        for name,val in zip(self.keys(), self.value):
            v,s = b = val.bitmap()

            if isinstance(val, container):
                v = 'struct[0x%s]'% bitmap.hex(b)
            else:
                v = '0x%s'% bitmap.hex(b)

            result.append( '%s%s=%s'% (name, ('', '{%d}'%s)[s>1], v) )
        return ' '.join(result)

    def __details_uninitialized(self):
        res = [ '%s=?'% (name) for name in self.keys() ]
        return ' '.join(res)

class array(_array_generic):
    length = 0

    def deserialize_consumer(self, consumer):
        position = self.getposition()
        obj = self._object_
        self.value = []
        generator = (self.newelement(obj,str(index),position) for index in xrange(self.length))
        return super(array,self).deserialize_consumer(consumer, generator)

    def blockbits(self):
        if self.initialized:
            return super(array,self).blockbits()

        res = 0
        for i in xrange(self.length):
            t = force(self._object_, self)
            n = self.newelement(t, str(i), 0)   # XXX
            res += n.blockbits()
        return res

class struct(_struct_generic):
    _fields_ = None

    def deserialize_consumer(self, consumer):
        self.value = []
        position = self.getposition()
        generator = (self.newelement(t,name,position) for t,name in self._fields_)
        return super(struct,self).deserialize_consumer(consumer, generator)

    def blockbits(self):
        if self.initialized:
            return super(struct,self).blockbits()

        res = 0
        for v,k in self._fields_:
            t = force(v,self)
            n = self.newelement(t, k, 0)    # XXX
            res += n.blockbits()
        return res

class terminatedarray(_array_generic):
    length = None
    def deserialize_consumer(self, consumer):
        self.value = []
        obj = self._object_
        forever = utils.infiniterange(0) if self.length is None else xrange(self.length)
        position = self.getposition()

        def generator():
            for index in forever:
                n = self.newelement(obj, str(index), position)
                yield n
                if self.isTerminator(n):
                    break
                continue
            return

        p = generator()
        try:
            return super(terminatedarray,self).deserialize_consumer(consumer, p)

        # terminated arrays can also stop when out-of-data
        except StopIteration:
            n = self.value[-1]
            path = ' ->\n\t'.join(self.backtrace())
            logging.info("<pbinary.terminatedarray> Terminated %s<%x:+%x> at %s<%x:+??>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), path))

        return self

    def isTerminator(self, v):
        '''intended to be overloaded. should return True if value /v/ represents the end of the array.'''
        raise NotImplementedError

class blockarray(terminatedarray):
    length = None
    def isTerminator(self, value):
        return False

    def deserialize_consumer(self, consumer):
        obj,position = self._object_,self.getposition()
        total = self.blocksize()*8
        if total != self.blockbits():
            total = self.blockbits()
        value = self.value = []
        forever = utils.infiniterange(0) if self.length is None else xrange(self.length)
        generator = (self.newelement(obj,str(index),position) for index in forever)

        # fork the consumer
        consumer = bitmap.consumer().push( (consumer.consume(total),total) )

        try:
            while total > 0:
                n = generator.next()
                n.setposition(position)
                value.append(n)

                n.deserialize_consumer(consumer)    #
                if self.isTerminator(n):
                    break

                s = n.blockbits()

                total -= s
                a,b = position
                b += s
                a,b = (a + b/8, b % 8)
                position = (a,b)

            if total < 0:
                logging.info('pbinary.blockarray.deserialize_consumer : %s read %d extra bits', self.name(), -total)

        except StopIteration:
            # FIXME: fix this error: total bits, bits left, byte offset: bit offset
            logging.warn('pbinary.blockarray.deserialize_consumer : %s : %s : %s : incomplete read while consuming %d bits', self.shortname(), n.__name__, repr(position), n.blockbits())
        return self

class partial(ptype.container):
    value = None
    _object_ = None
    position = 0,
    byteorder = None

    initializedQ = lambda s:s.value is not None
    def load(self, **attrs):
        result = self.__load_bigendian(**attrs) if self.byteorder is config.byteorder.bigendian else self.__load_littleendian(**attrs)
        result.setposition(result.getposition(), recurse=True)
        return result

    def __load_bigendian(self, **attrs):
        # big-endian. stream-based
        assert self.byteorder is config.byteorder.bigendian, '<partial.load> byteorder %s is invalid'% self.byteorder
        with utils.assign(self, **attrs):
            o = self.getoffset()
            self.source.seek(o)

            self.value = value = self.binaryobject()
            bc = bitmap.consumer( self.source.consume(1) for x in utils.infiniterange(0) )
            value.deserialize_consumer(bc)
        return self

    def __load_littleendian(self, **attrs):
        # little-endian. block-based
        assert self.byteorder is config.byteorder.littleendian, '<partial.load> byteorder %s is invalid'% self.byteorder
        with utils.assign(self, **attrs):
            o,s = self.getoffset(),self.blocksize()
            self.source.seek(o)
            block = ''.join(reversed(self.source.consume(s)))

            self.value = value = self.binaryobject()
            bc = bitmap.consumer(x for x in block)
            value.deserialize_consumer(bc)
        return self

    def alloc(self, **attrs):
        # FIXME
        with utils.assign(self, **attrs):
            self.value = self.binaryobject()
            result = self.value.deserialize_consumer( bitmap.consumer('\x00' for x in utils.infiniterange(0)))
        return self

    def commit(self, **attrs):
        with utils.assign(self, **attrs):
            self.source.seek( self.getoffset() )
            data = self.serialize()
            self.source.store(data)
        return self

    def binaryobject(self, **attrs):
        ofs = self.getoffset()
        obj = force(self._object_, self)
        updateattrs = dict(self.attributes)
        updateattrs.update(attrs)
        updateattrs['source'] = self.source
        updateattrs['offset'] = ofs
        updateattrs['parent'] = self
        return obj(**updateattrs)

    def bits(self):
        return self.size()*8
    def blockbits(self):
        return self.blocksize()*8

    def size(self):
        v = self.value if self.initialized else self.binaryobject()
        s = v.bits()
        res = (s) if (s&7) == 0x0 else ((s+8)&~7)
        return res / 8
    def blocksize(self):
        if self.initialized:
            return self.size()
        return self.a.blocksize()

    def serialize(self):
        if self.byteorder is config.byteorder.bigendian:
            bmp = self.value.bitmap()
            return bitmap.data(bmp)

        assert self.byteorder is config.byteorder.littleendian, 'byteorder %s is invalid'% self.byteorder
        bmp = self.value.bitmap()
        return ''.join(reversed(bitmap.data(bmp)))

    def properties(self):
        result = super(partial,self).properties()
        if self.initialized:
            if self.value.bits() != self.blockbits():
                result['unaligned'] = True
            result['bits'] = self.value.bits()
        result['partial'] = True

        # endianness
        if self.byteorder is config.byteorder.bigendian:
            result['byteorder'] = 'bigendian'
        else:
            assert self.byteorder is config.byteorder.littleendian, 'byteorder %s is invalid'% self.byteorder
            result['byteorder'] = 'littleendian'
        return result

    def repr(self):
        """Return a __repr__ of the type"""
        prop = '{%s}'% ','.join('%s=%s'%(k,repr(v)) for k,v in self.properties().iteritems())
        return '[%x] %s %s %s'%( self.getoffset(), self.name(), prop, self.details())

    def getoffset(self):
        res, = self.getposition()
        return res
    def setoffset(self, value, **_):
        pos = value,
        res, = self.setposition(pos, **_)
        return res
    offset = property(fget=getoffset,fset=setoffset)

    ### passthru
    def __len__(self):
        return len(self.value)
    def __getitem__(self, name):
        return self.value[name]
    def __setitem__(self, name, value):
        self.value[name] = value
    def values(self):
        return self.value.values()
    def number(self):
        return self.value.number()
    def details(self):
        if self.initialized:
            return self.value.details()
        return '???'
    def summary(self):
        if self.value.initialized:
            return self.value.summary()
        return '???'
    def __getattr__(self, name):
        return getattr(self.value, name)

    def bitmap(self):
        return self.value.bitmap()

    def shortname(self):
        return 'pbinary.partial(%s)'% self.value.shortname()

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin+self.blocksize()
        return (offset >= nmin) and (offset < nmax)

def new(type, **attrs):
    '''Create a new instance of /type/ applying the attributes specified by /attrs/'''
    if istype(type):
        logging.debug("pbinary.new : Instantiating type %s as type partial", repr(type))
        t = ptype.clone(partial, _object_=type)
        return t(**attrs)
    return type(**attrs)

## force type /p/ to a particular endianness
def bigendian(p):
    if not issubclass(p, partial):
        logging.debug("pbinary.bigendian : Promoting type %s to type partial", repr(p))
        p = ptype.clone(partial, _object_=p, byteorder=config.byteorder.bigendian)
    p.__name__ = 'bigendian(%s)'% p._object_.__name__
    return p

def littleendian(p):
    if not issubclass(p, partial):
        logging.debug("pbinary.littleendian : Promoting type %s to type partial", repr(p))
        p = ptype.clone(partial, _object_=p, byteorder=config.byteorder.littleendian)
    p.__name__ = 'littleendian(%s)'% p._object_.__name__
    return p

def align(bits):
    '''Returns a type that will align fields to the specified bit size'''
    def align(self):
        b = self.bits()
        r = b % bits
        if r == 0:
            return 0
        return bits - r
    return align

if __name__ == '__main__':
    import provider
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

##########################
if __name__ == '__main__' and False:
    import ptypes,pbinary
    @TestCase
    def array():
        class argh(pbinary.array):
            _object_ = 8
            length = 8

        x = argh(source=ptypes.prov.string('ABCDEFGH'))
        x=x.l
        print [x.v for x in x.v]

    @TestCase
    def nibble():
        class argh(pbinary.array):
            _object_ = 4
            length = 8

        x = argh(source=ptypes.prov.string('ABCDEFGH'))
        x=x.l
        print [x.v for x in x.v]

    @TestCase
    def struct484():
        class argh(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (8, 'b'),
                (4, 'c'),
            ]
        x = argh(source=ptypes.prov.string('\xac\x0f'))
        x=x.l
        print x

    class a(pbinary.type):
        value = (0,2)

    class argh(pbinary.array):
        _object_ = a
        length=4

    class argh2(pbinary.struct):
        _fields_ = [
            (4, 'a'),
            (argh, 'b'),
            (4, 'c'),
        ]

    x = argh2(source=ptypes.prov.string('\xac\x0f'))
    x=x.l

setbyteorder(config.integer.byteorder)

if __name__ == '__main__':
    import ptypes,pbinary

    TESTDATA = 'ABCDIEAHFLSDFDLKADSJFLASKDJFALKDSFJ'

    def fn(self):
        return self['size']

    class RECT(pbinary.struct):
        _fields_ = [
            (4, 'size'),
            (fn, 'value1'),
            (fn, 'value2'),
            (fn, 'value3'),
        ]

    class nibble(pbinary.struct):
        _fields_ = [
            (4, 'value')
        ]

    class byte(pbinary.struct):
        _fields_ = [
            (8, 'value')
        ]

    class word(pbinary.struct):
        _fields_ = [
            (8, 'high'),
            (8, 'low'),
        ]

    class dword(pbinary.struct):
        _fields_ = [
            (16, 'high'),
            (16, 'low')
        ]

    @TestCase
    def test1():
#        print "test1"
#        print "size = 4, value1 = 'a', value2 = 'b', value3 = 'c'"

        pbinary.setbyteorder(config.byteorder.bigendian)
#        x = RECT(source=provider.string('\x4a\xbc\xde\xf0')).l
        x = pbinary.new(RECT,source=provider.string('\x4a\xbc\xde\xf0')).l
#        print repr(x)
#        print repr(x.serialize())

        if (x['size'],x['value1'],x['value2'],x['value3']) == (4,0xa,0xb,0xc):
            raise Success
        raise Failure

    @TestCase
    def test2():
#        print "test2"
#        print "header = 4, RECT = {4,a,b,c}, heh=d"
        ### inline bitcontainer pbinary.structures
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'header'),
                (RECT, 'rectangle'),
                (lambda self: self['rectangle']['size'], 'heh')
            ]

        s = '\x44\xab\xcd\xef\x00'

#        a = blah(source=provider.string(s)).l
        a = pbinary.new(blah,source=provider.string(s)).l
#        print repr(s)
#        print repr(x)

        b = a['rectangle']

        if a['header'] == 4 and (b['size'],b['value1'],b['value2'],b['value3']) == (4,0xa,0xb,0xc):
            raise Success

#        print repr(x)
#        print repr(x.serialize())
#        print int(x)
#        print repr(''.join(x.serialize()))

    @TestCase
    def test3():
#        print "test3"
#        print "type=6, size=3f"
        #### test for integer endianness
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 0000 0001 1011 1111
        data = '\x01\xbf'
#        res = blah(source=provider.string(data)).l
        res = pbinary.new(blah,source=provider.string(data)).l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

    @TestCase
    def test4():
#        print "test4"
#        print "type=6, size=3f"
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 1011 1111 0000 0001
        data = '\xbf\x01'
        a = blah
        res = pbinary.littleendian(blah)
        b = res
        res = res()

        data = [x for n,x in zip(range(res.a.size()), data)]
        res.source = provider.string(''.join(data))
        res.l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

        print res.hexdump()
#        print repr(data)
#        print repr(res)
        print repr(res['type'])
        print repr(res['size'])

    @TestCase
    def test5():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (4, 'blah1'),
                (4, 'blah2'),
                (4, 'blah3'),
                (4, 'blah4'),
                (8, 'blah5'),
                (4, 'blah6')
            ]

        data = '\xaa\xbb\xcc\xdd\x11\x11'

        res = pbinary.new(blah,source=provider.string(data)).l

        if res.values() == [0xa,0xa,0xb,0xb,0xc,0xcd, 0xd]:
            raise Success
#        print repr(data), " -> ", repr(res)
#        print repr(res.keys())
#        print repr(res.values())

    @TestCase
    def test6():
#        print "test6 - littleendian"
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (4, 'blah1'),
                (4, 'blah2'),
                (4, 'blah3'),
                (4, 'blah4'),
                (8, 'blah5'),
                (4, 'blah6')
            ]
        data = '\xdd\xcc\xbb\xaa\x11\x11'
        res = blah
        res = pbinary.littleendian(res)
        res = res(source=provider.string(data))
        res = res.l
#        print res.values()
        if res.values() == [0xa, 0xa, 0xb, 0xb, 0xc, 0xcd, 0xd]:
            raise Success
#        print repr(data), " -> ", repr(res)
#        print repr(res.keys())
#        print repr(res.values())

    @TestCase
    def test7():
#        print "test7"

        x = pbinary.new(RECT,source=provider.string('hello world')).l
        #print x.size()
#        print x
#        print x.size()
#        print repr(x)
#        print repr(x['value1'])

#        print x.size()
        if x['size'] == 6 and x.size() == (4 + 6*3 + 7)/8:
            raise Success
        return

    @TestCase
    def test8():
        class blah(pbinary.array):
            _object_ = bitmap.new(0, 3)
            length = 3

        s = '\xaa\xbb\xcc'

        x = pbinary.new(blah,source=provider.string(s)).l
        if list(x) == [5, 2, 5]:
            raise Success

    @TestCase
    def test9():
#        print "test9"
        # print out bit offsets for a pbinary.struct

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]
        class nibble(pbinary.struct): _fields_ = [(4, 'value')]

        class byte(pbinary.array):
            _object_ = halfnibble
            length = 4

        class largearray(pbinary.array):
            _object_ = byte
            length = 16

        res = reduce(lambda x,y: x<<1 | [0,1][int(y)], ('11001100'), 0)

        x = pbinary.new(largearray,source=provider.string(chr(res)*63)).l
        if x[5].number() == res:
            raise Success

    @TestCase
    def test10():
#        print "test12"
        ## a struct containing ints
        self = pbinary.new(dword,source=provider.string('\xde\xad\xde\xaf')).l
        #self.deserialize_bitmap( bitmap.new(0xdeaddeaf, 32) )
#        print repr(self.serialize())
#        print self
        if self['high'] == 0xdead and self['low'] == 0xdeaf:
            raise Success

    @TestCase
    def test11():
#        print "test13"
        ## a struct containing ptype
        class blah(pbinary.struct):
            _fields_ = [
                (word, 'higher'),
                (word, 'lower'),
            ]
        self = pbinary.new(blah,source=provider.string('\xde\xad\xde\xaf')).l
#        self.deserialize('\xde\xad\xde\xaf')
#        print repr(self.serialize())
#        print '[1]', self
#        print '[2]', self['higher']
#        print '[3]', self['higher']['high']
#        for x in self.value:
#            print x.getposition()
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower']['high'] == 0xde and self['lower']['low'] == 0xaf:
            raise Success

    @TestCase
    def test12():
#        print "test14"
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = pbinary.new(blah,source=provider.string('\xde\xad\x80')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower'] == 0x80:
            raise Success

    @TestCase
    def test13():
#        print "test15"
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l

#        print self
#        print '\n'.join(map(repr,self))
        if list(self) == [0xa,0xb,0xc,0xd,0xe,0xf,0x1,0x2]:
            raise Success

    @TestCase
    def test14():
#        print "test16"
        ## an array containing a pbinary
        class blah(pbinary.array):
            _object_ = byte
            length = 4

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l

#        print self
#        print '\n'.join(map(repr,self))

        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test15():
#        print "test17"
        class blah(pbinary.array):
            _object_ = lambda s: byte
            length = 4

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l
#        print self
#        print '\n'.join(map(repr,self))
        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test16():
#        print "test18"
        class blah(pbinary.struct):
            _fields_ = [
                (byte, 'first'),
                (byte, 'second'),
                (byte, 'third'),
                (byte, 'fourth'),
            ]

        self = pbinary.new(blah)

        import provider
        self.source = provider.string(TESTDATA)
        self.load()
#        print self.values()
        l = [ v['value'] for v in self.values() ]
#        print l
        if l == [ ord(TESTDATA[i]) for i,x in enumerate(l) ]:
            raise Success

    @TestCase
    def test17():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (dword, 'dw'),
                (4, 'hehhh')
            ]

        import provider
        self = pbinary.new(blah)
        self.source = provider.string(TESTDATA)
        self.setoffset(0)
        self.load()
        if self['heh'] == 4 and self['dw']['high'] == 0x1424 and self['dw']['low'] == 0x3444 and self['hehhh'] == 9:
            raise Success

    @TestCase
    def test18():
        class RECT(pbinary.struct):
            _fields_ = [
                (5, 'Nbits'),
                (lambda self: self['Nbits'], 'Xmin'),
                (lambda self: self['Nbits'], 'Xmax'),
                (lambda self: self['Nbits'], 'Ymin'),
                (lambda self: self['Nbits'], 'Ymax')
            ]

#        print bitmap.string(a), bitmap.consume(a, 5)
        n = int('1110001110001110', 2)
        b = bitmap.new(n,16)

        a = bitmap.new(0,0)
        a = bitmap.push(a, (4, 5))
        a = bitmap.push(a, (0xd, 4))
        a = bitmap.push(a, (0xe, 4))
        a = bitmap.push(a, (0xa, 4))
        a = bitmap.push(a, (0xd, 4))

        s = bitmap.data(a)

        i = iter(s)
        z = pbinary.new(RECT,source=provider.string(s)).l

        if z['Nbits'] == 4 and z['Xmin'] == 0xd and z['Xmax'] == 0xe and z['Ymin'] == 0xa and z['Ymax'] == 0xd:
            raise Success

    @TestCase
    def test19():
        class myarray(pbinary.terminatedarray):
            _object_ = 4

            def isTerminator(self, v):
                if v.number() == 0:
                    return True
                return False

        z = pbinary.new(myarray,source=provider.string('\x44\x43\x42\x41\x3f\x0f\xee\xde')).l
        if z.serialize() == 'DCBA?\x00':
            raise Success

    @TestCase
    def test20():
        class mystruct(pbinary.struct):
            _fields_ = [
                (4, 'high'),
                (4, 'low'),
                (4, 'lower'),
                (4, 'hell'),
            ]

        z = pbinary.new(mystruct,source=provider.string('\x41\x40')).l
        if z.number() == 0x4140:
            raise Success

    @TestCase
    def test21():
        class mychild1(pbinary.struct):
            _fields_ = [(4, 'len')]
        class mychild2(pbinary.struct):
            _fields_ = [(4, 'len')]

        class myparent(pbinary.struct):
            _fields_ = [(mychild1, 'a'), (mychild2, 'b')]

        from ptypes import provider
        z = pbinary.new(myparent)
        z.source = provider.string('A'*5000)
        z.l

        a,b = z['a'],z['b']
        if (a.parent is b.parent) and (a.parent is z.v):
            raise Success
        raise Failure

    @TestCase
    def test22():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.uint32_t, 'v')]

        z = broken(source=provider.string(correct))
        z = z.l
        a = z['h']

        if a['t'] == 69 and a['l'] == 4:
            raise Success
        raise Failure

    @TestCase
    def test23():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.littleendian(pint.uint32_t), 'v')]

        z = broken().alloc()
        z['v'].set(8)

        z['h']['l'] = 4
        z['h']['t'] = 0x45

        if z.serialize() == correct:
            raise Success
        raise Failure

    @TestCase
    def test24():
        correct = '\x0f\x00'
        class header(pbinary.struct):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        z = pbinary.littleendian(header)(source=provider.string(correct)).l

        if z.serialize() != correct:
            raise Failure
        if z['version'] == 15 and z['instance'] == 0:
            raise Success
        raise Failure

    @TestCase
    def test25():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (pbinary.align(8), 'b'),
                (4, 'c')
            ]

        x = pbinary.new(blah,source=provider.string('\xde\xad')).l
        if x['a'] == 13 and x['b'] == 14 and x['c'] == 10:
            raise Success
        raise Failure

    import struct
    class blah(pbinary.struct):
        _fields_ = [
            (-16, 'a'),
        ]

    @TestCase
    def test26():
        s = '\xff\xff'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success
        print repr(s),a['a'],b

    @TestCase
    def test27():
        s = '\x80\x00'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success
        print repr(s),a['a']

    @TestCase
    def test28():
        s = '\x7f\xff'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success
        print repr(s),a['a']

    @TestCase
    def test29():
        s = '\x00\x00'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success
        print repr(s),a['a']

    @TestCase
    def test30():
        class blah2(pbinary.struct):
            _fields_ = [
                (4, 'a0'),
                (1, 'a1'),
                (1, 'a2'),
                (1, 'a3'),
                (1, 'a4'),
                (8, 'b'),
                (8, 'c'),
                (8, 'd'),
            ]

        s = '\x00\x00\x00\x04'
        a = pbinary.littleendian(blah2)(source=provider.string(s)).l
        if a['a2'] == 1:
            raise Success

    @TestCase
    def test31():
        s = '\x04\x00'
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.string(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test32():
        s = '\x00\x04'
        pbinary.setbyteorder(config.byteorder.littleendian)
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.string(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test33():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        src = provider.string('\xaa'*2)
        x = pbinary.new(test,source=src).l
        if tuple(x) == (1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0):
            raise Success

    @TestCase
    def test34():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        a = '\xaa'*2
        b = pbinary.new(test).a

        for i,x in enumerate((1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0)):
            b[i] = x

        if b.serialize() == a:
            raise Success

    @TestCase
    def test35():
        class test(pbinary.struct):
            _fields_ = [(8,'i'),(8,'v')]

        test = pbinary.bigendian(test)
        a = '\x00\x0f'
        b = test(source=provider.string(a)).l
        if b.serialize() == a:
            raise Success

    @TestCase
    def test36():
        pbinary.setbyteorder(config.byteorder.bigendian)

        # terminated-array
        class part(pbinary.struct):
            _fields_ = [(4,'a'),(4,'b')]

        class encompassing(pbinary.terminatedarray):
            _object_ = part
            def isTerminator(self, value):
                return value['a'] == value['b'] and value['a'] == 0xf

        class complete(pbinary.terminatedarray):
            _object_ = encompassing
            def isTerminator(self, value):
                v = value[0]
                return v['a'] == v['b'] and v['a'] == 0x0

        string = 'ABCD\xffEFGH\xffIJKL\xffMNOP\xffQRST\xffUVWX\xffYZ..\xff\x00!!!!!!!!\xffuhhh'
        a = pbinary.new(complete,source=ptypes.prov.string(string))
        a = a.l
        if len(a) == 8 and a.v[-1][0].bitmap() == (0,8):
            raise Success

    @TestCase
    def test37():
        pbinary.setbyteorder(config.byteorder.bigendian)

        string = "ABCDEFGHIJKL"
        src = provider.string(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.v) == 8 and a[-1].bitmap() == (0xb4c,12):
            raise Success

    @TestCase
    def test38():
        pbinary.setbyteorder(config.byteorder.littleendian)

        string = "ABCDEFGHIJKL"
        src = provider.string(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.v) == 8 and a.v[-1].bitmap() == (0x241,12):
            raise Success

    @TestCase
    def test39():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class st(pbinary.struct):
            _fields_ = [
                (word, 'mz'),
                (word, 'l'),
                (dword, 'ptr'),
            ]

        class argh(pbinary.blockarray):
            _object_ = st
            def blockbits(self):
                return 32*8

        data = ''.join(map(chr, (x for x in range(48,48+75))))
        src = provider.string(data)
        a = pbinary.new(argh, source=src)
        a = a.l
        if len(a) == 32/8 and a.size() == 32 and a.serialize() == data[:a.size()]:
            raise Success

    @TestCase
    def test40():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.blockarray):
            _object_ = 32

            def blockbits(self):
                return 32*4

        class ack(pbinary.array):
            _object_ = argh
            length = 4

        data = ''.join((''.join(chr(x)*4 for x in range(48,48+75)) for _ in range(500)))
        src = provider.string(data)
        a = pbinary.new(ack, source=src)
        a = a.l
        if a[0].bits() == 128 and len(a[0]) == 4 and a.blockbits() == 4*32*4 and a[0][-1] == 0x33333333:
            raise Success

if __name__ == '__main__':
#    logging.root=logging.RootLogger(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

#if __name__ == '__main__':
#    result = test39()
#    print result
