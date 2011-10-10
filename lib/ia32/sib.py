import decoder

def decode(instruction):
    '''Extract the modrm tuple out of the provided instruction'''
    modrm = instruction[2]
    if len(modrm) > 0:
        modrm = decoder.decodeInteger(modrm)
        return decoder.extractsib(modrm)
    return None
extract = decode

reg_index = {
    0 : 'eax', 1 : 'ecx', 2 : 'edx', 3 : 'ebx',
    4 :  None, 5 : 'ebp', 6 : 'esi', 7 : 'edi'
}

reg_base = {
    0 : 'eax', 1 : 'ecx', 2 : 'edx', 3 : 'ebx',
    4 : 'esp', 5 :  None, 6 : 'esi', 7 : 'edi'
}
