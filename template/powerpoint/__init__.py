from ptypes import *

def getstringpath(object):
    self = object
    name = []
    for obj in list(self.traverse(lambda s: s.getparent())):
        n = obj
        if type(obj) is not RecordGeneral:
            continue

        try:
            n = n.__name__
        except AttributeError:
            name.append(None)
            continue

        try:
            int(n)
            n = '[%s]'% str(n)
        except ValueError:
            n = '[%s]'% repr(n)
        
        t = int(obj['header']['recType'])
        #name.append(n)
        name.append( '<%x>%s'% (t,n) )
            
    return ''.join(list(reversed(name))[1:])

class bool1(pint.uint8_t): pass
class ubyte1(pint.uint8_t): pass
class uint2(pint.uint16_t): pass
class uint4(pint.uint32_t): pass
class sint2(pint.int16_t): pass
class sint4(pint.int32_t): pass

### all general records (scroll down to the next ###)
class RecordHeader(pstruct.type):
        
    _fields_ = [
        (pint.uint16_t, 'recVer/recInstance'),
        (pint.uint16_t, 'recType'),
        (pint.uint32_t, 'recLength')
    ]

    def __repr__(self):
        if self.initialized:
            v = int(self['recVer/recInstance'])
            t = int(self['recType'])
            l = int(self['recLength'])
            return '%s ver=%04x type=0x%04x length=0x%08x'% (self.name(), v,t,l)
        return super(RecordHeader, self).__repr__()

class RecordUnknown(dyn.block(0)): pass

LookupRecordType = {}
class RecordGeneral(pstruct.type):
    def autorecord(self):
        t = int(self['header'].l['recType'])
        l = int(self['header']['recLength'])
        try:
            cls = LookupRecordType[t]

        except KeyError:
            name = repr(RecordUnknown)
            return dyn.clone(RecordUnknown, maxsize=l, length=l, recordtype=t, name=lambda x:name)
        return dyn.clone(cls, maxsize=l)

    def autofiller(self):
        totalsize = self.size() - self['header'].size()
        decodedsize = self['data'].size()
        if totalsize > decodedsize:
            return dyn.block( totalsize - decodedsize )
        return dyn.block(0)

    _fields_ = [
        (RecordHeader, 'header'),
        (autorecord, 'data'),
        (autofiller, 'extra')
    ]

    def size(self):
        return self['header'].size() + int(self['header']['recLength'])

    def __repr__(self):
        if self.initialized:
            header = self['header']
            return '[%x] %s header={ver=%d,type=%x,length=%d} size=%d data=%s'%(self.getoffset(), self.name(), int(header['recVer/recInstance']), int(header['recType']), int(header['recLength']), self['data'].size(), self['data'].name())
        return super(RecordGeneral, self).__repr__()

class searchingcontainer(object):
    def search(self, type, recurse=False):
        '''Search through a list of records for a particular type'''
        if not recurse:
            for x in self:
                if int(x['header']['recType']) == type:
                    yield x
                continue
            return

        # ourselves first
        for d in self.search(type, False):
            yield d

        # now our chidren
        for x in self:
            try:
                x['data'].search
            except AttributeError:
                continue

            for d in x['data'].search(type, True):
                yield d
            continue
        return

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        res = [x for x in self if int(x['header']['recType']) == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

    def walk(self):
        for x in self:
            yield x['data']
        return

class Record(object): pass
class RecordContainer(parray.infinite, Record, searchingcontainer):
    _object_ = RecordGeneral
    currentsize = maxsize = 0

    def isTerminator(self, value):
        s = value.size()
        self.currentsize += s
        if (self.currentsize < self.maxsize):
            return False
        return True

    def load(self):
        self.currentsize = 0
        return super(RecordContainer, self).load()

    def deserialize(self, source):
        self.currentsize = 0
        return super(RecordContainer, self).deserialize(source)

    def __repr__(self):
        if self.initialized:
            records = []
            for v in self.walk():
                n = '%s[%x]'%(v.__class__.__name__,v.recordtype)
                records.append(n)
            header = self.parent['header']
            return '[%x] %s header={ver=%d,type=%x,length=%d} records=%d [%s]'%(self.getoffset(),self.name(), int(header['recVer/recInstance']), int(header['recType']), int(header['recLength']), len(self), ','.join(records))
        return super(RecordContainer, self).__repr__()

# yea, a file really is just a gigantic list of records...
class File(parray.infinite, searchingcontainer):
    _object_ = RecordGeneral

    def __repr__(self):
        if self.initialized:
            records = []
            for v in self.walk():
                n = '%s[%x]'%(v.__class__.__name__,v.recordtype)
                records.append(n)
            return '%s records=%d [%s]'%(self.name(), len(self), ','.join(records))
        return super(File, self).__repr__()

### list of all records
## PowerPoint stream
class Document(RecordContainer):
    recordtype = 1000

class OEPlaceholderAtom(pstruct.type, Record):
    recordtype = 3011
    _fields_ = [
        (uint4, 'placementId'),
        (ubyte1, 'placeholderId'),
        (ubyte1, 'size')
    ]

class ExObjRefAtom(pstruct.type, Record):
    recordtype = 3009
    _fields_ = [
        (uint4, 'exObjId')
    ]

class List(RecordContainer):
    recordtype = 1016

class Slide(RecordContainer):
    recordtype = 1006

class SSlideLayout(pstruct.type, Record):
    recordtype = 1015
    _fields_ = [
        (sint4, 'geom'),
        (dyn.array(ubyte1, 8), 'placeholderId'),
    ]

class SlideAtom(pstruct.type, Record):
    recordtype = 1007
    _fields_ = [
        (SSlideLayout, 'layout'),
        (sint4, 'masterId'),
        (sint4, 'notesId'),
        (uint2, 'Flags')
    ]

class PersistDirectoryEntry(pstruct.type):
    class __info(pbinary.littleendian(pbinary.struct)):
        _fields_ = [(12, 'cPersist'), (20,'persistId')]

    _fields_ = [
        (__info, 'info'),
        (lambda s: dyn.array( dyn.pointer(RecordGeneral), s['info'].l['cPersist'] ), 'offsets')
    ]

    def __repr__(self):
        id = 'id:%x'% self['info']['persistId']
        addresses = [hex(int(o)) for o in self['offsets']]
        return ' '.join( (self.name(), id, 'offsets:{', ','.join(addresses), '}') )

    def walk(self):
        # heh
        for n in self['offsets']:
            yield n.d.l['data']
        return

class PersistDirectoryAtom(parray.infinite, Record):
    recordtype = 6002
    recordtype = 0x1772

    _object_ = PersistDirectoryEntry

    def isTerminator(self, value):
        self.currentsize += value.size()

        if self.currentsize < self.maxsize - self.parent['header'].size():
            return False
        return True

    def load(self):
        self.currentsize = 0
        return super(PersistDirectoryAtom, self).load()

    def deserialize(self, source):
        self.currentsize = 0
        return super(PersistDirectoryAtom, self).deserialize(source)

class CString(ptype.type, Record):
    recordtype = 4026

class BinaryTagData(RecordContainer):
    recordtype = 5003

class ProgBinaryTag(RecordContainer):
    recordtype = 5002

class ProgTags(RecordContainer):
    recordtype = 5000

class PST_Notes(RecordContainer):
    recordtype = 1008

class PST_PPDrawing(RecordContainer):
    recordtype = 1036
class PST_DrawingContainer(RecordContainer):
    recordtype = 61442
class PST_GroupShapeContainer(RecordContainer):
    recordtype = 61443
class PST_ShapeContainer(RecordContainer):
    recordtype = 61444
class PST_ShapeClientContainer(RecordContainer):
    recordtype = 61457

class Handout(RecordContainer):
    recordtype = 4041
    recordtype = 0x0fc9

### office art
class msofbtExtTimeNodeContainer(RecordContainer):
    recordtype = 0xf144
    recordtype = 61764
class msofbtTimeConditionContainer(RecordContainer):
    recordtype = 0xf125
    recordtype = 61733
class msofbtTimeAnimateBehaviorContainer(RecordContainer):
    recordtype = 0xf12b
    recordtype = 61739
class msofbtTimeColorBehaviorContainer(RecordContainer):
    recordtype = 0xf12c
    recordtype = 61740

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

class msofbtTimeVariantList(parray.infinite, Record):
    recordtype = 0xf13f
    recordtype = 61759
    _object_ = msofbtTimeAnimationValue

    currentsize = maxsize = 0

    def isTerminator(self, value):
        s = value.size()
        self.currentsize += s
        if (self.currentsize < self.maxsize):
            return False
        return True

    def load(self):
        self.currentsize = 0
        return super(RecordContainer, self).load()

    def deserialize(self, source):
        self.currentsize = 0
        return super(RecordContainer, self).deserialize(source)

class msofbtTimeCondition(pstruct.type, Record):
    recordtype = 0xf128
    recordtype = 61736

    class __triggerType(pint.enum, pint.uint32_t):
        _fields_ = [
            ('totNone', 0),
            ('totVisualElement', 1),
            ('totTimeNode', 2),
            ('totRuntimeNodeRef', 3),
            ('TriggerObjectType_MaxEnumIDs', 4),
        ]

    class __event(pint.enum, pint.uint32_t):
        _fields_ = [
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

### Current User Stream
class PSR_UserEditAtom(pstruct.type, Record):
    recordtype = 0x0ff5
    recordtype = 4085
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

class RT_CurrentUserAtom(pstruct.type, Record):
    recordtype = 0x0ff6
    recordtype = 4086
    _fields_ = [
        (uint4, 'size'),
        (dyn.block(4), 'headerToken'),
        (dyn.pointer(RecordGeneral), 'offsetToCurrentEdit'),
        (uint2, 'lenUserName'),
        (uint2, 'docfileversion'),
        (ubyte1, 'majorVersion'),
        (ubyte1, 'minorVersion'),
        (dyn.block(2), 'unused'),
        (lambda s: dyn.clone(pstr.string,length=int(s['lenUserName'].l)), 'ansiUserName'),
        (uint4, 'relVersion'),
#        (lambda s: dyn.clone(pstr.wstring,length=int(s['lenUserName'].l)*2), 'unicodeUserName'),
    ]

class PSR_ColorSchemeAtom(parray.type, Record):
    recordtype = 0x7f0
    recordtype = 2032
    length = 8
    _object_ = uint4

class PSR_HashCodeAtom(pstruct.type, Record):
    recordtype = 0x2b00
    recordtype = 11008
    _fields_ = [(uint4, 'hash')]

class PSR_SlideTimeAtom10(pstruct.type, Record):
    recordtype = 0x2eeb
    recordtype = 12011
    _fields_ = [(uint4, 'dwHighDateTime'),(uint4, 'dwLowDateTime')]

class msofbtTimeNode(pstruct.type, Record):
    recordtype = 0xf127
    recordtype = 61735
    _fields_ = [
        (pint.uint32_t, 'masterID'),
        (pint.uint32_t, 'restart'),
        (pint.uint32_t, 'type'),
        (pint.uint32_t, 'fill'),
        (pint.uint32_t, 'syncBehavior'),
        (pint.uint8_t, 'fSyncMaster'),
        (pint.uint32_t, 'propertiesSet'),
    ]

class PSR_ParaBuild(RecordContainer):
    recordtype = 0x2b08
    recordtype = 11016

class PSR_BuildList(RecordContainer):
    recordtype = 0x2b02
    recordtype = 11010

class msofbtTimeSetBehaviorContainer(RecordContainer):
    recordtype = 0xf131
    recordtype = 61745

class msofbtTimePropertyList(RecordContainer):
    recordtype = 0xf13d
    recordtype = 61757

class msofbtTimeSetBehaviorContainer(RecordContainer):
    recordtype = 0xf131
    recordtype = 61745

class msofbtTimeEffectBehaviorContainer(RecordContainer):
    recordtype = 0xf12d
    recordtype = 61741

class msofbtTimeBehaviorContainer(RecordContainer):
    recordtype = 0xf12a
    recordtype = 61738

class msofbtClientVisualElement(RecordContainer):
    recordtype = 0xf13c
    recordtype = 61756

class msofbtTimeEffectBehavior(pstruct.type, Record):
    recordtype = 0xf136
    recordtype = 61750
    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'taetTransition'),
    ]

class msofbtTimeVariant(pstruct.type, Record):
    recordtype = 0xf142
    recordtype = 61762

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

class msofbtTimeBehavior(pstruct.type, Record):
    recordtype = 0xf133
    recordtype = 61747

    _fields_ = [
        (pint.uint32_t, 'propertiesUsed'),
        (pint.uint32_t, 'tbaddAdditive'),
        (pint.uint32_t, 'tbaccAccmulate'),
        (pint.uint32_t, 'tbbtTransformType'),
    ]

class PSR_VisualShapeAtom(pstruct.type, Record):
    recordtype = 11003
    recordtype = 0x2afb

    _fields_ = [
        (uint4, 'type'),
        (uint4, 'refType'),
        (uint4, 'id'),
        (sint4, 'data0'),
        (sint4, 'data1'),
    ]

### collect all classes
import inspect
for name,cls in globals().items():
    try:
        if inspect.isclass(cls) and issubclass(cls, Record) and cls is not Record:
            LookupRecordType[cls.recordtype] = cls
    except AttributeError:
        print '%s,%s has no record type'% (name,cls)
    continue

if __name__ == '__main__':
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
    for i,entry in enumerate(persistdirectory.l['data']):
        print '%s %x'%('-'*70, i)
        for obj in entry.walk():
            print obj
        continue
