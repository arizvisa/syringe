import ptypes
from . import ber
from ptypes import *

Protocol = ber.Protocol.copy(recurse=True)
Universal = Protocol.lookup(ber.Universal.Class)
Context = Protocol.lookup(ber.Context.Class)
Application = Protocol.lookup(ber.Application.Class)

@Universal.define
class OBJECT_IDENTIFIER(ber.OBJECT_IDENTIFIER):
    id_at = lambda name, oid: tuple('.'.join([item, value]) for item, value in zip(['joint-iso-itu-t.ds.attributeType', '2.5.4'], [name, "{:d}".format(oid)]))
    _values_ = [
        id_at('title', 12),
        id_at('dnQualifier', 46),
        id_at('countryName', 6),
        id_at('serialNumber', 5),
        id_at('pseudonym', 65),
        id_at('name', 41),
        id_at('surname', 4),
        id_at('givenName', 42),
        id_at('initials', 43),
        id_at('generationQualifier', 44),
        id_at('commonName', 3),
        id_at('localityName', 7),
        id_at('stateOrProvinceName', 8),
        id_at('organizationName', 10),
        id_at('organizationUnitName', 11),
        id_at('title', 12),
        id_at('dnQualifier', 46),
    ]

    # PKCS #7 & #9
    _values_ += [
        ('md5', '1.2.840.113549.2.5'),
        ('rsa', '1.3.14.3.2.1.1'),
        ('desMAC', '1.3.14.3.2.10'),
        ('rsaSignature', '1.3.14.3.2.11'),
        ('dsa', '1.3.14.3.2.12'),
        ('dsaWithSHA', '1.3.14.3.2.13'),
        ('mdc2WithRSASignature', '1.3.14.3.2.14'),
        ('shaWithRSASignature', '1.3.14.3.2.15'),
        ('dhWithCommonModulus', '1.3.14.3.2.16'),
        ('desEDE', '1.3.14.3.2.17'),
        ('sha', '1.3.14.3.2.18'),
        ('mdc-2', '1.3.14.3.2.19'),
        ('dsaCommon', '1.3.14.3.2.20'),
        ('dsaCommonWithSHA', '1.3.14.3.2.21'),
        ('rsaKeyTransport', '1.3.14.3.2.22'),
        ('keyed-hash-seal', '1.3.14.3.2.23'),
        ('md2WithRSASignature', '1.3.14.3.2.24'),
        ('md5WithRSASignature', '1.3.14.3.2.25'),
        ('sha1', '1.3.14.3.2.26'),
        ('dsaWithSHA1', '1.3.14.3.2.27'),
        ('dsaWithCommandSHA1', '1.3.14.3.2.28'),
        ('sha-1WithRSAEncryption', '1.3.14.3.2.29'),
        ('contentType', '1.2.840.113549.1.9.3'),
        ('messageDigest', '1.2.840.113549.1.9.4'),
        ('signingTime', '1.2.840.113549.1.9.5'),
        ('counterSignature', '1.2.840.113549.1.9.6'),
        ('challengePassword', '1.2.840.113549.1.9.7'),
        ('unstructuredAddress', '1.2.840.113549.1.9.8'),
        ('extendedCertificateAttributes', '1.2.840.113549.1.9.9'),
        ('rsaEncryption', '1.2.840.113549.1.1.1'),
        ('md2withRSAEncryption', '1.2.840.113549.1.1.2'),
        ('md4withRSAEncryption', '1.2.840.113549.1.1.3'),
        ('md5withRSAEncryption', '1.2.840.113549.1.1.4'),
        ('sha1withRSAEncryption', '1.2.840.113549.1.1.5'),
        ('rsaOAEPEncryptionSET', '1.2.840.113549.1.1.6'),
        ('dsa', '1.2.840.10040.4.1'),
        ('dsaWithSha1', '1.2.840.10040.4.3'),
        ('joint-iso-itu-t.ds.certificateExtension.authorityKeyIdentifier', (2,5,29,1)),
    ]

class AttributeType(OBJECT_IDENTIFIER):
    pass

class AttributeValue(ber.PrintableString):
    pass

class AttributeTypeAndValue(ber.SEQUENCE):
    def __AttributeValue(self):
        p = self.getparent(AttributeTypeAndValue)
        res = p['type']['value']
        return AttributeValue
    __AttributeValue.type = ber.PrintableString.type

    _fields_ = [
        (AttributeType, 'type'),
        (__AttributeValue, 'value'),
    ]

class RelativeDistinguishedName(ber.SET):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: AttributeTypeAndValue)

class RDNSequence(ber.SEQUENCE):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: RelativeDistinguishedName)

class Name(RDNSequence):
    pass

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
        (OBJECT_IDENTIFIER, 'algorithm'),
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

        # FIXME: this won't always be an RSAPublicKey as it depends
        #        on the algorithm.
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

@Application.define
class CountryName(ber.Constructed):
    tag = 1
    _fields_ = [
        (ber.NumericString, 'x121-dcc-code'),
        (ber.PrintableString, 'iso-3166-alpha2-code'),
    ]

@Application.define
class AdministrationDomainName(ber.Constructed):
    tag = 2
    _fields_ = [
        (ber.NumericString, 'numeric'),
        (ber.PrintableString, 'printable'),
    ]

class X121Address(ber.NumericString):
    pass

class NetworkAddress(ber.Constructed):
    _fields_ = [
        (X121Address, 'address'),
    ]

class TerminalIdentifier(ber.PrintableString):
    pass

class PrivateDomainName(ber.Constructed):
    _fields_ = [
        (ber.NumericString, 'numeric'),
        (ber.PrintableString, 'printable'),
    ]

class OrganizationName(ber.PrintableString):
    pass

class NumericUserIdentifier(ber.NumericString):
    pass

class PersonalName(ber.SET):
    _fields_ = [
        (dyn.clone(ber.PrintableString, type=(Context, 0)), 'surname'),
        (dyn.clone(ber.PrintableString, type=(Context, 1)), 'given-name'),
        (dyn.clone(ber.PrintableString, type=(Context, 2)), 'initials'),
        (dyn.clone(ber.PrintableString, type=(Context, 3)), 'generation-qualifier'),
    ]

class OrganizationalUnitName(ber.PrintableString):
    pass

class OrganizationalUnitNames(ber.SEQUENCE):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: OrganizationalUnitName)

class BuiltInStandardAttributes(ber.SEQUENCE):
    _fields_ = [
        (CountryName, 'country-name'),
        (AdministrationDomainName, 'administration-domain-name'),
        (dyn.clone(NetworkAddress, type=(Context, 0)), 'network-address'),
        (dyn.clone(TerminalIdentifier, type=(Context, 1)), 'terminal-identifier'),
        (dyn.clone(PrivateDomainName, type=(Context, 2)), 'private-domain-name'),
        (dyn.clone(OrganizationName, type=(Context, 3)), 'organization-name'),
        (dyn.clone(NumericUserIdentifier, type=(Context, 4)), 'numeric-user-identifier'),
        (dyn.clone(PersonalName, type=(Context, 5)), 'personal-name'),
        (dyn.clone(OrganizationalUnitNames, type=(Context, 6)), 'organizational-unit-names'),
    ]

class BuiltInDomainDefinedAttribute(ber.SEQUENCE):
    _fields_ = [
        (ber.PrintableString, 'type'),
        (ber.PrintableString, 'value'),
    ]

class BuiltInDomainDefinedAttributes(ber.SEQUENCE):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: BuiltInDomainDefineAttribute)

class ExtensionAttribute(ber.SEQUENCE):
    def __extension_attribute_value(self):
        p = self.getparent(ExtensionAttribute)
        t = p['extension-attribute-type']['value']
        return ber.Constructed
    __extension_attribute_value.type = (Context, 1)

    _fields_ = [
        (dyn.clone(ber.INTEGER, type=(Context, 0)), 'extension-attribute-type'),
        (__extension_attribute_value, 'extension-attribute-value'),
    ]

class ExtensionAttributes(ber.SET):
    def _object_(self):
        return dyn.clone(Packet, __object__=lambda self, _: ExtensionAttribute)

class ORAddress(ber.SEQUENCE):
    _fields_ = [
        (BuiltInStandardAttributes, 'built-in-standard-attributes'),
        (BuiltInDomainDefinedAttributes, 'built-in-domain-defined-attributes'),
        (ExtensionAttributes, 'extension-attributes'),
    ]

class TeletexString(ber.T61String):
    pass

class DirectoryString(ber.Constructed):
    _fields_ = [
        (TeletexString, 'teletexString'),
        (ber.PrintableString, 'printableString'),
        (ber.UniversalString, 'universalString'),
        (ber.UTF8String, 'utf8String'),
        (ber.BMPString, 'bmpString'),
    ]

class EDIPartyName(ber.SEQUENCE):
    _fields_ = [
        (dyn.clone(DirectoryString, type=(Context, 0)), 'nameAssigner'),
        (dyn.clone(DirectoryString, type=(Context, 1)), 'partyName'),
    ]

class AnotherName(ber.SEQUENCE):
    def __value(self):
        p = self.getparent(AnotherName)
        t = p['type-id']['value']
        return ber.Constructed
    __value.type = (Context, 0)

    _fields_ = [
        (OBJECT_IDENTIFIER, 'type-id'),
        (__value, 'value'),
    ]

class GeneralName(ber.Constructed):
    _fields_ = [
        (dyn.clone(AnotherName, type=(Context, 0)), 'otherName'),
        (dyn.clone(ber.IA5String, type=(Context, 1)), 'rfc822Name'),
        (dyn.clone(ber.IA5String, type=(Context, 2)), 'dNSName'),
        (dyn.clone(ORAddress, type=(Context, 3)), 'x400Address'),
        (dyn.clone(Name, type=(Context, 4)), 'directoryName'),
        (dyn.clone(EDIPartyName, type=(Context, 5)), 'ediPartyName'),
        (dyn.clone(ber.IA5String, type=(Context, 6)), 'uniformResourceIdentifier'),
        (dyn.clone(ber.OCTETSTRING, type=(Context, 7)), 'iPAddress'),
        (dyn.clone(OBJECT_IDENTIFIER, type=(Context, 8)), 'registeredID'),
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
    def __extnValue(self):
        p = self.getparent(Extension)
        extensionId = p['extnID']['value']
        id = extensionId.identifier()

        # This octet string is actually der-encoded, so we should
        # return a packet type specifically for the x509 extensions.
        # However, since that isn't implemented we'll just return a
        # packet so that we can force its decoding.
        return Packet
    __extnValue.type = ber.OCTETSTRING.type

    _fields_ = [
        (OBJECT_IDENTIFIER, 'extnID'),
        (ber.BOOLEAN, 'critical'),
        (__extnValue, 'extnValue'),
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
    Protocol = Protocol
    def __object__(self, _):
        return Certificate

if __name__ == '__main__':
    import sys, operator, ptypes, protocol.x509 as x509
    from ptypes import *

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    data = '308202a13082020ea003020102021019af5d26ef02acb448ea8886a359af0a300906052b0e03021d0500301e311c301a0603550403131363686d757468752d77372d747374332d636133301e170d3130303231303032323830335a170d3339313233313233353935395a301a311830160603550403130f63686d757468752d77372d7473743330820122300d06092a864886f70d01010105000382010f003082010a0282010100a5583ba38c6a21642334d91657c7cc8f7deea7b2b453cb4bf95a5e537e069036a95ad11700e17cb46340af803b7bbff966fb2af57fddff47f94db6105b63ffaf6bb026fa2a317d4fa652cfaf06f787658f2f1316b38b02eb39c6caf4ca68502f89e23ba8c2fc5e56671fc0d8eb9bc65ae2148df5730ff66cd9f940d22bea4b0b5a17264baf264f34e48c875bf4110a8c1f80647798cc5c54c03bb2b3c534384ad335f48f94a45f39d69508ad7c88f69bbc7d161b3f8e9351b6ba90ac065c2a7f9cbf6da82ef22808cb1c0bca30e15df47d958ac2d726a4c6489c0363459c84940310ce4af43acff707025ca0d502f6ff63b3b94cf78307930b6f38d9d68c7de90203010001a368306630130603551d25040c300a06082b06010505070301304f0603551d010448304680103c8db6418a8b1b208f76cc07c6724d5ca120301e311c301a0603550403131363686d757468752d77372d747374332d6361338210db048065d808f69f48fa85880a505184300906052b0e03021d0500038181002ba86f466e4a180dec1445a021bcd261ea1b31a7cbd8363b9464dc4dac8d9fb40aaab1f78509f048b360c07188c8ae59f8f5be8b7f31da4a4a31b2c16c0cf9e57827b5f1c5b46a4b52c89d6cdde1475e7f00d87cd426b581f989272aefd876edfed253a6e61c8d5a5d1572ecb91a8f4e4f4eba82e66ee3e825410c21e6425751'
    z = x509.Packet(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l

    cert = z['value'][0]
    print(cert['value']['version'])
    x = z['value']['tbscertificate']['value']['extensions']['value']['items']['value']
    k = z.at(0x99).getparent(ber.Element)
    print(z['value']['tbsCertificate']['value']['issuer']['value'][0]['value'][0])
    print(z['value']['tbsCertificate']['value']['issuer']['value'][0]['value'][0]['value']['type'])
