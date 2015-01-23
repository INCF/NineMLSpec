# encoding: utf-8
import nineml.user_layer as nineml

catalog = "http://svn.incf.org/svn/nineml/trunk/catalog/"

cell_parameters = {
    "membraneCapacitance": (1.0, "nF"),
    "membraneTimeConstant": (20.0, "ms"),
    "refractoryTime": (5.0, "ms"),
    "threshold": (-50.0, "mV"),
    "restingPotential": (-65.0, "mV"),
    "resetPotential": (-70.0, "mV"),
}

exc_celltype = nineml.SpikingNodeType(
    name="Excitatory neuron type",
    definition=catalog + "neurons/IaF_tau.xml",
    parameters=cell_parameters)

inh_celltype = nineml.SpikingNodeType(
    name="Inhibitory neuron type",
    definition=catalog + "neurons/IaF_tau.xml",
    parameters=cell_parameters)

inner_grid = nineml.Structure(
    name="neuronal grid with 1 micron spacing",
    definition=catalog + "networkstructures/2Dgrid.xml",
    parameters={'fillOrder': ("sequential", None),
                'aspectRatioXY': (1.0, "dimensionless"),
                'dx': (1.0, u"µm"), 'dy': (1.0, u"µm"),
                'x0': (0.0, u"µm"), 'y0': (0.0, u"µm")})

outer_grid = nineml.Structure(
    name="column grid with 100 micron spacing",
    reference=inner_grid.name,
    parameters={'dx': (100.0, u"µm"), 'dy': (100.0, u"µm")})

exc_cells = nineml.Population(
    name="Excitatory cells",
    number=100,
    prototype=exc_celltype,
    positions=nineml.PositionList(structure=inner_grid))

inh_cells = nineml.Population(
    name="Inhibitory cells",
    number=25,
    prototype=inh_celltype,
    positions=nineml.PositionList(structure=inner_grid))

column = nineml.Group("Column")
column.add(exc_cells, inh_cells)

exc_psr = nineml.SynapseType(
    name="Excitatory post-synaptic response",
    definition=catalog + "postsynapticresponses/exp_g.xml",
    parameters={'decayTimeConstant': (5.0, "ms"),
                'reversalPotential': (0.0, "mV")})
inh_psr = nineml.SynapseType(
    name="Inhibitory post-synaptic response",
    reference=exc_psr.name,
    parameters={'reversalPotential': (-70.0, "mV")})

exc_connection_type = nineml.ConnectionType(
    name="Static excitatory connections",
    definition=catalog + "connectiontypes/static_connection.xml",
    parameters={'weight': (0.1, "nS"), 'delay': (0.3, "ms")})

inh_connection_type = nineml.ConnectionType(
    name="Static inhibitory connections",
    reference=exc_connection_type.name,
    parameters={'weight': (0.2, "nS")})

intra_column_connector = nineml.ConnectionRule(
    name="local random connections",
    definition=catalog + "connectionrules/fixed_probability.xml",
    parameters={'p_connect': (0.1, "dimensionless")})

inner_exc2all = nineml.Projection(
    name="Intra-column excitatory connections",
    source=exc_cells,
    target=column,
    rule=intra_column_connector,
    synaptic_response=exc_psr,
    connection_type=exc_connection_type)

inner_inh2all = nineml.Projection(
    name="Intra-column inhibitory connections",
    source=inh_cells,
    target=column,
    rule=intra_column_connector,
    synaptic_response=inh_psr,
    connection_type=inh_connection_type)

column.add(inner_exc2all, inner_inh2all)

inter_column_connector = nineml.ConnectionRule(
    name="lateral random connections",
    reference=intra_column_connector.name,
    parameters={'p_connect': (0.05, "dimensionless")})

network = nineml.Group("Network")

columns = nineml.Population(
    name="Columns",
    number=9,
    prototype=column,
    positions=nineml.PositionList(structure=outer_grid))

outer_exc2all = nineml.Projection(
    name="Inter-column excitatory connections",
    source=columns,
    target=columns,
    rule=inter_column_connector,
    synaptic_response=exc_psr,
    connection_type=exc_connection_type)

network.add(columns, outer_exc2all)

model = nineml.Model("Nested 9ML example model")
model.add_group(network)

model.write("nested_example.xml")
