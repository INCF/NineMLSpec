"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.validators import (
    LocalNameConflictsComponentValidator,
    DimensionNameConflictsComponentValidator)
from . import BaseDistributionValidator
from ..utils.visitors import DistributionActionVisitor


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsDistributionValidator(
        LocalNameConflictsComponentValidator,
        DistributionActionVisitor):

    """
    Check for conflicts between Aliases, Parameters, and Ports
    """
    pass


class DimensionNameConflictsDistributionValidator(
        DimensionNameConflictsComponentValidator,
        BaseDistributionValidator):
    pass
