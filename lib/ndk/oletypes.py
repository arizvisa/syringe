import ptypes
from ptypes import *

from .datatypes import *

## string primitives
class LengthPrefixedAnsiString(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.int()), 'String'),
    ]
    def str(self):
        return self['String'].li.str()

class LengthPrefixedUnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.clone(pstr.wstring, length=s['Length'].li.int()), 'String'),
    ]
    def str(self):
        return self['String'].li.str()

## PresentationObject Format
class PresentationObjectHeader(pstruct.type):
    def __ClassName(self):
        fmt = self['FormatID'].li.int()
        if fmt == 5:
            return LengthPrefixedAnsiString
        return pstr.string

    _fields_ = [
        (pint.uint32_t, 'OLEVersion'),
        (pint.uint32_t, 'FormatID'),
        (__ClassName, 'ClassName'),
    ]

class PresentationObjectType(ptype.definition):
    cache = {}

@PresentationObjectType.define(type='METAFILEPICT')
@PresentationObjectType.define(type='BITMAP')
@PresentationObjectType.define(type='DIB')
class StandardPresentationObject(pstruct.type):
    class BitmapPresentationSize(pint.uint32_t): pass
    class MetaFilePresentationSize(pint.uint32_t): pass

    def __SizeType(self):
        if self.type in {'BITMAP', 'DIB'}:
            return self.BitmapPresentationSize
        if self.type in {'METAFILEPICT'}:
            return self.MetaFilePresentationSize
        return pint.uint32_t

    _fields_ = [
        (__SizeType, 'Width'),
        (__SizeType, 'Height'),
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]

class ClipboardFormatHeader(pstruct.type): pass

@PresentationObjectType.define
class GenericPresentationObject(pstruct.type):
    type = None
    def __ClipboardObject(self):
        fmt = self['Header'].li['ClipboardFormat'].int()
        return ClipboardFormatType.withdefault(fmt, type=fmt)

    _fields_ = [
        (ClipboardFormatHeader, 'Header'),
        (__ClipboardObject, 'Object'),
    ]
PresentationObjectType.default = GenericPresentationObject

## Clipboard Format (not be set to 0)
ClipboardFormatHeader._fields_ = [
    (pint.uint32_t, 'ClipboardFormat')
]

class ClipboardFormatType(ptype.definition):
    cache = {}

@ClipboardFormatType.define
class StandardClipboardFormatPresentationObject(pstruct.type):
    type = None
    _fields_ = [
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]
ClipboardFormatType.default = StandardClipboardFormatPresentationObject

@ClipboardFormatType.define
class RegisteredClipboardFormatPresentationObject(pstruct.type):
    type = 0x00000000
    _fields_ = [
        (pint.uint32_t, 'StringFormatDataSize'),
        (lambda s: dyn.block(s['StringFormatDataSize'].li.int()), 'StringFormatData'),
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]

## Object
class ObjectHeader(pstruct.type):
    def __ClassName(self):
        fmt = self['FormatID'].li.int()
        if fmt == 5:
            return LengthPrefixedAnsiString
        return ptype.type
    _fields_ = [
        (pint.uint32_t, 'OLEVersion'),
        (pint.uint32_t, 'FormatID'),
        (__ClassName, 'ClassName'),
        (LengthPrefixedAnsiString, 'TopicName'),
        (LengthPrefixedAnsiString, 'ItemName'),
    ]

class ObjectType(ptype.definition):
    cache = {}

@ObjectType.define
class EmbeddedObject(pstruct.type):
    type = 0x00000002
    _fields_ = [
        (pint.uint32_t, 'NativeDataSize'),
        (lambda s: dyn.block(s['NativeDataSize'].li.int()), 'NativeData'),
    ]

@ObjectType.define
class LinkedObject(pstruct.type):
    type = 0x00000001
    _fields_ = [
        (LengthPrefixedAnsiString, 'NetworkName'),
        (pint.uint32_t, 'Reserved'),
        (pint.uint32_t, 'LinkUpdateOption'),
    ]

### OLE 1.0 Format Structures
class PresentationObject(pstruct.type):
    def __PresentationObject(self):
        fmt = self['Header'].li['FormatID'].int()
        if fmt != 0:
            clsname = self['Header']['ClassName'].str()
            return PresentationObjectType.withdefault(clsname, type=clsname)
        return ptype.type

    _fields_ = [
        (PresentationObjectHeader, 'Header'),
        (__PresentationObject, 'Object'),
    ]

# Ole v1.0
class Object(pstruct.type):
    def __Object(self):
        fmtid = self['Header'].li['FormatID'].int()
        return ObjectType.withdefault(fmtid, type=fmtid)

    _fields_ = [
        (ObjectHeader, 'Header'),
        (__Object, 'Object'),
        (PresentationObject, 'Presentation'),
    ]

### Essentially declarations for different object types
class CSmAllocator(VOID): pass
class CMessageCall(VOID): pass
class CAsyncCall(VOID): pass
class CClientCall(VOID): pass
class CObjServer(VOID): pass
class CObjectContext(VOID): pass
class CComApartment(VOID): pass
class IUnknown(VOID): pass
class CCtxCall(VOID): pass
class CPolicySet(VOID): pass
class CAptCallCtrl(VOID): pass
class CSrvCallState(VOID): pass
class IMessageFilter(VOID): pass
class IDataObject(VOID): pass
class CAsyncCall(VOID): pass
class CSurrogatedObjectList(VOID): pass
class ContextStackNode(VOID): pass

### Referenced by pstypes.TEB
class OLETLS_(pbinary.flags):
    _fields_ = [
        (13, 'unused'),
        (1, 'APTINITIALIZING'),         # Apartment Object is initializing
        (1, 'FIRSTNTAINIT'),            # First thread to attempt an NTA init
        (1, 'FIRSTMTAINIT'),            # First thread to attempt an MTA init
        (1, 'PENDINGUNINIT'),           # This thread has pending uninit
        (1, 'ALLOWCOINIT'),             # This thread allows inits
        (1, 'HOSTTHREAD'),              # This is a host thread
        (1, 'DISPATCHTHREAD'),          # This is a dispatch thread
        (1, 'INNEUTRALAPT'),            # This thread is in the NTA
        (1, 'DISABLE_EVENTLOGGER'),     # Prevent recursion in event logger
        (1, 'IMPERSONATING'),           # This thread is impersonating
        (1, 'MULTITHREADED'),           # This is an MTA apartment thread
        (1, 'APARTMENTTHREADED'),       # This is an STA apartment thread
        (1, 'DISABLE_OLE1DDE'),         # This thread can't use a DDE window.
        (1, 'THREADUNINITIALIZING'),    # This thread is in CoUninitialize.
        (1, 'WOWTHREAD'),               # This thread is a 16-bit WOW thread.
        (1, 'CHANNELTHREADINITIALZED'), # This channel has been init'd
        (1, 'INTHREADDETACH'),          # This is in thread detach. Needed due to NT's special thread detach rules.
        (1, 'UUIDINITIALIZED'),         # This Logical thread is init'd.
        (1, 'LOCALTID'),                # This TID is in the current process.
    ]

class CallEntry(pstruct.type):
    _fields_ = [
        (void_star, 'pNext'),       # ptr to next entry
        (void_star, 'pvObject'),    # Entry object
    ]

class LockEntry(pstruct.type, versioned):
    '''https://github.com/dotnet/diagnostics/blob/master/src/SOS/Strike/util.h#L143'''
    def __tagLockEntry(self):
        return P(LockEntry)
    def __align(self):
        return dyn.padding(8 if getattr(self, 'WIN64', False) else 4)
    _fields_ = [
        (__tagLockEntry, 'pNext'),  # next entry
        (__tagLockEntry, 'pPrev'),  # prev entry
        (DWORD, 'dwULockID'),
        (DWORD, 'dwLLockID'),       # owning lock
        (WORD, 'wReaderLevel'),     # reader nesting level
        (__align, 'padding(wReaderLevel)'),
    ]

class SOleTlsData(pstruct.type, versioned):
    '''https://github.com/dotnet/diagnostics/blob/main/src/SOS/Strike/ntinfo.h'''
    @pbinary.littleendian
    class _dwFlags(OLETLS_):
        pass

    def __align(self):
        return dyn.block(4 if getattr(self, 'WIN64', False) else 0)

    def __punkStateWx86(self):
        if getattr(self, 'WIN64', False):
            return P(IUnknown)
        return ptype.undefined

    _fields_ = [
        (PVOID, 'pvThreadBase'),                # per thread base pointer
        (P(CSmAllocator), 'pSmAllocator'),      # per thread docfile allocator
        (DWORD, 'dwApartmentID'),               # Per thread "process ID"
        (_dwFlags, 'dwFlags'),                  # see OLETLSFLAGS above
        (LONG, 'TlsMapIndex'),                  # index in the global TLSMap
        (__align, 'padding(TlsMapIndex)'),
        (P(PVOID), 'ppTlsSlot'),                # Back pointer to the thread tls slot
        (DWORD, 'cComInits'),                   # number of per-thread inits
        (DWORD, 'cOleInits'),                   # number of per-thread OLE inits
        (DWORD, 'cCalls'),                      # number of outstanding calls
        (__align, 'padding(cCalls)'),
        (P(CMessageCall), 'pCallInfo'),         # channel call info
        (P(CAsyncCall), 'pFreeAsyncCall'),      # ptr to available call object for this thread.
        (P(CClientCall), 'pFreeClientCall'),    # ptr to available call object for this thread.
        (P(CObjServer), 'pObjServer'),          # Activation Server Object for this apartment.
        (DWORD, 'dwTIDCaller'),                 # TID of current calling app
        (__align, 'padding(dwTIDCaller)'),
        (P(CObjectContext), 'pCurrentCtx'),     # Current context

        # XXX: everything after this is probably platform-specific
        (P(CObjectContext), 'pEmptyCtx'),               # Empty context
        (P(CObjectContext), 'pNativeCtx'),              # Native context
        (ULONGLONG, 'ContextId'),                       # Uniquely identifies the current context
        (P(CComApartment), 'pNativeApt'),               # Native apartment for the thread.
        (P(IUnknown), 'pCallContext'),                  # call context object
        (P(CCtxCall), 'pCtxCall'),                      # Context call object
        (P(CPolicySet), 'pPS'),                         # Policy set
        (PVOID, 'pvPendingCallsFront'),                 # Per Apt pending async calls
        (PVOID, 'pvPendingCallsBack'),
        (P(CAptCallCtrl), 'pCallCtrl'),                 # call control for RPC for this apartment
        (P(CSrvCallState), 'pTopSCS'),                  # top server-side callctrl state
        (P(IMessageFilter), 'pMsgFilter'),              # temp storage for App MsgFilter
        (HWND, 'hwndSTA'),                              # STA server window same as poxid->hServerSTA ...needed on Win95 before oxid registration
        (LONG, 'cORPCNestingLevel'),                    # call nesting level (DBG only)
        (DWORD, 'cDebugData'),                          # count of bytes of debug data in call
        (UUID, 'LogicalThreadId'),                      # current logical thread id
        (HANDLE, 'hThread'),                            # Thread handle used for cancel
        (HANDLE, 'hRevert'),                            # Token before first impersonate.
        (P(IUnknown), 'pAsyncRelease'),                 # Controlling unknown for async release
        (HWND, 'hwndDdeServer'),                        # Per thread Common DDE server
        (HWND, 'hwndDdeClient'),                        # Per thread Common DDE client
        (ULONG, 'cServeDdeObjects'),                    # non-zero if objects DDE should serve
        (__align, 'padding(cServeDdeObjects)'),
        (PVOID, 'pSTALSvrsFront'),                      # Chain of LServers registers in this thread if STA
        (HWND, 'hwndClip'),                             # Clipboard window
        (P(IDataObject), 'pDataObjClip'),               # Current Clipboard DataObject
        (DWORD, 'dwClipSeqNum'),                        # Clipboard Sequence # for the above DataObject
        (DWORD, 'fIsClipWrapper'),                      # Did we hand out the wrapper Clipboard DataObject?
        (P(IUnknown), 'punkState'),                     # Per thread "state" object
        (DWORD, 'cCallCancellation'),                   # count of CoEnableCallCancellation
        (DWORD, 'cAsyncSends'),                         # count of async sends outstanding
        (P(CAsyncCall), 'pAsyncCallList'),              # async calls outstanding
        (P(CSurrogatedObjectList), 'pSurrogateList'),   # Objects in the surrogate
        (LockEntry, 'lockEntry'),                       # Locks currently held by the thread
        (CallEntry, 'CallEntry'),                       # client-side call chain for this thread
        (__punkStateWx86, 'punkStateWx86'),             # Per thread "state" object for Wx86
        (void_star, 'pDragCursors'),                    # Per thread drag cursor table.
        (P(IUnknown), 'punkError'),                     # Per thread error object.
        (ULONG, 'cbErrorData'),                         # Maximum size of error data.
        (__align, 'padding(cbErrorData)'),
        (P(IUnknown), 'punkActiveXSafetyProvider'),
        (P(ContextStackNode), 'pContextStack'),
    ]

if __name__ == '__main__':
    pass
