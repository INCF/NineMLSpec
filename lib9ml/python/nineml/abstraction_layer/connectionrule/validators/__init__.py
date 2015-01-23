from ...componentclass.validators.base import BaseValidator
from ..utils.visitors import ConnectionRuleActionVisitor


class BaseConnectionRuleValidator(BaseValidator, ConnectionRuleActionVisitor):

    def __init__(self, require_explicit_overrides=True):
        super(BaseConnectionRuleValidator, self).__init__(
            self, require_explicit_overrides=require_explicit_overrides)

    # Override this function, so we can extract out the
    # namespace, then propogate this as a parameter.
    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        namespace = component.get_node_addr()
        ConnectionRuleActionVisitor.visit_componentclass(
            self, component, namespace=namespace)

from .base import ConnectionRuleValidator
