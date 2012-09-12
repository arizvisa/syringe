from ptypes import *
import art,graph

'''maG
type id's to look u
'''

import __init__
class Record(__init__.Record): cache = {}
class RecordGeneral(__init__.RecordGeneral):
    Record=Record
    def __extra(s):
        t = int(s['type'].l)
        name = '[%s]'% ','.join(s.backtrace()[1:])

        used = s['data'].blocksize()
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
            cls = s.Record.lookup(t)
        except KeyError:
            return dyn.clone(__init__.RecordUnknown, type=t, length=l)
        return dyn.clone(cls, blocksize=lambda s:l)

    _fields_ = [
        (pint.littleendian(pint.uint16_t), 'type'),
        (pint.littleendian(pint.uint16_t), 'length'),
        (__data, 'data'),
        (__extra, 'extra')
    ]

    def blocksize(self):
        return 4 + int(self['length'])

class RecordContainer(__init__.RecordContainer): _object_ = RecordGeneral

### primitive types
class USHORT(pint.uint16_t): pass
class Rw(pint.uint32_t): pass
class ColByteU(pint.uint8_t): pass
class RwU(pint.uint32_t): pass
class Xnum(pfloat.double): pass
class IFmt(pint.uint16_t): pass
class FontIndex(pint.uint16_t): pass
class Col(pint.uint16_t): pass
class IXFCell(pint.uint16_t): pass
class XtiIndex(pint.uint16_t): pass
class DCol(pint.uint16_t): pass
class DColByteU(pint.uint8_t): pass
class DRw(pint.uint16_t): pass
class DRw_ByteU(pint.uint8_t): pass
class XFIndex(pint.uint16_t): pass

class ColRelU(pbinary.struct):
    _fields_ = [
        (14, 'col'),
        (1, 'colRelative'),
        (1, 'rowRelative'),
    ]

class ColRelNegU(pbinary.struct):
    _fields_ = [
        (14, 'col'),
        (1, 'colRelative'),
        (1, 'rowRelative'),
    ]

class RkNumber(pbinary.struct):
    _fields_ = [
        (1, 'fX100'),
        (1, 'fInt'),
        (30, 'num'),
    ]

class RkRec(pstruct.type):
    _fields_ = [
        (IXFCell, 'ixfe'),
        (RkNumber, 'RK'),
    ]

class RgceLoc(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColRelU, 'column'),
    ]
class RgceLocRel(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColRelNegU, 'column'),
    ]

class RgceArea(pstruct.type):
    _fields_ = [
        (RwU, 'rowFirst'),
        (RwU, 'rowLast'),
        (ColRelU, 'columnFirst'),
        (ColRelU, 'columnLast'),
    ]

class RgceAreaRel(pstruct.type):
    _fields_ = [
        (RwU, 'rowFirst'),
        (RwU, 'rowLast'),
        (ColRelNegU, 'columnFirst'),
        (ColRelNegU, 'columnLast'),
    ]

class LongRGBA(pstruct.type):
    _fields_ = [ (pint.uint8_t,'red'),(pint.uint8_t,'green'),(pint.uint8_t,'blue'),(pint.uint8_t,'alpha') ]

### File types
class BiffSubStream(parray.terminated):
    '''Each excel stream'''
    _object_ = RecordGeneral
    def isTerminator(self, value):
#        print hex(value.getoffset()),value['data'].name(), value.blocksize()
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

    def details(self):
        if self.initialized:
            bof = self[0]['data']
            try:
                return '%s -> %d records -> document type %s'% (self.name(), len(self), repr(bof['dt']))
            except (TypeError,KeyError):
                pass
            return '%s -> %d records -> document type %s'% (self.name(), len(self), repr(bof.serialize()))
        return '%s [uninitialized] -> %d records'% (self.name(), len(self))

class File(__init__.File):
    _object_ = BiffSubStream

    def details(self):
        if self.initialized:
            return '%s streams=%d'%(self.name(), len(self))
        return '%s [uninitialized] streams=%d'%(self.name(), len(self))

###
@Record.define
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
@Record.define
class RRTabId(parray.block):
    _object_ = USHORT
    type = 0x13d
    type = 317
    def blocksize(self):
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

@Record.define
class MTRSettings(pstruct.type):
    type = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'fMTREnabled'),
        (pint.uint32_t, 'fUserSetThreadCount'),
        (pint.uint32_t, 'cUserThreadCount')
    ]
###
@Record.define
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
@Record.define
class LabelSst(pstruct.type):
    type = 253
    _fields_ = [
        (Cell, 'cell'),
        (pint.uint32_t, 'isst')
    ]
###
@Record.define
class RK(pstruct.type):
    type = 638
    type = 0x273
    _fields_ = [
        (pint.uint16_t, 'rw'),
        (pint.uint16_t, 'col'),
        (RkRec, 'rkrec')
    ]

#@Record.define     # FIXME
class MulBlank(pstruct.type):
    type = 190
    type = 0xbe
    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (lambda s: dyn.array(IXFCell,s['colLast'].l.int()-s['colFirst'].l.int()), 'rgixfe'), 
        (Col, 'colLast'),   # FIXME
    ]

###
@Record.define
class Number(pstruct.type):
    type = 515
    type = 0x203
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

@Record.define
class MergeCells(pstruct.type):
    type = 229
    _fields_ = [
        (pint.uint16_t, 'cmcs'),
        (lambda s: dyn.array(Ref8, int(s['cmcs'].l)), 'rgref')
    ]
###
@Record.define
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
@Record.define
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
@Record.define
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
class VirtualPath(XLUnicodeString): pass

class ShortXLUnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'cch'),
        (pint.uint8_t, 'fHighByte'),
        (lambda s:dyn.block(s['cch'].l.int()*2) if s['fHighByte'].l.int()&0x80 else dyn.block(s['cch'].l.int()), 'rgb'),
#        (lambda s:dyn.clone(pstr.wstring,length=s['cch'].l.int()) if s['fHighByte'].l.int()&0x80 else dyn.clone(pstr.string, length=s['cch'].l.int()), 'rgb'),
    ]

@Record.define
class SupBook(pstruct.type):
    type = 430
    _fields_ = [
        (pint.uint16_t, 'ctab'),
        (pint.uint16_t, 'cch'),
    ]

#DataValidationCriteria
@Record.define
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

class CellRange(pstruct.type):
    class AddressOld(pstruct.type):
        '''XXX: BIFF2 through BIFF5 only'''
        _fields_ = [(pint.uint16_t,'first_row'),(pint.uint16_t,'last_row'),(pint.uint8_t,'first_column'),(pint.uint8_t,'last_column')]

    class Address(pstruct.type):
        _fields_ = [(pint.uint16_t,'first_row'),(pint.uint16_t,'last_row'),(pint.uint16_t,'first_column'),(pint.uint16_t,'last_column')]

    _fields_ = [
        (pint.uint16_t, 'number'),
        (lambda s: dyn.array(s.Address, int(s['number'].l)), 'addresses'),
    ]

@Record.define
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

    class __string(pstruct.type):
        def __unicode(self):
            if int(self['unicode_flag'].l):
                return dyn.clone(pstr.wstring, length=int(self['length'].l))
            return dyn.clone(pstr.string, length=int(self['length'].l))

        _fields_ = [
            (pint.uint16_t, 'length'),
            (pint.uint8_t, 'unicode_flag'),
            (__unicode, 'string'),
        ]

    class __formula(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'size'),
            (pint.uint16_t, 'reserved'),
            (lambda s: dyn.block(int(s['size'].l)), 'data'),
        ]

    _fields_ = [
        (__dwDvFlags, 'dwDvFlags'),
        (__string, 'prompt_title'),
        (__string, 'error_title'),
        (__string, 'prompt_text'),
        (__string, 'error_text'),

        (__formula, 'first'),
        (__formula, 'second'),

        (CellRange, 'addresses'),
    ]

###
@Record.define
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
        _values_ = [
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

###
@Record.define
class Font(pstruct.type):
    type = 0x0031
    type = 49
    _fields_ = [
        (pint.uint16_t, 'dyHeight'),
        (pint.uint16_t, 'flags'),
        (pint.uint16_t, 'icv'),
        (pint.uint16_t, 'bls'),
        (pint.uint16_t, 'sss'),
        (pint.uint8_t, 'uls'),
        (pint.uint8_t, 'vFamily'),
        (pint.uint8_t, 'bCharSet'),
        (pint.uint8_t, 'unused3'),
        (ShortXLUnicodeString, 'fontName'),
    ]

@Record.define
class BookBool(pbinary.struct):
    type = 0xda
    type = 218
    _fields_ = [
        (1, 'fNoSaveSup'),
        (1, 'reserved1'),
        (1, 'fHasEnvelope'),
        (1, 'fEnvelopeVisible'),
        (1, 'fEnvelopeInitDone'),
        (2, 'grUpdateLinks'),
        (1, 'unused'),
        (1, 'fHideBorderUnselLists'),
        (7, 'reserved2'),
    ]

@Record.define
class RefreshAll(pint.enum, pint.uint16_t):
    type = 0x1b7
    type = 439
    _values_ = [
        (0, 'noforce'),(1, 'force'),
    ]

class Boolean(pint.enum):
    _values_ = [
        (0, 'False'),(1, 'True'),
    ]

@Record.define
class CalcPrecision(Boolean, pint.uint16_t):
    type = 0xe
    type = 14

@Record.define
class Date1904(pint.enum,pint.uint16_t):
    type = 0x22
    type = 34

    _values_ = [
        (0, '1900 date system'),
        (1, '1904 date system'),
    ]

class HideObjEnum(pint.enum):
    _values_ = [
        (0, 'SHOWALL'),
        (1, 'SHOWPLACEHOLDER'),
        (2, 'HIDEALL'),
    ]

@Record.define
class HideObj(HideObjEnum, pint.uint16_t):
    type = 0x8d
    type = 141

@Record.define
class Backup(Boolean, pint.uint16_t):
    type = 0x40
    type = 64

class TabIndex(pint.uint16_t): pass

@Record.define
class Password(pint.uint16_t):
    type = 0x13
    type = 19

@Record.define
class Protect(Boolean, pint.uint16_t):
    type = 0x12
    type = 18

@Record.define
class WinProtect(Boolean, pint.uint16_t):
    type = 0x19
    type = 25

@Record.define
class WriteAccess(pstruct.type):
    type = 0x5c
    type = 92
    _fields_ = [
        (XLUnicodeString, 'userName'),
        (lambda s: dyn.block(112-s['userName'].l.size()), 'unused')
    ]

@Record.define
class InterfaceHdr(pint.uint16_t):
    type = 0xe1
    type = 225

@Record.define
class InterfaceEnd(pint.uint16_t):
    type = 0xe2
    type = 226

@Record.define
class Mms(pstruct.type):
    type = 0xc1
    type = 193
    _fields_ = [
        (pint.uint8_t, 'reserved1'),
        (pint.uint8_t, 'reserved2'),
    ]

@Record.define
class CodePage(pint.uint16_t):
    type = 0x42
    type = 66

@Record.define
class Excel9File(ptype.empty):
    type = 0x1c0
    type = 448

@Record.define
class Window1(pstruct.type):
    type = 61
    type = 0x3d
    _fields_ = [
        (pint.int16_t, 'xWn'),
        (pint.int16_t, 'yWn'),
        (pint.int16_t, 'dxWn'),
        (pint.int16_t, 'dyWn'),
        (pint.uint16_t, 'flags'),
        (TabIndex, 'itabCur'),
        (TabIndex, 'itabFirst'),
        (pint.uint16_t, 'ctabSel'),
        (pint.uint16_t, 'wTabRatio'),
    ]

@Record.define
class CalcMode(pint.enum, pint.uint16_t):
    type = 0xd
    type = 13
    _fields_ = [
        (0,'Manual'),(1,'Automatic'),(2,'No Tables'),
    ]

@Record.define
class BuiltInFnGroupCount(pint.uint16_t):
    type = 156
    type = 0x9c

@Record.define
class Prot4Rev(Boolean, pint.uint16_t):
    type = 431
    type = 0x1af

@Record.define
class Prot4RevPass(pint.uint16_t):
    type = 444
    type = 0x1bc

@Record.define
class DSF(pint.uint16_t):
    type = 353
    type = 0x161

@Record.define
class MSODRAWING(art.SpContainer):
    type = 0x00ec
    type = 236

@Record.define
class EOF(pstruct.type):
    type = 10
    _fields_ = []

@Record.define
class Blank(Cell):
    type = 513
    type = 0x201

#@Record.define     # FIXME
class Row(pstruct.type):
    type = 520
    type = 0x208

    class __flags(pbinary.struct):
        _fields_ = [
            (3, 'iOutLevel'),
            (1, 'reserved2'),
            (1, 'fCollapsed'),
            (1, 'fDyZero'),
            (1, 'fUnsynced'),
            (1, 'fGhostDirty'),
            (8, 'reserved3'),
            (12, 'ixfe_val'),
            (1, 'fExAsc'),
            (1, 'fExDes'),
            (1, 'fPhonetic'),
            (1, 'unused2'),
        ]

    _fields_ = [
        (Rw, 'rw'),
        (pint.uint32_t, 'colMic'),
        (pint.uint32_t, 'colMac'),
        (pint.uint32_t, 'miyRw'),
        (pint.uint32_t, 'reserved1'),
        (pint.uint32_t, 'unused1'),
        (__flags, 'flags'),
    ]

###
if True:
    class SerAr(pstruct.type):
        _fields_ = [
            (pint.uint32_t,'reserved'),
            (lambda s: SerArType.get(s['reserved1'].l.int()), 'Ser'),
        ]

    class SerArType(ptype.definition):
        cache = {}

    @SerArType.define
    class SerBool(pstruct.type):
        type = 0x04
        type = 4
        _fields_ = [
            (pint.uint8_t,'f'),
            (pint.uint8_t,'reserved2'),
            (pint.uint16_t,'unused1'),
            (pint.uint32_t,'unused2'),
        ]

    class BErr(pint.enum, pint.uint8_t):
        _values_ = [
            ('#NULL!', 0x00),
            ('#DIV/0!', 0x07),
            ('#VALUE!', 0x0f),
            ('#REF!', 0x17),
            ('#NAME?', 0x1d),
            ('#NUM!', 0x24),
            ('#N/A', 0x2a),
        ]

    @SerArType.define
    class SerErr(pstruct.type):
        type = 0x10
        type = 16
        _fields_ = [
            (BErr, 'err'),
            (pint.uint8_t,'reserved2'),
            (pint.uint16_t,'unused1'),
            (pint.uint32_t,'unused2'),
        ]

    @SerArType.define
    class SerNil(pstruct.type):
        type = 0x0
        type = 0
        _fields_ = [
            (pint.uint32_t,'unused1'),
            (pint.uint32_t,'unused2'),
        ]

    @SerArType.define
    class SerNum(pstruct.type):
        type = 0x1
        type = 1
        _fields_ = [
            (Xnum,'xnum'),
        ]

    @SerArType.define
    class SerStr(pstruct.type):
        type = 0x2
        type = 2
        _fields_ = [
            (XLUnicodeString,'string'),
        ]

#@Record.define # FIXME
class CRN(pstruct.type):
    type = 90
    type = 0x5a
    _fields_ = [
        (ColByteU, 'colLast'),
        (ColByteU, 'colFirst'),
        (RwU, 'colLast'),
        (lambda s: dyn.array(SerAr, s['colLast'].l.int()-s['colFirst'].l.int() + 1), 'crnOper'),
    ]

class CellXF(pbinary.struct):
    _fields_ = [
        (3, 'alc'),
        (1, 'fWrap'),
        (3, 'alcV'),
        (1, 'fJustLast'),

        (8, 'trot'),
        (4, 'cIndent'),
        (1, 'fShrinkToFit'),
        (1, 'reserved1'),
        (2, 'iReadOrder'),

        (2, 'reserved2'),
        (1, 'fAtrNum'),
        (1, 'fAtrFnt'),
        (1, 'fAtrAlc'),
        (1, 'fAtrBdr'),
        (1, 'fAtrPat'),
        (1, 'fAtrProt'),

        (4, 'dgLeft'),
        (4, 'dgRight'),
        (4, 'dgTop'),
        (4, 'dgBottom'),

        (7, 'icvLeft'),
        (7, 'icvRight'),
        (2, 'grbitDiag'),

        (7, 'icvTop'),
        (7, 'icvBottom'),
        (7, 'icvDiag'),
        (4, 'dgDiag'),
        (1, 'fHasXFExt'),
        (6, 'fls'),

        (7, 'icvFore'),
        (7, 'icvBack'),
        (1, 'fsxButton'),
        (1, 'reserved3'),
    ]

class StyleXF(pbinary.struct):
    _fields_ = [
        (3, 'alc'),
        (1, 'fWrap'),
        (3, 'alcV'),
        (1, 'fJustLast'),

        (8, 'trot'),
        (4, 'cIndent'),
        (1, 'fShrinkToFit'),
        (1, 'reserved1'),
        (2, 'iReadOrder'),

        (8, 'unused'),
        (4, 'dgLeft'),
        (4, 'dgRight'),

        (4, 'dgTop'),
        (4, 'dgBottom'),

        (7, 'icvLeft'),
        (7, 'icvRight'),
        (2, 'grbitDiag'),

        (7, 'icvTop'),
        (7, 'icvBottom'),
        (7, 'icvDiag'),
        (4, 'dgDiag'),
        (1, 'reserved2'),
        (6, 'fls'),

        (7, 'icvFore'),
        (7, 'icvBack'),
        (2, 'reserved3'),
    ]

#@Record.define
class XF(pstruct.type):
    type = 0xe0
    type = 224
    class __flags(pbinary.struct):
        _fields_ = [
            (1, 'fLocked'),
            (1, 'fHidden'),
            (1, 'fStyle'),
            (1, 'f123Prefix'),
            (12, 'ixfParent'),
        ]
    _fields_ = [
        (FontIndex, 'ifnt'),
        (IFmt, 'ifmt'),
        (__flags, 'flags'),
        (lambda s: CellXF if s['flags'].l['fStyle'] == 0 else StyleXF, 'data'),
    ]

#@Record.define # FIXME
class MulRk(pstruct.type):
    type = 0xbd
    type = 189
    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (lambda s: dyn.array(RkRec,s['colLast'].l.int() - s['colFirst'].l.int() + 1), 'rgrkrec'),
        (Col, 'colLast'),
    ]

if False:
    class CellParsedFormula(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'cce'),
            (lambda s: dyn.clone(Rgce, total=s['cce'].l.int()), 'rgce'),     # XXX: page 756. must not contain
            (lambda s: RgbExtra, 'rgcb'),
        ]

if True:
    class PtgDataType(pint.enum, pint.uint8_t):
        _values_ = [
            ('REFERENCE', 0x1),
            ('VALUE', 0x2),
            ('ARRAY', 0x3),
        ]

    class PtgType(ptype.definition):
        cache = {}

    class Ptg(pstruct.type):
        class __type(pbinary.struct):
            _fields_=[(7,'ptg'),(1,'reserved0')]

        def __value(self):
            t = self['type'].l['ptg']
            return PtgType.lookup(t)

        _fields_ = [
            (__type, 'type'),
            (__value, 'value'),
        ]

    @PtgType.define
    class PtgStr(ShortXLUnicodeString):
        type = 0x17

    class PtgExtraArray(pstruct.type):
        _fields_ = [
            (DColByteU, 'cols'),
            (DRw, 'rows'),
            (lambda s: dyn.array(SerAr, s['cols'].l.int() * s['rows'].l.int()), 'array'),
        ]

    class PtgArray(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'unused1'),
            (pint.uint16_t, 'unused2'),
            (pint.uint32_t, 'unused3'),
        ]
        ACTUAL_PTG_SIZE = 15
        extra = PtgExtraArray   ###

    @PtgType.define
    class PtgArray_REFERENCE(PtgArray):
        type = 2
    @PtgType.define
    class PtgArray_VALUE(PtgArray):
        type = 4
    @PtgType.define
    class PtgArray_ARRAY(PtgArray):
        type = 6

    class PtgRef(RgceLoc):
        ACTUAL_PTG_SIZE = 7
    @PtgType.define
    class PtgRef_REFERENCE(PtgRef):
        type = 34
    @PtgType.define
    class PtgRef_VALUE(PtgRef):
        type = 36
    @PtgType.define
    class PtgRef_ARRAY(PtgRef):
        type = 38

    class PtgArea(RgceArea):
        ACTUAL_PTG_SIZE = 13
    @PtgType.define
    class PtgArea_REFERENCE(PtgArea):
        type = 42
    @PtgType.define
    class PtgArea_VALUE(PtgArea):
        type = 44
    @PtgType.define
    class PtgArea_ARRAY(PtgArea):
        type = 46

    class PtgRefErr(pstruct.type):
        ACTUAL_PTG_SIZE = 7
        _fields_ = [
            (pint.uint16_t, 'unused1'),
            (pint.uint16_t, 'unused2'),
        ]

    @PtgType.define
    class PtgRefErr_REFERENCE(PtgRefErr):
        type = 82
    @PtgType.define
    class PtgRefErr_VALUE(PtgRefErr):
        type = 84
    @PtgType.define
    class PtgRefErr_ARRAY(PtgRefErr):
        type = 86

    class PtgAreaErr(pstruct.type):
        ACTUAL_PTG_SIZE = 13
        _fields_ = [
            (pint.uint16_t, 'unused1'),
            (pint.uint16_t, 'unused2'),
            (pint.uint16_t, 'unused3'),
            (pint.uint16_t, 'unused4'),
        ]

    @PtgType.define
    class PtgAreaErr_REFERENCE(PtgAreaErr):
        type = 138
    @PtgType.define
    class PtgAreaErr_VALUE(PtgAreaErr):
        type = 140
    @PtgType.define
    class PtgAreaErr_ARRAY(PtgAreaErr):
        type = 142

    class PtgRefN(RgceLocRel):
        ACTUAL_PTG_SIZE = 7
        
    @PtgType.define
    class PtgRefN_REFERENCE(PtgRefN):
        type = 98
    @PtgType.define
    class PtgRefN_VALUE(PtgRefN):
        type = 100
    @PtgType.define
    class PtgRefN_ARRAY(PtgRefN):
        type = 102

    class PtgAreaN(RgceAreaRel):
        ACTUAL_PTG_SIZE = 13
    @PtgType.define
    class PtgAreaN_REFERENCE(PtgAreaN):
        type = 106
    @PtgType.define
    class PtgAreaN_VALUE(PtgAreaN):
        type = 108
    @PtgType.define
    class PtgAreaN_ARRAY(PtgAreaN):
        type = 110

    class RevItab(pstruct.type):
        class __type(pint.enum, pint.uint8_t):
            _values_ = [
                (0x00, 'same-workbook'),
                (0x01, 'diff-workbook'),
                (0x02, 'prev-revitab'),
                (0x03, 'missing-sheet'),
            ]
        _fields_ = [
            (__type, 'type'),
            (pint.uint16_t, 'tabid'),
            (XLUnicodeString, 'sheet'),
        ]

    class RevExtern(pstruct.type):
        class __book(pstruct.type):
            _fields_ = [
                (pint.uint8_t, 'type'),
                (lambda s: pint.uint8_t if s['type'].l.int() == 1 else VirtualPath, 'book'),
            ]
        _fields_ = [
            (__book, 'book'),
            (RevItab, 'itabFirst'),
            (RevItab, 'itabLast'),
        ]

    class PtgRef3d(pstruct.type):
        ACTUAL_PTG_SIZE = 9
        def __loc(self):
            if self.parent.__class__ == NameParsedFormula:
                return RgceLocRel
            return RgceLoc

        _fields_ = [
            (XtiIndex, 'ixti'),
            (__loc, 'loc'),
        ]
        extra = RevExtern

    @PtgType.define
    class PtgRef3d_REFERENCE(PtgRef3d):
        type = 210
    @PtgType.define
    class PtgRef3d_VALUE(PtgRef3d):
        type = 212
    @PtgType.define
    class PtgRef3d_ARRAY(PtgRef3d):
        type = 214

    class PtgArea3d(pstruct.type):
        ACTUAL_PTG_SIZE = 15
        def __area(self):
            if self.parent.__class__ == NameParsedFormula:
                return RgceAreaRel
            return RgceArea

        _fields_ = [
            (XtiIndex, 'ixt'),
            (__area, 'area'),
        ]
        extra = RevExtern

    @PtgType.define
    class PtgArea3d_REFERENCE(PtgArea3d):
        type = 218
    @PtgType.define
    class PtgArea3d_VALUE(PtgArea3d):
        type = 220
    @PtgType.define
    class PtgArea3d_ARRAY(PtgArea3d):
        type = 222

    class PtgRefErr3d(pstruct.type):
        ACTUAL_PTG_SIZE = 9
        _fields_ = [
            (XtiIndex, 'ixti'),
            (pint.uint16_t, 'unused1'),
            (pint.uint16_t, 'unused2'),
        ]
        extra = RevExtern

    @PtgType.define
    class PtgRefErr3d_REFERENCE(PtgRefErr3d):
        type = 226
    @PtgType.define
    class PtgRefErr3d_VALUe(PtgRefErr3d):
        type = 228
    @PtgType.define
    class PtgRefErr3d_ARRAY(PtgRefErr3d):
        type = 230

    class PtgAreaErr3d(pstruct.type):
        ACTUAL_PTG_SIZE = 16
        _fields_ = [
            (XtiIndex, 'ixti'),
            (pint.uint16_t, 'unused1'),
            (pint.uint16_t, 'unused2'),
            (pint.uint16_t, 'unused3'),
            (pint.uint16_t, 'unused4'),
        ]
        extra = RevExtern

    @PtgType.define
    class PtgAreaErr3d_REFERENCE(PtgAreaErr3d):
        type = 234
    @PtgType.define
    class PtgAreaErr3d_VALUE(PtgAreaErr3d):
        type = 236
    @PtgType.define
    class PtgAreaErr3d_ARRAY(PtgAreaErr3d):
        type = 238

if False:
    class Rgce(parray.terminated):
        _object_ = Ptg

        def isTerminator(self, value):
            size = reduce(lambda x,y: x+y.ACTUAL_PTG_SIZE,self.v, 0)
            return size <= self.total

    # FIXME
    class RgbExtra(parray.infinite):
        def _object_(self):
            p = self.parent['rgce']
            for x in p:
                if x.hasattr('extra'):
                    yield x.extra
                continue
            return

class Icv(pint.uint16_t): pass
class IcvXF(pint.uint16_t): pass

if False:
    class NameParsedFormula(pstruct.type):
        # XXX: page 823 rgce must not contain
        _fields_ = [
            (Rgce, 'rgce'),
            (RgbExtra, 'rgcb'),
        ]

class FormulaValue(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'byte1'),
        (pint.uint16_t, 'byte2'),
        (pint.uint16_t, 'byte3'),
        (pint.uint16_t, 'byte4'),
        (pint.uint16_t, 'byte5'),
        (pint.uint16_t, 'byte6'),
        (pint.uint32_t, 'fExprO'),
    ]

if False:
    #@Record.define
    class Formula(pstruct.type):
        type = 0x6
        type = 6

        class __flags(pbinary.struct):
            _fields_ = [
                (1,'fAlwaysCalc'),
                (1, 'reserved1'),
                (1, 'fFill'),
                (1, 'fShrFmla'),
                (1, 'reserved2'),
                (1, 'fClearErrors'),
                (10, 'reserved3'),
            ]

        _fields_ = [
            (Cell, 'cell'),
            (FormulaValue, 'val'),
            (__flags, 'flags'),
            (dyn.block(4), 'chn'),  # XXX: application-specific
            (CellParsedFormula, 'formula'),
        ]

#@Record.define
class XCT(pstruct.type):
    type = 89
    type = 0x59
    _fields_ = [
        (pint.int16_t, 'ccrn'),
        (pint.uint16_t, 'itab'),
    ]

class BuiltInStyle(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'istyBuiltIn'),
        (pint.uint8_t, 'iLevel'),
    ]

#@Record.define # FIXME
class Style(pstruct.type):
    type = 659
    type = 0x293

    class __flags(pbinary.struct):
        _fields_ = [
            (12,'ixfe'),
            (3, 'unused'),
            (1, 'fBuiltIn'),
        ]

    _fields_ = [
        (__flags, 'flags'),
        (lambda s: BuiltInStyle if s['flags'].l['fBuiltIn'] else XLUnicodeString, 'data')
    ]

class XColorType(pint.enum, pint.uint32_t):
    _values_ = [
        ('XCLRAUTO', 0x00000000),
        ('XCLRINDEXED', 0x00000001),
        ('XCLRRGB', 0x00000002),
        ('XCLRTHEMED', 0x00000003),
        ('XCLRNINCHED', 0x00000004),
    ]

class FullColorExt(pstruct.type):
    def __xclrValue(self):
        t = self['xclrType'].l.int()
        if t == 1:
            return IcvXF
        if t == 2:
            return LongRGBA
        if t == 3:
            return ColorTheme
        raise NotImplementedError(t)
        
    _fields_ = [
        (XColorType, 'xclrType'),
        (pint.uint16_t, 'nTintShade'),
        (__xclrValue, 'xclrValue'),
        (pint.uint64_t, 'unused'),
    ]

class ColorTheme(pint.enum, pint.uint32_t):
    _values_ = [
        ('Dark 1', 0x00000000),
        ('Light 1', 0x00000001),
        ('Dark 2', 0x00000002),
        ('Light 2', 0x00000003),
        ('Accent 1', 0x00000004),
        ('Accent 2', 0x00000005),
        ('Accent 3', 0x00000006),
        ('Accent 4', 0x00000007),
        ('Accent 5', 0x00000008),
        ('Accent 6', 0x00000009),
        ('Hyperlink', 0x0000000A),
        ('Followed hyperlink', 0x0000000B),
    ]

class XFPropGradient(pstruct.type):
    class __type(pint.enum, pint.uint32_t):
        _values_ = [ (0, 'linear'), (1,'rectangular') ]
    _fields_ = [
        (__type, 'type'),
        (Xnum, 'numDegree'),
        (Xnum, 'numFillToLeft'),
        (Xnum, 'numFillToRight'),
        (Xnum, 'numFillToTop'),
        (Xnum, 'numFillToBottom'),
    ]

class GradStop(pstruct.type):
    def __xclrValue(self):
        t = self['xclrType'].l.int()
        if t == 1:
            return IcvXF
        if t == 2:
            return LongRGBA
        if t == 3:
            return ColorTheme
        raise NotImplementedError(t)

    _fields_ = [
        (XColorType, 'xclrType'),
        (__xclrValue, 'xclrValue'),
        (Xnum, 'numPosition'),
    ]

class XFExtGradient(pstruct.type):
    _fields_ = [
        (XFPropGradient, 'gradient'),
        (pint.uint32_t, 'cGradSTops'),
        (lambda s: dyn.array(GradStop, s['cGradStops'].l.int()), 'rgGradStops'),
    ]

class ExtPropType(ptype.definition):
    cache = {}
@ExtPropType.define
class ExtType_Foreground_Color(FullColorExt):
    type = 4
@ExtPropType.define
class ExtType_Background_Color(FullColorExt):
    type = 5
@ExtPropType.define
class ExtType_GradientFill(XFExtGradient):
    type = 6
@ExtPropType.define
class ExtType_TopBorderColor(FullColorExt):
    type = 7
@ExtPropType.define
class ExtType_BottomBorderColor(FullColorExt):
    type = 8
@ExtPropType.define
class ExtType_LeftBorderColor(FullColorExt):
    type = 9
@ExtPropType.define
class ExtType_RightBorderColor(FullColorExt):
    type = 10
@ExtPropType.define
class ExtType_DiagonalBorderColor(FullColorExt):
    type = 11
@ExtPropType.define
class ExtType_TextColor(FullColorExt):
    type = 13
@ExtPropType.define
class ExtType_FontScheme(pint.enum, pint.uint16_t):
    type = 14
    _values_ = [(0,'default'), (1,'default,bold'), (2,'default,italic'), (3,'default,bold,italic')]
@ExtPropType.define
class ExtType_TextIndentation(pint.uint16_t):
    type = 15

class ExtProp(pstruct.type):
    class __extType(pint.enum,pint.uint16_t):
        _values_ = [
        ]

    _fields_ = [
        (__extType, 'extType'),
        (pint.uint32_t, 'cb'),
        (lambda s: ExtPropType.get(s['extType'].l.int(), blocksize=lambda:s['cb'].l.int()-6), 'extPropData')
    ]

Record.define
class XFExt(pstruct.type):
    type = 0x87d
    type = 2173
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint16_t, 'reserved1'),
        (XFIndex, 'ixfe'),
        (pint.uint16_t, 'reserved2'),
        (pint.uint16_t, 'cexts'),
        (lambda s: dyn.array(ExtProp, s['cexts'].l.int()), 'rgExt'),
    ]

#@Record.define # FIXME
class Format(pstruct.type):
    type = 0x41e
    type = 1054
    _fields_ = [
        (pint.uint16_t, 'ifmt'),
        (XLUnicodeString, 'stFormat'),
    ]

#######
Record.update(art.Record)
Record.update(graph.Record)

if __name__ == '__main__':
    import sys
    import ptypes,office.excel as excel
    filename, = sys.argv[1:]
    ptypes.setsource( ptypes.file(filename) )

    y = ptypes.debugrecurse(excel.File)()
    z = excel.File()
    z = z.l

    streams = z

    if False:
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

    if z.source.size() == z.size():
        print 'successfully parsed %d streams of 0x%x bytes from %s'% (len(z), z.size(), filename)
        print 'z: found %d records'% reduce(lambda x,y:x+len(y),z,0)
    else:
        print 'unsuccessfully parsed %d biffsubstreams from %s (%d != %d)'% (len(z), filename, z.size(), z.source.size())
        print 'z: found %d records'% reduce(lambda x,y:x+len(y),z,0)

