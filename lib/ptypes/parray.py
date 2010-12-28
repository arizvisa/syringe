'''base array element'''
import ptype,utils

class __parray_generic(ptype.pcontainer):
    '''provides the generic features expected out of an array'''
    def __contains__(self,v):
        for x in self.value:
            if x is v:
                return True
        return False

    def __len__(self):
        if not self.initialized:
            return int(self.length)
        return len(self.value)

    # XXX: update offsets (?)
    def insert(self, index, object):
        self.value.insert(index, object)

    # XXX: update offset
    def append(self, object):
        self.value.append(object)

    def extend(self, iterable):
        for x in iterable:
            self.value.append(x)
        return

    def pop(self, index=-1):
        raise NotImplementedError('Implemented, but untested...')
        res = self.value[index]
        del(self.value[index])
        return res

    # XXX: update offsets
    def __delitem__(self, index):
        del(self.value[index])

    def __setitem__(self, index, value):
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
    A pcontainer for managing ranges of a particular object.

    Settable properties:
        _object_:ptype.type<w>
            The type of the array
        length:int<w>
            The length of the array used during initialization of the object
    '''
    _object_ = None     # subclass of ptype.type
    length = 0          # int

    # load ourselves lazily
    def load_block(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            ofs += n.blocksize()
        return self

    # load ourselves incrementally
    def load_container(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            n.load()
            ofs += n.blocksize()
        return self

    def load(self):
        obj = self._object_
        self.value = []

        # which kind of load are we
        if ptype.isptype(obj) and not ptype.ispcontainer(obj):
            self.load_block()

        elif ptype.ispcontainer(obj) or ptype.isresolveable(obj):
            self.load_container()

        return super(type, self).load()

    def __repr__(self):
        res = '???'
        if self.initialized:
            res = repr(''.join(self.serialize()))
            length = len(self)
        else:
            if self.value is None:
                length = 0
            else:
                length = len(self.value)

        ofs = '[%x]'%( self.getoffset() )

        if ptype.isptype(self._object_):
            obj = repr(self._object_)
        else:
            obj = repr(self._object_.__class__)

        name = [lambda:'__name__:%s'%self.__name__, lambda:''][self.__name__ is None]()
        return ' '.join((ofs, self.name(), name, '%s[%d]'% (obj, length), res))

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

    def load(self):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        obj = self._object_

        self.value = []
        ofs = self.getoffset()
        for index in forever:
            n = self.newelement(obj,str(index),ofs)
            self.value.append(n)
            if self.isTerminator(n.load()):
                break
            ofs += n.blocksize()
        return super(type, self).load()

    def __repr__(self):
        # copied..
        res = '???'
        index = '...'
        if self.value is not None:
            res = repr(''.join(self.serialize()))
            index = str(len(self))

        ofs = '[%x]'%( self.getoffset() )

        if ptype.isptype(self._object_):
            obj = repr(self._object_)
        else:
            obj = repr(self._object_.__class__)

        name = [lambda:'__name__:%s'%self.__name__, lambda:''][self.__name__ is None]()
        return ' '.join((ofs, self.name(), name, '%s[%s] %s'% (obj, index, res)))

class infinite(terminated):
    '''
    an array that consumes as much data as possible, and neatly leaves when out of data
    '''
    def isTerminator(self, v):
        if v.initialized:
            return False
        return True

    def load(self):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        obj = self._object_
        self.value = []

        try:
            ofs = self.getoffset()
            for index in forever:
                n = self.newelement(obj, str(index), ofs)
                self.value.append(n.load())
                if self.isTerminator(n):
                    break
                ofs += n.blocksize()
            return super(type, self).load()

        except StopIteration:
            if self.parent is not None:
                path = ' ->\n\t'.join(self.backtrace())
                print "Stopped reading %s at offset %x\n\t%s"%(self.name(), self.getoffset(), path)
            
        return self

class block(terminated):
    __current = 0
    def isTerminator(self, value):
        if value.initialized and self.__current < self.blocksize():
            self.__current += value.blocksize()
            return False
        return True

    def load(self):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        obj = self._object_
        self.value = []

        # FIXME: i'm having a problem with exceptions being raised from another parray.block defined in _object_
        #        to remedy that, should we add a special case for all _object_ instances that subclass parray.terminated?
        #        XXX: this version of parray.block breaks a bunch of my testcases

        ofs = self.getoffset()
        self.__current = 0
        for index in forever:
            n = self.newelement(obj, str(index), ofs)
            try:
                if self.isTerminator(n.load()):
                    break
                self.value.append(n)
            except StopIteration, e:
                print "<parray.block> Non-fatal error while decoding _object_ %s[%d] at offset %x from %x:+%x -> %s"%(n.shortname(), index, n.getoffset(), self.getoffset(), self.blocksize(), e)
                break

            ofs += n.blocksize()
            continue
        return self

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

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
        if len(z) == int(len(string)/2.0) and len(string)%2 == 1:
            raise Success

    @TestCase
    def Test6():
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        z = RecordContainer(source=provider.string('A'*5)).l
        if z.size() == 4 and len(z) == 2:
            raise Success

    @TestCase
    def Test7():
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
    def Test8():
        b = ''.join(map(chr,range(ord('a'), ord('z')) + range(ord('A'), ord('Z')) + range(ord('0'), ord('9'))))

        count = 0x10

        child_type = pint.uint32_t
        class container_type(parray.infinite):
            _object_ = child_type
    
        block_length = child_type.length * count
        block = '\x00'*block_length

        n = container_type(source=provider.string(block)).l
        if len(n) == count:
            raise Success

    @TestCase
    def Test9():
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

#    @TestCase
    def Test10():
        ''' This testcase is wrong '''
        class subarray(parray.type):
            length = 4
            _object_ = pint.uint8_t
            def __int__(self):
                return reduce(lambda x,y:x*256+int(y), self.v, 0)

            def __repr__(self):
                if self.initialized:
                    return self.name() + ' %x'% int(self)
                return self.name() + ' ???'

        class extreme(parray.infinite):
            _object_ = subarray
            def isTerminator(self, v):
                return int(v) == 0x42424242

            def blocksize(self):
                return 7

        a = extreme(source=provider.string('A'*0x100 + 'B'*0x100 + 'C'*0x100))
        a=a.l
        print len(a)
        print a[1].v
        if len(a) == 0x100 / subarray().alloc().size():
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
