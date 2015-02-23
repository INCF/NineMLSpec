from lxml import etree
from lxml.builder import ElementMaker
from operator import itemgetter
from nineml.abstraction_layer import BaseALObject
from nineml.exceptions import NineMLRuntimeError
from nineml.xmlns import uncertml_namespace, UNCERTML
from cStringIO import StringIO


class RandomVariable(BaseALObject):

    element_name = 'RandomVariable'
    defining_attributes = ('name', 'distribution', 'units')

    def __init__(self, name, distribution, units):
        self.name = name
        self.distribution = distribution
        self.units = units

    def __repr__(self):
        return ("RandomVariable(name={}, units={}, distribution={})"
                .format(self.name, self.distribution, self.units))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomvariable(self, **kwargs)

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    def set_units(self, units):
        assert self.units == units, \
            "Renaming units with ones that do not match"
        self.units = units


class RandomDistribution(BaseALObject):
    """
    A base class for reading and writing distributions defined in UncertML
    """

    defining_attributes = ('name', 'parameters')

    E = ElementMaker(namespace=uncertml_namespace,
                     nsmap={"un": uncertml_namespace})

    valid_distributions = (
        'Normal', 'Bernoulli', 'Beta', 'Binomial', 'Cauchy',
        'ChiSquare', 'Dirichlet', 'Exponential', 'F', 'Gamma', 'Geometric',
        'Hypergeometric', 'InverseGamma', 'Laplace', 'Logistic', 'LogNormal',
        'MixtureModel Multinomial', 'NegativeBinomial', 'Normal',
        'NormalInverseGamma', 'Pareto', 'Poisson', 'StudentT', 'Uniform',
        'Weibull')

    non_alphabetical = {'StudentT': ('location', 'scale', 'degreesOfFreedom'),
                        'Gamma': ('shape', 'scale'),
                        'InverseGamma': ('shape', 'scale'),
                        'NormalInverseGamma': ('mean', 'varianceScaling',
                                               'shape', 'scale'),
                        'Uniform': ('minimum', 'maximum', 'numberOfClasses')}

    def __init__(self, name, parameters, validate=True):
        self.name = name
        self.parameters = parameters
        # Convert to xml and check against UncertML schema
        if validate:
            try:
                self._validate_xml(self.to_xml())
            except NineMLRuntimeError:
                raise NineMLRuntimeError(
                    "Invalid parameters/values to random distribution '{}':\n"
                    "  {}\nSee {} for valid parameter/values."
                    .format(self.name, self.parameters, uncertml_namespace))

    def to_xml(self):
        # UncertML is order-specific, whereas NineML-UncertML is not in keeping
        # with the general design philosophy of NineML
        if self.name in self.non_alphabetical:
            sorted_params = ((n, self.parameters[n])
                             for n in self.non_alphabetical[self.name])
        else:
            sorted_params = sorted(self.parameters.iteritems(),
                                   key=itemgetter(0))
        return self.E(self.name + 'Distribution',
                      *((self.E(n, str(v)) for n, v in sorted_params)))

    @classmethod
    def from_xml(cls, element, document):  # @UnusedVariable
        cls._validate_xml(element)
        if not element.tag.endswith('Distribution'):
            raise NineMLRuntimeError(
                "Only UncertML distribution elements can be used inside "
                "RandomVariable elements, not '{}'".format(element.tag))
        name = element.tag[len(UNCERTML):-len('Distribution')]
        params = dict((c.tag[len(UNCERTML):], float(c.text))
                      for c in element.getchildren())
        return cls(name=name, parameters=params, validate=False)

    @classmethod
    def _validate_xml(cls, xml):
        if not uncertml_schema.validate(xml):
            error = uncertml_schema.error_log.last_error
            raise NineMLRuntimeError(
                "Invalid UncertML XML in Random distribution: {} - {}\n\n{}"
                .format(error.domain_name, error.type_name,
                        etree.tostring(xml, pretty_print=True)))


_UNCERTML_SCHEMA = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:un="http://www.uncertml.org/2.0" xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.uncertml.org/2.0" elementFormDefault="qualified" attributeFormDefault="unqualified">
  <!--==== Basic Types ====-->
  <xs:simpleType name="kurtosisValue">
    <xs:restriction base="xs:double">
      <xs:minInclusive value="-2"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="normalisedDouble">
    <xs:restriction base="xs:double">
      <xs:minInclusive value="-1.0"/>
      <xs:maxInclusive value="1.0"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="naturalNumber">
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="0"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="positiveNaturalNumber">
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="1"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="kurtosisValueArray">
    <xs:list itemType="un:kurtosisValue"/>
  </xs:simpleType>
  <xs:simpleType name="normalisedDoubleArray">
    <xs:list itemType="un:normalisedDouble"/>
  </xs:simpleType>
  <xs:simpleType name="naturalNumberArray">
    <xs:list itemType="un:naturalNumber"/>
  </xs:simpleType>
  <xs:simpleType name="positiveNaturalNumberArray">
    <xs:list itemType="un:naturalNumber"/>
  </xs:simpleType>
  <xs:simpleType name="probability">
    <xs:restriction base="xs:double">
      <xs:minInclusive value="0.0"/>
      <xs:maxInclusive value="1.0"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="probabilityArray">
    <xs:list itemType="un:probability"/>
  </xs:simpleType>
  <xs:simpleType name="positiveRealNumber">
    <xs:restriction base="xs:double">
      <xs:minExclusive value="0.0"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="positiveRealNumberArray">
    <xs:list itemType="un:positiveRealNumber"/>
  </xs:simpleType>
  <xs:simpleType name="doubleArray">
    <xs:list itemType="xs:double"/>
  </xs:simpleType>
  <xs:simpleType name="integerArray">
    <xs:list itemType="xs:integer"/>
  </xs:simpleType>
  <xs:simpleType name="stringArray">
    <xs:list itemType="xs:string"/>
  </xs:simpleType>
  <xs:attributeGroup name="HREFAttributeGroup">
    <xs:attribute name="href" type="xs:anyURI" use="optional"/>
    <xs:attribute name="mimeType" type="xs:string" use="optional"/>
  </xs:attributeGroup>
  <xs:complexType name="KurtosisValuesType">
    <xs:simpleContent>
      <xs:extension base="un:kurtosisValueArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="NormalisedValuesType">
    <xs:simpleContent>
      <xs:extension base="un:normalisedDoubleArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ContinuousValuesType">
    <xs:simpleContent>
      <xs:extension base="un:doubleArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="DiscreteValuesType">
    <xs:simpleContent>
      <xs:extension base="un:integerArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="CategoricalValuesType">
    <xs:simpleContent>
      <xs:extension base="un:stringArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ProbabilityValuesType">
    <xs:simpleContent>
      <xs:extension base="un:probabilityArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="PositiveRealValuesType">
    <xs:simpleContent>
      <xs:extension base="un:positiveRealNumberArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="NaturalNumbersType">
    <xs:simpleContent>
      <xs:extension base="un:naturalNumberArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="PositiveNaturalNumbersType">
    <xs:simpleContent>
      <xs:extension base="un:positiveNaturalNumberArray">
        <xs:attributeGroup ref="un:HREFAttributeGroup"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <!--==== Inheritance Types ====-->
  <xs:element name="AbstractUncertainty" type="un:AbstractUncertaintyType" abstract="true"/>
  <xs:complexType name="AbstractUncertaintyType" abstract="true"/>
  <xs:element name="AbstractDistribution" type="un:AbstractDistributionType" abstract="true" substitutionGroup="un:AbstractUncertainty"/>
  <xs:complexType name="AbstractDistributionType" abstract="true">
    <xs:complexContent>
      <xs:extension base="un:AbstractUncertaintyType"/>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="AbstractSummaryStatistic" type="un:AbstractSummaryStatisticType" abstract="true" substitutionGroup="un:AbstractUncertainty"/>
  <xs:complexType name="AbstractSummaryStatisticType" abstract="true">
    <xs:complexContent>
      <xs:extension base="un:AbstractUncertaintyType"/>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="AbstractSample" type="un:AbstractSampleType" abstract="true" substitutionGroup="un:AbstractUncertainty"/>
  <xs:complexType name="AbstractSampleType" abstract="true">
    <xs:complexContent>
      <xs:extension base="un:AbstractUncertaintyType">
        <xs:sequence>
          <xs:element name="samplingMethodDescription" type="xs:string" minOccurs="0"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <!--==== UncertML Core Summary Statistics ====-->
  <xs:element name="Mean" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MeanType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MeanType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Mode" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ModeType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ModeType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:choice>
          <xs:element name="values" type="un:ContinuousValuesType"/>
          <xs:element name="categories" type="un:CategoricalValuesType"/>
        </xs:choice>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Median" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MedianType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MedianType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Quantile" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:QuantileType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="QuantileType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="level" use="required">
          <xs:simpleType>
            <xs:restriction base="xs:double">
              <xs:minInclusive value="0.0"/>
              <xs:maxInclusive value="1.0"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:attribute>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="DiscreteProbability" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:DiscreteProbabilityType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="DiscreteProbabilityType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="categories">
            <xs:complexType>
              <xs:simpleContent>
                <xs:restriction base="un:CategoricalValuesType"/>
              </xs:simpleContent>
            </xs:complexType>
          </xs:element>
          <xs:element name="probabilities" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Probability" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ProbabilityType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ProbabilityType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="probabilities" type="un:ProbabilityValuesType"/>
        </xs:sequence>
        <xs:attribute name="gt" type="xs:double"/>
        <xs:attribute name="lt" type="xs:double"/>
        <xs:attribute name="ge" type="xs:double"/>
        <xs:attribute name="le" type="xs:double"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Variance" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:VarianceType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="VarianceType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="StandardDeviation" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:StandardDeviationType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="StandardDeviationType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Skewness" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:SkewnessType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="SkewnessType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="ConfidenceInterval" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ConfidenceIntervalType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ConfidenceIntervalType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="lower" type="un:QuantileType"/>
          <xs:element name="upper" type="un:QuantileType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="StatisticsCollection" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:StatisticsCollectionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="StatisticsCollectionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence maxOccurs="unbounded">
          <xs:element ref="un:AbstractSummaryStatistic"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="ConfusionMatrix" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ConfusionMatrixType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ConfusionMatrixType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="sourceCategories" type="un:CategoricalValuesType"/>
          <xs:element name="targetCategories" type="un:CategoricalValuesType"/>
          <xs:element name="counts" type="un:PositiveNaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="CovarianceMatrix" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CovarianceMatrixType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CovarianceMatrixType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="dimension" type="un:naturalNumber" use="required"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <!--==== UncertML + Summary Statistics ====-->
  <xs:element name="Range" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:RangeType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="RangeType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="lower" type="un:ContinuousValuesType"/>
          <xs:element name="upper" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="CentredMoment" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CentredMomentType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CentredMomentType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="order" type="un:naturalNumber" use="required"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Moment" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MomentType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MomentType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="order" type="un:naturalNumber" use="required"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Quartile" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:QuartileType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="QuartileType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="level" use="required">
          <xs:simpleType>
            <xs:restriction base="xs:double">
              <xs:pattern value="0.25"/>
              <xs:pattern value="0.50"/>
              <xs:pattern value="0.75"/>
              <xs:pattern value="1.00"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:attribute>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Decile" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:DecileType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="DecileType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="level" use="required">
          <xs:simpleType>
            <xs:restriction base="xs:integer">
              <xs:minInclusive value="1"/>
              <xs:maxInclusive value="9"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:attribute>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Percentile" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:PercentileType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="PercentileType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
        <xs:attribute name="level" use="required">
          <xs:simpleType>
            <xs:restriction base="xs:int">
              <xs:minInclusive value="0"/>
              <xs:maxInclusive value="100"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:attribute>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Kurtosis" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:KurtosisType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="KurtosisType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:KurtosisValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="CredibleInterval" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CredibleIntervalType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CredibleIntervalType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="lower" type="un:QuantileType"/>
          <xs:element name="upper" type="un:QuantileType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Correlation" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CorrelationType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CorrelationType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:NormalisedValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="CoefficientOfVariation" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CoefficientOfVariationType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CoefficientOfVariationType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="values" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="InterquartileRange" substitutionGroup="un:AbstractSummaryStatistic">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:InterquartileRangeType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="InterquartileRangeType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSummaryStatisticType">
        <xs:sequence>
          <xs:element name="lower" type="un:ContinuousValuesType"/>
          <xs:element name="upper" type="un:ContinuousValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <!--==== Distributions ====-->
  <xs:element name="DirichletDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:DirichletDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="DirichletDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="concentration" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="ExponentialDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ExponentialDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ExponentialDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="rate" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="GammaDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:GammaDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="GammaDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="InverseGammaDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:InverseGammaDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="InverseGammaDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="NormalInverseGammaDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:NormalInverseGammaDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="NormalInverseGammaDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="mean" type="un:ContinuousValuesType"/>
          <xs:element name="varianceScaling" type="un:PositiveRealValuesType"/>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="PoissonDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:PoissonDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="PoissonDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="rate" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="NormalDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:NormalDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="NormalDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="mean" type="un:ContinuousValuesType"/>
          <xs:element name="variance" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="BinomialDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:BinomialDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="BinomialDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="numberOfTrials" type="un:NaturalNumbersType"/>
          <xs:element name="probabilityOfSuccess" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="MultinomialDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MultinomialDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MultinomialDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="numberOfTrials" type="un:positiveNaturalNumber"/>
          <xs:element name="probabilities" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="LogNormalDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:LogNormalDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="LogNormalDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="logScale" type="un:ContinuousValuesType"/>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="StudentTDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:StudentTDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="StudentTDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="location" type="un:ContinuousValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
          <xs:element name="degreesOfFreedom" type="un:PositiveNaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="UniformDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:UniformDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="UniformDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:choice>
          <xs:sequence>
            <xs:element name="minimum" type="un:ContinuousValuesType"/>
            <xs:element name="maximum" type="un:ContinuousValuesType"/>
          </xs:sequence>
          <xs:sequence>
            <xs:element name="numberOfClasses" type="un:PositiveNaturalNumbersType"/>
          </xs:sequence>
        </xs:choice>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="MixtureModel" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MixtureModelType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MixtureModelType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="component" maxOccurs="unbounded">
            <xs:complexType>
              <xs:sequence>
                <xs:element ref="un:AbstractDistribution"/>
              </xs:sequence>
              <xs:attribute name="weight" type="un:probability" use="required"/>
            </xs:complexType>
          </xs:element>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="MultivariateNormalDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MultivariateNormalDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MultivariateNormalDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="mean" type="un:ContinuousValuesType"/>
          <xs:element name="covarianceMatrix" type="un:CovarianceMatrixType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="MultivariateStudentTDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:MultivariateStudentTDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="MultivariateStudentTDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="mean" type="un:ContinuousValuesType"/>
          <xs:element name="covarianceMatrix" type="un:CovarianceMatrixType"/>
          <xs:element name="degreesOfFreedom" type="un:PositiveNaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <!--==== UncertML+ Distributions ====-->
  <xs:element name="BetaDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:BetaDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="BetaDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="alpha" type="un:PositiveRealValuesType"/>
          <xs:element name="beta" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="LaplaceDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:LaplaceDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="LaplaceDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="location" type="un:ContinuousValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="CauchyDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:CauchyDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="CauchyDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="location" type="un:ContinuousValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="WeibullDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:WeibullDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="WeibullDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="LogisticDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:LogisticDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="LogisticDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="location" type="un:ContinuousValuesType"/>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="ChiSquareDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ChiSquareDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ChiSquareDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="degreesOfFreedom" type="un:PositiveNaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="GeometricDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:GeometricDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="GeometricDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="probability" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="HypergeometricDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:HypergeometricDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="HypergeometricDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="numberOfSuccesses" type="un:NaturalNumbersType"/>
          <xs:element name="numberOfTrials" type="un:NaturalNumbersType"/>
          <xs:element name="populationSize" type="un:NaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="FDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:FDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="FDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="denominator" type="un:NaturalNumbersType"/>
          <xs:element name="numerator" type="un:NaturalNumbersType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="NegativeBinomialDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:NegativeBinomialDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="NegativeBinomialDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="numberOfFailures" type="un:NaturalNumbersType"/>
          <xs:element name="probability" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="ParetoDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:ParetoDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="ParetoDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="scale" type="un:PositiveRealValuesType"/>
          <xs:element name="shape" type="un:PositiveRealValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="WishartDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:WishartDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="WishartDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="degreesOfFreedom" type="un:positiveRealNumber"/>
          <xs:element name="scaleMatrix" type="un:CovarianceMatrixType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="BernoulliDistribution" substitutionGroup="un:AbstractDistribution">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:BernoulliDistributionType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="BernoulliDistributionType">
    <xs:complexContent>
      <xs:extension base="un:AbstractDistributionType">
        <xs:sequence>
          <xs:element name="probabilities" type="un:ProbabilityValuesType"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <!--==== Samples ====-->
  <xs:element name="RandomSample" substitutionGroup="un:AbstractSample">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:RandomSampleType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="RandomSampleType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSampleType">
        <xs:sequence>
          <xs:element ref="un:Realisation" maxOccurs="unbounded"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="SystematicSample" substitutionGroup="un:AbstractSample">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:SystematicSampleType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="SystematicSampleType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSampleType">
        <xs:sequence>
          <xs:element ref="un:Realisation" maxOccurs="unbounded"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="UnknownSample" substitutionGroup="un:AbstractSample">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:UnknownSampleType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="UnknownSampleType">
    <xs:complexContent>
      <xs:extension base="un:AbstractSampleType">
        <xs:sequence>
          <xs:element ref="un:Realisation" maxOccurs="unbounded"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="Realisation" substitutionGroup="un:AbstractUncertainty">
    <xs:complexType>
      <xs:complexContent>
        <xs:extension base="un:RealisationType"/>
      </xs:complexContent>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="RealisationType">
    <xs:complexContent>
      <xs:extension base="un:AbstractUncertaintyType">
        <xs:sequence>
          <xs:element name="weight" type="xs:double" minOccurs="0"/>
          <xs:choice>
            <xs:element name="values" type="un:ContinuousValuesType"/>
            <xs:element name="categories" type="un:CategoricalValuesType"/>
          </xs:choice>
        </xs:sequence>
        <xs:attribute name="id" type="xs:ID"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
</xs:schema>
"""
uncertml_schema = etree.XMLSchema(etree.parse(StringIO(_UNCERTML_SCHEMA)))
