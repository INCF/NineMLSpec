import nineml.abstraction_layer as al

cond_decay = al.Regime(name='default',
                       time_derivatives=["dg/dt = -g/tau"],
                       transitions=[al.On(al.InputEvent('spikeinput'), do="g = g + q")]
                       )


coba_syn = al.ComponentClass(
    name="CoBaSynapse",
    dynamics=al.Dynamics(
        regimes=[cond_decay],
        aliases=["I := g*(E-V)"],
    ),
    analog_ports=[al.RecvPort("V"), al.SendPort("I")]
)
