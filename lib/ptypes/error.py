import exceptions
class Base(exceptions.StandardError):
    """Root exception type in ptypes"""
    def __init__(self, *args):
        return super(Base,self).__init__(args)

    def name(self):
        module = self.__module__
        name = type(self).__name__
        return '.'.join((module,name))

    def __repr__(self):
        return self.__str__()

### errors that are caused by a provider
class ProviderError(Base):
    """Generic error raised by a provider"""
class StoreError(ProviderError):
    """Error while attempting to store some number of bytes"""
    def __init__(self, identity, offset, amount, written=0,  **kwds):
        super(StoreError,self).__init__(kwds)
        self.stored = identity,offset,amount,written
    def __str__(self):
        identity,offset,amount,written = self.stored
        if written > 0:
            return 'StoreError({:s}) : Unable to store bytes ({:x}:{:+x}) : Wrote only {:+d} bytes'.format(type(identity), offset, amount, written)
        return 'StoreError({:s}) : Unable to store bytes ({:x}:{:+x})'.format(type(identity), offset, amount)
class ConsumeError(ProviderError):
    """Error while attempting to consume some number of bytes"""
    def __init__(self, identity, offset, desired, amount=0, **kwds):
        super(ConsumeError,self).__init__(kwds)
        self.consumed = identity,offset,desired,amount
    def __str__(self):
        identity,offset,desired,amount = self.consumed
        if amount > 0:
            return 'ConsumeError({:s}) : Unable to consume bytes ({:x}:{:+x}) : Read only {:+d} bytes'.format(type(identity), offset, desired, amount)
        return 'ConsumeError({:s}) : Unable to consume bytes ({:x}:{:+x})'.format(type(identity), offset, desired)

### errors that can happen during deserialization or serialization
class SerializationError(Base):
    def __init__(self, object, **kwds):
        super(SerializationError,self).__init__(kwds)
        self.object = object
    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()
    def path(self):
        return '{{{:s}}}'.format(str().join(map("<{:s}>".format, self.object.backtrace() or [])))
    def position(self):
        try: bs = '{:+x}'.format(self.object.blocksize())
        except: bs = '+?'
        return '{:x}:{:s}'.format(self.object.getoffset(), bs)
    def __str__(self):
        return ' : '.join((self.objectname(), self.typename(), self.path(), super(SerializationError,self).__str__()))

class LoadError(SerializationError, exceptions.EnvironmentError):
    """Error while initializing object from source"""
    def __init__(self, object, consumed=0, **kwds):
        super(LoadError,self).__init__(object, **kwds)
        self.loaded = consumed,

    def __str__(self):
        consumed, = self.loaded
        if consumed > 0:
            return '{:s} : {:s} : Unable to consume {:+#x} from source ({:s})'.format(self.typename(), self.path(), consumed, super(LoadError,self).__str__())
        return super(LoadError,self).__str__()

class CommitError(SerializationError, exceptions.EnvironmentError):
    """Error while committing object to source"""
    def __init__(self, object, written=0, **kwds):
        super(CommitError,self).__init__(object, **kwds)
        self.committed = written,

    def __str__(self):
        written, = self.committed
        if written > 0:
            return '{:s} : wrote {:+#x} : {:s}'.format(self.typename(), written, self.path())
        return super(CommitError,self).__str__()

class MemoryError(SerializationError, exceptions.MemoryError):
    """Out of memory or unable to load type due to not enough memory"""

### errors that happen due to different requests on a ptypes trie
class RequestError(Base):
    def __init__(self, object, method, message='', **kwds):
        super(RequestError,self).__init__(kwds)
        self.object,self.message = object,message
        self.method = method
    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()
    def methodname(self):
        return str(self.method)
    def __str__(self):
        if self.message:
            return ' : '.join((self.methodname(), self.objectname(), self.typename(), self.message))
        return ' : '.join((self.methodname(), self.objectname(), self.typename()))

class TypeError(RequestError, exceptions.TypeError):
    """Error while generating type or casting to type"""
class InputError(RequestError, exceptions.ValueError):
    """Source has reported termination of input"""
class NotFoundError(RequestError, exceptions.ValueError):
    """Traversal or search was unable to locate requested type or value"""
class InitializationError(RequestError, exceptions.ValueError):
    """Object is uninitialized"""

### assertion errors. doing things invalid
class AssertionError(Base, exceptions.AssertionError):
    def __init__(self, object, method, message='', **kwds):
        super(AssertionError,self).__init__(kwds)
        self.object,self.message = object,message
        self.method = method

    def typename(self):
        return self.object.instance()
    def objectname(self):
        return self.object.__name__ if type(self.object) is type else self.object.shortname()

    def methodname(self):
        return str(self.method)

    def __str__(self):
        if self.message:
            return ' : '.join((self.methodname(), self.objectname(), self.typename(), self.message))
        return ' : '.join((self.methodname(), self.objectname(), self.typename()))

class UserError(AssertionError):
    """User tried to do something invalid (assertion)"""
class DeprecationError(AssertionError):
    """Functionality has been deprecated"""
class ImplementationError(AssertionError, exceptions.NotImplementedError):
    """Functionality is currently unimplemented"""
class SyntaxError(AssertionError, exceptions.SyntaxError):
    """Syntax of a definition is incorrect"""
