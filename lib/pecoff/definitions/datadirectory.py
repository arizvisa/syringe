import ptypes,headers
from ptypes import pstruct,parray,provider,dyn
from __base__ import *

import exports,relocations,imports,resources

class Entry(pstruct.type):
    _fields_ = [
        (dyn.opointer(lambda s: dyn.clone(s.parent._object_,maxsize=int(s.parent['Size'].load())), headers.RelativeAddress), 'VirtualAddress'),
        (uint32, 'Size')
    ]

    def contains(self, addr):
        '''if an address is within our boundaries'''
        start = int(self['VirtualAddress'])
        end = start + int(self['Size'])
        if (addr >= start) and (addr < end):
            return True
        return False

    def get(self):
        return self['VirtualAddress'].d

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
class Tls(Entry): pass
class LoadConfig(Entry): pass
class BoundImport(Entry): pass
class IAT(Entry): pass
class DelayLoad(Entry): pass
class ComHeader(Entry): pass
class Reserved(Entry): pass

class DataDirectory(parray.type):
    length = 16

    def _object_(self):
        return [
            Export, Import, Resource, Exception, Security, BaseReloc,
            Debug, Architecture, GlobalPtr, Tls, LoadConfig,
            BoundImport, IAT, DelayLoad, ComHeader, Reserved,
            None        # hopefully it dies here since we only know about 16 dirs
        ][len(self.value)]

