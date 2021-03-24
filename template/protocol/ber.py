import sys, logging, math, six, codecs, operator, builtins, itertools, functools
import ptypes, ptypes.bitmap as bitmap, ptypes.utils as utils
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Primitive types for records
class IdentifierLong(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [
            (1, 'continue'),
            (7, 'integer'),
        ]

    def isTerminator(self, value):
        return value['continue'] == 0

    def int(self):
        '''Return the integer from the structure'''
        return functools.reduce(lambda t, item: (t * pow(2,7)) | item['integer'], self, 0)

    def set(self, *integer, **fields):
        '''Apply the specified integer to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer

            # calculate the number of 7-bit pieces for our integer
            res = math.floor(math.log(integer) / math.log(pow(2,7)) + 1)
            length = fields.pop('length', math.trunc(res))

            # slice the integer into 7-bit pieces. we could use ptypes.bitmap, but
            # that requires reading documentation and things. so let's avoid that.
            res = []
            while integer > 0:
                res.insert(0, integer & (pow(2,7) - 1))
                integer >>= 7

            # append any extra zeroes in order to pad the list to the specified length
            res = [0] * (length - len(res)) + res
            return self.alloc(length=length).set([[1, n] for n in res[:-1]] + [[0, res[-1]]])
        return super(IdentifierLong, self).set(*integer, **fields)

class Length(pbinary.struct):
    '''Indefinite Length (short form) 8.1.3.3'''
    def __value(self):
        return (8 * self['count']) if self['form'] else 0

    _fields_ = [
        (1, 'form'),
        (7, 'count'),
        (__value, 'value'),
    ]

    def int(self):
        '''Return the length from the structure'''
        return self['value'] if self['form'] else self['count']

    def set(self, *integer, **fields):
        '''Apply the specified length to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer

            # if our integer can be fit within 7 bits, then just assign it to 'count'
            if integer < pow(2,7):
                return self.alloc(form=0).set(count=integer)

            # otherwise, figure out how many bytes we need to allocate and then
            # simply assign the integer to them
            res = math.floor(math.log(integer) / math.log(pow(2,8)) + 1)
            return self.alloc(form=1, count=math.trunc(res)).set(value=integer)
        return super(Length, self).set(*integer, **fields)

    def IndefiniteQ(self):
        '''Return whether the contents will be terminated by an EOC tag.'''
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'IndefiniteQ')
        return (self['form'], self['count']) == (1, 0)

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Length, self).summary()) + (' Indefinite' if self.IndefiniteQ() else '')

class Tag(pbinary.struct):
    def __TagLong(self):
        return IdentifierLong if self['TagShort'] == 0x1f else dyn.clone(IdentifierLong, length=0)

    _fields_ = [
        (5, 'TagShort'),
        (__TagLong, 'TagLong'),
    ]

    def int(self):
        '''Return the tag number based on the values in our fields'''
        if self['TagShort'] < pow(2,5) - 1:
            return self['TagShort']
        return self['TagLong'].int()

    def set(self, *integer, **fields):
        '''Apply the tag number to the structure'''
        if len(integer) == 1 and isinstance(integer[0], six.integer_types):
            integer, = integer
            return self.alloc(TagShort=integer) if integer < pow(2,5) - 1 else self.alloc(TagShort=pow(2,5) - 1).set(TagLong=integer)
        return super(Tag, self).set(*integer, **fields)

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Tag, self).summary())

class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed'),
        (Tag, 'Tag'),
    ]

    def summary(self):
        klass, constructedQ, tag = self['Class'], self['Constructed'], self['Tag'].int()
        return 'class:{:d} tag:{:d} {:s}'.format(klass, tag, 'Constructed' if constructedQ else 'Universal')

class Constructed(parray.block):
    __object_state__ = None

    @classmethod
    def typename(cls):
        if hasattr(cls, 'type'):
            klass, tag = (Context.Class, cls.type) if isinstance(cls.type, six.integer_types) else cls.type
            return "{:s}<{:d},{:d}>".format(cls.__name__, klass, tag)
        return super(Constructed, cls).typename()

    def load(self, **attrs):
        cls = self.__class__

        # Allocate the lookup table so that we can assign it to ourself
        # while loading. This ties directly into the _object_ method
        # which determines each object to use.
        table = self.__get_lookup_table__()
        with utils.assign(self, __object_state__=table):

            # If the isTerminator method hasn't been overwritten, then we
            # can just use the original loader for the instance.
            if ptypes.utils.callable_eq(cls.isTerminator, Constructed.isTerminator):
                result = super(Constructed, self).load(**attrs)

            # Otherwise, we want to treat this as a parray.terminated instance so
            # that the user can control when the array should stop being loaded.
            else:
                result = super(parray.block, self).load(**attrs)

        # Now our attribute ia removed, and we can return the loaded result.
        return result

    def __setvalue__(self, *args, **attrs):

        # Allocate the lookup table so that we can assign it to ourself
        # while setting. This ties directly into the _object_ method
        # which will use it to determine each element to assign with.
        table = self.__get_lookup_table__()
        with utils.assign(self, __object_state__=table):

            # Call the original __setvalue__ implementation using our object
            # state that we've assigned.
            result = super(Constructed, self).__setvalue__(*args, **attrs)

        # Now we can return our result as if nothing happened.
        return result

    def classname(self):
        if hasattr(self, 'type'):
            klass, tag = (Context.Class, self.type) if isinstance(self.type, six.integer_types) else self.type
            protocol = self.parent.Protocol if self.parent else Protocol

            # Use the protocol to look up the Class and Tag for the type
            # that we're supposed to be.
            K = protocol.lookup(klass)
            try:
                t = K.lookup(tag)

            # If we didn't find it, then we use the same format for an
            # UnknownConstruct type.
            except KeyError:
                return self.typename()
            return t.typename()
        return super(Constructed, self).classname()

    def __get_lookup_table__(self):
        if not hasattr(self, '_fields_'):
            return {}

        # Iterate through all of our fields so that we can collect
        # them into a lookup table.
        res = {}
        for item, name in self._fields_:
            klass, tag = (Context.Class, item.type) if isinstance(item.type, six.integer_types) else item.type
            res[getattr(klass, 'Class', klass), tag] = (name, item)
        return res

    def __getitem__(self, index):
        if not isinstance(index, six.string_types):
            return super(Constructed, self).__getitem__(index)

        # Start by building the lookup table keyed by the field name.
        cls, res = self.__class__, self.__get_lookup_table__()
        table = {name : (klass, tag) for (klass, tag), (name, _) in res.items()}
        if len(res) != len(table):
            logging.warning("{:s}.getitem({!s}) : Duplicate name found in fields for instance {:s}".format('.'.join([cls.__module__, cls.__name__]), index, self.instance()))

        # Now we can search the lookup table for the index that was provided.
        try:
            klasstag = next(item for name, item in table.items() if name.lower() == index.lower())
            index = next(idx for idx, item in enumerate(self.value) if (item.Class(), item.Tag()) == klasstag)

        # If we couldn't find a matching Class and Tag, then raise a KeyError.
        except StopIteration:
            raise KeyError(index)
        return super(Constructed, self).__getitem__(index)

    def _object_(self):
        protocol = self.parent.Protocol if self.parent else Protocol
        objectstate = self.__object_state__

        # Define the closure that we're going to assign to our child
        # elements. This way they can use us to lookup what type should
        # be used when decoding their value.
        def lookup(self, klasstag, protocol=protocol, state=objectstate):
            try:
                _, type = state.pop(klasstag)
                result = type

            # If we couldn't find the klasstag in our current state,
            # then we need to fall-back to a standard protocol lookup.
            except KeyError:
                klass, tag = klasstag

            # Otherwise, we found what we're looking for and can just
            # return the type that was discovered.
            else:
                return result

            # Start by looking up the protocol class, once that's found
            # then we need to lookup the type by its tag.
            K = protocol.lookup(klass)
            try:
                result = K.lookup(tag)

            # If we couldn't find a type matching the right tag number, then
            # we just return None to let the caller know that they need to
            # figure out whether to return an unknown primitive or a construct.
            except KeyError:
                result = None

            # Now we have a type for the caller to use.
            return result

        # All we need to do is return the protocol's Element type with our
        # lookup closure assigned as an attribute for it to use.
        return dyn.clone(protocol.default, Protocol=protocol, __object__=lookup)

    def __summary_items(self, table):
        for item in self.value:
            try:
                if isinstance(item, Element) and item.initializedQ():
                    klasstag = item.Class(), item.Tag()
                    name, type = table.pop(klasstag)
                    yield "{:s}={:s}".format(name, item.__element__())
            except KeyError:
                yield "{:s}".format('???' if item is None else item.classname() if item.initializedQ() else item.typename())
            continue
        return

    def summary(self):
        if self.value is None:
            return '???'

        res = self.__get_lookup_table__()
        iterable = self.__summary_items(res)
        return "{:s} : {{ {:s} }}".format(self.__element__(), ', '.join(iterable))

    def alloc(self, *args, **fields):
        cls, protocol = self.__class__, getattr(self.parent, 'Protocol', Protocol)
        res, table = [], self.__get_lookup_table__()

        # First we need to figure out what positional fields we were
        # given so that we use them to empty out our lookup table, and
        # also preserve them when allocating our array later.
        items, = args if args else ([],)
        for fld in items:
            klasstag = getattr(fld, 'type', (fld.Class(), fld.Tag()))
            table.pop(klasstag, None)
            res.append(fld)

        # Now that we've used up some of the names for the positional
        # fields we were given, if we have some explicit fields that
        # were specified then we need to reshape our lookup table so
        # that we can preserve the order of the fields to append.
        if hasattr(self, '_fields_') and fields:
            nametable = [(name, (klasstag, t)) for klasstag, (name, t) in table.items()]
            #print('fields left', [item for item, _ in nametable])

            # Iterate through all of the names in the nametable looking
            # for fields that the caller has given us.
            for name, (klasstag, type) in nametable:
                if name not in fields:
                    continue
                item = fields.pop(name)

                # If an explicit Element instance was given to us, then
                # use it whilst updating the type.
                if isinstance(item, Element):
                    E = item.copy()
                    E['Value'].type = klasstag

                # If a ptype instance was provided, then use it as the
                # value for an Element instance.
                elif ptype.isinstance(item):
                    value = item.copy(type=klasstag)
                    E = protocol.default().alloc(Value=value)

                # If just the type was given to us, then we need to
                # instantiate it prior to assigning it as the value.
                elif ptype.istype(item):
                    value = dyn.clone(item, type=klasstag)
                    E = protocol.default().alloc(Value=value.a)

                # Otherwise, we have no idea what we're doing.
                else:
                    raise NotImplementedError

                # Append the item to our current list of elements
                res.append(E)

            # Now we need to figure out what fields this array will be
            # composed of. Before doing this though, we need to iterate
            # through any explicit elements we were given and use them
            # to empty out our table.
            return super(Constructed, self).alloc(res, **fields)
        return super(Constructed, self).alloc(res, **fields)

class U8(pint.uint8_t):
    pass

class Block(parray.block):
    _object_ = U8
    def isTerminator(self, value):
        return False

class String(parray.block):
    _object_ = pstr.char_t
    def str(self):
        encoding = self._object_.encoding
        res, _ = encoding.decode(self.serialize())
        return res
    def isTerminator(self, value):
        return False

### Element structure
class Protocol(ptype.definition):
    attribute, cache = 'Class', {}

    # use the following packet type for this protocol (assigned later)
    default = None

    # any elements that are unknown (or undefined) will use one of the
    # following types depending on whether it's constructed or not.
    class UnknownConstruct(Constructed):
        pass
    class UnknownPrimitive(Block):
        @classmethod
        def typename(cls):
            klass, tag = cls.type
            return "{:s}<{:d},{:d}>".format(cls.__name__, klass, tag)

class Element(pstruct.type):
    def classname(self):
        res = self.typename()
        return "{:s}<{:s}>".format(res, self['Value'].typename()) if self.value and 2 < len(self.value) else super(Element, self).classname()
        #return "{:s}<{:s}>".format(res, self['Value'].typename()) if self.value and not(len(self.value) < 3) else super(Element, self).classname()
        #return super(Element, self).classname() if len(self.value) < 3 else "{:s}<{:s}>".format(res, self['Value'].typename())

    def __element__(self):
        '''Return the typename so that it's a lot easier to read.'''

        if self.initializedQ():
            res = self['Value']

        # XXX: This is tied into the Constructed mixin
        elif hasattr(self, '_object_'):
            res = ptype.force(self._object_, self)

        # Otherwise, just figure out the correct type
        else:
            res = self.__object__(self['Type'], self['Length'])
        return res.classname() if isinstance(res, ptype.base) else res.typename()

    def __object__(self, klasstag):
        protocol, (klass, tag) = self.Protocol, klasstag

        # First look up the type that we're going to need by grabbing the protocol,
        # then using it to determine the class, and then then by the actual tag.
        K = protocol.lookup(klass)
        try:
            result = K.lookup(tag)

        # If we couldn't find a type matching the right tag number, then just
        # return None to let the caller know they will just need to figure
        # things out themselves.
        except KeyError:
            return None
        return result

    def __Value(self):
        type, length = (self[fld].li for fld in ['Type', 'Length'])
        indefiniteQ, (klass, constructedQ, tag) = length.IndefiniteQ(), (type[fld] for fld in ['Class', 'Constructed', 'Tag'])

        # First grab the type that our Class and Tag should return.
        klasstag = klass, tag.int()
        result = self.__object__(klasstag)

        # If one wasn't found, then we need to figure out whether we're
        # returning an unknown constructed or an unknown primitive.
        if result is None:
            result = self.Protocol.UnknownConstruct if constructedQ else self.Protocol.UnknownPrimitive

        # If this is not a constructed type and not of an indefinite length,
        # then that was all we really needed to do. So prior to returning it,
        # set its blocksize and then let it go.
        if not constructedQ and not indefiniteQ:
            F = lambda _, size=length.int(): size
            return dyn.clone(result, type=klasstag, blocksize=F)

        # Next we'll need to figure out how the value's size is to be
        # determined. If it's an indefinite length, then it'll be looking
        # for the EOC terminator.
        attributes = {'type': klasstag}
        if indefiniteQ:
            F = lambda _, value, sentinel=EOC: isinstance(value['Value'], sentinel)
            attributes.setdefault('isTerminator', F)

        # Otherwise the length is defined, so we use it as the blocksize
        # and thus the actual terminator for the array type.
        else:
            F = lambda _, size=length.int(): size
            attributes.setdefault('blocksize', F)

        # If our result type is already a member of the Constructed type,
        # then we can just use it as the array to return.
        if issubclass(result, Constructed):
            return dyn.clone(result, **attributes)

        # If our result type isn't actually constructed, then this element
        # is a wrapper and we'll need to return a constructed value using
        # a copy of our element type as the object.
        attributes.setdefault('_object_', self.__class__)
        return dyn.clone(Constructed, **attributes)

    def __Padding(self):
        length, value = (self[fld].li for fld in ['Length', 'Value'])
        return dyn.block(max(0, length.int() - value.size()))

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'),
        (__Value, 'Value'),
        (__Padding, 'Padding'),
    ]

    def __alloc_value_primitive(self, result, size):
        if isinstance(result, parray.block):
            method_t = type(result.isTerminator)
            F = lambda _, cb=size: cb
            if ptypes.utils.callable_eq(result.isTerminator, parray.block.isTerminator):
                result.blocksize = method_t(F, result)
        elif hasattr(result, 'length'):
            result.length = size
        return result

    def __alloc_value_indefinite(self, result):
        method_t, items = type(result.isTerminator), [String, Block]

        # If the array type is composed of integers, then we just
        # check to see if it's last element is the EOC byte.
        if isinstance(result, items):
            F = lambda _, value, sentinel=EOC.tag: value.int() == sentinel
            if any(ptypes.utils.callable_eq(result.isTerminator, item.isTerminator) for item in items):
                result.isTerminator = method_t(F, result)
            Fsentinel = result.isTerminator

        # Verify that the array is a terminated array. If it is,
        # then this might be a Constructed instance and so one of
        # its elements could be an EOC instance.
        elif isinstance(result, parray.terminated):
            F = lambda _, value, sentinel=EOC: isinstance(value['value'], sentinel)
            if ptypes.utils.callable_eq(result.isTerminator, parray.terminated.isTerminator):
                result.isTerminator = method_t(F, result)
            Fsentinel = result.isTerminator

        # Otherwise if we're not even an array, then we need to warn
        # the user that we have no clue what to do.
        elif not isinstance(result, parray.type):
            logging.warning("{:s}.alloc : Skipping verification of terminator in {:s} with an indefinite length due to usage of a non-array type ({:s})".format('.'.join([cls.__module__, cls.__name__]), self.instance(), result.classname()))
            return result

        # This is a constant-length array type, so we need to explicitly
        # check it in order to warn the user.
        else:
            isterminator_int = lambda value, sentinel=EOC.tag: value.int() == sentinel
            isterminator_object = lambda value, sentinel=EOC: isinstance(value['value'], sentinel)
            isterminator_empty = lambda value: False
            Fsentinel = is_teminator_empty if not len(result.value) else isterminator_object if isinstance(result.value[-1], Element) else isterminator_int

        # Warn the user if the terminator does not check out.
        item = result.value[-1] if len(result.value) else None
        if not Fsentinel(item):
            logging.warning("{:s}.alloc : Element {:s} with an indefinite length does not have an array instance that ends with an EOC element ({!s})".format('.'.join([cls.__module__, cls.__name__]), self.instance(), item if isinstance(item, six.integer_types) else item.summary()))
        return result

    def __alloc_value_construct(self, result, size):
        method_t = type(result.isTerminator)
        F = lambda _, cb=size: cb
        if ptypes.utils.callable_eq(result.isTerminator, parray.block.isTerminator):
            result.blocksize = method_t(F, result)
        return result

    def __alloc_value(self, value, size, constructedQ, indefiniteQ):
        cls = self.__class__
        if not constructedQ and not indefiniteQ:
            result = self.__alloc_value_primitive(value, size)

        elif indefiniteQ:
            result = self.__alloc_value_indefinite(value)

        elif isinstance(value, Constructed):
            result = self.__alloc_value_construct(value, size)

        else:
            result.length = size
        return result

    def alloc(self, **fields):

        # If a Value was provided during allocation without the Type, then assign
        # one from the Universal/Primitive class using whatever its Tag is in .type
        value = fields.get('Value', None)
        if hasattr(value, 'type'):
            klass, tag = (Context.Class, value.type) if isinstance(value.type, six.integer_types) else value.type
            constructedQ = 1 if (ptypes.istype(value) and issubclass(value, Constructed)) or isinstance(value, Constructed) else 0
            fields.setdefault('Type', Type().alloc(Class=klass, Constructed=constructedQ).set(Tag=tag))

        if 'Length' in fields:
            return super(Element, self).alloc(**fields)

        res = super(Element, self).alloc(**fields)
        res['Length'].set(res['Value'].size())
        self.__alloc_value(res['Value'], res['Value'].size(), res['Type']['Constructed'], res['Length'].IndefiniteQ())
        return res

    def Tag(self):
        t = self['Type']
        return t['Tag'].int()

    def ConstructedQ(self):
        t = self['Type']
        return t['Constructed'] == 1

    def Class(self):
        t = self['Type']
        return t['Class']

# set the defaults by connecting the Element type to the Protocol we defined.
Protocol.default, Element.Protocol = Element, Protocol

### Element classes
class ProtocolClass(ptype.definition):
    attribute = 'tag'

    @classmethod
    def __set__(cls, type, object, **kwargs):
        if isinstance(type, six.integer_types):
            object.type = cls.Class, type
            return super(ProtocolClass, cls).__set__(type, object)
        return super(ProtocolClass, cls).__set__(type, object)

@Protocol.define
class Universal(ProtocolClass):
    Class, cache = 0x00, {}
    # FIXME: These types need to distinguish between constructed and non-constructed
    #        types instead of just generalizing them.
    class UniversalUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = UniversalUnknown
Protocol.Universal = Universal

@Protocol.define
class Application(ProtocolClass):
    Class, cache = 0x01, {}
    # FIXME: This needs to be unique to the instance of all ber.Element types
    #        used by the application.
    class ApplicationUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = ApplicationUnknown
Protocol.Application = Application

@Protocol.define
class Context(ProtocolClass):
    Class, cache = 0x02, {}
    # FIXME: This needs to be unique to a specific ber.Element type
    class ContextUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = ContextUnknown
Protocol.Context = Context

@Protocol.define
class Private(ProtocolClass):
    Class, cache = 0x03, {}
    class PrivateUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = PrivateUnknown
Protocol.Private = Private

### Tag definitions (X.208)
@Universal.define
class EOC(ptype.type):
    tag = 0x00
    # Required only if the length field specifies it

@Universal.define
class BOOLEAN(pint.uint_t):
    tag = 0x01

    def bool(self):
        res = self.int()
        return not(res == 0)

    def summary(self):
        res = "{!s}".format(self.bool())
        return ' : '.join([super(BOOLEAN, self).summary(), res.upper()])

@Universal.define
class INTEGER(pint.sint_t):
    tag = 0x02

@Universal.define
class BITSTRING(Block):
    tag = 0x03
    def summary(self):
        res = str().join(map('{:02X}'.format, bytearray(self.serialize())))
        return "({:d}) {:s}".format(self.size(), res)

@Universal.define
class OCTETSTRING(Block):
    tag = 0x04
    def summary(self):
        res = str().join(map('{:02X}'.format, bytearray(self.serialize())))
        return "({:d}) {:s}".format(self.size(), res)

@Universal.define
class NULL(ptype.block):
    tag = 0x05

@Universal.define
class OBJECT_IDENTIFIER(ptype.type):
    tag = 0x06

    def set(self, string):
        if string in self._values_.values():
            res = {v : k for k, v in self._values_.items()}
            return self.set(res[string])

        res = map(int, string.split('.'))
        val = [res.pop(0)*40 + res.pop(0)]
        for n in res:
            if n <= 127:
                val.append(n)
                continue

            # convert integer to a bitmap
            x = bitmap.new(0,0)
            while n > 0:
                x = bitmap.insert(x, (n&0xf,4))
                n //= 0x10

            # shuffle bitmap into oid components
            y = []
            while bitmap.size(x) > 0:
                x,v = bitmap.consume(x, 7)
                y.insert(0, v)

            val.extend([x|0x80 for x in y[:-1]] + [y[-1]])
        return super(OBJECT_IDENTIFIER, self).set(str().join(map(six.int2byte, val)))

    def str(self):
        data = bytearray(self.serialize())
        if len(data) > 0:
            res = [data[0] // 40, data.pop(0) % 40]
            data = iter(data)
            for n in data:
                val = bitmap.new(0,0)
                while n & 0x80:
                    val = bitmap.push(val, (n & 0x7f, 7))
                    n = next(data)
                val = bitmap.push(val, (n, 7))
                res.append(bitmap.int(val))
            return '.'.join(map("{:d}".format, res))
        return '0'

    def summary(self):
        oid, data = self.str(), self.serialize()
        hexed = str().join(map("\\x{:02x}".format, bytearray(data)))
        if oid in self._values_:
            return '{:s} ({:s}) ({:s})'.format(self._values_[oid], oid, hexed)
        return '{:s} ({:s})'.format(oid, hexed)

    # https://support.microsoft.com/en-us/help/287547/object-ids-associated-with-microsoft-cryptography
    _values_ = [
        ('spcIndirectDataContext', '1.3.6.1.4.1.311.2.1.4'),
        ('spcStatementType', '1.3.6.1.4.1.311.2.1.11'),
        ('spcSpOpusInfo', '1.3.6.1.4.1.311.2.1.12'),
        ('individualCodeSigning', '1.3.6.1.4.1.311.2.1.21'),
        ('commercialCodeSigning', '1.3.6.1.4.1.311.2.1.22'),
        ('SPC_MS_JAVA_SOMETHING', '1.3.6.1.4.1.311.15.1'),
        ('spcPelmageData', '1.3.6.1.4.1.311.2.1.15'),
        ('spcLink', '1.3.6.1.4.1.311.2.1.25'),
        ('SPC_TIME_STAMP_REQUEST_OBJID', '1.3.6.1.4.1.311.3.2.1'),
        ('SPC_SIPINFO_OBJID', '1.3.6.1.4.1.311.2.1.30'),
        ('SPC_PE_IMAGE_PAGE_HASHES_V1', '1.3.6.1.4.1.311.2.3.1'), # Page hash using SHA1
        ('SPC_PE_IMAGE_PAGE_HASHES_V2', '1.3.6.1.4.1.311.2.3.2'), # Page hash using SHA256
        ('SPC_NESTED_SIGNATURE_OBJID', '1.3.6.1.4.1.311.2.4.1'),
        ('SPC_RFC3161_OBJID', '1.3.6.1.4.1.311.3.3.1'),

        ('iso.org.dod.internet.security.mechanism.snego', '1.3.6.1.5.5.2'), # FIXME

        # Authenticode PE
        ('codeSigning', '1.3.6.1.5.5.7.3.3'),
        ('timeStamping', '1.3.6.1.5.5.7.3.8'),
        ('SPC_KP_LIFETIME_SIGNING_OBJID',  '1.3.6.1.4.1.311.10.3.13'),

        # PKCS #7 & #9
        ('md5', '1.2.840.113549.2.5'),
        ('rsa', '1.3.14.3.2.1.1'),
        ('desMAC', '1.3.14.3.2.10'),
        ('rsaSignature', '1.3.14.3.2.11'),
        ('dsa', '1.3.14.3.2.12'),
        ('dsaWithSHA', '1.3.14.3.2.13'),
        ('mdc2WithRSASignature', '1.3.14.3.2.14'),
        ('shaWithRSASignature', '1.3.14.3.2.15'),
        ('dhWithCommonModulus', '1.3.14.3.2.16'),
        ('desEDE', '1.3.14.3.2.17'),
        ('sha', '1.3.14.3.2.18'),
        ('mdc-2', '1.3.14.3.2.19'),
        ('dsaCommon', '1.3.14.3.2.20'),
        ('dsaCommonWithSHA', '1.3.14.3.2.21'),
        ('rsaKeyTransport', '1.3.14.3.2.22'),
        ('keyed-hash-seal', '1.3.14.3.2.23'),
        ('md2WithRSASignature', '1.3.14.3.2.24'),
        ('md5WithRSASignature', '1.3.14.3.2.25'),
        ('sha1', '1.3.14.3.2.26'),
        ('dsaWithSHA1', '1.3.14.3.2.27'),
        ('dsaWithCommandSHA1', '1.3.14.3.2.28'),
        ('sha-1WithRSAEncryption', '1.3.14.3.2.29'),
        ('contentType', '1.2.840.113549.1.9.3'),
        ('messageDigest', '1.2.840.113549.1.9.4'),
        ('signingTime', '1.2.840.113549.1.9.5'),
        ('counterSignature', '1.2.840.113549.1.9.6'),
        ('challengePassword', '1.2.840.113549.1.9.7'),
        ('unstructuredAddress', '1.2.840.113549.1.9.8'),
        ('extendedCertificateAttributes', '1.2.840.113549.1.9.9'),
        ('rsaEncryption', '1.2.840.113549.1.1.1'),
        ('md2withRSAEncryption', '1.2.840.113549.1.1.2'),
        ('md4withRSAEncryption', '1.2.840.113549.1.1.3'),
        ('md5withRSAEncryption', '1.2.840.113549.1.1.4'),
        ('sha1withRSAEncryption', '1.2.840.113549.1.1.5'),
        ('rsaOAEPEncryptionSET', '1.2.840.113549.1.1.6'),
        ('dsa', '1.2.840.10040.4.1'),
        ('dsaWithSha1', '1.2.840.10040.4.3'),

        ('itu-t recommendation t 124 version(0) 1', '0.0.20.124.0.1'),
    ]
    _values_ = {__oid : __name for __name, __oid in _values_}

@Universal.define
class EXTERNAL(ptype.block):
    tag = 0x08

@Universal.define
class REAL(ptype.block):
    tag = 0x09

@Universal.define
class ENUMERATED(pint.enum):
    tag = 0x0a

@Universal.define
class UTF8String(String):
    tag = 0x0c
    class _object_(pstr.char_t):
        encoding = codecs.lookup('utf-8')

@Universal.define
class SEQUENCE(Constructed):
    tag = 0x10

@Universal.define
class SET(Constructed):
    tag = 0x11

@Universal.define
class NumericString(ptype.block):
    tag = 0x12

@Universal.define
class PrintableString(String):
    tag = 0x13

@Universal.define
class T61String(String):
    tag = 0x14

@Universal.define
class IA5String(String):
    tag = 0x16

@Universal.define
class UTCTime(String):
    tag = 0x17

@Universal.define
class VisibleString(ptype.block):
    tag = 0x1a

@Universal.define
class GeneralString(String):
    tag = 0x1b

@Universal.define
class UniversalString(String):
    tag = 0x1c

@Universal.define
class CHARACTER_STRING(String):
    tag = 0x1d

@Universal.define
class BMPString(String):
    tag = 0x1e

### End of Universal definitions

### Base structures
class Packet(Element):
    byteorder = ptypes.config.byteorder.bigendian

class File(Element):
    byteorder = ptypes.config.byteorder.bigendian

if __name__ == '__main__':
    import sys, operator
    import ptypes, protocol.ber as ber
    from ptypes import bitmap
    from ptypes import *

    #import importlib
    #importlib.reload(ber)
    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    def test_length():
        data = b'\x38'
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(data)).l
        assert(res.int() == 0x38)

        data = b'\x81\xc9'
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(data)).l
        assert(res.int() == 201)

        data = bitmap.zero
        data = bitmap.push(data, (0, 1))
        data = bitmap.push(data, (38, 7))
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(bitmap.data(data))).l
        assert(res.int() == 38)

        data = bitmap.zero
        data = bitmap.push(data, (0x81,8))
        data = bitmap.push(data, (0xc9,8))
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(bitmap.data(data))).l
        assert(res.int() == 201)
    test_length()

    def test_tag():
        data = bitmap.new(0x1e, 5)
        res = pbinary.new(ber.Tag, source=ptypes.prov.string(bitmap.data(data))).l
        assert(res.int() == 0x1e)

        data = bitmap.zero
        data = bitmap.push(data, (0x1f, 5))
        data = bitmap.push(data, (0x1, 1))
        data = bitmap.push(data, (0x10, 7))
        data = bitmap.push(data, (0x1, 0))
        data = bitmap.push(data, (0x0, 7))
        res = pbinary.new(ber.Tag, source=ptypes.prov.string(bitmap.data(data))).l
        assert(res['TagLong'][0].int() == 0x90)
        assert(res.int() == 0x800)
    test_tag()

    def t_dsa_sig():
        data = bytearray([ 0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 1)
        assert(z['value'][0]['value'].int() == 0x1)
        assert(z['value'][1]['value'].size() == 1)
        assert(z['value'][1]['value'].int() == 0x2)
    t_dsa_sig()

    def t_dsa_sig_extra():
        data = bytearray([0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02, 0x05, 0x00])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() + 2 == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 1)
        assert(z['value'][0]['value'].int() == 0x1)
        assert(z['value'][1]['value'].size() == 1)
        assert(z['value'][1]['value'].int() == 0x2)
    t_dsa_sig_extra()

    def t_dsa_sig_msb():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00, 0x82 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x81)
        assert(z['value'][1]['value'].size() == 2)
        assert(z['value'][1]['value'].int() == 0x82)
    t_dsa_sig_msb()

    def t_dsa_sig_two():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x01, 0x00, 0x02, 0x02, 0x02, 0x00 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x100)
        assert(z['value'][1]['value'].size() == 2)
        assert(z['value'][1]['value'].int() == 0x200)
    t_dsa_sig_two()

    def t_invalid_int_zero():
        data = bytearray([ 0x30, 0x05, 0x02, 0x00, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0x0)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_invalid_int_zero()

    def t_invalid_int():
        data = bytearray([ 0x30, 0x07, 0x02, 0x02, 0x00, 0x7f, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0x7f)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_invalid_int()

    def t_neg_int():
        data = bytearray([ 0x30, 0x06, 0x02, 0x01, 0xaa, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0xaa - 0x100)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_neg_int()

    def t_trunc_der():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        try: z=z.l
        except: pass
        assert(z.size() < z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 1)
        assert(z['value'][0].size() == 4)
        assert(isinstance(z['value'][0]['value'], ber.INTEGER))
    t_trunc_der()

    def t_trunc_seq():
        data = bytearray([ 0x30, 0x07, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00, 0x82 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        try: z=z.l
        except: pass
        assert(z.size() < z.source.size())
        assert(z['length'].int() == z['value'].size())
        assert(len(z['value']) == 2)
        assert(z['value'][0].initializedQ())
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x81)
        assert(not z['value'][1].initializedQ())
        assert(z['value'][1]['value'].size() == 1)
        assert(isinstance(z['value'][1]['value'], ber.INTEGER))
    t_trunc_seq()

    def t_invalid_zero():
        data = bytearray([0x30, 0x02, 0x02, 0x00])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 2)
        assert(len(z['value']) == 1)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0)
    t_invalid_zero()

    def t_invalid_template():
        data = bytearray([0x30, 0x03, 0x0c, 0x01, 0x41])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 3)
        assert(len(z['value']) == 1)
        assert(all(isinstance(item['value'], ber.UTF8String) for item in z['value']))
        assert(z['value'][0]['value'].str() == u'A')
    t_invalid_template()

    def test_x690_spec_0():
        data = '0307040A3B5F291CD0'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 7)
        assert(isinstance(z['value'], ber.BITSTRING))
        assert(z['value'].serialize() == fromhex('040a3b5f291cd0'))
    test_x690_spec_0()

    def test_x690_spec_1():
        data = '23800305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 2)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(isinstance(z['value'][0]['value'], ber.BITSTRING))
        assert(z['value'][0]['value'].serialize() == b'\x04\x5f\x29\x1c\xd0')
    test_x690_spec_1()

    def test_indef_cons():
        data = '23800403000a3b0405045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
    test_indef_cons()

    def test_indef_cons_cons():
        data = '23802380030200010302010200000302040f0000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        z = z['value'][0]
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
    test_indef_cons_cons()

    def test_cons():
        data = '230c03020001030200010302040f'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 12)
        assert(len(z['value']) == 3)
        assert(all(isinstance(item, ber.Element) for item in z['value']))
        assert([item['value'].serialize() for item in z['value']] == [b'\0\1', b'\0\1', b'\4\x0f'])
    test_cons()

    def test_indef_bit_bit():
        data = '23800303000a3b0305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(all(isinstance(item, ber.Element) for item in z['value']))
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert([item['value'].serialize() for item in z['value'][:-1]] == [fromhex('000a3b'), fromhex('045f291cd0')])
    test_indef_bit_bit()

    def test_empty_bit_cons():
        data = '2300'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.Element))
    test_empty_bit_cons()

    def test_empty_bit_prim():
        data = '0300'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.U8))
    test_empty_bit_prim()

    def test_cons_octetbit():
        data = '24800303000a3b0305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(z['value'].type == (0, 4))
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BITSTRING) for item in z['value'][:-1]))
        assert([item['value'].serialize() for item in z['value'][:-1]] == [fromhex('000a3b'), fromhex('045f291cd0')])
    test_cons_octetbit()

    def test_indef_incomplete():
        data = '24800403000405045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data)))
        try: z.l
        except: pass
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.OCTETSTRING) for item in z['value']))
    test_indef_incomplete()

    def test_empty_prim_oct():
        data = '0400'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.U8))
    test_empty_prim_oct()

    def test_empty_cons_oct():
        data = '2400'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.Element))
    test_empty_cons_oct()

    def test_consdef_bit():
        data = '230e030200010000030200010302040f'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == z['value'].size())
        assert(len(z['value']) == 4)
        assert(all(isinstance(item['value'], t) for item, t in zip(z['value'], [ber.BITSTRING, ber.EOC, ber.BITSTRING, ber.BITSTRING])))
        assert([item['value'].serialize() for item in z['value']] == [b'\0\1', b'', b'\0\1', b'\4\x0F'])
    test_consdef_bit()

    def test_consindef_bit():
        data = '2380030200010302000103020f0f0000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BITSTRING) for item in z['value'][:-1]))
        assert(z['value'][-1]['value'].size() == 0)
    test_consindef_bit()

    def test_consindef_bit_nonzeroeoc():
        data = '2380030200010302000103020f0f000120'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BITSTRING) for item in z['value'][:-1]))
        assert(z['value'][-1]['value'].size() == 1)
    test_consindef_bit_nonzeroeoc()
