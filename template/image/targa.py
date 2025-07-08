import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

class u0(pint.uint_t): pass
class u1(pint.uint8_t): pass
class u2(pint.uint16_t): pass
class u4(pint.uint32_t): pass
class s0(pint.sint_t): pass
class s1(pint.sint8_t): pass
class s2(pint.sint16_t): pass
class s4(pint.sint32_t): pass

class char(u1): pass
class short(s2): pass
class short_int(s2): pass

class ColorMapType(pint.enum, char):
    _values_ = [
        ('None', 0),
        ('Map', 1),
    ]

class ImageTypeCode(pint.enum, char):
    _values_ = [
        ('None', 0),                    # No image data included.
        ('Indexed', 1),                 # Uncompressed, color-mapped images.
        ('RGB', 2),                     # Uncompressed, RGB images.
        ('BW', 3),                      # Uncompressed, black and white images.
        ('RLE-Indexed', 9),             # Runlength encoded color-mapped images.
        ('RLE-RGB', 10),                # Runlength encoded RGB images.
        ('RLE-BW', 11),                 # Compressed, black and white images.
        ('Comp-HDR', 32),               # Compressed color-mapped data, using Huffman, Delta, and runlength encoding.
        ('Comp-HDR-Quadtree', 33),      # Compressed color-mapped data, using Huffman, Delta, and runlength encoding.  4-pass quadtree-type process.
    ]

class Footer(pstruct.type):
    class _Signature(pstr.string):
        length = 16
        def alloc(self, *values, **attributes):
            if not(values):
                return self.alloc('TRUEVISION-XFILE', **attributes)
            return super(Footer._Signature, self).alloc(*values, **attributes)
    _fields_ = [
        (dyn.pointer(ptype.block, u4), 'ExtensionOffset'),
        (dyn.pointer(ptype.block, u4), 'DeveloperAreaOffsert'),
        (_Signature, 'Signature'),
        (pstr.char_t, 'dot'),
        (pstr.char_t, 'null'),
    ]
    def alloc(self, **fields):
        fields.setdefault('Signature', Footer._Signature)
        res = super(Footer, self).alloc(**fields)
        if 'dot' not in fields:
            res['dot'].set('.')
        if 'null' not in fields:
            res['null'].set('\0')
        return res

class ColorMapSpecification(pstruct.type):
    _fields_ = [
        (u2, 'Origin'),     # Color Map Origin.
        (u2, 'Length'),     # Color Map Length.
        (u1, 'EntrySize'),  # Color Map Entry Size.
    ]
    def alloc(self, **fields):
        fields.setdefault('EntrySize', 3)
        return super(ColorMapSpecification, self).alloc(**fields)

class ColorMapEntries(ptype.definition):
    cache = {}

@ColorMapEntries.define
class ColorMapEntry4(pstruct.type):
    type = 4
    _fields_ = [
        (u1, 'B'),
        (u1, 'G'),
        (u1, 'R'),
        (u1, 'A'),
    ]

@ColorMapEntries.define
class ColorMapEntry3(pstruct.type):
    type = 3
    _fields_ = [
        (u1, 'B'),
        (u1, 'G'),
        (u1, 'R'),
    ]

@ColorMapEntries.define
class ColorMapEntry2(pbinary.struct):
    type = 2
    _fields_ = [
        (1, 'A'),
        (5, 'R'),
        (5, 'G'),
        (5, 'B'),
    ]

@ColorMapEntries.define
class ColorMapEntry0(ptype.undefined):
    type = 0

class ColorMapData(parray.type):
    pass

class ImageSpecification(pstruct.type):
    class _ImageDescriptorByte(pbinary.struct):
        ''' FIXME: pretty sure this definition is completely wrong. '''
        class _InterleavingFlag(pbinary.enum):
            length, _values_ = 2, [
                ('non-interleaved', 0), # non-interleaved.
                ('two-way', 1),         # two-way (even/odd) interleaving.
                ('four-way', 2),        # four way interleaving.
                ('reserved', 3),        # reserved.
            ]
        class _ScreenOriginBit(pbinary.enum):
            length, _values_ = 1, [
                ('lower-left', 0),
                ('upper-left', 1),
            ]
        class _MirroringBits(pbinary.flags):
            _fields_ = [
                (1, 'Vertical'),
                (1, 'Horizontal'),
            ]
        _fields_ = [
            (_InterleavingFlag, 'InterleavingFlag'),    # Data storage interleaving flag.
            (_MirroringBits, 'Mirroring'),              # flipped horizontal or vertical.
            (4, 'AttributeCount'),                      # number of attribute bits associated with each pixel.
        ]
    _fields_ = [
        (u2, 'XOrigin'),                                # X Origin of Image.
        (u2, 'YOrigin'),                                # Y Origin of Image.
        (u2, 'Width'),                                  # Width of Image.
        (u2, 'Height'),                                 # Height of Image.
        (u1, 'ImagePixelSize'),                         # Image Pixel Size.
        (_ImageDescriptorByte, 'ImageDescriptorByte'),  # Image Descriptor Byte.
    ]

class ImageDataPacket(pstruct.type):
    class _RepetitionCount(pbinary.flags):
        _fields_ = [
            (1, 'RLE'),
            (7, 'Count'),
        ]
    def __Entry(self):
        res = self['RepetitionCount'].li
        entry_t = ColorMapEntries.lookup(getattr(self, '_type_', 0), ptype.block)
        if res['RLE']:
            return entry_t
        return dyn.array(entry_t, 1 + res['Count'])
    _fields_ = [
        (_RepetitionCount, 'RepetitionCount'),
        (__Entry, 'Entry'),
    ]
    def alloc(self, **fields):
        if 'RepetitionCount' in fields:
            return super(ImageDataPacket, self).alloc(**fields)
        RepetitionCount = ImageDataPacket._RepetitionCount()
        RepetitionCount.set(**fields)
        [fields.pop(fld, 0) for fld in ['RLE', 'Count']]
        fields.setdefault('RepetitionCount', RepetitionCount)
        return self.alloc(**fields)

class File(pstruct.type):
    def __ImageIdentification(self):
        length = self['IdentificationLength'].li.int()
        return dyn.block(length) if length else ptype.block

    def __ColorMapData(self):
        specification = self['ColorMapSpecification'].li
        length, element = (specification[fld].int() for fld in ['Length', 'EntrySize'])
        entry_t = ColorMapEntries.lookup(element)
        return dyn.clone(ColorMapData, _object_=entry_t, length=0 if self['ColorMapType'].li.int() == 0 else length)

    _fields_ = [
        (u1, 'IdentificationLength'),                       # Number of Characters in Identification Field.
        (ColorMapType, 'ColorMapType'),                     # Color Map Type.
        (ImageTypeCode, 'ImageTypeCode'),                   # Image Type Code.
        (ColorMapSpecification, 'ColorMapSpecification'),   # Color Map Specification.
        (ImageSpecification, 'ImageSpecification'),         # Image Specification.
        (__ImageIdentification, 'ImageIdentification'),     # Image Identification Field.
        (__ColorMapData, 'ColorMapData'),                   # Color Map data.

        (ptype.block, 'ImageData'),
        (ptype.block, 'DeveloperFields'),
        (ptype.block, 'DeveloperDirectory'),
        (ptype.block, 'ExtensionSize'),
        (ptype.block, 'ScanLineTable'),
        (ptype.block, 'PostageStampImage'),
        (ptype.block, 'ColorCorrectionTable'),

        (Footer, 'Footer'),
    ]
    def alloc(self, **fields):
        newfields = fields.copy()
        newfields.setdefault('ColorMapSpecification', ColorMapSpecification)
        newfields.setdefault('ImageSpecification', ImageSpecification)
        res = super(File, self).alloc(**newfields)

        if 'IdentificationLength' not in fields:
            res['IdentificationLength'].set(res['ImageIdentification'].size())

        elif 'ImageSpecification' in fields:
            return res

        imagetype = res['ImageTypeCode']
        if any(imagetype[fld] for fld in ['Indexed', 'RLE-Indexed']):
            bpp = 8
        elif any(imagetype[fld] for fld in ['RGB', 'RLE-RGB']):
            bpp = 24
        elif any(imagetype[fld] for fld in ['BW', 'RLE-RGB']):
            bpp = 8
        else:
            return res

        res['ImageSpecification']['ImagePixelSize'].set(bpp)
        return res

if __name__ == '__main__':
    import sys
    import ptypes, image.targa

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.targa.File()
    a = a.l
