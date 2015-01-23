from ...componentclass.utils import ComponentClassInterfaceInferer
from .visitors import ConnectionRuleActionVisitor


class ConnectionRuleClassInterfaceInferer(ComponentClassInterfaceInferer,
                                        ConnectionRuleActionVisitor):

    """
    Not extended from base classes currently, just mixes in the connectionrule-
    specific action visitor to the component-class interface inferer.
    """
    pass
