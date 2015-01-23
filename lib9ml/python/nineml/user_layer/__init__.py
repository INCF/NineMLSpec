# encoding: utf-8
"""
Python module for reading/writing 9ML user layer files in XML format.

Functions
---------

    parse - read a 9ML file in XML format and parse it into a Model instance.

Classes
-------
    Model
    Definition
    Component
        SpikingNodeType
        SynapseType
        CurrentSourceType
        Structure
        ConnectionRule
        ConnectionType
        RandomDistribution
    Parameter
    PropertySet
    Value
    Network
    Population
    PositionList
    Projection
    Selection
    Operator
        Any
        All
        Not
        Comparison
        Eq
        In


:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.

"""
from .. import BaseNineMLObject


class BaseULObject(BaseNineMLObject):

    """
    Base class for user layer classes
    """

    def __init__(self):
        super(BaseULObject, self).__init__()
        self.from_reference = None

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name


from .network import Network
from .population import Population, PositionList, Structure
from .selection import Selection, Concatenate
from .projection import Projection, PortConnection, Delay
from .component import (PropertySet, Property, Component, Definition,
                        Prototype, DynamicsComponent, ConnectionRuleComponent,
                        DistributionComponent, resolve_reference,
                        write_reference, Reference, InitialValue,
                        InitialValueSet)
