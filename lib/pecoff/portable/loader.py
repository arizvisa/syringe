import ptypes
from ptypes import pstruct,parray,ptype,pbinary,pstr,dyn
from ..headers import *

class IMAGE_LOAD_CONFIG_CODE_INTEGRITY(pstruct.type):
    _fields_ = [
        (uint16, 'Flags'),
        (uint16, 'Catalog'),
        (uint32, 'CatalogOffset'),
        (uint32, 'Reserved'),
    ]

class IMAGE_DYNAMIC_RELOCATION(pstruct.type):
    _fields_ = [
        (uint32, 'Symbol'),
        (uint32, 'BaseRelocSize'),
        (lambda s: dyn.blockarray(uint32, s['BaseRelocSize'].li.int()), 'BaseRelocations'),
    ]

class IMAGE_DYNAMIC_RELOCATION64(pstruct.type):
    _fields_ = [
        (uint32, 'HeaderSize'),
        (uint32, 'FixupInfoSize'),
        (uint64, 'Symbol'),
        (uint32, 'SymbolGroup'),
        (uint32, 'Flags'),
        (lambda s: dyn.block(s['FixupInfoSize'].li.int()), 'FixupInfo'),
    ]

class IMAGE_PROLOGUE_DYNAMIC_RELOCATION_HEADER(pstruct.type):
    _fields_ = [
        (uint8, 'PrologueByteCount'),
        (lambda s: dyn.block(s['PrologueByteCount'].li.int()), 'PrologueBytes'),
    ]

class IMAGE_EPILOGUE_DYNAMIC_RELOCATION_HEADER(pstruct.type):
    _fields_ = [
        (uint32, 'EpilogueCount'),
        (uint8, 'EpilogueByteCount'),
        (uint8, 'BranchDescriptorElementSize'),
        (uint16, 'BranchDescriptorCount'),
        (lambda s: dyn.block(s['BranchDescriptorCount'].li.int()), 'BranchDescriptors'),
        (lambda s: dyn.block(((s['BranchDescriptorCount'].li.int()+7) & -8) // 8), 'BranchDescriptorBitmap'),
    ]

class IMAGE_DYNAMIC_RELOCATION_TABLE(pstruct.type):
    def __DynamicRelocations(self):
        # FIXME: figure out how to determine the type and size properly
        t = IMAGE_DYNAMIC_RELOCATION
        return dyn.blockarray(t, self['Size'].li.int())

    # FIXME: use the version to determine how this structure looks
    _fields_ = [
        (uint32, 'Version'),
        (uint32, 'Size'),
        (__DynamicRelocations, 'DynamicRelocations'),
    ]

class IMAGE_GUARD_(pbinary.flags):
    _fields_ = [
        (4, 'FUNCTION_TABLE_SIZE'),
        (8, 'unused(8)_28'),
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

class IMAGE_LOADCONFIG_DIRECTORY(pstruct.type):
    # FIXME: The size field in the DataDirectory is used to determine which
    #        IMAGE_LOADCONFIG_DIRECTORY to use. Instead we're cheating and
    #        using the size specified in the data-directory entry and a
    #        feature of pstruct.type when defining a custom .blocksize(). A
    #        proper implementation should check the 'Size' field and then
    #        use this to determine which IMAGE_LOADCONFIG_DIRECTORY
    #        should be used. Once that's done, then we can define a
    #        sub-object that chooses the correct IMAGE_LOADCONFIG_DIRECTORY
    #        to use.

    _fields_ = [
        (uint32, 'Size'),
        (TimeDateStamp, 'TimeDateStamp'),
        (uint16, 'MajorVersion'),
        (uint16, 'MinorVersion'),
        (uint32, 'GlobalFlagsClear'),   # FIXME
        (uint32, 'GlobalFlagsSet'), # FIXME
        (uint32, 'CriticalSectionDefaultTimeout'),

        (uint32, 'DeCommitFreeBlockThreshold'),
        (uint32, 'DeCommitTotalFreeThreshold'),
        (realaddress(ptype.undefined, type=uint32), 'LockPrefixTable'),     # XXX: NULL-terminated list of VAs
        (uint32, 'MaximumAllocationSize'),
        (uint32, 'VirtualMemoryThreshold'),
        (uint32, 'ProcessAffinityMask'),

        (uint32, 'ProcessHeapFlags'),   # FIXME: where are these flags at?
        (uint16, 'CSDVersion'),
        (uint16, 'Reserved'),

        (realaddress(ptype.undefined, type=uint32), 'EditList'),    # XXX: also probably a NULL-terminated list of VAs
        (realaddress(uint32, type=uint32), 'SecurityCookie'),
        (realaddress(lambda s:dyn.array(uint32, s.parent['SEHandlerCount'].li.int()), type=uint32), 'SEHandlerTable'),
        (uint32, 'SEHandlerCount'),

        (realaddress(uint32, type=uint32), 'GuardCFCheckFunctionPointer'),
        (realaddress(uint32, type=uint32), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda s: dyn.array(uint32, s.parent['GuardCFFunctionCount'].li.int()), type=uint32), 'GuardCFFunctionTable'),
        (uint32, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda s: dyn.array(uint32, s.parent['GuardAddressTakenIatEntryCount'].li.int()), type=uint32), 'GuardAddressTakenIatEntryTable'),
        (uint32, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda s: dyn.array(uint32, s.parent['GuardLongJumpTargetCount'].li.int()), type=uint32), 'GuardLongJumpTargetTable'),
        (uint32, 'GuardLongJumpTargetCount'),

        (realaddress(ptype.undefined, type=uint32), 'DynamicValueRelocTable'),  # XXX: Probably another NULL-terminated list of VAs
        (realaddress(ptype.undefined, type=uint32), 'CHPEMetadataPointer'),     # FIXME
        (realaddress(uint32, type=uint32), 'GuardRFFailureRoutine'),
        (realaddress(uint32, type=uint32), 'GuardRFFailureRoutineFunctionPointer'),
        (uint32, 'DynamicValueRelocTableOffset'),   # XXX: depends on DynamicValueRelocTableSection
        (uint16, 'DynamicValueRelocTableSection'),
        (uint16, 'Reserved2'),

        (realaddress(uint32, type=uint32), 'GuardRFVerifyStackPointerFunctionPointer'),
        (uint32, 'HotPatchTableOffset'),
        (realaddress(pstr.wstring, type=uint32), 'AddressOfSomeUnicodeString'),
        (uint32, 'Reserved3'),
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
        (realaddress(ptype.undefined, type=uint64), 'LockPrefixTable'),
        (uint64, 'MaximumAllocationSize'),
        (uint64, 'VirtualMemoryThreshold'),
        (uint64, 'ProcessAffinityMask'),

        (uint32, 'ProcessHeapFlags'),
        (uint16, 'CSDVersion'),
        (uint16, 'Reserved1'),

        (realaddress(ptype.undefined, type=uint64), 'EditList'),
        (realaddress(uint64, type=uint64), 'SecurityCookie'),
        (realaddress(lambda s:dyn.array(uint64, s.parent['SEHandlerCount'].li.int()), type=uint64), 'SEHandlerTable'),
        (uint64, 'SEHandlerCount'),

        (realaddress(uint64, type=uint64), 'GuardCFCheckFunctionPointer'),
        (realaddress(uint64, type=uint64), 'GuardCFDispatchFunctionPointer'),
        (realaddress(lambda s: dyn.array(uint64, s.parent['GuardCFFunctionCount'].li.int()), type=uint64), 'GuardCFFunctionTable'),
        (uint64, 'GuardCFFunctionCount'),
        (pbinary.littleendian(IMAGE_GUARD_), 'GuardFlags'),

        (IMAGE_LOAD_CONFIG_CODE_INTEGRITY, 'CodeIntegrity'),
        (realaddress(lambda s: dyn.array(uint64, s.parent['GuardAddressTakenIatEntryCount'].li.int()), type=uint64), 'GuardAddressTakenIatEntryTable'),
        (uint64, 'GuardAddressTakenIatEntryCount'),
        (realaddress(lambda s: dyn.array(uint64, s.parent['GuardLongJumpTargetCount'].li.int()), type=uint64), 'GuardLongJumpTargetTable'),
        (uint64, 'GuardLongJumpTargetCount'),

        (realaddress(ptype.undefined, type=uint64), 'DynamicValueRelocTable'),
        (realaddress(ptype.undefined, type=uint64), 'CHPEMetadataPointer'),
        (realaddress(uint64, type=uint64), 'GuardRFFailureRoutine'),
        (realaddress(uint64, type=uint64), 'GuardRFFailureRoutineFunctionPointer'),
        (uint32, 'DynamicValueRelocTableOffset'),
        (uint16, 'DynamicValueRelocTableSection'),
        (uint16, 'Reserved2'),

        (realaddress(uint64, type=uint64), 'GuardRFVerifyStackPointerFunctionPointer'),
        (uint32, 'HotPatchTableOffset'),
        (uint32, 'Reserved3'),
        (realaddress(pstr.szwstring, type=uint64), 'AddressOfSomeUnicodeString'),
    ]

