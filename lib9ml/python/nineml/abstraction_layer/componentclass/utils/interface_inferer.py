from .visitors import ComponentActionVisitor
from ...expressions.utils import get_reserved_and_builtin_symbols


class ComponentClassInterfaceInferer(ComponentActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, componentclass):
        super(ComponentClassInterfaceInferer, self).__init__(
            require_explicit_overrides=False)
        # Parameters:
        # Use visitation to collect all atoms that are not aliases and not
        # state variables
        self.componentclass = componentclass
        self.declared_symbols = set(get_reserved_and_builtin_symbols())
        self.atoms = set()
        self.input_event_port_names = set()
        self.event_out_port_names = set()
        self.visit(self.componentclass)
        # Visit class and populate declared_symbols and atoms sets
        self.parameter_names = self.atoms - self.declared_symbols

    def _notify_atom(self, atom):
        self.free_atoms.add(atom)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.declared_symbols.add(alias.lhs)
        self.atoms.update(alias.rhs_atoms)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.declared_symbols.add(constant.name)
