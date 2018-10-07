from ptypes import *

class r_empty(pint.int_t): pass
class r_long64(pint.int64_t): pass
class r_long(pint.int32_t): pass
class r_short(pint.int16_t): pass
class r_byte(pstr.char_t): pass
class r_string(ptype.block): pass
class r_unknown(ptype.block): pass

class r_object(pstruct.type):
    def __data(self):
        id = self['type'].li.str()
        return pobject.withdefault(id, type=id)

    _fields_ = [
        (r_byte, 'type'),
        (__data, 'data'),
    ]

class pobject(ptype.definition):
    cache = {}

@pobject.define
class TYPE_NULL(r_empty): type = '0'
@pobject.define
class TYPE_NONE(r_empty): type = 'N'
@pobject.define
class TYPE_FALSE(r_empty): type = 'F'
@pobject.define
class TYPE_TRUE(r_empty): type = 'T'
@pobject.define
class TYPE_STOPITER(r_empty): type = 'S'
@pobject.define
class TYPE_ELLIPSIS(r_empty): type = '.'
@pobject.define
class TYPE_INT(r_long): type = 'i'
@pobject.define
class TYPE_INT64(r_long64): type = 'I'

@pobject.define
class TYPE_FLOAT(pstruct.type):
    type = 'f'
    _fields_ = [
        (r_byte, 'n'),
        (lambda s: dyn.clone(r_string, length=s['n'].li.int()), 'float'),
    ]

@pobject.define
class TYPE_BINARY_FLOAT(r_string):
    type = 'g'
    length = 8

@pobject.define
class TYPE_COMPLEX(pstruct.type):
    type = 'x'
    _fields_ = [
        (r_byte, 'n1'),
        (lambda s: dyn.clone(r_string, length=s['n1'].li.int()), '1'),
        (r_byte, 'n2'),
        (lambda s: dyn.clone(r_string, length=s['n2'].li.int()), '2'),
    ]
@pobject.define
class TYPE_BINARY_COMPLEX(pstruct.type):
    type = 'y'
    _fields_ = [
        (dyn.clone(r_string, length=8), '1'),
        (dyn.clone(r_string, length=8), '2'),
    ]
@pobject.define
class TYPE_LONG(pstruct.type):
    type = 'l'
    _fields_ = [
        (r_long, 'n'),
        (lambda s: dyn.array(r_short, s['n'].li.int()), 'data'),
    ]
@pobject.define
class TYPE_STRING(pstruct.type):
    type = 's'
    _fields_ = [
        (r_long, 'n'),
        (lambda s: dyn.clone(r_string, length=s['n'].li.int()), 'string'),
    ]
@pobject.define
class TYPE_INTERNED(TYPE_STRING): type = 't'
@pobject.define
class TYPE_STRINGREF(r_long): type = 'R'
@pobject.define
class TYPE_TUPLE(pstruct.type):
    type = '('
    _fields_ = [
        (r_long, 'n'),
        (lambda s: dyn.array(r_object, s['n'].li.int()), 'data'),
    ]
@pobject.define
class TYPE_LIST(pstruct.type):
    type = '['
    _fields_ = [
        (r_long, 'n'),
        (lambda s: dyn.array(r_object, s['n'].li.int()), 'data'),
    ]

@pobject.define
class TYPE_DICT(parray.terminated):
    type = '{'
    class member(pstruct.type):
        _fields_ = [(r_object,'k'),(r_object,'v')]
    _object_ = member
    def isTerminator(self, value):
        return type(value['k']) is TYPE_NULL

@pobject.define
class TYPE_CODE(pstruct.type):
    type = 'c'
    _fields_ = [
        (r_long, 'argcount'),
        (r_long, 'nlocals'),
        (r_long, 'stacksize'),
        (r_long, 'flags'),
        (r_object, 'code'),
        (r_object, 'consts'),
        (r_object, 'names'),
        (r_object, 'varnames'),
        (r_object, 'freevars'),
        (r_object, 'cellvars'),
        (r_object, 'filename'),
        (r_object, 'name'),
        (r_long, 'firstlineno'),
        (r_object, 'lnotab'),
    ]
@pobject.define
class TYPE_UNICODE(pstruct.type):
    type = 'u'
    _fields_ = [
        (r_long,'n'),
        (lambda s: dyn.clone(r_string, length=s['n'].li.int()), 'data'),
    ]
@pobject.define
class TYPE_UNKNOWN(r_unknown): type = '?'
@pobject.define
class TYPE_SET(pstruct.type):
    type = '<'
    _fields_ = [
        (r_long, 'n'),
        (lambda s: dyn.array(r_object, s['n'].li.int()), 'data'),
    ]
@pobject.define
class TYPE_FROZENSET(TYPE_SET): type = '>'

class FileCache(pstruct.type):
    '''.pyc files'''
    _fields_ = [
        (r_long, 'magic'),
        (r_long, 'something'),
        (r_object, 'object'),
    ]

### python natural types
class voidptr_t(ptype.pointer_t): _object_ = ptype.undefined
class methods_t(parray.type): length, _object_ = 0, ptype.undefined

class destructor(voidptr_t): pass
class printfunc(voidptr_t): pass
class getattrfunc(voidptr_t): pass
class setattrfunc(voidptr_t): pass
class cmpfunc(voidptr_t): pass
class reprfunc(voidptr_t): pass
class hashfunc(voidptr_t): pass
class ternaryfunc(voidptr_t): pass
class getattrofunc(voidptr_t): pass
class setattrofunc(voidptr_t): pass
class inquiry(voidptr_t): pass
class richcmpfunc(voidptr_t): pass
class getiterfunc(voidptr_t): pass
class iternextfunc(voidptr_t): pass
class descrgetfunc(voidptr_t): pass
class descrsetfunc(voidptr_t): pass
class initproc(voidptr_t): pass
class allocfunc(voidptr_t): pass
class newfunc(voidptr_t): pass
class freefunc(voidptr_t): pass

class _long(pint.sint32_t): pass
class _unsigned_int(pint.uint32_t): pass
class Py_ssize_t(pint.uint32_t): pass
class PyObject(ptype.undefined): pass
class PyNumberMethods(methods_t): length = 0
class PySequenceMethods(methods_t): length = 0
class PyMappingMethods(methods_t): length = 0
class PyBufferProcs(methods_t): length = 0
class PyMethodDef(methods_t): length = 0
class PyMemberDef(methods_t): length = 0
class PyGetSetDef(methods_t): length = 0

class _typeobject(pstruct.type):
    def __init__(self, **attrs):
        self._fields_ = f = []
        f.extend([
            (Py_ssize_t, 'ob_refcnt'),
            (dyn.pointer(_typeobject), 'ob_type'),
            (Py_ssize_t, 'ob_size'),
            (dyn.pointer(pstr.szstring), 'tp_name'),
            (Py_ssize_t, 'tp_basicsize'),
            (Py_ssize_t, 'tp_itemsize'),
            (destructor, 'tp_dealloc'),
            (printfunc, 'tp_print'),
            (getattrfunc, 'tp_getattr'),
            (setattrfunc, 'tp_setattr'),
            (cmpfunc, 'tp_compare'),
            (reprfunc, 'tp_repr'),
            (dyn.pointer(PyNumberMethods), 'tp_as_number'),
            (dyn.pointer(PySequenceMethods), 'tp_as_sequence'),
            (dyn.pointer(PyMappingMethods), 'tp_as_mapping'),
            (hashfunc, 'tp_hash'),
            (ternaryfunc, 'tp_call'),
            (reprfunc, 'tp_str'),
            (getattrofunc, 'tp_getattro'),
            (setattrofunc, 'tp_setattro'),
            (dyn.pointer(PyBufferProcs), 'tp_as_buffer'),
            (_long, 'tp_flags'),
            (dyn.pointer(pstr.szstring), 'tp_doc'),
            (traverseproc, 'tp_traverse'),
            (inquiry, 'tp_clear'),
            (richcmpfunc, 'tp_richcompare'),
            (Py_ssize_t, 'tp_weaklistoffset'),
            (getiterfunc, 'tp_iter'),
            (iternextfunc, 'tp_iternext'),
            (dyn.pointer(PyMethodDef), 'tp_methods'),
            (dyn.pointer(PyMemberDef), 'tp_members'),
            (dyn.pointer(PyGetSetDef), 'tp_getset'),
            (dyn.pointer(_typeobject), 'tp_base'),
            (dyn.pointer(PyObject), 'tp_dict'),
            (descrgetfunc, 'tp_descr_get'),
            (descrsetfunc, 'tp_descr_set'),
            (Py_ssize_t, 'tp_dictoffset'),
            (initproc, 'tp_init'),
            (allocfunc, 'tp_alloc'),
            (newfunc, 'tp_new'),
            (freefunc, 'tp_free'),
            (inquiry, 'tp_is_gc'),
            (dyn.pointer(PyObject), 'tp_bases'),
            (dyn.pointer(PyObject), 'tp_mro'),
            (dyn.pointer(PyObject), 'tp_cache'),
            (dyn.pointer(PyObject), 'tp_subclasses'),
            (dyn.pointer(PyObject), 'tp_weaklist'),
            (destructor, 'tp_del'),
            (_unsigned_int, 'tp_version_tag'),
        ])
        super(_typeobject, self).__init__(**attrs)

if __name__ == '__main__':
    pass
