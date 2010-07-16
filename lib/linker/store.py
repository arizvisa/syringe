class store(dict):
    '''
    A dictionary attempting to represent all the symbol address information contained
    within a symbol store.
    '''
    def __setitem__(self, name, value):
        parent = super(store, self)
        try:
            parent.__getitem__(name)
        except KeyError:
            raise KeyError('Key %s not in symboltable'% name)
        parent.__setitem__(name, value)

    def add(self, name, value=None):
        '''Utility method for class to add a symbol'''
        if name in self:
            raise KeyError('Key %s already exists'% name)
        parent = super(store, self)
        parent.__setitem__(name, value)

    def getglobals(self):
        return self.getglobalsbysegmentname(None)
    def getlocals(self):
        return self.getlocalsbysegmentname(None)

    def getglobalsbysegmentname(self, name=None):
        '''Intended to be overloaded. returns a list of all symbol names that are globally defined for a segment'''
        raise NotImplementedError

    def getlocalsbysegmentname(self, name=None):
        '''Intended to be overloaded. returns a list of all symbol names that are locally defined for a segment'''
        raise NotImplementedError

    def getexternals(self):
        '''Intended to be overloaded. returns a list of all symbol names that are externally defined for a segment'''
        raise NotImplementedError
    
    def listsegments(self):
        '''Intended to be overloaded. list names of all available segments that are contained in this store'''
        raise NotImplementedError

    def getsegmentlength(self, name):
        '''Intended to be overloaded. get a segment's length so one can allocate for it...'''
        raise NotImplementedError

    def getsegmentprotection(self, name):
        '''Intended to be overloaded. get a segment's protection flags'''
        raise NotImplementedError

    def getsegment(self, name):
        '''Intended to be overloaded. get a segment from this store, relocated, and then return a string representing the segment data'''
        raise NotImplementedError

    def relocatesegment(self, name, data, baseaddress):
        raise NotImplementedError

    def __repr__(self):
        try:
            return super(object, self).__repr__() + ' -> %s'% self.modulename
        except AttributeError:
            pass
        return super(object, self).__repr__()

    def dumpsymbols(self):
        res = []
        for k,v in self.items():
            if v is not None:
                v = hex(v)
            res.append( repr((k,v)) )
        return '\n'.join(res)

    def undefinedsymbols(self):
        res = []
        for k,v in self.items():
            if v is None:
                res.append(k)
            continue
        return res

    def externalmodules(self):
        # XXX: this is fucking stupid
        res = set()
        for fullname in self.getexternals():
            if '!' not in fullname:
                continue
            module,name = fullname.split('!')
            res.add(module)
        return res


class container(store):
    stores = list

    def __init__(self):
        super(container, self).__init__()
        self.stores = []

    def getmember(self, name):
        return self.stores[name]

    def getmembercount(self):
        return len(self.stores)

    def listsegments(self):
        res = set()
        for v in self.stores:
            for s in v.listsegments():
                res.add(s)
            continue
        return list(res)

    def getsegment(self, name):
        result = []
        for st in self.stores:
            if name not in st.listsegments():
                continue
            data = st.getsegment(name)
            result.append(data)
        return ''.join(result)

    def getsegmentlength(self, name):
        """return reduce(lambda x,y:x+y, [st.getsegmentlength(name) for st in self.stores])"""
        result = 0
        for st in self.stores:
            if name not in st.listsegments():
                continue
            result += st.getsegmentlength(name)
        return result

    def getsegmentprotection(self, name):
        protection = 0
        for st in self.stores:
            if name not in st.listsegments():
                continue

            res = st.getsegmentprotection(name)
            if protection != res and res > 0:
                print 'Discovered protection %d on segment %s'% (res,name)
                protection = res

            continue
        return protection

    # XXX: do we need a .getmodules() for determining what external modules
    #      a store might depend on

    def getglobalsbysegmentname(self, name):
        if name is None:
            result = []
            for st in self.stores:
                result.extend( (n for n in st.getglobals()) )
            return result

        result = []
        for i in xrange( self.getmembercount() ):
            st = self.getmember(i)
            segments = (x for x in st.listsegments() if x == name)
            for segmentname in segments:
                # FIXME: should probably check for duplicate deifned globals
                result.extend( st.getglobalsbysegmentname(segmentname) )
            continue
        return result

    def getsegmentprotection(self, name):
        protections = []
        for st in self.stores:
            try:
                protection = st.getsegmentprotection(name)
                if protection != 0:
                    protections.append(protection)
                pass
            except KeyError, e:
                pass
            continue


        if len(protections) > 0:
            res = reduce(lambda a,b:a+b, protections) / len(protections)
            assert res == protections[0]
            return res
        return 0

    def relocatesegment(self, name, data, baseaddress):
        raise NotImplementedError

