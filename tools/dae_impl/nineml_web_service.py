#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, httplib, urllib, re
import json

class nineml_web_service:
    def __init__(self, server = 'nineml-app.incf.org', port = 80):
        self.headers = {'Content-type': 'application/x-www-form-urlencoded', 
                        'User-Agent'  : 'NineML WebService Application/1.0',
                        'Accept'      : 'text/plain'}
        self.http_connection = httplib.HTTPConnection(server, port)
        self._getApplicationID()

    def __del__(self):
        self.http_connection.close()
        
    def getAvailableALComponents(self):
        parameters = {'__NINEML_ACTION__' : 'getAvailableALComponents'}
        self._sendRequest(parameters, self.headers)
        available_components, response = self._getResponse()
        return available_components

    def setALComponent(self, testableComponentName):
        parameters = {'__NINEML_ACTION__'    : 'setALComponent',
                      '__NINEML_WEBAPP_ID__' : self.applicationID,
                      'TestableComponent'    : testableComponentName
                     }
        self._sendRequest(parameters, self.headers)
        component_name, response = self._getResponse()
        return component_name
    
    def uploadALComponent(self, xmlFile):
        f = open(xmlFile, "r")
        xml = f.read()
        f.close()

        parameters = {'__NINEML_ACTION__'    : 'uploadALComponentAsXMLString',
                      '__NINEML_WEBAPP_ID__' : self.applicationID,
                      'xmlFile'              : xml
                     }
        self._sendRequest(parameters, self.headers)
        component_name, response = self._getResponse()
        return component_name
    
    def getInitialValuesAsJSON(self):
        parameters = {'__NINEML_ACTION__'    : 'getInitialValuesAsJSON',
                      '__NINEML_WEBAPP_ID__' : self.applicationID
                     }
        self._sendRequest(parameters, self.headers)
        _json, response = self._getResponse()
        return _json
        
    def displayGUI(self, initialValues = ''):
        parameters = {'__NINEML_ACTION__'    : 'displayGUI',
                      '__NINEML_WEBAPP_ID__' : self.applicationID,
                      'InitialValues'        : initialValues
                     }
        self._sendRequest(parameters, self.headers)
        gui, response = self._getResponse()
        return gui
    
    def addTest(self, testName, testDescription, initialValues):
        parameters = {'__NINEML_ACTION__'    : 'addTestSkipGUI',
                      '__NINEML_WEBAPP_ID__' : self.applicationID,
                      'InitialValues'        : initialValues,
                      'testName'             : testName,
                      'testDescription'      : testDescription
                     }
        self._sendRequest(parameters, self.headers)
        validatedInitialValues, response = self._getResponse()
        return validatedInitialValues

    def generateReport(self):
        parameters = {'__NINEML_ACTION__'    : 'generateReport',
                      '__NINEML_WEBAPP_ID__' : self.applicationID
                     }
        self._sendRequest(parameters, self.headers)
        data, response = self._getResponse()
        return data

    def downloadPDF(self, **kwargs):
        def_filename     = kwargs.get('filename',         None)
        openInDefaultApp = kwargs.get('openInDefaultApp', True)
       
        parameters = {'__NINEML_ACTION__'    : 'downloadPDF',
                      '__NINEML_WEBAPP_ID__' : self.applicationID
                     }
        self._sendRequest(parameters, self.headers)
        pdf, response = self._getResponse()
        filename      = self._getAttachmentFilename(response)
        return filename, pdf
        
    def downloadHTML(self, **kwargs):
        def_filename     = kwargs.get('filename',         None)
        openInDefaultApp = kwargs.get('openInDefaultApp', True)

        parameters = {'__NINEML_ACTION__'    : 'downloadHTML',
                      '__NINEML_WEBAPP_ID__' : self.applicationID
                     }
        self._sendRequest(parameters, self.headers)
        html, response = self._getResponse()
        filename      = self._getAttachmentFilename(response)
        return filename, html

    def downloadZIP(self, **kwargs):
        parameters = {'__NINEML_ACTION__'    : 'downloadZIP',
                      '__NINEML_WEBAPP_ID__' : self.applicationID
                     }
        self._sendRequest(parameters, self.headers)
        zip, response = self._getResponse()
        filename      = self._getAttachmentFilename(response)
        return filename, zip

    def _getApplicationID(self):
        parameters = {'__NINEML_ACTION__' : 'getApplicationID'}
        self._sendRequest(parameters, self.headers)
        self.applicationID, response = self._getResponse()
        return self.applicationID

    def _sendRequest(self, dict_parameters, headers):
        parameters = urllib.urlencode(dict_parameters)
        self.http_connection.request('POST', '/nineml-webapp', parameters, headers)

    def _getAttachmentFilename(self, response):
        content_disposition = response.getheader('Content-Disposition', '')
        #print("content_disposition: " + content_disposition)
        
        filename = None
        if 'attachment' in content_disposition:
            regex = re.compile('attachment; filename=(\S+)')
            match = regex.match(content_disposition)
            if match:
                groups = match.groups()
                if len(groups) > 0:
                    filename = groups[0]
        return filename
        
    def _getResponse(self):
        data = None
        response = self.http_connection.getresponse()
        if(response.status != 200):
            raise RuntimeError('The http request failed: {0} {1}'.format(response.status, response.reason))
        
        content_type = response.getheader('Content-type', '')
        #print("content_type: " + content_type)
        
        if content_type == 'application/json':
            json_data = json.loads(response.read())
            if (not 'success' in json_data) or (not 'error' in json_data) or (not 'content' in json_data):
                raise RuntimeError('Invalid json response received')
            if json_data['success'] == False:
                raise RuntimeError('The error occured in NineML web application:\n' + json_data['error'])
            data = json_data['content']
        
        elif content_type == 'application/pdf':
            data = response.read()
        
        elif content_type == 'application/zip':
            data = response.read()
        
        elif content_type == 'text/html':
            data = response.read()
        
        else:
            raise RuntimeError('Unrecognized Content-type received: ' + content_type)
        
        return data, response
   
def saveFileAndOpenInDefaultApp(filename, contents):
    if not contents:
        return
    
    f = open(filename, "w")
    f.write(contents)
    f.close()
    if os.name == 'nt':
        os.filestart(filename)
    elif os.name == 'posix':
        os.system('/usr/bin/xdg-open ' + filename)  

def testComponentFromTheCatalog():
    initialValues = """
    {
        "timeHorizon": 1.0, 
        "reportingInterval": 0.001, 
        "initial_conditions": {
            "iaf_1coba.iaf.tspike": -10000000000, 
            "iaf_1coba.iaf.V": -0.06, 
            "iaf_1coba.cobaExcit.g": 0.0
        }, 
        "parameters": {
            "iaf_1coba.iaf.gl": 50.0, 
            "iaf_1coba.cobaExcit.vrev": 0.0, 
            "iaf_1coba.cobaExcit.q": 3.0, 
            "iaf_1coba.iaf.vreset": -0.06, 
            "iaf_1coba.cobaExcit.tau": 5.0, 
            "iaf_1coba.iaf.taurefrac": 0.008, 
            "iaf_1coba.iaf.vthresh": -0.04, 
            "iaf_1coba.iaf.vrest": -0.06, 
            "iaf_1coba.iaf.cm": 1.0
        }, 
        "variables_to_report": {
            "iaf_1coba.cobaExcit.I": true, 
            "iaf_1coba.iaf.V": true
        }, 
        "event_ports_expressions": {
            "iaf_1coba.cobaExcit.spikeinput": "0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90"
        }, 
        "active_regimes": {
            "iaf_1coba.cobaExcit": "cobadefaultregime", 
            "iaf_1coba.iaf": "subthresholdregime"
        }, 
        "analog_ports_expressions": {}
    }
    """
    testName          = 'Test testable component' 
    testDescription   = 'Test Description' 
    testableComponent = 'hierachical_iaf_1coba'
    
    # 1. Create nineml_web_service object
    #    With no arguments it will connect to the INCF web server
    #    It can also connect to the other servers running the app (localhost for instance)
    #ws = nineml_web_service('localhost')
    ws = nineml_web_service()
    
    # 2. Set the abstraction layer component.
    #    a) It can be a TestableComponent from the catalog with setALComponent('component-name')
    #    b) It can be uploaded with uploadALComponent('xml-file')
    ws.setALComponent(testableComponent)
    
    # 3. Empty test data can be obtained by calling the getInitialValuesAsJSON() function
    #    The return value is a dictionary with all information set to defaults (zeroes and other defaults),
    #    which can be filled-in with some meaningful values.
    json = ws.getInitialValuesAsJSON()
    print(json)
    
    # 4. Add one or more tests (optional). 
    #   Tests expect a dictionary with the initial values, as returned from the getInitialValuesAsJSON() function
    ws.addTest(testName, testDescription, initialValues)
    
    # 5. Generate report on the server
    ws.generateReport()

    # 6. Fetch the report in PDF format
    filename, pdf = ws.downloadPDF()
    saveFileAndOpenInDefaultApp(filename, pdf)
    
    # 7. Fetch the report in HTML format
    filename, html = ws.downloadHTML()
    saveFileAndOpenInDefaultApp(filename, html)

    # 8. Fetch the zip file with the tests data (optional, if any test specified)
    filename, zip = ws.downloadZIP()
    saveFileAndOpenInDefaultApp(filename, zip)

def testUploadedComponent(pathToXMLFile):
    initialValues = """
{
    "timeHorizon": 1.0, 
    "reportingInterval": 0.001, 
    "initial_conditions": {
        "iaf_1coba.iaf_tspike": -10000000000, 
        "iaf_1coba.iaf_V": -0.06, 
        "iaf_1coba.cobaExcit_g": 0.0
    }, 
    "parameters": {
        "iaf_1coba.iaf_gl": 50.0, 
        "iaf_1coba.cobaExcit_vrev": 0.0, 
        "iaf_1coba.cobaExcit_q": 3.0, 
        "iaf_1coba.iaf_vreset": -0.06, 
        "iaf_1coba.cobaExcit_tau": 5.0, 
        "iaf_1coba.iaf_taurefrac": 0.008, 
        "iaf_1coba.iaf_vthresh": -0.04, 
        "iaf_1coba.iaf_vrest": -0.06, 
        "iaf_1coba.iaf_cm": 1.0
    }, 
    "variables_to_report": {
        "iaf_1coba.cobaExcit_I": true, 
        "iaf_1coba.iaf_V": true
    }, 
    "event_ports_expressions": {
        "iaf_1coba.cobaExcit_spikeinput": "0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90"
    }, 
    "active_regimes": {
        "iaf_1coba": "Regime1"
    }, 
    "analog_ports_expressions": {
        "iaf_1coba.iaf_ISyn" : "0.0"
    }
}
"""

    testName        = 'Test uploaded component' 
    testDescription = 'Test Description' 
    #ws = nineml_web_service('localhost')
    ws = nineml_web_service()
    ws.uploadALComponent(pathToXMLFile)
    ws.addTest(testName, testDescription, initialValues)
    ws.generateReport()

    filename, pdf = ws.downloadPDF()
    saveFileAndOpenInDefaultApp(filename, pdf)
    
    filename, zip = ws.downloadZIP()
    saveFileAndOpenInDefaultApp(filename, zip)

if __name__ == "__main__":
    # 1. Use a component from the catalog
    testComponentFromTheCatalog()
    
    # 2. Upload a component
    #testUploadedComponent('path to the xml file')
    