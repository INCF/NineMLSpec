#! /usr/bin/env python
#
# Filename: hhid14.py
# Description:
# Author: Subhasis Ray
# Maintainer:
# Created: Wed Jan  5 12:23:02 2011 (+0530)
# Version:
# Last-Updated: Wed Jan 12 10:33:52 2011 (+0530)
#           By: Subhasis Ray
# Update #: 145
# URL:
# Keywords:
# Compatibility:
#
#

# Commentary:
#
# Generate prototype for the model used in Tiesinga et al 2004.
# This is mostly based on hh.py by Andrew Davison.
#

# Change log:
#
#
#

# Code:

import os
import nineml.abstraction_layer as al


aliases = [
    "q10 := 3.0**((celsius - 6.3)/10.0)",
    # Taking from hh.py - no formula in paper, but constant value 5 (which can
    # be achieved with celsius = 20.95)
    "alpha_m(V) := -0.1*(V+35.0)/(exp(-(V+35.0)/10.0) - 1.0)",
    # m - just a change of constant from hh.py
    "beta_m(V) := 4.0 * exp(-(V+60.0)/18.0)",
    "mtau(V) := 1/(q10*(alpha_m(V) + beta_m(V)))",
    "minf(V) := alpha_m(V)/(alpha_m(V) + beta_m(V))",

    "alpha_h(V) := 0.07*exp(-(V+58.0)/20.0)",               # h - just a change of constant
    "beta_h(V) := 1.0/(exp(-(V+28)/10.0) + 1.0)",
    "htau(V) := 1.0/(q10*(alpha_h(V) + beta_h(V)))",
    "hinf(V) := alpha_h(V)/(alpha_h(V) + beta_h(V))",
    "alpha_n(V) := -0.01*(V+34.0)/(exp(-(V+34.0)/10.0) - 1.0)",  # n
    "beta_n(V) := 0.125*exp(-(V+44.0)/80.0)",
    "ntau(V) := 1.0/(q10*(alpha_n(V) + beta_n(V)))",
    "ninf(V) := alpha_n(V)/(alpha_n(V) + beta_n(V))",
    "gna(m,h) := gnabar*m*m*m*h",                       #
    "gk(n) := gkbar*n*n*n*n",
    "ina(m,h,V) := gna(m,h)*(ena - V)",                 # currents
    "ik(n,V) := gk(n)*(ek - V)",
    "il(V) := gl*(el - V )",
]

equations = [
    "I(psi) := I0 + A0 * exp(- psi**2 / sigma_psi**2)",
    # psi - is the stimulus orientation and sigma_psi is the selectivity.
    # Probably this should be part of protocol.
]

# The Isyn was generated statistically in this paper.
#
# 1. The spike volleys had intervals normally distributed with mean P
# 2. Spike-time probability was the convolution of a Gaussian filter with the volley-time
# 3. Spike-times were generated as a Poisson process from the probability calculated in step 2.
# 4. Each input spike caused an exponentially decaying inhibitory conductance.
#
# TODO: how do we combine the above four into a state transition based
# system? What should be the components?
# I can think of NormalRNG -> GaussianFilter -> PoissonGenerator -> SpikeGenerator
#
# 1. Remove all volley intervals from buffer P[i-n], P[i-n+1], ..., P[i-j] where
#    sum(P[i-1] ... P[i-j] > 20 ms.
#    Generate a random sample P[i] from normal distribution with mean P and
#    coefficient of variation Cv. Generate P[i+1], P[i+2], P[i+n] until their
#    sum exceeds 20 ms (> 2 * SD of the Gaussian filter).
#
# 2. Calculate the "spike-time-probability" (STP) at current time t by convolving the Gaussian filter
#    SD = sigma and area = a * dt for all P[i] in buffer, where dt is the integration
#    timestep.
#
# 3. When it comes to computing the spikes, the paper is confusing. It says that
#    "input spike times were generated as a Poisson process from STP, as in [74]."
#    But ref [74] (Tiesinga, Fellous, Jos and Sejnowski, 2002. Network: Comput. Neural Syst. 13 (2002) 41–66))
#    does not even mention Poisson process, but computes firing probability by summing the firing rate over 1 s.
#    I am not clear if that resolves to a Poisson process. If we take STP to be the rate of
#    a homogeneous Poisson process, lambda, then the probability of a spike within the timestep t
#    to t+dt is STP * dt.
#
# 4. The synaptic conductance is exponentially decaying and can be easily implemented.
#
# 5. Causal vs non-causal Gaussian filter : My impression is that in
#    general a state machine cannot implement an noncausal Gaussian
#    filter. Although the current paper used a 40 ms window for the
#    Gaussian filter, this kind of a-priori spike generation will be
#    impossible to address with a state machine design as an
#    online-thing (because future can affect the past). We need to
#    separate the cases where all spikes/inputs are to be generated
#    beforehand and processed during simulation and where teh
#    spikes/inputs can be generated on-line during simulation.

hh_regime = al.Regime(
    "dn/dt = (ninf(V)-n)/ntau(V)",
    "dm/dt = (minf(V)-m)/mtau(V)",
    "dh/dt = (hinf(V)-h)/htau(V)",
    "dV/dt = (ina(m,h,V) + ik(n,V) + il(V) + Isyn - I)/C",
    # I is a current injected as a function of orientation
    name="hh_regime",
    transitions=al.On("V > theta", do=[al.SpikeOutputEvent])
)

parameters = ['el', 'C', 'ek', 'ena', 'gkbar', 'gnabar', 'theta', 'gl', 'celsius']

ports = [al.SendPort("V"),
         al.ReducePort("Isyn", op="+"),
         al.ReducePort("I", op="+"),
         # "op" keyword argument determines how multiple inputs to this port are handled ?
         ]
c1 = al.Component("Hodgkin-Huxley-id14", parameters=parameters,
                  regimes=(hh_regime,),
                  aliases=aliases, ports=ports)


# write to file object f if defined
try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:

    base = "HHid14"
    c1.write(base + ".xml")
    c2 = al.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))



#
# hhid14.py ends here
