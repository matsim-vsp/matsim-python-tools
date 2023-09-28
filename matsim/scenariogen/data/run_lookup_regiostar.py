#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import pandas as pd

METADATA = "data-plz-regiostar", "Create regiostar lookup for plz."


def prepare_regiostar_lookup(plz, regiostar) -> pd.DataFrame:
    plz = pd.read_csv(plz)

    regiostar = pd.read_excel(regiostar, sheet_name="ReferenzGebietsstand2020")
    df = plz.merge(regiostar, how="left", left_on="ags", right_on="gem_20")

    df = df[["plz", "ags", "RegioStaR2", "RegioStaR4", "RegioStaR5", "RegioStaR7", "RegioStaR17"]]

    return df


def setup(parser: argparse.ArgumentParser):
    pass


def main(args):
    d = "/Users/rakow/Development/matsim-scenarios/shared-svn/projects/matsim-germany/"

    # FIXME: use args

    df = prepare_regiostar_lookup(d + "zuordnung_plz_ort.csv", d + "RegioStaR-Referenzdateien.xlsx")

    df.to_csv(d + "zuordnung_plz_regiostar.csv", index=False)
