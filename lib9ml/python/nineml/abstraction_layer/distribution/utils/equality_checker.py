"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.utils.equality_checker import (ComponentEqualityChecker,
                                                      assert_equal)


class DistributionEqualityChecker(ComponentEqualityChecker):
    """
    Currently not extended from base class but created for future checks
    """
    @classmethod
    def check_equal_component(cls, comp1, comp2, strict_aliases):

        super(DistributionEqualityChecker, cls).check_equal_component(
            comp1, comp2, strict_aliases)

        # Check the Distribution
        # --------------------- #
        d1 = comp1.distribution
        d2 = comp2.distribution

        assert_equal(d1.standard_library, d2.standard_library)
