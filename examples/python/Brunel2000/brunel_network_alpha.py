# encoding: utf-8
"""
Network model from

    Brunel, N. (2000) J. Comput. Neurosci. 8: 183-208

expressed in NineML using the Python API

Author: Andrew P. Davison, UNIC, CNRS
June 2014
"""

from __future__ import division
from math import exp
import nineml.user_layer as nineml

order = 25         # scales the size of the network
Ne = 4 * order     # number of excitatory neurons
Ni = 1 * order     # number of inhibitory neurons
epsilon = 0.1      # connectivity probability
Ce = epsilon * Ne  # total number of excitatory synapses
Ci = epsilon * Ni  # total number of inhibitory synapses
Cext = Ce          # total number of external synapses
delay = 1.5        # (ms) global delay for all neurons in the group
J = 0.1            # (mV) synaptic weight
g = 5.0            # relative strength of inhibitory synapses
eta = 2.0          # nu_ext / nu_thresh
Je = J             # excitatory weights
Ji = -g * Je       # inhibitory weights
Jext = Je          # external weights
theta = 20.0       # firing thresholds
tau = 20.0         # membrane time constant
tau_syn = 0.5      # synapse time constant
nu_thresh = theta / (Je * Ce * tau * exp(1.0) * tau_syn)  # threshold rate
nu_ext = eta * nu_thresh      # external rate per synapse
input_rate = 1000.0 * nu_ext  # mean input spiking rate

neuron_parameters = nineml.ParameterSet(tau=(tau, "ms"),
                                        theta=(theta, "ms"),
                                        tau_rp=(2.0, "ms"),
                                        Vreset=(10.0, "mV"),
                                        R=(1.5, "dimensionless"))  # units??
psr_parameters = nineml.ParameterSet(tau_syn=(tau_syn, "ms"))
neuron_initial_values = {"V": (0.0, "mV"),  # todo: use random distr.
                         "t_rpend": (0.0, "ms")}

exc_celltype = nineml.SpikingNodeType("E", "BrunelIAF.xml", neuron_parameters, initial_values=neuron_initial_values)
inh_celltype = nineml.SpikingNodeType("I", "BrunelIAF.xml", neuron_parameters, initial_values=neuron_initial_values)
ext_stim = nineml.SpikingNodeType("Ext", "Poisson.xml",
                                  nineml.ParameterSet(rate=(input_rate, "Hz")))
psr = nineml.SynapseType("Syn", "AlphaPSR.xml", psr_parameters)

connection_rule = nineml.ConnectionRule("RandomUniform",
                                        "RandomUniformConnection.xml",
                                        {'epsilon': (epsilon, "dimensionless")})

exc_cells = nineml.Population("Exc", Ne, exc_celltype, positions=None)
inh_cells = nineml.Population("Inh", Ni, inh_celltype, positions=None)
external = nineml.Population("Ext", int(Cext), ext_stim, positions=None)

all_cells = nineml.Selection("All neurons",
                             nineml.Any(
                                nineml.Eq("population[@name]", exc_cells.name),
                                nineml.Eq("population[@name]", inh_cells.name)))

all_to_all = nineml.ConnectionRule("AllToAll", "AllToAllConnection.xml")
random_uniform = nineml.ConnectionRule("RandomUniform", "RandomUniformConnection.xml", {"epsilon": (epsilon, "dimensionless")})

static_ext = nineml.ConnectionType("ExternalPlasticity", "StaticConnection.xml", {"delay": (delay, "ms")}, initial_values={"weight": (Jext, "nA")})
static_exc = nineml.ConnectionType("ExcitatoryPlasticity", "StaticConnection.xml", {"delay": (delay, "ms")}, initial_values={"weight": (Je, "nA")})
static_inh = nineml.ConnectionType("InhibitoryPlasticity", "StaticConnection.xml", {"delay": (delay, "ms")}, initial_values={"weight": (Ji, "nA")})

input_prj = nineml.Projection("External", external, all_cells,
                              rule=all_to_all,
                              synaptic_response=psr,
                              synaptic_response_ports=[("Isyn", "Isyn")],
                              connection_type=static_ext,
                              connection_ports=[("weight", "q")])
exc_prj = nineml.Projection("Excitation", exc_cells, all_cells,
                            rule=random_uniform,
                            synaptic_response=psr,
                            synaptic_response_ports=[("Isyn", "Isyn")],
                            connection_type=static_exc,
                            connection_ports=[("weight", "q")])
inh_prj = nineml.Projection("Inhibition", inh_cells, all_cells,
                            rule=random_uniform,
                            synaptic_response=psr,
                            synaptic_response_ports=[("Isyn", "Isyn")],
                            connection_type=static_inh,
                            connection_ports=[("weight", "q")])

network = nineml.Group("BrunelCaseC")
network.add(exc_cells, inh_cells, external, all_cells)
network.add(input_prj, exc_prj, inh_prj)
model = nineml.Model("Brunel (2000) network with alpha synapses")
model.add_group(network)



if __name__ == "__main__":
    model.write(__file__.replace(".py", ".xml"))
