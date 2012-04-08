from ptypes import *
import __init__
class Record(__init__.Record): cache = {}
class RecordGeneral(__init__.RecordGeneral): Record=Record
class RecordContainer(__init__.RecordContainer): _object_ = RecordGeneral
class File(__init__.File): _object_ = RecordGeneral

@Record.define
class SpContainer(RecordContainer):
    type = 0xf004

@Record.define
class FSP(pstruct.type):
    type = 0xf00a
    class __flags(pbinary.struct):
        _fields_ = [(1, 'fGroup'),(1,'fChild'),(1,'fPatriarch'),(1,'fDeleted'),(1,'fOleShape'),(1,'fHaveMaster'),(1,'fFlipH'),(1,'fFlipV'),(1,'fConnector'),(1,'fHaveAnchor'),(1,'fBackground'),(1,'fHaveSpt'),(20,'unused1')]
        
    _fields_ = [
        (pint.uint32_t, 'spid'),
        (__flags, 'f')
    ]

@Record.define
class FOPT(pstruct.type):
    type = 0xf00b
    _fields_ = [
        (lambda s: dyn.array(FOPTE, s.blocksize()/6), 'fopt')
    ]

class FOPTE(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'opid'),
        (pint.uint32_t, 'op')
    ]

@Record.define
class msofbtExtTimeNodeContainer(RecordContainer):
    type = 0xf144
    type = 61764

@Record.define
class msofbtTimeConditionContainer(RecordContainer):
    type = 0xf125
    type = 61733

@Record.define
class msofbtTimeAnimateBehaviorContainer(RecordContainer):
    type = 0xf12b
    type = 61739

@Record.define
class msofbtTimeColorBehaviorContainer(RecordContainer):
    type = 0xf12c
    type = 61740

class msofbtTimeVariant(pstruct.type):
    def __Value(self):
        t = int(self['Type'].l)
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

@Record.define
class msofbtTimeVariantList(parray.block):
    type = 0xf13f
    type = 61759
    _object_ = msofbtTimeAnimationValue

@Record.define
class msofbtTimeCondition(pstruct.type):
    type = 0xf128
    type = 61736

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

@Record.define
class msofbtTimeSetBehaviorContainer(RecordContainer):
    type = 0xf131
    type = 61745

@Record.define
class msofbtTimePropertyList(RecordContainer):
    type = 0xf13d
    type = 61757

@Record.define
class msofbtTimeSetBehaviorContainer(RecordContainer):
    type = 0xf131
    type = 61745

@Record.define
class msofbtTimeEffectBehaviorContainer(RecordContainer):
    type = 0xf12d
    type = 61741

@Record.define
class msofbtTimeBehaviorContainer(RecordContainer):
    type = 0xf12a
    type = 61738

@Record.define
class msofbtClientVisualElement(RecordContainer):
    type = 0xf13c
    type = 61756

@Record.define
class msofbtTimeEffectBehavior(pstruct.type):
    type = 0xf136
    type = 61750
    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'taetTransition'),
    ]

@Record.define
class msofbtTimeVariant(pstruct.type):
    type = 0xf142
    type = 61762

    def __Value(self):
        n = int(self['Type'].l)
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

@Record.define
class msofbtTimeBehavior(pstruct.type):
    type = 0xf133
    type = 61747

    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'tbaddAdditive'),
        (pint.uint32_t, 'tbaccAccmulate'),
        (pint.uint32_t, 'tbbtTransformType'),
    ]

@Record.define
class msofbtDgContainer(RecordContainer):
    type = 0xf002
    type = 61442

@Record.define
class msofbtSpgrContainer(RecordContainer):
    type = 0xf003
    type = 61443

@Record.define
class msofbtClientAnchor(pstruct.type):
    type = 0xf010
    type = 61456
    _fields_ = [
        (pint.uint16_t, 'Flag'),

        (pint.uint16_t, 'Col1'),
        (pint.uint16_t, 'DX1'),
        (pint.uint16_t, 'Row1'),
        (pint.uint16_t, 'DY1'),

        (pint.uint16_t, 'Col2'),
        (pint.uint16_t, 'DX2'),
        (pint.uint16_t, 'Row2'),
        (pint.uint16_t, 'DY2'),
    ]
    

@Record.define
class OfficeArtBlipDIB(pstruct.type):
    type = 0xf01f
    type = 61471
    _fields_ = [
        (dyn.block(16), 'rgbUid1'),
#        (dyn.block(16), 'rgbUid2'),     # XXX: this is conditional?
        (pint.uint8_t, 'tag'),
        (dyn.block(0), 'BLIPFileData'), # FIXME: this isn't right..
    ]

if False:
    import ptypes    
    ptypes.setsource( ptypes.provider.file('poc.xls') )

    x = SpContainer()
#    x.setoffset(66100)
    x.setoffset(66360)
    print x.l

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
        class header(pbinary.littleendian(pbinary.struct)):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        class wtf(pstruct.type):
            _fields_ = [
                (header, 'h'),
                (pint.littleendian(pint.uint16_t), 't'),
            ]

        z = RecordGeneral()
        z.source = provider.string('\x0f\x00\x02\xf0')
        print z.l
