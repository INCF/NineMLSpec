"""
A composite leaky integrate-and-fire with conductance-based, exponential
synapses, like the IF_cond_exp standard cell model in PyNN

"""

import nineml.abstraction_layer as al


# class ComponentMetaData(object):
#    parameters = {
#            'iaf_vthresh':-57.0,
#            'iaf_vreset': -70.0,
#            'iaf_taurefrac': 20.0,
#            'iaf_gl':28.95,
#            'iaf_cm':289.5,
#            'iaf_vrest' : -70.0,
#            'cobaExcit_vrev': 0.0,
#            'cobaInhib_vrev': -75.0,
#            'cobaExcit_tau':1.5,
#            'cobaInhib_tau': 10.0}
#
#    synapse_components = [
#        ('cobaInhib', 'q' ),
#        ('cobaExcit', 'q' )
#            ]
#
#
#


def get_component():
    regimes = [
        al.Regime(
            name="sub_threshold_regime",
            time_derivatives=[
                "dV/dt = (v_rest - V)/tau_m + (gE*(e_rev_E - V) + gI*(e_rev_I - V) + i_offset)/cm",
                "dgE/dt = -gE/tau_syn_E",
                "dgI/dt = -gI/tau_syn_I", ],
            transitions=(al.On("V > v_thresh",
                               do=["t_spike = t",
                                   "V = v_reset",
                                   al.OutputEvent('spikeoutput')],
                               to="refractory_regime"),
                         al.On('excitatory', do="gE=gE+q"),
                         al.On('inhibitory', do="gI=gI+q"),
                         ),
        ),
        al.Regime(
            name = "refractory_regime",
            time_derivatives = [
                "dgE/dt = -gE/tau_syn_E",
                "dgI/dt = -gI/tau_syn_I", ],
            transitions = (al.On("t >= t_spike + tau_refrac", to="sub_threshold_regime"),
                           al.On('excitatoryspike', do="gE=gE+q"),
                           al.On('inhibitoryspike', do="gI=gI+q"),
                           ),
        )]

    analog_ports = [al.SendPort("V"), al.SendPort("gE"), al.SendPort("gI"),
                    al.RecvPort("q")]

    c1 = al.ComponentClass("IF_cond_exp", regimes=regimes, analog_ports=analog_ports)
    return c1
