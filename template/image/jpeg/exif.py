import ptypes, image.tiff as tiff
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### types
class Type(tiff.Type):
    class _enum_(pint.enum, pint.uint16_t):
        pass

class File(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'signature'),
        (tiff.Header, 'header'),
    ]

class DirectoryType(Type.enum):
    pass

### tags
class Tags(ptype.definition):
    attribute, cache = 'tag', {}
class TagValue(ptype.definition):
    cache = {}

class EXIFTAG(pint.enum):
    _values_ = [
        ('ImageWidth', 256),                    # 100 SHORT or LONG 1
        ('ImageLength', 257),                   # 101 SHORT or LONG 1
        ('BitsPerSample', 258),                 # 102 SHORT 3
        ('Compression', 259),                   # 103 SHORT 1
        ('PhotometricInterpretation', 262),     # 106 SHORT 1
        ('Orientation', 274),                   # 112 SHORT 1
        ('SamplesPerPixel', 277),               # 115 SHORT 1
        ('PlanarConfiguration', 284),           # 11C SHORT 1
        ('YCbCrSubSampling', 530),              # 212 SHORT 2
        ('YCbCrPositioning', 531),              # 213 SHORT 1
        ('XResolution', 282),                   # 11A RATIONAL 1
        ('YResolution', 283),                   # 11B RATIONAL 1
        ('ResolutionUnit', 296),                # 128 SHORT 1
        ('StripOffsets', 273),                  # 111 SHORT or LONG *S
        ('RowsPerStrip', 278),                  # 116 SHORT or LONG 1
        ('StripByteCounts', 279),               # 117 SHORT or LONG *S
        ('JPEGInterchangeFormat', 513),         # 201 LONG 1
        ('JPEGInterchangeFormatLength', 514),   # 202 LONG 1
        ('TransferFunction', 301),              # 12D SHORT 3 * 256
        ('WhitePoint', 318),                    # 13E RATIONAL 2
        ('PrimaryChromaticities', 319),         # 13F RATIONAL 6
        ('YCbCrCoefficients', 529),             # 211 RATIONAL 3
        ('ReferenceBlackWhite', 532),           # 214 RATIONAL 6
        ('DateTime', 306),                      # 132 ASCII 20
        ('ImageDescription', 270),              # 10E ASCII Any
        ('Make', 271),                          # 10F ASCII Any
        ('Model', 272),                         # 110 ASCII Any
        ('IFD', 34665),
    ]

@pint.littleendian
class DirectoryTag(EXIFTAG, pint.uint16_t):
    pass

### file
class Entry(pstruct.type):
    def __figure_type(self):
        tag_f, type_f = (self[fld].li for fld in ['tag', 'type'])

        # determine the base type
        type_ = Type.lookup(type_f.int(), pint.uint32_t)
        if not TagValue.has(tag_f.str()):
            return type_

        # determine the tag
        tag_ = TagValue.lookup(tag_f.str())

        # construct an enumeration type dynamically so that we can match the
        # exact type that was defined for the entry.
        ns = {key : value for key, value in tag_.__dict__.items()}
        ns.update(type_.__dict__)
        return type(tag_.__name__, (tag_, type_), ns)

    def __value(self):
        # FIXME: we need to use the tagvalue somehow to determine
        #        whether the type+tag combination results in this
        #        actually being a pointer/offset or just a long.
        t, count = self.__figure_type(), self['count'].li.int()

        # if the length of our value is less than a dword, then the
        # type's value can be stored within the entry. otherwise,
        # we undefine it so that we use the pointer.
        return t if t().a.size() * count <= 4 else ptype.undefined

    def __padding(self):
        if isinstance(self['value'].li, ptype.undefined):
            return ptype.block
        cb = max(0, 4 - self['value'].li.size())
        return dyn.block(cb) if cb else ptype.block

    def __pointer(self):
        t, count = self.__figure_type(), self['count'].li.int()
        result = dyn.clone(parray.type, _object_=t, length=count)

        # figure out what type of pointer we need to use
        p = self.parent and self.getparent(File, default=None)
        make_pointer = dyn.pointer if p is None else lambda target, type, file=p: dyn.rpointer(target, file['header'], type, byteorder=file['header'].Order())

        # if the value has been undefined, then this is a pointer
        # to the result type.
        if isinstance(self['value'].li, ptype.undefined):
            return make_pointer(result, pint.uint32_t)

        # otherwise our value is in the proper place, and we
        # need to return an unsized fake pointer.
        return make_pointer(ptype.undefined, pint.uint_t)

    _fields_ = [
        (DirectoryTag, 'tag'),
        (DirectoryType, 'type'),
        (pint.uint32_t, 'count'),
        (__value, 'value'),
        (__padding, 'padding'),
        (__pointer, 'pointer'),
    ]

class Directory(pstruct.type):
    def __next(self):
        p = self.parent and self.getparent(File, default=None)
        if p is None:
            return dyn.pointer(Directory, pint.uint32_t)
        return dyn.rpointer(Directory, p['header'], pint.uint32_t, byteorder=p['header'].Order())

    _fields_ = [
        (pint.uint16_t, 'count'),
        (lambda self: dyn.array(Entry, self['count'].li.int()), 'entry'),
        (__next, 'next')
    ]

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

    def enumerate(self):
        count = 0
        while True:
            for index, item in enumerate(self['entry']):
                yield count + index, item
            if not self['next'].int():
                break
            self, count = self['next'].d.li, count + self['count'].int()
        return

    def data(self):
        raise NotImplementedError

class File(pstruct.type):
    def __pointer(self):
        order = self['header'].li.Order()
        pointer = dyn.rpointer(Directory, self['header'], pint.uint32_t, byteorder=order)
        return dyn.clone(pointer, recurse={'byteorder': order})

    def __data(self):
        minimum = sum(self[fld].li.size() for fld in ['signature', 'header', 'pointer'])

        # if our source is bounded, then we can use it to determine
        # how many bytes are used for the data.
        if isinstance(self.source, ptypes.prov.bounded):
            size = self.source.size() - minimum

        # otherwise, we can't be sure what the size is we use 0.
        else:
            size = 0
        return dyn.block(max(0, size))

    _fields_ = [
        (dyn.clone(pstr.string, length=6), 'signature'),
        (tiff.Header, 'header'),
        (__pointer, 'pointer'),
        (__data, 'data'),
    ]
