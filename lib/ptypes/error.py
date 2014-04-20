import exceptions as exc
class Base(exc.StandardError):
    """Root exception type in ptypes"""
    def __init__(self, *args, **kwds):
        super(Base,self).__init__(*args)
        self.exception = kwds.get('exception',Exception)

    def name(self):
        module = self.__module__
        name = type(self).__name__
        return '%s.%s'%(module,name)

    def __repr__(self):
        return self.__str__()

### errors that are caused by a provider
class ProviderError(Base):
    """Generic error raised by a provider"""
class StoreError(ProviderError):
    """Error while attempting to store some number of bytes"""
    def __init__(self,identity,offset,amount,written=0,exception=Exception):
        super(StoreError,self).__init__(exception=exception)
        self.args = identity,offset,amount,written
    def __str__(self):
        identity,offset,amount,written = self.args
        if written > 0:
            return 'StoreError(%s) : Unable to store object to 0x%x:+%x : Wrote 0x%x'%( type(identity), offset, amount, written)
        return 'StoreError(%s) : Unable to write object to 0x%x:+%x'%( type(identity), offset, amount)
class ConsumeError(ProviderError):
    """Error while attempting to consume some number of bytes"""
    def __init__(self,identity,offset,desired,amount=0,exception=Exception):
        super(ConsumeError,self).__init__(exception=exception)
        self.args = identity,offset,desired,amount
    def __str__(self):
        identity,offset,desired,amount = self.args
        if amount > 0:
            return 'ConsumeError(%s) : Unable to read from 0x%x:+%x : Read 0x%x'% (type(identity), offset, desired, amount)
        return 'ConsumeError(%s) : Unable to read from 0x%x:+%x'% (type(identity), offset, desired)

### errors that can happen during deserialization or serialization
class SerializationError(Base):
    def __init__(self, object, exception=Exception):
        super(SerializationError,self).__init__(exception=exception)
        self.object = object
    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()
    def path(self):
        return (' -> '.join(self.object.backtrace())) or '<root>'
    def position(self):
        return '%x:+%x'%( self.object.getoffset(), self.object.blocksize() )
    def __str__(self):
        return ' : '.join((self.objectname(), self.typename(), self.position(), self.path(), repr(self.exception)))

class LoadError(SerializationError, exc.EnvironmentError):
    """Error while initializing object from source"""
    def __init__(self, object, consumed=0, exception=Exception):
        super(LoadError,self).__init__(object, exception)
        self.args = consumed,

    def __str__(self):
        consumed, = self.args
        if consumed > 0:
            return '%s : %s : %s : Unable to consume %x from source (%s)'%(self.typename(), self.position(), self.path(), consumed, repr(self.exception))
        return super(LoadError,self).__str__()

class CommitError(SerializationError, exc.EnvironmentError):
    """Error while committing object to source"""
    def __init__(self, object, written=0, exception=Exception):
        super(LoadError,self).__init__(object, exception)
        self.args = written,
    
    def __str__(self):
        written, = self.args
        if written > 0:
            return '%s : %s : wrote %x : %s'%(self.typename(), self.position(), written, self.path())
        return super(CommitError,self).__str__()

class MemoryError(SerializationError, exc.MemoryError):
    """Out of memory or unable to load type due to not enough memory"""

### errors that happen due to different requests on a ptypes trie
class RequestError(Base):
    def __init__(self, object, method, message='',exception=Exception):
        super(RequestError,self).__init__(exception=exception)
        self.object,self.message = object,message
        self.method = method

    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()

    def methodname(self):
        return '%s'% self.method

    def __str__(self):
        if self.message:
            return ' : '.join((self.methodname(), self.objectname(), self.typename(), self.message))
        return ' : '.join((self.methodname(), self.objectname(), self.typename()))

class TypeError(RequestError, exc.TypeError):
    """Error while generating type or casting to type"""
class InputError(RequestError, exc.ValueError):
    """Source has reported termination of input"""
class NotFoundError(RequestError, exc.ValueError):
    """Traversal or search was unable to locate requested type or value"""
class InitializationError(RequestError, exc.ValueError):
    """Object is uninitialized"""

### assertion errors. doing things invalid
class AssertionError(Base, exc.AssertionError):
    def __init__(self, object, method, message='', exception=Exception, *args):
        super(AssertionError,self).__init__(exception=exception)
        self.object,self.message = object,message
        self.method = method
        self.args = args

    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()

    def methodname(self):
        return '%s'% self.method

    def __str__(self):
        if self.message:
            return ' : '.join((self.methodname(), self.objectname(), self.typename(), self.message))
        return ' : '.join((self.methodname(), self.objectname(), self.typename()))

class UserError(AssertionError):
    """User tried to do something invalid (assertion)"""
class DeprecationError(AssertionError):
    """Functionality has been deprecated"""
class ImplementationError(AssertionError, exc.NotImplementedError):
    """Functionality is currently unimplemented"""
class SyntaxError(AssertionError, exc.SyntaxError):
    """Syntax of a definition is incorrect"""
