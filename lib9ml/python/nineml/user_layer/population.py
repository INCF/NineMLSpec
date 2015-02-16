from itertools import chain
from . import BaseULObject
from .component import resolve_reference, write_reference, Component
from nineml import TopLevelObject
from nineml.xmlns import NINEML, E
from nineml.utils import expect_single, check_tag
from nineml.annotations import annotate_xml, read_annotations


class Population(BaseULObject, TopLevelObject):
    """
    A collection of spiking neurons all of the same type.

    **Arguments**:
        *name*
            a name for the population.
        *size*
            an integer, the size of neurons in the population
        *cell*
            a :class:`Component`, or :class:`Reference` to a component defining
            the cell type (i.e. the mathematical model and its
            parameterisation).
        *positions*
            TODO: need to check if positions/structure are in the v1 spec
    """
    element_name = "Population"
    defining_attributes = ("name", "size", "cell", "positions")

    def __init__(self, name, size, cell, positions=None):
        super(Population, self).__init__()
        self.name = name
        self.size = size
        self.cell = cell
        if positions is not None:
            assert isinstance(positions, PositionList)
        self.positions = positions

    def __str__(self):
        return ('Population "%s": %dx"%s" %s' %
                (self.name, self.size, self.cell.name, self.positions))

    def __repr__(self):
        return ("Population(name='{}', size={}, cell={}{})"
                .format(self.name, self.size, self.cell.name,
                        'positions={}'.format(self.positions)
                        if self.positions else ''))

    def get_components(self):
        """
        Return a list of all components used by the population.
        """
        components = []
        if self.cell:
            components.append(self.cell)
            components.extend(self.cell.properties.get_random_distributions())
            components.extend(
                self.cell.initial_values.get_random_distributions())
        if self.positions is not None:
            components.extend(self.positions.get_components())
        return components

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.get_components()])

    @write_reference
    @annotate_xml
    def to_xml(self):
        positions = [self.positions.to_xml()] if self.positions else []
        return E(self.element_name,
                 E.Size(str(self.size)),
                 E.Cell(self.cell.to_xml()),
                 *positions,
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        layout_elem = element.find(NINEML + 'Layout')
        kwargs = {}
        if layout_elem:
            kwargs['positions'] = Component.from_xml(layout_elem, document)
        cell = expect_single(element.findall(NINEML + 'Cell'))
        cell_component = cell.find(NINEML + 'Component')
        if cell_component is None:
            cell_component = cell.find(NINEML + 'Reference')
        return cls(name=element.attrib['name'],
                   size=int(element.find(NINEML + 'Size').text),
                   cell=Component.from_xml(cell_component, document), **kwargs)


class PositionList(BaseULObject, TopLevelObject):
    """
    Represents a list of network node positions. May contain either an explicit
    list of positions or a :class:`Structure` instance that can be used to
    generate positions.

    Either `positions` or `structure` should be provided. Providing both
    will raise an Exception.

    **Arguments**:
        *positions*
            a list of (x,y,z) tuples or a 3xN (Nx3?) numpy array.
        *structure*
            a :class:`Structure` component.
    """
    element_name = "Layout"
    defining_attributes = []

    def __init__(self, positions=[], structure=None):
        """
        Create a new PositionList.

        Either `positions` or `structure` should be provided. Providing both
        will raise an Exception.

        `positions` should be a list of (x,y,z) tuples or a 3xN (Nx3?) numpy
                    array.
        `structure` should be a Structure componentclass.
        """
        super(PositionList, self).__init__()
        if positions and structure:
            raise Exception("Please provide either positions or structure, "
                            "not both.")
        assert not isinstance(positions, Structure)
        self._positions = positions
        if isinstance(structure, Structure):
            self.structure = structure
        elif structure is None:
            self.structure = None
        else:
            raise Exception("structure is", structure)

    def __eq__(self, other):
        if self._positions:
            return self._positions == other._positions
        else:
            return self.structure == other.structure

    def __str__(self):
        if self.structure:
            return "positioned according to '%s'" % self.structure.name
        else:
            return "with explicit position list"

    def get_positions(self, population):
        """
        Return a list or 1D numpy array of (x,y,z) positions.
        """
        if self._positions:
            assert len(self._positions) == population.size
            return self._positions
        elif self.structure:
            return self.structure.generate_positions(population.size)
        else:
            raise Exception("Neither positions nor structure is set.")

    def get_components(self):
        if self.structure:
            return [self.structure]
        else:
            return []

    @write_reference
    @annotate_xml
    def to_xml(self):
        element = E(self.element_name)
        if self._positions:
            for pos in self._positions:
                x, y, z = pos
                element.append(E.position(x=str(x), y=str(y), z=str(z),
                                          units="um"))
        elif self.structure:
            element.append(E.structure(self.structure.name))
        else:
            raise Exception("Neither positions nor structure is set.")
        return element

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        if element is None:
            return None
        else:
            check_tag(element, cls)
            structure_element = element.find(NINEML + 'structure')
            if structure_element is not None:
                return cls(structure=document.resolve_ref(
                    structure_element, Structure))
            else:
                positions = [(float(p.attrib['x']), float(p.attrib['y']),
                              float(p.attrib['z']))
                             for p in element.findall(NINEML + 'position')]
                return cls(positions=positions)


def qstr(obj):
    if isinstance(obj, basestring):
        return '"%s"' % obj
    else:
        return obj.__str__()


class Structure(Component):

    """
    Component representing the structure of a network, e.g. 2D grid, random
    distribution within a sphere, etc.
    """
    abstraction_layer_module = 'Structure'

    def generate_positions(self, number):
        """
        Generate a size of node positions according to the network structure.
        """
        raise NotImplementedError

    @property
    def is_csa(self):
        return self.get_definition().__module__ == 'csa.geometry'  # probably need a better test @IgnorePep8

    def to_csa(self):
        if self.is_csa:
            return self.get_definition()  # e.g. lambda size: csa.random2d(size, *self.properties) @IgnorePep8
        else:
            raise Exception("Structure cannot be transformed to CSA geometry "
                            "function")
