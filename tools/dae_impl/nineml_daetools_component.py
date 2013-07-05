#!/usr/bin/env python
"""
.. module:: nineml_daetools_component.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import nineml
import math
import numpy.random
import expression_parser
import units_parser
from daetools.pyDAE import daeVariableTypes, pyCore, pyUnits

"""
ACHTUNG, ACHTUNG!!
How should the global seed be initialized? 
If it is None then numpy gets it from the OS.
"""
_global_seed_ = None
_global_rng_  = numpy.random.RandomState()
_global_rng_.seed(_global_seed_)

def fixVariableTypeName(s): 
    s = s.replace(' ', '')
    s = s.replace('^', '')
    s = s.replace('-', '_')
    return s

class daetoolsRNG(object):
    """
    """
    
    uniform     = 0
    normal      = 1
    binomial    = 2
    poisson     = 3
    exponential = 4
    
    def __init__(self, distribution, **kwargs):
        self.distribution = distribution
        self.rng          = numpy.random.RandomState()
        self.seed         = kwargs.get('seed', None)
        if self.seed:
            self.rng.seed(self.seed)
        
        if self.distribution == daetoolsRNG.uniform:
            self.lowerBound = kwargs.get('lowerBound')
            self.upperBound = kwargs.get('upperBound')
        
        elif self.distribution == daetoolsRNG.normal:
            self.centre = kwargs.get('centre')
            self.width  = kwargs.get('width')
        
        elif self.distribution == daetoolsRNG.binomial:
            self.n = kwargs.get('n')
            self.p = kwargs.get('p')
        
        elif self.distribution == daetoolsRNG.poisson:
            self.lamb = kwargs.get('lamb')
        
        elif self.distribution == daetoolsRNG.exponential:
            self.beta = kwargs.get('beta')
        
        else:
            raise RuntimeError('Unsupported random distribution: {0}'.format(str(distribution)))
   
    def next(self):
        res = [0.0]
        if self.distribution == daetoolsRNG.uniform:
            res = self.rng.uniform(self.lowerBound, self.upperBound, 1)
        
        elif self.distribution == daetoolsRNG.normal:
            res = self.rng.normal(self.centre, self.width)
        
        elif self.distribution == daetoolsRNG.binomial:
            res = self.rng.binomial(self.n, self.p)
        
        elif self.distribution == daetoolsRNG.poisson:
            res = self.rng.poisson(self.lamb)
        
        elif self.distribution == daetoolsRNG.exponential:
            res = self.rng.exponential(self.beta)
        
        return float(res[0])
        
    @classmethod
    def createRNG(cls, al_component, parameters):
        """
        Creates numpy RNG based on the AL Component object and parameters from the UL component. 
        
        ACHTUNG, ACHTUNG!!
        Perhaps, the component names should be standardized to some convention?
        
        :param cls: daetoolsRNG class
        :param al_component: AL Component object
        :param parameters: python dictionary 'name' : (value, units)
        
        :rtype: daetoolsRNG object
        :raises: RuntimeError
        """
        seed = _global_seed_
        
        if al_component.name == 'uniform_distribution':
            lowerBound = parameters['lowerBound'][0]
            upperBound = parameters['upperBound'][0]
            rng = daetoolsRNG(daetoolsRNG.uniform, lowerBound = lowerBound, upperBound = upperBound, seed = seed)
        
        elif al_component.name == 'normal_distribution':
            centre = parameters['centre'][0]
            width  = parameters['width'][0]
            rng = daetoolsRNG(daetoolsRNG.normal, centre = centre, width = width, seed = seed)
        
        elif al_component.name == 'binomial_distribution':
            n = parameters['n'][0]
            p = parameters['p'][0]
            rng = daetoolsRNG(daetoolsRNG.binomial, n = n, p = p, seed = seed)
        
        elif al_component.name == 'poisson_distribution':
            lamb = parameters['lamb'][0]
            rng = daetoolsRNG(daetoolsRNG.poisson, lamb = lamb, seed = seed)
        
        elif al_component.name == 'exponential_distribution':
            beta = parameters['beta'][0]
            rng = daetoolsRNG(daetoolsRNG.exponential, beta = beta, seed = seed)
        
        else:
            raise RuntimeError('Unsupported random distribution component: {0}'.format(al_component.name))

        return rng

def random_uniform(lowerBound = 0.0, upperBound = 1.0):
    res = _global_rng_.uniform(lowerBound, upperBound, 1)
    return float(res[0])

def random_normal(centre = 0.0, width = 1.0):
    res = _global_rng_.normal(centre, width)
    return float(res)

def random_binomial(n, p):
    res = _global_rng_.binomial(n, p)
    return float(res)

def random_poisson(lam = 1.0):
    res = _global_rng_.poisson(lam)
    return float(res)

def random_exponential(beta = 1.0):
    res = _global_rng_.exponential(beta)
    return float(res)

def fixObjectName(name):
    """
    Replaces spaces in the 'name' string with underscores and returns the modified string.
    
    :param name: string
        
    :rtype: string
    :raises:
    """
    return name.replace(' ', '_')

dae_nineml_t = pyCore.daeVariableType("dae_nineml_t", pyUnits.unit(), -1.0e+20, 1.0e+20, 0.0, 1e-12)
_used_variable_types_ = {}

class daetoolsSpikeSource(pyCore.daeModel):
    """
    Used to generate spikes according to the predefined sequence.
    The component has no parameters, just a dummy variable *event* and 
    corresponding equation in the STN.
    """
    def __init__(self, spiketimes, Name, Parent = None, Description = ""):
        pyCore.daeModel.__init__(self, Name, Parent, Description)

        self.on_spike_out_action  = None
        self.target_synapses      = []    
        self.incoming_synapses    = []    
        self.events_heap          = None 
        self.incoming_synapses    = []
        self.Nitems               = 0

        # A dummy variable
        self.event = pyCore.daeVariable("event", daeVariableTypes.time_t, self, "")
        
        # Add one 'send' event port
        self.spikeoutput = pyCore.daeEventPort("spikeoutput", pyCore.eOutletPort, self, "Spike outlet event port")
        
        # A list of spike event times (pyUnits.quantity objects)
        self.spiketimes = list(spiketimes)

    def initialize(self):
        pass
    
    #@property
    #def initialEvents(self):
    #    return self.spiketimes
    
    def CleanUpSetupData(self):
        pass
    
    def DeclareEquations(self):
        self.stnSpikeSource = self.STN("SpikeSource")

        for i, t in enumerate(self.spiketimes):
            self.STATE('State_{0}'.format(i))
            eq = self.CreateEquation("event")
            eq.Residual = self.event() - pyCore.Constant(t)
            self.ON_CONDITION(pyCore.Time() >= pyCore.Constant(t), switchTo      = 'State_{0}'.format(i+1),
                                                                   triggerEvents = [(self.spikeoutput, pyCore.Time())])

        self.STATE('State_{0}'.format(len(self.spiketimes)))

        eq = self.CreateEquation("event")
        eq.Residual = self.event()

        self.END_STN()
        
    def getOutletEventPort(self): 
        return self.spikeoutput

class daetoolsVariableParameterDictionaryWrapper(object):
    """
    Dictionary-like class to wrap multidimensional parameters, variables, etc.
    A workaround to save a lot of time that would be spent on creating dictionaries
    for each neurone/connection.
    """
    def __init__(self, dictIDs, current_index = None):
        """
        :param dictIDs: python dictionary 'name' : daeVariable/daeParameter; 
                        they should be distributed on a single domain.
        :param current_index: daeDEDI object
        """
        self.dictIDs       = dictIDs
        self.current_index = current_index
        
    def __contains__(self, key):
        return key in self.dictIDs

    def has_key(self, key):
        return key in self.dictIDs

    def __getitem__(self, key):
        """
        Gets the daeVariable object at the given *key* and calls *operator ()*
        with the index equal to the *current_index* argument.
        """
        obj = self.dictIDs[key]
        if isinstance(obj, pyCore.adouble):
            return obj
        
        elif isinstance(obj, (pyCore.daeParameter, pyCore.daeVariable)):
            if self.current_index == None:
                if len(obj.Domains) > 0:
                    raise RuntimeError('')
                return obj()
            
            else:
                if len(obj.Domains) > 0:
                    return obj(self.current_index)
                else:
                    raise RuntimeError('')
        else:
            raise RuntimeError('')

"""
daetools do not support a concept of separate dimensions and units in equations;
equations are built of objects which represent quantities (numerical value + units).
Therefore, here we emulate dimensions by using base SI units (m, kg, s, A, K, cd, mol).
Also, we add empty string to support dimensionless quantities.
"""
_dictDimensions = {
                    'L' : pyUnits.m,
                    'M' : pyUnits.kg,
                    'T' : pyUnits.s,
                    'I' : pyUnits.A,
                    'O' : pyUnits.K,
                    'J' : pyUnits.cd,
                    'N' : pyUnits.mol,
                    ''  : pyUnits.unit() # Non-dimensional 
                  }
"""
daetools define a large number of units:
 - all base and derived SI units
 - All of these with prefixes tera(T), giga(G), mega(M), kilo(k), hecto(h), deka(da),
   deci(d), centi(c), mili(m), micro(u), nano(n), pico(p)
All are imported into the pyUnits module. Here we filter those symbols and add them
to the dictionary that will be used to evaluate the AST after the parsing phase.
"""
_dictUnits = {
               ''  : pyUnits.unit() # Non-dimensional
             }
for attr in dir(pyUnits):
    obj = getattr(pyUnits, attr)
    if isinstance(obj, pyUnits.unit):
        _dictUnits[attr] = obj
#print _dictDimensions
#print _dictUnits

_equation_parser_   = expression_parser.ExpressionParser()
_dimensions_parser_ = units_parser.UnitsParser(_dictDimensions)
_units_parser_      = units_parser.UnitsParser(_dictUnits)

def parseUnits(units):
    return _units_parser_.parse_and_evaluate(units)

def createPoissonSpikeTimes(rate, duration, t0, rng_poisson, lambda_, rng):
    """
    :param rate: rate in Hz
    :param duration: duration in s
    :param t0: start time in s
    :param lambda_: lambda (dimensionless)
    :param rng: numpy RandomState object

    :rtype: list of pyUnits.quantity objects
    """
    n  = int(rng.poisson(lambda_, 1))
    spiketimes = rng.uniform(t0.value, t0.value + duration.value, n)
    return [time * pyUnits.s for time in sorted(spiketimes)]

class daetoolsComponentInfo(object):
    """
    """
    def __init__(self, name, al_component):
        """
        Iterates over *Parameters*, *State variables*, *Aliases*, *Analogue ports*, *Event ports*, 
        *Sub-nodes* and *Port connections* and creates data structures needed to repeadetly create
        daetools models (daetoolsComponent objects).
        
        :param name: string
        :param al_component: AL component object
            
        :raises: RuntimeError
        """
        self.name                    = name
        self.al_component            = al_component
        self.nineml_parameters       = []
        self.nineml_state_variables  = []
        self.nineml_aliases          = []
        self.nineml_analog_ports     = []
        self.nineml_reduce_ports     = []
        self.nineml_event_ports      = []
        self.nineml_port_connections = []
        self.nineml_regimes          = []
        self.nineml_subcomponents    = []
        
        # AL component may be None (useful in certain cases); therefore do not raise an exception
        if not self.al_component:
            return
        
        # 1) Create parameters
        for param in self.al_component.parameters:
            units = _dimensions_parser_.parse_and_evaluate(param.dimension)
            print('Parameter: {0}, dimensions: {1}'.format(param.name, param.dimension))
            print('   Parse result:   {0}'.format(_dimensions_parser_.parseResult))
            print('   daetools units: {0}'.format(units))

            self.nineml_parameters.append( (param.name, units) )

        # 2) Create state-variables (diff. variables)
        for var in self.al_component.state_variables:
            units = _dimensions_parser_.parse_and_evaluate(var.dimension)
            print('Variable: {0}, dimensions: {1}'.format(var.name, var.dimension))
            print('   Parse result:   {0}'.format(_dimensions_parser_.parseResult))
            print('   daetools units: {0}'.format(units))
            
            var_type_name = fixVariableTypeName(var.dimension)
            print('   var_type_name:  {0}'.format(var_type_name))
            var_type = pyCore.daeVariableType(var_type_name, units, -1.0e+20, 1.0e+20, 0.0, 1e-12)
            
            self.nineml_state_variables.append( (var.name, var_type) )

        # 3) Create alias variables (algebraic) and parse rhs
        for alias in self.al_component.aliases:
            self.nineml_aliases.append( (alias.lhs, dae_nineml_t, _equation_parser_.parse(alias.rhs)) )

        # 4) Create analog-ports and reduce-ports
        for analog_port in self.al_component.analog_ports:
            if analog_port.mode == 'send':
                self.nineml_analog_ports.append( (analog_port.name, pyCore.eOutletPort, dae_nineml_t) )
            elif analog_port.mode == 'recv':
                self.nineml_analog_ports.append( (analog_port.name, pyCore.eInletPort, dae_nineml_t) )
            elif analog_port.mode == 'reduce':
                self.nineml_reduce_ports.append( (analog_port.name, pyCore.eInletPort, dae_nineml_t) )
            else:
                raise RuntimeError("")

        # 5) Create event-ports
        for event_port in self.al_component.event_ports:
            if event_port.mode == 'send':
                self.nineml_event_ports.append( (event_port.name, pyCore.eOutletPort) )
            elif event_port.mode == 'recv':
                self.nineml_event_ports.append( (event_port.name, pyCore.eInletPort) )
            else:
                raise RuntimeError("")

        # 6) Create port connections
        for port_connection in self.al_component.portconnections:
            portFrom = '.'.join(port_connection[0].loctuple)
            portTo   = '.'.join(port_connection[1].loctuple)
            self.nineml_port_connections.append( (portFrom, portTo) )
        
        # 7) Create regimes
        regimes         = list(self.al_component.regimes)
        state_variables = list(self.al_component.state_variables)
        if len(regimes) > 0:
            for regime in regimes:
                odes          = []
                on_conditions = []
                on_events     = []

                # 7a) Sometime a time_derivative equation is not given and in that case a 
                # derivative is equal to zero. We have to discover which variables do not 
                # have a corresponding ODE and we do that by creating a map {'state_var' : 'RHS'} 
                # which initially has set rhs to '0'. RHS will be set later while iterating through ODEs
                map_statevars_timederivs = {}
                for state_var in state_variables:
                    map_statevars_timederivs[state_var.name] = '0'

                time_derivatives = list(regime.time_derivatives)
                for time_deriv in time_derivatives:
                    map_statevars_timederivs[time_deriv.dependent_variable] = time_deriv.rhs

                for var_name, rhs in list(map_statevars_timederivs.items()):
                    odes.append( (var_name, _equation_parser_.parse(rhs)) )
                        
                # 2d) Create on_condition actions
                for on_condition in regime.on_conditions:
                    condition         = _equation_parser_.parse(on_condition.trigger.rhs)
                    switchTo          = on_condition.target_regime.name
                    triggerEvents     = []
                    setVariableValues = []

                    for state_assignment in on_condition.state_assignments:
                        setVariableValues.append( (state_assignment.lhs, _equation_parser_.parse(state_assignment.rhs)) )

                    for event_output in on_condition.event_outputs:
                        triggerEvents.append( (event_output.port_name, 0) )

                    on_conditions.append( (condition, switchTo, setVariableValues, triggerEvents) )
                
                # 2e) Create on_event actions
                for on_event in regime.on_events:
                    source_event_port = on_event.src_port_name                    
                    switchToStates    = []
                    triggerEvents     = []
                    setVariableValues = []

                    for state_assignment in on_event.state_assignments:
                        setVariableValues.append( (state_assignment.lhs, _equation_parser_.parse(state_assignment.rhs)) )

                    for event_output in on_event.event_outputs:
                        triggerEvents.append( (event_output.port_name, 0) )

                    on_events.append( (source_event_port, switchToStates, setVariableValues, triggerEvents) )
                
                self.nineml_regimes.append( (regime.name, odes, on_conditions, on_events) )

        # 8) Create sub-nodes
        for name, subcomponent in list(self.al_component.subnodes.items()):
            self.nineml_subcomponents.append( daetoolsComponentInfo(name, subcomponent) )

    def __str__(self):
        res = ''
        res += 'name = {0}\n'.format(self.name)
        res += 'al_component = {0}\n'.format(self.al_component)
        res += 'nineml_parameters = {0}\n'.format(self.nineml_parameters)
        res += 'nineml_state_variables = {0}\n'.format(self.nineml_state_variables)
        res += 'nineml_aliases = {0}\n'.format(self.nineml_aliases)
        res += 'nineml_analog_ports = {0}\n'.format(self.nineml_analog_ports)
        res += 'nineml_reduce_ports = {0}\n'.format(self.nineml_reduce_ports)
        res += 'nineml_event_ports = {0}\n'.format(self.nineml_event_ports)
        res += 'nineml_port_connections = {0}\n'.format(self.nineml_port_connections)
        res += 'nineml_regimes = {0}\n'.format(self.nineml_regimes)
        for subcomponent in self.nineml_subcomponents:
            res += 'Subcomponent: {0}\n{1}\n'.format(subcomponent.name, subcomponent)
        return res
    
class daetoolsComponent(pyCore.daeModel):
    ninemlSTNRegimesName = 'NineML_Regimes_STN'
    
    def __init__(self, info, Name, Parent = None, Description = ''):
        pyCore.daeModel.__init__(self, Name, Parent, Description)
        
        self.info                           = info
        self.Nitems                         = 0
        self.N                              = None
        self.nineml_parameters              = {}
        self.nineml_aliases                 = {}
        self.nineml_variables               = {}
        self.nineml_inlet_ports             = {}
        self.nineml_outlet_ports            = {}
        self.nineml_reduce_ports            = {}
        self.nineml_inlet_event_ports       = {}
        self.nineml_outlet_event_ports      = {}
        self.nineml_port_connections        = []
        self.nineml_reduce_port_connections = {}
        self.nineml_subcomponents           = []
        self.nineml_equations               = {}
        self.nineml_stns                    = []
        
        self.on_spike_out_action            = None
        self.target_synapses                = []    
        self.incoming_synapses              = []    
        self.synapse_weights                = []
        self.synapse_weight_units           = None
        self.events_heap                    = None 
        self.simulation                     = None

    def CleanUpSetupData(self):
        return
        
        del self.info
        del self.nineml_parameters
        """
        Cannot delete the following;
        del self.nineml_aliases
        del self.nineml_variables
        del self.nineml_inlet_ports
        del self.nineml_reduce_ports
        """
        del self.nineml_outlet_ports
        del self.nineml_port_connections
        del self.nineml_reduce_port_connections
        del self.nineml_equations
        del self.nineml_stns
        
        """
        Cannot delete the following;
        del self.nineml_inlet_event_ports
        del self.nineml_outlet_event_ports
        del self.nineml_subcomponents
        """
        
        for nineml_subcomponent in self.nineml_subcomponents:
            nineml_subcomponent.CleanUpSetupData()
        
        for (synapse, synapse_parameters) in self.incoming_synapses:
            synapse.CleanUpSetupData()

    def initialize(self, domainN = None):
        # If the number of items is zero then the component will not have any parameters,
        # variables, aliases nor equations.
        if self.Nitems == 0:
            return
        
        if domainN:
            self.N = domainN
        else:
            self.N = pyCore.daeDomain("N", self, pyUnits.unit(), "N domain")
        domains = [self.N]
        
        # 1) Create parameters
        for (name, units) in self.info.nineml_parameters:
            self.nineml_parameters[name] = pyCore.daeParameter(name, units, self, "", domains)

        # 2) Create state-variables (diff. variables)
        for (name, var_type) in self.info.nineml_state_variables:
            self.nineml_variables[name] = pyCore.daeVariable(name, var_type, self, "", domains)

        # 3) Create alias variables (algebraic)
        for (name, var_type, node) in self.info.nineml_aliases:
            self.nineml_aliases[name] = ( pyCore.daeVariable(name, var_type, self, "", domains), node )

        # 4a) Create analog-ports
        for (name, port_type, var_type) in self.info.nineml_analog_ports:
            if port_type == pyCore.eInletPort:
                self.nineml_inlet_ports[name] = pyCore.daeVariable(name, var_type, self, "", domains)
            else:
                if name in self.nineml_variables:
                    self.nineml_outlet_ports[name] = self.nineml_variables[name]
                elif name in self.nineml_aliases:
                    self.nineml_outlet_ports[name] = self.nineml_aliases[name][0]
                else:
                    raise RuntimeError("")
        
        # 4b) Create reduce-ports
        for (name, port_type, var_type) in self.info.nineml_reduce_ports:
            self.nineml_reduce_ports[name] = pyCore.daeVariable(name, var_type, self, "", domains)

        # 5) Create event-ports
        for (name, port_type) in self.info.nineml_event_ports:
            if port_type == pyCore.eInletPort:
                self.nineml_inlet_event_ports[name]  = [ pyCore.daeEventPort('{0}({1})'.format(name, i), port_type, self, "") for i in range(0, self.Nitems) ]
                    
            else:
                self.nineml_outlet_event_ports[name] = [ pyCore.daeEventPort('{0}({1})'.format(name, i), port_type, self, "") for i in range(0, self.Nitems) ]
                
        # 6) Create sub-components
        for sub_info in self.info.nineml_subcomponents:
            subcomponent = daetoolsComponent(sub_info, sub_info.name, self, '')
            subcomponent.Nitems = self.Nitems
            subcomponent.initialize(self.N)
            self.nineml_subcomponents.append(subcomponent)

        # 7) Create port connections
        inlet_ports  = self._getInletPorts(self)
        outlet_ports = self._getOutletPorts(self)
        reduce_ports = self._getReducePorts(self)
        
        # portFrom is always send, portTo is always receive/reduce
        for (nameFrom, nameTo) in self.info.nineml_port_connections:
            if (nameFrom in inlet_ports) and (nameTo in outlet_ports):
                portFrom = outlet_ports[nameTo]
                portTo   = inlet_ports [nameFrom]
                self.nineml_port_connections.append( (portFrom, portTo) )
            
            elif (nameFrom in outlet_ports) and (nameTo in inlet_ports):
                portFrom = outlet_ports[nameFrom]
                portTo   = inlet_ports [nameTo]
                self.nineml_port_connections.append( (portFrom, portTo) )

            elif (nameFrom in outlet_ports) and (nameTo in reduce_ports):
                portFrom = outlet_ports[nameFrom]
                portTo   = reduce_ports[nameTo]
                if nameTo in self.nineml_reduce_port_connections:
                    self.nineml_reduce_port_connections[nameTo][1].append(portFrom)
                else:
                    self.nineml_reduce_port_connections[nameTo] = (portTo, [portFrom])
            
            elif (nameFrom in reduce_ports) and (nameTo in outlet_ports):
                portFrom = outlet_ports[nameTo]
                portTo   = reduce_ports[nameFrom]
                if nameTo in self.nineml_reduce_port_connections:
                    self.nineml_reduce_port_connections[nameFrom][1].append(portFrom)
                else:
                    self.nineml_reduce_port_connections[nameFrom] = (portTo, [portFrom])

            else:
                raise RuntimeError('Cannot connect analogue ports {0} and {1}'.format(nameFrom, nameTo))
    
    #@property
    #def initialEvents(self):
    #    return []
    
    def __str__(self):
        res = ''
        res += 'canonical_name = {0}\n'.format(self.CanonicalName)
        res += 'nineml_parameters = {0}\n'.format(self.nineml_parameters)
        res += 'nineml_variables = {0}\n'.format(self.nineml_variables)
        res += 'nineml_aliases = {0}\n'.format(self.nineml_aliases)
        res += 'nineml_inlet_ports = {0}\n'.format(self.nineml_inlet_ports)
        res += 'nineml_outlet_ports = {0}\n'.format(self.nineml_outlet_ports)
        res += 'nineml_reduce_ports = {0}\n'.format(self.nineml_reduce_ports)
        res += 'nineml_inlet_event_ports = {0}\n'.format(self.nineml_inlet_event_ports)
        res += 'nineml_outlet_event_ports = {0}\n'.format(self.nineml_outlet_event_ports)
        res += 'nineml_port_connections = {0}\n'.format(self.nineml_port_connections)
        res += 'nineml_equations = {0}\n'.format(self.nineml_equations)
        res += 'nineml_stns = {0}\n'.format(self.nineml_stns)
        for sub_comp in self.nineml_subcomponents:
            res += str(sub_comp)
        return res
    
    def connectAnaloguePorts(self, source, target):
        """
        Establishes connections via simple send/receive analogue ports.
        It adds new items into the *nineml_port_connections* and 
        *nineml_reduce_port_connections* dictionaries. The corresponding 
        equations will be created during a call to *DeclareEquations* function.
        The created equations will be a part of the *self* daetoolsComponent.
        
        :param source: daetoolsComponent object (representing a synapse)
        :param target: daetoolsComponent object (representing a neurone) 
        
        :raises: RuntimeError
        """
        if source.Nitems == 0:
            # Raise an exception if there is any receive port in the target
            if len(target.nineml_inlet_ports) > 0:
                raise RuntimeError('Illegal connection: The target component ({0}) does not have any connections but declares receive ports'.format(target.CanonicalName))
            
            # Seal all the reduce ports in the target component
            for (target_variable_name, target_variable) in target.nineml_reduce_ports.iteritems():
                if not target_variable_name in self.nineml_reduce_port_connections:
                    self.nineml_reduce_port_connections[target_variable_name] = (target_variable, [])            
        
        for (source_variable_name, source_variable) in source.nineml_outlet_ports.iteritems():
            matching_port_found = False
            
            # 1) Look in the list of inlet ports
            for (target_variable_name, target_variable) in target.nineml_inlet_ports.iteritems():
                if source_variable_name == target_variable_name:
                    self.nineml_port_connections.append( (source_variable, target_variable) )
                    matching_port_found = True
                    break
            
            # 2) If not connected yet, look in the list of reduce ports
            if matching_port_found == False:
                for (target_variable_name, target_variable) in target.nineml_reduce_ports.iteritems():
                    if source_variable_name == target_variable_name:
                        if target_variable_name in self.nineml_reduce_port_connections:
                            self.nineml_reduce_port_connections[target_variable_name][1].append(source_variable)
                        else:
                            self.nineml_reduce_port_connections[target_variable_name] = (target_variable, [source_variable])
                        matching_port_found = True
                        break
            
            # If not found - die miserably
            if matching_port_found == False:
                raise RuntimeError('Cannot connect analogue ports: cannot find a match for the source port [{0}]'.format(source_variable_name))

        for (source_variable_name, source_variable) in source.nineml_inlet_ports.iteritems():
            matching_port_found = False
            
            # 1) Look in the list of outlet ports
            for (target_variable_name, target_variable) in target.nineml_outlet_ports.iteritems():
                if source_variable_name == target_variable_name:
                    self.nineml_port_connections.append( (source_variable, target_variable) )
                    matching_port_found = True
            
            # If not found - die miserably
            if matching_port_found == False:
                raise RuntimeError('Cannot connect analogue ports: cannot find a match for the source port [{0}]'.format(source_variable_name))

    def getInletEventPort(self, index):
        if len(self.nineml_inlet_event_ports) != 1:
            raise RuntimeError('{0} does not have any receive event ports'.format(self.CanonicalName))
        if index >= self.Nitems:
            raise RuntimeError('Receive event port out of bounds in {0} (size:{1}, index: {2})'.format(self.CanonicalName, self.Nitems, index))
        return self.nineml_inlet_event_ports.values()[0][index]
    
    def getOutletEventPort(self): 
        if len(self.nineml_outlet_event_ports) != 1:
            raise RuntimeError('{0} does not have any send event ports'.format(self.CanonicalName))
        if self.Nitems != 1:
            raise RuntimeError('{0} have distributed send event ports'.format(self.CanonicalName))
            
        return self.nineml_outlet_event_ports.values()[0][0]
    
    def increaseNumberOfItems(self):
        self.Nitems += 1
    
    def _getParameters(self, parent):
        parameters = {}
        for (name, parameter) in self.nineml_parameters.iteritems():
            parameters[ pyCore.daeGetRelativeName(parent, parameter) ] = parameter
        for sub_comp in self.nineml_subcomponents:
            parameters.update(sub_comp._getParameters(parent))
        return parameters

    def _getStateVariables(self, parent):
        variables = {}
        for (name, variable) in self.nineml_variables.iteritems():
            variables[ pyCore.daeGetRelativeName(parent, variable) ] = variable
        for sub_comp in self.nineml_subcomponents:
            variables.update(sub_comp._getStateVariables(parent))
        return variables

    def _getAliases(self, parent):
        aliases = {}
        for (name, (alias_var, node)) in self.nineml_aliases.iteritems():
            aliases[ pyCore.daeGetRelativeName(parent, alias_var) ] = alias_var
        for sub_comp in self.nineml_subcomponents:
            aliases.update(sub_comp._getAliases(parent))
        return aliases

    def _getInletPorts(self, parent):
        ports = {}
        for (name, port) in self.nineml_inlet_ports.iteritems():
            ports[ pyCore.daeGetRelativeName(parent, port) ] = port
        for sub_comp in self.nineml_subcomponents:
            ports.update(sub_comp._getInletPorts(parent))
        return ports

    def _getOutletPorts(self, parent):
        ports = {}
        for (name, port) in self.nineml_outlet_ports.iteritems():
            ports[ pyCore.daeGetRelativeName(parent, port) ] = port
        for sub_comp in self.nineml_subcomponents:
            ports.update(sub_comp._getOutletPorts(parent))
        return ports

    def _getReducePorts(self, parent):
        ports = {}
        for (name, port) in self.nineml_reduce_ports.iteritems():
            ports[ pyCore.daeGetRelativeName(parent, port) ] = port
        for sub_comp in self.nineml_subcomponents:
            ports.update(sub_comp._getReducePorts(parent))
        return ports
    
    def _getExpressionParserIdentifiers(self):
        dictIdentifiers = {}
        dictFunctions   = {}
        
        dictIdentifiers['pi'] = pyCore.Constant(math.pi)
        dictIdentifiers['e']  = pyCore.Constant(math.e)
        dictIdentifiers['t']  = pyCore.Time()
        
        for parameter in self.Parameters:
            dictIdentifiers[parameter.Name] = parameter

        for variable in self.Variables:
            dictIdentifiers[variable.Name] = variable

        # Standard math. functions (single argument)
        dictFunctions['__create_constant__'] = pyCore.Constant
        dictFunctions['sin']   = pyCore.Sin
        dictFunctions['cos']   = pyCore.Cos
        dictFunctions['tan']   = pyCore.Tan
        dictFunctions['asin']  = pyCore.ASin
        dictFunctions['acos']  = pyCore.ACos
        dictFunctions['atan']  = pyCore.ATan
        dictFunctions['sinh']  = pyCore.Sinh
        dictFunctions['cosh']  = pyCore.Cosh
        dictFunctions['tanh']  = pyCore.Tanh
        dictFunctions['asinh'] = pyCore.ASinh
        dictFunctions['acosh'] = pyCore.ACosh
        dictFunctions['atanh'] = pyCore.ATanh
        dictFunctions['log10'] = pyCore.Log10
        dictFunctions['log']   = pyCore.Log
        dictFunctions['sqrt']  = pyCore.Sqrt
        dictFunctions['exp']   = pyCore.Exp
        dictFunctions['floor'] = pyCore.Floor
        dictFunctions['ceil']  = pyCore.Ceil
        dictFunctions['fabs']  = pyCore.Abs

        # Non-standard functions (multiple arguments)
        dictFunctions['pow']   = pyCore.Pow

        # Random distributions, non-standard functions
        """ 
        ACHTUNG, ACHTUNG!! 
        According to the NineML docs, these function can be used only in StateAssignments statements.
        However, it is available for the equations/logical-conditions too. Could it be a problem?
        """
        dictFunctions['random.uniform']     = random_uniform
        dictFunctions['random.normal']      = random_normal
        dictFunctions['random.binomial']    = random_binomial
        dictFunctions['random.poisson']     = random_poisson
        dictFunctions['random.exponential'] = random_exponential

        return daetoolsVariableParameterDictionaryWrapper(dictIdentifiers), dictFunctions        
    
    def _generatePortConnectionEquation(self, varFrom, varTo):
        """
        """
        fromSize = varFrom.Domains[0].NumberOfPoints
        toSize   = varTo.Domains[0].NumberOfPoints
        
        eq = self.CreateEquation('port_connection_{0}_{1}'.format(varFrom.Name, varTo.Name), "")
        if fromSize == 1 and toSize == 1:
            eq.Residual = varFrom(0) - varTo(0)
            
        elif fromSize == 1:
            n = eq.DistributeOnDomain(varTo.Domains[0], pyCore.eClosedClosed)
            eq.Residual = varFrom(0) - varTo(n)
        
        elif toSize == 1:
            n = eq.DistributeOnDomain(varFrom.Domains[0], pyCore.eClosedClosed)
            eq.Residual = varFrom(n) - varTo(0)
        
        elif fromSize > 1 and toSize > 1:
            if varFrom.Domains[0].CanonicalName != varTo.Domains[0].CanonicalName:
                raise RuntimeError('')
            if fromSize != toSize:
                raise RuntimeError('')
            n = eq.DistributeOnDomain(varFrom.Domains[0], pyCore.eClosedClosed)
            eq.Residual = varFrom(n) - varTo(n)
        
        else:
            raise RuntimeError('Cannot generate a port connection equation for the port connection {0} -> {1}'.format(varFrom.CanonicalName, varTo.CanonicalName))

    def _generateReducePortConnectionEquation(self, source_variables, target_variable):
        """
        if the size of *source_variables* list is zero then the equation like the following will be created
        (to seal the port):
            eq.Residual = reduce_var()
        or
            eq.Residual = reduce_var(n)
        which is equivalent to saying that *reduce_var* is equal to zero.
        """
        eq = self.CreateEquation('reduce_port_connection_{0}'.format(target_variable.Name), "")
        
        target_domain = target_variable.Domains[0]
        if target_domain.NumberOfPoints == 1:
            residual = target_variable(0)
            for source_variable in source_variables:
                nr = pyCore.daeIndexRange(source_variable.Domains[0])
                residual = residual - self.sum(source_variable.array(nr))
        
        elif target_domain.NumberOfPoints > 1:
            n = eq.DistributeOnDomain(target_domain, pyCore.eClosedClosed)
            residual = target_variable(n)
            for source_variable in source_variables:
                source_domain = source_variable.Domains[0]
                if source_domain.CanonicalName != target_domain.CanonicalName:
                    raise RuntimeError('')
                if source_domain.NumberOfPoints != target_domain.NumberOfPoints:
                    raise RuntimeError('')
                residual = residual - source_variable(n)
        
        else:
            raise RuntimeError('')
        
        eq.Residual = residual
        
    def DeclareEquations(self):
        if self.Nitems == 0:
            return
        
        wrapperIdentifiers, dictFunctions = self._getExpressionParserIdentifiers()
        
        # 1a) Create aliases (algebraic equations)
        for (name, (var, num)) in self.nineml_aliases.iteritems():
            eq = self.CreateEquation(name, "")
            n = eq.DistributeOnDomain(self.N, pyCore.eClosedClosed)
            wrapperIdentifiers.current_index = n
            residual = var(n) - num.Node.evaluate(wrapperIdentifiers, dictFunctions)
            eq.Residual = residual
        
        # 1b) Create equations for ordinary analogue port connections
        for (varFrom, varTo) in self.nineml_port_connections:
            self._generatePortConnectionEquation(varFrom, varTo)
        
        # 1c) Create equations for reduce port connections
        for (name, (target_variable, source_variables)) in self.nineml_reduce_port_connections.iteritems():
            self._generateReducePortConnectionEquation(source_variables, target_variable)

        # 2) Create regimes
        if len(self.info.nineml_regimes) > 0:
            for stn_i in range(0, self.Nitems):
                # 2a) Create STN for model
                stn = self.STN('{0}({1})'.format(daetoolsComponent.ninemlSTNRegimesName, stn_i))
                self.nineml_stns.append(stn)

                for (regime_name, odes, on_conditions, on_events) in self.info.nineml_regimes:
                    # 2b) Create State for each regime
                    self.STATE(regime_name)

                    # 2c) Create equations for all state variables/time derivatives
                    for (var_name, num) in odes:
                        if not var_name in self.nineml_variables:
                            raise RuntimeError('Cannot find state variable {0}'.format(var_name))
                        variable = self.nineml_variables[var_name]

                        eq = self.CreateEquation('ODE_{0}'.format(var_name), "")
                        wrapperIdentifiers.current_index = stn_i
                        residual = variable.dt(stn_i) - num.Node.evaluate(wrapperIdentifiers, dictFunctions)                        
                        eq.Residual = residual
                            
                    # 2d) Create on_condition actions
                    for (condition_num, switch_to, set_variable_values, trigger_events) in on_conditions:
                        condition         = condition_num.CondNode.evaluate(wrapperIdentifiers, dictFunctions)
                        triggerEvents     = []
                        setVariableValues = []

                        for (var_name, num) in set_variable_values:
                            if not var_name in self.nineml_variables:
                                raise RuntimeError('Cannot find state variable {0}'.format(var_name))
                            variable = self.nineml_variables[var_name](stn_i)
                            wrapperIdentifiers.current_index = stn_i
                            expression = num.Node.evaluate(wrapperIdentifiers, dictFunctions)
                            setVariableValues.append( (variable, expression) )

                        for (port_name, value) in trigger_events:
                            if not port_name in self.nineml_outlet_event_ports:
                                raise RuntimeError('Cannot find event port {0}'.format(port_name))
                            event_port = self.nineml_outlet_event_ports[port_name][stn_i]
                            triggerEvents.append( (event_port, pyCore.Time()) )

                        self.ON_CONDITION(condition, switchTo          = switch_to,
                                                     setVariableValues = setVariableValues,
                                                     triggerEvents     = triggerEvents)

                    # 2e) Create on_event actions
                    for (source_port_name, switch_to_states, set_variable_values, trigger_events) in on_events:
                        if not source_port_name in self.nineml_inlet_event_ports:
                            raise RuntimeError('Cannot find event port {0}'.format(source_port_name))
                        if self.N:
                            source_event_port = self.nineml_inlet_event_ports[source_port_name][stn_i]
                        else:
                            source_event_port = self.nineml_inlet_event_ports[source_port_name]
                        
                        switchToStates    = []
                        triggerEvents     = []
                        setVariableValues = []

                        for (var_name, num) in set_variable_values:
                            if not var_name in self.nineml_variables:
                                raise RuntimeError('Cannot find state variable {0}'.format(var_name))
                            variable = self.nineml_variables[var_name](stn_i)
                            wrapperIdentifiers.current_index = stn_i
                            expression = num.Node.evaluate(wrapperIdentifiers, dictFunctions)
                            setVariableValues.append( (variable, expression) )

                        for (port_name, value) in trigger_events:
                            if not port_name in self.nineml_outlet_event_ports:
                                raise RuntimeError('Cannot find event port {0}'.format(port_name))
                            event_port = self.nineml_outlet_event_ports[port_name][stn_i]
                            triggerEvents.append( (event_port, pyCore.Time()) )

                        self.ON_EVENT(source_event_port, switchToStates    = switchToStates,
                                                         setVariableValues = setVariableValues,
                                                         triggerEvents     = triggerEvents)
                                                    
                self.END_STN()
    
class daetoolsComponentSetup(object):
    """
    Sets the parameter values, initial conditions and other processing needed,
    without a need for the separate object to wrap it.
    It defines three functions which are used by the simulation:
    
    * setUpParametersAndDomains
    * setUpVariables
    * setWeights
    """
    _random_number_generators = {}
    
    @staticmethod
    def setUpParametersAndDomains(model, parameters):
        if model.Nitems == 0:
            return
        
        dae_parameters = model._getParameters(model)
        
        if model.N.NumberOfPoints == 0:
            model.N.CreateArray(model.Nitems)
        
        for paramRelativeName, parameter in dae_parameters.iteritems():
            if not paramRelativeName in parameters:
                raise RuntimeError('Could not find a value for the parameter {0}'.format(paramRelativeName))
            
            value = parameters[paramRelativeName]
            
            if isinstance(value, tuple) and isinstance(value[0], (long, int, float)):
                _value, _units = daetoolsComponentSetup.getValue(value, paramRelativeName)
                q = pyUnits.quantity(_value, _units)
                print('Set the parameter: {0} with units: {1} value'.format(parameter.CanonicalName, parameter.Units))
                print('    quantity: {0}'.format(q))
                parameter.SetValues(q)
                try:
                    print('    new value: {0}'.format(parameter.GetValue()))
                except:
                    print('    new value: {0}'.format(parameter.GetValue(0)))
            
            elif isinstance(value, tuple) and isinstance(value[0], nineml.user_layer.RandomDistribution):
                rng, _units = daetoolsComponentSetup.getValue(value, paramRelativeName)
                n   = parameter.Domains[0].NumberOfPoints
                print('Set the parameter: {0} with units: {1} random value'.format(parameter.CanonicalName, parameter.Units))
                for i in xrange(0, n):
                    _value = float(rng.next())
                    q = pyUnits.quantity(_value, _units)
                    print('    quantity: {0}'.format(q))
                    parameter.SetValue(i, q)
            
            else:
                raise RuntimeError('Invalid parameter: {0} value type specified: {1}-{2}'.format(paramRelativeName, value, type(value)))
    
    @staticmethod      
    def setUpVariables(model, parameters, report_variables):
        if model.Nitems == 0:
            return
        
        # Reporting is off by default for all variables
        #model.SetReportingOn(True)
        
        dae_variables = model._getStateVariables(model)
        dae_aliases   = model._getAliases(model)
        
        for varRelativeName, variable in dae_variables.iteritems():
            if not varRelativeName in parameters:
                raise RuntimeError('Could not find an initial condition for the variable {0}'.format(varRelativeName))
            
            value = parameters[varRelativeName]
            
            if isinstance(value, tuple) and isinstance(value[0], (long, int, float)):
                _value, _units = daetoolsComponentSetup.getValue(value, varRelativeName)
                q = pyUnits.quantity(_value, _units)
                print('Set the variable: {0} with units: {1} value'.format(variable.CanonicalName, variable.VariableType.Units))
                print('    quantity: {0}'.format(q))
                variable.SetInitialConditions(q)
                try:
                    print('    new ic: {0}'.format(variable.GetNumPyArray()))
                except:
                    pass
            
            elif isinstance(value, tuple) and isinstance(value[0], nineml.user_layer.RandomDistribution):
                rng, _units = daetoolsComponentSetup.getValue(value, varRelativeName)
                n = variable.Domains[0].NumberOfPoints
                print('Set the variable: {0} with units: {1} random value'.format(variable.CanonicalName, variable.VariableType.Units))
                for i in xrange(0, n):
                    _value = float(rng.next())
                    q = pyUnits.quantity(_value, _units)
                    print('    quantity: {0}'.format(q))
                    variable.SetInitialCondition(i, q)
            
            else:
                raise RuntimeError('Invalid state variable: {0} initial consition type specified: {1}-{2}'.format(varRelativeName, value, type(value)))
        
        for varRelativeName in report_variables:
            if varRelativeName in dae_variables:
                variable = dae_variables[varRelativeName]
                variable.ReportingOn = True
            elif varRelativeName in dae_aliases:
                variable = dae_aliases[varRelativeName]
                variable.ReportingOn = True
                
    @staticmethod      
    def setWeights(model, weights):
        """
        :param: daetoolsComponent object
        :param: list of pyUnits.quantity objects
        
        :rtype: None
        :raises: RuntimeError
        """
        if model.Nitems != len(weights):
            raise RuntimeError('The number of weights not equal to the number of synapses in the synapse {0}'.format(model.Name))
        
        if model.Nitems == 0:
            return
            
        dae_parameters = model._getParameters(model)
        if 'weight' in dae_parameters:
            paramWeight = dae_parameters['weight']
        else:
            raise RuntimeError('Could not find a parameter with the name [weight] in the synapse {0}'.format(model.Name))
        
        print('Set the weights for: {0} with units: {1}'.format(paramWeight.CanonicalName, paramWeight.Units))
        for i, weight in enumerate(weights):
            print('    Weight value: {0}'.format(weight))
            paramWeight.SetValue(i, weight)
            print('    Set weight: {0}'.format(paramWeight.GetValue(i)))
            
    @staticmethod
    def getValue(value, name):
        """
        Internal function used to get a value of parameters values and initial conditions.
        It can handle simple numbers and tuples (value, units). The *value* can be a simple number, 
        an expression involving other parameters and variables or a random number distribution.
        
        :rtype: float
        :raises: RuntimeError
        """
        if isinstance(value, tuple):
            if len(value) != 2:
                raise RuntimeError('The value for: {0} must be a tuple in the format (float, units): {1}'.format(name, value))
            
            _value, _units = value
            
            if isinstance(_value, (float, int, long)): # Simple number
                return (_value, _units)
            
            elif isinstance(_value, nineml.user_layer.RandomDistribution): # A RandomDistribution component
                if not _value.name in daetoolsComponentSetup._random_number_generators:
                    raise RuntimeError('Cannot find RandomDistribution component {0}'.format(_value.name))
                
                rng = daetoolsComponentSetup._random_number_generators[_value.name]
                return (rng, _units)
            
            else: # Something is wrong
                raise RuntimeError('Invalid parameter: {0} value type specified: {1}-{2}'.format(name, value, type(value)))
        
        else:
            raise RuntimeError('Invalid parameter: {0} value type specified: {1}-{2}'.format(name, value, type(value)))
