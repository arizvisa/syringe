from ptypes import *
import art,graph
from . import *

@Record.define
class RT_Excel(ptype.definition):
    type,cache = __name__,{}

class RecordGeneral(RecordGeneral):
    class Header(pstruct.type):
        _fields_ = [
            (pint.littleendian(pint.uint16_t), 'type'),
            (pint.littleendian(pint.uint16_t), 'length'),
        ]
        def Type(self):
            return RT_Excel.type
        def Instance(self):
            return self['type'].num()
        def Length(self):
            return self['length'].num()

class RecordContainer(RecordContainer): _object_ = RecordGeneral

### primitive types
class USHORT(pint.uint16_t): pass
class Rw(pint.uint16_t): pass
class ColByteU(pint.uint8_t): pass
class RwU(pint.uint16_t): pass
class ColU(pint.uint16_t): pass
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
        if value['header'].Instance() == EOF.type:
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
        bof = self[0]['data']
        try:
            return '%s -> %d records -> document type %r'% (self.name(), len(self), bof['dt'])
        except (TypeError,KeyError):
            pass
        return '%s -> %d records -> document type %r'% (self.name(), len(self), bof.serialize())

class File(File):
    _object_ = BiffSubStream

    def details(self):
        return '%s streams=%d'%(self.name(), len(self))

###
@RT_Excel.define
class CatSerRange(pstruct.type):
    type = 0x1020
    type = 4128

    class flags(pbinary.struct):
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
        (flags, 'catFlags')
    ]

###
@RT_Excel.define
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

class FrtHeaderOld(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rt'),
        (FrtFlags, 'grbitFrt'),
    ]

@RT_Excel.define
class MTRSettings(pstruct.type):
    type = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'fMTREnabled'),
        (pint.uint32_t, 'fUserSetThreadCount'),
        (pint.uint32_t, 'cUserThreadCount')
    ]
###
@RT_Excel.define
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
@RT_Excel.define
class LabelSst(pstruct.type):
    type = 253
    _fields_ = [
        (Cell, 'cell'),
        (pint.uint32_t, 'isst')
    ]
###
@RT_Excel.define
class RK(pstruct.type):
    type = 638
    type = 0x273
    _fields_ = [
        (pint.uint16_t, 'rw'),
        (pint.uint16_t, 'col'),
        (RkRec, 'rkrec')
    ]

#@RT_Excel.define
class MulBlank(pstruct.type):
    type = 190
    type = 0xbe

    def __rgixfe(self):
        sz = self.size() + Col().size()
        count = (self.blocksize()-sz) / IXFCell().size()
        return dyn.array(IXFCell, count)

    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (__rgixfe, 'rgixfe'),
        (Col, 'colLast')
    ]

###
@RT_Excel.define
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

@RT_Excel.define
class MergeCells(pstruct.type):
    type = 229
    _fields_ = [
        (pint.uint16_t, 'cmcs'),
        (lambda s: dyn.array(Ref8, int(s['cmcs'].li)), 'rgref')
    ]
###
@RT_Excel.define
class CrtLayout12(pstruct.type):
    class CrtLayout12Auto(pbinary.struct):
        _fields_ = [
            (1, 'unused'),
            (4, 'autolayouttype'),
            (11, 'reserved')
        ]

    type = 2205
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint32_t, 'dwCheckSum'),
        (CrtLayout12Auto, 'auto'),
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
@RT_Excel.define
class Frame(pstruct.type):
    class FrameAuto(pbinary.struct):
        _fields_ = [
            (1, 'fAutoSize'),
            (1, 'fAutoPosition'),
            (14, 'reserved')
        ]

    type = 4146
    _fields_ = [
        (pint.uint16_t, 'frt'),
        (FrameAuto, 'f')
    ]

###
@RT_Excel.define
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
        (lambda s: dyn.clone(pstr.wstring, length=[s.length, s.length*2][int(s['fHighByte'].li)>>7]), 'rgb')
    ]

class XLUnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cch'),
        (pint.uint8_t, 'fHighByte'),
        (lambda s: dyn.clone(pstr.wstring, length=[int(s['cch'].li), int(s['cch'])*2][int(s['fHighByte'].li)>>7]), 'rgb')
    ]
class VirtualPath(XLUnicodeString): pass
class XLNameUnicodeString(XLUnicodeString): pass

class ShortXLUnicodeString(pstruct.type):
    def __rgb(self):
        length = self['cch'].li.int()
        high = self['fHighByte'].li.int()
        if high == 0:
            return dyn.clone(pstr.string, length=length)
        elif high == 1:
            return dyn.clone(pstr.wstring,length=length)
        elif high == 7:
            length = self.parent.blocksize()-self.parent.size()
            return dyn.block(length)
        raise NotImplementedError

    _fields_ = [
        (pint.uint8_t, 'cch'),
        (pint.uint8_t, 'fHighByte'),
        (__rgb, 'rgb'),
    ]

@RT_Excel.define
class SupBook(pstruct.type):
    type = 430
    _fields_ = [
        (pint.uint16_t, 'ctab'),
        (pint.uint16_t, 'cch'),
    ]

#DataValidationCriteria
@RT_Excel.define
class DVAL(pstruct.type):
    type = 434
    type = 0x1b2

    class wDviFlags(pbinary.struct):
        _fields_ = [
            (1, 'fWnClosed'),
            (1, 'fWnPinned'),
            (1, 'fCached'),
            (13, 'Reserved')
        ]

    _fields_ = [
        (pbinary.littleendian(wDviFlags), 'wDviFlags'),
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
        (lambda s: dyn.array(s.Address, int(s['number'].li)), 'addresses'),
    ]

@RT_Excel.define
class DV(pstruct.type):
    type = 0x1be
    type = 446

    class dwDvFlags(pbinary.struct):
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

    class string(pstruct.type):
        def __unicode(self):
            if int(self['unicode_flag'].li):
                return dyn.clone(pstr.wstring, length=int(self['length'].li))
            return dyn.clone(pstr.string, length=int(self['length'].li))

        _fields_ = [
            (pint.uint16_t, 'length'),
            (pint.uint8_t, 'unicode_flag'),
            (__unicode, 'string'),
        ]

    class formula(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'size'),
            (pint.uint16_t, 'reserved'),
            (lambda s: dyn.block(int(s['size'].li)), 'data'),
        ]

    _fields_ = [
        (dwDvFlags, 'dwDvFlags'),
        (string, 'prompt_title'),
        (string, 'error_title'),
        (string, 'prompt_text'),
        (string, 'error_text'),

        (formula, 'first'),
        (formula, 'second'),

        (CellRange, 'addresses'),
    ]

###
@RT_Excel.define
class BOF(pstruct.type):
    class Flags(pbinary.struct):
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

    class DocType(pint.enum, pint.uint16_t):
        _values_ = [
            ('workbook', 0x0005),
            ('worksheet', 0x0010),
            ('charsheet', 0x0020),
            ('macrosheet', 0x0040)
        ]

    type = 2057
    _fields_ = [
        (pint.uint16_t, 'vers'),
        (DocType, 'dt'),
        (pint.uint16_t, 'rupBuild'),
        (pint.uint16_t, 'rupYear'),
        (Flags, 'f')
    ]

###
@RT_Excel.define
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

@RT_Excel.define
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

@RT_Excel.define
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

@RT_Excel.define
class CalcPrecision(Boolean, pint.uint16_t):
    type = 0xe
    type = 14

@RT_Excel.define
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

@RT_Excel.define
class HideObj(HideObjEnum, pint.uint16_t):
    type = 0x8d
    type = 141

@RT_Excel.define
class Backup(Boolean, pint.uint16_t):
    type = 0x40
    type = 64

class TabIndex(pint.uint16_t): pass

@RT_Excel.define
class Password(pint.uint16_t):
    type = 0x13
    type = 19

@RT_Excel.define
class Protect(Boolean, pint.uint16_t):
    type = 0x12
    type = 18

@RT_Excel.define
class WinProtect(Boolean, pint.uint16_t):
    type = 0x19
    type = 25

@RT_Excel.define
class WriteAccess(pstruct.type):
    type = 0x5c
    type = 92
    _fields_ = [
        (XLUnicodeString, 'userName'),
        (lambda s: dyn.block(112-s['userName'].li.size()), 'unused')
    ]

@RT_Excel.define
class InterfaceHdr(pint.uint16_t):
    type = 0xe1
    type = 225

@RT_Excel.define
class InterfaceEnd(pint.uint16_t):
    type = 0xe2
    type = 226

@RT_Excel.define
class Mms(pstruct.type):
    type = 0xc1
    type = 193
    _fields_ = [
        (pint.uint8_t, 'reserved1'),
        (pint.uint8_t, 'reserved2'),
    ]

@RT_Excel.define
class CodePage(pint.uint16_t):
    type = 0x42
    type = 66

@RT_Excel.define
class Excel9File(ptype.type):
    type = 0x1c0
    type = 448

@RT_Excel.define
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

@RT_Excel.define
class CalcMode(pint.enum, pint.uint16_t):
    type = 0xd
    type = 13
    _fields_ = [
        (0,'Manual'),(1,'Automatic'),(2,'No Tables'),
    ]

@RT_Excel.define
class BuiltInFnGroupCount(pint.uint16_t):
    type = 156
    type = 0x9c

@RT_Excel.define
class Prot4Rev(Boolean, pint.uint16_t):
    type = 431
    type = 0x1af

@RT_Excel.define
class Prot4RevPass(pint.uint16_t):
    type = 444
    type = 0x1bc

@RT_Excel.define
class DSF(pint.uint16_t):
    type = 353
    type = 0x161

#@RT_Excel.define
#class MSODRAWING(art.SpContainer):
#    type = 0x00ec
#    type = 236

@RT_Excel.define
class EOF(pstruct.type):
    type = 10
    _fields_ = []

@RT_Excel.define
class Blank(Cell):
    type = 513
    type = 0x201

@RT_Excel.define
class Row(pstruct.type):
    type = 520
    type = 0x208

    class flags(pbinary.struct):
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
        (pint.uint16_t, 'colMic'),
        (pint.uint16_t, 'colMac'),
        (pint.uint16_t, 'miyRw'),
        (pint.uint16_t, 'reserved1'),
        (pint.uint16_t, 'unused1'),
        (flags, 'flags'),
    ]

###
if True:
    class SerAr(pstruct.type):
        _fields_ = [
            (pint.uint32_t,'reserved'),
            (lambda s: SerArType.get(s['reserved1'].li.int()), 'Ser'),
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

@RT_Excel.define
class CRN(pstruct.type):
    type = 90
    type = 0x5a

    _fields_ = [
        (ColByteU, 'colLast'),
        (ColByteU, 'colFirst'),
        (RwU, 'colLast'),
        (lambda s: dyn.array(SerAr, s['colLast'].li.int()-s['colFirst'].li.int() + 1), 'crnOper'),
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

@RT_Excel.define
class XF(pstruct.type):
    type = 0xe0
    type = 224
    class flags(pbinary.struct):
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
        (flags, 'flags'),
        (lambda s: CellXF if s['flags'].li['fStyle'] == 0 else StyleXF, 'data'),
    ]

#@RT_Excel.define # FIXME
class MulRk(pstruct.type):
    type = 0xbd
    type = 189
    def __rgrkrec(self):
        sz = self.size() + Col().size()
        count = (self.blocksize()-sz) / IXFCell().size()
        return dyn.array(RkRec, count)

    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (__rgrkrec, 'rgrkrec'),
        (Col, 'colLast'),
    ]

if False:
    class CellParsedFormula(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'cce'),
            (lambda s: dyn.clone(Rgce, total=s['cce'].li.int()), 'rgce'),     # XXX: page 756. must not contain
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
        class type(pbinary.struct):
            _fields_=[(7,'ptg'),(1,'reserved0')]

        def __value(self):
            t = self['type'].li['ptg']
            return PtgType.lookup(t)

        _fields_ = [
            (type, 'type'),
            (__value, 'value'),
        ]

    @PtgType.define
    class PtgStr(ShortXLUnicodeString):
        type = 0x17

    class PtgExtraArray(pstruct.type):
        _fields_ = [
            (DColByteU, 'cols'),
            (DRw, 'rows'),
            (lambda s: dyn.array(SerAr, s['cols'].li.int() * s['rows'].li.int()), 'array'),
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
        class type(pint.enum, pint.uint8_t):
            _values_ = [
                (0x00, 'same-workbook'),
                (0x01, 'diff-workbook'),
                (0x02, 'prev-revitab'),
                (0x03, 'missing-sheet'),
            ]
        _fields_ = [
            (type, 'type'),
            (pint.uint16_t, 'tabid'),
            (XLUnicodeString, 'sheet'),
        ]

    class RevExtern(pstruct.type):
        class book(pstruct.type):
            _fields_ = [
                (pint.uint8_t, 'type'),
                (lambda s: pint.uint8_t if s['type'].li.int() == 1 else VirtualPath, 'book'),
            ]
        _fields_ = [
            (book, 'book'),
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
    # FIXME: parsething parsing
    class Rgce(parray.terminated):
        _object_ = Ptg

        def isTerminator(self, value):
            size = reduce(lambda x,y: x+y.ACTUAL_PTG_SIZE,self.v, 0)
            return size <= self.total

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
    #@RT_Excel.define
    class Formula(pstruct.type):
        type = 0x6
        type = 6

        class flags(pbinary.struct):
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
            (flags, 'flags'),
            (dyn.block(4), 'chn'),  # XXX: application-specific
            (CellParsedFormula, 'formula'),
        ]

#@RT_Excel.define
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

#@RT_Excel.define # FIXME
class Style(pstruct.type):
    type = 659
    type = 0x293

    class flags(pbinary.struct):
        _fields_ = [
            (1, 'fBuiltIn'),
            (3, 'unused'),
            (12,'ixfe'),
        ]
    flags = pbinary.littleendian(flags)

    _fields_ = [
        (flags, 'flags'),
        (lambda s: BuiltInStyle if s['flags'].li['fBuiltIn'] else ptype.undefined, 'builtInData'),
        (lambda s: XLUnicodeString if not s['flags'].li['fBuiltIn'] else ptype.undefined, 'user')
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
        t = self['xclrType'].li.int()
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
    class type(pint.enum, pint.uint32_t):
        _values_ = [ (0, 'linear'), (1,'rectangular') ]
    _fields_ = [
        (type, 'type'),
        (Xnum, 'numDegree'),
        (Xnum, 'numFillToLeft'),
        (Xnum, 'numFillToRight'),
        (Xnum, 'numFillToTop'),
        (Xnum, 'numFillToBottom'),
    ]

class GradStop(pstruct.type):
    def __xclrValue(self):
        t = self['xclrType'].li.int()
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
        (lambda s: dyn.array(GradStop, s['cGradStops'].li.int()), 'rgGradStops'),
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
    class extType(pint.enum,pint.uint16_t):
        _values_ = [
            ('interior-fg-color', 0x0004),
            ('interior-bg-color', 0x0005),
            ('interior-igradient', 0x0006),
            ('top-border-color', 0x0007),
            ('bottom-border-color', 0x0008),
            ('left-border-color', 0x0009),
            ('right-border-color', 0x000a),
            ('diagonal-border-color', 0x000b),
            ('text-color', 0x000d),
            ('font-scheme', 0x000e),
            ('text-indent', 0x000f),
        ]

    def __extPropData(self):
        t = self['extType'].li.int()
        # FIXME: http://msdn.microsoft.com/en-us/library/dd906769(v=office.12).aspx
        sz = self['cb'].li.int()
        return ExtPropType.get(self['extType'].li.int(), blocksize=lambda s:sz)

    _fields_ = [
        (extType, 'extType'),
        (pint.uint16_t, 'cb'),
        (__extPropData, 'extPropData'),
    ]

#@RT_Excel.define # FIXME
class XFExt(pstruct.type):
    type = 0x87d
    type = 2173
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint16_t, 'reserved1'),
        (XFIndex, 'ixfe'),
        (pint.uint16_t, 'reserved2'),
        (pint.uint16_t, 'cexts'),
        (lambda s: dyn.array(ExtProp, s['cexts'].li.int()), 'rgExt'),
    ]

#@RT_Excel.define # FIXME
class Format(pstruct.type):
    type = 0x41e
    type = 1054
    _fields_ = [
        (pint.uint16_t, 'ifmt'),
        (XLUnicodeString, 'stFormat'),
    ]

@RT_Excel.define
class SerAuxErrBar(pstruct.type):
    type = 4187
    type = 0x105b

    class sertm(pint.enum, pint.uint8_t):
        _values_ = [
            ('horizontal+', 1),
            ('horizontal-', 2),
            ('vertical+', 3),
            ('vertical-', 4),
        ]

    class ebsrc(pint.enum, pint.uint8_t):
        _values_ = [
            ('percentage', 1),
            ('fixed', 2),
            ('standard', 3),
            ('custom', 4),
            ('error', 5),
        ]

    class fTeeTop(Boolean, pint.uint8_t): pass

    _fields_ = [
        (sertm, 'sertm'),
        (ebsrc, 'ebsrc'),
        (fTeeTop, 'fTeeTop'),
        (pint.uint8_t, 'reserved'),
        (Xnum, 'numValue'),
        (pint.uint16_t, 'cnum'),
    ]

class SharedFeatureType(pint.enum, pint.uint16_t):
    _values_ = [
        ('ISFPROTECTION', 0x2),
        ('ISFFEC2', 0x3),
        ('ISFFACTOID', 0x4),
        ('ISFLIST', 0x5),
    ]

class Ref8U(pstruct.type):
    _fields_ = [
        (RwU, 'rwFirst'),
        (RwU, 'rwLast'),
        (ColU, 'colFirst'),
        (ColU, 'colLast'),
    ]

class SDContainer(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'cbSD'),    # GUARD: >20
        (lambda s: dyn.block(s['cbSD'].li.int()), 'sd'),
    ]

class FeatProtection(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'fSD'),
        (pint.uint32_t, 'wPassword'),
        (XLUnicodeString, 'stTitle'),
        (SDContainer, 'sdContainer'),
    ]

class FFErrorCheck(pbinary.struct):
    _fields_ = [
        (1, 'ffecCalcError'),
        (1, 'ffecEmptyCellRef'),
        (1, 'ffecNumStoredAsText'),
        (1, 'ffecInconsistRange'),
        (1, 'ffecInconsistFmla'),
        (1, 'ffecTextDateInsuff'),
        (1, 'ffecUnprotFmla'),
        (1, 'ffecDateValidation'),
        (24, 'reserved'),
    ]

class FeatFormulaErr2(FFErrorCheck): pass

class Property(pstruct.type):
    _fields_ = [(pint.uint32_t,'keyIndex'),(pint.uint32_t,'valueIndex')]

class PropertyBag(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'id'),
        (pint.uint16_t, 'cProp'),
        (pint.uint16_t, 'cbUnknown'),
        (lambda s: dyn.array(Property, s['cProp'].li.int()), 'properties'),
    ]

class FactoidData(pstruct.type):
    class flags(pbinary.struct):
        _fields_ = [(1,'fDelete'),(1,'fXMLBased'),(6,'reserved')]

    _fields_ = [
        (flags, 'flags'),
        (PropertyBag, 'propertyBag'),
    ]

class FeatSmartTag(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'hashValue'),
        (pint.uint8_t, 'cSmartTags'),
        (lambda s: dyn.array(FactoidData,s['cSmartTags'].li.int()), 'rgFactoid'),
    ]

#@RT_Excel.define
class Feat(pstruct.type):
    type = 0x868
    type = 2152
    def __rgbFeat(self):
        isf = self['isf'].l
        if isf['ISFPROTECTION']:
            return FeatProtection
        elif isf['ISFFEC2']:
            return FeatFormulaErr2
        elif isf['ISFFACTOID']:
            return FeatSmartTag
        raise NotImplementedError(isf)

    _fields_ =[
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (pint.uint8_t, 'reserved1'),
        (pint.uint32_t, 'reserved2'),
        (pint.uint16_t, 'cref'),
        (pint.uint32_t, 'cbFeatData'),
        (pint.uint16_t, 'reserved3'),
        (lambda s: dyn.array(Reg8U, s['cref'].li.int()), 'refs'),
        (__rgbFeat, 'rgbFeat'),
    ]

class EnhancedProtection(pbinary.struct):
    _fields_ = [
        (1, 'iprotObjects'),
        (1, 'iprotScenarios'),
        (1, 'iprotFormatCells'),
        (1, 'iprotFormatColumns'),
        (1, 'iprotFormatRows'),
        (1, 'iprotInsertColumns'),
        (1, 'iprotInsertRows'),
        (1, 'iprotInsertHyperlinks'),
        (1, 'iprotDeleteColumns'),
        (1, 'iprotDeleteRows'),
        (1, 'iprotSelLockedCells'),
        (1, 'iprotSort'),
        (1, 'iprotAutoFilter'),
        (1, 'iprotPivotTables'),
        (1, 'iprotSelUnlockedCells'),
        (17, 'reserved'),
    ]

@RT_Excel.define
class FeatHdr(pstruct.type):
    type = 2151
    type = 0x867
    def __rgbHdrData(self):
        isf = self['isf'].l
        if self['cbHdrData'].li.int() == 0:
            return ptype.type
        if isf['ISFPROTECTION']:
            return EnhancedProtection
        elif isf['ISFFEC2']:
            return ptype.type
        raise NotImplementedError(isf)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (pint.uint8_t, 'reserved'),
        (pint.uint32_t, 'cbHdrData'),
        (__rgbHdrData, 'rgbHdrData'),
    ]

@RT_Excel.define
class FeatHdr11(pstruct.type):
    type = 2161
    type = 0x871
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'), # GUARD: ISFLIST
        (pint.uint8_t, 'reserved1'),
        (pint.uint32_t, 'reserved2'),
        (pint.uint32_t, 'reserved3'),
        (pint.uint32_t, 'idListNext'),
        (pint.uint16_t, 'reserved4'),
    ]

class FrtRefHeaderU(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rt'),
        (FrtFlags, 'grbitFrt'),
        (Ref8U, 'ref8'),
    ]


@RT_Excel.define
class ContinueFrt(pstruct.type):
    type = 0x812
    type = 2066

    def __rgb(self):
        return dyn.block(self.blocksize() - self.blocksize())

    _fields_ = [
        (FrtHeaderOld, 'frtHeaderOld'),
        (__rgb, 'rgb'),
    ]

class SourceType(pint.enum, pint.uint32_t):
    _values_ = [
        ('LTRANGE', 0),
        ('LTSHAREPOINT', 1),
        ('LTXML', 2),
        ('LTEXTERNALDATA', 3),
    ]

class LEMMode(pint.enum, pint.uint32_t):
    _values_ = [
        ('LEMNORMAL', 0x00000000),
        ('LEMREFRESHCOPY', 0x00000001),
        ('LEMREFRESHCACHE', 0x00000002),
        ('LEMREFRESHCACHEUNDO', 0x00000003),
        ('LEMREFRESHLOADED', 0x00000004),
        ('LEMREFRESHTEMPLATE', 0x00000005),
        ('LEMREFRESHREFRESH', 0x00000006),
        ('LEMNOINSROWSSPREQUIRED', 0x00000007),
        ('LEMNOINSROWSSPDOCLIB', 0x00000008),
        ('LEMREFRESHLOADDISCARDED', 0x00000009),
        ('LEMREFRESHLOADHASHVALIDATION', 0x0000000A),
        ('LEMNOEDITSPMODVIEW', 0x0000000B),
    ]

class XFExtNoFRT(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'reserved1'),
        (pint.uint16_t, 'reserved2'),
        (pint.uint16_t, 'reserved3'),
        (pint.uint16_t, 'cexts'),
        (lambda s: dyn.array(ExtProp,s['cexts'].li.int()), 'rgExt'),
    ]

# DXFN
#http://msdn.microsoft.com/en-us/library/dd926759(v=office.12).aspx

class DXFN12List(pstruct.type):
    def DXFN(self):
        return ptype.undefined

    _fields_ = [
        (DXFN, 'dxfn'),
        (XFExtNoFRT, 'xfext'),
    ]

class AFDOperRk(pstruct.type):
    _fields_ = [
        (RkNumber, 'rk'),
        (pint.uint32_t, 'unused1'),
    ]

class AFDOperStr(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'unused1'),
        (pint.uint8_t, 'cch'),
        (pint.uint8_t, 'fCompare'),
        (pint.uint8_t, 'reserved1'),
        (pint.uint8_t, 'unused2'),
        (pint.uint32_t, 'unused3'),
    ]

class Bes(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'bBoolErr'),
        (pint.uint8_t, 'fError'),
    ]
class AFDOperBoolErr(pstruct.type):
    _fields_ = [
        (Bes, 'bes'),
        (pint.uint16_t, 'unused1'),
        (pint.uint32_t, 'unused2'),
    ]
class AFDOper(pstruct.type):
    def __wtValue(self):    # XXX
        vt = self['vt'].li.int()
        if vt == 0:
            return dyn.block(8)
        elif vt == 2:
            return AFDOperRK
        elif vt == 4:
            return Xnum
        elif vt == 6:
            return AFDOperStr
        elif vt == 8:
            return AFDOperBoolErr
        elif vt == 0xc:
            return dyn.block(8)
        elif vt == 0xe:
            return dyn.block(8)
        raise NotImplementedError(vt)

    _fields_ = [
        (pint.uint8_t, 'vt'),
        (pint.uint8_t, 'grbitSign'),
        (__wtValue, 'wtValue'),
    ]

class AutoFilter(pstruct.type):
    class flag(pbinary.struct):
        _fields_ = [(2,'wJoin'),(1,'fSimple1'),(1,'fSimple2'),(1,'fTopN'),(1,'fTop'),(1,'fPercent'),(9,'wTopN')]

    def __str1(self):
        return XLUnicodeStringNoCch if self['doper1'].li['vt'].int() == 6 else ptype.type
    def __str2(self):
        return XLUnicodeStringNoCch if self['doper2'].li['vt'].int() == 6 else ptype.type

    _fields_ = [
        (pint.uint16_t, 'iEntry'),
        (flag, 'flag'),
        (AFDOper, 'doper1'),
        (AFDOper, 'doper2'),
        (__str1, 'str1'),
        (__str2, 'str2'),
    ]

class Feat11FdaAutoFilter(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'cbAutoFilter'), #GUARD : <= 2080 bytes
        (pint.uint16_t, 'unused'),
        (lambda s: AutoFilter, 'recAutoFilter'),
    ]

class Feat11XMapEntry2(pstruct.type):
    _fields_ = [
        (pint.uint32_t,'dwMapId'),
        (XLUnicodeString,'rgbXPath'),
    ]

class Feat11XMapEntry(pstruct.type):
    class flags(pbinary.struct):
        _fields_ = [(1,'reserved1'),(1,'fLoadXMap'),(1,'fCanBeSingle'),(1,'reserved2'),(28,'reserved3')]
    _fields_ = [
        (flags, 'flags'),
        (Feat11XMapEntry2, 'details'),
    ]

class Feat11XMap(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'iXmapMac'),
        (lambda s: dyn.array(Feat11XMapEntry,s['iXmapMac'].li.int()), 'rgXmap'),
    ]

class ListParsedArrayFormula(pstruct.type):
    def Rgce(self):
        return dyn.block(self['cce'].li.int())

    def RgbExtra(self):
        bs = self.blocksize()
        sz = self['cce'].size() + self['cce'].li.int()
        return dyn.block(bs-sz)

    _fields_ = [
        (pint.uint16_t, 'cce'),
        (Rgce, 'rgce'),
        (RgbExtra, 'rgcb')
    ]
class ListParsedFormula(pstruct.type):
    def Rgce(self): # FIXME
        return dyn.block(self['cce'].li.int())
    _fields_ = [
        (pint.uint16_t, 'cce'),
        (Rgce, 'rgce'),
    ]

class Feat11Fmla(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cbFmla'),
        (ListParsedFormula, 'rgbFmla'),
    ]

#class Feat11WSSListInfo(ptype.undefined):       # FIXME
#    pass

class CachedDiskHeader(pstruct.type):
    def __strStyleName(self):
        p = self.getparent(type=Feat11FieldDataItem)
        return XLUnicodeString if p['flags']['fSaveStyleName'].int() == 1 else ptype.type

    _fields_ = [
        (pint.uint32_t, 'cbdxfHdrDisk'),
        (DXFN12List, 'rgHdrDisk'),
        (XLUnicodeString, 'strStyleName'),
    ]

####
class Feat11FieldDataItem(pstruct.type):
    class lfdt(pint.enum, pint.uint32_t):
        _fields_ = [
            ('Text', 0x00000001),
            ('Number', 0x00000002),
            ('Boolean', 0x00000003),
            ('Date Time', 0x00000004),
            ('Note', 0x00000005),
            ('Currency', 0x00000006),
            ('Lookup', 0x00000007),
            ('Choice', 0x00000008),
            ('URL', 0x00000009),
            ('Counter', 0x0000000A),
            ('Multiple Choices', 0x0000000B),
        ]
    class lfxidt(pint.enum, pint.uint32_t):
        _fields_ = [
            ('SOMITEM_SCHEMA', 0x00001000),
            ('SOMITEM_ATTRIBUTE', 0x00001001),
            ('SOMITEM_ATTRIBUTEGROUP', 0x00001002),
            ('SOMITEM_NOTATION', 0x00001003),
            ('SOMITEM_IDENTITYCONSTRAINT', 0x00001100),
            ('SOMITEM_KEY', 0x00001101),
            ('SOMITEM_KEYREF', 0x00001102),
            ('SOMITEM_UNIQUE', 0x00001103),
            ('SOMITEM_ANYTYPE', 0x00002000),
            ('SOMITEM_DATATYPE', 0x00002100),
            ('SOMITEM_DATATYPE_ANYTYPE', 0x00002101),
            ('SOMITEM_DATATYPE_ANYURI', 0x00002102),
            ('SOMITEM_DATATYPE_BASE64BINARY', 0x00002103),
            ('SOMITEM_DATATYPE_BOOLEAN', 0x00002104),
            ('SOMITEM_DATATYPE_BYTE', 0x00002105),
            ('SOMITEM_DATATYPE_DATE', 0x00002106),
            ('SOMITEM_DATATYPE_DATETIME', 0x00002107),
            ('SOMITEM_DATATYPE_DAY', 0x00002108),
            ('SOMITEM_DATATYPE_DECIMAL', 0x00002109),
            ('SOMITEM_DATATYPE_DOUBLE', 0x0000210A),
            ('SOMITEM_DATATYPE_DURATION', 0x0000210B),
            ('SOMITEM_DATATYPE_ENTITIES', 0x0000210C),
            ('SOMITEM_DATATYPE_ENTITY', 0x0000210D),
            ('SOMITEM_DATATYPE_FLOAT', 0x0000210E),
            ('SOMITEM_DATATYPE_HEXBINARY', 0x0000210F),
            ('SOMITEM_DATATYPE_ID', 0x00002110),
            ('SOMITEM_DATATYPE_IDREF', 0x00002111),
            ('SOMITEM_DATATYPE_IDREFS', 0x00002112),
            ('SOMITEM_DATATYPE_INT', 0x00002113),
            ('SOMITEM_DATATYPE_INTEGER', 0x00002114),
            ('SOMITEM_DATATYPE_LANGUAGE', 0x00002115),
            ('SOMITEM_DATATYPE_LONG', 0x00002116),
            ('SOMITEM_DATATYPE_MONTH', 0x00002117),
            ('SOMITEM_DATATYPE_MONTHDAY', 0x00002118),
            ('SOMITEM_DATATYPE_NAME', 0x00002119),
            ('SOMITEM_DATATYPE_NCNAME', 0x0000211A),
            ('SOMITEM_DATATYPE_NEGATIVEINTEGER', 0x0000211B),
            ('SOMITEM_DATATYPE_NMTOKEN', 0x0000211C),
            ('SOMITEM_DATATYPE_NMTOKENS', 0x0000211D),
            ('SOMITEM_DATATYPE_NONNEGATIVEINTEGER', 0x0000211E),
            ('SOMITEM_DATATYPE_NONPOSITIVEINTEGER', 0x0000211F),
            ('SOMITEM_DATATYPE_NORMALIZEDSTRING', 0x00002120),
            ('SOMITEM_DATATYPE_NOTATION', 0x00002121),
            ('SOMITEM_DATATYPE_POSITIVEINTEGER', 0x00002122),
            ('SOMITEM_DATATYPE_QNAME', 0x00002123),
            ('SOMITEM_DATATYPE_SHORT', 0x00002124),
            ('SOMITEM_DATATYPE_STRING', 0x00002125),
            ('SOMITEM_DATATYPE_TIME', 0x00002126),
            ('SOMITEM_DATATYPE_TOKEN', 0x00002127),
            ('SOMITEM_DATATYPE_UNSIGNEDBYTE', 0x00002128),
            ('SOMITEM_DATATYPE_UNSIGNEDINT', 0x00002129),
            ('SOMITEM_DATATYPE_UNSIGNEDLONG', 0x0000212A),
            ('SOMITEM_DATATYPE_UNSIGNEDSHORT', 0x0000212B),
            ('SOMITEM_DATATYPE_YEAR', 0x0000212C),
            ('SOMITEM_DATATYPE_YEARMONTH', 0x0000212D),
            ('SOMITEM_DATATYPE_ANYSIMPLETYPE', 0x000021FF),
            ('SOMITEM_SIMPLETYPE', 0x00002200),
            ('SOMITEM_COMPLEXTYPE', 0x00002400),
            ('SOMITEM_PARTICLE', 0x00004000),
            ('SOMITEM_ANY', 0x00004001),
            ('SOMITEM_ANYATTRIBUTE', 0x00004002),
            ('SOMITEM_ELEMENT', 0x00004003),
            ('SOMITEM_GROUP', 0x00004100),
            ('SOMITEM_ALL', 0x00004101),
            ('SOMITEM_CHOICE', 0x00004102),
            ('SOMITEM_SEQUENCE', 0x00004103),
            ('SOMITEM_EMPTYPARTICLE', 0x00004104),
            ('SOMITEM_NULL', 0x00000800),
            ('SOMITEM_NULL_TYPE', 0x00002800),
            ('SOMITEM_NULL_ANY', 0x00004801),
            ('SOMITEM_NULL_ANYATTRIBUTE', 0x00004802),
            ('SOMITEM_NULL_ELEMENT', 0x00004803),
        ]

    class ilta(pint.enum, pint.uint32_t):
        _fields_ = [
            ('No formula (section 2.2.2)', 0x00000000),
            ('Average', 0x00000001),
            ('Count', 0x00000002),
            ('Count Numbers', 0x00000003),
            ('Max', 0x00000004),
            ('Min', 0x00000005),
            ('Sum', 0x00000006),
            ('Standard Deviation', 0x00000007),
            ('Variance', 0x00000008),
            ('Custom formula<157>', 0x00000009),
        ]

    class flags(pbinary.struct):
        _fields_ = [
            (1,'fAutoFilter'),
            (1,'fAutoFilterHidden'),
            (1,'fLoadXmapi'),
            (1,'fLoadFmla'),
            (2,'unused1'),
            (1,'reserved2'),
            (1,'fLoadTotalFmla'),
            (1,'fLoadTotalArray'),
            (1,'fSaveStyleName'),
            (1,'fLoadTotalStr'),
            (1,'fAutoCreateCalcCol'),
            (20, 'unused2'),
        ]

    def __dxfFmtAgg(self):
        sz = self['cbFmtAgg'].li.int()
        return dyn.clone(DXFN12List, blocksize=lambda s:sz)

    def __dxfFmtInsertRow(self):
        sz = self['cbFmtInsertRow'].li.int()
        return dyn.clone(DXFN12List, blocksize=lambda s:sz)

    def __AutoFilter(self):
        tft = self['flag'].l
        return Feat11FdaAutoFilter if tft['fAutoFilter'] else ptype.type

    def __rgXmap(self):
        tft = self['flags'].l
        return Feat11XMap if tft['fLoadXmapi'] else ptype.type

    def __fmla(self):
        tft = self['flags'].l
        return Feat11FdaAutoFilter if tft['fLoadFmla'] else ptype.type

    def __totalFmla(self):
        tft = self['flags'].l
        return ListParsedArrayFormula if tft['fLoadTotalArray'] else ListParsedFormula

    def __strTotal(self):
        tft = self['flags'].l
        return XLUnicodeString if tft['fLoadTotalStr'] else ptype.type

    def __wssInfo(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return Feat11WSSListInfo if lt.int() == 1 else ptype.type

    def __qsif(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return pint.uint32_t if lt.int() == 3 else ptype.type

    def __dskHdrCache(self):
        tft = self.getparent(type=TableFeatureType).l
        return CachedDiskHeader if tft['crwHeader'].int() == 0 and tft['flags']['fSingleCell'].int() == 0 else ptype.type

    _fields_ = [
        (pint.uint32_t, 'idField'),
        (lfdt, 'lfdt'),
        (lfxidt, 'lfxidt'),
        (ilta, 'ilta'),
        (pint.uint32_t, 'cbFmtAgg'),
        (pint.uint32_t, 'istnAgg'),
        (flags, 'flags'),
        (pint.uint32_t, 'cbFmtInsertRow'),
        (XLUnicodeString, 'strFieldName'),
        (XLUnicodeString, 'strCaption'),    # GUARD : fSingleCell === 0
        (__dxfFmtAgg, 'dxfFmtAgg'),
        (__dxfFmtInsertRow, 'dxfFmtInsertRow'),
        (__AutoFilter, 'AutoFilter'),
        (__rgXmap, 'rgXmap'),
        (__fmla, 'fmla'),
        (__totalFmla, 'totalFmla'),
        (__strTotal, 'strTotal'),
        (__wssInfo, 'wssInfo'),
        (__qsif, 'qsif'),   # GUARD: TableFeatureType
        (__dskHdrCache, 'dskHdrCache'),   # GUARD: TableFeatureType
    ]

class Feat11RgSharepointId(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cId'),
        (lambda s: dyn.array(pint.uint32_t, s['cId'].li.int()), 'rgId'),
    ]
class Feat11RgSharepointIdDel(Feat11RgSharepointId): pass
class Feat11RgSharepointIdChange(Feat11RgSharepointId): pass

class Feat11CellStruct(pstruct.type):
    _fields_ = [(pint.uint32_t, 'idxRow'),(pint.uint32_t,'idxField')]

class Feat11RgInvalidCells(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cCellInvalid'),
        (lambda s: dyn.array(Feat11CellStruct, s['cCellInvalid'].li.int()), 'rgCellInvalid'),
    ]

class TableFeatureType(pstruct.type):
    class crwHeader(Boolean, pint.uint32_t): pass
    class crwTotals(Boolean, pint.uint32_t): pass

    class flags(pbinary.struct):
        _fields_ = [
            (1, 'unused2'), (1, 'fAutoFilter'), (1, 'fPersistAutoFilter'),
            (1, 'fShowInsertRow'), (1, 'fInsertRowInsCells'), (1, 'fLoadPldwIdDeleted'),
            (1, 'fShownTotalRow'), (1, 'reserved1'), (1, 'fNeedsCommit'),
            (1, 'fSingleCell'), (1, 'reserved2'), (1, 'fApplyAutoFilter'),
            (1, 'fForceInsertToBeVis'), (1, 'fCompressedXml'), (1, 'fLoadCSPName'),
            (1, 'fLoadPldwIdChanged'), (4, 'verXL'), (1, 'fLoadEntryId'),
            (1, 'fLoadPllstclInvalid'), (1, 'fGoodRupBld'), (1, 'unused3'),
            (1, 'fPublished'), (7, 'reserved3'),
        ]

    def __cSPName(self):
        return XLUnicodeString if self['flags'].li['fLoadCSPName'] else ptype.type
    def __entryId(self):
        return XLUnicodeString if self['flags'].li['fLoadEntryId'] else ptype.type
    def __idDeleted(self):
        return Feat11RgSharepointIdDel if self['flags'].li['fLoadPldwIdDeleted'] else ptype.type
    def __idChanged(self):
        return Feat11RgSharepointIdChange if self['flags'].li['fLoadPldwIdChanged'] else ptype.type
    def __cellInvalid(self):
        return Feat11RgInvalidCells if self['flags'].li['fLoadPllstclInvalid'] else ptype.type

    _fields_ = [
        (SourceType, 'lt'),
        (pint.uint32_t, 'idList'),
        (crwHeader, 'crwHeader'),
        (crwTotals, 'crwTotals'),
        (pint.uint32_t, 'idFieldNext'),
        (pint.uint32_t, 'cbFSData'),    # GUARD: =64
        (pint.uint16_t, 'rupBuild'),
        (pint.uint16_t, 'unused1'),
        (flags, 'flags'),
        (pint.uint32_t, 'lPosStmCache'),
        (pint.uint32_t, 'cbStmCache'),
        (pint.uint32_t, 'cchStmCache'),
        (LEMMode, 'lem'),

        (dyn.array(pint.uint8_t, 16), 'rgbHashParam'),
        (XLUnicodeString, 'rgbName'),
        (pint.uint16_t, 'cFieldData'),
        (__cSPName, 'cSPName'),
        (__entryId, 'entryId'),
        (lambda s: dyn.array(Feat11FieldDataItem, s['cFieldData'].li.int()), 'fieldData'),
        (__idDeleted, 'idDeleted'),
        (__idChanged, 'idChanged'),
        (__cellInvalid, 'cellInvalid'),
    ]

@RT_Excel.define
class Feature11(pstruct.type):
    type = 2162
    type = 0x872

    def __rgbFeat(self):
        sz = self['cbFeatData'].li.int()
        if sz == 0:
            sz = self.blocksize() - (self['refs2'].li.size()+27)
        return dyn.block(sz)

    _fields_ = [
        (FrtRefHeaderU, 'frtRefHeaderU'),
        (SharedFeatureType, 'isf'),
        (pint.uint8_t, 'reserved1'),
        (pint.uint32_t, 'reserved2'),
        (pint.uint16_t, 'cref2'),
        (pint.uint32_t, 'cbFeatData'),
        (pint.uint16_t, 'reserved3'),
        (lambda s: dyn.array(Ref8U, s['cref2'].li.int()), 'refs2'),
        (__rgbFeat, 'rgbFeat'),
    ]

@RT_Excel.define
class Feature12(Feature11):
    type = 2168
    type = 0x878

class List12BlockLevel(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'cbdxfHeader'),  # GUARD : >=0
        (pint.int32_t, 'istnHeader'),
        (pint.int32_t, 'cbdxfData'),
        (pint.int32_t, 'istnData'),
        (pint.int32_t, 'cbdxfAgg'),
        (pint.int32_t, 'istnAgg'),
        (pint.int32_t, 'cbdxfBorder'),
        (pint.int32_t, 'cbdxfHeaderBorder'),
        (pint.int32_t, 'cbdxfAggBorder'),

        (lambda s: (DXFN12List if s['cbdxfHeader'].li.int() > 0 else ptype.type), 'dxfHeader'),
        (lambda s: (DXFN12List if s['cbdxfData'].li.int() > 0 else ptype.type), 'dxfData'),
        (lambda s: (DXFN12List if s['cbdxfAgg'].li.int() > 0 else ptype.type), 'dxfAgg'),
        (lambda s: (DXFN12List if s['cbdxfBorder'].li.int() > 0 else ptype.type), 'dxfBorder'),
        (lambda s: (DXFN12List if s['cbdxfHeaderBorder'].li.int() > 0 else ptype.type), 'dxfHeaderBorder'),
        (lambda s: (DXFN12List if s['cbdxfAggBorder'].li.int() > 0 else ptype.type), 'dxfAggBorder'),

        (lambda s: (XLUnicodeString if s['istnHeader'].li.int() != -1 else ptype.type), 'stHeader'),
        (lambda s: (XLUnicodeString if s['istnData'].li.int() != -1 else ptype.type), 'stData'),
        (lambda s: (XLUnicodeString if s['istnAgg'].li.int() != -1 else ptype.type), 'stAgg'),
    ]

class List12TableStyleClientInfo(pstruct.type):
    class flags(pbinary.struct):
        _fields_ = [
            (1,'fFirstColumn'),
            (1,'fLastColumn'),
            (1,'fRowStripes'),
            (1,'fColumnStripes'),
            (2,'unused1'),
            (1,'fDefaultStyle'),
            (9,'unused2'),
        ]

    _fields_ = [
        (flags, 'flags'),
        (XLUnicodeString,'stListStyleName'),
    ]

class List12DisplayName(pstruct.type):
    _fields_ = [
        (XLNameUnicodeString, 'stListName'),
        (XLUnicodeString, 'stListComment'),
    ]

#@RT_Excel.define
class List12(pstruct.type):
    type = 2167
    type = 0x877

    def __rgb(self):
        v = self['lsd'].li.int()
        if v == 0:
            return List12BlockLevel
        elif v == 1:
            return List12TableStyleClientInfo
        elif v == 2:
            return List12DisplayName
        raise NotImplementedError(v)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (pint.uint16_t, 'lsd'),
        (pint.uint32_t, 'idList'),
        (__rgb, 'rgb'),
    ]

@RT_Excel.define
class SerParent(pint.uint16_t):
    type = 4170
    type = 0x104a

@RT_Excel.define
class Begin(ptype.type):
    type = 4147
    type = 0x1033

@RT_Excel.define
class End(ptype.type):
    type = 4148
    type = 0x1034

@RT_Excel.define
class StartBlock(ptype.type):
    type = 2130
    type = 0x852

@RT_Excel.define
class EndBlock(ptype.type):
    type = 2131
    type = 0x853

#@RT_Excel.define
class PublisherRecord(pstruct.type):
    # XXX: undocumented
    type = 137
    type = 0x89

    class SectionRecord(dyn.block(24)):
        # XXX: also undocumented
        pass

    _fields_ = [
        (pint.uint16_t, 'grbit'),
        (Ref8U, 'Ref8u'),
        (SectionRecord, 'sec'),
    ]

#@RT_Excel.define # FIXME
class SST(pstruct.type):
    type = 252
    type = 0xfc
    _fields_ = [
        (pint.int32_t, 'cstTotal'),     # GUARD: >=0
        (pint.int32_t, 'cstUnique'),    # GUARD: >=0
        (lambda s: dyn.array(XLUnicodeRichExtendedString, s['cstUnique'].li.int()), 'rgb'),
    ]

class FontIndex(pint.enum, pint.uint16_t):
    _values_ = [
        (0, 'Default'),
        (1, 'Default,Bold'),
        (2, 'Default,Italic'),
        (3, 'Default,Bold,Italic'),
    ]

class FormatRun(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'ich'),
        (FontIndex, 'ifnt'),
    ]

class Phs(pstruct.type):
    class formatinfo(pbinary.struct):
        _fields_ = [(2,'phType'),(2,'alcH'),(12,'unused')]

    _fields_ = [
        (FontIndex, 'ifnt'),
        (formatinfo, 'ph'),
    ]

if False:
    # FIXME: http://msdn.microsoft.com/en-us/library/dd924700(v=office.12).aspx
    # this type doesn't align with this structure definition
    class LPWideString(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'cchCharacters'),
            (lambda s: dyn.clone(pstr.wstring, length=s['cchCharacters'].li.int()), 'rgchData'),
        ]

class RPHSSub(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'crun'),
        (pint.uint16_t, 'cch'),
        (lambda s: dyn.clone(pstr.wstring, length=s['cch'].li.int()), 'st'),
    ]

class PhRuns(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'ichFirst'),
        (pint.uint16_t, 'ichMom'),
        (pint.uint16_t, 'cchMom'),
    ]

class ExtRst(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'reserved'),
        (pint.uint16_t, 'cb'),
        (Phs, 'phs'),
        (RPHSSub, 'rphssub'),
        (lambda s: dyn.array(PhRuns, s['rphssub'].li['crun'].int()), 'rgphruns')
    ]

class XLUnicodeRichExtendedString(pstruct.type):
    class flags(pbinary.struct):
        _fields_ = [
            (1, 'fHighByte'),
            (1, 'reserved1'),
            (1, 'fExtSt'),
            (1, 'fRichSt'),
            (4, 'reserved2'),
        ]

    def __cRun(self):
        f = self['flags'].l
        return pint.uint16_t if f['fRichSt'] else pint.uint_t
    def __cbExtRst(self):
        f = self['flags'].l
        return pint.int32_t if f['fExtSt'] else pint.int_t
    def __rgb(self):
        f = self['flags'].l
        if f['fHighByte']:
            return dyn.clone(pstr.wstring, length=int(self['cch'].li))
        return dyn.clone(pstr.string, length=int(self['cch'].li))
    def __ExtRst(self):
        f = self['flags'].l
        return ExtRst if f['fExtSt'] else ptype.undefined

    _fields_ = [
        (pint.uint16_t, 'cch'),
        (flags, 'flags'),
        (__cRun, 'cRun'),
        (__cbExtRst, 'cbExtRst'),
        (__rgb, 'rgb'),
        (lambda s: dyn.array(FormatRun, s['cRun'].li.int()), 'rgRun'),
        (__ExtRst, 'ExtRst'),
    ]

class FilePointer(pint.uint32_t): pass
class ISSTInf(pstruct.type):
    _fields_ = [
        (FilePointer, 'ib'),
        (pint.uint16_t, 'cbOffset'),
        (pint.uint16_t, 'reserved'),
    ]

#@RT_Excel.define
class ExtSST(pstruct.type):
    type = 255
    type = 0xff
    def __rgISSTInf(self):
        bs = self.blocksize()
#        return dyn.clone(parray.block, _object_=ISSTInf, blocksize=lambda s: bs-self.size())
        return dyn.block(bs - self.blocksize())

    _fields_ = [
        (pint.uint16_t, 'dsst'),
        (__rgISSTInf, 'rgISSTInf'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes,office.excel as excel
    filename, = sys.argv[1:]
    ptypes.setsource( ptypes.file(filename,mode='r') )
    #filename = './excel.stream'

    #y = ptypes.debugrecurse(excel.File)()
    z = excel.File()
    z = z.l
    a = z[0]
    print a[2]

    print z[1]

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

