from ptypes import *
from stypes import *

def CBinary(iterable):
    iter(iterable)

    class _CBinary(pBinary):
        _fields_ = list(iterable)

    return _CBinary()

class Tag(pStruct):
    '''this wraps around a tag'''
    def autopad(self):
        size = int(self['Header']['length'])
        if size == 0x3f:
            assert 'HeaderLongLength' in self.keys()
            size = int(self['HeaderLongLength'])

        used = self['data'].size()
        assert used <= size, 'invalid size specified (%d > %d)'%(used, size)
        if size >= used:
            return dyn.block(size - used)()
        return Empty()

    def islongheader(self):
        if self['Header']['length'] == 0x3f:
            return UI32()
        return Empty()

    _fields_ = [
        (RECORDHEADER, 'Header'),
        (islongheader, 'HeaderLongLength'),
        (lambda self: autotag(self['Header']['type'])(), 'data'),
        (autopad, 'unknown')
    ]

    def serialize(self, iterable):
        iterable = iter(iterable)

        # fix up header
        tag, size = self['data'].tag, self['data'].size()
        self['Header']['type'] = tag
        if size >= 0x3f:
            self['Header']['length'] = 0x3f
            self['HeaderLongLength'] = size

        return super(Tag, self).serialize()

class TagList(pTerminatedArray):
    _object_ = Tag
    length = 0

    def isTerminator(self, n):
        return type(n['data']) == End

class SWFT(object):
    '''all tags are derived from this class'''
    tag = None

class TagS(pStruct, SWFT):
    pass

class TagB(pBinary, SWFT):
    pass

######## display list
class Unknown(pType):
    def __repr__(self):
        return "%s tagid: %d"%(self.__class__, self.tag);

def createUnknown(tagid):
    class _Unknown(Unknown):
        tag = tagid
    return _Unknown

class DoInitAction(TagS):
    tag = 59
    version = 3
    _fields_ = [
        (UI16, 'SpriteId'),
        (Empty, 'Actions')
    ]

class DoAction(TagS):
    tag = 12
    version = 3
    _fields_ = [
        (Empty, 'Actions')
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
class _PlaceObject_Flag(pBinary):
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
            if self['PlaceFlag'][flag]:
                return typ()
            return Empty()
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
class _PlaceObject3_Flag(pBinary):
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
            if self['PlaceFlag'][flag]:
                return typ()
            return Empty()

        return fn

    def _iff3(flag, typ):
        def fn(self):
            if self['PlaceFlag3'][flag]:
                return typ()
            return Empty()
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
    _fields = []

class End(TagS):
    tag = 0
    version = 1
    _fields_ = []

if False:
    class ExportAssets(TagS):
        tag = 56
        version = 5
        _fields_ = [
            (UI16, 'Count')
        ]

        _looped_ = [
            (UI16, 'Tag%d'),
            (STRING, 'Name%d')
        ]

        def deserialize(self, iterable):
            iterable = iter(iterable)

            def extend(num):
                for typ,name in self._looped_:
                    self._fields_.append( (typ,name%num) )

            self['Count'].deserialize(iterable)

            for n in range( int(self['Count']) ):
                extend(n)

            self.alloc()
            for typ,name in self._fields_[1:]:
                self[name].deserialize(iterable)

if False:
    class ImportAssets(TagS):
        tag = 57
        version = 5
        _fields_ = [
            (STRING, 'URL'),
            (UI16, 'Count')
        ]

        _looped_ = [
            (UI16, 'Tag%d'),
            (STRING, 'Name%d')
        ]

        def deserialize(self, iterable):
            iterable = iter(iterable)

            def extend(num):
                for typ,name in self._looped_:
                    self._fields_.append( (typ,name%num) )

            self['Count'].deserialize(iterable)
            for n in range( int(self['Count']) ):
                extend(n)

            for typ,name in self._fields_[2:]:
                self[name].deserialize(iterable)


class _asset(pStruct):
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
        (dyn.array( _asset, 'Count' ), 'Asset')        
    ]

class ExportAssets(TagS):
    tag = 56
    version = 5

    _fields_ = [
        (UI16, 'Count'),
        (dyn.array( _asset, 'Count'), 'Asset')
    ]

class ImportAssets2(TagS):
    tag = 71
    version = 8
    _fields_ = [
        (STRING, 'URL'),
        (UI8, 'Reserved1'),
        (UI8, 'Reserved2'),
        (UI16, 'Count'),
        (dyn.array(_asset, 'Count'), 'Asset')
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
    tag = 34
    version = 3
    _fields_ = [
        (UI16, 'ButtonId'),
        ( CBinary([(7,'Reserved'), (1,'TrackAsMenu')]), 'Flags'),
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
    tag = 83
    version = 8
    _fields_ = [
        (UI16, 'ShapeId'),
        (RECT, 'ShapeBounds'),
        (RECT, 'EdgeBounds'),
        (CBinary([(6,'Reserved'), (1, 'UsesNonScalingStrokes'), (1, 'UsesScalingStrokes')]), 'Flags'), (Empty, 'Shapes')
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

class JPEGTables(TagS):
    tag = 8
    version = 1
    _fields_ = []   # XXX: the rest of the tag contains the JET

##############################################
def istype(obj):
    return type(obj) == type(int)

classes = [ n for n in locals().values() if istype(n) ]
Tags = [ n for n in classes if issubclass(n, SWFT) ]
Taglookup = dict([ (n.tag, n) for n in Tags ])

def autotag(tagid):
    try:
        res = Taglookup[tagid]

    except KeyError:
        res = createUnknown(tagid)
    return res
