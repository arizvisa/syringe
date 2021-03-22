import ptypes
from . import ber, nlmp
from ptypes import *

class TSVersion(ber.SEQUENCE):
    tag = 0
    _fields_ = [
        (ber.INTEGER, 'Version'),
    ]

class NegoToken(ber.SEQUENCE):
    tag = 0
    _fields_ = [
        (nlmp.Message, 'negoMessage'),
    ]

class NegoDataSequenceOfSequence(ber.SEQUENCE):
    _fields_ = [
        (0, NegoToken, 'negoToken'),
    ]

class NegoDataSequence(ber.SEQUENCE):
    _fields_ = [
        (NegoDataSequenceOfSequence, 'Messages'),
    ]

class NegoData(ber.SEQUENCE):
    tag = 1
    _fields_ = [
        (NegoDataSequence, 'Data'),
    ]

class AuthInfo(ber.SEQUENCE):
    tag = 2
    _fields_ = [
        (ber.OCTETSTRING, 'Credentials'),
    ]

class PubKeyAuth(ber.SEQUENCE):
    tag = 3
    _fields_ = [
        (ber.OCTETSTRING, 'pubKeyAuth'),
    ]

class ErrorCode(ber.INTEGER):
    tag = 4

class ClientNonce(ber.SEQUENCE):
    tag = 5
    _fields_ = [
        (ber.OCTETSTRING, 'clientNonce'),
    ]

class TSRequest(ber.SEQUENCE):
    _fields_ = [
        (0, TSVersion, 'version'),
        (1, NegoData, 'negoData'),
        (2, AuthInfo, 'authInfo'),
        (3, PubKeyAuth, 'pubKeyAuth'),
        (4, ErrorCode, 'errorCode'),
        (5, ClientNonce, 'clientNonce'),
    ]

class TSPasswordCreds(ber.SEQUENCE):
    _fields_ = [
        (0, ber.OCTETSTRING, 'domainName'),
        (1, ber.OCTETSTRING, 'userName'),
        (2, ber.OCTETSTRING, 'password'),
    ]

class TSCspDataDetail(ber.SEQUENCE):
    _fields_ = [
        (0, ber.INTEGER, 'keySpec'),
        (1, ber.OCTETSTRING, 'cardName'),
        (2, ber.OCTETSTRING, 'readerName'),
        (3, ber.OCTETSTRING, 'containerName'),
        (4, ber.OCTETSTRING, 'cspName'),
    ]

class TSSmartCardCreds(ber.SEQUENCE):
    _fields_ = [
        (0, ber.OCTETSTRING, 'pin'),
        (1, TSCspDataDetail, 'cspData'),
        (2, ber.OCTETSTRING, 'userHint'),
        (3, ber.OCTETSTRING, 'domainHint'),
    ]

class TSRemoteGuardPackageCred(ber.SEQUENCE):
    _fields_ = [
        (0, ber.OCTETSTRING, 'packageName'),
        (1, ber.OCTETSTRING, 'credBuffer'),
    ]

class TSRemoteGuardCreds(ber.SEQUENCE):
    class _supplementalCred(ber.SEQUENCE):
        # FIXME: this isn't a sequence of actual fields, but is composed of an
        #        array of TSRemoteGuardPackageCred elements. this can be solved
        #        either by reimplementing SEQUENCE._object_ or by adding support
        #        to ber.SEQUENCE for hardcoding an element type.
        _fields_ = TSRemoteGuardPackageCred

    _fields_ = [
        (0, TSRemoteGuardPackageCred, 'logonCred'),
        (1, _supplementalCred, 'supplementalCred'),
    ]

class TSCredentials(ber.SEQUENCE):
    _fields_ = [
        (0, ber.INTEGER, 'credType'),
        (1, ber.OCTETSTRING, 'credentials'),
    ]

class Packet(ber.Packet):
    _object_ = TSRequest

if __name__ == '__main__':
    import sys, operator, ptypes, protocol.ber as ber, protocol.credssp as credssp, protocol.nlmp as nlmp
    from ptypes import *
    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    if False:
        res = '60 82 01 5d 06 06 2b 06 01 05 05 02 a0 82 01 51 30 82 01 4d a0 1a 30 18 06 0a 2b 06 01 04 01 82 37 02 02 1e 06 0a 2b 06 01 04 01 82 37 02 02 0a a2 82 01 01 04 81 fe 4e 45 47 4f 45 58 54 53 01 00 00 00 00 00 00 00 60 00 00 00 70 00 00 00 cf fa 11 76 5e 12 59 9a 34 7d 76 68 52 bf ce 70 97 45 87 10 bb 82 42 b4 c7 df ba d2 da 89 7a a3 11 a7 d8 68 46 34 30 95 25 62 dc 13 c5 54 f2 01 00 00 00 00 00 00 00 00 60 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 5c 33 53 0d ea f9 0d 4d b2 ec 4a e3 78 6e c3 08 4e 45 47 4f 45 58 54 53 03 00 00 00 01 00 00 00 40 00 00 00 8e 00 00 00 cf fa 11 76 5e 12 59 9a 34 7d 76 68 52 bf ce 70 5c 33 53 0d ea f9 0d 4d b2 ec 4a e3 78 6e c3 08 40 00 00 00 4e 00 00 00 30 4c a0 4a 30 48 30 2a 80 28 30 26 31 24 30 22 06 03 55 04 03 13 1b 58 4d 4c 50 72 6f 76 69 64 65 72 20 49 6e 74 65 72 6d 65 64 69 61 74 65 20 43 41 30 1a 80 18 30 16 31 14 30 12 06 03 55 04 03 13 0b 58 4d 4c 50 72 6f 76 69 64 65 72 a3 2a 30 28 a0 26 1b 24 6e 6f 74 5f 64 65 66 69 6e 65 64 5f 69 6e 5f 52 46 43 34 31 37 38 40 70 6c 65 61 73 65 5f 69 67 6e 6f 72 65   '
        res = '30 82 01 0f a0 03 02 01-02 a1 82 01 06 04 82 01 02 30 81 ff a0 1a 04 18-62 00 62 00 62 00 62 00 62 00 62 00 62 00 62 00-62 00 62 00 62 00 62 00 a1 81 e0 30 81 dd a0 03-02 01 01 a2 2e 04 2c 4f 00 4d 00 4e 00 49 00 4b-00 45 00 59 00 20 00 43 00 61 00 72 00 64 00 4d-00 61 00 6e 00 20 00 33 00 78 00 32 00 31 00 20-00 30 00 a3 50 04 4e 6c 00 65 00 2d 00 4d 00 53-00 53 00 6d 00 61 00 72 00 74 00 63 00 61 00 72-00 64 00 55 00 73 00 65 00 72 00 2d 00 38 00 62-00 64 00 61 00 30 00 31 00 39 00 66 00 2d 00 31-00 32 00 36 00 36 00 2d 00 2d 00 35 00 33 00 32-00 36 00 38 00 a4 54 04 52 4d 00 69 00 63 00 72-00 6f 00 73 00 6f 00 66 00 74 00 20 00 42 00 61-00 73 00 65 00 20 00 53 00 6d 00 61 00 72 00 74-00 20 00 43 00 61 00 72 00 64 00 20 00 43 00 72-00 79 00 70 00 74 00 6f 00 20 00 50 00 72 00 6f-00 76 00 69 00 64 00 65 00 72 00'
        data = ''.join(filter(lambda char: char not in ' -\r\n', res))
        #z = ber.Packet(source=ptypes.prov.string(fromhex(data)))
        z = credssp.Packet(source=ptypes.prov.string(fromhex(data)))
        z=z.l
        print(z['value'][0]['value'])
        print(z['value'][0]['value'][0])
        print(z['value'][1])
        print(z['value'][1]['value'][0])
        print(z['value'][1]['value'][0]['value'].hexdump())

        b = z['value'][1]['value'][0]['value'].cast(ber.Packet)
        print(b['value'][0]['value'][0]['value'].hexdump())
        print(b['value'][1]['value'][0]['value'][0]['value'][0]['value'])
        print(b['value'][1]['value'][0]['value'][1]['value'][0]['value'].hexdump())
        print(b['value'][1]['value'][0]['value'][2]['value'][0]['value'].hexdump())
        print(b['value'][1]['value'][0]['value'][3]['value'][0]['value'].hexdump())

        print(z['value'][1]['value'][0]['value'].cast(ber.Packet))
        print(z['value'][1]['value'][0]['value'].hexdump())
        assert(z.source.size() == z.size())

    def test_credssp_encode_tsversion():
        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(2))
        assert(tsversion.serialize() == b'\2\1\2')

        z = credssp.Packet().alloc(Value=tsversion)
        assert(z.serialize() == b'\x30\3\2\1\2')

    def test_credssp_decode_path():
        data = '3037a003020106a130302e302ca02a04284e544c4d5353500001000000b78208e2000000000000000000000000000000000a00cb490000000f'
        z = credssp.Packet(source=ptypes.prov.string(fromhex(data)))
        z=z.l

        #print(z['value'][0]['value']['Version']['value'])
        nlmsg = z['value'][1]['value'][0]['value'][0]['value'][0]['value']['negotoken']['value']

        #print(a['messagefields'])
        assert(z.size() == z.source.size())
        assert(isinstance(nlmsg, nlmp.Message))

    def test_credssp_token():
        data = '3037a003020106a130302e302ca02a04284e544c4d5353500001000000b78208e2000000000000000000000000000000000a00cb490000000f'
        z = credssp.Packet(source=ptypes.prov.string(fromhex(data))).l
        msg = '4e544c4d5353500001000000b78208e2000000000000000000000000000000000a00cb490000000f'

        assert(isinstance(z['value']['version']['value'], credssp.TSVersion))
        assert(isinstance(z['value']['negoData']['value'], credssp.NegoData))
        data = z['value']['negodata']['value']
        assert(isinstance(data[0]['value'][0]['value'][0]['value'], credssp.NegoToken))
        assert(data[0]['value'][0]['value'][0]['value'][0]['value'].serialize() == fromhex(msg))

    def test_credssp_encode_token():
        data = '3037a003020106a130302e302ca02a04284e544c4d5353500001000000b78208e2000000000000000000000000000000000a00cb490000000f'
        z = credssp.Packet(source=ptypes.prov.string(fromhex(data))).l

        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(6))
        assert(z['value']['version']['value'].serialize() == tsversion.serialize())

        nlmsg = z['value']['negoData']['value']['data']['value']['messages']['value']['negoToken']['value']['Message']['value'].copy(type=(ber.Protocol.Universal.Class, ber.OCTETSTRING.tag))
        negotoken = credssp.NegoToken().alloc(negoMessage=nlmsg)
        negodata_seq_seq = credssp.NegoDataSequenceOfSequence().alloc([credssp.Packet().alloc(Value=negotoken)])
        negodata_seq = credssp.NegoDataSequence().alloc([credssp.Packet().alloc(Value=negodata_seq_seq)])
        negodata = credssp.NegoData().alloc([credssp.Packet().alloc(Value=negodata_seq)])

        #tsrequest = credssp.TSRequest().alloc([credssp.Packet().alloc(Value=item) for item in [tsversion, negodata]])
        tsrequest = credssp.TSRequest().alloc(version=tsversion, negoData=negodata)
        cssp = credssp.Packet().alloc(Value=tsrequest)

        assert(cssp['value']['version'].serialize() == z['value']['version'].serialize())
        assert(cssp.serialize() == z.serialize())

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

        res = pstr.wstring().set('DESKTOP-UAGCVKC', retain=False)
        targetname = nlmp.PayloadString().alloc(string=res)
        challenge['TargetNameFields'].set(Length=targetname.size(), MaximumLength=targetname.size())

        res = []
        res.append(nlmp.AvNbDomainName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvNbComputerName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsDomainName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsComputerName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvTimestamp().a.set(dwLowDateTime=1329434256, dwHighDateTime=30757815))
        res.append(nlmp.AvEOL().a)
        pairs = nlmp.AV_PAIRs().alloc([nlmp.AV_PAIR().alloc(Value=item) for item in res])
        targetinfo = nlmp.AV_PAIRs().alloc(pairs)
        challenge['TargetInfoFields'].set(Length=targetinfo.size(), MaximumLength=targetinfo.size())

        return challenge, targetname, targetinfo

    def test_encode_nlmp():
        data = '30820102a003020106a181fa3081f73081f4a081f10481ee4e544c4d53535000020000001e001e003800000035828ae2a326c589b91aacc7000000000000000098009800560000000a0063450000000f4400450053004b0054004f0050002d00550041004700430056004b00430002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50100000000'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        a = ber.Packet().l
        z = credssp.Packet()
        z=z.l
        a = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        challenge, targetname, targetinfo = make_challenge()

        msg = nlmp.Message().alloc(MessageFields=challenge)
        targetname_offset = msg['MessagePayload'].append(targetname)
        targetinfo_offset = msg['MessagePayload'].append(targetinfo)
        msg['MessageFields']['TargetNameFields']['BufferOffset'].reference(targetname)
        msg['MessageFields']['TargetInfoFields']['BufferOffset'].reference(targetinfo)

        assert(a.serialize() == msg.serialize())

    if True:
        print('-'*72)
        data = '30820102a003020106a181fa3081f73081f4a081f10481ee4e544c4d53535000020000001e001e003800000035828ae2a326c589b91aacc7000000000000000098009800560000000a0063450000000f4400450053004b0054004f0050002d00550041004700430056004b00430002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50100000000'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'][0]['value']['Version']['value'])
        a = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        print(a['messagefields'])
        assert(z.size() == z.source.size())

        for item in a['messagefields'].Fields():
            if not item['bufferoffset'].int(): continue
            print(item.name(), item['BufferOffset'].d.li.summary())

    if True:
        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(6))
        assert(z['value'][0]['value'].serialize() == tsversion.serialize())

        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value'].copy(type=(ber.Protocol.Universal.Class, ber.OCTETSTRING.tag))
        negotoken = credssp.NegoToken().alloc(negoMessage=nlmsg)
        negodata_seq_seq = credssp.NegoDataSequenceOfSequence().alloc([credssp.Packet().alloc(Value=negotoken)])
        negodata_seq = credssp.NegoDataSequence().alloc([credssp.Packet().alloc(Value=negodata_seq_seq)])
        negodata = credssp.NegoData().alloc([credssp.Packet().alloc(Value=negodata_seq)])

        tsrequest = ber.SEQUENCE().alloc([credssp.Packet().alloc(Value=item) for item in [tsversion, negodata]])
        cssp = credssp.Packet().alloc(Value=tsrequest)
        assert(cssp.serialize() == z.serialize())

    if True:
        print('-'*72)
        data = '30820287a003020106a1820226308202223082021ea082021a048202164e544c4d535350000300000018001800a40000004a014a01bc0000001e001e005800000010001000760000001e001e00860000001000100006020000358288e20a00cb490000000f1e8f34474eb81d34c93de8ac22879f874400450053004b0054004f0050002d00370031004d003600440045004d0041004e0046004c0041004e004e0045004400450053004b0054004f0050002d00370031004d003600440045004d000000000000000000000000000000000000000000000000009ebe92602c8cf4986a1e18c570600cab0101000000000000908e3d4fb753d501669921e98c449f240000000002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50106000400020000000800300030000000000000000100000000200000f709fbc26afc6b10f259990a0d52b750bdf52ac081e50e05bd8e5b7c2cc4773e0a0010000000000000000000000000000000000009002a005400450052004d005300520056002f00310030002e003100360031002e003100370037002e0038003300000000000000000000000000c45115d42f73fac9522c4f5efeaccaf3a3320430010000003fc0504ff20375d000000000928ea327764e838d7a00dc499898e47f3e18b4e59e38feee09e0f516ea5bd00ca5220420e50faca0b401a6e585727dbc6436231e79d000d113d21809e8ba7e6f7b26543c'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'][0]['value']['Version']['value'])
        a = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

        print(a['messagefields'])
        assert(z.size() == z.source.size())

        for item in a['messagefields'].Fields():
            if not item['bufferoffset'].int(): continue
            print(item.name(), item['BufferOffset'].d.li.summary())

    if True:
        print('-'*72)
        data = '30820287a003020106a1820226308202223082021ea082021a048202164e544c4d535350000300000018001800a40000004a014a01bc0000001e001e005800000010001000760000001e001e00860000001000100006020000358288e20a00cb490000000f1e8f34474eb81d34c93de8ac22879f874400450053004b0054004f0050002d00370031004d003600440045004d0041004e0046004c0041004e004e0045004400450053004b0054004f0050002d00370031004d003600440045004d000000000000000000000000000000000000000000000000009ebe92602c8cf4986a1e18c570600cab0101000000000000908e3d4fb753d501669921e98c449f240000000002001e004400450053004b0054004f0050002d00550041004700430056004b00430001001e004400450053004b0054004f0050002d00550041004700430056004b00430004001e004400450053004b0054004f0050002d00550041004700430056004b00430003001e004400450053004b0054004f0050002d00550041004700430056004b00430007000800908e3d4fb753d50106000400020000000800300030000000000000000100000000200000f709fbc26afc6b10f259990a0d52b750bdf52ac081e50e05bd8e5b7c2cc4773e0a0010000000000000000000000000000000000009002a005400450052004d005300520056002f00310030002e003100360031002e003100370037002e0038003300000000000000000000000000c45115d42f73fac9522c4f5efeaccaf3a3320430010000003fc0504ff20375d000000000928ea327764e838d7a00dc499898e47f3e18b4e59e38feee09e0f516ea5bd00ca5220420e50faca0b401a6e585727dbc6436231e79d000d113d21809e8ba7e6f7b26543c'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'][0]['value']['Version']['value'])
        a = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value']

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
        res.append(nlmp.AvNbDomainName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvNbComputerName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsDomainName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvDnsComputerName().set('DESKTOP-UAGCVKC', retain=False))
        res.append(nlmp.AvTimestamp().a.set(dwLowDateTime=1329434256, dwHighDateTime=30757815))
        res.append(nlmp.AvFlags().a.set(Flags=dict(HasMessageIntegrity=1)))
        res.append(nlmp.AvSingleHost().alloc(CustomData=0x0000200000000001 , MachineID=0x3e77c42c7c5b8ebd050ee581c02af5bd50b7520d0a9959f2106bfc6ac2fb09f7))
        res.append(nlmp.AvChannelBindings().a)
        res.append(nlmp.AvTargetName().set('TERMSRV/10.161.177.83', retain=False))
        res.append(nlmp.AvEOL().a)
        pairs = nlmp.AV_PAIRs().alloc([nlmp.AV_PAIR().alloc(Value=item) for item in res])

        nt = nlmp.NTLMv2_RESPONSE().alloc(Response=0xab0c6070c5181e6a98f48c2c6092be9e, ClientChallenge=dict(
            RespType=1, HiRespType=1, TimeStamp=0x1d553b74f3d8e90, ChallengeFromClient=0x249f448ce9219966,
            AvPairs=pairs,
        ))
        authenticate['NtChallengeResponseFields'].set(Length=nt.size(), MaximumLength=nt.size())

        print(a['messagefields']['domainnamefields']['bufferoffset'].d.l)
        domainname = nlmp.PayloadString().alloc(string=pstr.wstring().set('DESKTOP-71M6DEM', retain=False))
        authenticate['DomainNameFields'].set(Length=domainname.size(), MaximumLength=domainname.size())

        print(a['messagefields']['usernamefields']['bufferoffset'].d.l)
        username = nlmp.PayloadString().alloc(string=pstr.wstring().set('ANFLANNE', retain=False))
        authenticate['UserNameFields'].set(Length=username.size(), MaximumLength=username.size())

        print(a['messagefields']['workstationfields']['bufferoffset'].d.l)
        workstation = nlmp.PayloadString().alloc(string=pstr.wstring().set('DESKTOP-71M6DEM', retain=False))
        authenticate['WorkstationFields'].set(Length=workstation.size(), MaximumLength=workstation.size())

        print(a['messagefields']['encryptedrandomsessionkeyfields']['bufferoffset'].d.l)
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

    if True:
        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(6))
        print(z['value'][0]['value'].hexdump())
        print(tsversion.hexdump())

        nlmsg = z['value']['negoData']['value']['Data']['value']['Messages']['value']['negoToken']['value']['negoMessage']['value'].copy(type=(ber.Protocol.Universal.Class, ber.OCTETSTRING.tag))
        negotoken = credssp.NegoToken().alloc(negoMessage=nlmsg)
        negodata_seq_seq = credssp.NegoDataSequenceOfSequence().alloc([credssp.Packet().alloc(Value=negotoken)])
        negodata_seq = credssp.NegoDataSequence().alloc([credssp.Packet().alloc(Value=negodata_seq_seq)])
        negodata = credssp.NegoData().alloc([credssp.Packet().alloc(Value=negodata_seq)])

        signature = z['value'][2]['value']['pubKeyAuth']['value'].copy()
        pubkeyauth = credssp.PubKeyAuth().alloc(pubKeyAuth=signature)

        clientnonce = z['value'][3]['value'].copy()

        tsrequest = ber.SEQUENCE().alloc([credssp.Packet().alloc(Value=item) for item in [tsversion, negodata, pubkeyauth, clientnonce]])
        cssp = credssp.Packet().alloc(Value=tsrequest)
        assert cssp.serialize() == z.serialize()

    if True:
        print('-'*72)
        data = '3039a003020106a3320430010000006c21ea64533bfeb3000000005e004ea3b9c8d210230c8d45b147cfe50f86f954456022171371f877e6bfc260'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'][0]['value']['Version']['value'])
        print(z['value'][1]['value']['pubKeyAuth']['value'])

        if z.size() != z.source.size():
            raise AssertionError

    if True:
        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(6))
        print(z['value'][0]['value'].hexdump())
        print(tsversion.hexdump())

        signature = z['value'][1]['value']['pubKeyAuth']['value'].copy()
        pubkeyauth = credssp.PubKeyAuth().alloc(pubKeyAuth=signature)

        tsrequest = ber.SEQUENCE().alloc([credssp.Packet().alloc(Value=item) for item in [tsversion, pubkeyauth]])
        cssp = credssp.Packet().alloc(Value=tsrequest)
        assert cssp.serialize() == z.serialize()

    if True:
        print('-'*72)
        data = '305ea003020106a2570455010000003ba4b813060c896a010000006496f0b88995b70e63ca52bc1fa443fb09d843561a7f90ed37acf851188ebf043add1941e0becf9666628169fb057a573edaee6776c76912a40d09b296ac9595bc92212eac'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'][0]['value']['Version']['value'])
        print(z['value'][1]['value']['Credentials']['value'])

    if True:
        tsversion = credssp.TSVersion().alloc(Version=ber.INTEGER(length=1).set(6))
        print(z['value'][0]['value'].hexdump())
        print(tsversion.hexdump())

        credentials = z['value'][1]['value']['Credentials']['value'].copy()
        authinfo = credssp.AuthInfo().alloc(Credentials=credentials)

        tsrequest = ber.SEQUENCE().alloc([credssp.Packet().alloc(Value=item) for item in [tsversion, authinfo]])
        cssp = credssp.Packet().alloc(Value=tsrequest)
        assert cssp.serialize() == z.serialize()

    if True:
        print('-'*72)
        data = '00000000'
        ptypes.setsource(ptypes.prov.string(fromhex(data)))
        z = credssp.Packet()
        z=z.l

        print(z['value'].classname())

    if True:
        cssp = credssp.Packet().alloc(Value=ber.EOC)
        assert cssp.serialize() == z.serialize()
