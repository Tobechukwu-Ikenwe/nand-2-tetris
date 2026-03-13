#!/usr/bin/env python3
"""
JackCompiler - Projects 10 & 11
Entry point: Compiles .jack file(s) to .vm files.

Usage:
  python JackCompiler.py <file.jack>       # single file
  python JackCompiler.py <directory/>      # all .jack files in directory
"""

import sys
import os
from glob import glob
from CompilationEngine import CompilationEngine


def compile_file(jack_path: str):
    out_path = os.path.splitext(jack_path)[0] + '.vm'
    with open(jack_path, 'r') as f:
        source = f.read()
    try:
        engine = CompilationEngine(source, out_path)
        engine.compile()
        print(f"Compiled: {jack_path}")
    except Exception as e:
        print(f"Error compiling {jack_path}: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)

    target = sys.argv[1].rstrip('/\\')

    if os.path.isdir(target):
        jack_files = glob(os.path.join(target, '*.jack'))
        if not jack_files:
            print(f"No .jack files found in {target}")
            sys.exit(1)
        for jack_path in sorted(jack_files):
            compile_file(jack_path)
    elif os.path.isfile(target):
        compile_file(target)
    else:
        print(f"Error: {target} is not a file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
