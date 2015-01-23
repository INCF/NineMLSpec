# encoding: utf-8
from . import BaseULObject
from .component import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from collections import defaultdict
from nineml.user_layer.component import Component
from itertools import chain
import nineml.user_layer
from ..abstraction_layer import units as un
from nineml.utils import expect_single, expect_none_or_single, check_tag
from ..exceptions import NineMLRuntimeError
from .values import SingleValue
from .component import Quantity


class Projection(BaseULObject):
    """
    A collection of connections between two :class:`Population`\s.

    **Arguments**:
        *name*
            a name for this projection.
        *source*
            the presynaptic :class:`Population`.
        *destination*
            the postsynaptic :class:`Population`.
        *response*
            a `dynamics` :class:`Component` that defines the post-synaptic
            response.
        *plasticity*
            a `dynamics` :class:`Component` that defines the plasticity
            rule for the synaptic weight/efficacy.
        *connectivity*
            a `connection rule` :class:`Component` that defines
            an algorithm for wiring up the neurons.
        *delay*
            a :class:`Delay` object specifying the delay of the connections.
        *port_connections*
            a list of :class:`PortConnection` tuples `(sender, receiver,
            send_port, receive_port)` that define the connections between the 4
            components of the projection, 'source', 'destination', 'response',
            'plasticity'. 'sender' and 'receiver' must be one of these 4 names
            and 'send_port' and 'receive_port' must each be the name of
            one of the ports in the corresponding components.

    **Attributes**:

    Each of the arguments to the constructor is available as an attribute of
    the same name.

    """
    element_name = "Projection"
    defining_attributes = ("name", "source", "destination", "connectivity",
                           "response", "plasticity", "port_connections",
                           "delay")

    _component_roles = set(['source', 'destination', 'plasticity', 'response'])

    def __init__(self, name, source, destination, response,
                 plasticity, connectivity, delay, port_connections):
        """
        Create a new projection.
        """
        super(Projection, self).__init__()
        self.name = name
        self.source = source
        # When exporting to XML we use the reference instead of the object
        # maintaing the original format of the XML.
        if source.from_reference is None:
            source.from_reference = Reference(source.name,
                                               {source.name: source})
        self.destination = destination
        if destination.from_reference is None:
            destination.from_reference = Reference(
                destination.name, {destination.name: destination})
        self.response = response
        self.plasticity = plasticity
        self.connectivity = connectivity
        if isinstance(delay, tuple):
            value, units = delay
            delay = Delay(SingleValue(value), units)
        self.delay = delay
        self.port_connections = sorted(port_connections,
                                       key=lambda x: (x._send_role,
                                                      x._receive_role,
                                                      x.send_port,
                                                      x.receive_port))
        for pc in self.port_connections:
            pc.set_projection(self)
        self._check_port_connections()

    def __repr__(self):
        return ('Projection(name="{}", source={}, destination={}, '
                'connectivity={}, response={}{}, delay={}, '
                'with {} port-connections)'
                .format(self.name, repr(self.source), repr(self.destination),
                        repr(self.connectivity), repr(self.response),
                        ('plasticity={}'.format(repr(self.plasticity))
                         if self.plasticity else ''), repr(self.delay),
                        len(self.port_connections)))

    def _check_port_connections(self):
        for pc in self.port_connections:
            if pc.send_port in (p.name
                                for p in pc.send_class.analog_send_ports):
                if (pc.receive_port not in
                    (p.name
                     for p in chain(pc.receive_class.analog_receive_ports,
                                    pc.receive_class.analog_reduce_ports))):
                    msg = ("No analog receive port named '{}' in {} component,"
                           " '{}'.".format(pc.receive_port, pc._receive_role,
                                           pc.receive_class.name))
                    raise NineMLRuntimeError(msg)
            elif pc.send_port in (p.name
                                  for p in pc.send_class.event_send_ports):
                if (pc.receive_port not in
                     (p.name for p in pc.receive_class.event_receive_ports)):
                    msg = ("No event receive port named '{}' in {} component, "
                           "'{}'.".format(pc.receive_port, pc._receive_role,
                                           pc.receive_class.name))
                    raise NineMLRuntimeError(msg)
            else:
                msg = ("'{}' send port was not found in {} component, '{}'"
                       .format(pc.send_port, pc._send_role,
                               pc.send_class.name))
                raise NineMLRuntimeError(msg)

    def get_components(self):
        """
        Return a list of all components used by the projection.
        """
        components = []
        for name in ('connectivity', 'response', 'plasticity'):
            component = getattr(self, name)
            if component is not None:
                components.append(component)
        return components

    @property
    def units(self):
        return chain([self.delay.units],
                     *[c.units for c in self.get_components()])

    def standardize_units(self, reference_units=None,
                          reference_dimensions=None):
        for c in self.get_components():
            c.standardize_units(reference_units=reference_units,
                                reference_dimensions=reference_dimensions)
        try:
            std_unit = next(u for u in reference_units
                            if u == self.delay.units)
            self.delay.set_units(std_unit)
        except StopIteration:
            pass

    @write_reference
    @annotate_xml
    def to_xml(self):
        pcs = defaultdict(list)
        for pc in self.port_connections:
            pcs[pc._receive_role].append(
                E('From' + pc._send_role.capitalize(),
                  send_port=pc.send_port, receive_port=pc.receive_port))
        args = [E.Source(self.source.to_xml(), *pcs['source']),
                E.Destination(self.destination.to_xml(), *pcs['destination']),
                E.Connectivity(self.connectivity.to_xml()),
                E.Response(self.response.to_xml(), *pcs['response'])]
        if self.plasticity:
            args.append(E.Plasticity(self.plasticity.to_xml(),
                                     *pcs['plasticity']))
        args.append(self.delay.to_xml())
        return E(self.element_name, *args, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        # Get Name
        name = element.get('name')
        # Get Source
        e = expect_single(element.findall(NINEML + 'Source'))
        e = expect_single(e.findall(NINEML + 'Reference'))
        source = nineml.user_layer.Reference.from_xml(
            e, document).user_layer_object
        # Get Destination
        e = expect_single(element.findall(NINEML + 'Destination'))
        e = expect_single(e.findall(NINEML + 'Reference'))
        destination = nineml.user_layer.Reference.from_xml(
            e, document).user_layer_object
        # Get Response
        e = element.find(NINEML + 'Response')
        component = e.find(NINEML + 'Component')
        if component is None:
            component = e.find(NINEML + 'Reference')
        response = Component.from_xml(component, document)
        # Get Plasticity
        e = expect_none_or_single(element.findall(NINEML + 'Plasticity'))
        if e is not None:
            component = e.find(NINEML + 'Component')
            if component is None:
                component = e.find(NINEML + 'Reference')
            plasticity = Component.from_xml(component, document)
        else:
            plasticity = None
        # Get Connectivity
        e = element.find(NINEML + 'Connectivity')
        component = e.find(NINEML + 'Component')
        if component is None:
            component = e.find(NINEML + 'Reference')
        connectivity = Component.from_xml(component, document)
        # Get Delay
        delay = Delay.from_xml(
            expect_single(element.findall(NINEML + 'Delay')), document)
        # Get port connections by Loop through 'source', 'destination',
        # 'response', 'plasticity' tags and extracting the "From*" elements
        port_connections = []
        for receive_role in cls._component_roles:
            # Get element for component name
            e = element.find(NINEML + receive_role.capitalize())
            if e is not None:  # Plasticity is not required
                # Loop through all incoming port connections and add them to
                # list
                for sender_role in cls._component_roles:
                    pc_elems = e.findall(NINEML +
                                         'From' + sender_role.capitalize())
                    if sender_role == receive_role and pc_elems:
                        msg = ("{} port connection receives from itself in "
                               "Projection '{}'".format(name, name))
                        raise NineMLRuntimeError(msg)
                    if (sender_role is 'plasticity' and plasticity is None and
                         len(pc_elems)):
                        msg = ("{} port connection receives from plasticity, "
                               "which wasn't provided for Projection '{}'"
                               .format(receive_role, name))
                        raise NineMLRuntimeError(msg)
                    for pc in pc_elems:
                        port_connections.append(
                            PortConnection(sender_role, receive_role,
                                           pc.get('send_port'),
                                           pc.get('receive_port')))
        return cls(name=element.attrib["name"],
                   source=source,
                   destination=destination,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connectivity,
                   delay=delay,
                   port_connections=port_connections)


class Delay(Quantity):
    """
    Representation of the connection delay.

    **Arguments**:
        *value*
            a numerical value, array of such values, or a component which
            generates such values (e.g. a random number generator). Allowed
            types are :class:`int`, :class:`float`, :class:`SingleValue`,
            :class:`ArrayValue', :class:`ExternalArrayValue`,
            :class:`ComponentValue`.
        *units*
            a :class:`Unit` object representing the physical units of the
            value.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = 'Delay'

    def __init__(self, value, units):
        if units.dimension != un.time:
            raise Exception("Units for delay must be of the time dimension "
                            "(found {})".format(units))
        super(Delay, self).__init__(value, units)


class PortConnection(object):
    """
    Specifies the connection of a send port with a receive port between two
    :class:`Component`\s in a :class:`Projection`.

    **Arguments**:
        *sender*
           one of 'source', 'destination', 'plasticity' or 'response'.
        *receiver*
            one of 'source', 'destination', 'plasticity' or 'response'.
        *send_port*
            the name of a send port in the sender component.
        *receive_port*
            the name of a receive or reduce port in the receiver component.
    """

    def __init__(self, sender, receiver, send_port, receive_port):
        if sender not in Projection._component_roles:
            raise Exception("Sender must be one of '{}'"
                            .format("', '".join(Projection._component_roles)))
        if receiver not in Projection._component_roles:
            raise Exception("Receiver must be one of '{}'"
                            .format("', '".join(Projection._component_roles)))
        if sender == receiver:
            raise Exception("Sender and Receiver cannot be the same ('{}')"
                            .format(sender))
        if not isinstance(send_port, basestring):
            raise NineMLRuntimeError("invalid send port '{}'"
                                     .format(send_port))
        if not isinstance(receive_port, basestring):
            raise NineMLRuntimeError("invalid receive port '{}'"
                                     .format(receive_port))
        self._send_role = sender
        self._receive_role = receiver
        self.send_port = send_port
        self.receive_port = receive_port
        self._projection = None

    def __eq__(self, other):
        return (self._send_role == other._send_role and
                self._receive_role == other._receive_role and
                self.send_port == other.send_port and
                self.receive_port == other.receive_port)

    def __repr__(self):
        return ("PortConnection('{}', '{}', '{}', '{}')"
                .format(self._send_role, self._receive_role, self.send_port,
                        self.receive_port))

    def __hash__(self):
        return (hash(self._send_role) ^ hash(self._receive_role) ^
                hash(self.send_port) ^ hash(self.receive_port))

    def set_projection(self, projection):
        """docstring"""
        self._projection = projection

    @property
    def sender(self):
        """The sending component."""
        assert self._projection is not None, ("Projection not set on port "
                                              "connection")
        return getattr(self._projection, self._send_role)

    @property
    def receiver(self):
        """The receiving component."""
        assert self._projection is not None, ("Projection not set on port "
                                              "connection")
        return getattr(self._projection, self._receive_role)

    @property
    def send_class(self):
        """The class of the sending component."""
        return self._get_class(self.sender)

    @property
    def receive_class(self):
        """The class of the receiving component."""
        return self._get_class(self.receiver)

    def _get_class(self, comp):
        # Resolve ref
        if isinstance(comp, nineml.user_layer.Reference):
            comp = comp.user_layer_object
        # Get component class
        if isinstance(comp, nineml.user_layer.Population):
            comp_class = comp.cell.component_class
        elif isinstance(comp, nineml.user_layer.Component):
            comp_class = comp.component_class
        elif isinstance(comp, nineml.user_layer.Selection):
            # print ("Warning: port connections have not been checked for '{}'"
            #        " Selection".format(comp.name))
            # only implemented for Concatenate
            def resolve(item):   # doing this here is a hack, I think
                if isinstance(item, Reference):
                    return item.user_layer_object
                else:
                    return item
            comp_classes = {}
            for item in comp.operation.items:
                cc = resolve(item).cell.component_class
                # here we use equality of component class names, should really
                # use equality of component classes
                comp_classes[cc.name] = cc
            if len(comp_classes) > 1:
                raise Exception(
                    "Selection contains multiple component classes: {}"
                    .format(comp_classes))
            comp_class = comp_classes.values()[0]
        else:
            assert False, ("Invalid '{}' object in port connection"
                           .format(type(comp)))
        return comp_class
