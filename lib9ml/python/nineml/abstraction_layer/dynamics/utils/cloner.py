"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...expressions.utils import MathUtil
from nineml.abstraction_layer.componentclass.namespace import NamespaceAddress
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentRenameSymbol, ComponentClonerVisitor)
from .visitors import DynamicsActionVisitor


class DynamicsExpandPortDefinition(DynamicsActionVisitor,
                                   ComponentExpandPortDefinition):

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        trigger.rhs_name_transform_inplace(self.namemap)


class DynamicsExpandAliasDefinition(DynamicsActionVisitor,
                                    ComponentExpandAliasDefinition):

    """ An action-class that walks over a componentclass, and expands an alias in
    Assignments, Aliases, TimeDerivatives and Conditions
    """

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        trigger.rhs_name_transform_inplace(self.namemap)


class DynamicsRenameSymbol(DynamicsActionVisitor,
                           ComponentRenameSymbol):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def action_dynamics(self, dynamics, **kwargs):
        pass

    def action_regime(self, regime, **kwargs):
        pass

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if state_variable.name == self.old_symbol_name:
            state_variable._name = self.new_symbol_name
            self.note_lhs_changed(state_variable)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_eventout(self, event_out, **kwargs):  # @UnusedVariable
        if event_out.port_name == self.old_symbol_name:
            event_out._port_name = self.new_symbol_name
            self.note_rhs_changed(event_out)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in assignment.atoms:
            self.note_rhs_changed(assignment)
            assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        if timederivative.dependent_variable == self.old_symbol_name:
            self.note_lhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in timederivative.atoms:
            self.note_rhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in trigger.rhs_atoms:
            self.note_rhs_changed(trigger)
            trigger.rhs_name_transform_inplace(self.namemap)

    def action_oncondition(self, on_condition, **kwargs):
        """ Handled in action_condition """
        pass

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if on_event.src_port_name == self.old_symbol_name:
            on_event._port_name = self.new_symbol_name
            self.note_rhs_changed(on_event)


class DynamicsClonerVisitor(ComponentClonerVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        ccn = componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters],
            analog_ports=[p.accept_visitor(self, **kwargs)
                          for p in componentclass.analog_ports],
            event_ports=[p.accept_visitor(self, **kwargs)
                         for p in componentclass.event_ports],
            dynamics=(componentclass.dynamics.accept_visitor(self, **kwargs)
                      if componentclass.dynamics else None),
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in componentclass.subnodes.iteritems()]),
            portconnections=componentclass.portconnections[:])
        return ccn

    def visit_dynamics(self, dynamics, **kwargs):
        return dynamics.__class__(
            regimes=[r.accept_visitor(self, **kwargs)
                     for r in dynamics.regimes],
            aliases=[
                a.accept_visitor(self, **kwargs) for a in dynamics.aliases],
            state_variables=[s.accept_visitor(self, **kwargs)
                             for s in dynamics.state_variables])

    def visit_regime(self, regime, **kwargs):
        return regime.__class__(
            name=regime.name,
            time_derivatives=[t.accept_visitor(self, **kwargs)
                              for t in regime.time_derivatives],
            transitions=[t.accept_visitor(self, **kwargs)
                         for t in regime.transitions])

    def visit_statevariable(self, state_variable, **kwargs):
        return state_variable.__class__(
            name=self.prefix_variable(state_variable.name, **kwargs),
            dimension=state_variable.dimension)

    def visit_analogreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_analogreduceport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_analogsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventout(self, event_out, **kwargs):
        return event_out.__class__(
            port_name=self.prefix_variable(event_out.port_name, **kwargs))

    def visit_assignment(self, assignment, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        lhs = self.prefix_variable(assignment.lhs, **kwargs)
        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=assignment, prefix=prefix, exclude=prefix_excludes)

        return assignment.__class__(lhs=lhs, rhs=rhs)

    def visit_timederivative(self, time_derivative, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        dep = self.prefix_variable(time_derivative.dependent_variable,
                                   **kwargs)

        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=time_derivative, prefix=prefix, exclude=prefix_excludes)
        return time_derivative.__class__(dependent_variable=dep, rhs=rhs)

    def visit_trigger(self, trigger, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=trigger, prefix=prefix, exclude=prefix_excludes)
        return trigger.__class__(rhs=rhs)

    def visit_oncondition(self, on_condition, **kwargs):
        return on_condition.__class__(
            trigger=on_condition.trigger.accept_visitor(self, **kwargs),
            event_outputs=[e.accept_visitor(self, **kwargs)
                           for e in on_condition.event_outputs],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_condition.state_assignments],
            target_regime_name=on_condition.target_regime_name
        )

    def visit_onevent(self, on_event, **kwargs):
        return on_event.__class__(
            src_port_name=self.prefix_variable(on_event.src_port_name,
                                               **kwargs),
            event_outputs=[e.accept_visitor(self, **kwargs)
                           for e in on_event.event_outputs],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_event.state_assignments],
            target_regime_name=on_event.target_regime_name
        )


class DynamicsClonerVisitorPrefixNamespace(DynamicsClonerVisitor):

    """ A visitor that walks over a hierarchical componentclass, and prefixes every
    variable with the namespace that that variable is in. This is preparation
    for flattening
    """

    def visit_componentclass(self, componentclass, **kwargs):  # @UnusedVariable
        prefix = componentclass.get_node_addr().get_str_prefix()
        if prefix == '_':
            prefix = ''
        prefix_excludes = ['t']
        kwargs = {'prefix': prefix, 'prefix_excludes': prefix_excludes}

        port_connections = []
        for src, sink in componentclass.portconnections:
            # To calculate the new address of the ports, we take of the 'local'
            # port address, i.e. the parent address, then add the prefixed
            # string:
            src_new = NamespaceAddress.concat(
                src.get_parent_addr(),
                NamespaceAddress.concat(
                    componentclass.get_node_addr(),
                    src.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(src.get_local_name()))
            sink_new = NamespaceAddress.concat(
                sink.get_parent_addr(), NamespaceAddress.concat(
                    componentclass.get_node_addr(),
                    sink.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(sink.get_local_name()))
            # self.prefix_variable(sink.get_local_name(), **kwargs) )

            # print 'Mapping Ports:', src, '->', src_new, '(%s)' %
#                  src.get_local_name(), prefix
            # print 'Mapping Ports:', sink, '->', sink_new
            # src_new = NamespaceAddress.concat(
#                 src.get_parent_addr(), src.getstr() )
            # sink_new = NamespaceAddress.concat(
#                 sink.get_parent_addr(), sink.getstr() )
            port_connections.append((src_new, sink_new))
        return componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters],
            analog_ports=[p.accept_visitor(self, **kwargs)
                          for p in componentclass.analog_ports],
            event_ports=[p.accept_visitor(self, **kwargs)
                         for p in componentclass.event_ports],
            dynamics=(componentclass.dynamics.accept_visitor(self, **kwargs)
                      if componentclass.dynamics else None),
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in componentclass.subnodes.iteritems()]),
            portconnections=port_connections)
