"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ..utils.visitors import ComponentActionVisitor


class BaseValidator(object):

    def get_warnings(self):
        raise NotImplementedError()


class PerNamespaceComponentValidator(BaseValidator,
                                     ComponentActionVisitor):

    def __init__(self, require_explicit_overrides=True):
        BaseValidator.__init__(self)
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=require_explicit_overrides)

    # Override this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        super(PerNamespaceComponentValidator, self).visit_componentclass(
            component, namespace=namespace)
