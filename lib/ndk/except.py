import ptypes
from ptypes import *

from .datatypes import *

# from Recon-2012-Skochinsky-Compiler-Internals.pdf

# some more from
# https://github.com/zynamics/rtti-helper-scripts/blob/master/rtti.parser.py
# https://github.com/Fatbag/Niotso/blob/master/Tools/rtti-reader/rtti-reader.cpp

# some c++ stuff is here
# http://www.blackhat.com/presentations/bh-dc-07/Sabanal_Yason/Paper/bh-dc-07-Sabanal_Yason-WP.pdf

class __except_handler3(PVOID): pass
class __except_handler4(PVOID): pass

class PSCOPETABLE_ENTRY(PVOID): pass

class _SCOPETABLE_ENTRY(pstruct.type):
    _fields_ = [
        (DWORD, 'EnclosingLevel'),
        (PVOID, 'FilterFunc'),
        (PVOID, 'HandlerFunc'),
    ]

#struct _EH4_SCOPETABLE_RECORD {
#        DWORD EnclosingLevel;
#        long (*FilterFunc)();
#            union {
#            void (*HandlerAddress)();
#            void (*FinallyFunc)();
#        };
#    };

class _EH4_SCOPETABLE_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'EnclosingLevel'),
        (PVOID, 'FilterFunc'),  #long (*FilterFunc)()
        (PVOID, 'HandlerAddress'),
        #(PVOID, 'FinallyFunc'),
    ]

class _EH4_SCOPETABLE(pstruct.type):
    _fields_ = [
        (DWORD, 'GSCookieOffset'),
        (DWORD, 'GSCookieXOROffset'),
        (DWORD, 'EHCookieOffset'),
        (DWORD, 'EHCookieXOROffset'),
        (dyn.array(_EH4_SCOPETABLE_RECORD, 0), 'ScopeRecord'),
    ]

class _EH3_EXCEPTION_REGISTRATION(pstruct.type):
    _fields_ = [
        (lambda s: pointer(_EH3_EXCEPTION_REGISTRATION), 'Next'),
        (PVOID, 'ExceptionHandler'),
        (PSCOPETABLE_ENTRY, 'ScopeTable'),
        (DWORD, 'TryLevel'),
    ]

class EHRegistrationNode(pstruct.type):
    _fields_ = [
        (lambda s: pointer(EHRegistrationNode), 'pNext'),
        (PVOID, 'frameHandler'),
        (pint.int32_t, 'state'),
    ]

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'toState'),
        (PVOID, 'action'),
    ]

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (PVOID, 'spare'),   # demangled name from type_info::name
        (pstr.szstring, 'name'),
    ]

class HandlerType(pstruct.type):
    _fields_ = [
        (DWORD, 'adjectives'),
        (pointer(TypeDescriptor), 'pType'),
        (pint.int32_t, 'dispCatchObj'),
        (PVOID, 'addressOfHandler'),
    ]

class TryBlockMapEntry(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'tryLow'),
        (pint.int32_t, 'tryHigh'),
        (pint.int32_t, 'catchHigh'),
        (pint.int32_t, 'nCatches'),
        (lambda s: pointer(dyn.array(HandlerType, s['nCatches'].li.int())), 'pHandlerArray'),
    ]

class ESTypeList(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'nCount'),
        (lambda s: pointer(dyn.array(HandlerType, s['nCount'].li.int())), 'pHandlerArray'),
    ]

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (PVOID, 'spare'),
        (pstr.szstring, 'name'),
    ]

class CatchableTypeArray(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'nCatchableTypes'),
        (lambda s: pointer(dyn.array(CatchableType, s['nCatchableTypes'].li.int())), 'arrayOfCatchableTypes'),
    ]

class PMD(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'mdisp'),
        (pint.int32_t, 'pdisp'),
        (pint.int32_t, 'vdisp'),
    ]

class CatchableType(pstruct.type):
    _fields_ = [
        (DWORD, 'properties'),
        (pointer(TypeDescriptor), 'pType'),
        (PMD, 'thisDisplacement'),
        (pint.int32_t, 'sizeOrOffset'),
        (PVOID, 'copyFunction'),
    ]

class ThrowInfo(pstruct.type):
    _fields_ = [
        (DWORD, 'attributes'),
        (PVOID, 'pmfnUnwind'),
        (PVOID, 'pForwardCompat'),
        (pointer(CatchableTypeArray), 'pCatchableTypeArray'),
    ]

class FuncInfo(pstruct.type):
    _fields_ = [
        (dyn.clone(pbinary.struct, _fields_=[(29,'magicNumber'),(3,'bbtFlags')]), 'header'),

        # 0x19930520    - pre-vc2005
        # 0x19930521    - pESTypeList is valid
        # 0x19930522    - EHFlags is valid

        (pint.int32_t, 'maxState'),
        (pointer(UnwindMapEntry), 'pUnwindMap'),

        (pint.uint32_t, 'nTryBlocks'),
        (pointer(TryBlockMapEntry), 'pTryBlockMap'),

        (pint.uint32_t, 'nIPMapEntries'),
        (PVOID, 'pIPtoStateMap'),

        (pointer(ESTypeList), 'pESTypeList'),
        (pint.int32_t, 'EHFlags'),
    ]

class _RUNTIME_FUNCTION(pstruct.type):
    _fields_ = [
        (DWORD, 'BeginAddress'),
        (DWORD, 'EndAddress'),
        (DWORD, 'UnwindInfoAddress'),
    ]

class RTTIClassHierarchyDescriptor(pstruct.type):
    _fields_ = [
        (DWORD, 'address'),
        (DWORD, 'signature'),
        (DWORD, 'attributes'),
        (DWORD, 'BaseClassCount'),
        (DWORD, 'BaseClassListAddress'),
    ]

class RTTICompleteObjectLocator(pstruct.type):
    _fields_ = [
        (DWORD, 'signature'),
        (DWORD, 'offset'),
        (DWORD, 'cdOffset'),
        (pointer(TypeDescriptor), 'pTypeDescriptor'),
        (pointer(RTTIClassHierarchyDescriptor), 'pClassDescriptor'),
    ]

class RTTIClassHierarchyDescriptor(pstruct.type):
    _fields_ = [
        (DWORD, 'signature'),
        (DWORD, 'attributes'),
        (DWORD, 'numBaseClasses'),
        (lambda s: pointer(dyn.clone(RTTIBaseClassArray, length=s['numBaseClasses'].li.int())), 'pBaseClassArray'),
    ]

class RTTIBaseClassArray(parray.type):
    _object_ = RTTIBaseClassDescriptor

class RTTIBaseClassDescriptor(pstruct.type):
    _fields_= [
        (pointer(TypeDescriptor), 'pTypeDescriptor'),
        (DWORD, 'numContainedBases'),
        (PMD, 'where'),
        (DWORD, 'attributes'),
    ]

if False:
    class _SCOPE_TABLE_AMD64(pstruct.type):
        class _ScopeRecord(pstruct.type):
            _fields_ = [
                (DWORD, 'BeginAddress'),
                (DWORD, 'EndAddress'),
                (DWORD, 'HandlerAddress'),
                (DWORD, 'JumpTarget'),
            ]

        _fields_ = [
            (DWORD, 'Count'),
            (lambda s: dyn.array(s._ScopeRecord, s['Count'].li.int()), 'ScopeRecord'),
        ]

    class _GS_HANDLER_DATA(pstruct.type):
        _fields_ = [
            (int, 'CookieOffset'),
            (long, 'AlignedBaseOffset'),
            (long, 'Alignment'),
        ]
