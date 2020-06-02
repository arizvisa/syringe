import functools, itertools, types, builtins, operator, six
import ptypes, elf
from . import store

class Shdr(store.Section):
    def __hash__(self):
        hdr = self._shdr
        items = (self.__section_name, self.bounds, hdr['sh_type'].int, hdr['sh_flags'].int)
        iterable = (item() for item in items)
        return functools.reduce(operator.xor, map(hash, iterable))

    def __eq__(self, other):
        if not isinstance(other, Shdr):
            return False
        nameEQ = self.name() == other.name()
        boundsEQ = self.bounds() == other.bounds()
        typeEQ = self._shdr['sh_type'].int() == other._shdr['sh_type'].int()
        flagsEQ = self._shdr['sh_flags'].int() == other._shdr['sh_flags'].int()
        return self._shdr.source is other._shdr.source and nameEQ and boundsEQ and typeEQ and flagsEQ

    def __ne__(self, other):
        return isinstance(other, Shdr) and super(Shdr, self).__ne__(other)

    def __init__(self, sh):
        header = sh.getparent(elf.base.ElfXX_Ehdr)
        sheaders = header['e_shoff'].d
        pheaders = header['e_phoff'].d

        # Grab our segment index for symbols to look us up
        idx = sheaders.value.index(sh)

        # Get the Phdr that our section is contained in
        try:
            phdr = pheaders.byaddress(sh['sh_addr'].int())

        except ptypes.error.InstanceNotFoundError:
            phdr = None

        # Grab the strtab that our section will use
        t, res = 'SHT_STRTAB', header['e_shstrndx'].int()
        shdr_strtab = sheaders[res]
        if not shdr_strtab['sh_type'][t]:
            raise LookupError("Section {:d} is of an incorrect type: {!s} <> {!s}".format(res, "{:s}({:#x})".format(t, elf.section.SHT_.byname('SHT_STRTAB')), shdr_strtab['sh_type'].summary()))

        # Assign all of our properties
        self._index = idx
        self._shdr = sh
        self._sections = sheaders
        self._phdr = phdr
        self._shstrtab = shdr_strtab['sh_offset'].d.li

    def name(self):
        return self._index

    def bounds(self):
        shdr = self._shdr
        res = shdr['sh_addr'].int()
        return res, res + shdr.getloadedsize()

    def __section_name(self):
        shdr, strtab = self._shdr, self._shstrtab
        res = strtab.field(shdr['sh_name'].int())
        return res.str()

    def __repr__(self):
        cls = self.__class__
        return "{!s} {:s} ({:d}) {:#x}{:+x}".format(cls, self.__section_name(), self.name(), *self.bounds())

class Phdr(store.Segment):
    def __hash__(self):
        hdr = self._phdr
        items = (hdr['p_type'].int, hdr['p_flags'].int, self.offset, self.length)
        iterable = (item() for item in items)
        return functools.reduce(operator.xor, map(hash, iterable))

    def __eq__(self, other):
        if not isinstance(other, Phdr):
            return False
        typeEQ = self._phdr['p_type'].int() == other._phdr['p_type'].int()
        offsetEQ = self.offset() == other.offset()
        lengthEQ = self.length() == other.length()
        return self._phdr.source is other._phdr.source and typeEQ and offsetEQ and lengthEQ

    def __ne__(self, other):
        return isinstance(other, Phdr) and super(Phdr, self).__ne__(other)

    def __init__(self, ph):
        self._phdr = ph

    def offset(self):
        phdr = self._phdr
        return phdr['p_vaddr'].int()

    def length(self):
        phdr = self._phdr
        return phdr.getloadedsize()

    def data(self):
        phdr = self._phdr
        res = phdr['p_vaddr'].d
        return bytearray(res.serialize())

    def protection(self):
        phdr = self._phdr
        res = { item for item in 'RWX' if phdr['p_flags'][item] }
        return store.Permissions(*res)

class Object(store.Store):
    def __init__(self, ehdr):
        self._ehdr = ehdr

        # grab the program headers and sections
        self._pheaders, self._sheaders = (ehdr[fld].d.li for fld in ['e_phoff', 'e_shoff'])

        # grab the symbol tables and pair them up with their sh_link and sh_info indices
        types = ['SHT_SYMTAB', 'SHT_DYNSYM']
        headers = (item for item in self._sheaders if any(item['sh_type'][t] for t in types))
        tables = ((item['sh_link'], item['sh_info'], item['sh_offset'].d.li) for item in headers)
        self._symtabs = [item for item in tables]

        # let the base class continue its initialization
        return super(Object, self).__init__()

    def segments(self):
        loadable = {'PT_LOAD', 'PT_DYNAMIC'}
        for item in self._pheaders:
            type = item['p_type']
            if any(type[f] for f in loadable):
                yield Phdr(item)
            continue
        return

    def sections(self):
        for item in self._sheaders:
            if item['sh_flags']['ALLOC']:
                yield Shdr(item)
            continue
        return

    def __iterate_symtabs__(self):
        for index, count, table in self._symtabs:
            shstrtab = self._sheaders[index.int()]
            strtab = shstrtab['sh_offset'].d.li
            for symbol in table:
                name = strtab.read(symbol['st_name'].int())
                yield name, symbol
            continue
        return

    def load_section(self, section):
        for name, sym in self.__iterate_symtabs__():
            if sym['st_shndx']['SHN_UNDEF']:
                continue

            if sym['st_shndx']['SHN_COMMON']:
                raise NotImplementedError

            index = sym['st_shndx'].int()
            if index != section.name():
                continue

            # Figure out information about the symbol such as its scope, and
            # then its type just so we include some metadata with our symbol
            # that gets added.

            sti, stv = (sym[fld] for fld in ['st_info', 'st_other'])
            sti_bind, sti_type = (sti.item(fld) for fld in ['ST_BIND', 'ST_TYPE'])

            if sti_bind['STB_LOCAL']:
                scope = store.Scope.Local
            elif sti_bind['STB_GLOBAL']:
                scope = store.Scope.Global
            elif sti_bind['STB_WEAK']:
                scope = store.Scope.External
            else:
                raise ValueError(sti_bind)

            # If we got a section symbol, then explicitly add that.
            if sti_type['STT_SECTION']:
                self.add_section(section, scope, sym)
                self._symbols.set(section, sym, sym['st_value'].int())
                continue

            # Otherwise, it's just a regular symbol and we can treat it normally
            self.add_symbol(name.str(), scope, section, sym)
            self._symbols.set(section, sym, sym['st_value'].int())
        return super(Object, self).load_section(section)

if __name__ == '__main__':
    import sys, os.path
    import ptypes, elf, linker
    from linker import store_elf, store
    import importlib
    store = importlib.reload(linker.store)
    #t = store.ScopeType('local')
    store_elf = importlib.reload(linker.store_elf)

    library_dir = os.path.dirname(__file__)
    #library_dir = os.path.join(os.getcwd())
    #library_dir = os.path.join(os.getcwd(), 'linker')
    #library_dir = os.path.join(os.getcwd(), 'lib', 'linker')
    samples_dir = os.path.join(library_dir, 'samples')
    ptypes.setsource(ptypes.prov.file(os.path.join(samples_dir, 'write.out'), 'rb'))
    #ptypes.setsource(ptypes.prov.file('/usr/lib64/libpython3.7m.so.1.0', 'rb'))

    z = elf.File().l
    z = z['e_data']

    if False:
        phl = z['e_phoff'].d.l
        self = store_elf.Phdr(phl[1])
        print(self.data())

    if False:
        shl = z['e_shoff'].d.l
        self = store_elf.Shdr(shl[1])

    if False:
        iterable = self.segments()
        seg = next(iterable)
        seg
        print(seg)
        iterable = self.sections()
        section = next(iterable)
        section
        print(section)

    self = store_elf.Object(z)
    res = self.load()

    if False:
        items = [item for _, item in self.__iterate_symtabs__()]
        for name, item in self.__iterate_symtabs__():
            if not len(name.str()):
                print(item)
    print(self._symbols['greeting'])
    print(self._symbols)
    self._symbols
    for item in self._sections:
        print(item.name())

    for item, sections in self._segments.items():
        print(item)
        for sec in sections:
            print(sec)
