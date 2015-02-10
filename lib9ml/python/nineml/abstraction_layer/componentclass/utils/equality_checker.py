"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import types


class UnequalException(Exception):

    def __init__(self, o1, o2, msg=""):
        Exception.__init__(self)
        self.msg = msg
        self.o1 = o1
        self.o2 = o2

    def __str__(self):
        s = self.msg
        s += '\nO1: %s' % str(self.o1)
        s += '\nO2: %s' % str(self.o2)
        return s


def assert_equal(o1, o2, msg=''):
    if not isinstance(o1, (types.NoneType, basestring)):
        print o1, o2
        assert not (o1 is o2)
    assert type(o1) == type(o2)
    assert isinstance(o1, (basestring, types.NoneType))
    if o1 == o2:
        return
    raise UnequalException(o1, o2, msg)


def assert_equal_list(o1, o2, msg='', do_sort=True):
    assert o1 is not o2
    assert type(o1) == type(o2)
    assert isinstance(o1, (tuple, list))
    if do_sort and sorted(o1) == sorted(o2):
        return
    raise UnequalException(sorted(o1), sorted(o2), msg)


class ComponentEqualityChecker(object):

    @classmethod
    def check_equal(cls, comp1, comp2, strict_aliases=True):
        """Forwarding Function :Easier Interface"""
        cls.check_equal_component(comp1, comp2, strict_aliases=strict_aliases)

    @classmethod
    def check_equal_component(cls, comp1, comp2, strict_aliases):

        # Check the component names are equal:
        assert_equal(comp1.name, comp2.name, 'Component Names')

        # CHECK THE INTERFACE:
        # -------------------#
        # Parameters:
        p1Names = sorted([p.name for p in comp1.parameters])
        p2Names = sorted([p.name for p in comp2.parameters])
        assert_equal_list(p1Names, p2Names)

        # Port Connections:
        # Tuples are comparable, so lets make 2 lists of tuples and compare
        # them:
        pc1 = [(src.loctuple, sink.loctuple)
               for (src, sink) in comp1.portconnections]
        pc2 = [(src.loctuple, sink.loctuple)
               for (src, sink) in comp2.portconnections]
        assert_equal_list(pc1, pc2)

        # CHECK THE DISTRIBUTION
        # ------------------- #
        d1 = comp1.distribution
        d2 = comp2.distribution

        # Check Aliases:
        assert strict_aliases
        a1 = [(a.lhs, a.rhs) for a in d1.aliases]
        a2 = [(a.lhs, a.rhs) for a in d2.aliases]
        assert_equal_list(a1, a2)

        # Check Constants:
        assert_equal_list(comp1.constants, comp2.constants)
