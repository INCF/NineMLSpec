import os.path
import unittest
from lxml.etree import _Element, ElementTree
from nineml import read
from nineml.abstraction_layer.connectionrule import (
    ConnectionRuleClass)
import tempfile

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                            '..', '..', '..', 'catalog', 'connectionrules')


class TestConnectionRule(unittest.TestCase):

    def test_load(self):
        document = read(os.path.join(examples_dir, 'AllToAll.xml'))
        self.assertEquals(type(document['AllToAll']),
                          ConnectionRuleClass)

    def test_to_xml(self):
        document = read(os.path.join(examples_dir, 'AllToAll.xml'))
        comp_class = document['AllToAll']
        xml = comp_class.to_xml()
        self.assertEquals(_Element, type(xml))
        with tempfile.TemporaryFile() as f:
            ElementTree(xml).write(f, encoding="UTF-8", pretty_print=True,
                                   xml_declaration=True)
