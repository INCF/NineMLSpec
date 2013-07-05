#!/usr/bin/env python
"""
.. module:: sedml_support.py
   :platform: GNU/Linux, Windows, MacOS
   :synopsis:

.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import nineml
from lxml import etree

sedml_namespace = '{http://sed-ml.org/}'

class sedmlBase:
    def __init__(self, id, name):
        self.id   = str(id)
        self.name = str(name)

    def __repr__(self):
        return '{0}, {1}'.format(self.id, self.name)
        
    def to_xml(self, root):
        root.set('id',   self.id)
        root.set('name', self.name)
        
    def from_xml(self, root, experiment):
        self.id   = root.get('id')
        self.name = root.get('name')

class UniformTimeCourseSimulation(sedmlBase):
    xmlTagName = 'uniformTimeCourse'
    
    def __init__(self, id, name, initialTime, outputStartTime, outputEndTime, numberOfPoints, algorithm):
        sedmlBase.__init__(self, id, name)
        
        if float(initialTime) != 0.0:
            raise RuntimeError('SED-ML: the initial time has to be 0.0')
        if float(outputStartTime) != 0.0:
            raise RuntimeError('SED-ML: the output start time has to be 0.0')
        if float(outputEndTime) <= float(outputStartTime):
            raise RuntimeError('SED-ML: the output start time is greater than the output end time')
            
        self.initialTime     = 0.0
        self.outputStartTime = 0.0
        self.outputEndTime   = float(outputEndTime)
        self.numberOfPoints  = int(numberOfPoints)
        self.algorithm       = str(algorithm)
    
    def __repr__(self):
        return 'sedmlSimulation({0}, {1}, {2}, {3}, {4}, {5})'.format(sedmlBase.__repr__(self), 
                                                                      self.initialTime,
                                                                      self.outputStartTime,
                                                                      self.outputEndTime,
                                                                      self.numberOfPoints,
                                                                      self.algorithm)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('initialTime',     str(self.initialTime))
        root.set('outputStartTime', str(self.outputStartTime))
        root.set('outputEndTime',   str(self.outputEndTime))
        root.set('numberOfPoints',  str(self.numberOfPoints))
        
        xml_algorithm = etree.SubElement(root, 'algorithm')
        xml_algorithm.set('kisaoID', str(self.algorithm))
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id              = root.get('id')
        name            = root.get('name')
        initialTime     = float(root.get('initialTime'))
        outputStartTime = float(root.get('outputStartTime'))
        outputEndTime   = float(root.get('outputEndTime'))
        numberOfPoints  = int(root.get('numberOfPoints'))
        
        xml_algorithm = root.find('%salgorithm' % sedml_namespace)
        if xml_algorithm == None:
            raise RuntimeError('Cannot load UniformTimeCourseSimulation object: unable to find the [algorithm] tag')
        algorithm  = str(xml_algorithm.get('kisaoID'))
        
        return UniformTimeCourseSimulation(id, name, initialTime, outputStartTime, outputEndTime, numberOfPoints, algorithm)

class Model(sedmlBase):
    xmlTagName = 'model'
    
    def __init__(self, id, name, language, source):
        sedmlBase.__init__(self, id, name)
        
        self.language = str(language) # URN
        self.source   = None
        self.ul_model = None
        
        if isinstance(source, str):
            self.source = source # URN
        elif isinstance(source, nineml.user_layer.Model):
            self.ul_model = source # python NineML UL Model object
        else:
            raise RuntimeError('SED-ML: invalid user-layer reference')
            
    def __repr__(self):
        return 'Model({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                  self.language,
                                                  self.source)
    
    def getUserLayerModel(self):
        if self.ul_model:
            return self.ul_model
        else:
            print self.source
            self.ul_model = nineml.user_layer.parse(self.source)
            return self.ul_model
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('language', str(self.language))
        root.set('source',   str(self.source))
                
    @classmethod
    def from_xml(self, root, **kwargs):
        id       = root.get('id')
        name     = root.get('name')
        language = root.get('language')
        source   = root.get('source')
        return Model(id, name, language, source)

class Task(sedmlBase):
    xmlTagName = 'task'
    
    def __init__(self, id, name, model, simulation):
        sedmlBase.__init__(self, id, name)
        
        self.model      = model
        self.simulation = simulation
    
    def __repr__(self):
        return 'Task({0}, {1}, {2})'.format(sedmlBase.__repr__(self), 
                                                 self.model.name,
                                                 self.simulation.name)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('modelReference',      self.model.id)
        root.set('simulationReference', self.simulation.id)
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id                  = root.get('id')
        name                = root.get('name')
        modelReference      = root.get('modelReference')
        simulationReference = root.get('simulationReference')
        
        model       = None
        simulation  = None
        models      = kwargs.get('models',      [])
        simulations = kwargs.get('simulations', [])
        for m in models:
            if m.id == modelReference:
                model = m
                break
        for s in simulations:
            if s.id == simulationReference:
                simulation = s
                break
                
        if not model:
            raise RuntimeError('Cannot load Task [{0}]: unable to find the model reference [{1}]'.format(id, modelReference))
        if not simulation:
            raise RuntimeError('Cannot load Task [{0}]: unable to find the simulation reference [{1}]'.format(id, simulationReference))
            
        return Task(id, name, model, simulation)

class DataGenerator(sedmlBase):
    xmlTagName = 'dataGenerator'
    
    def __init__(self, id, name, variables):
        sedmlBase.__init__(self, id, name)
        
        self.variables  = list(variables)
        self.parameters = []
    
    def __repr__(self):
        return 'DataGenerator({0}, {1})'.format(sedmlBase.__repr__(self), self.variables)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        xml_variables = etree.SubElement(root, 'listOfVariables')
        for variable in self.variables:
            xml_variable = etree.SubElement(xml_variables, variable.xmlTagName)
            variable.to_xml(xml_variable)
        
        xml_parameters = etree.SubElement(root, 'listOfParameters')
        for parameter in self.parameters:
            xml_parameter = etree.SubElement(xml_parameters, parameter.xmlTagName)
            parameter.to_xml(xml_parameter)
        
        xml_math = etree.SubElement(root, 'math')
        xml_math.set('xmlns', 'http://www.w3.org/1998/Math/MathML')
        xml_ci = etree.SubElement(xml_math, 'ci')
        xml_ci.text = str(self.name)
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id    = root.get('id')
        name  = root.get('name')
        
        tasks = kwargs.get('tasks', [])
        variables = []
        xml_variables = root.find('%slistOfVariables' % sedml_namespace)
        for xml_variable in xml_variables.getiterator('{0}{1}'.format(sedml_namespace, Variable.xmlTagName)):
            variable = Variable.from_xml(xml_variable, tasks = tasks)
            variables.append(variable)
        
        return DataGenerator(id, name, variables)

class Variable(sedmlBase):
    xmlTagName = 'variable'
    
    def __init__(self, id, name, task, target = None, symbol = None):
        sedmlBase.__init__(self, id, name)
        
        self.task   = task
        self.target = None
        self.symbol = None
        
        if target == None and symbol == None:
            raise RuntimeError('SED-ML: both target abd symbol are None')
        elif target != None and symbol != None:
            raise RuntimeError('SED-ML: target and symbol cannot be specified at the same time')

        if target != None:
            self.target = str(target)
        elif symbol != None:
            self.symbol = str(symbol)

    def __repr__(self):
        return 'Variable({0}, {1}, {2}, {3})'.format(sedmlBase.__repr__(self), 
                                                          self.task.name,
                                                          self.target,
                                                          self.symbol)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        root.set('taskReference', self.task.id)
        if self.symbol:
            root.set('symbol', self.symbol)
        elif self.target:
            root.set('target', self.target)
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id            = root.get('id')
        name          = root.get('name')
        taskReference = root.get('taskReference')
        target        = root.get('target')
        symbol        = root.get('symbol')
        
        task  = None
        tasks = kwargs.get('tasks', [])
        for t in tasks:
            if t.id == taskReference:
                task = t
                break
                
        if not task:
            raise RuntimeError('Cannot load Variable [{0}]: unable to find the task reference [{1}]'.format(id, taskReference))
        
        return Variable(id, name, task, target, symbol)

class Plot2D(sedmlBase):
    xmlTagName = 'plot2D'
    
    def __init__(self, id, name, curves):
        sedmlBase.__init__(self, id, name)
        
        self.curves = list(curves)
    
    def __repr__(self):
        return 'Plot2D({0}, {1})'.format(sedmlBase.__repr__(self), self.curves)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        xml_curves = etree.SubElement(root, 'listOfCurves')
        for curve in self.curves:
            xml_curve = etree.SubElement(xml_curves, curve.xmlTagName)
            curve.to_xml(xml_curve)
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id   = root.get('id')
        name = root.get('name')
        
        curves = []
        data_generators = kwargs.get('data_generators', [])
        xml_curves = root.find('%slistOfCurves' % sedml_namespace)
        for xml_curve in xml_curves.getiterator('{0}{1}'.format(sedml_namespace, Curve.xmlTagName)):
            curve = Curve.from_xml(xml_curve, data_generators = data_generators)
            curves.append(curve)

        return Plot2D(id, name, curves)

class Curve(sedmlBase):
    xmlTagName = 'curve'
    
    def __init__(self, id, name, logX, logY, xDataReference, yDataReference):
        sedmlBase.__init__(self, id, name)
        
        self.logX            = bool(logX)
        self.logY            = bool(logY)
        self.xDataReference = xDataReference
        self.yDataReference = yDataReference
    
    def __repr__(self):
        return 'Curve({0}, {1}, {2}, {3}, {4})'.format(sedmlBase.__repr__(self), 
                                                            self.logX,
                                                            self.logY,
                                                            self.xDataReference,
                                                            self.yDataReference)
    
    def to_xml(self, root):
        sedmlBase.to_xml(self, root)
        
        if self.logX:
            root.set('logX', 'true')
        else:
            root.set('logX', 'false')
        if self.logY:
            root.set('logY', 'true')
        else:
            root.set('logY', 'false')
        root.set('xDataReference', str(self.xDataReference.id))
        root.set('yDataReference', str(self.yDataReference.id))
        
    @classmethod
    def from_xml(self, root, **kwargs):
        id             = root.get('id')
        name           = root.get('name')
        logX           = True if root.get('logX') == 'true' else False
        logY           = True if root.get('logY') == 'true' else False
        xDataReference = root.get('xDataReference')
        yDataReference = root.get('yDataReference')
        
        xDataGenerator  = None
        yDataGenerator  = None
        data_generators = kwargs.get('data_generators', [])
        for dg in data_generators:
            if dg.id == xDataReference:
                xDataGenerator = dg
                break
        for dg in data_generators:
            if dg.id == yDataReference:
                yDataGenerator = dg
                break
        if not xDataGenerator:
            raise RuntimeError('Cannot load Curve [{0}]: unable to find the data generator reference [{1}]'.format(id, xDataReference))
        if not yDataGenerator:
            raise RuntimeError('Cannot load Curve [{0}]: unable to find the data generator reference [{1}]'.format(id, yDataReference))
        
        return Curve(id, name, logX, logY, xDataGenerator, yDataGenerator)

class Experiment:
    xmlTagName = 'sedML'
    
    def __init__(self, simulations, models, tasks, data_generators, outputs):
        self.simulations     = list(simulations)
        self.models          = list(models)
        self.tasks           = list(tasks)
        self.data_generators = list(data_generators)
        self.outputs         = list(outputs)

    def __repr__(self):
        res = 'Experiment('
        for o in self.simulations:
            res += repr(o) + '\n'
        for o in self.models:
            res += repr(o) + '\n'
        for o in self.tasks:
            res += repr(o) + '\n'
        for o in self.data_generators:
            res += repr(o) + '\n'
        for o in self.outputs:
            res += repr(o) + '\n'
        res += ')'
        return res
     
    def get_simulation(self):
        if len(self.simulations) != 1:
            raise RuntimeError('SED-ML: the number of simulations has to be zero')
        return self.simulations[0]
    
    def get_ul_model(self):
        if len(self.models) != 1:
            raise RuntimeError('SED-ML: the number of models has to be zero')
        return self.models[0].getUserLayerModel()
    
    def to_xml(self, filename):
        sedML = etree.Element(self.xmlTagName)
        sedML.set('level',   '1')
        sedML.set('version', '1')
        sedML.set('xmlns',   'http://sed-ml.org/')
        
        xml_simulations = etree.SubElement(sedML, 'listOfSimulations')
        for simulation in self.simulations:
            xml_simulation = etree.SubElement(xml_simulations, simulation.xmlTagName)
            simulation.to_xml(xml_simulation)
        
        xml_models = etree.SubElement(sedML, 'listOfModels')
        for model in self.models:
            xml_model = etree.SubElement(xml_models, model.xmlTagName)
            model.to_xml(xml_model)

        xml_tasks = etree.SubElement(sedML, 'listOfTasks')
        for task in self.tasks:
            xml_task = etree.SubElement(xml_tasks, task.xmlTagName)
            task.to_xml(xml_task)

        xml_datagenerators = etree.SubElement(sedML, 'listOfDataGenerators')
        for datagenerator in self.data_generators:
            xml_datagenerator = etree.SubElement(xml_datagenerators, datagenerator.xmlTagName)
            datagenerator.to_xml(xml_datagenerator)

        xml_outputs = etree.SubElement(sedML, 'listOfOutputs')
        for output in self.outputs:
            xml_output = etree.SubElement(xml_outputs, output.xmlTagName)
            output.to_xml(xml_output)
        
        etree.ElementTree(sedML).write(filename, encoding="utf-8", pretty_print=True, xml_declaration=True)
        
    @classmethod
    def from_xml(cls, filename):
        root = etree.parse(filename).getroot()
        
        simulations     = []
        models          = []
        tasks           = []
        data_generators = []
        outputs         = []
        
        xml_simulations = root.find('%slistOfSimulations' % sedml_namespace)
        for xml_simulation in xml_simulations.getiterator('{0}{1}'.format(sedml_namespace, UniformTimeCourseSimulation.xmlTagName)):
            simulation = UniformTimeCourseSimulation.from_xml(xml_simulation)
            simulations.append(simulation)
        
        xml_models = root.find('%slistOfModels' % sedml_namespace)
        for xml_model in xml_models.getiterator('{0}{1}'.format(sedml_namespace, Model.xmlTagName)):
            model = Model.from_xml(xml_model)
            models.append(model)
        
        xml_tasks = root.find('%slistOfTasks' % sedml_namespace)
        for xml_task in xml_tasks.getiterator('{0}{1}'.format(sedml_namespace, Task.xmlTagName)):
            task = Task.from_xml(xml_task, models = models, simulations = simulations)
            tasks.append(task)
        
        xml_datagenerators = root.find('%slistOfDataGenerators' % sedml_namespace)
        for xml_datagenerator in xml_datagenerators.getiterator('{0}{1}'.format(sedml_namespace, DataGenerator.xmlTagName)):
            dg = DataGenerator.from_xml(xml_datagenerator, tasks = tasks)
            data_generators.append(dg)
        
        xml_outputs = root.find('%slistOfOutputs' % sedml_namespace)
        for xml_output in xml_outputs.getiterator('{0}{1}'.format(sedml_namespace, Plot2D.xmlTagName)):
            plot2d = Plot2D.from_xml(xml_output, data_generators = data_generators)
            outputs.append(plot2d)
        
        sedml_experiment = Experiment(simulations, models, tasks, data_generators, outputs)
        return sedml_experiment
         
if __name__ == "__main__":
    sedml_simulation = UniformTimeCourseSimulation('Brette_simulation', 'Brette_simulation', 0.0, 0.0, 0.06, 600, 'KISAO:0000283')
    sedml_model      = Model('Brette_model', 'Brette_model', 'urn:sedml:language:nineml', 'file://user_layer_model.xml') 
    sedml_task       = Task('task1', 'task1', sedml_model, sedml_simulation)
    
    sedml_variable_time  = Variable('time',  'time',    sedml_task, symbol='urn:sedml:symbol:time')
    sedml_variable_excV0 = Variable('excV0', 'Voltage', sedml_task, target='Group 1.Excitatory population[0].V')
    sedml_variable_excV4 = Variable('excV4', 'Voltage', sedml_task, target='Group 1.Excitatory population[4].V')
    sedml_variable_inhV  = Variable('inhV',  'Voltage', sedml_task, target='Group 1.Inhibitory population[0].V')

    sedml_data_generator_time = DataGenerator('DG_time', 'DG_time', [sedml_variable_time])
    sedml_data_generator_excV = DataGenerator('DG_excV', 'DG_excV', [sedml_variable_excV0, sedml_variable_excV4])
    sedml_data_generator_inhV = DataGenerator('DG_inhV', 'DG_inhV', [sedml_variable_inhV])

    curve_excV = Curve('ExcV', 'ExcV', False, False, sedml_data_generator_time, sedml_data_generator_excV)
    curve_inhV = Curve('InhV', 'InhV', False, False, sedml_data_generator_time, sedml_data_generator_inhV)

    plot_excV  = Plot2D('Plot_excV', 'Plot_excV', [curve_excV])
    plot_inhV  = Plot2D('Plot_inhV', 'Plot_inhV', [curve_inhV])

    sedml_experiment = Experiment([sedml_simulation], 
                                       [sedml_model], 
                                       [sedml_task], 
                                       [sedml_data_generator_time, sedml_data_generator_excV, sedml_data_generator_inhV],
                                       [plot_excV, plot_inhV])
    #print sedml_experiment

    filename = 'sample_sedml.xml'
    sedml_experiment.to_xml(filename)

    sedml_experiment_copy = Experiment.from_xml(filename)
    filename2 = 'sample_sedml - copy.xml'
    sedml_experiment_copy.to_xml(filename2)
