import logging,ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

import stypes
from stypes import *
import as3,action

class Unknown(ptype.type):
    def classname(self):
        s = self.typename()
        names = s.split('.')
        names[-1] = '%s<%x>[size:0x%x]'%(names[-1], self.type, self.blocksize())
        return '.'.join(names)

class TagDef(ptype.definition):
    cache = {}
    unknown = Unknown

class Tag(pstruct.type):
    '''this wraps around a tag'''
    def __unknown(self):
        total = self.blocksize() - (self['Header'].size() + self['HeaderLongLength'].size())
        used = self['data'].size()
        if used > total:
            logging.warning('invalid size specified (%d > %d) : %s'%(used, total, self['data'].classname()))
            return Empty
        return dyn.block(total - used)

    def blocksize(self):
        res = self['Header']['Length'] if self['Header'].li['Length'] < 0x3f else self['HeaderLongLength'].li.num()
        return res + self['Header'].size() + self['HeaderLongLength'].size()

    def __HeaderLongLength(self):
        return UI32 if self['Header'].li['Length'] == 0x3f else pint.uint_t

    _fields_ = [
        (RECORDHEADER, 'Header'),
        (__HeaderLongLength, 'HeaderLongLength'),
        (lambda s: TagDef.get(s['Header'].li['Type'], length=s.blocksize()-(s['Header'].size()+s['HeaderLongLength'].size())), 'data'),
        (__unknown, 'unknown')
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

    def summary(self):
        # FIXME: lol, i probably should've planned this out functionally
        result, count = [], 0
        for x in ((x['data'].classname(),None)[issubclass(type(x['data']), Unknown)] for x in self):
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
        return '%d records\n[%s]'%(len(self), ','.join(result))

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

@TagDef.define
class PlaceObject(pstruct.type):
    type = 4
    version = 1

    def __ColorTransform(self):
        bs = self.p.blocksize() - self.p.size()
        raise NotImplementedError
        return CXFORM

    _fields_ = [
        (UI16, 'CharacterId'),
        (UI16, 'Depth'),
        (MATRIX, 'Matrix'),
        (__ColorTransform, 'ColorTransform')
    ]

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
            if self['PlaceFlag'].li[flag]:
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
            if self['PlaceFlag'].li[flag]:
                return typ
            return Empty

        return fn

    def _iff3(flag, typ):
        def fn(self):
            if self['PlaceFlag3'].li[flag]:
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

@TagDef.define
class RemoveObject2(pstruct.type):
    type = 28
    version = 3
    _fields_ = [
        (UI16, 'Depth')
    ]

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

@TagDef.define
class FrameLabel(pstruct.type):
    type = 43
    version = 3
    _fields_ = [
        (STRING, 'Name')
    ]

@TagDef.define
class StartSound(pstruct.type):
    version = 1
    type = 15

    _fields_ = [
        (UI16, 'SoundId'),
        (SOUNDINFO, 'SoundInfo'),
    ]

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
        (lambda s: dyn.array(_asset, s['Count'].li.num()), 'Asset')
    ]

@TagDef.define
class ExportAssets(pstruct.type):
    type = 56
    version = 5

    _fields_ = [
        (UI16, 'Count'),
        (lambda s: dyn.array(_asset, s['Count'].li.num()), 'Asset')
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
        (lambda s: dyn.array(_asset, s['Count'].li.num()), 'Asset')
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
        #(Empty, 'Shapes')   #XXX
        (SHAPEWITHSTYLE, 'Shapes')
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
        (Empty, 'Shapes')   # XXX
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
        (Empty, 'Shapes')   # XXX
    ]

@TagDef.define
class DefineSprite(pstruct.type):
    type = 39
    version = 3

    class __ControlTags(TagList):
        allowed = (ShowFrame,
            PlaceObject, PlaceObject2, RemoveObject, RemoveObject2,
            StartSound, FrameLabel,
#            SoundStreamHead, SoundStreamHead2, SoundStreamBlock,   # FIXME
            End)

    _fields_ = [
        (UI16, 'SpriteId'),
        (UI16, 'FrameCount'),
        (__ControlTags, 'ControlTags')
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
        if self['FontFlags'].li['WideCodes']:
            return dyn.array( UI16, nGlyphs )
        return dyn.array( UI8, nGlyphs )

    _fields_ = [
        (UI16, 'FontID'),
        (UI8, 'FontNameLen'),
        (lambda s: dyn.clone(pstr.string,length=s['FontNameLen'].li.num()), 'FontName'),
        (__FontFlags, 'FontFlags'),
        (__CodeTable, 'CodeTable'),
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

@TagDef.define
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

@TagDef.define
class SymbolClass(pstruct.type):
    version = 9
    type = 76

    class Symbol(pstruct.type):
        _fields_ = [(UI16, 'Tag'),(STRING,'Name')]

    _fields_ = [
        (UI16, 'NumSymbols'),
        (lambda s:dyn.array(s.Symbol, s['NumSymbols'].li.int()), 'Symbols')
    ]

## XXX font stuff
@TagDef.define
class DefineFont(Empty):
    version = 1
    type = 10

@TagDef.define
class DefineFontInfo(Empty):
    version = 1
    type = 13

@TagDef.define
class DefineFont2(Empty):
    version = 3
    type = 48

@TagDef.define
class DefineFontInfo2(Empty):
    version = 6
    type = 62

@TagDef.define
class DefineFont3(Empty):
    version = 8
    type = 75

@TagDef.define
class DefineFontAlignZones(Empty):
    version = 8
    type = 73

@TagDef.define
class DefineSceneAndFrameLabelData(pstruct.type):
    type = 86
    class Scene(pstruct.type):
        _fields_ = [
            (as3.u32, 'Offset'),
            (STRING, 'Name'),
        ]
    class Frame(pstruct.type):
        _fields_ = [
            (as3.u32, 'Num'),
            (STRING, 'Label'),
        ]

    _fields_ = [
        (as3.u32, 'SceneCount'),
        (lambda s: dyn.array(s.Scene, s['SceneCount'].li.num()), 'Scene'),
        (as3.u32, 'FrameLabelCount'),
        (lambda s: dyn.array(s.Frame, s['FrameLabelCount'].li.num()), 'Frame'),
    ]

@TagDef.define
class DefineBinaryData(pstruct.type):
    type = 87
    def __data(self):
        sz = self.p.blocksize() - self.p.size()
        return dyn.block(sz - 6)

    _fields_ = [
        (UI16, 'characterId'),
        (UI32, 'reserved'),
        (__data, 'data'),
    ]

##############################################
def istype(obj):
    return type(obj) == type(int)

if __name__ == '__main__':
    import logging
#    logging.root=logging.RootLogger(logging.DEBUG)

    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)
                raise Failure
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
            import traceback
            traceback.print_exc()
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes,tags,stypes
    from ptypes import *

    @TestCase
    def test_DefineShape_load():
        s = '\xbf\x00$\x00\x00\x00\x01\x00`\x002\x00\x00\r\xc0\x01\x00\xff\xff\xff\x01\x01\x00\x00\x00\x00\x115\x8c\x807\x1fD\xe0p\xc9\x1d\x0c\x81\xc2\xdc\x00'
        ptypes.setsource( prov.string(s) )
        a = tags.Tag()
        a = a.l
        b = a['data']
        print b
        print b['shapeid']
        print b['shapebounds']
        print b['shapes']

    @TestCase
    def test_SHAPEWITHSTYLE_load():
        global a
        s = '\x01\x00\xff\xff\xff\x01\x01\x00\x00\x00\x00\x115\x8c\x807\x1fD\xe0p\xc9\x1d\x0c\x81\xc2\xdc\x00'
        print repr(s[0xc:])
        ptypes.setsource( prov.string(s) )
        a = stypes.SHAPEWITHSTYLE()
        a = a.l
        print a.v
        #print a['fillstyles']['fillstyles'][0]
        #print a['linestyles']['linestyles'][0]
        #print a['numbits']
        print a['ShapeRecords'][0]
        print a['shaperecords']
        print a['shaperecords'][0]
        print a['shaperecords'][0]['Shape']

    def test_wtf():
        class fuck(pbinary.struct):
            _fields_ = [(1,'whut'), (1, 'whut2'), (2,'whut3')]

        a = fuck()
        print a.a
        print a.v[0]
        print a.v[0].bits()
        print a.v[0].getposition()
        print a.v[1]
        print a.v[1].bits()
        print a.v[1].getposition()

    @TestCase
    def test_abc():
        data = '\xbf\x14\xe5\x03\x00\x00\x01\x00\x00\x00\x00\x10\x00.\x00\x00\x00\x00"\x00\x04void\x07mx.core\nIFlexAsset\x0eByteArrayAsset\x0bflash.utils\tByteArray\x16mx.core:ByteArrayAsset\x08test_fla\x1aMainTimeline_Testinputsets#test_fla:MainTimeline_Testinputsets\x0cMainTimeline\rflash.display\tMovieClip\x15test_fla:MainTimeline\rTestinputsets\x05Class\x07loadres\x06frame1*http://www.adobe.com/2006/flex/mx/internal\x07VERSION\x06String\x073.0.0.0\x0bmx_internal\x06Object\tshareable\x0eaddFrameScript\x0cflash.events\x0fEventDispatcher\rDisplayObject\x11InteractiveObject\x16DisplayObjectContainer\x06Sprite\x0c\x16\x01\x16\x03\x16\x06\x18\x08\x16\t\x18\x0b\x16\r\x18\x0f\x17\t\x08\x14\x16\x1c\x03\x01\x02\x01\x05\x1a\x07\x01\x02\x07\x02\x04\x07\x02\x05\x07\x03\x07\t\x04\x01\x07\x05\n\x07\x05\x0c\x07\x07\x0e\x07\x01\x10\x07\x01\x11\x07\x01\x12\x07\t\x13\x07\n\x15\x07\x01\x16\x07\x02\x18\t\x05\x01\x07\x01\x19\t\n\x02\x07\x01\x1a\x07\x01\x1b\x07\x0b\x1d\x07\x07\x1e\x07\x07\x1f\x07\x07 \x07\x07!\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x05\x00\x02\x00\x03\x04\t\x04\x01\x05\x05\x00\x06\x03\t\x06\x00\x08\x00\x07\x08\x08\x08\x00\r\x03\t\x00\x00\n\x00\x0b\x01\x00\x0b\x0c\x01\x00\x0c\x01\x00\x04\x01\r\x06\x01\x0e\x17\x01\x07\x00\n\x00\x05\x00\x01\x0f\x06\x00\x00\n\x08\x03\x01\x02\x04\x00\x00\x06\x01\x03\x04\x00\x01\t\x01\x06\x04\x00\x02\x0e\x01\x07\x04\x01\x03\x0e\x00\x01\x01\x01\x02\x03\xd00G\x00\x00\x01\x00\x01\x03\x03\x01G\x00\x00\x03\x02\x01\x01\x02\n\xd00]\x05 X\x00h\x02G\x00\x00\x04\x02\x01\x04\x05\t\xd00^\r,\x17h\rG\x00\x00\x05\x01\x01\x05\x06\x06\xd00\xd0I\x00G\x00\x00\x06\x02\x01\x01\x04\x13\xd00]\x10`\x110`\x040`\x04X\x01\x1d\x1dh\x03G\x00\x00\x07\x01\x01\x05\x06\x03\xd00G\x00\x00\x08\x01\x01\x06\x07\x06\xd00\xd0I\x00G\x00\x00\t\x02\x01\x01\x05\x17\xd00]\x12`\x110`\x040`\x030`\x03X\x02\x1d\x1d\x1dh\x06G\x00\x00\n\x01\x01\t\n\x03\xd00G\x00\x00\x0b\x02\x02\n\x0b\x0e\xd00\xd0J\t\x00\x80\x04\xd5\xd1&a\x13G\x00\x00\x0c\x01\x01\n\x0b\x07\xd00\xd0O\x0b\x00G\x00\x00\r\x03\x01\n\x0b\x15\xd00\xd0`\x06h\t\xd0I\x00]\x14$\x00\xd0f\x0cO\x14\x02G\x00\x00\x0e\x02\x01\x01\t\'\xd00e\x00`\x110`\x150`\x160`\x170`\x180`\x190`\x080`\x08X\x03\x1d\x1d\x1d\x1d\x1d\x1d\x1dh\x07G\x00\x00'
        ptypes.setsource( prov.string(data) )

        a = tags.Tag()
        a = a.l
        print a['data']['ABCData']

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
