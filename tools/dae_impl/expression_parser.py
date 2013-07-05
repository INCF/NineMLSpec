#!/usr/bin/env python

"""********************************************************************************
                           expression_parser.py
                 Copyright (C) Dragan Nikolic, 2011
***********************************************************************************
ExpressionParser is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License version 3 as published by the Free Software
Foundation. It is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this 
software; if not, see <http://www.gnu.org/licenses/>.
********************************************************************************"""

from __future__ import print_function
import os, sys, operator
import ply.lex as lex
import ply.yacc as yacc
from math import *
from parser_objects import Number, BinaryNode, IdentifierNode, ConstantNode, Condition
from parser_objects import NonstandardFunctionNode, StandardFunctionNode, AssignmentNode

#logical_operator = {'and': 'and',
#                    'or' : 'or'
#                   }

functions = {'exp'  : 'exp',
            'sqrt' : 'sqrt',
            'log'  : 'log',
            'log10': 'log10',
            'sin'  : 'sin',
            'cos'  : 'cos',
            'tan'  : 'tan',
            'asin' : 'asin',
            'acos' : 'acos',
            'atan' : 'atan',
            'sinh' : 'sinh',
            'cosh' : 'cosh',
            'tanh' : 'tanh',
            'asinh': 'asinh',
            'acosh': 'acosh',
            'atanh': 'atanh',
            'ceil' : 'ceil',
            'floor': 'floor',
            'fabs' : 'fabs'
            }

# Parser class
class ExpressionParser:
    """
    The parser supports the following:
        a) math. functions: 'sqrt', 'exp', 'log', 'log10', 'ceil', 'floor',
                            'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                            'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh'
        b) math. operators: +, -, *, /, **, unary +, unary -
        c) comparison operators: <, <=, >, >=, !=, ==
        d) logical operators: && (and), || (or)
                                                       
    Objects that can be used to evaluate the expression after parsing should support the above math. functions and operators.
    User-defined functions with arbitrary number of arguments that operate on such objects can be defined by the user.
    Dictionary 'dictIdentifiers' should contain pairs of the following type:
        identifier-name:value (ie. 'var':number,  or 'name1.name2.var':object-that-defines-math-operators-and-functions)
    Dictionary 'dictFunctions' should contain pairs of the following type:
        function-name:callable-object (ie. 'exp':math.exp, 'Foo':user-defined-function-with-arbitrary-number-of-arguments)
    """
    
    tokens = [
        'NAME', 'NUMBER', 'FLOAT',
        'PLUS','MINUS','TIMES','DIVIDE','EXP','EQUALS',
        'LPAREN','RPAREN','PERIOD', 'COMMA',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
        'AND', 'OR'
        ] + list(functions.values()) #+ list(logical_operator.values())

    precedence = [
                    ('left', 'PLUS', 'MINUS'),
                    ('left', 'TIMES', 'DIVIDE'),
                    ('left', 'EXP')
                ]


    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'
    t_EXP     = r'\*\*'

    t_EQ = r'=='
    t_NE = r'!='
    t_GT = r'>'
    t_GE = r'>='
    t_LT = r'<'
    t_LE = r'<='
    t_AND = r'&&'
    t_OR  = r'\|\|'

    t_COMMA   = r','
    t_EQUALS  = r'='
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'
    t_PERIOD  = r'\.'

    #t_PI = r'pi'

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        if t.value in functions:
            t.type = functions[t.value]
        #elif t.value in logical_operator:
        #    t.type = logical_operator[t.value]
        else:
            t.type = 'NAME'
        return t

    t_NUMBER = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'

    exponent_part = r"""([eE][-+]?[0-9]+)"""
    fract_const   = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
    t_FLOAT = '(((('+fract_const+')'+exponent_part+'?)|([0-9]+'+exponent_part+'))[FfLl]?)'
    #t_FLOAT = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print("Illegal character '{0}' found while parsing '{1}'".format(t.value[0], t.value))
        #t.lexer.skip(1)

    # Parser rules:
    # expression:
    def p_expression_1(self, p): 
        'expression : assignment_expression'
        p[0] = p[1]

    def p_expression_2(self, p):
        'expression : expression COMMA assignment_expression'
        p[0] = p[1] + p[3]

    # assigment_expression:
    def p_assignment_expression_1(self, p):
        'assignment_expression : conditional_expression'
        p[0] = p[1]

    def p_assignment_expression_2(self, p):
        'assignment_expression : identifier EQUALS assignment_expression'
        p[0] = AssignmentNode(p[1], p[3])
        #'assignment_expression : shift_expression EQUALS assignment_expression'

    # conditional-expression
    def p_conditional_expression_1(self, p):
        'conditional_expression : or_expression'
        p[0] = p[1]

    # OR-expression
    def p_or_expression_1(self, p):
        'or_expression : and_expression'
        p[0] = p[1]

    def p_or_expression_2(self, p):
        'or_expression : or_expression OR and_expression'
        p[0] = (p[1] | p[3])

    # AND-expression
    def p_and_expression_1(self, p):
        'and_expression : equality_expression'
        p[0] = p[1]

    def p_and_expression_2(self, p):
        'and_expression : and_expression AND equality_expression'
        p[0] = (p[1] & p[3])

    # equality-expression:
    def p_equality_expression_1(self, p):
        'equality_expression : relational_expression'
        p[0] = p[1]

    def p_equality_expression_2(self, p):
        'equality_expression : equality_expression EQ relational_expression'
        p[0] = (p[1] == p[3])

    def p_equality_expression_3(self, p):
        'equality_expression : equality_expression NE relational_expression'
        p[0] = (p[1] != p[3])

    # relational-expression:
    def p_relational_expression_1(self, p):
        'relational_expression : shift_expression'
        p[0] = p[1]

    def p_relational_expression_2(self, p):
        'relational_expression : relational_expression LT shift_expression'
        p[0] = p[1] < p[3]

    def p_relational_expression_3(self, p):
        'relational_expression : relational_expression GT shift_expression'
        p[0] = p[1] > p[3]

    def p_relational_expression_4(self, p):
        'relational_expression : relational_expression LE shift_expression'
        p[0] = p[1] <= p[3]

    def p_relational_expression_5(self, p):
        'relational_expression : relational_expression GE shift_expression'
        p[0] = p[1] >= p[3]

    # shift-expression
    def p_shift_expression_1(self, p):
        'shift_expression : additive_expression'
        p[0] = p[1]

    # additive-expression
    def p_additive_expression_1(self, p):
        'additive_expression : multiplicative_expression'
        p[0] = p[1]

    def p_additive_expression_2(self, p):
        'additive_expression : additive_expression PLUS multiplicative_expression'
        p[0] = p[1] + p[3]

    def p_additive_expression_3(self, p):
        'additive_expression : additive_expression MINUS multiplicative_expression'
        p[0] = p[1] - p[3]

    # multiplicative-expression
    def p_multiplicative_expression_1(self, p):
        'multiplicative_expression : power_expression'
        p[0] = p[1]

    def p_multiplicative_expression_2(self, p):
        'multiplicative_expression : multiplicative_expression DIVIDE power_expression'
        p[0] = p[1] / p[3]

    def p_multiplicative_expression_3(self, p):
        'multiplicative_expression : multiplicative_expression TIMES power_expression'
        p[0] = p[1] * p[3]


    def p_power_expression_1(self, p):
        'power_expression : unary_expression'
        p[0] = p[1]

    def p_power_expression_2(self, p):
        'power_expression : power_expression EXP unary_expression'
        p[0] = p[1] ** p[3]

    # unary-expression:
    def p_unary_expression_1(self, p):
        'unary_expression : postfix_expression'
        p[0] = p[1]

    def p_unary_expression_2(self, p):
        'unary_expression : unary_operator'
        p[0] = p[1]

    # unary-operator:
    def p_unary_operator(self, p):
        '''
        unary_operator : PLUS  postfix_expression
                    | MINUS postfix_expression
        '''
        if p[1] == '+':
            p[0] = p[2]
        elif p[1] == '-':
            p[0] = - p[2]

    # postfix-expression:
    def p_postfix_expression_1(self, p):
        """postfix_expression : primary_expression"""
        p[0] = p[1]

    def p_postfix_expression_2(self, p):
        """
        postfix_expression : sin   LPAREN expression RPAREN
                        | cos   LPAREN expression RPAREN
                        | tan   LPAREN expression RPAREN
                        | asin  LPAREN expression RPAREN
                        | acos  LPAREN expression RPAREN
                        | atan  LPAREN expression RPAREN
                        | sinh  LPAREN expression RPAREN
                        | cosh  LPAREN expression RPAREN
                        | tanh  LPAREN expression RPAREN
                        | asinh LPAREN expression RPAREN
                        | acosh LPAREN expression RPAREN
                        | atanh LPAREN expression RPAREN
                        | exp   LPAREN expression RPAREN
                        | sqrt  LPAREN expression RPAREN
                        | log   LPAREN expression RPAREN
                        | log10 LPAREN expression RPAREN
                        | ceil  LPAREN expression RPAREN
                        | floor LPAREN expression RPAREN
                        | fabs  LPAREN expression RPAREN
        """
        p[0] = Number(StandardFunctionNode(p[1], p[3]))

    def p_postfix_expression_3(self, p):
        '''postfix_expression : postfix_expression PERIOD NAME'''
        p[0] = Number(IdentifierNode(p[1].Node.Name + '.' + p[3]))

    def p_postfix_expression_4(self, p):
        '''postfix_expression : postfix_expression LPAREN argument_expression_list RPAREN'''
        #print(str(p[1]) + '(' + str(p[3]) + ')')
        p[0] = Number(NonstandardFunctionNode(str(p[1]), p[3]))

    def p_postfix_expression_5(self, p):
        '''postfix_expression : postfix_expression LPAREN RPAREN'''
        #print(str(p[1]) + '()')
        p[0] = Number(NonstandardFunctionNode(str(p[1]), []))

    # primary-expression
    def p_primary_expression(self, p):
        '''primary_expression :  identifier
                            |  constant
                            |  LPAREN expression RPAREN'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 4:
            p[0] = p[2]

    # argument-expression-list:
    def p_argument_expression_list(self, p):
        '''argument_expression_list :  assignment_expression
                                    |  argument_expression_list COMMA assignment_expression'''
        arguments = []
        if len(p) == 2:
            arguments.append(p[1])
        elif len(p) == 4:
            for arg in list(p[1]):
                arguments.append(arg)
            arguments.append(p[3])

        p[0] = arguments

    def p_constant_1(self, p):
        """constant : NUMBER"""
        p[0] = Number(ConstantNode(int(p[1])))

    def p_constant_2(self, p):
        """constant : FLOAT"""
        p[0] = Number(ConstantNode(float(p[1])))

    def p_identifier(self, p):
        """identifier : NAME"""
        p[0] = Number(IdentifierNode(p[1]))

    def p_error(self, p):
        raise Exception("Syntax error at '%s'" % p.value)

    def __init__(self, dictIdentifiers = None, dictFunctions = None):
        self.lexer            = lex.lex(module=self) # optimize=1)
        self.parser           = yacc.yacc(module=self, debug=False, write_tables = 0) # optimize=1)
        self.parseResult      = None
        self.dictIdentifiers  = dictIdentifiers
        self.dictFunctions    = dictFunctions

    def parse_and_evaluate(self, expression):
        self.parse(expression)
        return self.evaluate()

    def parse_to_latex(self, expression):
        self.parse(expression)
        return self.toLatex()

    def parse_to_mathml(self, expression):
        self.parse(expression)
        return self.toMathML()

    def parse(self, expression):
        self.parseResult = self.parser.parse(expression, lexer = self.lexer)
        return self.parseResult

    def toLatex(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        return self.parseResult.toLatex()

    def toMathML(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        return self.parseResult.toMathML()

    def evaluate(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        if self.dictIdentifiers is None:
            raise RuntimeError('dictIdentifiers not set')
        if self.dictFunctions is None:
            raise RuntimeError('dictFunctions not set')

        node = None
        if isinstance(self.parseResult, Number):
            node = self.parseResult.Node
        elif isinstance(self.parseResult, Condition):
            node = self.parseResult.CondNode
        elif isinstance(self.parseResult, AssignmentNode):
            node = self.parseResult
        else:
            raise RuntimeError('Invalid parse result type')

        result = node.evaluate(self.dictIdentifiers, self.dictFunctions)
        return result

def testExpression(expression, expected_res, do_evaluation = True):
    parse_res  = parser.parse(expression)
    latex_res  = parser.toLatex()
    mathml_res = parser.toMathML()
    print('Expression: ' + expression)
    #print('NodeTree:\n', repr(parse_res))
    print('Parse result: ', str(parse_res))
    print('Latex: ', latex_res)
    print('MathML: ', mathml_res)
    eval_res = 0
    if do_evaluation:
        eval_res = parser.evaluate()
        if fabs(eval_res - expected_res) > 0:
            raise RuntimeError('Expression evaluation failed: {0} (evaluated {1}; expected {2})'.format(expression, eval_res, expected_res))
        else:
            print('Evaluate result: OK (={0})'.format(eval_res))
    print(' ')

    return parse_res, latex_res, eval_res
    
def testLatex(parser):
    operators = ['+', '-', '*', '/', '**']
    l = 'x_1'
    r = 'x_2'
    counter = 0
    for lop in operators:
        for rop in operators:
            for op in operators:
                expression   = l + lop + r + op + l + rop + r
                parse_res    = parser.parse(expression)
                latex_res    = parser.toLatex()
                print('\\begin{verbatim}' + str(counter) + '. ' + expression + '\\end{verbatim}\n')
                print('\\begin{verbatim}Parse result: ' + str(parse_res) + '\\end{verbatim}\n')
                print('$' + latex_res + '$\n\n')
                counter += 1

def Sum(a1, a2, a3):
    return a1 + a2 + a3

def step(t0, amplitude):
    return amplitude

def impulse(t0, amplitude):
    return amplitude

def linear(t0, t1, start, end):
    return end

if __name__ == "__main__":
    dictIdentifiers = {}
    dictFunctions   = {}

    # Some dummy identifiers:values
    y       = 10.0
    x1      =  1.0
    x2      =  2.0
    x3      =  3.0
    x4      =  4.0
    m1_x    =  2.11
    m1_m2_y = 10.12
    R       =  0.0

    # identifiers
    dictIdentifiers['pi']      = pi
    dictIdentifiers['e']       = e
    dictIdentifiers['y']       = y
    dictIdentifiers['x1']      = x1
    dictIdentifiers['x2']      = x2
    dictIdentifiers['x3']      = x3
    dictIdentifiers['x4']      = x4
    dictIdentifiers['m1.x']    = m1_x
    dictIdentifiers['m1.m2.y'] = m1_m2_y
    dictIdentifiers['R']       = R

    # Standard functions
    dictFunctions['__create_constant__'] = float
    dictFunctions['log10']  = log10
    dictFunctions['log']    = log
    dictFunctions['sqrt']   = sqrt
    dictFunctions['exp']    = exp
    dictFunctions['ceil']   = ceil
    dictFunctions['floor']  = floor
    dictFunctions['fabs']   = fabs
    dictFunctions['sin']    = sin
    dictFunctions['cos']    = cos
    dictFunctions['tan']    = tan
    dictFunctions['asin']   = asin
    dictFunctions['acos']   = acos
    dictFunctions['atan']   = atan
    dictFunctions['sinh']   = sinh
    dictFunctions['cosh']   = cosh
    dictFunctions['tanh']   = tanh
    dictFunctions['asinh']  = asinh
    dictFunctions['acosh']  = acosh
    dictFunctions['atanh']  = atanh

    # Nonstandard functions (custom functions)
    dictFunctions['Sum']      = Sum
    dictFunctions['step']     = step
    dictFunctions['impulse']  = impulse
    dictFunctions['linear']   = linear

    print('Identifiers:\n', dictIdentifiers, '\n')
    print('Functions:\n', dictFunctions, '\n')

    parser = ExpressionParser(dictIdentifiers, dictFunctions)

    #testLatex(parser)

    testExpression('step(1.2, 1.2)', 1.2)
    testExpression('impulse(1.2, 1.2)', 1.2)
    testExpression('linear(0.0, 1.0, 5, 10)', 10)
    #exit(0)

    testExpression('log10(pi)', log10(pi))
    testExpression('log(pi)',   log(pi))
    testExpression('sqrt(pi)',  sqrt(pi))
    testExpression('exp(pi)',   exp(pi))
    testExpression('ceil(pi)',  ceil(pi))
    testExpression('floor(pi)', floor(pi))

    testExpression('sin(pi)', sin(pi))
    testExpression('cos(pi)', cos(pi))
    testExpression('tan(pi)', tan(pi))
    testExpression('asin(1)', asin(1))
    testExpression('acos(1)', acos(1))
    testExpression('atan(1)', atan(1))

    testExpression('sinh(pi)', sinh(pi))
    testExpression('cosh(pi)', cosh(pi))
    testExpression('tanh(pi)', tanh(pi))
    testExpression('asinh(pi)', asinh(pi))
    testExpression('acosh(pi)', acosh(pi))
    testExpression('atanh(0.1)', atanh(0.1))

    testExpression('x1 + x2', x1 + x2)
    testExpression('x1 - x2', x1 - x2)
    testExpression('x1 * x2', x1 * x2)
    testExpression('x1 / x2', x1 / x2)
    testExpression('x1 ** x2', x1 ** x2)

    testExpression('Sum(pi, -1.5E-07, sqrt(4))', Sum(pi, -1.5E-07, sqrt(4)))
    testExpression('-sqrt(m1.m2.y + 2) / exp(-m1.x)', -sqrt(m1_m2_y + 2) / exp(-m1_x))
    testExpression('(-exp(y + x2 / x4) + 4.0) - x1', (-exp(y + x2 / x4) + 4.0) - x1)
    parse_res, latex_res, eval_res = testExpression('R = sin(x1 + x3)/x4', sin(x1 + x3)/x4)
    print('Updated dictIdentifiers[R] = {0}\n'.format(dictIdentifiers['R']))
    testExpression('(y + 4.0 >= x3 - 3.2e-03) || (y != 3) && (x1 <= 5)', (y + 4.0 >= x3 - 3.2e-03) or (y != 3) and (x1 <= 5))
    testExpression('(v_rest - V)/tau_m + (gE*(e_rev_E - V) + gI*(e_rev_I - V) + i_offset)/cm', 0, False)
    testExpression('x1 > x2', x1 > x2)

