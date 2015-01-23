"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import ComponentActionVisitor


class DistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(DistributionActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        if componentclass.distribution:
            componentclass.distribution.accept_visitor(self, **kwargs)

    def visit_distribution(self, distribution, **kwargs):
        self.action_distribution(distribution, **kwargs)
        nodes = distribution.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_distribution(self, distribution, **kwargs):  # @UnusedVariable
        self.check_pass()
