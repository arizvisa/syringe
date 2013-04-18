from ptypes import *
from primitives import *

class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class s24(pint.sint_t): length = 3
class d64(pfloat.double): pass

## variable length encoding...from the docs..
# The variable-length encoding for u30, u32, and s32 uses one to five bytes, depending on the magnitude of the value encoded. Each byte contributes its low seven bits to the value. If the high (eighth) bit of a byte is set, then the next byte of the abcFile is also part of the value. In the case of s32, sign extension is applied: the seventh bit of the last byte of the encoding is propagated to fill out the 32-bits of the decoded value.

# wtf, does this mean we're always a 35-bit number, discarding 3?
import bitmap
class _vle(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [
            (1, 'continue'),
            (7, 'value')
        ]

    length = 5
    def isTerminator(self, value):
        if value['continue'] == 0:
            return True
        return False

    def getbitmap(self):
        '''returns the array converted to a bitmap'''
        result = bitmap.new(0,0)
        for n in self:
            result = bitmap.insert(result, (n['value'], 7))

        # clamp to 32-bits...
        if result[1] > 32:
            result,v = bitmap.shift(result, result[1] - 32)
            if v != 0:
                print '%s -> some unexpected bits were set'% self.name()
        return result

    def __repr__(self):
        n = int(self)
        bmp = self.getbitmap()
        return ' '.join([self.name(), bitmap.repr(bmp), bitmap.string(bmp)])

class u30(_vle):
    def __int__(self):
        n = self.getbitmap()
        # clamp to 30-bits...
        if n[1] > 30:
            n = bitmap.shrink(n, n[1] - 30)
        return n[0]

class u32(_vle):
    def __int__(self):
        n = self.getbitmap()
        return n[0]

class s32(_vle):
    def __int__(self):
        n = self.getbitmap()
        n, sign = bitmap.shift(n, 1)
        return [1, -1][ sign ] * (n[0]&0x7fffffff)
###
class string_info(pstruct.type):
    _fields_ = [
        (u30, 'size'),
        (lambda s: dyn.clone(pstr.string, length=s['size'].l.number()), 'utf8')
    ]
    def __repr__(self):
        return ' '.join([self.name(), self.get()])

    def get(self):
        return self['utf8'].serialize()

class namespace_info(pstruct.type):
    class __kind(pint.enum, u8):
        _values_ = [
            ('Namespace', 0x08),
            ('PackageNamespace', 0x16),
            ('PackageInternalNs', 0x17),
            ('ProtectedNamespace', 0x18),
            ('ExplicitNamespace', 0x19),
            ('StaticProtectedNs', 0x1a),
            ('PrivateNs', 0x05),
        ]
    _fields_ = [
        (__kind, 'kind'),
        (u30, 'name')
    ]

    def getname(self):
        n = int(self['name'])
        if n == 0:
            return ''
        parent = self.getparent(cpool_info)
        return parent['string'][n - 1].get()

    def __repr__(self):
        s = self.getname()
        return ' -> '.join([self.name(), self['kind'].get(), repr(s)])

class ns_set_info(pstruct.type):
    _fields_ = [
        (u30, 'count'),
        (lambda s: dyn.array(u30, s['count'].l.number()), 'ns')
    ]

    def __repr__(self):
        l = len(self['ns'])
        parent = self.getparent(cpool_info)
        sets = repr([ int(x) for x in self['ns'] ])
        return ' '.join([self.name(), sets])

###
class MultiNameTypes(ptype.definition):
    cache = {}

class multiname_kind_QName(pstruct.type):
    type = 0x07
    _fields_ = [(u30, 'ns'), (u30, 'name')]
    def __repr__(self):
        return ' '.join([self.name(), self.get()])

    def get(self):
        parent = self.getparent(cpool_info)
        a,b = int(self['ns']), int(self['name'])
        ns,name = '*', '*'
        if a > 0:
            ns = parent['string'][a-1]
        if b > 0:
            name = parent['string'][b-1]
        return '%s.%s'% (ns.get(), name.get())

class multiname_kind_QNameA(multiname_kind_QName):
    type = 0x0d

class multiname_kind_RTQName(pstruct.type):
    type = 0x0f
    _fields_ = [(u30, 'name')]
    def __repr__(self):
        return ' '.join([self.name(), self.get()])

    def get(self):
        parent = self.getparent(cpool_info)
        a = int(self['name'])
        name = '*'
        if a > 0:
            name = parent['string'][a-1]
        return name.get()

class multiname_kind_RTQNameA(multiname_kind_RTQName):
    type = 0x10
class multiname_kind_RTQNameL(pstruct.type):
    type = 0x11
class multiname_kind_Multiname(pstruct.type):
    type = 0x09
    _fields_ = [(u30, 'name'),(u30, 'ns_set')]
    def __repr__(self):
        b = int(self['ns_set'])
        parent = self.getparent(cpool_info)

        if b == 0:
            print 'wtf'

        if b > 0:
            b -= 1

        nsset = repr(parent['ns_set'][b])
        return ' '.join([self.name(), self.get(), nsset])

    def get(self):
        a,b = int(self['name']),int(self['ns_set'])
        parent = self.getparent(cpool_info)
        name = '*'
        if a > 0:
            name = parent['string'][a - 1].get()
        return name

class multiname_kind_MultinameL(pstruct.type):
    type = 0x1b
    _fields_ = [(u30, 'ns_set')]
    def __repr__(self):
        s = int(self['ns_set'])
        nssets = self.getparent(cpool_info)['ns_set']
        return ' '.join([self.name(), repr(nssets[s])])

class multiname_kind_MultinameLA(multiname_kind_MultinameL):
    type = 0x1c

class multiname_kind_MultinameA(multiname_kind_Multiname):
    type = 0x0e

MultiNameTypes.define(multiname_kind_QName)
MultiNameTypes.define(multiname_kind_QNameA)
MultiNameTypes.define(multiname_kind_RTQName)
MultiNameTypes.define(multiname_kind_RTQNameA)
MultiNameTypes.define(multiname_kind_Multiname)
MultiNameTypes.define(multiname_kind_MultinameL)
MultiNameTypes.define(multiname_kind_MultinameLA)
MultiNameTypes.define(multiname_kind_MultinameA)

class multiname_info(pstruct.type):
    class __kind(pint.enum, u8):
        _values_ = [
            ('QName', 0x07),
            ('QNameA', 0x0d),
            ('RTQName', 0x0f),
            ('RTQNameA', 0x10),
            ('RTQNameL', 0x11),
            ('RTQNameLA', 0x12),
            ('Multiname', 0x09),
            ('MultinameA', 0x0e),
            ('MultinameL', 0x1b),
            ('MultinameLA', 0x1c),
        ]

    def __data(self):
        return MultiNameTypes.lookup( int(self['kind'].l) )

    _fields_ = [
        (__kind, 'kind'),
        (__data, 'data'),
    ]

    def __repr__(self):
        return ' '.join([self.name(), repr(self['data'])])

class option_detail(pstruct.type):
    _fields_ = [
        (u30, 'val'),
        (u8, 'kind')
    ]

class option_info(pstruct.type):
    _fields_ = [
        (u30, 'option_count'),
        (lambda s: dyn.array(option_detail, int(s['option_count'])), 'option')
    ]

class param_info(pstruct.type):
    _fields_ = [
        (lambda s: dyn.array(u30, int(s.parent['param_count'])), 'param_name')
    ]

class method_info(pstruct.type):
    class __flags(pbinary.struct):
        _fields_ = [
            (1, 'NEED_ARGUMENTS'),
            (1, 'NEED_ACTIVATION'),
            (1, 'NEED_REST'),
            (1, 'HAS_OPTIONAL'),
            (2, 'reserved'),
            (1, 'SET_DXNS'),
            (1, 'HAS_PARAM_NAMES'),
        ]

    def __option_info(self):
        if self['flags']['HAS_OPTIONAL']:
            return option_info
        return ptype.type
    def __param_names(self):
        if self['flags']['HAS_PARAM_NAMES']:
            return param_info
        return ptype.type

    _fields_ = [
        (u30, 'param_count'),
        (u30, 'return_type'),
        (lambda s: dyn.array(u30, s['param_count'].number()), 'param_type'),
        (u30, 'name'),
        (__flags, 'flags'),
        (__option_info, 'options'),
        (__param_names, 'param_names'),
    ]

class item_info(pstruct.type):
    _fields_ = [(u30, 'key'),(u30,'value')]

class metadata_info(pstruct.type):
    _fields_ = [
        (u30, 'name'),
        (u30, 'item_count'),
        (lambda s: dyn.array(item_info, int(s['item_count'])), 'items')
    ]

class TraitTypes(ptype.definition):
    cache = {}

class traits_info(pstruct.type):
    def __data(self):
        kind = self['kind'].l
        return TraitTypes.lookup(kind['k'])

    class __kind(pbinary.struct):
        _fields_ = [(4,'a'),(4,'k')]

    def __metadata_count(self):
        if self['kind']['a'] == 4:
            return u30
        return ptype.type

    def __metadata(self):
        if self['kind']['a'] == 4:
            return dyn.array(u30, int(self['metadata_count']))
        return ptype.type

    _fields_ = [
        (u30, 'name'),
        (__kind, 'kind'),
        (__data, 'data'),
        (__metadata_count, 'metadata_count'),
        (__metadata, 'metadata'),
    ]

    def __repr__(self):
        parent = self.getparent(abcFile)['constant_pool']
        n = int(self['name'])

        multiname = parent['multiname'][n]['data'].get()
        data = self['data']
        metadata = self['metadata']
        return ' '.join([self.name(), '%s<%x>'%(multiname,n), repr(data)])

class trait_slot(pstruct.type):
    class __vkind(pint.enum, u8):
        _values_ = [
            ('Int', 0x03),
            ('Uint', 0x04),
            ('Double', 0x06),
            ('Utf8', 0x01),
            ('True', 0x0b),
            ('False', 0x0a),
            ('Null', 0x0c),
            ('Undefined', 0x00),

            ('Namespace', 0x08),
            ('PackageNamespace', 0x16),
            ('PackageInternalNs', 0x17),
            ('ProtectedNamespace', 0x18),
            ('ExplicitNamespace', 0x19),
            ('StaticProtectedNs', 0x1a),
            ('PrivateNs', 0x05),
        ]

        _namespace_ = {
            3 : 'integer',
            4 : 'uinteger',
            6 : 'double',
            1 : 'string',

            8 : 'namespace',
            0x16 : 'namespace',
            0x17 : 'namespace',
            0x18 : 'namespace',
            0x19 : 'namespace',
            0x1a : 'namespace',
            5 : 'namespace',
        }

    _fields_ = [
        (u30, 'slot_id'),
        (u30, 'type_name'),
        (u30, 'vindex'),
        (__vkind, 'vkind'), # XXX: only exists when vindex is nonzero
    ]

    def get(self):
        parent = self.getparent(abcFile)['constant_pool']
        n = int(self['type_name'])
        name = '*'
        if n > 0:
            name = parent['multiname'][n-1]
        return name

    def getvalue(self):
        k,v = int(self['vkind']), int(self['vindex'])
        if k == 0xb:
            return True
        if k == 0xa:
            return False
        if k == 0xc:        # Null
            return None
        if k == 0:          # Undefined
            return None

        ns = self['vkind']._namespace_[k]
        parent = self.getparent(abcFile)
        if v > 0:
            return parent[ns][v-1]
        return None

    def __repr__(self):
        slid = int(self['slot_id'])
        vindex = int(self['vindex'])
        return ' '.join([ self.name(), self.get(), self['vkind'].get(), repr(self.getvalue())])

class trait_class(pstruct.type):
    _fields_ = [
        (u30, 'slot_id'),
        (u30, 'classi'),
    ]
class trait_function(pstruct.type):
    _fields_ = [
        (u30, 'slot_id'),
        (u30, 'function'),
    ]
class trait_method(pstruct.type):
    _fields_ = [
        (u30, 'disp_id'),
        (u30, 'method'),
    ]

class Trait_Slot(trait_slot): type = 0
class Trait_Method(trait_method): type = 1
class Trait_Getter(trait_method): type = 2
class Trait_Setter(trait_method): type = 3
class Trait_Class(trait_class): type = 4
class Trait_Function(trait_function): type = 5
class Trait_Const(trait_slot): type = 6

TraitTypes.define(Trait_Slot)
TraitTypes.define(Trait_Method)
TraitTypes.define(Trait_Getter)
TraitTypes.define(Trait_Setter)
TraitTypes.define(Trait_Class)
TraitTypes.define(Trait_Function)
TraitTypes.define(Trait_Const)

class instance_info(pstruct.type):
    def _row(type, fieldlength):
        def fn(self):
            s = self[fieldlength].number()
            if s > 0:
                s -= 1
            return dyn.array(type, s)
        return fn

    class __flags(pbinary.struct):
        _fields_ = [
            (4, 'reserved'),
            (1, 'ClassProtectedNs'),
            (1, 'ClassInterface'),
            (1, 'ClassFinal'),
            (1, 'ClassSealed'),
        ]

    def __protectedNs(self):
        if self['flags']['ClassProtectedNs']:
            return u30
        return ptype.type

    _fields_ = [
        (u30, 'name'),
        (u30, 'super_name'),
        (__flags, 'flags'),
        (__protectedNs, 'protectedNs'),
        (u30, 'intrf_count'),
        (_row(u30, 'intrf_count'), 'interface'),
        (u30, 'iinit'),
        (u30, 'trait_count'),
        (_row(traits_info, 'trait_count'), 'trait'),
    ]

class class_info(pstruct.type):
    _fields_ = [
        (u30, 'cinit'),
        (u30, 'trait_count'),
        (lambda s: dyn.array(traits_info, s['trait_count'].l.number()), 'traits')
    ]

class script_info(pstruct.type):
    _fields_ = [
        (u30, 'init'),
        (u30, 'trait_count'),
        (lambda s: dyn.array(traits_info, s['trait_count'].l.number()), 'traits')
    ]

class exception_info(pstruct.type):
    _fields_ = [
        (u30, 'from'),
        (u30, 'to'),
        (u30, 'target'),
        (u30, 'exc_type'),
        (u30, 'var_name'),
    ]

class method_body_info(pstruct.type):
    _fields_ = [
        (u30, 'method'),
        (u30, 'max_stack'),
        (u30, 'local_count'),
        (u30, 'init_scope_depth'),
        (u30, 'max_scope_depth'),
        (u30, 'code_length'),
        (lambda s: dyn.block(s['code_length'].l.number()), 'code'),
        (u30, 'exception_count'),
        (lambda s: dyn.array(exception_info, s['exception_count'].l.number()), 'exception'),
        (u30, 'trait_count'),
        (lambda s: dyn.array(traits_info, s['trait_count'].l.number()), 'trait'),
    ]

###
class cpool_info(pstruct.type):
    def _row(type, fieldlength):
        def fn(self):
            s = self[fieldlength].number()
            if s > 0:
                s -= 1
            return dyn.array(type, s)
        return fn

    _fields_ = [
        (u30, 'int_count'),
        (_row(s32, 'int_count'), 'integer'),
        (u30, 'uint_count'),
        (_row(u32, 'uint_count'), 'uinteger'),
        (u30, 'double_count'),
        (_row(d64, 'double_count'), 'double'),
        (u30, 'string_count'),
        (_row(string_info, 'string_count'), 'string'),
        (u30, 'namespace_count'),
        (_row(namespace_info, 'namespace_count'), 'namespace'),
        (u30, 'ns_set_count'),
        (_row(ns_set_info, 'ns_set_count'), 'ns_set'),
        (u30, 'multiname_count'),
        (_row(multiname_info, 'multiname_count'), 'multiname')
    ]

###
class abcFile(pstruct.type):
    def _row(type, fieldlength):
        def fn(self):
            s = self[fieldlength].number()
            return dyn.array(type, s)
        return fn

    _fields_ = [
        (u16, 'minor_version'),
        (u16, 'major_version'),
        (cpool_info, 'constant_pool'),
        (u30, 'method_count'),
        (_row(method_info, 'method_count'), 'method'),
        (u30, 'metadata_count'),
        (_row(metadata_info, 'metadata_count'), 'metadata'),
        (u30, 'class_count'),
        (_row(instance_info, 'class_count'), 'instance'),
        (_row(class_info, 'class_count'), 'class'),
        (u30, 'script_count'),
        (_row(script_info, 'script_count'), 'script'),
        (u30, 'method_body_count'),
        (_row(method_body_info, 'method_body_count'), 'method_body'),
    ]

if __name__ == '__file__':
    z = u30()
