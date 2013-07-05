#!/usr/bin/env python
"""
.. module:: geometry.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

from abc import ABCMeta, abstractmethod, abstractproperty

class Geometry(object):
    """
    Geometry interface has got three methods:
     * metric: returns a distance between two neurones
     * sourcePosition: returns x,y,z coordinates of a neurone from the source Population/Selection/Group
     * targetPosition: returns x,y,z coordinates of a neurone from the target Population/Selection/Group
    """
    
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def metric(self, source_index, target_index):
        """
        Returns a distance between two points (units: ???) specified by the *source_index*
        and the *target_index* arguments.
        
        :param source_index: Integer
        :param target_index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass

    @abstractmethod
    def sourcePosition(self, index):
        """
        Returns a coordinate (tuple: (x, y, z); units: ???) of a point specified by the *index* argument.
        
        :param index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass

    @abstractmethod
    def targetPosition(self, index):
        """
        Returns a coordinate (tuple: (x, y, z); units: ???) of a point specified by the *index* argument.
        
        :param index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass
    