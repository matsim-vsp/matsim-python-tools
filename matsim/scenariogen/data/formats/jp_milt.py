# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime

import pandas as pd

from .. import *

# Persons and trips
INPUT_FILES = 2


# This data format is for the person survey in Japan
# conducted by the Ministry of Land, Infrastructure, Transport and Tourism
# See https://www.mlit.go.jp/toshi/tosiko/toshi_tosiko_tk_000031.html

def is_format(f: os.DirEntry):
    fp = f.name
    if not f.path.endswith(".csv"):
        return False

    return _check_header(f.path, ["cities_code", "household_person_no"])


def read_raw(person_file, trip_file):
    """ Read the input files into format used by conversion """

    p = pd.read_csv(person_file)
    t = pd.read_csv(trip_file)

    return p, t


def convert(data: tuple, regio=None):
    """ Convert data to standardized survey format """

    (pp, tt) = data

    # Magnication factor is recaled to a mean of 1
    w_mean = pp["expansion factor2"].mean()
    weights = {}
    weekdays = {}

    ps = []
    hhs = {}
    for p in pp.itertuples():

        person_number = str(int(p.household_person_no))
        household_number = person_number[:-2]

        # _32 is expansion factor2, the name can not be used directly
        weights[person_number] = round(p._32 / w_mean, 2)
        weekdays[person_number] = Milt2010.weekday(p.survey_month, p.survey_day)

        n_trips = p.trip_end_no

        ps.append(
            Person(
                str(p.household_person_no),
                weights[person_number],
                household_number,
                # Age is a group and given as lower bound
                int(p.age5) + 2,
                Milt2010.gender(p.sex),
                pd.NA,
                Milt2010.restricted_mobility(p.out_difficult_div),
                Availability.YES if p.car_license == 1 else Availability.NO,
                Availability.YES if p.car_cnt > 0 else Availability.NO,
                Availability.YES if p.bicycle_cnt > 0 else Availability.NO,
                Availability.UNKNOWN,
                n_trips > 0,
                True,
                weekdays[person_number],
                n_trips,
                )
        )

        if household_number not in hhs:
            hhs[household_number] = Household(
                household_number,
                weights[person_number],
                1,
                p.car_cnt,
                p.bicycle_cnt,
                0,
                ParkingPosition.NA,
                pd.NA,
                pd.NA,
                0,
                str(p.cities_code)
            )


    # Save the previous trip
    prev_purpose = None
    prev = None

    ts = []
    for t in tt.itertuples():
        # Trucate last two digits
        person_number = str(int(t.household_person_no))
        household_number = person_number[:-2]

        purpose = Milt2010.trip_purpose(t.s_activity_type, prev_purpose)

        # Reset previous purpose if person changes
        if prev != None and prev.household_person_no != t.household_person_no:
            prev_purpose = None

        # Store context of person going to schhool or work
        if purpose == Purpose.WORK:
            prev_purpose = Purpose.WORK
        elif purpose == Purpose.EDU:
            prev_purpose = Purpose.EDU

        ts.append(
            Trip(
                person_number + "_" + str(int(t.trip_no)),
                weights[person_number],
                person_number,
                household_number,
                int(t.trip_no),
                # Weekday is not present in the trip, only for person
                weekdays.get(person_number, pd.NA),
                t.dep_hour * 60 + t.dep_minute,
                t.arr_hour * 60 + t.arr_minute - (t.dep_hour * 60 + t.dep_minute),
                # Only approximate distance between zones, in km
                # Original entry are in 100m
                float(t.move_dist) * 0.1,
                Milt2010.trip_mode(t.original_transport, t.driver),
                purpose,
                Milt2010.sd_group(purpose, prev_purpose, t.dep_pre_code, t.arr_pre_code),
                # Trip is valid if length and duration are present
                t.move_dist > 0 and not np.isnan(t.dep_hour) and not np.isnan(t.arr_hour),
                from_location=str(t.dep_cities_code),
                from_zone=str(t.dep_zone_code),
                to_location=str(t.arr_cities_code),
                to_zone=str(t.arr_zone_code),
            )
        )

        prev = t

    # Uses the dictionaries directly in order to avoid a copy of the dataclasses
    hhs = pd.DataFrame(h.__dict__ for h in hhs.values()).set_index("hh_id")
    ps = pd.DataFrame(p.__dict__ for p in ps).set_index("p_id")

    return hhs, ps, pd.DataFrame(t.__dict__ for t in ts).set_index("t_id")


class Milt2010:
    """ Parsing functions for the MILT 2010 data format """

    @staticmethod
    def weekday(month, day):
        if np.isnan(month) or np.isnan(day):
            return pd.NA

        weekday = datetime(2010, int(month), int(day)).weekday()
        return weekday + 1

    @staticmethod
    def gender(x):
        if x == 1:
            return Gender.M
        elif x == 2:
            return Gender.F

        return Gender.OTHER

    @staticmethod
    def restricted_mobility(div):
        if div == 2:
            return True

        return False

    @staticmethod
    def trip_mode(x, driver):
        if x in (81, 82, 71, 72, 73):
            return TripMode.PT
        elif x in (61, 62, 63, 64, 65):
            if driver == 1:
                return TripMode.CAR
            else:
                return TripMode.RIDE
        elif x in (41, 51, 55):
            return TripMode.MOTORCYCLE
        elif x in (31, 32):
            return TripMode.BIKE
        elif x in (10, 15, 21, 22):
            return TripMode.WALK

        return TripMode.OTHER

    @staticmethod
    def trip_purpose(x, prev_purpose):
        if x == 1:
            return Purpose.WORK
        elif x == 2:
            return Purpose.EDU
        elif x == 3:
            return Purpose.HOME
        elif x == 4:
            return Purpose.SHOPPING
        elif x == 5:
            return Purpose.LEISURE
        elif x == 6:
            return Purpose.PERSONAL_BUSINESS
        elif x == 7 or x == 8 or x == 9 or x == 47 or x == 11:
            return Purpose.WORK_BUSINESS
        elif x == 12:
            # return trip to work or school
            # need to know which one it is
            if prev_purpose == None:
                return Purpose.WORK

            return prev_purpose

        return Purpose.OTHER

    @staticmethod
    def sd_group(purpose, prev_purpose, dep_precode, arr_precode):

        # The precode does not allow a distinction between work and school
        # There fore the purpose and prev purpose need to be considered

        # Precode:  1 home, 2 work or school,  3 other
        source = "OTHER"
        destination = "OTHER"

        if dep_precode == 1:
            source = "HOME"
        elif dep_precode == 2:
            if prev_purpose == Purpose.EDU:
                source = "EDU"
            else:
                # Assume here that work is the default if no previous edu trip is known
                source = "WORK"
        elif dep_precode == 3:
            if prev_purpose == Purpose.LEISURE:
                source = "LEISURE"
            elif prev_purpose == Purpose.SHOPPING:
                source = "SHOP"
            else:
                source = "OTHER"

        if arr_precode == 1:
            destination = "HOME"
        elif arr_precode == 2:
            if purpose == Purpose.EDU:
                destination = "EDU"
            else:
                destination = "WORK"
        elif arr_precode == 3:
            if purpose == Purpose.LEISURE:
                destination = "LEISURE"
            elif purpose == Purpose.SHOPPING:
                destination = "SHOP"
            else:
                destination = "OTHER"

        return SourceDestinationGroup.parse(source, destination)
