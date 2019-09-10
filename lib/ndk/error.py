import functools, itertools, types, builtins, operator, six
import ptypes, exceptions

from . import sdkddkver

class NdkException(ptypes.error.RequestError):
    '''
    Base class for exceptions raised by the ndk library
    '''
    def __init__(self, object, method, *args, **kwds):
        super(NdkException, self).__init__(*((object, method) + args))
        map(None, itertools.starmap(functools.partial(setattr, self), kwds.items()))
        self.__iterdata__ = tuple(args)
        self.__mapdata__ = dict(kwds)
    def __iter__(self):
        for item in self.__iterdata__:
            yield item
        return
    def __str__(self):
        iterdata = map("{!r}".format, self.__iterdata__)
        mapdata = tuple(itertools.starmap("{:s}={!r}".format, self.__mapdata__.iteritems()))
        if hasattr(self, 'message') and isinstance(self.message, six.string_types):
            return "{:s} : {:s}".format(super(NdkException, self).__str__(), self.message)
        res = "({:s})".format(', '.join(itertools.chain(iterdata, mapdata)) if self.__iterdata__ or self.__mapdata__ else '')
        return "{:s} : {:s}".format(super(NdkException, self).__str__(), res)

class NdkUnsupportedVersion(NdkException):
    '''
    Raised when the structure does not support the NTDDI_VERSION that the user has specified.
    '''
    def __init__(self, object):
        version = object.NTDDI_VERSION
        major, minor = sdkddkver.NTDDI_MAJOR(version) / 0x10000, sdkddkver.NTDDI_MINOR(version)
        super(NdkUnsupportedVersion, self).__init__(object, '__init__', major=major, minor=minor, message="An unsupported version ({:#x}.{:#x}) was specified!".format(major, minor))

class NdkAssertionError(NdkException, AssertionError): pass

### Exceptions used by ndk.heaptypes
class NdkHeapException(NdkException):
    '''
    Base class for exceptions raised by the heaptypes module
    '''

class NotFoundException(NdkHeapException): pass
class ListHintException(NdkHeapException): pass
class InvalidPlatformException(NdkHeapException): pass
class InvalidHeapType(NdkHeapException): pass
class IncorrectHeapType(NdkHeapException): pass
class IncorrectChunkType(NdkHeapException): pass
class IncorrectChunkVersion(NdkHeapException): pass
class InvalidBlockSize(NdkHeapException): pass
class CorruptStructureException(NdkHeapException): pass
class CrtZoneNotFoundError(NdkHeapException): pass
class MissingSegmentException(NdkHeapException): pass

