from ptypes import *
from stypes import *
import as3,action

class Unknown(ptype.type):
    def shortname(self):
        s = super(Unknown, self).shortname()
        names = s.split('.')
        names[-1] = '%s<%x>[size:0x%x]'%(names[-1], self.type, self.blocksize())
        return '.'.join(names)

class TagDef(ptype.definition):
    cache = {}
    unknown = Unknown

class Tag(pstruct.type):
    '''this wraps around a tag'''
    def autopad(self):
        total = self.blocksize() - self.getheadersize()
        used = self['data'].size()
        assert used <= total, 'invalid size specified (%d > %d)'%(used, total)
        if total >= used:
            return dyn.block(total - used)
        return Empty

    def getheadersize(self):
        return self['Header'].size() + self['HeaderLongLength'].size()

    def blocksize(self):
        size = int(self['Header']['length'])
        if size == 0x3f:
            size = int(self['HeaderLongLength'])
        return size + self.getheadersize()

    def islongheader(self):
        if self['Header']['length'] == 0x3f:
            return UI32
        return Empty

    def autotag(self, tagid, size):
        return TagDef.get(tagid, length=size)

    _fields_ = [
        (RECORDHEADER, 'Header'),
        (islongheader, 'HeaderLongLength'),
        (lambda self: self.autotag(self['Header']['type'], self.blocksize() - self.getheadersize()), 'data'),
        (autopad, 'unknown')
    ]

    def serialize(self):
        # fix up header
        tag, size = self['data'].type, self['data'].size()
        self['Header']['type'] = tag
        if size >= 0x3f:
            self['Header']['length'] = 0x3f
            self['HeaderLongLength'] = self.new(UI32).set(size)     # this creates a bad reference but whatever..
            self['HeaderLongLength'].set(size)

        return super(Tag, self).serialize()

class TagList(parray.terminated):
    _object_ = Tag

    def isTerminator(self, n):
        return type(n['data']) == End

    def __repr__(self):
        # FIXME: lol, i probably should've planned this out functionally
        result, count = [], 0
        for x in ((x['data'].shortname(),None)[issubclass(type(x['data']), Unknown)] for x in self):
            if count == 0:
                if x is None:
                    count += 1
                else:
                    result.append(x)
            elif count > 0:
                if x is None:
                    count += 1
                else:
                    s = '..(repeats %d times)..'% (count-4)
                    if count - len(s) > 0:
                        result.append(s)
                    else:
                        result.append('.'*count)
                    result.append(x)
                    count = 0
            continue
        return '%s %d records\n[%s]'%(self.name(), len(self), ','.join(result))

######## display list
@TagDef.define
class DoInitAction(pstruct.type):
    type = 59
    version = 3
    _fields_ = [
        (UI16, 'SpriteId'),
        (action.Array, 'Actions'),
    ]

@TagDef.define
class DoAction(pstruct.type):
    type = 12
    version = 3
    _fields_ = [
        (action.Array, 'Actions')
    ]

@TagDef.define
class DoABC(pstruct.type):
    type = 82
    version = 9
    _fields_ = [
        (UI32, 'Flags'),
        (STRING, 'Name'),
        (as3.abcFile, 'ABCData')
    ]

#@TagDef.define
#class PlaceObject(pstruct.type):
#    type = 4
#    version = 1
#    _fields_ = [
#        (UI16, 'CharacterId'),
#        (UI16, 'Depth'),
#        (MATRIX, 'Matrix'),
#        (CXFORM, 'ColorTransform')
#    ]

#thank you macromedia for keeping this struct a multiple of 8 bits
class _PlaceObject_Flag(pbinary.struct):
    _fields_ = [
        (1, 'HasClipActions'),
        (1, 'HasClipDepth'),
        (1, 'HasName'),
        (1, 'HasRatio'),
        (1, 'HasColorTransform'),
        (1, 'HasMatrix'),
        (1, 'HasCharacter'),
        (1, 'Move')
    ]

@TagDef.define
class PlaceObject2(pstruct.type):
    type = 26
    version = 3
    def _iff(flag, typ):
        def fn(self):
            if self['PlaceFlag'].l[flag]:
                return typ
            return Empty
        return fn

    _fields_ = [
        (_PlaceObject_Flag, 'PlaceFlag'),
        (UI16, 'Depth'),
        (_iff('HasCharacter',UI16), 'CharacterId'),
        (_iff('HasMatrix',MATRIX), 'Matrix'),
        (_iff('HasColorTransform', CXFORM), 'ColorTransform'),
        (_iff('HasRatio', UI16), 'Ratio'),
        (_iff('HasName', STRING), 'Name'),
        (_iff('HasClipDepth', UI16), 'ClipDepth'),
        (_iff('HasClipActions', CLIPACTIONS), 'ClipActions')
    ]

#thank you macromedia for keeping this struct a byte in width
class _PlaceObject3_Flag(pbinary.struct):
    _fields_ = [
        (5, 'Reserved'),
        (1, 'HasCacheAsBitmap'),
        (1, 'HasBlendMode'),
        (1, 'HasFilterList')
    ]

@TagDef.define
class PlaceObject3(pstruct.type):
    type = 70
    version = 8
    def _iff(flag, typ):
        def fn(self):
            if self['PlaceFlag'].l[flag]:
                return typ
            return Empty

        return fn

    def _iff3(flag, typ):
        def fn(self):
            if self['PlaceFlag3'].l[flag]:
                return typ
            return Empty
        return fn

    _fields_ = [
        (_PlaceObject_Flag, 'PlaceFlag'),
        (_PlaceObject3_Flag, 'PlaceFlag3'),
        (UI16, 'Depth'),
        (_iff('HasCharacter', UI16), 'CharacterId'),
        (_iff('HasMatrix',MATRIX), 'Matrix'),
        (_iff('HasColorTransform', CXFORM), 'ColorTransform'),
        (_iff('HasRatio', UI16), 'Ratio'),
        (_iff('HasName', STRING), 'Name'),
        (_iff('HasClipDepth', UI16), 'ClipDepth'),
        (_iff3('HasFilterList', FILTERLIST), 'SurfaceFilteRList'),
        (_iff3('HasBlendMode', UI8), 'BlendMode'),
        (_iff('HasClipActions', CLIPACTIONS), 'ClipActions')
    ]

@TagDef.define
class RemoveObject(pstruct.type):
    type = 5
    version = 1
    _fields_ = [
        (UI16, 'CharacterId'),
        (UI16, 'Depth')
    ]

#class RemoveObject2(pstruct.type):
#    type = 28
#    version = 3
#    _fields_ = [
#        (UI16, 'Depth')
#    ]

@TagDef.define
class ShowFrame(pstruct.type):
    type = 1
    version = 1
    _fields_ = []

######## control tags
@TagDef.define
class SetBackgroundColor(pstruct.type):
    type = 9
    version = 1
    _fields_ = [
        (RGB, 'BackgroundColor')
    ]

#@TagDef.define
#class FrameLabel(pstruct.type):
#    type = 43
#    version = 3
#    _fields_ = [
#        (STRING, 'Name')
#    ]

if False:
    @TagDef.define
    class NamedAnchor(pstruct.type):
        type = 43
        version = 6
        _fields_ = [
            (STRING, 'Name'),
            (UI8, 'NamedAnchor')
        ]

@TagDef.define
class Protect(pstruct.type):
    type = 24
    version = 2
    _fields_ = []

@TagDef.define
class End(pstruct.type):
    type = 0
    version = 1
    _fields_ = []

class _asset(pstruct.type):
    _fields_ = [
        (UI16, 'Tag'),
        (STRING, 'Name')
    ]

@TagDef.define
class ImportAssets(pstruct.type):
    type = 57
    version = 5
    _fields_ = [
        (STRING, 'URL'),
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

@TagDef.define
class ExportAssets(pstruct.type):
    type = 56
    version = 5

    _fields_ = [
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

@TagDef.define
class ImportAssets2(pstruct.type):
    type = 71
    version = 8
    _fields_ = [
        (STRING, 'URL'),
        (UI8, 'Reserved1'),
        (UI8, 'Reserved2'),
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

@TagDef.define
class EnableDebugger(pstruct.type):
    type = 58
    version = 5
    _fields_ = [
        (STRING, 'Password')
    ]

@TagDef.define
class EnableDebugger2(pstruct.type):
    type = 64
    version = 6
    _fields_ = [
        (UI16, 'Reserved'),
        (STRING, 'Password')
    ]

@TagDef.define
class ScriptLimits(pstruct.type):
    type = 65
    version = 7
    _fields_ = [
        (UI16, 'MaxRecursionDepth'),
        (UI16, 'ScriptTimeoutSeconds')
    ]

@TagDef.define
class SetTabIndex(pstruct.type):
    type = 66
    version = 7
    _fields_ = [
        (UI16, 'Depth'),
        (UI16, 'TabIndex')
    ]

@TagDef.define
class FileAttributes(pbinary.struct):
    type = 69
    version = 8
    _fields_ = [
        (3, 'Reserved1'),
        (1, 'HasMetadata'),
        (3, 'Reserved2'),
        (1, 'UseNetwork'),
        (24, 'Reserved3')
    ]

@TagDef.define
class Metadata(pstruct.type):
    type = 77
    version = 1
    _fields_ = [
        (STRING, 'Metadata')
    ]

@TagDef.define
class DefineButton2(pstruct.type):
    class __Flags(pbinary.struct):
        _fields_ = [(7,'Reserved'), (1,'TrackAsMenu')]
    type = 34
    version = 3
    _fields_ = [
        (UI16, 'ButtonId'),
        (__Flags, 'Flags'),
        (UI16, 'ActionOffset'),
        (Empty, 'incomplete')
    ]

@TagDef.define
class DefineScalingGrid(pstruct.type):
    type = 78
    version = 8
    _fields_ = [
        (UI16, 'CharacterId'),
        (RECT, 'Splitter')
    ]

@TagDef.define
class DefineShape(pstruct.type):
    type = 2
    version = 1
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')   #XXX
    ]

@TagDef.define
class DefineShape2(pstruct.type):
    type = 22
    version = 2
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')   #XXX
    ]

@TagDef.define
class DefineShape3(pstruct.type):
    type = 32
    version = 3
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')
    ]

@TagDef.define
class DefineShape4(pstruct.type):
    class __Flags(pbinary.struct):
        _fields_ = [(6,'Reserved'), (1, 'UsesNonScalingStrokes'), (1, 'UsesScalingStrokes')]

    type = 83
    version = 8
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (RECT, 'EdgeBounds'),
        (__Flags, 'Flags'),
        (Empty, 'Shapes')
    ]

@TagDef.define
class DefineSprite(pstruct.type):
    type = 39
    version = 3
    _fields_ = [
        (UI16, 'SpriteId'),
        (UI16, 'FrameCount'),
        (Empty, 'ControlTags')
    ]

@TagDef.define
class DefineBits(pstruct.type):
    type = 6
    version = 1
    _fields_ = [
        (UI16, 'CharacterID')
    ]

@TagDef.define
class DefineFont(pstruct.type):
    type = 10
    version = 1
    _fields_ = [
        (UI16, 'FontID'),
        (Empty, 'OffsetTable'),
        (Empty, 'GlyphShapeTable')
    ]

@TagDef.define
class DefineFont2(pstruct.type):
    type = 48
    version = 3
    _fields_ = [
        (UI16, 'FontID'),
        (Empty, 'incomplete')
    ]

@TagDef.define
class DefineEditText(pstruct.type):
    type = 37
    version = 4
    _fields_ = [
        (UI16, 'CharacterID'),
        (RECT, 'Bounds'),
        (Empty, 'incomplete')
    ]

@TagDef.define
class DefineFontInfo(pstruct.type):
    type = 13
    version = 1

    class __FontFlags(pbinary.struct):
        _fields_ = [
            (2, 'Reserved'), (1, 'SmallText'), (1, 'ShiftJIS'), (1, 'ANSI'),
            (1, 'Italic'), (1, 'Bold'), (1, 'WideCodes')
        ]

    def __CodeTable(self):
        nGlyphs = 0
        if self['FontFlags'].l['WideCodes']:
            return dyn.array( UI16, nGlyphs )
        return dyn.array( UI8, nGlyphs )
    
    _fields_ = [
        (UI16, 'FontID'),
        (UI8, 'FontNameLen'),
        (lambda s: dyn.clone(pstr.string,length=int(s['FontNameLen'].l)), 'FontName'),
        (__FontFlags, 'FontFlags'),
        (__CodeTable, 'CodeTable'),
    ]

class GLYPHENTRY(pbinary.struct):
    def __Index(self):
        p = self.getparent(pstruct.type)    # DefineText
        return int(p['GlyphBits'].l)
        
    def __Advance(self):
        p = self.getparent(pstruct.type)    # DefineText
        return int(p['AdvanceBits'].l)

    _fields_ = [
        (__Index, 'Index'),
        (__Advance, 'Advance'),
    ]

class TEXTRECORD(pstruct.type):
    class __StyleFlags(pbinary.struct):
        _fields_ = [
            (1, 'Type'),
            (3, 'Reserved'),
            (1, 'HasFont'),
            (1, 'HasColor'),
            (1, 'HasYOffset'),
            (1, 'HasXOffset'),
        ]
    import tags
    def __TextColor(self):
        if int(self['StyleFlags'].l['HasColor']):
            try:
                self.getparent(DefineText2)
            except ValueError:
                return RGB
            return RGBA
        return Empty

    __FontID = lambda s: [Empty, UI16][ int(s['StyleFlags'].l['HasFont']) ]
    __XOffset = lambda s: [Empty, SI16][ int(s['StyleFlags']['HasXOffset']) ]
    __YOffset = lambda s: [Empty, SI16][ int(s['StyleFlags']['HasYOffset']) ]
    __TextHeight = lambda s: [Empty, UI16][ int(s['StyleFlags']['HasFont']) ]

    _fields_ = [
        (__StyleFlags, 'StyleFlags'),
        (__FontID, 'FontID'),
        (__TextColor, 'TextColor'),
        (__XOffset, 'XOffset'),
        (__YOffset, 'YOffset'),
        (__TextHeight, 'TextHeight'),
        (UI8, 'GlyphCount'),
        (lambda s: dyn.clone(pbinary.array, _object_=GLYPHENTRY,length=int(s['GlyphCount'].l)), 'GlyphEntries'),
    ]

@TagDef.define
class DefineText(pstruct.type):
    type = 11
    version = 1

    class __TextRecords(parray.terminated):
        _object_ = TEXTRECORD
        def isTerminator(self, value):
            if value.serialize()[0] == 0:
                return True
            return False

    _fields_ = [
        (UI16, 'CharacterID'),
        (RECT, 'TextBounds'),
        (MATRIX, 'TextMatrix'),
        (UI8, 'GlyphBits'),
        (UI8, 'AdvanceBits'),
#        (__TextRecords, 'TextRecord')
    ]

class DefineText2(DefineText):
    type = 33
    version = 3

@TagDef.define
class JPEGTables(pstruct.type):
    type = 8
    version = 1
    _fields_ = []   # XXX: the rest of the tag contains the JET

@TagDef.define
class FileAttributes(pbinary.struct):
    version = 8
    type = 69
    _fields_ = [
        (1, 'Reserved[0]'),
        (1, 'UseDirectBlit'),
        (1, 'UseGPU'),
        (1, 'HasMetadata'),
        (1, 'ActionScript3'),
        (2, 'Reserved'),
        (1, 'UseNetwork'),
        (24, 'Reserved[7]'),
    ]

if False:
    @TagDef.define
    class DefineSceneAndFrameLabelData(pstruct.type):
        type = 86
        class Scene(pstruct.type):
            _fields_ = [
                (as3.u32, 'Name'),
                (STRING, 'Offset'),
            ]
        class Frame(pstruct.type):
            _fields_ = [
                (as3.u32, 'Num'),
                (STRING, 'Label'),
            ]

        _fields_ = [
            (as3.u32, 'SceneCount'),
            (lambda s: dyn.array(s.Scene, int(s['SceneCount'].l)), 'Scene'),
            (as3.u32, 'FrameLabelCount'),
            (lambda s: dyn.array(s.Frame, int(s['FrameLabelCount'].l)), 'Scene'),
        ]

##############################################
def istype(obj):
    return type(obj) == type(int)
