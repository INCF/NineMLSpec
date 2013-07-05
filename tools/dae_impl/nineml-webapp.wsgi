from __future__ import print_function
from pprint import pformat
import numpy.random
import os, sys, re, math, json, traceback, os.path, tempfile, shutil, cgi, unicodedata, StringIO
import cPickle as pickle
from time import localtime, strftime, time
import uuid, urlparse, zipfile, cgitb
cgitb.enable()
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
import transaction

__scriptName__ = 'nineml-webapp'
__actionName__ = '__NINEML_ACTION__'

___import_exception___ = None
___import_exception_traceback___ = None
try:
    baseFolder = os.path.join(os.path.dirname(__file__))
    #print('baseFolder = %s' % baseFolder, file=sys.stderr)
    sys.path.append(baseFolder)
    os.environ['HOME'] = tempfile.gettempdir()
    #print(os.environ, file=sys.stderr)

    import nineml
    from nineml.abstraction_layer import readers
    from nineml.abstraction_layer.testing_utils import TestableComponent
    from nineml.abstraction_layer import ComponentClass

    from daetools.pyDAE import pyCore, pyActivity, pyDataReporting, pyIDAS, daeLogs
    from nineml_component_inspector import nineml_component_inspector
    from nineml_daetools_bridge import nineml_daetools_bridge
    from nineml_tex_report import createLatexReport, createPDF
    from nineml_html_report import createHTMLReport
    from nineml_daetools_simulation import daeSimulationInputData, nineml_daetools_simulation, ninemlTesterDataReporter
    from nineml_webapp_common import createErrorPage, getSetupDataForm, createSetupDataPage, getInitialPage, createResultPage, createDownloadResults

except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    ___import_exception___           = str(e)
    ___import_exception_traceback___ = exc_traceback

class daeNineMLWebAppLog(daeLogs.daeBaseLog):
    def __init__(self):
        daeLogs.daeBaseLog.__init__(self)

    def Message(self, message, severity):
        daeLogs.daeBaseLog.Message(self, message, severity)
        #print(self.IndentString + message, file=sys.stderr)

class nineml_webapp:
    def initial_page(self, environ, start_response):
        html = '<html><head><meta http-equiv="Refresh" content="0; url=nineml-webapp.html" /></head><body></body></html>'
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def log(self, function, uuid, message):
        print('{0} [{1}]:'.format(function, uuid), file=sys.stderr)
        print('  {0}'.format(message), file=sys.stderr)
    
    def error(self, e, trace_back = None):
        if not trace_back:
            trace_back = sys.exc_info()[2]
        strTraceBack = '\n'.join(traceback.format_tb(trace_back))
        results = {}
        results["success"]   = False
        results["error"]     = str(e)
        results['content']   = ''
        results['traceback'] = strTraceBack 
        html = json.dumps(results, indent = 2)
        return html

    def getAvailableALComponents(self, fieldStorage, environ, start_response):
        available_components = sorted(TestableComponent.list_available())
        content = ''
        for component in available_components:
            content += '<option value="{0}">{0}</option>\n'.format(component)
        
        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = content
        html = json.dumps(results, indent = 2)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def getApplicationID(self, fieldStorage, environ, start_response):
        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = str(uuid.uuid1())
        html = json.dumps(results, indent = 2)

        print(results['content'], file=sys.stderr)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def uploadALComponent(self, fieldStorage, environ, start_response):
        if not 'xmlNineMLFile' in fieldStorage:
            raise RuntimeError('No input xml file with NineML component has been specified')
        
        xmlFile = fieldStorage['xmlNineMLFile'].file
        nineml_component = readers.XMLReader.read(xmlFile)
        return self.writeComponentToZODB(nineml_component, fieldStorage, environ, start_response)
    
    def uploadALComponentAsXMLString(self, fieldStorage, environ, start_response):
        if not 'xmlFile' in fieldStorage:
            raise RuntimeError('No input string with NineML component has been specified')
        
        xmlFile = StringIO.StringIO(fieldStorage['xmlFile'].value)
        nineml_component = readers.XMLReader.read(xmlFile)
        return self.writeComponentToZODB(nineml_component, fieldStorage, environ, start_response)
        
    def setALComponent(self, fieldStorage, environ, start_response):
        if not 'TestableComponent' in fieldStorage:
            raise RuntimeError('No input NineML component has been specified')

        compName = fieldStorage['TestableComponent'].value
        nineml_component = TestableComponent(compName)()
        if not nineml_component:
            raise RuntimeError('The specified component: {0} could not be loaded'.format(compName))

        return self.writeComponentToZODB(nineml_component, fieldStorage, environ, start_response)

    def writeComponentToZODB(self, nineml_component, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        
        dictZODB = {}
        dictZODB['name']                = nineml_component.name
        dictZODB['nineml_component']    = nineml_component
        dictZODB['tests']               = {}
        dictZODB['REMOTE_ADDR']         = ''
        dictZODB['HTTP_USER_AGENT']     = ''
        if 'REMOTE_ADDR' in environ:
            dictZODB['REMOTE_ADDR'] = environ['REMOTE_ADDR']
        if 'HTTP_USER_AGENT' in environ:
            dictZODB['HTTP_USER_AGENT'] = environ['HTTP_USER_AGENT']
        
        self.writeZODB(applicationID, dictZODB)
    
        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = nineml_component.name
        html = json.dumps(results, indent = 2)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def getInitialValuesAsJSON(self, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        
        nineml_component = dictZODB['nineml_component']

        inspector = nineml_component_inspector()
        inspector.inspect(nineml_component)
        
        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = inspector.jsonData()
        html = json.dumps(results, indent = 2)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def displayGUI(self, fieldStorage, environ, start_response):
        html = ''
        data = {}

        applicationID = self.applicationIDFromDictionary(fieldStorage)
        
        if 'InitialValues' in fieldStorage:
            try:
                #print('JSON data: ' + str(fieldStorage['InitialValues'].value), file=sys.stderr)
                data = json.loads(fieldStorage['InitialValues'].value)
            except Exception as e:
                #print('JSON exception: ' + str(e), file=sys.stderr)
                pass
        
        simulation_data = daeSimulationInputData()
        simulation_data.loadDictionary(data)
        
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        
        nineml_component = dictZODB['nineml_component']
        
        inspector = nineml_component_inspector()
        inspector.inspect(nineml_component, timeHorizon              = simulation_data.timeHorizon,
                                            reportingInterval        = simulation_data.reportingInterval,
                                            parameters               = simulation_data.parameters,
                                            initial_conditions       = simulation_data.initial_conditions,
                                            active_regimes           = simulation_data.active_regimes,
                                            analog_ports_expressions = simulation_data.analog_ports_expressions,
                                            event_ports_expressions  = simulation_data.event_ports_expressions,
                                            variables_to_report      = simulation_data.variables_to_report)

        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = inspector.generateHTMLForm()
        html = json.dumps(results, indent = 2)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def addTest(self, fieldStorage, environ, start_response):
        testName, testDescription, simulation_data = self.getSimulationData(fieldStorage)
        return self.addTestToZODB(testName, testDescription, simulation_data, fieldStorage, environ, start_response)

    def addTestSkipGUI(self, fieldStorage, environ, start_response):
        if 'InitialValues' in fieldStorage:
            data = json.loads(fieldStorage['InitialValues'].value)
        
        if 'testName' in fieldStorage:
            testName = str(fieldStorage['testName'].value)
        else:
            testName = 'test-no.' + str(len(tests) + 1)
        
        if 'testDescription' in fieldStorage:
            testDescription = str(fieldStorage['testDescription'].value)
        else:
            testDescription = ''
        
        simulation_data = daeSimulationInputData()
        simulation_data.loadDictionary(data)
        
        return self.addTestToZODB(testName, testDescription, simulation_data, fieldStorage, environ, start_response)

    def addTestToZODB(self, testName, testDescription, simulation_data, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        
        valid = re.compile(r"[a-zA-Z0-9 _-]+$")
        if not valid.match(testName):
            raise RuntimeError('Test names can contain only alpha-numeric characters, space, _ and -') 
        
        tests = dictZODB['tests']
        tests[testName] = (testDescription, simulation_data)          
        dictZODB['tests'] = tests
        self.writeZODB(applicationID, dictZODB)
        
        results = {}
        results['success'] = True
        results['error']   = ''
        results['content'] = simulation_data.asJSON()
        html = json.dumps(results, indent = 2)
            
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def getSimulationData(self, fieldStorage):
        testName = ''
        testDescription = ''
        timeHorizon = 0.0
        reportingInterval = 0.0
        parameters = {}
        initial_conditions = {}
        analog_ports_expressions = {}
        event_ports_expressions = {}
        active_regimes = {}
        variables_to_report = {}
        
        if 'testName' in fieldStorage:
            testName = str(fieldStorage['testName'].value)
        if 'testDescription' in fieldStorage:
            testDescription = str(fieldStorage['testDescription'].value)
        if 'timeHorizon' in fieldStorage:
            timeHorizon = float(fieldStorage['timeHorizon'].value)
        if 'reportingInterval' in fieldStorage:
            reportingInterval = float(fieldStorage['reportingInterval'].value)

        for key in fieldStorage:
            value = fieldStorage[key].value
            names = key.split('.')
            #print(str(key) + ' : ' + str(value), file=sys.stderr)
            if len(names) > 0:
                canonicalName = '.'.join(names[1:])

                if names[0] == nineml_component_inspector.categoryParameters:
                    parameters[canonicalName] = float(value)

                elif names[0] == nineml_component_inspector.categoryInitialConditions:
                    initial_conditions[canonicalName] = float(value)

                elif names[0] == nineml_component_inspector.categoryActiveStates:
                    active_regimes[canonicalName] = value

                elif names[0] == nineml_component_inspector.categoryAnalogPortsExpressions:
                    analog_ports_expressions[canonicalName] = value

                elif names[0] == nineml_component_inspector.categoryEventPortsExpressions:
                    event_ports_expressions[canonicalName] = value

                elif names[0] == nineml_component_inspector.categoryVariablesToReport:
                    if value == 'on':
                        variables_to_report[canonicalName] = True

        simulation_data = daeSimulationInputData()
        simulation_data.timeHorizon              = timeHorizon
        simulation_data.reportingInterval        = reportingInterval
        simulation_data.parameters               = parameters
        simulation_data.initial_conditions       = initial_conditions
        simulation_data.analog_ports_expressions = analog_ports_expressions
        simulation_data.event_ports_expressions  = event_ports_expressions
        simulation_data.active_regimes           = active_regimes
        simulation_data.variables_to_report      = variables_to_report
        
        #print(testName, testDescription, file=sys.stderr)
        #print(simulation_data, file=sys.stderr)
        
        return testName, testDescription, simulation_data
        
    def readZODB(self, key):
        try:
            _storage_    = FileStorage(baseFolder + '/zodb/nineml-webapp.zodb')
            _db_         = DB(_storage_)
            _connection_ = _db_.open()
            _root_       = _connection_.root()
        
            if not key in _root_:
                raise RuntimeError('Cannot read key: {0} from database'.format(key))
            return _root_[key]
        
        finally:
            transaction.abort()
            _connection_.close()
            _db_.close()
            _storage_.close()
        
    def writeZODB(self, key, data):
        try:
            _storage_    = FileStorage(baseFolder + '/zodb/nineml-webapp.zodb')
            _db_         = DB(_storage_)
            _connection_ = _db_.open()
            _root_       = _connection_.root()
            
            _root_[key] = data
            transaction.commit()
        
        except Exception as e:
            print(str(e), file=sys.stderr)

        finally:
            transaction.abort()
            _connection_.close()
            _db_.close()
            _storage_.close()
    
    def generateReport(self, fieldStorage, environ, start_response):
        try:
            pdf = None
            htm = None
            zip = None
            html = ''
            test_reports = ''
            tests_data = []
            texReport = ''
            pdfReport = ''
            htmlReport = ''
            zipReport = ''
            tmpFolder = ''
            
            applicationID = self.applicationIDFromDictionary(fieldStorage)
            dictZODB = self.readZODB(applicationID)
            if not dictZODB:
                raise RuntimeError('Invalid application ID has been specified') 
            
            tests            = dictZODB['tests']
            nineml_component = dictZODB['nineml_component']
            inspector = nineml_component_inspector()
            inspector.inspect(nineml_component)
            
            tmpFolder = self.create_temp_folder()
            
            if len(tests) > 0:
                test_reports, tests_data, zip = self.do_tests(nineml_component, tmpFolder, applicationID, tests)
                
            texReport  = '{0}/{1}.tex'.format(tmpFolder, applicationID)
            pdfReport  = '{0}/{1}.pdf'.format(tmpFolder, applicationID)
            htmlReport = '{0}/{1}.html'.format(tmpFolder, applicationID)

            # Copy the logo image to tmp folder
            shutil.copy2(os.path.join(baseFolder, 'logo.png'), 
                         os.path.join(tmpFolder, 'logo.png'))
            # Generate Tex report
            createLatexReport(inspector, tests_data, os.path.join(baseFolder, 'nineml-tex-template.tex'), texReport, tmpFolder)

            # Generate PDF report
            createPDF = os.path.join(tmpFolder, 'createPDF.sh')
            createPDFfile = open(createPDF, "w")
            createPDFfile.write('cd {0}\n'.format(tmpFolder))
            # Run it twice because of the problems with the Table Of Contents (we need two passes)
            createPDFfile.write('/usr/bin/pdflatex -interaction=nonstopmode {0}\n'.format(texReport))
            createPDFfile.write('/usr/bin/pdflatex -interaction=nonstopmode {0}\n'.format(texReport))
            createPDFfile.close()
            os.system('sh {0}'.format(createPDF))

            # Read the contents of the report into a variable (to be sent together with the .html part)
            if os.path.isfile(pdfReport):
                pdf = open(pdfReport, "rb").read()
            
            # Generate HTML report
            createHTMLReport(inspector, tests_data, htmlReport, tmpFolder)
            
            # Read the contents of the html report into a variable (to be sent together with the .html part)
            if os.path.isfile(htmlReport):
                htm = open(htmlReport, "rb").read()

            dictZODB = self.readZODB(applicationID)
            dictZODB['pdfReport']   = pdf
            dictZODB['htmlReport']  = htm
            dictZODB['zipReport']   = zip
            self.writeZODB(applicationID, dictZODB)
        
        finally:
            # Remove temporary directory
            if os.path.isdir(tmpFolder):
                shutil.rmtree(tmpFolder)
            
        enablePDF  = False
        enableHTML = False
        enableZIP  = False
        if pdf:
            enablePDF = True
        if htm:
            enableHTML = True
        if zip:
            enableZIP = True
        
        results = {}
        results['success']      = True
        results['error']        = ''
        results['content']      = {'pdfAvailable'  : enablePDF,
                                   'htmlAvailable' : enableHTML,
                                   'zipAvailable'  : enableZIP}
        results['pdfAvailable']  = enablePDF
        results['htmlAvailable'] = enableHTML
        results['zipAvailable']  = enableZIP
        html = json.dumps(results, indent = 2)
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def downloadPDF(self, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        pdf  = dictZODB['pdfReport']
        name = dictZODB['name']
        html = str(pdf)        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/pdf'),
                                  ('Content-Disposition', 'attachment; filename={0}.pdf'.format(name)),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def downloadHTML(self, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        html = dictZODB['htmlReport']
        name = dictZODB['name']
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Disposition', 'attachment; filename={0}.html'.format(name)),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def downloadZIP(self, fieldStorage, environ, start_response):
        applicationID = self.applicationIDFromDictionary(fieldStorage)
        dictZODB = self.readZODB(applicationID)
        if not dictZODB:
            raise RuntimeError('Invalid application ID has been specified') 
        zip  = dictZODB['zipReport']
        name = dictZODB['name']
        html = str(zip)        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/zip'),
                                  ('Content-Disposition', 'attachment; filename={0}.zip'.format(name)),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def do_tests(self, nineml_component, tmpFolder, applicationID, tests):
        html       = ''
        zip        = None
        tests_data = []
        test_reports = ''
        
        zipReport = '{0}/{1}.zip'.format(tmpFolder, applicationID)
        
        for testName, test in tests.items():
            tmp = self.create_temp_folder(tmpFolder)
            testDescription, simulation_data = test
            isOK, results = self.run_test(nineml_component, simulation_data, tmp, testName, testDescription)
        
            print('isOK: ' + str(isOK), file=sys.stderr)
            if isOK:
                testName, testDescription, dictInputs, plots, log_output = results
                print('plots = ' + str(plots), file=sys.stderr)
                tests_data.append( (testName, testDescription, dictInputs, plots, log_output, tmp) )
                test_reports += 'Test status: {0} [SUCCEEDED]'.format(testName)
            else:
                testName, testDescription, dictInputs, plots, log_output, error = results
                test_reports += 'Test status: {0} [FAILED]\n'.format(testName)
                test_reports += error
        
        self.pack_tests_data(zipReport, tests_data)
        if os.path.isfile(zipReport):
            zip = open(zipReport, "rb").read()
        
        return test_reports, tests_data, zip

    def applicationIDFromDictionary(self, fieldStorage):
        if not '__NINEML_WEBAPP_ID__' in fieldStorage:
            raise RuntimeError('No application ID has been specified')

        applicationID   = fieldStorage['__NINEML_WEBAPP_ID__'].value
        if applicationID == '':
            raise RuntimeError('No application ID has been specified')
        return applicationID
        
    def generate_applicationID(self):
        return str(uuid.uuid1())
    
    def create_temp_folder(self, dir = None):
        tmpFolder = tempfile.mkdtemp(prefix='nineml-webapp-', dir = dir)
        os.chmod(tmpFolder, 0777)
        return tmpFolder

    def pack_tests_data(self, zipReport, tests_data):
        if len(tests_data) == 0:
            return
            
        zip = zipfile.ZipFile(zipReport, "w")
        
        for i, test_data in enumerate(tests_data):
            testName, testDescription, dictInputs, plots, log_output, tmpFolder = test_data
            #testFolder = 'test-no.{0}/'.format(i+1, testName) 
            testFolder = '{0}/'.format(testName) 
            
            # Write log file contents
            logName = '__log_output__.txt'
            f = open(tmpFolder + '/' + logName, "w")
            f.write(log_output)
            f.close()
            zip.write(tmpFolder + '/' + logName, testFolder + logName)

            # Write JSON input file
            jsonName = '__json_simulation_input__.txt'
            f = open(tmpFolder + '/' + jsonName, "w")
            json.dump(dictInputs, f, indent = 2)
            f.close()
            zip.write(tmpFolder + '/' + jsonName, testFolder + jsonName)

            # Write .png and .csv files
            for plot in plots:
                varName, xPoints, yPoints, pngName, csvName, pngPath, csvPath = plot
                # it was tmpFolder + '/' + pngName before
                if pngName:
                    zip.write(pngPath, testFolder + pngName)
                if csvName:
                    zip.write(csvPath, testFolder + csvName)
        
        zip.close()
    
    def run_test(self, nineml_component, simulation_data, tmpFolder, testName, testDescription):
        try:
            log_output  = ''
            log          = None
            daesolver    = None
            datareporter = None
            model        = None
            simulation   = None
            dictInputs = {}
            
            # Create Log, DAESolver, DataReporter and Simulation object
            log          = daeNineMLWebAppLog()
            daesolver    = pyIDAS.daeIDAS()
            datareporter = ninemlTesterDataReporter()
            model        = nineml_daetools_bridge(nineml_component.name, nineml_component, None, '')
            simulation   = nineml_daetools_simulation(model, timeHorizon                    = simulation_data.timeHorizon,
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
                raise RuntimeError('Cannot connect a TCP/IP datareporter; did you forget to start daePlotter?')

            # Initialize the simulation
            simulation.Initialize(daesolver, datareporter, log)

            # Save the model reports for all models
            #simulation.m.SaveModelReport(simulation.m.Name + ".xml")
            #simulation.m.SaveRuntimeModelReport(simulation.m.Name + "-rt.xml")

            # Solve at time=0 (initialization)
            simulation.SolveInitial()

            # Run
            simulation.Run()
            simulation.Finalize()

            log_output = log.JoinMessages('\n')
            dictInputs = simulation_data.asDictionary()
            plots      = datareporter.createReportData(tmpFolder)

            return True, (testName, testDescription, dictInputs, plots, log_output)
            
        except Exception as e:
            print(str(e), file=sys.stderr)
            if log:
                log_output = '<pre>{0}</pre>'.format(log.JoinMessages('\n'))
            return False, (testName, testDescription, dictInputs, None, log_output, str(e))
        
    def __call__(self, environ, start_response):
        try:
            html = ''
            if not ___import_exception___:
                fieldStorage = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ) 
                if not __actionName__ in fieldStorage:
                    return self.initial_page(environ, start_response)
                    #raise RuntimeError('Phase argument must be specified')

                action = fieldStorage[__actionName__].value
                
                if action == 'getAvailableALComponents':
                    return self.getAvailableALComponents(fieldStorage, environ, start_response)
                    
                elif action == 'getApplicationID':
                    return self.getApplicationID(fieldStorage, environ, start_response)
                
                elif action == 'uploadALComponent':
                    return self.uploadALComponent(fieldStorage, environ, start_response)
                
                elif action == 'uploadALComponentAsXMLString':
                    return self.uploadALComponentAsXMLString(fieldStorage, environ, start_response)
                
                elif action == 'setALComponent':
                    return self.setALComponent(fieldStorage, environ, start_response)
                
                elif action == 'displayGUI':
                    return self.displayGUI(fieldStorage, environ, start_response)
                    
                elif action == 'getInitialValuesAsJSON':
                    return self.getInitialValuesAsJSON(fieldStorage, environ, start_response)
                
                elif action == 'addTest':
                    return self.addTest(fieldStorage, environ, start_response)
                    
                elif action == 'addTestSkipGUI':
                    return self.addTestSkipGUI(fieldStorage, environ, start_response)
                
                elif action == 'generateReport':
                    return self.generateReport(fieldStorage, environ, start_response)
                
                elif action == 'downloadPDF':
                    return self.downloadPDF(fieldStorage, environ, start_response)
                
                elif action == 'downloadHTML':
                    return self.downloadHTML(fieldStorage, environ, start_response)
                
                elif action == 'downloadZIP':
                    return self.downloadZIP(fieldStorage, environ, start_response)
                
                else:
                    raise RuntimeError('Invalid action argument specified: {0}'.format(action))
            else:
                html = self.error(___import_exception___, ___import_exception_traceback___)

        except Exception as e:
            html = self.error(e)

        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/json'),
                                  ('Content-Length', str(output_len))])
        return [html]

application = nineml_webapp()