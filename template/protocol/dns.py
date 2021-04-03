import six, ptypes, osi.network.inet4, osi.network.inet6
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u0(pint.uint_t): pass
class s0(pint.sint_t): pass
class u8(pint.uint8_t): pass
class s8(pint.sint8_t): pass
class u16(pint.uint16_t): pass
class s16(pint.sint16_t): pass
class u32(pint.uint32_t): pass
class s32(pint.sint32_t): pass

class Name(pstruct.type):
    def __string(self):
        res = self['length'].li.int()
        return u8 if res & 0xc0 else dyn.block(res)

    _fields_ = [
        (u8, 'length'),
        (__string, 'string'),
    ]

    def CompressedQ(self):
        res = self['length'].int()
        return True if res & 0xc0 else False

    def str(self):
        if self.CompressedQ():
            raise TypeError("{:s} : Name is compressed".format(self.instance()))
        res = self['string'].serialize()
        return res.decode('ascii')

    def int(self):
        if self.CompressedQ():
            offset = self.cast(u16)
            return offset.int() & 0x3fff
        raise TypeError("{:s} : Name is not compressed".format(self.instance()))

    def summary(self):
        if self.CompressedQ():
            offset = self.int()
            return "OFFSET: {:+#x}".format(offset)
        res = self['length'].int()
        return "({:d}) {:s}".format(res, self.str())

    def repr(self):
        return self.summary()

    def set(self, value):
        if isinstance(value, six.integer_types):
            res = pint.uint16_t().set(0xc000 | value)
            return self.load(source=ptypes.prov.bytes(res.serialize()))
        elif isinstance(value, bytes) and len(value) < 0x40:
            return self.alloc(length=len(value), string=value)
        elif isinstance(value, six.string_types) and len(value) < 0x40:
            return self.alloc(length=len(value), string=value.encode('ascii'))
        elif isinstance(value, six.string_types) and len(value) < 0xc0:
            raise ValueError(value)
        raise ValueError(value)

class String(pstruct.type):
    def __string(self):
        res = self['length'].li
        return dyn.clone(pstr.string, length=res.int())

    _fields_ = [
        (u8, 'length'),
        (__string, 'string'),
    ]

    def str(self):
        return self['string'].str()

    def summary(self):
        res = self['length']
        return "({:d}) {:s}".format(res.int(), self.str())

    def repr(self):
        return self.summary()

class Label(parray.terminated):
    # XXX: Feeling kind of lazy now that all this data-entry is done, and
    #      this doesn't support message-compression at the moment even
    #      though the `Name` object does.
    _object_ = Name

    def isTerminator(self, item):
        return item.CompressedQ() or item['length'].int() == 0

    def str(self):
        items = ["{:+#x}".format(item.int()) if item.CompressedQ() else item.str() for item in self]
        return '.'.join(items)

    def alloc(self, items):
        name = items
        if isinstance(name, six.string_types):
            items = name.split('.') if name.endswith('.') else (name + '.').split('.')
            return super(Label, self).alloc(items)
        return super(Label, self).alloc(items)

    def summary(self):
        return "({:d}) {:s}".format(len(self), self.str())

class TYPE(pint.enum, u16):
    _values_ = [
        ('A', 1),
        ('NS', 2),
        ('MD', 3),
        ('MF', 4),
        ('CNAME', 5),
        ('SOA', 6),
        ('MB', 7),
        ('MG', 8),
        ('MR', 9),
        ('NULL', 10),
        ('WKS', 11),
        ('PTR', 12),
        ('HINFO', 13),
        ('MINFO', 14),
        ('MX', 15),
        ('TXT', 16),
        ('RP', 17),
        ('AFSDB', 18),
        ('X25', 19),
        ('ISDN', 20),
        ('RT', 21),
        ('NSAP', 22),
        ('NSAPPTR', 23),
        ('SIG', 24),
        ('KEY', 25),
        ('PX', 26),
        ('GPOS', 27),
        ('AAAA', 28),
        ('LOC', 29),
        ('NXT', 30),
        ('NB', 31),
        ('NBSTAT', 32),
        ('SRV', 33),
        ('ATMA', 34),
        ('NAPTR', 35),
        ('KX', 36),
        ('CERT', 37),
        ('A6', 38),
        ('DNAME', 39),
        ('SINK', 40),
        ('OPT', 41),
        ('APL', 42),
        ('DS', 43),
        ('SSHFP', 44),
        ('IPSECKEY', 45),
        ('RRSIG', 46),
        ('NSEC', 47),
        ('DNSKEY', 48),
        ('DHCID', 49),
        ('NSEC3', 50),      # FIXME
        ('NSEC3PARAM', 51), # FIXME
        ('TLSA', 52),       # FIXME
        ('SMIMEA', 53),     # FIXME
        ('HIP', 54),        # FIXME
        ('NINFO', 56),      # FIXME
        ('RKEY', 57),       # FIXME
        ('TALINK', 58),     # FIXME
        ('CDS', 59),        # FIXME
        ('CDNSKEY', 60),    # FIXME
        ('OPENPGPKEY', 61), # FIXME
        ('CSYNC', 62),      # FIXME
        ('ZONEMD', 63),     # FIXME
        ('SVCB', 64),       # FIXME
        ('HTTPS', 65),      # FIXME
        ('SPF', 99),
        ('UINFO', 100),     # FIXME
        ('UID', 101),       # FIXME
        ('GID', 102),       # FIXME
        ('UNSPEC', 103),    # FIXME
        ('NID', 104),       # FIXME
        ('L32', 105),       # FIXME
        ('L64', 106),       # FIXME
        ('LP', 107),        # FIXME
        ('EUI48', 108),     # FIXME
        ('EUI64', 109),     # FIXME
        ('TKEY', 249),
        ('TSIG', 250),
        ('MAILB', 253),
        ('MAILA', 254),
        ('URI', 256),
        ('CAA', 257),
        ('DOA', 259),
        ('TA', 32768),
        ('DLV', 32769),
    ]

class QTYPE(TYPE):
    _values_ = TYPE._values_ + [
        ('IXFR', 251),
        ('AXFR', 252),
        ('MAILB', 253),
        ('MAILA', 254),
        ('*', 255),
    ]

class CLASS(pint.enum, u16):
    _values_ = [
        ('IN', 1),
        ('CS', 2),
        ('CH', 3),
        ('HS', 4),
    ]

class QCLASS(CLASS):
    _values_ = CLASS._values_ + [
        ('*', 255),
    ]

class DIGEST_TYPE(pint.enum, u8):
    _values_ = [
        ('Reserved', 0),
        ('SHA1', 1),
    ]

class QR(pbinary.enum):
    length, _values_ = 1, [
        ('query', 0),
        ('response', 1),
    ]

class OPCODE(pbinary.enum):
    length, _values_ = 4, [
        ('QUERY', 0),
        ('IQUERY', 1),
        ('STATUS', 2),
        ('NOTIFY', 4),
        ('UPDATE', 5),
    ]

class _RCODE(object):
    _values_ = [
        ('NOERROR', 0),
        ('FORMERR', 1),
        ('SERVFAIL', 2),
        ('NXDOMAIN', 3),
        ('NOTIMP', 4),
        ('REFUSED', 5),
        ('YXDOMAIN', 6),
        ('YXRRSET', 7),
        ('NXRRSET', 8),
        ('NOTAUTH', 9),
        ('NOTZONE', 10),

        ('DSOTYPENI', 11),
        ('BADVERS', 16),
        ('BADSIG', 16),
        ('BADKEY', 17),
        ('BADTIME', 18),
        ('BADMODE', 19),
        ('BADNAME', 20),
        ('BADALG', 21),
        ('BADTRUNC', 22),
        ('BADCOOKIE', 23),
    ]

class RCODE(pbinary.enum, _RCODE):
    length = 4

class SECURITY_ALGORITHM(pint.enum, u8):
    _values_ = [
        ('reserved', 0),
        ('RSAMD5', 1),
        ('DH', 2),
        ('DSA', 3),
        ('ECC', 4),
        ('INDIRECT', 254),
        ('PRIVATEDNS', 253),
        ('PRIVATEOID', 254),
    ]

class RDATA(ptype.definition):
    cache = {}

@RDATA.define
class A(pstruct.type):
    type = TYPE.byname('A')
    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
    ]
    def summary(self):
        return self['ADDRESS'].summary()

@RDATA.define
class NS(pstruct.type):
    type = TYPE.byname('NS')
    _fields_ = [
        (Label, 'NSDNAME'),
    ]
    def summary(self):
        return self['NSDNAME'].str()

@RDATA.define
class MD(pstruct.type):
    type = TYPE.byname('MD')
    _fields_ = [
        (Label, 'MADNAME'),
    ]
    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MF(pstruct.type):
    type = TYPE.byname('MF')
    _fields_ = [
        (Label, 'MADNAME'),
    ]
    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class CNAME(pstruct.type):
    type = TYPE.byname('CNAME')
    _fields_ = [
        (Label, 'CNAME'),
    ]
    def summary(self):
        return self['CNAME'].str()

@RDATA.define
class SOA(pstruct.type):
    type = TYPE.byname('SOA')
    _fields_ = [
        (Label, 'MNAME'),
        (Label, 'RNAME'),
        (u32, 'SERIAL'),
        (u32, 'REFRESH'),
        (u32, 'RETRY'),
        (u32, 'EXPIRE'),
        (u32, 'MINIMUM'),
    ]
    def summary(self):
        fields = ['SERIAL', 'REFRESH', 'RETRY', 'EXPIRE', 'MINIMUM']
        items = ["{:d}".format(self[fld].int()) for fld in fields]
        return ' '.join([self['MNAME'].str(), self['RNAME'].str()] + items)

@RDATA.define
class MB(pstruct.type):
    type = TYPE.byname('MB')
    _fields_ = [
        (Label, 'MADNAME'),
    ]
    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MG(pstruct.type):
    type = TYPE.byname('MG')
    _fields_ = [
        (Label, 'MGMNAME'),
    ]
    def summary(self):
        return self['MGMNAME'].str()

@RDATA.define
class MR(pstruct.type):
    type = TYPE.byname('MR')
    _fields_ = [
        (Label, 'NEWNAME'),
    ]
    def summary(self):
        return self['NEWNAME'].str()

@RDATA.define
class NULL(ptype.block):
    type = TYPE.byname('NULL')

@RDATA.define
class WKS(pstruct.type):
    type = TYPE.byname('WKS')
    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
        (u8, 'PROTOCOL'),
        (ptype.undefined, 'BITMAP'),
    ]

@RDATA.define
class PTR(pstruct.type):
    type = TYPE.byname('PTR')
    _fields_ = [
        (Label, 'PTRDNAME'),
    ]
    def summary(self):
        return self['PTRDNAME'].str()

@RDATA.define
class HINFO(pstruct.type):
    type = TYPE.byname('HINFO')
    _fields_ = [
        (String, 'CPU'),
        (String, 'OS'),
    ]
    def summary(self):
        return "CPU={:s} OS={:s}".format(self['CPU'].str(), self['OS'].str())

@RDATA.define
class MINFO(pstruct.type):
    type = TYPE.byname('MINFO')
    _fields_ = [
        (Label, 'RMAILBX'),
        (Label, 'EMAILBX'),
    ]
    def summary(self):
        return ' '.join([self['RMAILBX'].str(), self['EMAILBX'].str()])

@RDATA.define
class MX(pstruct.type):
    type = TYPE.byname('MX')
    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'EXCHANGE'),
    ]
    def summary(self):
        return "{:d} {:s}".format(self['PREFERENCE'].int(), self['EXCHANGE'].str())

@RDATA.define
class TXT(parray.block):
    type = TYPE.byname('TXT')
    _object_ = String

@RDATA.define
class RP(pstruct.type):
    type = TYPE.byname('RP')
    _fields_ = [
        (Label, 'mbox'),
        (Label, 'txt'),
    ]

@RDATA.define
class AFSDB(pstruct.type):
    type = TYPE.byname('AFSDB')
    _fields_ = [
        (u16, 'subtype'),
        (Label, 'hostname'),
    ]

@RDATA.define
class X25(pstruct.type):
    type = TYPE.byname('X25')
    _fields_ = [
        (String, 'PSDN-address'),
    ]

@RDATA.define
class ISDN(pstruct.type):
    type = TYPE.byname('ISDN')
    _fields_ = [
        (String, 'ISDN-address'),
        (String, 'sa'),
    ]

@RDATA.define
class RT(pstruct.type):
    type = TYPE.byname('RT')
    _fields_ = [
        (u16, 'preference'),
        (Label, 'intermediate-host'),
    ]

@RDATA.define
class NSAP(pstr.string):
    type = TYPE.byname('NSAP')

@RDATA.define
class NSAPPTR(PTR):
    type = TYPE.byname('NSAPPTR')
    _fields_ = [
        (Label, 'PTRNAME'),
    ]
    def summary(self):
        return self['PTRNAME'].str()

class SECEXT_ALGORITHM(SECURITY_ALGORITHM):
    pass

@RDATA.define
class SIG(pstruct.type):
    type = TYPE.byname('SIG')
    _fields_ = [
        (u16, 'type-covered'),
        (SECEXT_ALGORITHM, 'algorithm'),
        (u8, 'labels'),
        (u32, 'original-ttl'),
        (u32, 'signature-expiration'),
        (u32, 'time-signed'),
        (u16, 'key-footprint'),
        (Label, 'signers-name'),
        (ptype.undefined, 'signature'),
    ]

@RDATA.define
class KEY(pstruct.type):
    type = TYPE.byname('KEY')
    _fields_ = [
        (u16, 'flags'),
        (u8, 'protocol'),
        (SECEXT_ALGORITHM, 'algorithm'),
        (ptype.undefined, 'public-key'),
    ]

@RDATA.define
class PX(pstruct.type):
    type = TYPE.byname('PX')
    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'MAP822'),
        (Label, 'MAPX400'),
    ]

@RDATA.define
class GPOS(pstruct.type):
    type = TYPE.byname('GPOS')
    _fields_ = [
        (String, 'LONGITUDE'),
        (String, 'LATITUDE'),
        (String, 'ALTITUDE'),
    ]

@RDATA.define
class AAAA(pstruct.type):
    type = TYPE.byname('AAAA')
    _fields_ = [
        (osi.network.inet6.in_addr, 'ADDRESS'),
    ]
    def summary(self):
        return self['ADDRESS'].summary()

@RDATA.define
class LOC(pstr.string):
    type = TYPE.byname('LOC')
    class Pow10(pbinary.struct):
        _fields_ = [
            (4, 'base'),
            (4, 'power'),
        ]
    _fields_ = [
        (u8, 'VERSION'),
        (Pow10, 'SIZE'),
        (Pow10, 'HORIZ_PRE'),
        (Pow10, 'VERT_PRE'),
        (s32, 'Latitude'),
        (s32, 'Longitude'),
        (s32, 'Altitude'),
    ]

@RDATA.define
class NXT(pstruct.type):
    type = TYPE.byname('NXT')
    _fields_ = [
        (Label, 'next-domain-name'),
        (ptype.undefined, 'type-bitmap'),
    ]

class NB_NODETYPE(pbinary.enum):
    length, _values_ = 2, [
        ('B node', 0b00),
        ('P node', 0b01),
        ('M node', 0b10),
        (  'NBDD', 0b11),
    ]

class NB_FLAGS(pbinary.flags):
    _fields_ = [
        (13, 'RESERVED'),
        (NB_NODETYPE, 'ONT'),
        (1, 'G'),
    ]

@RDATA.define
class NB(pstruct.type):
    type = TYPE.byname('NB')
    _fields_ = [
        (NB_FLAGS, 'NB_FLAGS'),
        (osi.network.inet4.in_addr, 'NB_ADDRESS'),
    ]

class NAME_FLAGS(pbinary.flags):
    _fields_ = [
        (9, 'RESERVED'),
        (1, 'PRM'),
        (1, 'ACT'),
        (1, 'CNF'),
        (1, 'DRG'),
        (NB_NODETYPE, 'ONT'),
        (1, 'G'),
    ]

class NODE_NAME(pstruct.type):
    _fields_ = [
        (Label, 'NAME'),
        (NAME_FLAGS, 'NAME_FLAGS'),
    ]

@RDATA.define
class NBSTAT(pstruct.type):
    type = TYPE.byname('NBSTAT')
    _fields_ = [
        (u8, 'NUM_NAMES'),
        (lambda self: dyn.array(NODE_NAME, self['NUM_NAMES'].li.int()), 'NAMES'),
    ]

@RDATA.define
class SRV(pstruct.type):
    type = TYPE.byname('SRV')
    _fields_ = [
        (u16, 'Priority'),
        (u16, 'Weight'),
        (u16, 'Port'),
        (Label, 'Target'),
    ]

class ATMA_FORMAT(pint.enum, u8):
    _values_ = [
        ('AESA', 0),
        ('E164', 1),
    ]

@RDATA.define
class ATMA(pstruct.type):
    type = TYPE.byname('ATMA')
    _fields_ = [
        (ATMA_FORMAT, 'FORMAT'),
        (Label, 'ADDRESS'),
    ]

@RDATA.define
class NAPTR(pstruct.type):
    type = TYPE.byname('NAPTR')
    _fields_ = [
        (u16, 'ORDER'),
        (u16, 'PREFERENCE'),
        (String, 'FLAGS'),
        (String, 'REGEXP'),
        (Label, 'REPLACEMENT'),
    ]

@RDATA.define
class KX(pstruct.type):
    type = TYPE.byname('KX')
    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'EXCHANGER'),
    ]

class CERT_TYPE(pint.enum, u16):
    _values_ = [
        ('PKIX', 1),
        ('SPKI', 2),
        ('PGP', 3),
        ('IPKIX', 4),
        ('ISPKI', 5),
        ('IPGP', 6),
        ('ACPKIX', 7),
        ('IACPKIX', 8),
        ('URI', 253),
        ('OID', 254),
        ('Reserved', 255),
    ]

class CERT_ALGORITHM(SECURITY_ALGORITHM):
    pass

@RDATA.define
class CERT(pstruct.type):
    type = TYPE.byname('CERT')
    _fields_ = [
        (CERT_TYPE, 'type'),
        (u16, 'key tag'),
        (CERT_ALGORITHM, 'algorithm'),
        (ptype.undefined, 'certificate'),
    ]

@RDATA.define
class A6(pstruct.type):
    type = TYPE.byname('A6')
    def __Suffix(self):
        prefix, bits = self['Prefix'].li.int(), 128
        res = max(bits, prefix) - prefix
        return dyn.block((prefix + 7) // 8)
    def __padding_Suffix(self):
        res = (self['Prefix'].li + 7) // 8
        return dyn.block(max(0, res) - self['Suffix'].li.size())
    _fields_ = [
        (u8, 'Prefix'),
        (__Suffix, 'Suffix'),
        (__padding_Suffix, 'padding(Suffix)'),
        (Label, 'Name'),
    ]

@RDATA.define
class DNAME(pstruct.type):
    type = TYPE.byname('DNAME')
    _fields_ = [
        (Label, 'target'),
    ]

class SINK_CODING(pint.enum, u8):
    _values_ = [
        ('SNMP', 1),
        ('OSI-1990', 2),
        ('OSI-1994', 3),
        ('PRIVATE', 63),
        ('DNS', 64),
        ('MIME', 65),
        ('TEXT', 66),
        ('URL', 254),
    ]

@RDATA.define
class SINK(pstruct.type):
    type = TYPE.byname('SINK')
    class ASN1_SUBCODING(pint.enum, u8):
        _values_ = [
            ('reserved', 0),
            ('ber', 1),
            ('der', 2),
            ('per-aligned', 3),
            ('per', 4),
            ('cer', 5),
        ]

    class MIME_SUBCODING(pint.enum, u8):
        _values_ = [
            ('reserved', 0),
            ('7bit', 1),
            ('8bit', 2),
            ('binary', 3),
            ('quoted', 4),
            ('base64', 5),
            ('private', 254),
        ]

    class TEXT_SUBCODING(pint.enum, u8):
        _values_ = [
            ('reserved', 0),
            ('ASCII', 1),
            ('UTF-7', 2),
            ('UTF-8', 3),
            ('ASCII-MIME', 4),
            ('private', 254),
        ]
    def __subcoding(self):
        res = self['coding'].li
        if 0 < res.int() < 64:
            return SINK.ASN1_SUBCODING
        elif res['MIME']:
            return SINK.MIME_SUBCODING
        elif res['TEXT']:
            return SINK.TEXT_SUBCODING
        return u8
    _fields_ = [
        (SINK_CODING, 'coding'),
        (__subcoding, 'subcoding'),
        (ptype.block, 'data'),
    ]

@RDATA.define
class OPT(pstruct.type):
    type = TYPE.byname('OPT')
    def __DATA(self):
        res, length = (self[fld].li for fld in ['CODE', 'LENGTH'])
        return dyn.block(length.int())
    _fields_ = [
        (u16, 'CODE'),
        (u16, 'LENGTH'),
        (__DATA, 'DATA'),
    ]

class ADDRESSFAMILY(pint.enum):
    # https://www.iana.org/assignments/address-family-numbers/address-family-numbers.xhtml
    _values_ = [
        ('IP', 1),
        ('IP6', 2),
        ('NSAP ', 3),
        ('HDLC', 4),
        ('BBN', 5),
        ('802', 6),
        ('E.163 ', 7),
        ('E.164', 8),
        ('F.69', 9),
        ('X.121', 10),
        ('IPX ', 11),
        ('Appletalk ', 12),
        ('Decnet IV ', 13),
        ('Banyan Vines ', 14),
        ('E.164', 15),
        ('DNS', 16),
        ('DN', 17),
        ('AS', 18),
        ('XTP-IP4', 19),
        ('XTP-IP6', 20),
        ('XTP-XTP', 21),
        ('FChannel-WW-Port', 22),
        ('FChannel-WW-Node', 23),
        ('GWID', 24),
        ('AFI', 25),
        ('MPLS-TP-SE', 26),
        ('MPLS-TP-LSP', 27),
        ('MPLS-TP-P', 28),
        ('MTIP', 29),
        ('MTIPv6', 30),
        ('EIGRP-Common', 16384),
        ('EIGRP-IPv4', 16385),
        ('EIGRP-IPv6', 16386),
        ('LCAF', 16387),
        ('BGP-LS', 16388),
        ('MAC48', 16389),
        ('MAC64', 16390),
        ('OUI', 16391),
        ('MAC/24', 16392),
        ('MAC/40', 16393),
        ('IPv6/64', 16394),
        ('RBridge', 16395),
        ('TRILL', 16396),
        ('UUID', 16397),
        ('AFI', 16398),
        ('Reserved', 65535),
    ]

@RDATA.define
class APL(pstruct.type):
    type = TYPE.byname('APL')
    class _ADDRESSFAMILY(ADDRESSFAMILY, u16):
        pass
    class _AFD(pbinary.flags):
        _fields_ = [
            (1, 'N'),
            (7, 'LENGTH'),
        ]
    def __AFDPART(self):
        res = self['AFD'].li
        return dyn.block(res['LENGTH'])
    _fields_ = [
        (_ADDRESSFAMILY, 'ADDRESSFAMILY'),
        (u8, 'PREFIX'),
        (_AFD, 'AFD'),
        (__AFDPART, 'AFDPART'),
    ]

class DNSKEY_ALGORITHM(SECURITY_ALGORITHM):
    pass

class DS_TYPE(DIGEST_TYPE):
    pass

@RDATA.define
class DS(pstruct.type):
    type = TYPE.byname('DS')
    _fields_ = [
        (u16, 'Key Tag'),
        (DNSKEY_ALGORITHM, 'Algorithm'),
        (DS_TYPE, 'Digest Type'),
        (ptype.undefined, 'Digest'),
    ]

class SSHFP_ALGORITHM(pint.enum, u8):
    _values_ = [
        ('reserved', 0),
        ('RSA', 1),
        ('DSS', 2),
    ]

class SSHFP_TYPE(DS_TYPE):
    pass

@RDATA.define
class SSHFP(pstruct.type):
    type = TYPE.byname('SSHFP')
    _fields_ = [
        (SSHFP_ALGORITHM, 'algorithm'),
        (SSHFP_TYPE, 'fp type'),
        (ptype.undefined, 'fingerprint'),
    ]

class IPSECKEY_GATEWAY(pint.enum, u8):
    _values_ = [
        ('none', 0),
        ('v4', 1),
        ('v6', 2),
        ('name', 3),
    ]

class IPSECKEY_ALGORITHM(pint.enum, u8):
    _values_ = [
        ('DSA', 1),
        ('RSA', 2),
    ]

@RDATA.define
class IPSECKEY(pstruct.type):
    type = TYPE.byname('IPSECKEY')
    def __gateway(self):
        res = self['gateway-type'].li
        if res['none']:
            return ptype.block
        elif res['v4']:
            return osi.network.inet4.in_addr
        elif res['v6']:
            return osi.network.inet6.in_addr
        elif res['name']:
            return Label
        return ptype.undefined

    _fields_ = [
        (u8, 'precedence'),
        (IPSECKEY_GATEWAY, 'gateway-type'),
        (IPSECKEY_ALGORITHM, 'algorithm'),
        (__gateway, 'gateway'),
        (ptype.undefined, 'public-key'),
    ]

@RDATA.define
class RRSIG(pstruct.type):
    type = TYPE.byname('RRSIG')
    _fields_ = [
        (TYPE, 'Type Covered'),
        (DNSKEY_ALGORITHM, 'Algorithm'),
        (u8, 'Labels'),
        (u32, 'Original TTL'),
        (u32, 'Signature Expiration'),
        (u32, 'Signature Inception'),
        (u16, 'Key Tag'),
        (Label, 'Signers Name'),
        (ptype.undefined, 'Signature'),
    ]

@RDATA.define
class NSEC(pstruct.type):
    type = TYPE.byname('NSEC')
    _fields_ = [
        (Label, 'Next Domain Name'),
        (ptype.undefined, 'Type Bit Maps'),
    ]

class DNSKEY_FLAGS(pbinary.flags):
    _fields_ = [
        (1, 'SE'),
        (7, 'Reserved'),
        (1, 'ZK'),
        (7, 'Reserved'),
    ]

class DNSKEY_PROTOCOL(pint.enum, u8):
    _values_ = [
        ('Default', 3),
    ]
    def default(self):
        return self.set('Default')
    def valid(self):
        res = self.copy().default()
        return res.int() == self.int()
    def alloc(self, **attrs):
        return super(DNSKEY_PROTOCOL, self).alloc(**attrs).default()

@RDATA.define
class DNSKEY(pstruct.type):
    type = TYPE.byname('DNSKEY')
    _fields_ = [
        (DNSKEY_FLAGS, 'Flags'),
        (DNSKEY_PROTOCOL, 'Protocol'),
        (DNSKEY_ALGORITHM, 'Algorithm'),
        (ptype.undefined, 'Public Key'),
    ]

@RDATA.define
class DHCID(pstruct.type):
    type = TYPE.byname('DHCID')
    class _Identifier_type(pint.enum, u16):
        _values_ = [
            ('HTYPE', 0),
            ('CID', 1),
            ('DUID', 2),
            ('Undefined', 0xffff),
        ]
    class _Digest_type(pint.enum, u8):
        _values_ = [
            ('SHA256', 1),
        ]
    _fields_ = [
        (_Identifier_type, 'Identifier type'),
        (_Digest_type, 'Digest type'),
        (ptype.undefined, 'Digest'),
    ]

@RDATA.define
class SPF(parray.block):
    type = TYPE.byname('SPF')
    _object_ = String

class TKEY_ERROR(pint.enum, pint.uint16_t, _RCODE):
    pass

@RDATA.define
class TKEY(pstruct.type):
    type = TYPE.byname('TKEY')
    _fields_ = [
        (Label, 'Algorithm'),
        (pint.uint32_t, 'Inception'),
        (pint.uint32_t, 'Expiration'),
        (pint.uint16_t, 'Mode'),
        (pint.uint16_t, 'Error'),
        (pint.uint16_t, 'Key Size'),
        (lambda self: dyn.block(self['Key Size'].li.int()), 'Key Data'),
        (pint.uint16_t, 'Other Size'),
        (lambda self: dyn.block(self['Other Size'].li.int()), 'Other Data'),
    ]

class TSIG_ERROR(pint.enum, pint.uint16_t, _RCODE):
    pass

@RDATA.define
class TSIG(pstruct.type):
    type = TYPE.byname('TSIG')
    _fields_ = [
        (Label, 'Algorithm Name'),
        (dyn.clone(pint.uint_t, length=6), 'Time Signed'),
        (pint.uint16_t, 'Fudge'),
        (pint.uint16_t, 'MAC Size'),
        (lambda self: dyn.block(self['MAC Size'].li.int()), 'MAC'),
        (pint.uint16_t, 'Original ID'),
        (pint.uint16_t, 'Error'),
        (pint.uint16_t, 'Other Len'),
        (lambda self: dyn.block(self['Other Len'].li.int()), 'Other Data'),
    ]

@RDATA.define
class MAILB(pstruct.type):
    type = TYPE.byname('MAILB')
    _fields_ = [
        (Label, 'NAME'),
    ]
    def summary(self):
        return self['NAME'].str()

@RDATA.define
class MAILA(pstruct.type):
    type = TYPE.byname('MAILA')
    _fields_ = [
        (Label, 'NAME'),
    ]
    def summary(self):
        return self['NAME'].str()

@RDATA.define
class URI(pstruct.type):
    type = TYPE.byname('URI')
    _fields_ = [
        (u16, 'Priority'),
        (u16, 'Weight'),
        (pstr.string, 'Target'),
    ]

@RDATA.define
class CAA(pstruct.type):
    type = TYPE.byname('CAA')
    def __Tag(self):
        res = self['Tag Length'].li
        return dyn.clone(pstr.string, length=res.int())
    _fields_ = [
        (u8, 'Flags'),
        (u8, 'Tag Length'),
        (__Tag, 'Tag'),
        (ptype.block, 'Value'),
    ]

@RDATA.define
class DOA(pstruct.type):
    type = TYPE.byname('DOA')
    _fields_ = [
        (u32, 'ENTERPRISE'),
        (u32, 'TYPE'),
        (u8, 'LOCATION'),
        (String, 'MEDIA-TYPE'),
        (ptype.block, 'DATA'),
    ]

@RDATA.define
class TA(DS):
    type = TYPE.byname('TA')

@RDATA.define
class DLV(DS):
    type = TYPE.byname('DLV')

class Header(pbinary.flags):
    _fields_ = [
        (QR, 'QR'),
        (OPCODE, 'OPCODE'),
        (1, 'AA'),
        (1, 'TC'),
        (1, 'RD'),
        (1, 'RA'),
        (1, 'Z'),
        (1, 'AD'),
        (1, 'CD'),
        (RCODE, 'RCODE'),
    ]

class Q(pstruct.type):
    _fields_ = [
        (Label, 'NAME'),
        (QTYPE, 'TYPE'),
        (QCLASS, 'CLASS'),
    ]

    def summary(self):
        return "{CLASS:s} {TYPE:s} {NAME:s}".format(NAME=self['NAME'].str(), TYPE=self['TYPE'].str(), CLASS=self['CLASS'].str())

class RR(pstruct.type):
    def __RDATA(self):
        res = self['TYPE'].li.int()
        try:
            t = RDATA.lookup(res)

        except KeyError:
            res = self['RDLENGTH'].li
            return dyn.block(res.int())

        if issubclass(t, parray.block):
            res = self['RDLENGTH'].li
            return dyn.clone(t, blocksize=lambda _, cb=res.int(): cb)

        elif issubclass(t, (ptype.block, pstr.string)):
            return dyn.clone(t, length=self['RDLENGTH'].li.int())
        return t

    def __Padding_RDATA(self):
        res, field = self['RDLENGTH'].li, self['RDATA'].li
        return dyn.block(max(0, res.int() - field.size()))

    _fields_ = [
        (Label, 'NAME'),
        (TYPE, 'TYPE'),
        (CLASS, 'CLASS'),
        (u32, 'TTL'),
        (u16, 'RDLENGTH'),
        (__RDATA, 'RDATA'),
        (__Padding_RDATA, 'Padding(RDATA)'),
    ]

    def alloc(self, **fields):
        fields.setdefault('CLASS', 'IN')
        res = super(RR, self).alloc(**fields)
        return res.set(RDLENGtH=res['RDATA'].size())

class RRcount(pstruct.type):
    _fields_ = [
        (u16, 'QDCOUNT'),
        (u16, 'ANCOUNT'),
        (u16, 'NSCOUNT'),
        (u16, 'ARCOUNT'),
    ]

    def summary(self):
        fields = ['qd', 'an', 'ns', 'ar']
        return ', '.join("{:s}={:d}".format(name, self[fld].int()) for name, fld in zip(fields, self))

class RRset(parray.type):
    _object_ = RR

class Message(pstruct.type):
    class _Question(parray.type):
        _object_ = Q

        def summary(self):
            iterable = (item.summary() for item in self)
            return "({:d}) {:s}".format(len(self), ', '.join(iterable))

    def __Question(self):
        res = self['Counts'].li
        count = res['QDCOUNT'].int()
        return dyn.clone(self._Question, length=count)

    def __Response(field):
        def field(self, field=field):
            res = self['Counts'].li
            count = res[field].int()
            return dyn.clone(RRset, length=count)
        return field

    _fields_ = [
        (u16, 'Id'),
        (Header, 'Header'),
        (RRcount, 'Counts'),
        (__Question, 'Question'),
        (__Response('ANCOUNT'), 'Answer'),
        (__Response('NSCOUNT'), 'Authority'),
        (__Response('ARCOUNT'), 'Additional'),
        (ptype.block, 'Padding'),
    ]

class MessageTCP(pstruct.type):
    def __padding_message(self):
        res, message = (self[fld].li for fld in ['length', 'message'])
        return dyn.block(max(0, res.int() - message.size()))

    _fields_ = [
        (u16, 'length'),
        (Message, 'message'),
        (__padding_message, 'padding(message)'),
    ]

class Stream(parray.infinite):
    _object_ = MessageTCP

if __name__ == '__main__':
    import sys, operator
    import ptypes, protocol.dns as dns
    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    res = 'fce2 0100 0001 0000 0000 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001               '.replace(' ', '')
    res = 'fce2 8183 0001 0000 0001 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001 0000 0600 0100 000e 1000 4001 610c 726f 6f74 2d73 6572 7665 7273 036e 6574 0005 6e73 746c 640c 7665 7269 7369 676e 2d67 7273 0363 6f6d 0078 67b1 a200 0007 0800 0003 8400 093a 8000 0151 80                           '.replace(' ', '')
    data = fromhex(res)

    a = dns.Message(source=ptypes.prov.bytes(data))
    a=a.l

    print(a['question'])
    print(a['question'][0]['name'])
    print(a['authority'][0])
    x = a['authority'][0]
    print(x['RDATA'])

    data = b''
    data += b"\x00\x34\xba\x0e\x00\x20\x00\x01\x00\x00\x00\x00\x00\x01\x07\x65"
    data += b"\x78\x61\x6d\x70\x6c\x65\x03\x63\x6f\x6d\x00\x00\xfc\x00\x01\x00"
    data += b"\x00\x29\x10\x00\x00\x00\x00\x00\x00\x0c\x00\x0a\x00\x08\x95\x93"
    data += b"\xf7\x69\xe7\x3f\xe5\x48"
    data += b"\x02\x1d\xba\x0e\x84\x80\x00\x01\x00\x14\x00\x00\x00\x01\x07\x65"
    data += b"\x78\x61\x6d\x70\x6c\x65\x03\x63\x6f\x6d\x00\x00\xfc\x00\x01\xc0"
    data += b"\x0c\x00\x06\x00\x01\x00\x01\x51\x80\x00\x28\x04\x64\x6e\x73\x31"
    data += b"\xc0\x0c\x0a\x68\x6f\x73\x74\x6d\x61\x73\x74\x65\x72\xc0\x0c\x77"
    data += b"\x45\xca\x65\x00\x00\x54\x60\x00\x00\x0e\x10\x00\x09\x3a\x80\x00"
    data += b"\x01\x51\x80\xc0\x0c\x00\x02\x00\x01\x00\x01\x51\x80\x00\x02\xc0"
    data += b"\x29\xc0\x0c\x00\x02\x00\x01\x00\x01\x51\x80\x00\x07\x04\x64\x6e"
    data += b"\x73\x32\xc0\x0c\xc0\x0c\x00\x0f\x00\x01\x00\x01\x51\x80\x00\x09"
    data += b"\x00\x0a\x04\x6d\x61\x69\x6c\xc0\x0c\xc0\x0c\x00\x0f\x00\x01\x00"
    data += b"\x01\x51\x80\x00\x0a\x00\x14\x05\x6d\x61\x69\x6c\x32\xc0\x0c\xc0"
    data += b"\x29\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x01\xc0"
    data += b"\x29\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xc0\x6b\x00\x01\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x02\xc0\x6b\x00\x1c\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x02\x03\x66\x74\x70\xc0\x0c\x00\x05\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x0b\x08\x73\x65\x72\x76\x69\x63\x65\x73"
    data += b"\xc0\x0c\xc0\x80\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00"
    data += b"\x01\x05\xc0\x80\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa"
    data += b"\xbb\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\xc0\x95"
    data += b"\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x06\xc0\x95"
    data += b"\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\xc1\x05\x00\x01\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x0a\xc1\x05\x00\x01\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x0b\xc1\x05\x00\x1c\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x10\xc1\x05\x00\x1c\x00\x01\x00\x01\x51\x80"
    data += b"\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    data += b"\x00\x11\x03\x77\x77\x77\xc0\x0c\x00\x05\x00\x01\x00\x01\x51\x80"
    data += b"\x00\x02\xc1\x05\xc0\x0c\x00\x06\x00\x01\x00\x01\x51\x80\x00\x18"
    data += b"\xc0\x29\xc0\x30\x77\x45\xca\x65\x00\x00\x54\x60\x00\x00\x0e\x10"
    data += b"\x00\x09\x3a\x80\x00\x01\x51\x80\x00\x00\x29\x10\x00\x00\x00\x00"
    data += b"\x00\x00\x1c\x00\x0a\x00\x18\x95\x93\xf7\x69\xe7\x3f\xe5\x48\x01"
    data += b"\x00\x00\x00\x5e\xe9\xba\x4a\x3e\x33\x62\x66\xee\x4a\xfc\xde"

    ptypes.setsource(ptypes.prov.bytes(data))
    z = dns.Stream()
    z=z.l

    print(z.size())
    print(z[1]['length'])
    print(z[1]['message'])
    print(z[1]['message'].size())
    x = z[1]['message']
    print(x)

    print(x['question'][0])
    print(x['answer'][19])

    data = '1f990120000100000000000106676f6f676c6503636f6d0000010001000029100000000000000c000a0008dd288f3fc1040a68'
    z = dns.Message(source=ptypes.prov.bytes(fromhex(data)))
    z=z.l
