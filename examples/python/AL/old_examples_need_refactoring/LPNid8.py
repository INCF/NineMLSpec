"""

Implements linear poisson neuron as described in eq. 5 of:

R. Guetig, R. Aharonov, S. Rotter, and Haim Sompolinsky (2003),
Learning Input Correlations through Nonlinear Temporally Asymmetric
Hebbian Plasticity, J. Neuroscience, 23(9) 3697--3714


Author: Abigail Morrison, 1/2011.

"""


import nineml.abstraction_layer as nineml

regimes = [
    nineml.Regime(
        transitions=nineml.On(nineml.SpikeInputEvent, do=nineml.SpikeOutputEvent),
        name="ongoing-regime"
    )]

linear_poiss = nineml.Component("LPNid8", regimes=regimes, ports=[])

inter_event_regime = nineml.Regime(
    transitions=nineml.On(nineml.SpikeInputEvent,
                          do=["pfire = W/N", "p = rand()"],
                          to="probabilistic_regime"),
    name="inter_event_regime"
)

probabilistic_regime = nineml.Regime(
    transitions=[nineml.On("pfire >= p",
                           do=nineml.SpikeInputEventRelay,
                           to=inter_event_regime),
                 nineml.On("pfire < p",
                           to=inter_event_regime)],
    name="probabilistic_regime"
)

ports = [nineml.RecvPort("W")]
# problems: assumes the presence of a decent rand function

prob_input = nineml.Component("prob_id8", regimes=[inter_event_regime, probabilistic_regime])


c1 = linear_poiss
# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "LPNid8"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))

c1 = prob_input
# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "prob_id8"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
