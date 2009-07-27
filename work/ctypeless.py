#
# FIXME: i'm not sure what problem i was trying to solve.
#        i pulled this out of context.py
#

def isNumber(n):
    try:
        n + 1
    except:
        return False
    return True

def resolve(v):
    if '_length_' in dir(v):
        return yourFriendlyList(v)
    if '_fields_' in dir(v):
        return yourFriendlyDictionary(v)
    return v

class friendly(object):
    pass

class yourFriendlyList(list, friendly):
    me = None
    def __init__(self, array):
        super(yourFriendlyList, self).__init__()
        self.me = array

    def __iter__(self):
        for x in range(len(self)):
            yield self[x]

    def __len__(self):
        return self.me._length_

    def __setitem__(self, k, v):
        if isNumber(v):
            self.me[k] = self.me._type_(v)
            return
        self.me[k] = resolve(v)

    def __getitem__(self, k):
        res = self.me[k]
        if isNumber(res):
            return self.type()(res)
        return resolve(res)

    def __repr__(self):
        return repr(list(self))

    def type(self):
        return self.me._type_

class yourFriendlyDictionary(dict, friendly):
    me = None
    def __init__(self, structure):
        super(yourFriendlyDictionary, self).__init__()
        self.me = structure

    def keys(self):
        return [k for k,t in self.me._fields_]

    def values(self):
        return [self[k] for k,t in self.me._fields_]

    def items(self):
        return list(zip(self.keys(), self.values()))

    def __getitem__(self, k):
        res = getattr(self.me, k)
        if isNumber(res):
            return res
        return resolve(res)

    def __setitem__(self, k, v):
        res = getattr(self.me, k)
        if isNumber(res):
            cls = type(res)
            setattr(self.me, k, cls(v))
        setattr(self.me, k, v)

    def __repr__(self):
        res = []
        for k,t in self.me._fields_:
            v = self[k]
            if isNumber(v):
                res.append( (k, t(self[k])) )
                continue
            res.append( (k, t(*self[k])) )
        
        return repr(dict([(k,resolve(v)) for (k,v) in res]))

if __name__ == '__main__':
    from context import *

    ## primitives
    print '- type'
    a = DWORD()
    print resolve(a)

    print '- array'
    a = ARRAY(DWORD, 2)()
    print resolve(a)

    print '- struct'
    a = M128A()
    print resolve(a)

    print '- arrays of arrays'
    a = ARRAY( ARRAY(BYTE, 2), 5 )()
    print resolve(a)

    print '- arrays of structs'
    a = ARRAY( M128A, 2 )()
    print resolve(a)
    print resolve(a)[0]
    print resolve(a)[0]['Low']

    print '- structs of arrays'
    class fuck(Structure):
        _fields_ = [
            ('test', ARRAY(BYTE, 2))
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test'][0]

    print '- structs of structs'
    class fuck(Structure):
        _fields_ = [
            ('test', M128A)
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test']['High']

    print '- structs of arrays of structs'
    class fuck(Structure):
        _fields_ = [
            ('test', ARRAY(M128A, 2))
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test'][0]
    print resolve(a)['test'][0]['Low']


    print '- arrays of of arrays of structs'
    a = ARRAY( ARRAY(2, M128A), 5)()
    print resolve(a)
    print resolve(a)[0]

    a = CONTEXT()
    v = resolve(a)

