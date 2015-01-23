"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentRenameSymbol, ComponentClonerVisitor)
from .visitors import ConnectionRuleActionVisitor


class ConnectionRuleExpandPortDefinition(ConnectionRuleActionVisitor,
                                       ComponentExpandPortDefinition):

    pass


class ConnectionRuleExpandAliasDefinition(ConnectionRuleActionVisitor,
                                        ComponentExpandAliasDefinition):

    """
    An action-class that walks over a componentclass, and expands an alias in
    Aliases
    """

    pass


class ConnectionRuleRenameSymbol(ConnectionRuleActionVisitor,
                               ComponentRenameSymbol):

    """ Can be used for:
    Aliases
    """
    pass


class ConnectionRuleClonerVisitor(ComponentClonerVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        ccn = componentclass.__class__(
            name=componentclass.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in componentclass.parameters],
            connectionrule=(
                componentclass.connectionrule.accept_visitor(self, **kwargs)
                if componentclass.connectionrule else None))
        return ccn

    def visit_connectionrule(self, connectionrule, **kwargs):
        return connectionrule.__class__(
            aliases=[
                a.accept_visitor(self, **kwargs)
                for a in connectionrule.aliases])
