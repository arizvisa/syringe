import operator,functools,itertools
from ptypes import *
import art,graph
from . import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

@Record.define
class RT_Excel(ptype.definition):
    type,cache = __name__,{}
    @classmethod
    def lookup(cls, type):
        type,none = type
        if none is not None:
            raise KeyError
        return super(RT_Excel, cls).lookup(type)

class RecordGeneral(RecordGeneral):
    class Header(pstruct.type):
        _fields_ = [
            (uint2, 'type'),
            (uint2, 'length'),
        ]
        def summary(self):
            if self.initializedQ():
                type, length = map(self.__getitem__, ('type','length'))
                return 'type={type:#04x} length={length:#04x}({length:d})'.format(type=type.int(), length=length.int())
            return super(RecordGeneral.Header, self).summary()
        def Type(self):
            return RT_Excel.type
        def Instance(self):
            return self['type'].int(), None
        def Length(self):
            return self['length'].int()

class RecordContainer(RecordContainer): _object_ = RecordGeneral

### primitive types
class USHORT(uint2): pass
class Rw(uint2): pass
class ColByteU(ubyte1): pass
class RwU(uint2): pass
class ColU(uint2): pass
class Xnum(pfloat.double): pass
class IFmt(uint2): pass
class Col(uint2): pass
class IXFCell(uint2): pass
class XtiIndex(uint2): pass
class DCol(uint2): pass
class DColByteU(ubyte1): pass
class DRw(uint2): pass
class DRw_ByteU(ubyte1): pass
class XFIndex(uint2): pass
class ObjId(uint2): pass
class Ilel(uint2): pass

class ColRelU(pbinary.struct):
    _fields_ = R([
        (14, 'col'),
        (1, 'colRelative'),
        (1, 'rowRelative'),
    ])

class ColRelNegU(pbinary.struct):
    _fields_ = R([
        (14, 'col'),
        (1, 'colRelative'),
        (1, 'rowRelative'),
    ])

class ColElfU(pbinary.struct):
    _fields_ = R([
        (14, 'col'),
        (1, 'fQuoted'),
        (1, 'fRelative'),
    ])

class RkNumber(pbinary.struct):
    _fields_ = R([
        (1, 'fX100'),
        (1, 'fInt'),
        (30, 'num'),
    ])

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

class RgceElfLoc(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColElfU, 'column'),
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
    _fields_ = [ (ubyte1,'red'),(ubyte1,'green'),(ubyte1,'blue'),(ubyte1,'alpha') ]

class Cetab(pbinary.enum):
    width = 15
    _values_ = [
        # FIXME
    ]

class Ftab(pbinary.enum):
    width = 15
    _values_ = [
        # FIXME
    ]

class FontScheme(pint.enum, uint2):
    _values_ = [
        ('default', 0),
        ('default,bold', 1),
        ('default,italic', 2),
        ('default,bold,italic', 3)
    ]

### File types
class BiffSubStream(RecordContainer):
    '''Each excel stream'''
    _object_ = RecordGeneral

    # make it a regular parray.terminated
    def load(self, **attrs):
        return super(parray.uninitialized, self).load(**attrs)
    def initializedQ(self):
        return super(parray.uninitialized, self).initializedQ()

    def isTerminator(self, value):
        rec,_ = value['header'].Instance()
        return True if rec == EOF.type else False

    def details(self):
        if not self.initializedQ():
            return '???'

        flazy = (lambda n: n['data'].d.l) if getattr(self, 'lazy', False) else (lambda n: n['data'])
        res = flazy(self[0])
        try:
            dt, vers, year, build = map(res.__getitem__, ('dt','vers','rupYear','rupBuild'))
            f = ((k, res['f'].__field__(k)) for k in res['f'])
            f = ((k, v) for k,v in f if v.int())
            flags = ('{:s}={:d}'.format(k, v.int()) if v.bits() > 1 else k for k,v in f)
            return '{:s} -> version({:d}.{:d}) : year({:d}) build({:d}) : {:s}'.format(dt.summary(), vers.int() // 0x100, vers.int() & 0xff, year.int(), build.int(), ' '.join(flags))
        except (TypeError,KeyError):
            pass
        return '{:s} -> {:s}'.format(res['dt'].summary(), super(BiffSubStream, self).summary())

class File(File):
    _object_ = BiffSubStream

    def details(self):
        if self.initializedQ():
            return 'size={length:#x} ({length:d}) blocksize={cb:#x} ({cb:d})'.format(length=self.size(), cb=self.blocksize())
        return '???'

###
@RT_Excel.define
class CatSerRange(pstruct.type):
    type = 0x1020
    type = 4128

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fBetween'),
            (1, 'fMaxCross'),
            (1, 'fReverse'),
            (13, 'reserved')
        ])

    _fields_ = [
        (sint2, 'catCross'),
        (sint2, 'catLabel'),
        (sint2, 'catMark'),
        (_flags, 'catFlags')
    ]

###
@RT_Excel.define
class RRTabId(parray.block):
    _object_ = USHORT
    type = 0x13d
    type = 317
    def blocksize(self):
        return self.parent['length'].int()

###
class FrtFlags(pbinary.flags):
    _fields_ = R([
        (1, 'fFrtRef'),
        (1, 'fFrtAlert'),
        (14, 'reserved')
    ])

class FrtHeader(pstruct.type):
    _fields_ = [
        (uint2, 'rt'),
        (FrtFlags, 'grbitFrt'),
        (dyn.block(8), 'reserved')
    ]

class FrtHeaderOld(pstruct.type):
    _fields_ = [
        (uint2, 'rt'),
        (FrtFlags, 'grbitFrt'),
    ]

@RT_Excel.define
class MTRSettings(pstruct.type):
    type = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'fMTREnabled'),
        (uint4, 'fUserSetThreadCount'),
        (uint4, 'cUserThreadCount')
    ]
###
@RT_Excel.define
class Compat12(pstruct.type):
    type = 2188
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'fNoCompatChk')
    ]
###
class Cell(pstruct.type):
    _fields_ = [
        (uint2, 'rw'),
        (uint2, 'col'),
        (uint2, 'ixfe')
    ]
@RT_Excel.define
class LabelSst(pstruct.type):
    type = 253
    _fields_ = [
        (Cell, 'cell'),
        (uint4, 'isst')
    ]
###
@RT_Excel.define
class RK(pstruct.type):
    type = 638
    type = 0x273
    _fields_ = [
        (uint2, 'rw'),
        (uint2, 'col'),
        (RkRec, 'rkrec')
    ]

#FIXME
@RT_Excel.define
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
        (uint2, 'rwFirst'),
        (uint2, 'rwLast'),
        (uint2, 'colFirst'),
        (uint2, 'colLast'),
    ]

@RT_Excel.define
class MergeCells(pstruct.type):
    type = 229
    _fields_ = [
        (uint2, 'cmcs'),
        (lambda s: dyn.array(Ref8, int(s['cmcs'].li)), 'rgref')
    ]
###
@RT_Excel.define
class CrtLayout12(pstruct.type):
    class CrtLayout12Auto(pbinary.struct):
        _fields_ = R([
            (1, 'unused'),
            (4, 'autolayouttype'),
            (11, 'reserved')
        ])

    type = 2205
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'dwCheckSum'),
        (CrtLayout12Auto, 'auto'),
        (uint2, 'wXMode'),
        (uint2, 'wYMode'),
        (uint2, 'wWidthMode'),
        (uint2, 'wHeightMode'),
        (Xnum, 'x'),
        (Xnum, 'y'),
        (Xnum, 'dx'),
        (Xnum, 'dy'),
        (uint2, 'reserved')
    ]

###
@RT_Excel.define
class Frame(pstruct.type):
    class FrameAuto(pbinary.flags):
        _fields_ = R([
            (1, 'fAutoSize'),
            (1, 'fAutoPosition'),
            (14, 'reserved')
        ])

    type = 4146
    _fields_ = [
        (uint2, 'frt'),
        (FrameAuto, 'f')
    ]

###
@RT_Excel.define
class Pos(pstruct.type):
    type = 4175
    _fields_ = [
        (uint2, 'mdTopLt'),
        (uint2, 'mdBotRt'),
        (uint2, 'x1'),
        (uint2, 'unused1'),
        (uint2, 'y1'),
        (uint2, 'unused2'),
        (uint2, 'x2'),
        (uint2, 'unused3'),
        (uint2, 'y2'),
        (uint2, 'unused4'),
    ]

###
class XLUnicodeStringNoCch(pstruct.type):
    def __rgb(self):
        res, cb = self['fHighByte'].li.int(), self.blocksize()
        hb = (res >> 7) & 1
        sz = (self.length * 2) if hb else (self.length)
        return dyn.clone(pstr.wstring, blocksize=lambda s,cb=cb: cb - 1)

    _fields_ = [
        (ubyte1, 'fHighByte'),
        (__rgb, 'rgb')
    ]

class XLUnicodeString(pstruct.type):
    def HighByte(self):
        res = self['fHighByte'].li.int()
        return bool(res >> 7) & 1

    def __rgb(self):
        cch = self['cch'].li.int()
        cb = (2*cch) if self.HighByte() else cch
        # FIXME: should be a pstr.wstring
        return dyn.block(cb)

    _fields_ = [
        (uint2, 'cch'),
        (ubyte1, 'fHighByte'),
        (__rgb, 'rgb'),
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
            return dyn.clone(pstr.wstring, length=length)
        elif high == 7:
            length = self.parent.blocksize()-2
            return dyn.block(length)
        # FIXME: test this out
        raise NotImplementedError

    _fields_ = [
        (ubyte1, 'cch'),
        (ubyte1, 'fHighByte'),
        (__rgb, 'rgb'),
    ]

@RT_Excel.define
class SupBook(pstruct.type):
    type = 430
    _fields_ = [
        (uint2, 'ctab'),
        (uint2, 'cch'),
    ]

#DataValidationCriteria
@RT_Excel.define
class DVAL(pstruct.type):
    type = 434
    type = 0x1b2

    class wDviFlags(pbinary.flags):
        _fields_ = R([
            (1, 'fWnClosed'),
            (1, 'fWnPinned'),
            (1, 'fCached'),
            (13, 'Reserved')
        ])

    _fields_ = [
        (wDviFlags, 'wDviFlags'),
        (uint4, 'xLeft'),
        (uint4, 'yTop'),
        (uint4, 'idObj'),
        (uint4, 'idvMac'),
    ]

class CellRange(pstruct.type):
    class AddressOld(pstruct.type):
        '''XXX: BIFF2 through BIFF5 only'''
        _fields_ = [(uint2,'first_row'),(uint2,'last_row'),(ubyte1,'first_column'),(ubyte1,'last_column')]

    class Address(pstruct.type):
        _fields_ = [(uint2,'first_row'),(uint2,'last_row'),(uint2,'first_column'),(uint2,'last_column')]

    _fields_ = [
        (uint2, 'number'),
        (lambda s: dyn.array(s.Address, int(s['number'].li)), 'addresses'),
    ]

@RT_Excel.define
class DV(pstruct.type):
    type = 0x1be
    type = 446

    class dwDvFlags(pbinary.flags):
        _fields_ = R([
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
        ])

    class string(pstruct.type):
        def __unicode(self):
            if int(self['unicode_flag'].li):
                return dyn.clone(pstr.wstring, length=int(self['length'].li))
            return dyn.clone(pstr.string, length=int(self['length'].li))

        _fields_ = [
            (uint2, 'length'),
            (ubyte1, 'unicode_flag'),
            (__unicode, 'string'),
        ]

    class formula(pstruct.type):
        _fields_ = [
            (uint2, 'size'),
            (uint2, 'reserved'),
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
    class Flags(pbinary.flags):
        _fields_ = R([
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
        ])

    class DocType(pint.enum, uint2):
        _values_ = [
            ('workbook', 0x0005),
            ('worksheet', 0x0010),
            ('charsheet', 0x0020),
            ('macrosheet', 0x0040)
        ]

    type = 2057
    _fields_ = [
        (uint2, 'vers'),
        (DocType, 'dt'),
        (uint2, 'rupBuild'),
        (uint2, 'rupYear'),
        (Flags, 'f')
    ]

###
@RT_Excel.define
class Font(pstruct.type):
    type = 0x0031
    type = 49
    _fields_ = [
        (uint2, 'dyHeight'),
        (uint2, 'flags'),
        (uint2, 'icv'),
        (uint2, 'bls'),
        (uint2, 'sss'),
        (ubyte1, 'uls'),
        (ubyte1, 'vFamily'),
        (ubyte1, 'bCharSet'),
        (ubyte1, 'unused3'),
        (ShortXLUnicodeString, 'fontName'),
    ]

@RT_Excel.define
class BookBool(pbinary.flags):
    type = 0xda
    type = 218
    _fields_ = R([
        (1, 'fNoSaveSup'),
        (1, 'reserved1'),
        (1, 'fHasEnvelope'),
        (1, 'fEnvelopeVisible'),
        (1, 'fEnvelopeInitDone'),
        (2, 'grUpdateLinks'),
        (1, 'unused'),
        (1, 'fHideBorderUnselLists'),
        (7, 'reserved2'),
    ])

@RT_Excel.define
class RefreshAll(pint.enum, uint2):
    type = 0x1b7
    type = 439
    _values_ = [
        ('noforce', 0),('force', 1),
    ]

class Boolean(pint.enum):
    _values_ = [
        ('False', 0),('True', 1),
    ]

@RT_Excel.define
class CalcPrecision(Boolean, uint2):
    type = 0xe
    type = 14

@RT_Excel.define
class Date1904(pint.enum,uint2):
    type = 0x22
    type = 34

    _values_ = [
        ('1900 date system', 0),
        ('1904 date system', 1),
    ]

class HideObjEnum(pint.enum):
    _values_ = [
        ('SHOWALL',         0),
        ('SHOWPLACEHOLDER', 1),
        ('HIDEALL',         2),
    ]

@RT_Excel.define
class HideObj(HideObjEnum, uint2):
    type = 0x8d
    type = 141

@RT_Excel.define
class Backup(Boolean, uint2):
    type = 0x40
    type = 64

class TabIndex(uint2): pass

@RT_Excel.define
class Password(uint2):
    type = 0x13
    type = 19

@RT_Excel.define
class Protect(Boolean, uint2):
    type = 0x12
    type = 18

@RT_Excel.define
class WinProtect(Boolean, uint2):
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
class InterfaceHdr(uint2):
    type = 0xe1
    type = 225

@RT_Excel.define
class InterfaceEnd(uint2):
    type = 0xe2
    type = 226

@RT_Excel.define
class Mms(pstruct.type):
    type = 0xc1
    type = 193
    _fields_ = [
        (ubyte1, 'reserved1'),
        (ubyte1, 'reserved2'),
    ]

@RT_Excel.define
class CodePage(uint2):
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
        (sint2, 'xWn'),
        (sint2, 'yWn'),
        (sint2, 'dxWn'),
        (sint2, 'dyWn'),
        (uint2, 'flags'),
        (TabIndex, 'itabCur'),
        (TabIndex, 'itabFirst'),
        (uint2, 'ctabSel'),
        (uint2, 'wTabRatio'),
    ]

@RT_Excel.define
class CalcMode(pint.enum, uint2):
    type = 0xd
    type = 13
    _values_ = [
        ('Manual', 0),('Automatic', 1),('No Tables', 2),
    ]

@RT_Excel.define
class BuiltInFnGroupCount(uint2):
    type = 156
    type = 0x9c

@RT_Excel.define
class Prot4Rev(Boolean, uint2):
    type = 431
    type = 0x1af

@RT_Excel.define
class Prot4RevPass(uint2):
    type = 444
    type = 0x1bc

@RT_Excel.define
class DSF(uint2):
    type = 353
    type = 0x161

@RT_Excel.define
class MSODRAWING(art.OfficeArtSpContainer):
    type = 0x00ec
    type = 236

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

    class _flags(pbinary.flags):
        _fields_ = R([
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
        ])

    _fields_ = [
        (Rw, 'rw'),
        (uint2, 'colMic'),
        (uint2, 'colMac'),
        (uint2, 'miyRw'),
        (uint2, 'reserved1'),
        (uint2, 'unused1'),
        (_flags, 'flags'),
    ]

###
if True:
    class SerAr(pstruct.type):
        _fields_ = [
            (uint4,'reserved'),
            (lambda s: SerArType.get(s['reserved1'].li.int()), 'Ser'),
        ]

    class SerArType(ptype.definition):
        cache = {}

    @SerArType.define
    class SerBool(pstruct.type):
        type = 0x04
        type = 4
        _fields_ = [
            (ubyte1,'f'),
            (ubyte1,'reserved2'),
            (uint2,'unused1'),
            (uint4,'unused2'),
        ]

    class BErr(pint.enum, ubyte1):
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
            (ubyte1,'reserved2'),
            (uint2,'unused1'),
            (uint4,'unused2'),
        ]

    @SerArType.define
    class SerNil(pstruct.type):
        type = 0x0
        type = 0
        _fields_ = [
            (uint4,'unused1'),
            (uint4,'unused2'),
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
    _fields_ = R([
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
    ])

class StyleXF(pbinary.struct):
    _fields_ = R([
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
    ])

class FontIndex(pint.enum, uint2):
    _values_ = [
        ('default-none', 0),
        ('default-bold', 1),
        ('default-italic', 2),
        ('default-both', 3),
    ]

@RT_Excel.define
class XF(pstruct.type):
    type = 0xe0
    type = 224
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fLocked'),
            (1, 'fHidden'),
            (1, 'fStyle'),
            (1, 'f123Prefix'),
            (12, 'ixfParent'),
        ])
    _fields_ = [
        (FontIndex, 'ifnt'),
        (IFmt, 'ifmt'),
        (_flags, 'flags'),
        (lambda s: CellXF if s['flags'].li['fStyle'] == 0 else StyleXF, 'data'),
    ]

# FIXME
@RT_Excel.define
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

class CellParsedFormula(pstruct.type):
    def __rgce(self):
        cb = self['cce'].li.int()
        return dyn.clone(Rgce, blocksize=lambda s,cb=cb: cb)

    def __rgcb(self):
        bs = self.blocksize()
        sz = self['cce'].li.size() + self['cce'].int()
        return dyn.block(bs-sz)
#        return RgbExtra        # FIXME

    _fields_ = [
        (uint2, 'cce'),
        (__rgce, 'rgce'),     # XXX: page 756. must not contain
        (__rgcb, 'rgcb'),
    ]

class Ptg(ptype.definition):
    cache = {}

class PtgDataType(pbinary.enum):
    width = 2
    _values_ = [
        ('UNKNOWN', 0x0),
        ('REFERENCE', 0x1),
        ('VALUE', 0x2),
        ('ARRAY', 0x3),
    ]

class PtgHeader(pstruct.type):
    def __eptg(self):
        res = self['ptg'].li
        return ubyte1 if res['ptg'] in (0x18,0x19) else 0

    def Type(self):
        first, second = map(self.__field__, ('ptg', 'eptg'))
        return first.int(), (second.int() if second.bits() else None)

    class _firstByte(pbinary.struct):
        _fields_ = R([
            (5, 'ptg'),
            (PtgDataType, 'type'),
            (1, 'reserved'),
        ])

    _fields_ = [
        (_firstByte, 'ptg'),
        (__eptg, 'eptg'),
    ]

class PtgGeneral(pstruct.type):
    def __data(self):
        hdr = self['header'].li
        res = hdr.Type()
        return Ptg.lookup(res)

    _fields_ = [
        (PtgHeader, 'header'),
        (__data, 'data'),
    ]

@Ptg.define
class PtgExp(pstruct.type):
    type = 0x01, None
    _fields_ = [
        (Rw, 'row'),
        (Col, 'col'),
    ]

@Ptg.define
class PtgTbl(pstruct.type):
    type = 0x02, None
    _fields_ = [
        (Rw, 'row'),
        (Col, 'col'),
    ]

@Ptg.define
class PtgAdd(ptype.undefined): type = 0x03, None
@Ptg.define
class PtgSub(ptype.undefined): type = 0x04, None
@Ptg.define
class PtgMul(ptype.undefined): type = 0x05, None
@Ptg.define
class PtgDiv(ptype.undefined): type = 0x06, None
@Ptg.define
class PtgPower(ptype.undefined): type = 0x07, None
@Ptg.define
class PtgPower(ptype.undefined): type = 0x07, None
@Ptg.define
class PtgConcat(ptype.undefined): type = 0x08, None
@Ptg.define
class PtgLt(ptype.undefined): type = 0x09, None
@Ptg.define
class PtgLe(ptype.undefined): type = 0x0a, None
@Ptg.define
class PtgEq(ptype.undefined): type = 0x0b, None
@Ptg.define
class PtgGe(ptype.undefined): type = 0x0c, None
@Ptg.define
class PtgGt(ptype.undefined): type = 0x0d, None
@Ptg.define
class PtgNe(ptype.undefined): type = 0x0e, None
@Ptg.define
class PtgIsect(ptype.undefined): type = 0x0f, None
@Ptg.define
class PtgUnion(ptype.undefined): type = 0x10, None
@Ptg.define
class PtgRange(ptype.undefined): type = 0x11, None
@Ptg.define
class PtgUplus(ptype.undefined): type = 0x12, None
@Ptg.define
class PtgUminus(ptype.undefined): type = 0x13, None
@Ptg.define
class PtgPercent(ptype.undefined): type = 0x14, None
@Ptg.define
class PtgParen(ptype.undefined): type = 0x15, None
@Ptg.define
class PtgMissArg(ptype.undefined): type = 0x16, None
@Ptg.define
class PtgStr(ShortXLUnicodeString): type = 0x17, None
@Ptg.define
class PtgElfLel(Ilel): type = 0x18, 0x01
@Ptg.define
class PtgElfRw(RgceElfLoc): type = 0x18, 0x02
@Ptg.define
class PtgElfCol(RgceElfLoc): type = 0x18, 0x03
@Ptg.define
class PtgElfRwV(RgceElfLoc): type = 0x18, 0x06
@Ptg.define
class PtgElfColV(RgceElfLoc): type = 0x18, 0x07
@Ptg.define
class PtgElfRadical(RgceElfLoc): type = 0x18, 0x0a
@Ptg.define
class PtgElfRadicalS(uint4): type = 0x18, 0x0b
@Ptg.define
class PtgElfColS(uint4): type = 0x18, 0x0d
@Ptg.define
class PtgElfColSV(uint4): type = 0x18, 0x0f
@Ptg.define
class PtgElfRadicalLel(Ilel): type = 0x18, 0x10
@Ptg.define
class PtgSxName(uint4): type = 0x18, 0x1d
@Ptg.define
class PtgAttrSemi(uint2): type = 0x19, 0x01

@Ptg.define
class PtgAttrIf(uint2): type = 0x19, 0x02
@Ptg.define
class PtgAttrChoose(pstruct.type):
    type = 0x19, 0x04
    _fields_ = [
        (uint2, 'cOffset'),
        (lambda s: dyn.array(uint2, s['cOffset'].int()+1), 'rgOffset'),
    ]
@Ptg.define
class PtgAttrGoto(uint2): type = 0x19, 0x08
@Ptg.define
class PtgAttrSum(uint2): type = 0x19, 0x10
@Ptg.define
class PtgAttrBaxcel(uint2): type = 0x19, 0x20

class PtgAttrSpaceType(pstruct.type):
    class _type(pint.enum, ubyte1):
        _values_ = [
            ('base-space', 0),
            ('base-returns', 1),
            ('open-space', 2),
            ('open-returns', 3),
            ('close-space', 4),
            ('close-returns', 5),
            ('expr-space', 6),
        ]
    _fields_ = [
        (_type, 'type'),
        (ubyte1, 'cch'),
    ]

@Ptg.define
class PtgAttrSpace(PtgAttrSpaceType): type = 0x19, 0x40
@Ptg.define
class PtgAttrSpaceSemi(PtgAttrSpaceType): type = 0x19, 0x41
@Ptg.define
class PtgErr(BErr): type = 0x1c, None
@Ptg.define
class PtgBool(Boolean, ubyte1): type = 0x1d, None
@Ptg.define
class PtgInt(uint2): type = 0x1e, None
@Ptg.define
class PtgNum(Xnum): type = 0x1f, None

@Ptg.define
class PtgArray(pstruct.type):
    type = 0x20, None
    _fields_ = [
        (ubyte1, 'unused1'),
        (uint2, 'unused2'),
        (uint4, 'unused3'),
    ]

@Ptg.define
class PtgFunc(Ftab):
    type = 0x21, None

@Ptg.define
class PtgFuncVar(pstruct.type):
    type = 0x22, None
    class _tab(pbinary.struct):
        def __value(self):
            return Cetab if self['fCeFunc'] else Ftab
        _fields_ = R([
            (__value, 'value'),
            (1, 'fCeFunc'),
        ])

    _fields_ = [
        (ubyte1, 'cparams'),
        (_tab, 'tab'),
    ]

@Ptg.define
class PtgName(uint4): type = 0x23, None
@Ptg.define
class PtgRef(RgceLocRel): type = 0x24, None
@Ptg.define
class PtgArea(RgceArea): type = 0x25, None

@Ptg.define
class PtgMemArea(pstruct.type):
    type = 0x26, None
    _fields_ = [
        (uint4, 'unused'),
        (uint2, 'cce'),
    ]

@Ptg.define
class PtgMemErr(pstruct.type):
    type = 0x27, None
    _fieldS_ = [
        (BErr, 'err'),
        (ubyte1, 'unused1'),
        (uint2, 'unused2'),
        (uint2, 'cce'),
    ]

@Ptg.define
class PtgMemNoMem(pstruct.type):
    type = 0x28, None
    _fields_ = [
        (uint4, 'unused'),
        (uint2, 'cce'),
    ]

@Ptg.define
class PtgMemFunc(uint2): type = 0x29, None

@Ptg.define
class PtgRefErr(pstruct.type):
    type = 0x2a, None
    _fields_ = [
        (uint2, 'unused1'),
        (uint2, 'unused2'),
    ]

@Ptg.define
class PtgAreaErr(pstruct.type):
    type = 0x2b, None
    _fields_ = [
        (uint2, 'unused1'),
        (uint2, 'unused2'),
        (uint2, 'unused3'),
        (uint2, 'unused4'),
    ]

@Ptg.define
class PtgRefN(RgceLocRel): type = 0x2c, None
@Ptg.define
class PtgAreaN(RgceAreaRel): type = 0x2d, None

@Ptg.define
class PtgNameX(pstruct.type):
    type = 0x39, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'nameindex'),
    ]

@Ptg.define
class PtgRef3d(pstruct.type):
    type = 0x3a, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (RgceLoc, 'nameindex'),
    ]

@Ptg.define
class PtgArea3d(pstruct.type):
    type = 0x3b, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (RgceArea, 'area'), # FIXME: or RgceAreaRel
    ]

@Ptg.define
class PtgRefErr3d(pstruct.type):
    type = 0x3c, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'unused1'),
        (uint4, 'unused2'),
    ]

@Ptg.define
class PtgAreaErr3d(pstruct.type):
    type = 0x3d, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'unused1'),
        (uint4, 'unused2'),
        (uint4, 'unused3'),
        (uint4, 'unused4'),
    ]

class Rgce(parray.block):
    _object_ = PtgGeneral

if False:
    class RgbExtra(parray.infinite):
        def _object_(self):
            p = self.parent['rgce']
            for x in p:
                if x.hasattr('extra'):
                    yield x.extra
                continue
            return

class Icv(uint2): pass
class IcvXF(uint2): pass

if False:
    class NameParsedFormula(pstruct.type):
        # XXX: page 823 rgce must not contain
        _fields_ = [
            (Rgce, 'rgce'),
            (RgbExtra, 'rgcb'),
        ]

class FormulaValue(pstruct.type):
    _fields_ = [
        (uint2, 'byte1'),
        (uint2, 'byte2'),
        (uint2, 'byte3'),
        (uint2, 'byte4'),
        (uint2, 'byte5'),
        (uint2, 'byte6'),
        (uint4, 'fExprO'),
    ]

if False:
    #@RT_Excel.define
    class Formula(pstruct.type):
        type = 0x6
        type = 6

        class _flags(pbinary.flags):
            _fields_ = R([
                (1,'fAlwaysCalc'),
                (1, 'reserved1'),
                (1, 'fFill'),
                (1, 'fShrFmla'),
                (1, 'reserved2'),
                (1, 'fClearErrors'),
                (10, 'reserved3'),
            ])

        _fields_ = [
            (Cell, 'cell'),
            (FormulaValue, 'val'),
            (_flags, 'flags'),
            (dyn.block(4), 'chn'),  # XXX: application-specific
            (CellParsedFormula, 'formula'),
        ]

@RT_Excel.define
class XCT(pstruct.type):
    type = 89
    type = 0x59
    _fields_ = [
        (sint2, 'ccrn'),
        (uint2, 'itab'),
    ]

class BuiltInStyle(pstruct.type):
    _fields_ = [
        (ubyte1, 'istyBuiltIn'),
        (ubyte1, 'iLevel'),
    ]

#FIXME
#@RT_Excel.define
class Style(pstruct.type):
    type = 659
    type = 0x293

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fBuiltIn'),
            (3, 'unused'),
            (12,'ixfe'),
        ])

    _fields_ = [
        (_flags, 'flags'),
        (lambda s: BuiltInStyle if s['flags'].li['fBuiltIn'] else ptype.undefined, 'builtInData'),
        (lambda s: XLUnicodeString if not s['flags'].li['fBuiltIn'] else ptype.undefined, 'user')
    ]

class XColorType(pint.enum, uint2):
    _values_ = [
        ('XCLRAUTO', 0x00000000),
        ('XCLRINDEXED', 0x00000001),
        ('XCLRRGB', 0x00000002),
        ('XCLRTHEMED', 0x00000003),
        ('XCLRNINCHED', 0x00000004),
    ]

class FullColorExt(pstruct.type):
    class Unknown(uint4): pass
    class IcvXF(uint4): pass

    def __xclrValue(self):
        t = self['xclrType'].li.int()
        if t == 1:
            return self.IcvXF
        if t == 2:
            return LongRGBA
        if t == 3:
            return ColorTheme
        return self.Unknown

    _fields_ = [
        (XColorType, 'xclrType'),
        (sint2, 'nTintShade'),
        (__xclrValue, 'xclrValue'),
        (pint.uint64_t, 'unused'),
    ]

class ColorTheme(pint.enum, uint4):
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
    class type(pint.enum, uint4):
        _values_ = [ ('linear', 0), ('rectangular', 1) ]
    _fields_ = [
        (type, 'type'),
        (Xnum, 'numDegree'),
        (Xnum, 'numFillToLeft'),
        (Xnum, 'numFillToRight'),
        (Xnum, 'numFillToTop'),
        (Xnum, 'numFillToBottom'),
    ]

class GradStop(pstruct.type):
    class Unknown(uint4): pass
    class IcvXF(uint4): pass

    def __xclrValue(self):
        t = self['xclrType'].li.int()
        if t == 1:
            return self.IcvXF
        if t == 2:
            return LongRGBA
        if t == 3:
            return ColorTheme
        return self.Unknown

    _fields_ = [
        (XColorType, 'xclrType'),
        (__xclrValue, 'xclrValue'),
        (Xnum, 'numPosition'),
    ]

class XFExtGradient(pstruct.type):
    _fields_ = [
        (XFPropGradient, 'gradient'),
        (uint4, 'cGradSTops'),
        (lambda s: dyn.array(GradStop, s['cGradStops'].li.int()), 'rgGradStops'),
    ]

class ExtPropType(ptype.definition):
    cache = {}
@ExtPropType.define
class ET_Foreground_Color(FullColorExt):
    type = 0x0004
@ExtPropType.define
class ET_Background_Color(FullColorExt):
    type = 0x0005
@ExtPropType.define
class ET_GradientFill(XFExtGradient):
    type = 0x0006
@ExtPropType.define
class ET_TopBorderColor(FullColorExt):
    type = 0x0007
@ExtPropType.define
class ET_BottomBorderColor(FullColorExt):
    type = 0x0008
@ExtPropType.define
class ET_LeftBorderColor(FullColorExt):
    type = 0x0009
@ExtPropType.define
class ET_RightBorderColor(FullColorExt):
    type = 0x000a
@ExtPropType.define
class ET_DiagonalBorderColor(FullColorExt):
    type = 0x000b
@ExtPropType.define
class ET_TextColor(FullColorExt):
    type = 0x000d
@ExtPropType.define
class ET_FontScheme(FontScheme):
    type = 0x000e
@ExtPropType.define
class ET_TextIndentation(uint2):
    type = 0x000f

class ExtProp(pstruct.type):
    class _extType(pint.enum, uint2):
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
        res = self['extType'].li.int()
        cb = self['cb'].li.int() - (2 + 2)
        res = ExtPropType.lookup(res)
        return dyn.clone(res, blocksize=lambda s,cb=cb:cb)

    _fields_ = [
        (_extType, 'extType'),
        (uint2, 'cb'),
        (__extPropData, 'extPropData'),
    ]

@RT_Excel.define
class XFExt(pstruct.type):
    type = 0x87d
    type = 2173
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint2, 'reserved1'),
        (XFIndex, 'ixfe'),
        (uint2, 'reserved2'),
        (uint2, 'cexts'),
        (lambda s: dyn.array(ExtProp, s['cexts'].li.int()), 'rgExt'),
    ]

@RT_Excel.define
class Format(pstruct.type):
    type = 0x41e
    type = 1054
    def __stFormat(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['length'].int() - 2
        return dyn.block(length)
    _fields_ = [
        (uint2, 'ifmt'),
        #(XLUnicodeString, 'stFormat'), # FIXME: is the specification wrong here?
        (__stFormat, 'stFormat'),
    ]

@RT_Excel.define
class SerAuxErrBar(pstruct.type):
    type = 4187
    type = 0x105b

    class sertm(pint.enum, ubyte1):
        _values_ = [
            ('horizontal+', 1),
            ('horizontal-', 2),
            ('vertical+', 3),
            ('vertical-', 4),
        ]

    class ebsrc(pint.enum, ubyte1):
        _values_ = [
            ('percentage', 1),
            ('fixed', 2),
            ('standard', 3),
            ('custom', 4),
            ('error', 5),
        ]

    class fTeeTop(Boolean, ubyte1): pass

    _fields_ = [
        (sertm, 'sertm'),
        (ebsrc, 'ebsrc'),
        (fTeeTop, 'fTeeTop'),
        (ubyte1, 'reserved'),
        (Xnum, 'numValue'),
        (uint2, 'cnum'),
    ]

class SharedFeatureType(pint.enum, uint2):
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
        (uint4, 'cbSD'),    # GUARD: >20
        (lambda s: dyn.block(s['cbSD'].li.int()), 'sd'),
    ]

class FeatProtection(pstruct.type):
    _fields_ = [
        (ubyte1, 'fSD'),
        (uint4, 'wPassword'),
        (XLUnicodeString, 'stTitle'),
        (SDContainer, 'sdContainer'),
    ]

class FFErrorCheck(pbinary.flags):
    _fields_ = R([
        (1, 'ffecCalcError'),
        (1, 'ffecEmptyCellRef'),
        (1, 'ffecNumStoredAsText'),
        (1, 'ffecInconsistRange'),
        (1, 'ffecInconsistFmla'),
        (1, 'ffecTextDateInsuff'),
        (1, 'ffecUnprotFmla'),
        (1, 'ffecDateValidation'),
        (24, 'reserved'),
    ])

class FeatFormulaErr2(FFErrorCheck): pass

class Property(pstruct.type):
    _fields_ = [(uint4,'keyIndex'),(uint4,'valueIndex')]

class PropertyBag(pstruct.type):
    _fields_ = [
        (uint2, 'id'),
        (uint2, 'cProp'),
        (uint2, 'cbUnknown'),
        (lambda s: dyn.array(Property, s['cProp'].li.int()), 'properties'),
    ]

class FactoidData(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([(1,'fDelete'),(1,'fXMLBased'),(6,'reserved')])

    _fields_ = [
        (_flags, 'flags'),
        (PropertyBag, 'propertyBag'),
    ]

class FeatSmartTag(pstruct.type):
    _fields_ = [
        (uint4, 'hashValue'),
        (ubyte1, 'cSmartTags'),
        (lambda s: dyn.array(FactoidData,s['cSmartTags'].li.int()), 'rgFactoid'),
    ]

@RT_Excel.define
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
        return ptype.undefined

    _fields_ =[
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (ubyte1, 'reserved1'),
        (uint4, 'reserved2'),
        (uint2, 'cref'),
        (uint4, 'cbFeatData'),
        (uint2, 'reserved3'),
        (lambda s: dyn.array(Reg8U, s['cref'].li.int()), 'refs'),
        (__rgbFeat, 'rgbFeat'),
    ]

class EnhancedProtection(pbinary.flags):
    _fields_ = R([
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
    ])

@RT_Excel.define
class FeatHdr(pstruct.type):
    type = 2151
    type = 0x867
    def __rgbHdrData(self):
        isf = self['isf'].l
        if self['cbHdrData'].li.int() == 0:
            return ptype.undefined
        if isf['ISFPROTECTION']:
            return EnhancedProtection
        elif isf['ISFFEC2']:
            return ptype.undefined
        raise NotImplementedError(isf)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (ubyte1, 'reserved'),
        (uint4, 'cbHdrData'),
        (__rgbHdrData, 'rgbHdrData'),
    ]

@RT_Excel.define
class FeatHdr11(pstruct.type):
    type = 2161
    type = 0x871
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'), # GUARD: ISFLIST
        (ubyte1, 'reserved1'),
        (uint4, 'reserved2'),
        (uint4, 'reserved3'),
        (uint4, 'idListNext'),
        (uint2, 'reserved4'),
    ]

class FrtRefHeaderU(pstruct.type):
    _fields_ = [
        (uint2, 'rt'),
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

class SourceType(pint.enum, uint4):
    _values_ = [
        ('LTRANGE', 0),
        ('LTSHAREPOINT', 1),
        ('LTXML', 2),
        ('LTEXTERNALDATA', 3),
    ]

class LEMMode(pint.enum, uint4):
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
        (uint2, 'reserved1'),
        (uint2, 'reserved2'),
        (uint2, 'reserved3'),
        (uint2, 'cexts'),
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
        (uint4, 'unused1'),
    ]

class AFDOperStr(pstruct.type):
    _fields_ = [
        (uint4, 'unused1'),
        (ubyte1, 'cch'),
        (ubyte1, 'fCompare'),
        (ubyte1, 'reserved1'),
        (ubyte1, 'unused2'),
        (uint4, 'unused3'),
    ]

class Bes(pstruct.type):
    _fields_ = [
        (ubyte1, 'bBoolErr'),
        (ubyte1, 'fError'),
    ]
class AFDOperBoolErr(pstruct.type):
    _fields_ = [
        (Bes, 'bes'),
        (uint2, 'unused1'),
        (uint4, 'unused2'),
    ]
class AFDOper(pstruct.type):
    def __vtValue(self):    # XXX
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
        (ubyte1, 'vt'),
        (ubyte1, 'grbitSign'),
        (__vtValue, 'vtValue'),
    ]

class AutoFilter(pstruct.type):
    class _flag(pbinary.flags):
        _fields_ = R([(2,'wJoin'),(1,'fSimple1'),(1,'fSimple2'),(1,'fTopN'),(1,'fTop'),(1,'fPercent'),(9,'wTopN')])

    def __str1(self):
        do = self['doper1'].li
        cb = do['vtValue']['cch'].int()
        return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda s,cb:cb) if do['vtValue'].int() == 6 else ptype.undefined
    def __str2(self):
        do = self['doper1'].li
        cb = do['vtValue']['cch'].int()
        return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda s,cb:cb) if do['vtValue'].int() == 6 else ptype.undefined

    _fields_ = [
        (uint2, 'iEntry'),
        (_flag, 'flag'),
        (AFDOper, 'doper1'),
        (AFDOper, 'doper2'),
        (__str1, 'str1'),
        (__str2, 'str2'),
    ]

class Feat11FdaAutoFilter(pstruct.type):
    _fields_ = [
        (uint4, 'cbAutoFilter'), #GUARD : <= 2080 bytes
        (uint2, 'unused'),
        (lambda s: AutoFilter, 'recAutoFilter'),
    ]

class Feat11XMapEntry2(pstruct.type):
    _fields_ = [
        (uint4,'dwMapId'),
        (XLUnicodeString,'rgbXPath'),
    ]

class Feat11XMapEntry(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([(1,'reserved1'),(1,'fLoadXMap'),(1,'fCanBeSingle'),(1,'reserved2'),(28,'reserved3')])
    _fields_ = [
        (_flags, 'flags'),
        (Feat11XMapEntry2, 'details'),
    ]

class Feat11XMap(pstruct.type):
    _fields_ = [
        (uint2, 'iXmapMac'),
        (lambda s: dyn.array(Feat11XMapEntry,s['iXmapMac'].li.int()), 'rgXmap'),
    ]

class ListParsedArrayFormula(pstruct.type):
    def __rgce(self):
        cb = self['cce'].li.int()
        return dyn.clone(Rgce, blocksize=lambda s,cb=cb: cb)

    def __RgbExtra(self):
        bs = self.blocksize()
        sz = self['cce'].li.size() + self['cce'].int()
        return dyn.block(bs-sz)

    _fields_ = [
        (uint2, 'cce'),
        (__rgce, 'rgce'),
        (__RgbExtra, 'rgcb')
    ]
class ListParsedFormula(pstruct.type):
    def __Rgce(self): # FIXME
        return dyn.block(self['cce'].li.int())
    _fields_ = [
        (uint2, 'cce'),
        (__Rgce, 'rgce'),
    ]

class Feat11Fmla(pstruct.type):
    _fields_ = [
        (uint2, 'cbFmla'),
        (ListParsedFormula, 'rgbFmla'),
    ]

#class Feat11WSSListInfo(ptype.undefined):       # FIXME
#    pass

class CachedDiskHeader(pstruct.type):
    def __strStyleName(self):
        p = self.getparent(type=Feat11FieldDataItem)
        return XLUnicodeString if p['flags']['fSaveStyleName'].int() == 1 else ptype.undefined

    _fields_ = [
        (uint4, 'cbdxfHdrDisk'),
        (DXFN12List, 'rgHdrDisk'),
        (XLUnicodeString, 'strStyleName'),
    ]

####
class Feat11FieldDataItem(pstruct.type):
    class lfdt(pint.enum, uint4):
        _values_ = [
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
    class lfxidt(pint.enum, uint4):
        _values_ = [
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

    class ilta(pint.enum, uint4):
        _values_ = [
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

    class _flags(pbinary.flags):
        _fields_ = R([
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
        ])

    def __dxfFmtAgg(self):
        sz = self['cbFmtAgg'].li.int()
        return dyn.clone(DXFN12List, blocksize=lambda s:sz)

    def __dxfFmtInsertRow(self):
        sz = self['cbFmtInsertRow'].li.int()
        return dyn.clone(DXFN12List, blocksize=lambda s:sz)

    def __AutoFilter(self):
        tft = self['flag'].l
        return Feat11FdaAutoFilter if tft['fAutoFilter'] else ptype.undefined

    def __rgXmap(self):
        tft = self['flags'].l
        return Feat11XMap if tft['fLoadXmapi'] else ptype.undefined

    def __fmla(self):
        tft = self['flags'].l
        return Feat11FdaAutoFilter if tft['fLoadFmla'] else ptype.undefined

    def __totalFmla(self):
        tft = self['flags'].l
        return ListParsedArrayFormula if tft['fLoadTotalArray'] else ListParsedFormula

    def __strTotal(self):
        tft = self['flags'].l
        return XLUnicodeString if tft['fLoadTotalStr'] else ptype.undefined

    def __wssInfo(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return Feat11WSSListInfo if lt.int() == 1 else ptype.undefined

    def __qsif(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return uint4 if lt.int() == 3 else ptype.undefined

    def __dskHdrCache(self):
        tft = self.getparent(type=TableFeatureType).l
        return CachedDiskHeader if tft['crwHeader'].int() == 0 and tft['flags']['fSingleCell'].int() == 0 else ptype.undefined

    _fields_ = [
        (uint4, 'idField'),
        (lfdt, 'lfdt'),
        (lfxidt, 'lfxidt'),
        (ilta, 'ilta'),
        (uint4, 'cbFmtAgg'),
        (uint4, 'istnAgg'),
        (_flags, 'flags'),
        (uint4, 'cbFmtInsertRow'),
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
        (uint2, 'cId'),
        (lambda s: dyn.array(uint4, s['cId'].li.int()), 'rgId'),
    ]
class Feat11RgSharepointIdDel(Feat11RgSharepointId): pass
class Feat11RgSharepointIdChange(Feat11RgSharepointId): pass

class Feat11CellStruct(pstruct.type):
    _fields_ = [(uint4, 'idxRow'),(uint4,'idxField')]

class Feat11RgInvalidCells(pstruct.type):
    _fields_ = [
        (uint2, 'cCellInvalid'),
        (lambda s: dyn.array(Feat11CellStruct, s['cCellInvalid'].li.int()), 'rgCellInvalid'),
    ]

class TableFeatureType(pstruct.type):
    class crwHeader(Boolean, uint4): pass
    class crwTotals(Boolean, uint4): pass

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'unused2'), (1, 'fAutoFilter'), (1, 'fPersistAutoFilter'),
            (1, 'fShowInsertRow'), (1, 'fInsertRowInsCells'), (1, 'fLoadPldwIdDeleted'),
            (1, 'fShownTotalRow'), (1, 'reserved1'), (1, 'fNeedsCommit'),
            (1, 'fSingleCell'), (1, 'reserved2'), (1, 'fApplyAutoFilter'),
            (1, 'fForceInsertToBeVis'), (1, 'fCompressedXml'), (1, 'fLoadCSPName'),
            (1, 'fLoadPldwIdChanged'), (4, 'verXL'), (1, 'fLoadEntryId'),
            (1, 'fLoadPllstclInvalid'), (1, 'fGoodRupBld'), (1, 'unused3'),
            (1, 'fPublished'), (7, 'reserved3'),
        ])

    def __cSPName(self):
        return XLUnicodeString if self['flags'].li['fLoadCSPName'] else ptype.undefined
    def __entryId(self):
        return XLUnicodeString if self['flags'].li['fLoadEntryId'] else ptype.undefined
    def __idDeleted(self):
        return Feat11RgSharepointIdDel if self['flags'].li['fLoadPldwIdDeleted'] else ptype.undefined
    def __idChanged(self):
        return Feat11RgSharepointIdChange if self['flags'].li['fLoadPldwIdChanged'] else ptype.undefined
    def __cellInvalid(self):
        return Feat11RgInvalidCells if self['flags'].li['fLoadPllstclInvalid'] else ptype.undefined

    _fields_ = [
        (SourceType, 'lt'),
        (uint4, 'idList'),
        (crwHeader, 'crwHeader'),
        (crwTotals, 'crwTotals'),
        (uint4, 'idFieldNext'),
        (uint4, 'cbFSData'),    # GUARD: =64
        (uint2, 'rupBuild'),
        (uint2, 'unused1'),
        (_flags, 'flags'),
        (uint4, 'lPosStmCache'),
        (uint4, 'cbStmCache'),
        (uint4, 'cchStmCache'),
        (LEMMode, 'lem'),

        (dyn.array(ubyte1, 16), 'rgbHashParam'),
        (XLUnicodeString, 'rgbName'),
        (uint2, 'cFieldData'),
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
        (ubyte1, 'reserved1'),
        (uint4, 'reserved2'),
        (uint2, 'cref2'),
        (uint4, 'cbFeatData'),
        (uint2, 'reserved3'),
        (lambda s: dyn.array(Ref8U, s['cref2'].li.int()), 'refs2'),
        (__rgbFeat, 'rgbFeat'),
    ]

@RT_Excel.define
class Feature12(Feature11):
    type = 2168
    type = 0x878

class List12BlockLevel(pstruct.type):
    _fields_ = [
        (sint4, 'cbdxfHeader'),  # GUARD : >=0
        (sint4, 'istnHeader'),
        (sint4, 'cbdxfData'),
        (sint4, 'istnData'),
        (sint4, 'cbdxfAgg'),
        (sint4, 'istnAgg'),
        (sint4, 'cbdxfBorder'),
        (sint4, 'cbdxfHeaderBorder'),
        (sint4, 'cbdxfAggBorder'),

        (lambda s: (DXFN12List if s['cbdxfHeader'].li.int() > 0 else ptype.undefined), 'dxfHeader'),
        (lambda s: (DXFN12List if s['cbdxfData'].li.int() > 0 else ptype.undefined), 'dxfData'),
        (lambda s: (DXFN12List if s['cbdxfAgg'].li.int() > 0 else ptype.undefined), 'dxfAgg'),
        (lambda s: (DXFN12List if s['cbdxfBorder'].li.int() > 0 else ptype.undefined), 'dxfBorder'),
        (lambda s: (DXFN12List if s['cbdxfHeaderBorder'].li.int() > 0 else ptype.undefined), 'dxfHeaderBorder'),
        (lambda s: (DXFN12List if s['cbdxfAggBorder'].li.int() > 0 else ptype.undefined), 'dxfAggBorder'),

        (lambda s: (XLUnicodeString if s['istnHeader'].li.int() != -1 else ptype.undefined), 'stHeader'),
        (lambda s: (XLUnicodeString if s['istnData'].li.int() != -1 else ptype.undefined), 'stData'),
        (lambda s: (XLUnicodeString if s['istnAgg'].li.int() != -1 else ptype.undefined), 'stAgg'),
    ]

class List12TableStyleClientInfo(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1,'fFirstColumn'),
            (1,'fLastColumn'),
            (1,'fRowStripes'),
            (1,'fColumnStripes'),
            (2,'unused1'),
            (1,'fDefaultStyle'),
            (9,'unused2'),
        ])

    _fields_ = [
        (_flags, 'flags'),
        (XLUnicodeString,'stListStyleName'),
    ]

class List12DisplayName(pstruct.type):
    _fields_ = [
        (XLNameUnicodeString, 'stListName'),
        (XLUnicodeString, 'stListComment'),
    ]

@RT_Excel.define
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
        return ptype.undefined

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint2, 'lsd'),
        (uint4, 'idList'),
        (__rgb, 'rgb'),
    ]

@RT_Excel.define
class SerParent(uint2):
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
        (uint2, 'grbit'),
        (Ref8U, 'Ref8u'),
        (SectionRecord, 'sec'),
    ]

@RT_Excel.define
class SST(pstruct.type):
    type = 252
    type = 0xfc
    _fields_ = [
        (sint4, 'cstTotal'),     # GUARD: >=0
        (sint4, 'cstUnique'),    # GUARD: >=0
        (lambda s: dyn.array(XLUnicodeRichExtendedString, abs(s['cstUnique'].li.int())), 'rgb'),
    ]

class FontIndex(pint.enum, uint2):
    _values_ = [
        ('Default',             0),
        ('Default,Bold',        1),
        ('Default,Italic',      2),
        ('Default,Bold,Italic', 3),
    ]

class FormatRun(pstruct.type):
    _fields_ = [
        (uint2, 'ich'),
        (FontIndex, 'ifnt'),
    ]

class Phs(pstruct.type):
    class formatinfo(pbinary.struct):
        _fields_ = R([(2,'phType'),(2,'alcH'),(12,'unused')])

    _fields_ = [
        (FontIndex, 'ifnt'),
        (formatinfo, 'ph'),
    ]

if False:
    # FIXME: http://msdn.microsoft.com/en-us/library/dd924700(v=office.12).aspx
    # this type doesn't align with this structure definition
    class LPWideString(pstruct.type):
        _fields_ = [
            (uint2, 'cchCharacters'),
            (lambda s: dyn.clone(pstr.wstring, length=s['cchCharacters'].li.int()), 'rgchData'),
        ]

class RPHSSub(pstruct.type):
    _fields_ = [
        (uint2, 'crun'),
        (uint2, 'cch'),
        (lambda s: dyn.clone(pstr.wstring, length=s['cch'].li.int()), 'st'),
    ]

class PhRuns(pstruct.type):
    _fields_ = [
        (uint2, 'ichFirst'),
        (uint2, 'ichMom'),
        (uint2, 'cchMom'),
    ]

class ExtRst(pstruct.type):
    _fields_ = [
        (uint2, 'reserved'),
        (uint2, 'cb'),
        (Phs, 'phs'),
        (RPHSSub, 'rphssub'),
        (lambda s: dyn.array(PhRuns, s['rphssub'].li['crun'].int()), 'rgphruns')
    ]

class XLUnicodeRichExtendedString(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fHighByte'),
            (1, 'reserved1'),
            (1, 'fExtSt'),
            (1, 'fRichSt'),
            (4, 'reserved2'),
        ])

    def __cRun(self):
        f = self['flags'].l
        return uint2 if f['fRichSt'] else pint.uint_t
    def __cbExtRst(self):
        f = self['flags'].l
        return sint4 if f['fExtSt'] else pint.int_t
    def __rgb(self):
        f = self['flags'].l
        if f['fHighByte']:
            return dyn.clone(pstr.wstring, length=int(self['cch'].li))
        return dyn.clone(pstr.string, length=int(self['cch'].li))
    def __ExtRst(self):
        f = self['flags'].l
        return ExtRst if f['fExtSt'] else ptype.undefined

    _fields_ = [
        (uint2, 'cch'),
        (_flags, 'flags'),
        (__cRun, 'cRun'),
        (__cbExtRst, 'cbExtRst'),
        (__rgb, 'rgb'),
        (lambda s: dyn.array(FormatRun, s['cRun'].li.int()), 'rgRun'),
        (__ExtRst, 'ExtRst'),
    ]

class FilePointer(uint4): pass
class ISSTInf(pstruct.type):
    _fields_ = [
        (FilePointer, 'ib'),
        (uint2, 'cbOffset'),
        (uint2, 'reserved'),
    ]

@RT_Excel.define
class ExtSST(pstruct.type):
    type = 255
    type = 0xff
    def __rgISSTInf(self):
        rg = self.getparent(RecordGeneral)
        container = rg.p
        idx = container.value.index(rg)
        previous = container[idx-1].d
        cu, dsst = previous['cstUnique'].li.int(), self['dsst'].li.int()
        count = (cu / dsst) + (1 if cu % dsst else 0)
        return dyn.array(ISSTInf, count)

    _fields_ = [
        (uint2, 'dsst'),
        (__rgISSTInf, 'rgISSTInf'),
    ]

class ControlInfo(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fDefault'),
            (1, 'fHelp'),
            (1, 'fCancel'),
            (1, 'fDismiss'),
            (12, 'reserved1'),
        ])
    _fields_ = [
        (_flags, 'flags'),
        (uint2, 'accel1'),
        (uint2, 'reserved2'),
    ]

class ObjectParsedFormula(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (15, 'cce'),
            (1, 'reserved'),
        ])

    def __rgce(self):
        cce = self['flags'].li['cce']
        return dyn.clone(Rgce, blocksize=lambda s,cce=cce: cce)

    _fields_ = [
        (_flags, 'flags'),
        (uint4, 'unused'),
        (__rgce, 'rgce'),
    ]

class PictFmlaEmbedInfo(pstruct.type):
    def __strClass(self):
        cb = self['cbClass'].li.int()
        if cb:
            return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda s,cb=cb: cb)
        return ptype.undefined

    _fields_ = [
        (ubyte1, 'ttb'),
        (ubyte1, 'cbClass'),
        (ubyte1, 'reserved'),
        (__strClass, 'strClass'),
    ]

class ObjFmla(pstruct.type):
    #class _formula(pstruct.type):
    #    def __formula(self):
    #        cb = self.blocksize()
    #        return dyn.clone(ObjectParsedFormula, blocksize=lambda s,cb=cb: cb - s.p['embedInfo'].blocksize())

    #    _fields_ = [
    #        (__formula, 'formula'),
    #        (PictFmlaEmbedInfo, 'embedInfo'),
    #    ]

    #def __fmla(self):
    #    cb = self['cbFmla'].li.int()
    #    return dyn.clone(ObjectParsedFormula, blocksize=lambda s,cb=cb: cb)

    _fields_ = [
        (uint2, 'cbFmla'),
        (ObjectParsedFormula, 'fmla'),
        (PictFmlaEmbedInfo, 'embedInfo'),
        (lambda s: dyn.block(s['cbFmla'].li.int() - s['fmla'].li.int() - s['embedInfo'].li.int()), 'padding'),
    ]

class ObjFmlaNoSize(ObjectParsedFormula):
    pass

class Ft(ptype.definition):
    cache = {}

class FtGeneral(pstruct.type):
    def __data(self):
        res, cb = self['ft'].li.int(), self['cb'].li.int()
        return Ft.get(res, blocksize=lambda s,cb=cb:cb)

    _fields_ = [
        (uint2, 'ft'),
        (uint2, 'cb'),
        (__data, 'data'),
    ]

@Ft.define
class FtReserved(ptype.undefined):
    type = 0x0000

@Ft.define
class FtCmo(pstruct.type):
    type = 0x0015
    class _ot(pint.enum, uint2):
        _values_ = [
            ('Group', 0x0000),
            ('Line', 0x0001),
            ('Rectangle', 0x0002),
            ('Oval', 0x0003),
            ('Arc', 0x0004),
            ('Chart', 0x0005),
            ('Text', 0x0006),
            ('Button', 0x0007),
            ('Picture', 0x0008),
            ('Polygon', 0x0009),
            ('Checkbox', 0x000B),
            ('Radio button', 0x000C),
            ('Edit box', 0x000D),
            ('Label', 0x000E),
            ('Dialog box', 0x000F),
            ('Spin control', 0x0010),
            ('Scrollbar', 0x0011),
            ('List', 0x0012),
            ('Group box', 0x0013),
            ('Dropdown list', 0x0014),
            ('Note', 0x0019),
            ('OfficeArt object', 0x001E),
        ]
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fLocked'),
            (1, 'reserved'),
            (1, 'fDefaultSize'),
            (1, 'fPublished'),
            (1, 'fPrint'),
            (1, 'unused1'),
            (1, 'unused2'),
            (1, 'fDisabled'),
            (1, 'fUIObj'),
            (1, 'fRecalcObj'),
            (1, 'unused3'),
            (1, 'unused4'),
            (1, 'fRecalcObjAlways'),
            (1, 'unused5'),
            (1, 'unused6'),
            (1, 'unused7'),
        ])

    _fields_ = [
        (_ot, 'ot'),
        (uint2, 'id'),
        (_flags, 'flags'),
        (uint4, 'unused8'),
        (uint4, 'unused9'),
        (uint4, 'unused10'),
    ]

@Ft.define
class FtGmo(pstruct.type):
    type = 0x0006
    _fields_ = [
        (uint2, 'unused'),
    ]

@Ft.define
class FtCf(pint.enum, uint2):
    type = 0x0007
    _values_ = [
        ('emf', 0x0002),
        ('bmp', 0x0009),
        ('unspecified', 0xffff),
    ]

@Ft.define
class FtPioGrbit(pbinary.flags):
    type = 0x0008
    _fields_ = R([
        (1, 'fAutoPict'),
        (1, 'fDde'),
        (1, 'fPrintCalc'),
        (1, 'fIcon'),
        (1, 'fCtl'),
        (1, 'fPrstm'),
        (1, 'unused1'),
        (1, 'fCamera'),
        (1, 'fDefaultSize'),
        (1, 'fAutoload'),
        (6, 'unused1'),
    ])

@Ft.define
class FtCbls(pstruct.type):
    type = 0x000a
    _fields_ = [
        (uint4, 'unused1'),
        (uint4, 'unused2'),
        (uint4, 'unused3'),
    ]

@Ft.define
class FtRbo(pstruct.type):
    type = 0x000b
    _fields_ = [
        (uint4, 'unused1'),
        (uint2, 'unused2'),
    ]

@Ft.define
class FtSbs(pstruct.type):
    type = 0x000c
    class _fHoriz(pint.enum, uint2):
        _values_ = [('vertical',0),('horizontal',1)]
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fDraw'),
            (1, 'fDrawSliderOnly'),
            (1, 'fTrackElevator'),
            (1, 'fNo3d'),
            (12, 'unused2'),
        ])
    _fields_ = [
        (uint4, 'unused1'),
        (sint2, 'iVal'),
        (sint2, 'iMin'),
        (sint2, 'iMax'),
        (sint2, 'dlnc'),
        (sint2, 'dPage'),
        (_fHoriz, 'fHoriz'),
        (sint2, 'dxScroll'),
        (_flags, 'flags'),
    ]

@Ft.define
class FtNts(pstruct.type):
    type = 0x000d
    class _fSharedNote(pint.enum, uint2):
        _values_ = [('unshared',0),('shared',1)]
    _fields_ = [
        (dyn.block(16), 'guid'),
        (_fSharedNote, 'fSharedNote'),
        (uint4, 'unused'),
    ]

@Ft.define
class FtMacro(ObjFmlaNoSize):
    type = 0x0004

class PictFmlaKey(pstruct.type):
    _fields_ = [
        (uint4, 'cbKey'),
        (lambda s: dyn.block(s['cbKey'].li.int()), 'keyBuf'),
        (ObjFmla, 'fmlaLinkedCell'),    # FIXME
        (ObjFmla, 'fmlaListFillRange'),
    ]

@Ft.define
class FtPictFmla(pstruct.type):
    type = 0x0009
    _fields_ = [
        (ObjFmlaNoSize, 'fmla'),
        (uint4, 'IPosInCtlStm'),
        (PictFmlaKey, 'key'),
    ]

@Ft.define(type=0x0014)
@Ft.define(type=0x000e)
class ObjLinkFmla(ObjFmlaNoSize):
    type = 0x0014

@Ft.define
class FtCblsData(pstruct.type):
    type = 0x0012
    class _fChecked(pint.enum, uint2):
        _values_ = [
            ('unchecked', 0),
            ('checked', 1),
            ('mixed', 2),
        ]
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fNo3d'),
            (15, 'unused'),
        ])
    _fields_ = [
        (uint2, 'fChecked'),
        (uint2, 'accel'),
        (uint2, 'reserved'),
        (_flags, 'flags'),
    ]

@Ft.define
class FtRboData(pstruct.type):
    type = 0x000b
    class _fFirstBtn(pint.enum, uint2):
        _values_ = [('first', 1),('other',0)]
    _fields_ = [
        (ObjId, 'idRadNext'),
        (_fFirstBtn, 'fFirstBtn'),
    ]

@Ft.define
class FtEdoData(pstruct.type):
    type = 0x0010
    class _ivtEdit(pint.enum, uint2):
        _values_ = [
            ('string', 0x0000),
            ('integer', 0x0001),
            ('number', 0x0002),
            ('range', 0x0003),
            ('formula', 0x0004),
        ]
    class _fMultiLine(pint.enum, uint2):
        _values_ = [
            ('single', 0x0000),
            ('multi', 0x0001),
        ]
    class _fVScroll(pint.enum, uint2):
        _values_ = [
            ('hidden', 0x0000),
            ('shown', 0x0001),
        ]
    _fields_ = [
        (_ivtEdit, 'ivtEdit'),
        (_fMultiLine, 'fMultiLine'),
        (_fVScroll, 'fVScroll'),
        (ObjId, 'id'),
    ]

class LbsDropData(pstruct.type):
    class _flags(pbinary.struct):
        class _wStyle(pbinary.enum):
            width = 2
            _values_ = [
                ('combo', 0),
                ('edit', 1),
                ('simple', 2),
            ]
        _fields_ = R([
            (_wStyle, 'wStyle'),
            (1, 'unused1'),
            (1, 'fFiltered'),
            (12, 'unused2'),
        ])

    _fields_ = [
        (_flags, 'flags'),
        (uint2, 'cLine'),
        (uint2, 'dxMin'),
        (XLUnicodeString, 'str'),
        (ubyte1, 'unused3'),
    ]

@Ft.define
class FtLbsData(pstruct.type):
    type = 0x0013
    class _flags(pbinary.flags):
        class _lct(pbinary.enum):
            width = 8
            _values_ = [
                ('regular', 0x01),
                ('pivot-page', 0x02),
                ('autofilter', 0x03),
                ('autocomplete', 0x05),
                ('validation', 0x06),
                ('pivot-rowcol', 0x07),
                ('row', 0x09),
            ]
        _fields_ = R([
            (1, 'UseCB'),
            (1, 'fValidPlex'),
            (1, 'fValidIds'),
            (1, 'fNo3d'),
            (1, 'wListSelType'),
            (1, 'unused'),
            (1, 'reserved'),
            (_lct, 'lct'),
        ])

    class _bsels(Boolean, ubyte1): pass

    _fields_ = [
        (ObjFmlaNoSize, 'fmla'),
        (uint2, 'cLines'),
        (uint2, 'iSel'),
        (_flags, 'flags'),
        (ObjId, 'idEdit'),
        (LbsDropData, 'dropData'),
        (lambda s: dyn.array(XLUnicodeString, s['cLines'].li.int()), 'dropData'),
        (lambda s: dyn.array(s._bsels, s['cLines'].li.int()), 'bsels'),
    ]

@Ft.define
class FtGboData(pstruct.type):
    type = 0x000f
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fNo3d'),
            (15, 'unused2'),
        ])
    _fields_ = [
        (uint2, 'accel'),
        (uint2, 'reserved'),
        (_flags, 'flags'),
    ]

@RT_Excel.define
class Obj(pstruct.type):
    type = 0x05d
    type = 93
    def __properties(self):
        p = self.getparent(RecordGeneral)
        cb = p['header'].li.Length() - self['cmo'].li.size()
        return dyn.blockarray(FtGeneral, cb)

    _fields_ = [
        (FtGeneral, 'cmo'),
        (__properties, 'props'),
    ]

@RT_Excel.define
class TxO(pstruct.type):
    type = 0x1b6
    type = 438

    class _flags(pbinary.flags):
        class _hAlignment(pbinary.enum):
            width = 3
            _values_ = [
                ('left', 1),
                ('center', 2),
                ('right', 3),
                ('justify', 4),
                ('distributed', 7),
            ]
        class _vAlignment(pbinary.enum):
            width = 3
            _values_ = [
                ('top', 1),
                ('middle', 2),
                ('bottom', 3),
                ('justify', 4),
                ('distributed', 7),
            ]

        _fields_ = [
            (1, 'reserved1'),
            (_hAlignment, 'hAlignment'),
            (_vAlignment, 'vAlignment'),
            (2, 'reserved2'),
            (1, 'fLockText'),
            (4, 'reserved3'),
            (1, 'fJustLast'),
            (1, 'fSecretEdit'),
        ]

    class _rot(pint.enum, uint2):
        _values_ = [
            ('none', 0),
            ('stacked', 1),
            ('ccw', 2),
            ('cw', 3),
        ]

    def __previousObjRecord(self, **count):
        rg = self.getparent(RecordGeneral)
        return rg.previousRecord(Obj, **count)

    def __fmla(self):
        rg = self.getparent(RecordGeneral)
        cb = rg['header'].li.Length()
        flds = map(operator.itemgetter(1), self._fields_)[:-1]
        res = sum(n.li.size() for n in map(self.__getitem__, flds))
        return dyn.block(cb - res)

    _fields_ = [
        (_flags, 'flags'),
        (_rot, 'rot'),
        (lambda s: uint2 if s.__previousObjRecord().d['cmo'].li['data']['ot'].int() not in (0,5,7,11,12,14) else pint.uint_t, 'reserved4'),
        (lambda s: uint4 if s.__previousObjRecord().d['cmo'].li['data']['ot'].int() not in (0,5,7,11,12,14) else pint.uint_t, 'reserved5'),
        (lambda s: ControlInfo if s.__previousObjRecord().d['cmo'].li['data']['ot'].int() in (0,5,7,11,12,14) else ptype.undefined, 'controlInfo'),
        (uint2, 'cchText'),
        (uint2, 'cbRuns'),
        (FontIndex, 'ifntEmpty'),
#        (ObjFmla, 'fmla'),     # FIXME
        (__fmla, 'fmla'),
    ]

@RT_Excel.define
class Continue(ptype.block):
    type = 0x3c
    def blocksize(self):
        rg = self.getparent(RecordGeneral)
        return rg['header'].Length()

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
        print 'successfully parsed {:d} streams of {:#x} bytes from {:s}'.format(len(z), z.size(), filename)
        print 'z: found {:d} records'.format(reduce(lambda x,y:x+len(y),z,0))
    else:
        print 'unsuccessfully parsed {:d} biffsubstreams from {:s} ({:d} != {:d})'.format(len(z), filename, z.size(), z.source.size())
        print 'z: found {:d} records'(reduce(lambda x,y:x+len(y),z,0))

