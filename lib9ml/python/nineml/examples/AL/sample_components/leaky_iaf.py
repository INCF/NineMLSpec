import nineml.abstraction_layer as al


def get_component():
    subthreshold_regime = al.Regime(
        name="subthreshold_regime",
        time_derivatives=["dV/dt = (-gL*(V-vL) + Isyn)/C", ],
        transitions=[al.On("V> theta",
                           do=["t_spike = t", "V = V_reset",
                                   al.OutputEvent('spikeoutput')],
                           to="refractory_regime")],
    )

    refractory_regime = al.Regime(
        transitions=[al.On("t >= t_spike + t_ref",
                           to='subthreshold_regime')],
        name="refractory_regime"
    )

    analog_ports = [al.SendPort("V"),
                    al.ReducePort("Isyn", operator="+")]

    c1 = al.ComponentClass("LeakyIAF", regimes=[
                           subthreshold_regime, refractory_regime], analog_ports=analog_ports)

    return c1
