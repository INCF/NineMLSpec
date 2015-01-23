"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xmlns import E
from ..base import DistributionClass, Distribution
from nineml.annotations import read_annotations
from ...componentclass.utils.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)


class DistributionClassXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_componentclass(self, element):
        subblocks = ('Parameter', 'RandomDistribution')
        children = self._load_blocks(element, blocks=subblocks)
        distribution = expect_single(children["RandomDistribution"])
        return DistributionClass(name=element.get('name'),
                                 parameters=children["Parameter"],
                                 distribution=distribution)

    @read_annotations
    def load_distribution(self, element):
        subblocks = ('Alias',)
        children = self._load_blocks(element, blocks=subblocks)
        return Distribution(standard_library=element.attrib['standardLibrary'],
                            aliases=children["Alias"])

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "RandomDistribution": load_distribution
    }


class DistributionClassXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, componentclass):
        elements = ([p.accept_visitor(self)
                     for p in componentclass.parameters] +
                    [componentclass.distribution.accept_visitor(self)])
        return E('ComponentClass', *elements, name=componentclass.name)

    @annotate_xml
    def visit_distribution(self, distribution):
        elements = [b.accept_visitor(self) for b in distribution.aliases]
        return E('RandomDistribution',
                 *elements, standardLibrary=distribution.standard_library)
