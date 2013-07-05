#!/usr/bin/env python
"""
.. module:: expplicit_list_of_connections.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

from nineml.connection_generator import ConnectionGenerator

class ExplicitListOfConnections(ConnectionGenerator):
    """
    The implementation of the ConnectionGenerator interface for the explicit list of connections.
    It is implemented as a python generator (not iterator) for performance reasons.
    Its __iter__() function returns an iterator over target-index-sorted connections. 
    
    **Achtung, Achtung!** 
    All indexes are zero based, for both source and target populations.
    The returned connections are target-index sorted.
    """
    def __init__(self, connections):
        if not connections or len(connections) == 0:
            raise RuntimeError('The connections argument is either None or an empty list')
        
        n_values = len(connections[0])
        if n_values < 2:
            raise RuntimeError('The number of items in each connection must be at least 2')
        
        for c in connections:
            if len(c) != n_values:
                raise RuntimeError('An invalid number of items in the connection: {0}; it should be {1}'.format(c, n_values))
        
        self._connections = connections
        self._mask        = None
    
    def __len__(self):
        return len(self._connections)
        
    @property
    def arity(self):
        return len(self._connections[0]) - 2
    
    def setMask(self, mask):
        self._mask = mask        

    def __iter__(self):
        """
        Returns an iterator over target-index-sorted connections.
        
        :rtype: iterator
        :raises:
        """
        return self.iterconnections()

    def connections(self):
        """
        Returns an internal unordered list of connections.
        
        :rtype: list of tuples (source_index, target_index, parameter0, parameter1, ...)
        :raises:
        """
        return self._connections
        
    def iterconnections(self):
        """
        A generator function that returns an iterator over target-index-sorted connections.
        The connections returned are target neurone sorted.
        
        :rtype: iterator
        :raises:
        """
        if not self._mask:
            raise RuntimeError('Mask has bot been set')
        
        for target_interval in self._mask.targets:
            for target_index in xrange(target_interval[0], target_interval[1] + 1, self._mask.targets.skip):
                for connection in self._connections:
                    si = connection[0]
                    ti = connection[1]
                    if target_index == ti: # if the index is equal to the target-index examine the source-index
                        for source_interval in self._mask.sources: # check if the source-index belongs to one of the intervals
                            if si in xrange(source_interval[0], source_interval[1] + 1, self._mask.sources.skip):
                                yield connection

    def iterunorderedconnections(self):
        """
        A generator function that returns an iterator over unsorted connections.
        
        :rtype: iterator
        :raises:
        """
        for connection in self._connections:
            yield connection

