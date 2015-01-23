"""
This module defines the namespace of functions and symbols available to 9ML
expressions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


import re
import numpy
from ...exceptions import NineMLMathParseError


_constants = set(['pi'])

_functions = set(['exp', 'sin', 'cos', 'log', 'log10', 'pow',
                  'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
                  'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2',
                  'uniform', 'binomial', 'poisson', 'exponential'])

_reserved_symbols = set(['t'])


math_namespace_separator = '.'

# Specific Namespace:
_random_namespace = {
    'randn': numpy.random.randn,
    'randint': numpy.random.randint,

    # Taken from numpy documentations:
    # http://docs.scipy.org/doc/numpy/reference/routines.random.html

    'binomial': numpy.random.binomial,  # binomial(n, p)
    'chisquare': numpy.random.chisquare,  # chisquare(df)
    'mtrand.dirichlet': numpy.random.mtrand.dirichlet,  # mtrand.dirichlet(alpha) @IgnorePep8
    'exponential': numpy.random.exponential,  # exponential(dfnum, dfden)
    'f': numpy.random.f,  # f(dfnum, dfden)
    'gamma': numpy.random.gamma,  # gamma(shape)
    'geometric': numpy.random.geometric,  # geometric(p)
    'hypergeometric': numpy.random.hypergeometric,  # hypergeometric(ngood, nbad, nsample) @IgnorePep8
    'laplace': numpy.random.laplace,  # laplace()
    'logistic': numpy.random.logistic,  # logistic()
    'lognormal': numpy.random.lognormal,  # lognormal()
    'logseries': numpy.random.logseries,  # logseries(p)
    'negative_binomial': numpy.random.negative_binomial,  # negative_binomial(n, p) @IgnorePep8
    'noncentral_chisquare': numpy.random.noncentral_chisquare,  # noncentral_chisquare(df, nonc) @IgnorePep8
    'noncentral_f': numpy.random.noncentral_f,  # noncentral_f(dfnum, dfden, nonc) @IgnorePep8
    'normal': numpy.random.normal,  # normal()
    'pareto': numpy.random.pareto,  # pareto(a)
    'poisson': numpy.random.poisson,  # poisson()
    'power': numpy.random.power,  # power(a)
    'rayleigh': numpy.random.rayleigh,  # rayleigh()
    'standard_cauchy': numpy.random.standard_cauchy,  # standard_cauchy()
    'standard_exponential': numpy.random.standard_exponential,  # standard_exponential() @IgnorePep8
    'standard_gamma': numpy.random.standard_gamma,  # standard_gamma(shape)
    'standard_normal': numpy.random.standard_normal,  # standard_normal()
    'standard_t': numpy.random.standard_t,  # standard_t(df)
    'triangular': numpy.random.triangular,  # triangular(left, mode, right)
    'uniform': numpy.random.uniform,  # uniform()
    'vonmises': numpy.random.vonmises,  # vonmises(mu, kappa)
    'wald': numpy.random.wald,  # wald(mean, scale)
    'weibull': numpy.random.weibull,  # weibull(a)
    'zipf': numpy.random.zipf,  # zipf(a)

}

_math_namespaces = {
    'random': _random_namespace
}


def is_builtin_math_constant(constname):
    assert isinstance(constname, basestring)
    return constname in _constants


def is_builtin_math_function(funcname):
    assert isinstance(funcname, basestring)

    # Is it a standard mathematical function (cos,sin,etc)
    if funcname in _functions:
        return True

    # Is it a namespace:
    if math_namespace_separator in funcname:
        namespace, func = funcname.split(math_namespace_separator)
        if namespace not in _math_namespaces:
            err = 'Unrecognised math namespace: %s' % namespace
            raise NineMLMathParseError(err)
        if func not in _math_namespaces[namespace]:
            err = ('Unrecognised function in namespace: %s %s' %
                   (namespace, func))
            raise NineMLMathParseError(err)
        return True

    # OK then, it is not built in.
    return False


def is_builtin_symbol(s):
    return is_builtin_math_constant(s) or is_builtin_math_function(s)


def get_builtin_symbols():

    builtins = _constants | _functions
    for ns_name in _math_namespaces:
        for func in _math_namespaces[ns_name]:
            builtins.add('%s%s%s' % (ns_name,
                                     math_namespace_separator,
                                     func))
    return builtins


def is_reserved(s):
    return s in _reserved_symbols


def is_valid_lhs_target(sym):
    return not(is_builtin_symbol(sym) or is_reserved(sym))


def get_reserved_and_builtin_symbols():
    return get_builtin_symbols() | _reserved_symbols


str_to_npfunc_map = {
    "exp": numpy.exp,
    "sqrt": numpy.sqrt,
    "sin": numpy.sin,
    "cos": numpy.cos,
    "atan2": numpy.arctan2,
    "log": numpy.log,
    "pi": numpy.pi,
    "e": numpy.e
}


def func_namespace_split(func_name):
    """Converts function names from
    'namespace.func'
    to
    'namespace','func'
    or None,'func' if it is not in a namespace
    """
    if math_namespace_separator not in func_name:
        return None, func_name

    toks = func_name.split(math_namespace_separator)
    if not len(toks) == 2:
        raise NineMLMathParseError('Invalid Namespace: %s' % toks)

    return toks


class MathUtil(object):

    """Useful static methods for manipulating expressions that are string"""

    @classmethod
    def str_expr_replacement(cls, frm, to, expr_string, func_ok=False):
        """ replaces all occurences of name 'frm' with 'to' in expr_string
        ('frm' may not occur as a function name on the rhs) ...
        'to' can be an arbitrary string so this function can also be used for
        argument substitution.

        This function *will* substitute standard builtin symbols, for example
        ``e`` and ``sin``.

        Returns the resulting string. """

        # Escape the original string, so we can handle special
        # characters.
        frm = re.escape(frm)

        # do replace using regex this matches names, using lookahead and
        # lookbehind to be sure we don't match for example 'xp' in name 'exp'
        # ...
        if func_ok:
            # func_ok indicates we may replace a function name
            p_func = re.compile(r"(?<![a-zA-Z_0-9])(%s)(?![a-zA-Z_0-9])" % frm)
        else:
            # this will not replace a function name even if its name matches
            # from due to the lookahead disallowing '('
            p_func = re.compile(r"(?<![a-zA-Z_0-9])(%s)(?![(a-zA-Z_0-9])" %
                                frm)
        return p_func.sub(to, expr_string)

    @classmethod
    def rename_function(cls, expr, orig_func_name, new_func_expr):
        """ This method allows us to subsitute function call names, and
        rearrange parameters
        For example, for neuron, we want to  remap
        randn(x,y) to normrand(x,y)

        in this case:

        orig_func_name = 'randn'
        new_func_expr = 'norm_rand(\\1,\\2)'

        """
        # \w = [a-zA-Z0-9_]

        regex = (r"""%s\( ([^,) ]*) \s* (?: , \s* ([^, )]*) )* \s* \)""" %
                 orig_func_name)
        r = re.compile(regex, re.VERBOSE)
        new_expr = r.sub(new_func_expr, expr)

        return new_expr

    @classmethod
    def get_rhs_substituted(cls, expr_obj, namemap):
        expr = expr_obj.rhs
        for frm, to in namemap.iteritems():
            expr = MathUtil.str_expr_replacement(frm, to, expr, func_ok=False)
        return expr

    @classmethod
    def get_prefixed_rhs_string(cls, expr_obj, prefix="", exclude=None):
        """
        Prefixes variable names in a string. This will not toouch math-builtins
        such as ``pi`` and ``sin``, (i.e. neither standard constants not
        variables)
        """

        expr = expr_obj.rhs
        for name in expr_obj.rhs_names:
            if exclude and name in exclude:
                continue
            expr = MathUtil.str_expr_replacement(name, prefix + name, expr)
        for func in expr_obj.rhs_funcs:
            if not is_builtin_symbol(func):
                expr = MathUtil.str_expr_replacement(func,
                                                     prefix + func,
                                                     expr,
                                                     func_ok=True)
        return expr

    @classmethod
    def is_single_symbol(cls, expr):
        """Returns ``True`` if the expression is a single symbol, possibly
        surrounded with white-spaces

        >>> is_single_symbol('hello')
        True

        >>> is_single_symbol('hello * world')
        False

        """

        expr = expr.strip()
        single_symbol = re.compile("^[a-zA-Z_]+[a-zA-Z_0-9]*$")
        m = single_symbol.match(expr)
        return m is not None
