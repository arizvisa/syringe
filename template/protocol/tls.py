import ptypes, math, datetime, time
from . import ber, tlsext
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class sint8(pint.sint8_t): pass
class sint16(pint.sint16_t): pass
class sint24(pint.sint_t): length = 3
class sint32(pint.sint32_t): pass
class sint64(pint.sint64_t): pass
class uint8(pint.uint8_t): pass
class uint16(pint.uint16_t): pass
class uint24(pint.uint_t): length = 3
class uint32(pint.uint32_t): pass
class uint64(pint.uint64_t): pass

class ProtocolVersion(pstruct.type):
    _fields_ = [
        (uint8, 'major'),
        (uint8, 'minor'),
    ]

    def summary(self):
        return "major={:d} minor={:d}".format(self['major'].int(), self['minor'].int())

class ContentType(pint.enum, uint8):
    _values_ = [
        ('change_cipher_spec', 20),
        ('alert', 21),
        ('handshake', 22),
        ('application_data', 23),
    ]

class TLSRecord(ptype.definition):
    cache = {}

class Record(pstruct.type):
    def __fragment(self):
        res, cb = (self[fld].li for fld in ['type', 'length'])
        try:
            t = TLSRecord.lookup(res.int())
            return dyn.blockarray(t, cb.int())
        except KeyError:
            pass
        return dyn.block(cb.int())

    def __unparsed(self):
        res = self['length'].li
        return dyn.block(res.int() - self['fragment'].li.size())

    _fields_ = [
        (ContentType, 'type'),
        (ProtocolVersion, 'version'),
        (uint16, 'length'),
        (__fragment, 'fragment'),
        (__unparsed, 'unparsed'),
    ]

@TLSRecord.define
class ChangeCipherSpec(pstruct.type):
    type = 20

    class _type(pint.enum, uint8):
        _values_ = [
            ('change_cipher_spec', 1),
        ]

    _fields_ = [
        (_type, 'type'),
    ]

class AlertLevel(pint.enum, uint8):
    _values_ = [
        ('warning', 1),
        ('fatal', 2),
    ]

class AlertDescription(pint.enum, uint8):
    _values_ = [
        ('close_notify', 0),
        ('unexpected_message', 10),
        ('bad_record_mac', 20),
        ('decryption_failed_RESERVED', 21),
        ('record_overflow', 22),
        ('decompression_failure', 30),
        ('handshake_failure', 40),
        ('no_certificate_RESERVED', 41),
        ('bad_certificate', 42),
        ('unsupported_certificate', 43),
        ('certificate_revoked', 44),
        ('certificate_expired', 45),
        ('certificate_unknown', 46),
        ('illegal_parameter', 47),
        ('unknown_ca', 48),
        ('access_denied', 49),
        ('decode_error', 50),
        ('decrypt_error', 51),
        ('export_restriction_RESERVED', 60),
        ('protocol_version', 70),
        ('insufficient_security', 71),
        ('internal_error', 80),
        ('user_canceled', 90),
        ('no_renegotiation', 100),
        ('unsupported_extension', 110),
    ]

@TLSRecord.define
class Alert(pstruct.type):
    type = 21
    _fields_ = [
        (AlertLevel, 'level'),
        (AlertDescription, 'description'),
    ]

class HandshakeType(pint.enum, uint8):
    _values_ = [
        ('hello_request', 0),
        ('client_hello', 1),
        ('server_hello', 2),
        ('certificate', 11),
        ('server_key_exchange ', 12),
        ('certificate_request', 13),
        ('server_hello_done', 14),
        ('certificate_verify', 15),
        ('client_key_exchange', 16),
        ('finished', 20),
    ]

class HandshakeRecord(ptype.definition):
    cache = {}

@TLSRecord.define
class Handshake(pstruct.type):
    type = 22
    def __body(self):
        res, cb = (self[fld].li for fld in ['type', 'length'])
        return HandshakeRecord.withdefault(res.int(), ptype.block, length=cb.int())

    def __missing(self):
        res = self['length'].li
        return dyn.block(res.int() - self['body'].li.size())

    _fields_ = [
        (HandshakeType, 'type'),
        (uint24, 'length'),
        (__body, 'body'),
        (__missing, 'missing'),
    ]

@HandshakeRecord.define
class HelloRequest(pstruct.type):
    type = 0
    _fields_ = []

class gmt_unix_time(uint32):
    def datetime(self):
        cons, res = datetime.datetime, self.__getvalue__()
        return cons.fromtimestamp(res, datetime.timezone.utc)
    def get(self):
        return self.datetime()
    def set(self, *args, **fields):
        cons, now = datetime.datetime, time.time()
        dt, = args or [cons.fromtimestamp(now, datetime.timezone.utc)]
        epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        delta = dt.astimezone(datetime.timezone.utc) - epoch
        res = math.trunc(delta.total_seconds())
        return super(gmt_unix_time, self).set(res, **fields)
    def summary(self):
        dt, tzinfo = self.datetime(), datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone)))
        return "({:#0{:d}x}) {:s}".format(self.int(), 2 + 2 * self.size(), dt.astimezone(tzinfo).isoformat())

class Random(pstruct.type):
    _fields_ = [
        (gmt_unix_time, 'gmt_unix_time'),
        (dyn.block(28), 'random_bytes'),
    ]
    def summary(self):
        ts, random = self['gmt_unix_time'], self['random_bytes'].serialize()
        return "gmt_unix_time={:s} random_bytes={:s}".format(ts.summary(), str().join(map("{:02x}".format, bytearray(random))))

class SessionID(pstruct.type):
    _fields_ = [
        (uint8, 'length'),
        (lambda self: dyn.clone(pint.uint_t, length=self['length'].li.int()), 'id'),
    ]

    def int(self):
        res = self['id']
        return res.int()

    def summary(self):
        res, session = self['length'], self['id'].serialize()
        if res.int():
            return "length={:d} id={:s}".format(res.int(), str().join(map("{:02x}".format, bytearray(session))))
        return "length={:d}".format(res.int())

class CipherSuite(pint.enum, uint16):
    _values_ = [
        (0x00,0x00,'TLS_NULL_WITH_NULL_NULL'),
        (0x00,0x01,'TLS_RSA_WITH_NULL_MD5'),
        (0x00,0x02,'TLS_RSA_WITH_NULL_SHA'),
        (0x00,0x03,'TLS_RSA_EXPORT_WITH_RC4_40_MD5'),
        (0x00,0x04,'TLS_RSA_WITH_RC4_128_MD5'),
        (0x00,0x05,'TLS_RSA_WITH_RC4_128_SHA'),
        (0x00,0x06,'TLS_RSA_EXPORT_WITH_RC2_CBC_40_MD5'),
        (0x00,0x07,'TLS_RSA_WITH_IDEA_CBC_SHA'),
        (0x00,0x08,'TLS_RSA_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x09,'TLS_RSA_WITH_DES_CBC_SHA'),
        (0x00,0x0A,'TLS_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x0B,'TLS_DH_DSS_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x0C,'TLS_DH_DSS_WITH_DES_CBC_SHA'),
        (0x00,0x0D,'TLS_DH_DSS_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x0E,'TLS_DH_RSA_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x0F,'TLS_DH_RSA_WITH_DES_CBC_SHA'),
        (0x00,0x10,'TLS_DH_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x11,'TLS_DHE_DSS_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x12,'TLS_DHE_DSS_WITH_DES_CBC_SHA'),
        (0x00,0x13,'TLS_DHE_DSS_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x14,'TLS_DHE_RSA_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x15,'TLS_DHE_RSA_WITH_DES_CBC_SHA'),
        (0x00,0x16,'TLS_DHE_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x17,'TLS_DH_anon_EXPORT_WITH_RC4_40_MD5'),
        (0x00,0x18,'TLS_DH_anon_WITH_RC4_128_MD5'),
        (0x00,0x19,'TLS_DH_anon_EXPORT_WITH_DES40_CBC_SHA'),
        (0x00,0x1A,'TLS_DH_anon_WITH_DES_CBC_SHA'),
        (0x00,0x1B,'TLS_DH_anon_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x1E,'TLS_KRB5_WITH_DES_CBC_SHA'),
        (0x00,0x1F,'TLS_KRB5_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x20,'TLS_KRB5_WITH_RC4_128_SHA'),
        (0x00,0x21,'TLS_KRB5_WITH_IDEA_CBC_SHA'),
        (0x00,0x22,'TLS_KRB5_WITH_DES_CBC_MD5'),
        (0x00,0x23,'TLS_KRB5_WITH_3DES_EDE_CBC_MD5'),
        (0x00,0x24,'TLS_KRB5_WITH_RC4_128_MD5'),
        (0x00,0x25,'TLS_KRB5_WITH_IDEA_CBC_MD5'),
        (0x00,0x26,'TLS_KRB5_EXPORT_WITH_DES_CBC_40_SHA'),
        (0x00,0x27,'TLS_KRB5_EXPORT_WITH_RC2_CBC_40_SHA'),
        (0x00,0x28,'TLS_KRB5_EXPORT_WITH_RC4_40_SHA'),
        (0x00,0x29,'TLS_KRB5_EXPORT_WITH_DES_CBC_40_MD5'),
        (0x00,0x2A,'TLS_KRB5_EXPORT_WITH_RC2_CBC_40_MD5'),
        (0x00,0x2B,'TLS_KRB5_EXPORT_WITH_RC4_40_MD5'),
        (0x00,0x2C,'TLS_PSK_WITH_NULL_SHA'),
        (0x00,0x2D,'TLS_DHE_PSK_WITH_NULL_SHA'),
        (0x00,0x2E,'TLS_RSA_PSK_WITH_NULL_SHA'),
        (0x00,0x2F,'TLS_RSA_WITH_AES_128_CBC_SHA'),
        (0x00,0x30,'TLS_DH_DSS_WITH_AES_128_CBC_SHA'),
        (0x00,0x31,'TLS_DH_RSA_WITH_AES_128_CBC_SHA'),
        (0x00,0x32,'TLS_DHE_DSS_WITH_AES_128_CBC_SHA'),
        (0x00,0x33,'TLS_DHE_RSA_WITH_AES_128_CBC_SHA'),
        (0x00,0x34,'TLS_DH_anon_WITH_AES_128_CBC_SHA'),
        (0x00,0x35,'TLS_RSA_WITH_AES_256_CBC_SHA'),
        (0x00,0x36,'TLS_DH_DSS_WITH_AES_256_CBC_SHA'),
        (0x00,0x37,'TLS_DH_RSA_WITH_AES_256_CBC_SHA'),
        (0x00,0x38,'TLS_DHE_DSS_WITH_AES_256_CBC_SHA'),
        (0x00,0x39,'TLS_DHE_RSA_WITH_AES_256_CBC_SHA'),
        (0x00,0x3A,'TLS_DH_anon_WITH_AES_256_CBC_SHA'),
        (0x00,0x3B,'TLS_RSA_WITH_NULL_SHA256'),
        (0x00,0x3C,'TLS_RSA_WITH_AES_128_CBC_SHA256'),
        (0x00,0x3D,'TLS_RSA_WITH_AES_256_CBC_SHA256'),
        (0x00,0x3E,'TLS_DH_DSS_WITH_AES_128_CBC_SHA256'),
        (0x00,0x3F,'TLS_DH_RSA_WITH_AES_128_CBC_SHA256'),
        (0x00,0x40,'TLS_DHE_DSS_WITH_AES_128_CBC_SHA256'),
        (0x00,0x41,'TLS_RSA_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x42,'TLS_DH_DSS_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x43,'TLS_DH_RSA_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x44,'TLS_DHE_DSS_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x45,'TLS_DHE_RSA_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x46,'TLS_DH_anon_WITH_CAMELLIA_128_CBC_SHA'),
        (0x00,0x67,'TLS_DHE_RSA_WITH_AES_128_CBC_SHA256'),
        (0x00,0x68,'TLS_DH_DSS_WITH_AES_256_CBC_SHA256'),
        (0x00,0x69,'TLS_DH_RSA_WITH_AES_256_CBC_SHA256'),
        (0x00,0x6A,'TLS_DHE_DSS_WITH_AES_256_CBC_SHA256'),
        (0x00,0x6B,'TLS_DHE_RSA_WITH_AES_256_CBC_SHA256'),
        (0x00,0x6C,'TLS_DH_anon_WITH_AES_128_CBC_SHA256'),
        (0x00,0x6D,'TLS_DH_anon_WITH_AES_256_CBC_SHA256'),
        (0x00,0x84,'TLS_RSA_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x85,'TLS_DH_DSS_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x86,'TLS_DH_RSA_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x87,'TLS_DHE_DSS_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x88,'TLS_DHE_RSA_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x89,'TLS_DH_anon_WITH_CAMELLIA_256_CBC_SHA'),
        (0x00,0x8A,'TLS_PSK_WITH_RC4_128_SHA'),
        (0x00,0x8B,'TLS_PSK_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x8C,'TLS_PSK_WITH_AES_128_CBC_SHA'),
        (0x00,0x8D,'TLS_PSK_WITH_AES_256_CBC_SHA'),
        (0x00,0x8E,'TLS_DHE_PSK_WITH_RC4_128_SHA'),
        (0x00,0x8F,'TLS_DHE_PSK_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x90,'TLS_DHE_PSK_WITH_AES_128_CBC_SHA'),
        (0x00,0x91,'TLS_DHE_PSK_WITH_AES_256_CBC_SHA'),
        (0x00,0x92,'TLS_RSA_PSK_WITH_RC4_128_SHA'),
        (0x00,0x93,'TLS_RSA_PSK_WITH_3DES_EDE_CBC_SHA'),
        (0x00,0x94,'TLS_RSA_PSK_WITH_AES_128_CBC_SHA'),
        (0x00,0x95,'TLS_RSA_PSK_WITH_AES_256_CBC_SHA'),
        (0x00,0x96,'TLS_RSA_WITH_SEED_CBC_SHA'),
        (0x00,0x97,'TLS_DH_DSS_WITH_SEED_CBC_SHA'),
        (0x00,0x98,'TLS_DH_RSA_WITH_SEED_CBC_SHA'),
        (0x00,0x99,'TLS_DHE_DSS_WITH_SEED_CBC_SHA'),
        (0x00,0x9A,'TLS_DHE_RSA_WITH_SEED_CBC_SHA'),
        (0x00,0x9B,'TLS_DH_anon_WITH_SEED_CBC_SHA'),
        (0x00,0x9C,'TLS_RSA_WITH_AES_128_GCM_SHA256'),
        (0x00,0x9D,'TLS_RSA_WITH_AES_256_GCM_SHA384'),
        (0x00,0x9E,'TLS_DHE_RSA_WITH_AES_128_GCM_SHA256'),
        (0x00,0x9F,'TLS_DHE_RSA_WITH_AES_256_GCM_SHA384'),
        (0x00,0xA0,'TLS_DH_RSA_WITH_AES_128_GCM_SHA256'),
        (0x00,0xA1,'TLS_DH_RSA_WITH_AES_256_GCM_SHA384'),
        (0x00,0xA2,'TLS_DHE_DSS_WITH_AES_128_GCM_SHA256'),
        (0x00,0xA3,'TLS_DHE_DSS_WITH_AES_256_GCM_SHA384'),
        (0x00,0xA4,'TLS_DH_DSS_WITH_AES_128_GCM_SHA256'),
        (0x00,0xA5,'TLS_DH_DSS_WITH_AES_256_GCM_SHA384'),
        (0x00,0xA6,'TLS_DH_anon_WITH_AES_128_GCM_SHA256'),
        (0x00,0xA7,'TLS_DH_anon_WITH_AES_256_GCM_SHA384'),
        (0x00,0xA8,'TLS_PSK_WITH_AES_128_GCM_SHA256'),
        (0x00,0xA9,'TLS_PSK_WITH_AES_256_GCM_SHA384'),
        (0x00,0xAA,'TLS_DHE_PSK_WITH_AES_128_GCM_SHA256'),
        (0x00,0xAB,'TLS_DHE_PSK_WITH_AES_256_GCM_SHA384'),
        (0x00,0xAC,'TLS_RSA_PSK_WITH_AES_128_GCM_SHA256'),
        (0x00,0xAD,'TLS_RSA_PSK_WITH_AES_256_GCM_SHA384'),
        (0x00,0xAE,'TLS_PSK_WITH_AES_128_CBC_SHA256'),
        (0x00,0xAF,'TLS_PSK_WITH_AES_256_CBC_SHA384'),
        (0x00,0xB0,'TLS_PSK_WITH_NULL_SHA256'),
        (0x00,0xB1,'TLS_PSK_WITH_NULL_SHA384'),
        (0x00,0xB2,'TLS_DHE_PSK_WITH_AES_128_CBC_SHA256'),
        (0x00,0xB3,'TLS_DHE_PSK_WITH_AES_256_CBC_SHA384'),
        (0x00,0xB4,'TLS_DHE_PSK_WITH_NULL_SHA256'),
        (0x00,0xB5,'TLS_DHE_PSK_WITH_NULL_SHA384'),
        (0x00,0xB6,'TLS_RSA_PSK_WITH_AES_128_CBC_SHA256'),
        (0x00,0xB7,'TLS_RSA_PSK_WITH_AES_256_CBC_SHA384'),
        (0x00,0xB8,'TLS_RSA_PSK_WITH_NULL_SHA256'),
        (0x00,0xB9,'TLS_RSA_PSK_WITH_NULL_SHA384'),
        (0x00,0xBA,'TLS_RSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xBB,'TLS_DH_DSS_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xBC,'TLS_DH_RSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xBD,'TLS_DHE_DSS_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xBE,'TLS_DHE_RSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xBF,'TLS_DH_anon_WITH_CAMELLIA_128_CBC_SHA256'),
        (0x00,0xC0,'TLS_RSA_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xC1,'TLS_DH_DSS_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xC2,'TLS_DH_RSA_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xC3,'TLS_DHE_DSS_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xC4,'TLS_DHE_RSA_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xC5,'TLS_DH_anon_WITH_CAMELLIA_256_CBC_SHA256'),
        (0x00,0xFF,'TLS_EMPTY_RENEGOTIATION_INFO_SCSV'),
        (0x13,0x01,'TLS_AES_128_GCM_SHA256'),
        (0x13,0x02,'TLS_AES_256_GCM_SHA384'),
        (0x13,0x03,'TLS_CHACHA20_POLY1305_SHA256'),
        (0x13,0x04,'TLS_AES_128_CCM_SHA256'),
        (0x13,0x05,'TLS_AES_128_CCM_8_SHA256'),
        (0x56,0x00,'TLS_FALLBACK_SCSV'),
        (0xC0,0x01,'TLS_ECDH_ECDSA_WITH_NULL_SHA'),
        (0xC0,0x02,'TLS_ECDH_ECDSA_WITH_RC4_128_SHA'),
        (0xC0,0x03,'TLS_ECDH_ECDSA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x04,'TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x05,'TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x06,'TLS_ECDHE_ECDSA_WITH_NULL_SHA'),
        (0xC0,0x07,'TLS_ECDHE_ECDSA_WITH_RC4_128_SHA'),
        (0xC0,0x08,'TLS_ECDHE_ECDSA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x09,'TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x0A,'TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x0B,'TLS_ECDH_RSA_WITH_NULL_SHA'),
        (0xC0,0x0C,'TLS_ECDH_RSA_WITH_RC4_128_SHA'),
        (0xC0,0x0D,'TLS_ECDH_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x0E,'TLS_ECDH_RSA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x0F,'TLS_ECDH_RSA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x10,'TLS_ECDHE_RSA_WITH_NULL_SHA'),
        (0xC0,0x11,'TLS_ECDHE_RSA_WITH_RC4_128_SHA'),
        (0xC0,0x12,'TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x13,'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x14,'TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x15,'TLS_ECDH_anon_WITH_NULL_SHA'),
        (0xC0,0x16,'TLS_ECDH_anon_WITH_RC4_128_SHA'),
        (0xC0,0x17,'TLS_ECDH_anon_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x18,'TLS_ECDH_anon_WITH_AES_128_CBC_SHA'),
        (0xC0,0x19,'TLS_ECDH_anon_WITH_AES_256_CBC_SHA'),
        (0xC0,0x1A,'TLS_SRP_SHA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x1B,'TLS_SRP_SHA_RSA_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x1C,'TLS_SRP_SHA_DSS_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x1D,'TLS_SRP_SHA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x1E,'TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA'),
        (0xC0,0x1F,'TLS_SRP_SHA_DSS_WITH_AES_128_CBC_SHA'),
        (0xC0,0x20,'TLS_SRP_SHA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x21,'TLS_SRP_SHA_RSA_WITH_AES_256_CBC_SHA'),
        (0xC0,0x22,'TLS_SRP_SHA_DSS_WITH_AES_256_CBC_SHA'),
        (0xC0,0x23,'TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256'),
        (0xC0,0x24,'TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384'),
        (0xC0,0x25,'TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA256'),
        (0xC0,0x26,'TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA384'),
        (0xC0,0x27,'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256'),
        (0xC0,0x28,'TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384'),
        (0xC0,0x29,'TLS_ECDH_RSA_WITH_AES_128_CBC_SHA256'),
        (0xC0,0x2A,'TLS_ECDH_RSA_WITH_AES_256_CBC_SHA384'),
        (0xC0,0x2B,'TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256'),
        (0xC0,0x2C,'TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384'),
        (0xC0,0x2D,'TLS_ECDH_ECDSA_WITH_AES_128_GCM_SHA256'),
        (0xC0,0x2E,'TLS_ECDH_ECDSA_WITH_AES_256_GCM_SHA384'),
        (0xC0,0x2F,'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256'),
        (0xC0,0x30,'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384'),
        (0xC0,0x31,'TLS_ECDH_RSA_WITH_AES_128_GCM_SHA256'),
        (0xC0,0x32,'TLS_ECDH_RSA_WITH_AES_256_GCM_SHA384'),
        (0xC0,0x33,'TLS_ECDHE_PSK_WITH_RC4_128_SHA'),
        (0xC0,0x34,'TLS_ECDHE_PSK_WITH_3DES_EDE_CBC_SHA'),
        (0xC0,0x35,'TLS_ECDHE_PSK_WITH_AES_128_CBC_SHA'),
        (0xC0,0x36,'TLS_ECDHE_PSK_WITH_AES_256_CBC_SHA'),
        (0xC0,0x37,'TLS_ECDHE_PSK_WITH_AES_128_CBC_SHA256'),
        (0xC0,0x38,'TLS_ECDHE_PSK_WITH_AES_256_CBC_SHA384'),
        (0xC0,0x39,'TLS_ECDHE_PSK_WITH_NULL_SHA'),
        (0xC0,0x3A,'TLS_ECDHE_PSK_WITH_NULL_SHA256'),
        (0xC0,0x3B,'TLS_ECDHE_PSK_WITH_NULL_SHA384'),
        (0xC0,0x3C,'TLS_RSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x3D,'TLS_RSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x3E,'TLS_DH_DSS_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x3F,'TLS_DH_DSS_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x40,'TLS_DH_RSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x41,'TLS_DH_RSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x42,'TLS_DHE_DSS_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x43,'TLS_DHE_DSS_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x44,'TLS_DHE_RSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x45,'TLS_DHE_RSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x46,'TLS_DH_anon_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x47,'TLS_DH_anon_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x48,'TLS_ECDHE_ECDSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x49,'TLS_ECDHE_ECDSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x4A,'TLS_ECDH_ECDSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x4B,'TLS_ECDH_ECDSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x4C,'TLS_ECDHE_RSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x4D,'TLS_ECDHE_RSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x4E,'TLS_ECDH_RSA_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x4F,'TLS_ECDH_RSA_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x50,'TLS_RSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x51,'TLS_RSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x52,'TLS_DHE_RSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x53,'TLS_DHE_RSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x54,'TLS_DH_RSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x55,'TLS_DH_RSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x56,'TLS_DHE_DSS_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x57,'TLS_DHE_DSS_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x58,'TLS_DH_DSS_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x59,'TLS_DH_DSS_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x5A,'TLS_DH_anon_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x5B,'TLS_DH_anon_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x5C,'TLS_ECDHE_ECDSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x5D,'TLS_ECDHE_ECDSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x5E,'TLS_ECDH_ECDSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x5F,'TLS_ECDH_ECDSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x60,'TLS_ECDHE_RSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x61,'TLS_ECDHE_RSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x62,'TLS_ECDH_RSA_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x63,'TLS_ECDH_RSA_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x64,'TLS_PSK_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x65,'TLS_PSK_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x66,'TLS_DHE_PSK_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x67,'TLS_DHE_PSK_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x68,'TLS_RSA_PSK_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x69,'TLS_RSA_PSK_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x6A,'TLS_PSK_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x6B,'TLS_PSK_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x6C,'TLS_DHE_PSK_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x6D,'TLS_DHE_PSK_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x6E,'TLS_RSA_PSK_WITH_ARIA_128_GCM_SHA256'),
        (0xC0,0x6F,'TLS_RSA_PSK_WITH_ARIA_256_GCM_SHA384'),
        (0xC0,0x70,'TLS_ECDHE_PSK_WITH_ARIA_128_CBC_SHA256'),
        (0xC0,0x71,'TLS_ECDHE_PSK_WITH_ARIA_256_CBC_SHA384'),
        (0xC0,0x72,'TLS_ECDHE_ECDSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x73,'TLS_ECDHE_ECDSA_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x74,'TLS_ECDH_ECDSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x75,'TLS_ECDH_ECDSA_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x76,'TLS_ECDHE_RSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x77,'TLS_ECDHE_RSA_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x78,'TLS_ECDH_RSA_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x79,'TLS_ECDH_RSA_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x7A,'TLS_RSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x7B,'TLS_RSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x7C,'TLS_DHE_RSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x7D,'TLS_DHE_RSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x7E,'TLS_DH_RSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x7F,'TLS_DH_RSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x80,'TLS_DHE_DSS_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x81,'TLS_DHE_DSS_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x82,'TLS_DH_DSS_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x83,'TLS_DH_DSS_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x84,'TLS_DH_anon_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x85,'TLS_DH_anon_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x86,'TLS_ECDHE_ECDSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x87,'TLS_ECDHE_ECDSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x88,'TLS_ECDH_ECDSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x89,'TLS_ECDH_ECDSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x8A,'TLS_ECDHE_RSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x8B,'TLS_ECDHE_RSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x8C,'TLS_ECDH_RSA_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x8D,'TLS_ECDH_RSA_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x8E,'TLS_PSK_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x8F,'TLS_PSK_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x90,'TLS_DHE_PSK_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x91,'TLS_DHE_PSK_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x92,'TLS_RSA_PSK_WITH_CAMELLIA_128_GCM_SHA256'),
        (0xC0,0x93,'TLS_RSA_PSK_WITH_CAMELLIA_256_GCM_SHA384'),
        (0xC0,0x94,'TLS_PSK_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x95,'TLS_PSK_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x96,'TLS_DHE_PSK_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x97,'TLS_DHE_PSK_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x98,'TLS_RSA_PSK_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x99,'TLS_RSA_PSK_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x9A,'TLS_ECDHE_PSK_WITH_CAMELLIA_128_CBC_SHA256'),
        (0xC0,0x9B,'TLS_ECDHE_PSK_WITH_CAMELLIA_256_CBC_SHA384'),
        (0xC0,0x9C,'TLS_RSA_WITH_AES_128_CCM'),
        (0xC0,0x9D,'TLS_RSA_WITH_AES_256_CCM'),
        (0xC0,0x9E,'TLS_DHE_RSA_WITH_AES_128_CCM'),
        (0xC0,0x9F,'TLS_DHE_RSA_WITH_AES_256_CCM'),
        (0xC0,0xA0,'TLS_RSA_WITH_AES_128_CCM_8'),
        (0xC0,0xA1,'TLS_RSA_WITH_AES_256_CCM_8'),
        (0xC0,0xA2,'TLS_DHE_RSA_WITH_AES_128_CCM_8'),
        (0xC0,0xA3,'TLS_DHE_RSA_WITH_AES_256_CCM_8'),
        (0xC0,0xA4,'TLS_PSK_WITH_AES_128_CCM'),
        (0xC0,0xA5,'TLS_PSK_WITH_AES_256_CCM'),
        (0xC0,0xA6,'TLS_DHE_PSK_WITH_AES_128_CCM'),
        (0xC0,0xA7,'TLS_DHE_PSK_WITH_AES_256_CCM'),
        (0xC0,0xA8,'TLS_PSK_WITH_AES_128_CCM_8'),
        (0xC0,0xA9,'TLS_PSK_WITH_AES_256_CCM_8'),
        (0xC0,0xAA,'TLS_PSK_DHE_WITH_AES_128_CCM_8'),
        (0xC0,0xAB,'TLS_PSK_DHE_WITH_AES_256_CCM_8'),
        (0xC0,0xAC,'TLS_ECDHE_ECDSA_WITH_AES_128_CCM'),
        (0xC0,0xAD,'TLS_ECDHE_ECDSA_WITH_AES_256_CCM'),
        (0xC0,0xAE,'TLS_ECDHE_ECDSA_WITH_AES_128_CCM_8'),
        (0xC0,0xAF,'TLS_ECDHE_ECDSA_WITH_AES_256_CCM_8'),
        (0xC0,0xB0,'TLS_ECCPWD_WITH_AES_128_GCM_SHA256'),
        (0xC0,0xB1,'TLS_ECCPWD_WITH_AES_256_GCM_SHA384'),
        (0xC0,0xB2,'TLS_ECCPWD_WITH_AES_128_CCM_SHA256'),
        (0xC0,0xB3,'TLS_ECCPWD_WITH_AES_256_CCM_SHA384'),
        (0xC0,0xB4,'TLS_SHA256_SHA256'),
        (0xC0,0xB5,'TLS_SHA384_SHA384'),
        (0xC1,0x00,'TLS_GOSTR341112_256_WITH_KUZNYECHIK_CTR_OMAC'),
        (0xC1,0x01,'TLS_GOSTR341112_256_WITH_MAGMA_CTR_OMAC'),
        (0xC1,0x02,'TLS_GOSTR341112_256_WITH_28147_CNT_IMIT'),
        (0xCC,0xA8,'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xA9,'TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xAA,'TLS_DHE_RSA_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xAB,'TLS_PSK_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xAC,'TLS_ECDHE_PSK_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xAD,'TLS_DHE_PSK_WITH_CHACHA20_POLY1305_SHA256'),
        (0xCC,0xAE,'TLS_RSA_PSK_WITH_CHACHA20_POLY1305_SHA256'),
        (0xD0,0x01,'TLS_ECDHE_PSK_WITH_AES_128_GCM_SHA256'),
        (0xD0,0x02,'TLS_ECDHE_PSK_WITH_AES_256_GCM_SHA384'),
        (0xD0,0x03,'TLS_ECDHE_PSK_WITH_AES_128_CCM_8_SHA256'),
        (0xD0,0x05,'TLS_ECDHE_PSK_WITH_AES_128_CCM_SHA256'),
    ]
    _values_ = [(_n, _u * 0x100 + _v) for _u, _v, _n in _values_]

class CipherSuites(pstruct.type):
    _fields_ = [
        (uint16, 'size'),
        (lambda self: dyn.blockarray(CipherSuite, self['size'].li.int()), 'items'),
    ]

    def summary(self):
        iterable = (item.summary() for item in self['items'])
        return "size={:d} items=[{:s}]".format(len(self['items']), ', '.join(iterable))
    repr = summary

class CompressionMethod(pint.enum, uint8):
    _values_ = [
        ('null', 0),
        ('deflate', 1),
        ('lzs', 64),
    ]

class CompressionMethods(pstruct.type):
    _fields_ = [
        (uint8, 'size'),
        (lambda self: dyn.array(CompressionMethod, self['size'].li.int()), 'items'),
    ]

    def summary(self):
        size, iterable = self['size'], (item.summary() for item in self['items'])
        return "size={:d} items=[{:s}]".format(size.int(), ', '.join(iterable))
    repr = summary

class Extensions(tlsext.List16):
    _object_ = tlsext.Extension

@HandshakeRecord.define
class ClientHello(pstruct.type):
    type = 1

    def __extensions(self):
        try:
            p = self.getparent(Handshake)
            cb = p['length'].li.int()
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        res = sum(self[fld].li.size() for fld in ['client_version','random','session_id','cipher_suites','compression_methods'])
        if cb >= res + 2:
            return Extensions
        return ptype.undefined

    def __missing(self):
        try:
            p = self.getparent(Handshake)
            cb = p['length'].li.int()
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        res = sum(self[fld].li.size() for fld in ['client_version','random','session_id','cipher_suites','compression_methods','extensions'])
        return dyn.block(cb - res)

    _fields_ = [
        (ProtocolVersion, 'client_version'),
        (Random, 'random'),
        (SessionID, 'session_id'),
        (CipherSuites, 'cipher_suites'),
        (CompressionMethods, 'compression_methods'),
        (__extensions, 'extensions'),
        (__missing, 'missing'),
    ]

@HandshakeRecord.define
class ServerHello(pstruct.type):
    type = 2
    def __extensions(self):
        try:
            p = self.getparent(Handshake)
            cb = p['length'].li.int()
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        res = sum(self[fld].li.size() for fld in ['server_version','random','session_id','cipher_suite','compression_method'])
        if cb >= res + 2:
            return Extensions
        return ptype.undefined

    def __missing(self):
        try:
            p = self.getparent(Handshake)
            cb = p['length'].li.int()
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        res = sum(self[fld].li.size() for fld in ['server_version','random','session_id','cipher_suite','compression_method','extensions'])
        return dyn.block(cb - res)

    _fields_ = [
        (ProtocolVersion, 'server_version'),
        (Random, 'random'),
        (SessionID, 'session_id'),
        (CipherSuite, 'cipher_suite'),
        (CompressionMethod, 'compression_method'),
        (__extensions, 'extensions'),
        (__missing, 'missing'),
    ]

@HandshakeRecord.define
class Certificate(pstruct.type):
    type = 11
    _fields_ = [
        (uint24, 'size'),
        (dyn.clone(tlsext.List24, _object_=ber.Packet), 'certificate_list'),
    ]
    def enumerate(self):
        for item in self['certificate_list'].enumerate():
            yield item
        return
    def iterate(self):
        for item in self['certificate_list'].iterate():
            yield item
        return

class HandshakeFinishedRecord(Record):
    def __fragment(self):
        res, cb = (self[fld].li for fld in ['type', 'length'])
        if not res['handshake']:
            raise KeyError(res.int())
        return dyn.block(cb.int())

    def __unparsed(self):
        res = self['length'].li
        return dyn.block(res.int() - self['fragment'].li.size())

    _fields_ = [
        (ContentType, 'type'),
        (ProtocolVersion, 'version'),
        (uint16, 'length'),
        (__fragment, 'fragment'),
        (__unparsed, 'unparsed'),
    ]

class InitiateClientHello(parray.type):
    _object_, length = Record, 1

class InitiateServerHello(parray.terminated):
    _object_ = Record
    def isTerminator(self, record):
        return record['fragment'][-1]['type']['server_hello_done']

class InitiateKeyExchange(parray.terminated):
    _object_ = Record
    def isTerminator(self, record):
        return record['type']['change_cipher_spec']

class InitiateHandshake(pstruct.type):
    _fields_ = [
        (InitiateClientHello, 'clientHello'),
        (InitiateServerHello, 'serverHello'),
        (InitiateKeyExchange, 'keyExchange'),
        (HandshakeFinishedRecord, 'handshakeFinished'),
    ]

if __name__ == '__main__':
    import sys, ptypes, protocol.tls as tls
    from ptypes import *

    import importlib
    importlib.reload(tls)
    importlib.reload(tls.tlsext)

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    data = '160301006d0100006903014b721ba2ee8ec1823474aaa67b1f870ac0c868b5a6c2cbff76efe329b5bebda9000018002f00350005000ac013c014c009c00a00320038001300040100002800000014001200000f63686d757468752d77372d74737433000a0006000400170018000b00020100'
    z = tls.InitiateClientHello(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l
    assert(z.size() == len(fromhex(data)))
    assert(z.serialize() == z.source.value)

    for ri, record in enumerate(z):
        print('record %d'%ri, record['type'].summary())
        for fi, fragment in enumerate(record['fragment']):
            print('fragment %d'%fi, fragment['type'].summary())
            body = fragment['body']
            print(body)
            if 'extensions' in body and isinstance(body['extensions'], parray.type):
                for ext in body['extensions'].iterate():
                    print(ext['type'].summary())
                    for item in ext['data'].iterate():
                        print(item)
                    continue
                continue
            continue
        continue

    data = '16030102fd0200004603014b721b9acec83afd96c1372abb00fa1a0905df09eaa84b224f77eaf11fab2e8d207d1300004c603107c832921f7085323a8d311492245b60f246b7311219ece553002f000b0002ab0002a80002a5308202a13082020ea003020102021019af5d26ef02acb448ea8886a359af0a300906052b0e03021d0500301e311c301a0603550403131363686d757468752d77372d747374332d636133301e170d3130303231303032323830335a170d3339313233313233353935395a301a311830160603550403130f63686d757468752d77372d7473743330820122300d06092a864886f70d01010105000382010f003082010a0282010100a5583ba38c6a21642334d91657c7cc8f7deea7b2b453cb4bf95a5e537e069036a95ad11700e17cb46340af803b7bbff966fb2af57fddff47f94db6105b63ffaf6bb026fa2a317d4fa652cfaf06f787658f2f1316b38b02eb39c6caf4ca68502f89e23ba8c2fc5e56671fc0d8eb9bc65ae2148df5730ff66cd9f940d22bea4b0b5a17264baf264f34e48c875bf4110a8c1f80647798cc5c54c03bb2b3c534384ad335f48f94a45f39d69508ad7c88f69bbc7d161b3f8e9351b6ba90ac065c2a7f9cbf6da82ef22808cb1c0bca30e15df47d958ac2d726a4c6489c0363459c84940310ce4af43acff707025ca0d502f6ff63b3b94cf78307930b6f38d9d68c7de90203010001a368306630130603551d25040c300a06082b06010505070301304f0603551d010448304680103c8db6418a8b1b208f76cc07c6724d5ca120301e311c301a0603550403131363686d757468752d77372d747374332d6361338210db048065d808f69f48fa85880a505184300906052b0e03021d0500038181002ba86f466e4a180dec1445a021bcd261ea1b31a7cbd8363b9464dc4dac8d9fb40aaab1f78509f048b360c07188c8ae59f8f5be8b7f31da4a4a31b2c16c0cf9e57827b5f1c5b46a4b52c89d6cdde1475e7f00d87cd426b581f989272aefd876edfed253a6e61c8d5a5d1572ecb91a8f4e4f4eba82e66ee3e825410c21e64257510e000000'
    z = tls.InitiateClientHello(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l
    assert(z.size() == len(fromhex(data)))
    assert(z.serialize() == z.source.value)

    for ri, record in enumerate(z):
        print('record %d'%ri, record['type'].summary())
        for fi, fragment in enumerate(record['fragment']):
            print('fragment %d'%fi, fragment['type'].summary())
            body = fragment['body']
            print(body)
            if 'extensions' in body and isinstance(body['extensions'], parray.type):
                for ext in body['extensions'].iterate():
                    print(ext['type'].summary())
                    for item in ext['data'].iterate():
                        print(item)
                    continue
                continue
            continue
        continue

    cert = z.at(0x56).getparent(tls.Certificate)['certificate_list']['items'][0]
    print(cert['value'][0])

    data = '160301010610000102010089428c550a5b5de8ff8bff84ec435e9744ddd25f762a35359f9d41aba1c4902d68333a36397407bf5a232ce34c3cbc7bfb7e2839aabba2f865d1d62650e420e80bc77e638326b10f15345843cec664f5c1deb85b0c702ce51287e73089752146c53fac66e72402ed5759e85f6301cc5b5c24c6f65e90e13a2ca7c57c043d9721a383ee469fe8c809a685687746f78007f1803197e4594c8ff51d73861955682cec4f0c2fcb7a6075ea5d04fb48fd9ab6bc0a03cf4d2955fd221acfcfd9ad50b01cd304511a8d1602d8fef9ff832f2a4558ca3578f97efb435ce4640d6a9982d61f5a707374d7c300af35eb96ed2d723062d0c924712569b24865af238086e4a614030100010116030100307df95238bcc63a1f08e849398b842b126eebb4a82ce26e88f6b07a360cd2c817fdf226bcd26a875469c550a9f5190017'
    data = '1403010001011603010030e5ad7c063a939b6e2ca9e6ded92e7e20d46002f90b3c4f69d62f784b9224a05c49043da5cfc1b44132971d70cb84e42c'
    data = '1703010070166fb243daf7c6a5b8849354ba80f44caf3734432b10de69957be6da70e7849ac70a0e8e93534c3b55c342c4b93279cd19fefc4caf574ca2f22ba9a8ee22603d2e5214c927b236d537e0a890ebf63b23393ed0530295789b2557a9f8d7fef9794172077a1555bbfe5e9d81949f4de2d5'
    data = '170301007086fa01b86a96a1e29f9bbb61d360ab8627cc9d1612e4edab785721ce3acb965f10d3b2a733e0550446ccbe9fa03911aafd8ee2a19852faf07e07aa3abbee2b128f8d1c389bd506c90ed05848254590bc7976da030903c69008e5e76979c51a0fb7dacdc3b58d145971a80bb3b323b9a0'
    data = '17030100f0aa5d67741968f6d98a748a66b47a969eb68809f59370eab071504ce8f20328fd22b24d3f87017c79ab482ebde0a7511ce0e184197bb746159ce542131182bed28b9e389223c7bc14f93fdbcccb3e910269504e8699be6183d8487c7664c2c31bdfe6ae5ef747002c3933fc95122f175ff912bf77a475eace0cff205bf66af07801a84e5603ef7803fcf4afe7798decc01249631094f3973ab747879eab499cca7df8125ccc89d93eae9abe96e6a3d00dddfbae46c20b4958c79a22079e9a5f7d92abea0b3941c86ce35b58d2595e7d82bb08ab9033780a8474e2d693cec0f65a4f1753ddf9fc3317aedefea8b34ec8a0'
    data = '17030100705edf883c10580ac4a0cf54bc51307bdb950a1c6aef8a615ad0ea1025e77700340a893ccfe9b4740f35b878a18ba9011905e48d3484a70319e587d25db6c0db2acb025d3914810b5fdcc63c005e2d9b62a92f125237e0d5043f9cd5b3b0ca75326c31ba98862c8da2ce7e8f721022c960'
    data = '1703010050b18490439c197e548898a980db24897c95124897aef48c43e567b455d969bb73dddcd673d777b5cc5013705de841c8c4bd86666f120a7e5f25798e04f474c7f6af9197d980cb22cb04a7f2742de90326'
    data = '1703010050a7717e35ede1937aacec667f5ea03ec16b2f8d385f653390413b2eeebb273985fb905b05db7c0d5dabaa8453637a44a92ba390738c60fc14b5e2ea3ba86aabc2a13221fb670be6ec559a1360ded40f3f'
    data = '17030100b0d4d5e480be03d6e88f471df529ce279641937a793716e7db9c46a5d3d9444854c21d6caae4f2e48d14a34c82076295ca79f07e1be4e19b89e279ff45bebf786f8b9ace35bdccd011f6d7537a4c1c72a57c0c36e52c23ff7c595c067ac8c3b825f6e9b758af2252418e3c055fb5f3850f15e85f3c3deaf5006538cbc3883abfdd78800824b2eece01c9fdd6683ee050bb32aff56ffaa27ce719d7e5f7cd813526475c8c8a5210d75ac81127a4024f80f5'
    data = '17030100b0b1569a5d6515d6c911e6df3bb98bdd7dde3bdf0eba85332690d3624d893107f25dc59a6576eda5c56bb561a7699e45162ba2db9713291dc7e863bf600c3960ba4fb9bd1cf85870cd2ceb0707870a3c67670ea49319aeceaf97650e704a05fe19c395a72dddcd128fb2eb7d804899cd9677a004ff605cbf890b8077a69e5845ec2a32ec6d7d90da91d8f566c6d4be6d95f0c84696ee8c9eccc82b54e91d58e8e5d77dee93a3757947dc24258adb5f5583'
    data = '17030100b046de3ff94bac170a9fc2c7f1b39d67fbd1e4801c8013b984816bc07a76c4847dee2f7145dcd8bbf02f79bd4092627c289a99f9ec5bc4a6246c0a89b3b496c6c85d39dd73cd565a3fd00bb4aa4f78a471b536d0343cab9adf874adf6f7ba8bb5a98a3aae475c9922227d34d52298dd8e5d30bd6856a2a481148aa61b7bf32dd382aa543c9dc6f10ad120520080e89de7b1c8c53a261ccba360e424023f4cf284913c75473ed31add381d070c961fa09d6'
    data = '17030100b096310e30353538bce9edc2c2691748e9d914999c4d83bb941b5cb4f1c1fb7162ce34b63e5a9b826980af146c2f2912e81102b91582dc164202dd62df711205b0c66cb5379d4cae9f737d93e7fe5c3338dd971c160b8a261742dfa026e7a05e7a2ed5f2377cde8b767d91b5ede25934e0a7a3c4752b1def2dde6cb6cd472694dd5c2c5732bdea0a69b418b1a2dcfe120b2ae042815ff9a3ceaa5cead3f7528924d51d0ce1b966f51f96fc8af5cd63648c'
    data = '17030100b0fec3a8ff15dd6aa976246f6e76f7011b53b39a1d5a55de517178e2e095f0167e55ed3ec089007299d6f94c00b3a3bdd5a1f6b2d49e80922667178521818ffc887f4476de5812e88031dff2746403775c30760a57e034ae9f8da8318e0ab301389e111eacf1c1f284c8a2f260fd303cb59383124a336f3ec1ffba2073eb4706b7167fa119e39828dd75eb3ad2d73de47a4acb1ce30b661c8fa8930ee04deb92bf7762033e446ecdd5147b1f9ddd63db04'
