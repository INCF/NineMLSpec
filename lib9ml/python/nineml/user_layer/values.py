# encoding: utf-8
from . import BaseULObject
from nineml.xmlns import E, NINEML
from nineml.annotations import read_annotations, annotate_xml
from nineml.utils import check_tag


class BaseValue(BaseULObject):
    pass


class SingleValue(BaseValue):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = "SingleValue"
    defining_attributes = ("value",)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "SingleValue(value={})".format(self.value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, str(self.value))

    @classmethod
    @read_annotations
    def from_xml(cls, element, _):
        check_tag(element, cls)
        return cls(float(element.text))


class ArrayValue(BaseValue):

    element_name = "ArrayValue"
    defining_attributes = ("rows",)

    def __init__(self, rows):
        self.rows = rows

    def __repr__(self):
        return "ArrayValue(with {} rows)".format(len(self.rows))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                len(self.rows) == len(other.rows) and
                all(r1 == r2 for r1, r2 in zip(self.rows, other.rows)))

    def __hash__(self):
        return hash(self.value)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, *[r.to_xml() for r in self.rows])

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        rows = []
        for row_xml in element.findall(NINEML + ArrayValueRow.element_name):
            rows.append(ArrayValueRow.from_xml(row_xml, document))
        sorted_rows = sorted(rows, key=lambda r: r.index)
        if any(r.index != i for i, r in enumerate(sorted_rows)):
            raise Exception("Missing or duplicate indices in ArrayValue rows "
                            "({})".format(', '.join(r.index
                                                    for r in sorted_rows)))
        return cls(sorted_rows)


class ArrayValueRow(BaseValue):

    element_name = "ArrayValueRow"
    defining_attributes = ("index", "value")

    def __init__(self, index, value):
        self.index = index
        self.value = value

    def __repr__(self):
        return "ArrayValueRow({}, {})".format(self.index, self.value)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                len(self.rows) == len(other.rows) and
                all(r1 == r2 for r1, r2 in zip(self.rows, other.rows)))

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, self.value, index=self.index)

    @classmethod
    @read_annotations
    def from_xml(cls, element, _):
        return cls(index=element.attrib["index"], value=element.text)


class ExternalArrayValue(BaseValue):

    element_name = "ExternalArrayValue"
    defining_attributes = ("url", "mimetype", "columnName")

    def __init__(self, url, mimetype, columnName):
        self.url = url
        self.mimetype = mimetype
        self.columnName = columnName

    def __repr__(self):
        return "ExternalArrayValue(with {} rows)".format(len(self.rows))

    def __eq__(self, other):
        return (self.url == other.url and self.mimetype == other.mimetype and
                self.columnName == other.columnName)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, url=self.url, mimetype=self.mimetype,
                 columnName=self.columnName)

    @classmethod
    @read_annotations
    def from_xml(cls, element, _):
        return cls(url=element.attrib["url"],
                   mimetype=element.attrib["mimetype"],
                   columnName=element.attrib["columnName"])


# class ComponentValue(BaseValue):
#
#     element_name = "ComponentValue"
#     defining_attributes = ("port", "component")
#
#     def __init__(self, component, port):
#         self.port = port
#         self.component = component
#
#     def __repr__(self):
#         return ("ComponentValue({} port of {} component)"
#                 .format(self.port, self.component.name))
#
#     def __eq__(self, other):
#         return (self.port == other.port and
#                 self.component == other.component)
#
#     @annotate_xml
#     def to_xml(self):
#         return E(self.element_name, self.component.to_xml(), port=self.url)
#
#     @classmethod
#     @read_annotations
#     def from_xml(cls, element, document):
#         comp_element = element.find(NINEML + 'Component')
#         if comp_element is None:
#             comp_element = element.find(NINEML + 'Reference')
#             if comp_element is None:
#                 raise Exception("Did not find component in ComponentValue")
#         component = Component.from_xml(comp_element, document)
#         return cls(component, port=element.attrib["port"])


class StringValue(BaseValue):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "Value"

    @classmethod
    @read_annotations
    def from_xml(cls, element):
        """
        Parse an XML ElementTree structure and return a string value.

        `element` - should be an ElementTree Element instance.
        """
        return element.text
