
"""

Implements triplet STDP as decribed in eqn (3) and (4) of:

J.P. Pfister and W. Gerstner, Triplets of Spikes in a Model of Spike
Timing-Dependent Plasticity, J. Neuroscience, Vol. 26, Nr. 38,
pp. 9673-9682, 2006.

Note: This model does not implement the adjustments to A2_plus and
A2_minus near the end of the paper to implement the mapping to a BCM rule.

Author: Eilif Muller, 2010.

"""

import nineml.abstraction_layer as nineml


regimes = [
    nineml.Regime(
        "dr1/dt = -r1/tau_plus",
        "dr2/dt = -r2/tau_x",
        "do1/dt = -o1/tau_minus",
        "do2/dt = -o2/tau_y",
        transitions=[nineml.On(nineml.PreEvent,
                               do=["W  -= o1*(A2_minus + A3_minus*r2)",
                                   "r1 += 1.0",
                                   "r2 += 1.0",
                                   nineml.EventPort("PreEventRelay", mode="send")]),
                     nineml.On(nineml.PostEvent,
                               do=["W  += r1*(A2_plus + A3_plus*o2)",
                                   "o1 += 1.0",
                                   "o2 += 1.0"])]
    )]

ports = [nineml.SendPort("W")]

c1 = nineml.Component("PfisterTripletSTDP", regimes=regimes, ports=ports)

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "pfister_triplet_stdp"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
