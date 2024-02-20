# -*- coding: utf-8 -*-

from typing import Callable

""" Constraint function, will be called with the parameter name and the value. """
F = Callable[[str, float], float]


def positive(param, val):
    """ Ensures parameter are positive """
    return max(0, val)


def negative(param, val):
    """ Ensure parameter are negative """
    return min(0, val)


def zero(param, val):
    """  A parameter is always 0 """
    return 0
