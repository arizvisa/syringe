import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

class DataType(pint.enum, pint.uint8_t):
    _values_ = [
        ('No image data included.', 0),
        ('Uncompressed, color-mapped images.', 1),
        ('Uncompressed, RGB images.', 2),
        ('Uncompressed, black and white images.', 3),
        ('Runlength encoded color-mapped images.', 9),
        ('Runlength encoded RGB images.', 10),
        ('Compressed, black and white images.', 11),
        ('Compressed color-mapped data, using Huffman, Delta, and runlength encoding.', 32),
        ('Compressed color-mapped data, using Huffman, Delta, and runlength encoding.  4-pass quadtree-type process.', 33),
    ]

class ColorMapSpecification(pstruct.type):
    _fields_ = [
        (pint.sint16_t, 'FirstEntryIndex'),
        (pint.sint16_t, 'Length'),
        (pint.uint8_t, 'EntrySize'),
    ]

class Dimensions(pstruct.type):
    _fields_ = [
        (pint.sint16_t, 'x'),
        (pint.sint16_t, 'y'),
        (pint.sint16_t, 'width'),
        (pint.sint16_t, 'height'),
    ]

class Header(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'numid'),
        (pint.uint8_t, 'maptyp'),
        (DataType, 'imgtyp'),
        (ColorMapSpecification, 'mapspec'),
        (Dimensions, 'imgdim'),
        (pint.uint8_t, 'pixdepth'),
        (pint.uint8_t, 'imgdes'),
    ]

class File(pstruct.type):
    _fields_ = [
        (Header, 'Header'),
        (ptype.block, 'Data'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, image.targa

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.targa.File()
    a = a.l
