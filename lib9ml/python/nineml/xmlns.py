"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml.builder import ElementMaker
from os import path

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = '{' + nineml_namespace + '}'
MATHML = "{http://www.w3.org/1998/Math/MathML}"
uncertml_namespace = "http://www.uncertml.org/2.0"
UNCERTML = '{' + uncertml_namespace + '}'

uncertml_schema_path = path.abspath(path.join(
    path.dirname(__file__), '..', '..', 'xml', 'NineML-UncertML.xsd'))

E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"ni": nineml_namespace})
