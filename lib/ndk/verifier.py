import ptypes, functools
from ptypes import *

from .datatypes import *

class RTL_VERIFIER_THUNK_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (PCHAR, 'ThunkName'),
        (PVOID, 'ThunkOldAddress'),
        (PVOID, 'ThunkNewAddress'),
    ]

class RTL_VERIFIER_DLL_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (PWCHAR, 'DllName'),
        (DWORD, 'DllFlags'),
        (PVOID, 'DllAddress'),
        (PRTL_VERIFIER_THUNK_DESCRIPTOR, 'DllThunks'),
    ]

class RTL_VERIFIER_DLL_LOAD_CALLBACK(PVOID): pass
class RTL_VERIFIER_DLL_UNLOAD_CALLBACK(PVOID): pass
class RTL_VERIFIER_NTDLLHEAPFREE_CALLBACK(PVOID): pass

class RTL_VERIFIER_PROVIDER_DESCRIPTOR(pstruct.type):
    class _ProviderDlls(parray.terminated):
        _object_ = RTL_VERIFIER_DLL_DESCRIPTOR
        def isTerminator(self, item):
            bytes = item.serialize()
            return functools.reduce(operator.or_, bytearray(bytes), 0) == 0
    _fields_ = [
        (DWORD, 'Length'),
        #(PRTL_VERIFIER_DLL_DESCRIPTOR, 'ProviderDlls'),
        (P(_ProviderDlls), 'ProviderDlls'),
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
    def alloc(self, **fields):
        res = super(RTL_VERIFIER_PROVIDER_DESCRIPTOR, self).alloc(**fields):
        if 'Length' not in res:
            res['Length'].set(sum(res[fld].size() for fld in res))
        return res

