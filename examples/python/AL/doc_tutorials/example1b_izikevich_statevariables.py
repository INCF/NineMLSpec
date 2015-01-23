import nineml.abstraction_layer as al

# Define a single regime, and specify the differential equations:
regime = al.Regime(
    name='defaultregime',
    time_derivatives=[
        'dV/dt = 0.04*V*V + 5*V + 140 -U + I',
        'dU/dt = a*(b*V - U)'
    ])


# Create the ComponentClass, including the dynamics.
iz = al.ComponentClass(
    name="IzikevichNeuron",
    parameters=['a', 'b', 'c', 'd'],
    analog_ports=[al.AnalogPort('I', mode='recv'),
                  al.AnalogPort('V', mode='send')],
    event_ports=[al.EventPort('spikeoutput', mode='send')],

    dynamics=al.Dynamics(regimes=[regime],
                         state_variables=['V', 'U'])
)
