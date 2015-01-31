from ptypes import *
import art,graph

import __init__
class Record(__init__.Record): cache = {}
class RecordGeneral(__init__.RecordGeneral): Record=Record
class RecordContainer(__init__.RecordContainer): _object_ = RecordGeneral
class File(__init__.File): _object_ = RecordGeneral

class bool1(pint.uint8_t): pass
class ubyte1(pint.uint8_t): pass
class uint2(pint.uint16_t): pass
class uint4(pint.uint32_t): pass
class sint2(pint.int16_t): pass
class sint4(pint.int32_t): pass

# FIXME: each type should be a tuple of
#        (rh.recVer, rh.recInstance, rh.recType)

# record types
class RecordType(pint.enum, uint4):
    _values_ = [
        ('RT_Document', 0x03E8),
        ('RT_DocumentAtom', 0x03E9),
        ('RT_EndDocumentAtom', 0x03EA),
        ('RT_Slide', 0x03EE),
        ('RT_SlideAtom', 0x03EF),
        ('RT_Notes', 0x03F0),
        ('RT_NotesAtom', 0x03F1),
        ('RT_Environment', 0x03F2),
        ('RT_SlidePersistAtom', 0x03F3),
        ('RT_MainMaster', 0x03F8),
        ('RT_SlideShowSlideInfoAtom', 0x03F9),
        ('RT_SlideViewInfo', 0x03FA),
        ('RT_GuideAtom', 0x03FB),
        ('RT_ViewInfoAtom', 0x03FD),
        ('RT_SlideViewInfoAtom', 0x03FE),
        ('RT_VbaInfo', 0x03FF),
        ('RT_VbaInfoAtom', 0x0400),
        ('RT_SlideShowDocInfoAtom', 0x0401),
        ('RT_Summary', 0x0402),
        ('RT_DocRoutingSlipAtom', 0x0406),
        ('RT_OutlineViewInfo', 0x0407),
        ('RT_SorterViewInfo', 0x0408),
        ('RT_ExternalObjectList', 0x0409),
        ('RT_ExternalObjectListAtom', 0x040A),
        ('RT_DrawingGroup', 0x040B),
        ('RT_Drawing', 0x040C),
        ('RT_GridSpacing10Atom', 0x040D),
        ('RT_RoundTripTheme12Atom', 0x040E),
        ('RT_RoundTripColorMapping12Atom', 0x040F),
        ('RT_NamedShows', 0x0410),
        ('RT_NamedShow', 0x0411),
        ('RT_NamedShowSlidesAtom', 0x0412),
        ('RT_NotesTextViewInfo9', 0x0413),
        ('RT_NormalViewSetInfo9', 0x0414),
        ('RT_NormalViewSetInfo9Atom', 0x0415),
        ('RT_RoundTripOriginalMainMasterId12Atom', 0x041C),
        ('RT_RoundTripCompositeMasterId12Atom', 0x041D),
        ('RT_RoundTripContentMasterInfo12Atom', 0x041E),
        ('RT_RoundTripShapeId12Atom', 0x041F),
        ('RT_RoundTripHFPlaceholder12Atom', 0x0420),
        ('RT_RoundTripContentMasterId12Atom', 0x0422),
        ('RT_RoundTripOArtTextStyles12Atom', 0x0423),
        ('RT_RoundTripHeaderFooterDefaults12Atom', 0x0424),
        ('RT_RoundTripDocFlags12Atom', 0x0425),
        ('RT_RoundTripShapeCheckSumForCL12Atom', 0x0426),
        ('RT_RoundTripNotesMasterTextStyles12Atom', 0x0427),
        ('RT_RoundTripCustomTableStyles12Atom', 0x0428),
        ('RT_List', 0x07D0),
        ('RT_FontCollection', 0x07D5),
        ('RT_FontCollection10', 0x07D6),
        ('RT_BookmarkCollection', 0x07E3),
        ('RT_SoundCollection', 0x07E4),
        ('RT_SoundCollectionAtom', 0x07E5),
        ('RT_Sound', 0x07E6),
        ('RT_SoundDataBlob', 0x07E7),
        ('RT_BookmarkSeedAtom', 0x07E9),
        ('RT_ColorSchemeAtom', 0x07F0),
        ('RT_BlipCollection9', 0x07F8),
        ('RT_BlipEntity9Atom', 0x07F9),
        ('RT_ExternalObjectRefAtom', 0x0BC1),
        ('RT_PlaceholderAtom', 0x0BC3),
        ('RT_ShapeAtom', 0x0BDB),
        ('RT_ShapeFlags10Atom', 0x0BDC),
        ('RT_RoundTripNewPlaceholderId12Atom', 0x0BDD),
        ('RT_OutlineTextRefAtom', 0x0F9E),
        ('RT_TextHeaderAtom', 0x0F9F),
        ('RT_TextCharsAtom', 0x0FA0),
        ('RT_StyleTextPropAtom', 0x0FA1),
        ('RT_MasterTextPropAtom', 0x0FA2),
        ('RT_TextMasterStyleAtom', 0x0FA3),
        ('RT_TextCharFormatExceptionAtom', 0x0FA4),
        ('RT_TextParagraphFormatExceptionAtom', 0x0FA5),
        ('RT_TextRulerAtom', 0x0FA6),
        ('RT_TextBookmarkAtom', 0x0FA7),
        ('RT_TextBytesAtom', 0x0FA8),
        ('RT_TextSpecialInfoDefaultAtom', 0x0FA9),
        ('RT_TextSpecialInfoAtom', 0x0FAA),
        ('RT_DefaultRulerAtom', 0x0FAB),
        ('RT_StyleTextProp9Atom', 0x0FAC),
        ('RT_TextMasterStyle9Atom', 0x0FAD),
        ('RT_OutlineTextProps9', 0x0FAE),
        ('RT_OutlineTextPropsHeader9Atom', 0x0FAF),
        ('RT_TextDefaults9Atom', 0x0FB0),
        ('RT_StyleTextProp10Atom', 0x0FB1),
        ('RT_TextMasterStyle10Atom', 0x0FB2),
        ('RT_OutlineTextProps10', 0x0FB3),
        ('RT_TextDefaults10Atom', 0x0FB4),
        ('RT_OutlineTextProps11', 0x0FB5),
        ('RT_StyleTextProp11Atom', 0x0FB6),
        ('RT_FontEntityAtom', 0x0FB7),
        ('RT_FontEmbedDataBlob', 0x0FB8),
        ('RT_CString', 0x0FBA),
        ('RT_MetaFile', 0x0FC1),
        ('RT_ExternalOleObjectAtom', 0x0FC3),
        ('RT_Kinsoku', 0x0FC8),
        ('RT_Handout', 0x0FC9),
        ('RT_ExternalOleEmbed', 0x0FCC),
        ('RT_ExternalOleEmbedAtom', 0x0FCD),
        ('RT_ExternalOleLink', 0x0FCE),
        ('RT_BookmarkEntityAtom', 0x0FD0),
        ('RT_ExternalOleLinkAtom', 0x0FD1),
        ('RT_KinsokuAtom', 0x0FD2),
        ('RT_ExternalHyperlinkAtom', 0x0FD3),
        ('RT_ExternalHyperlink', 0x0FD7),
        ('RT_SlideNumberMetaCharAtom', 0x0FD8),
        ('RT_HeadersFooters', 0x0FD9),
        ('RT_HeadersFootersAtom', 0x0FDA),
        ('RT_TextInteractiveInfoAtom', 0x0FDF),
        ('RT_ExternalHyperlink9', 0x0FE4),
        ('RT_RecolorInfoAtom', 0x0FE7),
        ('RT_ExternalOleControl', 0x0FEE),
        ('RT_SlideListWithText', 0x0FF0),
        ('RT_AnimationInfoAtom', 0x0FF1),
        ('RT_InteractiveInfo', 0x0FF2),
        ('RT_InteractiveInfoAtom', 0x0FF3),
        ('RT_UserEditAtom', 0x0FF5),
        ('RT_CurrentUserAtom', 0x0FF6),
        ('RT_DateTimeMetaCharAtom', 0x0FF7),
        ('RT_GenericDateMetaCharAtom', 0x0FF8),
        ('RT_HeaderMetaCharAtom', 0x0FF9),
        ('RT_FooterMetaCharAtom', 0x0FFA),
        ('RT_ExternalOleControlAtom', 0x0FFB),
        ('RT_ExternalMediaAtom', 0x1004),
        ('RT_ExternalVideo', 0x1005),
        ('RT_ExternalAviMovie', 0x1006),
        ('RT_ExternalMciMovie', 0x1007),
        ('RT_ExternalMidiAudio', 0x100D),
        ('RT_ExternalCdAudio', 0x100E),
        ('RT_ExternalWavAudioEmbedded', 0x100F),
        ('RT_ExternalWavAudioLink', 0x1010),
        ('RT_ExternalOleObjectStg', 0x1011),
        ('RT_ExternalCdAudioAtom', 0x1012),
        ('RT_ExternalWavAudioEmbeddedAtom', 0x1013),
        ('RT_AnimationInfo', 0x1014),
        ('RT_RtfDateTimeMetaCharAtom', 0x1015),
        ('RT_ExternalHyperlinkFlagsAtom', 0x1018),
        ('RT_ProgTags', 0x1388),
        ('RT_ProgStringTag', 0x1389),
        ('RT_ProgBinaryTag', 0x138A),
        ('RT_BinaryTagDataBlob', 0x138B),
        ('RT_PrintOptionsAtom', 0x1770),
        ('RT_PersistDirectoryAtom', 0x1772),
        ('RT_PresentationAdvisorFlags9Atom', 0x177A),
        ('RT_HtmlDocInfo9Atom', 0x177B),
        ('RT_HtmlPublishInfoAtom', 0x177C),
        ('RT_HtmlPublishInfo9', 0x177D),
        ('RT_BroadcastDocInfo9', 0x177E),
        ('RT_BroadcastDocInfo9Atom', 0x177F),
        ('RT_EnvelopeFlags9Atom', 0x1784),
        ('RT_EnvelopeData9Atom', 0x1785),
        ('RT_VisualShapeAtom', 0x2AFB),
        ('RT_HashCodeAtom', 0x2B00),
        ('RT_VisualPageAtom', 0x2B01),
        ('RT_BuildList', 0x2B02),
        ('RT_BuildAtom', 0x2B03),
        ('RT_ChartBuild', 0x2B04),
        ('RT_ChartBuildAtom', 0x2B05),
        ('RT_DiagramBuild', 0x2B06),
        ('RT_DiagramBuildAtom', 0x2B07),
        ('RT_ParaBuild', 0x2B08),
        ('RT_ParaBuildAtom', 0x2B09),
        ('RT_LevelInfoAtom', 0x2B0A),
        ('RT_RoundTripAnimationAtom12Atom', 0x2B0B),
        ('RT_RoundTripAnimationHashAtom12Atom', 0x2B0D),
        ('RT_Comment10', 0x2EE0),
        ('RT_Comment10Atom', 0x2EE1),
        ('RT_CommentIndex10', 0x2EE4),
        ('RT_CommentIndex10Atom', 0x2EE5),
        ('RT_LinkedShape10Atom', 0x2EE6),
        ('RT_LinkedSlide10Atom', 0x2EE7),
        ('RT_SlideFlags10Atom', 0x2EEA),
        ('RT_SlideTime10Atom', 0x2EEB),
        ('RT_DiffTree10', 0x2EEC),
        ('RT_Diff10', 0x2EED),
        ('RT_Diff10Atom', 0x2EEE),
        ('RT_SlideListTableSize10Atom', 0x2EEF),
        ('RT_SlideListEntry10Atom', 0x2EF0),
        ('RT_SlideListTable10', 0x2EF1),
        ('RT_CryptSession10Container', 0x2F14),
        ('RT_FontEmbedFlags10Atom', 0x32C8),
        ('RT_FilterPrivacyFlags10Atom', 0x36B0),
        ('RT_DocToolbarStates10Atom', 0x36B1),
        ('RT_PhotoAlbumInfo10Atom', 0x36B2),
        ('RT_SmartTagStore11Container', 0x36B3),
        ('RT_RoundTripSlideSyncInfo12', 0x3714),
        ('RT_RoundTripSlideSyncInfoAtom12', 0x3715),
        ('RT_TimeConditionContainer', 0xF125),
        ('RT_TimeNode', 0xF127),
        ('RT_TimeCondition', 0xF128),
        ('RT_TimeModifier', 0xF129),
        ('RT_TimeBehaviorContainer', 0xF12A),
        ('RT_TimeAnimateBehaviorContainer', 0xF12B),
        ('RT_TimeColorBehaviorContainer', 0xF12C),
        ('RT_TimeEffectBehaviorContainer', 0xF12D),
        ('RT_TimeMotionBehaviorContainer', 0xF12E),
        ('RT_TimeRotationBehaviorContainer', 0xF12F),
        ('RT_TimeScaleBehaviorContainer', 0xF130),
        ('RT_TimeSetBehaviorContainer', 0xF131),
        ('RT_TimeCommandBehaviorContainer', 0xF132),
        ('RT_TimeBehavior', 0xF133),
        ('RT_TimeAnimateBehavior', 0xF134),
        ('RT_TimeColorBehavior', 0xF135),
        ('RT_TimeEffectBehavior', 0xF136),
        ('RT_TimeMotionBehavior', 0xF137),
        ('RT_TimeRotationBehavior', 0xF138),
        ('RT_TimeScaleBehavior', 0xF139),
        ('RT_TimeSetBehavior', 0xF13A),
        ('RT_TimeCommandBehavior', 0xF13B),
        ('RT_TimeClientVisualElement', 0xF13C),
        ('RT_TimePropertyList', 0xF13D),
        ('RT_TimeVariantList', 0xF13E),
        ('RT_TimeAnimationValueList', 0xF13F),
        ('RT_TimeIterateData', 0xF140),
        ('RT_TimeSequenceData', 0xF141),
        ('RT_TimeVariant', 0xF142),
        ('RT_TimeAnimationValue', 0xF143),
        ('RT_TimeExtTimeNodeContainer', 0xF144),
        ('RT_TimeSubEffectContainer', 0xF145),
    ]

### Current User Stream
@Record.define
class PSR_UserEditAtom(pstruct.type):
    type = 0x0ff5
    type = 4085
    _fields_ = [
        (sint4, 'lastSlideIDRef'),
        (uint2, 'version'),
        (ubyte1, 'minorVersion'),
        (ubyte1, 'majorVersion'),
        (lambda s: dyn.pointer(PSR_UserEditAtom), 'offsetLastEdit'),
        (dyn.pointer(RecordGeneral), 'offsetPersistDirectory'),
        (uint4, 'docPersistIdRef'),
        (uint4, 'persistIdSeed'),
        (sint2, 'lastView'),
        (dyn.block(2), 'unused'),
    ]

@Record.define
class RT_CurrentUserAtom(pstruct.type):
    type = 0x0ff6
    type = 4086
    _fields_ = [
        (uint4, 'size'),
        (dyn.block(4), 'headerToken'),
        (dyn.pointer(RecordGeneral), 'offsetToCurrentEdit'),
        (uint2, 'lenUserName'),
        (uint2, 'docfileversion'),
        (ubyte1, 'majorVersion'),
        (ubyte1, 'minorVersion'),
        (dyn.block(2), 'unused'),
        (lambda s: dyn.clone(pstr.string,length=int(s['lenUserName'].li)), 'ansiUserName'),
        (uint4, 'relVersion'),
#        (lambda s: dyn.clone(pstr.wstring,length=int(s['lenUserName'].li)*2), 'unicodeUserName'),
    ]

## PowerPoint Document stream
class PersistDirectoryEntry(pstruct.type):
    class __info(pbinary.struct):
        _fields_ = [(12, 'cPersist'), (20,'persistId')]
    __info = pbinary.littleendian(__info)

    _fields_ = [
        (__info, 'info'),
        (lambda s: dyn.array( dyn.pointer(RecordGeneral), s['info'].li['cPersist'] ), 'offsets')
    ]

    def details(self):
        id = 'info.persistId:%x'% self['info']['persistId']
        addresses = [hex(int(o)) for o in self['offsets']]
        return ' '.join((id, 'offsets:{', ','.join(addresses), '}'))

    def walk(self):
        # heh
        for n in self['offsets']:
            yield n.d.li['data']
        return

#@Record.define
class PersistDirectoryAtom(parray.block):
    type = 6002
    type = 0x1772

    _object_ = PersistDirectoryEntry

    def walk(self):
        for v in self:
            for n in v.walk():
                yield n
            continue
        return

@Record.define
class Document(RecordContainer):
    type = 1000

@Record.define
class EndDocument(pstruct.type):
    type = 1002
    _fields_ = []

@Record.define
class OEPlaceholderAtom(pstruct.type):
    type = 3011

    class __placeholderid(pint.enum, ubyte1):
        _values_ = [
            ('None', 0), ('MasterTitle', 1), ('MasterBody', 2), ('MasterCenteredTitle', 3), ('MasterNotesSlideImage', 4),
            ('MasterNotesBodyImage', 5), ('MasterDate', 6), ('MasterSlideNumber', 7), ('MasterFooter', 8), ('MasterHeader', 9),
            ('MasterSubtitle', 10), ('GenericTextObject', 11), ('Title', 12), ('Body', 13), ('NotesBody', 14), ('CenteredTitle', 15),
            ('Subtitle', 16), ('VerticalTextTitle', 17), ('VerticalTextBody', 18), ('NotesSlideImage', 19), ('Object', 20),
            ('Graph', 21), ('Table', 22), ('ClipArt', 23), ('OrganizationChart', 24), ('MediaClip', 25),
        ]
        
    _fields_ = [
        (uint4, 'placementId'),
        (__placeholderid, 'placeholderId'),
        (ubyte1, 'size'),
        (lambda s: dyn.block(s.blocksize() - 6), 'unused'),
    ]

@Record.define
class ExObjRefAtom(pstruct.type):
    type = 3009
    _fields_ = [
        (uint4, 'exObjId')
    ]

@Record.define
class SSlideLayout(pstruct.type):
    type = 1015
    _fields_ = [
        (sint4, 'geom'),
        (dyn.array(ubyte1, 8), 'placeholderId'),
    ]

@Record.define
class SlideAtom(pstruct.type):
    type = 1007
    _fields_ = [
        (SSlideLayout, 'layout'),
        (sint4, 'masterIdRef'),
        (sint4, 'notesIdRef'),
        (uint2, 'slideFlags'),
        (uint2, 'unused')
    ]

@Record.define
class MainMaster(RecordContainer):
    type = 1016

@Record.define
class Slide(RecordContainer):
    type = 1006

@Record.define
class CString(pstr.string):
    type = 4026
    length = property(fget=lambda s:self.blocksize())

@Record.define
class BinaryTagData(RecordContainer):
    type = 5003

@Record.define
class ProgBinaryTag(RecordContainer):
    type = 5002

@Record.define
class ProgTags(RecordContainer):
    type = 5000

@Record.define
class Notes(RecordContainer):
    type = 1008

@Record.define
class PPDrawing(RecordContainer):
    type = 1036

#@Record.define
#class PST_DrawingContainer(RecordContainer):
#    type = 61442

#@Record.define
#class PST_GroupShapeContainer(RecordContainer):
#    type = 61443

#@Record.define
#class PST_ShapeContainer(RecordContainer):
#    type = 61444

#@Record.define
#class PST_ShapeClientContainer(RecordContainer):
#    type = 61457

@Record.define
class Handout(RecordContainer):
    type = 4041
    type = 0x0fc9

@Record.define
class PSR_ColorSchemeAtom(parray.type):
    type = 0x7f0
    type = 2032
    length = 8
    _object_ = uint4

@Record.define
class PSR_HashCodeAtom(pstruct.type):
    type = 0x2b00
    type = 11008
    _fields_ = [(uint4, 'hash')]

@Record.define
class PSR_SlideTimeAtom10(pstruct.type):
    type = 0x2eeb
    type = 12011
    _fields_ = [(uint4, 'dwHighDateTime'),(uint4, 'dwLowDateTime')]

@Record.define
class msofbtTimeNode(pstruct.type):
    type = 0xf127
    type = 61735
    _fields_ = [
        (pint.uint32_t, 'masterID'),
        (pint.uint32_t, 'restart'),
        (pint.uint32_t, 'type'),
        (pint.uint32_t, 'fill'),
        (pint.uint32_t, 'syncBehavior'),
        (pint.uint8_t, 'fSyncMaster'),
        (pint.uint32_t, 'propertiesSet'),
    ]

@Record.define
class PSR_ParaBuild(RecordContainer):
    type = 0x2b08
    type = 11016

@Record.define
class PSR_BuildList(RecordContainer):
    type = 0x2b02
    type = 11010

@Record.define
class PSR_VisualShapeAtom(pstruct.type):
    type = 11003
    type = 0x2afb

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

@Record.define
class DocumentAtom(pstruct.type):
    #alias = RT_DocumentAtom
    type = 1001
    type = 0x3e9
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


@Record.define
class DocumentTextInfoContainer(pstruct.type):
    # FIXME
    #parent = DocumentContainer
    #alias = RT_Environment
    type = 1010
    type = 0x03f2
    _fields_ = [
        #(KinsokuContainer, 'kinsoku'),
        #(FontCollectionContainer, 'fontCollection'),
        #(TextCFExceptionAtom, 'textCFDefaultsAtom'),
        #(TextPFExceptionAtom, 'textPFDefaultsAtom'),
        #(DefaultRulerAtom, 'defaultRulerAtom'),
        #(TextSIExceptionAtom, 'textSIDefaultsAtom'),
        #(TextMasterStyleAtom, 'textMasterStyleAtom'),
    ]

@Record.define
class DrawingGroupContainer(pstruct.type):
    # FIXME
    type = 1035
    type = 0x040b
    _fields_ = [
        #(OfficeArtDggContainer, 'OfficeArtDgg'),
    ]

@Record.define
class MasterListWithTextContainer(pstruct.type):
    # FIXME
    type = 4080
    type = 0x0ff0
    _fields_ = [
    #    (lambda s: parray.block(MasterPersistAtom, s.parent['rh']['recLen']), 'rgMasterPersistAtom'),
    ]

@Record.define
class DocInfoListContainer(pstruct.type):
    type = 2000
    type = 0x07d0
    _fields_ = [
    ]


Record.update(art.Record)
Record.update(graph.Record)

if False:
    import ptypes,powerpoint
    usersource = ptypes.provider.file('user.stream')
    datasource = ptypes.provider.file('data.stream')

    user = powerpoint.File(source=usersource).l
    datastream = powerpoint.File(source=datasource).l

    currentuseratom = user[0]['data']
    currentedit = currentuseratom['offsetToCurrentEdit'].d      # points to offset inside a data stream
    currentedit.source = datastream.source
    print currentedit.l
    usereditatom = currentedit['data']
    persistdirectory = usereditatom['offsetPersistDirectory'].d

    # go through persist directory
    for i,entry in enumerate(persistdirectory.li['data']):
        print '%s %x'%('-'*70, i)
        for obj in entry.walk():
            print obj
        continue

if __name__ == '__main__':
    import powerpoint as pp
    import ptypes
    from ptypes import *

    if False:
        s = '\x00\x00\x00\x00\x0c\x00\x00\x00' + 'A'*30
        z = pp.RecordGeneral()
        z.source = provider.string(s)
        print z.l

    if False:
        s = '\x00\x00'+'\xc3\x0b'+'\x06\x00\x00\x00'+'\r\n\x0e\r\xcc\x00'
        z = pp.RecordGeneral()
        z.source = provider.string(s)
        print z.l

    if False:
        header = '\x00\x00'+'\xc3\x0b' + '\x06\x00\x00\x00'
        data = '\x00'*6

        s = (header + data)*4
        z = pp.RecordContainer()
        z.source = provider.string(s+'\xff'*8)
        z.size = lambda:(len(header)+len(data))*4
        print z.l

    if True:
        header = '\x00\x00'+'\xc3\x0b' + '\x06\x00\x00\x00'
        data = '\x00'*6
        element = header+data

        container = '\x00\x00'+'\xe8\x03' + '\x38\x00\x00\x00'
        s = element*4
        container += s

        z = pp.RecordGeneral()
        z.source = ptypes.provider.string(container)
        z.size = lambda:len(container)
        print z.l
