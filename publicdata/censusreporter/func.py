# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE
"""
Aggregations functions
"""

import numpy as np


def sum_rs(x):
    """Root square sum, for margins"""

    return np.sqrt(sum(x ** 2))


def mean_m(x):
    """Compute the mean of a margin"""

    a = None # np.sum(x.value) # ends up being unused
    a_m90 = sum_rs(x)

    b = len(x)
    b_m90 = 0 # ends up being unused

    # The product equation
    # np.sqrt(a ** 2 * b_m90 ** 2 + b ** 2 * a_m90 ** 2)

    # The product equation, with the zeros removed. I have no idea if this is the
    # correct formula ....

    return  np.sqrt( b ** 2 * a_m90 ** 2 )