"""

Implements leaky integrate-and-fire neuron model with delta jump
synapses as described eqns 1 and 3 of:

F. Baroni & P. Varona (2010),
Spike timing-dependent plasticity is affected by the interplay of
intrinsic and network oscillations. J. Physiol. 104 91--98


Author: Abigail Morrison, 1/2011.

"""
import nineml.abstraction_layer as nineml

# there may be a better way of doing this. this also does not clamp the individual v_i to
# v_reset durung the refractory period, it just doesn't sum over them.

regimes = [
    nineml.Regime(
        "dv/dt = Isyn",
        transitions=nineml.On("V>Vth",
                              do=["tspike = t", "V = Vrest", nineml.SpikeOutputEvent],
                              to=refractory - regime),
        name="sub-threshold-regime"
    ),
    nineml.Regime(
        transitions=nineml.On("t >= tspike + trefractory", to="sub-threshold-regime"),
        name="refractory-regime"
    )]


ports = [nineml.ReducePort("Isyn", op="+")]

leaky_iaf = nineml.Component("deltaLIFid5", regimes=regimes, ports=ports)

# delta jump synapses

regimes = [
    nineml.Regime(
        "dv/dt = -g*v",
        transitions=nineml.On(nineml.SpikeInputEvent, do="g+=W"),
    )]

ports = [nineml.RecvPort("W"),
         nineml.SendPort("Isyn = dv/dt")]

# can i even send dv/dt as a variable?
delta_syn = nineml.Component("delta_jump_id5", regimes=regimes, ports=ports)


# User layer connects
# leaky_iaf.ports['V'] -> delta_syn.ports['V']
# delta_syn.ports['Isyn'] -> leaky_iaf.ports['Isyn'] for multiple synapses (reduce port)
# Simulator attaches to SpikeInput and SpikeOutput ports for input and output.


# write to file object f if defined

c1 = leaky_iaf
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "gLIFid1"
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

    base = "exp_cond_id1"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
