import ptypes
from ptypes import pstruct,parray,provider,dyn
from ..__base__ import *

from . import exports,relocations,imports,resources,exceptions,headers
from .headers import virtualaddress,realaddress,fileoffset

class Entry(headers.DataDirectoryEntry):
    def _object_(self):
        # called by 'Address'
        sz = self['Size'].num()
        return dyn.block(sz)

    def containsaddress(self, addr):
        '''if an address is within our boundaries'''
        start = self['Address'].num()
        end = start + self['Size'].num()
        if (addr >= start) and (addr < end):
            return True
        return False

    def valid(self):
        return self['Size'].num() != 0

    def __Address(self):
        t = self._object_
        if ptypes.iscontainer(t):
            return self.addressing(dyn.clone(t, blocksize=lambda s: s.getparent(Entry)['Size'].li.num()), type=uint32)
        return self.addressing(t, type=uint32)

    _fields_ = [
        (__Address, 'Address'),
        (uint32, 'Size')
    ]

class AddressEntry(Entry):
    addressing = staticmethod(virtualaddress)

class OffsetEntry(Entry):
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
class Tls(AddressEntry):
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
    def _object_(self):
        opt = self.getparent(Header)['OptionalHeader'].li
        return sself.IMAGE_TLS_DIRECTORY64 if opt.is64() else self.IMAGE_TLS_DIRECTORY

class LoadConfig(AddressEntry):
    # FIXME: The size field in the DataDirectory is used to determine which
    #        IMAGE_LOADCONFIG_DIRECTORY to use.
    #        Determine the different structures that are available, and modify
    #        _object_ to choose the correct one.
    class IMAGE_LOADCONFIG_DIRECTORY(pstruct.type):
        _fields_ = [
            (uint32, 'Size'),
            (TimeDateStamp, 'TimeDateStamp'),
            (uint16, 'MajorVersion'),
            (uint16, 'MinorVersion'),
            (uint32, 'GlobalFlagsClear'),
            (uint32, 'GlobalFlagsSet'),
            (uint32, 'CriticalSectionDefaultTimeout'),

            (uint32, 'DeCommitFreeBlockThreshold'),
            (uint32, 'DeCommitTotalFreeThreshold'),
            (realaddress(uint32, type=uint32), 'LockPrefixTable'),
            (uint32, 'MaximumAllocationSize'),
            (uint32, 'VirtualMemoryThreshold'),
            (uint32, 'ProcessAffinityMask'),

            (uint32, 'ProcessHeapFlags'),
            (uint16, 'CSDVersion'),
            (uint16, 'Reserved'),

            (realaddress(uint32, type=uint32), 'EditList'),
            (realaddress(uint32, type=uint32), 'SecurityCookie'),
            (realaddress(lambda s:dyn.array(uint32, s.parent['SEHandlerCount'].li.int()), type=uint32), 'SEHandlerTable'),
            (uint32, 'SEHandlerCount'),

            (uint32, 'GuardCFCheckFunctionPointer'),
            (uint32, 'Reserved2'),
            (realaddress(lambda s: dyn.array(uint32, s.parent['GuardCFFunctionCount'].li.num()), type=uint32), 'GuardCFFunctionTable'),
            (uint32, 'GuardCFFunctionCount'),
            (uint32, 'GuardFlags'),     # CF_INSTRUMENTED=0x100,CFW_INSTRUMENTED=0x200,CF_FUNCTION_TABLE_PRESENT=0x400
        ]

    class IMAGE_LOADCONFIG_DIRECTORY64(pstruct.type):
        _fields_ = [
            (uint32, 'Size'),
            (TimeDateStamp, 'TimeDateStamp'),
            (uint16, 'MajorVersion'),
            (uint16, 'MinorVersion'),
            (uint32, 'GlobalFlagsClear'),
            (uint32, 'GlobalFlagsSet'),
            (uint32, 'CriticalSectionDefaultTimeout'),

            (uint64, 'DeCommitFreeBlockThreshold'),
            (uint64, 'DeCommitTotalFreeThreshold'),
            (realaddress(uint32, type=uint64), 'LockPrefixTable'),
            (uint64, 'MaximumAllocationSize'),
            (uint64, 'VirtualMemoryThreshold'),
            (uint64, 'ProcessAffinityMask'),

            (uint32, 'ProcessHeapFlags'),
            (uint16, 'CSDVersion'),
            (uint16, 'Reserved'),

            (realaddress(uint32, type=uint64), 'EditList'),
            (realaddress(uint32, type=uint64), 'SecurityCookie'),
            (realaddress(lambda s:dyn.array(uint32, s.parent['SEHandlerCount'].li.int()), type=uint64), 'SEHandlerTable'),
            (uint64, 'SEHandlerCount'),

            (uint32, 'GuardCFCheckFunctionPointer'),
            (uint32, 'Reserved2'),
            (realaddress(lambda s: dyn.array(uint32, s.parent['GuardCFFunctionCount'].li.num()), type=uint64), 'GuardCFFunctionTable'),
            (uint32, 'GuardCFFunctionCount'),
            (uint32, 'GuardFlags'),     # CF_INSTRUMENTED=0x100,CFW_INSTRUMENTED=0x200,CF_FUNCTION_TABLE_PRESENT=0x400
        ]

    def _object_(self):
        opt = self.getparent(Header)['OptionalHeader'].li
        return LoadConfig.IMAGE_LOADCONFIG_DIRECTORY64 if opt.is64() else LoadConfig.IMAGE_LOADCONFIG_DIRECTORY

class BoundImport(AddressEntry): pass
class IAT(AddressEntry):
    _object_ = imports.IMAGE_IMPORT_ADDRESS_TABLE
class DelayLoad(AddressEntry):
    _object_ = imports.IMAGE_DELAYLOAD_DIRECTORY
class ComHeader(AddressEntry): pass
class Reserved(AddressEntry): pass

class DataDirectory(parray.type):
    length = 16

    def _object_(self):
        entries = (
            Export, Import, Resource, Exception, Security,
            BaseReloc, Debug, Architecture, GlobalPtr,
            Tls, LoadConfig, BoundImport, IAT,
            DelayLoad, ComHeader, Reserved
        )
        return entries[len(self.value)]

    def details(self, **options):
        if self.initializedQ():
            width = max(len(n.classname()) for n in self.value)
            return '\n'.join('[{:x}] {:>{}}{:4s} {:s}:+{:#x}'.format(n.getoffset(),n.classname(),width,'{%d}'%i, n['Address'].summary(), n['Size'].num()) for i,n in enumerate(self.value))
        return super(DataDirectory,self).details(**options)

    def repr(self, **options):
        return self.details(**options)

