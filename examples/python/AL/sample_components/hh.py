"""
Script for generating a single-compartment Hodgkin-Huxley cell in NineML XML format.

Andrew Davison, 2010
"""

import nineml.abstraction_layer as al


def get_component():
    aliases = [
        "q10 := 3.0**((celsius - 6.3)/10.0)",  # temperature correction factor
        "alpha_m := -0.1*(V+40.0)/(exp(-(V+40.0)/10.0) - 1.0)",  # m
        "beta_m := 4.0*exp(-(V+65.0)/18.0)",
        "mtau := 1/(q10*(alpha_m + beta_m))",
        "minf := alpha_m/(alpha_m + beta_m)",
        "alpha_h := 0.07*exp(-(V+65.0)/20.0)",               # h
        "beta_h := 1.0/(exp(-(V+35)/10.0) + 1.0)",
        "htau := 1.0/(q10*(alpha_h + beta_h))",
        "hinf := alpha_h/(alpha_h + beta_h)",
        "alpha_n := -0.01*(V+55.0)/(exp(-(V+55.0)/10.0) - 1.0)",  # n
        "beta_n := 0.125*exp(-(V+65.0)/80.0)",
        "ntau := 1.0/(q10*(alpha_n + beta_n))",
        "ninf := alpha_n/(alpha_n + beta_n)",
        "gna := gnabar*m*m*m*h",                       #
        "gk := gkbar*n*n*n*n",
        "ina := gna*(ena - V)",                 # currents
        "ik := gk*(ek - V)",
        "il := gl*(el - V )"]

    hh_regime = al.Regime(
        "dn/dt = (ninf-n)/ntau",
        "dm/dt = (minf-m)/mtau",
        "dh/dt = (hinf-h)/htau",
        "dV/dt = (ina + ik + il + Isyn)/C",
        transitions=al.On("V > theta", do=al.SpikeOutputEvent())
    )

# the rest are not "parameters" but aliases, assigned vars, state vars,
# indep vars, analog_analog_ports, etc.
    parameters = ['el', 'C', 'ek', 'ena', 'gkbar', 'gnabar', 'theta', 'gl', 'celsius', ]

    analog_ports = [al.SendPort("V"), al.ReducePort("Isyn", reduce_op="+")]

    c1 = al.ComponentClass("HodgkinHuxley",
                           parameters=parameters,
                           regimes=(hh_regime,),
                           aliases=aliases,
                           analog_ports=analog_ports)
    return c1
