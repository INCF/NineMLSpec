import os.path
import unittest
from nineml import read, load


class TestUnitsDimensions(unittest.TestCase):

    test_file = os.path.join(os.path.dirname(__file__), '..', '..',
                             '..', 'xml', 'units.xml')

    def test_xml_540degree_roundtrip(self):
        document1 = read(self.test_file)
        xml = document1.to_xml()
        document2 = load(xml, read_from=self.test_file)
        self.assertEquals(document1, document2)
