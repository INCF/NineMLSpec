
from nineml.abstraction_layer.dynamics import ComponentClass
from nineml.abstraction_layer.dynamics.testing_utils import RecordValue

import nmda
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
        # NMDA parameters from Gertner's book, pg 53.
        'nmda.taur': 3.0,  # ms
        'nmda.taud': 40.0,  # ms
        'nmda.gmax': 1.2,  # nS
        'nmda.E': 0.0,
        'nmda.gamma': 0.062,  # 1/mV
        'nmda.mgconc': 1.2,  # mM
        'nmda.beta': 3.57  # mM
    }

    initial_values = {
        'iaf_V': parameters['iaf.vrest'],
        'tspike': -1e99,
        'regime': 1002,
    }

    synapse_components = [
        ('nmda',  'weight'),
        ('cobaExcit', 'q'),
    ]

    records = [
        RecordValue(what='iaf_V',       tag='Voltage [mV]',     label='Membrane Voltage'),
        RecordValue(what='nmda_g',      tag='Conductance [ns]', label='NMDA-g'),
        RecordValue(what='cobaExcit_g', tag='Conductance [ns]', label='cobaexcit-g'),
        RecordValue(what='regime',      tag='Regime',           label='Regime'),
    ]


def get_component():
    # Create a model, composed of an iaf neuron, and
    iaf_nmda_model = ComponentClass(
        name="iaf_2coba",
        subnodes={"iaf":     iaf.get_component(),
                  "nmda":    nmda.get_component(),
                  'cobaExcit': coba_synapse.get_component()
                      })

    iaf_nmda_model.connect_ports("iaf.V", "cobaExcit.V")
    iaf_nmda_model.connect_ports("iaf.V", "nmda.V")
    iaf_nmda_model.connect_ports("cobaExcit.I", "iaf.ISyn")
    iaf_nmda_model.connect_ports("nmda.I", "iaf.ISyn")

    return iaf_nmda_model
