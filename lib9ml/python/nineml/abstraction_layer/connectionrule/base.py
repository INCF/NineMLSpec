#!/usr/bin/env python
"""
docstring goes here

.. module:: connection_generator.py
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from .. import BaseALObject
from ..componentclass import ComponentClass


class ConnectionRule(BaseALObject):

    defining_attributes = ()

    def __init__(self, standard_library, aliases=[]):
        self.standard_library = standard_library
        self.aliases = aliases

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_connectionrule(self, **kwargs)


class ConnectionRuleClass(ComponentClass):

    defining_attributes = ('name', '_parameters', 'connectionrule')

    def __init__(self, name, parameters=None, connectionrule=None):
        super(ConnectionRuleClass, self).__init__(name, parameters)
        self.connectionrule = connectionrule

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)
