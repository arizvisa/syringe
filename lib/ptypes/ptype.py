'''base ptype element'''
__all__ = 'isptype,ispcontainer,type,pcontainer,rethrow'.split(',')
import provider,utils
import types

## this is all a horrible and slow way to do this...
def isiterator(t):
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def isptype(t):
    ''' returns true if specified type is a class and inherits from ptype.type '''
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

def ispcontainer(t):
    ''' returns true if specified type inherits from pcontainer '''
    return isptype(t) and issubclass(t, pcontainer)

def isresolveable(p):
    return isinstance(p, (types.FunctionType, types.MethodType)) or isiterator(p)

def forceptype(p, self):
    ''' as long as value is a function, keep calling it with a context until we get a "ptype" '''

    # of type ptype
    if isinstance(p, type) or isptype(p):
        return p

    # functions
    if isinstance(p, types.FunctionType):
        res = p(self)
        return forceptype(res, self)

    # bound methods
    if isinstance(p, types.MethodType):
        return forceptype(p(), self)

    if False:
        # and lastly iterators
        if isiterator(p):
            return forceptype(p.next(), self)

    raise ValueError('forceptype %s could not be resolved as asked by %s'% (repr(p), self.name()))

## ...and yeah... now it's done.

# fn must be a method, so args[0] will fetch self
import sys,traceback
def rethrow(fn):
    def catch(*args, **kwds):
        try:
            return fn(*args, **kwds)

        except:
            # FIXME: this code is stupid.
            #        what we want is when an exception is raised in
            #          .load/.deserialize, to display the elements involved,
            #          and display the fields that have been successfully
            #          loaded. in order to debug those, all we care about is
            #          what particular field caused the structure initialization
            #          to fail.
            tb = traceback.format_stack()
            self = args[0]
            type, exception = sys.exc_info()[:2]

            path = ' ->\n\t'.join( self.backtrace() )

            res = []
            res.append('')
            res.append('Caught exception: %s\n'% exception)
            res.append(path + ' =>')

            res.append('\t<method name> %s'% fn.__name__)

            if self.initialized:
                if ispcontainer(self.__class__):
                    if self.value:
                        res.append('\t<container length> %x'% len(self.value))
                    else:
                        res.append('\t<container value> %s'% repr(self.value))
                else:
                    res.append('\t<type length> %x'% len(self))

            res.append('')
            res.append('Traceback (most recent call last):')
            res.append( ''.join(tb) )
            res.append('')
            sys.stderr.write('\n'.join(res))
            raise

        pass
    catch.__name__ = 'catching(%s)'% fn.__name__
    return catch

def debug(ptype):
    assert isptype(ptype), '%s is not a ptype'% repr(ptype)
    class newptype(ptype):
        @rethrow
        def deserialize_stream(self, stream):
            return super(newptype, self).deserialize_stream(stream)

        @rethrow
        def load(self):
            return super(newptype, self).load()

        @rethrow
        def commit(self):
            return super(newptype, self).commit()

    newptype.__name__ = 'debug(%s)'% ptype.__name__
    return newptype

def debugrecurse(ptype):
    class newptype(debug(ptype)):
        @rethrow
        def newelement(self, ptype, name, ofs):
            res = forceptype(ptype, self)
            assert isptype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)
            return super(newptype,self).newelement( debug(res), name, ofs )

    newptype.__name__ = 'debugrecurse(%s)'% ptype.__name__
    return newptype

class type(object):
    '''
    A very most atomical ptype.
    
    Contains the following settable properties:
        length:int<w>
            size of ptype
        source:ptypes.provider<rw>
            source of input for ptype

    Readable properties:
        value:str<r>
            contents of ptype

        parent:subclass(ptype.type)<r>
            the ptype that created us

        initialized:bool(r)
            if ptype has been initialized yet
    '''
    offset = 0
    length = 0      # int
    value = None    # str
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    initialized = property(fget=lambda self: self.value is not None and len(self.value) == self.length)    # bool
    source = None   # ptype.provider
    parent = type   # ptype.type

    attrs = None
    
    ## initialization
    def __init__(self, **attrs):
        self.source = self.source or provider.memory()
        self.parent = None
        if attrs:
            self.attrs = attrs
        if self.attrs is None:
            self.attrs = {}

        # update self if user specified
        for k,v in attrs.items():
            setattr(self, k, v)
        return

    def __nonzero__(self):
        return self.initialized

    def size(self):
        '''returns the number of bytes used by type'''
        return int(self.length)

    def blocksize(self):
        '''Can be overloaded to define the block's size'''
        return self.size()

    def __getparent_type(self,type):
        result = []
        self = self.parent
        while self is not None:
            result.append(self.__class__)
            if issubclass(self.__class__,type):
                return self
            self = self.parent
        raise ValueError('type %s not found in chain %s'% (repr(type), repr(result)))

    def __getparent_cmp(self, operand):
        result = []
        self = self.parent
        while self is not None:
            result.append(self.__class__)
            if operand(self):
                return self
            self = self.parent
        if operand(self):
            return self
        raise ValueError('match %s not found in chain %s'% (repr(operand), repr(result)))

    def getparent(self, type=None, cmp=None):
        '''
        Shortcut for traversing up to a parent node looking for a particular type
        XXX: subject to change?
        '''
        if type:
            return self.__getparent_type(type)
        elif cmp:
            return self.__getparent_cmp(cmp)

        return self.parent

    def traverse(self, next=lambda x: x.getparent()):
        '''
        Traverse the tree using the 'next' paremeter to navigate
        '''
        n = self
        while n is not None:
            yield n
            n = next(n)
        return

    def backtrace(self):
        '''Return a backtrace to the root element'''
        path = self.traverse(lambda n: n.parent)
        path = [ 'type:%s name:%s offset:%x'%(x.shortname(), getattr(x, '__name__', repr(None.__class__)), x.getoffset()) for x in path ]
        return list(reversed(path))

    def set(self, string, **kwds):
        '''set entire type equal to string'''
        last = self.value

        res = str(string)
        self.value = res
        self.length = len(res)
        return res

    def alloc(self):
        zero = ( '\x00' for x in utils.infiniterange(0) )
        #self.source = provider.empty()
        return self.deserialize(zero)

    ## operator overloads
    def __cmp__(self, x):
        return [-1,0][id(self) is id(x)]

    def setoffset(self, value, **kwds):
        '''modifies the current offset (should probably be deprecated)'''
        res = self.offset
        self.offset = value
        return res

    def getoffset(self, **kwds):
        '''returns the current offset (should probably be deprecated)'''
        return int(self.offset)

    def newelement(self, ptype, name, ofs):
        '''
        create a new element of type ptype with the specified name and offset.
        This will duplicate the source, and set the new element's .parent
        attribute.
        '''
        res = forceptype(ptype, self)
        assert isptype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)

        if isptype(res):
#            res.name = lambda s: name
            res = res(**self.attrs)     # all children will inherit too
        res.parent = self
        if 'source' not in self.attrs:
            res.source = self.source
        res.__name__ = name
        res.setoffset(ofs)
        return res

    ## reading/writing to memory provider
    l = property(fget=lambda s: s.load())   # abbr
    def load(self):
        '''sync self with some specified data source'''
        self.source.seek( self.getoffset() )
        self.value = self.source.consume(self.blocksize())
        return self

    def commit(self):
        '''write self to self.source'''
        self.source.seek( self.getoffset() )
        self.source.write( self.serialize() )
        return self

    ## byte stream input/output
    def serialize(self):
        '''return self as a byte stream'''
        if self.initialized:
            result = str(self.value)
            bs = self.blocksize()
            if len(result) < bs:
                padding = (bs - len(result)) * self.attrs.get('padding', '\x00')
                return result + padding
            assert len(result) == bs, 'value of %s is larger than blocksize (%d>%d)'%(self.shortname(), len(result), bs)
            return result
        raise ValueError('%s is uninitialized'% self.name())

    def deserialize(self, source):
        '''initialize self using source as a bytestream'''
        self.value = ''
        return self.deserialize_stream(iter(source))

    def deserialize_stream(self, source):
        bs = self.blocksize()
        block = ''.join( (x for i,x in zip(xrange(bs), source)) )
        if len(block) < bs:
            self.value = block[:self.size()]
            path = ' ->\n\t'.join(self.backtrace())
            raise StopIteration("Failed reading %s at offset %x byte %d of %d\n\t%s"%(self.name(), self.getoffset(), len(block), bs, path))

        self.value = block[:self.size()]
        return self

    ## representation
    def name(self):
        return "<class '%s'>"% self.shortname()

    def shortname(self):
        '''intended to be overloaded. should return the short name of the current ptype.'''
        return self.__class__.__name__

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if self.initialized:
            res = repr(''.join(self.serialize()))
        else:
            res = '???'
        return  ' '.join([ofs, self.name(), res])

    def hexdump(self, **kwds):
        return utils.hexdump( self.serialize(), offset=self.getoffset(), **kwds )

    def copy(self):
        result = self.newelement( self.__class__, self.name(), self.getoffset() )
        result.deserialize( self.serialize() )
        return result

    def cast(self, t):
        result = self.newelement( t, 'cast(%s, %s)'% (self.name(), repr(t.__class__)), self.getoffset() )
        try:
            result.deserialize( self.serialize() )
        except StopIteration:
            result.l # try to load it anyways
        return result

class pcontainer(type):
    '''
    This class is capable of containing other ptypes

    Readable properties:
        value:str<r>
            list of all elements that are being contained
    '''
    value = None    # list

    def isInitialized(self):
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value])
    initialized = property(fget=isInitialized)  # bool

    def commit(self):
        '''will commit values of all children back to source'''
        for n in self.value:
            n.commit()
        return self

    def size(self):
        '''Calculate the total used size of a container'''
        return reduce(lambda x,y: x+y.size(), self.value, 0)

    def getoffset(self, field=None, **attrs):
        '''fetch the offset of the specified field'''
        if not field:
            return super(pcontainer, self).getoffset()

        if field.__class__ is list:
            name,res = (field[0], field[1:])
            return self.getoffset(name) + self[name].getoffset(res)

        index = self.getindex(field)
        return self.getoffset() + reduce(lambda x,y: x+y, [ x.size() for x in self.value[:index]], 0)

    def getindex(self, name):
        '''intended to be overloaded. should return the index into self.value of the specified name'''
        raise NotImplementedError('Developer forgot to overload this method')

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if self.initialized:
            res = repr(''.join(self.serialize()))
        else:
            res = '???'
        return  ' '.join([self.name(), res])

    def at(self, offset, recurse=True, **kwds):
        if not recurse:
            for i,n in enumerate(self.value):
                nmin = n.getoffset()
                nmax = nmin + n.blocksize()
                if (offset >= nmin) and (offset < nmax):
                    return n
                continue
            raise ValueError('Specified offset %x not found'%offset)
    
        res = self.at(offset, False, **kwds)

        # drill into containees for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (NotImplementedError, AttributeError):
            pass
        return res
        
    def walkto(self, offset, **kwds):
        '''will walk all the objects needed to reach a particular offset'''
        obj = self

        # drill into containees for more detail
        try:
            while True:
                yield obj
                obj = obj.at(offset, recurse=False, **kwds)
            assert False is True
        except (NotImplementedError, AttributeError):
            pass
        return

    def setoffset(self, value, recurse=False):
        '''modifies the current offset'''
        res = super(pcontainer, self).setoffset(value)
        if recurse:
            assert self.initialized
            for n in self.value:
                n.setoffset(value, recurse=recurse)
                value += n.blocksize()
            pass
        return res

    def serialize(self):
        result = ''.join( (x.serialize() for x in self.value) )
        bs = self.blocksize()
        if len(result) < bs:
            padding = (bs - len(result)) * self.attrs.get('padding', '\x00')
            return result + padding
        if len(result) > bs:
            #XXX: serialized contents is larger than user allowed us to be
            #result = result[:bs]
            pass
        return result

    def load(self):
        assert self.value is not None, 'Parent must initialize self.value'

        self.source.seek(self.getoffset())
        block = self.source.consume(self.blocksize())
        stream = iter(block)
        return self.deserialize_stream(stream)

    def deserialize(self, source):
        assert self.value is not None and source is None, 'Parent must initialize self.value'
        block = ''.join( (x.serialize() for x in self.value) )

        bs = self.blocksize()
        if len(block) < bs:
            padding = (bs - len(block)) * self.attrs.get('padding', '\x00')
            block += padding

        if len(block) > bs:
            path = ' ->\n\t'.join(self.backtrace())
            raise StopIteration("Error reading %s at offset %x byte %d of %d\n\t%s"%(self.name(), self.getoffset(), len(block), bs, path))

        return self.deserialize_stream(iter(block))

    def deserialize_stream(self, source):
        assert self.value is not None, 'Parent must initialize self.value'
        ofs = self.getoffset()
        for n in self.value:
            n.setoffset(ofs)
            n.deserialize_stream(source)
            ofs += n.blocksize()
        return self

if __name__ == '__main__':
    import ptype
    if False:
        class p10bytes(ptype.type):
            length = 10

        import provider

        x = p10bytes()
        print repr(x)
    #    x.load()
    #    print repr(x)

        x.source = provider.memory()
        x.setoffset(id(x))
        x.load()
        print repr(x)

    if False:
        x.value = '\x7fHAI\x01\x01\x01\x00\x00\x00'
        x.commit()

        x.alloc()
        x.deserialize(input.file.read())
        x.set('hello there okay')

        x.set("okay, what the fuck. please work. i'm tired.")
        x.commit()

if __name__ == '__main__':
    class u8(ptype.type): length=1
    class u16(ptype.type): length=2
    class u32(ptype.type): length=4
    
    x = ptype.pcontainer()
    x.append( u8() )
    x.append( u32() )
    x.append( u16() )
    x.append( u16() )
    x.append( u32() )
    x.append( u16() )
    x.append( u8() )
    x.append( u8() )
    x.append( u16() )
