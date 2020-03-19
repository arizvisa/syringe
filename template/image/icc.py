import ptypes
from ptypes import *

class uInt8Number( pint.bigendian(pint.uint8_t)): pass
class uInt16Number( pint.bigendian(pint.uint16_t)): pass
class uInt32Number( pint.bigendian(pint.uint32_t)): pass
class uInt64Number( pint.bigendian(pint.uint64_t)): pass

class s15Fixed16Number(pint.uint32_t): pass
class u16Fixed16Number(pint.uint32_t): pass
class u1Fixed15Number(pint.uint16_t): pass
class u8Fixed8Number(pint.uint16_t): pass

class dateTimeNumber(pstruct.type):
    _fields_ = [
        (uInt16Number, 'year'),
        (uInt16Number, 'month'),
        (uInt16Number, 'day'),
        (uInt16Number, 'hours'),
        (uInt16Number, 'minutes'),
        (uInt16Number, 'seconds'),
    ]

class response16Number(pstruct.type):
    _fields_ = [
        (uInt16Number, 'number'),
        (pint.uint16_t, 'reserved'),
        (s15Fixed16Number, 'measurement')
    ]

class XYZNumber(pstruct.type):
    _fields_ = [
        (s15Fixed16Number, 'CIE X'),
        (s15Fixed16Number, 'CIE Y'),
        (s15Fixed16Number, 'CIE Z'),
    ]

class ProfileHeader(pstruct.type):
    class __profile_version(pbinary.struct):
        _fields_= [(8, 'major'), (4, 'minor'), (4, 'bugfix'), (16, 'reserved')]

    class __profile_class(pint.enum, pint.uint32_t):
        _values_ = {
            'Input Device':0x73636e72,
            'Display Device':0x6d6e7472,
            'Output Device':0x70727472,
            'DeviceLink':0x6c696e6b,
            'ColorSpace Conversion':0x73706163,
            'Abstract':0x61627374,
            'Named colour':0x6e6d636c,
        }.items()

    class __colorspace(pint.enum, pint.uint32_t):
        _values_ = [
            ('XYZData', 0x58595A20),
            ('labData', 0x4C616220),
            ('luvData', 0x4C757620),
            ('YCbCrData', 0x59436272),
            ('YxyData', 0x59787920),
            ('rgbData', 0x52474220),
            ('grayData', 0x47524159),
            ('hsvData', 0x48535620),
            ('hlsData', 0x484C5320),
            ('cmykData', 0x434D594B),
            ('cmyData', 0x434D5920),
            ('2colourData', 0x32434C52),
            ('3colourData', 0x33434C52),
            ('4colourData', 0x34434C52),
            ('5colourData', 0x35434C52),
            ('6colourData', 0x36434C52),
            ('7colourData', 0x37434C52),
            ('8colourData', 0x38434C52),
            ('9colourData', 0x39434C52),
            ('10colourData', 0x41434C52),
            ('11colourData', 0x42434C52),
            ('12colourData', 0x43434C52),
            ('13colourData', 0x44434C52),
            ('14colourData', 0x45434C52),
            ('15colourData', 0x46434C52)
        ]

    class __platform(pint.enum, pint.uint32_t):
        _values_ = [
            ('Apple Computer, Inc', 0x4150504c),
            ('Microsoft Corporation', 0x4d534654),
            ('Silicon Graphics, Inc.', 0x53474920),
            ('Sun Microsystems, Inc.', 0x53554e57),
        ]

    class __profile_flags(pbinary.struct):
        _fields_ = [
            (1, 'Embedded'),
            (1, 'Profile cannot be used independantly from the embedded colour data'),
            (30, 'Reserved'),
        ]

    class __device_attributes(pbinary.struct):
        _fields_ = [
            (1, 'Transparent'),
            (1, 'Matte'),
            (1, 'Negative Polarity'),
            (1, 'Black and White media'),    # as opposed to color media
            (60, 'Reserved')
        ]

    class __rendering_intent(pint.enum, pint.uint32_t):
        _values_ = [
            ('Perceptual', 0),
            ('Media-Relative Colorimetric', 1),
            ('Saturation', 2),
            ('ICC-Absolute Colorimetric', 3)
        ]

    _fields_ = [
        (uInt32Number, 'Profile size'),
        (dyn.block(4), 'Preferred CMM Type'),
        (__profile_version, 'Profile version'),
        (__profile_class, 'Profile/Device Class'),
        (__colorspace, 'Colour space of data'),
        (__colorspace, 'Profile Connection Space'),
        (dateTimeNumber, 'Date and time this profile was first created'),
        (dyn.block(4), 'Profile file signature'),
        (__platform, 'Primary Platform signature'),
        (__profile_flags, 'Profile flags'),
        (dyn.block(4), 'Device manufactureer'),
        (dyn.block(4), 'Device model'),
        (__device_attributes, 'Device attributes'),
        (dyn.block(4), 'Rendering Intent'),
        (XYZNumber, 'Profile Connection Space Illuminant'),
        (dyn.block(4), 'Profile creator'),
        (dyn.block(16), 'Profile ID'),      # md5 checksum
        (dyn.block(28), 'reserved'),
    ]

class TagStruct(object): pass

class TagEntry(pstruct.type):
    _fields_ = [
        (dyn.block(4), 'signature'),
        (uInt32Number, 'offset'),   # relative to the beginning of the profile header (byte 0 by default)
        (uInt32Number, 'size')
    ]

class ProfileFile(pstruct.type):
    _fields_ = [
        (ProfileHeader, 'header'),
        (uInt32Number, 'count'),
        (lambda s: dyn.array(TagEntry, int(s['count'].li)), 'tags')
    ]


def verify_bitsize(integertype, bitsize):
    from ptypes import bitmap
    class verifiedtype(integertype):
        def load(self):
            res = super(verifiedtype, self).load()
            self.__verify()
            return res

        def alloc(self):
            res = super(verifiedtype, self).alloc(source)
            self.__verify()
            return res

        def __verify(self):
            n = int(self)
            if bitmap.fit(n) > bitsize:
                print('|warning| %x is larger than %d bits. using 1 instead.'% (n, bitsize))
                self.set(1)

    verifiedtype.__name__ = integertype.__name__
    return verifiedtype

### Tag Structures
class DevStruct(pstruct.type, TagStruct):
    signature = 'devs'
    _fields_ = [
        (verify_bitsize(uInt32Number, 8), 'NumOfPlatforms'),
        (lambda s: dyn.array(PlatStruct, int(s['NumOfPlatforms'].li)), 'PlatformArray')
    ]

class PlatStruct(pstruct.type):
    _fields_ = [
        (dyn.block(4), 'PlatformId'),
        (verify_bitsize(uInt32Number, 8), 'CombCount'),
        (uInt32Number, 'PlatformSize'),
        (lambda s: dyn.array(CombStruct, int(s['CombCount'].li)), 'CombArray')
    ]

class CombStruct(pstruct.type):
    _fields_ = [
        (uInt32Number, 'SetCount'),
        (verify_bitsize(uInt32Number, 8), 'CombSize'),
        (lambda s: dyn.array(SetStruct, int(s['SetCount'].li)), 'SetArray')
    ]

class SetStruct(pstruct.type):
    _fields_ = [
        (dyn.block(4), 'SettingSig'),
        (uInt32Number, 'SettingSize'),
        (verify_bitsize(uInt32Number, 8), 'numSettings'),
        (lambda s: dyn.array(uInt32Number, int(s['numSettings'].li)), 'Setting')
    ]

class TextDescStruct(pstruct.type, TagStruct):
    signature = 'desc'

    _fields_ = [
        (pstr.szstring, 'IsoStr'),
        (uInt32Number, 'UniLangCode'),
        (pstr.szwstring, 'UniStr'),
        (uInt16Number, 'MacScriptCode'),
        (uInt8Number, 'MacCount'),
        (dyn.clone(pstr.string, length=67), 'MacStr')
    ]

if __name__ == '__main__':
    import ptypes
    from ptypes import *

    ptypes.setsource( provider.file('./poc.pf') )
    self = ProfileFile()
#    print(self.l)
    self.l

    z = ptype.debugrecurse(DevStruct)()
    z.setoffset(self['tags'][0]['offset'].__int__())
