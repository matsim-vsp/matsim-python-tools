#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optuna
import traceback

from . import study_as_df

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="matsim-calibration", description="Calibration CLI")
    parser.add_argument('file', nargs=1, type=str, help="Path to input db")
    parser.add_argument("--name", type=str, default="calib", help="Calibration name")
    parser.add_argument("--output", default=None, help="Output path")
    args = parser.parse_args()

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

