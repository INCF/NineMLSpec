'''

Adaptive exponential integrate-and-fire neuron as described in
A. Destexhe, J COmput Neurosci 27: 493--506 (2009)

Author B. Kriener (Jan 2011)

## neuron model: aeIF

## variables:
## V: membrane potential
## w: adaptation variable

## parameters:
## C_m     # specific membrane capacitance [muF/cm**2]
## g_L     # leak conductance [mS/cm**2]
## E_L     # resting potential [mV]
## Delta   # steepness of exponential approach to threshold [mV]
## V_T     # spike threshold [mV]
## S       # membrane area [mum**2]
## tau_ref # refractory time [ms]
## tau_w   # adaptation time constant
## a, b    # adaptation parameters [muS, nA]

'''

import nineml.abstraction_layer as al


def get_component():

    parameters = ['C_m', 'g_L', 'E_L', 'Delta', 'V_T', 'S', 'tau_ref', 'tau_w', 'a', 'b']

    aeIF = al.ComponentClass("aeIF",
                             regimes=[
                             al.Regime(
                             name="subthresholdregime",
                             time_derivatives=[
                             "dV/dt = -g_L*(V-E_L)/C_m + g_L*Delta*exp((V-V_T)/Delta-w/S)/C_m+ Isyn/C_m",
                             "dw/dt = (a*(V-E_L)-w)/tau_w", ],
                             transitions=al.On("V > V_T",
                                               do=["V = E_L",
                                                   "w = w + b",
                                                   al.OutputEvent('spikeoutput')],
                                               to="refractoryregime"),
                             ),

                             al.Regime(
                             name="refractoryregime",
                             transitions=al.On("t>=tspike+trefractory",
                                               to="subthresholdregime"),
                             )
                             ],
                             analog_ports=[al.ReducePort("Isyn", operator="+")]
                             )

    return aeIF
