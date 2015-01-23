"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from nineml.abstraction_layer.dynamics.utils import xml


class TestWriteDot(object):

    @classmethod
    def test(cls, testable_component, build_dir):  # @UnusedVariable
        print "Removed Dot writer"
#         component = testable_component()
#         print '  -- Writing Component to .dot'
#         dotfile = build_dir + component.name + '.dot'
#         writers.DotWriter.write(component, dotfile)
#
#         print '  -- Building .dot -> pdf, svg, png'
#         writers.DotWriter.build(dotfile, output_types=['pdf', 'svg', 'png'])
