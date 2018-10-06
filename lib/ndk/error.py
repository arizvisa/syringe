from exceptions import Exception

class NdkException(Exception):
    '''Base class for exceptions raised by the ndk library'''
    def __init__(self, *args, **kwds):
        super(NdkException,self).__init__(*args)
        map(None,itertools.starmap(functools.partial(setattr, self), kwds.items()))
        self.__iterdata__ = tuple(args)
        self.__mapdata__ = dict(kwds)
    def __iter__(self):
        for n in self.__iterdata__: yield n
    def __repr__(self):
        iterdata = (repr(v) for v in self.__iterdata__)
        mapdata = ('%s=%r'%(k,v) for k,v in self.__mapdata__.iteritems())
        res = '({:s})'.format(', '.join(itertools.chain(iterdata, mapdata)) if self.__iterdata__ or self.__mapdata__ else '')
        return '{:s}: {:s}'.format(self.__class__, res)

