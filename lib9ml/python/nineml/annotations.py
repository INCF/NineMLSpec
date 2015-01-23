from copy import copy
from nineml.xmlns import E, NINEML


class Annotations(dict):
    """
    Defines the dimension used for quantity units
    """

    element_name = 'Annotations'

    def __repr__(self):
        return ("Annotations({})"
                .format(', '.join('{}={}'.format(k, v)
                                  for k, v in self.iteritems())))

    def to_xml(self):
        return E(self.element_name,
                 *self.itervalues())

    @classmethod
    def from_xml(cls, element):
        children = {}
        for child in element.getchildren():
            children[child.tag] = child
        return cls(**children)


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, *args, **kwargs):
        annot_elem = expect_none_or_single(
            element.findall(NINEML + Annotations.element_name))
        if annot_elem is not None:
            # Extract the annotations
            annotations = Annotations.from_xml(annot_elem)
            # Get a copy of the element with the annotations stripped
            element = copy(element)
            element.remove(element.find(NINEML + Annotations.element_name))
        else:
            annotations = None
        nineml_object = from_xml(cls, element, *args, **kwargs)
        try:
            nineml_object.annotations = annotations
        except AttributeError:
            raise
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self, *args, **kwargs):
        elem = to_xml(self, *args, **kwargs)
        # If User Layer class
        if hasattr(self, 'annotations') and self.annotations is not None:
            elem.append(self.annotations.to_xml())
        # If Abstraction Layer class
        elif (len(args) and hasattr(args[0], 'annotations') and
              args[0].annotations is not None):
            elem.append(args[0].annotations.to_xml())
        return elem
    return annotate_to_xml

from nineml.utils import expect_none_or_single
