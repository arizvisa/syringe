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

    def __gather_segments__(self, segments, sections):

        # If we're using a memory-based backing, then we need
        # to use different methods to access the boundaries.
        if isinstance(self.source, ptypes.provider.memorybase):
            Fsize = operator.methodcaller('getloadsize')
            fields, Floadable = ['p_vaddr', 'sh_addr'], functools.partial(functools.reduce, operator.getitem, ['p_type', 'LOAD'])

            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_vaddr'].int(), 2+6, item['p_vaddr'].int() + item.getloadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getloadsize(), 2+6, ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))

        # Anything else is using a file-based backing which
        # we'll sort by the LOAD type so we don't include
        # any of the other types that users won't care about.
        else:
            Fsize = operator.methodcaller('getreadsize')
            fields, Floadable = ['p_offset', 'sh_offset'], functools.partial(functools.reduce, operator.getitem, ['p_type', 'LOAD'])
            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_offset'].int(), 2+6, item['p_offset'].int() + item.getreadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getreadsize(), 2+6, item['sh_name'].str(), ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))

        # Assign an anonymous function for summarizing our segments/sections
        Fsummary = lambda section_or_segment: Fsection_summary(section_or_segment) if isinstance(section_or_segment, section.ElfXX_Shdr) else Fsegment_summary(section_or_segment)

        # Now we can assign our attribute getters, as we're going
        # to preapare to gather our list of items to sort. The only
        # issue is that our headers that we're gaterhing will be
        # mutable and thus not comparable. So to handle this, we
        # key each of them into a table at the same time we collect.
        table, (Fsegment_offset, Fsection_offset) = {}, map(operator.itemgetter, fields)

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
            offset, size = Fsegment_offset(phdr).int(), Fsize(phdr)
            items.append(((offset, offset + (size if phdr['p_type']['LOAD'] else 0)), (0, phdr['p_type'].str()), (0, index)))

        # Next we'll do something similar for the sections in
        # that we'll sort by the boundaries and the name in
        # the second element. Then we'll use the third element
        # to find the sections inside our header index.
        for index, shdr in enumerate(sections):
            table[1, index] = shdr
            offset, size = Fsection_offset(shdr).int(), Fsize(shdr)
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
            offset, size = Fsegment_offset(phdr).int(), Fsize(phdr)
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
                offset = tree[stop_index - 1]
                items = tree_index.setdefault(offset, [])

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
                        logging.debug("(flatten) segm {:s} {:s}".format(header.typename(), Fsegment_summary(header)))

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
        results, flattener = {}, flatten(tree, tree_index, headers); next(flattener)
        for bounds, item in headers:
            offset, _ = bounds

            # Send our offset, get our segment. Simple as that. We first
            # need to update our results with it since it will always be
            # the first member for each segment in our results.
            segment = flattener.send(offset)
            items = results.setdefault(segment, [segment])

            # We need to double check that the segment is not the header
            # we're processing. because it always prefixes our results.
            if segment == item:
                logging.debug("(flatten)     skip {:s} {:s}".format(item.typename(), Fsegment_summary(item)))
                continue

            # We got an entry that we're keeping. So, add it to our results.
            logging.debug("(flatten)     keep {:s} {:s}".format(item.typename(), Fsummary(item)))
            items.append(item)
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

    def __e_entries(self):
        data = self['e_data'].li

        # Gather both the segments and the sections into a list, and colllect
        # their boundaries into a lookup table so that we can find the specific
        # instance that is found at a particular location.
        segmentlist, sectionlist = (F(data) for F in [self.__segment_list__, self.__section_list__])

        # FIXME: If we don't have any segments, then this is an object file and
        #        it's currently not implemented.
        if not segmentlist:
            return ptype.clone(parray.type, length=0)

        # Finally, we can build our index of the segments that we'll later
        # use to determine the boundaries of our entries. We also calculate
        # the minimum address so we can discard entries that have already
        # been loaded.
        table, minimum = self.__gather_segments__(segmentlist, sectionlist), sum(self[fld].li.size() for fld in ['e_ident', 'e_data', 'e_padding'])

        # Now we need to figure out which types and fields to use when figuring
        # out our layout. If it's a memory-based backing, we use the memory-related
        # types, undefined blocks, and the address-related fields.
        if isinstance(self.source, ptypes.provider.memorybase):
            section_t, segment_t, block_t, fields = section.SectionData, segment.MixedSegmentData, ptype.block, ['sh_addr', 'p_vaddr']
            Fsize = operator.methodcaller('getloadsize')

            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_vaddr'].int(), 2+6, item['p_vaddr'].int() + item.getloadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getloadsize(), 2+6, ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))
        else:
            section_t, segment_t, block_t, fields = section.MixedSectionData, segment.MixedSegmentData, ptype.block, ['sh_offset', 'p_offset']
            Fsize = operator.methodcaller('getreadsize')

            Fsegment_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} flags:{:s}".format(item.__class__.__name__, item['p_type'].str(), item['p_offset'].int(), 2+6, item['p_offset'].int() + item.getreadsize(), 2+6, ''.join(name for name in item['p_flags'] if item['p_flags'][name]))
            Fsection_summary = lambda item: "{:s} ({:s}) {:#0{:d}x}..{:#0{:d}x} name:{!r} flags:{:s}".format(item.__class__.__name__, item['sh_type'].str(), item['sh_offset'].int(), 2+6, item['sh_offset'].int() + item.getreadsize(), 2+6, item['sh_name'].str(), ' '.join(name for name in item['sh_flags'] if item['sh_flags'][name] and not isinstance(item['sh_flags'][name], pstruct.pbinary.flags)))

        # Assign our fields and an anonymous function to summarize items for debugging
        Fsection_offset, Fsegment_offset = map(operator.itemgetter, fields)
        Fsummary = lambda section_or_segment: Fsection_summary(section_or_segment) if isinstance(section_or_segment, section.ElfXX_Shdr) else Fsegment_summary(section_or_segment)

        # Build a index of segments that we can sort by their offset using
        # our segment list. We only care about the ones that're in our table
        # because our table uses a segment as its key.
        items = {Fsegment_offset(item).int() : item for item in segmentlist if item in table}
        index = [(position, items[position]) for position in sorted(items)]

        # With our index, we can now access the tables individually and
        # collect each of the entries for each loaded segment. This is
        # because we're going to iterate through as many segments as necessary
        # to remove entries that were loaded before the minimum offset.
        for _, header in index:
            entries = table[header]

            # Take our entries and convert them into an iterator of
            # offsets. This way we can drop anything that comes before
            # the minimum offset. We'll be using the number of elements
            # we cull when modifying the entries in our table.
            iterable = ((Fsection_offset(entry).int() if isinstance(entry, section.ElfXX_Shdr) else Fsegment_offset(entry).int()) for entry in entries)
            filtered = itertools.dropwhile(functools.partial(operator.gt, minimum), iterable)

            # Figure out how many elements were filtered, and use it to
            # determine the count to slice our our entries. We always
            # ensure that the segment header is the first entry.
            count = sum(1 for item in filtered)
            entries[:] = [header] + entries[-count:]

            # If there are still some entries left, then we're done. Otherwise,
            # there's likely still some entries below our minimum. So we'll
            # need to continue if the entries are empty.
            if entries:
                break
            continue

        # Finally we can iterate through index table and calculate the boundaries
        # between each member for each loaded segment.
        result, position, base = [], minimum, self.getparent(None).getoffset()
        for boundary, header in index:
            entries, size, items = table[header], Fsize(header), []
            logging.debug("(decode) Processing segment: {:s}".format(Fsegment_summary(header)))

            # If we're memory-backed, then we need to align our segment. This is
            # unmapped, so we'll need to make sure we don't decode from its address.
            if isinstance(self.source, ptypes.provider.memorybase) and position < boundary:
                delta = header.align(boundary) - boundary

                # We got the size of our alignment so pad our results with a block.
                res = position, boundary - position + delta, ptype.undefined
                result.append(res)
                logging.debug("(align)  {:#010x}..{:#010x} goal:{:#010x} {:#04x}{:+#04x}{:+#x} : {:s}".format(base + position, base + boundary, base + header.align(boundary), base + position, boundary - position, delta, ptype.undefined.typename()))
                position = header.align(boundary)

            # Very first thing we need to do is to pad things up to the current
            # segment ensuring that we begin at the right place.
            if position < boundary:
                res = position, boundary - position, block_t
                result.append(res)
                logging.debug("(pad)    {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + boundary, base + position, boundary - position, block_t.typename()))
                position = boundary

            # Iterate through all of our entries while keeping track of the
            # maximum size for the loaded segment. This way we can track when
            # an entry goes out of bounds be able to trim it down if so.
            for count, item in enumerate(entries):
                entrysize, offset = Fsize(item), Fsegment_offset(item).int() if isinstance(item, segment.ElfXX_Phdr) else Fsection_offset(item).int()

                # If this is the very first segment and we have some entries,
                # then we ignore the entrysize and clamp it down towards
                # whatever size we need for the next element.
                if not items:
                    res = offset, entrysize, item
                    items.append(res[-2:]), result.append(res)
                    logging.debug("(header) {:#010x}..{:#010x} {:#04x}{:+#04x} : {:s}".format(base + offset, base + offset + entrysize, base + offset, entrysize, Fsummary(item)))
                    position = offset + entrysize
                    continue

                # If we're below the minimum offset which should only really
                # happen if we're memory-backed, then adjust the previous
                # result so that it has a size that doesn't overlap anything.
                elif offset < minimum:
                    delta = minimum - offset
                    res, previous, t = result[-1]
                    result[-1] = res, previous - delta, t
                    logging.debug("(-min)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} ({:#x}) : {:s}".format(base + offset, base + minimum, base + previous, -delta, base + boundary + previous - delta, Fsummary(item)))

                # If our position does not point at our entry's offset,
                # then we need to add a block to pad us all the way there.
                elif position < offset:
                    delta = offset - position
                    res = offset, delta, block_t
                    logging.debug("(+pad)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + offset, base + position, -position, Fsummary(item)))
                    items.append(res[-2:]), result.append(res)
                    position = offset

                # If our projected position pushes us all the way to
                # our segment and we didn't terminate the loop, then
                # we need to backtrack and try it out again.
                elif position > offset:
                    delta = position - offset
                    res, previous, t = result[-1]
                    result[-1] = res, max(0, delta - previous), t
                    logging.debug("(-pad)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + offset, base + position, -offset, Fsummary(item)))
                    position = offset

                # If our next position is actually outside the bounds of
                # the segment, then we need to exit our loop only if the
                # size of the entry holds something. We have to explicitly
                # check for this because we didn't constrain our entries
                # when we built our segment index. Since we're terminating
                # early, subtract one from the counter since we're not
                # going to be processing the next element.
                if position >= boundary + size and size > 0:
                    logging.debug("(break)  {:#010x} >= {:#010x} {:+#04x} : {:s}".format(base + position, base + boundary + size, size, Fsummary(item)))
                    break

                # If we're where we expect, but it pushes us outside the
                # boundaries of the segment, the clamp it to a size that
                # lays us at the very end of the segment.
                elif position == offset and offset + entrysize > boundary + size:
                    res = offset, (boundary + size) - offset, item
                    items.append(res[-2:]), result.append(res)
                    logging.debug("(clamp)  {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(base + offset, base + boundary + size, size, Fsummary(item)))
                    position = boundary + size

                # If our position is where we expect it, then we can simply
                # append our element with its entrysize.
                elif position == offset and offset + entrysize <= boundary + size:
                    res = offset, entrysize, item
                    items.append(res[-2:]), result.append(res)
                    logging.debug("(append) {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(base + offset, base + offset + entrysize, entrysize, Fsummary(item)))
                    position = offset + entrysize

                # Raise an exception because this shouldn't happen at all.
                else:
                    raise AssertionError
                continue

            # Increment by one if we completed process the entries to
            # so that slicing doesn't include any of our entries.
            else:
                count += 1

            # If there's no leftover entries, then we can simply move
            # onto the next segment to process.
            if count == len(entries):
                continue

            # Otherwise we have some leftover entries and we need to
            # continue to add them to our list of results.
            logging.debug("(leftover) {:#010x}..{:#010x} {:d}/{:d} (need {:+d} more)".format(base + position, base + position + size, count, len(entries), len(entries) - count))

            # If we have any leftover entries, then continue to process
            # those, getting their size, and adding them to our results.
            for index, item in enumerate(entries[count:]):
                entrysize, offset = Fsize(item), Fsegment_offset(item).int() if isinstance(item, segment.ElfXX_Phdr) else Fsection_offset(item).int()

                # However, we still need to track our offset because we
                # actually might need to pad our way there.
                if position < offset:
                    res = offset, offset - position, block_t
                    result.append(res)
                    logging.debug("(pad)   {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + position, base + offset, base + position, offset - position, block_t.typename()))
                    position = offset

                # If we're not at the correct position, then we need to
                # adjust the size of our item so the sections line up.
                if position > offset:
                    delta = position - offset
                    #result[-1] = max(0, delta - previous), t
                    logging.debug("(clamp) {:#010x} goal:{:#010x} {:#04x}{:+#04x} : {:s}".format(base + offset, base + position, base + position, delta, block_t.typename()))
                    result.append((offset, entrysize - delta, item))
                    position += entrysize - delta

                # We should be good, so we just need to add it.
                else:
                    result.append((offset, entrysize, item))
                    logging.debug("(append) {:d}/{:d} {:#010x} goal:{:#010x} {:+#04x} : {:s}".format(1 + count + index, len(entries), base + offset, base + offset + entrysize, entrysize, Fsummary(item)))
                    position += entrysize
                continue
            continue

        # Everything has been sorted, so now we can construct our array and
        # align it properly to load as many contiguous pieces as possible.
        maximum = self.source.size() if isinstance(self.source, ptypes.provider.bounded) else None
        def _object_(self, items=result):
            offset, size, item = items[len(self.value)]
            if maximum is not None and any([maximum <= offset, maximum <= offset + size]):
                if isinstance(item, segment.ElfXX_Phdr):    keyword, type = '__segment__', segment.UndefinedSegmentData
                elif isinstance(item, section.ElfXX_Shdr):  keyword, type = '__section__', section.UndefinedSectionData
                else:                                       keyword, type = '', ptype.undefined
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
