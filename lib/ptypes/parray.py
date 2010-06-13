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
        assert self.initialized
        self.value[index] = value

#    @ptype.rethrow
    def __getitem__(self, index):
        assert self.initialized
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

#    @ptype.rethrow
    def alloc(self):
        self.value = []

        ofs = self.getoffset()
        obj = self._object_
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            n.alloc()
            n.setoffset(ofs)
            ofs += n.size()
        return self

#    @ptype.rethrow
    def deserialize(self, source):
        source = iter(source)
        self.value = []

        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            n.deserialize(source)
            ofs += n.size()
        return

    def load_block(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            ofs += n.size()
        return

    def load_container(self):
        ofs = self.getoffset()
        for index in xrange(self.length):
            n = self.newelement(self._object_, str(index), ofs)
            self.value.append(n)
            n.load()
            ofs += n.size()
        return

#    @ptype.rethrow
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
        self.source.seek( self.getoffset() )
        block = self.source.consume( self.size() )

        # start over and populate entire self with values
        block = iter(block)
        for i in xrange(len(self.value)):
            n = self.value[i]
            n.deserialize(block)

#        assert len(self) == len(self.value), '%d != %d'% (len(self), len(self.value))
        return self

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
    def isTerminator(self, v):
        '''intended to be overloaded. should return True if element /v/ represents the end of the array.'''
        raise NotImplementedError('Developer forgot to overload this method')

    def load_container(self):
        ofs = self.getoffset()
        for index in utils.infiniterange(0):
            n = self.newelement(self._object_, str(index), ofs)
            self.append(n)
            n.load()
            if self.isTerminator(n):
                break
            ofs += n.size()
        return self

#    @ptype.rethrow
    def deserialize(self, source):
        source = iter(source)
        self.value = []

        ofs = self.getoffset()
        for index in utils.infiniterange(0):
            n = self.newelement(self._object_, str(index), ofs)
            self.append(n)
            n.deserialize(source)
            if self.isTerminator(n):
                break
            ofs += n.size()
        return self

    load_block = load_container

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
    import sys
    sys.exit()

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
