import nineml.abstraction_layer.dynamics as nineml

# 9ML description of iaf_cond_exp
regimes = [
    nineml.Regime(
        "dV_m/dt = (-g_L*(V_m-E_L) + g_ex*(E_ex-V_m) + g_in*(E_in-V_m))/C_m",
        "dg_ex/dt = -g_ex/tau_syn_ex",
        "dg_in/dt = -g_in/tau_syn_in",
        transitions = [
            nineml.On("V_m>V_th",
                      do=["t_spike = t","V_m = V_reset",
                          nineml.SpikeOutputEvent()],
                      to="refractory_regime"),
            nineml.On('excitatory',
                      do="g_ex=g_ex+q_ex"),
            nineml.On('inhibitory',
                      do="g_in=g_in+q_in")
            ],
        name = "sub_threshold_regime"
    ),

    nineml.Regime(
        "dg_ex/dt = -g_ex/tau_syn_ex",
        "dg_in/dt = -g_in/tau_syn_in",
        transitions = [
            nineml.On("t >= t_spike + t_ref",
                      to="sub_threshold_regime"),
            nineml.On('excitatory',
                      do="g_ex=g_ex+q_ex"),
            nineml.On('inhibitory',
                      do="g_in=g_in+q_in")
            ],
        name = "refractory_regime"
    )]


ports = [nineml.SendPort("V_m"),
         nineml.ReducePort("Isyn", operator="+")]

iaf_cond_exp_9ML = nineml.ComponentClass("iaf_cond_exp",
                                         regimes=regimes,
                                         analog_ports=ports)

if __name__=="__main__":
    import os
    base = "iaf_cond_exp_9ML"
    iaf_cond_exp_9ML.to_dot(base+".dot")
    os.system("dot -Tpng %s -o %s" % (base+".dot",base+".png"))
    os.system("dot -Tsvg %s -o %s" % (base+".dot",base+".svg"))
