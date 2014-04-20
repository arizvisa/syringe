import ptypes
from ptypes import pstruct,parray,provider,dyn
from __base__ import *

import exports,relocations,imports,resources
from headers import virtualaddress,realaddress

class Entry(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda s: dyn.clone(s.parent._object_,maxsize=int(s.parent['Size'].load()))), 'VirtualAddress'),
        (uint32, 'Size')
    ]

    def containsaddress(self, addr):
        '''if an address is within our boundaries'''
        start = int(self['VirtualAddress'])
        end = start + int(self['Size'])
        if (addr >= start) and (addr < end):
            return True
        return False

    def valid(self):
        return bool(int(self['Size']) != 0)

class Export(Entry):
    _object_ = exports.IMAGE_EXPORT_DIRECTORY
        
class Import(Entry):
    _object_ = imports.IMAGE_IMPORT_DIRECTORY

class Resource(Entry):
    _object_ = resources.IMAGE_RESOURCE_DIRECTORY

class Exception(Entry): pass
class Security(Entry): pass
class BaseReloc(Entry):
    _object_ = relocations.IMAGE_BASERELOC_DIRECTORY

class Debug(Entry): pass
class Architecture(Entry): pass
class GlobalPtr(Entry): pass
class Tls(Entry):
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

class LoadConfig(Entry):
    # FIXME: in some dlls this table has been incorrect
    class IMAGE_LOADCONFIG_DIRECTORY(pstruct.type):
        _fields_ = [
            (uint32, 'Characteristics'),
            (uint32, 'TimeDateStamp'),
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
            (realaddress(uint32), 'EditList'),           # FIXME
            (realaddress(uint32), 'SecurityCookie'),
#            (virtualaddress(uint32), 'SEHandlerTable'),     # FIXME
            (realaddress(lambda s:dyn.array(uint32, s.parent['SEHandlerCount'].l.int())), 'SEHandlerTable'),     # FIXME
            (uint32, 'SEHandlerCount'),

            (uint32, 'GuardCFCheckFunctionPointer'),
            (uint32, 'Reserved2'),
            (realaddress(lambda s: dyn.array(uint32, s.parent['GuardCFFunctionCount'].l.num())), 'GuardCFFunctionTable'),
            (uint32, 'GuardCFFunctionCount'),
            (uint32, 'GuardFlags'),     # CF_INSTRUMENTED=0x100,CFW_INSTRUMENTED=0x200,CF_FUNCTION_TABLE_PRESENT=0x400
        ]
    _object_ = IMAGE_LOADCONFIG_DIRECTORY

class BoundImport(Entry): pass
class IAT(Entry):
    _object_ = imports.IMAGE_IMPORT_ADDRESS_TABLE
class DelayLoad(Entry): pass
class ComHeader(Entry): pass
class Reserved(Entry): pass

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

