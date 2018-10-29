import ptypes
from ptypes import *

class unsigned_int(pint.uint32_t): pass
class unsigned_short(pint.uint16_t): pass
class unsigned_char(pint.uint8_t): pass
class char(pint.sint8_t): pass
class float(pfloat.single): pass

class DpxFileHeader(pstruct.type):
    class magic_num(unsigned_int):
        @classmethod
        def default(cls):
            return cls().set(0x53445058)
        def valid(self):
            return self.int() == self.default().int()
        def properties(self):
            res = super(DpxFileHeader.magic_num, self).properties()
            res['valid'] = self.valid()
            return res
    _fields_ = [
        (magic_num, 'magic_num'),
        (unsigned_int, 'offset'),
        (dyn.clone(pstr.string, length=8), 'version'),
        (unsigned_int, 'file_size'),
        (unsigned_int, 'ditto_key'),
        (unsigned_int, 'gen_hdr_size'),
        (unsigned_int, 'ind_hdr_size'),
        (unsigned_int, 'user_data_size'),
        (dyn.clone(pstr.string, length=100), 'file_name'),
        (dyn.clone(pstr.string, length=24), 'creation_date'),
        (dyn.clone(pstr.string, length=100), 'creator'),
        (dyn.clone(pstr.string, length=200), 'project'),
        (dyn.clone(pstr.string, length=200), 'copyright'),
        (unsigned_int, 'key'),
        (dyn.block(104), 'reserved'),
    ]

class DpxElementHeader(pstruct.type):
    class descriptor(pint.enum, unsigned_char):
        _values_ = [
            ('UserDefined', 0),
            ('Red', 1),
            ('Green', 2),
            ('Blue', 3),
            ('Alpha', 4),
            ('Luminance', 6),
            ('Chrominance', 7),
            ('Depth', 8),
            ('Composite', 9),
            ('RGB', 50),
            ('RGBA', 51),
            ('ABGR', 52),
            ('CbYCrY', 100),
            ('CbYACrYA', 101),
            ('CbYCr', 102),
            ('CbYCrA', 103),
            ('UserDefined2Elt', 150),
            ('UserDefined3Elt', 151),
            ('UserDefined4Elt', 152),
            ('UserDefined5Elt', 153),
            ('UserDefined6Elt', 154),
            ('UserDefined7Elt', 155),
            ('UserDefined8Elt', 156),
            ('YA', 157),
        ]

    _fields_ = [
        (unsigned_int, 'data_sign'),
        (unsigned_int, 'ref_low_data'),
        (float, 'ref_low_quantity'),
        (unsigned_int, 'ref_high_data'),
        (float, 'ref_high_quantity'),
        (descriptor, 'descriptor'),
        (unsigned_char, 'transfer'),
        (unsigned_char, 'colorimetric'),
        (unsigned_char, 'bits_per_sample'),
        (unsigned_short, 'packing'),
        (unsigned_short, 'encoding'),
        (unsigned_int, 'data_offset'),
        (unsigned_int, 'line_padding'),
        (unsigned_int, 'element_padding'),
        (dyn.clone(pstr.string, length=32), 'description'),
    ]

class DpxImageHeader(pstruct.type):
    _fields_ = [
        (unsigned_short, 'orientation'),
        (unsigned_short, 'elements_per_image'),
        (unsigned_int, 'pixels_per_line'),
        (unsigned_int, 'lines_per_element'),
        #(dyn.clone(DpxElementHeader, length=8), 'element'),
        (lambda s: dyn.array(DpxElementHeader, s['elements_per_image'].li.int()), 'element'),
        (dyn.block(52), 'reserved'),
    ]

class DpxOrientationHeader(pstruct.type):
    _fields_ = [
        (unsigned_int, 'x_offset'),
        (unsigned_int, 'y_offset'),
        (float, 'x_center'),
        (float, 'y_center'),
        (unsigned_int, 'x_original_size'),
        (unsigned_int, 'y_original_size'),
        (dyn.clone(pstr.string, length=100), 'file_name'),
        (dyn.clone(pstr.string, length=24), 'creation_time'),
        (dyn.clone(pstr.string, length=32), 'input_device'),
        (dyn.clone(pstr.string, length=32), 'input_serial_number'),
        (dyn.array(unsigned_short, 4), 'border_validity'),
        (dyn.array(unsigned_int, 2), 'pixel_aspect_ratio'),
        (dyn.block(28), 'reserved'),
    ]

class DpxFilmHeader(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=2), 'film_manufacturer_id'),
        (dyn.clone(pstr.string, length=2), 'film_type'),
        (dyn.clone(pstr.string, length=2), 'edge_code_perforation_offset'),
        (dyn.clone(pstr.string, length=6), 'edge_code_prefix'),
        (dyn.clone(pstr.string, length=4), 'edge_code_count'),
        (dyn.clone(pstr.string, length=32), 'film_format'),
        (unsigned_int, 'frame_position'),
        (unsigned_int, 'sequence_length'),
        (unsigned_int, 'held_count'),
        (float, 'frame_rate'),
        (float, 'shutter_angle'),
        (dyn.clone(pstr.string, length=32), 'frame_identification'),
        (dyn.clone(pstr.string, length=100), 'slate_info'),
        (dyn.block(56), 'reserved'),
    ]

class DpxTelevisionHeader(pstruct.type):
    _fields_ = [
        (unsigned_int, 'time_code'),
        (unsigned_int, 'user_bits'),
        (unsigned_char, 'interlace'),
        (unsigned_char, 'field_number'),
        (unsigned_char, 'video_signal'),
        (unsigned_char, 'padding'),
        (float, 'horizontal_sample_rate'),
        (float, 'vertical_sample_rate'),
        (float, 'frame_rate'),
        (float, 'time_offset'),
        (float, 'gamma'),
        (float, 'black_level'),
        (float, 'black_gain'),
        (float, 'breakpoint'),
        (float, 'white_level'),
        (float, 'integration_times'),
        (dyn.block(76), 'reserved'),
    ]

class DpxMainHeader(pstruct.type):
    _fields_ = [
        (DpxFileHeader, 'fileHeader'),
        (DpxImageHeader, 'imageHeader'),
        (DpxOrientationHeader, 'orientationHeader'),
        (DpxFilmHeader, 'filmHeader'),
        (DpxTelevisionHeader, 'televisionHeader'),
    ]

class File(pstruct.type):
    _fields_ = [
        (DpxMainHeader, 'header'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, image.dpx

    if len(sys.argv) != 2:
        print "Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__)
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.dpx.File()
    a = a.l
