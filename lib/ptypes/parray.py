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
            self.append(x)

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
        assert self.initialized
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

    def size(self):
        return reduce(lambda x,y: x+y.size(), self.value, 0)

    def serialize(self):
        return ''.join([ x.serialize() for x in self.value ])

    def deserialize_stream(self, stream):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.addelement_stream(stream, self._object_, str(index), ofs)
            ofs += n.size()
        return self

    # load ourselves lazily
    def load_block(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            ofs += n.size()
        return

    # load ourselves incrementally
    def load_container(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            n.load()
            ofs += n.size()
        return

    def load(self):
        obj = self._object_
        self.value = []

        # which kind of load are we
        if ptype.isptype(obj) and not ptype.ispcontainer(obj):
            self.load_block()

        elif ptype.ispcontainer(obj) or ptype.isresolveable(obj):
            self.load_container()

        if self.initialized:
            return self
        
#        assert len(self) == len(self.value), '%d != %d'% (len(self), len(self.value))

        # now that we know the length, read the array
        self.source.seek(self.getoffset())
        block = self.source.consume(self.size())
        return self.deserialize(block)

    def __repr__(self):
        res = '???'
        if self.initialized:
            res = repr(''.join(self.serialize()))

        ofs = '[%x]'%( self.getoffset() )

        if ptype.isptype(self._object_):
            obj = repr(self._object_)
        else:
            obj = repr(self._object_.__class__)

        return ' '.join((ofs, self.name(), '%s[%d]'% (obj, len(self)), res))

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

    def load_container(self):
        forever = self.length
        if forever is None:
            forever = utils.infiniterange(0)
        else:
            forever = xrange(forever)

        ofs = self.getoffset()
        for index in forever:
            n = self.newelement(self._object_, str(index), ofs)
            self.append(n)
            if self.isTerminator(n.load()):
                break
            ofs += n.size()
        return self

    def deserialize_stream(self, stream):
        forever = self.length
        if forever is None:
            forever = utils.infiniterange(0)
        else:
            forever = xrange(forever)

        ofs = self.getoffset()
        for index in forever:
            n = self.addelement_stream(stream, self._object_, str(index), ofs)
            if self.isTerminator(n):
                break
            ofs += n.size()
        return self

    load_block = load_container

class infinite(terminated):
    '''
    an array that consumes as much data as possible, and neatly leaves when out of data
    '''
    length = None
    def isTerminator(self, v):
        return False

    def load_container(self):
        forever = self.length
        if forever is None:
            forever = utils.infiniterange(0)
        else:
            forever = xrange(forever)

        ofs = self.getoffset()
        for index in forever:
            n = self.newelement(self._object_, str(index), ofs)
            self.append(n.load())       # raise exception first.
            if self.isTerminator(n):    # then check.
                break
            ofs += n.size()
        return self
    load_block = load_container

    def deserialize_stream(self, stream):
        forever = self.length
        if forever is None:
            forever = utils.infiniterange(0)
        else:
            forever = xrange(forever)

        ofs = self.getoffset()
        for index in forever:
            n = self.addelement_stream(stream, self._object_, str(index), ofs)
            if self.isTerminator(n):
                break
            ofs += n.size()
        return self

    def deserialize_stream(self, stream):
        ofs = self.getoffset()
        try:
            return super(infinite, self).deserialize_stream(stream)
        except StopIteration:
            pass
        return self

if __name__ == '__main__':
    import ptype,parray

    string = 'A'*100
    class qword(ptype.type): length = 8
    class dword(ptype.type): length = 4
    class word(ptype.type): length = 2
    class byte(ptype.type): length = 1
   
    import random
    def function(self):
#        if len(self.value) > 0:
#            self[0].load()
#            print self[0]
        return random.sample([byte, word, dword, function2], 1)[0]

    def function2(self):
        return qword()

    class myarray(parray.type):
        length = 5
        _object_ = dword

    x = myarray()
    print x
    print x.length,len(x), x.value
    x.deserialize('AAAA'*15)
    print x.length,len(x), x.value
    print repr(x)

    class myarray(parray.type):
        length = 16
        _object_ = function

    random.seed()
    import provider
    x = myarray()
    x.source = provider.memory()
    x.setoffset(id(x))
    x.load()
    print x

    import utils
    print '\n'.join(['[%d] %s -> %x'% (i, repr(x), x.getoffset()) for x,i in zip(x, utils.infiniterange(0))])

    import pint
    class myarray(parray.terminated):
        _object_ = pint.uint8_t
        def isTerminator(self, v):
            if v.serialize() == 'H':
                return True
            return False

    z = myarray()
    z.deserialize('GFEDCBABCDHEFG')
    print z
    print len(z)

    # FIXME: I don't think the following type of code works anymore...

    import pstruct,parray,pint
    class RecordGeneral(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'start'),
            (pint.uint32_t, 'end'),
        ]

    class RecordContainer(parray.infinite):
        _object_ = RecordGeneral

    chars = '\xdd\xdd\xdd\xdd'
    st = chars * 2
    string = st * 8
    string = string[:-1]

    z = RecordContainer()
    z.deserialize(string)
    print z
