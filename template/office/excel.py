from ptypes import *
import art

import __init__
class Record(__init__.Record): cache = {}
class RecordGeneral(__init__.RecordGeneral):
    Record=Record
    def __extra(s):
        t = int(s['type'].l)
        name = '[%s]'% ','.join(s.backtrace()[1:])

        used = s['data'].size()
        total = int(s['length'].l)
        if used == total:
            return dyn.block(0)

        if total >= used:
            l = total-used
            print "biff object at %x (type %x) %s has %x bytes unused"% (s.getoffset(), t, name, l)
            return dyn.block(l)

        print "biff object at %x (type %x) %s's contents are larger than expected (%x>%x)"% (s.getoffset(), t, name, used, total)
        return dyn.block(0)

    def __data(s):
        t = int(s['type'].l)
        l = int(s['length'].l)
        try:
            cls = s.Record.Lookup(t)
        except KeyError:
            return dyn.clone(__init__.RecordUnknown, type=t, length=l)
        return dyn.clone(cls, blocksize=lambda s:l)

    _fields_ = [
        (pint.uint16_t, 'type'),
        (pint.uint16_t, 'length'),
        (__data, 'data'),
        (__extra, 'extra')
    ]

    def blocksize(self):
        return 4 + int(self['length'])

class RecordContainer(__init__.RecordContainer): _object_ = RecordGeneral

### primitive types
class USHORT(pint.uint16_t): pass

### File types
class BiffSubStream(parray.terminated):
    '''Each excel stream'''
    _object_ = RecordGeneral
    def isTerminator(self, value):
        if int(value['type']) == EOF.type:
            return True
        return False

    def search(self, type):
        type = int(type)
        result = []
        for i,n in enumerate(self):
            try:
                if n['data'].type == type:
                    result.append(i)
            except AttributeError:
                pass
            continue
        return result

    def searcht(self, biff):
        result = []
        for i,n in enumerate(self):
            if type(n['data']) is biff:
                result.append(i)
            continue
        return result

    def __repr__(self):
        if self.initialized:
            bof = self[0]['data']
            try:
                return '%s -> %d records -> document type %s'% (self.name(), len(self), repr(bof['dt']))
            except (TypeError,KeyError):
                pass
            return '%s -> %d records -> document type %s'% (self.name(), len(self), repr(bof.serialize()))
        return super(BiffSubStream, self).__repr__()

class File(__init__.File):
    _object_ = BiffSubStream

    def __repr__(self):
        if self.initialized:
            return '%s streams=%d'%(self.name(), len(self))
        return super(File, self).__repr__()

###
@Record.Define
class CatSerRange(pstruct.type):
    type = 0x1020
    type = 4128

    class __flags(pbinary.struct):
        _fields_ = [
            (1, 'fBetween'),
            (1, 'fMaxCross'),
            (1, 'fReverse'),
            (13, 'reserved')
        ]

    _fields_ = [
        (pint.int16_t, 'catCross'),
        (pint.int16_t, 'catLabel'),
        (pint.int16_t, 'catMark'),
        (__flags, 'catFlags')
    ]

###
#@Record.Define
class RRTabId(parray.block):
    _object_ = USHORT
    type = 317
    def size(self):
        return int(self.parent['length'])

###
class FrtFlags(pbinary.struct):
    _fields_ = [
        (1, 'fFrtRef'),
        (1, 'fFrtAlert'),
        (14, 'reserved')
    ]

class FrtHeader(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rt'),
        (FrtFlags, 'grbitFrt'),
        (dyn.block(8), 'reserved')
    ]

@Record.Define
class MTRSettings(pstruct.type):
    type = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'fMTREnabled'),
        (pint.uint32_t, 'fUserSetThreadCount'),
        (pint.uint32_t, 'cUserThreadCount')
    ]
###
@Record.Define
class Compat12(pstruct.type):
    type = 2188
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'fNoCompatChk')
    ]
###
class Cell(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rw'),
        (pint.uint16_t, 'col'),
        (pint.uint16_t, 'ixfe')
    ]
@Record.Define
class LabelSst(pstruct.type):
    type = 253
    _fields_ = [
        (Cell, 'cell'),
        (pint.uint32_t, 'isst')
    ]
###
class RkNumber(pbinary.struct):
    _fields_ = [
        (1, 'fX100'),
        (1, 'fInt'),
        (30, 'num'),
    ]

class RkRec(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'ixfe'),
        (RkNumber, 'RK')
    ]
@Record.Define
class RK(pstruct.type):
    type = 638
    _fields_ = [
        (pint.uint16_t, 'rw'),
        (pint.uint16_t, 'col'),
        (RkRec, 'rkrec')
    ]
###
class Xnum(pfloat.double): pass

@Record.Define
class Number(pstruct.type):
    type = 515
    _fields_ = [
        (Cell, 'cell'),
        (Xnum, 'num')
    ]
###
class Ref8(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rwFirst'),
        (pint.uint16_t, 'rwLast'),
        (pint.uint16_t, 'colFirst'),
        (pint.uint16_t, 'colLast'),
    ]

@Record.Define
class MergeCells(pstruct.type):
    type = 229
    _fields_ = [
        (pint.uint16_t, 'cmcs'),
        (lambda s: dyn.array(Ref8, int(s['cmcs'].l)), 'rgref')
    ]
###
@Record.Define
class CrtLayout12(pstruct.type):
    class __CrtLayout12Auto(pbinary.struct):
        _fields_ = [
            (1, 'unused'),
            (4, 'autolayouttype'),
            (11, 'reserved')
        ]

    type = 2205
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'dwCheckSum'),
        (__CrtLayout12Auto, 'auto'),
        (pint.uint16_t, 'wXMode'),
        (pint.uint16_t, 'wYMode'),
        (pint.uint16_t, 'wWidthMode'),
        (pint.uint16_t, 'wHeightMode'),
        (Xnum, 'x'),
        (Xnum, 'y'),
        (Xnum, 'dx'),
        (Xnum, 'dy'),
        (pint.uint16_t, 'reserved')
    ]

###
@Record.Define
class Frame(pstruct.type):
    class __FrameAuto(pbinary.struct):
        _fields_ = [
            (1, 'fAutoSize'),
            (1, 'fAutoPosition'),
            (14, 'reserved')
        ]

    type = 4146
    _fields_ = [
        (pint.uint16_t, 'frt'),
        (__FrameAuto, 'f')
    ]

###
@Record.Define
class Pos(pstruct.type):
    type = 4175
    _fields_ = [
        (pint.uint16_t, 'mdTopLt'),
        (pint.uint16_t, 'mdBotRt'),
        (pint.uint16_t, 'x1'),
        (pint.uint16_t, 'unused1'),
        (pint.uint16_t, 'y1'),
        (pint.uint16_t, 'unused2'),
        (pint.uint16_t, 'x2'),
        (pint.uint16_t, 'unused3'),
        (pint.uint16_t, 'y2'),
        (pint.uint16_t, 'unused4'),
    ]

###
class XLUnicodeStringNoCch(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'fHighByte'),
        (lambda s: dyn.clone(pstr.wstring, length=[s.length, s.length*2][int(s['fHighByte'].l)>>7]), 'rgb')
    ]

class XLUnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cch'),
        (pint.uint8_t, 'fHighByte'),
        (lambda s: dyn.clone(pstr.wstring, length=[int(s['cch'].l), int(s['cch'])*2][int(s['fHighByte'].l)>>7]), 'rgb')
    ]

@Record.Define
class SupBook(pstruct.type):
    type = 430
    _fields_ = [
        (pint.uint16_t, 'ctab'),
        (pint.uint16_t, 'cch'),
    ]

#DataValidationCriteria
@Record.Define
class DVAL(pstruct.type):
    type = 434
    type = 0x1b2

    class __wDviFlags(pbinary.struct):
        _fields_ = [
            (1, 'fWnClosed'),
            (1, 'fWnPinned'),
            (1, 'fCached'),
            (13, 'Reserved')
        ]

    _fields_ = [
        (pbinary.littleendian(__wDviFlags), 'wDviFlags'),
        (pint.uint32_t, 'xLeft'),
        (pint.uint32_t, 'yTop'),
        (pint.uint32_t, 'idObj'),
        (pint.uint32_t, 'idvMac'),
    ]

@Record.Define
class DV(pstruct.type):
    type = 0x1be
    type = 446

    class __dwDvFlags(pbinary.struct):
        _fields_ = [
            (4, 'ValType'),
            (3, 'ErrStyle'),
            (1, 'fStrLookup'),
            (1, 'fAllowBlank'),
            (1, 'fSuppressCombo'),
            (8, 'mdImeMode'),
            (1, 'fShowInputMsg'),
            (1, 'fShowErrorMsg'),
            (4, 'typOperator'),
            (8, 'Reserved'),
        ]

    _fields_ = [
        (__dwDvFlags, 'dwDvFlags'),
        (DVAL, 'Dval')
    ]

###
@Record.Define
class BOF(pstruct.type):
    class __BOFFlags(pbinary.struct):
        _fields_ = [
            (1, 'fWin'),
            (1, 'fRisc'),
            (1, 'fBeta'),
            (1, 'fWinAny'),
            (1, 'fMacAny'),
            (1, 'fBetaAny'),
            (2, 'unused1'),
            (1, 'fRiscAny'),
            (1, 'fOOM'),
            (1, 'fGIJmp'),
            (2, 'unused2'),
            (1, 'fFontLimit'),
            (4, 'verXLHigh'),
            (1, 'unused3'),
            (13, 'reserved1'),
            (8, 'verLowestBiff'),
            (4, 'verLastXLSaved'),
            (20, 'reserved2')
        ]

    class __BOFDocType(pint.enum, pint.uint16_t):
        _fields_ = [
            ('workbook', 0x0005),
            ('worksheet', 0x0010),
            ('charsheet', 0x0020),
            ('macrosheet', 0x0040)
        ]

    type = 2057
    _fields_ = [
        (pint.uint16_t, 'vers'),
        (__BOFDocType, 'dt'),
        (pint.uint16_t, 'rupBuild'),
        (pint.uint16_t, 'rupYear'),
        (__BOFFlags, 'f')
    ]

#@Record.Define
class MSODRAWING(art.SpContainer):
    type = 0x00ec
    type = 236

@Record.Define
class EOF(pstruct.type):
    type = 10
    _fields_ = []

if __name__ == '__main__':
    import ptypes
    from ptypes import *
    ptypes.setsource( provider.file('./poc.wb') )

    streams = dyn.array(BiffSubStream, 4)()
    streams.l

    workbook = None
    worksheets = []
    for st in streams:
        bof = st[0]['data']
        t = int(bof['dt'])
        if t == 5:
            if workbook is not None:
                print "Workbook has already been assigned. Honoring anyways.."

            workbook = st

        elif t == 0x10:
            worksheets.append(st)

        else:
            raise NotImplementedError( repr(bof['dt']) )
        continue

if __name__ == '__main__':
    # related to case
    supbook, = workbook.searcht(SupBook)
    supbook = workbook[supbook]

    def fixoffsets(container):
        o = container.getoffset()
        for n in container.value:
            n.setoffset(o)
            o += n.size()
        return

#    for z in range(64):
#        workbook.insert(403, supbook.copy())
#    fixupstream(workbook)
