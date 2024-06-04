'''
Multipoint Application Sharing protocol (T.128)
'''
import sys, ptypes, protocol.gcc as gcc
from ptypes import *
integer_types, string_types = ptypes.integer_types, ptypes.string_types

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### atomic definitions
class Integer8(pint.uint8_t): pass
class Integer16(pint.uint16_t): pass
class Integer32(pint.uint32_t): pass

class Boolean8(pint.enum, Integer8):
    _values_ = [
        ('FALSE', 0x00),
        ('TRUE', 0x01),
    ]

class Boolean16(pint.enum, Integer16):
    _values_ = [
        ('FALSE', 0x0000),
        ('TRUE', 0x0001),
    ]

class ShareId(pstruct.type):
    class UserId(pint.enum, pint.littleendian(gcc.ChannelId)):
        '''default value is set to server channel id (1002)'''
        _values_ = [
            ('serverChannelId', 1002),
        ]
        def properties(self):
            res = super(ShareId.UserId, self).properties()
            if self.initializedQ():
                res['valid'] = self.valid()
            return res
        def default(self):
            return self.set(0x3ea)
        def valid(self):
            return self.copy().default().int() == self.int()
        def alloc(self, **attrs):
            return super(ShareId.UserId, self).alloc(**attrs).default()

    _fields_ = [
        (UserId, 'userId'),
        (pint.uint16_t, 'counter'),
    ]

    def alloc(self, **fields):
        res = super(ShareId, self).alloc(**fields)
        if 'userId' not in res:
            res['userId'].default()
        return res

    def summary(self):
        return "userId={:d} counter={:d}".format(self['userId'].int(), self['counter'].int())

class Coordinate16(Integer16): pass

### Container types
class Rectangle16(pstruct.type):
    _fields_ = [
        (Integer16, 'left'),
        (Integer16, 'top'),
        (Integer16, 'right'),
        (Integer16, 'bottom'),
    ]

### Lookup types
class PDUType(ptype.definition):
    cache = {}

    class type(pbinary.enum):
        length, _values_ = 4, [
            ('confirmActive', 3),
            ('data', 7),
            ('deactivateAll', 6),
            ('deactivateOther', 4),
            ('deactivateSelf', 5),
            ('demandActive', 1),
            ('requestActive', 2),
            ('serverRedirect', 10),

            ('undocumented9', 9),   # implementation at rdpwd.sys+13022 (SaveClientRandom?)
        ]

class CapabilitySetType(ptype.definition):
    cache = {}

    class Choice(pint.enum, pint.uint16_t):
        _values_ = [
            ('bitmapCacheCapabilitySet', 4),
            ('bitmapCapabilitySet', 2),
            ('colorCacheCapabilitySet', 10),
            ('controlCapabilitySet', 5),
            ('generalCapabilitySet', 1),
            ('orderCapabilitySet', 3),
            ('pointerCapabilitySet', 8),
            ('activationCapabilitySet', 7),
            ('shareCapabilitySet', 9),

            ('soundCapabilitySet', 12),
            ('inputCapabilitySet', 13),
            ('fontCapabilitySet', 14),
            ('brushCapabilitySet', 15),
            ('glyphCacheCapabilitySet', 16),
            ('offscreenCacheCapabilitySet', 17),
            ('bitmapCacheHostSupportCapabilitySet', 18),
            ('bitmapCacheCapabilitySetRevision2', 19),
            ('virtualChannelCapabilitySet', 20),
            ('drawNineGridCacheCapabilitySet', 21),
            ('drawGdiPlusCapabilitySet', 22),
            ('railCapabilitySet', 23),
            ('windowCapabilitySet', 24),
            ('desktopCompositionCapabilitySet', 25),
            ('multipleFragmentUpdateCapabilitySet', 26),
            ('largePointerCapabilitySet', 27),
            ('surfaceCommandsCapabilitySet', 28),
            ('bitmapCodecsCapabilitySet', 29),
            ('frameAcknowledgementCapabilityType', 30),
        ]

class PDUType2(ptype.definition):
    cache = {}

    class type(pint.enum, pint.uint8_t):
        _values_ = [
            ('application', 25),
            ('control', 20),            # implemented at rdpwd.sys+1252f
            ('font', 11),
            ('flowResponse', 66),
            ('flowStop', 67),
            ('flowTest', 65),
            ('input', 28),              # implemented at rdpwd.sys+1251e
            ('mediatedControl', 29),
            ('pointer', 27),
            ('remoteShare', 30),
            ('synchronize', 31),
            ('update', 2),
            ('updateCapability', 32),
            ('windowActivation', 23),
            ('windowList', 24),

            ('refreshRectangle', 33),   # implemented at rdpwd.sys+1250e
            ('playSound', 34),
            ('suppressOutput', 35),     # implemented at rdpwd.sys+124fe
            ('shutdownRequest', 36),    # implemented at rdpwd.sys+124ee
            ('shutdownDenied', 37),
            ('saveSessionInfo', 38),
            ('fontList', 39),           # implemented at rdpwd.sys+1253f
            ('fontMap', 40),
            ('setKeyboardIndicators', 41),
            ('bitmapCachePersistentList', 43),
            ('bitmapCacheErrorPDU', 44),
            ('setKeyboardIMEStatus', 45),
            ('offscreenCacheErrorPDU', 46),
            ('setErrorInfoPDU', 47),
            ('drawNineGridErrorPDU', 48),
            ('drawGdiPlusErrorPDU', 49),
            ('arcStatusPDU', 50),
            ('statusInfoPDU', 54),
            ('monitorLayoutPDU', 55),
        ]

class PDUTypeFlow(ptype.definition):
    cache = {}
    class type(pint.enum, Integer16):
        _values_ = [
            ('response', 66),
            ('stop', 67),
            ('test', 65),
        ]

### capability set definitions
class OSMajorType(pint.enum, pint.uint16_t):
    _values_ = [
        ('unspecified', 0),
        ('windows', 1),
        ('os2', 2),
        ('macintosh', 3),
        ('unix', 4),
        ('ios', 5),
        ('osx', 6),
        ('android', 7),
        ('chromeOS', 8),
    ]

class OSMinorType(pint.enum, pint.uint16_t):
    _values_ = [
        ('unspecified', 0),
        ('windows-31x', 1),
        ('windows-95', 2),
        ('windows-NT', 3),
        ('oOS2-V21', 4),
        ('power-pc', 5),
        ('macintosh', 6),
        ('native-XServer', 7),
        ('pseudo-XServer', 8),
        ('windows-RT', 9),
    ]

@CapabilitySetType.define
class GeneralCapabilitySet(pstruct.type):
    type = 1

    class _protocolVersion(pint.enum, Integer16):
        _values_ = [
            ('TS_CAPS_PROTOCOLVERSION', 0x0200),
        ]
        def default(self):
            return self.set(0x0200)
        def valid(self):
            return self.copy().default().int() == self.int()
        def properties(self):
            res = super(GeneralCapabilitySet._protocolVersion, self).properties()
            res['valid'] = self.valid()
            return res

    @pbinary.littleendian
    class _extraFlags(pbinary.flags):
        _fields_ = [
            (5, 'unused0'),
            (1, 'NO_BITMAP_COMPRESSION_HDR'),
            (5, 'unused6'),
            (1, 'ENC_SALTED_CHECKSUM'),
            (1, 'AUTORECONNECT_SUPPORTED'),
            (1, 'LONG_CREDENTIALS_SUPPORTED'),
            (1, 'reserved'),
            (1, 'FASTPATH_OUTPUT_SUPPORTED'),
        ]

    def __refreshRectSupport(self):
        return pint.uint_t if self.blocksize() < 22 else Boolean16
    def __suppressOutputSupport(self):
        return pint.uint_t if self.blocksize() < 24 else Boolean16

    _fields_ = [
        (OSMajorType, 'osMajorType'),
        (OSMinorType, 'osMinorType'),
        (_protocolVersion, 'protocolVersion'),
        (Integer16, 'pad2octetsA'),
        (Integer16, 'generalCompressionTypes'),
        (_extraFlags, 'extraFlags'),
        (Integer16, 'updatecapabilityFlag'),
        (Integer16, 'remoteUnshareFlag'),
        (Integer16, 'generalCompressionLevel'),
        (Integer16, 'pad2octetsC'),

        #(Boolean16, 'refreshRectSupport'),
        #(Boolean16, 'suppressOutputSupport'),
        (__refreshRectSupport, 'refreshRectSupport'),
        (__suppressOutputSupport, 'suppressOutputSupport'),
    ]

@pbinary.littleendian
class BitmapCompressionCapabilityFlags(pbinary.enum):
    length, _values_ = 16, [
        ('FALSE', 0x0000),
        ('TRUE', 0x0001),
    ]

@pbinary.littleendian
class DRAW_(pbinary.flags):
    _fields_ = [
        (3, 'unused'),
        (1, 'UNUSED_FLAG'),
        (1, 'ALLOW_SKIP_ALPHA'),
        (1, 'ALLOW_COLOR_SUBSAMPLING'),
        (1, 'ALLOW_DYNAMIC_COLOR_FIDELITY'),
        (1, 'RESERVED'),
    ]

@CapabilitySetType.define
class BitmapCapabilitySet(pstruct.type):
    type = 2

    _fields_ = [
        (Integer16, 'preferredBitsPerPixel'),
        (Boolean16, 'receive1BitPerPixelFlag'),
        (Boolean16, 'receive4BitsPerPixelFlag'),
        (Boolean16, 'receive8BitsPerPixelFlag'),
        (Integer16, 'desktopWidth'),
        (Integer16, 'desktopHeight'),
        (Integer16, 'pad2octetsA'),
        (Boolean16, 'desktopResizeFlag'),
        (BitmapCompressionCapabilityFlags, 'bitmapCompressionType'),
        (Integer8, 'highColorFlags'),
        (DRAW_, 'drawingFlags'),

        (Boolean16, 'multipleRectangleSupport'),
        (Integer16, 'pad2octetsB'),
    ]

@pbinary.littleendian
class OrderCapabilityFlags(pbinary.flags):
    _fields_ = [
        (8, 'unused0'),
        (1, 'orderFlagsExtraFlags'),
        (1, 'solidPatternBrushOnly'),
        (1, 'colorIndexSupport'),
        (1, 'unused11'),
        (1, 'zeroBoundsDeltasSupport'),
        (1, 'cannotReceiveOrders'),
        (1, 'negotiateOrderSupport'),
        (1, 'unused15'),
    ]

@pbinary.littleendian
class TextCapabilityFlags(pbinary.flags):
    _fields_ = [
        (5, 'unused0'),
        (1, 'allowCellHeight'),
        (1, 'useBaselineStart'),
        (1, 'unused7'),
        (1, 'checkFontSignatures'),
        (1, 'unused9'),
        (1, 'allowDeltaXSimulation'),
        (4, 'unused11'),
        (1, 'checkFontAspect'),
    ]

@pbinary.littleendian
class ORDERFLAGS_EX_(pbinary.flags):
    _fields_ = [
        (13, 'unused0'),
        (1, 'ALTSEC_FRAME_MARKER_SUPPORT'),
        (1, 'CACHE_BITMAP_REV3_SUPPORT'),
        (1, 'unused15'),
    ]

class ORD_LEVEL_(pint.enum, Integer16):
    _values_ = [
        ('LEVEL_1_ORDERS', 1),
    ]
    def default(self):
        return self.set('LEVEL_1_ORDERS')
    def valid(self):
        return self.copy().default().int() == self.int()
    def properties(self):
        res = super(ORD_LEVEL_, self).properties()
        res['valid'] = self.valid()
        return res

@CapabilitySetType.define
class OrderCapabilitySet(pstruct.type):
    type = 3
    class _orderSupport(parray.type):
        length, _object_ = 32, Boolean8

        def __init__(self, **attrs):
            super(OrderCapabilitySet._orderSupport, self).__init__(**attrs)
            self.__nameByIndex__ = { key : name for name, key in self._values_ }
            self.__indexByName__ = { name : key for name, key in self._values_ }

        def __getindex__(self, index):
            undefined = 'undefinedOrder'
            return self.__indexByName__.get(index, int(index[len(undefined):]) if isinstance(index, string_types) and index.startswith(undefined) else index)

        def summary(self):
            res = [ index for index, item in enumerate(self) if item.int() > 0 ]
            res = [ "{:s}({:d})".format(self.__nameByIndex__.get(index, "undefinedOrder"), index) for index in res ]
            return "{{{:s}}}".format(', '.join(res))

        def details(self):
            res = []
            for index, item in enumerate(self):
                res.append("[{:x}] <instance {:s} '{:s}'> (index {:d}) {:s}".format(item.getoffset(), item.classname(), self.__nameByIndex__.get(index, "undefinedOrder{:d}".format(index)), index, item.summary()))
            return '\n'.join(res)

        def repr(self):
            return self.details()

        _values_ = [
            ('destinationBltSupport', 0),
            ('patternBltSupport', 1),
            ('screenBltSupport', 2),
            ('memoryBltSupport', 3),
            ('memoryThreeWayBltSupport', 4),
            ('textSupport', 5),
            ('extendedTextSupport', 6),
            ('rectangleSupport', 7),
            ('lineSupport', 8),
            ('frameSupport', 9),
            ('opaqueRectangleSupport', 10),
            ('desktopSaveSupport', 11),
            #('undefinedOrder12', 12),
            #('undefinedOrder13', 13),
            #('undefinedOrder14', 14),
            ('multipleDestinationBltSupport', 15),
            ('multiplePatternBltSupport', 16),
            ('multipleScreenBltSupport', 17),
            ('multipleOpaqueRectangleSupport', 18),
            ('fastIndexSupport', 19),
            ('polygonSCSupport', 20),
            ('polygonCBSupport', 21),
            ('polylineSupport', 22),
            #('undefinedOrder23', 23),
            ('fastGlyphSupport', 24),
            ('ellipseSCSupport', 25),
            ('ellipseCBSupport', 26),
            ('glyphIndexSupport', 27),
            #('undefinedOrder28', 28),
            #('undefinedOrder29', 29),
            #('undefinedOrder30', 30),
            #('undefinedOrder31', 31),
        ]

    _fields_ = [
        (dyn.array(pint.uint8_t, 16), 'terminalDescriptor'),
        (Integer32, 'pad4octetsA'),
        (Integer16, 'desktopXGranularity'),
        (Integer16, 'desktopYGranularity'),
        (Integer16, 'pad2octetsA'),
        (Integer16, 'maximumOrderLevel'),
        (Integer16, 'numberFonts'),
        (OrderCapabilityFlags, 'orderFlags'),
        (_orderSupport, 'orderSupport'),
        (TextCapabilityFlags, 'textFlags'),

        (ORDERFLAGS_EX_, 'orderSupportExFlags'),
        (Integer32, 'pad4octetsB'),
        (Integer32, 'desktopSaveSize'),

        (Integer16, 'pad2octetsC'),
        (Integer16, 'pad2octetsD'),
        (Integer16, 'textANSICodePage'),
        (Integer16, 'pad2octetsE'),
    ]

@pbinary.littleendian
class ControlCapabilityFlags(pbinary.flags):
    _fields_ = [
        (15, 'unused'),
        (1, 'allowMediateControl'),
    ]

class ControlPriority(pint.enum, Integer16):
    _values_ = [
        ('always', 1),
        ('never', 2),
        ('confirm', 3),
    ]

@CapabilitySetType.define
class ControlCapabilitySet(pstruct.type):
    type = 5
    _fields_ = [
        (ControlCapabilityFlags, 'controlFlags'),
        (Boolean16, 'remoteDetachFlag'),
        (ControlPriority, 'controlInterest'),
        (ControlPriority, 'detachInterest'),
    ]

@CapabilitySetType.define
class ActivationCapabilitySet(pstruct.type):
    type = 7
    _fields_ = [
        (Boolean16, 'helpKeyFlag'),
        (Boolean16, 'helpIndexKeyFlag'),
        (Boolean16, 'helpExtendedKeyFlag'),
        (Boolean16, 'windowActivateFlag'),
    ]

@CapabilitySetType.define
class PointerCapabilitySet(pstruct.type):
    type = 8
    _fields_ = [
        (Boolean16, 'colorPointerFlag'),
        (Integer16, 'colorPointerCacheSize'),
        (Integer16, 'pointerCacheSize'),
    ]

@CapabilitySetType.define
class ShareCapabilitySet(pstruct.type):
    type = 9
    _fields_ = [
        (ShareId.UserId, 'nodeID'),
        (Integer16, 'pad2octets'),
    ]

@CapabilitySetType.define
class ColorCacheCapabilitySet(pstruct.type):
    type = 10
    _fields_ = [
        (Integer16, 'colorTableCacheSize'),
        (Integer16, 'pad2octetsA'),
    ]

class CapabilitySet(pstruct.type):
    def __capabilityParameters(self):
        type, capacity = (self[fld].li for fld in ['capabilitySetType','lengthCapability'])
        total = type.size() + capacity.size()
        return CapabilitySetType.get(type.int(), blocksize=lambda self, cb=max(0, capacity.int() - total): cb)

    _fields_ = [
        (CapabilitySetType.Choice, 'capabilitySetType'),
        (Integer16, 'lengthCapability'),
        (__capabilityParameters, 'capabilityData'),
    ]

    def alloc(self, **fields):
        res = super(CapabilitySet, self).alloc(**fields)
        if 'capabilitySetType' not in fields:
            res.set(capabilitySetType=res['capabilityData'].type)
        if 'lengthCapability' not in fields:
            res.set(lengthCapability=self['capabilityData'].size() + sum(self[fld].size() for fld in ['capabilitySetType','lengthCapability']))
        return res

class CombinedCapabilities(pstruct.type):
    _fields_ = [
        (Integer16, 'numberCapabilities'),
        (Integer16, 'pad2octets'),
        (lambda self: dyn.array(CapabilitySet, self['numberCapabilities'].li.int()), 'capabilitySets'),
    ]

    def alloc(self, **fields):
        res = super(CombinedCapabilities, self).alloc(**fields)
        return res if 'numberCapabilities' in fields else res.set(numberCapabilities=len(res['capabilitySets']))

### PDUType definitions

# XXX: Microsoft's ms-rdpbcgr specification didn't describe the following structures
#      as an enumeration and so they initially weren't properly implemented.  After
#      realizing this, the definitions were then ported to the T.128 naming scheme.
#      So don't be surprised if you see mixing-and-matching of ms-rdpbcgr vs T.128
#      naming schemes.

@pbinary.littleendian
class PDUShareType(pbinary.struct):
    _fields_ = [
        (12, 'protocolVersion'),
        (PDUType.type, 'type'),
    ]

class ShareControlHeader(pstruct.type):
    def __pduSource(self):
        # In some cases (DeactivateAllPDU), the blocksize() of this PDU might be
        # 4 which requires discarding the pduSource. To fix this, we check for
        # the size explicitly and only include it if the size is correct.
        try:
            res = self.getparent(SharePDU)
            return pint.uint_t if res['totalLength'].li.int() == 4 else ShareId.UserId

        except ptypes.error.ItemNotFoundError: pass
        return ShareId.UserId

    _fields_ = [
        (PDUShareType, 'pduType'),
        (__pduSource, 'pduSource'),
    ]

    def summary(self):
        res = []
        res.append("pduSource={:s}".format(self['pduSource'].summary()))
        res.append("pduType={:s}({:d}) protocolVersion={:d}".format(self['pduType'].field('type').str(), self['pduType']['type'], self['pduType']['protocolVersion']))
        return ' '.join(res)

class PACKET_COMPR_(pbinary.enum):
    width, _values_ = 4, [
        ('TYPE_8K', 0x0),
        ('TYPE_64K', 0x1),
        ('TYPE_RDP6', 0x2),
        ('TYPE_RDP61', 0x3),
    ]

class ShareControlPDU(pstruct.type):
    def __shareControlPacket(self):
        try:
            parent = self.getparent(SharePDU)
            length = parent['totalLength'].li

        # If we don't have a parent, we can't determine the totalLength and
        # so we don't need to abate this field
        except ptypes.error.ItemNotFoundError:
            res = self['shareControlHeader'].li
            return PDUType.withdefault(res['pduType']['type'], ptype.undefined)

        # However, if we do have a length then use it to abate the structure
        # that gets chosen as shareControlPacket
        res = self['shareControlHeader'].li
        total = length.size() + res.size()
        return PDUType.get(res['pduType']['type'], ptype.block, blocksize=lambda self, cb=max(0, length.int() - total): cb)

    _fields_ = [
        (ShareControlHeader, 'shareControlHeader'),
        (__shareControlPacket, 'shareControlPacket'),
    ]

class SourceDescriptor(ptype.block):
    def summary(self):
        data = self.serialize().decode('latin1')
        encoded = data.encode('unicode_escape')
        return "({:d}) \"{:s}\"".format(self.size(), encoded.decode(sys.getdefaultencoding()).replace('"', '\\"'))

@PDUType.define
class DemandActivePDU(pstruct.type):
    type = 0x1

    _fields_ = [
        (ShareId, 'shareId'),
        (Integer16, 'lengthSourceDescriptor'),
        (Integer16, 'lengthCombinedCapabilities'),
        (lambda self: dyn.clone(SourceDescriptor, length=self['lengthSourceDescriptor'].li.int()), 'sourceDescriptor'),
        (CombinedCapabilities, 'combinedCapabilities'),

        (pint.uint32_t, 'sessionId'),
    ]

    def alloc(self, **fields):
        res = super(DemandActivePDU, self).alloc(**fields)
        flds = {}
        if 'lengthSourceDescriptor' not in fields:
            flds['lengthSourceDescriptor'] = res['sourceDescriptor'].size()
        if 'lengthCombinedCapabilities' not in fields:
            flds['lengthCombinedCapabilities'] = res['combinedCapabilities'].size()
        return res.set(**flds) if flds else res

@PDUType.define
class RequestActivePDU(DemandActivePDU):
    type = 2

    _fields_ = [
        (Integer16, 'lengthSourceDescriptor'),
        (Integer16, 'lengthCombinedCapabilities'),
        (lambda self: dyn.clone(SourceDescriptor, length=self['lengthSourceDescriptor'].li.int()), 'sourceDescriptor'),
        (CombinedCapabilities, 'combinedCapabilities'),
    ]

@PDUType.define
class ConfirmActivePDU(DemandActivePDU):
    type = 3

    _fields_ = [
        (ShareId, 'shareId'),
        (ShareId.UserId, 'originatorId'),
        (Integer16, 'lengthSourceDescriptor'),
        (Integer16, 'lengthCombinedCapabilities'),
        (lambda self: dyn.clone(SourceDescriptor, length=self['lengthSourceDescriptor'].li.int()), 'sourceDescriptor'),
        (CombinedCapabilities, 'combinedCapabilities'),
    ]

class DeactivatePDU(pstruct.type):
    '''
    This definition is used only to consolidate all of the deactivation PDUs
    (DeactivateOtherPDU, DeactivateSelfPDU, and DeactivateAllPDU) under the
    same base type so that they can be tested against if necessary.
    '''

@PDUType.define
class DeactivateOtherPDU(DeactivatePDU):
    type = 4
    _fields_ = [
        (ShareId, 'shareId'),
        (ShareId.UserId, 'deactivateId'),
        (Integer16, 'lengthSourceDescriptor'),
        (lambda self: dyn.clone(SourceDescriptor, length=self['lengthSourceDescriptor'].li.int()), 'sourceDescriptor'),
    ]

    def alloc(self, **fields):
        res = super(DeactivateOtherPDU, self).alloc(**fields)
        flds = {}
        if 'lengthSourceDescriptor' not in fields:
            flds['lengthSourceDescriptor'] = res['sourceDescriptor'].size()
        return res.set(**flds) if flds else res

    def summary(self):
        res = self['sourceDescriptor'].serialize().decode('latin1')
        encoded = res.encode('unicode_escape')
        return "shareId={:s} deactivateId={:s} sourceDescriptor=\"{:s}\"".format(self['shareId'].summary(), self['deactivateId'].summary(), encoded.decode(sys.getdefaultencoding()).replace('"', '\\"'))

@PDUType.define
class DeactivateSelfPDU(DeactivatePDU):
    type = 5
    _fields_ = [
        (ShareId, 'shareId'),
    ]

    def summary(self):
        return "shareId={:s}".format(self['shareId'].summary())

@PDUType.define
class DeactivateAllPDU(DeactivatePDU):
    type = 6
    _fields_ = [
        (ShareId, 'shareId'),
        (Integer16, 'lengthSourceDescriptor'),
        (lambda self: dyn.clone(SourceDescriptor, length=self['lengthSourceDescriptor'].li.int()), 'sourceDescriptor'),
    ]

    def summary(self):
        res = self.properties()

        # This packet will sometimes be clamped and so to deal with this case,
        # we'll explicitly check for the abated property before dumping it out
        # regularly.
        if not res.get('abated', False):
            res = self['sourceDescriptor'].serialize().decode('latin1')
            encoded = res.encode('unicode_escape')
            return "shareId={:s} sourceDescriptor=\"{:s}\"".format(self['shareId'].summary(), encoded.decode(sys.getdefaultencoding()).replace('"', '\\"'))

        # Otherwise, the structure is abated so we'll emit the parent's summary
        return super(DeactivateAllPDU, self).summary()

class StreamId(pint.enum, Integer8):
    _values_ = [
        ('streamUndefined', 0x0),
        ('streamLowPriority', 0x1),
        ('streamMediumPriority', 0x2),
        ('streamHighPriority', 0x4),
    ]

@pbinary.littleendian
class PACKET_(pbinary.flags):
    _fields_ = [
        (1, 'FLUSHED'),
        (1, 'AT_FRONT'),
        (1, 'COMPRESSED'),
        (1, 'RESERVED'),
        (PACKET_COMPR_, 'CompressionTypeMask'),
    ]

class ShareDataHeader(pstruct.type):
    _fields_ = [
        (ShareId, 'shareId'),
        (Integer8, 'pad1octet'),
        (StreamId, 'streamId'),
    ]

    def summary(self):
        res = []
        res.append("streamId={:s}({:d})".format(self['streamId'].str(), self['streamId'].int()))
        res.append("shareId=({:d},{:d})".format(self['shareId']['userId'].int(), self['shareId']['counter'].int()))
        return ' '.join(res)

class ShareDataPacket(pstruct.type):
    def __data(self):
        res = sum(self[fld].li.size() for fld in ['pduType2','generalCompressedType','generalCompressedLength'])
        if self['generalCompressedType']['COMPRESSED']:
            return dyn.block(max(0, self.blocksize() - res))
        return PDUType2.withdefault(self['pduType2'].li.int(), ptype.block, length=max(0, self.blocksize() - res))

    def __unparsed(self):
        res = sum(self[fld].li.size() for fld in ['pduType2','generalCompressedType','generalCompressedLength','data'])
        return dyn.block(max(0, self.blocksize() - res))

    _fields_ = [
        (PDUType2.type, 'pduType2'),
        (PACKET_, 'generalCompressedType'),
        (Integer16, 'generalCompressedLength'),
        (__data, 'data'),
        (__unparsed, 'undefined'),  # FIXME: this padding is based on the blocksize because I can't really figure out how the PDUType2's are supposed to be sized
    ]

    def summary(self):
        return "pduType2={:s}({:d}) data={:s}".format(self['pduType2'].str(), self['pduType2'].int(), self['data'].instance())

    def alloc(self, **fields):
        res = super(ShareDataPacket, self).alloc(**fields)
        return res.set(pduType2=res['data'].type) if 'pduType2' not in fields and hasattr(res['data'], 'type') else res

@PDUType.define
class DataPDU(pstruct.type):
    type = 7
    def __shareDataPacket(self):

        if False:
            # First check to see if the uncompressed length was specified as then we
            # can use this to calculate the actual blocksize of the ShareDataPacket
            res = self['uncompressedLength'].li
            if res.int():
                return dyn.clone(ShareDataPacket, blocksize=(lambda self, cb=res.int() - 0xe: cb)) if 0xe <= res.int() else ShareDataPacket

        # Otherwise, we'll need to traverse to the parent to grab the packet
        # size. We might not be able to be too sure about this since the field
        # name is "totalLength" which could imply that the length is the full
        # size of the entire SharePDU.
        try:
            parent = self.getparent(SharePDU)
            total = self.getoffset() - parent.getoffset()
            total += sum(self[fld].li.size() for fld in ['shareDataHeader','uncompressedLength'])

        # Nothing was found, so don't bother trying to adjust the ShareDataPacket
        # since this might be being constructed by the user.
        except ptypes.error.ItemNotFoundError:
            return ShareDataPacket

        # Now that we've figured out the total size and our parent that the size
        # is relative to, we should be able to bound the ShareDataPacket according
        # to what's left.
        res = parent['totalLength'].li.int()
        return dyn.clone(ShareDataPacket, blocksize=(lambda self, cb=res - total: cb)) if total <= res else ShareDataPacket

    _fields_ = [
        (ShareDataHeader, 'shareDataHeader'),
        (Integer16, 'uncompressedLength'),
        (__shareDataPacket, 'shareDataPacket'),
    ]

    #def alloc(self, **fields):
    #    fields.setdefault('uncompressedLength', 4)
    #    res = super(DataPDU, self).alloc(**fields)
    #    return res if 'uncompressedLength' in fields else res.set(uncompressedLength=res['shareDataPacket'].size())

    #def summary(self):
    #    res = self['shareDataHeader'].li
    #    return "shareDataHeader.streamId={:s}({:d}) shareDataHeader.pduType2={:s}({:d}) shareDataPacket={:s}".format(res['streamId'].str(), res['streamId'].int(), res['pduType2'].str(), res['pduType2'].int(), self['shareDataPacket'].instance())

### PDUType2 definitions
class UpdateType(ptype.definition):
    cache = {}

    class type(pint.enum, Integer16):
        _values_ = [
            ('orders', 0),
            ('bitmap', 1),
            ('palette', 2),
            ('synchronize', 3),
        ]

@PDUType2.define
class UpdatePDU(pstruct.type):
    type = 2

    def __updateData(self):
        res = self['updateType'].li
        return UpdateType.lookup(res.int(), ptype.undefined)

    _fields_ = [
        (UpdateType.type, 'updateType'),
        (__updateData, 'updateData'),
    ]

    def summary(self):
        return "updateType={:s} updateData={:s}".format(self['updateType'].summary(), self['updateData'].instance())

class RDP_ORDER_(pbinary.flags):
    _fields_ = [
        (1, 'TINY'),
        (1, 'SMALL'),
        (1, 'LASTBOUNDS'),
        (1, 'DELTA'),
        (1, 'CHANGE'),
        (1, 'BOUNDS'),
        (1, 'SECONDARY'),
        (1, 'PRIMARY'),
    ]

class UpdateOrder(pstruct.type):
    _fields_ = [
        (RDP_ORDER_, 'updateHeader'),
        (Integer16, 'updateSize'),
    ]

@UpdateType.define
class UpdateOrdersPDU(pstruct.type):
    type = 0
    _fields_ = [
        (Integer16, 'pad2octetsA'),
        (Integer16, 'numberOrders'),
        (Integer16, 'pad2octetsB'),
        (lambda self: dyn.array(ptype.undefined, self['numberOrders'].li.int()), 'orderList'),  # FIXME: not implemented
    ]

class CompressedBitmapData(pstruct.type):
    _fields_ = [
        (Integer16, 'pad2octets'),
        (Integer16, 'mainBodySize'),
        (Integer16, 'rowSize'),
        (Integer16, 'uncompressedSize'),
        (ptype.block, 'compressedBitmap'),
    ]

class BitmapData(pstruct.type):
    _fields_ = [
        (ptype.block, 'uncompressedBitmapData'),
        (CompressedBitmapData, 'compressedBitmapData'),
    ]

class TS_BITMAP_DATA(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (5, 'unused'),
            (1, 'NO_BITMAP_COMPRESSION_HDR'),
            (9, 'unused'),
            (1, 'BITMAP_COMPRESSION'),
        ]

    _fields_ = [
        (Coordinate16, 'destLeft'),
        (Coordinate16, 'destTop'),
        (Coordinate16, 'destRight'),
        (Coordinate16, 'destBottom'),
        (Integer16, 'width'),
        (Integer16, 'height'),
        (Integer16, 'bitsPerPixel'),

        (Boolean16, 'compressedFlag'),
        (Integer16, 'bitmapLength'),
        (lambda self: dyn.block(self['bitmapLength'].li.int()), 'bitmapData'), # XXX
    ]

@UpdateType.define
class UpdateBitmapPDU(pstruct.type):
    '''Microsoft's version of this structure is different from the T.128 specification'''
    type = 1
    _fields_ = [
        #(Integer16, 'pad2octetsA'),
        (Integer16, 'numberRectangles'),
        (lambda self: dyn.array(TS_BITMAP_DATA, self['numberRectangles'].li.int()), 'rectangles'),
    ]

class Color(pstruct.type):
    _fields_ = [
        (Integer8, 'red'),
        (Integer8, 'green'),
        (Integer8, 'blue'),
    ]

    def summary(self):
        red, green, blue = (self[fld].li.int() for fld in ['red','green','blue'])
        return "red={:d} green={:d} blue={:d}".format(red, green, blue)

@UpdateType.define
class UpdatePalettePDU(pstruct.type):
    type = 2
    _fields_ = [
        (Integer16, 'pad2octets'),
        (Integer32, 'numberColors'),
        (lambda self: dyn.array(Color, self['numberColors'].li.int()), 'palette'),
    ]

@UpdateType.define
class UpdateSynchronizePDU(pstruct.type):
    type = 3
    _fields_ = [
        (Integer16, 'pad2octets'),
    ]

class SynchronizeMessageType(pint.enum, pint.uint16_t):
    _values_ = [
        ('synchronize', 1),
    ]

@PDUType2.define
class SynchronizePDU(pstruct.type):
    type = 31

    _fields_ = [
        (SynchronizeMessageType, 'messageType'),
        (ShareId.UserId, 'targetUser'),
    ]

    def summary(self):
        return "messageType={:s} targetUser={:s}".format(*(self[fld].summary() for fld in ['messageType','targetUser']))

class ControlAction(pint.enum, pint.uint16_t):
    _values_ = [
        ('requestControl', 1),
        ('detach', 3),
        ('grantControl', 2),
        ('cooperate', 4),
    ]

@PDUType2.define
class ControlPDU(pstruct.type):
    type = 20
    _fields_ = [
        (ControlAction, 'action'),
        (ShareId.UserId, 'grantId'),
        (Integer32, 'controlId'),
    ]

    def summary(self):
        return "action={:s} grantId={:s} controlId={:s}".format(*(self[fld].summary() for fld in ['action','grantId','controlId']))

class InputMessageType(pint.enum, Integer16):
    _values_ = [
        ('inputSynchronize', 0),
        ('inputCodePoint', 1),
        ('inputVirtualKey', 2),
        ('inputPointingDevice', 32769),
    ]

@pbinary.littleendian
class PointingDeviceFlags(pbinary.flags):
    _fields_ = [
        (1, 'down'),    # 15
        (1, 'button3'), # 14
        (1, 'button2'), # 13
        (1, 'button1'), # 12
        (1, 'move'),    # 11
        (11, 'unused'),
    ]

class PointingDeviceEvent(pstruct.type):
    _fields_ = [
        (Integer32, 'eventTime'),
        (InputMessageType, 'messageType'),
        (PointingDeviceFlags, 'pointingDeviceFlags'),
        (Coordinate16, 'pointingDeviceY'),
        (Coordinate16, 'pointingDeviceY'),
    ]

@pbinary.littleendian
class KeyboardFlags(pbinary.flags):
    _fields_ = [
        (1, 'release'),     # 15
        (1, 'down'),        # 14
        (1, 'reserved'),
        (1, 'quiet'),       # 12
        (11, 'unused'),
        (1, 'right'),       # 0
    ]

class KeyboardEvent(pstruct.type):
    _fields_ = [
        (Integer32, 'eventTime'),
        (InputMessageType, 'messageType'),
        (KeyboardFlags, 'keyboardFlags'),
        (Integer16, 'keyCode'),
    ]

class InputEvent(pstruct.type):
    # FIXME: the event might be the wrong structure and misdefined for Microsoft's implementation
    class Choice(pbinary.enum):
        length, _values_ = 3, [
            ('pointingDevice', 0),
            ('keyboard', 1),
            ('synchronize', 2),
        ]
    def __event(self):
        res = self['choice'].li
        if res.int() == 0:
            return PointingDeviceEvent
        elif res.int() == 1:
            return KeyboardEvent
        elif res.int() == 2:
            return SynchronizeEvent
        raise NotImplementedError

    _fields_ = [
        (Choice, 'choice'),
        (__event, 'event'),
    ]

class SynchronizeEvent(pstruct.type):
    # FIXME: not sure how this is supposed to be defined
    _fields_ = [
        (Integer32, 'eventTime'),
        (ptype.undefined, 'nonStandardParameters'),
    ]

@PDUType2.define
class InputPDU(pstruct.type):
    type = 28
    _fields_ = [
        (Integer16, 'numberEvents'),
        (Integer16, 'pad2octets'),
        (lambda self: dyn.array(InputEvent, self['numberEvents'].li.int()), 'eventList'),
    ]

@PDUType2.define
@PDUTypeFlow.define
class FlowResponsePDU(pstruct.type):
    type = 66
    _fields_ = [
        (Integer8, 'flowIdentifier'),
        (Integer8, 'flowNumber'),
        (ShareId.UserId, 'pduSource'),
    ]

@PDUType2.define
@PDUTypeFlow.define
class FlowStopPDU(pstruct.type):
    type = 67
    _fields_ = [
        (Integer8, 'flowIdentifier'),
        (ShareId.UserId, 'pduSource'),
    ]

@PDUType2.define
@PDUTypeFlow.define
class FlowTestPDU(pstruct.type):
    type = 65
    _fields_ = [
        (Integer8, 'flowIdentifier'),
        (Integer8, 'flowNumber'),
        (ShareId.UserId, 'pduSource'),
    ]

### Share packets
class FlowPDU(pstruct.type):
    def __flowPacket(self):
        res = self['pduTypeFlow'].li
        return PDUTypeFlow.lookup(res.int(), ptype.undefined)

    _fields_ = [
        (PDUTypeFlow.type, 'pduTypeFlow'),
        (__flowPacket, 'flowPacket'),
    ]

class FlowMarker(pint.enum, Integer16):
    _values_ = [
        ('FlowMarker', 0x8000)
    ]
    def FlowMarkerQ(self):
        return self.str() == 'FlowMarker'
    def properties(self):
        res = super(FlowMarker, self).properties()
        res['FlowMarkerQ'] = self.FlowMarkerQ()
        return res

class SharePDU(pstruct.type):
    def __sharePdu(self):
        res = self['totalLength'].li
        if res.FlowMarkerQ():
            return FlowPDU
        return ShareControlPDU

    _fields_ = [
        (FlowMarker, 'totalLength'),
        (__sharePdu, 'sharePdu'),
    ]

    def alloc(self, **fields):
        res = super(SharePDU, self).alloc(**fields)
        return res if 'totalLength' in fields else res.set(totalLength='FlowMarker') if isinstance(res['sharePdu'], FlowPDU) else res.set(totalLength=res['totalLength'].size() + res['sharePdu'].size())

