import logging, bisect, functools, itertools, operator, ptypes
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

    def __segment_tables(self, data):
        '''Return the segment list and a lookup table that can be used to identify the segment associated with a boundary.'''
        segments = data['e_phoff'].d
        list = [phdr for _, phdr in segments.li.sorted()]

        # Iterate through the list and create a table for all of
        # the segments which use the segment boundaries as the key.
        table = {phdr['p_offset'].int() : phdr for phdr in list}
        table.update({phdr['p_offset'].int() + phdr.getreadsize() : phdr for phdr in list if phdr.getreadsize() > 0})

        # Simple as that, now to return them to the caller.
        return list, table

    def __section_tables(self, data):
        '''Return the section list and a lookup table that can be used to identify the section associated with a boundary.'''
        sections = data['e_shoff'].d
        list = [shdr for _, shdr in sections.li.sorted()]

        # Go through the list of sections and create a table for
        # them that uses the section's boundaries as its key.
        table = {shdr['sh_offset'].int() : shdr for shdr in list}
        table.update({shdr['sh_offset'].int() + shdr.getreadsize() : shdr for shdr in list if shdr.getreadsize() > 0})

        # Return both of them back to the caller.
        return list, table

    def __gather_lists(self, segments, sections):
        '''Iterate through each of the segments and sections in order to insert them into a sorted list.'''
        items = []

        # First we'll do the boundaries for the segments.
        for phdr in segments:
            offset = phdr['p_offset'].int()
            bisect.insort(items, offset)
            bisect.insort(items, offset + phdr.getreadsize())

        # Next we'll do the boundaries for the sections.
        for shdr in sections:
            offset = shdr['sh_offset'].int()
            bisect.insort(items, offset)
            bisect.insort(items, offset + shdr.getreadsize())

        # This list should be sorted, so now we can return it.
        return items

    def __e_dataentries(self):
        data = self['e_data'].li
        if isinstance(self.source, ptypes.provider.memorybase):
            return ptype.clone(parray.type, _object_=segment.MemorySegmentData, length=0)

        # Gather both the segments and the sections into a list, and colllect
        # their boundaries into a lookup table so that we can find the specific
        # instance that is found at a particular location.
        segmentlist, segmenttable = self.__segment_tables(data)
        sectionlist, sectiontable = self.__section_tables(data)

        # Finally, we need to create a sorted list of all of the available
        # boundaries. This way we can filter out bounds that have already been
        # included in the header, and more importantly we can convert them
        # into an iterator that we'll use to do our final processing.
        items, offset = self.__gather_lists(segmentlist, sectionlist), sum(self[fld].li.size() for fld in ['e_ident', 'e_data'])
        ilayout = itertools.dropwhile(functools.partial(operator.lt, offset), iter(items))
        ilayout = (ea for ea in ilayout if (segmenttable[ea]['p_offset'].int() if ea in segmenttable else offset) >= offset)
        ilayout = (ea for ea in ilayout if (sectiontable[ea]['sh_offset'].int() if ea in sectiontable else offset) >= offset)
        layout = [ea for ea in ilayout]

        # Our layout contains the boundaries of all of our sections, so now
        # we need to walk our layout and determine whether there's a section
        # or a segment at that particular address. We keep track of the last
        # position in order to identify if there's an empty slot in between.
        position, sorted, used = offset, [], {item for item in []}
        for boundary, _ in itertools.groupby(layout):

            # If our boundary is in the sectiontable, then use sections.
            if boundary in sectiontable:
                item = sectiontable[boundary]

                # If the current boundary is not the section's offset, then
                # we know it's the tail and we need to track its position.
                if item['sh_offset'].int() not in {boundary}:
                    position = boundary

            # If it was found in the segmenttable, then use segments.
            elif boundary in segmenttable:
                item = segmenttable[boundary]

                # If the boundary is not in the segment's offset, then we
                # know it's the tail and we need to track the position.
                if item['p_offset'].int() not in {boundary}:
                    position = boundary

            # It should be either a segment or a section, and anything else
            # should be an error.
            else:
                raise ValueError(boundary)

            # If our resulting segment or section was already used, then we
            # don't need to use it again.
            if item in used:
                continue

            # However if our position is smaller then the current boundary, then
            # we know there's some space between us and the section or segment.
            if boundary > position:
                sorted.append(boundary - position)
                position = boundary

            # Append the determined item to our sorted list, and add it so
            # that we don't have any duplicates.
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
            elif isinstance(item, section.ElfXX_Shdr):
                return ptype.clone(section_t, __section__=item)
            return ptype.clone(ptype.block, length=item)

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
