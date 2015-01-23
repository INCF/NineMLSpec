# A leaky_iaf which defines analog_ports to play with an ampa synapse
import nineml.abstraction_layer as al


def get_component():
# Leaky iaf
    regimes = [
        al.Regime(
            "dV/dt = (-gL*(V-vL) + Isyn)/C",
            transitions=al.On(
                "V>Vth", do=["tspike = t", "V = V_reset", al.OutputEvent('spikeoutput')], to="refractory-regime"),
            name="sub-threshold-regime"
        ),
        al.Regime(
            transitions=al.On("t >= tspike + trefractory", to="sub-threshold-regime"),
            name="refractory-regime"
        )]

    analog_ports = [al.SendPort("V"),
                    al.ReducePort("Isyn", reduce_op="+")]

    leaky_iaf = al.ComponentClass("LeakyIAF", regimes=regimes, analog_ports=analog_ports)

# ampa

    regimes = [
        al.Regime(
            "dg/dt = -g/tau",
            transitions=al.On(al.SpikeInputEvent, do="g+=q")
        )]

    analog_ports = [al.RecvPort("V"),
                    al.SendPort("Isyn = g(E-V)")]

    coba_syn = al.ComponentClass("CoBaSynapse", regimes=regimes, analog_ports=analog_ports)

# User layer connects
# leaky_iaf.analog_ports['V'] -> coba_syn.analog_ports['V']
# coba_syn.analog_ports['Isyn'] -> leaky_iaf.analog_ports['Isyn'] for multiple synapses (reduce port)
# Simulator attaches to SpikeInput and SpikeOutput analog_ports for input and output.


# write to file object f if defined

c1 = coba_syn

try:
    # This case is used in the test suite for examples.
    c1.write(f)
except NameError:
    import os

    base = "leaky_iaf_ampa_analog_ports_events"
    c1.write(base + ".xml")
    c2 = al.parse(base + ".xml")
    assert c1 == c2

    c1.to_dot(base + ".dot")
    os.system("dot -Tpng %s -o %s" % (base + ".dot", base + ".png"))
