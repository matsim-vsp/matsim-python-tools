#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import numpy as np
import pandas as pd

from . import *
from .io import read_all_srv
from .preparation import _fill

METADATA = "data-create-ref", "Extract and create reference data from surveys."


def weighted(x):
    data = dict(n=x.t_weight.sum(), mean_dist=np.average(x.gis_length * 1000, weights=x.t_weight))
    return pd.Series(data=data)


def summarize_purposes(x):
    x["departure_h"] = x.departure // 60
    x["arrival_h"] = (x.departure + x.duration) // 60

    d = x.groupby(["purpose", "departure_h"]).agg(n=("t_weight", "sum"))
    d["departure"] = d.n / d.n.sum()
    d = d.drop(columns=["n"])
    d.index.rename(names=["purpose", "h"], inplace=True)

    a = x.groupby(["purpose", "arrival_h"]).agg(n=("t_weight", "sum"))
    a["arrival"] = a.n / a.n.sum()
    a = a.drop(columns=["n"]).rename(index={"arrival_h": "h"})
    a.index.rename(names=["purpose", "h"], inplace=True)

    m = pd.merge(a, d, left_index=True, right_index=True, how="outer")
    m.fillna(0, inplace=True)

    return m


def mode_usage(mode):
    def f(x):
        return (x == mode).any()

    return f


def summarize_mode_usage(x, trips):
    total_mobile = x[x.mobile_on_day].p_weight.sum()

    args = {k.value: ("main_mode", mode_usage(k)) for k in set(trips.main_mode)}

    p_trips = trips[trips.p_id.isin(x.index)]

    mode_user = p_trips.groupby(["p_id"]).agg(**args)
    joined = x.join(mode_user, how="inner")

    data = {}
    for c in mode_user.columns:
        share = joined[joined[c]].p_weight.sum() / total_mobile
        data[c] = share

    return pd.DataFrame(data={"main_mode": data.keys(), "user": data.values()}).set_index("main_mode")


def setup(parser: argparse.ArgumentParser):
    parser.add_argument("dirs", nargs="+", help="Directories with survey data")


def main(args):
    all_hh, all_persons, all_trips = read_all_srv(args.dirs)

    # Filter person ad trips for area
    df = all_persons.join(all_hh, on="hh_id")

    # TODO: configurable filter
    persons = df[df.present_on_day &
                 (df.reporting_day <= 4) &
                 (df.region_type == 1)]

    # TODO: configurable attributes
    persons["age_group"] = pd.cut(persons.age, [0, 18, 66, np.inf], labels=["0 - 17", "18 - 65", "65+"], right=False)

    invalid = set(all_trips[~all_trips.valid].p_id)

    persons = persons[~persons.index.isin(invalid)]

    trips = all_trips.drop(columns=["hh_id"]).join(persons, on="p_id", how="inner")

    _fill(trips, "main_mode", TripMode.OTHER)

    # TODO: configurable dist binds
    labels = ["0 - 1000", "1000 - 2000", "2000 - 5000", "5000 - 10000", "10000 - 20000", "20000+"]
    bins = [0, 1000, 2000, 5000, 10000, 20000, np.inf]

    trips["dist_group"] = pd.cut(trips.gis_length * 1000, bins, labels=labels, right=False)

    aggr = trips.groupby(["dist_group", "main_mode"]).apply(weighted)

    aggr["share"] = aggr.n / aggr.n.sum()
    aggr["share"].fillna(0, inplace=True)

    aggr = aggr.drop(columns=["n"])

    # TODO: configurable output

    aggr.to_csv("mode_share_ref.csv")

    # Also normalize der distance group
    for dist_group in aggr.index.get_level_values(0).categories:
        sub = aggr.loc[dist_group, :]
        sub.share /= sub.share.sum()

    aggr.to_csv("mode_share_per_dist_ref.csv")

    aggr = summarize_purposes(trips)

    aggr.to_csv("trip_purposes_by_hour_ref.csv")

    aggr = summarize_mode_usage(persons, trips)
    aggr.to_csv("mode_users_ref.csv")

    # TODO: ref data per attribute ?
