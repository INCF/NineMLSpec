#from nineml.user_layer_aux.connection_generator import ConnectionGenerator, cgClosureFromURI
from nineml.user_layer_aux.cg_closure import alConnectionRuleFromURI
from nineml.user_layer_aux.explicit_list_of_connections import ExplicitListOfConnections
from nineml.user_layer_aux.grids import createUnstructuredGrid, GeometryImplementation

#memoizedConnectionGenerators = {}

def connectionGeneratorFromProjection (projection, geometry):
    """
    Returns an object that supports ConnectionGenerator interface.
    
    :param projection: user-layer Projection object
    :param geometry: Geometry-derived object
    
    :rtype: ConnectionGenerator-derived object
    :raises: RuntimeError
    """
    rule = projection.rule

    """
    ACHTUNG, ACHTUNG!!
    Testing for attribute is a temporal workaround. 
    Will be fixed when the XML serialization is implemented.
    """
    if hasattr (rule, 'connections'):
        connections = getattr (rule, 'connections') 
        cg = ExplicitListOfConnections (connections)
        return cg

    # Assembling a CG instantiation
    cgClosure = alConnectionRuleFromURI (rule.definition.url)
    cg = cgClosure (rule.parameters)
    return cg
    
def geometryFromProjection(projection):
    """
    Returns an object that supports Geometry interface.
    
    :param projection: user-layer Projection object
    
    :rtype: Geometry-derived object
    :raises: RuntimeError
    """
    source_grid = createUnstructuredGrid(projection.source)
    target_grid = createUnstructuredGrid(projection.target)
   
    geometry = GeometryImplementation(source_grid, target_grid)
    return geometry
    
