import ptypes
from ptypes import *

# primitive types
class char(pint.int8_t): pass
class signed_char(pint.sint8_t): pass
class unsigned_char(pint.uint8_t): pass
class short(pint.int16_t): pass
class signed_short(pint.sint16_t): pass
class unsigned_short(pint.uint16_t): pass
class int(pint.int32_t): pass
class signed_int(pint.sint32_t): pass
class unsigned_int(pint.uint32_t): pass
class long(pint.int_t):
    length = property(fget=lambda _: ptypes.Config.integer.size)
class signed_long(pint.sint_t):
    length = property(fget=lambda _: ptypes.Config.integer.size)
class unsigned_long(pint.uint_t):
    length = property(fget=lambda _: ptypes.Config.integer.size)
class long_long(pint.int64_t): pass
class signed_long_long(pint.sint64_t): pass
class unsigned_long_long(pint.uint64_t): pass

class void(ptype.undefined):
    length = 1
class void_star(ptype.pointer_t):
    _object_ = void
class uintptr_t(ptype.pointer_t):
    _object_ = ptype.undefined
class intptr_t(ptype.pointer_t):
    _object_ = ptype.undefined
class bool(int): pass

class float(pfloat.single): pass
class double(pfloat.double): pass

class unsigned_short_int(unsigned_short): pass
class long_int(long): pass
class long_unsigned_int(unsigned_long): pass
class unsigned_long_int(unsigned_long): pass
class unsigned_long_long_int(unsigned_long_long): pass

class __int64_t(pint.int64_t): pass
class __uint64_t(pint.uint64_t): pass

class size_t(long_unsigned_int): pass
class __ssize_t(long_int): pass
class ssize_t(__ssize_t): pass

class wchar_t(pstr.wchar_t): pass

# core types
class __dev_t(__uint64_t): pass
class __uid_t(unsigned_int): pass
class __gid_t(unsigned_int): pass
class __ino_t(unsigned_long_int): pass
class __ino64_t(__uint64_t): pass
class __mode_t(unsigned_int): pass
class __nlink_t(unsigned_long_int): pass
class __off_t(long_int): pass
class __off64_t(__int64_t): pass
class __pid_t(int): pass
#class __fsid_t(parray.type): length, _object_ = 2, int
class __clock_t(long_int): pass
class __rlim_t(unsigned_long_int): pass
class __rlim64_t(__uint64_t): pass
class __id_t(unsigned_int): pass
class __time_t(long_int): pass
class __useconds_t(unsigned_int): pass
class __suseconds_t(long_int): pass
class __suseconds64_t(__int64_t): pass
class __daddr_t(int): pass
class __key_t(int): pass

class sigset_t(unsigned_long): pass
class pid_t(__pid_t): pass
class off_t(__off_t): pass
class off64_t(__off64_t): pass

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
        (void_star, 's_mem'),
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
        (pint.uint64_t, 'arg_slot'),    # void_star arg
    ]

class dtv_pointer(pstruct.type):
    _fields_ = [
        (void_star, 'val'),
        (void_star, 'to_free'),
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
        (void_star, 'tcb'),
        (dyn.pointer(dtv_t), 'dtv'),
        (void_star, 'self'),
        (int, 'multiple_threads'),
        (int, 'gscope_flag'),
        (uintptr_t, 'sysinfo'),
        (uintptr_t, 'stack_guard'),
        (uintptr_t, 'pointer_guard'),
        (dyn.array(unsigned_long_int, 2), 'vgetcpu_cache'),
        (X86_FEATURE_1_, 'feature_1'),
        (int, '__glibc_unused1'),
        (dyn.array(void_star, 4), '__private_tm'),
        (void_star, '__private_ss'),
        (unsigned_long_long_int, 'ssp_base'),
        (dyn.align(32), 'align(__glibc_unused2)'),
        (dyn.array(dyn.array(__128bits, 8), 4), '__glibc_unused2'),
        (dyn.array(void_star, 8), '__padding'),
    ]

class list_t(pstruct.type): pass
list_t._fields_ = [
    (dyn.pointer(list_t), 'next'),
    (dyn.pointer(list_t), 'prev'),
]

class robust_list_head(pstruct.type):
    _fields_ = [
        (void_star, 'list'),
        (long_int, 'futex_offset'),
        (void_star, 'list_op_pending'),
    ]

class pthread_cleanup_buffer(pstruct.type):
    _fields_ = [
        (dyn.pointer(ptype.undefined), '__routine'),
        (void_star, '__arg'),
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
            (dyn.array(void_star, 4), 'pad'),
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

class psaddr_t(void_star): pass
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
        (void_star, 'eventdata'),
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
        (void_star, '__glibc_unused_qhook'),
        (void_star, '__glibc_unused_rhook'),
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
            (dyn.array(void_star, 24), '__padding'),
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
            (void_star, 'data'),
        ]
    _fields_ = [
        (_header, 'header'),
        (list_t, 'list'),
        (pid_t, 'tid'),
        (pid_t, 'pid_ununsed'),
        (void_star, 'robust_prev'),
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
        (void_star, 'result'),
        (sched_param, 'schedparam'),
        (int, 'schedpolicy'),
        (dyn.pointer(ptype.undefined), 'start_routine'),
        (void_star, 'arg'),
        (td_eventbuf_t, 'eventbuf'),
        (dyn.pointer(lambda self: pthread), 'nextevent'),
        (_Unwind_Exception, 'exc'),
        (void_star, 'stackblock'),
        (size_t, 'stackblock_size'),
        (size_t, 'guardsize'),
        (size_t, 'reported_guardsize'),
        (dyn.pointer(priority_protection_data), 'tpp'),
        (res_state, 'res'),
        (bool, 'c11'),
        (dyn.padding(pfloat.double.length), 'end_padding'),
    ]

class _IO_marker(pstruct.type):
    _fields_ = [
        (lambda _: dyn.pointer(_IO_marker), '_next'),
        (lambda _: dyn.pointer(FILE), '_sbuf'),
        (int, 'pos'),
    ]

class _IO_FLAGS2_(pbinary.flags):
    _fields_ = [
        (26, 'unused'),
        (1, 'NEED_LOCK'),
        (1, 'CLOEXEC'),
        (1, 'NOCLOSE'),
        (1, 'USER_WBUF'),
        (1, 'NOTCANCEL'),
        (1, 'MMAP'),
    ]

class _IO_lock_t(void): pass

class __gconv_fct__(void_star): pass
class __gconv_init_fct__(void_star): pass
class __gconv_end_fct__(void_star): pass

class __gconv_loaded_object__(pstruct.type):
    _fields_ = [
        (dyn.pointer(pstr.szstring), 'name'),
        (int, 'counter'),
        (void_star, 'handle'),
        (__gconv_fct__, 'fct'),
        (__gconv_init_fct__, 'init_fct'),
        (__gconv_end_fct__, 'end_fct'),
    ]

class __gconv_btowc_fct__(void_star): pass

class __gconv_step__(pstruct.type):
    _fields_ = [
        (dyn.pointer(__gconv_loaded_object__), '__shlib_handle'),
        (dyn.pointer(pstr.szstring), '__modname'),
        (int, '__counter'),
        (dyn.pointer(pstr.szstring), '__from_name'),
        (dyn.pointer(pstr.szstring), '__to_name'),
        (__gconv_fct__, '__fct'),
        (__gconv_btowc_fct__, '__btowc_fct'),
        (__gconv_init_fct__, '__init_fct'),
        (__gconv_end_fct__, '__end_fct'),
        (int, '__min_needed_from'),
        (int, '__max_needed_from'),
        (int, '__min_needed_to'),
        (int, '__max_needed_to'),
        (int, '__stateful'),
        (void_star, '__data'),
    ]

class __mbstate_t__(pstruct.type):
    _fields_ = [
        (int, '__count'),
        (unsigned_int, '__wch'),
    ]

class __gconv_step_data__(pstruct.type):
    _fields_ = [
        (dyn.pointer(unsigned_char), '__outbuf'),
        (dyn.pointer(unsigned_char), '__outbufend'),
        (int, '__flags'),
        (int, '__invocation_counter'),
        (int, '__internal_use'),
        (dyn.pointer(__mbstate_t__), '__statep'),
        (__mbstate_t__, '__state'),
    ]

class _IO_iconv_t(pstruct.type):
    _fields_ = [
        (dyn.pointer(__gconv_step__), 'step'),
        (dyn.pointer(__gconv_step_data__), 'step_data'),
    ]

class _IO_codecvt(pstruct.type):
    _fields_ = [
        (_IO_iconv_t, '__cd_in'),
        (_IO_iconv_t, '__cd_out'),
    ]

class _IO_finish_t(void_star): pass
class _IO_overflow_t(void_star): pass
class _IO_underflow_t(void_star): pass
class _IO_underflow_t(void_star): pass
class _IO_pbackfail_t(void_star): pass
class _IO_xsputn_t(void_star): pass
class _IO_xsgetn_t(void_star): pass
class _IO_seekoff_t(void_star): pass
class _IO_seekpos_t(void_star): pass
class _IO_setbuf_t(void_star): pass
class _IO_sync_t(void_star): pass
class _IO_doallocate_t(void_star): pass
class _IO_read_t(void_star): pass
class _IO_write_t(void_star): pass
class _IO_seek_t(void_star): pass
class _IO_close_t(void_star): pass
class _IO_stat_t(void_star): pass
class _IO_showmanyc_t(void_star): pass
class _IO_imbue_t(void_star): pass

class _IO_jump_t(pstruct.type):
    _fields_ = [
        (size_t, '__dummy'),
        (size_t, '__dummy2'),
        (_IO_finish_t, '__finish'),
        (_IO_overflow_t, '__overflow'),
        (_IO_underflow_t, '__underflow'),
        (_IO_underflow_t, '__uflow'),
        (_IO_pbackfail_t, '__pbackfail'),
        (_IO_xsputn_t, '__xsputn'),
        (_IO_xsgetn_t, '__xsgetn'),
        (_IO_seekoff_t, '__seekoff'),
        (_IO_seekpos_t, '__seekpos'),
        (_IO_setbuf_t, '__setbuf'),
        (_IO_sync_t, '__sync'),
        (_IO_doallocate_t, '__doallocate'),
        (_IO_read_t, '__read'),
        (_IO_write_t, '__write'),
        (_IO_seek_t, '__seek'),
        (_IO_close_t, '__close'),
        (_IO_stat_t, '__stat'),
        (_IO_showmanyc_t, '__showmanyc'),
        (_IO_imbue_t, '__imbue'),
    ]

class _IO_wide_data(pstruct.type):
    _fields_ = [
        (dyn.pointer(wchar_t), '_IO_read_base'),
        (dyn.pointer(wchar_t), '_IO_read_ptr'),
        (dyn.pointer(wchar_t), '_IO_read_end'),
        (dyn.pointer(wchar_t), '_IO_write_base'),
        (dyn.pointer(wchar_t), '_IO_write_ptr'),
        (dyn.pointer(wchar_t), '_IO_write_end'),
        (dyn.pointer(wchar_t), '_IO_buf_base'),
        (dyn.pointer(wchar_t), '_IO_buf_end'),
        (dyn.pointer(wchar_t), '_IO_save_base'),
        (dyn.pointer(wchar_t), '_IO_backup_base'),
        (dyn.pointer(wchar_t), '_IO_save_end'),
        (__mbstate_t__, '_IO_state'),
        (__mbstate_t__, '_IO_last_state'),
        (_IO_codecvt, '_codecvt'),
        (dyn.array(wchar_t, 1), '_shortbuf'),
        (dyn.pointer(_IO_jump_t), '_wide_vtable'),
    ]

class _IO_FILE(pstruct.type):
    @pbinary.littleendian
    class __flags(pbinary.flags):
        _fields_ = [
            (16, '_IO_MAGIC'),
            (1, '_IO_USER_LOCK'),
            (1, 'unused'),
            (1, '_IO_IS_FILEBUF'),
            (1, '_IO_IS_APPENDING'),
            (1, '_IO_CURRENTLY_PUTTING'),
            (1, '_IO_TIED_PUT_GET'),
            (1, '_IO_LINE_BUF'),
            (1, '_IO_IN_BACKUP'),
            (1, '_IO_LINKED'),
            (1, '_IO_DELETE_DONT_CLOSE'),
            (1, '_IO_ERR_SEEN'),
            (1, '_IO_EOF_SEEN'),
            (1, '_IO_NO_WRITES'),
            (1, '_IO_NO_READS'),
            (1, '_IO_UNBUFFERED'),
            (1, '_IO_USER_BUF'),
        ]
    @pbinary.littleendian
    class __flags2(_IO_FLAGS2_): pass
    class __mode(pint.enum, int):
        _values_ = [
            ('needflush', -1),
            ('single', 0),
            ('wide', 1),
        ]
    _fields_ = [
        (__flags, '_flags'),
        (lambda self: dyn.align(ptypes.Config.integer.size), 'align(_IO_read_ptr)'),
        (dyn.pointer(char), '_IO_read_ptr'),
        (dyn.pointer(char), '_IO_read_end'),
        (dyn.pointer(char), '_IO_read_base'),
        (dyn.pointer(char), '_IO_write_base'),
        (dyn.pointer(char), '_IO_write_ptr'),
        (dyn.pointer(char), '_IO_write_end'),
        (dyn.pointer(char), '_IO_buf_base'),
        (dyn.pointer(char), '_IO_buf_end'),
        (dyn.pointer(char), '_IO_save_base'),
        (dyn.pointer(char), '_IO_backup_base'),
        (dyn.pointer(char), '_IO_save_end'),
        (dyn.pointer(_IO_marker), '_markers'),
        (lambda _: dyn.pointer(_IO_FILE), '_chain'),
        (int, '_fileno'),
        (__flags2, '_flags2'),
        (off_t, '_old_offset'),
        (unsigned_short, '_cur_column'),
        (signed_char, '_vtable_offset'),
        (dyn.array(char, 1), '_shortbuf'),
        (lambda self: dyn.align(ptypes.Config.integer.size), 'align(_lock)'),
        (dyn.pointer(_IO_lock_t), '_lock'),
        (off64_t, '_offset'),
        (dyn.pointer(_IO_codecvt), '_codecvt'),
        (dyn.pointer(_IO_wide_data), '_wide_data'),
        (lambda self: dyn.pointer(_IO_FILE), '_freeres_list'),
        (void_star, '_freeres_buf'),
        (size_t, '__pad5'),
        (int, '_mode'),
        (lambda self: dyn.block(15 * int().blocksize() - 4 * void_star().blocksize() - size_t().blocksize()), '_unused2'),
    ]
class FILE(_IO_FILE): pass

class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u32(pint.uint32_t): pass
class comp_t(pfloat.float_t): components = (0, 3, 13) # base8
class comp2_t(pfloat.float_t): components = (0, 5, 19) # base2

ACCT_COMM = 16
class acct(pstruct.type):
    class _ac_flag(pbinary.flags):
        _fields_ = [
            (3, 'unused'),
            (1, 'AXSIG'),
            (1, 'ACORE'),
            (1, 'reserved'),
            (1, 'AFORK'),
        ]
    _fields_ = [
        (_ac_flag, 'ac_flag'),                                      # Flags
        (char, 'ac_version'),                                       # Always set to ACCT_VERSION
        (u16, 'ac_uid16'),                                          # LSB of Real User ID
        (u16, 'ac_gid16'),                                          # LSB of Real Group ID
        (u16, 'ac_tty'),                                            # Control Terminal
        (u32, 'ac_btime'),                                          # Process Creation Time
        (comp_t, 'ac_utime'),                                       # User Time
        (comp_t, 'ac_stime'),                                       # System Time
        (comp_t, 'ac_etime'),                                       # Elapsed Time
        (comp_t, 'ac_mem'),                                         # Average Memory Usage
        (comp_t, 'ac_io'),                                          # Chars Transferred
        (comp_t, 'ac_rw'),                                          # Blocks Read or Written
        (comp_t, 'ac_minflt'),                                      # Minor Pagefaults
        (comp_t, 'ac_majflt'),                                      # Major Pagefaults
        (comp_t, 'ac_swaps'),                                       # Number of Swaps
        (u16, 'ac_ahz'),                                            # AHZ
        (u32, 'ac_exitcode'),                                       # Exitcode
        (dyn.clone(pstr.string, length=ACCT_COMM + 1), 'ac_comm'),  # Command Name
        (u8, 'ac_etime_hi'),                                        # Elapsed Time MSB
        (u16, 'ac_etime_lo'),                                       # Elapsed Time LSB
        (u32, 'ac_uid'),                                            # Real User ID
        (u32, 'ac_gid'),                                            # Real Group ID
    ]

class acct_v3(pstruct.type):
    class _ac_flag(pbinary.flags):
        _fields_ = [
            (3, 'unused'),
            (1, 'AXSIG'),
            (1, 'ACORE'),
            (1, 'ACOMPAT'),
            (1, 'ASU'),
            (1, 'AFORK'),
        ]
    _fields_ = [
        (char, 'ac_flag'),                                      # Flags
        (char, 'ac_version'),                                   # Always set to ACCT_VERSION
        (u16, 'ac_tty'),                                        # Control Terminal
        (u32, 'ac_exitcode'),                                   # Exitcode
        (u32, 'ac_uid'),                                        # Real User ID
        (u32, 'ac_gid'),                                        # Real Group ID
        (u32, 'ac_pid'),                                        # Process ID
        (u32, 'ac_ppid'),                                       # Parent Process ID
        (u32, 'ac_btime'),                                      # Process Creation Time
        (float, 'ac_etime'),                                    # Elapsed Time
        (comp_t, 'ac_utime'),                                   # User Time
        (comp_t, 'ac_stime'),                                   # System Time
        (comp_t, 'ac_mem'),                                     # Average Memory Usage
        (comp_t, 'ac_io'),                                      # Chars Transferred
        (comp_t, 'ac_rw'),                                      # Blocks Read or Written
        (comp_t, 'ac_minflt'),                                  # Minor Pagefaults
        (comp_t, 'ac_majflt'),                                  # Major Pagefaults
        (comp_t, 'ac_swaps'),                                   # Number of Swaps
        (dyn.clone(pstr.string, length=ACCT_COMM), 'ac_comm'),  # Command Name
    ]

