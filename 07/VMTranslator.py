#!/usr/bin/env python3
"""
VM Translator - Projects 7 & 8
Translates Hack VM (.vm) files to Hack assembly (.asm).

Covers:
  - Project 7: Stack arithmetic, memory access (all 8 segments)
  - Project 8: Program flow (label/goto/if-goto), Functions (call/return/function)

Usage:
  python VMTranslator.py <file.vm>       # single file
  python VMTranslator.py <directory/>    # all .vm files in directory
"""

import sys
import os
from glob import glob

# ── Code Writer ────────────────────────────────────────────────────────────────

class CodeWriter:
    def __init__(self, output_path: str):
        self._file = open(output_path, 'w')
        self._filename = ''       # current .vm file base name (no extension)
        self._label_counter = 0  # for unique eq/gt/lt labels
        self._call_counter = 0   # for unique return-address labels

    def set_filename(self, vm_path: str):
        self._filename = os.path.splitext(os.path.basename(vm_path))[0]

    def close(self):
        self._file.close()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _write(self, *lines):
        for line in lines:
            self._file.write(line + '\n')

    def _unique_label(self, prefix: str) -> str:
        label = f"{prefix}_{self._label_counter}"
        self._label_counter += 1
        return label

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def write_bootstrap(self):
        """Write bootstrap code: SP=256, then call Sys.init."""
        self._write(
            '// Bootstrap',
            '@256',
            'D=A',
            '@SP',
            'M=D',
        )
        self.write_call('Sys.init', 0)

    # ── Stack helpers ─────────────────────────────────────────────────────────

    def _push_d(self):
        """Push D register onto stack."""
        self._write('@SP', 'A=M', 'M=D', '@SP', 'M=M+1')

    def _pop_d(self):
        """Pop top of stack into D register."""
        self._write('@SP', 'AM=M-1', 'D=M')

    # ── Arithmetic / Logic ────────────────────────────────────────────────────

    def write_arithmetic(self, command: str):
        self._write(f'// {command}')
        if command == 'add':
            self._pop_d()
            self._write('A=A-1', 'M=M+D')
        elif command == 'sub':
            self._pop_d()
            self._write('A=A-1', 'M=M-D')
        elif command == 'neg':
            self._write('@SP', 'A=M-1', 'M=-M')
        elif command == 'not':
            self._write('@SP', 'A=M-1', 'M=!M')
        elif command == 'and':
            self._pop_d()
            self._write('A=A-1', 'M=M&D')
        elif command == 'or':
            self._pop_d()
            self._write('A=A-1', 'M=M|D')
        elif command in ('eq', 'gt', 'lt'):
            jump_map = {'eq': 'JEQ', 'gt': 'JGT', 'lt': 'JLT'}
            true_lbl  = self._unique_label(f'{command.upper()}_TRUE')
            end_lbl   = self._unique_label(f'{command.upper()}_END')
            self._pop_d()
            self._write(
                'A=A-1',
                'D=M-D',
                f'@{true_lbl}',
                f'D;{jump_map[command]}',
                '@SP', 'A=M-1', 'M=0',    # false
                f'@{end_lbl}', '0;JMP',
                f'({true_lbl})',
                '@SP', 'A=M-1', 'M=-1',   # true
                f'({end_lbl})',
            )
        else:
            raise ValueError(f"Unknown arithmetic command: {command}")

    # ── Memory Access ─────────────────────────────────────────────────────────

    # Segment base pointer assembly symbols
    _SEGMENT_BASE = {
        'local':    'LCL',
        'argument': 'ARG',
        'this':     'THIS',
        'that':     'THAT',
    }

    def write_push_pop(self, command: str, segment: str, index: int):
        self._write(f'// {command} {segment} {index}')

        if command == 'push':
            if segment == 'constant':
                self._write(f'@{index}', 'D=A')
            elif segment in self._SEGMENT_BASE:
                base = self._SEGMENT_BASE[segment]
                self._write(f'@{base}', 'D=M', f'@{index}', 'A=D+A', 'D=M')
            elif segment == 'static':
                self._write(f'@{self._filename}.{index}', 'D=M')
            elif segment == 'temp':
                addr = 5 + index  # temp maps to R5..R12
                self._write(f'@{addr}', 'D=M')
            elif segment == 'pointer':
                reg = 'THIS' if index == 0 else 'THAT'
                self._write(f'@{reg}', 'D=M')
            else:
                raise ValueError(f"Unknown segment: {segment}")
            self._push_d()

        elif command == 'pop':
            if segment in self._SEGMENT_BASE:
                base = self._SEGMENT_BASE[segment]
                # Compute target address in R13
                self._write(f'@{base}', 'D=M', f'@{index}', 'D=D+A', '@R13', 'M=D')
                self._pop_d()
                self._write('@R13', 'A=M', 'M=D')
            elif segment == 'static':
                self._pop_d()
                self._write(f'@{self._filename}.{index}', 'M=D')
            elif segment == 'temp':
                addr = 5 + index
                self._pop_d()
                self._write(f'@{addr}', 'M=D')
            elif segment == 'pointer':
                reg = 'THIS' if index == 0 else 'THAT'
                self._pop_d()
                self._write(f'@{reg}', 'M=D')
            else:
                raise ValueError(f"Unknown segment for pop: {segment}")

    # ── Program Flow ──────────────────────────────────────────────────────────

    def write_label(self, function_name: str, label: str):
        self._write(f'// label {label}', f'({function_name}${label})')

    def write_goto(self, function_name: str, label: str):
        self._write(
            f'// goto {label}',
            f'@{function_name}${label}',
            '0;JMP',
        )

    def write_if(self, function_name: str, label: str):
        self._pop_d()
        self._write(
            f'// if-goto {label}',
            f'@{function_name}${label}',
            'D;JNE',
        )

    # ── Functions ─────────────────────────────────────────────────────────────

    def write_function(self, function_name: str, n_locals: int):
        self._write(f'// function {function_name} {n_locals}', f'({function_name})')
        for _ in range(n_locals):
            self._write('@SP', 'A=M', 'M=0', '@SP', 'M=M+1')

    def write_call(self, function_name: str, n_args: int):
        return_label = f'{function_name}$ret.{self._call_counter}'
        self._call_counter += 1
        self._write(f'// call {function_name} {n_args}')

        # push return-address
        self._write(f'@{return_label}', 'D=A')
        self._push_d()
        # push LCL, ARG, THIS, THAT
        for seg in ('LCL', 'ARG', 'THIS', 'THAT'):
            self._write(f'@{seg}', 'D=M')
            self._push_d()
        # ARG = SP - n_args - 5
        self._write('@SP', 'D=M', f'@{n_args + 5}', 'D=D-A', '@ARG', 'M=D')
        # LCL = SP
        self._write('@SP', 'D=M', '@LCL', 'M=D')
        # goto function
        self._write(f'@{function_name}', '0;JMP')
        # inject return-address label
        self._write(f'({return_label})')

    def write_return(self):
        self._write(
            '// return',
            # FRAME = LCL (stored in R14)
            '@LCL', 'D=M', '@R14', 'M=D',
            # RET = *(FRAME-5) (stored in R15)
            '@5', 'A=D-A', 'D=M', '@R15', 'M=D',
            # *ARG = pop()
            '@SP', 'AM=M-1', 'D=M', '@ARG', 'A=M', 'M=D',
            # SP = ARG + 1
            '@ARG', 'D=M+1', '@SP', 'M=D',
            # THAT = *(FRAME-1)
            '@R14', 'AM=M-1', 'D=M', '@THAT', 'M=D',
            # THIS = *(FRAME-2)
            '@R14', 'AM=M-1', 'D=M', '@THIS', 'M=D',
            # ARG  = *(FRAME-3)
            '@R14', 'AM=M-1', 'D=M', '@ARG',  'M=D',
            # LCL  = *(FRAME-4)
            '@R14', 'AM=M-1', 'D=M', '@LCL',  'M=D',
            # goto RET
            '@R15', 'A=M', '0;JMP',
        )


# ── Parser ─────────────────────────────────────────────────────────────────────

class Parser:
    C_ARITHMETIC = 'C_ARITHMETIC'
    C_PUSH       = 'C_PUSH'
    C_POP        = 'C_POP'
    C_LABEL      = 'C_LABEL'
    C_GOTO       = 'C_GOTO'
    C_IF         = 'C_IF'
    C_FUNCTION   = 'C_FUNCTION'
    C_RETURN     = 'C_RETURN'
    C_CALL       = 'C_CALL'

    ARITHMETIC_CMDS = {'add','sub','neg','eq','gt','lt','and','or','not'}

    def __init__(self, vm_path: str):
        with open(vm_path) as f:
            raw = f.readlines()
        self._lines = []
        for line in raw:
            line = line.split('//')[0].strip()
            if line:
                self._lines.append(line)
        self._pos = 0

    def has_more_commands(self) -> bool:
        return self._pos < len(self._lines)

    def advance(self):
        self._current = self._lines[self._pos]
        self._parts = self._current.split()
        self._pos += 1

    @property
    def command_type(self) -> str:
        cmd = self._parts[0]
        if cmd in self.ARITHMETIC_CMDS:  return self.C_ARITHMETIC
        if cmd == 'push':                return self.C_PUSH
        if cmd == 'pop':                 return self.C_POP
        if cmd == 'label':               return self.C_LABEL
        if cmd == 'goto':                return self.C_GOTO
        if cmd == 'if-goto':             return self.C_IF
        if cmd == 'function':            return self.C_FUNCTION
        if cmd == 'return':              return self.C_RETURN
        if cmd == 'call':                return self.C_CALL
        raise ValueError(f"Unknown VM command: {cmd}")

    @property
    def arg1(self) -> str:
        if self.command_type == self.C_ARITHMETIC:
            return self._parts[0]
        return self._parts[1]

    @property
    def arg2(self) -> int:
        return int(self._parts[2])


# ── Main ───────────────────────────────────────────────────────────────────────

def translate_file(parser: Parser, cw: CodeWriter, function_context: list):
    """Translate all commands in one parser into cw."""
    while parser.has_more_commands():
        parser.advance()
        ct = parser.command_type

        if ct == Parser.C_ARITHMETIC:
            cw.write_arithmetic(parser.arg1)

        elif ct in (Parser.C_PUSH, Parser.C_POP):
            cmd = 'push' if ct == Parser.C_PUSH else 'pop'
            cw.write_push_pop(cmd, parser.arg1, parser.arg2)

        elif ct == Parser.C_LABEL:
            cw.write_label(function_context[0], parser.arg1)

        elif ct == Parser.C_GOTO:
            cw.write_goto(function_context[0], parser.arg1)

        elif ct == Parser.C_IF:
            cw.write_if(function_context[0], parser.arg1)

        elif ct == Parser.C_FUNCTION:
            function_context[0] = parser.arg1
            cw.write_function(parser.arg1, parser.arg2)

        elif ct == Parser.C_CALL:
            cw.write_call(parser.arg1, parser.arg2)

        elif ct == Parser.C_RETURN:
            cw.write_return()


def main():
    if len(sys.argv) != 2:
        print("Usage: python VMTranslator.py <file.vm | directory>")
        sys.exit(1)

    target = sys.argv[1].rstrip('/\\')

    if os.path.isdir(target):
        vm_files = glob(os.path.join(target, '*.vm'))
        if not vm_files:
            print(f"No .vm files found in {target}")
            sys.exit(1)
        out_name = os.path.basename(target) + '.asm'
        out_path = os.path.join(target, out_name)
        multi = True
    elif os.path.isfile(target):
        vm_files = [target]
        out_path = os.path.splitext(target)[0] + '.asm'
        multi = False
    else:
        print(f"Error: {target} is not a file or directory")
        sys.exit(1)

    cw = CodeWriter(out_path)

    if multi:
        cw.write_bootstrap()

    # Sort so Sys.vm is first when present
    vm_files.sort(key=lambda p: (0 if 'Sys' in p else 1, p))

    for vm_path in vm_files:
        cw.set_filename(vm_path)
        parser = Parser(vm_path)
        function_context = ['']  # mutable container for current function name
        translate_file(parser, cw, function_context)
        print(f"Translated: {vm_path}")

    cw.close()
    print(f"Output written to: {out_path}")


if __name__ == '__main__':
    main()
