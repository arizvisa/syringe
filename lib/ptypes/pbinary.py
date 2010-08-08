import ptype,bitmap
import types

# FIXME: this needs to be reorganized
#        I imagine there's a lot of cross method calling that doesn't need to happen

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
            return self.set_bitmap(bmp)

        def deserialize(self, source):
            source = iter(source)
            bc = bitmap.consumer(source)
            bc.consume(self.getbitoffset())     # skip some number of bits
            return self.deserialize_consumer(bc)

    bigendianpbinary.__name__ = p.__name__
    return bigendianpbinary

def littleendian(p):
    class littleendianpbinary(p):
        # XXX: This won't work if the size is dynamic, for obvious reasons
        def set(self, integer):
            raise NotImplementedError
            bmp = bitmap.new(integer, self.bits())
            return self.set_bitmap(bmp)

        def deserialize(self, source):
            source = iter(source)
            block = ''.join([x for i,x in zip(range(self.alloc().size()), source)])
            bc = bitmap.consumer(reversed(block))
            bc.consume(self.getbitoffset())
            return self.deserialize_consumer(bc)

    littleendianpbinary.__name__ = p.__name__
    return littleendianpbinary

class type(ptype.pcontainer):
    initialized = property(fget=lambda s: s.value is not None)

    def deserialize(self, source):
        raise NotImplementedError(self.name())
    def set(self, source):
        raise NotImplementedError(self.name())

    def __int__(self):
        result = bitmap.new(0,0)
        for n in self.value:
            if ispbinaryinstance(n):
                result = bitmap.push( result, (int(n), n.bits()))
                continue

            if bitmap.isbitmap(n):
                result = bitmap.push(result, n)
                continue

            raise ValueError('Unknown type %s stored in %s'% (repr(n), repr(self)))
            continue
        return result[0]

    def serialize(self):
        p = bitmap.new(int(self), self.bits())

        res = []
        while p[1] > 0:
            p,v = bitmap.consume(p,8)
            res.append(v)
        
        return ''.join(map(chr,reversed(res)))

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
            n.__name__ = name
            n.source = self.source
            if bitmap.isbitmap(offset):
                n.setbitoffset(offset[1])
                n.setoffset(offset[0])
                return n
            n.setbitoffset(0)
            n.setoffset(offset)
            n.parent = self

        if ispbinaryinstance(n):
            return n

        elif bitmap.isbitmap(n):
            return bitmap.new(0, n[1])
            
        raise ValueError('Unknown type %s returned'% n.__class__)

    def set_bitmap(self, bits):
        assert bitmap.isbitmap(bits)
        for i in range(len(self.value)):
            n = self.value[i]
            if ispbinaryinstance(n):
                bits,value = bitmap.consume(bits, n.bits())
                n.set(value)
                continue

            value,bits = self.value[i]
            bits,value = bitmap.consume(bits,n.bits())
            self.value[i] = value,bits
        return self

    __boffset = 0
    def setbitoffset(self, value):
        self.__boffset = value % 7
    def getbitoffset(self):
        return int(self.__boffset)

    def size(self):
        return (self.bits()+7)/8

    def deserialize_consumer(self, source):
        raise NotImplementedError(self.name())

    def commit(self):
        # FIXME: this hasn't been formally tested
        newdata = bitmap.new(int(self), self.bits())
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

    def load_block(self):
        self.source.seek(self.getoffset())
        block = self.source.consume( self.size() + (self.getbitoffset()+7)/8 )
        return self.deserialize(block)

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
        return [integer&((1<<bits)-1) for integer,bits in self.value]

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
        raise NotImplementedError('Implemented, but untested...')
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
        return ''.join(['struct[', hex(int(element)), ']'])

    def __repr__initialized(self):
        res = [ '%s=%s'% (name, self.__repr__value(val)) for name,val in zip(self.keys(), self.value) ]
        return ' '.join(res)

    def __repr__uninitialized(self):
        res = [ '%s=?'% (name) for name in self.keys() ]
        return ' '.join(res)

class struct(__struct_generic):
    def alloc(self):
        self.value = []
        offset = self.getbitoffset() + (self.getoffset()<<3)
        for t,name in self._fields_:
            n = self.newelement(t, name, (offset>>3, offset))
            if bitmap.isbitmap(n):
                self.value.append(n)
                continue

            if ispbinaryinstance(n):
                n.alloc()
                offset += n.bits()
                self.value.append(n)
                continue

            raise ValueError('Unknown type %s while trying to assign to %s[%s]'% (n.__class_, self.__class__, name))
        return self

    def load(self):
        self.value = []
        offset = self.getbitoffset() + (self.getoffset()<<3)
        for t,name in self._fields_:
            n = self.newelement(t, name, (offset>>3, offset))
            if bitmap.isbitmap(n):
                offset += n[1]
            else:
                offset += n.load().bits()
            self.value.append(n)
            continue

        return self.load_block()

    def deserialize_consumer(self, source):
        self.value = []
        offset = (self.getoffset() << 3 + self.getbitoffset())
        for t,name in self._fields_:
            n = self.newelement(t, name, (offset>>3, offset & 7)) # XXX: offset needs to be fixed
            if bitmap.isbitmap(n):
                n = (source.consume(n[1]), n[1])
                offset += n[1]
            else:
                n.deserialize_consumer(source)
                offset += n.bits()
            self.value.append(n)
        return self

class __array_generic(type):
    length = 0
    def __len__(self):
        return int(self.length)

    def __iter__(self):
        return iter(self.value)

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
        return '%s[%d] ?'% (self._object_, len(self))

    def __repr__initialized(self):
        return '%s[%d] %x'% (self._object_.__class__, len(self), int(self))

class array(__array_generic):
    _object_ = None

    def alloc(self):
        self.value = []
        offset = self.getbitoffset() + (self.getoffset()<<3)
        for i in xrange(len(self)):
            n = self.newelement(self._object_, str(i), (offset>>3, offset))

            if bitmap.isbitmap(n):
                self.value.append(n)
                continue

            if ispbinaryinstance(n):
                n.alloc()
                offset += n.bits()
                self.value.append(n)
                continue

            raise ValueError('Unknown type %s while trying to assign to %s[%s]'% (n.__class_, self.__class__, name))
            continue
        return self

    def deserialize_consumer(self, source):
        self.value = []
        offset = (self.getoffset() << 3 + self.getbitoffset())
        for i in xrange(len(self)):
            n = self.newelement(self._object_, str(i), (offset>>3, offset & 7))   # XXx
            if bitmap.isbitmap(n):
                n = (source.consume(n[1]), n[1])
                offset += n[1]
            else:
                n.deserialize_consumer(source)
                offset += n.bits()
            self.value.append(n)
        return self
            
    def load(self):
        self.value = []
        offset = self.getbitoffset() + (self.getoffset()<<3)
        for i in xrange(len(self)):
            n = self.newelement(self._object_, str(i), (offset>>3, offset))
            if bitmap.isbitmap(n):
                offset += n[1]
            else:
                offset += n.load().bits()
            self.value.append(n)
            continue

        return self.load_block()

array = bigendian(array)
struct = bigendian(struct)

if __name__ == '__main__':
    import sys
    sys.path.append('f:/work')

    ####################################
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

    def test1():
        print "test1"
        print "size = 4, value1 = 'a', value2 = 'b', value3 = 'c'"

        x = RECT()
        x.deserialize('\x4a\xbc\xde\xf0')
        print repr(x)
        print repr(x.serialize())

    def test2():
        print "test2"
        print "header = 4, RECT = {4,a,b,c}, heh=d"
        ### inline bitcontainer pbinary.structures
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'header'),
                (RECT, 'rectangle'),
                (lambda self: self['rectangle']['size'], 'heh')
            ]

        s = '\x44\xab\xcd\xef\x00'

        x = blah()
        print repr(s)
        print repr(x)
        x.deserialize(s)
        print repr(x)
        print repr(x.serialize())
#        print int(x)
#        print repr(''.join(x.serialize()))

    def test3():
        print "test3"
        print "type=6, size=3f"
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
        print repr(data), "->\t", repr(res)

    def test4():
        print "test4"
        print "type=6, size=3f"
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 1011 1111 0000 0001
        data = '\xbf\x01'
        res = blah().alloc()

        data = [x for n,x in zip(range(res.size()), reversed(data))]
        res.deserialize(data)
        print repr(data)
        print repr(res)
        print repr(res['type'])
        print repr(res['size'])

    def test5():
        print "test5 - bigendian"
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

        blah = bigendian(blah)
        data = '\xaa\xbb\xcc\xdd\x11\x11'

        res = blah()
        res.deserialize(data)
        print repr(data), " -> ", repr(res)
        print repr(res.keys())
        print repr(res.values())

    def test6():
        print "test6 - littleendian"
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
        blah = littleendian(blah)
        data = '\xdd\xcc\xbb\xaa\x11\x11'

        res = blah()
        res.deserialize(data)
        print repr(data), " -> ", repr(res)
        print repr(res.keys())
        print repr(res.values())

    def test7():
        print "test7"

        x = RECT()
        #print x.size()
        print x
        x.deserialize('hello world')
        print x.size()
        print repr(x)
        print repr(x['value1'])

    def test8():
        print "test8"
        # print out bit offsets for an array

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]

        class blah(pbinary.array):
            _object_ = tribble
            length = 16

        res = reduce(lambda x,y: x<<1 | [0,1][int(y)], ('11001100'), 0)
        print hex(res)

        x = blah()
        x.deserialize(chr(res)*63)
        res = [ (x.getoffset(), x.getbitoffset()) for x in x ]
        print '\n'.join(map(repr,res))

    def test9():
        print "test9"
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

    def test12():
        print "test12"
        ## a struct containing ints
        self = dword()
        #self.deserialize_bitmap( bitmap.new(0xdeaddeaf, 32) )
        self.deserialize('\xde\xad\xde\xaf')
        print repr(self.serialize())
        print self

    def test13():
        print "test13"
        ## a struct containing ptype
        class blah(pbinary.struct):
            _fields_ = [
                (word, 'higher'),
                (word, 'lower'),
            ]
        self = blah()
        self.deserialize('\xde\xad\xde\xaf')
        print repr(self.serialize())
        print '[1]', self
        print '[2]', self['higher']
        print '[3]', self['higher']['high']
        for x in self.value:
            print x.getoffset(), x.getbitoffset()

    def test14():
        print "test14"
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = blah()
        self.deserialize('\xde\xad\x80')
        print self

    def test15():
        print "test15"
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        self = blah()

        data = '\xab\xcd\xef\x12'
        self.deserialize(data)
        print self
        print '\n'.join(map(repr,self))

    def test16():
        print "test16"
        ## an array containing a pbinary
        class blah(pbinary.array):
            _object_ = byte
            length = 4

        self = blah()

        data = '\xab\xcd\xef\x12'
        self.deserialize(data)

        print self
        print '\n'.join(map(repr,self))

    def test17():
        print "test17"
        class blah(pbinary.array):
            _object_ = lambda s: byte
            length = 4

        self = blah()
        data = '\xab\xcd\xef\x12'
        self.deserialize(data)
        print self
        print '\n'.join(map(repr,self))

    def test18():
        print "test18"
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
        self.setoffset(0)
        self.load()
        print repr(self)

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

    if True:
        testold()
        test1()
        test2()
        test3()
        test4()
        test5()
        test6()
        test7()
        test8()
        test9()
        test10()
        test12()
        test13()
        test14()
        test15()
        test16()
        test17()
        test18()
        test19()
        test20()

    ## wow, i can't believe this shit works
