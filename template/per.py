import logging, math, six
import ptypes, ber
from ptypes import *

class Length(ber.Length): pass

class CHOICE(ptype.definition):
    cache = {}
    @classmethod
    def define(cls, definition):
        cls.add(len(cls.cache), definition)
        return definition

    @classmethod
    def choice(cls):
        name = cls.__name__
        width = math.floor(math.log(len(cls.cache)) / math.log(2) + 1)
        values = [(definition.__name__, type) for type, definition in cls.cache.viewitems()]
        choice = dyn.clone(pbinary.enum, __name__=name, width=math.trunc(width), _values_=values)

        class Choose(pstruct.type): pass
        _fields_ = []
        _fields_.append((choice, 'choice'))
        _fields_.append((lambda self: cls.lookup(self['choice'].li.int()), 'value'))

        Choose.__name__ == name
        Choose._fields_ = _fields_
        return Choose

class SEQUENCE(pstruct.type):
    def __Value(self):
        res = self['Length'].li
        return dyn.clone(ber.SEQUENCE, blocksize=lambda self, cb=res.int(): cb)

    _fields_ = [
        (Length, 'Length'),
        (__Value, 'Value'),
    ]
