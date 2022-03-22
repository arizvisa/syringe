import logging, builtins

import ptypes
from ptypes import *

from . import exception
from .datatypes import *

NT_SUCCESS = lambda Status: ((builtins.int(Status)) >= 0)
NT_INFORMATION = lambda Status: (((builtins.int(Status)) >> 30) == 1)
NT_WARNING = lambda Status: (((builtins.int(Status)) >> 30) == 2)
NT_ERROR = lambda Status: (((builtins.int(Status)) >> 30) == 3)

MINCHAR = 0x80
MAXCHAR = 0x7f
MINSHORT = 0x8000
MAXSHORT = 0x7fff
MINLONG = 0x80000000
MAXLONG = 0x7fffffff
MAXUCHAR = 0xff
MAXUSHORT = 0xffff
MAXULONG = 0xffffffff

CSR_MAKE_OPCODE = lambda s, m: ((s) << 16) | (m)
CSR_API_ID_FROM_OPCODE = lambda n: (builtins.int(builtins.int(n)))
CSR_SERVER_ID_FROM_OPCODE = lambda n: builtins.int((n) >> 16)

class CINT(pint.uint32_t): pass
class PCSZ(P(pstr.char_t)): pass
class CLONG(ULONG): pass
class CSHORT(short): pass
class PCSHORT(P(CSHORT)): pass
class PHYSICAL_ADDRESS(LARGE_INTEGER): pass
class PPHYSICAL_ADDRESS(P(PHYSICAL_ADDRESS)): pass
class KPRIORITY(LONG): pass
class KAFFINITY(LONG): pass
class NTSTATUS(LONG): pass
class PNTSTATUS(P(NTSTATUS)): pass

class PSTR(pstr.string): pass
class WSTR(pstr.wstring): pass

class CLIENT_ID(pstruct.type, versioned):
    _fields_ = [
        (HANDLE, 'UniqueProcess'),
        (HANDLE, 'UniqueThread'),
    ]

class UNICODE_STRING(pstruct.type, versioned):
    def __Padding(self):
        length = 4 if getattr(self, 'WIN64', False) else 0
        return dyn.block(length)

    def __Buffer(self):
        length = self['Length'].li
        t = dyn.clone(WSTR, length=length.int() // 2)
        return P(t)

    _fields_ = [
        (USHORT, 'Length'),
        (USHORT, 'MaximumLength'),
#        (PWSTR, 'Buffer'),
#        (lambda self: P(dyn.clone(WSTR, length=self['MaximumLength'].li.int())), 'Buffer')
        (__Padding, 'Padding'),
        (__Buffer, 'Buffer')
    ]

    def get(self):
        logging.warning('UNICODE_STRING.get() has been deprecated in favor of .str()')
        return self.str()

    def str(self):
        return None if self['Buffer'].int() == 0 else self['Buffer'].d.li.str()[:self['Length'].int()]

    def summary(self):
        return 'Length={:x} MaximumLength={:x} Buffer={!r}'.format(self['Length'].int(), self['MaximumLength'].int(), self.str())

    def alloc(self, **fields):
        res = super(UNICODE_STRING, self).alloc(**fields)
        if not res['Buffer'].d.initializedQ():
            return res
        if 'Length' not in fields:
            res['Length'].set(res['Buffer'].d.size())
        if 'MaximumLength' not in fields:
            res['MaximumLength'].set(res['Length'].int())
        return res

class PUNICODE_STRING(P(UNICODE_STRING)): pass

class STRING(pstruct.type):
    def __Padding(self):
        length = 4 if getattr(self, 'WIN64', False) else 0
        return dyn.block(length)

    def __Buffer(self):
        length = self['Length'].li
        t = dyn.clone(PSTR, length=length.int())
        return P(t)

    _fields_ = [
        (USHORT, 'Length'),
        (USHORT, 'MaximumLength'),
        (__Padding, 'Padding'),
        (__Buffer, 'Buffer')
    ]

    def get(self):
        logging.warning('STRING.get() has been deprecated in favor of .str()')
        return self.str()

    def str(self):
        return None if self['Buffer'].int() == 0 else self['Buffer'].d.li.str()[:self['Length'].int()]

    def summary(self):
        return 'Length={:x} MaximumLength={:x} Buffer={!r}'.format(self['Length'].int(), self['MaximumLength'].int(), self.str())

    def alloc(self, **fields):
        res = super(UNICODE_STRING, self).alloc(**fields)
        if not res['Buffer'].d.initializedQ():
            return res
        if 'Length' not in fields:
            res['Length'].set(res['Buffer'].d.size())
        if 'MaximumLength' not in fields:
            res['MaximumLength'].set(res['Length'].int())
        return res

class PSTRING(P(STRING)): pass

class ANSI_STRING(STRING): pass
class PANSI_STRING(PSTRING): pass
class OEM_STRING(STRING): pass
class POEM_STRING(PSTRING): pass

class EX_PUSH_LOCK(pbinary.struct):
    _fields_ = [
        (1, 'Locked'),
        (1, 'Waiting'),
        (1, 'Waking'),
        (1, 'MultipleShared'),
        (28, 'Shared'),
    ]

class OBJECT_ATTRIBUTES(pstruct.type, versioned):
    _fields_ = [
        (ULONG, 'Length'),
        (HANDLE, 'RootDirectory'),
        (PUNICODE_STRING, 'ObjectName'),
        (ULONG, 'Attributes'),
        (PVOID, 'SecurityDescriptor'),
        (PVOID, 'SecurityQualityOfService'),
    ]

class PHYSICAL_MEMORY_RANGE(pstruct.type):
    _fields_ = [
        (PHYSICAL_ADDRESS, 'BaseAddress'),
        (LARGE_INTEGER, 'NumberOfBytes'),
    ]

WER_MAX_PREFERRED_MODULES = 128
WER_MAX_PREFERRED_MODULES_BUFFER = 256

class WER_FAULT_REPORTING_(pbinary.flags):
    _fields_ = [
        (22, 'unused'),
        (1, 'DURABLE'),                         # Mark the process as requiring flushing of its report store.
        (1, 'CRITICAL'),                        # Mark the process as critical.
        (1, 'DISABLE_SNAPSHOT_HANG'),           # Disable snapshots for hang reporting.
        (1, 'DISABLE_SNAPSHOT_CRASH'),          # Disable snapshots for crash/exception reporting.
        (1, 'FLAG_NO_HEAP_ON_QUEUE'),           # Do not add heap dumps when queueing reports for the process
        (1, 'NO_UI'),                           # Fault reporting UI should not be shown.
        (1, 'ALWAYS_SHOW_UI'),                  # Fault reporting UI should always be shown. This is only applicable for interactive processes
        (1, 'FLAG_QUEUE_UPLOAD'),               # Queue critical reports for this process and upload from the queue
        (1, 'FLAG_DISABLE_THREAD_SUSPENSION'),  # Do not suspend the process before error reporting
        (1, 'FLAG_QUEUE'),                      # Queue critical reports for this process
        (1, 'FLAG_NOHEAP'),                     # Do not add heap dumps for reports for the process
    ]

class WER_REPORT_UI(pint.enum):
    _values_ = [
        ('WerUIAdditionalDataDlgHeader', 1),
        ('WerUIIconFilePath', 2),
        ('WerUIConsentDlgHeader', 3),
        ('WerUIConsentDlgBody', 4),
        ('WerUIOnlineSolutionCheckText', 5),
        ('WerUIOfflineSolutionCheckText', 6),
        ('WerUICloseText', 7),
        ('WerUICloseDlgHeader', 8),
        ('WerUICloseDlgBody', 9),
        ('WerUICloseDlgButtonText', 10),
    ]

class WER_REGISTER_FILE_TYPE(pint.enum):
    _values_ = [
        ('WerRegFileTypeUserDocument', 1),
        ('WerRegFileTypeOther', 2),
    ]

class WER_FILE_TYPE(pint.enum):
    _values_ = [
       ('WerFileTypeMicrodump', 1),
       ('WerFileTypeMinidump', 2),
       ('WerFileTypeHeapdump', 3),
       ('WerFileTypeUserDocument', 4),
       ('WerFileTypeOther', 5),
       ('WerFileTypeTriagedump', 6),
       ('WerFileTypeCustomDump', 7),
       ('WerFileTypeAuxiliaryDump', 8),
       ('WerFileTypeEtlTrace', 9),
    ]

class WER_SUBMIT_RESULT(pint.enum):
    _values_ = [
       ('WerReportQueued', 1),
       ('WerReportUploaded', 2),
       ('WerReportDebug', 3),
       ('WerReportFailed', 4),
       ('WerDisabled', 5),
       ('WerReportCancelled', 6),
       ('WerDisabledQueue', 7),
       ('WerReportAsync', 8),
       ('WerCustomAction', 9),
       ('WerThrottled', 10),
       ('WerReportUploadedCab', 11),
       ('WerStorageLocationNotFound', 12),
    ]

class _WER_REPORT_TYPE(pint.enum):
    _values_ = [
       ('WerReportNonCritical', 0),
       ('WerReportCritical', 1),
       ('WerReportApplicationCrash', 2),
       ('WerReportApplicationHang', 3),
       ('WerReportKernel', 4),
    ]

class WER_FILE_(pbinary.flags):
    _fields_ = [
        (16, 'reserved'),
        (13, 'unused'),
        (1, 'COMPRESSED'),          # This file has been compressed using SQS
        (1, 'ANONYMOUS_DATA'),      # This file does not contain any PII
        (1, 'DELETE_WHEN_DONE'),    # Delete the file once WER is done
    ]

class WER_SUBMIT_(pbinary.flags):
    _fields_ = [
        (1, 'BYPASS_NETWORK_COST_THROTTLING'),  # Bypass network-related throttling (when on restricted networks)
        (1, 'BYPASS_POWER_THROTTLING'),         # Bypass power-related throttling (when on battery)
        (1, 'REPORT_MACHINE_ID'),               # Always send the machine ID, regardless of the consent the report was submitted with
        (1, 'ARCHIVE_PARAMETERS_ONLY'),         # Archive only the parameters; the cab is discarded
        (1, 'BYPASS_DATA_THROTTLING'),          # Bypass data throttling for the report
        (1, 'OUTOFPROCESS_ASYNC'),              # Force the report to go out of process and do not wait for it to finish
        (1, 'START_MINIMIZED'),                 # The initial reporting UI is minimized and will flash
        (1, 'NO_ARCHIVE'),                      # Do not archive the report
        (1, 'NO_QUEUE'),                        # Do not queue the report
        (1, 'NO_CLOSE_UI'),                     # Do not show the close dialog for the critical report
        (1, 'OUTOFPROCESS'),                    # Force the report to go out of process
        (1, 'ADD_REGISTERED_DATA'),             # Add registered data to the WER report
        (1, 'SHOW_DEBUG'),                      # show the debug button
        (1, 'QUEUE'),                           # report directly to queue
        (1, 'HONOR_RESTART'),                   # show application restart option
        (1, 'HONOR_RECOVERY'),                  # show recovery option
    ]

class WER_REPORT_INFORMATION_V3(pstruct.type):
    _fields_ = [
        (DWORD, 'dwSize'),
        (HANDLE, 'hProcess'),
        (dyn.clone(pstr.wstring, length=64), 'wzConsentKey'),
        (dyn.clone(pstr.wstring, length=128), 'wzFriendlyEventName'),
        (dyn.clone(pstr.wstring, length=128), 'wzApplicationName'),
        (dyn.clone(pstr.wstring, length=MAX_PATH), 'wzApplicationPath'),
        (dyn.clone(pstr.wstring, length=512), 'wzDescription'),
        (HWND, 'hwndParent'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespacePartner'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespaceGroup'),
    ]

class WER_DUMP_CUSTOM_OPTIONS(pstruct.type):
    _fields_ = [
        (DWORD, 'dwSize'),
        (DWORD, 'dwMask'),
        (DWORD, 'dwDumpFlags'),
        (BOOL, 'bOnlyThisThread'),
        (DWORD, 'dwExceptionThreadFlags'),
        (DWORD, 'dwOtherThreadFlags'),
        (DWORD, 'dwExceptionThreadExFlags'),
        (DWORD, 'dwOtherThreadExFlags'),
        (DWORD, 'dwPreferredModuleFlags'),
        (DWORD, 'dwOtherModuleFlags'),
        (dyn.clone(pstr.wstring, length=WER_MAX_PREFERRED_MODULES_BUFFER), 'wzPreferredModuleList'),
    ]

class WER_DUMP_CUSTOM_OPTIONS_V2(pstruct.type):
    _fields_ = [
        (DWORD, 'dwSize'),
        (DWORD, 'dwMask'),
        (DWORD, 'dwDumpFlags'),
        (BOOL, 'bOnlyThisThread'),
        (DWORD, 'dwExceptionThreadFlags'),
        (DWORD, 'dwOtherThreadFlags'),
        (DWORD, 'dwExceptionThreadExFlags'),
        (DWORD, 'dwOtherThreadExFlags'),
        (DWORD, 'dwPreferredModuleFlags'),
        (DWORD, 'dwOtherModuleFlags'),
        (dyn.clone(pstr.wstring, length=WER_MAX_PREFERRED_MODULES_BUFFER), 'wzPreferredModuleList'),
        (DWORD, 'dwPreferredModuleResetFlags'),
        (DWORD, 'dwOtherModuleResetFlags'),
    ]

class WER_REPORT_INFORMATION_V4(pstruct.type):
    _fields_ = [
        (DWORD, 'dwSize'),
        (HANDLE, 'hProcess'),
        (dyn.clone(pstr.wstring, length=64), 'wzConsentKey'),
        (dyn.clone(pstr.wstring, length=128), 'wzFriendlyEventName'),
        (dyn.clone(pstr.wstring, length=128), 'wzApplicationName'),
        (dyn.clone(pstr.wstring, length=MAX_PATH), 'wzApplicationPath'),
        (dyn.clone(pstr.wstring, length=512), 'wzDescription'),
        (HWND, 'hwndParent'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespacePartner'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespaceGroup'),
        (dyn.array(BYTE, 16), 'rgbApplicationIdentity'),
        (HANDLE, 'hSnapshot'),
        (HANDLE, 'hDeleteFilesImpersonationToken'),
    ]

class WER_REPORT_INFORMATION(pstruct.type):
    class _submitResultMax(WER_SUBMIT_RESULT, DWORD):
        pass
    _fields_ = [
        (DWORD, 'dwSize'),
        (HANDLE, 'hProcess'),
        (dyn.clone(pstr.wstring, length=64), 'wzConsentKey'),
        (dyn.clone(pstr.wstring, length=128), 'wzFriendlyEventName'),
        (dyn.clone(pstr.wstring, length=128), 'wzApplicationName'),
        (dyn.clone(pstr.wstring, length=MAX_PATH), 'wzApplicationPath'),
        (dyn.clone(pstr.wstring, length=512), 'wzDescription'),
        (HWND, 'hwndParent'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespacePartner'),
        (dyn.clone(pstr.wstring, length=64), 'wzNamespaceGroup'),
        (dyn.array(BYTE, 16), 'rgbApplicationIdentity'),
        (HANDLE, 'hSnapshot'),
        (HANDLE, 'hDeleteFilesImpersonationToken'),
        (_submitResultMax, 'submitResultMax'),
    ]

class WER_DUMP_CUSTOM_OPTIONS_V3(pstruct.type):
    _fields_ = [
        (DWORD, 'dwSize'),
        (DWORD, 'dwMask'),
        (DWORD, 'dwDumpFlags'),
        (BOOL, 'bOnlyThisThread'),
        (DWORD, 'dwExceptionThreadFlags'),
        (DWORD, 'dwOtherThreadFlags'),
        (DWORD, 'dwExceptionThreadExFlags'),
        (DWORD, 'dwOtherThreadExFlags'),
        (DWORD, 'dwPreferredModuleFlags'),
        (DWORD, 'dwOtherModuleFlags'),
        (dyn.clone(pstr.wstring, length=WER_MAX_PREFERRED_MODULES_BUFFER), 'wzPreferredModuleList'),
        (DWORD, 'dwPreferredModuleResetFlags'),
        (DWORD, 'dwOtherModuleResetFlags'),
        (PVOID, 'pvDumpKey'),
        (HANDLE, 'hSnapshot'),
        (DWORD, 'dwThreadID'),
    ]

class WER_EXCEPTION_INFORMATION(pstruct.type):
    _fields_ =[
        (P(exception.EXCEPTION_POINTERS), 'pExceptionPointers'),
        (BOOL, 'bClientPointers'),
    ]

class WER_CONSENT(pint.enum):
    _values_ = [
        ('WerConsentNotAsked', 1),
        ('WerConsentApproved', 2),
        ('WerConsentDenied', 3),
        ('WerConsentAlwaysPrompt', 4),
    ]

class KERB_ETYPE_(pint.enum):
    _values_ = [
        ('RC4_HMAC_NT', 0x17),
    ]

class KERB_ECRYPT(pstruct.type):
    class _EncryptionType(KERB_ETYPE_, ULONG): pass
    class PKERB_ECRYPT_INITIALIZE(PVOID): pass
    class PKERB_ECRYPT_ENCRYPT(PVOID): pass
    class PKERB_ECRYPT_DECRYPT(PVOID): pass
    class PKERB_ECRYPT_FINISH(PVOID): pass
    class PKERB_ECRYPT_RANDOMKEY(PVOID): pass
    class PKERB_ECRYPT_CONTROL(PVOID): pass
    def __HashPassword(self):
        res = self['EncryptionType'].li
        return PVOID
    _fields_ = [
        (_EncryptionType, 'EncryptionType'),
        (ULONG, 'BlockSize'),
        (ULONG, 'ExportableEncryptionType'),
        (ULONG, 'KeySize'),
        (ULONG, 'HeaderSize'),
        (ULONG, 'PreferredCheckSum'),
        (ULONG, 'Attributes'),
        #(PCWSTR, 'Name'),
        (PWSTR, 'Name'),
        (PKERB_ECRYPT_INITIALIZE, 'Initialize'),
        (PKERB_ECRYPT_ENCRYPT, 'Encrypt'),
        (PKERB_ECRYPT_DECRYPT, 'Decrypt'),
        (PKERB_ECRYPT_FINISH, 'Finish'),
        (__HashPassword, 'HashPassword'),
        (PKERB_ECRYPT_RANDOMKEY, 'RandomKey'),
        (PKERB_ECRYPT_CONTROL, 'Control'),
        (PVOID, 'unk0_null'),
        (PVOID, 'unk1_null'),
        (PVOID, 'unk2_null'),
    ]
