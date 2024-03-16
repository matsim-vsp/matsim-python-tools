# -*- coding: utf-8 -*-
# Contains grouped calibration related functions

from typing import Sequence, Iterable, Tuple

import numpy as np
import pandas as pd


def detect_binned_groups(s: Iterable[str]) -> Tuple[Sequence, Sequence]:
    """ Detect dist bins and labels from existing groups"""
    bins = set()
    s = set(s)

    for label in s:
        if "-" in label:
            a, b = label.split("-")
            bins.add(int(a))
            bins.add(int(b))
        elif "+" in label:
            a = int(label[:-1])
            bins.add(a)
            bins.add(np.Inf)

    bins = sorted(list(bins))

    # Same function as in preparation.py, not imported to avoid dependency
    res = ["%.0f - %.0f" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]
    if bins[-1] == np.inf:
        res[-1] = "%.0f+" % bins[-2]

    # Check if all groups are present
    for r in res:
        if r not in s:
            raise ValueError("Missing group %s" % r)

    return bins, res


def parse_group(p):
    p = p.strip("[]")
    return {x.split("=")[0]: x.split("=")[1] for x in p.split(",")}


class Group:
    """ Represents one group of attributes"""

    bins = None
    mapping = None

    def __init__(self, name, values):
        self.name = name
        self.values = set(v for v in values if not pd.isna(v))

        if all("-" in v or "+" in v for v in self.values):
            self.bins = detect_binned_groups(self.values)

        self.mapping = {k: k for k in self.values}

        # Support split entries
        for v in self.values:
            if "," in v:
                split = v.split(",")
                for s in split:
                    self.mapping[s.strip()] = v

    def __repr__(self):
        return f"Group({self.name}, {self.values}, bins={bool(self.bins)})"

    def categorize(self, series: pd.Series) -> pd.Series:

        # TODO: mapping with dtypes that could be valid float, int or str at the same time can cause problems.

        if self.bins:
            if not pd.api.types.is_numeric_dtype(series):
                series = pd.to_numeric(series, errors="coerce")

            return pd.cut(series, bins=self.bins[0], labels=self.bins[1], right=False)

        return series.map(self.mapping)
