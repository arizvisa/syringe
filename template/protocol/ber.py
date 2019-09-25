import logging, math, six, builtins
import ptypes, ptypes.bitmap as bitmap
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

    def int(self):
        '''Return the integer from the structure'''
        return reduce(lambda t, item: (t * 2**7) | item['integer'], self, 0)

    def set(self, *integer, **fields):
        '''Apply the specified integer to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer

            # calculate the number of 7-bit pieces for our integer
            res = math.floor(math.log(integer) / math.log(2**7) + 1)
            length = fields.pop('length', math.trunc(res))

            # slice the integer into 7-bit pieces. we could use ptypes.bitmap, but
            # that requires reading documentation and things. so let's avoid that.
            res = []
            while integer > 0:
                res.insert(0, integer & (2**7 - 1))
                integer >>= 7

            # append any extra zeroes in order to pad the list to the specified length
            res = [0] * (length - len(res)) + res
            return self.alloc(length=length).set([[1, n] for n in res[:-1]] + [[0, res[-1]]])
        return super(IdentifierLong, self).set(*integer, **fields)

class Length(pbinary.struct):
    '''Indefinite Length (short form) 8.1.3.3'''
    def __value(self):
        return (self['count']*8) if self['form'] else 0

    _fields_ = [
        (1, 'form'),
        (7, 'count'),
        (__value, 'value'),
    ]

    def int(self):
        '''Return the length from the structure'''
        return self['value'] if self['form'] else self['count']

    def set(self, *integer, **fields):
        '''Apply the specified length to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer

            # if our integer can be fit within 7 bits, then just assign it to 'count'
            if integer < 2**7:
                return self.alloc(form=0).set(count=integer)

            # otherwise, figure out how many bytes we need to allocate and then
            # simply assign the integer to them
            res = math.floor(math.log(integer) / math.log(2**8) + 1)
            return self.alloc(form=1, count=math.trunc(res)).set(value=integer)
        return super(Length, self).set(*integer, **fields)

    def isIndefinite(self):
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'isIndefinite')
        return self['form'] == self['count'] == 0

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Length, self).summary()) + (' Indefinite' if self.isIndefinite() else '')

class Tag(pbinary.struct):
    def __TagLong(self):
        return IdentifierLong if self['TagShort'] == 0x1f else dyn.clone(IdentifierLong, length=0)

    _fields_ = [
        (5, 'TagShort'),
        (__TagLong, 'TagLong'),
    ]

    def int(self):
        '''Return the tag number based on the values in our fields'''
        if self['TagShort'] < 2**5 - 1:
            return self['TagShort']
        return self['TagLong'].int()

    def set(self, *integer, **fields):
        '''Apply the tag number to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer
            return self.alloc(TagShort=integer) if integer < 2**5 - 1 else self.alloc(TagShort=2**5 - 1).set(TagLong=integer)
        return super(Tag, self).set(*integer, **fields)

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Tag, self).summary())

class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed'),
        (Tag, 'Tag'),
    ]

    def summary(self):
        klass, constructedQ, tag = self['Class'], self['Constructed'], self['Tag'].int()
        return 'class:{:d} tag:{:d} {:s}'.format(klass, tag, 'Constructed' if constructedQ else 'Universal')

class Structured(parray.type):
    def __getitem__(self, index):
        try:
            if hasattr(self, '_fields_'):
                index = next(i for i, (_, name) in enumerate(self._fields_) if name.lower() == index.lower())
        except:
            return super(Structured, self).__getitem__(index)
        return super(Structured, self).__getitem__(index)

    def summary(self):
        if hasattr(self, '_fields_'):
            res = ("{:s}={:s}".format(name, n.__element__() if isinstance(n, Element) else n.classname()) for (_, name), n in zip(self._fields_, self.value))
        else:
            res = (n.__element__() if isinstance(n, Element) else n.classname() for n in self.value)
        return "{:s} : {{ {:s} }}".format(self.__element__(), ', '.join(res))

    def _object_(self):
        protocol = getattr(self.parent, 'Protocol', Protocol)
        if hasattr(self, '_fields_') and len(self.value) < len(self._fields_):
            t, name = self._fields_[len(self.value)]
            return dyn.clone(protocol.default, _object_=lambda self, res=dyn.clone(t): res)
        return dyn.clone(protocol.default)

    def __fields(self):
        for _, name in self._fields_:
            yield name
        return
    def fields(self):
        return [ name for name in self.__fields() ]
    def iterfields(self):
        for name in self.__fields():
            yield name
        return

    def alloc(self, *args, **fields):
        if hasattr(self, '_fields_'):
            res, protocol = [], getattr(self.parent, 'Protocol', Protocol)

            # iterate through all of our fields
            for t, name in self._fields_:

                # If no field was specified, then construct the default
                if name not in fields:
                    E = protocol.default().alloc(Value=t)

                # If an Element instance was specified, then use that
                elif isinstance(fields[name], Element):
                    E = fields[name]

                # If a ptype instance was provided, then use that as the Value for an Element
                elif isinstance(fields[name], ptype.base):
                    E = protocol.default().alloc(Value=fields[name])

                # If a just a ptype was specified, then instantiate it as the Value for an element
                elif ptypes.istype(fields[name]):
                    E = protocol.default().alloc(Value=fields[name]().a)

                # Otherwise, we just simply assign the field to the Element's Value
                else:
                    E = protocol.default().alloc(Value=t().a.set(fields[name]))

                res.append(E)
            return super(Structured, self).alloc(res, length=len(res))
        return super(Structured, self).alloc(*args, **fields)

class String(pstr.string):
    def set(self, value):
        return self.alloc(length=len(value)).__setvalue__(value)

### Element structure
class Protocol(ptype.definition):
    attribute, cache = 'Class', {}
    class UnknownConstruct(parray.block, Structured):
        def classname(self):
            klass, tag = self.type
            return "UnknownConstruct<{:d},{:d}>".format(klass, tag)
    class Unknown(ptype.block):
        def classname(self):
            klass, tag = self.type
            return "UnknownPrimitive<{:d},{:d}>".format(klass, tag)

class Element(pstruct.type):
    Protocol = Protocol
    def __apply_length_type(self, result, length, indefiniteQ=False):
        '''Apply the specified length to the type specified by variable'''

        # Determine how to assign length to a type
        # FIXME: These cases should be implicitly defined instead of explicitly
        if issubclass(result, parray.block):
            result.blocksize = lambda self, cb=length: cb

        elif indefiniteQ and issubclass(result, parray.terminated):
            # Type['Constructed']
            # Length['Form'] and !Length['Value']
            result.isTerminator = lambda self, value: isinstance(value['Value'], EOC)

        elif ptype.iscontainer(result):
            result = result

        elif ptype.istype(result):
            result.length = length

        return result

    def __apply_length_instance(self, result, length, indefiniteQ=False):
        '''Apply the specified length to the instance specified by variable'''

        # Determine how to assign length to an already existing instance
        # FIXME: These cases should be implicitly defined instead of explicitly
        if isinstance(result, parray.block):
            result.blocksize = lambda cb=length: cb

        elif indefiniteQ and isinstance(result, parray.terminated):
            # Type['Constructed']
            # Length['Form'] and !Length['Value']
            result.isTerminator = lambda value: isinstance(value['Value'], EOC)

        elif isinstance(result, ptype.container):
            result = result

        elif isinstance(result, ptype.type):
            result.length = length

        return result

    def __type__(self, type, length, **attrs):
        klass, constructedQ, tag = (type[fld] for fld in ['Class','Constructed','Tag'])

        # Now we can look up the type that we need by grabbing hte protocol, then
        # using it to determine the class, and then its tag.
        protocol = self.Protocol

        K = protocol.lookup(klass)
        try:
            result = K.lookup(tag.int())

        except KeyError:
            result = protocol.UnknownConstruct if constructedQ else protocol.Unknown
            attrs.setdefault('type', (klass, tag.int()))
        return dyn.clone(result, **attrs)

    def __element__(self):
        '''Return the typename so that it's a lot easier to read.'''

        if self.initializedQ():
            res = self['Value']
        else:
            # XXX: This is tied into the Structured mixin
            res = self._object_() if hasattr(self, '_object_') else self.__type__(self['Type'], self['Length'])
        return res.typename()

    def __Value(self):
        '''Return the correct ptype and size it correctly according to Element's properties.'''
        t, length = (self[fld].li for fld in ['Type','Length'])

        # XXX: This is tied into the Structured mixin
        result = self._object_() if hasattr(self, '_object_') else self.__type__(t, length)

        # Apply our length to the type we determined
        return self.__apply_length_type(result, length.int(), length.isIndefinite())

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'), # FIXME: Distinguish between definite and indefinite (long and short) forms
        (__Value, 'Value'),
    ]

    def alloc(self, **fields):

        # If a Value was provided during allocation without the Type, then assign
        # one from the Universal/Primitive class using whatever its Tag is in .type
        value = fields.get('Value', None)
        if hasattr(value, 'type'):
            klass, tag = value.type
            constructedQ = 1 if (ptypes.istype(value) and issubclass(value, Structured)) or isinstance(value, Structured) else  0
            fields.setdefault('Type', Type().alloc(Class=klass, Constructed=constructedQ).set(Tag=tag))

        if 'Length' in fields:
            return super(Element, self).alloc(**fields)

        res = super(Element, self).alloc(**fields)
        res['Length'].set(res['Value'].size())
        self.__apply_length_instance(res['Value'], res['Value'].size(), res['Length'].isIndefinite())
        return res
Protocol.default = Element

### Element classes
class ProtocolClass(ptype.definition):
    attribute = 'tag'

    @classmethod
    def __set__(cls, type, object):
        if isinstance(type, six.integer_types):
            object.type = cls.Class, type
            return super(ProtocolClass, cls).__set__(type, object)
        return super(ProtocolClass, cls).__set__(type, object)

@Protocol.define
class Universal(ProtocolClass):
    Class, cache = 00, {}
    # FIXME: These types need to distinguish between constructed and non-constructed
    #        types instead of just generalizing them.
Protocol.Universal = Universal

@Protocol.define
class Application(ProtocolClass):
    Class, cache = 01, {}
    # FIXME: This needs to be unique to the instance of all ber.Element types
    #        used by the application.
Protocol.Application = Application

@Protocol.define
class Context(ProtocolClass):
    Class, cache = 02, {}
    # FIXME: This needs to be unique to a specific ber.Element type
Protocol.Context = Context

@Protocol.define
class Private(ProtocolClass):
    Class, cache = 03, {}
Protocol.Private = Private

### Tag definitions (X.208)
@Universal.define
class EOC(ptype.type):
    tag = 0x00
    # Required only if the length field specifies it

@Universal.define
class BOOLEAN(ptype.block):
    tag = 0x01

@Universal.define
class INTEGER(pint.uint_t):
    tag = 0x02

@Universal.define
class BITSTRING(ptype.block):
    tag = 0x03

@Universal.define
class OCTETSTRING(ptype.block):
    tag = 0x04
    def summary(self):
        res = str().join(map('{:02X}'.format, map(six.byte2int, self.serialize())))
        return "({:d}) {:s}".format(self.size(), res)

@Universal.define
class NULL(ptype.block):
    tag = 0x05

@Universal.define
class OBJECT_IDENTIFIER(ptype.type):
    tag = 0x06

    def set(self, string):
        if string in self._values_.viewvalues():
            res = dict((v, k) for k, v in self._values_.viewitems())
            return self.set(res[string])

        res = map(int, string.split('.'))
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
        return super(OBJECT_IDENTIFIER, self).set(str().join(map(six.int2byte, val)))

    def str(self):
        data = map(six.byte2int, self.serialize())
        if len(data) > 0:
            res = [data[0] / 40, data.pop(0) % 40]
            data = iter(data)
            for n in data:
                val = bitmap.new(0,0)
                while n & 0x80:
                    val = bitmap.push(val, (n & 0x7f, 7))
                    n = next(data)
                val = bitmap.push(val, (n, 7))
                res.append(bitmap.int(val))
            return '.'.join(map("{:d}".format, res))
        return '0'

    def summary(self):
        oid,data = self.str(),self.serialize().encode('hex')
        if oid in self._values_:
            return '{:s} ({:s}) ({:s})'.format(self._values_[oid],oid,data)
        return '{:s} ({:s})'.format(oid,data)

    # https://support.microsoft.com/en-us/help/287547/object-ids-associated-with-microsoft-cryptography
    _values_ = [
        ('spcIndirectDataContext', '1.3.6.1.4.1.311.2.1.4'),
        ('spcStatementType', '1.3.6.1.4.1.311.2.1.11'),
        ('spcSpOpusInfo', '1.3.6.1.4.1.311.2.1.12'),
        ('individualCodeSigning', '1.3.6.1.4.1.311.2.1.21'),
        ('commercialCodeSigning', '1.3.6.1.4.1.311.2.1.22'),
        ('SPC_MS_JAVA_SOMETHING', '1.3.6.1.4.1.311.15.1'),
        ('spcPelmageData', '1.3.6.1.4.1.311.2.1.15'),
        ('spcLink', '1.3.6.1.4.1.311.2.1.25'),
        ('SPC_TIME_STAMP_REQUEST_OBJID', '1.3.6.1.4.1.311.3.2.1'),
        ('SPC_SIPINFO_OBJID', '1.3.6.1.4.1.311.2.1.30'),
        ('SPC_PE_IMAGE_PAGE_HASHES_V1', '1.3.6.1.4.1.311.2.3.1'), # Page hash using SHA1 */
        ('SPC_PE_IMAGE_PAGE_HASHES_V2', '1.3.6.1.4.1.311.2.3.2'), # Page hash using SHA256 */
        ('SPC_NESTED_SIGNATURE_OBJID', '1.3.6.1.4.1.311.2.4.1'),
        ('SPC_RFC3161_OBJID', '1.3.6.1.4.1.311.3.3.1'),

        # Authenticode PE
        ('codeSigning', '1.3.6.1.5.5.7.3.3'),
        ('timeStamping', '1.3.6.1.5.5.7.3.8'),
        ('SPC_KP_LIFETIME_SIGNING_OBJID',  '1.3.6.1.4.1.311.10.3.13'),

        # PKCS #7 & #9
        ('md5', '1.2.840.113549.2.5'),
        ('rsa', '1.3.14.3.2.1.1'),
        ('desMAC', '1.3.14.3.2.10'),
        ('rsaSignature', '1.3.14.3.2.11'),
        ('dsa', '1.3.14.3.2.12'),
        ('dsaWithSHA', '1.3.14.3.2.13'),
        ('mdc2WithRSASignature', '1.3.14.3.2.14'),
        ('shaWithRSASignature', '1.3.14.3.2.15'),
        ('dhWithCommonModulus', '1.3.14.3.2.16'),
        ('desEDE', '1.3.14.3.2.17'),
        ('sha', '1.3.14.3.2.18'),
        ('mdc-2', '1.3.14.3.2.19'),
        ('dsaCommon', '1.3.14.3.2.20'),
        ('dsaCommonWithSHA', '1.3.14.3.2.21'),
        ('rsaKeyTransport', '1.3.14.3.2.22'),
        ('keyed-hash-seal', '1.3.14.3.2.23'),
        ('md2WithRSASignature', '1.3.14.3.2.24'),
        ('md5WithRSASignature', '1.3.14.3.2.25'),
        ('sha1', '1.3.14.3.2.26'),
        ('dsaWithSHA1', '1.3.14.3.2.27'),
        ('dsaWithCommandSHA1', '1.3.14.3.2.28'),
        ('sha-1WithRSAEncryption', '1.3.14.3.2.29'),
        ('contentType', '1.2.840.113549.1.9.3'),
        ('messageDigest', '1.2.840.113549.1.9.4'),
        ('signingTime', '1.2.840.113549.1.9.5'),
        ('counterSignature', '1.2.840.113549.1.9.6'),
        ('challengePassword', '1.2.840.113549.1.9.7'),
        ('unstructuredAddress', '1.2.840.113549.1.9.8'),
        ('extendedCertificateAttributes', '1.2.840.113549.1.9.9'),
        ('rsaEncryption', '1.2.840.113549.1.1.1'),
        ('md2withRSAEncryption', '1.2.840.113549.1.1.2'),
        ('md4withRSAEncryption', '1.2.840.113549.1.1.3'),
        ('md5withRSAEncryption', '1.2.840.113549.1.1.4'),
        ('sha1withRSAEncryption', '1.2.840.113549.1.1.5'),
        ('rsaOAEPEncryptionSET', '1.2.840.113549.1.1.6'),
        ('dsa', '1.2.840.10040.4.1'),
        ('dsaWithSha1', '1.2.840.10040.4.3'),

        ('itu-t recommendation t 124 version(0) 1', '0.0.20.124.0.1'),
    ]
    _values_ = dict((__oid, __name) for __name, __oid in _values_)

@Universal.define
class EXTERNAL(ptype.block):
    tag = 0x08

@Universal.define
class REAL(ptype.block):
    tag = 0x09

@Universal.define
class ENUMERATED(ptype.block):
    tag = 0x0a

@Universal.define
class UTF8String(String):
    tag = 0x0c

@Universal.define
class SEQUENCE(parray.block, Structured):
    tag = 0x10

@Universal.define
class SET(parray.block, Structured):
    tag = 0x11

@Universal.define
class NumericString(ptype.block):
    tag = 0x12

@Universal.define
class PrintableString(String):
    tag = 0x13

@Universal.define
class T61String(String):
    tag = 0x14

@Universal.define
class IA5String(String):
    tag = 0x16

@Universal.define
class UTCTime(String):
    tag = 0x17

@Universal.define
class VisibleString(ptype.block):
    tag = 0x1a

@Universal.define
class GeneralString(String):
    tag = 0x1b

@Universal.define
class UniversalString(String):
    tag = 0x1c

@Universal.define
class CHARACTER_STRING(String):
    tag = 0x1d

@Universal.define
class BMPString(String):
    tag = 0x1e

### End of Universal definitions

### Base structures
class Packet(Element):
    byteorder = ptypes.config.byteorder.bigendian

class File(Element):
    byteorder = ptypes.config.byteorder.bigendian

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
        print x.int()
        print int(x['TagLong'])

    def test_length():
        res = bitmap.zero
        res = bitmap.push(res, (0, 1))
        res = bitmap.push(res, (38, 7))
        x = pbinary.new(ber.Length,source=ptypes.prov.string(bitmap.data(res)))
        print x.l
        print x.int()

        res = bitmap.zero
        res = bitmap.push(res, (0x81,8))
        res = bitmap.push(res, (0xc9,8))
        x = pbinary.new(ber.Length,source=ptypes.prov.string(bitmap.data(res)))
        print x.l
        print x.int()
