"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

# Based on PLY calc.py example:
# -----------------------------------------------------------------------------
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
#
# Class-based example contributed to PLY by David McNab.
#
# Modified to use new-style classes.   Test case.
# -----------------------------------------------------------------------------


import os
import re
import ply.lex as lex
import ply.yacc as yacc

from nineml.utils import LocationMgr
from nineml.exceptions import NineMLMathParseError
from ..utils import get_builtin_symbols


def call_expr_func(expr_func, ns):
    args = []
    for var in expr_func.func_code.co_varnames:
        try:
            args.append(ns[var])
        except KeyError:
            raise KeyError("call_expr_func: namespace missing variable '%s'" %
                           var)
    return expr_func(*args)


class ExprParser(object):

    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.debug = kw.get('debug', 0)
        self.names = {}
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                1] + "_" + self.__class__.__name__
        except:
            modname = "parser" + "_" + self.__class__.__name__

        self.debugfile = LocationMgr.getTmpDir() + modname + ".dbg"
        self.tabmodule = LocationMgr.getTmpDir() + modname + "_" + "parsetab"

        # print self.debugfile, self.tabmodule

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile,
                  tabmodule=self.tabmodule)

    def parse(self, expr):
        self.names = []
        self.funcs = []
        try:
            yacc.parse(expr)
        except NineMLMathParseError, e:
            raise NineMLMathParseError(str(e) + " Expression was: '%s'" % expr)

        # remove names from the math_namespace
        self.names = set(self.names)
        self.names.difference_update(get_builtin_symbols())

        return self.names, set(self.funcs)


class CalcExpr(ExprParser):

    tokens = (
        'NAME', 'NUMBER',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE',
        'LPAREN', 'RPAREN', 'LFUNC', 'COMMA'
    )

    # Tokens

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_EXP = r'\*\*'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_LFUNC = r'[a-zA-Z_][a-zA-Z0-9_.]*[ ]*\('
    t_COMMA = r','

    def t_NUMBER(self, t):
        r'(\d*\.\d+)|(\d+\.\d*)|(\d+)'
        try:
            t.value = float(t.value)
        except ValueError:
            raise NineMLMathParseError("Invalid number %s" % t.value)
        return t

    t_ignore = " \t"

    def t_error(self, t):
        raise NineMLMathParseError("Illegal character '%s' in '%s'" %
                                   (t.value[0], t))

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
        ('left', 'LFUNC'),
    )

    def p_statement_expr(self, p):
        'statement : expression'
        pass

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EXP expression
        """
        pass

    def p_expression_uminus(self, p):
        'expression : MINUS expression %prec UMINUS'
        pass

    def p_func(self, p):
        """expression : LFUNC expression RPAREN\n | LFUNC RPAREN
                        | LFUNC expression COMMA expression RPAREN
                        | LFUNC expression COMMA expression COMMA expression RPAREN
        """
        # EM: Supports up to 3 args.  Don't know how to support N.

        # check that function name is known
        func_name = p[1][:-1].strip()
        # if func_name not in math_namespace.namespace:
        #    raise NineMLMathParseError, "Undefined function '%s'" % func_name
        self.funcs.append(func_name)

    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        pass

    def p_expression_number(self, p):
        'expression : NUMBER'
        pass

    def p_expression_name(self, p):
        'expression : NAME'
        self.names.append(p[1])

    def p_error(self, p):
        if p:
            raise NineMLMathParseError("Syntax error at '%s'" % p.value)
        else:
            raise NineMLMathParseError("Syntax error at EOF, probably "
                                       "unmatched parenthesis.")


def expr_parse(rhs):
    """ Parses an expression rhs, i.e. no "=, +=, -=, etc." in the expr
    and returns var names and func names as sets """

    calc = CalcExpr()
    # Remove endlines
    rhs = rhs.replace('\n', ' ')
    rhs = rhs.replace('\r', ' ')
    # Expand scientific notation, 1e-10 to 1 * pow(10, -10)
    rhs = re.sub(r'([0-9])e(\-?[0-9\.]+)', r'\1 * pow(10, \2)', rhs)
    # Convert '^' to pow()
    rhs = escape_carets(rhs)
    return calc.parse(rhs)


def escape_carets(string):
    if '^' in string:
        i = 0
        while i < len(string):
            if string[i] == '^':
                before = string[:i]
                after = string[i + 1:]
                if before.rstrip().endswith(')'):
                    base = match_bracket(before, open_bracket=')',
                                         close_bracket='(',
                                         direction='backwards')
                else:
                    base = re.search(r'((?:-)?(?:\w+|[\d\.]+) *)$',
                                     before).group(1)
                if after.lstrip().startswith('('):
                    exponent = match_bracket(after, open_bracket='(',
                                             close_bracket=')')
                    exponent = escape_carets(exponent)
                else:
                    exponent = re.match(r' *(?:-)?[\w\d\.]+', after).group(0)
                insert_string = 'pow({}, {})'.format(base, exponent)
                string = (string[:i - len(base)] + insert_string +
                          string[i + len(exponent) + 1:])
                i += len(insert_string) - len(base)
            i += 1
    return string


def match_bracket(string, open_bracket, close_bracket, direction='forwards'):
    depth = 0
    if direction == 'backwards':
        string = string[::-1]
    for i, c in enumerate(string):
        if c == open_bracket:
            depth += 1
        elif c == close_bracket:
            depth -= 1
            if depth == 0:
                output = string[:i + 1]
                if direction == 'backwards':
                    output = output[::-1]
                return output
    raise Exception("No matching '{}' found for opening '{}' in string '{}'"
                    .format(close_bracket, open_bracket, string))


if __name__ == '__main__':
    calc = CalcExpr()
    p = calc.parse("1 / ( 1 + mg_conc * eta *  exp ( -1 * gamma*V))")
    print p
