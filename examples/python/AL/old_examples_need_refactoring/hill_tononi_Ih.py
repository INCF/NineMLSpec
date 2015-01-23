from nineml.abstraction_layer import *

# H-current (I_h) from
#  Hill & Tononi, J Neurophysiol 93:1671-1698, 2005. doi:10.1152/jn.00915.2004
# Which in turn, is based on:
#  Huguenard, J.R. and McCormick, D.A. (1992) Voltage clamp simulations
# of currents involved in rhythmic oscillations in thalamic relay
# neurones. Journal of Neurophysiology, 68: 1373-1383.

regime = Regime(
    "m_inf(V) := 1/( 1 + exp((V-V_thresh)/5.5) )",
    "tau_m(V) := 1/( exp(-14.59 - 0.086*V) - exp(-1.87 + 0.0701*V) )",
    "dm/dt = (m_inf(V)-m)/tau_m(V)"
)

ports = [RecvPort("V"),
         SendPort("I = gmax*m*(E-V)")]

c1 = Component("Ih", regimes=[regime], ports=ports)


# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "hill_tononi_Ih"
    c1.write(base + ".xml")
    c2 = parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
