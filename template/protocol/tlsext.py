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

    def enumerate(self):
        for index, item in enumerate(self['items']):
            yield index, item
        return

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

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
    def enumerate(self):
        for item in self['named_curve_list'].enumerate():
            yield item
        return
    def iterate(self):
        for item in self['named_curve_list'].iterate():
            yield item
        return

class ECPointFormat(pint.enum, uint8):
    _values_ = [
        ('uncompressed', 0),
        ('ansiX962_compressed_prime', 1),
        ('ansiX962_compressed_char2', 2),
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
class Padding(ptype.block):
    type = 21

@TLSExtension.define
class SupportedVersions(pstruct.type):
    type = 43
    class _versions(parray.block):
        _object_ = uint16
        def summary(self):
            iterable = map("{:#x}".format, self)
            return "[{:s}]".format(', '.join(iterable))
    _fields_ = [
        (uint8, 'size'),
        (lambda self: dyn.clone(self._versions, blocksize=lambda _, cb=self['size'].li.int(): cb), 'versions'),
    ]
    def summary(self):
        return "size={:d} versions={:s}".format(self['size'].int(), self['versions'].summary())

class PskKeyExchangeMode(pint.enum, uint8):
    _values_ = [
        ('psk_ke', 0),
        ('psk_dhe_ke', 1),
    ]

@TLSExtension.define
class PskKeyExchangeModes(pstruct.type):
    type = 45
    class _ke_modes(parray.type):
        _object_ = PskKeyExchangeMode
        def summary(self):
            iterable = (item.summary() for item in self)
            return "[{:s}]".format(', '.join(iterable))
    _fields_ = [
        (uint8, 'size'),
        (lambda self: dyn.clone(self._ke_modes, length=self['size'].li.int()), 'ke_modes'),
    ]
    def summary(self):
        return "size={:d} ke_modes={:s}".format(self['size'].int(), self['ke_modes'].summary())

class NamedGroup(pint.enum, uint16):
    _values_ = [
        ('unallocated_RESERVED', 0x0000),
        ('secp256r1', 0x0017),
        ('secp384r1', 0x0018),
        ('secp521r1', 0x0019),
        ('x25519', 0x001D),
        ('x448', 0x001E),
        ('ffdhe2048', 0x0100),
        ('ffdhe3072', 0x0101),
        ('ffdhe4096', 0x0102),
        ('ffdhe6144', 0x0103),
        ('ffdhe8192', 0x0104),
    ]

class opaque(pstruct.type):
    _fields_ = [
        (uint16, 'length'),
        (lambda self: dyn.block(self['length'].li.int()), 'data'),
    ]
    def __format__(self, spec):
        return format(self['data'], spec)
    def summary(self):
        return "({:d}) {:s}".format(self['length'], self['data'].serialize().hex())

class KeyShareEntry(pstruct.type):
    _fields_ = [
        (NamedGroup, 'group'),
        (opaque, 'key_exchange'),
    ]
    def summary(self):
        return "group={:s} key_exchange={:x}".format(self['group'], self['key_exchange'])

@TLSExtension.define
class KeyShare(pstruct.type):
    type = 51
    class _shares(parray.block):
        _object_ = KeyShareEntry
        def summary(self):
            iterable = ("{:#s}({:x})".format(item['group'], item['key_exchange']) for item in self)
            return "[{:s}]".format(', '.join(iterable))
    _fields_ = [
        (uint16, 'size'),
        (lambda self: dyn.clone(self._shares, blocksize=lambda _, cb=self['size'].li.int(): cb), 'shares'),
    ]
    def summary(self):
        return "size={:d} shares={:s}".format(self['size'].int(), self['shares'].summary())

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
            res = TLSExtension.lookup(res.int())
        except KeyError:
            return dyn.block(self['size'].li.int())
        return dyn.clone(res, length=self['size'].li.int()) if issubclass(res, ptype.block) else res

    def __padding(self):
        res, fields = self['size'].li, ['data']
        size = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        return dyn.block(size) if size else ptype.block

    _fields_ = [
        (ExtensionType, 'type'),
        (uint16, 'size'),
        (__data, 'data'),
        (__padding, 'padding'),
    ]

    def summary(self):
        return "type={:s} size={:d} data={:s}".format(self['type'].summary(), self['size'].int(), self['data'].summary())
