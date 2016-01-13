import logging,math
import ptypes,ptypes.bitmap as bitmap
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Primitive types for records
class IdentifierLong(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [
            (1, 'continue'),
            (7, 'integer'),
        ]
    def isTerminator(self, value):
        return value['continue'] == 0

class Length(pbinary.struct):
    def __value(self):
        return (self['count']*8) if self['form'] else 0

    _fields_ = [
        (1, 'form'),
        (7, 'count'),
        (__value, 'value'),
    ]
    def number(self):
        #assert not self.isIndefinite()
        return self['value'] if self['form'] else self['count']
    __int__ = __long__ = number

    def isIndefinite(self):
        assert self.initialized
        return self['form'] == self['count'] == 0

    def summary(self):
        res = self.number()
        return '{:d} (0x{:x}) -- {:s}'.format(res, res, super(Length,self).summary()) + (' Indefinite' if self.isIndefinite() else '')

class Tag(pbinary.struct):
    def __TagLong(self):
        return IdentifierLong if self['Tag'] == 0x1f else dyn.clone(IdentifierLong, length=0)

    _fields_ = [
        (5, 'Tag'),
        (__TagLong, 'TagLong'),
    ]

    def number(self):
        res = self['Tag']
        res += sum(x['integer'] for x in self['TagLong'])
        return res
    __int__ = __long__ = number

    def summary(self):
        res = self.number()
        return '{:d} (0x{:x}) -- {:s}'.format(res,res,super(Tag,self).summary())

class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed'),
        (Tag, 'Tag'),
    ]

    def summary(self):
        c,p,t = self['Class'],self['Constructed'],self['Tag'].number()
        return 'class:{:d} tag:0x{:x} {:s}'.format(c,t, 'Constructed' if p else 'Universal')

### Element structure
class Protocol(ptype.definition):
    attribute,cache = 'Class',{}
    class UnknownConstruct(parray.block):
        def classname(self):
            return 'UnknownConstruct<{!r}>'.format(self.type)
    class Unknown(ptype.block):
        def classname(self):
            return 'UnknownPrimitive<{!r}>'.format(self.type)

class Element(pstruct.type):
    protocol = Protocol
    def Value(self):
        t = self['Type'].li
        cons,n = t['Constructed'],t['Tag'].number()
        K = self.protocol.lookup(t['Class'])

        # Lookup type by it's class
        try:
            result = K.lookup(n)
        except KeyError:
            result = self.protocol.UnknownConstruct if cons else self.protocol.Unknown
            result = dyn.clone(result, type=(t['Class'],n))
        return result

    def __Value(self):
        length,result = self['Length'].li, self.Value()

        # Assign ourself as the ber array's element if it inherits from
        # us and ._object_ is undefined
        if issubclass(result, parray.type):
            cls = type(self)
            parent = cls if cls.Value == Element.Value else cls.__base__
            result._object_ = parent if result._object_ == None else result._object_

        # Determine how to assign length
        if issubclass(result, parray.block):
            result = dyn.clone(result, blocksize=lambda _:length.number())
        elif length.isIndefinite() and issubclass(result, parray.terminated):
            result = dyn.clone(result, isTerminator=lambda s,v: type(v['Value']) == EOC)
        elif ptype.iscontainer(result):
            result = result
        elif ptype.istype(result):
            result = dyn.clone(result, length=length.number())
        return result

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'),
        (__Value, 'Value'),
    ]

### Element classes
@Protocol.define
class Universal(ptype.definition):
    Class,cache = 00, {}
@Protocol.define
class Application(ptype.definition):
    Class,cache = 01, {}
@Protocol.define
class Context(ptype.definition):
    Class,cache = 02, {}
@Protocol.define
class Private(ptype.definition):
    Class,cache = 03, {}

### Tag definitions (X.208)
@Universal.define
class EOC(ptype.type):
    type = 0x00
    # Required only if the length field specifies it

@Universal.define
class BOOLEAN(ptype.block):
    type = 0x01

@Universal.define
class INTEGER(pint.uint_t):
    type = 0x02

@Universal.define
class BITSTRING(ptype.block):
    type = 0x03

@Universal.define
class OCTETSTRING(pstr.string):
    type = 0x04
    def summary(self):
        return ''.join('{:02X}'.format(ord(_)) for _ in self.serialize())

@Universal.define
class NULL(ptype.block):
    type = 0x05

@Universal.define
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
        oid,data = self.str(),self.serialize()
        if oid in self._values_:
            return '{:s} ({:s}) ({!r})'.format(self._values_[oid],oid,data)
        return '{:s} ({!r})'.format(oid,data)

    _values_ = [
        ('SPC_INDIRECT_DATA_OBJID', '1.3.6.1.4.1.311.2.1.4'),
        ('SPC_STATEMENT_TYPE_OBJID', '1.3.6.1.4.1.311.2.1.11'),
        ('SPC_SP_OPUS_INFO_OBJID', '1.3.6.1.4.1.311.2.1.12'),
        ('SPC_INDIVIDUAL_SP_KEY_PURPOSE_OBJID', '1.3.6.1.4.1.311.2.1.21'),
        ('SPC_COMMERCIAL_SP_KEY_PURPOSE_OBJID', '1.3.6.1.4.1.311.2.1.22'),
        ('SPC_MS_JAVA_SOMETHING', '1.3.6.1.4.1.311.15.1'),
        ('SPC_PE_IMAGE_DATA_OBJID', '1.3.6.1.4.1.311.2.1.15'),
        ('SPC_CAB_DATA_OBJID', '1.3.6.1.4.1.311.2.1.25'),
        ('SPC_TIME_STAMP_REQUEST_OBJID', '1.3.6.1.4.1.311.3.2.1'),
        ('SPC_SIPINFO_OBJID', '1.3.6.1.4.1.311.2.1.30'),
        ('SPC_PE_IMAGE_PAGE_HASHES_V1', '1.3.6.1.4.1.311.2.3.1'), # Page hash using SHA1 */
        ('SPC_PE_IMAGE_PAGE_HASHES_V2', '1.3.6.1.4.1.311.2.3.2'), # Page hash using SHA256 */
        ('SPC_NESTED_SIGNATURE_OBJID', '1.3.6.1.4.1.311.2.4.1'),
        ('SPC_RFC3161_OBJID', '1.3.6.1.4.1.311.3.3.1'),
    ]
    _values_ = dict(_values_)


@Universal.define
class EXTERNAL(ptype.block):
    type = 0x08

@Universal.define
class REAL(ptype.block):
    type = 0x09

@Universal.define
class ENUMERATED(ptype.block):
    type = 0x0a

@Universal.define
class UTF8String(pstr.string):
    type = 0x0c

@Universal.define
class SEQUENCE(parray.block):
    type = 0x10

@Universal.define
class SET(parray.block):
    type = 0x11

@Universal.define
class NumericString(ptype.block):
    type = 0x12

@Universal.define
class PrintableString(pstr.string):
    type = 0x13

@Universal.define
class T61String(pstr.string):
    type = 0x14

@Universal.define
class IA5String(pstr.string):
    type = 0x16

@Universal.define
class UTCTime(pstr.string):
    type = 0x17

@Universal.define
class VisibleString(ptype.block):
    type = 0x1a

@Universal.define
class GeneralString(pstr.string):
    type = 0x1b

@Universal.define
class UniversalString(pstr.string):
    type = 0x1c

@Universal.define
class CHARACTER_STRING(pstr.string):
    type = 0x1d

@Universal.define
class BMPString(pstr.string):
    type = 0x1e
### End of Universal definitions

### Base structures
class Packet(Element):
    attributes = {'byteorder':ptypes.config.byteorder.bigendian}
class File(Element):
    attributes = {'byteorder':ptypes.config.byteorder.bigendian}

# add an alias for exported objects
protocol = Protocol
packet = Packet

if __name__ == '__main__':
    import ptypes,ber
    import ptypes.bitmap as bitmap
    reload(ber)
    ptypes.setsource(ptypes.file('./test.3','rb'))

    a = ber.Element
    a = a()
    a=a.l

    def test_tag():
        res = bitmap.new(0x1e, 5)

        res = bitmap.zero
        res = bitmap.push(res, (0x1f, 5))
        res = bitmap.push(res, (0x1, 1))
        res = bitmap.push(res, (0x10, 7))
        res = bitmap.push(res, (0x1, 0))
        res = bitmap.push(res, (0x0, 7))
        x = pbinary.new(ber.Tag,source=ptypes.prov.string(bitmap.data(res)))
        print x.l
        print x['TagLong'][0]
        print x.num()
        print int(x['TagLong'])

    def test_length():
        res = bitmap.zero
        res = bitmap.push(res, (0, 1))
        res = bitmap.push(res, (38, 7))
        x = pbinary.new(ber.Length,source=ptypes.prov.string(bitmap.data(res)))
        print x.l
        print x.number()

        res = bitmap.zero
        res = bitmap.push(res, (0x81,8))
        res = bitmap.push(res, (0xc9,8))
        x = pbinary.new(ber.Length,source=ptypes.prov.string(bitmap.data(res)))
        print x.l
        print x.number()
