#!/usr/bin/env python
import os.path

with open(os.path.join(os.path.dirname(__file__), 'builtin_functions.txt')) as f:
  funcs = f.read().split('\n')

print '\n'.join('\\item \\verb|{}|'.format(f) for f in sorted(funcs))

