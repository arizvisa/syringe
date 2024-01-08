import logging,ptypes
from ptypes import *
ptypes.setbyteorder( pint.config.byteorder.bigendian )

### base types
class uint0(pint.uint_t): pass
class int0(pint.int_t): pass
class uint8(pint.uint8_t): pass
class int8(pint.int8_t): pass
class uint16(pint.uint16_t): pass
class int16(pint.int16_t): pass
class uint32(pint.uint32_t): pass
class int32(pint.int32_t): pass

# floating based
class shortFrac(pint.int16_t): pass
class Fixed(pint.int32_t): pass

class FWord(pint.int16_t): pass
class uFWord(pint.uint16_t): pass

class F2Dot14(pint.int16_t): pass
class longDateTime(pint.uint32_t): pass     # XXX

### tables
class Table(ptype.definition):
    cache = {}
    # XXX: perhaps implement way to calculate checksum from a table

@Table.define
class cmap(pstruct.type):
    type = 'cmap'
    class entry(pstruct.type):
        _fields_ = [
            (uint16, 'platform-id'),
            (uint16, 'encoding-id'),
            (lambda s: dyn.rpointer(cmap.subtable, s.getparent(cmap)), 'offset'),
        ]
    def __data(self):
        sz = sum(x.li.size() for x in (s['version'],s['number'],s['entry']))
        return dyn.block(self.blocksize() - sz)

    _fields_ = [
        (uint16, 'version'),
        (uint16, 'number'),
        (lambda s: dyn.array(cmap.entry, s['number'].li.int()), 'entry'),
        (__data, 'data'),
    ]
    class subtable(pstruct.type):
        _fields_ = [
            (uint16, 'format'),
            (uint16, 'length'),
            (uint16, 'version'),
            (lambda s: cmap.table.withdefault(s['format'].li.int(), type=s['format'].li.int(), length=s['length'].li.int()-6), 'data'),
        ]
    class table(ptype.definition):
        cache = {}

@cmap.table.define
class cmap_format_0(pstruct.type):
    type = 0
    _fields_ = [(dyn.array(uint8,0x100),'glyphIdArray')]
@cmap.table.define
class cmap_format_2(pstruct.type):
    type = 2
    class subHeader(pstruct.type):
        _fields_ = [
            (uint16, 'firstCode'),
            (uint16, 'entryCount'),
            (int16, 'idDelta'),
            (uint16, 'idRangeOffset'),
        ]
    _fields_ = [
        (dyn.array(uint16,0x100),'subHeaderKeys'),
        # FIXME: not sure how the variable-length-arrays work here...
    ]
@cmap.table.define
class cmap_format_4(pstruct.type):
    type = 4
    _fields_ = [
        (uint16, 'segCountX2'),
        (uint16, 'searchRange'),
        (uint16, 'entrySelector'),
        (uint16, 'rangeShift'),
        (lambda s: dyn.array(uint16,s['segCountX2'].li.int()//2), 'endCount'),
        (uint16, 'reservedPad'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()//2), 'startCount'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()//2), 'idDelta'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()//2), 'idRangeOffset'),
        #(lambda s: dyn.block(s.blocksize()-s.size()), 'glyphIdArray'), # FIXME: this might not be correct
    ]
@cmap.table.define
class cmap_format_6(pstruct.type):
    type = 6
    _fields_ = [
        (uint16, 'firstCode'),
        (uint16, 'entryCount'),
        (lambda s: dyn.array(uint16, s['entryCount'].li.int()), 'glyphIdArray'),
    ]

@Table.define
class cvt(parray.block):
    type = 'cvt '
    _object_ = FWord

@Table.define
class fpgm(parray.block):
    type = 'fpgm'
    _object_ = uint8

@Table.define
class gasp(pstruct.type):
    type = 'gasp'
    _fields_ = [
        (uint16, 'version'),
        (uint16, 'numRanges'),
        (lambda s: dyn.array(gasp.range, s['numRanges'].li.int()), 'gaspRange'),
    ]
    class range(pstruct.type):
        _fields_ = [(uint16,'rangeMaxPPEM'),(uint16,'rangeGaspBehaviour')]

@Table.define
class glyf(parray.block):
    type = 'glyf'

    class singleglyph(pstruct.type):
        class _flags(pbinary.terminatedarray):
            class _element(pbinary.struct):
                _fields_ = [
                    (2,'Reserved'),
                    (1,'y-Dual'),
                    (1,'x-Dual'),
                    (1,'Repeat'),
                    (1,'y-Short'),
                    (1,'x-Short'),
                    (1,'On Curve'),
                ]
            class _object_(pbinary.struct):
                def __count(self):
                    if self['value']['Repeat']:
                        return 8
                    return 0

                _fields_ = [
                    (lambda s: s.parent._element, 'value'),
                    (__count, 'count'),
                ]
            def getActualLength(self):
                return sum(((x['count']+1) if x['value']['Repeat'] else 1) for x in self)
            def getActualElement(self, index):
                cur = index
                for x in self:
                    count = (x['count']+1) if x['value']['Repeat'] else 1
                    if cur >= 0 and cur < count:
                        return x['value']
                    cur -= count
                raise IndexError(index)
            def isTerminator(self, value):
                p = self.getparent(glyf.singleglyph)
                count = p['endPtsOfContours'][-1].int() + 1
                return self.getActualLength() >= count

        class _xCoords(parray.type):
            def _object_(self):
                idx,flags = len(self.value),self.parent['flags']
                fl = flags.getActualElement(idx)
                if fl['x-Short']:
                    return uint8
                if fl['x-Dual']:
                    return uint0
                return int16
        class _yCoords(parray.type):
            def _object_(self):
                idx,flags = len(self.value),self.parent['flags']
                fl = flags.getActualElement(idx)
                if fl['y-Short']:
                    return uint8
                if fl['y-Dual']:
                    return uint0
                return int16

        _fields_ = [
            (lambda s: dyn.array(uint16, abs(s.getparent(glyf.glyph)['numberOfContours'].li.int())), 'endPtsOfContours'),
            (uint16, 'instructionLength'),
            (lambda s: dyn.block(s['instructionLength'].li.int()), 'instructions'),
            (_flags, 'flags'),
            (lambda s: dyn.clone(s._xCoords, length=s['flags'].getActualLength()), 'xCoordinates'),
            (lambda s: dyn.clone(s._yCoords, length=s['flags'].getActualLength()), 'yCoordinates'),
        ]

    class compositeglyph(parray.terminated):
        class _object_(pstruct.type):
            class _flags(pbinary.struct):
                _fields_ = [
                    (6, 'PADDING'),
                    (1, 'USE_MY_METRICS'),
                    (1, 'WE_HAVE_INSTRUCTIONS'),
                    (1, 'WE_HAVE_A_TWO_BY_TWO'),
                    (1, 'WE_HAVE_AN_X_AND_Y_SCALE'),
                    (1, 'MORE_COMPONENTS'),
                    (1, 'RESERVED'),
                    (1, 'WE_HAVE_A_SCALE'),
                    (1, 'ROUND_XY_TO_GRID'),
                    (1, 'ARGS_ARE_XY_VALUES'),
                    (1, 'ARG_1_AND_2_ARE_WORDS'),
                ]
            class arg1and2_short(pstruct.type):
                _fields_ = [(uint16,'argument1'),(uint16,'argument2')]
            class arg1and2_fword(pstruct.type):
                _fields_ = [(FWord,'argument1'),(FWord,'argument2')]
            def __arg1and2(self):
                res = self.arg1and2_fword if 1 else self.arg1and2_short
                if self['flags'].li['ARG_1_AND_2_ARE_WORDS']:
                    return res
                return uint16

            class scale_xy(pstruct.type):
                _fields_ = [(F2Dot14,'xscale'),(F2Dot14,'yscale')]
            class scale_2x2(pstruct.type):
                _fields_ = [(F2Dot14,'xscale'),(F2Dot14,'scale01'),(F2Dot14,'scale10'),(F2Dot14,'yscale')]

            def __scale(self):
                f = self['flags']
                if f['WE_HAVE_A_SCALE']:
                    return F2Dot14
                elif f['WE_HAVE_AN_X_AND_Y_SCALE']:
                    return self.scale_xy
                elif f['WE_HAVE_A_TWO_BY_TWO']:
                    return self.scale_2x2
                return ptype.undefined

            class _instr(pstruct.type):
                _fields_ = [
                    (uint16, 'numInstr'),
                    (lambda s: dyn.block(s['numInstr'].li.int()), 'instr'),
                ]

            def __instr(self):
                return self._instr if self['flags']['WE_HAVE_INSTRUCTIONS'] else ptype.undefined

            _fields_ = [
                (_flags, 'flags'),
                (uint16, 'glyphIndex'),
                (__arg1and2, 'arg1and2'),
                (__scale, 'scale'),
                (__instr, 'instr'),
            ]
        def isTerminator(self, value):
            return value['flags']['MORE_COMPONENTS'] == 0

    class glyph(pstruct.type):
        def __data(self):
            n = self['numberOfContours'].li.int()
            if n >= 0:
                return glyf.singleglyph
            if n == -1:
                return glyf.compositeglyph
            logging.warning('glyf.compositeglyph:numberOfContours is negative but not -1:%d',n)
            return dyn.clone(ptype.undefined, length=self.blocksize()-(uint16.length*5))

        _fields_ = [
            (int16, 'numberOfContours'),
            (FWord, 'xMin'),
            (FWord, 'yMin'),
            (FWord, 'xMax'),
            (FWord, 'yMax'),
            (__data, 'header'),
            (dyn.align(2), 'alignment'),    # XXX: ?? is this right
        ]
    _object_ = glyph

# the following shit comes from here:
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6Tables.html
class BinSrchHeader(pstruct.type):
    _fields_ = [
        (uint16, 'unitSize'),       # Size of a lookup unit for this search in bytes.
        (uint16, 'nUnits'),         # Number of units of the preceding size to be searched.
        (uint16, 'searchRange'),    # The value of unitSize times the largest power of 2 that is less than or equal to the value of nUnits.
        (uint16, 'entrySelector'),  # The log base 2 of the largest power of 2 less than or equal to the value of nUnits.
        (uint16, 'rangeShift'),     # The value of unitSize times the difference of the value of nUnits minus the largest power of 2 less than or equal to the value of nUnits.
    ]
    def get_unit_type_or_something(self):
        unit = self['unitSize']
        unit_t = dyn.block(unit.int())
        return dyn.array(unit_t, self['nUnits'].int())

class LookupTableFormat(ptype.definition):
    cache = {}

@LookupTableFormat.define
class LookupTableFormatSimple(parray.block):
    type = 0

@LookupTableFormat.define
class LookupTableFormatSegment(pstruct.type):
    type = 2
    class LookupSegment(pstruct.type):
        def variable(self):
            p = self.getparent(LookupTableFormatSegment)
            return p.get_unit_type_or_something()
        _fields_ = [
            (uint16, 'lastGlyph'),  # Last glyph index in this segment
            (uint16, 'firstGlyph'), # First glyph index in this segment
            (variable, 'value'),    # The lookup value (only one)
        ]
    _fields_ = [
        (BinSrchHeader, 'binSrchHeader'),   # The units for this binary search are of type LookupSegment, and always have a minimum length of 6.
        (LookupSegment, 'segments[]'),      # The actual segments. These must already be sorted, according to the first word in each one (the last glyph in each segment).
    ]

@LookupTableFormat.define
class LookupTableFormatSegments(pstruct.type):
    type = 4
    class LookupSegment(pstruct.type):
        _fields_ = [
            (uint16, 'lastGlyph'),  # Last glyph index in this segment
            (uint16, 'firstGlyph'), # First glyph index in this segment
            (uint16, 'value'),      # A 16-bit offset from the start of the table to the data
        ]
    _fields_ = [
        (BinSrchHeader, 'binSrchHeader'),   # The units for this binary search are of type LookupSegment and always have a minimum length of 6.
        (LookupSegment, 'segments[]'),      # The actual segments. These must already be sorted, according to the first word in each one (the last glyph in each segment).
    ]

@LookupTableFormat.define
class LookupTableFormatSingle(pstruct.type):
    type = 6
    class LookupSingle(pstruct.type):
        def variable(self):
            p = self.getparent(LookupTableFormatSingle)
            return p.get_unit_type_or_something()
        _fields_ = [
            (uint16, 'glyph'),      # The glyph index
            (variable, 'value'),    # The lookup value
        ]
    _fields_ = [
        (BinSrchHeader, 'binSrchHeader'),                 # The units for this binary search are of type LookupSingle and always have a minimum length of 4.
        (LookupSingle, 'entries[]'),                 # The actual entries, sorted by glyph index.
    ]

@LookupTableFormat.define
class LookupTableFormatTrimmed(pstruct.type):
    type = 8
    def variable(self):
        entry_t, count = uint16, self['glyphCount'].li
        return dyn.array(entry_t, count.int())
    _fields_ = [
        (uint16, 'firstGlyph'),     # First glyph index included in the trimmed array.
        (uint16, 'glyphCount'),     # Total number of glyphs (equivalent to the last glyph minus the value of firstGlyph plus 1).
        (variable, 'valueArray[]'), # The lookup values (indexed by the glyph index minus the value of firstGlyph). Entries in the value array must be two bytes.
    ]

@LookupTableFormat.define
class LookupTableFormatExtended(pstruct.type):
    type = 10
    def variable(self):
        entry, count = self['unitSize'].li, self['glyphCount'].li
        entry_t = dyn.block(entry.int())
        return dyn.array(entry, count.int())
    _fields_ = [
        (uint16, 'unitSize'),       # Size of a lookup unit for this lookup table in bytes. Allowed values are 1, 2, 4, and 8.
        (uint16, 'firstGlyph'),     # First glyph index included in the trimmed array.
        (uint16, 'glyphCount'),     # Total number of glyphs (equivalent to the last glyph minus the value of firstGlyph plus 1).
        (variable, 'valueArray[]'), # The lookup values (indexed by the glyph index minus the value of firstGlyph).
    ]

class LookupTableHeader(pstruct.type):
    class _format(pint.enum):
        _values_ = [
            (0,  'Simple'),     # Simple array format. The lookup data is an array of lookup values, indexed by glyph index.
            (2,  'Segment'),    # Segment single format. Each non-overlapping segment has a single lookup value that applies to all glyphs in the segment. A segment is defined as a contiguous range of glyph indexes.
            (4,  'Segments'),   # Segment array format. A segment mapping is performed (as with Format 2), but instead of a single lookup value for all the glyphs in the segment, each glyph in the segment gets its own separate lookup value.
            (6,  'Single'),     # Single table format. The lookup data is a sorted list of <glyph index,lookup value> pairs.
            (8,  'Trimmed'),    # Trimmed array format. The lookup data is a simple trimmed array indexed by glyph index.
            (10, 'Extended'),   # Extended trimmed array format. The lookup data is a simple trimmed array indexed by glyph index.
        ]
    def __fsHeader(self):
        res = self['format'].li
        return LookupTableFormat.lookup(res.int())
    _fields_ = [
        (uint16, 'format'),         # Format of this lookup table. There are five lookup table formats, each with a format number.
        (__fsHeader, 'fsHeader'),   # Format-specific header (each of these is described in the following sections), followed by the actual lookup data. The details of the fsHeader structure are given with the different formats.
    ]
class LookupTable(LookupTableHeader):
    pass

# the following incomplete 'morx' stuff comes from here:
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6morx.html

class STXHeader(pstruct.type):
    _fields_ = [
        (uint32, 'nClasses'),           # Number of classes, which is the number of 16-bit entry indices in a single line in the state array.
        (uint32, 'classTableOffset'),   # Offset from the start of this state table header to the start of the class table.
        (uint32, 'stateArrayOffset'),   # Offset from the start of this state table header to the start of the state array.
        (uint32, 'entryTableOffset'),   # Offset from the start of this state table header to the start of the entry table.
    ]

class morx_feature_table(pstruct.type):
    _fields_ = [
        (uint16, 'featureType'),    # The type of feature.
        (uint16, 'featureSetting'), # The feature's setting (aka selector)
        (uint32, 'enableFlags'),    # Flags for the settings that this feature and setting enables.
        (uint32, 'disableFlags'),   # Complement of flags for the settings that this feature and setting disable
    ]

class subtableGlyphCoverage(pstruct.type):
    def __subTableOffsets(self):
        return dyn.array(uint32, 0)
    def __getNumGlyphs(self):
        return 0
    def __coverageBitfields(self):
        CHAR_BIT = 8
        numGlyphs = self.__getNumGlyphs()
        coverage = (numGlyphs + CHAR_BIT - 1) / CHAR_BIT
        bitfield = dyn.block(coverage)
        return dyn.array(coverage_t, 0)
    _fields_ = [
        (__subTableOffsets, 'subTableOffsets'),
        (__coverageBitfields, 'coverageBitfields'),
    ]

class morx_indic_rearrangement(pstruct.type):
    _fields_ = [
        (STXHeader, 'stxHeader'),       # The Indic rearrangement state table header
    ]

class morx_indic_rearrangement_subtable(pbinary.flags):
    class _verb(pbinary.enum):
        width, _values_ = 4, [
            ('no change', 0),
            ('Ax => xA', 1),
            ('xD => Dx', 2),
            ('AxD => DxA', 3),
            ('ABx => xAB', 4),
            ('ABx => xBA', 5),
            ('xCD => CDx', 6),
            ('xCD => DCx', 7),
            ('AxCD => CDxA', 8),
            ('AxCD => DCxA', 9),
            ('ABxD => DxAB', 10),
            ('ABxD => DxBA', 11),
            ('ABxCD => CDxAB', 12),
            ('ABxCD => CDxBA', 13),
            ('ABxCD => DCxAB', 14),
            ('ABxCD => DCxBA', 15),
        ]
    _fields_ = [
        (1, 'markFirst'),       # If set, make the current glyph the first glyph to be rearranged.
        (1, 'dontAdvance'),     # If set, don't advance to the next glyph before going to the new state. This means that the glyph index doesn't change, even if the glyph at that index has changed.
        (1, 'markLast'),        # If set, make the current glyph the last glyph to be rearranged.
        (9, 'reserved'),        # These bits are reserved and should be set to 0.
        (_verb, 'verb'),        # The type of rearrangement specified.
    ]

class morx_metamorphosis_subtable(pstruct.type):
    class _coverage(pbinary.flags):
        class _subtableType(pbinary.enum):
            width, _values_ = 8, [
                ('Rearrangement', 0),
                ('Contextual', 1),
                ('Ligature', 2),
                ('(Reserved)', 3),
                ('Noncontextual', 4),   # (“swash”) subtable.
                ('Insertion', 5),
            ]
        _fields_ = [
            (1, '0x80000000'),  # If set, this subtable will only be applied to vertical text. If clear, this subtable will only be applied to horizontal text.
            (1, '0x40000000'),  # If set, this subtable will process glyphs in descending order. If clear, it will process the glyphs in ascending order.
            (1, '0x20000000'),  # If set, this subtable will be applied to both horizontal and vertical text (i.e. the state of bit 0x80000000 is ignored).
            (1, '0x10000000'),  # If set, this subtable will process glyphs in logical order (or reverse logical order, depending on the value of bit 0x80000000).
            (20, '0x0FFFFF00'), # Reserved, set to zero.
            (8, '0x000000FF'),  # Subtable type; see following table.
        ]
        def interpretation(self):
            bit30, bit28 = self['0x40000000'], self['0x10000000']
            if (bit30, bit28) == (0, 0):
                return 'layout'
            elif (bit30, bit28) == (1, 0):
                return 'reverse-layout'
            elif (bit30, bit28) == (0, 1):
                return 'logical'
            elif (bit30, bit28) == (1, 1):
                return 'reverse-logical'
            return 'unknown'

    _fields_ = [
        (uint32, 'length'),             # Total subtable length, including this header.
        (_coverage, 'coverage'),        # Coverage flags and subtable type.
        (uint32, 'subFeatureFlags'),    # The 32-bit mask identifying which subtable this is (the subtable being executed if the AND of this value and the processed defaultFlags is nonzero)
    ]

class morx_contextual_glyph_substitution(pstruct.type):
    _fields_ = [
        (STXHeader, 'stxHeader'),       # The contextual glyph substitution state table header
        (uint32, 'substitutionTable'),  # Byte offset from the beginning of the state subtable to the beginning of the substitution tables.
    ]

class morx_contextual_glyph_substitution_subtable(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'setMark'),     # If set, make the current glyph the marked glyph.
            (1, 'dontAdvance'), # If set, don't advance to the next glyph before going to the new state.
            (14, 'reserved'),   # These bits are reserved and should be set to 0.
        ]
    _fields_ = [
        (uint16, 'newState'),       # Zero-based index to the new state
        (_flags, 'flags'),          # Table-specific flags.
        (uint16, 'markIndex'),      # Index of the substitution table for the marked glyph (use 0xFFFF for none)
        (uint16, 'currentIndex'),   # Index of the substitution table for the current glyph (use 0xFFFF for none)
    ]

class morx_non_contextual_glyph_substitution_subtable(pstruct.type):
    _fields_ = [
        (LookupTable, 'table'), # The noncontextual glyph substitution table
    ]

class glyph_insertion_action(pstruct.type):
    class flags(pbinary.flags):
        _fields_ = [
            (1, 'setMark'),                 # If set, mark the current glyph.
            (1, 'dontAdvance'),             # If set, don't update the glyph index before going to the new state. This does not mean that the glyph pointed to is the same one as before. If you've made insertions immediately downstream of the current glyph, the next glyph processed would in fact be the first one inserted.
            (1, 'currentIsKashidaLike'),    # If set, and the currentInsertList is nonzero, then the specified glyph list will be inserted as a kashida-like insertion, either before or after the current glyph (depending on the state of the currentInsertBefore flag). If clear, and the currentInsertList is nonzero, then the specified glyph list will be inserted as a split-vowel-like insertion, either before or after the current glyph (depending on the state of the currentInsertBefore flag).
            (1, 'markedIsKashidaLike'),     # If set, and the markedInsertList is nonzero, then the specified glyph list will be inserted as a kashida-like insertion, either before or after the marked glyph (depending on the state of the markedInsertBefore flag). If clear, and the markedInsertList is nonzero, then the specified glyph list will be inserted as a split-vowel-like insertion, either before or after the marked glyph (depending on the state of the markedInsertBefore flag).
            (1, 'currentInsertBefore'),     # If set, specifies that insertions are to be made to the left of the current glyph. If clear, they're made to the right of the current glyph.
            (1, 'markedInsertBefore'),      # If set, specifies that insertions are to be made to the left of the marked glyph. If clear, they're made to the right of the marked glyph.
            (4, 'currentInsertCount'),      # This 5-bit field is treated as a count of the number of glyphs to insert at the current position. Since zero means no insertions, the largest number of insertions at any given current location is 31 glyphs.
            (5, 'markedInsertCount'),       # This 5-bit field is treated as a count of the number of glyphs to insert at the marked position. Since zero means no insertions, the largest number of insertions at any given marked location is 31 glyphs.
        ]
    _fields_ = [
        (uint16, 'newState'),           # Zero-based index of the new state.
        (uint16, 'flags'),              # The action flags (defined below).
        (uint16, 'currentInsertIndex'), # Zero-based index into the insertion glyph table. The number of glyphs to be inserted is contained in the currentInsertCount field in the flags (see below).  A value of 0xFFFF indicates no insertion is to be done.
        (uint16, 'markedInsertIndex'),  # Zero-based index into the insertion glyph table. The number of glyphs to be inserted is contained in the markedInsertCount field in the flags (see below).  A value of 0xFFFF indicates no insertion is to be done.
    ]

class UInt32(uint32): pass
class UInt16(uint16): pass

class morx_glyph_insertion(pstruct.type):
    _fields_ = [
        (STXHeader, 'stateHeader'),         # Extended state table header
        (UInt32, 'insertionActionOffset'),  # Byte offset from stateHeader to the start of the insertion glyph table.
    ]

class morx_glyph_insertion_subtable(pstruct.type):
    _fields_ = [
    ]

class morx_ligature(pstruct.type):
    _fields_ = [
        (STXHeader, 'stateHeader'),     # Extended state table header, as described above.
        (UInt32, 'ligActionOffset'),    # Byte offset from stateHeader to the start of the ligature action table.
        (UInt32, 'componentOffset'),    # Byte offset from stateHeader to the start of the component table.
        (UInt32, 'ligatureOffset'),     # Byte offset from stateHeader to the start of the actual ligature lists.
    ]

class ligature_action_entry(pbinary.flags):
    _fields_ = [
        (1, 'last'),    # This is the last action in the list. This also implies storage.
        (1, 'store'),   # Store the ligature at the current cumulated index in the ligature table in place of the marked (i.e. currently-popped) glyph.
        (30, 'offset'), # A 30-bit value which is sign-extended to 32-bits and added to the glyph ID, resulting in an index into the component table.
    ]

class morx_ligature_subtable(pstruct.type):
    class _entryFlags(pbinary.flags):
        _fields_ = [
            (1, 'setComponent'),    # Push this glyph onto the component stack for eventual processing.
            (1, 'dontAdvance'),     # Leave the glyph pointer at this glyph for the next iteration.
            (1, 'performAction'),   # use the ligActionIndex to process a ligature group.
            (13, 'N/A'),            # Reserved; set to zero.
        ]
    _fields_ = [
        (UInt16, 'nextStateIndex'), # Row index in the state array for the state which will be used by the next glyph.
        (UInt16, 'entryFlags'),     # Flags.
        (UInt16, 'ligActionIndex'), # Index to the first ligActionTable entry for processing this group, if indicated by the flags.
    ]

class morx_chain_header(pstruct.type):
    _fields_ = [
        (uint32, 'defaultFlags'),
        (uint32, 'chainLength'),
        (uint32, 'nFeatureEntries'),
        (uint32, 'nSubtables'),
    ]

class morx_chain(pstruct.type):
    def __contents(self):
        header = self['header'].li
        size = header['chainLength'].int() - header.size()
        return dyn.block(max(0, size))

    _fields_ = [
        (morx_chain_header, 'header'),
        (__contents, 'contents'),
    ]

@Table.define
class morx(pstruct.type):
    type = 'morx'
    _fields_ = [
        (uint16, 'version'),
        (uint16, 'unused'),
        (uint32, 'nChains'),
        (lambda self: dyn.array(morx_chain, self['nChains'].li.int()), 'chains'),
        (lambda self: ptype.undefined if self['version'].li.int() < 3 else subtableGlyphCoverageArray, 'subtableGlyphCoverageArray'),
    ]

### main file format
class File(pstruct.type):
    class Entry(pstruct.type):
        class _tag(uint32):
            def str(self):
                return self.serialize()
            def summary(self, **options):
                return '{:s} (0x{:x})'.format(self.str(), self.int())

        def __table(self):
            self = self.getparent(File.Entry)
            rec, l = self['tag'].li.str(), self['length'].li.int()
            res = Table.withdefault(rec, type=rec, length=l)
            return dyn.clone(res, blocksize=lambda s:l)

        _fields_ = [
            (_tag, 'tag'),
            (uint32, 'checkSum'),
            (dyn.pointer(__table), 'offset'),
            (uint32, 'length'),
        ]
    _fields_ = [
        (Fixed, 'version'),
        (uint16, 'numTables'),
        (uint16, 'searchRange'),
        (uint16, 'entrySelector'),
        (uint16, 'rangeShift'),
        (lambda s: dyn.array(s.Entry, s['numTables'].li.int()), 'tables'),
    ]

if __name__ == '__main__':
    import ptypes, vector.ttf as ttf
    ptypes.setsource( ptypes.file('./cour.ttf', 'rb') )

    #t = dyn.block(ptypes.ptype.type.source.size())
    #a = t()
    #a = a.l

    b = ttf.File()
    b = b.l
    print('\n'.join(map(repr,((i,x['tag'].summary()) for i,x in enumerate(b['tables'])))))

    if 'tables' and False:
        print(b['tables'][0]['offset'].d.l.hexdump())
        print(b['tables'][1]['offset'].d.l.hexdump())
        print(b['tables'][8]['offset'].d.l.hexdump())
        print(b['tables'][9]['offset'].d.l.hexdump())
        print(b['tables'][10]['offset'].d.l)
        print(b['tables'][14])
        print(b['tables'][15]['offset'].d.l)

    # 'cmap'
    if 'cmap' and False:
        print(b['tables'][10])
        x = b['tables'][10]['offset'].d.l
        print(x)
        print(x['entry'][0]['offset'].d.l)
        print(x['entry'][0]['offset'].d.l['data'])
        print(x['entry'][1]['offset'].d.l['data'].hexdump())
        print(x['entry'][2]['offset'].d.l['data'])
        print(x.blocksize())

    # 'glyf'
    if 'glyf' and True:
        print(b['tables'][14])
        c = b['tables'][14]['offset'].d
        c = c.l

        #print(c[1]['header'])
        #d = c[1]
        #fl = d['header']['flags']
        #for i in range(fl.getActualLength()):
        #    f = set((k.lower() for k,v in fl.getActualElement(i).items() if v))
        #    print(i, ','.join(f))

        if 'simple' and False:
            c = c.l
            (X,Y) = (0,0)
            for i,(x,y) in enumerate(zip(d['header']['xCoordinates'],d['header']['yCoordinates'])):
                f = d['header']['flags'].getActualElement(i)
                fl = set((k.lower() for k,v in f.items() if v))

                dx = x.int()
                if 'x-short' in fl:
                    dx = dx if 'x-dual' in fl else -dx

                dy = y.int()
                if 'y-short' in fl:
                    dy = dy if 'y-dual' in fl else -dy
                (X,Y) = (X+dx,Y+dy)
                print(i, (X,Y))

        if False:
            d = ttf.glyf.glyph(offset=c.getoffset()+0x9036)
            d = d.l
            e = d['header']
            print(e[0]['flags'])
            print(e[1]['flags'])
            print(e[1]['scale'].hexdump())

