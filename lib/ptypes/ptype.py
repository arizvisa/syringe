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

    raise ValueError('Unknown type %s returned in %s'% (repr(p), repr(self)))

## ...and yeah... now it's done.

# fn must be a method, so args[0] will fetch self
import sys,traceback
def rethrow(fn):
    def catch(*args, **kwds):
        try:
            return fn(*args, **kwds)

        except:
            tb = traceback.format_stack()
            self = args[0]
            type, exception = sys.exc_info()[:2]

            getpathtohead = lambda x: x.parent and [x] + getpathtohead(x.parent) or [x]

            # XXX: any way to make this better?
            path = getpathtohead(self)
            path = [ repr(x.name()) for x in reversed(path)]
            path = '\t' + ' ->\n\t'.join(path)
#            id =  repr(map(lambda x: x.__class__, self.value))       # this should be the path from our parent's name to this element

            id = self.name()

            ### FIXME: there _has_ to be a better way than writing to stderr in order to modify the backtrace layout
            res = []
            res.append('')
            res.append('Caught exception %s in'% (repr(exception)))
            res.append(path + '->')
            res.append('\t' + id + '.' + fn.__name__)
            if self.initialized:
                res.append(repr(self.value))
            elif ispcontainer(self.__class__):
                res.append(repr([x.name() for x in self.value]))
            res.append('')
            res.append('Traceback (most recent call last):')
            res.append( ''.join(tb) )
            res.append('')
            sys.stderr.write('\n'.join(res))
            raise

        pass
    catch.__name__ = 'catching(%s)'% fn.__name__
    return catch

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

    initialized = property(fget=lambda self: self.value is not None)    # bool
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
        '''returns the number of bytes occupied'''
        return int(self.length)

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

    def path(self, next=lambda x: x.getparent()):
        '''
        Return the path to get to a particular node as determined by the 'next'
        parameter.
        '''
        n = self
        while n is not None:
            yield n
            n = next(n)
        return

    def alloc(self):
        '''initializes self with zeroes'''
        if not self.initialized:
            self.setoffset(0)
            self.value = '\x00'*self.size()
        return self

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
        res.source = self.source
        res.__name__ = name
        res.setoffset(ofs)
        return res

    ## reading/writing to memory provider
    # if source is undefined, we don't do anything, except for allocate if necessary
    l = property(fget=lambda s: s.load())   # abbr
    def load(self):
        '''sync self with some specified data source'''

        try:
            self.source.seek( self.getoffset() )
            self.value = self.source.consume( self.size() )
            return self

        except MemoryError:
            raise MemoryError('Out of memory trying to allocate %d bytes'% self.size())
        return self

    def commit(self):
        '''write self to self.source'''
        self.source.seek( self.getoffset() )
        self.source.write( self.serialize() )
        return self

    # XXX: perhaps we should remove this if we want to optimze?
    #      we should only be interacting with memory, period...
    # XXX: ..and technicaly if we can interact with memory, we can
    #      use this with files too, heh...  (why am i rewriting this software again?)

    def set(self, string, **kwds):
        '''set entire type equal to string'''
        last = self.value

        res = str(string)
        self.value = res
        self.length = len(res)

        return res

    ## byte stream input/output
    def serialize(self):
        '''return self as a byte stream'''
        if self.initialized:
            return str(self.value)
        raise ValueError('%s is uninitialized'% self.name())

    def deserialize(self, source):
        '''initializes self with input from from the specified iterator 'source\''''
        source = iter(source)
        self.value = ''
        
        try:
            for i,byte in zip(xrange(self.size()), source):
                self.value += byte

        except MemoryError:
            raise MemoryError('Out of memory trying to allocate %d bytes'% self.size())

        if len(self.value) != self.size():
            raise StopIteration("unable to continue reading (byte %d out of %d at %x)"% (len(self.value), self.size(), self.getoffset()))
        return

    ## representation
    def name(self):
        '''intended to be overloaded. should return the name of the current ptype.'''
        return repr(self.__class__)
#        return self.__class__.__name__

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

    def getoffset(self, field=None, **attrs):
        '''fetch the offset of the specified field'''
        if not field:
            return super(pcontainer, self).getoffset()

        if not self.initialized:
            self.load()

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

    def at(self, offset):
        assert self.initialized

        element = None
        for i,n in enumerate(self.value):
            nmin = n.getoffset()
            nmax = nmin + n.size()
            if (offset >= nmin) and (offset < nmax):
                element = n
                break
            continue

        assert element is not None, 'Specified offset %x not found'%offset

        # drill into containees for more detail
        try:
            l = element.at(offset)
            l.append(i)
            return l
        except (NotImplementedError, AttributeError):
            pass

        return [i]

    def setoffset(self, value=0, recurse=False):
        '''modifies the current offset'''
        res = super(pcontainer, self).setoffset(value)
        if recurse:
            assert self.initialized
            for n in self.value:
                n.setoffset(value, recurse=recurse)
                value += n.size()
            pass
        return res

def debug(ptype):
    assert isptype(ptype), '%s is not a ptype'% repr(ptype)
    class newptype(ptype):
        @rethrow
        def deserialize(self, source):
            return super(newptype, self).deserialize(source)

        @rethrow
        def load(self):
            return super(newptype, self).load()

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

if __name__ == '__main__':
    ptype = type
    class p10bytes(ptype):
        length = 10

    import provider

    x = p10bytes()
    print repr(x)
    x.load()
    print repr(x)

    x.source = provider.memprovider()
    x.setoffset(id(x))
    x.load()
    print repr(x)

#    x.value = '\x7fHAI\x01\x01\x01\x00\x00\x00'
#    x.commit()

#    x.alloc()
#    x.deserialize(input.file.read())
#    x.set('hello there okay')

#    x.set("okay, what the fuck. please work. i'm tired.")
#    x.commit()
