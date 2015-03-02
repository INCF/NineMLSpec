"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"
from itertools import chain
from operator import and_
import collections


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self):
        self.annotations = None

    def __eq__(self, other):
        return reduce(
            and_, [isinstance(other, self.__class__) or
                   isinstance(self, other.__class__)] +
            [getattr(self, name) == getattr(other, name)
             for name in self.__class__.defining_attributes])

    def __ne__(self, other):
        return not self == other

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        raise NotImplementedError(
            "Derived class '{}' has not overriden accept_visitor method."
            .format(self.__class__.__name__))

    def find_mismatch(self, other, indent='  '):
        """
        A function used for debugging where two NineML objects differ
        """
        if not indent:
            result = ("Mismatch between '{}' types:"
                      .format(self.__class__.__name__))
        else:
            result = ''
        if not (isinstance(other, self.__class__) or
                isinstance(self, other.__class__)):
            result += "mismatch in type"
        for attr_name in self.__class__.defining_attributes:
            self_attr = getattr(self, attr_name)
            other_attr = getattr(other, attr_name)
            if self_attr != other_attr:
                result += "\n{}Attribute '{}': ".format(indent, attr_name)
                result += self._unwrap_mismatch(self_attr, other_attr,
                                                indent + '  ')
        return result

    @classmethod
    def _unwrap_mismatch(cls, s, o, indent):
        result = ''
        if isinstance(s, BaseNineMLObject):
            result += s.find_mismatch(o, indent=indent + '  ')
        elif isinstance(s, dict):
            if set(s.keys()) != set(o.keys()):
                result += ('keys do not match ({} and {})'
                           .format(set(s.keys()), set(o.keys())))
            else:
                for k in s:
                    if s[k] != o[k]:
                        result += "\n{}Key '{}':".format(indent + '  ', k)
                        result += cls._unwrap_mismatch(s[k], o[k],
                                                       indent + '  ')
        elif isinstance(s, list):
            if len(s) != len(o):
                result += 'differ in length ({} to {})'.format(len(s), len(o))
            else:
                for i, (s_elem, o_elem) in enumerate(zip(s, o)):
                    if s_elem != o_elem:
                        result += "\n{}Index {}:".format(indent + '  ', i)
                        result += cls._unwrap_mismatch(s_elem, o_elem,
                                                       indent + '  ')
        else:
            result += "{} != {}".format(s, o)
        return result


class TopLevelObject(object):

    @property
    def attributes_with_dimension(self):
        return []  # To be overridden in derived classes

    @property
    def attributes_with_units(self):
        return []  # To be overridden in derived classes

    @property
    def all_units(self):
        return [a.units for a in self.attributes_with_units]

    @property
    def all_dimensions(self):
        return [a.dimension for a in self.attributes_with_dimension]

    def write(self, fname):
        """
        Writes the top-level NineML object to file in XML.
        """
        write(self, fname)  # Calls nineml.document.Document.write


import abstraction_layer
import user_layer
import exceptions
from abstraction_layer import Unit, Dimension
from document import read, write, load, Document
