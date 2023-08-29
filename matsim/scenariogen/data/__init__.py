""" This module contains dataclasses and methods for reading and processing survey data.
"""

__all__ = ["ParkingPosition", "HouseholdType", "EconomicStatus", "Gender", "Employment", "Availability", "Purpose",
           "TripMode", "DistanceGroup", "DurationGroup", "SourceDestinationGroup",
           "Household", "Person", "Trip", "Activity"]

from dataclasses import dataclass
from enum import Enum, auto

import numpy as np


class StrEnum(str, Enum):
    pass


# this creates nice lowercase and JSON serializable names
# https://docs.python.org/3/library/enum.html#using-automatic-values
class AutoNameLower(StrEnum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class AutoNameLowerStrEnum(AutoNameLower):
    pass


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

    SHOP_DAILY = auto()
    SHOP_OTHER = auto()
    PERSONAL_BUSINESS = auto()
    TRANSPORT = auto()
    LEISURE = auto()
    DINING = auto()
    OUTSIDE_RECREATION = auto()
    VISIT = auto()
    HOME = auto()
    OTHER = auto()


class TripMode(AutoNameLowerStrEnum):
    WALK = auto()
    BIKE = auto()
    CAR = auto()
    RIDE = auto()
    PT = auto()
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


@dataclass
class Activity:
    """ Activity information (including leg) """
    a_id: str
    p_id: str
    n: int
    type: Purpose
    duration: int
    leg_dist: float
    leg_duration: float
    leg_mode: TripMode