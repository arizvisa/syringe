import logging, bisect, itertools, ptypes
from ptypes import ptype, pint, pstruct, parray

from . import base, segment, section, dynamic

### header types
EI_NIDENT = 16

class EV_(pint.enum):
    _values_ = [
        ('NONE', 0),
        ('CURRENT', 1),
    ]

class EI_MAG(ptype.block):
    length = 4

    def default(self):
        return self.set(b'\x7fELF')

    def valid(self):
        res = self.copy().default()
        return res.serialize() == self.serialize()

    def properties(self):
        res = super(EI_MAG, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

class EI_CLASS(pint.enum, base.uchar):
    _values_ = [
        ('ELFCLASSNONE', 0),
        ('ELFCLASS32', 1),
        ('ELFCLASS64', 2),
    ]

class EI_DATA(pint.enum, base.uchar):
    # FIXME: switch the byteorder of everything based on this value
    _values_ = [
        ('ELFDATANONE', 0),
        ('ELFDATA2LSB', 1),
        ('ELFDATA2MSB', 2),
    ]

    def order(self):
        if self['ELFDATA2LSB']:
            return ptypes.config.byteorder.littleendian
        elif self['ELFDATA2MSB']:
            return ptypes.config.byteorder.bigendian
        return ptypes.config.defaults.integer.order

class EI_VERSION(EV_, base.uchar):
    pass

class EI_OSABI(pint.enum, base.uchar):
    _values_ = [
        ('ELFOSABI_SYSV', 0),
        ('ELFOSABI_HPUX', 1),
        ('ELFOSABI_ARM_EABI', 64),
        ('ELFOSABI_STANDALONE', 255),
    ]

class EI_ABIVERSION(base.uchar):
    pass

class EI_PAD(ptype.block):
    length = EI_NIDENT - 9

class E_IDENT(pstruct.type):
    _fields_ = [
        (EI_MAG, 'EI_MAG'),
        (EI_CLASS, 'EI_CLASS'),
        (EI_DATA, 'EI_DATA'),
        (EI_VERSION, 'EI_VERSION'),
        (EI_OSABI, 'EI_OSABI'),
        (EI_ABIVERSION, 'EI_ABIVERSION'),
        (EI_PAD, 'EI_PAD'),
    ]

    def valid(self):
        return self.initializedQ() and self['EI_MAG'].valid()

    def properties(self):
        res = super(E_IDENT, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

### File types
class File(pstruct.type, base.ElfXX_File):
    def __e_data(self):
        e_ident = self['e_ident'].li

        # Figure out the EI_CLASS to determine the Ehdr size
        ei_class = e_ident['EI_CLASS']
        if ei_class['ELFCLASS32']:
            t = header.Elf32_Ehdr
        elif ei_class['ELFCLASS64']:
            t = header.Elf64_Ehdr
        else:
            raise NotImplementedError(ei_class)

        # Now we can clone it using the byteorder from EI_DATA
        ei_data = e_ident['EI_DATA']
        return ptype.clone(t, recurse={'byteorder': ei_data.order()})

    def __e_dataentries(self):
        data = self['e_data'].li
        if isinstance(self.source, ptypes.provider.memorybase):
            return ptype.clone(parray.type, _object_=segment.MemorySegmentData, length=0)

        # If we're using a file source, then we'll need to include both sections
        # _and_ segments. We'll also create some lookup dicts so that we can
        # identify which type is at a particular offset. This way we can give
        # the sections priority since we're dealing with files.
        sections, segments = data['e_shoff'].d, data['e_phoff'].d
        segmentlist = [phdr for _, phdr in segments.li.sorted()]
        sectionlist = [shdr for _, shdr in sections.li.sorted()]

        segmentlookup = {phdr['p_offset'].int() : phdr for phdr in segmentlist}
        segmentlookup.update({phdr['p_offset'].int() + phdr.getreadsize() : phdr for phdr in segmentlist if phdr.getreadsize() > 0})

        sectionlookup = {shdr['sh_offset'].int() : shdr for shdr in sectionlist}
        sectionlookup.update({shdr['sh_offset'].int() + shdr.getreadsize() : shdr for shdr in sectionlist if shdr.getreadsize() > 0})

        # Now we need to sort both of them into a single list so we can figure
        # out the layout of this executable. To do this, we're just going to
        # create a list of the offset of each boundary. This way we can use
        # our lookup tables to figure out which type is the right one.
        layout = []
        for phdr in segmentlist:
            offset = phdr['p_offset'].int()
            bisect.insort(layout, offset)
            bisect.insort(layout, offset + phdr.getreadsize())

        for shdr in sectionlist:
            offset = shdr['sh_offset'].int()
            bisect.insort(layout, offset)
            bisect.insort(layout, offset + shdr.getreadsize())

        # Our layout contains the boundaries of all of our sections, so now
        # we need to walk our layout and determine whether there's a section
        # or a segment at that particular address.

        # FIXME: we need to filter out segments here if we found a section that
        #        is contained within it.
        sorted, used = [], {item for item in []}
        for boundary, _ in itertools.groupby(layout):
            item = sectionlookup.get(boundary, segmentlookup.get(boundary, None))
            if item is None or item in used:
                continue
            sorted.append(item)
            used.add(item)

        # Figure out which types we need to use depending on the source
        if isinstance(self.source, ptypes.provider.memorybase):
            section_t, segment_t = section.SectionData, segment.MemorySegmentData
        else:
            section_t, segment_t = section.SectionData, segment.FileSegmentData

        # Everything has been sorted, so now we can construct our array and
        # align it properly to load as many contiguous pieces as possible.
        def _object_(self, items=sorted):
            item = items[len(self.value)]
            if isinstance(item, segment.ElfXX_Phdr):
                return ptype.clone(segment_t, __segment__=item)
            return ptype.clone(section_t, __section__=item)

        # Finally we can construct our array composed of the proper types
        return ptype.clone(parray.type, _object_=_object_, length=len(sorted))

    def __padding(self):
        data = self['e_data'].li
        sections, segments = data['e_shoff'], data['e_phoff']

        position = sum(self[fld].li.size() for fld in ['e_ident', 'e_data', 'e_dataentries'])
        entry = min([item for item in [sections.int(), sections.int()] if item > position])

        return ptype.clone(ptype.block, length=max(0, entry - position))

    def __e_programhdrentries(self):
        data = self['e_data'].li
        sections, segments = data['e_shoff'], data['e_phoff']

        if isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        e_ident = self['e_ident'].li
        ei_class = e_ident['EI_CLASS']
        if ei_class['ELFCLASS32']:
            t = segment.Elf32_Phdr
        elif ei_class['ELFCLASS64']:
            t = segment.Elf64_Phdr
        else:
            raise NotImplementedError(ei_class)

        # FIXME: this needs to be properly calculated to ensure it's actually next
        count = data['e_phnum'].int() if segments.int() < sections.int() else 0

        return ptype.clone(header.PhdrEntries, _object_=t, length=count)

    def __e_sectionhdrentries(self):
        data = self['e_data'].li
        sections, segments = data['e_shoff'], data['e_phoff']

        if isinstance(self.source, ptypes.provider.memorybase):
            return ptype.undefined

        e_ident = self['e_ident'].li
        ei_class = e_ident['EI_CLASS']
        if ei_class['ELFCLASS32']:
            t = section.Elf32_Shdr
        elif ei_class['ELFCLASS64']:
            t = section.Elf64_Shdr
        else:
            raise NotImplementedError(ei_class)

        # FIXME: this needs to be properly calculated to ensure it's actually next
        count = data['e_shnum'].int() if segments.int() < sections.int() else 0

        return ptype.clone(header.ShdrEntries, _object_=t, length=count)

    _fields_ = [
        (E_IDENT, 'e_ident'),
        (__e_data, 'e_data'),
        (__e_dataentries, 'e_dataentries'),
        #(__padding, 'padding'),
        #(__e_programhdrentries, 'e_programhdrentries'),
        #(__e_sectionhdrentries, 'e_sectionhdrentries'),
    ]

### recursion for python2
from . import header

class Archive(pstruct.type):
    class _members(parray.block):
        _object_ = header.Elf_Armember

    def __members(self):
        res, t = self['armag'].li, self._members
        if isinstance(self.source, ptypes.prov.bounded):
            expected = self.source.size() - res.size()
            return ptype.clone(t, blocksize=lambda _, cb=max(0, expected): cb)

        cls = self.__class__
        logging.warning("{:s} : Unable to determine number of members for {!s} when reading from an unbounded source.".format(self.instance(), t))
        return t

    _fields_ = [
        (header.Elf_Armag, 'armag'),
        (__members, 'members'),
    ]
