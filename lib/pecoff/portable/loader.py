import ptypes
from ptypes import pstruct,parray,ptype,pbinary,pstr,dyn
from .headers import IMAGE_DATA_DIRECTORY
from ..headers import *

class IMAGE_LOAD_CONFIG_CODE_INTEGRITY(pstruct.type):
    _fields_ = [
        (WORD, 'Flags'),
        (WORD, 'Catalog'),
        (DWORD, 'CatalogOffset'),
        (DWORD, 'Reserved'),
    ]

class IMAGE_DYNAMIC_RELOCATION(pstruct.type):
    _fields_ = [
        (realaddress(VOID, type=DWORD), 'Symbol'),
        (DWORD, 'BaseRelocSize'),
        (lambda self: dyn.blockarray(DWORD, self['BaseRelocSize'].li.int()), 'BaseRelocations'),
    ]
IMAGE_DYNAMIC_RELOCATION32 = IMAGE_DYNAMIC_RELOCATION

class IMAGE_DYNAMIC_RELOCATION64(pstruct.type):
    _fields_ = [
        (realaddress(VOID, type=ULONGLONG), 'Symbol'),
        (DWORD, 'BaseRelocSize'),
        (lambda self: dyn.blockarray(DWORD, self['BaseRelocSize'].li.int()), 'BaseRelocations'),
    ]

class IMAGE_DYNAMIC_RELOCATION64_V2(pstruct.type):
    class _Symbol(pint.enum, ULONGLONG):
        _values_ = [
            ('PROLOGUE', 1),
            ('EPILOGUE', 2),
        ]
    _fields_ = [
        (DWORD, 'HeaderSize'),
        (DWORD, 'FixupInfoSize'),
        (_Symbol, 'Symbol'),
        (DWORD, 'SymbolGroup'),
        (DWORD, 'Flags'),
        (lambda self: dyn.array(BYTE, self['FixupInfoSize'].li.int()), 'FixupInfo'),
    ]

class IMAGE_PROLOGUE_DYNAMIC_RELOCATION_HEADER(pstruct.type):
    _fields_ = [
        (BYTE, 'PrologueByteCount'),
        (lambda self: dyn.array(BYTE, self['PrologueByteCount'].li.int()), 'PrologueBytes'),
    ]

class IMAGE_EPILOGUE_DYNAMIC_RELOCATION_HEADER(pstruct.type):
    class _BranchDescriptors(parray.type):
        _object_ = BYTE
    class _BranchDescriptorBitmap(parray.type):
        _object_ = BYTE
    def __BranchDescriptors(self):
        res = self['BranchDescriptorCount'].li
        return dyn.clone(self._BranchDescriptors, length=res.int())

    def __BranchDescriptorBitmap(self):
        res = self['BranchDescriptorCount'].li
        aligned = (7 + res.int()) & -8
        return dyn.clone(self._BranchDescriptorBitmap, length=aligned // 8)

    _fields_ = [
        (DWORD, 'EpilogueCount'),
        (BYTE, 'EpilogueByteCount'),
        (BYTE, 'BranchDescriptorElementSize'),
        (WORD, 'BranchDescriptorCount'),
        (__BranchDescriptors, 'BranchDescriptors'),
        (__BranchDescriptorBitmap, 'BranchDescriptorBitmap'),
    ]

class IMAGE_DYNAMIC_RELOCATION_TABLE(pstruct.type):
    def __DynamicRelocations(self):
        p, version = self.getparent(IMAGE_LOAD_CONFIG_DIRECTORY), self['Version'].li
        if version.int() < 2:
            if isinstance(p, IMAGE_LOAD_CONFIG_DIRECTORY32):
                t = IMAGE_DYNAMIC_RELOCATION32
            elif isinstance(p, IMAGE_LOAD_CONFIG_DIRECTORY64):
                t = IMAGE_DYNAMIC_RELOCATION64
            else:
                raise TypeError(p)
            return dyn.blockarray(t, self['Size'].li.int())

        # FIXME: Reverse what the 32-bit version of this structure should look like
        #        and more importantly how the size fits into this...
        raise NotImplementedError(version.int())

        return IMAGE_DYNAMIC_RELOCATION64_V2

    _fields_ = [
        (DWORD, 'Version'),
        (DWORD, 'Size'),
        (__DynamicRelocations, 'DynamicRelocations'),
    ]

class CF_FUNCTION_TABLE_SIZE_(pbinary.struct):
    _fields_ = [
        (4, 'SHIFT'),
    ]

class IMAGE_GUARD_(pbinary.flags):
    _fields_ = [
        (CF_FUNCTION_TABLE_SIZE_, 'CF_FUNCTION_TABLE_SIZE_MASK'),
        (7, 'unused(7)_21'),
        (1, 'RETPOLINE_PRESENT'),
        (1, 'RF_STRICT'),
        (1, 'RF_ENABLE'),
        (1, 'RF_INSTRUMENTED'),
        (1, 'CF_LONGJUMP_TABLE_PRESENT'),
        (1, 'CF_ENABLE_EXPORT_SUPPRESSION'),
        (1, 'CF_EXPORT_SUPPRESSION_INFO_PRESENT'),
        (1, 'DELAYLOAD_IAT_IN_ITS_OWN_SECTION'),
        (1, 'PROTECT_DELAYLOAD_IAT'),
        (1, 'SECURITY_COOKIE_UNUSED'),
        (1, 'CF_FUNCTION_TABLE_PRESENT'),
        (1, 'CFW_INSTRUMENTED'),
        (1, 'CF_INSTRUMENTED'),
        (8, 'unused(8)_0'),
    ]

class IMAGE_LOAD_CONFIG_DIRECTORY(pstruct.type):
    # FIXME: The size field in the DataDirectory is used to determine which
    #        IMAGE_LOAD_CONFIG_DIRECTORY to use. Instead we're cheating and
    #        using the size specified in the data-directory entry and a
    #        feature of pstruct.type when defining a custom .blocksize(). A
    #        proper implementation should check the 'Size' field and then
    #        use this to determine which IMAGE_LOAD_CONFIG_DIRECTORY
    #        should be used. Once that's done, then we can define a
    #        sub-object that chooses the correct IMAGE_LOAD_CONFIG_DIRECTORY
    #        to use.
    def blocksize(self):
        # If we're not allocated, then look at our parent directory for that size.
        if not self.value:
            p = self.getparent(IMAGE_DATA_DIRECTORY)
            return p['Size'].int()

        # Otherwise, we're allocated and just need to read our size field.
        return self['Size'].li.int()

class IMAGE_ENCLAVE_IMPORT_MATCH_(pint.enum, DWORD):
    _values_ = [
        ('NONE', 0x00000000),
        ('UNIQUE_ID', 0x00000001),
        ('AUTHOR_ID', 0x00000002),
        ('FAMILY_ID', 0x00000003),
        ('IMAGE_ID', 0x00000004),
    ]

IMAGE_ENCLAVE_SHORT_ID_LENGTH = 16
class IMAGE_ENCLAVE_IMPORT(pstruct.type):
    _fields_ = [
        (IMAGE_ENCLAVE_IMPORT_MATCH_, 'MatchType'),
        (DWORD, 'MinimumSecurityVersion'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'UniqueOrAuthorID'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'FamilyID'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'ImageID'),
        (virtualaddress(pstr.szstring, type=DWORD), 'ImportName'),
        (DWORD, 'Reserved'),
    ]

class IMAGE_ENCLAVE_POLICY_(pint.enum, DWORD):
    _values_ = [
        ('DEBUGGABLE', 1)
    ]

class IMAGE_ENCLAVE_FLAG_(pint.enum, DWORD):
    _values_ = [
        ('PRIMARY_IMAGE', 1),
    ]

class IMAGE_ENCLAVE_CONFIG(pstruct.type):
    def blocksize(self):
        # If we're already loaded, then we can just read our size field. If we're not
        # loaded yet, then to get the size we need to cheat by duplicating the instance,
        # allocating with the original blocksize, and then taking its loaded size.
        Fblocksize = super(IMAGE_ENCLAVE_CONFIG, self).blocksize
        return self['Size'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    def __ImportList(self):
        count, size = (self[fld].li for fld in ['NumberOfImports', 'ImportEntrySize'])

        # FIXME: set the size of IMAGE_ENCLAVE_IMPORT to the ImportEntrySize
        t = dyn.array(IMAGE_ENCLAVE_IMPORT, count.int())
        return virtualaddress(t, type=DWORD)

    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'MinimumRequiredConfigSize'),
        (IMAGE_ENCLAVE_POLICY_, 'PolicyFlags'),
        (DWORD, 'NumberOfImports'),
        (__ImportList, 'ImportList'),
        (DWORD, 'ImportEntrySize'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'FamilyID'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'ImageID'),
        (DWORD, 'ImageVersion'),
        (DWORD, 'SecurityVersion'),
        (DWORD, 'EnclaveSize'),
        (DWORD, 'NumberOfThreads'),
        (IMAGE_ENCLAVE_FLAG_, 'EnclaveFlags'),
    ]

class IMAGE_ENCLAVE_CONFIG64(pstruct.type):
    def blocksize(self):
        # If we're already loaded, then we can just read our size field. If we're not
        # loaded yet, then to get the size we need to cheat by duplicating the instance,
        # allocating with the original blocksize, and then taking its loaded size.
        Fblocksize = super(IMAGE_ENCLAVE_CONFIG64, self).blocksize
        return self['Size'].li.int() if self.value else self.copy(blocksize=Fblocksize).a.size()

    def __ImportList(self):
        count, size = (self[fld].li for fld in ['NumberOfImports', 'ImportEntrySize'])

        # FIXME: set the size of IMAGE_ENCLAVE_IMPORT to the ImportEntrySize
        t = dyn.array(IMAGE_ENCLAVE_IMPORT, count.int())
        return virtualaddress(t, type=DWORD)

    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'MinimumRequiredConfigSize'),
        (IMAGE_ENCLAVE_POLICY_, 'PolicyFlags'),
        (DWORD, 'NumberOfImports'),
        (__ImportList, 'ImportList'),
        (DWORD, 'ImportEntrySize'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'FamilyID'),
        (dyn.array(BYTE, IMAGE_ENCLAVE_SHORT_ID_LENGTH), 'ImageID'),
        (DWORD, 'ImageVersion'),
        (DWORD, 'SecurityVersion'),
        (ULONGLONG, 'EnclaveSize'),
        (DWORD, 'NumberOfThreads'),
        (IMAGE_ENCLAVE_FLAG_, 'EnclaveFlags'),
    ]

class HEAP_(pbinary.flags):
    _fields_ = [
        (1, 'LOCK_USER_ALLOCATED'),         # 0x80000000
        (1, 'VALIDATE_PARAMETERS_ENABLED'), # 0x40000000
        (1, 'VALIDATE_ALL_ENABLED'),        # 0x20000000
        (1, 'SKIP_VALIDATION_CHECKS'),      # 0x10000000
        (1, 'NO_ALIGNMENT'),                # 0x08000000
        (1, 'BREAK_WHEN_OUT_OF_VM'),        # 0x04000000
        (1, 'PROTECTION_ENABLED'),          # 0x02000000
        (1, 'FLAG_PAGE_ALLOCS'),            # 0x01000000
        (4, 'RESERVED_20'),
        (1, 'RESERVED_19'),
        (1, 'CREATE_ENABLE_EXECUTE'),       # 0x00040000
        (1, 'CREATE_ENABLE_TRACING'),       # 0x00020000
        (1, 'CREATE_ALIGN_16'),             # 0x00010000
        (4, 'CLASS_MASK'),                  # 0x0000F000
        (3, 'SETTABLE_USER_FLAGS'),         # 0x00000E00
        (1, 'SETTABLE_USER_VALUE'),         # 0x00000100
        (1, 'DISABLE_COALESCE_ON_FREE'),    # 0x00000080
        (1, 'FREE_CHECKING_ENABLED'),       # 0x00000040
        (1, 'TAIL_CHECKING_ENABLED'),       # 0x00000020
        (1, 'REALLOC_IN_PLACE_ONLY'),       # 0x00000010
        (1, 'ZERO_MEMORY'),                 # 0x00000008
        (1, 'GENERATE_EXCEPTIONS'),         # 0x00000004
        (1, 'GROWABLE'),                    # 0x00000002
        (1, 'NO_SERIALIZE'),                # 0x00000001
    ]

class FLG_(pbinary.flags):
    _fields_ = [
        (1, 'DISABLE_PROTDLLS'),            # 0x80000000
        (1, 'ENABLE_HANDLE_EXCEPTIONS'),    # 0x40000000
        (1, 'STOP_ON_UNHANDLED_EXCEPTION'), # 0x20000000
        (1, 'CRITSEC_EVENT_CREATION'),      # 0x10000000
        (1, 'DISABLE_DBGPRINT'),            # 0x08000000
        (1, 'DEBUG_INITIAL_COMMAND_EX'),    # 0x04000000
        (1, 'HEAP_PAGE_ALLOCS'),            # 0x02000000
        (1, 'ENABLE_HANDLE_TYPE_TAGGING'),  # 0x01000000
        (1, 'ENABLE_EXCEPTION_LOGGING'),    # 0x00800000
        (1, 'ENABLE_CLOSE_EXCEPTIONS'),     # 0x00400000
        (1, 'HEAP_DISABLE_COALESCING'),     # 0x00200000
        (1, 'ENABLE_SYSTEM_CRIT_BREAKS'),   # 0x00100000
        (1, 'DISABLE_PAGE_KERNEL_STACKS'),  # 0x00080000
        (1, 'ENABLE_KDEBUG_SYMBOL_LOAD'),   # 0x00040000
        (1, 'ENABLE_CSRDEBUG'),             # 0x00020000
        (1, 'DISABLE_STACK_EXTENSION'),     # 0x00010000
        (1, 'HEAP_ENABLE_TAG_BY_DLL'),      # 0x00008000
        (1, 'MAINTAIN_OBJECT_TYPELIST'),    # 0x00004000
        (1, 'KERNEL_STACK_TRACE_DB'),       # 0x00002000
        (1, 'USER_STACK_TRACE_DB'),         # 0x00001000
        (1, 'HEAP_ENABLE_TAGGING'),         # 0x00000800
        (1, 'POOL_ENABLE_TAGGING'),         # 0x00000400
        (1, 'MONITOR_SILENT_PROCESS_EXIT'), # 0x00000200
        (1, 'APPLICATION_VERIFIER'),        # 0x00000100
        (1, 'HEAP_VALIDATE_ALL'),           # 0x00000080
        (1, 'HEAP_VALIDATE_PARAMETERS'),    # 0x00000040
        (1, 'HEAP_ENABLE_FREE_CHECK'),      # 0x00000020
        (1, 'HEAP_ENABLE_TAIL_CHECK'),      # 0x00000010
        (1, 'STOP_ON_HUNG_GUI'),            # 0x00000008
        (1, 'DEBUG_INITIAL_COMMAND'),       # 0x00000004
        (1, 'SHOW_LDR_SNAPS'),              # 0x00000002
        (1, 'STOP_ON_EXCEPTION'),           # 0x00000001
    ]

class LOAD_LIBRARY_SEARCH_(pbinary.flags):
    _fields_ = [
        (3, 'Reserved'),
        (1, 'DEFAULT_DIRS'),
        (1, 'SYSTEM32'),
        (1, 'USER_DIRS'),
        (1, 'APPLICATION_DIR'),
        (1, 'DLL_LOAD_DIR'),
        (8, 'LOAD_LIBRARY_FLAGS?'),
    ]

class IMAGE_LOAD_CONFIG_DIRECTORY32(IMAGE_LOAD_CONFIG_DIRECTORY):
    _fields_ = [
        (DWORD, 'Size'),
        (TimeDateStamp, 'TimeDateStamp'),
        (WORD, 'MajorVersion'),
        (WORD, 'MinorVersion'),
        (pbinary.littleendian(FLG_), 'GlobalFlagsClear'),
        (pbinary.littleendian(FLG_), 'GlobalFlagsSet'),
        (DWORD, 'CriticalSectionDefaultTimeout'),

        (DWORD, 'DeCommitFreeBlockThreshold'),
        (DWORD, 'DeCommitTotalFreeThreshold'),
        (realaddress(VOID, type=DWORD), 'LockPrefixTable'),     # XXX: NULL-terminated list of VAs
        (DWORD, 'MaximumAllocationSize'),
        (DWORD, 'VirtualMemoryThreshold'),
        (DWORD, 'ProcessAffinityMask'),

        (pbinary.littleendian(HEAP_), 'ProcessHeapFlags'),      # XXX: maybe its from HeapCreate?
        (WORD, 'CSDVersion'),
        (pbinary.littleendian(LOAD_LIBRARY_SEARCH_), 'DependentLoadFlags'),

        (realaddress(VOID, type=DWORD), 'EditList'),    # XXX: also probably a NULL-terminated list of VAs
        (realaddress(DWORD, type=DWORD), 'SecurityCookie'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['SEHandlerCount'].li.int()), type=DWORD), 'SEHandlerTable'),
        (DWORD, 'SEHandlerCount'),

        (realaddress(realaddress(VOID, type=DWORD), type=DWORD), 'GuardCFCheckFunctionPointer'),
        (realaddress(realaddress(VOID, type=DWORD), type=DWORD), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda self: dyn.array(virtualaddress(VOID, type=DWORD), self.parent['GuardCFFunctionCount'].li.int()), type=DWORD), 'GuardCFFunctionTable'),
        (DWORD, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardAddressTakenIatEntryCount'].li.int()), type=DWORD), 'GuardAddressTakenIatEntryTable'),
        (DWORD, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardLongJumpTargetCount'].li.int()), type=DWORD), 'GuardLongJumpTargetTable'),
        (DWORD, 'GuardLongJumpTargetCount'),

        (realaddress(IMAGE_DYNAMIC_RELOCATION_TABLE, type=DWORD), 'DynamicValueRelocTable'),
        (realaddress(VOID, type=DWORD), 'CHPEMetadataPointer'),     # FIXME
        (realaddress(VOID, type=DWORD), 'GuardRFFailureRoutine'),
        (realaddress(VOID, type=DWORD), 'GuardRFFailureRoutineFunctionPointer'),
        (DWORD, 'DynamicValueRelocTableOffset'),   # XXX: depends on DynamicValueRelocTableSection
        (WORD, 'DynamicValueRelocTableSection'),
        (WORD, 'Reserved2'),

        (realaddress(DWORD, type=DWORD), 'GuardRFVerifyStackPointerFunctionPointer'),
        (DWORD, 'HotPatchTableOffset'),
        (realaddress(pstr.wstring, type=DWORD), 'AddressOfSomeUnicodeString'),
        (DWORD, 'Reserved3'),

        (realaddress(IMAGE_ENCLAVE_CONFIG, type=DWORD), 'EnclaveConfigurationPointer'),
        (realaddress(VOID, type=DWORD), 'VolatileMetadataPointer'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardEHContinuationCount'].li.int()), type=DWORD), 'GuardEHContinuationTable'),
        (DWORD, 'GuardEHContinuationCount'),
        (realaddress(VOID, type=DWORD), 'GuardXFGCheckFunctionPointer'),
        (realaddress(VOID, type=DWORD), 'GuardXFGDispatchFunctionPointer'),
        (realaddress(VOID, type=DWORD), 'GuardXFGTableDispatchFunctionPointer'),
        (DWORD, 'CastGuardOsDeterminedFailureMode'),
    ]

class IMAGE_LOAD_CONFIG_DIRECTORY64(IMAGE_LOAD_CONFIG_DIRECTORY):
    _fields_ = [
        (DWORD, 'Size'),
        (TimeDateStamp, 'TimeDateStamp'),
        (WORD, 'MajorVersion'),
        (WORD, 'MinorVersion'),
        (pbinary.littleendian(FLG_), 'GlobalFlagsClear'),
        (pbinary.littleendian(FLG_), 'GlobalFlagsSet'),
        (DWORD, 'CriticalSectionDefaultTimeout'),

        (ULONGLONG, 'DeCommitFreeBlockThreshold'),
        (ULONGLONG, 'DeCommitTotalFreeThreshold'),
        (realaddress(VOID, type=ULONGLONG), 'LockPrefixTable'),
        (ULONGLONG, 'MaximumAllocationSize'),
        (ULONGLONG, 'VirtualMemoryThreshold'),
        (ULONGLONG, 'ProcessAffinityMask'),

        (pbinary.littleendian(HEAP_), 'ProcessHeapFlags'),      # XXX: maybe its from HeapCreate?
        (WORD, 'CSDVersion'),
        (pbinary.littleendian(LOAD_LIBRARY_SEARCH_), 'DependentLoadFlags'),

        (realaddress(VOID, type=ULONGLONG), 'EditList'),
        (realaddress(ULONGLONG, type=ULONGLONG), 'SecurityCookie'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['SEHandlerCount'].li.int()), type=ULONGLONG), 'SEHandlerTable'),
        (ULONGLONG, 'SEHandlerCount'),

        (realaddress(realaddress(VOID, type=ULONGLONG), type=ULONGLONG), 'GuardCFCheckFunctionPointer'),
        (realaddress(realaddress(VOID, type=ULONGLONG), type=ULONGLONG), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda self: dyn.array(virtualaddress(VOID, type=DWORD), self.parent['GuardCFFunctionCount'].li.int()), type=ULONGLONG), 'GuardCFFunctionTable'),
        (ULONGLONG, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardAddressTakenIatEntryCount'].li.int()), type=ULONGLONG), 'GuardAddressTakenIatEntryTable'),
        (ULONGLONG, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardLongJumpTargetCount'].li.int()), type=ULONGLONG), 'GuardLongJumpTargetTable'),
        (ULONGLONG, 'GuardLongJumpTargetCount'),

        (realaddress(IMAGE_DYNAMIC_RELOCATION_TABLE, type=ULONGLONG), 'DynamicValueRelocTable'),
        (realaddress(VOID, type=ULONGLONG), 'CHPEMetadataPointer'),
        (realaddress(VOID, type=ULONGLONG), 'GuardRFFailureRoutine'),
        (realaddress(VOID, type=ULONGLONG), 'GuardRFFailureRoutineFunctionPointer'),
        (DWORD, 'DynamicValueRelocTableOffset'),
        (WORD, 'DynamicValueRelocTableSection'),
        (WORD, 'Reserved2'),

        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardRFVerifyStackPointerFunctionPointer'),
        (DWORD, 'HotPatchTableOffset'),
        (DWORD, 'Reserved3'),

        (realaddress(IMAGE_ENCLAVE_CONFIG64, type=ULONGLONG), 'EnclaveConfigurationPointer'),
        (realaddress(VOID, type=ULONGLONG), 'VolatileMetadataPointer'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardEHContinuationCount'].li.int()), type=ULONGLONG), 'GuardEHContinuationTable'),
        (ULONGLONG, 'GuardEHContinuationCount'),
        (realaddress(VOID, type=ULONGLONG), 'GuardXFGCheckFunctionPointer'),
        (realaddress(VOID, type=ULONGLONG), 'GuardXFGDispatchFunctionPointer'),
        (realaddress(VOID, type=ULONGLONG), 'GuardXFGTableDispatchFunctionPointer'),
        (ULONGLONG, 'CastGuardOsDeterminedFailureMode'),
    ]
