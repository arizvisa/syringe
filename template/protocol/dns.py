import six, ptypes, osi.network.inet4, osi.network.inet6
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u8(pint.uint8_t): pass
class s8(pint.sint8_t): pass
class u16(pint.uint16_t): pass
class s16(pint.sint16_t): pass
class u32(pint.uint32_t): pass
class s32(pint.sint32_t): pass

class Name(pstruct.type):
    def __string(self):
        octet = self['length'].li
        if octet.int() & 0xc0:
            return pint.uint8_t
        return dyn.block(octet.int())

    _fields_ = [
        (u8, 'length'),
        (__string, 'string'),
    ]

    def CompressedQ(self):
        length = self['length'].int()
        return True if length & 0xc0 else False

    def str(self):
        if self.CompressedQ():
            raise TypeError("{:s} : Name is compressed".format(self.instance()))
        res = self['string'].serialize()
        return res.decode('ascii')

    def int(self):
        if self.CompressedQ():
            offset = self['string'].cast(u8)
            return offset.int()
        raise TypeError("{:s} : Name is not compressed".format(self.instance()))

    def summary(self):
        if self.CompressedQ():
            offset = self.int()
            return "OFFSET: {:+#x}".format(offset)
        res = self['length'].int()
        return "({:d}) {:s}".format(res, self.str())

    def repr(self):
        return self.summary()

    def set(self, value):
        if isinstance(value, six.integer_types):
            res = pint.uint16_t().set(0xc000 | value)
            return self.load(source=ptypes.prov.bytes(res.serialize()))
        elif isinstance(value, six.string_types) and len(value) < 0x40:
            return self.alloc(length=len(value), string=value.encode('ascii'))
        elif isinstance(value, six.string_types) and len(value) < 0xc0:
            raise ValueError(value)
        raise ValueError(value)

class Label(parray.terminated):
    # XXX: Feeling kind of lazy now that all this data-entry is done, and
    #      this doesn't support message-compression at the moment even
    #      though the `Name` object does.
    _object_ = Name

    def isTerminator(self, item):
        return item['length'].int() & 0x3f == 0

    def str(self):
        items = ["{:+#x}".format(item.int()) if item.CompressedQ() else item.str() for item in self]
        return '.'.join(items)

    def alloc(self, items):
        name = items
        if isinstance(name, six.string_types):
            items = name.split('.') if name.endswith('.') else (name + '.').split('.')
            return super(Label, self).alloc(items)
        return super(Label, self).alloc(items)

    def summary(self):
        return "({:d}) {:s}".format(len(self), self.str())

class TYPE(pint.enum, pint.uint16_t):
    _values_ = [
        ('A', 1),
        ('NS', 2),
        ('MD', 3),
        ('MF', 4),
        ('CNAME', 5),
        ('SOA', 6),
        ('MB', 7),
        ('MG', 8),
        ('MR', 9),
        ('NULL', 10),
        ('WKS', 11),
        ('PTR', 12),
        ('HINFO', 13),
        ('MINFO', 14),
        ('MX', 15),
        ('TXT', 16),
    ]

class QTYPE(TYPE):
    _values_ = TYPE._values_ + [
        ('AXFR', 252),
        ('MAILB', 253),
        ('MAILA', 254),
        ('*', 255),
    ]

class CLASS(pint.enum, pint.uint16_t):
    _values_ = [
        ('IN', 1),
        ('CS', 2),
        ('CH', 3),
        ('HS', 4),
    ]

class QCLASS(CLASS):
    _values_ = CLASS._values_ + [
        ('*', 255),
    ]

class RDATA(ptype.definition):
    cache = {}

@RDATA.define
class A(pstruct.type):
    type = TYPE.byname('A'), CLASS.byname('IN')

    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
    ]

    def summary(self):
        return self['ADDRESS'].summary()

@RDATA.define
class NS(pstruct.type):
    type = TYPE.byname('NS'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'NSDNAME'),
    ]

    def summary(self):
        return self['NSDNAME'].str()

@RDATA.define
class MD(pstruct.type):
    type = TYPE.byname('MD'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MF(pstruct.type):
    type = TYPE.byname('MF'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class CNAME(pstruct.type):
    type = TYPE.byname('CNAME'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'CNAME'),
    ]

    def summary(self):
        return self['CNAME'].str()

@RDATA.define
class SOA(pstruct.type):
    type = TYPE.byname('SOA'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MNAME'),
        (Label, 'RNAME'),
        (u32, 'SERIAL'),
        (u32, 'REFRESH'),
        (u32, 'RETRY'),
        (u32, 'EXPIRE'),
        (u32, 'MINIMUM'),
    ]

    def summary(self):
        fields = ['SERIAL', 'REFRESH', 'RETRY', 'EXPIRE', 'MINIMUM']
        items = ["{:d}".format(self[fld].int()) for fld in fields]
        return ' '.join([self['MNAME'].str(), self['RNAME'].str()] + items)

@RDATA.define
class MB(pstruct.type):
    type = TYPE.byname('MB'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MG(pstruct.type):
    type = TYPE.byname('MG'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MGMNAME'),
    ]

    def summary(self):
        return self['MGMNAME'].str()

@RDATA.define
class MR(pstruct.type):
    type = TYPE.byname('MR'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'NEWNAME'),
    ]

    def summary(self):
        return self['NEWNAME'].str()

@RDATA.define
class NULL(ptype.block):
    type = TYPE.byname('NULL'), CLASS.byname('IN')

@RDATA.define
class WKS(pstruct.type):
    type = TYPE.byname('WKS'), CLASS.byname('IN')
    def __BITMAP(self):
        raise NotImplementedError

    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
        (u8, 'PROTOCOL'),
        (__BITMAP, 'BITMAP'),
    ]

@RDATA.define
class PTR(pstruct.type):
    type = TYPE.byname('PTR'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'PTRDNAME'),
    ]

    def summary(self):
        return self['PTRDNAME'].str()

@RDATA.define
class HINFO(pstruct.type):
    type = TYPE.byname('HINFO'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'CPU'),
        (Label, 'OS'),
    ]

    def summary(self):
        return "CPU={:s} OS={:s}".format(self['CPU'].str(), self['OS'].str())

@RDATA.define
class MINFO(pstruct.type):
    type = TYPE.byname('MINFO'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'RMAILBX'),
        (Label, 'EMAILBX'),
    ]

    def summary(self):
        return ' '.join([self['RMAILBX'].str(), self['EMAILBX'].str()])

@RDATA.define
class MX(pstruct.type):
    type = TYPE.byname('MX'), CLASS.byname('IN')

    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'EXCHANGE'),
    ]

    def summary(self):
        return "{:d} {:s}".format(self['PREFERENCE'].int(), self['EXCHANGE'].str())

@RDATA.define
class TXT(pstr.string):
    type = TYPE.byname('TXT'), CLASS.byname('IN')

class QR(pbinary.enum):
    width, _values_ = 1, [
        ('query', 0),
        ('response', 1),
    ]

class OPCODE(pbinary.enum):
    width, _values_ = 4, [
        ('QUERY', 0),
        ('IQUERY', 1),
        ('STATUS', 2),
    ]

class RCODE(pbinary.enum):
    width, _values_ = 4, [
        ('None', 0),
        ('Server', 1),
        ('Name', 2),
        ('Implemented', 2),
        ('Refused', 2),
    ]

class Header(pbinary.flags):
    _fields_ = [
        (QR, 'QR'),
        (OPCODE, 'OPCODE'),
        (1, 'AA'),
        (1, 'TC'),
        (1, 'RD'),
        (1, 'RA'),
        (3, 'Z'),
        (RCODE, 'RCODE'),
    ]

class Q(pstruct.type):
    _fields_ = [
        (Label, 'NAME'),
        (QTYPE, 'TYPE'),
        (QCLASS, 'CLASS'),
    ]

    def summary(self):
        return "{CLASS:s} {TYPE:s} {NAME:s}".format(NAME=self['NAME'].str(), TYPE=self['TYPE'].str(), CLASS=self['CLASS'].str())

class RR(pstruct.type):
    def __RDATA(self):
        res, klass = (self[fld].li.int() for fld in ['TYPE', 'CLASS'])
        try:
            t = RDATA.lookup((res, klass))

        except KeyError:
            res = self['RDLENGTH'].li
            return dyn.block(res.int())

        if issubclass(t, (ptype.block, pstr.string)):
            return dyn.clone(t, length=self['RDLENGTH'].li.int())
        return t

    def __Padding_RDATA(self):
        res, field = self['RDLENGTH'].li, self['RDATA'].li
        return dyn.block(max(0, res.int() - field.size()))

    _fields_ = [
        (Label, 'NAME'),
        (TYPE, 'TYPE'),
        (CLASS, 'CLASS'),
        (u32, 'TTL'),
        (u16, 'RDLENGTH'),
        (__RDATA, 'RDATA'),
        (__Padding_RDATA, 'Padding(RDATA)'),
    ]

    def alloc(self, **fields):
        fields.setdefault('CLASS', 'IN')
        res = super(RR, self).alloc(**fields)
        return res.set(RDLENGtH=res['RDATA'].size())

class Message(pstruct.type):
    class _Counts(pstruct.type):
        _fields_ = [
            (u16, 'QDCOUNT'),
            (u16, 'ANCOUNT'),
            (u16, 'NSCOUNT'),
            (u16, 'ARCOUNT'),
        ]

        def summary(self):
            fields = ['qd', 'an', 'ns', 'ar']
            return ', '.join("{:s}={:d}".format(name, self[fld].int()) for name, fld in zip(fields, self))

    class _Question(parray.type):
        _object_ = Q

        def summary(self):
            iterable = (item.summary() for item in self)
            return "({:d}) {:s}".format(len(self), ', '.join(iterable))

    def __Question(self):
        res = self['Counts'].li
        count = res['QDCOUNT'].int()
        return dyn.clone(self._Question, length=count)

    def __Response(field):
        def field(self, field=field):
            res = self['Counts'].li
            count = res[field].int()
            return dyn.array(RR, count)
        return field

    _fields_ = [
        (u16, 'Id'),
        (Header, 'Header'),
        (_Counts, 'Counts'),
        (__Question, 'Question'),
        (__Response('ANCOUNT'), 'Answer'),
        (__Response('NSCOUNT'), 'Authority'),
        (__Response('ARCOUNT'), 'Additional'),
        (ptype.block, 'Padding'),
    ]

if __name__ == '__main__':
    import ptypes, protocol.dns as dns
    res = 'fce2 0100 0001 0000 0000 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001               '
    res = 'fce2 8183 0001 0000 0001 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001 0000 0600 0100 000e 1000 4001 610c 726f 6f74 2d73 6572 7665 7273 036e 6574 0005 6e73 746c 640c 7665 7269 7369 676e 2d67 7273 0363 6f6d 0078 67b1 a200 0007 0800 0003 8400 093a 8000 0151 80                           '

    data = bytes.fromhex(res)

    a = dns.Message(source=ptypes.prov.bytes(data))
    a=a.l

    print(a['question'])
    print(a['question'][0]['name'])
    print(a['authority'][0])
    x = a['authority'][0]
    print(x['RDATA'])
