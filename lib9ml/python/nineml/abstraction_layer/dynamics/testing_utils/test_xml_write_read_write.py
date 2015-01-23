"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

# from ..utils import xml
# from ..utils import flattener as flattening2
# from nineml.utils import file_sha1_hexdigest
# from ...validators.equality_checker import DynamicsEqualityChecker
#
#
# class TestXMLWriteReadWrite(object):
#
#     @classmethod
#     def test(cls, testable_component, build_dir):
#         component = testable_component()
#         print '  -- Testing One and a half trips...'
#
#         if not component.is_flat():
#             component = flattening2.flatten(component)
#
#         xmlfile1 = build_dir + component.name + '1.xml'
#         xmlfile2 = build_dir + component.name + '2.xml'
#
#         print '    -- Saving Component To XML:', xmlfile1
#         xml.DynamicsClassXMLWriter.write(component, xmlfile1)
#
#         print '    -- Loading Component To XML.'
#         reloaded_comp = xml.DynamicsClassXMLReader.read(xmlfile1)
#
#         print '    -- Checking Components are identical'
#         DynamicsEqualityChecker.check_equal(component, reloaded_comp)
#
#         print '    -- Saving Reloaded Component to XML', xmlfile2
#         xml.DynamicsClassXMLWriter.write(reloaded_comp, xmlfile2)
#
#         print '    -- Checking the SHA1 Checksum of the two xml files:'
#         hash1 = file_sha1_hexdigest(xmlfile1)
#         hash2 = file_sha1_hexdigest(xmlfile2)
#         print '      -->', hash1
#         print '      -->', hash2
#
#         if hash1 != hash2:
#             raise ValueError(
#                 'XML files are different. This may not be an error but please'
#                 ' report it to the developers')
