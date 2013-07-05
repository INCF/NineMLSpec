#!/usr/bin/env python

"""********************************************************************************
                          parser_objects.py
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

import os, sys, operator, math, numbers, inspect
from copy import copy, deepcopy

class Node(object):
    def toLatex(self):
        pass
    
    def toMathML(self):
        pass

    def evaluate(self, dictIdentifiers, dictFunctions):
        pass

class ConstantNode(Node):
    def __init__(self, value):
        self.Value = value

    def __repr__(self):
        return 'ConstantNode({0})'.format(self.Value)

    def __str__(self):
        return str(self.Value)

    def toLatex(self):
        return str(self.Value)

    def toMathML(self):
        return '<mn>{0}</mn>'.format(self.Value)

    def evaluate(self, dictIdentifiers, dictFunctions):
        if dictFunctions and '__create_constant__' in dictFunctions:
            return dictFunctions['__create_constant__'](self.Value)
        else:
            return self.Value

class QuantityNode(Node):
    def __init__(self, value, units):
        self.node_value = value
        self.node_units = units

    def __repr__(self):
        return 'QuantityNode({0}, {1})'.format(repr(self.node_value), repr(self.node_units))

    def __str__(self):
        return '{0} {1}'.format(str(self.node_value), str(self.node_units))

    def toLatex(self):
        return '{{{0} {1}}}'.format(self.node_value.toLatex(), self.node_units.toLatex())

    def toMathML(self):
        return '<mrow>{0} {1}</mrow>'.format(self.node_value.toMathML(), self.node_units.toMathML())

    def evaluate(self, dictIdentifiers, dictFunctions):
        _value = self.node_value.evaluate(dictIdentifiers, dictFunctions)
        _units = self.node_units.evaluate(dictIdentifiers, dictFunctions)

        if '__create_quantity__' in dictFunctions:
            return dictFunctions['__create_quantity__'](_value, _units)
        else:
            raise RuntimeError('Cannot create a quantity {0} (the identifier "__create_quantity__" not found in the functions dictionary'.format(str(self)))

class AssignmentNode(Node):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression

    def __repr__(self):
        return 'AssignmentNode({0}, =, {1})'.format(repr(self.identifier), repr(self.expression))

    def __str__(self):
        return '{0} = {1}'.format(str(self.identifier), str(self.expression))

    def toLatex(self):
        return '{0} = {1}'.format(self.identifier.toLatex(), self.expression.toLatex())

    def toMathML(self):
        return '<mrow>{0} = {1}</mrow>'.format(self.identifier.toMathML(), self.expression.toMathML())

    def evaluate(self, dictIdentifiers, dictFunctions):
        value = self.expression.Node.evaluate(dictIdentifiers, dictFunctions)
        dictIdentifiers[self.identifier.Node.Name] = value
        return value

class IdentifierNode(Node):
    def __init__(self, name):
        self.Name = name

    def __repr__(self):
        return 'IdentifierNode({0})'.format(repr(self.Name))

    def __str__(self):
        return self.Name

    def toLatex(self):
        return self.Name

    def toMathML(self):
        return '<mi fontstyle="italic">{0}</mi>'.format(self.Name)

    def evaluate(self, dictIdentifiers, dictFunctions):
        if not self.Name in dictIdentifiers:
            raise RuntimeError('Identifier {0} not found in the identifiers dictionary'.format(self.Name))
        
        value = dictIdentifiers[self.Name]
        if hasattr(value, '__float__'):
            # If it is a simple number or an object that emulate a number-type behaviour
            return float(value)
        else:
            # It's an ordinary object; just return its name
            return dictIdentifiers[self.Name]


class StandardFunctionNode(Node):
    functions = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
                 'sqrt', 'exp', 'log', 'log10', 'ceil', 'floor', 'abs']

    def __init__(self, function, expression):
        if not (function in StandardFunctionNode.functions):
            raise RuntimeError('The function {0} is not supported'.format(function))

        self.Function = function
        self.Node     = expression.Node

    def __repr__(self):
        return 'StandardFunctionNode({0}, {1})'.format(self.Function, repr(self.Node))

    def __str__(self):
        return '{0}({1})'.format(self.Function, str(self.Node))

    def toLatex(self):
        if self.Function == 'sqrt':
            return '\\sqrt{{{0}}}'.format(self.Node.toLatex())
        elif self.Function == 'exp':
            return 'e ^ {{{0}}}'.format(self.Node.toLatex())
        else:
            return '{0} \\left( {1} \\right)'.format(self.Function, self.Node.toLatex())

    def toMathML(self):
        if self.Function == 'sqrt':
            return '<mrow> <msqrt> {0} </msqrt> </mrow>'.format(self.Node.toMathML())
        elif self.Function == 'exp':
            return '<mrow> <msup> <mi fontstyle="italic">e</mi> <mrow>{0}</mrow> </msup> </mrow>'.format(self.Node.toMathML())
        else:
            return '<mrow> <mi fontstyle="italic">{0}</mi> <mrow> <mo>(</mo> {1} <mo>)</mo> </mrow> </mrow>'.format(self.Function, self.Node.toMathML())
            
    def evaluate(self, dictIdentifiers, dictFunctions):
        if not self.Function in dictFunctions:
            raise RuntimeError('The function {0} not found in the functions dictionary'.format(self.Function))
        
        fun = dictFunctions[self.Function]
        if not hasattr(fun, '__call__'):
            raise RuntimeError('The function {0} in the dictionary is not a callable object'.format(self.Function))
        argument0 = self.Node.evaluate(dictIdentifiers, dictFunctions)
        return fun(argument0)

class NonstandardFunctionNode(Node):
    def __init__(self, function, argument_list = []):
        self.Function          = function
        self.ArgumentsNodeList = []
        for arg in argument_list:
            self.ArgumentsNodeList.append(arg.Node)

    def __repr__(self):
        argument_list = ''
        for i in range(0, len(self.ArgumentsNodeList)):
            node = self.ArgumentsNodeList[i]
            if i == 0:
                argument_list += repr(node)
            else:
                argument_list += ', ' + repr(node)
        return 'NonstandardFunctionNode({0}, {1})'.format(self.Function, argument_list)

    def __str__(self):
        argument_list = ''
        for i in range(0, len(self.ArgumentsNodeList)):
            node = self.ArgumentsNodeList[i]
            if i == 0:
                argument_list += str(node)
            else:
                argument_list += ', ' + str(node)
        return '{0}({1})'.format(self.Function, argument_list)

    def toLatex(self):
        argument_list = ''
        for i in range(0, len(self.ArgumentsNodeList)):
            node = self.ArgumentsNodeList[i]
            if i == 0:
                argument_list += node.toLatex()
            else:
                argument_list += ', ' + node.toLatex()
        return '{0} \\left( {1} \\right)'.format(self.Function, argument_list)
    
    def toMathML(self):
        argument_list = '<mfenced>'
        for node in self.ArgumentsNodeList:
            argument_list += ' <mi>{0}</mi> '.format(node.toMathML())
        argument_list += '</mfenced>'
        return '<mrow> <mi fontstyle="italic">{0}</mi> <mrow>{1}</mrow> </mrow>'.format(self.Function, argument_list)

    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Function in dictFunctions:
            fun = dictFunctions[self.Function]
            if not hasattr(fun, '__call__'):
                raise RuntimeError('The function {0} in the dictionary is not a callable object'.format(self.Function))
            
            argument_list = ()
            for node in self.ArgumentsNodeList:
                argument_list = argument_list + (node.evaluate(dictIdentifiers, dictFunctions), )
            print(self.Function, fun)
            (args, varargs, keywords, defaults) = inspect.getargspec(fun)
            #print(args, varargs, keywords, defaults)
            
            no_args          = len(argument_list)
            no_required_args = 0
            no_default_args  = 0
            if args:
                no_required_args = len(args)
            if defaults:
                no_default_args = len(defaults)
            
            if (no_args > no_required_args) or (no_args < no_required_args-no_default_args):
                raise RuntimeError('The number of provided arguments ({0}) of the function [{1}] does not match the number of expected arguments: {1}({2})'.format(no_args, self.Function, ', '.join(args)))
            
            return fun(*argument_list)
        
        else:
            raise RuntimeError('The function {0} not found in the functions dictionary'.format(self.Function))

class UnaryNode(Node):
    opMinus = '-'
    opPlus  = '+'

    def __init__(self, operator, node):
        self.Node     = node
        self.Operator = operator

    def __repr__(self):
        return 'UnaryNode({0}{1})'.format(self.Operator, repr(self.Node))

    def __str__(self):
        return '({0}{1})'.format(self.Operator, str(self.Node))

    def toLatex(self):
        return '{0}{1}'.format(self.Operator, self.encloseNode())

    def toMathML(self):
        return '<mrow> <mo>{0}</mo> <mrow> {1} </mrow> </mrow>'.format(self.Operator, self.encloseMathMLNode())

    def enclose(self, doEnclose):
        if doEnclose:
            return '\\left( ' + self.Node.toLatex() + ' \\right)'
        else:
            return self.Node.toLatex()

    def encloseMathML(self, doEnclose):
        if doEnclose:
            return '<mrow> <mo>(</mo> ' + self.Node.toMathML() + ' <mo>)</mo> </mrow>'
        else:
            return self.Node.toMathML()

    def encloseNode(self):
        if isinstance(self.Node, ConstantNode):
            return self.enclose(False)

        elif isinstance(self.Node, IdentifierNode):
            return self.enclose(False)

        elif isinstance(self.Node, StandardFunctionNode):
            return self.enclose(False)

        elif isinstance(self.Node, UnaryNode):
            return self.enclose(True)

        elif isinstance(self.Node, BinaryNode):
            if (self.Node.Operator == '+') or (self.Node.Operator == '-'):
                return self.enclose(True)
            elif (self.Node.Operator == '*') or (self.Node.Operator == '/') or (self.Node.Operator == '^'):
                return self.enclose(False)
            else:
                return self.enclose(True)

        else:
            return self.enclose(True)

    def encloseMathMLNode(self):
        if isinstance(self.Node, ConstantNode):
            return self.encloseMathML(False)

        elif isinstance(self.Node, IdentifierNode):
            return self.encloseMathML(False)

        elif isinstance(self.Node, StandardFunctionNode):
            return self.encloseMathML(False)

        elif isinstance(self.Node, UnaryNode):
            return self.encloseMathML(True)

        elif isinstance(self.Node, BinaryNode):
            if (self.Node.Operator == '+') or (self.Node.Operator == '-'):
                return self.encloseMathML(True)
            elif (self.Node.Operator == '*') or (self.Node.Operator == '/') or (self.Node.Operator == '^'):
                return self.encloseMathML(False)
            else:
                return self.encloseMathML(True)

        else:
            return self.encloseMathML(True)

    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Operator == UnaryNode.opMinus:
            return (-self.Node.evaluate(dictIdentifiers, dictFunctions))
        elif self.Operator == UnaryNode.opPlus:
            return self.Node.evaluate(dictIdentifiers, dictFunctions)
        else:
            raise RuntimeError("Not supported unary operator: {0}".format(self.Operator))

class BinaryNode(Node):
    opMinus  = '-'
    opPlus   = '+'
    opMulti  = '*'
    opDivide = '/'
    opPower  = '^'

    def __init__(self, lnode, operator, rnode):
        self.lNode    = lnode
        self.rNode    = rnode
        self.Operator = operator

    def __repr__(self):
        return 'BinaryNode({0}, {1}, {2})'.format(repr(self.lNode), self.Operator, repr(self.rNode))

    def __str__(self):
        return '({0} {1} {2})'.format(str(self.lNode), self.Operator, str(self.rNode))

    def encloseLeft(self, doEnclose):
        if doEnclose:
            return '\\left( ' + self.lNode.toLatex() + ' \\right)'
        else:
            return self.lNode.toLatex()

    def encloseRight(self, doEnclose):
        if doEnclose:
            return '\\left( ' + self.rNode.toLatex() + ' \\right)'
        else:
            return self.rNode.toLatex()

    def encloseMathMLLeft(self, doEnclose):
        if doEnclose:
            return '<mo>(</mo> ' + self.lNode.toMathML() + ' <mo>)</mo>'
        else:
            return self.lNode.toMathML()

    def encloseMathMLRight(self, doEnclose):
        if doEnclose:
            return '<mo>(</mo> ' + self.rNode.toMathML() + ' <mo>)</mo>'
        else:
            return self.rNode.toMathML()

    def toLatex(self):
        if (self.Operator == '+'):
            # Default behaviour is to not enclose any
            left  = self.encloseLeft(False)
            right = self.encloseRight(False)

            # Right exceptions:
            if isinstance(self.rNode, UnaryNode):
                right = self.encloseRight(True)

            return '{0} + {1}'.format(left, right)

        elif (self.Operator == '-'):
            # Default behaviour is to enclose right
            left  = self.encloseLeft(False)
            right = self.encloseRight(True)

            # Right exceptions:
            if isinstance(self.rNode, ConstantNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, IdentifierNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, StandardFunctionNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, BinaryNode):
                if (self.rNode.Operator == '*') or (self.rNode.Operator == '/') or (self.rNode.Operator == '^'):
                    right = self.encloseRight(False)

            return '{0} - {1}'.format(left, right)

        elif (self.Operator == '*'):
            # Default behaviour is to enclose both
            left  = self.encloseLeft(True)
            right = self.encloseRight(True)

            # Left exceptions:
            if isinstance(self.lNode, ConstantNode):
                left = self.encloseLeft(False)
            elif isinstance(self.lNode, IdentifierNode):
                left = self.encloseLeft(False)
            elif isinstance(self.lNode, StandardFunctionNode):
                left = self.encloseLeft(False)
            elif isinstance(self.lNode, UnaryNode):
                left = self.encloseLeft(False)
            elif isinstance(self.lNode, BinaryNode):
                if (self.lNode.Operator == '*') or (self.lNode.Operator == '/') or (self.lNode.Operator == '^'):
                    left = self.encloseLeft(False)

            # Right exceptions:
            if isinstance(self.rNode, ConstantNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, IdentifierNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, StandardFunctionNode):
                right = self.encloseRight(False)
            elif isinstance(self.rNode, BinaryNode):
                if (self.rNode.Operator == '*') or (self.rNode.Operator == '/') or (self.rNode.Operator == '^'):
                    right = self.encloseRight(False)

            return '{0} \\cdot {1}'.format(left, right)

        elif (self.Operator == '/'):
            # Default behaviour is to not enclose any
            left  = self.encloseLeft(False)
            right = self.encloseRight(False)

            return '\\frac{{{0}}}{{{1}}}'.format(left, right)

        elif (self.Operator == '^'):
            # Default behaviour is to enclose left
            left  = self.encloseLeft(True)
            right = self.encloseRight(False)

            # Left exceptions:
            if isinstance(self.lNode, ConstantNode):
                left = self.encloseLeft(False)
            elif isinstance(self.lNode, IdentifierNode):
                left = self.encloseLeft(False)

            return '{{{0}}} ^ {{{1}}}'.format(left, right)

        else:
            # Default behaviour is to enclose both
            left  = self.encloseLeft(True)
            right = self.encloseRight(True)

            return '{0} {1} {2}'.format(left, self.Operator, right)

    def toMathML(self):
        if (self.Operator == '+'):
            # Default behaviour is to not enclose any
            left  = self.encloseMathMLLeft(False)
            right = self.encloseMathMLRight(False)
            
            # Right exceptions:
            if isinstance(self.rNode, UnaryNode):
                right = '<mo>(</mo> {0} <mo>)</mo>'.format(right)

            return '<mrow> {0} + {1} </mrow>'.format(left, right)

        elif (self.Operator == '-'):
            # Default behaviour is to enclose right
            left  = self.encloseMathMLLeft(False)
            right = self.encloseMathMLRight(True)


            # Right exceptions:
            if isinstance(self.rNode, ConstantNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, IdentifierNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, StandardFunctionNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, BinaryNode):
                if (self.rNode.Operator == '*') or (self.rNode.Operator == '/') or (self.rNode.Operator == '^'):
                    right = self.encloseMathMLRight(False)

            return '<mrow> {0} - {1} </mrow>'.format(left, right)

        elif (self.Operator == '*'):
            # Default behaviour is to enclose both
            left  = self.encloseMathMLLeft(True)
            right = self.encloseMathMLRight(True)

            # Left exceptions:
            if isinstance(self.lNode, ConstantNode):
                left = self.encloseMathMLLeft(False)
            elif isinstance(self.lNode, IdentifierNode):
                left = self.encloseMathMLLeft(False)
            elif isinstance(self.lNode, StandardFunctionNode):
                left = self.encloseMathMLLeft(False)
            elif isinstance(self.lNode, UnaryNode):
                left = self.encloseMathMLLeft(False)
            elif isinstance(self.lNode, BinaryNode):
                if (self.lNode.Operator == '*') or (self.lNode.Operator == '/') or (self.lNode.Operator == '^'):
                    left = self.encloseMathMLLeft(False)

            # Right exceptions:
            if isinstance(self.rNode, ConstantNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, IdentifierNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, StandardFunctionNode):
                right = self.encloseMathMLRight(False)
            elif isinstance(self.rNode, BinaryNode):
                if (self.rNode.Operator == '*') or (self.rNode.Operator == '/') or (self.rNode.Operator == '^'):
                    right = self.encloseMathMLRight(False)

            return '<mrow> {0} &sdot; {1} </mrow>'.format(left, right)

        elif (self.Operator == '/'):
            # Default behaviour is to not enclose any
            left  = self.encloseMathMLLeft(False)
            right = self.encloseMathMLRight(False)

            return '<mrow> <mfrac> {0} {1} </mfrac> </mrow>'.format(left, right)

        elif (self.Operator == '^'):
            # Default behaviour is to enclose left
            left  = self.encloseMathMLLeft(True)
            right = self.encloseMathMLRight(False)

            # Left exceptions:
            if isinstance(self.lNode, ConstantNode):
                left = self.encloseMathMLLeft(False)
            elif isinstance(self.lNode, IdentifierNode):
                left = self.encloseMathMLLeft(False)

            return '<mrow> <msup> {0} {1} </msup> </mrow>'.format(left, right)

        else:
            # Default behaviour is to enclose both
            left  = self.encloseMathMLLeft(True)
            right = self.encloseMathMLRight(True)

            return '<mrow> {0} {1} {2} </mrow>'.format(left, self.Operator, right)
            
    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Operator == BinaryNode.opPlus:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) + self.rNode.evaluate(dictIdentifiers, dictFunctions)

        elif self.Operator == BinaryNode.opMinus:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) - self.rNode.evaluate(dictIdentifiers, dictFunctions)

        elif self.Operator == BinaryNode.opMulti:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) * self.rNode.evaluate(dictIdentifiers, dictFunctions)

        elif self.Operator == BinaryNode.opDivide:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) / self.rNode.evaluate(dictIdentifiers, dictFunctions)

        elif self.Operator == BinaryNode.opPower:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) ** self.rNode.evaluate(dictIdentifiers, dictFunctions)

        else:
            raise RuntimeError("Not supported binary operator: {0}".format(self.Operator))

class ConditionNode(object):
    def evaluate(self, dictIdentifiers, dictFunctions):
        pass
    
    def toMathML(self):
        pass

"""
class ConditionUnaryNode(ConditionNode):
    opNot = 'not'

    def __init__(self, operator, node):
        self.Node     = node
        self.Operator = operator

    def __repr__(self):
        return 'ConditionUnaryNode({0}, {1})'.format(self.Operator, repr(self.Node))

    def __str__(self):
        return '({0} {1})'.format(self.Operator, str(self.Node))

    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Operator == ConditionUnaryNode.opNot:
            return operator.not_(self.Node.evaluate(dictIdentifiers, dictFunctions))
        else:
            raise RuntimeError("Not supported logical unary operator: {0}".format(self.Operator))
"""

class ConditionBinaryNode(ConditionNode):
    opEQ = '=='
    opNE = '!='
    opGT = '>'
    opGE = '>='
    opLT = '<'
    opLE = '<='

    def __init__(self, lnode, operator, rnode):
        self.lNode    = lnode
        self.rNode    = rnode
        self.Operator = operator

    def __repr__(self):
        return 'ConditionBinaryNode({0}, {1}, {2})'.format(repr(self.lNode), self.Operator, repr(self.rNode))

    def __str__(self):
        return '({0} {1} {2})'.format(str(self.lNode), self.Operator, str(self.rNode))

    def toLatex(self):
        if self.Operator == ConditionBinaryNode.opEQ:
            return '{0} == {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionBinaryNode.opNE:
            return '{0} \\neq {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionBinaryNode.opLT:
            return '{0} < {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionBinaryNode.opLE:
            return '{0} \\leq {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionBinaryNode.opGT:
            return '{0} > {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionBinaryNode.opGE:
            return '{0} \\geq {1}'.format(self.lNode.toLatex(), self.rNode.toLatex())
        else:
            raise RuntimeError("Not supported logical binary operator: {0}".format(self.Operator))

    def toMathML(self):
        if self.Operator == ConditionBinaryNode.opEQ:
            return '<mrow> {0} <mo>==</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionBinaryNode.opNE:
            return '<mrow> {0} <mo>!=</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionBinaryNode.opLT:
            return '<mrow> {0} <mo>&lt;</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionBinaryNode.opLE:
            return '<mrow> {0} <mo>&le;</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionBinaryNode.opGT:
            return '<mrow> {0} <mo>&gt;</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionBinaryNode.opGE:
            return '<mrow> {0} <mo>&ge;</mo> {1} </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        else:
            raise RuntimeError("Not supported logical binary operator: {0}".format(self.Operator))

    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Operator == ConditionBinaryNode.opEQ:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) == self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionBinaryNode.opNE:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) != self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionBinaryNode.opLT:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) < self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionBinaryNode.opLE:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) <= self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionBinaryNode.opGT:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) > self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionBinaryNode.opGE:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) >= self.rNode.evaluate(dictIdentifiers, dictFunctions)
        else:
            raise RuntimeError("Not supported logical binary operator: {0}".format(self.Operator))

class ConditionExpressionNode(ConditionNode):
    opAnd = '&&'
    opOr  = '||'

    def __init__(self, lnode, operator, rnode):
        self.lNode    = lnode
        self.rNode    = rnode
        self.Operator = operator

    def __repr__(self):
        return 'ConditionExpressionNode({0}, {1}, {2})'.format(repr(self.lNode), self.Operator, repr(self.rNode))

    def __str__(self):
        return '({0} {1} {2})'.format(str(self.lNode), self.Operator, str(self.rNode))

    def toLatex(self):
        if self.Operator == ConditionExpressionNode.opAnd:
            return '\\left( {0} \\right) \\land \\left( {1} \\right)'.format(self.lNode.toLatex(), self.rNode.toLatex())
        elif self.Operator == ConditionExpressionNode.opOr:
            return '\\left( {0} \\right) \\lor \\left( {1} \\right)'.format(self.lNode.toLatex(), self.rNode.toLatex())
        else:
            raise RuntimeError("Not supported logical binary operator: {0}".format(self.Operator))

    def toMathML(self):
        if self.Operator == ConditionExpressionNode.opAnd:
            return '<mrow> <mo>(</mo> {0} <mo>)</mo> <mi>and</mi> <mo>(</mo> {1} <mo>)</mo> </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        elif self.Operator == ConditionExpressionNode.opOr:
            return '<mrow> <mo>(</mo> {0} <mo>)</mo> <mi>or</mi> <mo>(</mo> {1} <mo>)</mo> </mrow>'.format(self.lNode.toMathML(), self.rNode.toMathML())
        else:
            raise RuntimeError("Not supported logical binary operator: {0}".format(self.Operator))

    def evaluate(self, dictIdentifiers, dictFunctions):
        if self.Operator == ConditionExpressionNode.opAnd:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) & self.rNode.evaluate(dictIdentifiers, dictFunctions)
        elif self.Operator == ConditionExpressionNode.opOr:
            return self.lNode.evaluate(dictIdentifiers, dictFunctions) | self.rNode.evaluate(dictIdentifiers, dictFunctions)
        else:
            raise RuntimeError("Not supported logical operator: {0}".format(self.Operator))


class Condition(object):
    def __init__(self, condNode):
        self.CondNode = condNode

    def __repr__(self):
        return repr(self.CondNode)

    def __str__(self):
        return str(self.CondNode)

    def toLatex(self):
        return self.CondNode.toLatex()
    
    def toMathML(self):
        return self.CondNode.toMathML()

    #def not_(self):
    #    return Condition(ConditionUnaryNode(ConditionUnaryNode.opNot,
    #                                        self.CondNode
    #                                       )
    #                    )

    def __and__(self, cond):
        return Condition(ConditionExpressionNode(self.CondNode,
                                                 ConditionExpressionNode.opAnd,
                                                 cond.CondNode
                                                )
                        )

    def __or__(self, cond):
        return Condition(ConditionExpressionNode(self.CondNode,
                                                 ConditionExpressionNode.opOr,
                                                 cond.CondNode
                                                )
                        )

def getOperand(val):
    operand = None
    if isinstance(val, float):
        operand = Number(ConstantNode(val))
    elif isinstance(val, Number):
        operand = val
    else:
        raise RuntimeError("Invalid operand type")
    return operand

class Number(object):
    def __init__(self, node):
        if node == None:
            raise RuntimeError("Invalid node")
        self.Node = node

    def __repr__(self):
        return 'Number({0})'.format(repr(self.Node))

    def __str__(self):
        return str(self.Node)

    def toLatex(self):
        return self.Node.toLatex()

    def toMathML(self):
        return self.Node.toMathML()

    def __neg__(self):
        return Number(UnaryNode(UnaryNode.opMinus, self.Node))

    def __pos__(self):
        return Number(UnaryNode(UnaryNode.opPlus, self.Node))

    def __add__(self, val):
        return Number(BinaryNode(self.Node,
                                 BinaryNode.opPlus,
                                 val.Node))

    def __sub__(self, val):
        return Number(BinaryNode(self.Node,
                                 BinaryNode.opMinus,
                                 val.Node))

    def __mul__(self, val):
        return Number(BinaryNode(self.Node,
                                 BinaryNode.opMulti,
                                 val.Node))

    def __div__(self, val):
        return Number(BinaryNode(self.Node,
                                 BinaryNode.opDivide,
                                 val.Node))

    def __pow__(self, val):
        return Number(BinaryNode(self.Node,
                                 BinaryNode.opPower,
                                 val.Node))

    def __eq__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opEQ,
                                             val.Node))

    def __ne__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opNE,
                                             val.Node))

    def __lt__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opLT,
                                             val.Node))

    def __le__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opLE,
                                             val.Node))

    def __gt__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opGT,
                                             val.Node))

    def __ge__(self, val):
        return Condition(ConditionBinaryNode(self.Node,
                                             ConditionBinaryNode.opGE,
                                             val.Node))


class Quantity(object):
    def __init__(self, node):
        if node == None:
            raise RuntimeError("Invalid node specified")
        self.Node = node

    def __repr__(self):
        return 'QuantityNode({0})'.format(repr(self.Node))

    def __str__(self):
        return str(self.Node)

    def toLatex(self):
        return self.Node.toLatex()

    def toMathML(self):
        return self.Node.toMathML()
