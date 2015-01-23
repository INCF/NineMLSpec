"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.validators import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator)
from . import BaseConnectionRuleValidator


class AliasesAreNotRecursiveConnectionRuleValidator(
        AliasesAreNotRecursiveComponentValidator,
        BaseConnectionRuleValidator):

    """Check that aliases are not self-referential"""

    pass


class NoUnresolvedSymbolsConnectionRuleValidator(
        NoUnresolvedSymbolsComponentValidator,
        BaseConnectionRuleValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """
    pass


class NoDuplicatedObjectsConnectionRuleValidator(
        NoDuplicatedObjectsComponentValidator,
        BaseConnectionRuleValidator):

    def action_connectionrule(self, connectionrule, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(connectionrule)


class CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        BaseConnectionRuleValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """
    pass
