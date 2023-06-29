import sys, ptypes, logging, bisect, itertools, operator, functools
from ptypes import pstruct, parray, ptype, dyn, pstr, utils, pbinary, pint

from ..headers import *

class VOID(ptype.undefined):
    pass

def P32(target):
    return virtualaddress(target, type=dword)

class UnwindMapEntry(pstruct.type):
    _fields_ = [
        (int32, 'toState'),
        (P32(VOID), 'action'),
    ]
    def summary(self):
        return "action={:#x}(toState:{:d})".format(self['action'].int(), self['toState'].int())

class TypeDescriptor(pstruct.type):
    _fields_ = [
        (realaddress(VOID), 'pVFTable'),
        (realaddress(pstr.szstring), 'spare'),  # demangled name from type_info::name
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
        try:
            header = self.getparent(Header)
        except ptypes.error.ItemNotFoundError:
            return int0
        return int32 if header.is64() else int0

    _fields_ = [
        (HT_, 'adjectives'),
        (P32(TypeDescriptor), 'pType'),
        (int32, 'dispCatchObj'),
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
        (int32, 'tryLow'),
        (int32, 'tryHigh'),
        (int32, 'catchHigh'),
        (int32, 'nCatches'),
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
    class _state(pint.enum, int32):
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
        (int32, 'nCount'),
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
        try:
            header = self.getparent(Header)
        except ptypes.error.ItemNotFoundError:
            return int0
        return int32 if header.is64() else int0

    _fields_ = [
        (_magicNumber, 'magicNumber'),

        (int32, 'maxState'),
        (lambda self: P32(dyn.clone(self._pUnwindMap, length=self['maxState'].li.int())), 'pUnwindMap'),

        (int32, 'nTryBlocks'),
        (lambda self: P32(dyn.clone(self._pTryBlockMap, length=self['nTryBlocks'].li.int())), 'pTryBlockMap'),

        (int32, 'nIPMapEntries'),
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
        op, info = res.item('code'), res['info']
        if op['ALLOC_LARGE']:
            if info not in {0, 1}:
                raise NotImplementedError
            return uint16 if info == 0 else uint32

        elif any(op[code] for code in ['SAVE_NONVOL', 'SAVE_XMM128']):
            return uint16

        elif any(op[code] for code in ['SAVE_NONVOL_FAR', 'SAVE_XMM128_FAR']):
            return uint32

        return pint.uint_t
    _fields_ = [
        (byte, 'offset'),
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
        flags = res.item('Flags')
        return self._HandlerInfo if any(flags[item] for item in ['EHANDLER', 'UHANDLER', 'FHANDLER']) else VOID

    def __FunctionEntry(self):
        res = self['Header'].li
        flags = res.item('Flags')
        return IMAGE_RUNTIME_FUNCTION_ENTRY if flags['CHAININFO'] else VOID

    _fields_ = [
        (_Header, 'Header'),
        (byte, 'SizeOfProlog'),
        (byte, 'CountOfCodes'),
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
        (P32(UNWIND_INFO), 'UnwindData'),
    ]
RUNTIME_FUNCTION = IMAGE_RUNTIME_FUNCTION_ENTRY

class IMAGE_EXCEPTION_DIRECTORY(parray.block):
    _object_ = IMAGE_RUNTIME_FUNCTION_ENTRY
    def blocksize(self):
        return self.p.p['Size'].int()

    def enumerate(self):
        for index, item in enumerate(self):
            yield index, item
        return

    def augmented(self):
        '''Return an augmented interval tree of each `IMAGE_RUNTIME_FUNCTION_ENTRY` within the array as a dictionary of indices where each node is a tuple, (left-index, owners, maximum, right-index).'''
        logger = logging.getLogger(__name__)

        items = [(entry['BeginAddress'].int(), entry['EndAddress'].int(), id) for id, entry in self.enumerate()]
        intervals = sorted(items, key=operator.itemgetter(0))

        result, table = {}, {id : (start, stop, id) for start, stop, id in intervals}
        def augment(intervals, table=table, result=result):
            center = len(intervals) // 2
            key, point, cid = table[intervals[center]]

            left, right, owners = [], [], []
            for start, stop, id in map(functools.partial(operator.getitem, table), intervals):
                if stop <= key:
                    left.append(id)
                elif start > key:
                    right.append(id)
                else:
                    owners.append(id)
                point = max(point, stop)

            node = left and augment(left), owners, point, right and augment(right)
            [result.setdefault(id, node) for id in owners]
            return cid

        root = augment([id for id in map(operator.itemgetter(2), intervals)])
        return result

    def boundaries(self, augmented=None):
        '''Return a dictionary of points associated with each `IMAGE_RUNTIME_FUNCTION_ENTRY` and a sorted list of points.'''
        logger = logging.getLogger(__name__)

        items = [(entry['BeginAddress'].int(), entry['EndAddress'].int(), id) for id, entry in self.enumerate()]
        intervals = sorted(items, key=operator.itemgetter(0))

        result, table, augmented = [], {}, augmented or self.augmented()
        for start, stop, id in intervals:
            entry, (_, _, current, _) = self[id], augmented[id]
            assert(stop > start), entry

            # find the index of the result insertion point for each point in the interval.
            istart, istop = (bisect.bisect_left(result, point) for point in [start, stop])

            # if insertion point is even, then we're not overlapping anything and can add it.
            if istart == istop or not(istart % 2 and istart % 2):
                result[istart : istop] = [start, stop]
                table[start] = table[stop] = id
                logger.debug("{:s} : {:{:d}<s} {:s} ({:d}/{:d}) {:#0{:d}x}..{:#0{:d}x}".format(entry.instance(), 'insert', 9, '^^', 1, 1, start, 2 + 8, stop, 2 + 8))

            # if our insertion point is not even or the same, then our interval is overlapping.
            # so, we need to figure out which interval owns the point by checking its maximum.
            elif istart % 2 != istop % 2:
                point = result[istop - 1]
                _, _, maximum, _ = augmented[table[point]]
                result[istart : istop] = [start, stop]
                table[start] = table[stop] = id
                logger.debug("{:s} : {:{:d}<s} {:s} ({:d}/{:d}) {:#0{:d}x}..{:#0{:d}x}".format(entry.instance(), 'overlap', 9, '<' if istart % 2 else '>', id, table[point], start, 2 + 8, stop, 2 + 8))
            continue
        return table, result

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
