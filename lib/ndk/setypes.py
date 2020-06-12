import ptypes
from ptypes import *

from . import extypes
from .datatypes import *

class STANDARD_RIGHTS_(pbinary.flags):
    _fields_ = [
        (1, 'SYNCHRONIZE'),
        (1, 'WRITE_OWNER'),
        (1, 'WRITE_DAC'),
        (1, 'READ_CONTROL'),
        (1, 'DELETE'),
    ]

class GENERIC_(pbinary.flags):
    _fields_ = [
        (1, 'READ'),
        (1, 'WRITE'),
        (1, 'EXECUTE'),
        (1, 'ALL'),
    ]

class ACCESS_MASK(pbinary.flags):
    def _SPECIFIC_RIGHTS(self):
        return 16

    _fields_ = [
        (GENERIC_, 'GENERIC_RIGHTS'),
        (2, 'RESERVED1'),
        (1, 'MAXIMUM_ALLOWED'),
        (1, 'ACCESS_SYSTEM_SECURITY'),
        (3, 'RESERVED2'),
        (STANDARD_RIGHTS_, 'STANDARD_RIGHTS'),
        (lambda self: self._SPECIFIC_RIGHTS(), 'SPECIFIC_RIGHTS'),
    ]

### Security Descriptor Related Things
class SID_IDENTIFIER_AUTHORITY(parray.type):
    length = 6
    _object_ = pint.uint8_t

    _values_ = [
        ('NULL_SID_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
        ('WORLD_SID_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x01)),
        ('LOCAL_SID_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x02)),
        ('CREATOR_SID_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x03)),
        ('NON_UNIQUE_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x04)),
        ('SECURITY_NT_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x05)),
        ('SECURITY_APP_PACKAGE_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x0f)),
        ('SECURITY_MANDATORY_LABEL_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x10)),
        ('SECURITY_SCOPED_POLICY_ID_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x11)),
        ('SECURITY_AUTHENTICATION_AUTHORITY', (0x00, 0x00, 0x00, 0x00, 0x00, 0x12)),
    ]

    def authority(self):
        res = self.get()
        return next((name for name, value in self._values_ if res == value), None)

    def str(self):
        items = (item.int() for item in self)
        return "{{{:s}}}".format(','.join(map("{:d}".format, items)))

    def summary(self):
        res = self.authority()
        return "{:s}{:s}".format('' if res is None else "{:s} ".format(res), self.str())

    def int(self):
        res = 0
        for item in self:
            res *= 0x100
            res += item.int()
        return res

class SID(pstruct.type):
    _fields_ = [
        (UCHAR, 'Revision'),
        (UCHAR, 'SubAuthorityCount'),
        (SID_IDENTIFIER_AUTHORITY, 'IdentifierAuthority'),
        (lambda s: dyn.array(DWORD, s['SubAuthorityCount'].li.int()), 'SubAuthority'),
    ]

    def summary(self):
        res = (item.int() for item in self['SubAuthority'])
        return 'S-{:d}-{:d}'.format(self['Revision'].int(), self['IdentifierAuthority'].int()) + ('-' if self['SubAuthorityCount'].int() > 0 else '') + '-'.join(map("{:d}".format, res))

class ACE_TYPE(ptype.definition):
    cache = {}

class _ACE_TYPE(pint.enum, UCHAR):
    '''
    The name of this enumeration comes from the suffix of all the symbols
    that it contains.
    '''
    _values_ = [
        ('ACCESS_ALLOWED', 0x0),
        ('ACCESS_DENIED', 0x1),
        ('SYSTEM_AUDIT', 0x2),
        ('SYSTEM_ALARM', 0x3),
        ('ACCESS_ALLOWED_COMPOUND', 0x4),
        ('ACCESS_ALLOWED_OBJECT', 0x5),
        ('ACCESS_DENIED_OBJECT', 0x6),
        ('SYSTEM_AUDIT_OBJECT', 0x7),
        ('SYSTEM_ALARM_OBJECT', 0x8),
        ('ACCESS_ALLOWED_CALLBACK', 0x9),
        ('ACCESS_DENIED_CALLBACK', 0xa),
        ('ACCESS_ALLOWED_CALLBACK_OBJECT', 0xb),
        ('ACCESS_DENIED_CALLBACK_OBJECT', 0xc),
        ('SYSTEM_AUDIT_CALLBACK', 0xd),
        ('SYSTEM_ALARM_CALLBACK', 0xe),
        ('SYSTEM_AUDIT_CALLBACK_OBJECT', 0xf),
        ('SYSTEM_ALARM_CALLBACK_OBJECT', 0x10),
        ('SYSTEM_MANDATORY_LABEL', 0x11),
    ]

class INHERIT_ACE(pbinary.flags):
    _fields_ = [
        (1, 'INHERITED_ACE'),
        (1, 'INHERIT_ONLY_ACE'),
        (1, 'NO_PROPAGATE_INHERIT_ACE'),
        (1, 'CONTAINER_INHERIT_ACE'),
        (1, 'OBJECT_INHERIT_ACE'),
    ]

class ACE_FLAG(pbinary.flags):
    _fields_ = [
        (1, 'FAILED_ACCESS'),
        (1, 'SUCCESSFUL_ACCESS'),
        (1, 'RESERVED'),
        (INHERIT_ACE, 'VALID_INHERIT_FLAGS'),
    ]

class ACE_HEADER(pstruct.type):
    _fields_ = [
        (_ACE_TYPE, 'AceType'),
        (ACE_FLAG, 'AceFlags'),
        (USHORT, 'AceSize'),
    ]

class ACE(pstruct.type):
    def __Access(self):
        res = self['Header'].li
        return ACE_TYPE.lookup(res['AceType'].int())

    def __ApplicationData(self):
        res = self['Header'].li
        return dyn.block(max((0, res['AceSize'].size() - self['Access'].li.size())))

    _fields_ = [
        (ACE_HEADER, 'Header'),
        (__Access, 'Access'),
        (__ApplicationData, 'ApplicationData'),
    ]

class ACCESS_ACE_MASK_AND_SID(pstruct.type):
    _fields_ = [
        (ACCESS_MASK, 'Mask'),
        (SID, 'Sid'),
    ]

class ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE(pstruct.type):
    _fields_ = [
        (ACCESS_MASK, 'Mask'),
        (DWORD, 'Flags'),
        (GUID, 'ObjectType'),
        (GUID, 'InheritedObjectType'),
        (SID, 'Sid'),
    ]

# TODO: Implement the rest of the ACCESS_ and SYSTEM_ constructed security types

@ACE_TYPE.define
class ACCESS_ALLOWED_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 0

@ACE_TYPE.define
class ACCESS_DENIED_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 1

@ACE_TYPE.define
class SYSTEM_AUDIT_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 2

@ACE_TYPE.define
class SYSTEM_ALARM_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 3

@ACE_TYPE.define
class ACCESS_ALLOWED_OBJECT_ACE(ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE):
    type = 5

@ACE_TYPE.define
class ACCESS_DENIED_OBJECT_ACE(ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE):
    type = 6

@ACE_TYPE.define
class ACCESS_ALLOWED_CALLBACK_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 9

@ACE_TYPE.define
class ACCESS_DENIED_CALLBACK_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 10

@ACE_TYPE.define
class ACCESS_ALLOWED_CALLBACK_OBJECT_ACE(ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE):
    type = 11

@ACE_TYPE.define
class ACCESS_DENIED_CALLBACK_OBJECT_ACE(ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE):
    type = 12

@ACE_TYPE.define
class SYSTEM_AUDIT_CALLBACK_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 13

@ACE_TYPE.define
class SYSTEM_AUDIT_CALLBACK_OBJECT_ACE(ACCESS_ACE_MASK_FLAGS_AND_OBJECTTYPE):
    type = 15

@ACE_TYPE.define
class SYSTEM_MANDATORY_LABEL_ACE(ACCESS_ACE_MASK_AND_SID):
    type = 17

class ACL(pstruct.type):
    _fields_ = [
        (UCHAR, 'AclRevision'),
        (UCHAR, 'Sbz1'),
        (USHORT, 'AclSize'),
        (USHORT, 'AceCount'),
        (USHORT, 'Sbz2'),
    ]

class SECURITY_DESCRIPTOR_CONTROL(pbinary.flags):
    _fields_ = [
        (1, 'SE_SELF_RELATIVE'),
        (1, 'SE_RM_CONTROL_VALID'),
        (1, 'SE_SACL_PROTECTED'),
        (1, 'SE_DACL_PROTECTED'),
        (1, 'SE_SACL_AUTO_INHERITED'),
        (1, 'SE_DACL_AUTO_INHERITED'),
        (1, 'SE_SACL_AUTO_INHERIT_REQ'),
        (1, 'SE_DACL_AUTO_INHERIT_REQ'),
        (1, 'SE_SERVER_SECURITY'),
        (1, 'SE_DACL_UNTRUSTED'),
        (1, 'SE_SACL_DEFAULTED'),
        (1, 'SE_SACL_PRESENT'),
        (1, 'SE_DACL_DEFAULTED'),
        (1, 'SE_DACL_PRESENT'),
        (1, 'SE_GROUP_DEFAULTED'),
        (1, 'SE_OWNER_DEFAULTED'),
    ]

class SECURITY_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (UCHAR, 'Revision'),
        (UCHAR, 'Sbz1'),
        (SECURITY_DESCRIPTOR_CONTROL, 'Control'),

        # XXX: These are conditional depending on the SE_*_DEFAULTED flags in the Control field being unset
        (lambda self: dyn.clone(ptype.opointer_t, _baseobject_=self, _object_=SID), 'Owner'),
        (lambda self: dyn.clone(ptype.opointer_t, _baseobject_=self, _object_=SID), 'Group'),

        # XXX: These are conditional depending on the SE_*_PRESENT flags in the Control field being set
        (lambda self: dyn.clone(ptype.opointer_t, _baseobject_=self, _object_=ACL), 'Sacl'),
        (lambda self: dyn.clone(ptype.opointer_t, _baseobject_=self, _object_=ACL), 'Dacl'),
    ]

class TOKEN_SOURCE(pstruct.type):
    TOKEN_SOURCE_LENGTH = 8
    _fields_ = [
        (dyn.clone(pstr.string, length=TOKEN_SOURCE_LENGTH), 'SourceName'),
        (LUID, 'SourceIdentifier'),
    ]

class SEP_AUDIT_POLICY_CATEGORIES(pbinary.struct):
    _fields_ = [
        (4, 'System'),
        (4, 'Logon'),
        (4, 'ObjectAccess'),
        (4, 'PrivilegeUse'),
        (4, 'DetailedTracking'),
        (4, 'PolicyChange'),
        (4, 'AccountManagement'),
        (4, 'DirectoryServiceAccess'),
        (4, 'AccountLogon'),
    ]

class SEP_AUDIT_POLICY(ULONGLONG):
    pass

class TOKEN_TYPE(pint.enum, ULONG):
    _values_ = [
        ('TokenPrimary', 1),
        ('TokenImpersonation', 2),
    ]

class SID_AND_ATTRIBUTES(pstruct.type):
    _fields_ = [
        (P(SID), 'Sid'),
        (ULONG, 'Attributes'),
    ]

class SE_PRIVILEGE_(pbinary.flags):
    _fields_ = [
        (1, 'USED_FOR_ACCESS'),
        (28, 'RESERVED'),
        (1, 'REMOVED'),
        (1, 'ENABLED'),
        (1, 'ENABLED_BY_DEFAULT'),
    ]

class LUID_AND_ATTRIBUTES(pstruct.type):
    _fields_ = [
        (LUID, 'Luid'),
        (SE_PRIVILEGE_, 'Attributes'),
    ]

class PRIVILEGE_SET_(pbinary.flags):
    _fields_ = [
        (31, 'RESERVED'),
        (1, 'ALL_NECESSARY'),
    ]

class PRIVILEGE_SET(pstruct.type):
    _fields_ = [
        (DWORD, 'PrivilegeCount'),
        (PRIVILEGE_SET_, 'Control'),
        (lambda self: dyn.array(LUID_AND_ATTRIBUTES, self['PrivilegeCount'].li.int()), 'Privilege'),
    ]

class TOKEN_PRIVILEGES(pstruct.type):
    _fields_ = [
        (DWORD, 'PrivilegeCount'),
        (lambda self: dyn.array(LUID_AND_ATTRIBUTES, self['PrivilegeCount'].li.int()), 'Privileges'),
    ]

class SECURITY_IMPERSONATION_LEVEL(pint.enum, ULONG):
    _fields_ = [
        ('SecurityAnonymous', 0),
        ('SecurityIdentification', 1),
        ('SecurityImpersonation', 2),
        ('SecurityDelegation', 3),
    ]

class TOKEN(pstruct.type):
    _fields_ = [
        (TOKEN_SOURCE, 'TokenSource'),
        (LUID, 'TokenId'),
        (LUID, 'AuthenticationId'),
        (LUID, 'ParentTokenId'),
        (LARGE_INTEGER, 'ExpirationTime'),
        (P(extypes.ERESOURCE), 'TokenLock'),
        (lambda self: dyn.block(8 - self['TokenLock'].li.size()), 'padding(TokenLock)'),
        (SEP_AUDIT_POLICY, 'AuditPolicy'),
        (LUID, 'ModifiedId'),
        (ULONG, 'SessionId'),
        (ULONG, 'UserAndGroupCount'),
        (ULONG, 'RestrictedSidCount'),
        (ULONG, 'PrivilegeCount'),
        (ULONG, 'VariableLength'),
        (ULONG, 'DynamicCharged'),
        (ULONG, 'DynamicAvailable'),
        (ULONG, 'DefaultOwnersIndex'),
        (P(SID_AND_ATTRIBUTES), 'UserAndGroups'),
        (P(SID_AND_ATTRIBUTES), 'RestrictedSids'),
        (P(SID), 'PrimaryGroup'),
        (P(LUID_AND_ATTRIBUTES), 'Privileges'),
        (P(ULONG), 'DynamicPart'),
        (P(ACL), 'DefaultDacl'),
        (TOKEN_TYPE, 'TokenType'),
        (SECURITY_IMPERSONATION_LEVEL, 'ImpersionationLevel'),
        (ULONG, 'TokenFlags'),
        (dyn.clone(BOOLEAN, length=4), 'TokenInUse'),
        (PVOID, 'ProxyData'),
        (PVOID, 'AuditData'),
        (LUID, 'OriginatingLogonSession'),
        (ULONG, 'VariablePart'),
    ]

if __name__ == '__main__':
    sids = []; push = sids.append
    push("""
    01 04 00 00 00 00 00 05
    15 00 00 00 A7 40 4F 46
    FE 3C DA 76 44 37 1D 25
    """)
    push("""
    01 02 00 00 00 00 00 05
    20 00 00 00 20 02 00 00
    """)
    push("""
    01 01 00 00 00 00 00 01
    00 00 00 00
    """)

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    for siddata in sids:
        data = siddata.translate(None, ' \n')
        print("decoding {!s}".format(data))

        c = SID(__name__='sid').load(source=prov.bytes(fromhex(data)))
        print(c)

        for i, item in enumerate(c['SubAuthority']):
            print(i, item)

        print(c.summary())
