

import nineml
from nineml.abstraction_layer.testing_utils import (std_pynn_simulation,
                                                    RecordValue)
from nineml.abstraction_layer import (ComponentClass, Regime, On, SendPort,
                                      OutputEvent, ReducePort, flattening)


class FuncTest_Flat2(object):
# class FuncTest_Flat2(unittest.TestCase):

    """ Create a Neuron with leak, and a current clamp, and check that the
        Output is what we would expect.
    """

    def func_test(self):

        emitter = ComponentClass(
            name='EventEmitter',
            parameters=['cyclelength'],
            regimes=[
                Regime(transitions=On('t > tchange + random_offset + cyclelength',
                                      do=[OutputEvent(
                                          'emit'), 'tchange=t', 'random_offset=random.uniform(5,10) '])),
            ])

        ev_based_cc = ComponentClass(
            name='EventBasedCurrentClass',
            parameters=['dur', 'i'],
            analog_ports=[SendPort('I')],
            regimes=[
                Regime(
                    transitions=[
                        On('inputevent', do=['I=i', 'tchange = t', ]),
                        On('t>tchange + dur  ', do=['I=0', 'tchange=t'])
                    ]
                )
            ]
        )

        pulsing_emitter = ComponentClass(name='pulsing_cc',
                                         subnodes={'evs': emitter, 'cc': ev_based_cc},
                                         portconnections=[('evs.emit', 'cc.inputevent')]
                                         )

        nrn = ComponentClass(
            name='LeakyNeuron',
            parameters=['Cm', 'gL', 'E'],
            regimes=[Regime('dV/dt = (iInj + (E-V)*gL )/Cm'), ],
            aliases=['iIn := iInj'],
            analog_ports=[SendPort('V'),
                          ReducePort('iInj', operator='+')],
        )

        combined_comp = ComponentClass(name='Comp1',
                                       subnodes={'nrn': nrn,
                                                 'cc1': pulsing_emitter,
                                                 'cc2': pulsing_emitter},
                                       portconnections=[('cc1.cc.I', 'nrn.iInj'),
                                                        ('cc2.cc.I', 'nrn.iInj')]
                                       )

        combined_comp = flattening.flatten(combined_comp)

        records = [
            RecordValue(what='cc1_cc_I', tag='Current', label='Current Clamp 1'),
            RecordValue(what='cc2_cc_I', tag='Current', label='Current Clamp 2'),
            RecordValue(what='nrn_iIn',  tag='Current', label='Total Input Current'),
            RecordValue(what='nrn_V',    tag='Voltage', label='Neuron Voltage'),
            RecordValue(what='cc1_cc_tchange', tag='Tchange', label='tChange CC1'),
            RecordValue(what='cc2_cc_tchange', tag='Tchange', label='tChange CC2'),
            RecordValue(what='regime',     tag='Regime',  label='Regime'),
        ]

        parameters = flattening.ComponentFlattener.flatten_namespace_dict({
                                                                                    'cc1.cc.i': 13.8,
                                                                                    'cc1.cc.dur': 5,
                                                                                    'cc1.evs.cyclelength': 15,

                                                                                    'cc2.cc.i': 20.8,
                                                                                    'cc2.cc.dur': 5,
                                                                                    'cc2.evs.cyclelength': 15,

                                                                                    'nrn.gL': 4.3,
                                                                                    'nrn.E': -70})

        res = std_pynn_simulation(test_component=combined_comp,
                                  parameters=parameters,
                                  initial_values={},
                                  synapse_components=[],
                                  records=records,
                                  # plot = False,
                                  )
        return
        t, records = res

        def check_trace(trace_name, time_period, exp_mean, exp_std=0):
            t_indices = (t > time_period[0] + 1) & (t < time_period[1] - 1)
            self.assertAlmostEqual(records[trace_name][t_indices].mean(), exp_mean, places=3)
            self.assertAlmostEqual(records[trace_name][t_indices].std(),  exp_std, places=3)

        # check_trace('cc1_cc_I', (00,30),  exp_mean=0.0 )


FuncTest_Flat2().func_test()
