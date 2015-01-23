"""

Implements conductance based leaky integrate-and-fire neuron model
with afterhyperpolarization conductance as described on p 3649 of:

M. Farries and A. Fairhall (2007),
Reinforcement Learning With Modulated Spike Timing–Dependent
Synaptic Plasticity. J. Neurophysiol. 98 3648--3665


Author: Abigail Morrison, 1/2011.

"""
import nineml.abstraction_layer as nineml

regimes = [
    nineml.Regime(
        "dV/dt = g_R*(Vrest - V)/C + Isyn/C + g_AHP(E_AHP-V)/C",
        "dg_AHP/dt = -g_AHP/tau_AHP",
        transitions=nineml.On(
            "V>T", do=["tspike = t", "g_AHP = g_AHP+Delta_g", nineml.SpikeOutputEvent]),
        name="sub-threshold-regime"
    )]


ports = [nineml.SendPort("V"),
         nineml.ReducePort("Isyn", op="+")]

leaky_iaf = nineml.Component("gLIFid7", regimes=regimes, ports=ports)

# exponential conductances

regimes = [
    nineml.Regime(
        "dg/dt = -g/tau_syn",
        transitions=nineml.On(nineml.SpikeInputEvent, do="g+=W"),
    )]

ports = [nineml.RecvPort("V"),
         nineml.RecvPort("W"),
         nineml.SendPort("Isyn = g(E-V)")]


coba_syn = nineml.Component("exp_cond_id7", regimes=regimes, ports=ports)

# User layer connects
# leaky_iaf.ports['V'] -> coba_syn.ports['V']
# coba_syn.ports['Isyn'] -> leaky_iaf.ports['Isyn'] for multiple synapses (reduce port)
# Simulator attaches to SpikeInput and SpikeOutput ports for input and output.


# write to file object f if defined

c1 = leaky_iaf
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "gLIFid7"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))


c1 = coba_syn
# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "exp_cond_id7"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
