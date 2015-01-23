import nineml.abstraction_layer as al


model = al.ComponentClass(
    name="SynapticConnectionWithFixedWeightAndDelay",
    regimes=[
        al.Regime(
            name="default",
            time_derivatives=[
                "dweight/dt = 0"],
            transitions=[al.On('spike',
                               do=["t_next = t + delay"]),
                         al.On('t > t_next',
                               do=al.OutputEvent('spikeOutput'))]
        )
    ],
    state_variables=[
        al.StateVariable('weight', dimension="current"),  # would be nice to make this dimensionless
        al.StateVariable('t_next', dimension="time")
    ],
    analog_ports=[al.SendPort("weight")],
    event_ports=[al.SendEventPort('spikeOutput'),
                 al.RecvEventPort('spike')],
    parameters=["delay"]
)


if __name__ == "__main__":
    from nineml.abstraction_layer.dynamics.writers import XMLWriter
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    XMLWriter.write(model, filename)
