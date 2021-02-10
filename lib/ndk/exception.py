import ptypes
from ptypes import *
pbinary.setbyteorder(pbinary.littleendian)

from .datatypes import *

class EXCEPTION_FLAGS(pbinary.struct):
    _fields_ = [
        (1,    'NONCONTINUABLE'),
        (1,    'UNWINDING'),
        (1,    'EXIT_UNWIND'),
        (1,    'STACK_INVALID'),
        (1,    'NESTED_CALL'),
        (1,    'TARGET_UNWIND'),
        (1,    'COLLIDED_UNWIND'),
        (1+24, 'unknown'),
    ]

class EXCEPTION_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'ExceptionCode'),
        (EXCEPTION_FLAGS, 'ExceptionFlags'),
        (lambda self: pointer(EXCEPTION_RECORD), 'ExceptionRecord'),
        (PVOID, 'ExceptionAddress'),
        (DWORD, 'NumberParameters'),
        (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(NumberParameters)'),
        (lambda self: dyn.array(ULONG_PTR, self['NumberParameters'].li.int()), 'ExceptionInformation'),
    ]
PEXCEPTION_RECORD = P(EXCEPTION_RECORD)

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
        (unsigned_long, 'EnclosingLevel'),
        (PVOID, 'FilterFunc'),  #long (*FilterFunc)()
        (PVOID, 'HandlerAddress'),
        #(PVOID, 'FinallyFunc'),
    ]

class EH4_SCOPETABLE(pstruct.type):
    _fields_ = [
        (unsigned_long, 'GSCookieOffset'),
        (unsigned_long, 'GSCookieXOROffset'),
        (unsigned_long, 'EHCookieOffset'),
        (unsigned_long, 'EHCookieXOROffset'),
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
        (pointer(ptype.undefined, _value_=PVALUE32), 'BeginAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'EndAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'HandlerAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'JumpTarget'),
    ]

class SCOPE_TABLE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (lambda self: dyn.array(C_SCOPE_TABLE, self['Count'].li.int()), 'ScopeRecord'),
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
        (int, 'state'),
    ]

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (int, 'toState'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'action'),
    ]
    def summary(self):
        return "action={:#x}(toState:{:d})".format(self['action'].int(), self['toState'].int())

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (pointer(pstr.szstring), 'spare'),   # demangled name from type_info::name
        (pstr.szstring, 'name'),
    ]
    def summary(self):
        spare = self['spare']
        try:
            if spare.int():
                demangled = spare.d.li
                return "(VFTable:{:#x}) {:s} ({:s})".format(self['pVFTable'].int(), self['name'].str(), demangled.str())
        except ptypes.error.LoadError:
            pass
        return "(VFTable:{:#x}) {:s}".format(self['pVFTable'].int(), self['name'].str())

class HandlerType(pstruct.type):
    _fields_ = [
        (int, 'adjectives'),
        (pointer(TypeDescriptor, _value_=PVALUE32), 'pType'),
        (int, 'dispCatchObj'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'addressOfHandler'),
        (lambda self: int if getattr(self, 'WIN64', False) else pint.int_t, 'dispFrame'),
    ]
    def summary(self):
        items = []
        if self['adjectives'].int():
            items.append("adjectives:{:#x}".format(self['adjectives'].int()))
        if self['dispCatchObj'].int():
            items.append("dispCatchObj:{:+#x}".format(self['dispCatchObj'].int()))
        if self['dispFrame'].int():
            items.append("dispFrame:{:+#x}".format(self['dispFrame'].int()))
        properties = "({:s})".format(', '.join(items))

        items = []
        items.append("addressOfHandler={!s}".format(self['addressOfHandler'].summary()))
        if self['pType'].int():
            item = self['pType'].d
            try:
                res = item.li
            except ptypes.error.LoadError:
                res = self['pType']
            items.append(res.summary())
        return ' '.join([properties] + items)

class TryBlockMapEntry(pstruct.type):
    class _pHandlerArray(parray.type):
        _object_ = HandlerType
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())

                if item['dispFrame'].int():
                    res = "[{:s}] {:s} adjectives={:#x} dispCatchObj={:+#x} dispFrame={:+#x}".format(position, description, item['adjectives'].int(), item['dispCatchObj'].int(), item['dispFrame'].int())
                else:
                    res = "[{:s}] {:s} adjectives={:#x} dispCatchObj={:+#x}".format(position, description, item['adjectives'].int(), item['dispCatchObj'].int())
                items.append(res)

                name = 'pType'
                field, type = item[name], item[name].d
                try:
                    if not field.int():
                        raise ValueError
                    res = field.d.li
                except (ptypes.error.LoadError, ValueError):
                    res = field
                items.append("[{:s}] {:s} addressOfHandler={:#x} {!s}".format(position, description, item['addressOfHandler'].int(), res.summary()))
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details()
            return self.summary()

    _fields_ = [
        (int, 'tryLow'),
        (int, 'tryHigh'),
        (int, 'catchHigh'),
        (int, 'nCatches'),
        (lambda self: pointer(dyn.clone(self._pHandlerArray, length=self['nCatches'].li.int()), _value_=PVALUE32), 'pHandlerArray'),
    ]
    def summary(self):
        res = self['pHandlerArray'].d
        try:
            res = res.li.summary()
        except ptypes.error.LoadError:
            res = self['pHandlerArray'].summary()
        return "try<{:d},{:d}> catch<{:d}> handler:({:d}) {:s}".format(self['tryLow'].int(), self['tryHigh'].int(), self['catchHigh'].int(), self['nCatches'].int(), res)

class ESTypeList(pstruct.type):
    _fields_ = [
        (int, 'nCount'),
        (lambda self: pointer(dyn.array(HandlerType, self['nCount'].li.int()), _value_=PVALUE32), 'pHandlerArray'),
    ]

class PMD(pstruct.type):
    _fields_ = [
        (int, 'mdisp'), # member displacement -- member within the class that introduces the member
        (int, 'pdisp'), # vbtable displacement -- pointer to the vbtable within the derived class
        (int, 'vdisp'), # vftable displacement -- entry in the vbtable that contains the offset of the occurrence of the introducing class within the derived class
    ]

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (PVOID, 'spare'),
        (pstr.szstring, 'name'),
    ]

class CatchableType(pstruct.type):
    class _properties(pint.enum, unsigned_int):
        _values_ = [
            ('pointer', 1),
        ]
    _fields_ = [
        (_properties, 'properties'),
        (pointer(TypeDescriptor, _value_=PVALUE32), 'pType'),
        (PMD, 'thisDisplacement'),
        (int, 'sizeOrOffset'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'copyFunction'),
    ]

class CatchableTypeArray(pstruct.type):
    _fields_ = [
        (int, 'nCatchableTypes'),
        (lambda self: pointer(dyn.array(CatchableType, self['nCatchableTypes'].li.int()), _value_=PVALUE32), 'arrayOfCatchableTypes'),
    ]

class ThrowInfo(pstruct.type):
    class _attributes(pint.enum, unsigned_int):
        _values_ = [
            ('const', 1),
            ('volatile', 2),
        ]
    _fields_ = [
        (_attributes, 'attributes'),
        (PVOID, 'pmfnUnwind'),
        (PVOID, 'pForwardCompat'),
        (pointer(CatchableTypeArray), 'pCatchableTypeArray'),
    ]

class IPtoStateMap(pstruct.type):
    class _state(pint.enum, int):
        _values_ = [
            ('END', -1),
        ]
    _fields_ = [
        (pointer(ptype.undefined, _value_=PVALUE32), 'pc'),
        (_state, 'state'),
    ]
    def summary(self):
        return "state={:d} pc={!s}".format(self['state'].int(), self['pc'].summary())

class FI_(pbinary.flags):
    _fields_ = [
        (29, 'unused'),
        (1, 'EHNOEXCEPT_FLAG'),
        (1, 'DYNSTKALIGN_FLAG'),
        (1, 'EHS_FLAG'),
    ]

class FuncInfo(pstruct.type, versioned):
    class _magicNumber(pbinary.struct):
        # 0x19930520    - pre-vc2005
        # 0x19930521    - pESTypeList is valid
        # 0x19930522    - EHFlags is valid
        class _bbtFlags(pbinary.enum):
            _width_, _values_ = 3, [
                ('VC6', 0),
                ('VC7', 1), # 7.x (2002-2003)
                ('VC8', 2), # 8 (2005)
            ]
        _fields_ = [
            (29, 'number'),
            (_bbtFlags, 'bbtFlags'),
        ]
    class _pUnwindMap(parray.type):
        _object_ = UnwindMapEntry
        def summary(self):
            items = (item.summary() for item in self)
            return "({:d}) [{:s}]".format(len(self), ', '.join(items))
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())
                items.append("[{:s}] {:s} toState={:d} action={:#x}".format(position, description, item['toState'].int(), item['action'].int()))
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details()
            return super(FuncInfo._pUnwindMap, self).summary()

    class _pTryBlockMap(parray.type):
        _object_ = TryBlockMapEntry
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())
                items.append("[{:s}] {:s} tryLow={:d} tryHigh={:d} catchHigh={:d}".format(position, description, item['tryLow'].int(), item['tryHigh'].int(), item['catchHigh'].int()))

                name = 'pHandlerArray'
                field, handlers = item[name], item[name].d
                try:
                    if not field.int():
                        raise ValueError
                    res = handlers.li
                except (ptypes.error.LoadError, ValueError):
                    res = field
                position = ptypes.utils.repr_position(field.getposition())
                for index, handler in enumerate(handlers):
                    description = ptypes.utils.repr_instance(item.classname(), '.'.join([item.name(), name, "{:d}".format(index)]))
                    items.append("[{:s}] {:s} {!s}".format(position, description, handler.summary()))
                continue
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details() + '\n'
            return self.summary()

    class _pIPtoStateMap(parray.type):
        _object_ = IPtoStateMap
        def summary(self):
            items = ("({:d}) {:#x}".format(item['state'].int(), item['pc'].int()) for item in self)
            return "[{:s}]".format(', '.join(items))
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())
                items.append("[{:s}] {:s} state={:d} pc={:#x}".format(position, description, item['state'].int(), item['pc'].int()))
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details()
            return super(FuncInfo._pIPtoStateMap, self).summary()

    _fields_ = [
        (_magicNumber, 'magicNumber'),

        (int, 'maxState'),
        (lambda self: pointer(dyn.clone(self._pUnwindMap, length=self['maxState'].li.int()), _value_=PVALUE32), 'pUnwindMap'),

        (int, 'nTryBlocks'),
        (lambda self: pointer(dyn.clone(self._pTryBlockMap, length=self['nTryBlocks'].li.int()), _value_=PVALUE32), 'pTryBlockMap'),

        (int, 'nIPMapEntries'),
        (lambda self: pointer(dyn.clone(self._pIPtoStateMap, length=self['nIPMapEntries'].li.int()), _value_=PVALUE32), 'pIPtoStateMap'),
        (lambda self: int if getattr(self, 'WIN64', False) else pint.int_t, 'dispUnwindHelp'),

        (pointer(ESTypeList, _value_=PVALUE32), 'pESTypeList'),
        (FI_, 'EHFlags'),
    ]

class UWOP_(pbinary.enum):
    _width_, _values_ = 4, [
        ('PUSH_NONVOL', 0),
        ('ALLOC_LARGE', 1),
        ('ALLOC_SMALL', 2),
        ('SET_FPREG', 3),
        ('SAVE_NONVOL', 4),
        ('SAVE_NONVOL_FAR', 5),
        ('SAVE_XMM', 6),
        ('SAVE_XMM_FAR', 7),
        ('SAVE_XMM128', 8),
        ('SAVE_XMM128_FAR', 9),
        ('PUSH_MACHFRAME', 10),
    ]

class UNWIND_CODE(pbinary.struct):
    _fields_ = [
        (4, 'operation_info'),
        (UWOP_, 'unwind_operation_code'),
        (8, 'offset_in_prolog'),
    ]

class UNW_FLAG_(pbinary.enum):
    _width_, _values_ = 5, [
        ('NHANDLER', 0),
        ('EHANDLER', 1),
        ('UHANDLER', 2),
        ('FHANDLER', 3),
        ('CHAININFO', 4),
    ]

class UNWIND_INFO(pstruct.type):
    class _VersionFlags(pbinary.struct):
        _fields_ = [
            (UNW_FLAG_, 'Flags'),
            (3, 'Version'),
        ]
    class _Frame(pbinary.struct):
        _fields_ = [
            (4, 'Offset'),
            (4, 'Register'),
        ]
    class _HandlerInfo(pstruct.type):
        _fields_ = [
            (ULONG, 'ExceptionHandler'),
            (ULONG, 'ExceptionData'),
        ]
    def __HandlerInfo(self):
        res = self['VersionFlags'].li
        return self._HandlerInfo if any(res['Flags'][item] for item in ['EHANDLER', 'UHANDLER', 'FHANDLER']) else ptype.undefined
    def __FunctionEntry(self):
        res = self['VersionFlags'].li
        return RUNTIME_FUNCTION if res['Flags']['CHAININFO'] else ptype.undefined
    _fields_ = [
        (_VersionFlags, 'VersionFlags'),
        (BYTE, 'SizeOfProlog'),
        (BYTE, 'CountOfCodes'),
        (_Frame, 'Frame'),
        (lambda self: dyn.array(UNWIND_CODE, self['CountOfCodes'].li.int()), 'UnwindCode'),
        (__HandlerInfo, 'HandlerInfo'),
        (__FunctionEntry, 'FunctionEntry'),
    ]

class RUNTIME_FUNCTION(pstruct.type):
    _fields_ = [
        (pointer(ptype.undefined, _value_=PVALUE32), 'BeginAddress'),
        (pointer(ptype.undefined, _value_=PVALUE32), 'EndAddress'),
        (pointer(UNWIND_INFO, _value_=PVALUE32), 'UnwindInfoAddress'),
    ]
PRUNTIME_FUNCTION = P(RUNTIME_FUNCTION)

class EXCEPTION_ROUTINE(ptype.undefined): pass
PEXCEPTION_ROUTINE = P(EXCEPTION_ROUTINE)

class UNWIND_HISTORY_TABLE_ENTRY(pstruct.type):
    _fields_ = [
        (ULONG64, 'ImageBase'),
        (PRUNTIME_FUNCTION, 'FunctionEntry'),
    ]

class UNWIND_HISTORY_TABLE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (UCHAR, 'Search'),
        (ULONG64, 'LowAddress'),
        (ULONG64, 'HighAddress'),
        (lambda self: dyn.array(UNWIND_HISTORY_TABLE_ENTRY, self['Count'].li.int()), 'Entry'),
    ]
PUNWIND_HISTORY_TABLE = P(UNWIND_HISTORY_TABLE)

class DISPATCHER_CONTEXT(pstruct.type, versioned):
    _fields_ = [
        (ULONG64, 'ControlPc'),
        (ULONG64, 'ImageBase'),
        (PRUNTIME_FUNCTION, 'FunctionEntry'),
        (ULONG64, 'EstablisherFrame'),
        (ULONG64, 'TargetIp'),
        (PCONTEXT, 'ContextRecord'),
        (PEXCEPTION_ROUTINE, 'LanguageHandler'),
        (PVOID, 'HandlerData'),

        (PUNWIND_HISTORY_TABLE, 'HistoryTable'),
        (ULONG, 'ScopeIndex'),
        (ULONG, 'Fill0'),
    ]

# corrected with http://www.geoffchappell.com/studies/msvc/language/predefined/index.htm?tx=12,14

class RTTIBaseClassDescriptor(pstruct.type):
    _fields_= [
        (pointer(TypeDescriptor), 'pTypeDescriptor'),
        (unsigned_long, 'numContainedBases'),
        (PMD, 'where'),
        (unsigned_long, 'attributes'),
    ]

class RTTIBaseClassArray(parray.type):
    _object_ = RTTIBaseClassDescriptor

class RTTIClassHierarchyDescriptor(pstruct.type):
    class _attributes(unsigned_long, pint.enum):
        _values_ = [
            (1, 'multiple'),
            (2, 'virtual'),
        ]
    _fields_ = [
        (unsigned_long, 'signature'),
        (_attributes, 'attributes'),
        (unsigned_long, 'numBaseClasses'),
        (lambda self: pointer(dyn.clone(RTTIBaseClassArray, length=self['numBaseClasses'].li.int())), 'pBaseClassArray'),
    ]

class RTTICompleteObjectLocator(pstruct.type, versioned):
    _fields_ = [
        (unsigned_long, 'signature'),
        (unsigned_long, 'offset'),
        (unsigned_long, 'cdOffset'),
        (pointer(TypeDescriptor), 'pTypeDescriptor'),
        (pointer(RTTIClassHierarchyDescriptor), 'pClassDescriptor'),
    ]

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
