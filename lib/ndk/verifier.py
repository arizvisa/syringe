import ptypes
from ptypes import *

from .dtyp import *

class _RTL_VERIFIER_THUNK_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (PCHAR, 'ThunkName'),
        (PVOID, 'ThunkOldAddress'),
        (PVOID, 'ThunkNewAddress'),
    ]

class _RTL_VERIFIER_DLL_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (PWCHAR, 'DllName'),
        (DWORD, 'DllFlags'),
        (PVOID, 'DllAddress'),
        (PRTL_VERIFIER_THUNK_DESCRIPTOR, 'DllThunks'),
    ]

class _RTL_VERIFIER_PROVIDER_DESCRIPTOR(pstruct.type):
    class RTL_VERIFIER_DLL_LOAD_CALLBACK(PVOID): pass
    class RTL_VERIFIER_DLL_UNLOAD_CALLBACK(PVOID): pass
    class RTL_VERIFIER_NTDLLHEAPFREE_CALLBACK(PVOID): pass

    _fields_ = [
        (DWORD, 'Length'),
        (PRTL_VERIFIER_DLL_DESCRIPTOR, 'ProviderDlls'),
        (RTL_VERIFIER_DLL_LOAD_CALLBACK, 'ProviderDllLoadCallback'),
        (RTL_VERIFIER_DLL_UNLOAD_CALLBACK, 'ProviderDllUnloadCallback'),
        (PWSTR, 'VerifierImage'),
        (DWORD, 'VerifierFlags'),
        (DWORD, 'VerifierDebug'),
        (PVOID, 'RtlpGetStackTraceAddress'),
        (PVOID, 'RtlpDebugPageHeapCreate'),
        (PVOID, 'RtlpDebugPageHeapDestroy'),
        (RTL_VERIFIER_NTDLLHEAPFREE_CALLBACK, 'ProviderNtdllHeapFreeCallback'),
    ]

