import ptypes, ndk
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

class MessageType(pint.enum, pint.uint32_t):
    _values_ = [
        ('NtlmNegotiate', 0x00000001),
        ('NtlmChallenge', 0x00000002),
        ('NtlmAuthenticate', 0x00000003),
    ]

class NTLMMessageType(ptype.definition):
    cache = {}

class Message(pstruct.type):
    def __MessageFields(self):
        res = self['MessageType'].li
        return NTLMMessageType.withdefault(res.int())

    def __Payload(self):
        try:
            p = self.getparent()
            res = p.blocksize()
        except AttributeError:
            return dyn.block(0)
        bound = p.getoffset() + p.blocksize()
        return dyn.block(max(0, bound - self.getoffset()))

    def __Payload(self):
        res = self['MessageFields'].li
        fields = res.Fields() if hasattr(res, 'Fields') else []
        payload_offset = sum(self[fld].li.size() for fld in ['Signature','MessageType','MessageFields'])
        fields = { field for field in fields if payload_offset <= field['BufferOffset'].int() }
        if fields:
            largest_offset = max(field['BufferOffset'].int() + field['MaximumLength'].int() for field in fields)
            return dyn.block(max(0, largest_offset - payload_offset))
        return dyn.block(0)

    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'Signature'),
        (MessageType, 'MessageType'),
        (__MessageFields, 'MessageFields'), 
        (__Payload, 'MessagePayload'),
    ]

    def alloc(self, **fields):
        fields.setdefault('Signature', 'NTLMSSP\0')
        fields.setdefault('MessagePayload', dyn.clone(parray.type, _object_=ptype.type))
        res = super(Message, self).alloc(**fields)
        return res if 'MessageType' in fields else res.set(MessageType=res['MessageFields'].type)

@pbinary.littleendian
class NTLMSSP_(pbinary.flags):
#class NEGOTIATE(pbinary.flags):
    _fields_ = [
        (1, 'NEGOTIATE_56'),
        (1, 'NEGOTIATE_KEY_EXCH'),
        (1, 'NEGOTIATE_128'),
        (3, 'reserved0(3)'),
        (1, 'NEGOTIATE_VERSION'),
        (1, 'reserved1'),
        (1, 'NEGOTIATE_TARGET_INFO'),
        (1, 'REQUEST_NON_NT_SESSION_KEY'),
        (1, 'reserved2'),
        (1, 'NEGOTIATE_IDENTIFY'),
        (1, 'NEGOTIATE_EXTENDED_SESSIONSECURITY'),
        (1, 'reserved3'),
        (1, 'TARGET_TYPE_SERVER'),
        (1, 'TARGET_TYPE_DOMAIN'),
        (1, 'NEGOTIATE_ALWAYS_SIGN'),
        (1, 'reserved4'),
        (1, 'NEGOTIATE_OEM_WORKSTATION_SUPPLIED'),
        (1, 'NEGOTIATE_OEM_DOMAIN_SUPPLIED'),
        (1, 'NEGOTIATE_ANONYMOUS'),
        (1, 'reserved5'),
        (1, 'NEGOTIATE_NTLM'),
        (1, 'reserved6'),
        (1, 'NEGOTIATE_LM_KEY'),
        (1, 'NEGOTIATE_DATAGRAM'),
        (1, 'NEGOTIATE_SEAL'),
        (1, 'NEGOTIATE_SIGN'),
        (1, 'reserved7'),
        (1, 'REQUEST_TARGET'),
        (1, 'NEGOTIATE_OEM'),
        (1, 'NEGOTIATE_UNICODE'),
    ]

class NTLMSSP_REVISION_(pint.enum, pint.uint8_t):
    _values_ = [
        ('W2K3', 0x0f),
    ]

class VERSION(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'ProductMajorVersion'),
        (pint.uint8_t, 'ProductMinorVersion'),
        (pint.uint16_t, 'ProductBuild'),
        (dyn.block(3), 'Reserved'),
        (NTLMSSP_REVISION_, 'NTLMRevisionCurrent'),
    ]

    def summary(self):
        return "ProductVersion={:d}.{:d}.{:d} NTLMRevisionCurrent={:s}".format(self['ProductMajorVersion'].int(), self['ProductMinorVersion'].int(), self['ProductBuild'].int(), self['NTLMRevisionCurrent'].str())

class PayloadString(pstruct.type):
    def __string(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined

        if fields.p['NegotiateFlags']['NEGOTIATE_UNICODE']:
            return dyn.clone(pstr.wstring, length=fields['Length'].int() // 2)
        return dyn.clone(pstr.string, length=fields['Length'].int())

    def __padding(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined

        length, cb = (fields[fld].li.int() for fld in ('Length','MaximumLength'))
        return dyn.block(max(0, cb - length))

    _fields_ = [
        (__string, 'string'),
        (__padding, 'padding'),
    ]

    def summary(self):
        return "string={:s}".format(self['string'].summary())

class MessageDependentFields(pstruct.type):
    def __BufferOffset(self):
        # This field depends on the offset of the Message instance, so try and
        # locate it so that we can point our buffer into it.
        try:
            p = self.getparent(Message)

        # If we didn't find a parent, then we haven't been attached yet. In this
        # case, we'll just make it a regular pointer so the user can just reference
        # it to whatever they want.
        except ptypes.error.ItemNotFoundError:
            return dyn.pointer(self._object_, pint.uint32_t)
        return dyn.rpointer(self._object_, p, pint.uint32_t)

    _fields_ = [
        (pint.uint16_t, 'Length'),
        (pint.uint16_t, 'MaximumLength'),
        (__BufferOffset, 'BufferOffset'),
    ]

    def summary(self):
        return "Length={:d} MaximumLength={:d} BufferOffset={:#x}".format(self['Length'].li.int(), self['MaximumLength'].li.int(), self['BufferOffset'].li.int())

class DomainNameFields(MessageDependentFields):
    _object_ = PayloadString

class WorkstationFields(MessageDependentFields):
    _object_ = PayloadString

@NTLMMessageType.define
class NEGOTIATE_MESSAGE(pstruct.type):
    type = 1
    _fields_ = [
        (NTLMSSP_, 'NegotiateFlags'),
        (DomainNameFields, 'DomainNameFields'),
        (WorkstationFields, 'WorkstationFields'),
        (VERSION, 'Version'),
    ]

    def Fields(self):
        for fld in ['DomainNameFields','WorkstationFields']:
            yield self[fld]
        return

class TargetNameFields(MessageDependentFields):
    _object_ = PayloadString

class Msv(pint.enum, pint.uint16_t):
    _values_ = [
        ('AvEOL', 0x0000),
        ('AvNbComputerName', 0x0001),
        ('AvNbDomainName', 0x0002),
        ('AvDnsComputerName', 0x0003),
        ('AvDnsDomainName', 0x0004),
        ('AvDnsTreeName', 0x0005),
        ('AvFlags', 0x0006),
        ('AvTimestamp', 0x0007),
        ('AvSingleHost', 0x0008),
        ('AvTargetName', 0x0009),
        ('ChannelBindings', 0x000A),
    ]

class MsvValue(ptype.definition):
    cache = {}

@MsvValue.define
class AvEOL(ptype.block):
    type = 0x0000
@MsvValue.define
class AvNbComputerName(pstr.wstring):
    type = 0x0001
@MsvValue.define
class AvNbDomainName(pstr.wstring):
    type = 0x0002
@MsvValue.define
class AvDnsComputerName(pstr.wstring):
    type = 0x0003
@MsvValue.define
class AvDnsDomainName(pstr.wstring):
    type = 0x0004
@MsvValue.define
class AvDnsTreeName(pstr.wstring):
    type = 0x0005
@MsvValue.define
class AvFlags(pstruct.type):
    type = 0x0006

    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (29, 'unused'),
            (1, 'UntrustedSpn'),
            (1, 'HasMessageIntegrity'),
            (1, 'ConstrainedAuthentication'),
        ]
    _fields_ = [
        (_Flags, 'Flags'),
    ]
@MsvValue.define
class AvTimestamp(ndk.FILETIME):
    type = 0x0007
@MsvValue.define
class AvSingleHost(pstruct.type):
    type = 0x0008
    _fields_ = [
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'Z4'),
        (pint.uint64_t, 'CustomData'),
        (dyn.clone(pint.uint_t, length=32), 'MachineID'),
    ]
    def alloc(self, **fields):
        res = super(AvSingleHost, self).alloc(**fields)
        return res if 'Size' in fields else res.set(Size=sum(res[fld].size() for fld in ['Size','Z4','CustomData','MachineID']))
@MsvValue.define
class AvTargetName(pstr.wstring):
    type = 0x0009
@MsvValue.define
class AvChannelBindings(pint.uint_t):
    type = 0x000a
    length = 0x10

class AV_PAIR(pstruct.type):
    def __Value(self):
        res, cb = (self[fld].li for fld in ['AvId','AvLen'])
        try:
            t = MsvValue.lookup(res.int())
        except KeyError:
            return dyn.block(cb.int())

        if issubclass(t, pstr.wstring):
            return dyn.clone(t, length=cb.int() // 2)
        return t

    _fields_ = [
        (Msv, 'AvId'),
        (pint.uint16_t, 'AvLen'),
        (__Value, 'Value'),
    ]

    def summary(self):
        if self['AvId']['AvEOL']:
            return "AvId={:s}".format(self['AvId'].summary())
        return "AvId={:s} Value={:s}".format(self['AvId'].summary(), self['Value'].summary())

    def alloc(self, **fields):
        res = super(AV_PAIR, self).alloc(**fields)
        if 'AvLen' not in fields:
            res.set(AvLen=res['Value'].size())
        if 'AvId' not in fields:
            res.set(AvId=res['value'].type)
        return res

class AV_PAIRs(parray.terminated):
    _object_ = AV_PAIR
    def isTerminator(self, value):
        return value['AvId']['AvEOL']

    def summary(self):
        iterable = (item.summary() for item in self)
        return "[{:s}]".format(', '.join(iterable))

class PayloadPairs(pstruct.type):
    def __padding(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptypes.undefined
        length, cb = (fields[fld].li.int() for fld in ('Length','MaximumLength'))
        return dyn.block(max(0, cb - length))

    _fields_ = [
        (AV_PAIRs, 'pairs'),
        (__padding, 'padding'),
    ]

    def summary(self):
        return "string={:s}".format(self['string'].summary())

class TargetInfoFields(MessageDependentFields):
    _object_ = PayloadPairs

@NTLMMessageType.define
class CHALLENGE_MESSAGE(pstruct.type):
    type = 2
    _fields_ = [
        (TargetNameFields, 'TargetNameFields'),
        (NTLMSSP_, 'NegotiateFlags'),
        (dyn.clone(pint.uint_t, length=8), 'ServerChallenge'),
        (dyn.clone(pint.uint_t, length=8), 'Reserved'),
        (TargetInfoFields, 'TargetInfoFields'),
        (VERSION, 'Version'),
    ]

    def Fields(self):
        for fld in ['TargetNameFields','TargetInfoFields']:
            yield self[fld]
        return

class LM_RESPONSE(pstruct.type):
    _fields_ = [
        (dyn.clone(pint.uint_t, length=24), 'Response'),
    ]

class LMv2_RESPONSE(pstruct.type):
    _fields_ = [
        (dyn.clone(pint.uint_t, length=16), 'LmChallengeResponse'),
        (dyn.clone(pint.uint_t, length=8), 'ChallengeFromClient'),
    ]

class NTLM_RESPONSE(pstruct.type):
    _fields_ = [
        (dyn.clone(pint.uint_t, length=24), 'Response'),
    ]

class NTLMv2_CLIENT_CHALLENGE(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'RespType'),
        (pint.uint8_t, 'HiRespType'),
        (pint.uint16_t, 'Reserved1'),
        (pint.uint32_t, 'Reserved2'),
        (pint.uint64_t, 'TimeStamp'),
        (pint.uint64_t, 'ChallengeFromClient'),
        (pint.uint32_t, 'Reserved3'),
        (AV_PAIRs, 'AvPairs'),
    ]

    def summary(self):
        return "RespType={:d} HiRespType={:d} TimeStamp={:d} ChallengeFromClient={:#x} AvPairs={:s}".format(self['RespType'].int(), self['HiRespType'].int(), self['TimeStamp'].int(), self['ChallengeFromClient'].int(), self['AvPairs'].summary())

class NTLMv2_RESPONSE(pstruct.type):
    _fields_ = [
        (dyn.clone(pint.uint_t, length=16), 'Response'),
        (NTLMv2_CLIENT_CHALLENGE, 'ClientChallenge'),
    ]

    def summary(self):
        return "Response={:#x} ClientChallenge={{ {:s} }}".format(self['Response'].int(), self['ClientChallenge'].summary())

class LmChallengeResponseFields(MessageDependentFields):
    def _object_(self):
        p = self.getparent()
        if p['NegotiateFlags']['NEGOTIATE_EXTENDED_SESSIONSECURITY']:
            return LMv2_RESPONSE
        if p['NegotiateFlags']['NEGOTIATE_LM_KEY']:
            return LM_RESPONSE
        raise TypeError(p['NegotiateFlags'])

class NtChallengeResponseFields(MessageDependentFields):
    def _object_(self):
        p = self.getparent()
        if p['NegotiateFlags']['NEGOTIATE_EXTENDED_SESSIONSECURITY']:
            return NTLMv2_RESPONSE
        if p['NegotiateFlags']['NEGOTIATE_NTLM']:
            return NTLM_RESPONSE
        raise TypeError(p['NegotiateFlags'])

class UserNameFields(MessageDependentFields):
    _object_ = PayloadString

class SessionKey(pstruct.type):
    def __session_key(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        return dyn.clone(pint.uint_t, length=fields['Length'].int())

    def __padding(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptype.undefined
        length, cb = (fields[fld].li.int() for fld in ('Length','MaximumLength'))
        return dyn.block(max(0, cb - length))

    _fields_ = [
        (__session_key, 'session_key'),
        (__padding, 'padding'),
    ]

class EncryptedRandomSessionKeyFields(MessageDependentFields):
    _object_ = SessionKey

@NTLMMessageType.define
class AUTHENTICATE_MESSAGE(pstruct.type):
    type = 3
    _fields_ = [
        (LmChallengeResponseFields, 'LmChallengeResponseFields'),
        (NtChallengeResponseFields, 'NtChallengeResponseFields'),
        (DomainNameFields, 'DomainNameFields'),
        (UserNameFields, 'UserNameFields'),
        (WorkstationFields, 'WorkstationFields'),
        (EncryptedRandomSessionKeyFields, 'EncryptedRandomSessionKeyFields'),
        (NTLMSSP_, 'NegotiateFlags'),
        (VERSION, 'Version'),
        (dyn.clone(pint.uint_t, length=16), 'MIC'),
    ]

    def Fields(self):
        for fld in ['LmChallengeResponseFields','NtChallengeResponseFields','DomainNameFields','UserNameFields','WorkstationFields','EncryptedRandomSessionKeyFields']:
            yield self[fld]
        return

if __name__ == '__main__':
    pass
