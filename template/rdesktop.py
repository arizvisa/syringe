import ptypes,logging
from ptypes import *
from ptypes.pint import *
from ptypes.pint import bigendian

class crlf_terminate(parray.terminated):
    _object_ = pint.uint8_t
    def isTerminator(self, value):
        return (len(self.value)>1) and (self.value[-1].int() == 0x0a) and (self.value[-2].int() == 0x0d)

class dictionary(object):   # ptype.dictionary?
    # should provide an interface for looking up ptypes by some specific id
    #   need to implement __new__ in order to allocate .cache
    #   needs a function to create a new packet of a specific id, falling back to
    #       a user-defined unknown packet if able.

    cache = None
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, id):
        try:
            result = cls.cache[id]
        except KeyError:
            result = cls.Unknown
        return result
        
    @classmethod
    def Get(cls, id, size):
        return dyn.clone(cls.Lookup(id), blocksize=lambda s:size)

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

    @classmethod
    def Update(cls, records):
        a = set(cls.cache.keys())
        b = set(records.cache.keys())
        if a.intersection(b):
            logging.warning('%s : Unable to import module %s due to multiple definitions of the same record'%(cls.__module__, repr(records)))
            logging.debug(repr(a.intersection(b)))
            return False
        cls.cache.update(records.cache)
        return True

    @classmethod
    def Merge(cls, records):
        if cls.Update(records):
            # merge record caches into a single one
            records.cache = cls.cache
            return True
        return False

    class Unknown(dyn.block(0)): pass

### X.224
class X224(dictionary): cache = {}
class X224Param(dictionary): cache = {}

### X.224 packets
@X224.Define
class connection_request(pstruct.type):
    type = 0xe
    _fields_ = [
        (uint16_t, 'dest-ref'),
        (uint16_t, 'src-ref'),
        (uint8_t, 'class-option'),
    ]

@X224.Define
class connection_confirm(pstruct.type):
    type = 0xd
    _fields_ = [
        (uint16_t, 'dest-ref'),
        (uint16_t, 'src-ref'),
        (uint8_t, 'class-option'),
    ]

# XXX
@X224.Define
class data(pstruct.type):
    type = 0xf
    _fields_ = [
        (dyn.block(6), 'shareid'),
        (dyn.block(6), 'shareid'),
    ]

### X.224 Parameters
class X224Parameter(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'code'),
        (pint.uint8_t, 'flags'),
        (pint.uint16_t, 'length'),
#        (lambda s: dyn.block(s['length'].l.int()), 'value')
        (lambda s: X224Param.Get(s['code'].l.int(),s['length'].l.int() - 4), 'value'),
    ]

class X224ParameterArray(parray.block):
    _object_ = X224Parameter

@X224Param.Define
class RDPNegotiationRequest(pint.uint32_t, pint.enum):
    type = 0x01
    _values_ = [
        ('PROTOCOL_RDP', 0x00000000),
        ('PROTOCOL_SSL', 0x00000001),
        ('PROTOCOL_HYBRID', 0x00000002),
    ]
@X224Param.Define
class RDPNegotiationResponse(pint.uint32_t, pint.enum):
    type = 0x02
    _values_ = [
        ('PROTOCOL_RDP', 0x00000000),
        ('PROTOCOL_SSL', 0x00000001),
        ('PROTOCOL_HYBRID', 0x00000002),
    ]
@X224Param.Define
class RDPNegotiationFailure(pint.uint32_t, pint.enum):
    type = 0x02
    _values_ = [
        ('SSL_REQUIRED_BY_SERVER', 0x00000001),
        ('SSL_NOT_ALLOWED_BY_SERVER', 0x00000002),
        ('SSL_CERT_NOT_ON_SERVER', 0x00000003),
        ('INCONSISTENT_FLAGS', 0x00000004),
        ('HYBRID_REQUIRED_BY_SERVER', 0x00000005),
        ('SSL_WITH_USER_AUTH_REQUIRED_BY_SERVER', 0x00000006),
    ]

### T.123
class TPDU(pstruct.type):
    def __data(self):
        s = self['length'].l.int()
        if s < 2:
            logging.info("%s : length is (%d < 2)", self.shortname(), s)
            return dyn.block(0)
        return X224.Get(self['type'].l['high'], s-2)

    def __data(self):
        s = self['length'].l.int()
        if s < 2:
            logging.info("%s : length is (%d < 2)", self.shortname(), s)
            return dyn.block(0)
        try:
            result = X224.Lookup(self['type'].l['high'])
        except KeyError:
            result = dyn.block(s - 2)
        return result

    class __type(pbinary.struct):
        _fields_ = [(4, 'high'), (4, 'low')]

    _fields_ = [
        (bigendian(uint8_t), 'length'),
        (__type, 'type'),
        (__data, 'data'),
        (X224ParameterArray, 'param'),
#        (lambda s: dyn.block(s.blocksize() - (s['data'].size() + 2)), 'extra'), # XXX
    ]

class TPKT(pstruct.type):
    class default(pstruct.type):
        def __data(self):
            n=self['length'].l.int() - 4
            return dyn.clone(TPDU, blocksize=lambda s: n)

        _fields_ = [
            (ptype.type, '(version)'),  # 1 byte version
            (bigendian(pint.uint8_t), 'reserved'),
            (bigendian(pint.uint16_t), 'length'),
            (__data, 'data'),
        ]

        def blocksize(self):
            return self['length'].int()

    class rdp5(pstruct.type):
        def __data(self):
            raise NotImplementedError("RDP5 isn't decoding its length correctly")
            n = self['length'].l.int()
            return dyn.clone(TPDU, blocksize=lambda s: n)

        # XXX: maybe length is being decoded wrong, but whatever
        _fields_ = [
            (ptype.type, '(version)'),
            (bigendian(pint.uint16_t), 'length'),
            (__data, 'data'),
        ]

    _fields_ = [
        (bigendian(pint.uint8_t), 'version'),
        (lambda s: (s.default, s.rdp5)[ s['version'].l.int() != 3], 'data')
    ]

    def blocksize(self):
        return self['data']['length'].int()

    pdu = property(fget=lambda s: s['data']['data'])

### entry point
class Stream(parray.infinite):
    _object_ = TPKT

File=Stream

if __name__ == '__main__':
    import ptypes,analyze
    reload(analyze)
    ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
#    ptypes.setsource(ptypes.file('./termdd_1.dat'))
    ptypes.setsource(ptypes.file('./blah.dat'))

    from analyze import *

    z = analyze.Stream()
    z = z.l
#    for x in z:
#        print x

    if False:
        a = TPKT()
        a = a.l
        print a['data']

        b = TPDU(offset=a.getoffset()+a.size())
        b = b.l
    #    print b['data']

    #    c = TPDU(offset=b.getoffset()+b.size())
    #    c = TPDU(offset=c.getoffset()+c.size())
    #    c = c.l
    #    print c
    #
    #    print dyn.block(0x10)(offset=b.getoffset()+b.size()).l.hexdump()

#    a = z[1]['data']
#    b = a['data']
