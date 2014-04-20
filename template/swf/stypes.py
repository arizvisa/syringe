from primitives import *

class ShapeDefinition(ptype.boundary): pass

def _ifelse(field, t, f):
    def fn(self):
        if self[field]:
            return t
        return f
    return fn

def _ifeq(field, value, t, f):
    def fn(self):
        if int(self[field]) == value:
            return t
        return f
    return fn

class RECORDHEADER(pbinary.struct):
    _fields_ = [
        (10, 'type'),
        (6, 'length')
    ]
RECORDHEADER = pbinary.littleendian(RECORDHEADER)

class RGB(pstruct.type):
    _fields_ = [
        (UI8, 'Red'),
        (UI8, 'Green'),
        (UI8, 'Blue')
    ]

class RGBA(pstruct.type):
    _fields_ = [
        (UI8, 'Red'),
        (UI8, 'Green'),
        (UI8, 'Blue'),
        (UI8, 'Alpha')
    ]

class ARGB(pstruct.type):
    _fields_ = [
        (UI8, 'Alpha'),
        (UI8, 'Red'),
        (UI8, 'Green'),
        (UI8, 'Blue')
    ]

class LANGCODE(UI8):
    pass

####
class RECT(pbinary.struct):
    _fields_ = [
        (5, 'Nbits'),
        (lambda self: self['Nbits'], 'Xmin'),
        (lambda self: self['Nbits'], 'Xmax'),
        (lambda self: self['Nbits'], 'Ymin'),
        (lambda self: self['Nbits'], 'Ymax')
    ]

class MATRIX(pbinary.struct):
    def _ifelse(field, t, f):
        def fn(self):
            if self[field]:
                return t
            return f
        return fn

    _fields_ = [
        (1, 'HasScale'),
        (_ifelse('HasScale', 5, 0), 'NScaleBits'),
        (lambda self: self['NScaleBits'], 'ScaleX'),
        (lambda self: self['NScaleBits'], 'ScaleY'),

        (1, 'HasRotate'),
        (_ifelse('HasRotate', 5, 0), 'NRotateBits'),
        (lambda self: self['NRotateBits'], 'RotateSkew0'),
        (lambda self: self['NRotateBits'], 'RotateSkew1'),

        (5, 'NTranslateBits'),
        (lambda self: self['NTranslateBits'], 'TranslateX'),
        (lambda self: self['NTranslateBits'], 'TranslateY')
    ]

#### text records
class GLYPHENTRY(pbinary.struct):
    def __Index(self):
        p = self.getparent(pstruct.type)    # DefineText
        return p['GlyphBits'].l.num()
        
    def __Advance(self):
        p = self.getparent(pstruct.type)    # DefineText
        return p['AdvanceBits'].l.num()

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

###
class _CLIPEVENTFLAGS_Events(pbinary.struct):
    _fields_ = [
        (1, 'ClipEventKeyUp'),   
        (1, 'ClipEventKeyDown'),   
        (1, 'ClipEventMouseUp'),   
        (1, 'ClipEventMouseDown'),   
        (1, 'ClipEventMouseMove'),   
        (1, 'ClipEventUnload'),   
        (1, 'ClipEventEnterFrame'),
        (1, 'ClipEventLoad'),
        (1, 'ClipEventDragOver'),
        (1, 'ClipEventRollOut'),
        (1, 'ClipEventRollOver'),
        (1, 'ClipEventReleaseOutside'),

        (1, 'ClipEventRelease'),
        (1, 'ClipEventPress'),
        (1, 'ClipEventInitialize'),
        (1, 'ClipEventData'),
    ]

class _CLIPEVENTFLAGS6_Events(pbinary.struct):
    _fields_ = [
        (5, 'Reserved'),
        (1, 'ClipEventConstruct'),
        (1, 'ClipEventKeyPress'),
        (1, 'ClipEventDragOut'),
        (8, 'Reserved')
    ]

class CLIPEVENTFLAGS(pstruct.type):
    def _ifver(version, typ):
        return typ

    _fields_ = [
        (_CLIPEVENTFLAGS_Events, 'Events'),
        (_ifver(6, _CLIPEVENTFLAGS6_Events), 'Events6')
    ]
    
class CXFORM(pbinary.struct):
    '''fuck you swf'''
    _fields_ = [
        (1, 'HasAddTerms'),
        (1, 'HasMultTerms'),
        (4, 'Nbits'),
    
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'RedMultTerm'),
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'GreenMultTerm'),
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'BlueMultTerm'),

        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'RedAddTerm'),
        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'GreenAddTerm'),
        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'BlueAddTerm'),
    ]

class CXFORMWITHALPHA(pbinary.struct):
    '''fuck you swf'''
    _fields_ = [
        (1, 'HasAddTerms'),
        (1, 'HasMultTerms'),
        (4, 'Nbits'),
    
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'RedMultTerm'),
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'GreenMultTerm'),
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'BlueMultTerm'),
        (lambda self: _ifelse('HasMultTerms', self['Nbits'], 0), 'AlphaMultTerm'),

        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'RedAddTerm'),
        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'GreenAddTerm'),
        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'BlueAddTerm'),
        (lambda self: _ifelse('HasAddTerms', self['Nbits'], 0), 'AlphaAddTerm'),
    ]

### filters
class _DROPSHADOWFILTER_Flags(pbinary.struct):
    _fields_ = [
        (1, 'InnerShadow'),
        (1, 'KnockOut'),
        (1, 'CompositeSource'),
        (5, 'Passes')
    ]

class DROPSHADOWFILTER(pstruct.type):
    _fields_ = [
        (RGBA, 'DropShadowColor'),
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (FIXED, 'Angle'),
        (FIXED, 'Distance'),
        (FIXED8, 'Strength'),
        (_DROPSHADOWFILTER_Flags, 'Flags')
    ]

###
class _BLURFILTER_Flags(pbinary.struct):
    _fields_ = [
        (5, 'Passes'),
        (3, 'Reserved')
    ]

class BLURFILTER(pstruct.type):
    _fields_ = [
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (_BLURFILTER_Flags, 'Flags')
    ]

###
class _GLOWFILTER_Flags(_DROPSHADOWFILTER_Flags):
    pass

class GLOWFILTER(pstruct.type):
    _fields_ = [
        (RGBA, 'GlowColor'),
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (FIXED8, 'Strength'),
        (_GLOWFILTER_Flags, 'Flags')
    ]

###
class _BEVELFILTER_Flags(pbinary.struct):
    _fields_ = [
        (1, 'InnerShadow'),
        (1, 'KnockOut'),
        (1, 'CompositeSource'),
        (1, 'OnTop'),
        (4, 'Passes')
    ]

class BEVELFILTER(pstruct.type):
    _fields_ = [
        (RGBA, 'ShadowColor'),
        (RGBA, 'HighlightColor'),
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (FIXED, 'Angle'),
        (FIXED, 'Distance'),
        (FIXED8, 'Strength'),
        (_BEVELFILTER_Flags, 'Flags')
    ]

###
class _GRADIENTGLOWFILTER_Flags(_BEVELFILTER_Flags):
    pass

class GRADIENTGLOWFILTER(pstruct.type):
    _fields_ = [
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (FIXED, 'Angle'),
        (FIXED, 'Distance'),
        (FIXED8, 'Strength'),
        (_GRADIENTGLOWFILTER_Flags, 'Flags')
    ]

###
class _CONVOLUTIONFILTER_Flags(pbinary.struct):
    _fields_ = [
        (6, 'Reserved'),
        (1, 'Clamp'),
        (1, 'PreserveAlpha')
    ]

class CONVOLUTIONFILTER(pstruct.type):
    _fields_ = [
        (UI8, 'MatrixX'),
        (UI8, 'MatrixY'),
        (FLOAT, 'Divisor'),
        (FLOAT, 'Bias'),
        (lambda self: dyn.array(FLOAT, self['MatrixX']*self['MatrixY'])(), 'Matrix'),
        (RGBA, 'DefaultColor'),
        (_CONVOLUTIONFILTER_Flags, 'Flags')
    ]

###
class COLORMATRIXFILTER(parray.type):
    _object_ = FLOAT
    length = 20

###
class _GRADIENTBEVELFILTER_Flags(pbinary.struct):
    _fields_ = [
        (1, 'InnerShadow'),
        (1, 'KnockOut'),
        (1, 'CompositeSource'),
        (1, 'OnTop'),
        (4, 'Passes'),
    ]

class GRADIENTBEVELFILTER(pstruct.type):
    _fields_ = [
        (UI8, 'NumColors'),
        (lambda self: dyn.array(RGBA, self['NumColors'])(), 'Gradientcolors'),
        (lambda self: dyn.array(UI8, self['NumColors'])(), 'GradientRatio'),
        (FIXED, 'BlurX'),
        (FIXED, 'BlurY'),
        (FIXED, 'Angle'),
        (FIXED, 'Distance'),
        (FIXED8, 'Strength'),
        (_GRADIENTBEVELFILTER_Flags, 'Flags')
    ]

### XXX filters
class FILTER(pstruct.type):
    def _iff(field, value, typ):
        def fn(self):
            if self[field] == value:
                return ty
            return Empty
        return fn

    _fields_ = [
        (UI8, 'FilterID'),
        (_iff('FilterID', 0, DROPSHADOWFILTER), 'DropShadowFilter'),
        (_iff('FilterID', 1, BLURFILTER), 'BlurFilter'),
        (_iff('FilterID', 2, GLOWFILTER), 'GlowFilter'),
        (_iff('FilterID', 3, BEVELFILTER), 'BevelFilter'),
        (_iff('FilterID', 4, GRADIENTGLOWFILTER), 'GradientGlowFilter'),
        (_iff('FilterID', 5, CONVOLUTIONFILTER), 'ConvolutionFilter'),
        (_iff('FilterID', 6, COLORMATRIXFILTER), 'ColorMatrixFilter'),
        (_iff('FilterID', 7, GRADIENTBEVELFILTER), 'GradientBevelFilter')
    ]

class FILTERLIST(pstruct.type):
    _fields_ = [
        (UI8, 'NumberOfFilters'),
        (lambda self: dyn.array(FILTER, self['NumberOfFilters'])(), 'Filter')
    ]

class CLIPACTIONS(pstruct.type):
    _fields_ = [
        (UI16, 'Reserved'),
        (CLIPEVENTFLAGS, 'AllEventFlags'),
        (UI32, 'ClipActionEndFlag')
    ]

#### XXX gradient structures
class GRADRECORD(pstruct.type):
    def dyn_shape(self):
#        if self.stash('shape') == 3:
#            return RGBA
        return RGB       

    _fields_ = [
        (UI8, 'Ratio'),
        (dyn_shape, 'Color')       
    ]

class _GRADIENT_bits(pbinary.struct):
    _fields_ = [
        (2, 'SpreadMode'),
        (2, 'InterpolationMode'),
        (4, 'NumGradients')
    ]

class GRADIENT(pstruct.type):
    _fields_ = [
        (_GRADIENT_bits, 'GradientHeader'),
        (lambda self: dyn.array(GRADRECORD, self['GradientHeader']['NumGradients'])(), 'GradientRecords')
    ]

class FOCALGRADIENT(pstruct.type):
    _fields_ = [
        (_GRADIENT_bits, 'GradientHeader'),
        (lambda self: dyn.array(GRADRECORD, self['GradientHeader']['NumGradients'])(), 'GradientRecords'),
        (FIXED8, 'FocalPoint')
    ]

### XXX shapes
# 4 types of shape records
#####
class SHAPERECORD(pbinary.struct):
    def __Type(self):
        if self['TypeFlag'] == 0:
            return STYLECHANGERECORD
        return EDGERECORD

    class STYLECHANGE(pbinary.struct):
        # TypeFlag == 0
        _fields_ = [
            (1, 'StateNewStyles'),
            (1, 'StateLineStyle'),
            (1, 'StateFillStyle1'),
            (1, 'StateFillStyle0'),
            (1, 'StateMoveTo'),
            (lambda s: s['StateMoveTo'] and 5 or 0, 'MoveBits'),
            (lambda s: -s['MoveBits'], 'MoveDeltaX'),
            (lambda s: -s['MoveBits'], 'MoveDeltaY'),
            (lambda s: s.getparent(ShapeDefinition)['NumBits']['NumFillBits'] if s['StateFillStyle0'] else 0, 'FillStyle0'),
            (lambda s: s.getparent(ShapeDefinition)['NumBits']['NumFillBits'] if s['StateFillStyle1'] else 0, 'FillStyle1'),
            (lambda s: s.getparent(ShapeDefinition)['NumBits']['NumLineBits'] if s['StateLineStyle'] else 0, 'LineStyle'),

            #(lambda s: FILLSTYLEARRAY if s['StateNewStyles'] else 0, 'FillStyles'),
            #(lambda s: LINESTYLEARRAY if s['StateNewStyles'] else 0, 'LineStyles'),
            #(lambda s: 4 if s['StateNewStyles'] else 0, 'NumFillBits'),
            #(lambda s: 4 if s['StateNewStyles'] else 0, 'NumLineBits'),
        ]

        def isEndShapeRecord(self):
            return all(self[x] == 0 for x in ('StateNewStyles','StateLineStyle','StateFillStyle1','StateFillStyle0','StateMoveTo'))

    class EDGE(pbinary.struct):
        class STRAIGHT(pbinary.struct):
            # TypeFlag == 1, StraightFlag == 1
            _fields_ = [
                (1, 'GeneralLineFlag'),
                (lambda s: -(s.p['NumBits']+2) if s['GeneralLineFlag'] else 0, 'DeltaX'),
                (lambda s: -(s.p['NumBits']+2) if s['GeneralLineFlag'] else 0, 'DeltaY'),
                (lambda s: 1 if s['GeneralLineFlag'] else 0, 'VertLineFlag'),
                (lambda s: -(s.p['NumBits']+2) if s['VertLineFlag'] else 0, 'VertDeltaX'),
                (lambda s: -(s.p['NumBits']+2) if s['VertLineFlag'] else 0, 'VertDeltaY'),
            ]
        class CURVED(pbinary.struct):
            # TypeFlag == 1, StraightFlag == 0
            _fields_ = [
                (lambda s: -(s.p['NumBits']+2), 'ControlDeltaX'),
                (lambda s: -(s.p['NumBits']+2), 'ControlDeltaY'),
                (lambda s: -(s.p['NumBits']+2), 'AnchorDeltaX'),
                (lambda s: -(s.p['NumBits']+2), 'AnchorDeltaY'),
            ]

        _fields_ = [
            (1, 'StraightFlag'),
            (4, 'NumBits'),
            (lambda s: s.STRAIGHT if s['StraightFlag'] else s.CURVED, 'Edge'),
        ]

    _fields_ = [
        (1, 'TypeFlag'),
        (lambda s: s.EDGE if s['TypeFlag'] else s.STYLECHANGE, 'Shape'),
    ]

    def isEndShapeRecord(self):
        return self['TypeFlag'] == 0 and self['Shape'].isEndShapeRecord()

class SHAPERECORDLIST(pbinary.terminatedarray):
    _object_ = SHAPERECORD
    def isTerminator(self, value):
        return value.isEndShapeRecord()

### shape styles
class FILLSTYLE(pstruct.type):
    def __Color(self):
        type = self['FillStyleType'].l.num()
        tag = tags.DefineShape   # FIXME
        if type != 0:
            return Empty

        if tag.type in (tags.DefineShape.type,tags.DefineShape2.type):
            return RGB
        return RGBA

    def __has(types, result):
        def has(self):
            if self['FillStyleType'].l.num() in types:
                return result
            return Empty
        return has

    def __Gradient(self):
        type = self['FillStyleType'].l.num()
        if type in (0x10,0x12):
            return GRADIENT
        if type == 0x13:
            return FOCALGRADIENT
        return Empty

    _fields_ = [
        (UI8, 'FillStyleType'),
        (__Color, 'Color'),
        (__has((0x10,0x12,0x13), MATRIX), 'GradientMatrix'),
        (__Gradient, 'Gradient'),
        (__has((0x40,0x41,0x42,0x43), UI16), 'BitmapId'),
        (__has((0x40,0x41,0x42,0x43), MATRIX), 'BitmapMatrix'),
    ]


class LINESTYLE(pstruct.type):
    def __Color(self):
        type = tags.DefineShape.type  # FIXME
        if type == tags.DefineShape3.type:
            return RGBA
        if type in (tags.DefineShape.type,tags.DefineShape2.type):
            return RGB
        raise NotImplementedError

    _fields_ = [
        (UI16, 'Width'),
        (__Color, 'Color'),
    ]

class LINESTYLE2(pstruct.type):
    class __Style(pbinary.struct):
        _fields_ = [
            (2, 'StartCapStyle'),
            (2, 'JoinStyle'),
            (1, 'HasFillFlag'),
            (1, 'NoHScaleFlag'),
            (1, 'NoVScaleFlag'),
            (1, 'PixelHintingFlag'),
            (5, 'Reserved'),
            (1, 'NoClose'),
            (2, 'EndCapStyle'),
        ]
    _fields_ = [
        (UI16, 'Width'),
        (__Style, 'Style'), 
        (lambda s: UI16 if s['Style'].l['JoinStyle'] == 2 else Empty, 'MiterLimitFactor'),
        (lambda s: RGBA if s['Style'].l['HasFillFlag'] == 0 else Empty, 'Color'),
        (lambda s: FILLSTYLE if s['Style'].l['HasFillFlag'] == 1 else Empty, 'FillType'),
    ]

class FILLSTYLEARRAY(pstruct.type):
    _fields_ = [
        (UI8, 'FillStyleCount'),
        (lambda s: UI16 if s['FillStyleCount'].l.num() == 0xff else Empty, 'FillStyleCountExtended'),
        (lambda s: dyn.array(FILLSTYLE, s.getcount()), 'FillStyles'),
    ]

    def getcount(self):
        return self['FillStyleCountExtended'] if self['FillStyleCount'].num() == 0xff else self['FillStyleCount']

class LINESTYLEARRAY(pstruct.type):
    def __LineStyles(self):
        type = tags.DefineShape.type  # FIXME
        if type == tags.DefineShape4.type:
            return dyn.array(LINESTYLE2, self.getcount())
        if type in (tags.DefineShape.type,tags.DefineShape2.type,tags.DefineShape3.type):
            return dyn.array(LINESTYLE, self.getcount())
        raise NotImplementedError

    _fields_ = [
        (UI8, 'LineStyleCount'),
        (lambda s: UI16 if s['LineStyleCount'].l.int() == 0xff else Empty, 'LineStyleCountExtended'),
        (__LineStyles, 'LineStyles'),
    ]

    def getcount(self):
        return self['LineStyleCountExtended'] if self['LineStyleCount'] == 0xff else self['LineStyleCount']

class SHAPEWITHSTYLE(pstruct.type, ShapeDefinition):
    class __NumBits(pbinary.struct):
        _fields_ = [
            (4, 'NumFillBits'),
            (4, 'NumLineBits'),
        ]

    _fields_ = [
        (FILLSTYLEARRAY, 'FillStyles'),
        (LINESTYLEARRAY, 'LineStyles'),
        (__NumBits, 'NumBits'),
        (SHAPERECORDLIST, 'ShapeRecords'),
    ]

#### sound
class SOUNDENVELOPE(pstruct.type):
    _fields_ = [
        (UI32, 'Pos44'),
        (UI16, 'LeftLevel'),
        (UI16, 'RightLevel'),
    ]

class SOUNDINFO(pstruct.type):
    class __flags(pbinary.struct):
        _fields_ = [
            (2, 'Reserved'),
            (1, 'SyncStop'),
            (1, 'SyncNoMultiple'),
            (1, 'HasEnvelope'),
            (1, 'HasLoops'),
            (1, 'HasOutPoint'),
            (1, 'HasInPoint'),
        ]
    _fields_ = [
        (__flags, 'Flags'),
        (lambda s: UI32 if s['Flags'].l['HasInPoint'] else Empty, 'InPoint'),
        (lambda s: UI32 if s['Flags']['HasOutPoint'] else Empty, 'OutPoint'),
        (lambda s: UI16 if s['Flags']['HasLoops'] else Empty, 'LoopCount'),
        (lambda s: UI8 if s['Flags']['HasEnvelope'] else Empty, 'EnvPoints'),
        (lambda s: dyn.array(SOUNDENVELOPE, s['EnvPoints'].l.int()) if s['Flags']['HasEnvelope'] else Empty, 'EnvelopeRecords'),
    ]

## XXX font
import tags

if __name__ == '__main__':
    import ptypes
    data = '\x44\x11'

    z = RECORDHEADER(source=ptypes.provider.string(data)).l
    print z

    z.source = ptypes.provider.string(data)
    print z.l
