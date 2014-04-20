
section .data

_print_number:
    db "%I64d",10,0

_print_divide:
    db "%I64x / %I64x = %I64x",10,0

_print_sdivide:
    db "%I64d / %I64d = %I64d",10,0

_print_remainder:
    db "%I64d %% %I64d = %I64x",10,0
_print_sremainder:
    db "%I64d %% %I64d = %I64d\n",0

section .text
    extern printf

%macro signedmul 2
    mov rax, %1
    mov rdx, %2
    imul rax,rdx

    mov rdx,rax
    mov rcx, _print_number
    call printf
%endmacro

%macro signeddiv 2
    push r12
    push r13

    mov r12,%1
    mov r13,%2

    mov rax,r12
    cqo

    idiv r13

    mov r9, rax
    mov r8, r13
    mov rdx, r12
    mov rcx, _print_divide
    call printf

    pop r13
    pop r12
%endmacro

%macro signeddivi 2
    push r12
    push r13

    mov r12,%1
    mov r13,%2

    mov rax,r12
    cqo

    idiv r13

    mov r9, rax
    mov r8, r13
    mov rdx, r12
    mov rcx, _print_sdivide
    call printf

    pop r13
    pop r12
%endmacro

%macro signedmod 2
    push r12
    push r13

    mov r12,%1
    mov r13,%2

    mov rax,r12
    cqo

    idiv r13

    mov r9, rdx
    mov r8, r13
    mov rdx, r12
    mov rcx, _print_remainder
    call printf

    pop r13
    pop r12
%endmacro

%macro signedmodi 2
    push r12
    push r13

    mov r12,%1
    mov r13,%2

    mov rax,r12
    cqo

    idiv r13

    mov r9, rdx
    mov r8, r13
    mov rdx, r12
    mov rcx, _print_sremainder
    call printf

    pop r13
    pop r12
%endmacro

    global main
main:
    sub rsp, 0x20   ; 8*4 reg args

    signedmul 4,4
    signedmul 4,-4

    signeddivi 0x10,-0x10

    signeddivi 0xffffffffffffa251,0x00000000000000c1
    signeddivi 0xffffffffffff1634,0x00000000000000ad

    signedmod 4,4
    signedmod 4,3

    signedmod 0xffffffffffffa251,0x00000000000000c1
    signedmod 0xffffffffffff1634,0x00000000000000ad
    signedmodi 0xffffffffffffa251,0x00000000000000c1
    signedmodi 0xffffffffffff1634,0x00000000000000ad

    add rsp, 0x20
    ret

