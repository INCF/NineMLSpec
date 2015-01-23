"""
This file contains the ConnectionRuleValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    AliasesAreNotRecursiveConnectionRuleValidator,
    NoUnresolvedSymbolsConnectionRuleValidator,
    NoDuplicatedObjectsConnectionRuleValidator,
    CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator)
from .namingconflicts import (
    LocalNameConflictsConnectionRuleValidator,
    DimensionNameConflictsConnectionRuleValidator)
from .ports import (
    PortConnectionsConnectionRuleValidator)
from .types import (
    TypesConnectionRuleValidator)


class ConnectionRuleValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesConnectionRuleValidator(componentclass)
        NoDuplicatedObjectsConnectionRuleValidator(componentclass)
        LocalNameConflictsConnectionRuleValidator(componentclass)
        DimensionNameConflictsConnectionRuleValidator(componentclass)
        AliasesAreNotRecursiveConnectionRuleValidator(componentclass)
        NoUnresolvedSymbolsConnectionRuleValidator(componentclass)
        PortConnectionsConnectionRuleValidator(componentclass)
        CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator(
            componentclass)
