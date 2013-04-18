'''base array element'''
import ptype,utils,logging

class __parray_generic(ptype.container):
    '''provides the generic features expected out of an array'''
    def __contains__(self,v):
        for x in self.value:
            if x is v:
                return True
        return False

    def __len__(self):
        if not self.initializedQ():
            return int(self.length)
        return len(self.value)

    # XXX: update offsets (?)
    def insert(self, index, object):
        offset = self.value[index].getoffset()
        object.setoffset(offset, recurse=True)
        object.source = self.source  
        self.value.insert(index, object)

        for i in range(index, len(self.value)):
            v = self.value[i]
            v.setoffset(offset, recurse=True)
            offset += v.blocksize()
        return

    def append(self, object):
        offset = self.getoffset()+self.blocksize()
        object.setoffset(offset, recurse=True)
        object.source = self.source  
        self.value.append(object)

    def extend(self, iterable):
        for x in iterable:
            self.value.append(x)
        return

    def pop(self, index=-1):
        raise NotImplementedError('Implemented, but untested (offsets might be off)...')
        res = self.value[index]
        del(self.value[index])
        return res

    # XXX: update offsets
    def __delitem__(self, index):
        del(self.value[index])

    def __setitem__(self, index, value):
        assert isinstance(value, ptype.type), 'Cannot assign a non-ptype to an element of a container. Use .set instead.'

        offset = self.value[index].getoffset()
        value.setoffset(offset, recurse=True)
        value.source = self.source  
        self.value[index] = value

    def __getitem__(self, index):
        return self.value[index]

    def __getslice__(self, i, j):
        res = self.value[i:j]
        # XXX: perhaps fetch elements from memory too
        return res

    def __delslice__(self, i, j):
        del(self.value[i:j])

    def __iter__(self):
        assert self.value is not None
        for x in list(self.value):
            yield x

class type(__parray_generic):
    '''
    A container for managing ranges of a particular object.

    Settable properties:
        _object_:ptype.type<w>
            The type of the array
        length:int<w>
            The length of the array used during initialization of the object
    '''
    #_object_ = None     # subclass of ptype.type
    length = 0          # int

    def contains(self, offset):
        return super(ptype.container, self).contains(offset)

    # load ourselves lazily
    def load_block(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs, source=self.source)
            self.value.append(n)
            ofs += n.blocksize()
        return self

    # load ourselves incrementally
    def load_container(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs, source=self.source)
            self.value.append(n)
            n.load()
            ofs += n.blocksize()
        return self

    def load(self, **attrs):
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
                raise NotImplementedError('Unknown load type -> %s'% (repr(obj)))

            result = super(type, self).load()
        return result

    def details(self):
        if self.initializedQ():
            res = repr(''.join(self.serialize()))
            length = len(self)
        else:
            res = '???'
            length = 0 if self.value is None else len(self.value)

        if ptype.istype(self._object_):
            obj = self._object_().name()
        else:
            obj = repr(self._object_.__class__)

        return '%s[%d] %s'% (obj, length, res)

class terminated(type):
    '''
    an array that terminates deserialization based on the value returned by
    .isTerminator()
    '''
    length = None
    def isTerminator(self, v):
        '''intended to be overloaded. should return True if element /v/ represents the end of the array.'''
        raise NotImplementedError('Developer forgot to overload this method')

    def __len__(self):
        return len(self.value)

    def blocksize(self):
        return reduce(lambda x,y: x+y.blocksize(), self.value, 0)

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            forever = utils.infiniterange(0) if self.length is None else xrange(self.length)

            self.value = []
            ofs = self.getoffset()
            for index in forever:
                n = self.newelement(self._object_,str(index),ofs)
                self.value.append(n)
                if self.isTerminator(n.load()):
                    break
                s = n.blocksize(); assert s > 0; ofs += s

        return self

    def details(self):
        # copied..
        res = '???'
        index = '...'
        if self.value is not None:
            res = repr(''.join(self.serialize()))
            index = str(len(self))

        if ptype.istype(self._object_):
            obj = self._object_().name()
        else:
            obj = repr(self._object_.__class__)
        return '%s[%s] %s'% (obj, index, res)

class infinite(terminated):
    __offset = 0

    def nextelement(self, **attrs):
        '''method that returns a new element at a specified offset and loads it. intended to be overloaded.'''
        index = len(self.value)
        n = self.newelement(self._object_, str(index), self.__offset)
        try:
            n.load(**attrs)
        except StopIteration:
            logging.warn("%s.infinite : unable to read %x:+%x bytes for %s in %s", self.__module__, n.getoffset(), n.blocksize(), n.name(), self.name())
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

                    s = n.blocksize(); assert s > 0; self.__offset += s

            except StopIteration:
                if self.parent is not None:
                    path = ' ->\n\t'.join(self.backtrace())
                    logging.warn("<parray.infinite> Stopped reading %s<%x:+%x> at %s<%x:+??>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), path))
                raise
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

                    s = n.blocksize(); assert s > 0; self.__offset += s

            except StopIteration, (msg):
                logging.debug("<parray.infinite> StopIteration(%s)", msg)
                if self.parent is not None:
                    path = ' ->\n\t'.join(self.backtrace())
                    logging.warn("<parray.infinite> Stopped reading %s<%x:+%x> at %s<%x:+??>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), path))
                raise
            pass
        return
        
class block(terminated):
    def isTerminator(self, value):
        return False

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            forever = utils.infiniterange(0) if self.length is None else xrange(self.length)
            self.value = []

            ofs = self.getoffset()
            current = 0
            for index in forever:
                n = self.newelement(self._object_, str(index), ofs)

                try:
                    n = n.load()

                except StopIteration, e:
                    o = current + n.blocksize()

                    # if we error'd while decoding too much, then let user know
                    if o > self.blocksize():
                        path = ' ->\n\t'.join(n.backtrace())
                        logging.warn("parray.block.load : %s<%x:+%x> : Refusing to initialize element %s<%x:+%x> due to blocksize() constraint.\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), n.blocksize(), path))
                        self.value.append(n)

                    # otherwise add the incomplete element to the array
                    elif o < self.blocksize():
                        logging.warn("parray.block.load : %s<%x:+%x> : StopIteration raised while performing load %s<%x:+%x>\n\t%s"%(self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), n.blocksize(), e))
                        self.value.append(n)

                    break

                s = n.blocksize()
                assert s > 0

                # if our child element pushes us past the blocksize
                if current + s >= self.blocksize():
                    path = ' ->\n\t'.join(n.backtrace())
                    logging.info("parray.block.load : %s : Terminated %s<%x:+%x> at %s<%x:+%x>\n\t%s"%(self.shortname(), self.shortname(), self.getoffset(), self.blocksize(), n.shortname(), n.getoffset(), s, path))
                    self.value.append(n)
                    break

                # add to list, and check if we're done.
                self.value.append(n)
                if self.isTerminator(n):
                    break
                ofs,current = ofs+s,current+s

            pass
        return self

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

    import logging
#    logging.root=logging.RootLogger(logging.DEBUG)

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
    def Test1():
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
    def Test2():
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
    def Test3():
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
    def Test4():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        chars = '\xdd\xdd'
        string = chars * 8
        string = string[:-1]

        z = RecordContainer(source=provider.string(string)).l
        if len(z)-1 == int(len(string)/2.0) and len(string)%2 == 1:
            raise Success

    @TestCase
    def Test5():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        z = RecordContainer(source=provider.string('A'*5)).l
        s = RecordGeneral().a.blocksize()
        if z.size() == len(z)*s and len(z) == 3 and not z[-1].initialized:
            raise Success

    @TestCase
    def Test6():
        import pint
        class container(parray.block):
            _object_ = pint.uint8_t
            blocksize = lambda s:4

        block = ''.join(map(chr,range(0x10)))

        a = container(source=provider.string(block)).l
        if len(a) == 4:
            raise Success
        print a

    @TestCase
    def Test7():
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
    def Test8():
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
    def Test9():
        class subarray(parray.type):
            length = 4
            _object_ = pint.uint8_t
            def int(self):
                return reduce(lambda x,y:x*256+int(y), self.v, 0)

            def repr(self):
                if self.initialized:
                    return self4name() + ' %x'% self.int()
                return self.name() + ' ???'

        class extreme(parray.infinite):
            _object_ = subarray
            def isTerminator(self, v):
                return v.int() == 0x42424242

        a = extreme(source=provider.string('A'*0x100 + 'B'*0x100 + 'C'*0x100 + 'DDDD'))
        a=a.l
        if len(a) == (0x100 / subarray.length)+1:
            raise Success

    @TestCase
    def Test10():
        import random
        from ptypes import parray,dyn,ptype,pint,provider

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
    def Test11():
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
    def Test12():
        class szstring(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, value):
                return value.int() == 0

        data = provider.string("hello world\x00not included\x00")
        a = szstring(source=data).l
        if len(a) == len('hello world\x00'):
            raise Success

    @TestCase
    def Test13():
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
    def Test14():
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
    def Test15():
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
    def test16():
        # ??? parray.block is not respecting .blocksize
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

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
