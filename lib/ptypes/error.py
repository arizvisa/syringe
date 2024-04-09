import builtins as exceptions

class Base(exceptions.Exception):
    """Root exception type in ptypes"""
    def __init__(self, *args):
        return super(Base, self).__init__(*args)
    def name(self):
        cls, module = self.__class__, self.__module__
        return '.'.join([module, cls.__name__])
    def __str__(self):

        # micropython's implementation of Exception doesn't seem to
        # include Exception.__str__ yet, so we check to see if it
        # seems to exist and use it if so.
        if hasattr(exceptions.Exception, '__str__'):
            return super(Base, self).__str__()

        # otherwise, it seems the default python implements this as
        # an empty string...so, is this a specification problem?
        return ''
    def __repr__(self):
        return self.__str__()

class ObjectBase(Base):
    '''Exception type that wraps a particular ptype instance'''
    def __init__(self, object, **kwargs):
        super(ObjectBase, self).__init__(*kwargs.items())
        self.__object = object

    @property
    def object(self):
        return self.__object

    def instanceQ(self):
        return False if isinstance(self.__object, type) else True

    def instance(self):
        item = self.__object
        return "{!s}".format(item.instance() if hasattr(item, 'instance') else item.__class__)

    def objectname(self):
        item = self.__object
        if self.instanceQ() and hasattr(item, 'shortname'):
            return item.shortname()
        cls = item.__class__
        return '.'.join([item.__module__, item.__name__ if hasattr(item, '__name__') else cls.__name__])

    def __str__(self):
        if self.instanceQ():
            return "{:s} ({:s})".format(self.instance(), self.objectname()) + (" : {!r}".format(self.args) if self.args else '')
        return self.objectname()

class MethodBase(ObjectBase):
    '''Exception type that wraps the method of a particular ptype instance'''
    def __init__(self, object, method, **kwargs):
        super(MethodBase, self).__init__(object, **kwargs)
        self.__method = method

    def methodname(self):
        return "{!s}".format(self.__method)

    def __str__(self):
        if self.instanceQ():
            return ' : '.join(["{:s} ({:s})".format(self.instance(), self.objectname()), self.methodname()])
        return ' : '.join([self.objectname(), self.methodname()])

class MethodBaseWithMessage(MethodBase):
    '''Exception type that wraps the method of a particular ptype instance with some message'''
    def __init__(self, object, method, message='', **kwargs):
        super(MethodBaseWithMessage, self).__init__(object, method, **kwargs)
        self.__message = message

    def __str__(self):
        res = super(MethodBaseWithMessage, self).__str__()
        if self.__message:
            return ' : '.join((res, self.__message))
        return res

### errors that are caused by a provider
class ProviderError(Base):
    """Generic error raised by a provider"""
class StoreError(ProviderError):
    """Error while attempting to store some number of bytes"""
    def __init__(self, identity, offset, amount, written=None, **kwds):
        super(StoreError, self).__init__(*[(name, kwds[name]) for name in kwds])
        self.stored = identity, offset, amount, written
    def __str__(self):
        identity, offset, amount, written = self.stored
        if written is not None:
            return 'StoreError({!s}) : Only stored {:+#x} of {:+#x} bytes to {:#x}.'.format(type(identity), written, amount, offset)
        return 'StoreError({!s}) : Error storing {:+#x} bytes to {:#x}.'.format(type(identity), amount, offset)
class ConsumeError(ProviderError):
    """Error while attempting to consume some number of bytes"""
    def __init__(self, identity, offset, desired, amount, **kwds):
        super(ConsumeError, self).__init__(**kwds)
        self.consumed = identity, offset, desired, amount
    def __str__(self):
        identity, offset, desired, amount = self.consumed
        if amount is not None:
            return 'ConsumeError({!s}) : Only consumed {:+#x} of desired {:+#x} bytes from offset {:+#x}.'.format(type(identity), amount, desired, offset)
        return 'ConsumeError({!s}) : Error consuming {:+#x} bytes from {:#x}.'.format(type(identity), desired, offset)

### errors that can happen during deserialization or serialization
class SerializationError(ObjectBase):
    def path(self):
        return '{{{:s}}}'.format(str().join(map("<{:s}>".format, self.object.backtrace() or [])))
    def position(self):
        try: bs = '{:+x}'.format(self.object.blocksize())
        except Exception: bs = '+?'
        return '{:x}:{:s}'.format(self.object.getoffset(), bs)
    def __str__(self):
        return ' : '.join((self.objectname(), self.instance(), self.path(), super(SerializationError, self).__str__()))

class LoadError(SerializationError, exceptions.EnvironmentError):
    """Error while initializing object from source"""
    def __init__(self, object, consumed=0, **kwds):
        self.loaded = kwds.pop('offset', None), consumed
        super(LoadError, self).__init__(object, **kwds)

    def __str__(self):
        offset, consumed = self.loaded
        if offset is not None and consumed > 0:
            return '{:s} : {:s} : Only {:+#x} bytes were loaded from offset {:#x} of source.'.format(self.instance(), self.path(), consumed, offset)
        elif consumed > 0:
            return '{:s} : {:s} : Only {:+#x} bytes were loaded from source.'.format(self.instance(), self.path(), consumed)
        return super(LoadError, self).__str__()

class CommitError(SerializationError, exceptions.EnvironmentError):
    """Error while committing object to source"""
    def __init__(self, object, written=0, **kwds):
        self.committed = kwds.pop('offset', None), written
        super(CommitError, self).__init__(object, **kwds)

    def __str__(self):
        offset, written = self.committed
        if offset is not None and written > 0:
            return '{:s} : Only {:+#x} bytes were committed to offset {:#x} of source'.format(self.instance(), offset, written)
        elif written > 0:
            return '{:s} : Only {:+#x} bytes were committed to source.'.format(self.instance(), written)
        return super(CommitError, self).__str__()

class MemoryError(SerializationError, exceptions.MemoryError):
    """Out of memory or unable to load type due to not enough memory"""

### errors that happen due to different requests on a ptypes trie
class RequestError(MethodBaseWithMessage):
    """Error that happens when requesting from a ptypes trie."""

class TypeError(RequestError, exceptions.TypeError):
    """Error while generating type or casting to type"""
class InputError(RequestError, exceptions.ValueError):
    """Source has reported termination of input"""
class ItemNotFoundError(RequestError, exceptions.ValueError):
    """Traversal or search was unable to locate requested type or value"""
class InitializationError(RequestError, exceptions.ValueError):
    """Object is uninitialized"""

### assertion errors. doing things invalid
class AssertionError(MethodBaseWithMessage, exceptions.AssertionError):
    """Assertion error where the implementation fails a sanity check"""

class UserError(AssertionError):
    """User tried to do something invalid (assertion)"""
class DeprecationError(AssertionError):
    """Functionality has been deprecated"""
class ImplementationError(AssertionError, exceptions.NotImplementedError):
    """Functionality is currently unimplemented"""
class SyntaxError(AssertionError, exceptions.SyntaxError):
    """Syntax of a definition is incorrect"""
