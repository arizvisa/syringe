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
        return [shdr for _, shdr in sections.li.sorted() if not shdr['sh_type']['NOBITS']]

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

            # Find our collection, and insort our item into it.
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
            fields, Floadable = ['p_vaddr', 'sh_addr'], operator.methodcaller('loadableQ')

        # Anything else is using a file-based backing.
        else:
            Fsize = operator.methodcaller('getreadsize')
            fields, Floadable = ['p_offset', 'sh_offset'], functools.partial(functools.reduce, operator.getitem, ['p_type', 'LOAD'])

        # Now we can assign our attribute getters, as we're going
        # to preapare to gather our list of items to sort. The only
        # issue is that our headers that we're gaterhing will be
        # mutable and thus not comparable. So to handle this, we
        # key each of them into a table at the same time we collect.
        table, (Fsegment_offset, Fsection_offset) = {}, map(operator.itemgetter, fields)

        # We need to gather all our sections into a single sorted
        # list. To sort them, we use their tail boundary and their
        # to append them after any duplicate entries. As they've
        # already been sorted by size, this guarantees that if
        # they're _exact_ duplicates, they retain their file order.
        items = []
        for index, shdr in enumerate(sections):
            offset, size = Fsection_offset(shdr).int(), Fsize(shdr)
            table[0, index] = shdr
            bisect.insort_right(items, (offset + size, size, (0, index)))

        # Next we'll do the same for the segments, except we
        # give more priority and insert them in front of our
        # sections since generally they're unique.
        for index, phdr in enumerate(segments):
            offset, size = Fsegment_offset(phdr).int(), Fsize(phdr)
            table[1, index] = phdr
            bisect.insort_left(items, (offset, size, (1, index)))

        # Now that our list of entries have been sorted, we need to
        # replace the immutable keys with their actual entry. We preserve
        # the offset in our entries so we don't have to decode it again.
        headers = [(offset, table[key]) for offset, size, key in items]

        # We can now prepare to collect all the entries and group them
        # according to the segment they're loaded under. We use the
        # segment offsets as the key, and so we need to build up a lookup
        # table for the segments that will contain our keys.
        item, table = segments[-1], {Fsegment_offset(item).int() : item for item in segments if Floadable(item)}
        segment_key = Fsegment_offset(item).int()

        # Take our loaded segments table, and build an index for them
        # that we'll use to maintain the boundaries of the headers that
        # we're grouping them underneath.
        segment_index, results = [item for item in sorted(table)], {offset : [item] for offset, item in table.items()}
        for offset, item in headers:

            # If the current header is a segment and it's in our table,
            # then switch to it as our segment key. Insert it into our
            # index of segments.
            if isinstance(item, segment.ElfXX_Phdr) and offset in table:
                bounds = [F(item) for F in [Fsegment_offset, Fsize]]
                segment_key = Fsegment_offset(item).int()
                bisect.insort_right(segment_index, segment_key)

            # If the current header comes after our segment key (offset),
            # then append it to our results for the current segment.
            elif segment_key <= offset:
                results[segment_key].append(item)

            # If the current header did not come after our segment key,
            # then we need to find one that does. We traverse (bisect)
            # to find the offset in our segment index, and sanity check
            # that our traversal didn't result in a segment that doesn't
            # come before the current header that we're processing.
            else:
                index = bisect.bisect_left(segment_index, offset)
                key = segment_index[index]
                if key > offset:
                    raise NotImplementedError
                    segment_index.insert(index, key)

                # Now that we have a segment for the current header,
                # change our segment key, add the header to our results,
                # and continue chugging along.
                segment_key = segment_index[index]
                results[segment_key].append(item)
            continue

        # We got our results, we just need to transform their keys (offsets) back
        # into the real segment using our table.
        Fsortable = lambda item: Fsegment_offset(item).int() if isinstance(item, segment.ElfXX_Phdr) else Fsection_offset(item).int()
        return {table[offset] : sorted(items, key=Fsortable) for offset, items in results.items()}

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
        else:
            section_t, segment_t, block_t, fields = section.MixedSectionData, segment.MixedSegmentData, ptype.block, ['sh_offset', 'p_offset']
            Fsize = operator.methodcaller('getreadsize')
        Fsection_offset, Fsegment_offset = map(operator.itemgetter, fields)

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
        result, position = [], minimum
        for boundary, header in index:
            entries, size, items = table[header], Fsize(header), []

            # If we're memory-backed, then we need to align our segment. This is unmapped,
            # so we'll use an undefined type.
            if isinstance(self.source, ptypes.provider.memorybase) and position < boundary:
                alignment = header['p_align'].int()
                padding = abs((position % alignment) - alignment) if alignment else 0

                res = -1, padding, ptype.undefined
                result.append(res)
                position += padding

            # Pad things up to the current segment boundary ensuring that we're
            # at the right place in case that we're behind.
            if position < boundary:
                res = -1, boundary - position, block_t
                result.append(res)
                position = boundary

            # Iterate through all of our entries while keeping track of the
            # maximum size for the loaded segment. This way we can track when
            # an entry goes out of bounds be able to trim it down if so.
            for i, item in enumerate(entries):
                entrysize, offset = Fsize(item), Fsegment_offset(item).int() if isinstance(item, segment.ElfXX_Phdr) else Fsection_offset(item).int()

                # If this is the very first segment and we have some entries,
                # then we ignore the entrysize and clamp it down towards
                # whatever size we need for the next element.
                if not items:
                    res = 0, entrysize, item
                    items.append(res), result.append(res)
                    position = offset + entrysize
                    continue

                # If we're below the minimum offset which should only really
                # happen if we're memory-backed, then adjust the previous
                # result so that it has a size that doesn't overlap anything.
                elif offset < minimum:
                    delta = minimum - offset
                    _, previous, t = result[-1]
                    result[-1] = -1, previous - delta, t

                # If our position does not point at our entry's offset,
                # then we need to add a block to pad us all the way there.
                elif position < offset:
                    delta = offset - position
                    res = 2, delta, block_t
                    items.append(res), result.append(res)
                    position = offset

                # If our projected position pushes us all the way to
                # our segment and we didn't terminate the loop, then
                # we need to backtrack and try it out again.
                elif position > offset:
                    delta = position - offset
                    cls, previous, t = result[-1]
                    result[-1] = -3, max(0, delta - previous), t
                    position = offset

                # If our next position is actually outside the bounds of
                # the segment, then we need to exit our loop only if the
                # size of the entry holds something. We have to explicitly
                # check for this because we didn't constrain our entries
                # when we built our segment index. Since we're terminating
                # early, subtract one from the counter since we're not
                # going to be processing the next element.
                if position >= boundary + size and size > 0:
                    break

                # If we're where we expect, but it pushes us outside the
                # boundaries of the segment, the clamp it to a size that
                # lays us at the very end of the segment.
                elif position == offset and offset + entrysize > boundary + size:
                    res = 4, (boundary + size) - offset, item
                    items.append(res), result.append(res)
                    position = boundary + size

                # If our position is where we expect it, then we can simply
                # append our element with its entrysize.
                elif position == offset and offset + entrysize <= boundary + size:
                    res = 5, entrysize, item
                    items.append(res), result.append(res)
                    position = offset + entrysize

                # Otherwise if our position doesn't correspond, then we need to
                # adjust it directly to the offset that we should be at.
                elif position == offset:
                    raise NotImplementedError
                    res = 6, entrysize, item
                    items.append(res), result.append(res)
                    position = offset + entrysize

                # This is a case that we haven't discovered yet.
                elif position + entrysize > offset:
                    raise NotImplementedError
                    _, previous, t = result[-1]
                    result[-1] = -7, position - previous, t

                    res = 7, entrysize, item
                    items.append(res), result.append(res)
                    position = offset + entrysize

                elif position > offset:
                    raise NotImplementedError
                    delta = position - offset
                    _, previous, t = result[-1]
                    result[-1] = 8, previous - delta, t

                    res = 8, entrysize, item
                    items.append(res), result.append(res)
                    position = offset + entrysize

                continue

            # Increment by one if we completed process the entries to
            # so that slicing doesn't include any of our entries.
            else:
                i += 1
            continue

        # Everything has been sorted, so now we can construct our array and
        # align it properly to load as many contiguous pieces as possible.
        def _object_(self, items=result):
            _, size, item = items[len(self.value)]
            if isinstance(item, segment.ElfXX_Phdr):
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
