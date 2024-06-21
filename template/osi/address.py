import ptypes, logging, functools, operator, itertools
from ptypes import parray, pint, ptype, pbinary, bitmap

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class family_t(pint.enum):
    '''address family numbers'''
    _values_ = [
        ('other', 0),
        #('ipV4', 1),
        #('ipV6', 2),
        ('ip4', 1),
        ('ip6', 2),
        ('nsap', 3),
        ('hdlc', 4),
        ('bbn1822', 5),
        ('all802', 6),
        ('e163', 7),
        ('e164', 8),
        ('f69', 9),
        ('x121', 10),
        ('ipx', 11),
        ('appleTalk', 12),
        ('decnetIV', 13),
        ('banyanVines', 14),
        ('e164withNsap', 15),
        ('dns', 16),
        ('distinguishedName', 17),      # (Distinguished Name, per X.500)
        ('asNumber', 18),               # (16-bit quantity, per the AS number space)
        ('xtpOverIpv4', 19),
        ('xtpOverIpv6', 20),
        ('xtpNativeModeXTP', 21),
        ('fibreChannelWWPN', 22),
        ('fibreChannelWWNN', 23),
        ('gwid', 24),
        ('afi', 25),
        ('mplsTpSectionEndpointIdentifier', 26),
        ('mplsTpLspEndpointIdentifier', 27),
        ('mplsTpPseudowireEndpointIdentifier', 28),
        ('mtipmultitopologyipversion4 ', 29),
        ('mtipv6multitopologyipversion6 ', 30),
        ('bgpSfc ', 31),
        ('eigrpCommonServiceFamily', 16384),
        ('eigrpIpv4ServiceFamily', 16385),
        ('eigrpIpv6ServiceFamily', 16386),
        ('lispCanonicalAddressFormat', 16387),
        ('bgpLs', 16388),
        ('fortyeightBitMac', 16389),
        ('sixtyfourBitMac', 16390),
        ('oui', 16391),
        ('mac24', 16392),
        ('mac40', 16393),
        ('ipv664', 16394),
        ('rBridgePortID', 16395),
        ('trillNickname', 16396),
        ('universallyUniqueIdentifier', 16397),
        ('routingPolicyAfi', 16398),
        ('mplsNamespaces', 16399),
        ('reserved', 65535),
    ]

class family(ptype.definition):
    cache = {}
    class _enum_(family_t): pass
    attribute = 'family'

@family.define
class other_addr(ptype.block):
    family = family.enum.byname('other')

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

@family.define
class in4_addr(pint.enum, u_long):
    family = family.enum.byname('ip4')
    _values_ = [
        ('ALL-SYSTEMS', 0xE0000001),
        ('ALL-ROUTERS', 0xE0000002),
        ('DVRMP', 0xE0000004),
        ('ALL-OSPF', 0xE0000005),
        ('ALL-OSPF-DR', 0xE0000006),
        ('ALL-RIPv2', 0xE0000009),
        ('EIGRP', 0xE000000A),
        ('PIM', 0xE000000D),
        ('VRRP', 0xE0000012),
        ('IPAllL1ISs', 0xE0000013),
        ('IPAllL2ISs', 0xE0000014),
        ('IPAllIntermediate', 0xE0000015),
        ('IGMPv3', 0xE0000016),
        ('HSRPv2', 0xE0000066),
        ('MDAP', 0xE0000067),
        ('PTPv2-Peer', 0xE000006B),
        ('AllJoyn', 0xE0000071),
        ('MDNS', 0xE00000FB),
        ('LLMNR', 0xE00000FC),
        ('Teredo-Discovery', 0xE00000FD),
        ('NTP-Client', 0xE0000101),
        ('SLPv1-General', 0xE0000116),
        ('SLPv1-Agent', 0xE0000123),
        ('AUTO-RP-ANNOUNCE', 0xE0000127),
        ('AUTO-RP-DISCOVERY', 0xE0000128),
        ('H.323', 0xE0000129),
        ('PTPv2', 0xE0000181),
        ('SSDP', 0xEFFFFFFA),
        ('SLPv2', 0xEFFFFFFA),
    ]

    def __format__(self, spec):
        hash = spec.find('#')
        if spec.endswith('A'):
            spec = spec[:-1] if hash < 0 else spec[:hash] + spec[1 + hash:-1]
            octets = bytearray(self.serialize())
            dotted = "{:d}.{:d}.{:d}.{:d}".format(*octets)
            res = "{:#s}({:s})".format(self, dotted) if hash >= 0 and self.has(self.int()) else dotted
            return "{:{:s}s}".format(res, spec)
        return super(in4_addr, self).__format__(spec)

    def summary(self):
        res = self.int()
        integer = bitmap.new(res, 32)
        octets = bitmap.split(integer, 8)
        if self.has(res):
            return '{:#s}({:#x}) : {:d}.{:d}.{:d}.{:d}'.format(self, *map(bitmap.int, [integer] + octets))
        return '{:#x} : {:d}.{:d}.{:d}.{:d}'.format(*map(bitmap.int, [integer] + octets))

    def set(self, integer):
        if isinstance(integer, str) and self.has(integer):
            return self.__setvalue__(integer)
        elif isinstance(integer, str):
            octets = integer.split('.', 3)
            return self.set([int(item) for item in integer.split('.')])
        elif isinstance(integer, (tuple, list)):
            octets = bitmap.join([bitmap.new(item, 8) for item in integer])
            integer = bitmap.push(octets, bitmap.new(0, 32 - bitmap.size(octets)))
            return self.set(bitmap.int(integer))
        elif not bitmap.isinteger(integer):
            raise TypeError(integer)
        return super(in4_addr, self).set(integer)

    def is_linklocal(self):
        '''169.254/16'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(16) == 0xA9FE0000

    def is_multicast(self):
        '''224/4'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(4) == 0xE0000000

    def is_broadcast(self):
        '''224/4'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(32) == 0xFFFFFFFF

    def is_local(self):
        '''127/8'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        Fmask = Fcidr(8 * self.blocksize())
        return self.int() & Fmask(8) == 0x7F000000

    def is_private(self):
        '''10/8 172.16/12 192.168/16'''
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        address, Fmask = self.int(), Fcidr(8 * self.blocksize())
        return any(address & Fmask(bits) == network for bits, network in [(8, 0x0A00000000), (12, 0xAC100000), (16, 0xC0A80000)])

class u6_addr32(pint.uint32_t): pass

@family.define
class in6_addr(parray.type):
    family = family.enum.byname('ip6')

    _object_, length = u6_addr32, 4

    def summary(self):
        iterable = (item.int() for item in self)
        res = functools.reduce(lambda agg, item: agg * pow(2, 32) + item, iterable, 0)
        num = bitmap.new(res, 128)
        components = bitmap.split(num, 16)

        # FIXME: there's got to be a more elegant way than a hacky state machine
        result, counter = [], 0
        for item in map(bitmap.number, components):
            if counter < 2:
                if item == 0:
                    counter = 1
                    if len(result) == 0:
                        result.append('')

                elif counter > 0:
                    result.extend(['', "{:x}".format(item)])
                    counter = 2
                continue
            result.append("{:x}".format(item))
        return ':'.join(result + ([':'] if counter == 1 else []))

    def is_linklocal(self):
        # fe80::/10
        res = functools.reduce(lambda agg, item: agg * pow(2, 32) + item, iterable, 0)
        Fcidr = lambda size: lambda bits, broadcast=pow(2, size) - 1: broadcast & ~(pow(2, size - bits) - 1)
        return res & Fcidr(128)(10) == 0xfe800000000000000000000000000000

    def set(self, *values, **attributes):
        if len(values) != 1:
            return super(in6_addr, self).set(*values, **attributes)
        [value] = values
        if isinstance(value, (tuple, list)):
            value = [integer for integer in itertools.chain(operator.mul([0], self.length - len(value)), value)]
        return super(in6_addr, self).set(value, **attributes)

class oui_prefix(pbinary.struct):
    _fields_ = [
        (6, 'sextet'),
        (1, 'local'),
        (1, 'multicast'),
    ]
    def set(self, *values, **fields):
        if fields:
            return super(oui, self).set(*values, **fields)
        [integer] = values
        fields['multicast'] = 1 if integer & 0x01 else 0
        fields['local'] = 1 if integer & 0x02 else 0
        fields['sextet'], _ = divmod(integer & 0xfc, 4)
        return super(oui, self).set(**fields)

# TODO: it's probably better to format the whole ethaddr with a
#       binary type that includes an enumeration so that we can
#       include any special link addresses as req'd by the IANA.

@family.define
class ethaddr(parray.type):
    family = family.enum.byname('fortyeightBitMac')

    length, _object_ = 6, lambda self: u_char if self.value else oui_prefix

    def summary(self):
        oui = self[0]
        scope = 'local' if oui['local'] else 'global'
        cast = 'multicast' if oui['multicast'] else 'unicast'
        octets = [ "{:02X}".format(octet.int()) for octet in self ]
        return "({:s}) {:s}".format(','.join([scope,cast]), '-'.join(octets))

    def __setvalue__(self, *values, **attributes):
        if len(values) > 1:
            return super(lladdr, self).__setvalue__(*values, **attributes)
        [hwaddr] = values if values else ['']
        if not isinstance(hwaddr, ptypes.string_types):
            return super(lladdr, self).__setvalue__(*values, **attributes)
        octets = [int(octet, 16) for octet in hwaddr.split(':', max(0, self.length - 1))] if hwaddr else []
        octets = [octet for octet in itertools.chain(octets, [0] * self.length)][:self.length]
        return super(lladdr, self).__setvalue__(octets, **attributes)

    def set(self, *values, **fields):
        '''Allow setting the address as a list of bytes with any fields that are given.'''
        oui = {}
        if 'sextet' in fields:
            oui['sextet'] = fields.pop('sextet')
        if 'local' in fields:
            oui['local'] = fields.pop('local')
        if 'multicast' in fields:
            oui['multicast'] = fields.pop('multicast')

        # if no fields were specified, then just use the parent implementation.
        if not oui:
            return super(lladdr, self).set(*values, **fields)

        # if not values were set, then, also use the parent implementation.
        elif not values:
            res = super(lladdr, self).set(*values, **fields)
            res[0].set(**oui) if oui else res[0]
            return res

        # if we were given a list, then apply it to the lowest
        # octets along with the fields that were given.
        [octets] = values
        if isinstance(octets, (tuple, list, bytes, bytearray)):
            res = super(lladdr, self).set([octet for octet in itertools.chain([0] * max(0, self.length - len(octets)), bytearray(octets))])
            res[0].set(**oui)
            return res

        # if we were given a string or an integer, then we
        # ensure it is a valid integer so that we can mask it.
        elif isinstance(octets, ptypes.integer_types):
            integer = octets
        elif isinstance(octets, ptypes.string_types):
            octets = [item for item in map(int, octets.split('.', 3))]
            integer = functools.reduce(lambda agg, octet: 0x100 * agg + octet, octets, 0)
        else:
            raise TypeError(octets)

        # divide up the integer into separate octets, and then
        # prefix the IANA OUI before applying the given fields.
        lower, octets = integer & 0x007fffff, [0x00, 0x00, 0x5E]
        little = [ divmod(lower & 0xff * pow(2, exponent), pow(2, exponent))[0] for exponent in range(0, 24, 8) ]

        # FIXME: these prefixes should be extracted into an enumeration so that
        #        support for v6 multicast(0x333300) and CBOR can also be added.

        # now we can set the octets, then the fields, and then return it.
        res = super(lladdr, self).set(octets + little[::-1], **fields)
        res[0].set(**oui)
        return res
