// Mult.asm - Multiplies R0 and R1, stores result in R2
// R2 = R0 * R1  (R0, R1 >= 0)
// Uses repeated addition loop

// R2 = 0
@R2
M=0

// if R0 == 0, jump to END
@R0
D=M
@END
D;JEQ

// if R1 == 0, jump to END
@R1
D=M
@END
D;JEQ

// counter = R1
@R1
D=M
@counter
M=D

(LOOP)
    // R2 = R2 + R0
    @R2
    D=M
    @R0
    D=D+M
    @R2
    M=D

    // counter--
    @counter
    M=M-1
    D=M

    // if counter > 0 goto LOOP
    @LOOP
    D;JGT

(END)
@END
0;JMP
