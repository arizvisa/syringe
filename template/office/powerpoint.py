import ptypes
from ptypes import *
from . import *
from . import art,graph,storage

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

## Ripped from PowerPoint97-2007BinaryFileFormat(ppt)Specification.pdf
recordType = [
    ('RT_Unknown', 0x0000),
    ('RT_SubContainerCompleted', 0x0001),
    ('RT_IRRAtom', 0x0002),                 # indexed record reference
    ('RT_PSS', 0x0003),                     # start of stream
    ('RT_SubContainerException', 0x0004),
    ('RT_ClientSignal1', 0x0006),
    ('RT_ClientSignal2', 0x0007),
    ('RT_PowerPointStateInfoAtom', 0x000a),
    ('RT_Scheme', 0x03f4),
    ('RT_SchemeAtom', 0x03f5),
    ('RT_DocViewInfo', 0x03f6),
    ('RT_SslideLayoutAtom', 0x03f7),
    ('RT_ViewInfo', 0x03fc),
    ('RT_Texture', 0x0403),
    ('RT_VBASlideInfo', 0x0404),
    ('RT_VBASlideInfoAtom', 0x0405),
    ('RT_OEShape', 0x0bc0),
    ('RT_GrColor', 0x0bcc),
    ('RT_GrectAtom', 0x0bd1),
    ('RT_GratioAtom', 0x0bd7),
    ('RT_Gscaling', 0x0bd8),
    ('RT_GpointAtom', 0x0bda),
    ('RT_TypeFAce', 0x0fb9),
    ('RT_ExternalObject', 0x0fbb),
    ('RT_ExOleObject', 0x0fc2),
    ('RT_ExPlainLinkAtom', 0x0fc4),
    ('RT_CorePict', 0x0fc5),
    ('RT_CorePictAtom', 0x0fc6),
    ('RT_ExPlainAtom', 0x0fc7),
    ('RT_ExLinkAtom_old', 0x0fcf),
    ('RT_ExPlain', 0x0fd5),
    ('RT_ExPlainLink', 0x0fd6),
    ('RT_ReColorEntryAtom', 0x0fde),
    ('RT_EmFormatAtom', 0x0fe1),
    ('RT_CharFormatAtom', 0x0fe2),
    ('RT_ParaFormatAtom', 0x0fe3),
    ('RT_ExQuickTime', 0x0fe9),
    ('RT_ExQuickTimeMovie', 0x0fea),
    ('RT_ExQuickTimeMovieData', 0x0feb),
    ('RT_ExSubscription', 0x0fec),
    ('RT_ExSubscriptionSection', 0x0fed),
    ('RT_SlideList', 0x0ff4),
    ('RT_PersistPtrFullBlock', 0x1771),
    ('RT_RulerIndentAtom', 0x2710),
    ('RT_GscalingAtom', 0x2711),
    ('RT_GrColorAtom', 0x2712),
    ('RT_GLPointAtom', 0x2713),
    ('RT_GlineAtom', 0x2714),
]

## ripped from [MS-PPT]
recordType += [
    ('RT_Document', 0x03e8),
    ('RT_DocumentAtom', 0x03e9),
    ('RT_EndDocumentAtom', 0x03ea),
    ('RT_Slide', 0x03ee),
    ('RT_SlideAtom', 0x03ef),
    ('RT_Notes', 0x03f0),
    ('RT_NotesAtom', 0x03f1),
    ('RT_Environment', 0x03f2),
    ('RT_SlidePersistAtom', 0x03f3),
    ('RT_MainMaster', 0x03f8),
    ('RT_SlideShowSlideInfoAtom', 0x03f9),
    ('RT_SlideViewInfo', 0x03fa),
    ('RT_GuideAtom', 0x03fb),
    ('RT_ViewInfoAtom', 0x03fd),
    ('RT_SlideViewInfoAtom', 0x03fe),
    ('RT_VbaInfo', 0x03ff),
    ('RT_VbaInfoAtom', 0x0400),
    ('RT_SlideShowDocInfoAtom', 0x0401),
    ('RT_Summary', 0x0402),
    ('RT_DocRoutingSlipAtom', 0x0406),
    ('RT_OutlineViewInfo', 0x0407),
    ('RT_SorterViewInfo', 0x0408),
    ('RT_ExternalObjectList', 0x0409),
    ('RT_ExternalObjectListAtom', 0x040a),
    ('RT_DrawingGroup', 0x040b),
    ('RT_Drawing', 0x040c),
    ('RT_GridSpacing10Atom', 0x040d),
    ('RT_RoundTripTheme12Atom', 0x040e),
    ('RT_RoundTripColorMapping12Atom', 0x040f),
    ('RT_NamedShows', 0x0410),
    ('RT_NamedShow', 0x0411),
    ('RT_NamedShowSlidesAtom', 0x0412),
    ('RT_NotesTextViewInfo9', 0x0413),
    ('RT_NormalViewSetInfo9', 0x0414),
    ('RT_NormalViewSetInfo9Atom', 0x0415),
    ('RT_RoundTripOriginalMainMasterId12Atom', 0x041c),
    ('RT_RoundTripCompositeMasterId12Atom', 0x041d),
    ('RT_RoundTripContentMasterInfo12Atom', 0x041e),
    ('RT_RoundTripShapeId12Atom', 0x041f),
    ('RT_RoundTripHFPlaceholder12Atom', 0x0420),
    ('RT_RoundTripContentMasterId12Atom', 0x0422),
    ('RT_RoundTripOArtTextStyles12Atom', 0x0423),
    ('RT_RoundTripHeaderFooterDefaults12Atom', 0x0424),
    ('RT_RoundTripDocFlags12Atom', 0x0425),
    ('RT_RoundTripShapeCheckSumForCL12Atom', 0x0426),
    ('RT_RoundTripNotesMasterTextStyles12Atom', 0x0427),
    ('RT_RoundTripCustomTableStyles12Atom', 0x0428),
    ('RT_List', 0x07d0),
    ('RT_FontCollection', 0x07d5),
    ('RT_FontCollection10', 0x07d6),
    ('RT_BookmarkCollection', 0x07e3),
    ('RT_SoundCollection', 0x07e4),
    ('RT_SoundCollectionAtom', 0x07e5),
    ('RT_Sound', 0x07e6),
    ('RT_SoundDataBlob', 0x07e7),
    ('RT_BookmarkSeedAtom', 0x07e9),
    ('RT_ColorSchemeAtom', 0x07f0),
    ('RT_BlipCollection9', 0x07f8),
    ('RT_BlipEntity9Atom', 0x07f9),
    ('RT_ExternalObjectRefAtom', 0x0bc1),
    ('RT_PlaceholderAtom', 0x0bc3),
    ('RT_ShapeAtom', 0x0bdb),
    ('RT_ShapeFlags10Atom', 0x0bdc),
    ('RT_RoundTripNewPlaceholderId12Atom', 0x0bdd),
    ('RT_OutlineTextRefAtom', 0x0f9e),
    ('RT_TextHeaderAtom', 0x0f9f),
    ('RT_TextCharsAtom', 0x0fa0),
    ('RT_StyleTextPropAtom', 0x0fa1),
    ('RT_MasterTextPropAtom', 0x0fa2),
    ('RT_TextMasterStyleAtom', 0x0fa3),
    ('RT_TextCharFormatExceptionAtom', 0x0fa4),
    ('RT_TextParagraphFormatExceptionAtom', 0x0fa5),
    ('RT_TextRulerAtom', 0x0fa6),
    ('RT_TextBookmarkAtom', 0x0fa7),
    ('RT_TextBytesAtom', 0x0fa8),
    ('RT_TextSpecialInfoDefaultAtom', 0x0fa9),
    ('RT_TextSpecialInfoAtom', 0x0faa),
    ('RT_DefaultRulerAtom', 0x0fab),
    ('RT_StyleTextProp9Atom', 0x0fac),
    ('RT_TextMasterStyle9Atom', 0x0fad),
    ('RT_OutlineTextProps9', 0x0fae),
    ('RT_OutlineTextPropsHeader9Atom', 0x0faf),
    ('RT_TextDefaults9Atom', 0x0fb0),
    ('RT_StyleTextProp10Atom', 0x0fb1),
    ('RT_TextMasterStyle10Atom', 0x0fb2),
    ('RT_OutlineTextProps10', 0x0fb3),
    ('RT_TextDefaults10Atom', 0x0fb4),
    ('RT_OutlineTextProps11', 0x0fb5),
    ('RT_StyleTextProp11Atom', 0x0fb6),
    ('RT_FontEntityAtom', 0x0fb7),
    ('RT_FontEmbedDataBlob', 0x0fb8),
    ('RT_CString', 0x0fba),
    ('RT_MetaFile', 0x0fc1),
    ('RT_ExternalOleObjectAtom', 0x0fc3),
    ('RT_Kinsoku', 0x0fc8),
    ('RT_Handout', 0x0fc9),
    ('RT_ExternalOleEmbed', 0x0fcc),
    ('RT_ExternalOleEmbedAtom', 0x0fcd),
    ('RT_ExternalOleLink', 0x0fce),
    ('RT_BookmarkEntityAtom', 0x0fd0),
    ('RT_ExternalOleLinkAtom', 0x0fd1),
    ('RT_KinsokuAtom', 0x0fd2),
    ('RT_ExternalHyperlinkAtom', 0x0fd3),
    ('RT_ExternalHyperlink', 0x0fd7),
    ('RT_SlideNumberMetaCharAtom', 0x0fd8),
    ('RT_HeadersFooters', 0x0fd9),
    ('RT_HeadersFootersAtom', 0x0fda),
    ('RT_TextInteractiveInfoAtom', 0x0fdf),
    ('RT_ExternalHyperlink9', 0x0fe4),
    ('RT_RecolorInfoAtom', 0x0fe7),
    ('RT_ExternalOleControl', 0x0fee),
    ('RT_SlideListWithText', 0x0ff0),
    ('RT_AnimationInfoAtom', 0x0ff1),
    ('RT_InteractiveInfo', 0x0ff2),
    ('RT_InteractiveInfoAtom', 0x0ff3),
    ('RT_UserEditAtom', 0x0ff5),
    ('RT_CurrentUserAtom', 0x0ff6),
    ('RT_DateTimeMetaCharAtom', 0x0ff7),
    ('RT_GenericDateMetaCharAtom', 0x0ff8),
    ('RT_HeaderMetaCharAtom', 0x0ff9),
    ('RT_FooterMetaCharAtom', 0x0ffa),
    ('RT_ExternalOleControlAtom', 0x0ffb),
    ('RT_ExternalMediaAtom', 0x1004),
    ('RT_ExternalVideo', 0x1005),
    ('RT_ExternalAviMovie', 0x1006),
    ('RT_ExternalMciMovie', 0x1007),
    ('RT_ExternalMidiAudio', 0x100d),
    ('RT_ExternalCdAudio', 0x100e),
    ('RT_ExternalWavAudioEmbedded', 0x100f),
    ('RT_ExternalWavAudioLink', 0x1010),
    ('RT_ExternalOleObjectStg', 0x1011),
    ('RT_ExternalCdAudioAtom', 0x1012),
    ('RT_ExternalWavAudioEmbeddedAtom', 0x1013),
    ('RT_AnimationInfo', 0x1014),
    ('RT_RtfDateTimeMetaCharAtom', 0x1015),
    ('RT_ExternalHyperlinkFlagsAtom', 0x1018),
    ('RT_ProgTags', 0x1388),
    ('RT_ProgStringTag', 0x1389),
    ('RT_ProgBinaryTag', 0x138a),
    ('RT_BinaryTagDataBlob', 0x138b),
    ('RT_PrintOptionsAtom', 0x1770),
    ('RT_PersistDirectoryAtom', 0x1772),
    ('RT_PresentationAdvisorFlags9Atom', 0x177a),
    ('RT_HtmlDocInfo9Atom', 0x177b),
    ('RT_HtmlPublishInfoAtom', 0x177c),
    ('RT_HtmlPublishInfo9', 0x177d),
    ('RT_BroadcastDocInfo9', 0x177e),
    ('RT_BroadcastDocInfo9Atom', 0x177f),
    ('RT_EnvelopeFlags9Atom', 0x1784),
    ('RT_EnvelopeData9Atom', 0x1785),
    ('RT_VisualShapeAtom', 0x2afb),
    ('RT_HashCodeAtom', 0x2b00),
    ('RT_VisualPageAtom', 0x2b01),
    ('RT_BuildList', 0x2b02),
    ('RT_BuildAtom', 0x2b03),
    ('RT_ChartBuild', 0x2b04),
    ('RT_ChartBuildAtom', 0x2b05),
    ('RT_DiagramBuild', 0x2b06),
    ('RT_DiagramBuildAtom', 0x2b07),
    ('RT_ParaBuild', 0x2b08),
    ('RT_ParaBuildAtom', 0x2b09),
    ('RT_LevelInfoAtom', 0x2b0a),
    ('RT_RoundTripAnimationAtom12Atom', 0x2b0b),
    ('RT_RoundTripAnimationHashAtom12Atom', 0x2b0d),
    ('RT_Comment10', 0x2ee0),
    ('RT_Comment10Atom', 0x2ee1),
    ('RT_CommentIndex10', 0x2ee4),
    ('RT_CommentIndex10Atom', 0x2ee5),
    ('RT_LinkedShape10Atom', 0x2ee6),
    ('RT_LinkedSlide10Atom', 0x2ee7),
    ('RT_SlideFlags10Atom', 0x2eea),
    ('RT_SlideTime10Atom', 0x2eeb),
    ('RT_DiffTree10', 0x2eec),
    ('RT_Diff10', 0x2eed),
    ('RT_Diff10Atom', 0x2eee),
    ('RT_SlideListTableSize10Atom', 0x2eef),
    ('RT_SlideListEntry10Atom', 0x2ef0),
    ('RT_SlideListTable10', 0x2ef1),
    ('RT_CryptSession10Container', 0x2f14),
    ('RT_FontEmbedFlags10Atom', 0x32c8),
    ('RT_FilterPrivacyFlags10Atom', 0x36b0),
    ('RT_DocToolbarStates10Atom', 0x36b1),
    ('RT_PhotoAlbumInfo10Atom', 0x36b2),
    ('RT_SmartTagStore11Container', 0x36b3),
    ('RT_RoundTripSlideSyncInfo12', 0x3714),
    ('RT_RoundTripSlideSyncInfoAtom12', 0x3715),
    #('RT_TimeConditionContainer', 0xf125),         # office.art
    #('RT_TimeNode', 0xf127),                       # office.art
    #('RT_TimeCondition', 0xf128),                  # office.art
    #('RT_TimeModifier', 0xf129),                   # office.art
    #('RT_TimeBehaviorContainer', 0xf12a),          # office.art
    #('RT_TimeAnimateBehaviorContainer', 0xf12b),   # office.art
    #('RT_TimeColorBehaviorContainer', 0xf12c),     # office.art
    #('RT_TimeEffectBehaviorContainer', 0xf12d),    # office.art
    #('RT_TimeMotionBehaviorContainer', 0xf12e),    # office.art
    #('RT_TimeRotationBehaviorContainer', 0xf12f),  # office.art
    #('RT_TimeScaleBehaviorContainer', 0xf130),     # office.art
    #('RT_TimeSetBehaviorContainer', 0xf131),       # office.art
    #('RT_TimeCommandBehaviorContainer', 0xf132),   # office.art
    #('RT_TimeBehavior', 0xf133),                   # office.art
    #('RT_TimeAnimateBehavior', 0xf134),            # office.art
    #('RT_TimeColorBehavior', 0xf135),              # office.art
    #('RT_TimeEffectBehavior', 0xf136),             # office.art
    #('RT_TimeMotionBehavior', 0xf137),             # office.art
    #('RT_TimeRotationBehavior', 0xf138),           # office.art
    #('RT_TimeScaleBehavior', 0xf139),              # office.art
    #('RT_TimeSetBehavior', 0xf13a),                # office.art
    #('RT_TimeCommandBehavior', 0xf13b),            # office.art
    #('RT_TimeClientVisualElement', 0xf13c),        # office.art
    #('RT_TimePropertyList', 0xf13d),               # office.art
    #('RT_TimeVariantList', 0xf13e),                # office.art
    #('RT_TimeAnimationValueList', 0xf13f),         # office.art
    #('RT_TimeIterateData', 0xf140),                # office.art
    #('RT_TimeSequenceData', 0xf141),               # office.art
    #('RT_TimeVariant', 0xf142),                    # office.art
    #('RT_TimeAnimationValue', 0xf143),             # office.art
    #('RT_TimeExtTimeNodeContainer', 0xf144),       # office.art
    #('RT_TimeSubEffectContainer', 0xf145),         # office.art
]

# create a ptype.definition for each record type
locals().update(map(RecordType.define,recordType))

## ripped from [MS-PPT]

# Current User Stream
@RT_UserEditAtom.define
class UserEditAtom(pstruct.type):
    type = 0,0x000
    _fields_ = [
        (sint4, 'lastSlideIDRef'),
        (uint2, 'version'),
        (ubyte1, 'minorVersion'),
        (ubyte1, 'majorVersion'),
        (dyn.pointer(lambda self: UserEditAtom), 'offsetLastEdit'),
        (dyn.pointer(RecordGeneral), 'offsetPersistDirectory'),
        (uint4, 'docPersistIdRef'),
        (uint4, 'persistIdSeed'),
        (sint2, 'lastView'),
        (dyn.block(2), 'unused'),
    ]

@RT_CurrentUserAtom.define
class CurrentUserAtom(pstruct.type):
    type = 0x0,0x000
    _fields_ = [
        (uint4, 'size'),
        (dyn.block(4), 'headerToken'),
        (dyn.pointer(RecordGeneral), 'offsetToCurrentEdit'),
        (uint2, 'lenUserName'),
        (uint2, 'docfileversion'),
        (ubyte1, 'majorVersion'),
        (ubyte1, 'minorVersion'),
        (dyn.block(2), 'unused'),
        (lambda self: dyn.clone(pstr.string, length=self['lenUserName'].li.int()), 'ansiUserName'),
        (uint4, 'relVersion'),
#        (lambda self: dyn.clone(pstr.wstring,length=2 * self['lenUserName'].li.int()), 'unicodeUserName'),
    ]

# PowerPoint Document stream
class PersistDirectoryEntry(pstruct.type):
    class _info(pbinary.struct):
        _fields_ = R([(20,'persistId'), (12, 'cPersist')])

    _fields_ = [
        (_info, 'info'),
        (lambda self: dyn.array( dyn.pointer(RecordGeneral), self['info'].li['cPersist'] ), 'offsets')
    ]

    def summary(self):
        info = self['info']
        info_s = 'info.persistId:{:#x} info.cPersist:{:#x}'.format(info['persistId'], info['cPersist'])
        offset = __import__('array').array('L', self['offsets'].serialize())
        res = map('{:#x}'.format, offset)
        offset_s = 'offsets:({:s})'.format(','.join(res))
        return ' '.join((info_s, offset_s))

    def repr(self):
        return self.summary()

    def walk(self):
        # heh
        for n in self['offsets']:
            res = n.d.li
            yield res['data'] if getattr(res, 'lazy', false) else res['data'].d.l
        return

@RT_PersistDirectoryAtom.define
class PersistDirectoryAtom(parray.block):
    type = 0,0x000
    _object_ = PersistDirectoryEntry
    def walk(self):
        for v in self:
            for n in v.walk():
                yield n
            continue
        return

@RT_Document.define
class DocumentContainer(RecordContainer):
    type = 15,0x000

@RT_EndDocumentAtom.define
class EndDocumentAtom(pstruct.type):
    type = 0,0x000
    _fields_ = []

@RT_PlaceholderAtom.define
class PlaceholderAtom(pstruct.type):
    type = 0,0x000

    class __placeholderid(pint.enum, ubyte1):
        _values_ = [
            ('None', 0), ('MasterTitle', 1), ('MasterBody', 2), ('MasterCenteredTitle', 3), ('MasterNotesSlideImage', 4),
            ('MasterNotesBodyImage', 5), ('MasterDate', 6), ('MasterSlideNumber', 7), ('MasterFooter', 8), ('MasterHeader', 9),
            ('MasterSubtitle', 10), ('GenericTextObject', 11), ('Title', 12), ('Body', 13), ('NotesBody', 14), ('CenteredTitle', 15),
            ('Subtitle', 16), ('VerticalTextTitle', 17), ('VerticalTextBody', 18), ('NotesSlideImage', 19), ('Object', 20),
            ('Graph', 21), ('Table', 22), ('ClipArt', 23), ('OrganizationChart', 24), ('MediaClip', 25),
        ]

    def __unused(self):
        try:
            p = self.getparent(RecordGeneral)
            sz = p['header'].li.Length()
        except ptypes.error.ItemNotFoundError:
            return dyn.block(0)
        return dyn.block(sz - 6)

    _fields_ = [
        (uint4, 'placementId'),
        (__placeholderid, 'placeholderId'),
        (ubyte1, 'size'),
        (__unused, 'unused'),
    ]

@RT_ExternalObjectRefAtom.define
class ExObjRefAtom(pstruct.type):
    type = 0,0x000
    _fields_ = [
        (uint4, 'exObjId')
    ]

class SlideLayoutType(pint.enum, uint4): _values_ = []
class PlaceHolderEnum(pint.enum, ubyte1): _values_ = []
class MasterIdRef(uint4): pass
class NotesIdRef(uint4): pass
class SlideFlags(pbinary.struct):
    _fields_ = R([(1,'fMasterObjects'),(1,'fMasterScheme'),(1,'fMasterBackground'),(13,'reserved')])

@RT_SlideAtom.define
class SlideAtom(pstruct.type):
    type = 2,0x000
    _fields_ = [
        (SlideLayoutType, 'geom'),
        (dyn.array(PlaceHolderEnum,8), 'rgPlaceholderTypes'),
        (MasterIdRef, 'masterIdRef'),
        (NotesIdRef, 'notesIdRef'),
        (SlideFlags, 'slideFlags'),
        (uint2, 'unused')
    ]

@RT_MainMaster.define
class MainMaster(RecordContainer):
    type = 15,0x000

@RT_Slide.define
class SlideContainer(RecordContainer):
    type = 15,0x000

@RT_BinaryTagDataBlob.define
class BinaryTagData(RecordContainer):
    type = 0,0x000

@RT_ProgBinaryTag.define
class SlideProgBinaryTagContainer(RecordContainer):
    type = 15,0x000

@RT_ProgTags.define
class SlideProgTagsContainer(RecordContainer):
    type = 15,0x000

@RT_Notes.define
class NotesContainer(RecordContainer):
    type = 15,0x000

@RT_Drawing.define
class DrawingContainer(RecordContainer):
    type = 15,0x000

@RT_Handout.define
class HandoutContainer(RecordContainer):
    type = 15,0x000

class ColorStruct(pstruct.type):
    _fields_= [
        (ubyte1,'red'),
        (ubyte1,'green'),
        (ubyte1,'blue'),
        (ubyte1,'unused'),
    ]

@RT_ColorSchemeAtom.define
class SlideSchemeColorSchemeAtom(parray.type):
    type = 0,0x001
    length = 8
    _object_ = ColorStruct

@RT_ColorSchemeAtom.define
class SchemeListElementColorSchemeAtom(parray.type):
    type = 0,0x006
    length = 8
    _object_ = ColorStruct

@RT_HashCodeAtom.define
class HashCode10Atom(pstruct.type):
    type = 0,0x000
    _fields_ = [(uint4, 'hash')]

class FILETIME(pstruct.type):
    _fields_ = [(uint4, 'dwLowDateTime'),(uint4, 'dwHighDateTime')]

@RT_SlideTime10Atom.define
class SlideTime10Atom(FILETIME):
    type = 0,0x000

@RT_ParaBuild.define
class ParaBuildContainer(RecordContainer):
    type = 15,0x000         # FIXME

@RT_BuildList.define
class BuildListContainer(RecordContainer):
    type = 15,0x000

@RT_VisualShapeAtom.define
class VisualShapeGeneralAtom(pstruct.type):
    type = 0,0x000

    _fields_ = [
        (uint4, 'type'),
        (uint4, 'refType'),
        (uint4, 'id'),
        (sint4, 'data0'),
        (sint4, 'data1'),
    ]

class PointStruct(pstruct.type):
    _fields_ = [
        (sint4, 'x'),
        (sint4, 'y')
    ]

class RatioStruct(pstruct.type):
    _fields_ = [
        (sint4, 'number'),
        (sint4, 'denom'),
    ]

class PersistIdRef(uint4): pass

class SlideSizeEnum(pint.enum, uint2):
    _values_ = [
        ('SS_Screen', 0x0000),
        ('SS_LetterPaper', 0x0001),
        ('SS_A4Paper', 0x0002),
        ('SS_35mm', 0x0003),
        ('SS_Overhead', 0x0004),
        ('SS_Banner', 0x0005),
        ('SS_Custom', 0x0006),
    ]

@RT_DocumentAtom.define
class DocumentAtom(pstruct.type):
    type = 1,0x000
    _fields_ = [
        (PointStruct, 'slideSize'),
        (PointStruct, 'notesSize'),
        (RatioStruct, 'serverZoom'),
        (PersistIdRef, 'notesMasterPersistIdRef'),
        (PersistIdRef, 'handoutMasterPersistIdRef'),
        (uint2, 'firstSlideNumber'),
        (SlideSizeEnum, 'slideSizeType'),
        (bool1, 'fSaveWithFonts'),
        (bool1, 'fOmitTitlePlace'),
        (bool1, 'fRightToLeft'),
        (bool1, 'fShowComments'),
    ]

class TextTypeEnum(pint.enum):
    _values_ = [
        ( 'Tx_TYPE_TITLE', 0x00000000 ),        # Title placeholder shape text.
        ( 'Tx_TYPE_BODY', 0x00000001 ),         # Body placeholder shape text.
        ( 'Tx_TYPE_NOTES', 0x00000002 ),        # Notes placeholder shape text.
        ( 'Tx_TYPE_OTHER', 0x00000004 ),        # Any other text.
        ( 'Tx_TYPE_CENTERBODY', 0x00000005 ),   # Center body placeholder shape text.
        ( 'Tx_TYPE_CENTERTITLE', 0x00000006 ),  # Center title placeholder shape text.
        ( 'Tx_TYPE_HALFBODY', 0x00000007 ),     # Half-sized body placeholder shape text.
        ( 'Tx_TYPE_QUARTERBODY', 0x00000008 ),  # Quarter-sized body placeholder shape text.
    ]

class PFMasks(pbinary.flags):
    _fields_ = R([
        (1, 'hasBullet'),
        (1, 'bulletHasFont'),
        (1, 'bulletHasColor'),
        (1, 'bulletHasSize'),
        (1, 'bulletFont'),
        (1, 'bulletColor'),
        (1, 'bulletSize'),
        (1, 'bulletChar'),
        (1, 'leftMargin'),
        (1, 'unused'),
        (1, 'indent'),
        (1, 'align'),
        (1, 'lineSpacing'),
        (1, 'spaceBefore'),
        (1, 'spaceAfter'),
        (1, 'defaultTabSize'),
        (1, 'fontAlign'),
        (1, 'charWrap'),
        (1, 'wordWrap'),
        (1, 'overflow'),
        (1, 'tabStops'),
        (1, 'textDirection'),
        (1, 'reserved1'),
        (1, 'bulletBlip'),
        (1, 'bulletScheme'),
        (1, 'bulletHasScheme'),
        (6, 'reserved2'),
    ])

class BulletFlags(pbinary.flags):
    _fields_ = R([
        (1, 'fHasBullet'),
        (1, 'fBulletHasFont'),
        (1, 'fBulletHasColor'),
        (1, 'fBulletHasSize'),
        (12, 'reserved'),
    ])

class BulletSize(sint2): pass

class TextAlignmentEnum(pint.enum, uint2):
    _values_ = [
        ('Tx_ALIGNLeft', 0x0000), # For horizontal text, left aligned.  For vertical text, top aligned.
        ('Tx_ALIGNCenter', 0x0001), # For horizontal text, centered.  For vertical text, middle aligned.
        ('Tx_ALIGNRight', 0x0002), # For horizontal text, right aligned.  For vertical text, bottom aligned.
        ('Tx_ALIGNJustify', 0x0003), # For horizontal text, flush left and right.  For vertical text, flush top and bottom.
        ('Tx_ALIGNDistributed', 0x0004), # Distribute space between characters.
        ('Tx_ALIGNThaiDistributed', 0x0005), # Thai distribution justification.
        ('Tx_ALIGNJustifyLow', 0x0006), # Kashida justify low.
    ]

class ParaSpacing(sint2): pass
class MarginOrIndent(sint2): pass
class TabSize(sint2): pass

class TabStops(pstruct.type):
    _fields_ = [
        (uint2, 'count'),
        (lambda self: dyn.array(TabStop, self['count'].li.int()), 'rgTabStop'),
    ]

class TextTabTypeEnum(pint.enum, uint2):
    _values_ = [
        ('Tx_TABLeft', 0x0000), # Left-aligned tab stop.
        ('Tx_TABCenter', 0x0001), # Center-aligned tab stop.
        ('Tx_TABRight', 0x0002), # Right-aligned tab stop.
        ('Tx_TABDecimal', 0x0003), # Decimal point-aligned tab stop.
    ]

class TabStop(pstruct.type):
    _fields_ = [
        (sint2, 'position'),
        (TextTabTypeEnum, 'type'),
    ]

class TextFontAlignmentEnum(pint.enum, uint2):
    _values_ = [
        ('Tx_ALIGNFONTRoman', 0x0000), # Place characters on font baseline.
        ('Tx_ALIGNFONTHanging', 0x0001), # Characters hang from top of line height
        ('Tx_ALIGNFONTCenter', 0x0002), # Characters centered within line height.
        ('Tx_ALIGNFONTUpholdFixed', 0x0003), # Characters are anchored to the very bottom of a single line. This is different than Tx_ALIGNFONTRoman because of letters such as "g", "q", and "y".
    ]

class PFWrapFlags(pbinary.flags):
    _fields_ = R([
        (1, 'charWrap'),
        (1, 'wordWrap'),
        (1, 'overflow'),
        (13, 'reserved'),
    ])

class TextDirectionEnum(pint.enum, uint2):
    _values_ = [
        ('LeftToRight', 0x0000),
        ('RightToLeft', 0x0001),
    ]

class FontIndexRef(uint2): pass

class ColorIndexStruct(pstruct.type):
    class _index(pint.enum, ubyte1):
        _values_ = [
            ('Background', 0x00),
            ('Text', 0x01),
            ('Shadow', 0x02),
            ('Title', 0x03),
            ('Fill', 0x04),
            ('Accent1', 0x05),
            ('Accent2', 0x06),
            ('Accent3', 0x07),
            ('sRGB', 0xFE),
            ('undefined', 0xFF),
        ]
    _fields_ = [
        (ubyte1, 'red'),
        (ubyte1, 'green'),
        (ubyte1, 'blue'),
        (_index, 'index'),
    ]

class TextPFException(pstruct.type):
    fmask = lambda T,F: lambda *fields: lambda self: T if any(self['masks'].li[f] for f in fields) else F
    _fields_ = [
        (PFMasks, 'masks'),
        (fmask(BulletFlags,undefined)('hasBullet', 'bulletHasFont', 'bulletHasColor', 'bulletHasSize'), 'bulletFlags'),
        (fmask(sint2,pint.sint_t)('bulletChar'), 'bulletChar'),
        (fmask(FontIndexRef,pint.uint_t)('bulletFont'), 'bulletFontRef'),
        (fmask(BulletSize,pint.sint_t)('bulletSize'), 'bulletSize'),
        (fmask(ColorIndexStruct,undefined)('bulletColor'), 'bulletColor'),
        (fmask(TextAlignmentEnum,pint.uint_t)('align'), 'textAlignment'),
        (fmask(ParaSpacing,pint.sint_t)('lineSpacing'), 'lineSpacing'),
        (fmask(ParaSpacing,pint.sint_t)('spaceBefore'), 'spaceBefore'),
        (fmask(ParaSpacing,pint.sint_t)('spaceAfter'), 'spaceAfter'),
        (fmask(MarginOrIndent,pint.sint_t)('leftMargin'), 'leftMargin'),
        (fmask(MarginOrIndent,pint.sint_t)('indent'), 'indent'),
        (fmask(TabSize,pint.sint_t)('defaultTabSize'), 'defaultTabSize'),
        (fmask(TabStops,undefined)('tabStops'), 'tabStops'),
        (fmask(TextFontAlignmentEnum,pint.uint_t)('fontAlign'), 'fontAlign'),
        (fmask(PFWrapFlags,undefined)('charWrap','wordWrap','overflow'), 'wrapFlags'),
        (fmask(TextDirectionEnum,pint.uint_t)('textDirection'), 'textDirection'),
    ]

class CFMasks(pbinary.flags):
    _fields_ = R([
        (1, 'bold'),
        (1, 'italic'),
        (1, 'underline'),
        (1, 'unused1'),
        (1, 'shadow'),
        (1, 'fehint'),
        (1, 'unused2'),
        (1, 'kumi'),
        (1, 'unused3'),
        (1, 'emboss'),
        (4, 'fHasStyle'),
        (2, 'unused4'),
        (1, 'typeface'),
        (1, 'size'),
        (1, 'color'),
        (1, 'position'),
        (1, 'pp10ext'),
        (1, 'oldEATypeface'),
        (1, 'ansiTypeface'),
        (1, 'symbolTypeface'),
        (1, 'newEATypeface'),
        (1, 'csTypeface'),
        (1, 'pp11ext'),
        (5, 'reserved'),
    ])

class CFStyle(pbinary.flags):
    _fields_ = R([
        (1, 'bold'),
        (1, 'italic'),
        (1, 'underline'),
        (1, 'unused1'),
        (1, 'shadow'),
        (1, 'fehint'),
        (1, 'unused2'),
        (1, 'kumi'),
        (1, 'unused3'),
        (1, 'emboss'),
        (4, 'pp9rt'),
        (2, 'unused4'),
    ])

class TextCFException(pstruct.type):
    fmask = lambda T,F: lambda *fields: lambda self: T if any(self['masks'].li[f] for f in fields) else F
    _fields_ = [
        (CFMasks, 'masks'),
        (fmask(CFStyle,undefined)('bold','italic','underline','shadow','fehint','kumi','emboss','fHasStyle'), 'fontStyle'),
        (fmask(FontIndexRef,pint.uint_t)('typeface'), 'fontRef'),
        (fmask(FontIndexRef,pint.uint_t)('oldEATypeface'), 'oldEAFontRef'),
        (fmask(FontIndexRef,pint.uint_t)('ansiTypeface'), 'ansiFontRef'),
        (fmask(FontIndexRef,pint.uint_t)('symbolTypeface'), 'symbolFontRef'),
        (fmask(sint2,pint.sint_t)('size'), 'fontSize'),
        (fmask(ColorIndexStruct,undefined)('color'), 'color'),
        (fmask(sint2,pint.sint_t)('position'), 'position'),
    ]

class TextMasterStyleLevel(pstruct.type):
    def __level(self):
        try:
            p = self.getparent(type=RecordGeneral)
            _,instance = p['header'].Instance()
            res = uint2 if instance >= 5 else pint.uint_t
        except ptypes.error.ItemNotFoundError:
            res = pint.uint_t
        return res

    _fields_ = [
        (__level, 'level'),
        (TextPFException, 'pf'),
        (TextCFException, 'cf'),
    ]

@RT_TextMasterStyleAtom.define
class TextMasterStyleAtom(pstruct.type):
    type = 0, None
    _fields_ = [
        (uint2, 'cLevels'),
        (lambda self: dyn.array(TextMasterStyleLevel, min(5, self['cLevels'].li.int())), 'lstLvl'),
    ]

@RT_Environment.define
class DocumentTextInfoContainer(RecordContainer):
    type = 15,0x000
    _values_ = [
        #('kinsoku', KinsokuContainer),
        #('fontCollection', FontCollectionContainer),
        #('textCFDefaultsAtom', TextCFExceptionAtom),
        #('textPFDefaultsAtom', TextPFExceptionAtom),
        #('defaultRulerAtom', DefaultRulerAtom),
        #('textSIDefaultsAtom', TextSIExceptionAtom),
        ('textMasterStyleAtom', TextMasterStyleAtom),
    ]

@RT_DrawingGroup.define
class DrawingGroupContainer(RecordContainer):
    type = 15,0x000
    _values_ = [
    # FIXME
        #('OfficeArtDgg', OfficeArtDggContainer),
    ]

@RT_SlideListWithText.define
class MasterListWithTextContainer(RecordContainer):
    type = 15,0x001
    _values_ = [
    # FIXME
    #    ('rgMasterPersistAtom', MasterPersistAtom),
    ]

@RT_List.define
class DocInfoListContainer(RecordContainer):
    type = 15,0x000
    _values = [
    # FIXME
    ]

@storage.DirectoryStream.define
class File(File):
    type = 'PowerPoint Document'

if __name__ == '__main__':
    import office.powerpoint as pp
    import ptypes
    from ptypes import *

    if False:
        s = b'\x00\x00\x00\x00\x0c\x00\x00\x00' + b'A'*30
        z = pp.RecordGeneral()
        z.source = provider.string(s)
        print(z.l)

    if False:
        s = b'\x00\x00'+b'\xc3\x0b'+b'\x06\x00\x00\x00'+b'\r\n\x0e\r\xcc\x00'
        z = pp.RecordGeneral()
        z.source = provider.string(s)
        print(z.l)

    if False:
        header = b'\x00\x00'+b'\xc3\x0b' + b'\x06\x00\x00\x00'
        data = b'\x00'*6

        s = (header + data)*4
        z = pp.RecordContainer()
        z.source = provider.string(s+b'\xff'*8)
        z.size = lambda:(len(header)+len(data))*4
        print(z.l)

    if False:
        header = b'\x00\x00'+b'\xc3\x0b' + b'\x06\x00\x00\x00'
        data = b'\x00'*6
        element = header+data

        container = b'\x00\x00'+b'\xe8\x03' + b'\x38\x00\x00\x00'
        s = element*4
        container += s

        z = pp.RecordGeneral()
        z.source = ptypes.provider.string(container)
        z.size = lambda:len(container)
        print(z.l)

    if False:
        z = pp.File(source=ptypes.prov.file('./powerpoint.stream',mode='r'))
        z=z.l
        print(z[0].initializedQ())
        print(z[0]['data'][2]['data'])

    if False:
        import ptypes,office.powerpoint as powerpoint
        usersource = ptypes.provider.file('user.stream')
        datasource = ptypes.provider.file('data.stream')

        user = powerpoint.File(source=usersource).l
        datastream = powerpoint.File(source=datasource).l

        currentuseratom = user[0]['data']
        currentedit = currentuseratom['offsetToCurrentEdit'].d      # points to offset inside a data stream
        currentedit.source = datastream.source
        print(currentedit.l)
        usereditatom = currentedit['data']
        persistdirectory = usereditatom['offsetPersistDirectory'].d

        # go through persist directory
        for i,entry in enumerate(persistdirectory.li['data']):
            print('{:s} {:x}'.format('-'*70, i))
            for obj in entry.walk():
                print(obj)
            continue

