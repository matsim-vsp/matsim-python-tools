# -*- coding: utf-8 -*-

def positive_constraint(mode, val):
    """ Ensures parameter are positive """
    return max(0, val)


def negative_constraint(mode, val):
    """ Ensure parameter are negative """
    return min(0, val)
