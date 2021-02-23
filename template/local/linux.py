import ptypes
from ptypes import *

# primitive types
class short(pint.int16_t): pass
class int(pint.uint32_t): pass
class long(pint.int32_t): pass
class unsigned_short(pint.uint16_t): pass
class signed_int(pint.sint32_t): pass
class unsigned_int(pint.uint32_t): pass
class unsigned_long(pint.uint32_t): pass
class void_p(ptype.pointer_t):
    _object_ = ptype.undefined
class uintptr_t(ptype.pointer_t):
    _object_ = ptype.undefined
class intptr_t(ptype.pointer_t):
    _object_ = ptype.undefined
class bool(int): pass

class size_t(pint.uinteger.lookup(ptypes.Config.integer.size)): pass
class ssize_t(pint.sinteger.lookup(ptypes.Config.integer.size)): pass

class char(pint.int8_t): pass
class unsigned_char(pint.uint8_t): pass
class unsigned_short_int(pint.uint16_t): pass
class long_int(pint.sinteger.lookup(ptypes.Config.integer.size)): pass
class unsigned_long_int(pint.uinteger.lookup(ptypes.Config.integer.size)): pass
class unsigned_long_long_int(pint.uinteger.lookup(8)): pass

# core types
class __pid_t(int): pass
class sigset_t(unsigned_long): pass

class pid_t(__pid_t): pass

# base types
class list_head(pstruct.type): pass
class atomic_t(pstruct.type):
    _fields_ = [
        (int, 'counter'),
    ]

class slobidx_t(pint.sint16_t): pass
class slob_block(pstruct.type):
    _fields_ = [
        (slobidx_t, 'units'),
    ]
class slob_t(slob_block): pass

# structures
class slab(pstruct.type):
    _fields_ = [
        (list_head, 'list'),
        (unsigned_long, 'colouroff'),
        (void_p, 's_mem'),
        (unsigned_int, 'inuse'),
        (unsigned_short, 'nodeid'),
    ]

class slab_rcu(pstruct.type):
    _fields_ = []

class page(pstruct.type):
    _fields_ = []

class slob_page(pstruct.type):
    _fields_ = [
        (unsigned_long, 'flags'),
        (atomic_t, '_count'),
        (slobidx_t, 'units'),
        (dyn.array(unsigned_long,2), 'pad'),
        (dyn.pointer(slob_t), 'free'),
        (list_head, 'list'),
    ]

### glibc-2.31
class tlsdesc(pstruct.type):
    _fields_ = [
        (pint.uint64_t, 'entry_slot'),  # (ptrdiff_t* entry)(struct tlsdesc* on_rax)
        (pint.uint64_t, 'arg_slot'),    # void_p arg
    ]

class dtv_pointer(pstruct.type):
    _fields_ = [
        (void_p, 'val'),
        (void_p, 'to_free'),
    ]

class dtv_t(dynamic.union):
    _fields_ = [
        (size_t, 'counter'),
        (dtv_pointer, 'pointer'),
    ]

class tcbhead_t(pstruct.type):
    class X86_FEATURE_1_(pbinary.flags):
        '''unsigned_int'''
        _fields_ = [
            (28, 'unused'),
            (1, 'SHSTK'),
            (1, 'IBT'),
        ]
    class __128bits(pstruct.type):
        _fields_ = [
            (dyn.array(int, 4), 'i'),
        ]
    _fields_ = [
        (void_p, 'tcb'),
        (dyn.pointer(dtv_t), 'dtv'),
        (void_p, 'self'),
        (int, 'multiple_threads'),
        (int, 'gscope_flag'),
        (uintptr_t, 'sysinfo'),
        (uintptr_t, 'stack_guard'),
        (uintptr_t, 'pointer_guard'),
        (dyn.array(unsigned_long_int, 2), 'vgetcpu_cache'),
        (X86_FEATURE_1_, 'feature_1'),
        (int, '__glibc_unused1'),
        (dyn.array(void_p, 4), '__private_tm'),
        (void_p, '__private_ss'),
        (unsigned_long_long_int, 'ssp_base'),
        (dyn.align(32), 'align(__glibc_unused2)'),
        (dyn.array(dyn.array(__128bits, 8), 4), '__glibc_unused2'),
        (dyn.array(void_p, 8), '__padding'),
    ]

class list_t(pstruct.type): pass
list_t._fields_ = [
    (dyn.pointer(list_t), 'next'),
    (dyn.pointer(list_t), 'prev'),
]

class robust_list_head(pstruct.type):
    _fields_ = [
        (void_p, 'list'),
        (long_int, 'futex_offset'),
        (void_p, 'list_op_pending'),
    ]

class pthread_cleanup_buffer(pstruct.type):
    _fields_ = [
        (dyn.pointer(ptype.undefined), '__routine'),
        (void_p, '__arg'),
        (int, '__canceltype'),
    ]
pthread_cleanup_buffer._fields_ += [(dyn.pointer(pthread_cleanup_buffer), '__prev')]

class _jmp_buf(parray.type):
    length, _object_ = 6, int

class pthread_unwind_buf(pstruct.type):
    class _cancel_jmp_buf(pstruct.type):
        _fields_ = [
            (_jmp_buf, 'jmp_buf'),
            (int, 'mask_was_Saved'),
        ]
    class _priv(dynamic.union):
        class _data(pstruct.type):
            def __prev(self):
                return pthread_unwind_buf
            _fields_ = [
                (dyn.pointer(__prev), 'prev'),
                (dyn.pointer(pthread_cleanup_buffer), 'cleanup'),
                (int, 'canceltype'),
            ]
        _fields_ = [
            (dyn.array(void_p, 4), 'pad'),
            (_data, 'data'),
        ]
    _fields_ = [
        (dyn.array(_cancel_jmp_buf, 1), 'cancel_jmp_buf'),
        (_priv, 'priv'),
    ]

class sched_param(pstruct.type):
    _fields_ = [
        (int, 'sched_priority'),
    ]

class td_event_e(pbinary.flags):
    _fields_ = [
        (1, 'TD_EVENTS_ENABLE'),    # Event reporting enabled.
        (17,'unused'),
        (1, 'TD_TIMEOUT'),          # Conditional variable wait timed out.
        (1, 'TD_CONCURRENCY'),      # Number of processes changing.
        (1, 'TD_REAP'),             # Reaped.
        (1, 'TD_PRI_INHERIT'),      # Inherited elevated priority.
        (1, 'TD_PREEMPT'),          # Preempted.
        (1, 'TD_DEATH'),            # Thread terminated.
        (1, 'TD_CREATE'),           # New thread created.
        (1, 'TD_IDLE'),             # Process getting idle.
        (1, 'TD_CATCHSIG'),         # Signal posted to the thread.
        (1, 'TD_LOCK_TRY'),         # Trying to get an unavailable lock.
        (1, 'TD_SWITCHFROM'),       # Not anymore assigned to a process.
        (1, 'TD_SWITCHTO'),         # Now assigned to a process.
        (1, 'TD_SLEEP'),            # Blocked in a synchronization obj.
        (1, 'TD_READY'),            # Is executable now.
    ]

class td_notify_e(pbinary.flags):
    _fields_ = [
        (29, 'unused'),
        (1, 'NOTIFY_BPT'),      # User must insert breakpoint at u.bptaddr.
        (1, 'NOTIFY_AUTOBPT'),  # Breakpoint at u.bptaddr is automatically inserted.
        (1, 'NOTIFY_SYSCALL'),  # System call u.syscallno will be invoked.
    ]

class psaddr_t(void_p): pass
class td_notify_t(pstruct.type):
    class _u(dynamic.union):
        _fields_ = [
            (psaddr_t, 'bptaddr'),
            (int, 'syscallno'),
        ]
    _fields_ = [
        (td_notify_e, 'type'),
        (_u, 'u'),
    ]

class td_thragent_t(pstruct.type):
    class ta_howto_(pint.enum, pint.uint32_t):
        _values_ =[
            ('unknown', 0),
            ('reg', 1),
            ('reg_thread_area', 2),
            ('const_thread_area', 3),
        ]
    class _ta_howto_data(dynamic.union):
        _fields_ = [
            (pint.uint32_t, 'const_thread_area'),
            #(db_desc_t, 'reg'),
            #(db_desc_t, 'reg_thread_Data'),
        ]

    _fields_ = [
        (list_t, 'list'),
        #(dyn.pointer(ps_prochandle), 'ph'),
        # nptl_db/structs.def
        (ta_howto_, 'ta_howto'),
        (_ta_howto_data, 'ta_howto_data'),
    ]

class td_thrhandle_t(pstruct.type):
    _fields_ = [
        (dyn.pointer(td_thragent_t), 'th_ta_p'),
        (psaddr_t, 'th_unique'),
    ]

class td_event_msg_t(pstruct.type):
    class _msg(dynamic.union):
        _fields_ = [
            (uintptr_t, 'data'),
        ]
    _fields_ = [
        (td_event_e, 'event'),
        (dyn.pointer(td_thrhandle_t), 'th_p'),
        (_msg, 'msg'),
    ]

TD_EVENTSIZE = 2
class td_thr_events_t(pstruct.type):
    _fields_ = [
        (dyn.array(pint.uint32_t, TD_EVENTSIZE), 'event_bits'),
    ]

class td_eventbuf_t(pstruct.type):
    _fields_ = [
        (td_thr_events_t, 'eventmask'),
        (td_event_e, 'eventnum'),
        (void_p, 'eventdata'),
    ]

class thread_t(unsigned_long_int): pass

class td_thr_state_e(pint.enum, pint.uint32_t):
    _values_ = [
        ('TD_THR_ANY_STATE', 0),
        ('TD_THR_UNKNOWN', 1),
        ('TD_THR_STOPPED', 2),
        ('TD_THR_RUN', 3),
        ('TD_THR_ACTIVE', 4),
        ('TD_THR_ZOMBIE', 5),
        ('TD_THR_SLEEP', 6),
        ('TD_THR_STOPPED_ASLEEP', 7),
    ]

class td_thr_type_e(pint.enum, pint.uint32_t):
    _values_ = [
        ('TD_THR_ANY_TYPE', 0),
        ('TD_THR_USER', 1),
        ('TD_THR_SYSTEM', 2),
    ]

class lwpid_t(__pid_t): pass

class td_thrinfo_t(pstruct.type):
    _fields_ = [
        (dyn.pointer(td_thragent_t), 'ti_ta_p'),    #  Process handle.
        (unsigned_int, 'ti_user_flags'),            #  Unused.
        (thread_t, 'ti_tid'),                       #  Thread ID returned by pthread_create().
        (dyn.pointer(char), 'ti_tls'),              #  Pointer to thread-local data.
        (psaddr_t, 'ti_startfunc'),                 #  Start function passed to pthread_create().
        (psaddr_t, 'ti_stkbase'),                   #  Base of thread's stack.
        (long, 'int ti_stksize'),                   #  Size of thread's stack.
        (psaddr_t, 'ti_ro_area'),                   #  Unused.
        (int, 'ti_ro_size'),                        #  Unused.
        (td_thr_state_e, 'ti_state'),               #  Thread state.
        (unsigned_char, 'ti_db_suspended'),         #  Nonzero if suspended by debugger.
        (td_thr_type_e, 'ti_type'),                 #  Type of the thread (system vs user thread).
        (intptr_t, 'ti_pc'),                        #  Unused.
        (intptr_t, 'ti_sp'),                        #  Unused.
        (short, 'int ti_flags'),                    #  Unused.
        (int, 'ti_pri'),                            #  Thread priority.
        (lwpid_t, 'ti_lid'),                        #  Kernel PID for this thread.
        (sigset_t, 'ti_sigmask'),                   #  Signal mask.
        (unsigned_char, 'ti_traceme'),              #  Nonzero if event reporting enabled.
        (unsigned_char, 'ti_preemptflag'),          #  Unused.
        (unsigned_char, 'ti_pirecflag'),            #  Unused.
        (sigset_t, 'ti_pending'),                   #  Set of pending signals.
        (td_thr_events_t, 'ti_events'),             #  Set of enabled events.
    ]

class _Unwind_Exception_Class(unsigned_int): pass
class _Unwind_Exception_Cleanup_Fn(dyn.pointer(ptype.undefined)): pass
class _Unwind_Word(unsigned_int): pass
class _Unwind_Sword(signed_int): pass
class _Unwind_Ptr(ptype.pointer_t): pass
class _Unwind_Internal_Ptr(ptype.pointer_t): pass
class _Unwind_Reason_Code(pint.enum):
    _values_ = [
        ('_URC_NO_REASON', 0),
        ('_URC_FOREIGN_EXCEPTION_CAUGHT', 1),
        ('_URC_FATAL_PHASE2_ERROR', 2),
        ('_URC_FATAL_PHASE1_ERROR', 3),
        ('_URC_NORMAL_STOP', 4),
        ('_URC_END_OF_STACK', 5),
        ('_URC_HANDLER_FOUND', 6),
        ('_URC_INSTALL_CONTEXT', 7),
        ('_URC_CONTINUE_UNWIND', 8),
    ]

class _Unwind_Exception(pstruct.type):
    _fields_ = [
        (_Unwind_Exception_Class, 'exception_class'),
        (_Unwind_Exception_Cleanup_Fn, 'exception_cleanup'),
        (_Unwind_Word, 'private_1'),
        (_Unwind_Word, 'private_2'),
    ]

class priority_protection_data(pstruct.type):
    _fields_ = [
        (int, 'priomax'),
        (dyn.array(unsigned_int, 0), 'priomap'),
    ]

MAXNS = 3           # max # name servers we'll track
MAXDFLSRCH = 3      # default domain levels to try
MAXDNSRCH = 6       # max # domains in search path
MAXRESOLVSORT = 10  # number of net to sort on

class sa_family_t(unsigned_short_int): pass
class in_port_t(pint.uint16_t): pass
class sockaddr(pstruct.type):
    _fields_ = [
        (sa_family_t, 'sa_family'),
        (dyn.array(char, 14), 'sa_data'),
    ]

class in_addr_t(pint.uint32_t): pass
class in_addr(pstruct.type):
    _fields_ = [
        (in_addr_t, 's_addr'),
    ]

class sockaddr_in(pstruct.type):
    _fields_ = [
        (sa_family_t, 'sin_family'),
        (in_port_t, 'sin_port'),
        (dyn.block(sockaddr().a.blocksize() - sum(item().a.blocksize() for item in [sa_family_t,in_port_t,in_addr])), 'sin_zero'),
    ]

class in6_addr_t(dyn.block(16)): pass
class in6_addr(pstruct.type):
    _fields_ = [
        (in6_addr_t, 's6_addr'),
    ]

class sockaddr_in6(pstruct.type):
    _fields_ = [
        (sa_family_t, 'sin6_family'),
        (in_port_t, 'sin6_port'),
        (pint.uint32_t, 'sin6_flowinfo'),
        (in6_addr, 'sin6_addr'),
        (pint.uint32_t, 'sin6_scope_id'),
    ]

class res_state(pstruct.type):
    class __state(pbinary.struct):
        _fields_ = [
            (23, 'unused'),
            (1, 'ipv6_unavail'),
            (4, 'nsort'),
            (4, 'ndots'),
        ]
    class _sort_list(pstruct.type):
        _fields_ = [
            (in_addr, 'addr'),
            (pint.uint32_t, 'mask'),
        ]
    class _u(dynamic.union):
        class _ext(pstruct.type):
            _fields_ = [
                (pint.uint16_t, 'nscount'),
                (dyn.array(pint.uint16_t, MAXNS), 'nsmap'),
                (dyn.array(int, MAXNS), 'nssocks'),
                (pint.uint16_t, 'nscount6'),
                (pint.uint16_t, 'nsinit'),
                (dyn.array(dyn.pointer(sockaddr_in6), MAXNS), 'nsaddrs'),
                (dyn.array(unsigned_int, 2), '__glibc_reserved'),
            ]
        _fields_ = [
            (dyn.array(char, 52), 'pad'),
            (_ext, '_ext'),
        ]
    _fields_ = [
        (int, 'retrans'),
        (int, 'retry'),
        (unsigned_long, 'options'),
        (int, 'nscount'),
        (dyn.array(sockaddr_in, MAXNS), 'nsaddr_list'),
        (unsigned_short, 'id'),
        (dyn.padding(2), '0) 2 byte hole here.'),
        (dyn.array(char, MAXDNSRCH+1), 'dnsrch'),
        (dyn.array(char, 256), 'defdname'),
        (unsigned_long, 'pfcode'),
        (__state, 'state'),
        (dyn.array(_sort_list, MAXRESOLVSORT), 'sort_list'),
        (dyn.padding(8), '1) 4 byte hole here on 64-bit architectures.'),
        (void_p, '__glibc_unused_qhook'),
        (void_p, '__glibc_unused_rhook'),
        (int, 'res_h_errno'),
        (int, '_vcsock'),
        (unsigned_int, '_flags'),
        (dyn.padding(8), '2) 4 byte hole here on 64-bit architectures.'),
        (_u, '_u'),
    ]

PTHREAD_KEYS_MAX = 1024
PTHREAD_KEY_2NDLEVEL_SIZE = 32
PTHREAD_KEY_1STLEVEL_SIZE = (PTHREAD_KEYS_MAX + PTHREAD_KEY_2NDLEVEL_SIZE - 1) // PTHREAD_KEY_2NDLEVEL_SIZE

class pthread(pstruct.type):
    class _header(dynamic.union):
        class _multiple_threads(pstruct.type):
            _fields_ = [
                (int, 'multiple_threads'),
                (int, 'gscope_flag'),
            ]
        _fields_ = [
            (tcbhead_t, 'tcb'),
            (_multiple_threads, 'multiple_threads'),
            (dyn.array(void_p, 24), '__padding'),
        ]
    class _cancelhandling(pbinary.flags):
        '''int'''
        _fields_ = [
            (25, 'REST'),
            (1, 'SETXID'),
            (1, 'TERMINATED'),
            (1, 'EXITING'),
            (1, 'CANCELED'),
            (1, 'CANCELING'),
            (1, 'CANCELTYPE'),
            (1, 'CANCELSTATE'),
        ]
    class pthread_key_data(pstruct.type):
        _fields_ = [
            (uintptr_t, 'seq'),
            (void_p, 'data'),
        ]
    _fields_ = [
        (_header, 'header'),
        (list_t, 'list'),
        (pid_t, 'tid'),
        (pid_t, 'pid_ununsed'),
        (void_p, 'robust_prev'),
        (robust_list_head, 'robust_head'),
        (dyn.pointer(pthread_cleanup_buffer), 'cleanup'),
        (dyn.pointer(pthread_unwind_buf), 'cleanup_jmp_buf'),
        (_cancelhandling, 'cancelhandling'),
        (int, 'flags'),
        (dyn.array(pthread_key_data, PTHREAD_KEY_2NDLEVEL_SIZE), 'specific_1stblock'),
        (dyn.array(pthread_key_data, PTHREAD_KEY_1STLEVEL_SIZE), 'specific'),
        (bool, 'specific_used'),
        (bool, 'report_events'),
        (bool, 'user_stack'),
        (bool, 'stopped_start'),
        (int, 'parent_cancelhandling'),
        (int, 'lock'),
        (unsigned_int, 'setxid_futex'),
        (dyn.pointer(lambda self: pthread), 'joinid'),
        (void_p, 'result'),
        (sched_param, 'schedparam'),
        (int, 'schedpolicy'),
        (dyn.pointer(ptype.undefined), 'start_routine'),
        (void_p, 'arg'),
        (td_eventbuf_t, 'eventbuf'),
        (dyn.pointer(lambda self: pthread), 'nextevent'),
        (_Unwind_Exception, 'exc'),
        (void_p, 'stackblock'),
        (size_t, 'stackblock_size'),
        (size_t, 'guardsize'),
        (size_t, 'reported_guardsize'),
        (dyn.pointer(priority_protection_data), 'tpp'),
        (res_state, 'res'),
        (bool, 'c11'),
        (dyn.padding(pfloat.double.length), 'end_padding'),
    ]
