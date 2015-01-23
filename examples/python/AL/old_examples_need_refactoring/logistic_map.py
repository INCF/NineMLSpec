from nineml.abstraction_layer import *

# Case study:
# The logistic map in 9ML

# Initial conditions
# n = 0
# x = x0
# i = 1

regime = Regime(
    "dn/dt = 1",
    transitions=On("n >=i",
                   do=["x = r*x*(1.0-x)",
                       "i += 1",
                       # trigger an transition such that the client
                       # can read the new map iteration
                       EventPort("iteration-trigger", mode="send")]
                   )
)

ports = [SendPort("x"),  # the value of the logistic map at i
         SendPort("i")]  # the present value of the iteration

c1 = Component("Logistic Map", regimes=[regime], ports=ports)


try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "logistic_map"
    c1.write(base + ".xml")
    c2 = parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
