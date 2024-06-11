import sys
from .base import *

class sbyte(signed_char): 'Small signed integer.'
class ubyte(unsigned_char): 'Small unsigned integer.'
class shalf(signed_short): 'Medium signed integer.'
class uhalf(unsigned_short): 'Medium unsigned integer.'
class sword(signed_int): 'Large signed integer.'
class uword(unsigned_int): 'Large unsigned integer.'
class xword(unsigned_long_long): 'Huge unsigned integer.'
class sxword(signed_long_long): 'Huge signed integer.'
class szstring(pstr.szstring): pass

class DW_EH_PE_size(ptype.definition):
    cache = {
        #0x00: ElfXX_Addr,
        0x01: ULEB128,
        0x02: uhalf,
        0x03: uword,
        0x04: xword,
        0x09: SLEB128,
        0x0A: shalf,
        0x0B: sword,
        0x0C: sxword,
    }

class DW_EH_PE_ptr(ptype.opointer_t):
    def summary(self):
        if self.value is None:
            return u"???"
        F, offset = getattr(self, '_calculate_', lambda ea: ea), self.int()
        ea = F(offset)
        if ea == offset:
            return u"*{:#x}".format(ea)
        return u"({:#x}) *{:#x}".format(offset, ea)

class DW_EH_PE_pcrel(DW_EH_PE_ptr):
    ''' Value is relative to the current program counter. '''
    type = 1
    def _calculate_(self, offset):
        return self.getoffset() + offset

class DW_EH_PE_textrel(DW_EH_PE_ptr):
    ''' Value is relative to the beginning of the .text section. '''
    type = 2
    def _calculate_(self, offset):
        # FIXME: get address of .text section
        dottext = 0
        #raise NotImplementedError
        return dottext + offset

class DW_EH_PE_datarel(DW_EH_PE_ptr):
    ''' Value is relative to the beginning of the .got or .eh_frame_hdr section. '''
    type = 3
    def _calculate_(self, offset):
        # FIXME: get address of .eh_frame_hdr section
        eh_frame_hdr = 0
        #raise NotImplementedError
        return eh_frame_hdr + offset

class DW_EH_PE_funcrel(DW_EH_PE_ptr):
    ''' Value is relative to the beginning of the function. '''
    type = 4
    def _calculate_(self, offset):
        # FIXME: get address of function(?)
        ea = 0
        #raise NotImplementedError
        return ea + offset

class DW_EH_PE_aligned(DW_EH_PE_ptr):
    ''' Value is aligned to an address unit sized boundary. '''
    type = 5
    def _calculate_(self, offset):
        # FIXME: get size of address unit
        asize = 0
        #raise NotImplementedError
        aligned, extra = divmod(offset, asize)
        return offset + asize - extra if extra else offset

class DW_EH_PE_(pbinary.struct):
    class _high(pbinary.enum):
        length, _values_ = 4, [
            ('pcrel', 0x1),     # Value is relative to the current program counter.
            ('textrel', 0x2),   # Value is relative to the beginning of the .text section.
            ('datarel', 0x3),   # Value is relative to the beginning of the .got or .eh_frame_hdr section.
            ('funcrel', 0x4),   # Value is relative to the beginning of the function.
            ('aligned', 0x5),   # Value is aligned to an address unit sized boundary.
            ('omit', 0xF),
        ]

    class _low(pbinary.enum):
        length, _values_ = 4, [
            ('absptr', 0x00),       # The Value is a literal pointer whose size is determined by the architecture.
            ('uleb128', 0x01),      # Unsigned value is encoded using the Little Endian Base 128 (LEB128) as defined by DWARF Debugging Information Format, Version 4.
            ('udata2', 0x02),       # A 2 bytes unsigned value.
            ('udata4', 0x03),       # A 4 bytes unsigned value.
            ('udata8', 0x04),       # An 8 bytes unsigned value.
            ('sleb128', 0x09),      # Signed value is encoded using the Little Endian Base 128 (LEB128) as defined by DWARF Debugging Information Format, Version 4.
            ('sdata2', 0x0A),       # A 2 bytes signed value.
            ('sdata4', 0x0B),       # A 4 bytes signed value.
            ('sdata8', 0x0C),       # An 8 bytes signed value.
            ('omit', 0x0F),
        ]

    _fields_ = [
        (_high, 'high'),
        (_low, 'low'),
    ]

    def pointer_class(self):
        hi = self.field('high')
        if hi['pcrel']:
            ptr_t = DW_EH_PE_pcrel
        elif hi['textrel']:
            ptr_t = DW_EH_PE_textrel
        elif hi['datarel']:
            ptr_t = DW_EH_PE_datarel
        elif hi['funcrel']:
            ptr_t = DW_EH_PE_funcrel
        elif hi['aligned']:
            ptr_t = DW_EH_PE_aligned
        else:
            raise NotImplementedError("{}".format(hi))

        # FIXME: fetch the target architecture to determine this pointer size
        if self.field('low')['absptr']:
            return ptr_t
        return ptr_t

    def pointer_encoding(self):
        return DW_EH_PE_size.lookup(self['low'])

    def pointer_type(self):
        pointer_t = self.pointer_class()
        class address(pointer_t):
            pass
        address.__name__ = address.__qualname__ = pointer_t.__name__
        address._value_ = self.pointer_encoding()
        return address

#class DW_CFA_(pint.enum):
#    _values_ = [
#        ('DW_CFA_nop', 0, 0, none, none),
#        ('DW_CFA_set_loc', 0, 0x01, address, none),
#        ('DW_CFA_advance_loc', 0x1, 0, delta, none),
#        ('DW_CFA_offset', 0x2, 0, register, ULEB128),
#        ('DW_CFA_restore', 0x3, 0, register, none),
#        ('DW_CFA_advance_loc1', 0, 0x02, ubyte, delta),
#        ('DW_CFA_advance_loc2', 0, 0x03, uhalf, delta),
#        ('DW_CFA_advance_loc4', 0, 0x04, uword, delta),
#        ('DW_CFA_offset_extended', 0, 0x05, ULEB128, register),
#        ('DW_CFA_restore_extended', 0, 0x06, ULEB128, register),
#        ('DW_CFA_undefined', 0, 0x07, ULEB128, register),
#        ('DW_CFA_same_value', 0, 0x08, ULEB128, register),
#        ('DW_CFA_register', 0, 0x09, ULEB128, register),
#        ('DW_CFA_remember_state', 0, 0x0a, none, none),
#        ('DW_CFA_restore_state', 0, 0x0b, none, none),
#        ('DW_CFA_def_cfa', 0, 0x0c, ULEB128, register),
#        ('DW_CFA_def_cfa_register', 0, 0x0d, ULEB128, register),
#        ('DW_CFA_def_cfa_offset', 0, 0x0e, ULEB128, offset),
#        ('DW_CFA_def_cfa_expression', 0, 0x0f, BLOCK, none),
#        ('DW_CFA_expression', 0, 0x10, ULEB128, register),
#        ('DW_CFA_offset_extended_sf', 0, 0x11, ULEB128, register),
#        ('DW_CFA_def_cfa_sf', 0, 0x12, ULEB128, register),
#        ('DW_CFA_def_cfa_offset_sf', 0, 0x13, SLEB128, offset),
#        ('DW_CFA_val_offset', 0, 0x14, ULEB128, ULEB128),
#        ('DW_CFA_val_offset_sf', 0, 0x15, ULEB128, SLEB128),
#        ('DW_CFA_val_expression', 0, 0x16, ULEB128, BLOCK),
#        ('DW_CFA_lo_user', 0, 0x1c, BLOCK, none),
#        ('DW_CFA_hi_user', 0, 0x3f, ULEB128, BLOCK),
#        ('DW_CFA_GNU_args_size', 0, 0x2e, ULEB128, none),              # The DW_CFA_GNU_args_size instruction takes an unsigned LEB128 operand representing an argument size. This instruction specifies the total of the size of the arguments which have been pushed onto the stack.
#        ('DW_CFA_GNU_negative_offset_extended', 0, 0x2f, ULEB128, ULEB128),              # The DW_CFA_def_cfa_sf instruction takes two operands: an unsigned LEB128 value representing a register number and an unsigned LEB128 which represents the magnitude of the offset. This instruction is identical to DW_CFA_offset_extended_sf except that the operand is subtracted to produce the offset. This instructions is obsoleted by DW_CFA_offset_extended_sf.
#    ]

# https://refspecs.linuxfoundation.org/LSB_5.0.0/LSB-Core-generic/LSB-Core-generic/ehframechpt.html
class augmentation_string(szstring):
    def has_data(self):
        res = self.serialize()
        return res and res[:1] == b'z'

    # FIXME: the fields described by this string are ordered
    #        by the character's position in the string.
    def has_language_specific(self):
        res = self.serialize()
        return res and res[:1] == b'z' and res.find(b'L') > 0
    def has_personality_routine(self):
        res = self.serialize()
        return res and res[:1] == b'z' and res.find(b'P') > 0
    def has_pointer_encoding(self):
        res = self.serialize()
        return res and res[:1] == b'z' and res.find(b'R') > 0

class augmentation_data(pstruct.type):
    def __data(self):
        length = self['length'].li
        try:
            string = getattr(self, '_augmentation_string_', '')
            result = self._augmentation_(string.object if isinstance(string, pbinary.partial) else string, length.int())
        except NotImplementedError:
            result = ptype.block
        return result

    def __padding(self):
        length = self['length'].li.int()
        data = self['data'].li
        return dyn.block(max(0, length - data.size())) if length > data.size() else ptype.block

    _fields_ = [
        (ULEB128, 'length'),
        (__data, 'data'),
        (__padding, 'padding'),
    ]

    _augmentation_string_ = None
    def _augmentation_(self, string, length):
        raise NotImplementedError

class cie_augmentation_data(augmentation_data):
    def _augmentation_(self, string, length):
        assert(isinstance(string, augmentation_string))
        # FIXME: these fields are order-specific
        if string.has_pointer_encoding():
            return DW_EH_PE_
        elif string.has_language_specific():
            return DW_EH_PE_
        elif string.has_personality_routine():
            return DW_EH_PE_
        raise NotImplementedError(string)

    # FIXME: the 'data' field "should" be an array, which would mean that we would
    #        search for the pointer encoding to return. however, it currently isn't
    #        defined as such and so calling it like this is really a hack.
    def pointer_encoding(self):
        data = self['data'].object if isinstance(self['data'], pbinary.partial) else self['data']
        if not isinstance(data, DW_EH_PE_):
            raise NotImplementedError
            return ptype.pointer_t
        return self['data'].pointer_encoding()
    def pointer_size(self):
        return self['data'].pointer_size()
    def pointer_type(self):
        return self['data'].pointer_type()

class Entry(pstruct.type):
    def __padding(self):
        res = self['length'].li
        length = self['extended_length'].li if res.int() in {0xffffffff} else res
        return dyn.block(max(0, length.int() - self['entry'].li.size()))

    _fields_ = [
        (uword, 'length'),
        (lambda self: xword if self['length'].li.int() == 0xffffffff else pint.uint_t, 'extended_length'),
        (lambda self: getattr(self, '_object_', ptype.block) if self['length'].li.int() else ptype.block, 'entry'),
        (__padding, 'padding'),
    ]

    def pointer_encoding(self):
        return self['entry'].pointer_encoding()
    def pointer_size(self):
        return self['entry'].pointer_size()
    def pointer_type(self):
        return self['entry'].pointer_type()

class CIE_Entry(pstruct.type):
    def __return_address_register(self):
        res = self['version'].li
        if res.int() == 1:
            return ubyte
        elif res.int() == 3:
            return ULEB128
        return pint.uint_t

    def __augmentation_data(self):
        res = self['augmentation'].li
        if res.has_data():
            return dyn.clone(cie_augmentation_data, _augmentation_string_=res)
        return ptype.block

    #def __padding(self):
    #    res, fields = self['length'].li, ['extended_length', 'CIE_id', 'version', 'augmentation', 'code_alignment_factor', 'data_alignment_factor', 'return_address_register', 'augmentation_data', 'initial_instructions']
    #    length = self['extended_length'].li if res.int() in {0xffffffff} else res
    #    return dyn.block(max(0, length.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        #(uword, 'length'),
        #(lambda self: xword if self['length'].li.int() == 0xffffffff else pint.uint_t, 'extended_length'),
        (uword, 'CIE_id'),
        (ubyte, 'version'),
        (augmentation_string, 'augmentation'),
        (ULEB128, 'code_alignment_factor'),
        (LEB128, 'data_alignment_factor'),
        (__return_address_register, 'return_address_register'),
        (__augmentation_data, 'augmentation_data'),
        (ptype.block, 'initial_instructions'),
        #(__padding, 'padding'),
    ]

    @property
    def pointer_encoding(self):
        augmentation = self['augmentation_data']
        if not isinstance(augmentation, augmentation_data):
            raise NotImplementedError
            return ptype.pointer_t
        return augmentation.pointer_encoding() 
    @property
    def pointer_type(self):
        augmentation = self['augmentation_data']
        if not isinstance(augmentation, augmentation_data):
            raise NotImplementedError
            return ptype.pointer_t
        return augmentation.pointer_type() 

class CIE(Entry):
    _object_ = CIE_Entry

class CIE_pointer(DW_EH_PE_ptr):
    _value_, _object_ = uword, CIE
    def _calculate_(self, negative_offset):
        return self.getoffset() - negative_offset

class LSDA(ptype.block):
    pass

class fde_augmentation_data(augmentation_data):
    def _augmentation_(self, string, length):
        assert(isinstance(string, augmentation_string)), string
        # FIXME: these fields are order-specific
        if string.has_pointer_encoding():
            return ptype.undefined

        # FIXME: grabbing the CIE from here is pretty inefficient.
        p = self.getparent(FDE_Entry)
        cie = p['entry']['CIE_pointer'].d.li
        pointer_t = cie.pointer_type
        if string.has_language_specific():
            return dyn.clone(pointer_t, _object_=LSDA)
        elif string.has_personality_routine():
            return dyn.clone(pointer_t, _object_=void)
        raise NotImplementedError(string)
    
class FDE_Entry(pstruct.type):
    def __address(self):
        cie = self['CIE_pointer'].li and self['CIE_pointer'].d.li
        return cie.pointer_type

    def __address_size(self):
        cie = self['CIE_pointer'].li and self['CIE_pointer'].d.li
        return cie.pointer_encoding

    def __augmentation_data(self):
        cie = self['CIE_pointer'].li and self['CIE_pointer'].d.li
        augmentation = cie['entry']['augmentation']
        if augmentation.has_data():
            return dyn.clone(fde_augmentation_data, _augmentation_string_=augmentation)
        return ptype.block

    #def __padding(self):
    #    res, fields = self['length'].li, ['extended_length', 'CIE_pointer', 'pc_begin', 'pc_range', 'augmentation_data', 'CFI']
    #    length = self['extended_length'].li if res.int() in {0xffffffff} else res
    #    return dyn.block(max(0, length.int() - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        #(uword, 'length'),
        #(lambda self: xword if self['length'].li.int() == 0xffffffff else pint.uint_t, 'extended_length'),
        (CIE_pointer, 'CIE_pointer'),
        (__address, 'pc_begin'),
        (__address_size, 'pc_range'),
        (__augmentation_data, 'augmentation_data'),
        (ptype.block, 'CFI'),
        #(__padding, 'padding'),
    ]

class FDE(Entry):
    _object_ = FDE_Entry

class fde_table_entry(pstruct.type):
    def __encoded_pointer(self):
        return self._object_
    _fields_ = [
        (__encoded_pointer, 'fst'),
        (__encoded_pointer, 'snd'),
    ]

class eh_frame_hdr(pstruct.type):
    def __address(self):
        res = self['eh_frame_ptr_enc'].li
        pointer_t = res.pointer_type()
        return dyn.clone(pointer_t, _object_=eh_frame)

    def __address_size(self):
        res = self['fde_count_enc'].li
        return res.pointer_encoding()

    def __fde_table(self):        
        res, count = (self[fld].li for fld in ['table_enc', 'fde_count'])
        pointer_t = res.pointer_type
        entry_t = dyn.clone(fde_table_entry, _object_=pointer_t)
        return dyn.array(entry_t, count.int())
    
    _fields_ = [
        (ubyte, 'version'),
        (DW_EH_PE_, 'eh_frame_ptr_enc'),
        (DW_EH_PE_, 'fde_count_enc'),
        (DW_EH_PE_, 'table_enc'),
        (__address, 'eh_frame_ptr'),    # encoded
        (__address_size, 'fde_count'),  # encoded
        (__fde_table, 'fde_table'),
    ]

class eh_frame(parray.terminated):
    _object_ = lambda self: FDE if self.value else CIE
    def isTerminator(self, value):
        return not value['length'].int()

if __name__ == '__main__':
    import sys, elf

    source = ptypes.setsource(ptypes.prov.file(sys.argv[1], 'rb'))
    z = elf.File(source=source)
    z = z.l

    phdrs = z['e_data']['e_phoff'].d
    phdrs = phdrs.l

    phdr = phdrs.by('GNU_EH_FRAME')
    pdata = phdr['p_offset'].d.l

    eh = pdata.new(eh_frame_hdr, offset=pdata.getoffset())
    eh = eh.l
    print(eh)

    fp = eh['eh_frame_ptr'].d
    fp = fp.l
    print(fp)

    sys.exit(0)
