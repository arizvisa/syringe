    .section .text

arch_detect:
    xorl %eax, %eax
    rex
    nop
    jnz determine_32_os

determine_64_os:
  mov %ds, %eax
  test %eax, %eax
  jnz win64_code
  jmp lin64_code

determine_32_os:
  mov %fs, %eax
  test %eax, %eax
  jz lin32_code

win32_code:
    jmp .
win64_code:
    jmp .

lin32_code:
    jmp .
lin64_code:
    jmp .
