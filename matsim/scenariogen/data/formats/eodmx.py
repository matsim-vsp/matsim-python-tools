# -*- coding: utf-8 -*-
import math
import os
import random
import sys

import pandas as pd
import numpy as np

from .. import *

# Has households (hogares), persons, trips and viviendas
INPUT_FILES = 4


def is_format(f: os.DirEntry):
    fp = f.name
    if not f.path.endswith(".csv"):
        return False
    if "MiD" in f.name or "SrV" in f.name:
        return False

    return "thogar" in fp or "tsdem" in fp or "tviaje" or "tvivienda" in fp


def read_raw(household_file, person_file, trip_file, vivienda_file):
    """ Read the input files into format used by conversion """

    hh = pd.read_csv(household_file, encoding="utf-8", delimiter=",", decimal=".", low_memory=False, quoting=2)

    p = pd.read_csv(person_file, encoding="utf-8", delimiter=",", decimal=".", low_memory=False, quoting=2)

    t = pd.read_csv(trip_file, encoding="utf-8", delimiter=",", decimal=".", low_memory=False, quoting=2)

    vv = pd.read_csv(vivienda_file, encoding="utf-8", delimiter=",", decimal=".", low_memory=False, quoting=2)

    return hh, p, t, vv


def convert(data: tuple, regio=None):
    """ Convert eod data to standardized survey format """

    (hh, pp, tt, vv) = data

    ps = []
    for p in pp.itertuples():
        ps.append(
            Person(
                p_id=str(int(p.id_soc)),
                p_weight=p.factor,
                hh_id=str(int(p.id_hog)),
                age=int(p.edad),
                gender=EOD2017.gender(int(p.sexo)),
                employment=EOD2017.employment(None if math.isnan(p.p3_7) else int(p.p3_7), int(p.edad)),
                # no data on if person is able to be mobile or not, so always mobile
                restricted_mobility=False,
                driving_license=EOD2017.driv_lic_avail(p.edad),
                car_avail=EOD2017.veh_avail(pint(hh[hh.id_hog == p.id_hog].p2_1_1)),
                bike_avail=EOD2017.veh_avail(pint(hh[hh.id_hog == p.id_hog].p2_1_3)),
                # pt abo always available as there are no abos in cdmx / zmvm
                pt_abo_avail=Availability.YES,
                # always true as mobile persons without trips will be filtered out anyway (later)
                mobile_on_day= True if p.p4_2 == 1 else False,
                # same  as mobile_on_day as there is no specific question on this
                present_on_day= True if p.p4_2 == 1 else False,
                # there is no data on which weekday it is, so we just assume it always is a tuesday = valid
                reporting_day=2,
                n_trips=0 if math.isnan(p.p5_4) else pint(p.p5_4),
                home_district=str(int(p.distrito)).zfill(3)
            )
        )

    ps = pd.DataFrame(ps).set_index("p_id")

    hhs = []
    for h in hh.itertuples():

        hh_id = str(pint(h.id_hog))
        hhs.append(
            Household(
                hh_id=hh_id,
                h_weight=h.factor,
                n_persons=pint(vv[vv.id_viv == h.id_viv].p1_1),
                n_cars=pint(h.p2_1_1),
                n_bikes=pint(h.p2_1_3),
                n_other_vehicles=pint(h.p2_1_2),
                # no data on parking position -> all NA
                car_parking=ParkingPosition.NA,
                economic_status=EOD2017.economic_status(pint(h.estrato)),
                # no info on hh type given in data
                type=HouseholdType.UNKNOWN,
                region_type=EOD2017.region_type(str(pint(h.ent)).zfill(3)),
                location="ZMVM",
            )
        )

    ts = []
    for t in tt.itertuples():

        # only trips mo-thu are relevant
        if t.p5_3 != 1:
            continue

        hh_id = str(pint(ps[ps.index == str(pint(t.id_soc))].hh_id))
        departure = EOD2017.calc_minutes(t.p5_9_1, t.p5_9_2)
        arrival = EOD2017.calc_minutes(t.p5_10_1, t.p5_10_2)
        duration = arrival - departure
        ts.append(
            Trip(
                t_id=str(pint(t.id_via)),
                t_weight=t.factor,
                p_id=str(pint(t.id_soc)),
                hh_id=hh_id,
                n=pint(t.n_via),
                # map "during the week" as tue, everything else to sat
                day_of_week=2 if t.p5_3 == 1 else 6,
                departure=departure,
                duration=duration,
                # this is a dummy trip length. It will be calculated later on, as it is not given as a survey var
                gis_length=float(0),
                main_mode=EOD2017.trip_mode(t),
                purpose=EOD2017.trip_purpose(t.p5_13),
                sd_group=EOD2017.determine_sdGroup(int(t.p5_6)),
                # Trip is valid if length and duration are present
                valid=EOD2017.trip_valid(str(pint(t.dto_origen)).zfill(3), str(pint(t.dto_dest)).zfill(3), duration),
                dep_district=str(int(t.dto_origen)).zfill(3),
                arr_district=str(int(t.dto_dest)).zfill(3),
                arrival=arrival
            )
        )

    return pd.DataFrame(hhs).set_index("hh_id"), ps, pd.DataFrame(ts).set_index("t_id")


def pint(x):
    """ Convert to positive integer"""
    return max(0, int(x))


class EOD2017:
    """ Maps EOD data to standard format"""

    # Modal split CDMX hard coded
    # https://semovi.cdmx.gob.mx/storage/app/media/diagnostico-tecnico-de-movilidad-pim.pdf p 41
    MODALSPLIT = {
        # car
        'p5_14_01': 0.2199,
        # colectivo / microbus
        'p5_14_02': 0.3678,
        # taxi internet
        'p5_14_03': 0.0062,
        #taxi street
        'p5_14_04': 0.0482,
        #metro
        'p5_14_05': 0.2175,
        # autobus rtp
        'p5_14_06': 0.0202,
        # bike
        'p5_14_07': 0.0129,
        #autobus
        'p5_14_08': 0.0321,
        # motorbike
        'p5_14_09': 0.0087,
        #trolebus
        'p5_14_10': 0.0074,
        #metrobus
        'p5_14_11': 0.0409,
        #train ligero
        'p5_14_12': 0.0057,
        #suburban train
        'p5_14_13': 0.0080,
        #walk
        'p5_14_14': 0.2324,
        #mexicable
        'p5_14_15' : 0.00036,
        # bike taxi
        'p5_14_16': 0.0021,
        # mototaxi
        'p5_14_17': 0.0055,
        # school transport
        'p5_14_18': 0.0076,
        # transporte personal
        'p5_14_19': 0.00036,
        # other: 0.0011 split into other, mexicable and transporte personal
        'p5_14_20': 0.00036,
    }

    @staticmethod
    def economic_status(status):

        if status == 1:
            return EconomicStatus.LOW
        elif status == 2:
            return EconomicStatus.MEDIUM_LOW
        elif status == 3:
            return EconomicStatus.MEDIUM_HIGH
        elif status == 4:
            return EconomicStatus.HIGH

        return EconomicStatus.UNKNOWN

    @staticmethod
    def gender(x):
        if x == 1:
            return Gender.M
        elif x == 2:
            return Gender.F

        return Gender.OTHER

    @staticmethod
    def employment(x, age):
        # no data available on part_time_jobs and trainees
        if x == 1 or x == 2:
            return Employment.JOB_FULL_TIME
        elif x == 3:
            return Employment.UNEMPLOYED
        elif x == 4 and age < 18:
            return Employment.SCHOOL
        elif x == 4 and age >= 18:
            return Employment.STUDENT
        elif x == 5:
            return Employment.HOMEMAKER
        elif x == 6:
            return Employment.RETIREE
        elif x == 7:
            return Employment.UNEMPLOYED
        elif x == 8:
            return Employment.UNEMPLOYED
        # the dataset appears to fill all children until 11 years old with employment == "" or None
        # the same goes for people with age 99
        # we do the distribution ourselves according to mexican law
        elif (x is None) and age < 3:
            return Employment.CHILD
        elif (x is None) and 3 < age <= 11:
            return Employment.SCHOOL
        elif (x is None) and age == 99:
            return Employment.RETIREE

        return Employment.OTHER

    @staticmethod
    def calc_minutes(hours, minutes):
        # time values of travel begin / end are required in minutes

        time = int(hours) * 60 + int(minutes)

        return time

    @staticmethod
    def driv_lic_avail(age):
        if age < 18:
            return Availability.NO
        elif age >= 18:
            return Availability.YES

        return Availability.UNKNOWN

    @staticmethod
    def veh_avail(x):
        # 9 is "I do not know" for some questions
        if 9 > x > 0:
            return Availability.YES
        elif x == 0:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def trip_mode(trip):

        modes = []
        modesCount = []

        # the numerics in range() are the indexes of variables for transport mode usage of the survey
        for i in range(18, 58):
            if i % 2 == 0:
                modes.append(pint(trip[i]))
            if i % 2 != 0:
                modesCount.append(0 if math.isnan(trip[i]) else pint(trip[i]))

        if modes.count(1) == 1:
            # only one mode was used
            return EOD2017.mode_from_var_name("p5_14_" + str(modes.index(1) + 1).zfill(2))

        elif modes.count(1) > 1 and modesCount.count(max(modesCount)) == 1:
            # set mode with heaviest usage as main mode
            index = modesCount.index(max(modesCount))

            if modes[index] != 1:
                sys.exit("Error in dataset. The transport mode seems to have been used (p5_15_x = 1), but the pair variable (p5_14_x = 2) says it has not been used!")

            varName = "p5_14_" + str(index + 1).zfill(2)

            return EOD2017.mode_from_var_name(varName)

        elif modes.count(1) > 1 and modesCount.count(max(modesCount)) > 1:
            # several modes are used with the same number of legs -> use general modal share of cdmx
            varNames = []

            indexWalk = 13

            # if e.g. walk has 1 leg + metro has one leg: walk is access / egress mode -> walk must not be the main mode
            if modes[indexWalk] == 1:
                del modesCount[indexWalk]
                modesCount.insert(indexWalk,0)

            j = 0
            maxCount = modesCount.count(max(modesCount))

            for item in modesCount:
                if item == max(modesCount):
                    varNames.append("p5_14_" + str(modesCount.index(item) + 1).zfill(2))
                    modesCount.insert(modesCount.index(item),0)
                    modesCount.remove(item)
                    j = j+1

                    if j == maxCount:
                        break

            weights = []

            for var in varNames:
                weights.append(EOD2017.MODALSPLIT[var])

            # ramdom.choices() appears to produce a list with 1 single element. hence the [0]
            randomVarName = random.choices(varNames, weights)[0]

            return EOD2017.mode_from_var_name(randomVarName)


    @staticmethod
    def mode_from_var_name(varName):
        if varName == "p5_14_01":
            return TripMode.CAR
        # colectivo will be handled as single mode from now on, as it needs to be routed separately from "normal" pt -sme1223
        elif varName == "p5_14_02":
            return TripMode.TAXIBUS
        elif (varName == "p5_14_03" or varName == "p5_14_04" or varName == "p5_14_05" or varName == "p5_14_06" or
              varName == "p5_14_08" or varName == "p5_14_10" or varName == "p5_14_11" or varName == "p5_14_12" or varName == "p5_14_13" or
              varName == "p5_14_15" or varName == "p5_14_16" or varName == "p5_14_17"):
            return TripMode.PT
        elif varName == "p5_14_07":
            return TripMode.BIKE
        elif varName == "p5_14_09":
            return TripMode.MOTORCYCLE
        elif varName == "p5_14_14":
            return TripMode.WALK
        elif varName == "p5_14_18" or varName == "p5_14_19":
            return TripMode.OTHER
        return TripMode.OTHER

    @staticmethod
    def trip_purpose(x):

        if x == 1:
            return Purpose.HOME
        elif x == 2:
            return Purpose.WORK
        elif x == 3:
            return Purpose.EDU
        elif x == 4:
            return Purpose.SHOPPING
        elif x == 5:
            return Purpose.LEISURE
        elif x == 6:
            return Purpose.ACCOMP_OTHER
        elif x == 7 or x == 8:
            return Purpose.PERSONAL_BUSINESS
        elif x == 9:
            return Purpose.LEISURE
        elif x == 10:
            Purpose.OTHER

        return Purpose.OTHER

    @staticmethod
    def region_type(ent):
        if ent == "009":
            # cdmx
            return 1
        elif ent == "013" or ent == "015":
            # outside of cdmx = hidalgo or edomex
            return 3

        return 0

    @staticmethod
    def determine_sdGroup(x):
        # here, only source will be assigned as it is needed for the first act of the day
        # the following is based on assumptions, as e.g. not all trips from / to a shopping center do have the purpose "shopping"
        # but also could be "work" or other purposes
        if x == 1:
            return SourceDestinationGroup.HOME_OTHER
        if x == 2:
            return SourceDestinationGroup.EDU_HOME
        if x == 3 or x == 4 or x == 12:
            return SourceDestinationGroup.WORK_OTHER
        if x == 5:
            return SourceDestinationGroup.SHOP_HOME
        if x == 6 or x == 9 or x == 10 or x == 14:
            return SourceDestinationGroup.LEISURE_HOME
        if x == 7:
            return SourceDestinationGroup.VISIT_OTHER

        return SourceDestinationGroup.OTHER_OTHER

    @staticmethod
    def trip_valid(dep_district, arr_district, duration):
        # validation: trip must not be from or to unknown district, nor have a duration of 0 or lower (invalid)
        if dep_district == "999":
            return False
        if arr_district == "999":
            return False
        if duration <= 0:
            return False
        # it is assumed that trips to another district take at least 10 minutes. This filters out a share of about 0.4% (205314 / 49144928) of trips.
        if dep_district != arr_district and duration < 10:
            return False

        return True


