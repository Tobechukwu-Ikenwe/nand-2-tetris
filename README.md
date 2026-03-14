# Nand2Tetris — Full Implementation

A complete implementation of the **Nand to Tetris** course (nand2tetris.org),
building a modern 16-bit computer from first principles — from NAND gates to a
working operating system and Jack compiler.

---

## Project Structure

```
nand-2-tetris/
├── 01/            # Project 1: Boolean Logic (15 HDL chips)
├── 02/            # Project 2: Boolean Arithmetic (ALU + adders)
├── 03/
│   ├── a/         # Project 3a: Bit, Register, RAM8, RAM64, PC
│   └── b/         # Project 3b: RAM512, RAM4K, RAM16K
├── 04/
│   ├── mult/      # Project 4: Mult.asm (R0 × R1 → R2)
│   └── fill/      # Project 4: Fill.asm (keyboard-reactive screen)
├── 05/            # Project 5: Memory.hdl, CPU.hdl, Computer.hdl
├── 06/            # Project 6: Hack Assembler (Python)
├── 07/            # Projects 7 & 8: VM Translator (Python)
├── 10_11/         # Projects 10 & 11: Jack Compiler (Python)
└── 12/            # Project 12: Jack Operating System (Jack)
```

---

## 🕹️ Project Showcase: Tetris

The namesake game of the course is fully implemented and playable! It demonstrates the complete vertical stack: from NAND gates up to high-level game logic.

### How to Play
1.  **Download the Tools**: Get the official software suite from [nand2tetris.org](https://www.nand2tetris.org/software).
2.  **Open CPU Emulator**: Run `CPUEmulator.bat`. or` CPUEmulator.sh` on linux
3.  **Load the Game**: File -> Load Program -> `09/Tetris/Tetris.hack`.
4.  **Important Settings**:
    *   Set **Animate** to **"No Animation"** (required for playable speed).
    *   Press **Run** (double blue arrow).
5.  **Controls**:
    *   **Arrows**: Move and Rotate
    *   **ESC**: Quit

---

## Part I — Hardware (Projects 1–5)

All chips are written in the Hack HDL language and testable with the
**Hardware Simulator**.

---

## Part II — Software Toolchain (Projects 6–11)

Implemented in **Python 3.12+**. Translates high-level Jack code into machine binary.

### Project 6 — Assembler
Translates Hack `.asm` → `.hack` binary. Handles labels and symbols.
```bash
python 06/Assembler.py path/to/file.asm
```

### Projects 7 & 8 — VM Translator
Translates VM code to assembly. Includes full bootstrap and function support.
```bash
python 07/VMTranslator.py path/to/directory/
```

### Projects 10 & 11 — Jack Compiler
Compiles `.jack` source into VM code.
```bash
python 10_11/JackCompiler.py path/to/project/
```

---

## Part III — Operating System (Project 12)

A custom, performance-tuned Jack OS:

| Class      | Responsibility                                  |
|------------|--------------------------------------------------|
| `Sys`      | System bootstrap and initialization              |
| `Math`     | Fast multiplication/division algorithms          |
| `Memory`   | Efficient first-fit heap management              |
| `Screen`   | **Optimized**: 16-pixel word-level drawing       |
| `Output`   | **Slim**: Minimal font map to fit in 32k ROM     |

---

## Full Pipeline Example
To build the game from scratch:
```bash
# 1. Compile Jack to VM
python 10_11/JackCompiler.py 09/Tetris/

# 2. Translate VM to ASM (includes OS)
python 07/VMTranslator.py 09/Tetris/

# 3. Assemble ASM to Hack Binary
python 06/Assembler.py 09/Tetris/Tetris.asm
```

---

## Requirements

- **Python 3.10+** (for the software tools)
- **Official Nand2Tetris Tools** (optional; for HDL simulation and test running)
  - Download: https://www.nand2tetris.org/software
  - Requires Java 11+
