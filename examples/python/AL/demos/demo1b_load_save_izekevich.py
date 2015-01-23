"""

"""

from nineml.abstraction_layer import parse, writers, flattening
from nineml.abstraction_layer.testing_utils import (RecordValue,
                                                    TestableComponent,
                                                    std_pynn_simulation)

# Load the Component:
iz_file = '../../../../../../catalog/sample_xml_files/PostTF_izhikevich.xml'
iz = parse(iz_file)

# Write the component back out to XML
writers.XMLWriter.write(iz, 'TestOut_Iz.xml')
writers.DotWriter.write(iz, 'TestOut_Iz.dot')
writers.DotWriter.build('TestOut_Iz.dot')


# Simulate the Neuron:
records = [
    RecordValue(what='V', tag='V', label='V'),
    # RecordValue(what='U', tag='U', label='U'),
    # RecordValue( what='regime',     tag='Regime',  label='Regime' ),
]

parameters = flattening.ComponentFlattener.flatten_namespace_dict({
                                                                            'a': 0.02,
                                                                            'b': 0.2,
                                                                            'c': -65,
                                                                            'd': 8,
                                                                            'iinj_constant': 50.0,
                                                                            })

res = std_pynn_simulation(test_component=iz,
                          parameters=parameters,
                          initial_values={},
                          synapse_components=[],
                          records=records,
                          )
