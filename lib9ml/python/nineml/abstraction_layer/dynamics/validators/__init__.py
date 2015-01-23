from ...componentclass.validators.base import PerNamespaceComponentValidator
from ..utils.visitors import DynamicsActionVisitor


class PerNamespaceDynamicsValidator(PerNamespaceComponentValidator,
                                    DynamicsActionVisitor):

    def __init__(self, require_explicit_overrides=True):
        PerNamespaceComponentValidator.__init__(
            self, require_explicit_overrides=require_explicit_overrides)

    # Override this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        DynamicsActionVisitor.visit_componentclass(
            self, component, namespace=namespace)

from .base import DynamicsValidator

