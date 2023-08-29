#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd

from . import *

# TODO: generalized readers with auto detection

def read_srv(household_file, person_file, trip_file):
    """ Read SrV into pandas format """

    hh = pd.read_csv(household_file, encoding="windows-1252", delimiter=";", decimal=",",
                     quotechar="\"", low_memory=False, quoting=2)

    p = pd.read_csv(person_file, encoding="windows-1252", delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    t = pd.read_csv(trip_file, encoding="windows-1252", delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    return hh, p, t


def _batch(iterable: list, max_batch_size: int):
    """ Batches an iterable into lists of given maximum size, yielding them one by one. """
    batch = []
    for element in iterable:
        batch.append(element)
        if len(batch) >= max_batch_size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch


def read_all_srv(dirs, regio=None):
    """ Scan directories and read everything into one dataframe """

    hh = []
    pp = []
    tt = []

    for d in dirs:

        files = []

        # Collect all SrV files
        for f in os.scandir(d):
            fp = f.name
            if not f.is_file() or not f.path.endswith(".csv"):
                continue
            if "_HH" in fp or "_P" in fp or "_W" in fp or "H2018" in fp or "P2018" in fp or "W2018" in fp:
                files.append(f.path)

        files = sorted(files)

        if len(files) % 3 != 0:
            print(files)
            raise ValueError("File structure is wrong. Need exactly 3 files per region.")

        for h, p, t in _batch(files, 3):
            print("Reading", h, p, t)

            data = read_srv(h, p, t)
            df = srv_to_standard(data, regio)

            hh.append(df[0])
            pp.append(df[1])
            tt.append(df[2])

    hh = pd.concat(hh, axis=0)
    hh = hh[~hh.index.duplicated(keep='first')]
    print("Households: ", len(hh))

    pp = pd.concat(pp, axis=0)
    pp = pp[~pp.index.duplicated(keep='first')]
    pp.sort_index(inplace=True)
    print("Persons: ", len(pp))

    tt = pd.concat(tt, axis=0)
    tt = tt[~tt.index.duplicated(keep='first')]
    tt.sort_values(["p_id", "n"], inplace=True)
    print("Trips: ", len(tt))

    return hh, pp, tt


def pint(x):
    """ Convert to positive integer"""
    return max(0, int(x))


def srv_to_standard(data: tuple, regio=None):
    """ Convert srv data to standardized survey format """

    # Needs to be importer late
    from converter import SrV2018

    (hh, pp, tt) = data

    if regio is not None:
        regio = pd.read_csv(regio)

    ps = []
    for p in pp.itertuples():
        ps.append(
            Person(
                str(int(p.HHNR)) + "_" + str(int(p.PNR)),
                p.GEWICHT_P,
                str(int(p.HHNR)),
                int(p.V_ALTER),
                SrV2018.gender(p.V_GESCHLECHT),
                SrV2018.employment(p.V_ERW),
                False if p.V_EINSCHR_NEIN else True,
                SrV2018.yes_no(p.V_FUEHR_PKW),
                SrV2018.veh_avail(p.V_PKW_VERFUEG),
                Availability.YES if SrV2018.veh_avail(p.V_RAD_VERFUEG) == Availability.YES or SrV2018.veh_avail(
                    p.V_ERAD_VERFUEG) == Availability.YES else SrV2018.veh_avail(p.V_RAD_VERFUEG),
                SrV2018.veh_avail(p.V_FK_VERFUEG),
                p.V_WOHNUNG == 1,
                p.V_WOHNORT == 1,
                int(p.STICHTAG_WTAG),
                int(p.E_ANZ_WEGE)
            )
        )

    ps = pd.DataFrame(ps).set_index("p_id")

    random_state = np.random.RandomState(0)

    hhs = []
    for h in hh.itertuples():

        # Invalid entries in certain files
        if np.isnan(h.HHNR):
            continue

        hh_id = str(int(h.HHNR))
        hhs.append(
            Household(
                hh_id,
                h.GEWICHT_HH,
                pint(h.V_ANZ_PERS),
                pint(h.V_ANZ_PKW_PRIV + h.V_ANZ_PKW_DIENST),
                pint(h.V_ANZ_RAD + h.V_ANZ_ERAD),
                pint(h.V_ANZ_MOT125 + h.V_ANZ_MOPMOT + h.V_ANZ_SONST),
                SrV2018.parking_position(h.V_STELLPL1),
                SrV2018.economic_status(h.E_OEK_STATUS if "E_OEK_STATUS" in hh.keys() else -1, h.V_EINK,
                                        ps[ps.hh_id == hh_id]),
                SrV2018.household_type(h.E_HHTYP),
                SrV2018.region_type(h, regio, random_state),
                h.ST_CODE_NAME,
            )
        )

    ts = []
    for t in tt.itertuples():
        # TODO: E_DAUER, E_GESCHW
        # E_ANKUNFT
        # TODO: double check
        ts.append(
            Trip(
                str(int(t.HHNR)) + "_" + str(int(t.PNR)) + "_" + str(int(t.WNR)),
                t.GEWICHT_W,
                str(int(t.HHNR)) + "_" + str(int(t.PNR)),
                str(int(t.HHNR)),
                int(t.WNR),
                int(t.STICHTAG_WTAG),
                int(t.E_BEGINN),
                int(t.E_DAUER),
                float(t.GIS_LAENGE),
                SrV2018.trip_mode(t.E_HVM),
                SrV2018.trip_purpose(t.V_ZWECK),
                SrV2018.sd_group(int(t.E_QZG_17)),
                t.E_WEG_GUELTIG != 0 and t.GIS_LAENGE_GUELTIG != 0
            )
        )

    return pd.DataFrame(hhs).set_index("hh_id"), ps, pd.DataFrame(ts).set_index("t_id")
