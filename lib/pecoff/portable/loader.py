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
    _fields_ = [
        (DWORD, 'HeaderSize'),
        (DWORD, 'FixupInfoSize'),
        (ULONGLONG, 'Symbol'),
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

        raise NotImplementedError(version.int())

        # FIXME: Reverse what the 32-bit version of this structure should look like
        #        and more importantly how the size fits into this...
        return IMAGE_DYNAMIC_RELOCATION64_V2

    _fields_ = [
        (DWORD, 'Version'),
        (DWORD, 'Size'),
        (__DynamicRelocations, 'DynamicRelocations'),
    ]

class IMAGE_GUARD_(pbinary.flags):
    _fields_ = [
        (4, 'CF_FUNCTION_TABLE_SIZE'),
        (7, 'unused(7)_28'),
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
    pass

class IMAGE_LOAD_CONFIG_DIRECTORY32(IMAGE_LOAD_CONFIG_DIRECTORY):
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

    _fields_ = [
        (DWORD, 'Size'),
        (TimeDateStamp, 'TimeDateStamp'),
        (WORD, 'MajorVersion'),
        (WORD, 'MinorVersion'),
        (DWORD, 'GlobalFlagsClear'),   # FIXME
        (DWORD, 'GlobalFlagsSet'), # FIXME
        (DWORD, 'CriticalSectionDefaultTimeout'),

        (DWORD, 'DeCommitFreeBlockThreshold'),
        (DWORD, 'DeCommitTotalFreeThreshold'),
        (realaddress(VOID, type=DWORD), 'LockPrefixTable'),     # XXX: NULL-terminated list of VAs
        (DWORD, 'MaximumAllocationSize'),
        (DWORD, 'VirtualMemoryThreshold'),
        (DWORD, 'ProcessAffinityMask'),

        (DWORD, 'ProcessHeapFlags'),   # FIXME: where are these flags at?
        (WORD, 'CSDVersion'),
        (WORD, 'Reserved'),

        (realaddress(VOID, type=DWORD), 'EditList'),    # XXX: also probably a NULL-terminated list of VAs
        (realaddress(DWORD, type=DWORD), 'SecurityCookie'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['SEHandlerCount'].li.int()), type=DWORD), 'SEHandlerTable'),
        (DWORD, 'SEHandlerCount'),

        (realaddress(DWORD, type=DWORD), 'GuardCFCheckFunctionPointer'),
        (realaddress(DWORD, type=DWORD), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardCFFunctionCount'].li.int()), type=DWORD), 'GuardCFFunctionTable'),
        (DWORD, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardAddressTakenIatEntryCount'].li.int()), type=DWORD), 'GuardAddressTakenIatEntryTable'),
        (DWORD, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda self: dyn.array(DWORD, self.parent['GuardLongJumpTargetCount'].li.int()), type=DWORD), 'GuardLongJumpTargetTable'),
        (DWORD, 'GuardLongJumpTargetCount'),

        (realaddress(VOID, type=DWORD), 'DynamicValueRelocTable'),  # XXX: Probably another NULL-terminated list of VAs
        (realaddress(VOID, type=DWORD), 'CHPEMetadataPointer'),     # FIXME
        (realaddress(DWORD, type=DWORD), 'GuardRFFailureRoutine'),
        (realaddress(DWORD, type=DWORD), 'GuardRFFailureRoutineFunctionPointer'),
        (DWORD, 'DynamicValueRelocTableOffset'),   # XXX: depends on DynamicValueRelocTableSection
        (WORD, 'DynamicValueRelocTableSection'),
        (WORD, 'Reserved2'),

        (realaddress(DWORD, type=DWORD), 'GuardRFVerifyStackPointerFunctionPointer'),
        (DWORD, 'HotPatchTableOffset'),
        (realaddress(pstr.wstring, type=DWORD), 'AddressOfSomeUnicodeString'),
        (DWORD, 'Reserved3'),
    ]

class IMAGE_LOAD_CONFIG_DIRECTORY64(IMAGE_LOAD_CONFIG_DIRECTORY):
    _fields_ = [
        (DWORD, 'Size'),
        (TimeDateStamp, 'TimeDateStamp'),
        (WORD, 'MajorVersion'),
        (WORD, 'MinorVersion'),
        (DWORD, 'GlobalFlagsClear'),
        (DWORD, 'GlobalFlagsSet'),
        (DWORD, 'CriticalSectionDefaultTimeout'),

        (ULONGLONG, 'DeCommitFreeBlockThreshold'),
        (ULONGLONG, 'DeCommitTotalFreeThreshold'),
        (realaddress(VOID, type=ULONGLONG), 'LockPrefixTable'),
        (ULONGLONG, 'MaximumAllocationSize'),
        (ULONGLONG, 'VirtualMemoryThreshold'),
        (ULONGLONG, 'ProcessAffinityMask'),

        (DWORD, 'ProcessHeapFlags'),
        (WORD, 'CSDVersion'),
        (WORD, 'Reserved1'),

        (realaddress(VOID, type=ULONGLONG), 'EditList'),
        (realaddress(ULONGLONG, type=ULONGLONG), 'SecurityCookie'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['SEHandlerCount'].li.int()), type=ULONGLONG), 'SEHandlerTable'),
        (ULONGLONG, 'SEHandlerCount'),

        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardCFCheckFunctionPointer'),
        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardCFFunctionCount'].li.int()), type=ULONGLONG), 'GuardCFFunctionTable'),
        (ULONGLONG, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardAddressTakenIatEntryCount'].li.int()), type=ULONGLONG), 'GuardAddressTakenIatEntryTable'),
        (ULONGLONG, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda self: dyn.array(ULONGLONG, self.parent['GuardLongJumpTargetCount'].li.int()), type=ULONGLONG), 'GuardLongJumpTargetTable'),
        (ULONGLONG, 'GuardLongJumpTargetCount'),

        (realaddress(VOID, type=ULONGLONG), 'DynamicValueRelocTable'),
        (realaddress(VOID, type=ULONGLONG), 'CHPEMetadataPointer'),
        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardRFFailureRoutine'),
        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardRFFailureRoutineFunctionPointer'),
        (DWORD, 'DynamicValueRelocTableOffset'),
        (WORD, 'DynamicValueRelocTableSection'),
        (WORD, 'Reserved2'),

        (realaddress(ULONGLONG, type=ULONGLONG), 'GuardRFVerifyStackPointerFunctionPointer'),
        (DWORD, 'HotPatchTableOffset'),
        (DWORD, 'Reserved3'),
        (realaddress(pstr.szwstring, type=ULONGLONG), 'AddressOfSomeUnicodeString'),
    ]
