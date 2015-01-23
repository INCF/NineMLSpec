"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from . import PerNamespaceComponentValidator
from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction_layer.componentclass.namespace import NamespaceAddress


class PortConnectionsComponentValidator(PerNamespaceComponentValidator):

    """Check that all the port connections point to a port, and that
    each send & recv port only has a single connection.
    """

    def __init__(self, componentclass):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=False)

        self.ports = defaultdict(list)
        self.portconnections = list()

        self.visit(componentclass)

        connected_recv_ports = set()

        # Check for duplicate connections in the
        # portconnections. This can only really happen in the
        # case of connecting 'send to reduce ports' more than once.
        seen_port_connections = set()
        for pc in self.portconnections:
            if pc in seen_port_connections:
                err = 'Duplicate Port Connection: %s -> %s' % (pc[0], pc[1])
                raise NineMLRuntimeError(err)
            seen_port_connections.add(pc)

        # Check each source and sink exist,
        # and that each recv port is connected at max once.
        for src, sink in self.portconnections:
            if src not in self.ports:
                raise NineMLRuntimeError(
                    'Unable to find port specified in connection: %s' %
                    (src))
            if self.ports[src].is_incoming():
                raise NineMLRuntimeError(
                    'Port was specified as a source, but is incoming: %s' %
                    (src))

            if sink not in self.ports:
                raise NineMLRuntimeError(
                    'Unable to find port specified in connection: %s' %
                    (sink))

            if not self.ports[sink].is_incoming():
                raise NineMLRuntimeError(
                    'Port was specified as a sink, but is not incoming: %s' %
                    (sink))

            if self.ports[sink].mode == 'recv':
                if self.ports[sink] in connected_recv_ports:
                    raise NineMLRuntimeError(
                        "Port was 'recv' and specified twice: %s" % (sink))
                connected_recv_ports.add(self.ports[sink])

    def _action_port(self, port, namespace):
        port_address = NamespaceAddress.concat(namespace, port.name)
        if port_address in self.ports:
            raise NineMLRuntimeError(
                'Duplicated Name for port found: %s' % port_address)
        self.ports[port_address] = port

    def action_componentclass(self, componentclass, namespace):
        for src, sink in componentclass.portconnections:
            full_src = NamespaceAddress.concat(namespace, src)
            full_sink = NamespaceAddress.concat(namespace, sink)

            # print 'Adding Port:',full_src
            # print 'Adding Port:',full_sink
            self.portconnections.append((full_src, full_sink))
