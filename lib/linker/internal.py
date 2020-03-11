import abc,itertools,operator,weakref
import collections,sets,sparse

class OrderedDict(collections.OrderedDict): pass

class OrderedSet(sets.Set):
    __slots__ = ['_data']
    def __init__(self, iterable=None):
        super(OrderedSet,self).__init__(iterable=None)
        self._data = OrderedDict()
        if iterable is not None: self.update(iterable)

    def add(self, element):
        if element in self._data:
            raise TypeError, "Element already exists within set %s: %r"% (object.__repr__(self), element)
        return super(OrderedSet,self).add(element)

class AliasDict(collections.MutableMapping):
    """A dictionary that allows one to create aliases for keys"""
    __slots__ = ['_data', '_aliases']
    def __init__(self, iterable=None):
        super(AliasDict,self).__init__()
        if iterable is not None:
            self.update(iterable)
        self._data,self._aliases = dict(),OrderedDict()

    # tools
    def _getkey(self, key):
        return self._aliases[key] if key in self._aliases else key
    def _getaliases(self, target):
        return set(k for k,v in self._aliases.items() if v == target)
    def _listkeys(self):
        return self._data.viewkeys()
    def _listaliases(self):
        return self._aliases.viewkeys()

    # abstract methods
    def __setitem__(self, key, value):
        res = self._getkey(key)
        return self._data.__setitem__(res, value)
    def __getitem__(self, key):
        res = self._getkey(key)
        return self._data.__getitem__(res)
    def __delitem__(self, key):
        target = self._getkey(key)
        res = self._getaliases(target)
        [ self._aliases.pop(n) for n in res ]
        return self._data.__delitem__(target)
    def keys(self):
        return set(self._listkeys()).union(self._listaliases())
    def __iter__(self):
        for n in self.keys():
            yield n
        return
    def __len__(self):
        return len(self._listkeys())
    def __contains__(self, key):
        current,aliases = self._listkeys(),self._listaliases()
        return any(key in ring for ring in (current,aliases))

    # overloads
    def update(self, *args, **kwds):
        self = args[0]
        other = args[1] if len(args) >= 2 else ()
        res = super(AliasDict,self).update(*args, **kwds)
        if isinstance(other, AliasDict):
            other._aliases.update(self._aliases)
        return res

    # aliases
    def aliases(self):
        return self._listaliases()
    def alias(self, target, *aliases):
        if super(AliasDict,self).__contains__(target):

            # validate
            for n in aliases:
                if n in self._data:
                    raise KeyError, "Alias %r already exists as a target in AliasDict %s"% (n, object.__repr__(self))
                continue

            create_count = 0
            for n in aliases:
                if n not in self._aliases:
                    create_count += 1
                self._aliases[n] = target
            return create_count
        raise KeyError, "Target %r does not exist within AliasDict %s"% (target, object.__repr__(self))
    def unalias(self, *aliases):
        return [self._aliases.pop(n) for n in aliases]

    # general
    def __repr__(self):
        return '{:s} {!r}'.format(object.__repr__(self), [(k,self[k]) for k in self.keys()])

class HookedDict(AliasDict):
    """A dictionary that allows one to hook assignment of a particular key"""
    __slots__ = ['__hooks']
    def __init__(self, iterable=None):
        super(HookedDict,self).__init__(iterable)
        self.__hooks = {}

    def hook(self, key, fn, args=(), kwds={}):
        target = self._getkey(key)
        if target not in self._data:
            raise KeyError, "Target %r does not exist within HookDict %s"% (key, object.__repr__(self))
        res = self.__hooks.pop(target) if target in self.__hooks else None
        self.__hooks[target] = lambda s,k,v,fn=fn,args=tuple(args),kwds=dict(kwds): fn(s,k,v,*args,**kwds)
        return res

    def unhook(self, key):
        target = self._getkey(key)
        return self.__hooks.pop(target)

    def _execute_hook(self, key, value):
        target = self._getkey(key)
        if target in self.__hooks:
            p = self.__hooks[target]
            self.__hooks[target] = lambda *_: False
            res = p(self, key, value)
            self.__hooks[target] = p
            return res if isinstance(res, bool) else True
        return True

    def __setitem__(self, key, value):
        res = self._execute_hook(key, value)
        if res:
            target = self._getkey(key)
            return super(HookedDict,self).__setitem__(target, value)
        return

    def __delitem__(self, key):
        target = self._getkey(key)
        if target in self.__hooks:
            _ = self.unhook(target)
        return super(HookedDict,self).__delitem__(key)

class MergedMapping(collections.MutableMapping):
    """A dictionary composed of other Mapping types"""

    def __init__(self):
        super(MergedDict,self).__init__()

        self._cache = {}
        # FIXME: it might be better to use a weakref.WeakValueDictionary so that
        #        if a value in a sub-dictionary disappears, the cached key will
        #        disappear

        self._data = []

    def add(self, d):
        if id(d) in map(id,self._data):
            raise ReferenceError, 'Dictionary %s already exists in MergedDict %s'%(object.__repr__(d), object.__repr__(self))
        ref = weakref.ref(d)
        self._data.append(ref)
        return self._sync(d)

    def remove(self, d):
        ref = weakref.ref(d)
        self._data.remove(ref)
        return self.sync()

    def _sync(self, d):
        cur = set(self._cache.viewkeys())
        new = set(list(d))
        ref = weakref.ref(d)

        for n in cur.intersection(new):
            self._cache[n][:] = [x for x in self._cache[n] if x() is not None and x is not ref] + [ref]

        for n in new.difference(cur):
            self._cache[n] = [ref]

        return len(new)

    def sync(self):
        res = set(itertools.chain(*(x.viewkeys() for x in self._data if x() is not None)))
        cur = set(self._cache.viewkeys())
        [self._cache.pop(k) for k in cur.difference(res)]
        return reduce(operator.add, (self._sync(r()) for r in self._data))

    def __setitem__(self, key, value):
        res = self._cache[key]
        for d in res:
            d[key] = value
        return len(res)

    def __getitem__(self, key):
        results = [d[key] for d in self._cache[key]]
        res = results.pop(0)
        if not all(x == res for x in results):
            raise KeyError, 'More than one differnet value was returned'
        return res

    def __delitem__(self, key):
        res = self._cache[key]
        for d in res:
            del d[key]
        return len(res)

    def __len__(self):
        return len(self._cache)
    def __iter__(self):
        for n in self._cache:
            yield n
        return

    def __repr__(self):
        return '{:s} {:s} {!r}'.format(object.__repr__(self), ','.join(map(object.__repr__,self._data)), {k:self[k] for k in self.keys()})

if __name__ == '__main__':
    a = OrderedDict()
    a[0] = None
    a[1] = None
    a[2] = None
    a[3] = None
    a[4] = None
    a[-5] = None
    a[-4] = None
    a[-3] = None
    a[-2] = None
    a[-1] = None
    print a.keys() == [0,1,2,3,4,-5,-4,-3,-2,-1]

    a = OrderedSet( ('bla','blah','blahh') )
    a.add('meh')
    a.add('hmm')
    a.add('heh')
    print a.discard('hmm')
    print a.remove('meh')
    print list(a) == ['bla','blah','blahh','heh']

    a = AliasDict()
    a.alias('fuck', 'a','b','c')
    a['blah'] = 10
    a['heh'] = 20
    a['fuck'] = True
    print a['fuck']
    a.alias('fuck', 'a', 'b', 'c')
    print a.keys()
    print a['a']
    print a['b']
    print a['c']
    a['b'] = 'huh'

    a.unalias('heh')
    a.unalias('fuck')
    print a.unalias('a')
    print a.unalias('b')
    print a.aliases()
    print a.items()

    def ok(self, key, value):
        print 'assigned', key, value
    def ignore(self, key, value):
        print 'ignored', key, value
        return False

    a = internal.HookedDict()
    a['val1'] = 1
    a.alias('val1', 'alias1')
    print a['alias1'],a['val1']
    a['alias1'] = 10
    print a['alias2']

    a['val2'] = 0
    res = a.hook('val2', ok)
    a['val2'] = 1
    a.alias('val2', 'alias2')
    a['alias2'] = 500

    a['val3'] = 20
    a.hook('val3', ignore)
    a['val3'] = 50
    a.alias('val3', 'alias4')
    a['alias4'] = 40

    a = internal.MergedDict()
    b = {'bkey1':0,'bkey2':1,'bkey3':2}
    c = {'ckey1':0,'ckey2':1,'ckey3':2}
    d = {'dkey1':0,'dkey2':1,'dkey3':2}
    e = {'bkey1':0,'ckey1':0,'dkey1':0}
    a.add(b)
    a.add(c)
    a.add(d)
    print a
    a['bkey1'] = 5
    a['ckey1'] = 10
    a['dkey1'] = 15

    a.add(e)

# sys.path.append('c:/users/user/work/ata/lib')
