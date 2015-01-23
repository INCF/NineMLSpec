"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentRenameSymbol, ComponentClonerVisitor)
from .visitors import DistributionActionVisitor


class DistributionExpandPortDefinition(DistributionActionVisitor,
                                       ComponentExpandPortDefinition):

    pass


class DistributionExpandAliasDefinition(DistributionActionVisitor,
                                        ComponentExpandAliasDefinition):

    """
    An action-class that walks over a componentclass, and expands an alias in
    Aliases
    """

    pass


class DistributionRenameSymbol(DistributionActionVisitor,
                               ComponentRenameSymbol):

    """ Can be used for:
    Aliases
    """
    pass


class DistributionClonerVisitor(ComponentClonerVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        ccn = componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters],
            distribution=(
                componentclass.distribution.accept_visitor(self, **kwargs)
                if componentclass.distribution else None))
        return ccn

    def visit_distribution(self, distribution, **kwargs):
        return distribution.__class__(
            aliases=[
                a.accept_visitor(self, **kwargs)
                for a in distribution.aliases])
