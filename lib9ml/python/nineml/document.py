import os.path
from itertools import chain
from urllib import urlopen
from lxml import etree
from operator import and_
import itertools
import collections
from nineml.xmlns import NINEML, E
from nineml.annotations import annotate_xml, read_annotations, Annotations
import nineml.user_layer
import nineml.abstraction_layer
from . import BaseNineMLObject
from nineml.exceptions import NineMLRuntimeError


class Document(dict, BaseNineMLObject):
    """
    Loads and stores all top-level elements in a NineML file (i.e. any element
    that is able to sit directly within <NineML>...</NineML> tags). All
    elements are stored initially but only converted to lib9ml objects on
    demand so it doesn't matter which order they appear in the NineML file.
    """

    element_name = 'NineML'

    # Valid top-level NineML element names
    top_level_abstraction = ['Dimension', 'Unit', 'ComponentClass',
                             'Annotations']
    top_level_user = ['Component', 'PositionList',
                      'Population', 'Selection', 'Projection']

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls')

    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop('_url', None)
        # FIXME: should be able to take NineMLObjects read their names and
        #        populate the dictionary. Then kwargs could be reserved for
        #        other items.
        super(Document, self).__init__(*args, **kwargs)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []

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
        # This simplifies code in a few places where an optional
        # attribute refers to a name of an object which
        # should be resolved if present but be set to None if not.
        if name is None:
            return None
        try:
            elem = super(Document, self).__getitem__(name)
        except KeyError:
            raise KeyError("'{}' was not found in the NineML document {} ("
                           "elements in the document were '{}')."
                           .format(name, self.url or '',
                                   "', '".join(self.iterkeys())))
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
                if isinstance(o, nineml.user_layer.Component))

    @property
    def componentclasses(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.abstraction_layer.ComponentClass))

    @property
    def populations(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Population))

    @property
    def projections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Projection))

    @property
    def selections(self):
        return (o for o in self.itervalues()
                if isinstance(o, nineml.user_layer.Selection))

    @property
    def network_structures(self):
        return chain(self.populations, self.projections, self.selections)

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise Exception("Circular reference detected in '{}(name={})' "
                            "element. Resolution stack was:\n"
                            .format(unloaded.name,
                                    "\n".join('{}(name={})'.format(u.tag,
                                                                   u.name)
                                              for u in self._loading)))
        self._loading.append(unloaded)
        elem = unloaded.cls.from_xml(unloaded.xml, self)
        assert self._loading[-1] is unloaded
        self._loading.pop()
        self[unloaded.name] = elem
        return elem

    def _standardize_units_and_dimensions(self):
        """
        Updates the units and dimensions to match the ones currently used
        in the components/class and network structures
        """
        # Get complete set of units and dimensions across each item in the
        # document
        units = set(chain(*[c.units for c in self.components]))
        units.update(chain(*[p.units for p in self.populations]))
        units.update(chain(*[p.units for p in self.projections]))
        dimensions = set(chain(*[c.dimensions for c in self.componentclasses]))
        dimensions.update(u.dimension for u in units)
        # Delete unused units and dimensions from the document
        for k, o in self.items():
            if (isinstance(o, (nineml.abstraction_layer.Unit,
                               nineml.abstraction_layer.Dimension))
                    and o not in units and o not in dimensions):
                del self[k]
        # Add missing units and dimensions to the document
        for unit in units:
            if unit.name in self:
                if unit != self[unit.name]:
                    raise NineMLRuntimeError(
                        "Name of unit '{}' conflicts with existing object of "
                        "differring value or type '{}' and '{}'"
                        .format(unit.name, unit, self[unit.name]))
            self[unit.name] = unit
        for dimension in dimensions:
            if dimension.name in self:
                if dimension != self[dimension.name]:
                    raise NineMLRuntimeError(
                        "Name of dimension '{}' conflicts with existing object"
                        " of differring value or type '{}' and '{}'"
                        .format(dimension.name, dimension, self[unit.name]))
            self[dimension.name] = dimension
        # Standardize the units and dimensions used by the items in the
        # document, i.e. ensure that equal dimensions use the same name
        for compclass in self.componentclasses:
            compclass.standardize_unit_dimensions(reference_set=dimensions)
        for o in chain(self.components, self.populations, self.projections):
            o.standardize_units(reference_units=units,
                                reference_dimensions=dimensions)

    def to_xml(self):
        self._standardize_units_and_dimensions()
        return E(self.element_name,
                 *[c.to_xml(as_reference=False)
                   if isinstance(c, nineml.user_layer.component.BaseULObject)
                   else c.to_xml()
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
            if child.tag == NINEML + Annotations.element_name:
                assert annotations is None, "Multiple annotations tags found"
                annotations = Annotations.from_xml(child)
                continue
            elif child.tag in (NINEML + e for e in cls.top_level_user):
                child_cls = getattr(nineml.user_layer, child.tag[len(NINEML):])
            elif child.tag in (NINEML + e for e in cls.top_level_abstraction):
                child_cls = getattr(nineml.abstraction_layer,
                                    child.tag[len(NINEML):])
            else:
                top_level = itertools.chain(cls.top_level_abstraction,
                                            cls.top_level_user)
                raise Exception("Invalid top-level element '{}' found in "
                                "NineML document (valid elements are '{}')."
                                .format(child.tag, "', '".join(top_level)))
            # Units use 'symbol' as their unique identifier (from LEMS) all
            # other elements use 'name'
            name = child.attrib.get('name', child.attrib.get('symbol'))
            if name in elements:
                raise Exception("Duplicate identifier '{ob1}:{name}'in NineML "
                                "file '{url}'"
                                .format(name=name,
                                        ob1=elements[name].cls.element_name,
                                        ob2=child_cls.element_name,
                                        url=url or ''))
            elements[name] = cls._Unloaded(name, child, child_cls)
        document = cls(**elements)
        document.annotations = annotations
        return document


class BaseReference(BaseNineMLObject):

    """
    Base class for references to model components that are defined in the
    abstraction layer.
    """

    def __init__(self, name, document, url=None):
        self.url = url
        if self.url:
            if document.url is None:
                document = read(url, relative_to=os.getcwd())
            else:
                document = read(url, relative_to=os.path.dirname(document.url))
        self._referred_to = document[name]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return reduce(and_, (self._referred_to == other._referred_to,
                             self.url == other.url))

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self.component_name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(name="{}"{})'
                    .format(self.__class__.__name__, self._referred_to.name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    @annotate_xml
    def to_xml(self):
        kwargs = {'url': self.url} if self.url else {}
        element = E(self.element_name,
                    self._referred_to.name,
                    **kwargs)
        return element

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.text
        url = element.attrib.get("url", None)
        return cls(name, document, url)


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
        raise Exception("Could not parse XML file '{}'".format(url))
    root = xml.getroot()
    return load(root, url)


def write(document, filename):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    document.write(filename)
