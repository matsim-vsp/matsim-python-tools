# -*- coding: utf-8 -*-

import os

import pandas as pd

from .. import *


def read_visitations(folder):
    """ Read all visits from folder """

    visits = []

    for f in os.listdir(folder):

        if not f.endswith(".csv"):
            continue

        print("Reading", f)

        t = pd.read_csv(os.path.join(folder, f), parse_dates=[0])
        t.timestamps = t.timestamps.str.split(",")
        t["idx"] = t.index

        t = t.explode("timestamps")
        t.timestamps = pd.to_datetime(t.timestamps, format="%H:%M:%S")
        delta = (t.timestamps.dt.hour * 60 + t.timestamps.dt.minute) * 60 + t.timestamps.dt.second
        delta = pd.to_timedelta(delta, unit="s")

        t["ts"] = t.day + delta

        t = t.groupby(["device_id", "osm_id", "idx"]).agg(start=("ts", "min"), end=("ts", "max"),
                                                          home=("distance_to_home", "mean"),
                                                          work=("distance_to_work", "mean")).reset_index()

        t["purpose"] = Purpose.OTHER
        t.loc[t.home == 0, "purpose"] = Purpose.HOME
        t.loc[t.work == 0, "purpose"] = Purpose.WORK

        visits.append(t)

    df = pd.concat(visits)

    aggr = df.groupby(["osm_id", "purpose"]).agg(count=("idx", "count")).reset_index()

    total = []

    for v in aggr.itertuples():
        total.append(Visitations(v.osm_id, v.count, v.purpose))

    return pd.DataFrame(total)