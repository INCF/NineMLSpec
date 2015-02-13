from nineml.xmlns import E
from . import BaseALObject
from nineml import TopLevelObject
from nineml.annotations import annotate_xml, read_annotations

# Might be an idea to subclass namedtuple to prevent dimensions being redefined
# and therefore protect the hash
#
# class D(namedtuple('Base', 'name m l t i n k j'), A):
#     def __new__(self, name, m=0, l=0, t=0, n=0, k=0, j=0):
#         return super(D, self).__new__(self, name, t, k, m, l, n, j)
#     def __init__(self, name, m=0, l=0, t=0, n=0, k=0, j=0):
#         pass
#
# NB: Not sure this works


class Dimension(BaseALObject, TopLevelObject):
    """
    Defines the dimension used for quantity units
    """

    element_name = 'Dimension'
    valid_dims = ['m', 'l', 't', 'i', 'n', 'k', 'j']
    SI_unit_conversion = {'m': 'Kg', 'l': 'm', 't': 's', 'i': 'A', 'n': 'mol',
                          'k': 'K', 'j': 'cd'}

    def __init__(self, name, **kwargs):
        super(Dimension, self).__init__()
        self._name = name
        for k in kwargs:
            if k not in self.valid_dims:
                raise Exception("'{}' is not a valid dimension name ('{}')"
                                .format(k, "', '".join(self.valid_dims)))
        self._dims = kwargs

    def __eq__(self, other):
        assert isinstance(other, Dimension)
        return all(self.power(d) == other.power(d) for d in self.valid_dims)

    def __hash__(self):
        return hash(tuple(self.power(d) for d in self.valid_dims))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Dimension(name='{}'{})"
                .format(self.name, ''.join(", {}={}".format(d, p)
                                           for d, p in self._dims.items())))

    @property
    def name(self):
        return self._name

    def power(self, dim_name):
        return self._dims.get(dim_name, 0)

    def to_SI_units_str(self):
        numer = '*'.join(('({}**{})'.format(self.SI_unit_conversion[n], p)
                          if p > 1 else self.SI_unit_conversion[n])
                         for n, p in self._dims.iteritems()
                         if p > 0)
        denom = '*'.join(('({}**{})'.format(self.SI_unit_conversion[n], p)
                          if p > 1 else self.SI_unit_conversion[n])
                         for n, p in self._dims.iteritems()
                         if p < 0)
        return '{}/({})'.format(numer, denom)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_dimension(self, **kwargs)

    @annotate_xml
    def to_xml(self):
        kwargs = {'name': self.name}
        kwargs.update(dict((k, str(v)) for k, v in self._dims.items()))
        return E(self.element_name, **kwargs)

    @classmethod
    @read_annotations
    def from_xml(cls, element, _):
        kwargs = dict(element.attrib)
        name = kwargs.pop('name')
        kwargs = dict((k, int(v)) for k, v in kwargs.items())
        return cls(name, **kwargs)


class Unit(BaseALObject, TopLevelObject):
    """
    Defines the units of a quantity
    """

    element_name = 'Unit'
    defining_attributes = ('name', 'dimension', 'power', 'offset')

    def __init__(self, name, dimension, power, offset=0.0):
        super(Unit, self).__init__()
        self._name = name
        self._dimension = dimension
        self._power = power
        self._offset = offset

    def __eq__(self, other):
        assert isinstance(other, Unit)
        return (self.power == other.power and self.offset == other.offset and
                self.dimension == other.dimension)

    def __hash__(self):
        return hash((self.power, self.offset, self.dimension))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Unit(name='{}', dimension='{}', power={}{})"
                .format(self.name, self.dimension.name, self.power,
                        (", offset='{}'".format(self.offset)
                         if self.offset else '')))

    def to_SI_units_str(self):
        if self.offset != 0.0:
            raise Exception("Cannot convert to SI units string as offset is "
                            "not zero ({})".format(self.offset))
        return (self.dimension.to_SI_units_str() +
                ' * 10**({})'.format(self.power) if self.power else '')

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def set_dimension(self, dimension):
        """
        Used to standardize dimension names across a NineML document. The
        actual dimension (in terms of fundamental dimension powers) should
        not change.
        """
        assert self.dimension == dimension, "dimensions do not match"
        self._dimension = dimension

    @property
    def power(self):
        return self._power

    @property
    def offset(self):
        return self._offset

    @property
    def symbol(self):
        return self.name

    @annotate_xml
    def to_xml(self):
        kwargs = {'symbol': self.name, 'dimension': self.dimension.name,
                  'power': str(self.power)}
        if self.offset:
            kwargs['offset'] = str(self.offset)
        return E(self.element_name,
                 **kwargs)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        name = element.attrib['symbol']
        dimension = document[element.attrib['dimension']]
        power = int(element.get('power', 0))
        offset = float(element.attrib.get('name', 0.0))
        return cls(name, dimension, power, offset)


time = Dimension(name="time", t=1)
per_time = Dimension(name="per_time", t=-1)
voltage = Dimension(name="voltage", m=1, l=2, t=-3, i=-1)
per_voltage = Dimension(name="per_voltage", m=-1, l=-2, t=3, i=1)
conductance = Dimension(name="conductance", m=-1, l=-2, t=3, i=2)
conductanceDensity = Dimension(name="conductanceDensity", m=-1, l=-4, t=3, i=2)
capacitance = Dimension(name="capacitance", m=-1, l=-2, t=4, i=2)
specificCapacitance = Dimension(name="specificCapacitance", m=-1, l=-4, t=4,
                                i=2)
resistance = Dimension(name="resistance", m=1, l=2, t=-3, i=-2)
resistivity = Dimension(name="resistivity", m=2, l=2, t=-3, i=-2)
charge = Dimension(name="charge", i=1, t=1)
charge_per_mole = Dimension(name="charge_per_mole", i=1, t=1, n=-1)
charge_density = Dimension(name="charge_per_mole", i=1, t=1, m=-3)
mass_per_charge = Dimension(name="mass_per_charge", i=-1, t=-1)
current = Dimension(name="current", i=1)
currentDensity = Dimension(name="currentDensity", i=1, l=-2)
current_per_time = Dimension(name="current", i=1, t=-1)
length = Dimension(name="length", l=1)
area = Dimension(name="area", l=2)
volume = Dimension(name="volume", l=3)
concentration = Dimension(name="concentration", l=-3, n=1)
per_time_per_concentration = Dimension(name="concentration", l=3, n=-1, t=-1)
substance = Dimension(name="substance", n=1)
flux = Dimension(name="flux", m=1, l=-3, t=-1)
substance_per_area = Dimension(name="substance", n=1, l=-2)
permeability = Dimension(name="permeability", l=1, t=-1)
temperature = Dimension(name="temperature", k=1)
idealGasConstantDims = Dimension(name="idealGasConstantDims", m=1, l=2, t=-2,
                                 k=-1, n=-1)
rho_factor = Dimension(name="rho_factor", l=-1, n=1, i=-1, t=-1)
dimensionless = Dimension(name="dimensionless")
energy_per_temperature = Dimension(name="energy_per_temperature", m=1, l=2,
                                   t=-2, k=-1)

s = Unit(name="s", dimension=time, power=0)
per_s = Unit(name="per_s", dimension=per_time, power=0)
Hz = Unit(name="Hz", dimension=per_time, power=0)
ms = Unit(name="ms", dimension=time, power=-3)
per_ms = Unit(name="per_ms", dimension=per_time, power=3)
m = Unit(name="m", dimension=length, power=0)
cm = Unit(name="cm", dimension=length, power=-2)
um = Unit(name="um", dimension=length, power=-6)
m2 = Unit(name="m2", dimension=area, power=0)
cm2 = Unit(name="cm2", dimension=area, power=-4)
um2 = Unit(name="um2", dimension=area, power=-12)
m3 = Unit(name="m3", dimension=volume, power=0)
cm3 = Unit(name="cm3", dimension=volume, power=-6)
litre = Unit(name="litre", dimension=volume, power=-3)
um3 = Unit(name="um3", dimension=volume, power=-18)
V = Unit(name="V", dimension=voltage, power=0)
mV = Unit(name="mV", dimension=voltage, power=-3)
per_V = Unit(name="per_V", dimension=per_voltage, power=0)
per_mV = Unit(name="per_mV", dimension=per_voltage, power=3)
ohm = Unit(name="ohm", dimension=resistance, power=0)
kohm = Unit(name="kohm", dimension=resistance, power=3)
Mohm = Unit(name="Mohm", dimension=resistance, power=6)
S = Unit(name="S", dimension=conductance, power=0)
mS = Unit(name="mS", dimension=conductance, power=-3)
uS = Unit(name="uS", dimension=conductance, power=-6)
nS = Unit(name="nS", dimension=conductance, power=-9)
pS = Unit(name="pS", dimension=conductance, power=-12)
S_per_m2 = Unit(name="S_per_m2", dimension=conductanceDensity, power=0)
mS_per_cm2 = Unit(name="mS_per_cm2", dimension=conductanceDensity, power=1)
S_per_cm2 = Unit(name="S_per_cm2", dimension=conductanceDensity, power=4)
F = Unit(name="F", dimension=capacitance, power=0)
uF = Unit(name="uF", dimension=capacitance, power=-6)
nF = Unit(name="nF", dimension=capacitance, power=-9)
pF = Unit(name="pF", dimension=capacitance, power=-12)
F_per_m2 = Unit(name="F_per_m2", dimension=specificCapacitance, power=0)
uF_per_cm2 = Unit(name="uF_per_cm2", dimension=specificCapacitance, power=-2)
ohm_m = Unit(name="ohm_m", dimension=resistivity, power=0)
kohm_cm = Unit(name="kohm_cm", dimension=resistivity, power=1)
ohm_cm = Unit(name="ohm_cm", dimension=resistivity, power=-2)
C = Unit(name="C", dimension=charge, power=0)
C_per_mol = Unit(name="C_per_mol", dimension=charge_per_mole, power=0)
A = Unit(name="A", dimension=current, power=0)
mA = Unit(name="mA", dimension=current, power=-3)
uA = Unit(name="uA", dimension=current, power=-6)
nA = Unit(name="nA", dimension=current, power=-9)
pA = Unit(name="pA", dimension=current, power=-12)
A_per_m2 = Unit(name="A_per_m2", dimension=currentDensity, power=0)
uA_per_cm2 = Unit(name="uA_per_cm2", dimension=currentDensity, power=-2)
mA_per_cm2 = Unit(name="mA_per_cm2", dimension=currentDensity, power=1)
mol_per_m3 = Unit(name="mol_per_m3", dimension=concentration, power=0)
mol_per_cm3 = Unit(name="mol_per_cm3", dimension=concentration, power=6)
M = Unit(name="M", dimension=concentration, power=3)
mM = Unit(name="mM", dimension=concentration, power=0)
mol = Unit(name="mol", dimension=substance, power=0)
m_per_s = Unit(name="m_per_s", dimension=permeability, power=0)
cm_per_s = Unit(name="cm_per_s", dimension=permeability, power=-2)
um_per_ms = Unit(name="um_per_ms", dimension=permeability, power=-3)
cm_per_ms = Unit(name="cm_per_ms", dimension=permeability, power=1)
degC = Unit(name="degC", dimension=temperature, power=0, offset=273.15)
K = Unit(name="K", dimension=temperature, power=0)
J_per_K_per_mol = Unit(name="J_per_K_per_mol", dimension=idealGasConstantDims,
                       power=0)
J_per_K = Unit(name="J_per_K", dimension=energy_per_temperature, power=0)
mol_per_m_per_A_per_s = Unit(name="mol_per_m_per_A_per_s",
                             dimension=rho_factor, power=0)
unitless = Unit(name="unitless", dimension=dimensionless, power=0)
