
"""

Implements Power-law weight dependence STDP as decribed in:

A. Morrison, A. Aertsen, M. Diesmann, "Spike-Timing-Dependent Plasticity in Balanced Random Networks", Neural Computation 2007.


Author: Eilif Muller, 2012.

"""

import nineml.abstraction_layer as nineml


regimes = [
    nineml.Regime(
        "dr/dt = -r1/tau_plus",
        "do/dt = -o1/tau_minus",
        transitions=[nineml.On(nineml.PreEvent,
                               do=["W  -= lambda*alpha*W*o",
                                   "r += 1.0",
                                   nineml.EventPort("PreEventRelay", mode="send")]),
                     nineml.On(nineml.PostEvent,
                               do=["W  += (lambda*w0*(weight/w0)^mu*r",
                                   "o += 1.0"])]
    )]

ports = [nineml.SendPort("W")]

c1 = nineml.Component("MorrisonPowerlawSTDP", regimes=regimes, ports=ports)

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "morrison_powerlaw_stdp"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
