

import warnings
import unittest
from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction_layer.dynamics.testing_utils import TestableComponent
from nineml.abstraction_layer import (
    DynamicsClass as ComponentClass, Dynamics, AnalogSendPort, Alias,
    AnalogReceivePort, AnalogReducePort, Regime, On, NamespaceAddress,
    OutputEvent, EventReceivePort)


class ComponentClass_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|
        # Check the Component is forwarding arguments:

        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_componentclass(self, component, **kwargs):
                return kwargs

        c = ComponentClass(name='MyComponent')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_aliases(self):
        # Signature: name
                # Forwarding function to self.dynamics.aliases

        # No Aliases:
        self.assertEqual(
            list(ComponentClass(name='C1').aliases),
            []
        )

        # 2 Aliases
        C = ComponentClass(name='C1', aliases=['G:= 0', 'H:=1'])
        self.assertEqual(len(list((C.aliases))), 2)
        self.assertEqual(
            set(C.aliases_map.keys()), set(['G', 'H'])
        )

        C = ComponentClass(name='C1', aliases=['G:= 0', 'H:=1', Alias('I', '3')])
        self.assertEqual(len(list((C.aliases))), 3)
        self.assertEqual(
            set(C.aliases_map.keys()), set(['G', 'H', 'I'])
        )

        # Using Dynamics Parameter:
        C = ComponentClass(name='C1', dynamics=Dynamics(aliases=['G:= 0', 'H:=1']))
        self.assertEqual(len(list((C.aliases))), 2)
        self.assertEqual(
            set(C.aliases_map.keys()), set(['G', 'H'])
        )

        C = ComponentClass(name='C1', dynamics=Dynamics(
            aliases=['G:= 0', 'H:=1', Alias('I', '3')]))
        self.assertEqual(len(list((C.aliases))), 3)
        self.assertEqual(
            set(C.aliases_map.keys()), set(['G', 'H', 'I'])
        )

        # Invalid Construction:
        # Invalid Valid String:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='C1', aliases=['H=0']
        )

        # Duplicate Alias Names:
        ComponentClass(name='C1', aliases=['H:=0', 'G:=1'])
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='C1', aliases=['H:=0', 'H:=1']
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='C1', aliases=['H:=0', Alias('H', '1')]
        )

        # Defining through dynamics and Component:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['H:=0'],
            dynamics=Dynamics(aliases=['G:=1']),
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=[Alias('H', '0')],
            dynamics=Dynamics(aliases=[Alias('G', '1')]),
        )

        # Self referential aliases:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['H := H +1'],
        )
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['H := G + 1', 'G := H + 1'],
        )

        # Referencing none existant symbols:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['H := G + I'],
            parameters=[],
            analog_ports=[],
        )

        # Invalid Names:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['H.2 := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['2H := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['E(H) := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['tanh := 0'],
        )
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1', aliases=['pi := 0'],
        )

    def test_aliases_map(self):
        # Signature: name
                # Forwarding function to self.dynamics.alias_map

        self.assertEqual(
            ComponentClass(name='C1').aliases_map, {}
        )

        c1 = ComponentClass(name='C1', aliases=['A:=3'])
        self.assertEqual(c1.aliases_map['A'].rhs_as_python_func()(), 3)
        self.assertEqual(len(c1.aliases_map), 1)

        c2 = ComponentClass(name='C1', aliases=['A:=3', 'B:=5'])
        self.assertEqual(c2.aliases_map['A'].rhs_as_python_func()(), 3)
        self.assertEqual(c2.aliases_map['B'].rhs_as_python_func()(), 5)
        self.assertEqual(len(c2.aliases_map), 2)

        c3 = ComponentClass(name='C1', dynamics=Dynamics(aliases=['C:=13', 'Z:=15']))
        self.assertEqual(c3.aliases_map['C'].rhs_as_python_func()(), 13)
        self.assertEqual(c3.aliases_map['Z'].rhs_as_python_func()(), 15)

        self.assertEqual(len(c3.aliases_map), 2)

    def test_analog_ports(self):
        # Signature: name
                # No Docstring

        c = ComponentClass(name='C1')
        self.assertEqual(len(list(c.analog_ports)), 0)

        c = ComponentClass(name='C1')
        self.assertEqual(len(list(c.analog_ports)), 0)

        c = ComponentClass(name='C1', aliases=['A:=2'], analog_ports=[AnalogSendPort('A')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'send')
        self.assertEqual(len(c.query.analog_send_ports), 1)
        self.assertEqual(len(c.query.analog_recv_ports), 0)
        self.assertEqual(len(c.query.analog_reduce_ports), 0)

        c = ComponentClass(name='C1', analog_ports=[AnalogReceivePort('B')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'recv')
        self.assertEqual(len(c.query.analog_send_ports), 0)
        self.assertEqual(len(c.query.analog_recv_ports), 1)
        self.assertEqual(len(c.query.analog_reduce_ports), 0)

        c = ComponentClass(name='C1', analog_ports=[AnalogReducePort('B', reduce_op='+')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'reduce')
        self.assertEqual(list(c.analog_ports)[0].reduce_op, '+')
        self.assertEqual(len(c.query.analog_send_ports), 0)
        self.assertEqual(len(c.query.analog_recv_ports), 0)
        self.assertEqual(len(c.query.analog_reduce_ports), 1)

        # Duplicate Port Names:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogReducePort('B', reduce_op='+'), AnalogSendPort('B')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogSendPort('A'), AnalogSendPort('A')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogReceivePort('A'), AnalogReceivePort('A')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            lambda: ComponentClass(name='C1', analog_ports=[AnalogReceivePort('1')])
        )

        self.assertRaises(
            NineMLRuntimeError,
            lambda: ComponentClass(name='C1', analog_ports=[AnalogReceivePort('?')])
        )

    def duplicate_port_name_event_analog(self):

        # Check different names are OK:
        ComponentClass(
            name='C1', aliases=['A:=1'],
            event_ports=[EventReceivePort('A')],
            analog_ports=[AnalogSendPort('A')])

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            aliases=['A:=1'],
            event_ports=[EventReceivePort('A')],
            analog_ports=[AnalogSendPort('A')]
        )

    # Testing done in test_backsub_all()
    def test_backsub_aliases(self):
        pass

    def test_backsub_equations(self):
        pass

    def test_backsub_all(self):

        # Check the aliases:
        # ====================== #
        c2 = ComponentClass(name='C1', aliases=['A:=1+2', 'B:=5*A', 'C:=B+2'])
        self.assertEqual(c2.aliases_map['A'].rhs_as_python_func()(), 3)

        # This should assert, because its not yet back-subbed
        c2.backsub_all()
        self.assertEqual(c2.aliases_map['B'].rhs_as_python_func()(), 15)
        # Check the ordering:
        self.assertEqual(c2.aliases_map['C'].rhs_as_python_func()(), ((5 * (3)) + 2))
        # ====================== #

        # Check the equations:
        # ====================== #
#         warnings.warn('Tests not implemented')
        pass
        # ====================== #

    def test_connect_ports(self):
        # Signature: name(self, src, sink)
                # Connects the ports of 2 subcomponents.
                #
                # The ports can be specified as ``string`` s or ``NamespaceAddresses`` es.
                #
                #
                # :param src: The source port of one sub-component; this should either an
                #     event port or analog port, but it *must* be a send port.
                #
                # :param sink: The sink port of one sub-component; this should either an
                #     event port or analog port, but it *must* be either a 'recv' or a
                #     'reduce' port.


        tIaf = TestableComponent('iaf')
        tCoba = TestableComponent('coba_synapse')

        # Should be fine:
        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()})
        c.connect_ports('iaf.V', 'coba.V')

        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()},
                           portconnections=[('iaf.V', 'coba.V')]
                           )

        # Non existant Ports:
        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()})
        self.assertRaises(
            NineMLRuntimeError,
            c.connect_ports, 'iaf.V1', 'coba.V')
        self.assertRaises(
            NineMLRuntimeError,
            c.connect_ports, 'iaf.V', 'coba.V1')

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            subnodes={'iaf': tIaf(), 'coba': tCoba()},
            portconnections=[('iaf.V1', 'coba.V')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='C1',
            subnodes={'iaf': tIaf(), 'coba': tCoba()},
            portconnections=[('iaf.V', 'coba.V1')]
        )

        # Connect ports the wronf way around:
        # [Check the wright way around works:]
        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()},
                           portconnections=[('coba.I', 'iaf.ISyn')]
                           )
        # And the wrong way around:
        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()})
        self.assertRaises(
            NineMLRuntimeError,
            c.connect_ports, 'iaf.ISyn.', 'coba.I')
        self.assertRaises(
            NineMLRuntimeError,
            c.connect_ports, 'coba.V', 'iaf.V')

        # Error raised on duplicate port-connection:
        c = ComponentClass(name='C1',
                           subnodes={'iaf': tIaf(), 'coba': tCoba()},
                           )

        c.connect_ports('coba.I', 'iaf.ISyn')
        self.assertRaises(
            NineMLRuntimeError,
            c.connect_ports, 'coba.I', 'iaf.ISyn')

    def test_dynamics(self):
        pass

    def test_event_ports(self):
        # Signature: name
                # No Docstring

        # Check inference of output event ports:
        c = ComponentClass(
            name='Comp1',
            regimes=Regime(
                transitions=[
                    On('V > a', do=OutputEvent('ev_port1')),
                    On('V > b', do=OutputEvent('ev_port1')),
                    On('V < c', do=OutputEvent('ev_port2')),
                ]
            ),
        )
        self.assertEquals(len(list(c.event_ports)), 2)

        # Check inference of output event ports:
        c = ComponentClass(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                       On('V > a', do=OutputEvent('ev_port1'), to='r2'),
                       On('V < b', do=OutputEvent('ev_port2')),
                       ]
                       ),

                Regime(name='r2',
                       transitions=[
                       On('V > a', do=OutputEvent('ev_port2'), to='r1'),
                       On('V < b', do=OutputEvent('ev_port3')),
                       ]
                       )
            ]
        )
        self.assertEquals(len(list(c.event_ports)), 3)

        # Check inference of output event ports:
        c = ComponentClass(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                       On('spikeinput1', do=[]),
                       On('spikeinput2', do=OutputEvent('ev_port2'), to='r2'),
                       ]
                       ),

                Regime(name='r2',
                       transitions=[
                       On('V > a', do=OutputEvent('ev_port2')),
                       On('spikeinput3', do=OutputEvent('ev_port3'), to='r1'),
                       ]
                       )
            ]
        )
        self.assertEquals(len(list(c.event_ports)), 5)

    # These are done in the Testflatten and ComponentFlattener_test
    # Classes instead.
    # def test_flattener(self):
    # def test_is_flat(self):
    # def test_set_flattener(self):
    # def test_was_flattened(self):
    # Hierachical
    def test_get_node_addr(self):
        # Signature: name(self)
                # Get the namespace address of this component

        d = ComponentClass(name='D',)
        e = ComponentClass(name='E')
        f = ComponentClass(name='F')
        g = ComponentClass(name='G')
        b = ComponentClass(name='B', subnodes={'d': d, 'e': e})
        c = ComponentClass(name='C', subnodes={'f': f, 'g': g})
        a = ComponentClass(name='A', subnodes={'b': b, 'c': c})

        # Construction of the objects causes cloning to happen:
        # Therefore we test by looking up and checking that there
        # are the correct component names:
        bNew = a.get_subnode('b')
        cNew = a.get_subnode('c')
        dNew = a.get_subnode('b.d')
        eNew = a.get_subnode('b.e')
        fNew = a.get_subnode('c.f')
        gNew = a.get_subnode('c.g')

        self.assertEquals(a.get_node_addr(),
                          NamespaceAddress.create_root())
        self.assertEquals(bNew.get_node_addr(),
                          NamespaceAddress('b'))
        self.assertEquals(cNew.get_node_addr(),
                          NamespaceAddress('c'))
        self.assertEquals(dNew.get_node_addr(),
                          NamespaceAddress('b.d'))
        self.assertEquals(eNew.get_node_addr(),
                          NamespaceAddress('b.e'))
        self.assertEquals(fNew.get_node_addr(),
                          NamespaceAddress('c.f'))
        self.assertEquals(gNew.get_node_addr(),
                          NamespaceAddress('c.g'))

        self.assertEquals(a.name, 'A')
        self.assertEquals(bNew.name, 'B')
        self.assertEquals(cNew.name, 'C')
        self.assertEquals(dNew.name, 'D')
        self.assertEquals(eNew.name, 'E')
        self.assertEquals(fNew.name, 'F')
        self.assertEquals(gNew.name, 'G')

    def test_insert_subnode(self):
        # Signature: name(self, subnode, namespace)
                # Insert a subnode into this component
                #
                #
                # :param subnode: An object of type ``ComponentClass``.
                # :param namespace: A `string` specifying the name of the component in
                #     this components namespace.
                #
                # :raises: ``NineMLRuntimeException`` if there is already a subcomponent at
                #     the same namespace location
                #
                # .. note::
                #
                #     This method will clone the subnode.

        d = ComponentClass(name='D')
        e = ComponentClass(name='E')
        f = ComponentClass(name='F')
        g = ComponentClass(name='G')

        b = ComponentClass(name='B')
        b.insert_subnode(namespace='d', subnode=d)
        b.insert_subnode(namespace='e', subnode=e)

        c = ComponentClass(name='C')
        c.insert_subnode(namespace='f', subnode=f)
        c.insert_subnode(namespace='g', subnode=g)

        a = ComponentClass(name='A')
        a.insert_subnode(namespace='b', subnode=b)
        a.insert_subnode(namespace='c', subnode=c)

        # Construction of the objects causes cloning to happen:
        # Therefore we test by looking up and checking that there
        # are the correct component names:
        bNew = a.get_subnode('b')
        cNew = a.get_subnode('c')
        dNew = a.get_subnode('b.d')
        eNew = a.get_subnode('b.e')
        fNew = a.get_subnode('c.f')
        gNew = a.get_subnode('c.g')

        self.assertEquals(a.get_node_addr(),
                          NamespaceAddress.create_root())
        self.assertEquals(bNew.get_node_addr(),
                          NamespaceAddress('b'))
        self.assertEquals(cNew.get_node_addr(),
                          NamespaceAddress('c'))
        self.assertEquals(dNew.get_node_addr(),
                          NamespaceAddress('b.d'))
        self.assertEquals(eNew.get_node_addr(),
                          NamespaceAddress('b.e'))
        self.assertEquals(fNew.get_node_addr(),
                          NamespaceAddress('c.f'))
        self.assertEquals(gNew.get_node_addr(),
                          NamespaceAddress('c.g'))

        self.assertEquals(a.name, 'A')
        self.assertEquals(bNew.name, 'B')
        self.assertEquals(cNew.name, 'C')
        self.assertEquals(dNew.name, 'D')
        self.assertEquals(eNew.name, 'E')
        self.assertEquals(fNew.name, 'F')
        self.assertEquals(gNew.name, 'G')

        self.assertRaises(NineMLRuntimeError, a.get_subnode, 'x')
        self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.')
        self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.X')
        self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.b.')
        self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.b.X')

        # Adding to the same namespace twice:
        d1 = ComponentClass(name='D1')
        d2 = ComponentClass(name='D2')
        a = ComponentClass(name='B')

        a.insert_subnode(namespace='d', subnode=d1)
        self.assertRaises(
            NineMLRuntimeError,
            a.insert_subnode, namespace='d', subnode=d2)

    # TESTED IN:
        # test_get_node_addr
    # def test_name(self):
        # Signature: name
                # No Docstring
    def test_parameters(self):
        # Signature: name
                # No Docstring

        # No parameters; nothing to infer
        c = ComponentClass(name='cl')
        self.assertEqual(len(list(c.parameters)), 0)

        # Mismatch between inferred and actual parameters
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='cl', parameters=['a'])

        # Single parameter inference from an alias block
        c = ComponentClass(name='cl', aliases=['A:=a'])
        self.assertEqual(len(list(c.parameters)), 1)
        self.assertEqual(list(c.parameters)[0].name, 'a')

        # More complex inference:
        c = ComponentClass(name='cl', aliases=['A:=a+e', 'B:=a+pi+b'])
        self.assertEqual(len(list(c.parameters)), 3)
        self.assertEqual(sorted([p.name for p in c.parameters]), ['a', 'b', 'e'])

        # From State Assignments and Differential Equations, and Conditionals
        c = ComponentClass(name='cl',
                           aliases=['A:=a+e', 'B:=a+pi+b'],
                           regimes=Regime('dX/dt = 6 + c + sin(d)',
                                          'dV/dt = 1.0',
                                          transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                                          )
                           )
        self.assertEqual(len(list(c.parameters)), 7)
        self.assertEqual(
            sorted([p.name for p in c.parameters]),
            ['Vt', 'a', 'b', 'c', 'd', 'e', 'f'])

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            parameters=['a', 'b', 'c'])

    def test_regimes(self):

        c = ComponentClass(name='cl', )
        self.assertEqual(len(list(c.regimes)), 0)

        c = ComponentClass(name='cl',
                           regimes=Regime('dX/dt=0',
                                          name='r1',
                                          transitions=On('X>X1', do=['X = X0'], to=None))
                           )
        self.assertEqual(len(list(c.regimes)), 1)

        c = ComponentClass(name='cl',
                           regimes=[
                                Regime('dX/dt=0',
                                       name='r1',
                                       transitions=On('X>X1', do=['X=X0'], to='r2')),
                                Regime('dX/dt=0',
                                       name='r2',
                                       transitions=On('X>X1', do=['X=X0'],
                                                      to='r3')),
                                Regime('dX/dt=0',
                                       name='r3',
                                       transitions=On('X>X1', do=['X=X0'],
                                                      to='r4')),
                                Regime('dX/dt=0',
                                       name='r4',
                                       transitions=On('X>X1', do=['X=X0'],
                                                      to='r1')),
                           ]
                           )
        self.assertEqual(len(list(c.regimes)), 4)
        self.assertEqual(
            set(c.regimes_map.keys()),
            set(['r1', 'r2', 'r3', 'r4'])
        )

        c = ComponentClass(name='cl',
                           dynamics=Dynamics(
                                regimes=[
                                    Regime('dX/dt=0',
                                           name='r1',
                                           transitions=On('X>X1', do=['X=X0'], to='r2')),
                                    Regime('dX/dt=0',
                                           name='r2',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r3')),
                                    Regime('dX/dt=0',
                                           name='r3',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r4')),
                                    Regime('dX/dt=0',
                                           name='r4',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r1')),
                                ]
                           )
                           )
        self.assertEqual(len(list(c.regimes)), 4)
        self.assertEqual(
            set([r.name for r in c.regimes]),
            set(['r1', 'r2', 'r3', 'r4'])
        )

        # Duplicate Names:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='cl',
            regimes=[
                Regime('dX/dt=0',
                       name='r',
                       transitions=On('X>X1', do=['X=X0'])),
                Regime('dX/dt=0',
                       name='r',
                       transitions=On('X>X1', do=['X=X0'],)), ]
        )

    def test_state_variables(self):
        # No parameters; nothing to infer
        c = ComponentClass(name='cl')
        self.assertEqual(len(list(c.state_variables)), 0)

        # Mismatch between inferred and actual statevariables
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass, name='cl', state_variables=['a'])

        # From State Assignments and Differential Equations, and Conditionals
        c = ComponentClass(name='cl',
                           aliases=['A:=a+e', 'B:=a+pi+b'],
                           regimes=Regime('dX/dt = 6 + c + sin(d)',
                                          'dV/dt = 1.0',
                                          transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                                          )
                           )
        self.assertEqual(
            set(c.state_variables_map.keys()),
            set(['X', 'V']))

        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            state_variables=['X'])

        # Shouldn't pick up 'e' as a parameter:
        self.assertRaises(
            NineMLRuntimeError,
            ComponentClass,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            state_variables=['X', 'V', 'Vt'])

        c = ComponentClass(name='cl',
                           dynamics=Dynamics(
                                regimes=[
                                    Regime('dX1/dt=0',
                                           name='r1',
                                           transitions=On('X>X1', do=['X=X0'], to='r2')),
                                    Regime('dX1/dt=0',
                                           name='r2',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r3')),
                                    Regime('dX2/dt=0',
                                           name='r3',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r4')),
                                    Regime('dX2/dt=0',
                                           name='r4',
                                           transitions=On('X>X1', do=['X=X0'],
                                                          to='r1')),
                                ]
                           )
                           )
        self.assertEqual(set(c.state_variables_map.keys()),
                         set(['X1', 'X2', 'X']))

    def test_transitions(self):

        c = ComponentClass(name='cl',
                           dynamics=Dynamics(
                                regimes=[
                                    Regime('dX1/dt=0',
                                           name='r1',
                                           transitions=[On('X>X1', do=['X=X0'], to='r2'),
                                                        On('X>X2', do=['X=X0'], to='r3'), ]
                                           ),
                                    Regime('dX1/dt=0',
                                           name='r2',
                                           transitions=On('X>X1', do=['X=X0'], to='r3'),),
                                    Regime('dX2/dt=0',
                                           name='r3',
                                           transitions=[On('X>X1', do=['X=X0'], to='r4'),
                                                        On('X>X2', do=['X=X0'], to=None)]),
                                    Regime('dX2/dt=0',
                                           name='r4',
                                           transitions=On('X>X1', do=['X=X0'], to=None)),
                                ]
                           )
                           )

        self.assertEquals(len(list(c.transitions)), 6)

        r_map = c.regimes_map
        r1 = r_map['r1']
        r2 = r_map['r2']
        r3 = r_map['r3']
        r4 = r_map['r4']

        self.assertEquals(len(list(r1.transitions)), 2)
        self.assertEquals(len(list(r2.transitions)), 1)
        self.assertEquals(len(list(r3.transitions)), 2)
        self.assertEquals(len(list(r4.transitions)), 1)

        target_regimes = lambda r: set([tr.target_regime for tr in r.transitions])
        self.assertEquals(target_regimes(r1), set([r2, r3]))
        self.assertEquals(target_regimes(r2), set([r3]))
        self.assertEquals(target_regimes(r3), set([r3, r4]))
        self.assertEquals(target_regimes(r4), set([r4]))



    # Write is better tested in the round trip tests.
    # def test_write(self):
