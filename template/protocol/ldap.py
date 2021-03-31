#https://www.ietf.org/rfc/rfc4511.txt
import ptypes
from . import ber
from ptypes import *

Protocol = ber.Protocol.copy(recurse=True)
class Record(ber.Packet):
    Protocol = Protocol

Application = Protocol.lookup(ber.Application.Class)
Context = Protocol.lookup(ber.Context.Class)
Universal = Protocol.lookup(ber.Universal.Class)

### ber primitives
def OPTIONAL(t, **attrs):
    attrs.setdefault('OPTIONAL', True)
    return dyn.clone(t, **attrs)

def SETOF(t, **attrs):
    class result(Record): pass
    def lookup(self, klasstag, primitive=t):
        return primitive if primitive.type == klasstag else None
    result.__object__ = lookup
    result.__name__ = "SETOF({:s})".format(t.__name__)
    attrs.setdefault('_object_', result)
    return dyn.clone(ber.SET, **attrs)

def SEQUENCEOF(t, **attrs):
    class result(Record): pass
    def lookup(self, klasstag, primitive=t):
        return primitive if primitive.type == klasstag else None
    result.__object__ = lookup
    result.__name__ = "SEQUENCEOF({:s})".format(t.__name__)
    attrs.setdefault('_object_', result)
    return dyn.clone(ber.SEQUENCE, **attrs)

### primitives
class LDAPString(ber.OCTETSTRING):
    pass

class LDAPOID(ber.OCTETSTRING):
    pass

class LDAPDN(LDAPString):
    pass

class RelativeLDAPDN(LDAPString):
    pass

class AttributeDescription(LDAPString):
    pass

class AttributeValue(ber.OCTETSTRING):
    pass

class AssertionValue(ber.OCTETSTRING):
    pass

class AttributeValueAssertion(ber.SEQUENCE):
    _fields_ = [
        (AttributeDescription, 'attributeDesc'),
        (AssertionValue, 'assertionValue'),
    ]

class PartialAttribute(ber.SEQUENCE):
    _fields_ = [
        (AttributeDescription, 'type'),
        (SETOF(AttributeValue), 'vals'),
    ]

class Attribute(PartialAttribute):
    pass

class MatchingRuleId(LDAPString):
    pass

class ResultCode(ber.ENUMERATED):
    _values_ = [
        ('success', 0),
        ('operationsError', 1),
        ('protocolError', 2),
        ('timeLimitExceeded', 3),
        ('sizeLimitExceeded', 4),
        ('compareFalse', 5),
        ('compareTrue', 6),
        ('authMethodNotSupported', 7),
        ('strongerAuthRequired', 8),
        ('reserved', 9),
        ('referral', 10),
        ('adminLimitExceeded', 11),
        ('unavailableCriticalExtension', 12),
        ('confidentialityRequired', 13),
        ('saslBindInProgress', 14),
        ('noSuchAttribute', 16),
        ('undefinedAttributeType', 17),
        ('inappropriateMatching', 18),
        ('constraintViolation', 19),
        ('attributeOrValueExists', 20),
        ('invalidAttributeSyntax', 21),
        ('noSuchObject', 32),
        ('aliasProblem', 33),
        ('invalidDNSyntax', 34),
        ('isLeaf', 35),
        ('aliasDereferencingProblem', 36),
        ('inappropriateAuthentication', 48),
        ('invalidCredentials', 49),
        ('insufficientAccessRights', 50),
        ('busy', 51),
        ('unavailable', 52),
        ('unwillingToPerform', 53),
        ('loopDetect', 54),
        ('namingViolation', 64),
        ('objectClassViolation', 65),
        ('notAllowedOnNonLeaf', 66),
        ('notAllowedOnRDN', 67),
        ('entryAlreadyExists', 68),
        ('objectClassModsProhibited', 69),
        ('CLDAP', 70),
        ('affectsMultipleDSAs', 71),
        ('other', 80),
    ]

class URI(LDAPString):
    pass

class Referral(SEQUENCEOF(URI)):
    pass

class LDAPResult(ber.SEQUENCE):
    _fields_ = [
        (ResultCode, 'resultCode'),
        (LDAPDN, 'matchedDN'),
        (LDAPString, 'diagnosticMessage'),
        (OPTIONAL(Referral, type=(Context, 3)), 'referral'),
    ]

class Control(ber.SEQUENCE):
    _fields_ = [
        (LDAPOID, 'controlType'),
        (ber.BOOLEAN, 'criticality'),
        (OPTIONAL(ber.OCTETSTRING), 'controlValue'),
    ]

class Controls(SEQUENCEOF(Control)):
    pass

class SaslCredentials(ber.SEQUENCE):
    _fields_ = [
        (LDAPString, 'mechanism'),
        (OPTIONAL(ber.OCTETSTRING), 'credentials'),
    ]

class AuthenticationChoice(ber.Constructed):
    _values_ = [
        (dyn.clone(ber.OCTETSTRING, type=(Context, 0)), 'simple'),
        (dyn.clone(SaslCredentials, type=(Context, 3)), 'sasl'),
    ]

@Application.define
class BindRequest(ber.SEQUENCE):
    tag = 0
    _fields_ = [
        (ber.INTEGER, 'version'),
        (LDAPDN, 'name'),
        (AuthenticationChoice, 'authentication'),
    ]

@Application.define
class BindResponse(LDAPResult):
    tag = 1
    _fields_ = LDAPResult._fields_ + [
        (OPTIONAL(ber.OCTETSTRING, type=(Context, 7)), 'serverSaslCreds'),
    ]

@Application.define
class UnbindRequest(ber.NULL):
    tag = 2

class SubstringFilter(ber.SEQUENCE):
    class _substrings(ber.Constructed):
        _fields_ = [
            (dyn.clone(AssertionValue, type=(Context, 0)), 'initial'),
            (dyn.clone(AssertionValue, type=(Context, 1)), 'any'),
            (dyn.clone(AssertionValue, type=(Context, 2)), 'final'),
        ]
    _fields_ = [
        (AttributeDescription, 'type'),
        (SEQUENCEOF(_substrings), 'substrings'),
    ]

class MatchingRuleId(LDAPString):
    pass

class MatchingRuleAssertion(ber.SEQUENCE):
    _fields_ = [
        (OPTIONAL(MatchingRuleId, type=(Context, 1)), 'MatchingRule'),
        (OPTIONAL(AttributeDescription, type=(Context, 2)), 'type'),
        (dyn.clone(AssertionValue, type=(Context, 3)), 'matchValue'),
        (dyn.clone(ber.BOOLEAN, type=(Context, 4)), 'dnAttributes'),
    ]

class Filter(ber.Constructed):
    def __and(self):
        return SETOF(Filter, **attrs)
    __and.type = (Context, 0)

    def __or(self):
        return SETOF(Filter, **attrs)
    __or.type = (Context, 1)

    def __not(self):
        return Filter
    __not.type = (Context, 2)

    _fields_ = [
        (__and, 'and'),
        (__or, 'or'),
        (__not, 'not'),
        (dyn.clone(AttributeValueAssertion, type=(Context, 3)), 'equalityMatch'),
        (dyn.clone(SubstringFilter, type=(Context, 4)), 'substrings'),
        (dyn.clone(AttributeValueAssertion, type=(Context, 5)), 'greaterOrEqual'),
        (dyn.clone(AttributeValueAssertion, type=(Context, 6)), 'lessOrEqual'),
        (dyn.clone(AttributeDescription, type=(Context, 7)), 'present'),
        (dyn.clone(AttributeValueAssertion, type=(Context, 8)), 'approxMatch'),
        (dyn.clone(MatchingRuleAssertion, type=(Context, 9)), 'extensibleMatch'),
    ]

class AttributeSelection(SEQUENCEOF(LDAPString)):
    pass

@Application.define
class SearchRequest(ber.SEQUENCE):
    tag = 3
    class _scope(ber.ENUMERATED):
        _values_ = [
            ('baseObject', 0),
            ('singleLevel', 1),
            ('wholeSubtree', 2),
        ]

    class _derefAliases(ber.ENUMERATED):
        _values_ = [
            ('neverDerefAliases', 0),
            ('derefInSearching', 1),
            ('derefFindingBaseObj', 2),
            ('derefAlways', 3),
        ]

    _fields_ = [
        (LDAPDN, 'baseObject'),
        (_scope, 'scope'),
        (_derefAliases, 'derefAliases'),
        (ber.INTEGER, 'sizeLimit'),
        (ber.INTEGER, 'timeLimit'),
        (ber.BOOLEAN, 'typesOnly'),
        (Filter, 'filter'),
        (AttributeSelection, 'attributes'),
    ]

class PartialAttributeList(SEQUENCEOF(PartialAttribute)):
    pass

@Application.define
class SearchResultEntry(ber.SEQUENCE):
    tag = 4
    _fields_ = [
        (LDAPDN, 'objectName'),
        (PartialAttributeList, 'attributes'),
    ]

@Application.define
class SearchResultReference(SEQUENCEOF(URI)):
    tag = 19

@Application.define
class SearchResultDone(LDAPResult):
    tag = 5

@Application.define
class ModifyRequest(ber.SEQUENCE):
    tag = 6
    class _changes(ber.SEQUENCE):
        class _operation(ber.ENUMERATED):
            _values_ = [
                (0, 'add'),
                (1, 'delete'),
                (2, 'replace')
            ]
        _fields_ = [
            (_operation, 'operation'),
            (PartialAttribute, 'modification'),
        ]
    _fields_ = [
        (LDAPDN, 'object'),
        (SEQUENCEOF(_changes), 'changes'),
    ]

@Application.define
class ModifyResponse(LDAPResult):
    tag = 7

class AttributeList(SEQUENCEOF(Attribute)):
    pass

@Application.define
class AddRequest(ber.SEQUENCE):
    tag = 8
    _fields_ = [
        (LDAPDN, 'entry'),
        (AttributeList, 'attributes'),
    ]

@Application.define
class AddResponse(LDAPResult):
    tag = 9

@Application.define
class DelRequest(LDAPDN):
    tag = 10

@Application.define
class DelResponse(LDAPResult):
    tag = 11

@Application.define
class ModifyDNRequest(ber.SEQUENCE):
    tag = 12
    _fields_ = [
        (LDAPDN, 'entry'),
        (RelativeLDAPDN, 'newrdn'),
        (ber.BOOLEAN, 'deleteoldrdn'),
        (OPTIONAL(LDAPDN, type=(Context, 0)), 'newSuperior'),
    ]

@Application.define
class ModifyDNResponse(LDAPResult):
    tag = 13

@Application.define
class CompareRequest(ber.SEQUENCE):
    tag = 14
    _fields_ = [
        (LDAPDN, 'entry'),
        (AttributeValueAssertion, 'ava'),
    ]

@Application.define
class CompareResponse(LDAPResult):
    tag = 15

class MessageID(ber.INTEGER):
    pass

@Application.define
class AbandonRequest(MessageID):
    tag = 16

@Application.define
class ExtendedRequest(ber.SEQUENCE):
    tag = 23
    _fields_ = [
        (dyn.clone(LDAPOID, type=(Context, 0)), 'requestName'),
        (OPTIONAL(ber.OCTETSTRING, type=(Context, 1)), 'requestValue'),
    ]

@Application.define
class ExtendedResponse(LDAPResult):
    tag = 24
    _fields_ = LDAPResult._fields_ + [
        (OPTIONAL(LDAPOID, type=(Context, 10)), 'responseName'),
        (OPTIONAL(ber.OCTETSTRING, type=(Context, 11)), 'responseValue'),
    ]

@Application.define
class IntermediateResponse(ber.SEQUENCE):
    tag = 25
    _fields_ = [
        (OPTIONAL(LDAPOID, type=(Context, 0)), 'responseName'),
        (OPTIONAL(ber.OCTETSTRING, type=(Context, 1)), 'responseValue'),
    ]

class Op(ber.Constructed):
    _fields_ = [
        (BindRequest, 'bindRequest'),
        (BindResponse, 'bindResponse'),
        (UnbindRequest, 'unbindRequest'),
        (SearchRequest, 'searchRequest'),
        (SearchResultEntry, 'searchResEntry'),
        (SearchResultDone, 'searchResDone'),
        (SearchResultReference, 'searchResRef'),
        (ModifyRequest, 'modifyRequest'),
        (ModifyResponse, 'modifyResponse'),
        (AddRequest, 'addRequest'),
        (AddResponse, 'addResponse'),
        (DelRequest, 'delRequest'),
        (DelResponse, 'delResponse'),
        (ModifyDNRequest, 'modDNRequest'),
        (ModifyDNResponse, 'modDNResponse'),
        (CompareRequest, 'compareRequest'),
        (CompareResponse, 'compareResponse'),
        (AbandonRequest, 'abandonRequest'),
        (ExtendedRequest, 'extendedReq'),
        (ExtendedResponse, 'extendedResp'),
    ]

class LDAPMessage(ber.SEQUENCE):
    _fields_ = [
        (MessageID, 'messageID'),
    ] + Op._fields_ + [
        (dyn.clone(Controls, type=(Context, 0)), 'controls'),
    ]

class Packet(Record):
    def __object__(self, _):
        return LDAPMessage

if __name__ == '__main__':
    import sys, operator, ptypes, protocol.ldap as ldap
    from ptypes import *

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex
    x = ldap.MessageID(length=1).set(5)
    y = ldap.Packet().alloc(Value=LDAPMessage().alloc(messageID=x, controls=dict()))
    print(y)
