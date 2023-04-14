import sys, ptypes, itertools, logging, traceback
from ptypes import pstruct, parray, ptype, pbinary, pstr, dyn
from ..headers import *

from . import exports, imports, resources, exceptions, relocations, debug, loader, clr, tls, headers

## directory entry base types
class AddressEntry(headers.IMAGE_DATA_DIRECTORY): addressing = staticmethod(virtualaddress)
class OffsetEntry(headers.IMAGE_DATA_DIRECTORY):  addressing = staticmethod(fileoffset)

## directory entry list
class IMAGE_DIRECTORY_ENTRY_EXPORT(AddressEntry):
    _object_ = exports.IMAGE_EXPORT_DIRECTORY

class IMAGE_DIRECTORY_ENTRY_IMPORT(AddressEntry):
    _object_ = imports.IMAGE_IMPORT_DIRECTORY

class IMAGE_DIRECTORY_ENTRY_RESOURCE(AddressEntry):
    #_object_ = resources.IMAGE_RESOURCE_DIRECTORY
    class _object_(resources.IMAGE_RESOURCE_DIRECTORY):
        def __ResourceData(self):
            first, last = self.value[0], self.value[-1]
            lastoffset, lastsize = last.getoffset(), last.blocksize()
            start, stop = first.getoffset(), last.getoffset() + last.blocksize()
            blocksize, expected = self.blocksize(), stop - start

            # If the IMAGE_DIRECTORY_ENTRY is lying about the size of its data,
            # then warn the user about it and correct it to the minimum.
            if expected > blocksize and self.p and self.p.p:
                directory = self.getparent(headers.IMAGE_DATA_DIRECTORY)
                log = logging.getLogger(__name__)
                log.warning("{:s} : Ignoring size ({:#x}) inside {:s} entry as it is smaller than the minimum size of {:s} ({:#x}).".format(__name__, blocksize, directory.instance(), self.instance(), expected))
                log.warning("{:s} : Traceback (most recent call last):".format(__name__))
                stack = [item.split('\n') for item in traceback.format_list(traceback.extract_stack()[:-1])]
                [log.warning("{:s} : {:s}".format(__name__, item.rstrip())) for item in itertools.chain(*stack)]
            return dyn.block(max(expected, blocksize) - expected)

        _fields_ = resources.IMAGE_RESOURCE_DIRECTORY._fields_[:] + [(__ResourceData, 'ResourceData')]

class IMAGE_DIRECTORY_ENTRY_EXCEPTION(AddressEntry):
    _object_ = exceptions.IMAGE_EXCEPTION_DIRECTORY

class IMAGE_DIRECTORY_ENTRY_SECURITY(OffsetEntry):
    class _object_(parray.block):
        _object_ = headers.Certificate

class IMAGE_DIRECTORY_ENTRY_BASERELOC(AddressEntry):
    _object_ = relocations.IMAGE_BASERELOC_DIRECTORY

class IMAGE_DIRECTORY_ENTRY_DEBUG(AddressEntry):
    _object_ = debug.IMAGE_DEBUG_DIRECTORY
class IMAGE_DIRECTORY_ENTRY_ARCHITECTURE(AddressEntry):
    '''IMAGE_DIRECTORY_ENTRY_COPYRIGHT'''
class IMAGE_DIRECTORY_ENTRY_GLOBALPTR(AddressEntry):
    pass

class IMAGE_DIRECTORY_ENTRY_TLS(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        return tls.IMAGE_TLS_DIRECTORY64 if res.is64() else tls.IMAGE_TLS_DIRECTORY32

class IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        res = loader.IMAGE_LOAD_CONFIG_DIRECTORY64 if res.is64() else loader.IMAGE_LOAD_CONFIG_DIRECTORY32
        #return dyn.clone(res, blocksize=lambda self, cb=self['Size'].li.int(): cb)
        return res

class IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT(OffsetEntry):
    _object_ = imports.IMAGE_BOUND_IMPORT_DIRECTORY
class IMAGE_DIRECTORY_ENTRY_IAT(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        return imports.IMAGE_IMPORT_ADDRESS_TABLE64 if res.is64() else imports.IMAGE_IMPORT_ADDRESS_TABLE
class IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT(AddressEntry):
    _object_ = imports.IMAGE_DELAYLOAD_DIRECTORY
class IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR(AddressEntry):
    _object_ = clr.IMAGE_COR20_HEADER
class IMAGE_DIRECTORY_ENTRY_RESERVED(AddressEntry): pass

class DataDirectoryEntry(pint.enum):
    _values_ = [
        ('Export', 0),
        ('Import', 1),
        ('Resource', 2),
        ('Exception', 3),
        ('Security', 4),
        ('BaseReloc', 5),
        ('Debug', 6),
        ('Architecture', 7),
        ('GlobalPtr', 8),
        ('Tls', 9),
        ('LoadConfig', 10),
        ('BoundImport', 11),
        ('IAT', 12),
        ('DelayLoad', 13),
        ('ClrHeader', 14),
        ('Reserved', 15),

        # aliases
        ('Exports', 0),
        ('Imports', 1),
        ('Resources', 2),
        ('Exceptions', 3),
        ('Certificate', 4),
        ('Reloc', 5),
        ('Relocations', 5),
        ('Relocation', 5),
        ('BaseRelocation', 5),
        ('BaseRelocations', 5),
        ('Global', 8),
        ('Thread', 9),
        ('ThreadLocalStorage', 9),
        ('LoaderConfig', 10),
        ('Loader', 10),
        ('Bound', 11),
        ('BoundImports', 11),
        ('ImportAddress', 12),
        ('DelayImportDescriptor', 13),
        ('DelayImport', 13),
        ('Clr', 14),
        ('COM', 14),
        ('COR20', 14),
    ]

class DataDirectory(parray.type):
    length = 16

    def __getindex__(self, key):
        string_types = (str, unicode) if sys.version_info.major < 3 else (str,)
        if isinstance(key, string_types):
            # try and be smart in case user tries to be dumb
            mapping = DataDirectoryEntry.mapping()
            key, res = key.lower(), { k.lower() : v for k, v in mapping.items() }
            key = key[:key.rfind('table')] if key.endswith('table') else key[:]
            return res[key]
        return key

    def _object_(self):
        entries = (
            IMAGE_DIRECTORY_ENTRY_EXPORT,
            IMAGE_DIRECTORY_ENTRY_IMPORT,
            IMAGE_DIRECTORY_ENTRY_RESOURCE,
            IMAGE_DIRECTORY_ENTRY_EXCEPTION,
            IMAGE_DIRECTORY_ENTRY_SECURITY,
            IMAGE_DIRECTORY_ENTRY_BASERELOC,
            IMAGE_DIRECTORY_ENTRY_DEBUG,
            IMAGE_DIRECTORY_ENTRY_ARCHITECTURE,
            IMAGE_DIRECTORY_ENTRY_GLOBALPTR,
            IMAGE_DIRECTORY_ENTRY_TLS,
            IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG,
            IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT,
            IMAGE_DIRECTORY_ENTRY_IAT,
            IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT,
            IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR,
            IMAGE_DIRECTORY_ENTRY_RESERVED,
        )
        return entries[len(self.value)]

    def details(self, **options):
        if self.initializedQ():
            width = max(len(n.classname()) for n in self.value) if self.value else 0
            return '\n'.join('[{:x}] {:>{}}{:4s} {:s}:+{:#x}'.format(n.getoffset(), n.classname(), width, '{%d}'%i, n['Address'].summary(), n['Size'].int()) for i, n in enumerate(self.value))
        return super(DataDirectory,self).details(**options)

    def repr(self, **options):
        return self.details(**options)

