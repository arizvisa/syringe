import types,inspect,itertools,operator
import ptype,utils,bitmap,config,error
Config = config.defaults
__all__ = 'setbyteorder,istype,iscontainer,new,bigendian,littleendian,align,type,container,array,struct,terminatedarray,blockarray,partial'.split(',')

def setbyteorder(endianness):
    '''Sets the _global_ byte order for any pbinary.type.
    
    ``endianness`` can be either pbinary.bigendian or pbinary.littleendian
    '''
    global partial
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        result = partial.byteorder
        partial.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian
        return result
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness %s"% repr(endianness))

# instance tests
@utils.memoize('t')
def istype(t):
    return t.__class__ is t.__class__.__class__ and not ptype.isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

@utils.memoize('t')
def iscontainer(t):
    return istype(t) and issubclass(t, container)

def force(t, self, chain=None):
    """Resolve type ``t`` into a pbinary.type for the provided object ``self``"""
    if chain is None:
        chain = []
    chain.append(t)

    # conversions
    if bitmap.isinteger(t):
        return ptype.clone(type, value=(0,t))
    if bitmap.isbitmap(t):
        return ptype.clone(type, value=t)

    # passthrough
    if istype(t) or isinstance(t, type):
        return t

    # functions
    if isinstance(t, types.FunctionType):
        return force(t(self), self, chain)
    if isinstance(t, types.MethodType):
        return force(t(), self, chain)

    if inspect.isgenerator(t):
        return force(t.next(), self, chain)

    path = ','.join(self.backtrace())
    raise error.TypeError(self, 'force<pbinary>', message='chain=%r : refusing request to resolve %r to a type that does not inherit from pbinary.type : %s'% (chain, t, path))

class type(ptype.generic):
    """An atomic component of any binary array or structure.

    This type is used internally to represent an element of any binary container.
    """
    value,position = None,(0,0)
    def setoffset(self, value, **_):
        _,suboffset = self.getposition()
        return self.setposition((value,suboffset))
    def getoffset(self):
        offset,_ = self.getposition()
        return offset

    @property
    def boffset(self):
        _,suboffset = self.getposition()
        return suboffset
    @boffset.setter
    def boffset(self, value):
        offset,_ = self.getposition()
        self.setposition((offset,value))

    initializedQ = lambda s: s.value is not None

    def num(self):
        return bitmap.number(self.value)
    def bits(self):
        return bitmap.size(self.value)
    def blockbits(self):
        return self.bits()
    def set(self, value):
        if not isinstance(value, (int,long)):
            raise error.UserError(self, 'type.set', message='tried to call .set with an unknown type %s'%value.__class__)
        res = _,size = self.value
        self.value = value,size
        return res
    def bitmap(self):
        return tuple(self.value)
    def update(self, value):
        if not bitmap.isbitmap(value):
            raise error.UserError(self, 'type.update', message='tried to call .update with an unknown type %s'%value.__class__)
        self.value = value
        return self
    def copy(self):
        result = self.new(self.__class__, __name__=self.__name__ if hasattr(self,'__name__') else None, position=self.getposition())
        result.deserialize_consumer(bitmap.consumer().push(self.bitmap()))
        return result

    def __eq__(self, other):
        if isinstance(other, type):
            return (self.initializedQ(),self.bitmap()) == (other.initializedQ(),other.bitmap())
        return False

    def deserialize_consumer(self, consumer):
        try:
            self.set(consumer.consume(self.blockbits()))
        except StopIteration, error:
            raise error
        return self

    def new(self, pbinarytype, **attrs):
        res = force(pbinarytype, self)
        return super(type,self).new(res, **attrs)

    def summary(self, **options):
        if self.initializedQ():
            res = _,size = self.bitmap()
            return '(%s, %d)'% (bitmap.hex(res), size)
        return '???'

    def details(self, **options):
        if self.initializedQ():
            return bitmap.string(self.bitmap())
        return '???'

    def contains(self, offset):
        nmin = self.getoffset()
        nmax = nmin+self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    # default methods
    def size(self):
        return (self.bits()+7)/8
    def blocksize(self):
        return (self.blockbits()+7)/8

    def alloc(self, **attrs):
        '''will initialize a pbinary.type with zeroes'''
        try:
            with utils.assign(self, **attrs):
                result = self.deserialize_consumer( bitmap.consumer('\x00' for x in itertools.count()))

        except StopIteration, error:
            raise error.LoadError(self, exception=error)
        return result

    def properties(self):
        result = super(type, self).properties()
        if self.initializedQ() and bitmap.signed(self.bitmap()):
            result['signed'] = True
        return result

    def repr(self, **options):
        return self.details(**options)

    #def __getstate__(self):
    #    return super(type,self).__getstate__(),self.value,self.position,

    #def __setstate__(self, state):
    #    state,self.value,self.position, = state
    #    super(type,self).__setstate__(state)

class container(type):
    '''contains a list of variable-bit integers'''

    # positioning
    def getposition(self, index=None):
        if index is None:
            return super(container,self).getposition()
        return self.value[index].getposition()

    def setposition(self, (offset,suboffset), recurse=False):
        result = self.getposition()
        ofs,bofs = (offset + (suboffset // 8), suboffset % 8)
        super(container,self).setposition((ofs,bofs))

        if recurse and self.value is not None:
            for n in self.value:
                n.setposition((offset,bofs), recurse=recurse)
                bofs += n.blockbits()
            pass
        return result

    def initializedQ(self):
        if self.value is None:
            return False
        return all(x is not None and isinstance(x,type) and x.initializedQ() for x in self.value)

    ### standard stuff
    def num(self):
        return bitmap.number(self.bitmap())
    def bitmap(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.bitmap')
        return reduce(bitmap.push, map(operator.methodcaller('bitmap'),self.value), bitmap.new(0,0))
    def bits(self):
        return sum(n.bits() for n in self.value)
    def blockbits(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.blockbits')
        return sum(n.blockbits() for n in self.value)
    def blocksize(self):
        return (self.blockbits()+7) // 8

    def set(self, value):
        if not isinstance(value, (int,long)):
            raise error.UserError(self, 'container.set', message='tried to call .set with an unknown type %s'%value.__class__)
        _,size = original = self.bitmap()
        result = value,size
        for element in self.value:
            result,number = bitmap.shift(result, element.bits())
            element.set(number)
        return original

    def update(self, value):
        if bitmap.size(value) != self.blockbits():
            raise error.UserError(self, 'container.update', message='not allowed to change size of container')
        return self.set(bitmap.number(value))

    # loading
    def deserialize_consumer(self, consumer, generator):
        '''initialize container object with bitmap /consumer/ using the type produced by /generator/'''
        if self.value is None:
            raise error.SyntaxError(self, 'container.deserialize_consumer', message='caller is responsible for pre-allocating the elements in self.value')

        position = self.getposition()
        for n in generator:
            self.append(n)
            n.setposition(position)
            n.deserialize_consumer(consumer)

            size = n.blockbits()
            offset,suboffset = position
            suboffset += size
            offset,suboffset = (offset + suboffset/8, suboffset % 8)
            position = (offset, suboffset)
        return self

    def serialize(self):
        Config.log.warn('container.serialize : %s : Returning a potentially unaligned binary structure as a string', self.classname())
        return bitmap.data(self.bitmap())

    def load(self, **attrs):
        raise error.UserError(self, 'container.load', "Not allowed to load from a binary-type. traverse to a partial, and then call .load")

    def commit(self, **attrs):
        raise error.UserError(self, 'container.commit', "Not allowed to commit from a binary-type")

    def alloc(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                result = self.deserialize_consumer(bitmap.consumer(itertools.repeat('\x00')))
        except StopIteration, error:
            raise error.LoadError(self, exception=error)
        return result

    def append(self, object):
        '''Add an element to a pbinary.container. Return it's index.'''
        current,size = len(self.value),0 if self.value is None else self.bits()

        offset,suboffset = self.getposition()
        res = (offset+size//8,suboffset+size%8)

        object.parent,object.source = self,None
        if object.getposition() != res:
            object.setposition(res, recurse=True)

        if self.value is None: self.value = []
        self.value.append(object)
        return current

    def __iter__(self):
        for x in self.value:
            yield x if isinstance(x,container) else x.num()
        return

    def cast(self, container, **attrs):
        if not iscontainer(container):
            raise error.UserError(self, 'container.cast', message='unable to cast to type not of a pbinary.container (%s)'% container.typename())

        source = bitmap.consumer()
        source.push( self.bitmap() )

        target = self.new(container, __name__=self.name(), position=self.getposition(), **attrs)
        target.value = []
        try:
            target.deserialize_consumer(source)
        except StopIteration:
            Config.log.warn('container.cast : %s : Incomplete cast to %s. Target has been left partially initialized.', self.classname(), target.typename())
        return target

    def __getitem__(self, index):
        res = self.value[index]
        return res if isinstance(res,container) else res.num()

    def __setitem__(self, index, value):
        # if it's a pbinary element
        if isinstance(value,type):
            res = self.value[index].getposition()
            if value.getposition() != res:
                value.setposition(res, recurse=True)
            value.parent,value.source = self,None
            self.value[index] = value
            return value

        # if element it's being assigned to is a container
        res = self.value[index]
        if not isinstance(res, type):
            raise error.AssertionError(self, 'container.__setitem__', message='Unknown %s at index %d while trying to assign to it'% (res.__class__, index))

        # if value is a bitmap
        if bitmap.isbitmap(value):
            size = res.blockbits()
            res.update(value)
            if bitmap.size(value) != size:
                self.setposition(self.getposition(), recurse=True)
            return value

        if not isinstance(value, (int,long)):
            raise error.UserError(self, 'container.__setitem__', message='tried to assign to index %d with an unknown type %s'%(index,value.__class__))

        # update a pbinary.type with the provided value clamped
        return res.set(value & ((2**res.bits())-1))

### generics
class _array_generic(container):
    length = 0
    def __len__(self):
        if not self.initialized:
            return self.length
        return len(self.value)

    def __getitem__(self, index):
        return super(_array_generic, self).__getitem__(index)

    def __setitem__(self, index, value):
        value = super(_array_generic, self).__setitem__(index, value)
        if isinstance(value, type):
            value.__name__ = str(index)
        return value

    def summary(self, **options):
        if not self.initialized:
            return self.__summary_uninitialized()
        return self.__summary_initialized()
    def details(self, **options):
        # FIXME: make this display the array in a multiline format
        return self.summary(**options)

    def __getobject_name(self):
        if bitmap.isbitmap(self._object_):
            res = self._object_
            return ('signed<%d>' if bitmap.signed(res) else 'unsigned<%d>')% bitmap.size(res)
        elif istype(self._object_):
            return self._object_.typename()
        elif self._object_.__class__ in (int,long):
            return ('signed<%d>' if self._object_ < 0 else 'unsigned<%d>')% abs(self._object_)
        return self._object_.__name__

    def __summary_uninitialized(self):
        name = self.__getobject_name()
        try:count = len(self)
        except (TypeError): count = None
        return '%s[%s] ???'%(name, repr(count) if count is None else str(count))

    def __summary_initialized(self):
        name,value = self.__getobject_name(),self.bitmap()
        try:count = len(self)
        except (TypeError): count = None
        return '%s[%s] %s'% (name, repr(count) if count is None else str(count), bitmap.hex(value) if bitmap.size(value) > 0 else '...')

    def getindex(self, index):
        if index.__class__ == str:
            return self.getindex(int(index))
        return index

class _struct_generic(container):
    def __init__(self, *args, **kwds):
        super(_struct_generic,self).__init__(*args, **kwds)
        self.__fastindex = {}

    def getposition(self, name=None):
        if name is None:
            return super(_struct_generic,self).getposition()
        index = self.getindex(name)
        return super(_struct_generic,self).getposition(index)

    def append(self, object):
        """Add an element to a pbinary.struct. Return it's index."""
        current = super(_struct_generic,self).append(object)
        self.__fastindex[object.name().lower()] = current
        return current

    def alias(self, alias, target):
        """Add an alias from /alias/ to the field /target/"""
        res = self.getindex(target)
        self.__fastindex[alias.lower()] = res
    def unalias(self, alias):
        """Remove the alias /alias/ as long as it's not defined in self._fields_"""
        if any(alias.lower() == name.lower() for _,name in self._fields_):
            raise error.UserError(self, '_struct_generic.__contains__', message='Not allowed to remove %s from aliases'% alias.lower())
        del self.__fastindex[alias.lower()]

    def getindex(self, name):
        return self.__fastindex[name.lower()]

    def keys(self):
        '''return the name of each field'''
        return [name for type,name in self._fields_]

    def values(self):
        '''return all the integer values of each field'''
        return [ n if isinstance(n,container) else n.num() for n in self.value ]

    def items(self):
        return [(k,v) for (_,k),v in zip(self._fields_, self.values())]

    def __getitem__(self, name):
        index = self.getindex(name)
        return super(_struct_generic, self).__getitem__(index)

    def __setitem__(self, name, value):
        index = self.getindex(name)
        value = super(_struct_generic, self).__setitem__(index, value)
        if isinstance(value, type):
            value.__name__ = name
        return value

    def details(self, **options):
        if not self.initialized:
            return self.__details_uninitialized()
        return self.__details_initialized()

    def __details_initialized(self):
        result = []
        for (t,name),value in map(None,self._fields_,self.value):
            if value is None:
                if istype(t):
                    typename = t.typename()
                elif bitmap.isbitmap(t):
                    typename = 'signed<%s>'%bitmap.size(t) if bitmap.signed(t) else 'unsigned<%s>'%bitmap.size(t)
                elif t.__class__ in (int,long):
                    typename = 'signed<%d>'%t if t<0 else 'unsigned<%d>'%t
                else:
                    typename = 'unknown<%s>'%repr(t)

                i = utils.repr_class(typename)
                result.append('[%s] %s %s ???'%(utils.repr_position(self.getposition(name), hex=Config.display.partial.hex, precision=3 if Config.display.partial.fractional else 0),i,name,v))
                continue

            _,s = b = value.bitmap()
            i = utils.repr_instance(value.classname(),value.name())
            v = '(%s,%d)'%(bitmap.hex(b), s)
            result.append('[%s] %s %s'%(utils.repr_position(self.getposition(name), hex=Config.display.partial.hex, precision=3 if Config.display.partial.fractional else 0),i,value.summary()))
        return '\n'.join(result)

    def __details_uninitialized(self):
        result = []
        for t,name in self._fields_:
            if istype(t):
                s,typename = self.new(t).blockbits(), t.typename()
            elif bitmap.isbitmap(t):
                s,typename = bitmap.size(s),'signed' if bitmap.signed(t) else 'unsigned'
            elif t.__class__ in (int,long):
                s,typename = abs(t),'signed' if t<0 else 'unsigned'
            else:
                s,typename = 0,'unknown'

            i = utils.repr_class(typename)
            result.append('[%s] %s %s{%d} ???'%(utils.repr_position(self.getposition(), hex=Config.display.partial.hex, precision=3 if Config.display.partial.fractional else 0),i,name,s))
        return '\n'.join(result)

    #def __getstate__(self):
    #    return super(_struct_generic,self).__getstate__(),self.__fastindex

    #def __setstate__(self, state):
    #    state,self.__fastindex, = state
    #    super(_struct_generic,self).__setstate__(state)

class array(_array_generic):
    length = 0

    def alloc(self, *fields, **attrs):
        result = super(array,self).alloc(**attrs)
        if len(fields) > 0 and fields[0].__class__ is tuple:
            for k,v in fields:
                idx = result.getindex(k)
                if istype(v) or isinstance(v, type) or ptype.isresolveable(v):
                    result.value[idx] = result.new(v)
                else:
                    result.value[idx].set(v)
                continue
            return result
        for idx,v in enumerate(fields):
            if istype(v) or isinstance(v, type) or ptype.isresolveable(v):
                result.value[idx] = result.new(v)
            else:
                result.value[idx].set(v)
            continue
        return result

    def deserialize_consumer(self, consumer):
        position = self.getposition()
        obj = self._object_
        self.value = []
        generator = (self.new(obj,__name__=str(index),position=position) for index in xrange(self.length))
        return super(array,self).deserialize_consumer(consumer, generator)

    def blockbits(self):
        if self.initialized:
            return super(array,self).blockbits()

        res = 0
        for i in xrange(self.length):
            t = force(self._object_, self)
            n = self.new(t, __name__=str(i))
            res += n.blockbits()
        return res

    def blockbits(self):
        if self.initializedQ():
            return super(array,self).blockbits()

        res = self._object_
        if isinstance(res, (int,long)):
            size = res
        elif bitmap.isbitmap(res):
            size = bitmap.size(res)
        elif istype(res):
            size = self.new(res).blockbits()
        else:
            raise error.InitializationError(self, 'array.blockbits')
        return size * len(self)

    #def __getstate__(self):
    #    return super(array,self).__getstate__(),self._object_,self.length

    #def __setstate__(self, state):
    #    state,self._object_,self.length, = state
    #    super(array,self).__setstate__(state)

class struct(_struct_generic):
    _fields_ = None

    def alloc(self, __attrs__={}, **fields):
        result = super(struct,self).alloc(**__attrs__)
        for k,v in fields.iteritems():
            idx = result.getindex(k)

            if any((istype(v),isinstance(v,type),ptype.isresolveable(v))):
                result.value[idx] = result.new(v)
            else:
                result.value[idx].set(v)
            continue
        return result

    def deserialize_consumer(self, consumer):
        self.value = []
        position = self.getposition()
        generator = (self.new(t,__name__=name,position=position) for t,name in self._fields_)
        return super(struct,self).deserialize_consumer(consumer, generator)

    def blockbits(self):
        if self.initializedQ():
            return super(struct,self).blockbits()
        return sum((t if isinstance(t,(int,long)) else bitmap.size(t) if bitmap.isbitmap(t) else self.new(t,self).blockbits()) for t,_ in self._fields_)

    def __and__(self, field):
        '''Returns the specified /field/'''
        return self[field]

    #def __getstate__(self):
    #    return super(struct,self).__getstate__(),self._fields_,

    #def __setstate__(self, state):
    #    state,self._fields_, = state
    #    super(struct,self).__setstate__(state)

class terminatedarray(_array_generic):
    length = None

    def alloc(self, *fields, **attrs):
        if 'length' in attrs:
            return super(terminatedarray, self).alloc(*fields, **attrs)
    
        # a terminatedarray will always have at least 1 element if it's
        #   initialized
        attrs.setdefault('length',1)
        return super(terminatedarray, self).alloc(*fields, **attrs)

    def deserialize_consumer(self, consumer):
        self.value = []
        obj = self._object_
        forever = itertools.count() if self.length is None else xrange(self.length)
        position = self.getposition()

        def generator():
            for index in forever:
                n = self.new(obj, __name__=str(index), position=position)
                yield n
                if self.isTerminator(n):
                    break
                continue
            return

        p = generator()
        try:
            return super(terminatedarray,self).deserialize_consumer(consumer, p)

        # terminated arrays can also stop when out-of-data
        except StopIteration,e:
            n = self.value[-1]
            path = ' ->\n\t'.join(self.backtrace())
            Config.log.info("terminatedarray : %s : Terminated at %s<%x:+??>\n\t%s"%(self.instance(), n.typename(), n.getoffset(), path))

        return self

    def isTerminator(self, v):
        '''Intended to be overloaded. Should return True if value ``v`` represents the end of the array.'''
        raise error.ImplementationError(self, 'terminatedarray.isTerminator')

    def blockbits(self):
        if self.initializedQ():
            return super(terminatedarray,self).blockbits()
        return 0 if self.length is None else self.new(self._object_).blockbits() * len(self)

class blockarray(terminatedarray):
    length = None
    def isTerminator(self, value):
        return False

    def deserialize_consumer(self, consumer):
        obj,position = self._object_,self.getposition()
        total = self.blocksize()*8
        if total != self.blockbits():
            total = self.blockbits()
        value = self.value = []
        forever = itertools.count() if self.length is None else xrange(self.length)
        generator = (self.new(obj,__name__=str(index),position=position) for index in forever)

        # fork the consumer
        consumer = bitmap.consumer().push( (consumer.consume(total),total) )

        try:
            while total > 0:
                n = generator.next()
                n.setposition(position)
                value.append(n)

                n.deserialize_consumer(consumer)    #
                if self.isTerminator(n):
                    break

                size = n.blockbits()
                total -= size

                (offset,suboffset) = position
                suboffset += size
                offset,suboffset = (offset + suboffset/8, suboffset % 8)
                position = (offset,suboffset)

            if total < 0:
                Config.log.info('blockarray.deserialize_consumer : %s : Read %d extra bits', self.instance(), -total)

        except StopIteration,e:
            # FIXME: fix this error: total bits, bits left, byte offset: bit offset
            Config.log.warn('blockarray.deserialize_consumer : %s : Incomplete read at %s while consuming %d bits', self.instance(), repr(position), n.blockbits())
        return self

class partial(ptype.container):
    value = None
    _object_ = None
    byteorder = Config.integer.order
    initializedQ = lambda s:s.value is not None

    def serialize(self):
        if self.byteorder is config.byteorder.bigendian:
            bmp = self.value.bitmap()
            return bitmap.data(bmp)

        if self.byteorder is not config.byteorder.littleendian:
            raise error.AssertionError(self, 'partial.serialize', message='byteorder %s is invalid'% self.byteorder)
        bmp = self.value.bitmap()
        return ''.join(reversed(bitmap.data(bmp)))

    def deserialize_block(self, block):
        data = iter(block) if self.byteorder is config.byteorder.bigendian else reversed(block)
        return self.value.deserialize_consumer(bitmap.consumer(data))

    def load(self, **attrs):
        try:
            result = self.__load_bigendian(**attrs) if self.byteorder is config.byteorder.bigendian else self.__load_littleendian(**attrs)
            result.setoffset(result.getoffset())
            return result

        except StopIteration, e:
            raise error.LoadError(self, exception=e)

    def __load_bigendian(self, **attrs):
        # big-endian. stream-based
        if self.byteorder is not config.byteorder.bigendian:
            raise error.AssertionError(self, 'partial.load', message='byteorder %s is invalid'% self.byteorder)
        with utils.assign(self, **attrs):
            o = self.getoffset()
            self.source.seek(o)

            self.value = value = self.binaryobject()
            bc = bitmap.consumer( self.source.consume(1) for x in itertools.count() )
            value.deserialize_consumer(bc)
        return self

    def __load_littleendian(self, **attrs):
        # little-endian. block-based
        if self.byteorder is not config.byteorder.littleendian:
            raise error.AssertionError(self, 'partial.load', message='byteorder %s is invalid'% self.byteorder)
        with utils.assign(self, **attrs):
            o,s = self.getoffset(),self.blocksize()
            self.source.seek(o)
            block = ''.join(reversed(self.source.consume(s)))

            self.value = value = self.binaryobject()
            bc = bitmap.consumer(x for x in block)
            value.deserialize_consumer(bc)
        return self

    def commit(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                self.source.seek( self.getoffset() )
                data = self.serialize()
                self.source.store(data)
            return self

        except (StopIteration,error.ProviderError), e:
            raise error.CommitError(self, exception=e)

    def alloc(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                self.value = self.binaryobject()
                result = self.value.deserialize_consumer( bitmap.consumer('\x00' for x in itertools.count()))
            return self
        except (StopIteration,error.ProviderError), e:
            raise error.LoadError(self, exception=e)

    def binaryobject(self, **attrs):
        ofs = self.getoffset()
        obj = force(self._object_, self)
        updateattrs = dict(self.attributes)
        updateattrs.update(attrs)
        updateattrs['position'] = ofs,0
        updateattrs['parent'] = self
        return obj(**updateattrs)

    def bits(self):
        return self.size()*8
    def blockbits(self):
        return self.blocksize()*8

    def size(self):
        v = self.value if self.initialized else self.binaryobject()
        s = v.bits()
        res = (s) if (s&7) == 0x0 else ((s+8)&~7)
        return res / 8
    def blocksize(self):
        v = self.value if self.initialized else self.binaryobject()
        s = v.blockbits()
        res = (s) if (s&7) == 0x0 else ((s+8)&~7)
        return res / 8

    def properties(self):
        result = super(partial,self).properties()
        if self.initialized:
            if self.value.bits() != self.blockbits():
                result['unaligned'] = True
            result['bits'] = self.value.bits()
        result['partial'] = True

        # endianness
        if self.byteorder is config.byteorder.bigendian:
            result['byteorder'] = 'bigendian'
        else:
            if self.byteorder is not config.byteorder.littleendian:
                raise error.AssertionError(self, 'partial.properties', message='byteorder %s is invalid'% self.byteorder)
            result['byteorder'] = 'littleendian'
        return result

    ### passthru
    def __len__(self):
        return len(self.value)
    def __getitem__(self, name):
        return self.value[name]
    def __setitem__(self, name, value):
        self.value[name] = value
    def values(self):
        return self.value.values()
    def num(self):
        return self.value.num()
    def details(self, **options):
        if self.initializedQ():
            return self.value.details(**options)
        return '???'
    def summary(self, **options):
        if self.initializedQ():
            return self.value.summary(**options)
        return '???'
    def __getattr__(self, name):
        if name in ('__module__','__name__'):
            raise AttributeError(name)
        if self.value is None:
            raise error.InitializationError(self, 'partial.__getattr__')
        return getattr(self.value, name)

    def bitmap(self):
        return self.value.bitmap()

    def classname(self):
        fmt = {
            config.byteorder.littleendian : Config.display.partial.littleendian_name,
            config.byteorder.bigendian : Config.display.partial.bigendian_name,
        }
        cn = self.value.classname() if self.initializedQ() else self._object_.typename()
        return fmt[self.byteorder].format(cn, **(utils.attributes(self) if Config.display.mangle_with_attributes else {}))

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin+self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def summary(self, **options):
        if self.value is None:
            return '???'
        return self.value.summary(**options)

    def details(self, **options):
        if self.value is None:
            return '???'
        return self.value.details(**options)

    def repr(self, **options):
        if self.value is None:
            return '???'
        return self.value.repr(**options)

    def get(self):
        return self.value.num()

    def set(self, value, **attrs):
        self.value.set(value)
        return self

    #def __getstate__(self):
    #    return super(partial,self).__getstate__(),self._object_,self.position,self.byteorder,

    #def __setstate__(self, state):
    #    state,self._object_,self.position,self.byteorder, = state
    #    super(type,self).__setstate__(state)

    def setoffset(self, ofs, recurse=False):
        if recurse:
            self.value.setposition((ofs,0), recurse=True)
            return super(partial,self).setoffset(ofs, recurse=False)
        return super(partial,self).setoffset(ofs, recurse=False)

class flags(struct):
    '''represents bit flags that can be toggled'''
    def summary(self, **options):
        if not self.initialized:
            return self.__summary_uninitialized()
        return self.__summary_initialized()

    def __summary_initialized(self):
        flags = []
        for (t,name),value in map(None,self._fields_,self.value):
            if value is None:
                flags.append( (name,value) )
                continue
            flags.append( (name,value.num()) )

        x = _,s = self.bitmap()
        return '(%s, %d) %s'% (bitmap.hex(x), s, ','.join("%s%s"%(n, '?' if v is None else '=%d'%v if v > 1 else '') for n,v in flags if v is None or v > 0))

    def __summary_uninitialized(self):
        return '(flags) %s'% ','.join("%s?"%name for t,name in self._fields_)

    def __and__(self, field):
        '''Returns if the specified /field/ is set'''
        return bool(self[field] > 0)

## binary type conversion/generation
def new(type, **attrs):
    '''Create a new instance of /type/ applying the attributes specified by /attrs/'''
    if istype(type):
        Config.log.debug("new : %s : Instantiating type as partial"% type.typename())
        t = ptype.clone(partial, _object_=type)
        return t(**attrs)
    return type(**attrs)

def bigendian(p, **attrs):
    '''Force binary type /p/ to be ordered in the bigendian integer format'''
    attrs.setdefault('byteorder', config.byteorder.bigendian)
    attrs.setdefault('__name__', p._object_.__name__ if issubclass(p,partial) else p.__name__)

    if not issubclass(p, partial):
        Config.log.debug("bigendian : %s : Promoting type to partial"% p.typename())
        p = ptype.clone(partial, _object_=p, **attrs)
    else:
        p.update_attributes(attrs)
    return p

def littleendian(p, **attrs):
    '''Force binary type /p/ to be ordered in the littleendian integer format'''
    attrs.setdefault('byteorder', config.byteorder.littleendian)
    attrs.setdefault('__name__', p._object_.__name__ if issubclass(p,partial) else p.__name__)

    if not issubclass(p, partial):
        Config.log.debug("littleendian : %s : Promoting type to partial"% p.typename())
        p = ptype.clone(partial, _object_=p, **attrs)
    else:
        p.update_attributes(attrs)
    return p

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
                raise Failure
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
            import traceback
            traceback.print_exc()
            return False
        TestCaseList.append(harness)
        return fn

##########################
if __name__ == '__main__':
    import ptypes,pbinary

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
    def test_pbinary_struct_load_be_global_1():
        pbinary.setbyteorder(config.byteorder.bigendian)
        x = pbinary.new(RECT,source=provider.string('\x4a\xbc\xde\xf0'))
        x = x.l

        if (x['size'],x['value1'],x['value2'],x['value3']) == (4,0xa,0xb,0xc):
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_struct_dynamic_load_2():
        ### inline bitcontainer pbinary.structures
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'header'),
                (RECT, 'rectangle'),
                (lambda self: self['rectangle']['size'], 'heh')
            ]

        s = '\x44\xab\xcd\xef\x00'

        a = pbinary.new(blah,source=provider.string(s)).l

        b = a['rectangle']

        if a['header'] == 4 and (b['size'],b['value1'],b['value2'],b['value3']) == (4,0xa,0xb,0xc):
            raise Success

    @TestCase
    def test_pbinary_struct_be_3():
        #### test for integer endianness
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 0000 0001 1011 1111
        data = '\x01\xbf'
        res = pbinary.new(blah,source=provider.string(data)).l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

    @TestCase
    def test_pbinary_struct_le_4():
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 1011 1111 0000 0001
        data = '\xbf\x01'
        a = blah
        res = pbinary.littleendian(blah)
        b = res
        res = res()

        data = itertools.islice(data, res.a.size())
        res.source = provider.string(''.join(data))
        res.l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

    @TestCase
    def test_pbinary_struct_be_5():
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

        data = '\xaa\xbb\xcc\xdd\x11\x11'

        res = pbinary.new(blah,source=provider.string(data)).l

        if res.values() == [0xa,0xa,0xb,0xb,0xc,0xcd, 0xd]:
            raise Success

    @TestCase
    def test_pbinary_struct_le_6():
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
        data = '\xdd\xcc\xbb\xaa\x11\x11'
        res = blah
        res = pbinary.littleendian(res)
        res = res(source=provider.string(data))
        res = res.l

        if res.values() == [0xa, 0xa, 0xb, 0xb, 0xc, 0xcd, 0xd]:
            raise Success

    @TestCase
    def test_pbinary_struct_unaligned_7():
        x = pbinary.new(RECT,source=provider.string('hello world')).l
        if x['size'] == 6 and x.size() == (4 + 6*3 + 7)/8:
            raise Success
        return

    @TestCase
    def test_pbinary_array_int_load_8():
        class blah(pbinary.array):
            _object_ = bitmap.new(0, 3)
            length = 3

        s = '\xaa\xbb\xcc'

        x = pbinary.new(blah,source=provider.string(s)).l
        if list(x) == [5, 2, 5]:
            raise Success

    @TestCase
    def test_pbinary_struct_bitoffsets_9():
        # print out bit offsets for a pbinary.struct

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]
        class nibble(pbinary.struct): _fields_ = [(4, 'value')]

        class byte(pbinary.array):
            _object_ = halfnibble
            length = 4

        class largearray(pbinary.array):
            _object_ = byte
            length = 16

        res = reduce(lambda x,y: x<<1 | [0,1][int(y)], ('11001100'), 0)

        x = pbinary.new(largearray,source=provider.string(chr(res)*63)).l
        if x[5].num() == res:
            raise Success

    @TestCase
    def test_pbinary_struct_load_10():
        self = pbinary.new(dword,source=provider.string('\xde\xad\xde\xaf')).l
        if self['high'] == 0xdead and self['low'] == 0xdeaf:
            raise Success

    @TestCase
    def test_pbinary_struct_recurse_11():
        ## a struct containing a struct
        class blah(pbinary.struct):
            _fields_ = [
                (word, 'higher'),
                (word, 'lower'),
            ]
        self = pbinary.new(blah,source=provider.string('\xde\xad\xde\xaf')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower']['high'] == 0xde and self['lower']['low'] == 0xaf:
            raise Success

    @TestCase
    def test_pbinary_struct_dynamic_12():
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = pbinary.new(blah,source=provider.string('\xde\xad\x80')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower'] == 0x80:
            raise Success

    @TestCase
    def test_pbinary_array_int_load_13():
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l

        if list(self) == [0xa,0xb,0xc,0xd,0xe,0xf,0x1,0x2]:
            raise Success

    @TestCase
    def test_pbinary_array_struct_load_14():
        ## an array containing a pbinary
        class blah(pbinary.array):
            _object_ = byte
            length = 4

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l

        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test_pbinary_array_dynamic_15():
        class blah(pbinary.array):
            _object_ = lambda s: byte
            length = 4

        data = '\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.string(data)).l

        l = [ x['value'] for x in self ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test_pbinary_struct_struct_load_16():
        class blah(pbinary.struct):
            _fields_ = [
                (byte, 'first'),
                (byte, 'second'),
                (byte, 'third'),
                (byte, 'fourth'),
            ]

        self = pbinary.new(blah)

        import provider
        self.source = provider.string(TESTDATA)
        self.load()

        l = [ v['value'] for v in self.values() ]

        if l == [ ord(TESTDATA[i]) for i,x in enumerate(l) ]:
            raise Success

    @TestCase
    def test_pbinary_struct_struct_load_17():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (dword, 'dw'),
                (4, 'hehhh')
            ]

        import provider
        self = pbinary.new(blah)
        self.source = provider.string(TESTDATA)
        self.load()
        if self['heh'] == 4 and self['dw']['high'] == 0x1424 and self['dw']['low'] == 0x3444 and self['hehhh'] == 9:
            raise Success

    @TestCase
    def test_pbinary_struct_dynamic_load_18():
        class RECT(pbinary.struct):
            _fields_ = [
                (5, 'Nbits'),
                (lambda self: self['Nbits'], 'Xmin'),
                (lambda self: self['Nbits'], 'Xmax'),
                (lambda self: self['Nbits'], 'Ymin'),
                (lambda self: self['Nbits'], 'Ymax')
            ]

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
        z = pbinary.new(RECT,source=provider.string(s)).l

        if z['Nbits'] == 4 and z['Xmin'] == 0xd and z['Xmax'] == 0xe and z['Ymin'] == 0xa and z['Ymax'] == 0xd:
            raise Success

    @TestCase
    def test_pbinary_terminatedarray_19():
        class myarray(pbinary.terminatedarray):
            _object_ = 4

            def isTerminator(self, v):
                if v.num() == 0:
                    return True
                return False

        z = pbinary.new(myarray,source=provider.string('\x44\x43\x42\x41\x3f\x0f\xee\xde')).l
        if z.serialize() == 'DCBA?\x00':
            raise Success

    @TestCase
    def test_pbinary_struct_aggregatenum_20():
        class mystruct(pbinary.struct):
            _fields_ = [
                (4, 'high'),
                (4, 'low'),
                (4, 'lower'),
                (4, 'hell'),
            ]

        z = pbinary.new(mystruct,source=provider.string('\x41\x40')).l
        if z.num() == 0x4140:
            raise Success

    @TestCase
    def test_pbinary_partial_hierarchy_21():
        class mychild1(pbinary.struct):
            _fields_ = [(4, 'len')]
        class mychild2(pbinary.struct):
            _fields_ = [(4, 'len')]

        class myparent(pbinary.struct):
            _fields_ = [(mychild1, 'a'), (mychild2, 'b')]

        from ptypes import provider
        z = pbinary.new(myparent)
        z.source = provider.string('A'*5000)
        z.l

        a,b = z['a'],z['b']
        if (a.parent is b.parent) and (a.parent is z.v):
            raise Success
        raise Failure

    @TestCase
    def test_pstruct_partial_load_22():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.uint32_t, 'v')]

        z = broken(source=provider.string(correct))
        z = z.l
        a = z['h']

        if a['t'] == 69 and a['l'] == 4:
            raise Success
        raise Failure

    @TestCase
    def test_pstruct_partial_le_set_23():
        import pstruct,pint

        correct='\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.littleendian(pint.uint32_t), 'v')]

        z = broken().alloc()
        z['v'].set(8)

        z['h']['l'] = 4
        z['h']['t'] = 0x45

        if z.serialize() == correct:
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_struct_partial_load_24():
        correct = '\x0f\x00'
        class header(pbinary.struct):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        z = pbinary.littleendian(header)(source=provider.string(correct)).l

        if z.serialize() != correct:
            raise Failure
        if z['version'] == 15 and z['instance'] == 0:
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_align_load_25():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (pbinary.align(8), 'b'),
                (4, 'c')
            ]

        x = pbinary.new(blah,source=provider.string('\xde\xad')).l
        if x['a'] == 13 and x['b'] == 14 and x['c'] == 10:
            raise Success
        raise Failure

    import struct
    class blah(pbinary.struct):
        _fields_ = [
            (-16, 'a'),
        ]

    @TestCase
    def test_pbinary_struct_signed_load_26():
        s = '\xff\xff'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_27():
        s = '\x80\x00'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_28():
        s = '\x7f\xff'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_29():
        s = '\x00\x00'
        a = pbinary.new(blah,source=provider.string(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_load_le_conf_30():
        class blah2(pbinary.struct):
            _fields_ = [
                (4, 'a0'),
                (1, 'a1'),
                (1, 'a2'),
                (1, 'a3'),
                (1, 'a4'),
                (8, 'b'),
                (8, 'c'),
                (8, 'd'),
            ]

        s = '\x00\x00\x00\x04'
        a = pbinary.littleendian(blah2)(source=provider.string(s)).l
        if a['a2'] == 1:
            raise Success

    @TestCase
    def test_pbinary_struct_load_31():
        s = '\x04\x00'
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.string(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test_pbinary_struct_load_global_le_32():
        s = '\x00\x04'
        pbinary.setbyteorder(config.byteorder.littleendian)
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.string(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test_pbinary_array_load_iter_33():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        src = provider.string('\xaa'*2)
        x = pbinary.new(test,source=src).l
        if tuple(x) == (1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0):
            raise Success

    @TestCase
    def test_pbinary_array_set_34():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        a = '\xaa'*2
        b = pbinary.new(test).a

        for i,x in enumerate((1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0)):
            b[i] = x

        if b.serialize() == a:
            raise Success

    @TestCase
    def test_pbinary_struct_load_be_conv_35():
        class test(pbinary.struct):
            _fields_ = [(8,'i'),(8,'v')]

        test = pbinary.bigendian(test)
        a = '\x00\x0f'
        b = test(source=provider.string(a)).l
        if b.serialize() == a:
            raise Success

    @TestCase
    def test_pbinary_terminatedarray_multiple_load_36():
        pbinary.setbyteorder(config.byteorder.bigendian)

        # terminated-array
        class part(pbinary.struct):
            _fields_ = [(4,'a'),(4,'b')]

        class encompassing(pbinary.terminatedarray):
            _object_ = part
            def isTerminator(self, value):
                return value['a'] == value['b'] and value['a'] == 0xf

        class complete(pbinary.terminatedarray):
            _object_ = encompassing
            def isTerminator(self, value):
                v = value[0]
                return v['a'] == v['b'] and v['a'] == 0x0

        string = 'ABCD\xffEFGH\xffIJKL\xffMNOP\xffQRST\xffUVWX\xffYZ..\xff\x00!!!!!!!!\xffuhhh'
        a = pbinary.new(complete,source=ptypes.prov.string(string))
        a = a.l
        if len(a) == 8 and a.v[-1][0].bitmap() == (0,8):
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_37():
        pbinary.setbyteorder(config.byteorder.bigendian)

        string = "ABCDEFGHIJKL"
        src = provider.string(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.v) == 8 and a[-1].bitmap() == (0xb4c,12):
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_38():
        pbinary.setbyteorder(config.byteorder.littleendian)

        string = "ABCDEFGHIJKL"
        src = provider.string(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.v) == 8 and a.v[-1].bitmap() == (0x241,12):
            raise Success

    @TestCase
    def test_pbinary_blockarray_load_global_be_39():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class st(pbinary.struct):
            _fields_ = [
                (word, 'mz'),
                (word, 'l'),
                (dword, 'ptr'),
            ]

        class argh(pbinary.blockarray):
            _object_ = st
            def blockbits(self):
                return 32*8

        data = ''.join(map(chr, (x for x in range(48,48+75))))
        src = provider.string(data)
        a = pbinary.new(argh, source=src)
        a = a.l
        if len(a) == 32/8 and a.size() == 32 and a.serialize() == data[:a.size()]:
            raise Success

    @TestCase
    def test_pbinary_array_blockarray_load_global_be_40():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.blockarray):
            _object_ = 32

            def blockbits(self):
                return 32*4

        class ack(pbinary.array):
            _object_ = argh
            length = 4

        data = ''.join((''.join(chr(x)*4 for x in range(48,48+75)) for _ in range(500)))
        src = provider.string(data)
        a = pbinary.new(ack, source=src)
        a = a.l
        if a[0].bits() == 128 and len(a[0]) == 4 and a.blockbits() == 4*32*4 and a[0][-1] == 0x33333333:
            raise Success

    @TestCase
    def test_pbinary_struct_load_signed_global_be_41():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.struct):
            _fields_ = [
                (-8, 'a'),
                (+8, 'b'),
                (-8, 'c'),
                (-8, 'd'),
            ]

        data = '\xff\xff\x7f\x80'
        a = pbinary.new(argh, source=provider.string(data))
        a = a.l
        if a.values() == [-1,255,127,-128]:
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_42():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.array):
            _object_ = -8
            length = 4

        data = '\xff\x01\x7f\x80'
        a = pbinary.new(argh, source=provider.string(data))
        a = a.l
        if list(a) == [-1,1,127,-128]:
            raise Success

    @TestCase
    def test_pbinary_struct_samesize_casting_43():
        from ptypes import pbinary,prov
        class p1(pbinary.struct):
            _fields_ = [(2,'a'),(2,'b'),(4,'c')]
        class p2(pbinary.struct):
            _fields_ = [(4,'a'),(2,'b'),(2,'c')]

        data = '\x5f'
        a = pbinary.new(p1, source=prov.string(data))
        a = a.l
        b = a.cast(p2)
        c = a.v
        d = a.v.cast(p2)
        if b['a'] == d['a'] and b['b'] == d['b'] and b['c'] == d['c']:
            raise Success

    @TestCase
    def test_pbinary_struct_casting_incomplete_44():
        from ptypes import pbinary,prov
        class p1(pbinary.struct):
            _fields_ = [(2,'a'),(2,'b')]
        class p2(pbinary.struct):
            _fields_ = [(4,'a'),(2,'b')]
        data = '\x5f'
        a = pbinary.new(p1, source=prov.string(data))
        a = a.l
        b = a.v.cast(p2)
        x,_ = a.bitmap()
        if b['a'] == x:
            raise Success

    @TestCase
    def test_pbinary_flags_load_45():
        from ptypes import pbinary,prov
        class p(pbinary.flags):
            _fields_ = [
                (1,'set0'),
                (1,'notset1'),
                (1,'set1'),
                (1,'notset2'),
                (1,'set2'),
            ]

        data = '\xa8'
        a = pbinary.new(pbinary.bigendian(p, source=prov.string(data)))
        a = a.l
        if 'notset' not in a.summary() and all(('set%d'%x) in a.summary() for x in range(3)):
            raise Success

    @TestCase
    def test_pbinary_partial_terminatedarray_dynamic_load_46():
        class vle(pbinary.terminatedarray):
            class _continue_(pbinary.struct):
                _fields_ = [(1, 'continue'), (7, 'value')]
            class _sentinel_(pbinary.struct):
                _fields_ = [(0, 'continue'), (8, 'value')]

            def _object_(self):
                if len(self.value) < 4:
                    return self._continue_
                return self._sentinel_

            length = 5
            def isTerminator(self, value):
                if value['continue'] == 0:
                    return True
                return False

        source = '\x80\x80\x80\x80\xff'
        a = pbinary.new(vle, source=ptypes.provider.string(source))
        a = a.load()

        if a.serialize() == '\x80\x80\x80\x80\xff':
            raise Success
        for x in a:
            print x
        print repr(a.serialize())

    @TestCase
    def test_pbinary_pstruct_set_num_47():
        class structure(pbinary.struct):
            _fields_ = [
                (4, 'a'),(4,'b')
            ]
        x = structure()
        res = x.alloc(a=4,b=8)
        if res.num() == 0x48:
            raise Success

    def test_pbinary_parray_set_tuple_48():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        x = array(length=4).alloc((0,0xabcd),(3,0xdcba))
        if x[0].num() == 0xabcd and x[-1].num()==0xdcba:
            raise Success

    def test_pbinary_parray_set_iterable_49():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        x = array(length=4).alloc(0xabcd,0xdcba)
        if x[0].num() == 0xabcd and x[1].num()==0xdcba:
            raise Success

    @TestCase
    def test_pbinary_pstruct_set_container_50():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        class structure(pbinary.struct):
            _fields_ = [
                (array, 'a'),(4,'b')
            ]

        x = array(length=2).alloc(0xdead,0xdead)
        res = structure().alloc(a=x, b=4)
        if res['a'].num() == 0xdeaddead:
            raise Success

    @TestCase
    def test_pbinary_parray_set_container_50():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        class structure(pbinary.struct):
            _fields_ = [
                (8, 'a'),(8,'b')
            ]

        x = array(length=2).alloc((1,structure().alloc(a=0x41,b=0x42)))
        if x[1].num() == 0x4142:
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

