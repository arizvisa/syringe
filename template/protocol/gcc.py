'''
Generic Conference Control protocol (T.124)
'''
import sys, ptypes, protocol.ber as ber, protocol.per as per
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

# Create a per.LengthDeterminant that is byte-aligned as we will be using
# this in a couple of structures within the gcc protocol.
LengthDeterminant = pbinary.bigendian(per.LengthDeterminant)

### atomic types
class TokenId(pint.uint16_t): pass
class ChannelId(pint.uint16_t):
    def properties(self):
        res = super(ChannelId, self).properties()
        if self.initializedQ() and self.get() == 0x3ea:
            res['ServerChannelId'] = True
        return res

    def summary(self):
        if self.size() > 0:
            res = "{:#0{:d}x}".format(self.int(), 2 + self.size() * 2)
            return "{:s} -> {:d}".format(res, self.get())
        return '...missing...'

class StaticChannelId(ChannelId):
    def get(self):
        return 1 + self.int()
    def set(self, integer):
        if 1 <= integer < 1001:
            return super(DynamicChannelId, self).set(integer - 1)
        raise ValueError("Requested value {:d} for {:s} is not within range ({:d}<>{:d})".format(integer, self.instance(), 1, 1000))

class DynamicChannelId(ChannelId):
    def get(self):
        return 1001 + self.int()
    def set(self, integer):
        if 1001 <= integer < 65536:
            return super(DynamicChannelId, self).set(integer - 1001)
        raise ValueError("Requested value {:d} for {:s} is not within range ({:d}<>{:d})".format(integer, self.instance(), 1001, 65535))

class UserId(DynamicChannelId): pass

### Key
class Key(ptype.definition):
    cache = {}

    class Header(pbinary.enum):
        length, _values_ = 1, [
            ('object', 0),
            ('h221NonStandard', 1),
        ]

### GCCPDU
class GCCPDU(ptype.definition):
    cache = {}

    class Choice(pbinary.enum):
        length, _values_ = 2, [
            ('request', 0),
            ('response', 1),
            ('indication', 2),
        ]
    Header = Choice

@GCCPDU.define
class RequestPDU(ptype.definition):
    type, cache = 0, {}
    class Choice(pbinary.flags):
        class _choice(pbinary.enum):
            length, _values_ = 4, [
                ('conferenceJoinRequest', 0),
                ('conferenceAddRequest', 1),
                ('conferenceLockRequest', 2),
                ('conferenceUnlockRequest', 3),
                ('conferenceTerminateRequest', 4),
                ('conferenceEjectUserRequest', 5),
                ('conferenceTransferRequest', 6),
                ('registryRegisterChannelRequest', 7),
                ('registryAssignTokenRequest', 8),
                ('registrySetParameterRequest', 9),
                ('registryRetrieveEntryRequest', 10),
                ('registryDeleteEntryRequest', 11),
                ('registryMonitorEntryRequest', 12),
                ('registryAllocateHandleRequest', 13),
                ('nonStandardRequest', 14),
            ]
        _fields_ = [
            (1, 'extension'),
            (_choice, 'choice'),
        ]
    Header = Choice

@GCCPDU.define
class ResponsePDU(ptype.definition):
    type, cache = 1, {}
    class Choice(pbinary.flags):
        class _choice(pbinary.enum):
            length, _values_ = 4, [
                ('conferenceJoinResponse', 0),
                ('conferenceAddResponse', 1),
                ('conferenceLockResponse', 2),
                ('conferenceUnlockResponse', 3),
                ('conferenceTerminateResponse', 4),
                ('conferenceEjectUserResponse', 5),
                ('conferenceTransferResponse', 6),
                ('registryResponse', 7),
                ('registryAllocateHandleResponse', 8),
                ('functionNotSupportedResponse', 9),
                ('nonStandardResponse', 10),
            ]
        _fields_ = [
            (1, 'extension'),
            (_choice, 'choice'),
        ]
    Header = Choice

@GCCPDU.define
class IndicationPDU(ptype.definition):
    type, cache = 2, {}
    class Choice(pbinary.flags):
        class _choice(pbinary.enum):
            length, _values_ = 5, [
                ('userIDIndication', 0),
                ('conferenceLockIndication', 1),
                ('conferenceUnlockIndication', 2),
                ('conferenceTerminateIndication', 3),
                ('conferenceEjectUserIndication', 4),
                ('conferenceTransferIndication', 5),
                ('rosterUpdateIndication', 6),
                ('applicationInvokeIndication', 7),
                ('registryMonitorEntryIndication', 8),
                ('conductorAssignIndication', 9),
                ('conductorReleaseIndication', 10),
                ('conductorPermissionAskIndication', 11),
                ('conductorPermissionGrantIndication', 12),
                ('conferenceTimeRemainingIndication', 13),
                ('conferenceTimeInquireIndication', 14),
                ('conferenceTimeExtendIndication', 15),
                ('conferenceAssistanceIndication', 16),
                ('textMessageIndication', 17),
                ('nonStandardIndication', 18),
            ]
        _fields_ = [
            (1, 'extension'),
            (_choice, 'choice'),
        ]
    Header = Choice

### ConnectGCCPDU
class ConnectGCCPDU(ptype.definition):
    cache = {}

    class Choice(pbinary.struct):
        class _choice(pbinary.enum):
            length, _values_ = 3, [
                ('conferenceCreateRequest', 0),
                ('conferenceCreateResponse', 1),
                ('conferenceQueryRequest', 2),
                ('conferenceQueryResponse', 3),
                ('conferenceJoinRequest', 4),
                ('conferenceJoinResponse', 5),
                ('conferenceInviteRequest', 6),
                ('conferenceInviteResponse', 7),
            ]

        _fields_ = [
            (1, 'extension'),
            (_choice, 'choice'),
        ]
    Header = Choice

class Privilege(ptype.type):
    class Header(pbinary.flags):
        class _privilege(pbinary.enum):
            length, _values_ = 3, [
                ('terminate', 0),
                ('ejectUser', 1),
                ('add', 2),
                ('lockUnlock', 3),
                ('transfer', 4),
            ]

        _fields_ = [
            (1, 'extension'),
            (_privilege, 'privilege'),
        ]

class ConferenceName(ptype.type):
    class Header(pbinary.flags):
        def __padding(self):
            _, offset = self.getposition()
            return 8 - (offset + 2)
        _fields_ = [
            (1, 'extension'),
            (1, 'textQ'),
            (__padding, 'padding(conferenceName)'),
            (per.LengthDeterminant, 'length'),
            (lambda self: dyn.clone(pbinary.array, _object_=4, length=self['length'].int()+1), 'name'),
        ]

        def alloc(self, **fields):
            res = super(ConferenceName.Header, self).alloc(**fields)
            return res if 'length' in fields else res.set(length=max(0, len(res['name']) - 1))

class TerminationMethod(ptype.type):
    class Header(pbinary.flags):
        class _enumeration(pbinary.enum):
            length, _values_ = 1, [
                ('automatic', 0),
                ('manual', 1),
            ]
        _fields_ = [
            (1, 'extension'),
            (_enumeration, 'terminationMethod'),
        ]

class UserDataItem(pstruct.type):
    class Header(pbinary.flags):
        _fields_ = [
            (1, 'valueQ'),
            (Key.Header, 'key'),
        ]

    class _value(pstruct.type):
        _fields_ = [
            (LengthDeterminant, 'length'),
            (lambda self: dyn.block(self['length'].li.int()), 'value'),
        ]
        def alloc(self, **fields):
            res = super(UserDataItem._value, self).alloc(**fields)
            return res if 'length' in fields else res.set(length=res['value'].size())

    _fields_ = [
        (Header, 'header'),
        (lambda self: Key.lookup(self['header'].li['key']), 'key'),
        (lambda self, _value=_value: _value if self['header'].li['valueQ'] else ptype.undefined, 'value'),
    ]

class UserData(pstruct.type):
    _fields_ = [
        (LengthDeterminant, 'count'),
        (lambda self: dyn.array(UserDataItem, self['count'].li.int()), 'set'),
    ]

### Main PDU
class PDU(pstruct.type):
    class _header(pbinary.struct):
        def __choice(self):
            res = self['gcc']
            res = GCCPDU.lookup(res)
            return res.Header

        def __pdu(self):
            res = self['gcc']
            res = GCCPDU.lookup(res)
            res = res.lookup(self['choice']['choice'], 0)
            return getattr(res, 'Header', 0)

        _fields_ = [
            (GCCPDU.Header, 'gcc'),
            (__choice, 'choice'),
            (__pdu, 'pdu'),
        ]

    def __pdu(self):
        header = self['header'].li
        res = header['gcc']
        pduType = GCCPDU.lookup(res)
        res = header['choice']
        return pduType.get(res, ptype.undefined, __header__=header.field('pdu'))

    def __unknown(self):
        res = sum(self[fld].li.size() for fld in ['header','pdu'])
        return dyn.block(self.blocksize() - res)

    _fields_ = [
        (_header, 'header'),
        (__pdu, 'pdu'),
        (__unknown, 'unknown'),
    ]

class ConnectPDU(pstruct.type):
    @pbinary.bigendian
    class _header(pbinary.struct):
        def __pdu(self):
            res = self['connectPDU']['choice']
            res = ConnectGCCPDU.lookup(res, 0)
            return getattr(res, 'Header', 0)

        _fields_ = [
            (ConnectGCCPDU.Header, 'connectPDU'),
            (__pdu, 'pdu'),
        ]

    def __pdu(self):
        res = self['header'].li
        res = res['connectPDU']
        res = res['choice']
        return ConnectGCCPDU.get(res, __header__=self['header'].field('pdu'))

    _fields_ = [
        (_header, 'header'),
        (__pdu, 'pdu'),
    ]

class ConnectData(pstruct.type):
    class _header(pbinary.struct):
        _fields_ = [
            (Key.Header, 'key'),
        ]

    class _length_connectPDU(pstruct.type):
        _fields_ = [
            (LengthDeterminant, 'length'),
            (ConnectPDU, 'connectPDU'),
        ]
        def alloc(self, **fields):
            res = super(ConnectData._length_connectPDU, self).alloc(**fields)
            return res if 'length' in fields else res.set(length=res['connectPDU'].size())

    _fields_ = [
        (_header, 'header'),
        (lambda self: Key.lookup(self['header'].li['key']), 'Key'),
        (_length_connectPDU, 'connectPDU'),
    ]

### Key definitions
@Key.define
class Key_object(pstruct.type):
    type = 0
    _fields_ = [
        (LengthDeterminant, 'length'),
        (lambda self: dyn.clone(ber.OBJECT_IDENTIFIER, length=self['length'].li.int()), 'object'),
    ]

    def alloc(self, **fields):
        res = super(Key_object, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=res['object'].size())

@Key.define
class H221NonStandardIdentifier(pstruct.type):
    type = 1
    _fields_ = [
        (LengthDeterminant, 'length'),
        (lambda self: dyn.clone(ber.OCTET_STRING, length=self['length'].li.int() + 4), 'h221NonStandard'),
    ]

    def alloc(self, **fields):
        res = super(H221NonStandardIdentifier, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=max(0, res['h221NonStandard'].size() - 4))

    def summary(self):
        res, standard = self['length'].li, self['h221NonStandard'].serialize().decode('latin1')
        encoded = standard.encode('unicode_escape')
        return "length={:d} h221NonStandard=\"{:s}\"".format(res.int(), encoded.decode(sys.getdefaultencoding()).replace('"', '\\"'))

### GCC Definitions
@RequestPDU.define
class ConferenceTerminateRequest(ptype.undefined):
    type = 4
    class Header(pbinary.flags):
        class _result(pbinary.enum):
            length, _values_ = 1, [
                ('userInitiated', 0),
                ('timedConferenceTermination', 1),
            ]
        _fields_ = [
            (1, 'extension'),
            (_result, 'result'),
        ]

@ResponsePDU.define
class ConferenceTerminateResponse(ptype.undefined):
    type = 4
    class Header(pbinary.flags):
        class _result(pbinary.enum):
            length, _values_ = 1, [
                ('success', 0),
                ('invalidRequester', 1),
            ]
        _fields_ = [
            (1, 'extension'),
            (_result, 'result'),
        ]

### ConnectGCCPDU definitions
@ConnectGCCPDU.define
class ConferenceCreateRequest(pstruct.type):
    type = 0

    class Header(pbinary.flags):
        _fields_ = [
            (1, 'extension'),
            (1, 'convenerPasswordQ'),
            (1, 'passwordQ'),
            (1, 'conductorPrivilegesQ'),
            (1, 'conductedPrivilegesQ'),
            (1, 'nonConductedPrivilegesQ'),
            (1, 'conferenceDescriptionQ'),
            (1, 'callerIdentifierQ'),
            (1, 'userDataQ'),
            (ConferenceName.Header, 'conferenceName'),
            (1, 'lockedConference'),
            (1, 'listedConference'),
            (1, 'conductibleConference'),
            (TerminationMethod.Header, 'terminationMethod'),
            (lambda self: Privilege.Header if self['conductorPrivilegesQ'] else 0, 'conductorPrivileges'),
            (lambda self: Privilege.Header if self['conductedPrivilegesQ'] else 0, 'conductedPrivileges'),
            (lambda self: Privilege.Header if self['nonConductedPrivilegesQ'] else 0, 'nonConductedPrivileges'),
        ]

    _fields_ = [
        (ConferenceName, 'conferenceName'),
        (lambda self: Password if self.__header__['convenerPasswordQ'] else ptype.undefined, 'convenerPassword'),
        (lambda self: Password if self.__header__['passwordQ'] else ptype.undefined, 'password'),
        (ber.BOOLEAN, 'lockedConference'),
        (ber.BOOLEAN, 'listedConference'),
        (ber.BOOLEAN, 'conductibleConference'),
        (TerminationMethod, 'terminationMethod'),
        (lambda self: Privilege if self.__header__['conductorPrivilegesQ'] else ptype.undefined, 'conductorPrivileges'),
        (lambda self: Privilege if self.__header__['conductedPrivilegesQ'] else ptype.undefined, 'conductedPrivileges'),
        (lambda self: Privilege if self.__header__['nonConductedPrivilegesQ'] else ptype.undefined, 'nonConductedPrivileges'),
        (lambda self: TextString if self.__header__['conferenceDescriptionQ'] else ptype.undefined, 'conferenceDescription'),
        (lambda self: TextString if self.__header__['callerIdentifierQ'] else ptype.undefined, 'callerIdentifier'),
        (lambda self: UserData if self.__header__['userDataQ'] else ptype.undefined, 'userData'),
    ]

@ConnectGCCPDU.define
class ConferenceCreateResponse(pstruct.type):
    type = 1

    class Header(pbinary.flags):
        _fields_ = [
            (1, 'extension'),
            (1, 'userDataQ'),
        ]

    class extensionResult(pbinary.flags):
        class Result(pbinary.enum):
            length, _values_=  3, [
                ('success', 0),
                ('userRejected', 1),
                ('resourcesNotAvailable', 2),
                ('rejectedForSymmetryBreaking', 3),
                ('lockedConferenceNotSupported', 4),
            ]
        _fields_ = [
            (1, 'extension'),
            (Result, 'result'),
        ]

    _fields_ = [
        (UserId, 'nodeID'),
        (per.INTEGER, 'tag'),
        (extensionResult, 'result'),
        (lambda self: UserData if self.__header__['userDataQ'] else ptype.undefined, 'userData'),
    ]
