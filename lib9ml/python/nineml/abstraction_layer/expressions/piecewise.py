from itertools import chain
from .. import BaseALObject
from .base import Expression
from . import parse


class Piecewise(BaseALObject):

    element_name = 'Piecewise'
    defining_attributes = ('name', 'pieces', 'otherwise')

    def __init__(self, name, pieces, otherwise):
        self.name = name
        self.pieces = pieces
        self.otherwise = otherwise

    def __repr__(self):
        return ("Piecewise(name={}, value={})"
                .format(self.name, self.value))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_piecewise(self, **kwargs)

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    @property
    def rhs_atoms(self):
        return set(chain(*([p.rhs_atoms for p in self.pieces] +
                           [self.otherwise.rhs_atoms])))


class Piece(Expression, BaseALObject):

    element_name = "Piece"
    defining_attributes = ('_rhs', 'condition')

    def __init__(self, expr, condition):
        super(Piece, self).__init__(expr)
        if isinstance(condition, basestring):
            condition = Condition(condition)
        self.condition = condition

    def __str__(self):
        return '{},    {}'.format(self.rhs, self.condition)

    def __repr__(self):
        return "Piece(expr='{}', test='{}')".format(self.rhs,
                                                    self.condition.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_piece(self, **kwargs)

    @property
    def rhs_atoms(self):
        return chain(super(Piece, self).rhs_atoms,
                     self.condition.rhs_atoms)

    def __getitem__(self, i):
        if i == 0:
            return self.rhs
        elif i == 1:
            return self.condition.rhs
        else:
            raise IndexError("Index '{}' out of bounds (0 <= i <= 1)"
                             .format(i))


class Otherwise(Expression, BaseALObject):

    element_name = "Otherwise"

    def __repr__(self):
        return "Otherwise(expr='{}')".format(self.rhs)

    def __str__(self):
        return self.rhs

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_otherwise(self, **kwargs)


class Condition(Expression, BaseALObject):

    element_name = "Condition"

    def __str__(self):
        return self.rhs

    def __repr__(self):
        return "Condition('{}')".format(self.rhs)

    def _parse_rhs(self, rhs):
        return parse.cond(rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_condition(self, **kwargs)
