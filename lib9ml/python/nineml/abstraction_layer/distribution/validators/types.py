"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.validators.types import TypesComponentValidator
from ..base import Distribution
from ..utils.visitors import DistributionActionVisitor


class TypesDistributionValidator(DistributionActionVisitor,
                                 TypesComponentValidator):

    def action_distribution(self, distribution):
        assert isinstance(distribution, Distribution)
