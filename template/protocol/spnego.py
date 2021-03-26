import ptypes, protocol.ber as ber, protocol.nlmp as nlmp
from ptypes import *

SPNEGO = ber.Protocol.copy(recurse=True)
Context = SPNEGO.lookup(ber.Context.Class)

class MechType(ber.SEQUENCE):
    def iterate(self):
        for item in self:
            if isinstance(item['value'], ber.OBJECT_IDENTIFIER):
                yield item['value']
            else:
                yield item['value']
            continue
        return

class MechTypeList(ber.SEQUENCE):
    type = Context, 0
    _fields_ = [
        (MechType, 'mechTypeList'),
        (ber.OBJECT_IDENTIFIER, 'mechType'),
    ]

    def iterate(self):
        if self.has('mechType'):
            yield self['mechType']['value']
        if self.has('mechTypeList'):
            for item in self['mechTypeList']['value'].iterate():
                yield item
            return
        return

class ContextFlags(ber.BITSTRING):
    type = Context, 1

class MechanismToken(ber.Constructed):
    _fields_ = [
        (dyn.clone(nlmp.Message, type=ber.OCTETSTRING.type), 'token'),
    ]

class NegTokenInit(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(MechTypeList, type=(Context, 0)), 'mechTypes'),
        (dyn.clone(ContextFlags, type=(Context, 1)), 'reqFlags'),
        (dyn.clone(MechanismToken, type=(Context, 2)), 'mechToken'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 3)), 'mechListMIC'),
    ]

class GeneralString(ber.OCTETSTRING): pass

class NegHints(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(GeneralString, type=(Context, 0)), 'hintName'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 1)), 'hintAddress'),
    ]

class NegTokenInit2(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(MechTypeList, type=(Context, 0)), 'mechTypes'),
        (dyn.clone(ContextFlags, type=(Context, 1)), 'reqFlags'),
        (dyn.clone(MechanismToken, type=(Context, 2)), 'mechToken'),
        (dyn.clone(NegHints, type=(Context, 3)), 'negHints'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 4)), 'mechListMIC'),
    ]

class NegTokenInitContext(ber.SEQUENCE):
    _fields_ = [
        #(NegTokenInit, 'context'),
        (NegTokenInit2, 'context'),
    ]

class NegotiationState(ber.ENUMERATED):
    _values_ = [
        ('accept-completed', 0),
        ('accept-incomplete', 1),
        ('reject', 2),
        ('reject-mic', 3),
    ]

class NegotiationStateCons(ber.Constructed):
    _fields_ = [
        (NegotiationState, 'state'),
    ]

class NegTokenResp(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(NegotiationStateCons, type=(Context, 0)), 'negState'),
        (dyn.clone(MechTypeList, type=(Context, 1)), 'supportedMech'),
        (dyn.clone(MechanismToken, type=(Context, 2)), 'responseToken'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 3)), 'mechListMIC'),
    ]

class NegTokenRespContext(ber.SEQUENCE):
    _fields_ = [
        (NegTokenResp, 'context'),
    ]

@SPNEGO.Application.define
class NegotiationToken(ber.SEQUENCE):
    tag = 0
    _fields_ = [
        (ber.OBJECT_IDENTIFIER, 'securityMechanism'),
        (dyn.clone(NegTokenInitContext, type=(Context, 0)), 'negTokenInit'),
        (dyn.clone(NegTokenRespContext, type=(Context, 1)), 'negTokenResp'),
    ]

class Packet(ber.Packet):
    Protocol = SPNEGO
    def __object__(self, klasstag):
        return NegTokenRespContext if self.Tag() == 1 else NegotiationToken

if __name__ == '__main__':
    import importlib
    import sys, ptypes, protocol.ber as ber, protocol.spnego as spnego
    #importlib.reload(spnego.ber)
    importlib.reload(spnego)

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex
    data = []
    data.append(fromhex('604806062b0601050502a03e303ca00e300c060a2b06010401823702020aa22a04284e544c4d53535000010000001582086200000000280000000000000028000000060100000000000f'))
    data.append(fromhex('a182010b30820107a0030a0101a10c060a2b06010401823702020aa281f10481ee4e544c4d53535000020000001e001e003800000015828a6299f54405a8a793e2000000000000000098009800560000000a00ab3f0000000f560041004700520041004e0054002d004e0038003900430031004600330002001e00560041004700520041004e0054002d004e0038003900430031004600330001001e00560041004700520041004e0054002d004e0038003900430031004600330004001e00560041004700520041004e0054002d004e0038003900430031004600330003001e00560041004700520041004e0054002d004e0038003900430031004600330007000800645c8e69911ad70100000000'))
    data.append(fromhex('a18201f8308201f4a28201dc048201d84e544c4d535350000300000018001800580000003c013c01700000000a000a00ac01000008000800b60100000a000a00be01000010001000c801000015820862060100000000000f464bcb2f406aa4497382acba3f21709600000000000000000000000000000000000000000000000026f0bdfb18a8125594be797ce25095e40101000000000000645c8e69911ad701d1f37eb9edb78dca0000000002001e00560041004700520041004e0054002d004e0038003900430031004600330001001e00560041004700520041004e0054002d004e0038003900430031004600330004001e00560041004700520041004e0054002d004e0038003900430031004600330003001e00560041004700520041004e0054002d004e0038003900430031004600330007000800645c8e69911ad701060004000200000008003000300000000000000000000000000000007e665b88158c4d42eea4f77717498d90eaabdbf1699579f8f650a6a35948635b0a001000000000000000000000000000000000000900240063006900660073002f003100370032002e00320032002e00320032002e0031003200380000000000530041004d004200410075007300650072004500350035003700300032824f18b392a61f6bc1c7b9d4179f17a312041001000000c40f8cea64e0e56400000000'))
    data.append(fromhex('604806062b0601050502a03e303ca00e300c060a2b06010401823702020aa22a04284e544c4d53535000010000001582086200000000280000000000000028000000060100000000000f'))
    data.append(fromhex('a182010b30820107a0030a0101a10c060a2b06010401823702020aa281f10481ee4e544c4d53535000020000001e001e003800000015828a621a0af3f290bb80c3000000000000000098009800560000000a00ab3f0000000f560041004700520041004e0054002d004e0038003900430031004600330002001e00560041004700520041004e0054002d004e0038003900430031004600330001001e00560041004700520041004e0054002d004e0038003900430031004600330004001e00560041004700520041004e0054002d004e0038003900430031004600330003001e00560041004700520041004e0054002d004e003800390043003100460033000700080026be9069911ad70100000000'))
    data.append(fromhex('a16e306ca26a04684e544c4d5353500003000000000000005800000000000000580000000000000058000000000000005800000000000000580000001000100058000000158a0062060100000000000f7d521c9e7262eaf2763a33721990755673fcdfd4e99f1b5786975ef2cd9c8282'))
    data.append(fromhex('604806062b0601050502a03e303ca00e300c060a2b06010401823702020aa22a04284e544c4d53535000010000001582086200000000280000000000000028000000060100000000000f'))
    data.append(fromhex('a182010b30820107a0030a0101a10c060a2b06010401823702020aa281f10481ee4e544c4d53535000020000001e001e003800000015828a62bcae443094508191000000000000000098009800560000000a00ab3f0000000f560041004700520041004e0054002d004e0038003900430031004600330002001e00560041004700520041004e0054002d004e0038003900430031004600330001001e00560041004700520041004e0054002d004e0038003900430031004600330004001e00560041004700520041004e0054002d004e0038003900430031004600330003001e00560041004700520041004e0054002d004e0038003900430031004600330007000800c4dc356c911ad70100000000'))
    data.append(fromhex('a18201f8308201f4a28201dc048201d84e544c4d535350000300000018001800580000003c013c01700000000a000a00ac01000008000800b60100000a000a00be01000010001000c801000015820862060100000000000f869edfa10f0714da527caa5da9caf5af000000000000000000000000000000000000000000000000f8e5942603c06bdd99642fb0413c97cc0101000000000000c4dc356c911ad70169f6d67314e243590000000002001e00560041004700520041004e0054002d004e0038003900430031004600330001001e00560041004700520041004e0054002d004e0038003900430031004600330004001e00560041004700520041004e0054002d004e0038003900430031004600330003001e00560041004700520041004e0054002d004e0038003900430031004600330007000800c4dc356c911ad70106000400020000000800300030000000000000000000000000000000b756d72e9ea5efcd0c3499af097b9a458e415a2100bf8f22c2ef4002c2f4a4770a001000000000000000000000000000000000000900240063006900660073002f003100370032002e00320032002e00320032002e0031003200380000000000530041004d0042004100750073006500720045003500350037003000025c542d1920ccaa153d4376c65949e5a3120410010000004ea6d81de60bbda700000000'))
    data.append(fromhex('a11b3019a0030a0100a3120410010000007c3cf99405b02f5500000000'))

    z = spnego.Packet(source=ptypes.prov.bytes(data[0]))
    z=z.l
    if z['value'].has('securityMechanism'):
        print(z['value']['securityMechanism']['value'])
    print(z['value']['negtokeninit'])
    print(z['value']['negtokeninit']['value']['context'])
    if z['value']['negtokeninit']['value']['context']['value'].has('mechTypes'):
        for item in z['value']['negTokenInit']['value']['context']['value']['mechTypes']['value'].iterate():
            print(item)
    print(z['value']['negTokenInit']['value']['context']['value']['mechToken']['value'])

    nlmsg = z['value']['negTokenInit']['value']['context']['value']['mechToken']['value']['token']['value']
    print(nlmsg['MessageFields'])
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    print(nlmsg['messagefields']['DomainNameFields']['bufferoffset'].d.l)
    print(nlmsg['messagefields']['WorkstationFields']['bufferoffset'].d.l)

    z = spnego.Packet(source=ptypes.prov.bytes(data[1]))
    z=z.l
    print(z['value']['context'])
    if z['value']['context']['value'].has('supportedMech'):
        for item in z['value']['context']['value']['supportedMech']['value'].iterate():
            print(item)
    print(z['value']['context']['value']['negState']['value']['state'])
    print(z['value']['context']['value']['responseToken'])

    nlmsg = z['value']['context']['value']['responseToken']['value']['token']['value']
    print(nlmsg['MessageFields'])
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    nlmsg['messagefields']['targetnamefields']['bufferoffset'].d.l
    ti = nlmsg['messagefields']['targetinfofields']['bufferoffset'].d.l
    for item in ti['pairs']:
        print(item['Avid'].str(), item['value'].summary())

    z = spnego.Packet(source=ptypes.prov.bytes(data[2]))
    z=z.l
    print(z['value']['context'])
    if z['value']['context']['value'].has('mechListMIC'):
        for item in z['value']['context']['value']['mechListMIC']['value']:
            print(item['value'].summary())

    print(z['value']['context']['value']['mechListMIC']['value'][0]['value'].summary())
    print(z['value']['context']['value']['responseToken']['value'])

    nlmsg = z['value']['context']['value']['responseToken']['value']['token']['value']
    print(nlmsg['MessageFields'])
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    print(nlmsg['MessageFields']['MIC'].summary())
    nlmsg['messagefields']['LmChallengeResponseFields']['bufferoffset'].d.l
    resp = nlmsg['messagefields']['NtChallengeResponseFields']['bufferoffset'].d.l
    resp['clientchallenge']
    for item in resp['clientchallenge']['avpairs']:
        print(item['Avid'].str(), item['value'].summary())

    nlmsg['messagefields']['DomainNameFields']['bufferoffset'].d.l
    nlmsg['messagefields']['UserNameFields']['bufferoffset'].d.l
    nlmsg['messagefields']['WorkstationFields']['bufferoffset'].d.l
    nlmsg['messagefields']['EncryptedRandomSessionKeyFields']['bufferoffset'].d.l

    z = spnego.Packet(source=ptypes.prov.bytes(data[3]))
    z=z.l
    if z['value'].has('securityMechanism'):
        print(z['value']['securityMechanism']['value'])
    print(z['value']['negTokenInit'])
    print(z['value']['negTokenInit']['value']['context'])
    if z['value']['negTokenInit']['value']['context']['value'].has('mechTypes'):
        for item in z['value']['negTokenInit']['value']['context']['value']['mechTypes']['value'].iterate():
            print(item)
    print(z['value']['negTokenInit']['value']['context']['value']['mechToken']['value'])

    nlmsg = (z['value']['negTokenInit']['value']['context']['value']['mechToken']['value']['token']['value'])
    nlmsg['messagefields']
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    nlmsg['messagefields']['domainnamefields']
    nlmsg['messagefields']['workstationfields']

    z = spnego.Packet(source=ptypes.prov.bytes(data[4]))
    z=z.l
    if z['value']['context']['value'].has('supportedMech'):
        for item in z['value']['context']['value']['supportedMech']['value'].iterate():
            print(item)
    print(z['value']['context']['value']['negState']['value']['state'])
    nlmsg = (z['value']['context']['value']['responseToken']['value']['token']['value'])
    nlmsg['messagefields']
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    nlmsg['messagefields']['targetnamefields']['bufferoffset'].d.l
    ti = nlmsg['messagefields']['targetinfofields']['bufferoffset'].d.l
    for item in ti['pairs']:
        print(item['Avid'].str(), item['value'].summary())

    z = spnego.Packet(source=ptypes.prov.bytes(data[5]))
    z=z.l
    if z['value']['context']['value'].has('supportedMech'):
        for item in z['value']['context']['value']['supportedMech']['value'].iterate():
            print(item)
    print(z['value']['context']['value']['responseToken'])

    nlmsg = (z['value']['context']['value']['responseToken']['value']['token']['value'])
    nlmsg['messagefields']
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    print(nlmsg['MessageFields']['MIC'].summary())
    nlmsg['messagefields']['encryptedrandomsessionkeyfields']['bufferoffset'].d.l

    z = spnego.Packet(source=ptypes.prov.bytes(data[6]))
    z=z.l
    if z['value'].has('securityMechanism'):
        print(z['value']['securityMechanism']['value'])
    print(z['value']['negTokenInit'])
    print(z['value']['negTokenInit']['value']['context'])
    if z['value']['negTokenInit']['value']['context']['value'].has('mechTypes'):
        for item in z['value']['negTokenInit']['value']['context']['value']['mechTypes']['value'].iterate():
            print(item)
    print(z['value']['negTokenInit']['value']['context']['value']['mechToken'])

    nlmsg = (z['value']['negTokenInit']['value']['context']['value']['mechToken']['value']['token']['value'])
    nlmsg['messagefields']
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]

    z = spnego.Packet(source=ptypes.prov.bytes(data[7]))
    z=z.l
    print(z['value']['context'])
    if z['value']['context']['value'].has('supportedMech'):
        for item in z['value']['context']['value']['supportedMech']['value'].iterate():
            print(item)
    print(z['value']['context']['value']['negState']['value']['state'])
    print(z['value']['context']['value']['responseToken'])

    nlmsg = (z['value']['context']['value']['responseToken']['value']['token']['value'])
    nlmsg['messagefields']
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    nlmsg['messagefields']['targetnamefields']['bufferoffset'].d.l
    ti = nlmsg['messagefields']['targetinfofields']['bufferoffset'].d.l
    for item in ti['pairs']:
        print(item['Avid'].str(), item['value'].summary())

    z = spnego.Packet(source=ptypes.prov.bytes(data[8]))
    z=z.l
    print(z['value']['context'])
    if z['value']['context']['value'].has('mechListMIC'):
        for item in z['value']['context']['value']['mechListMIC']['value']:
            print(item['value'].summary())
    print(z['value']['context']['value']['responseToken'])

    nlmsg = (z['value']['context']['value']['responseToken']['value']['token']['value'])
    print(nlmsg['MessageFields'])
    [item for item in nlmsg['messagefields']['negotiateflags'] if nlmsg['messagefields']['negotiateflags'][item]]
    print(nlmsg['MessageFields']['MIC'].summary())
    nlmsg['messagefields']['LmChallengeResponseFields']['bufferoffset'].d.l
    resp = nlmsg['messagefields']['NtChallengeResponseFields']['bufferoffset'].d.l
    resp['clientchallenge']
    for item in resp['clientchallenge']['avpairs']:
        print(item['Avid'].str(), item['value'].summary())

    nlmsg['messagefields']['DomainNameFields']['bufferoffset'].d.l
    nlmsg['messagefields']['UserNameFields']['bufferoffset'].d.l
    nlmsg['messagefields']['WorkstationFields']['bufferoffset'].d.l
    nlmsg['messagefields']['EncryptedRandomSessionKeyFields']['bufferoffset'].d.l

    z = spnego.Packet(source=ptypes.prov.bytes(data[9]))
    z=z.l
    print(z['value']['context'])
    print(z['value']['context']['value']['negState']['value']['state'])
    if z['value']['context']['value'].has('mechListMIC'):
        for item in z['value']['context']['value']['mechListMIC']['value']:
            print(item['value'].summary())

    # not sure where this hex came from
    data = fromhex('6082015d06062b0601050502a08201513082014da01a3018060a2b06010401823702021e060a2b06010401823702020aa28201010481fe4e45474f4558545301000000000000006000000070000000cffa11765e12599a347d766852bfce7097458710bb8242b4c7dfbad2da897aa311a7d868463430952562dc13c554f2010000000000000000600000000100000000000000000000005c33530deaf90d4db2ec4ae3786ec3084e45474f455854530300000001000000400000008e000000cffa11765e12599a347d766852bfce705c33530deaf90d4db2ec4ae3786ec308400000004e000000304ca04a3048302a80283026312430220603550403131b584d4c50726f766964657220496e7465726d656469617465204341301a80183016311430120603550403130b584d4c50726f7669646572a32a3028a0261b246e6f745f646566696e65645f696e5f5246433431373840706c656173655f69676e6f7265')
