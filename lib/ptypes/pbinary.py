import ptype,utils,bitmap
import types

# FIXME: unfortunately this module doesn't currently support block-based loads
#        due to needing to support endianness as well as dynamic elements.
#        I'll need to fully initialize the container in it's .load() method.

def ispbinarytype(t):
    return t.__class__ is t.__class__.__class__ and not ptype.isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

def ispbinaryinstance(v):
    return isinstance(v, type)

def forcepbinary(p, self):
    ''' as long as value is a function, keep calling it with a context until we get a "ptype" '''
    if bitmap.isinteger(p):
        return bitmap.new(0, p)
    if bitmap.isbitmap(p):
        return p

    if isinstance(p, types.FunctionType):
        return forcepbinary(p(self), self)

    if isinstance(p, types.MethodType):
        return forcepbinary(p(), self)

    assert ispbinaryinstance(p) or ispbinarytype(p), 'resolved class %s cannot be made a member of a pbinary type'% repr(p)
    return p

### endianness
def bigendian(p):
    class bigendianpbinary(p):
        def set(self, integer):
            bmp = bitmap.new(integer, self.bits())
            return self.deserialize_bitmap(bmp)

        def deserialize(self, source):
            source = iter(source)
#            block = self.transform(block)   # whee
            return self.deserialize_stream(source)

        def serialize(self):
            p = bitmap.new(self.getinteger(), self.bits())
            return bitmap.data(p)

        def load(self):
            # XXX: this has been deprecated to using the stream-based loader
            self.source.seek(self.getoffset())
            producer = ( self.source.consume(1) for x in utils.infiniterange(0) )
            return self.deserialize_stream(producer)

    bigendianpbinary.__name__ = p.__name__
    return bigendianpbinary

def littleendian(p):
    class littleendianpbinary(p):
        def set(self, integer):
            raise NotImplementedError
            bmp = bitmap.new(integer, self.bits())
            return self.deserialize_bitmap(bmp)

        # XXX: This won't work if the size is dynamic, for obvious reasons
        def deserialize(self, source):
            source = iter(source)
            block = ''.join([x for i,x in zip(range(self.alloc().size()), source)])
            block = self.transform(block)   # whee
            return self.deserialize_stream(reversed(block))

        def load(self):
            self.source.seek(self.getoffset())
            block = self.source.consume( self.alloc().size() )
            return self.deserialize_stream(iter(block))

        def serialize(self):
            p = bitmap.new(self.getinteger(), self.bits())
            return bitmap.data(p, flipendian=True)
            
    littleendianpbinary.__name__ = p.__name__
    return littleendianpbinary

class type(ptype.pcontainer):
    def isInitialized(self):
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value if ispbinaryinstance(x)])
    initialized = property(fget=isInitialized)  # bool

    # for the "decorators"
    def serialize(self):
        raise NotImplementedError(self.name())
    def set(self, source):
        raise NotImplementedError(self.name())

    def deserialize_stream(self, source):
        bc = bitmap.consumer(source)
        bc.consume(self.getbitoffset())     # skip some number of bits
        return self.deserialize_consumer(bc)

    # por los hijos
    def deserialize_consumer(self, source):
        raise NotImplementedError(self.name())

    def getinteger(self):
        result = bitmap.new(0,0)
        for n in self.value:
            if ispbinaryinstance(n):
                result = bitmap.push( result, (n.getinteger(), n.bits()))
                continue

            if bitmap.isbitmap(n):
                result = bitmap.push(result, n)
                continue

            raise ValueError('Unknown type %s stored in %s'% (repr(n), repr(self)))
            continue
        return result[0]

    def bits(self):
        result = 0
        for x in self.value:
            if bitmap.isbitmap(x):
                result += x[1]
                continue
            if ispbinaryinstance(x):
                result += x.bits()
                continue
            raise ValueError('Unknown type %s stored in %s'% (repr(x), repr(self)))
        return result

    def newelement(self, pbinarytype, name, offset):
        '''Given a valid type that we can contain, instantiate a new element'''
        n = forcepbinary(pbinarytype, self)
        if ispbinarytype(n):
            n = n()
            n.parent = self
            n.source = self.source
            n.__name__ = name
            if bitmap.isbitmap(offset):
                n.setbitoffset(offset[1])
                n.setoffset(offset[0])
                return n
            n.setbitoffset(0)
            n.setoffset(offset)
            return n

        if ispbinaryinstance(n):
            n.parent = self
            return n

        elif bitmap.isbitmap(n):
            return bitmap.new(0, n[1])
            
        raise ValueError('Unknown type %s returned'% n.__class__)

    def deserialize_bitmap(self, source):
        '''Initialize container using the bitmap provided by source'''
        assert bitmap.isbitmap(source)
        for i in range(len(self.value)):
            n = self.value[i]
            if ispbinaryinstance(n):
                source,value = bitmap.consume(source, n.bits())
                n.set(value)
                continue

            value,source = self.value[i]
            source,value = bitmap.consume(source,n.bits())
            self.value[i] = value,source
        return self

    __boffset = 0
    def setbitoffset(self, value):
        self.__boffset = value % 7
    def getbitoffset(self):
        return int(self.__boffset)

    def size(self):
        return (self.bits()+7)/8

    def commit(self):
        raise NotImplementedError("I'm pretty certain I just broke this")
        # FIXME: this hasn't been formally tested
        newdata = bitmap.new(self.getinteger(), self.bits())
        bo = self.getbitoffset()

        # read original data that we're gonna update
        self.source.seek( self.getoffset() )
        olddata = self.source.consume( self.size() )
        bc = bitmap.consumer(iter(olddata))

        # calculate offsets
        leftbits,middlebits = bo, self.bits() - bo, 
        rightbits = (self.size()*8 - middlebits)

        left,middle,right = bc.consume(leftbits),bc.consume(middlebits),bc.consume(rightbits)

        # handle each chunk
        result = bitmap.new(0, 0)
        result = bitmap.push(result, (left, leftbits))
        result = bitmap.push(result, newdata)
        result = bitmap.push(result, (right, rightbits))
        
        # convert to serialized data
        res = []
        while result[1] > 0:
            result,v = bitmap.consume(result,8)
            res.append(v)
        
        data = ''.join(map(chr,reversed(res)))

        # write it finally
        self.source.seek(self.getoffset())
        self.source.write(data)

        return self

    def copy(self):
        result = self.newelement( self.__class__, self.__name__, (self.getoffset(), self.getbitoffset()) )
        result.deserialize( self.serialize() )
        return result

    def addbitsfromsource(self, source, type, name, offset):
        '''
        Adds an element to the current container reading /type/ from source.
        /name/ and /offsets/ are attributes that will be set. returns bitsize
        '''
        n = self.newelement(type, name, (offset>>3, offset & 7)) # XXX: offset needs to be fixed
        if bitmap.isbitmap(n):
            n = (source.consume(n[1]), n[1])
            res = n[1]
        else:
            n.deserialize_consumer(source)
            res = n.bits()
        self.value.append(n)
        return res

    def alloc(self):
        zero = ( 0 for x in utils.infiniterange(0) )
        class allocator(object):
            def consume(self, v):
                return zero.next()
        return self.deserialize_consumer( allocator() )

class __struct_generic(type):
    __fastindex = dict  # our on-demand index lookup for .value

    def __iter__(self):
        return iter(self.keys())

    def getindex(self, name):
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
            if bitmap.isbitmap(x):
                result.append( x[0] )
                continue
            result.append( x )
        return result

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def __getitem__(self, name):
        index = self.getindex(name)
        value = self.value[index]
        if ispbinaryinstance(value):
            return value
        integer,bits = value
        return integer & ((1<<bits)-1)

    def __setitem__(self, name, value):
#        raise NotImplementedError('Implemented, but untested...')
        index = self.getindex(name)
        if ispbinaryinstance(value):
            self.value[index] = value
            return
        integer,bits = self.value[index]
        self.value[index] = (value, bits)

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if not self.initialized:
            return ' '.join([ofs, repr(self.__class__), self.__repr__uninitialized()])
        return ' '.join([ofs, repr(self.__class__), self.__repr__initialized()])

    def __repr__value(self, element):
        if bitmap.isbitmap(element):
            return hex(element[0])
        return ''.join(['struct[', hex(element.getinteger()), ']'])

    def __repr__initialized(self):
        res = [ '%s=%s'% (name, self.__repr__value(val)) for name,val in zip(self.keys(), self.value) ]
        return ' '.join(res)

    def __repr__uninitialized(self):
        res = [ '%s=?'% (name) for name in self.keys() ]
        return ' '.join(res)

class struct(__struct_generic):
    def deserialize_consumer(self, source):
        self.value = []
        offset = (self.getoffset() << 3) + self.getbitoffset()
        for t,name in self._fields_:
            s = self.addbitsfromsource(source, t, name, offset)
            offset += s
        return self

class __array_generic(type):
    length = 0
    def __len__(self):
        if not self.initialized:
            return int(self.length)
        return len(self.value)

    def __iter__(self):
        for x in self.value:
            if bitmap.isbitmap(x):
                yield x[0]
                continue
            yield x
        return

    def __getitem__(self, index):
        n = self.value[index]
        if bitmap.isbitmap(n):
            return n[0]
        return n

    def __setitem__(self, index, value):
        raise NotImplementedError('Implemented, but untested...')
        if ispbinaryinstance(value):
            self.value[index] = value
            return

        v = self.value[index]
        if bitmap.isbitmap(v):
            integer,bits = v
            self.value[index] = (value & ((2**bits)-1), bits)
            return

        raise ValueError('Unknown type %s while trying to assign to index %d'% (value.__class_, index))

    def __repr__(self):
        if not self.initialized:
            return repr(self.__class__) + ' ' + self.__repr__uninitialized()
        return repr(self.__class__) + ' ' + self.__repr__initialized()

    def __repr__uninitialized(self):
        obj = self._object_
        if bitmap.isbitmap(obj):
            name = bitmap.repr(obj)
        else:
            name = obj.__class__
        return '%s[%d] length=?'% (name, len(self))

    def __repr__initialized(self):
        obj = self._object_
        if bitmap.isbitmap(obj):
            name = bitmap.repr(obj)
        else:
            name = obj.__class__
        return '%s[%d] value=%x,bits=%x'% (name, len(self), self.getinteger(), self.bits())

class array(__array_generic):
    _object_ = None

    def deserialize_consumer(self, source):
        self.value = []
        offset = (self.getoffset() << 3) + self.getbitoffset()
        for i in xrange(self.length):
            s = self.addbitsfromsource(source, self._object_, str(i), offset)
            offset += s
        return self

class terminatedarray(__array_generic):
    length = None
    def deserialize_consumer(self, source):
        forever = self.length
        if forever is None:
            forever = utils.infiniterange(0)
        else:
            forever = xrange(forever)

        self.value = []
        offset = (self.getoffset() << 3) + self.getbitoffset()

        try:
            for i in forever:
                s = self.addbitsfromsource(source, self._object_, str(i), offset)
                if self.isTerminator(self.value[-1]):
                    break
                offset += s

        except StopIteration:
            pass
        return self

    def isTerminator(self, v):
        '''intended to be overloaded. should return True if value /v/ represents the end of the array.'''
        raise NotImplementedError

array = bigendian(array)
terminatedarray = bigendian(terminatedarray)
struct = bigendian(struct)

if __name__ == '__main__':
    import sys
    sys.path.append('f:/work')

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

    import pbinary

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

    @TestCase
    def test1():
#        print "test1"
#        print "size = 4, value1 = 'a', value2 = 'b', value3 = 'c'"

        x = RECT()
        x.deserialize('\x4a\xbc\xde\xf0')
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

        a = blah()
#        print repr(s)
#        print repr(x)
        a.deserialize(s)

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
        res = blah()

        # xxx: this needs to be moved into bitcontainer
        res.deserialize(data)

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
        res = pbinary.littleendian(blah)().alloc()

        data = [x for n,x in zip(range(res.size()), data)]
        res.deserialize(data)

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

#        print repr(data)
#        print repr(res)
#        print repr(res['type'])
#        print repr(res['size'])

    @TestCase
    def test5():
#        print "test5 - bigendian"
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

        blah = pbinary.bigendian(blah)
        data = '\xaa\xbb\xcc\xdd\x11\x11'

        res = blah()
        res.deserialize(data)

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
        blah = pbinary.littleendian(blah)
        data = '\xdd\xcc\xbb\xaa\x11\x11'

        res = blah()
        res.deserialize(data)
#        print res.values()
        if res.values() == [0xa, 0xa, 0xb, 0xb, 0xc, 0xcd, 0xd]:
            raise Success
#        print repr(data), " -> ", repr(res)
#        print repr(res.keys())
#        print repr(res.values())

    @TestCase
    def test7():
#        print "test7"

        x = RECT()
        #print x.size()
#        print x
        x.deserialize('hello world')
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

        x = blah()
        x.deserialize(s)
        if list(x) == [5, 2, 5]:
            raise Success

    def test9():
#        print "test9"
        # print out bit offsets for a pbinary.struct

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]
        class nibble(pbinary.struct): _fields_ = [(4, 'value')]

        class byte(pbinary.array):
            _object_ = halfnibble
            length = 4

        class blah(pbinary.struct):
            _fields_ = [
                (nibble, 'first-nibble'),
                (nibble, 'second-nibble'),
                (tribble, '3bits')
            ]

        class largearray(pbinary.array):
            _object_ = blah
            length = 16

        res = reduce(lambda x,y: x<<1 | [0,1][int(y)], ('11001100'), 0)
        print hex(res)

        x = largearray()
        x.deserialize(chr(res)*63)
        print x
        print x[1]
        print x[1].getoffset(), x[1].getbitoffset()

    def test10():
        print "test10"
        # test out bit offset loads for an array

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]

        class blah(pbinary.array):
            _object_ = tribble
            length = 16

        from ptypes import provider
        
        x = blah()
        x.source = provider.string(TESTDATA)
        x.setbitoffset(3)
        x.load()
        print repr(x)
        res = [ (x.getoffset(), x.getbitoffset(), repr(x)) for x in x ]
        print '\n'.join(map(repr,res))

        # wow, that really worked...

    def test11():
        print "test11"
        # test out bit offset loads for a pbinary.struct

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]

        class blah(pbinary.array):
            _object_ = tribble
            length = 16

        from ptypes import provider
        x = blah()
        x.source = provider.file('blah.data', 'rb')
        x.setbitoffset(3)
        x.load()
        print repr(x)
        res = [ (x.getoffset(), x.getbitoffset(), repr(x)) for x in x ]
        print '\n'.join(map(repr,res))

        # holy shit, that one worked too

    def testold():
        print 'old shitty tests'
        class blah1(pbinary.struct):
            bigendian = False
            _fields_ = [
                (6, 'padding'), #000000
                (8, 'byte'),    #11111111
                (4, 'nibble1'), #1101
                (4, 'nibble2'), #1011
                (2, 'half')     #00
            ]
        class blah2(pbinary.struct):
            bigendian = True
            _fields_ = [
                (8, 'byte'),    #11111111
                (4, 'nibble1'), #1101
                (4, 'nibble2'), #1011
                (2, 'half'),     #00
                (6, 'padding') #000000
            ]

    #    num = '1111 1111 1101 1011 00'
    #    s = utils.bin2int(num)
    #    s = utils.i2h(s, count=3)
        s = '\xff\xdb\x00'

        n = blah1()
        n.deserialize(s)
        print n
        print n.value

        ## another binary test
    #    num = ''.join( reversed(num) )
    #    num = 0011 0110 1111 1111 1100
    #    s = utils.bin2int(num)
    #    s = utils.i2h(s, count=3)
        s = '\x36\xff\xc0'

        n = blah2()
        n.deserialize(s)
        print n
        print n.value

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
    def test12():
#        print "test12"
        ## a struct containing ints
        self = dword()
        #self.deserialize_bitmap( bitmap.new(0xdeaddeaf, 32) )
        self.deserialize('\xde\xad\xde\xaf')
#        print repr(self.serialize())
#        print self
        if self['high'] == 0xdead and self['low'] == 0xdeaf:
            raise Success

    @TestCase
    def test13():
#        print "test13"
        ## a struct containing ptype
        class blah(pbinary.struct):
            _fields_ = [
                (word, 'higher'),
                (word, 'lower'),
            ]
        self = blah()
        self.deserialize('\xde\xad\xde\xaf')
#        print repr(self.serialize())
#        print '[1]', self
#        print '[2]', self['higher']
#        print '[3]', self['higher']['high']
#        for x in self.value:
#            print x.getoffset(), x.getbitoffset()
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower']['high'] == 0xde and self['lower']['low'] == 0xaf:
            raise Success

    @TestCase
    def test14():
#        print "test14"
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = blah()
        self.deserialize('\xde\xad\x80')
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower'] == 0x80:
            raise Success

    @TestCase
    def test15():
#        print "test15"
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        self = blah()

        data = '\xab\xcd\xef\x12'
        self.deserialize(data)
#        print self
#        print '\n'.join(map(repr,self))
        if list(self) == [0xa,0xb,0xc,0xd,0xe,0xf,0x1,0x2]:
            raise Success

    @TestCase
    def test16():
#        print "test16"
        ## an array containing a pbinary
        class blah(pbinary.array):
            _object_ = byte
            length = 4

        self = blah()

        data = '\xab\xcd\xef\x12'
        self.deserialize(data)

#        print self
#        print '\n'.join(map(repr,self))

        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success
        
    @TestCase
    def test17():
#        print "test17"
        class blah(pbinary.array):
            _object_ = lambda s: byte
            length = 4

        self = blah()
        data = '\xab\xcd\xef\x12'
        self.deserialize(data)
#        print self
#        print '\n'.join(map(repr,self))
        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test18():
#        print "test18"
        class blah(pbinary.struct):
            _fields_ = [
                (byte, 'first'),
                (byte, 'second'),
                (byte, 'third'),
                (byte, 'fourth'),
            ]

        self = blah()

        import provider
        self.source = provider.string(TESTDATA)
        self.load()
#        print self.values()
        l = [ v['value'] for v in self.values() ]
#        print l
        if l == [ ord(TESTDATA[i]) for i,x in enumerate(l) ]:
            raise Success

    def test19():
        print "test19"
        class blah(pbinary.array):
            length = 12
            _object_ = nibble

        self = blah()

        import provider
        self.source = provider.string(TESTDATA)
        self.setoffset(0)
        self.setbitoffset(4)
        self.load()
        print repr(self)
        print '\n'.join(map(repr,self))

    def test20():
        print "test20"
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (dword, 'dw'),
                (4, 'hehhh')
            ]

        import provider
        self = blah()
        self.source = provider.string(TESTDATA)
        self.setoffset(0)
        #print self
        self.load()
        print self
        #print '\n'.join(map(repr,self.value))
        #self.alloc()
        #print self.value[0]
        #print self.value[1].getbitoffset()
        #print self.value[2]
        #print self

    @TestCase
    def test21():
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
#        print repr(s)

        i = iter(s)
        z = pbinary.bigendian(RECT)()
        z.deserialize(i)
        
        if z['Nbits'] == 4 and z['Xmin'] == 0xd and z['Xmax'] == 0xe and z['Ymin'] == 0xa and z['Ymax'] == 0xd:
            raise Success

    @TestCase
    def test22():
        class myarray(pbinary.terminatedarray):
            _object_ = 4
    
            def isTerminator(self, v):
                if v[0] == 0:
                    return True
                return False

        z = myarray()
        z.deserialize('\x44\x43\x42\x41\x3f\x0f\xee\xde')
        if z.serialize() == 'DCBA?\x00':
            raise Success

    @TestCase
    def test23():
        class mystruct(pbinary.struct):
            _fields_ = [
                (4, 'high'),
                (4, 'low'),
                (4, 'lower'),
                (4, 'hell'),
            ]

        z = mystruct()
        z.deserialize('\x41\x40')
        if z.getinteger() == 0x4140:
            raise Success

    @TestCase
    def test24():
        class mychild1(pbinary.struct):
            _fields_ = [(4, 'len')]
        class mychild2(pbinary.struct):
            _fields_ = [(4, 'len')]
        
        class myparent(pbinary.struct):
            _fields_ = [(mychild1, 'a'), (mychild2, 'b')]

        from ptypes import provider
        z = myparent()
        z.source = provider.string('A'*5000)
        z.l

        a,b = z['a'],z['b']
        if (a.parent is b.parent) and (a.parent is z):
            raise Success
        raise Failure

    results = []
    for t in TestCaseList:
        results.append( t() )
