import logging,math
import ptypes.bitmap as bitmap
from ptypes import *

class IdentifierLong(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [
            (1, 'continue'),
            (7, 'integer'),
        ]
    def isTerminator(self, value):
        return value['continue'] == 0

class IndefiniteLength(pbinary.struct):
    _fields_ = [(0,'unknown')]

class Length(pbinary.struct):
    def __form(self):
        if self['form']:
            if self['count'] == 0:
                return IndefiniteLength
            return self['count']*8
        return 0

    def num(self):
        if self['form']:
            if self['count'] == 0:
                raise Exception, 'Indefinite form not implemented'
            return self['value']
        return self['count']

    _fields_ = [
        (1, 'form'),
        (7, 'count'),
        (__form, 'value'),
    ]

    def summary(self):
        res = super(Length,self).summary()
        return '{:d} (0x{:x}) -- {:s}'.format(self.num(),self.num(), res)

###
class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed?'),
        (5, 'Tag'),
    ]

    def summary(self):
        c,p,t = self['Class'],self['Constructed?'],self['Tag']
        return 'class:{:d} tag:0x{:x} {:s}'.format(c,t, 'constructed' if p else 'primitive')

class Record(pstruct.type):
    def __Value(self):
        c,p,n = self['Type'].l['Class'],self['Type']['Constructed?'],self['Type']['Tag']
        s = self['Length'].l.num()
        if p:
            return dyn.clone(AbstractConstruct.get(n, length=s), blocksize=lambda _:s, length=s)
        return dyn.clone(AbstractPrimitive.get(n, length=s), blocksize=lambda _:s, length=s)

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'),
        (__Value, 'Value')
    ]

class AbstractPrimitive(ptype.definition):
    cache = {}
    attribute = 'type'
    class unknown(ptype.block):
        def classname(self):
            return 'UnknownPrimitive<%d>'%(self.type)

class AbstractConstruct(ptype.definition):
    cache = {}
    attribute = 'type'
    class unknown(ptype.block):
        _object_ = Record
        def classname(self):
            return 'UnknownConstruct<%d>'%(self.type)

### classes
@AbstractConstruct.define
@AbstractPrimitive.define
class EOC(ptype.block):
    type = 0x00

@AbstractPrimitive.define
class BOOLEAN(ptype.block):
    type = 0x01

@AbstractPrimitive.define
class INTEGER(pint.uint_t):
    type = 0x02

@AbstractPrimitive.define
class BITSTRING(ptype.block):
    type = 0x03

@AbstractPrimitive.define
class OCTETSTRING(pstr.string):
    type = 0x04
    def summary(self):
        return ''.join('{:02X}'.format(ord(_)) for _ in self.serialize())

@AbstractPrimitive.define
class NULL(ptype.block):
    type = 0x05

@AbstractPrimitive.define
class OBJECT_IDENTIFIER(ptype.type):
    type = 0x06

    def set(self, string):
        res = map(int,string.split('.'))
        val = [res.pop(0)*40 + res.pop(0)]
        for n in res:
            if n <= 127:
                val.append(n)
                continue
            
            # convert integer to a bitmap
            x = bitmap.new(0,0)
            while n > 0:
                x = bitmap.insert(x, (n&0xf,4))
                n /= 0x10

            # shuffle bitmap into oid components
            y = []
            while bitmap.size(x) > 0:
                x,v = bitmap.consume(x, 7)
                y.insert(0, v)

            val.extend([x|0x80 for x in y[:-1]] + [y[-1]])
        return super(OBJECT_IDENTIFIER).set(''.join(map(chr,val)))

    def str(self):
        data = map(ord,self.serialize())
        res = [data[0]/40, data.pop(0)%40]
        data = iter(data)
        for n in data:
            v = bitmap.new(0,0)
            while n&0x80:
                v = bitmap.push(v,(n&0x7f,7))
                n = data.next()
            v = bitmap.push(v,(n,7))
            res.append(bitmap.number(v))
        return '.'.join(map(str,res))

    def summary(self):
        data = self.serialize()
        return '{:s} ({!r})'.format(self.str(),data)

@AbstractPrimitive.define
class EXTERNAL(ptype.block):
    type = 0x08

@AbstractPrimitive.define
class REAL(ptype.block):
    type = 0x09

@AbstractPrimitive.define
class ENUMERATED(ptype.block):
    type = 0x0a

@AbstractPrimitive.define
class UTF8String(pstr.string):
    type = 0x0c

@AbstractConstruct.define
class SEQUENCE(parray.block):
    type = 0x10
    _object_ = Record

@AbstractConstruct.define
class SET(parray.block):
    type = 0x11
    _object_ = Record

@AbstractPrimitive.define
class NumericString(ptype.block):
    type = 0x12

@AbstractPrimitive.define
class PrintableString(pstr.string):
    type = 0x13

@AbstractPrimitive.define
class T61String(pstr.string):
    type = 0x14
    _fields_ = []

@AbstractPrimitive.define
class IA5String(pstr.string):
    type = 0x16
    _fields_ = []

@AbstractPrimitive.define
class UTCTime(pstr.string):
    type = 0x17
    _fields_ = []

@AbstractPrimitive.define
class VisibleString(ptype.block):
    type = 0x1a
    _fields_ = []

@AbstractPrimitive.define
class GeneralString(pstr.string):
    type = 0x1b
    _fields_ = []

@AbstractPrimitive.define
class UniversalString(pstr.string):
    type = 0x1c
    _fields_ = []

@AbstractPrimitive.define
class CHARACTER_STRING(pstr.string):
    type = 0x1d
    _fields_ = []

@AbstractPrimitive.define
class BMPString(pstr.string):
    type = 0x1e
    _fields_ = []

if __name__ == '__main__':
    import ptypes,ber
    reload(ber)
    ptypes.setsource(ptypes.file('./test.3','rb'))

    a = ber.Record
    a = a()
    a=a.l
