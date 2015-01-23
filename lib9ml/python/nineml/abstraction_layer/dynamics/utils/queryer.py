"""
Definitions for the ComponentQuery Class

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
from nineml.utils import filter_expect_single
from ...componentclass.utils.queryer import ComponentQueryer


class DynamicsQueryer(ComponentQueryer):

    """
    DynamicsQueryer provides a way of adding methods to query a
    ComponentClass object, without polluting the class
    """

    def __init__(self, componentclass):
        """Constructor for the DynamicsQueryer"""
        self.componentclass = componentclass

    @property
    def ports(self):
        """Return an iterator over all the port (Event & Analog) in the
        componentclass"""
        return chain(super(DynamicsQueryer, self).ports,
                     self.componentclass.analog_ports,
                     self.componentclass.event_ports)

    # Find basic properties by name
    def regime(self, name=None,):
        """Find a regime in the componentclass by name"""
        assert isinstance(name, basestring)

        return filter_expect_single(self.componentclass.regimes,
                                    lambda r: r.name == name)

    # Query Ports:
    @property
    def event_send_ports(self):
        """Get the ``send`` EventPorts"""
        return sorted(self.componentclass.event_send_ports,
                      key=lambda p: p.name)

    @property
    def event_recv_ports(self):
        """Get the ``recv`` EventPorts"""
        return sorted(self.componentclass.event_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_reduce_ports(self):
        """Get the ``reduce`` AnalogPorts"""
        return sorted(self.componentclass.analog_reduce_ports,
                      key=lambda p: p.name)

    @property
    def analog_send_ports(self):
        """Get the ``send`` AnalogPorts"""
        return sorted(self.componentclass.analog_send_ports,
                      key=lambda p: p.name)

    @property
    def analog_recv_ports(self):
        """Get the ``recv`` AnalogPorts"""
        return sorted(self.componentclass.analog_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_ports_map(self):
        """Returns a map of names to |AnalogPort| objects"""
        return dict([(p.name, p) for p in self.componentclass.analog_ports])

    @property
    def event_ports_map(self):
        """Returns a map of names to |EventPort| objects"""
        return dict([(p.name, p) for p in self.componentclass.event_ports])

    @property
    def recurse_all_components(self):
        """
        Returns an iterator over this componentclass and all subcomponents
        """
        yield self.componentclass
        for subcomponent in self.componentclass.subnodes.values():
            for subcomp in subcomponent.query.recurse_all_components:
                yield subcomp
