
# a benchmark of the inh_gamma_generator independent multiple targets
# feature.

# Compare simulation times to the equivalent multiple generator
# objects for independent realizations (bench.py).
#
# On my Opteron system, the timed simulation step is almost
# 20 times faster (than the bench.py implementation).
#

# Author: Eilif Muller

# See also: test_ng.py for a verification that this feature of
# inh_gamma_generator approachs yields identical spike trains to
# the equivalent multiple generator objects for independent realizations.


import nest
#nest.Install("mymodule")
import numpy

import time

nest.ResetKernel()

dt = 0.1 # milliseconds
tsim = 2 # seconds
bg_e = 6.0 # Hz
bg_i = 10.2 # Hz

nest.SetStatus([0],{'resolution':dt})

# neuron to receive input 

iaf = nest.Create('iaf_cond_exp',1)
iaf9ml =  nest.Create('iaf_cond_exp_9ml',1)

iafParams = {'V_th':-57.0, 'V_reset': -70.0, 't_ref': 20.0, 'g_L':28.95,
'C_m':289.5, 'E_L' : -70.0, 'E_ex': 0.0, 'E_in': -75.0, 'tau_syn_ex':1.5,
'tau_syn_in': 10.0}

nest.SetStatus(iaf,iafParams)
nest.SetStatus(iaf9ml,iafParams)


# excitatory input

ige = nest.Create('poisson_generator',1)

# inhihibtory input

igi = nest.Create('poisson_generator',1)

# set inh_gamma_generator parameters

# excitatory

ige_Params = {}
ige_Params['rate'] = bg_e
nest.SetStatus(ige,ige_Params)

# inhibitory

igi_Params = {}
igi_Params['rate'] = bg_i
nest.SetStatus(igi,igi_Params)
    
# connect

# note list multiplication : [0]*4 = [0,0,0,0]
# thus we have 1000 ex, 250 inh independent connections to iaf  

# build parrots
pe = nest.Create('parrot_neuron',1000)
pi = nest.Create('parrot_neuron',250)

nest.DivergentConnect(ige,pe,model='static_synapse')
nest.DivergentConnect(igi,pi,model='static_synapse')

# here now we are safe to chose a dynaic synapse
nest.ConvergentConnect(pe,iaf,[2.0],[dt],model='static_synapse')
nest.ConvergentConnect(pi,iaf,[-2.0],[dt],model='static_synapse')

# 9ml neuron needs to set receptor type
cParams = {'weight': 1.0, 'receptor_type': 1, #'model':'static_synapse',
           'delay': dt}
for x in pe:
    nest.Connect([x],iaf9ml,params=cParams )

cParams['receptor_type'] = 2
for x in pi:
    nest.Connect([x],iaf9ml,params=cParams )


# record spikes

spike_detector = nest.Create('spike_detector',1)

nest.Connect(iaf,spike_detector,model='static_synapse')
nest.Connect(iaf9ml,spike_detector,model='static_synapse')


m = nest.Create('multimeter',
                params = {'withtime': True, 
                          'interval': 0.1,
                          'record_from': ['V_m', 'g_ex', 'g_in']})


nest.Connect(m, iaf)

m_9ml = nest.Create('multimeter',
                params = {'withtime': True, 
                          'interval': 0.1,
                          'record_from': ['V_m', 'g_ex', 'g_in', 'Regime9ML']})

nest.Connect(m_9ml, iaf9ml)

# simulate

t1 = time.time()
nest.Simulate(tsim*1000)
t2 = time.time()
print "Elapsed: ", t2-t1, " seconds."

# get iaf spike output

spikes = nest.GetStatus(spike_detector,'events')[0]['times']
espikes = spikes.astype(float)

data = nest.GetStatus(m)[0]['events']
data_9ml = nest.GetStatus(m_9ml)[0]['events']

t = data["times"]

g_in = data["g_in"]
g_in_9ml = data_9ml["g_in"]

v = data["V_m"]
v_9ml = data_9ml["V_m"]

regime = data_9ml["Regime9ML"]



subplot(211)
plot(t,regime,'r-')
ylabel('regime')
axis([0, 500,0.0,3.0])

subplot(212)
plot(t,v,'g-',lw=4, label='iaf_cond_exp')
plot(t,v_9ml,'r-',lw=1.5,label='iaf_cond_exp_9ml')
xlabel("time [ms]")
ylabel("voltage [mV]")
axis([0, 500,-72, -55])
legend()


