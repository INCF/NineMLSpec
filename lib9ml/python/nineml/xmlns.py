"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace
MATHML = "{http://www.w3.org/1998/Math/MathML}"
UNCERTML = "{http://www.uncertml.org/2.0}"

E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})
