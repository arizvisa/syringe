from ptypes import *
from . import *

# ripped from [MS-OART]
recordType = [
    ('FT_OfficeArgDgg', 0xf000),
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
    ('FT_OfficeArtBlipJPEG', 0xf02a),
    ('FT_OfficeArtFRIT', 0xf118),
    ('FT_OfficeArtFDGSL', 0xf119),
    ('FT_OfficeArtColorMRU', 0xf11a),
    ('FT_OfficeArtFPSPL', 0xf11d),
    ('FT_OfficeArtSplitMenuColor', 0xf11e),
    ('FT_OfficeArtSecondaryFOPT', 0xf121),
    ('FT_OfficeArtTertiaryFOPT', 0xf122),
]

# Ripped from OfficeDrawing97-2007BinaryFormatSpecification.pdf
recordType.extend([
    ('FT_msofbtTimeNodeContainer', 0xf123),
    ('FT_msofbtTimeConditionList', 0xf124),
    ('FT_msofbtTimeConditionContainer', 0xf125),
    ('FT_msofbtTimeModifierList', 0xf126),
    ('FT_msofbtTimeNode', 0xf127),
    ('FT_msofbtTimeCondition', 0xf128),
    ('FT_msofbtTimeModifier', 0xf129),
    ('FT_msofbtTimeBehaviorContainer', 0xf12a),
    ('FT_msofbtTimeAnimateBehaviorContainer', 0xf12b),
    ('FT_msofbtTimeColorBehaviorContainer', 0xf12c),
    ('FT_msofbtTimeEffectBehaviorContainer', 0xf12d),
    ('FT_msofbtTimeMotionBehaviorContainer', 0xf12e),
    ('FT_msofbtTimeRotationBehaviorContainer', 0xf12f),
    ('FT_msofbtTimeScaleBehaviorContainer', 0xf130),
    ('FT_msofbtTimeSetBehaviorContainer', 0xf131),
    ('FT_msofbtTimeCommandBehaviorContainer', 0xf132),
    ('FT_msofbtTimeBehavior', 0xf133),
    ('FT_msofbtTimeAnimateBehavior', 0xf134),
    ('FT_msofbtTimeColorBehavior', 0xf135),
    ('FT_msofbtTimeEffectBehavior', 0xf136),
    ('FT_msofbtTimeMotionBehavior', 0xf137),
    ('FT_msofbtTimeRotationBehavior', 0xf138),
    ('FT_msofbtTimeScaleBehavior', 0xf139),
    ('FT_msofbtTimeSetBehavior', 0xf13a),
    ('FT_msofbtTimeCommandBehavior', 0xf13b),
    ('FT_msofbtClientVisualElement', 0xf13c),
    ('FT_msofbtTimePropertyList', 0xf13d),
    ('FT_msofbtTimeVariantList', 0xf13e),
    ('FT_msofbtTimeAnimationValueList', 0xf13f),
    ('FT_msofbtTimeIterateData', 0xf140),
    ('FT_msofbtTimeSequenceData', 0xf141),
    ('FT_msofbtTimeVariant', 0xf142),
    ('FT_msofbtTimeAnimationValue', 0xf143),
    ('FT_msofbtExtTimeNodeContainer', 0xf144),
    ('FT_msofbtSubNodeContainer', 0xf145),
])

# create a ptype.definition for each record type
locals().update(map(RecordType.define,recordType))

# record types from [MS-OART]
@FT_OfficeArtSp.define
class OfficeArtSpContainer(RecordContainer):
    type = 15,0x000

@FT_OfficeArtSolver.define
class OfficeArtSolverContainer(RecordContainer):
    type = 15,None      # OfficeArtSolverContainerFileBlock records

class MSOSPID(uint4): pass

@FT_OfficeArtFSP.define
class OfficeArtFSP(pstruct.type):
    type = 2,None       # MSOPT enumeration value
    class __flags(pbinary.struct):
        _fields_ = [
            (20,'unused1'),
            (1,'fHaveSpt'),(1,'fBackground'),(1,'fHaveAnchor'),(1,'fConnector'),
            (1,'fFlipV'),(1,'fFlipH'),(1,'fHaveMaster'),(1,'fOleShape'),
            (1,'fDeleted'),(1,'fPatriarch'),(1,'fChild'),(1,'fGroup'),
        ]
        
    _fields_ = [
        (MSOSPID, 'spid'),
        (pbinary.littleendian(__flags), 'f')
    ]

class OfficeArtFOPTE(pstruct.type):
    class OPID(pbinary.struct):
        _fields_ = [
            (1,'fComplex'),
            (1,'fBid'),
            (14, 'opid'),
        ]

    _fields_ = [
        (pbinary.littleendian(OPID), 'opid'),
        (sint4, 'op')
    ]

@FT_OfficeArtFOPT.define
class OfficeArtFOPT(pstruct.type):
    type = 3,None           # Number of properties in the table
    def __fopt(self):
        p = self.getparent(type=__init__.RecordGeneral)
        count = p['header'].getinstance()
        return dyn.array(FOPTE, count)

    def __complex(self):
        # FIXME this should be an array that corresponds to fopt
        bs = self.blocksize()
        s = self['fopt'].li.size()
        return dyn.block(bs-s)

    _fields_ = [
        (__fopt, 'fopt'),
        (__complex, 'complex'),
    ]

@FT_OfficeArtDg.define
class OfficeArtDgContainer(RecordContainer):
    type = 15,0x000

@FT_OfficeArtSpgr.define
class OfficeArtSpgrContainer(RecordContainer):
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

## ripped from OfficeDrawing97-2007BinaryFormatSpecification.pdf
@FT_msofbtExtTimeNodeContainer.define  # FIXME
class msofbtExtTimeNodeContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeConditionContainer.define  # FIXME
class msofbtTimeConditionContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeAnimateBehaviorContainer.define  # FIXME
class msofbtTimeAnimateBehaviorContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeColorBehaviorContainer.define  # FIXME
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

@FT_msofbtTimeVariantList.define  # FIXME
class msofbtTimeVariantList(parray.block):
    type = 0,None
    _object_ = msofbtTimeAnimationValue

@FT_msofbtTimeCondition.define  # FIXME
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

@FT_msofbtTimeSetBehaviorContainer.define  # FIXME
class msofbtTimeSetBehaviorContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimePropertyList.define  # FIXME
class msofbtTimePropertyList(RecordContainer):
    type = 15,None

@FT_msofbtTimeSetBehaviorContainer.define  # FIXME
class msofbtTimeSetBehaviorContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeEffectBehaviorContainer.define  # FIXME
class msofbtTimeEffectBehaviorContainer(RecordContainer):
    type = 15,None

@FT_msofbtTimeBehaviorContainer.define  # FIXME
class msofbtTimeBehaviorContainer(RecordContainer):
    type = 15,None

@FT_msofbtClientVisualElement.define  # FIXME
class msofbtClientVisualElement(RecordContainer):
    type = 15,None   # list of msofbtTimeVariantRecords

@FT_msofbtTimeEffectBehavior.define  # FIXME
class msofbtTimeEffectBehavior(pstruct.type):
    type = 0,None
    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'taetTransition'),
    ]

@FT_msofbtTimeVariant.define  # FIXME
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

        print 'unknown type %x'% n
        print hex(self.getoffset()),getstringpath(self)
        return pint.uint32_t

    _fields_ = [
        (pint.uint8_t, 'Type'),
        (__Value, 'Value'),
    ]

@FT_msofbtTimeBehavior.define  # FIXME
class msofbtTimeBehavior(pstruct.type):
    type = 0,None

    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'tbaddAdditive'),
        (pint.uint32_t, 'tbaccAccmulate'),
        (pint.uint32_t, 'tbbtTransformType'),
    ]

if __name__ == '__main__':
    from ptypes import *
    import art

    if False:
        s = '\x00\x00\x00\x00\x0c\x00\x00\x00' + 'A'*30
        z = art.RecordGeneral()
        z.source = provider.string(s)

    if False:
        s = '\x00\x00'+'\x28\xf1'+'\x10\x00\x00\x00'+'\x00'*16
        z = art.RecordGeneral()
        z.source = provider.string(s)

    if False:
        header = '\x00\x00'+'\x28\xf1' + '\x10\x00\x00\x00'
        data = '\x00'*16

        s = header + data + header + data + header + data + header + data
        z = art.RecordContainer()
        z.source = provider.string(s)
        z.size = lambda:len(s)
    
    if True:
        s = '7ACqAA8AAvAWAQAAEAAI8AgAAAADAAAAEgQAAA8AA/D+AAAADwAE8CgAAAABAAnwEAAAAAAAAAAAAAAAAAAAAAAAAAACAArwCAAAAAAEAAAFAAAADwAE8FIAAACSDArwCAAAAAMEAAAACgAAQwAL8BgAAAB/AAQBBAG/AAgACAD/AQAACAC/AwAAAgAAABDwEgAAAAEAAAAAAAEAAAABAJoBAgAAAAAAEfAAAAAA'
        s = s.decode('base64')[4:] + '\x00'*800
        print repr(s)

    if True:
        z = art.RecordGeneral()
        z.source = provider.string(s)
        print z.l

    if False:
        import ptypes    
        ptypes.setsource( ptypes.provider.file('poc.xls') )

        x = SpContainer()
    #    x.setoffset(66100)
        x.setoffset(66360)
        print x.l

    if False:
        class header(pbinary.struct):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]
        header = pbinary.littleendian(header)

        class wtf(pstruct.type):
            _fields_ = [
                (header, 'h'),
                (pint.littleendian(pint.uint16_t), 't'),
            ]

        z = RecordGeneral()
        z.source = provider.string('\x0f\x00\x02\xf0')
        print z.l
