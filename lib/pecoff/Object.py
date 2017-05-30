import ptypes
from ptypes import *

from . import portable
from .__base__ import *

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class Signature(portable.FileHeader):
    _fields_ = [
        (Machine, 'Machine'),
        (uint16, 'NumberOfSections'),
    ]

    def isImportSignature(self):
        return all((self['Machine'].int() == self['Machine'].byname('UNKNOWN'), self['NumberOfSections'].int() == 0xffff))

class ObjectHeader(portable.FileHeader):
    _fields_ = portable.FileHeader._fields_[2:]

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
            width = 2
            _values_ = [
                ('IMPORT_CODE', 0),
                ('IMPORT_DATA', 1),
                ('IMPORT_CONST', 2),
            ]
        class _name(pbinary.enum):
            width = 3
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

class File(pstruct.type, Header, ptype.boundary):
    """Coff Object File"""
    def __Sections(self):
        sig = self['Signature'].li
        count = 0 if sig.isImportSignature() else sig['NumberOfSections'].int()
        return dynamic.clone(portable.SectionTableArray, length=count)

    def __Data(self):
        sig = self['Signature'].li
        if sig.isImportSignature():
            return ImportData

        sections = filter(lambda n: not n['Characteristics']['CNT_UNINITIALIZED_DATA'], self['Sections'].li)
        class result(parray.type):
            length = len(sections)
            def _object_(self):
                sect = sections[len(self.value)]
                return dynamic.clone(dynamic.block(sect['SizeOfRawData'].li.int()), Section=sect, SectionName=sect['Name'].str())
        return result

    _fields_ = [
        (Signature, 'Signature'),
        (lambda s: ImportHeader if s['Signature'].li.isImportSignature() else ObjectHeader, 'Header'),
        (__Sections, 'Sections'),
        (__Data, 'Data'),
    ]

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

    print '-'*20 + 'loading file..'
    coff = pecoff.Object.File(source=provider.file(sys.argv[1]))
    coff.load()

    __name__ = 'ImportLibrary' if coff.isImportLibrary() else 'CoffObject'

if __name__ == 'ImportLibrary':
    print coff['Signature']
    print coff['Header']
    print coff['Data']

if __name__ == 'CoffObject':
    print coff['Signature']
    print coff['Header']
    print coff['Sections']

    ### check everything from the symbol table's perspective
    sst = coff['Header']['PointerToSymbolTable'].d
    print sst
    sst.load()

    symboltable = sst['Symbols']

    print '-'*20 + 'printing external symbols'
    ## build list of external symbols
    sym_external = {}
    for name in sst.names():
        v = sst.getSymbol(name)
        if v['StorageClass'].int() == v['StorageClass'].byname('EXTERNAL'):
            sym_external[name] = v
        continue

    print '\n'.join(map(repr, sym_external.values()))

    print '-'*20 + 'printing statically defined symbols'
    ## build list of static symbols
    sym_static = {}
    for name in sst.names():
        sym = sst.getSymbol(name)
        if sym['StorageClass'].int() == sym['StorageClass'].byname('STATIC') and sym['Value'].int() == 0:
            idx = sym.getSectionIndex()
            sym_static[idx] = (sym, sst.getAuxiliary(name))
        continue

    for x in sym_static.keys():
        sym,aux = sym_static[x]
        print sym
        if aux:
            print '\n'.join(map(repr,aux))

    print '-'*20 + 'check that the number of relocations in the symboltable matches the section\'s'
    ## build list of static symbols
    ## sanity check that the number of relocations are correct
    sections = coff['Sections']
    for index,(sym,aux) in sym_static.iteritems():
        section = sections[index]
        sectioncount = section['NumberOfRelocations'].int()
        if len(aux) > 0:
            symbolcount = aux[0]['NumberOfRelocations'].int()
            if sectioncount != symbolcount:
                logging.warn('number of relocations (%d) for section %s differs from section definition (%d)'% (symbolcount,sym['Name'].str(),sectioncount))
                logging.warn(aux[0])
                print 'failed with relocated section %r'% section
                continue
        print 'successfully relocated section %r'% section

    print '-'*20 + 'adding some symbols'
    ## reassign some symbols
    sy = sst.assign('_TlsAlloc@0', 0xcccccccc)
    print 'added symbol', sy
    sy = sst.assign('.text', 0x4010000)
    print 'added symbol', sy

    print '-'*20 + 'printing all symbol information'
    print '\n'.join(map(repr, symboltable))

    def formatrelocation(relo, symboltable):
        symbol = symboltable[ relo['SymbolTableIndex'].int() ]
        return '\n'.join([repr(symbol), repr(relo)]) + '\n'

    ### everything from the section's perpsective
    print '-'*20 + 'printing all relocations'
    sections = []
    for section in coff['Sections']:
        relocations, data = section['PointerToRelocations'].d, section.data().l
        sections.append((data.serialize(), relocations))    # save for later

    ## do relocations for every section
    for section, sdr in zip(coff['Sections'], sections):
        data, relocations = sdr
        for r in relocations.load():
            print r
            data = r.relocate(data, symboltable)
        continue

    ## print out results
    print '-'*20 + 'printing relocated sections'
    for section in coff['Sections']:
        print section['Name'].str()
        print ptypes.utils.indent('\n'.join(map(lambda x: formatrelocation(x, symboltable), section['PointerToRelocations'].d.l)))
        print ptypes.utils.hexdump(section.data())

    if False:
        print '-'*20 + 'dumping relocated sections'
        for index in range( len(sections) ):
            section = sections[index]

            name = ptypes.utils.strdup( section['Name'].serialize(), terminator='\x00')
            print name,
            if index in sym_static.keys():
                sym,aux = sym_static[index]
                print sym['Name'].str(), sym['SectionNumber'].int(), int(sym['Value'])
                data = section.getrelocateddata(symboltable)
            else:
                data = section.data().serialize()
                print

    #        print ptypes.utils.hexdump( section.getdata().serialize() )
            print ptypes.utils.hexdump( data )

            x = file('%s.section'% name[1:], 'wb')
            x.write(data)
            x.close()
