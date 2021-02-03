'''
This module is based on the ndk.exception library module. Please
consider using that module instead of this one.
'''

import ptypes, ndk, ndk.exception
from ndk.exception import *

class vtable_ptr(PVOID): pass
class type_info(TypeDescriptor): pass

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

class cxx_copy_ctor(PVOID): pass

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

class cxx_exc_custom_handler(PVOID): pass

class cxx_exception_type(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'flags'),
        (PVOID, 'destructor'),
        (cxx_exc_custom_handler, 'custom_handler'),
        (dyn.pointer(cxx_type_info_table), 'type_info_table'),
    ]
