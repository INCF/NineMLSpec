# encoding: utf-8
from itertools import chain
from lxml import etree
from abc import ABCMeta
from nineml.reference import BaseReference
from nineml.exceptions import (
    NineMLUnitMismatchError, NineMLRuntimeError, NineMLMissingElementError)
from nineml.xmlns import nineml_namespace
from operator import and_
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from nineml.utils import expect_single, check_tag, check_units
from ..abstraction_layer.units import Unit, unitless
from .values import SingleValue, ArrayValue, ExternalArrayValue
from . import BaseULObject
from nineml.document import Document
from nineml import TopLevelObject
from os import path


class Reference(BaseReference):
    """
    A reference to a NineML user layer object previously defined or defined
    elsewhere.

    **Arguments**:
        *name*
            The name of a NineML object which already exists, or which is
            defined in a separate XML file.
        *document*
            A dictionary or :class:`Document` object containing the object
            being referred to, if the object already exists.
        *url*
            If the object is defined in a separate XML file, the URL
            of the file.

    """
    element_name = "Reference"

    def __init__(self, name, document, url=None):
        """
        docstring needed

        `name`     -- a name of an existing componentclass to refer to
        `document` -- a Document object containing the top-level
                      objects in the current file
        `url`      -- a url of the file containing the exiting componentclass
        """
        super(Reference, self).__init__(name, document, url)
        if not isinstance(self._referred_to, BaseULObject):
            msg = ("Reference points to a non-user-layer object '{}'"
                   .format(self._referred_to.name))
            raise NineMLRuntimeError(msg)
        self._referred_to.from_reference = self

    @property
    def user_layer_object(self):
        """The object being referred to."""
        return self._referred_to


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, document):
        if element.tag == NINEML + Reference.element_name:
            reference = Reference.from_xml(element, document)
            ul_object = reference.user_layer_object
        else:
            assert element.tag == NINEML + cls.element_name
            ul_object = from_xml(cls, element, document)
        return ul_object
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, as_reference=True):
        if self.from_reference is not None and as_reference:
            xml = self.from_reference.to_xml()
        else:
            xml = to_xml(self)
        return xml
    return unresolving_to_xml


class Component(BaseULObject, TopLevelObject):
    """
    Base class for model components.

    A :class:`Component` may be regarded as a parameterized instance of a
    :class:`~nineml.abstraction_layer.ComponentClass`.

    A componentclass may be created either from a
    :class:`~nineml.abstraction_layer.ComponentClass`  together with a set
    of properties (parameter values), or by cloning then modifying an
    existing componentclass (the prototype).

    *Arguments*:
        `name`:
             a name for the componentclass.
        `definition`:
             the URL of an abstraction layer componentclass class definition,
             a :class:`Definition` or a :class:`Prototype` instance.
        `properties`:
             a dictionary containing (value,units) pairs or a
             :class:`PropertySet` for the componentclass's properties.
        `initial_values`:
            a dictionary containing (value,units) pairs or a
            :class:`PropertySet` for the componentclass's state variables.

    """
    __metaclass__ = ABCMeta  # Abstract base class

    element_name = "Component"
    defining_attributes = ('name', 'component_class', 'properties')
    children = ("Property", "Definition", 'Prototype')

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, definition, properties={}, initial_values={}):
        """
        Create a new componentclass with the given name, definition and
        properties, or create a prototype to another componentclass that will
        be resolved later.
        """
        super(Component, self).__init__()
        self.name = name
        if isinstance(definition, basestring):
            definition = Definition(
                name=path.basename(definition).replace(".xml", ""),
                document=Document(_url=definition),
                url=definition)
        elif not (isinstance(definition, Definition) or
                  isinstance(definition, Prototype)):
            raise ValueError("'definition' must be either a 'Definition' or "
                             "'Prototype' element")
        self._definition = definition
        if isinstance(properties, PropertySet):
            self._properties = properties
        elif isinstance(properties, dict):
            self._properties = PropertySet(**properties)
        else:
            raise TypeError("properties must be a PropertySet or a dict")
        if isinstance(initial_values, InitialValueSet):
            self._initial_values = initial_values
        elif isinstance(initial_values, dict):
            self._initial_values = InitialValueSet(**initial_values)
        else:
            raise TypeError("initial_values must be an InitialValueSet or a "
                            "dict, not a %s" % type(initial_values))
        self.check_properties()
        try:
            self.check_initial_values()
        except AttributeError:  # 'check_initial_values' is only in dynamics
            pass

    @property
    def component_class(self):
        """
        Returns the componentclass class from the definition object or the
        prototype's definition, or the prototype's prototype's definition, etc.
        depending on how the componentclass is defined.
        """
        defn = self._definition
        while not isinstance(defn, Definition):
            defn = defn.componentclass._definition
        return defn.component_class

    @property
    def properties(self):
        """
        The set of componentclass properties (parameter values).
        """
        # Recursively retrieves properties defined in prototypes and updates
        # them with properties defined locally
        props = PropertySet()
        if isinstance(self._definition, Prototype):
            props.update(self._definition.componentclass.properties)
        props.update(self._properties)
        return props

    @property
    def initial_values(self):
        """
        The set of initial values for the state variables of the
        componentclass.
        """
        # Recursively retrieves initial values defined in prototypes and
        # updates them with properties defined locally
        vals = InitialValueSet()
        if isinstance(self._definition, Prototype):
            vals.update(self._definition.componentclass.initial_values)
        vals.update(self._initial_values)
        return vals

    @property
    def attributes_with_units(self):
        return set(p for p in chain(self.properties.values(),
                                    self.initial_values.values())
                   if p.units is not None)

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self.name) ^
                hash(self.component_class) ^ hash(self.properties))

    def __repr__(self):
        return ('%s(name="%s", componentclass="%s")' %
                (self.__class__.__name__, self.name,
                 self.component_class.name))

    def diff(self, other):
        d = []
        if self.name != other.name:
            d += ["name: %s != %s" % (self.name, other.name)]
        if self.definition != other.definition:
            d += ["definition: %s != %s" % (self.definition, other.definition)]
        if self.properties != other.properties:
            d += ["properties: %s != %s" % (self.properties, other.properties)]
        return "\n".join(d)

    def get_definition(self):
        if not self._definition.componentclass:
            self._definition.retrieve()
        return self._definition.componentclass

    def check_properties(self):
        # First check the names
        properties = set(self.properties.iterkeys())
        parameters = set(p.name for p in self.component_class.parameters)
        msg = []
        diff_a = properties.difference(parameters)
        diff_b = parameters.difference(properties)
        if diff_a:
            msg.append("User properties contains the following parameters "
                       "that are not present in the definition: %s" %
                       ",".join(diff_a))
        if diff_b:
            msg.append("Definition contains the following parameters that are "
                       "not present in the user properties: %s" %
                       ",".join(diff_b))
        if msg:
            # need a more specific type of Exception
            raise Exception(". ".join(msg))
        # Check dimensions match
        for param in self.component_class.parameters:
            prop_units = self.properties[param.name].units
            prop_dimension = prop_units.dimension
            param_dimension = param.dimension
            if prop_dimension != param_dimension:
                err = ("Dimensions for '{}' parameter don't match, "
                       "componentclass class '{}', componentclass '{}'."
                       .format(param.name, param_dimension.name,
                               prop_dimension.name))
                raise NineMLUnitMismatchError(err)

    @write_reference
    @annotate_xml
    def to_xml(self):
        """
        docstring missing, although since the decorators don't
        preserve the docstring, it doesn't matter at the moment.
        """
        props_and_initial_values = (self._properties.to_xml() +
                                    [iv.to_xml()
                                     for iv in self.initial_values.values()])
        element = E(self.element_name,
                    self._definition.to_xml(),
                    *props_and_initial_values,
                    name=self.name)
        return element

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        """docstring missing"""
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.attrib.get("name", None)
        properties = PropertySet.from_xml(
            element.findall(NINEML + Property.element_name), document)
        initial_values = InitialValueSet.from_xml(
            element.findall(NINEML + InitialValue.element_name), document)
        definition_element = element.find(NINEML + Definition.element_name)
        if definition_element is not None:
            definition = Definition.from_xml(definition_element, document)
        else:
            prototype_element = element.find(NINEML + "Prototype")
            if prototype_element is None:
                raise Exception("A componentclass must contain either a "
                                "defintion or a prototype")
            definition = Prototype.from_xml(prototype_element, document)
        return cls(name, definition, properties,
                       initial_values=initial_values)

    @property
    def used_units(self):
        return set(p.units for p in self.properties.itervalues())

    def write(self, file):  # @ReservedAssignment
        self.standardize_units()
        xml = [self.to_xml()]
        xml.extend(chain(*((u.to_xml(), u.dimension.to_xml())
                            for u in self.used_units)))
        doc = E.NineML(*xml, xmlns=nineml_namespace)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)


class Definition(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Definition"

    @property
    def component_class(self):
        return self._referred_to


class Prototype(BaseReference):

    element_name = "Prototype"

    @property
    def componentclass(self):
        return self._referred_to


class Quantity(BaseULObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a componentclass that generates
    numbers, e.g. a RandomDistribution instance.
    """
    __metaclass__ = ABCMeta  # Abstract base class

    defining_attributes = ("name", "value", "units")

    def __init__(self, value, units=None):
        if not isinstance(value, (int, float, SingleValue, ArrayValue,
                                  ExternalArrayValue)):
            raise Exception("Invalid type '{}' for value, can be one of "
                            "'Value', 'Reference', 'Component', 'ValueList', "
                            "'ExternalValueList'"
                            .format(value.__class__.__name__))
        if units is None:
            units = unitless
        if not isinstance(units, Unit):
            raise Exception("Units ({}) must of type <Unit>".format(units))
        super(Quantity, self).__init__()
        if isinstance(value, (int, float)):
            value = SingleValue(value)
        self._value = value
        self.units = units

    def __hash__(self):
        return hash(self.value) ^ hash(self.units)

    def is_single(self):
        return isinstance(self._value, SingleValue)

    def is_random(self):
        return False

    def is_array(self):
        return (isinstance(self._value, ArrayValue) or
                isinstance(self._value, ExternalArrayValue))

    @property
    def value(self):
        if self.is_single():
            return self._value.value
        else:
            raise NineMLRuntimeError("Cannot access single value for array or "
                                     "componentclass type")

    @property
    def quantity(self):
        """The value of the parameter (magnitude and units)."""
        return (self.value, self.units)

    @property
    def value_array(self):
        if self.is_array():
            raise NotImplementedError
        else:
            raise NineMLRuntimeError("Cannot access value array for "
                                     "componentclass or single value types")

    @property
    def random_distribution(self):
        if self.is_random():
            return self._value.componentclass
        else:
            raise NineMLRuntimeError("Cannot access random distribution for "
                                     "componentclass or single value types")

    def set_units(self, units):
        if units.dimension != self.units.dimension:
            raise NineMLRuntimeError(
                "Can't change dimension of quantity from '{}' to '{}'"
                .format(self.units.dimension, units.dimension))
        self.units = units

    def __repr__(self):
        units = self.units.name
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return ("{}(value={}, units={})"
                .format(self.element_name, self.value, units))

    def __eq__(self, other):
        # FIXME: obviously we should resolve the units, so 0.001 V == 1 mV,
        #        could use python-quantities package to do this if we are
        #        okay with the dependency
        return isinstance(other, self.__class__) and \
            reduce(and_, (self.value == other.value,
                          self.units == other.units))

    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self._value.to_xml(),
                 units=self.units.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        if element.find(NINEML + 'SingleValue') is not None:
            value = SingleValue.from_xml(
                expect_single(element.findall(NINEML + 'SingleValue')),
                document)
        elif element.find(NINEML + 'ArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        elif element.find(NINEML + 'ExternalArrayValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        elif element.find(NINEML + 'ComponentValue') is not None:
            value = ArrayValue.from_xml(
                expect_single(element.findall(NINEML + 'ArrayValue')),
                document)
        else:
            raise Exception(
                "Did not find recognised value tag in property (found {})"
                .format(', '.join(c.tag for c in element.getchildren())))
        units_str = element.attrib.get('units')
        try:
            units = document[units_str]
        except KeyError:
            raise NineMLMissingElementError(
                "Did not find definition of '{}' units in the current document."
                .format(units_str))
        return cls(value=value, units=units)


class Property(Quantity):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a componentclass that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "Property"

    def __init__(self, name, value, units=None):
        super(Property, self).__init__(value, units)
        self.name = name

    def __hash__(self):
        return hash(self.name) ^ super(Property, self).__hash__()

    def __eq__(self, other):
        return self.name == other.name and super(Property, self).__eq__(other)

    def __repr__(self):
        units = self.units.name
        if u"µ" in units:
            units = units.replace(u"µ", "u")
        return ("{}(name={}, value={}, units={})"
                .format(self.element_name, self.name, self.value, units))

    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self._value.to_xml(),
                 name=self.name,
                 units=self.units.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        quantity = Quantity.from_xml(element, document)
        try:
            name = element.get('name')
        except KeyError:
            raise Exception("Property did not have a name")
        return cls(name=name, value=quantity.value, units=quantity.units)


class InitialValue(Property):

    """
    temporary, longer-term plan is to use SEDML or something similar
    """
    element_name = "Initial"


class PropertySet(dict):

    """
    Container for the set of properties for a componentclass.
    """

    def __init__(self, *properties, **kwproperties):
        """
        `*properties` - should be Property instances
        `**kwproperties` - should be name=(value,units)
        """
        dict.__init__(self)
        for prop in properties:
            self[prop.name] = prop  # should perhaps do a copy
        for name, (value, units) in kwproperties.items():
            self[name] = Property(name, value, units)

    def __hash__(self):
        return hash(tuple(self.items()))

    def __repr__(self):
        return "PropertySet(%s)" % dict(self)

    def complete(self, other_property_set):
        """
        Pull properties from another property set into this one, if they do
        not already exist in this one.
        """
        for name, parameter in other_property_set.items():
            if name not in self:
                self[name] = parameter  # again, should perhaps copy

    def get_random_distributions(self):
        return [p.value for p in self.values() if p.is_random()]

    def to_xml(self):
        # serialization is in alphabetical order
        return [self[name].to_xml() for name in sorted(self.keys())]

    @classmethod
    def from_xml(cls, elements, document):
        properties = []
        for parameter_element in elements:
            properties.append(Property.from_xml(parameter_element, document))
        return cls(*properties)


class InitialValueSet(PropertySet):

    def __init__(self, *ivs, **kwivs):
        """
        `*ivs` - should be InitialValue instances
        `**kwivs` - should be name=(value,units)
        """
        dict.__init__(self)
        for iv in ivs:
            self[iv.name] = iv  # should perhaps do a copy
        for name, (value, units) in kwivs.items():
            self[name] = InitialValue(name, value, units)

    def __repr__(self):
        return "InitialValueSet(%s)" % dict(self)

    @classmethod
    def from_xml(cls, elements, document):
        initial_values = []
        for iv_element in elements:
            initial_values.append(InitialValue.from_xml(iv_element,
                                                        document))
        return cls(*initial_values)


class Dynamics(Component):

    def check_initial_values(self):
        for var in self.definition.componentclass.state_variables:
            try:
                initial_value = self.initial_values[var.name]
            except KeyError:
                raise Exception("Initial value not specified for %s" %
                                var.name)
            check_units(initial_value.units, var.dimension)


class ConnectionRule(Component):
    """
    docstring needed
    """
    pass


class Distribution(Component):
    """
    Component representing a random number distribution, e.g. normal, gamma,
    binomial.

    *Example*::

        example goes here
    """
    pass
