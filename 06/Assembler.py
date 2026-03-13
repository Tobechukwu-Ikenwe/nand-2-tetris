#!/usr/bin/env python3
"""
Hack Assembler - Project 6
Translates Hack assembly language (.asm) to Hack binary machine code (.hack)
Implements a two-pass assembler:
  Pass 1: Scan for label declarations (Xxx) and build symbol table
  Pass 2: Translate each instruction to binary
"""

import sys
import os
import re

# ── Predefined symbols ────────────────────────────────────────────────────────
PREDEFINED_SYMBOLS = {
    'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
    'R0': 0,  'R1': 1,  'R2': 2,  'R3': 3,
    'R4': 4,  'R5': 5,  'R6': 6,  'R7': 7,
    'R8': 8,  'R9': 9,  'R10': 10, 'R11': 11,
    'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
    'SCREEN': 16384, 'KBD': 24576,
}

# ── C-instruction lookup tables ───────────────────────────────────────────────
COMP_TABLE = {
    # a=0
    '0':   '0101010', '1':   '0111111', '-1':  '0111010',
    'D':   '0001100', 'A':   '0110000', '!D':  '0001101',
    '!A':  '0110001', '-D':  '0001111', '-A':  '0110011',
    'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
    'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011',
    'A-D': '0000111', 'D&A': '0000000', 'D|A': '0010101',
    # a=1
    'M':   '1110000', '!M':  '1110001', '-M':  '1110011',
    'M+1': '1110111', 'M-1': '1110010', 'D+M': '1000010',
    'M-D': '1000111', 'D&M': '1000000', 'D|M': '1010101',
    # Commutative aliases
    'A+D': '0000010', 'M+D': '1000010', 'A&D': '0000000', 'M&D': '1000000',
    'A|D': '0010101', 'M|D': '1010101',
}

DEST_TABLE = {
    None:  '000', 'M':  '001', 'D':  '010', 'MD': '011',
    'A':   '100', 'AM': '101', 'AD': '110', 'AMD': '111',
}

JUMP_TABLE = {
    None:  '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
    'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111',
}


def strip_comment(line: str) -> str:
    """Remove inline comments and strip whitespace."""
    idx = line.find('//')
    if idx >= 0:
        line = line[:idx]
    return line.strip()


def is_a_instruction(line: str) -> bool:
    return line.startswith('@')


def is_label(line: str) -> bool:
    return line.startswith('(') and line.endswith(')')


def translate_a(value: int) -> str:
    """Convert integer to 16-bit A-instruction binary string."""
    return '0' + format(value, '015b')


def translate_c(instruction: str) -> str:
    """Parse and translate a C-instruction to binary."""
    # Split jump
    if ';' in instruction:
        comp_dest, jump = instruction.split(';', 1)
        jump = jump.strip()
    else:
        comp_dest = instruction
        jump = None

    # Split dest
    if '=' in comp_dest:
        dest, comp = comp_dest.split('=', 1)
        dest = dest.strip()
        comp = comp.strip()
    else:
        dest = None
        comp = comp_dest.strip()

    comp_bits = COMP_TABLE.get(comp)
    dest_bits = DEST_TABLE.get(dest)
    jump_bits = JUMP_TABLE.get(jump)

    if comp_bits is None:
        raise ValueError(f"Unknown comp mnemonic: '{comp}'")
    if dest_bits is None:
        raise ValueError(f"Unknown dest mnemonic: '{dest}'")
    if jump_bits is None:
        raise ValueError(f"Unknown jump mnemonic: '{jump}'")

    return '111' + comp_bits + dest_bits + jump_bits


def assemble(source: str) -> list[str]:
    """
    Two-pass assembler.
    Returns list of 16-bit binary instruction strings.
    """
    lines = source.splitlines()
    symbol_table = dict(PREDEFINED_SYMBOLS)

    # ── Pass 1: build label symbol table ─────────────────────────────────────
    rom_address = 0
    for line in lines:
        clean = strip_comment(line)
        if not clean:
            continue
        if is_label(clean):
            label = clean[1:-1]
            symbol_table[label] = rom_address
        else:
            rom_address += 1

    # ── Pass 2: translate instructions ───────────────────────────────────────
    next_var_address = 16
    output = []

    for line in lines:
        clean = strip_comment(line)
        if not clean or is_label(clean):
            continue

        if is_a_instruction(clean):
            symbol = clean[1:]
            if symbol.isdigit():
                value = int(symbol)
            else:
                if symbol not in symbol_table:
                    symbol_table[symbol] = next_var_address
                    next_var_address += 1
                value = symbol_table[symbol]
            output.append(translate_a(value))
        else:
            output.append(translate_c(clean))

    return output


def main():
    if len(sys.argv) != 2:
        print("Usage: python Assembler.py <filename.asm>")
        sys.exit(1)

    asm_path = sys.argv[1]
    if not os.path.isfile(asm_path):
        print(f"Error: File not found: {asm_path}")
        sys.exit(1)

    with open(asm_path, 'r') as f:
        source = f.read()

    binary_instructions = assemble(source)

    # Write output to .hack file (same directory, same name)
    out_path = os.path.splitext(asm_path)[0] + '.hack'
    with open(out_path, 'w') as f:
        f.write('\n'.join(binary_instructions) + '\n')

    print(f"Assembled {len(binary_instructions)} instructions -> {out_path}")


if __name__ == '__main__':
    main()
