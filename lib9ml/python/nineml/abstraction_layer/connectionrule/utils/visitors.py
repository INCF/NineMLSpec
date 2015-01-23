"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import ComponentActionVisitor


class ConnectionRuleActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(ConnectionRuleActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        if componentclass.connectionrule:
            componentclass.connectionrule.accept_visitor(self, **kwargs)

    def visit_connectionrule(self, connectionrule, **kwargs):
        self.action_connectionrule(connectionrule, **kwargs)
        nodes = connectionrule.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_connectionrule(self, connectionrule, **kwargs):  # @UnusedVariable
        self.check_pass()
