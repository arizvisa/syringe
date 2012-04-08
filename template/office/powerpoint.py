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
        (lambda s: dyn.clone(pstr.string,length=int(s['lenUserName'].l)), 'ansiUserName'),
        (uint4, 'relVersion'),
#        (lambda s: dyn.clone(pstr.wstring,length=int(s['lenUserName'].l)*2), 'unicodeUserName'),
    ]

## PowerPoint Document stream
class PersistDirectoryEntry(pstruct.type):
    class __info(pbinary.littleendian(pbinary.struct)):
        _fields_ = [(12, 'cPersist'), (20,'persistId')]

    _fields_ = [
        (__info, 'info'),
        (lambda s: dyn.array( dyn.pointer(RecordGeneral), s['info'].l['cPersist'] ), 'offsets')
    ]

    def __repr__(self):
        id = 'info.persistId:%x'% self['info']['persistId']
        addresses = [hex(int(o)) for o in self['offsets']]
        return ' '.join( (self.name(), id, 'offsets:{', ','.join(addresses), '}') )

    def walk(self):
        # heh
        for n in self['offsets']:
            yield n.d.l['data']
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
    _fields_ = [
        (uint4, 'placementId'),
        (ubyte1, 'placeholderId'),
        (ubyte1, 'size')
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

@Record.define
class PST_ShapeClientContainer(RecordContainer):
    type = 61457

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
    for i,entry in enumerate(persistdirectory.l['data']):
        print '%s %x'%('-'*70, i)
        for obj in entry.walk():
            print obj
        continue

if __name__ == '__main__':
    import powerpoint as pp
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
        z.source = provider.string(container)
        z.size = lambda:len(container)
        print z.l
