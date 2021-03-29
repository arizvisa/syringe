import ptypes
from . import ber
from ptypes import *

Protocol = ber.Protocol.copy(recurse=True)
Context = Protocol.lookup(ber.Context.Class)

class AttributeType(ber.OBJECT_IDENTIFIER): pass
class AttributeValue(ber.PrintableString): pass
class AttributeTypeAndValue(ber.SEQUENCE):
    _fields_ = [
        (AttributeType, 'type'),
        (AttributeValue, 'value'),
    ]

class RelativeDistinguishedName(ber.SET):
    _fields_ = [
        (AttributeTypeAndValue, 'Item'),
    ]

class RDNSequence(RelativeDistinguishedName):
    _fields_ = []

class Name(ber.SEQUENCE):
    _fields_ = [
        (RDNSequence, 'rdnSequence'),
    ]

class Version(pint.enum, ber.INTEGER):
    _values_ = [
        ('v1', 0),
        ('v2', 1),
        ('v3', 2),
    ]

class Version_DEFAULT(ber.Constructed):
    _fields_ = [
        (Version, 'DEFAULT'),
    ]

class CertificateSerialNumber(ber.INTEGER):
    pass

class Time(ber.UTCTime):
    pass

class Validity(ber.SEQUENCE):
    _fields_ = [
        (Time, 'notBefore'),
        (Time, 'notAfter'),
    ]

class UniqueIdentifier(ber.BITSTRING):
    pass

class AlgorithmIdentifier(ber.SEQUENCE):
    def __parameters(self):
        return ber.SEQUENCE
    __parameters.type = ber.SEQUENCE.type

    _fields_ = [
        (ber.OBJECT_IDENTIFIER, 'algorithm'),
        (__parameters, 'parameters'),
    ]

class RSAPublicKey(ber.SEQUENCE):
    _fields_ = [
        (ber.INTEGER, 'modulus'),
        (ber.INTEGER, 'publicExponent'),
    ]

class SubjectPublicKeyInfo(ber.SEQUENCE):
    def __subjectPublicKey(self):
        p = self.getparent(SubjectPublicKeyInfo)
        res = p['algorithm']['value']
        algorithm, parameters = (res[fld]['value'] if res.has(fld) else None for fld in ['algorithm', 'parameters'])
        algoIdentifier = tuple(algorithm.identifier())
        t = dyn.clone(Packet, __object__=lambda self, _: RSAPublicKey)
        return dyn.clone(ber.BITSTRING, _object_=t)
    __subjectPublicKey.type = ber.BITSTRING.type

    _fields_ = [
        (AlgorithmIdentifier, 'algorithm'),
        #(ber.BITSTRING, 'subjectPublicKey'),
        (__subjectPublicKey, 'subjectPublicKey'),
    ]

class KeyIdentifier(ber.OCTETSTRING):
    pass

class ORAddress(ber.SEQUENCE):
    _fields_ = []

class EDIPartyName(ber.SEQUENCE):
    _fields_ = []

class GeneralName(ber.Constructed):
    # FIXME
    _fields_ = [
        (dyn.clone(ber.PrintableString, type=(Context, 0)), 'otherName'),
        (dyn.clone(ber.PrintableString, type=(Context, 1)), 'rfc822Name'),
        (dyn.clone(ber.PrintableString, type=(Context, 2)), 'dNSName'),
        (dyn.clone(ORAddress, type=(Context, 3)), 'x400Address'),
        (dyn.clone(Name, type=(Context, 4)), 'directoryName'),
        (dyn.clone(EDIPartyName, type=(Context, 5)), 'ediPartyName'),
        (dyn.clone(ber.PrintableString, type=(Context, 6)), 'uniformResourceIdentifier'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 7)), 'iPAddress'),
        (dyn.clone(ber.OBJECT_IDENTIFIER, type=(Context, 8)), 'registeredID'),
    ]

class GeneralNames(ber.SEQUENCE):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: GeneralName)

class AuthorityKeyIdentifier(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(KeyIdentifier, type=(Context, 0)), 'keyIdentifier'),
        (dyn.clone(GeneralNames, type=(Context, 1)), 'authorityCertIssuer'),
        (dyn.clone(CertificateSerialNumber, type=(Context, 2)), 'authorityCertSerialNumber'),
    ]

class Extension(ber.SEQUENCE):
    _fields_ = [
        (ber.OBJECT_IDENTIFIER, 'extnID'),
        (ber.BOOLEAN, 'critical'),
        (dyn.clone(ber.Packet, type=ber.OCTETSTRING.type), 'extnValue'),
    ]

class ExtensionList(ber.SEQUENCE):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: Extension)

class Extensions(ber.SEQUENCE):
    _fields_ = [
        (ExtensionList, 'items'),
    ]

class TBSCertificate(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(Version_DEFAULT, type=(Context, 0)), 'version'),
        (CertificateSerialNumber, 'serialNumber'),
        (AlgorithmIdentifier, 'signature'),
        (Name, 'issuer'),
        (Validity, 'validity'),
        (Name, 'subject'),
        (SubjectPublicKeyInfo, 'subjectPublicKeyInfo'),
        (dyn.clone(UniqueIdentifier, type=(Context, 1)), 'issuerUniqueID'),
        (dyn.clone(UniqueIdentifier, type=(Context, 2)), 'subjectUniqueID'),
        (dyn.clone(Extensions, type=(Context, 3)), 'extensions'),
    ]

class Certificate(ber.SEQUENCE):
    _fields_ = [
        (TBSCertificate, 'tbsCertificate'),
        (AlgorithmIdentifier, 'signatureAlgorithm'),
        (ber.BITSTRING, 'signatureValue'),
    ]

class Packet(ber.Packet):
    def __object__(self, _):
        return Certificate

if __name__ == '__main__':
    import sys, ptypes, protocol.x509 as x509
    from ptypes import *

    import importlib
    importlib.reload(x509)

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    data = '308202a13082020ea003020102021019af5d26ef02acb448ea8886a359af0a300906052b0e03021d0500301e311c301a0603550403131363686d757468752d77372d747374332d636133301e170d3130303231303032323830335a170d3339313233313233353935395a301a311830160603550403130f63686d757468752d77372d7473743330820122300d06092a864886f70d01010105000382010f003082010a0282010100a5583ba38c6a21642334d91657c7cc8f7deea7b2b453cb4bf95a5e537e069036a95ad11700e17cb46340af803b7bbff966fb2af57fddff47f94db6105b63ffaf6bb026fa2a317d4fa652cfaf06f787658f2f1316b38b02eb39c6caf4ca68502f89e23ba8c2fc5e56671fc0d8eb9bc65ae2148df5730ff66cd9f940d22bea4b0b5a17264baf264f34e48c875bf4110a8c1f80647798cc5c54c03bb2b3c534384ad335f48f94a45f39d69508ad7c88f69bbc7d161b3f8e9351b6ba90ac065c2a7f9cbf6da82ef22808cb1c0bca30e15df47d958ac2d726a4c6489c0363459c84940310ce4af43acff707025ca0d502f6ff63b3b94cf78307930b6f38d9d68c7de90203010001a368306630130603551d25040c300a06082b06010505070301304f0603551d010448304680103c8db6418a8b1b208f76cc07c6724d5ca120301e311c301a0603550403131363686d757468752d77372d747374332d6361338210db048065d808f69f48fa85880a505184300906052b0e03021d0500038181002ba86f466e4a180dec1445a021bcd261ea1b31a7cbd8363b9464dc4dac8d9fb40aaab1f78509f048b360c07188c8ae59f8f5be8b7f31da4a4a31b2c16c0cf9e57827b5f1c5b46a4b52c89d6cdde1475e7f00d87cd426b581f989272aefd876edfed253a6e61c8d5a5d1572ecb91a8f4e4f4eba82e66ee3e825410c21e6425751'
    z = x509.Packet(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l

    cert = z['value'][0]
    print(cert['value']['version'])
    x = z['value']['tbscertificate']['value']['extensions']['value']['items']['value']
    k = z.at(0x99).getparent(ber.Element)
