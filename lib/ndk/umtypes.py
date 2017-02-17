from WinNT import *
import logging

NT_SUCCESS = lambda Status: ((int(Status)) >= 0)
NT_INFORMATION = lambda Status: (((int(Status)) >> 30) == 1)
NT_WARNING = lambda Status: (((int(Status)) >> 30) == 2)
NT_ERROR = lambda Status: (((int(Status)) >> 30) == 3)

MINCHAR = 0x80
MAXCHAR = 0x7f
MINSHORT = 0x8000
MAXSHORT = 0x7fff
MINLONG = 0x80000000
MAXLONG = 0x7fffffff
MAXUCHAR = 0xff
MAXUSHORT = 0xffff
MAXULONG = 0xffffffff

CSR_MAKE_OPCODE = lambda s,m: ((s) << 16) | (m)
CSR_API_ID_FROM_OPCODE = lambda n: (int(int(n)))
CSR_SERVER_ID_FROM_OPCODE = lambda n: int((n) >> 16)

class CINT(pint.uint32_t): pass
class PCSZ(dyn.pointer(pstr.char_t)): pass
class CLONG(ULONG): pass
class CSHORT(short): pass
class PCSHORT(dyn.pointer(CSHORT)): pass
class PHYSICAL_ADDRESS(LARGE_INTEGER): pass
class PPHYSICAL_ADDRESS(dyn.pointer(PHYSICAL_ADDRESS)): pass
class KPRIORITY(LONG): pass
class KAFFINITY(LONG): pass
class NTSTATUS(LONG): pass
class PNTSTATUS(dyn.pointer(NTSTATUS)): pass

class PSTR(pstr.string): pass
class WSTR(pstr.wstring): pass

class CLIENT_ID(pstruct.type):
    _fields_ = [
        (HANDLE, 'UniqueProcess'),
        (HANDLE, 'UniqueThread'),
    ]

class UNICODE_STRING(pstruct.type):
    _fields_ = [
        (USHORT, 'Length'),
        (USHORT, 'MaximumLength'),
#        (PWSTR, 'Buffer'),
#        (lambda s: dyn.pointer(dyn.clone(WSTR, length=s['MaximumLength'].li.int())), 'Buffer')
        (lambda s: dyn.pointer(dyn.clone(WSTR, length=s['Length'].li.int()/2)), 'Buffer')
    ]

    def get(self):
        logging.warn('UNICODE_STRING.get() has been deprecated in favor of .str()')
        return self.str()

    def str(self):
        return None if self['Buffer'].int() == 0 else self['Buffer'].d.li.str()[:self['Length'].int()]

    def summary(self):
        return 'Length={:x} MaximumLength={:x} Buffer={!r}'.format(self['Length'].int(), self['MaximumLength'].int(), self.str())

class PUNICODE_STRING(dyn.pointer(UNICODE_STRING)): pass

class STRING(pstruct.type):
    _fields_ = [
        (USHORT, 'Length'),
        (USHORT, 'MaximumLength'),
        (lambda s: dyn.pointer(dyn.clone(PSTR, length=s['Length'].li.int())), 'Buffer')
    ]

    def get(self):
        logging.warn('STRING.get() has been deprecated in favor of .str()')
        return self.str()

    def str(self):
        return None if self['Buffer'].int() == 0 else self['Buffer'].d.li.str()[:self['Length'].int()]

    def summary(self):
        return 'Length={:x} MaximumLength={:x} Buffer={!r}'.format(self['Length'].int(), self['MaximumLength'].int(), self.str())

class PSTRING(dyn.pointer(STRING)): pass

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
