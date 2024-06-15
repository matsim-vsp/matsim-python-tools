#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import traceback

METADATA = "create-csv", "Create plots and csv from calibration study."

def setup(parser: argparse.ArgumentParser):
    parser.add_argument('file', nargs=1, type=str, help="Path to input db")
    parser.add_argument("--name", type=str, default="calib", help="Calibration name")
    parser.add_argument("--output", default=None, help="Output path")

def main(args):

    import optuna
    from . import study_as_df

    study = optuna.load_study(
        study_name=args.name,
        storage="sqlite:///%s" % args.file[0],
    )

    if not args.output:
        args.output = args.file[0] + ".csv"

    df = study_as_df(study)
    df.to_csv(args.output, index=False)

    try:
        from .plot import plot_study
        plot_study(study)

    except ImportError:
        print("Could not plot study.")
        traceback.print_exc()