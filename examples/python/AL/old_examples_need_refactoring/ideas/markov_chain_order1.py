from nineml.abstraction_layer import *
import numpy

# Case study:
# N state Markov chain in 9ML

# This is NOT valid 9ML

# Why:
# - Need to allow events to go to Events
# - Need to allow from_=None
# - Need to allow for to=list of tuples: (target,probability)

N = 10
events = []

# build the events
for i in xrange(N):
    # N and not N-1, because it can return to itself, with some probability
    transition_matrix = numpy.uniform.random(size=N)
    # Normalize to 1
    transition_matrix /= numpy.sum(transition_matrix)

    e = Event("x = s%d" % i,
              "n+=1",
              # to=list, each element must be a tuple: (target,probability)
              # the implementation should check that the sum of probabilities is 1.0
              to=[("S%d" % i, transition_matrix[i]) for i in xrange(N)]
              name="S%d" % i)
    events += [e]

ports = [SendPort("x"), SendPort("n")]

markov_chain = nineml.Component("Order-1 Markov Chain", events=events, ports=ports)
