import ptypes, functools, itertools
from ptypes import *

from . import layer, stackable, terminal

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

# TODO: it's probably better to format the whole lladdr with a
#       binary type that includes an enumeration so that we can
#       include any special link addresses as req'd by the IANA.

class oui(pbinary.struct):
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

class lladdr(parray.type):
    length, _object_ = 6, lambda self: u_char if self.value else oui

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

class ethhdr(pstruct.type, stackable):
    def __type(self):
        from .. import network
        # FIXME: these enumerations could be better organized.
        class type(network.layer.enum, u_short):
            pass
        return type

    _fields_ = [
        (lladdr, 'dhost'),
        (lladdr, 'shost'),
        #(u_short, 'type'),
        (__type, 'type'),
    ]

    def layer(self):
        layer, unimplemented, remaining = super(ethhdr, self).layer()
        return layer, self['type'], None

header = ethhdr
