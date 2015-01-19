import os.path
import unittest
from lxml.etree import _Element, ElementTree
from nineml import read
from nineml.abstraction_layer.distribution import (
    DistributionClass as ComponentClass)
import tempfile

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                            '..', '..', '..', 'catalog', 'randomdistributions')


class TestDistribution(unittest.TestCase):

    def test_load(self):
        document = read(os.path.join(examples_dir, 'normal.xml'))
        self.assertEquals(type(document['NormalDistribution']), ComponentClass)

    def test_to_xml(self):
        document = read(os.path.join(examples_dir, 'normal.xml'))
        comp_class = document['NormalDistribution']
        xml = comp_class.to_xml()
        self.assertEquals(_Element, type(xml))
        with tempfile.TemporaryFile() as f:
            ElementTree(xml).write(f, encoding="UTF-8", pretty_print=True,
                                   xml_declaration=True)
