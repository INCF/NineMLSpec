

import unittest
from nineml.abstraction_layer import (Regime, On, OutputEvent,
                                      AnalogReceivePort, AnalogSendPort,
                                      flattening)
from nineml.abstraction_layer.dynamics import DynamicsClass as ComponentClass


class ComponentFlattener_test(unittest.TestCase):

    def test_Flattening1(self):

        c = ComponentClass(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/cp2',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('c_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
                          AnalogSendPort('C1'), AnalogSendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        d = ComponentClass(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/dp2',
                    transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('d_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
                          AnalogSendPort('D1'), AnalogSendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        # Flatten a flat component
        # Everything should be as before:
        c_flat = flattening.flatten(c)

        assert c_flat is not c

        self.assertEqual(c_flat.name, 'C')
        self.assertEqual(set(c_flat.aliases_map.keys()), set(['C1', 'C2', 'C3']))

        # - Regimes and Transitions:
        self.assertEqual(set(c_flat.regimes_map.keys()), set(['r1', 'r2']))
        self.assertEqual(len(list(c_flat.regimes_map['r1'].on_events)), 1)
        self.assertEqual(len(list(c_flat.regimes_map['r1'].on_conditions)), 1)
        self.assertEqual(len(list(c_flat.regimes_map['r2'].on_events)), 0)
        self.assertEqual(len(list(c_flat.regimes_map['r2'].on_conditions)), 1)
        self.assertEqual(len(list(c_flat.regimes_map['r2'].on_conditions)), 1)

        #  - Ports & Parameters:
        self.assertEqual(
            set(c_flat.query.analog_ports_map.keys()),
            set(['cIn2', 'cIn1', 'C1', 'C2']))
        self.assertEqual(
            set(c_flat.query.event_ports_map.keys()),
            set(['spikein', 'c_emit', 'emit']))
        self.assertEqual(set(c_flat.query.parameters_map.keys()),
                         set(['cp1', 'cp2']))
        self.assertEqual(set(c_flat.state_variables_map.keys()),
                         set(['SV1']))

    def test_Flattening2(self):

        c = ComponentClass(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/cp2',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('c_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
                          AnalogSendPort('C1'), AnalogSendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        d = ComponentClass(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/dp2',
                    transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('d_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
                          AnalogSendPort('D1'), AnalogSendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        # Test Cloner, 1 level of hierachy
        # ------------------------------ #

        # Everything should be as before:
        b = ComponentClass(name='B',
                           subnodes={'c1': c, 'c2': c, 'd': d},
                           # portconnections= [('c1.C1','c2.cIn1'),('c2.emit','c1.spikein'), ]
                           )

        b_flat = flattening.flatten(b)

        # Name
        self.assertEqual(b_flat.name, 'B')

        # Aliases
        self.assertEqual(
            set(b_flat.aliases_map.keys()),
            set(['c1_C1', 'c1_C2', 'c1_C3', 'c2_C1', 'c2_C2', 'c2_C3', 'd_D1', 'd_D2', 'd_D3']))

        # - Regimes and Transitions:
        self.assertEqual(len(b_flat.regimes_map), 8)
        r_c1_1_c2_1_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r1 c2:r1 ')
        r_c1_1_c2_2_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r1 c2:r2 ')
        r_c1_2_c2_1_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r2 c2:r1')
        r_c1_2_c2_2_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r2 c2:r2')
        r_c1_1_c2_1_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r1 c2:r1 ')
        r_c1_1_c2_2_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r1 c2:r2 ')
        r_c1_2_c2_1_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r2 c2:r1')
        r_c1_2_c2_2_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r2 c2:r2')

        # Do we have the right number of on_events and on_conditions:
        self.assertEqual(len(list(r_c1_1_c2_1_d_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_1_d_1.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1.on_conditions)), 3)

        self.assertEqual(len(list(r_c1_1_c2_1_d_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2.on_conditions)), 3)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2.on_events)), 0)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2.on_conditions)), 3)

        # All on_events return to thier same transition:
        self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[0].target_regime, r_c1_1_c2_1_d_1)
        self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[1].target_regime, r_c1_1_c2_1_d_1)
        self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[2].target_regime, r_c1_1_c2_1_d_1)
        self.assertEqual((list(r_c1_1_c2_2_d_1.on_events))[0].target_regime, r_c1_1_c2_2_d_1)
        self.assertEqual((list(r_c1_1_c2_2_d_1.on_events))[1].target_regime, r_c1_1_c2_2_d_1)
        self.assertEqual((list(r_c1_2_c2_1_d_1.on_events))[0].target_regime, r_c1_2_c2_1_d_1)
        self.assertEqual((list(r_c1_2_c2_1_d_1.on_events))[1].target_regime, r_c1_2_c2_1_d_1)
        self.assertEqual((list(r_c1_2_c2_2_d_1.on_events))[0].target_regime, r_c1_2_c2_2_d_1)
        self.assertEqual((list(r_c1_1_c2_1_d_2.on_events))[0].target_regime, r_c1_1_c2_1_d_2)
        self.assertEqual((list(r_c1_1_c2_1_d_2.on_events))[1].target_regime, r_c1_1_c2_1_d_2)
        self.assertEqual((list(r_c1_1_c2_2_d_2.on_events))[0].target_regime, r_c1_1_c2_2_d_2)
        self.assertEqual((list(r_c1_2_c2_1_d_2.on_events))[0].target_regime, r_c1_2_c2_1_d_2)

        # Check On-Event port names are remapped properly:
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_1.on_events]), set(
            ['c1_spikein', 'c2_spikein', 'd_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_1.on_events]), set(['c1_spikein', 'd_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_1.on_events]), set(['c2_spikein', 'd_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_1.on_events]), set(['d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_1_d_2.on_events]), set(['c1_spikein', 'c2_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_2.on_events]), set(['c1_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_2.on_events]), set(['c2_spikein', ]))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_2_c2_2_d_2.on_events]), set([]))

        # ToDo: Check the OnConditions:
        #  - Ports & Parameters:
        self.assertEqual(
            set(b_flat.query.analog_ports_map.keys()),
            set(['c1_cIn1', 'c1_cIn2', 'c1_C1', 'c1_C2', 'c2_cIn1', 'c2_cIn2', 'c2_C1', 'c2_C2', 'd_dIn1', 'd_dIn2', 'd_D1', 'd_D2']))

        self.assertEqual(
            set(b_flat.query.event_ports_map.keys()),
            set(['c1_spikein', 'c1_emit', 'c1_c_emit', 'c2_spikein', 'c2_emit', 'c2_c_emit', 'd_spikein', 'd_emit', 'd_d_emit']))

        self.assertEqual(
            set(b_flat.query.parameters_map.keys()),
            set(['c1_cp1', 'c1_cp2', 'c2_cp1', 'c2_cp2', 'd_dp1', 'd_dp2', ]))

        self.assertEqual(
            set(b_flat.state_variables_map.keys()),
            set(['c1_SV1', 'c2_SV1', 'd_SV1']))

    def test_Flattening3(self):

        c = ComponentClass(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/cp2',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('c_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'), AnalogSendPort('C1'), AnalogSendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        d = ComponentClass(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/dp2',
                    transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('d_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'), AnalogSendPort('D1'), AnalogSendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        # Test Cloner, 2 levels of hierachy
        # ------------------------------ #

        # Everything should be as before:
        b = ComponentClass(name='B',
                           subnodes={'c1': c, 'c2': c, 'd': d},
                           )

        a = ComponentClass(name='A',
                           subnodes={'b': b, 'c': c},
                           )

        a_flat = flattening.flatten(a)

        # Name
        self.assertEqual(a_flat.name, 'A')

        # Aliases
        self.assertEqual(
            set(a_flat.aliases_map.keys()),
            set(['b_c1_C1', 'b_c1_C2', 'b_c1_C3', 'b_c2_C1', 'b_c2_C2', 'b_c2_C3', 'b_d_D1', 'b_d_D2', 'b_d_D3', 'c_C1', 'c_C2', 'c_C3']))

        # - Regimes and Transitions:
        self.assertEqual(len(a_flat.regimes_map), 16)
        r_c1_1_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r1')
        r_c1_1_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r1')
        r_c1_2_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r1')
        r_c1_2_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r1')
        r_c1_1_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r1')
        r_c1_1_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r1')
        r_c1_2_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r1')
        r_c1_2_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r1')
        r_c1_1_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r2')
        r_c1_1_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r2')
        r_c1_2_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r2')
        r_c1_2_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r2')
        r_c1_1_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r2')
        r_c1_1_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r2')
        r_c1_2_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r2')
        r_c1_2_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r2')

        regimes = [
            r_c1_1_c2_1_d_1_c_1,
            r_c1_1_c2_2_d_1_c_1,
            r_c1_2_c2_1_d_1_c_1,
            r_c1_2_c2_2_d_1_c_1,
            r_c1_1_c2_1_d_2_c_1,
            r_c1_1_c2_2_d_2_c_1,
            r_c1_2_c2_1_d_2_c_1,
            r_c1_2_c2_2_d_2_c_1,
            r_c1_1_c2_1_d_1_c_2,
            r_c1_1_c2_2_d_1_c_2,
            r_c1_2_c2_1_d_1_c_2,
            r_c1_2_c2_2_d_1_c_2,
            r_c1_1_c2_1_d_2_c_2,
            r_c1_1_c2_2_d_2_c_2,
            r_c1_2_c2_1_d_2_c_2,
            r_c1_2_c2_2_d_2_c_2]
        self.assertEqual(len(set(regimes)), 16)

        # Do we have the right number of on_events and on_conditions:
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_events)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_conditions)), 4)

        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_events)), 0)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_conditions)), 4)

# All on_events return to thier same transition:
        for r in a_flat.regimes:
            for on_ev in r.on_events:
                self.assertEquals(on_ev.target_regime, r)

        # Check On-Event port names are remapped properly:
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_1.on_events]), set(['c_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_c2_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_1.on_events]), set(['c_spikein', 'b_c1_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_1.on_events]), set(['c_spikein', 'b_c2_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_1.on_events]), set(['c_spikein']))

        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_1_c_2.on_events]), set(
            ['b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_2.on_events]), set(['b_c1_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_2.on_events]), set(['b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_2.on_events]), set(['b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_2.on_events]), set(['b_c1_spikein', 'b_c2_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_2.on_events]), set(['b_c1_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_2.on_events]), set(['b_c2_spikein', ]))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_2.on_events]), set([]))

        # ToDo: Check the OnConditions:

        #  - Ports & Parameters:
        self.assertEqual(
            set(a_flat.query.analog_ports_map.keys()),
            set(['b_c1_cIn1', 'b_c1_cIn2', 'b_c1_C1', 'b_c1_C2',
                 'b_c2_cIn1', 'b_c2_cIn2', 'b_c2_C1', 'b_c2_C2',
                 'b_d_dIn1', 'b_d_dIn2', 'b_d_D1', 'b_d_D2',
                 'c_cIn1', 'c_cIn2', 'c_C1', 'c_C2']))

        self.assertEqual(
            set(a_flat.query.event_ports_map.keys()),
            set(['b_c1_spikein', 'b_c1_emit', 'b_c1_c_emit',
                 'b_c2_spikein', 'b_c2_emit', 'b_c2_c_emit',
                 'b_d_spikein', 'b_d_emit', 'b_d_d_emit',
                 'c_spikein', 'c_emit', 'c_c_emit', ]))

        self.assertEqual(
            set(a_flat.query.parameters_map.keys()),
            set(['c_cp1', 'c_cp2',
                 'b_c1_cp1', 'b_c1_cp2',
                 'b_c2_cp1', 'b_c2_cp2',
                 'b_d_dp1', 'b_d_dp2', ]))

        self.assertEqual(
            set(a_flat.state_variables_map.keys()),
            set(['b_c1_SV1', 'b_c2_SV1', 'b_d_SV1', 'c_SV1']))

    def test_Flattening4(self):

        c = ComponentClass(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1', 'C4:=cIn2'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/cp2',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('c_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
                          AnalogSendPort('C1'), AnalogSendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        d = ComponentClass(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1 + dp2', 'D3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/dp2',
                    transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('d_emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
                          AnalogSendPort('D1'), AnalogSendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        # Test Cloner, 2 levels of hierachy
        # ------------------------------ #

        # Everything should be as before:
        b = ComponentClass(name='B',
                           subnodes={'c1': c, 'c2': c, 'd': d},
                           portconnections=[('c1.C1', 'c2.cIn2'),
                                            ('c2.C1', 'c1.cIn1')],
                           )

        a = ComponentClass(name='A',
                           subnodes={'b': b, 'c': c},
                           portconnections=[('b.c1.C1', 'b.c1.cIn2'),
                                            ('b.c1.C1', 'b.c2.cIn1'),
                                            ('b.c1.C2', 'b.d.dIn1')]
                           )

        a_flat = flattening.flatten(a)

        # Name
        self.assertEqual(a_flat.name, 'A')

        # Aliases
        self.assertEqual(
            set(a_flat.aliases_map.keys()),
            set(['b_c1_C1', 'b_c1_C2', 'b_c1_C3', 'b_c1_C4',
                 'b_c2_C1', 'b_c2_C2', 'b_c2_C3', 'b_c2_C4',
                 'b_d_D1', 'b_d_D2', 'b_d_D3',
                 'c_C1', 'c_C2', 'c_C3', 'c_C4']))

        # - Regimes and Transitions:
        self.assertEqual(len(a_flat.regimes_map), 16)
        r_c1_1_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r1')
        r_c1_1_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r1')
        r_c1_2_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r1')
        r_c1_2_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r1')
        r_c1_1_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r1')
        r_c1_1_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r1')
        r_c1_2_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r1')
        r_c1_2_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r1')
        r_c1_1_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r2')
        r_c1_1_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r2')
        r_c1_2_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r2')
        r_c1_2_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r2')
        r_c1_1_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r2')
        r_c1_1_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r2')
        r_c1_2_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r2')
        r_c1_2_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r2')

        regimes = [
            r_c1_1_c2_1_d_1_c_1,
            r_c1_1_c2_2_d_1_c_1,
            r_c1_2_c2_1_d_1_c_1,
            r_c1_2_c2_2_d_1_c_1,
            r_c1_1_c2_1_d_2_c_1,
            r_c1_1_c2_2_d_2_c_1,
            r_c1_2_c2_1_d_2_c_1,
            r_c1_2_c2_2_d_2_c_1,
            r_c1_1_c2_1_d_1_c_2,
            r_c1_1_c2_2_d_1_c_2,
            r_c1_2_c2_1_d_1_c_2,
            r_c1_2_c2_2_d_1_c_2,
            r_c1_1_c2_1_d_2_c_2,
            r_c1_1_c2_2_d_2_c_2,
            r_c1_2_c2_1_d_2_c_2,
            r_c1_2_c2_2_d_2_c_2]
        self.assertEqual(len(set(regimes)), 16)

        # Do we have the right number of on_events and on_conditions:
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_events)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_conditions)), 4)

        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_events)), 3)
        self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_events)), 2)
        self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_events)), 1)
        self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_conditions)), 4)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_events)), 0)
        self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_conditions)), 4)

# All on_events return to thier same transition:
        for r in a_flat.regimes:
            for on_ev in r.on_events:
                self.assertEquals(on_ev.target_regime, r)

        # Check On-Event port names are remapped properly:
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_1.on_events]), set(
            ['c_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_1.on_events]), set(['c_spikein', 'b_d_spikein']))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_1.on_events]), set(
            ['c_spikein', 'b_c1_spikein', 'b_c2_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_1.on_events]), set(['c_spikein', 'b_c1_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_1.on_events]), set(['c_spikein', 'b_c2_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_1.on_events]), set(['c_spikein']))

        self.assertEqual(set([ev.src_port_name for ev in r_c1_1_c2_1_d_1_c_2.on_events]), set(
            ['b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_2.on_events]), set(['b_c1_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_2.on_events]), set(['b_c2_spikein', 'b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_2.on_events]), set(['b_d_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_2.on_events]), set(['b_c1_spikein', 'b_c2_spikein']))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_2.on_events]), set(['b_c1_spikein', ]))
        self.assertEqual(
            set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_2.on_events]), set(['b_c2_spikein', ]))
        self.assertEqual(set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_2.on_events]), set([]))

        # ToDo: Check the OnConditions:

        #  - Ports & Parameters:
        self.assertEqual(
            set(a_flat.query.analog_ports_map.keys()),
            set(['b_c1_C1', 'b_c1_C2',
                 'b_c2_C1', 'b_c2_C2',
                 'b_d_dIn2', 'b_d_D1', 'b_d_D2',
                 'c_cIn1', 'c_cIn2', 'c_C1', 'c_C2']))

        self.assertEqual(
            set(a_flat.query.event_ports_map.keys()),
            set(['b_c1_spikein', 'b_c1_emit', 'b_c1_c_emit',
                 'b_c2_spikein', 'b_c2_emit', 'b_c2_c_emit',
                 'b_d_spikein', 'b_d_emit', 'b_d_d_emit',
                 'c_spikein', 'c_emit', 'c_c_emit', ]))

        self.assertEqual(
            set(a_flat.query.parameters_map.keys()),
            set(['c_cp1', 'c_cp2',
                 'b_c1_cp1', 'b_c1_cp2',
                 'b_c2_cp1', 'b_c2_cp2',
                 'b_d_dp1', 'b_d_dp2', ]))

        self.assertEqual(
            set(a_flat.state_variables_map.keys()),
            set(['b_c1_SV1', 'b_c2_SV1', 'b_d_SV1', 'c_SV1']))

        # Back-sub everything - then do we get the correct port mappings:
        a_flat.backsub_all()

        self.assertEqual(
            set(a_flat.aliases_map['b_c2_C4'].rhs_atoms),
            set(['b_c1_cp1']))

        self.assertEqual(
            set(a_flat.aliases_map['b_c1_C2'].rhs_atoms),
            set(['b_c2_cp1']))

        self.assertEqual(
            set(a_flat.aliases_map['b_c1_C4'].rhs_atoms),
            set(['b_c1_cp1']))

        self.assertEqual(
            set(a_flat.aliases_map['b_c2_C2'].rhs_atoms),
            set(['b_c1_cp1']))

        self.assertEqual(
            set(a_flat.aliases_map['b_d_D2'].rhs_atoms),
            set(['b_c2_cp1', 'b_d_dp2']))

    def test_event_resolution(self):
        pass
        # pass
        # DONE IN FUNCTIONAL TESTS INSTEAD:
        #
        # Component that 'EvOut' every 20 ms
        # c1 = ComponentClass(
        #        name = 'CC1',
        #        regimes = [ Regime(
        #                name = 'r1',
        #                transitions = On(' t > 20 + tlast', do= ['tlast=t',
        #                    OutputEvent('EvOut')]) ,
        #                )
        #            ] )

        # Component that forwards events from EvIn to EvOut
        # c2 = ComponentClass(
        #        name = 'CC2',
        #        regimes = [ Regime( name = 'r1', transitions = On('EvIn', do= OutputEvent('EvOut')) )
        #            ] )

        # c3 = ComponentClass(
        #        name = 'CC3',
        #        regimes = [
        #            Regime( name = 'r1', transitions = On('EvIn', to='r2') ),
        #            Regime( name = 'r2', transitions = On('EvIn', to='r1') ),
        #            ] )

        # Component that chains the components together:
        # comp = ComponentClass(
        #        name = 'C',
        #        subnodes = { 'c1':c1, 'c2':c2, 'c3':c3},
        #        portconnections= [ ('c1.EvOut','c2.EvIn'),('c2.EvOut','c3.EvIn') ]
        #        )

        # c_flat = nineml.abstraction_layer.flattening.flatten(comp)
