#!/usr/bin/env python
"""
.. module:: geometry.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import math
from nineml.geometry import Geometry

import nineml
import nineml.user_layer
from nineml.abstraction_layer import readers

class GeometryImplementation(Geometry):
    """
    Implementation of the Geometry interface. 
    It is a wrapper on top the source and target UnstructuredGrid object.
    """
    def __init__(self, source_unstructured_grid, target_unstructured_grid):
        if (not source_unstructured_grid) or (not isinstance(source_unstructured_grid, UnstructuredGrid)):
            raise RuntimeError('')
        if (not target_unstructured_grid) or (not isinstance(target_unstructured_grid, UnstructuredGrid)):
            raise RuntimeError('')
        
        self.source_unstructured_grid = source_unstructured_grid
        self.target_unstructured_grid = target_unstructured_grid
    
    def metric(self, source_index, target_index):
        (x1, y1, z1) = self.source_unstructured_grid.positions[source_index]
        (x2, y2, z2) = self.target_unstructured_grid.positions[target_index]
        return math.sqrt( (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2 )
    
    def sourcePosition(self, index):
        return self.source_unstructured_grid.positions[index]
    
    def targetPosition(self, index):
        return self.target_unstructured_grid.positions[index]

def createUnstructuredGrid(ul_population):
    """
    """
    if not isinstance(ul_population.prototype, nineml.user_layer.SpikingNodeType):
        raise RuntimeError('Currently, only populations of spiking neurones (not groups) are supported; population {0}'.format(ul_population.name))

    if ul_population.positions._positions:
        if len(ul_population.positions._positions) != ul_population.number:
            raise RuntimeError('')
        
        return UnstructuredGrid(ul_population.positions._positions)
    
    elif ul_population.positions.structure:
        try:
            # Try to load the Structure component
            al_structure = nineml.abstraction_layer.readers.XMLReader.read(ul_population.positions.structure.definition.url) 
        
        except Exception as e:
            raise RuntimeError('Failed to load the Structure component: {0}; the reason: {1}'.format(url, str(e)))
        
        if al_structure.name == 'grid_2d':
            fillOrder     = ul_population.positions.structure.parameters['fillOrder'].value
            aspectRatioXY = ul_population.positions.structure.parameters['aspectRatioXY'].value
            x0            = ul_population.positions.structure.parameters['x0'].value
            y0            = ul_population.positions.structure.parameters['y0'].value
            dx            = ul_population.positions.structure.parameters['dx'].value
            dy            = ul_population.positions.structure.parameters['dy'].value
            
            return Grid2D(x0, y0, dx, dy, ul_population.number)
        
        else:
            raise RuntimeError('Unsupported Structure component: {0}'.format(al_structure.name))
        
    else:
        raise RuntimeError('')
    
    return UnstructuredGrid(positions)

class UnstructuredGrid(object):
    """
    The base class for all objects created from user_layer.Structure objects. 
    """
    def __init__(self, positions):
        if not positions:
            raise RuntimeError('')
        if not isinstance(positions, list):
            raise RuntimeError('')
        
        self._positions = positions

    @property
    def positions(self):
        return self._positions

class Grid2D(UnstructuredGrid):
    def __init__(self, x0, y0, dx, dy, N):
        self.x0 = x0
        self.y0 = y0
        self.dx = dx
        self.dy = dy
        self.N  = N
        
        n = math.sqrt(N)
        if int(n) == n:
            Nx = int(n)
            Ny = int(n)
        else:
            Nx = int(n) + 1
            Ny = int(n) + 1
        
        positions = [ (x0 + i*dx, y0 + j*dy, 0.0) for i in xrange(0, Nx) for j in xrange(0, Ny) ]
        
        # Keep only N positions!
        UnstructuredGrid.__init__(self, positions[0 : self.N-1])
    
    def __str__(self):
        return str(self.positions)
    
    def __repr__(self):
        return 'Grid2D({0}, {1}, {2}, {3}, {4})'.format(self.x0, self.y0, self.dx, self.dy, self.N)

if __name__ == "__main__":
    grid2d = Grid2D(0.0, 0.0, 0.1, 0.1, 100)
    print(grid2d)
    print(repr(grid2d))
    print(grid2d.positions)
    
    