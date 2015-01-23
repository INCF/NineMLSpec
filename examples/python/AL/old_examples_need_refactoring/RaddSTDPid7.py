
"""

Implements reward modulated additive STDP with efficacies
as described on page 3650 of:

M. Farries and A. Fairhall (2007),
Reinforcement Learning With Modulated Spike Timing–Dependent
Synaptic Plasticity. J. Neurophysiol. 98 3648--3665


Author: Abigail Morrison, 1/2011.

"""

import nineml.abstraction_layer as nineml

# note: this assumes that Pre/PostEvent are the arrival times of the event
# at the synapse, i.e. after application of axonal or back-propagation delays
regimes = [
    nineml.Regime(
        "dr/dt = -r/tau_plus",
        "do/dt = -o/tau_minus",
        "deps_r/dt = (1-eps_r)/tau_er",
        "deps_o/dt = (1-eps_o)/tau_eo",
        transitions=[nineml.On(nineml.PreEvent,
                               do=["W -= R * A_minus * eps_r * o,
                                   "W = max(W,W_min)",
                                   "r += eps_r",
                                   "eps_r = 0.0",
                                   nineml.PreEventRelay]),
                     nineml.On(nineml.PostEvent,
                               do=["W  += R*A_plus*eps_o*r",
                                   "W = max(W,W_max)",
                                   "o += eps_o",
                                   "eps_o = 0.0"])]
    )]
ports = [nineml.RecvPort("R"), nineml.SendPort("W")]

c1 = nineml.Component("RaddSTDPid7", regimes=regimes, ports=ports)

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "RaddSTDPid7"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
