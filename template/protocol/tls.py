import ptypes
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

class Random(pstruct.type):
    _fields_ = [
        (uint32, 'gmt_unix_time'),
        (dyn.block(28), 'random_bytes'),
    ]

class SessionID(pstruct.type):
    _fields_ = [
        (uint8, 'length'),
        (lambda self: dyn.clone(pint.uint_t, length=self['length'].li.int()), 'id'),
    ]

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
        res = (item.summary() for item in self['items'])
        return "({:d}) items=[{:s}]".format(len(self['items']), ', '.join(res))
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
        res = (item.summary() for item in self['items'])
        return "({:d}) items=[{:s}]".format(len(self['items']), ', '.join(res))
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
