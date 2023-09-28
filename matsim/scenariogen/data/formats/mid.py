# -*- coding: utf-8 -*-

import os
import pandas as pd
import pyproj
import re
from collections import Counter
from shapely.geometry import box
from shapely.ops import transform

from .. import *

INPUT_FILES = 3


def is_format(f: os.DirEntry):
    return f.name.startswith("MiD2017_") and f.path.endswith(".csv")


def read_raw(household_file, person_file, trip_file):
    hh = pd.read_csv(household_file, delimiter=";", decimal=",",
                     quotechar="\"", low_memory=False, quoting=2)

    p = pd.read_csv(person_file, delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    t = pd.read_csv(trip_file, delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    return hh, p, t


def convert(data: tuple, regio=None):
    hh, pp, tt = data

    hhs = []
    for h in hh.itertuples():
        hh_id = str(int(h.H_ID_Lok))
        hhs.append(Household(hh_id, h.H_GEW, int(h.hhgr_gr2), int(h.anzauto_gr3), int(h.pedrad), int(h.motmop),
                             ParkingPosition.NA,
                             Mid2017.economic_status(h), Mid2017.household_type(h), 0, "", Mid2017.geom(h)))

    ps = []
    for p in pp.itertuples():
        p_id = str(int(p.HP_ID_Lok))
        hh_id = str(int(p.H_ID_Lok))

        # exlucde business trips
        ps.append(Person(
            p_id, p.P_GEW, hh_id, Mid2017.age(p), Mid2017.gender(p), Mid2017.employment(p), None,
            Mid2017.driving_license(p), Mid2017.car_avail(p), Mid2017.bike_avail(p), Mid2017.pt_abo_avail(p),
            Mid2017.mobile(p), Mid2017.present_on_day(p), int(p.ST_WOTAG), int(p.anzwege1)
        ))

    ts = []

    counts = Counter()

    for t in tt.itertuples():

        # business trips are not accounted
        if t.W_RBW == 1.0:
            continue

        # Person might have multiple days
        p_id = str(int(t.HP_ID_Lok))
        t_id = p_id + "%d%d" % (t.ST_WOCHE, t.ST_WOTAG)

        n = counts[t_id]
        counts[t_id] += 1

        depature = Mid2017.parse_time(t.W_SZ)

        trip = Trip(
            t_id + "_" + str(n),
            t.W_GEW, p_id, str(int(t.H_ID_Lok)),
            n, int(t.ST_WOTAG),depature, int(t.wegmin), float(t.wegkm),
            Mid2017.main_mode(t), Mid2017.purpose(t), None,
            float(t.wegkm) < 1000 and int(t.wegmin) < 1000 and depature is not None
        )

        if trip.purpose == Purpose.WAYBACK:
            if trip.n >= 3:
                # Use purpose of previous trip
                trip.purpose = ts[-2].purpose
            else:
                trip.purpose = Purpose.HOME

        ts.append(trip)

    return pd.DataFrame(hhs).set_index("hh_id"), pd.DataFrame(ps).set_index("p_id"), pd.DataFrame(ts).set_index("t_id")

def flip(x, y):
    """Flips the x and y coordinate values"""
    return y, x

class Mid2017:
    """ Converter for 2017 MID format """

    ct = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:3035'),  # source coordinate system
        pyproj.Proj('epsg:4326'),
        always_xy=True)  # destination coordinate system

    @staticmethod
    def coordinate(value, grid_size, scale):
        # EPSG:3035, coordinate is left lower point
        split = re.split(r"N|E", value)
        x = float(split[2]) * scale
        y = float(split[1]) * scale

        geom = box(x, y, x + grid_size, y + grid_size)

        return transform(Mid2017.ct.transform, geom).wkt

    @staticmethod
    def geom(h):
        if h.GITTER_500m.strip():
            return Mid2017.coordinate(h.GITTER_500m, 500, 100)
        elif h.GITTER_1km.strip():
            return Mid2017.coordinate(h.GITTER_1km, 1000, 1000)
        elif h.GITTER_5km.strip():
            return Mid2017.coordinate(h.GITTER_5km, 5000, 1000)

        return None

    @staticmethod
    def economic_status(h):
        return list(EconomicStatus)[int(h.oek_status) - 1]

    @staticmethod
    def household_type(h):
        x = int(h.hhtyp2)

        if x == 2:
            return HouseholdType.MULTI_W_CHILDREN
        elif x == 3:
            return HouseholdType.MULTI_WO_CHILDREN

        return HouseholdType.SINGLE if int(h.hhgr_gr2) == 1 else HouseholdType.MULTI_WO_CHILDREN

    @staticmethod
    def age(p):
        x = int(p.alter_gr)
        if x == 1:
            return 0
        elif x == 2:
            return 18
        elif x == 3:
            return 30
        elif x == 4:
            return 40
        elif x == 5:
            return 50
        elif x == 6:
            return 60
        elif x == 7:
            return 70
        elif x == 8:
            return 80

        return -1

    @staticmethod
    def gender(p):
        if p.HP_SEX == 1.0:
            return Gender.M
        elif p.HP_SEX == 2.0:
            return Gender.F

        return Gender.OTHER

    @staticmethod
    def employment(p):
        x = int(p.taet)
        if x == 1:
            return Employment.JOB_FULL_TIME
        elif x == 2:
            return Employment.STUDENT
        elif x == 3:
            return Employment.HOMEMAKER
        elif x == 4:
            return Employment.RETIREE

        return Employment.OTHER

    @staticmethod
    def driving_license(p):
        x = int(p.P_FSCHEIN)
        if x == 1:
            return Availability.YES
        elif x == 2:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def car_avail(p):
        x = int(p.P_STKFZ)
        if x == 1 or x == 2:
            return Availability.YES
        elif x == 3:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def bike_avail(p):
        x = int(p.vpedrad)
        if x == 1 or x == 2 or x == 3:
            return Availability.YES
        elif x == 4:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def pt_abo_avail(p):
        x = int(p.P_FKARTE)
        if x == 4 or x == 5:
            return Availability.YES
        elif x > 8:
            return Availability.UNKNOWN

        return Availability.NO

    @staticmethod
    def mobile(p):
        x = int(p.mobil)
        if x == 0:
            return False
        elif x == 1:
            return True
        return None

    @staticmethod
    def present_on_day(p):
        x = int(p.P_STUM)
        if x == 3:
            return True
        elif x == 1 or x == 2:
            return False
        return None

    @staticmethod
    def parse_time(x):
        t = x.strip().split(":")
        if len(t) < 2:
            return None

        return int(t[0]) * 60 + int(t[1])

    @staticmethod
    def main_mode(t):
        x = int(t.hvm)
        if x == 1:
            return TripMode.WALK
        elif x == 2:
            return TripMode.BIKE
        elif x == 3:
            return TripMode.RIDE
        elif x == 4:
            return TripMode.CAR
        elif x == 5:
            return TripMode.PT

        return TripMode.OTHER

    @staticmethod
    def purpose(t):
        x = int (t.zweck)
        if x == 1:
            return Purpose.WORK
        elif x == 2:
            return Purpose.WORK_BUSINESS
        elif x == 3:
            return Purpose.EDU
        elif x == 4:
            return Purpose.SHOPPING
        elif x == 5:
            return Purpose.PERSONAL_BUSINESS
        elif x == 6:
            return Purpose.TRANSPORT
        elif x == 7:
            return Purpose.LEISURE
        elif x == 8:
            return Purpose.HOME
        elif x == 9: # trip back to previous
            return Purpose.WAYBACK

        return Purpose.OTHER