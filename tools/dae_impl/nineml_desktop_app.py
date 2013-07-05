#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os, sys, tempfile, traceback, shutil
from time import localtime, strftime
from nineml.abstraction_layer.testing_utils import TestableComponent
from PyQt4 import QtGui
from nineml_component_inspector import nineml_component_inspector
from nineml_tex_report import createLatexReport, createPDF, showFile

def test_Izhikevich():
    nineml_component = TestableComponent('izhikevich')()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component')

    timeHorizon = 1
    reportingInterval = 0.001
    parameters = {
                    "Izhikevich.a": 0.02,
                    "Izhikevich.b": 0.2,
                    "Izhikevich.c": -0.05,
                    "Izhikevich.d": 2.0,
                    "Izhikevich.theta": 0.03
                 }
    initial_conditions = {
                            "Izhikevich.U": 0.0,
                            "Izhikevich.V": -0.07
                         }
    analog_ports_expressions = {
                                  "Izhikevich.Isyn": "0.1"
                               }
    event_ports_expressions = {}
    active_regimes = {}
    variables_to_report = {
                             'Izhikevich.U' : True,
                             'Izhikevich.V' : True
                          }

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_component, timeHorizon              = timeHorizon,
                                        reportingInterval        = reportingInterval,
                                        parameters               = parameters,
                                        initial_conditions       = initial_conditions,
                                        active_regimes           = active_regimes,
                                        analog_ports_expressions = analog_ports_expressions,
                                        event_ports_expressions  = event_ports_expressions,
                                        variables_to_report      = variables_to_report)
    results = inspector.showQtGUI()
    return results, inspector

def test_hierachical_iaf_1coba():
    nineml_component = TestableComponent('hierachical_iaf_1coba')()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component')

    timeHorizon =  1.0
    reportingInterval = 0.001 
    initial_conditions = {
        "iaf_1coba.iaf.tspike": -1.0, 
        "iaf_1coba.iaf.V": -0.060, 
        "iaf_1coba.cobaExcit.g": 0.0
    }
    parameters = {
        "iaf_1coba.iaf.gl": 1E-8, 
        "iaf_1coba.iaf.vreset": -0.060, 
        "iaf_1coba.iaf.taurefrac": 0.001, 
        "iaf_1coba.iaf.vthresh": -0.040, 
        "iaf_1coba.iaf.vrest": -0.060, 
        "iaf_1coba.iaf.cm": 0.2E-9,
        
        "iaf_1coba.cobaExcit.vrev": 0.0, 
        "iaf_1coba.cobaExcit.q": 4.0E-9, 
        "iaf_1coba.cobaExcit.tau": 0.005
    } 
    variables_to_report = {
        "iaf_1coba.cobaExcit.I": True, 
        "iaf_1coba.iaf.V": True
    } 
    event_ports_expressions = {
        "iaf_1coba.cobaExcit.spikeinput": "0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90"
    } 
    active_regimes = {
        "iaf_1coba.cobaExcit": "cobadefaultregime", 
        "iaf_1coba.iaf": "subthresholdregime"
    } 
    analog_ports_expressions = {}

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_component, timeHorizon              = timeHorizon,
                                        reportingInterval        = reportingInterval,
                                        parameters               = parameters,
                                        initial_conditions       = initial_conditions,
                                        active_regimes           = active_regimes,
                                        analog_ports_expressions = analog_ports_expressions,
                                        event_ports_expressions  = event_ports_expressions,
                                        variables_to_report      = variables_to_report)
    results = inspector.showQtGUI()
    return results, inspector

def test_coba_synapse():
    nineml_component = TestableComponent('coba_synapse')()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component')

    timeHorizon = 1
    reportingInterval = 0.001
    parameters = {
        'CobaSyn.q' : 4.0E-9,
        'CobaSyn.tau' : 0.005,
        'CobaSyn.vrev' : 0.0
    }
    initial_conditions = {
        'CobaSyn.g' : 1E-8,
    }
    analog_ports_expressions = {
        'CobaSyn.V' : -0.050
    }
    event_ports_expressions = {
        'CobaSyn.spikeinput' : '' #'0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90'
    }
    active_regimes = {
        'CobaSyn' : 'cobadefaultregime'
    }
    variables_to_report = {
        'CobaSyn.I' : True
    }

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_component, timeHorizon              = timeHorizon,
                                        reportingInterval        = reportingInterval,
                                        parameters               = parameters,
                                        initial_conditions       = initial_conditions,
                                        active_regimes           = active_regimes,
                                        analog_ports_expressions = analog_ports_expressions,
                                        event_ports_expressions  = event_ports_expressions,
                                        variables_to_report      = variables_to_report)
    results = inspector.showQtGUI()
    return results, inspector

def test_iaf():
    nineml_component = TestableComponent('iaf')()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component')

    timeHorizon = 1
    reportingInterval = 0.001
    parameters = {
        'iaf.cm' : 0.2E-9,
        'iaf.gl' : 1E-8,
        'iaf.taurefrac' : 0.001,
        'iaf.vreset' : -0.060,
        'iaf.vrest' : -0.060,
        'iaf.vthresh' : -0.040
    }
    initial_conditions = {
        'iaf.V' : -0.050,
        'iaf.tspike' : -1.0
    }
    analog_ports_expressions = {
        'iaf.ISyn' : 0.0
    }
    event_ports_expressions = {}
    active_regimes = {
        'iaf' : 'subthresholdregime'
    }
    variables_to_report = {
        'iaf.V' : True
    }

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_component, timeHorizon              = timeHorizon,
                                        reportingInterval        = reportingInterval,
                                        parameters               = parameters,
                                        initial_conditions       = initial_conditions,
                                        active_regimes           = active_regimes,
                                        analog_ports_expressions = analog_ports_expressions,
                                        event_ports_expressions  = event_ports_expressions,
                                        variables_to_report      = variables_to_report)
    results = inspector.showQtGUI()
    return results, inspector

def test_other(component_name):
    nineml_component = TestableComponent(component_name)()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component {0}'.format(component_name))

    inspector = nineml_component_inspector()
    inspector.inspect(nineml_component)
    results = inspector.showQtGUI()
    return results, inspector

if __name__ == "__main__":
    tests_data = []
    tmpFolder = tempfile.gettempdir()
    
    app = QtGui.QApplication(sys.argv)
    components = sorted(TestableComponent.list_available())
    component_name, ok = QtGui.QInputDialog.getItem(None, "nineml_desktop_app", "Select the testable component name", components, 0, False)
    if not ok:
       exit(0) 

    component_name = str(component_name)
    if(component_name == 'iaf'):
        results, inspector = test_iaf()
    elif(component_name == 'coba_synapse'):
        results, inspector = test_coba_synapse()
    elif(component_name == 'hierachical_iaf_1coba'):
        results, inspector = test_hierachical_iaf_1coba()
    else:
        results, inspector = test_other(component_name)
    
    if results:
        try:
            from daetools.pyDAE import daeSimulationInputData, daeIDAS, daePythonStdOutLog
            from nineml_daetools_bridge import createExpressionParser, nineml_daetools_bridge
            from nineml_daetools_simulation import ninemlTesterDataReporter, nineml_daetools_simulation
            
            testName, testDescription, inputs = results
            simulation_data = daeSimulationInputData()
            simulation_data.timeHorizon              = inputs['timeHorizon']
            simulation_data.reportingInterval        = inputs['reportingInterval']
            simulation_data.parameters               = inputs['parameters']
            simulation_data.initial_conditions       = inputs['initial_conditions']
            simulation_data.active_regimes           = inputs['active_regimes']
            simulation_data.analog_ports_expressions = inputs['analog_ports_expressions']
            simulation_data.event_ports_expressions  = inputs['event_ports_expressions']
            simulation_data.variables_to_report      = inputs['variables_to_report']
            
            parser = createExpressionParser()
            
            # Create Log, DAESolver, DataReporter and Simulation object
            log          = daePythonStdOutLog()
            daesolver    = daeIDAS()
            datareporter = ninemlTesterDataReporter() # daeTCPIPDataReporter()
            model        = nineml_daetools_bridge(inspector.ninemlComponent.name, inspector.ninemlComponent, None, '')
            
            simulation  = nineml_daetools_simulation(model, timeHorizon                    = simulation_data.timeHorizon,
                                                            reportingInterval              = simulation_data.reportingInterval,
                                                            parameters                     = simulation_data.parameters,
                                                            initial_conditions             = simulation_data.initial_conditions,
                                                            active_regimes                 = simulation_data.active_regimes,
                                                            analog_ports_expressions       = simulation_data.analog_ports_expressions,
                                                            event_ports_expressions        = simulation_data.event_ports_expressions,
                                                            variables_to_report            = simulation_data.variables_to_report)

            # Set the time horizon and the reporting interval
            simulation.ReportingInterval = simulation_data.reportingInterval
            simulation.TimeHorizon       = simulation_data.timeHorizon

            # Connect data reporter
            simName = simulation.m.Name + strftime(" [%d.%m.%Y %H:%M:%S]", localtime())
            if(datareporter.Connect("", simName) == False):
                sys.exit()

            # Initialize the simulation
            simulation.Initialize(daesolver, datareporter, log)
            
            # Solve at time=0 (initialization)
            simulation.SolveInitial()
            
            #simulation.m.SaveModelReport(simulation.m.Name + ".xml")
            #simulation.m.SaveRuntimeModelReport(simulation.m.Name + "-rt.xml")
            
            # Run
            simulation.Run()
            simulation.Finalize()
            
            dictInputs = {}
            dictInputs['parameters']                = simulation_data.parameters
            dictInputs['initial_conditions']        = simulation_data.initial_conditions
            dictInputs['analog_ports_expressions']  = simulation_data.analog_ports_expressions
            dictInputs['event_ports_expressions']   = simulation_data.event_ports_expressions
            dictInputs['active_regimes']            = simulation_data.active_regimes
            dictInputs['variables_to_report']       = simulation_data.variables_to_report
            dictInputs['timeHorizon']               = simulation_data.timeHorizon
            dictInputs['reportingInterval']         = simulation_data.reportingInterval
            log_output = log.JoinMessages('\n')
            plots = datareporter.createReportData(tmpFolder)
            tests_data.append( (testName, testDescription, dictInputs, plots, log_output, tmpFolder) )
        
        except ImportError as e:
            print("Failed to load daetools modules; is it installed?")
            print(str(e))
        
        except Exception as e:
            print("Component test failed: ")
            print(str(e))
            exc_traceback = sys.exc_info()[2]
            print('\n'.join(traceback.format_tb(exc_traceback)), file=sys.stderr)
            
    tex = os.path.join(tmpFolder, inspector.ninemlComponent.name + '.tex')
    pdf = os.path.join(tmpFolder, inspector.ninemlComponent.name + '.pdf')
    
    cwd = sys.path[0]
    shutil.copy2(os.path.join(cwd, 'logo.png'), os.path.join(tmpFolder, 'logo.png'))

    createLatexReport(inspector, tests_data, 'nineml-tex-template.tex', tex)
    res = createPDF(tex, tmpFolder)
    showFile(pdf)
