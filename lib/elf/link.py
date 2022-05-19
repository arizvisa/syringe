import ptypes
from .base import *

from . import dynamic, File

class RT_(pint.enum):
    _values_ = [
        ('CONSISTENT', 0),
        ('ADD', 1),
        ('DELETE', 2),
    ]

class r_debug32(pstruct.type):
    attributes = {'ElfXX_Addr': Elf32_Addr}
    class r_state(RT_, Elf32_Word):
        pass
    def __r_map(self):
        return dyn.clone(Elf32_Addr, _object_=link_map)
    _fields_ = [
        (pint.int32_t, 'version'),
        (__r_map, 'r_map'),
        (Elf32_Addr, 'r_brk'),
        (r_state, 'r_state'),
        (Elf32_Addr, 'r_ldbase'), # elf.File
    ]

class r_debug64(pstruct.type):
    attributes = {'ElfXX_Addr': Elf64_Addr}
    class r_state(RT_, Elf64_Word):
        pass
    def __r_map(self):
        return dyn.clone(Elf64_Addr, _object_=link_map)
    _fields_ = [
        (pint.int32_t, 'version'),
        (dyn.align(8), 'align(version)'),
        (__r_map, 'r_map'),
        (Elf64_Addr, 'r_brk'),
        (r_state, 'r_state'),
        (dyn.align(8), 'align(r_state)'),
        (Elf64_Addr, 'r_ldbase'), # elf.File
    ]

### link_map types
class Lmid_t(long_int):
    pass

class libname_list(pstruct.type):
    _fields_ = [
        (dyn.clone(void_star, _object_=pstr.szstring), 'name'),
        (lambda self: dyn.clone(void_star, _object_=self.__class__), 'next'),
        (int, 'dont_free'),
    ]

class r_scope_elem(pstruct.type):
    def __r_list(self):
        def items(_, self=self):
            count = self['r_nlist'].li
            return dyn.array(link_map, count.int())
        return dyn.clone(void_star, _object_=items)
    _fields_ = [
        (__r_list, 'r_list'),
        (unsigned_int, 'r_nlist'),
    ]

class r_found_version(pstruct.type):
    _fields_ = [
        (dyn.clone(void_star, _object_=pstr.szstring), 'name'),
        (ElfXX_Word, 'hash'),
        (int, 'hidden'),
        (dyn.clone(void_star, _object_=pstr.szstring), 'filename'),
    ]

class r_dir_status(pint.enum, int):
    _values_ = [
        ('unknown', 0),
        ('nonexisting', 1),
        ('existing', 2),
    ]

class r_search_path_elem(pstruct.type):
    _fields_ = [
        (lambda self: dyn.clone(self.void_star, _object_=self.__class__), 'next'),
        (dyn.clone(void_star, _object_=pstr.szstring), 'what'),
        (dyn.clone(void_star, _object_=pstr.szstring), 'where'),
        (dyn.clone(void_star, _object_=pstr.szstring), 'dirname'),
        (size_t, 'dirnamelen'),
        (dyn.array(r_dir_status, 1), 'status'),
    ]

class r_search_path_struct(pstruct.type):
    def __dirs(self):
        t = lambda s: dyn.array(r_search_path_elem, self['malloced'].li.int())
        return dyn.clone(void_star, _object_=t)
    _fields_ = [
        (__dirs, 'dirs'),
        (int, 'malloced'),
    ]

class reloc_result(pstruct.type):
    def __bound(self):
        return dyn.clone(void_star, _object_=link_map)
    _fields_ = [
        (ElfXX_Addr, 'addr'),
        (__bound, 'bound'),
        (unsigned_int, 'boundndx'),
        (pint.uint32_t, 'enterexit'),
        (unsigned_int, 'flags'),
        (unsigned_int, 'init'),
    ]

#class r_file_id(pstruct.type):
#    _fields_ = [
#        (dev_t, 'dev'),
#        (ino64_t, 'ino'),
#    ]

class link_map_reldeps(pstruct.type):
    def __list(self):
        t = dyn.array(link_map, 0)
        return dyn.clone(void_star, _object_=t)
    _fields_ = [
        (unsigned_int, 'act'),
        (__list, 'list'),
    ]

class link_map(pstruct.type):
    class _l_info(parray.type):
        DT_NUM = 35
        DT_THISPROCNUM = 0      # architecture-specific
        DT_VERSIONTAGNUM = 16
        DT_EXTRANUM = 3
        DT_VALNUM = 12
        DT_ADDRNUM = 11
        length = DT_NUM + DT_THISPROCNUM + DT_VERSIONTAGNUM + DT_EXTRANUM + DT_VALNUM + DT_ADDRNUM

        DT_ADDRRNGHI = 0x6ffffeff
        DT_GNU_HASH = 0x6ffffef5

        @classmethod
        def DT_ADDRTAGIDX(cls, tag):
            '''DT_ADDRTAGIDX = lambda tag: DT_ADDRRNGHI - tag'''
            return cls.DT_ADDRRNGHI - tag
        @classmethod
        def ADDRIDX(cls, tag):
            '''ADDRIDX = lambda tag: DT_NUM + DT_THISPROCNUM + DT_VERSIONTAGNUM + DT_EXTRANUM + DT_VALNUM + DT_ADDRTAGIDX(tag)'''
            properties = ['DT_NUM', 'DT_THISPROCNUM', 'DT_VERSIONTAGNUM', 'DT_EXTRANUM', 'DT_VALNUM']
            result = sum(getattr(cls, name) for name in properties)
            return result + cls.DT_ADDRTAGIDX(tag)

    class _l_gnuhash_table(pstruct.type):
        _fields_ = [
            (dyn.clone(void_star, _object_=dyn.array(Elf32_Word, 0)), 'l_gnu_chain_zero'),
            (dyn.clone(void_star, _object_=dyn.array(Elf_Symndx, 0)), 'l_buckets'),
        ]

    class _l_hash_table(pstruct.type):
        _fields_ = [
            (dyn.clone(void_star, _object_=dyn.array(Elf32_Word, 0)), 'l_gnu_buckets'),
            (dyn.clone(void_star, _object_=dyn.array(Elf_Symndx, 0)), 'l_chain'),
        ]

    def __l_hash_table(self):
        l_info = self['l_info'].li
        ELF_MACHINE_GNU_HASH_ADDRIDX = l_info.ADDRIDX(l_info.DT_GNU_HASH)
        if l_info[ELF_MACHINE_GNU_HASH_ADDRIDX] == None:
            return self._l_gnuhash_table
        return self._l_hash_table

    @pbinary.littleendian
    class _l_flags(pbinary.flags):
        class _l_type(pbinary.enum):
            length, _values_ = 2, [
                ('lt_executable', 0),
                ('lt_library', 1),
                ('lt_loaded', 2),
            ]
        _fields_ = [
            (_l_type, 'l_type'),
            (1, 'l_relocated'),
            (1, 'l_init_called'),
            (1, 'l_global'),
            (2, 'l_reserved'),
            (1, 'l_phdr_allocated'),

            (1, 'l_soname_added'),
            (1, 'l_faked'),
            (1, 'l_need_tls_init'),
            (1, 'l_auditing'),
            (1, 'l_audit_any_plt'),
            (1, 'l_removed'),
            (1, 'l_contiguous'),
            (1, 'l_symbolic_in_local_scope'),

            (1, 'l_free_initfini'),
            (lambda self: 32 - 2 - sum(bits for bits, _ in self._fields_[1:-1]), 'padding'),
        ]

    class _l_x86(pstruct.type):
        class _l_property(pbinary.enum):
            length, _values_ = 2, [
                ('unknown', 0),
                ('none', 1),
                ('valid', 2),
            ]
        _fields_ = [
            (_l_property, 'l_property'),
            (lambda self: dyn.block(4 - self['l_property'].li.size()), 'padding(l_property)'),
            (unsigned_int, 'l_x86_feature_1_and'),
            (unsigned_int, 'l_x86_isa_1_needed'),
        ]

    def __init__(self, **attrs):
        super(link_map, self).__init__(**attrs)
        self._fields_ = F = []

        ElfXX_Addr = self.ElfXX_Addr
        ElfXX_Dyn = dynamic.Elf32_Dyn if ElfXX_Addr is Elf32_Addr else dynamic.Elf64_Dyn
        star = ElfXX_Addr._value_

        F.extend([
            (dyn.clone(ElfXX_Addr, _object_=File), 'l_addr'),
            (dyn.pointer(pstr.szstring, star), 'l_name'),
            (dyn.pointer(ElfXX_Dyn, star), 'l_ld'),
            (dyn.pointer(self.__class__, star), 'l_next'),
            (dyn.pointer(self.__class__, star), 'l_prev'),
        ])
        return

        # All following members are internal to the dynamic linker.
        # They may change without notice.
        F.extend([
            (Lmid_t, 'l_ns'),
            (dyn.clone(void_star, _object_=libname_list), 'l_libname'),
            (dyn.clone(self._l_info, _object_=ElfXX_Dyn), 'l_info'),
            (dyn.clone(void_star, _object_=lambda _: dyn.array(ElfXX_Phdr, self['l_phnum'].int())), 'l_phdr'),
            (ElfXX_Addr, 'l_entry'),
            (ElfXX_Half, 'l_phnum'),
            (ElfXX_Half, 'l_ldnum'),
        ])

        F.extend([
            (r_scope_elem, 'l_searchlist'),
            (r_scope_elem, 'l_symbolic_searchlist'),
            (dyn.clone(void_star, _object_=self.__class__), 'l_loader'),
            (dyn.clone(void_star, _object_=lambda _: dyn.array(r_found_version, self['l_nversions'].li.int())), 'l_versions'),
            (unsigned_int, 'l_nversions'),
        ])

        F.extend([
            (Elf_Symndx, 'l_nbuckets'),
            (Elf32_Word, 'l_gnu_bitmask_idxbits'),
            (Elf32_Word, 'l_gnu_shift'),
            (dyn.clone(void_star, _object_=ElfXX_Addr), 'l_gnu_bitmask'),
            (self.__l_hash_table, 'l_hash_table'),
        ])

        F.extend([
            (unsigned_int, 'l_direct_opencount'),
            (self._l_flags, 'l_flags'),
            (bool, 'l_nodelete_active'),
            (bool, 'l_nodelete_pending'),
        ])

        if 'x86':
            F.append((self._l_x86, 'l_x86')),

        F.extend([
            (r_search_path_struct, 'l_rpath_dirs'),
            (dyn.clone(void_star, _object_=reloc_result), 'l_reloc_result'),
            (dyn.clone(void_star, _object_=ElfXX_Versym), 'l_versyms'),
            (dyn.clone(void_star, _object_=pstr.szstring), 'l_origin'),
            (ElfXX_Addr, 'l_map_start'),
            (ElfXX_Addr, 'l_map_end'),
            (ElfXX_Addr, 'l_text_end'),
        ])

        F.extend([
            (dyn.array(dyn.clone(void_star, _object_=r_scope_elem), 4), 'l_scope_mem'),
            (size_t, 'l_scope_max'),
            (lambda self: dyn.clone(void_star, _object_=dyn.array(r_scope_elem, self['l_scope_max'].li.int())), 'l_scope'),
            (dyn.array(dyn.clone(void_star, _object_=r_scope_elem), 2), 'l_local_scope'),
            #(r_file_id, 'l_file_id'),  # posix-only
            (r_search_path_struct, 'l_runpath_dirs'),
        ])

    def __iterate__(self, field):
        yield self
        while self[field].int():
            self = self[field].d
            yield self.l
        return
    def iterate(self, field='l_next'):
        for item in self.__iterate__(field):
            yield item
        return
    def enumerate(self, field='l_next'):
        for index, item in enumerate(self.iterate()):
            yield index, item
        return

class link_map32(link_map):
    ElfXX_Addr = Elf32_Addr
class link_map64(link_map):
    ElfXX_Addr = Elf64_Addr

# just some aliases
map, map32, map64 = link_map, link_map32, link_map64
