from primitives import *

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

class RECORDHEADER(pbinary.littleendian(pbinary.struct)):
    _fields_ = [
        (10, 'type'),
        (6, 'length')
    ]

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

###
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

###
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

####
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

############
class ENDSHAPERECORD(pbinary.struct):
    pass

class FILLSTYLE(pstruct.type):
    def dyn_shape(self):
#        if self.stash('shape') == 3:
#            return RGBA

        return RGB       

    def color(self):
        if int(self['FillStyleType']) == 0:
            return self.dyn_shape()
        return Empty

    def gradient(self):
        if int(self['FillStyleType']) in [0x10,0x12]:
            return GRADIENT
        if int(self['FillStyleType']) == 0x13:
            return FOCALGRADIENT
        return Empty

    def iftypes(value, typ):
        def fn(self):
            if int(self['FillStyleType']) in value:
                return typ
            return Empty
        return fn

    _fields_ = [
        (UI8, 'FillStyleType'),
        (color, 'Color'),
        (iftypes([0x10,0x12], MATRIX), 'GradientMatrix'),
        (gradient, 'Gradient'),
        (iftypes([0x40,0x41,0x42,0x43], UI16), 'BitmapId'),
        (iftypes([0x40,0x41,0x42,0x43], MATRIX), 'BitmapMatrix')
    ]

class LINESTYLE(pstruct.type):
    def dyn_shape(self):
#        if self.stash('shape') == 3:
#            return RGBA
        return RGB       

    _fields_ = [
        (UI16, 'Width'),
        (dyn_shape, 'Color'),
    ]

class FILLSTYLEARRAY(pstruct.type):
    def _iff(field, value, typ):
        def fn(self):
            if self[field] == value:
                return typ
            return Empty
        return fn

    _fields_ = [
        (UI8, 'FillStyleCount'),
        (_iff('FillStyleCount', 0xff, UI16), 'FillStyleCountExtended'),
        (lambda self: dyn.array(FILLSTYLE, self['FillStyleCount'])(), 'FillStyles')
    ]

class LINESTYLEARRAY(FILLSTYLEARRAY):
    def _iff(field, value, typ):
        def fn(self):
            if self[field] == value:
                return typ
            return Empty
        return fn

    _fields_ = [
        (UI8, 'LineStyleCount'),
        (_iff('LineStyleCount', 0xff, UI16), 'LineStyleCountExtended'),
        (lambda self: dyn.array(LINESTYLE, self['LineStyleCount'])(), 'LineStyles')
    ]


class _SHAPEWITHSTYLE_Num(pbinary.struct):
    _fields_ = [
        (4, 'FillBits'),
        (4, 'LineBits')
    ]

class SHAPEWITHSTYLE(pstruct.type):
    _fields_ = [
        (FILLSTYLEARRAY, 'FillStyles'),
        (LINESTYLEARRAY, 'LineStyles'),
        (_SHAPEWITHSTYLE_Num, 'Num'),
        (Empty, 'ShapeRecords')
    ]

if False:
    '''
    # FIXME: please implement this....
    class SHAPERECORD(pbinary.struct):
        id = 0

    class ENDSHAPERECORD(SHAPERECORD):
        _fields_ = [
            (1, 'TypeFlag'),
            (5, 'EndOfshape')
        ]

    class _STYLECHANGERECORD_bits(pbinary.struct):
        _fields_ = [
            (1, 'TypeFlag'),
            (1, 'StateNewStyles'),
            (1, 'StateLineStyle'),
            (1, 'StateFillStyle1'),
            (1, 'StateFillStyle0'),
            (1, 'StateMoveTo')
            (lambda self: self['StateMoveTo'] and 5 or 0, 'MoveBits'),
            (lambda self: self['StateMoveTo'] and self['MoveBits'] or 0, 'MoveDeltaX'),
            (lambda self: self['StateMoveTo'] and self['MoveBits'] or 0, 'MoveDeltaX'),
        ]

        def debit(self, nextbit):
            fillbits = self.parent['Num']['FillBits']
            linebits = self.parent['Num']['LineBits']

            nextbit(6)
           
            if self['StateMoveTo']:
                self._fields_.append( (5, 'MoveBits') )
                nextbit(5)

                self._fields_.append( (self['MoveBits'], 'MoveDeltaX') )
                self._fields_.append( (self['MoveBits'], 'MoveDeltaY') )
                nextbit( self['MoveBits']*2 )
            
            if self['StateFillStyle0']:
                self._fields_.append( (fillbits, 'FillStyle0') )
                nextbit(fillbits)

            if self['StateFillStyle1']:
                self._fields_.append( (fillbits, 'FillStyle1') )
                nextbit(fillbits)
    '''

class FILLSTYLE(pstruct.type):
    def _ifcolor(self):
        if self['FillStyleType'] == 0:
            if type(self.parent) == DefineShape3:
                return RGBA
            else:
                return RGB
        return Empty

    def _ifgradient(self):
        if int(self['FillStyleType']) in [0x10, 0x12]:
            return GRADIENT
        elif int(self['FillStyleType']) == 0x13:
            return FOCALGRADIENT
        return Empty

    _fields_ = [
        (UI8, 'FillStyleType'),
        (_ifcolor, 'Color'),
        ( _ifelse(lambda x: int(x['FillStyleType']) in [0x10, 0x12], MATRIX, Empty), 'GradientMatrix'),
        ( _ifgradient, 'Gradient'),
        ( _ifelse( lambda x: int(x['FillStyleType']) in [0x40, 0x41, 0x42, 0x43], UI16, Empty), 'BitmapId' ),
        ( _ifelse( lambda x: int(x['FillStyletype']) in [0x40, 0x41, 0x42, 0x43], MATRIX, Empty), 'BitmapMatrix' )
    ]

class LINESTYLE(pstruct.type):
    def _ifshape(self):
        if type(self.parent) == DefineShape3:
            return RGBA
        return RGB

    _fields_ = [
        (UI16, 'Width'),
        (_ifshape, 'Color'),
    ]

class _LINESTYLE2_style(pbinary.struct):
    _fields_ = [
        (2, 'StartCapStyle'),
        (2, 'JoinStyle'),
        (1, 'HasFillFlag'),
        (1, 'NoHScaleFlag'),
        (1, 'NoVScaleFlag'),
        (1, 'PixelHintingFlag'),
        (5, 'Reserved'),
        (1, 'NoClose'),
        (2, 'EndCapStyle')
    ]

class LINESTYLE2(pstruct.type):
    def _ifshape(self):
        if type(self.parent) == DefineShape3:
            return RGBA
        return RGB

    _fields_ = [
        (UI16, 'Width'),
        (_LINESTYLE2_style, 'Style'),
        (_ifelse( lambda x: x['Style']['JoinStyle'] == 2, UI16, Empty), 'MiterLimitFactor'),
        (_ifelse( lambda x: x['Style']['HasFillFlag'] == 0, RGBA, Empty), 'Color'),
        (_ifelse( lambda x: x['Style']['HasFillFlag'] == 1, FILLSTYLE, Empty), 'FillType')
    ]

class FILLSTYLEARRAY(pstruct.type):
    _fields_ = [
        (UI8, 'FillStyleCount'),
        (_ifeq('FillStylecount', 0xff, UI16, Empty), 'FillStyleCountExtended'),
        (lambda self: dyn.array(FILLSTYLE, self['FillStyleCount'])(), 'FillStyles' )
    ]

class LINESTYLEARRAY(pstruct.type):
    def _dynstyles(self):
        if type(self.parent) == DefineShape4:
            return dyn.array(LINESTYLE2, self['LineStyleCount'])()
        return dyn.array(LINESTYLE, self['LineStyleCount'])()

    _fields_ = [
        (UI8, 'LineStyleCount'),
        (_ifeq('LineStylecount', 0xff, UI16, Empty), 'LineStyleCountExtended'),
        ( _dynstyles, 'LineStyles' )
    ]

if __name__ == '__main__':
    import ptypes
    data = '\x44\x11'

    z = RECORDHEADER()
    z.deserialize(data)
    print z

    z.source = ptypes.provider.string(data)
    print z.l
