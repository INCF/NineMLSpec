"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .cloner import DistributionExpandPortDefinition
from ...componentclass.utils.modifiers import ComponentModifier


class DistributionModifier(ComponentModifier):

    """Utility classes for modifying components"""

    _ExpandPortDefinition = DistributionExpandPortDefinition
