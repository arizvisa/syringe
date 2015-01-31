import ptypes,portable
from warnings import warn

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class File(ptypes.pstruct.type, ptypes.ptype.boundary):
    """Coff Object File"""
    def __Data(self):
        sections = self['Sections'].li
        class result(ptypes.parray.type):
            length = len(sections)
            def _object_(self):
                sect = sections[len(self.value)]
                return ptypes.dynamic.clone(ptypes.dynamic.block(sect['SizeOfRawData'].li.num()), Section=sect, SectionName=sect['Name'].str())
        return result

    _fields_ = [
        (portable.FileHeader, 'Header'),
        (lambda s: ptypes.dynamic.clone(portable.SectionTableArray, length=s['Header'].li['NumberOfSections'].num()), 'Sections'),
        (__Data, 'Data'),
    ]

if __name__ == '__main__':
    ## parse the file
    import sys, pecoff, ptypes
    from ptypes import provider

    print '-'*20 + 'loading file..'
    coff = pecoff.Object.File()
    coff.source = provider.file('../../obj/test.obj')
    coff.load()
    print coff['Header']
    print coff['Sections']

    ### check everything from the symbol table's perspective
    sst = coff['Header'].getsymbols()
    sst.load()

    symboltable = sst['Symbols']

    print '-'*20 + 'printing external symbols'
    ## build list of external symbols
    sym_external = {}
    for name in sst.names():
        v = sst.getSymbol(name)
        if int(v['StorageClass']) == 2:
            sym_external[name] = v
        continue

    print '\n'.join(map(repr, sym_external.values()))

    print '-'*20 + 'printing statically defined symbols'
    ## build list of static symbols
    sym_static = {}
    for name in sst.names():
        v = sst.getSymbol(name)
        if int(v['StorageClass']) == 3 and int(v['Value']) == 0:
            num = v['SectionNumber'].num()
            sym_static[num] = (v, sst.getaux(name))
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
    for index,(sym,aux) in sym_static.items():
        section = sections[index]
        sectioncount = int(section['NumberOfRelocations'])
        if len(aux) > 0:
            symbolcount = int(aux[0]['NumberOfRelocations'])
            if sectioncount != symbolcount:
                warn('number of relocations (%d) for section %s differs from section definition (%d)'% (symbolcount,sym['Name'].str(),sectioncount))
        print 'relocated section %s'% repr(section)
        continue

    print '-'*20 + 'adding some symbols'
    ## reassign some symbols
    sst.assign('_TlsAlloc@0', 0xcccccccc)
    sst.assign('.text', 0x4010000)

    print '-'*20 + 'printing all symbol information'
    print '\n'.join(map(repr, symboltable))

    def formatrelocation(relo, symboltable):
        symbol = symboltable[ int(relo['SymbolTableIndex']) ]
        return '\n'.join([repr(symbol), repr(relo)]) + '\n'

    ### everything from the section's perpsective
    print '-'*20 + 'printing all relocations'
    for section in coff['Sections']:
        relocations = section.getrelocations()
        data = section.data().load()
        section.data, section.relocations = data.serialize(), relocations   # save for later
        continue
        
    ## do relocations for every section
    for section in coff['Sections']:
        data = section.data
        for r in section.relocations.load():
            print r
            section.data = r.relocate(section.data, symboltable)
        continue
        
    ## print out results
    print '-'*20 + 'printing relocated sections'
    for section in coff['Sections']:
        print section['Name'].str()
        print ptypes.utils.indent('\n'.join(map(lambda x: formatrelocation(x, symboltable), section.relocations)))
        print ptypes.utils.hexdump(section.data)

    if False:
        print '-'*20 + 'dumping relocated sections'
        for index in range( len(sections) ):
            section = sections[index]

            name = ptypes.utils.strdup( section['Name'].serialize(), terminator='\x00')
            print name,
            if index in sym_static.keys():
                sym,aux = sym_static[index]
                print sym['Name'].str(), sym['SectionNumber'].num(), int(sym['Value'])
                data = section.getrelocateddata(symboltable)
            else:
                data = section.data().serialize()
                print 

    #        print ptypes.utils.hexdump( section.getdata().serialize() )
            print ptypes.utils.hexdump( data )

            x = file('%s.section'% name[1:], 'wb')
            x.write(data)
            x.close()
