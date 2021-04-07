import sys, ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils,pbinary,pint
from ..headers import *

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (int32, 'toState'),
        (virtualaddress(ptype.undefined, type=dword), 'action'),
    ]
    def summary(self):
        return "action={:#x}(toState:{:d})".format(self['action'].int(), self['toState'].int())

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (realaddress(ptype.undefined), 'pVFTable'),
        (realaddress(ptype.undefined), 'spare'),
        (pstr.szstring, 'name'),
    ]

@pbinary.littleendian
class HT_(pbinary.flags):
    '''unsigned_int'''
    _fields_ = [
        (1, 'IsComPlusEh'),         # Is handling within complus eh.
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
        try:
            header = self.getparent(Header)
        except ptypes.error.ItemNotFoundError:
            return int0
        return int32 if header.is64() else int0

    _fields_ = [
        (HT_, 'adjectives'),
        (virtualaddress(TypeDescriptor, type=dword), 'pType'),
        (int32, 'dispCatchObj'),
        (virtualaddress(ptype.undefined, type=dword), 'addressOfHandler'),
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

class TryBlockMapEntry(pstruct.type):
    class _pHandlerArray(parray.type):
        _object_ = HandlerType
        def details(self):
            items = []
            for item in self:
                position = ptypes.utils.repr_position(item.getposition())
                description = ptypes.utils.repr_instance(item.classname(), item.name())

                res = item['adjectives']
                iterable = (fld if item[fld] in {1} else "{:s}={:#x}".format(fld, item[fld]) for fld in item if item[fld])
                adjectives = '|'.join(iterable) or "{:#x}".format(res.int())

                if item['dispFrame'].int():
                    res = "[{:s}] {:s} dispCatchObj={:+#x} dispFrame={:+#x} addressOfHandler={:#x} adjectives={:s}".format(position, description, item['dispCatchObj'].int(), item['dispFrame'].int(), item['addressOfHandler'].int(), adjectives)
                else:
                    res = "[{:s}] {:s} dispCatchObj={:+#x} addressOfHandler={:#x} adjectives={:s}".format(position, description, item['dispCatchObj'].int(), item['addressOfHandler'].int(), adjectives)
                items.append(res)
            return '\n'.join(items)
        def repr(self):
            if self.initializedQ():
                return self.details() + '\n'
            return self.summary()
    _fields_ = [
        (int32, 'tryLow'),
        (int32, 'tryHigh'),
        (int32, 'catchHigh'),
        (int32, 'nCatches'),
        (lambda self: virtualaddress(dyn.clone(self._pHandlerArray, length=self['nCatches'].li.int()), type=dword), 'pHandlerArray'),
    ]

class IPtoStateMap(pstruct.type):
    class _state(pint.enum, int32):
        _values_ = [
            ('END', -1),
        ]
    _fields_ = [
        (virtualaddress(ptype.undefined, type=dword), 'pc'),
        (_state, 'state'),
    ]
    def summary(self):
        return "state={:d} pc={!s}".format(self['state'].int(), self['pc'].summary())

class ESTypeList(pstruct.type):
    _fields_ = [
        (int32, 'nCount'),
        (lambda self: virtualaddress(dyn.array(HandlerType, self['nCount'].li.int()), type=dword), 'pHandlerArray'),
    ]

@pbinary.littleendian
class FI_(pbinary.flags):
    _fields_ = [
        (29, 'unused'),
        (1, 'EHNOEXCEPT_FLAG'),
        (1, 'DYNSTKALIGN_FLAG'),
        (1, 'EHS_FLAG'),
    ]

class FuncInfo(pstruct.type):
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
        try:
            header = self.getparent(Header)
        except ptypes.error.ItemNotFoundError:
            return int0
        return int32 if header.is64() else int0

    _fields_ = [
        (_magicNumber, 'magicNumber'),

        (int32, 'maxState'),
        (lambda self: virtualaddress(dyn.clone(self._pUnwindMap, length=self['maxState'].li.int()), type=dword), 'pUnwindMap'),

        (int32, 'nTryBlocks'),
        (lambda self: virtualaddress(dyn.clone(self._pTryBlockMap, length=self['nTryBlocks'].li.int()), type=dword), 'pTryBlockMap'),

        (int32, 'nIPMapEntries'),
        (lambda self: virtualaddress(dyn.clone(self._pIPtoStateMap, length=self['nIPMapEntries'].li.int()), type=dword), 'pIPtoStateMap'),
        (__dispUnwindHelp, 'dispUnwindHelp'),

        (virtualaddress(ESTypeList, type=dword), 'pESTypeList'),
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
        op, info = res.item('code'), res['info']
        if op['ALLOC_LARGE']:
            if info not in {0, 1}:
                raise NotImplementedError
            return pint.uint16_t if info == 0 else pint.uint32_t

        elif any(op[code] for code in ['SAVE_NONVOL', 'SAVE_XMM128']):
            return pint.uint16_t

        elif any(op[code] for code in ['SAVE_NONVOL_FAR', 'SAVE_XMM128_FAR']):
            return pint.uint32_t

        return pint.uint_t
    _fields_ = [
        (pint.uint8_t, 'offset'),
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
        _fields_= [
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
            (virtualaddress(ptype.undefined, type=dword), 'ExceptionHandler'),
            (virtualaddress(FuncInfo, type=dword), 'ExceptionData')
        ]

    def __HandlerInfo(self):
        res = self['Header'].li
        flags = res.item('Flags')
        return self._HandlerInfo if any(flags[item] for item in ['EHANDLER', 'UHANDLER', 'FHANDLER']) else ptype.undefined

    def __FunctionEntry(self):
        res = self['Header'].li
        flags = res.item('Flags')
        return RUNTIME_FUNCTION if flags['CHAININFO'] else ptype.undefined

    _fields_ = [
        (_Header, 'Header'),
        (byte, 'SizeOfProlog'),
        (byte, 'CountOfCodes'),
        (_Frame, 'Frame'),
        (lambda self: dyn.blockarray(UNWIND_CODE, 2 * self['CountOfCodes'].li.int()), 'UnwindCode'),
        (dyn.align(4), 'align(ExceptionHandler)'),  # FIXME: this was copied from IDA
        (__HandlerInfo, 'HandlerInfo'),
        (__FunctionEntry, 'FunctionEntry'),
    ]

class IMAGE_RUNTIME_FUNCTION_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(ptype.undefined, type=dword), 'BeginAddress'),
        (virtualaddress(ptype.undefined, type=dword), 'EndAddress'),
        (virtualaddress(UNWIND_INFO, type=dword), 'UnwindData'),
    ]

class IMAGE_EXCEPTION_DIRECTORY(parray.block):
    _object_ = IMAGE_RUNTIME_FUNCTION_ENTRY

    def blocksize(self):
        return self.p.p['Size'].int()

if __name__ == '__main__':
    import ptypes, pecoff
    source = ptypes.provider.file('c:/windows/system32/wow64win.dll', mode='rb')
    a = pecoff.Executable.File(source=source).l
    print(a['Next']['Header']['padding'].hexdump())
    print(a['Next']['Data']['Segments'][0])
    #b = a.new(dyn.block(0x5b74), offset=0x50e00)
    b = a['Next']['Header']['DataDirectory'][3]['Address'].d
    b=b.l
    #c = RUNTIME_FUNCTION(source=ptypes.prov.proxy(b))
    c = b[2]['UnwindData'].d.l
    print(c['header'])
    print(ptypes.bitmap.string(c['header'].bitmap()))
    print(c['sizeofprolog'])
    print(c['countofcodes'])
    print(c['frame'])
    print(c['unwindcode'])
    print(c['exceptionhandler'])
    print(c['chainedunwindinfo'])
