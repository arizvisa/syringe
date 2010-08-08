from ptypes import *

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

LookupRecordType = {}
class RecordGeneral(pstruct.type):
    def autorecord(self):
        t = int(self['header'].l['recType'])
        l = int(self['header']['recLength'])
        try:
            cls = LookupRecordType[t]

        except KeyError:
            return dyn.clone(dyn.block(l), maxsize=l)
        return dyn.clone(cls, maxsize=l)

    def autofiller(self):
        totalsize = self['data'].size()
        maxsize = self['data'].maxsize

        if totalsize > maxsize:
            t = int(self['header'].l['recType'])
            
            name = []
            for n in list(self.path()):
                try:
                    name.append(str(n.__name__))
                except AttributeError:
                    name.append(None)
                continue
            name = '[%s]'% ','.join(list(reversed(name))[1:])
            
            print "record at %x (type %x) %s's contents are larger than expected (%x>%x)"%(self.getoffset(), t, name, totalsize, maxsize)
            totalsize = maxsize

        return dyn.block(maxsize - totalsize)

    _fields_ = [
        (RecordHeader, 'header'),
        (autorecord, 'data'),
        (autofiller, 'extra')
    ]

class Record(object): pass
class RecordContainer(parray.terminated, Record):
    _object_ = RecordGeneral
    currentsize = maxsize = 0

    def isTerminator(self, value):
        s = value.size()
        self.currentsize += s
        if (self.currentsize < self.maxsize):
            return False
        return True

    def search(self, type):
        '''Search through a list of records for a particular type'''
        return (x for x in self if int(x['header']['recType']) == type)

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        res = [x for x in self if int(x['header']['recType']) == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

# yea, a file really is just a gigantic list of records...
class File(parray.infinite):
    _object_ = RecordGeneral

    def search(self, type):
        '''Search through a list of records for a particular type'''
        return (x for x in self if int(x['header']['recType']) == type)

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        res = [x for x in self if int(x['header']['recType']) == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

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
        (lambda s: dyn.array(uint4, s['info'].l['cPersist'] ), 'offsets')
    ]

class PersistDirectoryAtom(parray.infinite, Record):
    recordtype = 6002
    recordtype = 0x1772

    _object_ = PersistDirectoryEntry

    currentsize = 0
    def isTerminator(self, value):
        s = value.size()
        self.currentsize += s

        l = self.parent['header']['recLength']
        if self.currentsize < int(l):
            return False
        return True

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

### office art
class msofbtExtTimeNodeContainer(RecordContainer):
    recordtype = 0xf144
class msofbtTimeConditionContainer(RecordContainer):
    recordtype = 0xf125
class msofbtTimeColorBehaviorContainer(RecordContainer):
    recordtype = 0xf12c

class msofbtTimeCondition(pstruct.type, Record):
    recordtype = 0xf128

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

### collect all classes
import inspect
for cls in globals().values():
    try:
        if inspect.isclass(cls) and issubclass(cls, Record) and cls is not Record:
            LookupRecordType[cls.recordtype] = cls
    except AttributeError:
        print '%s has no record type'% cls
    continue

