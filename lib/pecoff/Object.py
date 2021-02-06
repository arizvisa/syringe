import ptypes
from ptypes import *

from . import portable
from .headers import *

import logging

class Signature(portable.IMAGE_FILE_HEADER):
    _fields_ = [
        (Machine, 'Machine'),
        (uint16, 'NumberOfSections'),
    ]

    def isImportSignature(self):
        return all((self['Machine'].li.int() == self['Machine'].byname('UNKNOWN'), self['NumberOfSections'].li.int() == 0xffff))

class ObjectHeader(portable.IMAGE_FILE_HEADER):
    _fields_ = portable.IMAGE_FILE_HEADER._fields_[2:]

class ImportHeader(pstruct.type):
    _fields_ = [
        (uint16, 'Version'),
        (Machine, 'Machine'),
        (TimeDateStamp, 'TimeDateStamp'),
        (uint32, 'SizeOfData'),
    ]

class ImportData(pstruct.type):
    class Type(pbinary.struct):
        class _type(pbinary.enum):
            _width_ = 2
            _values_ = [
                ('IMPORT_CODE', 0),
                ('IMPORT_DATA', 1),
                ('IMPORT_CONST', 2),
            ]
        class _name(pbinary.enum):
            _width_ = 3
            _values_ = [
                ('IMPORT_ORDINAL', 0),
                ('IMPORT_NAME', 1),
                ('IMPORT_NAME_NOPREFIX', 2),
                ('IMPORT_NAME_UNDECORATE', 3),
            ]
        _fields_ = [
            (11, 'Reserved'),
            (_name, 'Name'),
            (_type, 'Type'),
        ]

    _fields_ = [
        (portable.imports.word, 'Ordinal/Hint'),
        (Type, 'Type'),
        (pstr.szstring, 'Symbol'),
        (pstr.szstring, 'Library'),
    ]

class FileSegmentEntry(pstruct.type):
    def __Data(self):
        section = self.Section
        return dyn.block(section['SizeOfRawData'].li.int())

    def __Relocations(self):
        section = self.Section
        return dyn.clone(portable.relocations.RelocationTable, length=section['NumberOfRelocations'].int())

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
        p = self.getparent(Header)
        sections = p['Sections'].li
        section = sections[len(self.value)]
        return dynamic.clone(FileSegmentEntry, Section=section)

class File(pstruct.type, Header, ptype.boundary):
    """Coff Object File"""
    def __Sections(self):
        sig = self['Signature'].li
        count = 0 if sig.isImportSignature() else sig['NumberOfSections'].int()
        return dynamic.clone(portable.SectionTableArray, length=count)

    def __Segments(self):
        sig = self['Signature'].li
        if sig.isImportSignature():
            return ImportData
        return dynamic.clone(SegmentTableArray, length=sig['NumberOfSections'].int())

    _fields_ = [
        (Signature, 'Signature'),
        (lambda s: ImportHeader if s['Signature'].li.isImportSignature() else ObjectHeader, 'Header'),
        (__Sections, 'Sections'),

        # FIXME: we're actually assuming that these fields are packed and
        #        aligned, so there's a large chance that that empty space
        #        could exist in between each item, or the segments could
        #        be in a completely different order.
        (__Segments, 'Segments'),
        (portable.symbols.SymbolTableAndStringTable, 'SymbolTable'),
    ]

    def FileHeader(self):
        '''Return the Header which contains a number of sizes used by the file.'''
        return self['Header']

    def Machine(self):
        sig = self['Signature']
        return self['Header']['Machine'] if sig.isImportSignature() else sig['Machine']

    def isImportLibrary(self):
        sig = self['Signature']
        return sig.isImportSignature()

if __name__ == '__main__':
    ## parse the file
    import sys, pecoff, ptypes
    from ptypes import provider
    import logging

    print('-'*20 + 'loading file..')
    coff = pecoff.Object.File(source=provider.file(sys.argv[1]))
    coff.load()

    __name__ = 'ImportLibrary' if coff.isImportLibrary() else 'CoffObject'

if __name__ == 'ImportLibrary':
    print(coff['Signature'])
    print(coff['Header'])
    print(coff['Data'])

if __name__ == 'CoffObject':
    print(coff['Signature'])
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
            sym_static[idx] = (sym, sst.AuxiliarySymbols(name))
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
                logging.warn("number of relocations ({:d}) for section {:s} differs from section definition ({:d})".format(symbolcount, sym['Name'].str(), sectioncount))
                logging.warn(aux[0])
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
        print(ptypes.utils.hexdump(section.data()))

    if False:
        print('-'*20 + 'dumping relocated sections')
        for index in range( len(sections) ):
            section = sections[index]

            name = ptypes.utils.strdup(section['Name'].serialize(), terminator=b'\0')
            __import__.six.print_(name, end='')
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
