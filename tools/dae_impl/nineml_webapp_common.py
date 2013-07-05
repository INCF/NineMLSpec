from __future__ import print_function
import traceback

_css = """
    <style type="text/css">
        body 
        {
            padding:0;
            margin:20px;
            color:#333;
            background: white;
            font:14px sans-serif Tahoma;
            margin-left: auto; 
            margin-right: auto; 
            width: 700px;
        }
        form 
        {
            margin:0;
            padding:0;
        }
        fieldset 
        { 
            margin:1em 0;
            border:none;
            border-top:1px solid #ccc;
        }
        textarea
        {
             border: 1px solid LightGray;
        }
        input
        {
             border: 1px solid LightGray;
        }
        input:hover 
        {
            border: 1px solid Gray;
            background: white;
        }
        textarea:hover 
        {
            border: 1px solid Gray;
            background: white;
        }
        select
        {
            color: #202020; 
            background-color: White;
            width: 200px;
        }
        /*
        input:focus,textarea:focus 
        {
            background:#efefef;
            color:#000;
        }
        */
        
        form fieldset 
        {
            margin-bottom: 10px;
        }
        form legend 
        {
            padding: 0 2px;
            font-weight: bold;
        }
        form label 
        {
            display: inline-block;
            line-height: 1.8;
            vertical-align: top;
        }
        form fieldset ol 
        {
            margin: 0;
            padding: 0;
        }
        form fieldset li 
        {
            list-style: disc;
            padding: 0px;
            margin: 0;
        }
        form fieldset fieldset 
        {
            border: none;
            margin: 3px 0 0;
        }
        form fieldset fieldset legend 
        {
            padding: 0 0 5px;
            font-weight: normal;
        }
        form fieldset fieldset label 
        {
            display: block;
            width: auto;
        }
        form em 
        {
            font-weight: bold;
            font-style: normal;
            color: #f00;
        }
        form label 
        {
            width: 150px; /* Width of labels */
        }
        form fieldset fieldset label 
        {
            margin-left: 153px; /* Width plus 3 (html space) */
        }
        
        .info, .success, .warning, .error, .validation {
            border: 1px solid;
            margin: 10px 0px;
            padding:15px 15px 15px 15px;
            background-repeat: no-repeat;
            background-position: 10px center;
        }
        .info {
            color: black;
            background-color: white;
        }
        .success {
            color: black; //white;
            background-color: white; //DarkGreen;
        }
        .warning {
            color: black; //white;
            background-color: white; //Gold;
        }
        .error {
            color: black; //white;
            background-color: white; //DarkRed;
        }    
    </style>
"""

def getInitialPage(available_components):
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            <form action="nineml-webapp" method="post">
                <p>
                    <label for="TestableComponent" style="width:200px">NineML component:</label>
                    <select name="TestableComponent">
                        AVAILABLE_COMPONENTS
                    </select>
                </p>
                <p>
                    Initial values (in JSON format):<br/>
                    <textarea name="InitialValues" rows="10" cols="80" style="width:100%"></textarea>
                </p>
                <input type="submit" name="__NINEML_ACTION__" value="generateReport" />
                <input type="submit" name="__NINEML_ACTION__" value="Add test" />
            </form>
            <hr />
            <h3>Notes:</h3>
            <p>
            The web application takes a NineML component as an input and produces the component report in Latex/PDF format. 
            Optionally it can show the GUI that allows user to enter the data necessary for simulation: values of the parameters,
            initial conditions etc. Some predefined initial input values can be given in JSON format (to speed-up oftenly repeated tests).
            If no initial values are provided the GUI will be populated with zeros and defaults. <br/>
            The button <b>Generate report</b> produces the report with no test data added.<br/>
            The button <b>Add test</b> generates GUI with the data that should be entered, runs the simulation, produces results/plots
            and generates the report with the test data.<br/>
            </p>
            <p>
            The analog ports input fields accept simple numbers or expressions made with the basic mathematical functions, pi, e and numbers. <br/>
            The event ports input fields accept a comma-delimited values that represent time in seconds when the event will be triggered.
            </p>
            
            <p>Some dummy input data that should work</p>
            <p><b>Component: hierachical_iaf_1coba</b> <br/>
                <pre>
{
  "timeHorizon": 1.0, 
  "reportingInterval": 0.001, 
  "initial_conditions": {
    "iaf_1coba.iaf.tspike": -1e+99, 
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
                </pre>
            </p>
            
            <p><b>Component: iaf</b><br/>
                <pre>
{
  "timeHorizon": 1.0, 
  "reportingInterval": 0.001, 
  "initial_conditions": {
    "iaf.tspike": -1e+99, 
    "iaf.V": -0.06
  }, 
  "parameters": {
    "iaf.gl": 50.0, 
    "iaf.vreset": -0.06, 
    "iaf.taurefrac": 0.008, 
    "iaf.vthresh": -0.04, 
    "iaf.vrest": -0.06, 
    "iaf.cm": 1.0
  }, 
  "variables_to_report": {
    "iaf.V": true
  }, 
  "event_ports_expressions": {}, 
  "active_regimes": {
    "iaf": "subthresholdregime"
  }, 
  "analog_ports_expressions": {
    "iaf.ISyn" : "1.2"
  }
}
                </pre>
            </p>
            
            <p><b>Component: coba_synapse</b> <br/>
                <pre>
{
  "timeHorizon": 1.0, 
  "reportingInterval": 0.001, 
  "initial_conditions": {
    "CobaSyn.g": 0.0
  }, 
  "parameters": {
    "CobaSyn.vrev": 0.0, 
    "CobaSyn.q": 3.0, 
    "CobaSyn.tau": 5.0
  }, 
  "variables_to_report": {
    "CobaSyn.I": true 
  }, 
  "event_ports_expressions": {
    "CobaSyn.spikeinput": "0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90"
  }, 
  "active_regimes": {
    "CobaSyn": "cobadefaultregime"
  }, 
  "analog_ports_expressions": {
    "CobaSyn.V" : "-0.050"
  }
}
                </pre>
            </p>

        </body>
        </html>
    """
    _av_comps = ''
    for component in available_components:
        _av_comps += '<option value="{0}">{0}</option>\n'.format(component)
    html = html.replace('CSS_STYLES',           _css)
    html = html.replace('AVAILABLE_COMPONENTS', _av_comps)
    return html

def getRepositoryInitialPage():
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            <hr/>
            <form action="nineml-model-repository" method="post">
                <input type="submit" name="__NINEML_ACTION__" value="Browse" />
                <input type="submit" name="__NINEML_ACTION__" value="Search" />
                <input type="submit" name="__NINEML_ACTION__" value="AdvancedSearch" />
                <input type="submit" name="__NINEML_ACTION__" value="AddNew" />
            </form>
        </body>
        </html>
    """
    html = html.replace('CSS_STYLES', _css)
    return html

def addNewComponentPage():
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            <form action="nineml-model-repository" enctype="multipart/form-data" method="post">
                <fieldset>
                    <legend>General</legend>
                    <label for="name">Name</label>          <input type="text" name="name" value=""/> <br/>
                    <label for="version">Version</label>    <input type="text" name="version" value=""/> <br/>
                    <label for="author">Author</label>      <input type="text" name="author" value=""/> <br/>
                    <label for="keywords">Keywords</label>  <input type="text" name="keywords" value=""/> <br/>
                    <label for="category">Category</label>  <input type="text" name="category" value=""/> <br/>
                    <label for="notes">Notes</label>        <textarea name="notes" rows="10" cols="80" style="width:100%"></textarea> <br/>
                </fieldset>
                <fieldset>
                    <legend>Files</legend>
                    <label for="nineml">NineML XML file</label> <input type="file" name="nineml"   ACCEPT="text/xml"> <br/>
                    <label for="report">Model report</label>    <input type="file" name="report"   ACCEPT="application/pdf"> <br/>
                    <label for="testdata">Test data</label>     <input type="file" name="testdata" ACCEPT="application/zip"> <br/>
                </fieldset>
                <hr/>
                <input type="hidden" name="__NINEML_ACTION__" value="AddNewExecute"/>
                <input type="submit" value="Add" />
            </form>
        </body>
        </html>
    """
    html = html.replace('CSS_STYLES', _css)
    return html
    
def searchForComponentPage():
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            <form action="nineml-model-repository" method="post">
                <fieldset>
                    <legend>Search in names</legend>
                    <label for="name">Name</label> <input type="text" name="name" value=""/> <br/>
                </fieldset>
                <hr/>
                <input type="hidden" name="__NINEML_ACTION__" value="SearchResults"/>
                <input type="submit" value="Search" />
            </form>
        </body>
        </html>
    """
    html = html.replace('CSS_STYLES', _css)
    return html

def advancedSearchForComponentPage():
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            <form action="nineml-model-repository" method="post">
                <fieldset>
                    <legend>Advanced search</legend>
                    <label for="name">Name</label>          <input type="text" name="name" value=""/> <br/>
                    <label for="notes">Notes</label>        <input type="text" name="notes" value=""/> <br/>
                    <label for="version">Version</label>    <input type="text" name="version" value=""/> <br/>
                    <label for="author">Author</label>      <input type="text" name="author" value=""/> <br/>
                    <label for="keywords">Keywords</label>  <input type="text" name="keywords" value=""/> <br/>
                    <label for="category">Category</label> <input type="text" name="category" value=""/> <br/>
                </fieldset>
                <hr/>
                <input type="hidden" name="__NINEML_ACTION__" value="AdvancedSearchResults"/>
                <input type="submit" value="Search" />
            </form>
        </body>
        </html>
    """
    html = html.replace('CSS_STYLES', _css)
    return html
    
def formatComponent(component):
    html = '<pre>'
    html += 'name:     {0}\n'.format(component.name)
    html += 'version:  {0}\n'.format(component.version)
    html += 'author:   {0}\n'.format(component.author)
    html += 'keywords: {0}\n'.format(component.keywords)
    html += 'category: {0}\n'.format(component.category)
    html += 'notes:    {0}\n'.format(component.notes)
    #html += 'nineml:   {0}\n'.format(component.nineml)
    #html += 'report:   {0}\n'.format(component.report)
    #html += 'testdata: {0}\n'.format(component.testdata)
    html += '</pre>'
    return html

def showComponents(components):
    html = """
    <html>
        <head>
            CSS_STYLES
        </head>
        <body>
            CONTENT
        </body>
        </html>
    """
    content = ''
    for component in components:
        content += formatComponent(component)
    
    html = html.replace('CSS_STYLES', _css)
    html = html.replace('CONTENT', content)
    return html

def getSetupDataForm():
    html = """
    <form action="nineml-webapp" method="post">
        <h2>NineML AL Component: {0}</h2>
        {1}
        <input type="hidden" name="__NINEML_WEBAPP_ID__" value="{2}"/>
        <input type="hidden" name="__NINEML_ACTION__" value="Generate report with tests" />
    </form>
    """
    return html

def createResultPage(content):
    html =  """
    <html>
        <head>
            {0}
        </head>
        <body>
            <pre>
                {1}
            </pre>
        </body>
    </html>
    """
    return html.format(_css, content)

def createDownloadResults(content, applicationID, enablePDF, enableZIP):
    pdf = ''
    zip = ''
    if enablePDF:
        pdf = '<input type="submit" name="__NINEML_ACTION__" value="Download pdf report" />'
    if enableZIP:
        zip = '<input type="submit" name="__NINEML_ACTION__" value="Download zip archive" />'
    
    html =  """
        <pre>{0}</pre>
        <form action="nineml-webapp" method="post">
        <input type="hidden" name="__NINEML_WEBAPP_ID__" value="{1}"/>
        {2}
        {3}
        </form>
    """
    return html.format(content, applicationID, pdf, zip)

def createSetupDataPage(content):
    html =  """
    <html>
        <head>
            {0}
        </head>
        <body>
            {1}
        </body>
    </html>
    """
    return html.format(_css, content)

def createErrorPage(error, trace_back = None, additional_data = ''):
    html =  """
    <html>
        <head>
            {0}
        </head>
        <body>
            <pre>Error occurred:\n  {1}</pre>
            <pre>{2}</pre>
            <pre>{3}</pre>
        </body>
    </html>
    """
    errorDescription = ''
    if trace_back:
        messages = traceback.format_tb(trace_back)
        for msg in messages:
            errorDescription += msg
        
    return html.format(_css, error, errorDescription, additional_data)

def showResultsPage(msg_type, message, action, name, value):
    html =  """
    <html>
        <head>
            {0}
        </head>
        <body>
            <form action="{1}" method="post">
                <div class="{2}">{3}</div>
                <input type="hidden" name="{4}" value="{5}"/>
                <input type="submit" value="Close" />
            </form>
        </body>
    </html>
    """
    return html.format(_css, action, msg_type, message, name, value)
