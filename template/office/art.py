import ptypes
from ptypes import *
from . import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

## ripped from [MS-OART]
recordType = [
    ('FT_OfficeArtDgg', 0xf000),
    ('FT_OfficeArtBStore', 0xf001),
    ('FT_OfficeArtDg', 0xf002),
    ('FT_OfficeArtSpgr', 0xf003),
    ('FT_OfficeArtSp', 0xf004),
    ('FT_OfficeArtSolver', 0xf005),
    ('FT_OfficeArtFDGG', 0xf006),
    ('FT_OfficeArtFBSE', 0xf007),
    ('FT_OfficeArtFDG', 0xf008),
    ('FT_OfficeArtFSPGR', 0xf009),
    ('FT_OfficeArtFSP', 0xf00a),
    ('FT_OfficeArtFOPT', 0xf00b),
    ('FT_OfficeArtChildAnchor', 0xf00f),
    ('FT_OfficeArtFConnectorRule', 0xf012),
    ('FT_OfficeArtFArcRule', 0xf014),
    ('FT_OfficeArtFCalloutRule', 0xf017),
    ('FT_OfficeArtInlineSp', 0xf018),
    ('FT_OfficeArtBlipEMF', 0xf01a),
    ('FT_OfficeArtBlipWMF', 0xf01b),
    ('FT_OfficeArtBlipPICT', 0xf01c),
    ('FT_OfficeArtBlipJPEG', 0xf01d),
    ('FT_OfficeArtBlipPNG', 0xf01e),
    ('FT_OfficeArtBlipDIB', 0xf01f),
    ('FT_OfficeArtBlipTIFF', 0xf020),
    ('FT_OfficeArtBlipTIFF2', 0xf029),
    ('FT_OfficeArtBlipJPEG2', 0xf02a),
    ('FT_OfficeArtFRIT', 0xf118),
    ('FT_OfficeArtFDGSL', 0xf119),
    ('FT_OfficeArtColorMRU', 0xf11a),
    ('FT_OfficeArtFPSPL', 0xf11d),
    ('FT_OfficeArtSplitMenuColor', 0xf11e),
    ('FT_OfficeArtSecondaryFOPT', 0xf121),
    ('FT_OfficeArtTertiaryFOPT', 0xf122),
]

## Missing ripped from OfficeDrawing97-2007BinaryFormatSpecification.pdf
recordType.extend([
    ('FT_msofbtTextBox', 0xf00c),
    #('FT_msofbtClientTextBox', 0xf00d),    # office.graph.FT_OfficeArtClientTextBox
    ('FT_msofbtAnchor', 0xf00e),
    #('FT_msofbtChildAnchor', 0xf010),      # office.graph.FT_OfficeArtClientAnchorChart
    #('FT_msofbtClientData', 0xf011),       # office.graph.FT_OfficeArtClientData
    ('FT_msofbtAlignRule', 0xf013),
    ('FT_msofbtClientRule', 0xf015),
    ('FT_msofbtCLSID', 0xf016), # clipboard data
    ('FT_msofbtOleObject', 0xf11f), # clipboard ole object's serialized data
    ('FT_msofbtColorScheme', 0xf120),
])

## Time-related ripped from OfficeDrawing97-2007BinaryFormatSpecification.pdf
recordType.extend([
    ('FT_msofbtTimeNodeContainer', 0xf123),
    ('FT_msofbtTimeConditionList', 0xf124),
    ('FT_msofbtTimeConditionContainer', 0xf125),
    ('FT_msofbtTimeModifierList', 0xf126),
    #('FT_msofbtTimeNode', 0xf127),
    #('FT_msofbtTimeCondition', 0xf128),
    #('FT_msofbtTimeModifier', 0xf129),
    #('FT_msofbtTimeBehaviorContainer', 0xf12a),
    #('FT_msofbtTimeAnimateBehaviorContainer', 0xf12b),
    #('FT_msofbtTimeColorBehaviorContainer', 0xf12c),
    #('FT_msofbtTimeEffectBehaviorContainer', 0xf12d),
    #('FT_msofbtTimeMotionBehaviorContainer', 0xf12e),
    #('FT_msofbtTimeRotationBehaviorContainer', 0xf12f),
    #('FT_msofbtTimeScaleBehaviorContainer', 0xf130),
    #('FT_msofbtTimeSetBehaviorContainer', 0xf131),
    #('FT_msofbtTimeCommandBehaviorContainer', 0xf132),
    #('FT_msofbtTimeBehavior', 0xf133),
    #('FT_msofbtTimeAnimateBehavior', 0xf134),
    #('FT_msofbtTimeColorBehavior', 0xf135),
    #('FT_msofbtTimeEffectBehavior', 0xf136),
    #('FT_msofbtTimeMotionBehavior', 0xf137),
    #('FT_msofbtTimeRotationBehavior', 0xf138),
    #('FT_msofbtTimeScaleBehavior', 0xf139),
    #('FT_msofbtTimeSetBehavior', 0xf13a),
    #('FT_msofbtTimeCommandBehavior', 0xf13b),
    #('FT_msofbtClientVisualElement', 0xf13c),
    #('FT_msofbtTimePropertyList', 0xf13d),
    #('FT_msofbtTimeVariantList', 0xf13e),
    #('FT_msofbtTimeAnimationValueList', 0xf13f),
    #('FT_msofbtTimeIterateData', 0xf140),
    #('FT_msofbtTimeSequenceData', 0xf141),
    #('FT_msofbtTimeVariant', 0xf142),
    #('FT_msofbtTimeAnimationValue', 0xf143),
    #('FT_msofbtExtTimeNodeContainer', 0xf144),
    #('FT_msofbtSubNodeContainer', 0xf145),
    ('RT_TimeNode', 0xf127),
    ('RT_TimeCondition', 0xf128),
    ('RT_TimeModifier', 0xf129),
    ('RT_TimeBehaviorContainer', 0xf12a),
    ('RT_TimeAnimateBehaviorContainer', 0xf12b),
    ('RT_TimeColorBehaviorContainer', 0xf12c),
    ('RT_TimeEffectBehaviorContainer', 0xf12d),
    ('RT_TimeMotionBehaviorContainer', 0xf12e),
    ('RT_TimeRotationBehaviorContainer', 0xf12f),
    ('RT_TimeScaleBehaviorContainer', 0xf130),
    ('RT_TimeSetBehaviorContainer', 0xf131),
    ('RT_TimeCommandBehaviorContainer', 0xf132),
    ('RT_TimeBehavior', 0xf133),
    ('RT_TimeAnimateBehavior', 0xf134),
    ('RT_TimeColorBehavior', 0xf135),
    ('RT_TimeEffectBehavior', 0xf136),
    ('RT_TimeMotionBehavior', 0xf137),
    ('RT_TimeRotationBehavior', 0xf138),
    ('RT_TimeScaleBehavior', 0xf139),
    ('RT_TimeSetBehavior', 0xf13a),
    ('RT_TimeCommandBehavior', 0xf13b),
    ('RT_TimeClientVisualElement', 0xf13c),
    ('RT_TimePropertyList', 0xf13d),
    ('RT_TimeVariantList', 0xf13e),
    ('RT_TimeAnimationValueList', 0xf13f),
    ('RT_TimeIterateData', 0xf140),
    ('RT_TimeSequenceData', 0xf141),
    ('RT_TimeVariant', 0xf142),
    ('RT_TimeAnimationValue', 0xf143),
    ('RT_TimeExtTimeNodeContainer', 0xf144),
    ('RT_TimeSubEffectContainer', 0xf145),
])

# create a ptype.definition for each record type
locals().update(map(RecordType.define,recordType))

## base types
class MSOSPID(uint4): pass
class FixedPoint(pfloat.sfixed_t):
    length,fractional = 4,16

class IMsoArray(pstruct.type):
    _object_ = None

    class trunc(ptype.encoded_t):
        _value_ = dyn.block(4)
        def decode(self, **attrs):
            block = b'\x00\x00\x00\x00' + self.serialize()
            return super(trunc,self).decode(source=ptypes.prov.string(block))

    def __data(self):
        sz = self['cbElem'].li.int()
        count = self['nElems'].li.int()
        if sz == 0xfff0:
            t = dyn.clone(self.trunc, _object_=self._object_ or uint8)
        else:
            t = self._object_ or dyn.block(sz)
        return dyn.array(t, count)

    _fields_ = [
        (uint2,'nElems'),
        (uint2,'nElemsAlloc'),
        (uint2,'cbElem'),
        (__data,'data'),
    ]

class IMsoInkData(pstruct.type):
    _fields_ = [
        (dyn.block(16), 'CLSID_InkDisp'),
        (uint4, 'cbBlob'),
        (lambda s: dyn.block(s['cbBlob'].li.int()), 'data'),
    ]

class POINT(pstruct.type):
    _fields_ = [
        (sint4, 'X'),
        (sint4, 'Y'),
    ]

class MSOPATHINFO(pbinary.struct):
    _fields_ = R([
        (3, 'type'), # MSOPATHTYPE
        (13, 'segments'),
    ])

class MSOPATHESCAPEINFO(pbinary.struct):
    _fields_ = R([
        (3, 'type'),    # MSOPATHTYPE
        (5, 'escape'),  # MSOPATHESCAPE
        (8, 'segments'),
    ])

class RECT(pstruct.type):
    _fields_ = [
        (sint4, 'left'),
        (sint4, 'top'),
        (sint4, 'right'),
        (sint4, 'bottom'),
    ]

class ADJH(pstruct.type):
    class flags(pbinary.flags):
        _fields_ = R([
            (1, 'fahInverseX'),
            (1, 'fahInverseY'),
            (1, 'fahSwitchPosition'),
            (1, 'fahPolar'),
            (1, 'fahMap'),
            (1, 'fahPin'),
            (1, 'fahUnused'),
            (1, 'fahxMin'),
            (1, 'fahxMax'),
            (1, 'fahyMin'),
            (1, 'fahyMax'),
            (1, 'fahxRange'),
            (1, 'fahyRange'),
            (1, 'fahPolarPin'),
            (18, 'unused1'),
        ])
    _fields_ = [
        (flags, 'flags'),
        (uint4, 'apX'),
        (uint4, 'apY'),
        (sint4, 'xRange'),
        (sint4, 'yRange'),
        (sint4, 'xMin'),
        (sint4, 'xMax'),
        (sint4, 'yMin'),
        (sint4, 'yMax'),
    ]

class SG(pbinary.struct):
    _fields_ = R([
        (13, 'sgf'),
        (1, 'fCalculatedParam1'),
        (1, 'fCalculatedParam2'),
        (1, 'fCalculatedParam3'),
        (16, 'param1'),
        (16, 'param2'),
        (16, 'param3'),
    ])

class IHlink(pstruct.type):
    _fields_ = [
        (dyn.block(16), 'CLSID_StdHlink'),
        (ptype.undefined, 'hyperlink'), # FIXME: [MS-OSHARED] Hyperlink
    ]

class OfficeArtFOPTEOPID(pbinary.struct):
    _fields_ = R([
        (14,'id'),
        (1,'fBid'),
        (1,'fComplex'),
    ])

class OfficeArtFOPTEOP(ptype.definition):
    cache = {}
    class unknown(sint4): pass
    default = unknown

class OfficeArtFOPTE(pstruct.type):
    def __op(self):
        res = self['opid'].li
        opid = res['id']
        return OfficeArtFOPTEOP.withdefault(opid, type=opid)

    _fields_ = [
        (OfficeArtFOPTEOPID, 'opid'),
        (__op, 'op'),
    ]

    def Type(self):
        return self['op'].complex()

class TABLEFLAGS(pbinary.struct):
    _fields_ = R([
        (1, 'fIsTable'),
        (1, 'fIsTablePlaceholder'),
        (1, 'fIsTableRTL'),
        (29, 'unused1'),
    ])

class COLORREF(pbinary.struct):
    _fields_ = R([
        (8, 'red'),
        (8, 'green'),
        (8, 'blue'),
        (1, 'fPaletteIndex'),
        (1, 'fPaletteRGB'),
        (1, 'fSystemRGB'),
        (1, 'fSchemeIndex'),
        (1, 'fSysIndex'),
        (1, 'unused1'),
        (1, 'unused2'),
        (1, 'unused3'),
    ])

class MSOSHADECOLOR(pstruct.type):
    _fields_ = [
        (COLORREF, 'color'),
        (FixedPoint, 'position'),
    ]

class MSOSHADETYPE(pbinary.flags):
    _values_ = [
        (1, 'msoshadeNone'),
        (1, 'msoshadeGamma'),
        (1, 'msoshadeSigma'),
        (1, 'msoshadeBand'),
        (1, 'msoshadeOneColor'),
        (27, 'unused1'),
    ]

class MSOTINTSHADE(uint4): pass

## base enumerations
class MSOBLIPTYPE(pint.enum, uint4):
    _values_ = [
        ('msoblipERROR', 0x00), # Error reading the file.
        ('msoblipUNKNOWN', 0x01), # Unknown BLIP type.
        ('msoblipEMF', 0x02), # EMF.
        ('msoblipWMF', 0x03), # WMF.
        ('msoblipPICT', 0x04), # Macintosh PICT.
        ('msoblipJPEG', 0x05), # JPEG.
        ('msoblipPNG', 0x06), # PNG.
        ('msoblipDIB', 0x07), # DIB
        ('msoblipTIFF', 0x11), # TIFF
        ('msoblipCMYKJPEG', 0x12), # JPEG in the YCCK or CMYK color space.
    ]

class MSODGCID(pint.enum, uint4):
    _values_ = [
        ('msodgcidNil', 0x0000), # Undefined-the command is specified by a toolbar control identifier (TCID).
        ('msodgcidPaste', 0x0004), # Paste.
        ('msodgcidSelectAll', 0x0006), # Select all the drawing objects.
        ('msodgcidRepeat', 0x0008), # Repeat the last action.
        ('msodgcidBringToFront', 0x000c), # Bring the drawing objects to the front.
        ('msodgcidSendToBack', 0x000d), # Send the drawing objects to the back.
        ('msodgcidBringForward', 0x000e), # Bring the drawing objects forward. (Not necessarily all the way to the front.)
        ('msodgcidSendBackward', 0x000f), # Send the drawing objects backward. (Not necessarily all the way to the back.)
        ('msodgcidBringInFrontOfDocument', 0x0010), # Bring the drawing objects in front of the text.
        ('msodgcidSendBehindDocument', 0x0011), # Send the drawing objects behind the text.
        ('msodgcidGroup', 0x0012), # Group the drawing objects.
        ('msodgcidUngroup', 0x0013), # Ungroup the grouped drawing objects.
        ('msodgcidRegroup', 0x0014), # Regroup the drawing objects.
        ('msodgcidInsertPolygonPt', 0x0019), # Add a point to a polygon shape.
        ('msodgcidDeletePolygonPt', 0x001a), # Delete a point from a polygon shape.
        ('msodgcidCopyPolygonPt', 0x001c), # Copy a polygon point.
        ('msodgcidClosePolygon', 0x001d), # Close the path on a shape that has an open path.
        ('msodgcidOpenPolygon', 0x001e), # Open the path on a shape that has a closed path.
        ('msodgcidPolygonReshape', 0x0020), # Update the vertex and segment information in the polygon.
        ('msodgcidAutoVertex', 0x0021), # Edit a point on a shape to be an automatic point. An automatic point has Bezier handles which are automatically calculated based on the positions of the adjacent vertices.
        ('msodgcidSmoothVertex', 0x0022), # Edit a point on a shape to be a smooth point. A smooth point has Bezier handles which are collinear with and equidistant from the point.
        ('msodgcidStraightVertex', 0x0023), # Edit a point on a shape to be a straight point. A straight point has Bezier handles which are collinear with the point, but not necessarily equidistant from it.
        ('msodgcidCornerVertex', 0x0024), # Edit a point on a shape to be a corner point.
        ('msodgcidStraightSegment', 0x0025), # Edit a segment on a shape to be a straight segment.
        ('msodgcidCurvedSegment', 0x0026), # Edit a segment on a shape to be a curved segment.
        ('msodgcidRotateLeft90', 0x0029), # Rotate the drawing objects 90 degrees counterclockwise.
        ('msodgcidRotateRight90', 0x002a), # Rotate the drawing objects 90 degrees clockwise.
        ('msodgcidFlipHorizontal', 0x002b), # Horizontally flip the drawing objects.
        ('msodgcidFlipVertical', 0x002c), # Vertically flip the drawing objects.
        ('msodgcidAlignLeft', 0x002d), # Align the drawing objects to the left side.
        ('msodgcidAlignCenterHorizontal', 0x002e), # Align the drawing objects to the center.
        ('msodgcidAlignRight', 0x002f), # Align the drawing objects to the right side.
        ('msodgcidAlignTop', 0x0030), # Align the drawing objects to the top.
        ('msodgcidAlignCenterVertical', 0x0031), # Vertically align the drawing objects to the middle.
        ('msodgcidAlignBottom', 0x0032), # Align the drawing objects to the bottom.
        ('msodgcidAlignPageRelative', 0x0033), # Align the drawing objects relative to the page, rather than relative to one another.
        ('msodgcidDistributeHorizontal', 0x0034), # Horizontally distribute the drawing objects.
        ('msodgcidDistributeVertical', 0x0035), # Vertically distribute the drawing objects.
        ('msodgcidDistributePageRelative', 0x0036), # When distributing the drawing objects, do so relative to the page or slide, rather than relative to one another.
        ('msodgcidNudgeLeft', 0x0037), # Nudge the drawing objects to the left.
        ('msodgcidNudgeRight', 0x0038), # Nudge the drawing objects to the right.
        ('msodgcidNudgeUp', 0x0039), # Nudge the drawing objects up.
        ('msodgcidNudgeDown', 0x003a), # Nudge the drawing objects down.
        ('msodgcidNudgeLeftOne', 0x003b), # Nudge the drawing objects to the left by one pixel.
        ('msodgcidNudgeRightOne', 0x003c), # Nudge the drawing objects to the right by one pixel.
        ('msodgcidNudgeUpOne', 0x003d), # Nudge the drawing objects up by one pixel.
        ('msodgcidNudgeDownOne', 0x003e), # Nudge the drawing objects down by one pixel.
        ('msodgcidToggleReshapeMode', 0x003f), # Toggle the reshape mode.
        ('msodgcidToggleRotateMode', 0x0040), # Toggle the rotate mode.
        ('msodgcidToggleCropMode', 0x0041), # Crop the picture.
        ('msodgcidMoreFillColor', 0x0043), # Show more fill colors.
        ('msodgcidFillEffect', 0x0044), # Show more fill effects.
        ('msodgcidMoreLineColor', 0x0045), # Show more outline colors.
        ('msodgcidMoreLineWidth', 0x0046), # Show more line widths.
        ('msodgcidMoreArrow', 0x0047), # Show more line end decorations.
        ('msodgcidTextEffectRotateCharacters', 0x0048), # Display the text in stylized text objects as vertical text.
        ('msodgcidTextEffectStretchToFill', 0x0049), # Stretch the text in stylized text objects to fill the shape.
        ('msodgcidTextEffectSameHeight', 0x004a), # Set all the letters to the same height in stylized text objects.
        ('msodgcidTextEffectAlignLeft', 0x004b), # Align the text in stylized text objects to the left side.
        ('msodgcidTextEffectAlignCenter', 0x004c), # Align the text in stylized text objects to the center.
        ('msodgcidTextEffectAlignRight', 0x004d), # Align the text in stylized text objects to the right side.
        ('msodgcidTextEffectAlignLetterJustify', 0x004e), # Set the alignment for stylized text objects to letter justify.
        ('msodgcidTextEffectAlignWordJustify', 0x0050), # Set the alignment for stylized text objects to word justify.
        ('msodgcidTextEffectAlignStretchJustify', 0x0051), # Set the alignment for stylized text objects to stretch justify.
        ('msodgcidTextEffectSpacingVeryTight', 0x0052), # Set the text spacing for stylized text objects to very tight.
        ('msodgcidTextEffectSpacingTight', 0x0053), # Set the text spacing for stylized text objects to tight.
        ('msodgcidTextEffectSpacingNormal', 0x0054), # Set the text spacing for stylized text objects to normal.
        ('msodgcidTextEffectSpacingLoose', 0x0055), # Set the text spacing for stylized text objects to loose.
        ('msodgcidTextEffectSpacingVeryLoose', 0x0056), # Set the text spacing for stylized text objects to very loose.
        ('msodgcidTextEffectKernPairs', 0x0057), # Kern character pairs that exist in the text in stylized text objects.
        ('msodgcidTextEffectEditText', 0x0058), # Edit the text in a stylized text object.
        ('msodgcidPictureMoreContrast', 0x0059), # Increase the contrast of the picture.
        ('msodgcidPictureLessContrast', 0x005a), # Decrease the contrast of the picture.
        ('msodgcidPictureMoreBrightness', 0x005b), # Increase the brightness of the picture.
        ('msodgcidPictureLessBrightness', 0x005c), # Decrease the brightness of the picture.
        ('msodgcidPictureReset', 0x005d), # Reset the picture to the default settings.
        ('msodgcidPictureImageAutomatic', 0x005e), # Use automatic picture colors.
        ('msodgcidPictureImageGrayscale', 0x005f), # Display the picture in grayscale.
        ('msodgcidPictureImageBlackWhite', 0x0060), # Display picture in black and white.
        ('msodgcidPictureImageWatermark', 0x0061), # Add a watermark to the picture.
        ('msodgcidPictureInLine', 0x0062), # Set the picture to be inline with the text.
        ('msodgcidMoreShadow', 0x0067), # Show the shadow settings.
        ('msodgcidMoreShadowColor', 0x0068), # Show more shadow colors.
        ('msodgcidNudgeShadowUp', 0x0069), # Nudge the shadow up.
        ('msodgcidNudgeShadowDown', 0x006a), # Nudge the shadow down.
        ('msodgcidNudgeShadowLeft', 0x006b), # Nudge the shadow to the left.
        ('msodgcidNudgeShadowRight', 0x006c), # Nudge the shadow to the right.
        ('msodgcidMore3D', 0x006d), # Show the 3-D settings.
        ('msodgcidMore3DColor', 0x006e), # Show more 3-D colors.
        ('msodgcid3DToggle', 0x006f), # Toggle the 3-D options on or off.
        ('msodgcid3DTiltForward', 0x0070), # Tilt the 3-D drawing objects down.
        ('msodgcid3DTiltBackward', 0x0071), # Tilt the 3-D drawing objects up.
        ('msodgcid3DTiltLeft', 0x0072), # Tilt the 3-D drawing objects to the left.
        ('msodgcid3DTiltRight', 0x0073), # Tilt the 3-D drawing objects to the right.
        ('msodgcid3DDepth0', 0x0074), # Set the 3-D depth to 0 points.
        ('msodgcid3DDepth1', 0x0075), # Set the 3-D depth to 36 points.
        ('msodgcid3DDepth2', 0x0076), # Set the 3-D depth to 72 points.
        ('msodgcid3DDepth3', 0x0077), # Set the 3-D depth to 144 points.
        ('msodgcid3DDepth4', 0x0078), # Set the 3-D depth to 288 points.
        ('msodgcid3DDepthInfinite', 0x0079), # Set the 3-D depth to infinity.
        ('msodgcid3DPerspective', 0x007a), # Set the 3-D direction to perspective.
        ('msodgcid3DParallel', 0x007b), # Set the 3-D direction to parallel.
        ('msodgcid3DLightingFlat', 0x007c), # Set the 3-D lighting to bright.
        ('msodgcid3DLightingNormal', 0x007d), # Set the 3-D lighting to normal.
        ('msodgcid3DLightingHarsh', 0x007e), # Set the 3-D lighting to dim.
        ('msodgcid3DSurfaceMatte', 0x007f), # Set the 3-D surface to matte.
        ('msodgcid3DSurfacePlastic', 0x0080), # Set the 3-D surface to plastic.
        ('msodgcid3DSurfaceMetal', 0x0081), # Set the 3-D surface to metal.
        ('msodgcid3DSurfaceWireFrame', 0x0082), # Set the 3-D surface to wire frame.
        ('msodgcidToolPointer', 0x0087), # Select drawing objects.
        ('msodgcidToolMarquee', 0x0088), # Drag a rectangle to select multiple drawing objects.
        ('msodgcidToolLine', 0x008c), # Insert a line shape.
        ('msodgcidToolArrow', 0x008d), # Insert an arrow shape.
        ('msodgcidToolDoubleArrow', 0x008e), # Insert a double arrow shape.
        ('msodgcidToolArc', 0x008f), # Insert an arc shape.
        ('msodgcidToolPolygon', 0x0090), # Insert a polygon shape.
        ('msodgcidToolFilledPolygon', 0x0091), # Insert a filled polygon shape.
        ('msodgcidToolCurve', 0x0092), # Insert a curve shape.
        ('msodgcidToolFreeform', 0x0093), # Insert a freeform shape.
        ('msodgcidToolFilledFreeform', 0x0094), # Insert a filled freeform shape.
        ('msodgcidToolFreehand', 0x0095), # Insert a scribble shape.
        ('msodgcidToolText', 0x0098), # Insert a text box.
        ('msodgcidToolStraightConnector', 0x009d), # Insert a straight connector shape.
        ('msodgcidToolAngledConnector', 0x009e), # Insert an elbow connector shape.
        ('msodgcidToolCurvedConnector', 0x009f), # Insert a curved connector shape.
        ('msodgcidSwatchFillColorNone', 0x00a1), # Set the fill color to no color.
        ('msodgcidSwatchFillColorStandard', 0x00a2), # Standard fill colors.
        ('msodgcidSwatchFillColorMRU', 0x00a3), # Recently used fill colors.
        ('msodgcidSwatchLineColorNone', 0x00a4), # Set the line color to no color.
        ('msodgcidSwatchLineColorStandard', 0x00a5), # Standard line colors.
        ('msodgcidSwatchLineColorMRU', 0x00a6), # Recently used line colors.
        ('msodgcidSwatchShadowColorStandard', 0x00a8), # Standard shadow colors.
        ('msodgcidSwatchShadowColorMRU', 0x00a9), # Recently used shadow colors.
        ('msodgcidSwatch3DColorAutomatic', 0x00ab), # Automatic 3-D colors.
        ('msodgcidSwatch3DColorStandard', 0x00ac), # Standard 3-D colors.
        ('msodgcidSwatch3DColorMRU', 0x00ad), # Recently used 3-D colors.
        ('msodgcidSwatchDlgGradientFgColorStandard', 0x00bd), # Select the gradient foreground color from the standard colors.
        ('msodgcidSwatchDlgColorMRU', 0x00c7), # Recently used colors.
        ('msodgcidSplitMenuLineColor', 0x00df), # Recently used line colors.
        ('msodgcidSplitMenuShadowColor', 0x00e0), # Recently used shadow colors.
        ('msodgcidSplitMenu3DColor', 0x00e1), # Recently used 3-D colors.
        ('msodgcidRerouteConnections', 0x00e2), # Reroute the connectors.
        ('msodgcidStraightStyle', 0x00e3), # Change the selected connector to a straight connector.
        ('msodgcidAngledStyle', 0x00e4), # Change the selected connector to an elbow connector.
        ('msodgcidCurvedStyle', 0x00e5), # Change the selected connector to an arrow connector.
        ('msodgcidToggleFill', 0x00e6), # Set the fill color.
        ('msodgcidToggleLine', 0x00e7), # Set the line color.
        ('msodgcidToggleShadow', 0x00e8), # Toggle the shadow on or off.
        ('msodgcidEditPicture', 0x00eb), # Edit the picture.
        ('msodgcidFormatShape', 0x00ec), # Format the shape object.
        ('msodgcidTextEffectInsert', 0x00f0), # Show the options for stylized text objects.
        ('msodgcidTextEffectToolbarToggle', 0x00f1), # Show the toolbar for stylized text objects.
        ('msodgcidLinePatternFill', 0x00fd), # Show the options for patterned lines.
        ('msodgcidActivateText', 0x010a), # Add text to the drawing object.
        ('msodgcidToggleShadowOpacity', 0x010b), # Set the shadow opacity.
        ('msodgcidExitReshapeMode', 0x010c), # Exit edit point mode.
        ('msodgcidToolVerticalText', 0x010d), # Insert a vertical text box.
        ('msodgcidExitRotateMode', 0x010e), # Exit rotate mode.
        ('msodgcidTogglePictureToolbar', 0x010f), # Show the picture toolbar.
        ('msodgcidSetDefaults', 0x0110), # Set the selected shape as the default shape.
        ('msodgcidToolStraightArrowConnector', 0x0112), # Insert a straight arrow connector shape.
        ('msodgcidToolAngledArrowConnector', 0x0113), # Insert an elbow arrow connector shape.
        ('msodgcidToolCurvedArrowConnector', 0x0114), # Insert a curved arrow connector shape.
        ('msodgcidToolStraightDblArrowConnector', 0x0115), # Insert a straight double-arrow connector shape.
        ('msodgcidToolAngledDblArrowConnector', 0x0116), # Insert an elbow double-arrow connector shape.
        ('msodgcidToolCurvedDblArrowConnector', 0x0117), # Insert a curved double-arrow connector shape.
        ('msodgcidToolSetTransparentColor', 0x0118), # Set the transparent color.
        ('msodgcidTextEffectGallery', 0x0119), # Show the gallery for stylized text objects. The gallery is a series of sample images that illustrate the various stylized text objects available. Any option may be customized after it has been selected from the gallery.
        ('msodgcidShowAutoShapesAndDrawingToolbars', 0x011a), # Show the automatic shapes and drawing toolbars.
        ('msodgcidDeleteSegment', 0x011d), # Delete a line segment from a shape.
        ('msodgcidTogglePointerMode', 0x0122), # Select objects.
        ('msodgcidInsertScript', 0x0136), # Insert a script on the Web page.
        ('msodgcidRunCag', 0x0139), # Open the task pane for clip art.
        ('msodgcidRunCagForPictures', 0x013a), # Insert a picture from the clip organizer.
        ('msodgcidRunCagForMovies', 0x013b), # Insert a movie from the clip organizer.
        ('msodgcidRunCagForSounds', 0x013c), # Insert a sound from the clip organizer.
        ('msodgcidRunCagForShapes', 0x013d), # Show the automatic shapes from the clip organizer.
        ('msodgcidMultiSelect', 0x013f), # Select multiple objects.
        ('msodgcidInsertDrawingCanvas', 0x0140), # Insert a new drawing canvas.
        ('msodgcidInsertOrgChart', 0x0141), # Insert an organizational chart diagram.
        ('msodgcidInsertRadialChart', 0x0142), # Insert a radial diagram.
        ('msodgcidInsertCycleChart', 0x0143), # Insert a cycle diagram.
        ('msodgcidInsertStackedChart', 0x0144), # Insert a pyramid diagram.
        ('msodgcidInsertBullsEyeChart', 0x0145), # Insert a target diagram.
        ('msodgcidInsertVennDiagram', 0x0146), # Insert a Venn diagram.
        ('msodgcidOrgChartInsertSubordinate', 0x0147), # Insert a subordinate node for an organizational chart.
        ('msodgcidOrgChartInsertCoworker', 0x0148), # Insert a coworker node for an organizational chart.
        ('msodgcidOrgChartInsertAssistant', 0x0149), # Insert an assistant node for an organizational chart.
        ('msodgcidOrgChartDeleteNode', 0x014a), # Delete the diagram node.
        ('msodgcidOrgChartLayoutHorizontal1', 0x014b), # Set the organizational chart layout to standard.
        ('msodgcidOrgChartLayoutHorizontal2', 0x014c), # Set the organizational chart layout to both hanging.
        ('msodgcidOrgChartLayoutVertical1', 0x014d), # Set the organizational chart layout to right hanging.
        ('msodgcidOrgChartLayoutVertical2', 0x014e), # Set the organizational chart layout to left hanging.
        ('msodgcidDiagramStyle', 0x014f), # Change the diagram style.
        ('msodgcidConvertToVenn', 0x0151), # Convert the selected diagram to a Venn diagram.
        ('msodgcidConvertToRadial', 0x0152), # Convert the selected diagram to a radial diagram.
        ('msodgcidConvertToCycle', 0x0153), # Convert the selected diagram to a cycle diagram.
        ('msodgcidConvertToBullsEye', 0x0154), # Convert the selected diagram to a target diagram.
        ('msodgcidConvertToPyramid', 0x0155), # Convert the selected diagram to a pyramid diagram.
        ('msodgcidMoveDiagramShapeUp', 0x0156), # Move the diagram shape backward.
        ('msodgcidMoveDiagramShapeDown', 0x0157), # Move the diagram shape forward.
        ('msodgcidInsertDiagramShape', 0x0158), # Insert a shape into diagram.
        ('msodgcidInsertDiagram', 0x0159), # Insert a diagram.
        ('msodgcidCanvasFit', 0x015b), # Fit the diagram to the canvas.
        ('msodgcidCanvasResize', 0x015c), # Resize the drawing canvas.
        ('msodgcidToggleCanvasToolbar', 0x015d), # Show the drawing canvas toolbar.
        ('msodgcidCanvasExpand', 0x015f), # Expand the drawing canvas.
        ('msodgcidAlignCanvasRelative', 0x0179), # Align the diagram relative to the drawing canvas, rather than relative to the page or to other objects.
        ('msodgcidOrgChartSelectLevel', 0x017a), # Select the level inside the organizational chart.
        ('msodgcidOrgChartSelectBranch', 0x017b), # Select the branch inside the organizational chart.
        ('msodgcidOrgChartSelectAllAssistants', 0x017c), # Select all the assistants.
        ('msodgcidOrgChartSelectAllConnectors', 0x017d), # Select all the connector shapes.
        ('msodgcidDiagramDeleteNode', 0x017e), # Delete the shape from the diagram.
        ('msodgcidDiagramReverse', 0x017f), # Reverse the direction of the diagram.
        ('msodgcidDiagramAutoLayout', 0x0180), # Set the diagram layout to automatic layout.
        ('msodgcidOrgChartAutoLayout', 0x0181), # Set the organizational chart layout to automatic layout.
        ('msodgcidOptimizePictDialog', 0x0187), # Show the compress pictures options.
        ('msodgcidDiagramFit', 0x018d), # Fit the diagram to its contents.
        ('msodgcidDiagramResize', 0x018e), # Resize the diagram.
        ('msodgcidDiagramExpand', 0x018f), # Expand the diagram.
        ('msodgcidOrgChartFit', 0x0190), # Fit the organizational chart to its contents.
        ('msodgcidOrgChartResize', 0x01f5), # Resize the organizational chart.
        ('msodgcidOrgChartExpand', 0x01f6), # Expand the organizational chart.
        ('msodgcidOrgChartStyle', 0x01f7), # Change the style for the organizational chart.
        ('msodgciSplitMenuOrgChartInsertShape', 0x01f8), # Insert a shape in the organizational chart.
        ('msodgcidDiagramAutoFormat', 0x01f9), # Use automatic formatting for the organizational chart.
        ('msodgcidCanvasScale', 0x01fb), # Scale the drawing canvas.
        ('msodgcidOrgChartScale', 0x01fc), # Scale the organizational chart.
        ('msodgcidDiagramScale', 0x01fd), # Scale the diagram.
        ('msodgcidAlignOrgChartRelative', 0x01ff), # Align the selection relative to the organizational chart it is contained in.
        ('msodgcidAlignDiagramRelative', 0x0200), # Align the selection relative to the diagram it is contained in.
        ('msodgcidSplitMenuInkColor', 0x0204), # Recently used ink color.
        ('msodgcidSplitMenuInkAnntColor', 0x0206), # Recently used annotation color.
        ('msodgcidInkStyle1', 0x0208), # Set the ink style to Color 1.
        ('msodgcidInkStyle2', 0x0209), # Set the ink style to Color 2.
        ('msodgcidInkStyle3', 0x020a), # Set the ink style to Color 3.
        ('msodgcidInkStyle4', 0x020b), # Set the ink style to Color 4.
        ('msodgcidInkStyle5', 0x020c), # Set the ink style to Color 5.
        ('msodgcidInkStyle6', 0x020d), # Set the ink style to Color 6.
        ('msodgcidInkStyle7', 0x020e), # Set the ink style to Color 7.
        ('msodgcidInkStyle8', 0x020f), # Set the ink style to Color 8.
        ('msodgcidInkStyle9', 0x0210), # Set the ink style to Color 9.
        ('msodgcidInkAnnotationStyle1', 0x0211), # Set the annotation style to Color 1.
        ('msodgcidInkAnnotationStyle2', 0x0212), # Set the annotation style to Color 2.
        ('msodgcidInkAnnotationStyle3', 0x0213), # Set the annotation style to Color 3.
        ('msodgcidInkAnnotationStyle4', 0x0214), # Set the annotation style to Color 4.
        ('msodgcidInkAnnotationStyle5', 0x0215), # Set the annotation style to Color 5.
        ('msodgcidInkAnnotationStyle6', 0x0216), # Set the annotation style to Color 6.
        ('msodgcidInkAnnotationStyle7', 0x0217), # Set the annotation style to Color 7.
        ('msodgcidInkAnnotationStyle8', 0x0218), # Set the annotation style to Color 8.
        ('msodgcidInkAnnotationStyle9', 0x0219), # Set the annotation style to Color 9.
        ('msodgcidToggleInkToolbar', 0x021a), # Show the ink drawing and writing toolbar.
        ('msodgcidToggleInkAnnotationToolbar', 0x021b), # Show the ink annotations toolbar.
        ('msodgcidClearAllInkAnnotations', 0x021c), # Delete all the ink annotations in the document.
        ('msodgcidInkDrawing', 0x021e), # Toggle the ink drawing/writing mode.
        ('msodgcidExitInkMode', 0x0220), # Exit ink mode.
        ('msodgcidInkEraser', 0x0221), # Use the ink eraser.
        ('msodgcidInkAnnotationEraser', 0x0222), # Use the annotation eraser.
        ('msodgcidExitInkAnnotationMode', 0x0223), # Exit ink annotation mode.
        ('msodgcidInkLabel1', 0x0224), # Use the ballpoint pen for ink.
        ('msodgcidInkLabel2', 0x0225), # Use the felt tip pen for ink.
        ('msodgcidInkLabel3', 0x0226), # Use the highlighter pen for ink.
        ('msodgcidOrgChartFitText', 0x0227), # Fit text inside the organizational chart.
        ('msodgcidEyedropperFillColor', 0x0228), # Set the eyedropper fill color.
        ('msodgcidEyedropperLineColor', 0x0229), # Set the eyedropper line color.
        ('msodgcidEyedropperShadowColor', 0x022a), # Set the eyedropper shadow color.
        ('msodgcidEyedropper3DColor', 0x022b), # Set the eyedropper 3-D color.
        ('msodgcidPictureFill', 0x022c), # Set the picture fill.
        ('msodgcidAlignSelectionRelativeSmart', 0x022d), # Align the selected objects.
        ('msodgcidAlignContainerRelativeSmart', 0x022e), # Align the drawing objects to the page.
        ('msodgcidDistributeHorizontalSmart', 0x0235), # Horizontally distribute the drawing objects.
        ('msodgcidDistributeVerticalSmart', 0x0236), # Vertically distribute the drawing objects.
        ('msodgcidInkInsertSpace', 0x023a), # Insert a space inside the ink shape.
        ('msodgcidInkAnnotationBallpoint', 0x0242), # Use the ballpoint pen for ink annotation.
        ('msodgcidInkAnnotationFelt', 0x0243), # Use the felt tip pen for ink annotation.
        ('msodgcidInkAnnotationHighlighter', 0x0244), # Use the highlighter pen for ink annotation.
        ('msodgcidMoreColorsLines', 0x0245), # Show additional color and line options.
        ('msodgcidAlignRelativeToMarginSmart', 0x0248), # Align the drawing objects to the margin.
        ('msodgcidMoreSize', 0x0249), # Show additional size options.
        ('msodgcidMoreInkColor', 0x024b), # Show more pen colors.
        ('msodgcidFillEffectGradient', 0x024c), # Show the gradient options.
        ('msodgcidFillEffectTexture', 0x024d), # Show the texture options.
        ('msodgcidFillEffectPattern', 0x024e), # Show the pattern options.
        ('msodgcidCloseInkTab', 0x024f), # Close the ink tools.
        ('msodgcidShapeRectangle', 0x1001), # Insert a rectangle shape.
        ('msodgcidShapeRoundRectangle', 0x1002), # Insert a rounded rectangle shape.
        ('msodgcidShapeEllipse', 0x1003), # Insert an oval shape.
        ('msodgcidShapeDiamond', 0x1004), # Insert a diamond shape.
        ('msodgcidShapeIsocelesTriangle', 0x1005), # Insert an isosceles triangle shape.
        ('msodgcidShapeRightTriangle', 0x1006), # Insert a right triangle shape.
        ('msodgcidShapeParallelogram', 0x1007), # Insert a parallelogram shape.
        ('msodgcidShapeTrapezoid', 0x1008), # Insert a trapezoid shape.
        ('msodgcidShapeHexagon', 0x1009), # Insert a hexagon shape.
        ('msodgcidShapeOctagon', 0x100a), # Insert an octagon shape.
        ('msodgcidShapePlus', 0x100b), # Insert a cross shape.
        ('msodgcidShapeStar', 0x100c), # Insert a 5-point star shape.
        ('msodgcidShapeArrow', 0x100d), # Insert a right arrow shape.
        ('msodgcidShapeHomePlate', 0x100f), # Insert a pentagon shape.
        ('msodgcidShapeCube', 0x1010), # Insert a cube shape.
        ('msodgcidShapeBalloon', 0x1011), # Insert a balloon shape.
        ('msodgcidShapeArc', 0x1013), # Insert an arc shape.
        ('msodgcidShapePlaque', 0x1015), # Insert a plaque shape.
        ('msodgcidShapeCan', 0x1016), # Insert a can shape.
        ('msodgcidShapeDonut', 0x1017), # Insert a donut shape.
        ('msodgcidShapeCallout1', 0x1029), # Insert a Line Callout 2 (no border) shape.
        ('msodgcidShapeCallout2', 0x102a), # Insert a Line Callout 3 (no border) shape.
        ('msodgcidShapeCallout3', 0x102b), # Insert a Line Callout 4 (no border) shape.
        ('msodgcidShapeAccentCallout1', 0x102c), # Insert a Line Callout 2 (accent bar) shape.
        ('msodgcidShapeAccentCallout2', 0x102d), # Insert a Line Callout 3 (accent bar) shape.
        ('msodgcidShapeAccentCallout3', 0x102e), # Insert a Line Callout 4 (accent bar) shape.
        ('msodgcidShapeBorderCallout1', 0x102f), # Insert a Line Callout 2 shape.
        ('msodgcidShapeBorderCallout2', 0x1030), # Insert a Line Callout 3 shape.
        ('msodgcidShapeBorderCallout3', 0x1031), # Insert a Line Callout 4 shape.
        ('msodgcidShapeAccentBorderCallout1', 0x1032), # Insert a Line Callout 2 (border and accent bar) shape.
        ('msodgcidShapeAccentBorderCallout2', 0x1033), # Insert a Line Callout 3 (border and accent bar) shape.
        ('msodgcidShapeAccentBorderCallout3', 0x1034), # Insert a Line Callout 4 (border and accent bar) shape.
        ('msodgcidShapeRibbon', 0x1035), # Insert a down ribbon shape.
        ('msodgcidShapeRibbon2', 0x1036), # Insert an up ribbon shape.
        ('msodgcidShapeChevron', 0x1037), # Insert a chevron shape.
        ('msodgcidShapePentagon', 0x1038), # Insert a regular pentagon shape.
        ('msodgcidShapeNoSmoking', 0x1039), # Insert a no symbol shape.
        ('msodgcidShapeSeal8', 0x103a), # Insert an 8-point star shape.
        ('msodgcidShapeSeal16', 0x103b), # Insert a 16-point star shape.
        ('msodgcidShapeSeal32', 0x103c), # Insert a 32-point star shape.
        ('msodgcidShapeWedgeRectCallout', 0x103d), # Insert a rectangular callout shape.
        ('msodgcidShapeWedgeRRectCallout', 0x103e), # Insert a rounded rectangular callout shape.
        ('msodgcidShapeWedgeEllipseCallout', 0x103f), # Insert an oval callout shape.
        ('msodgcidShapeWave', 0x1040), # Insert a wave shape.
        ('msodgcidShapeFoldedCorner', 0x1041), # Insert a folded corner shape.
        ('msodgcidShapeLeftArrow', 0x1042), # Insert a left arrow shape.
        ('msodgcidShapeDownArrow', 0x1043), # Insert a down arrow shape.
        ('msodgcidShapeUpArrow', 0x1044), # Insert an up arrow shape.
        ('msodgcidShapeLeftRightArrow', 0x1045), # Insert a left-right arrow shape.
        ('msodgcidShapeUpDownArrow', 0x1046), # Insert an up-down arrow shape.
        ('msodgcidShapeIrregularSeal1', 0x1047), # Insert an Explosion 1 shape.
        ('msodgcidShapeIrregularSeal2', 0x1048), # Insert an Explosion 2 shape.
        ('msodgcidShapeLightningBolt', 0x1049), # Insert a lightning bolt shape.
        ('msodgcidShapeHeart', 0x104a), # Insert a heart shape.
        ('msodgcidShapeQuadArrow', 0x104c), # Insert a quad arrow shape.
        ('msodgcidShapeLeftArrowCallout', 0x104d), # Insert a left-arrow callout shape.
        ('msodgcidShapeRightArrowCallout', 0x104e), # Insert a right-arrow callout shape.
        ('msodgcidShapeUpArrowCallout', 0x104f), # Insert an up-arrow callout shape.
        ('msodgcidShapeDownArrowCallout', 0x1050), # Insert a down-arrow callout shape.
        ('msodgcidShapeLeftRightArrowCallout', 0x1051), # Insert a left-right arrow callout shape.
        ('msodgcidShapeUpDownArrowCallout', 0x1052), # Insert an up-down arrow callout shape.
        ('msodgcidShapeQuadArrowCallout', 0x1053), # Insert a quad-arrow callout shape.
        ('msodgcidShapeBevel', 0x1054), # Insert a bevel shape.
        ('msodgcidShapeLeftBracket', 0x1055), # Insert a left bracket shape.
        ('msodgcidShapeRightBracket', 0x1056), # Insert a right bracket shape.
        ('msodgcidShapeLeftBrace', 0x1057), # Insert a left brace shape.
        ('msodgcidShapeRightBrace', 0x1058), # Insert a right brace shape.
        ('msodgcidShapeLeftUpArrow', 0x1059), # Insert a left-up arrow shape.
        ('msodgcidShapeBentUpArrow', 0x105a), # Insert a bent-up arrow shape.
        ('msodgcidShapeBentArrow', 0x105b), # Insert a bent arrow shape.
        ('msodgcidShapeSeal24', 0x105c), # Insert a 24-point star shape.
        ('msodgcidShapeStripedRightArrow', 0x105d), # Insert a striped right-arrow shape.
        ('msodgcidShapeNotchedRightArrow', 0x105e), # Insert a notched right-arrow shape.
        ('msodgcidShapeBlockArc', 0x105f), # Insert a block arc shape.
        ('msodgcidShapeSmileyFace', 0x1060), # Insert a smiling face shape.
        ('msodgcidShapeVerticalScroll', 0x1061), # Insert a vertical scroll shape.
        ('msodgcidShapeHorizontalScroll', 0x1062), # Insert a horizontal scroll shape.
        ('msodgcidShapeCircularArrow', 0x1063), # Insert a circular arrow shape.
        ('msodgcidShapeNotchedCircularArrow', 0x1064), # Insert a reserved shape.
        ('msodgcidShapeUturnArrow', 0x1065), # Insert a U-turn arrow shape.
        ('msodgcidShapeCurvedRightArrow', 0x1066), # Insert a curved right-arrow shape.
        ('msodgcidShapeCurvedLeftArrow', 0x1067), # Insert a curved left-arrow shape.
        ('msodgcidShapeCurvedUpArrow', 0x1068), # Insert a curved up-arrow shape.
        ('msodgcidShapeCurvedDownArrow', 0x1069), # Insert a curved down-arrow shape.
        ('msodgcidShapeCloudCallout', 0x106a), # Insert a cloud callout shape.
        ('msodgcidShapeEllipseRibbon', 0x106b), # Insert a curved-down ribbon shape.
        ('msodgcidShapeEllipseRibbon2', 0x106c), # Insert a curved-up ribbon shape.
        ('msodgcidShapeFlowChartProcess', 0x106d), # Insert a flowchart process shape.
        ('msodgcidShapeFlowChartDecision', 0x106e), # Insert a flowchart decision shape.
        ('msodgcidShapeFlowChartInputOutput', 0x106f), # Insert a flowchart data shape.
        ('msodgcidShapeFlowChartPredefinedProcess', 0x1070), # Insert a flowchart predefined-process shape.
        ('msodgcidShapeFlowChartInternalStorage', 0x1071), # Insert a flowchart internal-storage shape.
        ('msodgcidShapeFlowChartDocument', 0x1072), # Insert a flowchart document shape.
        ('msodgcidShapeFlowChartMultidocument', 0x1073), # Insert a flowchart multiple-document shape.
        ('msodgcidShapeFlowChartTerminator', 0x1074), # Insert a flowchart terminator shape.
        ('msodgcidShapeFlowChartPreparation', 0x1075), # Insert a flowchart preparation shape.
        ('msodgcidShapeFlowChartManualInput', 0x1076), # Insert a flowchart manual-input shape.
        ('msodgcidShapeFlowChartManualOperation', 0x1077), # Insert a flowchart manual-operation shape.
        ('msodgcidShapeFlowChartConnector', 0x1078), # Insert a flowchart connector shape.
        ('msodgcidShapeFlowChartPunchedCard', 0x1079), # Insert a flowchart card shape.
        ('msodgcidShapeFlowChartPunchedTape', 0x107a), # Insert a flowchart punched-tape shape.
        ('msodgcidShapeFlowChartSummingJunction', 0x107b), # Insert a flowchart summing-junction shape.
        ('msodgcidShapeFlowChartOr', 0x107c), # Insert a flowchart OR shape.
        ('msodgcidShapeFlowChartCollate', 0x107d), # Insert a flowchart collate shape.
        ('msodgcidShapeFlowChartSort', 0x107e), # Insert a flowchart sort shape.
        ('msodgcidShapeFlowChartExtract', 0x107f), # Insert a flowchart extract shape.
        ('msodgcidShapeFlowChartMerge', 0x1080), # Insert a flowchart merge shape.
        ('msodgcidShapeFlowChartOfflineStorage', 0x1081), # Insert a flowchart offline-storage shape.
        ('msodgcidShapeFlowChartOnlineStorage', 0x1082), # Insert a flowchart stored-data shape.
        ('msodgcidShapeFlowChartMagneticTape', 0x1083), # Insert a flowchart sequential-access storage shape.
        ('msodgcidShapeFlowChartMagneticDisk', 0x1084), # Insert a flowchart magnetic-disk shape.
        ('msodgcidShapeFlowChartMagneticDrum', 0x1085), # Insert a flowchart direct-access storage shape.
        ('msodgcidShapeFlowChartDisplay', 0x1086), # Insert a flowchart display shape.
        ('msodgcidShapeFlowChartDelay', 0x1087), # Insert a flowchart delay shape.
        ('msodgcidShapeFlowChartAlternateProcess', 0x10b0), # Insert a flowchart alternate-process shape.
        ('msodgcidShapeFlowChartOffpageConnector', 0x10b1), # Insert a flowchart off-page connector shape.
        ('msodgcidShapeCallout90', 0x10b2), # Insert a Line Callout 1 (no border) shape.
        ('msodgcidShapeAccentCallout90', 0x10b3), # Insert a Line Callout 1 (accent bar) shape.
        ('msodgcidShapeBorderCallout90', 0x10b4), # Insert a Line Callout 1 shape.
        ('msodgcidShapeAccentBorderCallout90', 0x10b5), # Insert a Line Callout 1 (border and accent bar) shape.
        ('msodgcidShapeLeftRightUpArrow', 0x10b6), # Insert a left-right-up arrow shape.
        ('msodgcidShapeSun', 0x10b7), # Insert a sun shape.
        ('msodgcidShapeMoon', 0x10b8), # Insert a moon shape.
        ('msodgcidShapeBracketPair', 0x10b9), # Insert a double bracket shape.
        ('msodgcidShapeBracePair', 0x10ba), # Insert a double brace shape.
        ('msodgcidShapeSeal4', 0x10bb), # Insert a 4-point star shape.
        ('msodgcidShapeDoubleWave', 0x10bc), # Insert a double wave shape.
        ('msodgcidShapeMinusSign', 0x10cc), # Insert a minus sign shape.
        ('msodgcidShapeMultiplySign', 0x10cd), # Insert a multiply sign shape.
        ('msodgcidShapeDivisionSign', 0x10ce), # Insert a division sign shape.
        ('msodgcidShapeEqualSign', 0x10cf), # Insert an equal sign shape.
        ('msodgcidShapeNotEqualSign', 0x10d0), # Insert a not-equal sign shape.
        ('msodgcidShapeSnipSingleCornerRectangle', 0x10d1), # Insert a rectangle shape which has a single snipped corner.
        ('msodgcidShapeSnipSameSideCornerRectangle', 0x10d2), # Insert a rectangle shape which has two snipped corners on the same side.
        ('msodgcidShapeSnipDiagonalCornerRectangle', 0x10d3), # Insert a rectangle shape which has two snipped corners diagonally across from one another.
        ('msodgcidShapeSnipRoundSingleCornerRectangle', 0x10d4), # Insert a rectangle shape which has one rounded and one snipped corner on the same side.
        ('msodgcidShapeRoundSingleCornerRectangle', 0x10d5), # Insert a rectangle shape which has a single rounded corner.
        ('msodgcidShapeRoundSameSideCornerRectangle', 0x10d6), # Insert a rectangle shape which has two rounded corners on the same side.
        ('msodgcidShapeRoundDiagonalCornerRectangle', 0x10d7), # Insert a rectangle shape which has two rounded corners diagonally across from one another.
        ('msodgcidShapeDecagon', 0x10d8), # Insert a decagon shape.
        ('msodgcidShapeDodecagon', 0x10d9), # Insert a dodecagon shape.
        ('msodgcidShapeDiagonalStripe', 0x10da), # Insert a diagonal stripe shape.
        ('msodgcidShapeTearDrop', 0x10db), # Insert a teardrop shape.
        ('msodgcidShapeChord', 0x10dc), # Insert a chord shape.
        ('msodgcidShapeHeptagon', 0x10dd), # Insert a heptagon shape.
        ('msodgcidShapeFrame', 0x10de), # Insert a frame shape.
        ('msodgcidShapeHalfFrame', 0x10df), # Insert a half-frame shape.
        ('msodgcidShapePie', 0x10e0), # Insert a pie shape.
        ('msodgcidShapeLShape', 0x10e1), # Insert an L-shape shape.
        ('msodgcidShape6PointStar', 0x10e2), # Insert a 6-point star shape.
        ('msodgcidShape7PointStar', 0x10e3), # Insert a 7-point star shape.
        ('msodgcidShape10PointStar', 0x10e4), # Insert a 10-point star shape.
        ('msodgcidShape12PointStar', 0x10e5), # Insert a 12-point star shape.
        ('msodgcidShapeCloud', 0x10e6), # Insert a cloud shape.
        ('msodgcidChangeShapeRectangle', 0x2001), # Change the selected shape to a rectangle shape.
        ('msodgcidChangeShapeRoundRectangle', 0x2002), # Change the selected shape to a rounded rectangle shape.
        ('msodgcidChangeShapeEllipse', 0x2003), # Change the selected shape to an oval shape.
        ('msodgcidChangeShapeDiamond', 0x2004), # Change the selected shape to a diamond shape.
        ('msodgcidChangeShapeIsocelesTriangle', 0x2005), # Change the selected shape to an isosceles triangle shape.
        ('msodgcidChangeShapeRightTriangle', 0x2006), # Change the selected shape to a right triangle shape.
        ('msodgcidChangeShapeParallelogram', 0x2007), # Change the selected shape to a parallelogram shape.
        ('msodgcidChangeShapeTrapezoid', 0x2008), # Change the selected shape to a trapezoid shape.
        ('msodgcidChangeShapeHexagon', 0x2009), # Change the selected shape to a hexagon shape.
        ('msodgcidChangeShapeOctagon', 0x200a), # Change the selected shape to an octagon shape.
        ('msodgcidChangeShapePlus', 0x200b), # Change the selected shape to a cross shape.
        ('msodgcidChangeShapeStar', 0x200c), # Change the selected shape to a 5-point star shape.
        ('msodgcidChangeShapeArrow', 0x200d), # Change the selected shape to a right arrow shape.
        ('msodgcidChangeShapeHomePlate', 0x200f), # Change the selected shape to a pentagon shape.
        ('msodgcidChangeShapeCube', 0x2010), # Change the selected shape to a cube shape.
        ('msodgcidChangeShapeArc', 0x2013), # Change the selected shape to an arc shape.
        ('msodgcidChangeShapePlaque', 0x2015), # Change the selected shape to a plaque shape.
        ('msodgcidChangeShapeCan', 0x2016), # Change the selected shape to a can shape.
        ('msodgcidChangeShapeDonut', 0x2017), # Change the selected shape to a donut shape.
        ('msodgcidChangeShapeCallout1', 0x2029), # Change the selected shape to a Line Callout 2 (no border) shape.
        ('msodgcidChangeShapeCallout2', 0x202a), # Change the selected shape to a Line Callout 3 (no border) shape.
        ('msodgcidChangeShapeCallout3', 0x202b), # Change the selected shape to a Line Callout 4 (no border) shape.
        ('msodgcidChangeShapeAccentCallout1', 0x202c), # Change the selected shape to a Line Callout 2 (accent bar) shape.
        ('msodgcidChangeShapeAccentCallout2', 0x202d), # Change the selected shape to a Line Callout 3 (accent bar) shape.
        ('msodgcidChangeShapeAccentCallout3', 0x202e), # Change the selected shape to a Line Callout 4 (accent bar) shape.
        ('msodgcidChangeShapeBorderCallout1', 0x202f), # Change the selected shape to a Line Callout 2 shape.
        ('msodgcidChangeShapeBorderCallout2', 0x2030), # Change the selected shape to a Line Callout 3 shape.
        ('msodgcidChangeShapeBorderCallout3', 0x2031), # Change the selected shape to a Line Callout 4 shape.
        ('msodgcidChangeShapeAccentBorderCallout1', 0x2032), # Change the selected shape to a Line Callout 2 (border and accent bar) shape.
        ('msodgcidChangeShapeAccentBorderCallout2', 0x2033), # Change the selected shape to a Line Callout 3 (border and accent bar) shape.
        ('msodgcidChangeShapeAccentBorderCallout3', 0x2034), # Change the selected shape to a Line Callout 4 (border and accent bar) shape.
        ('msodgcidChangeShapeRibbon', 0x2035), # Change the selected shape to a down ribbon shape.
        ('msodgcidChangeShapeRibbon2', 0x2036), # Change the selected shape to an up ribbon shape.
        ('msodgcidChangeShapeChevron', 0x2037), # Change the selected shape to a chevron shape.
        ('msodgcidChangeShapePentagon', 0x2038), # Change the selected shape to a regular pentagon shape.
        ('msodgcidChangeShapeNoSmoking', 0x2039), # Change the selected shape to a no symbol shape.
        ('msodgcidChangeShapeSeal8', 0x203a), # Change the selected shape to an 8-point star shape.
        ('msodgcidChangeShapeSeal16', 0x203b), # Change the selected shape to a 16-point star shape.
        ('msodgcidChangeShapeSeal32', 0x203c), # Change the selected shape to a 32-point star shape.
        ('msodgcidChangeShapeWedgeRectCallout', 0x203d), # Change the selected shape to a rectangular callout shape.
        ('msodgcidChangeShapeWedgeRRectCallout', 0x203e), # Change the selected shape to a rounded-rectangular callout shape.
        ('msodgcidChangeShapeWedgeEllipseCallout', 0x203f), # Change the selected shape to an oval callout shape.
        ('msodgcidChangeShapeWave', 0x2040), # Change the selected shape to a wave shape.
        ('msodgcidChangeShapeFoldedCorner', 0x2041), # Change the selected shape to a folded corner shape.
        ('msodgcidChangeShapeLeftArrow', 0x2042), # Change the selected shape to a left arrow shape.
        ('msodgcidChangeShapeDownArrow', 0x2043), # Change the selected shape to a down arrow shape.
        ('msodgcidChangeShapeUpArrow', 0x2044), # Change the selected shape to an up arrow shape.
        ('msodgcidChangeShapeLeftRightArrow', 0x2045), # Change the selected shape to a left-right arrow shape.
        ('msodgcidChangeShapeUpDownArrow', 0x2046), # Change the selected shape to an up-down arrow shape.
        ('msodgcidChangeShapeIrregularSeal1', 0x2047), # Change the selected shape to an Explosion 1 shape.
        ('msodgcidChangeShapeIrregularSeal2', 0x2048), # Change the selected shape to an Explosion 2 shape.
        ('msodgcidChangeShapeLightningBolt', 0x2049), # Change the selected shape to lightning bolt shape.
        ('msodgcidChangeShapeHeart', 0x204a), # Change the selected shape to a heart shape.
        ('msodgcidChangeShapeQuadArrow', 0x204c), # Change the selected shape to a quad arrow shape.
        ('msodgcidChangeShapeLeftArrowCallout', 0x204d), # Change the selected shape to a left-arrow callout shape.
        ('msodgcidChangeShapeRightArrowCallout', 0x204e), # Change the selected shape to a right-arrow callout shape.
        ('msodgcidChangeShapeUpArrowCallout', 0x204f), # Change the selected shape to an up-arrow callout shape.
        ('msodgcidChangeShapeDownArrowCallout', 0x2050), # Change the selected shape to a down-arrow callout shape.
        ('msodgcidChangeShapeLeftRightArrowCallout', 0x2051), # Change the selected shape to a left-right arrow callout shape.
        ('msodgcidChangeShapeUpDownArrowCallout', 0x2052), # Change the selected shape to an up-down arrow callout shape.
        ('msodgcidChangeShapeQuadArrowCallout', 0x2053), # Change the selected shape to a quad-arrow callout shape.
        ('msodgcidChangeShapeBevel', 0x2054), # Change the selected shape to a bevel shape.
        ('msodgcidChangeShapeLeftBracket', 0x2055), # Change the selected shape to a left bracket shape.
        ('msodgcidChangeShapeRightBracket', 0x2056), # Change the selected shape to a right bracket shape.
        ('msodgcidChangeShapeLeftBrace', 0x2057), # Change the selected shape to a left brace shape.
        ('msodgcidChangeShapeRightBrace', 0x2058), # Change the selected shape to a right brace shape.
        ('msodgcidChangeShapeLeftUpArrow', 0x2059), # Change the selected shape to a left-up arrow shape.
        ('msodgcidChangeShapeBentUpArrow', 0x205a), # Change the selected shape to a bent-up arrow shape.
        ('msodgcidChangeShapeBentArrow', 0x205b), # Change the selected shape to a bent arrow shape.
        ('msodgcidChangeShapeSeal24', 0x205c), # Change the selected shape to a 24-point star shape.
        ('msodgcidChangeShapeStripedRightArrow', 0x205d), # Change the selected shape to a striped right-arrow shape.
        ('msodgcidChangeShapeNotchedRightArrow', 0x205e), # Change the selected shape to a notched right-arrow shape.
        ('msodgcidChangeShapeBlockArc', 0x205f), # Change the selected shape to a block arc shape.
        ('msodgcidChangeShapeSmileyFace', 0x2060), # Change the selected shape to a smiling face shape.
        ('msodgcidChangeShapeVerticalScroll', 0x2061), # Change the selected shape to a vertical scroll shape.
        ('msodgcidChangeShapeHorizontalScroll', 0x2062), # Change the selected shape to a horizontal scroll shape.
        ('msodgcidChangeShapeCircularArrow', 0x2063), # Change the selected shape to a circular arrow shape.
        ('msodgcidChangeShapeUturnArrow', 0x2065), # Change the selected shape to a U-turn arrow shape.
        ('msodgcidChangeShapeCurvedRightArrow', 0x2066), # Change the selected shape to a curved right-arrow shape.
        ('msodgcidChangeShapeCurvedLeftArrow', 0x2067), # Change the selected shape to a curved left-arrow shape.
        ('msodgcidChangeShapeCurvedUpArrow', 0x2068), # Change the selected shape to a curved up-arrow shape.
        ('msodgcidChangeShapeCurvedDownArrow', 0x2069), # Change the selected shape to a curved down-arrow shape.
        ('msodgcidChangeShapeCloudCallout', 0x206a), # Change the selected shape to a cloud callout shape.
        ('msodgcidChangeShapeEllipseRibbon', 0x206b), # Change the selected shape to a curved-down ribbon shape.
        ('msodgcidChangeShapeEllipseRibbon2', 0x206c), # Change the selected shape to a curved-up ribbon shape.
        ('msodgcidChangeShapeFlowChartProcess', 0x206d), # Change the selected shape to a flowchart process shape.
        ('msodgcidChangeShapeFlowChartDecision', 0x206e), # Change the selected shape to a flowchart decision shape.
        ('msodgcidChangeShapeFlowChartInputOutput', 0x206f), # Change the selected shape to a flowchart data shape.
        ('msodgcidChangeShapeFlowChartPredefinedProcess', 0x2070), # Change the selected shape to a flowchart predefined-process shape.
        ('msodgcidChangeShapeFlowChartInternalStorage', 0x2071), # Change the selected shape to a flowchart internal-storage shape.
        ('msodgcidChangeShapeFlowChartDocument', 0x2072), # Change the selected shape to a flowchart document shape.
        ('msodgcidChangeShapeFlowChartMultidocument', 0x2073), # Change the selected shape to a flowchart multiple-document shape.
        ('msodgcidChangeShapeFlowChartTerminator', 0x2074), # Change the selected shape to a flowchart terminator shape.
        ('msodgcidChangeShapeFlowChartPreparation', 0x2075), # Change the selected shape to a flowchart preparation shape.
        ('msodgcidChangeShapeFlowChartManualInput', 0x2076), # Change the selected shape to a flowchart manual-input shape.
        ('msodgcidChangeShapeFlowChartManualOperation', 0x2077), # Change the selected shape to a flowchart manual-operation shape.
        ('msodgcidChangeShapeFlowChartConnector', 0x2078), # Change the selected shape to a flowchart connector shape.
        ('msodgcidChangeShapeFlowChartPunchedCard', 0x2079), # Change the selected shape to a flowchart card shape.
        ('msodgcidChangeShapeFlowChartPunchedTape', 0x207a), # Change the selected shape to a flowchart punched-tape shape.
        ('msodgcidChangeShapeFlowChartSummingJunction', 0x207b), # Change the selected shape to a flowchart summing-junction shape.
        ('msodgcidChangeShapeFlowChartOr', 0x207c), # Change the selected shape to a flowchart OR shape.
        ('msodgcidChangeShapeFlowChartCollate', 0x207d), # Change the selected shape to a flowchart collate shape.
        ('msodgcidChangeShapeFlowChartSort', 0x207e), # Change the selected shape to a flowchart sort shape.
        ('msodgcidChangeShapeFlowChartExtract', 0x207f), # Change the selected shape to a flowchart extract shape.
        ('msodgcidChangeShapeFlowChartMerge', 0x2080), # Change the selected shape to a flowchart merge shape.
        ('msodgcidChangeShapeFlowChartOnlineStorage', 0x2082), # Change the selected shape to a flowchart stored-data shape.
        ('msodgcidChangeShapeFlowChartMagneticTape', 0x2083), # Change the selected shape to a flowchart sequential-access storage shape.
        ('msodgcidChangeShapeFlowChartMagneticDisk', 0x2084), # Change the selected shape to a flowchart magnetic-disk shape.
        ('msodgcidChangeShapeFlowChartMagneticDrum', 0x2085), # Change the selected shape to a flowchart direct-access storage shape.
        ('msodgcidChangeShapeFlowChartDisplay', 0x2086), # Change the selected shape to a flowchart display shape.
        ('msodgcidChangeShapeFlowChartDelay', 0x2087), # Change the selected shape to a flowchart delay shape.
        ('msodgcidChangeShapeFlowChartAlternateProcess', 0x20b0), # Change the selected shape to a flowchart alternate-process shape.
        ('msodgcidChangeShapeFlowChartOffpageConnector', 0x20b1), # Change the selected shape to a flowchart off-page connector shape.
        ('msodgcidChangeShapeCallout90', 0x20b2), # Change the selected shape to a Line Callout 1 (no border) shape.
        ('msodgcidChangeShapeAccentCallout90', 0x20b3), # Change the selected shape to a Line Callout 1 (accent bar) shape.
        ('msodgcidChangeShapeBorderCallout90', 0x20b4), # Change the selected shape to a Line Callout 1 shape.
        ('msodgcidChangeShapeAccentBorderCallout90', 0x20b5), # Change the selected shape to a Line Callout 1 (border and accent bar) shape.
        ('msodgcidChangeShapeLeftRightUpArrow', 0x20b6), # Change the selected shape to a left-right-up arrow shape.
        ('msodgcidChangeShapeSun', 0x20b7), # Change the selected shape to a sun shape.
        ('msodgcidChangeShapeMoon', 0x20b8), # Change the selected shape to a moon shape.
        ('msodgcidChangeShapeBracketPair', 0x20b9), # Change the selected shape to a double bracket shape.
        ('msodgcidChangeShapeBracePair', 0x20ba), # Change the selected shape to a double brace shape.
        ('msodgcidChangeShapeSeal4', 0x20bb), # Change the selected shape to a 4-point star shape.
        ('msodgcidChangeShapeDoubleWave', 0x20bc), # Change the selected shape to a double wave shape.
    ]

class MSOWRAPMODE(pint.enum, uint4):
    _values_ = [
        ('msowrapSquare', 0x00000000), # Specifies that a line of text will continue on subsequent lines instead of extending into or beyond a margin. This value MAY<103> be used.
        ('msowrapByPoints', 0x00000001), # Specifies a wrapping rule (1) that is equivalent to that of msowrapSquare. This value MAY<104> be used.
        ('msowrapNone', 0x00000002), # Specifies that a line of text will extend into or beyond a margin instead of continuing on subsequent lines. This value MAY<105> be used.
        ('msowrapTopBottom', 0x00000003), # Specifies a wrapping rule (1) that is undefined and MUST be ignored.
        ('msowrapThrough', 0x00000004), # Specifies a wrapping rule (1) that is undefined and MUST be ignored.
    ]

class MSOANCHOR(pint.enum, uint4):
    _values_ = [
        ('msoanchorTop', 0x00000000), # The primary determinant for the placement of the text is that the top of the text coincides with the top internal margin of the text box area.
        ('msoanchorMiddle', 0x00000001), # The primary determinant for the placement of the text is that the vertical center of the text coincides with the vertical midpoint of the internal margins of the text box area.
        ('msoanchorBottom', 0x00000002), # The primary determinant for the placement of the text is that the bottom of the text coincides with the bottom internal margin of the text box area.
        ('msoanchorTopCentered', 0x00000003), # This anchor mode specifies the same vertical placement as that of msoanchorTop. Additionally, the primary determinant for the horizontal placement of the text is that the horizontal center of the text coincides with the horizontal center of the text box area, respecting the specified internal margins.
        ('msoanchorMiddleCentered', 0x00000004), # This anchor mode specifies the same vertical placement as that of msoanchorMiddle. Additionally, the primary determinant for the horizontal placement of the text is that the horizontal center of the text coincides with the horizontal center of the text box area, respecting the specified internal margins.
        ('msoanchorBottomCentered', 0x00000005), # This anchor mode specifies the same vertical placement as that of msoanchorBottom. Additionally, the primary determinant for the horizontal placement of the text is that the horizontal center of the text coincides with the horizontal center of the text box area, respecting the specified internal margins.
        ('msoanchorTopBaseline', 0x00000006), # The primary determinant for the placement of the text is the offset of the baseline of the text from the top internal margin of the text box area. The offset is determined by the host application. This value SHOULD NOT<107> be used. The value msoanchorTop MAY be used instead.
        ('msoanchorBottomBaseline', 0x00000007), # The primary determinant for the placement of the text is the offset of the baseline of the text from the bottom internal margin of the text box area. The offset is determined by the host application. This value SHOULD NOT<108> be used. The value msoanchorBottom MAY be used instead.
        ('msoanchorTopCenteredBaseline', 0x00000008), # This anchor mode specifies the same vertical placement as that of msoanchorTopBaseline. Additionally, the primary determinant for the horizontal placement of the text is that the horizontal center of the text coincides with the horizontal center of the text box area, respecting the specified internal margins. This value SHOULD NOT<109> be used. The value msoanchorTopCentered MAY be used instead.
        ('msoanchorBottomCenteredBaseline', 0x00000009), # This anchor mode specifies the same vertical placement as that of msoanchorBottomBaseline. Additionally, the primary determinant for the horizontal placement of the text is that the horizontal center of the text coincides with the horizontal center of the text box area, respecting the specified internal margins. This value SHOULD NOT<110> be used. The value msoanchorBottomCentered MAY be used instead.
    ]

class MSOTXFL(pint.enum, uint4):
    _values_ = [
        ('msotxflHorzN', 0x00000000), # Character glyphs are oriented such that their tops are closest to the top of the text body container. Subsequent character glyphs are placed to the right of antecedent character glyphs. Subsequent lines of text are placed below antecedent lines of text. This value SHOULD NOT<111> be used.
        ('msotxflTtoBA', 0x00000001), # Character glyphs are oriented such that their tops are closest to the right side of the text body container. Subsequent character glyphs are placed below antecedent character glyphs. Subsequent lines of text are placed to the left of antecedent lines of text. This value MAY<112> be used.
        ('msotxflBtoT', 0x00000002), # Character glyphs are oriented such that their tops are closest to the left side of the text body container. Subsequent character glyphs are placed above antecedent character glyphs. Subsequent lines of text are placed to the right of antecedent lines of text. This value MAY<113> be used.
        ('msotxflTtoBN', 0x00000003), # Character glyphs are oriented such that their tops are closest to the right side of the text body container. Subsequent character glyphs are placed below antecedent character glyphs. Subsequent lines of text are placed to the left of antecedent lines of text. This value MAY<114> be used.
        ('msotxflHorzA', 0x00000004), # Character glyphs are oriented such that their tops are closest to the top of the text body container. Subsequent character glyphs are placed to the right of antecedent character glyphs. Subsequent lines of text are placed below antecedent lines of text. This value SHOULD NOT<115> be used.
        ('msotxflVertN', 0x00000005), # Character glyphs are oriented such that their tops are closest to the right side of the text body container. Subsequent character glyphs are placed below antecedent character glyphs. Subsequent lines of text are placed to the left of antecedent lines of text. This value MAY<116> be used.
    ]

class MSOCDIR(pint.enum, uint4):
    _values_ = [
        ('msocdir0', 0x00000000), # Specifies either no rotation or a direction that is horizontally to the right.
        ('msocdir90', 0x00000001), # Specifies either a 90-degree rotation or a direction that is vertically down.
        ('msocdir180', 0x00000002), # Specifies either a 180-degree rotation or a direction that is horizontally to the left.
        ('msocdir270', 0x00000003), # Specifies either a 270-degree rotation or a direction that is vertically up.
    ]

class MSOTXDIR(pint.enum, uint4):
    _values_ = [
        ('msotxdirLTR', 0x00000000), # Specifies that the text is read from left to right.<117>
        ('msotxdirRTL', 0x00000001), # Specifies that the text is read from right to left.<118>
        ('msotxdirContext', 0x00000002), # Specifies that the direction is determined from the text string. If no associated text string exists, the text SHOULD be read from left to right.
    ]

class MSOBLIPFLAGS(pint.enum, uint4):
    _values_ = [
        ('msoblipflagComment', 0x00000000), # Specifies that the name in the property set designates a comment. This value, msoblipflagFile, and msoblipflagURL are mutually exclusive.
        ('msoblipflagFile', 0x00000001), # Specifies that the name in the property set designates a file name. This value, msoblipflagComment, and msoblipflagURL are mutually exclusive.
        ('msoblipflagURL', 0x00000002), # Specifies that the name in the property set designates a URL. This value, msoblipflagComment, and msoblipflagFile are mutually exclusive.
        ('msoblipflagDoNotSave', 0x00000004), # Specifies that the BLIP data MUST not be embedded on save. If this flag is set, msoblipflagLinkToFile MUST also be set.
        ('msoblipflagLinkToFile', 0x00000008), # Specifies that the BLIP data is linked in the specified URL. If this flag is set, either msoblipflagFile or msoblipflagURL MUST also be set.
    ]

class MSOSHAPEPATH(pint.enum, uint4):
    _values_ = [
        ('msoshapeLines', 0x00000000), # An open path of straight line segments.
        ('msoshapeLinesClosed', 0x00000001), # A closed path of straight line segments.
        ('msoshapeCurves', 0x00000002), # An open path of Bezier curve line segments.
        ('msoshapeCurvesClosed', 0x00000003), # A closed path of Bezier curve line segments.
        ('msoshapeComplex', 0x00000004), # A complex path composed of a combination of multiple types of lines. The pSegmentInfo_complex property of this shape specifies the types of lines that form the path, and that property MUST exist.
    ]

class MSOCXK(pint.enum, uint4):
    _values_ = [
        ('msocxkNone', 0x00000000), # No connection points exist.
        ('msocxkSegments', 0x00000001), # The edit points of the shape are used as connection points.
        ('msocxkCustom', 0x00000002), # A custom array of connection points is used.
        ('msocxkRect', 0x00000003), # The standard four connection points at the midpoints of the top, bottom, left, and right sides are used.
    ]

class MSOFILLTYPE(pint.enum, uint4):
    _values_ = [
        ('msofillSolid', 0x00000000), # A solid fill:
        ('msofillPattern', 0x00000001), # A patterned fill:
        ('msofillTexture', 0x00000002), # A textured fill:
        ('msofillPicture', 0x00000003), # A picture fill:
        ('msofillShade', 0x00000004), # A gradient fill that starts and ends with defined endpoints:
        ('msofillShadeCenter', 0x00000005), # A gradient fill that starts and ends based on the bounds of the shape:
        ('msofillShadeShape', 0x00000006), # A gradient fill that starts on the outline of the shape and ends at a point defined within the shape:
        ('msofillShadeScale', 0x00000007), # A gradient fill that starts on the outline of the shape and ends at a point defined within the shape. The fill angle is scaled by the aspect ratio of the shape:
    ]

class MSODZTYPE(pint.enum, uint4):
    _values_ = [
        ('msodztypeDefault', 0x00000000), # The width and height are ignored, and the shape dimensions are used.
        ('msodztypeA', 0x00000001), # Values are in EMUs.
        ('msodztypeV', 0x00000002), # Values are in pixels.
        ('msodztypeShape', 0x00000003), # Values are of type FixedPoint, as specified in [MS-OSHARED] section 2.2.1.6, and specify fractions of a shape dimension.
        ('msodztypeFixedAspect', 0x00000004), # The aspect ratio of the shape is maintained. The width and height are ignored, and the shape dimensions are used.
        ('msodztypeAFixed', 0x00000005), # Values are in EMUs. The aspect ratio of the shape is maintained.
        ('msodztypeVFixed', 0x00000006), # Values are in pixels. The aspect ratio of the shape is maintained.
        ('msodztypeShapeFixed', 0x00000007), # Values are proportional to the size of the shape. The aspect ratio of the shape is maintained.
        ('msodztypeFixedAspectEnlarge', 0x00000008), # The aspect ratio is maintained, favoring the largest dimension.
        ('msodztypeAFixedBig', 0x00000009), # Values are in EMUs. The aspect ratio is maintained, favoring the largest dimension.
        ('msodztypeVFixedBig', 0x0000000a), # Values are in pixels. The aspect ratio is maintained, favoring the largest dimension.
        ('msodztypeShapeFixedBig', 0x0000000b), # Values are proportional to the size of the shape. The aspect ratio is maintained, favoring the largest dimension.
    ]

class MSOLINETYPE(pint.enum, uint4):
    _values_ = [
        ('msolineSolidType', 0x00000000), # A solid fill:
        ('msolinePattern', 0x00000001), # A patterned fill:
        ('msolineTexture', 0x00000002), # A textured fill:
    ]

class MSOLINESTYLE(pint.enum, uint4):
    _values_ = [
        ('msolineSimple', 0x00000000), # A simple line:
        ('msolineDouble', 0x00000001), # A double line:
        ('msolineThickThin', 0x00000002), # A thick line and a thin line:
        ('msolineThinThick', 0x00000003), # A thin line and a thick line:
        ('msolineTriple', 0x00000004), # A triple line:
    ]

class MSOLINEDASHING(pint.enum, uint4):
    _values_ = [
        ('msolineSolid', 0x00000000), # 1
        ('msolineDashSys', 0x00000001), # 1110
        ('msolineDotSys', 0x00000002), # 10
        ('msolineDashDotSys', 0x00000003), # 111010
        ('msolineDashDotDotSys', 0x00000004), # 11101010
        ('msolineDotGEL', 0x00000005), # 1000
        ('msolineDashGEL', 0x00000006), # 1111000
        ('msolineLongDashGEL', 0x00000007), # 11111111000
        ('msolineDashDotGEL', 0x00000008), # 11110001000
        ('msolineLongDashDotGEL', 0x00000009), # 111111110001000
        ('msolineLongDashDotDotGEL', 0x0000000a), # 1111111100010001000
    ]

class MSOLINEEND(pint.enum, uint4):
    _values_ = [
        ('msolineNoEnd', 0x00000000), # No shape.
        ('msolineArrowEnd', 0x00000001), # A triangular arrow head:
        ('msolineArrowStealthEnd', 0x00000002), # A stealth arrow head:
        ('msolineArrowDiamondEnd', 0x00000003), # A diamond:
        ('msolineArrowOvalEnd', 0x00000004), # An oval:
        ('msolineArrowOpenEnd', 0x00000005), # A line arrow head:
        ('msolineArrowChevronEnd', 0x00000006), # A value that MUST be ignored.
        ('msolineArrowDoubleChevronEnd', 0x00000007), # A value that MUST be ignored.
    ]

class MSOLINEENDWIDTH(pint.enum, uint4):
    _values_ = [
        ('msolineNarrowArrow', 0x00000000), # Narrow:
        ('msolineMediumWidthArrow', 0x00000001), # Medium:
        ('msolineWideArrow', 0x00000002), # Wide:
    ]

class MSOLINEENDLENGTH(pint.enum, uint4):
    _values_ = [
        ('msolineShortArrow', 0x00000000), # Short:
        ('msolineMediumLenArrow', 0x00000001), # Medium:
        ('msolineLongArrow', 0x00000002), # Long:
    ]

class MSOLINEJOIN(pint.enum, uint4):
    _values_ = [
        ('msolineJoinBevel', 0x00000000), # Beveled:
        ('msolineJoinMiter', 0x00000001), # Mitered:
        ('msolineJoinRound', 0x00000002), # Rounded:
    ]

class MSOLINECAP(pint.enum, uint4):
    _values_ = [
        ('msolineEndCapRound', 0x00000000), # A rounded end that protrudes past the line endpoint:
        ('msolineEndCapSquare', 0x00000001), # A square end that protrudes past the line endpoint:
        ('msolineEndCapFlat', 0x00000002), # A flat end that ends at the line endpoint:
    ]

class MSOSHADOWTYPE(pint.enum, uint4):
    _values_ = [
        ('msoshadowOffset', 0x00000000), # Only the offset of the shadow is used:
        ('msoshadowDouble', 0x00000001), # A double shadow is cast. Only the offset of the shadow is used:
        ('msoshadowRich', 0x00000002), # The shadow offset and a transformation is applied to skew the shadow relative to the drawing:
        ('msoshadowShape', 0x00000003), # The shadow offset and a transformation is applied to skew the shadow relative to the shape:
        ('msoshadowDrawing', 0x00000004), # The shadow is cast onto a drawing plane:
        ('msoshadowEmbossOrEngrave', 0x00000005), # A double shadow is cast to create an embossed or engraved appearance.
    ]

class MSOXFORMTYPE(pint.enum, uint4):
    _values_ = [
        ('msoxformAbsolute', 0x00000000), # The perspective transformation is applied in absolute space, centered on the shape.
        ('msoxformShape', 0x00000001), # The perspective transformation is applied to the shape geometry.
        ('msoxformDrawing', 0x00000002), # The perspective transformation is applied in the drawing space.
    ]

class MSO3DRENDERMODE(pint.enum, uint4):
    _values_ = [
        ('msoFullRender', 0x00000000), # Rendering displays a solid shape.
        ('msoWireframe', 0x00000001), # Rendering displays a wireframe shape.
        ('msoBoundingCube', 0x00000002), # Rendering displays the bounding cube that contains the shape.
    ]

class MSOSPT(pint.enum, uint4):
    _values_ = [
        ('msosptNotPrimitive', 0x00000000),
        ('msosptRectangle', 0x00000001),
        ('msosptRoundRectangle', 0x00000002),
        ('msosptEllipse', 0x00000003),
        ('msosptDiamond', 0x00000004),
        ('msosptIsoscelesTriangle', 0x00000005),
        ('msosptRightTriangle', 0x00000006),
        ('msosptParallelogram', 0x00000007),
        ('msosptTrapezoid', 0x00000008),
        ('msosptHexagon', 0x00000009),
        ('msosptOctagon', 0x0000000a),
        ('msosptPlus', 0x0000000b),
        ('msosptStar', 0x0000000c),
        ('msosptArrow', 0x0000000d),
        ('msosptThickArrow', 0x0000000e),
        ('msosptHomePlate', 0x0000000f),
        ('msosptCube', 0x00000010),
        ('msosptBalloon', 0x00000011),
        ('msosptSeal', 0x00000012),
        ('msosptArc', 0x00000013),
        ('msosptLine', 0x00000014),
        ('msosptPlaque', 0x00000015),
        ('msosptCan', 0x00000016),
        ('msosptDonut', 0x00000017),
        ('msosptTextSimple', 0x00000018),
        ('msosptTextOctagon', 0x00000019),
        ('msosptTextHexagon', 0x0000001a),
        ('msosptTextCurve', 0x0000001b),
        ('msosptTextWave', 0x0000001c),
        ('msosptTextRing', 0x0000001d),
        ('msosptTextOnCurve', 0x0000001e),
        ('msosptTextOnRing', 0x0000001f),
        ('msosptStraightConnector1', 0x00000020),
        ('msosptBentConnector2', 0x00000021),
        ('msosptBentConnector3', 0x00000022),
        ('msosptBentConnector4', 0x00000023),
        ('msosptBentConnector5', 0x00000024),
        ('msosptCurvedConnector2', 0x00000025),
        ('msosptCurvedConnector3', 0x00000026),
        ('msosptCurvedConnector4', 0x00000027),
        ('msosptCurvedConnector5', 0x00000028),
        ('msosptCallout1', 0x00000029),
        ('msosptCallout2', 0x0000002a),
        ('msosptCallout3', 0x0000002b),
        ('msosptAccentCallout1', 0x0000002c),
        ('msosptAccentCallout2', 0x0000002d),
        ('msosptAccentCallout3', 0x0000002e),
        ('msosptBorderCallout1', 0x0000002f),
        ('msosptBorderCallout2', 0x00000030),
        ('msosptBorderCallout3', 0x00000031),
        ('msosptAccentBorderCallout1', 0x00000032),
        ('msosptAccentBorderCallout2', 0x00000033),
        ('msosptAccentBorderCallout3', 0x00000034),
        ('msosptRibbon', 0x00000035),
        ('msosptRibbon2', 0x00000036),
        ('msosptChevron', 0x00000037),
        ('msosptPentagon', 0x00000038),
        ('msosptNoSmoking', 0x00000039),
        ('msosptSeal8', 0x0000003a),
        ('msosptSeal16', 0x0000003b),
        ('msosptSeal32', 0x0000003c),
        ('msosptWedgeRectCallout', 0x0000003d),
        ('msosptWedgeRRectCallout', 0x0000003e),
        ('msosptWedgeEllipseCallout', 0x0000003f),
        ('msosptWave', 0x00000040),
        ('msosptFoldedCorner', 0x00000041),
        ('msosptLeftArrow', 0x00000042),
        ('msosptDownArrow', 0x00000043),
        ('msosptUpArrow', 0x00000044),
        ('msosptLeftRightArrow', 0x00000045),
        ('msosptUpDownArrow', 0x00000046),
        ('msosptIrregularSeal1', 0x00000047),
        ('msosptIrregularSeal2', 0x00000048),
        ('msosptLightningBolt', 0x00000049),
        ('msosptHeart', 0x0000004a),
        ('msosptPictureFrame', 0x0000004b),
        ('msosptQuadArrow', 0x0000004c),
        ('msosptLeftArrowCallout', 0x0000004d),
        ('msosptRightArrowCallout', 0x0000004e),
        ('msosptUpArrowCallout', 0x0000004f),
        ('msosptDownArrowCallout', 0x00000050),
        ('msosptLeftRightArrowCallout', 0x00000051),
        ('msosptUpDownArrowCallout', 0x00000052),
        ('msosptQuadArrowCallout', 0x00000053),
        ('msosptBevel', 0x00000054),
        ('msosptLeftBracket', 0x00000055),
        ('msosptRightBracket', 0x00000056),
        ('msosptLeftBrace', 0x00000057),
        ('msosptRightBrace', 0x00000058),
        ('msosptLeftUpArrow', 0x00000059),
        ('msosptBentUpArrow', 0x0000005a),
        ('msosptBentArrow', 0x0000005b),
        ('msosptSeal24', 0x0000005c),
        ('msosptStripedRightArrow', 0x0000005d),
        ('msosptNotchedRightArrow', 0x0000005e),
        ('msosptBlockArc', 0x0000005f),
        ('msosptSmileyFace', 0x00000060),
        ('msosptVerticalScroll', 0x00000061),
        ('msosptHorizontalScroll', 0x00000062),
        ('msosptCircularArrow', 0x00000063),
        ('msosptNotchedCircularArrow', 0x00000064),
        ('msosptUturnArrow', 0x00000065),
        ('msosptCurvedRightArrow', 0x00000066),
        ('msosptCurvedLeftArrow', 0x00000067),
        ('msosptCurvedUpArrow', 0x00000068),
        ('msosptCurvedDownArrow', 0x00000069),
        ('msosptCloudCallout', 0x0000006a),
        ('msosptEllipseRibbon', 0x0000006b),
        ('msosptEllipseRibbon2', 0x0000006c),
        ('msosptFlowChartProcess', 0x0000006d),
        ('msosptFlowChartDecision', 0x0000006e),
        ('msosptFlowChartInputOutput', 0x0000006f),
        ('msosptFlowChartPredefinedProcess', 0x00000070),
        ('msosptFlowChartInternalStorage', 0x00000071),
        ('msosptFlowChartDocument', 0x00000072),
        ('msosptFlowChartMultidocument', 0x00000073),
        ('msosptFlowChartTerminator', 0x00000074),
        ('msosptFlowChartPreparation', 0x00000075),
        ('msosptFlowChartManualInput', 0x00000076),
        ('msosptFlowChartManualOperation', 0x00000077),
        ('msosptFlowChartConnector', 0x00000078),
        ('msosptFlowChartPunchedCard', 0x00000079),
        ('msosptFlowChartPunchedTape', 0x0000007a),
        ('msosptFlowChartSummingJunction', 0x0000007b),
        ('msosptFlowChartOr', 0x0000007c),
        ('msosptFlowChartCollate', 0x0000007d),
        ('msosptFlowChartSort', 0x0000007e),
        ('msosptFlowChartExtract', 0x0000007f),
        ('msosptFlowChartMerge', 0x00000080),
        ('msosptFlowChartOfflineStorage', 0x00000081),
        ('msosptFlowChartOnlineStorage', 0x00000082),
        ('msosptFlowChartMagneticTape', 0x00000083),
        ('msosptFlowChartMagneticDisk', 0x00000084),
        ('msosptFlowChartMagneticDrum', 0x00000085),
        ('msosptFlowChartDisplay', 0x00000086),
        ('msosptFlowChartDelay', 0x00000087),
        ('msosptTextPlainText', 0x00000088),
        ('msosptTextStop', 0x00000089),
        ('msosptTextTriangle', 0x0000008a),
        ('msosptTextTriangleInverted', 0x0000008b),
        ('msosptTextChevron', 0x0000008c),
        ('msosptTextChevronInverted', 0x0000008d),
        ('msosptTextRingInside', 0x0000008e),
        ('msosptTextRingOutside', 0x0000008f),
        ('msosptTextArchUpCurve', 0x00000090),
        ('msosptTextArchDownCurve', 0x00000091),
        ('msosptTextCircleCurve', 0x00000092),
        ('msosptTextButtonCurve', 0x00000093),
        ('msosptTextArchUpPour', 0x00000094),
        ('msosptTextArchDownPour', 0x00000095),
        ('msosptTextCirclePour', 0x00000096),
        ('msosptTextButtonPour', 0x00000097),
        ('msosptTextCurveUp', 0x00000098),
        ('msosptTextCurveDown', 0x00000099),
        ('msosptTextCascadeUp', 0x0000009a),
        ('msosptTextCascadeDown', 0x0000009b),
        ('msosptTextWave1', 0x0000009c),
        ('msosptTextWave2', 0x0000009d),
        ('msosptTextWave3', 0x0000009e),
        ('msosptTextWave4', 0x0000009f),
        ('msosptTextInflate', 0x000000a0),
        ('msosptTextDeflate', 0x000000a1),
        ('msosptTextInflateBottom', 0x000000a2),
        ('msosptTextDeflateBottom', 0x000000a3),
        ('msosptTextInflateTop', 0x000000a4),
        ('msosptTextDeflateTop', 0x000000a5),
        ('msosptTextDeflateInflate', 0x000000a6),
        ('msosptTextDeflateInflateDeflate', 0x000000a7),
        ('msosptTextFadeRight', 0x000000a8),
        ('msosptTextFadeLeft', 0x000000a9),
        ('msosptTextFadeUp', 0x000000aa),
        ('msosptTextFadeDown', 0x000000ab),
        ('msosptTextSlantUp', 0x000000ac),
        ('msosptTextSlantDown', 0x000000ad),
        ('msosptTextCanUp', 0x000000ae),
        ('msosptTextCanDown', 0x000000af),
        ('msosptFlowChartAlternateProcess', 0x000000b0),
        ('msosptFlowChartOffpageConnector', 0x000000b1),
        ('msosptCallout90', 0x000000b2),
        ('msosptAccentCallout90', 0x000000b3),
        ('msosptBorderCallout90', 0x000000b4),
        ('msosptAccentBorderCallout90', 0x000000b5),
        ('msosptLeftRightUpArrow', 0x000000b6),
        ('msosptSun', 0x000000b7),
        ('msosptMoon', 0x000000b8),
        ('msosptBracketPair', 0x000000b9),
        ('msosptBracePair', 0x000000ba),
        ('msosptSeal4', 0x000000bb),
        ('msosptDoubleWave', 0x000000bc),
        ('msosptActionButtonBlank', 0x000000bd),
        ('msosptActionButtonHome', 0x000000be),
        ('msosptActionButtonHelp', 0x000000bf),
        ('msosptActionButtonInformation', 0x000000c0),
        ('msosptActionButtonForwardNext', 0x000000c1),
        ('msosptActionButtonBackPrevious', 0x000000c2),
        ('msosptActionButtonEnd', 0x000000c3),
        ('msosptActionButtonBeginning', 0x000000c4),
        ('msosptActionButtonReturn', 0x000000c5),
        ('msosptActionButtonDocument', 0x000000c6),
        ('msosptActionButtonSound', 0x000000c7),
        ('msosptActionButtonMovie', 0x000000c8),
        ('msosptHostControl', 0x000000c9),
        ('msosptTextBox', 0x000000ca),
    ]

class MSOCXSTYLE(pint.enum, uint4):
    _values_ = [
        ('msocxstyleStraight', 0x00000000), #A straight connector.
        ('msocxstyleBent', 0x00000001), # An elbow-shaped connector.
        ('msocxstyleCurved', 0x00000002), # A curved connector.
        ('msocxstyleNone', 0x00000003), # No connector.
    ]

class MSOBWMODE(pint.enum, uint4):
    _values_ = [
        ('msobwColor', 0x00000000), # The object is rendered with normal coloring.
        ('msobwAutomatic', 0x00000001), # The object is rendered with automatic coloring.
        ('msobwGrayScale', 0x00000002), # The object is rendered with gray coloring.
        ('msobwLightGrayScale', 0x00000003), # The object is rendered with light gray coloring.
        ('msobwInverseGray', 0x00000004), # The object is rendered with inverse gray coloring.
        ('msobwGrayOutline', 0x00000005), # The object is rendered with gray and white coloring.
        ('msobwBlackTextLine', 0x00000006), # The object is rendered with black and gray coloring.
        ('msobwHighContrast', 0x00000007), # The object is rendered with black and white coloring.
        ('msobwBlack', 0x00000008), # The object is rendered only with black coloring.
        ('msobwWhite', 0x00000009), # The object is rendered with white coloring.
        ('msobwDontShow', 0x0000000a), # The object is not rendered.
    ]

class MSODGMT(pint.enum, uint4):
    _values_ = [
        ('msodgmtCanvas', 0x00000000), # A drawing area for ink and shapes.
        ('msodgmtOrgChart', 0x00000001), # An organizational chart diagram:
        ('msodgmtRadial', 0x00000002), # A diagram that shows the relationships to a central entity:
        ('msodgmtCycle', 0x00000003), # A diagram that shows a cyclical process:
        ('msodgmtStacked', 0x00000004), # A pyramid diagram:
        ('msodgmtVenn', 0x00000005), # A Venn diagram:
        ('msodgmtBullsEye', 0x00000006 ), # A diagram that has concentric rings:
    ]

class MSODGSLK(pint.enum, uint4):
    _fields_ = [
        ('msodgslkNormal', 0x00000000), # The default state.
        ('msodgslkRotate', 0x00000001), # Ready to rotate.
        ('msodgslkReshape', 0x00000002), # Ready to change the curvature of line shapes.
        ('msodgslkCrop', 0x00000007), # Ready to crop the picture.
    ]

class MSODGMLO(pint.enum, uint4):
    _values_ = [
        ('msodgmloOrgChartStd', 0x00000000), # Organizational chart:
        ('msodgmloOrgChartBothHanging', 0x00000001), # Organizational chart with child nodes hanging both left and right:
        ('msodgmloOrgChartRightHanging', 0x00000002), # Organizational chart with child nodes hanging to the right:
        ('msodgmloOrgChartLeftHanging', 0x00000003), # Organizational chart with child nodes hanging to the left:
        ('msodgmloCycleStd', 0x00000004), # Cycle diagram:
        ('msodgmloRadialStd', 0x00000005), # Radial diagram:
        ('msodgmloStackedStd', 0x00000006), # Pyramid diagram:
        ('msodgmloVennStd', 0x00000007), # Venn diagram:
        ('msodgmloBullEyeStd', 0x00000008), # Target diagram:
    ]

class MSOPATHTYPE(pint.enum, uint4):
    _values_ = [
        ('msopathLineTo', 0x00000000), # For each POINT record in the array, add a straight line segment from the current ending POINT to the new POINT. The number of POINT values to process equals the number of segments. The last POINT in the array becomes the new ending POINT.
        ('msopathCurveTo', 0x00000001), # For each segment, three POINT values are used to draw a cubic Bezier curve. The first two POINT values are control POINT values, and the last POINT is the new ending POINT. The number of POINT values consumed is three times the number of segments.
        ('msopathMoveTo', 0x00000002), # Start a new sub-path by using a single POINT. The starting POINT becomes the current ending POINT. The value of the segment field MUST be zero. The number of POINT values used is one.
        ('msopathClose', 0x00000003), # If the starting POINT and the ending POINT are not the same, a single straight line is drawn to connect the starting POINT and the ending POINT of the path. The number of segments MUST be one. The number of POINT values used is zero.
        ('msopathEnd', 0x00000004), # The end of the current path. All consecutive lines and fill values MUST be drawn before any subsequent path or line is drawn. The number of segments MUST be zero. The number of POINT
    ]

class MSOPATHESCAPE(pint.enum, uint4):
    _values_ = [
        ('msopathEscapeExtension', 0x00000000), # This value adds additional POINT values to the escape code that follows msopathEscapeExtension.
        ('msopathEscapeAngleEllipseTo', 0x00000001), # The first POINT specifies the center of the ellipse. The second POINT specifies the starting radius in the x value and the ending radius in the y value. The third POINT specifies the starting angle in the x value and the ending angle in the y value. Angles are in degrees. The number of ellipse segments drawn equals the number of segments divided by three.
        ('msopathEscapeAngleEllipse', 0x00000002), # The first POINT specifies the center of the ellipse. The second POINT specifies the starting radius in the x value and the ending radius in the y valye. The third POINT specifies the starting angle in the x value and the ending angle in the y value. Angles are in degrees. The number of ellipse segments drawn equals the number of segments divided by three. The first POINT of the ellipse becomes the first POINT of a new path.
        ('msopathEscapeArcTo', 0x00000003), # The first two POINT values specify the bounding rectangle of the ellipse. The second two POINT values specify the radial vectors for the ellipse. The radial vectors are cast from the center of the bounding rectangle. The path starts at the POINT where the first radial vector intersects the bounding rectangle and goes to the POINT where the second radial vector intersects the bounding rectangle. The drawing direction is always counterclockwise. If the path has already been started, a line is drawn from the last POINT to the starting POINT of the arc; otherwise, a new path is started. The number of arc segments drawn equals the number of segments divided by four.
        ('msopathEscapeArc', 0x00000004), # The first two POINT values specify the bounding rectangle of the ellipse. The second two POINT values specify the radial vectors for the ellipse. The radial vectors are cast from the center of the bounding rectangle. The path starts at the POINT where the first radial vector intersects the bounding rectangle and goes to the POINT where the second radial vector intersects the bounding rectangle. The drawing direction is always counterclockwise. The number of arc segments drawn equals the number of segments divided by four.
        ('msopathEscapeClockwiseArcTo', 0x00000005), # The first two POINT values specify the bounding rectangle of the ellipse. The second two POINT values specify the radial vectors for the ellipse. The radial vectors are cast from the center of the bounding rectangle. The path starts at the POINT where the first radial vector intersects the bounding rectangle and goes to the POINT where the second radial vector intersects the bounding rectangle. The drawing direction is always clockwise. If the path has already been started, a line is drawn from the last POINT to the starting POINT of the arc; otherwise, a new path is started. The number of arc segments drawn equals the number of segments divided by four.
        ('msopathEscapeClockwiseArc', 0x00000006), # The first two POINT values specify the bounding rectangle of the ellipse. The second two POINT values specify the radial vectors for the ellipse. The radial vectors are cast from the center of the bounding rectangle. The path starts at the POINT where the first radial vector intersects the bounding rectangle and goes to the POINT where the second radial vector intersects the bounding rectangle. The drawing direction is always clockwise. The number of arc segments drawn equals the number of segments divided by four. This escape code always starts a new path.
        ('msopathEscapeEllipticalQuadrantX', 0x00000007), # This value adds an ellipse to the path from the current POINT to the next POINT. The ellipse is drawn as a quadrant that starts as a tangent to the x-axis. Multiple elliptical quadrants are joined by a straight line. The number of elliptical quadrants drawn equals the number of segments.
        ('msopathEscapeEllipticalQuadrantY', 0x00000008), # This value adds an ellipse to the path from the current POINT to the next POINT. The ellipse is drawn as a quadrant that starts as a tangent to the y-axis. Multiple elliptical quadrants are joined by a straight line. The number of elliptical quadrants drawn equals the number of segments.
        ('msopathEscapeQuadraticBezier', 0x00000009), # Each POINT defines a control point for a quadratic Bezier curve. The number of control POINT values is defined by the segments property of the containing MSOPATHESCAPEINFO record.
        ('msopathEscapeNoFill', 0x0000000a), # The path is not to be filled, even if it is passed to a rendering routine that would normally fill the path.
        ('msopathEscapeNoLine', 0x0000000b), # The path is not to be drawn, even if it passed to a rendering routine that would normally draw the path.
        ('msopathEscapeAutoLine', 0x0000000c), # For Bezier curve editing, the vertex joints are calculated, are of equal length, and are collinear. The segment after the POINT is a line. The tangent is not visible.
        ('msopathEscapeAutoCurve', 0x0000000d), # For Bezier curve editing, the vertex joints are calculated, are of equal length, and are collinear. The segment after the POINT is a curve. The tangent is not visible.
        ('msopathEscapeCornerLine', 0x0000000e), # For Bezier curve editing, the vertex joints are not calculated, are not of equal lengths and are not collinear. The segment after the POINT is a line. The tangent is visible.
        ('msopathEscapeCornerCurve', 0x0000000f), # For Bezier curve editing, the vertex joints are not calculated, are not of equal length, and are not collinear. The segment after the POINT is a curve. The tangent is visible.
        ('msopathEscapeSmoothLine', 0x00000010), # For Bezier curve editing, the vertex joints are not calculated, are not of equal length, and are not collinear. The segment after the POINT is a line. The tangent is visible.
        ('msopathEscapeSmoothCurve', 0x00000011), # For Bezier curve editing, the vertex joints are not calculated, are not of equal length, and are not collinear. The segment after the POINT is a curve. The tangent is visible.
        ('msopathEscapeSymmetricLine', 0x00000012), # For Bezier curve editing, the vertex joints are not calculated, are of equal length, and are not collinear. The segment after the POINT is a line. The tangent is visible.
        ('msopathEscapeSymmetricCurve', 0x00000013), # For Bezier curve editing the vertex joints are not calculated, are of equal length, and are not collinear. The segment after the POINT is a curve. The tangent is visible.
        ('msopathEscapeFreeform', 0x00000014), # For Bezier curve editing, the vertex joints are calculated, are of equal length, and are collinear. The tangent is not visible.
        ('msopathEscapeFillColor', 0x00000015), # This value sets a new fill color. A single POINT is used to represent the colors. The x value is an OfficeArtCOLORREF record that specifies the new foreground color. The y value is an OfficeArtCOLORREF that specifies the new background color.
        ('msopathEscapeLineColor', 0x00000016), # This value sets a new line drawing color. A single POINT is used to represent the colors. The x value is an OfficeArtCOLORREF that specifies the new foreground color. The y value is an OfficeArtCOLORREF that specifies the new background color.
    ]

## record types from [MS-OART]
@FT_OfficeArtSp.define
class OfficeArtSpContainer(RecordContainer):
    # PST_ShapeContainer
    type = 15,0x000

#@FT_msofbtChildAnchor.define
#class OfficeArtClientAnchorChart(RecordContainer):
#    type = 0,0x000

#@FT_msofbtClientData.define
#class OfficeArtClientData(RecordContainer):
#    # PST_ShapeClientContainer
#    type = 15,0x000

@FT_OfficeArtSolver.define
class OfficeArtSolverContainer(RecordContainer):
    type = 15,None      # OfficeArtSolverContainerFileBlock records

@FT_OfficeArtFSP.define
class OfficeArtFSP(pstruct.type):
    type = 2,None       # MSOPT enumeration value
    class _flags(pbinary.flags):
        _fields_ = R([
            (1,'fGroup'),
            (1,'fChild'),
            (1,'fPatriarch'),
            (1,'fDeleted'),
            (1,'fOleShape'),
            (1,'fHaveMaster'),
            (1,'fFlipH'),
            (1,'fFlipV'),
            (1,'fConnector'),
            (1,'fHaveAnchor'),
            (1,'fBackground'),
            (1,'fHaveSpt'),
            (20,'unused1'),
        ])

    _fields_ = [
        (MSOSPID, 'spid'),
        (_flags, 'f')
    ]

@FT_OfficeArtDgg.define
class OfficeArtDggContainer(RecordContainer):
    type = 15, 0x000

@FT_OfficeArtDg.define
class OfficeArtDgContainer(RecordContainer):
    # PST_DrawingContainer
    type = 15,0x000

@FT_OfficeArtSpgr.define
class OfficeArtSpgrContainer(RecordContainer):
    # PST_GroupShapeContainer
    type = 15,0x000

@FT_OfficeArtBlipDIB.define
class OfficeArtBlipDIB_Single(pstruct.type):
    type = 0,0x7a8
    _fields_ = [
        (dyn.block(16), 'rgbUid1'),
        (pint.uint8_t, 'tag'),
        (dyn.block(0), 'BLIPFileData'), # FIXME: this isn't right..
    ]

@FT_OfficeArtBlipDIB.define
class OfficeArtBlipDIB_Double(pstruct.type):
    type = 0,0x7a9
    _fields_ = [
        (dyn.block(16), 'rgbUid1'),
        (dyn.block(16), 'rgbUid2'),
        (pint.uint8_t, 'tag'),
        (dyn.block(0), 'BLIPFileData'), # FIXME: this isn't right..
    ]

@FT_OfficeArtFDG.define
class OfficeArtFDG(pstruct.type):
    type = 0,None       # drawing identifier
    _fields_ = [(pint.uint32_t,'csp'),(MSOSPID, 'spidCur')]

@FT_OfficeArtFSPGR.define
class OfficeArtFSPGR(pstruct.type):
    type = 1,0x000
    _fields_ = [
        (pint.int32_t,'xLeft'),
        (pint.int32_t,'yTop'),
        (pint.int32_t,'xRight'),
        (pint.int32_t,'yBottom'),
    ]

## ripped from OfficeDrawing97-2007BinaryFormatSpecification.pdf
@RT_TimeExtTimeNodeContainer.define  # FIXME
class msofbtExtTimeNodeContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeConditionContainer.define  # FIXME
class msofbtTimeConditionContainer(RecordContainer):
    type = 15,None

@RT_TimeAnimateBehaviorContainer.define     # FIXME
class msofbtTimeAnimateBehaviorContainer(RecordContainer):
    type = 15,None

@RT_TimeColorBehaviorContainer.define   # FIXME
class msofbtTimeColorBehaviorContainer(RecordContainer):
    type = 15,None

class msofbtTimeVariant(pstruct.type):
    def __Value(self):
        t = int(self['Type'].li)
        if t == -1:
            return dyn.block(0)
        elif t == 0:
            return pint.uint8_t
        elif t == 1:
            return pint.int32_t
        elif t == 2:
            return pfloat.double
        elif t == 3:
            return pstr.szwstring

        return dyn.block(0)

    _fields_ = [
        (pint.int8_t, 'Type'),
        (__Value, 'Value'),
    ]

class msofbtTimeAnimationValue(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Time'),
        (msofbtTimeVariant, 'Value'),
        (pstr.szwstring, 'Formula'),
    ]

@RT_TimeVariantList.define  # FIXME
class msofbtTimeVariantList(parray.block):
    type = 0,None
    _object_ = msofbtTimeAnimationValue

@RT_TimeCondition.define    # FIXME
class msofbtTimeCondition(pstruct.type):
    type = 0,None   # ConditionType

    class __triggerType(pint.enum, pint.uint32_t):
        _values_ = [
            ('totNone', 0),
            ('totVisualElement', 1),
            ('totTimeNode', 2),
            ('totRuntimeNodeRef', 3),
            ('TriggerObjectType_MaxEnumIDs', 4),
        ]

    class __event(pint.enum, pint.uint32_t):
        _values_ = [
            ('totNone', 0),
            ('totOnBegin', 1),
            ('totOnEnd', 2),
            ('totBegin', 3),
            ('totEnd', 4),
            ('totOnClick', 5),
            ('totOnDoubleclick', 6),
            ('totOnMouseOver', 7),
            ('totOnMouseOut', 8),
            ('totOnNext', 9),
            ('totOnPrev', 10),
            ('totOnStopAudio', 11),
            ('TriggerEventType_MaxEnumIDs', 12),
        ]

    _fields_ = [
        (__triggerType, 'triggerType'),
        (__event, 'event'),
        (pint.uint32_t, 'id'),
        (pint.int32_t, 'delay'),
    ]

@RT_TimeSetBehaviorContainer.define     # FIXME
class msofbtTimeSetBehaviorContainer(RecordContainer):
    type = 15,None

@RT_TimePropertyList.define # FIXME
class msofbtTimePropertyList(RecordContainer):
    type = 15,None

#@FT_msofbtTimeSetBehaviorContainer.define  # FIXME
#class msofbtTimeSetBehaviorContainer(RecordContainer):
#    type = 15,None

@RT_TimeEffectBehaviorContainer.define  # FIXME
class msofbtTimeEffectBehaviorContainer(RecordContainer):
    type = 15,None

@RT_TimeBehaviorContainer.define    # FIXME
class msofbtTimeBehaviorContainer(RecordContainer):
    type = 15,None

@RT_TimeClientVisualElement.define  # FIXME
class msofbtClientVisualElement(RecordContainer):
    type = 15,None   # list of msofbtTimeVariantRecords

@RT_TimeEffectBehavior.define   # FIXME
class msofbtTimeEffectBehavior(pstruct.type):
    type = 0,None
    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'taetTransition'),
    ]

@RT_TimeVariant.define  # FIXME
class msofbtTimeVariant(pstruct.type):
    type = 0,None

    def __Value(self):
        n = int(self['Type'].li)
        if n == 0:
            return pint.uint32_t
        if n == 1:
            return pint.uint32_t
        if n == 2:
            return pfloat.double
        if n == 3:
            return pstr.szwstring
        if n == 0xff:
            return dyn.block(0)

#        print('unknown type {:s}'.format(n))
#        print(hex(self.getoffset()),getstringpath(self))
        return pint.uint32_t

    _fields_ = [
        (pint.uint8_t, 'Type'),
        (__Value, 'Value'),
    ]

@RT_TimeBehavior.define # FIXME
class msofbtTimeBehavior(pstruct.type):
    type = 0,None

    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'tbaddAdditive'),
        (pint.uint32_t, 'tbaccAccmulate'),
        (pint.uint32_t, 'tbbtTransformType'),
    ]

# Office art property records
class OfficeArtRGFOPTE(pstruct.type):
    def __rgfopt(self):
        try:
            p = self.getparent(type=RecordGeneral)
            _,count = p['header'].Instance()
        except ptypes.error.ItemNotFoundError:
            count = 0
        return dyn.array(OfficeArtFOPTE, count)

    class complexData(parray.type):
        def _object_(self):
            if len(self.value) == 0:
                res = self.getparent(OfficeArtRGFOPTE)
                rgfopte = res['rgfopte'].li
                state = ((i,pr) for i,pr in enumerate(rgfopte) if pr['opid'].li['fComplex'])
                self.__state = state

            index,prop = self.__state.next()
            #t = prop['op'].complex() if hasattr(prop['op'],'complex') else dyn.block(prop['op'].int())
            t = dyn.block(prop['op'].int())
            return dyn.clone(t, Property=property(lambda s:prop))

    def __complexData(self):
        rgfopte = self['rgfopte'].li
        calculatedSize = sum(x['op'].li.int() for x in rgfopte if x['opid'].li['fComplex'])
        realSize = self.blocksize() - self['rgfopte'].li.size()
        if calculatedSize > realSize:
            ptypes.Config.log.warn("OfficeArtRGFOPTE.complexData : calculated size of complexData is larger than available : {:x} > {:x}".format(calculatedSize,realSize))
            return dyn.block(realSize)
        return dyn.clone(self.complexData, length=sum(x['opid']['fComplex'] for x in rgfopte))

    _fields_ = [
        (__rgfopt, 'rgfopte'),
        (__complexData, 'complexData'),
    ]

@FT_OfficeArtFOPT.define
class OfficeArtFOPT(OfficeArtRGFOPTE):
    type = 3,None           # Number of properties in the table

@FT_OfficeArtSecondaryFOPT.define
class OfficeArtSecondaryFOPT(OfficeArtRGFOPTE):
    type = 3,None           # Number of properties in the table

@FT_OfficeArtTertiaryFOPT.define
class OfficeArtTertiaryFOPT(OfficeArtRGFOPTE):
    type = 3,None           # Number of properties in the table

@FT_OfficeArtBlipEMF.define
class OfficeArtBlipEMF(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x3d4:50, 0x3d5:66}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipWMF.define
class OfficeArtBlipWMF(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x216:50, 0x217:66}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipPICT.define
class OfficeArtBlipPICT(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x542:50, 0x543:66}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipJPEG.define
class OfficeArtBlipJPEG(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x46a:17, 0x46b:33, 0x6e2:17, 0x6e3:33}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipPNG.define
class OfficeArtBlipPNG(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x6e0:17, 0x6e1:33}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipDIB.define
class OfficeArtBlipDIB(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x7a8:17, 0x7a9:33}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

@FT_OfficeArtBlipTIFF.define
class OfficeArtBlipTIFF(pstruct.type):
    type = 0,None
    def __BLIPFileData(self):
        p = self.getparent(type=RecordGeneral)
        length = p['header']['Length'].int()
        _,instance = p['header'].Instance()
        uid = {0x6e4:17, 0x6e5:33}
        return dyn.block(length - uid[instance])

    _fields_ = [
        (MD4, 'rgbUid1'),
        (MD4, 'rgbUid2'),
        (ubyte1, 'tag'),
        (__BLIPFileData, 'BLIPFileData'),
    ]

## OfficeArt Properties
# Shape
@OfficeArtFOPTEOP.define
class hspMaster(MSOSPID):
    type = 0x0301

@OfficeArtFOPTEOP.define
class cxstyle(MSOCXSTYLE):
    type = 0x0303

@OfficeArtFOPTEOP.define
class bWMode(MSOBWMODE):
    type = 0x0304

@OfficeArtFOPTEOP.define
class bWModePureBW(MSOBWMODE):
    type = 0x0305

@OfficeArtFOPTEOP.define
class bWModeBW(MSOBWMODE):
    type = 0x0306

@OfficeArtFOPTEOP.define
class idDiscussAnchor(uint4):
    type = 0x0307

@OfficeArtFOPTEOP.define
class dgmLayout(MSODGMLO):
    type = 0x0309

@OfficeArtFOPTEOP.define
class dgmNodeKind(pint.enum, uint4):
    type = 0x030a
    _values_ = [
        ('dgmnkNode', 0x00000000),
        ('dgmnkRoot', 0x00000001),
        ('dgmnkAssistant', 0x00000002),
        ('dgmnkCoWorker', 0x00000003),
        ('dgmnkSubordinate', 0x00000004),
        ('dgmnkAuxNode', 0x00000005),
        ('dgmnkNil', 0x0000ffff),
    ]

@OfficeArtFOPTEOP.define
class dgmLayoutMRU(MSODGMLO):
    type = 0x030b

@OfficeArtFOPTEOP.define
class equationXML(uint4):
    type = 0x030c
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class shapeBooleanProperties(pbinary.flags):
    type = 0x033f
    _fields_ = R([
        (1, 'fBackground'),
        (1, 'reserved1'),
        (1, 'fInitiator'),
        (1, 'fLockShapeType'),
        (1, 'fPreferRelativeResize'),
        (1, 'fOleIcon'),
        (1, 'fFlipVOverride'),
        (1, 'fFlipHOverride'),
        (1, 'fPolicyBarcode'),
        (1, 'fPolicyLabel'),
        (1, 'unused1'),
        (1, 'unused2'),
        (4, 'unused3'),
        (1, 'fUsefBackground'),
        (1, 'unused4'),
        (1, 'fUsefInitiator'),
        (1, 'fUseLockShapeType'),
        (1, 'fUsefPreferRelativeResize'),
        (1, 'fUsefOleIcon'),
        (1, 'fUsefFlipVOverride'),
        (1, 'fUsefFlipHOverride'),
        (1, 'fUsefPolicyBarcode'),
        (1, 'fUsefPolicyLabel'),
        (1, 'unused5'),
        (1, 'unused6'),
        (4, 'unused7'),
    ])

# Callout
@OfficeArtFOPTEOP.define
class unused832(sint4):
    type = 0x0340

@OfficeArtFOPTEOP.define
class dxyCalloutGap(sint4):
    type = 0x0341

@OfficeArtFOPTEOP.define
class spcoa(pint.enum, sint4):
    type = 0x0342
    _values_ = [
        ('msospcoaAny', 0x00000000), # The callout is drawn according to its list of vertices.
        ('msospcoa30', 0x00000001), # The callout is drawn at a 30-degree angle.
        ('msospcoa45', 0x00000002), # The callout is drawn at a 45-degree angle.
        ('msospcoa60', 0x00000003), # The callout is drawn at a 60-degree angle.
        ('msospcoa90', 0x00000004), # The callout is drawn vertically.
        ('msospcoa0', 0x00000005), # The callout is drawn horizontally.
    ]

@OfficeArtFOPTEOP.define
class spcod(pint.enum, sint4):
    type = 0x0343
    _values_ = [
        ('msospcodTop', 0x00000000), # This callout connects to the top of the callout box.
        ('msospcodCenter', 0x00000001), # This callout connects to the callout box at the midpoint of its top and bottom coordinates.
        ('msospcodBottom', 0x00000002), # This callout connects to the bottom of the callout box.
        ('msospcodSpecified', 0x00000003), # This callout connects to the callout box as defined by the dxyCalloutDropSpecified property.
    ]

@OfficeArtFOPTEOP.define
class dxyCalloutDropSpecified(pint.enum, sint4):
    type = 0x0344

@OfficeArtFOPTEOP.define
class dxyCalloutLengthSpecified(pint.enum, sint4):
    type = 0x0345

@OfficeArtFOPTEOP.define
class CalloutBooleanProperties(pbinary.flags):
    type = 0x037f
    _fields_ = R([
        (1, 'fCalloutLengthSpecified'),
        (1, 'fCalloutDropAuto'),
        (1, 'fCalloutMinusY'),
        (1, 'fCalloutMinusX'),
        (1, 'fCalloutTextBorder'),
        (1, 'fCalloutAccentBar'),
        (1, 'fCallout'),
        (9, 'unused1'),
        (1, 'fUsefCalloutLengthSpecified'),
        (1, 'fUsefCalloutDropAuto'),
        (1, 'fUsefCalloutMinusY'),
        (1, 'fUsefCalloutMinusX'),
        (1, 'fUsefCalloutTextBorder'),
        (1, 'fUsefCalloutAccentBar'),
        (1, 'fUsefCallout'),
        (9, 'unused2'),
    ])

# Group Shape
@OfficeArtFOPTEOP.define
class wzName(uint4):
    type = 0x0380
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class wzDescription(uint4):
    type = 0x0381
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class pihlShape(uint4):
    type = 0x0382
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class pWrapPolygonVertices(uint4):
    type = 0x0383
    complex = lambda s: dyn.clone(IMsoArray, _object_=POINT, blocksize=lambda _: s.int())

@OfficeArtFOPTEOP.define
class dxWrapDistLeft(uint4):
    type = 0x0384

@OfficeArtFOPTEOP.define
class dxWrapDistTop(uint4):
    type = 0x0385

@OfficeArtFOPTEOP.define
class dxWrapDistRight(uint4):
    type = 0x0386

@OfficeArtFOPTEOP.define
class dxWrapDistBottom(uint4):
    type = 0x0387

@OfficeArtFOPTEOP.define
class lidRegroup(uint4):
    type = 0x0388

@OfficeArtFOPTEOP.define
class unused906(sint4):
    type = 0x038a

@OfficeArtFOPTEOP.define
class wzTooltip(uint4):
    type = 0x038d
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class wzScript(uint4):
    type = 0x038e
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class posh(uint4):
    type = 0x038f
    _values_ = [
        ('msophAbs', 0x00000000), # The shape is horizontally offset by an absolute distance from the page element.
        ('msophLeft', 0x00000001), # The shape is horizontally positioned at the left side of the page element.
        ('msophCenter', 0x00000002), # The shape is horizontally positioned at the center of the page element.
        ('msophRight', 0x00000003), # The shape is horizontally positioned at the right side of the page element.
        ('msophInside', 0x00000004), # The shape is horizontally positioned like msophLeft on odd-numbered pages and like msophRight on even-numbered pages.
        ('msophOutside', 0x00000005), # The shape is horizontally positioned like msophRight on odd-numbered pages and like msophLeft on even-numbered pages.
    ]

@OfficeArtFOPTEOP.define
class posrelh(uint4):
    type = 0x0390
    _values_ = [
        ('msoprhMargin', 0x00000001), # The shape is horizontally positioned relative to the margins of the page:
        ('msoprhPage', 0x00000002), # The shape is horizontally positioned relative to the edges of the page:
        ('msoprhText', 0x00000003), # The shape is horizontally positioned relative to the column of text underneath it:
        ('msoprhChar', 0x00000004), # The shape is horizontally positioned relative to the character of text underneath it:
    ]

@OfficeArtFOPTEOP.define
class posv(uint4):
    type = 0x0391
    _values_ = [
        ('msophAbs', 0x00000000), # The shape is horizontally offset by an absolute distance from the page element.
        ('msophLeft', 0x00000001), # The shape is horizontally positioned at the left side of the page element.
        ('msophCenter', 0x00000002), # The shape is horizontally positioned at the center of the page element.
        ('msophRight', 0x00000003), # The shape is horizontally positioned at the right side of the page element.
        ('msophInside', 0x00000004), # The shape is horizontally positioned like msophLeft on odd-numbered pages and like msophRight on even-numbered pages.
        ('msophOutside', 0x00000005), # The shape is horizontally positioned like msophRight on odd-numbered pages and like msophLeft on even-numbered pages.
    ]

@OfficeArtFOPTEOP.define
class posrelv(uint4):
    type = 0x0392
    _values_ = [
        ('msoprvMargin', 0x00000001), # The shape is horizontally positioned relative to the margins of the page:
        ('msoprvPage', 0x00000002), # The shape is horizontally positioned relative to the edges of the page:
        ('msoprvText', 0x00000003), # The shape is horizontally positioned relative to the column of text underneath it:
        ('msoprvLine', 0x00000004), # The shape is horizontally positioned relative to the character of text underneath it:
    ]

@OfficeArtFOPTEOP.define
class pctHR(uint4):
    type = 0x0393

@OfficeArtFOPTEOP.define
class alignHR(pint.enum, uint4):
    type = 0x0394
    _values_ = [
        ('left-aligned', 0x00000000),
        ('center', 0x00000001),
        ('right-aligned', 0x00000002),
    ]

@OfficeArtFOPTEOP.define
class dxHeightHR(uint4):
    type = 0x0395

@OfficeArtFOPTEOP.define
class dxWidthHR(uint4):
    type = 0x0396

@OfficeArtFOPTEOP.define
class wzScriptExtAttr(uint4):
    type = 0x0397
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class alignHR(pint.enum, uint4):
    type = 0x0398
    _values_ = [
        ('JavaScript', 0x00000001),
        ('VBScript', 0x00000002),
        ('ASP', 0x00000003),
        ('Other', 0x00000004),
    ]

@OfficeArtFOPTEOP.define
class borderTopColor(COLORREF):
    type = 0x039b

@OfficeArtFOPTEOP.define
class borderLeftColor(COLORREF):
    type = 0x039c

@OfficeArtFOPTEOP.define
class borderBottomColor(COLORREF):
    type = 0x039d

@OfficeArtFOPTEOP.define
class borderRightColor(COLORREF):
    type = 0x039e

@OfficeArtFOPTEOP.define
class tableProperties(uint4):
    type = 0x039f

@OfficeArtFOPTEOP.define
class tableRowProperties(uint4):
    type = 0x03a0
    complex = lambda s: dyn.clone(IMsoArray, _object_=sint4, blocksize=lambda _: s.int())

@OfficeArtFOPTEOP.define
class wzWebBot(uint4):
    type = 0x03a5
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class metroBlob(uint4):
    type = 0x03a9
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class dhgt(uint4):
    type = 0x03aa

@OfficeArtFOPTEOP.define
class GroupShapeBooleanProperties(pbinary.flags):
    type = 0x03bf
    _fields_ = R([
        (1, 'fPrint'),
        (1, 'fHidden'),
        (1, 'fOneD'),
        (1, 'fIsButton'),
        (1, 'fOnDblClickNotify'),
        (1, 'fBehindDocument'),
        (1, 'fEditedWrap'),
        (1, 'fScriptAnchor'),
        (1, 'fReallyHidden'),
        (1, 'fAllowOverlap'),
        (1, 'fUserDrawn'),
        (1, 'fHorizRule'),
        (1, 'fNoshadeHR'),
        (1, 'fStandardHR'),
        (1, 'fIsBullet'),
        (1, 'fLayoutInCell'),
        (1, 'fUsefPrint'),
        (1, 'fUsefHidden'),
        (1, 'fUsefOneD'),
        (1, 'fUsefIsButton'),
        (1, 'fUsefOnDblClickNotify'),
        (1, 'fUsefBehindDocument'),
        (1, 'fUsefEditedWrap'),
        (1, 'fUsefScriptAnchor'),
        (1, 'fUsefReallyHidden'),
        (1, 'fUsefAllowOverlap'),
        (1, 'fUsefUserDrawn'),
        (1, 'fUsefHorizRule'),
        (1, 'fUsefNoshadeHR'),
        (1, 'fUsefStandardHR'),
        (1, 'fUsefIsBullet'),
        (1, 'fUsefLayoutInCell'),
    ])

# Group Shape 2
@OfficeArtFOPTEOP.define
class pctHoriz(uint4):
    type = 0x07c0

@OfficeArtFOPTEOP.define
class pctVert(uint4):
    type = 0x07c1

@OfficeArtFOPTEOP.define
class pctHorizPos(uint4):
    type = 0x07c2

@OfficeArtFOPTEOP.define
class pctVertPos(uint4):
    type = 0x07c3

@OfficeArtFOPTEOP.define
class sizerelh(pint.enum, uint4):
    type = 0x07c4
    _values_ = [
        ('msosrhMargin', 0x00000000), # The page, excluding the margins.
        ('msosrhPage', 0x00000001), # The page.
        ('msosrhLeftMargin', 0x00000002), # The left margin.
        ('msosrhRightMargin', 0x00000003), # The tight margin.
        ('msosrhInsideMargin', 0x00000004), # The inside margin.
        ('msosrhOutsideMargin', 0x00000005), # The outside margin.
    ]

@OfficeArtFOPTEOP.define
class sizerelv(pint.enum, uint4):
    type = 0x07c5
    _values_ = [
        ('msosrvMargin', 0x00000000), # The page, excluding the margins.
        ('msosrvPage', 0x00000001), # The page.
        ('msosrvLeftMargin', 0x00000002), # The left margin.
        ('msosrvRightMargin', 0x00000003), # The tight margin.
        ('msosrvInsideMargin', 0x00000004), # The inside margin.
        ('msosrvOutsideMargin', 0x00000005), # The outside margin.
    ]

# Geometry
@OfficeArtFOPTEOP.define
class geoLeft(uint4):
    type = 0x0140

@OfficeArtFOPTEOP.define
class geoTop(uint4):
    type = 0x0141

@OfficeArtFOPTEOP.define
class geoRight(uint4):
    type = 0x0142

@OfficeArtFOPTEOP.define
class geoBottom(uint4):
    type = 0x0143

@OfficeArtFOPTEOP.define
class shapePath(MSOSHAPEPATH):
    type = 0x0144

@OfficeArtFOPTEOP.define
class pVertices(uint4):
    type = 0x0145
    complex = lambda s: dyn.clone(IMsoArray, _object_=POINT, blocksize=lambda _: s.int())

@OfficeArtFOPTEOP.define
class pSegmentInfo(uint4):
    type = 0x0146
    complex = lambda s: dyn.clone(IMsoArray, _object_=MSOPATHINFO, blocksize=lambda _: s.int())

@OfficeArtFOPTEOP.define
class adjustValue(uint4):
    type = 0x0147

@OfficeArtFOPTEOP.define
class adjust2Value(uint4):
    type = 0x0148

@OfficeArtFOPTEOP.define
class adjust3Value(uint4):
    type = 0x0149

@OfficeArtFOPTEOP.define
class adjust4Value(uint4):
    type = 0x014a

@OfficeArtFOPTEOP.define
class adjust5Value(uint4):
    type = 0x014b

@OfficeArtFOPTEOP.define
class adjust6Value(uint4):
    type = 0x014c

@OfficeArtFOPTEOP.define
class adjust7Value(uint4):
    type = 0x014d

@OfficeArtFOPTEOP.define
class adjust8Value(uint4):
    type = 0x014e

@OfficeArtFOPTEOP.define
class pConnectionSites(uint4):
    type = 0x0151
    complex = lambda s: dyn.clone(IMsoArray, _object_=MSOPATHINFO, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class pConnectionSitesDir(uint4):
    type = 0x0152
    complex = lambda s: dyn.clone(IMsoArray, _object_=FixedPoint, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class xLimo(uint4):
    type = 0x0153

@OfficeArtFOPTEOP.define
class yLimo(uint4):
    type = 0x0154

@OfficeArtFOPTEOP.define
class pAdjustHandles(uint4):
    type = 0x0155
    complex = lambda s: dyn.clone(IMsoArray, _object_=ADJH, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class pGuides(uint4):
    type = 0x0156
    complex = lambda s: dyn.clone(IMsoArray, _object_=SG, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class pInscribe(uint4):
    type = 0x0157
    complex = lambda s: dyn.clone(IMsoArray, _object_=RECT, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class cxk(MSOCXK):
    type = 0x0158

@OfficeArtFOPTEOP.define
class GeometryBooleanProperties(pbinary.flags):
    type = 0x017f
    _fields_ = R([
        (1, 'fFillOK'),
        (1, 'fFillShadeShapeOK'),
        (1, 'fGtextOK'),
        (1, 'fLineOK'),
        (1, 'f3DOK'),
        (1, 'fShadowOK'),
        (1, 'unused1'),
        (9, 'unused2'),
        (1, 'fUsefFillOK'),
        (1, 'fUsefFillShadeShapeOK'),
        (1, 'fUsefGtextOK'),
        (1, 'fUsefLineOK'),
        (1, 'fUsef3DOK'),
        (1, 'fUsefShadowOK'),
        (1, 'unused3'),
        (9, 'unused4'),
    ])

# Fill Style
@OfficeArtFOPTEOP.define
class fillType(MSOFILLTYPE):
    type = 0x0180

@OfficeArtFOPTEOP.define
class fillColor(COLORREF):
    type = 0x0181

@OfficeArtFOPTEOP.define
class fillOpacity(FixedPoint):
    type = 0x0182

@OfficeArtFOPTEOP.define
class fillBackColor(COLORREF):
    type = 0x0183

@OfficeArtFOPTEOP.define
class fillBackOpacity(FixedPoint):
    type = 0x0184

@OfficeArtFOPTEOP.define
class fillCrMod(COLORREF):
    type = 0x0185

@OfficeArtFOPTEOP.define
class fillBlip(uint4):
    type = 0x0186
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class fillBlipName(uint4):
    type = 0x0187
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class fillBlipFlags(MSOBLIPFLAGS):
    type = 0x0188

@OfficeArtFOPTEOP.define
class fillWidth(uint4):
    type = 0x0189

@OfficeArtFOPTEOP.define
class fillHeight(uint4):
    type = 0x018a

@OfficeArtFOPTEOP.define
class fillAngle(FixedPoint):
    type = 0x018b

@OfficeArtFOPTEOP.define
class fillFocus(uint4):
    type = 0x018c

@OfficeArtFOPTEOP.define
class fillToLeft(uint4):
    type = 0x018d

@OfficeArtFOPTEOP.define
class fillToTop(uint4):
    type = 0x018e

@OfficeArtFOPTEOP.define
class fillToRight(uint4):
    type = 0x018f

@OfficeArtFOPTEOP.define
class fillToBottom(uint4):
    type = 0x0190

@OfficeArtFOPTEOP.define
class fillRectLeft(uint4):
    type = 0x0191

@OfficeArtFOPTEOP.define
class fillRectTop(uint4):
    type = 0x0192

@OfficeArtFOPTEOP.define
class fillRectRight(uint4):
    type = 0x0193

@OfficeArtFOPTEOP.define
class fillRectBottom(uint4):
    type = 0x0194

@OfficeArtFOPTEOP.define
class fillDztype(MSODZTYPE):
    type = 0x0195

@OfficeArtFOPTEOP.define
class fillShadePreset(uint4):
    type = 0x0196

@OfficeArtFOPTEOP.define
class fillShadeColors(uint4):
    type = 0x0197
    complex = lambda s: dyn.clone(IMsoArray, _object_=MSOSHADECOLOR, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class fillOriginX(FixedPoint):
    type = 0x0198

@OfficeArtFOPTEOP.define
class fillOriginY(FixedPoint):
    type = 0x0199

@OfficeArtFOPTEOP.define
class fillShapeOriginX(FixedPoint):
    type = 0x019a

@OfficeArtFOPTEOP.define
class fillShapeOriginY(FixedPoint):
    type = 0x019b

@OfficeArtFOPTEOP.define
class fillShadeType(MSOSHADETYPE):
    type = 0x019c

@OfficeArtFOPTEOP.define
class fillColorExt(COLORREF):
    type = 0x019e

@OfficeArtFOPTEOP.define
class reserved415(uint4):
    type = 0x019f

@OfficeArtFOPTEOP.define
class fillColorExtMod(MSOTINTSHADE):
    type = 0x01a0

@OfficeArtFOPTEOP.define
class reserved417(uint4):
    type = 0x01a1

@OfficeArtFOPTEOP.define
class fillBackColorExt(COLORREF):
    type = 0x01a2

@OfficeArtFOPTEOP.define
class reserved419(uint4):
    type = 0x01a3

@OfficeArtFOPTEOP.define
class fillBackColorExtMod(uint4):
    type = 0x01a4

@OfficeArtFOPTEOP.define
class reserved421(uint4):
    type = 0x01a5

@OfficeArtFOPTEOP.define
class reserved422(uint4):
    type = 0x01a6

@OfficeArtFOPTEOP.define
class reserved423(uint4):
    type = 0x01a7

@OfficeArtFOPTEOP.define
class FillStyleBooleanProperties(pbinary.flags):
    type = 0x01bf
    _fields_ = R([
        (1, 'fNoFillHitTest'),
        (1, 'fillUseRect'),
        (1, 'fillShape'),
        (1, 'fHitTestFill'),
        (1, 'fFilled'),
        (1, 'fUseShapeAnchor'),
        (1, 'fRecolorFillAsPicture'),
        (9, 'unused1'),
        (1, 'fUsefNoFillHitTest'),
        (1, 'fUsefillUseRect'),
        (1, 'fUsefillShape'),
        (1, 'fUsefHitTestFill'),
        (1, 'fUsefFilled'),
        (1, 'fUsefUseShapeAnchor'),
        (1, 'fUsefRecolorFillAsPicture'),
        (9, 'unused2'),
    ])

# Line Style
@OfficeArtFOPTEOP.define
class lineColor(COLORREF):
    type = 0x01c0

@OfficeArtFOPTEOP.define
class lineOpacity(COLORREF):
    type = 0x01c1

@OfficeArtFOPTEOP.define
class lineBackColor(COLORREF):
    type = 0x01c2

@OfficeArtFOPTEOP.define
class lineCrMod(COLORREF):
    type = 0x01c3

@OfficeArtFOPTEOP.define
class lineType(MSOLINETYPE):
    type = 0x01c4

@OfficeArtFOPTEOP.define
class lineFillBlip(uint4):
    type = 0x01c5
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class lineFillBlipName(uint4):
    type = 0x01c6
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class lineFillBlipFlags(MSOBLIPFLAGS):
    type = 0x01c7

@OfficeArtFOPTEOP.define
class lineFillWidth(MSOBLIPFLAGS):
    type = 0x01c8

@OfficeArtFOPTEOP.define
class lineFillHeight(MSOBLIPFLAGS):
    type = 0x01c9

@OfficeArtFOPTEOP.define
class lineFillDztype(MSODZTYPE):
    type = 0x01ca

@OfficeArtFOPTEOP.define
class lineWidth(uint4):
    type = 0x01cb

@OfficeArtFOPTEOP.define
class lineMiterLimit(FixedPoint):
    type = 0x01cc

@OfficeArtFOPTEOP.define
class lineStyle(MSOLINESTYLE):
    type = 0x01cd

@OfficeArtFOPTEOP.define
class lineDashing(MSOLINEDASHING):
    type = 0x01ce

@OfficeArtFOPTEOP.define
class lineDashStyle(uint4):
    type = 0x01cf
    complex = lambda s: dyn.clone(IMsoArray, _object_=uint4, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class lineStartArrowhead(MSOLINEEND):
    type = 0x01d0

@OfficeArtFOPTEOP.define
class lineEndArrowhead(MSOLINEEND):
    type = 0x01d1

@OfficeArtFOPTEOP.define
class lineStartArrowWidth(MSOLINEENDWIDTH):
    type = 0x01d2

@OfficeArtFOPTEOP.define
class lineStartArrowLength(MSOLINEENDLENGTH):
    type = 0x01d3

@OfficeArtFOPTEOP.define
class lineEndArrowWidth(MSOLINEENDWIDTH):
    type = 0x01d4

@OfficeArtFOPTEOP.define
class lineEndArrowLength(MSOLINEENDLENGTH):
    type = 0x01d5

@OfficeArtFOPTEOP.define
class lineJoinStyle(MSOLINEJOIN):
    type = 0x01d6

@OfficeArtFOPTEOP.define
class lineEndCapStyle(MSOLINECAP):
    type = 0x01d7

@OfficeArtFOPTEOP.define
class lineColorExt(COLORREF):
    type = 0x01d9

@OfficeArtFOPTEOP.define
class reserved474(uint4):
    type = 0x01da

@OfficeArtFOPTEOP.define
class lineColorExtMod(COLORREF):
    type = 0x01db

@OfficeArtFOPTEOP.define
class reserved476(uint4):
    type = 0x01dc

@OfficeArtFOPTEOP.define
class lineBackColorExt(COLORREF):
    type = 0x01dd

@OfficeArtFOPTEOP.define
class reserved478(uint4):
    type = 0x01de

@OfficeArtFOPTEOP.define
class lineBackColorExtMod(MSOTINTSHADE):
    type = 0x01df

@OfficeArtFOPTEOP.define
class reserved480(uint4):
    type = 0x01e0

@OfficeArtFOPTEOP.define
class reserved481(uint4):
    type = 0x01e1

@OfficeArtFOPTEOP.define
class reserved482(uint4):
    type = 0x01e2

@OfficeArtFOPTEOP.define
class LineStyleBooleanProperties(pbinary.flags):
    type = 0x01ff
    _fields_ = R([
        (1, 'fNoLineDrawDash'),
        (1, 'fLineFillShape'),
        (1, 'fHitTestLine'),
        (1, 'fLine'),
        (1, 'fArrowheadsOK'),
        (1, 'fInsetPenOK'),
        (1, 'fInsetPen'),
        (1, 'reserved1'),
        (1, 'reserved2'),
        (1, 'fLineOpaqueBackColor'),
        (6, 'unused1'),
        (1, 'fUsefNoLineDrawDash'),
        (1, 'fUsefLineFillShape'),
        (1, 'fUsefHitTestLine'),
        (1, 'fUsefLine'),
        (1, 'fUsefArrowheadsOK'),
        (1, 'fUsefInsetPenOK'),
        (1, 'fUsefInsetPen'),
        (1, 'unused2'),
        (1, 'unused3'),
        (1, 'fUsefLineOpaqueBackColor'),
        (6, 'unused4'),
    ])

# Left Line Style
@OfficeArtFOPTEOP.define
class lineLeftColor(COLORREF):
    type = 0x0540

@OfficeArtFOPTEOP.define
class lineLeftOpacity(FixedPoint):
    type = 0x0541

@OfficeArtFOPTEOP.define
class lineLeftBackColor(COLORREF):
    type = 0x0542

@OfficeArtFOPTEOP.define
class lineLeftCrMod(COLORREF):
    type = 0x0543

@OfficeArtFOPTEOP.define
class lineLeftType(MSOLINETYPE):
    type = 0x0544

@OfficeArtFOPTEOP.define
class lineLeftFillBlip(uint4):
    type = 0x0545
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class lineLeftFillBlipName(uint4):
    type = 0x0546

@OfficeArtFOPTEOP.define
class lineLeftFillBlipFlags(MSOBLIPFLAGS):
    type = 0x0547

@OfficeArtFOPTEOP.define
class lineLeftFillWidth(sint4):
    type = 0x0548

@OfficeArtFOPTEOP.define
class lineLeftFillHeight(sint4):
    type = 0x0549

@OfficeArtFOPTEOP.define
class lineLeftFillDztype(MSODZTYPE):
    type = 0x054a

@OfficeArtFOPTEOP.define
class lineLeftWidth(sint4):
    type = 0x054b

@OfficeArtFOPTEOP.define
class lineLeftMiterLimit(FixedPoint):
    type = 0x054c

@OfficeArtFOPTEOP.define
class lineLeftStyle(MSOLINESTYLE):
    type = 0x054d

@OfficeArtFOPTEOP.define
class lineLeftDashing(MSOLINEDASHING):
    type = 0x054e

@OfficeArtFOPTEOP.define
class lineLeftDashStyle(uint4):
    type = 0x054f
    complex = lambda s: dyn.clone(IMsoArray, _object_=uint4, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class lineLeftStartArrowhead(MSOLINEEND):
    type = 0x0550

@OfficeArtFOPTEOP.define
class lineLeftEndArrowhead(MSOLINEEND):
    type = 0x0551

@OfficeArtFOPTEOP.define
class lineLeftStartArrowWidth(MSOLINEENDWIDTH):
    type = 0x0552

@OfficeArtFOPTEOP.define
class lineLeftStartArrowLength(MSOLINEENDLENGTH):
    type = 0x0553

@OfficeArtFOPTEOP.define
class lineLeftEndArrowWidth(MSOLINEENDWIDTH):
    type = 0x0554

@OfficeArtFOPTEOP.define
class lineLeftEndArrowLength(MSOLINEENDLENGTH):
    type = 0x0555

@OfficeArtFOPTEOP.define
class lineLeftJoinStyle(MSOLINEJOIN):
    type = 0x0556

@OfficeArtFOPTEOP.define
class lineLeftEndCapStyle(MSOLINECAP):
    type = 0x0557

@OfficeArtFOPTEOP.define
class lineLeftColorExt(COLORREF):
    type = 0x0559

@OfficeArtFOPTEOP.define
class reserved1370(uint4):
    type = 0x055a

@OfficeArtFOPTEOP.define
class lineLeftColorExtMod(MSOTINTSHADE):
    type = 0x055b

@OfficeArtFOPTEOP.define
class reserved1372(uint4):
    type = 0x055c

@OfficeArtFOPTEOP.define
class lineLeftBackColorExt(COLORREF):
    type = 0x055d

@OfficeArtFOPTEOP.define
class reserved1374(uint4):
    type = 0x055e

@OfficeArtFOPTEOP.define
class lineLeftBackColorExtMod(MSOTINTSHADE):
    type = 0x055f

@OfficeArtFOPTEOP.define
class reserved1376(uint4):
    type = 0x0560

@OfficeArtFOPTEOP.define
class reserved1377(uint4):
    type = 0x0561

@OfficeArtFOPTEOP.define
class reserved1378(uint4):
    type = 0x0562

@OfficeArtFOPTEOP.define
class LeftLineStyleBooleanProperties(pbinary.flags):
    type = 0x057f
    _fields_ = R([
        (1, 'fLeftNoLineDrawDash'),
        (1, 'fLineLeftFillShape'),
        (1, 'fLeftHitTestLine'),
        (1, 'fLeftLine'),
        (1, 'reserved1'),
        (1, 'fLeftInsetPenOK'),
        (1, 'fLeftInsetPen'),
        (1, 'reserved2'),
        (1, 'reserved3'),
        (1, 'unused1'),
        (6, 'unused2'),
        (1, 'fUsefLeftNoLineDrawDash'),
        (1, 'fUsefLineLeftFillShape'),
        (1, 'fUsefLeftHitTestLine'),
        (1, 'fUsefLeftLine'),
        (1, 'unused3'),
        (1, 'fUsefLeftInsetPenOK'),
        (1, 'fUsefLeftInsetPen'),
        (1, 'unused4'),
        (1, 'unused5'),
        (1, 'unused6'),
        (6, 'unused7'),
    ])

# Top Line Style
@OfficeArtFOPTEOP.define
class lineTopColor(COLORREF):
    type = 0x0580

@OfficeArtFOPTEOP.define
class lineTopOpacity(FixedPoint):
    type = 0x0581

@OfficeArtFOPTEOP.define
class lineTopBackColor(COLORREF):
    type = 0x0582

@OfficeArtFOPTEOP.define
class lineTopCrMod(COLORREF):
    type = 0x0583

@OfficeArtFOPTEOP.define
class lineTopType(MSOLINETYPE):
    type = 0x0584

@OfficeArtFOPTEOP.define
class lineTopFillBlip(uint4):
    type = 0x0585
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class lineTopFillBlipName(uint4):
    type = 0x0586
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class lineTopFillBlipFlags(MSOBLIPFLAGS):
    type = 0x0587

@OfficeArtFOPTEOP.define
class lineTopFillWidth(sint4):
    type = 0x0588

@OfficeArtFOPTEOP.define
class lineTopFillHeight(sint4):
    type = 0x0589

@OfficeArtFOPTEOP.define
class lineTopFillDztype(MSODZTYPE):
    type = 0x058a

@OfficeArtFOPTEOP.define
class lineTopWidth(sint4):
    type = 0x058b

@OfficeArtFOPTEOP.define
class lineTopMiterLimit(FixedPoint):
    type = 0x058c

@OfficeArtFOPTEOP.define
class lineTopStyle(MSOLINESTYLE):
    type = 0x058d

@OfficeArtFOPTEOP.define
class lineTopDashing(MSOLINEDASHING):
    type = 0x058e

@OfficeArtFOPTEOP.define
class lineTopDashStyle(uint4):
    type = 0x058f
    complex = lambda s: dyn.clone(IMsoArray, _object_=uint4, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class lineTopStartArrowhead(MSOLINEEND):
    type = 0x0590

@OfficeArtFOPTEOP.define
class lineTopEndArrowhead(MSOLINEEND):
    type = 0x0591

@OfficeArtFOPTEOP.define
class lineTopStartArrowWidth(MSOLINEENDWIDTH):
    type = 0x0592

@OfficeArtFOPTEOP.define
class lineTopStartArrowLength(MSOLINEENDLENGTH):
    type = 0x0593

@OfficeArtFOPTEOP.define
class lineTopEndArrowWidth(MSOLINEENDWIDTH):
    type = 0x0594

@OfficeArtFOPTEOP.define
class lineTopEndArrowLength(MSOLINEENDLENGTH):
    type = 0x0595

@OfficeArtFOPTEOP.define
class lineTopJoinStyle(MSOLINEJOIN):
    type = 0x0596

@OfficeArtFOPTEOP.define
class lineTopEndCapStyle(MSOLINECAP):
    type = 0x0597

@OfficeArtFOPTEOP.define
class lineTopColorExt(COLORREF):
    type = 0x0599

@OfficeArtFOPTEOP.define
class reserved1434(uint4):
    type = 0x059a

@OfficeArtFOPTEOP.define
class lineTopColorExtMod(MSOTINTSHADE):
    type = 0x059b

@OfficeArtFOPTEOP.define
class reserved1436(uint4):
    type = 0x059c

@OfficeArtFOPTEOP.define
class lineTopBackColorExt(COLORREF):
    type = 0x059d

@OfficeArtFOPTEOP.define
class reserved1438(uint4):
    type = 0x059e

@OfficeArtFOPTEOP.define
class lineTopBackColorExtMod(MSOTINTSHADE):
    type = 0x059f

@OfficeArtFOPTEOP.define
class reserved1440(uint4):
    type = 0x05a0

@OfficeArtFOPTEOP.define
class reserved1441(uint4):
    type = 0x05a1

@OfficeArtFOPTEOP.define
class reserved1442(uint4):
    type = 0x05a2

@OfficeArtFOPTEOP.define
class TopLineStyleBooleanProperties(pbinary.flags):
    type = 0x05bf
    _fields_ = R([
        (1, 'fTopNoLineDrawDash'),
        (1, 'fLineTopFillShape'),
        (1, 'fTopHitTestLine'),
        (1, 'fTopLine'),
        (1, 'reserved1'),
        (1, 'fTopInsetPenOK'),
        (1, 'fTopInsetPen'),
        (1, 'reserved2'),
        (1, 'reserved3'),
        (1, 'unused1'),
        (6, 'unused2'),
        (1, 'fUsefTopNoLineDrawDash'),
        (1, 'fUsefLineTopFillShape'),
        (1, 'fUsefTopHitTestLine'),
        (1, 'fUsefTopLine'),
        (1, 'unused3'),
        (1, 'fUsefTopInsetPenOK'),
        (1, 'fUsefTopInsetPen'),
        (1, 'unused4'),
        (1, 'unused5'),
        (1, 'unused6'),
        (6, 'unused7'),
    ])

# Right Line Style
@OfficeArtFOPTEOP.define
class lineRightColor(COLORREF):
    type = 0x05c0

@OfficeArtFOPTEOP.define
class lineRightOpacity(FixedPoint):
    type = 0x05c1

@OfficeArtFOPTEOP.define
class lineRightBackColor(COLORREF):
    type = 0x05c2

@OfficeArtFOPTEOP.define
class lineRightCrMod(COLORREF):
    type = 0x05c3

@OfficeArtFOPTEOP.define
class lineRightType(MSOLINETYPE):
    type = 0x05c4

@OfficeArtFOPTEOP.define
class lineRightFillBlip(uint4):
    type = 0x05c5
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class lineRightFillBlipName(uint4):
    type = 0x05c6
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class lineRightFillBlipFlags(MSOBLIPFLAGS):
    type = 0x05c7

@OfficeArtFOPTEOP.define
class lineRightFillWidth(sint4):
    type = 0x05c8

@OfficeArtFOPTEOP.define
class lineRightFillHeight(sint4):
    type = 0x05c9

@OfficeArtFOPTEOP.define
class lineRightFillDztype(MSODZTYPE):
    type = 0x05ca

@OfficeArtFOPTEOP.define
class lineRightWidth(sint4):
    type = 0x05cb

@OfficeArtFOPTEOP.define
class lineRightMiterLimit(FixedPoint):
    type = 0x05cc

@OfficeArtFOPTEOP.define
class lineRightStyle(MSOLINESTYLE):
    type = 0x05cd

@OfficeArtFOPTEOP.define
class lineRightDashing(MSOLINEDASHING):
    type = 0x05ce

@OfficeArtFOPTEOP.define
class lineRightDashStyle(uint4):
    type = 0x05cf
    complex = lambda s: dyn.clone(IMsoArray, _object_=uint4, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class lineRightStartArrowhead(MSOLINEEND):
    type = 0x05d0

@OfficeArtFOPTEOP.define
class lineRightEndArrowhead(MSOLINEEND):
    type = 0x05d1

@OfficeArtFOPTEOP.define
class lineRightStartArrowWidth(MSOLINEENDWIDTH):
    type = 0x05d2

@OfficeArtFOPTEOP.define
class lineRightStartArrowLength(MSOLINEENDLENGTH):
    type = 0x05d3

@OfficeArtFOPTEOP.define
class lineRightEndArrowWidth(MSOLINEENDWIDTH):
    type = 0x05d4

@OfficeArtFOPTEOP.define
class lineRightEndArrowLength(MSOLINEENDLENGTH):
    type = 0x05d5

@OfficeArtFOPTEOP.define
class lineRightJoinStyle(MSOLINEJOIN):
    type = 0x05d6

@OfficeArtFOPTEOP.define
class lineRightEndCapStyle(MSOLINECAP):
    type = 0x05d7

@OfficeArtFOPTEOP.define
class lineRightColorExt(COLORREF):
    type = 0x05d9

@OfficeArtFOPTEOP.define
class reserved1498(uint4):
    type = 0x05da

@OfficeArtFOPTEOP.define
class lineRightColorExtMod(MSOTINTSHADE):
    type = 0x05db

@OfficeArtFOPTEOP.define
class reserved1500(uint4):
    type = 0x05dc

@OfficeArtFOPTEOP.define
class lineRightBackColorExt(COLORREF):
    type = 0x05dd

@OfficeArtFOPTEOP.define
class reserved1502(uint4):
    type = 0x05de

@OfficeArtFOPTEOP.define
class lineRightBackColorExtMod(MSOTINTSHADE):
    type = 0x05df

@OfficeArtFOPTEOP.define
class reserved1504(uint4):
    type = 0x05e0

@OfficeArtFOPTEOP.define
class reserved1505(uint4):
    type = 0x05e1

@OfficeArtFOPTEOP.define
class reserved1506(uint4):
    type = 0x05e2

@OfficeArtFOPTEOP.define
class RightLineStyleBooleanProperties(pbinary.flags):
    type = 0x05ff
    _fields_ = R([
        (1, 'fRightNoLineDrawDash'),
        (1, 'fLineRightFillShape'),
        (1, 'fRightHitTestLine'),
        (1, 'fRightLine'),
        (1, 'reserved1'),
        (1, 'fRightInsetPenOK'),
        (1, 'fRightInsetPen'),
        (1, 'reserved2'),
        (1, 'reserved3'),
        (1, 'unused1'),
        (6, 'unused2'),
        (1, 'fUsefRightNoLineDrawDash'),
        (1, 'fUsefLineRightFillShape'),
        (1, 'fUsefRightHitTestLine'),
        (1, 'fUsefRightLine'),
        (1, 'unused3'),
        (1, 'fUsefRightInsetPenOK'),
        (1, 'fUsefRightInsetPen'),
        (1, 'unused4'),
        (1, 'unused5'),
        (1, 'unused6'),
        (6, 'unused7'),
    ])

# Bottom Line Style
@OfficeArtFOPTEOP.define
class lineBottomColor(COLORREF):
    type = 0x0600

@OfficeArtFOPTEOP.define
class lineBottomOpacity(FixedPoint):
    type = 0x0601

@OfficeArtFOPTEOP.define
class lineBottomBackColor(COLORREF):
    type = 0x0602

@OfficeArtFOPTEOP.define
class lineBottomCrMod(COLORREF):
    type = 0x0603

@OfficeArtFOPTEOP.define
class lineBottomType(MSOLINETYPE):
    type = 0x0604

@OfficeArtFOPTEOP.define
class lineBottomFillBlip(uint4):
    type = 0x0605
    complex = lambda s: dyn.block(s.int())

@OfficeArtFOPTEOP.define
class lineBottomFillBlipName(uint4):
    type = 0x0606
    complex = lambda s: dyn.clone(pstr.string, length=s.int())

@OfficeArtFOPTEOP.define
class lineBottomFillBlipFlags(MSOBLIPFLAGS):
    type = 0x0607

@OfficeArtFOPTEOP.define
class lineBottomFillWidth(sint4):
    type = 0x0608

@OfficeArtFOPTEOP.define
class lineBottomFillHeight(sint4):
    type = 0x0609

@OfficeArtFOPTEOP.define
class lineBottomFillDztype(MSODZTYPE):
    type = 0x060a

@OfficeArtFOPTEOP.define
class lineBottomWidth(sint4):
    type = 0x060b

@OfficeArtFOPTEOP.define
class lineBottomMiterLimit(FixedPoint):
    type = 0x060c

@OfficeArtFOPTEOP.define
class lineBottomStyle(MSOLINESTYLE):
    type = 0x060d

@OfficeArtFOPTEOP.define
class lineBottomDashing(MSOLINEDASHING):
    type = 0x060e

@OfficeArtFOPTEOP.define
class lineBottomDashStyle(uint4):
    type = 0x060f
    complex = lambda s: dyn.clone(IMsoArray, _object_=uint4, blocksize=lambda n: s.int())

@OfficeArtFOPTEOP.define
class lineBottomStartArrowhead(MSOLINEEND):
    type = 0x0610

@OfficeArtFOPTEOP.define
class lineBottomEndArrowhead(MSOLINEEND):
    type = 0x0611

@OfficeArtFOPTEOP.define
class lineBottomStartArrowWidth(MSOLINEENDWIDTH):
    type = 0x0612

@OfficeArtFOPTEOP.define
class lineBottomStartArrowLength(MSOLINEENDLENGTH):
    type = 0x0613

@OfficeArtFOPTEOP.define
class lineBottomEndArrowWidth(MSOLINEENDWIDTH):
    type = 0x0614

@OfficeArtFOPTEOP.define
class lineBottomEndArrowLength(MSOLINEENDLENGTH):
    type = 0x0615

@OfficeArtFOPTEOP.define
class lineBottomJoinStyle(MSOLINEJOIN):
    type = 0x0616

@OfficeArtFOPTEOP.define
class lineBottomEndCapStyle(MSOLINECAP):
    type = 0x0617

@OfficeArtFOPTEOP.define
class lineBottomColorExt(COLORREF):
    type = 0x0619

@OfficeArtFOPTEOP.define
class reserved1562(uint4):
    type = 0x061a

@OfficeArtFOPTEOP.define
class lineBottomColorExtMod(MSOTINTSHADE):
    type = 0x061b

@OfficeArtFOPTEOP.define
class reserved1500(uint4):
    type = 0x061c

@OfficeArtFOPTEOP.define
class lineBottomBackColorExt(COLORREF):
    type = 0x061d

@OfficeArtFOPTEOP.define
class reserved1566(uint4):
    type = 0x061e

@OfficeArtFOPTEOP.define
class lineBottomBackColorExtMod(MSOTINTSHADE):
    type = 0x061f

@OfficeArtFOPTEOP.define
class reserved1568(uint4):
    type = 0x0620

@OfficeArtFOPTEOP.define
class reserved1569(uint4):
    type = 0x0621

@OfficeArtFOPTEOP.define
class reserved1570(uint4):
    type = 0x0622

@OfficeArtFOPTEOP.define
class BottomLineStyleBooleanProperties(pbinary.flags):
    type = 0x063f
    _fields_ = R([
        (1, 'fBottomNoLineDrawDash'),
        (1, 'fLineBottomFillShape'),
        (1, 'fBottomHitTestLine'),
        (1, 'fBottomLine'),
        (1, 'reserved1'),
        (1, 'fBottomInsetPenOK'),
        (1, 'fBottomInsetPen'),
        (1, 'reserved2'),
        (1, 'reserved3'),
        (1, 'unused1'),
        (6, 'unused2'),
        (1, 'fUsefBottomNoLineDrawDash'),
        (1, 'fUsefLineBottomFillShape'),
        (1, 'fUsefBottomHitTestLine'),
        (1, 'fUsefBottomLine'),
        (1, 'unused3'),
        (1, 'fUsefBottomInsetPenOK'),
        (1, 'fUsefBottomInsetPen'),
        (1, 'unused4'),
        (1, 'unused5'),
        (1, 'unused6'),
        (6, 'unused7'),
    ])

# Shadow Style
@OfficeArtFOPTEOP.define
class shadowType(MSOSHADOWTYPE):
    type = 0x0200

@OfficeArtFOPTEOP.define
class shadowColor(COLORREF):
    type = 0x0201

@OfficeArtFOPTEOP.define
class shadowHilight(COLORREF):
    type = 0x0202

@OfficeArtFOPTEOP.define
class shadowCrMod(COLORREF):
    type = 0x0203

@OfficeArtFOPTEOP.define
class shadowOpacity(FixedPoint):
    type = 0x0204

@OfficeArtFOPTEOP.define
class shadowOffsetX(sint4):
    type = 0x0205

@OfficeArtFOPTEOP.define
class shadowOffsetX(sint4):
    type = 0x0206

@OfficeArtFOPTEOP.define
class shadowSecondOffsetX(sint4):
    type = 0x0207

@OfficeArtFOPTEOP.define
class shadowSecondOffsetY(sint4):
    type = 0x0208

@OfficeArtFOPTEOP.define
class shadowOriginX(FixedPoint):
    type = 0x0210

@OfficeArtFOPTEOP.define
class shadowOriginY(FixedPoint):
    type = 0x0211

@OfficeArtFOPTEOP.define
class shadowColorExt(COLORREF):
    type = 0x0212

@OfficeArtFOPTEOP.define
class reserved531(uint4):
    type = 0x0213

@OfficeArtFOPTEOP.define
class shadowColorExtMod(MSOTINTSHADE):
    type = 0x0214

@OfficeArtFOPTEOP.define
class reserved533(uint4):
    type = 0x0215

@OfficeArtFOPTEOP.define
class shadowHighlightExt(COLORREF):
    type = 0x0216

@OfficeArtFOPTEOP.define
class reserved535(uint4):
    type = 0x0217

@OfficeArtFOPTEOP.define
class shadowHighlightExtMod(MSOTINTSHADE):
    type = 0x0218

@OfficeArtFOPTEOP.define
class reserved537(uint4):
    type = 0x0219

@OfficeArtFOPTEOP.define
class reserved538(uint4):
    type = 0x021a

@OfficeArtFOPTEOP.define
class reserved539(uint4):
    type = 0x021b

@OfficeArtFOPTEOP.define
class shadowSoftness(sint4):
    type = 0x021c

@OfficeArtFOPTEOP.define
class ShadowStyleBooleanProperties(pbinary.flags):
    type = 0x023f
    _fields_ = R([
        (1, 'fshadowObscured'),
        (1, 'fShadow'),
        (14, 'unused1'),
        (1, 'fUsefshadowObscured'),
        (1, 'fUsefShadow'),
        (14, 'unused2'),
    ])

# Perspective Style
@OfficeArtFOPTEOP.define
class perspectiveType(MSOXFORMTYPE):
    type = 0x0240

@OfficeArtFOPTEOP.define
class perspectiveOffsetX(uint4):
    type = 0x0241

@OfficeArtFOPTEOP.define
class perspectiveOffsetY(uint4):
    type = 0x0242

@OfficeArtFOPTEOP.define
class perspectiveScaleXToX(FixedPoint):
    type = 0x0243

@OfficeArtFOPTEOP.define
class perspectiveScaleYToX(FixedPoint):
    type = 0x0244

@OfficeArtFOPTEOP.define
class perspectiveScaleXToY(FixedPoint):
    type = 0x0245

@OfficeArtFOPTEOP.define
class perspectiveScaleYToY(FixedPoint):
    type = 0x0246

@OfficeArtFOPTEOP.define
class perspectivePerspectiveX(FixedPoint):
    type = 0x0247

@OfficeArtFOPTEOP.define
class perspectivePerspectiveY(FixedPoint):
    type = 0x0248

@OfficeArtFOPTEOP.define
class perspectiveWeight(uint4):
    type = 0x0249

@OfficeArtFOPTEOP.define
class perspectiveOriginX(FixedPoint):
    type = 0x024a

@OfficeArtFOPTEOP.define
class perspectiveOriginY(FixedPoint):
    type = 0x024b

@OfficeArtFOPTEOP.define
class PerspectiveStyleBooleanProperties(pbinary.flags):
    type = 0x027f
    _fields_ = R([
        (1, 'fPerspective'),
        (15, 'unused1'),
        (1, 'fUsefPerspective'),
        (15, 'unused2'),
    ])

# FIXME: 3D Object

# FIXME: 3D Style

# FIXME: Diagram

# Transform
@OfficeArtFOPTEOP.define
class left(sint4):
    type = 0x0000

@OfficeArtFOPTEOP.define
class top(sint4):
    type = 0x0001

@OfficeArtFOPTEOP.define
class right(sint4):
    type = 0x0002

@OfficeArtFOPTEOP.define
class bottom(sint4):
    type = 0x0003

@OfficeArtFOPTEOP.define
class rotation(FixedPoint):
    type = 0x0004

@OfficeArtFOPTEOP.define
class gvPage(uint4):
    type = 0x0005

@OfficeArtFOPTEOP.define
class TransformBooleanProperties(pbinary.flags):
    type = 0x003f
    _fields_ = R([
        (1, 'fFlipH'),
        (1, 'fFlipV'),
        (1, 'unused1'),
        (13, 'unused2'),
        (1, 'fUsefFlipH'),
        (1, 'fUsefFlipV'),
        (1, 'unused3'),
        (13, 'unused4'),
    ])

# Relative Transform
@OfficeArtFOPTEOP.define
class relLeft(sint4):
    type = 0x03c0

@OfficeArtFOPTEOP.define
class relTop(sint4):
    type = 0x03c1

@OfficeArtFOPTEOP.define
class relRight(sint4):
    type = 0x03c2

@OfficeArtFOPTEOP.define
class relBottom(sint4):
    type = 0x03c3

@OfficeArtFOPTEOP.define
class relRotation(FixedPoint):
    type = 0x03c4

@OfficeArtFOPTEOP.define
class gvRelPage(uint4):
    type = 0x03c5

@OfficeArtFOPTEOP.define
class RelativeTransformBooleanProperties(pbinary.flags):
    type = 0x03ff
    _fields_ = R([
        (1, 'fRelFlipH'),
        (1, 'fRelFlipV'),
        (1, 'unused1'),
        (13, 'unused2'),
        (1, 'fUsefRelFlipH'),
        (1, 'fUsefRelFlipV'),
        (1, 'unused3'),
        (13, 'unused4'),
    ])

# Protection
@OfficeArtFOPTEOP.define
class ProtectionBooleanProperties(pbinary.flags):
    type = 0x007f
    _fields_ = R([
        (1, 'fLockAgainstGrouping'),
        (1, 'fLockAdjustHandles'),
        (1, 'fLockText'),
        (1, 'fLockVertices'),
        (1, 'fLockCropping'),
        (1, 'fLockAgainstSelect'),
        (1, 'fLockPosition'),
        (1, 'fLockAspectRatio'),
        (1, 'fLockRotation'),
        (1, 'fLockAgainstUngrouping'),
        (6, 'unused1'),
        (1, 'fUsefLockAgainstGrouping'),
        (1, 'fUsefLockAdjustHandles'),
        (1, 'fUsefLockText'),
        (1, 'fUsefLockVertices'),
        (1, 'fUsefLockCropping'),
        (1, 'fUsefLockAgainstSelect'),
        (1, 'fUsefLockPosition'),
        (1, 'fUsefLockAspectRatio'),
        (1, 'fUsefLockRotation'),
        (1, 'fUsefLockAgainstUngrouping'),
        (6, 'unused2'),
    ])

# Text
@OfficeArtFOPTEOP.define
class ITxId(sint4):
    type = 0x0080

@OfficeArtFOPTEOP.define
class dxTextLeft(sint4):
    type = 0x0081

@OfficeArtFOPTEOP.define
class dyTextTop(sint4):
    type = 0x0082

@OfficeArtFOPTEOP.define
class dxTextRight(sint4):
    type = 0x0083

@OfficeArtFOPTEOP.define
class dyTextBottom(sint4):
    type = 0x0084

@OfficeArtFOPTEOP.define
class WrapText(MSOWRAPMODE):
    type = 0x0085

@OfficeArtFOPTEOP.define
class unused134(uint4):
    type = 0x0086

@OfficeArtFOPTEOP.define
class anchorText(MSOANCHOR):
    type = 0x0087

@OfficeArtFOPTEOP.define
class txflTextFlow(MSOTXFL):
    type = 0x0088

@OfficeArtFOPTEOP.define
class cdirFont(MSOCDIR):
    type = 0x0089

@OfficeArtFOPTEOP.define
class hspNext(MSOSPID):
    type = 0x008a

@OfficeArtFOPTEOP.define
class txdir(MSOTXDIR):
    type = 0x008b

@OfficeArtFOPTEOP.define
class unused140(uint4):
    type = 0x008c

@OfficeArtFOPTEOP.define
class unused141(uint4):
    type = 0x008d

@OfficeArtFOPTEOP.define
class TextBooleanProperties(pbinary.flags):
    type = 0x00bf
    _fields_ = R([
        (1, 'unused1'),
        (1, 'fFitShapeToText'),
        (1, 'unused2'),
        (1, 'fAutoTextMargin'),
        (1, 'fSelectText'),
        (11, 'unused3'),
        (1, 'unused4'),
        (1, 'fUsefFitShapeToText'),
        (1, 'unused5'),
        (1, 'fUsefAutoTextMargin'),
        (1, 'fUsefSelectText'),
        (11, 'unused6'),
    ])

# Geometry Text
@OfficeArtFOPTEOP.define
class gtextUNICODE(uint4):
    type = 0x00c0
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class gtextAlign(pint.enum, uint4):
    type = 0x00c1
    _values_ = [
        ('msoalignTextStretch', 0x00000000), # Text SHOULD<59> be stretched to fill the entire length of the path:
        ('msoalignTextCenter', 0x00000001), # Text is centered along the length of the path:
        ('msoalignTextLeft', 0x00000002), # Text is placed at the beginning of the path:
        ('msoalignTextRight', 0x00000003), # Text is placed at the end of the path:
        ('msoalignTextLetterJust', 0x00000004), # Spacing between individual letters SHOULD<60> be added so that the letters fill the entire path:
        ('msoalignTextWordJust', 0x00000005), # Spacing between individual words SHOULD<61> be added so that the words fill the entire path:
    ]

@OfficeArtFOPTEOP.define
class gtextSize(FixedPoint):
    type = 0x00c3

@OfficeArtFOPTEOP.define
class gtextSpacing(FixedPoint):
    type = 0x00c4

@OfficeArtFOPTEOP.define
class gtextFont(uint4):
    type = 0x00c5
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class gtextCSSFont(uint4):
    type = 0x00c6
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class GeometryTextBooleanProperties(pbinary.flags):
    type = 0x00ff
    _fields_ = R([
        (1, 'gtextFStrikeThrough'),
        (1, 'gtextFSmallcaps'),
        (1, 'gtextFShadow'),
        (1, 'gtextFUnderline'),
        (1, 'gtextFItalic'),
        (1, 'gtextFBold'),
        (1, 'gtextFDxMeasure'),
        (1, 'gtextFNormalize'),
        (1, 'gtextFBestFit'),
        (1, 'gtextFShrinkFit'),
        (1, 'gtextFStretch'),
        (1, 'gtextFTight'),
        (1, 'gtextFKern'),
        (1, 'gtextFVertical'),
        (1, 'fGtext'),
        (1, 'gtextFReverseRows'),
        (1, 'fUsegtextFStrikethrough'),
        (1, 'fUsegtextFSmallcaps'),
        (1, 'fUsegtextFShadow'),
        (1, 'fUsegtextFUnderline'),
        (1, 'fUsegtextFItalic'),
        (1, 'fUsegtextFBold'),
        (1, 'fUsegtextFDxMeasure'),
        (1, 'fUsegtextFNormalize'),
        (1, 'fUsegtextFBestFit'),
        (1, 'fUsegtextFShrinkFit '),
        (1, 'fUsegtextFStretch '),
        (1, 'fUsegtextFTight '),
        (1, 'fUsegtextFKern '),
        (1, 'fUsegtextFVertical '),
        (1, 'fUsefGtext '),
        (1, 'fUsegtextFReverseRows '),
    ])

# Blip
@OfficeArtFOPTEOP.define
class cropFromTop(FixedPoint):
    type = 0x0100

@OfficeArtFOPTEOP.define
class cropFromBottom(FixedPoint):
    type = 0x0101

@OfficeArtFOPTEOP.define
class cropFromLeft(FixedPoint):
    type = 0x0102

@OfficeArtFOPTEOP.define
class cropFromRight(FixedPoint):
    type = 0x0103

@OfficeArtFOPTEOP.define
class pib(FixedPoint):
    type = 0x0104
    complex = lambda s: RecordGeneral

@OfficeArtFOPTEOP.define
class pibName(uint4):
    type = 0x0105
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class pibFlags(MSOBLIPFLAGS):
    type = 0x0106

@OfficeArtFOPTEOP.define
class pictureTransparent(COLORREF):
    type = 0x0107

@OfficeArtFOPTEOP.define
class pictureContrast(sint4):
    type = 0x0108

@OfficeArtFOPTEOP.define
class pictureBrightness(sint4):
    type = 0x0109

@OfficeArtFOPTEOP.define
class pictureId(sint4):
    type = 0x010b

@OfficeArtFOPTEOP.define
class pictureDblCrMod(COLORREF):
    type = 0x010c

@OfficeArtFOPTEOP.define
class pictureFillCrMod(COLORREF):
    type = 0x010d

@OfficeArtFOPTEOP.define
class pictureLineCrMod(COLORREF):
    type = 0x010e

@OfficeArtFOPTEOP.define
class pibPrint(uint4):
    type = 0x010f
    complex = lambda s: RecordGeneral

@OfficeArtFOPTEOP.define
class pibPrintName(COLORREF):
    type = 0x0110
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class pibPrintFlags(MSOBLIPFLAGS):
    type = 0x0111

@OfficeArtFOPTEOP.define
class movie(uint4):
    type = 0x0112
    complex = lambda s: ptype.undefined

@OfficeArtFOPTEOP.define
class pictureTransparentEx(COLORREF):
    type = 0x0115

@OfficeArtFOPTEOP.define
class reserved278(uint4):
    type = 0x0116

@OfficeArtFOPTEOP.define
class pictureTransparentExMod(MSOTINTSHADE):
    type = 0x0117

@OfficeArtFOPTEOP.define
class reserved280(uint4):
    type = 0x0118

@OfficeArtFOPTEOP.define
class reserved281(uint4):
    type = 0x0119

@OfficeArtFOPTEOP.define
class pictureRecolor(COLORREF):
    type = 0x011a

@OfficeArtFOPTEOP.define
class pictureRecolorExt(COLORREF):
    type = 0x011b

@OfficeArtFOPTEOP.define
class reserved284(uint4):
    type = 0x011c

@OfficeArtFOPTEOP.define
class pictureRecolorExtModl(MSOTINTSHADE):
    type = 0x011d

@OfficeArtFOPTEOP.define
class reserved286(uint4):
    type = 0x011e

@OfficeArtFOPTEOP.define
class reserved287(uint4):
    type = 0x011f

@OfficeArtFOPTEOP.define
class BlipBooleanProperties(pbinary.flags):
    type = 0x013f
    _fields_ = R([
        (1, 'fPictureActive'),
        (1, 'fPictureBiLevel'),
        (1, 'fpictureGray'),
        (1, 'fNoHitTestPicture'),
        (1, 'fLooping'),
        (1, 'fRewind'),
        (1, 'fPicturePreserveGrays'),
        (9, 'unused1'),
        (1, 'fUsefPictureActive'),
        (1, 'fUsefPictureBiLevel'),
        (1, 'fUsefPictureGray'),
        (1, 'fUsefNoHitTestPicture'),
        (1, 'fUsefLooping'),
        (1, 'FusefRewind'),
        (1, 'FusefPicturePreserveGrays'),
        (9, 'unused2'),
    ])

# Unknown HTML
@OfficeArtFOPTEOP.define
class wzLineId(uint4):
    type = 0x0402
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzFillId(uint4):
    type = 0x0403
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzPictureId(uint4):
    type = 0x0404
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzPathId(uint4):
    type = 0x0405
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzShadowId(uint4):
    type = 0x0406
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzPerspectiveId(uint4):
    type = 0x0407
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzGtextId(uint4):
    type = 0x0408
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzFormulaeId(uint4):
    type = 0x0409
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzHandlesId(uint4):
    type = 0x040a
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzCalloutId(uint4):
    type = 0x040b
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzLockId(uint4):
    type = 0x040c
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzTextId(uint4):
    type = 0x040d
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzThreeDId(uint4):
    type = 0x040e
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class UnknownHTMLBooleanProperties(pbinary.flags):
    type = 0x043f
    _fields_ = [
        (1, 'unused1'),
        (1, 'fFakeMaster'),
        (1, 'fOleFromHtml'),
        (13, 'unused2'),
        (1, 'unused3'),
        (1, 'fUsefFakeMaster'),
        (1, 'FusefOleFromHtml'),
        (13, 'unused4'),
    ]

# Web Component
@OfficeArtFOPTEOP.define
class webComponentWzHtml(uint4):
    type = 0x0680
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class webComponentWzName(uint4):
    type = 0x0681
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class webComponentWzUrl(uint4):
    type = 0x0682
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class WebComponentBooleanProperties(pbinary.flags):
    type = 0x06bf
    _fields_ = [
        (1, 'fIsWebComponent'),
        (15, 'unused1'),
        (1, 'fUsefIsWebComponent'),
        (15, 'unused2'),
    ]

# Ink
@OfficeArtFOPTEOP.define
class pInkData(uint4):
    type = 0x0700
    #complex = lambda s: dyn.clone(pstr.wstring, length=s.int()) #FIXME

@OfficeArtFOPTEOP.define
class InkBooleanProperties(pbinary.flags):
    type = 0x073f
    _fields_ = R([
        (1, 'fRenderInk'),
        (1, 'fRenderShape'),
        (1, 'fHitTestInk'),
        (1, 'fInkAnnotation'),
        (12, 'unused1'),
        (1, 'fUsefRenderInk'),
        (1, 'fUsefRenderShape'),
        (1, 'fUsefHItTestInk'),
        (1, 'fUsefInkAnnotation'),
        (12, 'unused2'),
    ])

# Signature Line
@OfficeArtFOPTEOP.define
class wzSigSetupId(uint4):
    type = 0x0781
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupProvId(uint4):
    type = 0x0782
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupSuggSigner(uint4):
    type = 0x0783
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupSuggSigner2(uint4):
    type = 0x0784
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupSuggSignerEmail(uint4):
    type = 0x0785
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupSignInst(uint4):
    type = 0x0786
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupAddlXml(uint4):
    type = 0x0787
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class wzSigSetupProvUrl(uint4):
    type = 0x0788
    complex = lambda s: dyn.clone(pstr.wstring, length=s.int())

@OfficeArtFOPTEOP.define
class SignatureLineBooleanProperties(pbinary.flags):
    type = 0x07bf
    _fields_ = R([
        (1, 'fIsSignatureLine'),
        (1, 'fSigSetupSignInstSet'),
        (1, 'fSigSetupAllowComments'),
        (1, 'fSigSetupShowSignDate'),
        (12, 'unused1'),
        (1, 'fUsefIsSignatureLine'),
        (1, 'fUsefSigSetupSignInsetSet'),
        (1, 'fUsefSigSetupAllowComments'),
        (1, 'fUsefSigSetupShowSignDate'),
        (12, 'unused2'),
    ])

@RT_TimeNode.define
class TimeNodeAtom(pstruct.type):
    type = 0,0x000
    _fields_ = [
        (pint.uint32_t, 'masterID'),    # FIXME: doesn't match up
        (pint.uint32_t, 'restart'),
        (pint.uint32_t, 'type'),
        (pint.uint32_t, 'fill'),
        (pint.uint32_t, 'syncBehavior'),
        (pint.uint8_t, 'fSyncMaster'),
        (pint.uint32_t, 'propertiesSet'),
    ]

if __name__ == '__main__':
    from ptypes import *
    import office.art as art

    if False:
        s = b'\x00\x00\x00\x00\x0c\x00\x00\x00' + b'A'*30
        z = art.RecordGeneral()
        z.source = provider.string(s)

    if False:
        s = b'\x00\x00'+'\x28\xf1'+b'\x10\x00\x00\x00'+b'\x00'*16
        z = art.RecordGeneral()
        z.source = provider.string(s)

    if False:
        header = b'\x00\x00'+b'\x28\xf1' + b'\x10\x00\x00\x00'
        data = b'\x00'*16

        s = header + data + header + data + header + data + header + data
        z = art.RecordContainer()
        z.source = provider.string(s)
        z.size = lambda:len(s)

    if True:
        s = '7ACqAA8AAvAWAQAAEAAI8AgAAAADAAAAEgQAAA8AA/D+AAAADwAE8CgAAAABAAnwEAAAAAAAAAAAAAAAAAAAAAAAAAACAArwCAAAAAAEAAAFAAAADwAE8FIAAACSDArwCAAAAAMEAAAACgAAQwAL8BgAAAB/AAQBBAG/AAgACAD/AQAACAC/AwAAAgAAABDwEgAAAAEAAAAAAAEAAAABAJoBAgAAAAAAEfAAAAAA'
        s = s.decode('base64')[4:] + b'\x00'*800
        print(repr(s))

    if True:
        z = art.RecordGeneral()
        z.source = provider.string(s)
        print(z.l)

    if False:
        import ptypes
        ptypes.setsource( ptypes.provider.file('poc.xls') )

        x = OfficeArtSpContainer()
    #    x.setoffset(66100)
        x.setoffset(66360)
        print(x.l)

    if False:
        class header(pbinary.struct):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        class wtf(pstruct.type):
            _fields_ = [
                (header, 'h'),
                (pint.uint16_t, 't'),
            ]

        z = RecordGeneral()
        z.source = provider.string(b'\x0f\x00\x02\xf0')
        print(z.l)
