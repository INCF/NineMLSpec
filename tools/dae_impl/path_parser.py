from __future__ import print_function
import os, sys, operator, math
import ply.lex as lex
import ply.yacc as yacc

"""
"""
class pathItem(object):
    typeID        = 0
    typeIndexedID = 1
    typeSlicedID  = 2
    
    def __init__(self):
        self.Type  = None
        self.Name  = None
        self.Index = None
        self.Start = None 
        self.End = None 
    
    @classmethod
    def create(cls, name):
        path = pathItem()
        path.Type = pathItem.typeID
        path.Name = str(name)
        return path
    
    @classmethod
    def create_indexed(cls, name, index):
        path = pathItem()
        path.Type  = pathItem.typeIndexedID
        path.Name  = str(name)
        path.Index = int(index)
        return path
    
    @classmethod
    def create_sliced(cls, name, start, end):
        path = pathItem()
        path.Type  = pathItem.typeSlicedID
        path.Name  = str(name)
        path.Start = int(start)
        path.End   = int(end)
        return path
    
    def __str__(self):
        res = ''
        if self.Type == pathItem.typeID:
            res = '{0}'.format(self.Name)
        elif self.Type == pathItem.typeIndexedID:
            res = '{0}[{1}]'.format(self.Name, self.Index)
        elif self.Type == pathItem.typeSlicedID:
            res = '{0}[{1}:{2}]'.format(self.Name, self.Start, self.End)
        else:
            raise RuntimeError('')
        return res
    
    def __repr__(self):
        res = ''
        if self.Type == pathItem.typeID:
            res = 'pathItem({0})'.format(self.Name)
        elif self.Type == pathItem.typeIndexedID:
            res = 'pathItem({0}, {1})'.format(self.Name, self.Index)
        elif self.Type == pathItem.typeSlicedID:
            res = 'pathItem({0}, {1}, {2})'.format(self.Name, self.Start, self.End)
        else:
            raise RuntimeError('')
        return res
        
tokens = [ 'ID',
           'NUMBER',
           'LPAREN', 'RPAREN', 'PERIOD', 'COLON'
         ]


t_NUMBER  = r'(\+|-)?\d+'

t_COLON   = r':'
t_LPAREN  = r'\['
t_RPAREN  = r'\]'
t_PERIOD  = r'\.'

t_ignore = " \t\n"

t_ID = r'[a-zA-Z_ ][a-zA-Z_ 0-9]*'

def t_error(t):
    print("Illegal character '{0}' found while parsing '{1}'".format(t.value[0], t.value))
    #t.lexer.skip(1)

# Parser rules:
def p_expression(p):
    """expression : canonical_name"""
    p[0] = p[1]

def p_canonical_name(p):
    """canonical_name :  name
                      |  canonical_name PERIOD name"""
    if len(p) == 2:
        p[0] = p[1]
    
    elif len(p) == 4:
        p[0] = p[1] + p[3]
    
def p_name_1(p):
    """name : identifier"""
    p[0] = [ pathItem.create(p[1]) ]

def p_name_2(p):
    """name : identifier LPAREN NUMBER RPAREN"""
    p[0] = [ pathItem.create_indexed(p[1], int(p[3])) ]

def p_name_3(p):
    """name : identifier LPAREN NUMBER COLON NUMBER RPAREN"""
    p[0] = [ pathItem.create_sliced(p[1], int(p[3]), int(p[5])) ]

def p_identifier(p):
    """identifier : ID"""
    p[0] = str(p[1])

def p_error(p):
    raise Exception("Syntax error at '%s'" % p.value)

class CanonicalNameParser:
    def __init__(self):
        self.lexer  = lex.lex()
        self.parser = yacc.yacc()
        self.parseResult = None
        
    def parse(self, expression):
        self.parseResult = self.parser.parse(expression, lexer = self.lexer)
        return self.parseResult

if __name__ == "__main__":
    parser = CanonicalNameParser()
    print(parser.parse('uja[0]'))
    print(parser.parse('group.uja[0]'))
    print(parser.parse('group.uja[0].V'))
    print(parser.parse('group.uja[0:5].V'))
    for i in parser.parse('group.uja[0:5].V'):
        print('Item: {0} type: {1}'.format(i, type(i)))
