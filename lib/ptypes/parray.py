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

    def deserialize(self, source):
        source = iter(source)
        obj = self._object_
        self.value = []
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(type,str(index),ofs)
            self.value.append(n)
            n.deserialize(source)
            ofs += n.blocksize()

        return super(type, self).deserialize(None)

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

        return ' '.join((ofs, self.name(), '%s[%d]'% (obj, length), res))

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

    def deserialize(self, source):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        source = iter(source)
        obj = self._object_
        self.value = []

        ofs = self.getoffset()
        for index in forever:
            n = self.newelement(obj,str(index),ofs)
            self.value.append(n)
            n.deserialize(source)
            if self.isTerminator(n):
                break
            ofs += n.blocksize()
        return super(type, self).deserialize(None)

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

        return ' '.join((ofs, self.name(), '%s[%s] %s'% (obj, index, res)))

class infinite(terminated):
    '''
    an array that consumes as much data as possible, and neatly leaves when out of data
    '''
    def isTerminator(self, v):
        if v.initialized:
            return False
        return True

    def deserialize(self, source):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        source = iter(source)
        obj = self._object_
        self.value = []

        try:
            ofs = self.getoffset()
            for index in forever:
                n = self.newelement(obj,str(index),ofs)
                n.deserialize(source)
                if self.isTerminator(n):
                    break
                self.value.append(n)
                ofs += n.blocksize()
            pass
        except StopIteration:
            if self.parent:
                path = ' ->\n\t'.join(self.backtrace())
                print "Stopped reading %s at offset %x\n\t%s"%(self.name(), self.getoffset(), path)
        return super(type, self).deserialize(None)

    def load(self):
        forever = [lambda:xrange(self.length), lambda:utils.infiniterange(0)][self.length is None]()
        obj = self._object_
        self.value = []

        try:
            ofs = self.getoffset()
            for index in forever:
                n = self.newelement(obj, str(index), ofs)
                if self.isTerminator(n.load()):
                    break
                self.value.append(n)
                ofs += n.blocksize()
            return super(type, self).load()
        except StopIteration:
            if self.parent is not None:
                path = ' ->\n\t'.join(self.backtrace())
                print "Stopped reading %s at offset %x\n\t%s"%(self.name(), self.getoffset(), path)
        return self

class block(infinite):
    __current = 0
    def isTerminator(self, value):
        if value.initialized and self.__current < self.blocksize():
            self.__current += value.blocksize()
            return False
        return True

    def load(self):
        self.__current = 0
        return super(block, self).load()

    def deserialize(self, source):
        self.__current = 0
        return super(block, self).deserialize(source)

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

    class RecordGeneral(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'start'),
            (pint.uint8_t, 'end'),
        ]

    if False:
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

    if False:
        class myarray(parray.type):
            length = 5
            _object_ = dword

        x = myarray()
        print x
        print x.length,len(x), x.value
        x.deserialize('AAAA'*15)
        print x.length,len(x), x.value
        print repr(x)

    if False:
        class myarray(parray.type):
            length = 16
            _object_ = function

        import provider
        x = myarray()
        x.source = provider.memory()
        x.setoffset(id(x))
        x.load()
        print x

        import utils
        print '\n'.join(['[%d] %s -> %x'% (i, repr(x), x.getoffset()) for x,i in zip(x, utils.infiniterange(0))])

    if False:
        import pint
        class myarray(parray.terminated):
            _object_ = pint.uint8_t
            def isTerminator(self, v):
                if v.serialize() == 'H':
                    return True
                return False

        block = 'GFEDCBABCDHEFG'
        z = myarray()
        z.deserialize(block)
        print len(z) == 11

        z = myarray(source=provider.string(block))
        z.l
        print len(z) == 11

        # FIXME: I don't think the following type of code works anymore...

    if False:
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        chars = '\xdd\xdd\xdd\xdd'
        st = chars * 2
        string = st * 8
        string = string[:-1]

        z = RecordContainer()
        z.deserialize(string)
        print z

    if False:
        class RecordContainer(parray.infinite):
            _object_ = RecordGeneral

        z = RecordContainer()
        z.deserialize('A'*5)
        print z
        print z.size() == 4 and len(z) == 2

    if False:
        import pint
        class container(parray.block):
            _object_ = pint.uint8_t
            blocksize = 4

        block = ''.join(map(chr,range(0x10)))

        z = container()
        print z.deserialize(block)
        print len(z) == 4 and z.size() == 4

        a = container(source=provider.string(block))
        a.l
        print a, len(a) == 4

    if False:
        b = ''.join(map(chr,range(ord('a'), ord('z')) + range(ord('A'), ord('Z')) + range(ord('0'), ord('9'))))

        count = 0x10

        child_type = pint.uint32_t
        class container_type(parray.infinite):
            _object_ = child_type
    
        block_length = child_type.length * count
        block = '\x00'*block_length

        n = container_type()
        n.deserialize(block)
        print n, len(n) == count

        from ptypes import provider
        n = container_type(source=provider.string(block))
        n.l
        print n, len(n) == count

    if True:
        count = 8

        child_type = pint.uint32_t
        class container_type(parray.block):
            _object_ = child_type
        
        block_length = child_type.length * count
        block = '\x00'*block_length
        container_type.size = lambda s: child_type.length * 4

        from ptypes import provider
        a = container_type()
        a.deserialize(block)
        print a, len(a) == 4

        a = container_type(source=provider.string(block))
        a.l
        print a, len(a) == 4
        
