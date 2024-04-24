import builtins, operator, os, math, functools, itertools, sys, types
import ptypes, logging
from ptypes import *
ptypes.setbyteorder('little')
from ptypes.pint import uint8_t, uint16_t, uint32_t, uint64_t, sint8_t, sint16_t, sint32_t, sint64_t
from ptypes.pfloat import single, double

from .alljoyn_ajn import org

### Constants
ALLJOYN_MAJOR_PROTOCOL_VERSION = 1
ALLJOYN_PROTOCOL_VERSION = 12

### Primitives
class char(pstr.char_t):
    pass

class UNIX_FD(pint.uint32_t):
    pass

class ALLJOYN_ENDIAN_(pint.enum, pstr.char_t):
    _values_ = [
        ('LITTLE', 'l'),
        ('BIG', 'B'),
    ]

class MESSAGE_TYPE_(pint.enum):
    _values_ = [
        ('INVALID', 0),         # an invalid message type
        ('METHOD_CALL', 1),     # a method call message type
        ('METHOD_RET', 2),      # a method return message type
        ('ERROR', 3),           # an error message type
        ('SIGNAL', 4),          # a signal message type
    ]

class ALLJOYN_FLAG_(pbinary.flags):
    _fields_ = [
        (1, 'ENCRYPTED'),           # Body is encrypted
        (1, 'COMPRESSED'),
        (1, 'GLOBAL_BROADCAST'),    # Global (bus-to-bus) broadcast
        (1, 'SESSIONLESS'),         # Sessionless message
        (1, 'UNUSED'),
        (1, 'ALLOW_REMOTE_MSG'),    # Allow messages from remote hosts (valid only in Hello message)
        (1, 'AUTO_START'),          # Auto start the service
        (1, 'NO_REPLY_EXPECTED'),   # No reply is expected
    ]

class ALLJOYN_TYPE_(pint.enum):
    _values_ = [(name, functools.reduce(lambda agg, item: item + agg * 0x100, bytearray(value))) for name, value in [
        ('INVALID',             b'\0'),     # AllJoyn INVALID typeId
        ('ARRAY',               b'a'),      # AllJoyn array container type
        ('BOOLEAN',             b'b'),      # AllJoyn boolean basic type, @c 0 is @c FALSE and @c 1 is @c TRUE - Everything else is invalid
        ('DOUBLE',              b'd'),      # AllJoyn IEEE 754 double basic type
        ('DICT_ENTRY',          b'e'),      # AllJoyn dictionary or map container type - an array of key-value pairs
        ('SIGNATURE',           b'g'),      # AllJoyn signature basic type
        ('HANDLE',              b'h'),      # AllJoyn socket handle basic type
        ('INT32',               b'i'),      # AllJoyn 32-bit signed integer basic type
        ('INT16',               b'n'),      # AllJoyn 16-bit signed integer basic type
        ('OBJECT_PATH',         b'o'),      # AllJoyn Name of an AllJoyn object instance basic type
        ('UINT16',              b'q'),      # AllJoyn 16-bit unsigned integer basic type
        ('STRUCT',              b'r'),      # AllJoyn struct container type
        ('STRING',              b's'),      # AllJoyn UTF-8 NULL terminated string basic type
        ('UINT64',              b't'),      # AllJoyn 64-bit unsigned integer basic type
        ('UINT32',              b'u'),      # AllJoyn 32-bit unsigned integer basic type
        ('VARIANT',             b'v'),      # AllJoyn variant container type
        ('INT64',               b'x'),      # AllJoyn 64-bit signed integer basic type
        ('BYTE',                b'y'),      # AllJoyn 8-bit unsigned integer basic type
        ('STRUCT_OPEN',         b'('),      # Never actually used as a typeId: specified as ALLJOYN_STRUCT
        ('STRUCT_CLOSE',        b')'),      # Never actually used as a typeId: specified as ALLJOYN_STRUCT
        ('DICT_ENTRY_OPEN',     b'{'),      # Never actually used as a typeId: specified as ALLJOYN_DICT_ENTRY
        ('DICT_ENTRY_CLOSE',    b'}'),      # Never actually used as a typeId: specified as ALLJOYN_DICT_ENTRY
        ('BOOLEAN_ARRAY',       b'ba'),     # AllJoyn array of booleans
        ('DOUBLE_ARRAY',        b'da'),     # AllJoyn array of IEEE 754 doubles
        ('INT32_ARRAY',         b'ia'),     # AllJoyn array of 32-bit signed integers
        ('INT16_ARRAY',         b'na'),     # AllJoyn array of 16-bit signed integers
        ('UINT16_ARRAY',        b'qa'),     # AllJoyn array of 16-bit unsigned integers
        ('UINT64_ARRAY',        b'ta'),     # AllJoyn array of 64-bit unsigned integers
        ('UINT32_ARRAY',        b'ua'),     # AllJoyn array of 32-bit unsigned integers
        ('INT64_ARRAY',         b'xa'),     # AllJoyn array of 64-bit signed integers
        ('BYTE_ARRAY',          b'ya'),     # AllJoyn array of 8-bit unsigned integers
        ('WILDCARD',            b'*'),      # This never appears in a signature but is used for matching arbitrary message args
    ]]

class AllJoynTypeId(ALLJOYN_TYPE_, uint16_t):
    pass

class ALLJOYN_HDR_FIELD_(pint.enum):
    ''' Wire-protocol defined header field types '''
    _values_ = [
        ('INVALID', 0),                 # an invalid header field type
        ('PATH', 1),                    # an object path header field type
        ('INTERFACE', 2),               # a message interface header field type
        ('MEMBER', 3),                  # a member (message/signal) name header field type
        ('ERROR_NAME', 4),              # an error name header field type
        ('REPLY_SERIAL', 5),            # a reply serial number header field type
        ('DESTINATION', 6),             # message destination header field type
        ('SENDER', 7),                  # senders well-known name header field type
        ('SIGNATURE', 8),               # message signature header field type
        ('HANDLES', 9),                 # number of file/socket handles that accompany the message
        ('TIMESTAMP', 10),              # time stamp header field type
        ('TIME_TO_LIVE', 11),           # messages time-to-live header field type
        ('COMPRESSION_TOKEN', 12),      # message compression token header field type @deprecated
        ('SESSION_ID', 13),             # Session id field type
        ('UNKNOWN', 14),                # unknown header field type also used as maximum number of header field types.
    ]

class MessageHeader(pstruct.type):
    class _msgType(MESSAGE_TYPE_, uint8_t):
        pass

    #def __endianed(type):
    #    table = {'l': pint.littleendian, 'B': pint.bigendian}
    #    return lambda self: (lambda orderlookup: orderlookup(type))(table.get(self['endian'].li.get(), lambda type: type))

    def __endianed(type):
        table = {'l': 'little', 'B': 'big'}
        return lambda self: (lambda orderlookup: dyn.clone(type, byteorder=orderlookup))(table.get(self['endian'].li.get(), lambda type: type))

    _fields_ = [
        (ALLJOYN_ENDIAN_, 'endian'),            # The endianness of this message
        (_msgType, 'msgType'),                  # Indicates if the message is method call, signal, etc.
        (ALLJOYN_FLAG_, 'flags'),               # Flag bits
        (uint8_t, 'majorVersion'),              # Major version of this message
        (__endianed(uint32_t), 'bodyLen'),      # Length of the body data
        (__endianed(uint32_t), 'serialNum'),    # serial of this message
        (__endianed(uint32_t), 'headerLen'),    # Length of the header fields
    ]

    def alloc(self, **fields):
        fields.setdefault('endian', sys.byteorder.upper())
        res = super(MessageHeader, self).alloc(**fields)
        if 'majorVersion' not in fields:
            res['majorVersion'].set(ALLJOYN_MAJOR_PROTOCOL_VERSION)
        return res

class MsgArg(ptype.definition):
    cache, _enum_ = {}, AllJoynTypeId

class AllJoynHandle(UNIX_FD):
    pass
    #_fields_ = [
    #    (dyn.align(4), 'AlignPtr(index)'),
    #    (UNIX_FD, 'index'),
    #    # uint32_t num = (hdrFields.field[ALLJOYN_HDR_FIELD_HANDLES].typeId == ALLJOYN_INVALID) ? 0 : hdrFields.field[ALLJOYN_HDR_FIELD_HANDLES].v_uint32;
    #]

class AllJoynString(pstruct.type):
    def __str(self):
        res = self['len'].li
        return dyn.clone(pstr.string, length=res.int())

    _fields_ = [
        (uint32_t, 'len'),  # Length of AllJoynString
        (__str, 'str'),     # The actual string
    ]

    def summary(self):
        return "({:d}) {!r}".format(self['len'], self['str'].str())

    def alloc(self, *string, **fields):
        if string:
            [value] = string
            instance = pstr.string().set(value) if isinstance(value, str) else value
            fields.setdefault('str', instance)
        res = super(AllJoynString, self).alloc(**fields)
        if 'len' not in fields:
            res['len'].set(len(res['str']))
        return res

    def set(self, *string, **fields):
        fields.setdefault('str', *string) if string else fields
        return super(AllJoynString, self).set(**fields)

    def Get(self):
        return self['str'].get()

    @classmethod
    def New(cls, string, **fields):
        return cls().alloc(string, **fields)

class AllJoynSignature(pstruct.type):
    def __sig(self):
        res = self['len'].li
        return dyn.clone(pstr.string, length=res.int())
    _fields_ = [
        (uint8_t, 'len'),   # Length of AllJoyn signature
        (__sig, 'sig'),     # The  signature
        (char, 'nul'),
    ]
    def summary(self):
        res = super(AllJoynSignature, self).summary()
        return "{:s} : {:s}".format(res, self['sig'].summary())

    def alloc(self, *sig, **fields):
        if sig:
            [value] = sig
            instance = pstr.string().set(value) if isinstance(value, str) else value
            fields.setdefault('sig', instance)
        res = super(AllJoynSignature, self).alloc(**fields)
        if 'len' not in fields:
            res['len'].set(res['sig'].size())
        return res

    def unmarshal(self):
        string = self['sig'].str()
        unmarshalled = [item for item in SignatureUtils.Unmarshal(string)]
        return dyn.clone(AllJoynSignatureValue, _signature_=(string, unmarshalled))

    def str(self):
        return self['sig'].str()

    def set(self, *signature, **fields):
        fields.setdefault('sig', *signature) if signature else fields
        return super(AllJoynSignature, self).set(**fields)

    def Get(self):
        return self['sig'].str(), self.unmarshal()

    @classmethod
    def New(cls, signature, **fields):
        return cls().alloc(signature, **fields)

class SignatureValue(pstruct.type):
    _alignment_ = 0
    def __AlignPtr(self):
        res = 0
        if hasattr(self, '_object_'):
            res = self._alignment_
        return dyn.align(res)
    def __SignatureValue(self):
        if hasattr(self, '_object_'):
            return self._object_
        return ptype.undefined
    _fields_ = [
        (__AlignPtr, 'AlignPtr'),
        (__SignatureValue, 'Value'),
    ]
    def summary(self):
        return "{:s} : AlignPtr={:d} : Value -> {:s}".format(self['Value'].typename(), self['AlignPtr'].size(), self['Value'].summary())

    def set(self, *values, **fields):
        fields.setdefault('Value', *values) if values else fields
        return super(SignatureValue, self).set(**fields)

    def alloc(self, *args, **fields):
        result = super(SignatureValue, self).alloc(**fields)
        if args:
            sig, unmarshalled = self._object_._signature_ if hasattr(self._object_, '_signature_') else (chr(result['Value'].type), [])
            if sig[:1] in SignatureUtils.groups:
                result['Value'].set(args)
            elif sig in SignatureUtils.scalars:
                result['Value'].alloc(*args)
            else:
                result['Value'].alloc(*args)
            return result
        return result

    def Get(self):
        res = self['Value']
        return res.Get() if hasattr(res, 'Get') else res.get()

    # XXX: this might not be needed
    def Allocate(self, signature, **fields):
        unmarshalled = [item for item in SignatureUtils.Unmarshal(signature)]
        self._alignment_ = SignatureUtils.Alignment(signature)
        self._object_ = value = dyn.clone(AllJoynSignatureValue, _signature_=(signature, unmarshalled))
        return self.alloc(**fields)

    @classmethod
    def New(cls, signature, *value, **fields):
        unmarshalled = [item for item in SignatureUtils.Unmarshal(signature)]
        alignment = SignatureUtils.Alignment(signature)
        object = dyn.clone(AllJoynSignatureValue, _signature_=(signature, unmarshalled))

        # valid signatures (just allocating)
        if signature[:1] in SignatureUtils.groups and len(value) == 1:
            [container] = value
            fields['Value'] = container
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)
        elif signature[:1] in 'a' and len(value) == 1:
            [items] = value
            fields['Value'] = items
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)
        elif value and len(value) == 1:
            [scalar] = value
            fields['Value'] = scalar
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)

        # invalid signatures (ungrouped)
        elif signature[:1] in SignatureUtils.groups and len(value) > 1:
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)
            res['Value'].alloc(*value)
        elif signature[:1] in 'a' and len(value) > 1:
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)
            res['Value'].alloc(*value)
        elif value and len(value) == 1:
            res = cls(_object_=object, _alignment_=alignment).alloc(**fields)
            res['Value'].alloc(*value)
        else:
            return cls(_object_=object, _alignment_=alignment).alloc(*value, **fields)
        return res

class AllJoynSignatureValue(parray.type):
    def __init__(self, **attrs):
        super(AllJoynSignatureValue, self).__init__(**attrs)
        if hasattr(self, '_signature_'):
            signature, items = self._signature_
            iterable = self.__of_signature(items)
        else:
            _, iterable = self._signature_ = '', []
        real = self.__real_objects = [item for item in iterable]
        self.length = len(real)

    @classmethod
    def __of_signature(cls, signature):
        for type, align in signature:
            yield dyn.clone(SignatureValue, _object_=type, _alignment_=align)
        return

    def _object_(self):
        index = len(self.value)
        return self.__real_objects[index] if 0 <= index < len(self.__real_objects) else ptype.undefined

    def alloc(self, *args, **attrs):
        if not args:
            return super(AllJoynSignatureValue, self).alloc(**attrs)

        # use the signature to determine the formatting to use when initializing
        # this signature-value-array. essentially, this is responsible for mapping
        # the parameters so that an array will take a list, variants can be nested,
        # groups/ungroups are flattened, and scalars are just single values.
        sig, _ = self._signature_
        if sig[:1] in SignatureUtils.groups:
            return super(AllJoynSignatureValue, self).alloc(args, **attrs)
        elif sig[:1] in SignatureUtils.containers:
            return super(AllJoynSignatureValue, self).alloc(args, **attrs)
        elif sig in {'v', b'v'}:
            return super(AllJoynSignatureValue, self).alloc([args], **attrs)
        elif sig in SignatureUtils.scalars:
            return super(AllJoynSignatureValue, self).alloc(args, **attrs)
        return super(AllJoynSignatureValue, self).alloc(*args, **attrs)

    def set(self, *args, **attrs):
        return super(AllJoynSignatureValue, self).set(args, **attrs)

    def properties(self):
        res = super(AllJoynSignatureValue, self).properties()
        if hasattr(self, '_signature_'):
            res['sig'], _ = self._signature_
        return res

    def summary(self):
        if self.initializedQ():
            sig, _ = self._signature_ if hasattr(self, '_signature_') else ('', ())
            singles = ["{}".format(item['Value'].summary()) for item in self]
            count = "({:d}) ".format(len(singles)) if len(singles) > 1 else ''
            if sig in SignatureUtils.scalars and len(singles) == 1:
                return "{:s}".format(', '.join(singles))
            elif sig[:1] in SignatureUtils.groups and len(singles) == 1:
                return singles[0]
            return "{:s}[{:s}]".format(count, ', '.join(singles))
        return '???'

    def repr(self):
        if self.initializedQ():
            singles = ("{}\n".format(item) for item in self)
            return ''.join(singles)
        return '???'

    @classmethod
    def New(cls, sig, *args, **attrs):
        unmarshalled = [item for item in SignatureUtils.Unmarshal(sig)]
        res = cls(_signature_=(sig, unmarshalled))
        return res.alloc(*args, **attrs)

    # XXX: this might not be needed
    def Allocate(self, signature, **attrs):
        unmarshalled = [item for item in SignatureUtils.Unmarshal(signature)]
        self.length = len(unmarshalled)
        self._signature_ = signature, unmarshalled
        self.__real_objects = [item for item in self.__of_signature(unmarshalled)]
        return super(AllJoynSignatureValue, self).alloc(**attrs)

    def set(self, *elements, **fields):
        fields.setdefault('elements', *elements) if elements else fields
        return super(AllJoynSignatureValue, self).set(**fields)

    def Get(self):
        iterable = (item for item in self)
        getter = lambda item: item.Get() if hasattr(item, 'Get') else item.get()
        gotten = tuple(map(getter, iterable))
        [result] = [gotten] if len(gotten) > 1 else gotten or [()]
        return result

class AllJoynArray(pstruct.type):
    ''' alljoyn_core/src/Message_Parse.cc:79 '''
    def __elements(self):
        res = self['length'].li

        # if the array has a signature, then honor it for each element.
        if hasattr(self, '_signature_'):
            sig, unmarshalled = self._signature_
            assert(sig[:1] in {b'a', 'a'})
            element = dyn.clone(AllJoynSignatureValue, _signature_=(sig[1:], unmarshalled[:]))
            return dyn.blockarray(element, res.int())

        # if there is an _object_ property, then we can just use that too.
        elif hasattr(self, '_object_'):
            return dyn.blockarray(self._object_, res.int())
        return parray.type

    def __extra_elements(self):
        res, fields = self['length'].li, ['elements']
        size = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        return dyn.block(size)

    _fields_ = [
        (uint32_t, 'length'),
        (__elements, 'elements'),               # Pointer to array
        (__extra_elements, 'extra'),
    ]

    def alloc(self, *elements, **fields):
        fields.setdefault('elements', *elements) if elements else fields

        # first do an allocation with the specified elements and fields.
        # if one of the fields was the length, then we have our result.
        result = calculator = super(AllJoynArray, self).alloc(**fields)
        if 'length' in fields:
            return result

        # figure out the length that we got from the first allocation,
        # and use it to allocate the array that we're going to return.
        length = sum(calculator[fld].size() for fld in ['elements', 'extra'])

        # FIXME: this double-alloc is a hack and should be unnecessary.
        fields['length'] = uint32_t().a.set(length)
        return super(AllJoynArray, self).alloc(**fields)

    def set(self, *elements, **fields):
        fields.setdefault('elements', *elements) if elements else fields
        return super(AllJoynArray, self).set(**fields)

    def Get(self):
        iterable = (element for element in self['elements'])
        return [item.Get() for item in iterable]

    @classmethod
    def New(cls, *elements, **fields):
        res = parray.type(length=len(elements))
        res.alloc(*elements) if elements else res.alloc()
        fields.setdefault('elements', res)
        return cls().alloc(**fields)

class AllJoynVariant(pstruct.type):
    ''' alljoyn_core/src/Message_Parse.cc:365 '''
    def __marshalled(self):
        sig = self['sig'].li
        return sig.unmarshal()

    # XXX: check this
    _fields_ = [
        (AllJoynSignature, 'sig'),
        (__marshalled, 'marshalled?'),
    ]

    def alloc(self, *marshalled, **fields):
        if not marshalled:
            return super(AllJoynVariant, self).alloc(**fields)
        [signature], marshalled = marshalled[:1], marshalled[1:]

        # unpack the signature and any marshalled data ignoring whether it's
        # been packed into a list or a tuple. this way we can use the extra
        # parameters to initialize the marshalled data containing the variant.
        [fields['sig']], marshalled = (signature[:1], signature[1:] + marshalled) if isinstance(signature, (list, tuple)) else ([signature], marshalled)

        # now we can allocate the variant and return if there was no extra data.
        res = super(AllJoynVariant, self).alloc(**fields)
        sig = res['sig'].str()
        if not marshalled:
            return res

        # we need to handle any extra parameters depending on whatever the signature is
        # for the variant. we specially handle nested variants so that there is no limit
        # to their nesting. everything else should be pretty similar to "SignatureValue".
        # FIXME: not all of these conditionals are needed, and can be reduced...
        if sig[:1] in {b'v', 'v'}:
            res['marshalled?'].alloc(*marshalled)
        elif sig[:1] in {b'a', 'a'}:
            res['marshalled?'].alloc(*marshalled)
        elif sig[:1] in SignatureUtils.containers:
            res['marshalled?'].alloc(marshalled)
        elif sig in SignatureUtils.scalars:
            res['marshalled?'].alloc(*marshalled)
        else:
            res['marshalled?'].alloc(*marshalled)
        return res

    def set(self, *marshalled, **fields):
        fields.setdefault('marshalled?', *marshalled) if marshalled else fields
        return super(AllJoynVariant, self).set(**fields)

    def Get(self):
        res = self['marshalled?']
        return res.Get()

    @classmethod
    def New(cls, signature, *value, **fields):
        sig = fields.setdefault('sig', AllJoynSignature().New(signature))
        marshalled_t = sig.unmarshal()
        marshalled = fields.setdefault('marshalled?', marshalled_t().New(*value) )
        return cls().alloc(**fields)

class AllJoynStruct(AllJoynSignatureValue):
    ''' alljoyn_core/src/Message_Parse.cc:299 '''
    pass

class AllJoynDictEntry(AllJoynSignatureValue):
    ''' alljoyn_core/src/Message_Parse.cc:334 '''
    pass

class MessageField(pstruct.type):
    class AllJoynFieldType(ALLJOYN_HDR_FIELD_, pint.uint8_t):
        pass

    def __marshalled(self):
        sig = self['sig'].li
        return sig.unmarshal()

    _fields_ = [
        (dyn.align(8), 'AlignPtr'),
        (AllJoynFieldType, 'fieldId'),
        (AllJoynSignature, 'sig'),
        (__marshalled, 'marshalled'),
    ]

    def set(self, *marshalled, **fields):
        fields.setdefault('marshalled', *marshalled) if marshalled else fields
        return super(MessageField, self).set(**fields)

class MessageFields(parray.block):
    #_object_ = MessageField

    # the start of each "MessageField" needs to be aligned, according to the specification.
    # however, the MessageFields array can terminate _before_ an element being aligned or
    # _after_ it has been aligned. to deal with this, we perform the alignment inside this
    # array so that the blocksize (headerLen) is always honored when loading this array.
    def _object_(self):
        numerator = len(self.value) - 1
        res = numerator % 3
        return dyn.align(8) if res else MessageField

    # since this array is inconsistent and contains both a "MessageField"
    # object and an alignment block, we need some methods to skip over the
    # elements containing alignments that we don't need to care about.
    def enumerate(self):
        for index, item in enumerate(self):
            if isinstance(item, MessageField):
                yield index, item
            continue
        return

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

    # Some methods that can be used to query the fields in this array.
    def Has(self, field):
        Fpredicate = field if callable(field) else operator.itemgetter(field)
        iterable = (index for index, item in self.enumerate() if Fpredicate(item['fieldId']))
        return next(iterable, -1) >= 0

    def By(self, field, *default):
        Fpredicate = field if callable(field) else operator.itemgetter(field)
        iterable = (index for index, item in self.enumerate() if Fpredicate(item['fieldId']))
        index = next(iterable, -1)
        if 0 <= index < len(self):
            return self[index]
        elif not default:
            raise KeyError(field)
        [result] = default
        return result

    def Signature(self, field, *default):
        res = self.By(field, *default)
        return res['sig'].str() if isinstance(res, MessageField) else res

    def SignatureValue(self, field, *default):
        res = self.By(field, *default)
        return res['marshalled'] if isinstance(res, MessageField) else res

class MessageBodyBase(ptype.generic): pass
class MessageBodyUnknown(ptype.block, MessageBodyBase): pass
class MessageBodySignatured(AllJoynSignatureValue, MessageBodyBase): pass

class Message(pstruct.type):
    def __MessageFields(self):
        hdr = self['Header'].li
        res = hdr['headerLen'].li
        return dyn.clone(MessageFields, blocksize=lambda self, sz=res.int(): sz)

    def __AssignByteOrder(self):
        res = self['Header'].li
        endian = res['endian']
        order = 'big' if endian['BIG'] else 'little' if endian['LITTLE'] else self.attributes.get('byteorder', sys.byteorder)
        self.attributes['byteorder'] = self.byteorder = order
        return ptype.undefined

    def __ExtraHeader(self):
        hdr, fields = self['Header'].li, ['Header', 'Fields']
        res, size = hdr['headerLen'].int(), sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, res - size))

    #def __Body(self):
    #    hdr = self['Header'].li
    #    res = hdr['bodyLen'].int()
    #    return dyn.clone(MessageBody, length=res)

    def __Body(self):
        hdr, fields = self['Header'].li, self['Fields'].li
        res = hdr['bodyLen'].int()
        if fields.Has('SIGNATURE'):
            sigfield = fields.SignatureValue('SIGNATURE')
            if len(sigfield) == 1:
                sigvalue = sigfield[0]
                sig = sigvalue['Value']
                return sig.unmarshal()
            return dyn.clone(MessageBodyUnknown, length=res)
        return dyn.clone(MessageBodyUnknown, length=res)

    def __ExtraBody(self):
        hdr, fields = self['Header'].li, ['Body']
        res = max(0, hdr['bodyLen'].int() - sum(self[fld].li.size() for fld in fields))
        return dyn.block(res)

    _fields_ = [
        (MessageHeader, 'Header'),
        (__AssignByteOrder, ''),
        (__MessageFields, 'Fields'),
        (__ExtraHeader, 'HeaderExtra'),
        (dyn.align(8), 'Align(Body)'),
        (__Body, 'Body'),
        (__ExtraBody, 'BodyExtra'),
    ]

    def properties(self):
        res = super(Message, self).properties()
        if hasattr(self, 'byteorder'):
            res['byteorder'] = self.byteorder
        return res

    def GetFlags(self):
        return self['Header']['flags']
    def GetHeaderFields(self):
        return self['Fields']
    def GetField(self, field, *default):
        fields = self['Fields']
        [res] = [fields.By(field)] if fields.Has(field) else (default or [None])
        return res['marshalled'].Get() if res else res

    def IsBroadcastSignal(self):
        hdr, fields = (self[fld] for fld in ['Header', 'Fields'])
        is_signal_from_destination = hdr['msgType']['SIGNAL'] and fields.Has('DESTINATION')
        return is_signal_from_destination and fields.By('DESTINATION')['fieldId']['INVALID']

    def isGlobalBroadcast(self):
        flags = self['Header']['flags']
        return self.IsBroadcastSignal() and flags['GLOBAL_BROADCAST']

    def isSessionless(self):
        return self['Header']['flags']['SESSIONLESS']

    def GetTTL(self):
        ''' milliseconds '''
        res = self.GetField('TIME_TO_LIVE', 0)
        return 1000 * res if self['Header']['flags']['SESSIONLESS'] else res

    def isExpired(self):
        if not self['Fields'].Has('TIME_TO_LIVE'):
            return False
        ms, start = self.GetTTL(), self.GetField('TIMESTAMP', now)
        return now - start > ms

    def isUnreliable(self):
        if self['Fields'].Has('TIME_TO_LIVE'):
            return self.GetField('TIME_TO_LIVE') != 0
        return False

    def isEncrypted(self):
        res = self['Header']['flags']['ENCRYPTED']
        return True if res else False

    def GetType(self):
        return self['Header']['msgType']
    def GetCallSerial(self):
        return self['Header']['serialNum'].int()

    def GetSignature(self):
        return self.GetField('SIGNATURE', '')
    def GetObjectPath(self):
        return self.GetField('OBJECT_PATH', '')
    def GetInterface(self):
        return self.GetField('INTERFACE', '')
    def GetMemberName(self):
        return self.Getfield('MEMBER', '')
    def GetReplySerial(self):
        return self.Getfield('REPLY_SERIAL', 0)
    def GetSender(self):
        return self.GetField('SENDER', '')
    def GetDestination(self):
        return self.GetField('DESTINATION', '')
    def HasDestination(self):
        res = self.GetField('DESTINATION', '')
        return True if res else False
    def GetSessionId(self):
        return self.GetField('SESSION_ID', 0)

    ### Message creation that is used by the protocol.
    @classmethod
    def MarshalMessage(cls, expectedSignature, msgType, flags, serialNum=0, sender=None, destination=None, sessionId=None, **fields):
        header = fields.pop('Header', MessageHeader().a)
        header = header.set(flags=flags, msgType=msgType, serialNum=serialNum)

        # FIXME: added support for encryption
        # encrypt = (flags & ALLJOYN_FLAG_ENCRYPTED) ? true : false;
        #msgHeader.endian = outEndian;
        #msgHeader.flags = flags;
        #msgHeader.msgType = (uint8_t)msgType;
        #msgHeader.majorVersion = ALLJOYN_MAJOR_PROTOCOL_VERSION;
        #msgHeader.serialNum = serialNumber;
        #msgHeader.bodyLen = static_cast<uint32_t>(argsLen);

        hdrFields = fields.pop('Fields', MessageFields().a)
        if destination is not None and not hdrFields.Has('DESTINATION'):
            field = hdrFields.append(MessageField).alloc(fieldId='DESTINATION', sig='s', marshalled=destination)
        if sender is not None and not hdrFields.Has('SENDER'):
            field = hdrFields.append(MessageField).alloc(fieldId='SENDER', sig='s', marshalled=sender)
        if not hdrFields.Has('SIGNATURE'):
            field = hdrFields.append(MessageField).alloc(fieldId='SIGNATURE', sig='g', marshalled=expectedSignature)
        if sessionId is not None and not hdrFields.Has('SESSION_ID'):
            field = hdrFields.append(MessageField).alloc(fieldId='SESSION_ID', sig='u', marshalled=sessionId)

        res = Message()
        return res.alloc(Header=header, Fields=hdrFields, **fields)

    @classmethod
    def HelloMessage(cls, isBusToBus, sender, destination, allowRemote, guid, nameType):
        ''' alljoyn_core/src/Message_Gen.cc:1093 '''
        fields = MessageFields().a

        field = fields.append(MessageField).alloc(fieldId='PATH', sig='o', marshalled=org.alljoyn.Bus.ObjectPath)
        field = fields.append(MessageField).alloc(fieldId='INTERFACE', sig='s', marshalled=org.alljoyn.Bus.InterfaceName)
        field = fields.append(MessageField).alloc(fieldId='MEMBER', sig='s', marshalled='BusHello' if isBusToBus else 'SimpleHello')

        nameTypeField = getattr(NameTransferType, nameType, nameType) if isinstance(nameType, str) else nameType
        return cls.MarshalMessage(
            'su',
            'METHOD_CALL', {'AUTO_START'}.union({'ALLOW_REMOTE_MSG'} if allowRemote else {}),
            sender=sender, destination=destination, sessionId=0,
            Fields=fields,
            Body=AllJoynSignatureValue.New('su', [guid, nameTypeField << 30 | ALLJOYN_PROTOCOL_VERSION])
        )

    @classmethod
    def HelloReply(cls, isBusToBus, sender, uniqueName, guid, nameType):
        ''' alljoyn_core/src/Message_Gen.cc:1146 '''
        fields = MessageFields().a

        field = fields.append(MessageField).alloc(fieldId='REPLY_SERIAL', sig='u')

        if isBusToBus:
            signature = 'ssu' if isBusToBus else 's'
            body = [uniqueName, guid, nameType << 30 | ALLJOYN_PROTOCOL_VERSION]
        else:
            signature = 's'
            body = uniqueName

        res = cls.MarshalMessage(
            signature, 'METHOD_RET', {}, sender=sender, destination=uniqueName,
            Fields=fields, Body=body
        )
        hdrSerial = res['Header']['serialNum']
        res['Fields'].By('REPLY_SERIAL').set(hdrSerial.int())
        return res

    @classmethod
    def CallMsg(cls, signature, sender, destination, sessionId, objPath, iface, methodName, flags, body=()):
        ''' alljoyn_core/src/Message_Gen.cc:1193 '''
        fields = MessageFields().a

        assert(objPath.startswith('/'))
        assert(not(objPath.endswith('/')))
        assert(all(objPath.split('/')[1:]))
        # (flags & ~(ALLJOYN_FLAG_NO_REPLY_EXPECTED | ALLJOYN_FLAG_AUTO_START | ALLJOYN_FLAG_ENCRYPTED | 0x40 /* ALLJOYN_FLAG_COMPRESSED */ | ALLJOYN_FLAG_SESSIONLESS))

        field = fields.append(MessageField).alloc(fieldId='PATH', sig='o', marshalled=objPath)
        field = fields.append(MessageField).alloc(fieldId='MEMBER', sig='s', marshalled=methodName)
        if iface is not None:
            field = fields.append(MessageField).alloc(fieldId='INTERFACE', sig='s', marshalled=iface)

        return cls.MarshalMessage(
            signature, 'METHOD_CALL', flags, sender=sender, destination=destination, sessionId=sessionId,
            Fields=fields, Body=body
        )

    @classmethod
    def SignalMsg(cls, signature, sender, destination, sessionId, objPath, iface, signalName, flags, timeToLive=None, body=()):
        ''' alljoyn_core/src/Message_Gen.cc:1284 '''
        fields = MessageFields().a

        assert(objPath.startswith('/'))
        assert(not(objPath.endswith('/')))
        assert(all(objPath.split('/')[1:]))
        # (flags & ~(ALLJOYN_FLAG_ENCRYPTED | 0x40 /* ALLJOYN_FLAG_COMPRESSED */ | ALLJOYN_FLAG_GLOBAL_BROADCAST | ALLJOYN_FLAG_SESSIONLESS))

        if timeToLive is not None:
            timestamp = 0       # FIXME: GetTimestamp()
            field = fields.append(MessageField).alloc(fieldId='TIME_TO_LIVE', sig='q', marshalled=timeToLive)
            field = fields.append(MessageField).alloc(fieldId='TIMESTAMP', sig='q', marshalled=timestamp)

        field = fields.append(MessageField).alloc(fieldId='PATH', sig='o', marshalled=objPath)
        field = fields.append(MessageField).alloc(fieldId='MEMBER', sig='s', marshalled=signalName)
        field = fields.append(MessageField).alloc(fieldId='INTERFACE', sig='s', marshalled=iface)

        return cls.MarshalMessage(
            signature, 'SIGNAL', flags, sender=sender, destination=destination, sessionId=sessionId,
            Fields=fields, Body=body
        )

    @classmethod
    def ReplyMsg(cls, callMsg, sender, replySignature='', body=()):
        ''' alljoyn_core/src/Message_Gen.cc:1372 '''
        fields = MessageFields().a

        assert(isinstance(callMsg, Message))
        replySerialNum = callMsg['Header']['serialNum'].int()
        field = fields.append(MessageField).alloc(fieldId='REPLY_SERIAL', sig='u', marshalled=replySerialNum)

        replyCallSessionId = callMsg['Fields'].SignatureValue('SESSION_ID').Get()
        replyFlags = {name for name, flag in callMsg['Header']['flags'].items() if flag.int()}
        replyDestination = callMsg['Fields'].SignatureValue('SENDER').Get()

        return cls.MarshalMessage(
            replySignature, 'METHOD_RET', replyFlags, sender=sender, destination=replyDestination, sessionId=replyCallSessionId,
            Fields=fields, Body=body
        )

    @classmethod
    def ErrorMessage(cls, callMsg, sender, status, errorName, description=None):
        ''' alljoyn_core/src/Message_Gen.cc:1497 '''
        fields = MessageFields().a

        assert(isinstance(callMsg, Message))
        field = fields.append(MessageField).alloc(fieldId='ERROR_NAME', sig='s', marshalled=errorName)
        field = fields.append(MessageField).alloc(fieldId='REPLY_SERIAL', sig='u', marshalled=callMsg['Header']['serialNum'].int())

        if description is None:
            signature = 'sqs'
            body = (errorName, status, description)
        else:
            signature = 'sq'
            body = (errorName, status)

        replyCallSessionId = callmsg['Fields'].SignatureValue['SESSION_ID'].Get()
        replyFlags = {name for name, flag in callMsg['Header']['flags'].items() if flag.int()}
        replyDestination = callMsg['Fields'].SignatureValue('SENDER').Get()

        return cls.MarshalMessage(signature, 'ERROR', replyFlags,
            sender=sender, destination=replyDestination, sessionId=replyCallSessionId,
            Fields=fields, Body=body
        )

class ALLJOYN_MSGARG_TYPE(ptype.generic): pass
class ALLJOYN_MSGARG_SCALAR(ALLJOYN_MSGARG_TYPE):
    def Get(self):
        return self.get()
    def Set(self, *scalar):
        return self.set(*scalar, **fields)
class ALLJOYN_MSGARG_CONTAINER(ALLJOYN_MSGARG_TYPE): pass

@MsgArg.define
class ALLJOYN_INVALID(ptype.block, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('INVALID'), 0
@MsgArg.define
class ALLJOYN_BYTE(uint8_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('BYTE'), 1
@MsgArg.define
class ALLJOYN_INT16(sint16_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('INT16'), 2
@MsgArg.define
class ALLJOYN_UINT16(uint16_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('UINT16'), 2
@MsgArg.define
class ALLJOYN_BOOLEAN(uint32_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('BOOLEAN'), 4
@MsgArg.define
class ALLJOYN_INT32(sint32_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('INT32'), 4
@MsgArg.define
class ALLJOYN_UINT32(uint32_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('UINT32'), 4
@MsgArg.define
class ALLJOYN_DOUBLE(double, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('DOUBLE'), 8
@MsgArg.define
class ALLJOYN_INT64(sint64_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('INT64'), 8
@MsgArg.define
class ALLJOYN_UINT64(uint64_t, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('UINT64'), 8
@MsgArg.define
class ALLJOYN_OBJECT_PATH(AllJoynString, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('OBJECT_PATH'), 4
@MsgArg.define
class ALLJOYN_STRING(AllJoynString, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('STRING'), 4
@MsgArg.define
class ALLJOYN_SIGNATURE(AllJoynSignature, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('SIGNATURE'), 0
@MsgArg.define
class ALLJOYN_HANDLE(AllJoynHandle, ALLJOYN_MSGARG_SCALAR):
    type, alignment = AllJoynTypeId.byname('HANDLE'), 4

@MsgArg.define
class ALLJOYN_VARIANT(AllJoynVariant, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('VARIANT'), 1

@MsgArg.define
class ALLJOYN_ARRAY(AllJoynArray, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('ARRAY'), 4

@MsgArg.define
class ALLJOYN_DICT_ENTRY_OPEN(AllJoynDictEntry, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('DICT_ENTRY_OPEN'), 8
@MsgArg.define
class ALLJOYN_DICT_ENTRY_CLOSE(AllJoynDictEntry, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('DICT_ENTRY_CLOSE'), 8

@MsgArg.define
class ALLJOYN_STRUCT_ENTRY_OPEN(AllJoynStruct, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('STRUCT_OPEN'), 8
@MsgArg.define
class ALLJOYN_STRUCT_ENTRY_CLOSE(AllJoynStruct, ALLJOYN_MSGARG_CONTAINER):
    type, alignment = AllJoynTypeId.byname('STRUCT_CLOSE'), 8

class SignatureUtils(object):
    bytemembers, charmembers = b'bdghinoqrstuvxy*', 'bdghinoqrstuvxy*'
    scalars = (lambda bytes: {character for character in itertools.chain(*([chr(ord(bytes[index : index + 1])), bytes[index : index + 1]] for index in range(len(bytes))))})(bytemembers)
    groups = {pair[:1] : pair[-1:] for pair in itertools.chain(*((pair[:1]+pair[-1:], pair[-1:]+pair[:1]) for pair in ['()', '{}', b'()', b'{}']))}
    containers = {character for character in groups} | {'a', b'a'}

    @classmethod
    def ParseContainerSignature(cls, iterable):
        members = cls.charmembers

        # start state, mostly terminals.
        start = {ch : {} for ch in members}

        # groups, seeded by terminals
        dict_open = {'}': {}, 'a': start}
        [dict_open.setdefault(ch, dict_open) for ch in members]
        struct_open = {')': {}, 'a': start}
        [struct_open.setdefault(ch, struct_open) for ch in members]
        start['{'], start['('] = dict_open, struct_open

        # cycles
        start['a'] = start
        dict_open['('], struct_open['{'] = struct_open, dict_open
        dict_open['{'], struct_open['('] = dict_open, struct_open

        # traverse the first state until we need to nest them.
        char, contents, openers = '', start, {'(', '{'}
        while not char or (contents is contents.get(char, ()) and char not in openers):
            char = next(iterable)
            yield char
            contents = contents[char]

        # if we encounter an opener, then we need a stack for nesting
        state = [contents] if char in openers else []
        while state:
            char = next(iterable)
            yield char
            if not contents[char]:
                contents = state.pop()
            elif contents[char] is not contents or char in openers:
                state.append(contents)
                contents = contents[char]
            continue
        return

    @classmethod
    def ParseContainerSignatureBytes(cls, iterable):
        types = cls.bytemembers
        members = {types[i : i+1] for i, _ in enumerate(types)}

        # start state, mostly terminals.
        start = {ch : {} for ch in members}

        # groups, seeded by terminals
        dict_open = {b'}': {}, b'a': start}
        [dict_open.setdefault(ch, dict_open) for ch in members]
        struct_open = {b')': {}, b'a': start}
        [struct_open.setdefault(ch, struct_open) for ch in members]
        start[b'{'], start[b'('] = dict_open, struct_open

        # cycles
        start[b'a'] = start
        dict_open[b'('], struct_open[b'{'] = struct_open, dict_open
        dict_open[b'{'], struct_open[b'('] = dict_open, struct_open

        # traverse the first state until we need to nest them.
        char, contents, openers = b'', start, {b'(', b'{'}
        while not char or (contents is contents.get(char, ()) and char not in openers):
            char = next(iterable)
            yield char
            contents = contents[char]

        # if we encounter an opener, then we need a stack for nesting
        state = [contents] if char in openers else []
        while state:
            char = next(iterable)
            yield char
            if not contents[char]:
                contents = state.pop()
            elif contents[char] is not contents or char in openers:
                state.append(contents)
                contents = contents[char]
            continue
        return

    @classmethod
    def Parse(cls, sig):
        members = cls.charmembers
        iterable = iter(sig)
        while True:
            character = next(iterable, '')
            if not character:
                break
            elif character in members + 'a({':
                complete = cls.ParseContainerSignature(itertools.chain(character, iterable))
                yield ''.join(complete)
            else:
                raise NotImplementedError(character)
            continue
        return

    @classmethod
    def Unmarshal(cls, string):
        chars = (string[index : index + 1] for index in range(len(string))) if isinstance(string, (bytes, bytearray)) else iter(string)
        iterable = (complete for complete in SignatureUtils.Parse(chars))
        while True:
            complete = next(iterable, b'')
            if not complete: break
            type = complete[:1]
            if type in {'a', b'a'}:
                unmarshalled = cls.UnmarshalArray(complete)
            elif type in {b'{', b'(', '{', '('}:
                unmarshalled = cls.UnmarshalContainer(complete)
            else:
                unmarshalled = cls.UnmarshalScalar(complete)
            for arg, alignment in unmarshalled:
                yield arg, alignment
            continue
        return

    @classmethod
    def UnmarshalScalar(cls, string):
        assert(len(string) == 1)
        arg = MsgArg.lookup(ord(string))
        yield arg, arg.alignment

    @classmethod
    def UnmarshalArray(cls, string):
        assert(string[:1] in {'a', b'a'})
        arg_array = MsgArg.lookup(ord(string[:1]))
        iterable = cls.Unmarshal(string[1:])
        signature = [(arg, alignment) for arg, alignment in iterable]
        #yield dyn.clone(AllJoynArray, _signature_=(string, signature)), 4
        yield dyn.clone(arg_array, _signature_=(string, signature)), 4

    @classmethod
    def UnmarshalContainer(cls, complete):
        open, close = complete[:1], complete[-1:]
        assert((cls.groups[open] == close) and (open == cls.groups[close]))
        arg_open, arg_close = (MsgArg.lookup(ord(byte)) for byte in [open, close])
        iterable = cls.Unmarshal(complete[+1 : -1])
        signature = [(arg, alignment) for arg, alignment in iterable]
        #object = dyn.clone(AllJoynSignatureValue, _signature_=(complete, signature))
        object = dyn.clone(arg_open, _signature_=(complete[+1 : -1], signature))
        yield object, 8

    @classmethod
    def Alignment(cls, complete):
        res = MsgArg.lookup(ord(complete[:1]))
        return res.alignment

class DbusSignature(pstr.szstring):
    def isTerminator(self, character):
        return not character.initializedQ()

    def __deserialize_stream_from_iterable__(self, iterable):
        item = self.new(self._object_, offset=self.getoffset())

        # use the signature parser to deserialize the matching
        # signature characters from the stream parameter.
        for character in iterable:
            item.__deserialize_block__(character)

            # we now have a character to deserialize into our value
            # after which we can check to see if it's a sentinel.
            offset = self.__append__(item)
            if self.isTerminator(item):
                break
            continue
        return self

    def __deserialize_stream__(self, stream):
        self.value, iterable = b'', SignatureUtils.ParseContainerSignatureBytes(stream)
        try:
            res = self.__deserialize_stream_from_iterable__(iterable)
        except KeyError:
            logging.warning("{:s}.__deserialize_stream__ : {:s} : Error while trying to parse signature from stream due to it not being valid.".format(self.classname(), self.instance()), exc_info=True)
            res = self
        return res

### session options
class NameTransferType(object):
    ALL_NAMES   = 0x00  # ExchangeNames and NameChanged to be forwarded to this session, AttachSessionWithNames to be converted into an ExchangeNames and sent over this session, all NameChanged to be sent, all names to be sent as a part of initial AttachSessionWithNames
    SLS_NAMES   = 0x01  # No ExchangeNames and NameChanged forwarding, no NameChanged to be sent, only router names and sessionless emitter names(if host routing node) to be sent as a part of initial AttachSessionWithNames
    MP_NAMES    = 0x02  # ExchangeNames and NameChanged to be forwarded only over endpoints that match the session id of the endpoint that it was received on, NameChanged to be sent to routing nodes if a session to this leaf existed, only routing node and joiner or host and existing session member names to be sent as a part of initial AttachSessionWithNames
    P2P_NAMES   = 0x03  # No ExchangeNames and NameChanged forwarding, NameChanged to be sent only if a session to this leaf existed, only routing node and joiner/host names to be sent as a part of initial AttachSessionWithNames

if __name__ == '__main__':
    import sys, operator

    fromhex = bytes.fromhex if hasattr(bytes, 'fromhex') else operator.methodcaller('decode', 'hex')

    def test_parse_signature_short_1():
        s = b'aixno'
        parsed = SignatureUtils.ParseContainerSignature(iter(s.decode('ascii')))
        assert(''.join(parsed) == 'ai')

    def test_parse_signature_badgroup():
        s = b'a({ii)aaa'
        parsed = SignatureUtils.ParseContainerSignature(iter(s.decode('ascii')))
        try:    [item for item in parsed]
        except KeyError: pass
        else:   assert(False)

    def test_parse_signature_short_2():
        s = 'ixxx'
        parsed = SignatureUtils.ParseContainerSignature(iter(s))
        assert(''.join(parsed) == 'i')

    def test_parse_signature_short_3():
        s = b'(i(ii))term'
        parsed = SignatureUtils.ParseContainerSignature(iter(s.decode('ascii')))
        assert(''.join(parsed) == '(i(ii))')

    def test_parse_signature_short_4():
        s = b'(aaaaaaai)no'
        parsed = SignatureUtils.ParseContainerSignature(iter(s.decode('ascii')))
        assert(''.join(parsed) == '(aaaaaaai)')

    def test_dbus_signature_invalid():
        data = b'(aaaaaaaiz)no'
        source = ptypes.provider.bytes(data)
        res = DbusSignature()
        res.load(source=source)
        assert(res.serialize() == b'(aaaaaaaiz')

    def load_le_blob():
        le_blob = b''

        # yyyyuu fixed headers
        le_blob+= b"l"                  # little-endian
        le_blob+= b"\2"                 # reply (which is the simplest message)
        le_blob+= b"\2"                 # no auto-starting
        le_blob+= b"\1"                 # D-Bus version = 1
        # byte 4
        le_blob+= b"\4\0\0\0"           # bytes in body = 4
        # byte 8
        le_blob+= b"\x78\x56\x34\x12"   # serial number = 0x12345678
        # byte 12
        # a(uv) variable headers start here
        le_blob+= b"\x0f\0\0\0"         # bytes in array of variable headers = 15
                                        # pad to 8-byte boundary = nothing
        # byte 16
        le_blob+= b"\5"                 # in reply to:
        le_blob+= b"\1u\0"              # variant signature = u
                                        # pad to 4-byte boundary = nothing
        le_blob+= b"\x12\xef\xcd\xab"   # 0xabcdef12
                                                # pad to 8-byte boundary = nothing
        # byte 24
        le_blob+= b"\x08"               # signature:
        le_blob+=    b"\1g\0"           # variant signature = g
        le_blob+=    b"\1u\0"           # 1 byte, u, NUL (no alignment needed)
        le_blob+=    b"\0"              # pad to 8-byte boundary for body
        # body; byte 32
        le_blob+= b"\xef\xbe\xad\xde"   # 0xdeadbeef

        return Message(source=ptypes.provider.bytes(le_blob)).l

    def test_MessageField():
        le_blob = b"\5"                 # in reply to:
        le_blob+= b"\1u\0"              # variant signature = u
                                        # pad to 4-byte boundary = nothing
        le_blob+= b"\x12\xef\xcd\xab"   # 0xabcdef12

        res = MessageField(source=ptypes.prov.bytes(le_blob)).l
        assert(res['fieldId']['REPLY_SERIAL']), res['fieldId'].summary()
        assert(res['sig'].str() == 'u')
        assert(res['marshalled'].Get() == 0xabcdef12)

    def load_be_blob():
        be_blob = b''

        # byte 0
        # yyyyuu fixed headers
        be_blob+= b"B"                     # big-endian
        be_blob+= b"\2"                    # reply (which is the simplest message)
        be_blob+= b"\2"                    # no auto-starting
        be_blob+= b"\1"                    # D-Bus version = 1
        # byte 4
        be_blob+= b"\0\0\0\4"              # bytes in body = 4
        # byte 8
        be_blob+= b"\x12\x34\x56\x78"      # serial number = 0x12345678
         # byte 12
        # a(uv) variable headers start here
        be_blob+= b"\0\0\0\x0f"            # bytes in array of variable headers = 15
                                # pad to 8-byte boundary = nothing
        # byte 16
        be_blob+= b"\5"                    # in reply to:
        be_blob+=    b"\1u\0"             # variant signature = u
                                # pad to 4-byte boundary = nothing
        be_blob+=    b"\xab\xcd\xef\x12"  # 0xabcdef12
                                # pad to 8-byte boundary = nothing
        # byte 24
        be_blob+= b"\x08"                  # signature:
        be_blob+=    b"\1g\0"             # variant signature = g
        be_blob+=    b"\1u\0"             # 1 byte, u, NUL (no alignment needed)
        be_blob+=    b"\0"                # pad to 8-byte boundary for body
        # body; byte 32
        be_blob+= b"\xde\xad\xbe\xef"      # 0xdeadbeef

        return Message(source=ptypes.provider.bytes(be_blob)).l

    def test_le_blob():
        le = load_le_blob()
        assert(le['header']['msgType']['METHOD_RET'])
        assert(le['header']['flags'].get() == (0, 0, 0, 0, 0, 0, 1, 0))
        assert(le['header']['serialNum'].int() == 0x12345678)
        fields = [mfield for mfield in le['fields'].iterate()]
        assert(len(fields) == 2)
        expected = [('REPLY_SERIAL', 'u', 0xabcdef12), ('SIGNATURE', 'g', 'u')]
        for field, expectation in zip(fields, expected):
            k, sig, val = expectation
            assert(field['fieldId'][k])
            assert(field['sig'].str() == sig)
            res = field['marshalled'].Get()
            [fieldval] = res[:1] if isinstance(res, (list, tuple)) else [res]
            assert(val == fieldval)
        assert(le['Body'].Get() == 0xdeadbeef)

    def test_be_blob():
        be = load_be_blob()
        assert(be['header']['msgType']['METHOD_RET'])
        assert(be['header']['flags'].get() == (0, 0, 0, 0, 0, 0, 1, 0))
        assert(be['header']['serialNum'].int() == 0x12345678)
        fields = [mfield for mfield in be['fields'].iterate()]
        assert(len(fields) == 2)
        expected = [('REPLY_SERIAL', 'u', 0xabcdef12), ('SIGNATURE', 'g', 'u')]
        for field, expectation in zip(fields, expected):
            k, sig, val = expectation
            assert(field['fieldId'][k])
            assert(field['sig'].str() == sig)
            res = field['marshalled'].Get()
            [fieldval] = res[:1] if isinstance(res, (list, tuple)) else [res]
            assert(val == fieldval)
        assert(be['Body'].Get() == 0xdeadbeef)

    def load_frida_message():
        data = ''
        data+= '6c 01 00 01 08 00 00 00 01 00 00 00 70 00 00 00'
        data+= '01 01 6f 00 15 00 00 00 2f 72 65 2f 66 72 69 64'
        data+= '61 2f 48 6f 73 74 53 65 73 73 69 6f 6e 00 00 00'
        data+= '02 01 73 00 16 00 00 00 72 65 2e 66 72 69 64 61'
        data+= '2e 48 6f 73 74 53 65 73 73 69 6f 6e 31 35 00 00'
        data+= '08 01 67 00 05 61 7b 73 76 7d 00 00 00 00 00 00'
        data+= '03 01 73 00 17 00 00 00 47 65 74 46 72 6f 6e 74'
        data+= '6d 6f 73 74 41 70 70 6c 69 63 61 74 69 6f 6e 00'
        data+= '00 00 00 00 00 00 00 00'
        data = fromhex(data.replace(' ', ''))
        return Message(source=ptypes.prov.bytes(data)).l

    def test_frida_message():
        msg = load_frida_message()
        assert(msg['header']['msgType']['METHOD_CALL'])
        assert(msg['header']['flags'].get() == (0, 0, 0, 0, 0, 0, 0, 0))
        assert(msg['header']['serialNum'].int() == 1)
        fields = [mfield for mfield in msg['fields'].iterate()]
        assert(len(fields) == 4)
        expected = [
            ('PATH', 'o', '/re/frida/HostSession'),
            ('INTERFACE', 's', 're.frida.HostSession15'),
            ('SIGNATURE', 'g', 'a{sv}'),
            ('MEMBER', 's', 'GetFrontmostApplication'),
        ]
        for field, expectation in zip(fields, expected):
            k, sig, val = expectation
            assert(field['fieldId'][k])
            assert(field['sig'].str() == sig)
            res = field['marshalled'].Get()
            [fieldval] = res[:1] if isinstance(res, (list, tuple)) else [res]
            assert(val == fieldval)
        assert(msg['Body'].serialize() == bytes(bytearray(4 * [0])))

    def test_allocate_signature_ungrouped():
        res = AllJoynSignatureValue().Allocate('(iis)(iis)')
        res.alloc([1,2,'a'], [3,4,'b'])
        assert(res.Get() == ((1, 2, 'a'), (3, 4, 'b')))

    def test_allocate_signature_array():
        res = AllJoynSignatureValue().Allocate('ai')
        res.alloc([21,42])
        assert(res.Get() == [21, 42])

    def test_array_allocate_instances():
        res = AllJoynArray().alloc([pint.uint32_t().a, pint.uint8_t().a])
        assert(res.size() == 9 == res.blocksize())
        assert(res['length'].int() == 5)
        assert(res['elements'].serialize() == bytes(bytearray(5 * [0])))

    def test_array_allocate_types():
        res = AllJoynArray().alloc(elements=4 * [pint.uint32_t])
        assert(res.size() == 4*5 == res.blocksize())
        assert(res['length'].int() == res['elements'].size() + res['extra'].size())
        assert(len(res['elements']) == 4)

    def test_array_allocate_untyped_length():
        res = AllJoynArray().alloc(length=0x10)
        assert(res.size() == 4*5 == res.blocksize())
        assert(res['length'].int() == res['elements'].size() + res['extra'].size())
        assert(len(res['elements']) == 0)

    def test_array_allocate_object_length():
        res = AllJoynArray(_object_=pint.uint32_t).alloc(length=0x10)
        assert(res.size() == 4*5 == res.blocksize())
        assert(res['length'].int() == res['elements'].size() + res['extra'].size())
        assert(len(res['elements']) == 0x10 // pint.uint32_t().a.size())

    def test_hello():
        sender, destination = 'me', org.alljoyn.Bus.WellKnownName
        a = Message.HelloMessage(True, sender, destination, True, '{123}', 'SLS_NAMES', 0)

    def test_helloreply():
        sender, unique = 'me', 'you'
        b = Message.HelloReply(True, sender, unique, '{SOMEGUID}', 4)

    def test_callmessage():
        sender, destination = 'me', 'you'
        objectpath, interface, methodname = '/path/to/something', 'interface', 'somemethod'
        c = Message.CallMsg('s', sender, destination, 21, objectpath, interface, methodname, {}, body='hai')

    def test_signalmessage():
        sender, destination = 'me', 'you'
        objectpath, interface, methodname = '/path/to/something', 'interface', 'somemethod'
        d = Message.SignalMsg('s', sender, destination, 21, objectpath, interface, methodname, {}, body='hai')

    def test_replymessage():
        sender = 'me'
        c = Message.CallMsg(Ellipsis)
        e = Message.ReplyMsg(c, sender, replySignature='s', body='hai')

    def test_errormessage():
        sender = 'me'
        c = Message.CallMsg(Ellipsis)
        f = Message.ErrorMessage(c, sender, 404, 'four-oh-four', 'this is a description')
