"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import os
from urllib2 import urlopen
from lxml import etree
from itertools import chain
from nineml.xmlns import E
from . import ComponentVisitor
from ...expressions import Alias
from nineml.abstraction_layer.componentclass.base import Parameter
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import expect_single, filter_expect_single
from nineml.xmlns import NINEML, MATHML, nineml_namespace
from nineml.exceptions import NineMLRuntimeError


class ComponentClassXMLLoader(object):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    class_types = ('Dynamics', 'RandomDistribution', 'ConnectionRule')

    def __init__(self, document=None):
        self.document = document

    def load_connectports(self, element):
        return element.get('source'), element.get('sink')

    @read_annotations
    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_alias(self, element):
        name = element.get("name")
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name, rhs=rhs)

    def load_single_internmaths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                print elements
                assert 0, 'Unexpected tags found'
        assert (len(element.findall(MATHML + "MathML")) +
                len(element.findall(NINEML + "MathInline"))) == 1
        if element.find(NINEML + "MathInline") is not None:
            mblock = expect_single(
                element.findall(NINEML + 'MathInline')).text.strip()
        elif element.find(MATHML + "MathML") is not None:
            mblock = self.load_mathml(
                expect_single(element.find(MATHML + "MathML")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError

    def _load_blocks(self, element, blocks):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in blocks)

        for t in element.iterchildren(tag=etree.Element):
            # Strip namespace
            tag = t.tag[len(NINEML):] if t.tag.startswith(NINEML) else t.tag
            if tag not in blocks:
                err = "Unexpected block tag: %s " % tag
                err += '\n Expected: %s' % ','.join(blocks)
                raise NineMLRuntimeError(err)
            loaded_objects[tag].append(self._get_loader(tag)(self, t))
        return loaded_objects

    def _get_loader(self, tag):
        try:
            loader = self.tag_to_loader[tag]
        except KeyError:
            try:
                loader = self.base_tag_to_loader[tag]
            except KeyError:
                assert False, "Did not finder loader for '{}' tag".format(tag)
        return loader

    @classmethod
    def read_class_type(cls, element):
        """
        Returns the name of the tag that defines the type of the ComponentClass
        """
        assert element.tag == NINEML + 'ComponentClass', \
            "Not a component class ('{}')".format(element.tag)
        class_type = expect_single(chain(*(element.findall(NINEML + t)
                                           for t in cls.class_types))).tag
        if class_type.startswith(NINEML):
            class_type = class_type[len(NINEML):]
        # TGC 1/15 Temporary hack until name is reverted (pending approval)
        if class_type == "RandomDistribution":
            class_type = "Distribution"
        return class_type

    base_tag_to_loader = {
        "Parameter": load_parameter,
        "Alias": load_alias,
    }


class ComponentClassXMLWriter(ComponentVisitor):

    @annotate_xml
    def visit_parameter(self, parameter):
        return E('Parameter',
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_alias(self, alias):
        return E('Alias', E("MathInline", alias.rhs), name=alias.lhs)


class ComponentClassXMLReader(object):

    """A class that can read |COMPONENTCLASS| objects from a NineML XML file.
    """
    loader = ComponentClassXMLLoader

    @classmethod
    def _load_include(cls, include_element, basedir, xml_node_filename_map):
        """Help function for replacing <Include> nodes.

        We replace the include node with the tree referenced
        by that filename. To do this, we load the file referenced,
        get  the elements in the root node, and copy them over to the place
        in the origintree where the originnode was. It is important that
        we preserve the order. Finy, we remove the <Include> element node.

        """

        filename = include_element.get('file')

        # Load the new XML
        included_xml = cls._load_nested_xml(
            filename=os.path.join(basedir, filename),
            xml_node_filename_map=xml_node_filename_map)

        # Insert it into the parent node:
        index_of_node = include_element.getparent().index(include_element)
        for i, newchild in enumerate(included_xml.getchildren()):
            include_element.getparent().insert(i + index_of_node, newchild)

        include_element.getparent().remove(include_element)

    @classmethod
    def _load_nested_xml(cls, filename, xml_node_filename_map):
        """ Load the XML, including   referenced Include files .

        We o populate a dictionary, ``xml_node_filename_map`` which maps each
        node to the name of the filename that it was originy in, so that when
        we load in single components from a file, which are hierachically and
        contain references to other components, we can find the components that
        were in the file specified.

        """

        if filename[:5] == "https":  # lxml only supports http and ftp
            doc = etree.parse(urlopen(filename))
        else:
            doc = etree.parse(filename)
        # Store the source filenames of  the nodes:
        for node in doc.getroot().getiterator():
            xml_node_filename_map[node] = filename

        root = doc.getroot()
        if root.nsmap[None] != nineml_namespace:
            errmsg = ("The XML namespace is not compatible with this version "
                      "of the NineML library. Expected {}, file contains {}")
            raise Exception(errmsg.format(nineml_namespace, root.nsmap[None]))

        # Recursively Load Include Nodes:
        for include_element in root.getiterator(tag=NINEML + 'Include'):
            cls._load_include(include_element=include_element,
                              basedir=os.path.dirname(filename),
                              xml_node_filename_map=xml_node_filename_map)
        return root

    @classmethod
    def read(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one
            ComponentClass definition, this parameter must be provided as a
            ``string`` specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object.
        """
        return cls.read_component(filename, component_name=component_name)

    @classmethod
    def read_component(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one
            ComponentClass definition, this parameter must be provided as a
            ``string`` specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object.
        """

        xml_node_filename_map = {}
        root = cls._load_nested_xml(
            filename=filename, xml_node_filename_map=xml_node_filename_map)

        loader = cls.loader()
        loader.load_componentclasses(
            xmlroot=root, xml_node_filename_map=xml_node_filename_map)

        if component_name is None:
            key_func = lambda c: loader.component_srcs[c] == filename
            return filter_expect_single(loader.components, key_func)

        else:
            key_func = lambda c: c.name == component_name
            return filter_expect_single(loader.components, key_func)

    @classmethod
    def read_components(cls, filename):
        """Reads a sever|COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :rtype: Returns a list of |COMPONENTCLASS| objects, for each
            <ComponentClass> node in the XML tree.

        """
        xml_node_filename_map = {}
        root = cls._load_nested_xml(filename, xml_node_filename_map)
        loader = cls.loader()
        loader.load_componentclasses(
            xmlroot=root, xml_node_filename_map=xml_node_filename_map)
        return loader.components
