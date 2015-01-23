

import unittest


from nineml.abstraction_layer import NamespaceAddress as NSA
from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction_layer.dynamics import DynamicsClass as ComponentClass


class NamespaceAddress_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_concat(self):
        # Signature: name(cls, *args)
                # Concatenates all the Namespace Addresses.
                #
                # This method take all the arguments supplied, converts each one into a
                # namespace object, then, produces a new namespace object which is the
                # concatentation of all the arugements namespaces.
                #
                # For example:
                #
                # >>> NamespaceAddress.concat('first.second','third.forth','fifth.sixth')
                #     NameSpaceAddress: '/first/second/third/forth/fifth/sixth'
        # from nineml.abstraction_layer.component.namespaceaddress import NamespaceAddress
        self.assertEqual(
            NSA.concat(NSA('a.b.c'), NSA('d.e.f'), NSA('g.h.i')),
            NSA('a.b.c.d.e.f.g.h.i'))
        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA('a.b.c'), NSA.create_root()),
            NSA('a.b.c')
        )
        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA.create_root()),
            NSA.create_root()
        )

    def test_create_root(self):
        # Signature: name(cls)
                # Returns a empty (root) namespace address
                #
                #
                # >>> nineml.abstraction_layer.NamespaceAddress.create_root()
                # NameSpaceAddress: '//'
        # from nineml.abstraction_layer.component.namespaceaddress import NamespaceAddress
        self.assertEqual(NSA.create_root().loctuple, ())

    def test_get_local_name(self):
        # Signature: name(self)
                # Returns the local reference; i.e. the last field in the
                # address, as a ``string``
        # from nineml.abstraction_layer.component.namespaceaddress import NamespaceAddress
        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').get_local_name(),
            'i')
        self.assertEqual(
            NSA('a.b.lastname').get_local_name(),
            'lastname')
        self.assertRaises(
            NineMLRuntimeError,
            NSA.create_root().get_local_name,
        )

    def test_get_parent_addr(self):
        # Signature: name(self)
                # Return the address of an namespace higher
                #
                # >>> a = NamespaceAddress('level1.level2.level3')
                # >>> a
                # NameSpaceAddress: '/level1/level2/level3/'
                # >>> a.get_parent_addr()
                # NameSpaceAddress: '/level1/level2/'

        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').get_parent_addr(),
            NSA('a.b.c.d.e.f.g.h')
        )

        self.assertEqual(
            NSA('a.b.lastname').get_parent_addr(),
            NSA('a.b')
        )

        self.assertRaises(
            NineMLRuntimeError,
            NSA.create_root().get_local_name,
        )

    def test_get_subns_addr(self):
        # Signature: name(self, component_name)
                # Returns the address of a subcomponent at this address.
                #
                # For example:
                #
                # >>> a = NamespaceAddress('level1.level2.level3')
                # >>> a.get_subns_addr('subcomponent')
                # NameSpaceAddress: '/level1/level2/level3/subcomponent/'

        d = ComponentClass(name='D',)
        e = ComponentClass(name='E')
        f = ComponentClass(name='F')
        g = ComponentClass(name='G')
        b = ComponentClass(name='B', subnodes={'atD': d, 'atE': e})
        c = ComponentClass(name='C', subnodes={'atF': f, 'atG': g})
        a = ComponentClass(name='A', subnodes={'atB': b, 'atC': c})

        # Construction of the objects causes cloning to happen:
        # Therefore we test by looking up and checking that there
        # are the correct component names:
        bNew = a.get_subnode('atB')
        cNew = a.get_subnode('atC')
        dNew = a.get_subnode('atB.atD')
        eNew = a.get_subnode('atB.atE')
        fNew = a.get_subnode('atC.atF')
        gNew = a.get_subnode('atC.atG')

        self.assertEquals(
            gNew.get_node_addr().get_subns_addr('MyObject1'),
            NSA('atC.atG.MyObject1')
        )

        self.assertEquals(
            eNew.get_node_addr().get_subns_addr('MyObject2'),
            NSA('atB.atE.MyObject2')
        )

        self.assertEquals(
            bNew.get_node_addr().get_subns_addr('MyObject3'),
            NSA('atB.MyObject3')
        )

    def test_getstr(self):
        # Signature: name(self, join_char='_')
                # Returns the namespace address as a string.
                #
                # :param join_char: The character used to join the levels in the address.
        # from nineml.abstraction_layer.component.namespaceaddress import NamespaceAddress

        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').getstr('.'),
            'a.b.c.d.e.f.g.h.i'
        )

        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA.create_root(), NSA(
                       'a.b.c.d.e.f.g.h.i')).getstr('.'),
            'a.b.c.d.e.f.g.h.i'
        )

        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA.create_root(), NSA(
                       'a.b.c.d.e.f.g.h.i'), NSA.create_root(),).getstr('.'),
            'a.b.c.d.e.f.g.h.i'
        )

        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').getstr('/'),
            'a/b/c/d/e/f/g/h/i'
        )

    def test_get_str_prefix(self):
        # Signature: name(self, join_char='_')
                # Returns the same as ``getstr``, but prepends the ``join_char`` to
                # the end of the string, so that the string can be used to prefix
                # variables.
                #
                # :param join_char: The character used to join the levels in the address.
        # from nineml.abstraction_layer.component.namespaceaddress import NamespaceAddress

        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').get_str_prefix('.'),
            'a.b.c.d.e.f.g.h.i.'
        )

        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA.create_root(),
                       NSA('a.b.c.d.e.f.g.h.i')).get_str_prefix('.'),
            'a.b.c.d.e.f.g.h.i.'
        )

        self.assertEqual(
            NSA.concat(NSA.create_root(), NSA.create_root(),
                       NSA('a.b.c.d.e.f.g.h.i'), NSA.create_root(),).get_str_prefix('.'),
            'a.b.c.d.e.f.g.h.i.'
        )

        self.assertEqual(
            NSA('a.b.c.d.e.f.g.h.i').get_str_prefix('/'),
            'a/b/c/d/e/f/g/h/i/'
        )
