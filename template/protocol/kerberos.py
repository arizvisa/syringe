import ptypes
from . import ber
from ptypes import *

Protocol = ber.Protocol.copy(recurse=True)
Universal = Protocol.lookup(ber.Universal.Class)
Context = Protocol.lookup(ber.Context.Class)
Application = Protocol.lookup(ber.Application.Class)

class Packet(ber.Packet):
    Protocol = Protocol

@Universal.define
class OBJECT_IDENTIFIER(ber.OBJECT_IDENTIFIER):
    _values_ = [
        ('iso.org.dod.internet.security.kerberosv5', (1,3,5,1,5,2)),
    ]

class Int32(ber.INTEGER):
    pass

class UInt32(pint.uint_t, ber.INTEGER):
    def __getvalue__(self):
        return super(pint.sinteger_t, self).__getvalue__()
    def __setvalue__(self, *values, **attrs):
        return super(pint.sinteger_t, self).__setvalue__(*values, **attrs)

class Microseconds(ber.INTEGER):
    pass

class KerberosString(ber.GeneralString):
    pass

class Realm(ber.GeneralString):
    pass

class KRB_NT_(pint.enum, ber.INTEGER):
    _values_ = [
        ('UNKNOWN', 0),
        ('PRINCIPAL', 1),
        ('SRV_INST', 2),
        ('SRV_HST', 3),
        ('SRV_XHST', 4),
        ('UID', 5),
    ]

class KRB_(pint.enum, ber.INTEGER):
    _values_ = [
        ('AS_REQ', 10),
        ('AS_REP', 11),
        ('TGS_REQ', 12),
        ('TGS_REP', 13),
        ('AP_REQ', 14),
        ('AP_REP', 15),
        ('SAFE', 20),
        ('PRIV', 21),
        ('CRED', 22),
        ('ERROR', 30),
    ]

class PrincipalName(ber.SEQUENCE):
    class GeneralStringList(ber.SEQUENCE):
        def _object_(self):
            def lookup(_, klasstag):
                return KerberosString if klasstag == KerberosString.type else None
            return dyn.clone(Packet, __object__=lookup)

    _fields_ = [
        (dyn.clone(KRB_NT_, type=(Context, 0)), 'name-type'),
        (dyn.clone(GeneralStringList, type=(Context,1)), 'name-string'),
    ]

class GeneralizedTime(ber.GeneralString):
    pass

class KerberosTime(GeneralizedTime):
    pass

class HostAddress(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Int32, type=(Context, 0)), 'addr-type'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'address'),
    ]

class HostAddresses(ber.SEQUENCE):
    def _object_(self):
        def lookup(_, klasstag):
            return HostAddress if klasstag == HostAddress.type else None
        return dyn.clone(Packet, __object__=lookup)

class APOptions(ber.BITSTRING):
    class options(pbinary.flags):
        _fields_ = [
            (29, 'reserved3-31'),
            (1, 'mutual-required'),
            (1, 'use-session-key'),
            (1, 'reserved'),
        ]
    _object_ = options

class TicketFlags(ber.BITSTRING):
    class flags(pbinary.flags):
        _fields_ = [
            (18, 'reserved14-31'),
            (1, 'ok-as-delegate'),
            (1, 'transited-policy-checked'),
            (1, 'hw-authen'),
            (1, 'pre-authen'),
            (1, 'initial'),
            (1, 'renewable'),
            (1, 'invalid'),
            (1, 'postdated'),
            (1, 'may-postdate'),
            (1, 'proxy'),
            (1, 'proxiable'),
            (1, 'forwarded'),
            (1, 'forwardable'),
            (1, 'reserved'),
        ]
    _object_ = flags

class KDCOptions(ber.BITSTRING):
    class flags(pbinary.flags):
        _fields_ = [
            (1, 'validate'),
            (1, 'renew'),
            (1, 'enc-tkt-in-skey'),
            (1, 'renewable-ok'),
            (1, 'disable-transited-check'),
            (15, 'reserved12-25'),
            (1, 'opt-hardware-auth'),
            (1, 'unused10'),
            (1, 'PK-Cross'),
            (1, 'renewable'),
            (1, 'unused7'),
            (1, 'postdated'),
            (1, 'allow-postdate'),
            (1, 'proxy'),
            (1, 'proxiable'),
            (1, 'forwarded'),
            (1, 'forwardable'),
            (1, 'reserved'),
        ]
    _object_ = flags

class LastReq(ber.SEQUENCE):
    class LastReqItems(ber.SEQUENCE):
        class _lr_type(pint.enum, Int32):
            _values_ = [
                ('none', 0),
                ('tgt-request', 1),
                ('initial-request', 2),
                ('tgt-issue', 3),
                ('renewal', 4),
                ('any', 5),
                ('password-expire', 6),
                ('account-expire', 7),
            ]
        _fields_ = [
            (dyn.clone(_lr_type, type=(Context, 0)), 'lr-type'),
            (dyn.clone(KerberosTime, type=(Context, 1)), 'lr-data'),
        ]
    class _object_(Packet):
        def __object__(self, klasstag):
            return LastReq.LastReqItems

class AuthorizationData(ber.SEQUENCE):
    class AuthorizationDataItems(ber.SEQUENCE):
        class _ad_type(pint.enum, Int32):
            _values_ = [
                ('AD-IF-RELEVANT', 1),
                ('AD-KDC-ISSUED', 4),
                ('AD-AND-OR', 5),
                ('AD-MANDATORY-FOR-KDC', 6),
                ('OSF-DCE', 64),
                ('SESAME', 65),
            ]
        _fields_ = [
            (dyn.clone(_ad_type, type=(Context, 0)), 'ad-type'),
            (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'ad-data'), # FIXME: this should point to one of the post-defined AD_ types
        ]
    class _object_(Packet):
        def __object__(self, klasstag):
            return AuthorizationData.AuthorizationDataItems

class Checksum(ber.SEQUENCE):
    class _cksumtype(pint.enum, Int32):
        _values_ = [
            ('CRC32', 1),
            ('rsa-md4', 2),
            ('rsa-md4-des', 3),
            ('des-mac', 4),
            ('des-mac-k', 5),
            ('rsa-md4-des-k', 6),
            ('rsa-md5', 7),
            ('rsa-md5-des', 8),
        ]
    _fields_ = [
        (dyn.clone(_cksumtype, type=(Context, 0)), 'cksumtype'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'checksum'),
    ]

class AD_IF_RELEVANT(AuthorizationData):
    pass

class AD_KDCIssued(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Checksum, type=(Context, 0)), 'ad-checksum'),
        (dyn.clone(Realm, type=(Context, 1)), 'i-realm'),
        (dyn.clone(PrincipalName, type=(Context, 2)), 'i-sname'),
        (dyn.clone(AuthorizationData, type=(Context, 3)), 'elements'),
    ]

class AD_AND_OR(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Int32, type=(Context, 0)), 'condition-count'),
        (dyn.clone(AuthorizationData, type=(Context, 1)), 'elements'),
    ]

class AD_MANDATORY_FOR_KDC(AuthorizationData):
    pass

class EncryptionKey(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Int32, type=(Context, 0)), 'keytype'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'keyvalue'),
    ]

class EncryptedData(ber.SEQUENCE):
    # FIXME: the "cipher" field should have its _object_
    #        attribute assigned with a ptype.encoded_t so
    #        that we can encrypt/decrypt its data when it's
    #        given a proper stream that has been seeded by
    #        a key.
    class _etype(pint.enum, Int32):
        _values_ = [
            ('NULL', 0),
            ('des-cbc-crc', 1),
            ('des-cbc-md4', 2),
            ('des-cbc-md5', 3),
        ]

    _fields_ = [
        (dyn.clone(_etype, type=(Context, 0)), 'etype'),
        (dyn.clone(UInt32, type=(Context, 1)), 'kvno'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 2)), 'cipher'),
    ]

class CipherText(pstruct.type):
    # FIXME: these fields should be sized according to the
    #        encryption type. as they are not being sized,
    #        if this class is instantiated as-is, the fields
    #        will not contain anything.
    _fields_ = [
        (ptype.block, 'confounder'),
        (ptype.block, 'check'),
        (ptype.block, 'msg-seq'),
        (dyn.padding(0), 'pad'),
    ]

class TransitedEncoding(ber.SEQUENCE):
    class _tr_type(pint.enum, Int32):
        _values_ = [
            ('DOMAIN-X500-COMPRESS', 1),
        ]
    _fields_ = [
        (dyn.clone(_tr_type, type=(Context, 0)), 'tr-type'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'contents'),
    ]

@Application.define
class Ticket(ber.SEQUENCE):
    tag = 1
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'tkt-vno'),
        (dyn.clone(Realm, type=(Context, 1)), 'realm'),
        (dyn.clone(PrincipalName, type=(Context, 2)), 'sname'),
        (dyn.clone(EncryptedData, type=(Context, 3)), 'enc-part'),
    ]

@Application.define
class EncTicketPart(ber.SEQUENCE):
    tag = 3
    _fields_ = [
        (dyn.clone(TicketFlags, type=(Context, 0)), 'flags'),
        (dyn.clone(EncryptionKey, type=(Context, 1)), 'keys'),
        (dyn.clone(Realm, type=(Context, 2)), 'crealm'),
        (dyn.clone(PrincipalName, type=(Context, 3)), 'cname'),
        (dyn.clone(TransitedEncoding, type=(Context, 4)), 'transited'),
        (dyn.clone(KerberosTime, type=(Context, 5)), 'authtime'),
        (dyn.clone(KerberosTime, type=(Context, 6)), 'starttime'),
        (dyn.clone(KerberosTime, type=(Context, 7)), 'endtime'),
        (dyn.clone(KerberosTime, type=(Context, 8)), 'renew-till'),
        (dyn.clone(HostAddresses, type=(Context, 9)), 'caddr'),
        (dyn.clone(AuthorizationData, type=(Context, 10)), 'authorization-data'),
    ]

@Application.define
class Authenticator(ber.SEQUENCE):
    tag = 2
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'authenticator-vno'),
        (dyn.clone(Realm, type=(Context, 1)), 'crealm'),
        (dyn.clone(PrincipalName, type=(Context, 2)), 'cname'),
        (dyn.clone(Checksum, type=(Context, 3)), 'cksum'),
        (dyn.clone(Microseconds, type=(Context, 4)), 'cusec'),
        (dyn.clone(KerberosTime, type=(Context, 5)), 'ctime'),
        (dyn.clone(EncryptionKey, type=(Context, 6)), 'subkey'),
        (dyn.clone(UInt32, type=(Context, 7)), 'seq-number'),
        (dyn.clone(AuthorizationData, type=(Context, 8)), 'authorization-data'),
    ]

class PA_ENC_TS_ENC(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(KerberosTime, type=(Context, 0)), 'patimestamp'),
        (dyn.clone(Microseconds, type=(Context, 1)), 'pausec'),
    ]

class PA_ENC_TIMESTAMP(EncryptedData):
    pass

class ETYPE_INFO_ENTRY(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Int32, type=(Context, 0)), 'etype'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'salt'),
    ]

class ETYPE_INFO(ber.SEQUENCE):
    def _object_(self):
        def lookup(_, klasstag):
            return ETYPE_INFO_ENTRY if klasstag == ETYPE_INFO_ENTRY.type else None
        return dyn.clone(Packet, __object__=lookup)

class ETYPE_INFO2_ENTRY(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Int32, type=(Context, 0)), 'etype'),
        (dyn.clone(KerberosString, type=(Context, 1)), 'salt'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 2)), 's2kparams'),
    ]

class ETYPE_INFO2(ber.SEQUENCE):
    def _object_(self):
        def lookup(_, klasstag):
            return ETYPE_INFO2_ENTRY if klasstag == ETYPE_INFO2_ENTRY.type else None
        return dyn.clone(Packet, __object__=lookup)

class PA_DATA(ber.SEQUENCE):
    class _padata_type(pint.enum, ber.INTEGER):
        _values_ = [
            ('pa-tgs-req', 1),          # FIXME: this points to AP-REQ
            ('pa-enc-timestamp', 2),
            ('pa-pw-salt', 3),          # FIXME: not ASN.1 encoded data
            ('pa-etype-info', 11),
            ('pa-etype-info2', 19),
        ]
    _fields_ = [
        (dyn.clone(_padata_type, type=(Context, 1)), 'padata-type'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 2)), 'padata-value'),    # FIXME: this should point to one of the prior types
    ]

class KerberosFlags(ber.BITSTRING):
    pass

class EncryptionType(ber.SEQUENCE):
    class _object_(Packet):
        def __object__(self, klasstag):
            return Int32 if klasstag == Int32.type else None

class KDC_REQ_BODY(ber.SEQUENCE):
    class _additional_tickets(ber.SEQUENCE):
        class _object_(Packet):
            def __object__(self, klasstag):
                return Ticket if klasstag == Ticket.type else None

    _fields_ = [
        (dyn.clone(KDCOptions, type=(Context, 0)), 'kdc-options'),
        (dyn.clone(PrincipalName, type=(Context, 1)), 'cname'),
        (dyn.clone(Realm, type=(Context, 2)), 'realm'),
        (dyn.clone(PrincipalName, type=(Context, 3)), 'sname'),
        (dyn.clone(KerberosTime, type=(Context, 4)), 'from'),
        (dyn.clone(KerberosTime, type=(Context, 5)), 'till'),
        (dyn.clone(KerberosTime, type=(Context, 6)), 'rtime'),
        (dyn.clone(UInt32, type=(Context, 7)), 'nonce'),
        (dyn.clone(EncryptionType, type=(Context, 8)), 'etype'),
        (dyn.clone(HostAddresses, type=(Context, 9)), 'addresses'),
        (dyn.clone(EncryptedData, type=(Context, 10)), 'enc-authorization-data'),
        (dyn.clone(_additional_tickets, type=(Context, 11)), 'additional-tickets'),
    ]

class KDC_REQ(ber.SEQUENCE):
    class _pa_data(ber.SEQUENCE):
        class _object_(Packet):
            def __object__(self, klasstag):
                return PA_DATA if klasstag == PA_DATA.type else None

    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 1)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 2)), 'msg-type'),
        (dyn.clone(_pa_data, type=(Context, 3)), 'padata'),
        (dyn.clone(KDC_REQ_BODY, type=(Context, 4)), 'req-body'),
    ]

@Application.define
class AS_REQ(KDC_REQ):
    tag = 10

@Application.define
class TGS_REQ(KDC_REQ):
    tag = 12

class KDC_REP(ber.SEQUENCE):
    class _pa_data(ber.SEQUENCE):
        class _object_(Packet):
            def __object__(self, klasstag):
                return PA_DATA if klasstag == PA_DATA.type else None

    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(_pa_data, type=(Context, 2)), 'padata'),
        (dyn.clone(Realm, type=(Context, 3)), 'crealm'),
        (dyn.clone(PrincipalName, type=(Context, 4)), 'cname'),
        (dyn.clone(Ticket, type=(Context, 5)), 'ticket'),
        (dyn.clone(EncryptedData, type=(Context, 6)), 'enc-part'),
    ]

@Application.define
class AS_REP(KDC_REP):
    tag = 11

@Application.define
class TGS_REP(KDC_REP):
    tag = 13

class EncKDCRepPart(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(EncryptionKey, type=(Context, 0)), 'key'),
        (dyn.clone(LastReq, type=(Context, 1)), 'last-req'),
        (dyn.clone(UInt32, type=(Context, 2)), 'nonce'),
        (dyn.clone(KerberosTime, type=(Context, 3)), 'key-expiration'),
        (dyn.clone(TicketFlags, type=(Context, 4)), 'flags'),
        (dyn.clone(KerberosTime, type=(Context, 5)), 'authtime'),
        (dyn.clone(KerberosTime, type=(Context, 6)), 'starttime'),
        (dyn.clone(KerberosTime, type=(Context, 7)), 'endtime'),
        (dyn.clone(KerberosTime, type=(Context, 8)), 'renew-till'),
        (dyn.clone(Realm, type=(Context, 9)), 'srealm'),
        (dyn.clone(PrincipalName, type=(Context, 10)), 'sname'),
        (dyn.clone(HostAddresses, type=(Context, 11)), 'caddr'),
    ]

@Application.define
class EncASRepPart(EncKDCRepPart):
    tag = 25

@Application.define
class EncTGSRepPart(EncKDCRepPart):
    tag = 26

@Application.define
class AP_REQ(ber.SEQUENCE):
    tag = 14
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(APOptions, type=(Context, 2)), 'ap-options'),
        (dyn.clone(Ticket, type=(Context, 3)), 'ticket'),
        (dyn.clone(EncryptedData, type=(Context, 4)), 'authenticator'),
    ]

@Application.define
class AP_REP(ber.SEQUENCE):
    tag = 15
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(EncryptedData, type=(Context, 2)), 'enc-part'),
    ]

@Application.define
class EncAPRepPart(ber.SEQUENCE):
    tag = 27
    _fields_ = [
        (dyn.clone(KerberosTime, type=(Context, 0)), 'ctime'),
        (dyn.clone(Microseconds, type=(Context, 1)), 'cusec'),
        (dyn.clone(EncryptionKey, type=(Context, 2)), 'subkey'),
        (dyn.clone(UInt32, type=(Context, 3)), 'seq-number'),
    ]

class KRB_SAFE_BODY(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(ber.OCTETSTRING, type=(Context, 0)), 'user-data'),
        (dyn.clone(KerberosTime, type=(Context, 1)), 'timestamp'),
        (dyn.clone(Microseconds, type=(Context, 2)), 'usec'),
        (dyn.clone(UInt32, type=(Context, 3)), 'seq-number'),
        (dyn.clone(HostAddress, type=(Context, 4)), 's-address'),
        (dyn.clone(HostAddress, type=(Context, 5)), 'r-address'),
    ]

@Application.define
class KRB_SAFE(ber.SEQUENCE):
    tag = 20
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(KRB_SAFE_BODY, type=(Context, 2)), 'safe-body'),
        (dyn.clone(Checksum, type=(Context, 3)), 'cksum'),
    ]

@Application.define
class KRB_PRIV(ber.SEQUENCE):
    tag = 21
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(EncryptedData, type=(Context, 3)), 'enc-part'),
    ]

@Application.define
class EncKrbPrivPart(ber.SEQUENCE):
    tag = 28
    _fields_ = [
        (dyn.clone(ber.OCTETSTRING, type=(Context, 0)), 'user-data'),
        (dyn.clone(KerberosTime, type=(Context, 1)), 'timestamp'),
        (dyn.clone(Microseconds, type=(Context, 2)), 'usec'),
        (dyn.clone(UInt32, type=(Context, 3)), 'seq-number'),
        (dyn.clone(HostAddress, type=(Context, 4)), 's-address'),
        (dyn.clone(HostAddress, type=(Context, 5)), 'r-address'),
    ]

@Application.define
class KRB_CRED(ber.SEQUENCE):
    tag = 22
    class _tickets(ber.SEQUENCE):
        class _object_(Packet):
            def __object__(self, klasstag):
                return Ticket if klasstag == Ticket.type else None
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(_tickets, type=(Context, 2)), 'tickets'),
        (dyn.clone(EncryptedData, type=(Context, 3)), 'enc-part'),
    ]

class KrbCredInfo(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(EncryptionKey, type=(Context, 0)), 'key'),
        (dyn.clone(Realm, type=(Context, 1)), 'prealm'),
        (dyn.clone(PrincipalName, type=(Context, 2)), 'pname'),
        (dyn.clone(TicketFlags, type=(Context, 3)), 'flags'),
        (dyn.clone(KerberosTime, type=(Context, 4)), 'authtime'),
        (dyn.clone(KerberosTime, type=(Context, 5)), 'starttime'),
        (dyn.clone(KerberosTime, type=(Context, 6)), 'endtime'),
        (dyn.clone(KerberosTime, type=(Context, 7)), 'renew-till'),
        (dyn.clone(Realm, type=(Context, 8)), 'srealm'),
        (dyn.clone(PrincipalName, type=(Context, 9)), 'sname'),
        (dyn.clone(HostAddresses, type=(Context, 10)), 'caddr'),
    ]

@Application.define
class EncKrbCredPart(ber.SEQUENCE):
    tag = 29
    class _ticket_info(ber.SEQUENCE):
        class _object_(Packet):
            def __object__(self, klasstag):
                return KrbCredInfo if klasstag == KrbCredInfo.type else None
    _fields_ = [
        (dyn.clone(_ticket_info, type=(Context, 0)), 'ticket-info'),
        (dyn.clone(UInt32, type=(Context, 1)), 'nonce'),
        (dyn.clone(KerberosTime, type=(Context, 2)), 'timestamp'),
        (dyn.clone(Microseconds, type=(Context, 3)), 'usec'),
        (dyn.clone(HostAddress, type=(Context, 4)), 's-address'),
        (dyn.clone(HostAddress, type=(Context, 5)), 'r-address'),
    ]

class KDC_ERR(pint.enum, Int32):
    _values_ = [
        ('KDC_ERR_NONE', 0),                    # No error
        ('KDC_ERR_NAME_EXP', 1),                # Client's entry in database has expired
        ('KDC_ERR_SERVICE_EXP', 2),             # Server's entry in database has expired
        ('KDC_ERR_BAD_PVNO', 3),                # Requested protocol version number not supported
        ('KDC_ERR_C_OLD_MAST_KVNO', 4),         # Client's key encrypted in old master key
        ('KDC_ERR_S_OLD_MAST_KVNO', 5),         # Server's key encrypted in old master key
        ('KDC_ERR_C_PRINCIPAL_UNKNOWN', 6),     # Client not found in Kerberos database
        ('KDC_ERR_S_PRINCIPAL_UNKNOWN', 7),     # Server not found in Kerberos database
        ('KDC_ERR_PRINCIPAL_NOT_UNIQUE', 8),    # Multiple principal entries in database
        ('KDC_ERR_NULL_KEY', 9),                # The client or server has a null key
        ('KDC_ERR_CANNOT_POSTDATE', 10),        # Ticket not eligible for postdating
        ('KDC_ERR_NEVER_VALID', 11),            # Requested start time is later than end time
        ('KDC_ERR_POLICY', 12),                 # KDC policy rejects request
        ('KDC_ERR_BADOPTION', 13),              # KDC cannot accommodate requested option
        ('KDC_ERR_ETYPE_NOSUPP', 14),           # KDC has no support for encryption type
        ('KDC_ERR_SUMTYPE_NOSUPP', 15),         # KDC has no support for checksum type
        ('KDC_ERR_PADATA_TYPE_NOSUPP', 16),     # KDC has no support for padata type
        ('KDC_ERR_TRTYPE_NOSUPP', 17),          # KDC has no support for transited type
        ('KDC_ERR_CLIENT_REVOKED', 18),         # Clients credentials have been revoked
        ('KDC_ERR_SERVICE_REVOKED', 19),        # Credentials for server have been revoked
        ('KDC_ERR_TGT_REVOKED', 20),            # TGT has been revoked
        ('KDC_ERR_CLIENT_NOTYET', 21),          # Client not yet valid - try again later
        ('KDC_ERR_SERVICE_NOTYET', 22),         # Server not yet valid - try again later
        ('KDC_ERR_KEY_EXPIRED', 23),            # Password has expired - change password to reset
        ('KDC_ERR_PREAUTH_FAILED', 24),         # Pre-authentication information was invalid
        ('KDC_ERR_PREAUTH_REQUIRED', 25),       # Additional pre-authentication required*
        ('KRB_AP_ERR_BAD_INTEGRITY', 31),       # Integrity check on decrypted field failed
        ('KRB_AP_ERR_TKT_EXPIRED', 32),         # Ticket expired
        ('KRB_AP_ERR_TKT_NYV', 33),             # Ticket not yet valid
        ('KRB_AP_ERR_REPEAT', 34),              # Request is a replay
        ('KRB_AP_ERR_NOT_US', 35),              # The ticket isn't for us
        ('KRB_AP_ERR_BADMATCH', 36),            # Ticket and authenticator don't match
        ('KRB_AP_ERR_SKEW', 37),                # Clock skew too great
        ('KRB_AP_ERR_BADADDR', 38),             # Incorrect net address
        ('KRB_AP_ERR_BADVERSION', 39),          # Protocol version mismatch
        ('KRB_AP_ERR_MSG_TYPE', 40),            # Invalid msg type
        ('KRB_AP_ERR_MODIFIED', 41),            # Message stream modified
        ('KRB_AP_ERR_BADORDER', 42),            # Message out of order
        ('KRB_AP_ERR_BADKEYVER', 44),           # Specified version of key is not available
        ('KRB_AP_ERR_NOKEY', 45),               # Service key not available
        ('KRB_AP_ERR_MUT_FAIL', 46),            # Mutual authentication failed
        ('KRB_AP_ERR_BADDIRECTION', 47),        # Incorrect message direction
        ('KRB_AP_ERR_METHOD', 48),              # Alternative authentication method required*
        ('KRB_AP_ERR_BADSEQ', 49),              # Incorrect sequence number in message
        ('KRB_AP_ERR_INAPP_CKSUM', 50),         # Inappropriate type of checksum in
        ('KRB_ERR_GENERIC', 60),                # Generic error (description in e-text)
        ('KRB_ERR_FIELD_TOOLONG', 61),          # Field is too long for this implementation
    ]

@Application.define
class KRB_ERROR(ber.SEQUENCE):
    tag = 30
    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'pvno'),
        (dyn.clone(KRB_, type=(Context, 1)), 'msg-type'),
        (dyn.clone(KerberosTime, type=(Context, 2)), 'ctime'),
        (dyn.clone(Microseconds, type=(Context, 3)), 'cusec'),
        (dyn.clone(KerberosTime, type=(Context, 4)), 'stime'),
        (dyn.clone(Microseconds, type=(Context, 5)), 'susec'),
        (dyn.clone(KDC_ERR, type=(Context, 6)), 'error-code'),
        (dyn.clone(Realm, type=(Context, 7)), 'crealm'),
        (dyn.clone(PrincipalName, type=(Context, 8)), 'cname'),
        (dyn.clone(Realm, type=(Context, 9)), 'realm'),
        (dyn.clone(PrincipalName, type=(Context, 10)), 'sname'),
        (dyn.clone(KerberosString, type=(Context, 11)), 'e-text'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 12)), 'e-data'),
    ]

class METHOD_DATA(ber.SEQUENCE):
    class _method_type(pint.enum, Int32):
        _values_ = [
            ('ATT-CHALLENGE-RESPONSE', 64),
        ]
    _fields_ = [
        (dyn.clone(_method_type, type=(Context, 0)), 'method-type'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'method-value'),
    ]

if __name__ == '__main__':
    import sys, operator
    import ptypes, protocol.ber as ber, protocol.kerberos as krb5
    from ptypes import bitmap
    from ptypes import *

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex
