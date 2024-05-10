import ptypes
from ptypes import ptype, parray, pstruct, dynamic

# FIXME: this packet structure doesn't properly incorporate all the layers
#        in a portable fashion
class layer(ptype.definition):
    cache = {}
    class contents(ptype.block):
        pass
    _default_ = contents

class stackable(object):
    _layer_ = layer
    def layer(self):
        '''return the elements used to find the next layer as a tuple composed of the (definition, key, remaining)'''
        return self._layer_, NotImplementedError, None

class terminal(stackable):
    pass

from . import datalink, network, transport

class layers(parray.terminated):
    protocol = ptype.block

    leftover = None     # XXX: this is garbage
    def isTerminator(self, value):
        #if self.leftover is None:
        #    return False
        #assert self.leftover >= 0, 'More than one layer contained within payload: %s'% '\n'.join(self.backtrace())
        #if self.leftover == 0 or value.size() == 0:
        #    return True
        # return False
        if self.leftover is not None:
            self.leftover -= value.size()

        # FIXME: the previous code using "leftover" is likely garbage
        if isinstance(value, terminal) and not self.leftover:
            self.leftover = None
            return True
        return not isinstance(value, stackable)

    def _object_(self):
        if not len(self.value):
            return self.protocol

        prevlayersegment = self.value[-1]
        if not isinstance(prevlayersegment, stackable):
            return ptype.block

        layer, identity, remaining = prevlayersegment.layer()

        print('previous', self.leftover, "{}".format(prevlayersegment))
        print('trying', identity, remaining, layer, layer.cache)

        if self.leftover is not None and remaining is not None:
            raise AssertionError("ERROR: expected {:d}, but {:d} is remaining".format(self.leftover, remaining))
        self.leftover = self.leftover if remaining is None else remaining

        if ptypes.istype(identity):
            return identity
        elif layer is None:
            return dynamic.block(remaining or 0 if self.leftover is None else self.leftover)
        elif layer.has(identity):
            return layer.lookup(identity)
        print('empty', remaining, self.leftover)
        return dynamic.block(self.leftover or 0)

default = packet = ptype.clone(layers, protocol=datalink.ethernet.header)

if __name__ == '__main__':
    import ptypes,osi,libpcap
    filename = 'c:/users/user/work/audit/openldap-2.4.40/ldapsearch.anonymous-base.1.pcap'
    a = libpcap.File(source=ptypes.prov.file(filename,mode='rb'))
    a=a.l
    b = a['packets'][7]['data'].cast(osi.packet)
