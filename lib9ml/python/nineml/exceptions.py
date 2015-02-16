"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


class NineMLRuntimeError(Exception):
    pass


class NineMLMathParseError(ValueError):
    pass


class NineMLUnitMismatchError(ValueError):
    pass


class NineMLMissingElementError(KeyError):
    pass


def internal_error(s):
    assert False, 'INTERNAL ERROR:' + s


def raise_exception(exception=None):
    if exception:
        if isinstance(exception, basestring):
            raise NineMLRuntimeError(exception)
        else:
            raise exception
    else:
        raise NineMLRuntimeError()
