
.. |NineML| replace:: NineML
.. |AbstractionLayer| replace:: Abstraction Layer

.. |ComponentClass| replace:: **ComponentClass**
.. |ComponentClasses| replace:: **ComponentClasses**


.. |Interface| replace:: **Interface**
.. |Dynamics| replace:: **Dynamics**

.. |StateVariable| replace:: **StateVariable**
.. |StateVariables| replace:: **StateVariables**

.. |Transition| replace:: **Transition**
.. |Transitions| replace:: **Transitions**

.. |Regime| replace:: **Regime**
.. |Regimes| replace:: **Regimes**


.. |Alias| replace:: **Alias**
.. |Aliases| replace:: **Aliases**

.. |TimeDerivative| replace:: **TimeDerivative**
.. |TimeDerivatives| replace:: **TimeDerivatives**

.. |StateAssignment| replace:: **StateAssignment**
.. |StateAssignments| replace:: **StateAssignments**


.. |OnCondition| replace:: **OnCondition**
.. |OnConditions| replace:: **OnConditions**

.. |OnEvent| replace:: **OnEvent**
.. |OnEvents| replace:: **OnEvents**
.. |EventPort| replace:: **EventPort**

.. |OutputEvent| replace:: **OutputEvent**
.. |OutputEvents| replace:: **OutputEvents**

.. |Event| replace:: **Event**
.. |Events| replace:: **Events**



============================================
The NineML Abstraction Layer & Object Model
============================================


Introduction
=============


NineML is an API designed for specifying the dynamics and connectivity of neural
simulations; in particular for large-scale simulations of many point neurons.
NineML is split into two levels; User Layer and Abstraction Layer.
Simplistically, the abstraction layer allows us to define the behaviour of 
*parameterised* components, while the user layer defines the instantiation of
these components in terms of parameters and interconnectivity.


The NineML abstraction is an evolving standard. There are currently three
implementations; in Python, Java (via LEMS/NEUROML??) and Chicken.

In this document we define the concepts common to the object models supported by
these three implementations. 


The Object Model
================


In the NineML Abstraction Layer; we define our model in terms of |ComponentClasses|. A |ComponentClass| could typically represent a point-neuron model or a synapse model for example. 


A |ComponentClass| is composed of its |Interface| and its |Dynamics|. 





Dynamics
--------

The Dynamics are the *internal* mechanisms governing the behaviour of the component. 
The dynamics of a component are specified in terms of the following:

* |StateVariables|
* A *RegimeGraph* composed of |Regimes| & |Transitions|
* |Aliases|





The *RegimeGraph* and StateVariables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The internal state of a component is defined by a set of |StateVariables|; variables that can
change either continuously or discontinuously as a function of time. 

The |Regimes| form the vertices and the |Transitions| form the directional edges of the *RegimeGraph*, which must have at least one |Regime|, and contain no regime-islands.  At any given time, a component will be in a single |Regime|, and can change which |Regime| it is in through |Transitions|.




A |Regime| contains a set of |TimeDerivatives|, one for each |StateVariable| of the |ComponentClass|, which define how the |StateVariables| evolve over time. 


The |StateVariable| changes happen in two ways:

    * continuously through |TimeDerivatives| (in |Regimes|), which define the |StateVariables|
      evolution over time, for example `dX/dt=1-X`

    * discretely through |StateAssignments| (in |Transitions|), which make discrete changes to a
      |StateVariable|'s value, for example `X = X + 1`





This diagram shows the dynamics block for an example component. 

.. image::
        al_figs/SimpleRegimeGraph.eps


This dynamics has 3 state variables, *X,Y & Z*, and a state graph with 3
regimes, *regime1*, *regime2* & *regime3*. At any time, a component will be in one of these regimes, and the state variables will evolve accordingly. 



Movement between |Regimes| happens via |Transitions|. There are 2 types of
Transitions:

* An |OnCondition| function of the |StateVariables|, for example `X>Y`.
* An |OnEvent| on an input |EventPort|. (Discussed further in XX).

During either type of transition; three things can happen:

* The component can change regime. For example, in the example above, if the
  component is in *regime3*, and the trigger for *t3* is satisfied, then the
  component will move into *regime1*.

* |StateAssignments| can take place, for example, `X=0`
* The component can send |OutputEvents|

During a transition, multiple |StateAssignments| and |OutputEvents| can occur.
(For more on the resolution of |Transitions|, see XX)




.. note::

    * If a |TimeDerivative| for a |StateVariable| is not defined in a |Regime|, it is 
      assumed to be zero.
    * A |Transition| does not need to lead to a change of |Regime|. It can cause
      |StateAssignments| and/or |OutputEvents|, and return to the original
      regime. (For example *t5* in the diagram)




Aliases
~~~~~~~~~~


|Aliases| are motivated from two problems;

* Rather than writing long expressions for functions of |StateVariables|, we can
  define an |Alias| once. 
  For example, we can define chains of |Aliases|::
    
    m_alpha = (alphaA + alphaB*V) / ( alphaC + exp((alphaD+V/alphaE)) )
    m_beta =  (betaA + betaB*V) / ( betaC + exp((betaD+V/betaE)) )
    minf = m_alpha / (m_alpha + m_beta)
    mtau = 1./(m_alpha+m_beta)
    dm/dt = (1/C) * (minf-m)/mtau

  In this case, *m_alpha*, *m_beta*, *minf* and *mtau* are all alias
  definitions. There is no reason we couldn't expand our `dm/dt`
  description out to eliminate these intermediate |Aliases|, but the expression
  would be very long and difficult to read.

* If we would like to communicate a value other than a simple |StateVariable| to
  to another |ComponentClass|. For example, if we have a component representing a
  neuron, which has an internal |StateVariable|, 'V', we may be interested in
  transmitting a current, for example `i=g*(E-V)`.

.. note:: 
    
    Aliases are defined in the Dynamics, *not* in the Regime. This means that
    aliases are the same across all regimes.




Events
~~~~~~

As well as being able to communicate continuous values, components are also able
to emit and receive |Events|. Events are discrete notifications that are transmitted 
over EventPorts. Since EventPorts have names, saying
that we transmit  'event1' for example would mean transmitting an event on
the EventPort called 'event1'. Events can be used to signal action
potentials firing for example. 











Interface
---------

The interface is the *external* view of the component; what inputs and outputs the component exposes
to other components and the parameters that can be set for the component.

The interface consists of *Ports* and *Parameters*.


Parameters
~~~~~~~~~~~~

Parameters allow us to define the dynamics of a component once, then adjust the
behaviours by using different parameters. For example, if we are building an
integrate-and-fire neuron, we can specify that the Reset-Voltage and the
Firing-Threshold are parameters, write our dynamics in terms of these
parameters, then use the *User Layer* to provide parameters to create different
neurons. Parameters are set at the start of the simulation, and remain constant
throughout.


Ports
~~~~~

Ports allow components to communicate between each other during a simulation. 
There are 2 types, *AnalogPorts* and *EventPorts*, and each can have
different modes.

AnalogPorts
^^^^^^^^^^^

AnalogPorts transmit and receive continuous values, either  |Aliases| and
|StateVariables|. AnalogPorts can have 3 modes:

    * ``SendPort`` - transmit data originating in this component which can be read by
      other components.

    * ``RecvPort`` - receive data from another components ``SendPort`` port.
      Each ``RecvPort`` can be connected to *one* ``SendPort``.

    * ``ReducePort`` - receive data from multiple ``SendPort`` . These
      differ from ``RecvPorts`` in that they can be connected to multiple
      ``SendPort`` . ``ReducePorts`` take an additional operator,
      ``reduce_op``, which specifies how the data from multiple ``Send``
      ports should be combined to produce a single value. Currently, the
      only supported operations is `+`, which sums the inputs. The
      motivation for ``ReducePorts`` is that it allows us to make our
      component definitions more general. For example, if we are defining a
      neuron, would define a ``ReducePort`` called, ``InjectedCurrents``.
      This allows us to write the membrane equation for that neuron as 
      `dV/dt = (1/C) * InjectedCurrents`
      
      Then, when we connect this neuron to synapses, current-clamps, etc, we
      simply need to connect the SendPorts containing the currents of these components onto
      the ``InjectedCurrents`` reduce-port, within having to change our
      original component definitions.
        

EventPorts
^^^^^^^^^^

Event ports transmit discrete events. They are useful for example in
simulation of integrate-and-fire neurons to notify components about neuron's
spiking. Event ports only have 2 modes:

    * ``SendPort`` - transmit events originating in this component which can be read by
      other components
    * ``RecvPort`` - receive events from another components ``SendPort`` port.
      Each recv port can be connected to *multiple* ``SendPort``.

For example, a synapse component may have a ``RecvPort`` connected to the
presynaptic neurons ``SendPort`` port. When the presynaptic neuron fires;
it delivers an event to the synapse, which could cause it to produce current
flow in a post-synaptic neuron. 






.. raw:: pdf

    PageBreak








NineML Abstraction Layer as XML
===============================


Tag Descriptions
----------------



<NineML>
~~~~~~~~~



    <NineML>

This is the root namespace tag for a NineML file. It can contain
`<ComponentClass>` elements.


todo:
    
    XML namespaces -XX





<ComponentClass>
~~~~~~~~~~~~~~~~


    <ComponentClass name="">

This tag starts an abstraction layer component definition. 

Attributes:

* name [Required]

Child Elements:

* <Parameter> [0+]
* <AnalogPort>[0+]
* <EventPort> [0+]
* <Dynamics>  [1]
  






<Parameter>
~~~~~~~~~~~

    
    <Parameter name="" dimension="">

This tag specifies a parameter in the interface of the component

Attributes:

* name [Required]
* dimension [Required]

Child Elements: ``None``






<AnalogPort>
~~~~~~~~~~~~
    
    
    <AnalogPort name="" mode="" reduce_op="" dimension="" >

This tag specifies an AnalogPort in the interface of the component

Attributes:

* name [Required]
* mode [Required: 'send','recv' or 'reduce']
* reduce_op [Required if mode=='reduce']
* dimension [Required]

Child Elements: ``None``






<EventPort>
~~~~~~~~~~~

    
    <EventPort name="" mode="">

This tag specifies an EventPort in the interface of the component

Attributes:

* name [Required]
* mode [Required: 'send','recv']
* dimension [Required]

Child Elements: ``None``




<Dynamics>
~~~~~~~~~~

    
    <Dynamics>

This tag specifies the dynamics of the component

Attributes: ``None``

Child Elements: 

* <StateVariable> [0+]
* <Alias> [0+]
* <Regime> [1+]





<StateVariable>
~~~~~~~~~~~~~~~

    
    <StateVariable name='' dimension=''>

This tag declares a state-variable in the component

Attributes: 

* name [Required] (The variable name)
* dimension [Required] 

Child Elements: ``None``



<Alias>
~~~~~~~

    
    <Alias name=''>

This tag declares an alias in the component

Attributes: 

* name [Required] (The alias name)
* dimension [Required] 

Child Elements: 

* <MathInline> [Required] (The equation on the right-hand-side of the alias)





<Regime>
~~~~~~~~

    
    <Regime>

This tag declares an regime in the component. There must be exactly on
TimeDerivative block for each StateVariable block declared in the enclosing
<Dynamics> block, even if it has a RHS of zero.

Attributes: 

* name [Required] (The regime name)

Child Elements: 

* <TimeDerivative> [0+] 
* <OnCondition> [0+] (The transitions from this regime, triggered by conditions)
* <OnEvent> [0+] (The transitions from this regime, triggered by events)



<TimeDerivative>
~~~~~~~~~~~~~~~~

    
    <TimeDerivative>

This tag defines the differential equation controlling the evolution of a StateVariable while
in this regime.

Attributes: 

* variable [Required] (The name of the state variable)

Child Elements: 

* <MathInline> [1] (The right-hand-side of the differential equation)



<OnCondition>
~~~~~~~~~~~~~


    <OnCondition>

This block specifies a transition from the enclosing Regime, which is triggered
by a mathematical function of the Component's Aliases, StateVariables, Ports and
Parameters.

Attributes: ``None``


Child Elements: 

* <Trigger> [1] (A <Trigger> block defining the condition that causes this
      transition to occur)
* <StateAssignment> [0+] (The state assignments that should occur when this
  transition is triggered)
* <EventOut> [0+] (The events that should be sent when this transition is triggered)

<OnEvent>
~~~~~~~~~~


    <OnEvent>

This block specifies a transition from the enclosing Regime, which is triggered
by an input event.

Attributes: 

* port [Required] The name of the input event port which triggers this
  transition


Child Elements: 

* <StateAssignment> [0+] (The state assignments that should occur when this
  transition is triggered)
* <EventOut> [0+] (The events that should be sent when this transition is triggered)



<Trigger>
~~~~~~~~~~


    <Trigger>

This block is used by <OnCondition> blocks to define the condition needed for
them to be triggered.


Attributes: ``None``


Child Elements: 

* <MathInline> [1] (A mathematical expression. This should evaluate to a
  boolean, for example by invoking a comparison operator  `('>', '<')` )


<StateAssignment>
~~~~~~~~~~~~~~~~~


    <StateAssignment>

Used in transitions to assign a value to a state-variable during a transition. 

.. note::

    'In-place' operations are not supported and should be written out as in full: `x+=z \rightarrow x=x+z`


Attributes: 

* variable [Required] (The name of the variable to be assigned to)


Child Elements: 

* <MathInline> [1] (The right-hand-side of the assignment expression)


<EventOut>
~~~~~~~~~~


    <EventOut>

Used in transitions to emit an event.

Attributes: 

* port_name [Required] (The name of the EventPort to send an event over)


Child Elements: ``None``



<MathInline>
~~~~~~~~~~~~
::

    <MathInline>

A block used to specify mathematical expressions. The expression is expected to
be in ``C`` style and given as text. In future versions of NineML, we will
support <MathML> blocks too.



Attributes:  ``None``

Child Elements: ``None``


.. raw:: pdf

    PageBreak



Example XML
-----------


An example model of an Izhikevich model is given:
::

    <?xml version='1.0' encoding='UTF-8'?>
    <NineML xmlns="http://nineml.org/9ML/0.1"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://nineml.org/9ML/0.1 NineML_v0.2.xsd">

      <ComponentClass name="izhikevichCellNew">

        <Parameter name="a" dimension='none'/>
        <Parameter name="c" dimension='none'/>
        <Parameter name="b" dimension='none'/>
        <Parameter name="d" dimension='none'/>
        <Parameter name="theta" dimension='voltage'/>

        <AnalogPort name="iSyn" mode='reduce' reduce_op='+' dimension='current'/>
        <AnalogPort name="U" mode="send" dimension='none'/>
        <AnalogPort name="V" mode="send" dimension='voltage'/>
        <EventPort name="spikeOutput" mode="send"/>
        

        <Dynamics>
            
            <StateVariable name="V" dimension="voltage"/>
            <StateVariable name="U" dimension="none"/> 
              
            <Alias name='rv' dimension='none'>
                <MathInline>V*U</MathInline>
            </Alias>

            <Regime name="subthresholdRegime">
                  
              <TimeDerivative variable="U">
                <MathInline>a*(b*V - U)</MathInline>
              </TimeDerivative>

              <TimeDerivative variable="V">
                <MathInline>0.04*V*V + 5*V + 140.0 - U + iSyn</MathInline>
              </TimeDerivative>

              
              <OnCondition>
                <Trigger>
                  <MathInline>V &gt; theta </MathInline>
                </Trigger>

                <StateAssignment variable="V" >
                  <MathInline>c</MathInline>
                </StateAssignment>
                
                <StateAssignment variable="U" >
                  <MathInline>U+d</MathInline>
                </StateAssignment>
                
                <EventOut port="spikeOutput" />
                
              </OnCondition>

            </Regime>
        </Dynamics>

      </ComponentClass>
    </NineML>





.. raw:: pdf

    PageBreak






















