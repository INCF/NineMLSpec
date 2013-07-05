from __future__ import print_function
from pprint import pformat
import os, sys, cgi, math, json, traceback, os.path, tempfile, shutil
import cPickle as pickle
from copy import copy, deepcopy
from time import localtime, strftime, time
import uuid, urlparse, zipfile, cgitb
cgitb.enable()
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
import transaction
from persistent import Persistent
# http://www.blazingthings.com/dev/zcatalog.html
from zcatalog import catalog, indexes

baseFolder = '/home/ciroki/Data/NineML/nineml-model-tree/lib9ml/python/dae_impl'
sys.path.append(baseFolder)
from nineml_webapp_common import createErrorPage, getRepositoryInitialPage, addNewComponentPage
from nineml_webapp_common import searchForComponentPage, advancedSearchForComponentPage
from nineml_webapp_common import showComponents, showResultsPage

__scriptName__ = 'nineml-model-repository'
__actionName__ = '__NINEML_ACTION__'

class storageComponent(Persistent):
    def __init__(self):
        self.name     = ''
        self.version  = ''
        self.author   = ''
        self.keywords = ''
        self.category = ''
        self.notes    = ''
        self.nineml   = None
        self.report   = None
        self.testdata = None
        
    def __str__(self):
        return self.name
    
    def __repr__(self):
        result = ''
        result += 'name:     {0}\n'.format(self.name)
        result += 'version:  {0}\n'.format(self.version)
        result += 'author:   {0}\n'.format(self.author)
        result += 'keywords: {0}\n'.format(self.keywords)
        result += 'category: {0}\n'.format(self.category)
        result += 'notes:    {0}\n'.format(self.notes)
        #result += 'nineml:   {0}\n'.format(self.nineml)
        #result += 'report:   {0}\n'.format(self.report)
        #result += 'testdata: {0}\n'.format(self.testdata)
        return result

class nineml_model_repository:
    def __init__(self):
        pass

    def initial_page(self, environ, start_response):
        html = getRepositoryInitialPage()
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
        
    def browse(self, fieldStorage, environ, start_response):
        components = self.readZODB('components')
        html = showComponents(components.values())
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def search(self, fieldStorage, environ, start_response):
        html = searchForComponentPage()
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def advanced_search(self, fieldStorage, environ, start_response):
        html = advancedSearchForComponentPage()
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def search_results(self, fieldStorage, environ, start_response):
        html = ''
        kwargs = {}
        results = []
        components_found = []
        
        if 'name' in fieldStorage:
            kwargs['name'] = str(fieldStorage['name'].value)
        
        cat = self.createIndexes()
        try:
            results = map(str, list(cat.searchResults(**kwargs)))
        except Exception as e:
            return self.returnExceptionPage(str(e), environ, start_response)
        
        components = self.readZODB('components')
        if results:
            if components:
                for name in results:
                    components_found.append(components[name])
        else:
            html = 'Found nothing'
        html = showComponents(components_found)
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def advanced_search_results(self, fieldStorage, environ, start_response):
        html = ''
        results = []
        components_found = []
        
        kwargs = {}
        if 'name' in fieldStorage:
            kwargs['name'] = str(fieldStorage['name'].value)
        if 'notes' in fieldStorage:
            kwargs['notes'] = str(fieldStorage['notes'].value)
        if 'category' in fieldStorage:
            kwargs['category'] = str(fieldStorage['category'].value)
        if 'author' in fieldStorage:
            kwargs['author'] = str(fieldStorage['author'].value)
        if 'keywords' in fieldStorage:
            kwargs['keywords'] = str(fieldStorage['keywords'].value)
        if 'version' in fieldStorage:
            kwargs['version'] = str(fieldStorage['version'].value)
        
        cat = self.createIndexes()
        try:
            results = map(str, list(cat.searchResults(**kwargs)))
        except Exception as e:
            return self.returnExceptionPage(str(e), environ, start_response)
            
        components = self.readZODB('components')
        if len(results) > 0:
            if components:
                for name in results:
                    components_found.append(components[name])
                html = showComponents(components_found)
        else:
            html = 'Found nothing'
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def createIndexes(self):
        cat       = catalog.Catalog()
        iname     = indexes.TextIndex(field_name="name")
        inotes    = indexes.TextIndex(field_name="notes")
        iauthor   = indexes.TextIndex(field_name="author")
        ikeywords = indexes.TextIndex(field_name="keywords")
        icategory = indexes.TextIndex(field_name="category")
        
        cat["name"]     = iname
        cat["notes"]    = inotes
        cat["author"]   = iauthor
        cat["keywords"] = ikeywords
        cat["category"] = icategory
        
        components = self.readZODB('components')
        if components:
            for key, value in components.iteritems():
                cat.index_doc(value)
        #print(str(cat), file=sys.stderr)
        return cat

    def add_new(self, fieldStorage, environ, start_response):
        html = addNewComponentPage()
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def add_new_execute(self, fieldStorage, environ, start_response):
        html = ''
        comp = storageComponent()
        comp.name     = fieldStorage['name'].value
        comp.version  = fieldStorage['version'].value
        comp.author   = fieldStorage['author'].value
        comp.keywords = fieldStorage['keywords'].value
        comp.category = fieldStorage['category'].value
        comp.notes    = fieldStorage['notes'].value
        if fieldStorage['nineml'].file:
            comp.nineml   = fieldStorage['nineml'].file.read()
        if fieldStorage['report'].file:
            comp.report   = fieldStorage['report'].file.read()
        if fieldStorage['testdata'].file:
            comp.testdata = fieldStorage['testdata'].file.read()

       if self.addComponentZODB(comp.name, comp):
            html = showResultsPage('info', 
                                   'Component {0} successfully added to the model repository'.format(comp.name), 
                                   __scriptName__, __actionName__, 'Home')
        else:
            html = showResultsPage('error', 'Component {0} already exist or an error occurred'.format(comp.name), 
                                   __scriptName__, __actionName__, 'Home')
        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]

    def readZODB(self, key):
        try:
            _storage_    = FileStorage(baseFolder + '/zodb/nineml-model-repository.zodb')
            _db_         = DB(_storage_)
            _connection_ = _db_.open()
            _root_       = _connection_.root()
        
            if not key in _root_:
                raise RuntimeError('Cannot read key: {0} from database'.format(key))
            return deepcopy(_root_[key])
        
        finally:
            _connection_.close()
            _db_.close()
            _storage_.close()
        
    def addComponentZODB(self, name, component):
        try:
            _storage_    = FileStorage(baseFolder + '/zodb/nineml-model-repository.zodb')
            _db_         = DB(_storage_)
            _connection_ = _db_.open()
            _root_       = _connection_.root()
            if not 'components' in _root_:
                _root_['components'] = {}
            _components_ = _root_['components']

            if name in _components_:
                result = False
            else:
                _components_[name] = component
                _root_['components'] = _components_
                transaction.commit()
                result = True
            print(str(_root_['components']), file=sys.stderr)
        
        except Exception as e:
            transaction.abort()
            print(str(e), file=sys.stderr)
            
        finally:
            _connection_.close()
            _db_.close()
            _storage_.close()
        
        return result
    
    def downloadFile(self, filename, data, environ, start_response):
        html = str(data)        
        output_len = len(html)
        start_response('200 OK', [('Content-type', 'application/pdf'),
                                  #('Content-Transfer-Encoding', 'base64'),
                                  ('Content-Disposition', 'attachment; filename={0}'.format(name)),
                                  ('Content-Length', str(output_len))])
        return [html]
    
    def returnExceptionPage(self, strError, environ, start_response):
        content = ''
        #content = 'Application environment:\n' + pformat(environ) + '\n\n'
        #content += 'Form arguments:\n  {0}\n\n'.format(raw_arguments)

        exc_traceback = sys.exc_info()[2]
        html = createErrorPage(strError, exc_traceback, content)

        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]
           
    def __call__(self, environ, start_response):
        html = ''
        if environ['REQUEST_METHOD'] == 'GET':
            return self.initial_page(environ, start_response)

        else:
            fieldStorage = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ) 
            if not __actionName__ in fieldStorage:
                raise RuntimeError('Phase argument must be specified')

            action = fieldStorage[__actionName__].value
            if action == 'AddNew':
                return self.add_new(fieldStorage, environ, start_response)

            elif action == 'AddNewExecute':
                return self.add_new_execute(fieldStorage, environ, start_response)
            
            elif action == 'Browse':
                return self.browse(fieldStorage, environ, start_response)

            elif action == 'Edit':
                return self.edit(fieldStorage, environ, start_response)
            
            elif action == 'Delete':
                return self.delete(fieldStorage, environ, start_response)
            
            elif action == 'Search':
                return self.search(fieldStorage, environ, start_response)
            
            elif action == 'AdvancedSearch':
                return self.advanced_search(fieldStorage, environ, start_response)
            
            elif action == 'SearchResults':
                return self.search_results(fieldStorage, environ, start_response)
            
            elif action == 'AdvancedSearchResults':
                return self.advanced_search_results(fieldStorage, environ, start_response)
            
            elif action == 'Home':
                return self.initial_page(environ, start_response)
            
            else:
                raise RuntimeError('Invalid action argument specified: {0}'.format(action))


        output_len = len(html)
        start_response('200 OK', [('Content-type', 'text/html'),
                                  ('Content-Length', str(output_len))])
        return [html]

application = nineml_model_repository()