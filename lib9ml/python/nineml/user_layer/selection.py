from operator import itemgetter
from . import BaseULObject
from .component import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import expect_single, check_tag


def find_difference(this, that):
    assert isinstance(that, this.__class__)
    if this != that:
        if isinstance(this, BaseULObject):
            for attr in this.defining_attributes:
                a = getattr(this, attr)
                b = getattr(that, attr)
                if a != b:
                    if attr in this.children:
                        find_difference(a, b)
                    else:
                        errmsg = ("'%s' attribute of %s instance '%s' differs:"
                                  " '%r' != '%r'" % (attr,
                                                     this.__class__.__name__,
                                                     this.name, a, b))
                        if type(a) != type(b):
                            errmsg += "(%s, %s)" % (type(a), type(b))
                        raise Exception(errmsg)
        else:
            assert sorted(this.keys()) == sorted(
                that.keys())  # need to handle case of different keys
            for key in this:
                find_difference(this[key], that[key])


class Selection(BaseULObject):
    """
    Container for combining multiple populations or subsets thereof.

    **Arguments**:
        *name*
            a name for the selection
        *operation*
            a "selector" object which determines which neurons form part of the
            selection. Only :class:`Concatenate` is currently supported.
    """
    element_name = "Selection"
    defining_attributes = ('name', 'operation')

    def __init__(self, name, operation):
        super(Selection, self).__init__()
        self.name = name
        self.operation = operation

    def __repr__(self):
        return "Selection('%s', '%r')" % (self.name, self.operation)

    @write_reference
    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self.operation.to_xml(),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        # The only supported op at this stage
        op = Concatenate.from_xml(
            expect_single(element.findall(NINEML + 'Concatenate')), document)
        return cls(element.attrib['name'], op)

    def evaluate(self):
        assert isinstance(self.operation, Concatenate), \
            "Only concatenation is currently supported"
        return (item.user_layer_object for item in self.operation.items)


class Concatenate(BaseULObject):
    """
    Concatenates multiple :class:`Population`\s or :class:`Selection`\s
    together into a larger :class:`Selection`.
    """

    element_name = 'Concatenate'
    defining_attributes = ('items',)

    def __init__(self, *items):
        super(Concatenate, self).__init__()
        self._items = items

    def __repr__(self):
        return "Concatenate(%s)" % ", ".join(repr(item) for item in self.items)

    @property
    def items(self):
        """Return a list of the items in the concatenation."""
        # should this perhaps flatten to a list of Populations, where the
        # concatenation includes other Selections? or should that be a separate
        # method?
        return self._items

    @write_reference
    @annotate_xml
    def to_xml(self):
        def item_to_xml(item):
            if isinstance(item, Reference):
                return item.to_xml()
            else:
                return E.Reference(item.name)
        return E(self.element_name,
                 *[E.Item(item_to_xml(item), index=str(i))
                   for i, item in enumerate(self.items)])

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        # Load references and indices from xml
        items = ((e.attrib['index'],
                  Reference.from_xml(e.find(NINEML + 'Reference'), document))
                 for e in element.findall(NINEML + 'Item'))
        # Sort by 'index' attribute
        indices, items = zip(*sorted(items, key=itemgetter(0)))
        indices = [int(i) for i in indices]
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate indices found in Concatenate list ({})"
                             .format(indices))
        if indices[0] != 0:
            raise ValueError("Indices of Concatenate items must start from 0 "
                             "({})".format(indices))
        if indices[-1] != len(indices) - 1:
            raise ValueError("Missing indices in Concatenate items ({}), list "
                             "must be contiguous.".format(indices))
        return cls(*items)  # Strip off indices used to sort elements


# TGC 11/11/ This old implementation of Set (now called Selection) was copied
#            from nineml.user_layer.populations.py probably some of it is worth
#            salvaging as we look to implement some of this functionality for
#            version 2.0
#
# class Set(BaseULObject):
#     """
#     A set of network nodes selected from existing populations within the
#     Network.
#     """
#     element_name = "Selection"
#     defining_attributes = ("name", "condition")
#
#     def __init__(self, name, condition):
#         """
#         condition - instance of an Operator subclass
#         """
#         super(Property, self).__init__()
#         assert isinstance(condition, Operator)
#         self.name = name
#         self.condition = condition
#         self.populations = []
#         self.evaluated = False
#
#     def to_xml(self):
#         return E(self.element_name,
#                  E.select(self.condition.to_xml()),
#                  name=self.name)
#
#     @classmethod
#     def from_xml(cls, element, components):
#         check_tag(element, cls)
#         select_element = element.find(NINEML + 'select')
#         assert len(select_element) == 1
#         return cls(element.attrib["name"],
#                    Operator.from_xml(select_element.getchildren()[0]))
#
#     def evaluate(self, group):
#         if not self.evaluated:
#             selection = str(self.condition)
#             # look away now, this isn't pretty
#             subnet_pattern = re.compile(r'\(\("population\[@name\]"\) == '
#                                         r'\("(?P<name>[\w ]+)"\)\) and '
#                                         r'\("population\[@id\]" in '
#                                         r'"(?P<slice>\d*:\d*:\d*)"\)')
#             assembly_pattern = re.compile(r'\(\("population\[@name\]"\) == '
#                                           r'\("(?P<name1>[\w ]+)"\)\) or '
#                                           r'\(\("population\[@name\]"\) == '
#                                           r'\("(?P<name2>[\w ]+)"\)\)')
#             # this should be replaced by the use of ply, or similar
#             match = subnet_pattern.match(selection)
#             if match:
#                 name = match.groupdict()["name"]
#                 slice = match.groupdict()["slice"]
#                 self.populations.append((group.populations[name], slice))
#             else:
#                 match = assembly_pattern.match(selection)
#                 if match:
#                     name1 = match.groupdict()["name1"]
#                     name2 = match.groupdict()["name2"]
#                     self.populations.append((group.populations[name1], None))
#                     self.populations.append((group.populations[name2], None))
#                 else:
#                     raise Exception("Can't evaluate selection")
#             self.evaluated = True
#
#
# class SelectionOperator(Operator):
#     pass
#
#
# class Any(SelectionOperator):
#     element_name = "Any"
#
#     def __str__(self):
#         return "(" + ") or (".join(qstr(op) for op in self.operands) + ")"
#
#
# class All(SelectionOperator):
#     element_name = "All"
#
#     def __str__(self):
#         return "(" + ") and (".join(qstr(op) for op in self.operands) + ")"
#
#
# class Not(SelectionOperator):
#     element_name = "Not"
#
#     def __init__(self, *operands):
#         assert len(operands) == 1
#         SelectionOperator.__init__(self, *operands)
#
#
# class Comparison(Operator):
#
#     def __init__(self, value1, value2):
#         Operator.__init__(self, value1, value2)
#
#
# class Eq(Comparison):
#     element_name = "Equal"
#
#     def __str__(self):
#         return "(%s) == (%s)" % tuple(qstr(op) for op in self.operands)
#
#
# class In(Comparison):
#     element_name = "In"
#
#     def __init__(self, item, sequence):
#         Operator.__init__(self, item, sequence)
#
#     def __str__(self):
#         return "%s in %s" % tuple(qstr(op) for op in self.operands)
#
# class Operator(BaseULObject):
#     super(Property, self).__init__()
#     defining_attributes = ("operands",)
#     children = ("operands",)
#
#     def __init__(self, *operands):
#         self.operands = operands
#
#     def to_xml(self):
#         operand_elements = []
#         for c in self.operands:
#             if isinstance(c, (basestring, float, int)):
#                 operand_elements.append(E(StringValue.element_name, str(c)))
#             else:
#                 operand_elements.append(c.to_xml())
#         return E(self.element_name,
#                  *operand_elements)
#
#     @classmethod
#     def from_xml(cls, element):
#         if hasattr(cls, "element_name") and element.tag == (NINEML +
#                                                            cls.element_name):
#             dispatch = {
#                 NINEML + StringValue.element_name: StringValue.from_xml,
#                 NINEML + Eq.element_name: Eq.from_xml,
#                 NINEML + Any.element_name: Any.from_xml,
#                 NINEML + All.element_name: All.from_xml,
#                 NINEML + Not.element_name: Not.from_xml,
#                 NINEML + In.element_name: In.from_xml,
#             }
#             operands = []
#             for child in element.iterchildren():
#                 operands.append(dispatch[element.tag](child))
#             return cls(*operands)
#         else:
#             return {
#                 NINEML + Eq.element_name: Eq,
#                 NINEML + Any.element_name: Any,
#                 NINEML + All.element_name: All,
#                 NINEML + Not.element_name: Not,
#                 NINEML + StringValue.element_name: StringValue,
#                 NINEML + In.element_name: In,
#             }[element.tag].from_xml(element)
