# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

from matsim.calibration.group import Group, detect_binned_groups


def test_detect_dist_groups():
    groups = ["1000 - 2000", "2000+", "0 - 1000"]

    bins, labels = detect_binned_groups(groups)

    assert bins == [0, 1000, 2000, np.inf]
    assert labels == ["0 - 1000", "1000 - 2000", "2000+"]

    groups = ["1000 - 2000", "20000+", "0 - 1000", "2000 - 10000", "10000 - 20000"]

    bins, labels = detect_binned_groups(groups)

    assert bins == [0, 1000, 2000, 10000, 20000, np.inf]
    assert labels == ["0 - 1000", "1000 - 2000", "2000 - 10000", "10000 - 20000", "20000+"]


def test_groups_bins():
    g = Group("age", ["0 - 18", "18 - 66", "66+"])

    s = pd.Series([0, 17, 18, 65, 66, None, np.nan])

    assert list(g.categorize(s)) == ["0 - 18", "0 - 18", "18 - 66", "18 - 66", "66+", np.nan, np.nan]

    assert list(g.categorize(s.astype(str))) == ["0 - 18", "0 - 18", "18 - 66", "18 - 66", "66+", np.nan, np.nan]


def test_groups_values():
    g = Group("v", ["low", "medium", "high"])

    s = pd.Series(["low", "low", "medium", "high", "other", None, np.nan])

    assert list(g.categorize(s)) == ["low", "low", "medium", "high", np.nan, np.nan, np.nan]


def test_groups_split():
    g = Group("v", ["1,2", "4,5"])
    s = pd.Series(["1", "4", "5", "2", "3"])

    assert list(g.categorize(s)) == ["1,2", "4,5", "4,5", "1,2", np.nan]
