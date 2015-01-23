"""

"""

import nineml.abstraction_layer as al

model = al.ComponentClass(
    name="BrunelIaF",
    regimes=[
        al.Regime(
            name="subthresholdRegime",
            time_derivatives=["dV/dt = (-V + R*Isyn)/tau"],
            transitions=al.On("V > theta",
                              do=["t_rpend = t + tau_rp",
                                  "V = Vreset",
                                  al.OutputEvent('spikeOutput')],
                              to="refractoryRegime"),
        ),
        al.Regime(
            name="refractoryRegime",
            time_derivatives=["dV/dt = 0"],
            transitions=[al.On("t > t_rpend",
                               do=[al.OutputEvent('refractoryEnd')],
                               to="subthresholdRegime")],
        )
    ],
    state_variables=[
        al.StateVariable('V', dimension="voltage"),
        al.StateVariable('t_rpend', dimension="time")],
    analog_ports=[
        al.SendPort("V"),
        al.SendPort("t_rpend"),
        al.ReducePort("Isyn", reduce_op="+")],
    event_ports=[
        al.SendEventPort('spikeOutput'),
        al.SendEventPort('refractoryEnd')],
    parameters=['tau', 'theta', 'tau_rp', 'Vreset', 'R']
)


if __name__ == "__main__":
    from nineml.abstraction_layer.dynamics.writers import XMLWriter
    filename = __file__[0].upper() + __file__[1:].replace(".py", ".xml")
    XMLWriter.write(model, filename)
