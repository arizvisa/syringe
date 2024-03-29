import ptypes
from ptypes import *

from . import headers, portable
from .headers import *

import logging

class ObjectHeader(portable.IMAGE_FILE_HEADER):
    _fields_ = portable.IMAGE_FILE_HEADER._fields_[2:]

class FakeOptionalHeader(portable.IMAGE_OPTIONAL_HEADER):
    _fields_ = [
        ( dyn.clone(portable.headers.IMAGE_NT_OPTIONAL_MAGIC, length=0), 'Magic' ),
        ( pint.uint_t, 'MajorLinkerVersion' ),
        ( pint.uint_t, 'MinorLinkerVersion' ),
        ( pint.uint_t, 'SizeOfCode' ),
        ( pint.uint_t, 'SizeOfInitializedData' ),
        ( pint.uint_t, 'SizeOfUninitializedData' ),
        ( virtualaddress(ptype.undefined, type=pint.uint_t), 'AddressOfEntryPoint' ),
        ( pint.uint_t, 'BaseOfCode' ),
        ( pint.uint_t, 'BaseOfData' ),
        ( pint.uint_t, 'ImageBase' ),
        ( pint.uint_t, 'SectionAlignment' ),
        ( pint.uint_t, 'FileAlignment' ),
        ( pint.uint_t, 'MajorOperatingSystemVersion' ),
        ( pint.uint_t, 'MinorOperatingSystemVersion' ),
        ( pint.uint_t, 'MajorImageVersion' ),
        ( pint.uint_t, 'MinorImageVersion' ),
        ( pint.uint_t, 'MajorSubsystemVersion' ),
        ( pint.uint_t, 'MinorSubsystemVersion' ),
        ( pint.uint_t, 'Win32VersionValue' ),
        ( pint.uint_t, 'SizeOfImage' ),
        ( pint.uint_t, 'SizeOfHeaders' ),
        ( pint.uint_t, 'CheckSum' ),
        ( dyn.clone(portable.headers.IMAGE_SUBSYSTEM_, length=0), 'Subsystem' ),
        ( pbinary.flags, 'DllCharacteristics' ),
        ( pint.uint_t, 'SizeOfStackReserve' ),
        ( pint.uint_t, 'SizeOfStackCommit' ),
        ( pint.uint_t, 'SizeOfHeapReserve' ),
        ( pint.uint_t, 'SizeOfHeapCommit' ),
        ( pint.uint_t, 'LoaderFlags' ),
        ( pint.uint_t, 'NumberOfRvaAndSizes' ),
    ]

class ImportHeader(pstruct.type):
    _fields_ = [
        (uint16, 'Version'),
        (headers.IMAGE_FILE_MACHINE_, 'Machine'),
        (headers.TimeDateStamp, 'TimeDateStamp'),
        (uint32, 'SizeOfData'),
    ]

class ImportData(pstruct.type):
    _fields_ = [
        (portable.imports.word, 'Ordinal/Hint'),
        (headers.IMAGE_IMPORT_TYPE_INFORMATION, 'Type'),
        (pstr.szstring, 'Symbol'),
        (pstr.szstring, 'Library'),
    ]

    def str(self):
        fields = ['Library', 'Symbol']
        return '!'.join(self[fld].str() for fld in fields)

class FileSegmentEntry(pstruct.type):
    def __Data(self):
        section = self.Section
        return dyn.block(section['SizeOfRawData'].li.int())

    def __Relocations(self):
        section = self.Section
        if section['PointerToRelocations'].int() == self.getoffset() + section['SizeOfRawData'].li.int():
            return dyn.clone(portable.relocations.RelocationTable, length=section['NumberOfRelocations'].int())
        return portable.relocations.RelocationTable

    _fields_ = [
        (__Data, 'Data'),
        (__Relocations, 'Relocations'),
    ]
    def properties(self):
        res = super(FileSegmentEntry, self).properties()
        if hasattr(self, 'Section'):
            res['SectionName'] = self.Section['Name'].str()
        return res

class SegmentTableArray(parray.type):
    def _object_(self):
        p = self.getparent(headers.Header)
        sections = p['Sections'].li
        section = sections[len(self.value)]
        return dynamic.clone(FileSegmentEntry, Section=section)

class File(pstruct.type, headers.Header, ptype.boundary):
    """Coff Object File"""
    def __Header(self):
        machine = self['Machine'].li
        if machine['UNKNOWN'] and self['NumberOfSections'].li.int() == 0xffff:
            return ImportHeader
        return ObjectHeader

    def __OptionalHeader(self):
        res = self['Header'].li
        if isinstance(res, ObjectHeader) and res['SizeOfOptionalHeader'].int():
            return portable.IMAGE_OPTIONAL_HEADER
        return FakeOptionalHeader

    def __DataDirectory(self):
        cls = self.__class__
        hdr, optional = (self[fld].li for fld in ['Header', 'OptionalHeader'])
        if 'SizeOfOptionalHeader' not in hdr or not isinstance(optional, portable.IMAGE_OPTIONAL_HEADER):
            return dyn.clone(portable.DataDirectory, length=0)

        length, directory = optional['NumberOfRvaAndSizes'].int(), 8

        if hdr['SizeOfOptionalHeader'].int() < optional.size():
            logging.warning("{:s} : FileHeader.SizeOfOptionalHeader ({:+#x}) is smaller than the OptionalHeader ({:+#x}). Ignoring the OptionalHeader.NumberOfRvaAndSizes ({:d}) and thus the DataDirectory.".format('.'.join([cls.__module__, cls.__name__]), hdr['SizeOfOptionalHeader'].size(), optional.size(), length))
            length = 0

        elif length * directory != hdr['SizeOfOptionalHeader'].int() - optional.size():
            available = hdr['SizeOfOptionalHeader'].int() - optional.size()
            logging.warning("{:s} : OptionalHeader.NumberOfRvaAndSizes ({:d}) does not correspond to FileHeader.SizeOfOptionalHeader ({:+#x}). Available space ({:+#x}) results in only {:d} entries.".format('.'.join([cls.__module__, cls.__name__]), length, optional.size(), available, available // directory))
            length = available // directory

        elif length > 0x10:
            logging.warning("{:s} : OptionalHeader.NumberOfRvaAndSizes ({:d}) is larger than {:d}. Assuming the maximum number of DataDirectory entries ({:d}).".format('.'.join([cls.__module__, cls.__name__]), length, 0x10, 0x10))

        return dyn.clone(portable.DataDirectory, length=min(0x10, length))

    def __OptionalHeaderPadding(self):
        hdr, fields = self['Header'].li, ['OptionalHeader', 'DataDirectory']
        if isinstance(hdr, ObjectHeader):
            expected = hdr['SizeOfOptionalHeader'].int()
            return dyn.block(max(0, expected - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)

    def __Sections(self):
        header = self['Header'].li
        if isinstance(header, ImportHeader):
            return dynamic.clone(portable.SectionTableArray, length=0)

        count = self['NumberOfSections'].li
        return dynamic.clone(portable.SectionTableArray, length=count.int())

    def __Segments(self):
        header = self['Header'].li
        if isinstance(header, ImportHeader):
            return ImportData

        count = self['NumberOfSections'].li
        return dynamic.clone(SegmentTableArray, length=count.int())

    def __align_SymbolTable(self):
        header, fields = self['Header'].li, ['Machine', 'NumberOfSections', 'Header', 'OptionalHeader', 'DataDirectory', 'Padding(OptionalHeader,DataDirectory)', 'Sections', 'Segments']
        if 'PointerToSymbolTable' in header:
            res, size = header['PointerToSymbolTable'].li, sum(self[fld].li.size() for fld in fields)
            return dyn.block(max(0, res.int() - size))
        return ptype.block

    def __SymbolTable(self):
        header = self['Header'].li
        if isinstance(header, ImportHeader):
            return ptype.undefined
        return portable.symbols.SymbolTableAndStringTable

    _fields_ = [
        (headers.IMAGE_FILE_MACHINE_, 'Machine'),
        (uint16, 'NumberOfSections'),
        (__Header, 'Header'),
        (__OptionalHeader, 'OptionalHeader'),
        (__DataDirectory, 'DataDirectory'),
        (__OptionalHeaderPadding, 'Padding(OptionalHeader,DataDirectory)'),
        (__Sections, 'Sections'),

        # FIXME: everything after this could be laid out in any sorta way since
        #        these are all referenced by pointers within the list of sections
        #        and the header. so, we're actually assuming that these fields
        #        are packed and aligned. the relocations could be at the end of
        #        its corresponding segment, before the symboltable, or afterwards.
        #        the segments could also be in a completely different order, even.
        #        the right way would be to gather all the pointers and sort them
        #        into a flat array with each element padded until the next one.

        (__Segments, 'Segments'),
        (__align_SymbolTable, 'align(SymbolTable)'),
        (__SymbolTable, 'SymbolTable'),
    ]

    def ImportLibraryQ(self):
        machine = self['Machine'].li
        if machine['UNKNOWN']:
            return self['NumberOfSections'].li.int() == 0xffff
        return False

    def FileHeader(self):
        '''Return the Header which contains a number of sizes used by the file.'''
        return self['Header']

    def Machine(self):
        if self.ImportLibraryQ():
            return self['Header']['Machine']
        return self['Machine']

    def Sections(self):
        '''Iterate through all of the sections within the file and yield each one.'''
        for index, section in enumerate(self['Sections']):
            yield section
        return

    def Segments(self):
        '''Iterate through all of the segments within the file and yield each one.'''
        for index, section in enumerate(self['Sections']):
            segment = section['PointerToRawData'].d
            yield segment.li
        return

if __name__ == '__main__':
    ## parse the file
    import sys, pecoff, ptypes
    from ptypes import provider
    import logging

    print('-'*20 + 'loading file..')
    self = coff = pecoff.Object.File(source=provider.file(sys.argv[1], 'rb'))
    coff.load()

    __name__ = 'ImportLibrary' if coff.ImportLibraryQ() else 'CoffObject'

if __name__ == 'ImportLibrary':
    print(coff['Header'])
    print(coff['Segments'])

if __name__ == 'CoffObject':
    print(coff['Header'])
    print(coff['Sections'])

    ### check everything from the symbol table's perspective
    sst = coff['Header']['PointerToSymbolTable'].d
    print(sst)
    sst.load()

    symboltable = sst['Symbols']

    print('-'*20 + 'printing external symbols')
    ## build list of external symbols
    sym_external = {}
    for name in sst.names():
        v = sst.Symbol(name)
        if v['StorageClass'].int() == v['StorageClass'].byname('EXTERNAL'):
            sym_external[name] = v
        continue

    print('\n'.join(map(repr, sym_external.values())))

    print('-'*20 + 'printing statically defined symbols')
    ## build list of static symbols
    sym_static = {}
    for name in sst.names():
        sym = sst.Symbol(name)
        if sym['StorageClass'].int() == sym['StorageClass'].byname('STATIC') and sym['Value'].int() == 0:
            idx = sym.SectionIndex()
            sym_static[idx] = (sym, sst.Auxiliary(name))
        continue

    for x in sym_static.keys():
        sym,aux = sym_static[x]
        print(sym)
        if aux:
            print('\n'.join(map(repr,aux)))

    print('-'*20 + 'check that the number of relocations in the symboltable matches the section\'s')
    ## build list of static symbols
    ## sanity check that the number of relocations are correct
    sections = coff['Sections']
    for index, (sym, aux) in sym_static.items():
        section = sections[index]
        sectioncount = section['NumberOfRelocations'].int()
        if len(aux) > 0:
            symbolcount = aux[0]['NumberOfRelocations'].int()
            if sectioncount != symbolcount:
                logging.warning("number of relocations ({:d}) for section {:s} differs from section definition ({:d})".format(symbolcount, sym['Name'].str(), sectioncount))
                logging.warning(aux[0])
                print('failed with relocated section {!r}'.format(section))
                continue
        print('successfully relocated section {!r}'.format(section))

    print('-'*20 + 'adding some symbols')
    ## reassign some symbols
    sy = sst.assign('_TlsAlloc@0', 0xcccccccc)
    print('added symbol', sy)
    sy = sst.assign('.text', 0x4010000)
    print('added symbol', sy)

    print('-'*20 + 'printing all symbol information')
    print('\n'.join(map(repr, symboltable)))

    def formatrelocation(relo, symboltable):
        symbol = symboltable[ relo['SymbolTableIndex'].int() ]
        return '\n'.join([repr(symbol), repr(relo)]) + '\n'

    ### everything from the section's perpsective
    print('-'*20 + 'printing all relocations')
    sections = []
    for section in coff['Sections']:
        relocations, data = section['PointerToRelocations'].d, section.data().l
        sections.append((data.serialize(), relocations))    # save for later

    ## do relocations for every section
    for section, sdr in zip(coff['Sections'], sections):
        data, relocations = sdr
        for r in relocations.load():
            print(r)
            data = r.relocate(data, symboltable)
        continue

    ## print out results
    print('-'*20 + 'printing relocated sections')
    for section in coff['Sections']:
        print(section['Name'].str())
        print(ptypes.utils.indent('\n'.join(map(lambda x: formatrelocation(x, symboltable), section['PointerToRelocations'].d.l))))
        print(section.data())

    if False:
        print('-'*20 + 'dumping relocated sections')
        for index in range( len(sections) ):
            section = sections[index]

            name = ptypes.utils.strdup(section['Name'].serialize(), terminator=b'\0')
            sys.stdout.write(name)
            if index in sym_static.keys():
                sym,aux = sym_static[index]
                print(sym['Name'].str(), sym['SectionNumber'].int(), int(sym['Value']))
                data = section.getrelocateddata(symboltable)
            else:
                data = section.data().serialize()
                print()

    #        print(ptypes.utils.hexdump( section.getdata().serialize() ))
            print(ptypes.utils.hexdump( data ))

            x = file("{:s}.section".format(name[1:]), 'wb')
            x.write(data)
            x.close()
