from WinNT import *
import umtypes,pecoff

class LDR_DATA_TABLE_ENTRY(pstruct.type, versioned):
    class SectionPointerUnion(dynamic.union):
        class SectionPointer(pstruct.type):
            _fields_ = [(PVOID, 'SectionPointer'),(ULONG,'CheckSum')]
        _fields_ = [
            (LIST_ENTRY, 'HashLinks'),
            (SectionPointer, 'SectionPointer')
        ]
    class TimeDateStampUnion(dynamic.union):
        _fields_ = [(ULONG, 'TimeDateStamp'), (PVOID, 'LoadedImports')]

    class Flags(pbinary.flags):
        _fields_ = [
            (1, 'LDRP_COMPAT_DATABASE_PROCESSED'),  # 0x80000000
            (1, 'LDRP_MM_LOADED'),                  # 0x40000000
            (1, 'LDRP_NON_PAGED_DEBUG_INFO'),       # 0x20000000
            (1, 'LDRP_REDIRECTED'),                 # 0x10000000
            (1, 'LDRP_ENTRY_NATIVE'),               # 0x08000000
            (1, 'LDRP_DRIVER_DEPENDENT_DLL'),       # 0x04000000
            (1, 'LDRP_IMAGE_VERIFYING'),            # 0x02000000
            (1, 'LDRP_SYSTEM_MAPPED'),              # 0x01000000
            (1, 'LDR_COR_OWNS_UNMAP'),              # 0x00800000
            (1, 'LDRP_COR_IMAGE'),                  # 0x00400000
            (1, 'LDRP_IMAGE_NOT_AT_BASE'),          # 0x00200000
            (1, 'LDRP_DEBUG_SYMBOLS_LOADED'),       # 0x00100000
            (1, 'LDRP_PROCESS_ATTACH_CALLED'),      # 0x00080000
            (1, 'LDRP_DONT_CALL_FOR_THREADS'),      # 0x00040000
            (1, 'LDRP_FAILED_BUILTIN_LOAD'),        # 0x00020000
            (1, 'LDRP_CURRENT_LOAD'),               # 0x00010000
            (1, 'LDRP_ENTRY_INSERTED'),             # 0x00008000
            (1, 'LDRP_ENTRY_PROCESSED'),            # 0x00004000
            (1, 'LDRP_UNLOAD_IN_PROGRESS'),         # 0x00002000
            (1, 'LDRP_LOAD_IN_PROGRESS'),           # 0x00001000
            (9, 'LDRP_RESERVED'),                   # 0x00000??8
            (1, 'LDRP_IMAGE_DLL'),                  # 0x00000004
            (1, 'LDRP_STATIC_LINK'),                # 0x00000002
            (1, 'LDRP_RESERVED'),                   # 0x00000001
        ]

    def __init__(self, **attrs):
        super(LDR_DATA_TABLE_ENTRY, self).__init__(**attrs)
        self._fields_ = f = []
        aligned = dyn.align(8 if getattr(self,'WIN64',False) else 4)

        f.extend([
            (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder, 'InLoadOrderLinks'),
            (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder, 'InMemoryOrderModuleList'),
            (lambda s:_LDR_DATA_TABLE_ENTRY_LIST_InInitializationOrder, 'InInitializationOrderModuleList'),
            (P(pecoff.Executable.File), 'DllBase'),
            (PVOID, 'EntryPoint'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'SizeOfImage'),
            (aligned, 'align(FullDllName)'),
            (umtypes.UNICODE_STRING, 'FullDllName'),
            (umtypes.UNICODE_STRING, 'BaseDllName'),
            (pbinary.littleendian(LDR_DATA_TABLE_ENTRY.Flags), 'Flags'),   # !!!
            (USHORT, 'LoadCount'),
            (USHORT, 'TlsIndex'),

            (LIST_ENTRY, 'HashLinks'),
            #(LDR_DATA_TABLE_ENTRY.SectionPointerUnion, 'SectionPointer/HashLinks'),

            (ULONG, 'TimeDateStamp'),
            (aligned, 'align(EntryPointActivationContext)'),
            #(LDR_DATA_TABLE_ENTRY.TimeDateStampUnion, 'TimeDateStampUnion/LoadedImports'),

            (PVOID, 'EntryPointActivationContext'), # FIXME: P(_ACTIVATION_CONTEXT)
            (PVOID, 'PatchInformation'),
            (LIST_ENTRY, 'ForwarderLinks'),
            (LIST_ENTRY, 'ServiceTagLinks'),
            (LIST_ENTRY, 'StaticLinks'),        # FIXME: points to 0x18/0x30 byte entries in the heap?
            (PVOID, 'ContextInformation'),
            (ULONGLONG if getattr(self,'WIN64',False) else ULONG, 'OriginalBase'),
            (LARGE_INTEGER, 'LoadTime'),
        ])

    def contains(self, address):
        left = self['DllBase'].int()
        right = left + self['SizeOfImage'].int()
        return (address >= left) and (address < right)

## declarations, heh.
class _LDR_DATA_TABLE_ENTRY_LIST(LIST_ENTRY):
    _object_ = P(LDR_DATA_TABLE_ENTRY)

class _LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder(_LDR_DATA_TABLE_ENTRY_LIST): _path_ = ('InLoadOrderLinks',)
class _LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder(_LDR_DATA_TABLE_ENTRY_LIST): _path_ = ('InMemoryOrderModuleList',)
class _LDR_DATA_TABLE_ENTRY_LIST_InInitializationOrder(_LDR_DATA_TABLE_ENTRY_LIST): _path_ = ('InInitializationOrderModuleList',)

class PEB_LDR_DATA(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(PEB_LDR_DATA, self).__init__(**attrs)
        self._fields_ = f = []
        f.extend([
            (ULONG, 'Length'),
            (ULONG, 'Initialized'),
            (PVOID, 'SsHandle'),

            (_LDR_DATA_TABLE_ENTRY_LIST_InLoadOrder, 'InLoadOrderModuleList'),
            (_LDR_DATA_TABLE_ENTRY_LIST_InMemoryOrder, 'InMemoryOrderModuleList'),
            (_LDR_DATA_TABLE_ENTRY_LIST_InInitializationOrder, 'InInitializationOrderModuleList'),

            (PVOID, 'EntryInProgress'),
            (PVOID, 'ShutdownInProgress'),
            (ULONG, 'ShutdownThreadId'),
        ])

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

class PPEB_LDR_DATA(P(PEB_LDR_DATA)): pass

