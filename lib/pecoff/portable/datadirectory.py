import six, ptypes
from ptypes import pstruct,parray,ptype,pbinary,pstr,dyn
from ..headers import *

from . import exports,imports,resources,exceptions,relocations,debug,loader,clr,headers

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
        _fields_ = resources.IMAGE_RESOURCE_DIRECTORY._fields_[:]
        _fields_.append((lambda s: dyn.block(s.blocksize() - (s.value[-1].getoffset()+s.value[-1].blocksize()-s.value[0].getoffset())), 'ResourceData'))

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
        return tls.IMAGE_TLS_DIRECTORY64 if res.is64() else tls.IMAGE_TLS_DIRECTORY

class IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        res = loader.IMAGE_LOADCONFIG_DIRECTORY64 if res.is64() else loader.IMAGE_LOADCONFIG_DIRECTORY
        return dyn.clone(res, blocksize=lambda s, cb=self['Size'].li.int(): cb)

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
        if isinstance(key, six.string_types):
            # try and be smart in case user tries to be dumb
            key, res = key.lower(), { k.lower() : v for k, v in DataDirectoryEntry.mapping().iteritems() }
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

