.section .text

### constants
word=4
halfword=word/2
byte=halfword/2

## data tables
_optable:
    .incbin "_optable.bin"

_prefix:
    # 11 prefixes here
    .string "\x26\x2e\x36\x3e\x64\x65\x66\x67\xf0\xf2\xf3"

##############################################################################
## this should decode the optable and then extract a byte from it
# input: %esi=pointer to opcode
# output: %eax=optable entry
op_fetch:
    pushl %esi
    pushl %ebx
    andl $0xff,%eax
    movb (%esi),%al
    movl _optable,%ebx

    cmpb $0x0f,%al
    .byte 0x3e
    jne 1f

    incl %esi
    addl $0x100,%ebx
    movb (%esi),%al

1:
    movb (%ebx,%eax,1),%al
    andl %eax, 0xff
    popl %ebx
    popl %esi
    ret

##############################################################################
# input: %eax=optable entry
# output: %eax=1 if true
op_hasmodrm:
    and $0x80,%eax
    shrl $7,%eax
    ret
op_hasimm:
    and $0x40,%eax
    shrl $6,%eax
    ret

##############################################################################
#input: %eax=optable entry,%ebx=has size prefix
#output: %eax=length of immediate value
op_getimm16:
    andl $0x3f,%eax
    andl %ebx,%ebx
    jnz _op_getimm_ext
    jmp _op_getimm_reg

op_getimm32:
    andl $0x3f,%eax
    andl %ebx,%ebx
    jnz _op_getimm_reg
    jmp _op_getimm_ext

_op_imm_extended:
    .long halfword+word,word*2,word,halfword,byte,halfword
_op_imm_regular:
    .long word,halfword,word*2,word,halfword,2*word

_op_getimm_ext:
    pushl %ebx
    movl _op_imm_extended,%ebx
    jmp 1f
_op_getimm_reg:
    pushl %ebx
    movl _op_imm_regular,%ebx
1:
    cmpl $0x3a,%eax
    jb 1f
    subl $0x3a,%eax
    leal (%ebx,%eax,4), %eax
    movl (%eax),%eax
1:
    popl %ebx
    ret

##############################################################################
# input: %eax=modrm
op_getdisp16:
    jmp _op_getdisp_ext
op_getdisp32:
    jmp _op_getdisp_reg

_op_disp_extended:
    .long 0,byte,halfword,0
_op_disp_regular:
    .long 0,byte,word,0

_op_getdisp_ext:
    pushl %ebx
    movl _op_disp_extended,%ebx
    jmp 1f
_op_getdisp_reg:
    pushl %ebx
    movl _op_imm_regular,%ebx
1:
    andl $0xc0,%eax
    shrl $6,%eax
    leal (%ebx,%eax,4), %eax
    movl (%eax),%eax
    popl %ebx
    ret

.global decode
decode:
	
	
