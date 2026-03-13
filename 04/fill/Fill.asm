// Fill.asm - Screen fill program
// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the entire screen.
// When no key is pressed, the program clears the screen.

(LOOP)
    // Read keyboard
    @KBD
    D=M

    // if key pressed, fill black
    @FILL_BLACK
    D;JNE

    // else fill white
    @FILL_WHITE
    0;JMP

(FILL_BLACK)
    @color
    M=-1        // -1 = 0xFFFF (all ones = black)
    @DRAW
    0;JMP

(FILL_WHITE)
    @color
    M=0         // 0 = white
    @DRAW
    0;JMP

(DRAW)
    // i = 8192 (256 rows * 32 words/row = 8192 words)
    @8192
    D=A
    @i
    M=D

    @SCREEN
    D=A
    @addr
    M=D

(DRAW_LOOP)
    // if i == 0, goto LOOP
    @i
    D=M
    @LOOP
    D;JEQ

    // Screen[addr] = color
    @color
    D=M
    @addr
    A=M
    M=D

    // addr++
    @addr
    M=M+1

    // i--
    @i
    M=M-1

    @DRAW_LOOP
    0;JMP
