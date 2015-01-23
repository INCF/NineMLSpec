"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.validators.ports import (
    PortConnectionsComponentValidator)
from ..utils.visitors import ConnectionRuleActionVisitor


class PortConnectionsConnectionRuleValidator(
        ConnectionRuleActionVisitor,
        PortConnectionsComponentValidator):

    """Check that all the port connections point to a port, and that
    each send & recv port only has a single connection.
    """
    pass
