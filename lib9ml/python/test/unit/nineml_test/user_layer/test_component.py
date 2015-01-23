import os.path
import unittest
from nineml import read, load
from lxml import etree
from nineml.exceptions import NineMLUnitMismatchError

examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class TestComponent(unittest.TestCase):

    def test_component_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxley.xml')
        document1 = read(test_file)
        xml = document1.to_xml()
        document2 = load(xml, read_from=test_file)
        self.assertEquals(document1, document2)

    def test_prototype_xml_540degree_roundtrip(self):
        test_file = os.path.join(examples_dir, 'HodgkinHuxleyModified.xml')
        document1 = read(test_file)
        xml = document1.to_xml()
        document2 = load(xml, read_from=test_file)
        self.assertEquals(document1, document2)

    def test_mismatch_dimension(self):
        document = read(os.path.join(examples_dir, 'HodgkinHuxleyBadUnits.xml'))
        with self.assertRaises(NineMLUnitMismatchError):
            document['HodgkinHuxleyBadUnits']
