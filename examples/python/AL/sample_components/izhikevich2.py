import nineml.abstraction_layer as al


# parameters = ["Isyn","a", "b", "c", "d", "theta"]

def get_component():
    regimes = [
        al.Regime(
            name="subthreshold_regime",
            time_derivatives=[
                "dV/dt = 0.04*V*V + 5*V + 140.0 - U + Isyn",
                "dU/dt = a*(b*V - U)"],
            transitions=[al.On("V > theta",
                               do=["V = c",
                                   "U = U + d",
                                   al.OutputEvent('spikeoutput')])],

        )]

    analog_ports = [al.SendPort("V"),
                    al.ReducePort("Isyn", reduce_op="+")]

    c1 = al.ComponentClass("Izhikevich",
                           regimes=regimes,
                           analog_ports=analog_ports)
    return c1
