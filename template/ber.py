import logging
from ptypes import *

class UNKNOWN(dyn.block(0)):
    def classname(self):
        return 'Unknown<%d,%d>'%(self.type[0], self.type[1])

class AbstractClass(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

    @classmethod
    def Update(cls, record):
        a = set(cls.cache.keys())
        b = set(record.cache.keys())
        if a.intersection(b):
            logging.warning('%s : Unable to import module %s due to multiple definitions of the same record'%(cls.__module__, repr(record)))
            logging.debug(repr(a.intersection(b)))
            return False

        # merge record caches into a single one
        cls.cache.update(record.cache)
        record.cache = cls.cache
        return True

###
class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed?'),
        (5, 'Number'),
    ]

class Length(pbinary.struct):
    def __long(self):
        if not self['islong']:
            return 0
        return self['length']*8

    def get(self):
        return (self['length'], self['longform'])[self['islong']]
            
    _fields_ = [
        (1, 'islong'),
        (7, 'length'),
        (__long, 'longform'),
    ]

class Record(pstruct.type):
    def __Value(self):
        c,n = self['Type'].l['Class'],self['Type']['Number']
        s = self['Length'].l.get()
        
        try:
            result = dyn.clone(AbstractClass.Lookup((c,n)), blocksize=lambda x:s)
        except KeyError:
            result = dyn.clone(UNKNOWN, type=(c,n))
        
        if n not in set([0x10,0x11]):
            result.length = s
        return result

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'),
        (__Value, 'Value')
    ]

### classes
@AbstractClass.Define
class BOOLEAN(ptype.type):
    type = (0, 0x00)

@AbstractClass.Define
class INTEGER(ptype.type):
    type = (0, 0x02)

@AbstractClass.Define
class BITSTRING(ptype.type):
    type = (0, 0x03)

#@AbstractClass.Define
class OCTETSTRING(ptype.type):
    type = (0, 0x04)

@AbstractClass.Define
class NULL(ptype.type):
    type = (0, 0x05)

@AbstractClass.Define
class OBJECT_IDENTIFIER(ptype.type):
    type = (0, 0x06)

@AbstractClass.Define
class SEQUENCE(parray.block):
    type = (0, 0x10)
    _object_ = Record

@AbstractClass.Define
class SET(parray.block):
    type = (0, 0x11)
    _object_ = Record

@AbstractClass.Define
class PrintableString(ptype.type):
    type = (0, 0x13)

@AbstractClass.Define
class IA5String(ptype.type):
    type = (0, 0x16)

@AbstractClass.Define
class UTCTime(ptype.type):
    type = (0, 0x17)

if __name__ == '__main__':
    import ptypes,ber
    reload(ber)
    ptypes.setsource(ptypes.file('./test.3','rb'))

    a = ber.Record
    a = a()
    a=a.l
