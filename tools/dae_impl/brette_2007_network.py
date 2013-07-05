#!/usr/bin/env python
"""
.. module:: brette_2007_network.py
   :platform: GNU/Linux, Windows, MacOS
   :synopsis:

.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import os

import nineml
import nineml.user_layer

import sedml_support as sedml
from nineml_point_neurone_network import simulate_network

###############################################################################
#                           NineML UserLayer Model
###############################################################################
N_neurons = 200
N_exc     = int(N_neurons * 0.8)
N_inh     = int(N_neurons * 0.2)
N_poisson = 20

"""
Ideally the catalog folder should be:
    catalog = 'file://' + os.path.join(sys.path[0], 'catalog')
but for some reasons it can't be resolved in windows. 
"""
catalog = 'catalog'
    
"""
The parameters values are adopted from the Brette et al (2007) paper.
Their values are for the network of 4000 neurones; the weights here should be changed to
account for the lower number of neurones.
"""

"""
ACHTUNG, ACHTUNG!!
Whats the purpose of units here?? Units make sense when used as a value of a parameter.
RNG itself have no idea how to use them. Therefore, the user has to be careful with
the values, to ensure that the produced random number values match the desired units.

Here, the units should be mV, but they are not used. They do get used below in 'poisson_params',
parameter V. There we have to specify the correct units (mV).
"""
rnd_uniform_params = {
                        'lowerBound': (-60, ''),
                        'upperBound': (-40, '')
                     }
uni_distr = nineml.user_layer.RandomDistribution("uniform(-0.060, -0.040)", os.path.join(catalog, "uniform_distribution.xml"), rnd_uniform_params)

poisson_params = {
                    'rate'     : (100, 'Hz'),
                    'duration' : ( 50, 'ms'),
                    't0'       : (  0, 'ms')
                 }

neurone_params = {
                    'tspike' :    ( -1.000,   's'),
                    'V' :         (uni_distr, 'mV'), # ACHTUNG!! Here the units should match those 
                                                     # produced by the uni_distr; it seems that this is
                                                     # a responsibility of the user...
                    'gl' :        ( 10, 'nS'),
                    'vreset' :    (-60, 'mV'),
                    'taurefrac' : (  1, 'ms'),
                    'vthresh' :   (-40, 'mV'),
                    'vrest' :     (-60, 'mV'),
                    'cm' :        (0.2, 'nF')
                 }

psr_poisson_params = {
                        'vrev'   : (0, 'mV'),
                        'weight' : (0, 'nS'),
                        'tau'    : (5, 'ms'),
                        'g'      : (0, 'nS')
                     }

psr_excitatory_params = {
                            'vrev'  : (0, 'mV'),
                            'weight': (0, 'nS'),
                            'tau'   : (5, 'ms'),
                            'g'     : (0, 'mS')
                        }
                
psr_inhibitory_params = {
                            'vrev'   : (-80, 'mV'),
                            'weight' : (  0, 'nS'),
                            'tau'    : ( 10, 'ms'),
                            'g'      : (  0, 'mS')
                        }

neurone_IAF     = nineml.user_layer.SpikingNodeType("IAF neurone", os.path.join(catalog, "iaf.xml"), neurone_params)

neurone_poisson = nineml.user_layer.SpikingNodeType("Poisson Source", os.path.join(catalog, "spike_source_poisson.xml"), poisson_params)

psr_poisson     = nineml.user_layer.SynapseType("COBA poisson",    os.path.join(catalog, "coba_synapse.xml"), psr_poisson_params)
psr_excitatory  = nineml.user_layer.SynapseType("COBA excitatory", os.path.join(catalog, "coba_synapse.xml"), psr_excitatory_params)
psr_inhibitory  = nineml.user_layer.SynapseType("COBA inhibitory", os.path.join(catalog, "coba_synapse.xml"), psr_inhibitory_params)

grid2d_params = {
                    'x0'            : (0.00, 'm'),
                    'y0'            : (0.00, 'm'), 
                    'dx'            : (1E-5, 'm'),
                    'dy'            : (1E-5, 'm'),
                    'fillOrder'     : (0.00, ''),
                    'aspectRatioXY' : (0.00, '')
                }
grid2D = nineml.user_layer.Structure("2D Grid", os.path.join(catalog, "grid_2d.xml"), grid2d_params)

connection_type = nineml.user_layer.ConnectionType("ConnectionType - not used", os.path.join(catalog, "not_used.xml"))

population_excitatory = nineml.user_layer.Population("Excitatory population", N_exc,     neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
population_inhibitory = nineml.user_layer.Population("Inhibitory population", N_inh,     neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
population_poisson    = nineml.user_layer.Population("Poisson population",    N_poisson, neurone_poisson, nineml.user_layer.PositionList(structure=grid2D))

# Create connection rules (using CSA)
# The original parameters' values are for the network of 4000 neurones
# We can scale weights to 
sf = 2000.0/N_neurons

exc_params = {
                'p'      : (  0.02, ''),
                'weight' : (sf * 4, 'nS'),
                'delay'  : (   0.2, 'ms')
             }
inh_params = {
                'p'      : (0.02, ''),
                'weight' : (  51, 'nS'),
                'delay'  : ( 0.2, 'ms')
             }
poi_params = {
                'p'      : (0.02, ''),
                'weight' : ( 100, 'nS'),
                'delay'  : ( 0.2, 'ms')
             }

connection_rule_exc_exc     = nineml.user_layer.ConnectionRule("Connections exc_exc",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), exc_params)
connection_rule_exc_inh     = nineml.user_layer.ConnectionRule("Connections exc_inh",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), exc_params)
connection_rule_inh_inh     = nineml.user_layer.ConnectionRule("Connections inh_inh",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), inh_params)
connection_rule_inh_exc     = nineml.user_layer.ConnectionRule("Connections inh_exc",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), inh_params)
connection_rule_poisson_exc = nineml.user_layer.ConnectionRule("Connections poisson_exc", os.path.join(catalog, "random_fixed_probability_w_d.xml"), poi_params)
connection_rule_poisson_inh = nineml.user_layer.ConnectionRule("Connections poisson_inh", os.path.join(catalog, "random_fixed_probability_w_d.xml"), poi_params)

# Create projections
projection_exc_exc     = nineml.user_layer.Projection("Projection exc_exc",     population_excitatory, population_excitatory, connection_rule_exc_exc,     psr_excitatory, connection_type)
projection_exc_inh     = nineml.user_layer.Projection("Projection exc_inh",     population_excitatory, population_inhibitory, connection_rule_exc_inh,     psr_excitatory, connection_type)
projection_inh_inh     = nineml.user_layer.Projection("Projection inh_inh",     population_inhibitory, population_inhibitory, connection_rule_inh_inh,     psr_inhibitory, connection_type)
projection_inh_exc     = nineml.user_layer.Projection("Projection inh_exc",     population_inhibitory, population_excitatory, connection_rule_inh_exc,     psr_inhibitory, connection_type)
projection_poisson_exc = nineml.user_layer.Projection("Projection poisson_exc", population_poisson,    population_excitatory, connection_rule_poisson_exc, psr_poisson,    connection_type)
projection_poisson_inh = nineml.user_layer.Projection("Projection poisson_inh", population_poisson,    population_inhibitory, connection_rule_poisson_inh, psr_poisson,    connection_type)

# Add everything to a single group
group = nineml.user_layer.Group("Group 1")

# Add populations
group.add(population_poisson)
group.add(population_excitatory)
group.add(population_inhibitory)

# Add projections
group.add(projection_poisson_exc)
group.add(projection_poisson_inh)
group.add(projection_exc_exc)
group.add(projection_exc_inh)
group.add(projection_inh_inh)
group.add(projection_inh_exc)

# Create a network and add the group to it
name = 'brette_2007_network'
nineml_filename = name + ' - nineml.xml'

ul_model = nineml.user_layer.Model(name)
ul_model.add_group(group)
ul_model.write(nineml_filename)

"""
ul_model_copy = nineml.user_layer.parse(nineml_filename)
ul_model_copy.write(name + ' - copy.xml')
# For some reasons The files are not equal (if compared by content)
assert(ul_model == ul_model_copy)
"""

###############################################################################
#                            SED-ML experiment
###############################################################################
timeHorizon       = 0.1000 # seconds
reportingInterval = 0.0001 # seconds
noPoints          = 1 + int(timeHorizon / reportingInterval)

sedml_simulation = sedml.UniformTimeCourseSimulation('simulation', 'Brette_2007_simulation', 0.0, 0.0, timeHorizon, noPoints, 'KISAO:0000071')

sedml_model      = sedml.Model('model', 'Brette_2007_model', 'urn:sedml:language:nineml', nineml_filename) 

sedml_task       = sedml.Task('task', 'Brette_2007_task', sedml_model, sedml_simulation)

sedml_variable_time  = sedml.Variable('time',  'Time',                              sedml_task, symbol='urn:sedml:symbol:time')
sedml_variable_excV1 = sedml.Variable('excV1', 'Excitatory_neurone[0]_voltage, V',  sedml_task, target='Group 1.Excitatory population[0].V')
sedml_variable_excV2 = sedml.Variable('excV2', 'Excitatory_neurone[3]_voltage, V',  sedml_task, target='Group 1.Excitatory population[3].V')
sedml_variable_excV3 = sedml.Variable('excV3', 'Excitatory_neurone[12]_voltage, V', sedml_task, target='Group 1.Excitatory population[12].V')
sedml_variable_inhV  = sedml.Variable('inhV',  'Inhibitory_neurone[5]_voltage, V',  sedml_task, target='Group 1.Inhibitory population[5].V')

sedml_data_generator_time = sedml.DataGenerator('DG_time', 'DG_time', [sedml_variable_time])
sedml_data_generator_excV = sedml.DataGenerator('DG_excV', 'DG_excV', [sedml_variable_excV1, sedml_variable_excV2, sedml_variable_excV3])
sedml_data_generator_inhV = sedml.DataGenerator('DG_inhV', 'DG_inhV', [sedml_variable_inhV])

curve_excV = sedml.Curve('ExcV', 'ExcV', False, False, sedml_data_generator_time, sedml_data_generator_excV)
curve_inhV = sedml.Curve('InhV', 'InhV', False, False, sedml_data_generator_time, sedml_data_generator_inhV)

plot_excV  = sedml.Plot2D('Plot_excV', 'Plot_excV', [curve_excV])
plot_inhV  = sedml.Plot2D('Plot_inhV', 'Plot_inhV', [curve_inhV])

sedml_experiment = sedml.Experiment([sedml_simulation], 
                                    [sedml_model], 
                                    [sedml_task], 
                                    [sedml_data_generator_time, sedml_data_generator_excV, sedml_data_generator_inhV],
                                    [plot_excV, plot_inhV])
    
sedml_filename = 'brette_2007_network - sedml.xml'
sedml_experiment.to_xml(sedml_filename)

simulate_network(sedml_filename)
    
