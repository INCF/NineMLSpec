#!/usr/bin/env python

from __future__ import print_function
import json, tempfile, shutil
import nineml
from nineml.abstraction_layer.testing_utils import TestableComponent
import os, sys, math
import numpy
from time import localtime, strftime
from daetools.pyDAE import (
    daeDataReporterLocal, daeSimulation, eDoNotStopAtDiscontinuity,
    daeBaseLog, daeIDAS)
from nineml_daetools_bridge import (
    getAnalogPortsExpressionParser,
    getParametersValuesInitialConditionsExpressionParser,
    getParametersValuesInitialConditionsExpressionParserIdentifiers,
    getObjectFromCanonicalName,
    ninemlReduceAnalogPort, ninemlAnalogPort,
    ninemlSTNRegimesName,
    nineml_daetools_bridge
    )
from nineml_component_inspector import nineml_component_inspector
#import nineml_tex_report
import nineml_html_report

import matplotlib as mpl
# There were some problems in webapp; 'Agg' is a workaround
mpl.use('Agg')
import matplotlib.pyplot as plt

class daeSimulationInputData:
    """
    The class that handles input data for the daetools simulation.
    It can convert to/from python dictionaries and json strings with some basic checks.
    More thorough checks should be added. 
    The data include:
    
    * timeHorizon               : float (in seconds)
    * reportingInterval         : float (in seconds)
    * parameters                : dictionary 'parameter name':float
    * initial_conditions        : dictionary 'variable name':float
    * analog_ports_expressions  : dictionary 'port name':float
    * event_ports_expressions   : dictionary 'port name':string (input expression) 
    * active_regimes            : dictionary 'model name':'active regime name'
    * variables_to_report       : dictionary 'variable|port name':boolean
    
    **Achtung!** All names (keys in dictionaries) are given in canonical form: 
    *toplevel_model.child_model1.child_model2.parameter_name*
    """
    def __init__(self):
        """
        :rtype: 
        :raises: 
        """
        # Dictionaries 'canonical/relative name' : floating-point-value
        self.parameters         = {}
        self.initial_conditions = {}
        # Dictionaries: 'canonical/relative name' : 'expression'
        self.analog_ports_expressions = {}
        self.event_ports_expressions  = {}
        # Dictionary: 'canonical/relative name' : string
        self.active_regimes      = {}
        # Dictionary: 'canonical/relative name' : boolean
        self.variables_to_report = {}

        self.timeHorizon       = 0.0
        self.reportingInterval = 0.0

    def asDictionary(self):
        """
        Returns the simulation data as a python dictionary.
        
        :rtype: python dictionary
        :raises: 
        """
        data = {}
        data['timeHorizon']               = self.timeHorizon
        data['reportingInterval']         = self.reportingInterval
        data['parameters']                = self.parameters
        data['initial_conditions']        = self.initial_conditions
        data['analog_ports_expressions']  = self.analog_ports_expressions
        data['event_ports_expressions']   = self.event_ports_expressions
        data['active_regimes']            = self.active_regimes
        data['variables_to_report']       = self.variables_to_report
        return data
        
    def asJSON(self, sort = True, indent = 2):
        """
        Returns the simulation data as a JSON string.
        
        :param sort: Boolean (should the keys be sorted)
        :param indent: integer (number of blank characters to use as an indent)
        
        :rtype: string (in JSON format)
        :raises: OverflowError, TypeError, ValueError
        """
        data = self.asDictionary()
        return json.dumps(data, sort_keys = sort, indent = indent)

    def loadDictionary(self, dictData):
        """
        Loads the simulation data from a python dictionary.
        
        :param dictData: python dictionary
        
        :rtype:
        :raises: 
        """
        if 'timeHorizon' in dictData:
            self.timeHorizon = float(dictData['timeHorizon'])

        if 'reportingInterval' in dictData:
            self.reportingInterval = float(dictData['reportingInterval'])

        if 'parameters' in dictData:
            temp = dictData['parameters']
            if isinstance(temp, dict):
                self.parameters = temp

        if 'initial_conditions' in dictData:
            temp = dictData['initial_conditions']
            if isinstance(temp, dict):
                self.initial_conditions = temp

        if 'analog_ports_expressions' in dictData:
            temp = dictData['analog_ports_expressions']
            if isinstance(temp, dict):
                self.analog_ports_expressions = temp

        if 'event_ports_expressions' in dictData:
            temp = dictData['event_ports_expressions']
            if isinstance(temp, dict):
                self.event_ports_expressions = temp

        if 'active_regimes' in dictData:
            temp = dictData['active_regimes']
            if isinstance(temp, list):
                self.active_regimes = temp

        if 'variables_to_report' in dictData:
            temp = dictData['variables_to_report']
            if isinstance(temp, dict):
                self.variables_to_report = temp
        
    def loadJSON(self, jsonContent):
        """
        Loads the simulation data from a JSON string.
        
        :param jsonContent: string (in JSON format)
        
        :rtype:
        
        :raises: OverflowError, TypeError, ValueError
        """
        dictData = json.loads(jsonContent)
        self.loadFromDictionary(dictData)
       
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        data = self.asDictionary()
        return str(data)

class ninemlTesterDataReporter(daeDataReporterLocal):
    """
    A tailor-made daetools datareporter. It holds the data reported by the daetools simulation 
    and prepares the data for the report generation. 
    It derives from the daeDataReporterLocal class which does all the processing and keeps the data
    in the 'Process' data member (daeDataReporterProcess object). 
    daeDataReporterProcess class has the following properties:
    
    * Name      : string
    * Domains   : list of daeDataReceiverDomain objects (not used in NineML)
    * Variables : list of daeDataReceiverVariable objects
    
    For more information consult daetools documentation (http://daetools.sourceforge.net/w/index.php/Documentation)
    """
    def __init__(self):
        """
        """
        daeDataReporterLocal.__init__(self)
        self.ProcessName = ""

    def createReportData(self, tmp_folder = '/tmp'):
        """
        Creates matplotlib plots for every variable/port requested and returns the data 
        for the model report as a list of python tuples (one for each plot):
        
        * variable name : string
        * xPoints : 1D numpy array of floats (time values)
        * yPoints : 1D numpy array of floats (variable values)
        * pngName : filename with a PNG image
        * csvName : filename with the plot raw data in CSV format
        * pngPath : path to the PNG image
        * csvPath : path to the raw data CSV file
        
        :param tmp_folder: string (a folder where the plots will be stored)
        
        :rtype: python tuple
        
        :raises: RuntimeError
        """
        fp8  = mpl.font_manager.FontProperties(family='sans-serif', style='normal', variant='normal', weight='normal', size=8)
        fp9  = mpl.font_manager.FontProperties(family='sans-serif', style='normal', variant='normal', weight='normal', size=9)
        fp11 = mpl.font_manager.FontProperties(family='sans-serif', style='normal', variant='normal', weight='normal', size=11)

        font = {'family' : 'sans-serif',
                'weight' : 'normal',
                'size'   : 8}
        mpl.rc('font', **font)
        params = {'axes.labelsize':  9,
                  'text.fontsize':   8,
                  'xtick.labelsize': 8,
                  'ytick.labelsize': 8,
                  'text.usetex':     True}
        mpl.rcParams.update(params)

        plots = []
        for i, var in enumerate(self.Process.Variables):
            fileName   = var.Name
            fileName   = fileName.replace('.', '')
            fileName   = fileName.replace('_', '')
            pngName    = fileName + '.png'
            csvName    = fileName + '.csv'
            pngPath    = tmp_folder + '/' + pngName
            csvPath    = tmp_folder + '/' + csvName
            title      = var.Name.split('.')[-1] + ' = f(t)'
            xAxisLabel = 't'
            yAxisLabel = var.Name
            xPoints    = var.TimeValues
            yPoints    = var.Values.reshape(len(var.Values))

            fig = plt.figure(figsize=(4, 3), dpi=(300))
            ax = fig.add_subplot(111)
            ax.plot(xPoints, yPoints)
            ax.set_title(title)
            ax.set_xlabel(xAxisLabel)
            #ax.set_ylabel(yAxisLabel)
            fig.savefig(pngPath, dpi=(300))
            
            if self._exportCSV(xPoints, yPoints, xAxisLabel, yAxisLabel, csvPath):
                plots.append((var.Name, xPoints, yPoints, pngName, csvName, pngPath, csvPath))
            else:
                plots.append((var.Name, xPoints, yPoints, pngName, None, pngPath, None))

        return plots

    def _exportCSV(self, x, y, xname, yname, filename):
        """
        Private function to create CSV file with the raw simulation data.
        :rtype: Boolean (True if successful)
        """
        try:
            n = len(x)
            f = open(filename, "w")
            f.write('{0},{1}\n'.format(xname, yname))
            for i in range(0, n):
                f.write('%.18e,%.18e\n' % (x[i], y[i]))
            f.close()
            return True
        
        except Exception as e:
            return False

    def Connect(self, ConnectionString, ProcessName):
        """
        Virtual function, a part of the daetools daeDataReporter interface,
        called to connect the data reporter to the corresponding data receiver.
        Here everything is kept in the data reporter so just return True always.
        """
        return True

    def Disconnect(self):
        """
        Virtual function, a part of the daetools daeDataReporter interface,
        called to disconnect the data reporter from the corresponding data receiver.
        Here it always returns True.
        """
        return True

    def IsConnected(self):
        """
        Virtual function, a part of the daetools daeDataReporter interface,
        called to test if the data reporter is connected to the corresponding data receiver.
        Here it always returns True.
        """
        return True

__analog_ports_expression_parser__ = getAnalogPortsExpressionParser()
__values_expression_parser__       = getParametersValuesInitialConditionsExpressionParser(None)

class daetools_model_setup:
    """
    Sets the parameter values, initial conditions and other processing needed.
    It is used by the daetools_simulation class to set-up indicidual models (neurones, synapses etc). 
    naturally it belongs to the daetools_simulation class. However, it is defined as a seperate class 
    for it will be needed to setup params/variables/... for a model that is not a top-level model of 
    a simulation (for instance in a network).
    It defines two functions which are used by the simulation:
    
    * SetUpParametersAndDomains
    * SetUpVariables
    """
    def __init__(self, model, keysAsCanonicalNames, **kwargs):
        """
        :param model: daeModel-derived object
        :param keysAsCanonicalNames: Boolean (True if the keys are canonical names)
        :param **kwargs: python dictionaries containing parameters values, initial conditions, etc.
         * parameters -- python dictionary: 'canonical_name' : (value,units) (default: empty dict)
         * initial_conditions -- python dictionary: 'canonical_name' : (value,units) (default: empty dict)
         * active_regimes -- python dictionary: 'canonical_name' : string (default: empty dict)
         * variables_to_report -- python dictionary: 'canonical_name' : boolean (default: empty dict)
         * analog_ports_expressions -- python dictionary: 'canonical_name' : string (default: empty dict)
         * event_ports_expressions -- python dictionary: 'canonical_name' : string) (default: empty dict)
         * analog_ports_expression_parser -- ExpressionParser object (default: None)
         * values_expression_parser -- ExpressionParser object (default: None)
         * random_number_generators -- python dictionary: 'name': ninemlRNG object (default: empty dict)
        
        :raises: RuntimeError
        """
        self.model                = model
        self.keysAsCanonicalNames = keysAsCanonicalNames

        # Is there a problem if these dictionaries contain unicode strings?
        # (if the input originated from the web form)
        self._parameters               = kwargs.get('parameters',               {})
        self._initial_conditions       = kwargs.get('initial_conditions',       {})
        self._active_regimes           = kwargs.get('active_regimes',           {})
        self._variables_to_report      = kwargs.get('variables_to_report',      {})
        self._analog_ports_expressions = kwargs.get('analog_ports_expressions', {})
        self._event_ports_expressions  = kwargs.get('event_ports_expressions',  {})
        self._random_number_generators = kwargs.get('random_number_generators', {})

        self.intervals = {}
        self.debug     = False
        
        # Initialize reduce ports
        for portName, expression in list(self._analog_ports_expressions.items()):
            if not self.keysAsCanonicalNames:
                portName = self.model.CanonicalName + '.' + portName
            port = getObjectFromCanonicalName(self.model, portName, look_for_ports = True, look_for_reduceports = True)
            if port == None:
                if self.debug:
                    print('Warning: Could not locate port {0}'.format(portName))
                continue
            
            if isinstance(port, ninemlReduceAnalogPort):
                if len(port.Ports) != 0:
                    raise RuntimeError('The reduce port {0} is connected and cannot be set a value'.format(portName))
                a_port = port.addPort()
            elif isinstance(port, ninemlAnalogPort):
                pass

    def _getValue(self, value, name):
        """
        Internal function used to get a value of parameters values and initial conditions.
        It can handle simple numbers and tuples (value, units). The *value* can be a simple number, 
        an expression involving other parameters and variables or a random number distribution.
        
        :rtype: float
        :raises: RuntimeError
        """
        if isinstance(value, tuple):
            if len(value) != 2:
                raise RuntimeError('The value for: {0} must be a tuple in the format (float, units): {1}'.format(name, value))
            
            _value, _units = value
            
            if isinstance(_value, (float, int, long)): # Simple number
                return float(_value)
            
            elif isinstance(_value, nineml.user_layer.RandomDistribution): # A RandomDistribution component
                if not _value.name in self._random_number_generators:
                    raise RuntimeError('Cannot find RandomDistribution component {0}'.format(_value.name))
                
                rng = self._random_number_generators[_value.name]
                return float(rng.next())
            
            elif isinstance(_value, str): # A astring expression (does it exist??)
                return float(__values_expression_parser__.parse_and_evaluate(_value))
            
            else: # Something is wrong
                raise RuntimeError('Invalid parameter: {0} value type specified: {1}-{2}'.format(name, value, type(value)))
        
        elif isinstance(value, (float, int, long)):
            return float(value)
        
        else:
            raise RuntimeError('Invalid parameter: {0} value type specified: {1}-{2}'.format(name, value, type(value)))

    def SetUpParametersAndDomains(self):
        """
        Sets the parameter values. Called automatically by the simulation.
        
        It requires two passes through the list of parameters:
        
         #. Set the values that are simple numerical values.
         #. Set the values that require parsing and (probably) depend on the values of
            parameters with the simple numerical values.
        
        :rtype: None
        :raises: RuntimeError
        """
        __values_expression_parser__ = getParametersValuesInitialConditionsExpressionParserIdentifiers(self.model)
        
        numerical_values  = {}
        expression_values = {}
        
        # First create two dictionaries (numerical_values, expression_values)
        for paramName, value in list(self._parameters.items()):
            if not self.keysAsCanonicalNames:
                paramName = self.model.CanonicalName + '.' + paramName
            parameter = getObjectFromCanonicalName(self.model, paramName, look_for_parameters = True)
            if parameter == None:
                if self.debug:
                    print('Warning: Could not locate parameter {0}'.format(paramName))
                continue
            
            if (isinstance(value, (long, int, float)) or (isinstance(value, tuple) and isinstance(value[0], (long, int, float)))):
                numerical_values[paramName] = parameter, value
            else:
                expression_values[paramName] = parameter, value
                
        # First set the parameters with simple numerical values
        for paramName, (parameter, value) in list(numerical_values.items()):
            v = self._getValue(value, paramName)
            parameter.SetValue(v)
        
        # Then set the parameters with expressions as values
        for paramName, (parameter, expression) in list(expression_values.items()):
            v = self._getValue(expression, paramName)
            parameter.SetValue(v)
        
    def SetUpVariables(self):
        """
        Sets the initial conditions and other stuff. Called automatically by the simulation.
        
        It requires two passes through the list of variables:
        
         #. Set the initial conditions that are simple numerical values.
         #. Set the initial conditions that require parsing and (probably) depend on the values of
            parameters/variables with the simple numerical values.
        
        :rtype: None
        :raises: RuntimeError
        """
        numerical_values  = {}
        expression_values = {}

        # First create two dictionaries (numerical_values, expression_values)
        for varName, value in list(self._initial_conditions.items()):
            if not self.keysAsCanonicalNames:
                varName = self.model.CanonicalName + '.' + varName
            variable = getObjectFromCanonicalName(self.model, varName, look_for_variables = True)
            if variable == None:
                if self.debug:
                    print('Warning: Could not locate variable {0}'.format(varName))
                continue
            
            if (isinstance(value, (long, int, float)) or (isinstance(value, tuple) and isinstance(value[0], (long, int, float)))):
                numerical_values[varName] = variable, value
            else:
                expression_values[varName] = variable, value
        
        # First set the parameters with simple numerical values
        for varName, (variable, value) in list(numerical_values.items()):
            v = self._getValue(value, varName)
            variable.SetInitialCondition(v)
        
        # Then set the parameters with expressions as values
        for varName, (variable, expression) in list(expression_values.items()):
            v = self._getValue(expression, varName)
            variable.SetInitialCondition(v)
        
        for portName, expression in list(self._analog_ports_expressions.items()):
            if not self.keysAsCanonicalNames:
                portName = self.model.CanonicalName + '.' + portName
            if expression == None or expression == '':
                raise RuntimeError('The analog port {0} is not connected and no value has been provided'.format(portName))
            port = getObjectFromCanonicalName(self.model, portName, look_for_ports = True, look_for_reduceports = True)
            if port == None:
                if self.debug:
                    print('Warning: Could not locate port {0}'.format(portName))
                continue
            
            value = float(__analog_ports_expression_parser__.parse_and_evaluate(expression))
            if isinstance(port, ninemlAnalogPort):
                port.value.AssignValue(value)
            elif isinstance(port, ninemlReduceAnalogPort):
                for a_port in port.Ports:
                    a_port.value.AssignValue(value)
            else:
                raise RuntimeError('Unknown port object: {0}'.format(portName))
            
            if self.debug:
                print('  --> Assign the value of the port variable: {0} to {1} (evaluated value: {2})'.format(portName, expression, value))
        
        for portName, expression in list(self._event_ports_expressions.items()):
            if not self.keysAsCanonicalNames:
                portName = self.model.CanonicalName + '.' + portName
            if expression == None or expression == '':
                continue
            port = getObjectFromCanonicalName(self.model, portName, look_for_eventports = True)
            if port == None:
                if self.debug:
                    print('Warning: Could not locate event port {0}'.format(portName))
                continue
            
            str_values = expression.split(',')
            for item in str_values:
                try:
                    value = float(item)
                except ValueError:
                    raise RuntimeError('Cannot convert: {0} to floating point value in the event port expression: {1}'.format(item, expression))
                
                # ACHTUNG, ACHTUNG!!! At this point self.intervals contain only event emit time points!!
                if value in self.intervals:
                    data = self.intervals[value]
                else:
                    data = []
                data.append(port)
                self.intervals[value] = data
            
            if self.debug:
                print('  --> Event port {0} triggers at: {1}'.format(portName, expression))

        for modelName, stateName in list(self._active_regimes.items()):
            if not self.keysAsCanonicalNames:
                modelName = self.model.CanonicalName + '.' + modelName
            stateName = str(stateName)
            stn = getObjectFromCanonicalName(self.model, modelName + '.' + ninemlSTNRegimesName, look_for_stns = True)
            if stn == None:
                if self.debug:
                    print('Warning: Could not locate STN {0}'.format(ninemlSTNRegimesName))
                continue

            if self.debug:
                print('  --> Set the active state in the model: {0} to: {1}'.format(modelName, stateName), 0)
            stn.ActiveState = stateName

        # This should be False by default
        self.model.SetReportingOn(False)
        for varName, value in list(self._variables_to_report.items()):
            if not self.keysAsCanonicalNames:
                varName = self.model.CanonicalName + '.' + varName
            if value:
                variable = getObjectFromCanonicalName(self.model, varName, look_for_variables = True)
                if variable == None:
                    if self.debug:
                        print('Warning: Could not locate variable {0}'.format(varName))
                    continue
                
                if self.debug:
                    print('  --> Report the variable: {0}'.format(varName), 0)
                variable.ReportingOn = True


class nineml_daetools_simulation(daeSimulation):
    """
    nineml_daetools_simulation carries out the simulation of the given (top level) model.
    Used only for simulation of the single AL component (wrapped into the nineml_daetools_bridge object),
    by the NineML WebApp and nineml_desktop_app.
    """
    def __init__(self, model, **kwargs):
        """
        Initializes nineml_daetools_simulation object.
        
        :param model: nineml_daetools_bridge object
        :param **kwargs: python dictionaries containing parameters values, initial conditions, reporting interval, time horizon, etc
        
        :rtype: None
        :raises: RuntimeError
        """
        daeSimulation.__init__(self)
        
        self.TimeHorizon       = float(kwargs.get('timeHorizon',       0.0))
        self.ReportingInterval = float(kwargs.get('reportingInterval', 0.0))

        self.setup = daetools_model_setup(model, True, **kwargs)
        self.m     = model
    
    def SetUpParametersAndDomains(self):
        """
        Sets the parameter values. Called automatically by the simulation.
        
        :rtype: None
        :raises: RuntimeError
        """
        self.setup.SetUpParametersAndDomains()
        
    def SetUpVariables(self):
        """
        Sets the initial conditions and other stuff. Called automatically by the simulation.
        
        :rtype: None
        :raises: RuntimeError
        """
        self.setup.SetUpVariables()
                
    def Run(self):
        """
        Runs the simulation for the specified time horizon reporting the results after every interval
        (either a regular reporting time or spike event) + whenever a discontinuity is encountered.
        If specified, spikes will be generated on corresponding event ports at given times. 
        
        Spike times are merged together with the reporting intervals in the dictionary setup.intervals
        (time : event_port) so that they can be iterated over and the simulation run until the next one. 
        
        :rtype: None
        :raises: RuntimeError
        """
        # Add the normal reporting times
        for t in self.ReportingTimes:
            if not t in self.setup.intervals:
                self.setup.intervals[t] = None
        #for t, ports in sorted(self.setup.intervals.items()):
        #    print('%.18e: %s' % (t, str(ports)))
        
        for t, event_ports in sorted(self.setup.intervals.items()):
            # IDA complains when time horizon is too close to the current time 
            if math.fabs(t - self.CurrentTime) < 1E-5:
                self.Log.Message('WARNING: skipping the time point %.18e: too close to the previous time point' % t, 0)
                continue
            
            # Integrate until 't'
            self.Log.Message('Integrating from %.7f to %.7f ...' % (self.CurrentTime, t), 0)
            self.IntegrateUntilTime(t, eDoNotStopAtDiscontinuity)
            
            # Trigger the events (if any) and reinitialize
            if event_ports:
                for event_port in event_ports:
                    event_port.ReceiveEvent(0.0)
                self.Reinitialize()
            
            # Report the data
            self.ReportData(self.CurrentTime)
   
if __name__ == "__main__":
    """
    # Parser tests for equations with random numbers (should appear only in StateAssignment blocks):
    parser = getEquationsExpressionParser(None)
    print('uniform     =', parser.parse_and_evaluate('1.0 + random.uniform(0.0, 15)'))
    print('normal      =', parser.parse_and_evaluate('1.0 + random.normal()'))
    print('binomial    =', parser.parse_and_evaluate('1.0 + random.binomial(1.0, 0.5)'))
    print('poisson     =', parser.parse_and_evaluate('1.0 + random.poisson(2.3)'))
    print('exponential =', parser.parse_and_evaluate('1.0 + random.exponential(2.0)'))
    exit(0)
    """
    
    """
    Brette et al. 2007
    
    neurone_params = {
                       'tspike' :    ( -1.000, 's'),
                       'V' :         (uniform_distribution, 'V'),
                       'gl' :        ( 1.0E-8, 'S'),
                       'vreset' :    ( -0.060, 'V'),
                       'taurefrac' : (  0.001, 's'),
                       'vthresh' :   ( -0.040, 'V'),
                       'vrest' :     ( -0.060, 'V'),
                       'cm' :        ( 0.2E-9, 'F')
                     }
    
    psr_excitatory_params = {
                             'vrev' : (  0.000, 'V'),
                             'q'    : ( 4.0E-9, 'S'),
                             'tau'  : (  0.005, 's'),
                             'g'    : (  0.000, 'S')
                            }
    """
    timeHorizon       = 1.000
    reportingInterval = 0.001
    parameters = {
        "iaf_1coba.iaf.gl":         (   1E-8, "S"), 
        "iaf_1coba.iaf.vreset":     ( -0.060, "V"), 
        "iaf_1coba.iaf.taurefrac":  (  0.001, "s"), 
        "iaf_1coba.iaf.vthresh":    ( -0.040, "V"), 
        "iaf_1coba.iaf.vrest":      ( -0.060, "V"), 
        "iaf_1coba.iaf.cm":         ( 0.2E-9, "F"),
        
        "iaf_1coba.cobaExcit.vrev": (  0.000, "V"), 
        "iaf_1coba.cobaExcit.q":    ( 4.0E-9, "S"), 
        "iaf_1coba.cobaExcit.tau":  (  0.005, "s"), 
    } 
    initial_conditions = {
        "iaf_1coba.iaf.tspike":  (-1.00, ""), 
        "iaf_1coba.iaf.V":       (-0.045, ""), 
        "iaf_1coba.cobaExcit.g": ( 0.00, "")
    }
    variables_to_report = {
        "iaf_1coba.cobaExcit.I": True, 
        "iaf_1coba.iaf.V": True
    } 
    spike_times = [str(t) for t in numpy.arange(0, 0.20, 0.005)]
    #print(spike_times)
    event_ports_expressions = {
        "iaf_1coba.cobaExcit.spikeinput": '' #', '.join(spike_times)
    } 
    active_regimes = {
        "iaf_1coba.cobaExcit": "cobadefaultregime", 
        "iaf_1coba.iaf": "subthresholdregime"
    } 
    analog_ports_expressions = {}

    # Load the Component:
    nineml_comp  = TestableComponent('hierachical_iaf_1coba')()
    if not nineml_comp:
        raise RuntimeError('Cannot load NineML component')

    # Create Log, Solver, DataReporter and Simulation object
    log          = daeBaseLog()
    daesolver    = daeIDAS()
    
    #from daetools.solvers import pySuperLU as superlu
    #lasolver = superlu.daeCreateSuperLUSolver()
    #daesolver.SetLASolver(lasolver)

    model = nineml_daetools_bridge(nineml_comp.name, nineml_comp, None, '')
    simulation = nineml_daetools_simulation(model, timeHorizon                    = timeHorizon,
                                                   reportingInterval              = reportingInterval,
                                                   parameters                     = parameters,
                                                   initial_conditions             = initial_conditions,
                                                   active_regimes                 = active_regimes,
                                                   analog_ports_expressions       = analog_ports_expressions,
                                                   event_ports_expressions        = event_ports_expressions,
                                                   variables_to_report            = variables_to_report,
                                                   random_number_generators       = {} )
    datareporter = ninemlTesterDataReporter()

    # Set the time horizon and the reporting interval
    simulation.ReportingInterval = reportingInterval
    simulation.TimeHorizon       = timeHorizon

    # Connect data reporter
    simName = simulation.m.Name + strftime(" [%d.%m.%Y %H:%M:%S]", localtime())
    if(datareporter.Connect("", simName) == False):
        sys.exit()

    # Initialize the simulation
    simulation.Initialize(daesolver, datareporter, log)

    # Solve at time=0 (initialization)
    simulation.SolveInitial()

    # Run
    simulation.Run()
    simulation.Finalize()

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_comp)

    tmpFolder = tempfile.gettempdir()
    log_output = log.JoinMessages('\n')
    plots = datareporter.createReportData(tmpFolder)

    dictInputs = {}
    dictInputs['parameters']                = parameters
    dictInputs['initial_conditions']        = initial_conditions
    dictInputs['analog_ports_expressions']  = analog_ports_expressions
    dictInputs['event_ports_expressions']   = event_ports_expressions
    dictInputs['active_regimes']            = active_regimes
    dictInputs['variables_to_report']       = variables_to_report
    dictInputs['timeHorizon']               = timeHorizon
    dictInputs['reportingInterval']         = reportingInterval
    
    tests_data = []
    tests_data.append( ('Dummy test', 'Dummy test notes', dictInputs, plots, log_output, tmpFolder) )

    cwd = sys.path[0]
    shutil.copy2(os.path.join(cwd, 'logo.png'), os.path.join(tmpFolder, 'logo.png'))

    tex  = os.path.join(tmpFolder, 'coba_iaf.tex')
    pdf  = os.path.join(tmpFolder, 'coba_iaf.pdf')
    html = os.path.join(tmpFolder, 'coba_iaf.html')
    
    #nineml_tex_report.createLatexReport(inspector, tests_data, 'nineml-tex-template.tex', tex)
    #res = nineml_tex_report.createPDF(tex, tmpFolder)
    #nineml_tex_report.showFile(pdf)

    nineml_html_report.createHTMLReport(inspector, tests_data, html)
    nineml_html_report.showFile(html)
