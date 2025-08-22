"""
rfc2408 (IKEv1) -> rfc4306 (IKEv2)

the original definitions are based on output from some ai.. so there's a huge
chance that their naming schemes are wrong. despite this, the sizes line up so i
think we're good here.
"""
import ptypes
from ptypes import *

class U8(pint.uint_t): pass
class U8(pint.uint8_t): pass
class U16(pint.uint16_t): pass
class U24(pint.uint_t): length = 3
class U32(pint.uint32_t): pass
class U64(pint.uint64_t): pass

class ISAKMP_NEXT_PAYLOAD_TYPES(pint.enum, U8):
    _values_ = [
        ('NONE', 0),
        ('SA_v1', 1),
        ('PROPOSAL_v1', 2),
        ('TRANSFORM_v1', 3),
        ('KEY_EXCHANGE_v1', 4),
        ('IDENTIFICATION_v1', 5),
        ('CERTIFICATE_v1', 6),
        ('CERT_REQUEST_v1', 7),
        ('HASH_v1', 8),
        ('SIGNATURE_v1', 9),
        ('NONCE_v1', 10),
        ('NOTIFICATION_v1', 11),
        ('DELETE_v1', 12),
        ('VENDOR_ID_v1', 13),

        ('SA_v2', 33),          # Security Association
        ('KE_v2', 34),          # Key Exchange
        ('IDi_v2', 35),         # Identification - Initiator
        ('IDr_v2', 36),         # Identification - Responder
        ('CERT_v2', 37),        # Certificate
        ('CERTREQ_v2', 38),     # Certificate Request
        ('AUTH_v2', 39),        # Authentication
        ('Ni_v2', 40),          # Nonce
        ('Nr_v2', 40),          # Nonce
        ('N_v2', 41),           # Notify
        ('D_v2', 42),           # Delete
        ('V_v2', 43),           # Vendor ID
        ('TSi_v2', 44),         # Traffic Selector - Initiator
        ('TSr_v2', 45),         # Traffic Selector - Responder
        ('E_v2', 46),           # Encrypted
        ('CP_v2', 47),          # Configuration
        ('EAP_v2', 48),         # Extensible Authentication
    ]

# ISAKMP Exchange Types (Partial List) [5]
class ISAKMP_EXCHANGE_TYPES(pint.enum, U8):
    _values_ = [
        ('NONE', 0),
        ('BASE', 1),
        ('ID_PROTECTION', 2),
        ('AUTH_ONLY', 3),
        ('AGGRESSIVE', 4),
        ('INFORMATIONAL_v1', 5),
        ('IKE_SA_INIT', 34),
        ('IKE_AUTH', 35),
        ('CREATE_CHILD_SA', 36),
        ('INFORMATIONAL_v2', 37),
    ]

# ISAKMP Flags (Bitfield) [4, 5]
# This would be a BitfieldDef in pycstruct
class ISAKMP_FLAGS(pbinary.flags):
    _fields_ = [
        (5, 'Reserved'),
        (1, 'AUTHENTICATION_ONLY'), # Bit 2: Authentication Only [4]
        (1, 'COMMIT'),      # Bit 1: Commit [4]
        (1, 'ENCRYPTION'),  # Bit 0: Encryption [4]
    ]

class PROTO_(pint.enum):
    _values_ = [
        ('RESERVED', 0),
        ('PROTO_ISAKMP', 1),            # [RFC2407]
        ('PROTO_IPSEC_AH', 2),          # [RFC2407]
        ('PROTO_IPSEC_ESP', 3),         # [RFC2407]
        ('PROTO_IPCOMP', 4),            # [RFC2407]
        ('PROTO_GIGABEAM_RADIO', 5),    # [RFC4705]
    ]

class ISAKMP_PROTOCOL_IDENTIFIER(PROTO_, U8):
    pass

class ISAKMP_ATTRIBUTE_TYPE(pint.enum, U16):
    _values_ = []

class ISAKMP_ATTRIBUTE(pstruct.type):
    def __type(self):
        return getattr(self, '_type_', ISAKMP_ATTRIBUTE_TYPE)

    def __length(self):
        res = self['type'].li
        if res.int() & 0x8000:
            return U0
        return U16

    def __value(self):
        res, size = (self[fld].li for fld in ['type', 'length'])
        if res.int() & 0x8000:
            return U16
        elif size.int():
            return dyn.block(size.int())
        return ptype.block

    def __padding(self):
        res, value = (self[fld].li for fld in ['length', 'value'])
        size = max(0, res.int() - value.size())
        if size:
            return dyn.block(size)
        return ptype.block

    _fields_ = [
        (__type, 'type'),
        (__length, 'length'),
        (__value, 'value'),
        (__padding, 'padding'),
    ]

class ISAKMP_ATTRIBUTE_ARRAY(parray.type):
    _object_ = ISAKMP_ATTRIBUTE

class ISAKMP_ATTRIBUTES(parray.block):
    _object_ = ISAKMP_ATTRIBUTE

class ISAKMP_PAYLOAD(ptype.definition):
    cache, _enum_ = {}, ISAKMP_NEXT_PAYLOAD_TYPES

class ISAKMP_PAYLOAD_ARRAY(parray.terminated):
    def _object_(self):
        next_payload = self.value[-1]['next_payload'].int() if self.value else getattr(self, '_type_', 0)
        payload_t = ISAKMP_PAYLOAD.withdefault(next_payload)
        return dyn.clone(GENERIC_PAYLOAD, _object_=payload_t)

    def isTerminator(self, value):
        return self.value and self.value[-1]['next_payload'].int() == 0

class ISAKMP_VERSION(pbinary.struct):
    _fields_ = [
        (4, 'major'),
        (4, 'minor'),
    ]

# 1. ISAKMP Header Format [1, 2, 3, 4, 5, 6, 7]
# An ISAKMP message begins with a fixed header, followed by a variable number of payloads. [1]
class ISAKMP_HEADER(pstruct.type):
    _fields_ = [
        (U64, 'initiator_cookie'),  # 8 octets [1, 2, 3, 5]
        (U64, 'responder_cookie'),  # 8 octets [1, 2, 3, 5]
        (ISAKMP_PAYLOAD.enum, 'next_payload'), # 1 octet, type of first payload [3, 4, 5, 6, 7]
        (ISAKMP_VERSION, 'version'), # 4 bits [3, 4, 5]
        (ISAKMP_EXCHANGE_TYPES, 'exchange_type'), # 1 octet [2, 4, 5, 6]
        (ISAKMP_FLAGS, 'flags'), # 1 octet [4, 5]
        (U32, 'message_id'),  # 4 octets [5, 6, 7]
        (U32, 'length'),      # 4 octets, total length of message (header + payloads) [2, 3, 4, 5, 6, 7]
    ]

class GENERIC_PAYLOAD(pstruct.type):
    class _reserved(pbinary.flags):
        _fields_ = [(1, 'C'), (7, 'RESERVED')]
    def __payload(self):
        res, fields = self['payload_length'].li, ['next_payload', 'reserved', 'payload_length']
        size = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        if hasattr(self, '_object_'):
            return self._object_
        elif size:
            return dyn.block(size)
        return ptype.block

    def __padding(self):
        res, fields = self['payload_length'].li, ['next_payload', 'reserved', 'payload_length', 'payload']
        size = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block

    _fields_ = [
        (ISAKMP_PAYLOAD.enum, 'next_payload'), # 1 octet, type of next payload [4, 5, 7]
        (_reserved, 'reserved'),      # 1 octet, must be set to zero [4, 5]
        (U16, 'payload_length'), # 2 octets, length of current payload including this header [4, 5, 7]
        (__payload, 'payload'),
        (__padding, 'padding'),
    ]

    def alloc(self, **fields):
        res = super(GENERIC_PAYLOAD, self).alloc(**fields)
        length = sum(res[fld].size() for fld in ['payload', 'padding'])
        if 'payload_length' not in fields:
            res['payload_length'].set(length)
        return res

## 2. Generic ISAKMP Payload Header [1, 4, 5]
## All ISAKMP payloads start with this generic header. [4]
#class GENERIC_PAYLOAD_HEADER(pstruct.type):
#    _fields_ = [
#        ( ISAKMP_PAYLOAD.enum, 'next_payload'), # 1 octet, type of next payload [4, 5, 7]
#        ( U8, 'reserved'),      # 1 octet, must be set to zero [4, 5]
#        ( U16, 'payload_length'), # 2 octets, length of current payload including this header [4, 5, 7]
#    ]

# 3. Security Association (SA) Payload [1, 5]
# This payload defines a security association. [4]
@ISAKMP_PAYLOAD.define
class SA_PAYLOAD_v1(pstruct.type):
    type = 1
    _fields_ = [
        (U32, 'doi'),       # 4 octets, Domain of Interpretation [5]
        (U32, 'situation'), # 4 octets [1, 5]
    ]

# 4. Proposal Payload (often nested within SA Payload) [5]
@ISAKMP_PAYLOAD.define
class PROPOSAL_PAYLOAD_v1(pstruct.type):
    type = 2
    def __spi(self):
        size = self['spi_size'].li.int()
        if size:
            return dyn.block(size)
        return ptype.block

    _fields_ = [
        (U8, 'proposal_no'),                            # 1 octet [5]
        (ISAKMP_PROTOCOL_IDENTIFIER, 'protocol_id'),    # 1 octet [5]
        (U8, 'spi_size'),                               # 1 octet [5]
        (U8, 'num_transforms'),                         # 1 octet [5]
        (__spi, 'spi'),
    ]

@ISAKMP_PAYLOAD.define
class TRANSFORM_PAYLOAD_v1(pstruct.type):
    type = 3
    def __sa_attributes(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.clone(ISAKMP_ATTRIBUTES, blocksize=lambda _, cb=res: cb)
        return ISAKMP_ATTRIBUTE_ARRAY
    _fields_ = [
        (U8, 'transform_number'),
        (U8, 'transform_id'),
        (U16, 'RESERVED2'),
        (__sa_attributes, 'sa_attributes')
    ]

# 5. Key Exchange (KE) Payload [1, 4, 9]
@ISAKMP_PAYLOAD.define
class KE_PAYLOAD_v1(pstruct.type):
    type = 4
    def __key_exchange_data(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.block(res)
        return ptype.block
    _fields_ = [
        (__key_exchange_data, 'key_exchange_data')
    ]

class ISAKMP_IDENTIFICATION_TYPE(pint.enum, U8):
    _values_ = [
        ('ID_IPV4_ADDR', 0),
        ('ID_IPV4_ADDR_SUBNET', 1),
        ('ID_IPV6_ADDR', 2),
        ('ID_IPV6_ADDR_SUBNET', 3),
    ]

# 6. Identification (ID) Payload
# This payload is used to identify the communicating peers.
@ISAKMP_PAYLOAD.define
class ID_PAYLOAD_v1(pstruct.type):
    type = 5
    def __id_data(self):
        res, fields = getattr(self, '_length_', 0), ['id_type', 'doi']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block
    _fields_ = [
        (ISAKMP_IDENTIFICATION_TYPE, 'id_type'),
        (U32, 'doi'),
        (__id_data, 'id_data'),
    ]

class CERTIFICATE_ENCODING_TYPE(pint.enum, U8):
    _values_ = [
        ('PKCS7', 1),               # PKCS #7 wrapped X.509 certificate      1
        ('PGPCertificate', 2),
        ('DNSSignedKey', 3),
        ('X509Signature', 4),       # X.509 Certificate - Signature
        ('X509KeyExchange', 5),     # X.509 Certificate - Key Exchange
        ('KerberosTokens', 6),
        ('CRL', 7),                 # Certificate Revocation List
        ('ARL', 8),                 # Authority Revocation List
        ('SPKICertificate', 9),
        ('X509Attribute', 10),      # X.509 Certificate - Attribute
    ]

@ISAKMP_PAYLOAD.define
class CERTIFICATE_PAYLOAD_v1(pstruct.type):
    type = 6
    def __certificate_data(self):
        res, fields = getattr(self, '_length_', 0), ['certificate_encoding']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block
    _fields_ = [
        (CERTIFICATE_ENCODING_TYPE, 'certificate_encoding'),
        (__certificate_data, 'certificate_data'),
    ]

@ISAKMP_PAYLOAD.define
class CERT_REQUEST_PAYLOAD_v1(pstruct.type):
    type = 7
    def __certificate_authority(self):
        res, fields = getattr(self, '_length_', 0), ['certificate_type']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block
    _fields_ = [
        (CERTIFICATE_ENCODING_TYPE, 'certificate_type'),
        (__certificate_authority, 'certificate_authority'),
    ]

@ISAKMP_PAYLOAD.define
class HASH_PAYLOAD_v1(pstruct.type):
    type = 8
    def __hash_data(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.block(res)
        return ptype.block
    _fields_ = [
        (__hash_data, 'hash_data'),
    ]

@ISAKMP_PAYLOAD.define
class SIGNATURE_PAYLOAD_v1(pstruct.type):
    type = 9
    def __signature_data(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.block(res)
        return ptype.block
    _fields_ = [
        (__signature_data, 'signature_data'),
    ]

# 7. Nonce Payload [14]
@ISAKMP_PAYLOAD.define
class NONCE_PAYLOAD_v1(pstruct.type):
    type = 10
    def __nonce_data(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.block(res)
        return ptype.block
    _fields_ = [
        (__nonce_data, 'nonce_data'),
    ]

class NOTIFICATION_MESSAGE_TYPE(pint.enum, U16):
    _values_ = [
        ('INVALID-PAYLOAD-TYPE', 1),
        ('DOI-NOT-SUPPORTED', 2),
        ('SITUATION-NOT-SUPPORTED', 3),
        ('INVALID-COOKIE', 4),
        ('INVALID-MAJOR-VERSION', 5),
        ('INVALID-MINOR-VERSION', 6),
        ('INVALID-EXCHANGE-TYPE', 7),
        ('INVALID-FLAGS', 8),
        ('INVALID-MESSAGE-ID', 9),
        ('INVALID-PROTOCOL-ID', 10),
        ('INVALID-SPI', 11),
        ('INVALID-TRANSFORM-ID', 12),
        ('ATTRIBUTES-NOT-SUPPORTED', 13),
        ('NO-PROPOSAL-CHOSEN', 14),
        ('BAD-PROPOSAL-SYNTAX', 15),
        ('PAYLOAD-MALFORMED', 16),
        ('INVALID-KEY-INFORMATION', 17),
        ('INVALID-ID-INFORMATION', 18),
        ('INVALID-CERT-ENCODING', 19),
        ('INVALID-CERTIFICATE', 20),
        ('CERT-TYPE-UNSUPPORTED', 21),
        ('INVALID-CERT-AUTHORITY', 22),
        ('INVALID-HASH-INFORMATION', 23),
        ('AUTHENTICATION-FAILED', 24),
        ('INVALID-SIGNATURE', 25),
        ('ADDRESS-NOTIFICATION', 26),
        ('NOTIFY-SA-LIFETIME', 27),
        ('CERTIFICATE-UNAVAILABLE', 28),
        ('UNSUPPORTED-EXCHANGE-TYPE', 29),
        ('UNEQUAL-PAYLOAD-LENGTHS', 30),
        ('CONNECTED', 16384),
    ]

@ISAKMP_PAYLOAD.define
class NOTIFICATION_PAYLOAD_v1(pstruct.type):
    type = 11
    def __spi(self):
        size = self['spi_size'].li.int()
        if size:
            return dyn.block(size)
        return ptype.block
    def __notification_data(self):
        res, fields = getattr(self, '_length_', 0), ['doi', 'protocol_id', 'spi_size', 'message_type', 'spi']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block
    _fields_ = [
        (U32, 'doi'),
        (ISAKMP_PROTOCOL_IDENTIFIER, 'protocol_id'),
        (U8, 'spi_size'),
        (NOTIFICATION_MESSAGE_TYPE, 'message_type'),
        (__spi, 'spi'),
        (__notification_data, 'notification_data'),
    ]

@ISAKMP_PAYLOAD.define
class DELETE_PAYLOAD_v1(pstruct.type):
    type = 12
    def __spi(self):
        element, count = (self[fld].li.int() for fld in ['spi_size', 'spi_count'])
        element_table = {0: U0, 1: U8, 2: U16, 4: U32, 8: U64}
        element_t = element_table.get(element, dyn.block(element))
        if count:
            return dyn.array(element_t)
        return dyn.clone(parray.type, _object_=element_t)

    _fields_ = [
        (U32, 'doi'),
        (ISAKMP_PROTOCOL_IDENTIFIER, 'protocol_id'),
        (U8, 'spi_size'),
        (U16, 'spi_count'),
        (__spi, 'spi'),
    ]

@ISAKMP_PAYLOAD.define
class VENDOR_ID_PAYLOAD_v1(pstruct.type):
    type = 13
    def __vendor_id(self):
        res = getattr(self, '_length_', 0)
        if res:
            return dyn.block(res)
        return ptype.block
    _fields_ = [
        (__vendor_id, 'vendor_id'),
    ]

class Packet(pstruct.type):
    def __payload(self):
        res = self['next_payload'].li
        return dyn.clone(ISAKMP_PAYLOAD_ARRAY, _type_=res.int())
    _fields_ = [
        (U64, 'initiator_cookie'),  # 8 octets [1, 2, 3, 5]
        (U64, 'responder_cookie'),  # 8 octets [1, 2, 3, 5]
        (ISAKMP_PAYLOAD.enum, 'next_payload'), # 1 octet, type of first payload [3, 4, 5, 6, 7]
        (ISAKMP_VERSION, 'version'), # 4 bits [3, 4, 5]
        (ISAKMP_EXCHANGE_TYPES, 'exchange_type'), # 1 octet [2, 4, 5, 6]
        (ISAKMP_FLAGS, 'flags'), # 1 octet [4, 5]
        (U32, 'message_id'),  # 4 octets [5, 6, 7]
        (U32, 'length'),      # 4 octets, total length of message (header + payloads) [2, 3, 4, 5, 6, 7]
        (__payload, 'payload'),
    ]

class Traffic_Selector_Type(pint.enum, U8):
    _values_ = [
        ('TS_IPV4_ADDR_RANGE', 7),
        ('TS_IPV6_ADDR_RANGE', 8),
    ]

class Traffic_Selector(pstruct.type):
    def __address_type(self):
        res = self['ts_type'].li
        if res['TS_IPV4_ADDR_RANGE']:
            return dyn.block(4)
        elif res['TS_IPV6_ADDR_RANGE']:
            return dyn.block(16)
        raise
    _fields_ = [
        (Traffic_Selector_Type, 'ts_type'),
        (U8, 'ip_protocol_id'),
        (U16, 'selector_length'),
        (U16, 'start_port'),
        (U16, 'end_port'),
        (__address_type, 'start_address'),
        (__address_type, 'end_address'),
    ]

class TS_PAYLOAD_v2(pstruct.type):
    def __ts(self):
        res = self['ts_count'].li
        return dyn.array(Traffic_Selector, res.int())
    _fields_ = [
        (U8, 'ts_count'),
        (U24, 'RESERVED'),
        (__ts, 'ts'),
    ]

@ISAKMP_PAYLOAD.define
class TS_INITIATOR_PAYLOAD_v2(TS_PAYLOAD_v2):
    type = 44
@ISAKMP_PAYLOAD.define
class TS_RESPONDER_PAYLOAD_v2(TS_PAYLOAD_v2):
    type = 45

@ISAKMP_PAYLOAD.define
class ENCRYPTED_PAYLOAD(pstruct.type):
    type = 46
    def __initialization_vector(self):
        if isinstance(self.parent, GENERIC_PAYLOAD) and isinstance(self.parent.parent, ISAKMP_PAYLOAD_ARRAY):
            p = self.getparent(ISAKMP_PAYLOAD_ARRAY)
            # FIXME: need to figure out the IV size from the array
            return dyn.block(16)
        return dyn.block(16)

    # FIXME: none of these fields are defined properly
    _fields_ = [
        (__initialization_vector, 'initialization_vector'),
        (ptype.block, 'encrypted_ike_payloads'),
        (ptype.block, 'padding'),
        (U8, 'pad_length'),
        (ptype.block, 'integrity_checksum_data'),
    ]

class CONFIGURATION_PAYLOAD_TYPE(pint.enum, U8):
    _values_ = [
        ('RESERVED', 0),
        ('CFG_REQUEST', 1),
        ('CFG_REPLY', 2),
        ('CFG_SET', 3),
        ('CFG_ACK', 4),
    ]

class CONFIGURATION_ATTRIBUTE_TYPE(ISAKMP_ATTRIBUTE_TYPE):
    _values_ = [
        ('INTERNAL_IP4_ADDRESS', 1),        # YES*  0 or 4 octets
        ('INTERNAL_IP4_NETMASK', 2),        # NO    0 or 4 octets
        ('INTERNAL_IP4_DNS', 3),            # YES   0 or 4 octets
        ('INTERNAL_IP4_NBNS', 4),           # YES   0 or 4 octets
        ('INTERNAL_ADDRESS_EXPIRY', 5),     # NO    0 or 4 octets
        ('INTERNAL_IP4_DHCP', 6),           # YES   0 or 4 octets
        ('APPLICATION_VERSION', 7),         # NO    0 or more
        ('INTERNAL_IP6_ADDRESS', 8),        # YES*  0 or 17 octets
        ('INTERNAL_IP6_DNS', 10),           # YES   0 or 16 octets
        ('INTERNAL_IP6_NBNS', 11),          # YES   0 or 16 octets
        ('INTERNAL_IP6_DHCP', 12),          # YES   0 or 16 octets
        ('INTERNAL_IP4_SUBNET', 13),        # YES   0 or 8 octets
        ('SUPPORTED_ATTRIBUTES', 14),       # NO    Multiple of 2
        ('INTERNAL_IP6_SUBNET', 15),        # YES   17 octets
    ]

@ISAKMP_PAYLOAD.define
class CONFIGURATION_PAYLOAD(pstruct.type):
    type = 47
    def __cfg_attributes(self):
        res, fields = getattr(self, '_length_', 0), ['cfg_type', 'RESERVED']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        object_t = dyn.clone(ISAKMP_ATTRIBUTE, _type_=CONFIGURATION_ATTRIBUTE_TYPE)
        if size:
            return dyn.clone(ISAKMP_ATTRIBUTES, _object_=object_t, blocksize=lambda _, cb=size: cb)
        return dyn.clone(ISAKMP_ATTRIBUTE_ARRAY, _object_=object_t)
    _fields_ = [
        (CONFIGURATION_PAYLOAD_TYPE, 'cfg_type'),
        (U24, 'RESERVED'),
        (__cfg_attributes, 'cfg_attributes'),
    ]

class EAP_MESSAGE(pstruct.type):
    class _Code(pint.enum, U8):
        _values_ = [
            ('Request', 1),
            ('Response', 2),
            ('Success', 3),
            ('Failure', 4),
        ]

    def __Type(self):
        res = self['Code'].li
        if res['Request'] or res['Response']:
            return U8
        return U0

    def __Type_Data(self):
        res = self['Code'].li
        if not(res['Request'] or res['Response']):
            return U0
        res, fields = getattr(self, '_length_', 0), ['Code', 'Identifier', 'Length', 'Type']
        size = max(0, res - sum(self[fld].li.size() for fld in fields))
        if size:
            return dyn.block(size)
        return ptype.block

    _fields_ = [
        (_Code, 'Code'),
        (U8, 'Identifier'),
        (U16, 'Length'),
        (__Type, 'Type'),
        (__Type_Data, 'Type_Data'),
    ]

@ISAKMP_PAYLOAD.define
class EAP_PAYLOAD(pstruct.type):
    type = 48
    _fields_ = [
        (EAP_MESSAGE, 'eap_message'),
    ]

if __name__ == '__main__':
    import protocol.isakmp
    importlib.reload(protocol.isakmp)

    data = '31f7658ff8a9c2a6759bece169ce6d032e2025080000045d0000004c00000030b83e98f22624e7f347a3e67a7fb99ff4a5ebd32e0c4180b30113e61b7e8cf81df4b7a3781cc91fc0c5532c87'
    bytes = bytearray.fromhex(data)
    source = ptypes.setsource(ptypes.prov.bytes(bytes))

    z = protocol.isakmp.Packet()
    z=z.l

    z['next_payload']
    z['payload'][0]
