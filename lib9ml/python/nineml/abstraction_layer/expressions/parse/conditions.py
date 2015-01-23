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


# EM: Added floats funcs, collect names and funcs instead of eval'ing.

# This is a conditional parser


import ply.lex as lex
import ply.yacc as yacc
import os
from .expressions import call_expr_func
from nineml.utils import LocationMgr
from nineml.exceptions import NineMLMathParseError
from ..utils import is_builtin_math_function, get_builtin_symbols

# for now avoid duplication, but maintain distinctness
call_cond_func = call_expr_func


class CondParser(object):

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
        # self.debugfile = modname + ".dbg"
        # self.tabmodule = modname + "_" + "parsetab"

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
        # return set(self.names), set(self.funcs)

        self.names = set(self.names)
        self.names.difference_update(get_builtin_symbols())

        return self.names, set(self.funcs)


class CalcCond(CondParser):

    tokens = (
        'NAME', 'NUMBER', 'CONDITIONAL', 'NOT', 'LOGICAL',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE',
        'LPAREN', 'RPAREN', 'LFUNC', 'COMMA', 'BOOL'
    )

    # Tokens

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_EXP = r'\*\*'
    t_TIMES = r'\*'
    t_CONDITIONAL = r'(<=)|(>=)|(==)|(!=)|(>)|(<)'
    t_LOGICAL = r'(&)|(\|)'
    t_NOT = r'\!'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','

    def t_LFUNC(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_.]*[ ]*\('
        return t

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        if t.value in ('True', 'true', 'False', 'false'):
            t.type = 'BOOL'
        return t

    def t_NUMBER(self, t):
        r'(\d*\.\d+)|(\d+\.\d*)|(\d+)'
        try:
            t.value = float(t.value)
        except ValueError:
            raise NineMLMathParseError, "Invalid number %s" % t.value
        return t

    t_ignore = " \t"

    def t_error(self, t):
        raise NineMLMathParseError, \
            "Illegal character '%s' in '%s'" % (t.value[0], t)

    precedence = (
        ('left', 'NAME'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
        ('right', 'UNOT'),
        ('left', 'NOT'),
        ('left', 'LFUNC')
    )

    start = 'conditional'

    def p_conditional(self, p):
        'conditional : boolean'
        pass

    def p_boolean_bool(self, p):
        "boolean : BOOL"
        pass

    def p_boolean_not(self, p):
        'boolean : NOT boolean %prec UNOT'
        pass

    def p_boolean_logical(self, p):
        'boolean : boolean LOGICAL boolean'
        pass

    def p_boolean_group(self, p):
        'boolean : LPAREN boolean RPAREN'
        pass

    def p_boolean_conditional(self, p):
        'boolean : expression CONDITIONAL expression'
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

    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        pass

    def p_expression_number(self, p):
        'expression : NUMBER'
        pass

    def p_expression_name(self, p):
        'expression : NAME'
        self.names.append(p[1])

    def p_func(self, p):
        """expression : LFUNC expression RPAREN\n | LFUNC RPAREN
                        | LFUNC expression COMMA expression RPAREN
                        | LFUNC expression COMMA expression COMMA expression RPAREN
        """
        # EM: Supports up to 3 args.  Don't know how to support N.

        func_name = p[1][:-1].strip()
        if not is_builtin_math_function(func_name):
            raise NineMLMathParseError("Undefined function '%s'" % func_name)
        self.funcs.append(func_name)

    def p_error(self, p):
        if p:
            raise NineMLMathParseError("Syntax error at '%s'" % p.value)
        else:
            raise NineMLMathParseError("Syntax error at EOF, probably "
                                       "unmatched parenthesis.")


def cond_parse(conditional):
    """ Parses a conditinal expression
    and returns var names and func names as sets """

    calc = CalcCond()
    return calc.parse(conditional)

# if __name__ == '__main__':
#    calc = CalcCond()
#    p = calc.parse("q > 1 / (( 1 + mg_conc * eta *  exp ( -1 * gamma*V))")
#    print p
