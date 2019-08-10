import logging, math
import ptypes
from ptypes import *

### Primitive types
class RGB(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'R'),
        (pint.uint8_t, 'G'),
        (pint.uint8_t, 'B'),
    ]

    def summary(self):
        r, g, b = (self[k] for k in 'RGB')
        return "R={:d} G={:d} B={:d}".format(r.int(), g.int(), b.int())

class TRANSMATRIX(parray.type):
    length, _object_ = 3 * 4, pfloat.single
    def matrix(self):
        iterable = iter(n.float() for n in self)
        identity = iter([0, 0, 0, 1])

        # produce a matrix
        rows = []
        for r in range(4):
            row = []
            for c in range(3):
                row.append(next(iterable))
            row.append(next(identity))
            rows.append(row)
        return rows

    def summary(self):
        rows = self.matrix()
        return ' / '.join(''.join('[{:d}]'.format(math.trunc(r)) if math.trunc(r) == r else '[{:+f}]'.format(r) for r in row) for row in rows)

    def details(self):
        rows = self.matrix()
        return '\n'.join(''.join('[{:+f}]'.format(r) for r in row) for row in rows)

    def repr(self):
        return self.details()

### Chunk base types
class ChunkType(ptype.definition): cache = {}
class ID(pint.enum, pint.uint16_t):
    Type, _values_ = ChunkType, []
    @classmethod
    def define(cls, t):
        res = cls.Type.define(t)
        cls._values_.append((t.__name__, t.type))
        return res
class Chunk(pstruct.type):
    Identifier = ID
    def __Data(self):
        type, length = self['ID'].li, self['Length'].li
        cb = type.blocksize() + length.blocksize()
        if cb > length.int():
            raise AssertionError(cb, length)
        try:
            res = self.Identifier.Type.lookup(type.int())
            res = dyn.clone(res, blocksize=lambda s, res=length.int() - cb: res)
        except KeyError:
            res = dyn.block(length.int() - cb, type=type.int())
        return res

    _fields_ = [
        (lambda self: self.Identifier, 'ID'),
        (pint.uint32_t, 'Length'),
        (__Data, 'Data'),
    ]
class ChunkContainer(parray.block):
    _object_ = Chunk

### Chunk type definitions

## Main chunks base types
class MainChunkType(ptype.definition): cache = {}
class Main(ID): Type, _values_ = MainChunkType, []
class MainChunk(Chunk): Identifier = Main
class MainChunkContainer(parray.block): _object_ = MainChunk

## Edit chunks base types
class EditChunkType(ptype.definition): cache = {}
class Edit(ID): Type, _values_ = EditChunkType, []
class EditChunk(Chunk): Identifier = Edit
class EditChunkContainer(parray.block): _object_ = EditChunk

## Object chunks base types
class ObjectChunkType(ptype.definition): cache = {}
class Object(ID): Type, _values_ = ObjectChunkType, []
class ObjectChunk(Chunk): Identifier = Object
class ObjectChunkContainer(parray.block): _object_ = ObjectChunk

## Camera chunks base types
class CameraChunkType(ptype.definition): cache = {}
class Camera(ID): Type, _values_ = CameraChunkType, []
class CameraChunk(Chunk): Identifier = Camera
class CameraChunkContainer(parray.block): _object_ = CameraChunk

## Light chunks base types
class LightChunkType(ptype.definition): cache = {}
class Light(ID): Type, _values_ = LightChunkType, []
class LightChunk(Chunk): Identifier = Light
class LightChunkContainer(parray.block): _object_ = LightChunk

## KeyF chunks base types
class KeyFChunkType(ptype.definition): cache = {}
class KeyF(ID): Type, _values_ = KeyFChunkType, []
class KeyFChunk(Chunk): Identifier = KeyF
class KeyFChunkContainer(parray.block): _object_ = KeyFChunk

## Color chunks base types
class ColorChunkType(ptype.definition): cache = {}
class Color(ID): Type, _values_ = ColorChunkType, []
class ColorChunk(Chunk): Identifier = Color
class ColorChunkContainer(parray.block): _object_ = ColorChunk

## Viewport chunks base types
class ViewportChunkType(ptype.definition): cache = {}
class Viewport(ID): Type, _values_ = ViewportChunkType, []
class ViewportChunk(Chunk): Identifier = Viewport
class ViewportChunkContainer(parray.block): _object_ = ViewportChunk

## Material chunks base types
class MaterialChunkType(ptype.definition): cache = {}
class Material(ID): Type, _values_ = MaterialChunkType, []
class MaterialChunk(Chunk): Identifier = Material
class MaterialChunkContainer(parray.block): _object_ = MaterialChunk

## MaterialSub chunks base types
class MaterialSubChunkType(ptype.definition): cache = {}
class MaterialSub(ID): Type, _values_ = MaterialSubChunkType, []
class MaterialSubChunk(Chunk): Identifier = MaterialSub
class MaterialSubChunkContainer(parray.block): _object_ = MaterialSubChunk

## Tri chunks base types
class TriChunkType(ptype.definition): cache = {}
class Tri(ID): Type, _values_ = TriChunkType, []
class TriChunk(Chunk): Identifier = Tri
class TriChunkContainer(parray.block): _object_ = TriChunk

### Chunk definitions

## main chunk
@ID.define
class MAIN3DS(MainChunkContainer):
    type = 0x4d4d

@Main.define
class EDIT3DS(EditChunkContainer):
    type = 0x3d3d
@Main.define
class KEYF3DS(KeyFChunkContainer):
    type = 0xb000

## Edit chunks
@Edit.define
class EDIT_MATERIAL(MaterialChunkContainer):
    type = 0xafff
@Edit.define
class EDIT_CONFIG1(ptype.block):
    type = 0x0100
@Edit.define
class EDIT_CONFIG2(ptype.block):
    type = 0x3e3d
@Edit.define
class EDIT_VIEW_P1(ViewportChunkContainer):
    type = 0x7012
@Edit.define
class EDIT_VIEW_P2(ViewportChunkContainer):
    type = 0x7011
@Edit.define
class EDIT_VIEW_P3(ptype.block):
    type = 0x7020
@Edit.define
class EDIT_VIEW1(ptype.block):
    type = 0x7001
@Edit.define
class EDIT_BACKGR(ptype.block):
    type = 0x1200
@Edit.define
class EDIT_AMBIENT(ColorChunkContainer):
    type = 0x2100
@Edit.define
class EDIT_OBJECT(pstruct.type): # FIXME: ObjectChunkContainer?
    type = 0x4000
    _fields_ = [
        (pstr.szstring, 'name'),
        (ObjectChunk, 'chunk'),
    ]
@Edit.define
class EDIT_UNKNWN01(ptype.block):
    type = 0x1100
@Edit.define
class EDIT_UNKNWN02(ptype.block):
    type = 0x1201
@Edit.define
class EDIT_UNKNWN03(ptype.block):
    type = 0x1300
@Edit.define
class EDIT_UNKNWN04(ptype.block):
    type = 0x1400
@Edit.define
class EDIT_UNKNWN05(ptype.block):
    type = 0x1420
@Edit.define
class EDIT_UNKNWN06(ptype.block):
    type = 0x1450
@Edit.define
class EDIT_UNKNWN07(ptype.block):
    type = 0x1500
@Edit.define
class EDIT_UNKNWN08(ptype.block):
    type = 0x2200
@Edit.define
class EDIT_UNKNWN09(ptype.block):
    type = 0x2201
@Edit.define
class EDIT_UNKNWN10(ptype.block):
    type = 0x2210
@Edit.define
class EDIT_UNKNWN11(ptype.block):
    type = 0x2300
@Edit.define
class EDIT_UNKNWN12(ptype.block):
    type = 0x2302
@Edit.define
class EDIT_UNKNWN13(ptype.block):
    type = 0x3000

## Material chunks
@Material.define
class MAT_NAME(pstr.szstring): type = 0xa000
@Material.define
class MAT_AMBIENT(MaterialSubChunk): type = 0xa010
@Material.define
class MAT_DIFFUSE(MaterialSubChunk): type = 0xa020
@Material.define
class MAT_SPECULAR(MaterialSubChunk): type = 0xa030
@Material.define
class MAT_SHININESS(MaterialSubChunk): type = 0xa040
@Material.define
class MAT_SHININESS_STRENGTH(MaterialSubChunk): type = 0xa041
@Material.define
class MAT_TRANSPARENCY(MaterialSubChunk): type = 0xa050
@Material.define
class MAT_TRANSPARENCY_FALLOFF(MaterialSubChunk): type = 0xa052
@Material.define
class MAT_REFLECT_BLUR(MaterialSubChunk): type = 0xa053
@Material.define
class MAT_TYPE(pint.enum, pint.uint16_t):
    type = 0xa100
    _values_ = [
        ('flat', 1),
        ('gouraud', 2),
        ('phong', 3),
        ('metal', 4),
    ]
@Material.define
class MAT_SELF_ILLUM(MaterialSubChunk): type = 0xa084
@Material.define
class MAT_UNKNOWN(ptype.undefined): type = 0xa087
@Material.define
class MAT_SOME_TRANSPARENCY_FALLOFF_AMOUNT(ptype.undefined): type = 0xa240
@Material.define
class MAT_SOME_REFLECT_BLUR(ptype.undefined): type = 0xa250
@Material.define
class MAT_TWO_SIDED(ptype.undefined): type = 0xa081
@Material.define
class MAT_TRANSPARENCY_ADD(ptype.undefined): type = 0xa083
@Material.define
class MAT_WIRE_ON(ptype.undefined): type = 0xa085
@Material.define
class MAT_FACE_MAP(ptype.undefined): type = 0xa088
@Material.define
class MAT_TRANSPARENCY_FALLOFF_IN(ptype.undefined): type = 0xa08a
@Material.define
class MAT_SOFTEN(ptype.undefined): type = 0xa08c
@Material.define
class MAT_3D_WIRE_THICKNESS_IN_PIX(ptype.block): type = 0xa08e
@Material.define
class MAT_WIRE_THICKNESS(pfloat.single): type = 0xa087

@Material.define
class texture1_map(MaterialSubChunkContainer): type = 0xa200
@Material.define
class texture1_mask(MaterialSubChunkContainer): type = 0xa33e
@Material.define
class texture2_map(MaterialSubChunkContainer): type = 0xa33a
@Material.define
class texture2_mask(MaterialSubChunkContainer): type = 0xa340
@Material.define
class opacity_map(MaterialSubChunkContainer): type = 0xa210
@Material.define
class opacity_mask(MaterialSubChunkContainer): type = 0xa342
@Material.define
class bump_map(MaterialSubChunkContainer): type = 0xa230
@Material.define
class bump_mask(MaterialSubChunkContainer): type = 0xa344
@Material.define
class specular_map(MaterialSubChunkContainer): type = 0xa204
@Material.define
class specular_mask(MaterialSubChunkContainer): type = 0xa348
@Material.define
class shininess_map(MaterialSubChunkContainer): type = 0xa33c
@Material.define
class shininess_mask(MaterialSubChunkContainer): type = 0xa346
@Material.define
class self_illum_map(MaterialSubChunkContainer): type = 0xa33d
@Material.define
class self_illum_mask(MaterialSubChunkContainer): type = 0xa34a
@Material.define
class reflection_map(MaterialSubChunkContainer): type = 0xa220
@Material.define
class reflection_mask(MaterialSubChunkContainer): type = 0xa34c

## MaterialSub chunks
@MaterialSub.define
class RGB1(RGB): type = 0x0011
@MaterialSub.define
class RGB2(RGB): type = 0x0012
@MaterialSub.define
class intsh(pint.uint16_t): type = 0x0030
@MaterialSub.define
class asciiz(pstr.szstring): type = 0xa300
@MaterialSub.define
class map_options(pint.uint16_t): type = 0xa351 # FIXME: this is a pbinary.flags
@MaterialSub.define
class map_filtering_blur(pfloat.single): type = 0xa353
@MaterialSub.define
class u_scale(pfloat.single): type = 0xa354
@MaterialSub.define
class v_scale(pfloat.single): type = 0xa356
@MaterialSub.define
class u_offset(pfloat.single): type = 0xa358
@MaterialSub.define
class v_offset(pfloat.single): type = 0xa35a
@MaterialSub.define
class map_rotation_angle(pfloat.single): type = 0xa35c
@MaterialSub.define
class tint_first_color(RGB): type = 0xa360
@MaterialSub.define
class tint_secnd_color(RGB): type = 0xa362
@MaterialSub.define
class tint_Rchan_color(RGB): type = 0xa364
@MaterialSub.define
class tint_Gchan_color(RGB): type = 0xa366
@MaterialSub.define
class tint_Bchan_color(RGB): type = 0xa368
@MaterialSub.define
class tint_Bchan_color(RGB): type = 0xa368

## KeyF chunks
@KeyF.define
class KEYF_UNKNWN01(ptype.block): type = 0xb009
@KeyF.define
class KEYF_UNKNWN02(ptype.block): type = 0xb00a
@KeyF.define
class KEYF_FRAMES(pstruct.type):
    type = 0xb008
    _fields_ = [
        (pint.uint32_t, 'start'),
        (pint.uint32_t, 'end'),
    ]
@KeyF.define
class KEYF_OBJDES(KeyFChunkContainer): type = 0xb002
@KeyF.define
class KEYF_OBJINDEX(pint.uint16_t): type = 0xb030
@KeyF.define
class KEYF_OBJHIERARCH(pstruct.type):
    type = 0xb010
    _fields_ = [
        (pstr.szstring, 'name'),
        (pint.uint16_t, 'flags1'),
        (pint.uint16_t, 'flags2'),
        (pint.uint16_t, 'hierarchy'),
    ]
@KeyF.define
class KEYF_OBJDUMMYNAME(pstr.szstring): type = 0xb011
@KeyF.define
class KEYF_OBJPIVOT(ptype.block): type = 0xb013
@KeyF.define
class KEYF_OBJBOUNDBOX(parray.type):
    type = 0xb014
    length, _object_ = 6, pfloat.single
    def summary(self):
        iterable = (n.float() for n in self)
        return "[{:s}]".format(', '.join(map("{:f}".format, iterable)))
@KeyF.define
class KEYF_OBJUNKNWN03(ptype.block): type = 0xb015
@KeyF.define
class KEYF_OBJPOSITION(pstruct.type):
    type = 0xb020
    class key(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'framenum'),
            (pint.uint32_t, 'unknown'),
            (pfloat.single, 'x'),
            (pfloat.single, 'y'),
            (pfloat.single, 'z'),
        ]
        def summary(self):
            x, y, z = (self[k] for k in 'xyz')
            return "framenum({:d}) unknown({:#x}) ({:f}, {:f}, {:f})".format(self['framenum'].int(), self['unknown'].int(), x.float(), y.float(), z.float())
    _fields_ = [
        (pint.uint16_t, 'flags'),
        (dyn.array(pint.uint16_t, 4), 'unknown_0'),
        (pint.uint16_t, 'keys'),
        (pint.uint16_t, 'unknown_1'),
        (lambda self: dyn.array(self.key, self['keys'].li.int()), 'pos'),
    ]
@KeyF.define
class KEYF_OBJROTATION(pstruct.type):
    type = 0xb021
    class key(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'framenum'),
            (pint.uint32_t, 'unknown'),
            (pfloat.single, 'angle'),
            (pfloat.single, 'x'),
            (pfloat.single, 'y'),
            (pfloat.single, 'z'),
        ]
        def summary(self):
            x, y, z = (self[k] for k in 'xyz')
            return "framenum({:d}) unknown({:#x}) ({:f}, {:f}, {:f})".format(self['framenum'].int(), self['unknown'].int(), x.float(), y.float(), z.float())
    _fields_ = [
        (pint.uint16_t, 'flags'),
        (dyn.array(pint.uint16_t, 4), 'unknown_0'),
        (pint.uint16_t, 'keys'),
        (pint.uint16_t, 'unknown_1'),
        (lambda self: dyn.array(self.key, self['keys'].li.int()), 'rotate'),
    ]
@KeyF.define
class KEYF_OBJSCALING(pstruct.type):
    type = 0xb022
    class key(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'framenum'),
            (pint.uint32_t, 'unknown'),
            (pfloat.single, 'x'),
            (pfloat.single, 'y'),
            (pfloat.single, 'z'),
        ]
        def summary(self):
            x, y, z = (self[k] for k in 'xyz')
            return "framenum({:d}) unknown({:#x}) ({:f}, {:f}, {:f})".format(self['framenum'].int(), self['unknown'].int(), x.float(), y.float(), z.float())
    _fields_ = [
        (pint.uint16_t, 'flags'),
        (dyn.array(pint.uint16_t, 4), 'unknown_0'),
        (pint.uint16_t, 'keys'),
        (pint.uint16_t, 'unknown_1'),
        (lambda self: dyn.array(self.key, self['keys'].li.int()), 'scale'),
    ]

## object chunks
@Object.define
class OBJ_TRIMESH(TriChunkContainer): type = 0x4100
@Object.define
class OBJ_LIGHT(LightChunkContainer): type = 0x4600
@Object.define
class OBJ_CAMERA(CameraChunkContainer): type = 0x4700
@Object.define
class OBJ_UNKNWN01(ptype.block): type = 0x4710
@Object.define
class OBJ_UNKNWN02(ptype.block): type = 0x4720

## tri chunks
@Tri.define
class TRI_VERTEXL(pstruct.type):
    type = 0x4110
    class vertex(pstruct.type):
        _fields_ = [(pfloat.single, 'x'), (pfloat.single, 'y'), (pfloat.single, 'z')]
        def summary(self):
            x, y, z = (self[k] for k in 'xyz')
            return "({:f}, {:f}, {:f})".format(x.float(), y.float(), z.float())
    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(self.vertex, self['count'].li.int()), 'vertex'),
    ]
@Tri.define
class TRI_VERTEXOPTIONS(ptype.block): type = 0x4111
@Tri.define
class TRI_MAPPINGCOORS(pstruct.type):
    type = 0x4140
    class vertex(pstruct.type):
        _fields_ = [(pfloat.single, 'x'), (pfloat.single, 'y')]
        def summary(self):
            x, y = (self[k] for k in 'xy')
            return "({:f}, {:f})".format(x.float(), y.float())

    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(self.vertex, self['count'].li.int()), 'vertex'),
    ]
@Tri.define
class TRI_MAPPINGSTANDARD(ptype.block): type = 0x4170
@Tri.define
class TRI_FACEL1(pstruct.type):
    type = 0x4120
    class face(pstruct.type):
        class faceinfo(pint.uint16_t): pass # XXX: this is a pbinary.flags
        _fields_ = [
            (pint.uint16_t, 'vertexA'),
            (pint.uint16_t, 'vertexB'),
            (pint.uint16_t, 'vertexC'),
            (faceinfo, 'faceinfo'),
        ]
        def summary(self):
            A, B, C = (self['vertex'+k] for k in 'ABC')
            return "vertices=({:d},{:d},{:d}) faceinfo={:#x}".format(A.int(), B.int(), C.int(), self['faceinfo'].int())
    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(self.face, self['count'].li.int()), 'face'),
        (lambda self: dyn.clone(TriChunkContainer, blocksize=lambda s, cb=self.blocksize()-(self['count'].li.size()+self['face'].li.size()): cb), 'facedata'),
    ]
@Tri.define
class TRI_SMOOTH(parray.block):
    type = 0x4150
    _object_ = pint.uint32_t

@Tri.define
class TRI_MATERIAL(pstruct.type):
    type = 0x4130
    _fields_ = [
        (pstr.szstring, 'material'),
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(pint.uint16_t, self['count'].li.int()), 'face'),
    ]
@Tri.define
class TRI_LOCAL(TRANSMATRIX): type = 0x4160
@Tri.define
class TRI_VISIBLE(ptype.block): type = 0x4165

## lit chunks
@Light.define
class LIT_OFF(ptype.block): type = 0x4620
@Light.define
class LIT_SPOT(ptype.block): type = 0x4610
@Light.define
class LIT_UNKNWN01(ptype.block): type = 0x465a

## lit chunks
@Camera.define
class CAM_UNKNWN01(ptype.block): type = 0x4710
@Camera.define
class CAM_UNKNWN02(ptype.block): type = 0x4720

## color chunks
@Color.define
class COL_RGB(RGB): type = 0x0010
@Color.define
class COL_TRU(RGB): type = 0x0011
@Color.define
class COL_UNK(ptype.block): type = 0x0013

# viewport chunks
@Viewport.define
class TOP(ptype.block): type = 0x0001
@Viewport.define
class BOTTOM(ptype.block): type = 0x0002
@Viewport.define
class LEFT(ptype.block): type = 0x0003
@Viewport.define
class RIGHT(ptype.block): type = 0x0004
@Viewport.define
class FRONT(ptype.block): type = 0x0005
@Viewport.define
class BACK(ptype.block): type = 0x0006
@Viewport.define
class USER(ptype.block): type = 0x0007
@Viewport.define
class CAMERA(ptype.block): type = 0x0008
@Viewport.define
class LIGHT(ptype.block): type = 0x0009
@Viewport.define
class DISABLED(ptype.block): type = 0x0010
@Viewport.define
class BOGUS(ptype.block): type = 0x0011

## File chunk
class File(Chunk): pass

if __name__ == '__main__':
    import ptypes, max
    ptypes.setsource(ptypes.prov.file('./samples/3ds/boletus.3ds', mode='rb'))
    z = max.File()
    z=z.l
    print z['data']

    print z['data'][1]['data'][0]['data']
    print z['data'][1]['data'][1]
    print z['data'][1]['data'][2]['data'][0]['data']
    print z['data'][1]['data'][3]['data']['chunk']['data'][0]['data']   # TRI_VERTEXL
    print z['data'][1]['data'][3]['data']['chunk']['data'][1]['data']   # TRI_LOCAL
    print z['data'][1]['data'][3]['data']['chunk']['data'][2]['data']   # TRI_MAPPINGCOORS
    print z['data'][1]['data'][3]['data']['chunk']['data'][3]
    print z['data'][1]['data'][3]['data']['chunk']['data'][3]['data']
    print z['data'][1]['data'][3]['data']['chunk']['data'][3]['data']['face']
    print z['data'][1]['data'][3]['data']['chunk']['data'][3]['data']['facedata'][0]['data']['face']
    print z['data'][1]['data'][3]['data']['chunk']['data'][3]['data']['facedata'][1]['data']
    print max.TriChunk(offset=0x228a).l
    print max.TriChunk(offset=0x25d6).l
    print z['data'][2]['data'][0]
    print z['data'][2]['data'][1]
    print z['data'][2]['data'][2]

    print z['data'][2]['data'][3]
    print z['data'][2]['data'][3]['data'][0]    # KEYF_OBJINDEX
    print z['data'][2]['data'][3]['data'][1]    # KEYF_OBJHIERARCH
    print z['data'][2]['data'][3]['data'][1]['data']
    print z['data'][2]['data'][3]['data'][2]    # KEYF_OBJBOUNDBOX
    print z['data'][2]['data'][3]['data'][2]['data']
    print z['data'][2]['data'][3]['data'][3]    # KEYF_OBJPIVOT
    print z['data'][2]['data'][3]['data'][3]['data']['pos'][0]
    print z['data'][2]['data'][3]['data'][4]    # KEYF_OBJSCALING
    print z['data'][2]['data'][3]['data'][4]['data']['scale'][0]
    print z['data'][2]['data'][3]['data'][5]    # KEYF_OBJROTATION
    print z['data'][2]['data'][3]['data'][5]['data']['rotate'][0]

if __name__ == '__main__':
    import ptypes, max
    ptypes.setsource(ptypes.prov.file('./results/3ds/crashes/id_000071_00', mode='rb'))
    ptypes.setsource(ptypes.prov.file('./samples/3ds/boletus.3ds', mode='rb'))
    z = max.File()
    z=z.l
    print z.at(0x12f).getparent(max.Chunk)
    print z.at(0x11d).getparent(max.Chunk)
