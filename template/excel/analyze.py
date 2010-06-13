from ptypes import *

### primitive types
class USHORT(pint.uint16_t): pass

###
class Biff(object):
    """Anything that inherits from this is considered a frontend biff type"""
    bifftype = int

LookupBiffType = {}     # this gets initialized at the very end of this file
class BiffGeneral(pstruct.type):
    def __lookuptype(s):
        global LookupBiffType
        t = int(s['type'].l)
        try:
            return LookupBiffType[t]
        except KeyError:
            pass
        return dyn.block( int(s['length'].l) )

    _fields_ = [
        (pint.uint16_t, 'type'),
        (pint.uint16_t, 'length'),
        (__lookuptype, 'data')
    ]

class BiffSubStream(parray.terminated):
    _object_ = BiffGeneral
    def isTerminator(self, value):
        if type(value['data']) is EOF:
            return True
        return False

    def search(self, bifftype):
        result = []
        for i,n in enumerate(self):
            try:
                if n['data'].bifftype == bifftype:
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
        bof = self[0]['data']
        return '%s -> %d records -> document type %s'% (self.name(), len(self), repr(bof['dt']))

###
class RRTabId(dyn.array(USHORT, 3), Biff):
    bifftype = 317

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

class MTRSettings(pstruct.type, Biff):
    bifftype = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'fMTREnabled'),
        (pint.uint32_t, 'fUserSetThreadCount'),
        (pint.uint32_t, 'cUserThreadCount')
    ]
###
class Compat12(pstruct.type, Biff):
    bifftype = 2188
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

class LabelSst(pstruct.type, Biff):
    bifftype = 253
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
class RK(pstruct.type, Biff):
    bifftype = 638
    _fields_ = [
        (pint.uint16_t, 'rw'),
        (pint.uint16_t, 'col'),
        (RkRec, 'rkrec')
    ]
###
class Xnum(pfloat.double): pass
class Number(pstruct.type, Biff):
    bifftype = 515
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

class MergeCells(pstruct.type, Biff):
    bifftype = 229
    _fields_ = [
        (pint.uint16_t, 'cmcs'),
        (lambda s: dyn.array(Ref8, int(s['cmcs'].l)), 'rgref')
    ]
###
class CrtLayout12(pstruct.type, Biff):
    class __CrtLayout12Auto(pbinary.struct):
        _fields_ = [
            (1, 'unused'),
            (4, 'autolayouttype'),
            (11, 'reserved')
        ]

    bifftype = 2205
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
class Frame(pstruct.type, Biff):
    class __FrameAuto(pbinary.struct):
        _fields_ = [
            (1, 'fAutoSize'),
            (1, 'fAutoPosition'),
            (14, 'reserved')
        ]

    bifftype = 4146
    _fields_ = [
        (pint.uint16_t, 'frt'),
        (__FrameAuto, 'f')
    ]

###
class Pos(pstruct.type, Biff):
    bifftype = 4175
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
        (lambda s: dyn.clone(pstr.wstring, length=[s.length, s.length*2][int(s['fHighByte'].l)>>7]), 'rgb')
    ]

class SupBook(pstruct.type, Biff):
    bifftype = 430
    _fields_ = [
        (pint.uint16_t, 'ctab'),
        (pint.uint16_t, 'cch'),
    ]

###
class BOF(pstruct.type, Biff):
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

    bifftype = 2057
    _fields_ = [
        (pint.uint16_t, 'vers'),
        (__BOFDocType, 'dt'),
        (pint.uint16_t, 'rupBuild'),
        (pint.uint16_t, 'rupYear'),
        (__BOFFlags, 'f')
    ]

class EOF(pstruct.type, Biff):
    bifftype = 10
    _fields_ = []

### build lookup table
import inspect
for cls in globals().values():
    if inspect.isclass(cls) and issubclass(cls, Biff):
        LookupBiffType[cls.bifftype] = cls
    continue

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
