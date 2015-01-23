"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from . import PerNamespaceComponentValidator
from nineml.exceptions import NineMLRuntimeError
from ...expressions.utils import (get_reserved_and_builtin_symbols,
                                  is_valid_lhs_target)
from nineml.utils import assert_no_duplicates


class AliasesAreNotRecursiveComponentValidator(PerNamespaceComponentValidator):

    """Check that aliases are not self-referential"""

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(componentclass)

    def action_componentclass(self, componentclass, namespace):

        unresolved_aliases = dict((a.lhs, a) for a in componentclass.aliases)

        def alias_contains_unresolved_symbols(alias):
            unresolved = [sym for sym in alias.rhs_atoms
                          if sym in unresolved_aliases]
            return len(unresolved) != 0

        def get_resolved_aliases():
            return [alias for alias in unresolved_aliases.values()
                    if not alias_contains_unresolved_symbols(alias)]

        while(unresolved_aliases):

            resolved_aliases = get_resolved_aliases()
            if resolved_aliases:
                for r in resolved_aliases:
                    del unresolved_aliases[r.lhs]

            else:
                errmsg = "Unable to resolve all aliases in %s. " % namespace
                errmsg += "You may have a recursion issue."
                errmsg += ("Remaining Aliases: %s" %
                           ','.join(unresolved_aliases.keys()))
                raise NineMLRuntimeError(errmsg)


class NoUnresolvedSymbolsComponentValidator(PerNamespaceComponentValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)

        self.available_symbols = defaultdict(list)
        self.aliases = defaultdict(list)
        self.time_derivatives = defaultdict(list)
        self.state_assignments = defaultdict(list)

        self.visit(componentclass)

        excludes = get_reserved_and_builtin_symbols()

        # Check Aliases:
        for ns, aliases in self.aliases.iteritems():
            for alias in aliases:
                for rhs_atom in alias.rhs_atoms:
                    if rhs_atom in excludes:
                        continue
                    if rhs_atom not in self.available_symbols[ns]:
                        err = ('Unresolved Symbol in Alias: %s [%s]' %
                               (rhs_atom, alias))
                        raise NineMLRuntimeError(err)

        # Check TimeDerivatives:
        for ns, timederivatives in self.time_derivatives.iteritems():
            for timederivative in timederivatives:
                for rhs_atom in timederivative.rhs_atoms:
                    if (rhs_atom not in self.available_symbols[ns] and
                            rhs_atom not in excludes):
                        err = ('Unresolved Symbol in Time Derivative: %s [%s]'
                               % (rhs_atom, timederivative))
                        raise NineMLRuntimeError(err)

        # Check StateAssignments
        for ns, state_assignments in self.state_assignments.iteritems():
            for state_assignment in state_assignments:
                for rhs_atom in state_assignment.rhs_atoms:
                    if (rhs_atom not in self.available_symbols[ns] and
                            rhs_atom not in excludes):
                        err = ('Unresolved Symbol in Assignment: %s [%s]' %
                               (rhs_atom, state_assignment))
                        raise NineMLRuntimeError(err)

    def add_symbol(self, namespace, symbol):
        if symbol in self.available_symbols[namespace]:
            err = ("Duplicate Symbol: [%s] found in namespace: %s" %
                   (symbol, namespace))
            raise NineMLRuntimeError(err)
        self.available_symbols[namespace].append(symbol)

    def action_alias(self, alias, namespace, **kwargs):  # @UnusedVariable
        self.add_symbol(namespace=namespace, symbol=alias.lhs)
        self.aliases[namespace].append(alias)

    def action_parameter(self, parameter, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(namespace=namespace, symbol=parameter.name)


class NoDuplicatedObjectsComponentValidator(PerNamespaceComponentValidator):

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=True)
        self.all_objects = list()
        self.visit(componentclass)
        assert_no_duplicates(self.all_objects)

    def action_componentclass(self, componentclass, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(componentclass)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.all_objects.append(parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.all_objects.append(alias)


class CheckNoLHSAssignmentsToMathsNamespaceComponentValidator(
        PerNamespaceComponentValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)

        self.visit(componentclass)

    def check_lhssymbol_is_valid(self, symbol):
        assert isinstance(symbol, basestring)

        if not is_valid_lhs_target(symbol):
            err = 'Symbol: %s found on left-hand-side of an equation'
            raise NineMLRuntimeError(err)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(parameter.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(alias.lhs)
