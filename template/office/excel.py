from ptypes import *
from . import art,graph
from . import *

import operator,functools,itertools
import logging

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

@Record.define
class BIFF5(ptype.definition):
    type, cache = '.'.join([__name__, 'BIFF5']), {}

    class unknown(undefined):
        def classname(self):
            res = getattr(self, BIFF5.attribute, None)
            if res is None:
                return self.typename()
            type, none = res
            return "{:s}<{:04x}>".format(self.typename(), type) if none is None else "{:s}<{:04x},{!r}>".format(self.typename(), type, none)
    default = unknown

    @classmethod
    def __get__(cls, key, default, **kwargs):
        type, none = key if isinstance(key, (tuple, list)) else (key, None)
        if none is not None:
            return default
        return super(BIFF5, cls).__get__(type, default, **kwargs)

@Record.define
class BIFF8(ptype.definition):
    type, cache = '.'.join([__name__, 'BIFF8']), {}

    class unknown(undefined):
        def classname(self):
            res = getattr(self, BIFF8.attribute, None)
            if res is None:
                return self.typename()
            type, none = res
            return "{:s}<{:04x}>".format(self.typename(), type) if none is None else "{:s}<{:04x},{!r}>".format(self.typename(), type, none)
    default = unknown

    @classmethod
    def __get__(cls, key, default, **kwargs):
        type, none = key if isinstance(key, (tuple, list)) else (key, None)
        if none is not None:
            return default
        return super(BIFF8, cls).__get__(type, default, **kwargs)

RecordGeneralBase = RecordGeneral
class RecordGeneral(RecordGeneralBase):
    class Header(pstruct.type):
        _fields_ = [
            (uint2, 'type'),
            (uint2, 'length'),
        ]
        def summary(self):
            if self.initializedQ():
                type, length = map(self.__getitem__, ('type','length'))
                return 'type={type:#06x} length={length:#x}({length:d})'.format(type=type.int(), length=length.int())
            return super(RecordGeneral.Header, self).summary()
        def Type(self):
            version = self.attributes.get('_biffver', 8)
            return BIFF5.type if version <= 5 else BIFF8.type
        def Instance(self):
            return self['type'].int(), None
        def Length(self):
            return self['length'].int() if len(self.value) == 2 and self['length'].initializedQ() else 0

    def alloc(self, **fields):
        res = super(RecordGeneralBase, self).alloc(**fields)
        if operator.contains(fields, 'header'):
            return res
        rt, cb = getattr(res.d, 'type', 0), sum(item.size() for item in [res.d, res['extra']])
        res.h.set(type=rt if isinstance(rt, six.integer_types) else rt[0], length=cb)
        return res

class RecordContainer(RecordContainer):
    _object_ = RecordGeneral

    def __init__(self, **attributes):
        version_attributes = ['_biffver', 'biff', '_biff', 'version', '_version']

        # grab the version if it's defined
        try:
            version = getattr(self, '_biffver') if hasattr(self, '_biffver') else next(attributes[item] for item in version_attributes if item in attributes)

        # if we couldn't find one, then set a default one.
        except StopIteration:
            version = 8

            cls = self.__class__
            logging.warn("{:s} : Assuming version {:d} as version attribute is missing.".format('.'.join([__name__, cls.__name__]), version))

        # delete any attributes that might've contained our version
        else:
            [ attributes.pop(item) for item in version_attributes if item in attributes ]

        # finally we can add the version to our recursive attributes to assign
        recurse = attributes.setdefault('recurse', {})
        recurse.setdefault('_biffver', version)
        super(RecordContainer, self).__init__(**attributes)

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
class ColorICV(uint4): pass
class TabId(uint2): pass

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
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class RgceLoc(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColRelU, 'column'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class RgceLocRel(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColRelNegU, 'column'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class RgceElfLoc(pstruct.type):
    _fields_ = [
        (RwU, 'row'),
        (ColElfU, 'column'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class RgceArea(pstruct.type):
    _fields_ = [
        (RwU, 'rowFirst'),
        (RwU, 'rowLast'),
        (ColRelU, 'columnFirst'),
        (ColRelU, 'columnLast'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class RgceAreaRel(pstruct.type):
    _fields_ = [
        (RwU, 'rowFirst'),
        (RwU, 'rowLast'),
        (ColRelNegU, 'columnFirst'),
        (ColRelNegU, 'columnLast'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class Ts(pbinary.flags):
    _fields_ = R([
        (1, 'unused1'),
        (1, 'ftsItalic'),
        (5, 'unused2'),
        (1, 'ftsStrikeout'),
        (24, 'unused3'),
    ])

class Stxp(pstruct.type):
    _fields_ = [
        (sint4, 'twpHeight'),
        (Ts, 'ts'),
        (sint2, 'bls'),
        (sint2, 'sss'),
        (ubyte1, 'uls'),
        (ubyte1, 'bFamily'),
        (ubyte1, 'bCharSet'),
        (ubyte1, 'unused'),
    ]

class LongRGB(pstruct.type):
    _fields_ = [ (ubyte1,'red'),(ubyte1,'green'),(ubyte1,'blue'),(ubyte1,'reserved') ]

class LongRGBA(pstruct.type):
    _fields_ = [ (ubyte1,'red'),(ubyte1,'green'),(ubyte1,'blue'),(ubyte1,'alpha') ]

class XColorType(pint.enum, uint2):
    _values_ = [
        ('XCLRAUTO', 0x00000000),
        ('XCLRINDEXED', 0x00000001),
        ('XCLRRGB', 0x00000002),
        ('XCLRTHEMED', 0x00000003),
        ('XCLRNINCHED', 0x00000004),
    ]

class CFColor(pstruct.type):
    def __xclrValue(self):
        res = self['xclrType'].li
        if res == 'XCLRAUTO':
            return undefined
        elif res == 'XCLRINDEXED':
            return ColorICV
        elif res == 'XCLRRGB':
            return LongRGBA
        elif res == 'XCLRTHEMED':
            return ColorTheme
        logging.warn('{:s}.__xclrValue : Unknown xclrType value. : {:04x}'.format(self.instance(), res.int()))
        return undefined

    _fields_ = [
        (XColorType, 'xclrType'),
        (__xclrValue, 'xclrValue'),
        (Xnum, 'numTint'),
    ]

class CFVOParsedFormula(pstruct.type):
    def __rgce(self):
        cce = self['cce'].li.int()
        # FIXME
        return dyn.clone(Rgce, blocksize=lambda _, size=cce: size)

    _fields_ = [
        (uint2, 'cce'),
        (__rgce, 'rgce'),
    ]

class CFVO(pstruct.type):
    _fields_ = [
        (ubyte1, 'cfvoType'),
        (CFVOParsedFormula, 'fmla'),
        (Xnum, 'numValue'),
    ]

class CFMStateItem(pstruct.type):
    _fields_ = [
        (CFVO, 'cfvo'),
        (ubyte1, 'fEqual'),
        (uint4, 'unused'),
    ]

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

class HorizAlign(pbinary.enum):
    width = 3
    _values_ = [
        ('ALCNIL', 0xFF), # Alignment not specified
        ('ALCGEN', 0x00), # General alignment
        ('ALCLEFT', 0x01), # Left alignment
        ('ALCCTR', 0x02), # Centered alignment
        ('ALCRIGHT', 0x03), # Right alignment
        ('ALCFILL', 0x04), # Fill alignment
        ('ALCJUST', 0x05), # Justify alignment
        ('ALCCONTCTR', 0x06), # Center-across-selection alignment
        ('ALCDIST', 0x07), # Distributed alignment
    ]

class VertAlign(pbinary.enum):
    width = 3
    _values_ = [
        ('ALCVTOP', 0x00), # Top alignment
        ('ALCVCTR', 0x01), # Center alignment
        ('ALCVBOT', 0x02), # Bottom alignment
        ('ALCVJUST', 0x03), # Justify alignment
        ('ALCVDIST', 0x04), # Distributed alignment
    ]

class ReadingOrder(pbinary.enum):
    width = 2
    _values_ = [
        ('READING_ORDER_CONTEXT', 0x00), # Context reading order
        ('READING_ORDER_LTR', 0x01), # Left-to-right reading order
        ('READING_ORDER_RTL', 0x02), # Right-to-left reading order
    ]

class BorderStyle(pbinary.enum):
    width = 4
    _values_ = [
        ('NONE', 0x0000), # No border
        ('THIN', 0x0001), # Thin line
        ('MEDIUM', 0x0002), # Medium line
        ('DASHED', 0x0003), # Dashed line
        ('DOTTED', 0x0004), # Dotted line
        ('THICK', 0x0005), # Thick line
        ('DOUBLE', 0x0006), # Double line
        ('HAIR', 0x0007), # Hairline
        ('MEDIUMDASHED', 0x0008), # Medium dashed line
        ('DASHDOT', 0x0009), # Dash-dot line
        ('MEDIUMDASHDOT', 0x000A), # Medium dash-dot line
        ('DASHDOTDOT', 0x000B), # Dash-dot-dot line
        ('MEDIUMDASHDOTDOT', 0x000C), # Medium dash-dot-dot line
        ('SLANTDASHDOT', 0x000D), # Slanted dash-dot-dot line
    ]

class FillPattern(pbinary.enum):
    width = 6
    _values_ = [
        ('FLSNULL', 0x00), # No fill pattern
        ('FLSSOLID', 0x01), # Solid
        ('FLSMEDGRAY', 0x02), # 50% gray
        ('FLSDKGRAY', 0x03), # 75% gray
        ('FLSLTGRAY', 0x04), # 25% gray
        ('FLSDKHOR', 0x05), # Horizontal stripe
        ('FLSDKVER', 0x06), # Vertical stripe
        ('FLSDKDOWN', 0x07), # Reverse diagonal stripe
        ('FLSDKUP', 0x08), # Diagonal stripe
        ('FLSDKGRID', 0x09), # Diagonal crosshatch
        ('FLSDKTRELLIS', 0x0A), # Thick Diagonal crosshatch
        ('FLSLTHOR', 0x0B), # Thin horizontal stripe
        ('FLSLTVER', 0x0C), # Thin vertical stripe
        ('FLSLTDOWN', 0x0D), # Thin reverse diagonal stripe
        ('FLSLTUP', 0x0E), # Thin diagonal stripe
        ('FLSLTGRID', 0x0F), # Thin horizontal crosshatch
        ('FLSLTTRELLIS', 0x10), # Thin diagonal crosshatch
        ('FLSGRAY125', 0x11), # 12.5% gray
        ('FLSGRAY0625', 0x12), # 6.25% gray
    ]

class RevisionType(pint.enum, uint2):
    _values_ = [
        ('REVTINSRW', 0x0000), # Insert Row.
        ('REVTINSCOL', 0x0001), # Insert Column.
        ('REVTDELRW', 0x0002), # Delete Row.
        ('REVTDELCOL', 0x0003), # Delete Column.
        ('REVTMOVE', 0x0004), # Cell Move.
        ('REVTINSERTSH', 0x0005), # Insert Sheet.
        ('REVTSORT', 0x0007), # Sort.
        ('REVTCHANGECELL', 0x0008), # Cell Change.
        ('REVTRENSHEET', 0x0009), # Rename Sheet.
        ('REVTDEFNAME', 0x000A), # Defined name Change.
        ('REVTFORMAT', 0x000B), # Format Revision.
        ('REVTAUTOFMT', 0x000C), # AutoFormat Revision.
        ('REVTNOTE', 0x000D), # Comment Revision.
        ('REVTHEADER', 0x0020), # Header (meta-data) Revision.
        ('REVTCONFLICT', 0x0025), # Conflict.
        ('REVTADDVIEW', 0x002B), # Custom view Add.
        ('REVTDELVIEW', 0x002C), # Custom view Delete.
        ('REVTTRASHQTFIELD', 0x002E), # Query table field Removal.
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
        return True if rec == EOF.type or value.getoffset() + value.size() >= self.parent.getoffset() + self.parent.blocksize() else False

    def properties(self):
        flazy = (lambda item: item['data'].d.l) if getattr(self, 'lazy', False) else (lambda item: item['data'])
        record = flazy(self[0])

        dt, vers, year, build = (record[fld] for fld in ['dt', 'vers', 'rupYear', 'rupBuild'])

        res = super(BiffSubStream, self).properties()
        res['document-type'] = dt.summary()
        res['document-version'] = '{:d}.{:d}'.format(vers.int() // 0x100, vers.int() & 0xff)
        res['document-year'] = year.int()
        res['document-build'] = build.int()
        return res

class File(File):
    _object_ = BiffSubStream

    def __init__(self, **attributes):
        version_attributes = ['_biffver', 'biff', '_biff', 'version', '_version']

        # grab the version if it's defined
        try:
            version = getattr(self, '_biffver') if hasattr(self, '_biffver') else next(attributes[item] for item in version_attributes if item in attributes)

        # if we couldn't find one, then set a default one.
        except StopIteration:
            version = 8

            cls = self.__class__
            logging.warn("{:s} : Assuming version {:d} as version attribute is missing.".format('.'.join([__name__, cls.__name__]), version))

        # delete any attributes that might've contained our version
        else:
            [ attributes.pop(item) for item in version_attributes if item in attributes ]

        # finally we can add the version to our recursive attributes to assign
        recurse = attributes.setdefault('recurse', {})
        recurse.setdefault('_biffver', version)
        super(File, self).__init__(**attributes)

    def details(self):
        try:
            items = [item for item in self]
        except ptypes.error.InitializationError:
            return super(File, self).details()

        res = []
        for idx, item in enumerate(items):
            if len(item) and isinstance(item[0].d, BOF):
                summary = ' : '.join(["{:s}(version={:d})".format(item[0].d.DocumentType().str(), item[0].d.Version()), item.summary()])
            else:
                summary = item.summary()
            res.append("[{:x}] {:s}[{:d}] : {:s}".format(item.getoffset(), item.classname(), idx, summary))

        return '\n'.join(res) + '\n'

###
@BIFF5.define
@BIFF8.define
class CALCCOUNT(pstruct.type):
    type = 0x000c
    type = 12
    _fields_ = [
        (uint2, 'cIter'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class CALCMODE(pint.enum, uint2):
    type = 0xd
    type = 13
    _values_ = [
        ('Manual', 0),
        ('Automatic', 1),
        ('No Tables', 2),
    ]

@BIFF5.define
@BIFF8.define
class REFMODE(pstruct.type):
    type = 0x000f
    type = 15
    class _fRefA1(pint.enum, uint2):
        _values_ = [
            ('R1C1', 0),
            ('A1', 1),
        ]
    _fields_ = [
        (_fRefA1, 'fRefA1'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class DELTA(pstruct.type):
    type = 0x0010
    type = 16
    _fields_ = [
        (Xnum, 'numDelta'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class ITERATION(pstruct.type):
    type = 0x0011
    type = 17
    class _fIter(pint.enum, uint2):
        _values_ = [
            ('off', 0),
            ('on', 1),
        ]
    _fields_ = [
        (_fIter, 'fIter'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class SAVERECALC(pstruct.type):
    type = 0x005f
    type = 95
    class _fSaveRecalc(pint.enum, uint2):
        _values_ = [
            ('no', 0),
            ('yes', 1),
        ]
    _fields_ = [
        (_fSaveRecalc, 'fSaveRecalc'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class PRINTHEADERS(pstruct.type):
    type = 0x002a
    type = 42
    class _fPrintRwCol(pint.enum, uint2):
        _values_ = [
            ('no', 0),
            ('yes', 1),
        ]
    _fields_ = [
        (_fPrintRwCol, 'fPrintRwCol'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class PRINTGRIDLINES(pstruct.type):
    type = 0x002b
    type = 43
    class _fPrintGrid(pint.enum, uint2):
        _values_ = [
            ('no', 0),
            ('yes', 1),
        ]
    _fields_ = [
        (_fPrintGrid, 'fPrintGrid'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class GUTS(pstruct.type):
    type = 0x0080
    type = 128
    _fields_ = [
        (uint2, 'dxRwGut'),
        (uint2, 'dyColGut'),
        (uint2, 'iLevelRwMac'),
        (uint2, 'iLevelColMac'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class WSBOOL(pbinary.flags):
    type = 0x0081
    type = 129
    _fields_ = R([
        (1, 'fShowAutoBreaks'),
        (3, 'unused'),
        (1, 'fDialog'),
        (1, 'fApplyStyles'),
        (1, 'fRwSumsBelow'),
        (1, 'fColSumsRight'),
        (1, 'fFitToPage'),
        (1, 'reserved1'),
        (2, 'fDspGuts'),
        (2, 'reserved2'),
        (1, 'fAee'),
        (1, 'fAfe'),
    ])

@BIFF5.define
@BIFF8.define
class GRIDSET(pstruct.type):
    type = 0x0082
    type = 130
    class _fGridSet(pint.enum, uint2):
        _values_ = [
            ('no', 0),
            ('yes', 1),
        ]
    _fields_ = [
        (_fGridSet, 'fGridSet'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class GRIDSET(pstruct.type):
    type = 0x0225
    type = 549

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fUnsynced'),
            (1, 'fDyZero'),
            (1, 'fExAsc'),
            (1, 'fExDsc'),
            (12, 'unused'),
        ])

    _fields_ = [
        (_flags, 'grbit'),
        (uint2, 'miyRw'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in reversed(self._fields_))

@BIFF5.define
@BIFF8.define
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
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

###
@BIFF5.define
@BIFF8.define
class RRTabId(parray.block):
    _object_ = USHORT
    type = 0x13d
    type = 317
    def blocksize(self):
        try:
            rec = self.getparent(RecordGeneralBase)
        except ptypes.error.ItemNotFoundError:
            return 0
        return rec['header'].li.Length()

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
    def summary(self):
        return "rt={:0{:d}x} grbitFrt={!s}".format(self['rt'].int(), 2 + 2 * self['rt'].size(), self['grbitFrt'].summary())

class FrtHeaderOld(pstruct.type):
    _fields_ = [
        (uint2, 'rt'),
        (FrtFlags, 'grbitFrt'),
    ]
    def summary(self):
        return "rt={:0{:d}x} grbitFrt={!s}".format(self['rt'].int(), 2 + 2 * self['rt'].size(), self['grbitFrt'].summary())

@BIFF5.define
@BIFF8.define
class MTRSettings(pstruct.type):
    type = 2202
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'fMTREnabled'),
        (uint4, 'fUserSetThreadCount'),
        (uint4, 'cUserThreadCount')
    ]
###
@BIFF5.define
@BIFF8.define
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
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class LabelSst(pstruct.type):
    type = 253
    _fields_ = [
        (Cell, 'cell'),
        (uint4, 'isst')
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in reversed(self._fields_))
###
@BIFF5.define
@BIFF8.define
class RK(pstruct.type):
    type = 638
    type = 0x273
    _fields_ = [
        (uint2, 'rw'),
        (uint2, 'col'),
        (RkRec, 'rkrec')
    ]

@BIFF5.define
@BIFF8.define
class MulBlank(pstruct.type):
    type = 190
    type = 0xbe

    def __rgixfe(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            # XXX: unable to calculate number of elements without the blocksize
            return dyn.array(IXFCell, 0)

        res = cb - sum(self[fld].li.size() for fld in ['rw', 'colFirst', 'colFirst'])
        return dyn.blockarray(IXFCell, res)

    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (__rgixfe, 'rgixfe'),
        (Col, 'colLast')
    ]

###
@BIFF5.define
@BIFF8.define
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
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class MergeCells(pstruct.type):
    type = 229
    _fields_ = [
        (uint2, 'cmcs'),
        (lambda self: dyn.array(Ref8, self['cmcs'].li.int()), 'rgref')
    ]
###
@BIFF5.define
@BIFF8.define
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
@BIFF5.define
@BIFF8.define
class Frame(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fAutoSize'),
            (1, 'fAutoPosition'),
            (14, 'reserved')
        ])

    type = 4146
    _fields_ = [
        (uint2, 'frt'),
        (_flags, 'flags')
    ]

###
@BIFF5.define
@BIFF8.define
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
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

class XLUnicodeString(pstruct.type):
    class _grbit(pbinary.flags):
        _fields_ = [
            (4, '(Reserved)'),
            (1, 'fRichSt'),
            (1, 'fExtSt'),
            (1, 'Reserved'),
            (1, 'fHighByte'),
        ]

    def __crun(self):
        flags = self['grbit'].li
        return uint2 if flags['fRichSt'] else pint.uint_t

    def __cchExtRst(self):
        flags = self['grbit'].li
        return uint4 if flags['fExtSt'] else pint.uint_t

    def __rgb(self):
        length, flags = (self[fld].li for fld in ['cch', 'grbit'])
        return dyn.clone(pstr.wstring if flags['fHighByte'] else pstr.string, length=length.int())

    _fields_ = [
        (uint2, 'cch'),
        (_grbit, 'grbit'),
        (__crun, 'crun'),
        (__cchExtRst, 'cchExtRst'),
        (__rgb, 'rgb'),
        (lambda self: dyn.array(FormatRun, self['crun'].li.int()), 'rgSTRUN'),
        (lambda self: dyn.block(self['cchExtRst'].li.int()), 'ExtRst'),
    ]

class XLUnicodeStringNoCch(pstruct.type):
    def __crun(self):
        flags = self['grbit'].li
        return uint2 if flags['fRichSt'] else pint.uint_t

    def __cchExtRst(self):
        flags = self['grbit'].li
        return uint4 if flags['fExtSt'] else pint.uint_t

    def __rgb(self):
        flags = self['grbit'].li

        try:
            # If there was a length that was specified, then use that
            if hasattr(self, 'length'):
                length = getattr(self, 'length')

            # Otherwise, we need to calculate it from the blocksize
            else:
                p = self.getparent(RecordGeneralBase)
                cb = p['header'].li.Length()
                length = cb // 2 if flags['fHighByte'] else cb

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            # XXX: unable to calculate length without the blocksize
            length = 0
        return dyn.clone(pstr.wstring if flags['fHighByte'] else pstr.string, length=length)

    _fields_ = [
        (XLUnicodeString._grbit, 'grbit'),
        (__crun, 'crun'),
        (__cchExtRst, 'cchExtRst'),
        (__rgb, 'rgb'),
        (lambda self: dyn.array(FormatRun, self['crun'].li.int()), 'rgSTRUN'),
        (lambda self: dyn.block(self['cchExtRst'].li.int()), 'ExtRst'),
    ]

class ShortXLUnicodeString(pstruct.type):
    def __crun(self):
        flags = self['grbit'].li
        return uint2 if flags['fRichSt'] else pint.uint_t

    def __cchExtRst(self):
        flags = self['grbit'].li
        return uint4 if flags['fExtSt'] else pint.uint_t

    def __rgb(self):
        length, flags = (self[fld].li for fld in ['cch', 'grbit'])
        return dyn.clone(pstr.wstring if flags['fHighByte'] else pstr.string, length=length.int())

    _fields_ = [
        (ubyte1, 'cch'),
        (XLUnicodeString._grbit, 'grbit'),
        (__crun, 'crun'),
        (__cchExtRst, 'cchExtRst'),
        (__rgb, 'rgb'),
        (lambda self: dyn.array(FormatRun, self['crun'].li.int()), 'rgSTRUN'),
        (lambda self: dyn.block(self['cchExtRst'].li.int()), 'ExtRst'),
    ]

# FIXME: http://msdn.microsoft.com/en-us/library/dd924700(v=office.12).aspx
# this type doesn't align with this structure definition
class LPWideString(pstruct.type):
    _fields_ = [
        (uint2, 'cchCharacters'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cchCharacters'].li.int()), 'rgchData'),
    ]
    def summary(self):
        return self['rgchData'].summary()
    def str(self):
        return self['rgchData'].str()

class VirtualPath(XLUnicodeString): pass
class XLNameUnicodeString(XLUnicodeString): pass

@BIFF5.define
@BIFF8.define
class SupBook(pstruct.type):
    type = 430
    type = 0x1ae
    _fields_ = [
        (uint2, 'ctab'),
        (uint2, 'cch'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

#DataValidationCriteria
@BIFF5.define
@BIFF8.define
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
        (lambda self: dyn.array(self.Address, self['number'].li.int()), 'addresses'),
    ]

@BIFF5.define
@BIFF8.define
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
            if self['unicode_flag'].li.int():
                return dyn.clone(pstr.wstring, length=self['length'].li.int())
            return dyn.clone(pstr.string, length=self['length'].li.int())

        _fields_ = [
            (uint2, 'length'),
            (ubyte1, 'unicode_flag'),
            (__unicode, 'string'),
        ]
        def summary(self):
            return "unicode_flag={:#0{:d}x} string={:s}".format(self['unicode_flag'].int(), 2 + 2 * self['unicode_flag'].size(), self['string'].summary())

    class formula(pstruct.type):
        _fields_ = [
            (uint2, 'size'),
            (uint2, 'reserved'),
            (lambda self: dyn.block(self['size'].li.int()), 'data'),
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
class DocType(pint.enum, uint2):
    _values_ = [
        ('workbook', 0x0005),
        ('visualbasic', 0x0006),
        ('worksheet', 0x0010),
        ('charsheet', 0x0020),
        ('macrosheet', 0x0040),
        ('workspace', 0x0100)
    ]

class BOF(pstruct.type):
    def Version(self):
        raise NotImplementedError
    def DocumentType(self):
        raise NotImplementedError

@BIFF5.define
@BIFF8.define
class BOF2(BOF):
    type = 9
    type = 0x0009
    _fields_ = [
        (uint2, 'vers'),
        (DocType, 'dt'),
        (uint2, 'rupBuild'),
        (uint2, 'rupYear'),
    ]
    def Version(self):
        return 2
    def DocumentType(self):
        return self['dt']
    def summary(self):
        if self.size():
            return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for fld in ['vers', 'rupBuild', 'rupYear', 'dt'])
        return '...'

@BIFF5.define
@BIFF8.define
class BOF3(BOF):
    type = 521
    type = 0x0209
    def Version(self):
        return 3

@BIFF5.define
@BIFF8.define
class BOF4(BOF):
    type = 1033
    type = 0x0409
    def Version(self):
        return 4

@BIFF5.define
@BIFF8.define
class BOF5(BOF):
    type = 2057
    type = 0x0809

    class _flags(pbinary.flags):
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

    def __flags(self):
        return undefined if self.Version() < 8 else self._flags

    _fields_ = [
        (uint2, 'vers'),
        (DocType, 'dt'),
        (uint2, 'rupBuild'),
        (uint2, 'rupYear'),
        (__flags, 'flags')
    ]

    def Version(self):
        version, lookup = self['vers'].li, {6:8, 5:7}
        if not hasattr(self, '_biffver'):
            try:
                self._biffver
            except:
                import traceback
                traceback.print_stack()
        return lookup.get(version.int(), self._biffver)

    def DocumentType(self):
        return self['dt']

    def summary(self):
        if self.size():
            return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for fld in ['vers', 'rupBuild', 'rupYear', 'dt', 'flags'])
        return '...'

@BIFF5.define
class BOUNDSHEET(pstruct.type):
    type = 0x85
    type = 133

    class _grbit(pbinary.struct):
        class _hsState(pbinary.enum):
            width, _values_ = 2, [
                ('visible', 0),
                ('hidden', 1),
                ('very-hidden', 2),
            ]
        class _docType(pbinary.enum):
            width, _values_ = 8, [
                ('worksheet', 0x00),
                ('macro', 0x01),
                ('chart', 0x02),
                ('vba-module', 0x06),
            ]
        _fields_ = R([
            (_hsState, 'hsState'),
            (6, 'unused'),
            (_docType, 'dt'),
        ])

    _fields_ = [
        (uint4, 'lbPlyPos'),
        (_grbit, 'grbit'),
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgch'),
    ]

@BIFF8.define
class BoundSheet8(pstruct.type):
    type = 0x85
    type = 133

    _fields_ = [
        (uint4, 'lbPlyPos'),
        (BOUNDSHEET._grbit, 'grbit'),
        (ShortXLUnicodeString, 'stName'),
    ]

@BIFF5.define
class LABEL(pstruct.type):
    type = 0x0204
    type = 516
    _fields_ = [
        (Rw, 'rw'),
        (Col, 'col'),
        (uint2, 'ixfe'),
        (uint2, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgb'),
    ]
    def summary(self):
        return "rw={:d} col={:d} ixfe={:d} rgb={:s}".format(self['rw'].int(), self['col'].int(), self['ixfe'].int(), self['rgb'].summary())

###
@BIFF5.define
@BIFF8.define
class Font(pstruct.type):
    type = 0x0031
    type = 49
    class _fontName(pstruct.type):
        _fields_ = [
            (ubyte1, 'cch'),
            (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgcch'),
        ]
        def summary(self):
            return self['rgcch'].summary()
        def str(self):
            return self['rgcch'].str()

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
        (_fontName, 'fontName'),
    ]

@BIFF5.define
@BIFF8.define
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

class BookExt_Conditional11(pbinary.flags):
    _fields_ = R([
        (1, 'fBuggedUserAboutSolution'),
        (1, 'fShowInkAnnotation'),
        (6, 'unused'),
    ])

class BookExt_Conditional12(pbinary.flags):
    _fields_ = R([
        (1, 'reserved'),
        (1, 'fPublishedBookItems'),
        (1, 'fShowPivotChartFilter'),
        (5, 'reserved2'),
    ])

@BIFF5.define
@BIFF8.define
class ExtString(pstruct.type):
    type = 2052
    type = 0x804

    _fields_ = [
        (uint2, 'rt'),
        (FrtFlags, 'grbitFrt'),
        (XLUnicodeString, 'rgb'),
    ]

@BIFF5.define
@BIFF8.define
class INDEX(pstruct.type):
    type = 523
    type = 0x20b

    _fields_ = [
        (uint4, 'reserved'),
        (uint4, 'rwMic'),          # FIXME: version 7 and earlier sets these at uint4
        (uint4, 'rwMac'),
        (uint4, 'reserved2'),
        (dyn.array(uint4, 0), 'rgibRw'),    # FIXME
    ]

@BIFF5.define
@BIFF8.define
class BookExt(pstruct.type):
    type = 2147
    type = 0x863
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fDontAutoRecover'),
            (1, 'fHidePivotList'),
            (1, 'fFilterPrivacy'),
            (1, 'fEmbedFactoids'),
            (2, 'mdFactoidDisplay'),
            (1, 'fSavedDuringRecovery'),
            (1, 'fCreatedViaMinimalSave'),
            (1, 'fOpenedViaDataRecovery'),
            (1, 'fOpenedViaSafeLoad'),
            (22, 'reserved'),
        ])

    def __unknown(self):
        cb = self['cb'].li.int()
        total = 12 + 4 + 4 + 1 + 1
        return dyn.block(cb - total)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'cb'),
        (_flags, 'flags'),
        (BookExt_Conditional11, 'grbit1'),
        (BookExt_Conditional12, 'grbit2'),
        (__unknown, 'unknown'),
    ]

@BIFF5.define
@BIFF8.define
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

@BIFF5.define
@BIFF8.define
class CalcPrecision(Boolean, uint2):
    type = 0xe
    type = 14

@BIFF5.define
@BIFF8.define
class Date1904(pint.enum,uint2):
    type = 0x22
    type = 34
    _values_ = [
        ('datesystem(1900)', 0),
        ('datesystem(1904)', 1),
    ]

class HideObjEnum(pint.enum):
    _values_ = [
        ('SHOWALL',         0),
        ('SHOWPLACEHOLDER', 1),
        ('HIDEALL',         2),
    ]

@BIFF5.define
@BIFF8.define
class HideObj(HideObjEnum, uint2):
    type = 0x8d
    type = 141

@BIFF5.define
@BIFF8.define
class Backup(Boolean, uint2):
    type = 0x40
    type = 64

@BIFF5.define
@BIFF8.define
class CompressPictures(pstruct.type):
    type = 0x89b
    type = 2203
    class _fAutoCompressPicture(Boolean, uint4): pass

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (_fAutoCompressPicture, 'fAutoCompressPicture'),
    ]

class TabIndex(uint2): pass

@BIFF5.define
@BIFF8.define
class Password(uint2):
    type = 0x13
    type = 19

@BIFF5.define
@BIFF8.define
class PROTECT(Boolean, uint2):
    type = 0x12
    type = 18

@BIFF5.define
@BIFF8.define
class WinProtect(Boolean, uint2):
    type = 0x19
    type = 25

@BIFF5.define
@BIFF8.define
class UsesELFs(Boolean, uint2):
    type = 0x1ae
    type = 352

@BIFF5.define
class WRITEACCESS(pstruct.type):
    type = 0x5c
    type = 92
    def __stName(self):
        res = self['cch'].li
        return dyn.clone(pstr.string, length=res.int())

    def __padding(self):
        res = self['cch'].li
        return dyn.clone(pstr.string, length=max(0, 31 - res.int()))

    _fields_ = [
        (ubyte1, 'cch'),
        (__stName, 'stName'),
        (__padding, 'pad(stName)'),
    ]
    def summary(self):
        return "(pad={:+#x}) stName={:s}".format(self['pad(stName)'].size(), self['stName'].summary())

@BIFF8.define
class WriteAccess8(pstruct.type):
    type = 0x5c
    type = 92

    def __padding(self):
        fields = ['cch', 'stName']
        return dyn.clone(pstr.string, length=max(0, 112 - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'stName'),
        (__padding, 'pad(stName)'),
    ]
    def summary(self):
        return "(pad={:+#x}) stName={:s}".format(self['pad(stName)'].size(), self['stName'].summary())

@BIFF5.define
@BIFF8.define
class InterfaceHdr(pstruct.type):
    type = 0xe1
    type = 225
    _fields_ = [
        (uint2, 'Cv'),
    ]

@BIFF5.define
@BIFF8.define
class InterfaceEnd(undefined):
    type = 0xe2
    type = 226

@BIFF5.define
@BIFF8.define
class Mms(pstruct.type):
    type = 0xc1
    type = 193
    _fields_ = [
        (ubyte1, 'reserved1'),
        (ubyte1, 'reserved2'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class CodePage(uint2):
    type = 0x42
    type = 66

@BIFF5.define
@BIFF8.define
class Excel9File(undefined):
    type = 0x1c0
    type = 448

@BIFF5.define
@BIFF8.define
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

@BIFF5.define
@BIFF8.define
class Country(pstruct.type):
    type = 0x8c
    type = 140
    class _iCountryWinIni(pint.enum, uint2):
        _values_ = [
            ('United States', 1),
            ('Canada', 2),
            ('Latin America', 3),
            ('Russia', 7),
            ('Egypt', 20),
            ('Greece', 30),
            ('Netherlands', 31),
            ('Belgium', 32),
            ('France', 33),
            ('Spain', 34),
            ('Hungary', 36),
            ('Italy', 39),
            ('Switzerland', 41),
            ('Austria', 43),
            ('United Kingdom', 44),
            ('Denmark', 45),
            ('Sweden', 46),
            ('Norway', 47),
            ('Poland', 48),
            ('Germany', 49),
            ('Mexico', 52),
            ('Brazil', 55),
            ('Australia', 61),
            ('New Zealand', 64),
            ('Thailand', 66),
            ('Japan', 81),
            ('Korea', 82),
            ('Viet Nam', 84),
            ('People\'s Republic of China', 86),
            ('Turkey', 90),
            ('Algeria', 213),
            ('Morocco', 216),
            ('Libya', 218),
            ('Portugal', 351),
            ('Iceland', 354),
            ('Finland', 358),
            ('Czech Republic', 420),
            ('Taiwan', 886),
            ('Lebanon', 961),
            ('Jordan', 962),
            ('Syria', 963),
            ('Iraq', 964),
            ('Kuwait', 965),
            ('Saudi Arabia', 966),
            ('United Arab Emirates', 971),
            ('Israel', 972),
            ('Qatar', 974),
            ('Iran', 981),
        ]

    _fields_ = [
        (uint2, 'iCountryDef'),
        (_iCountryWinIni, 'iCountryWinIni'),
    ]

@BIFF5.define
@BIFF8.define
class ObProj(undefined):
    '''
    The existence of the ObProj record specifies that there is a VBA
    project in the file.

    This project is located in the VBA storage stream.
    '''

    type = 0xd3
    type = 211

@BIFF5.define
@BIFF8.define
class CodeName(XLUnicodeString):
    '''
    The CodeName record specifies the name of a workbook object, a sheet
    object in the VBA project located in this file.
    '''

    type = 0x1ba
    type = 442

@BIFF5.define
@BIFF8.define
class RecalcId(pstruct.type):
    type = 449
    type = 0x1c1
    _fields_ = [
        (uint2, 'rt'),
        (uint2, 'reserved'),
        (uint4, 'dwBuild'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class BuiltInFnGroupCount(uint2):
    type = 156
    type = 0x9c

@BIFF5.define
@BIFF8.define
class Prot4Rev(Boolean, uint2):
    type = 431
    type = 0x1af

@BIFF5.define
@BIFF8.define
class Prot4RevPass(uint2):
    type = 444
    type = 0x1bc

@BIFF5.define
@BIFF8.define
class DSF(uint2):
    type = 353
    type = 0x161

@BIFF5.define
@BIFF8.define
class MsoDrawingGroup(art.OfficeArtDggContainer):
    type = 0xeb
    type = 235
    def blocksize(self):
        try:
            rec = self.getparent(RecordGeneralBase)
        except ptypes.error.ItemNotFoundError:
            return 0
        return rec['header'].li.Length()

@BIFF5.define
@BIFF8.define
class HFPicture(pstruct.type):
    type = 2150
    type = 0x866
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fIsDrawing'),
            (1, 'fIsDrawingGroup'),
            (1, 'fContinue'),
            (5, 'unused'),
        ])
    def __rgDrawing(self):
        res = self['flags'].li
        fd, fg = res['fIsDrawing'], res['fIsDrawingGroup']

        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.clone(art.RecordContainer, blocksize=lambda _, size=max(0, cb - res): size)

        res = self['FrtHeader'].li.size() + self['flags'].li.size() + self['reserved'].li.size()
        if fd and not fg:
            return dyn.clone(art.OfficeArtDgContainer, blocksize=lambda _, size=max(0, cb - res): size)
        elif not fd and fg:
            return dyn.clone(art.OfficeArtDggContainer, blocksize=lambda _, size=max(0, cb - res): size)
        elif not fd and not fg:
            return undefined
        logging.warn('{:s}.__rgDrawing : Mutually exclusive fIsDrawing and fIsDrawing is set. Using a generic RecordContainer.'.format(self.classname()))
        return dyn.clone(art.RecordContainer, blocksize=lambda _, size=cb - res: size)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (_flags, 'flags'),
        (ubyte1, 'reserved'),
        (__rgDrawing, 'rgDrawing'),
    ]

@BIFF5.define
@BIFF8.define
class MsoDrawing(art.OfficeArtDgContainer):
    type = 0xec
    type = 236

    def blocksize(self):
        try:
            rec = self.getparent(RecordGeneralBase)
        except ptypes.error.ItemNotFoundError:
            return 0
        return rec['header'].li.Length()

@BIFF5.define
@BIFF8.define
class EOF(undefined):
    type = 10
    type = 0xa


@BIFF5.define
@BIFF8.define
class Lbl(pstruct.type):
    type = 24
    type = 0x18

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fHidden'),
            (1, 'fFunc'),
            (1, 'fOB'),
            (1, 'fProc'),
            (1, 'fCalcExp'),
            (1, 'fBuiltin'),
            (6, 'fGrp'),
            (1, 'reserved1'),
            (1, 'fPublished'),
            (1, 'fWorkbookParam'),
            (1, 'reserved2'),
        ])

    def __Name(self):
        res = self['cch'].li.int()
        return dyn.clone(XLUnicodeStringNoCch, length=res)

    def __rgce(self):
        cb = self['cce'].li.int()
        #res = NameParsedFormula    # FIXME
        res = ptype.block
        return dyn.clone(res, blocksize=lambda _, size=cb: size)

    def __NameIndex(self):
        res = self['flags'].li
        return ubyte1 if res.o['fBuiltin'] else pint.uint_t

    _fields_ = [
        (_flags, 'flags'),
        (ubyte1, 'chKey'),
        (ubyte1, 'cch'),
        (ubyte1, 'cce'),
        (uint2, 'reserved3'),
        (uint2, 'itab'),
        (ubyte1, 'reserved4'),
        (ubyte1, 'reserved5'),
        (ubyte1, 'reserved6'),
        (ubyte1, 'reserved7'),
        (__NameIndex, 'NameIndex'),
        (__Name, 'Name'),
        (__rgce, 'rgce'),
    ]

@BIFF5.define
@BIFF8.define
class Theme(pstruct.type):
    type = 2198
    type = 0x896
    def __rgb(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            # XXX: unable to calculate length without the blocksize
            return undefined

        total = sum(self[fld].li.size() for fld in ['frtHeader', 'dwThemeVersion'])
        return dyn.block(max(0, cb - total))

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'dwThemeVersion'),
        (__rgb, 'rgb'),
    ]

@BIFF5.define
@BIFF8.define
class Blank(Cell):
    type = 513
    type = 0x201

@BIFF5.define
@BIFF8.define
class ForceFullCalculation(pstruct.type):
    type = 0x8a3
    type = 2211
    class _fNoDeps(Boolean, uint4): pass
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (_fNoDeps, 'fNoDeps'),
    ]

@BIFF5.define
class EXTERNSHEET(pstruct.type):
    type = 0x17
    type = 23

    def __rgch(self):
        length = self['cch'].li.int()
        return dyn.clone(pstr.string, length=length)

    _fields_ = [
        (ubyte1, 'cch'),
        (__rgch, 'rgch'),
    ]
    def summary(self):
        return self['rgch'].summary()
    def str(self):
        return self['rgch'].str()

class XTI(pstruct.type):
    _fields_ = [
        (uint2, 'iSupBook'),
        (sint2, 'iTabFirst'),
        (sint2, 'iTabLast'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF8.define
class ExternSheet(pstruct.type):
    type = 0x17
    type = 23

    _fields_ = [
        (uint2, 'cXTI'),
        (lambda self: dyn.array(XTI, self['cXTI'].li.int()), 'rgXTI'),
    ]

@BIFF5.define
class EXTERNNAME(pstruct.type):
    type = 0x23
    type = 35
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fBuiltIn'),
            (1, 'fWantAdvise'),
            (1, 'fWantPict'),
            (1, 'fOle'),
            (1, 'fOleLink'),
            (10, 'cf'),
            (1, 'fIcon'),
        ])
    def __body(self):
        res = self['flags'].li
        f1, f2 = res['fOle'], res['fOleLink']
        #lookup = {
        #    #(0, 0) : ExternOleDdeLink,
        #    (0, 0) : ExternDocName,
        #    (0, 1) : undefined,   # ???
        #    (1, 0) : ExternDdeLinkNoOper,
        #}
        # FIXME: this is pretty poorly documented
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)

        return dyn.block(cb - self['flags'].li.size())

    _fields_ = [
        (_flags, 'flags'),
        (uint4, 'reserved'),
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgch'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for fld in ['reserved', 'rgch', 'flags'])

@BIFF8.define
class ExternName(pstruct.type):
    type = 0x23
    type = 35
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fBuiltIn'),
            (1, 'fWantAdvise'),
            (1, 'fWantPict'),
            (1, 'fOle'),
            (1, 'fOleLink'),
            (10, 'cf'),
            (1, 'fIcon'),
        ])
    def __body(self):
        res = self['flags'].li
        f1, f2 = res['fOle'], res['fOleLink']
        #lookup = {
        #    #(0, 0) : ExternOleDdeLink,
        #    (0, 0) : ExternDocName,
        #    (0, 1) : undefined,   # ???
        #    (1, 0) : ExternDdeLinkNoOper,
        #}
        # FIXME: this is pretty poorly documented
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)

        return dyn.block(cb - self['flags'].li.size())

    _fields_ = [
        (_flags, 'flags'),
        (__body, 'body'),
    ]

@BIFF5.define
@BIFF8.define
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
class XFProperty(ptype.definition):
    attribute, cache = 'propertyType', {}

    class XFUnknown(ptype.block):
        def classname(self):
            res = getattr(self, XFProperty.attribute, None)
            return "{:s}<{:s}>".format(self.typename(), '????' if res is None else "{:04x}".format(res))
    default = XFUnknown

# FIXME: implement some XFProperty types

class XFProp(pstruct.type):
    def __xfPropDataBlob(self):
        t, cb = self['xfPropType'].li.int(), self['cb'].li.int()
        length = cb - (2+2)
        res = XFProperty.withdefault(t, propertyType=t, length=length)
        return dyn.clone(res, blocksize=lambda _, cb=length: cb)

    _fields_ = [
        (uint2, 'xfPropType'),      # XXX: make this a pint.enum
        (uint2, 'cb'),
        (__xfPropDataBlob, 'xfPropDataBlob'),
    ]

class XFProps(pstruct.type):
    _fields_ = [
        (uint2, 'reserved'),
        (uint2, 'cprops'),
        (lambda self: dyn.array(XFProp, self['cprops'].li.int()), 'xfPropArray'),
    ]

###
if True:
    class SerArType(ptype.definition):
        attribute, cache = 'serType', {}

        class SerUnknown(ptype.block):
            def classname(self):
                res = getattr(self, SerArType.attribute, None)
                return self.typename() if res is None else "{:s}<{:x}>".format(self.typename(), res)
        default = SerUnknown

    class SerAr(pstruct.type):
        def __Ser(self):
            res = self['reserved1'].li.int()
            return SerArType.withdefault(res, serType=res)
        _fields_ = [
            (uint4,'reserved1'),        # XXX: make this a pint.enum
            (__Ser, 'Ser'),
        ]

    @SerArType.define
    class SerBool(pstruct.type):
        serType = 0x04
        serType = 4
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
        serType = 0x10
        serType = 16
        _fields_ = [
            (BErr, 'err'),
            (ubyte1,'reserved2'),
            (uint2,'unused1'),
            (uint4,'unused2'),
        ]

    @SerArType.define
    class SerNil(pstruct.type):
        serType = 0x0
        serType = 0
        _fields_ = [
            (uint4,'unused1'),
            (uint4,'unused2'),
        ]
        def summary(self):
            return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

    @SerArType.define
    class SerNum(pstruct.type):
        serType = 0x1
        serType = 1
        _fields_ = [
            (Xnum,'xnum'),
        ]
        def summary(self):
            return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

    @SerArType.define
    class SerStr(pstruct.type):
        serType = 0x2
        serType = 2
        _fields_ = [
            (XLUnicodeString,'string'),
        ]
        def summary(self):
            return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@BIFF5.define
@BIFF8.define
class CRN(pstruct.type):
    type = 90
    type = 0x5a

    _fields_ = [
        (ColByteU, 'colLast'),
        (ColByteU, 'colFirst'),
        (RwU, 'colLast'),
        (lambda self: dyn.array(SerAr, self['colLast'].li.int() - self['colFirst'].li.int() + 1), 'crnOper'),
    ]

class CellXF7(pbinary.flags):
    _fields_ = R([
        (3, 'alc'),
        (1, 'fWrap'),
        (3, 'alcV'),
        (1, 'fJustLast'),

        (2, 'ori'),
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

class CellXF8(pbinary.flags):
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

class StyleXF7(pbinary.flags):
    _fields_ = R([
        (1, 'fAtrNum'),
        (1, 'fAtrFnt'),
        (1, 'fAtrAlc'),
        (1, 'fAtrBdr'),
        (1, 'fAtrPat'),
        (1, 'fAtrProt'),
        (1, 'fsxButton'),
    ])

class StyleXF8(pbinary.flags):
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

@BIFF5.define
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
        (dyn.array(uint2, 5), 'style'),
    ]

@BIFF8.define
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
        (lambda self: CellXF8 if self['flags'].li['fStyle'] == 0 else StyleXF8, 'data'),
    ]

@BIFF5.define
@BIFF8.define
class MulRk(pstruct.type):
    type = 0xbd
    type = 189
    def __rgrkrec(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            # XXX: unable to calculate number of elements without the blocksize
            return dyn.array(RkRec, 0)

        res = sum(self[fld].li.size() for fld in ['rw', 'colFirst', 'colFirst'])
        return dyn.blockarray(RkRec, max(0, cb - res))

    _fields_ = [
        (Rw, 'rw'),
        (Col, 'colFirst'),
        (__rgrkrec, 'rgrkrec'),
        (Col, 'colLast'),
    ]

class CellParsedFormula(pstruct.type):
    def __rgce(self):
        cb = self['cce'].li.int()
        return dyn.clone(Rgce, blocksize=lambda _, size=cb: size)

    def __rgcb(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)

        sz = self['cce'].li.size() + self['cce'].int()
        return dyn.block(bs - sz)
#        return RgbExtra        # FIXME

    _fields_ = [
        (uint2, 'cce'),
        (__rgce, 'rgce'),     # XXX: page 756. must not contain
        (__rgcb, 'rgcb'),
    ]

class Ptg(ptype.definition):
    attribute, cache = 'parseType', {}

    class PtgUnknown(ptype.block):
        def classname(self):
            res = getattr(self, Ptg.attribute, None)
            if res is None:
                return self.typename()
            first, second = res
            return "{:s}<{:s},{:s}>".format(self.typename(), '*' if first is None else "{:x}".format(first), '*' if second is None else "{:x}".format(second))
    default = PtgUnknown

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
        return ubyte1 if res['ptg'] in {0x18, 0x19} else 0

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
    parseType = 0x01, None
    _fields_ = [
        (Rw, 'row'),
        (Col, 'col'),
    ]

@Ptg.define
class PtgTbl(pstruct.type):
    parseType = 0x02, None
    _fields_ = [
        (Rw, 'row'),
        (Col, 'col'),
    ]

@Ptg.define
class PtgAdd(undefined): parseType = 0x03, None
@Ptg.define
class PtgSub(undefined): parseType = 0x04, None
@Ptg.define
class PtgMul(undefined): parseType = 0x05, None
@Ptg.define
class PtgDiv(undefined): parseType = 0x06, None
@Ptg.define
class PtgPower(undefined): parseType = 0x07, None
@Ptg.define
class PtgConcat(undefined): parseType = 0x08, None
@Ptg.define
class PtgLt(undefined): parseType = 0x09, None
@Ptg.define
class PtgLe(undefined): parseType = 0x0a, None
@Ptg.define
class PtgEq(undefined): parseType = 0x0b, None
@Ptg.define
class PtgGe(undefined): parseType = 0x0c, None
@Ptg.define
class PtgGt(undefined): parseType = 0x0d, None
@Ptg.define
class PtgNe(undefined): parseType = 0x0e, None
@Ptg.define
class PtgIsect(undefined): parseType = 0x0f, None
@Ptg.define
class PtgUnion(undefined): parseType = 0x10, None
@Ptg.define
class PtgRange(undefined): parseType = 0x11, None
@Ptg.define
class PtgUplus(undefined): parseType = 0x12, None
@Ptg.define
class PtgUminus(undefined): parseType = 0x13, None
@Ptg.define
class PtgPercent(undefined): parseType = 0x14, None
@Ptg.define
class PtgParen(undefined): parseType = 0x15, None
@Ptg.define
class PtgMissArg(undefined): parseType = 0x16, None
@Ptg.define
class PtgStr(ShortXLUnicodeString): parseType = 0x17, None
@Ptg.define
class PtgElfLel(Ilel): parseType = 0x18, 0x01
@Ptg.define
class PtgElfRw(RgceElfLoc): parseType = 0x18, 0x02
@Ptg.define
class PtgElfCol(RgceElfLoc): parseType = 0x18, 0x03
@Ptg.define
class PtgElfRwV(RgceElfLoc): parseType = 0x18, 0x06
@Ptg.define
class PtgElfColV(RgceElfLoc): parseType = 0x18, 0x07
@Ptg.define
class PtgElfRadical(RgceElfLoc): parseType = 0x18, 0x0a
@Ptg.define
class PtgElfRadicalS(uint4): parseType = 0x18, 0x0b
@Ptg.define
class PtgElfColS(uint4): parseType = 0x18, 0x0d
@Ptg.define
class PtgElfColSV(uint4): parseType = 0x18, 0x0f
@Ptg.define
class PtgElfRadicalLel(Ilel): parseType = 0x18, 0x10
@Ptg.define
class PtgSxName(uint4): parseType = 0x18, 0x1d
@Ptg.define
class PtgAttrSemi(uint2): parseType = 0x19, 0x01

@Ptg.define
class PtgAttrIf(uint2): parseType = 0x19, 0x02
@Ptg.define
class PtgAttrChoose(pstruct.type):
    parseType = 0x19, 0x04
    _fields_ = [
        (uint2, 'cOffset'),
        (lambda self: dyn.array(uint2, 1 + self['cOffset'].int()), 'rgOffset'),
    ]
@Ptg.define
class PtgAttrGoto(uint2): parseType = 0x19, 0x08
@Ptg.define
class PtgAttrSum(uint2): parseType = 0x19, 0x10
@Ptg.define
class PtgAttrBaxcel(uint2): parseType = 0x19, 0x20

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
class PtgAttrSpace(PtgAttrSpaceType): parseType = 0x19, 0x40
@Ptg.define
class PtgAttrSpaceSemi(PtgAttrSpaceType): parseType = 0x19, 0x41
@Ptg.define
class PtgErr(BErr): parseType = 0x1c, None
@Ptg.define
class PtgBool(Boolean, ubyte1): parseType = 0x1d, None
@Ptg.define
class PtgInt(uint2): parseType = 0x1e, None
@Ptg.define
class PtgNum(Xnum): parseType = 0x1f, None

@Ptg.define
class PtgArray(pstruct.type):
    parseType = 0x20, None
    _fields_ = [
        (ubyte1, 'unused1'),
        (uint2, 'unused2'),
        (uint4, 'unused3'),
    ]

@Ptg.define
class PtgFunc(Ftab):
    parseType = 0x21, None

@Ptg.define
class PtgFuncVar(pstruct.type):
    parseType = 0x22, None
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
class PtgName(uint4): parseType = 0x23, None
@Ptg.define
class PtgRef(RgceLocRel): parseType = 0x24, None
@Ptg.define
class PtgArea(RgceArea): parseType = 0x25, None

@Ptg.define
class PtgMemArea(pstruct.type):
    parseType = 0x26, None
    _fields_ = [
        (uint4, 'unused'),
        (uint2, 'cce'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@Ptg.define
class PtgMemErr(pstruct.type):
    parseType = 0x27, None
    _fieldS_ = [
        (BErr, 'err'),
        (ubyte1, 'unused1'),
        (uint2, 'unused2'),
        (uint2, 'cce'),
    ]

@Ptg.define
class PtgMemNoMem(pstruct.type):
    parseType = 0x28, None
    _fields_ = [
        (uint4, 'unused'),
        (uint2, 'cce'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@Ptg.define
class PtgMemFunc(uint2): parseType = 0x29, None

@Ptg.define
class PtgRefErr(pstruct.type):
    parseType = 0x2a, None
    _fields_ = [
        (uint2, 'unused1'),
        (uint2, 'unused2'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@Ptg.define
class PtgAreaErr(pstruct.type):
    parseType = 0x2b, None
    _fields_ = [
        (uint2, 'unused1'),
        (uint2, 'unused2'),
        (uint2, 'unused3'),
        (uint2, 'unused4'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@Ptg.define
class PtgRefN(RgceLocRel): parseType = 0x2c, None
@Ptg.define
class PtgAreaN(RgceAreaRel): parseType = 0x2d, None

@Ptg.define
class PtgNameX(pstruct.type):
    parseType = 0x39, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'nameindex'),
    ]
    def summary(self):
        return ' '.join("{:s}={:s}".format(fld, self[fld].summary()) for _, fld in self._fields_)

@Ptg.define
class PtgRef3d(pstruct.type):
    parseType = 0x3a, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (RgceLoc, 'nameindex'),
    ]

@Ptg.define
class PtgArea3d(pstruct.type):
    parseType = 0x3b, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (RgceArea, 'area'), # FIXME: or RgceAreaRel
    ]

@Ptg.define
class PtgRefErr3d(pstruct.type):
    parseType = 0x3c, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'unused1'),
        (uint4, 'unused2'),
    ]

@Ptg.define
class PtgAreaErr3d(pstruct.type):
    parseType = 0x3d, None
    _fields_ = [
        (XtiIndex, 'ixti'),
        (uint4, 'unused1'),
        (uint4, 'unused2'),
        (uint4, 'unused3'),
        (uint4, 'unused4'),
    ]

class Rgce(parray.block):
    _object_ = PtgGeneral

class CFGradientInterpItem(pstruct.type):
    _fields_ = [
        (CFVO, 'cfvoInterp'),
        (Xnum, 'numDomain'),
    ]

class CFGradientItem(pstruct.type):
    _fields_ = [
        (Xnum, 'numGrange'),
        (CFColor, 'color'),
    ]

class CFGradient(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'fClamp'),
            (1, 'fBackground'),
            (6, 'reserved2'),
        ]
    _fields_ = [
        (uint2, 'unused'),
        (ubyte1, 'reserved1'),
        (ubyte1, 'cInterpCurve'),
        (ubyte1, 'cGradientCurve'),
        (_flags, 'flags'),
        (lambda self: dyn.array(CFGradientInterpItem, self['cInterpCurve'].li.int()), 'rgInterp'),
        (lambda self: dyn.array(CFGradientItem, self['cGradientCurve'].li.int()), 'rgCurve'),
    ]

class CFDatabar(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fRightToLeft'),
            (1, 'fShowValue'),
            (6, 'reserved2'),
        ])
    _fields_ = [
        (uint2, 'unused'),
        (ubyte1, 'reserved1'),
        (_flags, 'flags'),
        (ubyte1, 'iPercentMin'),
        (ubyte1, 'iPercentMax'),
        (CFColor, 'color'),
        (CFVO, 'cfvoDB1'),
        (CFVO, 'cfvoDB2'),
    ]

class CFFilter(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'fTop'),
            (1, 'fPercent'),
            (6, 'reserved2'),
        ]
    _fields_ = [
        (uint2, 'cbFilter'),
        (ubyte1, 'reserved1'),
        (_flags, 'flags'),
        (uint2, 'iParam'),
    ]

class CFMultistate(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'fIconOnly'),
            (1, 'reserved2'),
            (1, 'fReverse'),
            (5, 'reserved3'),
        ]
    _fields_ = [
        (uint2, 'unused'),
        (ubyte1, 'reserved1'),
        (ubyte1, 'cStates'),
        (ubyte1, 'iIconSet'),
        (_flags, 'flags'),
        (lambda self: dyn.array(CFMStateItem, self['cStates'].li.int()), 'rgStates'),
    ]

class CFParsedFormula(pstruct.type):
    def __rgce(self):
        cce = self['cce'].li.int()
        # FIXME
        return dyn.clone(Rgce, blocksize=lambda _, size=cce: size)

    _fields_ = [
        (uint2, 'cce'),
        (__rgce, 'rgce'),
    ]

class CFParsedFormulaNoCCE(Rgce): pass

if False:
    class RgbExtra(parray.infinite):
        def _object_(self):
            p = self.parent['rgce']
            for x in p:
                if x.hasattr('extra'):
                    yield x.extra
                continue
            return

class Icv(uint2): '''A color in the color table.'''
class IcvXF(uint2): '''A color in the color table for cell and style formatting properties.'''

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

@BIFF5.define
class FORMULA(pstruct.type):
    type = 0x6
    type = 6
    _fields_ = [
        (Rw, 'rw'),
        (Col, 'col'),
        (uint2, 'ixfe'),
        (Xnum, 'num'),
        (uint2, 'grbit'),
        (uint4, 'chn'),
        (uint2, 'cce'),
        #(lambda self: dyn.block(self['cce'].li.int()), 'rgce'),
    ]

@BIFF8.define
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

@BIFF5.define
@BIFF8.define
class XCT(pstruct.type):
    type = 89
    type = 0x59
    _fields_ = [
        (sint2, 'ccrn'),
        (uint2, 'itab'),
    ]

class BuiltInStyle(pstruct.type):
    _fields_ = [
        (ubyte1, 'istyBuiltIn'),    # FIXME: this can be a pint.enum
        (ubyte1, 'iLevel'),
    ]
    def summary(self):
        return "iLevel={:d} istyBuiltIn={:#04x}".format(self['iLevel'].int(), self['istyBuiltIn'].int())

class UserDefinedStyle(pstruct.type):
    _fields_ = [
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgch'),
    ]
    def summary(self):
        return self['rgch'].summary()
    def str(self):
        return self['rgch'].str()

@BIFF5.define
@BIFF8.define
class TableStyles(pstruct.type):
    type = 2190
    type = 0x88e
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint4, 'cts'),
        (uint2, 'cchDefTableStyle'),
        (uint2, 'cchDefPivotStyle'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cchDefTableStyle'].li.int()), 'rgchDefTableStyle'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cchDefPivotStyle'].li.int()), 'rgchDefPivotStyle'),
    ]

@BIFF5.define
class STYLE(pstruct.type):
    type = 659
    type = 0x293

    class _ixfe(pbinary.flags):
        _fields_ = R([
            (12, 'ixfe'),
            (3, 'unused'),
            (1, 'fBuiltIn'),
        ])

    _fields_ = [
        (_ixfe, 'ixfe'),
        (lambda self: BuiltInStyle if self['ixfe'].li['fBuiltIn'] else UserDefinedStyle, 'styleData'),
    ]

    def summary(self):
        flags, res = self['ixfe'], self['styleData']
        if flags['fBuiltIn']:
            return "styleData.iLevel={:d} styleData.istyBuiltIn={:#0{:d}x} ixfe={!s}".format(res['iLevel'].int(), res['istyBuiltIn'].int(), 2 + 2 * res['istyBuiltIn'].size(), flags.summary())
        return "styleData={!r} ixfe={!s}".format(res.str(), flags.summary())

@BIFF8.define
class Style(pstruct.type):
    type = 659
    type = 0x293

    class _ixfe(pbinary.flags):
        _fields_ = R([
            (12, 'ixfe'),
            (3, 'unused'),
            (1, 'fBuiltIn'),
        ])

    _fields_ = [
        (_ixfe, 'ixfe'),
        (lambda self: BuiltInStyle if self['ixfe'].li['fBuiltIn'] else undefined, 'builtInData'),
        (lambda self: XLUnicodeString if not self['ixfe'].li['fBuiltIn'] else undefined, 'user')
    ]

@BIFF5.define
@BIFF8.define
class StyleExt(pstruct.type):
    type = 2194
    type = 0x892
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fBuiltIn'),
            (1, 'fHidden'),
            (1, 'fCustom'),
            (5, 'reserved'),
        ])
    class _iCategory(pint.enum, ubyte1):
        _values_ = [
            ('custom', 0x00),
            ('good-bad-neutral', 0x00),
            ('data-model', 0x00),
            ('title-heading', 0x00),
            ('themed', 0x00),
            ('number-format', 0x00),
        ]
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (_flags, 'flags'),
        (_iCategory, 'iCategory'),
        (BuiltInStyle,'builtInData'),
        (LPWideString, 'stName'),
        (XFProps, 'xfProps'),
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
        (lambda self: dyn.array(GradStop, self['cGradStops'].li.int()), 'rgGradStops'),
    ]

class ExtPropType(ptype.definition):
    attribute, cache = 'extType', {}

    class ET_Unknown(ptype.block):
        def classname(self):
            res = getattr(self, ExtPropType.attribute, None)
            return self.typename() if res is None else "{:s}<{:04x}>".format(self.typename(), res)
    default = ET_Unknown

@ExtPropType.define
class ET_Foreground_Color(FullColorExt):
    extType = 0x0004
@ExtPropType.define
class ET_Background_Color(FullColorExt):
    extType = 0x0005
@ExtPropType.define
class ET_GradientFill(XFExtGradient):
    extType = 0x0006
@ExtPropType.define
class ET_TopBorderColor(FullColorExt):
    extType = 0x0007
@ExtPropType.define
class ET_BottomBorderColor(FullColorExt):
    extType = 0x0008
@ExtPropType.define
class ET_LeftBorderColor(FullColorExt):
    extType = 0x0009
@ExtPropType.define
class ET_RightBorderColor(FullColorExt):
    extType = 0x000a
@ExtPropType.define
class ET_DiagonalBorderColor(FullColorExt):
    extType = 0x000b
@ExtPropType.define
class ET_TextColor(FullColorExt):
    extType = 0x000d
@ExtPropType.define
class ET_FontScheme(FontScheme):
    extType = 0x000e
@ExtPropType.define
class ET_TextIndentation(uint2):
    extType = 0x000f

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
        # FIXME
        return ExtPropType.get(res, blocksize=lambda _, size=cb: size)

    _fields_ = [
        (_extType, 'extType'),
        (uint2, 'cb'),
        (__extPropData, 'extPropData'),
    ]

@BIFF5.define
@BIFF8.define
class XFCFC(pstruct.type):
    type = 0x87c
    type = 2172
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint2, 'reserved'),
        (uint2, 'cxfs'),
        (uint4, 'crc'),
    ]

@BIFF5.define
@BIFF8.define
class XFExt(pstruct.type):
    type = 0x87d
    type = 2173
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint2, 'reserved1'),
        (XFIndex, 'ixfe'),
        (uint2, 'reserved2'),
        (uint2, 'cexts'),
        (lambda self: dyn.array(ExtProp, self['cexts'].li.int()), 'rgExt'),
    ]

@BIFF5.define
class Format(pstruct.type):
    type = 0x41e
    type = 1054
    def __stFormat(self):
        res = self['cch'].li
        return dyn.clone(pstr.string, length=res.int())
    _fields_ = [
        (uint2, 'ifmt'),
        (ubyte1, 'cch'),
        (__stFormat, 'stFormat'),
    ]
    def summary(self):
        return "ifmt={:#0{:d}x} stFormat={:s}".format(self['ifmt'].int(), 2 + 2 * self['ifmt'].size(), self['stFormat'].summary())

@BIFF8.define
class Format(pstruct.type):
    type = 0x41e
    type = 1054
    def __stFormat(self):
        p = self.getparent(type=RecordGeneralBase)
        length = p['header']['length'].int() - 2
        return dyn.block(length)
    _fields_ = [
        (uint2, 'ifmt'),
        #(XLUnicodeString, 'stFormat'), # FIXME: is the specification wrong here?
        (__stFormat, 'stFormat'),
    ]

@BIFF5.define
@BIFF8.define
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

class SqRefU(pstruct.type):
    _fields_ = [
        (uint2, 'cref'),
        (lambda self: dyn.array(Ref8U, self['cref'].li.int()), 'rgrefs'),
    ]

class SDContainer(pstruct.type):
    _fields_ = [
        (uint4, 'cbSD'),    # GUARD: >20
        (lambda self: dyn.block(self['cbSD'].li.int()), 'sd'),
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
        (lambda self: dyn.array(Property, self['cProp'].li.int()), 'properties'),
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
        (lambda self: dyn.array(FactoidData, self['cSmartTags'].li.int()), 'rgFactoid'),
    ]

@BIFF5.define
@BIFF8.define
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
        return undefined

    _fields_ =[
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (ubyte1, 'reserved1'),
        (uint4, 'reserved2'),
        (uint2, 'cref'),
        (uint4, 'cbFeatData'),
        (uint2, 'reserved3'),
        (lambda self: dyn.array(Reg8U, self['cref'].li.int()), 'refs'),
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

@BIFF5.define
@BIFF8.define
class FeatHdr(pstruct.type):
    type = 2151
    type = 0x867
    def __rgbHdrData(self):
        isf = self['isf'].l
        if self['cbHdrData'].li.int() == 0:
            return undefined
        if isf['ISFPROTECTION']:
            return EnhancedProtection
        elif isf['ISFFEC2']:
            return undefined
        raise NotImplementedError(isf)

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (SharedFeatureType, 'isf'),
        (ubyte1, 'reserved'),
        (uint4, 'cbHdrData'),
        (__rgbHdrData, 'rgbHdrData'),
    ]

@BIFF5.define
@BIFF8.define
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

@BIFF5.define
@BIFF8.define
class ContinueFrt(pstruct.type):
    type = 0x812
    type = 2066

    def __rgb(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)
        return dyn.block(cb - self['frtHeaderOld'].li.size())

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
        (lambda self: dyn.array(ExtProp, self['cexts'].li.int()), 'rgExt'),
    ]

@BIFF5.define
@BIFF8.define
class DXF(pstruct.type):
    type = 2189
    type = 0x88d
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'unused'),
            (1, 'fNewBorder'),
            (1, 'unused2'),
            (13, 'reserved'),
        ])
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (_flags, 'flags'),
        (XFProps, 'xfprops'),
    ]

# DXFN
class DXFNumIfmt(IFmt): pass

class DXFNumUsr(pstruct.type):
    _fields_ = [
        (ubyte1, 'cb'),
        (XLUnicodeString, 'fmt'),   # FIXME: should this be bound by cb?
    ]

class DXFFntD(pstruct.type):
    def __stFontName(self):
        cch = self['cchFont'].li.int()
        # FIXME
        return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda _, size=cch: size)
    _fields_ = [
        (ubyte1, 'cchFont'),
        (__stFontName, 'stFontName'),
        (lambda self: dyn.block(max(0, 63 - self['cchFont'].li.int())), 'unused1'),
        (Stxp, 'stxp'),
        (uint4, 'icvFore'),
        (uint4, 'reserved'),
        (Ts, 'tsNinch'),
        (uint4, 'fSssNinch'),
        (uint4, 'fUlsNinch'),
        (uint4, 'fBlsNinch'),
        (uint4, 'unused2'),
        (sint4, 'ich'),
        (uint4, 'cch'),
        (uint2, 'iFnt'),
    ]

class DXFALC(pstruct.type):
    class _flags(pbinary.struct):
        _fields_ = R([
            (HorizAlign, 'alc'),
            (1, 'fWrap'),
            (VertAlign, 'alcv'),
            (1, 'fJustLast'),
            (8, 'trot'),
            (4, 'cIndent'),
            (1, 'fShrinkToFit'),
            (1, 'fMergeCell'),
            (ReadingOrder, 'iReadingOrder'),
            (8, 'unused'),
        ])
    _fields_ = [
        (_flags, 'flags'),
        (sint2, 'iIndent'),
    ]

class DXFBdr(pbinary.struct):
    _fields_ = R([
        (BorderStyle, 'dgLeft'),
        (BorderStyle, 'dgRight'),
        (BorderStyle, 'dgTop'),
        (BorderStyle, 'dgBottom'),
        (7, 'icvLeft'),
        (7, 'icvRight'),
        (1, 'bitDiagDown'),
        (1, 'bitDiagUp'),
        (7, 'icvTop'),
        (7, 'icvBottom'),
        (7, 'icvDiag'),
        (4, 'dgDiag'),
        (7, 'unused'),
    ])

class DXFPat(pbinary.struct):
    _fields_ = R([
        (10, 'unused1'),
        (FillPattern, 'fls'),
        (7, 'icvForeground'),
        (7, 'icvBackground'),
        (2, 'unused2'),
    ])

class DXFProt(pbinary.struct):
    _fields_ = R([
        (1, 'fLocked'),
        (1, 'fHidden'),
        (14, 'reserved'),
    ])

class DXFN(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'alchNinch'),       (1, 'alcvNinch'),       (1, 'wrapNinch'),
            (1, 'trotNinch'),       (1, 'kintoNinch'),      (1, 'cIndentNinch'),
            (1, 'fShrinkNinch'),    (1, 'fMergeCellNinch'), (1, 'lockedNinch'),
            (1, 'hiddenNinch'),     (1, 'glLeftNinch'),     (1, 'glRightNinch'),
            (1, 'glTopNinch'),      (1, 'glBottomNinch'),   (1, 'glDiagDownNinch'),
            (1, 'glDiagUpNinch'),   (1, 'flsNinch'),        (1, 'icvFNinch'),
            (1, 'icvBNinch'),       (1, 'ifmtNinch'),       (1, 'fIfntNinch'),
            (1, 'unused1'),         (1, 'reserved1'),       (1, 'ibitAtrNum'),
            (1, 'ibitAtrFnt'),      (1, 'ibitAtrAlc'),      (1, 'ibitAtrBdr'),
            (1, 'ibitAtrPat'),      (1, 'ibitAtrProt'),     (1, 'iReadingOrderNinch'),
            (1, 'fIfmtUser'),       (1, 'unused2'),         (1, 'fNewBorder'),
            (1, 'fZeroInited'),
        ])
    def __dxfnum(self):
        f = self['flags'].li
        if f['ibitAtrNum']:
            return DXFNumUsr if f['fIfmtUser'] else DXFNumIfmt
        return undefined

    hasFlag = lambda t, field: lambda self: field if self['flags'].li[field] else undefined
    _fields_ = [
        (_flags, 'flags'),
        (__dxfnum,  'dxfnum'),
        (hasFlag(DXFFntD,'ibitAtrFnt'), 'dxffntd'),
        (hasFlag(DXFALC,'ibitAtrAlc'),  'dxfalc'),
        (hasFlag(DXFBdr,'ibitAtrBdr'),  'dxfbdr'),
        (hasFlag(DXFPat,'ibitAtrPat'),  'dxfpat'),
        (hasFlag(DXFProt,'ibitAtrProt'),'dxfprot'),
    ]

class DXFN12List(pstruct.type):
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
        # FIXME
        return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda _, size=cb: size) if do['vtValue'].int() == 6 else undefined
    def __str2(self):
        do = self['doper1'].li
        cb = do['vtValue']['cch'].int()
        return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda _, size=cb: size) if do['vtValue'].int() == 6 else undefined

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
        (lambda self: AutoFilter, 'recAutoFilter'),
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
        (lambda self: dyn.array(Feat11XMapEntry, self['iXmapMac'].li.int()), 'rgXmap'),
    ]

class ListParsedArrayFormula(pstruct.type):
    def __rgce(self):
        cb = self['cce'].li.int()
        # FIXME
        return dyn.clone(Rgce, blocksize=lambda _, size=cb: size)

    def __RgbExtra(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)
        sz = self['cce'].li.size() + self['cce'].int()
        return dyn.block(bs - sz)

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

#class Feat11WSSListInfo(undefined):       # FIXME
#    pass

class CachedDiskHeader(pstruct.type):
    def __strStyleName(self):
        p = self.getparent(type=Feat11FieldDataItem)
        return XLUnicodeString if p['flags']['fSaveStyleName'].int() == 1 else undefined

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
        # FIXME
        return dyn.clone(DXFN12List, blocksize=lambda _, size=sz: size)

    def __dxfFmtInsertRow(self):
        sz = self['cbFmtInsertRow'].li.int()
        # FIXME
        return dyn.clone(DXFN12List, blocksize=lambda _, size=sz: size)

    def __AutoFilter(self):
        tft = self['flag'].l
        return Feat11FdaAutoFilter if tft['fAutoFilter'] else undefined

    def __rgXmap(self):
        tft = self['flags'].l
        return Feat11XMap if tft['fLoadXmapi'] else undefined

    def __fmla(self):
        tft = self['flags'].l
        return Feat11FdaAutoFilter if tft['fLoadFmla'] else undefined

    def __totalFmla(self):
        tft = self['flags'].l
        return ListParsedArrayFormula if tft['fLoadTotalArray'] else ListParsedFormula

    def __strTotal(self):
        tft = self['flags'].l
        return XLUnicodeString if tft['fLoadTotalStr'] else undefined

    def __wssInfo(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return Feat11WSSListInfo if lt.int() == 1 else undefined

    def __qsif(self):
        lt = self.getparent(type=TableFeatureType)['lt'].l
        return uint4 if lt.int() == 3 else undefined

    def __dskHdrCache(self):
        tft = self.getparent(type=TableFeatureType).l
        return CachedDiskHeader if tft['crwHeader'].int() == 0 and tft['flags']['fSingleCell'].int() == 0 else undefined

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
        (lambda self: dyn.array(uint4, self['cId'].li.int()), 'rgId'),
    ]
class Feat11RgSharepointIdDel(Feat11RgSharepointId): pass
class Feat11RgSharepointIdChange(Feat11RgSharepointId): pass

class Feat11CellStruct(pstruct.type):
    _fields_ = [(uint4, 'idxRow'),(uint4,'idxField')]

class Feat11RgInvalidCells(pstruct.type):
    _fields_ = [
        (uint2, 'cCellInvalid'),
        (lambda self: dyn.array(Feat11CellStruct, self['cCellInvalid'].li.int()), 'rgCellInvalid'),
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
        return XLUnicodeString if self['flags'].li['fLoadCSPName'] else undefined
    def __entryId(self):
        return XLUnicodeString if self['flags'].li['fLoadEntryId'] else undefined
    def __idDeleted(self):
        return Feat11RgSharepointIdDel if self['flags'].li['fLoadPldwIdDeleted'] else undefined
    def __idChanged(self):
        return Feat11RgSharepointIdChange if self['flags'].li['fLoadPldwIdChanged'] else undefined
    def __cellInvalid(self):
        return Feat11RgInvalidCells if self['flags'].li['fLoadPllstclInvalid'] else undefined

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
        (lambda self: dyn.array(Feat11FieldDataItem, self['cFieldData'].li.int()), 'fieldData'),
        (__idDeleted, 'idDeleted'),
        (__idChanged, 'idChanged'),
        (__cellInvalid, 'cellInvalid'),
    ]

@BIFF5.define
@BIFF8.define
class Feature11(pstruct.type):
    type = 2162
    type = 0x872

    def __rgbFeat(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.block(0)

        sz = self['cbFeatData'].li.int()
        if sz == 0:
            sz = cb - (self['refs2'].li.size()+27)
        return dyn.block(sz)

    _fields_ = [
        (FrtRefHeaderU, 'frtRefHeaderU'),
        (SharedFeatureType, 'isf'),
        (ubyte1, 'reserved1'),
        (uint4, 'reserved2'),
        (uint2, 'cref2'),
        (uint4, 'cbFeatData'),
        (uint2, 'reserved3'),
        (lambda self: dyn.array(Ref8U, self['cref2'].li.int()), 'refs2'),
        (__rgbFeat, 'rgbFeat'),
    ]

@BIFF5.define
@BIFF8.define
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

        (lambda self: (DXFN12List if self['cbdxfHeader'].li.int() > 0 else undefined), 'dxfHeader'),
        (lambda self: (DXFN12List if self['cbdxfData'].li.int() > 0 else undefined), 'dxfData'),
        (lambda self: (DXFN12List if self['cbdxfAgg'].li.int() > 0 else undefined), 'dxfAgg'),
        (lambda self: (DXFN12List if self['cbdxfBorder'].li.int() > 0 else undefined), 'dxfBorder'),
        (lambda self: (DXFN12List if self['cbdxfHeaderBorder'].li.int() > 0 else undefined), 'dxfHeaderBorder'),
        (lambda self: (DXFN12List if self['cbdxfAggBorder'].li.int() > 0 else undefined), 'dxfAggBorder'),

        (lambda self: (XLUnicodeString if self['istnHeader'].li.int() != -1 else undefined), 'stHeader'),
        (lambda self: (XLUnicodeString if self['istnData'].li.int() != -1 else undefined), 'stData'),
        (lambda self: (XLUnicodeString if self['istnAgg'].li.int() != -1 else undefined), 'stAgg'),
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

@BIFF5.define
@BIFF8.define
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
        return undefined

    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (uint2, 'lsd'),
        (uint4, 'idList'),
        (__rgb, 'rgb'),
    ]

@BIFF5.define
@BIFF8.define
class GUIDTypeLib(pstruct.type):
    type = 2199
    type = 0x897
    _fields_ = [
        (FrtHeader, 'frtHeader'),
        (dyn.block(16), 'guid'),
    ]

@BIFF5.define
@BIFF8.define
class SerParent(uint2):
    type = 4170
    type = 0x104a

@BIFF5.define
@BIFF8.define
class Begin(undefined):
    type = 4147
    type = 0x1033

@BIFF5.define
@BIFF8.define
class End(undefined):
    type = 4148
    type = 0x1034

@BIFF5.define
@BIFF8.define
class StartBlock(undefined):
    type = 2130
    type = 0x852

@BIFF5.define
@BIFF8.define
class EndBlock(undefined):
    type = 2131
    type = 0x853

#@BIFF5.define
@BIFF8.define
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

@BIFF5.define
@BIFF8.define
class SST(pstruct.type):
    type = 252
    type = 0xfc

    def __rgb(self):
        try:
            p = self.getparent(RecordGeneralBase)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            res = self['cstUnique'].li
            return dyn.array(XLUnicodeRichExtendedString, abs(res.int()))
        return dyn.blockarray(XLUnicodeRichExtendedString, cb - sum(self[fld].li.size() for fld in ['cstTotal', 'cstUnique']))

    _fields_ = [
        (sint4, 'cstTotal'),     # GUARD: >=0
        (sint4, 'cstUnique'),    # GUARD: >=0
        (__rgb, 'rgb'),
    ]

class Phs(pstruct.type):
    class formatinfo(pbinary.struct):
        _fields_ = R([(2,'phType'),(2,'alcH'),(12,'unused')])

    _fields_ = [
        (FontIndex, 'ifnt'),
        (formatinfo, 'ph'),
    ]


class RPHSSub(pstruct.type):
    _fields_ = [
        (uint2, 'crun'),
        (uint2, 'cch'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cch'].li.int()), 'st'),
    ]
    def summary(self):
        return "crun={:#0{:d}x} st={:s}".format(self['crun'].int(), 2 + 2 * self['crun'].size(), self['st'].summary())

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
        (lambda self: dyn.array(PhRuns, self['rphssub'].li['crun'].int()), 'rgphruns')
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
        type = pstr.wstring if f['fHighByte'] else pstr.string
        return dyn.clone(type, length=self['cch'].li.int())
    def __ExtRst(self):
        f = self['flags'].l
        return ExtRst if f['fExtSt'] else undefined

    _fields_ = [
        (uint2, 'cch'),
        (_flags, 'flags'),
        (__cRun, 'cRun'),
        (__cbExtRst, 'cbExtRst'),
        (__rgb, 'rgb'),
        (lambda self: dyn.array(FormatRun, self['cRun'].li.int()), 'rgRun'),
        (__ExtRst, 'ExtRst'),
    ]

class FilePointer(uint4): pass
class ISSTInf(pstruct.type):
    _fields_ = [
        (FilePointer, 'ib'),
        (uint2, 'cbOffset'),
        (uint2, 'reserved'),
    ]

@BIFF5.define
@BIFF8.define
class ExtSST(pstruct.type):
    type = 255
    type = 0xff
    def __rgISSTInf(self):
        rg = self.getparent(RecordGeneralBase)
        container = rg.p
        index = container.value.index(rg)
        while index > 0 and isinstance(container.value[index - 1].d, Continue):
            index -= 1

        if index == 0 or not isinstance(container[index - 1].d, SST):
            logging.warn("{:s}.__rgISSTInf : Unable to locate SST at index {:d}".format(self.instance(), index))
            return dyn.array(ISSTInf, 0)
        previous = container[index - 1].d

        # Figure out how many ISSTInf records there are
        cu, dsst = previous['cstUnique'].li.int(), self['dsst'].li.int()
        if dsst > 0:
            count = (cu // dsst) + (1 if cu % dsst else 0)
            return dyn.array(ISSTInf, count)

        # If dsst is 0, then just return 0 to avoid dividing by it
        return dyn.array(ISSTInf, 0)

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
        # FIXME
        return dyn.clone(Rgce, blocksize=lambda _, size=cce: size)

    _fields_ = [
        (_flags, 'flags'),
        (uint4, 'unused'),
        (__rgce, 'rgce'),
    ]

class PictFmlaEmbedInfo(pstruct.type):
    def __strClass(self):
        cb = self['cbClass'].li.int()
        # FIXME
        if cb:
            return dyn.clone(XLUnicodeStringNoCch, blocksize=lambda _, size=cb: size)
        return undefined

    _fields_ = [
        (ubyte1, 'ttb'),
        (ubyte1, 'cbClass'),
        (ubyte1, 'reserved'),
        (__strClass, 'strClass'),
    ]

class ObjFmla(pstruct.type):
    #class _formula(pstruct.type):
    #    def __formula(self):
    #        try:
    #            p = self.getparent(RecordGeneralBase)
    #            cb = p['header'].li.Length()
    #        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
    #            return dyn.clone(ObjectParsedFormula, blocksize=lambda _: 0)
    #        return dyn.clone(ObjectParsedFormula, blocksize=lambda _, size=cb: size - s.p['embedInfo'].blocksize())

    #    _fields_ = [
    #        (__formula, 'formula'),
    #        (PictFmlaEmbedInfo, 'embedInfo'),
    #    ]

    #def __fmla(self):
    #    cb = self['cbFmla'].li.int()
    #    return dyn.clone(ObjectParsedFormula, blocksize=lambda _, size=cb: size)

    _fields_ = [
        (uint2, 'cbFmla'),
        (ObjectParsedFormula, 'fmla'),
        (PictFmlaEmbedInfo, 'embedInfo'),
        (lambda self: dyn.block(self['cbFmla'].li.int() - self['fmla'].li.int() - self['embedInfo'].li.int()), 'padding'),
    ]

class ObjFmlaNoSize(ObjectParsedFormula):
    pass

class Ft(ptype.definition):
    attribute, cache = 'featureType', {}

    class FtUnknown(ptype.block):
        def classname(self):
            res = getattr(self, Ft.attribute, None)
            return self.typename() if res is None else "{:s}<{:04x}>".format(self.typename(), res)
    default = FtUnknown

class FtGeneral(pstruct.type):
    def __data(self):
        res, cb = self['ft'].li.int(), self['cb'].li.int()
        # FIXME
        return Ft.withdefault(res, featureType=res, blocksize=lambda _, size=cb: size)

    _fields_ = [
        (uint2, 'ft'),          # XXX: Make this a pint.enum
        (uint2, 'cb'),
        (__data, 'data'),
    ]

@Ft.define
class FtReserved(undefined):
    featureType = 0x0000

@Ft.define
class FtMacro(ObjFmlaNoSize):
    featureType = 0x0004

@Ft.define
class FtGmo(pstruct.type):
    featureType = 0x0006
    _fields_ = [
        (uint2, 'unused'),
    ]

@Ft.define
class FtCf(pint.enum, uint2):
    featureType = 0x0007
    _values_ = [
        ('emf', 0x0002),
        ('bmp', 0x0009),
        ('unspecified', 0xffff),
    ]

@Ft.define
class FtPioGrbit(pbinary.flags):
    featureType = 0x0008
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

class PictFmlaKey(pstruct.type):
    _fields_ = [
        (uint4, 'cbKey'),
        (lambda self: dyn.block(self['cbKey'].li.int()), 'keyBuf'),
        (ObjFmla, 'fmlaLinkedCell'),    # FIXME
        (ObjFmla, 'fmlaListFillRange'),
    ]

@Ft.define
class FtPictFmla(pstruct.type):
    featureType = 0x0009
    _fields_ = [
        (ObjFmlaNoSize, 'fmla'),
        (uint4, 'IPosInCtlStm'),
        (PictFmlaKey, 'key'),
    ]

@Ft.define
class FtCbls(pstruct.type):
    featureType = 0x000a
    _fields_ = [
        (uint4, 'unused1'),
        (uint4, 'unused2'),
        (uint4, 'unused3'),
    ]

@Ft.define
class FtRbo(pstruct.type):
    featureType = 0x000b
    _fields_ = [
        (uint4, 'unused1'),
        (uint2, 'unused2'),
    ]

@Ft.define
class FtSbs(pstruct.type):
    featureType = 0x000c
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
    featureType = 0x000d
    class _fSharedNote(pint.enum, uint2):
        _values_ = [('unshared',0),('shared',1)]
    _fields_ = [
        (dyn.block(16), 'guid'),
        (_fSharedNote, 'fSharedNote'),
        (uint4, 'unused'),
    ]

class ObjLinkFmla(ObjFmlaNoSize):
    pass

@Ft.define
class ObjLinkFmla_000e(ObjLinkFmla):
    featureType = 0x000e

@Ft.define
class FtGboData(pstruct.type):
    featureType = 0x000f
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

@Ft.define
class FtEdoData(pstruct.type):
    featureType = 0x0010
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

@Ft.define
class FtRboData(pstruct.type):
    featureType = 0x0011
    class _fFirstBtn(pint.enum, uint2):
        _values_ = [('first', 1),('other',0)]
    _fields_ = [
        (ObjId, 'idRadNext'),
        (_fFirstBtn, 'fFirstBtn'),
    ]

@Ft.define
class FtCblsData(pstruct.type):
    featureType = 0x0012
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
    featureType = 0x0013
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
        (lambda self: dyn.array(XLUnicodeString, self['cLines'].li.int()), 'dropData'),
        (lambda self: dyn.array(s._bsels, self['cLines'].li.int()), 'bsels'),
    ]

@Ft.define
class ObjLinkFmla_0014(ObjLinkFmla):
    featureType = 0x0014

@Ft.define
class FtCmo(pstruct.type):
    featureType = 0x0015
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

@BIFF5.define
class OBJ(pstruct.type):
    type = 0x005d
    type = 93
    _fields_ = [
        # FIXME
    ]

@BIFF8.define
class Obj(pstruct.type):
    type = 0x005d
    type = 93
    def __props(self):
        try:
            res = self.getparent(RecordGeneralBase)
            cb = res['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return dyn.array(FtGeneral, 0)

        return dyn.blockarray(FtGeneral, cb - self['cmo'].li.size())

    _fields_ = [
        (FtGeneral, 'cmo'),
        (__props, 'props'),
    ]

class FormatRun(pstruct.type):
    _fields_ = [
        (uint2, 'ich'),
        (FontIndex, 'ifnt'),
    ]

class Run(pstruct.type):
    _fields_ = [
        (FormatRun, 'formatRun'),
        (uint2, 'unused1'),
        (uint2, 'unused2'),
    ]

class TxOLastRun(pstruct.type):
    _fields_ = [
        (uint2, 'cchText'),
        (uint2, 'unused1'),
        (uint4, 'unused2'),
    ]

class TxORuns(pstruct.type):
    def __rgTxoRuns(self):
        try:
            rg = self.getparent(RecordGeneralBase)
            res = rg.previousRecord(TxO, **count)
        except ptypes.error.ItemNotFoundError:
            return dyn.array(Run, 0)

        cbRuns = res.d['cbRuns']
        return dyn.array(Run, cbRuns.int() // 8 - 1)
    _fields_ = [
        (__rgTxoRuns, 'rgTxoRuns'),
        (TxOLastRun, 'lastRun'),
    ]

@BIFF5.define
@BIFF8.define
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
        rg = self.getparent(RecordGeneralBase)
        return rg.previousRecord(Obj, **count)

    def __fmla(self):
        try:
            res = self.getparent(RecordGeneralBase)
            cb = res['header'].li.Length()

        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            # XXX: unable to calculate size of element without the blocksize
            return dyn.block(0)

        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(cb - res)

    def __reserved(type):
        def reserved(self, type=type):
            try:
                res = self.__previousObjRecord()
            except:
                return undefined
            if res.d['cmo'].li['data']['ot'].int() not in {0,5,7,11,12,14}:
                return type
            return pint.uint_t
        return reserved

    def __controlInfo(self):
        try:
            res = self.__previousObjRecord()
            if res.d['cmo'].li['data']['ot'].int() in {0,5,7,11,12,14}:
                return ControlInfo
        except: pass
        return ControlInfo

    _fields_ = [
        (_flags, 'flags'),
        (_rot, 'rot'),
        #(lambda self: uint2 if self.__previousObjRecord().d['cmo'].li['data']['ot'].int() not in {0,5,7,11,12,14} else pint.uint_t, 'reserved4'),
        #(lambda self: uint4 if self.__previousObjRecord().d['cmo'].li['data']['ot'].int() not in {0,5,7,11,12,14} else pint.uint_t, 'reserved5'),
        (__reserved(uint2), 'reserved4'),
        (__reserved(uint4), 'reserved5'),
        #(lambda self: ControlInfo if self.__previousObjRecord().d['cmo'].li['data']['ot'].int() in {0,5,7,11,12,14} else undefined, 'controlInfo'),
        (__controlInfo, 'controlInfo'),
        (uint2, 'cchText'),
        (uint2, 'cbRuns'),
        (FontIndex, 'ifntEmpty'),
#        (ObjFmla, 'fmla'),     # FIXME
        (__fmla, 'fmla'),
    ]

@BIFF5.define
@BIFF8.define
class Continue(ptype.block):
    type = 0x3c
    type = 60

@BIFF5.define
@BIFF8.define
class CondFmt(pstruct.type):
    type = 0x1b0
    type = 432
    class _id(pbinary.struct):
        _fields_ = R([
            (1, 'fToughRecalc'),
            (15, 'nID'),
        ])
    _fields_ = [
        (uint2, 'ccf'),
        (_id, 'id'),
        (Ref8U, 'refBound'),
        (SqRefU, 'sqref'),
    ]

@BIFF5.define
@BIFF8.define
class Palette(pstruct.type):
    type = 0x92
    type = 146
    _fields_ = [
        (sint2, 'ccv'),
        (lambda self: dyn.array(LongRGB, self['ccv'].li.int()), 'rgColor'),
    ]

@BIFF5.define
@BIFF8.define
class HEADER(pstruct.type):
    type = 0x14
    type = 20
    _fields_ = [
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgch'),
    ]
    def summary(self):
        return self['rgch'].summary()
    def str(self):
        return self['rgch'].str()

@BIFF5.define
@BIFF8.define
class FOOTER(pstruct.type):
    type = 0x15
    type = 21
    _fields_ = [
        (ubyte1, 'cch'),
        (lambda self: dyn.clone(pstr.string, length=self['cch'].li.int()), 'rgch'),
    ]
    def summary(self):
        return self['rgch'].summary()
    def str(self):
        return self['rgch'].str()

@BIFF5.define
@BIFF8.define
class EXTERNCOUNT(pstruct.type):
    type = 0x16
    type = 22
    _fields_ = [
        (uint2, 'cxals'),
    ]
    def summary(self):
        return "cxals={:s}".format(self['cxals'].summary())

@BIFF5.define
@BIFF8.define
class SELECTION(pstruct.type):
    type = 0x1d
    type = 29

    class _ref(pstruct.type):
        _fields_ = [
            (RwU, 'rwFirst'),
            (RwU, 'rwLast'),
            (ColByteU, 'colFirst'),
            (ColByteU, 'colLast'),
        ]
        def summary(self):
            return "rwFirst={:d} rwLast={:d} colFirst={:d} colLast={:d}".format(*(self[fld].int() for fld in ['rwFirst', 'rwLast', 'colFirst', 'colLast']))

    _fields_ = [
        (ubyte1, 'pnn'),
        (Rw, 'rwAct'),
        (Col, 'colAct'),
        (uint2, 'irefAct'),
        (uint2, 'cref'),
        (lambda self: dyn.array(self._ref, self['cref'].li.int()), 'rgref'),
    ]

@BIFF5.define
@BIFF8.define
class LEFTMARGIN(pstruct.type):
    type = 0x26
    type = 38
    _fields_ = [
        (Xnum, 'num'),
    ]

@BIFF5.define
@BIFF8.define
class RIGHTMARGIN(pstruct.type):
    type = 0x27
    type = 39
    _fields_ = [
        (Xnum, 'num'),
    ]

@BIFF5.define
@BIFF8.define
class TOPMARGIN(pstruct.type):
    type = 0x28
    type = 40
    _fields_ = [
        (Xnum, 'num'),
    ]

@BIFF5.define
@BIFF8.define
class BOTTOMMARGIN(pstruct.type):
    type = 0x29
    type = 41
    _fields_ = [
        (Xnum, 'num'),
    ]

@BIFF5.define
@BIFF8.define
class DCON(pstruct.type):
    type = 0x50
    type = 80
    _fields_ = [
        (uint2, 'iiftab'),
        (uint2, 'fLeftCat'),
        (uint2, 'fTopCat'),
        (uint2, 'fLinkConsol'),
    ]

@BIFF5.define
@BIFF8.define
class DEFCOLWIDTH(pstruct.type):
    type = 0x55
    type = 85
    _fields_ = [
        (uint2, 'cchdefColWidth'),
    ]

@BIFF5.define
@BIFF8.define
class HCENTER(pstruct.type):
    type = 0x83
    type = 131
    _fields_ = [
        (uint2, 'fHCenter'),
    ]

@BIFF5.define
@BIFF8.define
class VCENTER(pstruct.type):
    type = 0x84
    type = 132
    _fields_ = [
        (uint2, 'fVCenter'),
    ]

@BIFF5.define
@BIFF8.define
class STANDARDWIDTH(pstruct.type):
    type = 0x99
    type = 153
    _fields_ = [
        (uint2, 'DxGCol'),
    ]

@BIFF5.define
@BIFF8.define
class SETUP(pstruct.type):
    type = 0xa1
    type = 161
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fLeftToRight'),
            (1, 'fLandscape'),
            (1, 'fNoPls'),
            (1, 'fNoColor'),
            (1, 'fDraft'),
            (1, 'fNotes'),
            (1, 'fNoOrient'),
            (1, 'fUsePage'),
            (1, 'Reserved'),
            (1, 'fEndNotes'),
            (2, 'iErrors'),
            (4, 'unused'),
        ])
    _fields_ = [
        (uint2, 'iPaperSize'),
        (uint2, 'iScale'),
        (uint2, 'iPageStart'),
        (uint2, 'iFitWidth'),
        (uint2, 'iFitHeight'),
        (_flags, 'grbit'),
        (uint2, 'iRes'),
        (uint2, 'iVRes'),
        (Xnum, 'numHdr'),
        (Xnum, 'numFtr'),
        (uint2, 'iCopies'),
    ]

@BIFF5.define
@BIFF8.define
class DIMENSIONS(pstruct.type):
    type = 0x200
    type = 512
    _fields_ = [
        (uint4, 'rwMic'),
        (uint4, 'rwMac'),
        (Col, 'colMic'),
        (Col, 'colMac'),
        (uint2, 'reserved'),
    ]

@BIFF5.define
@BIFF8.define
class WINDOW2(pstruct.type):
    type = 0x23e
    type = 574
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fDspFmla'),
            (1, 'fDspGrid'),
            (1, 'fDspRwCol'),
            (1, 'fFrozen'),
            (1, 'fDspZeroes'),
            (1, 'fDefaultHdr'),
            (1, 'fRightToLeft'),
            (1, 'fDspGuts'),
            (1, 'fFrozenNoSplit'),
            (1, 'fSelected'),
            (1, 'fPaged'),
            (1, 'fSLV'),
            (4, 'reserved'),
        ])
    _fields_ = [
        (_flags, 'grbit'),
        (Rw, 'rwTop'),
        (Col, 'colLeft'),
        (uint4, 'icvHdr'),
        (uint2, 'wScaleSLV'),
        (uint2, 'wScaleNormal'),
        (uint4, 'reserved'),
    ]

@BIFF5.define
@BIFF8.define
class CF(pstruct.type):
    type = 0x1b1
    type = 433
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'unused1'),
            (1, 'fStopIfTrue'),
            (2, 'reserved1'),
            (1, 'unused2'),
            (3, 'reserved2'),
        ])
    class _icfTemplate(pint.enum, uint2):
        _values_ = [
            ('Cell value', 0x0000),
            ('Formula', 0x0001),
            ('Color scale formatting', 0x0002),
            ('Data bar formatting', 0x0003),
            ('Icon set formatting', 0x0004),
            ('Filter', 0x0005),
            ('Unique values', 0x0007),
            ('Contains text', 0x0008),
            ('Contains blanks', 0x0009),
            ('Contains no blanks', 0x000A),
            ('Contains errors', 0x000B),
            ('Contains no errors', 0x000C),
            ('Today', 0x000F),
            ('Tomorrow', 0x0010),
            ('Yesterday', 0x0011),
            ('Last 7 days', 0x0012),
            ('Last month', 0x0013),
            ('Next month', 0x0014),
            ('This week', 0x0015),
            ('Next week', 0x0016),
            ('Last week', 0x0017),
            ('This month', 0x0018),
            ('Above average', 0x0019),
            ('Below Average', 0x001A),
            ('Duplicate values', 0x001B),
            ('Above or equal to average', 0x001D),
            ('Below or equal to average', 0x001E),
        ]

    def __rgce(field):
        def rgce(self, field=field):
            cce = self[field].li.int()
            # FIXME
            return dyn.clone(CFParsedFormulaNoCCE, blocksize=lambda _, size=cce: size)
        return rgce

    def __rgbCT(self):
        ct = self['ct'].li.int()
        if ct in {0x01, 0x02}:
            return undefined
        elif ct in {0x03}:
            return CFGradient
        elif ct in {0x04}:
            return CFDatabar
        elif ct in {0x05}:
            return CFFilter
        elif ct in {0x06}:
            return CFMultistate
        logging.warn('{:s}.__rgbCT : Unknown ct value. : {:02x}'.format(self.instance(), ct))
        return undefined

    _fields_ = [
        (ubyte1, 'ct'),
        (ubyte1, 'cp'),
        (uint2, 'cce1'),
        (uint2, 'cce2'),
        (DXFN, 'rgbdxf'),
        (__rgce('cce1'), 'rgce1'),
        (__rgce('cce2'), 'rgce2'),
        (CFParsedFormula, 'fmlaActive'),
        (uint2, 'ipriority'),
        (_icfTemplate, 'icfTemplate'),
        (ubyte1, 'cbTemplateParm'),
        #(CFExTemplateParams, 'rgbTemplateParms'),  # FIXME
        (lambda self: dyn.block(self['cbTemplateParm'].li.int()), 'rgbTemplateParms'),
        (__rgbCT, 'rgbCT'),
    ]

class RRD(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fAccepted'),
            (1, 'fUndoAction'),
            (1, 'unused'),
            (1, 'fDelAtEdgeOfSort'),
            (12, 'reserved'),
        ])
    _fields_ = [
        (uint4, 'cbMemory'),
        (sint4, 'revid'),
        (RevisionType, 'revt'),
        (_flags, 'flags'),
        (TabId, 'tabid'),
    ]

class NoteRR(pstruct.type):
    class _revisionFlags(pbinary.flags):
        _fields_ = R([
            (1, 'bitfDelNote'),
            (1, 'bitfAddNote'),
            (14, 'reserved1'),
        ])
    class _hideFlags(pbinary.flags):
        _fields_ = R([
            (1, 'reserved2'),
            (1, 'fShow'),
            (5, 'reserved3'),
            (1, 'fRwHidden'),
            (1, 'fColHidden'),
            (2, 'reserved4'),
            (1, 'unused1'),
            (4, 'reserved5'),
        ])
    _fields_ = [
        (RRD, 'rrd'),
        (_revisionFlags, 'revFlags'),
        (RwU, 'row'),
        (ColU, 'col'),
        (_hideFlags, 'hideFlags'),
        (dyn.block(16), 'guid'),    # FIXME
        (uint4, 'ichEnd'),
        (uint4, 'cchNote'),
        (XLUnicodeString, 'stAuthor'),
        (uint2, 'unused2'),
    ]

class NoteSh(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'reserved1'),
            (1, 'fShow'),
            (1, 'reserved2'),
            (1, 'unused1'),
            (3, 'reserved3'),
            (1, 'fRwHidden'),
            (1, 'fColHidden'),
            (7, 'reserved4'),
        ])

    _fields_ = [
        (Rw, 'row'),
        (Col, 'col'),
        (_flags, 'flags'),
        (ObjId, 'idObj'),
        (XLUnicodeString, 'stAuthor'),
        (ubyte1, 'unused2'),
    ]

@BIFF5.define
@BIFF8.define
class Note(pstruct.type):
    type = 0x1c
    type = 28

    def __body(self):
        container = self.getparent(type=RecordContainer)
        record = container[0].d

        # FIXME: is this the right way to determine which stream we're in?
        dt = record['dt']
        return NoteSh if dt in {'workbook', 'worksheet', 'macrosheet'} else NoteRR

    _fields_ = [
        (__body, 'body'),
    ]

class ObjectLink(pstruct.type):
    class _WLinkObj(pint.enum, uint2):
        _values_ = [
            ('Entire chart', 0x0001),
            ('Value axis, or vertical value axis on bubble and scatter chart groups', 0x0002),
            ('Category axis, or horizontal value axis on bubble and scatter chart groups.', 0x0003),
            ('Series or data points.', 0x0004),
            ('Series axis.', 0x0007),
            ('Display units labels of an axis.', 0x000c),
        ]

    _fields_ = [
        (_WLinkObj, 'wLinkObj'),
        (uint2, 'wLinkVar1'),   # index into Series
        (uint2, 'wLinkVar2'),   # index into Category
    ]

class Text(pstruct.type):
    class _at(pint.enum, ubyte1):
        _values_ = [
            ('left', 1),
            ('center', 2),
            ('right', 3),
            ('justify', 4),
            ('distributed', 7),
        ]

    class _vat(pint.enum, ubyte1):
        _values_ = [
            ('top', 1),
            ('middle', 2),
            ('bottom', 3),
            ('justify', 4),
            ('distributed', 7),
        ]

    class _wBkgMode(pint.enum, uint2):
        _values_ = [
            ('transparent', 0x0001),
            ('opaque', 0x0002),
        ]

    class _flags(pbinary.flags):
        _fields_ = R([
            (1, 'fAutoColor'),
            (1, 'fShowKey'),
            (1, 'fShowValue'),
            (1, 'unused1'),
            (1, 'fAutoText'),
            (1, 'fGenerated'),
            (1, 'fDeleted'),
            (1, 'fAutoMode'),
            (3, 'unused2'),
            (1, 'fShowLabelAndPerc'),
            (1, 'fShowPercent'),
            (1, 'fShowBubbleSizes'),
            (1, 'fShowLabel'),
            (1, 'reserved'),
        ])

    class _dlp(pbinary.struct):
        class _position(pbinary.enum):
            width = 4
            _values_ = [
                ('default', 0x0),
                ('outside-end', 0x1),
                ('inside-end', 0x2),
                ('center', 0x3),
                ('inside-base', 0x4),
                ('above', 0x5),
                ('below', 0x6),
                ('left', 0x7),
                ('right', 0x8),
                ('auto', 0x9),
                ('user', 0xa),
            ]
        class _iReadingOrder(pbinary.enum):
            width = 2
            _values_ = [
                ('default', 0),
                ('left-to-right', 1),
                ('right-to-left', 2),
            ]
        _fields_ = R([
            (_position, 'position'),
            (10, 'unused3'),
            (_iReadingOrder, 'iReadingOrder'),
        ])

    _fields_ = [
        (_at, 'at'),
        (_vat, 'vat'),
        (_wBkgMode, 'wBkgMode'),
        (LongRGB, 'rgbText'),
        (sint4, 'x'),
        (sint4, 'y'),
        (sint4, 'dx'),
        (sint4, 'dy'),
        (_flags, 'flags'),
        (Icv, 'icvText'),
        (_dlp, 'dlp'),
        (uint2, 'trot'),
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
    print(a[2])

    print(z[1])

    streams = z

    if False:
        workbook = None
        worksheets = []
        for st in streams:
            bof = st[0]['data']
            t = bof['dt']
            if t['workbook']:
                if workbook is not None:
                    print("Workbook has already been assigned. Honoring anyways..")

                workbook = st

            elif t['worksheet']:
                worksheets.append(st)

            else:
                raise NotImplementedError( repr(bof['dt']) )
            continue

    if z.source.size() == z.size():
        print('successfully parsed {:d} streams of {:#x} bytes from {:s}'.format(len(z), z.size(), filename))
        print('z: found {:d} records'.format(reduce(lambda x,y:x+len(y),z,0)))
    else:
        print('unsuccessfully parsed {:d} biffsubstreams from {:s} ({:d} != {:d})'.format(len(z), filename, z.size(), z.source.size()))
        print('z: found {:d} records'.format(reduce(lambda x,y:x+len(y),z,0)))

