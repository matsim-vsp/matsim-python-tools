#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

from typing import Any, Tuple

import geopandas
import numpy as np
import pandas as pd


def calc_adjusted_mode_share(sim: pd.DataFrame, survey: pd.DataFrame,
                             count_var: str = "trips", dist_var: str = "dist_group") -> Tuple[Any, pd.DataFrame]:
    """ This function can be used if the given input trip data has a different distance distribution than the survey data.
        It will rescale the survey data to match simulated data, which allows to calculate an adjusted overall mode share.

        :param sim: data frame containing shares for distance group and modes
        :param survey: data frame containing shares from survey data
        :param count_var: name of column containing the number of trips or share in 'sim'
        :param dist_var: name of the column holding the distance group information
        :return: tuple of optimization result and adjusted mode share
    """
    from scipy.optimize import minimize

    sagg = sim.groupby(dist_var).sum()
    sagg['share'] = sagg[count_var] / np.sum(sagg[count_var])

    # Rescale the distance groups of the survey data so that it matches the distance group distribution of the simulation
    # The overall mode share after this adjustment will the resulting adjusted mode share
    def f(x, result=False):
        adj = survey.copy()

        for i, t in enumerate(x):
            adj.loc[adj[dist_var] == sagg.index[i], "share"] *= t

        adj.share = adj.share / np.sum(adj.share)

        agg = adj.groupby(dist_var).sum()

        # Minimized difference between adjusted and simulated distribution
        err = sum((sagg.share - agg.share)**2)

        if result:
            return adj

        return err

    # One variable for each distance group
    x0 = np.ones(len(sagg.index)) / len(sagg.index)

    # Sum should be less than one
    cons = [{'type': 'ineq', 'fun': lambda x:  1 - sum(x)}]
    bnds = tuple((0, 1) for x in x0)

    res = minimize(f, x0, method='SLSQP', bounds=bnds, constraints=cons)

    df = f(res.x, True)

    return res, df


def read_trips_and_persons(run, transform_persons=None, transform_trips=None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """ Read trips and persons from run directory """

    # Return input as output
    # This allows to re-use input for the calc functions
    if type(run) is tuple and len(run) == 2:
        return run

    trips = glob.glob(run.rstrip("/") + "/*.output_trips.csv.gz")[0]
    persons = glob.glob(run.rstrip("/") + "/*.output_persons.csv.gz")[0]


    df = pd.read_csv(trips, sep=None, dtype={"person": "str"}, low_memory=False)
    dfp = pd.read_csv(persons, sep=None, dtype={"person": "str"}, low_memory=False)

    gdf = geopandas.GeoDataFrame(dfp,
            geometry=geopandas.points_from_xy(dfp.first_act_x, dfp.first_act_y)
    )

    if transform_persons is not None:
        gdf = transform_persons(gdf)

    df = pd.merge(df, gdf, how="inner", left_on="person", right_on="person")

    nans = df.main_mode.isnull()

    # use longest distance mode if there is no main mode
    df.loc[nans, "main_mode"] = df.loc[nans, "longest_distance_mode"]

    if transform_trips is not None:
        df = transform_trips(df)

    return df, gdf

def read_leg_stats(run : str, transform_persons=None, transform_legs=None):
    """ Reads leg statistic from run directory """

    legs = glob.glob(run.rstrip("/") + "/*.output_trips.csv.gz")[0]
    persons = glob.glob(run.rstrip("/") + "/*.output_persons.csv.gz")[0]

    df = pd.read_csv(legs, sep=";")
    dfp = pd.read_csv(persons, sep=";", index_col=0)

    gdf = geopandas.GeoDataFrame(dfp,
            geometry=geopandas.points_from_xy(dfp.first_act_x, dfp.first_act_y)
    )

    if transform_persons is not None:
        gdf = transform_persons(gdf)

    if transform_legs is not None:
        df = transform_legs(df)

    return df

def calc_mode_share(run, transform_persons=None, transform_trips=None):
    """ Calculates the mode share from output directory """
    df, _ = read_trips_and_persons(run, transform_persons, transform_trips)

    return df.groupby("main_mode").count()["trip_number"] / len(df)

def calc_mode_stats(run, attrs=[],
                    dist_bins = [0, 1000, 2000, 5000, 10000, 20000, np.inf],
                    dist_labels = ["0 - 1000", "1000 - 2000", "2000 - 5000", "5000 - 10000", "10000 - 20000", "20000+"],
                    transform_persons=None, transform_trips=None) -> pd.DataFrame:
    """ Calculate detailed mode statistics """

    trips, _ = read_trips_and_persons(run, transform_persons, transform_trips)
    trips["dist_group"] = pd.cut(trips.traveled_distance, dist_bins, labels=dist_labels, right=False)

    def aggr(x):
        data = dict(n=len(x), mean_dist=np.average(x.traveled_distance))
        return pd.Series(data=data)

    aggr = trips.groupby(attrs + ["dist_group", "main_mode"], observed=True).apply(aggr)

    aggr["n"] = aggr["n"].fillna(0)

    aggr["share"] = aggr.n / aggr.n.sum()
    aggr["share"] = aggr["share"].fillna(0)

    return aggr


def calc_population_stats(run, attrs=[], transform_persons=None, transform_trips=None) -> pd.DataFrame:
    """ Calculate population statistics """

    trips, persons = read_trips_and_persons(run, transform_persons, transform_trips)

    def mode_usage(mode):
        def f(x):
            return (x == mode).any()
        return f

    n_trips = trips.groupby("person").agg(n_trips=("trip_number", "max"))

    persons = persons.join(n_trips, on="person")
    persons.n_trips.fillna(0, inplace=True)

    def summarize(x):

        total = len(x)
        total_mobile = (x.n_trips > 0).sum()

        mobile = total_mobile / total

        args = {"%s_user" % k: ("main_mode", mode_usage(k)) for k in set(trips.main_mode)}

        p_trips = trips[trips.person.isin(x.person)]

        mode_user = p_trips.groupby(["person"]).agg(**args)
        joined = x.join(mode_user, on="person", how="inner")

        data = {}
        for c in mode_user.columns:
            share = joined[c].sum() / total_mobile
            data[c] = share

        data.update({"mobile": mobile, "n": len(x), "avg_trips": np.average(x.n_trips)})

        return pd.Series(data=data)

    if attrs:
        aggr = persons.groupby(attrs).apply(summarize)
    else:
        aggr = summarize(persons)
        aggr = aggr.to_frame(0).T

    aggr["population_share"] = aggr.n / aggr.n.sum()

    return aggr

if __name__ == "__main__":

    def prepare_persons(df):
        df["age_group"] = pd.cut(df.age, [0, 18, 66, np.inf], labels=["0 - 17", "18 - 65", "65+"], right=False)
        return df

    #df = calc_mode_stats("/Users/rakow/Volumes/math-cluster/matsim-kelheim/calibration-v3/runs/010", attrs=["age_group"], transform_persons=prepare_persons)
    #print(df)

    df = calc_population_stats("/Users/rakow/Volumes/math-cluster/matsim-kelheim/calibration-v3/runs/010", attrs=["age_group"], transform_persons=prepare_persons)
    print(df)