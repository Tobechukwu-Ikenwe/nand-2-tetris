// Add.asm - simple test: 2 + 3
// Manually encoded: computes RAM[2] = 2 + 3 = 5 for assembler testing
@2
D=A
@3
D=D+A
@R2
M=D

(END)
@END
0;JMP
