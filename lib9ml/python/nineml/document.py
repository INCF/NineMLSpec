import os.path
from itertools import chain
from urllib import urlopen
from lxml import etree
import collections
from nineml.xmlns import NINEML, E
from nineml.annotations import Annotations
from . import BaseNineMLObject
from nineml.exceptions import NineMLRuntimeError, NineMLMissingElementError
from nineml import TopLevelObject


class Document(dict, BaseNineMLObject):
    """
    Loads and stores all top-level elements in a NineML file (i.e. any element
    that is able to sit directly within <NineML>...</NineML> tags). All
    elements are stored initially but only converted to lib9ml objects on
    demand so it doesn't matter which order they appear in the NineML file.
    """

    element_name = 'NineML'

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls')

    def __init__(self, *elements, **kwargs):
        self.url = kwargs.pop('_url', None)
        dict.__init__(self, **kwargs)
        for element in elements:
            self.add(element)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []

    def add(self, element):
        try:
            if not isinstance(element, TopLevelObject):
                raise NineMLRuntimeError(
                    "Could not add {} as it is not a document level NineML "
                    "object ('{}') ".format(element.element_name,
                                            "', '".join(self.top_level_types)))
        except AttributeError:
            raise NineMLRuntimeError("Could not add {} as it is not a NineML "
                                     "object".format(element))
        if element.name in self:
            raise NineMLRuntimeError(
                "Could not add element '{}' as an element with that name "
                "already exists in the document".format(element.name))
        self[element.name] = element

    def __eq__(self, other):
        # Ensure all objects are loaded
        self.values()
        other.values()
        # Use the parent dictionary class equality
        return (super(Document, self).__eq__(other) and
                self.url == other.url)

    def __getitem__(self, name):
        """
        Returns the element referenced by the given name
        """
        if name is None:
            # This simplifies code in a few places where an optional
            # attribute refers to a name of an object which
            # should be resolved if present but be set to None if not.
            return None
        try:
            elem = super(Document, self).__getitem__(name)
        except KeyError:
            raise NineMLMissingElementError(
                "'{}' was not found in the NineML document {} (elements in the"
                " document were '{}')."
                .format(name, self.url or '', "', '".join(self.iterkeys())))
        # Load (lazily) the element from the xml description
        if isinstance(elem, self._Unloaded):
            elem = self._load_elem_from_xml(elem)
        return elem

    def itervalues(self):
        for v in super(Document, self).itervalues():
            if isinstance(v, self._Unloaded):
                v = self._load_elem_from_xml(v)
            yield v

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for k, v in super(Document, self).iteritems():
            if isinstance(v, self._Unloaded):
                v = self._load_elem_from_xml(v)
            yield k, v

    def items(self):
        return list(self.iteritems())

    @property
    def components(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Component))  # @UndefinedVariable @IgnorePep8

    @property
    def componentclasses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.abstraction_layer.ComponentClass))  # @UndefinedVariable @IgnorePep8

    @property
    def populations(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Population))  # @UndefinedVariable @IgnorePep8

    @property
    def projections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Projection))  # @UndefinedVariable @IgnorePep8

    @property
    def selections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Selection))  # @UndefinedVariable @IgnorePep8

    @property
    def network_structures(self):
        return chain(self.populations, self.projections, self.selections)

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise NineMLRuntimeError(
                "Circular reference detected in '{}(name={})' element. "
                "Resolution stack was:\n"
                .format(unloaded.cls.__name__, unloaded.name,
                        "\n".join('{}(name={})'.format(u.cls.__name__, u.name)
                                  for u in self._loading)))
        self._loading.append(unloaded)
        elem = unloaded.cls.from_xml(unloaded.xml, self)
        assert self._loading[-1] is unloaded
        self._loading.pop()
        self[unloaded.name] = elem
        return elem

    def standardize_units(self):
        """
        Standardized the units into a single set (no duplicates). Used to avoid
        naming conflicts when writing to file.
        """
        # Get the set of all units and dimensions that are used in the document
        # Note that Dimension & Unit objects are equal even if they have
        # different names so when this set is traversed the dimension/unit will
        # be substituted for the first equivalent dimension/unit.
        all_units = set(chain(*[o.all_units for o in self.itervalues()]))
        all_dimensions = set(chain(
            [u.dimension for u in all_units],
            *[o.all_dimensions for o in self.itervalues()]))
        # Delete unused units from the document
        for k, o in self.items():
            if ((isinstance(o, nineml.abstraction_layer.Unit) and
                 o not in all_units) or
                (isinstance(o, nineml.abstraction_layer.Dimension) and
                 o not in all_dimensions)):
                del self[k]
        # Add missing units and dimensions to the document
        for unit in all_units:
            if unit.name in self:
                if unit != self[unit.name]:
                    raise NineMLRuntimeError(
                        "Name of unit '{}' conflicts with existing object of "
                        "differring value or type '{}' and '{}'"
                        .format(unit.name, unit, self[unit.name]))
            self[unit.name] = unit
        for dimension in all_dimensions:
            if dimension.name in self:
                if dimension != self[dimension.name]:
                    raise NineMLRuntimeError(
                        "Name of dimension '{}' conflicts with existing object"
                        " of differring value or type '{}' and '{}'"
                        .format(dimension.name, dimension, self[unit.name]))
            self[dimension.name] = dimension
        # Replace units and dimensions with those in the superset
        for obj in self.itervalues():
            for a in obj.attributes_with_dimension:
                try:
                    std_dim = next(d for d in all_dimensions
                                   if d == a.dimension)
                except StopIteration:
                    assert False, \
                        ("Did not find matching dimension in supposed superset"
                         " of dimensions")
                a.set_dimension(std_dim)
            for a in obj.attributes_with_units:
                try:
                    std_units = next(u for u in all_units
                                     if u == a.units)
                except StopIteration:
                    assert False, \
                        ("Did not find matching unit in supposed superset"
                         " of units")
                a.set_units(std_units)

    def to_xml(self):
        self.standardize_units()
        return E(
            self.element_name,
            *[c.to_xml(as_reference=False)
              if isinstance(c, nineml.user_layer.BaseULObject) else c.to_xml()
              for c in self.itervalues()])

    def write(self, filename):
        doc = self.to_xml()
        with open(filename, 'w') as f:
            etree.ElementTree(doc).write(f, encoding="UTF-8",
                                         pretty_print=True,
                                         xml_declaration=True)

    @classmethod
    def from_xml(cls, element, url=None):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ('{}')".format(element.tag))
        # Initialise the document
        elements = {'_url': url}
        # Loop through child elements, determine the class needed to extract
        # them and add them to the dictionary
        annotations = None
        for child in element.getchildren():
            if child.tag.startswith(NINEML):
                element_name = child.tag[len(NINEML):]
                if element_name == Annotations.element_name:
                    assert annotations is None, \
                        "Multiple annotations tags found"
                    annotations = Annotations.from_xml(child)
                    continue
                try:
                    child_cls = getattr(nineml.user_layer, element_name)
                except AttributeError:
                    try:
                        child_cls = getattr(nineml.abstraction_layer,
                                            element_name)
                    except AttributeError:
                        raise NineMLRuntimeError(
                            "Did not find matching NineML class for '{}' "
                            "element".format(element_name))
                if not issubclass(child_cls, TopLevelObject):
                    raise NineMLRuntimeError(
                        "'{}' is not a valid top-level NineML element"
                        .format(element_name))
            else:
                raise NotImplementedError(
                    "Cannot load '{}' element (extensions not implemented)"
                    .format(child.tag))
            # Units use 'symbol' as their unique identifier (from LEMS) all
            # other elements use 'name'
            name = child.attrib.get('name', child.attrib.get('symbol'))
            if name in elements:
                raise NineMLRuntimeError(
                    "Duplicate identifier '{ob1}:{name}'in NineML file '{url}'"
                    .format(name=name, ob1=elements[name].cls.element_name,
                            ob2=child_cls.element_name, url=url or ''))
            elements[name] = cls._Unloaded(name, child, child_cls)
        document = cls(**elements)
        document.annotations = annotations
        return document


def load(root_element, read_from=None):
    """
    Loads the lib9ml object model from a root lxml.etree.Element

    root_element -- the 'NineML' etree.Element to load the object model from
    read_from    -- specifies the url, which the xml should be considered to
                    have been read from in order to resolve relative references
    """
    return Document.from_xml(root_element, url=read_from)


def read(url, relative_to=None):
    """
    Read a NineML file and parse its child elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if url.startswith('.') and relative_to:
        url = os.path.abspath(os.path.join(relative_to, url))
    try:
        if not isinstance(url, file):
            try:
                f = urlopen(url)
                xml = etree.parse(f)
            except:  # FIXME: Need to work out what exceptions urlopen raises
                raise Exception("Could not read URL '{}'".format(url))
            finally:
                f.close()
        else:
            xml = etree.parse(url)
    except:  # FIXME: Need to work out what exceptions etree raises
        raise NineMLRuntimeError("Could not parse XML file '{}'".format(url))
    root = xml.getroot()
    return load(root, url)


def write(document, filename):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(document, Document):
        document = Document(document)
    document.write(filename)

import nineml.user_layer
import nineml.abstraction_layer
