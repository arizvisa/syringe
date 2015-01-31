from ptypes import *

# primitive types
class short(pint.int16_t): pass
class int(pint.uint32_t): pass
class long(pint.int32_t): pass
class unsigned_short(pint.uint16_t): pass
class unsigned_int(pint.uint32_t): pass
class unsigned_long(pint.uint32_t): pass

# base types
class list_head(pstruct.type): pass

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
