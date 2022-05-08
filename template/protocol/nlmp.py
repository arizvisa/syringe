import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

class MessageType(pint.enum, pint.uint32_t):
    _values_ = [
        ('NtLmNegotiate', 0x00000001),
        ('NtLmChallenge', 0x00000002),
        ('NtLmAuthenticate', 0x00000003),
    ]

class NTLMMessageType(ptype.definition):
    cache = {}

class Message(pstruct.type):
    class _Signature(pstr.string):
        length = 8
        def default(self):
            return self.set('NTLMSSP\0')
        def valid(self):
            return self.copy().default().serialize() == self.serialize()
        def alloc(self, **attrs):
            return super(Message._Signature, self).alloc(**attrs).default()
        def properties(self):
            res = super(Message._Signature, self).properties()
            if self.initializedQ():
                res['valid'] = self.valid()
            return res

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
        payload_offset = sum(self[fld].li.size() for fld in ['Signature', 'MessageType', 'MessageFields'])
        fields = { field for field in fields if payload_offset <= field['BufferOffset'].int() }
        if fields:
            largest_offset = max(field['BufferOffset'].int() + field['MaximumLength'].int() for field in fields)
            return dyn.block(max(0, largest_offset - payload_offset))
        return dyn.block(0)

    _fields_ = [
        (_Signature, 'Signature'),
        (MessageType, 'MessageType'),
        (__MessageFields, 'MessageFields'),
        (__Payload, 'MessagePayload'),
    ]

    def alloc(self, **fields):
        fields.setdefault('Signature', 'NTLMSSP\0')
        fields.setdefault('MessagePayload', dyn.clone(parray.type, _object_=ptype.type))
        res = super(Message, self).alloc(**fields)
        return res if 'MessageType' in fields or not hasattr(res['MessageFields'], 'type') else res.set(MessageType=res['MessageFields'].type)

@pbinary.littleendian
class NTLMSSP_(pbinary.flags):
#class NEGOTIATE_(pbinary.flags):
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

        length, cb = (fields[fld].li.int() for fld in ['Length', 'MaximumLength'])
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
            return dyn.pointer(self._object_, pint.littleendian(pint.uint32_t))
        return dyn.rpointer(self._object_, p, pint.littleendian(pint.uint32_t))

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

    def enumerate(self):
        '''Yield the name and field that compose the message type payload.'''
        for fld in ['DomainNameFields', 'WorkstationFields']:
            yield fld, self[fld]
        return

    def iterate(self):
        '''Yield each field that composes the message type payload.'''
        for _, item in self.enumerate():
            yield item
        return

    def Fields(self):
        """
        Yield all of the fields that are used to calculate the size
        and compose the payload for this message type.
        """
        for item in self.iterate():
            yield item
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
    def summary(self):
        res = self['Flags']
        return "Flags={:s}".format(res.summary())
@MsvValue.define
class AvTimestamp(pstruct.type):
    type = 0x0007

    # this was copied out of ndk.datatypes to avoid a whole dependency
    _fields_ = [
        (pint.uint32_t, 'dwLowDateTime'),
        (pint.uint32_t, 'dwHighDateTime')
    ]
    def timestamp(self):
        '''Return the number of 100ns represented by the instance.'''
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * pow(2, 32) + low
    def datetime(self):
        res, epoch = self.timestamp(), datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc if hasattr(datetime, 'timezone') else None)
        delta = datetime.timedelta(microseconds=res * 1e-1)
        return epoch + delta
    def summary(self):
        tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone))) if hasattr(datetime, 'timezone') else None
        try:
            dt = self.datetime()
            res = dt.astimezone(tzinfo) if tzinfo else dt
        except (ValueError, OverflowError):
            return super(AvTimestamp, self).summary()
        ts, seconds = self.timestamp(), res.second + res.microsecond * 1e-6
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s}{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.6f}".format(seconds).zfill(9), res.strftime('%z'), ts)

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
        return res if 'Size' in fields else res.set(Size=sum(res[fld].size() for fld in ['Size', 'Z4', 'CustomData', 'MachineID']))
    def summary(self):
        res, required = [], {'Size', 'MachineID'}
        for key in self:
            value = self[key]
            if value.int() or key in required:
                res.append("{:s}={:#x}".format(key, value.int()))
            continue
        return ' '.join(res)
@MsvValue.define
class AvTargetName(pstr.wstring):
    type = 0x0009
@MsvValue.define
class AvChannelBindings(pint.uint_t):
    type = 0x000a
    length = 0x10

class AV_PAIR(pstruct.type):
    def __Value(self):
        res, cb = (self[fld].li for fld in ['AvId', 'AvLen'])
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

    def has(self, id):
        for item in self:
            if item['AvId'][id]:
                return True
            continue
        return False

    def item(self, id):
        for item in self:
            if item['AvId'][id]:
                return item['value']
            continue
        return

    def enumerate(self):
        for item in self:
            res = item['AvId']
            yield res.int(), item['value']
        return

class PayloadPairs(pstruct.type):
    def __padding(self):
        try:
            fields = self.getparent(MessageDependentFields)
        except ptypes.error.ItemNotFoundError:
            return ptypes.undefined
        length, cb = (fields[fld].li.int() for fld in ['Length', 'MaximumLength'])
        return dyn.block(max(0, cb - length))

    _fields_ = [
        (AV_PAIRs, 'pairs'),
        (__padding, 'padding'),
    ]

    #def summary(self):
    #    return "string={:s}".format(self['string'].summary())

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

    def enumerate(self):
        '''Yield the name and field that compose the message type payload.'''
        for fld in ['TargetNameFields', 'TargetInfoFields']:
            yield fld, self[fld]
        return

    def iterate(self):
        '''Yield each field that composes the message type payload.'''
        for _, item in self.enumerate():
            yield item
        return

    def Fields(self):
        """
        Yield all of the fields that are used to calculate the size
        and compose the payload for this message type.
        """
        for item in self.iterate():
            yield item
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
        length, cb = (fields[fld].li.int() for fld in ['Length', 'MaximumLength'])
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

    def enumerate(self):
        '''Yield the name and field that compose the message type payload.'''
        for fld in ['LmChallengeResponseFields', 'NtChallengeResponseFields', 'DomainNameFields', 'UserNameFields', 'WorkstationFields', 'EncryptedRandomSessionKeyFields']:
            yield fld, self[fld]
        return

    def iterate(self):
        '''Yield each field that composes the message type payload.'''
        for _, item in self.enumerate():
            yield item
        return

    def Fields(self):
        """
        Yield all of the fields that are used to calculate the size
        and compose the payload for this message type.
        """
        for item in self.iterate():
            yield item
        return

if __name__ == '__main__':
    import sys, operator, ptypes, protocol.ber as ber, protocol.credssp as credssp, protocol.nlmp as nlmp
    from ptypes import *
    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    def make_challenge():
        challenge = nlmp.CHALLENGE_MESSAGE().alloc(NegotiateFlags=dict(
            NEGOTIATE_56=1, NEGOTIATE_KEY_EXCH=1, NEGOTIATE_128=1, NEGOTIATE_VERSION=1,
            NEGOTIATE_TARGET_INFO=1, NEGOTIATE_EXTENDED_SESSIONSECURITY=1, TARGET_TYPE_SERVER=1,
            NEGOTIATE_ALWAYS_SIGN=1, NEGOTIATE_NTLM=1, NEGOTIATE_SEAL=1,
            NEGOTIATE_SIGN=1, REQUEST_TARGET=1, NEGOTIATE_UNICODE=1,
        )).set(
            Version=dict(ProductMajorVersion=10, ProductBuild=17763, NTLMRevisionCurrent='W2K3'),
            ServerChallenge=0xc7ac1ab989c526a3,
        )

        res = pstr.wstring().set(u'DESKTOP-UAGCVKC', retain=False)
        targetname = nlmp.PayloadString().alloc(string=res)
        challenge['TargetNameFields'].set(Length=targetname.size(), MaximumLength=targetname.size())

        res = []
        res.append(nlmp.AvNbDomainName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvNbComputerName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsDomainName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsComputerName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvTimestamp().a.set(dwLowDateTime=1329434256, dwHighDateTime=30757815))
        res.append(nlmp.AvEOL().a)
        pairs = nlmp.AV_PAIRs().alloc([nlmp.AV_PAIR().alloc(Value=item) for item in res])
        targetinfo = nlmp.AV_PAIRs().alloc(pairs)
        challenge['TargetInfoFields'].set(Length=targetinfo.size(), MaximumLength=targetinfo.size())

        return challenge, targetname, targetinfo

    def test_encode_nlmp():
        data = '30820102a003020106a181fa3081f73081f4a081f10481ee4e544c4d53535000020000001e001e003800000035828ae2a326c589b91aacc7000000000000000098009800560000000a0063450000000f4400450053004b0054004f0050002d00550041004700430056004b00430002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50100000000'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l
        assert(z.size() == z.source.size())
        assert(z.serialize() == z.source.value)

        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        challenge, targetname, targetinfo = make_challenge()

        msg = nlmp.Message().alloc(MessageFields=challenge)
        targetname_offset = msg['MessagePayload'].append(targetname)
        targetinfo_offset = msg['MessagePayload'].append(targetinfo)
        msg['MessageFields']['TargetNameFields']['BufferOffset'].reference(targetname)
        msg['MessageFields']['TargetInfoFields']['BufferOffset'].reference(targetinfo)

        assert(nlmsg.serialize() == msg.serialize())
    test_encode_nlmp()

    def test_decode_nlmp_messagefields_0():
        data = '30820102a003020106a181fa3081f73081f4a081f10481ee4e544c4d53535000020000001e001e003800000035828ae2a326c589b91aacc7000000000000000098009800560000000a0063450000000f4400450053004b0054004f0050002d00550041004700430056004b00430002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50100000000'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        assert(z.size() == z.source.size())
        assert(z['value'][0]['value']['Version'].serialize() == b'\2\1\6')

        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        expected = {
            'TargetNameFields': '4400450053004b0054004f0050002d00550041004700430056004b004300',
            'TargetInfoFields': '02001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50100000000',
        }

        for name, item in nlmsg['messagefields'].enumerate():
            value = fromhex(expected[name])
            assert(item['BufferOffset'].d.li.serialize() == fromhex(expected[name]))
        assert(z.serialize() == z.source.value)
    test_decode_nlmp_messagefields_0()

    def test_decode_nlmp_messagefields_1():
        data = '30820287a003020106a1820226308202223082021ea082021a048202164e544c4d535350000300000018001800a40000004a014a01bc0000001e001e005800000010001000760000001e001e00860000001000100006020000358288e20a00cb490000000f1e8f34474eb81d34c93de8ac22879f874400450053004b0054004f0050002d00370031004d003600440045004d0041004e0046004c0041004e004e0045004400450053004b0054004f0050002d00370031004d003600440045004d000000000000000000000000000000000000000000000000009ebe92602c8cf4986a1e18c570600cab0101000000000000908e3d4fb753d501669921e98c449f240000000002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50106000400020000000800300030000000000000000100000000200000f709fbc26afc6b10f259990a0d52b750bdf52ac081e50e05bd8e5b7c2cc4773e0a0010000000000000000000000000000000000009002a005400450052004d005300520056002f00310030002e003100360031002e003100370037002e0038003300000000000000000000000000c45115d42f73fac9522c4f5efeaccaf3a3320430010000003fc0504ff20375d000000000928ea327764e838d7a00dc499898e47f3e18b4e59e38feee09e0f516ea5bd00ca5220420e50faca0b401a6e585727dbc6436231e79d000d113d21809e8ba7e6f7b26543c'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l
        assert(z.size() == z.source.size())
        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        expected = {
            'LmChallengeResponseFields': '000000000000000000000000000000000000000000000000',
            'NtChallengeResponseFields': '9ebe92602c8cf4986a1e18c570600cab0101000000000000908e3d4fb753d501669921e98c449f240000000002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50106000400020000000800300030000000000000000100000000200000f709fbc26afc6b10f259990a0d52b750bdf52ac081e50e05bd8e5b7c2cc4773e0a0010000000000000000000000000000000000009002a005400450052004d005300520056002f00310030002e003100360031002e003100370037002e003800330000000000',
            'DomainNameFields': '4400450053004b0054004f0050002d00370031004d003600440045004d00',
            'UserNameFields': '41004e0046004c0041004e004e004500',
            'WorkstationFields': '4400450053004b0054004f0050002d00370031004d003600440045004d00',
            'EncryptedRandomSessionKeyFields': 'c45115d42f73fac9522c4f5efeaccaf3',
        }

        for name, item in nlmsg['messagefields'].enumerate():
            value = fromhex(expected[name])
            assert(item['BufferOffset'].d.li.serialize() == fromhex(expected[name]))
        assert(z.serialize() == z.source.value)
    test_decode_nlmp_messagefields_1()

    def test_decode_nlmp_messagefields_2():
        data = '30820287a003020106a1820226308202223082021ea082021a048202164e544c4d535350000300000018001800a40000004a014a01bc0000001e001e005800000010001000760000001e001e00860000001000100006020000358288e20a00cb490000000f1e8f34474eb81d34c93de8ac22879f874400450053004b0054004f0050002d00370031004d003600440045004d0041004e0046004c0041004e004e0045004400450053004b0054004f0050002d00370031004d003600440045004d000000000000000000000000000000000000000000000000009ebe92602c8cf4986a1e18c570600cab0101000000000000908e3d4fb753d501669921e98c449f240000000002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50106000400020000000800300030000000000000000100000000200000f709fbc26afc6b10f259990a0d52b750bdf52ac081e50e05bd8e5b7c2cc4773e0a0010000000000000000000000000000000000009002a005400450052004d005300520056002f00310030002e003100360031002e003100370037002e0038003300000000000000000000000000c45115d42f73fac9522c4f5efeaccaf3a3320430010000003fc0504ff20375d000000000928ea327764e838d7a00dc499898e47f3e18b4e59e38feee09e0f516ea5bd00ca5220420e50faca0b401a6e585727dbc6436231e79d000d113d21809e8ba7e6f7b26543c'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        assert(z['value'][0]['value']['Version'].serialize() == b'\2\1\6')
        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        authenticate = nlmp.AUTHENTICATE_MESSAGE().alloc(NegotiateFlags=dict(
            NEGOTIATE_56=1, NEGOTIATE_KEY_EXCH=1, NEGOTIATE_128=1,
            NEGOTIATE_VERSION=1, NEGOTIATE_TARGET_INFO=1, NEGOTIATE_EXTENDED_SESSIONSECURITY=1,
            NEGOTIATE_ALWAYS_SIGN=1, NEGOTIATE_NTLM=1, NEGOTIATE_SEAL=1, NEGOTIATE_SIGN=1,
            REQUEST_TARGET=1, NEGOTIATE_UNICODE=1,
        )).set(
            Version=dict(ProductMajorVersion=10, ProductBuild=18891, NTLMRevisionCurrent='W2K3'),
            MIC=0x879f8722ace83dc9341db84e47348f1e,
        )

        lm = nlmp.LMv2_RESPONSE().a
        authenticate['LmChallengeResponseFields'].set(Length=lm.size(), MaximumLength=lm.size())

        res = []
        res.append(nlmp.AvNbDomainName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvNbComputerName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsDomainName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsComputerName().set(u'DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvTimestamp().a.set(dwLowDateTime=1329434256, dwHighDateTime=30757815))
        res.append(nlmp.AvFlags().a.set(Flags=dict(HasMessageIntegrity=1)))
        res.append(nlmp.AvSingleHost().alloc(CustomData=0x0000200000000001 , MachineID=0x3e77c42c7c5b8ebd050ee581c02af5bd50b7520d0a9959f2106bfc6ac2fb09f7))
        res.append(nlmp.AvChannelBindings().a)
        res.append(nlmp.AvTargetName().set(u'TERMSRV/10.161.177.83', retain=False))
        res.append(nlmp.AvEOL().a)
        pairs = nlmp.AV_PAIRs().alloc([nlmp.AV_PAIR().alloc(Value=item) for item in res])

        nt = nlmp.NTLMv2_RESPONSE().alloc(Response=0xab0c6070c5181e6a98f48c2c6092be9e, ClientChallenge=dict(
            RespType=1, HiRespType=1, TimeStamp=0x1d553b74f3d8e90, ChallengeFromClient=0x249f448ce9219966,
            AvPairs=pairs,
        ))
        authenticate['NtChallengeResponseFields'].set(Length=nt.size(), MaximumLength=nt.size())

        #print(nlmsg['messagefields']['domainnamefields']['bufferoffset'].d.l)
        domainname = nlmp.PayloadString().alloc(string=pstr.wstring().set(u'DESKTOP-71M6DEM', retain=False))
        authenticate['DomainNameFields'].set(Length=domainname.size(), MaximumLength=domainname.size())

        #print(nlmsg['messagefields']['usernamefields']['bufferoffset'].d.l)
        username = nlmp.PayloadString().alloc(string=pstr.wstring().set(u'ANFLANNE', retain=False))
        authenticate['UserNameFields'].set(Length=username.size(), MaximumLength=username.size())

        #print(nlmsg['messagefields']['workstationfields']['bufferoffset'].d.l)
        workstation = nlmp.PayloadString().alloc(string=pstr.wstring().set(u'DESKTOP-71M6DEM', retain=False))
        authenticate['WorkstationFields'].set(Length=workstation.size(), MaximumLength=workstation.size())

        #print(nlmsg['messagefields']['encryptedrandomsessionkeyfields']['bufferoffset'].d.l)
        sessionkey = nlmp.SessionKey().alloc(session_key=pint.uint_t(length=0x10).set(0xf3caacfe5e4f2c52c9fa732fd41551c4))
        authenticate['EncryptedRandomSessionKeyFields'].set(Length=sessionkey.size(), MaximumLength=sessionkey.size())

        challenge, targetname, targetinfo = make_challenge()

        msg = nlmp.Message().alloc(MessageFields=challenge)
        lm_offset = msg['MessagePayload'].append(lm)
        nt_offset = msg['MessagePayload'].append(nt)
        domainname_offset = msg['MessagePayload'].append(domainname)
        username_offset = msg['MessagePayload'].append(username)
        workstation_offset = msg['MessagePayload'].append(workstation)
        sessionkeyoffset = msg['MessagePayload'].append(sessionkey)
        msg['MessageFields']['TargetNameFields']['BufferOffset'].reference(targetname)
    test_decode_nlmp_messagefields_2()
