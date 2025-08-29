import ptypes, builtins, bisect, itertools, logging
from ptypes import *

import ptypes.bitmap as bitmap
from . import layer, stackable, terminal, datalink
from . import utils, address

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass
in_addr = address.in4_addr

class IPOPT_(pint.enum, u_char):
    _values_ = [
        ('EOOL', 0),            # End of Options List [RFC791]
        ('NOP', 1),             # No Operation [RFC791]
        ('SEC', 130),           # Security [RFC1108]
        ('LSR', 131),           # Loose Source Route [RFC791]
        ('TS', 68),             # Time Stamp [RFC791]
        ('E-SEC', 133),         # Extended Security [RFC1108]
        ('CIPSO', 134),         # Commercial Security [draft-ietf-cipso-ipsecurity-01]
        ('RR', 7),              # Record Route [RFC791]
        ('SID', 136),           # Stream ID [RFC791][RFC6814]
        ('SSR', 137),           # Strict Source Route [RFC791]
        ('ZSU', 10),            # Experimental Measurement
        ('MTUP', 11),           # MTU Probe [RFC1063][RFC1191]
        ('MTUR', 12),           # MTU Reply [RFC1063][RFC1191]
        ('FINN', 205),          # Experimental Flow Control
        ('VISA', 142),          # Experimental Access Control [RFC6814]
        ('ENCODE', 15),         # ??? [RFC6814]
        ('IMITD', 144),         # IMI Traffic Descriptor
        ('EIP', 145),           # Extended Internet Protocol [RFC1385][RFC6814]
        ('TR', 82),             # Traceroute [RFC1393][RFC6814]
        ('ADDEXT', 147),        # Address Extension [RFC6814]
        ('RTRALT', 148),        # Router Alert [RFC2113]
        ('SDB', 149),           # Selective Directed Broadcast [RFC6814]
        ('DPS', 151),           # Dynamic Packet State [RFC6814]
        ('UMP', 152),           # Upstream Multicast Pkt. [RFC6814]
    ]

class IP4_OPT_UNPACKED:
    _values_ = [
        ('EOOL', (0,0,0)),          # End of Options List [RFC791]
        ('NOP', (0,0,1)),           # No Operation [RFC791]
        ('SEC', (1,0,2)),           # Security [RFC1108]
        ('LSR', (1,0,3)),           # Loose Source Route [RFC791]
        ('TS', (0,2,4)),            # Time Stamp [RFC791]
        ('E-SEC', (1,0,5)),         # Extended Security [RFC1108]
        ('CIPSO', (1,0,6)),         # Commercial Security [draft-ietf-cipso-ipsecurity-01]
        ('RR', (0,0,7)),            # Record Route [RFC791]
        ('SID', (1,0,8)),           # Stream ID [RFC791][RFC6814]
        ('SSR', (1,0,9)),           # Strict Source Route [RFC791]
        ('ZSU', (0,0,10)),          # Experimental Measurement
        ('MTUP', (0,0,11)),         # MTU Probe [RFC1063][RFC1191]
        ('MTUR', (0,0,12)),         # MTU Reply [RFC1063][RFC1191]
        ('FINN', (1,2,13)),         # Experimental Flow Control
        ('VISA', (1,0,14)),         # Experimental Access Control [RFC6814]
        ('ENCODE', (0,0,15)),       # ??? [RFC6814]
        ('IMITD', (1,0,16)),        # IMI Traffic Descriptor
        ('EIP', (1,0,17)),          # Extended Internet Protocol [RFC1385][RFC6814]
        ('TR', (0,2,18)),           # Traceroute [RFC1393][RFC6814]
        ('ADDEXT', (1,0,19)),       # Address Extension [RFC6814]
        ('RTRALT', (1,0,20)),       # Router Alert [RFC2113]
        ('SDB', (1,0,21)),          # Selective Directed Broadcast [RFC6814]
        ('DPS', (1,0,23)),          # Dynamic Packet State [RFC6814]
        ('UMP', (1,0,24)),          # Upstream Multicast Pkt. [RFC6814]
    ]

class ip4_option(ptype.definition):
    cache = {}
    default = ptype.block
    class _object_(pbinary.flags):
        _fields_ = [
            (1, 'copied'),
            (2, 'class'),
            (5, 'number'),
        ]

class IP4_OPT(ptype.generic): pass
class IP4_OPT_LENGTH(IP4_OPT): pass

class PointerToRouteData(pstruct.type):
    class _pointer(ptype.opointer_t):
        _value_, _object_ = u_char, in_addr
        def _calculate_(self, byte):
            return self.getoffset() + self.size() + byte

    def __route_data(self):
        res, fields = self['length'].li, ['length', 'pointer']
        used = 1 + sum(self[fld].li.size() for fld in fields)
        available = max(0, res.int() - used)
        count, extra = divmod(available, in_addr.length)
        return dyn.array(in_addr, count)

    def __padding(self):
        res, fields = self['length'].li, ['length', 'pointer', 'data']
        used = 1 + sum(self[fld].li.size() for fld in fields)
        missed = max(0, res.int() - used)
        return dyn.block(missed) if missed else ptype.block

    _fields_ = [
        (u_char, 'length'),
        (_pointer, 'pointer'),
        (__route_data, 'data'),
        (__padding, 'padding'),
    ]

    def alloc(self, **fields):
        res = super(PointerToRouteData, self).alloc(**fields)
        if 'length' not in fields:
            res['length'].set(1 + res.size())
        return res

@ip4_option.define
class EOOL(ptype.block, IP4_OPT):
    '''End of Option List'''
    type = 0x00

@ip4_option.define
class NOP(ptype.block, IP4_OPT):
    '''No Operation'''
    type = 0x01

@ip4_option.define
class SEC(pstruct.type, IP4_OPT_LENGTH):
    '''Security (defunct)'''
    type = IPOPT_.byname('SEC')
    _fields_ = [
        (u_short, 'S'),                             # Security
        (u_short, 'C'),                             # Compartments
        (u_short, 'H'),                             # Handling Restrictions
        (dyn.clone(pint.uint_t, length=3), 'TCC'),  # Transmission Control Code
    ]

@ip4_option.define
class SSRR(PointerToRouteData, IP4_OPT):
    '''Strict Source and Record Route'''
    type = IPOPT_.byname('SSR')

@ip4_option.define
class RR(PointerToRouteData, IP4_OPT):
    '''Record Route'''
    type = IPOPT_.byname('RR')

@ip4_option.define
class ZSU(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Measurement'''
    type = 0x0A

@ip4_option.define
class MTUP(u_short, IP4_OPT_LENGTH):
    '''MTU Probe'''
    type = IPOPT_.byname('MTUP')

@ip4_option.define
class MTUR(u_short, IP4_OPT_LENGTH):
    '''MTU Reply'''
    type = IPOPT_.byname('MTUR')

@ip4_option.define
class ENCODE(ptype.block, IP4_OPT_LENGTH):
    '''ENCODE'''
    type = 0x0F

@ip4_option.define
class QS(ptype.block, IP4_OPT_LENGTH):
    '''Quick-Start'''
    type = 0x19

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x1E

@ip4_option.define
class TS(pstruct.type, IP4_OPT_LENGTH):
    '''Time Stamp'''
    type = 0x44

    def __timestamp(self):
        l = self['ipt_len'].li.int()
        return dyn.array(pint.uint32_t, max(0, l - 4))

    _fields_ = [
        #(u_char, 'ipt_code'),
        #(u_char, 'ipt_len'),
        (u_char, 'ipt_ptr'),
        (u_char, 'ipt_flg/ipt_oflw'),
        (__timestamp, 'ipt_timestamp'),
    ]

@ip4_option.define
class TR(pstruct.type, IP4_OPT_LENGTH):
    '''Traceroute'''
    type = IPOPT_.byname('TR')
    _fields_ = [
        (u_short, 'ID'),
        (u_short, 'OHC'),
        (u_short, 'RHC'),
        (in_addr, 'Originator'),
    ]

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x5E

@ip4_option.define
class LSR(PointerToRouteData, IP4_OPT_LENGTH):
    '''Loose Source Route'''
    type = IPOPT_.byname('LSR')

@ip4_option.define
class E_SEC(ptype.block, IP4_OPT_LENGTH):
    '''Extended Security (RIPSO)'''
    type = 0x85

@ip4_option.define
class CIPSO(ptype.block, IP4_OPT_LENGTH):
    '''Commercial IP Security Option'''
    type = 0x86

@ip4_option.define
class SID(u_short, IP4_OPT_LENGTH):
    '''Stream ID'''
    type = 0x88

@ip4_option.define
class VISA(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Access Control'''
    type = 0x8E

@ip4_option.define
class IMITD(ptype.block, IP4_OPT_LENGTH):
    '''IMI Traffic Descriptor'''
    type = 0x90

@ip4_option.define
class EIP(ptype.block, IP4_OPT_LENGTH):
    '''Extended Internet Protocol'''
    type = IPOPT_.byname('EIP')

@ip4_option.define
class ADDEXT(ptype.block, IP4_OPT_LENGTH):
    '''Address Extension'''
    type = 0x93

@ip4_option.define
class SDB(ptype.block, IP4_OPT_LENGTH):
    '''Selective Directed Broadcast'''
    type = 0x95

@ip4_option.define
class DPS(ptype.block, IP4_OPT_LENGTH):
    '''Dynamic Packet State'''
    type = 0x97

@ip4_option.define
class UMP(ptype.block, IP4_OPT_LENGTH):
    '''Upstream Multicast Packet'''
    type = 0x98

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment'''
    type = 0x9E

@ip4_option.define
class FINN(ptype.block, IP4_OPT_LENGTH):
    '''Experimental Flow Control'''
    type = 0xCD

@ip4_option.define
class EXP(ptype.block, IP4_OPT_LENGTH):
    '''RFC3692-style Experiment '''
    type = 0xDE

@ip4_option.define
class RA(pint.enum, u_short, IP4_OPT_LENGTH):
    '''Router Alert'''
    type = IPOPT_.byname('RTRALT')
    _values_ = [
        ('ALERT', 0),
    ]

class ip4_opt(pstruct.type):
    def __Length(self):
        opt = self['ipo_type'].li
        res = ip4_option.lookup(opt.int())
        return u_char if issubclass(res, IP4_OPT_LENGTH) else pint.uint_t

    def __Value(self):
        opt = self['ipo_type'].li
        return ip4_option.lookup(opt.int())

    def __Missed(self):
        res, fields = self['ipo_len'].li, ['ipo_type', 'ipo_len', 'ipo_value']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (IPOPT_, 'ipo_type'),
        (__Length, 'ipo_len'),
        (__Value, 'ipo_value'),
        (__Missed, 'ip_missed'),
    ]

    def alloc(self, **fields):
        res = super(ip4_opt, self).alloc(**fields)
        if 'ipo_len' not in fields:
            res['ipo_len'].set(sum(res[fld].size() for fld in res))
        if 'ipo_type' not in fields and hasattr(res['ipo_value'], 'type'):
            res['ipo_type'].set(res['ipo_value'].type)
        return res

class ip4_options(parray.block):
    _object_ = ip4_opt
    def isTerminator(self, option):
        return option['ipo_type']['EOOL']
    def alloc(self, *values, **attributes):
        if not values:
            return super(ip4_options, self).alloc(*values, **attributes)
        res, [items] = [], values
        for item in items:
            if ptype.isinstance(item) and isinstance(item, IP4_OPT):
                res.append(self._object_().alloc(ipo_value=item))

            elif ptype.istype(item) and issubclass(item, IP4_OPT):
                res.append(self._object_().alloc(ipo_value=item))

            elif isinstance(item, (int, str)):
                res.append(self._object_().alloc(ipo_type=item))

            else:
                res.append(item)
            continue
        return super(ip4_options, self).alloc(res, **attributes)

class ip4_opts(ptype.encoded_t):
    def _object_(self):
        size = self.size()
        return dyn.clone(ip4_options, blocksize = lambda self, sz=size: sz)

@layer.define(type=4)   # protocol number
@datalink.layer.define
class ip4_hdr(pstruct.type, stackable):
    type = 0x0800

    class _ip_h(pbinary.struct):
        _fields_ = [(4,'ver'),(4,'hlen')]

    class _ip_tos(pbinary.struct):
        class _ecn(pbinary.enum):
            length, _values_ = 2, [
                ('NotECT',  0b00),
                ('ECT0',    0b01),
                ('ECT1',    0b10),
                ('CE',      0b11),
            ]

        _fields_ = [
            (6, 'dscp'),
            (_ecn, 'ecn'),
        ]

    class _ip_fragoff(pbinary.flags):
        _fields_ = [
            (1, 'reserved'),
            (1, 'donotfragment'),
            (1, 'morefragments'),
            (13, 'offset')
        ]

    def __ip4_opts(self):
        res, fields = self['ip_h'].li, ['ip_h', 'ip_tos', 'ip_len', 'ip_id', 'ip_fragoff', 'ip_ttl', 'ip_protocol', 'ip_sum', 'ip_src', 'ip_dst']
        size = sum(self[fld].li.size() for fld in fields)
        optsize = max(0, 4 * res['hlen'] - size)
        backing = dyn.block(optsize)
        return dyn.clone(ip4_opts, _value_=backing)

    def __ip_protocol(self):
        from .. import transport
        # FIXME: these enumerations could be better organized.
        class ip_protocol(transport.layer.enum, u_char):
            pass
        return ip_protocol

    _fields_ = [
#        (u_char, 'ip_h'),
        (_ip_h, 'ip_h'),
        (_ip_tos, 'ip_tos'),
        (u_short, 'ip_len'),
        (u_short, 'ip_id'),
        (_ip_fragoff, 'ip_fragoff'),
        (u_char, 'ip_ttl'),
        #(u_char, 'ip_protocol'),
        (__ip_protocol, 'ip_protocol'),
        (u_short, 'ip_sum'),

        (in_addr, 'ip_src'),
        (in_addr, 'ip_dst'),

        (__ip4_opts, 'ip_opt'),
        (dyn.padding(4), 'padding(ip_opt)'),
    ]

    def checksum(self):
        instance = self.copy().set(ip_sum=0)
        return utils.checksum(instance.serialize())

    def layer(self):
        layer, id, remaining = super(ip4_hdr, self).layer()
        header, fields = self['ip_h'].li, ['ip_h', 'ip_tos', 'ip_len', 'ip_id', 'ip_fragoff', 'ip_ttl', 'ip_protocol', 'ip_sum', 'ip_src', 'ip_dst', 'ip_opt', 'padding(ip_opt)']

        # Check if the header length matches the actual size we decoded.
        if 4 * header['hlen'] == sum(self[fld].li.size() for fld in fields):
            return layer, self['ip_protocol'].li.int(), max(0, self['ip_len'].li.int() - 4 * header['hlen'])

        # Otherwise, log a warning before returning the next layer.
        hlen, optsize = 4 * header['hlen'], sum(self[fld].size() for fld in ['ip_opt', 'padding(ip_opt)'])
        hsize = sum(self[fld].size() for fld in fields) - optsize
        logging.warning(u"{:s} : Error decoding the IP4 header. The size specified in the header ({:d}) does not match the size ({:d}) of the header with its options ({:d}).".format(self.instance(), hlen, hsize, optsize))
        return layer, self['ip_protocol'].li, max(0, self['ip_len'].li.int() - 4 * header['hlen'])

header = ip4_hdr

def reassemble(result, **kwds):
    """Coroutine that receives packets and reassembles any discovered v4 fragments.

    This coroutine takes an output list as a parameter, and consumes a tuple
    composed of a unique id and an `osi.layers` packet. Upon closing the
    coroutine, all submitted fragments will be reassembled and appended to the
    output list in the order the fragments were initially received.
    """
    if not(isinstance(result, [].__class__)):
        raise TypeError(u"Expected type {!s}, got {!s}.".format([].__class__, result.__class__))

    # Define an anonymous function that formats all the fields composing the
    # ipv4 stream identification key.
    streamkey_to_descriptions = lambda key: (lambda id, src, dst, proto: tuple(itertools.chain(["{:#0{:d}x}".format(id, 2 + 4)], ["{:#0{:d}x}".format(v4, 2 + 8) for v4 in [src, dst]], ["{:d}".format(proto)])))(*key)

    # Enter main loop for collecting packets and appending them to the stream.
    streams, order, packets, layer_t = {}, [], {}, ip4_hdr
    try:
        while True:
            (id, packet) = (yield)

            # Stash the packet according to the id it was given.
            if id in packets:
                logging.warning(u"Overwriting packet #{:d} ({:d} byte{:s}): {}".format(id, packets[id].size(), '' if packets[id].size() == 1 else 's', packet))
            packets[id] = packet

            # Scan the packet that we received for the IPv4 layer. If we
            # didn't find one, then skip the submitted packet entirely.
            iterable = (index for index, packet in enumerate(packet) if isinstance(packet, layer_t))
            index = next(iterable, -1)
            if index < 0:
                logging.warning(u"Skipping packet #{:d} due to missing {:s} layer: {}".format(id, '.'.join([layer_t.__module__, layer_t.__name__]), packet))
                continue
            layer = packet[index]

            # Figure out the key to use for uniquely identifying the stream.
            fields = ['ip_id', 'ip_src', 'ip_dst', 'ip_protocol']
            key = tuple(layer[fld].int() for fld in fields)
            ip_id, ip_src, ip_dst, ip_proto = streamkey_to_descriptions(key)

            # If we haven't processed this key yet, then add it to a list so
            # that we can preserve the order when assembling the results.
            key not in streams and order.append(key)

            # Gather the fragment information from the IPv4 layer.
            fragoff = layer['ip_fragoff']
            offset, length = 8 * fragoff['offset'], max(0, layer['ip_len'].int() - 4 * layer['ip_h']['hlen'])
            fragmented = fragoff['morefragments'] or offset > 0

            # Initialize the segment tree for the packet fragment.
            start, stop = bounds = offset, offset + length
            tree, tree_index = streams.setdefault(key, ([], {}))
            tree_index.setdefault(start, []), tree_index.setdefault(stop, [])

            # If this packet is not fragmented, then update the tree and
            # index with its exact boundaries.
            if not(fragmented):
                # FIXME: if there's no more fragments, then we received the
                #        last packet and we'll need to combine all fragments
                logging.debug(u"Found non-fragmented packet #{:d} for IPv4 ID {!s} ({!s} -> {!s}) protocol {!s}: {}".format(id, ip_id, ip_src, ip_dst, ip_proto, packet))
                tree[:] = [start, stop]
                tree_index[start] = tree_index[stop] = [(bounds, id)]
                continue

            # if both start and stop indices are the same or they're
            # odd-numbered, then the segment we're going to insert will be
            # overlapping. this is because we always insert the points for
            # each segment into the tree as a pair.
            start_index, stop_index = bisect.bisect_left(tree, start), bisect.bisect_right(tree, stop)

            if start_index % 2 or stop_index % 2 or start_index != stop_index:
                tree[start_index : stop_index] = [start, stop]
                tree_index[start].insert(0, (bounds, id))
                tree_index[stop].insert(0, (bounds, id))

            elif not(start_index % 2 and stop_index % 2):
                tree[start_index : stop_index] = [start, stop]
                tree_index[start].append((bounds, id))
                tree_index[stop].append((bounds, id))

            elif start_index % 2:
                tree[start_index : stop_index] = [stop]
                tree_index[start].append((bounds, id))
                tree_index[stop].append((bounds, id))

            elif stop_index % 2:
                tree[start_index : stop_index] = [start]
                tree_index[start].append((bounds, id))
                tree_index[stop].append((bounds, id))
            continue

    # Once the generator has been exited, we can start assembling each of
    # the streams that we discovered and append them to our results.
    except GeneratorExit:
        pass

    # Iterate through all of the streams that we've found and grab the
    # most recent fragment for each one. The loop that follows this one is
    # then responsible for flatting each segment tree into their bytes.
    contiguous_streams = {}
    for key in streams:
        tree, index = streams[key]
        ip_id, ip_src, ip_dst, ip_proto = streamkey_to_descriptions(key)

        tree, contiguous = contiguous_streams.setdefault(key, (tree, {}))
        for point in tree:
            fragments = index[point]
            if len(fragments) > 1:
                overlaps = [bounds for bounds in {bounds for bounds, _ in fragments}]
                logging.info(u"Found {:d} overlapping IP fragment{:s} for IPv4 ID {!s} ({!s} -> {!s}) protocol {:s} : [{:s}]".format(len(fragments), '' if len(fragments) == 1 else 's', ip_id, ip_src, ip_dst, ip_proto, ', '.join("{:#x}..{:#x}".format(start, stop) for start, stop in overlaps)))
                for bounds, id in fragments:
                    logging.debug(u"Packet contents: {}".format(packets[id]))
                contiguous[point] = fragments[0]
            else:
                contiguous[point] = fragments[0]
            continue
        continue

    # Go through all of the streams where we honored the most recent packet
    # fragment, and assemble each segment tree into its corresponding bytes.
    assembled_streams = {}
    for key in contiguous_streams:
        tree, index = contiguous_streams[key]
        ip_id, ip_src, ip_dst, ip_proto = streamkey_to_descriptions(key)

        offset, assembled = 0, assembled_streams.setdefault(key, bytearray())
        for point in tree:
            (start, stop), id = index[point]
            if offset != start and len(index) > 2:
                count = abs(start - offset)
                left, right = sorted([offset, start])
                logging.warning(u"Found gap from {:#x}..{:#x} ({:d}) for IPv4 ID {!s} ({!s} -> {!s}) protocol {!s}.".format(left, right, count, ip_id, ip_src, ip_dst, ip_proto))

            # Grab the packet by its id and verify that the size is correct.
            packet = packets[id]
            assert(abs(stop - start) == packet[2].size() + packet[3].size())
            assembled[start : stop] = packet[2:].serialize()
            offset = stop
        continue

    # Now go through and append each assembled stream to the results array
    # using the order that was collected when we were reading packets. If we
    # were given a packet layers type, then use it with the assembled streams to
    # instantiate the packet for each connection.
    if 'layer' not in kwds:
        return [ result.append((key, assembled_streams[key])) for key in order ]

    # If we were given a "layer" keyword parameter, then use it to instantiate
    # the packet for each assembled stream.
    packet_t, layer = __import__('osi').layers, kwds['layer']
    for key in order:
        _, _, _, protocol = key
        data = assembled_streams[key]
        packet = packet_t(protocol=layer.lookup(protocol), source=ptypes.prov.bytes(data))
        result.append((key, packet.li))
    return
