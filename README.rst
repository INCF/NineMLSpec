
NineML
======

.. image:: https://readthedocs.org/projects/nineml-spec/badge/?version=latest
    :target: http://nineml-spec.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status 

Network Interchange for NEuroscience (NineML) is a simulator-independent
language with the aim of providing an unambiguous description of neuronal
network models for efficient model sharing and reusability
(http://nineml.net).

NineML emerged from a joint effort of experts in the fields of computational
neuroscience, simulator development and simulator-independent language
initiatives (NeuroML_, PyNN_), grouped in the INCF Multiscale Modeling Task Force.
This effort was initiated by the Multiscale Modeling Program,
as part of the standardization effort of the `International Neuroinformatics Coordinating Facility (INCF) <http://www.incf.org>`_,
but the project is now run as a `community project <http://nineml.net/committee>`_.


How to build the source
-----------------------

The source is written in reStructured text and can be build using
Sphinx (http://www.sphinx-doc.org/) using the provided Makefile
(or the make.bat if on Windows). If you have ``pip`` setup you can
install sphinx, along with the Read-the-docs theme, with::

    $ pip install sphinx sphinx-rtd-theme

HTML
^^^^

To make the html docs use the command

    $ make html
    
PDF
~~~

To make the pdf you will also need a TeX distribution installed
(see `MacTex <https://www.tug.org/mactex/>`__ on macOS or the ``texlive-full``
package on Ubuntu/Debian). After that the PDF can be made with.

    $ make latexpdf

Related repositories
--------------------

In addition to this main NineML repository,
which only contains the specification document and XML schema, there are
related repositories that are maintained by the NineML team
(see http://nineml.net/committee).

- `NineML Python Library`_: A Python library for reading, writing and
  manipulating NineML descriptions
- `NineML Catalog`_: A collection of example NineML models serialized to XML.

.. _PyNN: http://neuralensemble.org/PyNN/
.. _NeuroML: http://neuroml.org
.. _`NineML Python Library`: http://nineml-python.readthedocs.io
.. _`NineML Catalog`: http://github.com/INCF/nineml-catalog
