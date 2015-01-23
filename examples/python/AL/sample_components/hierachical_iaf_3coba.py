

from nineml.abstraction_layer.dynamics import ComponentClass
from nineml.abstraction_layer.dynamics.testing_utils import RecordValue

import coba_synapse
import iaf


class ComponentMetaData(object):
    is_neuron_model = False

    supports_test_pynn_neuron_std = True

    parameters = {
        'iaf.cm': 1.0,
        'iaf.gl': 50.0,
        'iaf.taurefrac': 5.0,
        'iaf.vrest': -65.0,
        'iaf.vreset': -65.0,
        'iaf.vthresh': -50.0,
        'AMPA.tau': 2.0,
        'GABAa.tau': 5.0,
        'GABAb.tau': 50.0,
        'AMPA.vrev': 0.0,
        'GABAa.vrev': -70.0,
        'GABAb.vrev': -95.0,

    }

    initial_values = {
        'iaf_V': parameters['iaf.vrest'],
        'tspike': -1e99,
        'regime': 1002,
    }

    synapse_components = [
        ('AMPA', 'q'),
        ('GABAa', 'q'),
        ('GABAb', 'q'),
    ]

    records = [
        RecordValue(what='iaf_V',       tag='Voltage [mV]',     label='Membrane Voltage'),
        RecordValue(what='AMPA_g',      tag='Conductance [ns]', label='ampa-g'),
        RecordValue(what='GABAa_g',      tag='Conductance [ns]', label='GABAa-g'),
        RecordValue(what='GABAb_g',      tag='Conductance [ns]', label='GABAb-g'),
        RecordValue(what='regime',      tag='Regime',           label='Regime'),
    ]


def get_component():

    # Create a model, composed of an iaf neuron, and
    iaf_3coba_model = ComponentClass(name="iaf_3coba",
                                        subnodes={"iaf": iaf.get_component(),
                                                  "AMPA":  coba_synapse.get_component(),
                                                  "GABAa": coba_synapse.get_component(),
                                                  "GABAb":  coba_synapse.get_component(),
                                                  })

    # Connections have to be setup as strings, because we are deep-copying objects.
    iaf_3coba_model.connect_ports("iaf.V", "AMPA.V")
    iaf_3coba_model.connect_ports("iaf.V", "GABAa.V")
    iaf_3coba_model.connect_ports("iaf.V", "GABAb.V")
    iaf_3coba_model.connect_ports("AMPA.I", "iaf.ISyn")
    iaf_3coba_model.connect_ports("GABAa.I", "iaf.ISyn")
    iaf_3coba_model.connect_ports("GABAb.I", "iaf.ISyn")

    return iaf_3coba_model
