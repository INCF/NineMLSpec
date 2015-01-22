"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ..utils import ComponentClassActionVisitor
from ..base import ComponentClass, Parameter
from ...expressions import Alias


class TypesComponentValidator(ComponentClassActionVisitor):

    def __init__(self, componentclass):
        super(TypesComponentValidator, self).__init__()
        self.visit(componentclass)

    def action_componentclass(self, component):
        assert isinstance(component, ComponentClass)

    def action_parameter(self, parameter):
        assert (isinstance(parameter, Parameter),
                "{} != {}".format(type(parameter), Parameter))

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)
