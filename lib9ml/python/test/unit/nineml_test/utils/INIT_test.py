

import warnings
import unittest
import types
import numbers
import sys

from nineml.utils import (check_list_contain_same_items, expect_single,
                          flatten_first_level, invert_dictionary,
                          assert_no_duplicates, restore_sys_path, safe_dict,
                          safe_dictionary_merge, filter_expect_single,
                          filter_by_type, filter_discrete_types)
from nineml.exceptions import NineMLRuntimeError


class Testcheck_list_contain_same_items(unittest.TestCase):

    def test_check_list_contain_same_items(self):
        # Signature: name(lst1, lst2, desc1='', desc2='', ignore=[], desc='')
                # No Docstring


        self.assertRaises(
            NineMLRuntimeError,
            check_list_contain_same_items,
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4],
        )
        self.assertRaises(
            NineMLRuntimeError,
            check_list_contain_same_items,
            ['some', 'funny', 'order', 'in', 'extra'],
            ['some', 'funny', 'order', 'in'],
        )

        # Good cases:
        check_list_contain_same_items(
            ['in', 'some', 'funny', 'order', ],
            ['some', 'funny', 'order', 'in'],
        )

        check_list_contain_same_items(
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        )

        check_list_contain_same_items(
            [1, 3, 4, 5, 2],
            [1, 2, 3, 4, 5],
        )

        # Chack ignoring:
        check_list_contain_same_items(
            [1, 3, 4, 5, 2],
            [1, 2, 3, 4, 5, 6],
            ignore=[6],
        )


# Testing Skeleton for function:
class Testfilter_expect_single(unittest.TestCase):

    def test_filter_expect_single(self):
        # Signature: name(lst, func=None, error_func=None)
                # Find a single element matching a predicate in a list.
                #
                # This is a syntactic-sugar function ``_filter`` and ``expect_single``
                # in a single call.
                #
                #  Returns::
                #
                #      expect_single( _filter(lst, func), error_func )
                #
                #
                #  This is useful when we want to find an item in a sequence with a certain
                #  property, and expect there to be only one.
                #
                #  Examples:
                #
                #  >>> find_smith = lambda s: s.split()[-1] == 'Smith'
                # >>> filter_expect_single( ['John Smith','Tim Jones'], func=find_smith )  #doctest: +NORMALIZE_WHITESPACE
                #  'John Smith'

        find_smith = lambda s: s.split()[-1] == 'Smith'
        self.assertEqual(
            filter_expect_single(['John Smith', 'Tim Jones'], func=find_smith),
            'John Smith'
        )

        self.assertEqual(
            filter_expect_single(['Rob Black', 'John Smith', 'Tim Jones'], func=find_smith),
            'John Smith'
        )
        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, ['Rob Black', 'Tim Jones'], func=find_smith,
        )

        # No Objects:
        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [], func=lambda x: None,
        )

        # Only a single None
        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [None], func=lambda x: x == None,
        )

        # Duplicate objects:
        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [None, None], func=lambda x: x == None,
        )

        # Duplicate objects:
        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [False, False], func=lambda x: x == None,
        )

        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [True, True], func=lambda x: x == None,
        )

        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, [1, 2, 3, 4, 5, 4, 3, 2, 1], func=lambda x: x == 2,
        )

        self.assertRaises(
            NineMLRuntimeError,
            filter_expect_single, ['1', '2', '3', '4', '3', '2', '1'], func=lambda x: x == '2',
        )

        self.assertEqual(
            True,
            filter_expect_single(['1', '2', '3', '4', '5', True], func=lambda x: x is True)
        )
        # Good Cases
        self.assertEqual(
            2,
            filter_expect_single([1, 2, 3, 4, 5], func=lambda x: x == 2)
        )
        self.assertEqual(
            '2',
            filter_expect_single(['1', '2', '3', '4', '5'], func=lambda x: x == '2')
        )


# Testing Skeleton for function:
class Testexpect_single(unittest.TestCase):

    def test_expect_single(self):
        # Signature: name(lst, error_func=None)
                # Retrieve a single element from an iterable.
                #
                # This function tests whether an iterable contains just a single element and
                # if so returns that element. Otherwise it raises an Exception.
                #
                # :param lst: An iterable
                #
                # :param error_func: An exception object or a callable. ``error_func`` will be
                #     raised or called in case there is not exactly one element in ``lst``. If
                #     ``error_func`` is ``None``, a ``NineMLRuntimeError`` exception will be
                #     raised.
                #
                #
                # :rtype: the element in the list, ``lst[0]``, provided ``len(lst)==1``
                #
                #
                #
                # >>> expect_single( ['hello'] )
                # 'hello'
                #
                # >>> expect_single( [1] )
                # 1
                #
                # >>> expect_single( [] ) #doctest: +SKIP
                # NineMLRuntimeError: expect_single() recieved an iterable of length: 0
                #
                # >>> expect_single( [None,None] ) #doctest: +SKIP
                # NineMLRuntimeError: expect_single() recieved an iterable of length: 2
                #
                # >>> expect_single( [], lambda: raise_exception( RuntimeError('Aggh') ) #doctest: +SKIP
                # RuntimeError: Aggh
                #
                # >>> #Slightly more tersly:
                # >>> expect_single( [], RuntimeError('Aggh') ) #doctest: +SKIP
                # RuntimeError: Aggh


        # Empty Objects should raise:
        self.assertRaises(NineMLRuntimeError, expect_single, [])
        self.assertRaises(NineMLRuntimeError, expect_single, tuple())
        self.assertRaises(NineMLRuntimeError, expect_single, set())

        # Dictionaries should raise:
        self.assertRaises(NineMLRuntimeError, expect_single, {})
        self.assertRaises(NineMLRuntimeError, expect_single, {1: None})
        self.assertRaises(NineMLRuntimeError, expect_single, {1: None, 2: True})

        # Strings should raise:
        self.assertRaises(NineMLRuntimeError, expect_single, "")
        self.assertRaises(NineMLRuntimeError, expect_single, "A")
        self.assertRaises(NineMLRuntimeError, expect_single, "AA")

        # Two items should raise:
        self.assertRaises(NineMLRuntimeError, expect_single, [None, None])
        self.assertRaises(NineMLRuntimeError, expect_single, [True, False])
        self.assertRaises(NineMLRuntimeError, expect_single, [True, True])
        self.assertRaises(NineMLRuntimeError, expect_single, ["Hello", "World"])

        # Some good cases:
        self.assertEqual(expect_single([None]), None)
        self.assertEqual(expect_single([1]), 1)
        self.assertEqual(expect_single([2]), 2)
        self.assertEqual(expect_single(['2']), '2')
        self.assertEqual(expect_single(['hello']), 'hello')


# Testing Skeleton for function:


class Testflatten_first_level(unittest.TestCase):

    def test_flatten_first_level(self):
        # Signature: name(nested_list)
                # Flattens the first level of an iterable, ie
                #
                # >>> flatten_first_level( [ ['This','is'],['a','short'],['phrase'] ] ) #doctest: +NORMALIZE_WHITESPACE
                # ['This', 'is', 'a', 'short', 'phrase']

        self.assertEqual(
            flatten_first_level([[1, 2], [3, 4, 5], [6]]),
            [1, 2, 3, 4, 5, 6]
        )

        self.assertEqual(
            flatten_first_level(((1, 2), (3, 4, 5), (6,))),
            [1, 2, 3, 4, 5, 6]
        )

        # Check nesting is not flattened:
        self.assertEqual(
            flatten_first_level([[1, ['a', 'b'], 2], [3, 4, ['c', 'd'], 5], [6]]),
            [1, ['a', 'b'], 2, 3, 4, ['c', 'd'], 5, 6]
        )

        self.assertRaises(NineMLRuntimeError, flatten_first_level, [None])
        self.assertRaises(NineMLRuntimeError, flatten_first_level, ['abbn'])
        self.assertRaises(NineMLRuntimeError, flatten_first_level, [True])
        self.assertRaises(NineMLRuntimeError, flatten_first_level, [None, None])


# Testing Skeleton for function:
class Testinvert_dictionary(unittest.TestCase):

    def test_invert_dictionary(self):
        # Signature: name(dct)
                # Takes a dictionary mapping (keys => values) and returns a
                # new dictionry mapping (values => keys).
                # i.e. given a dictionary::
                #
                #     {k1:v1, k2:v2, k3:v3, ...}
                #
                # it returns a dictionary::
                #
                #     {v1:k1, v2:k2, v3:k3, ...}
                #
                # It checks to make sure that no values are duplicated before converting.

        # Good cases:
        self.assertEqual(
            invert_dictionary({}),
            {},
        )

        self.assertEqual(
            invert_dictionary({1: True, 2: False}),
            {True: 1, False: 2},
        )
        self.assertEqual(
            invert_dictionary({2: True, 1: False}),
            {True: 2, False: 1},
        )

        self.assertEqual(
            invert_dictionary({'red': 'RED', 'blue': 'BLUE'}),
            {'BLUE': 'blue', 'RED': 'red'},
        )

        # Bad cases (Duplicates in values):
        self.assertRaises(
            NineMLRuntimeError,
            invert_dictionary, {'RED': 1, 'BLUE': 1},
        )

        self.assertRaises(
            NineMLRuntimeError,
            invert_dictionary, {True: None, False: None},
        )

        # Unhashable values:
        self.assertRaises(
            NineMLRuntimeError,
            invert_dictionary, {True: None, False: {1: None}},
        )


# Testing Skeleton for function:
class Testassert_no_duplicates(unittest.TestCase):

    def test_assert_no_duplicates(self):
        # Signature: name(lst, error_func=None)
                # Check for duplicates in a sequence.
                #
                # This function checks that a list contains no duplicates, by casting the list
                # to a set and comparing the lengths.
                #
                # It raises an `NineMLRuntimeError` if the lengths are not equal.


        # Duplication
        self.assertRaises(
            NineMLRuntimeError,
            assert_no_duplicates, [1, 2, 3, 4, 4],
        )

        self.assertRaises(
            NineMLRuntimeError,
            assert_no_duplicates, ['1', '2', '3', '4', '4'],
        )

        assert_no_duplicates([1, 2, 3, 4])
        assert_no_duplicates(['1', '2', '3', '4'])

        assert_no_duplicates([None])
        assert_no_duplicates([True])
        assert_no_duplicates([()])


# Testing Skeleton for function:
class Testfile_sha1_hexdigest(unittest.TestCase):

    def test_file_sha1_hexdigest(self):
        # Signature: name(filename)
                # Returns the SHA1 hex-digest of a file
        # from nineml.utility import file_sha1_hexdigest
#         warnings.warn('Tests not implemented: sha1_hex_digest')
        pass


# Testing Skeleton for function:
class Testfilter_by_type(unittest.TestCase):

    def test_filter_by_type(self):
        # Signature: name(lst, acceptedtype)
                # Find all the objects of a certain type in a list
                #
                # This is a syntactic sugar function, which returns a list of all the
                # objects in a iterable for which  ``isinstance(o,acceptedtype) == True``

        # Good Case
        data = ['hello', 'world', 1, 2, 3, None]
        self.assertEqual(
            filter_by_type(data, basestring),
            ['hello', 'world']
        )
        self.assertEqual(
            filter_by_type(data, numbers.Number),
            [1, 2, 3]
        )

        # Slightly specical case for None:
        self.assertEqual(
            filter_by_type(data, types.NoneType),
            []
        )

        self.assertEqual(
            filter_by_type(data, types.BooleanType),
            []
        )


# Testing Skeleton for function:
class Testfilter_discrete_types(unittest.TestCase):

    def test_filter_discrete_types(self):
        # Signature: name(lst, acceptedtypes)
                # Creates a dictionary mapping types to objects of that type.
                #
                # Starting with a list of object, and a list of types, this returns a
                # dictionary mapping each type to a list of objects of that type.
                #
                # For example::
                #
                #     >>> import types
                # >>> filter_discrete_types( ['hello',1,2,'world'], ( basestring, types.IntType) ) #doctest: +NORMALIZE_WHITESPACE
                #     {<type 'basestring'>: ['hello', 'world'], <type 'int'>: [1, 2]}
                #
                #
                # The function checks that each object is mapped to exactly one type

        # Good Case:
        data = ['hello', 'world', 1, 2, 3]
        types_ = [basestring, numbers.Number, types.BooleanType]
        filtered = filter_discrete_types(data, types_)

        self.assertEqual(filtered[basestring], ['hello', 'world'])
        self.assertEqual(filtered[numbers.Number], [1, 2, 3])

        # Not all objects covered by listed classes:
        self.assertRaises(
            NineMLRuntimeError,
            filter_discrete_types, data, [basestring]
        )


# Testing Skeleton for function:
class Testrestore_sys_path(unittest.TestCase):

    def test_restore_sys_path(self):
        # Signature: name(func)
                # Decorator used to restore the sys.path
                # to the value it was before the function call.
                # This is useful for loading modules.

        original_path = sys.path[:]

        # Doesn't change
        @restore_sys_path
        def myfunc():
            sys.path.append('a')

        # Does change:
        def myfunc2():
            sys.path.append('a')

        # Lets Check:
        self.assertEqual(original_path, sys.path)
        myfunc()
        self.assertEqual(original_path, sys.path)
        myfunc2()
        self.assertNotEqual(original_path, sys.path)

        # Restore the orignal Path:
        sys.path = original_path


# Testing Skeleton for function:
class Testsafe_dict(unittest.TestCase):

    def test_safe_dict(self):
        # Signature: name(vals)
                # Create a dict, like dict(), but ensure no duplicate keys are given!
                # [Python silently allows dict( [(1:True),(1:None)] ) !!


        self.assertEqual(
            safe_dict([[1, 'One'], [2, 'Two']]),
            {1: 'One', 2: 'Two'}
        )
        self.assertEqual(
            safe_dict([[1, 'One'], [2, 'Two'], [3, 'Three'], [4, 'Four']]),
            {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four'}
        )

        self.assertRaises(
            NineMLRuntimeError,
            safe_dict,
            [[1, 'One'], [2, 'Two'], [3, 'Three'], [1, 'One'], [4, 'Four']]
        )


# Testing Skeleton for function:
class Testsafe_dictionary_merge(unittest.TestCase):

    def test_safe_dictionary_merge(self):
        # Signature: name(dictionaries)
                # Safely merge multiple dictionaries into one
                #
                # Merges an iterable of dictionaries into a new single dictionary,
                # checking that there are no key collisions
                #
                # >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three'} ] ) #doctest: +NORMALIZE_WHITESPACE
                # {1: 'One', 2: 'Two', 3: 'Three'}
                #
                # >>> safe_dictionary_merge( [ {1:'One',2:'Two'},{3:'Three',1:'One'} ] ) #doctest: +NORMALIZE_WHITESPACE +IGNORE_EXCEPTION_DETAIL +SKIP
                # NineMLRuntimeError: Key Collision while merging dictionarys

        self.assertEqual(
            safe_dictionary_merge([{1: 'One'}, {2: 'Two'}]),
            {1: 'One', 2: 'Two'}
        )
        self.assertEqual(
            safe_dictionary_merge([{1: 'One'}, {2: 'Two', 3: 'Three'}, {4: 'Four'}]),
            {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four'}
        )

        self.assertRaises(
            NineMLRuntimeError,
            safe_dictionary_merge,
            [{1: 'One'}, {2: 'Two', 3: 'Three', 1: 'One'}, {4: 'Four'}]
        )


# Testing Skeleton for function:
class Test_filter(unittest.TestCase):

    def test__filter(self):
        # Signature: name(lst, func=None)
                # Filter a list according to a predicate.
                #
                # Takes a sequence [o1,o2,..] and returns a list contains those which
                # are not `None` and satisfy the predicate `func(o)`
                #
                # :param lst: Input iterable
                # :param func: Predicate function. If ``none``, this function always returns ``True``
                #
                #
                # Implementation::
                #
                #     if func:
                #         return  [ l for l in lst if l is not None and func(l) ]
                #     else:
                #         return  [ l for l in lst if l is not None]
                #
                # Examples:
                #
                # >>> _filter( ['hello','world'] )         #doctest: +NORMALIZE_WHITESPACE
                # ['hello', 'world']
                #
                #
                # >>> _filter( ['hello',None,'world'] )    #doctest: +NORMALIZE_WHITESPACE
                # ['hello', 'world']
                #
                # >>> _filter( [None,] )                   #doctest: +NORMALIZE_WHITESPACE
                # []
        # from nineml.utility import _filter
#         warnings.warn('Tests not implemented: _filter')
        # raise NotImplementedError()
        pass
