# encoding: utf-8
import nineml.user_layer as nineml

#catalog = "https://raw.githubusercontent.com/INCF/nineml/master/catalog/"
catalog = "https://raw.githubusercontent.com/apdavison/nineml/modular/catalog/"


tau_distr = nineml.RandomDistribution(
    "normal(20.0,3.0)",
    catalog + "randomdistributions/normal_distribution.xml",
    {'standardDeviation': (10.0, "dimensionless"),
     'mean': (50.0, "dimensionless")})

reset_distr = nineml.RandomDistribution(
    "uniform(-70.0,-60.0)",
    catalog + "randomdistributions/uniform_distribution.xml",
    {'lowerBound': (-70.0, "dimensionless"),
     'upperBound': (-60.0, "dimensionless")})

exc_cell_parameters = nineml.ParameterSet(
    C=(1.0, "nF"),
    gL=(tau_distr, "nS"),
    t_ref=(5.0, "ms"),
    theta=(-50.0, "mV"),
    vL=(-65.0, "mV"),
    V_reset=(reset_distr, "mV"))

inh_cell_parameters = nineml.ParameterSet(
    gL=(20.0, "nS"),
    V_reset=(-60.0, "mV"))
inh_cell_parameters.complete(exc_cell_parameters)

exc_celltype = nineml.SpikingNodeType("Excitatory neuron type",
                                      catalog + "neurons/leaky_iaf.xml",
                                      exc_cell_parameters)
inh_celltype = nineml.SpikingNodeType("Inhibitory neuron type",
                                      catalog + "neurons/leaky_iaf.xml",
                                      inh_cell_parameters)

grid2D = nineml.Structure("2D grid",
                          catalog + "networkstructures/2Dgrid.xml",
                          {'fillOrder': ("sequential", None),
                           'aspectRatioXY': (1.0, "dimensionless"),
                           'dx': (1.0, u"µm"), 'dy': (1.0, u"µm"),
                           'x0': (0.0, u"µm"), 'y0': (0.0, u"µm")})

exc_cells = nineml.Population("Excitatory cells", 100, exc_celltype,
                              nineml.PositionList(structure=grid2D))
inh_cells = nineml.Population("Inhibitory cells", 25, inh_celltype,
                              nineml.PositionList(structure=grid2D))
all_cells = nineml.Selection("All cells",
                             nineml.Any(
                             nineml.Eq("population[@name]", exc_cells.name),
                             nineml.Eq("population[@name]", inh_cells.name))
                             )

connection_rule = nineml.ConnectionRule("random connections",
                                        catalog + "connectionrules/random_fixed_probability.xml",
                                        {'p_connect': (0.1, "dimensionless")})

exc_psr = nineml.SynapseType("Excitatory post-synaptic response",
                             catalog + "postsynapticresponses/exp_g.xml",
                             dict(tau=(5.0, "ms"), vrev=(0.0, "mV"), q=(1.0, "dimensionless")))
                            # don't really want to be setting 'q' here
inh_psr = nineml.SynapseType("Inhibitory post-synaptic response",
                             catalog + "postsynapticresponses/exp_g.xml",
                             dict(tau=(5.0, "ms"), vrev=(-70.0, "mV"), q=(1.0, "dimensionless")))

exc_connection_type = nineml.ConnectionType("Static excitatory connections",
                                            catalog + "connectiontypes/static_connection.xml")  ##,
                                            ##{'weight': (0.1, "nS"), 'delay': (0.3, "ms")})
inh_connection_type = nineml.ConnectionType("Static inhibitory connections",
                                            catalog + "connectiontypes/static_connection.xml") ##,
                                            ##{'weight': (0.2, "nS"), 'delay': (0.3, "ms")})

exc2exc = nineml.Projection("Excitatory cells-Excitatory cells",
                            exc_cells, exc_cells, connection_rule,
                            exc_psr, exc_connection_type)
inh2all = nineml.Projection("Inhibitory connections",
                            inh_cells, all_cells, connection_rule,
                            inh_psr, inh_connection_type)

network = nineml.Group("Network")
network.add(exc_cells)
network.add(inh_cells)
network.add(all_cells)
network.add(exc2exc)
network.add(inh2all)

model = nineml.Model("Simple 9ML example model")
model.add_group(network)


if __name__ == "__main__":

    model.write("simple_example.xml")
