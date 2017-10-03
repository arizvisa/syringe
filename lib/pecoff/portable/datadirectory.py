import ptypes
from ptypes import pstruct,parray,ptype,pbinary,pstr,dyn
from ..__base__ import *

from . import exports,relocations,imports,resources,exceptions,clr,loader,headers
from .headers import virtualaddress,realaddress,fileoffset
from .headers import IMAGE_DATA_DIRECTORY

class AddressEntry(IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(virtualaddress)

class OffsetEntry(IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(fileoffset)

class Export(AddressEntry):
    _object_ = exports.IMAGE_EXPORT_DIRECTORY

class Import(AddressEntry):
    _object_ = imports.IMAGE_IMPORT_DIRECTORY

class Resource(AddressEntry):
    #_object_ = resources.IMAGE_RESOURCE_DIRECTORY
    class _object_(resources.IMAGE_RESOURCE_DIRECTORY):
        _fields_ = resources.IMAGE_RESOURCE_DIRECTORY._fields_[:]
        _fields_.append((lambda s: dyn.block(s.blocksize() - (s.value[-1].getoffset()+s.value[-1].blocksize()-s.value[0].getoffset())),'ResourceData'))

class Exception(AddressEntry):
    _object_ = exceptions.IMAGE_EXCEPTION_DIRECTORY

class Security(OffsetEntry):
    class _object_(parray.block):
        _object_ = headers.Certificate

class BaseReloc(AddressEntry):
    _object_ = relocations.IMAGE_BASERELOC_DIRECTORY

class Debug(AddressEntry): pass
class Architecture(AddressEntry): pass
class GlobalPtr(AddressEntry): pass

class IMAGE_TLS_DIRECTORY(pstruct.type):
    _fields_ = [
        (uint32, 'StartAddressOfRawData'),
        (uint32, 'EndAddressOfRawData'),
        (uint32, 'AddressOfIndex'),
        (virtualaddress(dyn.clone(parray.terminated, isTerminator=lambda x:int(x)==0, _object_=uint32), type=uint32), 'AddressOfCallbacks'),
        (uint32, 'SizeOfZeroFill'),
        (uint32, 'Characteristics'),
    ]

class IMAGE_TLS_DIRECTORY64(pstruct.type):
    _fields_ = [
        (uint64, 'StartAddressOfRawData'),
        (uint64, 'EndAddressOfRawData'),
        (uint64, 'AddressOfIndex'),
        (virtualaddress(dyn.clone(parray.terminated, isTerminator=lambda x:int(x)==0, _object_=uint32), type=uint64), 'AddressOfCallbacks'),
        (uint32, 'SizeOfZeroFill'),
        (uint32, 'Characteristics'),
    ]

class Tls(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        return IMAGE_TLS_DIRECTORY64 if res.is64() else IMAGE_TLS_DIRECTORY

class LoadConfig(AddressEntry):
    def _object_(self):
        res = self.getparent(Header)['OptionalHeader'].li
        res = loader.IMAGE_LOADCONFIG_DIRECTORY64 if res.is64() else loader.IMAGE_LOADCONFIG_DIRECTORY
        return dyn.clone(res, blocksize=lambda s, cb=self['Size'].li.int(): cb)

class BoundImport(AddressEntry): pass
class IAT(AddressEntry):
    _object_ = lambda s: IMAGE_IMPORT_ADDRESS_TABLE64 if self.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_ADDRESS_TABLE
class DelayLoad(AddressEntry):
    _object_ = imports.IMAGE_DELAYLOAD_DIRECTORY
class ClrHeader(AddressEntry):
    _object_ = clr.IMAGE_COR20_HEADER
class Reserved(AddressEntry): pass

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
        if isinstance(key, basestring):
            # try and be smart in case user tries to be dumb
            key, res = key.lower(), { k.lower() : v for k, v in DataDirectoryEntry.mapping().iteritems() }
            key = key[:-key.find('table')] if key.endswith('table') else key
            return res[key]
        return key

    def _object_(self):
        entries = (
            Export, Import, Resource, Exception, Security,
            BaseReloc, Debug, Architecture, GlobalPtr,
            Tls, LoadConfig, BoundImport, IAT,
            DelayLoad, ClrHeader, Reserved
        )
        return entries[len(self.value)]

    def details(self, **options):
        if self.initializedQ():
            width = max(len(n.classname()) for n in self.value) if self.value else 0
            return '\n'.join('[{:x}] {:>{}}{:4s} {:s}:+{:#x}'.format(n.getoffset(), n.classname(), width, '{%d}'%i, n['Address'].summary(), n['Size'].int()) for i, n in enumerate(self.value))
        return super(DataDirectory,self).details(**options)

    def repr(self, **options):
        return self.details(**options)

