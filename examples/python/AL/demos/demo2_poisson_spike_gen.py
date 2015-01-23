

from nineml.abstraction_layer.testing_utils import (std_pynn_simulation,
                                                    RecordValue)
from nineml.abstraction_layer import (ComponentClass, Regime, On, OutputEvent,
                                      SendPort, ReducePort, flattening)


class FuncTest_Flat2(object):
# class FuncTest_Flat2(unittest.TestCase):

    """ Create a Neuron with leak, and a current clamp, and check that the
        Output is what we would expect.
    """

    def func_test(self):

        emitter = ComponentClass(
            name='EventEmitter',
            parameters=['rate'],
            regimes=[
                Regime(
                    transitions=On(
                        't > tchange', do=[OutputEvent('emit'), 'tchange=t + random.exponential(1/rate) '])),
            ])

        ev_based_cc = ComponentClass(
            name='EventBasedCurrentClass',
            parameters=['dur', 'i'],
            analog_ports=[SendPort('I')],
            regimes=[
                Regime(
                    transitions=[
                        On('inputevent', do=['I=i', 'tchange = t']),
                        On('t>tchange + dur', do=['I=0', 'tchange=t'])
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
                          ReducePort('iInj', reduce_op='+')],
        )

        combined_comp = ComponentClass(name='Comp1',
                                       subnodes={
                                       'nrn': nrn,  'cc1': pulsing_emitter, 'cc2': pulsing_emitter},
                                       portconnections=[('cc1.cc.I', 'nrn.iInj'),
                                                        ('cc2.cc.I', 'nrn.iInj')]
                                       )

        combined_comp = flattening.flatten(combined_comp)

        records = [
            RecordValue(what='cc1_cc_I', tag='Current', label='Current Clamp 1'),
            RecordValue(what='cc2_cc_I', tag='Current', label='Current Clamp 2'),
            # RecordValue(what='nrn_iIn', tag='Current', label='Total Input Current'),
            RecordValue(what='nrn_V', tag='Voltage', label='Neuron Voltage'),
            RecordValue(what='cc1_cc_tchange', tag='Tchange', label='tChange CC1'),
            RecordValue(what='cc2_cc_tchange', tag='Tchange', label='tChange CC2'),
            RecordValue(what='regime',     tag='Regime',  label='Regime'),
        ]

        parameters = flattening.ComponentFlattener.flatten_namespace_dict({
                                                                                    'cc1.cc.i': 13.8,
                                                                                    'cc1.cc.dur': 1,
                                                                                    'cc1.evs.rate': 110. / 1000.,

                                                                                    'cc2.cc.i': 20.8,
                                                                                    'cc2.cc.dur': 1.,
                                                                                    'cc2.evs.rate': 20. / 1000.,

                                                                                    'nrn.gL': 4.3,
                                                                                    'nrn.E': -70})

        res = std_pynn_simulation(test_component=combined_comp,
                                  parameters=parameters,
                                  initial_values={},
                                  synapse_components=[],
                                  records=records,
                                  sim_time=1000
                                  # plot = False,
                                  )
        return
        t, records = res

        def check_trace(trace_name, time_period, exp_mean, exp_std=0):
            t_indices = (t > time_period[0] + 1) & (t < time_period[1] - 1)
            self.assertAlmostEqual(records[trace_name][t_indices].mean(), exp_mean, places=3)
            self.assertAlmostEqual(records[trace_name][t_indices].std(),  exp_std, places=3)

        check_trace('cc1_cc_I', (00, 30),  exp_mean=0.0)
        check_trace('cc1_cc_I', (30, 40), exp_mean=13.8)
        check_trace('cc1_cc_I', (40, 60), exp_mean=0.0)
        check_trace('cc1_cc_I', (60, 70), exp_mean=13.8)
        check_trace('cc1_cc_I', (70, 90), exp_mean=0.0)
        check_trace('cc1_cc_I', (90, 100), exp_mean=13.8)

        check_trace('cc2_cc_I', (00, 20),  exp_mean=0.0)
        check_trace('cc2_cc_I', (20, 25),  exp_mean=20.8)
        check_trace('cc2_cc_I', (25, 40),  exp_mean=0.0)
        check_trace('cc2_cc_I', (40, 45),  exp_mean=20.8)
        check_trace('cc2_cc_I', (45, 60),  exp_mean=0.0)
        check_trace('cc2_cc_I', (60, 65),  exp_mean=20.8)
        check_trace('cc2_cc_I', (65, 80),  exp_mean=0.0)
        check_trace('cc2_cc_I', (80, 85),  exp_mean=20.8)
        check_trace('cc2_cc_I', (85, 100), exp_mean=0.0)

        check_trace('nrn_iIn', (00, 20),  exp_mean=0.0)
        check_trace('nrn_iIn', (20, 25),  exp_mean=20.8)
        check_trace('nrn_iIn', (25, 30),  exp_mean=0.0)
        check_trace('nrn_iIn', (30, 40),  exp_mean=13.8)
        check_trace('nrn_iIn', (40, 45),  exp_mean=20.8)
        check_trace('nrn_iIn', (45, 60),  exp_mean=0.0)
        check_trace('nrn_iIn', (60, 65),  exp_mean=34.6)
        check_trace('nrn_iIn', (65, 70),  exp_mean=13.8)
        check_trace('nrn_iIn', (70, 80),  exp_mean=0.0)
        check_trace('nrn_iIn', (80, 85),  exp_mean=20.8)
        check_trace('nrn_iIn', (85, 90),  exp_mean=0.0)
        check_trace('nrn_iIn', (90, 100),  exp_mean=13.8)

        check_trace('nrn_V', (00 + 2, 20),  exp_mean=(0.0 / 4.3) - 70)
        check_trace('nrn_V', (20 + 2, 25),  exp_mean=(20.8 / 4.3) - 70)
        check_trace('nrn_V', (25 + 2, 30),  exp_mean=(0.0 / 4.3) - 70)
        check_trace('nrn_V', (30 + 2, 40),  exp_mean=(13.8 / 4.3) - 70)
        check_trace('nrn_V', (40 + 2, 45),  exp_mean=(20.8 / 4.3) - 70)
        check_trace('nrn_V', (45 + 2, 60),  exp_mean=(0.0 / 4.3) - 70)
        check_trace('nrn_V', (60 + 2, 65),  exp_mean=(34.6 / 4.3) - 70)
        check_trace('nrn_V', (65 + 2, 70),  exp_mean=(13.8 / 4.3) - 70)
        check_trace('nrn_V', (70 + 2, 80),  exp_mean=(0.0 / 4.3) - 70)
        check_trace('nrn_V', (80 + 2, 85),  exp_mean=(20.8 / 4.3) - 70)
        check_trace('nrn_V', (85 + 2, 90),  exp_mean=(0.0 / 4.3) - 70)
        check_trace('nrn_V', (90 + 2, 100),  exp_mean=(13.8 / 4.3) - 70)


FuncTest_Flat2().func_test()
