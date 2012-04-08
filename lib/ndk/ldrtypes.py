from WinNT import *
from umtypes import *

## XXX: It would be worth it to do the Loader Data Table Entry Flags

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

    class __Flags(pbinary.struct):
        _fields_ = list(reversed([
            (1, 'LDRP_RESERVED'),   # 0x00000001
            (1, 'LDRP_STATIC_LINK'),    # 0x00000002
            (1, 'LDRP_IMAGE_DLL'),  # 0x00000004
            (1, 'LDRP_LOAD_IN_PROGRESS'),   # 0x00001000
            (1, 'LDRP_UNLOAD_IN_PROGRESS'), # 0x00002000
            (1, 'LDRP_ENTRY_PROCESSED'),    # 0x00004000
            (1, 'LDRP_ENTRY_INSERTED'), # 0x00008000
            (1, 'LDRP_CURRENT_LOAD'),   # 0x00010000
            (1, 'LDRP_FAILED_BUILTIN_LOAD'),    # 0x00020000
            (1, 'LDRP_DONT_CALL_FOR_THREADS'),  # 0x00040000
            (1, 'LDRP_PROCESS_ATTACH_CALLED'),  # 0x00080000
            (1, 'LDRP_DEBUG_SYMBOLS_LOADED'),   # 0x00100000
            (1, 'LDRP_IMAGE_NOT_AT_BASE'),  # 0x00200000
            (1, 'LDRP_COR_IMAGE'),  # 0x00400000
            (1, 'LDR_COR_OWNS_UNMAP'),  # 0x00800000
            (1, 'LDRP_SYSTEM_MAPPED'),  # 0x01000000
            (1, 'LDRP_IMAGE_VERIFYING'),    # 0x02000000
            (1, 'LDRP_DRIVER_DEPENDENT_DLL'),   # 0x04000000
            (1, 'LDRP_ENTRY_NATIVE'),   # 0x08000000
            (1, 'LDRP_REDIRECTED'), # 0x10000000
            (1, 'LDRP_NON_PAGED_DEBUG_INFO'),   # 0x20000000
            (1, 'LDRP_MM_LOADED'),  # 0x40000000
            (1, 'LDRP_COMPAT_DATABASE_PROCESSED'),  # 0x80000000
        ]))

    _fields_ = [
        (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder, 'InLoadOrderLinks'),
        (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder, 'InMemoryOrderModuleList'),
        (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InInitializationOrder, 'InInitializationOrderModuleList'),
        #(PVOID, 'DllBase'),
        (dyn.pointer(pecoff.Executable.File), 'DllBase'),   # !!!
        (PVOID, 'EntryPoint'),
        (ULONG, 'SizeOfImage'),
        (UNICODE_STRING, 'FullDllName'),
        (UNICODE_STRING, 'BaseDllName'),
#        (ULONG, 'Flags'),   # !!!
        (__Flags, 'Flags'),   # !!!
        (USHORT, 'LoadCount'),
        (USHORT, 'TlsIndex'),
        (__SectionPointerUnion, 'SectionPointerUnion'),
        (ULONG, 'CheckSum'),
        (__TimeDateStampUnion, 'TimeDateStampUnion'),
        (PVOID, 'EntryPointActivationContext'),
        (PVOID, 'PatchInformation'),
    ]

    def contains(self, address):
        left = self['DllBase'].long()
        right = left + self['SizeOfImage'].long()
        return (address >= left) and (address < right)

## declarations, heh. 
class _LDR_DATA_TABLE_ENTRY_LIST(dyn.clone(LIST_ENTRY, _object_=LDR_DATA_TABLE_ENTRY)):
    LinkHeader = None
    def walk(self, direction='Flink'):
        nextentry = self[direction]
        while (nextentry.load().int() != 0):
            res = nextentry.dereference()
            if res.load()['DllBase'].int() == 0:
                break

            yield res

            nextentry = res[self.LinkHeader][direction]
            if nextentry.int() == self.getoffset():
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
        (_LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder, 'InMemoryOrderModuleList'),

        (PVOID, 'EntryInProgress'),
    ]
    def walk(self):
        for x in self['InLoadOrderModuleList'].walk():
            yield x
        return

    def search(self, string):
        for x in self.walk():
            if string == x['FullDllName'].str():
                return x
            continue
        raise KeyError

class PPEB_LDR_DATA(dyn.pointer(PEB_LDR_DATA)): pass

