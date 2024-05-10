import ptypes, logging
from ptypes import parray, dyn

from .. import layer, stackable, terminal, datalink

class layer(layer):
    cache = {}

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import arp, inet4, inet6

if False:
    class stack(parray.terminated):
        _object_ = lambda s: s.protocol
        protocol = payload = None

        def alloc(self, **attrs):
            self.payload = None
            return super(layer, self).alloc(**attrs)

        # FIXME: this super lame method of calculating the payload size probably
        #        doesn't work with all network-level protocols

        def isTerminator(self, value):
            try:
                sz = value.nextlayersize()
                if self.payload is not None:
                    logging.fatal('%s : overwriting payload-size %x with new size %x', self.name(), self.payload, sz)
                self.payload = sz

            except (AttributeError,NotImplementedError):    # XXX: yea, i know it's bad to use exceptions as substitutes for branches...
                self.payload -= value.blocksize()

            try:
                nxt = value.nextlayer()
                self.protocol = nxt
            except (AttributeError,NotImplementedError):
                return True
            return False

        def nextlayer(self):
            return dyn.block(self.payload)

        def nextlayersize(self):
            return self.payload
