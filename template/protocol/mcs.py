'''
Multipoint communication service protocol (T.125)
'''
import logging, ptypes, protocol.gcc as gcc, protocol.ber as ber, protocol.per as per
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### MCS protocol data (BER Encoding)
class Protocol(ber.Protocol.copy(recurse=True)):
    pass
class Element(ber.Element):
    Protocol = Protocol
Protocol.default = Element
class Packet(Element):
    byteorder = ptypes.config.byteorder.bigendian

# FIXME: this number is actually encoded with PER-ALIGNED
class Result(pbinary.enum):
    length, _values_ = 4, [
        ('rt-successful', 0),
        ('rt-domain-merging', 1),
        ('rt-domain-not-hierarchical', 2),
        ('rt-no-such-channel', 3),
        ('rt-no-such-domain', 4),
        ('rt-no-such-user', 5),
        ('rt-not-admitted', 6),
        ('rt-other-user-id', 7),
        ('rt-parameters-unacceptable', 8),
        ('rt-token-not-available', 9),
        ('rt-token-not-possessed', 10),
        ('rt-too-many-channels', 11),
        ('rt-too-many-tokens', 12),
        ('rt-too-many-users', 13),
        ('rt-unspecified-failure', 14),
    ]

    def summary(self):
        return "{:s}({:d})".format(self.str(), self.int())

class Reason(pbinary.enum):
    length, _values_ = 3, [
        ('rn-domain-disconnect', 0),
        ('rn-provider-initiated', 1),
        ('rn-token-purged', 2),
        ('rn-user-requested', 3),
        ('rn-channel-purged', 4),
    ]

class TokenStatus(ber.ENUMERATED):
    _values_ = [
        ('notInUse', 0),
        ('selfGrabbed', 1),
        ('otherGrabbed', 2),
        ('selfInhibited', 3),
        ('otherInhibited', 4),
        ('selfRecipient', 5),
        ('selfGiving', 6),
        ('otherGiving', 7),
    ]

class DataPriority(ber.ENUMERATED):
    _values_ = [
        ('top', 0),
        ('high', 1),
        ('medium', 2),
        ('low', 3),
    ]

class DomainParameters(ber.SEQUENCE):
    _fields_ = [
        (ber.INTEGER, 'maxChannelIds'),
        (ber.INTEGER, 'maxUserIds'),
        (ber.INTEGER, 'maxTokenIds'),
        (ber.INTEGER, 'numPriorities'),
        (ber.INTEGER, 'minThroughput'),
        (ber.INTEGER, 'maxHeight'),
        (ber.INTEGER, 'maxMCSPDUsize'),
        (ber.INTEGER, 'protocolVersion'),
    ]

@Protocol.Application.define
class ConnectInitial(ber.SEQUENCE):
    tag = 101

    _fields_ = [
        (ber.OCTET_STRING, 'callingDomainSelector'),
        (ber.OCTET_STRING, 'calledDomainSelector'),
        (ber.BOOLEAN, 'upwardFlag'),
        (DomainParameters, 'targetParameters'),
        (DomainParameters, 'minimumParameters'),
        (DomainParameters, 'maximumParameters'),
        (ber.OCTET_STRING, 'userData'),
    ]

@Protocol.Application.define
class ConnectResponse(ber.SEQUENCE):
    tag = 102

    class Result(ber.ENUMERATED):
        def str(self):
            res = self.cast(Result, width=8 * self.size())
            return res.str()

        def int(self):
            res = self.cast(Result, width=8 * self.size())
            return res.int()

        def summary(self):
            return "{:s}({:d})".format(self.str(), self.int())

    # FIXME: is this right?
    _fields_ = [
        (Result, 'result'),
        (ber.INTEGER, 'calledConnectId'),
        (DomainParameters, 'domainParameters'),
        (ber.OCTET_STRING, 'userData'),
    ]

@Protocol.Application.define
class ConnectAdditional(ber.SEQUENCE):
    tag = 103

    _fields_ = [
        (ber.INTEGER, 'calledConnectId'),
        (DataPriority, 'dataPriority'),
    ]

@Protocol.Application.define
class ConnectResult(ber.SEQUENCE):
    tag = 104

    _fields_ = [
        (ber.OCTET_STRING, 'result'),
    ]

### DomainMCSPDU
class DomainMCSPDU(ptype.definition):
    cache = {}

    class Choice(pbinary.enum):
        length, _values_ = 6, [
            ('plumbDomainIndication', 0),
            ('erectDomainRequest', 1),
            ('mergeChannelsRequest', 2),
            ('mergeChannelsConfirm', 3),
            ('purgeChannelsIndication', 4),
            ('mergeTokensRequest', 5),
            ('mergeTokensConfirm', 6),
            ('purgeTokensIndication', 7),
            ('disconnectProviderUltimatum', 8),
            ('rejectMCSPDUUltimatum', 9),
            ('attachUserRequest', 10),
            ('attachUserConfirm', 11),
            ('detachUserRequest', 12),
            ('detachUserIndication', 13),
            ('channelJoinRequest', 14),
            ('channelJoinConfirm', 15),
            ('channelLeaveRequest', 16),
            ('channelConveneRequest', 17),
            ('channelConveneConfirm', 18),
            ('channelDisbandRequest', 19),
            ('channelDisbandIndication', 20),
            ('channelAdmitRequest', 21),
            ('channelAdmitIndication', 22),
            ('channelExpelRequest', 23),
            ('channelExpelIndication', 24),
            ('sendDataRequest', 25),            # Each of these cases are handled by HandleAllSendDataPDUs
            ('sendDataIndication', 26),         #
            ('uniformSendDataRequest', 27),     #
            ('uniformSendDataIndication', 28),  #
            ('tokenGrabRequest', 29),
            ('tokenGrabConfirm', 30),
            ('tokenInhibitRequest', 31),
            ('tokenInhibitConfirm', 32),
            ('tokenGiveRequest', 33),
            ('tokenGiveIndication', 34),
            ('tokenGiveResponse', 35),
            ('tokenGiveConfirm', 36),
            ('tokenPleaseRequest', 37),
            ('tokenPleaseIndication', 38),
            ('tokenReleaseRequest', 39),
            ('tokenReleaseConfirm', 40),
            ('tokenTestRequest', 41),
            ('tokenTestConfirm', 42),
        ]
    Header = Choice

### Main PDU
class PDU(pstruct.type):
    '''
    MCS packet
    '''
    @pbinary.bigendian
    class _header(pbinary.struct):
        def __value(self):
            res = self['choice']
            res = DomainMCSPDU.lookup(res, 0)
            return getattr(res, 'Header', 0)

        _fields_ = [
            (DomainMCSPDU.Header, 'choice'),
            (__value, 'value'),
        ]

    def __value(self):
        res = self['header'].li
        return DomainMCSPDU.get(res['choice'], ptype.undefined, __header__=res.item('value'))

    _fields_ = [
        (_header, 'header'),
        (__value, 'value'),
    ]

    def alloc(self, **fields):

        # Check if the caller is allocating the 'value' field
        if 'value' in fields and not isinstance(fields['value'], dict):
            res = fields['value']

            # If so, then copy its Header type into the 'header' field
            hdr = fields.setdefault('header', {})
            if isinstance(hdr, dict) and hasattr(res, 'Header'):
                hdr.setdefault('value', res.Header)
            elif isinstance(hdr, ptype.base) and hasattr(res, 'Header'):
                hdr['value'] = res.Header().a
                res.__header__ = hdr['value']
            elif ptypes.istype(res) and not hasattr(res, 'Header'):
                logging.warning("Unable to map .__header__ attribute for {:s} due to missing .Header attribute for value {:s}".format(self.classname(), res.typename()))

        # Now we can finally allocate our instance
        res = super(PDU, self).alloc(**fields)

        # If there is currently no '__header__' attribute, then explicitly assign one
        if not hasattr(res['value'], '__header__'):
            res['value'].__header__ = res['header'].item('value')
        return res

### DomainMCSPDU definitions
@DomainMCSPDU.define
class PlumbDomainIndication(pstruct.type):
    type = 0
    _fields_ = [
        (dyn.clone(ber.INTEGER, length=2), 'heightLimit'),
    ]

    def summary(self):
        return "heightLimit={:d}".format(self['heightLimit'].int())

@DomainMCSPDU.define
class ErectDomainRequest(pstruct.type):
    type = 1
    _fields_ = [
        (per.INTEGER, 'subHeight'),
        (per.INTEGER, 'subInterval'),
    ]

    def summary(self):
        return "subHeight={:s} subInterval={:s}".format(self['subHeight'].summary(), self['subInterval'].summary())

@DomainMCSPDU.define
class DisconnectProviderUltimatum(ptype.undefined):
    type = 8
    Header = Reason

    def __getitem__(self, name):
        if name.lower() == 'reason':
            return self.__header__
        raise KeyError(name)

    def summary(self):
        return "reference(reason)={:s}".format(self['reason'].summary())

    def set(self, **fields):
        if 'reason' in fields:
            self['reason'].set(fields.pop('reason'))
        return super(DisconnectProviderUltimatum, self).set(**fields)

    def details(self):
        return "[{:x}] <reference {:s} 'reason'> {:s}".format(self.getoffset(), self['reason'].classname(), self['reason'].summary()) + '\n'

    def repr(self):
        return self.details()

class Diagnostic(pbinary.enum):
    length, _values_ = 4, [
        ('dc-inconsistent-merge', 0),
        ('dc-forbidden-PDU-downward', 1),
        ('dc-forbidden-PDU-upward', 2),
        ('dc-invalid-BER-encoding', 3),
        ('dc-invalid-PER-encoding', 4),
        ('dc-misrouted-user', 5),
        ('dc-unrequested-confirm', 6),
        ('dc-wrong-transport-priority', 7),
        ('dc-channel-id-conflict', 8),
        ('dc-token-id-conflict', 9),
        ('dc-not-user-id-channel', 10),
        ('dc-too-many-channels', 11),
        ('dc-too-many-tokens', 12),
        ('dc-too-many-users', 13),
    ]

@DomainMCSPDU.define
class RejectMCSPDUUltimatum(pstruct.type):
    type = 9
    Header = Diagnostic

    _fields_ = [
        (gcc.LengthDeterminant, 'length'),
        (lambda self: dyn.clone(ber.OCTET_STRING, length=self['length'].li.int()), 'initialOctets'),
    ]

    def __field__(self, name):
        if name.lower() == 'diagnostic':
            return self.__header__
        return super(RejectMCSPDUUltimatum, self).__field__(name)

    def summary(self):
        return "reference(diagnostic)={:s} initialOctets={:s}".format(self['diagnostic'].summary(), self['initialOctets'].summary())

@DomainMCSPDU.define
class AttachUserRequest(ptype.undefined):
    type = 10

@DomainMCSPDU.define
class AttachUserConfirm(pstruct.type):
    type = 11
    class Header(pbinary.flags):
        _fields_ = [
            (1, 'initiatorQ'),
            (Result, 'result'),
        ]

    def __initiator(self):
        res = self.__header__
        return gcc.UserId if res['initiatorQ'] else dyn.clone(gcc.UserId, length=0)

    _fields_ = [
        (__initiator, 'initiator'),
    ]

    def __field__(self, name):
        if name.lower() == 'result':
            return self.__header__.item('result')
        return super(AttachUserConfirm, self).__field__(name)

    def summary(self):
        if self.__header__['initiatorQ']:
            return "reference(result)={:s} initiator={:s}".format(self['result'].summary(), self['initiator'].summary())
        return "reference(result)={:s}".format(self['result'].summary())

@DomainMCSPDU.define
class DetachUserRequest(pstruct.type):
    type = 12

    Header = Reason

    _fields_ = [
        (gcc.LengthDeterminant, 'count'),
        (lambda self: dyn.array(gcc.UserId, self['count'].li.int()), 'userIds'),
    ]

    def __field__(self, name):
        if name.lower() == 'reason':
            return self.__header__
        return super(DetachUserRequest, self).__field__(name)

    def summary(self):
        res = self['userIds']
        return "reference(reason)={:s} userIds=[{:s}]".format(self['reason'].summary(), ', '.join(item.summary() for item in res))

    def alloc(self, **fields):
        res = super(DetachUserRequest, self).alloc(**fields)
        return res if 'count' in fields else res.set(count=len(res['userIds']))

    def set(self, **fields):
        if 'reason' in fields:
            self['reason'].set(fields.pop('reason'))
        return super(DetachUserRequest, self).set(**fields)

@DomainMCSPDU.define
class DetachUserIndication(DetachUserRequest):
    type = 13

@DomainMCSPDU.define
class ChannelJoinRequest(pstruct.type):
    type = 14
    _fields_ = [
        (gcc.UserId, 'initiator'),
        (gcc.ChannelId, 'channelId'),
    ]

    def summary(self):
        return "initiator={:s} channelId={:s}".format(self['initiator'].summary(), self['channelId'].summary())

@DomainMCSPDU.define
class ChannelJoinConfirm(pstruct.type):
    type = 15
    class Header(pbinary.flags):
        _fields_ = [
            (1, 'channelIdQ'),
            (Result, 'result'),
        ]

    def __channelId(self):
        res = self.__header__
        return gcc.ChannelId if res['channelIdQ'] else dyn.clone(gcc.ChannelId, length=0)

    _fields_ = [
        (gcc.UserId, 'initiator'),
        (gcc.ChannelId, 'requested'),
        (__channelId, 'channelId'),
    ]

    def __field__(self, name):
        if name.lower() == 'result':
            return self.__header__.item('result')
        return super(ChannelJoinConfirm, self).__field__(name)

    def summary(self):
        if self.__header__['channelIdQ']:
            return "reference(result)={:s} initiator={:s} requested={:s} channelId={:s}".format(self['result'].summary(), self['initiator'].summary(), self['requested'].summary(), self['channelId'].summary())
        return "reference(result)={:s} initiator={:s} requested={:s}".format(self['result'].summary(), self['initiator'].summary(), self['requested'].summary())

@DomainMCSPDU.define
class ChannelLeaveRequest(pstruct.type):
    type = 16
    _fields_ = [
        (gcc.LengthDeterminant, 'count'),
        (lambda self: dyn.array(gcc.ChannelId, self['count'].li.int()), 'channelIds'),
    ]

    def alloc(self, **fields):
        res = super(ChannelLeaveRequest, self).alloc(**fields)
        return res if 'count' in fields else res.set(count=len(res['channelIds']))

    def summary(self):
        return "({:d}) [{:s}]".format(self['count'].int(), ', '.join(ch.summary() for ch in self['channelIds']))

@DomainMCSPDU.define
class ChannelConveneRequest(pstruct.type):
    type = 17
    _fields_ = [
        (gcc.UserId, 'initiator'),
    ]

    def summary(self):
        return "initiator={:s}".format(self['initiator'].summary())

@DomainMCSPDU.define
class ChannelDisbandRequest(pstruct.type):
    type = 19
    _fields_ = [
        (gcc.UserId, 'initiator'),
        (gcc.ChannelId, 'channelId'),
    ]

    def summary(self):
        return "initiator={:s} channelId={:s}".format(self['initiator'].summary(), self['channelId'].summary())

@DomainMCSPDU.define
class ChannelDisbandIndication(pstruct.type):
    type = 20
    _fields_ = [
        (gcc.ChannelId, 'channelId'),
    ]

    def summary(self):
        return "channelId={:s}".format(self['channelId'].summary())

class DataPriority(pbinary.enum):
    length, _values_ = 2, [
        ('top', 0),
        ('high', 1),
        ('medium', 2),
        ('low', 3),
    ]

class Segmentation(pbinary.integer):
    def blockbits(self):
        return 2

class SendDataPDU(pstruct.type):
    '''
    Microsoft's RDP implementation handles each of the available Send-
    Data types (SendDataRequest, SendDataIndication, UniformSendDataRequest, and
    UniformSendDataIndication) with the same handler since they have the exact
    same structure. Due to this, we implement all of them via this definition
    and use it as a base-class when assigning each one individually so that we
    can test against all of them via a single individual type.
    '''

    @pbinary.bigendian
    class _priority_segmentation(pbinary.struct):
        _fields_ = [
            (DataPriority, 'dataPriority'),
            (Segmentation, 'segmentation'),
        ]

    class _length_userData(pstruct.type):
        _fields_ = [
            (gcc.LengthDeterminant, 'length'),
            (lambda self: dyn.block(self['length'].li.int()), 'data'),
        ]

    _fields_ = [
        (gcc.UserId, 'initiator'),
        (gcc.ChannelId, 'channelId'),

        (_priority_segmentation, 'dataAttributes'),
        (_length_userData, 'userData'),
    ]

@DomainMCSPDU.define
class SendDataRequest(SendDataPDU):
    type = 25

@DomainMCSPDU.define
class SendDataIndication(SendDataPDU):
    type = 26

@DomainMCSPDU.define
class UniformSendDataRequest(SendDataRequest):
    type = 27

@DomainMCSPDU.define
class UniformSendDataIndication(SendDataIndication):
    type = 28
