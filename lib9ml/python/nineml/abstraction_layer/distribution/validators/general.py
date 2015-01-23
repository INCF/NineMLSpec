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
from . import BaseDistributionValidator


class AliasesAreNotRecursiveDistributionValidator(
        AliasesAreNotRecursiveComponentValidator,
        BaseDistributionValidator):

    """Check that aliases are not self-referential"""

    pass


class NoUnresolvedSymbolsDistributionValidator(
        NoUnresolvedSymbolsComponentValidator,
        BaseDistributionValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """
    pass


class NoDuplicatedObjectsDistributionValidator(
        NoDuplicatedObjectsComponentValidator,
        BaseDistributionValidator):

    def action_distribution(self, distribution, **kwargs):  # @UnusedVariable
        self.all_objects.append(distribution)


class CheckNoLHSAssignmentsToMathsNamespaceDistributionValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        BaseDistributionValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """
    pass
