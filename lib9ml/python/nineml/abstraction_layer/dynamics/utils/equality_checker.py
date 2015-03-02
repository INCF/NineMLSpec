"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.utils import safe_dict
from ...componentclass.utils.equality_checker import (
    ComponentEqualityChecker, assert_equal,
    assert_equal_list)


class DynamicsEqualityChecker(ComponentEqualityChecker):

    @classmethod
    def check_equal_component(cls, comp1, comp2, strict_aliases):

        super(DynamicsEqualityChecker, cls).check_equal_component(
            comp1, comp2, strict_aliases)

        # Analog Ports: Check Modes & reduce ops:
        ap1Dict = safe_dict([(ap.name, ap) for ap in comp1.analog_ports])
        ap2Dict = safe_dict([(ap.name, ap) for ap in comp2.analog_ports])
        assert_equal_list(ap1Dict.keys(), ap2Dict.keys())
        for portname in ap1Dict.keys():
            assert_equal(ap1Dict[portname].mode, ap2Dict[portname].mode)
            assert_equal(ap1Dict[portname].operator,
                         ap2Dict[portname].operator)

        # Event Ports: Check Modes & reduce ops:
        ev1Dict = safe_dict([(ev.name, ev) for ev in comp1.event_ports])
        ev2Dict = safe_dict([(ev.name, ev) for ev in comp2.event_ports])
        assert_equal_list(ev1Dict.keys(), ev2Dict.keys())
        for portname in ev1Dict.keys():
            assert_equal(ev1Dict[portname].mode, ev2Dict[portname].mode)
            assert_equal(ev1Dict[portname].operator,
                         ev2Dict[portname].operator)

        # CHECK THE SUBNAMESPACES AND PORT CONNECTIONS
        # ------------------------------------------- #
        # Recurse over subnamespaces:
        assert_equal_list(comp1.subnodes.keys(), comp2.subnodes.keys())
        for subnamespace in comp1.subnodes.keys():
            subcomp1 = comp1.subnodes[subnamespace]
            subcomp2 = comp2.subnodes[subnamespace]
            cls.check_equal_component(subcomp1, subcomp2)

        # CHECK THE DYNAMICS
        # ------------------- #
        d1 = comp1.dynamics
        d2 = comp2.dynamics

        # State Variables:
        sv1Names = sorted([sv.name for sv in d1.state_variables])
        sv2Names = sorted([sv.name for sv in d2.state_variables])
        assert_equal_list(sv1Names, sv2Names)

        # Check Regimes:

        rgm1Dict = d1.regimes_map
        rgm2Dict = d2.regimes_map
        assert_equal_list(rgm1Dict.keys(), rgm2Dict.keys())
        for regime_name in rgm1Dict.keys():
            rgm1 = rgm1Dict[regime_name]
            rgm2 = rgm2Dict[regime_name]
            cls.check_equal_regime(rgm1, rgm2)

    @classmethod
    def check_equal_regime(cls, rgm1, rgm2):

        assert_equal(rgm1.name, rgm2.name)

        # Check the OnEvents:
        on_event1dict = safe_dict([(ev.src_port_name, ev)
                                   for ev in rgm1.on_events])
        on_event2dict = safe_dict([(ev.src_port_name, ev)
                                   for ev in rgm2.on_events])
        assert_equal_list(on_event1dict.keys(), on_event2dict.keys())
        for eventport in on_event1dict.keys():
            ev1 = on_event1dict[eventport]
            ev2 = on_event2dict[eventport]
            cls.check_equal_transitions(ev1, ev2)

        # Check the OnEvents:
        # [We use safe_dict, to ensure that we don't have any duplicate
        # condition.rhs ]
        on_condition1dict = safe_dict([(cond.trigger.rhs, cond)
                                       for cond in rgm1.on_conditions])
        on_condition2dict = safe_dict([(cond.trigger.rhs, cond)
                                       for cond in rgm2.on_conditions])
        assert_equal_list(on_condition1dict.keys(), on_condition2dict.keys())
        for condition_trigger_rhs in on_condition1dict.keys():
            on_cond1 = on_condition1dict[condition_trigger_rhs]
            on_cond2 = on_condition2dict[condition_trigger_rhs]
            cls.check_equal_transitions(on_cond1, on_cond2)

        # Check the TimeDerivatives:
        time_deriv1s = [(td.dependent_variable, td.rhs)
                        for td in rgm1.time_derivatives]
        time_deriv2s = [(td.dependent_variable, td.rhs)
                        for td in rgm2.time_derivatives]
        assert_equal_list(time_deriv1s, time_deriv2s)

    @classmethod
    def check_equal_transitions(cls, trans1, trans2):

        # Check they are connecting the same named regions:
        assert_equal(trans1.source_regime.name, trans2.source_regime.name)
        assert_equal(trans1.target_regime.name, trans2.target_regime.name)

        # State Assignments:
        sa1 = [(sa.lhs, sa.rhs) for sa in trans1.state_assignments]
        sa2 = [(sa.lhs, sa.rhs) for sa in trans2.state_assignments]
        assert_equal_list(sa1, sa2)

        # Output Events:
        op1 = [op.port_name for op in trans1.event_outputs]
        op2 = [op.port_name for op in trans2.event_outputs]
        assert_equal_list(sa1, sa2)
