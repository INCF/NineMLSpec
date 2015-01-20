"""
Python module for reading and writing 9ML abstraction layer files in XML
format.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from .. import BaseNineMLObject


class BaseALObject(BaseNineMLObject):

    """
    Base class for abstraction layer classes
    """
    pass


import dynamics
import expressions
import connectionrule
import distribution
import units
import ports
from .base import Parameter, ComponentClass, NamespaceAddress
from .expressions import Alias, Expression
from .dynamics import (DynamicsClass, Regime,
                       EventOut, StateAssignment, TimeDerivative,
                       Dynamics, OnCondition,
                       Condition, StateVariable, OnEvent, On,
                       EventOut as OutputEvent)  # For old tests
from .ports import (AnalogSendPort, AnalogReceivePort,
                    AnalogReducePort, EventSendPort,
                    EventReceivePort, AnalogPort, EventPort, Port)
from .dynamics import flatten as flattening  # For old tests
from .connectionrule import ConnectionRuleClass
from .distribution import DistributionClass
from .units import Unit, Dimension
