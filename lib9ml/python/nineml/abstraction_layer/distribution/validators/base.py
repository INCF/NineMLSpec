"""
This file contains the DistributionValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    AliasesAreNotRecursiveDistributionValidator,
    NoUnresolvedSymbolsDistributionValidator,
    NoDuplicatedObjectsDistributionValidator,
    CheckNoLHSAssignmentsToMathsNamespaceDistributionValidator)
from .namingconflicts import (
    LocalNameConflictsDistributionValidator,
    DimensionNameConflictsDistributionValidator)
from .ports import (
    PortConnectionsDistributionValidator)
from .types import (
    TypesDistributionValidator)


class DistributionValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesDistributionValidator(componentclass)
        NoDuplicatedObjectsDistributionValidator(componentclass)
        LocalNameConflictsDistributionValidator(componentclass)
        DimensionNameConflictsDistributionValidator(componentclass)
        AliasesAreNotRecursiveDistributionValidator(componentclass)
        NoUnresolvedSymbolsDistributionValidator(componentclass)
        PortConnectionsDistributionValidator(componentclass)
        CheckNoLHSAssignmentsToMathsNamespaceDistributionValidator(
            componentclass)
