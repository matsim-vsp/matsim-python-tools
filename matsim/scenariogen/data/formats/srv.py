# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd

from .. import *
from ..preparation import equivalent_household_size

# Has households, persons and trips
INPUT_FILES = 3


def is_format(f: os.DirEntry):
    fp = f.name
    if not f.path.endswith(".csv"):
        return False
    if "MiD" in f.name:
        return False

    return "_HH" in fp or "_P" in fp or "_W" in fp or "H2018" in fp or "P2018" in fp or "W2018" in fp or "_H" in fp


def read_raw(household_file, person_file, trip_file):
    """ Read the input files into format used by conversion """

    hh = pd.read_csv(household_file, encoding="windows-1252", delimiter=";", decimal=",",
                     quotechar="\"", low_memory=False, quoting=2)

    p = pd.read_csv(person_file, encoding="windows-1252", delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    t = pd.read_csv(trip_file, encoding="windows-1252", delimiter=";", decimal=",",
                    quotechar="\"", low_memory=False, quoting=2)

    return hh, p, t


def convert(data: tuple, regio=None):
    """ Convert srv data to standardized survey format """

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
        hh_persons = ps[ps.hh_id == hh_id]

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
                                        hh_persons),
                SrV2018.household_type(h.E_HHTYP),
                SrV2018.region_type(h, regio, random_state),
                h.ST_CODE_NAME,
                zone=SrV2018.parse_zone(h),
                equivalent_size=equivalent_household_size(hh_persons),
                income=SrV2018.income(h.V_EINK),
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
                # Trip is valid if length and duration are present
                0 <= t.GIS_LAENGE and t.E_DAUER > 0,
                from_location=SrV2018.parse_location(t, "V_START_"),
                from_zone=SrV2018.parse_zone(t, "V_START_"),
                to_location=SrV2018.parse_location(t, "V_ZIEL_"),
                to_zone=SrV2018.parse_zone(t, "V_ZIEL_"),
            )
        )

    return pd.DataFrame(hhs).set_index("hh_id"), ps, pd.DataFrame(ts).set_index("t_id")


def pint(x):
    """ Convert to positive integer"""
    return max(0, int(x))


def parse_int_str(x):
    """ Return parsed int or string """
    try:
        i = int(x)
        if i >= 0:
            return str(i)
        return None
    except ValueError:
        if not x:
            return None
        return x


class SrV2018:
    """ Maps SrV data to standard format"""

    # Fallback regiostar codes hard-coded
    CODES = {
        'Berlin': 1,
        'Potsdam': 2,
        'Cottbus': 4,
        'Frankfurt (Oder)': 2,
        'Kleinmachnow/Stahnsdorf/Teltow': 3,
        'Werder (Havel)/Schwielowsee': 3,
        'Michendorf/Nuthetal': 3,
        'Bernau': 3,
        'Blankenfelde-Mahlow/Rangsdorf': 3,
        'Dallgow/Falkensee/Wustermark': 3,
        'Eichwalde/Zeuthen': 3,
        'Fürstenwalde': 3,
        'Spremberg': 3,
        'Strausberg': 3,
        'Rüdersdorf': 3,
        'Oranienburg': 3,
        'Hennigsdorf/Velten': 3,
        'Brandenburg (Havel)': 5,
        'Schönefeld': 3,
        'Königs Wusterhausen': 3,
        'Eberswalde': 3,
        'Lübben/Lübbenau': 6,
        'Ludwigsfelde': 3,
        'Leipzig': 1,
        'Dresden': 1
    }

    @staticmethod
    def parking_position(x):

        if x == 1:
            return ParkingPosition.PRIVATE
        elif x == 2:
            return ParkingPosition.PUBLIC
        elif x == 3:
            return ParkingPosition.DIFFERENT

        return ParkingPosition.NA

    @staticmethod
    def economic_status(status, eink, persons):

        if status >= 1:
            return list(EconomicStatus)[int(status) - 1]

        # Calculated according to Srv 2018
        # https://tu-dresden.de/bu/verkehr/ivs/srv/ressourcen/dateien/SrV2018_Tabellenbericht_Oberzentren_500TEW-_flach.pdf?lang=de

        if eink < 1:
            return EconomicStatus.UNKNOWN

        if eink == 1 or eink == 2:
            return EconomicStatus.VERY_LOW

        w = equivalent_household_size(persons)

        if eink == 3:
            if w < 1.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 4:
            if w < 1.3:
                return EconomicStatus.MEDIUM
            elif w < 1.6:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 5:
            if w < 1.6:
                return EconomicStatus.MEDIUM
            elif w < 2.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 6:
            if w < 1.3:
                return EconomicStatus.HIGH
            elif w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.0:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 7:
            if w < 1.6:
                return EconomicStatus.HIGH
            elif w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.5:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 8:
            if w < 2.1:
                return EconomicStatus.HIGH
            elif w < 3.0:
                return EconomicStatus.MEDIUM

            return EconomicStatus.LOW

        elif eink == 9:
            if w < 1.3:
                return EconomicStatus.VERY_HIGH
            if w < 2.8:
                return EconomicStatus.HIGH
            return EconomicStatus.MEDIUM

        elif eink == 10:
            if w < 2.5:
                return EconomicStatus.VERY_HIGH

            return EconomicStatus.HIGH

        return EconomicStatus.UNKNOWN

    @staticmethod
    def household_type(x):
        if x == 1:
            return HouseholdType.MULTI_W_CHILDREN
        elif x == 2:
            return HouseholdType.MULTI_WO_CHILDREN

        return HouseholdType.SINGLE

    @staticmethod
    def gender(x):
        if x == 1:
            return Gender.M
        elif x == 2:
            return Gender.F

        return Gender.OTHER

    @staticmethod
    def employment(x):
        if x == 1:
            return Employment.CHILD
        elif x == 2:
            return Employment.HOMEMAKER
        elif x == 3:
            return Employment.RETIREE
        elif x == 5:
            return Employment.UNEMPLOYED
        elif x == 6:
            return Employment.SCHOOL
        elif x == 7:
            return Employment.STUDENT
        elif x == 8:
            return Employment.TRAINEE
        elif x == 9:
            return Employment.JOB_FULL_TIME
        elif x == 10 or x == 11:
            return Employment.JOB_PART_TIME

        return Employment.OTHER

    @staticmethod
    def yes_no(x):
        if x == 1:
            return Availability.YES
        elif x == 2:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def veh_avail(x):
        if x == 1 or x == 2:
            return Availability.YES
        elif x == 3:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def trip_mode(x):
        if x == 1:
            return TripMode.WALK
        elif x == 2 or x == 18 or x == 19:
            return TripMode.BIKE
        elif x == 3:
            return TripMode.MOTORCYCLE
        elif x == 4 or x == 5 or x == 6:
            return TripMode.CAR
        elif x == 7 or x == 8 or x == 9:
            return TripMode.RIDE
        elif 10 <= x <= 17:
            return TripMode.PT

        return TripMode.OTHER

    @staticmethod
    def trip_purpose(x):
        if x == 1:
            return Purpose.WORK
        elif x == 2:
            return Purpose.WORK_BUSINESS
        elif x == 3:
            return Purpose.EDU_KIGA
        elif x == 4:
            return Purpose.EDU_PRIMARY
        elif x == 5:
            return Purpose.EDU_SECONDARY
        elif x == 6:
            return Purpose.EDU_HIGHER
        elif x == 7:
            return Purpose.EDU_OTHER
        elif x == 8:
            return Purpose.SHOP_DAILY
        elif x == 9:
            return Purpose.SHOP_OTHER
        elif x == 19 or x == 10:
            return Purpose.PERSONAL_BUSINESS
        elif x == 11:
            return Purpose.TRANSPORT
        elif x == 15:
            return Purpose.OUTSIDE_RECREATION
        elif x == 13:
            return Purpose.DINING
        elif 12 <= x <= 17:
            return Purpose.LEISURE
        elif x == 18:
            return Purpose.HOME

        return Purpose.OTHER

    @staticmethod
    def sd_group(x):
        if x <= 0:
            return SourceDestinationGroup.UNKNOWN

        return list(SourceDestinationGroup)[int(x) - 1]

    @staticmethod
    def region_type(d, regio, random_state):

        if "PLZ" in dir(d) and regio is not None:
            plz = int(d.PLZ)

            r = regio[regio.plz == plz]
            if len(r) == 0:
                raise ValueError("Unknown PLZ: %d" % plz)

            if len(r) > 1:
                r = r.sample(n=1, random_state=random_state)

            r = r.iloc[0].RegioStaR7
            if np.isnan(r):
                raise ValueError("No RegioStar value available for: %d" % plz)

            return int(r) - 70

        else:
            name = d.ST_CODE_NAME
            return SrV2018.CODES[name]

    @staticmethod
    def income(x):
        # Original groups are
        # 0, 500, 900, 1500, 2000, 2600, 3000, 3600, 4600, 5600

        # Return the mean between each grop
        if x == 1:
            return 250
        elif x == 2:
            return 700
        elif x == 3:
            return 1200
        elif x == 4:
            return 1750
        elif x == 5:
            return 2300
        elif x == 6:
            return 2800
        elif x == 7:
            return 3300
        elif x == 8:
            return 4100
        elif x == 9:
            return 5100
        elif x == 10:
            return 6100

        return -1

    @staticmethod
    def parse_zone(h, prefix=""):
        ob = parse_int_str(getattr(h, prefix + "OBERBEZIRK"))

        zone = pd.NA
        if ob and hasattr(h, prefix + "UNTERBEZIRK"):
            zone = ob
            ub = parse_int_str(getattr(h, prefix + "UNTERBEZIRK"))
            if ub:
                zone += "-" + ub
                tb = parse_int_str(getattr(h, prefix + "TEILBEZIRK"))
                if tb:
                    zone += "-" + tb

        return zone

    @staticmethod
    def parse_location(h, prefix=""):
        ort = parse_int_str(getattr(h, prefix + "ORT"))
        if not ort:
            return pd.NA

        if "Berlin" in ort:
            return "Berlin"

        return ort
