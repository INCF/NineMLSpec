#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import nineml
from nineml.user_layer import Model, Definition, Parameter, ParameterSet, SpikingNodeType, SynapseType, CurrentSourceType
from nineml.abstraction_layer.testing_utils import TestableComponent
import sys, collections, json
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from nineml_tester_ui import Ui_ninemlTester
from expression_parser import ExpressionParser
from StringIO import StringIO
import dot2tex

def printDictionary(dictionary):
    for key, value in dictionary.iteritems():
        print('    {0} : {1}'.format(key, repr(value)))

def printList(l):
    for value in l:
        print('    {0}'.format(repr(value)))

def updateDictionary(dictOld, dictNew):
    for key, value in dictNew.items():
        if key in dictOld:
            if isinstance(dictOld[key], float):
                new_value = float(value)
            elif isinstance(dictOld[key], basestring):
                new_value = str(value)
            else:
                new_value = value
            if dictOld[key] != new_value:
                dictOld[key] = new_value

def updateTree(item, dictNew):
    """
    Updates tree item with a new value located in the dictionary 'dictNew'.
    
    :param item: treeItem object
    :param dictNew: dictionary 'canonical name' : value
        
    :rtype: 
    :raises:
    """
    key = item.canonicalName
    if key in dictNew:
        if item.itemType == treeItem.typeFloat:
            item.value = float(dictNew[key])

        elif item.itemType == treeItem.typeInteger:
            item.value = int(dictNew[key])

        elif item.itemType == treeItem.typeString:
            item.value = str(dictNew[key])

        elif item.itemType == treeItem.typeBoolean:
            item.value = bool(dictNew[key])

        elif item.itemType == treeItem.typeList:
            item.value = str(dictNew[key])

    for child in item.children:
        updateTree(child, dictNew)

class treeItem:
    """
    Tree-like class used to store hierarchical values from a single or a hierarchical AL Component.
    It is used to generate various types of GUI and get inputs for daetools simulations.
    """
    typeNoValue = -1
    typeFloat   =  0
    typeInteger =  1
    typeString  =  2
    typeBoolean =  3
    typeList    =  4

    def __init__(self, parent, name, value, data, itemType = typeNoValue):
        """
        Initializes a tree item.
        
        :param parent: a parent treeItem object
        :param name: string
        :param value: string | float | integer | boolean | string-list object
        :param data: object-specific data
        :param itemType: type of the item (typeNoValue, typeFloat, typeInteger, typeString, typeBoolean, typeList)
            
        :rtype: 
        :raises:
        """
        self.parent   = parent
        self.children = []
        self.name     = name
        self.value    = value
        self.data     = data
        self.itemType = itemType
        if parent:
            parent.children.append(self)

    @property
    def canonicalName(self):
        """
        Returns a canonical name of the item ('root.parent1.parent2.[...].item_name').
        
        :rtype: string
        :raises:
        """
        if self.parent:
            return self.parent.canonicalName + '.' + self.name
        else:
            return self.name

    @property
    def level(self):
        """
        A level of the item (used to calculate an indent, for instance). Root item's level is 0.
        
        :rtype: integer
        :raises:
        """
        if self.parent:
            return self.parent.level + 1
        else:
            return 0

    @property
    def hasChildren(self):
        """
        True if the item has got child items.
        
        :rtype: boolean
        :raises:
        """
        if len(self.children) == 0:
            return False
        else:
            return True
            
    def getDictionary(self):
        """
        Recursively fills a dictionary 'canonical name':value with values (including all child-items).
        
        :rtype: python dictionary
        :raises:
        """
        dictItems = {}
        if self.itemType != treeItem.typeNoValue:
            dictItems[self.canonicalName] = self.value

        for child in self.children:
            dictItems = dict(dictItems.items() + child.getDictionary().items())

        return dictItems

    def __str__(self):
        indent = self.level * '    '
        res = '{0}- {1}: {2}\n'.format(indent, self.name, self.value)
        for child in sorted(self.children):
            res += str(child)
        return res

def getConnectedAnalogPorts(root_model_name, component, connected_ports):
    """
    Recursively iterates over all port connections and returns a list of tuples:
    (canonical_name, AL Component object, list_of_connected_port_canonical_names).
    
    :param root_model_name: string
    :param component: AL Component object
    :param connected_ports: list of python tuples
        
    :rtype: list of python tuples (modified 'connected_ports' argument)
    :raises:
    """
    rootName = root_model_name
    if rootName != '':
        rootName += '.'

    for port_connection in component.portconnections:
        connected_ports.append(rootName + '.'.join(port_connection[0].loctuple))
        connected_ports.append(rootName + '.'.join(port_connection[1].loctuple))

    for name, subcomponent in component.subnodes.items():
        connected_ports = getConnectedAnalogPorts(rootName + name, subcomponent, connected_ports)

    return connected_ports

def getValueFromDictionary(canonicalName, dictValues, defaultValue, excludeRootName = False):
    """
    Recursively iterates over all port connections and returns a list of tuples:
    (canonical_name, AL Component object, list_of_connected_port_canonical_names).
    
    :param canonicalName: string
    :param dictValues: python dictionary 'canonical name':value
    :param defaultValue: string | float | integer | boolean | string-list object
    :param excludeRootName: booleans
        
    :rtype: string | float | integer | boolean | string-list object
    :raises:
    """
    #if excludeRootName:
    #    names = canonicalName.split('.')
    #    if len(names) == 1:
    #        key = names[0]
    #    else:
    #        key = '.'.join(names[1:])
    #else:
    #    key = canonicalName
        
    key = canonicalName
    
    #print('canonicalName = {0} -> key = {1}'.format(canonicalName, key))
    if key in dictValues:
        return dictValues[key]
    else:
        return defaultValue

def isValueInList(canonicalName, listValues, excludeRootName = False):
    """
    Detects if the item with 'canonicalName' is in the list.
    
    :param canonicalName: string
    :param listValues: python list
    :param excludeRootName: booleans
        
    :rtype: Boolean
    :raises:
    """
    #if excludeRootName:
    #    names = canonicalName.split('.')
    #    if len(names) == 1:
    #        key = names[0]
    #    else:
    #        key = '.'.join(names[1:])
    #else:
    #    key = canonicalName
    
    key = canonicalName
    #print('canonicalName = {0} -> key = {1}'.format(canonicalName, key))
    return (key in listValues)

def collectParameters(nodeItem, component, dictParameters, initialValues = {}):
    """
    Recursively looks for parameters in the 'component' and all its sub-nodes and
    adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictParameters: python dictionary 'canonical name' : value
    :param initialValues: python dictionary
        
    :rtype:
    :raises:
    """
    for obj in component.parameters:
        objName = nodeItem.canonicalName + '.' + obj.name
        value   = getValueFromDictionary(objName, initialValues, 0.0, True)
        dictParameters[objName] = value
        item = treeItem(nodeItem, obj.name, value, None, treeItem.typeFloat)

    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectParameters(subnodeItem, subcomponent, dictParameters, initialValues)

def collectStateVariables(nodeItem, component, dictStateVariables, initialValues = {}):
    """
    Recursively looks for state variables in the 'component' and all its sub-nodes and
    adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictStateVariables: python dictionary 'canonical name' : value
    :param initialValues: python dictionary
        
    :rtype:
    :raises:
    """
    for obj in component.state_variables:
        objName = nodeItem.canonicalName + '.' + obj.name
        value   = getValueFromDictionary(objName, initialValues, 0.0, True)
        dictStateVariables[objName] = value
        item = treeItem(nodeItem, obj.name, value, None, treeItem.typeFloat)

    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectStateVariables(subnodeItem, subcomponent, dictStateVariables, initialValues)

def collectRegimes(nodeItem, component, dictRegimes, activeRegimes = {}):
    """
    Recursively looks for regimes in the 'component' and all its sub-nodes and
    adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictRegimes: python dictionary 'canonical name' : string
    :param activeRegimes: python dictionary
        
    :rtype:
    :raises:
    """
    available_regimes = []
    active_regime     = None

    for obj in component.regimes:
        available_regimes.append(obj.name)
        objName = nodeItem.canonicalName + '.' + obj.name
        value   = getValueFromDictionary(nodeItem.canonicalName, activeRegimes, None, True)
        if value == obj.name:
            active_regime = obj.name

    if len(available_regimes) > 0:
        if active_regime == None:
            active_regime = available_regimes[0]

        dictRegimes[nodeItem.canonicalName] = active_regime

        nodeItem.itemType = treeItem.typeList
        nodeItem.value    = active_regime
        nodeItem.data     = available_regimes

    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectRegimes(subnodeItem, subcomponent, dictRegimes, activeRegimes)

def collectAnalogPorts(nodeItem, component, dictAnalogPortsExpressions, connected_ports, expressions = {}):
    """
    Recursively looks for analogue ports in the 'component' and all its sub-nodes and
    adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictAnalogPortsExpressions: python dictionary 'canonical name' : string
    :param expressions: python dictionary
        
    :rtype:
    :raises:
    """
    for obj in component.analog_ports:
        if (obj.mode == 'recv') or (obj.mode == 'reduce'):
            objName = nodeItem.canonicalName + '.' + obj.name
            if isValueInList(objName, connected_ports, False) == False:
                value   = str(getValueFromDictionary(objName, expressions, '', True))
                dictAnalogPortsExpressions[objName] = value
                item = treeItem(nodeItem, obj.name, value, None, treeItem.typeString)

    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectAnalogPorts(subnodeItem, subcomponent, dictAnalogPortsExpressions, connected_ports, expressions)

def collectEventPorts(nodeItem, component, dictEventPortsExpressions, expressions = {}):
    """
    Recursively looks for event ports in the 'component' and all its sub-nodes and
    adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictEventPortsExpressions: python dictionary 'canonical name' : string
    :param initialValues: python dictionary
        
    :rtype:
    :raises:
    """
    for obj in component.event_ports:
        if (obj.mode == 'recv') or (obj.mode == 'reduce'):
            objName = nodeItem.canonicalName + '.' + obj.name
            value   = str(getValueFromDictionary(objName, expressions, '', True))
            dictEventPortsExpressions[objName] = value
            item = treeItem(nodeItem, obj.name, value, None, treeItem.typeString)

    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectEventPorts(subnodeItem, subcomponent, dictEventPortsExpressions, expressions)

def collectVariablesToReport(nodeItem, component, dictVariablesToReport, variables_to_report = {}):
    """
    Recursively looks for variables marked for inclusion in the report in the 'component' 
    and all its sub-nodes and adds a new treeItem object to the parent item 'nodeItem'.
    
    :param nodeItem: parent treeItem object
    :param component: AL Component object
    :param dictStateVariables: python dictionary 'canonical name' : value
    :param initialValues: python dictionary
        
    :rtype:
    :raises:
    """
    for obj in component.aliases:
        objName = nodeItem.canonicalName + '.' + obj.lhs
        checked = getValueFromDictionary(objName, variables_to_report, False, True)
        dictVariablesToReport[objName] = checked
        item = treeItem(nodeItem, obj.lhs, checked, None, treeItem.typeBoolean)

    for obj in component.state_variables:
        objName = nodeItem.canonicalName + '.' + obj.name
        checked = getValueFromDictionary(objName, variables_to_report, False, True)
        dictVariablesToReport[objName] = checked
        item = treeItem(nodeItem, obj.name, checked, None, treeItem.typeBoolean)

    # ACHTUNG, ACHTUNG!!!
    # It crashes with this included
    """
    for obj in component.analog_ports:
        objName = nodeItem.canonicalName + '.' + obj.name
        if (obj.mode == 'recv') or (obj.mode == 'reduce'):
            checked = getValueFromDictionary(objName, variables_to_report, False, True)
            dictVariablesToReport[objName] = checked
            item = treeItem(nodeItem, obj.name, checked, None, treeItem.typeBoolean)
    """
    
    for name, subcomponent in component.subnodes.items():
        subnodeItem = treeItem(nodeItem, name, None, None, treeItem.typeNoValue)
        collectVariablesToReport(subnodeItem, subcomponent, dictVariablesToReport, variables_to_report)

def addItem(treeWidget, parent, item):
    """
    Adds new QTreeWidgetItem to the 'parent' tree item.
    
    :param treeWidget: QTreeWidget object
    :param parent: QTreeWidgetItem object
    :param item: treeItem object
        
    :rtype: QTreeWidgetItem object
    :raises:
    """
    widgetItem = QtGui.QTreeWidgetItem(parent, [item.name, ''])

    # Item's data is always the tree item object
    widgetItem.setData(1, QtCore.Qt.UserRole, QtCore.QVariant(item))

    # The common flags
    widgetItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    # Depending on the type set the text(0) or something else
    if item.itemType == treeItem.typeFloat or item.itemType == treeItem.typeInteger or item.itemType == treeItem.typeString:
        widgetItem.setFlags(widgetItem.flags() | Qt.ItemIsEditable)
        widgetItem.setText(1, str(item.value))

    elif item.itemType == treeItem.typeBoolean:
        widgetItem.setFlags(widgetItem.flags() | Qt.ItemIsUserCheckable)
        if item.value:
            widgetItem.setCheckState(0, Qt.Checked)
        else:
            widgetItem.setCheckState(0, Qt.Unchecked)

    elif item.itemType == treeItem.typeList:
        widgetItem.setFlags(widgetItem.flags() | Qt.ItemIsEditable)
        widgetItem.setText(1, str(item.value))

    return widgetItem
    
def addItemsToTree(treeWidget, parent, tree_item):
    """
    Recursively adds the whole tree of treeItems to QTreeWidget tree.
    
    :param treeWidget: QTreeWidget object
    :param parent: QTreeWidgetItem object
    :param tree_item: treeItem object
        
    :rtype: 
    :raises:
    """
    new_parent = addItem(treeWidget, parent, tree_item)
    for child in tree_item.children:
        addItemsToTree(treeWidget, new_parent, child)

class nineml_component_qtGUI(QtGui.QDialog):
    """
    Qt dialog form to get the inputs from the user.
    """
    def __init__(self, inspector):
        """
        Initializes the Qt GUI with the data from the nineml_component_inspector object.
        
        :param inspector: nineml_component_inspector object
            
        :rtype: 
        :raises:
        """
        QtGui.QDialog.__init__(self)
        self.ui = Ui_ninemlTester()
        self.ui.setupUi(self)

        validator = QtGui.QDoubleValidator(self)
        self.ui.timeHorizonSLineEdit.setValidator(validator)
        self.ui.reportingIntervalSLineEdit.setValidator(validator)

        self.inspector = inspector
        addItemsToTree(self.ui.treeParameters,          self.ui.treeParameters,        self.inspector.treeParameters)
        addItemsToTree(self.ui.treeInitialConditions,   self.ui.treeInitialConditions, self.inspector.treeInitialConditions)
        addItemsToTree(self.ui.treeAnalogPorts,         self.ui.treeAnalogPorts,       self.inspector.treeAnalogPorts)
        addItemsToTree(self.ui.treeEventPorts,          self.ui.treeEventPorts,        self.inspector.treeEventPorts)
        addItemsToTree(self.ui.treeRegimes,             self.ui.treeRegimes,           self.inspector.treeActiveStates)
        addItemsToTree(self.ui.treeResultsVariables,    self.ui.treeResultsVariables,  self.inspector.treeVariablesToReport)

        self.connect(self.ui.buttonOk,              QtCore.SIGNAL('clicked()'),                                self.slotOK)
        self.connect(self.ui.buttonCancel,          QtCore.SIGNAL('clicked()'),                                self.slotCancel)
        self.connect(self.ui.treeParameters,        QtCore.SIGNAL("itemChanged(QTreeWidgetItem*, int)"),       self.slotTreeItemChanged)
        self.connect(self.ui.treeInitialConditions, QtCore.SIGNAL("itemChanged(QTreeWidgetItem*, int)"),       self.slotTreeItemChanged)
        self.connect(self.ui.treeRegimes,           QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.slotRegimesItemDoubleClicked)
        self.connect(self.ui.treeAnalogPorts,       QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.slotAnalogPortsItemDoubleClicked)
        self.connect(self.ui.treeEventPorts,        QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.slotEventPortsItemDoubleClicked)
        self.connect(self.ui.treeResultsVariables,  QtCore.SIGNAL("itemChanged(QTreeWidgetItem*, int)"),       self.slotTreeItemChanged)

        self.ui.treeParameters.expandAll()
        self.ui.treeParameters.resizeColumnToContents(0)
        self.ui.treeParameters.resizeColumnToContents(1)
        self.ui.treeInitialConditions.expandAll()
        self.ui.treeInitialConditions.resizeColumnToContents(0)
        self.ui.treeInitialConditions.resizeColumnToContents(1)
        self.ui.treeAnalogPorts.expandAll()
        self.ui.treeAnalogPorts.resizeColumnToContents(0)
        self.ui.treeAnalogPorts.resizeColumnToContents(1)
        self.ui.treeEventPorts.expandAll()
        self.ui.treeEventPorts.resizeColumnToContents(0)
        self.ui.treeEventPorts.resizeColumnToContents(1)
        self.ui.treeRegimes.expandAll()
        self.ui.treeRegimes.resizeColumnToContents(0)
        self.ui.treeRegimes.resizeColumnToContents(1)
        self.ui.treeResultsVariables.expandAll()
        self.ui.treeResultsVariables.resizeColumnToContents(0)
        #self.ui.treeResultsVariables.resizeColumnToContents(1)

    def slotOK(self):
        self.done(QtGui.QDialog.Accepted)

    def slotCancel(self):
        self.done(QtGui.QDialog.Rejected)

    def slotTreeItemChanged(self, item, column):
        """
        Validates and updates QTreeWidgetItem 'item' with the data entered by the user.
        
        :param item: QTreeWidgetItem object
        :param column: integer
            
        :rtype: 
        :raises:
        """
        if column == 1:
            data = item.data(1, QtCore.Qt.UserRole)
            if not data:
                return
            tree_item = data.toPyObject()

            if tree_item.itemType == treeItem.typeFloat:
                varValue  = QtCore.QVariant(item.text(1))
                newValue, isOK = varValue.toDouble()
                if not isOK:
                    msg = 'Invalid floating point value ({0}) entered for the item: {1}'.format(item.text(1), item.text(0))
                    QtGui.QMessageBox.warning(None, "NineML", msg)
                    item.setText(1, str(tree_item.value))
                    return
                tree_item.value = newValue

            elif tree_item.itemType == treeItem.typeInteger:
                varValue  = QtCore.QVariant(item.text(1))
                newValue, isOK = varValue.toInteger()
                if not isOK:
                    msg = 'Invalid integer value ({0}) entered for the item: {1}'.format(item.text(1), item.text(0))
                    QtGui.QMessageBox.warning(None, "NineML", msg)
                    item.setText(1, str(tree_item.value))
                    return
                tree_item.value = newValue

            elif tree_item.itemType == treeItem.typeString:
                tree_item.value  = str(item.text(1))

            elif tree_item.itemType == treeItem.typeList:
                tree_item.value  = str(item.text(1))

        # Only for boolean data (with a check-box)
        elif column == 0:
            data = item.data(1, QtCore.Qt.UserRole)
            if not data:
                return
            tree_item = data.toPyObject()
            if tree_item.itemType == treeItem.typeBoolean:
                if item.checkState(0) == Qt.Checked:
                    tree_item.value = True
                else:
                    tree_item.value = False

    def slotEventPortsItemDoubleClicked(self, item, column):
        """
        Shows the input dialog when QTreeWidgetItem 'item' is double-clicked, 
        validates the input, and updates the treeItem with the data entered by the user.
        
        :param item: QTreeWidgetItem object
        :param column: integer
            
        :rtype: 
        :raises:
        """
        if column == 1:
            data      = item.data(1, QtCore.Qt.UserRole)
            tree_item = data.toPyObject()
            if tree_item.value == None:
                return
            old_expression = item.text(1)
            new_expression, ok = QtGui.QInputDialog.getText(self, "Event Port Input", "Set the input event expression:", QtGui.QLineEdit.Normal, old_expression)
            if ok:
                item.setText(1, new_expression)
                tree_item.value = str(new_expression)

    def slotAnalogPortsItemDoubleClicked(self, item, column):
        """
        Shows the input dialog when QTreeWidgetItem 'item' is double-clicked, 
        validates the input, and updates the treeItem with the data entered by the user.
        
        :param item: QTreeWidgetItem object
        :param column: integer
            
        :rtype: 
        :raises:
        """
        if column == 1:
            data      = item.data(1, QtCore.Qt.UserRole)
            tree_item = data.toPyObject()
            if tree_item.value == None:
                return
            old_expression = item.text(1)
            new_expression, ok = QtGui.QInputDialog.getText(self, "Analog Port Input", "Set the analog port input expression:", QtGui.QLineEdit.Normal, old_expression)
            if ok:
                item.setText(1, new_expression)
                tree_item.value = str(new_expression)

    def slotRegimesItemDoubleClicked(self, item, column):
        """
        Shows the input dialog when QTreeWidgetItem 'item' is double-clicked, 
        validates the input, and updates the treeItem with the data entered by the user.
        
        :param item: QTreeWidgetItem object
        :param column: integer
            
        :rtype: 
        :raises:
        """
        if column == 1:
            data      = item.data(1, QtCore.Qt.UserRole)
            tree_item = data.toPyObject()
            if tree_item.value == None:
                return
            available_regimes = tree_item.data
            active_state, ok = QtGui.QInputDialog.getItem(self, "Available regimes", "Select the new active regime:", available_regimes, 0, False)
            if ok:
                item.setText(1, active_state)
                tree_item.value = str(active_state)

def latex_table(header_flags, header_items, rows_items, caption = ''):
    """
    Creates Latex table based on the given input arguments and returns it as a string.
    
    :param header_flags: python string list
    :param header_items: python string list
    :param rows_items: python list of string lists
    :param caption: string
        
    :rtype: string
    :raises:
    """
    table_template = """
\\begin{{table}}[placement=!h]
{3}
\\begin{{center}}
\\begin{{tabular}}{{ {0} }}
\\hline
{1}
\\hline
{2}
\\end{{tabular}}
\\end{{center}}
\\end{{table}}
    """
    #flags  = ' | ' + ' | '.join(header_flags) + ' | '
    flags  = ' '.join(header_flags)
    header = ' & '.join(header_items) + ' \\\\'
    rows = ''
    for item in rows_items:
        rows += ' & '.join(item) + ' \\\\ \n'
    if caption:
        title = '\\caption{{{0}}} \n'.format(caption)
    else:
        title = ''
    return table_template.format(flags, header, rows, title)

def latex_regime_table(header_flags, regime, odes, _on_conditions, _on_events, caption = ''):
    """
    Creates Latex representation of regimes based on the given input arguments and returns it as a string.
    
    :param header_flags: python string list
    :param regime: string
    :param odes: python string list
    :param _on_conditions: python string list
    :param _on_events: python string list
    :param caption: string
        
    :rtype: string
    :raises:
    """
    table_template = """
\\begin{{table}}[placement=!h]
{3}
\\begin{{center}}
\\begin{{tabular}}{{ {0} }}
\\hline
\\multicolumn{{2}}{{c}}{{ {1} }} \\\\
\\hline
{2}
\\end{{tabular}}
\\end{{center}}
\\end{{table}}
    """
    flags  = ' '.join(header_flags)
    rows = '\\multirow{{{0}}}{{*}}{{ODEs}} & '.format(len(odes))
    for item in odes:
        rows += item + ' \\\\ \n'

    rows += '\\multirow{{{0}}}{{*}}{{On condition}} & '.format(len(_on_conditions))
    for item in _on_conditions:
        rows += item + ' \\\\ \n'

    rows += '\\multirow{{{0}}}{{*}}{{On event}} & '.format(len(_on_events))
    for item in _on_events:
        rows += item + ' \\\\ \n'

    if caption:
        title = '\\caption{{{0}}} \n'.format(caption)
    else:
        title = ''
    return table_template.format(flags, regime, rows, title)

class nineml_component_inspector:
    """
    Analyses the AL Component object and provides various sorts of services:
    
    * Creates html or latex report
    * Generates pyQt desktop graphical user interface (GUI) form to enable users to enter the data necessary for a simulation
    * Generates html GUI form to enable users to enter the data necessary for a simulation

    GUI forms consist of seven parts:
    
    * Simulation-related runtime data: time horizon, reporting interval etc.
    * A tree-like structure that shows the parameters and input fields to enter their values.
    * A tree-like structure that shows state-variables and input fields to enter their values (initial conditions).
    * A tree-like structure that shows unconnected input/reduce analogue ports and input fields to enter their values. The values allowed are simple numbers or time-dependent functions that may contain numbers, basic mathematical functions, constants (such as p, e etc.) and time. Other identifiers may be added subject to the users needs (like variables, parameters, ports and aliases found in the component and some additional functions like step-change, impulse-change functions etc.).
    * A tree-like structure that shows inlet event ports and input fields to enter their values.  The values allowed at the moment are limited to a sequence of floating point numbers representing incoming event moments.
    * A tree-like structure that shows all regimes and allows specification of initially active states.
    * A tree-like structure that shows all variables, aliases and ports where users can select variables/aliases/ports to be included in the report. This produces a table: (time, value) and a plot: variable value = f(t)) for every selected item and these data are incorporated into a tex/pdf report.        
    """
    
    categoryParameters              = '___PARAMETERS___'
    categoryInitialConditions       = '___INITIAL_CONDITIONS___'
    categoryActiveStates            = '___ACTIVE_STATES___'
    categoryAnalogPortsExpressions  = '___INLET_ANALOG_PORTS_EXPRESSIONS___'
    categoryEventPortsExpressions   = '___EVENT_PORTS_EXPRESSIONS___'
    categoryVariablesToReport       = '___VARIABLES_TO_REPORT___'

    begin_itemize = '\\begin{itemize}\n'
    item          = '\\item '
    end_itemize   = '\\end{itemize}\n\n'

    def __init__(self):
        """
        Initializes the inspector object.
            
        :rtype:
        :raises:
        """
        self.ninemlComponent = None

        self.timeHorizon       = 0.0
        self.reportingInterval = 0.0
        
        # Dictionaries 'key' : floating-point-value
        self.parameters                 = {}
        self.initial_conditions         = {}
        # Dictionaries: 'key' : 'expression'
        self.analog_ports_expressions   = {}
        self.event_ports_expressions    = {}
        # Dictionary 'key' : 'current-active-state'
        self.active_regimes             = {}
        # Dictionaries 'key' : boolean-value
        self.variables_to_report        = {}

        self.treeParameters         = None
        self.treeInitialConditions  = None
        self.treeActiveStates       = None
        self.treeEventPorts         = None
        self.treeVariablesToReport  = None
        self.treeAnalogPorts        = None

    def inspect(self, component, **kwargs):
        """
        Inspects the AL Component object and creates 7 treeItem tree objects:
        
        * treeParameters
        * treeInitialConditions
        * treeActiveStates
        * treeEventPorts 
        * treeVariablesToReport
        * treeAnalogPorts
        
        :param component: AL Component object
        :param kwargs: python dictionaries with the initial values
            
        :rtype:
        :raises:
        """
        if isinstance(component, nineml.abstraction_layer.ComponentClass):
            self.ninemlComponent = component
        elif isinstance(component, basestring):
            self.ninemlComponent = nineml.abstraction_layer.parse(component)
        else:
            raise RuntimeError('the input NineML component must be either ComponentClass or a path to xml file')
        if not self.ninemlComponent:
            raise RuntimeError('Invalid input NineML component')

        _parameters               = kwargs.get('parameters',               {})
        _initial_conditions       = kwargs.get('initial_conditions',       {})
        _active_regimes           = kwargs.get('active_regimes',           {})
        _analog_ports_expressions = kwargs.get('analog_ports_expressions', {})
        _event_ports_expressions  = kwargs.get('event_ports_expressions',  {})
        _variables_to_report      = kwargs.get('variables_to_report',      {})

        if not isinstance(_parameters, dict):
            raise RuntimeError('parameters argument must be a dictionary')
        if not isinstance(_initial_conditions, dict):
            raise RuntimeError('initial_conditions argument must be a dictionary')
        if not isinstance(_active_regimes, dict):
            raise RuntimeError('active_regimes argument must be a dictionary')
        if not isinstance(_analog_ports_expressions, dict):
            raise RuntimeError('analog_ports_expressions argument must be a dictionary')
        if not isinstance(_event_ports_expressions, dict):
            raise RuntimeError('event_ports_expressions argument must be a dictionary')
        if not isinstance(_variables_to_report, dict):
            raise RuntimeError('variables_to_report argument must be a dictionary')

        if 'timeHorizon' in kwargs:
            self.timeHorizon = float(kwargs.get('timeHorizon'))
        if 'reportingInterval' in kwargs:
            self.reportingInterval = float(kwargs.get('reportingInterval'))

        self.treeParameters = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectParameters(self.treeParameters, self.ninemlComponent, self.parameters, _parameters)

        self.treeInitialConditions = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectStateVariables(self.treeInitialConditions, self.ninemlComponent, self.initial_conditions, _initial_conditions)

        self.treeActiveStates = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectRegimes(self.treeActiveStates, self.ninemlComponent, self.active_regimes, _active_regimes)

        self.treeEventPorts = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectEventPorts(self.treeEventPorts, self.ninemlComponent, self.event_ports_expressions, _event_ports_expressions)

        self.treeVariablesToReport = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectVariablesToReport(self.treeVariablesToReport, self.ninemlComponent, self.variables_to_report, _variables_to_report)

        connected_ports = []
        connected_ports = getConnectedAnalogPorts(self.ninemlComponent.name, self.ninemlComponent, connected_ports)
        self.treeAnalogPorts = treeItem(None, self.ninemlComponent.name, None, None, treeItem.typeNoValue)
        collectAnalogPorts(self.treeAnalogPorts, self.ninemlComponent, self.analog_ports_expressions, connected_ports, _analog_ports_expressions)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        res = []
        res.append('tree parameters:')
        res.append(str(self.treeParameters))
        res.append('tree initial_conditions:')
        res.append(str(self.treeInitialConditions))
        return '\n'.join(res)

    def jsonData(self):
        """
        Returns the trees data as a JSON string.
        
        :rtype: string
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
        return json.dumps(data, indent = 2)

    def printCollectedData(self):
        print('timeHorizon: ' + str(self.timeHorizon))
        print('reportingInterval: ' + str(self.reportingInterval))
        print('parameters:')
        printDictionary(self.parameters)
        print('initial_conditions:')
        printDictionary(self.initial_conditions)
        print('active_regimes:')
        printDictionary(self.active_regimes)
        print('analog_ports_expressions:')
        printDictionary(self.analog_ports_expressions)
        print('event_ports_expressions:')
        printDictionary(self.event_ports_expressions)
        print('variables_to_report:')
        printDictionary(self.variables_to_report)
    
    def printTrees(self):
        print('timeHorizon: ' + str(self.timeHorizon))
        print('reportingInterval: ' + str(self.reportingInterval))
        print('tree parameters:')
        print(str(self.treeParameters))
        print('tree initial_conditions:')
        print(str(self.treeInitialConditions))
        print('tree active_regimes:')
        print(str(self.treeActiveStates))
        print('tree event_ports_expressions:')
        print(str(self.treeEventPorts))
        print('tree analog_ports_expressions:')
        print(str(self.treeAnalogPorts))
        print('tree variables_to_report:')
        print(str(self.treeVariablesToReport))

    def printTreeDictionaries(self):
        print('tree parameters dictionary:')
        printDictionary(self.treeParameters.getDictionary())
        print('tree initial_conditions dictionary:')
        printDictionary(self.treeInitialConditions.getDictionary())
        print('tree active_regimes dictionary:')
        printDictionary(self.treeActiveStates.getDictionary())
        print('tree event_ports_expressions dictionary:')
        printDictionary(self.treeEventPorts.getDictionary())
        print('tree analog_ports_expressions dictionary:')
        printDictionary(self.treeAnalogPorts.getDictionary())
        print('tree variables_to_report dictionary:')
        printDictionary(self.treeVariablesToReport.getDictionary())

    def generateUserLayerComponent(self, component_type, filename):
        definition   = Definition(self.ninemlComponent.name)
        parameters   = []
        for name, value in self.parameters.items():
            print(name, value)
            parameters.append(Parameter(name, value, 'mV'))
        
        param_set = ParameterSet(*parameters)
        ul_component = None
        if component_type == 'SpikingNodeType':
            ul_component = SpikingNodeType(self.ninemlComponent.name, definition = definition, parameters = param_set)
        elif component_type == 'SynapseType':
            ul_component = SynapseType(self.ninemlComponent.name, definition = definition, parameters = param_set)
        elif component_type == 'CurrentSourceType':
            ul_component = CurrentSourceType(self.ninemlComponent.name, definition = definition, parameters = param_set)
        else:
            raise RuntimeError('Invalid component_type argument')
        
        model      = Model(self.ninemlComponent.name)
        model.add_component(ul_component)
        model.write(filename)
        
    def updateData(self, **kwargs):
        """
        Updates the trees data with the dictionaries in the 'kwargs' argument.
        
        :param kwargs: python dictionaries with the values
            
        :rtype:
        :raises: RuntimeError
        """
        _parameters               = kwargs.get('parameters',               {})
        _initial_conditions       = kwargs.get('initial_conditions',       {})
        _active_regimes           = kwargs.get('active_regimes',           {})
        _analog_ports_expressions = kwargs.get('analog_ports_expressions', {})
        _event_ports_expressions  = kwargs.get('event_ports_expressions',  {})
        _variables_to_report      = kwargs.get('variables_to_report',      {})

        if not isinstance(_parameters, dict):
            raise RuntimeError('parameters argument must be a dictionary')
        if not isinstance(_initial_conditions, dict):
            raise RuntimeError('initial_conditions argument must be a dictionary')
        if not isinstance(_active_regimes, dict):
            raise RuntimeError('active_regimes argument must be a dictionary')
        if not isinstance(_analog_ports_expressions, dict):
            raise RuntimeError('analog_ports_expressions argument must be a dictionary')
        if not isinstance(_event_ports_expressions, dict):
            raise RuntimeError('event_ports_expressions argument must be a dictionary')
        if not isinstance(_variables_to_report, dict):
            raise RuntimeError('variables_to_report argument must be a dictionary')

        if 'timeHorizon' in kwargs:
            self.timeHorizon = float(kwargs.get('timeHorizon'))
        if 'reportingInterval' in kwargs:
            self.reportingInterval = float(kwargs.get('reportingInterval'))
        updateDictionary(self.parameters,               _parameters)
        updateDictionary(self.initial_conditions,       _initial_conditions)
        updateDictionary(self.active_regimes,           _active_regimes)
        updateDictionary(self.analog_ports_expressions, _analog_ports_expressions)
        updateDictionary(self.event_ports_expressions,  _event_ports_expressions)
        updateDictionary(self.variables_to_report,      _variables_to_report)

    def updateTrees(self):
        """
        Self-update of the trees data.
            
        :rtype:
        :raises:
        """
        updateTree(self.treeParameters,         self.parameters)
        updateTree(self.treeInitialConditions,  self.initial_conditions)
        updateTree(self.treeActiveStates,       self.active_regimes)
        updateTree(self.treeAnalogPorts,        self.analog_ports_expressions)
        updateTree(self.treeEventPorts,         self.event_ports_expressions)
        updateTree(self.treeVariablesToReport,  self.variables_to_report)

    def getComponentXMLSourceCode(self, flatten = True):
        """
        Mickey mice function to get the xml source of the AL component.
        
        :param flatten: boolean
            
        :rtype: string
        :raises: IOError
        """
        f = StringIO()
        nineml.al.writers.XMLWriter.write(self.ninemlComponent, f, flatten)
        xmlSource = f.getvalue()
        return xmlSource

    def getComponentALObject(self):
        return self.ninemlComponent

    def writeComponentToXMLFile(self, filename, flatten = True):
        """
        Mickey mice function to write the AL component to a file.
        
        :param filename: string
        :param flatten: boolean
            
        :rtype:
        :raises: IOError
        """
        if not self.ninemlComponent or not isinstance(self.ninemlComponent, nineml.abstraction_layer.ComponentClass):
            raise RuntimeError('Invalid input NineML component')
        nineml.al.writers.XMLWriter.write(self.ninemlComponent, filename, flatten)

    def generateHTMLForm(self):
        """
        Generates HTML form (used in the nineml-webapp) for the AL component.
        
        :param filename: string
        :param flatten: boolean
            
        :rtype:
        :raises: RuntimeError
        """
        if not self.ninemlComponent or not isinstance(self.ninemlComponent, nineml.abstraction_layer.ComponentClass):
            raise RuntimeError('Invalid input NineML component')
        
        content = ''
        content += '<fieldset>'
        content += '<legend>General</legend>'
        content += '<label for="testName">Test name</label>'
        content += '<input class="ninemlString required" id="id_testName" type="text" name="testName" value=""/><br/>'
        content += '<label for="testDescription">Test description</label>'
        content += '<textarea class="ninemlMultilineString" id="id_testDescription" name="testDescription" rows="2" cols="2"></textarea><br/>'
        content += '</fieldset>\n'

        content += '<fieldset>'
        content += '<legend>Simulation</legend>'
        content += '<label for="timeHorizon">Time horizon</label>'
        content += '<input class="ninemlFloat required number" id="id_timeHorizon" type="text" name="timeHorizon" value="{0}"/><br/>'.format(self.timeHorizon)
        content += '<label for="reportingInterval">Reporting interval</label>'
        content += '<input class="ninemlFloat required number" id="id_reportingInterval" type="text" name="reportingInterval" value="{0}"/><br/>'.format(self.reportingInterval)
        content += '</fieldset>\n'

        if len(self.parameters) > 0:
            content += '<fieldset>'
            content += '<legend>Parameters</legend>\n'
            content += self._generateHTMLFormTree(self.treeParameters, nineml_component_inspector.categoryParameters)
            content += '</fieldset>\n'

        if len(self.initial_conditions) > 0:
            content += '<fieldset>'
            content += '<legend>Initial conditions</legend>\n'
            content += self._generateHTMLFormTree(self.treeInitialConditions, nineml_component_inspector.categoryInitialConditions) + '\n'
            content += '</fieldset>\n'

        if len(self.active_regimes) > 0:
            content += '<fieldset>'
            content += '<legend>Initially active regimes</legend>\n'
            content += self._generateHTMLFormTree(self.treeActiveStates, nineml_component_inspector.categoryActiveStates)
            content += '</fieldset>\n'

        if len(self.analog_ports_expressions) > 0:
            content += '<fieldset>'
            content += '<legend>Analog-ports inputs</legend>\n'
            content += self._generateHTMLFormTree(self.treeAnalogPorts, nineml_component_inspector.categoryAnalogPortsExpressions, True) + '\n'
            content += '</fieldset>\n'

        if len(self.event_ports_expressions) > 0:
            content += '<fieldset>'
            content += '<legend>Event-ports inputs</legend>\n'
            content += self._generateHTMLFormTree(self.treeEventPorts, nineml_component_inspector.categoryEventPortsExpressions) + '\n'
            content += '</fieldset>\n'

        if len(self.variables_to_report) > 0:
            content += '<fieldset>'
            content +='<legend>Variables to report</legend>\n'
            content += self._generateHTMLFormTree(self.treeVariablesToReport, nineml_component_inspector.categoryVariablesToReport) + '\n'
            content += '</fieldset>\n'

        return content

    def _generateHTMLFormTree(self, item, category = '', required = False):
        """
        Internal function to recursively generate a HTML form for the given treeItem root item.
        
        :param item: treeItem object
        :param category: string
        :param required: boolean
            
        :rtype: string
        :raises:
        """
        if category == '':
            inputName = item.canonicalName
        else:
            inputName = category + '.' + item.canonicalName

        content = '<ul>'
        if item.itemType == treeItem.typeFloat:
            content += '<li><label for="{1}">{0}</label><input class="ninemlFloat required number" type="text" name="{1}" value="{2}"/></li>'.format(item.name, inputName, item.value)

        elif item.itemType == treeItem.typeInteger:
            content += '<li><label for="{1}">{0}</label><input class="ninemlFloat required digits" type="text" name="{1}" value="{2}"/></li>'.format(item.name, inputName, item.value)

        elif item.itemType == treeItem.typeString:
            if required:
                content += '<li><label for="{1}">{0}</label><input class="ninemlString required" type="text" name="{1}" value="{2}"/></li>'.format(item.name, inputName, item.value)
            else:
                content += '<li><label for="{1}">{0}</label><input class="ninemlString" type="text" name="{1}" value="{2}"/></li>'.format(item.name, inputName, item.value)

        elif item.itemType == treeItem.typeBoolean:
            if item.value:
                content += '<li><label for="{1}">{0}</label><input class="ninemlCheckBox" type="checkbox" name="{1}" checked/></li>'.format(item.name, inputName)
            else:
                content += '<li><label for="{1}">{0}</label><input class="ninemlCheckBox" type="checkbox" name="{1}"/></li>'.format(item.name, inputName)

        elif item.itemType == treeItem.typeList:
            if isinstance(item.data, collections.Iterable) and len(item.data) > 0:
                content += '<li><label for="{1}">{0}</label> <select class="ninemlComboBox" name="{1}">'.format(item.name, inputName)
                for available_regime in item.data:
                    if available_regime == item.value:
                        content += '<option value="{0}" selected>{0}</option>'.format(available_regime)
                    else:
                        content += '<option value="{0}">{0}</option>'.format(available_regime)
                content += '</select></li>'
            else:
                content += '<li>{0}</li>'.format(item.name)

        else:
            content += '<li>{0}</li>'.format(item.name)

        for child in item.children:
            content += self._generateHTMLFormTree(child, category, required)

        content += '</ul>'
        return content

    def generateHTMLReport(self, tests = []):
        """
        Generates HTML report for the AL component.
            
        :rtype: string
        :raises: RuntimeError
        """
        content       = []
        tests_content = []
        parser        = ExpressionParser()
        
        # Collect all unique components from sub-nodes:
        unique_components = {}
        self._detectUniqueComponents(self.ninemlComponent, unique_components)

        # Add all detected components to the report
        for name, component in unique_components.items():
            self._addComponentToHTMLReport(content, component, name, parser)

        # Add all tests to the report
        for test in tests:
            self._addTestToHTMLReport(tests_content, test)

        return (''.join(content), ''.join(tests_content))

    def _addComponentToHTMLReport(self, content, component, name, parser):
        """
        Adds AL component to HTML report.
            
        :rtype: string
        :raises: RuntimeError
        """
        content.append('<h2>NineML Component: {0}</h2>\n\n'.format(name))
        
        # 1) Create parameters
        parameters = list(component.parameters)
        if len(parameters) > 0:
            content.append('<h3>Parameters</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>Name</th> <th>Units</th> <th>Notes</th> </tr>\n')
            for param in parameters:
                _name = self._correctName(param.name)
                content.append('<tr> <td>{0}</td> <td>{1}</td> <td>{2}</td> </tr>\n'.format(_name, ' - ', ' '))
            content.append('</table>\n')

        # 2) Create state-variables (diff. variables)
        state_variables = list(component.state_variables)
        if len(state_variables) > 0:
            content.append('<h3>State-Variables</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>Name</th> <th>Units</th> <th>Notes</th> </tr>\n')
            for var in state_variables:
                _name = self._correctName(var.name)
                content.append('<tr> <td>{0}</td> <td>{1}</td> <td>{2}</td> </tr>\n'.format(_name, ' - ', ' '))
            content.append('</table>\n')

        # 3) Create alias variables (algebraic)
        aliases = list(component.aliases)
        if len(aliases) > 0:
            content.append('<h3>Aliases</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>Name</th> <th>Expression</th> <th>Units</th> <th>Notes</th> </tr>\n')
            for alias in aliases:
                _name = alias.lhs
                _rhs  = '<math xmlns="http://www.w3.org/1998/Math/MathML">'
                _rhs += parser.parse_to_mathml(alias.rhs)
                _rhs += '</math>'
                content.append('<tr> <td>{0}</td> <td>{1}</td> <td>{2}</td> <td>{3}</td> </tr>\n'.format(_name, _rhs, ' - ', ' '))
            content.append('</table>\n')
        
        # 4) Create analog-ports and reduce-ports
        analog_ports = list(component.analog_ports)
        if len(analog_ports) > 0:
            content.append('<h3>Analog Ports</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>Name</th> <th>Type</th> <th>Units</th> <th>Notes</th> </tr>\n')
            for port in analog_ports:
                _name = self._correctName(port.name)
                _type = port.mode
                content.append('<tr> <td>{0}</td> <td>{1}</td> <td>{2}</td> <td>{3}</td> </tr>\n'.format(_name, _type, ' - ', ' '))
            content.append('</table>\n')

        # 5) Create event-ports
        event_ports = list(component.event_ports)
        if len(event_ports) > 0:
            content.append('<h3>Event Ports</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>Name</th> <th>Type</th> <th>Units</th> <th>Notes</th> </tr>\n')
            for port in event_ports:
                _name = port.name
                _type = port.mode
                content.append('<tr> <td>{0}</td> <td>{1}</td> <td>{2}</td> <td>{3}</td> </tr>\n'.format(_name, _type, ' - ', ' '))
            content.append('</table>\n')
        
        # 6) Create sub-nodes
        """
        Do we need this??
        
        if len(component.subnodes.items()) > 0:
            content.append('\\subsection*{Sub-nodes}\n\n')
            content.append(nineml_component_inspector.begin_itemize)
            for name, subcomponent in component.subnodes.items():
                _name = self._correctName(name)
                tex = nineml_component_inspector.item + _name + '\n'
                content.append(tex)
            content.append(nineml_component_inspector.end_itemize)
            content.append('\n')
        """
        
        # 7) Create port connections
        portconnections = list(component.portconnections)
        if len(portconnections) > 0:
            content.append('<h3>Port Connections</h3>\n\n')
            content.append('<table>\n')
            content.append('<tr> <th>From</th> <th>To</th> </tr>\n')
            for port_connection in portconnections:
                portFrom = '.'.join(port_connection[0].loctuple)
                portTo   = '.'.join(port_connection[1].loctuple)
                _fromname = self._correctName(portFrom)
                _toname   = self._correctName(portTo)
                content.append('<tr> <td>{0}</td> <td>{1}</td> </tr>\n'.format(_fromname, _toname))
            content.append('</table>\n')

        # 8) Create regimes
        regimes = list(component.regimes)
        if len(regimes) > 0:
            regimes_list     = []
            transitions_list = []

            content.append('<h3>Regimes</h3>\n\n')
            for ir, regime in enumerate(regimes):
                regimes_list.append(regime.name)
                
                mathml = ''
                # 8a) Create time derivatives
                for time_deriv in regime.time_derivatives:
                    mathml += '<mtr> <mrow> <mfrac> <mi fontstyle="italic">d{0}</mi> <mi fontstyle="italic">dt</mi> </mfrac> = {1} </mrow> </mtr>\n'.format(time_deriv.dependent_variable, parser.parse_to_mathml(time_deriv.rhs))
            
                # 8b) Create on_condition actions
                for on_condition in regime.on_conditions:
                    regimeFrom = regime.name
                    if on_condition.target_regime.name == '':
                        regimeTo = regimeFrom
                    else:
                        regimeTo = on_condition.target_regime.name
                    
                    condition = parser.parse_to_mathml(on_condition.trigger.rhs)
                    mathml += '<mtr> <mrow> <mtext>if </mtext> <mspace width="0.3em"/> {0} </mrow> </mtr>\n'.format(condition)

                    if regimeTo != regimeFrom:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>switch to</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> </mrow> </mtr>\n'.format(regimeTo)

                    for state_assignment in on_condition.state_assignments:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>set</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> = {1} </mrow> </mtr>\n'.format(state_assignment.lhs, parser.parse_to_mathml(state_assignment.rhs))

                    for event_output in on_condition.event_outputs:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>emit</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> </mrow> </mtr>\n'.format(event_output.port_name)

                    transition = '{0} -> {1} [label="{2}"];'.format(regimeFrom, regimeTo, condition)
                    transitions_list.append(transition)

                # 8c) Create on_event actions
                for on_event in regime.on_events:
                    regimeFrom = regime.name
                    if on_event.target_regime.name == '':
                        regimeTo = regimeFrom
                    else:
                        regimeTo = on_event.target_regime.name
                    source_port = on_event.src_port_name

                    mathml += '<mtr> <mrow> <mtext>on</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> </mrow> </mtr>\n'.format(source_port)

                    if regimeTo != regimeFrom:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>switch to</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> </mrow> </mtr>\n'.format(regimeTo)

                    for state_assignment in on_event.state_assignments:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>set</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> = {1} </mrow> </mtr>\n'.format(state_assignment.lhs, parser.parse_to_mathml(state_assignment.rhs))

                    for event_output in on_event.event_outputs:
                        mathml += '<mtr> <mrow> <mspace width="1em"/> <mtext>emit</mtext> <mspace width="0.3em"/> <mi fontstyle="italic">{0}</mi> </mrow> </mtr>\n'.format(event_output.port_name)

                    transition = '{0} -> {1} [label="{2}"];'.format(regimeFrom, regimeTo, source_port)
                    transitions_list.append(transition)

                content.append('<p>\n')
                content.append('<math xmlns="http://www.w3.org/1998/Math/MathML">\n')
                content.append('<mrow> <mi fontstyle="italic">{0}</mi> = <mo>{{</mo> <mtable> {1} </mtable> </mrow>\n'.format(regime.name, mathml))
                content.append('</math>\n')
                content.append('</p>\n')

            """
            dot_graph_template = '''
            digraph finite_state_machine {{
                rankdir=LR;
                node [shape=ellipse]; {0};
                {1}
            }}
            '''
            if len(regimes_list) > 1:
                dot_graph = dot_graph_template.format(' '.join(regimes_list), '\n'.join(transitions_list))
                graph     = dot2tex.dot2tex(dot_graph, autosize=True, texmode='math', format='tikz', crop=True, figonly=True)
                tex_graph = '\\begin{center}\n' + graph + '\\end{center}\n'
                content.append('\\newline \n')
                content.append(tex_graph)
                content.append('\n')
            """
            
        return content

    def _generateHTMLReportTree(self, item):
        """
        Internal function to recursively generate a HTML report for the given treeItem root item.
        
        :param item: treeItem object
            
        :rtype: string
        :raises:
        """
        content = '<ul>'
        if item.itemType == treeItem.typeFloat:
            content += '<li>{0} ({1})</li>'.format(item.name, item.value)

        elif item.itemType == treeItem.typeInteger:
            content += '<li>{0} ({1})</li>'.format(item.name, item.value)

        elif item.itemType == treeItem.typeString:
            content += '<li>{0} ({1})</li>'.format(item.name, item.value)

        elif item.itemType == treeItem.typeBoolean:
            content += '<li>{0} ({1})</li>'.format(item.name, item.value)

        elif item.itemType == treeItem.typeList:
            content += '<li>{0} ({1})</li>'.format(item.name, item.value)

        else:
            content += '<li>{0}</li>'.format(item.name)

        for child in item.children:
            content += self._generateHTMLReportTree(child)

        content += '</ul>'
        return content
        
    def showQtGUI(self):
        """
        Generates and displays Qt GUI dialog and returns the simulation input data.
            
        :rtype: python tuple
        :raises: RuntimeError
        """
        if not self.ninemlComponent or not isinstance(self.ninemlComponent, nineml.abstraction_layer.ComponentClass):
            raise RuntimeError('Invalid input NineML component')

        app = QtGui.QApplication(sys.argv)
        gui = nineml_component_qtGUI(self)
        gui.ui.timeHorizonSLineEdit.setText(str(self.timeHorizon))
        gui.ui.reportingIntervalSLineEdit.setText(str(self.reportingInterval))

        isOK = gui.exec_()
        if isOK == QtGui.QDialog.Accepted:
            self.updateData(timeHorizon              = float(str(gui.ui.timeHorizonSLineEdit.text())),
                            reportingInterval        = float(str(gui.ui.reportingIntervalSLineEdit.text())),
                            parameters               = self.treeParameters.getDictionary(),
                            initial_conditions       = self.treeInitialConditions.getDictionary(),
                            active_regimes           = self.treeActiveStates.getDictionary(),
                            analog_ports_expressions = self.treeAnalogPorts.getDictionary(),
                            event_ports_expressions  = self.treeEventPorts.getDictionary(),
                            variables_to_report      = self.treeVariablesToReport.getDictionary())
            
            testName        = gui.ui.testNameLineEdit.text()
            testDescription = gui.ui.testDescriptionLineEdit.text()
            results = {}
            results['timeHorizon']              = self.timeHorizon
            results['reportingInterval']        = self.reportingInterval
            results['parameters']               = self.parameters
            results['initial_conditions']       = self.initial_conditions
            results['active_regimes']           = self.active_regimes
            results['analog_ports_expressions'] = self.analog_ports_expressions
            results['event_ports_expressions']  = self.event_ports_expressions
            results['variables_to_report']      = self.variables_to_report
            return (testName, testDescription, results)
        else:
            return None

    def generateLatexReport(self, tests = []):
        """
        Generates Latex/PDF report for the AL component (optional: test data).
        
        :param tests: list of tuples with the test data
            
        :rtype: python tuple (latex_report_as_a_string, string_list_with_the_tests_data)
        :raises: RuntimeError
        """
        if not self.ninemlComponent or not isinstance(self.ninemlComponent, nineml.abstraction_layer.ComponentClass):
            raise RuntimeError('Invalid input NineML component')

        content       = []
        tests_content = []
        parser        = ExpressionParser()

        # Collect all unique components from sub-nodes:
        unique_components = {}
        self._detectUniqueComponents(self.ninemlComponent, unique_components)

        # Add all detected components to the report
        for name, component in unique_components.items():
            self._addComponentToPDFReport(content, component, name, parser)

        # Add all tests to the report
        for test in tests:
            self._addTestToPDFReport(tests_content, test)

        return (''.join(content), ''.join(tests_content))

    def _detectUniqueComponents(self, component, unique_components):
        """
        Internal function to create a list of unique AL components to be included in the report.
        
        :param component: list of tuples with the test data
        :param unique_components: string list of unique AL Component names
            
        :rtype: 
        :raises:
        """
        if not component.name in unique_components:
            unique_components[component.name] = component

        for name, subcomponent in component.subnodes.items():
            self._detectUniqueComponents(subcomponent, unique_components)

    def _addTestToPDFReport(self, content, test):
        """
        Internal function used to add a test to the Latex/PDF report.
        
        :param content: string (Latex report)
        :param test: string with the test data
            
        :rtype: string
        :raises:
        """
        testName, testDescription, dictInputs, plots, log_output, tmpFolder = test
        
        testInputs = '\\begin{verbatim}\n'
        testInputs += 'Time horizon = {0}\n'.format(dictInputs['timeHorizon'])
        testInputs += 'Reporting interval = {0}\n'.format(dictInputs['reportingInterval'])
        
        testInputs += 'Parameters:\n'
        for name, value in dictInputs['parameters'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Initial conditions:\n'
        for name, value in dictInputs['initial_conditions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Analog ports expressions:\n'
        for name, value in dictInputs['analog_ports_expressions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Event ports expressions:\n'
        for name, value in dictInputs['event_ports_expressions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Initially active regimes:\n'
        for name, value in dictInputs['active_regimes'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Variables to report:\n'
        for name, value in dictInputs['variables_to_report'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += '\\end{verbatim}\n'

        content.append('\\subsection*{{Test: {0}}}\n\n'.format(testName))
        content.append('Description: \n{0}\\newline\n'.format(testDescription))
        content.append('Input data: \n{0}\\newline\n'.format(testInputs))
        for plot in plots:
            varName, xPoints, yPoints, pngName, csvName, pngPath, csvPath = plot
            tex_plot = '\\begin{center}\n\\includegraphics{' + pngPath + '}\n\\end{center}\n'
            content.append(tex_plot)
        
        return content
        
    def _addTestToHTMLReport(self, content, test):
        """
        Internal function used to add a test to the Latex/PDF report.
        
        :param content: string (Latex report)
        :param test: string with the test data
            
        :rtype: string
        :raises:
        """
        testName, testDescription, dictInputs, plots, log_output, tmpFolder = test
        
        testInputs = '<pre>\n'
        testInputs += 'Time horizon = {0}<br/>\n'.format(dictInputs['timeHorizon'])
        testInputs += 'Reporting interval = {0}<br/>\n'.format(dictInputs['reportingInterval'])
        
        testInputs += 'Parameters:<br/>\n'
        for name, value in dictInputs['parameters'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Initial conditions:<br/>\n'
        for name, value in dictInputs['initial_conditions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Analog ports expressions:<br/>\n'
        for name, value in dictInputs['analog_ports_expressions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Event ports expressions:<br/>\n'
        for name, value in dictInputs['event_ports_expressions'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Initially active regimes:<br/>\n'
        for name, value in dictInputs['active_regimes'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += 'Variables to report:<br/>\n'
        for name, value in dictInputs['variables_to_report'].items():
            testInputs += '    {0} = {1}\n'.format(name, value)
        
        testInputs += '</pre>\n'

        content.append('<h2>Test: {0}</h2>\n\n'.format(testName))
        content.append('<p>Description: \n{0}</p>\n'.format(testDescription))
        content.append('<p>Input data: \n{0}</p>\n'.format(testInputs))
        for plot in plots:
            varName, xPoints, yPoints, pngName, csvName, pngPath, csvPath = plot
            image = open(pngPath, 'rb').read()
            image_data = image.encode("base64")
            html_plot = '<p> <img src="data:image/png;base64,{0}" width="400" height="300"> </p>\n'.format(image_data)
            content.append(html_plot)
        
        return content
        
    def _correctName(self, name):
        """
        Internal function that replaces underscores with Latex mangles underscores in the given string.
        
        :param name: string
            
        :rtype: string
        :raises:
        """
        return name.replace('_', '\\_')
    
    def _addComponentToPDFReport(self, content, component, name, parser):
        """
        Internal function used to add a component to the Latex/PDF report.
        
        :param content: stringa
        :param component: AL Component object
        :param name: string
        :param parser: ExpressionParser object
            
        :rtype: string
        :raises:
        """
        comp_name = self._correctName(name)
        content.append('\\section{{NineML Component: {0}}}\n\n'.format(comp_name))

        # 1) Create parameters
        parameters = list(component.parameters)
        if len(parameters) > 0:
            content.append('\\subsection*{Parameters}\n\n')
            header_flags = ['l', 'c', 'l']
            header_items = ['Name', 'Units', 'Notes']
            rows_items = []
            for param in parameters:
                _name = self._correctName(param.name)
                rows_items.append([_name, ' - ', ' '])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')

        # 2) Create state-variables (diff. variables)
        state_variables = list(component.state_variables)
        if len(state_variables) > 0:
            content.append('\\subsection*{State-Variables}\n\n')
            header_flags = ['l', 'c', 'l']
            header_items = ['Name', 'Units', 'Notes']
            rows_items = []
            for var in state_variables:
                _name = self._correctName(var.name)
                rows_items.append([_name, ' - ', ' '])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')

        # 3) Create alias variables (algebraic)
        aliases = list(component.aliases)
        if len(aliases) > 0:
            content.append('\\subsection*{Aliases}\n\n')
            header_flags = ['l', 'l', 'c', 'l']
            header_items = ['Name', 'Expression', 'Units', 'Notes']
            rows_items = []
            for alias in aliases:
                _name = '${0}$'.format(alias.lhs)
                _rhs  = '${0}$'.format(parser.parse_to_latex(alias.rhs))
                rows_items.append([_name, _rhs, ' - ', ' '])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')

        # 4) Create analog-ports and reduce-ports
        analog_ports = list(component.analog_ports)
        if len(analog_ports) > 0:
            content.append('\\subsection*{Analog Ports}\n\n')
            header_flags = ['l', 'l', 'c', 'l']
            header_items = ['Name', 'Type', 'Units', 'Notes']
            rows_items = []
            for port in analog_ports:
                _name = self._correctName(port.name)
                _type = port.mode
                rows_items.append([_name, _type, ' - ', ' '])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')

        # 5) Create event-ports
        event_ports = list(component.event_ports)
        if len(event_ports) > 0:
            content.append('\\subsection*{Event ports}\n\n')
            header_flags = ['l', 'l', 'c', 'l']
            header_items = ['Name', 'Type', 'Units', 'Notes']
            rows_items = []
            for port in event_ports:
                _name = self._correctName(port.name)
                _type = port.mode
                rows_items.append([_name, _type, ' - ', ' '])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')
        
        # 6) Create sub-nodes
        """
        Do we need this??
        
        if len(component.subnodes.items()) > 0:
            content.append('\\subsection*{Sub-nodes}\n\n')
            content.append(nineml_component_inspector.begin_itemize)
            for name, subcomponent in component.subnodes.items():
                _name = self._correctName(name)
                tex = nineml_component_inspector.item + _name + '\n'
                content.append(tex)
            content.append(nineml_component_inspector.end_itemize)
            content.append('\n')
        """
        
        # 7) Create port connections
        portconnections = list(component.portconnections)
        if len(portconnections) > 0:
            content.append('\\subsection*{Port Connections}\n\n')
            header_flags = ['l', 'l']
            header_items = ['From', 'To']
            rows_items = []
            for port_connection in portconnections:
                portFrom = '.'.join(port_connection[0].loctuple)
                portTo   = '.'.join(port_connection[1].loctuple)
                _fromname = self._correctName(portFrom)
                _toname   = self._correctName(portTo)
                rows_items.append([_fromname, _toname])
            content.append(latex_table(header_flags, header_items, rows_items))
            content.append('\n')

        # 8) Create regimes
        regimes = list(component.regimes)
        """
        if len(regimes) > 0:
            content.append('\\subsection*{Regimes}\n\n')
            for regime in regimes:
                header_flags = ['l', 'l', 'l']
                header_items = ['ODEs', 'Transitions']
                rows_items = []

                _name = self._correctName(regime.name)
                _odes = []
                _on_events = []
                _on_conditions = []

                for time_deriv in regime.time_derivatives:
                    _odes.append('$\\frac{{d{0}}}{{dt}} = {1}$'.format(time_deriv.dependent_variable, parser.parse_to_latex(time_deriv.rhs)))

                for on_condition in regime.on_conditions:
                    _on_conditions.append('\\mbox{If } $' + parser.parse_to_latex(on_condition.trigger.rhs) + '$\mbox{:}')

                    if on_condition.target_regime.name != '':
                        _on_conditions.append('\\hspace*{{0.2in}} \\mbox{{switch to }} {0}'.format(on_condition.target_regime.name))

                    for state_assignment in on_condition.state_assignments:
                        _on_conditions.append('\\hspace*{{0.2in}} \\mbox{{set }} {0} = {1}'.format(state_assignment.lhs, parser.parse_to_latex(state_assignment.rhs)))

                    for event_output in on_condition.event_outputs:
                        _on_conditions.append('\\hspace*{{0.2in}} \\mbox{{emit }} {0}'.format(event_output.port_name))

                # 8c) Create on_event actions
                for on_event in regime.on_events:
                    _on_events.append('\\mbox{On } $' + on_event.src_port_name + '$\mbox{:}')

                    if on_event.target_regime.name != '':
                        _on_events.append('\\hspace*{{0.2in}} \\mbox{{switch to }} {0}'.format(on_event.target_regime.name))

                    for state_assignment in on_event.state_assignments:
                        _on_events.append('\\hspace*{{0.2in}} \\mbox{{set }} {0} = {1}'.format(state_assignment.lhs, parser.parse_to_latex(state_assignment.rhs)))

                    for event_output in on_event.event_outputs:
                        _on_events.append('\\hspace*{{0.2in}} \\mbox{{emit }} {0}'.format(event_output.port_name))

                content.append(latex_regime_table(header_flags, _name, _odes, _on_conditions, _on_events))
                content.append('\n')
        """
        if len(regimes) > 0:
            regimes_list     = []
            transitions_list = []

            content.append('\\subsection*{Regimes}\n\n')
            for ir, regime in enumerate(regimes):
                regimes_list.append(self._correctName(regime.name))

                tex = ''
                # 8a) Create time derivatives
                counter = 0
                for time_deriv in regime.time_derivatives:
                    if counter != 0:
                        tex += ' \\\\ '
                    tex += '\\frac{{d{0}}}{{dt}} = {1}'.format(time_deriv.dependent_variable, parser.parse_to_latex(time_deriv.rhs))
                    counter += 1

                # 8b) Create on_condition actions
                for on_condition in regime.on_conditions:
                    regimeFrom = self._correctName(regime.name)
                    if on_condition.target_regime.name == '':
                        regimeTo = regimeFrom
                    else:
                        regimeTo = self._correctName(on_condition.target_regime.name)
                    condition  = parser.parse_to_latex(on_condition.trigger.rhs)

                    tex += ' \\\\ \\mbox{If } ' + condition + '\mbox{:}'

                    if regimeTo != regimeFrom:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{switch to }} {0}'.format(regimeTo)

                    for state_assignment in on_condition.state_assignments:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{set }} {0} = {1}'.format(state_assignment.lhs, parser.parse_to_latex(state_assignment.rhs))

                    for event_output in on_condition.event_outputs:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{emit }} {0}'.format(event_output.port_name)

                    transition = '{0} -> {1} [label="{2}"];'.format(regimeFrom, regimeTo, condition)
                    transitions_list.append(transition)

                # 8c) Create on_event actions
                for on_event in regime.on_events:
                    regimeFrom = regime.name
                    if on_event.target_regime.name == '':
                        regimeTo = regimeFrom
                    else:
                        regimeTo = on_event.target_regime.name
                    source_port = on_event.src_port_name

                    tex += ' \\\\ \\mbox{On } ' + source_port + '\mbox{:}'

                    if regimeTo != regimeFrom:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{switch to }} {0}'.format(regimeTo)

                    for state_assignment in on_event.state_assignments:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{set }} {0} = {1}'.format(state_assignment.lhs, parser.parse_to_latex(state_assignment.rhs))

                    for event_output in on_event.event_outputs:
                        tex += ' \\\\ \\hspace*{{0.2in}} \\mbox{{emit }} {0}'.format(event_output.port_name)

                    transition = '{0} -> {1} [label="{2}"];'.format(regimeFrom, regimeTo, source_port)
                    transitions_list.append(transition)

                tex = '${0} = \\begin{{cases}} {1} \\end{{cases}}$\n'.format(regime.name, tex)
                tex += '\\newline \n'
                content.append(tex)

            dot_graph_template = '''
            digraph finite_state_machine {{
                rankdir=LR;
                node [shape=ellipse]; {0};
                {1}
            }}
            '''
            if len(regimes_list) > 1:
                dot_graph = dot_graph_template.format(' '.join(regimes_list), '\n'.join(transitions_list))
                graph     = dot2tex.dot2tex(dot_graph, autosize=True, texmode='math', format='tikz', crop=True, figonly=True)
                tex_graph = '\\begin{center}\n' + graph + '\\end{center}\n'
                content.append('\\newline \n')
                content.append(tex_graph)
                content.append('\n')
            
            content.append('\\newpage')
            content.append('\n')
            
        return content

if __name__ == "__main__":
    #nineml_component = '/home/ciroki/Data/daetools/trunk/python-files/examples/iaf.xml'
    nineml_component = TestableComponent('hierachical_iaf_1coba')()
    if not nineml_component:
        raise RuntimeError('Cannot load NineML component')

    timeHorizon = 10
    reportingInterval = 0.01
    parameters = {
        'cobaExcit.q' : 3.0,
        'cobaExcit.tau' : 5.0,
        'cobaExcit.vrev' : 0.0,
        'iaf.cm' : 1,
        'iaf.gl' : 50,
        'iaf.taurefrac' : 0.008,
        'iaf.vreset' : -60,
        'iaf.vrest' : -60,
        'iaf.vthresh' : -40
    }
    initial_conditions = {
        'cobaExcit.g' : 0.0,
        'iaf.V' : -60,
        'iaf.tspike' : -1E99
    }
    analog_ports_expressions = {}
    event_ports_expressions = {}
    active_regimes = {
        'cobaExcit' : 'cobadefaultregime',
        'iaf' : 'subthresholdregime'
    }
    variables_to_report = {
        'cobaExcit.I' : True,
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
    isOK = inspector.showQtGUI()
    inspector.printCollectedData()
    
    f = open('report.html', 'w')
    content, tests = inspector.generateHTMLReport()
    f.write(content + tests)
    f.close()
    
