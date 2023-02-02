import ptypes, ndk
from ptypes import *
from ndk.datatypes import *

### [MS-NEGOEX]
class AUTH_SCHEME(ndk.GUID): pass
class CONVERSATION_ID(ndk.GUID): pass

class ALERT_VECTOR(pstruct.type):
    _fields_ = [
        (ULONG, 'AlertArrayOffset'),
        (USHORT, 'AlertCount'),
    ]

class AUTH_SCHEME_VECTOR(pstruct.type):
    _fields_ = [
        (ULONG, 'AuthSchemeArrayOffset'),
        (USHORT, 'AuthSchemeCount'),
    ]

class BYTE_VECTOR(pstruct.type):
    _fields_ = [
        (ULONG, 'ByteArrayOffset'),
        (ULONG, 'ByteArrayLength'),
    ]

class EXTENSION_VECTOR(pstruct.type):
    _fields_ = [
        (ULONG, 'ExtensionArrayOffset'),
        (USHORT, 'ExtensionCount'),
    ]

class ALERT_TYPE_(pint.enum):
    _values_ = [
        ('PULSE', 1),
    ]

class ALERT(pstruct.type):
    class _AlertType(ALERT_TYPE_, ULONG):
        pass
    _fields_ = [
        (ULONG, 'AlertType'),
        (BYTE_VECTOR, 'AlertValue'),
    ]

class ALERT_VERIFY_(pint.enum):
    _values_ = [
        ('NO_KEY', 1),
    ]

class ALERT_PULSE(pstruct.type):
    class _Reason(ALERT_VERIFY_, ULONG):
        pass
    _fields_ = [
        (ULONG, 'cbHeaderLength'),
        (ULONG, 'Reason'),
    ]

class CHECKSUM_SCHEME_(pint.enum):
    _values_ = [
        ('RFC3961', 1),
    ]

class CHECKSUM(pstruct.type):
    class _ChecksumScheme(CHECKSUM_SCHEME_, ULONG):
        pass
    _fields_ = [
        (ULONG, 'cbHeaderLength'),
        (ULONG, 'ChecksumScheme'),
        (ULONG, 'ChecksumType'),
        (BYTE_VECTOR, 'ChecksumValue'),
    ]

class EXTENSION(pstruct.type):
    _fields_ = [
        (ULONG, 'ExtensionType'),
        (BYTE_VECTOR, 'ExtensionValue'),
    ]

class MESSAGE_TYPE_(pint.enum):
    _values_ = [
        ('INITIATOR_NEGO', 0),
        ('ACCEPTOR_NEGO', 1),
        ('INITIATOR_META_DATA', 2),
        ('ACCEPTOR_META_DATA', 3),
        ('CHALLENGE', 4),
        ('AP_REQUEST', 5),
        ('VERIFY', 6),
        ('ALERT', 7),
    ]

class MESSAGE_TYPE(MESSAGE_TYPE_, ULONG): pass

class MESSAGE_HEADER(pstruct.type):
    class _Signature(ULONG64):
        0x535458454f47454e

    _fields_ = [
        (ULONG64, 'Signature'),
        (MESSAGE_TYPE, 'MessageType'),
        (ULONG, 'SequenceNum'),
        (ULONG, 'cbHeaderLength'),
        (ULONG, 'cbMessageLength'),
        (CONVERSATION_ID, 'ConversationId'),
    ]

class NEGO_MESSAGE(pstruct.type):
    _fields_ = [
        (MESSAGE_HEADER, 'Header'),
        (dyn.array(UCHAR, 32), 'Random'),
        (ULONG64, 'ProtocolVersion'),
        (AUTH_SCHEME_VECTOR, 'AuthSchemes'),
        (EXTENSION_VECTOR, 'Extensions'),
    ]

class EXCHANGE_MESSAGE(pstruct.type):
    _fields_ = [
        (MESSAGE_HEADER, 'Header'),
        (AUTH_SCHEME, 'AuthScheme'),
        (BYTE_VECTOR, 'Exchange'),
    ]

class VERIFY_MESSAGE(pstruct.type):
    _fields_ = [
        (MESSAGE_HEADER, 'Header'),
        (AUTH_SCHEME, 'AuthScheme'),
        (CHECKSUM, 'Checksum'),
    ]

class ALERT_MESSAGE(pstruct.type):
    _fields_ = [
        (MESSAGE_HEADER, 'Header'),
        (AUTH_SCHEME, 'AuthScheme'),
        (ULONG, 'ErrorCode'),           # NTSTATUS
        (ALERT_VECTOR, 'Alerts'),
    ]

if __name__ == '__main__':
    import operator
    import sys, ptypes, protocol.spnegoex as spex

    # INITIATOR_NEGO
    '''
    0000   4e 45 47 4f 45 58 54 53 00 00 00 00 00 00 00 00   NEGOEXTS........
    0010   60 00 00 00 70 00 00 00 36 91 b8 12 16 8c ba d4   `...p...6.......
    0020   f6 7c 3b 24 f0 69 35 c7 f1 1e 9e 45 67 89 22 83   .|;$.i5....Eg.".
    0030   8a e1 f2 23 2f db db 12 dc be 22 9f 8c 3f 58 69   ...#/....."..?Xi
    0040   4d e6 0a 4f 5a 82 8e f4 00 00 00 00 00 00 00 00   M..OZ...........
    0050   60 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00   `...............
    0060   5c 33 53 0d ea f9 0d 4d b2 ec 4a e3 78 6e c3 08   \3S....M..J.xn..
    '''

    # MESSAGE_HEADER
    '''
    0000   4e 45 47 4f 45 58 54 53 00 00 00 00 00 00 00 00   NEGOEXTS........
    0010   60 00 00 00 70 00 00 00 36 91 b8 12 16 8c ba d4   `...p...6.......
    0020   f6 7c 3b 24 f0 69 35 c7                           .|;$.i5.
    '''

    # RANDOM, ProtocolVersion
    '''
    0020   f6 7c 3b 24 f0 69 35 c7 f1 1e 9e 45 67 89 22 83   .|;$.i5....Eg.".
    0030   8a e1 f2 23 2f db db 12 dc be 22 9f 8c 3f 58 69   ...#/....."..?Xi
    0040   4d e6 0a 4f 5a 82 8e f4 00 00 00 00 00 00 00 00   M..OZ...........
    '''

    # AuthSchemes
    '''
    0050   60 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00   `...............
    0060   5c 33 53 0d ea f9 0d 4d b2 ec 4a e3 78 6e c3 08   \3S....M..J.xn..
    '''
