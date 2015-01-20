
"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from . import BaseALObject
from nineml.xmlns import NINEML
from nineml.annotations import read_annotations, annotate_xml
from nineml.utility import filter_discrete_types, ensure_valid_identifier
from .units import dimensionless, Dimension


class ComponentClass(BaseALObject):
    """Base class for ComponentClasses in different 9ML modules."""

    element_name = 'ComponentClass'

    @annotate_xml
    def to_xml(self):
        exec('from nineml.abstraction_layer.{}.writers import XMLWriter'
             .format(self.writer_name))
        return XMLWriter().visit(self)  # @UndefinedVariable

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        if element.find(NINEML + 'Dynamics') is not None:
            module_name = 'dynamics'
        elif element.find(NINEML + 'ConnectionRule') is not None:
            module_name = 'connectionrule'
        elif element.find(NINEML + 'RandomDistribution') is not None:
            module_name = 'random'
        exec('from nineml.abstraction_layer.{}.xml import XMLLoader'
             .format(module_name))
        return XMLLoader(document).load_componentclass(element)  # @UndefinedVariable @IgnorePep8

    def __init__(self, name, parameters=None):
        BaseALObject.__init__(self)
        self._name = name
        # Turn any strings in the parameter list into Parameters:
        if parameters is None:
            parameters = []
        else:
            param_types = (basestring, Parameter)
            param_td = filter_discrete_types(parameters, param_types)
            params_from_strings = [Parameter(s) for s in param_td[basestring]]
            parameters = param_td[Parameter] + params_from_strings
        self._parameters = dict((p.name, p) for p in parameters)

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return self._parameters.itervalues()

    @property
    def parameters_map(self):
        """Returns the underlying parameters dictionary containing the local
          |Parameter| objects"""
        return self._parameters

    @property
    def parameter_names(self):
        return self._parameters.iterkeys()

    def parameter(self, name):
        return self._parameters[name]

    @property
    def dimensions(self):
        return set(p.dimension for p in self._attributes_with_dimension)

    @property
    def _attributes_with_dimension(self):
        return self.parameters

    def standardize_unit_dimensions(self, reference_set=None):
        """
        Replaces dimension objects with ones from a reference set so that their
        names do not conflict when writing to file
        """
        if reference_set is None:
            reference_set = self.dimensions
        for p in self._attributes_with_dimension:
            try:
                std_dim = next(d for d in reference_set if d == p.dimension)
            except StopIteration:
                continue
            p.set_dimension(std_dim)


class Parameter(BaseALObject):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('name', 'dimension')

    def __init__(self, name, dimension=None):
        """Parameter Constructor

        `name` -- The name of the parameter.
        """
        name = name.strip()
        ensure_valid_identifier(name)

        self._name = name
        self._dimension = dimension if dimension is not None else dimensionless
        assert isinstance(self._dimension, Dimension), (
            "dimension must be None or a nineml.Dimension instance")

    def __eq__(self, other):
        return self.name == other.name and self.dimension == other.dimension

    @property
    def name(self):
        """Returns the name of the parameter"""
        return self._name

    @property
    def dimension(self):
        """Returns the dimensions of the parameter"""
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("Parameter({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)
                        if self.dimension else ''))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_parameter(self, **kwargs)
