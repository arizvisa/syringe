import ptypes, protocol.ber as ber, protocol.per as per, protocol.gcc as gcc

import protocol.mas as mas
from protocol.mas import CapabilitySetType, PDUType, PDUType2, Integer8, Integer16, Integer32, Boolean8, Boolean16

from protocol.intsafe import GUID
from ptypes import *

import functools, itertools, types, builtins, operator
import logging

fcompose = lambda *f: functools.reduce(lambda f1, f2: lambda *a: f1(f2(*a)), builtins.reversed(f))
fpartial = functools.partial
islice = itertools.islice

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

@pint.littleendian
class INTEGER(pint.uint_t):
    def summary(self):
        res = self.size()
        return "({:d}) {:0{:d}X}".format(8 * res, self.int(), 2 * res)

### RDP negotiations packets
class TYPE_RDP_(pint.enum, pint.uint8_t):
    _values_ = [
        ('NEG_REQ', 0x01),
        ('CORRELATION_INFO', 0x06),
        ('NEG_RSP', 0x02),
        ('NEG_FAILURE', 0x03),
    ]

class RDP_NEG_TYPE(ptype.definition):
    cache = {}

    @pbinary.littleendian
    class Flags(pbinary.flags):
        _fields_ = [(8, 'unused')]

class RDP_NEG(pstruct.type):
    def __flags(self):
        res = self['type'].li.int()
        t = RDP_NEG_TYPE.lookup(res, RDP_NEG_TYPE)
        return getattr(t, 'Flags', RDP_NEG_TYPE.Flags)

    def __value(self):
        res = self['type'].li.int()
        cb = sum(self[fld].li.size() for fld in ['type','flags','length'])
        return RDP_NEG_TYPE.lookup(res, dyn.block(max((0, self['length'].li.int() - cb))))

    def __padding(self):
        cb = sum(self[fld].li.size() for fld in ['type','flags','length','value'])
        res = self['length'].li.int()
        if cb <= res:
            return dyn.block(res - cb)
        return ptype.undefined

    _fields_ = [
        (TYPE_RDP_, 'type'),
        (__flags, 'flags'),
        (pint.uint16_t, 'length'),
        (__value, 'value'),
        (__padding, 'padding'),
    ]

    def alloc(self, **fields):
        res = super(RDP_NEG, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=sum(res[fld].size() for fld in ['type','flags','length','value','padding']))

class RDP_NEGOTIATION(pstruct.type):
    def __rdpPackets(self):
        return dyn.array(RDP_NEG, 0) if self.parent is None else dyn.blockarray(RDP_NEG, self.blocksize())

    _fields_ = [
        (pstr.string, 'routingToken'),
        (pstr.string, 'cookie'),
        (__rdpPackets, 'rdpPackets'),
    ]

@RDP_NEG_TYPE.define
class RDP_NEG_REQ(pstruct.type):
    type = 0x01

    @pbinary.littleendian
    class Flags(pbinary.flags):
        _fields_ = [
            (4, 'UNKNOWN(4)'),
            (1, 'CORRELATION_INFO_PRESENT'),
            (1, 'RESERVED'),
            (1, 'REDIRECTED_AUTHENTICATION_MODE_REQUIRED'),
            (1, 'RESTRICTED_ADMIN_MODE_REQUIRED'),
        ]

    @pbinary.littleendian
    class PROTOCOL_(pbinary.flags):
        _fields_ = [
            (0, 'RDP'),     # place-holder that doesn't do anything
            (28, 'unused'),
            (1, 'HYBRID_EX'),
            (1, 'RDSTLS'),
            (1, 'HYBRID'),
            (1, 'SSL'),
        ]

    _fields_ = [
        (PROTOCOL_, 'selectedProtocol'),
    ]

    def summary(self):
        res = self['selectedProtocol']
        return "selectedProtocol={:s}".format(res.summary())

@RDP_NEG_TYPE.define
class RDP_NEG_RSP(pstruct.type):
    type = 0x02

    @pbinary.littleendian
    class Flags(pbinary.flags):
        _fields_ = [
            (3, 'UNKNOWN(3)'),
            (1, 'REDIRECTED_AUTHENTICATION_MODE_SUPPORTED'),
            (1, 'RESTRICTED_ADMIN_MODE_SUPPORTED'),
            (1, 'NEGRSP_FLAG_RESERVED'),
            (1, 'DYNVC_GFX_PROTOCOL_SUPPORTED'),
            (1, 'EXTENDED_CLIENT_DATA_SUPPORTED'),
        ]

    class PROTOCOL_(pint.enum, pint.uint32_t):
        _values_ = [
            ('RDP', 0),
            ('SSL', 1),
            ('HYBRID', 2),
            ('RDSTLS', 4),
            ('HYBRID_EX', 8),
        ]

    _fields_ = [
        (PROTOCOL_, 'selectedProtocol'),
    ]

    def summary(self):
        res = self['selectedProtocol']
        return "selectedProtocol={:s}".format(res.summary())

@RDP_NEG_TYPE.define
class RDP_NEG_FAILURE(pstruct.type):
    type = 0x03

    class _failureCode(pint.enum, pint.uint32_t):
        _values_ = [
            ('SSL_REQUIRED_BY_SERVER', 0x00000001),
            ('SSL_NOT_ALLOWED_BY_SERVER', 0x00000002),
            ('SSL_CERT_NOT_ON_SERVER', 0x00000003),
            ('INCONSISTENT_FLAGS', 0x00000004),
            ('HYBRID_REQUIRED_BY_SERVER', 0x00000005),
            ('SSL_WITH_USER_AUTH_REQUIRED_BY_SERVER', 0x00000006),
        ]

    _fields_ = [
        (_failureCode, 'failureCode'),
    ]

    def summary(self):
        res = self['failureCode']
        return "failureCode={:s}".format(res.summary())

@RDP_NEG_TYPE.define
class RDP_NEG_CORRELATION_INFO(pstruct.type):
    type = 0x06

    _fields_ = [
        (dyn.block(16), 'correlationId'),
        (dyn.block(16), 'reserved'),
    ]

    def summary(self):
        res = self['correlationId']
        return "correlationId={:#0{:d}x} reserved={:#x}".format(res.cast(pint.uint_t, length=res.size()).int(), 2 + res.size() * 2, self['reserved'].cast(pint.uint_t, length=self['reserved'].size()).int())

### TS UserData packets
class TS_UD(ptype.definition): cache = {}

class TS_UD_HEADER(pint.enum, pint.uint16_t):
    _values_ = [
        ('CS_CORE', 0xc001),
        ('CS_SECURITY', 0xc002),
        ('CS_NET', 0xc003),
        ('CS_CLUSTER', 0xc004),
        ('CS_MONITOR', 0xc005),
        ('CS_MCS_MSGCHANNEL', 0xc006),
        ('CS_MONITOR_EX', 0xc008),
        ('CS_MULTITRANSPORT', 0xc00a),
        ('SC_CORE', 0x0c01),
        ('SC_SECURITY', 0x0c02),
        ('SC_NET', 0x0c03),
        ('SC_MCS_MSGCHANNEL', 0x0c04),
        ('SC_MULTITRANSPORT', 0x0c08),
    ]

class TS_UD_PACKET(pstruct.type):
    def __value(self):
        res, length = self['type'].li, self['length'].li
        cb = sum(self[fld].li.size() for fld in ['type','length'])
        return TS_UD.get(res.int(), blocksize=lambda self, cb=max((length.int() - cb, 0)): cb)

    def __extra(self):
        res = self['length'].li
        cb = sum(self[fld].li.size() for fld in ['type','length','value'])
        return dyn.block(max((res.int() - cb, 0)))

    _fields_ = [
        (TS_UD_HEADER, 'type'),
        (pint.uint16_t, 'length'),
        (__value, 'value'),
        (__extra, 'padding'),
    ]

    def alloc(self, **fields):
        res = super(TS_UD_PACKET, self).alloc(**fields)
        flds = {}
        if 'length' not in fields:
            flds['length'] = res['value'].size() + sum(self[fld].size() for fld in ['type','length'])
        if 'type' not in fields and hasattr(res['value'], 'type'):
            flds['type'] = res['value'].type
        return res.set(**flds) if flds else res

class TS_UD_PACKETS(parray.block):
    _object_ = TS_UD_PACKET

class RNS_UD_COLOR_(pint.enum, pint.uint16_t):
    _values_ = [
        ('4BPP', 0xCA00),
        ('8BPP', 0xCA01),
        ('16BPP_555', 0xCA02),
        ('16BPP_565', 0xCA03),
        ('24BPP', 0xCA04),
    ]

class RNS_UD_SAS_(pint.enum, pint.uint16_t):
    _values_ = [
        ('DEL', 0xaa03),
    ]

class HIGH_COLOR_(pint.enum, pint.uint16_t):
    _values_ = [
        ('4BPP', 0x0004),
        ('8BPP', 0x0008),
        ('15BPP', 0x000f),
        ('16BPP', 0x0010),
        ('24BPP', 0x0018),
    ]

@pbinary.littleendian
class RNS_UD_BPP_(pbinary.flags):
    _fields_ = [
        (12, 'unused'),
        (1, 'SUPPORT_32BPP'),
        (1, 'SUPPORT_15BPP'),
        (1, 'SUPPORT_16BPP'),
        (1, 'SUPPORT_24BPP'),
    ]

@pbinary.littleendian
class RNS_UD_CS_(pbinary.flags):
    _fields_ = [
        (5, 'unused'),
        (1, 'SUPPORT_HEARTBEAT_PDU'),
        (1, 'SUPPORT_DYNAMIC_TIME_ZONE'),
        (1, 'SUPPORT_DYNVC_GFX_PROTOCOL'),

        (1, 'SUPPORT_NETCHAR_AUTODETECT'),
        (1, 'SUPPORT_MONITOR_LAYOUT_PDU'),
        (1, 'VALID_CONNECTION_TYPE'),
        (1, 'UNUSED'),
        (1, 'STRONG_ASYMMETRIC_KEYS'),
        (1, 'SUPPORT_STATUSINFO_PDU'),
        (1, 'WANT_32BPP_SESSION'),
        (1, 'SUPPORT_ERRINFO_PDU'),
    ]

class CONNECTION_TYPE_(pint.enum, pint.uint8_t):
    _values_ = [
        ('MODEM', 0x01),
        ('BROADBAND_LOW', 0x02),
        ('SATELLITE', 0x03),
        ('BROADBAND_HIGH', 0x04),
        ('WAN', 0x05),
        ('LAN', 0x06),
        ('AUTODETECT', 0x07),
    ]

class TS_VERSION(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'major'),
        (pint.uint16_t, 'minor'),
    ]

    def summary(self):
        return "major={:d} minor={:d}".format(self['major'].int(), self['minor'].int())

@TS_UD.define
class TS_UD_CS_CORE(pstruct.type):
    type = 0xc001

    _fields_ = [
        (TS_VERSION, 'version'),
        (pint.uint16_t, 'desktopWidth'),
        (pint.uint16_t, 'desktopHeight'),
        (RNS_UD_COLOR_, 'colorDepth'),
        (RNS_UD_SAS_, 'SASSequence'),
        (pint.uint32_t, 'keyboardLayout'),
        (pint.uint32_t, 'clientBuild'),
        (dyn.clone(pstr.wstring, length=16), 'clientName'),
        (pint.uint32_t, 'keyboardType'),
        (pint.uint32_t, 'keyboardSubType'),
        (pint.uint32_t, 'keyboardFunctionKey'),
        (dyn.block(64), 'imeFileName'),
        (RNS_UD_COLOR_, 'postBeta2ColorDepth'),
        (pint.uint16_t, 'clientProductId'),
        (pint.uint32_t, 'serialNumber'),
        (HIGH_COLOR_, 'highColorDepth'),
        (RNS_UD_BPP_, 'supportedColorDepths'),
        (RNS_UD_CS_, 'earlyCapabilityFlags'),
        (dyn.clone(pstr.wstring, length=32), 'clientDigProductId'),
        (CONNECTION_TYPE_, 'connectionType'),
        (pint.uint8_t, 'pad1octet'),
        (pint.uint32_t, 'serverSelectedProtocol'),
        (pint.uint32_t, 'desktopPhysicalWidth'),
        (pint.uint32_t, 'desktopPhysicalHeight'),
        (pint.uint32_t, 'desktopOrientation'),
        (pint.uint32_t, 'desktopScaleFactor'),
        (pint.uint32_t, 'deviceScaleFactor'),
    ]

    def alloc(self, **fields):
        res = super(TS_UD_CS_CORE, self).alloc(**fields)
        if 'connectionType' in fields:
            res['earlyCapabilityFlags'].set(VALID_CONNECTION_TYPE=1)
        return res

@pbinary.littleendian
class ENCRYPTION_METHOD_(pbinary.flags):
    _fields_ = [
        (27, 'unused'),
        (1, 'FIPS'),
        (1, '56BIT'),
        (1, 'RESERVED'),
        (1, '128BIT'),
        (1, '40BIT'),
    ]

class ENCRYPTION_LEVEL_(pint.enum, pint.uint32_t):
    _values_ = [
        ('NONE', 0x00000000),
        ('LOW', 0x00000001),
        ('CLIENT_COMPATIBLE', 0x00000002),
        ('HIGH', 0x00000003),
        ('FIPS', 0x00000004),
    ]

@TS_UD.define
class TS_UD_CS_SEC(pstruct.type):
    type = 0xc002
    _fields_ = [
        (ENCRYPTION_METHOD_, 'encryptionMethods'),
        (pint.uint32_t, 'extEncryptionMethods'),
    ]

@pbinary.littleendian
class CHANNEL_OPTION_(pbinary.flags):
    _fields_ = [
        (1, 'INITIALIZED'),
        (1, 'ENCRYPT_RDP'),
        (1, 'ENCRYPT_SC'),
        (1, 'ENCRYPT_CS'),
        (1, 'PRI_HIGH'),
        (1, 'PRI_MED'),
        (1, 'PRI_LOW'),
        (1, 'RESERVED'),

        (1, 'COMPRESS_RDP'),
        (1, 'COMPRESS'),
        (1, 'SHOW_PROTOCOL'),
        (1, 'REMOTE_CONTROL_PERSISTENT'),
        (20, 'unused'),
    ]

class CHANNEL_DEF(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'name'),
        (CHANNEL_OPTION_, 'options'),
    ]

@TS_UD.define
class TS_UD_CS_NET(pstruct.type):
    type = 0xc003
    _fields_ = [
        (pint.uint32_t, 'channelCount'),
        (lambda self: dyn.array(CHANNEL_DEF, self['channelCount'].li.int()), 'channelDefArray'),
    ]

class REDIRECTION_VERSION(pbinary.enum):
    width, _values_ = 4, [
        ('VERSION1', 0x00),
        ('VERSION2', 0x01),
        ('VERSION3', 0x02),
        ('VERSION4', 0x03),
        ('VERSION5', 0x04),
        ('VERSION6', 0x05),
    ]

@pbinary.littleendian
class REDIRECTED_(pbinary.flags):
    _fields_ = [
        (25, 'unused'),
        (1, 'SMARTCARD'),
        (REDIRECTION_VERSION, 'ServerSessionRedirectionMask'),
        (1, 'SESSIONID_FIELD_VALID'),
        (1, 'SUPPORTED'),
    ]

@TS_UD.define
class TS_UD_CS_CLUSTER(pstruct.type):
    type = 0xc004
    _fields_ = [
        (REDIRECTED_, 'Flags'),
        (pint.uint32_t, 'RedirectedSessionID'),
    ]
    def alloc(self, **fields):
        res = super(TS_UD_CS_CLUSTER, self).alloc(**fields)
        if 'RedirectedSessionID' in fields:
            res['Flags'].set(SESSIONID_FIELD_VALID=1)
        return res

class TS_MONITOR_(pbinary.flags):
    _fields_ = [
        (31, 'unused'),
        (1, 'PRIMARY'),
    ]

class TS_MONITOR_DEF(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'left'),
        (pint.uint32_t, 'top'),
        (pint.uint32_t, 'right'),
        (pint.uint32_t, 'bottom'),
        (TS_MONITOR_, 'flags'),
    ]

@TS_UD.define
class TS_UD_CS_MONITOR(pstruct.type):
    type = 0xc005
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (pint.uint32_t, 'monitorCount'),
        (lambda self: dyn.array(TS_MONITOR_DEF, self['monitorCount'].li.int()), 'monitorDefArray'),
    ]

@TS_UD.define
class TS_UD_CS_MCS_MSGCHANNEL(pstruct.type):
    type = 0xc006
    _fields_ = [
        (pint.uint32_t, 'flags'),
    ]

@pbinary.littleendian
class TRANSPORTTYPE_(pbinary.flags):
    _fields_ = [
        (22, 'unused'),
        (1, 'TCP_TO_UDP'),
        (1, 'UDP_PREFERRED'),
        (5, 'RESERVED2'),
        (1, 'UDPFECL'),
        (1, 'RESERVED1'),
        (1, 'UDPFECR'),
    ]

@TS_UD.define
class TS_UD_CS_MULTITRANSPORT(pstruct.type):
    type = 0xc00a
    _fields_ = [
        (TRANSPORTTYPE_, 'flags'),
    ]

class TS_MONITOR_ATTRIBUTES(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'physicalWidth'),
        (pint.uint32_t, 'physicalHeight'),
        (pint.uint32_t, 'orientation'),
        (pint.uint32_t, 'desktopScaleFactor'),
        (pint.uint32_t, 'deviceScaleFactor'),
    ]

@TS_UD.define
class TS_UD_CS_MONITOR_EX(pstruct.type):
    type = 0xc008
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (pint.uint32_t, 'monitorAttributeSize'),
        (pint.uint32_t, 'monitorCount'),
        (lambda self: dyn.array(TS_MONITOR_ATTRIBUTES, self['monitorCount'].li.int()), 'monitorAttributesArray'),
    ]

@pbinary.littleendian
class RNS_UD_SC_(pbinary.flags):
    _fields_ = [
        (29, 'unused'),
        (1, 'EDGE_ACTIONS_SUPPORTED_V2'),
        (1, 'DYNAMIC_DST_SUPPORTED'),
        (1, 'EDGE_ACTIONS_SUPPORTED_V1'),
    ]

@TS_UD.define
class TS_UD_SC_CORE(pstruct.type):
    type = 0x0c01

    _fields_ = [
        (TS_VERSION, 'version'),
        (lambda self: pint.uint_t if self.blocksize() <= 4 else pint.uint32_t, 'clientRequestedProtocols'),
        (lambda self: pint.uint_t if self.blocksize() <= 8 else RNS_UD_SC_, 'earlyCapabilityFlags'),
    ]

@TS_UD.define
class TS_UD_SC_SEC1(pstruct.type):
    type = 0x0c02

    def __serverRandom(self):
        method, level = (self[fld].li for fld in ['encryptionMethod','encryptionLevel'])
        if method.int() == 0 and level.int() == 0:
            return ptype.undefined
        return dyn.clone(INTEGER, length=self['serverRandomLen'].li.int())

    def __serverCertificate(self):
        method, level = (self[fld].li for fld in ['encryptionMethod','encryptionLevel'])
        if method.int() == 0 and level.int() == 0:
            return ptype.undefined
        return dyn.clone(PROPRIETARYSERVERCERTIFICATE, blocksize=lambda self, length=self['serverCertLen'].li.int(): length)

    _fields_ = [
        (ENCRYPTION_METHOD_, 'encryptionMethod'),
        (ENCRYPTION_LEVEL_, 'encryptionLevel'),
        (pint.uint32_t, 'serverRandomLen'),
        (pint.uint32_t, 'serverCertLen'),
        (__serverRandom, 'serverRandom'),
        (__serverCertificate, 'serverCertificate'),
    ]

@TS_UD.define
class TS_UD_SC_NET(pstruct.type):
    type = 0x0c03

    _fields_ = [
        (pint.littleendian(gcc.ChannelId), 'MCSChannelId'),
        (pint.uint16_t, 'channelCount'),
        (lambda self: dyn.array(pint.littleendian(gcc.ChannelId), self['channelCount'].li.int()), 'channelIdArray'),
        (lambda self: dyn.block(4 - sum(self[fld].li.size() for fld in ['MCSChannelId','channelCount','channelIdArray']) % 4), 'Pad'),
    ]

@TS_UD.define
class TS_UD_SC_MCS_MSGCHANNEL(pstruct.type):
    type = 0x0c04
    _fields_ = [
        (pint.littleendian(gcc.ChannelId), 'MCSChannelId'),
    ]

@TS_UD.define
class TS_UD_SC_MULTITRANSPORT(pstruct.type):
    type = 0x0c08
    _fields_ = [
        (TRANSPORTTYPE_, 'flags'),
    ]

### security pdu headers
class TS_SECURITY_HEADER0(ber.INTEGER):
    length = 0
    def DataSignature(self):
        return self

class TS_SECURITY_HEADER1(pstruct.type):
    _fields_ = [
        (dyn.clone(ber.INTEGER, length=8), 'dataSignature'),
    ]
    def DataSignature(self):
        return self['dataSignature']
    def summary(self):
        dataSignature = self['dataSignature']
        return "dataSignature={:#x}".format(dataSignature.int())

class TSFIPS_VERSION(pint.enum, pint.uint8_t):
    _values_ = [
        ('VERSION1', 0x01),
    ]

class TS_SECURITY_HEADER2(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'length'),
        (TSFIPS_VERSION, 'version'),
        (pint.uint8_t, 'padlen'),
        (dyn.clone(ber.INTEGER, length=8), 'dataSignature'),
    ]
    def DataSignature(self):
        return self['dataSignature']

@pbinary.littleendian
class SEC_(pbinary.flags):
    _fields_ = [
        (16, 'flagsHi'),

        (1, 'FLAGSHI_VALID'),
        (1, 'HEARTBEAT'),
        (1, 'AUTODETECT_RSP'),
        (1, 'AUTODETECT_REQ'),
        (1, 'SECURE_CHECKSUM'),
        (1, 'REDIRECTION_PKT'),
        (1, 'LICENSE_ENCRYPT_SC'),
        (1, 'LICENSE_ENCRYPT_CS'),

        (1, 'LICENSE_PKT'),
        (1, 'INFO_PKT'),
        (1, 'IGNORE_SEQNO'),
        (1, 'RESET_SEQNO'),
        (1, 'ENCRYPT'),
        (1, 'TRANSPORT_RSP'),
        (1, 'TRANSPORT_REQ'),
        (1, 'EXCHANGE_PKT'),
    ]

class SharePDU(parray.block):
    '''
    Microsoft's implementation actually multiple T128 packets within each
    SecurePDU. This should be bounded by a blocksize since in most cases it'll be
    encrypted.
    '''
    _object_ = mas.SharePDU

class SecureBasePDU(pstruct.type):
    pass

class SecurePDU(SecureBasePDU):
    def __securityHeader(self):
        # First check to see if we're not supposed to be encrypted because if so
        # then we don't need a header or any of that shit.
        res = self['basicSecurityHeader'].li
        if not res['ENCRYPT']:
            return TS_SECURITY_HEADER0

        # Grab the encryption level that the user specified, defaulting to none
        # if it wasn't.
        level = getattr(self, 'encryptionLevel', 0)

        # Use the encryption level to determine security header
        res = level.int() if hasattr(level, 'int') else level
        if res == ENCRYPTION_LEVEL_.byname('NONE'):
            return TS_SECURITY_HEADER0
        elif res == ENCRYPTION_LEVEL_.byname('FIPS'):
            return TS_SECURITY_HEADER2
        return TS_SECURITY_HEADER1

    def __data(self):
        # Figure out our backing type
        res = sum(self[fld].li.size() for fld in ['basicSecurityHeader','securityHeader'])
        cb = max((0, self.blocksize() - res))
        backingType = dyn.block(cb)

        # If the user has provided a SecuredDataType attribute, then use that
        # otherwise we'll fall back to the RC4EncodedType which doesn't preserve
        # the RC4 state by default.
        et = getattr(self, 'SecuredDataType', RC4EncodedType)

        # Figure out which type is specified by our header, and return it
        # depending on whether or not the ENCRYPT flag is set in our header.
        res = self['basicSecurityHeader'].li

        # Standard TS_LICENSE_PDU
        if res['LICENSE_PKT']:
            return dyn.clone(et, _value_=backingType, _object_=TS_LICENSING_PDU) if res['ENCRYPT'] else TS_LICENSING_PDU

        # A TS_INFO_PACKET
        elif res['INFO_PKT']:
            return dyn.clone(et, _value_=backingType, _object_=TS_INFO_PACKET) if res['ENCRYPT'] else TS_INFO_PACKET

        # The TS_EXCHANGE_PACKET
        elif res['EXCHANGE_PKT']:
            return dyn.clone(et, _value_=backingType, _object_=TS_EXCHANGE_PACKET) if res['ENCRYPT'] else TS_EXCHANGE_PACKET

        # If it was none of the types specified in the header, and we're not
        # encrypted, then we have no idea what this is supposed to be. So in
        # that case we'll simply return the backingType and force the user to
        # cast it to whatever they need.
        elif not res['ENCRYPT']:
            return backingType

        # If it was encrypted, however, then we need to check to see if the
        # encryptedType has an ._object_ attribute, because if it doesn't then
        # we'll decrypt to a ptype.block so the user can still see what the
        # decrypted data looks like and the RC4 state can be cycled propery.

        return dyn.clone(et, _value_=backingType) if hasattr(et, '_object_') else dyn.clone(et, _value_=backingType, _object_=ptype.block)

    _fields_ = [
        (SEC_, 'basicSecurityHeader'),
        (__securityHeader, 'securityHeader'),
        (__data, 'securedData'),
    ]

    def DataSignature(self):
        return self['securityHeader'].DataSignature()

    def encryptedQ(self):
        return bool(self['basicSecurityHeader']['ENCRYPT'])

    def alloc(self, **fields):
        res = super(SecurePDU, self).alloc(**fields)

        # if we have an IOStream assigned to us, then we can calculate our MAC
        if hasattr(res, 'IOStream'):
            sdata = res['securedData']
            if isinstance(sdata, RC4EncodedType):
                data = sdata.d.li
            else:
                data = sdata

            # if we're initialized, then calculate the MAC signature
            if data.initializedQ():
                iostream = res.IOStream
                signature = iostream.MACSignature(data)
                res.DataSignature().set(signature.int())
            return res
        return res

### security exchange
class TS_SYSTEMTIME(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'wYear'),
        (pint.uint16_t, 'wMonth'),
        (pint.uint16_t, 'wDayOfWeek'),
        (pint.uint16_t, 'wDay'),
        (pint.uint16_t, 'wHour'),
        (pint.uint16_t, 'wMinute'),
        (pint.uint16_t, 'wSecond'),
        (pint.uint16_t, 'wMilliseconds'),
    ]

class TS_TIME_ZONE_INFORMATION(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Bias'),

        (dyn.clone(pstr.wstring, length=32), 'StandardName'),
        (TS_SYSTEMTIME, 'StandardDate'),
        (pint.uint32_t, 'StandardBias'),

        (dyn.clone(pstr.wstring, length=32), 'DaylightName'),
        (TS_SYSTEMTIME, 'DaylightDate'),
        (pint.uint32_t, 'DaylightBias'),
    ]

@pbinary.littleendian
class PERF_(pbinary.flags):
    _fields_ = [
        (1, 'RESERVED2'),
        (22, 'UNKNOWN'),
        (1, 'ENABLE_DESKTOP_COMPOSITION'),
        (1, 'ENABLE_FONT_SMOOTHING'),
        (1, 'DISABLE_CURSORSETTINGS'),
        (1, 'DISABLE_CURSOR_SHADOW'),
        (1, 'RESERVED1'),
        (1, 'DISABLE_THEMING'),
        (1, 'DISABLE_MENUANIMATIONS'),
        (1, 'DISABLE_FULLWINDOWDRAG'),
        (1, 'DISABLE_WALLPAPER'),
    ]

class TS_EXTENDED_INFO_PACKET(pstruct.type):
    class _clientAddressFamily(pint.enum, pint.uint16_t):
        _values_ = [
            ('AF_INET', 0x0002),
            ('AF_INET6', 0x0017),
        ]

    class _dynamicDaylightTimeDisabled(pint.enum, pint.uint16_t):
        _values_ = [
            ('FALSE', 0x0000),
            ('TRUE', 0x0001),
        ]

    def __mbstring(field):
        def mbstring(self):
            fld = self[field].li
            try:
                info = self.getparent(TS_INFO_PACKET)

            except ptypes.error.ItemNotFoundError:
                type, length = pstr.string, fld.int()
                return dyn.clone(type, length=length)

            flags = info['flags'].li
            type, length = (pstr.wstring, fld.int() // 2) if flags['UNICODE'] else (pstr.string, fld.int())
            return dyn.clone(type, length=length)
        return mbstring

    _fields_ = [
        (_clientAddressFamily, 'clientAddressFamily'),
        (pint.uint16_t, 'cbClientAddress'),
        (__mbstring('cbClientAddress'), 'clientAddress'),
        (pint.uint16_t, 'cbClientDir'),
        (__mbstring('cbClientDir'), 'clientDir'),
        (TS_TIME_ZONE_INFORMATION, 'clientTimeZone'),
        (pint.uint32_t, 'clientSessionId'),
        (PERF_, 'performanceFlags'),
        (pint.uint16_t, 'cbAutoReconnectCookie'),
        (lambda self: dyn.block(self['cbAutoReconnectCookie'].li.int()), 'autoReconnectCookie'),    # XXX: ARC_CS_PRIVATE_PACKET

        # XXX: the following fields are super conditional with regards to their existence
        #(pint.uint16_t, 'reserved1'),
        #(pint.uint16_t, 'reserved2'),
        #(pint.uint16_t, 'cbDynamicDSTTimeZoneKeyName'),
        #(lambda self: dyn.clone(pstr.wstring, length=self['cbDynamicDSTTimeZoneKeyName'].li.int()), 'dynamicDSTTimeZoneKeyName'),
        #(_dynamicDaylightTimeDisabled, 'dynamicDaylightTimeDisabled'),
    ]

@pbinary.littleendian
class INFO_(pbinary.flags):
    _fields_ = [
        (6, 'unused'),
        (1, 'HIDEF_RAIL_SUPPORTED'),
        (1, 'RESERVED2'),

        (1, 'RESERVED1'),
        (1, 'VIDEO_DISABLE'),
        (1, 'AUDIOCAPTURE'),
        (1, 'USING_SAVED_CREDS'),
        (1, 'NOAUDIOPLAYBACK'),
        (1, 'PASSWORD_IS_SC_PIN'),
        (1, 'MOUSE_HAS_WHEEL'),
        (1, 'LOGONERRORS'),

        (1, 'RAIL'),
        (1, 'FORCE_ENCRYPTED_CS_PDU'),
        (1, 'REMOTECONSOLEAUDIO'),
        (mas.PACKET_COMPR_, 'CompressionTypeMask'),
        (1, 'ENABLE_WINDOWS_KEY'),

        (1, 'COMPRESSION'),
        (1, 'LOGONNOTIFY'),
        (1, 'MAXIMIZESHELL'),
        (1, 'UNICODE'),
        (1, 'AUTOLOGON'),
        (1, 'RESERVED'),
        (1, 'DISABLECTRLALTDEL'),
        (1, 'MOUSE'),
    ]

class TS_EXCHANGE_PACKET(pstruct.type):
    def __encryptedClientRandom(self):
        res = self['length'].li.int()
        return dyn.clone(RSAPaddedInteger, blocksize=lambda self, cb=self['length'].li.int(): cb)

    _fields_ = [
        (pint.uint32_t, 'length'),
        (__encryptedClientRandom, 'encryptedClientRandom'),
    ]

    def alloc(self, **fields):
        res = super(TS_EXCHANGE_PACKET, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=res['encryptedClientRandom'].size())

class TS_INFO_PACKET(pstruct.type):
    def __mbstring(field):
        def mbstring(self):
            fld, flags = self[field].li, self['flags'].li

            type, length = (pstr.wstring, fld.int() // 2) if flags['UNICODE'] else (pstr.string, fld.int())
            return dyn.clone(type, length=length + 1)
        return mbstring

    _fields_ = [
        (pint.uint32_t, 'CodePage'),
        (INFO_, 'flags'),
        (pint.uint16_t, 'cbDomain'),
        (pint.uint16_t, 'cbUserName'),
        (pint.uint16_t, 'cbPassword'),
        (pint.uint16_t, 'cbAlternateShell'),
        (pint.uint16_t, 'cbWorkingDir'),
        (__mbstring('cbDomain'), 'Domain'),
        (__mbstring('cbUserName'), 'UserName'),
        (__mbstring('cbPassword'), 'Password'),
        (__mbstring('cbAlternateShell'), 'AlternateShell'),
        (__mbstring('cbWorkingDir'), 'WorkingDir'),
        (TS_EXTENDED_INFO_PACKET, 'extraInfo'),
    ]

### Terminal services cryptography
class SIGNATURE_ALG_(pint.enum, pint.uint32_t):
    _values_ = [
        ('SIGNATURE_ALG_RSA', 0x00000001)
    ]

class KEY_EXCHANGE_ALG_(pint.enum, pint.uint32_t):
    _values_ = [
        ('KEY_EXCHANGE_ALG_RSA', 0x00000001)
    ]

class BB_KEY_BLOB_(pint.enum, pint.uint16_t):
    _values_ = [
        ('BB_RSA_KEY_BLOB', 0x0006)
    ]

class BB_SIGNATURE_BLOB_(pint.enum, pint.uint16_t):
    _values_ = [
        ('BB_RSA_SIGNATURE_BLOB', 0x0008)
    ]

class RSAPaddedInteger(pstruct.type):
    def __integer(self):
        # First check if our blocksize was initialized because we can
        # simply use that to calculate the size of our integer since
        # the spec requires 8 bytes of padding
        try:
            res = self.blocksize()

        # Otherwise, we just need to hardcode the length to
        # 64 + 8 (padding) according to the specification.
        except ptypes.error.InitializationError:
            res = 64 + 8

        return dyn.clone(INTEGER, length=max((0, res - 8)))

    _fields_ = [
        (__integer, 'integer'),
        (dyn.block(8), 'padding'),
    ]

    def int(self):
        return self['integer'].int()

    def summary(self):
        nsize, psize = self['integer'].size(), self['padding'].size()
        nvalue, pvalue = self['integer'].int(), self['padding'].cast(INTEGER, length=psize).int()
        return "({:d}{:s}) {:0{:d}X}".format(8 * nsize, "+{:d}".format(8 * psize) if psize else '', nvalue * 0x100**psize + pvalue, 2 * (nsize + psize))

    def set(self, *pkrsa, **fields):
        if pkrsa:
            rsa, = pkrsa

            # unpack our integer that we're going to copy the size from
            M, e, n = (n.int() if isinstance(n, pint.type) else n for n in rsa)
            _, _, pkmod = rsa

            # encrypt our integer with the rsa parameters we received
            c = pow(M, e, n)
            keylen = math.ceil(math.log(c) / math.log(0x100))

            # figure out what instance we're going to assign our encrypted integer to
            res = fields.setdefault('integer', INTEGER(length=pkmod.size() if isinstance(pkmod, pint.type) else math.trunc(keylen)))

            # assign our integer and we're done
            res.set(c)
            return super(RSAPaddedInteger, self).set(**fields)
        return super(RSAPaddedInteger, self).set(**fields)

class RSA_PUBLIC_KEY(pstruct.type):
    class _magic(pint.uint32_t):
        def default(self):
            return self.set(0x31415352)
        def valid(self):
            return self.copy().default().int() == self.int()
        def properties(self):
            res = super(RSA_PUBLIC_KEY._magic, self).properties()
            res['valid'] = self.valid()
            return res

    def valid(self):
        if self.initializedQ():
            keylen, bitlen, datalen = (self[fld].int() for fld in ['keylen','bitlen','datalen'])
            return 8 * (datalen + 1) == bitlen and self['magic'].valid()
        return False

    def properties(self):
        res = super(RSA_PUBLIC_KEY, self).properties()
        res['valid'] = self.valid()
        return res

    class _modulus(RSAPaddedInteger):
        def __modulus(self):
            res = self.getparent(RSA_PUBLIC_KEY)
            return dyn.clone(INTEGER, length=res['datalen'].li.int() + 1)

        def __padding(self):
            res = self.getparent(RSA_PUBLIC_KEY)
            return dyn.block(max((0, res['keylen'].li.int() - self['integer'].li.size())))

        _fields_ = [
            (__modulus, 'integer'),
            (__padding, 'padding'),
        ]

    _fields_ = [
        (_magic, 'magic'),
        (pint.uint32_t, 'keylen'),
        (pint.uint32_t, 'bitlen'),
        (pint.uint32_t, 'datalen'),
        (pint.uint32_t, 'pubExp'),
        (_modulus, 'modulus'),
    ]

class PROPRIETARYSERVERCERTIFICATE(pstruct.type):
    class _dwVersion(pint.enum, pint.uint32_t):
        _values_ = [('CERT_CHAIN_VERSION_1', 0x00000001)]

    def __PublicKeyBlob(self):
        res = self['wPublicKeyBlobLen'].li.int()
        return dyn.clone(RSA_PUBLIC_KEY, blocksize=lambda self, cb=res: cb)

    class _SignatureBlob(pstruct.type):
        def __modulus(self):
            res = self.getparent(PROPRIETARYSERVERCERTIFICATE)
            return dyn.clone(ber.INTEGER, length=max((0, res['wSignatureBlobLen'].li.int() - 8)))

        def __padding(self):
            res = self.getparent(PROPRIETARYSERVERCERTIFICATE)
            return dyn.block(max((0, res['wSignatureBlobLen'].li.int() - self['integer'].li.size())))

        _fields_ = [
            (__modulus, 'integer'),
            (__padding, 'padding'),
        ]

        def int(self):
            return self['integer'].int()

        def summary(self):
            res = self.serialize().encode('hex').upper()
            return "({:d}{:s}) {:s}".format(self['integer'].size() * 8, "+{:d}".format(self['padding'].size() * 8) if self['padding'].size() else '', res)

    _fields_ = [
        (_dwVersion, 'dwVersion'),
        (SIGNATURE_ALG_, 'dwSigAlgId'),
        (KEY_EXCHANGE_ALG_, 'dwKeyAlgId'),
        (BB_KEY_BLOB_, 'wPublicKeyBlobType'),
        (pint.uint16_t, 'wPublicKeyBlobLen'),
        (__PublicKeyBlob, 'PublicKeyBlob'),
        (BB_SIGNATURE_BLOB_, 'wSignatureBlobType'),
        (pint.uint16_t, 'wSignatureBlobLen'),
        (_SignatureBlob, 'SignatureBlob'),
        #(lambda self: dyn.block(self['wSignatureBlobLen'].li.int()), 'SignatureBlob'),
    ]

class SERVER_CERTIFICATE(pstruct.type):
    class _dwVersion(pbinary.struct):
        class _t(pbinary.enum):
            width, _values_ = 1, [
                ('permanent', 0),
                ('temporary', 1),
            ]
        _fields_ = [
            (31, 'certChainVersion'),
            (1, 't'),
        ]
    _fields_ = [
        (_dwVersion, 'dwVersion'),
        (ptype.undefined, 'certData'),
    ]

### Licensing
class PREAMBLE_VERSION(pbinary.enum):
    width, _values_ = 4, [
        ('VERSION_2_0', 0x2),
        ('VERSION_3_0', 0x3),
    ]

class LicensingMessageType(ptype.definition):
    cache = {}

class LICENSE_MESSAGE(pint.enum, pint.uint8_t):
    _values_ = [
        ('LICENSE_REQUEST', 0x01),
        ('PLATFORM_CHALLENGE', 0x02),
        ('NEW_LICENSE', 0x03),
        ('UPGRADE_LICENSE', 0x04),
        ('LICENSE_INFO', 0x12),
        ('NEW_LICENSE_REQUEST', 0x13),
        ('PLATFORM_CHALLENGE_RESPONSE', 0x15),
        ('ERROR_ALERT', 0xff),
    ]

class LICENSE_PREAMBLE(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'EXTENDED_ERROR_MSG_SUPPORTED'),
            (3, 'unused'),
            (PREAMBLE_VERSION, 'LicenseProtocolVersionMask'),
        ]
    _fields_ = [
        (LICENSE_MESSAGE, 'bMsgType'),
        (_flags, 'flags'),
        (pint.uint16_t, 'wMsgSize'),
    ]

class BB_(pint.enum, pint.uint16_t):
    _values_ = [
        ('DATA_BLOB', 0x0001),
        ('RANDOM_BLOB', 0x0002),
        ('CERTIFICATE_BLOB', 0x0003),
        ('ERROR_BLOB', 0x0004),
        ('ENCRYPTED_DATA_BLOB', 0x0009),
        ('KEY_EXCHG_ALG_BLOB', 0x000d),
        ('SCOPE_BLOB', 0x000e),
        ('CLIENT_USER_NAME_BLOB', 0x000f),
        ('CLIENT_MACHINE_NAME_BLOB', 0x0010),
    ]

class LICENSE_BINARY_BLOB(pstruct.type):
    _fields_ = [
        (BB_, 'wBlobType'),
        (pint.uint16_t, 'wBlobLen'),
        (lambda self: dyn.block(self['wBlobLen'].li.int()), 'blobData'),
    ]

class ERR_(pint.enum, pint.uint32_t):
    _values_ = [
        ('INVALID_SERVER_CERTIFICATE', 0x00000001),
        ('NO_LICENSE', 0x00000002),
        ('INVALID_MAC', 0x00000003),
        ('INVALID_SCOPE', 0x00000004),
        ('NO_LICENSE_SERVER', 0x00000006),
        ('VALID_CLIENT', 0x00000007),
        ('INVALID_CLIENT', 0x00000008),
        ('INVALID_PRODUCTID', 0x0000000b),
        ('INVALID_MESSAGE_LEN', 0x0000000c),
    ]

class ST_(pint.enum, pint.uint32_t):
    _values_ = [
        ('TOTAL_ABORT', 0x00000001),
        ('NO_TRANSITION', 0x00000002),
        ('RESET_PHASE_TO_START', 0x00000003),
        ('RESEND_LAST_MESSAGE', 0x00000004),
    ]

@LicensingMessageType.define
class LICENSE_ERROR_MESSAGE(pstruct.type):
    type = 0xff
    _fields_ = [
        (ERR_, 'dwErrorCode'),
        (ST_, 'dwStateTransition'),
        (LICENSE_BINARY_BLOB, 'bbErrorInfo'),
    ]

class TS_LICENSING_PDU(pstruct.type):
    def __licensingMessage(self):
        res = self['preamble'].li
        if res['bMsgType']['ERROR_ALERT']:
            return LICENSE_ERROR_MESSAGE

        logging.fatal("License type {:s} is unimplemented".format(res['bMsgType']))
        cb = res['wMsgSize'].li
        return dyn.block(cb.int() - res.size())

    _fields_ = [
        (LICENSE_PREAMBLE, 'preamble'),
        (__licensingMessage, 'licensingMessage'),
    ]

class PRODUCT_INFO(pstruct.type):
    _fields_ = [
        (TS_VERSION, 'dwVersion'),
        (pint.uint32_t, 'cbCompanyName'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cbCompanyName'].li.int()), 'pbCompanyName'),
        (pint.uint32_t, 'cbProductId'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cbProductId'].li.int()), 'pbProductId'),
    ]

class SCOPE(LICENSE_BINARY_BLOB):
    pass

class SCOPE_LIST(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'ScopeCount'),
        (lambda self: dyn.array(SCOPE, self['ScopeCount'].li.int()), 'ScopeList'),
    ]

@LicensingMessageType.define
class SERVER_LICENSE_REQUEST(pstruct.type):
    type = 0x01
    _fields_ = [
        (dyn.clone(pint.uint_t, length=32), 'ServerRandom'),
        (PRODUCT_INFO, 'ProductInfo'),
        (LICENSE_BINARY_BLOB, 'KeyExchangeList'),
        (LICENSE_BINARY_BLOB, 'ServerCertificate'),
        (SCOPE_LIST, 'ScopeList'),
    ]

@LicensingMessageType.define
class CLIENT_NEW_LICENSE_REQUEST(pstruct.type):
    type = 0x13
    _fields_ = [
        (KEY_EXCHANGE_ALG_, 'PreferredKeyExchangeAlg'),
        (pint.uint32_t, 'PlatformId'),
        (dyn.clone(pint.uint_t, length=32), 'ClientRandom'),
        (LICENSE_BINARY_BLOB, 'EncryptedPreMasterSecret'),
        (LICENSE_BINARY_BLOB, 'ClientUserName'),
        (LICENSE_BINARY_BLOB, 'ClientMachineName'),
    ]

@LicensingMessageType.define
class CLIENT_LICENSE_INFO(pstruct.type):
    type = 0x12
    _fields_ = [
        (KEY_EXCHANGE_ALG_, 'PreferredKeyExchangeAlg'),
        (pint.uint32_t, 'PlatformId'),
        (dyn.clone(pint.uint_t, length=32), 'ClientRandom'),
        (LICENSE_BINARY_BLOB, 'EncryptedPreMasterSecret'),
        (LICENSE_BINARY_BLOB, 'LicenseInfo'),
        (LICENSE_BINARY_BLOB, 'EncryptedHWID'),
        (dyn.clone(pint.uint_t, length=16), 'MACData'),
    ]

class CLIENT_HARDWARE_ID(pstruct.type):
    # FIXME: This is a LICENSE_BINARY_BLOB type
    _fields_ = [
        (pint.uint32_t, 'PlatformId'),
        (pint.uint32_t, 'Data1'),
        (pint.uint32_t, 'Data2'),
        (pint.uint32_t, 'Data3'),
        (pint.uint32_t, 'Data4'),
    ]

@LicensingMessageType.define
class SERVER_PLATFORM_CHALLENGE(pstruct.type):
    type = 0x02
    _fields_ = [
        (pint.uint32_t, 'ConnectFlags'),
        (LICENSE_BINARY_BLOB, 'EncryptedPlatformChallenge'),
        (dyn.clone(pint.uint_t, length=16), 'MACData'),
    ]

@LicensingMessageType.define
class CLIENT_PLATFORM_CHALLENGE_RESPONSE(pstruct.type):
    type = 0x15
    _fields_ = [
        (LICENSE_BINARY_BLOB, 'EncryptedPlatformChallengeResponse'),
        (LICENSE_BINARY_BLOB, 'EncryptedHWID'),
        (dyn.clone(pint.uint_t, length=16), 'MACData'),
    ]

@LicensingMessageType.define
class SERVER_UPGRADE_LICENSE(pstruct.type):
    type = 0x04
    _fields_ = [
        (LICENSE_BINARY_BLOB, 'EncryptedLicenseInfo'),
        (dyn.clone(pint.uint_t, length=16), 'MACData'),
    ]

class NEW_LICENSE_INFO(pstruct.type):
    # FIXME: This is a LICENSE_BINARY_BLOB type
    _fields_ = [
        (TS_VERSION, 'dwVersion'),
        (pint.uint32_t, 'cbScope'),
        (lambda self: dyn.clone(pstr.string, length=self['cbScope'].li.int()), 'pbScope'),
        (pint.uint32_t, 'cbCompanyName'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cbCompanyName'].li.int()), 'pbCompanyName'),
        (pint.uint32_t, 'cbProductId'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cbProductId'].li.int()), 'pbProductId'),
        (pint.uint32_t, 'cbLicenseInfo'),
        (lambda self: dyn.block(self['cbLicenseInfo'].li.int()), 'pbLicenseInfo'),
    ]

@LicensingMessageType.define
class SERVER_NEW_LICENSE(pstruct.type):
    type = 0x03
    _fields_ = [
        (LICENSE_BINARY_BLOB, 'EncryptedNewLicenseInfo'),
        (dyn.clone(pint.uint_t, length=16), 'MACData'),
    ]

### T.128 extensions (CapabilitySetType)
@pbinary.littleendian
class SOUND_(pbinary.flags):
    _fields_ = [
        (15, 'unused'),
        (1, 'BEEPS_FLAG'),
    ]

@CapabilitySetType.define
class SoundCapabilitySet(pstruct.type):
    type = 12
    _fields_ = [
        (SOUND_, 'soundFlags'),
        (Integer16, 'pad2octetsA'),
    ]

@pbinary.littleendian
class INPUT_FLAG_(pbinary.flags):
    _fields_ = [
        (6, 'UNUSED3'),
        (1, 'QOE_TIMESTAMPS'),
        (1, 'MOUSE_HWHEEL'),
        (1, 'UNUSED2'),
        (1, 'UNUSED1'),
        (1, 'FASTPATH_INPUT2'),
        (1, 'UNICODE'),
        (1, 'FASTPATH_INPUT'),
        (1, 'MOUSEX'),
        (1, 'RESERVED'),
        (1, 'SCANCODES'),
    ]

@CapabilitySetType.define
class InputCapabilitySet(pstruct.type):
    type = 13
    _fields_ = [
        (INPUT_FLAG_, 'inputFlags'),
        (Integer16, 'pad2octetsA'),
        (Integer32, 'keyboardLayout'),
        (Integer32, 'keyboardType'),
        (Integer32, 'keyboardSubType'),
        (Integer32, 'keyboardFunctionKey'),
        (dyn.clone(pstr.string, length=64), 'imeFileName'),
    ]

@pbinary.littleendian
class FONTSUPPORT_(pbinary.flags):
    _fields_ = [
        (15, 'unused'),
        (1, 'FONTLIST'),
    ]

@CapabilitySetType.define
class FontCapabilitySet(pstruct.type):
    type = 14
    _fields_ = [
        (FONTSUPPORT_, 'fontSupportFlags'),
        (Integer16, 'pad2octets'),
    ]

class BRUSH_(pint.enum, Integer32):
    _values_ = [
        ('DEFAULT', 0x00000000),
        ('COLOR_8x8', 0x00000001),
        ('COLOR_FULL', 0x00000002),
    ]

@CapabilitySetType.define
class BrushCapabilitySet(pstruct.type):
    type = 15
    _fields_ = [
        (BRUSH_, 'brushSupportLevel'),
    ]

class TS_CACHE_DEFINITION(pstruct.type):
    _fields_ = [
        (Integer16, 'CacheEntries'),
        (Integer16, 'CacheMaximumCellSize'),
    ]

class GLYPH_SUPPORT_(pint.enum, Integer16):
    _values_ = [
        ('NONE', 0x0000),
        ('PARTIAL', 0x0001),
        ('FULL', 0x0002),
        ('ENCODE', 0x0003),
    ]

@CapabilitySetType.define
class GlyphCacheCapabilitySet(pstruct.type):
    type = 16
    _fields_ = [
        (dyn.array(TS_CACHE_DEFINITION, 10), 'GlyphCache'),
        (Integer32, 'FragCache'),
        (GLYPH_SUPPORT_, 'GlyphSupportLevel'),
        (Integer16, 'pad2octets'),
    ]

@CapabilitySetType.define
class OffscreenCapabilitySet(pstruct.type):
    type = 17
    class _offscreenSupportLevel(pint.enum, Integer32):
        _values_ = [
            ('FALSE', 0x00000000),
            ('TRUE', 0x00000001),
        ]

    _fields_ = [
        (_offscreenSupportLevel, 'offscreenSupportLevel'),
        (Integer16, 'offscreenCacheSize'),
        (Integer16, 'offscreenCacheEntries'),
    ]

class BITMAP_CACHE_(pint.enum, Integer8):
    _values_ = [
        ('V2', 0x01),
    ]

@CapabilitySetType.define
class BitmapCacheHostSupportCapabilitySet(pstruct.type):
    type = 18
    _fields_ = [
        (BITMAP_CACHE_, 'cacheVersion'),
        (Integer8, 'pad1'),
        (Integer16, 'pad2'),
    ]

@pbinary.littleendian
class TS_BITMAPCACHE_CELL_CACHE_INFO(pbinary.struct):
    _fields_ = [
        (1, 'k'),
        (31, 'NumEntries'),
    ]

@CapabilitySetType.define
class BitmapCacheCapabilitySetRevision2(pstruct.type):
    type = 19
    @pbinary.littleendian
    class _CacheFlags(pbinary.flags):
        _fields_ = [
            (14, 'unused'),
            (1, 'ALLOW_CACHE_WAITING_LIST_FLAG'),
            (1, 'PERSISTENT_KEYS_EXPECTED_FLAG'),
        ]

    class _CellInfo(parray.type):
        _object_ = TS_BITMAPCACHE_CELL_CACHE_INFO
        length = 5

    _fields_ = [
        (_CacheFlags, 'CacheFlags'),
        (Integer8, 'pad2'),
        (Integer8, 'NumCellCaches'),
        (_CellInfo, 'CellInfo'),
        (dyn.block(12), 'Pad3'),
    ]

class VCCAPS_(pint.enum, Integer32):
    _values_ = [
        ('NO_COMPR', 0),
        ('COMPR_SC', 1),
        ('COMPR_CS_8K', 2),
    ]

@CapabilitySetType.define
class VirtualChannelCapabilitySet(pstruct.type):
    type = 20
    _fields_ = [
        (VCCAPS_, 'flags'),
        (Integer32, 'VCChunkSize'),
    ]

class DRAW_NINEGRID_(pint.enum, Integer32):
    _values_ = [
        ('NO_SUPPORT', 0x00000000),
        ('SUPPORTED', 0x00000001),
        ('SUPPORTED_REV2', 0x00000000),
    ]

@CapabilitySetType.define
class DrawNineGridCapabilitySet(pstruct.type):
    type = 21
    _fields_ = [
        (DRAW_NINEGRID_, 'drawNineGridSupportLevel'),
        (Integer16, 'drawNineGridCacheSize'),
        (Integer16, 'drawNineGridCacheEntries'),
    ]

class TS_DRAW_GDIPLUS_(pint.enum, Integer32):
    _values_ = [
        ('DEFAULT', 0x00000000),
        ('SUPPORTED', 0x00000001),
    ]

class TS_DRAW_GDIPLUS_CACHE_LEVEL_(pint.enum, Integer32):
    _values_ = [
        ('DEFAULT', 0x00000000),
        ('ONE', 0x00000001),
    ]

class TS_GDIPLUS_CACHE_ENTRIES(pstruct.type):
    _fields_ = [
        (Integer16, 'GdipGraphicsCacheEntries'),
        (Integer16, 'GdipBrushCacheEntries'),
        (Integer16, 'GdipPenCacheEntries'),
        (Integer16, 'GdipImageCacheEntries'),
        (Integer16, 'GdipImageAttributesCacheEntries'),
    ]

class TS_GDIPLUS_CACHE_CHUNK_SIZE(pstruct.type):
    _fields_ = [
        (Integer16, 'GdipGraphicsCacheChunkSize'),
        (Integer16, 'GdipObjectBrushCacheChunkSize'),
        (Integer16, 'GdipObjectPenCacheChunkSize'),
        (Integer16, 'GdipObjectImageAttributesCacheChunkSize'),
    ]

class TS_GDIPLUS_IMAGE_CACHE_PROPERTIES(pstruct.type):
    _fields_ = [
        (Integer16, 'GdipObjectImageCacheChunkSize'),
        (Integer16, 'GdipObjectImageCacheTotalSize'),
        (Integer16, 'GdipObjectImageCacheMaxSize'),
    ]

@CapabilitySetType.define
class DrawGDIPlusCapabilitySet(pstruct.type):
    type = 22
    _fields_ = [
        (TS_DRAW_GDIPLUS_, 'drawGDIPlusSupportLevel'),
        (Integer32, 'GdipVersion'),
        (TS_DRAW_GDIPLUS_CACHE_LEVEL_, 'drawGdiplusCacheLevel'),
        (TS_GDIPLUS_CACHE_ENTRIES, 'GdipCacheEntries'),
        (TS_GDIPLUS_CACHE_CHUNK_SIZE, 'GdipCacheChunkSize'),
        (TS_GDIPLUS_IMAGE_CACHE_PROPERTIES, 'GdipImageCacheProperties'),
    ]

@pbinary.littleendian
class RAIL_LEVEL_(pbinary.flags):
    _fields_ = [
        (24, 'unused'),
        (1, 'HANDSHAKE_EX_SUPPORTED'),
        (1, 'WINDOW_CLOAKING_SUPPORTED'),
        (1, 'HIDE_MINIMIZED_APPS_SUPPORTED'),
        (1, 'SERVER_TO_CLIENT_IME_SYNC_SUPPORTED'),
        (1, 'LANGUAGE_IME_SYNC_SUPPORTED'),
        (1, 'SHELL_INTEGRATION_SUPPORTED'),
        (1, 'DOCKED_LANGBAR_SUPPORTED'),
        (1, 'SUPPORTED'),
    ]

@CapabilitySetType.define
class RailCapabilitySet(pstruct.type):
    type = 23
    _fields_ = [
        (RAIL_LEVEL_, 'railSupportLevel'),
    ]

class WINDOW_LEVEL_(pint.enum, Integer32):
    _values_ = [
        ('NOT_SUPPORTED', 0x00000000),
        ('SUPPORTED', 0x00000001),
        ('SUPPORTED_EX', 0x00000002),
    ]

@CapabilitySetType.define
class WindowCapabilitySet(pstruct.type):
    type = 24
    _fields_ = [
        (WINDOW_LEVEL_, 'wndSupportLevel'),
        (Integer8, 'numIconCaches'),
        (Integer16, 'numIconCacheEntries'),
    ]

class COMPDESK_(pint.enum, Integer16):
    _values_ = [
        ('NOT_SUPPORTED', 0x0000),
        ('SUPPORTED', 0x0001),
    ]

@CapabilitySetType.define
class DesktopCompositionCapabilitySet(pstruct.type):
    type = 25
    _fields_ = [
        (COMPDESK_, 'CompDeskSupportLevel'),
    ]

@CapabilitySetType.define
class MultipleFragmentUpdateCapabilitySet(pstruct.type):
    type = 26
    _fields_ = [
        (Integer32, 'MaxRequestSize'),
    ]

@pbinary.littleendian
class LargePointerSupportFlags(pbinary.flags):
    _fields_ = [
        (15, 'unused'),
        (1, 'LARGE_POINTER_FLAG_96x96'),
    ]

@CapabilitySetType.define
class LargePointerCapabilitySet(pstruct.type):
    type = 27
    _fields_ = [
        (LargePointerSupportFlags, 'largePointerSupportFlags'),
    ]

@pbinary.littleendian
class SURFCMDS_(pbinary.flags):
    _fields_ = [
        (25, 'unused'),
        (1, 'STREAMSURFACEBITS'),
        (1, 'RESERVED'),
        (1, 'FRAMEMARKER'),
        (2, 'unused2'),
        (1, 'SETSURFACEBITS'),
        (1, 'unused3'),
    ]

@CapabilitySetType.define
class SurfaceCommandsCapabilitySet(pstruct.type):
    type = 28
    _fields_ = [
        (SURFCMDS_, 'cmdFlags'),
        (Integer32, 'reserved'),
    ]

class TS_CODEC_PROPERTIES(ptype.definition):
    cache = {}

class TS_BITMAPCODEC(pstruct.type):
    def __codecProperties(self):
        res, length = self['codecGUID'].li, self['codecPropertiesLength'].li
        return TS_CODEC_PROPERTIES.get(res.get(), blocksize=lambda self, cb=length.int(): cb)

    _fields_ = [
        (GUID, 'codecGUID'),
        (Integer8, 'codecID'),
        (Integer16, 'codecPropertiesLength'),
        (__codecProperties, 'codecProperties'),
    ]

@CapabilitySetType.define
class BitmapCodecsCapabilitySet(pstruct.type):
    type = 29
    _fields_ = [
        (Integer8, 'bitmapCodecCount'),
        (lambda self: dyn.array(TS_BITMAPCODEC, self['bitmapCodecCount'].li.int()), 'bitmapCodecArray'),
    ]

## ts codec properties
@TS_CODEC_PROPERTIES.define
class TS_NSCODEC_CAPABILITYSET(pstruct.type):
    type = (0xca8d1bb9, 0x000f, 0x154f, 0x589fae2d1a87e2d6)
    _fields_ = [
        (Boolean8, 'fAllowDynamicFidelity'),
        (Boolean8, 'fAllowSubSampling'),
        (Integer8, 'colorLossLevel'), #MS-RDPEGDI
    ]

@TS_CODEC_PROPERTIES.define
class TS_RFX_SRVR_CAPS_CONTAINER(pstruct.type):
    type = (0x76772f12, 0xbd72, 0x4463, 0xafb3b73c9c6f7886)
    def __reserved(self):
        try:
            res = self.blocksize()
        except ptypes.error.InitializationError:
            res = 0
        return dyn.block(res)

    _fields_ = [
        (__reserved, 'reserved'),
    ]

@pbinary.littleendian
class CARDP_CAPS_(pbinary.flags):
    _fields_ = [
        (31, 'unused'),
        (1, 'CAPTURE_NON_CAC'),
    ]

@TS_CODEC_PROPERTIES.define
class TS_RFX_CLNT_CAPS_CONTAINER(pstruct.type):
    type = (0x2744ccd4, 0x9d8a, 0x4e74, 0x803c0ecbeea19c54)
    class _captureData(pstruct.type):
        _fields_ = [
            (CARDP_CAPS_, 'captureFlags'),
            (Integer32, 'capsLength'),
            (lambda self: dyn.block(self['capsLength'].li.int()), 'capsData'),
        ]

    _fields_ = [
        (Integer32, 'length'),
        (lambda self: dyn.block(self['length'].li.int()), 'captureData'),
    ]

    def alloc(self, **fields):
        res = super(TS_RFX_CLNT_CAPS_CONTAINER, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=res['captureData'].size())

@TS_CODEC_PROPERTIES.define
class TS_IGNORECODEC_CAPABILITYSET(pstruct.type):
    type = (0x9c4351a6, 0x3535, 0x42ae, 0x910ccdfce5760b58)
    def __reserved(self):
        try:
            res = self.blocksize()
        except ptypes.error.InitializationError:
            res = 0
        return dyn.block(res)

    _fields_ = [
        (__reserved, 'reserved'),
    ]

@CapabilitySetType.define
class FrameAcknowledgementCapabilitySet(pstruct.type):
    type = 30
    _fields_ = [
        (Integer32, 'frameAcknowledge'),
    ]

### T.128 extensions (PDUType2)
@PDUType2.define
class ShutdownRequestPDU(ptype.undefined):
    type = 0x24

@PDUType2.define
class ShutdownDeniedPDU(ptype.undefined):
    type = 0x25

class INFOTYPE_(pint.enum, pint.uint32_t):
    _values_ = [
        ('LOGON', 0x00000000),
        ('LOGON_LONG', 0x00000001),
        ('LOGON_PLAINNOTIFY', 0x00000002),
        ('LOGON_EXTENDED_INFO', 0x00000003),
    ]

class SessionInfoPduType(ptype.definition):
    cache = {}

@SessionInfoPduType.define
class TS_LOGON_INFO(pstruct.type):
    type = 0
    _fields_ = [
        (pint.uint32_t, 'cbDomain'),
        (dyn.clone(pstr.wstring, length=26), 'Domain'),
        (pint.uint32_t, 'cbUserName'),
        (dyn.clone(pstr.wstring, length=256), 'UserName'),
        (pint.uint32_t, 'SessionId'),
    ]

@SessionInfoPduType.define
class TS_LOGON_INFO_VERSION2(pstruct.type):
    type = 1
    def __extraPadding(self):
        cb = sum(self[fld].li.size() for fld in ['Version','Size','SessionId','cbDomain','cbUserName','Pad'])
        res = self['Size'].li.int()
        return dyn.block(max((0, res - cb)))

    _fields_ = [
        (pint.uint16_t, 'Version'),
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'SessionId'),
        (pint.uint32_t, 'cbDomain'),
        (pint.uint32_t, 'cbUserName'),
        (dyn.block(558), 'Pad'),
        (__extraPadding, 'extraPadding'),
        (lambda self: dyn.block(self['cbDomain'].li.int()), 'Domain'),
        (lambda self: dyn.block(self['cbUserName'].li.int()), 'UserName'),
    ]

@SessionInfoPduType.define
class TS_PLAIN_NOTIFY(pstruct.type):
    type = 2
    _fields_ = [
        (dyn.block(576), 'Pad'),
    ]

@pbinary.littleendian
class LOGON_EX_(pbinary.flags):
    _fields_ = [
        (30, 'unused'),
        (1, 'LOGONERRORS'),
        (1, 'AUTORECONNECTCOOKIE'),
    ]

    def iterate(self):
        yield 'LOGONERRORS', TS_LOGON_ERRORS_INFO
        yield 'AUTORECONNECTCOOKIE', None   # FIXME: this isn't implemented

class LOGON_MSG_(pint.enum, pint.uint32_t):
    _values_ = [
        ('DISCONNECT_REFUSED', 0xFFFFFFF9),
        ('NO_PERMISSION', 0xFFFFFFFA),
        ('BUMP_OPTIONS', 0xFFFFFFFB),
        ('RECONNECT_OPTIONS', 0xFFFFFFFC),
        ('SESSION_TERMINATE', 0xFFFFFFFD),
        ('SESSION_CONTINUE', 0xFFFFFFFE),

    ]

class LOGON_(pint.enum, pint.uint32_t):
    _values_ = [
        ('BAD_PASSWORD', 0),
        ('UPDATE_PASSWORD', 1),
        ('OTHER', 2),
        ('WARNING', 3),
    ]

class TS_LOGON_ERRORS_INFO(pstruct.type):
    _fields_ = [
        (LOGON_MSG_, 'ErrorNotificationType'),
        (LOGON_, 'ErrorNotificationData'),
    ]

class TS_LOGON_INFO_FIELD(pstruct.type):
    def __FieldData(self):
        res = self['cbFieldData'].li
        return self._object_ if hasattr(self, '_object_') else dyn.block(res.int())

    _fields_ = [
        (pint.uint32_t, 'cbFieldData'),
        (__FieldData, 'FieldData'),
    ]

class LogonFields(parray.terminated):
    _object_ = TS_LOGON_INFO_FIELD
    def _object_(self):
        if hasattr(self, '__FieldsPresent__'):
            res = self.__FieldsPresent__

            # Grab only types where FieldsPresent is defined.
            items = (t for fld, t in res.iterate() if res[fld])

            # Determine which type FieldsPresent claims this should be by checking
            # how many TS_LOGON_INFO_FIELD instances we've already decoded.
            count = 1 + len(self.value)
            while count > 0:
                t = next(items, None)
                count -= 1

            # Return our TS_LOGON_INFO_FIELD pointing at our type if it's not None
            return TS_LOGON_INFO_FIELD if t is None else dyn.clone(TS_LOGON_INFO_FIELD, _object_=t)
        return TS_LOGON_INFO_FIELD

    def isTerminator(self, value):
        if hasattr(self, '__FieldsPresent__'):
            res = self.__FieldsPresent__
            return len(self.value) >= ptypes.bitmap.count(res.bitmap(), True)
        elif hasattr(self, 'length'):
            return len(self.value) >= self.length
        return True

@SessionInfoPduType.define
class TS_LOGON_INFO_EXTENDED(pstruct.type):
    type = 3
    def __missing(self):
        cb = self['Length'].li
        res = sum(self[fld].li.size() for fld in ['Length','FieldsPresent','LogonFields'])
        return dyn.block(cb.int() - res)

    def __LogonFields(self):
        res = self['FieldsPresent'].li
        return dyn.clone(LogonFields, __FieldsPresent__=res, length=ptypes.bitmap.count(res.bitmap(), True))

    _fields_ = [
        (pint.uint16_t, 'Length'),
        (LOGON_EX_, 'FieldsPresent'),
        #(lambda self: dyn.clone(LogonFields, length=ptypes.bitmap.count(self['FieldsPresent'].li.bitmap(), True)), 'LogonFields'),
        (__LogonFields, 'LogonFields'),
        (__missing, 'Missing'),
        (dyn.block(570), 'Pad'),
    ]

@PDUType2.define
class TS_SAVE_SESSION_INFO_PDU_DATA(pstruct.type):
    type = 0x26

    def __infoData(self):
        res = self['infoType'].li
        return SessionInfoPduType.lookup(res.int())

    _fields_ = [
        (INFOTYPE_, 'infoType'),
        (__infoData, 'infoData'),
    ]

@pbinary.littleendian
class FONTLIST_(pbinary.flags):
    _fields_ = [
        (14, 'unused'),
        (1, 'LAST'),
        (1, 'FIRST'),
    ]

@PDUType2.define
class TS_FONT_LIST_PDU(pstruct.type):
    type = 0x27

    class _entrySize(pint.uint16_t):
        def default(self):
            return self.set(0x32)
        def valid(self):
            return self.copy().default().int() == self.int()
        def properties(self):
            res = super(TS_FONT_LIST_PDU._entrySize, self).properties()
            res['valid'] = self.valid()
            return res
        def alloc(self, **attrs):
            return super(TS_FONT_LIST_PDU._entrySize, self).alloc(**attrs).default()

    _fields_ = [
        (pint.uint16_t, 'numberFonts'),
        (pint.uint16_t, 'totalNumFonts'),
        (FONTLIST_, 'listFlags'),
        (_entrySize, 'entrySize'),
    ]

    def alloc(self, **fields):
        res = super(TS_FONT_LIST_PDU, self).alloc(**fields)
        if 'entrySize' not in fields:
            res['entrySize'].default()
        return res

@PDUType2.define
class TS_FONT_MAP_PDU(pstruct.type):
    type = 0x28
    class _entrySize(pint.uint16_t):
        def default(self):
            return self.set(0x4)
        def valid(self):
            return self.copy().default().int() == self.int()
        def properties(self):
            res = super(TS_FONT_MAP_PDU._entrySize, self).properties()
            res['valid'] = self.valid()
            return res
        def alloc(self, **attrs):
            return super(TS_FONT_MAP_PDU._entrySize, self).alloc(**attrs).default()

    _fields_ = [
        (pint.uint16_t, 'numberEntries'),
        (pint.uint16_t, 'totalNumEntries'),
        (FONTLIST_, 'mapFlags'),
        (_entrySize, 'entrySize'),
    ]

    def alloc(self, **fields):
        res = super(TS_FONT_MAP_PDU, self).alloc(**fields)
        if 'entrySize' not in fields:
            res['entrySize'].default()
        return res

class TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Key1'),
        (pint.uint32_t, 'Key2'),
    ]

    def summary(self):
        return "({:d},{:d})".format(self['Key1'].int(), self['Key2'].int())

@pbinary.littleendian
class PERSIST_(pbinary.flags):
    _fields_ = [
        (6, 'unused'),
        (1, 'LAST_PDU'),
        (1, 'FIRST_PDU'),
    ]

@PDUType2.define
class TS_BITMAPCACHE_PERSISTENT_LIST_PDU(pstruct.type):
    type = 0x2b

    class _entries(parray.type):
        length = 5

        def _object_(self):
            parent = self.getparent(TS_BITMAPCACHE_PERSISTENT_LIST_PDU)
            index, res = len(self.value), parent['numEntriesCache'].li
            return dyn.array(TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY, res[index].int())

        def summary(self):
            rows = [(i, len(item)) for i, item in enumerate(self)]

            F = fcompose(operator.itemgetter(1), fpartial(operator.eq, 0))
            #prefix = map(None, itertools.takewhile(F, rows))
            prefix = [item for item in itertools.takewhile(F, rows)]
            #suffix = map(None, itertools.takewhile(F, islice(reversed(rows), 0, len(rows) - len(prefix))))
            suffix = [item for item in itertools.takewhile(F, islice(reversed(rows), 0, len(rows) - len(prefix)))]
            iterable = islice(rows, len(prefix), len(rows) - len(suffix))

            cols = []
            if prefix and len(prefix) < len(rows):
                cols.append("...(index #{:d}) {:d} items".format(*next(iterable)))

            for index, length in iterable:
                cols.append("{:d} item{:s}".format(length, '' if length == 1 else 's'))

            #suffix = map(None, reversed(suffix))
            suffix = [item for item in reversed(suffix)]
            if suffix:
                cols.append("...({:d} more entr{:s})".format(len(suffix), 'y' if len(suffix) == 1 else 'ies'))
            else:
                cols.extend(map("{:d} items".format, suffix))

            res = "{{{:s}}}".format(', '.join(cols)) if cols else '...(empty)...'
            return "{:s}[{:d}] {:s}".format(TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY.typename(), len(self), res)

    class _integerList(parray.type):
        length, _object_ = 5, pint.uint16_t

        def summary(self):
            res = ( item.int() for item in self )
            return "{:s} :> {{{:s}}}".format(self.__element__(), ', '.join(map("{:d}".format, res)))

    _fields_ = [
        (_integerList, 'numEntriesCache'),
        (_integerList, 'totalEntriesCache'),
        (PERSIST_, 'bBitMask'),
        (pint.uint8_t, 'Pad2'),
        (pint.uint16_t, 'Pad3'),
        (_entries, 'entries'),
    ]

    def alloc(self, **fields):
        res = super(TS_BITMAPCACHE_PERSISTENT_LIST_PDU, self).alloc(**fields)
        return res if 'numEntriesCache' in fields else res.set(numEntriesCache=[ len(item) for item in res['entries'] ])

@pbinary.littleendian
class BC_ERR_(pbinary.flags):
    _fields_ = [
        (6, 'unused'),
        (1, 'NEWNUMENTRIES_VALID'),
        (1, 'FLUSH_CACHE'),
    ]

class TS_BITMAP_CACHE_ERROR_INFO(pstruct.type):
    _fields_ = [
        (Integer8, 'CacheID'),
        (BC_ERR_, 'bBitField'),
        (Integer16, 'Pad'),
        (Integer32, 'NewNumEntries'),
    ]

@PDUType2.define
class TS_BITMAP_CACHE_ERROR_PDU(pstruct.type):
    type = 0x2c
    _fields_ = [
        (Integer8, 'NumInfoBlocks'),
        (Integer8, 'Pad1'),
        (Integer16, 'Pad2'),
        (lambda self: dyn.array(TS_BITMAP_CACHE_ERROR_INFO, self['NumInfoBlocks'].li.int()), 'Info'),
    ]

@pbinary.littleendian
class OC_ERR_(pbinary.flags):
    _fields_ = [
        (31, 'unused'),
        (1, 'FLUSH_AND_DISABLE_OFFSCREEN'),
    ]

@PDUType2.define
class TS_OFFSCRCACHE_ERROR_PDU(pstruct.type):
    type = 0x2e
    _fields_ = [
        (OC_ERR_, 'flags'),
    ]

class ERROR_INFO_(pint.enum, pint.uint32_t):
    _values_ = [
        ('NONE', 0x00000000),
        ('RPC_INITIATED_DISCONNECT', 0x00000001),
        ('RPC_INITIATED_LOGOFF', 0x00000002),
        ('IDLE_TIMEOUT', 0x00000003),
        ('LOGON_TIMEOUT', 0x00000004),
        ('DISCONNECTED_BY_OTHERCONNECTION', 0x00000005),
        ('OUT_OF_MEMORY', 0x00000006),
        ('SERVER_DENIED_CONNECTION', 0x00000007),
        ('SERVER_INSUFFICIENT_PRIVILEGES', 0x00000009),
        ('SERVER_FRESH_CREDENTIALS_REQUIRED', 0x0000000A),
        ('RPC_INITIATED_DISCONNECT_BYUSER', 0x0000000B),
        ('LOGOFF_BY_USER', 0x0000000C),
        ('LICENSE_INTERNAL', 0x00000100),
        ('LICENSE_NO_LICENSE_SERVER', 0x00000101),
        ('LICENSE_NO_LICENSE', 0x00000102),
        ('LICENSE_BAD_CLIENT_MSG', 0x00000103),
        ('LICENSE_HWID_DOESNT_MATCH_LICENSE', 0x00000104),
        ('LICENSE_BAD_CLIENT_LICENSE', 0x00000105),
        ('LICENSE_CANT_FINISH_PROTOCOL', 0x00000106),
        ('LICENSE_CLIENT_ENDED_PROTOCOL', 0x00000107),
        ('LICENSE_BAD_CLIENT_ENCRYPTION', 0x00000108),
        ('LICENSE_CANT_UPGRADE_LICENSE', 0x00000109),
        ('LICENSE_NO_REMOTE_CONNECTIONS', 0x0000010A),
        ('CB_DESTINATION_NOT_FOUND', 0x00000400),
        ('CB_LOADING_DESTINATION', 0x00000402),
        ('CB_REDIRECTING_TO_DESTINATION', 0x00000404),
        ('CB_SESSION_ONLINE_VM_WAKE', 0x00000405),
        ('CB_SESSION_ONLINE_VM_BOOT', 0x00000406),
        ('CB_SESSION_ONLINE_VM_NO_DNS', 0x00000407),
        ('CB_DESTINATION_POOL_NOT_FREE', 0x00000408),
        ('CB_CONNECTION_CANCELLED', 0x00000409),
        ('CB_CONNECTION_ERROR_INVALID_SETTINGS', 0x00000410),
        ('CB_SESSION_ONLINE_VM_BOOT_TIMEOUT', 0x00000411),
        ('CB_SESSION_ONLINE_VM_SESSMON_FAILED', 0x00000412),
        ('UNKNOWNPDUTYPE2', 0x000010C9),
        ('UNKNOWNPDUTYPE', 0x000010CA),
        ('DATAPDUSEQUENCE', 0x000010CB),
        ('CONTROLPDUSEQUENCE', 0x000010CD),
        ('INVALIDCONTROLPDUACTION', 0x000010CE),
        ('INVALIDINPUTPDUTYPE', 0x000010CF),
        ('INVALIDINPUTPDUMOUSE', 0x000010D0),
        ('INVALIDREFRESHRECTPDU', 0x000010D1),
        ('CREATEUSERDATAFAILED', 0x000010D2),
        ('CONNECTFAILED', 0x000010D3),
        ('CONFIRMACTIVEWRONGSHAREID', 0x000010D4),
        ('CONFIRMACTIVEWRONGORIGINATOR', 0x000010D5),
        ('PERSISTENTKEYPDUBADLENGTH', 0x000010DA),
        ('PERSISTENTKEYPDUILLEGALFIRST', 0x000010DB),
        ('PERSISTENTKEYPDUTOOMANYTOTALKEYS', 0x000010DC),
        ('PERSISTENTKEYPDUTOOMANYCACHEKEYS', 0x000010DD),
        ('INPUTPDUBADLENGTH', 0x000010DE),
        ('BITMAPCACHEERRORPDUBADLENGTH', 0x000010DF),
        ('SECURITYDATATOOSHORT', 0x000010E0),
        ('VCHANNELDATATOOSHORT', 0x000010E1),
        ('SHAREDATATOOSHORT', 0x000010E2),
        ('BADSUPRESSOUTPUTPDU', 0x000010E3),
        ('CONFIRMACTIVEPDUTOOSHORT', 0x000010E5),
        ('CAPABILITYSETTOOSMALL', 0x000010E7),
        ('CAPABILITYSETTOOLARGE', 0x000010E8),
        ('NOCURSORCACHE', 0x000010E9),
        ('BADCAPABILITIES', 0x000010EA),
        ('VIRTUALCHANNELDECOMPRESSIONERR', 0x000010EC),
        ('INVALIDVCCOMPRESSIONTYPE', 0x000010ED),
        ('INVALIDCHANNELID', 0x000010EF),
        ('VCHANNELSTOOMANY', 0x000010F0),
        ('REMOTEAPPSNOTENABLED', 0x000010F3),
        ('CACHECAPNOTSET', 0x000010F4),
        ('BITMAPCACHEERRORPDUBADLENGTH2', 0x000010F5),
        ('OFFSCRCACHEERRORPDUBADLENGTH', 0x000010F6),
        ('DNGCACHEERRORPDUBADLENGTH', 0x000010F7),
        ('GDIPLUSPDUBADLENGTH', 0x000010F8),
        ('SECURITYDATATOOSHORT2', 0x00001111),
        ('SECURITYDATATOOSHORT3', 0x00001112),
        ('SECURITYDATATOOSHORT4', 0x00001113),
        ('SECURITYDATATOOSHORT5', 0x00001114),
        ('SECURITYDATATOOSHORT6', 0x00001115),
        ('SECURITYDATATOOSHORT7', 0x00001116),
        ('SECURITYDATATOOSHORT8', 0x00001117),
        ('SECURITYDATATOOSHORT9', 0x00001118),
        ('SECURITYDATATOOSHORT10', 0x00001119),
        ('SECURITYDATATOOSHORT11', 0x0000111A),
        ('SECURITYDATATOOSHORT12', 0x0000111B),
        ('SECURITYDATATOOSHORT13', 0x0000111C),
        ('SECURITYDATATOOSHORT14', 0x0000111D),
        ('SECURITYDATATOOSHORT15', 0x0000111E),
        ('SECURITYDATATOOSHORT16', 0x0000111F),
        ('SECURITYDATATOOSHORT17', 0x00001120),
        ('SECURITYDATATOOSHORT18', 0x00001121),
        ('SECURITYDATATOOSHORT19', 0x00001122),
        ('SECURITYDATATOOSHORT20', 0x00001123),
        ('SECURITYDATATOOSHORT21', 0x00001124),
        ('SECURITYDATATOOSHORT22', 0x00001125),
        ('SECURITYDATATOOSHORT23', 0x00001126),
        ('BADMONITORDATA', 0x00001129),
        ('VCDECOMPRESSEDREASSEMBLEFAILED', 0x0000112A),
        ('VCDATATOOLONG', 0x0000112B),
        ('BAD_FRAME_ACK_DATA', 0x0000112C),
        ('GRAPHICSMODENOTSUPPORTED', 0x0000112D),
        ('GRAPHICSSUBSYSTEMRESETFAILED', 0x0000112E),
        ('GRAPHICSSUBSYSTEMFAILED', 0x0000112F),
        ('TIMEZONEKEYNAMELENGTHTOOSHORT', 0x00001130),
        ('TIMEZONEKEYNAMELENGTHTOOLONG', 0x00001131),
        ('DYNAMICDSTDISABLEDFIELDMISSING', 0x00001132),
        ('VCDECODINGERROR', 0x00001133),
        ('VIRTUALDESKTOPTOOLARGE', 0x00001134),
        ('MONITORGEOMETRYVALIDATIONFAILED', 0x00001135),
        ('INVALIDMONITORCOUNT', 0x00001136),
        ('UPDATESESSIONKEYFAILED', 0x00001191),
        ('DECRYPTFAILED', 0x00001192),
        ('ENCRYPTFAILED', 0x00001193),
        ('ENCPKGMISMATCH', 0x00001194),
        ('DECRYPTFAILED2', 0x00001195),
    ]

@PDUType2.define
class TS_SET_ERROR_INFO_PDU(pstruct.type):
    type = 0x2f
    _fields_ = [
        (ERROR_INFO_, 'errorInfo'),
    ]

    def summary(self):
        res = self['errorInfo'].summary()
        return "errorInfo={:s}".format(res)

@pbinary.littleendian
class DNG_ERR_(pbinary.flags):
    _fields_ = [
        (31, 'unused'),
        (1, 'FLUSH_AND_DISABLE_DRAWNINEGRID'),
    ]

@PDUType2.define
class TS_DRAWNINEGRID_ERROR_PDU(pstruct.type):
    type = 0x30
    _fields_ = [
        (DNG_ERR_, 'flags'),
    ]

@pbinary.littleendian
class GDIPLUS_ERR_(pbinary.flags):
    _fields_ = [
        (31, 'unused'),
        (1, 'FLUSH_AND_DISABLE_DRAWGDIPLUS'),
    ]

@PDUType2.define
class TS_DRAWGDIPLUS_ERROR_PDU(pstruct.type):
    type = 0x31
    _fields_ = [
        (GDIPLUS_ERR_, 'flags'),
    ]

class TS_STATUS_(pint.enum, pint.uint32_t):
    _values_ = [
        ('FINDING_DESTINATION', 0x00000401),
        ('LOADING_DESTINATION', 0x00000402),
        ('BRINGING_SESSION_ONLINE', 0x00000403),
        ('REDIRECTING_TO_DESTINATION', 0x00000404),
        ('VM_LOADING', 0x00000501),
        ('VM_WAKING', 0x00000502),
        ('VM_STARTING', 0x00000503),
        ('VM_STARTING_MONITORING', 0x00000504),
        ('VM_RETRYING_MONITORING', 0x00000505),
    ]

@PDUType2.define
class TS_STATUS_INFO_PDU(pstruct.type):
    type = 0x36
    _fields_ = [
        (TS_STATUS_, 'statusCode'),
    ]

    def summary(self):
        res = self['statusCode'].summary()
        return "statusCode={:s}".format(res)

@PDUType2.define
class TS_REFRESH_RECT_PDU(pstruct.type):
    type = 0x21

    def __padding(self):
        res = self['desktopRect'].li.size()
        return dyn.block((4 - res % 4) & 3)

    _fields_ = [
        (Integer8, 'rectCount'),    # +12 and maximum of 0xff since only the lsb is used
        (dyn.array(Integer8, 3), 'pad3Octets'),
        (lambda self: dyn.array(mas.Rectangle16, self['rectCount'].li.int()), 'desktopRect'),
        (__padding, 'desktopRectPadding'),
    ]

    def alloc(self, **fields):
        res = super(TS_REFRESH_RECT_PDU, self).alloc(**fields)
        return res if 'rectCount' in fields else res.set(rectCount=(3 + res['desktopRect'].size()) // 4)

class _DISPLAY_UPDATES(pint.enum, Integer8):
    _values_ = [
        ('SUPPRESS', 0),
        ('ALLOW', 1),
    ]

@PDUType2.define
class TS_SUPPRESS_OUTPUT_PDU(pstruct.type):
    type = 0x23
    _fields_ = [
        (_DISPLAY_UPDATES, 'allowDisplayUpdates'),
        (dyn.array(Integer8, 3), 'pad3Octets'),
        (mas.Rectangle16, 'destkopRect'),
    ]

### FastPath definitions
# input events
class TS_FASTPATH_EVENT_(pbinary.enum):
    width, _values_ = 3, [
        ('SCANCODE', 0x0),
        ('MOUSE', 0x1),
        ('MOUSEX', 0x2),
        ('SYNC', 0x3),
        ('UNICODE', 0x4),
        ('QOE_TIMESTAMP', 0x6),
    ]

class TS_FASTPATH_EVENT(ptype.definition):
    cache = {}

class FASTPATH_INPUT_KBDFLAGS_(pbinary.struct):
    _fields_ = [
        (2, 'unused'),
        (1, 'EXTENDED1'),
        (1, 'EXTENDED'),
        (1, 'RELEASE'),
    ]

@TS_FASTPATH_EVENT.define
class TS_FP_KEYBOARD_EVENT(pstruct.type):
    type = 0
    eventFlags = FASTPATH_INPUT_KBDFLAGS_
    _fields_ = [
        (pint.uint8_t, 'keyCode'),
    ]

class PTRFLAGS_(pbinary.flags):
    _fields_ = [
        (1, 'DOWN'),
        (1, 'BUTTON3'),
        (1, 'BUTTON2'),
        (1, 'BUTTON1'),

        (1, 'MOVE'),

        (1, 'HWHEEL'),
        (1, 'WHEEL'),
        (9, 'WheelRotationMask'),
    ]

class TS_POINTER_EVENT(pstruct.type):
    _fields_ = [
        (PTRFLAGS_, 'pointerFlags'),
        (pint.uint16_t, 'xPos'),
        (pint.uint16_t, 'yPos'),
    ]

class PTRXFLAGS_(pbinary.flags):
    _fields_ = [
        (1, 'DOWN'),
        (13, 'unused'),
        (1, 'BUTTON2'),
        (1, 'BUTTON1'),
    ]

class TS_POINTERX_EVENT(pstruct.type):
    _fields_ = [
        (PTRXFLAGS_, 'pointerFlags'),
        (pint.uint16_t, 'xPos'),
        (pint.uint16_t, 'yPos'),
    ]

@TS_FASTPATH_EVENT.define
class TS_FP_POINTER_EVENT(TS_POINTER_EVENT):
    type = 1

@TS_FASTPATH_EVENT.define
class TS_FP_POINTERX_EVENT(TS_POINTERX_EVENT):
    type = 2

class FASTPATH_INPUT_SYNC_(pbinary.flags):
    _fields_ = [
        (1, 'unused'),
        (1, 'KANA_LOCK'),
        (1, 'CAPS_LOCK'),
        (1, 'NUM_LOCK'),
        (1, 'SCROLL_LOCK'),
    ]

@TS_FASTPATH_EVENT.define
class TS_FP_SYNC_EVENT(ptype.undefined):
    type = 3
    eventFlags = FASTPATH_INPUT_SYNC_

@TS_FASTPATH_EVENT.define
class TS_FP_UNICODE_KEYBOARD_EVENT(pstruct.type):
    type = 4
    eventFlags = FASTPATH_INPUT_KBDFLAGS_
    _fields_ = [
        (pint.uint16_t, 'unicodeCode'),
    ]

@TS_FASTPATH_EVENT.define
class TS_FP_QOETIMESTAMP_EVENT(pstruct.type):
    type = 6
    _fields_ = [
        (pint.uint32_t, 'timestamp'),
    ]

class TS_FP_INPUT_EVENT_HEADER(pbinary.struct):
    def __eventFlags(self):
        res = TS_FASTPATH_EVENT.lookup(self['eventCode'])
        return getattr(self, 'eventFlags', 5)

    _fields_ = [
        (TS_FASTPATH_EVENT_, 'eventCode'),
        (__eventFlags, 'eventFlags'),
    ]

class TS_FP_INPUT_EVENT(pstruct.type):
    def __eventData(self):
        res = self['eventHeader'].li
        return TS_FASTPATH_EVENT.lookup(res['eventCode'])

    _fields_ = [
        (TS_FP_INPUT_EVENT_HEADER, 'eventHeader'),
        (__eventData, 'eventData'),
    ]

class TS_FP_INPUT_PDU(pstruct.type):
    def __fpInputEvents(self):
        res = self['numEvents'].li
        return dyn.array(TS_FP_INPUT_EVENT, res.int())

    _fields_ = [
        (Integer8, 'numEvents'),
        (__fpInputEvents, 'fpInputEvents'),
    ]

    def alloc(self, **fields):
        res = super(TS_FP_INPUT_PDU, self).alloc(**fields)
        return res if 'numEvents' in fields else res.set(numEvents=len(res['fpInputEvents']))

class TS_FP_INPUT_PDU_Small(pstruct.type):
    def __fpInputEvents(self):
        try:
            res = self.getparent(SecureFastPathPDU)
        except ptypes.error.ItemNotFoundError:
            return dyn.clone(parray.infinite, _object_=TS_FP_INPUT_EVENT)
        res = res['header'].li
        return dyn.clone(parray.infinite, _object_=TS_FP_INPUT_EVENT, length=res['numEvents'])

    _fields_ = [
        (pint.uint_t, 'numEvents'),
        (__fpInputEvents, 'fpInputEvents'),
    ]

    def alloc(self, **fields):
        res = super(TS_FP_INPUT_PDU_Small, self).alloc(**fields)
        return res if 'numEvents' in fields else res.set(numEvents=len(res['fpInputEvents']))

class FASTPATH_OUTPUT_COMPRESSION_(pbinary.flags):
    _fields_ = [
        (1, 'USED'),
        (1, 'RESERVED'),
    ]

class FASTPATH_FRAGMENT_(pbinary.enum):
    width, _values_ = 2, [
        ('SINGLE', 0),
        ('LAST', 1),
        ('FIRST', 2),
        ('NEXT', 3),
    ]

class FASTPATH_UPDATETYPE_(pbinary.enum):
    width, _values_ = 4, [
        ('ORDERS', 0x0),
        ('BITMAP', 0x1),
        ('PALETTE', 0x2),
        ('SYNCHRONIZE', 0x3),
        ('SURFCMDS', 0x4),
        ('PTR_NULL', 0x5),
        ('PTR_DEFAULT', 0x6),
        ('PTR_POSITION', 0x8),
        ('COLOR', 0x9),
        ('CACHED', 0xA),
        ('POINTER', 0xB),
        ('LARGE_POINTER', 0xC),
    ]

class TS_FP_UPDATE_PDU(pstruct.type):
    class _updateHeader(pbinary.struct):
        _fields_ = [
            (FASTPATH_UPDATETYPE_, 'updateCode'),
            (FASTPATH_FRAGMENT_, 'fragmentation'),
            (FASTPATH_OUTPUT_COMPRESSION_, 'compression'),
        ]

    def __compressionFlags(self):
        res = self['header'].li
        return pint.uint8_t if res['compression']['USED'] else pint.uint_t

    _fields_ = [
        (_updateHeader, 'header'),
        (__compressionFlags, 'compressionFlags'),
        (pint.uint16_t, 'size'),
        (lambda self: dyn.block(self['size'].li.int()), 'updateData'),
    ]

class FASTPATH_ACTION_(pbinary.enum):
    width, _values_ = 2, [
        ('FASTPATH', 0x0),
        ('X224', 0x3),
    ]

class FASTPATH_FLAGS_(pbinary.flags):
    _fields_ = [
        (1, 'ENCRYPTED'),
        (1, 'SECURE_CHECKSUM'),
    ]

class FASTPATH_HEADER(pbinary.struct):
    _fields_ = [
        (FASTPATH_FLAGS_, 'flags'),
        (4, 'numEvents'),
        (FASTPATH_ACTION_, 'action'),
    ]

    def numEvents(self):
        return self['numEvents']

class TS_FP_FIPS_INFO(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'length'),
        (pint.uint8_t, 'version'),
        (pint.uint8_t, 'padlen'),
    ]

class SecureFastPathPDU(SecureBasePDU):
    def __fipsInformation(self):
        level = getattr(self, 'encryptionLevel', 0)

        # Use the encryption level that the user has specified to determine existence
        res = level.int() if hasattr(level, 'int') else level
        return TS_FP_FIPS_INFO if res == ENCRYPTION_LEVEL_.byname('FIPS') else ptype.undefined

    def __dataSignature(self):
        res = self['header'].li
        flags = res['flags']
        return dyn.clone(ber.INTEGER, length=8) if flags['ENCRYPTED'] else ber.INTEGER

    def __securedData(self):
        res = self['header'].li
        flags = res['flags']

        res = self['length'].li
        cb = sum(self[fld].li.size() for fld in ['header','length','fipsInformation','dataSignature'])

        # By default, we're reading an update and so we'll assign a TS_FP_UPDATE_PDU
        # to the securedData. However, if you're building a FASTPATH packet, to
        # send you'll need to assign a TS_FP_INPUT_PDU to data.
        size, _object_ = max((0, res.int() - cb)), TS_FP_UPDATE_PDU

        if flags['ENCRYPTED'] and hasattr(self, 'SecuredDataType'):
            return dyn.clone(self.SecuredDataType, _value_=dyn.block(size), _object_=_object_)
        return dyn.clone(_object_, blocksize=lambda self, cb=size: cb)

    _fields_ = [
        (FASTPATH_HEADER, 'header'),
        (per.LengthDeterminant, 'length'),
        (__fipsInformation, 'fipsInformation'),
        (__dataSignature, 'dataSignature'),
        (__securedData, 'data'),
    ]

    def alloc(self, **fields):
        res = super(SecureFastPathPDU, self).alloc(**fields)

        # if we have an IOStream assigned to us, then we can calculate our MAC
        if hasattr(res, 'IOStream'):
            sdata = res['data']
            if isinstance(sdata, RC4EncodedType) and sdata.d.initializedQ():
                data = sdata.d.li
            else:
                data = sdata
            iostream = res.IOStream
            signature = iostream.MACSignature(data)
            res.DataSignature().set(signature.int())

        cb = sum(self[fld].size() for fld in ['header','length','fipsInformation','dataSignature','data'])
        return res if 'length' in fields else res.set(length=cb)

    def DataSignature(self):
        return self['dataSignature']

    def encryptedQ(self):
        flags = self['header']['flags']
        return bool(flags['ENCRYPTED'])

### ptype.encoded_t for RC4 decoding/encoding
class RC4EncodedType(ptype.encoded_t):
    '''
    This type needs to be constructed with an RC4 attribute that contains an
    object with a single method "cycle". It is up to this RC4 implementation
    to preserve its state so that it can be used to to encode or decode the
    instance multiple times.
    '''

    def encode(self, object, **attrs):
        if hasattr(self, 'RC4'):
            data = self.RC4.cycle(object.serialize())
            return super(RC4EncodedType, self).encode(ptype.block(length=len(data)).set(data), **attrs)
        return super(RC4EncodedType, self).decode(object, **attrs)

    def decode(self, object, **attrs):
        if hasattr(self, 'RC4'):
            data = self.RC4.cycle(object.serialize())
            return super(RC4EncodedType, self).decode(ptype.block(length=len(data)).set(data), **attrs)
        return super(RC4EncodedType, self).decode(object, **attrs)

    def DataSignature(self):
        secure = self.getparent(SecureBasePDU)
        return secure.IOStream.MACSignature(self.dereference())

    def properties(self):
        res = super(RC4EncodedType, self).properties()
        decoded = self.dereference()
        if decoded.initializedQ():
            try:
                secure = self.getparent(SecureBasePDU)
            except ptypes.error.ItemNotFoundError:
                return res
            res['valid'] = secure.DataSignature().int() == self.DataSignature().int()
        return res

### Channel definitions
@pbinary.littleendian
class CHANNEL_FLAG_(pbinary.flags):
    _fields_ = [
        (8, 'unused'),
        (1, 'PACKET_FLUSHED'),
        (1, 'PACKET_AT_FRONT'),
        (1, 'PACKET_COMPRESSED'),
        (1, 'RESERVED'),
        (mas.PACKET_COMPR_, 'CompressionTypeMask'),
        (8, 'unused2'),
        (1, 'SHADOW_PERSISTENT'),
        (1, 'RESUME'),
        (1, 'SUSPEND'),
        (1, 'SHOW_PROTOCOL'),
        (2, 'reserved2'),
        (1, 'FIRST'),
        (1, 'LAST'),
    ]

## This is the structure as defined by Microsoft. We choose not to use this
## because if we hide the header fields (length and flags), then it makes
## allocating the data in this structure non-user-friendly. Plus, there's
## no real reason to hide the header fields within a separate structure.

#class CHANNEL_PDU_HEADER(pstruct.type):
#    _fields_ = [
#        (pint.uint32_t, 'length'),
#        (CHANNEL_FLAG_, 'flags'),
#    ]
#
#    def summary(self):
#        return "length={:x} flags={:s}".format(self['length'].int(), self['flags'].summary())

#class ChannelPDU(pstruct.type):
#    _object_ = ptype.block
#    def __virtualChannelData(self):
#        res = self['channelPduHeader'].li
#        return dyn.clone(self._object_, blocksize=lambda self, cb=res['length'].int(): cb)
#
#    def __padding(self):
#        res = self['channelPduHeader'].li
#        return dyn.block(max((0, res['length'].li.int() - self['virtualChannelData'].li.size())))
#
#    _fields_ = [
#        (CHANNEL_PDU_HEADER, 'channelPduHeader'),
#        (__virtualChannelData, 'virtualChannelData'),
#        (__padding, 'padding'),
#    ]

class ChannelPDU(pstruct.type):
    _object_ = ptype.block

    def __data(self):
        res = self['length'].li
        return dyn.clone(self._object_, blocksize=lambda self, cb=res.int(): cb)

    def __data(self):
        parent = self.parent
        if parent is None:
            res = self['length'].li
            return dyn.clone(self._object_, blocksize=lambda self, cb=res.int(): cb)
        res = parent.blocksize() - sum(self[fld].li.size() for fld in ['length','flags'])
        return dyn.clone(self._object_, blocksize=lambda self, cb=max((0, res)): cb)

    _fields_ = [
        (pint.uint32_t, 'length'),
        (CHANNEL_FLAG_, 'flags'),
        (__data, 'data'),
    ]

    def alloc(self, **fields):
        res = super(ChannelPDU, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=res['data'].size())
