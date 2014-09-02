'''base array element'''
import itertools
from . import ptype,utils,error,config
Config = config.defaults
__all__ = 'type,terminated,infinite,block'.split(',')

class _parray_generic(ptype.container):
    '''provides the generic features expected out of an array'''
    def __contains__(self,v):
        return any(x is v for x in self.value)

    def __len__(self):
        if not self.initializedQ():
            return int(self.length)
        return len(self.value)

    # XXX: update offsets (?)
    def insert(self, index, object):
        offset = self.value[index].getoffset()
        object.setoffset(offset, recurse=True)
        object.parent,object.source = self,None
        self.value.insert(index, object)

        for i in range(index, len(self.value)):
            v = self.value[i]
            v.setoffset(offset, recurse=True)
            offset += v.blocksize()
        return

    def append(self, object):
        """Add an element to a parray.type. Return it's index.

        This will make the instance of ``object`` owned by the array.
        """
        offset = self.getoffset()+self.blocksize()
        object.setoffset(offset, recurse=True)
        object.parent,object.source = self,None
        return super(_parray_generic,self).append(object)

    def extend(self, iterable):
        for x in iterable:
            self.value.append(x)
        return

    def pop(self, index=-1):
        raise error.ImplementationError(self, '_parray_generic.pop')

        # Implemented, but untested (offsets might be off)...
        res = self.value[index]
        del(self.value[index])
        return res

    # XXX: update offsets
    def __delitem__(self, index):
        index = self.getindex(index)
        del(self.value[index])

    def __setitem__(self, index, value):
        if not isinstance(value, ptype.type):
            raise error.TypeError(self, '_parray_generic.__setitem__',message='Cannot assign a non-ptype to an element of a container. Use .set instead.')

        index = self.getindex(index)
        offset = self.value[index].getoffset()
        value.setoffset(offset, recurse=True)
        value.parent,value.source = self,None
        self.value[index] = value

    def __getitem__(self, index):
        range(len(self))[index]     # make python raise the correct exception if so..
        return super(_parray_generic, self).__getitem__(index)

    def __getslice__(self, i, j):
        res = self.value[i:j]
        # XXX: perhaps fetch elements from memory too
        return res

    def __delslice__(self, i, j):
        del(self.value[i:j])

    def getindex(self, index):
        return index

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

    def contains(self, offset):
        return super(ptype.container, self).contains(offset)

    # load ourselves lazily
    def load_block(self, **attrs):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.new(self._object_, __name__=str(index), offset=ofs, **attrs)
            self.value.append(n)
            ofs += n.blocksize()
        return self

    # load ourselves incrementally
    def load_container(self, **attrs):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.new(self._object_, __name__=str(index), offset=ofs, **attrs)
            self.value.append(n)
            n.load()
            ofs += n.blocksize()
        return self

    def load(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                obj = self._object_
                self.value = []

                # which kind of load are we
                if ptype.istype(obj) and not ptype.iscontainer(obj):
                    self.load_block()

                elif ptype.iscontainer(obj) or ptype.isresolveable(obj):
                    self.load_container()

                else:
                    # XXX: should never be encountered
                    raise error.ImplementationError(self, 'type.load', 'Unknown load type -> %s'% (repr(obj)))

                return super(type, self).load()

        except error.LoadError, e:
            raise error.LoadError(self, exception=e)

    def summary(self, **options):
        res = super(type,self).summary(**options)
        length = len(self) if self.initializedQ() else (self.length or 0)
        if self._object_ is None:
            obj = 'untyped'
        else:
            obj = self._object_.typename() if ptype.istype(self._object_) else self._object_.__name__
        return '%s[%d] %s'% (obj, length, res)

    def repr(self, **options):
        return self.summary(**options)

    def set(self, value):
        """Update self with the contents of the list ``value``"""
        if self.initializedQ() and self.length == len(value):
            return super(type,self).set(*value)

        result = super(type,self).set(*(self._object_ for _ in xrange(len(value))))
        result.length = len(result.value)
        return result.set(value)

    def __getstate__(self):
        return super(type,self).__getstate__(),self._object_,self.length

    def __setstate__(self, state):
        state,self._object_,self.length = state
        super(type,self).__setstate__(state)

class terminated(type):
    '''
    an array that terminates deserialization based on the value returned by
    .isTerminator()
    '''
    length = None
    def isTerminator(self, v):
        '''intended to be overloaded. should return True if element /v/ represents the end of the array.'''
        raise error.ImplementationError(self, 'terminated.isTerminator')

    def __len__(self):
        if self.initializedQ():
            return len(self.value)
        raise error.InitializationError(self, 'terminated.__len__')

    def blocksize(self):
        return reduce(lambda x,y: x+y.blocksize(), self.value, 0)

    def load(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                forever = itertools.count() if self.length is None else xrange(self.length)

                self.value = []
                ofs = self.getoffset()
                for index in forever:
                    n = self.new(self._object_,__name__=str(index),offset=ofs)
                    self.value.append(n)
                    if self.isTerminator(n.load()):
                        break

                    s = n.blocksize()
                    if s <= 0 and Config.parray.break_on_zero_size:
                        Config.log.warn("terminated.load : %s : Terminated early due to zero-length element : %s"%( self.instance(), n.instance()))
                        break
                    if s < 0:
                        raise error.AssertionError(self, 'terminated.load', message="Element size for %s is < 0"% n.classname())
                    ofs += s

            return self

        except KeyboardInterrupt:
            # XXX: some of these variables might not be defined due to a race. who cares...
            path = ' -> '.join(self.backtrace())
            Config.log.warn("terminated.load : %s : User interrupt at element %s : %s"% (self.instance(), n.instance(), path))
            return self

        except error.LoadError, e:
            raise error.LoadError(self, exception=e)

    def initializedQ(self):
        return self.v is not None and len(self.v) > 0 and self.v[-1].initializedQ()

class uninitialized(terminated):
    def size(self):
        if self.v is not None:
            value = (_ for _ in self.value if _.value is not None)
            return reduce(lambda x,y: x+y.size(), value, 0)
        raise error.InitializationError(self, 'uninitialized.size')

    def initializedQ(self):
        return self.v is not None

class infinite(uninitialized):
    __offset = 0

    def nextelement(self, **attrs):
        '''method that returns a new element at a specified offset and loads it. intended to be overloaded.'''
        index = len(self.value)
        n = self.new(self._object_, __name__=str(index), offset=self.__offset)
        try:
            n.load(**attrs)
        except error.LoadError,e:
            path = ' -> '.join(self.backtrace())
            Config.log.warn("infinite.nextelement : %s : Unable to read element %s : %s"% (self.instance(), n.instance(), path))
        return n
        
    def isTerminator(self, value):
        return False

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value = []
            self.__offset = self.getoffset()

            try:
                while True:
                    n = self.nextelement()
                    self.value.append(n)
                    if not n.initializedQ():
                        break

                    if self.isTerminator(n):
                        break

                    s = n.blocksize()
                    if s <= 0 and Config.parray.break_on_zero_size:
                        Config.log.warn("infinite.load : %s : Terminated early due to zero-length element : %s"%( self.instance(), n.instance()))
                        break
                    if s < 0:
                        raise error.AssertionError(self, 'infinite.load', message="Element size for %s is < 0"% n.classname())
                    self.__offset += s

            except KeyboardInterrupt:
                # XXX: some of these variables might not be defined due to a race. who cares...
                path = ' -> '.join(self.backtrace())
                Config.log.warn("infinite.load : %s : User interrupt at element %s : %s"% (self.instance(), n.instance(), path))
                return self

            except error.LoadError,e:
                if self.parent is not None:
                    path = ' -> '.join(self.backtrace())
                    Config.log.warn("infinite.load : %s : Stopped reading at element %s : %s"% (self.instance(), n.instance(), path))
                raise error.LoadError(self, exception=e)
        return self

    def loadstream(self, **attr):
        '''an iterator that incrementally populates the array'''
        with utils.assign(self, **attr):
            self.value = []
            self.__offset = self.getoffset()

            try:
                while True:
                    n = self.nextelement()
                    self.value.append(n)
                    yield n

                    if not n.initializedQ():
                        break

                    if self.isTerminator(n):
                        break

                    s = n.blocksize()
                    if s <= 0 and Config.parray.break_on_zero_size:
                        Config.log.warn("infinite.loadstream : %s : Terminated early due to zero-length element : %s"%( self.instance(), n.instance()))
                        break
                    if s < 0:
                        raise error.AssertionError(self, 'infinite.loadstream', message="Element size for %s is < 0"% n.classname())
                    self.__offset += s

            except error.LoadError, e:
                if self.parent is not None:
                    path = ' -> '.join(self.backtrace())
                    Config.log.warn("infinite.loadstream : %s : Stopped reading at element %s : %s"% (self.instance(), n.instance(), path))
                raise error.LoadError(self, exception=e)
            pass
        return

class block(uninitialized):
    def isTerminator(self, value):
        return False

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            forever = itertools.count() if self.length is None else xrange(self.length)
            self.value = []

            if self.blocksize() == 0:   # if array is empty...
                return self

            ofs = self.getoffset()
            current = 0
            for index in forever:
                n = self.new(self._object_, __name__=str(index), offset=ofs)

                try:
                    n = n.load()

                except error.LoadError, e:
                    #e = error.LoadError(self, exception=e)
                    o = current + n.blocksize()

                    # if we error'd while decoding too much, then let user know
                    if o > self.blocksize():
                        path = ' -> '.join(n.backtrace())
                        Config.log.warn("block.load : %s : Reached end of blockarray at %s : %s"%(self.instance(), n.instance(), path))
                        self.value.append(n)

                    # otherwise add the incomplete element to the array
                    elif o < self.blocksize():
                        Config.log.warn("block.load : %s : LoadError raised at %s : %s"%(self.instance(), n.instance(), repr(e)))
                        self.value.append(n)

                    break

                s = n.blocksize()
                if s <= 0 and Config.parray.break_on_zero_size:
                    Config.log.warn("block.load : %s : Terminated early due to zero-length element : %s"%( self.instance(), n.instance()))
                    break
                if s < 0:
                    raise error.AssertionError(self, 'block.load', message="Element size for %s is < 0"% n.classname())

                # if our child element pushes us past the blocksize
                if current + s >= self.blocksize():
                    path = ' -> '.join(n.backtrace())
                    Config.log.info("block.load : %s : Terminated at %s : %s"%(self.instance(), n.instance(), path))
                    self.value.append(n)
                    break

                # add to list, and check if we're done.
                self.value.append(n)
                if self.isTerminator(n):
                    break
                ofs,current = ofs+s,current+s

            pass
        return self

    def initializedQ(self):
        return super(block,self).initializedQ() and self.size() == self.blocksize()

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

    import config,logging
    #config.defaults.log.setLevel(logging.DEBUG)
    #config.defaults.log.setLevel(logging.WARN)
    config.defaults.log.setLevel(logging.FATAL)

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

    class RecordGeneral(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'start'),
            (pint.uint8_t, 'end'),
        ]

    string = 'A'*100
    class qword(ptype.type): length = 8
    class dword(ptype.type): length = 4
    class word(ptype.type): length = 2
    class byte(ptype.type): length = 1

    import random
    random.seed()
    def function(self):
#        if len(self.value) > 0:
#            self[0].load()
#            print self[0]
        return random.sample([byte, word, dword, function2], 1)[0]

    def function2(self):
        return qword()

    @TestCase
    def test_array_type_dword():
        class myarray(parray.type):
            length = 5
            _object_ = dword

        x = myarray()
#        print x
#        print x.length,len(x), x.value
        x.source = provider.string('AAAA'*15)
        x.l
#        print x.length,len(x), x.value
#        print repr(x)
        if len(x) == 5 and x[4].serialize() == 'AAAA':
            raise Success

    @TestCase
    def test_array_type_function():
        class myarray(parray.type):
            length = 16
            _object_ = function

        import provider
        x = myarray()
        x.source = provider.memory()
        x.setoffset(id(x))
        x.load()
#        print x

        import utils
        if len(x) == 16:
            raise Success

    @TestCase
    def test_array_terminated_uint8():
        import pint
        class myarray(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, v):
                if v.serialize() == 'H':
                    return True
                return False

        block = 'GFEDCBABCDHEFG'
        x = myarray(source=provider.string(block)).l
        if len(x) == 11:
            raise Success

    @TestCase
    def test_array_infinite_struct():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        chars = '\xdd\xdd'
        string = chars * 8
        string = string[:-1]

        z = RecordContainer(source=provider.string(string)).l
        if len(z)-1 == int(len(string)/2.0) and len(string)%2 == 1:
            raise Success

    @TestCase
    def test_array_infinite_struct_partial():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        data = provider.string('AAAAA')
        z = RecordContainer(source=data).l
        s = RecordGeneral().a.blocksize()
        if z.blocksize() == len(z)*s and len(z) == 3 and z.size() == 5 and not z[-1].initialized:
            raise Success

    @TestCase
    def test_array_block_uint8():
        import pint
        class container(parray.block):
            _object_ = pint.uint8_t
            blocksize = lambda s:4

        block = ''.join(map(chr,range(0x10)))

        a = container(source=provider.string(block)).l
        if len(a) == 4:
            raise Success

    @TestCase
    def test_array_infinite_type_partial():
        b = ''.join(map(chr,range(ord('a'), ord('z')) + range(ord('A'), ord('Z')) + range(ord('0'), ord('9'))))

        count = 0x10

        child_type = pint.uint32_t
        class container_type(parray.infinite):
            _object_ = child_type
    
        block_length = child_type.length * count
        block = '\x00'*block_length

        n = container_type(source=provider.string(block)).l
        if len(n)-1 == count and not n[-1].initialized:
            raise Success

    @TestCase
    def test_array_block_uint32():
        count = 8

        child_type = pint.uint32_t
        class container_type(parray.block):
            _object_ = child_type
        
        block_length = child_type.length * count
        block = '\x00'*block_length
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
                return reduce(lambda x,y:x*256+int(y), self.v, 0)

            def repr(self, **options):
                if self.initialized:
                    return self.classname() + ' %x'% self.int()
                return self.classname() + ' ???'

        class extreme(parray.infinite):
            _object_ = subarray
            def isTerminator(self, v):
                return v.int() == 0x42424242

        a = extreme(source=provider.string('A'*0x100 + 'B'*0x100 + 'C'*0x100 + 'DDDD'))
        a=a.l
        if len(a) == (0x100 / subarray.length)+1:
            raise Success

    @TestCase
    def test_array_infinite_nested_block():
        import random
        from ptypes import parray,dynamic,ptype,pint,provider

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

        string = ''.join([ chr(random.randint(ord('A'),ord('Z'))) for x in range(0x100) ])
        a = arr(source=provider.string(string))
        a=a.l
        if a.blocksize() == 0x108:
            raise Success

    import array
    @TestCase
    def test_array_infinite_nested_partial():
        class fakefile(object):
            d = array.array('L', ((0xdead*x)&0xffffffff for x in range(0x100)))
            d = array.array('c', d.tostring() + '\xde\xad\xde\xad')
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
        if not a.initialized and x[-2].serialize() == '\xde\xad\xde\xad':
            raise Success

    @TestCase
    def test_array_terminated_string():
        class szstring(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, value):
                return value.int() == 0

        data = provider.string("hello world\x00not included\x00")
        a = szstring(source=data).l
        if len(a) == len('hello world\x00'):
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
                return value.serialize() == 'end\x00'

        data = provider.string("hello world\x00is included\x00end\x00not\x00")
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

        s = (('A'*498) + '\x00\x00') + (('B'*498)+'\x00\x00')
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
                return value.serialize() == '\x00\x00\x00\x00\x00'

        class dundundun(parray.block):
            _object_ = feiverfrei
            blocksize = lambda x: 50

        dat = 'A'*5
        end = '\x00'*5
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

        data = '\xAA\xAA\xAA\xAA'*4
        data+= '\xBB'*4

        x = blocked(source=provider.string(data))
        x = x.l
        if len(x) == 4 and x.size() == 16:
            raise Success

    @TestCase
    def test_array_set_uninitialized():
        import pint
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty())
        a.set([x for x in range(69)])
        if len(a) == 69 and sum(x.num() for x in a) == 2346:
            raise Success

    @TestCase
    def test_array_set_initialized():
        import pint
        class argh(parray.type):
            _object_ = pint.int32_t

        a = argh(source=provider.empty(), length=69)
        a.a.set([42 for _ in range(69)])
        if sum(x.num() for x in a) == 2898:
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
