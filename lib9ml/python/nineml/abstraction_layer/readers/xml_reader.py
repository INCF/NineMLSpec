""" This file defines classes for reading NineML files.


"""


import os
import nineml


__all__ = ['XMLReader']



class XMLLoader(object):
    """This class is used by XMLReader internally.
    
    This class loads a NineML XML tree, and stores
    the components in ``components``. It also records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """


    def __init__(self, xmlroot, xml_node_filename_map):
        
        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.findall(nineml.al.NINEML + "ComponentClass"):
            component = self.load_componentclass( comp_block )

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]



    def load_connectports(self, element ):
        return element.get('source'), element.get('sink')



    def load_subnode(self, subnode):
        namespace = subnode.get('namespace')
        component = nineml.utility.filter_expect_single( self.components, 
                                          lambda c: c.name==subnode.get('node'))
        return namespace, component
    


    def load_componentclass(self, element):
    
        blocks = ('Parameter', 'AnalogPort', 'EventPort', 
                  'Dynamics', 'Subnode', 'ConnectPorts') 
    
        subnodes = self.loadBlocks( element, blocks=blocks)
    
        dynamics = nineml.utility.expect_single(subnodes["Dynamics"])
        return nineml.al.ComponentClass(name=element.get('name'),
                              parameters = subnodes["Parameter" ] ,
                              analog_ports = subnodes["AnalogPort"] ,
                              event_ports = subnodes["EventPort"],
                              dynamics = dynamics,
                              subnodes = dict(subnodes['Subnode'] ),
                              portconnections = subnodes["ConnectPorts"])

    def load_parameter(self, element):
        return nineml.al.Parameter(name=element.get('name'), dimension=element.get('dimension')) 

    def load_analogport(self, element):
        return nineml.al.AnalogPort( name = element.get("name"),
                              mode = element.get('mode'), 
                              reduce_op = element.get("reduce_op", None)
                            )

    def load_eventport(self, element):
        return nineml.al.EventPort( name = element.get('name'), 
                             mode = element.get('mode') )



    def load_dynamics(self, element):
        subblocks = ('Regime', 'Alias', 'StateVariable') 
        subnodes = self.loadBlocks( element, blocks= subblocks )

        return nineml.al.Dynamics(  regimes = subnodes["Regime"] ,
                             aliases = subnodes["Alias"] ,
                             state_variables = subnodes["StateVariable"] )


    def load_regime(self, element):
        subblocks = ('TimeDerivative', 'OnCondition', 'OnEvent')
        subnodes = self.loadBlocks( element, blocks=subblocks)
        transitions = subnodes["OnEvent"] + subnodes['OnCondition'] 
        return nineml.al.Regime( name=element.get('name'),
                          time_derivatives = subnodes["TimeDerivative"],
                          transitions = transitions )



    def load_statevariable(self, element):
        name = element.get("name")
        dimension=element.get('dimension')
        return nineml.al.StateVariable( name=name, dimension=dimension)


    def load_timederivative(self, element):
        variable = element.get("variable")
        expr = self.load_single_internal_maths_block(element)
        return nineml.al.TimeDerivative( dependent_variable=variable, 
                                  rhs=expr)
        
    def load_alias(self, element):
        name = element.get("name")
        rhs =  self.load_single_internal_maths_block(element)
        return nineml.al.Alias(lhs=name,  
                        rhs=rhs)


    def load_oncondition(self, element):
        subblocks = ('Trigger', 'StateAssignment', 'EventOut')
        subnodes = self.loadBlocks( element, blocks=subblocks)
        target_regime = element.get('target_regime', None)
        trigger = nineml.utility.expect_single( subnodes["Trigger"] )

        return nineml.al.OnCondition( trigger = trigger,
                               state_assignments = subnodes["StateAssignment"],
                               event_outputs = subnodes[ "EventOut" ],
                               target_regime_name = target_regime)
                                    

    def load_onevent(self, element):
        subblocks = ('StateAssignment', 'EventOut' ) 
        subnodes = self.loadBlocks( element, blocks = subblocks )
        target_regime_name = element.get('target_regime', None)


        return nineml.al.OnEvent( src_port_name = element.get('src_port'),
                           state_assignments = subnodes["StateAssignment"],
                           event_outputs = subnodes["EventOut"],
                           target_regime_name = target_regime_name
                         )

    def load_trigger(self, element):
        return self.load_single_internal_maths_block ( element ) 


    def load_stateassignment(self, element):
        lhs = element.get('variable')
        rhs = self.load_single_internal_maths_block(element)
        return nineml.al.StateAssignment(lhs=lhs, rhs=rhs)

    def load_eventout(self, element):
        port_name = element.get('port')
        return nineml.al.OutputEvent(port_name=port_name)

    def load_single_internal_maths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=nineml.al.etree.Element ) ) 
            if  len( elements ) != 1:
                print elements
                assert False, 'Unexpected tags found'

        assert len( element.findall(nineml.al.NINEML+"MathML") ) == 0
        assert len( element.findall(nineml.al.NINEML+"MathInline") ) == 1
        
        return nineml.utility.expect_single( element.findall(nineml.al.NINEML+'MathInline') ).text


    # These blocks map directly in to classes:
    def loadBlocks(self, element, blocks=None, check_for_spurious_blocks=True ):
        """ 
        Creates a dictionary that maps class-types to instantiated objects
        """


        res =  dict( (block,[]) for block in blocks ) 

        for t in element.iterchildren(tag=nineml.al.etree.Element):
            if t.tag.startswith(nineml.al.NINEML):
                tag = t.tag[len(nineml.al.NINEML):]
            else:
                tag = t.tag

            

            if check_for_spurious_blocks and not tag in blocks:
                    err = "Unexpected Block tag: %s "%tag
                    err += '\n Expected: %s'%','.join(blocks)
                    raise nineml.exceptions.NineMLRuntimeError(err)
            
            res[tag].append( XMLLoader.tag_to_loader[tag](self,t) ) 
        return res





    tag_to_loader = {
        "ComponentClass" : load_componentclass,
        "Regime" : load_regime,
        "StateVariable" : load_statevariable,
        "Parameter": load_parameter,
        "EventPort": load_eventport,
        "AnalogPort": load_analogport,
        "Dynamics": load_dynamics,
        "OnCondition": load_oncondition,
        "OnEvent": load_onevent,
        "Alias": load_alias,
        "TimeDerivative": load_timederivative,
        "Trigger": load_trigger,
        "StateAssignment": load_stateassignment,
        "EventOut": load_eventout,
        #"EventIn": load_eventin,
        "Subnode": load_subnode,
        "ConnectPorts": load_connectports,
        }





class XMLReader(object):
    """A class that can read |COMPONENTCLASS| objects from a NineML XML file. 
    """


    @classmethod
    def _load_include(cls, include_element, basedir, xml_node_filename_map):
        """Help function for replacing <Include> nodes.
        
        We replace the include node with the tree referenced
        by that filename. To do this, we load the file referenced,
        get all the elements in the root node, and copy them over to the place
        in the original tree where the original node was. It is important that
        we preserve the order. Finally, we remove the <Include> element node.

        """

        filename = include_element.get('file')

        # Load the new XML
        included_xml = cls._load_nested_xml( 
                                filename = os.path.join(basedir, filename),
                                xml_node_filename_map=xml_node_filename_map )

        #Insert it into the parent node:
        index_of_node = include_element.getparent().index(include_element)
        for i, newchild in enumerate(included_xml.getchildren()):
            include_element.getparent().insert(  i+index_of_node, newchild)

        include_element.getparent().remove( include_element )


    @classmethod
    def _load_nested_xml(cls, filename, xml_node_filename_map):
        """ Load the XML, including  all referenced Include files .

        We also populate a dictionary, ``xml_node_filename_map`` which maps each
        node to the name of the filename that it was originally in, so that when
        we load in single components from a file, which are hierachical and
        contain references to other components, we can find the components that
        were in the file specified.
        
        """
        
        
        doc = nineml.al.etree.parse(filename)
        # Store the source filenames of all the nodes:
        for node in doc.getroot().getiterator():
            xml_node_filename_map[node] = filename

        
        root = doc.getroot()
        assert root.nsmap[None] == nineml.al.nineml_namespace
        
        # Recursively Load Include Nodes:
        for include_element in root.getiterator(tag=nineml.al.NINEML+'Include'):
            cls._load_include( include_element=include_element, 
                               basedir=os.path.dirname(filename),
                               xml_node_filename_map=xml_node_filename_map ) 
        return root



    @classmethod
    def read(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one ComponentClass
            definition, this parameter must be provided as a ``string``
            specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object. 
        """
        return cls.read_component(filename, component_name=component_name)

    @classmethod
    def read_component(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one ComponentClass
            definition, this parameter must be provided as a ``string``
            specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object. 
        """

        xml_node_filename_map = {}
        root = cls._load_nested_xml( filename=filename, 
                                   xml_node_filename_map=xml_node_filename_map)



        loader = XMLLoader( xmlroot=root, 
                            xml_node_filename_map=xml_node_filename_map)

        if component_name == None:
            key_func = lambda c: loader.component_srcs[c] == filename
            return nineml.utility.filter_expect_single(loader.components, key_func)
            
        else:
            key_func = lambda c: c.name == component_name 
            return nineml.utility.filter_expect_single(loader.components, key_func) 
                                         

    @classmethod
    def read_components(cls, filename):
        """Reads a several |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :rtype: Returns a list of |COMPONENTCLASS| objects, for each
            <ComponentClass> node in the XML tree.
        
        """
        xml_node_filename_map = {}
        root = cls._load_nested_xml(filename, xml_node_filename_map)
        loader = XMLLoader( xmlroot = root, 
                            xml_node_filename_map = xml_node_filename_map  )
        return loader.components

        




