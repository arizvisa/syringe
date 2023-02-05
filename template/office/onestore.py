'''[MS-ONESTORE]'''
import ptypes, builtins, operator, os, math, functools, itertools, sys, types
from ptypes import *
from .intsafe import *

class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u32(pint.uint32_t): pass
class u64(pint.uint64_t): pass
class s8(pint.sint8_t): pass
class s16(pint.sint16_t): pass
class s32(pint.sint32_t): pass
class s64(pint.sint64_t): pass

class u24(pint.uint_t): length = 3
class u128(pint.uint_t): length = 16

class uint_default(pint.uinteger_t):
    @classmethod
    def default(cls):
        if not hasattr(cls, '_default_'):
            raise AttributeError('_default_')
        default = cls._default_
        return cls().set(default)
    def valid(self):
        return self.int() == self.default().int()
    def properties(self):
        res = super(uint_default, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

### 2.2 Common Types
class ExtendedGUID(pstruct.type):
    _fields_ = [
        (GUID, 'guid'),
        (u32, 'n'),
    ]

class CompactID(pstruct.type):
    _fields_ = [
        (u8, 'n'),
        (u24, 'guidIndex'),
    ]

class StringInStorageBuffer(pstruct.type):
    _fields_ = [
        (u32, 'cch'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cch'].li.int()), 'StringData'),
    ]

### 2.2.4 File Chunk Reference
class FileChunkTarget(pstruct.type):
    def __data(self):
        reference = self.getparent(FileChunkReference)
        return reference._object_ if isinstance(getattr(reference, '_object_', None), ptype.type) else ptype.undefined

    def __padding(self):
        reference = self.getparent(FileChunkReference)
        expected, fields = reference['cb'].li, ['data']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (__data, 'data'),
        (__padding, 'padding'),
    ]

class FileChunkReference(pstruct.type):
    def valid(self):
        fcrNil = pow(2, 8 * self['stp'].blocksize()) - 1
        return self['stp'].int() != fcrNil

    def properties(self):
        res = super(FileChunkReference, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

    def alloc(self, **fields):
        res = super(FileChunkReference, self).alloc(**fields)
        return res if 'stp' in fields else res.set(stp=pow(2, 8 * res['stp'].blocksize()))

class FileChunkReference32(FileChunkReference):
    _fields_ = [
        (dyn.pointer(FileChunkTarget, u32), 'stp'),
        (u32, 'cb'),
    ]

class FileNodeChunkReference(FileChunkReference):
    _fields_ = [
        (dyn.pointer(FileChunkTarget, u32), 'stp'),
        (u32, 'cb'),
    ]

class FileChunkReference64(FileChunkReference):
    _fields_ = [
        (dyn.pointer(FileChunkTarget, u64), 'stp'),
        (u64, 'cb'),
    ]

class FileChunkReference64x32(FileChunkReference):
    _fields_ = [
        (dyn.pointer(FileChunkTarget, u64), 'stp'),
        (u32, 'cb'),
    ]

### 2.6.10 ObjectInfoDependencyOverrideData
class ObjectInfoDependencyOverride8(pstruct.type):
    _fields_ = [
        (CompactID, 'oid'),
        (u8, 'cRef'),
    ]

class ObjectInfoDependencyOverride32(pstruct.type):
    _fields_ = [
        (CompactID, 'oid'),
        (u32, 'cRef'),
    ]

class ObjectInfoDependencyOverrideData(pstruct.type):
    _fields_ = [
        (u32, 'c8BitOverrides'),
        (u32, 'c32BitOverrides'),
        (u32, 'crc'),
        (lambda self: dyn.array(ObjectInfoDependencyOverride8, self['c8BitOverrides'].li.int()), 'Overrides1'),
        (lambda self: dyn.array(ObjectInfoDependencyOverride32, self['c32BitOverrides'].li.int()), 'Overrides2'),
    ]

### 2.6.13 FileDataStoreObject
class FileDataStoreObject(pstruct.type):
    _fields_ = [
        (GUID, 'guidHeader'),
        (u64, 'cbLength'),
        (u32, 'unused'),
        (u64, 'reserved'),
        (lambda self: dyn.block(self['cbLength'].li.int()), 'FileData'),
        (dyn.padding(8), 'padding(FileData)'),
        (GUID, 'guidFotter'),
    ]

### 2.6.14 JCID
class JCID(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'IsBinary'),
            (1, 'IsPropertySet'),
            (1, 'IsGraphNode'),
            (1, 'IsFileData'),
            (1, 'IsReadOnly'),
            (11, 'Reserved'),
        ]
    _fields_ = [
        (u16, 'index'),
        (_flags, 'flags'),
    ]

### 2.6.15 ObjectDeclarationWithRefCountBody
class ObjectDeclarationWithRefCountBody(pbinary.struct):
    class _jci(pbinary.flags):
        _fields_ = [
            (10, 'jci'),
            (4, 'odcs'),
            (2, 'fReserved1'),
        ]
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'fHasOidReferences'),
            (1, 'fHasOsidReferences'),
            (30, 'fReserved2'),
        ]
    _fields_ = [
        (CompactID, 'oid'),
        (_jci, 'jci'),
        (_flags, 'flags'),
    ]

### 2.6.16 ObjectDeclaration2Body
class ObjectDeclaration2Body(pstruct.type):
    class _flags(pbinary.flags):
        _fields_ = [
            (1, 'fHasOidReferences'),
            (1, 'fHasOsidReferences'),
            (30, 'fReserved2'),
        ]
    _fields_ = [
        (CompactID, 'oid'),
        (JCID, 'jcid'),
        (_flags, 'flags'),
    ]

### 2.4 File Node List
class FileNodeHeader(pbinary.struct):
    class _StpFormat(pbinary.enum):
        length, _values_ = 2, [
            ('8u', 0),  # 8 bytes, uncompressed.
            ('4u', 1),  # 4 bytes, uncompressed.
            ('2c', 2),  # 2 bytes, compressed.
            ('4c', 3),  # 4 bytes, compressed.
        ]

    class _CbFormat(pbinary.enum):
        length, _values_ = 2, [
            ('4u', 0),  # 4 bytes, uncompressed.
            ('8u', 1),  # 8 bytes, uncompressed.
            ('1c', 2),  # 1 bytes, compressed.
            ('2c', 3),  # 2 bytes, compressed.
        ]

    class _BaseType(pbinary.enum):
        length, _values_ = 4, [
            ('none', 0),    # This FileNode structure does not reference other data
            ('data', 1),    # This FileNode structure contains a reference to data.
            ('list', 2),    # This FileNode structure contains a reference to a file node list.
        ]
    _fields_ = [
        (10, 'FileNodeID'),
        (13, 'Size'),
        (_StpFormat, 'StpFormat'),
        (_CbFormat, 'CbFormat'),
        (_BaseType, 'BaseType'),
        (1, 'Reserved'),
    ]

class FileNodeType(ptype.definition):
    cache = {}

class FileNode(pstruct.type):
    def __fnd(self):
        header = self['header'].li
        id, size = (header[fld] for fld in ['FileNodeID', 'Size'])
        try:
            element = FileNodeType.lookup(id)
        except Exception:
            return dyn.array(ptype.block, 0)
        return dyn.blockarray(element, size)

    def __padding(self):
        header = self['header'].li
        size, fields = header['Size'], ['header', 'fnd']
        return dyn.block(max(0, size - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (FileNodeHeader, 'header'),
        (__fnd, 'fnd'),
        (__padding, 'padding'),
    ]

class FileNodeListHeader(pstruct.type):
    class _uintMagic(u64):
        _default_ = 0xA4567AB1F5F7F4C4

    _fields_ = [
        (_uintMagic, 'uintMagic'),
        (u32, 'FileNodeListID'),
        (u32, 'nFragmentSequence'),
    ]

class FileNodeListFragment(pstruct.type):
    def __rgFileNodes(self):
        header, notloaded = self['header'].li, sum(type().a.size() for type, _ in self._fields_[-2:])
        try:
            reference = self.getparent(FileChunkReference)
        except Exception:
            expected = header.size() + notloaded
        else:
            expected = reference['cb'].li.int()
        finally:
            size = max(0, expected - sum([header.size(), notloaded]))
        return dyn.blockarray(FileNode, size)

    def __padding(self):
        notloaded = sum(type().a.size() for type, _ in self._fields_[-2:])
        loaded = sum(self[fld].li.size() for fld in ['header', 'rgFileNodes'])
        try:
            reference = self.getparent(FileChunkReference)
        except Exception:
            expected = loaded + notloaded
        else:
            expected = reference['cb'].li.int()
        finally:
            size = max(0, expected - sum([loaded, notloaded]))
        return dyn.block(size)
        
    class _footer(uint_default, u64):
        _default_ = 0x8BC215C38233BA4B

    _fields_ = [
       (FileNodeListHeader , 'header'),
       (__rgFileNodes, 'rgFileNodes'),
       (__padding, 'padding'),
       (FileChunkReference64x32, 'nextFragment'),   # FIXME: this should be pointing to a FileNodeListFragment
       (_footer, 'footer'),
    ]

### 2.3.2 Free Chunk List
class FreeChunkListFragment(pstruct.type):
    def __fcrFreeChunk(self):
        minimum = sum(self[fld].li.size() for fld in ['crc', 'fcrNextChunk'])
        try:
            reference = self.getparent(FileChunkReference)
        except Exception:
            expected = minimum
        else:
            expected = reference['cb'].li.int()
        finally:
            size = max(0, expected - minimum)
        return dyn.blockarray(FileChunkReference64, size)

    _fields_ = [
        (u32, 'crc'),
        (FileChunkReference64x32, 'fcrNextChunk'),  # FIXME: this should be pointing to a FreeChunkListFragment
        (__fcrFreeChunk, 'fcrFreeChunk'),
    ]

### 2.3.3 Transaction Log
class TransactionEntry(pstruct.type):
    _fields_ = [
        (u32, 'srcID'),
        (u32, 'TransactionEntrySwitch'),
    ]

class TransactionLogFragment(pstruct.type):
    class _sizeTable(parray.terminated):
        _object_ = TransactionEntry
        def isTerminator(self, entry):
            sourceId = entry['srcID'].li
            return sourceId.int() == 0x00000001

    _fields_ = [
        (_sizeTable, 'sizeTable'),
        (FileChunkReference64x32, 'nextFragment'),  # FIXME: this should be pointing to a TransactionLogFragment
    ]

### 2.6.1 ObjectSpaceObjectPropSet
class ObjectSpaceObjectStreamHeader(pbinary.flags):
    _fields_ = [
        (24, 'Count'),
        (6, 'Reserved'),
        (1, 'ExtendedStreamsPresent'),
        (1, 'OsidStreamNotPresent'),
    ]

class ObjectSpaceArrayOfCompactIDs(pbinary.struct):
    def __body(self):
        header = self['header']
        return dyn.clone(pbinary.array, _object_=CompactID, length=header['Count']),
    _fields_ = [
        (ObjectSpaceObjectStreamHeader, 'header'),
        (__body, 'body'),
    ]

class ObjectSpaceObjectStreamOfOIDs(ObjectSpaceArrayOfCompactIDs): pass
class ObjectSpaceObjectStreamOfOSIDs(ObjectSpaceArrayOfCompactIDs): pass
class ObjectSpaceObjectStreamOfContextIDs(ObjectSpaceArrayOfCompactIDs): pass

class PropertyID(pbinary.struct):
    class _type(pbinary.enum):
        length, _values_ = 5, [
            ('NoData', 0x1),                            # The property contains no data.
            ('Bool', 0x2),                              # The property is a Boolean value specified by boolValue.
            ('OneByteOfData', 0x3),                     # The property contains 1 byte of data in the PropertySet.rgData stream field.
            ('TwoBytesOfData', 0x4),                    # The property contains 2 bytes of data in the PropertySet.rgData stream field.
            ('FourBytesOfData', 0x5),                   # The property contains 4 bytes of data in the PropertySet.rgData stream field.
            ('EightBytesOfData', 0x6),                  # The property contains 8 bytes of data in the PropertySet.rgData stream field.
            ('FourBytesOfLengthFollowedByData', 0x7),   # The property contains a prtFourBytesOfLengthFollowedByData (section 2.6.8) in the PropertySet.rgData stream field.
            ('ObjectID', 0x8),                          # The property contains one CompactID (section 2.2.2) in the ObjectSpaceObjectPropSet.OIDs.body stream field.
            ('ArrayOfObjectIDs', 0x9),                  # The property contains an array of CompactID structures in the ObjectSpaceObjectPropSet.OIDs.body stream field. The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.
            ('ObjectSpaceID', 0xA),                     # The property contains one CompactID structure in the ObjectSpaceObjectPropSet.OSIDs.body stream field.
            ('ArrayOfObjectSpaceIDs', 0xB),             # The property contains an array of CompactID structures in the ObjectSpaceObjectPropSet.OSIDs.body stream field. The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.
            ('ContextID', 0xC),                         # The property contains one CompactID in the ObjectSpaceObjectPropSet.ContextIDs.body stream field.
            ('ArrayOfContextIDs', 0xD),                 # The property contains an array of CompactID structures in the ObjectSpaceObjectPropSet.ContextIDs.body stream field. The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.
            ('ArrayOfPropertyValues', 0x10),            # The property contains a prtArrayOfPropertyValues (section 2.6.9) structure in the PropertySet.rgData stream field.
            ('PropertySet', 0x11),                      # The property contains a child PropertySet (section 2.6.7) structure in the PropertySet.rgData stream field of the parent PropertySet.
        ]
    _fields_ = [
        (26, 'id'),
        (_type, 'type'),
        (1, 'boolValue'),
    ]

class PropertyType(ptype.definition):
    cache = {}
    class unknown(ptype.undefined): pass
    default = unknown

@PropertyType.define
class prtNoData(ptype.undefined):
    '''The property contains no data.'''
    type = 0x1
@PropertyType.define
class prtBool(ptype.undefined):
    '''The property is a Boolean value specified by boolValue.'''
    type = 0x2
@PropertyType.define
class prtOneByteOfData(u8):
    '''The property contains 1 byte of data in the PropertySet.rgData stream field.'''
    type = 0x3
@PropertyType.define
class prtTwoBytesOfData(u16):
    '''The property contains 2 bytes of data in the PropertySet.rgData stream field.'''
    type = 0x4
@PropertyType.define
class prtFourBytesOfData(u32):
    '''The property contains 4 bytes of data in the PropertySet.rgData stream field.'''
    type = 0x5
@PropertyType.define
class prtEightBytesOfData(u64):
    '''The property contains 8 bytes of data in the PropertySet.rgData stream field.'''
    type = 0x6
@PropertyType.define
class prtFourBytesOfLengthFollowedByData(pstruct.type):
    '''The property contains a prtFourBytesOfLengthFollowedByData (section 2.6.8) in the PropertySet.rgData stream field.'''
    type = 0x7
    _fields_ = [
        (u32, 'cb'),
        (lambda self: dyn.block(self['cb'].li.int()), 'Data'),
    ]
@PropertyType.define
class prtObjectID(ptype.undefined):
    type = 0x8
@PropertyType.define
class prtArrayOfObjectIDs(u32):
    '''The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.'''
    type = 0x9
@PropertyType.define
class prtObjectSpaceID(ptype.undefined):
    type = 0xa
@PropertyType.define
class prtArrayOfObjectSpaceIDs(u32):
    '''The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.'''
    type = 0xb
@PropertyType.define
class prtContextID(ptype.undefined):
    type = 0xc
@PropertyType.define
class prtArrayOfContextIDs(u32):
    '''The property contains an unsigned integer of size 4 bytes in the PropertySet.rgData stream field that specifies the number of CompactID structures this property contains.'''
    type = 0xd
@PropertyType.define
class prtArrayOfPropertyValues(pstruct.type):
    '''The property contains a prtArrayOfPropertyValues (section 2.6.9) structure in the PropertySet.rgData stream field.'''
    type = 0x10
    def __Data(self):
        propertyid = self['prid'].li
        prtype = PropertyType.lookup(propertyid['type'], ptype.undefined)
        return dyn.array(prtype, self['cProperties'].li.int())
    _fields_ = [
        (u32, 'cProperties'),
        (PropertyID, 'prid'),
        (__Data, 'Data'),
    ]
    
# XXX: this PropertySet can be nested according to the docs, but i haven't checked it or anything
@PropertyType.define
class PropertySet(pstruct.type):
    '''The property contains a child PropertySet (section 2.6.7) structure in the PropertySet.rgData stream field of the parent PropertySet.'''
    type = 0x11
    def __rgData(self):
        def _object_(self, properties=self['rgPrids'].li):
            '''use the PropertyType definition to look up each property type'''
            propertyid = properties[len(self.value)]
            return PropertyType.lookup(propertyid['type'], ptype.undefined)

        # return an array for each property that we loaded.
        return dyn.clone(parray.type, length=self['cProperties'].li.int(), _object_=_object_)

    _fields_ = [
        (u16, 'cProperties'),
        (lambda self: dyn.clone(pbinary.array, _object_=PropertyID, length=self['cProperties'].li.int()), 'rgPrids'),
        (__rgData, 'rgData'),
    ]

class ObjectSpaceObjectPropSet(pstruct.type):
    _fields_ = [
        (ObjectSpaceObjectStreamOfOIDs, 'OIDs'),
        (ObjectSpaceObjectStreamOfOSIDs, 'OSIDs'),
        (ObjectSpaceObjectStreamOfContextIDs, 'ContextIDs'),
        (PropertySet, 'body'),
        (dyn.padding(8), 'padding'),
    ]

### 2.3.4 Hashed Chunk List
@FileNodeType.define
class HashedChunkDescriptor2FND(pstruct.type):
    type = 0xc2
    _fields_ = [
       (dyn.clone(FileNodeChunkReference, _object_=ObjectSpaceObjectPropSet), 'BlobRef'),
       (u128, 'guidHash'),
    ]

### 2.5 File Node Types
@FileNodeType.define
class ObjectSpaceManifestRootFND(ptype.undefined):
    type = 0x4
@FileNodeType.define
class ObjectSpaceManifestListReferenceFND(ptype.undefined):
    type = 0x8
@FileNodeType.define
class ObjectSpaceManifestListStartFND(ptype.undefined):
    type = 0xC
@FileNodeType.define
class RevisionManifestListReferenceFND(ptype.undefined):
    type = 0x10
@FileNodeType.define
class RevisionManifestListStartFND(ptype.undefined):
    type = 0x14
@FileNodeType.define
class RevisionManifestStart4FND(ptype.undefined):
    type = 0x1B
@FileNodeType.define
class RevisionManifestEndFND(ptype.undefined):
    '''Specifies the end of a revision manifest '''
    type = 0x1C
@FileNodeType.define
class RevisionManifestStart6FND(ptype.undefined):
    type = 0x1E
@FileNodeType.define
class RevisionManifestStart7FND(ptype.undefined):
    type = 0x1F
@FileNodeType.define
class GlobalIdTableStartFNDX(ptype.undefined):
    type = 0x21
@FileNodeType.define
class GlobalIdTableStart2FND(ptype.undefined):
    '''Specifies the beginning of the global identification table '''
    type = 0x22
@FileNodeType.define
class GlobalIdTableEntryFNDX(ptype.undefined):
    type = 0x24
@FileNodeType.define
class GlobalIdTableEntry2FNDX(ptype.undefined):
    type = 0x25
@FileNodeType.define
class GlobalIdTableEntry3FNDX(ptype.undefined):
    type = 0x26
@FileNodeType.define
class GlobalIdTableEndFNDX(ptype.undefined):
    '''Specifies the end of the global identification table '''
    type = 0x28
@FileNodeType.define
class ObjectDeclarationWithRefCountFNDX(ptype.undefined):
    type = 0x2D
@FileNodeType.define
class ObjectDeclarationWithRefCount2FNDX(ptype.undefined):
    type = 0x2E
@FileNodeType.define
class ObjectRevisionWithRefCountFNDX(ptype.undefined):
    type = 0x41
@FileNodeType.define
class ObjectRevisionWithRefCount2FNDX(ptype.undefined):
    type = 0x42
@FileNodeType.define
class RootObjectReference2FNDX(ptype.undefined):
    type = 0x59
@FileNodeType.define
class RootObjectReference3FND(ptype.undefined):
    type = 0x5A
@FileNodeType.define
class RevisionRoleDeclarationFND(ptype.undefined):
    type = 0x5C
@FileNodeType.define
class RevisionRoleAndContextDeclarationFND(ptype.undefined):
    type = 0x5D
@FileNodeType.define
class ObjectDeclarationFileData3RefCountFND(ptype.undefined):
    type = 0x72
@FileNodeType.define
class ObjectDeclarationFileData3LargeRefCountFND(ptype.undefined):
    type = 0x73
@FileNodeType.define
class ObjectDataEncryptionKeyV2FNDX(ptype.undefined):
    type = 0x7C
@FileNodeType.define
class ObjectInfoDependencyOverridesFND(ptype.undefined):
    type = 0x84
@FileNodeType.define
class DataSignatureGroupDefinitionFND(ptype.undefined):
    type = 0x8C
@FileNodeType.define
class FileDataStoreListReferenceFND(ptype.undefined):
    type = 0x90
@FileNodeType.define
class FileDataStoreObjectReferenceFND(ptype.undefined):
    type = 0x94
@FileNodeType.define
class ObjectDeclaration2RefCountFND(ptype.undefined):
    type = 0xA4
@FileNodeType.define
class ObjectDeclaration2LargeRefCountFND(ptype.undefined):
    type = 0xA5
@FileNodeType.define
class ObjectGroupListReferenceFND(ptype.undefined):
    type = 0xB0
@FileNodeType.define
class ObjectGroupStartFND(ptype.undefined):
    type = 0xB4
@FileNodeType.define
class ObjectGroupEndFND(ptype.undefined):
    '''Specifies the end of an object group '''
    type = 0xB8
#@FileNodeType.define
#class HashedChunkDescriptor2FND(ptype.undefined):
#    type = 0xC2
@FileNodeType.define
class ReadOnlyObjectDeclaration2RefCountFND(ptype.undefined):
    type = 0xC4
@FileNodeType.define
class ReadOnlyObjectDeclaration2LargeRefCountFND(ptype.undefined):
    type = 0xC5
@FileNodeType.define
class ChunkTerminatorFND(ptype.undefined):
    '''Specifies the end of the stream of FileNode structures in a FileNodeListFragment structure.'''
    type = 0xFF

### 2.3 File Structure
class Header(pstruct.type):
    class _ffv(pint.enum, u32):
        _values_ = [
            ('.one', 0x0000002a),
            ('.onetoc2', 0x0000001b),
        ]
    _fields_ = [
        (GUID, 'guidFileType'),
        (GUID, 'guidFile'),
        (GUID, 'guidLegacyFileVersion'),
        (GUID, 'guidFileFormat'),
        (_ffv, 'ffvLastCodeThatWroteToThisFile'),
        (_ffv, 'ffvOldestCodeThatHasWrittenToThisFile'),
        (_ffv, 'ffvNewestCodeThatHasWrittenToThisFile'),
        (_ffv, 'ffvOldestCodeThatMayReadThisFile'),
        (FileChunkReference32, 'fcrLegacyFreeChunkList'),               # XXX: legacy
        (FileChunkReference32, 'fcrLegacyTransactionLog'),              # XXX: legacy
        (u32, 'cTransactionsInLog'),
        (u32, 'cbLegacyExpectedFileLength'),
        (u64, 'rgbPlaceholder'),
        (FileChunkReference32, 'fcrLegacyFileNodeListRoot'),            # XXX: legacy
        (u32, 'cbLegacyFreeSpaceInFreeChunkList'),
        (u8, 'fNeedsDefrag'),
        (u8, 'fRepairedFile'),
        (u8, 'fNeedsGarbageCollect'),
        (u8, 'fHasNoEmbeddedFileObjects'),
        (GUID, 'guidAncestor'),
        (u32, 'crcName'),
        (dyn.clone(FileChunkReference64x32, _object_=FileNodeListFragment), 'fcrHashedChunkList'),
        (dyn.clone(FileChunkReference64x32, _object_=TransactionLogFragment), 'fcrTransactionLog'),
        (dyn.clone(FileChunkReference64x32, _object_=FileNodeListFragment), 'fcrFileNodeListRoot'),
        (dyn.clone(FileChunkReference64x32, _object_=FreeChunkListFragment), 'fcrFreeChunkList'),
        (u64, 'cbExpectedFileLength'),
        (u64, 'cbFreeSpaceInFreeChunkList'),
        (GUID, 'guidFileVersion'),
        (u64, 'nFileVersionGeneration'),
        (GUID, 'guidDenyReadFileVersion'),
        (u32, 'grfDebugLogFlags'),
        (FileChunkReference64x32, 'fcrDebugLog'),                       # XXX: unknown
        (FileChunkReference64x32, 'fcrAllocVerificationFreeChunkList'), # XXX: unknown
        (u32, 'bnCreated'),
        (u32, 'bnLastWroteToThisFile'),
        (u32, 'bnOldestWritten'),
        (u32, 'bnNewestWritten'),
        (dyn.block(728), 'rgbReserved'),
    ]

class File(pstruct.type):
    def __legacy(self):
        header = self['header'].li
        expected = header['cbLegacyExpectedFileLength']
        return dyn.block(max(0, expected.int() - header.size()))
    def __data(self):
        header = self['header'].li
        expected, fields = header['cbExpectedFileLength'], ['header', 'legacy']
        return dyn.block(max(0, expected.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (Header, 'header'),
        (__legacy, 'legacy'),
        (__data, 'data'),
    ]

if __name__ == '__main__':
    import ptypes
    import importlib
    from office import onestore
    importlib.reload(onestore)
    from office.onestore import *
