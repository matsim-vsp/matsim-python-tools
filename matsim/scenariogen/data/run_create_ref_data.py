#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Sequence, SupportsFloat

import numpy as np
import pandas as pd

from . import *
from .preparation import cut

METADATA = "data-create-ref", "Extract and create reference data from surveys."


class InvalidHandling(Enum):
    """ How to handle invalid trips. """
    # Invalid trips are ignored
    KEEP = auto()
    # Drop single invalid trips
    REMOVE_TRIPS = auto()
    # Drop whole person if any trip is invalid
    REMOVE_PERSONS = auto()


@dataclass
class AggregationResult:
    """ Return value of create function. """

    persons: pd.DataFrame
    trips: pd.DataFrame
    share: pd.DataFrame

    groups: pd.DataFrame = None


def weighted(x):
    data = dict(n=x.t_weight.sum())
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


def grouped_share(df, groups, normalize=True):
    """ Compute share of each group. """

    aggr = df.groupby(groups).apply(weighted)
    aggr["share"] = aggr.n / aggr.n.sum()
    aggr["share"].fillna(0, inplace=True)
    aggr.drop(columns=["n"], inplace=True)

    # Normalize per group
    if normalize:
        for group in set(aggr.index.get_level_values(0)):
            sub = aggr.loc[group, :]
            sub.share /= sub.share.sum()

    return aggr


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


def default_person_filter(df):
    """ Default person filter for reference data. """
    return df[df.present_on_day & (df.reporting_day <= 4)]


def create(survey_dirs, transform_persons, transform_trips,
           invalid_trip_handling: InvalidHandling = InvalidHandling.REMOVE_TRIPS,
           dist_groups: Sequence[SupportsFloat] = None,
           ref_groups: List[str] = None,
           output_prefix="") -> AggregationResult:
    """ Create reference data from survey data.
    :param survey_dirs: Directories with survey data
    :param transform_persons: Function to transform person data frame
    :param transform_trips: Function to transform trip data frame
    :param invalid_trip_handling: How to handle invalid trips
    :param dist_groups: distance group bins in meters
    :param ref_groups: Create reference data for these attribute groups
    :param output_prefix: prefix for the ouput files
    :return:
    """

    if dist_groups is None:
        dist_groups = [0, 1000, 2000, 5000, 10000, 20000, np.inf]

    all_hh, all_persons, all_trips = read_all(survey_dirs)

    # Filter person ad trips for area
    df = all_persons.join(all_hh, on="hh_id")

    persons = transform_persons(df) if transform_persons is not None else df

    if invalid_trip_handling == InvalidHandling.REMOVE_PERSONS:
        # Filter persons, if they have at least one invalid trip
        invalid = set(all_trips[~all_trips.valid].p_id)
        persons = persons[~persons.index.isin(invalid)]
    elif invalid_trip_handling == InvalidHandling.REMOVE_TRIPS:
        # Use only valid trips
        all_trips = all_trips[all_trips.valid]

    # Because of inner join, trips might be filtered if person was removed
    trips = all_trips.drop(columns=["hh_id"]).join(persons, on="p_id", how="inner")

    # Transform existing trips
    trips = transform_trips(trips) if transform_trips is not None else trips

    # Set dist groups
    trips["dist_group"] = cut(trips.gis_length * 1000, dist_groups)

    aggr = trips.groupby(["dist_group", "main_mode"]).apply(weighted)

    aggr["share"] = aggr.n / aggr.n.sum()
    aggr["share"].fillna(0, inplace=True)

    share = aggr.drop(columns=["n"])
    aggr = share.copy()

    aggr.to_csv(output_prefix + "mode_share_ref.csv")

    # Also normalize per distance group
    for dist_group in aggr.index.get_level_values(0).categories:
        sub = aggr.loc[dist_group, :]
        sub.share /= sub.share.sum()

    aggr.to_csv(output_prefix + "mode_share_per_dist_ref.csv")

    aggr = summarize_purposes(trips)

    aggr.to_csv(output_prefix + "trip_purposes_by_hour_ref.csv")

    aggr = summarize_mode_usage(persons, trips)
    aggr.to_csv(output_prefix + "mode_users_ref.csv")

    groups = None
    if ref_groups:

        overall = share.groupby("main_mode").sum().reset_index()

        # Include total share in reference data
        groups = [overall]
        dist = [grouped_share(trips, ["dist_group", "main_mode"], normalize=False).reset_index()]

        for g in ref_groups:

            if g not in persons.columns:
                raise ValueError("Column %s not found in persons" % g)

            aggr = grouped_share(trips, [g, "main_mode"])
            groups.append(aggr.reset_index())

            aggr = grouped_share(trips, [g, "dist_group", "main_mode"], normalize=False)
            dist.append(aggr.reset_index())

        groups = pd.concat(groups, sort=False)
        # Reorder columns
        groups = groups[ref_groups + ["main_mode", "share"]]
        groups.to_csv(output_prefix + "mode_share_per_group_ref.csv", index=False)

        dist = pd.concat(dist, sort=False)
        dist = dist[ref_groups + ["dist_group", "main_mode", "share"]]
        dist.to_csv(output_prefix + "mode_share_per_group_dist_ref.csv", index=False)

    return AggregationResult(persons, trips, share.groupby("main_mode").sum(), groups=groups)


def main(args):
    create(args.dirs, default_person_filter)
