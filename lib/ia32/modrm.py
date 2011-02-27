import decoder

def decode(instruction):
    '''Extract the modrm tuple out of the provided instruction'''
    modrm = instruction[2]
    if len(modrm) > 0:
        modrm = decoder.decodeInteger(modrm)
        return decoder.extractmodrm(modrm)
    return None
extract = decode

def isSib(modrm):
    '''[sib],[sib+u8], or [sib+u32]'''
    mod,reg,rm = modrm
    return mod != 3 and rm == 4

def isMemory(modrm):
    '''[address]'''
    mod,reg,rm = modrm
    return mod == 0 and rm == 5

def isRegister(modrm):
    '''reg'''
    mod,reg,rm = modrm
    return mod == 3

def isMemoryRegister(modrm):
    '''[reg]'''
    mod,reg,rm = modrm
    return mod == 0

def isMemoryRegisterPlusByte(modrm):
    '''[reg+u8]'''
    mod,reg,rm = modrm
    return mod == 1

def isMemoryRegisterPlusDword(modrm):
    '''[reg+u32]'''
    mod,reg,rm = modrm
    return mod == 2

### reg bits
reg_8 = {
    0 : 'al', 1 : 'cl', 2 : 'dl', 3 : 'bl',
    4 : 'ah', 5 : 'ch', 6 : 'dh', 7 : 'bh',
}
reg_16 = {
    0 : 'ax', 1 : 'cx', 2 : 'dx', 3 : 'bx',
    4 : 'sp', 5 : 'bp', 6 : 'si', 7 : 'di',
}
reg_32 = {
    0 : 'eax', 1 : 'ecx', 2 : 'edx', 3 : 'ebx',
    4 : 'esp', 5 : 'ebp', 6 : 'esi', 7 : 'edi',
}
reg_mmx = {
    0 : 'mm0', 1 : 'mm1', 2 : 'mm2', 3 : 'mm3',
    4 : 'mm4', 5 : 'mm5', 6 : 'mm6', 7 : 'mm7',
}
reg_xmm = {
    0 : 'xmm0', 1 : 'xmm1', 2 : 'xmm2', 3 : 'xmm3',
    4 : 'xmm4', 5 : 'xmm5', 6 : 'xmm6', 7 : 'xmm7',
}

### now invert them because i'm an asshole
for d in (reg_8, reg_16, reg_32, reg_mmx, reg_xmm):
    d.update( dict(((v,k) for k,v in d.items())) )

### mod/rm bits
mod_8 = dict(reg_8)
mod_8[4] = None
mod_8[5] = None

mod_16 = dict(reg_16)
mod_16[4] = None

mod_32 = dict(reg_32)
mod_16[4] = None
