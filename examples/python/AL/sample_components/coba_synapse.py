import nineml.abstraction_layer as al


def get_component():
    coba = al.dynamics.DynamicsClass(
        name="CobaSyn",
        aliases=["I:=g*(vrev-V)", ],
        regimes=[
            al.Regime(
                name="cobadefaultregime",
                time_derivatives=["dg/dt = -g/tau", ],
                transitions=al.On('spikeinput', do=["g=g+q"]),
            )
        ],
        state_variables=[al.StateVariable('g')],
        analog_ports=[al.AnalogReceivePort("V"), al.AnalogSendPort("I"), ],
        parameters=['tau', 'q', 'vrev']
    )
    return coba
