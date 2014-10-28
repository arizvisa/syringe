import ptypes
from ptypes import pstruct,parray,provider,dyn
from __base__ import *

import exports,relocations,imports,resources,exceptions
from headers import virtualaddress,realaddress,fileoffset

class Entry(pstruct.type):
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

class AddressEntry(Entry):
    _fields_ = [
        (lambda s: virtualaddress(s._object_), 'Address'),
        (uint32, 'Size')
    ]

class OffsetEntry(Entry):
    _fields_ = [
        (lambda s: fileoffset(s._object_), 'Address'),
        (uint32, 'Size')
    ]

class Export(AddressEntry):
    _object_ = exports.IMAGE_EXPORT_DIRECTORY
        
class Import(AddressEntry):
    _object_ = imports.IMAGE_IMPORT_DIRECTORY

class Resource(AddressEntry):
    _object_ = resources.IMAGE_RESOURCE_DIRECTORY

class Exception(AddressEntry):
    _object_ = exceptions.IMAGE_EXCEPTION_DIRECTORY
class Security(OffsetEntry):
    pass
class BaseReloc(AddressEntry):
    _object_ = relocations.IMAGE_BASERELOC_DIRECTORY

class Debug(AddressEntry): pass
class Architecture(AddressEntry): pass
class GlobalPtr(AddressEntry): pass
class Tls(AddressEntry):
    class IMAGE_TLS_DIRECTORY(pstruct.type):
        _fields_ = [
            (uint32, 'Raw Data Start VA'),
            (uint32, 'Raw Data End VA'),
            (uint32, 'Address of Index'),
#            (uint32, 'Address of Callbacks'),
#            (dyn.pointer(dyn.clone(parray.terminated, isTerminator=lambda x:int(x)==0, _object_=uint32)), 'Address of Callbacks'),
            (virtualaddress(dyn.clone(parray.terminated, isTerminator=lambda x:int(x)==0, _object_=uint32)), 'Address of Callbacks'),
            (uint32, 'Size of Zero Fill'),
            (uint32, 'Characteristics'),
        ]

    _object_ = IMAGE_TLS_DIRECTORY

class LoadConfig(AddressEntry):
    # FIXME: The size field in the DataDirectory is used to determine which
    #        IMAGE_LOADCONFIG_DIRECTORY to use.
    #        Determine the different structures that are available, and modify
    #        _object_ to choose the correct one.
    class IMAGE_LOADCONFIG_DIRECTORY(pstruct.type):
        _fields_ = [
            (uint32, 'Characteristics'),
            (TimeDateStamp, 'TimeDateStamp'),
            (uint16, 'MajorVersion'),
            (uint16, 'MinorVersion'),
            (uint32, 'GlobalFlagsClear'),
            (uint32, 'GlobalFlagsSet'),
            (uint32, 'CriticalSectionDefaultTimeout'),
            (uint32, 'DeCommitFreeBlockThreshold'),
            (uint32, 'DeCommitTotalFreeThreshold'),
            (realaddress(uint32), 'LockPrefixTable'),
            (uint32, 'MaximumAllocationSize'),
            (uint32, 'VirtualMemoryThreshold'),
            (uint32, 'ProcessAffinityMask'),
            (uint32, 'ProcessHeapFlags'),
            (uint16, 'CSDVersion'),
            (uint16, 'Reserved'),
            (realaddress(uint32), 'EditList'),
            (realaddress(uint32), 'SecurityCookie'),
#            (virtualaddress(uint32), 'SEHandlerTable'),     # FIXME
            (realaddress(lambda s:dyn.array(uint32, s.parent['SEHandlerCount'].l.int())), 'SEHandlerTable'),
            (uint32, 'SEHandlerCount'),

            (uint32, 'GuardCFCheckFunctionPointer'),
            (uint32, 'Reserved2'),
            (realaddress(lambda s: dyn.array(uint32, s.parent['GuardCFFunctionCount'].l.num())), 'GuardCFFunctionTable'),
            (uint32, 'GuardCFFunctionCount'),
            (uint32, 'GuardFlags'),     # CF_INSTRUMENTED=0x100,CFW_INSTRUMENTED=0x200,CF_FUNCTION_TABLE_PRESENT=0x400
        ]
    _object_ = IMAGE_LOADCONFIG_DIRECTORY

class BoundImport(AddressEntry): pass
class IAT(AddressEntry):
    _object_ = imports.IMAGE_IMPORT_ADDRESS_TABLE
class DelayLoad(AddressEntry):
    _object_ = imports.IMAGE_DELAYLOAD_DIRECTORY_ENTRY
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

