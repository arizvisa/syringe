import ptypes, logging
from ptypes import ptype, parray, pstruct, dynamic

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

class data(ptype.block):
    pass

class end(ptype.block, terminal):
    pass

class layers(parray.terminated):
    protocol = ptype.block

    _remaining = None
    def isTerminator(self, value):
        remaining = self._remaining

        # If we decoded an element that's a "terminal", but there's still some bytes remaining, then
        # we're not done yet. Our next element will be the last one that consumes the remaining, and
        # due to not being an instance of "stackable" will terminate the array due to the last case.
        if isinstance(value, terminal) and self._remaining:
            return False

        # If we encountered a "terminal" element and remaining is false-y,
        # then reset it to None, before we terminate reading this array.
        elif isinstance(value, terminal):
            self._remaining = None
            return True

        # All elements of the array should be subclassed from "stackable". We use this in combination
        # with the "_object_" property to determine when we can actually stop decoding the array.
        return not isinstance(value, stackable)

    def _object_(self):

        # If there are no elements in the array, then we use the type
        # stored in the "protocol" attribute as the very first element.
        if not len(self.value):
            self._remaining = None
            return self.protocol

        # Once we have at least one "stackable" element, we
        # can determine which of the layers should follow it.
        previous = self.value[-1]
        size = previous.size()

        # If the last element is not stackable, then we consume whatever bytes
        # are remaining and expect "isTerminator" to terminate the array.
        if not isinstance(previous, stackable):
            return dynamic.clone(end, length=self._remaining) if self._remaining else end

        # Now we can extract the tuple from the previous layer that contains the information
        # to use for the current one. This gives us the next type to return. If we are
        # tracking the remaining octets, then adjust it by the current element size.
        layer, identity, remaining = previous.layer()
        expected = None if self._remaining is None else self._remaining - size

        # If there's some bytes remaining as specified by one of the previous layers and
        # the last layer changed the remaining bytes, then log an error and return a type
        # that consumes the remaining octets. The only time this should happen is if the
        # layers are not linked together properly and our previous layer was wrong.
        if self._remaining is not None and remaining is not None and expected != remaining:
            maximum = max(expected, remaining)
            logging.error("{:s} : Previous layer {:s} suggested {:d} byte{:s} remaining, but an earlier layer specified that {:d} byte{:s} should be left.".format(self.instance(), previous.instance(), remaining, '' if remaining == 1 else 's', expected, '' if expected == 1 else 's'))
            return dynamic.clone(end, length=maximum)

        # If we consumed more bytes than the remaining bytes suggested by a previous
        # layer (<0), then it was wrong and we need to log an error before aborting.
        elif expected is not None and expected < 0:
            logging.error("{:s} : An earlier layer suggested {:d} byte{:s} should be available, but the previous layer {:s} decoded more bytes ({:d}) than should be left.".format(self.instance(), self._remaining or 0, '' if self._remaining == 1 else 's', previous.instance(), size))
            return end if remaining is None else dynamic.clone(end, length=remaining)

        # If we don't know the size and are not tracking anything, then use the
        # size from the previous layer. Otherwise, we adjust the number of
        # remaining octets using the current total we stored in "expected".
        self._remaining = remaining if expected is None else expected

        # If we know there's some number of octets, then assign it to "available".
        # Then we can check if the previous layer gave us a type to actually return.
        available = expected or remaining or 0
        if ptypes.istype(identity):
            # FIXME: we should check if this is a dynamically-sizable type.
            return identity

        # If it didn't give us a definition to use when searching for the id, then
        # we just return a type that consumes whatever number of octets are available.
        elif layer is None:
            return dynamic.clone(end, length=available) if available else end

        # If we were given a layer definition, then we can use with the id that
        # was returned to figure out the next type in the array to return.
        elif layer.has(identity):
            return layer.lookup(identity)

        # If we didn't get any fields that we know then just return a block
        # that consumes whatever is available. This should terminate the array.
        return dynamic.clone(data, length=available) if available else data

default = packet = dynamic.clone(layers, protocol=datalink.ethernet.header)

if __name__ == '__main__':
    import ptypes,osi,libpcap
    filename = 'c:/users/user/work/audit/openldap-2.4.40/ldapsearch.anonymous-base.1.pcap'
    a = libpcap.File(source=ptypes.prov.file(filename,mode='rb'))
    a=a.l
    b = a['packets'][7]['data'].cast(osi.packet)
