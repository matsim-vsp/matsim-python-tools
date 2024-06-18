""" This module contains dataclasses and methods for reading and processing survey data.
"""

__all__ = ["read_all", "ParkingPosition", "HouseholdType", "EconomicStatus", "Gender", "Employment", "Availability",
           "Purpose",
           "TripMode", "DistanceGroup", "DurationGroup", "SourceDestinationGroup",
           "Household", "Person", "Trip", "Activity", "Visitations"]

import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Union, Tuple, get_type_hints

import numpy as np
import pandas as pd


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


def read_all(dirs: Union[str, List[str]], regio=None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """ Scan directories and read everything into one dataframe """

    from .formats import srv, mid

    hh = []
    pp = []
    tt = []

    # Allow to use without list
    if type(dirs) == str:
        dirs = [dirs]

    for d in dirs:

        for format in (srv, mid):

            files = []

            # Collect all files for each format
            for f in os.scandir(d):
                if not f.is_file():
                    continue
                if format.is_format(f):
                    files.append(f.path)

            files = sorted(files)

            if len(files) % format.INPUT_FILES != 0:
                print(files)
                raise ValueError("File structure is wrong. Need exactly %d files per region." % format.INPUT_FILES)

            for input_files in _batch(files, format.INPUT_FILES):
                print("Reading", format.__name__, *input_files)

                data = format.read_raw(*input_files)
                df = format.convert(data, regio)

                hh.append(df[0])
                pp.append(df[1])
                tt.append(df[2])

    hh = pd.concat(hh, axis=0)
    hh = hh[~hh.index.duplicated(keep='first')]
    hh = hh.dropna(axis=1, how='all')
    # _df_to_categorical(hh, Household)

    print("Households: ", len(hh))

    pp = pd.concat(pp, axis=0)
    pp = pp[~pp.index.duplicated(keep='first')]
    pp = pp.dropna(axis=1, how='all')
    pp.sort_index(inplace=True)
    # _df_to_categorical(pp, Person)

    print("Persons: ", len(pp))

    tt = pd.concat(tt, axis=0)
    tt = tt[~tt.index.duplicated(keep='first')]
    tt = tt.dropna(axis=1, how='all')
    tt.sort_values(["p_id", "n"], inplace=True)
    # _df_to_categorical(tt, Trip)

    print("Trips: ", len(tt))

    return hh, pp, tt


class StrEnum(str, Enum):
    pass


# this creates nice lowercase and JSON serializable names
# https://docs.python.org/3/library/enum.html#using-automatic-values
class AutoNameLower(StrEnum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class AutoNameLowerStrEnum(AutoNameLower):

    @classmethod
    def dtype(cls):
        """Returns a pandas CategoricalDtype with the enum values as categories."""
        return pd.api.types.CategoricalDtype(categories=list(cls), ordered=True)

    @classmethod
    def sort_idx(cls, series):
        """ Return index needed for sorting"""
        v = list(cls)
        return series.map(v.index)


def _df_to_categorical(df, clazz):
    """ Convert columns to categorical types """

    for k, v in get_type_hints(clazz).items():
        if hasattr(v, "dtype") and k in df.columns:
            df[k] = df[k].astype(v.dtype())

    return df


class ParkingPosition(AutoNameLowerStrEnum):
    PRIVATE = auto()
    PUBLIC = auto()
    DIFFERENT = auto()
    NA = auto()


class HouseholdType(AutoNameLowerStrEnum):
    MULTI_W_CHILDREN = auto()
    MULTI_WO_CHILDREN = auto()
    SINGLE = auto()


class EconomicStatus(AutoNameLowerStrEnum):
    VERY_LOW = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    VERY_HIGH = auto()
    UNKNOWN = auto()


class Gender(AutoNameLowerStrEnum):
    M = auto()
    F = auto()
    OTHER = auto()


class Employment(AutoNameLowerStrEnum):
    CHILD = auto()
    HOMEMAKER = auto()
    RETIREE = auto()
    UNEMPLOYED = auto()
    SCHOOL = auto()
    STUDENT = auto()
    TRAINEE = auto()

    JOB_FULL_TIME = auto()
    JOB_PART_TIME = auto()
    OTHER = auto()


class Availability(AutoNameLowerStrEnum):
    YES = auto()
    NO = auto()
    UNKNOWN = auto()


class Purpose(AutoNameLowerStrEnum):
    WORK = auto()
    WORK_BUSINESS = auto()
    EDU_KIGA = auto()
    """ Kinderkrippe/-garten  """
    EDU_PRIMARY = auto()
    """ Grundschule """
    EDU_SECONDARY = auto()
    """ Weiterführende Schule """
    EDU_HIGHER = auto()
    """ Berufs-, Fach-, Hochschule """
    EDU_OTHER = auto()
    """ Andere Bildungseinrichtung """
    EDU = auto()
    """ All Edu """

    SHOPPING = auto()
    """ General non differentiated shopping """

    SHOP_DAILY = auto()
    SHOP_OTHER = auto()
    PERSONAL_BUSINESS = auto()
    TRANSPORT = auto()
    LEISURE = auto()
    DINING = auto()
    OUTSIDE_RECREATION = auto()
    VISIT = auto()
    HOME = auto()
    WAYBACK = auto()
    OTHER = auto()


class TripMode(AutoNameLowerStrEnum):
    WALK = auto()
    BIKE = auto()
    CAR = auto()
    RIDE = auto()
    PT = auto()
    MOTORCYCLE = auto()
    OTHER = auto()


class DistanceGroup(AutoNameLowerStrEnum):
    """ These distance groups are designed so that they are roughly equally populated. """

    ZERO = auto()
    G_500M = auto()
    G_1KM = auto()
    G_2KM = auto()
    G_3KM = auto()
    G_5KM = auto()
    G_10KM = auto()
    G_25KM = auto()
    G_50KM = auto()
    G_100KM = auto()
    OVER_100KM = auto()

    @staticmethod
    def cut(values):
        bins = [0, 0.5, 1, 2, 3, 5, 10, 25, 50, 100]
        values = np.asarray(values)

        idx = np.digitize(values, bins, right=True)
        # Set ZERO group manually
        idx[np.where(values <= 0)] = 0
        return np.take(np.asarray(DistanceGroup, dtype=object), idx, axis=0)


class DurationGroup(AutoNameLowerStrEnum):
    """ Most common duration groups, right side is inclusive e.g <= 5 min """

    G_5MIN = auto()
    G_15MIN = auto()
    G_30MIN = auto()
    G_60MIN = auto()
    G_120MIN = auto()
    G_180MIN = auto()
    G_300MIN = auto()
    G_420MIN = auto()
    G_480MIN = auto()
    G_510MIN = auto()
    G_570MIN = auto()
    G_660MIN = auto()
    G_750MIN = auto()
    REST_OF_DAY = auto()

    @staticmethod
    def cut(values):
        bins = [5, 15, 30, 60, 120, 180, 300, 420, 480, 510, 570, 660, 750]

        values = np.asarray(values)
        idx = np.digitize(values, bins, right=True)
        return np.take(np.asarray(DurationGroup, dtype=object), idx, axis=0)


class SourceDestinationGroup(AutoNameLowerStrEnum):
    HOME_WORK = auto()
    HOME_CHILDCARE = auto()
    HOME_EDU = auto()
    HOME_BUSINESS = auto()
    HOME_SHOP = auto()
    HOME_LEISURE = auto()
    HOME_OTHER = auto()
    WORK_HOME = auto()
    CHILDCARE_HOME = auto()
    EDU_HOME = auto()
    BUSINESS_HOME = auto()
    SHOP_HOME = auto()
    LEISURE_HOME = auto()
    OTHER_HOME = auto()
    OTHER_WORK = auto()
    WORK_OTHER = auto()
    OTHER_OTHER = auto()

    UNKNOWN = auto()

    def source(self):
        if self.name.startswith("HOME"):
            return Purpose.HOME
        elif self.name.startswith("WORK"):
            return Purpose.WORK

        return Purpose.OTHER


@dataclass
class Household:
    """ Universal definition of household attributes """
    hh_id: str
    h_weight: float
    n_persons: int
    n_cars: int
    n_bikes: int
    n_other_vehicles: int
    car_parking: ParkingPosition
    economic_status: EconomicStatus
    type: HouseholdType
    region_type: int
    location: str
    zone: str = None
    """ A detailed zone, which can be more accurate than location. """
    income: float = None
    geom: object = None


@dataclass
class Person:
    """ Universal definition of person attributes."""
    p_id: str
    p_weight: float
    hh_id: str
    age: int
    gender: Gender
    employment: Employment
    restricted_mobility: bool
    driving_license: Availability
    car_avail: Availability
    bike_avail: Availability
    pt_abo_avail: Availability
    mobile_on_day: bool
    present_on_day: bool
    reporting_day: int
    n_trips: int


@dataclass
class Trip:
    """ Universal definition of trip attributes"""
    t_id: str
    t_weight: float
    p_id: str
    hh_id: str
    n: int
    day_of_week: int
    departure: int
    duration: int
    gis_length: float
    main_mode: TripMode
    purpose: Purpose
    sd_group: SourceDestinationGroup
    valid: bool
    from_location: str = pd.NA
    from_zone: str = pd.NA
    to_location: str = pd.NA
    to_zone: str = pd.NA


@dataclass
class Activity:
    """ Activity information (including some leg information as well) """
    a_id: str
    a_weight: float
    p_id: str
    n: int
    type: Purpose
    duration: int
    leg_dist: float
    leg_duration: float
    leg_mode: TripMode
    location: str = pd.NA
    zone: str = pd.NA


@dataclass
class Visitations:
    """ Aggregated visitation information """
    location: str
    n: int
    purpose: Purpose = pd.NA
    time: pd.Timestamp = pd.NA
