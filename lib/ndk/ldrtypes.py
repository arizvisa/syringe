from WinNT import *
from umtypes import *

## XXX: It would be worth it to do the Loader Data Table Entry Flags

## declarations, heh. 
class LDR_DATA_TABLE_ENTRY(pstruct.type): pass
class _LDR_DATA_TABLE_ENTRY_LIST(dyn.clone(LIST_ENTRY, _object_=lambda s:LDR_DATA_TABLE_ENTRY)):
    LinkHeader = None
    def walk(self, direction='Flink'):
        nextentry = self[direction]
        while (int(nextentry.load()) != 0):
            res = nextentry.dereference()
            if int(res.load()['DllBase']) == 0:
                break

            yield res

            nextentry = res[self.LinkHeader][direction]
            if int(nextentry) == self.getoffset():
                break
            continue
        return

    def moonwalk(self):
        return self.walk('Blink')

class _LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder(_LDR_DATA_TABLE_ENTRY_LIST): LinkHeader = 'InLoadOrderLinks'
class _LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder(_LDR_DATA_TABLE_ENTRY_LIST): LinkHeader = 'InMemoryOrderModuleList'
class _LDR_DATA_TABLE_ENTRY_LIST_InInitializationOrder(_LDR_DATA_TABLE_ENTRY_LIST): LinkHeader = 'InInitializationOrderModuleList'

class PEB_LDR_DATA(pstruct.type):
    _fields_ = [
        (ULONG, 'Length'),
        (BOOLEAN, 'Initialized'),
        (PVOID, 'SsHandle'),
        (_LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder, 'InLoadOrderModuleList'),
        (_LDR_DATA_TABLE_ENTRY_LIST, 'InMemoryOrderModuleList'),
        (_LDR_DATA_TABLE_ENTRY_LIST, 'InInitializationOrderModuleList'),
        (PVOID, 'EntryInProgress'),
    ]
    def walk(self):
        for x in self['InLoadOrderModuleList'].walk():
            yield x
        return
class PPEB_LDR_DATA(dyn.pointer(PEB_LDR_DATA)): pass

import pecoff
class LDR_DATA_TABLE_ENTRY(pstruct.type):
    class SectionPointerUnion(dyn.union):
        _fields_ = [(LIST_ENTRY, 'HashLinks'), (PVOID, 'SectionPointer')]
    class TimeDateStampUnion(dyn.union):
        _fields_ = [(ULONG, 'TimeDateStamp'), (PVOID, 'LoadedImports')]

    class __SectionPointerUnion(dyn.union):
        _fields_ = [(LIST_ENTRY, 'HashLinks'), (PVOID, 'SectionPointer')]
    class __TimeDateStampUnion(dyn.union):
        _fields_ = [(ULONG, 'TimeDateStamp'), (PVOID, 'LoadedImports')]

    _fields_ = [
        (_LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder, 'InLoadOrderLinks'),
        (_LDR_DATA_TABLE_ENTRY_LIST, 'InMemoryOrderModuleList'),
        (_LDR_DATA_TABLE_ENTRY_LIST, 'InInitializationOrderModuleList'),
        #(PVOID, 'DllBase'),
        (dyn.pointer(pecoff.Executable.File), 'DllBase'),   # !!!
        (PVOID, 'EntryPoint'),
        (ULONG, 'SizeOfImage'),
        (UNICODE_STRING, 'FullDllName'),
        (UNICODE_STRING, 'BaseDllName'),
        (ULONG, 'Flags'),
        (USHORT, 'LoadCount'),
        (USHORT, 'TlsIndex'),
        (__SectionPointerUnion, 'SectionPointerUnion'),
        (ULONG, 'CheckSum'),
        (__TimeDateStampUnion, 'TimeDateStampUnion'),
        (PVOID, 'EntryPointActivationContext'),
        (PVOID, 'PatchInformation'),
    ]
