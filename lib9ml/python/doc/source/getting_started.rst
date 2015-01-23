===============
Getting started
===============


Reading model descriptions from XML files
=========================================

NineML XML files can contain abstraction layer models, user layer models (with links to abstraction layer models
defined elsewhere) or both.

To read a file containing only abstraction layer elements:

.. code-block:: python

   >>> import nineml
   >>> items = nineml.read("BrunelIaF.xml")
   >>> items
   {'BrunelIaF': <dynamics.ComponentClass BrunelIaF>,
    'current': Dimension(name='current', i=1),
    'resistance': Dimension(name='resistance', i=-2, m=1, t=-3, l=2),
    'time': Dimension(name='time', t=1),
    'voltage': Dimension(name='voltage', i=-1, m=1, t=-3, l=2)}

This gives us a :class:`~nineml.Document` instance, a dictionary-like object containing a
:class:`~nineml.abstraction_layer.ComponentClass` definition of an integrate-and-fire
neuron model, together with the definitions of the physical dimensions of parameters
and state variables used in the model.

Now for a file containing an entire user layer model (with references to other XML files
containing the abstraction layer definitions):

.. code-block:: python

    >>> all_items = nineml.read("brunel_network_alpha_AI.xml")
    >>> from pprint import pprint
    >>> pprint(all_items)
    {'All neurons': <nineml.user_layer.containers.Selection object at 0x105c49cd0>,
     'Exc': Population(name='Exc', number=4000, cell=nrn),
     'Excitation': Projection(name="Excitation", source=Population(name='Exc', number=4000, cell=nrn), destination=<nineml.user_layer.containers.Selection object at 0x105c49cd0>, connectivity=BaseComponent(name="RandomExc", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExcitatoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
     'Ext': Population(name='Ext', number=5000, cell=stim),
     'External': Projection(name="External", source=Population(name='Ext', number=5000, cell=stim), destination=<nineml.user_layer.containers.Selection object at 0x105c49cd0>, connectivity=BaseComponent(name="OneToOne", componentclass="OneToOne"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExternalPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
     'Hz': Unit(name='Hz', dimension='per_time', power=0),
     'Inh': Population(name='Inh', number=1000, cell=nrn),
     'Inhibition': Projection(name="Inhibition", source=Population(name='Inh', number=1000, cell=nrn), destination=<nineml.user_layer.containers.Selection object at 0x105c49cd0>, connectivity=BaseComponent(name="RandomInh", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
     'Mohm': Unit(name='Mohm', dimension='resistance', power=6),
     'current': Dimension(name='current', i=1),
     'mV': Unit(name='mV', dimension='voltage', power=-3),
     'ms': Unit(name='ms', dimension='time', power=-3),
     'nA': Unit(name='nA', dimension='current', power=-9),
     'per_time': Dimension(name='per_time', t=-1),
     'resistance': Dimension(name='resistance', i=-2, m=1, t=-3, l=2),
     'time': Dimension(name='time', t=1),
     'voltage': Dimension(name='voltage', i=-1, m=1, t=-3, l=2)}

Again we get a dictionary-like object containing all the NineML objects in the XML file. An alternative
representation can be obtained by reading the file as a :class:`~nineml.user_layer.Network` object:

.. code-block:: python

    >>> from nineml.user_layer import Network
    >>> net = Network.read("brunel_network_alpha_AI.xml")
    >>> print(net)
    <nineml.user_layer.containers.Network object at 0x106442690>

This gives a much more structured representation. For example, all the :class:`~nineml.user_layer.Population`\s within the model are
available through the ``populations`` attribute:

.. code-block:: python

    >>> net.populations
    {'Exc': Population(name='Exc', number=4000, cell=nrn),
     'Ext': Population(name='Ext', number=5000, cell=stim),
     'Inh': Population(name='Inh', number=1000, cell=nrn)}




Introspecting NineML models
===========================

Introspecting abstraction layer models
--------------------------------------

Once we have loaded a model from an XML file we can begin to examine its structure.

.. code-block:: python

    >>> model = items['BrunelIaF']
    >>> model
    <dynamics.ComponentClass BrunelIaF>

We can see a list of model parameters:

.. code-block:: python

    >>> list(model.parameters)
    [Parameter(theta, dimension=voltage),
    Parameter(Vreset, dimension=voltage),
    Parameter(R, dimension=resistance),
    Parameter(tau_rp, dimension=time),
    Parameter(tau, dimension=time)]

a list of state variables:

.. code-block:: python

    >>> list(model.state_variables)
    >>> [StateVariable(V, dimension=voltage), StateVariable(t_rpend, dimension=time)]

and a list of the variables that are imported from/exposed to the outside world:

.. code-block:: python

    >>> list(model.ports)
    [AnalogSendPort('V', dimension='Dimension(name='voltage', i=-1, m=1, t=-3, l=2)'),
     AnalogSendPort('t_rpend', dimension='Dimension(name='time', t=1)'),
     AnalogReducePort('Isyn', dimension='Dimension(name='current', i=1)', op='+'),
     EventSendPort('spikeOutput')]

Delving more deeply, we can examine the model's regimes more closely:

.. code-block:: python

    >>> list(model.regimes)
    [Regime(refractoryRegime), Regime(subthresholdRegime)]
    >>> r_ref, r_sth = model.regimes

Looking first at the subthreshold regime, we can see the differential equations:

.. code-block:: python

    >>> list(r_sth.time_derivatives)
    [TimeDerivative( dV/dt = (-V + R*Isyn)/tau )]

and the conditions under which the model will transition to the refractory regime:

.. code-block:: python

    >>> list(r_sth.transitions)
    [OnCondition( V > theta )]
    >>> tr_spike = list(r_sth.transitions)[0]

The trigger for this transition is for the variable ``V`` to pass a threshold (parameter ``theta``):

.. code-block:: python

    >>> tr_spike.trigger
    Condition('V > theta')

When the transition is initiated, the model will emit an output event (i.e. a spike) and discontinusouly change
the values of some of the state variables:

.. code-block:: python

    >>> tr_spike.event_outputs
    [OutputEvent('spikeOutput')]
    >>> tr_spike.state_assignments
    [StateAssignment('t_rpend', 't + tau_rp'), StateAssignment('V', 'Vreset')]

Then it will move to the refractory regime:

.. code-block:: python

    >>> tr_spike.target_regime
    Regime(refractoryRegime)

The refractory regime can be introspected in a similar way.

Introspecting user layer models
-------------------------------

As shown above, once a complete network model has been loaded as a :class:`~nineml.user_layer.Network` object, we
can look at its neuron populations and the connections between these populations ("projections"):

.. code-block:: python

    >>> net.populations
    {'Exc': Population(name='Exc', number=4000, cell=nrn),
     'Ext': Population(name='Ext', number=5000, cell=stim),
     'Inh': Population(name='Inh', number=1000, cell=nrn)}

    >>> net.projections
    {'Excitation': Projection(name="Excitation", source=Population(name='Exc', number=4000, cell=nrn), destination=<nineml.user_layer.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="RandomExc", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExcitatoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
    'External': Projection(name="External", source=Population(name='Ext', number=5000, cell=stim), destination=<nineml.user_layer.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="OneToOne", componentclass="OneToOne"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExternalPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
    'Inhibition': Projection(name="Inhibition", source=Population(name='Inh', number=1000, cell=nrn), destination=<nineml.user_layer.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="RandomInh", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections)}

NineML also supports "selections", groupings of neurons which span populations:

.. code-block:: python

    >>> net.selections
    {'All neurons': Selection('All neurons', 'Concatenate(Reference(name="Exc"), Reference(name="Inh"))')}

.. note:: in NineML version 1, the only type of selection is a concatenation of two or more populations. In future
          versions it will be possible to select and combine sub-populations.

Looking more closely at a population, we can see its name, the number of neurons it contains and
the neuron model used (:class:`~nineml.user_layer.Component`):

.. code-block:: python

    >>> p_exc = net.populations['Exc']
    >>> p_exc
    Population(name='Exc', number=4000, cell=nrn)
    >>> p_exc.number
    4000
    >>> p_exc.cell
    BaseComponent(name="nrn", componentclass="BrunelIaF")

In the neuron model component we can see its abstraction layer definition
(:class:`~nineml.abstraction_layer.dynamics.ComponentClass`), it's properties (parameter values), and the initial
values of its state variables.

.. note:: the handling of initial values is likely to change in future versions of NineML.

.. code-block:: python

    >>> p_exc.cell.component_class
    <dynamics.ComponentClass BrunelIaF>
    >>> p_exc.cell.properties
    PropertySet({'Vreset': Property(name=Vreset, value=10.0, unit=mV), 'tau': Property(name=tau, value=20.0, unit=ms), 'R': Property(name=R, value=1.5, unit=Mohm), 'tau_rp': Property(name=tau_rp, value=2.0, unit=ms), 'theta': Property(name=theta, value=20.0, unit=mV)})
    >>> p_exc.cell.initial_values
    InitialValueSet({'t_rpend': Property(name=t_rpend, value=0.0, unit=ms), 'V': Property(name=V, value=0.0, unit=mV)})

Turning from a population to a projection:

.. code-block:: python

    >>> prj_inh = net.projections['Inhibition']
    >>> prj_inh.source
    Population(name='Inh', number=1000, cell=nrn)
    >>> prj_inh.destination
    Selection('All neurons', 'Concatenate(Reference(name="Exc"), Reference(name="Inh"))')
    >>> prj_inh.response
    BaseComponent(name="syn", componentclass="AlphaPSR")
    >>> prj_inh.connectivity
    BaseComponent(name="RandomInh", componentclass="RandomFanIn")
    >>> prj_inh.plasticity
    BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection")
    >>> prj_inh.delay
    Delay(value=1.5, unit=ms)
    >>> prj_inh.port_connections
    [PortConnection('plasticity', 'response', 'weight', 'q'),
     PortConnection('response', 'destination', 'Isyn', 'Isyn')]

Note that the :attr:`source` and :attr:`destination` attributes point to :class:`~nineml.user_layer.Population`\s or
:class:`~nineml.user_layer.Projection`\s, the :attr:`connectivity` rule, the post-synaptic :attr:`response` model and
the synaptic :attr:`plasticity` model are all :class:`~nineml.user_layer.Component`\s. The :attr:`port_connections`
attribute indicates which ports in the different components should be connected together.


Writing model descriptions in Python
====================================

Writing abstraction layer models
--------------------------------

.. todo:: implement here at least one neuron example and one synapse example. Izhikevich, adexp, NMDA. Ideally we should
          try a plasticity model as well, and a spike generator. Adapt tutorials/al/class_overview.rst and nineml_al_implementation_and_xml.rst


Writing user layer models
-------------------------

.. todo:: implement here a fairly simple network model.


Using NineML model descriptions for simulations
===============================================

.. todo:: links to PyDSTool, nineml2nmodl, PyNN, etc.

