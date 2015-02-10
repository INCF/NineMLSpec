"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.exceptions import NineMLRuntimeError
from collections import defaultdict
from base import PerNamespaceComponentValidator


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsComponentValidator(PerNamespaceComponentValidator):

    """
    Check for conflicts between Aliases, StateVariables, Parameters, and
    EventPorts, and analog input ports

    We do not need to check for comflicts with output AnalogPorts, since, these
    will use names.
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)
        self.symbols = defaultdict(list)
        self.visit(componentclass)

    def check_conflicting_symbol(self, namespace, symbol):
        if symbol in self.symbols[namespace]:
            err = 'Duplication of symbol found: %s in %s' % (symbol, namespace)
            raise NineMLRuntimeError(err)
        self.symbols[namespace].append(symbol)

    def action_parameter(self, parameter, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(namespace=namespace,
                                      symbol=parameter.name)

    def action_alias(self, alias, namespace, **kwargs):  # @UnusedVariable
        self.check_conflicting_symbol(namespace=namespace, symbol=alias.lhs)

    def action_constant(self, constant, namespace, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(namespace=namespace,
                                      symbol=constant.name)


class DimensionNameConflictsComponentValidator(PerNamespaceComponentValidator):

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)
        self.dimensions = {}
        self.visit(componentclass)

    def check_conflicting_dimension(self, dimension):
        try:
            if dimension != self.dimensions[dimension.name]:
                err = ("Duplication of dimension name '{}' for differing "
                       "dimensions ('{}', '{}')"
                       .format(dimension.name, dimension,
                               self.dimensions[dimension.name]))
                raise NineMLRuntimeError(err)
        except KeyError:
            self.dimensions[dimension.name] = dimension

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(parameter.dimension)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(constant.units.dimension)
