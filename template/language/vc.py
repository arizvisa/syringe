import ptypes
from ptypes import *
#http://doxygen.reactos.org/dc/d27/cppexcept_8h_source.html

class codeptr_t(pint.uint32_t): pass
class vtable_ptr(codeptr_t): pass
class type_info(pstruct.type):
    _fields_ = [
        (dyn.pointer(vtable_ptr), 'vtable'),
        (dyn.pointer(pstr.szstring), 'name'),
        (dyn.clone(pstr.string, length=32), 'mangled'),
    ]

class exception(pstruct.type):
    _fields_ = [
        (dyn.pointer(vtable_ptr), 'vtable'),
        (dyn.pointer(pstr.szstring), 'name'),
        (pint.int32_t, 'do_free'),
    ]


class cxx_exception_frame(pstruct.type):
    _fields_ = [
        (dyn.pointer(ptype.undefined), 'frame'), # XXX
        (pint.int32_t, 'trylevel'),
        (pint.uint32_t, 'ebp'),
    ]

class catchblock_info(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (dyn.pointer(type_info), 'type_info'),
        (pint.int32_t, 'offset'),
        (codeptr_t, 'handler'),
    ]

class tryblock_info(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'start_level'),
        (pint.int32_t, 'end_level'),
        (pint.int32_t, 'catch_level'),
        (pint.int32_t, 'catchblock_count'),
        (dyn.pointer(catchblock_info), 'catchblock'),
    ]

class unwind_info(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'prev'),
        (codeptr_t, 'handler'),
    ]

class cxx_function_descr(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'magic'),
        (pint.uint32_t, 'unwind_count'),
        (lambda s: dyn.pointer(dyn.array(unwind_info, s['unwind_count'].li.int())), 'unwind_table'),
        (pint.uint32_t, 'tryblock_count'),
        (lambda s: dyn.pointer(dyn.array(tryblock_info, s['unwind_count'].li.int())), 'tryblock'),
        (pint.uint32_t, 'ipmap_count'),
        (dyn.pointer(ptype.undefined), 'ipmap'),       # XXX
        (dyn.pointer(ptype.undefined), 'expect_list'),     # XXX
        (pint.uint32_t, 'flags'),
    ]

class cxx_copy_ctor(codeptr_t): pass

class this_ptr_offsets(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'this_offset'),
        (pint.int32_t, 'vbase_descr'),
        (pint.int32_t, 'vbase_offset'),
    ]

class cxx_type_info(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (dyn.pointer(type_info), 'type_info'),
        (this_ptr_offsets, 'offsets'),
        (pint.uint32_t, 'size'),
        (cxx_copy_ctor, 'copy_ctor'),
    ]

class cxx_type_info_table(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'count'),
        (dyn.array(cxx_type_info, 3), 'info'),
    ]

class cxx_exc_custom_handler(codeptr_t): pass

class cxx_exception_type(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (codeptr_t, 'destructor'),
        (cxx_exc_custom_handler, 'custom_handler'),
        (dyn.pointer(cxx_type_info_table), 'type_info_table'),
    ]
