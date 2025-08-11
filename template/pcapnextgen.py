'''
https://www.ietf.org/archive/id/draft-ietf-opsawg-pcapng-03.txt
'''
import sys, logging, itertools, functools, math, fractions, datetime
import ptypes, osi
from ptypes import *

# just a function for automatically customizing the byteorder
def order(type):
    def reorder(self):
        if not(hasattr(self, 'pcap_byteorder')):
            return type

        order = self.pcap_byteorder
        if order == 'big':
            return pint.bigendian(type)
        elif order == 'little':
            return pint.littleendian(type)
        return type
    return reorder

class ordered_uinteger(pint.uint_t):
    @property
    def byteorder(self):
        order = self.pcap_byteorder if hasattr(self, 'pcap_byteorder') else sys.byteorder
        if order == 'big':
            return ptypes.config.byteorder.bigendian
        elif order == 'little':
            return ptypes.config.byteorder.littleendian
        return ptypes.Config.integer.order

class ordered_sinteger(pint.uint_t):
    @property
    def byteorder(self):
        order = self.pcap_byteorder if hasattr(self, 'pcap_byteorder') else sys.byteorder
        if order == 'big':
            return ptypes.config.byteorder.bigendian
        elif order == 'little':
            return ptypes.config.byteorder.littleendian
        return ptypes.Config.integer.order

class u8(ordered_uinteger): length = 1
class u16(ordered_uinteger): length = 2
class u32(ordered_uinteger): length = 4
class u64(ordered_uinteger): length = 8
class s8(ordered_sinteger): length = 1
class s16(ordered_sinteger): length = 2
class s32(ordered_sinteger): length = 4
class s64(ordered_sinteger): length = 8

class BlockType(ptype.definition):
    cache = {}
    class _enum_(pint.enum, u32):
        pass

class Block(pstruct.type):
    def __Body(self):
        res, length, fields = self['Type'].li, self['Length'].li, ['Type', 'Length', 'Length']
        used = sum(self[fld].li.size() for fld in fields)
        size = max(0, length.int() - used)
        return BlockType.get(res.int(), _length_=size)

    def __Padding(self):
        res, fields = self['Length'].li, ['Type', 'Length', 'Length', 'Body']
        used = sum(self[fld].li.size() for fld in fields)
        size = max(0, res.int() - used)
        return dyn.block(size) if size else ptype.block

    def __Options(self):
        res, length, fields = self['Type'].li, self['Length'].li, ['Type', 'Length', 'Body', 'Padding', 'Length']
        total = sum(self[fld].li.size() for fld in fields)
        size = max(0, length.int() - total)

        definition = BlockOptionType.withdefault(res.int())
        opt_record = dyn.clone(OptionRecord, _definition_=definition)
        if size:
            return dyn.clone(OptionList, _object_=opt_record)
        return dyn.clone(parray.type, _object_=opt_record)

    _fields_ = [
        (BlockType.enum, 'Type'),
        (u32, 'Length'),
        (__Body, 'Body'),
        (__Padding, 'Padding'),
        (__Options, 'Options'),
        (u32, 'SuffixLength')
    ]

class OptionType(ptype.definition):
    cache, default = {}, ptype.block
    class _enum_(pint.enum, u16):
        pass

class BlockOptionType(ptype.definition):
    cache, default = {}, OptionType

class OptionRecord(pstruct.type):
    _definition_ = None
    def __Value(self):
        code, res = (self[fld].li for fld in ['Code', 'Length'])
        object_t = (self._definition_ or OptionType).withdefault(code.int())
        if issubclass(object_t, (ptype.block, pstr.string)):
            return dyn.clone(object_t, length=res.int())
        return res

    def __Padding(self):
        length, value = (self[fld].li for fld in ['Length', 'Value'])
        res, extra = divmod(length.int(), 4)
        count = 1 + res if extra else res
        unaligned = 4 * count
        padding = max(0, unaligned - value.size())
        return dyn.block(padding) if padding else ptype.block

    _fields_ = [
        (lambda self: OptionType.enum, 'Code'),
        (u16, 'Length'),
        (__Value, 'Value'),
        (__Padding, 'Padding'),
    ]

# FIXME: these options exist for all block types
@OptionType.define
class opt_endofopt(ptype.block):
    type = 0
@OptionType.define
class opt_comment(ptype.block):
    type = 1

class OptionList(parray.terminated):
    #_object_ = OptionRecord
    def isTerminator(self, opt):
        return opt['Code'].int() == 0

class MagicNumber(pint.enum, pint.uint32_t):
    _values_ = [
        ('big', 0x1A2B3C4D),
        ('little', 0x4D3C2B1A),
    ]

    def order(self):
        if self['big']:
            return 'big'
        elif self['little']:
            return 'little'
        data = self.serialize()
        logging.warning("Assuming host order ({:s}) due to being unable to determine byteorder : {:s}".format(sys.byteorder, data.hex().upper()))
        return sys.byteorder

class Version(pstruct.type):
    _fields_ = [
        (u16, 'Major'),
        (u16, 'Minor'),
    ]

    def summary(self):
        iterable = (self[fld] for fld in ['Major', 'Minor'])
        return "{!s} : major={:#x} minor={:#x}".format('.'.join(map("{:d}".format, iterable)), self['Major'], self['Minor'])

    def set(self, *args, **fields):
        if args:
            res, = args
            if isinstance(res, tuple):
                major, minor = res
                fields.setdefault('Minor', minor)
                fields.setdefault('Major', major)
                return self.set(**fields)

            gcd = fractions.gcd if sys.version_info.major < 3 else math.gcd
            lcm = lambda *numbers: functools.reduce(lambda x, y: (x * y) // gcd(x, y), numbers, 1)

            mantissa, integer = math.modf(res)
            fraction = fractions.Fraction.from_float(mantissa).limit_denominator()
            next10 = pow(10, math.ceil(math.log10(fraction.denominator)))
            exponent = math.log10(lcm(fraction.denominator, next10))

            fields.setdefault('Minor', math.trunc(0.5 + mantissa * pow(10, math.ceil(exponent))))
            fields.setdefault('Major', math.trunc(integer))
            return self.set(**fields)
        return super(Version, self).set(**fields)

class Timestamp(pstruct.type):
    _fields_ = [
        (u32, 'High'),
        (u32, 'Low'),
    ]

@BlockType.define
class SectionHeader(pstruct.type):
    type = 0x0A0D0D0A
    def __ByteOrderMagic(self):
        magic_number = self['Magic'].li
        if magic_number['big']:
            self.attributes['pcap_byteorder'] = 'big'
        elif magic_number['little']:
            self.attributes['pcap_byteorder'] = 'little'
        else:
            logging.warning("Unable to determine byteorder : {}".format(magic_number))
        return ptype.undefined

    _fields_ = [
        (MagicNumber, 'Magic'),
        (__ByteOrderMagic, 'ByteOrder'),
        (Version, 'Version'),
        (u64, 'SectionLength'),
    ]

@BlockOptionType.define
class SectionHeaderOptionType(OptionType):
    type = SectionHeader.type
    cache = { name : field for name, field in OptionType.cache.items() }

@SectionHeaderOptionType.define
class shb_hardware(pstr.string):
    type = 2
@SectionHeaderOptionType.define
class shb_os(pstr.string):
    type = 3
@SectionHeaderOptionType.define
class shb_userappl(pstr.string):
    type = 4

# FIXME: We need to track everytime we decode one of these records so that we
#        can figure out which link type is needed to decode a captured packet.
@BlockType.define
class InterfaceDescription(pstruct.type):
    type = 0x00000001
    class _LinkType(osi.datalink.LINKTYPE_, u16):
        pass
    _fields_ = [
        (order(_LinkType), 'LinkType'),
        (u16, 'Reserved'),
        (u32, 'SnapLen'),

    ]

@BlockType.define
class PacketBlock(pstruct.type):
    type = 0x00000002

    def __Data(self):
        id = self['InterfaceID'].li
        length = self['CapturedPacketLength'].li
        # FIXME: we should be using the interface id to determine the link type
        #        needed to decode the data of this packet.
        return dyn.block(length.int())

    def __Padding(self):
        length, data = (self[fld].li for fld in ['CapturedPacketLength', 'Data'])
        res, extra = divmod(length.int(), 4)
        count = 1 + res if extra else res
        unaligned = 4 * count
        padding = max(0, unaligned - data.size())
        return dyn.block(padding) if padding else ptype.block

    _fields_ = [
        (u16, 'InterfaceID'),
        (u16, 'DropsCount'),
        (Timestamp, 'Timestamp'),
        (u32, 'CapturedPacketLength'),
        (u32, 'OriginalPacketLength'),
        (__Data, 'Data'),
        (__Padding, 'Padding'),
    ]

@BlockType.define
class SimplePacket(pstruct.type):
    type = 0x00000003
    def __Data(self):
        res = self['Length'].li
        return dyn.block(res.int())
    def __Padding(self):
        length, data = (self[fld].li for fld in ['Length', 'Data'])
        res, extra = divmod(length.int(), 4)
        count = 1 + res if extra else res
        unaligned = 4 * count
        padding = max(0, unaligned - data.size())
        return dyn.block(padding) if padding else ptype.block
    _fields_ = [
        (u32, 'Length'),
        (__Data, 'Data'),
        (__Padding, 'Padding'),
    ]

class NameResolutionRecordType(ptype.definition):
    cache = {}
    class _enum_(pint.enum, u16):
        pass

class NameResolutionRecord(pstruct.type):
    def __Value(self):
        res = self['Length'].li
        return dyn.block(res.int())
    def __Padding(self):
        length, value = (self[fld].li for fld in ['Length', 'Value'])
        res, extra = divmod(length.int(), 4)
        count = 1 + res if extra else res
        unaligned = 4 * count
        padding = max(0, unaligned - value.size())
        return dyn.block(padding) if padding else ptype.block
    _fields_ = [
        (NameResolutionRecordType.enum, 'Type'),
        (u16, 'Length'),
        (__Value, 'Value'),
        (__Padding, 'Padding'),
    ]

@BlockType.define
class NameResolution(parray.terminated):
    type = 0x00000004
    _object_ = NameResolutionRecord
    def isTerminator(self, record):
        return record['Type']['nrb_record_end']

@NameResolutionRecordType.define
class nrb_record_end(ptype.block):
    type = 0x0000
@NameResolutionRecordType.define
class nrb_record_ipv4(osi.address.in4_addr):
    type = 0x0001
@NameResolutionRecordType.define
class nrb_record_ipv6(osi.address.in6_addr):
    type = 0x0002

# FIXME: these options are specific to the NameResolution block.
@BlockOptionType.define
class NameServiceOptionType(OptionType):
    type = NameResolution.type
    cache = { name : field for name, field in OptionType.cache.items() }

@NameServiceOptionType.define
class ns_dnsname(ptype.block):
    type = 2
@NameServiceOptionType.define
class ns_dnsIP4addr(osi.address.in4_addr):
    type = 3
@NameServiceOptionType.define
class ns_dnsIP6addr(osi.address.in6_addr):
    type = 4

@BlockType.define
class InterfaceStatistics(pstruct.type):
    type = 0x00000005
    _fields_ = [
        (u32, 'InterfaceID'),
        (Timestamp, 'Timestamp'),
    ]

# FIXME: these options are specific to the InterfaceStatistics block.
@BlockOptionType.define
class InterfaceStatisticsOptionType(OptionType):
    type = InterfaceStatistics.type
    cache = { name : field for name, field in OptionType.cache.items() }

@InterfaceStatisticsOptionType.define
class isb_starttime(u64):
    type = 2 
@InterfaceStatisticsOptionType.define
class isb_endtime(u64):
    type = 3 
@InterfaceStatisticsOptionType.define
class isb_ifrecv(u64):
    type = 4 
@InterfaceStatisticsOptionType.define
class isb_ifdrop(u64):
    type = 5 
@InterfaceStatisticsOptionType.define
class isb_filteraccept(u64):
    type = 6 
@InterfaceStatisticsOptionType.define
class isb_osdrop(u64):
    type = 7 
@InterfaceStatisticsOptionType.define
class isb_usrdeliv(u64):
    type = 8 

@BlockType.define
class EnhancedPacket(pstruct.type):
    type = 0x00000006
    def __Data(self):
        id = self['InterfaceID'].li
        length = self['CapturedPacketLength'].li
        unknown = dyn.block(length.int()) if length.int() else ptype.block

        # If this instance is not attached to a BlockArray or Blocks type, then
        # there isn't a way to determine how to decode the EnahancedPacket body.
        if not(self.parent) or not(isinstance(self.parent.parent, (BlockArray, Blocks))):
            return unknown

        # If there's no interfaces that have been enumerated yet, then we have
        # no way to know how we're supposed to decode the EnhancedPacket body.
        elif not(self.parent.parent.InterfaceCount()):
            return unknown

        # Otherwise, we can grab the parent and use it to find the descriptor
        # for the "InterfaceId". Then we can use that to get the datalink type.
        else:
            parent = self.parent.parent

        descriptor = parent.InterfaceDescriptor(id.int())
        linktype = descriptor['Body']['LinkType']
        if osi.layer.has(linktype.int()):
            return dyn.clone(osi.layers, protocol=osi.layer.lookup(linktype.int()))
        return unknown

    def __Padding(self):
        length, data = (self[fld].li for fld in ['CapturedPacketLength', 'Data'])
        res, extra = divmod(length.int(), 4)
        count = 1 + res if extra else res
        unaligned = 4 * count
        padding = max(0, unaligned - data.size())
        return dyn.block(padding) if padding else ptype.block

    _fields_ = [
        (u32, 'InterfaceID'),
        (Timestamp, 'Timestamp'),
        (u32, 'CapturedPacketLength'),
        (u32, 'OriginalPacketLength'),
        (__Data, 'Data'),
        (__Padding, 'Padding'),
    ]

# FIXME: these options are specific to the EnhancedPacket block.
@BlockOptionType.define
class EnhancedPacketOptionType(OptionType):
    type = EnhancedPacket.type
    cache = { name : field for name, field in OptionType.cache.items() }

@EnhancedPacketOptionType.define
class epb_flags(pbinary.flags):
    type = 2
    _fields_ = [
        (16, 'errors'),
        (4, 'reserved'),
        (1, 'tcp_offloaded'),
        (1, 'checksum_valid'),
        (1, 'checksum_notready'),
        (4, 'fcs'),
        (3, 'reception_type'),
        (2, 'inbound_outbound'),
    ]
@EnhancedPacketOptionType.define
class epb_hash(pstruct.type):
    type = 3
    def __value(self):
        res = self['algorithm'].li
        algorithm = res.int()
        if algorithm == 2:
            return u32
        elif algorithm == 3:
            return dyn.block(16)
        elif algorithm == 4:
            return u32
        else:
            logging.warning("Unexpected hash algorithm type : {}".format(res))
        return ptype.block
    _fields_ = [
        (u8, 'algorithm'),
        (__value, 'value'),
    ]
@EnhancedPacketOptionType.define
class epb_dropcount(u64):
    type = 4
@EnhancedPacketOptionType.define
class epb_packetid(ptype.block):
    type = 5
@EnhancedPacketOptionType.define
class epb_queue(ptype.block):
    type = 6
@EnhancedPacketOptionType.define
class epb_verdict(ptype.block):
    type = 7

@BlockType.define
class IRIGTimestamp(ptype.block):
    type = 0x00000007

@BlockType.define
class AFDXEncapsulationInformation(ptype.block):
    type = 0x00000008

@BlockType.define
class SystemJournal(ptype.block):
    type = 0x00000009

@BlockType.define
class DecryptionSecrets(pstruct.type):
    type = 0x0000000A
    class _Type(pint.enum, u32):
        _values_ = [
            ('TLS', 0x544c534b),
            ('Wireguard', 0x57474b4c),
            ('NWK', 0x5a4e574b),
            ('APS', 0x5a415053),
        ]
    def __Data(self):
        length = self['Length'].li
        size = length.int()
        return dyn.block(size) if size else ptype.block

    _fields_ = [
        (_Type, 'Type'),
        (u32, 'Length'),
        (__Data, 'Data'),
    ]

@BlockType.define
class HoneMachineInfo(ptype.block):
    type = 0x00000101

@BlockType.define
class HoneConnectionEvent(ptype.block):
    type = 0x00000102

@BlockType.define
class SysdigMachineInfo(ptype.block):
    type = 0x00000201
@BlockType.define
class SysdigProcessInfo(ptype.block):
    type = 0x00000202

@BlockType.define
class SysdigFDList(ptype.block):
    type = 0x00000203
@BlockType.define
class SysdigEvent(ptype.block):
    type = 0x00000204
@BlockType.define
class SysdigInterfaceList(ptype.block):
    type = 0x00000205
@BlockType.define
class SysdigUserList(ptype.block):
    type = 0x00000206
@BlockType.define
class SysdigProcessInfov2(ptype.block):
    type = 0x00000207
@BlockType.define
class SysdigEventWithFlags(ptype.block):
    type = 0x00000208
@BlockType.define
class SysdigProcessInfov3(ptype.block):
    type = 0x00000209
@BlockType.define
class SysdigProcessInfov4(ptype.block):
    type = 0x00000210
@BlockType.define
class SysdigProcessInfov5(ptype.block):
    type = 0x00000211
@BlockType.define
class SysdigProcessInfov6(ptype.block):
    type = 0x00000212
@BlockType.define
class SysdigProcessInfov7(ptype.block):
    type = 0x00000213

class CompressionBlock(pstruct.type):
    def __Data(self):
        res = self['Type'].li
        return max(0, self._length_ - res.size())
    _fields_ = [
        (u8, 'Type'),
        (__Data, 'Data'),
        (ptype.block, 'Padding'),
    ]

class EncryptionBlock(pstruct.type):
    def __Data(self):
        res = self['Type'].li
        return max(0, self._length_ - res.size())
    _fields_ = [
        (u8, 'Type'),
        (__Data, 'Data'),
        (ptype.block, 'Padding'),
    ]

class FieldLength(pstruct.type):
    def __Data(self):
        res = self['Type'].li
        return max(0, self._length_ - res.size())
    _fields_ = [
        (u16, 'CellSize'),
        (__Data, 'Data'),
        (ptype.block, 'Padding'),
    ]

class EndianlessLength(dynamic.union):
    _fields_ = [
        (pint.bigendian(pint.uint32_t), 'big'),
        (pint.littleendian(pint.uint32_t), 'little'),
    ]

class BlockArray(parray.terminated):
    _object_ = Block

    _interfaces_ = None
    def load(self, **attrs):
        self._interfaces_ = []
        return super(BlockArray, self).load(**attrs)

    def isTerminator(self, value):
        index = len(self.value)
        if value['Type']['InterfaceDescription']:
            self._interfaces_.append(index)
        return super(BlockArray, self).isTerminator(value)

    def InterfaceCount(self):
        return len(self._interfaces_)

    def InterfaceDescriptor(self, Id):
        index = self._interfaces_[Id]
        return self[index - 1]

class Blocks(parray.block, BlockArray):
    def load(self, **attrs):
        self._interfaces_ = []
        return super(Blocks, self).load(**attrs)

    def isTerminator(self, value):
        index = len(self.value)
        if value['Type']['InterfaceDescription']:
            self._interfaces_.append(index)
        return super(Blocks, self).isTerminator(value)

class File(pstruct.type):
    def __Body(self):
        type = self['Type'].li
        if not(type['SectionHeader']):
            logging.warning("Unexpected header type : {}".format(type))
            return ptype.block
        return SectionHeader

    def __AssignByteOrder(self):
        body = self['Body'].li
        if not(isinstance(body, SectionHeader)):
            pass
        elif body['Magic']['big']:
            self.attributes['pcap_byteorder'] = self.pcap_byteorder = 'big'
        elif body['Magic']['little']:
            self.attributes['pcap_byteorder'] = self.pcap_byteorder = 'little'
        else:
            return ptype.block
        return ptype.block

    def __Padding(self):
        if not(hasattr(self, 'pcap_byteorder')):
            return ptype.block
        order = self.attributes['pcap_byteorder']
        res = self['Length'].li
        size = res[order].int()

        fields = ['Type', 'Length', 'Length', 'Body', 'Options']
        used = sum(self[fld].li.size() for fld in fields)
        remaining = max(0, size - used)
        return dyn.block(remaining) if remaining else ptype.block

    def __Options(self):
        order = self.attributes.get('pcap_byteorder', sys.byteorder)
        length = self['Length'].li
        size = length[order].int()

        fields = ['Type', 'Length', 'Body', 'Order', 'Length']
        total = sum(self[fld].li.size() for fld in fields)
        size = max(0, size - total)

        definition = BlockOptionType.withdefault(self['Type'].li.int())
        opt_record = dyn.clone(OptionRecord, _definition_=definition)
        if size:
            return dyn.clone(OptionList, _object_=opt_record)
        return dyn.clone(parray.type, _object_=opt_record)

    def __SuffixLength(self):
        order = self.attributes['pcap_byteorder']
        if order == 'little':
            return pint.littleendian(pint.uint32_t)
        return pint.bigendian(pint.uint32_t)

    def __Blocks(self):
        if not(isinstance(self.source, ptypes.provider.bounded)):
            return BlockArray
        size = self.source.size()
        fields = ['Type', 'Length', 'Body', 'Order', 'Options', 'Padding', 'SuffixLength']
        blocksize = size - sum(self[fld].li.size() for fld in fields)
        return dyn.clone(Blocks, blocksize=lambda _, bs=max(0, blocksize): bs)

    _fields_ = [
        (BlockType.enum, 'Type'),
        (EndianlessLength, 'Length'),
        (__Body, 'Body'),
        (__AssignByteOrder, 'Order'),
        (__Options, 'Options'),
        (__Padding, 'Padding'),
        (u32, 'SuffixLength'),
        (__Blocks, 'Blocks'),
    ]

if __name__ == '__main__':
    import ptypes, pcapnextgen
    source = ptypes.setsource(ptypes.provider.file(sys.argv[1], 'rb'))

    file = pcapnextgen.File(source=source)
    file = file.l
