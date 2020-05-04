import functools, itertools, types, builtins, operator, sys
import collections, weakref

if sys.version_info.major < 3:
    MutableSet = collections.MutableSet
    MutableMapping = collections.MutableMapping

else:
    import collections.abc
    MutableMapping = collections.abc.MutableMapping
    MutableSet = collections.abc.MutableSet

# Python3 doesn't have ordered sets...so we have to implement this ourselves
class OrderedSet(MutableSet):
    __slots__ = ['_data', '_order']
    def __init__(self, iterable=None):
        items = iterable or []
        self._data = [ item for item in items ]
        self._order = { item : index for index, item in enumerate(self._data) }

    def __contains__(self, value):
        return value in self._order

    def __len__(self):
        return len(self._data)

    def add(self, value):
        if value in self._order:
            raise TypeError("Element already exists within set {!s}: {!r}".format(object.__repr__(self), value))
        self._order[value] = len(self._data)
        self._data.append(value)

    def discard(self, item):
        if item in self._order:
            index = self._order.pop(item)
            self._data.pop(index)
        return

    def __iter__(self):
        for item in self._data:
            yield item
        return

    def __str__(self):
        cls = self.__class__
        return "{!s} {:s}".format(cls, ', '.join(map("{!r}".format, self)))
    __repr__ = __str__

class OrderedDict(MutableMapping):
    __slots__ = ['_data', '_order', '_mapping']

    def __init__(self, iterable=None, **pairs):
        items = [item for item in pairs.items()]
        if isinstance(iterable, dict):
            items += iterable.items()
        else:
            items += [(key, value) for key, value in iterable or []]

        self._order = [ (key, value) for key, value in items ]
        self._data = { key : index for index, (key, value) in enumerate(self._order) }
        self._mapping = { key : value for key, value in self._order }

    def __len__(self):
        return len(self._order)

    def __iter__(self):
        for key, _ in self._order:
            yield key
        return

    def __getitem__(self, key):
        index = self._data[key]
        _, value = self._order[index]
        return value

    def __setitem__(self, key, value):
        if key in self._data:
            index = self._data[key]
        else:
            index = len(self._order)
            self._order.append((key, value))
        self._data[key] = index
        self._mapping[key] = value

    def __delitem__(self, key):
        if key in self._data:
            index = self._data.pop(key)
            del self._order[index]
            del self._mapping[key]
        raise KeyError(key)

    def __str__(self):
        cls = self.__class__
        return "{!s} {:s}".format(cls, ', '.join(itertools.starmap("{!s}={!r}".format, self.items())))
    __repr__ = __str__

class AliasDict(MutableMapping):
    """A dictionary that allows one to create aliases for keys"""
    __slots__ = ['_data', '_aliases']
    def __init__(self, iterable=None):
        super(AliasDict, self).__init__()
        if iterable is not None:
            self.update(iterable)
        self._data, self._aliases = {}, OrderedDict()

    # tools
    def _getkey(self, key):
        return self._aliases[key] if key in self._aliases else key
    def _getaliases(self, target):
        return set(k for k, v in self._aliases.items() if v == target)
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
        res = { item for item in self._listkeys() }
        return res.union(self._listaliases())
    def __iter__(self):
        for item in self.keys():
            yield item
        return
    def __len__(self):
        return len(self._listkeys())
    def __contains__(self, key):
        current, aliases = self._listkeys(), self._listaliases()
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
            for item in aliases:
                if item in self._data:
                    raise KeyError("Alias {!r} already exists as a target in AliasDict {!s}".format(item, object.__repr__(self)))
                continue

            create_count = 0
            for item in aliases:
                if item not in self._aliases:
                    create_count += 1
                self._aliases[item] = target
            return create_count
        raise KeyError("Target {!r} does not exist within AliasDict {!s}".format(target, object.__repr__(self)))
    def unalias(self, *aliases):
        return [self._aliases.pop(item) for item in aliases]

    # general
    def __repr__(self):
        return '{:s} {!r}'.format(object.__repr__(self), [(key, self[key]) for key in self.keys()])

class HookedDict(AliasDict):
    """A dictionary that allows one to hook assignment of a particular key"""
    __slots__ = ['__hooks']
    def __init__(self, iterable=None):
        super(HookedDict,self).__init__(iterable)
        self.__hooks = {}

    def hook(self, key, F, args=(), kwds={}):
        target = self._getkey(key)
        if target not in self._data:
            raise KeyError("Target {!r} does not exist within HookDict {!s}".format(key, object.__repr__(self)))
        res = self.__hooks.pop(target) if target in self.__hooks else None
        def closure(self, key, value, F=F, args=tuple(args), kwargs=dict(kwds)):
            return F(self, key, value, *args, **kwargs)
        self.__hooks[target] = closure
        return res

    def unhook(self, key):
        target = self._getkey(key)
        return self.__hooks.pop(target)

    def _execute_hook(self, key, value):
        Ffalse = lambda *args, **kwargs: False

        target = self._getkey(key)
        if target in self.__hooks:
            try:
                F, self.__hooks[target] = self.__hooks[target], Ffalse
                res = F(self, key, value)

            finally:
                self.__hooks[target] = F
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
            F = self.unhook(target)
        return super(HookedDict,self).__delitem__(key)

class MergedMapping(MutableMapping):
    """A dictionary composed of other Mapping types"""

    def __init__(self):
        super(MergedDict,self).__init__()

        self._cache = {}
        # FIXME: it might be better to use a weakref.WeakValueDictionary so that
        #        if a value in a sub-dictionary disappears, the cached key will
        #        disappear

        self._data = []

    def add(self, D):
        if id(D) in map(id, self._data):
            raise ReferenceError("Dictionary {!s} already exists in MergedDict {!s}".format(object.__repr__(D), object.__repr__(self)))
        ref = weakref.ref(D)
        self._data.append(ref)
        return self._sync(D)

    def remove(self, D):
        ref = weakref.ref(D)
        self._data.remove(ref)
        return self.sync()

    def _sync(self, D):
        cur = { item for item in self._cache.keys() }
        new = { item for item in D }
        ref = weakref.ref(d)

        for key in cur.intersection(new):
            self._cache[key][:] = [item for item in self._cache[key] if item() is not None and item is not ref] + [ref]

        for key in new.difference(cur):
            self._cache[key] = [ref]

        return len(new)

    def sync(self):
        iterable = (item.keys() for item in self._data if item() is not None)
        res = { item for item in itertools.chain(*iterable) }
        cur = { item for item in self._cache.keys() }
        [self._cache.pop(key) for key in cur.difference(res)]

        iterable = (self._sync(M()) for M in self._data)
        return functools.reduce(operator.add, iterable)

    def __setitem__(self, key, value):
        res = self._cache[key]
        for D in res:
            D[key] = value
        return len(res)

    def __getitem__(self, key):
        results = [D[key] for D in self._cache[key]]
        res = results.pop(0)
        if not all(item == res for item in results):
            raise KeyError('More than one differnet value was returned')
        return res

    def __delitem__(self, key):
        res = self._cache[key]
        for D in res:
            del D[key]
        return len(res)

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        for item in self._cache:
            yield item
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
    if list(a.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
        raise ValueError

    a = OrderedSet( ('bla','blah','blahh') )
    a.add('meh')
    a.add('hmm')
    a.add('heh')
    a.discard('hmm')
    a.remove('meh')

    if list(a) != ['bla','blah','blahh','heh']:
        raise ValueError

    a = AliasDict()
    a.alias('fuck', 'a','b','c')
    a['blah'] = 10
    a['heh'] = 20
    a['fuck'] = True
    print(a['fuck'])
    a.alias('fuck', 'a', 'b', 'c')
    print(a.keys())
    print(a['a'])
    print(a['b'])
    print(a['c'])
    a['b'] = 'huh'

    a.unalias('heh')
    a.unalias('fuck')
    print(a.unalias('a'))
    print(a.unalias('b'))
    print(a.aliases())
    print(a.items())

    def ok(self, key, value):
        print('assigned', key, value)
    def ignore(self, key, value):
        print('ignored', key, value)
        return False

    a = internal.HookedDict()
    a['val1'] = 1
    a.alias('val1', 'alias1')
    print(a['alias1'],a['val1'])
    a['alias1'] = 10
    print(a['alias2'])

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
    print(a)
    a['bkey1'] = 5
    a['ckey1'] = 10
    a['dkey1'] = 15

    a.add(e)

# sys.path.append('c:/users/user/work/ata/lib')
