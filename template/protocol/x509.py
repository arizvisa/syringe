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
        ('emailAddress', '1.2.840.113549.1.9.1'),
        ('unstructuredName', '1.2.840.113549.1.9.2'),
        ('contentType', '1.2.840.113549.1.9.3'),
        ('messageDigest', '1.2.840.113549.1.9.4'),
        ('signingTime', '1.2.840.113549.1.9.5'),
        ('counterSignature', '1.2.840.113549.1.9.6'),
        ('challengePassword', '1.2.840.113549.1.9.7'),
        ('unstructuredAddress', '1.2.840.113549.1.9.8'),
        ('extendedCertificateAttributes', '1.2.840.113549.1.9.9'),
        ('issuerAndSerialNumber', '1.2.840.113549.1.9.10'),
        ('passwordCheck', '1.2.840.113549.1.9.11'),
        ('publicKey', '1.2.840.113549.1.9.12'),
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

class AttributeValue(ptype.definition): pass
class AttributeValuePrintable(ber.PrintableString): pass
class AttributeValueUTF8(ber.UTF8String): pass
class AttributeValueIA5(ber.IA5String): pass

class AttributeTypeAndValue(ber.SEQUENCE):
    def __AttributeValuePrintable(self):
        p = self.getparent(AttributeTypeAndValue)
        res = p['type']['value']
        return AttributeValuePrintable
    __AttributeValuePrintable.type = ber.PrintableString.type

    def __AttributeValueUTF8(self):
        p = self.getparent(AttributeTypeAndValue)
        res = p['type']['value']
        return AttributeValueUTF8
    __AttributeValueUTF8.type = ber.UTF8String.type

    def __AttributeValueIA5(self):
        p = self.getparent(AttributeTypeAndValue)
        res = p['type']['value']
        return AttributeValueIA5
    __AttributeValueIA5.type = ber.IA5String.type

    _fields_ = [
        (AttributeType, 'type'),
        (__AttributeValuePrintable, 'value-printable'),
        (__AttributeValueUTF8, 'value-utf8'),
        (__AttributeValueIA5, 'value-ia5'),
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

class UniqueIdentifier(ber.BIT_STRING):
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
        algoIdentifier = tuple(algorithm.get())

        # FIXME: this won't always be an RSAPublicKey as it depends
        #        on the algorithm.
        t = dyn.clone(Packet, __object__=lambda self, _: RSAPublicKey)
        return dyn.clone(ber.BIT_STRING, _object_=t)
    __subjectPublicKey.type = ber.BIT_STRING.type

    _fields_ = [
        (AlgorithmIdentifier, 'algorithm'),
        #(ber.BIT_STRING, 'subjectPublicKey'),      # FIXME: this can cause deserialization issues
        (__subjectPublicKey, 'subjectPublicKey'),   # FIXME: this callable seems to be bunk in some situations
    ]

class KeyIdentifier(ber.OCTET_STRING):
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
        (dyn.clone(ber.OCTET_STRING, type=(Context, 7)), 'iPAddress'),
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
        id = extensionId.get()

        # This octet string is actually der-encoded, so we should
        # return a packet type specifically for the x509 extensions.
        # However, since that isn't implemented we'll just return a
        # packet so that we can force its decoding.
        return Packet
    __extnValue.type = ber.OCTET_STRING.type

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
        (SubjectPublicKeyInfo, 'subjectPublicKeyInfo'),     # FIXME: this needs to be verified
        (dyn.clone(UniqueIdentifier, type=(Context, 1)), 'issuerUniqueID'),
        (dyn.clone(UniqueIdentifier, type=(Context, 2)), 'subjectUniqueID'),
        (dyn.clone(Extensions, type=(Context, 3)), 'extensions'),
    ]

class Certificate(ber.SEQUENCE):
    _fields_ = [
        (TBSCertificate, 'tbsCertificate'),
        (AlgorithmIdentifier, 'signatureAlgorithm'),
        (ber.BIT_STRING, 'signatureValue'),
    ]

class Packet(ber.Packet):
    Protocol = Protocol
    def __object__(self, _):
        return Certificate

if __name__ == '__main__':
    import sys, operator, ptypes, protocol.ber as ber, protocol.x509 as x509
    from ptypes import *

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    def smoketest():
        data = '308202a13082020ea003020102021019af5d26ef02acb448ea8886a359af0a300906052b0e03021d0500301e311c301a0603550403131363686d757468752d77372d747374332d636133301e170d3130303231303032323830335a170d3339313233313233353935395a301a311830160603550403130f63686d757468752d77372d7473743330820122300d06092a864886f70d01010105000382010f003082010a0282010100a5583ba38c6a21642334d91657c7cc8f7deea7b2b453cb4bf95a5e537e069036a95ad11700e17cb46340af803b7bbff966fb2af57fddff47f94db6105b63ffaf6bb026fa2a317d4fa652cfaf06f787658f2f1316b38b02eb39c6caf4ca68502f89e23ba8c2fc5e56671fc0d8eb9bc65ae2148df5730ff66cd9f940d22bea4b0b5a17264baf264f34e48c875bf4110a8c1f80647798cc5c54c03bb2b3c534384ad335f48f94a45f39d69508ad7c88f69bbc7d161b3f8e9351b6ba90ac065c2a7f9cbf6da82ef22808cb1c0bca30e15df47d958ac2d726a4c6489c0363459c84940310ce4af43acff707025ca0d502f6ff63b3b94cf78307930b6f38d9d68c7de90203010001a368306630130603551d25040c300a06082b06010505070301304f0603551d010448304680103c8db6418a8b1b208f76cc07c6724d5ca120301e311c301a0603550403131363686d757468752d77372d747374332d6361338210db048065d808f69f48fa85880a505184300906052b0e03021d0500038181002ba86f466e4a180dec1445a021bcd261ea1b31a7cbd8363b9464dc4dac8d9fb40aaab1f78509f048b360c07188c8ae59f8f5be8b7f31da4a4a31b2c16c0cf9e57827b5f1c5b46a4b52c89d6cdde1475e7f00d87cd426b581f989272aefd876edfed253a6e61c8d5a5d1572ecb91a8f4e4f4eba82e66ee3e825410c21e6425751'
        z = x509.Packet(source=ptypes.prov.bytes(fromhex(data)))
        z=z.l

        cert = z['value'][0]
        version = cert['value']['version']['value']['DEFAULT']
        assert(version['value']['v3'])
        x = z['value']['tbscertificate']['value']['extensions']['value']['items']['value']
        k = z.at(0x99).getparent(ber.Element)
        base = z['value']['tbsCertificate']['value']['issuer']['value'][0]['value'][0]['value']
        assert(base['type']['value'].get() == (2,5,4,3))
        assert(base['type']['value'].str() == '2.5.4.3')
        assert(base['type']['value'].description() == 'joint-iso-itu-t.ds.attributeType.commonName')
        assert(all(base['type']['value'][item] for item in [(2,5,4,3), '2.5.4.3', 'joint-iso-itu-t.ds.attributeType.commonName']))
        assert(base['value-printable']['value'].str() == 'chmuthu-w7-tst3-ca3')

    def sampletest():
        data = '308202123082017b02020dfa300d06092a864886f70d010105050030819b310b3009060355040613024a50310e300c06035504081305546f6b796f3110300e060355040713074368756f2d6b753111300f060355040a13084672616e6b34444431183016060355040b130f5765624365727420537570706f7274311830160603550403130f4672616e6b344444205765622043413123302106092a864886f70d0109011614737570706f7274406672616e6b3464642e636f6d301e170d3132303832323035323635345a170d3137303832313035323635345a304a310b3009060355040613024a50310e300c06035504080c05546f6b796f3111300f060355040a0c084672616e6b3444443118301606035504030c0f7777772e6578616d706c652e636f6d305c300d06092a864886f70d0101010500034b0030480241009bfc6690798442bbab13fd2b7bf8de1512e5f193e3068a7bb8b1e19e26bb9501bfe730ed648502dd1569a834b006ec3f353c1e1b2b8ffa8f001bdf07c6ac53070203010001300d06092a864886f70d01010505000381810014b64cbb817933e671a4da516fcb081d8d60ecbc18c7734759b1f22048bb61fafc4dad898dd121ebd5d8e5bad6a636fd745083b60fc71ddf7de52e817f45e09fe23e79eed73031c72072d9582e2afe125a3445a119087c89475f4a95be23214a5372da2a052f2ec970f65bfafddfb431b2c14a9c062543a1e6b41e7f869b1640'
        source = ptypes.prov.bytes(fromhex(data))
        z = x509.Packet(source=source)
        z=z.l

        signatureValue = ber.BIT_STRING().alloc(string=fromhex('14B64CBB817933E671A4DA516FCB081D8D60ECBC18C7734759B1F22048BB61FAFC4DAD898DD121EBD5D8E5BAD6A636FD745083B60FC71DDF7DE52E817F45E09FE23E79EED73031C72072D9582E2AFE125A3445A119087C89475F4A95BE23214A5372DA2A052F2EC970F65BFAFDDFB431B2C14A9C062543A1E6B41E7F869B1640'))
        assert(z['value']['signaturevalue']['value'].serialize() == signatureValue.serialize())

        algorithm = x509.OBJECT_IDENTIFIER().set('sha1withRSAEncryption')   # (1,2,840,113549,1,1,5)
        signatureAlgorithm = x509.AlgorithmIdentifier().alloc(algorithm=algorithm)
        assert(signatureAlgorithm['algorithm'].serialize() == z['value']['signaturealgorithm']['value']['algorithm'].serialize())

        # FIXME: need some way to ensure that ber.Element<ber.NULL> is appended at the end of the signature algorithm
        signatureAlgorithm = x509.AlgorithmIdentifier().alloc([x509.Packet().alloc(Value=algorithm), x509.Packet().alloc(Value=ber.NULL)])
        assert(signatureAlgorithm.serialize() == z['value']['signaturealgorithm']['value'].serialize())

        #print(z['value']['tbscertificate'])
        names = ['serialNumber', 'signature', 'issuer', 'validity', 'subject', 'subjectPublicKeyInfo']
        serialNumber = x509.CertificateSerialNumber(length=2).set(3578)
        assert(z['value']['tbscertificate']['value']['serialnumber']['value'].serialize() == serialNumber.serialize())

        algorithm = x509.OBJECT_IDENTIFIER().set('sha1withRSAEncryption')   # (1,2,840,113549,1,1,5))
        signature = x509.AlgorithmIdentifier().alloc(algorithm=algorithm)
        assert(z['value']['tbscertificate']['value']['signature']['value']['algorithm']['value'].serialize() == algorithm.serialize())

        # FIXME: need some way to ensure that ber.Element<ber.NULL> is appended at the end of the signature algorithm
        signature = x509.AlgorithmIdentifier().alloc([x509.Packet().alloc(Value=algorithm), x509.Packet().alloc(Value=ber.NULL)])
        assert(z['value']['tbscertificate']['value']['signature']['value'].serialize() == signature.serialize())

        def attributetypeandvalue(type, key, value):
            t = x509.AttributeType().set(type)
            return x509.AttributeTypeAndValue().alloc(type=t, **{key: value})

        def name(items):
            names = [x509.RelativeDistinguishedName().alloc([x509.Packet().alloc(Value=item)]) for item in items]
            return x509.Name().alloc([x509.Packet().alloc(Value=item) for item in names])

        issuer = []
        # joint-iso-itu-t.ds.attributeType.countryName
        issuer.append(attributetypeandvalue((2,5,4,6), 'value-printable', x509.AttributeValuePrintable().alloc('JP')))
        # joint-iso-itu-t.ds.attributeType.stateOrProvinceName
        issuer.append(attributetypeandvalue((2,5,4,8), 'value-printable', x509.AttributeValuePrintable().alloc('Tokyo')))
        # joint-iso-itu-t.ds.attributeType.localityName
        issuer.append(attributetypeandvalue((2,5,4,7), 'value-printable', x509.AttributeValuePrintable().alloc('Chuo-ku')))
        # joint-iso-itu-t.ds.attributeType.organizationName
        issuer.append(attributetypeandvalue((2,5,4,10), 'value-printable', x509.AttributeValuePrintable().alloc('Frank4DD')))
        # joint-iso-itu-t.ds.attributeType.organizationUnitName
        issuer.append(attributetypeandvalue((2,5,4,11), 'value-printable', x509.AttributeValuePrintable().alloc('WebCert Support')))
        # joint-iso-itu-t.ds.attributeType.commonName
        issuer.append(attributetypeandvalue((2,5,4,3), 'value-printable', x509.AttributeValuePrintable().alloc('Frank4DD Web CA')))
        # emailName
        issuer.append(attributetypeandvalue((1,2,840,113549,1,9,1), 'value-ia5', x509.AttributeValueIA5().alloc('support@frank4dd.com')))
        assert(name(issuer).serialize() == z['value']['tbscertificate']['value']['issuer']['value'].serialize())

        notbefore = x509.Time().alloc('120822052654Z')
        notafter = x509.Time().alloc('170821052654Z')
        validity = x509.Validity().alloc(notBefore=notbefore, notAfter=notafter)
        assert(z['value']['tbscertificate']['value']['validity']['value'].serialize() == validity.serialize())

        subject = []
        # joint-iso-itu-t.ds.attributeType.countryName
        subject.append(attributetypeandvalue((2,5,4,6), 'value-printable', x509.AttributeValuePrintable().alloc('JP')))
        # joint-iso-itu-t.ds.attributeType.stateOrProvinceName
        subject.append(attributetypeandvalue((2,5,4,8), 'value-utf8', x509.AttributeValueUTF8().alloc('Tokyo')))
        # joint-iso-itu-t.ds.attributeType.organizationName
        subject.append(attributetypeandvalue((2,5,4,10), 'value-utf8', x509.AttributeValueUTF8().alloc('Frank4DD')))
        # joint-iso-itu-t.ds.attributeType.commonName
        subject.append(attributetypeandvalue((2,5,4,3), 'value-utf8', x509.AttributeValueUTF8().alloc('www.example.com')))
        assert(z['value']['tbscertificate']['value']['subject']['value'].serialize() == name(subject).serialize())

        algorithm = x509.OBJECT_IDENTIFIER().set('rsaEncryption')
        subjectalgorithm = x509.AlgorithmIdentifier().alloc(algorithm=algorithm)
        assert(z['value']['tbscertificate']['value']['subjectpublickeyinfo']['value']['algorithm']['value']['algorithm']['value'].serialize() == algorithm.serialize())

        # FIXME: need some way to ensure that ber.Element<ber.NULL> is appended at the end of the signature algorithm
        subjectalgorithm = x509.AlgorithmIdentifier().alloc([x509.Packet().alloc(Value=algorithm), x509.Packet().alloc(Value=ber.NULL)])
        assert(z['value']['tbscertificate']['value']['subjectpublickeyinfo']['value']['algorithm']['value'].serialize() == subjectalgorithm.serialize())

        modulus = ber.INTEGER(length=65).set(0x009bfc6690798442bbab13fd2b7bf8de1512e5f193e3068a7bb8b1e19e26bb9501bfe730ed648502dd1569a834b006ec3f353c1e1b2b8ffa8f001bdf07c6ac5307)
        pubexp = ber.INTEGER(length=3).set(65537)
        rsakey = x509.RSAPublicKey().alloc(modulus=modulus, publicExponent=pubexp)
        assert(z['value']['tbscertificate']['value']['subjectpublickeyinfo']['value']['subjectpublickey']['value']['string']['value'].serialize() == rsakey.serialize())

        pubkey = ber.BIT_STRING().alloc(string=x509.Packet().alloc(Value=rsakey))
        assert(z['value']['tbscertificate']['value']['subjectpublickeyinfo']['value']['subjectpublickey']['value'].serialize() == pubkey.serialize())

        subjectpublickeyinfo = x509.SubjectPublicKeyInfo().alloc(algorithm=subjectalgorithm, subjectPublicKey=pubkey)
        assert(z['value']['tbscertificate']['value']['subjectpublickeyinfo']['value'].serialize() == subjectpublickeyinfo.serialize())

        tbs = x509.TBSCertificate().alloc(
            serialNumber=serialNumber,
            signature=signature,
            issuer=name(issuer),
            validity=validity,
            subject=name(subject),
            subjectPublicKeyInfo=subjectpublickeyinfo
        )
        assert(z['value']['tbscertificate']['value'].serialize() == tbs.serialize())

        cert = x509.Certificate().alloc(tbsCertificate=tbs, signatureAlgorithm=signatureAlgorithm, signatureValue=signatureValue)
        a = x509.Packet().alloc(Value=cert)
        assert(a.serialize() == z.serialize())

if __name__ == '__main__':
    import sys, ptypes, protocol.x509 as x509, protocol.ber as ber

    if len(sys.argv) < 2:
        print('running smoketest...')
        smoketest()
        print('running x509sample...')
        sampletest()
        print('you win.')
        sys.exit(0)

    source = ptypes.prov.file(sys.argv[1], 'rb')
    source = ptypes.setsource(source)

    z = x509.Packet(source=source)
    z=z.l
