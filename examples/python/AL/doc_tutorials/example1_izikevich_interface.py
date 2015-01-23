import nineml.abstraction_layer as al

iz = al.ComponentClass(
    name="IzikevichNeuron",
    parameters=['a', 'b', 'c', 'd'],
    analog_ports=[al.AnalogPort('I', mode='recv'),
                  al.AnalogPort('V', mode='send')],
    event_ports=[al.EventPort('spikeoutput', mode='send')],
)
