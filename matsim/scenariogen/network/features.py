#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path

import pandas as pd


def build_datasets(network, inter, routes, model_type):
    """ Build all datasets needed for training models"""
    ft = pd.read_csv(network)

    df_i = pd.concat([pd.merge(pd.read_csv(i), ft, left_on="fromEdgeId", right_on="linkId") for i in inter])
    df_r = pd.concat(
        [pd.merge(pd.read_csv(r).drop(columns=["speed"]), ft, left_on="edgeId", right_on="linkId") for r in routes])

    result = {}

    aggr = df_r.groupby(["junction_type"])
    for g in aggr.groups:
        if str(g) == "dead_end":
            continue

        result["speedRelative_" + str(g)] = prepare_dataframe(aggr.get_group(g), model_type, target="speedRelative")

    aggr = df_i.groupby(["junction_type"])
    df_i["norm_cap"] = df_i.capacity / df_i.num_lanes
    for g in aggr.groups:
        result["capacity_" + str(g)] = prepare_dataframe(aggr.get_group(g), model_type, target="norm_cap")

    return result


def prepare_dataframe(df, model_type, target):
    """ Simple preprocessing """

    df = df.rename(columns={target: "target"})

    # Drop length outliers
    df = df[df.length < 500]

    # drop 2.5% smallest and largest
    drop = len(df) // 40
    df = df.drop(df.nsmallest(drop, ["target"]).index)
    df = df.drop(df.nlargest(drop, ["target"]).index)

    s = df['target']
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    iqr_lower = q1 - 1.5 * iqr
    iqr_upper = q3 + 1.5 * iqr
    outliers = s[(s < iqr_lower) | (s > iqr_upper)]

    df = df.drop(outliers.index)

    # select features based on model
    if model_type == "extended":
        df = df[["target", "length", "speed", "change_speed", "num_lanes", "change_num_lanes", "num_to_links",
                 "dir_l", "dir_r", "dir_s", "dir_multiple_s", "dir_exclusive", "num_foes",
                 "junction_inc_lanes", "priority_lower", "priority_equal", "priority_higher",
                 "is_secondary_or_higher", "is_primary_or_higher", "is_motorway", "is_link"]]
    elif model_type == "default":
        df = df[["target", "length", "speed", "change_speed", "num_lanes", "change_num_lanes", "num_to_links",
                 "junction_inc_lanes", "priority_lower", "priority_equal", "priority_higher",
                 "is_secondary_or_higher", "is_primary_or_higher", "is_motorway", "is_link"]]

    else:
        raise ValueError("Illegal model type:" + model_type)

    return df


def read_edges(folder):
    """ Combine resulting files for edges """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        df = pd.read_csv(os.path.join(folder, f))
        edge_id = df.iloc[0].edgeId

        aggr = df.groupby("laneId").agg(capacity=("flow", "max"))

        data.append({
            "edgeId": edge_id,
            "capacity": float(aggr.capacity.mean())
        })

    return pd.DataFrame(data)


def read_intersections(folder):
    """ Read intersection results """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        # there could be exclusive lanes and the capacity to two edges completely additive
        # however if the capacity is shared one direction could use way more than physical possible
        aggr = df.groupby("fromEdgeId").agg(capacity=("flow", "max")).reset_index()
        aggr.rename(columns={"fromEdgeId": "edgeId"})

        data.append(aggr)

    return pd.concat(data)


def read_routes(folder):
    """ Read routes from folder """
    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        data.append(df)

    df = pd.concat(data)
    aggr = df.groupby("edgeId").mean()

    return aggr.reset_index()
