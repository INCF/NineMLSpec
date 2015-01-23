"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import os
import sys

from nineml.exceptions import NineMLRuntimeError
from nineml.utils import restore_sys_path
from nineml.utils import LocationMgr
from nineml.abstraction_layer import DynamicsClass


@restore_sys_path
def load_py_module(filename):
    """Takes the fully qualified path of a python file,
    loads it and returns the module object
    """

    if not os.path.exists(filename):
        print "CWD:", os.getcwd()
        raise NineMLRuntimeError('File does not exist %s' % filename)

    dirname, fname = os.path.split(filename)
    sys.path = [dirname] + sys.path

    module_name = fname.replace('.py', '')
    module_name_short = module_name

    module = __import__(module_name)
    return module


class TestableComponent(object):

    @classmethod
    def list_available(cls):
        """Returns a list of strings, of the available components"""
        compdir = LocationMgr.getComponentDir()
        comps = []
        for fname in os.listdir(compdir):
            fname, ext = os.path.splitext(fname)
            if not ext == '.py':
                continue
            if fname == '__init__':
                continue
            comps.append(fname)
        return comps

    functor_name = 'get_component'
    metadata_name = 'ComponentMetaData'

    def __str__(self):
        s = ('Testable Component from %s [MetaData=%s]' %
             (self.filename, self.has_metadata))
        return s

    def has_metadata(self):
        return self.metadata != None

    def __call__(self):
        return self.component_functor()

    def __init__(self, filename):
        cls = TestableComponent

        # If we recieve a filename like 'iaf', that doesn't
        # end in '.py', then lets prepend the component directory
        # and append .py
        if not filename.endswith('.py'):
            compdir = LocationMgr.getComponentDir()
            filename = os.path.join(compdir, '%s.py' % filename)

        self.filename = filename
        self.mod = load_py_module(filename)

        # Get the component functor:
        if cls.functor_name not in self.mod.__dict__.keys():
            err = """Can't load TestableComponnet from %s""" % self.filename
            err += """Can't find required method: %s""" % cls.functor_name
            raise NineMLRuntimeError(err)

        self.component_functor = self.mod.__dict__[cls.functor_name]

        # Check the functor will actually return us an object:
        try:
            c = self.component_functor()
        except Exception:
            raise NineMLRuntimeError('component_functor() threw an exception')

        if not isinstance(c, DynamicsClass):
            raise NineMLRuntimeError('Functor does not return Component Class')

        # Try and get the meta-data
        self.metadata = None
        if cls.metadata_name in self.mod.__dict__.keys():
            self.metadata = self.mod.__dict__[cls.metadata_name]
