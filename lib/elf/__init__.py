import logging, bisect, functools, itertools, operator, ptypes
from ptypes import ptype, pint, pstruct, parray

from . import base, segment, section, dwarf, dwarf as exception

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

    def __segment_list__(self, data):
        '''Return the segment list and a lookup table that can be used to identify the segment associated with a boundary.'''
        segments = data['e_phoff'].d
        list = [phdr for _, phdr in segments.li.sorted()]

        # If we're using a memory-based backing, then we need to
        # only interact with all of the loadable segments.
        if isinstance(self.source, ptypes.provider.memorybase):
            return [phdr for phdr in list if phdr.loadableQ()]
        return list

    def __section_list__(self, data):
        '''Return the section list and a lookup table that can be used to identify the section associated with a boundary.'''
        sections = data['e_shoff'].d

        # If we're using a memory-based backing, then it's likely
        # that our table is actually unmapped. So, we return an
        # empty list and table just to be safe.
        if isinstance(self.source, ptypes.provider.memorybase):
            return []
        elif isinstance(self.source, ptypes.provider.bounded) and not(sections.getoffset() < self.source.size()):
            logging.warning("{:s} : Skipping {:s} due to it being outside the boundaries of the source ({:#x}..{:+#x}).".format(self.instance(), sections.instance(), 0, self.source.size()))
            return []
        return [shdr for _, shdr in sections.li.sorted()]

    def __gather_sections__(self, sections):
        '''Iterate through each of the sections in order to group their duplicates.'''

        # If we're using a memory-based backing, then we need
        # to use different methods to access the boundaries.
        if isinstance(self.source, ptypes.provider.memorybase):
            Fsize = operator.methodcaller('getloadsize')
            fields = ['p_vaddr', 'sh_addr']

        # Anything else is using a file-based backing.
        else:
            Fsize = operator.methodcaller('getreadsize')
            fields = ['p_offset', 'sh_offset']

        # Now we can assign our attribute getters.
        Fsegment_offset, Fsection_offset = map(operator.itemgetter, fields)

        # We need to combine our lists into a single collection.
        # The only issue is that our header types are mutable,
        # and thus they're not comparable. So to accomplish this,
        # we key them into a table at the same time we collect them.
        table, collection = {}, {}
        for index, shdr in enumerate(sections):
            offset, size = Fsection_offset(shdr).int(), Fsize(shdr)
            table[0, index] = shdr

            if size > 0:
                items = collection.setdefault(offset + size, [])
                bisect.insort_left(items, (size, (0, index)))

            # Now find the collection, and insort into it.
            items = collection.setdefault(offset, [])
            bisect.insort_left(items, (size, (0, index)))

        # Next we'll do the same for the segments, except we
        # give more priority since generally they're larger.
        for index, phdr in enumerate(segments):
            offset, size = Fsegment_offset(phdr).int(), Fsize(phdr)
            table[1, index] = phdr

            # Find our collection, and insort our item into it. We
            # use bisect right in case there are any duplicates so
            # that segments that come first get priority.
            items = collection.setdefault(offset + size, [])
            bisect.insort_right(items, (size, (1, index)))

        # Before we return our collection, we need to restore them
        # using our index table.
        return {offset : [(size, table[key]) for size, key in items] for offset, items in collection.items()}

    def __gather_segments__(self, segments, sections, others=[]):

        # If we're using a memory-based backing, then we need
        # to use different methods to access the boundaries.
        if isinstance(self.source, ptypes.provider.memorybase):
            Fentry_size = operator.methodcaller('getloadsize')
            fields, Floadable = ['p_vaddr', 'sh_addr'], functools.partial(functools.reduce, operator.getitem, ['p_type', 'LOAD'])

            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_vaddr'].int(), 2+6, item['p_vaddr'].int() + item.getloadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getloadsize(), 2+6, ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))

        # Anything else is using a file-based backing which
        # we'll sort by the LOAD type so we don't include
        # any of the other types that users won't care about.
        else:
            Fentry_size = operator.methodcaller('getreadsize')
            fields, Floadable = ['p_offset', 'sh_offset'], functools.partial(functools.reduce, operator.getitem, ['p_type', 'LOAD'])

            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_offset'].int(), 2+6, item['p_offset'].int() + item.getreadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getreadsize(), 2+6, item['sh_name'].str(), ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))

        # Assign an anonymous function for summarizing our segments, sections,
        # or external type (others) for the purpose of friendlier debug logging.
        summary_table = {section.ElfXX_Shdr: Fsection_summary, segment.ElfXX_Phdr: Fsegment_summary}
        Fdetermine_summary = lambda table: lambda section_or_segment: (lambda F: F(section_or_segment))(next((F for baseclass, F in table.items() if isinstance(section_or_segment, baseclass)), "{}".format))
        Fentry_summary = Fdetermine_summary(summary_table)

        # Now we can assign our attribute getters, as we're going
        # to preapare to gather our list of items to sort. The only
        # issue is that our headers that we're gaterhing will be
        # mutable and thus not comparable. So to handle this, we
        # key each of them into a table at the same time we collect.
        table, (Fsegment_offset, Fsection_offset) = {}, map(operator.itemgetter, fields)
        Fdetermine_offset = lambda table: lambda section_or_segment: (lambda F: (lambda field: field.int() if ptype.isinstance(field) else field)(F(section_or_segment)))(next((F for baseclass, F in table.items() if isinstance(section_or_segment, baseclass)), 0))
        Fentry_offset = Fdetermine_offset({section.ElfXX_Shdr: Fsection_offset, segment.ElfXX_Phdr: Fsegment_offset})

        # First we'll gather the segments. We need to do two things
        # here. We need to build an index to recognize them which
        # we store in the third element of our tuple. We'll also
        # need to identify their boundaries (1st tuple element),
        # and we'll also need another element to ensure that
        # duplicate boundaries are prioritized using the second
        # tuple element.
        items = []
        for index, phdr in enumerate(segments):
            table[0, index] = phdr
            offset, size = Fsegment_offset(phdr).int(), Fentry_size(phdr)
            items.append(((offset, offset + (size if phdr['p_type']['LOAD'] else 0)), (0, phdr['p_type'].str()), (0, index)))

        # Next we'll do something similar for the sections in
        # that we'll sort by the boundaries and the name in
        # the second element. Then we'll use the third element
        # to find the sections inside our header index.
        for index, shdr in enumerate(sections):
            table[1, index] = shdr
            offset, size = Fsection_offset(shdr).int(), Fentry_size(shdr)
            items.append(((offset, offset + size), (1, shdr['sh_name'].str()), (1, index)))

        # Now that our list of entries have been made, we need to replace
        # the immutable last element with the actual entry. We sort all
        # of them using the first two entries and use the third entry
        # to build our index. We save the bounds in the first element
        # so we don't have to calculate them again.
        headers = [(bounds, table[key]) for bounds, _, key in sorted(items, key=operator.itemgetter(0, 1))]
        headers_index = {item : index for index, (bounds, item) in enumerate(headers)}
        assert(len(headers) == len(headers_index))

        # Next thing to do is to build a segment tree for all of the
        # loadable segments. We do this in order to determine the
        # segments that a header overlaps with. We need to gather
        # an index for the segment tree so that we can identify the
        # segment header that a point on the tree is describing.
        tree, tree_index = [], {}
        for phdr in filter(Floadable, segments):
            offset, size = Fsegment_offset(phdr).int(), Fentry_size(phdr)
            start, stop = bounds = offset, offset + size
            tree_index.setdefault(start, []), tree_index.setdefault(stop, [])

            # Get the indices into the tree to figure out where our segment
            # belongs. We can do this in order to identify if a loadable
            # segments overlaps with another.
            start_index, stop_index = bisect.bisect_left(tree, start), bisect.bisect_right(tree, stop)

            # If any of our indices are odd-numbered or the same, then our
            # segment is overlapping because we're always inserting the
            # boundaries of the segment into the tree in pairs.
            if start_index % 2 or stop_index % 2 or start_index != stop_index:
                point = tree[stop_index - 1]
                items = tree_index.setdefault(point, [])

                # As the current segment is overlapping, we gather it into a
                # list for this segment because we'll sort this out later.
                index = bisect.bisect_left(items, (bounds, headers_index[phdr]))
                items.insert(index, (bounds, headers_index[phdr]))

                # Log which side of the tree we're overlapping.
                logging.debug("(overlap) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {:s}".format('<' if start_index % 2 else '>', index, len(items), start, stop, Fsegment_summary(phdr)))

            # Otherwise we figure out what slice of the tree to modify when
            # we're inserting the segment's boundaries into it.
            elif not(start_index % 2 and stop_index % 2):
                tree[start_index : stop_index] = [start, stop]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {:s}".format('><', 0, 1, start, stop, Fsegment_summary(phdr)))
            elif start_index % 2:
                tree[start_index : stop_index] = [stop]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {:s}".format('<', 0, 1, start, stop, Fsegment_summary(phdr)))
            elif stop_index % 2:
                tree[start_index : stop_index] = [start]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {:s}".format('>', 0, 1, start, stop, Fsegment_summary(phdr)))
            continue

        # Now we need to go ahead and process the "others" that were given
        # to us by the caller. This is used for contiguous blocks of memory
        # that aren't a segment or a section.
        for offset, size, item in others:
            start, stop = bounds = offset, offset + size
            tree_index.setdefault(start, []), tree_index.setdefault(stop, [])
            start_index, stop_index = bisect.bisect_left(tree, start), bisect.bisect_right(tree, stop)

            if start_index % 2 or stop_index % 2 or start_index != stop_index:
                point = tree[stop_index - 1]
                items = tree_index.setdefault(point, [])

                # As the current segment is overlapping, we gather it into a
                # list for this segment because we'll sort this out later.
                index = bisect.bisect_left(items, (bounds, headers_index[phdr]))
                items.insert(index, (bounds, headers_index[phdr]))

                # Log which side of the tree we're overlapping.
                logging.debug("(overlap) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {}".format('<' if start_index % 2 else '>', index, len(items), start, stop, item.typename()))

            elif not(start_index % 2 and stop_index % 2):
                tree[start_index : stop_index] = [start, stop]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {}".format('><', 0, 1, start, stop, item.typename()))

            elif start_index % 2:
                tree[start_index : stop_index] = [stop]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {}".format('<', 0, 1, start, stop, item.typename()))

            elif stop_index % 2:
                tree[start_index : stop_index] = [start]
                tree_index[start].append((bounds, headers_index[phdr]))
                tree_index[stop].append((bounds, headers_index[phdr]))
                logging.debug("(insert) {:s} ({:d}/{:d}) {:#010x}..{:#010x} {}".format('>', 0, 1, start, stop, item.typename()))
            continue

        # Define a closure that will walk the tree returning the segment
        # header for any offset that gets sent to it. We'll use a set to
        # keep track of the segments that have been used because we use
        # it as part of a small trick to figure out the boundary to check.
        def flatten(tree, index, headers):
            offset, used, header = 0, {item for item in []}, ptype.undefined
            for point in tree:
                items = index[point]

                # The way we walk our tree containing duplicates is that
                # when there's more than one entry for the same segment,
                # we check the starting address of the entire list first.
                # Then we check the stopping address on the second round.
                # These duplicates were only inserted into the tree once,
                # so we double it up because if the header has already
                # been used it will end up being discarded anyways.
                for bounds, key in items + items:
                    _, header = headers[key]
                    if header not in used:
                        logging.debug("(flatten) {:s} segm {:s} {:s}".format("{:#x}..{:#x}".format(*bounds), header.typename(), Fentry_summary(header)))

                    # If the header has been used once before, then compare
                    # the offset we get against the end of the segment.
                    start, stop = bounds
                    if header in used:
                        while offset < stop:
                            offset = (yield header)
                        continue

                    # If we haven't used the header yet, then compare the
                    # offset we consume against the start of the segment.
                    while offset < start:
                        offset = (yield header)

                    # Add the segment to our list of already used segments.
                    used.add(header)
                continue

            # We hit all the elements in our tree, but we still might receive
            # headers that we need to process, so take the bounds we got and
            # keep returning the last header we snagged.
            while True:
                yield header
            return

        # Now we can pass the prior closure the segment tree, its index, and
        # the list of headers and then use it to produce a table of the
        # segments and the headers each of them actually contains.
        results, iterable = {}, (((offset, offset + size), item) for offset, size, item in others)
        flattener = flatten(tree, tree_index, headers); next(flattener)
        for bounds, item in itertools.chain(headers, iterable):
            offset, _ = bounds

            # Send our offset, get our encompassing (head) segment, and
            # then use it to update our results. We will also use it as
            # the first member for each set of results that we return.
            head = flattener.send(offset)
            items = results.setdefault(head, [head])
            hoffset, hsize = Fentry_offset(head), Fentry_size(head)

            # We need to double check that the segment is not the header
            # we're processing. because it always prefixes our results.
            if head == item:
                logging.debug("(flatten) {:#x}..{:#x}     skip {:s} {:s}".format(hoffset, hoffset + hsize, item.typename(), Fentry_summary(item)))
                continue

            # We got an entry that we're keeping. So, add it to our results.
            logging.debug("(flatten) {:#x}..{:#x}     keep {:s} {:s}".format(hoffset, hoffset + hsize, item.typename(), Fentry_summary(item)))
            items.append(item)

        flattener.close()
        return results

    def __e_padding(self):
        data = self['e_data'].li
        segments, sections = (Flist(data) for Flist in [self.__segment_list__, self.__section_list__])
        offset = sum(self[fld].li.size() for fld in ['e_ident', 'e_data'])

        # If we're using a memory-backed source, then we only need to calculate
        # the empty space between our offset and the first egment.
        if isinstance(self.source, ptypes.provider.memorybase):
            iterable = (item['p_vaddr'].int() for item in segments)
            return ptype.clone(ptype.undefined, length=max(0, next(iterable, offset) - offset))

        # Otherwise we're file-backed and sections need to be included.
        iterable = (item['p_offset'].int() for item in segments)
        filtered = itertools.dropwhile(functools.partial(operator.gt, offset), iterable)
        iterable = (item['sh_offset'].int() for item in sections)
        length = min(next(itertools.dropwhile(functools.partial(operator.gt, offset), iterable), offset), next(filtered, offset))

        # Now that we have the closest boundary, we can calculate the length.
        return ptype.clone(ptype.block, length=length - offset)

    def __e_entries_unmapped_fields(self):
        '''Yield any section/segment boundaries for fields in the header that might be stored outside the segments list.

        Specifically, this can include the section header (usually) or
        the program header lists. These tables aren't actually required
        to be available during runtime. So there's a chance that they're in
        the file but won't be caught by our segment tree logic. As such,
        we need to explicitly check for them and inject them into our tree.
        '''
        data, memory_backed = self['e_data'].li, isinstance(self.source, ptypes.provider.memorybase)

        # If it's memory-backed, then we don't really care since
        # only program headers should be loaded into memory.
        if memory_backed:
            return

        # Use the sizes for the fields that we've decoded in order to determine
        # whether the segment or section header offset has been loaded already.
        fields = ['e_ident', 'e_data', 'e_padding']
        minimum = sum(self[fld].li.size() for fld in fields)

        # Grab the section header and segment header offsets for checking.
        shdr, phdr = (data[fld].li for fld in ['e_shoff', 'e_phoff'])
        if data['e_shoff'].int() > minimum:
            yield data['e_shoff'].int(), data['e_shentsize'].int() * data['e_shnum'].int(), shdr.d.__class__
        if data['e_phoff'].int() > minimum:
            yield data['e_phoff'].int(), data['e_phentsize'].int() * data['e_phnum'].int(), phdr.d.__class__
        return

    def __e_entries(self):
        data, memory_backed = self['e_data'].li, isinstance(self.source, ptypes.provider.memorybase)

        # Start out by determining whether or not our source provider is memory-backed.
        # This is so we can figure out which field of a section/segment to determine the
        # offset/address. If memory-backed, segments can be page-aligned with sections
        # not really existing. So we select the correct types for each value, and create
        # a function that can be used to get the right size for a processed section/segment.
        if memory_backed:
            section_t, segment_t, block_t = section.SectionData, segment.MixedSegmentData, ptype.block
            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_vaddr'].int(), 2+6, item['p_vaddr'].int() + item.getloadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getloadsize(), 2+6, ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))
            Fsection_offset, Fsegment_offset = map(operator.itemgetter, ['sh_addr', 'p_vaddr'])
            Fsection_size = Fsegment_size = operator.methodcaller('getloadsize')

        else:
            section_t, segment_t, block_t = section.MixedSectionData, segment.MixedSegmentData, ptype.block
            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_offset'].int(), 2+6, item['p_offset'].int() + item.getreadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getreadsize(), 2+6, item['sh_name'].str(), ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))
            Fsection_offset, Fsegment_offset = map(operator.itemgetter, ['sh_offset', 'p_offset'])
            Fsection_size = Fsegment_size = operator.methodcaller('getreadsize')

        # For the purpose of debugging, we create a function that use the type of
        # its parameter to summarize a section, segment, or external type (others).
        summary_table = {section.ElfXX_Shdr: Fsection_summary, segment.ElfXX_Phdr: Fsegment_summary}
        Fdetermine_summary = lambda table: lambda section_or_segment: (lambda F: F(section_or_segment))(next((F for baseclass, F in table.items() if isinstance(section_or_segment, baseclass)), "{}".format))
        Fentry_summary = Fdetermine_summary(summary_table)

        # Gather both the segments and the sections into a list, and colllect
        # their boundaries into a lookup table so that we can find the specific
        # instance that is found at a particular location.
        segmentlist, sectionlist = (F(data) for F in [self.__segment_list__, self.__section_list__])

        # FIXME: If we don't have any segments, then this is an object file and
        #        it's currently not implemented.
        if not segmentlist:
            return ptype.clone(parray.type, length=0)

        # Gather any segment boundaries explicitly defined in the header. These might
        # not be part of the regular segments and sections tables, but we still need
        # to inject these into our tree in order to cover the entire file contents.
        others = [offset_size_type for offset_size_type in self.__e_entries_unmapped_fields()]
        otherstable = {ooffset: otype for ooffset, osize, otype in others}

        # Finally, we can build our index of the segments that we'll later
        # use to determine the boundaries of our entries. We also calculate
        # the minimum address of the sections/segments so that we can discard
        # entries that reference the header and entries that were loaded earlier.
        minimum = sum(self[fld].li.size() for fld in ['e_ident', 'e_data', 'e_padding'])
        table = self.__gather_segments__(segmentlist, sectionlist, others)

        # Afterwards, we build a lookup table to map each segment, section,
        # or item (other) to its corresponding boundaries. This way we can
        # avoid explicit type checking in order to determine how to format
        # each processed item for the purpose of logging.
        boundstable = {item: (offset, size) for offset, size, item in others}
        for item in itertools.chain(*table.values()):
            if isinstance(item, section.ElfXX_Shdr):
                boundstable[item] = Fsection_offset(item).int(), Fsection_size(item)
            elif isinstance(item, segment.ElfXX_Phdr):
                boundstable[item] = Fsegment_offset(item).int(), Fsegment_size(item)
            else:
                assert(item in boundstable)
            continue

        # Now we can use our boundary lookup table to determine the offset
        # and size for whatever section, segment, or item being queried.
        Fentry_offset = lambda item: (lambda offset, size: offset)(*boundstable[item])
        Fentry_size = lambda item: (lambda offset, size: size)(*boundstable[item])

        # Build a index of segments that we can sort by their offset using
        # our segment list. We only care about the ones that're in our table
        # because our table uses a segment as its key.
        items = {Fsegment_offset(item).int() : item for item in segmentlist if item in table}
        headerindex = [(position, items[position]) for position in sorted(items)]
        Flogging_debug = lambda string: logging.debug("{:s}{:s}".format('    ', string))

        # With our index, we can now access the tables individually and
        # collect each of the entries for each loaded segment. This is
        # because we're going to iterate through as many segments as necessary
        # to remove entries that were loaded before the minimum offset.
        for _, header in headerindex:
            entries = table[header]

            # Take our entries and convert them into an iterator of
            # offsets. This way we can drop anything that comes before
            # the minimum offset. We'll be using the number of elements
            # we cull when modifying the entries in our table.
            iterable = (Fentry_offset(entry) for entry in entries)
            filtered = itertools.dropwhile(functools.partial(operator.gt, minimum), iterable)

            # Figure out how many elements were filtered, and use it to
            # determine the count for slicing our entries. We also need to
            # ensure that the segment header is included as the first entry.
            count = sum(1 for item in filtered)
            entries[:] = [header] + entries[-count:]

            # If there are still some entries left, then we're done. Otherwise,
            # there's likely still some entries below our minimum. So we'll
            # need to continue if the entries are empty.
            if entries:
                break
            continue

        # Finally, we start iterating through the index and using it to calculate
        # the boundaries between each member belonging to the current segment.
        result, position, base = [], minimum, self.getparent(None).getoffset()
        for boundary, header in headerindex:
            entries, size = table[header], Fentry_size(header)
            left, right, items = boundary, boundary + size, []

            logging.debug("Processing segment ({:#010x}..{:#010x}): {:s}".format(boundary, boundary + size, Fsegment_summary(header)))

            # First thing to do is to pad our current position until
            # we got to the starting offset for the current header.
            if position < left:
                res = position, left - position, block_t
                result.append(res)
                Flogging_debug("(pad)    {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + boundary, base + position, boundary - position, block_t.typename()))
                position = left

            # Now we iterate through every entry for the current header, and
            # gather only the ones that are within the current segment. The
            # purpose of this loop is to identify the segments that have the
            # highest priority so that we can slice them up into sections.
            logging.debug("Processing {:d} entries for segment ({:#010x}..{:#010x}): {:s}".format(len(entries), boundary, boundary + size, Fsegment_summary(header)))

            index, collected = 0, []
            while position < right:
                item = entries[index]
                eoffset, esize = Fentry_offset(item), Fentry_size(item)

                # We first need to handle a special case for when the segment
                # being processed includes the header that was read earlier
                # when decoding. We do this by adjusting both the offset and
                # size of the entry to exclude the header from its boundaries.
                if eoffset < minimum:
                    delta = minimum - eoffset
                    Flogging_debug("<adjust> {:#010x}..{:#010x} {:#04x}{:+#04x} : {:s}".format(base + eoffset, base + eoffset + esize, base + eoffset, esize, Fentry_summary(item)))
                    eoffset, esize = delta + eoffset, esize - delta

                # If we haven't added any entries yet, then this is the
                # first entry which should contain the segment boundaries.
                if not items:
                    res = eoffset, esize, item
                    items.append(res[-2:]), collected.append(res)
                    Flogging_debug("(header) {:#010x}..{:#010x} {:#04x}{:+#04x} : {:s}".format(base + eoffset, base + eoffset + esize, base + eoffset, esize, Fentry_summary(item)))
                    position = eoffset + esize
                    index += 1
                    continue

                # If we're below the minimum offset which should only really
                # happen if we're memory-backed, then adjust the previous
                # result so that it has a size that doesn't overlap anything.
                if eoffset < minimum:
                    delta = minimum - eoffset
                    res, previous, type = collected[-1]
                    collected[-1] = res, previous - delta, type
                    Flogging_debug("(-min)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} ({:#x}) : {:s}".format(base + eoffset, base + minimum, base + previous, -delta, base + boundary + previous - delta, Fentry_summary(item)))

                # If the current position is not pointing at the offset
                # for the entry, then pad ourselves all the way there.
                elif position < eoffset:
                    delta = eoffset - position
                    res = eoffset, delta, block_t
                    Flogging_debug("(+pad)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + eoffset, base + position, -position, Fentry_summary(item)))
                    items.append(res[-2:]), collected.append(res)
                    position = eoffset

                # If we've pushed past the offset of the current entry, then we
                # need to adjust the size for the previous result so that we don't.
                elif position > eoffset:
                    delta = position - eoffset
                    res, previous, type = collected[-1]
                    collected[-1] = res, max(0, delta - previous), type
                    Flogging_debug("(-pad)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + eoffset, base + position, -eoffset, Fentry_summary(item)))
                    position = eoffset
                    break

                # Our current position should now correspond to the offset
                # of the current entry. So, we now need to add the entry
                # to our results, whilst taking care that the size is correct.

                # If adding the entry still keeps us within the current
                # segment, then we can add it to our results untouched.
                if eoffset + esize <= right:
                    res = eoffset, esize, item
                    items.append(res[-2:]), collected.append(res)
                    Flogging_debug("(append) {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(base + eoffset, base + eoffset + esize, esize, Fentry_summary(item)))
                    position = eoffset + esize

                # If the entry pushes us outside of the segment, then
                # we need to clamp its size so that it fits correctly.
                elif eoffset + esize > right:
                    res = eoffset, right - eoffset, item
                    items.append(res[-2:]), collected.append(res)
                    Flogging_debug("(clamp)  {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(base + eoffset, base + right, right - left, Fentry_summary(item)))
                    position = boundary + size

                # Otherwise, raise an exception...this case shouldn't ever be hit.
                else:
                    raise AssertionError("(error)  {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(base + eoffset, base + eoffset + esize, esize, Fentry_summary(item)))

                index += 1
                continue

            # After processing the entries, we now need to check if
            # our current position has gotten to the end of the segment.
            # However, if we're memory-backed then we need to align the
            # current position before verifying that we're at the end.
            if memory_backed and position < right:
                delta = header.align(right) - position

                # After calculating alignment, pad our results with it.
                res = position, operator.sub(boundary, position + delta), ptype.undefined
                collected.append(res)
                Flogging_debug("(align)  {:#010x}..{:#010x} goal:{:#010x} {:#04x}{:+#04x}{:+#x} : {:s}".format(base + position, base + boundary, base + header.align(boundary), base + position, boundary - position, delta, ptype.undefined.typename()))
                position = header.align(boundary)

            # We should've completely covered the segment. Although, we still need
            # to slice up our results to include any other entries that weren't processed.
            remaining = ((Fentry_offset(entry), Fentry_size(entry), entry) for entry in entries[index:])
            while collected:
                offset, size, instance = collected.pop(0)
                while size > 0:
                    eoffset_esize_einstance = next(remaining, None)
                    if not eoffset_esize_einstance:
                        break

                    # If the boundaries and the instance are the same,
                    # then we can just skip it.
                    eoffset, esize, einstance = eoffset_esize_einstance
                    if (left, right) == (eoffset, eoffset + esize):
                        continue

                    # If the entry offset comes before our current offset,
                    # then adjust the previous entry so that the entry fits.
                    if eoffset < offset:
                        assert(result), "{:#x}..{:#x} {:#x}{:+#x} : {}".format(offset, offset + size, offset, size, instance)
                        correction = offset - eoffset
                        ooffset, osize, oinstance = result[-1]
                        result[-1] = ooffset, osize - correction, oinstance

                    # Pad up to the current element offset.
                    if eoffset > offset:
                        result.append((offset, eoffset - offset, instance))
                    offset, size = eoffset, size - eoffset + offset

                    # Finally add the regular entry to our results.
                    result.append((eoffset, esize, einstance))
                    offset, size = eoffset + esize, size - esize

                # Now we can add the header to the results.
                result.append((offset, size, instance))

            # Now we add every entry that is remaining. These don't reside within
            # a known segment, so we don't need to guarantee that they're paired.
            for eoffset, esize, einstance in remaining:
                if eoffset < offset:
                    assert(result), "{:#x}..{:#x} {:#x}{:+#x} : {}".format(eoffset, eoffset + esize, eoffset, esize, einstance)
                    correction = offset - eoffset
                    ooffset, osize, oinstance = result[-1]
                    result[-1] = ooffset, osize - correction, oinstance

                # Pad up to the current element offset.
                if eoffset > offset:
                    result.append((offset, eoffset - offset, block_t))
                offset, size = eoffset, size - eoffset + offset

                result.append((eoffset, esize, einstance))
                offset, size = eoffset + esize, size - esize
            continue

        # Everything has been sorted, so now we can construct our array and
        # align it properly to load as many contiguous pieces as possible.
        maximum = self.source.size() if isinstance(self.source, ptypes.provider.bounded) else None
        def _object_(self, items=result):
            offset, size, item = items[len(self.value)]
            if maximum is not None and any([maximum <= offset, maximum <= offset + size]):
                if isinstance(item, segment.ElfXX_Phdr):    keyword, type = '__segment__', segment.UndefinedSegmentData
                elif isinstance(item, section.ElfXX_Shdr):  keyword, type = '__section__', section.UndefinedSectionData
                elif offset not in otherstable:             keyword, type = '', ptype.undefined
                else:                                       return otherstable[offset]
                return ptype.clone(type, length=size, **{keyword: item} if keyword else {})
            elif isinstance(item, segment.ElfXX_Phdr):
                return ptype.clone(segment_t, length=size, __segment__=item)
            elif isinstance(item, section.ElfXX_Shdr):
                return ptype.clone(section_t, length=size, __section__=item)
            return ptype.clone(item, length=size)

        # Finally we can construct our array composed of the proper types
        return ptype.clone(parray.type, _object_=_object_, length=len(result))

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
        #(__e_hdrentries, 'e_hdrentries'),
        (__e_padding, 'e_padding'),
        (__e_entries, 'e_entries'),
        (ptype.block, 'e_trailer'),
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
