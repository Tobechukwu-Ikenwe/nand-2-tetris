#!/usr/bin/env python3
"""
Compilation Engine + Symbol Table + VM Writer — Projects 10 & 11

Full recursive-descent compiler for Jack → VM code.
"""

from JackTokenizer import (
    JackTokenizer,
    TOKEN_KEYWORD, TOKEN_SYMBOL, TOKEN_INTEGER_CONST,
    TOKEN_STRING_CONST, TOKEN_IDENTIFIER,
)

# ── Symbol Table ───────────────────────────────────────────────────────────────

class SymbolTable:
    """Two-scope symbol table: class-level and subroutine-level."""

    STATIC   = 'static'
    FIELD    = 'field'
    ARG      = 'argument'
    VAR      = 'local'

    def __init__(self):
        self._class_table = {}
        self._sub_table   = {}
        self._counts = {self.STATIC: 0, self.FIELD: 0,
                        self.ARG: 0, self.VAR: 0}

    def start_subroutine(self):
        self._sub_table = {}
        self._counts[self.ARG] = 0
        self._counts[self.VAR] = 0

    def define(self, name: str, type_: str, kind: str):
        idx = self._counts[kind]
        self._counts[kind] += 1
        table = self._sub_table if kind in (self.ARG, self.VAR) else self._class_table
        table[name] = (type_, kind, idx)

    def var_count(self, kind: str) -> int:
        return self._counts[kind]

    def _lookup(self, name: str):
        return self._sub_table.get(name) or self._class_table.get(name)

    def type_of(self, name: str) -> str:
        return self._lookup(name)[0]

    def kind_of(self, name: str):
        entry = self._lookup(name)
        return entry[1] if entry else None

    def index_of(self, name: str) -> int:
        return self._lookup(name)[2]


# ── VM Writer ──────────────────────────────────────────────────────────────────

class VMWriter:
    SEGMENT_MAP = {
        'static': 'static', 'field': 'this',
        'argument': 'argument', 'local': 'local',
    }

    def __init__(self, output_path: str):
        self._f = open(output_path, 'w')

    def close(self):
        self._f.close()

    def _w(self, line: str):
        self._f.write(line + '\n')

    def write_push(self, segment: str, index: int):
        self._w(f'push {segment} {index}')

    def write_pop(self, segment: str, index: int):
        self._w(f'pop {segment} {index}')

    def write_arithmetic(self, command: str):
        self._w(command)

    def write_label(self, label: str):
        self._w(f'label {label}')

    def write_goto(self, label: str):
        self._w(f'goto {label}')

    def write_if(self, label: str):
        self._w(f'if-goto {label}')

    def write_call(self, name: str, n_args: int):
        self._w(f'call {name} {n_args}')

    def write_function(self, name: str, n_locals: int):
        self._w(f'function {name} {n_locals}')

    def write_return(self):
        self._w('return')


# ── Compilation Engine ─────────────────────────────────────────────────────────

class CompilationEngine:
    def __init__(self, source: str, output_path: str):
        self._tk = JackTokenizer(source)
        self._vm = VMWriter(output_path)
        self._sym = SymbolTable()
        self._class_name = ''
        self._label_counter = 0

    def compile(self):
        self._tk.advance()
        self._compile_class()
        self._vm.close()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _eat(self, expected=None):
        """Consume current token, optionally asserting its value."""
        tok = self._tk._current
        if expected is not None and tok[1] != expected:
            raise SyntaxError(f"Expected '{expected}', got '{tok[1]}'")
        if self._tk.has_more_tokens():
            self._tk.advance()
        return tok

    def _peek_type(self):
        p = self._tk.peek()
        return p[0] if p else None

    def _peek_val(self):
        p = self._tk.peek()
        return p[1] if p else None

    def _new_label(self, prefix='L') -> str:
        lbl = f'{prefix}_{self._label_counter}'
        self._label_counter += 1
        return lbl

    # ── Class ─────────────────────────────────────────────────────────────────

    def _compile_class(self):
        self._eat('class')
        self._class_name = self._tk.identifier
        self._eat()                 # className
        self._eat('{')
        while self._tk._current[1] in ('static', 'field'):
            self._compile_class_var_dec()
        while self._tk._current[1] in ('constructor', 'function', 'method'):
            self._compile_subroutine()
        self._eat('}')

    def _compile_class_var_dec(self):
        kind = self._tk.keyword  # 'static' or 'field'
        kind_map = {'static': SymbolTable.STATIC, 'field': SymbolTable.FIELD}
        self._eat()
        type_ = self._tk._current[1]; self._eat()
        name  = self._tk.identifier;  self._eat()
        self._sym.define(name, type_, kind_map[kind])
        while self._tk._current[1] == ',':
            self._eat(',')
            name = self._tk.identifier; self._eat()
            self._sym.define(name, type_, kind_map[kind])
        self._eat(';')

    # ── Subroutine ────────────────────────────────────────────────────────────

    def _compile_subroutine(self):
        sub_type = self._tk.keyword  # constructor / function / method
        self._eat()
        self._eat()                  # return type
        sub_name = self._tk.identifier; self._eat()
        self._sym.start_subroutine()

        if sub_type == 'method':
            # 'this' is argument 0
            self._sym.define('this', self._class_name, SymbolTable.ARG)

        self._eat('(')
        self._compile_parameter_list()
        self._eat(')')
        self._compile_subroutine_body(sub_name, sub_type)

    def _compile_parameter_list(self):
        if self._tk._current[1] == ')':
            return
        type_ = self._tk._current[1]; self._eat()
        name  = self._tk.identifier;  self._eat()
        self._sym.define(name, type_, SymbolTable.ARG)
        while self._tk._current[1] == ',':
            self._eat(',')
            type_ = self._tk._current[1]; self._eat()
            name  = self._tk.identifier;  self._eat()
            self._sym.define(name, type_, SymbolTable.ARG)

    def _compile_subroutine_body(self, sub_name: str, sub_type: str):
        self._eat('{')
        while self._tk._current[1] == 'var':
            self._compile_var_dec()
        n_locals = self._sym.var_count(SymbolTable.VAR)
        self._vm.write_function(f'{self._class_name}.{sub_name}', n_locals)

        if sub_type == 'constructor':
            n_fields = self._sym.var_count(SymbolTable.FIELD)
            self._vm.write_push('constant', n_fields)
            self._vm.write_call('Memory.alloc', 1)
            self._vm.write_pop('pointer', 0)
        elif sub_type == 'method':
            self._vm.write_push('argument', 0)
            self._vm.write_pop('pointer', 0)

        self._compile_statements()
        self._eat('}')

    def _compile_var_dec(self):
        self._eat('var')
        type_ = self._tk._current[1]; self._eat()
        name  = self._tk.identifier;  self._eat()
        self._sym.define(name, type_, SymbolTable.VAR)
        while self._tk._current[1] == ',':
            self._eat(',')
            name = self._tk.identifier; self._eat()
            self._sym.define(name, type_, SymbolTable.VAR)
        self._eat(';')

    # ── Statements ────────────────────────────────────────────────────────────

    def _compile_statements(self):
        while self._tk._current[1] in ('let','if','while','do','return'):
            kw = self._tk._current[1]
            if   kw == 'let':    self._compile_let()
            elif kw == 'if':     self._compile_if()
            elif kw == 'while':  self._compile_while()
            elif kw == 'do':     self._compile_do()
            elif kw == 'return': self._compile_return()

    def _compile_let(self):
        self._eat('let')
        var_name = self._tk.identifier; self._eat()
        is_array = self._tk._current[1] == '['
        if is_array:
            self._push_var(var_name)
            self._eat('[')
            self._compile_expression()
            self._eat(']')
            self._vm.write_arithmetic('add')   # base + index
        self._eat('=')
        self._compile_expression()
        self._eat(';')
        if is_array:
            self._vm.write_pop('temp', 0)      # save rhs
            self._vm.write_pop('pointer', 1)   # set THAT
            self._vm.write_push('temp', 0)
            self._vm.write_pop('that', 0)
        else:
            self._pop_var(var_name)

    def _compile_if(self):
        lbl_false = self._new_label('IF_FALSE')
        lbl_end   = self._new_label('IF_END')
        self._eat('if')
        self._eat('(')
        self._compile_expression()
        self._eat(')')
        self._vm.write_arithmetic('not')
        self._vm.write_if(lbl_false)
        self._eat('{')
        self._compile_statements()
        self._eat('}')
        if self._tk._current[1] == 'else':
            self._vm.write_goto(lbl_end)
            self._vm.write_label(lbl_false)
            self._eat('else')
            self._eat('{')
            self._compile_statements()
            self._eat('}')
            self._vm.write_label(lbl_end)
        else:
            self._vm.write_label(lbl_false)

    def _compile_while(self):
        lbl_start = self._new_label('WHILE_START')
        lbl_end   = self._new_label('WHILE_END')
        self._vm.write_label(lbl_start)
        self._eat('while')
        self._eat('(')
        self._compile_expression()
        self._eat(')')
        self._vm.write_arithmetic('not')
        self._vm.write_if(lbl_end)
        self._eat('{')
        self._compile_statements()
        self._eat('}')
        self._vm.write_goto(lbl_start)
        self._vm.write_label(lbl_end)

    def _compile_do(self):
        self._eat('do')
        name = self._tk.identifier; self._eat()
        self._compile_subroutine_call(name)
        self._eat(';')
        self._vm.write_pop('temp', 0)  # discard return value

    def _compile_return(self):
        self._eat('return')
        if self._tk._current[1] != ';':
            self._compile_expression()
        else:
            self._vm.write_push('constant', 0)
        self._eat(';')
        self._vm.write_return()

    # ── Expressions ───────────────────────────────────────────────────────────

    OPS = {'+': 'add', '-': 'sub', '*': None, '/': None,
           '&': 'and', '|': 'or',  '<': 'lt', '>': 'gt', '=': 'eq'}

    def _compile_expression(self):
        self._compile_term()
        while self._tk._current[1] in self.OPS:
            op = self._tk._current[1]; self._eat()
            self._compile_term()
            if op == '*':
                self._vm.write_call('Math.multiply', 2)
            elif op == '/':
                self._vm.write_call('Math.divide', 2)
            else:
                self._vm.write_arithmetic(self.OPS[op])

    def _compile_term(self):
        tt = self._tk.token_type
        val = self._tk._current[1]

        if tt == TOKEN_INTEGER_CONST:
            self._vm.write_push('constant', self._tk.int_val)
            self._eat()

        elif tt == TOKEN_STRING_CONST:
            s = self._tk.string_val
            self._vm.write_push('constant', len(s))
            self._vm.write_call('String.new', 1)
            for ch in s:
                self._vm.write_push('constant', ord(ch))
                self._vm.write_call('String.appendChar', 2)
            self._eat()

        elif tt == TOKEN_KEYWORD:
            if val == 'true':
                self._vm.write_push('constant', 0)
                self._vm.write_arithmetic('not')
            elif val in ('false', 'null'):
                self._vm.write_push('constant', 0)
            elif val == 'this':
                self._vm.write_push('pointer', 0)
            self._eat()

        elif tt == TOKEN_SYMBOL:
            if val == '(':
                self._eat('(')
                self._compile_expression()
                self._eat(')')
            elif val == '-':
                self._eat('-')
                self._compile_term()
                self._vm.write_arithmetic('neg')
            elif val == '~':
                self._eat('~')
                self._compile_term()
                self._vm.write_arithmetic('not')

        elif tt == TOKEN_IDENTIFIER:
            # Could be: varName | varName[expr] | subroutineCall
            name = self._tk.identifier; self._eat()
            nxt = self._tk._current[1]
            if nxt == '[':
                # Array access
                self._push_var(name)
                self._eat('[')
                self._compile_expression()
                self._eat(']')
                self._vm.write_arithmetic('add')
                self._vm.write_pop('pointer', 1)
                self._vm.write_push('that', 0)
            elif nxt in ('.', '('):
                self._compile_subroutine_call(name)
            else:
                self._push_var(name)

    def _compile_subroutine_call(self, name: str):
        """name may be 'Foo', 'Foo.bar', or varName"""
        n_args = 0
        if self._tk._current[1] == '.':
            self._eat('.')
            method = self._tk.identifier; self._eat()
            # Check if name is a variable (object reference)
            kind = self._sym.kind_of(name)
            if kind is not None:
                self._push_var(name)
                full_name = f'{self._sym.type_of(name)}.{method}'
                n_args = 1
            else:
                full_name = f'{name}.{method}'
        else:
            # method call on 'this'
            full_name = f'{self._class_name}.{name}'
            self._vm.write_push('pointer', 0)
            n_args = 1

        self._eat('(')
        n_args += self._compile_expression_list()
        self._eat(')')
        self._vm.write_call(full_name, n_args)

    def _compile_expression_list(self) -> int:
        count = 0
        if self._tk._current[1] != ')':
            self._compile_expression()
            count = 1
            while self._tk._current[1] == ',':
                self._eat(',')
                self._compile_expression()
                count += 1
        return count

    # ── Variable push/pop helpers ─────────────────────────────────────────────

    _SEG_MAP = {
        SymbolTable.STATIC: 'static',
        SymbolTable.FIELD:  'this',
        SymbolTable.ARG:    'argument',
        SymbolTable.VAR:    'local',
    }

    def _push_var(self, name: str):
        kind = self._sym.kind_of(name)
        self._vm.write_push(self._SEG_MAP[kind], self._sym.index_of(name))

    def _pop_var(self, name: str):
        kind = self._sym.kind_of(name)
        self._vm.write_pop(self._SEG_MAP[kind], self._sym.index_of(name))
