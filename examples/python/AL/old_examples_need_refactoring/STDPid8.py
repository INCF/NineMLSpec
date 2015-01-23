
"""

Implements STDP with variable weight dependence as decribed in
eqns (1) and (2) of:

R. Guetig, R. Aharonov, S. Rotter, and Haim Sompolinsky (2003),
Learning Input Correlations through Nonlinear Temporally Asymmetric
Hebbian Plasticity, J. Neuroscience, 23(9) 3697--3714


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
                               do=["W  -= o*learning_rate*alpha*W**mu",
                                   "W = max(W,0.0)",
                                   "r += 1.0",
                                   nineml.PreEventRelay]),
                     nineml.On(nineml.PostEvent,
                               do=["W  += r*learning_rate*(1-W)**mu",
                                   "W = min(W,1.0)",
                                   "o += 1.0"])]
    )]
# should there be an additional parameter to scale the weight?
ports = [nineml.SendPort("W")]

c1 = nineml.Component("STDP_id8", regimes=regimes, ports=ports)

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "STDPid8"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
