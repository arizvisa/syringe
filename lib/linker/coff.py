import os,array
import pecoff,ptypes,bitmap
from warnings import warn       # XXX: i really should learn to use this module correctly...

from store import *

####################### please don't look below this line
class object(store):
    value = pecoff.Object.File
    symbols = None          #pecoff.Object.definitions.Symbols

    def open(self, filename):
        return self.load(pecoff.Object.open(filename, mode='rb'), os.path.basename(filename))

    def load(self, pcoff, modulename):
        self.modulename = modulename
        self.value = pcoff.load()
        self.symbols = self.value['Header'].getsymbols().load()
        self.update( self.__getnamespace() )

        # we'll tack our sized symbols onto the end of this section
        #       yeah, this is fucking really hacky...hey, first linker with
        #       non-executable files. :>
        hiddensegmentname = None
        if self.__gethiddensegmentlength() > 0:
            for n in self.listsegments():
                if self.getsegmentprotection(n) == self.__gethiddensegmentprotection():
                    hiddensegmentname = n
                    break
                continue
        self.hiddensegmentname = hiddensegmentname
        return self

    def __sym_externals(self):
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if sectionnumber is None and storageclass == 2 and int(s['Value']) == 0:
                yield s
            continue
        return

    def __sym_globals(self):
        sectionarray = self.value['Sections']
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if storageclass != 2:
                continue
            if (sectionnumber is None) and (int(s['Value']) == 0):
                continue
            yield s
        return

    def __sym_locals(self):
        sectionarray = self.value['Sections']
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if sectionnumber is None:       # XXX: should this be testing for s['Value'] too?
                continue

            if storageclass in [ 3, 104, 6 ]:
                yield s
            continue
        return

    def getglobalsbysegmentname(self, name=None):
        res = []
        sectionarray = self.value['Sections']
        for s in self.__sym_globals():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if (sectionnumber is None):
                if (int(s['Value']) != 0):
                    res.append( s['Name'].get() )
                continue

            section = sectionarray[sectionnumber]
            if name is None or section['Name'].get() == name:
                res.append( s['Name'].get() )
            continue
        return res

    def getlocalsbysegmentname(self, name=None):
        res = []
        sectionarray = self.value['Sections']
        for s in self.__sym_locals():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            section = sectionarray[sectionnumber]
            if name is None or section['Name'].get() == name:
                res.append( s['Name'].get() )
            continue
        return res

    def getexternals(self):
        res = []
        for s in self.__sym_externals():
            res.append( s['Name'].get() )
        return res

    def __getnamespace(self):
        segmentnames = set(self.listsegments())
        namespace = dict([(n,None) for n in segmentnames])
        
        # locals
        for s in self.__sym_locals():
            name = s['Name'].get()
            namespace[name] = int(s['Value'])

        # globals
        for s in self.__sym_globals():
            name = s['Name'].get()
            namespace[name] = int(s['Value'])

        # externals
        for s in self.__sym_externals():
            name = s['Name'].get()
            namespace[name] = None
        return namespace
        
    if False:
        def __getnamespace(self):
            segmentnames = set(self.listsegments())
            symbols = self.symbols
            namespace = dict([(n,None) for n in segmentnames])
            for sym in symbols.get():
                name = sym['Name'].get()
                storageclass = int(sym['StorageClass'])

                sectionnumber = sym['SectionNumber'].get()
                if sectionnumber is None or name in segmentnames:
                    namespace[name] = None
                    continue

                if storageclass in ([2,3,6] + [100,101,104]):
                    namespace[name] = int(sym['Value'])
                    continue

                warn("ignoring symbol %s with untested storageclass %s"% (name, str(sym['StorageClass'])))

            namespace.update( dict([(n,None) for n in self.listsegments()]) )
            return namespace

    def listsegments(self):
        result = []
        for section in self.value['Sections']:
            n = int(section['Characteristics'])
            if n&0x800 or n&0x2000000 or n&0x200 or n&0x80:    #LNK_REMOVE or MEM_DISCARDABLE or LNK_INFO 
                continue
            result.append( section['Name'].get() )
        return result

    ## segments
    def getsegment(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        data = section['PointerToRawData'].d.load().serialize()

        diff = section.getloadedsize() - len(data)
        assert diff >= 0, 'Loaded size (%x) < Segment size (%x)'% (section.getloadedsize(), len(data))
        data += '\x00' * diff
        if self.hiddensegmentname == name:  # hidden segment hack
            data += self.__gethiddensegment()
        return data

    def getsegmentlength(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        if self.hiddensegmentname == name:  # hidden segment hack
            return section.getloadedsize() + self.__gethiddensegmentlength()
        return section.getloadedsize()

    def __gethiddensegment(self):
        return '\x00'*self.__gethiddensegmentlength()

    def __gethiddensegmentlength(self):
        size = 0
        for s in self.__sym_globals():
            sectionnumber = s['SectionNumber'].get()
            if sectionnumber is None:
#                print s['Name'].get(), int(s['Value'])
                size += int(s['Value'])
            continue
        return size

    def __gethiddensegmentprotection(self):
        return 6        # we just assume we'll need read/write

    def __gethiddensymbols(self):
        res = []
        for s in self.__sym_globals():
            sectionnumber = s['SectionNumber'].get()
            if sectionnumber is None:
                res.append(s)
            continue
        return res

    def getsegmentprotection(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        chars = section['Characteristics']
        x = int(chars)

        if x&chars.CNT_CODE:
            readable,writeable,executable = True, False, True
        elif x&chars.CNT_INITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        elif x&chars.CNT_UNINITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        else:
            raise NotImplementedError('Unknown protection for segment %s : %s : %s'% (self.modulename, name, repr(chars)))

        binarydigits = ['0', '1']
        res = [ binarydigits[x] for x in (readable,writeable,executable)]
        return int(''.join(res), 2)

    def relocatesegment(self, name, data, baseaddress):
        section = self.value['Sections'].getsectionbyname(name)
        relocations = section.getrelocations().load()
        symboltable = self.symbols['Symbols']

        ## assign namespace stuff
        self[name] = baseaddress
        namespace = dict(self)

        ## update symbols for the relocator
        for sym in self.__getsymbolsbysection(section):
            symbolname = sym['Name'].get()
            namespace[symbolname] = self[symbolname] + baseaddress
        namespace[name] = baseaddress

        ## update the symbols that we tacked onto the end of this section
        if self.hiddensegmentname == name:  # hidden segment hack
            ofs = baseaddress + section.getloadedsize()
            for sym in self.__gethiddensymbols():
                symbolname = sym['Name'].get()
                namespace[symbolname] = ofs
                ofs += int(sym['Value'])
            pass

        ## relocate them
        for r in relocations:
            sym = symboltable[ int(r['SymbolTableIndex']) ]
            data = r.relocate(data, symboltable, namespace)

        ## and now back to us
        for sym in self.__getsymbolsbysection(section):
            symbolname = sym['Name'].get()
            self[symbolname] = namespace[symbolname]

        ## copy those other symbols back
        if self.hiddensegmentname == name:  # hidden segment hack
            for sym in self.__gethiddensymbols():
                symbolname = sym['Name'].get()
                self[symbolname] = namespace[symbolname]
            pass

        return data

    def __getsymbolsbysection(self, section):
        sectionnumber = section.parent.value.index(section)
        return [ x for x in self.symbols.get() if x['SectionNumber'].get() == sectionnumber]


class executable(store):
    value = pecoff.Executable.File
    symbols = None          #pecoff.Object.definitions.Symbols

    exports = imports = relocations = forwards = None

    def open(self, filename):
        return self.load(pecoff.Executable.open(filename, mode='rb'), os.path.basename(filename))

    def load(self, peexecutable, modulename):
        warn("linker.coff.executable's symbol table is probably broken.")
        self.modulename = modulename
        self.value = peexecutable.load()['Pe']
        self.imports = self.__getimports()

        # XXX: this will need to be rewritten
        self.exports,self.forwards = self.__getexportsymbols()
        self.__globalcache,self.__importcache,self.__forwardcache = self.__getglobalsandforwardcache()

        self.relocations = self.__getrelocations()
        self.update( self.__getnamespace() )
        return self

    def getexternals(self):
        splitter = self.__splitModuleName
        return ['%s!%s'% (module,name) for module,hint,name,address in self.imports] +\
               ['%s'%(a) for a,b in self.__importcache.values()]

    def __getnamespace(self):
        base = self.value.parent.getoffset()
        namespace = {}

        namespace.update( dict([(k,None) for k in self.getexternals()]) )
        namespace.update( dict([(n,None) for n in self.listsegments()]) )
        namespace.update( self.__getexportnamespace() ) # this might overwrite one of the previous values
        return namespace

    # forward rva handling code
    def __splitModuleName(self, n):
        module,name = n.split('.', 1)
        if name.startswith('#'):
            try:
                name = 'Ordinal%d'% int(n[1:])
            except ValueError:
                name = n[1:]        # XXX: for HUNIMPL.#UNIMPL_SHCreateStreamWrapper
            pass
        return module.lower() + '.dll',name

    def __getforward_exports(self):
        modulename = self.modulename
        for ordinal,name,ordinalstring,value in self.forwards.values():
            fullname = '%s!%s'% (modulename, name)
            yield ordinal,fullname
        return

    def __getforward_imports(self):
        modulename = self.modulename
        for ordinal,name,ordinalstring,value in self.forwards.values():
            value = self.__splitModuleName(value)
            fullname = '%s!%s'% value
            yield ordinal,fullname
        return

    def __getforward_ordinalnames(self):
        modulename = self.modulename
        for ordinal,name,ordinalstring,value in self.forwards.values():
            fullname = '%s!%s'% (modulename,ordinalstring)
            yield ordinal,fullname
        return

    def __getexport_ordinals(self):
        modulename = self.modulename
        for ordinal,name,ordinalstring,value in self.exports.values():
            fullname = '%s!%s'% (modulename, ordinalstring)
            yield ordinal,fullname
        return

    def __getexport_names(self):
        modulename = self.modulename
        for ordinal,name,ordinalstring,value in self.exports.values():
            fullname = '%s!%s'% (modulename, name)
            yield ordinal,fullname
        return

    # XXX: i fucking hate this code. i swear it was designed at first...
    def __getglobalsandforwardcache(self):
        # our components
        forward_lookup_exports = list(self.__getforward_exports())
        forward_lookup_imports = list(self.__getforward_imports())
        forward_lookup_ordinalnames = list(self.__getforward_ordinalnames())

        export_lookup_ordinals = list(self.__getexport_ordinals())
        export_lookup_names = list(self.__getexport_names())

        # to dicts
        forward_lookup_exports,forward_lookup_imports,forward_lookup_ordinalnames,export_lookup_ordinals,export_lookup_names = dict(forward_lookup_exports),dict(forward_lookup_imports),dict(forward_lookup_ordinalnames),dict(export_lookup_ordinals),dict(export_lookup_names)

        # alias lookups keyed by ordinal
        namelookup = dict(export_lookup_names.items() + forward_lookup_exports.items())
        ordinallookup = dict(export_lookup_ordinals.items() + forward_lookup_ordinalnames.items())

        # any assignment to an import will update the name,ordinalstring
        cache_importname = ( (forward_lookup_imports[ordinal], (namelookup[ordinal], ordinallookup[ordinal])) for ordinal,name in forward_lookup_exports.items() )

        # an ordinal will update the name,ordinalstring
        cache_ordinalname = ( (name, (namelookup[ordinal],ordinallookup[ordinal])) for ordinal,name in export_lookup_ordinals.items()+forward_lookup_ordinalnames.items() )

        # a name will update the name,ordinalstring
        cache_exportname = ( (name, (namelookup[ordinal],ordinallookup[ordinal])) for ordinal,name in export_lookup_names.items() )

        # for the forwards
        cache_forwardexport = []
        for ordinal,name in forward_lookup_exports.items():
            forwarded = forward_lookup_imports[ordinal]

            ordinalstring,namestring = ordinallookup[ordinal],namelookup[ordinal]
            cache_forwardexport.append( (namestring, (forwarded, None)) )
            cache_forwardexport.append( (ordinalstring, (forwarded, None)) )

        globalcache = dict()
        globalcache.update(cache_ordinalname)
        globalcache.update(cache_exportname)

        importcache = dict(cache_forwardexport)
       
        # for assignments to a forward
        forwardcache = dict(cache_importname)
        return globalcache,importcache,forwardcache

    ## exports
    def __getexportnamespace(self):
        base = self.value.parent.getoffset()
        namespace = {}

        for o,name in list(self.__getexport_names())+list(self.__getexport_ordinals()):
            _,_,_,v = self.exports[o]
            namespace[name]  = base+v

        for o,forwardname in list(self.__getforward_exports())+list(self.__getforward_ordinalnames()):
            _,name,_,v = self.forwards[o]
            namespace[name] = namespace[forwardname] = None
        return namespace

    def __getexportsymbols(self):
        exportDirectory = self.value['OptionalHeader']['DataDirectory'][0].load()
        if not exportDirectory.valid():
            return []

        ied = exportDirectory.get().load()

        exported,forwarded = {},{}
        for (ordinal,name,ordinalstring,value) in ied.enumerateAllExports():
            if type(value) is str:
                # forwarded
                forwarded[ordinal] = (ordinal,name,ordinalstring,value)
                continue
            exported[ordinal] = (ordinal,name,ordinalstring,value)
        return exported,forwarded

    ## imports
    def __getimportmodules(self):
        result = []
        importDirectory = self.value['OptionalHeader']['DataDirectory'][1].load()
        if not importDirectory.valid():
            return result

        importDirectory = importDirectory.get()
        for module in importDirectory.load()[:-1]:
            modulename = module['Name'].d.load().get().lower()
            result.append( (modulename, module.fetchimports()) )

        return result

    def __getimports(self):
        result = []
        for modulename,items in self.__getimportmodules():
#            print '..loading import module %s'% modulename
            # modulename, name, virtual addresses
            for hint,name,address in items:
                result.append( (modulename, hint, name, address) )
            continue
        return result

    def __getrelocations(self):
        relo = self.value['OptionalHeader']['DataDirectory'][5]
        if relo.valid():
            return relo.get().load()
        return []

    def listsegments(self):
        sections = self.value['Sections']
        return [ x['Name'].get() for x in sections if int(x['Characteristics']) & 0x2000000 == 0]

    def getlocalsbysegmentname(self, name=None):
        # XXX: if we can parse symbol information for this executable, we might
        # be able to get more function granularity to populate this list
        return []

    def getglobalsbysegmentname(self, name=None):
        if not name:
            return self.__globalcache.keys() + self.__importcache.keys()

        section = self.value['Sections'].getsectionbyname(name)
        min = int(section['VirtualAddress'])
        max = min + int(section['VirtualSize'])

        result = []
        for o,name,ordinalstring,value in self.exports.values():
            if value >= min and value < max:
                result.append('%s!%s'%(self.modulename,name))
                result.append('%s!%s'%(self.modulename,ordinalstring))
            continue
        return result

    def getsegment(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        data = section['PointerToRawData'].d.load().serialize()

        diff = section.getloadedsize() - len(data)
        assert diff >= 0, 'Loaded size (%x) < Segment size (%x)'% (section.getloadedsize(), len(data))
        data += '\x00' * diff
        return data

    def getsegmentlength(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        return section.getloadedsize()

    def getsegmentprotection(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        chars = section['Characteristics']
        x = int(chars)

        if x&chars.CNT_CODE:
            readable,writeable,executable = True, False, True
        elif x&chars.CNT_INITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        elif x&chars.CNT_UNINITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        else:
            raise NotImplementedError('Unknown protection for %s'% repr(characteristics))

        binarydigits = ['0', '1']
        res = [ binarydigits[x] for x in (readable,writeable,executable)]
        return int(''.join(res), 2)

    def relocatesegment(self, name, data, baseaddress):
        ## assign some defaults
        section = self.value['Sections'].getsectionbyname(name)
        self[name] = baseaddress

        ## do relocations
        data = self.__updateimports(data, section)
        if self.relocations:
            data = self.relocations.relocate(data, section, self)

        ## update symbols
        for n in self.getglobalsbysegmentname(name):
            res = self[n] - int(section['VirtualAddress'])
            self[n] = res + baseaddress

        ## update forwarded imports
        for name,aliases in self.__importcache.items():
            fullname,ordinal = aliases
            assert ordinal is None
            self[name] = self[fullname]

        return data

    def __updateimports(self, data, section):
        assert type(data) is str

        data = array.array('c', data)
        undefinedmodulelist = set()
        ## update specified data in specified section with values in namespace
        for module,hint,name,address in self.imports:
            if not section.containsaddress(address):
                continue

            key = '%s!%s'% (module,name)
            value = self[key]
            if value is None:
                undefinedmodulelist.add(module)
                continue

            # convert value to string
            res = bitmap.new( value, 4*8 )
            string = ''
            while res[1] > 0:
                res,value = bitmap.consume(res, 8)
                string += chr(value)
            value = string

            # write it back into data
            o = address - int(section['VirtualAddress'])
            data[o:o+4] = array.array('c',value)

            # print module,hex(hint),name,hex(address)

        if undefinedmodulelist and False:
            print self.modulename + ' : modules that are undefined modules : ' + ', '.join(undefinedmodulelist)
        return data.tostring()

    def __setitem__(self, key, value):
        parent_setitem = super(coffexecutable, self).__setitem__
        if key in self.__importcache:
            fullname,ordinalstring = self.__importcache[key]
            self[fullname] = value  # recurse
#            parent_setitem(fullname, value)
            assert ordinalstring is None
            return parent_setitem(key,value)

        if key in self.__forwardcache:
            fullname,ordinalstring = self.__forwardcache[key]
            parent_setitem(fullname, value)
            parent_setitem(ordinalstring, value)
            return parent_setitem(key,value)

        return parent_setitem(key,value)

class library(container):
    value = pecoff.Archive.File
    def open(self, filename):
        return self.load(pecoff.Archive.open(filename, mode='rb'), os.path.basename(filename))

    def load(self, cofflibrary, modulename):
        warn("linker.coff.library's import symbol table updating is broken.")
        self.modulename = modulename
        self.value = cofflibrary.load()
        self.stores,self.importmembers = self.__getstoresandimportmembers()
        self.imports = self.__getimports(self.importmembers)
        self.update( self.__getnamespace() )
        return self

    def getmembercount(self):
        return self.value.getmembercount()

    def getmember(self, index):
        m = self.value.getmember(index).load()
        data = self.value.getmemberdata(index)
        name = 'Member[%d]'% index
        offset = m.getoffset() + m.size()
        if data[0:4] == '\x00\x00\xff\xff':
            res = m.newelement(pecoff.Archive.ImportMember, name, offset)
        else:
            res = m.newelement(pecoff.Object.File, name, offset)
        #res.deserialize(data)
        return res

    def listsegments(self):
        result,d = ([], set())
        for st in self.stores:
            for n in st.listsegments():
                try:
                    n = n[:n.index('$')]
                except ValueError, e:
                    pass

                if n not in d:
                    result.append(n)
                    d.add(n)
                continue
            continue
        return result

    def __getimports(self, members):
        result = {}
        for module,name,ordinal,headertype in members:
            if module not in result:
                result[module] = []
            result[module].append(name)
        return result

    def __getlocalimports(self):
        return [(module,name) for module,name,ordinal,headertype in self.importmembers]

    def getglobalsbysegmentname(self, name):
        result = []
        # globals by segment
        if name == '.idata':
            result.extend( ('__imp__%s'%(n) for m,n in self.__getlocalimports()) )
            return result

        if name:
            for st in self.stores:
                segments = (x for x in st.listsegments() if x == name or x.startswith(name+'$'))
                for segmentname in segments:
                    result.extend( st.getglobalsbysegmentname(segmentname) )
                continue
            return result

        # all globals
        for st in self.stores:
            result.extend( st.getglobalsbysegmentname(None) )
        result.extend( ('__imp__%s'%(n) for m,n in self.__getlocalimports()) )
        return result

    def getlocalsbysegmentname(self, name):
        raise NotImplementedError("Doesn't make sense to fetch locals for a coff container")

    def __getstoresandimportmembers(self):
        objs = [x for x in self.value.fetchmembers()]
        stores = [coffstore() for x in objs]
        [ st.load(o, repr(st)) for o,st in zip(objs,stores) ]

        # convert import names to dll looking names
        imports = [ (m, n[1:], o, h) for m,n,o,h in self.value.fetchimports() ]

        return (stores, list(imports))

    def getexternals(self):
        return ['%s!%s'% (module,name) for module,name,ordinal,headertype in self.importmembers]# + self.listsegments()

    def __getnamespace(self):
        namespace = {}
        for st in self.stores:
            r = [(n,st[n]) for n in st.getglobals()]
            namespace.update(dict(r))

        for fullname in self.getexternals():
            namespace[fullname] = None

        for module,name in self.__getlocalimports():
            namespace['__imp__%s'% name] = None

        namespace.update( dict([(n,None) for n in self.listsegments()]) )
        return namespace

    def getsegmentprotection(self, name):
        if name == '.idata':
            return 6            # rw-
        return super(coffcontainer, self).getsegmentprotection(name)

    def __getsegmentsbyname(self, name, store):
        # for handling coff segment naming with '$'
        result = []
        for n in store.listsegments():
            if (n == name) or ('$' in n and n[:n.index('$')] == name):
                result.append(n)
            continue
        return result

    def getsegmentlength(self, name):
        if name == '.idata':
            return self.__getiatlength()
        return self.__getsegmentlength(name)

    def __getsegmentlength(self, name):
        result = 0
        for st in self.stores:
            result += reduce(lambda a,b: a+b, [st.getsegmentlength(n) for n in self.__getsegmentsbyname(name,st)], 0)
        return result

    def __getiatlength(self):
        '''this will return the size req'd for just the iat'''
        imports = [True for name in self.getexternals()]
        return len(imports) * 4

    def getsegment(self, name):
        if name == '.idata':
            return self.__getimporttable()
        return self.__getsegment(name)

    def __getsegment(self, name):
        segments = self.getsegment_list(name)
        result = []
        for name,store,offset,length in segments:
            result.append(store.getsegment(name))
        return ''.join(result)

    def __getsegment_list(self, name):
        # build a list of all segments with the specified name
        segments = []
        for i in xrange( self.getmembercount() ):
            st = self.getmember(i)
            segments.extend( ((n,st) for n in self.__getsegmentsbyname(name,st)) )

        # sort them         (XXX: should probably sort by number instead of name
        segments.sort(cmp=lambda x,y: cmp(int(x[len(name)+1:]),int(y[len(name)+1:])))

        # precalculate their lengths and offset
        result = []
        ofs = 0
        for name,store in segments:
            length = store.getsegmentlength(name)
            result.append( (name, store, ofs, length) )
            ofs += length
        return result

    def relocatesegment(self, name, data, baseaddress):
        self[name] = baseaddress
        if name == '.idata':
            res = self.__relocateimporttable(data, baseaddress)
        else:
            res = self.__relocatesegment(name, data, baseaddress)
        return res

    def __relocatesegment(self, name, data, baseaddress):
        raise NotImplementedError("This is broken, probably")

        segments = self.getsegment_list(name)
        lookup = dict([(name,offset) for name,store,offset in segments])

        for _name,store,offset,size in segments:
            globals = store.getglobalsbysegmentname(name)
            chunk = data[offset:offset+size]

            # XXX: enumerate all segment bases
            namespace = dict(self)

            chunk = store.relocatesegment(name, chunk, namespace)

            # write any globals back that we might want
            chunk = store.relocatesegment(name, chunk, newbaseaddress)

        return data

    def __getimporttable(self):
        '''this will allocate the import table and return it, but it doesn't really count....'''

        # collect all addresses user chose to give us
        importaddresses = [(module,name,ordinal) for module,name,ordinal,headertype in self.importmembers]

        return '\x00' * (4*len(importaddresses))

    def __relocateimporttable(self, data, baseaddress):
        # collect all addresses user chose to give us
        importaddresses = [(module,name,self[external]) for (module,name),external in zip(self.__getlocalimports(), self.getexternals())]

        undefinedmodules = set( (module for module,name,value in importaddresses if value is None) )
        if undefinedmodules:
            # XXX: display the number of undefined symbols in each module
            raise ValueError('The following modules are undefined: %s'% repr(undefinedmodules))

        data = array.array('c', data)
        o = 0
        for (module,name,value) in importaddresses:
            res = bitmap.new( value, 4*8 )
            string = ''
            while res[1] > 0:
                res,value = bitmap.consume(res, 8)
                string += chr(value)
            value = string

            data[o:o+4] = array.array('c',value)
            self['__imp__%s'% name] = baseaddress+o
            o += 4
        return data.tostring()

    def __setitem__(self, key, value):
        # XXX: this is cheating, but whatever. fuck it.
        if key == '.idata' and value is not None:
            importaddresses = [(module,name,self[external]) for (module,name),external in zip(self.__getlocalimports(), self.getexternals())]
            o = 0
            for m,n,v in importaddresses:
                self['__imp__%s'% n] = value+o
                o += 4
            return super(coffcontainer, self).__setitem__(key, value)
        return super(coffcontainer, self).__setitem__(key, value)
