import pCOFF
from warnings import warn

class store(object):
    namespace = dict

    def __init__(self):
        # here's where you load and initialize namespace
        raise NotImplementedError

    def __getitem__(self, name):
        return self.namespace[name]

    def __setitem__(self, name, value):
        try:
            self.namespace[name]
            self.namespace[name] = value

        except KeyError:
            raise KeyError('Key %s not in symboltable'% name)
        return

    def keys(self):
        '''list names of all symbols'''
        return self.namespace.keys()

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def getglobals(self):
        '''returns a list of all symbol names that are globally defined'''
        raise NotImplementedError

    def getlocals(self):
        '''returns a list of all symbol names that are locally defined'''
        raise NotImplementedError

    def listsegments(self):
        '''
        list names of all available segments that are contained in this store
        '''
        raise NotImplementedError

# XXX: trying out .getsegment, and .getsegmentlength to avoid creating a
#      Segment object...

    def getsegment(self, name, baseaddress=0):
        '''
        get a segment from this store, relocated, and then return a string
        representing the segment data
        '''
        raise NotImplementedError

    def getsegmentlength(self, name):
        '''
        get a segments length so one can allocate for it...
        FIXME: this doesn't feel right to have this as a method
        '''
        raise NotImplementedError

class coffstore(store):
    pcoff = pCOFF.File

    def __init__(self, filename):
        self.pcoff = pCOFF.open(filename)
        self.__symbolcache = self.pcoff['Header'].getsymbols()
        symbols = self.__symbolcache

        ## create our initial namespace
        self.namespace = dict()
        for sym in symbols.get():
            name = sym['Name'].get()
            storageclass = int(sym['StorageClass'])

            # undefined section
            if sym['SectionNumber'] == sym['SectionNumber'].IMAGE_SYM_UNDEFINED:
                self.namespace[name] = None
                continue

            if storageclass in ([2, 3, 6] + [100, 101]):
                self.namespace[name] = int(sym['Value'])
                continue
            warn("ignoring symbol %s of storageClass %s"% (name, str(sym['StorageClass'])))
            continue
        return

    def getsegment(self, name, baseaddress=0):
        section = self.__getsection(name)
        section['VirtualAddress'].set(baseaddress)

        ## assign symbols
        try:
            self[name] = baseaddress
            self.__assign_symbols(section, baseaddress)

        except KeyError:
            # XXX: it's okay because not every store will have the same
            #      segments, right?
            pass

        # copy symbols our section depends on
        relocations = section.getrelocations()
        
        ## figure out the data
        data = section.get()
        for r in section.getrelocations():
            data = r.relocate(data, self.__symbolcache['Symbols'])

        ## update the symbol table
        self.__relocate_symbols(section, baseaddress)
        return data

    def __assign_symbols(self, section, baseaddress):
        ## go through all the global symbols in specified section
        ## and assign them with the value from our namespace

        section['VirtualAddress'].set(baseaddress)
        sectionindex = section.parent.value.index(section)  # heh
        sectionname = section['Name'].get()

        symbols = self.__getsymbolsbysectionnumber(sectionindex)
        symbols += self.__getrelocationsymbolsbysection(section)

        for sym in symbols:
            name = sym['Name'].get()
            storageclass = sym['StorageClass']

            # section name
            if storageclass == 3 and name == sectionname:
                self[name] = baseaddress
                sym['Value'].set(baseaddress)
                continue

            res = self[name]
            if res is None:
                raise ValueError("symbol %s undefined"% name)

            sym['Value'].set(res)
        return

    def __relocate_symbols(self, section, baseaddress):
        oldbase = int(section['VirtualAddress'])

        sectionindex = section.parent.value.index(section)  # heh
        sectionname = section['Name'].get()

        for sym in self.__getsymbolsbysectionnumber(sectionindex):
            name = sym['Name'].get()
            storageclass = int(sym['StorageClass'])

            # don't tamper with a section symbol
            if storageclass == 3 and name == sectionname:
                continue

            # if it's a relocateable address, then assign its value to our namespace
            if int(sym['StorageClass']) in ([2, 3, 6] + [100, 101]):
                self[name] = baseaddress + int(sym['Value'])
                continue

            # otherwise don't tamper with it
            self[name] = int(sym['Value'])
            
        return

    def getglobals(self):
        return [ x['Name'].get() for x in self.__symbolcache.get() if int(x['StorageClass']) == 2]

    def getlocals(self):
        return [ x['Name'].get() for x in self.__symbolcache.get() if int(x['StorageClass']) == 3]

    def listsegments(self):
        return [ x['Name'].get() for x in self.pcoff['Sections'] ]

    def __getsectionbyname(self, name):
        res = [x for x in self.pcoff['Sections'] if x['Name'].get() == name ]
        if len(res) == 0:
            raise KeyError('Section %s not found'% name)
        assert len(res) == 1, '>1 Section named %s is listed'% name
        return res[0]

    def __getsectionbyindex(self, index):   
        return self.pcoff['Sections'][index]

    def __getsection(self, name):
        # this is an attempt to make python more perl-like
        if type(name) == str:
            return self.__getsectionbyname(name)
        return self.__getsectionbyindex( int(index) )

    def getsegmentlength(self, name):
        section = self.__getsection(name)
        return int(section['SizeOfRawData'])

    def __getsymbolsbysectionnumber(self, sectionnumber):
        return [ x for x in self.__symbolcache.get() if x['SectionNumber'].get() == sectionnumber]

    def __getrelocationsymbolsbysection(self, section):
        return [self.__symbolcache['Symbols'][int(x['SymbolTableIndex'])] for x in section.getrelocations()]

class linker(object):
    namespace = dict
    symbolstores = list

    def __init__(self):
        self.namespace = {}
        self.symbolstores = []

    def add(self, symbolstore):
        self.symbolstores.append(symbolstore)
        self.__merge(symbolstore)

    def __merge(self, symbolstore):
        for name in symbolstore.getglobals():

            # pull from linker namespace by default
            if name in self.keys():
                if symbolstore[name] is None:
                    symbolstore[name] = self[name]
                    continue

                if self[name] is None:
                    self[name] = symbolstore[name]
                    print 'Updated undefined symbol %s with %s'% (name, symbolstore[name])
                    continue

                if self[name] is not None:
                    print "Duplicate symbol %s declared in %s -> %s"% (name, symbolstore, (self[name], symbolstore[name]))
                continue
            
            # merge symbol into our namespace
            self.namespace[name] = symbolstore[name]
        return
    
    def __getitem__(self, name):
        return self.namespace[name]

    def __setitem__(self, name, value):
        try:
            self.namespace[name]
            self.namespace[name] = value

        except KeyError:
            raise KeyError('Key %s not in symboltable'% name)
        return

    def keys(self):
        return self.namespace.keys()

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def listsegments(self):
        res = {}
        for v in self.symbolstores:
            res.update( dict([(k,None) for k in v.listsegments()]) )
        return res.keys()

    def getsegment(self, name, baseaddress):
        ofs = 0; res = []
        for st in self.symbolstores:
            # copy symbols into symbolstore
            for k in st.getglobals():
                st[k] = self[k]

            # now relocate
            data = st.getsegment(name, baseaddress+ofs)
            ofs += len(data)
            res.append(data)

            # update our symboltable
            for k in st.getglobals():
                self[k] = st[k]
        return ''.join(res)

    def getsegmentlength(self, name):
        return reduce(lambda x,y:x+y, [st.getsegmentlength(name) for st in self.symbolstores])

def new(*args, **kwds):
    return linker(*args, **kwds)

if __name__ == '__main__':
    import linker; reload(linker)
    self = linker.new()

    for filename in 'shit/obj1.obj shit/obj2.obj shit/obj3.obj'.split(' '):
        symbolstore = linker.coffstore(filename)
        self.add(symbolstore)

    self['_printf'] = 0xfeeddead

    data = self.getsegment('.data', 0x1000)
    print pCOFF.ptypes.utils.hexdump(data, offset=0x1000)
    text = self.getsegment('.text', 0x2000)
    print pCOFF.ptypes.utils.hexdump(text, offset=0x2000)

    x = file('shit/fuckyou.bin', 'wb')
    x.write('\x90'*0x1000)
    x.write(data + '\x90'*(0x1000-len(data)))
    x.write(text)
    x.close()

