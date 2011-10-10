import logging,types
import ptype,utils,bitmap

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
    '''
    Sets the _global_ byte order for any pbinary.type.
    can be either .bigendian or .littleendian
    '''
    for k,v in globals().items():
        if hasattr(v, '__bases__') and issubclass(v, type) and v is not type:
            globals()[k] = endianness(v)
        continue
    return

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
        byteorder=bigendian
        def shortname(self):
#            return 'bigendian(%s)'% self.__class__.__name__
            return self.__class__.__name__

        def serialize(self):
            bs = self.blockbits()
            p = self.getblockbitmap()
            return bitmap.data(p)

        def getblockbitmap(self):
            '''Return the structure as a tuple (integral value, bits) including padding for block boundaries'''
            result = bitmap.new(0,0)
            for n in self.value:
                if ispbinaryinstance(n):
                    result = bitmap.push(result, n.getblockbitmap())
                    continue

                if bitmap.isbitmap(n):
                    result = bitmap.push(result, n)
                    continue

                raise ValueError('Unknown type %s stored in %s'% (repr(n), repr(self)))
            return bitmap.push(result, (0, self.blockbits() - result[1]))

    return bigendianpbinary

def littleendian(p):
    class littleendianpbinary(p):
        byteorder=littleendian
        def shortname(self):
            return 'littleendian(%s)'% self.__class__.__name__

        def deserialize_stream(self, stream):
            string = [x for i,x in zip(xrange(self.alloc().blocksize()),stream)]
            return super(littleendianpbinary, self).deserialize_stream( ''.join(reversed(string)) )

        def serialize(self):
            bs = self.blockbits() / 8
            p = self.getblockbitmap()
            return ''.join(reversed(bitmap.data(p)))

        def getblockbitmap(self):
            '''Return the structure as a tuple (integral value, bits) including padding for block boundaries'''
            result = bitmap.new(0,0)
            for n in self.value:
                if ispbinaryinstance(n):
                    result = bitmap.push(result, n.getblockbitmap())
                    continue

                if bitmap.isbitmap(n):
                    result = bitmap.push(result, n)
                    continue

                raise ValueError('Unknown type %s stored in %s'% (repr(n), repr(self)))
            return bitmap.insert(result, (0, self.blockbits() - result[1]))
            
    return littleendianpbinary

class type(ptype.container):
    def isInitialized(self):
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value if ispbinaryinstance(x)])
    initialized = property(fget=isInitialized)  # bool

    # for the "decorators"
    def serialize(self):
        raise NotImplementedError(self.name())

    # initialization
    def load(self):
        self.source.seek( self.getoffset() )
        # cheat, and fall back to a byte stream since we won't know our full length until
        #   we read some bits
        producer = ( self.source.consume(1) for x in utils.infiniterange(0) )
        return self.deserialize_stream(producer)

    def deserialize_block(self, string):
        return self.deserialize_stream( iter(string) )

    def deserialize_stream(self, stream):
        bc = bitmap.consumer(stream)
        bc.consume(self.getposition()[1])     # skip some number of bits
        return self.deserialize_consumer(bc)

    def alloc(self):
        '''will initialize a pbinary.type with zeroes'''
        # XXX: should we actually allocate space for a remote provider?
        return self.deserialize_stream( ('\x00' for x in utils.infiniterange(0)) )

    if False:
        def set(self, integer):
            raise NotImplementedError("This method is untested")
            bmp = bitmap.new(integer, self.bits())
            return self.deserialize_bitmap(bmp)

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

    def number(self):
        '''Return the binary structure as it's integer value'''
        return self.getbitmap()[0]

    def bits(self):
        '''Return the number of bits occupied by the structure'''
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

    def getbitmap(self):
        '''Return the structure as a tuple (integral value, bits)'''
        result = bitmap.new(0,0)
        for n in self.value:
            if ispbinaryinstance(n):
                result = bitmap.push(result, n.getbitmap())
                continue

            if bitmap.isbitmap(n):
                result = bitmap.push(result, n)
                continue

            raise ValueError('Unknown type %s stored in %s'% (repr(n), repr(self)))
        return result

    def newelement(self, pbinarytype, name, offset):
        '''Given a valid type that we can contain, instantiate a new element'''
        n = forcepbinary(pbinarytype, self)
        if ispbinarytype(n):
            n = n(**self.attrs)
            n.__name__ = name
            n.parent = self
            if 'source' not in self.attrs:
                n.source = self.source

            if bitmap.isbitmap(offset):
                n.setposition(offset[0], offset[1])
                return n

            n.setposition(offset[0], 0)
            return n

        elif bitmap.isbitmap(n):
            return bitmap.new(0, n[1])
            
        raise ValueError('Unknown type %s returned'% n.__class__)

    def newelement_consumer(self, pbinarytype, name, offset, consumer):
        n = self.newelement(pbinarytype, name, offset)
        if bitmap.isbitmap(n):
            return bitmap.new(consumer.consume(n[1]), n[1])
        return n.deserialize_consumer(consumer)

    ## position for dealing with an index into a binary number
    __boffset = 0
    def setposition(self, offset, bitoffset, recurse=False):
        '''Move pbinary.type to specified offset:bitoffset'''
        a,b = self.getoffset(), self.__boffset

        offset,bitoffset = (offset+(bitoffset/8), bitoffset % 8)
        super(type, self).setoffset(offset)
        self.__boffset = bitoffset

        if recurse:
            for n in self.value:
                if bitmap.isbitmap(n):
                    bitoffset += n[1]
                else:
                    n.setposition(offset, bitoffset, recurse=recurse)
                    bitoffset += n.blockbits()
                continue
            pass
        return (a,b)

    def getposition(self):
        return ( super(type, self).getoffset(), self.__boffset )

    def setoffset(self, offset, recurse=False):
        return self.setposition(offset, 0, recurse=recurse)

    def size(self):
        '''Return the loaded size occupied by the structure'''
        return (self.bits()+7)/8

    def set(self, value):
        return self.alloc().deserialize_block(bitmap.data((value, self.bits())))

    def commit(self):
        raise NotImplementedError("this hasn't really been tested")
        newdata = self.getbitmap()
        offset,bitoffset = self.getposition()

        # read original data that we're gonna update
        self.source.seek(offset)
        olddata = self.source.consume( self.size() )
        bc = bitmap.consumer(iter(olddata))

        # calculate offsets
        leftbits,middlebits = bitoffset, self.bits() - bitoffset, 
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
        self.source.seek(offset)
        self.source.store(data)
        return self

    def copy(self):
        result = self.newelement( self.__class__, self.__name__, self.getposition() )
        result.deserialize_block( self.serialize() )
        return result

    def alloc(self):
        zero = ( 0 for x in utils.infiniterange(0) )
        class zeroprovider(object):
            def consume(self, v):
                return zero.next()
        return self.deserialize_consumer( zeroprovider() )

    def blockbits(self):
        '''return the minimum number of bits required to read the pbinary.type'''
        result = 0
        for x in self.value:
            if bitmap.isbitmap(x):
                result += x[1]
                continue
            if ispbinaryinstance(x):
                result += x.blockbits()
                continue
            raise ValueError('Unknown type %s stored in %s'% (repr(x), repr(self)))
        return result

    # FIXME: needs a better name
    def blockbits_element(self, type, source):
        '''
        calculate the total number of bits required to load type.
        returns sign flag,size
        '''
        if bitmap.isbitmap(type):
            n = type[1]
            result = abs(n)
            return n == result, result

        n = type.blockbits()
        result = abs(n)
        source.consume(result - type.bits())
        return n == result, result

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

    def __repr__initialized(self):
        result = []
        for name,val in zip(self.keys(), self.value):
            if bitmap.isbitmap(val):
                v,s = (hex(val[0]), val[1])
            else:
                v,s = ''.join(['struct[', hex(val.number()), ']']),val.bits()

            result.append( '%s%s=%s'% (name, ['', '{%d}'%s][s>1], v) )
        return ' '.join(result)

    def __repr__uninitialized(self):
        res = [ '%s=?'% (name) for name in self.keys() ]
        return ' '.join(res)

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
        return '%s[%d] value=%x,bits=%x'% (name, len(self), self.number(), self.bits())

class struct(__struct_generic):
    def deserialize_consumer(self, source):
        self.value = []

        position = self.getposition()
        for t,name in self._fields_:
            n = self.newelement_consumer(t, name, position, source)
            self.value.append(n)
            sf,s = self.blockbits_element(n, source)

            # fixup the offset
            a,b=position
            b += s
            a,b = (a + b/8, b % 8)
            position = (a,b)
        return self

class array(__array_generic):
    _object_ = None

    def deserialize_consumer(self, source):
        obj = self._object_
        self.value = []

        position = self.getposition()
        for index in xrange(self.length):
            n = self.newelement_consumer(obj, str(index), position, source)
            self.value.append(n)
            sf,s = self.blockbits_element(n, source)

            # fixup the offset
            a,b=position
            b += s
            a,b = (a + b/8, b % 8)
            position = (a,b)
        return self

class terminatedarray(__array_generic):
    length = None
    def deserialize_consumer(self, source):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        position = self.getposition()

        obj = self._object_
        self.value = []

        try:
            for index in forever:
                n = self.newelement_consumer(obj, str(index), position, source)
                self.value.append(n)
                if self.isTerminator(self.value[-1]):
                    break
                sf,s = self.blockbits_element(n, source)

                # fixup the offset
                a,b=position
                b += s
                a,b = (a + b/8, b % 8)
                position = (a,b)
            pass
        except StopIteration:
            pass
        return self

    def isTerminator(self, v):
        '''intended to be overloaded. should return True if value /v/ represents the end of the array.'''
        raise NotImplementedError

class blockarray(terminatedarray):
    def isTerminator(self, value):
        return False

    def deserialize_consumer(self, source):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        position = self.getposition()

        obj = self._object_
        self.value = []

        current = 0
        for index in forever:
            try:
                n = self.newelement_consumer(obj, str(index), position, source)
                sf,s = self.blockbits_element(n, source)

            except StopIteration:
                if current >= self.blockbits():
                    path = ' ->\n\t'.join(n.backtrace())
                    logging.warn("<pbinary.blockarray> Stopped reading %s<%x:+%x> at %s<%x:+??>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), path))
                break

            if (current + s >= self.blockbits()):
                path = ' ->\n\t'.join(n.backtrace())
                logging.info("<pbinary.blockarray> Terminated %s<%x:+%x> at %s<%x:+??>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), path))
                self.value.append(n)
                break

            self.value.append(n)
            if self.isTerminator(n):
                break

            # fixup the offset
            a,b=position
            b += s
            a,b = (a + b/8, b % 8)
            position = (a,b)

            s = n.blockbits(); assert s > 0
            current += s

        return self

struct = bigendian(struct)
array = bigendian(array)
terminatedarray = bigendian(terminatedarray)

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

        x = RECT(source=provider.string('\x4a\xbc\xde\xf0')).l
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

        a = blah(source=provider.string(s)).l
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
        res = blah(source=provider.string(data)).l

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

        res = blah(source=provider.string(data)).l

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

        res = blah(source=provider.string(data)).l
#        print res.values()
        if res.values() == [0xa, 0xa, 0xb, 0xb, 0xc, 0xcd, 0xd]:
            raise Success
#        print repr(data), " -> ", repr(res)
#        print repr(res.keys())
#        print repr(res.values())

    @TestCase
    def test7():
#        print "test7"

        x = RECT(source=provider.string('hello world')).l
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

        x = blah(source=provider.string(s)).l
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

        x = largearray(provider.string(chr(res)*63)).l
        print x
        print x[1]
        print x[1].getposition()

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
        x.setposition(0, 3)
        x.load()
        print repr(x)
        res = [ (x.getposition(), repr(x)) for x in x ]
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
        x.setposition(0, 3)
        x.load()
        print repr(x)
        res = [ (x.getposition(), repr(x)) for x in x ]
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

        n = blah1(source=provider.string(s)).l
        print n
        print n.value

        ## another binary test
    #    num = ''.join( reversed(num) )
    #    num = 0011 0110 1111 1111 1100
    #    s = utils.bin2int(num)
    #    s = utils.i2h(s, count=3)
        s = '\x36\xff\xc0'

        n = blah2(source=provider.string(s)).l
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
        self = dword(source=provider.string('\xde\xad\xde\xaf')).l
        #self.deserialize_bitmap( bitmap.new(0xdeaddeaf, 32) )
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
        self = blah(source=provider.string('\xde\xad\xde\xaf')).l
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
    def test14():
#        print "test14"
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = blah(source=provider.string('\xde\xad\x80')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower'] == 0x80:
            raise Success

    @TestCase
    def test15():
#        print "test15"
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        data = '\xab\xcd\xef\x12'
        self = blah(source=provider.string(data)).l

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

        data = '\xab\xcd\xef\x12'
        self = blah(source = provider.string(data)).l

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

        data = '\xab\xcd\xef\x12'
        self = blah(source=provider.string(data)).l
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
        self.setposition(0, 4)
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
        #print self.value[1].getposition()
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

        i = iter(s)
        z = pbinary.bigendian(RECT)(source=provider.string(s)).l
        
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

        z = myarray(source=provider.string('\x44\x43\x42\x41\x3f\x0f\xee\xde')).l
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

        z = mystruct(source=provider.string('\x41\x40')).l
        if z.number() == 0x4140:
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

    @TestCase
    def test25():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.littleendian(pbinary.struct)):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(RECORDHEADER, 'h'), (pint.uint32_t, 'v')]

        z = broken(source=provider.string(correct)).l

        if z['h']['t'] == 69 and z['h']['l'] == 4:
            raise Success
        raise Failure

    @TestCase
    def test26():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.littleendian(pbinary.struct)):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(RECORDHEADER, 'h'), (pint.littleendian(pint.uint32_t), 'v')]

        z = broken().alloc()
        z['v'].set(8)

        z['h']['l'] = 4
        z['h']['t'] = 0x45

        if z.serialize() == correct:
            raise Success
        raise Failure

    @TestCase
    def test27():
        correct = '\x0f\x00'
        class header(pbinary.littleendian(pbinary.struct)):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        z = header(source=provider.string(correct)).l

        if z.serialize() != correct:
            raise Failure
        if z['version'] == 15 and z['instance'] == 0:
            raise Success
        raise Failure

    @TestCase
    def test28():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (pbinary.align(8), 'b'),
                (4, 'c')
            ]

        x = blah(source=provider.string('\xde\xad')).l
        if x['a'] == 13 and x['b'] == 14 and x['c'] == 10:
            raise Success
        raise Failure

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
