import ptypes
from ptypes import *

class __mixin(object):
    def summary(self):
        n,s = self.int(),self.blocksize()
        fmt = '0x%%0%dx (%%d)'% (s*2)
        return fmt % (n,n)

class code_t(ptype.type): pass

class slong(__mixin,pint.int64_t): pass
class ulong(__mixin,pint.uint64_t): pass
class sint(__mixin,pint.int32_t): pass
class uint(__mixin,pint.uint32_t): pass
class sshort(__mixin,pint.int16_t): pass
class ushort(__mixin,pint.uint16_t): pass
class schar(__mixin,pint.int8_t): pass
class uchar(__mixin,pint.uint8_t): pass
class unused(ptype.block):
    def summary(self):
        result = reduce(lambda a,b:a+ord(b), self.serialize(), 0)
        if result == 0:
            return '[...empty...]'
        return '[...NOT-empty...]'
block = dyn.block

class string(pstr.string):
    def summary(self):
        return '"%s"'%self.str().strip()

class wstring(pstr.wstring):
    class _object_(pstr.wchar_t):
        length = 2

        def set(self, value):
            self.value = '\x00' + value
            return self

        def get(self):
            return self.value[1]

    def summary(self):
        return '"%s"'%self.str().strip()

    def str(self):
        return ''.join(x.get() for x in self)

class __mixin(object):
    def summary(self):
        l,r=self['little'].int(),self['big'].int()
        s = self['little'].blocksize()*2
        if l == r:
            fmt = '0x%%0%dx (%%d)'% s
            return fmt % (l,l)

        fmt = '0x%%0%dx <error-diff:0x%%0%dx>'% (s,s)
        return fmt % (l,r)

class dual_ushort(__mixin,pstruct.type):
    _fields_ = [(pint.littleendian(ushort),'little'),(pint.bigendian(ushort),'big')]
class dual_uint(__mixin,pstruct.type):
    _fields_ = [(pint.littleendian(uint),'little'),(pint.bigendian(uint),'big')]

class stringinteger(pstr.string):
    def int(self):
        if len(self.str()) > 0:
            return int(self.str())
        return 0
    def __int__(self):
        return self.int()
    def summary(self):
        return str(self.int())

class sector(unused):
    length = 2048
    def is_empty(self):
        return reduce(lambda x,y:x+ord(y), self.value, 0) == 0

class sectorpointer(ptype.opointer_t):
    _type_ = uint
    def _calculate_(self, sectornumber):
        offset = sectornumber*sector.length
        return offset

def pointer(object):
    return dyn.clone(sectorpointer, _target_=object)

class iso_date(pstruct.type):
    _fields_ = [
        (dyn.clone(stringinteger, length=4), 'year'),
        (dyn.clone(stringinteger, length=2), 'month'),
        (dyn.clone(stringinteger, length=2), 'day'),
        (dyn.clone(stringinteger, length=2), 'hour'),
        (dyn.clone(stringinteger, length=2), 'minute'),
        (dyn.clone(stringinteger, length=2), 'second'),
        (dyn.clone(stringinteger, length=2), 'hundredth'),
        (schar, 'gmtoffset'),
    ]

    def summary(self):
        year,month,day=self['year'].int(),self['month'].int(),self['day'].int()
        hour,minute,second=self['hour'].int(),self['minute'].int(),self['second'].int()
        hundredth=self['hundredth'].int()
        gmtoffset = self['gmtoffset'].int()
        gmt = ('+%d'%gmtoffset) if gmtoffset > 0 else repr(gmtoffset)
        return '[%d-%d-%d %d:%02d:%02d.%02d GMT:%s]'%(year,month,day,hour,minute,second,hundredth,gmt)

class iso_path(pstruct.type):
    '''directory structure'''
    _fields_ = [
        (uchar, 'length'),
        (uchar, 'ext_length'),
        (uint, 'first_sector'),
        (ushort, 'parent'),
        (lambda s: dyn.clone(string,length=s['length'].int()-8), 'identifier'),
        (dyn.align(2), 'padding'),
    ]

class iso_directory_record(pstruct.type):
    class date(pstruct.type):
        _fields_ = [
            (uchar, 'year'),
            (uchar, 'month'),
            (uchar, 'day'),
            (uchar, 'hour'),
            (uchar, 'minute'),
            (uchar, 'second'),
            (schar, 'gmtoffset'),
        ]
        def summary(self):
            year,month,day=self['year'].int()+1900,self['month'].int(),self['day'].int()
            hour,minute,second=self['hour'].int(),self['minute'].int(),self['second'].int()
            gmtoffset = self['gmtoffset'].int()
            gmt = ('+%d'%gmtoffset) if gmtoffset > 0 else repr(gmtoffset)
            return '[%d-%d-%d %d:%02d:%02d GMT:%s]'%(year,month,day,hour,minute,second,gmt)

    class __flags(pbinary.struct):
        _fields_ = [
            (1,'multi-extent'),
            (2,'unused'),
            (1,'protection'),
            (1,'recordformat'),
            (1,'associated'),
            (1,'directory'),
            (1,'existence'),
        ]

    _fields_ = [
        (uchar, 'length'),
        (uchar, 'ext_attr_length'),
        (dual_uint, 'extent'),
        (dual_uint, 'size'),
        (date, 'date'),
        (__flags, 'flags'),
        (uchar, 'file_unit_size'),
        (uchar, 'interleave'),
        (dual_ushort, 'volume_sequence_number'),
        (uchar, 'name_len'),
        (lambda s: dyn.clone(string, length=s['name_len'].li.int()), 'name'),
        (dyn.align(2), 'padding'),
    ]

#/* can't take sizeof(iso_directory_record), because of possible alignment
#   of the last entry (34 instead of 33) */
#define ISO_DIRECTORY_RECORD_SIZE       33

class iso_volume_descriptor(pstruct.type):
    def __data(self):
        res = self['type'].li.int()
        return volume_descriptor.withdefault(res, type=res)

    _fields_ = [
        (uchar, 'type'),
        (dyn.clone(string,length=5), 'id'),
        (uchar, 'version'),
        (__data, 'data'),
    ]

class volume_descriptor(ptype.definition):
    cache = {}

    class unknown(unused):
        length = 2041

    class array(parray.terminated):
        _object_ = iso_volume_descriptor

        def isTerminator(self, value):
            return value['type'].int() == 0xff

@volume_descriptor.define
class iso_volume_descriptor_terminator(unused):
    type = 0xff
    length = 2041

@volume_descriptor.define
class iso_primary_descriptor(pstruct.type):
    type = 1
    _fields_ = [
        (uchar, 'unused1'),
        (dyn.clone(string,length=32), 'system_id'),
        (dyn.clone(string,length=32), 'volume_id'),
        (dyn.clone(unused,length=8), 'unused2'),
        (dual_uint, 'volume_space_size'),
        (dyn.clone(unused,length=32), 'unused3'),
        (dual_ushort, 'volume_set_size'),
        (dual_ushort, 'volume_sequence_number'),
        (dual_ushort, 'logical_block_size'),
        (dual_uint, 'path_table_size'),
        (uint, 'type_l_path_table'),
        (uint, 'opt_type_l_path_table'),
        (uint, 'type_m_path_table'),
        (uint, 'opt_type_m_path_table'),
        (iso_directory_record, 'root_directory_record'),
        (dyn.clone(string,length=128), 'volume_set_id'),
        (dyn.clone(string,length=128), 'publisher_id'),
        (dyn.clone(string,length=128), 'preparer_id'),
        (dyn.clone(string,length=128), 'application_id'),
        (dyn.clone(string,length=37), 'copyright_file_id'),
        (dyn.clone(string,length=37), 'abstract_file_id'),
        (dyn.clone(string,length=37), 'bibliographic_file_id'),
        (iso_date, 'creation_date'),
        (iso_date, 'modification_date'),
        (iso_date, 'expiration_date'),
        (iso_date, 'effective_date'),
        (uchar, 'file_structure_version'),
        (uchar, 'unused4'),
        (dyn.clone(unused, length=512), 'application_data'),
        (dyn.clone(unused,length=653), 'unused5'),
    ]

@volume_descriptor.define
class iso_boot_record(pstruct.type):
    type = 0
    _fields_ = [
        (dyn.clone(string,length=32), 'system_id'),
        (dyn.clone(unused,length=32), 'boot_id'),
        (pointer(dyn.clone(code_t,mode=16, length=2048)), 'boot_catalog'),
        (dyn.clone(unused,length=1973), 'unused2'),
    ]

@volume_descriptor.define
class iso_supplementary_descriptor(pstruct.type):
    type = 2
    _fields_ = [
        (uchar, 'flags'),
        (dyn.clone(wstring,length=16), 'system_id'),
        (dyn.clone(wstring,length=16), 'volume_id'),
        (block(8), 'unused2'),
        (dual_uint, 'volume_space_size'),
        (block(32), 'escape'),
        (uint, 'volume_set_size'),
        (dual_ushort, 'volume_sequence_number'),
        (uint, 'logical_block_size'),
        (dual_uint, 'path_table_size'),
        (uint, 'type_l_path_table'),
        (uint, 'opt_type_l_path_table'),
        (uint, 'type_m_path_table'),
        (uint, 'opt_type_m_path_table'),
        (iso_directory_record, 'root_directory_record'),
        (dyn.clone(string,length=128), 'volume_set_id'),
        (dyn.clone(string,length=128), 'publisher_id'),
        (dyn.clone(string,length=128), 'preparer_id'),
        (dyn.clone(string,length=128), 'application_id'),
        (dyn.clone(string,length=37), 'copyright_file_id'),
        (dyn.clone(string,length=37), 'abstract_file_id'),
        (dyn.clone(string,length=37), 'bibliographic_file_id'),
        (iso_date, 'creation_date'),
        (iso_date, 'modification_date'),
        (iso_date, 'expiration_date'),
        (iso_date, 'effective_date'),
        (uchar, 'file_structure_version'),
        (uchar, 'unused4'),
        (dyn.clone(unused,length=512), 'application_data'),
        (dyn.clone(unused,length=653), 'unused5'),
    ]

@volume_descriptor.define
class iso_volume_partition(pstruct.type):
    type = 3
    _fields_ = [
        (uchar, 'unused'),
        (dyn.clone(string,length=32), 'system_id'),
        (dyn.clone(string,length=32), 'partition_id'),
        (dual_uint, 'partition_location'),
        (dual_uint, 'partition_size'),
        (dyn.clone(unused,length=1960), 'partition_size'),
    ]

if False:
    class iso_sierra_primary_descriptor(pstruct.type):
        _fields_ = [
            (uchar, 'unused1'),
            (block(32), 'system_id'),
            (block(32), 'volume_id'),
            (dyn.clone(unused,length=8), 'unused2'),
            (dual_uint, 'volume_space_size'),
            (dyn.clone(unused,length=32), 'unused3'),
            (uint, 'volume_set_size'),
            (dual_ushort, 'volume_sequence_number'),
            (uint, 'logical_block_size'),
            (dual_uint, 'path_table_size'),
            (uint, 'type_l_path_table'),
            (uint, 'opt_type_l_path_table'),
            (uint, 'unknown2'),
            (uint, 'unknown3'),
            (uint, 'type_m_path_table'),
            (uint, 'opt_type_m_path_table'),
            (uint, 'unknown4'),
            (uint, 'unknown5'),
    #        (block(34), 'root_directory_record'),
            (iso_directory_record, 'root_directory_record'),
            (dyn.clone(string,length=128), 'volume_set_id'),
            (dyn.clone(string,length=128), 'publisher_id'),
            (dyn.clone(string,length=128), 'preparer_id'),
            (dyn.clone(string,length=128), 'application_id'),
            (dyn.clone(string,length=64), 'copyright_id'),
            (block(16), 'creation_date'),
            (block(16), 'modification_date'),
            (block(16), 'expiration_date'),
            (block(16), 'effective_date'),
            (uchar, 'file_structure_version'),
            (dyn.clone(unused,length=1193), 'unused4'),
        ]

class iso_extended_attributes(pstruct.type):
    _fields_ = [
        (uint, 'owner'),
        (uint, 'group'),
        (ushort, 'perm'),
        (iso_date, 'ctime'),
        (iso_date, 'mtime'),
        (iso_date, 'xtime'),
        (iso_date, 'ftime'),
        (uchar, 'recfmt'),
        (uchar, 'recattr'),
        (uint, 'reclen'),
        (dyn.clone(string,length=32), 'system_id'),
        (block(64), 'system_use'),
        (uchar, 'version'),
        (uchar, 'len_esc'),
        (block(64), 'reserved'),
        (uint, 'len_au'),
    ]

class File(pstruct.type):
    _fields_ = [
        (dyn.array(sector, 16), 'unused'),
        (volume_descriptor.array, 'desc'),
    ]

class section_validation_entry(pstruct.type):
    _fields_ = [
        (uchar, 'header_id'),
        (uchar, 'platform_id'),
        (ushort, 'resered'),
        (dyn.clone(string, length=24), 'manufacturer_id'),
        (ushort, 'checksum'),
        (ushort, 'key'),
    ]

class section_initial_entry(pstruct.type):
    _fields_ = [
        (uchar, 'boot_indicator'),
        (uchar, 'media_type'),
        (ushort, 'load_segment'),
        (uchar, 'system_type'),
        (uchar, 'unused'),
        (ushort, 'sector_count'),
        (uint, 'load_rba'),
        (uchar,'unused2'),
    ]

class section_header_entry(pstruct.type):
    _fields_ = [
        (uchar, 'indicator'),
        (uchar, 'platform_id'),
        (ushort, 'section_count'),
        (dyn.clone(string, length=28), 'id_string'),
    ]

class section_entry(pstruct.type):
    _fields_ = [
        (uchar, 'indicator'),
        (uchar, 'media_type'),
        (ushort, 'load_segment'),
        (uchar, 'system_type'),
        (uchar, 'unused'),
        (ushort, 'sector_count'),
        (uint, 'load_rba'),
        (uchar, 'selection_criteria'),
        (dyn.block(19), 'vendor_criteria'),
    ]

class section_entry_extension(pstruct.type):
    class __field(pbinary.struct):
        _fields_ = [(4,'unused'),(1,'record_follows'),(2,'unused2'),(1,'wtf')]

    _fields_ = [
        (uchar, 'indicator'),
        (uchar, 'field'),
        (dyn.block(30), 'vendor_criteria'),
    ]

if __name__ == '__main__':
    import ptypes,iso9660
    reload(iso9660)
    reload(ptypes.provider)
    ptypes.setsource(ptypes.provider.WindowsFile('~/downloads/6euj41uc.iso', 'r'))

    z = iso9660.File()
    z = z.l
    boot_sector = z['desc'][1]['data']['boot_catalog']
    if False:
        a = iso9660.sector(offset=boot_sector*2048).l
        print a.cast(iso9660.section_validation_entry)
        #    print z['iso']
        #    print [x for x in z['unused'] if not x.is_empty()]
        #    date = z['primary']['root_directory_record']['date']
        #    print date
        #    print date['year'].summary()

        a = z['desc'][1]['data']['boot_catalog']
        print a.cast(iso9660.sectorpointer)

    if False:
        #    x = iso_volume_descriptor()
        #    x = block(32768)()
        #    print x.l.hexdump()
        #    x = iso_volume_descriptor(source=ptypes.file('~/downloads/6euj41uc.iso', 'r'))
        #    x.setoffset(32768)
        #    print x.l
        #    print iso_volume_descriptor().a.size()
        #
        #    print z['desc'][0]

        p = z['primary']
        print p
        x = p['type_l_path_table']
        print x
        x = iso9660.pointer(iso9660.sector)()
        x.set(0x16)
        print x.d.l.hexdump()

        a = iso9660.sector(offset=p.getoffset()+p.size())
        print a.l
        print a.cast(iso9660.iso_volume_descriptor)
        x = a
        x = iso9660.sector(offset=x.getoffset()+x.size())
        print x.l.cast(iso9660.iso_volume_descriptor)
        print x.l
