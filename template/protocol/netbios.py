import osi.network.inet4, osi.network.inet6, ptypes
from ptypes import *
from . import dns

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class U0(pint.uint_t): pass
class U8(pint.uint8_t): pass
class U16(pint.uint16_t): pass
class U32(pint.uint32_t): pass
class S0(pint.sint_t): pass
class S8(pint.sint8_t): pass
class S16(pint.sint16_t): pass
class S32(pint.sint32_t): pass

class NAME(dns.Name):
    @classmethod
    def __decode_name__(cls, data):
        res, iterable = bytearray(), iter(bytearray(data))
        for item in iterable:
            hi = item - ord(b'A')
            lo = next(iterable, b'A') - ord(b'A')
            res.append(hi * pow(2, 4) + lo)
        return bytes(res).decode('latin1')

    def str(self):
        if self.CompressedQ():
            return super(NAME, self).str()
        res = self['string'].serialize()
        decoded = self.__decode_name__(res)
        stripped = decoded.rstrip('\0')
        return stripped.rstrip()

    def summary(self):
        if self.CompressedQ():
            return super(NAME, self).summary()
        res, encoded = self['length'].int(), super(NAME, self).str()
        return "({:d}) {:s} :> {:s}".format(res, encoded, self.str().rstrip())

class Label(dns.Label):
    _object_ = NAME

class OPCODE(pbinary.enum):
    length, _values_ = 4, [
        ('query', 0),
        ('registration', 5),
        ('release', 6),
        ('WACK', 7),
        ('refresh', 8),
    ]

class RCODE(pbinary.enum):
    length, _fields_ = 4, [
        ('FMT_ERR', 0x1),
        ('SRV_ERR', 0x2),
        ('IMP_ERR', 0x4),
        ('RFS_ERR', 0x5),
        ('ACT_ERR', 0x6),
        ('CFT_ERR', 0x7),
    ]

class HEADER(pbinary.flags):
    _fields_ = [
        (1, 'R'),
        (OPCODE, 'OPCODE'),
        (1, 'AA'),
        (1, 'TC'),
        (1, 'RD'),
        (1, 'RA'),
        (2, 'ZERO'),
        (1, 'B'),
        (RCODE, 'RCODE'),
    ]

class TYPE(dns.QTYPE):
    pass

class CLASS(dns.CLASS):
    pass

class QUESTION_NAME(Label): pass
class QUESTION_TYPE(TYPE): pass
class QUESTION_CLASS(CLASS): pass

class QUESTION(dns.Q):
    _fields_ = [
        (QUESTION_NAME, 'NAME'),
        (QUESTION_TYPE, 'TYPE'),
        (QUESTION_CLASS, 'CLASS'),
    ]
    def summary(self):
        return "{CLASS:s} {TYPE:s} {NAME:s}".format(NAME=self['NAME'].str(), TYPE=self['TYPE'].str(), CLASS=self['CLASS'].str())

class RR_NAME(Label): pass
class RR_TYPE(TYPE): pass
class RR_CLASS(CLASS): pass

class NMPACKET(pstruct.type):
    class _Question(parray.type):
        _object_ = QUESTION
        def summary(self):
            iterable = (item.summary() for item in self)
            return "({:d}) {:s}".format(len(self), ', '.join(iterable))

    def __Question(self):
        res = self['COUNT'].li
        count = res['QDCOUNT'].int()
        return dyn.clone(self._Question, length=count)

    def __Response(field):
        def field(self, field=field):
            res = self['COUNT'].li
            count = res[field].int()
            return dyn.clone(dns.RRset, length=count)
        return field

    _fields_ = [
        (U16, 'NAME_TRN_ID'),
        (HEADER, 'HEADER'),
        (dns.RRcount, 'COUNT'),
        (__Question, 'QUESTION'),
        (__Response('ANCOUNT'), 'ANSWER'),
        (__Response('NSCOUNT'), 'AUTHORITY'),
        (__Response('ARCOUNT'), 'ADDITIONAL'),
        (ptype.block, 'Padding'),
    ]

class SessionPacket(ptype.definition):
    cache = {}

class SSTYPE(pint.enum, U8):
    _values_ = [
        (          'SESSION MESSAGE', 0x00),
        (          'SESSION REQUEST', 0x81),
        ('POSITIVE SESSION RESPONSE', 0x82),
        ('NEGATIVE SESSION RESPONSE', 0x83),
        ('RETARGET SESSION RESPONSE', 0x84),
        (       'SESSION KEEP ALIVE', 0x85),
    ]

class SSFLAGS(pbinary.flags):
    _fields_ = [
        (1, 'E'),
        (7, 'RESERVED'),
    ]

@SessionPacket.define
class SESSION_REQUEST_PACKET(pstruct.type):
    type = 0x81
    _fields_ = [
        (NAME, 'CALLED'),
        (NAME, 'CALLING'),
    ]

@SessionPacket.define
class POSITIVE_SESSION_RESPONSE_PACKET(pstruct.type):
    type = 0x82
    _fields_ = [
        (U0, 'ERROR_CODE'),
    ]

@SessionPacket.define
class NEGATIVE_SESSION_RESPONSE_PACKET(pstruct.type):
    type = 0x83
    class _ERROR_CODE(pint.enum, U8):
        _values_ = [
            (                   'Not listening on called name', 0x80),
            (                 'Not listening for calling name', 0x81),
            (                        'Called name not present', 0x82),
            ('Called name present, but insufficient resources', 0x83),
            (                              'Unspecified error', 0x8F),
        ]
    _fields_ = [
        (_ERROR_CODE, 'ERROR_CODE'),
    ]

@SessionPacket.define
class SESSION_RETARGET_RESPONSE_PACKET(pstruct.type):
    type = 0x84
    _fields_ = [
        (osi.network.inet4.in_addr, 'RETARGET_IP_ADDRESS'),
        (U16, 'PORT'),
    ]

@SessionPacket.define
class SESSSION_MESSAGE_PACKET(ptype.block):
    type = 0x00

@SessionPacket.define
class SESSSION_KEEP_ALIVE_PACKET(ptype.block):
    type = 0x85

class SSPACKET(pstruct.type):
    _fields_ = [
        (SSTYPE, 'TYPE'),
        (SSFLAGS, 'FLAGS'),
        (U16, 'LENGTH'),
        (lambda self: dyn.block(self['LENGTH'].li.int()), 'TRAILER'),
    ]

class ServicePacket(ptype.definition):
    cache = {}

class MSG_TYPE(pint.enum, U8):
    _values_ = [
        (          'DIRECT_UNIQUE DATAGRAM', 0x10),
        (           'DIRECT_GROUP DATAGRAM', 0x11),
        (              'BROADCAST DATAGRAM', 0x12),
        (                  'DATAGRAM ERROR', 0x13),
        (          'DATAGRAM QUERY REQUEST', 0x14),
        ('DATAGRAM POSITIVE QUERY RESPONSE', 0x15),
        ('DATAGRAM NEGATIVE QUERY RESPONSE', 0x16),
    ]

class SVHEADER(pstruct.type):
    class _FLAGS(pbinary.flags):
        class _SNT(pbinary.enum):
            length, _values_ = 2, [
                (0b00, 'B node'),
                (0b01, 'P node'),
                (0b10, 'M node'),
                (0b11, 'NBDD'),
            ]
        _fields_ = [
            (1, 'M'),
            (1, 'F'),
            (_SNT, 'SNT'),
            (4, 'RESERVED'),
        ]
    _fields_ = [
        (MSG_TYPE, 'MSG_TYPE'),
        (_FLAGS, 'FLAGS'),
        (U16, 'DGM_ID'),
        (osi.network.inet4.in_addr, 'SOURCE_IP'),
        (U16, 'SOURCE_PORT'),
        (U16, 'DGM_LENGTH'),
        (U16, 'PACKET_OFFSET'),
    ]

class DIRECT_DATAGRAM(pstruct.type):
    _fields_ = [
        (NAME, 'SOURCE_NAME'),
        (NAME, 'DESTINATION_NAME'),
        (ptype.block, 'USER_DATA'),
    ]

@ServicePacket.define
class DIRECT_UNIQUE_DATAGRAM(DIRECT_DATAGRAM):
    type = 0x10

@ServicePacket.define
class DIRECT_GROUP_DATAGRAM(DIRECT_DATAGRAM):
    type = 0x11

@ServicePacket.define
class BROADCAST_DATAGRAM(DIRECT_DATAGRAM):
    type = 0x12

@ServicePacket.define
class ERROR_DATAGRAM(pstruct.type):
    type = 0x13
    class _ERROR_CODE(pint.enum, U8):
        _fields_ = [
            (   'DESTINATION NAME NOT PRESENT', 0x82),
            (     'INVALID SOURCE NAME FORMAT', 0x83),
            ('INVALID DESTINATION NAME FORMAT', 0x84),
        ]

    _fields_ = [
        (_ERROR_CODE, 'ERROR_CODE'),
    ]

class QUERY_DATAGRAM(pstruct.type):
    _fields_ = [
        (NAME, 'DESTINATION_NAME'),
    ]

@ServicePacket.define
class QUERY_REQUEST_DATAGRAM(QUERY_DATAGRAM):
    type = 0x14

@ServicePacket.define
class POSITIVE_QUERY_RESPONSE_DATAGRAM(QUERY_DATAGRAM):
    type = 0x15

@ServicePacket.define
class NEGATIVE_QUERY_RESPONSE_DATAGRAM(QUERY_DATAGRAM):
    type = 0x16

class SVPACKET(pstruct.type):
    _fields_ = [
        (SVHEADER, 'Header'),
        (ptype.block, 'Packet'),
    ]

if __name__ == '__main__':
    import ptypes, protocol.netbios as nb
    import importlib
    importlib.reload(nb)
    
    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    data = '8096011000010000000000002046484641454245454341434143414341434143414341434143414341434141410000200001'
    z = nb.NMPACKET(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l
    print(z)
    print(z['header'])

    data = '8097011000010000000000002045424644454a46444546454d45474549455046444645434143414341434141410000200001'
    z = nb.NMPACKET(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l
    print(z)
    print(z['header'])

