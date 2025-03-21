import ptypes
from ptypes import *

from .datatypes import *

class PTR(opointer_t):
    pass

def P32(target):
    def Fbaseaddress(self, offset):
        shift = 31
        mask = pow(2, 64 - shift) - 1
        if offset and getattr(self, 'WIN64', 0):
            baseaddress = self.getoffset() & (mask * pow(2, shift))
            return baseaddress + offset
        return offset
    return dyn.clone(PTR, _calculate_=Fbaseaddress, _object_=target, _value_=ptr32)

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (int, 'toState'),
        (P32(VOID), 'action'),
    ]
    def summary(self):
        return "action={:#x}(toState:{:d})".format(self['action'].d.getoffset(), self['toState'].int())

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (P(pstr.szstring), 'spare'),   # demangled name from type_info::name
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

@pbinary.littleendian
class HT_(pbinary.flags):
    '''unsigned_int'''
    _fields_ = [
        (1, 'IsComplusEh'),         # Is handling within complus eh.
        (23, 'reserved'),
        (1, 'IsBadAllocCompat'),    # the WinRT type can catch a std::bad_alloc
        (1, 'IsStdDotDot'),         # the catch is std C++ catch(...) which is suppose to catch only C++ exception.
        (1, 'unknown'),
        (1, 'IsResumable'),         # the catch may choose to resume (reserved)
        (1, 'IsReference'),         # catch type is by reference
        (1, 'IsUnaligned'),         # type referenced is 'unaligned' qualified
        (1, 'IsVolatile'),          # type referenced is 'volatile' qualified
        (1, 'IsConst'),             # type referenced is 'const' qualified
    ]

class HandlerType(pstruct.type):
    def __dispFrame(self):
        if getattr(self, 'WIN64', False):
            return int
        return pint.int_t
    _fields_ = [
        (HT_, 'adjectives'),
        (P32(TypeDescriptor), 'pType'),
        (int, 'dispCatchObj'),
        (P32(VOID), 'addressOfHandler'),
        (__dispFrame, 'dispFrame'),
    ]
    def summary(self):
        items = []
        if self['adjectives'].int():
            item = self['adjectives']
            iterable = (fld if item[fld] in {1} else "{:s}={:#x}".format(fld, item[fld]) for fld in item if item[fld])
            items.append("adjectives:{:s}".format('|'.join(iterable) or "{:#x}".format(item.int())))
        if self['dispCatchObj'].int():
            items.append("dispCatchObj:{:+#x}".format(self['dispCatchObj'].int()))
        if self['dispFrame'].size() and self['dispFrame'].int():
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
_s_HandlerType = HandlerType

class TryBlockMapEntry(pstruct.type):
    class _pHandlerArray(parray.type):
        _object_ = HandlerType
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())

                res = item['adjectives']
                iterable = (fld if res[fld] in {1} else "{:s}={:#x}".format(fld, res[fld]) for fld in res if res[fld])
                adjectives = '|'.join(iterable) or "{:#x}".format(res.int())

                if item['dispFrame'].int():
                    res = "[{:s}] {:s} dispCatchObj={:+#x} dispFrame={:+#x} addressOfHandler={:#x} adjectives={:s}".format(position, description, item['dispCatchObj'].int(), item['dispFrame'].int(), item['addressOfHandler'].int(), adjectives)
                else:
                    res = "[{:s}] {:s} dispCatchObj={:+#x} addressOfHandler={:#x} adjectives={:s}".format(position, description, item['dispCatchObj'].int(), item['addressOfHandler'].int(), adjectives)
                items.append(res)

                name = 'pType'
                field = item[name]
                try:
                    if not field.int():
                        raise ValueError
                    type = field.d.li
                except (ptypes.error.LoadError, ValueError):
                    type = field
                items.append("[{:s}] {:s} addressOfHandler={:#x} {!s}".format(position, description, item['addressOfHandler'].d.getoffset(), type.summary()))
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details() + '\n'
            return self.summary()

    _fields_ = [
        (int, 'tryLow'),
        (int, 'tryHigh'),
        (int, 'catchHigh'),
        (int, 'nCatches'),
        (lambda self: P32(dyn.clone(self._pHandlerArray, length=self['nCatches'].li.int())), 'pHandlerArray'),
    ]
    def summary(self):
        res = self['pHandlerArray'].d
        try:
            res = res.li.summary()
        except ptypes.error.LoadError:
            res = self['pHandlerArray'].summary()
        return "try<{:d},{:d}> catch<{:d}> handler:({:d}) {:s}".format(self['tryLow'].int(), self['tryHigh'].int(), self['catchHigh'].int(), self['nCatches'].int(), res)

class IPtoStateMap(pstruct.type):
    class _state(pint.enum, int):
        _values_ = [
            ('END', -1),
        ]
    _fields_ = [
        (P32(VOID), 'pc'),
        (_state, 'state'),
    ]
    def summary(self):
        return "state={:d} pc={!s}".format(self['state'].int(), self['pc'].summary())

class ESTypeList(pstruct.type):
    _fields_ = [
        (int, 'nCount'),
        (lambda self: P32(dyn.array(HandlerType, self['nCount'].li.int())), 'pHandlerArray'),
    ]

@pbinary.littleendian
class FI_(pbinary.flags):
    _fields_ = [
        (29, 'unused'),
        (1, 'EHNOEXCEPT_FLAG'),
        (1, 'DYNSTKALIGN_FLAG'),
        (1, 'EHS_FLAG'),
    ]

class FuncInfo(pstruct.type, versioned):
    @pbinary.littleendian
    class _magicNumber(pbinary.struct):
        # 0x19930520    - pre-vc2005
        # 0x19930521    - pESTypeList is valid
        # 0x19930522    - EHFlags is valid
        class _bbtFlags(pbinary.enum):
            length, _values_ = 3, [
                ('VC6', 0),
                ('VC7', 1), # 7.x (2002-2003)
                ('VC8', 2), # 8 (2005)
            ]
        _fields_ = [
            (29, 'magicNumber'),
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
                return self.details() + '\n'
            return super(FuncInfo._pUnwindMap, self).summary()

    class _pTryBlockMap(parray.type):
        _object_ = TryBlockMapEntry
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())
                items.append("[{:s}] {:s} tryLow={:d} tryHigh={:d} catchHigh={:d} nCatches={:d} pHandlerArray={:#x}".format(position, description, item['tryLow'].int(), item['tryHigh'].int(), item['catchHigh'].int(), item['nCatches'].int(), item['pHandlerArray'].int()))

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
            items = ("({:d}) {:#x}".format(item['state'].int(), item['pc'].d.getoffset()) for item in self)
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
                return self.details() + '\n'
            return super(FuncInfo._pIPtoStateMap, self).summary()

    def __dispUnwindHelp(self):
        # FIXME: if this is part of a PECOFF, then we need to check the header
        if getattr(self, 'WIN64', False):
            return int
        return pint.int_t

    _fields_ = [
        (_magicNumber, 'magicNumber'),

        (int, 'maxState'),
        (lambda self: P32(dyn.clone(self._pUnwindMap, length=self['maxState'].li.int())), 'pUnwindMap'),

        (int, 'nTryBlocks'),
        (lambda self: P32(dyn.clone(self._pTryBlockMap, length=self['nTryBlocks'].li.int())), 'pTryBlockMap'),

        (int, 'nIPMapEntries'),
        (lambda self: P32(dyn.clone(self._pIPtoStateMap, length=self['nIPMapEntries'].li.int())), 'pIPtoStateMap'),
        (__dispUnwindHelp, 'dispUnwindHelp'),

        (P32(ESTypeList), 'pESTypeList'),
        (FI_, 'EHFlags'),
    ]

class UWOP_(pbinary.enum):
    length, _values_ = 4, [
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

class operation_(pbinary.struct):
    _fields_ = [
        (4, 'info'),
        (UWOP_, 'code')
    ]

class UNWIND_CODE(pstruct.type):
    # FIXME: define operation_info which depends on the unwind_operation_code.
    def __parameter(self):
        res = self['operation']
        op, info = res.field('code'), res['info']
        if op['ALLOC_LARGE']:
            if info not in {0, 1}:
                raise NotImplementedError
            return USHORT if info == 0 else ULONG

        elif any(op[code] for code in ['SAVE_NONVOL', 'SAVE_XMM128']):
            return USHORT

        elif any(op[code] for code in ['SAVE_NONVOL_FAR', 'SAVE_XMM128_FAR']):
            return UINT

        return pint.uint_t
    _fields_ = [
        (BYTE, 'offset'),
        (operation_, 'operation'),
        (__parameter, 'parameter'),
    ]

class UNW_FLAG_(pbinary.enum):
    length, _values_ = 5, [
        ('NHANDLER', 0),
        ('EHANDLER', 1),
        ('UHANDLER', 2),
        ('FHANDLER', 3),
        ('CHAININFO', 4),
    ]

class UNWIND_INFO(pstruct.type):
    class _Header(pbinary.struct):
        _fields_ = [
            (UNW_FLAG_, 'Flags'),
            (3, 'Version'),
        ]
    class _Frame(pbinary.struct):
        _fields_ = [
            (4, 'Offset'),
            (4, 'Register'),
        ]
        def FrameOffset(self):
            return self['Offset'] * 0x10
        def FrameRegister(self):
            raise NotImplementedError
        def summary(self):
            res = self['Offset']
            return "Register={:d} Offset={:#x} ({:d})".format(self['Register'], res, res * 0x10)

    class _HandlerInfo(pstruct.type):
        _fields_ = [
            (P32(VOID), 'ExceptionHandler'),
            (P32(FuncInfo), 'ExceptionData'),
        ]
    def __HandlerInfo(self):
        res = self['Header'].li
        flags = res.field('Flags')
        return self._HandlerInfo if any(flags[item] for item in ['EHANDLER', 'UHANDLER', 'FHANDLER']) else VOID

    def __FunctionEntry(self):
        res = self['Header'].li
        flags = res.field('Flags')
        return IMAGE_RUNTIME_FUNCTION_ENTRY if flags['CHAININFO'] else VOID

    _fields_ = [
        (_Header, 'Header'),
        (BYTE, 'SizeOfProlog'),
        (BYTE, 'CountOfCodes'),
        (_Frame, 'Frame'),
        (lambda self: dyn.blockarray(UNWIND_CODE, 2 * self['CountOfCodes'].li.int()), 'UnwindCode'),
        (dyn.align(4), 'align(UnwindCode)'),
        (__HandlerInfo, 'HandlerInfo'),
        (__FunctionEntry, 'FunctionEntry'),
    ]

class IMAGE_RUNTIME_FUNCTION_ENTRY(pstruct.type):
    def __BeginAddressPointer(self):
        if not self.parent:
            return ptype.block

        # Grab our parent and collect our function boundaries
        p = self.getparent(IMAGE_RUNTIME_FUNCTION_ENTRY)
        begin, end = (p[fld].li for fld in ['BeginAddress', 'EndAddress'])

        # Figure out its size and return a block that fits it.
        length = abs(end.int() - begin.int())
        return dyn.block(length)
    _fields_ = [
        (P32(__BeginAddressPointer), 'BeginAddress'),
        (P32(ptype.block), 'EndAddress'),
        (P32(UNWIND_INFO), 'UnwindInfoAddress'),
    ]
RUNTIME_FUNCTION = IMAGE_RUNTIME_FUNCTION_ENTRY

### XXX: Everything above this is also defined in pecoff.portable.exceptions

@pbinary.littleendian
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
        (lambda self: P(EXCEPTION_RECORD), 'ExceptionRecord'),
        (PVOID, 'ExceptionAddress'),
        (DWORD, 'NumberParameters'),
        (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(NumberParameters)'),
        (lambda self: dyn.array(ULONG_PTR, self['NumberParameters'].li.int()), 'ExceptionInformation'),
    ]

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
        (lambda self: P(EH3_EXCEPTION_REGISTRATION), 'Next'),
        (PVOID, 'ExceptionHandler'),
        (PSCOPETABLE_ENTRY, 'ScopeTable'),
        (DWORD, 'TryLevel'),
    ]

class EXCEPTION_POINTERS(pstruct.type):
    _fields_ = [
        (P(EXCEPTION_RECORD), 'ExceptionRecord'),
        (P(CONTEXT), 'ContextRecord'),
    ]

class C_SCOPE_TABLE(pstruct.type):
    _fields_ = [
        (P32(VOID), 'BeginAddress'),
        (P32(VOID), 'EndAddress'),
        (P32(VOID), 'HandlerAddress'),
        (P32(VOID), 'JumpTarget'),
    ]

class SCOPE_TABLE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (lambda self: dyn.array(C_SCOPE_TABLE, self['Count'].li.int()), 'ScopeRecord'),
    ]

class CPPEH_RECORD(pstruct.type):
    _fields_ = [
        (DWORD, 'old_esp'),
        (P(EXCEPTION_POINTERS), 'exc_ptr'),
        (EH3_EXCEPTION_REGISTRATION, 'registration'),
    ]

class EHRegistrationNode(pstruct.type):
    _fields_ = [
        (lambda self: P(EHRegistrationNode), 'pNext'),
        (PVOID, 'frameHandler'),
        (int, 'state'),
    ]

class EXCEPTION_ROUTINE(ptype.undefined):
    pass
#PEXCEPTION_ROUTINE = P(EXCEPTION_ROUTINE)

class UNWIND_HISTORY_TABLE_ENTRY(pstruct.type):
    _fields_ = [
        (ULONG64, 'ImageBase'),
        (P(RUNTIME_FUNCTION), 'FunctionEntry'),
    ]

class UNWIND_HISTORY_TABLE(pstruct.type):
    _fields_ = [
        (ULONG, 'Count'),
        (UCHAR, 'LocalHint'),
        (UCHAR, 'GlobalHint'),
        (UCHAR, 'Search'),
        (UCHAR, 'Once'),
        (ULONG64, 'LowAddress'),
        (ULONG64, 'HighAddress'),
        (lambda self: dyn.array(UNWIND_HISTORY_TABLE_ENTRY, self['Count'].li.int()), 'Entry'),
    ]
#PUNWIND_HISTORY_TABLE = P(UNWIND_HISTORY_TABLE)

class DISPATCHER_CONTEXT(pstruct.type, versioned):
    _fields_ = [
        (ULONG64, 'ControlPc'),
        (ULONG64, 'ImageBase'),
        (P(IMAGE_RUNTIME_FUNCTION_ENTRY), 'FunctionEntry'),
        (ULONG64, 'EstablisherFrame'),
        (ULONG64, 'TargetIp'),
        (P(CONTEXT), 'ContextRecord'),
        (P(EXCEPTION_ROUTINE), 'LanguageHandler'),
        (PVOID, 'HandlerData'),

        (P(UNWIND_HISTORY_TABLE), 'HistoryTable'),
        (ULONG, 'ScopeIndex'),
        (ULONG, 'Fill0'),
    ]

class xDISPATCHER_CONTEXT(DISPATCHER_CONTEXT):
    _fields_ = DISPATCHER_CONTEXT._fields_[:-1]

class PMD(pstruct.type):
    _fields_ = [
        (int, 'mdisp'), # member displacement -- member within the class that introduces the member
        (int, 'pdisp'), # vbtable displacement -- pointer to the vbtable within the derived class
        (int, 'vdisp'), # vftable displacement -- entry in the vbtable that contains the offset of the occurrence of the introducing class within the derived class
    ]
    def summary(self):
        m, p, v = (self[fld] for fld in ['mdisp', 'pdisp', 'vdisp'])
        return "mdisp={:+#0{:d}x} pdisp={:+#0{:d}x} vdisp={:+#0{:d}x}".format(m.int(), 1 + 2 + m.size() * 2, p.int(), 1 + 2 + p.size() * 2, v.int(), 1 + 2 + v.size() * 2)

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (PVOID, 'pVFTable'),
        (PVOID, 'spare'),
        (pstr.szstring, 'name'),
    ]

@pbinary.littleendian
class CT_(pbinary.flags):
    '''unsigned_int'''
    _fields_ = [
        (27, 'reserved'),
        (1, 'IsStdBadAlloc'),
        (1, 'IsWinRTHandle'),
        (1, 'HasVirtualBase'),
        (1, 'ByReferenceOnly'),
        (1, 'IsSimpleType'),
    ]

class CatchableType(pstruct.type):
    _fields_ = [
        (CT_, 'properties'),
        (P32(TypeDescriptor), 'pType'),
        (PMD, 'thisDisplacement'),
        (int, 'sizeOrOffset'),
        (P32(VOID), 'copyFunction'),
    ]

class CatchableTypeArray(pstruct.type):
    _fields_ = [
        (int, 'nCatchableTypes'),
        (lambda self: P32(dyn.array(CatchableType, self['nCatchableTypes'].li.int())), 'arrayOfCatchableTypes'),
    ]

@pbinary.littleendian
class TI_(pbinary.flags):
    '''unsigned_int'''
    _fields_ = [
        (27, 'reserved'),
        (1, 'IsWinRT'),
        (1, 'IsPure'),
        (1, 'IsUnaligned'),
        (1, 'IsVolatile'),
        (1, 'IsConst'),
    ]

class ThrowInfo(pstruct.type):
    _fields_ = [
        (TI_, 'attributes'),
        (PVOID, 'pmfnUnwind'),
        (PVOID, 'pForwardCompat'),
        (P(CatchableTypeArray), 'pCatchableTypeArray'),
    ]
_s_ThrowInfo = ThrowInfo

# corrected with http://www.geoffchappell.com/studies/msvc/language/predefined/index.htm?tx=12,14

@pbinary.littleendian
class CHD_(pbinary.flags):
    '''unsigned_long'''
    _fields_ = [
        (29, 'RESERVED'),
        (1, 'AMBIGUOUS'),
        (1, 'VIRTINH'),
        (1, 'MULTINH'),
    ]

class RTTIClassHierarchyDescriptor(pstruct.type):
    def __pBaseClassArray(self):
        length = self['numBaseClasses'].li
        return P32(dyn.clone(RTTIBaseClassArray, length=length.int()))
    _fields_ = [
        (unsigned_long, 'signature'),
        (CHD_, 'attributes'),
        (unsigned_long, 'numBaseClasses'),
        (__pBaseClassArray, 'pBaseClassArray'),
    ]

@pbinary.littleendian
class BCD_(pbinary.flags):
    '''unsigned_long'''
    _fields_ = [
        (25, 'RESERVED'),
        (1, 'HASPCHD'),
        (1, 'NONPOLYMORPHIC'),
        (1, 'VBOFCONTOBJ'),
        (1, 'PRIVORPROTINCOMPOBJ'),
        (1, 'PRIVORPROTBASE'),
        (1, 'AMBIGUOUS'),
        (1, 'NOTVISIBLE'),
    ]

class RTTIBaseClassDescriptor(pstruct.type):
    _fields_= [
        (P32(TypeDescriptor), 'pTypeDescriptor'),
        (unsigned_long, 'numContainedBases'),
        (PMD, 'where'),
        (BCD_, 'attributes'),
        (P32(RTTIClassHierarchyDescriptor), 'pClassDescriptor'),
    ]

class RTTIBaseClassArray(parray.type):
    _object_ = P32(RTTIBaseClassDescriptor)

class COL_SIG_(pint.enum, unsigned_long):
    _values_ = [
        ('REV0', 0),
        ('REV1', 1),
    ]

class RTTICompleteObjectLocator(pstruct.type, versioned):
    def __pSelf(self):
        sig = self['signature'].li
        return P32(RTTICompleteObjectLocator) if sig['REV1'] else ptype.undefined
    _fields_ = [
        (COL_SIG_, 'signature'),
        (unsigned_long, 'offset'),
        (unsigned_long, 'cdOffset'),
        (P32(TypeDescriptor), 'pTypeDescriptor'),
        (P32(RTTIClassHierarchyDescriptor), 'pClassDescriptor'),
        (__pSelf, 'pSelf'),
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

class _EXCEPTION_DISPOSITION(pint.enum):
    _values_ = [
        ('ExceptionContinueExecution', 0),
        ('ExceptionContinueSearch', 1),
        ('ExceptionNestedException', 2),
        ('ExceptionCollidedUnwind',3),
    ]

class PEXCEPTION_ROUTINE(voidstar):
    '''
    EXCEPTION_DISPOSITION
    NTAPI EXCEPTION_ROUTINE(_EXCEPTION_RECORD* ExceptionRecord, PVOID EstablisherFrame, _CONTEXT* ContextRecord, PVOID DispatcherContext);
    '''

class EHExceptionRecord(EXCEPTION_RECORD):
    class EHParameters(pstruct.type):
        _fields_ = [
            (ULONG, 'magicNumber'),
            (dyn.padding(8), 'padding(magicNumber)'),
            (PVOID, 'pExceptionObject'),
            (P(ThrowInfo), 'pThrowInfo'),
            (PVOID, 'pThrowImageBase'),
        ]
    _fields_ = EXCEPTION_RECORD._fields_[:-1] + [
        (EHParameters, 'params'),
    ]

class EXCEPTION_REGISTRATION_RECORD(pstruct.type):
    def __Next(self):
        return EXCEPTION_REGISTRATION_RECORD
    _fields_ = [
        (P(__Next), 'Next'),
        (PEXCEPTION_ROUTINE, 'Hander'),
    ]

class WinRTExceptionInfo(pstruct.type):
    _fields_ = [
        (PVOID, 'description'),
        (PVOID, 'restrictedErrorString'),
        (PVOID, 'restrictedErrorReference'),
        (PVOID, 'capabilitySid'),
        (LONG, 'hr'),
        (PVOID, 'restrictedInfo'),
        (P(ThrowInfo), 'throwInfo'),
        (uint32_t, 'size'),
        (dyn.padding(8), 'padding(size)'),
        (PVOID, 'PrepareThrow'),
    ]

class FrameInfo(pstruct.type):
    def __pNext(self):
        return P(FrameInfo)
    _fields_ = [
        (PVOID, 'pExceptionObject'),
        (__pNext, 'pNext'),
    ]

### VCRUNTIME140.dll - GS_HANDLER_DATA
class GS_HANDLER_DATA(pstruct.type):
    class _CookieOffset(dynamic.union):
        class Bits(pbinary.flags):
            _fields_ = [
                (1, 'EHandler'),
                (1, 'UHandler'),
                (1, 'HasAlignment'),
                (29, 'unused'),
            ]
        _fields_ = [
            (Bits, 'bits'),
            (ULONG, 'offset'),
        ]
    _fields_ = [
        (ULONG, 'CookieOffset'),
        (ULONG, 'AlignedBaseOffset'),
        (ULONG, 'Alignment'),
    ]

### VCRUNTIME140.dll - FrameHandler3
class FrameHandler3(pstruct.type):
    pass

class FrameHandler3(FrameHandler3):
    class TryBlockMap(pstruct.type):
        _fields_ = [
            (P(FuncInfo), '_pFuncInfo'),
            (ULONG64, '_imageBase'),
        ]

class FrameHandler3(FrameHandler3):
    class HandlerMap(pstruct.type):
        _fields_ = [
            (uint32_t, '_numHandlers'),
            (dyn.padding(8), 'padding(_numHandlers)'),
            (P(HandlerType), '_handler'),
        ]

### VCRUNTIME140.dll - FH4
class Bool(int32_t): pass

class FH4(object):
    pass

class FH4(FH4):
    class HandlerTypeHeader(pbinary.flags):
        class contType(pbinary.enum):
            width, _values_ = 2, [
                ('NONE', 0),
                ('ONE', 1),
                ('TWO', 2),
                ('RESERVED', 3),
            ]

class FH4(FH4):
    class HandlerTypeHeader(FH4.HandlerTypeHeader):
        _fields_ = [
            (2, 'unused'),
            #(2, 'contAddr'),
            (FH4.HandlerTypeHeader.contType, 'contAddr'),
            (1, 'contIsRVA'),
            (1, 'dispCatchObj'),
            (1, 'dispType'),
            (1, 'adjectives'),
        ]

class FH4(FH4):
    class FuncInfoHeader(pbinary.flags):
        _fields_ = [
            (1, 'reserved'),
            (1, 'NoExcept'),
            (1, 'EHs'),
            (1, 'TryBlockMap'),
            (1, 'UnwindMap'),
            (1, 'BBT'),
            (1, 'isSeparated'),
            (1, 'isCatch'),
        ]

class FH4(FH4):
    class FuncInfo4(pstruct.type):
        _fields_ = [
            (FH4.FuncInfoHeader, 'header'),
            (dyn.padding(8), 'padding(header)'),
            (uint32_t, 'bbtFlags'),
            (int32_t, 'dispUnwindTryBlockIp'),
            (int32_t, 'dispUnwindTryBlockIp'),
            (int32_t, 'dispUnwindTryBlockIp'),
            (uint32_t, 'dispUnwindTryBlockIp'),
        ]

class FH4(FH4):
    class TryBlockMapEntry4(pstruct.type):
        _fields_ = [
            (int32_t, 'tryLow'),
            (int32_t, 'tryHigh'),
            (int32_t, 'catchHigh'),
            (int32_t, 'dispHandlerArray'),
        ]

class FH4(FH4):
    class TryBlockMap4(pstruct.type):
        _fields_ = [
            (uint32_t, '_numTryBlocks'),
            (dyn.padding(8), 'padding(_numTryBlocks)'),
            (pointer_t, 'buffer'),
            (pointer_t, '_bufferStart'),
            (FH4.TryBlockMapEntry4, 'tryBlock'),
        ]

class FH4(FH4):
    class HandlerType4(pstruct.type):
        _fields_ = [
            (FH4.HandlerTypeHeader, 'header'),
            (dyn.padding(8), 'padding(header)'),
            (uint32_t, 'adjectives'),
            (int32_t, 'dispType'),
            (uint32_t, 'dispCatchObj'),
            (int32_t, 'dispOfHandler'),
            (dyn.padding(8), 'padding(dispOfHandler)'),
            (dyn.array(uint64_t, 2), 'continuationAddress'),
        ]

class FH4(FH4):
    class HandlerMap4(pstruct.type):
        _fields_ = [
            (uint32_t, '_numHandlers'),
            (dyn.padding(8), 'padding(_numHandlers)'),
            (pointer_t, '_buffer'),
            (pointer_t, '_bufferStart'),
            (FH4.HandlerType4, '_handler'),
            (uint64_t, '_imageBase'),
            (int32_t, '_functionStart'),
            (dyn.padding(8), 'padding(_functionStart)'),
        ]

class FH4(FH4):
    class UnwindMapEntry4(pstruct.type):
        class Type(pint.enum, uint32_t):
            _values_ = [
                ('NoUW', 0),
                ('DtorWithObj', 1),
                ('DtorWithPtrToObj', 2),
                ('RVA', 3),
            ]

class FH4(FH4):
    class UnwindMapEntry4(FH4.UnwindMapEntry4):
        _fields_ = [
            (uint32_t, 'nextOffset'),
            (FH4.UnwindMapEntry4.Type, 'type'),
            (int32_t, 'action'),
            (uint32_t, 'object'),
        ]

class FH4(FH4):
    class SepIPtoStateMapEntry4(pstruct.type):
        _fields_ = [
            (int32_t, 'addrStartRVA'),
            (int32_t, 'dispOfIPMap'),
        ]

class FH4(FH4):
    class SepIPtoStateMap4(pstruct.type):
        _fields_ = [
            (uint32_t, '_numEntries'),
            (dyn.padding(8), 'padding(_numEntries)'),
            (pointer_t, '_bufferStart'),
            (uint64_t, '_imageBase'),
            (FH4.SepIPtoStateMapEntry4, 'singleEntry'),
            (Bool, 'isSingle'),
            (dyn.padding(8), 'padding(_numEntries)'),
        ]

class FH4(FH4):
    class IPtoStateMap4(pstruct.type):
        _fields_ = [
            (uint32_t, '_numEntries'),
            (dyn.padding(8), 'padding(_numEntries)'),
            (pointer_t, '_bufferStart'),
            (uint64_t, '_imageBase'),
            (uint32_t, '_funcStart'),
        ]

class FH4(FH4):
    class IPtoStateMapEntry4(pstruct.type):
        _fields_ = [
            (int32_t, 'Ip'),
            (int32_t, 'State'),
        ]

class FH4(FH4):
    class UWMap4(pstruct.type):
        _fields_ = [
            (int32_t, '_numEntries'),
            (dyn.padding(8), 'padding(_numEntries)'),
            (pointer_t, '_bufferStart'),
            (FH4.UnwindMapEntry4, '_UWEntry'),
        ]

class FH4(FH4):
    class Compress(object):
        class RVAoffsets(pstruct.type):
            _fields_ = [
                (uint32_t, 'count'),
                (dyn.array(uint32_t, 4), 'values'),
            ]

