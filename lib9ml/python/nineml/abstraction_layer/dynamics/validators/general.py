"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import assert_no_duplicates
from ...componentclass.validators import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator)
from . import PerNamespaceDynamicsValidator


class TimeDerivativesAreDeclaredDynamicsValidator(
        PerNamespaceDynamicsValidator):

    """ Check all variables used in TimeDerivative blocks are defined
        as  StateVariables.
    """

    def __init__(self, componentclass):
        PerNamespaceDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.sv_declared = defaultdict(list)
        self.time_derivatives_used = defaultdict(list)

        self.visit(componentclass)

        for namespace, time_derivatives in self.time_derivatives_used.\
                                                                   iteritems():
            for td in time_derivatives:
                if td not in self.sv_declared[namespace]:
                    err = 'StateVariable not declared: %s' % td
                    raise NineMLRuntimeError(err)

    def action_statevariable(self, state_variable, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared[namespace].append(state_variable.name)

    def action_timederivative(self, timederivative, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.time_derivatives_used[namespace].append(
            timederivative.dependent_variable)


class StateAssignmentsAreOnStateVariablesDynamicsValidator(
        PerNamespaceDynamicsValidator):

    """ Check that we only attempt to make StateAssignments to state-variables.
    """

    def __init__(self, componentclass):
        PerNamespaceDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.sv_declared = defaultdict(list)
        self.state_assignments_lhses = defaultdict(list)

        self.visit(componentclass)

        for namespace, state_assignments_lhs in self.state_assignments_lhses.\
                                                                   iteritems():
            for td in state_assignments_lhs:
                if td not in self.sv_declared[namespace]:
                    err = 'Not Assigning to state-variable: {}'.format(td)
                    raise NineMLRuntimeError(err)

    def action_statevariable(self, state_variable, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared[namespace].append(state_variable.name)

    def action_stateassignment(self, state_assignment, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        assert False
        self.state_assignments_lhses[namespace].append(state_assignment.lhs)


class AliasesAreNotRecursiveDynamicsValidator(
        AliasesAreNotRecursiveComponentValidator,
        PerNamespaceDynamicsValidator):

    """Check that aliases are not self-referential"""

    pass


class NoUnresolvedSymbolsDynamicsValidator(
        NoUnresolvedSymbolsComponentValidator,
        PerNamespaceDynamicsValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def action_analogreceiveport(self, port, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.available_symbols[namespace].append(port.name)

    def action_analogreduceport(self, port, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.available_symbols[namespace].append(port.name)

    def action_statevariable(self, state_variable, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(namespace=namespace, symbol=state_variable.name)

    def action_timederivative(self, time_derivative, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.time_derivatives[namespace].append(time_derivative)

    def action_assignment(self, state_assignment, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.state_assignments[namespace].append(state_assignment)


class RegimeGraphDynamicsValidator(PerNamespaceDynamicsValidator):

    def __init__(self, componentclass):
        PerNamespaceDynamicsValidator.__init__(
            self, require_explicit_overrides=False)

        self.connected_regimes_from_regime = defaultdict(set)
        self.regimes_in_namespace = defaultdict(set)

        self.visit(componentclass)

        def add_connected_regimes_recursive(regime, connected):
            connected.add(regime)
            for r in self.connected_regimes_from_regime[regime]:
                if r not in connected:
                    add_connected_regimes_recursive(r, connected)

        for namespace, regimes in self.regimes_in_namespace.iteritems():

            # Perhaps we have no transition graph; this is OK:
            if len(regimes) == 0:
                continue

            connected = set()
            add_connected_regimes_recursive(regimes[0], connected)
            if len(connected) != len(self.regimes_in_namespace[namespace]):
                raise NineMLRuntimeError('Transition graph is contains '
                                         'islands')

    def action_componentclass(self, componentclass, namespace):
        self.regimes_in_namespace[namespace] = list(componentclass.regimes)

    def action_regime(self, regime, namespace):  # @UnusedVariable
        for transition in regime.transitions:
            self.connected_regimes_from_regime[regime].add(
                transition.target_regime)
            self.connected_regimes_from_regime[transition.target_regime].add(
                regime)


class NoDuplicatedObjectsDynamicsValidator(
        NoDuplicatedObjectsComponentValidator,
        PerNamespaceDynamicsValidator):

    def action_dynamics(self, dynamics, **kwargs):  # @UnusedVariable
        self.all_objects.append(dynamics)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        self.all_objects.append(regime)

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(state_variable)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_eventout(self, event_out, **kwargs):  # @UnusedVariable
        self.all_objects.append(event_out)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        self.all_objects.append(assignment)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(time_derivative)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        self.all_objects.append(trigger)

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        self.all_objects.append(on_condition)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.all_objects.append(on_event)


class RegimeOnlyHasOneHandlerPerEventDynamicsValidator(
        PerNamespaceDynamicsValidator):

    def __init__(self, componentclass):
        PerNamespaceDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(componentclass)

    def action_regime(self, regime, namespace, **kwargs):  # @UnusedVariable
        event_triggers = [on_event.src_port_name
                          for on_event in regime.on_events]
        assert_no_duplicates(event_triggers)


class CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        PerNamespaceDynamicsValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_lhssymbol_is_valid(state_variable.name)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(assignment.lhs)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_lhssymbol_is_valid(time_derivative.dependent_variable)
