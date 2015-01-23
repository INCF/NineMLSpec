"""

"""

import nineml.abstraction_layer as al

model = al.ComponentClass(
    name="Poisson",
    regimes=[
        al.Regime(
            name="default",
            transitions=al.On("t > t_next",
                              do=["t_next = t + random.exponential(1000/rate)",
                                  al.OutputEvent('spikeOutput')]))
    ],
    event_ports=[al.SendEventPort('spikeOutput')],
    state_variables=[al.StateVariable('t_next', dimension="time")],
    parameters=["rate"]
)


if __name__ == "__main__":
    from nineml.abstraction_layer.dynamics.writers import XMLWriter
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    XMLWriter.write(model, filename)
