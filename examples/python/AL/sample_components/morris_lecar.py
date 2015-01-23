"""

The Morris-Lecar Model

Authors:
- G4 (A. Davison, Y. Le Franc, E. Muller, I. Raikov
- Gif-sur-Yvette, CNRS-UNIC Salle de Vie, Dec 3rd, 2010.

Modified:
- Mike Hull June/2011 EPFL
"""


class ComponentMetadata(object):
    pass


import nineml.abstraction_layer as al


def get_component():
    r = al.Regime(
        name="subthreshold_regime",
        transitions=[al.On("V > theta", do=al.OutputEvent('spikeoutput'))],
        time_derivatives=[
            "dV/dt = (g_l*(V_l - V) + I_ca + I_k + Isyn)/C",
            "dW/dt = lambda_W*(W_inf - W)",
        ],
    )

    ports = [al.SendPort("V"),
             al.ReducePort("Isyn", reduce_op="+")]

    c1 = al.ComponentClass("MorrisLecar",
                           dynamics=al.Dynamics(
                           regimes=[r],

                           aliases=[
                           "M_inf := 0.5*(1.0+tanh((V-V1)/V2))",
                           "W_inf := 0.5*(1.0+tanh((V-V3)/V4))",
                           "lambda_W := phi*cosh((V-V3)/(2.0*V4))",
                           "I_ca := g_ca*M_inf*(V_ca-V)",
                           "I_k := g_k*W*(V_k-V)",
                           ]
                           )
                           )
    return c1
