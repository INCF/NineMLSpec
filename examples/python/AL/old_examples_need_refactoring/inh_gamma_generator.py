from nineml.abstraction_layer import *

# Case study:
# Inhomogeneous Gamma Renewal Process

# This is NOT valid 9ML

# Problems:
# - gamma_hazard
# - exp_rand
# - rand
# Implementation conformence:
# - Transitions are simulataneous if their conditions can be simultaneously true.
# - If the Regime solver has a timestep of dt, then transitions on the time-scale of dt are treated as simulteneous.
# - all Regime Transition conditions _must_ be evaluated before running any transition nodes
# - When Simultaneous transitions occur, the order of execution of each
#   simulataneous transition's do=[] code is not specifiable, i.e. the user
#   should take care that the order does not matter.  Only one transition can
#   transition, and the transition happens after all do=[] code is
#   executed.

poisson_thin_process = On("t>t_next", do="t_next = t + exp_rand(nu_max)")

gamma_hazard = On("( t>t_next ) & ( rand(0.0,1.0)<gamma_hazard(age,a,b)/nu_max) )",
                  do=["age = 0.0", SpikeOutputEvent])

regime = Regime(
    "dage/dt = 1.0",
    transitions=[poisson_thin_process, gamma_hazard]
)

# As a,b are time varying, they must come in through analog ports, rather than a user parameter.
ports = [RecvPort("a"), RecvPort("b")]

c1 = Component("Inhomogeneous Gamma Renewal Process (thinning method)",
               regimes=[regime], ports=ports)


try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "inh_gamma_generator"
    c1.write(base + ".xml")
    c2 = parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
