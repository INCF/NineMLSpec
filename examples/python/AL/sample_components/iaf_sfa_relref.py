"""
This model implements the iaf_sfa_rr aspects of iaf_cond_exp_sfa_rr in
nest, that is contrary to the nest model, it does not include the "cond_exp" synapse model,

This model was used in:

Muller, E., Buesing, L., Schemmel, J., & Meier, K. (2007).
Spike-frequency adapting neural ensembles: Beyond mean adaptation and
renewal theories. Neural Computation, 19, 2958-3010.

Documentation from NEST:

/* BeginDocumentation
Name: iaf_cond_exp_sfa_rr - Simple conductance based leaky integrate-and-fire neuron model.

Description:
iaf_cond_exp_sfa_rr is an iaf_cond_exp_sfa_rr i.e. an implementation of a
spiking neuron using IAF dynamics with conductance-based synapses,
with additional spike-frequency adaptation and relative refractory
mechanisms as described in Dayan+Abbott, 2001, page 166.

As for the iaf_cond_exp_sfa_rr, Incoming spike events induce a post-synaptic
change  of  conductance  modelled  by an  exponential  function.  The
exponential function is  normalised such that an event  of weight 1.0
results in a peak current of 1 nS.

Outgoing spike events induce a change of the adaptation and relative
refractory conductances by q_sfa and q_rr, respectively.  Otherwise
these conductances decay exponentially with time constants tau_sfa
and tau_rr, respectively.

Parameters:
The following parameters can be set in the status dictionary.

V        double - Membrane potential in mV
E_L        double - Leak reversal potential in mV.
C_m        double - Capacity of the membrane in pF
t_ref      double - Duration of refractory period in ms.
V_th       double - Spike threshold in mV.
V_reset    double - Reset potential of the membrane in mV.
E_ex       double - Excitatory reversal potential in mV.
E_in       double - Inhibitory reversal potential in mV.
g_L        double - Leak conductance in nS;
tau_ex     double - Time constant of the excitatory synaptic exponential function in ms.
tau_in     double - Time constant of the inhibitory synaptic exponential function in ms.
q_sfa      double - Outgoing spike activated quantal spike-frequency adaptation conductance increase in nS.
q_rr       double - Outgoing spike activated quantal relative refractory conductance increase in nS.
tau_sfa    double - Time constant of spike-frequency adaptation in ms.
tau_rr     double - Time constant of the relative refractory mechanism in ms.
E_sfa      double - spike-frequency adaptation conductance reversal potential in mV.
E_rr       double - relative refractory mechanism conductance reversal potential in mV.
I_e        double - an external stimulus current in pA.

Sends: SpikeEvent

Receives: SpikeEvent, CurrentEvent, DataLoggingRequest

Author: Sven Schrader, Eilif Muller

SeeAlso: iaf_cond_exp_sfa_rr, aeif_cond_alpha, iaf_psc_delta, iaf_psc_exp, iaf_cond_alpha
*/

"""

import nineml.abstraction_layer as al


def get_component():
    subthreshold_regime = al.Regime(
        name="subthreshold_regime",
        time_derivatives=[
            "dV/dt = (g_L*(E_L-V) + g_sfa*(E_sfa-V) + g_rr*(E_rr-V) + Isyn)/C",
            "dg_sfa/dt = -g_sfa/tau_sfa",
            "dg_rr/dt = -g_rr/tau_rr",
        ],
        transitions=al.On("V> theta",
                          do=["g_sfa =g_sfa +  q_sfa", "g_rr =g_rr + q_rr", "t_spike = t",
                              al.OutputEvent('spikeoutput')],
                          to="refractory_regime"),
    )

    refractory_regime = al.Regime(
        name="refractory_regime",
        transitions=al.On("t >= t_spike + t_ref",
                          to='subthreshold_regime'),
    )

    analog_ports = [al.SendPort("V"),
                    al.ReducePort("Isyn", reduce_op="+")]

    c1 = al.ComponentClass("iaf_sfa_relref",
                           regimes=[subthreshold_regime, refractory_regime],
                           analog_ports=analog_ports,
                           )

    return c1
