
"""

Implements additive STDP as described on page 521 of:

S. Bamford, A. Murray & D. Willshaw (2010),
Synaptic rewiring for topographic mapping and receptive field
development. Neural Network, 23 517-527


Author: Abigail Morrison, 1/2011.

"""

import nineml.abstraction_layer as nineml

# note: this assumes that Pre/PostEvent are the arrival times of the event
# at the synapse, i.e. after application of axonal or back-propagation delays
regimes = [
    nineml.Regime(
        "dr/dt = -r/tau_plus",
        "do/dt = -o/tau_minus",
        transitions=[nineml.On(nineml.PreEvent,
                               do=["W -= W_max * A_minus * o,
                                   "W = max(W,0.0)",
                                   "r += 1.0",
                                   nineml.PreEventRelay]),
                     nineml.On(nineml.PostEvent,
                               do=["W  += W_max*A_plus*r",
                                   "W = min(W,W_max)",
                                   "o += 1.0"])]
    )]
ports = [nineml.SendPort("W")]

c1 = nineml.Component("STDPid1", regimes=regimes, ports=ports)

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "STDPid1"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
