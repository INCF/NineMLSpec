from itertools import chain
from .population import Population
from .projection import Projection
from .selection import Selection
from ..document import Document
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.xmlns import E, NINEML
from nineml.utils import check_tag


class Network(BaseULObject):
    """
    Container for populations and projections between those populations.

    **Arguments**:
        *name*
            a name for the network.
        *populations*
            a dict containing the populations contained in the network.
        *projections*
            a dict containing the projections contained in the network.
        *selections*
            a dict containing the selections contained in the network.
    """
    element_name = "Network"
    defining_attributes = ("name", "populations", "projections", "selections")
    children = ("populations", "projections", "selections")

    def __init__(self, name="anonymous", populations={}, projections={},
                 selections={}):
        # better would be *items, then sort by type, taking the name from the
        # item
        super(Network, self).__init__()
        self.name = name
        self.populations = populations
        self.projections = projections
        self.selections = selections

    def add(self, *objs):
        """
        Add one or more Population, Projection or Selection instances to the
        network.
        """
        for obj in objs:
            if isinstance(obj, Population):
                self.populations[obj.name] = obj
            elif isinstance(obj, Projection):
                self.projections[obj.name] = obj
            elif isinstance(obj, Selection):
                self.selections[obj.name] = obj
            else:
                raise Exception("Networks may only contain Populations, "
                                "Projections, or Selections")

    # def _resolve_population_references(self):
    #     for prj in self.projections.values():
    #         for name in ('source', 'target'):
    #             if prj.references[name] in self.populations:
    #                 obj = self.populations[prj.references[name]]
    #             elif prj.references[name] in self.selections:
    #                 obj = self.selections[prj.references[name]]
    #             elif prj.references[name] == self.name:
    #                 obj = self
    #             else:
    #                 raise Exception("Unable to resolve population/selection "
    #                                 "reference ('%s') for %s of %s" %
    #                                 (prj.references[name], name, prj))
    #             setattr(prj, name, obj)

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    @write_reference
    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 *[p.to_xml() for p in chain(self.populations.values(),
                                             self.selections.values(),
                                             self.projections.values())])

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        populations = []
        for pop_elem in element.findall(NINEML + 'PopulationItem'):
            pop = Population.from_xml(pop_elem, document)
            populations[pop.name] = pop
        projections = []
        for proj_elem in element.findall(NINEML + 'ProjectionItem'):
            proj = Projection.from_xml(proj_elem, document)
            projections[proj.name] = proj
        selections = []
        for sel_elem in element.findall(NINEML + 'Selection'):
            sel = Selection.from_xml(sel_elem, document)
            selections[sel.name] = sel
        network = cls(name=element.attrib["name"], populations=populations,
                      projections=projections, selections=selections)
        return network

    def write(self, filename):
        document = Document()
        units = set()
        for name, obj in chain(self.populations.items(),
                               self.projections.items()):
            document[name] = obj
            for c in obj.get_components():
                units = units.union(c.units)
        for name, obj in self.selections.items():
            document[name] = obj
        for u in units:
            document[u.dimension.name] = u.dimension
            document[u.name] = u
        document.write(filename)
