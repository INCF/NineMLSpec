"""

Implements conductance based leaky integrate-and-fire neuron model
as decribed on p 3699 of:

R. Guetig, R. Aharonov, S. Rotter, and Haim Sompolinsky (2003),
Learning Input Correlations through Nonlinear Temporally Asymmetric
Hebbian Plasticity, J. Neuroscience, 23(9) 3697--3714


Author: Abigail Morrison, 1/2011.

"""
import nineml.abstraction_layer as nineml

regimes = [
    nineml.Regime(
        "dV/dt = (Vrest - V)/(Rm*Cm) + Isyn/Cm",
        transitions=nineml.On("V>Vth", do=["tspike = t", "V = Vrest", nineml.SpikeOutputEvent]),
        name="sub-threshold-regime"
    )]


ports = [nineml.SendPort("V"),
         nineml.ReducePort("Isyn", op="+")]

leaky_iaf = nineml.Component("gLIFid8", regimes=regimes, ports=ports)

# alpha conductances

regimes = [
    nineml.Regime(
        "dg_a/dt = -g_a/tau_a",
        "dg/dt = g_a - g/tau_a",
        transitions=nineml.On(nineml.SpikeInputEvent, do="g+=W"),
    )]

ports = [nineml.RecvPort("V"),
         nineml.RecvPort("W"),
         nineml.SendPort("Isyn = g(E-V)")]


coba_syn = nineml.Component("alpha_cond_id8", regimes=regimes, ports=ports)

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

    base = "gLIFid8"
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

    base = "alpha_cond_id8"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
