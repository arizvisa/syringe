import ptypes
from ptypes import *

class unsigned_int(pint.uint32_t): pass
class unsigned_short(pint.uint16_t): pass
class unsigned_char(pint.uint8_t): pass
class char(pint.sint8_t): pass
class float(pfloat.single): pass
class signed_int(pint.sint32_t): pass

class CineonFileHeader(pstruct.type):
    class magic_num(unsigned_int):
        @classmethod
        def default(cls):
            return cls().set(0x802A5FD7)
        def valid(self):
            return self.int() == self.default().int()
        def properties(self):
            res = super(CineonFileHeader.magic_num, self).properties()
            res['valid'] = self.valid()
            return res

    _fields_ = [
        (magic_num, 'magic_num'),
        (unsigned_int, 'offset'),
        (unsigned_int, 'gen_hdr_size'),
        (unsigned_int, 'ind_hdr_size'),
        (unsigned_int, 'user_data_size'),
        (unsigned_int, 'file_size'),
        (dyn.clone(pstr.string, length=8), 'version'),
        (dyn.clone(pstr.string, length=100), 'file_name'),
        (dyn.clone(pstr.string, length=12), 'creation_date'),
        (dyn.clone(pstr.string, length=12), 'creation_time'),
        (dyn.block(36), 'reserved'),
    ]

class CineonElementHeader(pstruct.type):
    _fields_ = [
        (unsigned_char, 'descriptor1'),
        (unsigned_char, 'descriptor2'),
        (unsigned_char, 'bits_per_sample'),
        (unsigned_char, 'filler'),
        (unsigned_int, 'pixels_per_line'),
        (unsigned_int, 'lines_per_image'),
        (unsigned_int, 'ref_low_data'),
        (float, 'ref_low_quantity'),
        (unsigned_int, 'ref_high_data'),
        (float, 'ref_high_quantity'),
    ]

class CineonImageHeader(pstruct.type):
    _fields_ = [
        (unsigned_char, 'orientation'),
        (unsigned_char, 'elements_per_image'),
        (unsigned_short, 'filler'),
        #(dyn.array(CineonElementHeader, 8), 'element'),
        (lambda s: dyn.array(CineonElementHeader, s['elements_per_image'].li.int()), 'element'),
        (float, 'white_point_x'),
        (float, 'white_point_y'),
        (float, 'red_primary_x'),
        (float, 'red_primary_y'),
        (float, 'green_primary_x'),
        (float, 'green_primary_y'),
        (float, 'blue_primary_x'),
        (float, 'blue_primary_y'),
        (dyn.clone(pstr.string,length=200), 'label'),
        (dyn.block(28), 'reserved'),
        (unsigned_char, 'interleave'),
        (unsigned_char, 'packing'),
        (unsigned_char, 'data_sign'),
        (unsigned_char, 'sense'),
        (unsigned_int, 'line_padding'),
        (unsigned_int, 'element_padding'),
        (dyn.block(20), 'reserved2'),
    ]

class CineonOriginationHeader(pstruct.type):
    _fields_ = [
        (signed_int, 'x_offset'),
        (signed_int, 'y_offset'),
        (dyn.clone(pstr.string, length=100), 'file_name'),
        (dyn.clone(pstr.string, length=12), 'creation_date'),
        (dyn.clone(pstr.string, length=12), 'creation_time'),
        (dyn.clone(pstr.string, length=64), 'input_device'),
        (dyn.clone(pstr.string, length=32), 'model_number'),
        (dyn.clone(pstr.string, length=32), 'input_serial_number'),
        (float, 'x_input_samples_per_mm'),
        (float, 'y_input_samples_per_mm'),
        (float, 'input_device_gamma'),
        (dyn.block(40), 'reserved'),
    ]

class CineonFilmHeader(pstruct.type):
    _fields_ = [
        (unsigned_char, 'film_code'),
        (unsigned_char, 'film_type'),
        (unsigned_char, 'edge_code_perforation_offset'),
        (unsigned_char, 'filler'),
        (unsigned_int, 'prefix'),
        (unsigned_int, 'count'),
        (dyn.clone(pstr.string, length=32), 'format'),
        (unsigned_int, 'frame_position'),
        (float, 'frame_rate'),
        (dyn.clone(pstr.string, length=32), 'attribute'),
        (dyn.clone(pstr.string, length=200), 'slate'),
        (dyn.block(740), 'reserved'),
    ]

class CineonMainHeader(pstruct.type):
    _fields_ = [
        (CineonFileHeader, 'fileHeader'),
        (CineonImageHeader, 'imageHeader'),
        (CineonOriginationHeader, 'originationHeader'),
        (CineonFilmHeader, 'filmHeader'),
    ]

class File(pstruct.type):
    _fields_ = [
        (CineonMainHeader, 'header'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, image.cineon

    if len(sys.argv) != 2:
        print "Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__)
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.cineon.File()
    a = a.l
