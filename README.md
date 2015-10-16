
NineML
======

Network Interchange for NEuroscience (NineML) is a simulator-independent language with the aim of providing an unambiguous description of neuronal network models for efficient model sharing and reusability ([http://nineml.net](http://nineml.net)).

NineML emerged from a joint effort of experts in the fields of computational neuroscience, simulator development and simulator-independent language initiatives ([NeuroML](http://www.neuroml.org/), [PyNN](http://neuralensemble.org/PyNN/)), grouped in the [INCF Multiscale Modeling Task Force](https://www.incf.org/activities/our-programs/modeling/people). This effort was initiated and is still supported by the [International Neuroinformatics Coordinating Facility (INCF)](http://www.incf.org), as part of the standardization effort of the [Multiscale Modeling Program](https://www.incf.org/activities/our-programs/modeling), but the project is now run as a [community project](../committee).


How to build the pdf
---

If running from Ubuntu linux or some other linux flavour it may not be enough to simply install the base distribution that comes with a latex editing environment you to compile this document you be required to install the texlive-full package.

```
$ sudo apt-get install texlive-full 
```

Build the pdf

```
$ cd latex
$ pdflatex NineMLSpec.tex
$ bibtex NineMLSpec
$ pdflatex NineMLSpec.tex
$ pdflatex NineMLSpec.tex
```

Related repositories
---

In addition to this main NineML repository (http://github.com/INCF/nineml), which only contains the specification document and XML schema, there are related repositories that are maintained by the NineML team (see http://nineml.net/committee).

* lib9ML (http://github.com/INCF/lib9ML): A Python library for reading, writing and manipulating NineML descriptions
* NineMLCatalog (http://github.com/INCF/NineMLCatalog): A collection of example NineML models written in XML.
