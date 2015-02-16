"""
This file defines the Port classes used in NineML

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from abc import ABCMeta
from . import BaseALObject
from nineml.abstraction_layer.units import dimensionless
from nineml.utils import ensure_valid_identifier
from nineml.exceptions import NineMLRuntimeError


class Port(BaseALObject):

    """
    Base class for |AnalogSendPorts|, |AnalogReceivePorts|,
    |EventSendPorts|, |EventReceivePorts| and |AnalogReducePorts|.

    In general, a port has a ``name``, which can be used to reference it,
    and a ``mode``, which specifies whether it sends or receives information.

    Generally, a send port can be connected to receive port to allow different
    components to communicate.

    |AnalogSendPorts| and |EventSendPorts| can be connected to any number of
    |AnalogReceivePorts| and |EventReceivePorts| respectively, but each
    |AnalogReceivePort| and |EventReceivePort| can only be connected to a
    single |AnalogSendPort| and |EventSendPort| respectively.

    """
    __metaclass__ = ABCMeta  # Ensure abstract base class isn't instantiated

    defining_attributes = ('name',)
    index_key = 'Port'

    def __init__(self, name):
        """ Port Constructor.

        `name` -- The name of the port, as a `string`
        """
        name = name.strip()
        ensure_valid_identifier(name)
        self._name = name

    @property
    def name(self):
        """The name of the port, local to the current component"""
        return self._name

    def __repr__(self):
        classstring = self.__class__.__name__
        return "{}('{}')".format(classstring, self.name)


class DimensionedPort(Port):
    """DimensionedPort

    A |DimensionedPort| is the base class for ports with dimensions (e.g.
    Analog and Property ports).
    """

    defining_attributes = ('name', 'dimension')

    __metaclass__ = ABCMeta  # Ensure abstract base class isn't instantiated

    def __init__(self, name, dimension=None):
        super(DimensionedPort, self).__init__(name)
        self._dimension = dimension if dimension is not None else dimensionless # TODO: This needs checking @IgnorePep8

    @property
    def dimension(self):
        """The dimension of the port"""
        return self._dimension

    def set_dimension(self, dimension):
        assert self.dimension == dimension,\
            "Dimensions should not change, only change of names is permitted"
        self._dimension = dimension

    def __repr__(self):
        classstring = self.__class__.__name__
        return "{}('{}', dimension='{}')".format(classstring, self.name,
                                                 self.dimension)


class SendPort(object):
    """SendPort

    Base class for sending ports
    """
    mode = "send"  # FIXME: This is here for legacy unittest I think (TGC 1/15)

    def is_incoming(self):
        return False

    def can_connect_to(self, port):
        return isinstance(port, ReceivePort) and self.type_matches(port)


class ReceivePort(object):
    """ReceivePort

    Base class for receiving ports
    """
    mode = "recv"  # FIXME: This is here for legacy unittest I think (TGC 1/15)

    def is_incoming(self):
        return True

    def can_connect_to(self, port):
        return isinstance(port, SendPort) and self.type_matches(port)


class AnalogPort(DimensionedPort):
    """AnalogPort

    An |AnalogPort| represents a continuous input or output to/from a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.
    """

    def type_matches(self, port):
        return isinstance(port, AnalogPort)


class EventPort(Port):
    """EventPort

    An |EventPort| is a port that can transmit and receive discrete events at
    points in time. For example, an integrate-and-fire could 'send' events to
    notify other components that it had fired; or synapses could receive events
    to notify them to provide current to a post-synaptic neuron.
    """

    def type_matches(self, port):
        return isinstance(port, AnalogPort)


class AnalogSendPort(AnalogPort, SendPort):
    """AnalogSendPort

    An |AnalogSendPort| represents a continuous output from a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.

    """

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogsendport(self, **kwargs)


class AnalogReceivePort(AnalogPort, ReceivePort):
    """AnalogReceivePort

    An |AnalogReceivePort| represents a continuous input to a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.

    """

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogreceiveport(self, **kwargs)


class EventSendPort(EventPort, SendPort):
    """EventSendPort

    An |EventSendPort| is a port that can transmit discrete events at
    points in time. For example, an integrate-and-fire could 'send' events to
    notify other components that it had fired.
    """

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventsendport(self, **kwargs)


class EventReceivePort(EventPort, ReceivePort):
    """EventReceivePort

    An |EventReceivePort| is a port that can receive discrete events at
    points in time. For example, synapses could receive events
    to notify them to provide current to a post-synaptic neuron.
    """

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventreceiveport(self, **kwargs)


class AnalogReducePort(AnalogPort, ReceivePort):
    """AnalogReducePort

    An |AnalogReducePort| represents a collection of continuous inputs to a
    Component from a common type of input that can be reduced into a single
    input. For example, or the currents provided by a collection of
    ion-channels.

    .. note::

        Currently support ``reduce_op`` s are: ``+``.

    """
    mode = "reduce"
    _reduce_op_map = {'add': '+', '+': '+', }

    def __init__(self, name, dimension=None, reduce_op='+'):
        if reduce_op not in self._reduce_op_map.keys():
            err = ("%s('%s')" + "specified undefined reduce_op: '%s'") %\
                  (self.__class__.__name__, name, str(reduce_op))
            raise NineMLRuntimeError(err)
        super(AnalogReducePort, self).__init__(name, dimension)
        self._reduce_op = reduce_op

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogreduceport(self, **kwargs)

    @property
    def reduce_op(self):
        return self._reduce_op

    def __repr__(self):
        classstring = self.__class__.__name__
        return ("{}('{}', dimension='{}', op='{}')"
                .format(classstring, self.name, self.dimension,
                        self.reduce_op))
