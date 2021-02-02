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

class SCOPETABLE_ENTRY(pstruct.type):
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

class EH4_SCOPETABLE_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'EnclosingLevel'),
        (PVOID, 'FilterFunc'),  #long (*FilterFunc)()
        (PVOID, 'HandlerAddress'),
        #(PVOID, 'FinallyFunc'),
    ]

class EH4_SCOPETABLE(pstruct.type):
    _fields_ = [
        (DWORD, 'GSCookieOffset'),
        (DWORD, 'GSCookieXOROffset'),
        (DWORD, 'EHCookieOffset'),
        (DWORD, 'EHCookieXOROffset'),
        (dyn.array(EH4_SCOPETABLE_RECORD, 0), 'ScopeRecord'),
    ]

class EH3_EXCEPTION_REGISTRATION(pstruct.type):
    _fields_ = [
        (lambda self: pointer(EH3_EXCEPTION_REGISTRATION), 'Next'),
        (PVOID, 'ExceptionHandler'),
        (PSCOPETABLE_ENTRY, 'ScopeTable'),
        (DWORD, 'TryLevel'),
    ]

class EXCEPTION_POINTERS(pstruct.type):
    _fields_ = [
        (PEXCEPTION_RECORD, 'ExceptionRecord'),
        (PCONTEXT, 'ContextRecord'),
    ]

class C_SCOPE_TABLE(pstruct.type):
    _fields_ = [
        (pointer(ptype.undefined, _value_=PVALUE32), 'Begin'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'End'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'Handler'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'Target'),
    ]

class CPPEH_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'old_esp'),
        (dyn.pointer(EXCEPTION_POINTERS), 'exc_ptr'),
        (EH3_EXCEPTION_REGISTRATION, 'registration'),
    ]

class EHRegistrationNode(pstruct.type):
    _fields_ = [
        (lambda self: pointer(EHRegistrationNode), 'pNext'),
        (PVOID, 'frameHandler'),
        (pint.int32_t, 'state'),
    ]

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'toState'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'action'),
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
        (pointer(TypeDescriptor, _value_=PVALUE32), 'pType'),
        (pint.int32_t, 'dispCatchObj'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'addressOfHandler'),
        (pint.int32_t, 'dispFrame'),
    ]

class TryBlockMapEntry(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'tryLow'),
        (pint.int32_t, 'tryHigh'),
        (pint.int32_t, 'catchHigh'),
        (pint.int32_t, 'nCatches'),
        (lambda self: pointer(dyn.array(HandlerType, self['nCatches'].li.int()), _value_=PVALUE32), 'pHandlerArray'),
    ]

class ESTypeList(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'nCount'),
        (lambda self: pointer(dyn.array(HandlerType, self['nCount'].li.int()), _value_=PVALUE32), 'pHandlerArray'),
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
        (lambda self: pointer(dyn.array(CatchableType, self['nCatchableTypes'].li.int()), _value_=PVALUE32), 'arrayOfCatchableTypes'),
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
        (pointer(CatchableTypeArray, _value_=PVALUE32), 'pCatchableTypeArray'),
    ]

class IPtoStateMap(pstruct.type):
    _fields_ = [
        (pointer(ptype.undefined, _value_=PVALUE32), 'pc'),
        (pint.int32_t, 'state'),
    ]

class FuncInfo(pstruct.type):
    class _magicNumber(pbinary.struct):
        # 0x19930520    - pre-vc2005
        # 0x19930521    - pESTypeList is valid
        # 0x19930522    - EHFlags is valid
        _fields_ = [
            (29, 'number'),
            (3, 'bbtFlags'),
        ]
    _fields_ = [
        (_magicNumber, 'magicNumber'),

        (pint.int32_t, 'maxState'),
        (pointer(UnwindMapEntry, _value_=PVALUE32), 'pUnwindMap'),

        (pint.int32_t, 'nTryBlocks'),
        (pointer(TryBlockMapEntry, _value_=PVALUE32), 'pTryBlockMap'),

        (pint.int32_t, 'nIPMapEntries'),
        (pointer(IPtoStateMap, _value_=PVALUE32), 'pIPtoStateMap'),
        (pint.int32_t, 'dispUnwindHelp'),

        (pointer(ESTypeList, _value_=PVALUE32), 'pESTypeList'),
        (pint.int32_t, 'EHFlags'),
    ]

class RUNTIME_FUNCTION(pstruct.type):
    _fields_ = [
        (pointer(ptype.undefined, _value_=PVALUE32), 'BeginAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'EndAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'UnwindInfoAddress'),
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
        (lambda self: pointer(dyn.clone(RTTIBaseClassArray, length=self['numBaseClasses'].li.int())), 'pBaseClassArray'),
    ]

class RTTIBaseClassDescriptor(pstruct.type):
    _fields_= [
        (pointer(TypeDescriptor), 'pTypeDescriptor'),
        (DWORD, 'numContainedBases'),
        (PMD, 'where'),
        (DWORD, 'attributes'),
    ]

class RTTIBaseClassArray(parray.type):
    _object_ = RTTIBaseClassDescriptor

if False:
    class SCOPE_TABLE_AMD64(pstruct.type):
        class _ScopeRecord(pstruct.type):
            _fields_ = [
                (DWORD, 'BeginAddress'),
                (DWORD, 'EndAddress'),
                (DWORD, 'HandlerAddress'),
                (DWORD, 'JumpTarget'),
            ]

        _fields_ = [
            (DWORD, 'Count'),
            (lambda self: dyn.array(self._ScopeRecord, self['Count'].li.int()), 'ScopeRecord'),
        ]

    class GS_HANDLER_DATA(pstruct.type):
        _fields_ = [
            (int, 'CookieOffset'),
            (long, 'AlignedBaseOffset'),
            (long, 'Alignment'),
        ]
