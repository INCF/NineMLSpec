"""
Definitions for the ComponentQuery Class

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
from ...componentclass.utils.queryer import ComponentQueryer


class DistributionQueryer(ComponentQueryer):

    """
    DistributionQueryer provides a way of adding methods to query a
    ComponentClass object, without polluting the class
    """

    def __init__(self, componentclass):
        """Constructor for the DistributionQueryer"""
        self.componentclass = componentclass

    @property
    def ports(self):
        """Return an iterator over all the port (Event & Analog) in the
        componentclass"""
        # TODO: Distribution-specific ports to go here
        return chain(super(DistributionQueryer, self).ports, [])
