
"""
Example of using a cell type defined in 9ML with pyNN.neuron
"""


def run(plot_and_show=True):

    import sys
    from os.path import abspath, realpath, join
    import nineml

    root = abspath(join(realpath(nineml.__path__[0]), "../../.."))
    sys.path.append(join(root, "lib9ml/python/examples/AL"))
    sys.path.append(join(root, "code_generation/nmodl"))

    from nineml.abstraction_layer.example_models import get_hierachical_iaf_2coba
    from nineml.abstraction_layer.flattening import ComponentFlattener

    import pyNN.neuron as sim
    import pyNN.neuron.nineml as pyNNml

    from pyNN.utility import init_logging

    init_logging(None, debug=True)
    sim.setup(timestep=0.1, min_delay=0.1)

    testModel = get_hierachical_iaf_2coba()

    celltype_cls = pyNNml.nineml_celltype_from_model(
        name="iaf_2coba",
        nineml_model=testModel,
        synapse_components=[
            pyNNml.CoBaSyn(
                namespace='cobaExcit',  weight_connector='q'),
            pyNNml.CoBaSyn(
                namespace='cobaInhib',  weight_connector='q'),
        ]
    )

    parameters = {
        'iaf.cm': 1.0,
        'iaf.gl': 50.0,
        'iaf.taurefrac': 5.0,
        'iaf.vrest': -65.0,
        'iaf.vreset': -65.0,
        'iaf.vthresh': -50.0,
        'cobaExcit.tau': 2.0,
        'cobaInhib.tau': 5.0,
        'cobaExcit.vrev': 0.0,
        'cobaInhib.vrev': -70.0,
    }

    parameters = ComponentFlattener.flatten_namespace_dict(parameters)

    cells = sim.Population(1, celltype_cls, parameters)
    cells.initialize('iaf_V', parameters['iaf_vrest'])
    cells.initialize('tspike', -1e99)  # neuron not refractory at start
    cells.initialize('regime', 1002)  # temporary hack

    input = sim.Population(2, sim.SpikeSourcePoisson, {'rate': 100})

    connector = sim.OneToOneConnector(weights=1.0, delays=0.5)
    # connector = sim.OneToOneConnector(weights=20.0, delays=0.5)

    conn = [sim.Projection(input[0:1], cells, connector, target='cobaExcit'),
            sim.Projection(input[1:2], cells, connector, target='cobaInhib')]

    cells._record('iaf_V')
    cells._record('cobaExcit_g')
    cells._record('cobaInhib_g')
    cells._record('regime')
    cells.record()

    sim.run(100.0)

    cells.recorders['iaf_V'].write("Results/nineml_neuron.V", filter=[cells[0]])
    cells.recorders['regime'].write("Results/nineml_neuron.regime", filter=[cells[0]])
    cells.recorders['cobaExcit_g'].write("Results/nineml_neuron.g_exc", filter=[cells[0]])
    cells.recorders['cobaInhib_g'].write("Results/nineml_neuron.g_inh", filter=[cells[0]])

    t = cells.recorders['iaf_V'].get()[:, 1]
    v = cells.recorders['iaf_V'].get()[:, 2]
    regime = cells.recorders['regime'].get()[:, 2]
    gInh = cells.recorders['cobaInhib_g'].get()[:, 2]
    gExc = cells.recorders['cobaExcit_g'].get()[:, 2]

    if plot_and_show:
        import pylab
        pylab.subplot(311)
        pylab.plot(t, v)
        pylab.subplot(312)
        pylab.plot(t, gInh)
        pylab.plot(t, gExc)
        pylab.subplot(313)
        pylab.plot(t, regime)
        pylab.ylim((999, 1005))
        pylab.suptitle("From Tree-Model Pathway")
        pylab.show()

    sim.end()


if __name__ == '__main__':
    run(plot_and_show=True)
else:
    run(plot_and_show=False)
