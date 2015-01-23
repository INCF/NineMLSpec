

from nineml.abstraction_layer.dynamics import flattening

import hierachical_iaf_2coba

from nineml.abstraction_layer.dynamics.visitors import RenameSymbol


class ComponentMetaData(object):
    is_neuron_model = False

    # Standard Metadata:
    short_description = "Standard integrate and fire with exponential conductance based synapses"
    long_description = """
            Long description of the iaf_cond_exp ...
            Author: Eilif Muller, Ecublens, 2011
            """

    nest_classname = "iaf_cond_exp_9ml"

    # New - Corresponding to remapped ports:
    parameters = {'V_th': -57.0,
                  'V_reset': -70.0,
                  't_ref': 20.0,
                  'g_L': 28.95,
                  'C_m': 289.5,
                  'E_L': -70.0,
                  'E_ex': 0.0,
                  'E_in': -75.0,
                  'tau_syn_ex': 1.5,
                  'tau_syn_in': 10.0,
                  'q_ex': 2.0,
                  'q_in': 2.0,
                  }

    initial_values = {
        'V_m': -70.0,
        'tspike': -1e99,
        'regime': 1002,
        'g_ex': 0,
        'g_in': 0,
    }

    synapse_ports = ['spike_ex', 'spike_in']

    initial_regime = """ iaf:subthresholdregime
                         cobaInhib:cobadefaultregime
                         cobaExcit:cobadefaultregime
                     """


def get_component():

    component = hierachical_iaf_2coba.get_component()
    comp = flattening.flatten(component)

    # Remap some ports:
    RenameSymbol(comp, 'iaf_vthresh', 'V_th')
    RenameSymbol(comp, 'iaf_vreset', 'V_reset')
    RenameSymbol(comp, 'iaf_taurefrac', 't_ref')
    RenameSymbol(comp, 'iaf_vrest', 'E_L')
    RenameSymbol(comp, 'iaf_cm', 'C_m')
    RenameSymbol(comp, 'iaf_gl', 'g_L')
    RenameSymbol(comp, 'cobaExcit_vrev', 'E_ex')
    RenameSymbol(comp, 'cobaInhib_vrev', 'E_in')
    RenameSymbol(comp, 'cobaInhib_q', 'q_in')
    RenameSymbol(comp, 'cobaExcit_q', 'q_ex')
    RenameSymbol(comp, 'cobaExcit_tau', 'tau_syn_ex')
    RenameSymbol(comp, 'cobaInhib_tau', 'tau_syn_in')
    RenameSymbol(comp, 'iaf_V', 'V_m')
    RenameSymbol(comp, 'iaf_tspike', 'tspike')
    RenameSymbol(comp, 'cobaInhib_g', 'g_in')
    RenameSymbol(comp, 'cobaExcit_g', 'g_ex')
    RenameSymbol(comp, 'cobaInhib_spikeinput', 'spike_in')
    RenameSymbol(comp, 'cobaExcit_spikeinput', 'spike_ex')

    return comp
