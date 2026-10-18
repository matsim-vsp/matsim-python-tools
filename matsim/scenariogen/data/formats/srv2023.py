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

    return ("_HH" in fp or "_P" in fp or "_W" in fp or "H2023" in fp or "P2023" in fp or "W2023" in fp or "_H" in fp) and "2023" in fp


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
                SrV2023.gender(p.V_GESCHLECHT),
                SrV2023.employment(p.V_ERW),
                False if p.V_EINSCHR_NEIN else True,
                SrV2023.yes_no(p.V_FUEHR_PKW),
                SrV2023.veh_avail(p.V_PKW_VERFUEG),
                Availability.YES if SrV2023.veh_avail(p.V_RAD_VERFUEG) == Availability.YES or SrV2023.veh_avail(
                    p.V_ERAD_VERFUEG) == Availability.YES  or p.LASTENRAD_VERFUEG == Availability.YES else SrV2023.veh_avail(p.V_RAD_VERFUEG),
                SrV2023.veh_avail(p.V_FK_VERFUEG),
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
                pint(h.V_ANZ_PKW),
                pint(h.V_ANZ_RAD_GESAMT) + pint(h.V_ANZ_LASTENRAD),
                pint(h.V_ANZ_MOT125) + pint(h.V_ANZ_MOPMOT) + pint(h.V_ANZ_ETRETROL) + pint(h.V_ANZ_SONST),
                SrV2023.parking_position(h.V_STELLPL1),
                SrV2023.economic_status(h.E_OEK_STATUS if "E_OEK_STATUS" in hh.keys() else -1, h.V_EINK,
                                        hh_persons),
                SrV2023.household_type(h.E_HHTYP),
                SrV2023.region_type(h, regio, random_state),
                h.ST_CODE_NAME,
                zone=SrV2023.parse_zone(h),
                equivalent_size=equivalent_household_size(hh_persons),
                income=SrV2023.income(h.V_EINK),
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
                # holiday attribute not set
                None,
                int(t.E_BEGINN),
                int(t.E_DAUER),
                float(t.GIS_LAENGE),
                SrV2023.trip_mode(t.E_HVM),
                SrV2023.trip_purpose(t.V_ZWECK),
                SrV2023.sd_group(int(t.E_QZG_17)),
                # Trip is valid if length and duration are present
                0 <= t.GIS_LAENGE and t.E_DAUER > 0,
                from_location=SrV2023.parse_location(t, "V_START_"),
                from_zone=SrV2023.parse_zone(t, "V_START_"),
                to_location=SrV2023.parse_location(t, "V_ZIEL_"),
                to_zone=SrV2023.parse_zone(t, "V_ZIEL_"),
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


class SrV2023:
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

    # Aggregated locations needed to remap
    LOCATIONS = [
        "Blankenfelde-Mahlow/Rangsdorf",
        "Dallgow/Falkensee/Wustermark",
        "Eichwalde/Zeuthen",
        "Hennigsdorf/Velten",
        "Kleinmachnow/Stahnsdorf/Teltow",
        "Lübben/Lübbenau",
        "Werder (Havel)/Schwielowsee",
        "Fürstenwalde"
    ]

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

        # Calculated according to Srv 2023
        # see here: https://tu-dresden.de/bu/verkehr/ivs/srv/ressourcen/dateien/SrV2023_Tabellenbericht_Oberzentren_u500TEW_flach.pdf?lang=de
        # or rather in the Methodenbericht on page 18.

        if eink < 1:
            return EconomicStatus.UNKNOWN

        if eink == 1 or eink == 2 or eink == 3:
            return EconomicStatus.VERY_LOW

        w = equivalent_household_size(persons)

        if eink == 4:
            if w <= 1.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 5:
            if w <= 1.3:
                return EconomicStatus.MEDIUM
            elif w < 2.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 6:
            if w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.0:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 7:
            if w < 1.3:
                return EconomicStatus.HIGH
            elif w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.5:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 8:
            if w < 2.0:
                return EconomicStatus.HIGH
            elif w < 2.6:
                return EconomicStatus.MEDIUM

            return EconomicStatus.LOW

        elif eink == 9:
            if w < 1.3:
                return EconomicStatus.VERY_HIGH
            if w < 2.4:
                return EconomicStatus.HIGH

            return EconomicStatus.MEDIUM


        elif eink == 10:
            if w < 2.0:
                return EconomicStatus.VERY_HIGH

            return EconomicStatus.HIGH

        elif eink == 11:
            if w < 2.6:
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
        elif 2 <= x <= 7:  # fahrrad oder elektrofahrrad oder leihfahrrad oder elektroleihfahrrad oder lastenrad oder elektrolastenrad
            return TripMode.BIKE
        elif x == 9 or x == 10:  # moped/motorrad/motorroller oder elektro-moped/motorrad/motorroller
            return TripMode.MOTORCYCLE
        elif x == 11 or x == 12 or x == 13: # pkw fahrer haushalt, pkw fahrer carsharing, pkw fahrer in anderem pkw
            return TripMode.CAR
        elif x == 14 or x == 15 or x == 16:  # pkw mitfahrer haushalt, pkw mitfahrer carsharing, pkw mitfahrer in anderem pkw
            return TripMode.RIDE
        elif 17 <= x <= 24: # bus, straba, ubahn, sbahn, nahverkehrszug, fvz, taxi, fernbus
            return TripMode.PT

        return TripMode.OTHER  # beinhaltet auch x==8: elektrotretroller

    @staticmethod
    def trip_purpose(x):
        if x == 1: # eigener arbeitsplatz
            return Purpose.WORK
        elif x == 2:  # anderer dienstord/weg
            return Purpose.WORK_BUSINESS
        elif x == 3: # kita
            return Purpose.EDU_KIGA
        elif x == 4: # grundschule
            return Purpose.EDU_PRIMARY
        elif x == 5: # weiterführende schule
            return Purpose.EDU_SECONDARY
        elif x == 6: # berufs/fach/hochschule
            return Purpose.EDU_HIGHER
        elif x == 7: # andere bildungseinrichtung
            return Purpose.EDU_OTHER
        elif x == 8: # einkauf täglicher bedarf
            return Purpose.SHOP_DAILY
        elif x == 9: # sonstiger einkauf
            return Purpose.SHOP_OTHER
        elif x == 10 or x == 11:  # behördengang, arztbesuch oder dienstleistungseinrichtung (post, bank, friseur)
            return Purpose.PERSONAL_BUSINESS
        elif x == 12: # bringen oder holen von personen
            return Purpose.TRANSPORT
        elif x == 16: # erholung/sport im freien (auch wandern, hund ausführen)
            return Purpose.OUTSIDE_RECREATION
        elif x == 14: # gaststätte/kneipe
            return Purpose.DINING
        elif 13 <= x <= 18: # note: ohne 16, 14. kultur, theater, kino oder privater besuch (fremde wohnung) oder sportstätte (allgemein) oder andere freizeitaktivität
            return Purpose.LEISURE
        elif x == 19: # eigene wohnung
            return Purpose.HOME

        return Purpose.OTHER  # sonstiges und unplausibel

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
            return SrV2023.CODES[name]

    @staticmethod
    def income(x):
        # Original groups are
        # 0, 500, 900, 1500, 2000, 2600, 3000, 3600, 4600, 5600, 6600

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
        elif x == 11:
            return 7100

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

        # Truncate ortsteil, this is redundant and not consistent with zone naming scheme
        ot = ort.find("OT")
        if ot > 0:
            ort = ort[:ot]

        # some kind of ortsteils as well
        gt = ort.find("GT")
        if gt > 0:
            ort = ort[:gt]

        ort = ort.strip()

        if "Berlin" in ort:
            return "Berlin"

        if "Lübben (Spreewald)" in ort:
            ort = "Lübben"

        if "Schwielowsee" in ort:
            ort = "Schwielowsee"

        if "Brandenburg" in ort and "Havel" in ort:
            ort = "Brandenburg (Havel)"

        for loc in SrV2023.LOCATIONS:
            if ort in loc:
                return loc

        return ort if ort else pd.NA
