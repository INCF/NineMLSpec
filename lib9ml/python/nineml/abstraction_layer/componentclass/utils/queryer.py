"""
Definitions for the ComponentQuery Class

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__all__ = ['ComponentQueryer']


class ComponentQueryer(object):

    """
    ComponentQueryer provides a way of adding methods to query a
    ComponentClass object, without polluting the class
    """

    def __init__(self, componentclass):
        """Constructor for the ComponentQueryer"""
        self.componentclass = componentclass

    @property
    def ports(self):
        """Return an iterator over all the port (Event & Analog) in the
        componentclass"""
        return []  # TODO: Common ports to be added here.

    @property
    def parameters_map(self):
        """Returns a map of names to |Parameter| objects"""
        return dict([(p.name, p) for p in self.componentclass.parameters])

    @property
    def constants_map(self):
        """Returns a map of names to |Parameter| objects"""
        return dict([(c.name, c) for c in self.componentclass.constants])

    # Used by the flattening code:
    def get_fully_qualified_port_connections(self):
        """Used by the flattening code.

        This method returns a list of tuples of the
        the fully-qualified port connections.
        For example,
        [("a.b.C","d.e.F"),("g.h.I","j.k.L"), ..., ("u.W","x.y.Z") ]
        but note that it is not ``string`` objects that are returned, but
        NamespaceAddress objects.
        """
        namespace = self.componentclass.get_node_addr()
        conns = []
        for src, sink in self.componentclass.portconnections:
            src_new = namespace.get_subns_addr(src)
            sink_new = namespace.get_subns_addr(sink)
            conns.append((src_new, sink_new))
        return conns
