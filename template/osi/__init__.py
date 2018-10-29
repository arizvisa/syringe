from ptypes import ptype, parray, pstruct

# FIXME: this packet structure doesn't properly incorporate all the layers
#        in a portable fashion

from . import datalink, network
from ptypes import dyn

class layers(parray.terminated):
    protocol = ptype.block
    leftover = None
    def __nextlayer(self):
        if len(self) == 0:
            return self.protocol

        last = self.value[-1].l
        try:
            t,sz=last.nextlayer()
            if t is None and self.leftover is not None:
                return dyn.block(self.leftover)

            if self.leftover is not None:
                self.leftover -= last.size()
                return t

            if t is None and self.leftover is None:
                self.leftover = 0
                return dyn.block(0)

            self.leftover = sz
            return t

        except (AttributeError,NotImplementedError):
            pass

        self.leftover -= last.size()
        return dyn.block(self.leftover)

    def isTerminator(self, value):
        if self.leftover is None:
            return False
        assert self.leftover >= 0, 'More than one layer contained within payload: %s'% '\n'.join(self.backtrace())
        if self.leftover == 0:
            return True
        return False

    _object_ = __nextlayer

def protocol(layer):
    return ptype.clone(layers, protocol=layer)

default = packet = protocol(datalink.ethernet.header)

if __name__ == '__main__':
    import ptypes,osi,libpcap
    filename = 'c:/users/user/work/audit/openldap-2.4.40/ldapsearch.anonymous-base.1.pcap'
    a = libpcap.File(source=ptypes.prov.file(filename,mode='rb'))
    a=a.l
    b = a['packets'][7]['data'].cast(osi.packet)
