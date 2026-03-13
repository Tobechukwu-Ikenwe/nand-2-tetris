#!/usr/bin/env python3
"""
Jack Tokenizer - Projects 10 & 11
Tokenizes Jack source code into a stream of tokens.
"""

import re

KEYWORDS = {
    'class', 'constructor', 'function', 'method',
    'field', 'static', 'var', 'int', 'char', 'boolean',
    'void', 'true', 'false', 'null', 'this',
    'let', 'do', 'if', 'else', 'while', 'return',
}

SYMBOLS = set('{}()[].,;+-*/&|<>=~')

TOKEN_KEYWORD         = 'keyword'
TOKEN_SYMBOL          = 'symbol'
TOKEN_INTEGER_CONST   = 'integerConstant'
TOKEN_STRING_CONST    = 'stringConstant'
TOKEN_IDENTIFIER      = 'identifier'


class JackTokenizer:
    def __init__(self, source: str):
        # Strip comments
        # Remove block comments /* ... */ and /** ... */
        source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
        # Remove line comments //...
        source = re.sub(r'//[^\n]*', '', source)
        self._tokens = self._tokenize(source)
        self._pos = 0
        self._current = None

    def _tokenize(self, source: str) -> list:
        tokens = []
        i = 0
        while i < len(source):
            c = source[i]

            # Whitespace
            if c.isspace():
                i += 1
                continue

            # String constant
            if c == '"':
                j = source.index('"', i + 1)
                tokens.append((TOKEN_STRING_CONST, source[i+1:j]))
                i = j + 1
                continue

            # Symbol
            if c in SYMBOLS:
                tokens.append((TOKEN_SYMBOL, c))
                i += 1
                continue

            # Integer constant
            if c.isdigit():
                j = i
                while j < len(source) and source[j].isdigit():
                    j += 1
                tokens.append((TOKEN_INTEGER_CONST, int(source[i:j])))
                i = j
                continue

            # Identifier or keyword
            if c.isalpha() or c == '_':
                j = i
                while j < len(source) and (source[j].isalnum() or source[j] == '_'):
                    j += 1
                word = source[i:j]
                if word in KEYWORDS:
                    tokens.append((TOKEN_KEYWORD, word))
                else:
                    tokens.append((TOKEN_IDENTIFIER, word))
                i = j
                continue

            # Unknown character — skip
            i += 1

        return tokens

    def has_more_tokens(self) -> bool:
        return self._pos < len(self._tokens)

    def advance(self):
        self._current = self._tokens[self._pos]
        self._pos += 1

    def peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    @property
    def token_type(self) -> str:
        return self._current[0]

    @property
    def keyword(self) -> str:
        return self._current[1]

    @property
    def symbol(self) -> str:
        return self._current[1]

    @property
    def identifier(self) -> str:
        return self._current[1]

    @property
    def int_val(self) -> int:
        return self._current[1]

    @property
    def string_val(self) -> str:
        return self._current[1]
