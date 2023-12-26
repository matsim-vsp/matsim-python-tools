#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.utils import shuffle

from . import *


def prepare_persons(hh, pp, tt, augment=5, max_hh_size=5, core_weekday=False, remove_with_invalid_trips=False):
    """ Cleans common data errors and fill missing values """
    df = pp.join(hh, on="hh_id", lsuffix="hh_")

    # Augment data using p_weight
    if augment > 1:
        df = augment_persons(df, augment)
        df = shuffle(df, random_state=0).reset_index(drop=True)

    # set car avail
    df.loc[df.age < 17, "driving_license"] = Availability.NO
    _fill(df, "driving_license", Availability.UNKNOWN)

    df["car_avail"] = (df.n_cars > 0) & (df.driving_license == Availability.YES)
    df["bike_avail"] = (df.n_bikes > 0) | (df.bike_avail == Availability.YES)

    # small children don't have pt abo
    df.loc[df.age < 6, "pt_abo_avail"] = Availability.NO
    _fill(df, "pt_abo_avail", Availability.UNKNOWN)

    # Replace unknown income group
    _fill(df, "economic_status", EconomicStatus.UNKNOWN)

    # Large households are underrepresented and capped
    df.n_persons = np.minimum(df.n_persons, max_hh_size)

    if core_weekday:
        df = df[df.reporting_day <= 4]

    if remove_with_invalid_trips:
        invalid = set(tt[~tt.valid].p_id)
        df = df[~df.p_id.isin(invalid)]

        mobile = set(tt[tt.valid].p_id)

        # Filter persons that are supposed to be mobile but have no trips
        df = df[(df.p_id.isin(mobile) | (~df.mobile_on_day))]

    df = df.drop(columns=['hh_id', 'present_on_day', 'reporting_day', 'location', 'h_weight',
                          'n_cars', 'n_bikes', 'n_other_vehicles', 'car_parking'])

    # Move the region type variable to the front because it is used as conditional
    df.insert(3, 'region_type', df.pop('region_type'))

    # Regions other than 1 and 3 are massively under-represented
    # Regions are reduced to 1 (Berlin) and 3 (Outside Berlin)
    df.loc[df.region_type != 1, "region_type"] = 3

    # Maximum age is 99, also to be able to encode age with two tokens
    df.loc[df.age >= 99, "age"] = 99

    return df

def bins_to_labels(bins):
    """ Convert bins to labels """
    res =  ["%.0f - %.0f" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]

    if bins[-1] == np.inf:
        res[-1] = "%.0f+" % bins[-2]

    return res

def cut(x, bins):
    """ Cut x into bind and return labels """
    return pd.cut(x, bins, labels=bins_to_labels(bins), right=False)

def augment_persons(pp, factor=1, permute_age=0.5):
    """ Augment persons using p weight

    :param pp Person table
    :param factor multiply weight by this factor
    :param permute_age if larger 0 add gaussian noise to the age with parameter as scale
    """
    pp = pp.reset_index()

    duplicated = pp.loc[pp.index.repeat(np.maximum(1, np.rint(pp.p_weight * factor)))]

    if permute_age > 0:
        np.random.seed(0)

        age_permute = np.rint(np.random.normal(0, permute_age, len(duplicated))).astype(np.int32)
        duplicated.age += age_permute

        # 0 age is minimum
        duplicated.age = np.maximum(0, duplicated.age)

    # Filter invalid options
    return duplicated[check_age_employment(None, duplicated)]


def prepare_trips(pp, trips, core_weekday=True):
    """ Create trip data frame """

    df = trips.join(pp, on="p_id")

    # remove person if any trip is invalid
    invalid = set(trips[~trips.valid].p_id)
    df = df[~df.p_id.isin(invalid)]

    df = df.drop(columns=["t_weight", "sd_group", "mobile_on_day", "valid"])

    if core_weekday:
        # Monday - Thursday
        df = df[df.day_of_week <= 4]
        df = df.drop(columns=["day_of_week"])

    # reverse columns so activities are at the end
    return df[df.columns[::-1]]


def _fill(df, col, val=None):
    """ Fill null values with dist of the rest (or replace val)"""
    if val is not None:
        df.loc[df[col] == val, col] = None

    isnull = df[col].isnull()
    sample = df[col].dropna().sample(isnull.sum(), replace=True).values
    df.loc[isnull, col] = sample


def create_activities(all_persons: pd.DataFrame, tt: pd.DataFrame, core_weekday=True, cut_groups=True,
                      include_person_context=True):
    """ Create activity representation from trip table """

    tt = tt.reset_index().set_index("p_id")

    import multiprocess as mp

    def convert(persons):
        res = []

        for p in persons.itertuples():

            acts = []
            valid = True

            # Filter if not done yet
            if "present_on_day" in persons.keys() and not p.present_on_day:
                continue

            p_id = p.p_id if "p_id" in persons.keys() else p.Index

            try:
                #            trips = tt[tt.p_id == p_id]
                trips = tt.loc[[p_id]]
            except KeyError:
                # Empty dataframe of same type
                trips = tt.iloc[:0, :].copy()

            if (~trips.valid).any():
                continue

            if core_weekday:
                # Monday - Thursday
                if (trips.day_of_week > 4).any():
                    continue

            # id generator
            def a_id(t_i):
                return "%s_%d" % (p.Index, t_i)

            if len(trips) == 0:
                acts.append(Activity(a_id(0), p.Index, 0, Purpose.HOME, 1440, 0, 0, TripMode.OTHER))
            else:
                acts.append(
                    Activity(a_id(0), p.Index, 0, trips.iloc[0].sd_group.source(), trips.iloc[0].departure, 0, 0,
                             TripMode.OTHER))

            for i in range(len(trips) - 1):
                t0 = trips.iloc[i]
                t1 = trips.iloc[i + 1]

                duration = t1.departure - t0.departure - t0.duration

                if duration < 0 or t0.gis_length < 0:
                    valid = False

                acts.append(Activity(a_id(i + 1), p.Index, i + 1, t0.purpose,
                                     duration, t0.gis_length, t0.duration, t0.main_mode))

            if len(trips) > 1:
                i += 1
                # last trip
                tl = trips.iloc[i]

                if tl.gis_length < 0:
                    valid = False

                # Duration is set to rest of day
                acts.append(
                    Activity(a_id(i + 1), p.Index, i + 1, tl.purpose, 1440, tl.gis_length, tl.duration, tl.main_mode))

            if valid:
                res.extend(acts)

        return res

    with mp.Pool(8) as pool:
        docs = pool.map(convert, np.array_split(all_persons, 16))
        result = functools.reduce(lambda a, b: a + b, docs)

    activities = pd.DataFrame(result).set_index("a_id")
    # Reverse columns because it will be reversed again at the end
    activities = activities.iloc[:, ::-1]
    persons = all_persons.iloc[:, ::-1].drop(columns=["p_id"], errors="ignore")

    if include_person_context:
        df = activities.join(persons, on="p_id", rsuffix="_p")
    else:
        df = activities

    df = df.drop(columns=["mobile_on_day", "p_weight", "hh_id", "present_on_day"], errors="ignore")

    # TODO: permute length and dist

    if cut_groups:
        df.duration = DurationGroup.cut(df.duration)
        df.leg_dist = DistanceGroup.cut(df.leg_dist)

    # reverse columns so activities are at the end
    return df.iloc[:, ::-1]


def check_age_employment(column_names, df):
    """ Check if age vs. employment status is valid"""

    invalid = (df.employment == Employment.CHILD) & (df.age > 7)
    invalid |= (df.employment == Employment.RETIREE) & (df.age < 30)
    invalid |= (df.employment == Employment.STUDENT) & ((df.age < 17) | (df.age > 55))
    invalid |= (df.employment == Employment.SCHOOL) & ((df.age < 5) | (df.age > 25))
    invalid |= (df.employment == Employment.UNEMPLOYED) & ((df.age < 17) | (df.age > 66))
    invalid |= (df.employment == Employment.JOB_PART_TIME) & (df.age < 18)
    invalid |= (df.employment == Employment.JOB_FULL_TIME) & (df.age < 18)
    invalid |= (df.employment == Employment.HOMEMAKER) & (df.age < 18)
    invalid |= (df.employment == Employment.TRAINEE) & (df.age < 16)

    return ~invalid


def check_age_license(column_names, df):
    """ Check driving license and age is valid """

    invalid = (df.driving_license == Availability.YES) & (df.age < 17)
    invalid |= df.car_avail & (df.age < 17)

    return ~invalid


def check_positive(column_names, df):
    """ Check for plausible number of vehicles"""

    invalid = (df.n_persons <= 0)
    #  invalid |= (df.n_cars < 0)
    #  invalid |= (df.n_bikes < 0)
    #  invalid |= (df.n_other_vehicles < 0)

    invalid |= (df.n_persons <= 1) & (df["type"] != HouseholdType.SINGLE)

    return ~invalid


def calc_commute(pp, tt):
    """ Calculate commute distances """

    work = tt[tt.valid &
              ((tt.sd_group == SourceDestinationGroup.HOME_WORK) | (tt.sd_group == SourceDestinationGroup.WORK_HOME))]

    edu = tt[tt.valid &
             ((tt.sd_group == SourceDestinationGroup.HOME_EDU) | (tt.sd_group == SourceDestinationGroup.EDU_HOME))]

    # t_weight is always the same for one person
    return work.groupby("p_id").agg(commute_dist=("gis_length", "mean"), weight=("t_weight", "max")), \
        edu.groupby("p_id").agg(commute_dist=("gis_length", "mean"), weight=("t_weight", "max"))


def calc_needed_short_distance_trips(ref_trips: pd.DataFrame, sim_trips: pd.DataFrame, max_dist=1000) -> Tuple[float, int]:
    """ Calculate number of short distance trips needed to add to match required share """

    target_share = float(ref_trips[ref_trips.gis_length < (max_dist / 1000)].t_weight.sum() / ref_trips.t_weight.sum())

    short_trips = sim_trips[sim_trips.traveled_distance < max_dist]

    current_share = len(short_trips) / len(sim_trips)
    num_trips = (len(short_trips) - len(sim_trips) * target_share) / (target_share - 1)

    return target_share, num_trips