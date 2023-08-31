#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

from .io import read_all
from .preparation import prepare_persons, create_activities

METADATA = "data-extract-activities", "Extract activities and persons from survey data."


def setup(parser: argparse.ArgumentParser):
    parser.add_argument("dirs", nargs="+", help="Directories with survey data")
    parser.add_argument("--regiostar", default=None)

    parser.add_argument("--output", default="table", help="Output prefix")


def main(args):
    hh, persons, trips = read_all(args.dirs, regio=args.regiostar)

    hh.to_csv(args.output + "-households.csv")
    trips.to_csv(args.output + "-trips.csv")
    persons.to_csv(args.output + "-unscaled-persons.csv")

    print("Written survey csvs")

    df = prepare_persons(hh, persons, trips, augment=5, core_weekday=True, remove_with_invalid_trips=True)

    df.to_csv(args.output + "-persons.csv", index_label="idx")
    print("Created %d synthetics persons" % len(df))

    activities = create_activities(df, trips, include_person_context=False, cut_groups=False)
    activities.to_csv(args.output + "-activities.csv", index=False)
