import logging
from datetime import datetime
import ptypes
from ptypes import *

class guint32(pint.uint32_t): pass
class guint16(pint.uint16_t): pass
class gint32(pint.int32_t): pass
class gint32(pint.int32_t): pass

class pcap_hdr_t(pstruct.type):
    class version(pstruct.type):
        _fields_ = [(guint16,'major'),(guint16,'minor')]

    def __version(self):
        magic_number = self['magic_number'].li.serialize()
        if magic_number == b'\xa1\xb2\xc3\xd4':
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.bigendian
        elif magic_number == b'\xd4\xc3\xb2\xa1':
            self.attributes['pcap_byteorder'] = ptypes.config.byteorder.littleendian
        else:
            logging.warn("Unable to determine byteorder : {!r}".format(magic_number))
        return self.version

    _fields_ = [
        (dyn.block(4), 'magic_number'),
        (__version, 'version'),
        (gint32, 'thiszone'),
        (guint32, 'sigfigs'),
        (guint32, 'snaplen'),
        (guint32, 'network'),
    ]

class pcaprec_hdr_s(pstruct.type):
    class timestamp(pstruct.type):
        _fields_ = [
            (guint32, 'sec'),
            (guint32, 'usec'),
        ]
        def now(self):
            ts = self['sec'].int() + self['usec'].int()/1000000.0
            return datetime.fromtimestamp(ts)

        def summary(self):
            return self.now().isoformat()

    _fields_ = [
        (timestamp, 'ts'),
        (guint32, 'incl_len'),
        (guint32, 'orig_len'),
    ]

class Packet(pstruct.type):
    def __header(self):
        res = pcaprec_hdr_s
        return dyn.clone(res, recurse=dict(byteorder=self.pcap_byteorder))

    _fields_ = [
        (__header, 'header'),
        (lambda s: dyn.block(s['header']['incl_len'].li.int()), 'data'),
    ]

class List(parray.infinite):
    _object_ = Packet

    def summary(self):
        l = len(self)
        if l == 1:
            return '..1 packet..'
        return '..%d packets..'% l

    def within(self, start, end):
        for n in self:
            d = n['header'].now()
            if start >= d > end:
                yield n
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
    import ptypes,libpcap,osi
    s = ptypes.file('~/work/nezzwerk/pcap/win-2008.updates.restart.pcap')
    a = libpcap.File(source=s)
    b = a.l
    c = b['packets']

    packet = osi.default
    z = [x['data'].cast(packet) for x in c]
