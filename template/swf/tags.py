from ptypes import *
from stypes import *
import as3,action

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
        global Taglookup
        try:
            res = Taglookup[tagid]

        except KeyError:
            res = createUnknown(tagid, size)
        return res

    _fields_ = [
        (RECORDHEADER, 'Header'),
        (islongheader, 'HeaderLongLength'),
        (lambda self: self.autotag(self['Header']['type'], self.blocksize() - self.getheadersize()), 'data'),
        (autopad, 'unknown')
    ]

    def serialize(self):
        # fix up header
        tag, size = self['data'].tag, self['data'].size()
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

class SWFT(object):
    '''all tags are derived from this class'''
    tag = None

class TagS(pstruct.type, SWFT):
    pass

class TagB(pbinary.struct, SWFT):
    pass

######## display list
class Unknown(ptype.type):
    def shortname(self):
        s = super(Unknown, self).shortname()
        names = s.split('.')
        names[-1] = '%s<%x>[size:0x%x]'%(names[-1], self.tag, self.blocksize())
        return '.'.join(names)

def createUnknown(tagid, size):
    class _Unknown(Unknown):
        tag = tagid
        length = size
    return _Unknown

class DoInitAction(TagS):
    tag = 59
    version = 3
    _fields_ = [
        (UI16, 'SpriteId'),
        (action.Array, 'Actions'),
    ]

class DoAction(TagS):
    tag = 12
    version = 3
    _fields_ = [
        (action.Array, 'Actions')
    ]

class DoABC(TagS):
    tag = 82
    version = 9
    _fields_ = [
        (UI32, 'Flags'),
        (STRING, 'Name'),
        (as3.abcFile, 'ABCData')
    ]

#class PlaceObject(TagS):
#    tag = 4
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

class PlaceObject2(TagS):
    tag = 26
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

class PlaceObject3(TagS):
    tag = 70
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

class RemoveObject(TagS):
    tag = 5
    version = 1
    _fields_ = [
        (UI16, 'CharacterId'),
        (UI16, 'Depth')
    ]

#class RemoveObject2(TagS):
#    tag = 28
#    version = 3
#    _fields_ = [
#        (UI16, 'Depth')
#    ]

class ShowFrame(TagS):
    tag = 1
    version = 1
    _fields_ = []

######## control tags
class SetBackgroundColor(TagS):
    tag = 9
    version = 1
    _fields_ = [
        (RGB, 'BackgroundColor')
    ]

#class FrameLabel(TagS):
#    tag = 43
#    version = 3
#    _fields_ = [
#        (STRING, 'Name')
#    ]

if False:
    class NamedAnchor(TagS):
        tag = 43
        version = 6
        _fields_ = [
            (STRING, 'Name'),
            (UI8, 'NamedAnchor')
        ]

class Protect(TagS):
    tag = 24
    version = 2
    _fields_ = []

class End(TagS):
    tag = 0
    version = 1
    _fields_ = []

class _asset(pstruct.type):
    _fields_ = [
        (UI16, 'Tag'),
        (STRING, 'Name')
    ]

class ImportAssets(TagS):
    tag = 57
    version = 5
    _fields_ = [
        (STRING, 'URL'),
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

class ExportAssets(TagS):
    tag = 56
    version = 5

    _fields_ = [
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

class ImportAssets2(TagS):
    tag = 71
    version = 8
    _fields_ = [
        (STRING, 'URL'),
        (UI8, 'Reserved1'),
        (UI8, 'Reserved2'),
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, int(s['Count'].l)), 'Asset')
    ]

class EnableDebugger(TagS):
    tag = 58
    version = 5
    _fields_ = [
        (STRING, 'Password')
    ]

class EnableDebugger2(TagS):
    tag = 64
    version = 6
    _fields_ = [
        (UI16, 'Reserved'),
        (STRING, 'Password')
    ]

class ScriptLimits(TagS):
    tag = 65
    version = 7
    _fields_ = [
        (UI16, 'MaxRecursionDepth'),
        (UI16, 'ScriptTimeoutSeconds')
    ]

class SetTabIndex(TagS):
    tag = 66
    version = 7
    _fields_ = [
        (UI16, 'Depth'),
        (UI16, 'TabIndex')
    ]

class FileAttributes(TagB):
    tag = 69
    version = 8
    _fields_ = [
        (3, 'Reserved1'),
        (1, 'HasMetadata'),
        (3, 'Reserved2'),
        (1, 'UseNetwork'),
        (24, 'Reserved3')
    ]

class Metadata(TagS):
    tag = 77
    version = 1
    _fields_ = [
        (STRING, 'Metadata')
    ]

class DefineButton2(TagS):
    class __Flags(pbinary.struct):
        _fields_ = [(7,'Reserved'), (1,'TrackAsMenu')]
    tag = 34
    version = 3
    _fields_ = [
        (UI16, 'ButtonId'),
        (__Flags, 'Flags'),
        (UI16, 'ActionOffset'),
        (Empty, 'incomplete')
    ]

class DefineScalingGrid(TagS):
    tag = 78
    version = 8
    _fields_ = [
        (UI16, 'CharacterId'),
        (RECT, 'Splitter')
    ]

class DefineShape(TagS):
    tag = 2
    version = 1
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')   #XXX
    ]

class DefineShape2(TagS):
    tag = 22
    version = 2
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')   #XXX
    ]

class DefineShape3(TagS):
    tag = 32
    version = 3
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (Empty, 'Shapes')
    ]

class DefineShape4(TagS):
    class __Flags(pbinary.struct):
        _fields_ = [(6,'Reserved'), (1, 'UsesNonScalingStrokes'), (1, 'UsesScalingStrokes')]

    tag = 83
    version = 8
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (RECT, 'EdgeBounds'),
        (__Flags, 'Flags'),
        (Empty, 'Shapes')
    ]

class DefineSprite(TagS):
    tag = 39
    version = 3
    _fields_ = [
        (UI16, 'SpriteId'),
        (UI16, 'FrameCount'),
        (Empty, 'ControlTags')
    ]

class DefineBits(TagS):
    tag = 6
    version = 1
    _fields_ = [
        (UI16, 'CharacterID')
    ]

class DefineFont(TagS):
    tag = 10
    version = 1
    _fields_ = [
        (UI16, 'FontID'),
        (Empty, 'OffsetTable'),
        (Empty, 'GlyphShapeTable')
    ]

class DefineFont2(TagS):
    tag = 48
    version = 3
    _fields_ = [
        (UI16, 'FontID'),
        (Empty, 'incomplete')
    ]

class DefineEditText(TagS):
    tag = 37
    version = 4
    _fields_ = [
        (UI16, 'CharacterID'),
        (RECT, 'Bounds'),
        (Empty, 'incomplete')
    ]

class DefineFontInfo(TagS):
    tag = 13
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
        p = self.getparent(TagS)    # DefineText
        return int(p['GlyphBits'].l)
        
    def __Advance(self):
        p = self.getparent(TagS)    # DefineText
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

class DefineText(TagS):
    tag = 11
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
    tag = 33
    version = 3

class JPEGTables(TagS):
    tag = 8
    version = 1
    _fields_ = []   # XXX: the rest of the tag contains the JET

class FileAttributes(TagB):
    version = 8
    tag = 69
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
    class DefineSceneAndFrameLabelData(TagS):
        tag = 86
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

classes = [ n for n in locals().values() if istype(n) ]
Tags = [ n for n in classes if issubclass(n, SWFT) ]
Taglookup = dict([ (n.tag, n) for n in Tags ])
