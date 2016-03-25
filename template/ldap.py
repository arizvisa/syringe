#https://www.ietf.org/rfc/rfc4511.txt
import ptypes,ber
from ptypes import *

### Helpers
if False:
    class CHOICE(ber.Element):
        def __init__(self, **kwds):
            ctx = self.protocol.get(Context.Class)
            for tag,name,element in self._values_:
                result = dyn.clone(element, __name__=name, type=(self.__class__,tag))
                element = ctx.define(result)
            return super(CHOICE,self).__init__(**kwds)

        def Value(self):
            t = self['Type'].li
            cons,n = t['Constructed'],t['Tag'].number()

            ctx = self.protocol.get(Context.Class)
            try:
                res = ctx.lookup((self.__class__,n))
            except KeyError:
                return super(CHOICE,self).Value()
            return res

    class CONSTRAINT(parray.type):
        class Local(ptype.definition): cache = {}
        class Optional(ptype.definition): cache = {}

        def __init__(self, **kwds):
            for i,(t,name) in enumerate(self._fields_):
                type = t.type if hasattr(t,'type') else i
                result = dyn.clone(t, __name__=name)
                if hasattr(t,'OPTIONAL'):
                    self.Optional.define(dyn.clone(result, type=(self.__class__,type)))
                self.Local.define(dyn.clone(result, type=(self.__class__,i)))
            return super(CONSTRAINT,self).__init__(**kwds)

        def append(self, value):
            Type = value['Type'].li
            c,n = Type['Class'],Type['Tag'].number()
            index = len(self)
            try:
                parent = self.__class__
                t = self.Optional.cache.get((parent,n), self.Local.lookup((parent,index)))
            except KeyError:
                res = value
            else:
                res = value.copy(Value=lambda:t, __name__=t.__name__)
            return super(CONSTRAINT,self).append(res)

###########
@ber.protocol.copy
class protocol(ber.protocol): pass
class record(ber.Element): protocol = protocol

@protocol.define
class Application(ber.Application): cache = {}
@protocol.define
class Context(ber.Context): cache = {}

### ber primitives
class CHOICE(ber.CHOICE): protocol = protocol
def OPTIONAL(t): return dyn.clone(t, OPTIONAL=True)

def SETOF(t):
    return dyn.clone(ber.SET, _object_=t)
def COMPONENTSOF(t):
    return t
def SEQUENCEOF(t):
    return dyn.clone(ber.SEQUENCE, _object_=t)

### primitives
class MessageID(ber.INTEGER): pass
class LDAPString(ber.OCTETSTRING): pass
class LDAPOID(ber.OCTETSTRING): pass
class URI(LDAPString): pass
class Referral(URI): pass

class LDAPDN(LDAPString): pass
class RelativeLDAPDN(LDAPString): pass
class AttributeDescription(LDAPString): pass
class AttributeValue(ber.OCTETSTRING): pass
class MatchingRuleId(LDAPString): pass

class Op(record): pass

class Control(ber.SEQUENCE):
    _fields_ = [
        (LDAPOID, 'controlType'),
        (ber.BOOLEAN, 'criticality'),
        (OPTIONAL(ber.OCTETSTRING), 'controlValue'),
    ]

class LDAPMessage(ber.SEQUENCE):
    _fields_ = [
        (MessageID, 'MessageID'),
        (Op, 'protocolOp'),
        (Control, 'controls'),
    ]

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

class AssertionValue(ber.OCTETSTRING): pass

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

class Attribute(PartialAttribute): pass

class LDAPResult(ber.SEQUENCE):
    _fields_ = [
        (ResultCode, 'resultCode'),
        (LDAPDN, 'matchedDN'),
        (LDAPString, 'diagnosticMessage'),
        (OPTIONAL(Referral), 'referral'),
    ]

#### requests
class SaslCredentials(ber.SEQUENCE):
    _fields_ = [
        (LDAPString, 'mechanism'),
        (OPTIONAL(ber.OCTETSTRING), 'credentials'),
    ]

class AuthenticationChoice(CHOICE):
    _values_ = [
        (0, 'simple', ber.OCTETSTRING),
        (3, 'sasl', SaslCredentials),
    ]

@Application.define
class BindRequest(ber.SEQUENCE):
    type = 0
    _fields_ = [
        (ber.INTEGER, 'version'),
        (LDAPDN, 'name'),
        (AuthenticationChoice, 'authentication'),
    ]

@Application.define
class BindResponse(ber.SEQUENCE):
    type = 1
    _fields_ = [
        (COMPONENTSOF(LDAPResult), 'result'),
        (OPTIONAL(ber.OCTETSTRING), 'serverSaslCreds'),
    ]

@Application.define
class UnbindRequest(ber.NULL):
    type = 2

class SubstringFilter(ber.SEQUENCE):
    class substrings(ber.SEQUENCE):
        class _object_(CHOICE):
            _values_ = [
                (0, 'initial', AssertionValue),
                (1, 'any', AssertionValue),
                (2, 'final', AssertionValue),
            ]
    _fields_ = [
        (AttributeDescription, 'type'),
        (substrings, 'substrings'),
    ]

class MatchingRuleAssertion(ber.SEQUENCE):
    class MatchingRuleId(LDAPString): pass
    _fields_ = [
        (OPTIONAL(MatchingRuleId), 'MatchingRule'),
        (OPTIONAL(AttributeDescription), 'type'),
        (AssertionValue, 'matchValue'),
        (ber.BOOLEAN, 'dnAttributes'),
    ]

class Filter(CHOICE):
    _values_ = [
        (0, 'and', lambda s: SETOF(Filter)),
        (1, 'or', lambda s: SETOF(Filter)),
        (2, 'not', lambda s: Filter),
        (3, 'equalityMatch', AttributeValueAssertion),
        (4, 'substrings', SubstringFilter),
        (5, 'greaterOrEqual', AttributeValueAssertion),
        (6, 'lessOrEqual', AttributeValueAssertion),
        (7, 'present', AttributeDescription),
        (8, 'approxMatch', AttributeValueAssertion),
        (9, 'extensibleMatch', MatchingRuleAssertion),
    ]

@Application.define
class SearchRequest(ber.SEQUENCE):
    type = 3

    class scope(ber.ENUMERATED):
        _values_ = [
            (0, 'baseObject'),
            (1, 'singleLevel'),
            (2, 'wholeSubtree'),
        ]
    class derefAliases(ber.ENUMERATED):
        _values_ = [
            (0, 'neverDerefAliases'),
            (1, 'derefInSearching'),
            (2, 'derefFindingBaseObj'),
            (3, 'derefAlways'),
        ]
    class AttributeSelection(SEQUENCEOF(LDAPString)): pass

    _fields_ = [
        (LDAPDN, 'baseObject'),
        (scope, 'scope'),
        (derefAliases, 'derefAliases'),
        (ber.INTEGER, 'sizeLimit'),
        (ber.INTEGER, 'timeLimit'),
        (ber.BOOLEAN, 'typesOnly'),
        (Filter, 'filter'),
        (AttributeSelection, 'attributes'),
    ]

@Application.define
class SearchResult(ber.SEQUENCE):
    type = 4
    class PartialAttributeList(SEQUENCEOF(PartialAttribute)): pass
    _fields_ = [
        (LDAPDN, 'objectName'),
        (PartialAttributeList, 'attributes'),
    ]

@Application.define
class SearchResultReference(SEQUENCEOF(URI)):
    type = 19

@Application.define
class SearchResultDone(LDAPResult):
    type = 5

@Application.define
class ModifyRequest(ber.SEQUENCE):
    type = 6
    class change(ber.SEQUENCE):
        class operation(ber.ENUMERATED):
            _values_ = [(0,'add'), (1,'delete'), (2,'replace')]
        _fields_ = [
            (operation, 'operation'),
            (PartialAttribute, 'modification'),
        ]
    _fields_ = [
        (LDAPDN, 'object'),
        (SEQUENCEOF(change), 'changes'),
    ]

@Application.define
class ModifyResponse(LDAPResult):
    type = 7

@Application.define
class AddRequest(ber.SEQUENCE):
    type = 8
    class AttributeList(SEQUENCEOF(Attribute)): pass
    _fields_ = [
        (LDAPDN, 'entry'),
        (AttributeList, 'attributes'),
    ]
@Application.define
class AddResponse(LDAPResult):
    type = 9

@Application.define
class DelRequest(LDAPDN):
    type = 10

@Application.define
class DelResponse(LDAPResult):
    type = 11

@Application.define
class ModifyDNRequest(ber.SEQUENCE):
    type = 12
    _fields_ = [
        (LDAPDN, 'entry'),
        (RelativeLDAPDN, 'newrdn'),
        (ber.BOOLEAN, 'deleteoldrdn'),
        (OPTIONAL(LDAPDN), 'newSuperior'),
    ]

@Application.define
class ModifyDNResponse(LDAPResult):
    type = 13

@Application.define
class CompareRequest(ber.SEQUENCE):
    type = 14
    _fields_ = [
        (LDAPDN, 'entry'),
        (AttributeValueAssertion, 'ava'),
    ]

@Application.define
class CompareResponse(LDAPResult):
    type = 15

@Application.define
class AbandonRequest(MessageID):
    type = 16

@Application.define
class ExtendedRequest(ber.SEQUENCE):
    type = 23
    _fields_ = [
        (LDAPOID, 'requestName'),
        (OPTIONAL(ber.OCTETSTRING), 'requestValue'),
    ]

@Application.define
class ExtendedResponse(ber.SEQUENCE):
    type = 24
    _fields_ = [
        (COMPONENTSOF(LDAPResult), 'result'),
        (OPTIONAL(LDAPOID), 'responseName'),
        (OPTIONAL(ber.OCTETSTRING), 'responseValue'),
    ]

@Application.define
class IntermediateResponse(ber.SEQUENCE):
    type = 25
    _fields_ = [
        (OPTIONAL(LDAPOID), 'responseName'),
        (OPTIONAL(ber.OCTETSTRING), 'responseValue'),
    ]

class packet(record):
    def Value(self):
        return LDAPMessage
