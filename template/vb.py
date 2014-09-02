# ripped from https://www.hex-rays.com/products/ida/support/freefiles/vb.idc
#   and http://vrt-blog.snort.org/2014/08/discovering-dynamically-loaded-api-in.html
import ptypes,ndk
from ptypes import *

class Str(pstr.string): pass
class Byte(pint.uint8_t): pass
class Word(pint.uint16_t): pass
class Dword(pint.uint32_t): pass
class UUID(ndk.GUID): pass
class PVOID(ndk.PVOID): pass
class CLSID(ndk.GUID): pass
class GUID(ndk.GUID): pass
class BSTR(pstruct.type):
    _fields_ = [
        (Dword, 'length'),
        (lambda s: A(Str, s['length'].l.int()), 'string'),
    ]
class Empty(ptype.undefined): pass
A = dyn.array 
P = dyn.pointer
C = dyn.clone
OD = lambda t: dyn.rpointer(t, object=lambda s: s.p, type=Dword)
OW = lambda t: dyn.rpointer(t, object=lambda s: s.p, type=Word)

###
class DesignerInfo(pstruct.type):
    _fields_ = [
        (UUID, "uuidDesigner"),             # CLSID of the Addin/Designer
	    (Dword, "cbStructSize"),            # Total Size of the next fields.
	    (BSTR, "bstrAddinRegKey"),        # Registry Key of the Addin
	    (BSTR, "bstrAddinName"),          # Friendly Name of the Addin
	    (BSTR, "bstrAddinDescription"),   # Description of Addin
	    (Dword, "dwLoadBehaviour"),         # CLSID of Object
	    (BSTR, "bstrSatelliteDll"),       # Satellite DLL, if specified
	    (BSTR, "bstrAdditionalRegKey"),   # Extra Registry Key, if specified
	    (Dword, "dwCommandLineSafe"),       # Specifies a GUI-less Addin if 1.
	]

class COMRegistrationInfo(pstruct.type):
    _fields_ = [
        (lambda s: O(COMRegistrationInfo), "bNextObject"),         # Offset to COM Interfaces Info
	    (OD(Str), "bObjectName"),         # Offset to Object Name
	    (OD(Str), "bObjectDescription"),  # Offset to Object Description
	    (Dword, "dwInstancing"),        # Instancing Mode
	    (Dword, "dwObjectId"),          # Current Object ID in the Project
	    (UUID, "uuidObject"),           # CLSID of Object
	    (Dword, "fIsInterface"),        # Specifies if the next CLSID is valid
	    (OD(CLSID), "bUuidObjectIFace"),    # Offset to CLSID of Object Interface
	    (OD(CLSID), "bUuidEventsIFace"),    # Offset to CLSID of Events Interface
	    (Dword, "fHasEvents"),          # Specifies if the CLSID above is valid
	    (Dword, "dwMiscStatus"),        # OLEMISC Flags (see MSDN docs)
	    (Byte, "fClassType"),           # Class Type
	    (Byte, "fObjectType"),          # Flag identifying the Object Type
	    (Word, "wToolboxBitmap32"),     # Control Bitmap ID in Toolbox
	    (Word, "wDefaultIcon"),         # Minimized Icon of Control Window
	    (Word, "fIsDesigner"),          # Specifies whether this is a Designer
	    (OD(DesignerInfo), "bDesignerData"),       # Offset to Designer Data
    ]

class COMRegistrationData(pstruct.type):
    _fields_ = [
        (P(COMRegistrationInfo), "bRegInfo"), # Offset to COM Interfaces Info
	    (OD(Str), "bSZProjectName"), # Offset to Project/Typelib Name
	    (OD(Str), "bSZHelpDirectory"), # Offset to Help Directory
	    (OD(Str), "bSZProjectDescription"), # Offset to Project Description
	    (UUID, "uuidProjectClsId"), # CLSID of Project/Typelib
	    (Dword, "dwTlbLcid"), # LCID of Type Library
	    (Word, "wUnknown"), # Might be something. Must check
	    (Word, "wTlbVerMajor"), # Typelib Major Version
	    (Word, "wTlbVerMinor"), # Typelib Minor Version
    ]

class ObjectTable(pstruct.type):
    _fields_ = [
 	    (PVOID, "lpHeapLink"),          # Unused after compilation, always 0.
	    (PVOID, "lpExecProj"),          # Pointer to VB Project Exec COM Object.
	    (P(lambda s: A(P(PrivateObjectDescriptor), s.getparent(ptype.pointer_t).p['dwCompiledObjects'].l.int())), "lpProjectInfo2"),      # Secondary Project Information.
	    (Dword, "dwReserved"),          # Always set to -1 after compiling. Unused
	    (Dword, "dwNull"),              # Not used in compiled mode.
	    (PVOID, "lpProjectObject"),     # Pointer to in-memory Project Data.
	    (UUID, "uuidObject"),           # GUID of the Object Table.
	    (Word, "fCompileState"),        # Internal flag used during compilation.
	    (Word, "dwTotalObjects"),       # Total objects present in Project.
	    (Word, "dwCompiledObjects"),    # Equal to above after compiling.
	    (Word, "dwObjectsInUse"),       # Usually equal to above after compile.
	    (lambda s: P(A(PublicObjectDescriptor, s['dwTotalObjects'].l.int())), "lpObjectArray"),  # Pointer to Object Descriptors
	    (Dword, "fIdeFlag"),            # Flag/Pointer used in IDE only.
	    (PVOID, "lpIdeData"),           # Flag/Pointer used in IDE only.
	    (PVOID, "lpIdeData2"),          # Flag/Pointer used in IDE only.
	    (P(Str), "lpszProjectName"),    # Pointer to Project Name.
	    (Dword, "dwLcid"),              # LCID of Project.
	    (Dword, "dwLcid2"),             # Alternate LCID of Project.
	    (PVOID, "lpIdeData3"),          # Flag/Pointer used in IDE only.
	    (Dword, "dwIdentifier"),        # Template Version of Structure.
    ]

class ProjectInformation(pstruct.type):
    _fields_ = [
        (Dword, "dwVersion"),       # 5.00 in Hex (0x1F4). Version.
	    (P(ObjectTable), "lpObjectTable"),   # Pointer to the Object Table
	    (Dword, "dwNull"),          # Unused value after compilation.
	    (PVOID, "lpCodeStart"),     # Points to start of code. Unused.
	    (PVOID, "lpCodeEnd"),       # Points to end of code. Unused.
	    (Dword, "dwDataSize"),      # Size of VB Object Structures. Unused.
	    (PVOID, "lpThreadSpace"),   # Pointer to Pointer to Thread Object.
	    (PVOID, "lpVbaSeh"),        # Pointer to VBA Exception Handler
	    (PVOID, "lpNativeCode"),    # Pointer to .DATA section.
	    (dyn.clone(Str, length=0x210), "szPathInformation"), # Contains Path and ID string. < SP6
	    (P(lambda s: A(Dword, s.getparent(ptype.pointer_t).p['dwExternalCount'].l.int())), "lpExternalTable"), # Pointer to External Table.
	    (Dword, "dwExternalCount"), # Objects in the External Table.
    ]

class PrivateObjectDescriptor(pstruct.type):
    _fields_ = [
 	    (PVOID, "lpHeapLink"), # Unused after compilation, always 0.
	    (P(lambda s: ObjectInformation), "lpObjectInfo"), # Pointer to the Object Info for this Object.
	    (Dword, "dwReserved"), # Always set to -1 after compiling.
	    (Dword, "dwIdeData"), # [3] Not valid after compilation.
	    (Dword, "v_10"),
	    (Dword, "v_14"),
	    (PVOID, "lpObjectList"), # Points to the Parent Structure (Array)
	    (Dword, "dwIdeData2"), # Not valid after compilation.
	    (PVOID, "lpObjectList2"), # [3] Points to the Parent Structure (Array).
	    (Dword, "v_24"),
	    (Dword, "v_28"),
	    (Dword, "dwIdeData3"), # [3] Not valid after compilation.
	    (Dword, "v_30"),
	    (Dword, "v_34"),
	    (Dword, "dwObjectType"), # Type of the Object described.
	    (Dword, "dwIdentifier"), # Template Version of Structure.
    ]

class PublicObjectDescriptor(pstruct.type):
    _fields_ = [
        (P(lambda s: ObjectInformation), "lpObjectInfo"), # Pointer to the Object Info for this Object.
	    (Dword, "dwReserved"), # Always set to -1 after compiling.
	    (PVOID, "lpPublicBytes"), # Pointer to Public Variable Size integers.
	    (PVOID, "lpStaticBytes"), # Pointer to Static Variable Size integers.
	    (PVOID, "lpModulePublic"), # Pointer to Public Variables in DATA section
	    (PVOID, "lpModuleStatic"), # Pointer to Static Variables in DATA section
	    (P(Str), "lpszObjectName"), # Name of the Object.
	    (Dword, "dwMethodCount"), # Number of Methods in Object.
	    (lambda s: P(A(P(STR), s['dwMethodCount'].l.int)()), "lpMethodNames"), # If present, pointer to Method names array.
	    (OD(Dword), "bStaticVars"), # Offset to where to copy Static Variables.
	    (Dword, "fObjectType"), # Flags defining the Object Type.
	    (Dword, "dwNull"), # Not valid after compilation.
	]

class ObjectInformation(pstruct.type):
    _fields_ = [
        (Word, "wRefCount"), # Always 1 after compilation.
	    (Word, "wObjectIndex"), # Index of this Object.
	    (P(ObjectTable), "lpObjectTable"), # Pointer to the Object Table
	    (Dword, "lpIdeData"), # Zero after compilation. Used in IDE only.
	    (P(PrivateObjectDescriptor), "lpPrivateObject"), # Pointer to Private Object Descriptor.
	    (Dword, "dwReserved"), # Always -1 after compilation.
	    (Dword, "dwNull"), # Unused.
	    (P(PublicObjectDescriptor), "lpObject"), # Back-Pointer to Public Object Descriptor.
	    (P(ProjectInformation), "lpProjectData"), # Pointer to in-memory Project Object.
	    (Word, "wMethodCount"), # Number of Methods
	    (Word, "wMethodCount2"), # Zeroed out after compilation. IDE only.
	    (lambda s: P(A(PVOID, s['wMethodCount'].l.int())), "lpMethods"), # Pointer to Array of Methods.
	    (Word, "wConstants"), # Number of Constants in Constant Pool.
	    (Word, "wMaxConstants"), # Constants to allocate in Constant Pool.
	    (PVOID, "lpIdeData2"), # Valid in IDE only.
	    (PVOID, "lpIdeData3"), # Valid in IDE only.
	    (PVOID, "lpConstants"), # Pointer to Constants Pool.
    ]

class OptionalObjectInformation(pstruct.type):
    _fields_ = [
        (Dword, "dwObjectGuids"), # How many GUIDs to Register. 2 = Designer
	    (lambda s: P(A(GUID, s['dwObjectGuids'].l.int())), "lpObjectGuid"), # Unique GUID of the Object *VERIFY*
	    (Dword, "dwNull"), # Unused.
	    (Dword, "lpuuidObjectTypes"), # Pointer to Array of Object Interface GUIDs
	    (Dword, "dwObjectTypeGuids"), # How many GUIDs in the Array above.
	    (P(lambda s: A(ControlInformation, s.p.p['dwControlCount'].l.int())), "lpControls2"), # Usually the same as lpControls.
	    (Dword, "dwNull2"), # Unused.
	    (P(lambda s: A(GUID, s.p.p['dwObjectGuids'].l.int())), "lpObjectGuid2"), # Pointer to Array of Object GUIDs.
	    (Dword, "dwControlCount"), # Number of Controls in array below.
	    (lambda s: P(A(ControlInformation, s['dwControlCount'].l.int())), "lpControls"), # Pointer to Controls Array.
	    (Word, "wEventCount"), # Number of Events in Event Array.
	    (Word, "wPCodeCount"), # Number of P-Codes used by this Object.
	    (OW(PVOID), "bWInitializeEvent"), # Offset to Initialize Event from Event Table.
	    (OW(PVOID), "bWTerminateEvent"), # Offset to Terminate Event in Event Table.
	    (lambda s: P(EventHandlerTable, s['wEventCount'].l.int()), "lpEvents"), # Pointer to Events Array.
	    (PVOID, "lpBasicClassObject"), # Pointer to in-memory Class Objects.
	    (Dword, "dwNull3"), # Unused.
	    (PVOID, "lpIdeData"), # Only valid in IDE.
    ]

class EventHandlerTable(pstruct.type):
    _fields_ = [
	    (Dword, "dwNull"),          # Always Null.
	    (PVOID, "lpControlType"),   # Pointer to control type.
	    (PVOID, "lpObjectInfo"),    # Pointer to object info.
	    (Dword, "lpQuery"),         # Jump to EVENT_SINK_QueryInterface.
	    (Dword, "lpAddRef"),        # Jump to EVENT_SINK_AddRef.
	    (Dword, "lpRelease"),       # Jump to EVENT_SINK_Release.
        (lambda s: A(EventHandlerType, s.getparent(OptionalObjectInformation)['wEventCount'].l.int()), 'Events'),
    ]

class EventHandlerType(ptype.pointer_t):
    class _object_(Dword, pint.enum):
        _values_ = [
            (0, 'lpButton_Click'),     # Ptr to Button Click Event Code.");
            (1, 'lpButton_DragDrop'),  # Ptr to Button DragDrop Event Code.");
            (2, 'lpButton_DragOver'),  # Ptr to Button DragOver Event Code.");
            (3, 'lpButton_GotFocus'),  # Ptr to Button GotFocus Event Code.");
            (4, 'lpButton_KeyDown'),   # Ptr to Button KeyDown Event Code.");
            (5, 'lpButton_KeyPress'),  # Ptr to Button KeyPress Event Code.");
            (6, 'lpButton_KeyUp'),     # Ptr to Button KeyUp Event Code.");
            (7, 'lpButton_LostFocus'), # Ptr to Button LostFocus Event Code.");
            (8, 'lpButton_MouseDown'), # Ptr to Button MouseDown Event Code.");
            (9, 'lpButton_MouseMove'), # Ptr to Button MouseMove Event Code.");
            (10, 'lpButton_MouseUp'),   # Ptr to Button MouseUp Event Code.");
            (11, 'lpButton_OLEDragOver'),   # Ptr to Button OLEDragOver Event Code.");
            (12, 'lpButton_OLEDragDrop'),   # Ptr to Button OLEDragDrop Event Code.");
            (13, 'lpButton_OLEGiveFeedback'),   # Ptr to Button OLEGiveFeedback Event Code.");
            (14, 'lpButton_OLEStartDrag'),  # Ptr to Button OLEStartDrag Event Code.");
            (15, 'lpButton_OLESetData'),# Ptr to Button OLESetData Event Code.");
            (16, 'lpButton_OLECompleteDrag'),   # Ptr to Button OLECompleteDrag Event Code.");
        ]

class Header(pstruct.type):
    _fields_ = [
        (P(Str), 'szVbMagic'),      # "VB5!" String    
        (Word, 'wRuntimeBuild'),    # Build of the VB6 Runtime
        (C(Str, length=0xe), 'szLangDll'),        # Language Extension DLL
	    (C(Str, length=0xe), 'szSecLangDll'),      # 2nd Language Extension DLL
	    (Word, 'wRuntimeRevision'), # Internal Runtime Revision
	    (Dword, 'dwLCID'),          # LCID of Language DLL
	    (Dword, 'dwSecLCID'),       # LCID of 2nd Language DLL
	    (PVOID, 'lpSubMain'),       # Pointer to Sub Main Code
	    (P(ProjectInformation), 'lpProjectData'),   # Pointer to Project Data
	    (Dword, 'fMdlIntCtls'),     # VB Control Flags for IDs < 32
	    (Dword, 'fMdlIntCtls2'),    # VB Control Flags for IDs > 32
	    (Dword, 'dwThreadFlags'),   # Threading Mode
	    (Dword, 'dwThreadCount'),   # Threads to support in pool
	    (Word, 'wFormCount'),       # Number of forms present
	    (Word, 'wExternalCount'),   # Number of external controls
	    (Dword, 'dwThunkCount'),    # Number of thunks to create
	    (PVOID, 'lpGuiTable'),      # Pointer to GUI Table
	    (PVOID, 'lpExternalTable'), # Pointer to External Table
	    (P(COMRegistrationData), 'lpComRegisterData'),       # Pointer to COM Information
	    (OD(Str), 'bSZProjectDescription'),      # Offset to Project Description
	    (OD(Str), 'bSZProjectExeName'),          # Offset to Project EXE Name
	    (OD(Str), 'bSZProjectHelpFile'),         # Offset to Project Help File
	    (OD(Str), 'bSZProjectName'),             # Offset to Project Name
    ]
###
class DynamicHandles(pstruct.type):
    _fields_ = [
        (ndk.DWORD, 'dwUnknown'),
        (ndk.HANDLE, 'hModule'),
        (ndk.PVOID, 'fnAddress'),
    ]

class DllFunctionCallStruct(pstruct.type):
    _fields_ = [
        (dyn.pointer(ndk.STRING), 'lpDllName'),
        (dyn.pointer(ndk.STRING), 'lpExportName'),
        (ndk.CHAR, 'sizeOfExportName'),
        (DynamicHandles, 'sHandleData'),
    ]
