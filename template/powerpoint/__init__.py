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

### list of all records
## Current User Stream
class PSR_UserEditAtom(pstruct.type):
    _fields_ = [
        (sint4, 'lastSlideID'),
        (uint4, 'version'),
        (uint4, 'offsetLastEdit'),
        (uint4, 'offsetPersistDirectory'),
        (uint4, 'documentRef'),
        (uint4, 'maxPersistWritten'),
        (sint2, 'lastViewType'),
    ]

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

### collect all classes
import inspect
for cls in globals().values():
    try:
        if inspect.isclass(cls) and issubclass(cls, Record) and cls is not Record:
            LookupRecordType[cls.recordtype] = cls
    except AttributeError:
        print '%s has no record type'% cls
    continue

