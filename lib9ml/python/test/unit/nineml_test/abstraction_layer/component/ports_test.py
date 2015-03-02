

# Automatically Generated Testing Skeleton Template:
import warnings
import unittest


from nineml.abstraction_layer import AnalogReceivePort, AnalogReducePort, AnalogSendPort, EventReceivePort, EventSendPort
from nineml.exceptions import NineMLRuntimeError


# Testing Skeleton for class: AnalogPort
class AnalogPort_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        # Check the Component is forwarding arguments:
        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_analogsendport(self, component, **kwargs):
                return kwargs

            def visit_analogreceiveport(self, component, **kwargs):
                return kwargs

            def visit_analogreduceport(self, component, **kwargs):
                return kwargs

        v = TestVisitor()

        self.assertEqual(
            v.visit(AnalogSendPort('V'), kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )
        self.assertEqual(
            v.visit(AnalogReceivePort('V'), kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

        self.assertEqual(
            v.visit(AnalogReducePort('V', operator='+'), kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_name(self):
        # Signature: name
                # The name of the port, local to the current component
        self.assertEqual(AnalogReceivePort('A').name, 'A')
        self.assertEqual(AnalogReducePort('B', operator='+').name, 'B')
        self.assertEqual(AnalogSendPort('C').name, 'C')

    def test_operator(self):
        # Signature: name
                # The reduction operation of the port, if it is a 'reduce' port
        # from nineml.abstraction_layer.component.ports import AnalogPort
        self.assertRaises(
            NineMLRuntimeError,
            AnalogReducePort, 'V', operator='-')


# Testing Skeleton for class: EventPort
class EventPort_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_eventsendport(self, component, **kwargs):
                return kwargs

            def visit_eventreceiveport(self, component, **kwargs):
                return kwargs

        v = TestVisitor()

        self.assertEqual(
            v.visit(EventSendPort('EV'), kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )
        self.assertEqual(
            v.visit(EventReceivePort('EV'), kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_name(self):
        self.assertEqual(EventReceivePort('A').name, 'A')
        self.assertEqual(EventSendPort('C').name, 'C')

    def test_mode(self):
        # Signature: name
                # The mode of the port. ['send','recv' or 'reduce']
        # from nineml.abstraction_layer.component.ports import EventPort
#         warnings.warn('Tests not implemented')
        pass
        # raise NotImplementedError()

    def test_operator(self):
#         warnings.warn('Tests not implemented')
        pass
