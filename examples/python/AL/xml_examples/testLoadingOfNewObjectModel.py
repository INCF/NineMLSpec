

from nineml.utility import LocationMgr
from os.path import join as Join
from nineml.abstraction_layer.xmlns import *

import nineml.abstraction_layer as al
import nineml.abstraction_layer.readers as readers
import nineml.abstraction_layer.writers as writers

import pyNN.neuron.nineml as pyNNml

from nineml.abstraction_layer.flattening import ComponentFlattener

#LocationMgr.StdAppendToPath()


sample_xml_dir = Join(LocationMgr.getCatalogDir(), "sample_xml_files")
tenml_dir = Join(LocationMgr.getCatalogDir(), "sample_xml_files/10ml/")


def t1():
    print 'Loading First XML File'
    print '----------------------'
    component = readers.XMLReader.read_component(Join(sample_xml_dir,
                                                      'PostTF_izhikevich.xml'))
    writers.XMLWriter.write(component, '/tmp/nineml_toxml1.xml')


def t2():
    print 'Loading Second XML File (IAF-Component'
    print '--------------------------------------'
    component = readers.XMLReader.read_component(Join(tenml_dir,
                                                      'comp_iaf.9ml'))
    writers.XMLWriter.write(component, '/tmp/nineml_toxml2.xml')


def t3():
    print 'Loading Third XML File (COBA-Component)'
    print '---------------------------------------'
    component = readers.XMLReader.read_component(Join(tenml_dir,
                                                      'comp_coba.9ml'))
    writers.XMLWriter.write(component, '/tmp/nineml_toxml3.xml')


def t4():
    print 'Loading Forth XML File (iaf-2coba-Model)'
    print '----------------------------------------'
    component = readers.XMLReader.read_component(
        Join(tenml_dir, 'iaf_2coba.10ml'), component_name='iaf')
    writers.XMLWriter.write(component, '/tmp/nineml_toxml4.xml', )
    model = readers.XMLReader.read_component(Join(tenml_dir, 'iaf_2coba.10ml'))

    from nineml.abstraction_layer.flattening import flatten
    from nineml.abstraction_layer.dynamics.utils.modifiers import (
        DynamicsModifier)

    flatcomponent = flatten(model, componentname='iaf_2coba')
    DynamicsModifier.close_analog_port(component=flatcomponent,
                                       port_name='iaf_iSyn', value='0')

    writers.XMLWriter.write(flatcomponent, '/tmp/nineml_out_iaf_2coba.9ml')

    import pyNN.neuron as sim
    from pyNN.utility import init_logging

    init_logging(None, debug=True)
    sim.setup(timestep=0.1, min_delay=0.1)
    print 'Attempting to simulate From Model:'
    print '----------------------------------'
    celltype_cls = pyNNml.nineml_celltype_from_model(
        name="iaf_2coba",
        nineml_model=flatcomponent,
        synapse_components=[
            pyNNml.CoBaSyn(namespace='cobaExcit', weight_connector='q'),
            pyNNml.CoBaSyn(namespace='cobaInhib', weight_connector='q'),
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

    conn = [sim.Projection(input[0:1], cells, connector, target='cobaExcit'),
            sim.Projection(input[1:2], cells, connector, target='cobaInhib')]

    cells._record('iaf_V')
    cells._record('cobaExcit_g')
    cells._record('cobaInhib_g')
    cells._record('cobaExcit_I')
    cells._record('cobaInhib_I')
    cells.record()

    sim.run(100.0)

    cells.recorders['iaf_V'].write("Results/nineml_neuron.V", filter=[cells[0]])
    cells.recorders['cobaExcit_g'].write("Results/nineml_neuron.g_exc", filter=[cells[0]])
    cells.recorders['cobaInhib_g'].write("Results/nineml_neuron.g_inh", filter=[cells[0]])
    cells.recorders['cobaExcit_I'].write("Results/nineml_neuron.g_exc", filter=[cells[0]])
    cells.recorders['cobaInhib_I'].write("Results/nineml_neuron.g_inh", filter=[cells[0]])

    t = cells.recorders['iaf_V'].get()[:, 1]
    v = cells.recorders['iaf_V'].get()[:, 2]
    gInh = cells.recorders['cobaInhib_g'].get()[:, 2]
    gExc = cells.recorders['cobaExcit_g'].get()[:, 2]
    IInh = cells.recorders['cobaInhib_I'].get()[:, 2]
    IExc = cells.recorders['cobaExcit_I'].get()[:, 2]

    import pylab
    pylab.subplot(311)
    pylab.ylabel('Voltage')
    pylab.plot(t, v)

    pylab.subplot(312)
    pylab.ylabel('Conductance')
    pylab.plot(t, gInh)
    pylab.plot(t, gExc)

    pylab.subplot(313)
    pylab.ylabel('Current')
    pylab.plot(t, IInh)
    pylab.plot(t, IExc)

    pylab.suptitle("From Tree-Model Pathway")
    pylab.show()

    sim.end()


t1()
t2()
t3()
t4()
