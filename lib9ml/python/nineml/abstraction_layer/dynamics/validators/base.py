"""
This file contains the DynamicsValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    TimeDerivativesAreDeclaredDynamicsValidator,
    StateAssignmentsAreOnStateVariablesDynamicsValidator,
    AliasesAreNotRecursiveDynamicsValidator,
    NoUnresolvedSymbolsDynamicsValidator,
    RegimeGraphDynamicsValidator, NoDuplicatedObjectsDynamicsValidator,
    RegimeOnlyHasOneHandlerPerEventDynamicsValidator,
    CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator)
from .namingconflicts import (
    LocalNameConflictsDynamicsValidator,
    DimensionNameConflictsDynamicsValidator,
    DuplicateRegimeNamesDynamicsValidator)
from .ports import (
    EventPortsDynamicsValidator, OutputAnalogPortsDynamicsValidator,
    PortConnectionsDynamicsValidator)
from .types import (
    TypesDynamicsValidator)


class DynamicsValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesDynamicsValidator(componentclass)
        NoDuplicatedObjectsDynamicsValidator(componentclass)
        DuplicateRegimeNamesDynamicsValidator(componentclass)
        LocalNameConflictsDynamicsValidator(componentclass)
        DimensionNameConflictsDynamicsValidator(componentclass)
        EventPortsDynamicsValidator(componentclass)
        OutputAnalogPortsDynamicsValidator(componentclass)
        TimeDerivativesAreDeclaredDynamicsValidator(componentclass)
        StateAssignmentsAreOnStateVariablesDynamicsValidator(componentclass)
        AliasesAreNotRecursiveDynamicsValidator(componentclass)
        NoUnresolvedSymbolsDynamicsValidator(componentclass)
        PortConnectionsDynamicsValidator(componentclass)
        RegimeGraphDynamicsValidator(componentclass)
        RegimeOnlyHasOneHandlerPerEventDynamicsValidator(componentclass)
        CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(componentclass)
