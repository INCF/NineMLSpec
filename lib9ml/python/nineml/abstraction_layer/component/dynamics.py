"""This file contains the main classes for defining dynamics"""

from itertools import chain

from expressions import StateAssignment, TimeDerivative, Alias 
from conditions import  Condition
from events import  OutputEvent
from util import StrToExpr, MathUtil

import nineml.utility
from nineml.exceptions import NineMLRuntimeError


#from nineml.utility import filter_discrete_types


class Transition(object):

    def __init__(self, state_assignments=None, event_outputs=None, 
                 target_regime_name=None):
        """Abstract class representing a transition from one |Regime| to
        another.

        |Transition| objects are not created directly, but via the subclasses
        |OnEvent| and |OnCondition|.

        :param state_assignments: A list of the state-assignments performed
            when this transition occurs. Objects in this list are either
            `string` (e.g A = A+13) or |StateAssignment| objects.
        :param event_outputs: A list of |OutputEvent| objects emitted when
            this transition occurs.
        :param target_regime_name: The name of the regime to go into after this
            transition.  ``None`` implies staying in the same regime. This has
            to be specified as a string, not the object, because in general the
            |Regime| object is not yet constructed. This is automatically
            resolved by the |ComponentClass| in
            ``_ResolveTransitionRegimeNames()`` during construction.


        .. todo::

            For more information about what happens at a regime transition, see
            here: XXXXXXX

        """
        if target_regime_name:
            assert isinstance(target_regime_name, basestring)

        # Load state-assignment objects as strings or StateAssignment objects
        from nineml.utility import filter_discrete_types
        state_assignments = state_assignments or []

        sa_types = (basestring, StateAssignment )
        sa_type_dict = filter_discrete_types( state_assignments, sa_types )
        sa_from_str = [StrToExpr.state_assignment(o) for o in sa_type_dict[basestring]] 
        self._state_assignments = sa_type_dict[StateAssignment] + sa_from_str
        

        self._event_outputs = event_outputs or [] 

        
        self._target_regime_name = target_regime_name
        self._source_regime_name = None

        # Set later, once attached to a regime:
        self._target_regime = None
        self._source_regime = None
    

    def set_source_regime(self, source_regime):
        """ Internal method, used during component construction.
        
        Used internally by the ComponentClass objects after all objects
        have be constructed, in the ``_ResolveTransitionRegimeNames()`` method.
        This is because when we build Transitions, the Regimes that they refer
        to generally are not build yet, so are referred to by strings. This
        method is used to set the source ``Regime`` object. We check that the name
        of the object set is the same as that previously expected.
        """

        assert isinstance( source_regime, Regime)
        assert not self._source_regime
        if self._source_regime_name: 
            assert self._source_regime_name == source_regime.name
        else:
            self._source_regime_name = source_regime.name
        self._source_regime = source_regime
        
    # MH: I am pretty sure we don't need this, but its possible, 
    # so I won't delete it yet - since there might be a reason we do :)
    #def set_target_regime_name(self, target_regime_name):
    #    assert False
    #    assert isinstance( target_regime_name, basestring)
    #    assert not self._target_regime
    #    assert not self._target_regime_name 
    #    self._target_regime_name = target_regime_name


    def set_target_regime(self, target_regime):
        """ Internal method, used during component construction.

            See ``set_source_regime``
        """
        assert isinstance( target_regime, Regime)
        if self._target_regime:
            assert self.target_regime == target_regime
            return 

        # Did we already set the target_regime_name
        if self._target_regime_name: 
            assert self._target_regime_name == target_regime.name
        else:
            self._target_regime_name = target_regime.name
        self._target_regime = target_regime
    
    @property
    def target_regime_name(self):
        """DO NOT USE: Internal function. Use `target_regime.name` instead.
        """
        if self._target_regime_name:
            assert isinstance( self._target_regime_name, basestring) 
        return self._target_regime_name

    @property
    def source_regime_name(self):
        """DO NOT USE: Internal function. Use `source_regime.name` instead.
        """
        if self._source_regime:
            err = "Should not be called by users.Use source_regime.name instead"
            raise NineMLRuntimeError(err)
        assert self._source_regime_name
        return self._source_regime_name

    @property
    def target_regime(self):
        """Returns the target regime of this transition.

        .. note::
        
            This method will only be available after the ComponentClass
            containing this transition has been built. See ``set_source_regime``
        """

        assert self._target_regime
        return self._target_regime
    @property
    def source_regime(self):
        """Returns the source regime of this transition.

        .. note::
        
            This method will only be available after the |ComponentClass|
            containing this transition has been built. See ``set_source_regime``
        """
        assert self._source_regime
        return self._source_regime
    

    @property
    def state_assignments(self):
        """An ordered list of |StateAssignments| that happen when this
        transitions occurs"""
        return self._state_assignments
    
    @property
    def event_outputs(self):
        """|Events| that happen when this transitions occurs"""
        return self._event_outputs







class OnEvent(Transition):

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_onevent(self, **kwargs)

    def __init__(self, src_port_name, state_assignments=None, 
                 event_outputs=None, target_regime_name=None):
        """Constructor for ``OnEvent``
            
            :param src_port_name: The name of the |EventPort| that triggers this transition

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        Transition.__init__(self, state_assignments=state_assignments, 
                            event_outputs=event_outputs, 
                            target_regime_name=target_regime_name)
        self._src_port_name = src_port_name.strip()
        nineml.utility.ensure_valid_c_variable_name(self._src_port_name)

    @property
    def src_port_name(self):
        return self._src_port_name

    def __repr__(self):
        return """OnEvent( %s )"""%self.src_port_name



class OnCondition(Transition):

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_oncondition(self, **kwargs)

    def __init__(self, trigger, state_assignments=None, 
                 event_outputs=None, target_regime_name=None):
        """Constructor for ``OnEvent``
            
            :param trigger: Either a |Condition| object or a ``string`` object
                specifying the conditions under which this transition should
                occur.

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        from nineml.abstraction_layer.visitors import ClonerVisitor
        if isinstance( trigger, Condition): 
            self._trigger = ClonerVisitor().visit( trigger )
        elif isinstance( trigger, basestring): 
            self._trigger = Condition( rhs = trigger )
        else:  
            assert False

        Transition.__init__(self, state_assignments=state_assignments, 
                            event_outputs=event_outputs, 
                            target_regime_name=target_regime_name)


    def __repr__(self):
        return 'OnCondition( %s )' % self.trigger.rhs
    
    @property
    def trigger(self):
        return self._trigger


















class Regime(object):
    """
    A Regime is something that contains |TimeDerivatives|, has temporal extent,
    defines a set of |Transitions| which occur based on |Conditions|, and can be join the Regimes to other Regimes.
    """

    _n = 0
   
    @classmethod
    def get_next_name(cls):
        """Return the next distinct autogenerated name
        """
        Regime._n = Regime._n + 1
        return 'Regime%d'% Regime._n


    # Visitation:
    # -------------
    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_regime(self, **kwargs)


    def __init__(self, *args, **kwargs):
        """Regime constructor
            
            :param name: The name of the constructor. If none, then a name will
                be automatically generated.
            :param time_derivatives: A list of time derivatives, as
                either ``string``s (e.g 'dg/dt = g/gtau') or as |TimeDerivative|
                objects.
            :param transitions: A list containing either |OnEvent| or
                |OnCondition| objects, which will automatically be sorted into
                the appropriate classes automatically.
            :param *args: Any non-keyword arguments will be treated as
                time_derivatives.


        """
        valid_kwargs = ('name','transitions','time_derivatives')
        for arg in kwargs:
            if not arg in valid_kwargs:
                err = 'Unexpected Arg: %s'%arg
                raise NineMLRuntimeError(err)

        transitions=kwargs.get('transitions',None)
        name = kwargs.get('name', None)
        kw_tds = nineml.utility.normalise_parameter_as_list( kwargs.get('time_derivatives',None))
        time_derivatives = list(args) + kw_tds
        


        # Generate a name for unnamed regions:
        self._name = name.strip() if name else Regime.get_next_name()
        nineml.utility.ensure_valid_c_variable_name(self._name)



        # Un-named arguments are time_derivatives:
        time_derivatives = nineml.utility.normalise_parameter_as_list(time_derivatives) 
        #time_derivatives.extend( args )

        td_types = (basestring, TimeDerivative )
        td_type_dict = nineml.utility.filter_discrete_types(time_derivatives, td_types)
        td_from_str = [StrToExpr.time_derivative(o) for o in td_type_dict[basestring]]  
        self._time_derivatives = td_type_dict[TimeDerivative] + td_from_str

        # Check for double definitions:
        td_dep_vars = [td.dependent_variable for td in self._time_derivatives]
        nineml.utility.assert_no_duplicates(td_dep_vars)


        # We support passing in 'transitions', which is a list of both OnEvents
        # and OnConditions. So, lets filter this by type and add them
        # appropriately:

        transitions = nineml.utility.normalise_parameter_as_list(transitions) 
        f_dict = nineml.utility.filter_discrete_types( transitions, (OnEvent, OnCondition)) 
        self._on_events = [] 
        self._on_conditions = [] 

        # Add all the OnEvents and OnConditions:
        for event in f_dict[OnEvent] :
            self.add_on_event(event)
        for condition in f_dict[OnCondition]:
            self.add_on_condition(condition)



    def _resolve_references_on_transition(self, transition):
        if transition.target_regime_name is None:
            transition.set_target_regime(self)
        
        assert not transition._source_regime_name
        transition.set_source_regime( self )


    def add_on_event(self, on_event):
        """Add an |OnEvent| transition which leaves this regime

        If the on_event object has not had its target regime name
        set in the constructor, or by calling its ``set_target_regime_name()``, 
        then the target is assumed to be this regime, and will be set
        appropriately.

        The source regime for this transition will be set as this regime.

        """

        if not isinstance(on_event, OnEvent):
            err = "Expected 'OnEvent' Obj, but got %s"%(type(on_event))
            raise NineMLRuntimeError(err)

        self._resolve_references_on_transition(on_event)
        self._on_events.append( on_event )

    def add_on_condition(self, on_condition):
        """Add an |OnCondition| transition which leaves this regime

        If the on_condition object has not had its target regime name
        set in the constructor, or by calling its ``set_target_regime_name()``, 
        then the target is assumed to be this regime, and will be set
        appropriately.
        
        The source regime for this transition will be set as this regime.

        """
        if not isinstance(on_condition, OnCondition):
            err = "Expected 'OnCondition' Obj, but got %s"%(type(on_condition))
            raise NineMLRuntimeError(err)
        self._resolve_references_on_transition(on_condition)
        self._on_conditions.append( on_condition )


    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)


    # Regime Properties:
    # ------------------
    @property
    def time_derivatives(self):
        """Returns the state-variable time-derivatives in this regime.

        .. note::
    
            This is not guaranteed to contain the time derivatives for all the
            state-variables specified in the component. If they are not defined,
            they are assumed to be zero in this regime.

        """
        return iter(self._time_derivatives)

    @property
    def transitions(self):
        """Returns all the transitions leaving this regime.
        
        Returns an iterator over both the on_events and on_conditions of this
        regime"""

        return chain(  self._on_events, self._on_conditions )

    @property 
    def on_events(self):
        """Returns all the transitions out of this regime trigger by events"""
        return iter(self._on_events)

    @property 
    def on_conditions(self):
        """Returns all the transitions out of this regime trigger by
        conditions"""
        return iter(self._on_conditions)

    @property
    def name(self):
        return self._name
























# Forwarding Function:
def On( trigger, do=None, to=None ):
    if isinstance(do, (OutputEvent, basestring)): 
        do = [do]
    elif do == None: 
        do = []
    else: 
        pass

    if isinstance( trigger, basestring):
        if MathUtil.is_single_symbol(trigger):
            return DoOnEvent(input_event=trigger, do=do, to=to)
        else:
            return DoOnCondition(condition=trigger, do=do, to=to)

    elif isinstance( trigger, OnCondition):
        return DoOnCondition(condition=trigger, do=do, to=to)
    else:
        err = "Unexpected Type for On() trigger: %s %s" %(type(trigger),
                str(trigger) )
        raise NineMLRuntimeError(err)





def do_to_assignments_and_events(doList):
    if not doList: return [], []
    # 'doList' is a list of strings, OutputEvents, and StateAssignments.
    do_type_list =  (OutputEvent, basestring, StateAssignment) 
    do_types = nineml.utility.filter_discrete_types(doList, do_type_list)
    
    #Convert strings to StateAssignments:
    sa_from_strs = [StrToExpr.state_assignment(s) for s in do_types[basestring]]

    return do_types[StateAssignment]+sa_from_strs, do_types[OutputEvent]


def DoOnEvent(input_event, do=None, to=None):
    assert isinstance( input_event, basestring) 
    
    assignments, output_events = do_to_assignments_and_events( do ) 
    return OnEvent( src_port_name=input_event,
                    state_assignments = assignments,
                    event_outputs=output_events,
                    target_regime_name = to )



def DoOnCondition( condition, do=None, to=None ):
    assignments, output_events = do_to_assignments_and_events( do ) 
    return OnCondition( trigger=condition,
                        state_assignments = assignments,
                        event_outputs=output_events,
                        target_regime_name = to )



class Dynamics(object):
    """A container class, which encapsulates a component's regimes, transitions,
    and state variables"""

    def __init__(self, regimes = None, aliases = None, state_variables = None):
        """Dynamics object constructor
        
           :param aliases: A list of aliases, which must be either |Alias|
               objects or ``string``s.
           :param regimes: A list containing at least one |Regime| object.
           :param state_variables: An optional list of the state variables,
                which can either be |StateVariable| objects or `string` s. If
                provided, it must match the inferred state-variables from the
                regimes; if it is not provided it will be inferred
                automatically.
        """

        aliases = nineml.utility.normalise_parameter_as_list(aliases)
        regimes = nineml.utility.normalise_parameter_as_list(regimes)
        state_variables = nineml.utility.normalise_parameter_as_list(state_variables)

        # Load the aliases as objects or strings:
        from nineml.utility import filter_discrete_types
        alias_td = filter_discrete_types( aliases, (basestring, Alias ) )
        aliases_from_strs = [StrToExpr.alias(o) for o in alias_td[basestring]] 
        aliases = alias_td[Alias] + aliases_from_strs

        # Load the state variables as objects or strings:
        sv_types =  (basestring, StateVariable) 
        sv_td = filter_discrete_types( state_variables, sv_types)
        sv_from_strings =  [ StateVariable(o) for o in sv_td[basestring] ] 
        state_variables = sv_td[StateVariable] + sv_from_strings


        self._regimes = regimes
        self._aliases = aliases
        self._state_variables = state_variables

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_dynamics(self, **kwargs)

    @property
    def regimes(self):
        return iter( self._regimes )

    @property
    def regimes_map(self):
        return dict( (r.name,r) for r in self.regimes )

    @property
    def transitions(self):
        return chain( *[r.transitions for r in self._regimes] )

    @property
    def aliases(self):
        return iter( self._aliases )

    @property
    def aliases_map(self):
        return dict( [ (a.lhs, a) for a in self._aliases ] )

    @property
    def state_variables(self):
        return iter( self._state_variables )

    @property
    def state_variables_map(self):
        return dict( [(sv.name, sv) for sv in self._state_variables ] )
    
    

    
class StateVariable(object):
    """A class representing a state-variable in a ``ComponentClass``.
    
    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)
    def __init__(self, name, dimension=""):
        """StateVariable Constructor

        :param name:  The name of the state variable.
        """
        self._name = name.strip()
        self._dimension = dimension
        nineml.utility.ensure_valid_c_variable_name(self._name)


    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def __str__(self):
        return "<StateVariable: %s (%s)>" % (self.name, self.dimension)
