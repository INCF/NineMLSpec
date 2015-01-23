import nineml.abstraction_layer as nineml

# define a step current

# parameters = ["t_step", "dI"]

step = nineml.Regime(transitions=nineml.On("t>t_step", do=["I+=dI"]))
ports = [nineml.SendPort("I")]

c1 = nineml.Component("Step Current", regimes=(step,))

# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "step_current"
    c1.write(base + ".xml")
    c2 = nineml.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
