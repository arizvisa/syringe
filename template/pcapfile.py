import sys, logging, itertools, functools, math, fractions, datetime
import ptypes
from ptypes import *

class guint32(pint.uint32_t): pass
class guint16(pint.uint16_t): pass
class gint32(pint.int32_t): pass
class gint32(pint.int32_t): pass

class version(pstruct.type):
    _fields_ = [
        (guint16, 'major'),
        (guint16, 'minor')
    ]

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

class pcap_hdr_t(pstruct.type):
    def __byteorder(self):
        magic_number = self['magic_number'].li.serialize()
        if magic_number == b'\xa1\xb2\xc3\xd4':
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.bigendian
        elif magic_number == b'\xd4\xc3\xb2\xa1':
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.littleendian
        else:
            logging.warning("Unable to determine byteorder : {!r}".format(magic_number))
        return ptype.undefined

    _fields_ = [
        (dyn.block(4), 'magic_number'),
        (__byteorder, 'byteorder'),
        (version, 'version'),
        (gint32, 'thiszone'),
        (guint32, 'sigfigs'),
        (guint32, 'snaplen'),
        (guint32, 'network'),
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

    _fields_ = [
        (__header, 'header'),
        (lambda self: dyn.block(self['header']['incl_len'].li.int()), 'data'),
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
        self.attributes.update(self['header'].attributes)
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
