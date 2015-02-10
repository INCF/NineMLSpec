
import unittest
from nineml.abstraction_layer import (Expression,
                                      Alias, StateAssignment, TimeDerivative)
from nineml.abstraction_layer.expressions import ExpressionWithSimpleLHS, Constant
from nineml.exceptions import NineMLMathParseError
from nineml.abstraction_layer.units import coulomb
from nineml.abstraction_layer.componentclass.utils.xml import (
    ComponentClassXMLWriter as XMLWriter, ComponentClassXMLLoader as XMLLoader)
from nineml import Document


class Expression_test(unittest.TestCase):

    def test_Valid(self):
        # rhs, expt_vars, expt_funcs, result, values
        valid_rhses = [
            (('a'),                ('a'),                (), 5,            {'a': 5}, ),
            (('b'),                ('b'),                (), 7,            {'b': 7}, ),
            (('a+b'),              ('a', 'b'),
             (), 13,           {'a': 12, 'b': 1}),
            (('1./(alpha+2*beta)'),  ('alpha', 'beta'),
             (), 0.2,          {'alpha': 1, 'beta': 2}),
            (('pi'),                (),                  (), 3.14159265,   {}),
        ]

        for rhs, exp_var, exp_func, exp_res, params in valid_rhses:
            e = Expression(rhs)
            self.assertEquals(set(e.rhs_names), set(exp_var))
            self.assertEquals(set(e.rhs_funcs), set(exp_func))
            self.assertAlmostEqual(e.rhs_as_python_func()(**params), exp_res, places=4)

        import numpy
        expr_vars = [["-A/tau_r", ("A", "tau_r"), ()],
                    ["V*V", ("V",), ()],
                    ["a*(b*V - U)", ("U", "V", "b", "a"), ()],
                    [" 0.04*V*V + 5.0*V + 1. + 140.0 - U + Isyn", ("V", "U", "Isyn"), ()],
                    ["c", ("c"), ()],
                    ["1", (), ()],
                    ["atan2(sin(x),cos(y))", ("x", "y"), ("atan2", "sin", "cos")],
                    ["1.*V", ("V"), ()],
                    ["1.0", (), ()],
                    [".1", (), ()],
                    ["1/(1 + mg_conc*eta*exp(-1*gamma*V))", (
                        "mg_conc", "eta", "gamma", "V"), ('exp',)],
                    ["1 / ( 1 + mg_conc * eta *  exp( -1 * gamma*V))",
                     ("mg_conc", "eta", "gamma", "V"), ('exp',)],
                    ["1 / ( 1 + mg_conc * sin(0.5) *  exp ( -1 * gamma*V))",
                     ("mg_conc", "gamma", "V"), ('exp', "sin")],
                    [".1 / ( 1.0 + mg_conc * sin(V) *  exp ( -1.0 * gamma*V))",
                     ("mg_conc", "gamma", "V"), ('exp', "sin")],
                    ["sin(w)", ("w"), ("sin",)]]

        namespace = {
            "A": 10.0,
            "tau_r": 11.0,
            "V": -70.0,
            "a": 1.2,
            "b": 3.0,
            "U": -80.0,
            "Isyn": 2.0,
            "c": 10.0,
            "mg_conc": 1.0,
            "eta": 2.0,
            "gamma": -20.0,
            "x": 1.0,
            "y": 1.0,
            "w": numpy.arange(10)
        }

        return_values = [-0.909090909091, 4900.0, -156.0, 69.0, 10.0, 1,
                         1.0, -70.0, 1.0, 0.1, 1.0, 1.0, 1.0, 0.1, numpy.sin(namespace['w'])]

        for i, (expr, expt_vars, expt_funcs) in enumerate(expr_vars):
            c = Expression(expr)
            self.assertEqual(set(c.rhs_names), set(expt_vars))
            self.assertEqual(set(c.rhs_funcs), set(expt_funcs))

            python_func = c.rhs_as_python_func(namespace=namespace)
            param_dict = dict([(v, namespace[v]) for v in expt_vars])

            v = return_values[i] - python_func(**param_dict)
            self.assertAlmostEqual(numpy.dot(v, v), 0)

    def test_rhs_name_transform_inplace(self):
        # Signature: name(self, name_map)
                # Replace atoms on the RHS with values in the name_map

        e = Expression("V/(1 + mg_conc*eta*exp(-1*gamma*V*V)) * sin(V)")
        e.rhs_name_transform_inplace({'V': 'VNEW'})
        self.assertEquals(e.rhs, "VNEW/(1 + mg_conc*eta*exp(-1*gamma*VNEW*VNEW)) * sin(VNEW)")

        # Don't Change builtin function names:
        e.rhs_name_transform_inplace({'sin': 'SIN'})
        self.assertEquals(e.rhs, "VNEW/(1 + mg_conc*eta*exp(-1*gamma*VNEW*VNEW)) * sin(VNEW)")
        e.rhs_name_transform_inplace({'exp': 'EXP'})
        self.assertEquals(e.rhs, "VNEW/(1 + mg_conc*eta*exp(-1*gamma*VNEW*VNEW)) * sin(VNEW)")

        # Check the attributes:
        self.assertEquals(set(e.rhs_atoms), set(
            ['VNEW', 'mg_conc', 'eta', 'gamma', 'exp', 'sin']))
        self.assertEquals(set(e.rhs_funcs), set(['exp', 'sin']))

    def test_rhs_atoms_in_namespace(self):
        e = Expression("random.randn() + random.randn() + random.randint() / sin(t)")
        self.assertEquals(
            set(e.rhs_atoms),
            set(['t', 'random.randn', 'random.randint', 'sin'])
        )

        self.assertEquals(
            set(e.rhs_atoms_in_namespace('random')),
            set(['randn', 'randint'])
        )

    def test_escape_of_carets(self):
        try:
            expr = Expression("a^2")  # @UnusedVariable
            expr = Expression("(a - 2)^2")  # @UnusedVariable
            expr = Expression("(a - (a^2 - 2))^2")  # @UnusedVariable
            expr = Expression("a^(a - 2)")  # @UnusedVariable
        except NineMLMathParseError as e:
            self.fail("Carets (signifying exponents) were not escaped properly"
                      " in expression: {}".format(e))
        self.assertTrue(True)

# Testing Skeleton for class: ExpressionWithLHS
#
# class ExpressionWithLHS_test(unittest.TestCase):
#
#
#    def test_atoms(self):
# Signature: name
# No Docstring
# from nineml.abstraction_layer.component.expressions import ExpressionWithLHS
#        warnings.warn('Tests not implemented')
# raise NotImplementedError()
#
#    def test_lhs_name_transform_inplace(self):
# Signature: name(self, name_map)
# No Docstring
# from nineml.abstraction_layer.component.expressions import ExpressionWithLHS
#        warnings.warn('Tests not implemented')
# raise NotImplementedError()
#
#    def test_name_transform_inplace(self):
# Signature: name(self, name_map)
# No Docstring
# from nineml.abstraction_layer.component.expressions import ExpressionWithLHS
#        warnings.warn('Tests not implemented')
# raise NotImplementedError()
#
#
#    def test_lhs_atoms(self):
#        warnings.warn('Tests not implemented')


class TestVisitor(object):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)


# Testing Skeleton for class: ExpressionWithSimpleLHS
class ExpressionWithSimpleLHS_test(unittest.TestCase):

    def test_lhs(self):

        e = ExpressionWithSimpleLHS('a', 't+t+3 + sin(t*pi) +q')

        self.assertEqual(list(e.lhs), ['a'])
        self.assertEqual(list(e.lhs_atoms), ['a'])
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['t', 'sin', 'q']))
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # RHS transform not affecting LHS:
        e.rhs_name_transform_inplace({'a': 'b'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # LHS transform not affecting RHS:
        e.lhs_name_transform_inplace({'t': 'T'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 't', 'sin', 'q']))

        # name_transform affecting LHS & RHS:
        e.name_transform_inplace({'t': 'T'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['a', 'T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.lhs_atoms)), sorted(['a']))

        e.name_transform_inplace({'a': 'A'})
        self.assertEqual(sorted(list(e.atoms)), sorted(['A', 'T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.rhs_atoms)), sorted(['T', 'sin', 'q']))
        self.assertEqual(sorted(list(e.lhs_atoms)), sorted(['A']))


class Alias_test(unittest.TestCase):

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|

        class AliasTestVisitor(TestVisitor):
            def visit_alias(self, component, **kwargs):
                return kwargs

        c = Alias(lhs='V', rhs='0')
        v = AliasTestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )


class StateAssignment_test(unittest.TestCase):

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|

        class StateAssignmentTestVisitor(TestVisitor):

            def visit_assignment(self, component, **kwargs):
                return kwargs

        c = StateAssignment(lhs='V', rhs='0')
        v = StateAssignmentTestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )


# Testing Skeleton for class: TimeDerivative
class TimeDerivative_test(unittest.TestCase):

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|

        class TimeDerivativeTestVisitor(TestVisitor):

            def visit_timederivative(self, component, **kwargs):
                return kwargs

        c = TimeDerivative(dependent_variable='V', rhs='0')
        v = TimeDerivativeTestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_atoms(self):
        td = TimeDerivative(dependent_variable='X', rhs=' y*f - sin(q*q) + 4*a*exp(Y)')
        self.assertEquals(sorted(td.atoms), sorted(
            ['X', 'y', 'f', 'sin', 'exp', 'q', 'a', 'Y', 't']))
        self.assertEquals(sorted(td.lhs_atoms), sorted(['X', 't']))
        self.assertEquals(sorted(td.rhs_atoms), sorted(['y', 'f', 'sin', 'exp', 'q', 'a', 'Y']))

#   def test_dependent_variable(self):
    def test_independent_variable(self):
        td = TimeDerivative(dependent_variable='X', rhs=' y*f - sin(q*q) + 4*a*exp(Y)')
        self.assertEquals(td.independent_variable, 't')
        self.assertEquals(td.dependent_variable, 'X')

        # Check substitutions to the LHS:
        td.lhs_name_transform_inplace({'X': 'x'})
        self.assertEquals(td.dependent_variable, 'x')

        # Since this is always time, we should not be changing the
        # independent_variable (dt)
        td.lhs_name_transform_inplace({'t': 'T'})
        self.assertEquals(td.independent_variable, 'T')

        # Aand change them again using 'name_transform_inplace'
        # Check substitutions to the LHS:
        td.name_transform_inplace({'x': 'X1'})
        self.assertEquals(td.dependent_variable, 'X1')

        # Since this is always time, we should not be changing the
        # independent_variable (dt)
        td.lhs_name_transform_inplace({'T': 'time'})
        self.assertEquals(td.independent_variable, 'time')


class Constant_test(unittest.TestCase):

    def setUp(self):
        self.c = Constant(name="faraday", value=96485.3365, units=coulomb)

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|

        class ConstantTestVisitor(TestVisitor):

            def visit_constant(self, component, **kwargs):  # @UnusedVariable @IgnorePep8
                return kwargs

        v = ConstantTestVisitor()
        self.assertEqual(
            v.visit(self.c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_xml_roundtrip(self):
        writer = XMLWriter()
        xml = self.c.accept_visitor(writer)
        loader = XMLLoader(Document(coulomb))
        c = loader.load_constant(xml)
        self.assertEqual(c, self.c, "Constant failed xml roundtrip")
