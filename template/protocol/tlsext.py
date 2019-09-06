import ptypes
from . import ber
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

class ExtensionType(pint.enum, uint16):
    _values_ = [
        ('server_name', 0),
        ('max_fragment_length', 1),
        ('client_certificate_url', 2),
        ('trusted_ca_keys', 3),
        ('truncated_hmac', 4),
        ('status_request', 5),
        ('user_mapping', 6),
        ('client_authz', 7),
        ('server_authz', 8),
        ('cert_type', 9),
        ('supported_groups', 10),
        ('ec_point_formats', 11),
        ('srp', 12),
        ('signature_algorithms', 13),
        ('use_srtp', 14),
        ('heartbeat', 15),
        ('application_layer_protocol_negotiation', 16),
        ('status_request_v2', 17),
        ('signed_certificate_timestamp', 18),
        ('client_certificate_type', 19),
        ('server_certificate_type', 20),
        ('padding', 21),
        ('encrypt_then_mac', 22),
        ('extended_master_secret', 23),
        ('token_binding', 24),
        ('cached_info', 25),
        ('tls_lts', 26),
        ('compress_certificate', 27),
        ('record_size_limit', 28),
        ('pwd_protect', 29),
        ('pwd_clear', 30),
        ('password_salt', 31),
        ('ticket_pinning', 32),
        ('session_ticket', 35),
        ('pre_shared_key', 41),
        ('early_data', 42),
        ('supported_versions', 43),
        ('cookie', 44),
        ('psk_key_exchange_modes', 45),
        ('Unassigned', 46),
        ('certificate_authorities', 47),
        ('oid_filters', 48),
        ('post_handshake_auth', 49),
        ('signature_algorithms_cert', 50),
        ('key_share', 51),
        ('transparency_info', 52),
        ('connection_id', 53),
        ('external_id_hash', 55),
        ('external_session_id', 56),
        ('renegotation_info', 65281),
    ]

class TLSExtension(ptype.definition):
    cache = {}

class NameType(pint.enum, uint8):
    _values_ = [
        ('host_name', 0),
    ]

class List(pstruct.type):
    def __items(self):
        res = self['size'].li
        if getattr(self, '_object_', None) is not None:
            return dyn.blockarray(self._object_, res.int())
        return dyn.block(res.int())

    _fields_ = [
        (__items, 'items')
    ]

    def classname(self):
        res = getattr(self, '_object_', None)
        if res is None:
            return super(List, self).classname()
        return "{:s}<{:s}>".format(self.typename(), self._object_.typename())

    def summary(self):
        if getattr(self, '_object_', None) is None:
            return super(List, self).summary()
        res = (item.summary() for item in self['items'])
        return "({:d}) items=[{:s}]".format(len(self['items']), ', '.join(res))
    repr = summary

class List8(List):
    _fields_ = [(uint8, 'size')] + List._fields_

class List16(List):
    _fields_ = [(uint16, 'size')] + List._fields_

class List24(List):
    _fields_ = [(uint24, 'size')] + List._fields_

class HostName(pstruct.type):
    _fields_ = [
        (uint16, 'size'),
        (lambda self: dyn.clone(pstr.string, length=self['size'].li.int()), 'name'),
    ]

    def str(self):
        return self['name'].str()

    def summary(self):
        return "({:d}) {:s}".format(self['size'].int(), self.str())

class ServerName(pstruct.type):
    _fields_ = [
        (NameType, 'name_type'),
        (HostName, 'server_name'),
    ]

    def summary(self):
        return "name_type={:s} name={:s}".format(self['name_type'].summary(), self['server_name'].summary())

@TLSExtension.define
class ServerNameList(List16):
    type = 0
    _object_ = ServerName

class CertificateStatusType(pint.enum, uint8):
    _values_ = [
        ('ocsp', 1),
    ]

class TLSCertificateStatusType(ptype.definition):
    cache = {}

class ResponderId(ber.Packet): pass

@TLSCertificateStatusType.define
class OCSPStatusRequest(pstruct.type):
    type = 1
    _fields_ = [
        (dyn.clone(List16, _object_=ResponderId), 'responder_id_list'),
        (List16, 'request_extensions'),
    ]

@TLSExtension.define
class CertificateStatusRequest(pstruct.type):
    type = 5

    def __request(self):
        res = self['status_type'].li
        return TLSCertificateStatusType.withdefault(res.int(), ptype.undefined)

    _fields_ = [
        (CertificateStatusType, 'status_type'),
        (__request, 'request'),
    ]

    def summary(self):
        return "status_type={:s} request={:s}".format(self['status_type'].summary(), self['request'].summary())

class NamedCurve(pint.enum, uint16):
    _values_ = [
        ('secp256r1', 23),
        ('secp384r1', 24),
        ('secp521r1', 25),
        ('x25519', 29),
        ('x448', 30),
    ]

@TLSExtension.define
class NamedCurveList(pstruct.type):
    type = 10
    _fields_ = [
        (dyn.clone(List16, _object_=NamedCurve), 'named_curve_list'),
    ]
    def summary(self):
        return "named_curve_list={:s}".format(self['named_curve_list'].summary())

class ECPointFormat(pint.enum, uint8):
    _values_ = [
        ('uncompressed', 0),
    ]

@TLSExtension.define
class ECPointFormatList(List8):
    type = 11
    _object_ = ECPointFormat

class HashAlgorithm(pint.enum, uint8):
    _values_ = [
        ('none', 0),
        ('md5', 1),
        ('sha1', 2),
        ('sha224', 3),
        ('sha256', 4),
        ('sha384', 5),
        ('sha512', 6),
    ]

class SignatureAlgorithm(pint.enum, uint8):
    _values_ = [
        ('anonymous', 0),
        ('rsa', 1),
        ('dsa', 2),
        ('ecdsa', 3),
    ]

class SignatureAndHashAlgorithm(pstruct.type):
    _fields_ = [
        (HashAlgorithm, 'hash'),
        (SignatureAlgorithm, 'signature'),
    ]
    def summary(self):
        return "hash={:s} signature={:s}".format(self['hash'].summary(), self['signature'].summary())

@TLSExtension.define
class SignatureAndHashAlgorithmList(List16):
    type = 13
    _object_ = SignatureAndHashAlgorithm

@TLSExtension.define
class RenegotiationInfo(pstruct.type):
    type = 65281
    _fields_ = [
        (uint8, 'size'),
        (lambda self: dyn.block(self['size'].li.int()), 'renegotiated_connection'),
    ]

class Extension(pstruct.type):
    def __data(self):
        res = self['type'].li
        try:
            return TLSExtension.lookup(res.int())
        except KeyError:
            pass
        return dyn.block(self['size'].li.int())

    _fields_ = [
        (ExtensionType, 'type'),
        (uint16, 'size'),
        (__data, 'data'),
    ]

    def summary(self):
        return "type={:s} size={:d} data={:s}".format(self['type'].summary(), self['size'].int(), self['data'].summary())
