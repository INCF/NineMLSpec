from __future__ import print_function
import os, sys, operator, math
import ply.lex as lex
import ply.yacc as yacc
import parser_objects
from parser_objects import Number, BinaryNode, IdentifierNode, ConstantNode
from units_parser import UnitsParser, QuantityParser
from expression_parser import ExpressionParser
try:
    from daetools.pyDAE import pyUnits, pyCore
except ImportError as e:
    print(e)

def testConsistency(parser, expression, expected_units):
    parse_res    = parser.parse(expression)
    latex_res    = parser.toLatex()
    print('Expression: ' + expression)
    #print('NodeTree:\n', repr(parse_res))
    print('Parse result: ', str(parse_res))
    try:
        # If no exception has been thrown everything is fine
        eval_res = parser.evaluate()
        print('Units consistency: OK, evaluated {0}, expected {1}\n'.format(eval_res.units, expected_units))
    except RuntimeError as e:
        print('Units consistency failed: {0}\n'.format(str(e)))
        
def testExpression(parser, expression, do_evaluation = True):
    parse_res    = parser.parse(expression)
    latex_res    = parser.toLatex()
    print('Expression: ' + expression)
    #print('NodeTree:\n', repr(parse_res))
    print('Parse result string: ', str(parse_res))
    print('Parse result latex: ', parser.toLatex())
    print('Parse result mathml: ', parser.toMathML())
    if do_evaluation:
        eval_res = parser.evaluate()
        print('Evaluate result: {0}'.format(str(eval_res)))
    print(' ')

def testUnitsConsistency():
    dictIdentifiers = {}
    dictFunctions   = {}

    # Define some 'quantity' objects (they have 'value' and 'units')
    y   = 15   * pyUnits.mm
    x1  = 1.0  * pyUnits.m
    x2  = 0.2  * pyUnits.km
    x3  = 15   * pyUnits.N
    x4  = 1.25 * pyUnits.kJ
    print('y  = {0} ({1} {2})'.format(y,  y.valueInSIUnits,  y.units.baseUnit))
    print('x1 = {0} ({1} {2})'.format(x1, x1.valueInSIUnits, x1.units.baseUnit))
    print('x2 = {0} ({1} {2})'.format(x2, x2.valueInSIUnits, x2.units.baseUnit))
    print('x3 = {0} ({1} {2})'.format(x3, x3.valueInSIUnits, x3.units.baseUnit))
    print('x4 = {0} ({1} {2})'.format(x4, x4.valueInSIUnits, x4.units.baseUnit))

    #print('x1({0}) == x2({1}) ({2})'.format(x1, x2, x1 == x2))
    #print('x1({0}) != x2({1}) ({2})'.format(x1, x2, x1 != x2))
    #print('x1({0}) > x2({1}) ({2})'.format(x1, x2, x1 > x2))
    #print('x1({0}) >= x2({1}) ({2})'.format(x1, x2, x1 >= x2))
    #print('x1({0}) < x2({1}) ({2})'.format(x1, x2, x1 < x2))
    #print('x1({0}) <= x2({1}) ({2})'.format(x1, x2, x1 <= x2))
    
    # quantity in [m]
    z = 1 * pyUnits.m
    print(z)
    z.value = 12.4 * pyUnits.mm # set a new value given in [mm]
    print(z)
    z.value = 0.32 * pyUnits.km # set a new value given in [km]
    print(z)
    z.value = 1 # set a new value in units in the quantity object, here in [m]
    print(z)
    
    # Define identifiers for the parser
    dictIdentifiers['pi'] = math.pi
    dictIdentifiers['e']  = math.e
    dictIdentifiers['y']  = y
    dictIdentifiers['x1'] = x1
    dictIdentifiers['x2'] = x2
    dictIdentifiers['x3'] = x3
    dictIdentifiers['x4'] = x4

    # Define math. functions for the parser
    dictFunctions['__create_constant__'] = float
    dictFunctions['sin']   = pyCore.Sin
    dictFunctions['cos']   = pyCore.Cos
    dictFunctions['tan']   = pyCore.Tan
    dictFunctions['asin']  = pyCore.ASin
    dictFunctions['acos']  = pyCore.ACos
    dictFunctions['atan']  = pyCore.ATan
    dictFunctions['sinh']  = pyCore.Sinh
    dictFunctions['cosh']  = pyCore.Cosh
    dictFunctions['tanh']  = pyCore.Tanh
    dictFunctions['asinh'] = pyCore.ASinh
    dictFunctions['acosh'] = pyCore.Cosh
    dictFunctions['atanh'] = pyCore.ATanh
    dictFunctions['log10'] = pyCore.Log10
    dictFunctions['log']   = pyCore.Log
    dictFunctions['sqrt']  = pyCore.Sqrt
    dictFunctions['exp']   = pyCore.Exp
    dictFunctions['floor'] = pyCore.Floor
    dictFunctions['ceil']  = pyCore.Ceil
    dictFunctions['abs']   = pyCore.Abs

    #print('Identifiers:\n', dictIdentifiers, '\n')
    #print('Functions:\n', dictFunctions, '\n')

    parser = ExpressionParser(dictIdentifiers, dictFunctions)

    testConsistency(parser, 'x1 * x3', pyUnits.kJ)                  # OK
    testConsistency(parser, 'x1 - x3', None)                        # Fail
    testConsistency(parser, 'x1 * y', pyUnits.m**2)                 # OK
    testConsistency(parser, '1 + x1/x2 + x1*x3/x4', pyUnits.unit()) # OK
    
def testDimensionsParser():
    dictIdentifiers = {
                        'L' : pyUnits.m,
                        'M' : pyUnits.kg,
                        'T' : pyUnits.s,
                        'I' : pyUnits.A,
                        'O' : pyUnits.K,
                        'J' : pyUnits.cd,
                        'N' : pyUnits.mol,
                        ''  : pyUnits.unit
                      }
    parser = UnitsParser(dictIdentifiers)

    print('######################################################')
    print('          testDimensionsParser')
    print('######################################################')
    testExpression(parser, 'M')
    testExpression(parser, 'M T^2 J^-2')
    testExpression(parser, 'M^5 L^-2 O')

def testUnitsParser():
    """
    daetools define a large number of units:
    - all base and derived SI units
    - All of these with prefixes tera(T), giga(G), mega(M), kilo(k), hecto(h), deka(da),
    deci(d), centi(c), mili(m), micro(u), nano(n), pico(p)
    All are imported into the pyUnits module. Here we filter those symbols and add them
    to the dictionary that will be used to evaluate the AST after the parsing phase.
    """
    dictIdentifiers = {
                        ''  : pyUnits.unit() # Non-dimensional
                      }
    for attr in dir(pyUnits):
        obj = getattr(pyUnits, attr)
        if isinstance(obj, pyUnits.unit):
            dictIdentifiers[attr] = obj

    print('Supported units: %s' % sorted(dictIdentifiers))
    parser = UnitsParser(dictIdentifiers)

    print('######################################################')
    print('          testUnitsParser')
    print('######################################################')
    testExpression(parser, 'kg')
    testExpression(parser, 'kg m')
    testExpression(parser, 's kg^-1 m^-2')
    testExpression(parser, 's kg^-1 mm^2')

def testQuantityParser():
    dictIdentifiers = {
                        ''  : pyUnits.unit() # Non-dimensional
                      }
    for attr in dir(pyUnits):
        obj = getattr(pyUnits, attr)
        if isinstance(obj, pyUnits.unit):
            dictIdentifiers[attr] = obj

    #print('Supported units: %s' % sorted(dictIdentifiers))

    dictFunctions = {
                      '__create_quantity__' : pyUnits.quantity
                    }

    parser = QuantityParser(dictIdentifiers, dictFunctions)
    
    print('######################################################')
    print('          testQuantityParser')
    print('######################################################')

    testExpression(parser, '.1 kg')
    testExpression(parser, '-1.067e-09 s kg^-1 m^-2')
    testExpression(parser, '-1.067')
    testExpression(parser, '-1.067E-07 s kg^-1 m^-2')

if __name__ == "__main__":
    #testDimensionsParser()
    #testUnitsParser()
    #testUnitsConsistency()
    testQuantityParser()
