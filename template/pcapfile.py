import sys, logging, itertools, functools, math, fractions, datetime
import ptypes, osi
from ptypes import *

class guint32(pint.uint32_t): pass
class guint16(pint.uint16_t): pass
class gint32(pint.int32_t): pass
class gint32(pint.int32_t): pass

class version(pstruct.type):
    def __guint16(self):
        if not(hasattr(self, 'pcap_byteorder')):
            return guint16
        elif self.pcap_byteorder == ptypes.config.byteorder.littleendian:
            return pint.littleendian(guint16)
        elif self.pcap_byteorder == ptypes.config.byteorder.bigendian:
            return pint.bigendian(guint16)
        return guint16

    _fields_ = [
        (__guint16, 'major'),
        (__guint16, 'minor')
    ]

    def summary(self):
        iterable = (self[fld] for fld in ['major', 'minor'])
        return "{!s} : major={:#x} minor={:#x}".format('.'.join(map("{:d}".format, iterable)), self['major'], self['minor'])

    def set(self, *args, **fields):
        if args:
            res, = args
            if isinstance(res, tuple):
                major, minor = res
                fields.setdefault('minor', minor)
                fields.setdefault('major', major)
                return self.set(**fields)

            gcd = fractions.gcd if sys.version_info.major < 3 else math.gcd
            lcm = lambda *numbers: functools.reduce(lambda x, y: (x * y) // gcd(x, y), numbers, 1)

            mantissa, integer = math.modf(res)
            fraction = fractions.Fraction.from_float(mantissa).limit_denominator()
            next10 = pow(10, math.ceil(math.log10(fraction.denominator)))
            exponent = math.log10(lcm(fraction.denominator, next10))

            fields.setdefault('minor', math.trunc(0.5 + mantissa * pow(10, math.ceil(exponent))))
            fields.setdefault('major', math.trunc(integer))
            return self.set(**fields)
        return super(version, self).set(**fields)

@pint.bigendian
class magic_number(pint.enum, guint32):
    _values_ = [
        ('big/microseconds', 0xA1B2C3D4),
        ('little/microseconds', 0xD4C3B2A1),
        ('big/nanoseconds', 0xA1B23C4D),
        ('little/nanoseconds', 0x4D3CB2A1),
    ]

    def order(self):
        if any(self[fld] for fld in ['big/microseconds', 'big/nanoseconds']):
            return 'big'
        elif any(self[fld] for fld in ['little/microseconds', 'little/nanoseconds']):
            return 'little'
        data = self.serialize()
        logging.warning("Assuming host order ({:s}) due to being unable to determine byteorder : {:s}".format(sys.byteorder, data.hex().upper()))
        return sys.byteorder

class pcap_hdr_t(pstruct.type):
    class _linktype(osi.datalink.LINKTYPE_, guint16):
        pass

    class _fcs(pbinary.flags):
        _fields_ = [
            (3, 'number'),
            (1, 'f'),
            (12, 'unknown'),
        ]
    def __byteorder(self):
        magic_number = self['magic_number'].li

        # seconds/microseconds
        if magic_number['big/microseconds']:
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.bigendian
        elif magic_number['little/microseconds']:
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.littleendian

        # seconds/nanoseconds
        elif magic_number['big/nanoseconds']:
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.bigendian
        elif magic_number['little/nanoseconds']:
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.littleendian

        else:
            logging.warning("Unable to determine byteorder : {!r}".format(magic_number))
        return ptype.undefined

    def __order(type):
        def reorder(self):
            res = self['magic_number'].li
            order = res.order()
            if order == 'big':
                return pint.bigendian(type)
            elif order == 'little':
                return pint.littleendian(type)
            return type
        return reorder

    _fields_ = [
        (magic_number, 'magic_number'),
        (__byteorder, 'byteorder'),
        (version, 'version'),
        (__order(gint32), 'thiszone'),
        (__order(guint32), 'sigfigs'),
        (__order(guint32), 'snaplen'),
        (__order(_linktype), 'linktype'),
        (_fcs, 'fcs'),
    ]

    def timezone(self):
        res = self['thiszone'].int()
        delta = datetime.timedelta(seconds=-res)
        return datetime.timezone(delta)

class timestamp(pstruct.type):
    _fields_ = [
        (guint32, 'sec'),
        (guint32, 'usec'),
    ]
    def datetime(self):
        epoch = datetime.datetime(1970, 1, 1)
        delta = datetime.timedelta(seconds=self['sec'].int(), microseconds=self['usec'].int() * 1e-1)
        return epoch + delta

    def summary(self):
        parent = self.getparent(File)
        header, dt = parent['header'], self.datetime()
        res = dt.replace(tzinfo=header.timezone())
        return res.isoformat()

class pcaprec_hdr_s(pstruct.type):
    def __order(type):
        def reorder(self):
            if not(hasattr(self, 'pcap_byteorder')):
                return type

            order = self.pcap_byteorder
            if order == ptypes.config.byteorder.bigendian:
                return pint.bigendian(type)
            elif order == ptypes.config.byteorder.littlendian:
                return pint.littleendian(type)
            return type
        return reorder
    _fields_ = [
        (timestamp, 'ts'),
        (guint32, 'incl_len'),
        (guint32, 'orig_len'),
    ]

    def summary(self):
        included, original = (self[fld].int() for fld in ['incl_len', 'orig_len'])
        timestamp = self['ts'].datetime()
        if original != included:
            return "ts={:s} : incl_len={:+#x} : orig_len={:#x}".format(timestamp.isoformat(), included, original)
        return "ts={:s} : orig_len={:+#x}".format(timestamp.isoformat(), original)

class Packet(pstruct.type):
    def __header(self):
        res = pcaprec_hdr_s
        return dyn.clone(res, recurse=dict(byteorder=self.pcap_byteorder))

    def __data(self):
        header = self['header'].li
        length = header['incl_len']
        if hasattr(self, '_object_'):
            return self._object_
        return dyn.block(length.int())

    def __padding(self):
        header, data = (self[fld].li for fld in ['header', 'data'])
        length = header['incl_len'].int()
        padding = length - header.size()
        if max(0, padding):
            return dyn.block(max(0, padding))
        return ptype.block

    _fields_ = [
        (__header, 'header'),
        (__data, 'data'),
        (ptype.block, 'padding'),
    ]

class List(parray.infinite):
    _object_ = Packet

    def within(self, start, end):
        for item in self:
            dt = item['header'].datetime()
            if start <= dt < end:
                yield item
            continue
        return

class File(pstruct.type):
    def __packets(self):
        header = self['header'].li
        self.attributes.update(self['header'].attributes)
        linktype = header['linktype']
        if osi.layer.has(linktype.int()):
            layers_t = dyn.clone(osi.layers, protocol=osi.layer.lookup(header['linktype'].int()))
            return dyn.clone(List, _object_=dyn.clone(Packet, _object_=layers_t))
        return List

    def blocksize(self):
        if isinstance(self.source, ptypes.provider.bounded):
            return self.source.size()
        return sys.maxint

    _fields_ = [
        (pcap_hdr_t, 'header'),
        (__packets, 'packets'),
    ]

if __name__ == '__main__':
    import ptypes, pcapfile, osi
    packet = osi.packet
    source = ptypes.setsource(ptypes.provider.file(sys.argv[1], 'rb'))
    file = pcapfile.File(source=source)
    file = file.l
    items = file['packets'] if file['packets'][-1].initializedQ() else file['packets'][:-1]
    z = [item['data'].cast(packet) for item in items]
