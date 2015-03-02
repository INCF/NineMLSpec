

import nineml.abstraction_layer as al


def get_component():
    subthreshold_regime = al.Regime(
        name="subthreshold_regime",
        time_derivatives=[
            "dV/dt = 0.04*V*V + 5*V + 140.0 - U + Isyn",
            "dU/dt = a*(b*V - U)", ],

        transitions=[al.On("V > theta",
                           do=["V = c",
                                   "U =  U+ d",
                                   al.OutputEvent('spike'), ],
                           to='subthreshold_regime')]
    )

    ports = [al.SendPort("V"),
             al.ReducePort("Isyn", operator="+")]

    c1 = al.ComponentClass(
        name="Izhikevich",
        regimes=[subthreshold_regime],
        analog_ports=ports

    )
    return c1
